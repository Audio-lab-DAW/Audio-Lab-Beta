/* ===== lane E (task IN-L): loudness, L2 (the loudness history) =====
   The user's pick L2 (docs/design-round-4-instruments.md): a history graph like iZotope Insight and NUGEN VisLM. Short-term loudness is the line,
   momentary faint behind it, integrated dashed (amber, the unit colour), the target band ±1 LU shaded green; where the short-term line goes above the
   band it turns yellow, and red more than 3 LU above (the same rule as the top-bar number: green within ±1 LU, yellow to +3, red above). LUFS on the
   left, time marks along the bottom. One drawer, INS.lhist, for every place:
   - the loudness pop-up (#lufsPop): the last 30 s, momentary and short-term sampled 10 times a second from LM (what the al-meter worklet already
     sends; no new audio work), redrawn 10 times a second while it is open (half that at the Light level)
   - the top-bar box (.lfgr): the last 30 s, short-term only, 4 times a second as before
   - the mixer's master box (.mxme Target row): the last 30 s under the target read-out, at the mixer's slow rate
   - the Loudness device (ND loud): its own measurement, 60 s as before, on its own scale (the target line is still dragged on it)
   - the Meter device (ND measure): its own history, the whole measurement as before (at least 60 s, up to 10 minutes)
   The loudness range (LRA, EBU Tech 3342) is marked as settling for the first 60 s of measurement after a reset (Tech 3341: "not yet stable"):
   dimmed in the Loudness device, "settling" in the Meter device. (X15, the ± settling read-out, is task SC-K's; it can take this over.) */
INS.lhist=function(g,x,y,w,h,o){/* o: lo, hi (LUFS shown), target, tol (band, ±LU), n, M(i), S(i) (oldest first; below −69 = no sound), span (samples across the width), dt (s per sample),
     I (integrated, dashed), step and major (grid, LU), rel (grid from the target), lab (numbers), labIn (numbers inside on the left), fs, tm (time marks), tlab (their numbers), mOff (no momentary line), legend */
  const L=INS.look(),lo=o.lo,hi=o.hi,T=o.target,tol=o.tol==null?1:o.tol,Y=v=>y+h-h*(Math.max(lo,Math.min(hi,v))-lo)/(hi-lo),n=o.n|0,span=Math.max(2,o.span||n,n),dx=w/(span-1),xr=x+w;
  {const a=Y(T+tol),b=Y(T-tol);g.fillStyle='rgba(62,207,142,.12)';g.fillRect(x,a,w,Math.max(1,b-a))}
  if(o.grid!==false){const st=o.step||3,mj=o.major||6,base=o.rel===false?0:T,on=(v,m)=>Math.abs((v-base)/m-Math.round((v-base)/m))<1e-6;g.lineWidth=INS.hair(g,L.lwGrid);
    for(const m of[0,1]){g.strokeStyle=m?L.gMaj:L.gMid;g.beginPath();for(let v=base+Math.ceil((lo-base)/st-1e-9)*st;v<=hi+1e-9;v+=st){if(on(v,mj)!==!!m)continue;const yy=INS.px(g,Y(v));g.moveTo(x,yy);g.lineTo(xr,yy)}g.stroke()}
    if(o.lab!==false){g.font=(o.fs||7)+'px '+L.mono;g.textBaseline='middle';g.textAlign=o.labIn?'left':'right';let last=-1e9;
      for(let v=base+Math.floor((hi-base)/mj+1e-9)*mj;v>=lo-1e-9;v-=mj){const yy=Y(v);if(yy-last<(o.gap||9)||yy<y+3||yy>y+h-3)continue;last=yy;g.fillStyle=Math.abs(v-T)<1e-6?L.unit:L.mut;g.fillText(INS.num(v,0),o.labIn?x+2:x-3,o.labIn?yy-4:yy)}}}
  if(o.tm!==false&&o.dt){const tot=(span-1)*o.dt,sts=[5,10,15,30,60,120,300,600];let st=sts[sts.length-1];for(const s of sts)if(tot/s<=8){st=s;break}
    g.lineWidth=INS.hair(g,L.lwLine);g.strokeStyle=L.tick;g.beginPath();for(let s=0;s<=tot+1e-9;s+=st){const xx=INS.px(g,xr-s/o.dt*dx);g.moveTo(xx,y+h);g.lineTo(xx,y+h-3)}g.stroke();
    if(o.tlab){g.font=(o.fs||7)+'px '+L.mono;g.textBaseline=o.tlab==='in'?'bottom':'top';g.fillStyle=L.mut;let last=-1e9;for(let s=0;s<=tot+1e-9;s+=st){const xx=xr-s/o.dt*dx,t=s?INS.MIN+(s>=60?(s/60)+' min':s+' s'):'now';
      g.textAlign=s?'center':'right';const tw=g.measureText(t).width,l0=s?xx-tw/2:xx-tw;if(xr-l0-tw<last||l0<x)continue;last=xr-l0+3;g.fillText(t,s?xx:xx-1,o.tlab==='in'?y+h-4:y+h+2)}}}
  if(n>1){/* at most about one point per pixel: the loudest value of each pixel's samples */const k=Math.max(1,Math.floor(n/Math.max(8,w))),pts=INS._lp||(INS._lp=[]);let m=0;
    for(let i=0;i<n;i+=k){let vm=-200,vs=-200;for(let q=i;q<Math.min(n,i+k);q++){const a=o.M?o.M(q):-200,b=o.S(q);if(a>vm)vm=a;if(b>vs)vs=b}pts[m++]=[x+w-(n-1-i)*dx,vm,vs]}
    if(o.M&&!o.mOff){g.lineWidth=INS.hair(g,L.lwCurve);g.strokeStyle='rgba(255,255,255,.25)';g.beginPath();let on=false;for(let j=0;j<m;j++){const p=pts[j];if(p[1]<-69){on=false;continue}const yy=Y(p[1]);if(on)g.lineTo(p[0],yy);else{g.moveTo(p[0],yy);on=true}}g.stroke()}
    g.lineWidth=o.lw||1.4;g.lineJoin='round';const cols=['#4cc9f0','#f5c84c','#ff6b6b'];for(let c=0;c<3;c++){g.strokeStyle=cols[c];g.beginPath();for(let j=1;j<m;j++){const a=pts[j-1],b=pts[j];if(a[2]<-69||b[2]<-69)continue;const cc=b[2]>T+3?2:b[2]>T+tol?1:0;if(cc!==c)continue;g.moveTo(a[0],Y(a[2]));g.lineTo(b[0],Y(b[2]))}g.stroke()}}
  if(o.I>-69){g.save();g.setLineDash([4,3]);g.lineWidth=1;g.strokeStyle=L.unit;const yy=INS.px(g,Y(o.I));g.beginPath();g.moveTo(x,yy);g.lineTo(xr,yy);g.stroke();g.restore()}
  if(o.legend){g.font='600 '+(o.fs||7)+'px '+L.mono;g.textBaseline='top';g.textAlign='left';let lx=x+(o.labIn?24:4);for(const[t,c] of[['S','#4cc9f0'],['M','rgba(255,255,255,.5)'],['I',L.unit],['TARGET ±'+INS.num(tol,0)+' LU','rgba(62,207,142,.9)']]){g.fillStyle=c;g.fillText(t,lx,y+3);lx+=g.measureText(t).width+7}}
  return Y};
/* the master's history: momentary and short-term 10 times a second from LM (the readings the al-meter worklet already sends), 60 s kept; while nothing plays
   and nothing sounds, nothing is added (the graph stands still, as today's did); a reset (LM.hist made new and empty) clears it */
const INL={N:600,M:new Float32Array(600),S:new Float32Array(600),i:0,n:0,ref:null,pk:0,
  push(m,s){INL.M[INL.i]=m;INL.S[INL.i]=s;INL.i=(INL.i+1)%INL.N;if(INL.n<INL.N)INL.n++},
  at(arr,q,cnt){/* q-th of the newest cnt samples, oldest first */return arr[(INL.i-cnt+q+INL.N*2)%INL.N]},
  draw(g,x,y,w,h,secs,o){const cnt=Math.min(INL.n,Math.round(secs*10)),T=lmTarget()[2];return INS.lhist(g,x,y,w,h,Object.assign({lo:T-24,hi:T+9,target:T,n:cnt,span:secs*10,dt:.1,M:q=>INL.at(INL.M,q,cnt),S:q=>INL.at(INL.S,q,cnt),I:LM.I},o||{}))}};
setInterval(()=>{try{if(LM.hist!==INL.ref){INL.ref=LM.hist;if(!LM.hist.length){INL.n=0;INL.i=0}}if(!LM.w)return;const act=(typeof play==='object'&&play.on)||(typeof LIVE!=='undefined'&&LIVE.size>0)||LM.S>-69||LM.M>-69;if(act)INL.push(LM.M,LM.S)}catch(e){}},100);
/* the pop-up's graph (replaces its own drawing), 10 times a second while open */
function inlPop(){const cv=document.getElementById('lmC');if(!cv||!cv.offsetParent)return;const{g,w,h}=fit(cv);g.clearRect(0,0,w,h);INL.draw(g,28,6,w-34,h-20,30,{lab:true,fs:7.5,tlab:true,legend:true})}
setInterval(function inlTick(){/* a screen-only timer like lmPaint's, so the background freeze stops it (AOVIS) */if(!LMP||document.hidden)return;INL.pk=(INL.pk+1)%2;if(INS.lite()&&INL.pk)return;try{inlPop()}catch(e){}},100);
/* the top-bar box's little graph: the last 30 s of short-term, the band, the colour rule */
function inlTop(cv){const{g,w,h}=fit(cv),T=lmTarget()[2];g.clearRect(0,0,w,h);INL.draw(g,0,1,w,h-2,30,{lo:T-18,hi:T+6,grid:false,tm:false,mOff:true,I:-90,lw:1.3})}
/* the mixer's master box: the same little graph under the target read-out (its bar is replaced by it) */
function inlMx(){const w=document.getElementById('mixWin');if(!w||w.hidden)return;const tg=w.querySelector('.mxme .mxtg');if(!tg)return;let cv=tg.querySelector('canvas.inlh');
  if(!cv){tg.insertAdjacentHTML('beforeend','<canvas class="inlh" aria-hidden="true"></canvas>');cv=tg.querySelector('canvas.inlh')}if(!cv.offsetParent)return;const{g,w:W,h}=fit(cv),T=lmTarget()[2];g.clearRect(0,0,W,h);INL.draw(g,0,1,W,h-2,30,{lo:T-18,hi:T+6,grid:false,tm:false,mOff:true,I:-90,lw:1.2})}
{const _mxL=mxsMaster;mxsMaster=function(){const r=_mxL.apply(this,arguments);try{inlMx()}catch(e){}return r}}
/* the Meter device's history: the same drawer on its own data (the whole measurement, as before) */
msuHist=function(g,x,y,w,h,X,T){const lo=Math.min(-40,T[1]-20),hi=0,n=X.hn|0,k0=(X.hi-n+6000)%6000;g.fillStyle='rgba(255,255,255,.025)';g.fillRect(x,y,w,h);
  const Yf=INS.lhist(g,x,y,w,h,{lo,hi,target:T[1],tol:T[4],n,span:Math.max(600,n),dt:.1,M:q=>X.hM[(k0+q)%6000],S:q=>X.hS[(k0+q)%6000],I:X.I,step:10,major:10,rel:false,labIn:true,fs:8,tlab:'in'});
  g.fillStyle='rgba(62,207,142,.8)';g.fillRect(x,Yf(T[1]),w,1);txt(g,'target '+T[1],x+w-4,Yf(T[1])-3,'#3ecf8e',8,'right')};
/* the Loudness device: LRA settling for the first 60 s of sound after a reset */
function inlSettle(H){if(!H)return 0;let c=0;for(let i=0;i<H.length;i++)if(H[i].S>-70)c++;return c}
/* ===== end of lane E IN-L ===== */
