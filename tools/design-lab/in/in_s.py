"""Task IN-S (lane E, instruments): the spectrum, the user's pick S2 (the analyzer front panel).
Edit script with unique asserted anchors, so a rebase can re-run it on a fresh index.html.
  python3 tools/design-lab/in/in_s.py [index.html]
Does:
  1. adds the IN-S block (in_s_block.js) before askChoice: INS.spec (the one front-panel drawer), INS.an (an analyser's FFT size and
     smoothing set in one place), INS.rbw, INS.avgOf, INS.smooth; the overlay's spectrum module (ANZD.spec) and the Visualizer's spectrum
     (VZD.fft) through the drawer; insMxSpecTicks (decade marks on the mixer's spec view)
  2. the Spectrum device (ND('spec')) draws through the drawer (its Top, Floor, Slope and Smoothing dots, presets, FFT size, Peak hold,
     Hold ref and Clear ref stay); its FFT size goes through INS.an
  3. the overlay's and the Visualizer's analysers are sized through INS.an
  4. the mixer's spec view gets the decade marks (its bars, colours, mirror and caps stay)
"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
P = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
s = open(P, encoding='utf-8').read()
if '/* ===== lane E (task IN-S)' in s:
    print('IN-S already applied'); sys.exit(0)
assert '/* ===== end of lane E IN-A' in s, 'IN-A must be in first'

def rep(s, old, new, n=1):
    c = s.count(old)
    assert c == n, (old[:80], c, n)
    return s.replace(old, new)

def cut(s, a, b, new):
    """replace from the unique start a up to (not including) the unique end b that follows it"""
    assert s.count(a) == 1, ('start', a[:70], s.count(a))
    i = s.index(a); j = s.index(b, i); assert s.count(b) == 1, ('end', b[:70], s.count(b))
    return s[:i] + new + s[j:]

# 2. the Spectrum device
s = cut(s, "for(let db=Math.ceil(p.floor/12)*12;db<=p.top;db+=12){const y=Yd(db);lineH(g,y,w,'rgba(255,255,255,.05)');",
        " hnd:(p,w,h)=>[{x:w-12,y:14,c:'#4cc9f0',l:'Top'",
        "void a0;void ah;void Yd;/* IN-S: S2, the analyzer front panel (Top is the reference level on the top line, Floor the bottom, Slope the tilt, Smoothing the averaging time, Peak fall the hold's fall) */\n"
        "  INS.spec(g,0,0,w,h,{tr:[{an:X.an,col:INS.SPC.c1,hold:!!p.peak,fall:(+p.decay||0)*60,avg:INS.smooth(p.smooth),st:X.st}],lo,hi,top:p.top,bot:p.floor,tilt:p.slope,ref:X.ref,padL:4,padR:26,st:X.sp||(X.sp={})})},\n")
s = rep(s, "set(p){const n=+p.fft||8192;if(an.fftSize!==n)an.fftSize=n}}},", "set(p){INS.an(an,+p.fft||8192)}}},/* IN-S: sized in one place */")
# 3. analysers
s = rep(s, "const an=ctx.createAnalyser();an.fftSize=8192;an.smoothingTimeConstant=.82;an.minDecibels=-100;",
        "const an=INS.an(ctx.createAnalyser(),8192,.82);an.minDecibels=-100;")
s = rep(s, "VZ.an=ctx.createAnalyser();VZ.an.fftSize=4096;VZ.an.smoothingTimeConstant=.55;",
        "VZ.an=INS.an(ctx.createAnalyser(),4096,.55);")
# 3b. the Visualizer's Light level: twice the normal gate (33 ms against 20 gave the same rate on a 60 Hz screen)
s = rep(s, "if(now-VZ.last<(UI.lite?33:20))return;", "if(now-VZ.last<(UI.lite?40:20))return;/* IN-S: the Light level at half rate */")
# 4. the mixer's spec view
s = rep(s, "else g.fillRect(3+cw,y+1,1.5,H/bars-1.5)}}g.globalAlpha=1}}",
        "else g.fillRect(3+cw,y+1,1.5,H/bars-1.5)}}g.globalAlpha=1;insMxSpecTicks(g,W,H,an)/* IN-S */}}")

# 1. the block
js = open(os.path.join(HERE, 'in_s_block.js'), encoding='utf-8').read()
s = rep(s, "function askChoice(title,text,btns,icon){", js + "function askChoice(title,text,btns,icon){")
open(P, 'w', encoding='utf-8').write(s)
print('IN-S applied')
