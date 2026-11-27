/* ===== task MX-2 (lane K, mixing engine): device automation in export; delay compensation for every path (X5); latency you can see (X6) =====
   1. Export: S.pauto (track volume and pan, master volume, device parameters, instrument parameters, macros through their targets) is built into
      the offline render: AudioParam curves for volumes and pans (a point every 256 samples, linear between), device parameters set every 256
      samples while rendering (only where the value moves), instrument parameters at each note's start (as the Vector Map does).
      Live playback sets them every 33 ms (paApply), so live and export differ only by that stepping.
   2. pdcMap(sr, live): one solve over the whole graph: every track's output (master, group, return or track), every send (before or after the
      fader) and every Ducker trigger, with the latency each track's devices report (fxLat). The latest-possible schedule: buses are not
      delayed, so a project with groups only gets exactly the delays it had before; the extra a send, an output or a trigger needs is put on
      that edge alone (M.edge). A track whose Ducker takes a trigger gets its delay before its devices (M.pre), so the trigger meets
      the sound at the device. Delays are never negative. A track that has clips and also receives another track's output: its clips are not
      delayed to meet that sound (the incoming sound is lined up, the clips start on time).
   3. A small read-out on the track's first device when its devices add latency; hooks for the device hover and the routing map. */
let MXPML=null;
/* the delay of a live path moves under a short dip (4 ms down, 4 ms up) instead of jumping, so it does not click */
function mxDelaySet(dl,g,v,back){const now=ctx.currentTime;if(!g){dl.delayTime.setValueAtTime(v,now);return}const f=.004;try{g.cancelScheduledValues(now);g.setValueAtTime(g.value,now);g.linearRampToValueAtTime(0,now+f);dl.delayTime.setValueAtTime(v,now+f);g.linearRampToValueAtTime(back,now+2*f)}catch(e){dl.delayTime.setValueAtTime(v,now)}}
function mxOffCon(oc,a,b,smp){if(smp>0){const d=oc.createDelay(1);d.delayTime.value=Math.min(oc.sampleRate,smp)/oc.sampleRate;a.connect(d);d.connect(b)}else a.connect(b)}
/* the latency of the devices before device f on track t (where a trigger enters) */
function mxLatBefore(t,f,sr){if(t.fxByp)return 0;let n=0;for(const x of t.fx||[]){if(x===f)break;n+=fxLat(x,sr)}return n}
function mxKeyEdges(){const L=[];for(const t of S.tracks){if(t.fxByp)continue;for(const f of t.fx||[]){if(f.type!=='duck'||!f.on||!f.p||typeof f.p.src!=='string')continue;const s=trkById(f.p.src);if(s&&s!==t&&!abxReach(t,s))L.push({k:'sc',a:s,b:t,f})}}return L}
function pdcMap(sr,live){const M=new Map();M.target=0;M.edge=new Map();M.lat=new Map();M.pre=new Set();M.crit=null;if(UI.pdc===false)return M;
  let LV=null;try{if(live&&typeof LT_HOOKS!=='undefined'&&typeof LT_HOOKS.pdcLive==='function')LV=LT_HOOKS.pdcLive()}catch(e){LV=null}
  const T=S.tracks,L=new Map(),E=[],inc=new Map(),outs=new Map();for(const t of T){L.set(t.id,trkLat(t,sr));inc.set(t.id,[]);outs.set(t.id,[])}
  for(const t of T){const d=mxDestT(t);E.push({k:'out',a:t,b:d||null,key:'o:'+t.id});if(t.kind!=='return')for(const rid in t.sends||{})if(t.sends[rid]>0&&mxSendOk(t,rid))E.push({k:'send',a:t,b:trkById(rid),key:'s:'+t.id+':'+rid})}
  for(const e of mxKeyEdges()){e.lb=mxLatBefore(e.b,e.f,sr);e.key='k:'+e.f.id;E.push(e)}
  for(const e of E){outs.get(e.a.id).push(e);if(e.b)inc.get(e.b.id).push(e)}
  /* earliest: when each input can be ready */
  const ei=new Map(),pre=new Map();for(const t of T)ei.set(t.id,0);
  for(let it=0,ch=true;ch&&it<=T.length+1;it++){ch=false;for(const t of T){let v=0,p=null;for(const e of inc.get(t.id)){const w=ei.get(e.a.id)+L.get(e.a.id)-(e.k==='sc'?e.lb:0);if(w>v){v=w;p=e}}if(v!==ei.get(t.id)){ei.set(t.id,v);pre.set(t.id,p);ch=true}}}
  let tg=0,last=null;for(const e of E)if(e.k==='out'&&!e.b){const w=ei.get(e.a.id)+L.get(e.a.id);if(w>tg){tg=w;last=e.a}}
  M.target=tg;for(const t of T)M.lat.set(t.id,L.get(t.id));
  if(last){let x=last,best=null,bl=0,n=0;while(x&&n++<64){if(!x.fxByp)for(const f of x.fx||[]){const l=fxLat(f,sr);if(l>bl){bl=l;best={t:x,f}}}const p=pre.get(x.id);x=p?p.a:null}M.crit={t:last,dev:best}}
  if(!(tg>0))return M;
  /* latest: when each input has to be ready so that everything meets at the master at the same time */
  const In=new Map(),req=e=>e.b?In.get(e.b.id)+(e.k==='sc'?e.lb:0):tg;for(const t of T)In.set(t.id,tg);
  for(let it=0,ch=true;ch&&it<=T.length+1;it++){ch=false;for(const t of T){let r=Infinity;for(const e of outs.get(t.id)){const q=e.b&&!In.has(e.b.id)?tg:req(e);if(q<r)r=q}if(r===Infinity)r=tg;const v=r-L.get(t.id);if(v!==In.get(t.id)){In.set(t.id,v);ch=true}}}
  for(const t of T){const bus=inc.get(t.id).some(e=>e.k!=='sc'),d=bus||(LV&&LV.has&&LV.has(t.id))?0:Math.max(0,Math.min(sr,In.get(t.id)));M.set(t.id,d);if(!bus&&d>0&&inc.get(t.id).length)M.pre.add(t.id);/* a track a trigger enters: its delay goes before its devices, so the keyed device sees it */
    const out=(bus?In.get(t.id):d)+L.get(t.id);for(const e of outs.get(t.id)){const pad=Math.max(0,Math.min(sr,Math.round(req(e)-out)));if(pad>0)M.edge.set(e.key,pad)}}
  return M}
/* ---- export of automation ---- */
function mxPaSrc(){const pa=S.pauto||{},src=new Map();
  const vmOwn=new Set();for(const t of S.tracks)for(const m of t.mods||[])if(m.type==='vmap'&&!m.off)for(const r of m.routes||[])vmOwn.add(r.pid);
  const own=id=>{const p=id.split(':');return p[0]==='m'?null:trkById(p[1])};
  for(const id in pa){const pts=pa[id];if(!pts||!pts.length||vmOwn.has(id))continue;const o=own(id);if(o&&o.read===false)continue;
    if(id.startsWith('x:')){const p=id.split(':'),t=trkById(p[1]),it=t&&t.macro&&(t.macro.items||[]).find(q=>q.id===p.slice(2).join(':'));if(!it)continue;
      for(const r of it.routes||[]){if(r.ax==='y'||pa[r.pid]&&pa[r.pid].length||vmOwn.has(r.pid))continue;src.set(r.pid,b=>{let f=envAt(pts,b,.5);if(r.inv)f=1-f;return clamp(r.a+(r.b-r.a)*f,0,1)})}continue}
    src.set(id,b=>envAt(pts,b,.5))}
  return src}
function mxPaSpec(){const m=new Map();try{for(const e of paEnum())m.set(e.id,e)}catch(err){}return id=>m.get(id)||PAREG.get(id)||null}
const mxMG=db=>db<=-60?0:(UI.bitPerfect?1:Math.pow(10,(UI.headroom??-6)/20))*Math.pow(10,db/20);
function mxPaPlan(oc,b0,R,fast){if(!S.pauto)return;const src=mxPaSrc();if(!src.size)return;const sp=mxPaSpec(),sr=oc.sampleRate,STP=256,len=oc.length,N=Math.ceil(len/STP)+1,s0=secOf(b0||0),bAt=fr=>beatOf(s0+fr/sr),jobs=new Map();
  const curve=(fn,map)=>{const cv=new Float32Array(N);for(let i=0;i<N;i++)cv[i]=map(fn(bAt(i*STP)));return cv},put=(prm,cv)=>{try{prm.cancelScheduledValues(0);prm.setValueCurveAtTime(cv,0,(N-1)*STP/sr)}catch(err){console.warn('AudioLab automation curve',err)}};
  for(const[id,fn] of src){const p=id.split(':'),e=sp(id);
    if(p[0]==='m'&&p[1]==='master'){if(fast||!R.mst||!e)continue;put(R.mst.gain,curve(fn,n=>mxMG(e.spec.v(n))))}
    else if(p[0]==='t'&&(p[2]==='vol'||p[2]==='pan')){const r=R.trk.get(p[1]);if(!r||!e||(p[2]==='vol'&&!r.aud))continue;put(p[2]==='vol'?r.vol.gain:r.pn.pan,curve(fn,n=>e.spec.v(n)))}
    else if(p[0]==='f'){const r=R.fx.get(p[2]);if(!r||!e)continue;let j=jobs.get(p[2]);if(!j){j={r,ks:[]};jobs.set(p[2],j)}j.ks.push([p.slice(3).join(':'),fn,e])}}
  if(!jobs.size)return;const J=[...jobs.values()],val=(j,fr)=>{const b=bAt(fr),o={};for(const[k,fn,e] of j.ks)o[k]=e.spec.v(fn(b));return o};
  const last=new Map();const apply=(j,o)=>{try{j.r.x.set(Object.assign({},j.r.f.p,o))}catch(err){}};
  for(const j of J){const o=val(j,0);apply(j,o);last.set(j,o)}
  for(let fr=STP/2;fr<len;fr+=STP){const ch=[];for(const j of J){const o=val(j,fr),l=last.get(j);let d=false;for(const k in o)if(Math.abs(o[k]-l[k])>1e-9*Math.max(1,Math.abs(o[k]))){d=true;break}if(d){ch.push([j,o]);last.set(j,o)}}
    if(!ch.length)continue;try{oc.suspend(fr/sr).then(()=>{for(const[j,o] of ch)apply(j,o);return oc.resume()}).catch(()=>{for(const[j,o] of ch)apply(j,o)})}catch(err){}}}
/* instrument parameters: set for the moment a note starts in an export, then put back (as the Vector Map does) */
const MXOFI=new WeakMap();
function mxInstAt(c,I,beat){let L=MXOFI.get(c);if(L===undefined){L=null;try{if(S.pauto){const src=mxPaSrc(),sp=mxPaSpec();for(const[id,fn] of src){const p=id.split(':');if(p[0]!=='i'&&p[0]!=='c')continue;const t=trkById(p[1]),e=sp(id);if(!t||!t.inst||!e)continue;L=L||new Map();let a=L.get(t.inst);if(!a)L.set(t.inst,a=[]);a.push([e,fn])}}}catch(err){L=null}MXOFI.set(c,L)}
  const a=L&&L.get(I);if(!a)return null;const back=[];for(const[e,fn] of a){try{const v0=e.get();e.set(e.spec.v(fn(beat)));back.push([e,v0])}catch(err){}}return back}
{const _s=synthB;synthB=function(c,I,dest,p,w,dur,v,clip,ns,spb){let back=null;if(c!==ctx&&clip&&typeof OfflineAudioContext!=='undefined'&&c instanceof OfflineAudioContext){try{back=mxInstAt(c,I,clip.start+(ns||0)-(clip.off||0))}catch(e){back=null}}
  if(!back||!back.length)return _s.apply(this,arguments);try{return _s.apply(this,arguments)}finally{for(const[e,v0] of back){try{e.set(v0)}catch(_){}}}}}
/* ---- X6: latency you can see, in few places ---- */
const mxMs=(smp,sr)=>(smp/sr*1000).toFixed(1);
function mxLatInfo(t){if(!ctx||!t)return null;const sr=ctx.sampleRate,M=MXPML||pdcMap(sr),own=trkLat(t,sr);let crit='';if(M.crit&&M.target>0){const c=M.crit;crit=' Longest path in the song: '+mxMs(M.target,sr)+' ms ('+c.t.name+(c.dev?', '+((FXDEF[c.dev.f.type]||{}).name||c.dev.f.type):'')+').'}
  return{own,ms:mxMs(own,sr),sr,tip:'This track’s devices delay its sound by '+mxMs(own,sr)+' ms ('+own+' samples). AudioLab delays the other tracks to match.'+crit+(UI.pdc===false?' Delay compensation is switched off in Settings.':'')}}
function mxLatShow(){const d=document.querySelector('#fxin .tdev2[data-id]');if(!d)return;const t=trkById(d.dataset.id),h=d.querySelector('.devh');if(!h)return;let el=h.querySelector('.mxlat');const I=t&&mxLatInfo(t);
  if(!I||!(I.own>0)){if(el)el.remove();return}if(!el){el=document.createElement('small');el.className='mxlat';const n=h.querySelector('.tdn');(n||h.firstChild).after(el)}
  const tx=I.ms+' ms';if(el.textContent!==tx)el.textContent=tx;if(el.title!==I.tip)el.title=I.tip}
{const _rf=renderFx;renderFx=function(){const r=_rf.apply(this,arguments);try{mxLatShow()}catch(e){}return r}}
Object.assign(MX_HOOKS,{
  /* a track's own latency, a device's latency, and the longest path: {smp, ms} */
  lat(t){if(!t)return null;const sr=ctx?ctx.sampleRate:48000,n=trkLat(t,sr);return{smp:n,ms:+mxMs(n,sr)}},
  devLat(t,f){if(!f)return null;const sr=ctx?ctx.sampleRate:48000,n=fxLat(f,sr);return{smp:n,ms:+mxMs(n,sr)}},
  pathLat(){const sr=ctx?ctx.sampleRate:48000,M=MXPML||pdcMap(sr);return{smp:M.target,ms:+mxMs(M.target,sr),track:M.crit?M.crit.t:null,dev:M.crit&&M.crit.dev?M.crit.dev.f:null}},
  /* the delay compensation map: d per track (samples) and pads per link (M.edge: 'o:<track>', 's:<track>:<return>', 'k:<device>') */
  pdc:sr=>pdcMap(sr||(ctx?ctx.sampleRate:48000))});
{const _lk=MX_HOOKS.links;MX_HOOKS.links=function(){const L=_lk.apply(this,arguments);try{const M=MXPML;if(M&&M.edge)for(const l of L){const k=l.k==='out'?'o:'+l.a.id:l.k==='send'?'s:'+l.a.id+':'+l.b.id:l.fx?'k:'+l.fx.id:'';l.lat=M.edge.get(k)||0}}catch(e){}return L}}
