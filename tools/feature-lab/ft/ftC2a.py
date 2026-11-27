#!/usr/bin/env python3
"""Task FT-C2a (lane C): Ableton Push 1, part 1 (connect, display, pads). Needs FT-C1a and FT-C1b. Anchored; re-run on a fresh index.html after a rebase.
   python3 tools/feature-lab/ft/ftC2a.py [index.html]"""
import sys, os
F = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
H = os.path.dirname(os.path.abspath(__file__))
s = open(F, encoding='utf-8').read()
if 'task FT-C2a' in s: sys.exit('already applied')
assert 'task FT-C1b' in s, 'needs FT-C1b'
a = "{const _s=start;start=function(){const r=_s.apply(this,arguments);try{if(CTL.fbn)ctlPoll()}catch(e){}return r}}\n"
assert s.count(a) == 1, s.count(a)
blk = open(os.path.join(H, 'ftC2a_block.js'), encoding='utf-8').read().rstrip('\n')
s = s.replace(a, a + blk + "\n")
open(F, 'w', encoding='utf-8').write(s); print('FT-C2a applied')
