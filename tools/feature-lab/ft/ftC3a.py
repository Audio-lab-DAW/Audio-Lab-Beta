#!/usr/bin/env python3
"""Task FT-C3a (lane C): generic controllers and templates. Anchored edits; re-run on a fresh index.html after a rebase.
   python3 tools/feature-lab/ft/ftC3a.py [index.html]"""
import sys, os
F = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
H = os.path.dirname(os.path.abspath(__file__))
s = open(F, encoding='utf-8').read()
if 'task FT-C3a' in s: sys.exit('already applied')
assert 'task FT-C2c' in s, 'needs FT-C2c'
def rep(a, b):
    global s
    assert s.count(a) == 1, ('anchor count %d' % s.count(a), a[:120]); s = s.replace(a, b)
# template targets ("@dev:0", "@pad:3", "@cmd:play"...) get a plain name everywhere a mapping is named
rep("const ctlLabel=id=>{const C=CT.get(id)", "const ctlLabel=id=>{if(String(id)[0]==='@'&&typeof ctlTLabel==='function')return ctlTLabel(id);const C=CT.get(id)")
a = "FT_HOOKS.push1Launch=(id,now)=>p1cLaunch(p1cSecs().find(s=>s.id===id),!!now);\n"
blk = open(os.path.join(H, 'ftC3a_block.js'), encoding='utf-8').read().rstrip('\n')
rep(a, a + blk + "\n")
open(F, 'w', encoding='utf-8').write(s); print('FT-C3a applied')
