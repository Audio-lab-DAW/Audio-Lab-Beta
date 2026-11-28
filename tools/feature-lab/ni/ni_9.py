"""Task NI-9 (lane D): I5 harmonic ruler.
Edit script with unique asserted anchors (needs NI-5c in the file), so a rebase can re-run it on a fresh index.html.
  python3 tools/feature-lab/ni/ni_9.py [index.html]
Adds (JS from ni_9_block.js, after the NI-5c block):
  - a piano strip along the bottom of every live spectrum view drawn by lane E's INS.spec (Spectrum device, spectrum overlay, Visualizer),
    size 'full' and 'mid' only; the five strongest peaks named with note and cents ("A2 0 c"), amber outside the song key (NI_key), red
    with "rings" when a pitch keeps sounding for more than a beat while the rest of the sound fades by 6 dB more than it
  - INS.spec is wrapped once from lane D's block (lane E's code is not changed); peaks found at most 8 times a second per view
    (3 at the Light level), from the bins the view already read this frame; nothing while the view is not live
  - switch UI.niHr (on unless false): command ni.harmonicRuler, main menu entry, NI_SETTINGS row ni.harmonicRuler
  - NI_HOOKS.harmonicRuler(g, box, peaks, o), NI_HOOKS.harmonicPeaks(an, lo, hi, st)
"""
import sys, os
P = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
s = open(P, encoding='utf-8').read()
if '/* ===== lane D (task NI-9)' in s:
    print('NI-9 already applied'); sys.exit(0)
assert '/* ===== end of lane D NI-5c ===== */' in s, 'NI-5c must be in the file first'
def rep(s, old, new):
    n = s.count(old)
    assert n == 1, (old[:70], n)
    return s.replace(old, new)
# 1. the command, after ni.monoLoss
A1 = "{id:'ni.monoLoss',g:'view',l:'Mono loss map (what each track loses in mono, band by band)',d:'',ic:'M3 12h4l3-7 4 14 3-7h4',run:()=>NI_mlOpen()},"
s = rep(s, A1, A1 + "\n {id:'ni.harmonicRuler',g:'view',l:'Harmonic ruler on / off (note names of the strongest peaks under every spectrum view)',d:'',ic:'M2 15h16M4 15V9M7 15V6M10 15V10M13 15V5M16 15V11',run:()=>NI_hrShow(!NI_hrOn())},")
# 2. the main menu, after Mono loss
A2 = "{label:'Mono loss…',sub:'what each track loses in mono, and which tracks cancel',ic:I('M3 12h4l3-7 4 14 3-7h4','#4cc9f0'),act:()=>NI_mlOpen()},"
s = rep(s, A2, A2 + "\n   {label:NI_hrOn()?'Harmonic ruler: on':'Harmonic ruler: off',sub:'note names of the strongest peaks under every spectrum view',ic:I('M2 15h16M4 15V9M7 15V6M10 15V10M13 15V5M16 15V11','#f5c84c'),act:()=>NI_hrShow(!NI_hrOn())},")
# 3. JS after NI-5c
JS = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ni_9_block.js'), encoding='utf-8').read()
A3 = '/* ===== end of lane D NI-5c ===== */'
s = rep(s, A3, A3 + JS.rstrip('\n'))
open(P, 'w', encoding='utf-8').write(s)
print('NI-9 applied')
