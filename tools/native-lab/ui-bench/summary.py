"""AudioLab UI bench (task RN4): one table from out/metal.json, out/web.json and out/web-unlimited.json.
Usage: python3 summary.py <out dir>"""
import json, os, sys

d = sys.argv[1] if len(sys.argv) > 1 else 'out'


def load(name):
    try:
        with open(os.path.join(d, name)) as f:
            return json.load(f)
    except Exception as e:  # noqa: BLE001 - a missing run is reported, not fatal
        return {'error': f'{name}: {e}'}


def f(v):
    return '-' if v is None else (f'{v:.2f}' if isinstance(v, float) else str(v))


rows = []
m = load('metal.json')
mx = m.get('max_3840x2160', {})
rows.append(('Metal, 3840x2160 off screen, each frame waited for', mx.get('rects'), mx.get('frame_waited_ms', {}).get('median'),
             mx.get('frame_waited_ms', {}).get('p99'), mx.get('cpu_build_encode_ms', {}).get('median'), mx.get('gpu_ms', {}).get('median'),
             mx.get('pipelined_fps')))
sc = m.get('screen', {})
rows.append((f"Metal, window {sc.get('drawable')} at screen max {sc.get('screen_max_fps')} Hz", None, sc.get('interval_ms', {}).get('median'),
             sc.get('interval_ms', {}).get('p99'), sc.get('cpu_build_encode_ms', {}).get('median'), sc.get('gpu_ms', {}).get('median'), sc.get('fps')))
for name, w in (('Electron', load('web.json')), ('Electron, no frame limit', load('web-unlimited.json'))):
    for k in ('webgl2', 'canvas2d'):
        a = w.get('max_3840x2160_' + k, {})
        if name == 'Electron':
            rows.append((f'{name} {k}, 3840x2160 off screen, each frame waited for', a.get('rects'), a.get('frame_waited_ms', {}).get('median'),
                         a.get('frame_waited_ms', {}).get('p99'), a.get('js_build_and_draw_calls_ms', {}).get('median'), None, None))
        s = w.get('screen_' + k, {})
        rows.append((f"{name} {k}, window {s.get('canvas')}", None, s.get('interval_ms', {}).get('median'), s.get('interval_ms', {}).get('p99'),
                     s.get('js_per_frame_ms', {}).get('median'), None, s.get('fps')))
print('| Case | rects | frame median ms | frame p99 ms | CPU/JS median ms | GPU median ms | fps |')
print('|---|---|---|---|---|---|---|')
for r in rows:
    print('| ' + ' | '.join(f(x) for x in r) + ' |')
for name in ('metal.json', 'web.json', 'web-unlimited.json'):
    j = load(name)
    if 'error' in j:
        print(f'\n{name}: {j["error"]}')
print('\nMetal device:', m.get('device'), '| Electron', load('web.json').get('electron'), 'renderer',
      load('web.json').get('max_3840x2160_webgl2', {}).get('renderer'))
