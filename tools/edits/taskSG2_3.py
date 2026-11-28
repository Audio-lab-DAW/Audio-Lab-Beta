"""Task SG2-3 (lane R, prefix sg): S1, the stem split's card with a strip per stem (the user's pick), and the hooks for lanes F and G.
Needs SG2-2. Inserts taskSG2_3_block.js after the SG2-2 block and taskSG2_3_css.txt before .a2dbar. Keep working now sends the split
to the card (SG_HOOKS.keep); the end of a split sent on says what was added, with Undo (SG_HOOKS.added); SG_HOOKS.card(job) gives
lane F the strips for OV5's notify, SG_HOOKS.pill(key) gives lane G a strip for MD1's pill. Bumps VERSION (highest on main + 0.001).
  python3 tools/edits/taskSG2_3.py [index.html]"""
import sys, os, re
P = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
H = os.path.dirname(os.path.abspath(__file__))
s = open(P, encoding='utf-8').read()
blk = open(os.path.join(H, 'taskSG2_3_block.js'), encoding='utf-8').read()
css = open(os.path.join(H, 'taskSG2_3_css.txt'), encoding='utf-8').read()
assert 'task SG2-2' in s, 'SG2-2 first'
assert 'task SG2-3' not in s, 'already applied'
for n in ('sgStrips', 'sgDoneText', 'sgCard', 'sgCardClose', 'sgAdded'):
    assert not re.search(r'(function|const|let|var)\s+' + n + r'\b', s), n + ' exists already'
def one(a, b):
    global s
    assert s.count(a) == 1, (s.count(a), a[:90]); s = s.replace(a, b)
m = re.findall(r"const VERSION='(\d+)\.(\d+)'", s); assert len(m) == 1
v = '%s.%03d' % (m[0][0], int(m[0][1]) + 1)
A = "/* ===================== neural stem separation: HTDemucs v4 (Meta, MIT weights) running in the browser ====================="
one(A, blk.replace('v0.000', 'v' + v) + A)
one('.a2dbar{height:6px;', css + '.a2dbar{height:6px;')
one("if(!pick||!pick.length){j.added=0;", "if(!pick||!pick.length){j.added=0;j.pickNull=!pick;")
s = re.sub(r"const VERSION='\d+\.\d+'", "const VERSION='%s'" % v, s, count=1)
open(P, 'w', encoding='utf-8').write(s)
print(v)
