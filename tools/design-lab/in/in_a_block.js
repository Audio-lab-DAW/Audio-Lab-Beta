/* ===== lane E (task IN-A): the shared instrument base =====
   One small module for every meter, scope and analyser (docs/design-round-4-instruments.md, step IN-A). It draws nothing by itself and adds no
   audio nodes; the later steps (IN-M level meters, IN-L loudness, IN-S spectrum, IN-E EQ, IN-G dynamics, IN-O stereo, IN-V Visualizer, IN-C CPU,
   IN-D device previews) build on it. Parts:
   - the look values (INS_LOOK0), until task LK adds LOOK; then LOOK's values of the same names win
   - one number formatter (INS.fmt, INS.num, INS.hz, INS.note): units, SI prefixes, a real minus sign, a thin space before the unit, Hz with the note
   - colour maps as lookup tables (magma, inferno, viridis, today's heat) and a colour bar
   - scale drawers: the meter taper scale, the log frequency axis, the dB grid, the scope graticule (drafting grid levels, hairlines)
   - ballistics: digital peak (falls 20 dB in 1.7 s, IEC 60268-18) with hold and a latched maximum, VU (IEC 60268-17), PPM type IIb (IEC 60268-10),
     RMS over a sliding window (AES17, a sine reads its peak level), K-weighted momentary loudness (ITU-R BS.1770)
   - one analyser read per analyser per frame (INS.fft, INS.fftB, INS.td) and the samples that are new since the last frame (INS.fresh) */
const INS_LOOK0={/* the user's design-direction picks (DR3: G3 drafting grid, W1 hairlines, L2 amber units, A1 yellow selection, N3 dense), as named constants until task LK; the keys are meant to be LOOK's names */
  grid:'G3',gMaj:'rgba(255,255,255,.13)',gMid:'rgba(255,255,255,.05)',gMin:'rgba(136,136,136,.07)',/* G3: three levels, like graph paper */
  lwGrid:.5,lwLine:.5,lwCurve:1,/* W1: hairlines in CSS px (one device pixel at 2x); curves (data) one CSS px */
  unit:'#ffb547',sel:'#f5c84c',/* L2 amber units, A1 yellow selection */
  ink:'#ececf1',mut:'#8b8b97',lab:'#b7b7c2',tick:'rgba(255,255,255,.32)',tickHi:'rgba(255,255,255,.5)',
  mono:'"JetBrains Mono",ui-monospace,Menlo,monospace',dense:true};
const INS={nfft:0,ntd:0,
  _src(){/* LK's look tokens. Note: the name LOOK is already taken by the Settings look sliders (an array), so only a plain object counts; LK points this line at its object if it picks another name */try{return typeof LOOK==='object'&&LOOK&&!Array.isArray(LOOK)?LOOK:null}catch(e){return null}},
  look(){const L=INS._src();if(this._lk&&this._lk.src===L&&this._lk.f===FRN)return this._lk.v;const v=Object.assign({},INS_LOOK0);if(L)for(const k in INS_LOOK0)if(L[k]!=null)v[k]=L[k];this._lk={src:L,f:FRN,v};return v},
  lite:()=>!!(typeof UI==='object'&&UI.lite),/* the Light level: half rate, no afterglow or persistence, smaller FFTs */
  due(st,now){/* screen rate, or half of it at the Light level; st keeps its own time */const iv=INS.lite()?31:0;if(now-(st.tDraw||0)<iv)return false;st.tDraw=now;return true},
  /* ---------- numbers ---------- */
  MIN:'−',TS:' ',
  num(v,d=1,plus){if(!isFinite(v))return v>0?'+∞':INS.MIN+'∞';const s=Math.abs(v).toFixed(d);if(+s===0)return(0).toFixed(d);return(v<0?INS.MIN:plus?'+':'')+s},
  sig(v,n=3){/* n significant figures, trailing zeros kept: 12.4, 1.25, 500 */const a=Math.abs(v);if(!a)return(0).toFixed(Math.max(0,n-1));const e=Math.floor(Math.log10(a)+1e-9),d=Math.max(0,n-1-e);let s=a.toFixed(d);if(s.replace('.','').replace(/^0+/,'').length>n&&d>0)s=a.toFixed(d-1);return(v<0?INS.MIN:'')+s},
  PRE:[[1e6,'M'],[1e3,'k'],[1,''],[1e-3,'m'],[1e-6,'µ']],
  si(v,n=3){/* [mantissa string, prefix] */if(!isFinite(v)||!v)return[INS.sig(v||0,n),''];const a=Math.abs(v);let p=INS.PRE[INS.PRE.length-1];for(const q of INS.PRE)if(a>=q[0]*.9995){p=q;break}return[INS.sig(v/p[0],n),p[1]]},
  LOG:{dB:1,dBFS:1,dBTP:1,dBu:1,dBV:1,LUFS:1,LKFS:1,LU:1,VU:1},
  parts(v,u,o={}){/* [number, unit] for drawing the unit apart (amber, L2) */
    if(u&&INS.LOG[u]){if(!isFinite(v)||v<-200)return[INS.MIN+'∞',u];return[INS.num(v,o.d==null?1:o.d,o.plus!=null?o.plus:u==='LU'),u]}
    if(u==='%')return[INS.num(v,o.d==null?0:o.d,o.plus),'%'];
    if(u==='ct'){const s=INS.num(v,o.d==null?0:o.d,true);return[/^[0.]+$/.test(s)?'+'+s:s,'ct']}
    if(u===':1')return[INS.sig(v,o.n||3),':1'];
    if(u==='°')return[INS.num(v,o.d==null?0:o.d,o.plus),'°'];
    if(u==='x'||u==='×')return[INS.sig(v,o.n||4),'×'];
    if(u==='Hz'||u==='s'||u==='V'||u==='B'||o.si){const[m,p]=INS.si(v,o.n||3);return[m,p+(u||'')]}
    return[o.d!=null?INS.num(v,o.d,o.plus):INS.sig(v,o.n||3),u||'']},
  ucap(u){/* a unit as a small capital label (L2, M1) without turning the micro sign into a Greek capital M: µs -> µS, kHz -> KHZ */return String(u||'').replace(/[^\u00b5]/g,c=>c.toUpperCase())},
  fmt(v,u,o={}){const[a,b]=INS.parts(v,u,o);return b?a+(b==='%'||b==='°'||b===':1'?'':INS.TS)+b:a},
  NOTES:['C','C♯','D','D♯','E','F','F♯','G','G♯','A','A♯','B'],
  note(f,a4){/* nearest note and the offset in cents */const r0=69+12*Math.log2(f/(a4||440)),r=Math.round(r0);return{name:INS.NOTES[((r%12)+12)%12]+(Math.floor(r/12)-1),midi:r,ct:(r0-r)*100}},
  hz(f,o={}){/* "1.25 kHz", or with the note (X8): "440 Hz  A4 +0 ct" */const s=INS.fmt(f,'Hz',o);if(!o.note||!(f>0))return s;const n=INS.note(f);return s+'  '+n.name+' '+INS.fmt(n.ct,'ct')},
  /* ---------- colour maps (matplotlib's magma, inferno, viridis: lightness rises steadily; today's heat as the app has it) ---------- */
  CMH:{magma:'@MAGMA@',inferno:'@INFERNO@',viridis:'@VIRIDIS@'},
  _cm:{},
  cmap(k){if(INS._cm[k])return INS._cm[k];const a=new Uint8Array(768);let st=null;
    if(INS.CMH[k]){const h=INS.CMH[k],n=h.length/6;st=[];for(let i=0;i<n;i++)st.push([i/(n-1),[0,2,4].map(j=>parseInt(h.substr(i*6+j,2),16))])}
    else st=[[0,[27,42,107]],[.22,[47,107,255]],[.45,[37,208,200]],[.65,[255,210,63]],[.85,[255,138,31]],[1,[255,95,70]]];/* today's heat (heatCol0, MXPAL.heat) */
    for(let i=0;i<256;i++){const t=i/255;let j=1;while(j<st.length-1&&st[j][0]<t)j++;const[x0,p0]=st[j-1],[x1,p1]=st[j],u=Math.min(1,Math.max(0,(t-x0)/(x1-x0||1)));for(let c=0;c<3;c++)a[i*3+c]=Math.round(p0[c]+(p1[c]-p0[c])*u)}
    return INS._cm[k]=a},
  cmapNames:['magma','inferno','viridis','heat'],
  rgb(k,t){const a=INS.cmap(k),q=Math.max(0,Math.min(255,Math.round(t*255)))*3;return`rgb(${a[q]},${a[q+1]},${a[q+2]})`},
  _cb:{},
  cbar(g,x,y,w,h,k,vert){/* a colour bar, made once per map and size, then copied */const key=k+'|'+(vert?1:0);let c=INS._cb[key];
    if(!c){c=INS._cb[key]=document.createElement('canvas');c.width=vert?1:256;c.height=vert?256:1;const cg=c.getContext('2d'),im=cg.createImageData(c.width,c.height),L=INS.cmap(k);for(let i=0;i<256;i++){const q=(vert?255-i:i)*3;im.data.set([L[q],L[q+1],L[q+2],255],i*4)}cg.putImageData(im,0,0)}
    const sm=g.imageSmoothingEnabled;g.imageSmoothingEnabled=true;g.drawImage(c,x,y,w,h);g.imageSmoothingEnabled=sm},
  /* ---------- scales ---------- */
  dpr(g){const m=g.getTransform?g.getTransform():null;return m&&m.a>0?m.a:1},
  px(g,v){/* a hairline on a whole device pixel */const d=INS.dpr(g);return(Math.round(v*d-.5)+.5)/d},
  hair(g,lw){return Math.max(1/INS.dpr(g),lw)},
  taper:db=>dbN(db),untaper:p=>nDb(p),
  TT:null,
  taperTicks(){/* M1: a mark per dB from +6 to -12, every 3 dB to -24, then every 6 to -60; numbers at the long marks */if(INS.TT)return INS.TT;const all=[];for(let d=6;d>=-60;d--){if(d>=-12||(d>=-24&&d%3===0)||d%6===0)all.push(d)}
    return INS.TT={all,long:[6,3,0,-3,-6,-9,-12,-18,-24,-30,-36,-48,-60],lab:[6,0,-6,-12,-18,-24,-36,-48,-60]}},
  scaleTaper(g,x,y,h,o={}){/* a vertical tick scale beside a meter: top = +6 dB, bottom = -60 dB (the fader taper); o.side 1 = ticks to the right; o.lab false = no numbers; o.gap = smallest space between numbers */
    const L=INS.look(),T=INS.taperTicks(),side=o.side||-1,Y=d=>y+h-h*dbN(d),ln=INS.hair(g,L.lwLine);g.lineWidth=ln;g.strokeStyle=o.col||L.tick;g.beginPath();
    for(const d of T.all){const yy=INS.px(g,Y(d)),lg=T.long.includes(d),k=(lg?(d===0?5:4):2)*(o.k||1);if(h<80&&!lg)continue;g.moveTo(x,yy);g.lineTo(x+side*k,yy)}g.stroke();
    if(o.lab===false)return Y;g.font=(o.fs||7)+'px '+L.mono;g.textAlign=side>0?'left':'right';g.textBaseline='middle';let last=-1e9;const gap=o.gap||9;
    for(const d of T.lab){const yy=Y(d);if(Math.abs(yy-last)<gap)continue;last=yy;g.fillStyle=d===0?L.lab:(o.labCol||L.mut);g.fillText(d>0?'+'+d:d<0?INS.MIN+(-d):'0',x+side*((o.k||1)*5+2),yy)}return Y},
  fAxis(g,x0,w,y0,h,o={}){/* log frequency axis: long marks at decades, mid at 2 and 5, short elsewhere; numbers only where they fit; returns f -> x */
    const L=INS.look(),lo=o.lo||20,hi=o.hi||20000,K=Math.log(hi/lo),fx=f=>x0+w*Math.log(f/lo)/K,lw=INS.hair(g,L.lwGrid),gr=o.grid!==false,tk=o.ticks!==false;
    const by=[[],[],[]];for(let d=1;d<=hi;d*=10)for(let m=1;m<10;m++){const f=d*m;if(f<lo*.999||f>hi*1.001)continue;by[m===1?0:m===2||m===5?1:2].push(f)}
    const cols=[L.gMaj,L.gMid,L.gMin],tl=[5,3.5,2];g.lineWidth=lw;
    for(let lv=0;lv<3;lv++){if(gr){g.strokeStyle=cols[lv];g.beginPath();for(const f of by[lv]){const x=INS.px(g,fx(f));g.moveTo(x,y0);g.lineTo(x,y0+h)}g.stroke()}
      if(tk){g.strokeStyle=lv?L.tick:L.tickHi;g.beginPath();for(const f of by[lv]){const x=INS.px(g,fx(f));g.moveTo(x,y0+h);g.lineTo(x,y0+h+tl[lv])}g.stroke()}}
    if(o.lab!==false){const lb=o.labels||[20,50,100,200,500,1000,2000,5000,10000,20000],fs=o.fs||7;g.font=fs+'px '+L.mono;g.textBaseline='top';let last=-1e9;
      for(const f of lb){const x=fx(f);if(x<x0-1||x>x0+w+1)continue;const s=f>=1000?f/1000+'k':String(f),tw=g.measureText(s).width,al=f<=lo?'left':f>=hi?'right':'center',l0=al==='left'?x:al==='right'?x-tw:x-tw/2;if(l0<last+(o.gap||6))continue;last=l0+tw;
        g.textAlign=al;g.fillStyle=f===100||f===1000||f===10000?L.lab:L.mut;g.fillText(s,x,y0+h+(tk?6:2))}}
    return fx},
  dbGrid(g,x0,y0,w,h,top,bot,step,o={}){/* horizontal dB lines every step, heavier every o.major; numbers on the left or right (o.side); returns dB -> y */
    const L=INS.look(),Y=v=>y0+h*(top-v)/(top-bot),lw=INS.hair(g,L.lwGrid),maj=o.major||step*2;g.lineWidth=lw;
    for(const m of[0,1]){g.strokeStyle=m?L.gMaj:L.gMid;g.beginPath();for(let v=top;v>=bot-1e-9;v-=step){const isM=Math.abs(v/maj-Math.round(v/maj))<1e-6;if(isM!==!!m)continue;const yy=INS.px(g,Y(v));g.moveTo(x0,yy);g.lineTo(x0+w,yy)}g.stroke()}
    if(o.lab!==false){g.font=(o.fs||7)+'px '+L.mono;g.textBaseline='middle';const right=o.side==='right';g.textAlign=right?'left':'right';let last=-1e9;
      for(let v=top;v>=bot-1e-9;v-=(o.labStep||maj)){const yy=Y(v);if(yy-last<(o.gap||9))continue;last=yy;g.fillStyle=o.labCol||L.mut;g.fillText(INS.num(v,0,o.plus),right?x0+w+3:x0-3,yy)}}
    return Y},
  graticule(g,x,y,w,h,o={}){/* oscilloscope graticule: nx by ny major divisions, five minor marks per division on the centre axes (Tektronix layout), drafting levels */
    const L=INS.look(),nx=o.nx||10,ny=o.ny||8,lw=INS.hair(g,L.lwGrid),cx=x+w/2,cy=y+h/2;g.lineWidth=lw;
    if(o.minor!==false&&!INS.lite()&&o.fine){g.strokeStyle=L.gMin;g.beginPath();for(let i=0;i<=nx*5;i++){if(i%5===0)continue;const xx=INS.px(g,x+i*w/(nx*5));g.moveTo(xx,y);g.lineTo(xx,y+h)}for(let j=0;j<=ny*5;j++){if(j%5===0)continue;const yy=INS.px(g,y+j*h/(ny*5));g.moveTo(x,yy);g.lineTo(x+w,yy)}g.stroke()}
    g.strokeStyle=L.gMid;g.beginPath();for(let i=0;i<=nx;i++){const xx=INS.px(g,x+i*w/nx);g.moveTo(xx,y);g.lineTo(xx,y+h)}for(let j=0;j<=ny;j++){const yy=INS.px(g,y+j*h/ny);g.moveTo(x,yy);g.lineTo(x+w,yy)}g.stroke();
    g.strokeStyle=L.gMaj;g.beginPath();const X=INS.px(g,cx),Y=INS.px(g,cy);g.moveTo(X,y);g.lineTo(X,y+h);g.moveTo(x,Y);g.lineTo(x+w,Y);
    if(o.minor!==false){for(let i=0;i<=nx*5;i++){const xx=INS.px(g,x+i*w/(nx*5));g.moveTo(xx,cy-2);g.lineTo(xx,cy+2)}for(let j=0;j<=ny*5;j++){const yy=INS.px(g,y+j*h/(ny*5));g.moveTo(cx-2,yy);g.lineTo(cx+2,yy)}}g.stroke();
    return{dx:w/nx,dy:h/ny,cx,cy}},
  corner(g,s,x,y,al){/* a setting written in a corner of a display (graticule first, settings in the corners) */const L=INS.look();g.font='7px '+L.mono;g.textAlign=al||'left';g.textBaseline='top';g.fillStyle=L.mut;g.fillText(s,x,y)},
  /* ---------- ballistics ---------- */
  DPK:20/1.7,/* digital peak meter (IEC 60268-18): returns 20 dB in 1.7 s = 11.8 dB/s */
  peak(st,db,dt,o={}){/* instant rise, falls at o.fall dB/s (11.8), the hold line waits o.hold s (2) and then falls; mx is latched until reset */
    const fall=o.fall||INS.DPK,hold=o.hold==null?2:o.hold;st.t=(st.t||0)+dt;if(st.d==null){st.d=st.h=st.mx=-240;st.ht=0}
    st.d=Math.max(db,st.d-fall*dt);if(db>=st.h){st.h=db;st.ht=st.t}else if(st.t-st.ht>hold)st.h=Math.max(st.d,st.h-fall*dt);if(db>st.mx)st.mx=db;return st},
  VUZ:.81,VUW:13.4,VUAL:20*Math.log10(Math.PI/2),/* VU (IEC 60268-17): second order on the rectified signal, 99 % in 0.3 s, about 1.3 % overshoot; aligned so a sine reads its peak level */
  vu(st,a,i0,i1,sr){let x=st.x||0,v=st.v||0;const w=INS.VUW,z=INS.VUZ,dt=1/sr,ww=w*w,zw=2*z*w;for(let i=i0;i<i1;i++){const r=a[i]<0?-a[i]:a[i];v+=(ww*(r-x)-zw*v)*dt;x+=v*dt}st.x=x;st.v=v;return x>1e-12?20*Math.log10(x)+INS.VUAL:-240},
  PPMAL:.214,/* the steady-sine ripple of the detector, added back so a steady sine reads its peak level */
  ppm(st,a,i0,i1,sr){/* PPM type IIb (EBU, IEC 60268-10): a 10 ms tone burst reads 2 dB below the steady tone (charge time constant 2.75 ms on the rectified signal, set by that rule), falls 24 dB in 2.8 s; returns the highest reading in this block */
    if(st.sr!==sr){st.sr=sr;st.at=1-Math.exp(-1/(.00275*sr));st.fl=Math.pow(10,-24/2.8/20/sr)}let p=st.p||0,m=0;const at=st.at,fl=st.fl;for(let i=i0;i<i1;i++){const r=a[i]<0?-a[i]:a[i];p=r>p?p+(r-p)*at:p*fl;if(p>m)m=p}st.p=p;return m>1e-12?20*Math.log10(m)+INS.PPMAL:-240},
  win(st,T,sr){/* a sliding window of T seconds in 10 ms pieces */if(st.T!==T||st.sr!==sr){st.T=T;st.sr=sr;st.sb=Math.max(1,Math.round(sr*.01));st.nb=Math.max(1,Math.round(T/.01));st.ring=new Float64Array(st.nb);st.ri=0;st.acc=0;st.cnt=0;st.sum=0}return st},
  _wadd(st,q){st.acc+=q;if(++st.cnt===st.sb){st.sum+=st.acc-st.ring[st.ri];st.ring[st.ri]=st.acc;st.ri=(st.ri+1)%st.nb;st.acc=0;st.cnt=0}},
  wmean(st){return Math.max(0,st.sum)/(st.nb*st.sb)},
  rms(st,a,i0,i1,sr,T){/* RMS over a sliding window (T s, 0.3 by default), AES17: +3.01 dB so a sine reads its peak level */INS.win(st,T||.3,sr);for(let i=i0;i<i1;i++)INS._wadd(st,a[i]*a[i]);const m=INS.wmean(st);return m>1e-12?10*Math.log10(m)+3.0103:-240},
  kms(st,a,i0,i1,sr){/* K-weighted mean square over a 400 ms window (ITU-R BS.1770 momentary); the two filters keep their state from block to block */
    INS.win(st,.4,sr);if(st.ksr!==sr){st.ksr=sr;st.kc=kBiquads(sr);st.kz=new Float64Array(8)}const[A,B]=st.kc,z=st.kz;let x1=z[0],x2=z[1],y1=z[2],y2=z[3],u1=z[4],u2=z[5],w1=z[6],w2=z[7];
    for(let i=i0;i<i1;i++){const v=a[i],o=A[0]*v+A[1]*x1+A[2]*x2-A[3]*y1-A[4]*y2;x2=x1;x1=v;y2=y1;y1=o;const p=B[0]*o+B[1]*u1+B[2]*u2-B[3]*w1-B[4]*w2;u2=u1;u1=o;w2=w1;w1=p;INS._wadd(st,p*p)}
    if(!(Math.abs(w1)<1e6))w1=w2=u1=u2=x1=x2=y1=y2=0;z[0]=x1;z[1]=x2;z[2]=y1;z[3]=y2;z[4]=u1;z[5]=u2;z[6]=w1;z[7]=w2;return INS.wmean(st)},
  /* ---------- analyser reads: once per analyser per frame ---------- */
  _ok(an,k,now){return an[k+'f']===FRN&&now-an[k+'t']<12},
  fft(an,buf){/* dB per bin (getFloatFrequencyData), read once per frame and shared by every drawer of this analyser */const n=an.frequencyBinCount,now=performance.now();let c=an._insF;if(!c||c.length!==n){c=an._insF=new Float32Array(n);an._insFf=-1}
    if(!INS._ok(an,'_insF',now)){an.getFloatFrequencyData(c);an._insFf=FRN;an._insFt=now;INS.nfft++}if(buf&&buf!==c){if(buf.length>=n)buf.set(c);else buf.set(c.subarray(0,buf.length))}return buf||c},
  fftB(an,buf){const n=an.frequencyBinCount,now=performance.now();let c=an._insB;if(!c||c.length!==n){c=an._insB=new Uint8Array(n);an._insBf=-1}
    if(!INS._ok(an,'_insB',now)){an.getByteFrequencyData(c);an._insBf=FRN;an._insBt=now;INS.nfft++}if(buf&&buf!==c){if(buf.length>=n)buf.set(c);else buf.set(c.subarray(0,buf.length))}return buf||c},
  td(an){/* the time-domain samples (getFloatTimeDomainData), read once per frame */const n=an.fftSize,now=performance.now();let c=an._insT;if(!c||c.length!==n){c=an._insT=new Float32Array(n);an._insTf=-1}
    if(!INS._ok(an,'_insT',now)){an.getFloatTimeDomainData(c);an._insTf=FRN;an._insTt=now;INS.ntd++}return c},
  fresh(a,st,exp){/* where the samples that arrived since this reader's last look start in a (the analyser's latest fftSize samples): the last four samples seen are found again,
     trying the expected place first and then whole 128-sample render blocks either side, so nothing is counted twice or missed; if they are not found (a gap longer than the buffer, or the first look) the last exp samples count */
    const n=a.length,t=st.tl||(st.tl=new Float32Array(4));let s=-1;
    if(st.tv&&n>=256){/* the buffer always ends on a render block, so the new part is a whole number of 128-sample blocks */const m0=Math.round(Math.max(0,exp)/128),mx=n>>7,at=m=>{const j=n-m*128;return m>=0&&m<=mx&&j>=4&&a[j-1]===t[3]&&a[j-2]===t[2]&&a[j-3]===t[1]&&a[j-4]===t[0]};
      for(let k=0;k<=16&&s<0;k++){if(at(m0+k))s=n-(m0+k)*128;else if(k&&at(m0-k))s=n-(m0-k)*128}}
    if(s<0)s=Math.max(0,n-Math.max(0,Math.min(n,Math.round(exp))));t[0]=a[n-4];t[1]=a[n-3];t[2]=a[n-2];t[3]=a[n-1];st.tv=1;return s},
};
/* ===== end of lane E IN-A ===== */
