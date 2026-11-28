"""Task SQ3b (lane N): inserts the pitched read (sq3b.js) right after SQ3's block in index.html (SQ1 and SQ3 must be in the file).
Re-runnable on a fresh file: it removes an earlier copy first. Anchors are asserted unique.
  python3 tools/engine-lab/sq/sq3b.py [index.html]"""
import sys, os, re
H = os.path.dirname(os.path.abspath(__file__))
p = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
s = open(p, encoding='utf-8').read()
js = open(os.path.join(H, 'sq3b.js'), encoding='utf-8').read().rstrip('\n') + '\n'
s = re.sub(r'/\* ===== lane N \(task SQ3b.*?/\* ===== end of lane N SQ3b ===== \*/\n', '', s, flags=re.S)
A = '/* ===== end of lane N SQ3 ===== */\n'
assert s.count(A) == 1, 'SQ3 is not in the file: run sq3.py first'
assert 'const SQP=' not in s
for f in ('function sampPlay(c,I,dest,p,w,dur,v){', 'function pzPlay(c,I,dest,p,w,v){', 'function warmSounds(){', 'const PZAB=new Map();',
          'function pzKey(I){', 'async function renderMix(sr,', 'async function renderMixChunked(sr,', 'async function bounceRender(',
          'function sqRsPut(b,sr,chs){', 'function askChoice(title,text,btns,icon){'):
    assert s.count(f) == 1, f
s = s.replace(A, A + js)
open(p, 'w', encoding='utf-8').write(s)
print('SQ3b inserted')
