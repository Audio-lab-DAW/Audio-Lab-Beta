"""Task NI-8 (lane D): I4 mono-loss map.
Edit script with unique asserted anchors (needs NI-7 in the file), so a rebase can re-run it on a fresh index.html.
  python3 tools/feature-lab/ni/ni_8.py [index.html]
Adds (JS from ni_8_block.js, after the NI-7 block):
  - a window "Mono loss" (#niMono, the app's fwin): one row per track that plays in the range, a band strip 20 Hz to 20 kHz coloured by
    how much level that track loses in mono in each 1/6-octave band (from NI-3's per-beat mid and side bands: loss = mid / (mid + side)),
    faint where the band is quiet for that track; the whole track's loss in dB; the worst stretch in words ("-7 dB at 200 to 800 Hz")
  - tracks that cancel each other in mono joined by a line, with a sentence each: the 8 loudest tracks of the range rendered offline on
    their own (NI-7's one-track render with a tap after fader and pan, 22.05 kHz, at most 8 bars) and compared pair by pair per 1/3 octave
    in a worker (mono sum of the pair at least 3 dB under the sum of their powers, both within 15 dB); says whether stereo cancels too
  - range: the loop or the 8 bars around the playhead (as NI-7), or the whole song (switch); measures again 0.8 s after an edit settles
    while stopped; nothing runs while closed
  - "Hear in mono" (the master strip's Mono switch), a "Loss" button next to Mono on the master strip (a one-line hook in the mixer's
    render: NI_HOOKS.mxMon(w)), command ni.monoLoss, main menu entry, NI_HOOKS.monoLoss
  - NI_jourRender (NI-7, lane D) learns taps.raw (return the tapped channels) and taps.sr (render rate)
"""
import sys, os
P = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
s = open(P, encoding='utf-8').read()
MARK = '/* ===== lane D (task NI-8)'
if MARK in s:
    print('NI-8 already applied'); sys.exit(0)
assert '/* ===== end of lane D NI-7 ===== */' in s, 'NI-7 must be in the file first'

def rep(s, old, new):
    n = s.count(old)
    assert n == 1, (old[:70], n)
    return s.replace(old, new)

# 1. the command, after ni.levelJourney
A1 = "run:()=>NI_jourOpen()},"
s = rep(s, A1, A1 + "\n {id:'ni.monoLoss',g:'view',l:'Mono loss map (what each track loses in mono, band by band)',d:'',ic:'M3 12h4l3-7 4 14 3-7h4',run:()=>NI_mlOpen()},")

# 2. the main menu, after the level journey
A2 = "act:()=>NI_jourOpen()},"
s = rep(s, A2, A2 + "\n   {label:'Mono loss…',sub:'what each track loses in mono, and which tracks cancel',ic:I('M3 12h4l3-7 4 14 3-7h4','#4cc9f0'),act:()=>NI_mlOpen()},")

# 3. the mixer's render: one hook call after monPaint() (the master strip's Mono, Dim, L/R row)
A3 = '</div><div class="mxb"></div></div></div>`;monPaint();'
s = rep(s, A3, A3 + "try{NI_HOOKS.mxMon&&NI_HOOKS.mxMon(w)}catch(e){}")

# 4. NI-7's one-track render: a render rate and the raw tapped channels on request
s = rep(s, "async function NI_jourRender(t,b0,b1,steps,taps){const sr=NI_JOUR_SR,", "async function NI_jourRender(t,b0,b1,steps,taps){const sr=taps.sr||NI_JOUR_SR,")
A4 = "const buf=await oc.startRendering(),skip=Math.round(secSpan(bs,b0)*sr),out=[];"
s = rep(s, A4, A4 + "if(taps.raw)return{L:buf.getChannelData(0).slice(skip),R:buf.getChannelData(1).slice(skip),sr};")

# 5. CSS
CSS = r"""/* lane D (task NI-8): the mono-loss map. Instrument look: drafting grid, dB on every number, loss colours cyan, grey, amber, red */
#niMono .fwb{flex-direction:column;gap:6px;padding:6px 10px 10px;overflow:auto}
#niMono .nmt{display:flex;align-items:center;gap:8px;flex-wrap:wrap;font-size:var(--fs1);color:var(--mut)}
#niMono .nmt button{min-height:22px;padding:0 8px;font-size:var(--fs1)}#niMono .nmt button.on{background:#f5c84c;color:#1a1400;border-color:#f5c84c}
#niMono .nmt label{display:flex;align-items:center;gap:4px;cursor:pointer}#niMono .nmst{margin-left:auto;font-variant-numeric:tabular-nums;white-space:nowrap}
#niMono .nmk{display:flex;align-items:center;gap:4px 6px;flex-wrap:wrap;font-size:var(--fs1);color:var(--mut)}#niMono .nmk i{width:10px;height:10px;border-radius:2px;background:rgb(var(--k));margin-left:4px}#niMono .nmk span{margin-left:auto;opacity:.8}
#niMono .nmg{position:relative;display:grid;grid-template-columns:14px minmax(80px,1fr) minmax(160px,2.6fr) 58px minmax(120px,1.6fr);gap:3px 8px;align-items:center;font-size:var(--fs1)}
#niMono .nmh{color:var(--mut)}#niMono .nmh.r,#niMono .nmn{text-align:right}
#niMono .nmsc{position:relative;height:13px}#niMono .nmsc span{position:absolute;top:0;transform:translateX(-50%);font:var(--fw5) 9px/13px var(--ffu);color:var(--mut);font-variant-numeric:tabular-nums}
#niMono .nmj{height:14px}
#niMono .nmnm{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;color:#d9dce3;display:flex;align-items:center;gap:5px;cursor:pointer}#niMono .nmnm i{flex:none;width:9px;height:9px;border-radius:2px;background:var(--c)}
#niMono .nmb{height:14px;border-radius:2px;background-color:#05070b;cursor:pointer;box-shadow:inset 0 0 0 1px rgba(255,255,255,.06)}
#niMono .nmn{font-variant-numeric:tabular-nums;color:#cfe6ff;white-space:nowrap}#niMono .nmn.warn,#niMono .nmw.warn{color:#ffb547}#niMono .nmn.bad,#niMono .nmw.bad{color:#ff6b6b}
#niMono .nmw{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;color:var(--mut)}#niMono .nmw.ok{color:#4cc9f0}
#niMono .nmline{position:absolute;width:6px;border:1.5px solid #ffb547;border-right:0;border-radius:3px 0 0 3px;pointer-events:auto;box-sizing:border-box}#niMono .nmline.bad{border-color:#ff6b6b}
#niMono .nmp{display:flex;flex-direction:column;gap:2px;font-size:var(--fs1)}#niMono .nmpn{color:var(--mut)}#niMono .nmpr{color:#ffb547;cursor:pointer}#niMono .nmpr:hover{text-decoration:underline}
#niMono .nmempty{grid-column:1/-1;color:var(--mut)}#niMono .nmnote{font-size:var(--fs1);color:var(--mut);line-height:1.35}
"""
s = rep(s, ".dacv{display:flex;", CSS + ".dacv{display:flex;")

# 6. JS after NI-7
JS = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ni_8_block.js'), encoding='utf-8').read()
A6 = '/* ===== end of lane D NI-7 ===== */'
s = rep(s, A6, A6 + JS.rstrip('\n'))
open(P, 'w', encoding='utf-8').write(s)
print('NI-8 applied')
