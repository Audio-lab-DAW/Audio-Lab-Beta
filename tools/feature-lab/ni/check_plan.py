"""NI-0 check: every picked RF2 idea has a step in docs/ideas-build.md, no unpicked idea is built."""
import re, sys, pathlib
root = pathlib.Path(__file__).resolve().parents[3]
doc = (root / 'docs/ideas-build.md').read_text()
picked = 'I1 I2 I3 I4 I5 I6 I7 I8 I9 I10 I11 I12 I13 I14 I15 I16 I17 I18 I20 I21 I22 I23 I26 I27 I28 I29 I31 I32'.split()
unpicked = 'I19 I24 I25 I30 I33 I34'.split()
rows = [l for l in doc.splitlines() if re.match(r'\| NI-\d+[ab]? \|', l)]
built = {}
for r in rows:
    step = r.split('|')[1].strip()
    m = re.search(r'\*\*(I\d+)\b', r)
    if m: built.setdefault(m.group(1), []).append(step)
# NI-12 builds I26 inside "the control tape and I26 knob memory"
if 'I26' not in built and any('I26 knob memory' in r for r in rows): built['I26'] = ['NI-12']
fail = 0
for i in picked:
    ok = i in built
    print(('ok  ' if ok else 'FAIL'), i, built.get(i, '-'))
    fail += not ok
for i in unpicked:
    if i in built:
        print('FAIL unpicked idea scheduled', i, built[i]); fail += 1
print(len(rows), 'step rows;', 'all pass' if not fail else f'{fail} failures')
sys.exit(1 if fail else 0)
