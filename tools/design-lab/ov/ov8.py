#!/usr/bin/env python3
"""Task OV8 (lane F, overlays; docs/design-round-5-overlays.md section 5, step OV8): the command palette K1 on ⌘K with the
Assistant inside, Recent first, and the ? key sheet. The user's pick K1 (palette on ⌘K, the Assistant inside it).
   python3 tools/design-lab/ov/ov8.py index.html
Two anchors, asserted unique: the JS block (ov8_block.js) before askChoice, the CSS (ov8_css.txt) before .dacv. The block adds two
rows to the shortcut list at run time (help.palette on Mod+K, help.keySheet on ?) and takes the Assistant's default key Mod+K off
its row (a key the user gave the Assistant is kept). No other lane's code is changed. Re-run on a fresh file after a rebase."""
import sys, os
F = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
H = os.path.dirname(os.path.abspath(__file__))
s = open(F, encoding='utf-8').read()
assert 'task OV8' not in s, 'already applied'
assert 'task OV2a' in s and 'function xtCommands(' in s and 'function runCommand(' in s, 'needs OV2a and the commands registry (XT-DL2)'
for nm in ['ovPalOpen', 'ovKeysOpen', 'ovFz', 'ovK1Init', 'OV_K1', 'ovPalDraw']:
    assert nm + '(' not in s and nm + '=' not in s, 'name taken: ' + nm

def ins(anchor, text):
    global s
    c = s.count(anchor)
    assert c == 1, (c, anchor)
    s = s.replace(anchor, text + anchor)

ins('function askChoice(title,text,btns,icon){', open(os.path.join(H, 'ov8_block.js'), encoding='utf-8').read())
ins('.dacv{display:flex;', open(os.path.join(H, 'ov8_css.txt'), encoding='utf-8').read())
open(F, 'w', encoding='utf-8').write(s)
print('task OV8 applied')
