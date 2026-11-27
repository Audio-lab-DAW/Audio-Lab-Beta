#!/usr/bin/env python3
"""Task FT-C3b (lane C): Mackie Control and HUI. Anchored edit; re-run on a fresh index.html after a rebase.
   python3 tools/feature-lab/ft/ftC3b.py [index.html]"""
import sys, os
F = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
H = os.path.dirname(os.path.abspath(__file__))
s = open(F, encoding='utf-8').read()
if 'task FT-C3b' in s: sys.exit('already applied')
assert 'task FT-C3a' in s, 'needs FT-C3a'
a = "remove:dn=>ctlTplRemove(dn)};\n"
assert s.count(a) == 1, s.count(a)
blk = open(os.path.join(H, 'ftC3b_block.js'), encoding='utf-8').read().rstrip('\n')
s = s.replace(a, a + blk + "\n")
open(F, 'w', encoding='utf-8').write(s); print('FT-C3b applied')
