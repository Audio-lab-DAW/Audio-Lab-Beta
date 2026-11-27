"""Task NI-5c (lane D): X16, the clash measure that knows the beat (AE3 pick folded into I12 masking cables).
Edit script with unique asserted anchors (needs NI-8 in the file), so a rebase can re-run it on a fresh index.html.
  python3 tools/feature-lab/ni/ni_5c.py [index.html]
Adds (JS from ni_5c_block.js, after the NI-8 block):
  - each clash candidate of NI-5a is checked in time: both tracks rendered offline on their own over the 8 beats around the playhead
    (NI-7's one-track render after fader and pan, 22.05 kHz), band levels every 11.6 ms (1/3 octave, two cascaded band-passes), the share of
    moments both are loud in the clash's band at once (each within 10 dB of its own top, within 12 dB of each other)
  - under 25 %: "take turns": the cable is drawn dashed and thin, labelled "A and B take turns", not counted in the legend
  - otherwise the cable's thickness is scaled by the share; the tooltip says the share and that it is an estimate
  - the clash card gets the pair view: both tracks in the band over the 8 beats, beat and bar lines, the moments loud together shaded
  - kept per track and window under NI-3's piece key; measured in the background (NI-3's rules: not during an export, while playing only
    with a quiet CPU); NI_HOOKS.clashTiming
"""
import sys, os
P = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
s = open(P, encoding='utf-8').read()
if '/* ===== lane D (task NI-5c)' in s:
    print('NI-5c already applied'); sys.exit(0)
assert '/* ===== end of lane D NI-8 ===== */' in s, 'NI-8 must be in the file first'
def rep(s, old, new):
    n = s.count(old)
    assert n == 1, (old[:70], n)
    return s.replace(old, new)
# NI-5a's drawing (lane D's own code): the timing in the key, the class, the width, the label; the legend count
s = rep(s, "+':'+Math.round(c.s)+(c.duck?'d':'')).join('|')", "+':'+Math.round(c.s)+(c.duck?'d':'')+(c.turns?'t':c.gate?'g'+Math.round(c.gate.share*20):'')).join('|')")
s = rep(s, "wd=(1.4+4.6*clamp(c.s/36,0,1)).toFixed(2);", "wd=(c.turns?1.2:1.4+4.6*clamp(c.s*(c.gate?c.gate.share:1)/36,0,1)).toFixed(2);")
s = rep(s, 'class="nicc${c.duck?\' nidk\':\'\'}"', 'class="nicc${c.duck?\' nidk\':\'\'}${c.turns?\' nitn\':\'\'}"')
s = rep(s, "const tx=c.duck?`${c.b.name} ducks under ${c.a.name}, ${c.range}`:", "const tx=c.turns?`${c.a.name} and ${c.b.name} take turns, ${c.range}`:c.duck?`${c.b.name} ducks under ${c.a.name}, ${c.range}`:")
s = rep(s, "String(C.list.filter(c=>!c.duck).length)", "String(C.list.filter(c=>!c.duck&&!c.turns).length)")
s = rep(s, "Thicker means a bigger clash.", "Thicker means a bigger clash; a thin dashed cable means the two take turns inside the beat (kick and bass in a rolling bass), which is not counted.")
CSS = r"""/* lane D (task NI-5c): clashes that take turns, and the pair view in the clash card */
#mixWin svg.cabs .nicc.nitn{stroke-dasharray:2 4;opacity:.5}
#niClashPop .nicgv{display:flex;flex-direction:column;gap:3px;margin:2px 0 8px}#niClashPop .nicgv canvas{width:100%;height:64px;border-radius:4px;display:block;box-shadow:inset 0 0 0 1px rgba(255,255,255,.08)}
#niClashPop .nicgt{font-size:var(--fs1);color:var(--mut);font-variant-numeric:tabular-nums}#niClashPop .nicgt b{color:#f3c4ff}#niClashPop .nicgt.tn b{color:#4cc9f0}
"""
s = rep(s, ".dacv{display:flex;", CSS + ".dacv{display:flex;")
JS = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ni_5c_block.js'), encoding='utf-8').read()
A = '/* ===== end of lane D NI-8 ===== */'
s = rep(s, A, A + JS.rstrip('\n'))
open(P, 'w', encoding='utf-8').write(s)
print('NI-5c applied')
