#!/usr/bin/env python3
"""Task FT-C2c (lane C): Ableton Push 1, part 3 (sections as scenes: Session mode). Needs FT-C2b. Anchored; re-run on a fresh index.html after a rebase.
   python3 tools/feature-lab/ft/ftC2c.py [index.html]"""
import sys, os
F = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
H = os.path.dirname(os.path.abspath(__file__))
s = open(F, encoding='utf-8').read()
if 'task FT-C2c' in s: sys.exit('already applied')
assert 'task FT-C2b' in s, 'needs FT-C2b'
a = "A drum kit track: the lower left pads play its 16 pads, the top two rows are 16 steps of the chosen pad.';w.appendChild(h)}return r}}\n"
assert s.count(a) == 1, s.count(a)
blk = open(os.path.join(H, 'ftC2c_block.js'), encoding='utf-8').read().rstrip('\n')
s = s.replace(a, a + blk + "\n")
open(F, 'w', encoding='utf-8').write(s); print('FT-C2c applied')
