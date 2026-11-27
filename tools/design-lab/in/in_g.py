"""Task IN-G (lane E, instruments): the dynamics displays, the user's picks G1 (gain reduction history), G3 (transfer curve with a live
point) and G4 (per-band gain reduction).
Edit script with unique asserted anchors, so a rebase can re-run it on a fresh index.html.
  python3 tools/design-lab/in/in_g.py [index.html]
Does:
  1. adds the IN-G block (in_g_block.js) before askChoice: INSG, INS.grh (the one G1 drawer), ingBar (the one G4 bar), ingComp, ingLimit,
     ingGate, ingDuck, ingOTT, ingMB, ingDeess
  2. Compressor (vizComp) and OTT (vizOTT) draw through the block (their bodies become one call; compGeo, the drag and COMPH stay)
  3. Limiter draw through ingLimit; Gate's history through ingGate (its lines, OPEN mark and envelope stay); Ducker's history through
     ingDuck (its text and trigger colour stay); Multiband's GR meter and the De-Esser's reduction panel through ingMB and ingDeess
  4. the gate's, de-esser's and ducker's display history keeps 4 s (400 messages of 512 samples) instead of 2 (display arrays only)
"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
P = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
s = open(P, encoding='utf-8').read()
if '/* ===== lane E (task IN-G)' in s:
    print('IN-G already applied'); sys.exit(0)
assert '/* ===== end of lane E IN-E' in s or 'lane E (task IN-E)' in s, 'IN-E must be in first'

def rep(s, old, new, n=1):
    c = s.count(old)
    assert c == n, (old[:90], c, n)
    return s.replace(old, new)

def cut(s, start, end, new, keep_end=True):
    """replace the text from start up to end (end kept when keep_end) by new; start and end unique"""
    assert s.count(start) == 1, ('start', start[:90], s.count(start))
    i = s.index(start)
    j = s.index(end, i)
    assert s.count(end) >= 1
    return s[:i] + new + (s[j:] if keep_end else s[j + len(end):])

# 2. Compressor and OTT
s = cut(s, "function vizComp(g,w,h,f,X){\n  g.fillStyle='#07070a';g.fillRect(0,0,w,h);const p=f.p,G=compGeo(w,h)",
        "\nfunction delayTime(p){", "function vizComp(g,w,h,f,X){ingComp(g,w,h,f,X)}/* IN-G: G3 and G1, block 'lane E (task IN-G)' */")
s = cut(s, "function vizOTT(g,w,h,f,X){const p=f.p,cols=['#ff6b6b','#f5c84c','#4cc9f0'],labs=['LOW','MID','HIGH'],bw=(w-40)/3;",
        "g.fillText('depth '+Math.round(p.depth)+'%',w-60,7)}", "function vizOTT(g,w,h,f,X){ingOTT(g,w,h,f,X)}/* IN-G: G4 */", keep_end=False)

# 3. Limiter
s = cut(s, " draw:(g,w,h,f,X)=>{const p=f.p;vbg(g,w,h);const T=10,Bm=h-12,dbY=db=>T+(1-clamp((db+30)/33,0,1))*(Bm-T),GX=26,GW=w-26-58;",
        "\n hnd:(p,w,h)=>{const T=10,Bm=h-12,dbY=", " draw:(g,w,h,f,X)=>ingLimit(g,w,h,f,X),/* IN-G: G1 */")
# Gate: the history part
s = cut(s, "for(const db of[-72,-60,-48,-36,-24,-12,0]){lineH(g,Yd(db),SW,'rgba(255,255,255,.055)');txt(g,db+'',3,Yd(db)-2,'rgba(255,255,255,.28)',8)}",
        "g.strokeStyle='#ff9a3c';g.lineWidth=1.5;g.stroke()}", "const H=X?X.H:[],n=H.length;ingGate(g,SW,T,Bm,X,p);/* IN-G: G1 */", keep_end=False)
s = rep(s, "mode:p.mode,listen:!!p.listen});x.H=[];x.onmsg=m=>{x.H.push(m);if(x.H.length>200)x.H.shift()};return x},\n draw:(g,w,h,f,X)=>{const p=f.p;vbg(g,w,h);const T=10,Bm=h-14,SW=w-170",
        "mode:p.mode,listen:!!p.listen});x.H=[];x.onmsg=m=>{x.H.push(m);if(x.H.length>400)x.H.shift()};return x},/* IN-G: 4 s of display history */\n draw:(g,w,h,f,X)=>{const p=f.p;vbg(g,w,h);const T=10,Bm=h-14,SW=w-170")
# Ducker
s = cut(s, "  if(H&&live){const st=w/(n-1);g.fillStyle=sc;g.globalAlpha=.55;",
        "  {const y=Math.round(yDb(+f.p.th||-30))+.5;", "  const r=ingDuck(g,w,T,B,X,live,sc);/* IN-G: G1 (trigger in its colour, the reduction in red on the same dB scale) */\n")
s = rep(s, "g.fillStyle=dc;const tx=(t?t.name:'')+' '+(gr>.05?'−'+gr.toFixed(1)+' dB':'0.0 dB');g.textAlign='right';g.fillText(tx,w-4,2);g.textAlign='left'}",
        "g.fillStyle=dc;const tx=(t?t.name:'')+' '+(gr>.05?'−'+gr.toFixed(1)+' dB':'0.0 dB');g.textAlign='right';g.fillText(tx,w-4,2);g.textAlign='left';if(r){g.font='6.5px '+INS.look().mono;g.fillStyle=INS.look().mut;g.textAlign='right';g.fillText('max '+INS.num(Math.min(0,r.mx),1)+' in 4 s',w-14,T+2);g.textAlign='left'}}")
s = rep(s, "H:{k:new Float32Array(200),g:new Float32Array(200).fill(1),i:0}", "H:{k:new Float32Array(400),g:new Float32Array(400).fill(1),i:0}/* IN-G: 4 s */")
# Multiband
s = cut(s, "/* GR sum meter */const gx=PW+20;txt(g,'GAIN REDUCTION',gx-6,T-4,'rgba(255,255,255,.4)',8);",
        "txt(g,red>.1?red.toFixed(1):'0',gx+b*28+9,B+11,c2,8,'center')}", "/* IN-G: G4 */ingMB(g,w,h,T,B,PW,p,X,ms,nb,f.id)", keep_end=False)
# De-Esser
s = cut(s, "  const H=X?X.H:[],n=H.length,last=H[n-1],gr=last?last.gr:0,hx0=PW+14,hw=w-hx0-10,hh=B-T;",
        "txt(g,gr>.1?'-'+gr.toFixed(1)+' dB':'0 dB',hx0+hw/2,B+12,gr>.3?'#ff6b6b':'rgba(255,255,255,.5)',10,'center');",
        "  const H=X?X.H:[],n=H.length,last=H[n-1],gr=last?last.gr:0;ingDeess(g,w,h,T,B,PW,p,X,H,f.id);/* IN-G: G4 */g.fillStyle=gr>.3?'#ff6b6b':'#3ecf8e';glow(g,g.fillStyle,gr>.3?10:0);g.beginPath();g.arc(PW-12,T+10,5,0,7);g.fill();g.shadowBlur=0;", keep_end=False)
s = rep(s, "mode:p.mode,listen:!!p.listen});const an=c.createAnalyser();an.fftSize=4096;x.in.connect(an);x.an=an;x.H=[];x.onmsg=m=>{x.H.push(m);if(x.H.length>200)x.H.shift()};return x},",
        "mode:p.mode,listen:!!p.listen});const an=c.createAnalyser();an.fftSize=4096;x.in.connect(an);x.an=an;x.H=[];x.onmsg=m=>{x.H.push(m);if(x.H.length>400)x.H.shift()};return x},/* IN-G: 4 s of display history */")

# 1. the block
js = open(os.path.join(HERE, 'in_g_block.js'), encoding='utf-8').read()
s = rep(s, "function askChoice(title,text,btns,icon){", js + "function askChoice(title,text,btns,icon){")
open(P, 'w', encoding='utf-8').write(s)
print('IN-G applied')
