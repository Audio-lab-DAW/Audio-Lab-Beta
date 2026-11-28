"""Task NI-10a (lane D): I7 draw the arc, part 1.
Edit script with unique asserted anchors (needs NI-7b in the file: run ni_31.py and ni_7b.py first), so a rebase can re-run it.
  python3 tools/feature-lab/ni/ni_10a.py [index.html]
Adds (JS from ni_10a_block.js, after the NI-7b block):
  - drawing the wanted energy in NI-6's energy lane (draw mode from the lane's menu or the command ni.drawArc; drag draws, Alt-drag
    erases, Esc or right-click ends; one undo step per stroke), stored as S.ni_arc = {v:1, line:[per beat, or null]}
  - the shortfall: stretches of at least a bar where the measured energy sits 0.06 or more under the line, shaded red with "−20 dB"
    (the loudness change that closes the gap), listed in the lane's menu (click to go there) and said in a toast after each stroke
  - NI_arcDraw (NI-6, lane D) wrapped to draw the line after the lane; the lane's menu gets Draw your line, the stretches, Clear
  - NI.al, NI_HOOKS.arcLine (line(), short(), set(b0, b1, v0, v1), mode(on)) for NI-10b and NI-11
"""
import sys, os
P = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
s = open(P, encoding='utf-8').read()
if '/* ===== lane D (task NI-10a)' in s:
    print('NI-10a already applied'); sys.exit(0)
assert '/* ===== end of lane D NI-7b ===== */' in s, 'NI-7b must be in the file first (ni_31.py, then ni_7b.py)'
def rep(s, old, new):
    n = s.count(old)
    assert n == 1, (old[:70], n)
    return s.replace(old, new)
A1 = "{id:'ni.harmonicRuler',g:'view',"
s = rep(s, A1, "{id:'ni.drawArc',g:'view',l:'Draw your energy line (the energy you want over the song; the parts under it are marked)',d:'',ic:'M2 14c3-6 5-8 8-4s5 2 8-6',run:()=>NI_alMode(!NI.al.draw)},\n " + A1)
A2 = "{label:'Hide the energy arc',act:()=>NI_arcShow(false)}])}"
s = rep(s, A2, "...NI_alMenuItems()," + A2)
JS = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ni_10a_block.js'), encoding='utf-8').read()
A3 = '/* ===== end of lane D NI-7b ===== */'
s = rep(s, A3, A3 + JS.rstrip('\n'))
open(P, 'w', encoding='utf-8').write(s)
print('NI-10a applied')
