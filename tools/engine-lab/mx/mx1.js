/* ===== task MX-1 (lane K, mixing engine): pre or post per send (X12), output to any group, return or track (X13) =====
   Project data (both optional; absent means what AudioLab did before):
   - t.sendPre = {returnId: true}: that send is taken before the fader (after the track's effects, delay compensation, width, phase and trim),
     so fading the track keeps its send. It still follows Mute and Solo. Absent: after the fader and the pan, as before.
   - t.out = id of a group, a return or another track, or 'master'. Absent: the group the track sits in (t.grp), else the master, as before.
     t.grp stays the arrangement's folder: choosing an output does not regroup anything.
   One loop check for every link (abxReach, used by outputs, sends and Ducker triggers). Hooks for other lanes in window.MX_HOOKS. */
window.MX_HOOKS=window.MX_HOOKS||{};
const mxRawOut=x=>x&&x.out&&x.out!=='master'?trkById(x.out)||null:null;
/* where x's sound goes, as stored (used inside the loop check, so it does not check loops itself) */
let MXRV=false;/* true while checking a send: outputs that are refused themselves do not count, so in a loop the output gives way and the send stays */
function mxRawDest(x){if(!x)return null;if(MXRV)return mxDestT(x);if(x.out){if(x.out==='master')return null;const o=trkById(x.out);if(o)return o}return grpOf(x)}
/* the chosen output when it exists and makes no loop, else null */
function mxOutT(t){const o=mxRawOut(t);if(!o||o===t)return null;const k=MXRV;MXRV=false;try{return abxReach(o,t)?null:o}finally{MXRV=k}}
/* where t's sound really goes: its output, its group, or null for the master */
function mxDestT(t){const o=mxOutT(t);if(o)return o;return t&&t.out==='master'?null:grpOf(t)}
function mxSendOk(t,rid){const r=trkById(rid);if(!r||r===t)return false;const k=MXRV;MXRV=true;try{return!abxReach(r,t)}finally{MXRV=k}}
/* can a play into b? k: 'out' (output), 'send', 'sc' (a trigger). {ok, why} in plain words */
function mxCan(a,b,k){if(!a||!b)return{ok:false,why:'There is nothing to connect.'};if(b==='master')return{ok:true,why:''};if(a===b)return{ok:false,why:'A track cannot play into itself.'};
  if(k==='send'&&b.kind!=='return')return{ok:false,why:'Sends go to return tracks only.'};if(k==='send'&&a.kind==='return')return{ok:false,why:'Return tracks have no sends. Choose their output instead.'};
  if(abxReach(b,a))return{ok:false,why:b.name+' already plays into '+a.name+', so this would make a loop.'};return{ok:true,why:''}}
const mxOutName=t=>{const d=mxDestT(t);return d?d.name:'Master'};
function mxSetOut(t,id){if(!t)return false;const g=grpOf(t),v=id==='master'||id==null?(g?'master':null):(g&&id===g.id?null:id);
  if(v&&v!=='master'){const b=trkById(v),c=mxCan(t,b,'out');if(!c.ok){toast(c.why);return false}}
  if((t.out||null)===v)return true;pushUndo();if(v)t.out=v;else delete t.out;changed(true);try{cabSoon()}catch(e){}try{mxSends()}catch(e){}
  toast(t.name+' now plays into '+mxOutName(t)+'.');return true}
function mxOutMenu(t,x,y){if(!t)return;const cur=mxDestT(t),g=grpOf(t),it=[{head:'Output of '+t.name}];
  it.push({label:'Master',sub:'plays straight into the master',check:!cur,dot:'#cfd3db',act:()=>mxSetOut(t,'master')});
  const add=(b,sub)=>{const c=mxCan(t,b,'out');it.push({label:b.name,sub:c.ok?sub:c.why,check:cur===b,dot:b.color||'#cfd3db',dis:!c.ok,act:()=>mxSetOut(t,b.id)})};
  const gs=S.tracks.filter(x=>x.kind==='group'&&x!==t),rs=S.tracks.filter(x=>x.kind==='return'&&x!==t),ts=S.tracks.filter(x=>x.kind!=='group'&&x.kind!=='return'&&x!==t);
  if(gs.length){it.push({head:'Groups'});for(const b of gs)add(b,b===g?'its group in the arrangement':'group: its effects and fader')}
  if(rs.length){it.push({head:'Returns'});for(const b of rs)add(b,'return: its effects and fader')}
  if(ts.length){it.push({head:'Tracks'});for(const b of ts)add(b,'plays through its devices, to resample')}
  openMenu(x,y,it)}
/* the output button under a strip's inserts (one per strip, not on the master) */
function mxOutBtn(mx,t){if(!mx||!t)return;mx.querySelector('.mxout')?.remove();const d=mxDestT(t),bad=!!(t.out&&t.out!=='master'&&!mxOutT(t)),b=document.createElement('button');
  b.type='button';b.className='mxout'+(t.out?' set':'')+(bad?' bad':'');b.dataset.mxout=t.id;b.style.setProperty('--oc',d?d.color||'#cfd3db':'#cfd3db');
  b.innerHTML='<i></i><span>'+esc(d?d.name:'Master')+'</span><b aria-hidden="true">▾</b>';
  b.title='Output: where '+t.name+' plays into. Now: '+(d?d.name:'the Master')+'.'+(bad?' The chosen output would make a loop, so it plays here for now.':'')+' Click to choose the Master, a group, a return or another track.';
  b.setAttribute('aria-label','Output of '+t.name+': '+(d?d.name:'Master'));b.setAttribute('aria-haspopup','menu');
  (mx.querySelector('.mxi')||mx.querySelector('.mxn')).after(b)}
/* the ring on each send: blue before the fader, yellow after it */
function mxRings(box,t){if(!box||!t)return;for(const el of box.querySelectorAll('.hb[data-c]')){const m=/^mx:[^:]+:s:(.+)$/.exec(el.dataset.c||'');if(!m||el.parentNode.classList.contains('mxsr'))continue;const rid=m[1],r=trkById(rid);if(!r)continue;
  const pre=!!(t.sendPre&&t.sendPre[rid]),w=document.createElement('div'),b=document.createElement('button');w.className='mxsr';el.before(w);
  b.type='button';b.className='mxpp'+(pre?' pre':'');b.dataset.mxpp=rid;b.dataset.tid=t.id;b.setAttribute('aria-pressed',pre?'true':'false');b.setAttribute('aria-label','Send to '+r.name+': '+(pre?'before':'after')+' the fader');
  b.title=(pre?'Before the fader (blue)':'After the fader (yellow)')+'. Blue: taken before the fader, so fading the track keeps its send. Yellow: after the fader. Click to switch.';w.append(b,el);
  if((t.sends||{})[rid]>0&&!mxSendOk(t,rid)){el.classList.add('mxlp');el.title=r.name+' already plays into '+t.name+', so this send would make a loop. It stays silent.'}}}
function mxTogPre(t,rid){if(!t||!trkById(rid))return;pushUndo();t.sendPre=t.sendPre||{};if(t.sendPre[rid])delete t.sendPre[rid];else t.sendPre[rid]=true;if(!Object.keys(t.sendPre).length)delete t.sendPre;
  sgSoon();changed(false);try{mxSends()}catch(e){}toast('The send from '+t.name+' to '+trkById(rid).name+' is now taken '+(t.sendPre&&t.sendPre[rid]?'before':'after')+' the fader.')}
document.addEventListener('click',e=>{const o=e.target.closest&&e.target.closest('.mxout[data-mxout]');if(o){e.stopPropagation();e.preventDefault();const t=trkById(o.dataset.mxout),r=o.getBoundingClientRect();if(t)mxOutMenu(t,r.left,r.bottom+2);return}
  const p=e.target.closest&&e.target.closest('.mxpp[data-mxpp]');if(p){e.stopPropagation();e.preventDefault();mxTogPre(trkById(p.dataset.tid),p.dataset.mxpp)}},true);
/* the cable menu: a cable to a return or a track can be an output */
function mxOptsOut(a,b,it){if(!a||!b||b==='master'||a===b||b.kind==='group')return;const c=mxCan(a,b,'out'),cur=mxOutT(a)===b;
  if(cur){it.push({ic:'grp',col:b.color,t:'Already plays into '+b.name,d:'Its sound goes through the effects and fader of '+b.name+'.',dis:true});return}
  it.push({ic:'grp',col:b.color,main:b.kind!=='return'&&a.kind==='return',t:'Play into '+b.name,d:b.kind==='return'?'The whole sound of '+a.name+' goes into the return '+b.name+' instead of the '+(grpOf(a)?'group '+grpOf(a).name:'Master')+'.':'The sound of '+a.name+' goes into '+b.name+' and plays through its devices and fader, together with its own clips. Good for resampling.',dis:!c.ok,why:c.ok?'':c.why,act:()=>mxSetOut(a,b.id)})}
/* offline: the track's width, phase and trim, only when they are not neutral (so older projects render exactly as before) */
function mxUtilOff(oc,t,prev){const w=(t.width??100)/100,ph=t.phase?-1:1,tr=Math.pow(10,(t.trim||0)/20);if(w===1&&ph===1&&tr===1)return prev;
  const i=oc.createGain(),sp=oc.createChannelSplitter(2),m=oc.createChannelMerger(2),o=oc.createGain(),a=(.5+.5*w)*ph,b=(.5-.5*w)*ph,G=v=>{const g=oc.createGain();g.gain.value=v;return g},LL=G(a),RR=G(a),LR=G(b),RL=G(b);
  i.channelCountMode='explicit';i.channelCount=2;i.connect(sp);sp.connect(LL,0);sp.connect(RL,0);sp.connect(LR,1);sp.connect(RR,1);LL.connect(m,0,0);LR.connect(m,0,0);RL.connect(m,0,1);RR.connect(m,0,1);m.connect(o);o.gain.value=tr;prev.connect(i);return o}
/* Solo: a soloed track keeps the bus it plays into audible (as a soloed member keeps its group) */
let MXTAD=0;
{const _ta=trkAudible;trkAudible=function(t,solo){const r=_ta.call(this,t,solo);if(r||!solo||!t||MXTAD>24||!S.tracks.some(x=>x.out))return r;if(t.mute||grpAnc(t).some(g=>g.mute))return r;
  MXTAD++;try{return S.tracks.some(x=>x!==t&&mxDestT(x)===t&&trkAudible(x,solo))}finally{MXTAD--}}}
/* sleeping tracks (lane J): a track, group or return that an awake track plays into stays awake; pre sends sleep with their track */
const MXWK=new Set();
function mxWake(){if(!ctx)return;const any=S.tracks.some(t=>t.out&&t.out!=='master'),now=new Set();
  if(any){const wake=x=>{if(!x)return false;const O=NODES.get(x.id);if(!O||!O.slp)return false;try{O.ut.out.connect(O.vol)}catch(e){}O.slp=false;try{slzSinks(O,true)}catch(e){}
      if(!MXWK.has(x.id))for(const f of O.fxm.values()){try{if(f.resync)f.resync();else if(f.sync)f.sync(play.on?play.t0-play.b0*60/S.bpm:ctx.currentTime)}catch(e){}}return true};
    let ch=true,k=0;while(ch&&k++<16){ch=false;for(const t of S.tracks){const o=mxOutT(t),N=NODES.get(t.id);if(!o||!N||N.slp)continue;now.add(o.id);if(wake(o))ch=true;
      for(const g of grpAnc(o)){now.add(g.id);if(wake(g))ch=true}if(o.kind!=='return')for(const rid in o.sends||{})if(o.sends[rid]>0){now.add(rid);if(wake(trkById(rid)))ch=true}}}}
  MXWK.clear();for(const id of now)MXWK.add(id);
  for(const[,N] of NODES)if(N.mxPre){const on=!N.slp;if(!!N.mxPreC!==on){try{on?N.ut.out.connect(N.mxPre):N.ut.out.disconnect(N.mxPre)}catch(e){}N.mxPreC=on}}}
{const _sl=slpTick;slpTick=function(){const r=_sl.apply(this,arguments);try{mxWake()}catch(e){}return r}}
/* mixer cables: a channel whose output goes elsewhere no longer draws its group cable */
{const _cl=cabList;cabList=function(){const L=_cl.apply(this,arguments);try{if(!S.tracks.some(t=>t.out))return L;return L.filter(c=>!(c.k==='out'&&c.a&&c.a.out&&mxDestT(c.a)!==c.b))}catch(e){return L}}}
Object.assign(MX_HOOKS,{
  /* every link of the project: {k:'out'|'send'|'sc', a, b ('master' for the master), pre, lv, tap, lat (MX-2)} */
  links(){const L=[];for(const t of S.tracks){L.push({k:'out',a:t,b:mxDestT(t)||'master',pre:false,tap:null,lat:null});
      if(t.kind!=='return')for(const rid in t.sends||{}){const r=trkById(rid);if(r&&t.sends[rid]>0&&mxSendOk(t,rid))L.push({k:'send',a:t,b:r,lv:t.sends[rid],pre:!!(t.sendPre&&t.sendPre[rid]),tap:null,lat:null})}
      for(const f of t.fx||[])if(f&&f.type==='duck'&&f.p&&typeof f.p.src==='string'){const s=trkById(f.p.src);if(s&&s!==t)L.push({k:'sc',a:s,b:t,fx:f,pre:true,tap:'fx',lat:null})}}return L},
  canLink:(a,b,k)=>mxCan(a,b,k||'out'),
  outOf:t=>mxDestT(t)||'master',
  setOut:(t,id)=>mxSetOut(t,id),
  outMenu:(t,x,y)=>mxOutMenu(t,x,y),
  isPre:(t,rid)=>!!(t&&t.sendPre&&t.sendPre[rid]),
  setPre(t,rid,on){if(!t||!!(t.sendPre&&t.sendPre[rid])===!!on)return;mxTogPre(t,rid)},
  /* the live node at a tap point: 'in' (before effects), 'fx' (after effects), 'fader' (after fader and pan), 'group' (after the bus it plays into) */
  tap(t,pt){if(!ctx||!t)return null;const N=NODES.get(t.id);if(!N)return null;if(pt==='in')return N.in;if(pt==='fx')return N.ut.out;if(pt==='fader')return N.pan;
    if(pt==='group'){const d=mxDestT(t),D=d&&NODES.get(d.id);return D?D.pan:master}return null}});
