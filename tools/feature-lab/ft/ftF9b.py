#!/usr/bin/env python3
"""Task FT-F9b (lane C): step sequencer clips, part 2. Anchored edit; re-run on a fresh index.html after a rebase.
   python3 tools/feature-lab/ft/ftF9b.py [index.html] [version]"""
import sys, os
F = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
VER = sys.argv[2] if len(sys.argv) > 2 else None
H = os.path.dirname(os.path.abspath(__file__))
s = open(F, encoding='utf-8').read()
if 'task FT-F9b)' in s: sys.exit('already applied')
assert 'task FT-F9a)' in s, 'needs FT-F9a'
def rep(a, b):
    global s
    assert s.count(a) == 1, (s.count(a), a[:80])
    s = s.replace(a, b)
# 1. chance also rolls in a converted clip (clip.nch), not only in step clips (lane C's own F9a code)
rep("if(!c||!c.steps||!Array.isArray(r))return r;", "if(!c||!(c.steps||c.nch)||!Array.isArray(r))return r;")
# 2. accent and slide as Acid hears them (F9a's note writer)
rep("function ftSqGen(c){const st=c&&c.steps;if(!st)return;", "function ftSqGen(c){const st=c&&c.steps;if(!st)return;const acid=ftSqAcid(c);")
rep("v=+Math.min(1,lv+(q.ac?.25:0)).toFixed(4)", "v=ftSqV(lv,q.ac,acid)")
# 3. the block, after F9a's last line
a = "FT_HOOKS.stepEditor={open:id=>ftSqOpen(id)"
i = s.index(a); j = s.index("\n", i) + 1
blk = open(os.path.join(H, 'ftF9b_block.js'), encoding='utf-8').read().rstrip('\n')
if VER: blk = blk.replace('/* v0.278 (task FT-F9b)', '/* v%s (task FT-F9b)' % VER, 1)
s = s[:j] + blk + "\n" + s[j:]
# 4. two commands, after Edit steps
a = " {id:'clip.editSteps',g:'edit',"
i = s.index(a); j = s.index("\n", i) + 1
cmds = (" {id:'clip.toSteps',g:'edit',l:'Make step sequencer clip',d:'',ic:'M3 5h3v3H3zM8 5h3v3H8zM13 12h3v3h-3z',run:()=>ftSqCmdConv('steps')},\n"
        " {id:'clip.toNotes',g:'edit',l:'Make normal MIDI clip',d:'',ic:'M3 6h6v2H3zM10 11h7v2h-7z',run:()=>ftSqCmdConv('notes')},\n")
s = s[:j] + cmds + s[j:]
open(F, 'w', encoding='utf-8').write(s); print('FT-F9b applied')
