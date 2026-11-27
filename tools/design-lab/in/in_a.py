"""Task IN-A (lane E, instruments): the shared instrument base.
Edit script with unique asserted anchors, so a rebase can re-run it on a fresh index.html.
  python3 tools/design-lab/in/in_a.py [index.html]
Does:
  1. adds the INS module (in_a_block.js; colour maps filled from tools/design-lab/dr4/cmaps.txt) before askChoice
  2. every analyser frequency read goes through INS.fft / INS.fftB (one read per analyser per frame)
  3. the level meter's "Loudness" reading (peak, RMS and VU untouched) is now K-weighted (BS.1770, 400 ms window,
     only the samples new since the last frame, filter state kept), scaled so a sound in both channels reads the LUFS of the loudness box
  4. the two `function vizSide` declarations: the Visualizer's layout helper becomes vizDockSide, so the Sidechain device gets its picture back
"""
import sys, os, re
HERE = os.path.dirname(os.path.abspath(__file__))
P = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
s = open(P, encoding='utf-8').read()
MARK = '/* ===== lane E (task IN-A)'
if MARK in s:
    print('IN-A already applied'); sys.exit(0)

def rep(s, old, new, n=1):
    c = s.count(old)
    assert c == n, (old[:70], c, n)
    return s.replace(old, new)

# 2. analyser frequency reads (before the block goes in, since the block itself calls the native methods)
pat = re.compile(r'(\b[\w$]+(?:\.[\w$]+)?)\.get(Float|Byte)FrequencyData\(')
hits = pat.findall(s)
assert len(hits) == 13, ('frequency reads', len(hits), hits)
s = pat.sub(lambda m: 'INS.fft%s(%s,' % ('' if m.group(2) == 'Float' else 'B', m.group(1)), s)

# 3. the meter engine
s = rep(s, "  else{let q=0;for(let i=n-k;i<n;i++)q+=a[i]*a[i];q/=k;const T=MTRWIN[o.alg]",
           "  else if(o.alg==='lufs'){/* IN-A: K-weighted (ITU-R BS.1770) over a 400 ms window of only the new samples; +3.01 dB so a sound in both channels reads the LUFS the loudness box shows */"
           "const q=INS.kms(st.kw||(st.kw={}),a,INS.fresh(a,st.kw,dt*sr),n,sr);st.ss=q;db=q>1e-12?10*Math.log10(q)-.691+3.0103:-90}\n"
           "  else{let q=0;for(let i=n-k;i<n;i++)q+=a[i]*a[i];q/=k;const T=MTRWIN[o.alg]")
s = rep(s, "lufs:'Loudness averages over 400 ms (momentary).'",
           "lufs:'Loudness is K-weighted like the loudness meter (ITU-R BS.1770), over 400 ms (momentary): a sound in both channels reads the LUFS the loudness box shows.'")

# 4. vizSide twice
s = rep(s, "vizSide()", "vizDockSide()", 4)
s = rep(s, "clearTimeout(vizSide.t);vizSide.t=setTimeout(vizSide,60)", "clearTimeout(vizDockSide.t);vizDockSide.t=setTimeout(vizDockSide,60)")
assert s.count('function vizSide(') == 1 and s.count('function vizDockSide(') == 1

# 1. the block
js = open(os.path.join(HERE, 'in_a_block.js'), encoding='utf-8').read()
cm = dict(l.strip().split('|') for l in open(os.path.join(HERE, '..', 'dr4', 'cmaps.txt')) if '|' in l)
for k in ('magma', 'inferno', 'viridis'):
    assert len(cm[k]) == 384, k
    js = js.replace('@%s@' % k.upper(), cm[k])
assert '@' not in js.split('CMH:')[1].split('}')[0]
s = rep(s, "function askChoice(title,text,btns,icon){", js + "function askChoice(title,text,btns,icon){")
open(P, 'w', encoding='utf-8').write(s)
print('IN-A applied')
