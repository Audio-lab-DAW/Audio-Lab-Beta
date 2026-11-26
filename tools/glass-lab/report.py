#!/usr/bin/env python3
"""python3 report.py results.json  -> table scenario x variant (median over reps of each window's numbers) and the saving against 'full'."""
import json, sys, statistics as st
r = json.load(open(sys.argv[1])); rows = r['rows']
print(json.dumps({k: v for k, v in r['meta'].items() if k in ('gpu', 'dsf', 'win', 'reps', 'chromium', 'cores', 'errors')}))
med = lambda v: st.median([x for x in v if x is not None]) if v else float('nan')
scs = []
for x in rows:
    if x['scen'] not in scs: scs.append(x['scen'])
for sc in scs:
    vs = []
    for x in rows:
        if x['scen'] == sc and x['variant'] not in vs: vs.append(x['variant'])
    print('\nscenario', sc); print('%-12s %7s %7s %7s | %7s %7s | %8s %6s | %7s %7s | %s' % ('variant', 'swMed', 'swP95', 'fps', 'rafMed', 'rafP95', 'viz/f', 'gpu/f', 'cpuGPU', 'cpuRend', 'saved viz ms/f, spread of reps'))
    base = None
    for v in vs:
        w = [x for x in rows if x['scen'] == sc and x['variant'] == v]
        g = lambda k: med([x.get(k) for x in w])
        cost = [x['viz_draw_ms_per_frame'] + x['gpu_ms_per_frame'] for x in w]
        if v == 'full': base = med(cost)
        print('%-12s %7.1f %7.1f %7.1f | %7.1f %7.1f | %8.2f %6.2f | %7.0f %7.0f | %+6.1f  [%s]' % (v, g('sw_med'), g('sw_p95'), g('fps'), g('raf_med'), g('raf_p95'), g('viz_draw_ms_per_frame'), g('gpu_ms_per_frame'), g('cpu_gpu-process'), g('cpu_renderer'), base - med(cost), ' '.join('%.1f' % c for c in cost)))
