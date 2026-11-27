/* ===== lane E (task IN-G): the dynamics displays, the user's picks G1, G3 and G4 =====
   G1 gain reduction history (FabFilter Pro-L style): 4 s, the input as a grey area, the output as a blue line, the gain reduction in red
      hanging from the top on the same dB scale (1 dB down is 1 dB), the level scale on the left and the GR scale on the right, the GR now as a
      big number and the most in the last 4 s smaller. Compressor, Limiter, Gate and Ducker.
   G3 the compressor's transfer curve, calibrated: input and output in dBFS from -60 to 0, a line every 6 dB, labels every 12, the 1:1 line
      dashed; the curve is the one Chromium's compressor really has (measured: the 6 dB knee starts at the threshold and ends 6 dB above it;
      it reads the peak level, ingCK); the signal rides it as a dot with a short trail (none at the Light level), and an amber caliper to the 1:1 line
      gives the gain reduction with its number.
   G4 per-band gain reduction for OTT, Multiband Dynamics and the De-Esser: one bar per band falling from the top on the studio scale
      0, 1, 2, 3, 4, 6, 8, 10, 15, 20, 30 dB (the first dB gets the most room), a white tick held 2 s, the bar falling 25 dB/s, the band's
      edges as frequencies and its number.
   Only drawing: the values are the ones the devices already post (compressor and band reduction, the limiter's, gate's, de-esser's and
   ducker's worklet messages); the gate's and ducker's display history is kept 4 s instead of 2 (display arrays only). Nothing new runs
   when a display is hidden: everything here is called by drawViz for visible canvases only. */
const INSG={IN:'rgba(255,255,255,.13)',OUT:'#4c8dff',GR:'#ff4d6d',GRA:'rgba(255,77,109,.2)',GRT:'#ff8aa0',SPAN:4,KNEE:6,
  GRS:[0,1,2,3,4,6,8,10,15,20,30],st:new Map(),bi:new Float32Array(1024),bo:new Float32Array(1024),bg:new Float32Array(1024),bx:new Float32Array(1024),A:[0,0,0]};
const ingSt=(id,k)=>{const key=id+'|'+k;let s=INSG.st.get(key);if(!s){s={};INSG.st.set(key,s)}return s};
/* the compressor's static curve exactly as Chromium's DynamicsCompressor computes it (DynamicsCompressorKernel: an exponential knee in linear
   amplitude from the threshold, its constant k found so the slope at threshold + knee is 1/ratio, then the ratio in dB; measured to agree
   within 0.05 dB with square waves); the reduction in dB (<= 0) at input peak level x dBFS. Cached per setting. */
function ingCK(T,R,K){const key=T+'|'+R+'|'+K;let c=INSG.ck;if(c&&c.key===key)return c;const lt=Math.pow(10,T/20),kc=(x,k)=>x<lt?x:lt+(1-Math.exp(-k*(x-lt)))/k,l2d=v=>20*Math.log10(v),
  slope=(x,k)=>{if(x<lt)return 1;const x2=x*1.001;return(l2d(kc(x2,k))-l2d(kc(x,k)))/(l2d(x2)-l2d(x))},xk=Math.pow(10,(T+K)/20),ds=1/Math.max(1,R);
  let lo=.1,hi=1e4,k=5;for(let i=0;i<15;i++){if(slope(xk,k)<ds)hi=k;else lo=k;k=Math.sqrt(lo*hi)}
  c=INSG.ck={key,lt,k,kc,xkDb:T+K,ykDb:l2d(kc(xk,k)),s:ds};return c}
function ingRed(x,T,R,K){const c=ingCK(T,R,K),a=Math.pow(10,x/20);if(a<c.lt)return 0;if(x<c.xkDb)return 20*Math.log10(c.kc(a,c.k)/a);return c.ykDb+c.s*(x-c.xkDb)-x}
/* G1: gain reduction history in the box x0,y0,w,h. o.n entries, o.at(i,A) fills A=[in dB, out dB, GR dB (<=0)] for i=0 (oldest) to n-1
   (newest), o.age(i) its age in seconds; o.top, o.bot the dB scale (GR hangs from the top with the same dB per pixel); o.lab 'out' or 'in'
   for the level scale outside or inside the left edge, o.rlab the same for the GR scale on the right; o.num {x,y,al} for the numbers. */
INS.grh=function(g,x0,y0,w,h,o){const L=INS.look(),top=o.top,bot=o.bot,R=top-bot,sp=o.span||INSG.SPAN,lw=INS.hair(g,L.lwGrid),
  Y=v=>y0+h*Math.min(1,Math.max(0,(top-v)/R)),G=d=>y0+h*Math.min(1,Math.max(0,-d/R)),st=o.step||6;
  g.lineWidth=lw;if(o.grid!==false)for(const m of[0,1]){g.strokeStyle=m?L.gMaj:L.gMid;g.beginPath();for(let v=Math.floor(top/st)*st;v>=bot-1e-9;v-=st){const maj=Math.abs(v)%(st*2)<1e-6;if(maj!==!!m)continue;const yy=INS.px(g,Y(v));g.moveTo(x0,yy);g.lineTo(x0+w,yy)}g.stroke()}
  const N=Math.min(o.n,1024),bi=INSG.bi,bo=INSG.bo,bg=INSG.bg,bx=INSG.bx,A=INSG.A;let m=0,mx=0,now=0;
  const dp=INS.dpr(g);let lc=-1e9;/* one point per device pixel column: the highest input and output, the deepest reduction */
  for(let i=Math.max(0,o.n-N);i<o.n;i++){const a=o.age(i);if(a>sp||a<0)continue;o.at(i,A);const x=x0+w*(1-a/sp),c=Math.floor(x*dp),gr=Math.min(0,A[2]);if(gr<mx)mx=gr;
    if(c===lc&&m){const k=m-1;if(A[0]>bi[k])bi[k]=A[0];if(A[1]>bo[k])bo[k]=A[1];if(gr<bg[k])bg[k]=gr;bx[k]=x;if(i===o.n-1)now=gr;continue}lc=c;bx[m]=x;bi[m]=A[0];bo[m]=A[1];bg[m]=gr;m++;if(i===o.n-1)now=gr}
  g.save();g.beginPath();g.rect(x0,y0,w,h);g.clip();
  if(m>1){if(o.in!==false){g.beginPath();g.moveTo(bx[0],y0+h);for(let k=0;k<m;k++)g.lineTo(bx[k],Y(bi[k]));g.lineTo(bx[m-1],y0+h);g.closePath();g.fillStyle=o.inCol||INSG.IN;g.fill()}
    if(o.out!==false){g.beginPath();for(let k=0;k<m;k++){const yy=Y(bo[k]);k?g.lineTo(bx[k],yy):g.moveTo(bx[k],yy)}g.strokeStyle=INSG.OUT;g.lineWidth=1.2;g.stroke()}
    g.beginPath();g.moveTo(bx[0],y0);for(let k=0;k<m;k++)g.lineTo(bx[k],G(bg[k]));g.lineTo(bx[m-1],y0);g.closePath();g.fillStyle=INSG.GRA;g.fill();
    g.beginPath();for(let k=0;k<m;k++){const yy=G(bg[k]);k?g.lineTo(bx[k],yy):g.moveTo(bx[k],yy)}g.strokeStyle=INSG.GR;g.lineWidth=1.2;g.stroke()}
  if(o.thr!=null&&o.thr<top&&o.thr>bot){const yy=INS.px(g,Y(o.thr));g.strokeStyle='rgba(255,181,71,.5)';g.lineWidth=lw;g.beginPath();g.moveTo(x0,yy);g.lineTo(x0+w,yy);g.stroke()}
  g.restore();
  g.font='7px '+L.mono;g.textBaseline='middle';const ls=o.lstep||12;
  if(o.lab){const out=o.lab==='out';g.textAlign=out?'right':'left';g.fillStyle=L.mut;for(let v=Math.floor(top/ls)*ls;v>=bot-1e-9;v-=ls){const yy=Y(v);if(yy<y0+4||yy>y0+h-3)continue;g.fillText(INS.num(v,0),out?x0-3:x0+2,yy)}}
  if(o.rlab){const out=o.rlab==='out';g.textAlign=out?'left':'right';g.fillStyle=INSG.GRT;for(let d=0;d<=R-1e-9;d+=ls){const yy=G(-d);if(yy>y0+h-3)continue;g.fillText(d?INS.num(-d,0):'0',out?x0+w+3:x0+w-2,Math.max(y0+4,yy))}}
  g.textAlign='left';
  if(o.num)ingNum(g,o.num.x,o.num.y,now,mx,o.num.al||'right',sp,o.num.small);
  if(o.leg!==false&&w>140){g.font='6.5px '+L.mono;g.textBaseline='bottom';let x=x0+3;const yb=y0+h-2;for(const[s,c]of[['IN',o.in===false?null:'rgba(255,255,255,.55)'],['OUT',o.out===false?null:INSG.OUT],['GR',INSG.GR]]){if(!c)continue;g.fillStyle=c;g.fillText(s,x,yb);x+=g.measureText(s).width+6}g.textBaseline='alphabetic'}
  return{now,mx}};
/* the G1 numbers: the gain reduction now, big, and the most in the last 4 s */
function ingNum(g,x,y,now,mx,al,sp,small){const L=INS.look();g.textAlign=al;g.textBaseline='alphabetic';g.font='600 '+(small?11:14)+'px '+L.mono;g.fillStyle=INSG.GRT;const s=INS.num(Math.min(0,now),1),sw=g.measureText(s).width;g.fillText(s,al==='right'?x-(small?10:12):x,y);
  g.font='7px '+L.mono;g.fillStyle=L.unit;const sc='fontVariantCaps' in g&&typeof lkT==='function'&&lkT().unitCase==='small caps';if(sc)g.fontVariantCaps='all-small-caps';g.fillText('dB',al==='right'?x:x+sw+2,y);if(sc)g.fontVariantCaps='normal';/* MD1's M1: units in small capitals */
  g.fillStyle=L.mut;g.font='6.5px '+L.mono;g.fillText('max '+INS.num(Math.min(0,mx),1)+' in '+Math.round(sp||4)+' s',x,y+10);g.textAlign='left'}
/* G4: one gain reduction bar at x (width bw) from y0 down h, on the studio scale; st keeps its ballistics; gr in dB (>= 0) */
const ingGY=(d,y0,h)=>y0+h*Math.sqrt(Math.min(30,Math.max(0,d))/30);
function ingBar(g,x,y0,bw,h,st,gr,col,o={}){const L=INS.look(),t=performance.now(),dt=st.tp?Math.min(.1,(t-st.tp)/1000):0;st.tp=t;const q=INS.peak(st,Math.max(0,gr),dt,{fall:25,hold:2});
  g.fillStyle='#15171d';g.fillRect(x,y0,bw,h);const yy=ingGY(q.d,y0,h);if(yy>y0+.3){g.fillStyle=col;g.fillRect(x,y0,bw,yy-y0)}
  if(q.h>.05){g.fillStyle='#fff';g.fillRect(x-1,Math.round(ingGY(q.h,y0,h)),bw+2,1.3)}
  if(o.ticks!==false){g.strokeStyle='rgba(255,255,255,.4)';g.lineWidth=INS.hair(g,1);g.beginPath();for(const d of INSG.GRS){const y2=INS.px(g,ingGY(d,y0,h));g.moveTo(x-4,y2);g.lineTo(x-1,y2)}g.stroke()}
  if(o.nums){g.font='6.5px '+L.mono;g.fillStyle=L.mut;g.textAlign='right';g.textBaseline='middle';let last=-1e9;for(const d of INSG.GRS){const y2=ingGY(d,y0,h);if(y2-last<7)continue;last=y2;g.fillText(String(d),x-5,y2)}g.textAlign='left';g.textBaseline='alphabetic'}
  return q}
/* a band's GR number under its bar, and its edges (a short frequency text) */
function ingBarLab(g,xc,y,gr,col,edge,fs){const L=INS.look();g.textAlign='center';g.textBaseline='alphabetic';g.font='600 '+(fs||9)+'px '+L.mono;g.fillStyle=col;g.fillText(gr>.05?INS.num(-gr,1):'0.0',xc,y);
  if(edge){g.font='6.5px '+L.mono;g.fillStyle=L.mut;g.fillText(edge,xc,y+8)}g.textAlign='left'}
const ingHz=f=>f>=1000?INS.num(f/1000,f<10000?1:0).replace(/\.0$/,'')+'k':String(Math.round(f));
/* ---------- Compressor (vizComp): G3 curve and G1 history ---------- */
function ingComp(g,w,h,f,X){const L=INS.look(),p=f.p,G=compGeo(w,h),{S2,ox,oy,mx,my}=G,T=p.threshold,R=Math.max(1,p.ratio),K=INSG.KNEE,lw=INS.hair(g,L.lwGrid),now=performance.now(),st=ingSt(f.id,'c');
  g.fillStyle='#07070a';g.fillRect(0,0,w,h);
  g.lineWidth=lw;for(const m of[0,1]){g.strokeStyle=m?'rgba(255,255,255,.1)':L.gMid;g.beginPath();for(let d=-60;d<=0;d+=6){if((d%12===0)!==!!m)continue;const a=INS.px(g,mx(d)),b=INS.px(g,my(d));g.moveTo(a,oy);g.lineTo(a,oy+S2);g.moveTo(ox,b);g.lineTo(ox+S2,b)}g.stroke()}
  g.font='6.5px '+L.mono;g.fillStyle=L.mut;g.textBaseline='bottom';g.textAlign='center';for(const d of[-48,-36,-24,-12])g.fillText(INS.num(d,0),mx(d),oy+S2-2);
  g.textAlign='left';g.textBaseline='middle';for(const d of[-48,-36,-24,-12])g.fillText(INS.num(d,0),ox+2,my(d));
  g.textBaseline='bottom';g.textAlign='right';g.fillText('IN dBFS',ox+S2-2,oy+S2-10);g.textAlign='left';g.textBaseline='alphabetic';
  g.strokeStyle='rgba(255,255,255,.3)';g.lineWidth=1;g.setLineDash([3,3]);g.beginPath();g.moveTo(mx(-60),my(-60));g.lineTo(mx(0),my(0));g.stroke();
  g.strokeStyle='rgba(255,107,107,.7)';g.beginPath();g.moveTo(INS.px(g,mx(T)),oy);g.lineTo(INS.px(g,mx(T)),oy+S2);g.stroke();g.setLineDash([]);
  let cv=st.cv;if(!cv||cv.key!==T+'|'+R){cv=st.cv={key:T+'|'+R,y:new Float32Array(121)};for(let i=0;i<=120;i++){const d=-60+i/2;cv.y[i]=d+ingRed(d,T,R,K)}}/* the curve once per setting */
  g.strokeStyle='#ffd27a';g.lineWidth=2;g.beginPath();for(let i=0;i<=120;i++){const d=-60+i/2,y=my(cv.y[i]);i?g.lineTo(mx(d),y):g.moveTo(mx(d),y)}g.stroke();g.lineWidth=1;
  /* the live point: the input's peak over the analyser's window (the compressor reads the peak), the reduction it reports */
  let pk=0;if(X&&X.an){const a=INS.td(X.an);for(let i=0;i<a.length;i++){const v=a[i]<0?-a[i]:a[i];if(v>pk)pk=v}}
  const xin=pk>1e-6?20*Math.log10(pk):-120,gr=X&&X.k?Math.min(0,X.k.reduction):0,live=xin>-60;
  const tr=st.tr||(st.tr=[]);if(live){tr.push(xin,xin+gr);if(tr.length>60)tr.splice(0,2)}else if(tr.length)tr.splice(0,2);
  if(!INS.lite()){const n=tr.length/2;for(let i=0;i<n-1;i++){g.fillStyle='rgba(255,210,122,'+(i/n*.6).toFixed(2)+')';g.beginPath();g.arc(mx(Math.min(0,tr[2*i])),my(Math.max(-60,Math.min(0,tr[2*i+1]))),1.2,0,7);g.fill()}}
  if(live){const xi=Math.min(0,xin),px=mx(xi),py=my(Math.max(-60,Math.min(0,xi+gr))),p1=my(xi);g.fillStyle='#fff';g.beginPath();g.arc(px,py,3.5,0,7);g.fill();
    if(gr<-.2){const left=px>ox+S2-46,cx=left?px-8:px+8,d=left?-1:1;g.strokeStyle=L.unit;g.lineWidth=INS.hair(g,1);g.beginPath();g.moveTo(cx-2,p1);g.lineTo(cx+2,p1);g.moveTo(cx-2,py);g.lineTo(cx+2,py);g.moveTo(INS.px(g,cx),p1);g.lineTo(INS.px(g,cx),py);g.stroke();
      g.font='7.5px '+L.mono;g.fillStyle=L.unit;g.textAlign=left?'right':'left';g.textBaseline='middle';g.fillText(INS.num(gr,1)+' dB',cx+d*4,(p1+py)/2);g.textAlign='left';g.textBaseline='alphabetic'}}
  /* today's GR bar beside the curve */
  g.fillStyle='#15161c';g.fillRect(G.gx,oy,10,S2);g.fillStyle='#ff6b6b';g.fillRect(G.gx,oy,10,-gr/24*S2);g.fillStyle='rgba(62,207,142,.35)';g.fillRect(G.gx,oy+S2-p.makeup/24*S2,10,p.makeup/24*S2);
  /* G1 history: in = input peak, out = in + GR + the compressor's own make-up (Chromium adds 0.6 x the reduction at 0 dBFS) + Make-up */
  let H=st.h;if(!H){H=st.h={t:new Float64Array(512),i:new Float32Array(512),g:new Float32Array(512),n:0,w:0}}
  if(now-(H.lt||0)>12){H.lt=now;H.t[H.w]=now;H.i[H.w]=live?xin:-120;H.g[H.w]=live?gr:0;H.w=(H.w+1)%512;if(H.n<512)H.n++}
  const mk=-.6*ingRed(0,T,R,K)+p.makeup,bot=Math.max(-60,Math.min(-30,Math.floor((T-12)/6)*6)),o0=(H.w-H.n+512)%512;
  const wide=G.hw>110,r=INS.grh(g,G.hx0+(wide?14:0),oy,G.hw-(wide?14:0),S2,{n:H.n,age:i=>(now-H.t[(o0+i)%512])/1000,at:(i,A)=>{const k=(o0+i)%512;A[0]=H.i[k];A[2]=H.g[k];A[1]=H.i[k]+H.g[k]+mk},
    top:0,bot,thr:T,lab:wide?'out':null,rlab:wide?'in':null,leg:wide,num:wide?{x:G.hx0+G.hw-24,y:oy+16,al:'right'}:null});
  if(!wide){g.font='6.5px '+L.mono;g.fillStyle=L.mut;g.fillText('GR',ox+5,oy+30);ingNum(g,ox+20,oy+30,r.now,r.mx,'left',INSG.SPAN,1)}/* a narrow display: the numbers in the curve's empty corner */
  g.fillStyle='#fff';g.font='600 10.5px Inter,system-ui,sans-serif';g.fillText(`${INS.num(T,1)} dB · ${INS.num(R,1)}:1`,ox+5,oy+12);
  g.fillStyle='rgba(255,255,255,.45)';g.font='9px Inter,system-ui,sans-serif';g.fillText('GR',G.gx,h-1)}
/* ---------- Limiter: G1 on its own scale (-30 to +3 dB, the handles keep it) ---------- */
function ingLimit(g,w,h,f,X){const p=f.p;vbg(g,w,h);const L=INS.look(),T=10,Bm=h-12,dbY=db=>T+(1-clamp((db+30)/33,0,1))*(Bm-T),GX=26,GW=w-26-58,sr=(typeof ctx!=='undefined'&&ctx&&ctx.sampleRate)||48000,dt=1024/sr;
  const H=X?X.H:[],n=H.length;
  INS.grh(g,GX,T,GW,Bm-T,{n,age:i=>(n-1-i)*dt,at:(i,A)=>{const q=H[i];A[0]=toDb(q.i);A[1]=toDb(q.o);A[2]=toDb(q.g)},top:3,bot:-30,step:6,lstep:6,lab:'out',rlab:'out',num:{x:w-4,y:T+40,al:'right',small:1}});
  const yc=dbY(p.ceil);lineH(g,yc,GX+GW,'rgba(255,154,60,.9)',[6,3]);txt(g,'ceiling '+INS.num(p.ceil,1)+' dB',GX+GW-4,yc-4,'#ff9a3c',9,'right');
  if(X&&X.grM){X.grM*=.995}
  txt(g,(p.style||'transparent')+(p.tp!==false?' · true peak':' · sample peak'),GX+GW/2,Bm+10,'rgba(255,255,255,.4)',8,'center');
  g.font='6.5px '+L.mono;g.fillStyle=L.mut;g.textAlign='right';g.fillText('dBFS',GX-3,Bm+9);g.fillStyle=INSG.GRT;g.textAlign='left';g.fillText('GR',GX+GW+3,Bm+9);g.textAlign='left'}
/* ---------- Gate: G1 on its -80 to 0 scale; its open shading, lines and envelope stay ---------- */
function ingGate(g,SW,T,Bm,X,p){const sr=(typeof ctx!=='undefined'&&ctx&&ctx.sampleRate)||48000,dt=512/sr,H=X?X.H:[],n=H.length,R=80,dx=SW/(INSG.SPAN/dt);
  if(n>1){g.fillStyle='rgba(62,207,142,.1)';for(let i=0;i<n;i++){if(!H[i].open)continue;const x=SW-(n-1-i)*dx;if(x<0)continue;g.fillRect(x,T,dx+.6,Bm-T)}}
  const r=INS.grh(g,0,T,SW,Bm-T,{n,age:i=>(n-1-i)*dt,at:(i,A)=>{const q=H[i],gd=Math.max(-R,toDb(q.g));A[0]=Math.max(-120,q.lv);A[1]=A[0]+gd;A[2]=gd},top:0,bot:-R,step:12,lstep:12,lab:'in',rlab:null,leg:true});
  ingNum(g,SW-6,T+34,r.now,r.mx,'right',INSG.SPAN,1)}
/* ---------- Ducker (abxPaint): G1, the trigger stays in its track's colour; the reduction in red on the same dB scale ---------- */
function ingDuck(g,w,T,B,X,live,sc){const H=X&&X.H,n=H?H.k.length:0,sr=(typeof ctx!=='undefined'&&ctx&&ctx.sampleRate)||48000,dt=512/sr;if(!H||!live)return null;
  return INS.grh(g,0,T,w,B-T,{n,age:i=>(n-1-i)*dt,at:(i,A)=>{const k=(H.i+i)%n,v=H.k[k];A[0]=v>1e-6?20*Math.log10(v):-120;A[1]=0;A[2]=Math.max(-60,toDb(H.g[k]))},top:0,bot:-60,step:12,lstep:12,lab:'in',rlab:'in',inCol:sc,out:false,leg:false,grid:false})}
/* ---------- OTT: G4 per band beside the band's level ---------- */
function ingOTT(g,w,h,f,X){const L=INS.look(),p=f.p,cols=['#ff6b6b','#f5c84c','#4cc9f0'],labs=['LOW','MID','HIGH'],edge=['< 120 Hz','120 Hz to 2.5 kHz','> 2.5 kHz'],bw=(w-40)/3,y0=12,hh=h-32;
  for(let j=0;j<3;j++){const x=10+j*(bw+10),gx=x+bw-16,lwid=bw-40;let lv=0;if(X&&X.bands){X.bands[j].getFloatTimeDomainData(ottBuf);for(const v of ottBuf)lv=Math.max(lv,Math.abs(v))}
    const db=lv>1e-5?20*Math.log10(lv):-60,nn=clamp((db+60)/60,0,1),gr=X&&X.comps?Math.max(0,-X.comps[j].reduction):0;
    g.fillStyle='#14161c';g.fillRect(x,y0,lwid,hh);const gg=g.createLinearGradient(0,y0+hh,0,y0);gg.addColorStop(0,cols[j]+'55');gg.addColorStop(1,cols[j]);g.fillStyle=gg;g.fillRect(x,y0+hh*(1-nn),lwid,hh*nn);
    const ty=y0+hh*(1-clamp((-10-p.down/100*38+60)/60,0,1));g.strokeStyle='#fff';g.setLineDash([3,2]);g.beginPath();g.moveTo(x,ty);g.lineTo(x+lwid,ty);g.stroke();g.setLineDash([]);
    ingBar(g,gx,y0,12,hh,ingSt(f.id,'b'+j),gr,cols[j],{nums:true});
    g.font='600 9px Inter,system-ui,sans-serif';g.fillStyle='#cfd2da';g.fillText(labs[j],x+3,h-11);g.font='6.5px '+L.mono;g.fillStyle=L.mut;g.fillText(edge[j],x+3,h-3);
    g.fillStyle='#8a8d98';g.font='600 9px Inter,system-ui,sans-serif';g.textAlign='right';g.fillText((p[['lo','mid','hi'][j]]>0?'+':'')+INS.num(Math.round(p[['lo','mid','hi'][j]]),0)+' dB',x+lwid-2,h-11);g.textAlign='left';
    ingBarLab(g,gx+6,h-11,gr,'#ff8aa0')}
  g.fillStyle='rgba(255,255,255,.5)';g.font='9px Inter,system-ui,sans-serif';g.fillText('depth '+Math.round(p.depth)+'%',w-60,9);g.font='6.5px '+L.mono;g.fillStyle=L.mut;g.fillText('GR dB',10,9)}
/* ---------- Multiband Dynamics: G4 in the right column ---------- */
function ingMB(g,w,h,T,B,PW,p,X,ms,nb,id){const L=INS.look(),bs=ms?(X?X.MC:[]):(X?X.B:[]),col=['#ff6b6b','#f5c84c','#4cc9f0'],gx=PW+30,sp=(w-gx-4)/nb,bw=Math.min(18,sp-12),
  ed=ms?['mid','side']:['<'+ingHz(p.x1),ingHz(p.x1)+'-'+ingHz(p.x2),'>'+ingHz(p.x2)];
  g.font='6.5px '+L.mono;g.fillStyle=L.mut;g.fillText('GR dB',PW+12,T-5);
  for(let b=0;b<nb;b++){const bb=bs[b],red=bb?Math.max(0,-bb.comp.reduction):0,c2=ms?(b?'#b583ff':'#3ecf8e'):col[b],x=gx+b*sp;ingBar(g,x,T,bw,B-T,ingSt(id,'mb'+(ms?'s':'')+b),red,c2,{nums:b===0});ingBarLab(g,x+bw/2,B+9,red,c2,ed[b],sp<34?7.5:9)}}
/* ---------- De-Esser: the band's GR history on the studio scale with its G4 bar ---------- */
function ingDeess(g,w,h,T,B,PW,p,X,H,id){const L=INS.look(),n=H.length,last=H[n-1],gr=last?Math.max(0,last.gr):0,hx0=PW+14,bw=14,bx=w-10-bw,hw=bx-16-hx0,hh=B-T,sr=(typeof ctx!=='undefined'&&ctx&&ctx.sampleRate)||48000,dt=512/sr,q=Math.max(.3,p.q||1.5),
  f1=p.freq*(Math.sqrt(1+1/(4*q*q))-1/(2*q)),f2=p.freq*(Math.sqrt(1+1/(4*q*q))+1/(2*q));
  g.strokeStyle='rgba(255,255,255,.1)';g.lineWidth=INS.hair(g,L.lwGrid);g.strokeRect(INS.px(g,hx0),INS.px(g,T),hw,hh);
  g.strokeStyle=L.gMid;g.beginPath();for(const d of[1,3,6,10,20]){const yy=INS.px(g,ingGY(d,T,hh));g.moveTo(hx0,yy);g.lineTo(hx0+hw,yy)}g.stroke();
  g.font='6.5px '+L.mono;g.fillStyle=L.mut;g.fillText('REDUCTION, GR dB',hx0,T-4);
  if(n>1){const sp=hw/(INSG.SPAN/dt);g.save();g.beginPath();g.rect(hx0,T,hw,hh);g.clip();
    g.beginPath();g.moveTo(Math.max(hx0,hx0+hw-(n-1)*sp),T);for(let i=0;i<n;i++)g.lineTo(Math.max(hx0,hx0+hw-(n-1-i)*sp),ingGY(H[i].gr,T,hh));g.lineTo(hx0+hw,T);g.closePath();g.fillStyle=INSG.GRA;g.fill();
    g.beginPath();for(let i=0;i<n;i++){const x=Math.max(hx0,hx0+hw-(n-1-i)*sp),y=ingGY(H[i].gr,T,hh);i?g.lineTo(x,y):g.moveTo(x,y)}g.strokeStyle=INSG.GR;g.lineWidth=1.2;g.stroke();g.restore()}
  ingBar(g,bx,T,bw,hh,ingSt(id,'ds'),gr,'#ff6b6b',{nums:true});
  ingBarLab(g,hx0+hw/2,B+12,gr,gr>.3?'#ff6b6b':'rgba(255,255,255,.5)');g.font='6.5px '+L.mono;g.fillStyle=L.mut;g.textAlign='center';g.fillText(INS.num(f1/1000,1)+'-'+INS.num(f2/1000,1)+' kHz',bx+bw/2-8,B+12);g.textAlign='left'}
/* ===== end of lane E IN-G ===== */
