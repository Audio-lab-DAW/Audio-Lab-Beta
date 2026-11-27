/* ===== task MX-2 (lane K, mixing engine): delay compensation for every path (X5), latency you can see (X6), device automation in exports =====
   X5. One plan for the whole graph (mxSolve): each track's own latency (fxLat), its output (to the master, a group, a return or a track), its sends
   (before or after the fader) and every Ducker trigger. The longest path to the master sets the target; every link gets the delay that makes its sound
   arrive with the others, on the same sample, live and in export:
   - tracks keep today's delay after their effects (N.pdc), so a project whose sends, returns and triggers carry no latency builds exactly today's nodes;
   - a link that needs more gets a delay of its own (an output, a send, a trigger), made only when it is needed;
   - a trigger that would arrive late (the kick has a compressor) makes the ducked track wait instead (a delay at its input, before its devices);
   - a track that receives another track's output and has clips of its own gets the same input delay for its clips.
   Lane J's played-track exception: pdcMap(sr,live) asks LT_HOOKS.pdcLive() (when lane J has made it) which tracks are played live; those get no delay.
   Latency changes while playing fade the moved paths down and up in 8 ms each instead of jumping (no click); nothing runs while nothing changes.
   X6. A small grey read-out next to the name in the track's first device (the channel strip on the left), only when the track's own devices add latency.
   Hooks: MX_HOOKS.lat(t), devLat(t,f), pathLat() for lane I (a device's hover) and lane C (the routing map); links() gets each link's added delay.
   Export automation (the bug from the sound-quality research): S.pauto was applied only live (paApply, every 33 ms). renderMix now renders it:
   volume, pan and the master as curves on the audio parameters (every 64 samples), device parameters at every render block (128 samples, 2.7 ms at 48 kHz).
   Several features stop an offline render at the same moment (Vector Map, progress, automation): mxSuspWrap merges them so none is refused. */
let MXSOL=null;
function mxSolve(sr,live){const R={T:0,d:new Map(),c:new Map(),eo:new Map(),es:new Map(),ek:new Map(),I:new Map(),A:new Map(),L:new Map(),lv:null,crit:null};
  if(UI.pdc===false)return R;
  let LV=null;if(live){try{const h=typeof LT_HOOKS==='object'&&LT_HOOKS&&LT_HOOKS.pdcLive;if(typeof h==='function'){const r=h(sr);if(r&&(r.size||r.length)){LV=new Set();for(const x of r)LV.add(typeof x==='string'?x:x&&x.id)}}}catch(e){LV=null}}R.lv=LV;
  const TR=S.tracks,byId=new Map(TR.map(t=>[t.id,t])),OUT=new Map(),IN=new Map(),bus=new Set();
  for(const t of TR){OUT.set(t.id,[]);IN.set(t.id,[]);R.L.set(t.id,trkLat(t,sr))}
  const add=(k,a,b,x)=>{const E=Object.assign({k,a,b},x||{});OUT.get(a.id).push(E);if(b){IN.get(b.id).push(E);if(k!=='key')bus.add(b.id)}};
  for(const t of TR){add('out',t,mxDestT(t)||null);
    if(t.kind!=='return')for(const rid in t.sends||{}){const r=byId.get(rid);if(r&&t.sends[rid]>0&&mxSendOk(t,rid))add('send',t,r,{rid})}
    if(!t.fxByp){let pos=0;for(const f of t.fx||[]){if(!f||!f.on)continue;if(f.type==='duck'&&f.p&&typeof f.p.src==='string'){const s=byId.get(f.p.src);if(s&&s!==t&&!abxReach(t,s))add('key',s,t,{fx:f,pos})}pos+=fxLat(f,sr)}}}
  /* producers before consumers (the loop checks keep this graph free of loops; a loop written by hand is cut where it closes) */
  const ord=[],deg=new Map();for(const t of TR)deg.set(t.id,IN.get(t.id).length);const q=TR.filter(t=>!deg.get(t.id));
  while(q.length){const t=q.shift();ord.push(t);for(const E of OUT.get(t.id))if(E.b){const n=deg.get(E.b.id)-1;deg.set(E.b.id,n);if(!n)q.push(E.b)}}
  if(ord.length<TR.length)for(const t of TR)if(!ord.includes(t))ord.push(t);
  const pos=new Map(ord.map((t,i)=>[t.id,i])),fwd=E=>pos.get(E.a.id)<pos.get(E.b.id),isLV=t=>!!(LV&&LV.has(t.id)&&!bus.has(t.id));
  /* forward: the earliest each track's sound can be ready */
  const A=new Map();
  for(const t of ord){let i=0;if(!isLV(t))for(const E of IN.get(t.id)){if(!fwd(E)||isLV(E.a))continue;const a=A.get(E.a.id);const need=E.k==='key'?a-E.pos:a;if(need>i)i=need}
    A.set(t.id,i+R.L.get(t.id))}
  let T=0,ct=null;for(const t of TR){if(isLV(t))continue;if((t.kind==='group'||t.kind==='return')&&!IN.get(t.id).length)continue;/* an empty group or return makes no sound: it does not hold the others back */const E=OUT.get(t.id).find(e=>e.k==='out');if(E&&!E.b&&A.get(t.id)>T){T=A.get(t.id);ct=t}}
  R.T=T;R.A=A;
  /* backward: as late as allowed, so buses keep no delay of their own and the sources carry it, as before */
  const Iin=new Map(),Rout=new Map();
  for(let k=ord.length-1;k>=0;k--){const t=ord[k],id=t.id,L=R.L.get(id),ed=OUT.get(id);
    if(isLV(t)){Iin.set(id,0);Rout.set(id,L);R.d.set(id,0);R.c.set(id,0);continue}
    const req=E=>!E.b?T:!fwd(E)?A.get(id):E.k==='key'?Iin.get(E.b.id)+E.pos:Iin.get(E.b.id);
    let ro=Infinity;for(const E of ed){const v=req(E);if(v<ro)ro=v}if(!isFinite(ro))ro=T;
    let ii,dd;if(bus.has(id)){ii=Math.max(0,ro-L);dd=Math.max(0,ro-L-ii)}else{ii=A.get(id)-L;dd=Math.max(0,ro-ii-L)}
    Iin.set(id,ii);Rout.set(id,ii+L+dd);R.d.set(id,Math.min(sr,dd));
    if(t.kind!=='group'&&t.kind!=='return'&&ii>0)R.c.set(id,Math.min(sr,ii));
    for(const E of ed){const e=Math.max(0,Math.min(sr,req(E)-(ii+L+dd)));if(!(e>0))continue;if(E.k==='out')R.eo.set(id,e);else if(E.k==='send')R.es.set(id+'>'+E.rid,e);else R.ek.set(E.fx.id,e)}}
  R.I=Iin;
  /* the longest path, for the read-out: the track that sets it and the device on it with the most latency */
  if(ct&&T>0){let best=null,x=ct,n=0;const seen=new Set();while(x&&!seen.has(x.id)&&n++<64){seen.add(x.id);for(const f of x.fx||[]){const l=x.fxByp?0:fxLat(f,sr);if(l>0&&(!best||l>best.l))best={l,t:x,f}}x=mxDestT(x)}
    let src=ct;for(let g=0;g<64;g++){let up=null;for(const E of IN.get(src.id))if(E.k!=='key'&&A.get(E.a.id)+R.L.get(src.id)===A.get(src.id)){up=E.a;break}if(!up)break;src=up;for(const f of src.fx||[]){const l=src.fxByp?0:fxLat(f,sr);if(l>0&&(!best||l>best.l))best={l,t:src,f}}}
    R.crit={smp:T,t:src,dev:best}}
  return R}
/* the live delays move with a short fade (8 ms down, 8 ms up) while the song plays */
function mxDSet(dl,fg,sec){if(!dl)return;if(dl._mxv===undefined)dl._mxv=dl.delayTime.value;if(Math.abs(dl._mxv-sec)<1e-9)return;dl._mxv=sec;const now0=ctx.currentTime,now=now0+Math.min(.06,Math.max(.012,(ctx.baseLatency||.01)+.008));/* set a little ahead: the audio thread runs ahead of currentTime, so a fade that starts now may already be over when it gets there */
  if(!fg||!play.on||ctx.state!=='running'){try{dl.delayTime.cancelScheduledValues(now0)}catch(e){}dl.delayTime.setValueAtTime(sec,now0);return}
  const g=fg.gain;try{g.cancelScheduledValues(now);dl.delayTime.cancelScheduledValues(now)}catch(e){}g.setValueAtTime(g.value,now);g.linearRampToValueAtTime(0,now+.008);dl.delayTime.setValueAtTime(sec,now+.008);g.linearRampToValueAtTime(1,now+.016)}
const mxEdge=()=>{const g=ctx.createGain(),d=ctx.createDelay(1);d.delayTime.value=0;d._mxv=0;g.connect(d);return{g,d}};
/* the track's own delay after its effects (N.pdc): a fade node goes in the first time it moves while playing */
function mxPdcSet(N,d){if(d===N.pdcV)return;N.pdcV=d;if(!N.mxF&&play.on&&ctx.state==='running'){N.mxF=ctx.createGain();try{N.pdc.disconnect(N.ut.in)}catch(e){}N.pdc.connect(N.mxF);N.mxF.connect(N.ut.in)}
  if(N.pdc._mxv===undefined)N.pdc._mxv=N.pdc.delayTime.value;mxDSet(N.pdc,N.mxF||null,d)}
/* the input delay (a trigger that would arrive late, or the clips of a track that receives other tracks): N.in → N.mxc → N.mxh → the effects */
function mxHead(N,t,sr){const c=(MXSOL&&MXSOL.c.get(t.id)||0)/sr;if(!(c>0)&&!N.mxh)return;
  if(!N.mxh){N.mxh=ctx.createGain();N.mxc=ctx.createDelay(1);N.mxc.delayTime.value=0;N.mxc._mxv=0;N.mxcg=ctx.createGain();N.mxcg.connect(N.mxc);N.mxc.connect(N.mxh);N.mxhIn=null}
  if(N.mxhIn!==N.in){try{if(N.mxhIn)N.mxhIn.disconnect(N.mxcg)}catch(e){}N.in.connect(N.mxcg);N.mxhIn=N.in}
  mxDSet(N.mxc,N.mxcg,c)}
const mxInOf=N=>N?(N.mxh||N.in):master;
/* offline: a delay on a link only when it needs one */
function mxOffD(oc,from,to,smp){if(!from||!to)return;if(smp>0){const dl=oc.createDelay(1);dl.delayTime.value=smp/oc.sampleRate;from.connect(dl);dl.connect(to)}else from.connect(to)}
/* several features stop an offline render at the same moment: one real stop, resumed when the last of them is done */
function mxSuspWrap(oc){if(!oc||oc._mxS||typeof oc.suspend!=='function')return;oc._mxS=1;const S0=oc.suspend.bind(oc),R0=oc.resume.bind(oc),M=new Map();let cur=null;
  oc.suspend=function(t){const q=oc.renderQuantumSize||128,k=Math.floor(t*oc.sampleRate/q+1e-6);let e=M.get(k);if(!e){e={n:0};e.p=S0((k*q+.5)/oc.sampleRate).then(()=>{cur=e});M.set(k,e)}e.n++;return e.p};
  oc.resume=function(){const e=cur;if(e&&e.n>1){e.n--;return Promise.resolve()}cur=null;if(e)e.n=0;return R0()}}
/* parameter automation in an offline render */
function mxCurve(P,fn,sr,L){const stp=64,N=Math.max(2,Math.ceil(L/stp)+1),cv=new Float32Array(N);let same=true;for(let i=0;i<N;i++){cv[i]=fn(i*stp/sr);if(same&&Math.abs(cv[i]-cv[0])>1e-7)same=false}
  if(same){P.value=cv[0];return}try{P.setValueCurveAtTime(cv,0,(N-1)*stp/sr)}catch(e){console.warn('AudioLab automation curve',e);P.value=cv[0]}}
function mxPaPlan(oc,b0,NN,FXN,mst,fast){const A=S.pauto;if(!A)return 0;const ids=Object.keys(A).filter(k=>A[k]&&A[k].length);if(!ids.length)return 0;
  const sr=oc.sampleRate,q=oc.renderQuantumSize||128,s0=secOf(b0),L=oc.length,B=tau=>beatOf(s0+tau),E=new Map(),vmR=new Set(),jobs=new Map();let n=0;
  try{for(const e of paEnum())E.set(e.id,e)}catch(e){}
  for(const t of S.tracks)for(const m of t.mods||[])if(m&&m.type==='vmap'&&!m.off)for(const r of m.routes||[])vmR.add(r.pid);
  for(const id of ids){if(vmR.has(id))continue;const pts=A[id],pp=id.split(':'),own=paOwner(id);if(own&&own.read===false)continue;
    if(pp[0]==='t'&&(pp[2]==='vol'||pp[2]==='pan')){const x=NN.get(pp[1]);if(!x)continue;if(pp[2]==='vol'){if(!x.aud||!x.vol)continue;mxCurve(x.vol.gain,tau=>SPEC_VOL.v(envAt(pts,B(tau),.5)),sr,L)}else mxCurve(x.pn.pan,tau=>SPEC_PAN.v(envAt(pts,B(tau),.5)),sr,L);n++}
    else if(pp[0]==='m'&&pp[1]==='master'){if(fast)continue;mxCurve(mst.gain,tau=>{const db=SPEC_MASTER.v(envAt(pts,B(tau),.5));return db<=-60?0:(UI.bitPerfect?1:Math.pow(10,(UI.headroom??-6)/20))*Math.pow(10,db/20)},sr,L);n++}
    else if(pp[0]==='f'){const J=FXN.get(pp[2]);if(!J)continue;const k=pp.slice(3).join(':'),e=E.get(id),G=FXDEF[J.f.type],sp=e&&e.spec?e.spec:(G&&G.p&&G.p[k]?specD(G.p[k]):null);if(!sp)continue;
      let j=jobs.get(pp[2]);if(!j){j={J,ks:[],last:[]};jobs.set(pp[2],j)}j.ks.push([k,sp,pts]);j.last.push(NaN);n++}}
  if(!jobs.size)return n;
  const apply=(tau,force)=>{const b=B(tau);for(const j of jobs.values()){let ch=force;const vs=j.ks.map(([k,sp,pts],i)=>{const v=envAt(pts,b,.5);if(!(Math.abs(v-j.last[i])<1e-4)){ch=true}return v});if(!ch)continue;
      const p=Object.assign({},j.J.f.p);j.ks.forEach(([k,sp],i)=>{j.last[i]=vs[i];p[k]=sp.v(vs[i])});try{j.J.x.set(p)}catch(e){}}};
  apply(0,true);
  for(let i=1;i*q<L;i++){const tau=i*q/sr,b=B(tau);let ch=false;for(const j of jobs.values()){j.ks.forEach(([k,sp,pts],m)=>{if(!ch&&!(Math.abs(envAt(pts,b,.5)-(j.nx?j.nx[m]:j.last[m]))<1e-4))ch=true})}
    if(!ch)continue;for(const j of jobs.values())j.nx=j.ks.map(([k,sp,pts])=>envAt(pts,b,.5));
    try{oc.suspend(tau).then(()=>{apply(tau,false);return oc.resume()}).catch(()=>{})}catch(e){}}
  return n}
/* ---- X6: latency you can see, in few places ---- */
const mxMs=(n,sr)=>(n/sr*1000).toFixed(1);
const mxSr=()=>ctx?ctx.sampleRate:(UI.sr||48000);
function mxLatTip(t){const sr=mxSr(),n=trkLat(t,sr),X=MXSOL&&MXSOL.crit,P=UI.pdc===false;
  let s='The devices on '+t.name+' delay its sound by '+mxMs(n,sr)+' ms ('+n+' samples).';
  s+=P?' Delay compensation is off, so it plays this much late.':' AudioLab delays the other tracks, sends and returns to match, so everything stays in time.';
  if(!P&&X&&X.smp>0){s+=' Longest path in the song: '+mxMs(X.smp,sr)+' ms ('+X.t.name+(X.dev?', '+((FXDEF[X.dev.f.type]||{}).name||X.dev.f.type)+(X.dev.t!==X.t?' on '+X.dev.t.name:''):'')+').'}
  return s}
function mxLatPaint(){const D=document.querySelector('#fxin .tdev2[data-id]');if(!D)return;const t=trkById(D.dataset.id),nm=D.querySelector('.devh .tdn');if(!nm)return;let o=nm.querySelector('.mxlat');
  const n=t?trkLat(t,mxSr()):0;if(!(n>0)){if(o)o.remove();return}
  if(!o){o=document.createElement('small');o.className='mxlat';nm.appendChild(o)}const v=mxMs(n,mxSr()),k=v+'|'+(UI.pdc===false);if(o._k!==k){o._k=k;o.innerHTML=v+' <span class="lku">ms</span>'}
  o.classList.toggle('off',UI.pdc===false);o.title=mxLatTip(t);o.setAttribute('aria-label','Latency '+v+' ms')}
{const _rf=renderFx;renderFx=function(){const r=_rf.apply(this,arguments);try{mxLatPaint()}catch(e){console.error('AudioLab latency read-out',e)}return r}}
Object.assign(MX_HOOKS,{
  /* a track's own latency */
  lat(t){const sr=mxSr(),n=t?trkLat(t,sr):0;return{smp:n,ms:n/sr*1000}},
  /* one device's latency (for a device's hover in its title strip, lane I) */
  devLat(t,f){const sr=mxSr(),n=f&&!(t&&t.fxByp)?fxLat(f,sr):0;return{smp:n,ms:n/sr*1000,text:n>0?mxMs(n,sr)+' ms':''}},
  /* the longest path to the master: its length, the track that sets it and the device on it with the most latency */
  pathLat(){const sr=mxSr(),X=MXSOL||mxSolve(sr,false),c=X.crit;return{smp:X.T,ms:X.T/sr*1000,track:c?c.t:null,dev:c&&c.dev?c.dev.f:null,devTrack:c&&c.dev?c.dev.t:null}},
  /* the whole plan: delays per track and per link, in samples */
  pdcPlan:sr=>mxSolve(sr||mxSr(),false)});
{const _lk=MX_HOOKS.links;MX_HOOKS.links=function(){const L=_lk.apply(this,arguments),sr=mxSr(),X=MXSOL||mxSolve(sr,false);
  for(const l of L){const n=l.k==='out'?X.eo.get(l.a.id):l.k==='send'?X.es.get(l.a.id+'>'+l.b.id):l.fx?X.ek.get(l.fx.id):0;l.lat=(n||0)/sr*1000}return L}}
