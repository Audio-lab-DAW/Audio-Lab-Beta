"""Task SQ1 (lane N): inserts the Quality switch (sq1.js) and its chip style (sq1.css) into index.html.
Re-runnable on a fresh file: it removes an earlier copy first. Anchors are asserted unique.
  python3 tools/engine-lab/sq/sq1.py [index.html]"""
import sys, os, re
H = os.path.dirname(os.path.abspath(__file__))
p = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
s = open(p, encoding='utf-8').read()
js = open(os.path.join(H, 'sq1.js'), encoding='utf-8').read().rstrip('\n') + '\n'
css = open(os.path.join(H, 'sq1.css'), encoding='utf-8').read().rstrip('\n') + '\n'
# remove an earlier copy
s = re.sub(r'/\* ===== lane N \(task SQ1\).*?/\* ===== end of lane N SQ1 ===== \*/\n', '', s, flags=re.S)
s = re.sub(r'/\* lane N \(task SQ1\): the Hi-Fi switch.*?#sqCard \.sqold\{color:#f5c84c\}\n', '', s, flags=re.S)
s = re.sub(r'/\* lane N \(task SQ1\): the Quality chip.*?#fxin \.dev\.dfclosed \.dfs>\.devh>\.sqchip\{display:none\}\n', '', s, flags=re.S)
A = 'function askChoice(title,text,btns,icon){'
B = '.dacv{display:flex;'
assert s.count(A) == 1, A
assert s.count(B) == 1, B
assert 'const SQ=' not in s and 'SQ_HOOKS=window' not in s
s = s.replace(A, js + A).replace(B, css + B)
open(p, 'w', encoding='utf-8').write(s)
print('SQ1 inserted')
