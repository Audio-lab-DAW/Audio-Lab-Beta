"""Task TM0 (lane S, themes): the build plan is in place and matches the picks it builds from.
Checks: docs/themes-build.md has the six steps and a status table; every picked version (A1 B1 C2 D2 E2 E2L G2 H1 J2 J2D) is in
tools/design-lab/th2/themes.json with its tokens; each one's icons exist in desktop/icon-assets/picker; the round 2 gate passes.
No browser needed: TM0 changes no app code.
  python3 tools/ui-tests/taskTM0.py"""
# for: TM0
import os, sys, json, re, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, '..', '..')
N = [0, 0]; FAIL = []
def ck(name, ok, info=''):
    N[0] += 1
    if ok: N[1] += 1
    else: FAIL.append(name)
    print(('PASS ' if ok else 'FAIL ') + name + ((' : ' + str(info)) if info and not ok else ''))
plan = open(os.path.join(ROOT, 'docs', 'themes-build.md'), encoding='utf-8').read()
for st in ['TM0', 'TM1', 'TM2', 'TM3', 'TM4', 'TM5']:
    ck('plan has a status row for ' + st, re.search(r'^\| ' + st + r' \|', plan, re.M) is not None)
ck('plan names the picks line', 'A1 B1 C2 D2 E2 G2 H1 J2 | default A1' in plan)
ck('plan ends with "themes complete"', 'themes complete' in plan)
D = json.load(open(os.path.join(ROOT, 'tools', 'design-lab', 'th2', 'themes.json')))
by = {t['id']: t for t in D['themes']}
NEED = ['bg', 'chrome', 'ruler', 'lane0', 'lane1', 'laneSel', 'panel', 'panel2', 'strip', 'display', 'glass', 'glassA', 'line', 'ink', 'lab',
        'mut', 'dis', 'rulerTxt', 'accent', 'accentFill', 'onAccent', 'sel', 'selFill', 'unit', 'rec', 'over', 'ok', 'okS', 'ph', 'tip', 'tipInk', 'tipEdge']
pics = set(f[:-4] for f in os.listdir(os.path.join(ROOT, 'desktop', 'icon-assets', 'picker')) if f.endswith('.png'))
for v in ['A1', 'B1', 'C2', 'D2', 'E2', 'E2L', 'G2', 'H1', 'J2', 'J2D']:
    t = by.get(v)
    ck(v + ' is in th2/themes.json', t is not None)
    if not t: continue
    miss = [k for k in NEED if k not in t['t']]
    ck(v + ' has every semantic token', not miss, miss)
    ck(v + ' has eight track colours', len(t.get('pal', [])) == 8, len(t.get('pal', [])))
    bad = [i for i in t['icons'] if i not in pics]
    ck(v + ' icons exist in the picker', t['icons'] and not bad, bad)
r = subprocess.run([sys.executable, os.path.join(ROOT, 'tools', 'design-lab', 'th2', 'check.py'), '--gate'], capture_output=True, text=True, cwd=os.path.join(ROOT, 'tools', 'design-lab', 'th2'), timeout=600)
ck('th2 check.py --gate passes', r.returncode == 0, (r.stdout + r.stderr)[-300:])
print('%d/%d passed' % (N[1], N[0]))
sys.exit(1 if FAIL else 0)
