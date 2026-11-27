#!/usr/bin/env python3
"""Task FT-C3c (lane C): Launchpad and APC as section launchers. Anchored edit; re-run on a fresh index.html after a rebase.
   python3 tools/feature-lab/ft/ftC3c.py [index.html]"""
import sys, os
F = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
H = os.path.dirname(os.path.abspath(__file__))
s = open(F, encoding='utf-8').read()
if 'task FT-C3c' in s: sys.exit('already applied')
assert 'task FT-C3b' in s, 'needs FT-C3b'
a = "FT_HOOKS.surfacePaint=()=>mcAll();FT_HOOKS.surfaceAs=(name,kind)=>mcAsSet(name,kind||'');\n"
assert s.count(a) == 1, s.count(a)
blk = open(os.path.join(H, 'ftC3c_block.js'), encoding='utf-8').read().rstrip('\n')
s = s.replace(a, a + blk + "\n")
open(F, 'w', encoding='utf-8').write(s); print('FT-C3c applied')
