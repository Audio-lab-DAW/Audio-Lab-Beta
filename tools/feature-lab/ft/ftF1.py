#!/usr/bin/env python3
"""Task FT-F1 (lane C): linked clips. Anchored edit; re-run on a fresh index.html after a rebase.
   python3 tools/feature-lab/ft/ftF1.py [index.html]"""
import sys, os
F = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
H = os.path.dirname(os.path.abspath(__file__))
s = open(F, encoding='utf-8').read()
if 'task FT-F1' in s: sys.exit('already applied')
assert 'task FT-C3c' in s, 'needs FT-C3c'
# 1. the block, after FT-C3c's
a = "FT_HOOKS.gridPaint=()=>lpAll();\n"
assert s.count(a) == 1, s.count(a)
blk = open(os.path.join(H, 'ftF1_block.js'), encoding='utf-8').read().rstrip('\n')
s = s.replace(a, a + blk + "\n")
# 2. two commands in the registry, beside Duplicate clip
a = " {id:'dup',g:'edit',l:'Duplicate clip',"
assert s.count(a) == 1, s.count(a)
cmds = (" {id:'clip.linkedDup',g:'edit',l:'Duplicate as linked copy',d:'',ic:'M8 12l4-4M6.5 9.5l-2 2a2.5 2.5 0 0 0 3.5 3.5l2-2M13.5 10.5l2-2a2.5 2.5 0 0 0-3.5-3.5l-2 2',run:()=>lkDupSel()},\n"
        " {id:'clip.unique',g:'edit',l:'Make unique (break the link)',d:'',ic:'M6.5 9.5l-2 2a2.5 2.5 0 0 0 3.5 3.5l2-2M13.5 10.5l2-2a2.5 2.5 0 0 0-3.5-3.5l-2 2M4 4l2 2M14 14l2 2',run:()=>lkUnique(lkSel())},\n")
s = s.replace(a, cmds + a)
open(F, 'w', encoding='utf-8').write(s); print('FT-F1 applied')
