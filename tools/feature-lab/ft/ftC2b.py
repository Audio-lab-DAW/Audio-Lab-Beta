#!/usr/bin/env python3
"""Task FT-C2b (lane C): Ableton Push 1, part 2 (control: encoders on devices, tracks, transport, drum pads and step lane). Needs FT-C2a. Anchored; re-run on a fresh index.html after a rebase.
   python3 tools/feature-lab/ft/ftC2b.py [index.html]"""
import sys, os
F = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
H = os.path.dirname(os.path.abspath(__file__))
s = open(F, encoding='utf-8').read()
if 'task FT-C2b' in s: sys.exit('already applied')
assert 'task FT-C2a' in s, 'needs FT-C2a'
a = "FT_HOOKS.push1Paint=()=>p1All();\n"
assert s.count(a) == 1, s.count(a)
blk = open(os.path.join(H, 'ftC2b_block.js'), encoding='utf-8').read().rstrip('\n')
s = s.replace(a, a + blk + "\n")
open(F, 'w', encoding='utf-8').write(s); print('FT-C2b applied')
