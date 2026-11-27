#!/usr/bin/env python3
"""Task FT-F16a (lane C): Volume shaper, part 1. Anchored edit; re-run on a fresh index.html after a rebase.
   python3 tools/feature-lab/ft/ftF16a.py [index.html] [version]"""
import sys, os
F = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
VER = sys.argv[2] if len(sys.argv) > 2 else None
H = os.path.dirname(os.path.abspath(__file__))
s = open(F, encoding='utf-8').read()
if 'task FT-F16a)' in s: sys.exit('already applied')
assert "ND('ftvs'" not in s and 'al-ftvs' not in s
# the block right after the LFO Shaper's helpers (ND, ANOUT, shPulse and shEval are ready there)
a = "function shApply(f){"
assert s.count(a) == 1, s.count(a)
i = s.index(a); j = s.index("\n", i) + 1
blk = open(os.path.join(H, 'ftF16a_block.js'), encoding='utf-8').read().rstrip('\n')
if VER: blk = blk.replace('/* v0.289 (task FT-F16a)', '/* v%s (task FT-F16a)' % VER, 1)
s = s[:j] + blk + "\n" + s[j:]
open(F, 'w', encoding='utf-8').write(s); print('FT-F16a applied')
