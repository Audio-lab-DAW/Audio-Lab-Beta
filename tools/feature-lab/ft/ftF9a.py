#!/usr/bin/env python3
"""Task FT-F9a (lane C): step sequencer clips, part 1. Anchored edit; re-run on a fresh index.html after a rebase.
   python3 tools/feature-lab/ft/ftF9a.py [index.html] [version]"""
import sys, os
F = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
VER = sys.argv[2] if len(sys.argv) > 2 else None
H = os.path.dirname(os.path.abspath(__file__))
s = open(F, encoding='utf-8').read()
if 'task FT-F9a)' in s: sys.exit('already applied')
assert 'task FT-F2)' in s, 'needs FT-F2'
def rep(a, b):
    global s
    assert s.count(a) == 1, (s.count(a), a[:80])
    s = s.replace(a, b)
# 1. the block, after FT-F2's
a = "  insert:(b,beats)=>ftAmEdit('insert',b,beats),del:id=>{const sc=(S.sections||[]).find(q=>q.id===id);return sc?ftAmEdit('delete',sc.start,sc.len):false}};\n"
blk = open(os.path.join(H, 'ftF9a_block.js'), encoding='utf-8').read().rstrip('\n')
if VER: blk = blk.replace('/* v0.269 (task FT-F9a)', '/* v%s (task FT-F9a)' % VER, 1)
rep(a, a + blk + "\n")
# 2. two commands in the registry, before Duplicate clip
cmds = (" {id:'clip.newSteps',g:'edit',l:'New step sequencer clip',d:'',ic:'M3 5h3v3H3zM8 5h3v3H8zM13 12h3v3h-3zM3 12h3v3H3z',run:()=>ftSqCmdNew()},\n"
        " {id:'clip.editSteps',g:'edit',l:'Edit steps of the selected clip',d:'',ic:'M3 5h14M3 10h14M3 15h14M6 3v14M11 3v14',run:()=>ftSqCmdEdit()},\n")
a = " {id:'dup',g:'edit',l:'Duplicate clip',"
rep(a, cmds + a)
open(F, 'w', encoding='utf-8').write(s); print('FT-F9a applied')
