"""Task IN-V (lane E, instruments): the Visualizer, the user's pick V1 (one frequency axis) with the viridis colour map, and the right-click
menu entries (colour map, range, tilt, hold, speed).
Edit script with unique asserted anchors, so a rebase can re-run it on a fresh index.html.
  python3 tools/design-lab/in/in_v.py [index.html]
Does:
  1. adds the IN-V block (in_v_block.js) before askChoice: INV; VZD.spec (the V1 module: spectrogram | shared axis | sideways spectrum,
     colour bar), VZD.fft (IN-S's front panel with the menu's tilt and hold), VZD.lev (M2), VZD.wave wrapped (amplitude and time scale)
  2. vizFrame: in All, the spectrogram and spectrum panes become one module (INV.merge)
  3. pvMenu (the Visualizer's right-click menu): the entries of INV.menu after "Visualizer sits"
"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
P = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
s = open(P, encoding='utf-8').read()
if '/* ===== lane E (task IN-V)' in s:
    print('IN-V already applied'); sys.exit(0)
assert '/* ===== lane E (task IN-S)' in s or 'insVzSpec' in s, 'IN-S must be in first'

def rep(s, old, new, n=1):
    c = s.count(old)
    assert c == n, (old[:100], c, n)
    return s.replace(old, new)

s = rep(s, ":[[mode,0,0,W,H]];\n", ":[[mode,0,0,W,H]];INV.merge(P);/* IN-V: V1, one frequency axis */\n")
s = rep(s, "act:at(k)}))])}", "act:at(k)})),...INV.menu()/* IN-V */])}")
js = open(os.path.join(HERE, 'in_v_block.js'), encoding='utf-8').read()
s = rep(s, "function askChoice(title,text,btns,icon){", js + "function askChoice(title,text,btns,icon){")
open(P, 'w', encoding='utf-8').write(s)
print('IN-V applied')
