#!/usr/bin/env python3
"""Task DS-A4 (lane A, design round 2, detail AW3 of look A5): audio clips in three bands.
   python3 tools/design-lab/ds/ds_a4.py index.html
Lows (2-pole low-pass 200 Hz) in muted blue, mids (2-pole band-pass 200 Hz to 2.5 kHz) in muted amber, highs
(2-pole high-pass 2.5 kHz) in white, each the peak of its band, drawn
from the clip's centre line, lows first and highs on top (as the pick page's arrWave with w:3). Stereo files keep their
two halves. The analysis runs once per audio buffer (and per warped buffer), in slices of about 6 ms off the drawing
path, at the resolution of the buffer's existing peaks; it is kept with those peaks (WeakMap, freed with them). The
picture goes into the existing per-clip cache (drawClipC), which is keyed by size and zoom, so a zoom or a clip change
redraws from the stored analysis and nothing runs per frame. Until the analysis is ready, and in the other looks
(Live, FL, Cubase, Logic, Bitwig ...), today's waveform is drawn. No audio nodes: playback and export do not change.
Needs task DS-A3 (dsAC3). Every anchor is asserted. Re-run on a fresh file after a rebase."""
import sys
F = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
s = open(F, encoding='utf-8').read()
assert 'task DS-A4' not in s, 'already applied'
assert 'function dsAC3()' in s, 'needs task DS-A3'

def rep(old, new, n=1):
    global s
    c = s.count(old)
    assert c == n, (c, n, old[:120])
    s = s.replace(old, new)

BLOCK = r"""/* task DS-A4 (lane A, design round 2, AW3): audio clips in three bands, lows, mids and highs (peak of each band per bin).
   dsBands(view) gives the analysis of the buffer behind a clip, or null while it is being worked out (once per buffer, in
   slices of about 6 ms, never inside a drawing); dsWaveDraw draws it into the clip's cached picture. */
const DSW_COL=['rgba(88,120,200,.62)','rgba(206,156,84,.66)','rgba(236,236,241,.75)'],DSW_FC=[200,2500];
function dsBandMap(){return dsBandMap.m||(dsBandMap.m=new WeakMap())}
function dsBands(V0){if(!V0||!V0.buf||!V0.peaks)return null;const M=dsBandMap(),P=V0.peaks;let e=M.get(P);if(e)return e.ok?e:null;
  e={ok:false,t0:performance.now()};M.set(P,e);dsBandJob(V0.buf,P.length/2,e);return null}
function dsBandJob(buf,N,e){const nc=Math.min(2,buf.numberOfChannels),ch=[];for(let k=0;k<nc;k++)ch.push(buf.getChannelData(k));
  const len=buf.length,sr=buf.sampleRate,aL=1-Math.exp(-2*Math.PI*DSW_FC[0]/sr),aH=1-Math.exp(-2*Math.PI*DSW_FC[1]/sr),out=ch.map(()=>new Float32Array(N*3)),st=ch.map(()=>new Float64Array(7)),per=N/len;let j=0;e.n=0;
  const run=()=>{const t0=performance.now();e.n++;
    while(j<len&&performance.now()-t0<6){const end=Math.min(len,j+32768);
      for(let k=0;k<nc;k++){const d=ch[k],o=out[k],s=st[k];let l1=s[0],l2=s[1],q1=s[2],m1=s[3],m2=s[4],h1=s[5],h2=s[6];
        /* three separate 2-pole bands (no differences of filters with different phase): low-pass 200 Hz; high-pass 200 Hz then
           low-pass 2.5 kHz; high-pass 2.5 kHz */
        for(let i=j;i<end;i++){const x=d[i];l1+=aL*(x-l1);l2+=aL*(l1-l2);const p1=x-l1;q1+=aL*(p1-q1);const p2=p1-q1;m1+=aH*(p2-m1);m2+=aH*(m1-m2);
          h1+=aH*(x-h1);const r1=x-h1;h2+=aH*(r1-h2);
          const b=Math.min(N-1,(i*per)|0)*3,lo=Math.abs(l2),mi=Math.abs(m2),hi=Math.abs(r1-h2);if(lo>o[b])o[b]=lo;if(mi>o[b+1])o[b+1]=mi;if(hi>o[b+2])o[b+2]=hi}
        s[0]=l1;s[1]=l2;s[2]=q1;s[3]=m1;s[4]=m2;s[5]=h1;s[6]=h2}j=end}
    if(j<len){setTimeout(run,0);return}
    e.ch=out;e.mono=nc===1?out[0]:out[0].map((v,i)=>Math.max(v,out[1][i]));e.ms=performance.now()-e.t0;e.ok=true;try{CLC.clear()}catch(_){}dirty=true};
  setTimeout(run,0)}
function dsBandCols(g,c,full,A,x,y,w,h,ga,xmax){const N=A.length/3,mid=y+h/2,i0=Math.max(0,Math.floor(-x)),i1=Math.min(Math.ceil(w),Math.ceil(xmax-x));if(i1<=i0)return;
  for(let b=0;b<3;b++){g.fillStyle=DSW_COL[b];
    for(let i=i0;i<i1;i++){const t0=(c.off+i/w*c.len)/full*N,t1=(c.off+(i+1)/w*c.len)/full*N;let k=Math.max(0,Math.floor(t0));const ke=Math.min(N,Math.max(k+1,Math.ceil(t1)));if(k>=N)break;
      let v=0;for(;k<ke;k++){const q=A[3*k+b];if(q>v)v=q}const a=Math.min(1,v*ga);if(a>.002)g.fillRect(x+i,mid-a*h/2,1,Math.max(.5,a*h))}}}
function dsWaveDraw(g,c,G,w,col){const V0=srcView(c);if(!V0)return false;const D=dsBands(V0);if(!D)return false;
  const st=D.ch.length===2&&G.bh>=30,ga=Math.pow(10,(c.gain||0)/20),d=(window.devicePixelRatio||1)*ZOOM;g.fillStyle='rgba(255,255,255,.14)';
  if(st){const hh=(G.bh-4)/2;g.fillRect(G.x,Math.round((G.by+1+hh/2)*d)/d,G.w,1/d);g.fillRect(G.x,Math.round((G.by+1+hh*1.5)*d)/d,G.w,1/d);
    dsBandCols(g,c,V0.full,D.ch[0],G.x,G.by+1,G.w,hh,ga,w);dsBandCols(g,c,V0.full,D.ch[1],G.x,G.by+1+hh,G.w,hh,ga,w)}
  else{g.fillRect(G.x,Math.round((G.by+G.bh/2)*d)/d,G.w,1/d);dsBandCols(g,c,V0.full,D.mono,G.x,G.by+2,G.w,G.bh-4,ga,w)}
  return true}
"""
rep('function askChoice(title,text,btns,icon){', BLOCK + 'function askChoice(title,text,btns,icon){')

# drawClip: the three bands in the AudioLab look once the analysis is ready, else today's waveform
rep("  else if(srcView(c)){const P=srcView(c).peaks,st=P.ch&&P.ch.length===2&&G.bh>=30;",
    "  else if(DS3&&dsWaveDraw(g,c,G,w,col)){}\n  else if(srcView(c)){const P=srcView(c).peaks,st=P.ch&&P.ch.length===2&&G.bh>=30;")

open(F, 'w', encoding='utf-8').write(s)
print('task DS-A4 applied to', F)
