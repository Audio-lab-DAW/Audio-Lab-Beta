#!/usr/bin/env python3
"""Task FT-C1b (lane C): the mappings page. Anchored edits; re-run on a fresh index.html after a rebase.
   python3 tools/feature-lab/ft/ftC1b.py [index.html]"""
import sys, os
F = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
H = os.path.dirname(os.path.abspath(__file__))
s = open(F, encoding='utf-8').read()
if 'task FT-C1b' in s: sys.exit('already applied')
assert 'task FT-C1a' in s, 'needs FT-C1a'
def rep(a, b):
    global s
    assert s.count(a) == 1, ('anchor count %d' % s.count(a), a[:120]); s = s.replace(a, b)
# a bigger first window for the full page
rep("const w=fwin('ctlWin','Controllers',{x:Math.max(20,innerWidth/(ZOOM||1)/2-340),y:110,w:680,h:420});", "const w=fwin('ctlWin','Controllers',{x:Math.max(20,innerWidth/(ZOOM||1)/2-390),y:90,w:780,h:520});")
blk = open(os.path.join(H, 'ftC1b_block.js'), encoding='utf-8').read().rstrip('\n')
rep("SCM.set('learn',SCM.get('ctl.learn'));\n", "SCM.set('learn',SCM.get('ctl.learn'));\n" + blk + "\n")
open(F, 'w', encoding='utf-8').write(s); print('FT-C1b applied')
