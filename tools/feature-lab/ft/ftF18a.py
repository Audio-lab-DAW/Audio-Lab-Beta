#!/usr/bin/env python3
"""Task FT-F18a (lane C): Kick and bass lab, part 1 (bass line key, tail overlap, low-band correlation as a row of lane D's lab).
   One new block before the MIDI utility pack (after lane C's F16b block); nothing else is changed. Re-run on a fresh index.html after a rebase.
   python3 tools/feature-lab/ft/ftF18a.py [index.html] [version]"""
import sys, os
F = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
VER = sys.argv[2] if len(sys.argv) > 2 else None
H = os.path.dirname(os.path.abspath(__file__))
s = open(F, encoding='utf-8').read()
if 'task FT-F18a)' in s: sys.exit('already applied')
for need in ['NI_HOOKS.kickBassView={', 'const FT_HOOKS=window.FT_HOOKS', 'function NI_allNotes' if 'function NI_allNotes' in s else 'const NI_allNotes=', 'async function renderMixChunked(']:
    assert need in s, need
a = "/* ---------------- MIDI utility pack ---------------- */"
assert s.count(a) == 1, s.count(a)
assert s.index('const FT_HOOKS=window.FT_HOOKS') < s.index(a) and s.index('NI_HOOKS.kickBassView={') < s.index(a)
blk = open(os.path.join(H, 'ftF18a_block.js'), encoding='utf-8').read().rstrip('\n')
if VER: blk = blk.replace('/* v0.315 (task FT-F18a)', '/* v%s (task FT-F18a)' % VER, 1)
for name in ['FTKB', 'ftKbBassKey', 'ftKbOverlap', 'ftKbLow', 'ftKbCorrOf', 'ftKbCorr', 'ftKbSg', 'ftKbDb', 'ftKbCorrWords', 'ftKbDraw', 'FTKB_TIP', 'ftKbRow']:
    for k in ('function %s(' % name, 'const %s=' % name, 'let %s=' % name):
        assert k not in s, 'name taken: ' + name
s = s.replace(a, blk + "\n" + a, 1)
open(F, 'w', encoding='utf-8').write(s); print('FT-F18a applied')
