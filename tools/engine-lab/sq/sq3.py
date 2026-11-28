"""Task SQ3 (lane N): inserts resample once (sq3.js) right after SQ1's block in index.html (SQ1 must be in the file: run sq1.py first).
Re-runnable on a fresh file: it removes an earlier copy first. Anchors are asserted unique.
  python3 tools/engine-lab/sq/sq3.py [index.html]"""
import sys, os, re
H = os.path.dirname(os.path.abspath(__file__))
p = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
s = open(p, encoding='utf-8').read()
js = open(os.path.join(H, 'sq3.js'), encoding='utf-8').read().rstrip('\n') + '\n'
s = re.sub(r'/\* ===== lane N \(task SQ3\).*?/\* ===== end of lane N SQ3 ===== \*/\n', '', s, flags=re.S)
A = '/* ===== end of lane N SQ1 ===== */\n'
assert s.count(A) == 1, 'SQ1 is not in the file: run sq1.py first'
assert s.count('function askChoice(title,text,btns,icon){') == 1
assert 'const SQRS=' not in s
for f in ('async function renderMix(sr,', 'async function renderMixChunked(sr,', 'async function bounceRender(', 'async function neuTo44(buf){', 'const SBUF=new Map();', 'BUFS=new Map()', 'WARPBUF=new Map()'):
    assert s.count(f) == 1, f
s = s.replace(A, A + js)
open(p, 'w', encoding='utf-8').write(s)
print('SQ3 inserted')
