"""Task NI-7b (lane D): X23 the gain staging check for the whole mix (AE3 pick, folded into I13 level journey).
Edit script with unique asserted anchors (needs NI-31 in the file: run ni_31.py first), so a rebase can re-run it on a fresh index.html.
  python3 tools/feature-lab/ni/ni_7b.py [index.html]
Adds (JS from ni_7b_block.js, after the NI-31 block):
  - a window "Gain staging" (#niGain, the app's fwin): every track that plays in NI-7's range (the loop or the 8 bars around the playhead)
    measured with NI-7's one-track render (taps after the clips or instrument, each device that is on, the fader and pan); one line per
    problem: hot (a peak over -1 dBFS before the fader, named by the device it goes into, with the amount to turn down), quiet into a
    level-sensitive device (under -30 dBFS into a compressor, drive, OTT, limiter...), barely heard (under -40 dBFS after the fader);
    a click selects the track, Journey opens its level journey
  - the master: its peak after its own chain (renderMixChunked, no safety limiter) as headroom; a problem over -1 dBFS without a limiter
  - measures again 0.8 s after an edit settles while stopped; nothing runs while closed; command ni.gainStaging, main menu entry,
    NI.gs, NI_HOOKS.gainStaging
"""
import sys, os
P = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
s = open(P, encoding='utf-8').read()
if '/* ===== lane D (task NI-7b)' in s:
    print('NI-7b already applied'); sys.exit(0)
assert '/* ===== end of lane D NI-31 ===== */' in s, 'NI-31 must be in the file first (python3 tools/feature-lab/ni/ni_31.py)'
def rep(s, old, new):
    n = s.count(old)
    assert n == 1, (old[:70], n)
    return s.replace(old, new)
IC = 'M4 16V9M8 16V5M12 16V8M16 16V3M2 6h18'
A1 = "{id:'ni.harmonicRuler',g:'view',"
s = rep(s, A1, "{id:'ni.gainStaging',g:'view',l:'Gain staging check (tracks too hot into their devices or too quiet, the master\\'s headroom)',d:'',ic:'%s',run:()=>NI_gsOpen()},\n " % IC + A1)
A2 = "   {label:NI_hrOn()?'Harmonic ruler: on'"
s = rep(s, A2, "   {label:'Gain staging…',sub:'tracks too hot into their devices or too quiet, the master\\'s headroom',ic:I('%s','#ffb547'),act:()=>NI_gsOpen()},\n" % IC + A2)
CSS = r"""/* lane D (task NI-7b): the gain staging check. dB on every number, amber for quiet, red for hot */
#niGain .fwb{flex-direction:column;gap:6px;padding:6px 10px 10px;overflow:auto}
#niGain .ngt{display:flex;align-items:center;gap:8px;flex-wrap:wrap;font-size:var(--fs1);color:var(--mut)}
#niGain .ngt button,#niGain .ngr button{min-height:22px;padding:0 8px;font-size:var(--fs1);white-space:nowrap}#niGain .ngst{margin-left:auto;font-variant-numeric:tabular-nums;white-space:nowrap}
#niGain .ngl{display:flex;flex-direction:column;gap:3px;font-size:var(--fs1)}
#niGain .ngr{display:grid;grid-template-columns:minmax(90px,1fr) minmax(160px,3fr) auto;gap:8px;align-items:center;padding:2px 6px;border-radius:4px;cursor:pointer;border-left:2px solid transparent}
#niGain .ngr:hover{background:rgba(255,255,255,.05)}#niGain .ngr.bad{border-left-color:#ff6b6b}#niGain .ngr.warn{border-left-color:#ffb547}
#niGain .ngn{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;color:var(--ink);display:flex;align-items:center;gap:5px}#niGain .ngn i{flex:none;width:9px;height:9px;border-radius:2px;background:var(--c)}
#niGain .ngw{color:var(--ink);font-variant-numeric:tabular-nums}#niGain .ngr.bad .ngw{color:#ff8f8f}#niGain .ngr.warn .ngw{color:#ffc46b}
#niGain .ngok{color:#4cc9f0}#niGain .ngempty{color:var(--mut)}
#niGain .ngm{font-size:var(--fs1);color:var(--ink);font-variant-numeric:tabular-nums}#niGain .ngnote{font-size:var(--fs1);color:var(--mut);line-height:1.35}
"""
s = rep(s, ".dacv{display:flex;", CSS + ".dacv{display:flex;")
JS = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ni_7b_block.js'), encoding='utf-8').read()
A3 = '/* ===== end of lane D NI-31 ===== */'
s = rep(s, A3, A3 + JS.rstrip('\n'))
open(P, 'w', encoding='utf-8').write(s)
print('NI-7b applied')
