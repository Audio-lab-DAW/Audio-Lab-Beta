/* ===== lane E (task IN-S): the spectrum, the user's pick S2 (the analyzer front panel) =====
   One drawer, INS.spec, laid out like a bench spectrum analyzer (Keysight, Rohde & Schwarz): a 10 by 10 graticule with the reference level on
   the top line, the dB per division beside it, start and stop frequency, resolution bandwidth, averaging and detector in the corners;
   trace 1 is the live trace (yellow, "clear/write"), trace 2 the max hold (cyan); marker 1 sits on the strongest peak, the delta marker on the
   next one, with the difference in frequency and level. Used by the Spectrum device (ND('spec')), the analyser overlay's spectrum module, and
   the Visualizer's spectrum; the mixer's spec view keeps its bars (a strip is too narrow for a panel) and gets decade marks on its edge.
   - Reads: INS.fft (one analyser read per analyser per frame, IN-A). The detector is positive peak: each pixel column takes the highest bin in
     its frequency span (bins closer than a pixel), or the level between the two nearest bins (bins wider than a pixel).
   - Averaging is by time, not by frame (the same at 60 or 120 frames a second, and at the Light level's half rate): AVG is the time
     constant in seconds, including the analyser's own smoothing where the caller keeps one (INS.avgOf).
   - RBW is the noise bandwidth of the analyser's window: Web Audio applies a Blackman window (1.73 bins), so RBW = 1.73 x rate / FFT size.
   - INS.an sets an analyser's FFT size and smoothing in one place, only when they change (a change clears the analyser's history).
   - Nothing new in the audio path. Drawn only when the callers draw (on screen, not hidden, not in the background freeze). */
INS.an=function(an,n,sm){if(!an)return an;if(n&&an.fftSize!==n)an.fftSize=n;if(sm!=null&&Math.abs(an.smoothingTimeConstant-sm)>1e-6)an.smoothingTimeConstant=sm;return an};
INS.ENBW=1.73;/* Blackman window (what AnalyserNode uses), noise bandwidth in bins */
INS.SPCAL=20*Math.log10(2/.42);/* 13.56 dB: the analyser reads a sine 20 log(0.42 / 2) under its peak (the Blackman window's coherent gain, one side); added so a sine reads its peak level in dBFS, as on the pick page */
INS.rbw=(an,sr)=>INS.ENBW*(sr||(typeof ctx==='object'&&ctx?ctx.sampleRate:48000))/(an&&an.fftSize||8192);
INS.avgOf=function(an,dt){/* the time constant (s) of the analyser's own smoothing at this read interval: X = s X' + (1 - s) |X| per read */const s=an&&an.smoothingTimeConstant||0;return s>0&&s<1&&dt>0?-dt/Math.log(s):0};
INS.smooth=s=>{/* the Spectrum device's Smoothing (%, the share of the last frame kept at 60 frames a second) as a time constant in s */const f=Math.min(.999,Math.max(0,(+s||0)/100));return f>0?-1/(60*Math.log(f)):0};
INS.SPC={c1:'#f5c84c',c2:'rgba(76,201,240,.7)',ref:'rgba(255,154,60,.8)',frame:'rgba(255,255,255,.22)',mk:'#ffffff'};/* today's colours: yellow live, cyan hold, orange reference */
INS._segs=function(g,parts,x,y,al){/* text in pieces of its own colour (numbers ink, units amber: L2), aligned as one string */let w=0;for(const p of parts)w+=g.measureText(p[0]).width;let xx=al==='right'?x-w:al==='center'?x-w/2:x;g.textAlign='left';for(const p of parts){g.fillStyle=p[1];g.fillText(p[0],xx,y);xx+=g.measureText(p[0]).width}return w};
INS._spU=function(v,u,L,o){/* a value and its unit as coloured pieces: ' 1.00', ' kHz' */const[a,b]=INS.parts(v,u,o||{});return[[a,L.ink],[b?' '+b:'',L.unit]]};
INS._spCol=function(D,m,c){/* the positive-peak detector of one column, in the analyser's dB */const n=D.length,i0=m.b0[c],i1=m.b1[c];if(i1>i0){let v=-1e9;for(let i=i0;i<=i1;i++)if(D[i]>v)v=D[i];return v}const f=m.fr[c],x0=D[i0],x1=D[Math.min(n-1,i0+1)];return x0>-1e9&&x1>-1e9?x0+(x1-x0)*f:Math.max(x0,x1)};
INS._spTr=function(t,an,map,tilt,o,now){/* one trace: read, detect, average, hold; t.sm (averaged dB, tilt included) and t.mh (held) per column */
  const D=INS.fft(an),n=D.length,gw=map.n,first=!t.sm||t.sm.length!==gw;let dt=t.tt?(now-t.tt)/1000:0;t.tt=now;
  if(first||dt>1){t.sm=new Float32Array(gw).fill(-240);t.mh=new Float32Array(gw).fill(-240);dt=0}dt=Math.min(.25,dt);t.dt=t.dt?t.dt*.9+dt*.1:dt;
  const avg=(o.avg||0)+(o.anAvg?INS.avgOf(an,t.dt||1/60):0),a=avg>0&&dt>0?Math.exp(-dt/avg):0,fall=o.fall||0,sil=o.sil==null?-150:o.sil,sm=t.sm,mh=t.mh;t.avgT=avg;
  if(map.bn!==n)INS._spMap(map,n);const B0=map.b0,B1=map.b1,FR=map.fr,TL=map.tl;
  void B0;void B1;void FR;for(let c=0;c<gw;c++){let v=INS._spCol(D,map,c);
    v=v>sil&&isFinite(v)?v+INS.SPCAL+tilt*TL[c]:-240;sm[c]=sm[c]<-200||!a?v:sm[c]*a+v*(1-a);if(sm[c]<-240)sm[c]=-240;mh[c]=Math.max(sm[c],fall>0?mh[c]-fall*dt:mh[c])}
  return t};
INS._spMap=function(m,n){/* pixel columns to bins, once per size, range, rate and FFT size */const gw=m.n,lo=m.lo,K=Math.log(m.hi/lo),bh=m.sr/2/n;m.bn=n;m.b0=new Int32Array(gw);m.b1=new Int32Array(gw);m.fr=new Float32Array(gw);m.tl=new Float32Array(gw);
  for(let c=0;c<gw;c++){const fa=lo*Math.exp(K*c/gw),fb=lo*Math.exp(K*(c+1)/gw),fc=Math.sqrt(fa*fb),ba=fa/bh,bb=fb/bh;m.tl[c]=Math.log2(fc/1000);
    if(bb-ba>=1){m.b0[c]=Math.max(1,Math.min(n-1,Math.round(ba)));m.b1[c]=Math.max(m.b0[c],Math.min(n-1,Math.round(bb)-1))}else{const bc=Math.max(1,Math.min(n-1.001,fc/bh));m.b0[c]=m.b1[c]=Math.floor(bc);m.fr[c]=bc-Math.floor(bc)}}};
INS._spPk=function(D,m,c,tilt){/* a marker's frequency and level from the bins (a parabola through the highest bin and its neighbours, in dB): free of the window's scalloping */
  const n=D.length,bh=m.sr/2/n;let k=m.b0[c];for(let i=m.b0[c];i<=Math.max(m.b1[c],m.b0[c]+(m.b1[c]>m.b0[c]?0:1));i++)if(i<n&&D[i]>D[k])k=i;for(let s=0;s<3;s++){if(k>1&&D[k-1]>D[k])k--;else if(k<n-2&&D[k+1]>D[k])k++;else break}
  const a=D[Math.max(0,k-1)],b=D[k],e=D[Math.min(n-1,k+1)],dn=a-2*b+e;let p=0;if(isFinite(a)&&isFinite(e)&&dn<0)p=Math.max(-.5,Math.min(.5,.5*(a-e)/dn));const f=Math.max(1e-3,(k+p)*bh);return{f,v:b-.25*(a-e)*p+INS.SPCAL+tilt*Math.log2(f/1000)}};
INS.spec=function(g,x,y,w,h,o){/* the analyzer front panel in the box (x, y, w, h). o: tr [{an, col, hold, fall (dB/s, 0 = max hold), avg (s), anAvg, st, dash}] (the first is
   trace 1 and carries the markers), lo, hi (Hz), top (the reference level, dBFS), bot, tilt (dB/oct around 1 kHz), live (false: graticule only),
   ref (a held trace per column), padL, padR, size ('full', 'mid', 'mini'), st (the panel's own state). Returns {Y, map, mx (the highest point of trace 1), gx, gy, gw, gh}. */
  o=o||{};const L=INS.look(),C=INS.SPC,st=o.st||(o.st={}),lo=o.lo||20,hi=o.hi||20000,top=o.top==null?0:o.top,bot=o.bot==null?top-100:o.bot,rng=Math.max(1e-3,top-bot),tilt=o.tilt||0,now=performance.now();
  const sz=o.size||(h>=150&&w>=320?'full':h>=96&&w>=200?'mid':'mini'),fs=sz==='full'?7.5:7,hd=sz==='mini'?0:13,ft=sz==='full'?25:sz==='mid'?13:0;
  const gx=Math.round(x+(o.padL||0)),gy=Math.round(y+hd+(sz==='mini'?1:0)),gw=Math.max(8,Math.floor(w-(o.padL||0)-(o.padR||0))),gh=Math.max(8,Math.floor(h-hd-ft-(sz==='mini'?2:0))),Y=v=>gy+gh*(top-v)/rng;
  const sr=typeof ctx==='object'&&ctx?ctx.sampleRate:48000;let map=st.map;if(!map||map.n!==gw||map.lo!==lo||map.hi!==hi||map.sr!==sr)map=st.map={n:gw,lo,hi,sr,bn:-1};
  /* graticule: 10 by 10, the centre axes with five minor marks per division (IN-A's drawer, drafting levels, hairlines) */
  INS.graticule(g,gx,gy,gw,gh,{nx:10,ny:10});
  /* frequency marks inside the bottom line: decades long, 2 and 5 short, numbers at the decades */
  {const K=Math.log(hi/lo),fx=f=>gx+gw*Math.log(f/lo)/K,lw=INS.hair(g,L.lwLine);g.lineWidth=lw;g.strokeStyle=L.tick;g.beginPath();const labs=[];
    for(let d=1;d<=hi;d*=10)for(const m of[1,2,5]){const f=d*m;if(f<lo*1.001||f>hi*.999)continue;const xx=INS.px(g,fx(f)),k=m===1?4:2;g.moveTo(xx,gy+gh);g.lineTo(xx,gy+gh-k);if(m===1||(sz==='full'&&gw>520))labs.push([f,xx])}g.stroke();
    g.font=(fs-.5)+'px '+L.mono;g.textBaseline='bottom';g.textAlign='left';let last=-1e9;for(const[f,xx] of labs){const s=f>=1000?f/1000+'k':String(f),tw=g.measureText(s).width;if(xx+2<last+4||xx+2+tw>gx+gw-2)continue;g.fillStyle=f===100||f===1000||f===10000?L.lab:L.mut;g.fillText(s,xx+2,gy+gh-2);last=xx+2+tw}}
  /* traces */
  const T=o.tr||[],live=o.live!==false;let mx=-240;
  g.save();g.beginPath();g.rect(gx,gy,gw,gh);g.clip();
  if(o.ref&&o.ref.length===gw){g.beginPath();for(let c=0;c<gw;c++){const yy=Y(o.ref[c]);c?g.lineTo(gx+c+.5,yy):g.moveTo(gx+.5,yy)}g.strokeStyle=C.ref;g.setLineDash([4,3]);g.lineWidth=1.2;g.stroke();g.setLineDash([])}
  for(let k=T.length-1;k>=0;k--){const r=T[k];if(!r||!r.an)continue;const t=r.st||(r.st={});if(!live){t.tt=0;continue}INS._spTr(t,r.an,map,tilt,r,now);
    if(!k)for(let c=0;c<gw;c++)if(t.sm[c]>mx)mx=t.sm[c];
    if(r.hold){g.beginPath();let on=false;for(let c=0;c<gw;c++){const v=t.mh[c];if(v<-200){on=false;continue}const yy=Y(v);on?g.lineTo(gx+c+.5,yy):g.moveTo(gx+c+.5,yy);on=true}
      g.strokeStyle=r.col2||(k?r.col:C.c2);g.globalAlpha=k?.45:1;if(r.dash||k)g.setLineDash([2,3]);g.lineWidth=INS.hair(g,L.lwCurve);g.stroke();g.setLineDash([]);g.globalAlpha=1}
    g.beginPath();let on=false;for(let c=0;c<gw;c++){const v=t.sm[c];if(v<-200){on=false;continue}const yy=Y(v);on?g.lineTo(gx+c+.5,yy):g.moveTo(gx+c+.5,yy);on=true}
    g.strokeStyle=r.col||C.c1;g.lineWidth=k?1:Math.max(1,L.lwCurve);g.globalAlpha=k?.85:1;g.stroke();g.globalAlpha=1}
  g.restore();
  /* the frame */
  g.lineWidth=INS.hair(g,L.lwLine);g.strokeStyle=C.frame;g.strokeRect(INS.px(g,gx),INS.px(g,gy),Math.round(gw),Math.round(gh));
  /* markers: 1 on the strongest peak of trace 1, delta 2 on the next local maximum at least 3 % of the width away */
  const t0=T[0]&&T[0].st,mk=st.mk||(st.mk={});mk.a=mk.b=-1;
  if(live&&t0&&t0.sm&&t0.sm.length===gw){const sm=t0.sm,K=Math.log(hi/lo),fc=c=>lo*Math.exp(K*(c+.5)/gw),c0=Math.max(0,Math.ceil(gw*Math.log(Math.max(lo,25)/lo)/K)),thr=bot+3;let a=-1,av=-1e9;
    for(let c=c0;c<gw;c++)if(sm[c]>av&&sm[c]>thr){av=sm[c];a=c}
    if(a>=0){let b=-1,bv=-1e9;const md=Math.max(6,Math.round(gw*.03));for(let c=Math.max(c0,1);c<gw-1;c++){if(Math.abs(c-a)<md)continue;const v=sm[c];if(v>bv&&v>thr&&v>=sm[c-1]&&v>=sm[c+1]){bv=v;b=c}}
      mk.a=a;mk.av=av;mk.af=fc(a);mk.b=b;mk.bv=bv;mk.bf=b>=0?fc(b):0;
      {/* the read-outs from the bins; the averaging keeps its share: the trace's level plus the refinement of this frame's peak */const D=INS.fft(T[0].an),raw=c=>INS._spCol(D,map,c)+INS.SPCAL+tilt*map.tl[c];
        const pa=INS._spPk(D,map,a,tilt);if(pa.v>-200&&Math.abs(Math.log2(pa.f/mk.af))<.25){mk.af=pa.f;mk.av=av+Math.max(0,pa.v-raw(a))}
        if(b>=0){const pb=INS._spPk(D,map,b,tilt);if(pb.v>-200&&Math.abs(Math.log2(pb.f/mk.bf))<.25){mk.bf=pb.f;mk.bv=bv+Math.max(0,pb.v-raw(b))}}}
      g.font=(fs-.5)+'px '+L.mono;g.textBaseline='bottom';g.textAlign='center';const tri=(c,v,s)=>{const xx=gx+c+.5,yy=Math.max(gy+10,Y(v));g.fillStyle=C.mk;g.beginPath();g.moveTo(xx,yy-2);g.lineTo(xx+3,yy-6);g.lineTo(xx-3,yy-6);g.closePath();g.fill();g.fillText(s,xx,yy-7)};
      tri(a,av,'1');if(b>=0)tri(b,bv,sz==='mini'?'2':'Δ2')}}
  /* the settings around the graticule (front-panel style; units amber, L2) */
  g.font=fs+'px '+L.mono;g.textBaseline='alphabetic';const u=tilt?'dB':'dBFS',div=rng/10,dv=INS.parts(div,'dB',{d:Math.abs(div-Math.round(div))<.05?0:1})[0];
  const refP=[['REF ',L.mut],...INS._spU(top,'dBFS',L,{d:1}),['  '+dv+' ',L.ink],['dB/div',L.unit]];
  const mk1=mk.a>=0?[['MKR1 ',L.mut],...INS._spU(mk.af,'Hz',L),...(sz==='full'&&gw>=420?[['  '+INS.note(mk.af).name,L.lab]]:[]),['  ',L.ink],...INS._spU(mk.av,u,L,{d:1})]:[['MKR1 ',L.mut],['–',L.mut]];
  const tr1=(T[0]&&typeof T[0].col==='string'?T[0].col:C.c1),hold0=T[0]&&T[0].hold,fl0=T[0]&&T[0].fall||0;
  const tl=[['1 CLRW',tr1],...(hold0?[['  2 '+(fl0>0?'PK HOLD':'MAXH'),T[0].col2||C.c2]]:[])];
  if(sz==='mini'){g.font='6.5px '+L.mono;const ty=gy+8;INS._segs(g,[['REF ',L.mut],...INS._spU(top,'dBFS',L,{d:0}),[' '+dv+' dB/div',L.mut]],gx+3,ty,'left');if(mk.a>=0)INS._segs(g,[...INS._spU(mk.af,'Hz',L),[' ',L.ink],...INS._spU(mk.av,u,L,{d:1})],gx+gw-3,ty,'right')}
  else{const ty=y+9;const lw0=INS._segs(g,refP,gx,ty,'left');const rw=INS._segs(g,mk1,gx+gw,ty,'right');void lw0;void rw;
    g.font=(fs-1.5)+'px '+L.mono;INS._segs(g,tl,gx+4,gy+8,'left');g.font=fs+'px '+L.mono;
    const r1=gy+gh+11,an0=T[0]&&T[0].an,av=t0&&t0.avgT||0;
    const sP=[['START ',L.mut],...INS._spU(lo,'Hz',L)],eP=[['STOP ',L.mut],...INS._spU(hi,'Hz',L)];
    const ws=INS._segs(g,sP,gx,r1,'left'),we=INS._segs(g,eP,gx+gw,r1,'right');
    const rbwP=[['RBW ',L.mut],...INS._spU(INS.rbw(an0,sr),'Hz',L),['  AVG ',L.mut],...(av>=.0005?INS._spU(av,'s',L):[['OFF',L.ink]]),['  DET ',L.mut],['PEAK',L.ink],...(tilt?[['  TILT ',L.mut],[INS.num(tilt,1),L.ink],[' dB/oct',L.unit]]:[])];
    if(sz==='full'){g.textAlign='center';g.fillStyle=L.mut;const lg='LOG';if(gw/2-g.measureText(lg).width/2>ws+8&&gw/2+g.measureText(lg).width/2<gw-we-8)g.fillText(lg,gx+gw/2,r1);
      const r2=r1+11,wl=INS._segs(g,rbwP,gx,r2,'left');if(mk.b>=0){const dP=[['ΔMKR2 ',L.mut],...(()=>{const q=INS._spU(mk.bf-mk.af,'Hz',L,{n:3});if(mk.bf>mk.af)q[0][0]='+'+q[0][0];return q})(),['  ',L.ink],...INS._spU(mk.bv-mk.av,'dB',L,{d:1,plus:true})];let wd=0;for(const p of dP)wd+=g.measureText(p[0]).width;if(gx+wl+12<gx+gw-wd)INS._segs(g,dP,gx+gw,r2,'right')}}
    else{let wr=0;for(const p of rbwP)wr+=g.measureText(p[0]).width;if(gw/2-wr/2>ws+8&&gw/2+wr/2<gw-we-8)INS._segs(g,rbwP,gx+gw/2,r1,'center')}}
  return{Y,map,mx,gx,gy,gw,gh,mk}};
/* the overlay's spectrum module through the drawer (its colours, sources, range menu, slow automatic range and Peak button stay) */
function insSpoSpec(ov,M,g,w,h,st){g.clearRect(0,0,w,h);const auto=ov.rng==='auto',rng=auto?72:(+ov.rng||72),T0=Math.round(ANZTOP+INS.SPCAL),top=auto?(ov.insT?(ov.top??T0):T0):T0;if(auto&&!ov.insT){ov.insT=1;ov.top=undefined}M.ss=M.ss||{};/* the steady top keeps the picture where it was (the levels are now dBFS: 13.6 dB up) */
  const tr=[];ov.src.forEach((k,si)=>{if(!ctx)return;const an=spoAn(k);if(!an)return;let col=spoCol(k);
    if(!si&&st.cm!=='track'){if(M.gk!==st.cm+col+w+'x'+h){M.gk=st.cm+col+w+'x'+h;const pos=st.cm==='tri'||st.cm==='bass'||st.cm==='rainbow',G=pos?g.createLinearGradient(0,0,w,0):g.createLinearGradient(0,0,0,h);
      if(pos)for(let q=0;q<=12;q++){const c=st.cm==='rainbow'?anzHue(q/12,.95):mxPosRGB(st.cm,q/12,.95,col);G.addColorStop(q/12,`rgb(${c[0]|0},${c[1]|0},${c[2]|0})`)}else{const Lc=anzLut(st.cm,col).css;for(let q=0;q<=6;q++)G.addColorStop(q/6,Lc[Math.round(255-q/6*190)])}M.gr=G}col=M.gr}
    tr.push({an,col,col2:si?null:(typeof col==='string'?col:INS.SPC.c2),dash:true,hold:!!ov.hold,fall:21,anAvg:true,sil:-104,st:M.ss[k]||(M.ss[k]={})})});
  const r=INS.spec(g,0,0,w,h,{tr,lo:20,hi:20000,top,bot:top-rng,tilt:4.5,live:!!st.active,st:M.sp||(M.sp={})});
  if(auto&&st.active&&r.mx>-150){const mxv=r.mx,want=Math.ceil((mxv+6)/6)*6,cur=ov.top??want;if(want>cur){ov.top=cur+(want-cur)*Math.min(1,st.dt*1.5);M.lo=0}else if(want<cur-6){M.lo=(M.lo||0)+st.dt;ov.top=M.lo>6?cur-st.dt*1.5:cur}else{M.lo=0;ov.top=cur}}}
if(typeof ANZD==='object'&&ANZD)ANZD.spec=insSpoSpec;
/* the Visualizer's spectrum through the drawer: REF 0 dBFS, 10 dB/div, no tilt (as on the pick page); max hold falls 3 dB/s, none at the Light level */
function insVzSpec(g,w,h,live){const st=VZ.ins||(VZ.ins={tr:{}});
  INS.spec(g,0,0,w,h,{tr:[{an:VZ.an,col:INS.SPC.c1,hold:!INS.lite(),fall:3,anAvg:true,st:st.tr}],lo:20,hi:20000,top:0,bot:-100,live:!!(live&&VZ.an),st})}
if(typeof VZD==='object'&&VZD)VZD.fft=insVzSpec;
/* the mixer's spec view keeps its bars (a strip is too narrow for a panel); the frequency scale is marked on its edge: 100 Hz, 1 kHz, 10 kHz */
function insMxSpecTicks(g,W,H,an){if(!an||!ctx)return;const n=an.frequencyBinCount,bh=ctx.sampleRate/2/n,L=INS.look();g.lineWidth=INS.hair(g,L.lwLine);g.strokeStyle=L.tickHi;g.beginPath();const lb=[];
  for(const f of[100,1000,10000]){const k=f/bh;if(k<1||k>=n)continue;const yy=INS.px(g,H*(1-Math.log(k)/Math.log(n)));g.moveTo(W-4,yy);g.lineTo(W,yy);lb.push([f,yy])}g.stroke();
  if(W>=44){g.font='6.5px '+L.mono;g.textAlign='right';g.textBaseline='middle';g.fillStyle=L.mut;for(const[f,yy] of lb)if(yy>6&&yy<H-4)g.fillText(f>=1000?f/1000+'k':String(f),W-6,yy)}}
/* ===== end of lane E IN-S ===== */
