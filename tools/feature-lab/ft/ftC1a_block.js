/* v0.233 (task FT-C1a): the controller layer. One MIDI service for every controller: Web MIDI with SysEx (without it when the browser refuses),
   devices found at the start and followed when they are plugged in or out, each device's messages handed to its profile (a profile can take
   a whole device, as Push 1 will in FT-C2; every other device is "generic" and behaves as before: notes play the armed or selected track,
   controller moves go to the mappings and the recorded controller lanes). Mappings: {id, dev, type cc/note/pb, ch, num, target, min, max,
   take pickup/scale/jump, enc abs/rel2c/relsb/rel64, fb, scope}; for every project in UI.ctl, for one project in S.ctl (only written when used).
   The old UI.midiMap is read once into UI.ctl and left in place, so an older build still finds its links. Event driven: nothing runs while no
   MIDI arrives; feedback to a controller is sent only when a mapped control changes, at most 30 times a second. */
const FT_HOOKS=window.FT_HOOKS||(window.FT_HOOKS={});
const CTL={acc:null,sysex:false,started:false,devs:new Map(),profs:[],last:null,rt:new WeakMap(),idx:null,idxK:null,fbq:new Set(),fbT:0,sent:new Map(),fbn:0,n:{in:0,out:0,fb:0,learn:0}};
window.CTL=CTL;
/* ---- storage ---- */
function ctlG(){if(!UI.ctl||!Array.isArray(UI.ctl.maps))UI.ctl={v:1,maps:[]};
  if(!UI.ctl.mig){UI.ctl.mig=1;const M=UI.midiMap||{};for(const k in M){const[ch,cc]=k.split(':').map(Number),t=M[k];if(!t||!(cc>=0)||UI.ctl.maps.some(m=>m.type==='cc'&&m.ch===ch&&m.num===cc&&m.dev==='*'))continue;
    UI.ctl.maps.push({id:'m'+rid(),dev:'*',type:'cc',ch:ch|0,num:cc,target:t,min:0,max:1,take:'jump',enc:'abs',fb:true,scope:'global'})}if(UI.ctl.maps.length)saveUI()}
  return UI.ctl}
const ctlP=mk=>{if(S.ctl&&Array.isArray(S.ctl.maps))return S.ctl;if(!mk)return null;S.ctl={v:1,maps:[]};return S.ctl};
function ctlAll(){const g=ctlG(),p=ctlP(false);return(p?p.maps.map(m=>(m.scope='project',m)):[]).concat(g.maps.map(m=>(m.scope='global',m)))}
/* a pinned device window shows the same control as the panel under "pn:<track>/<device>:" + its id; a mapping always names the panel's id */
const ctlBid=id=>{id=String(id||'');if(id.startsWith('pn:')){const i=id.indexOf(':fx:');if(i>0)return id.slice(i+1)}return id};
const ctlKey=(type,ch,num)=>type+':'+ch+':'+num;
function ctlIndex(){const p=ctlP(false),k=[S,p,p&&p.maps.length,UI.ctl&&UI.ctl.maps.length];
  if(CTL.idx&&CTL.idxK&&k.every((x,i)=>x===CTL.idxK[i]))return CTL.idx;
  const byM=new Map(),byT=new Map();for(const m of ctlAll()){const a=ctlKey(m.type,m.ch,m.num);if(!byM.has(a))byM.set(a,[]);byM.get(a).push(m);if(!byT.has(m.target))byT.set(m.target,[]);byT.get(m.target).push(m)}
  CTL.idx={byM,byT};CTL.idxK=k;ctlFbCount();return CTL.idx}
const ctlDirty=()=>{CTL.idx=null;CTL.idxK=null;ctlIndex()};
/* ---- devices ---- */
const ctlBase=n=>String(n||'').replace(/^MIDI(?:IN|OUT)\d*\s*\((.*)\)$/i,'$1').replace(/\s+(?:in|out|input|output)(?:\s*\d+)?$/i,'').trim();
function ctlProf(p){CTL.profs=CTL.profs.filter(x=>x.id!==p.id);CTL.profs.unshift(p);for(const d of CTL.devs.values())ctlAttach(d,true);return p}
const ctlOff=d=>!!(UI.ctlOff&&UI.ctlOff[d.name]);
function ctlAttach(d,re){const p=CTL.profs.find(x=>x.match(d))||CTL.profs[CTL.profs.length-1];if(d.prof===p&&re)return;if(d.prof&&d.prof.detach)try{d.prof.detach(d)}catch(e){console.error('AudioLab controller',e)}d.prof=p;if(p.attach&&!ctlOff(d))try{p.attach(d)}catch(e){console.error('AudioLab controller',e)}ctlFbDev(d)}
function ctlScan(first){const A=CTL.acc;if(!A)return;const seen=new Set(),outs=[...A.outputs.values()].filter(o=>o.state!=='disconnected');
  for(const i of A.inputs.values()){if(i.state==='disconnected')continue;seen.add(i.id);let d=CTL.devs.get(i.id);
    if(!d){d={id:i.id,name:i.name||'MIDI device',man:i.manufacturer||'',inp:i,out:null,prof:null,base:ctlBase(i.name)};CTL.devs.set(i.id,d);
      i.onmidimessage=ev=>ctlMsg(d,ev.data);d.out=outs.find(o=>ctlBase(o.name)===d.base&&(o.manufacturer||'')===d.man)||outs.find(o=>ctlBase(o.name)===d.base)||null;ctlAttach(d);if(!first)toast('Controller connected: '+d.name+(d.prof&&d.prof.id!=='generic'?' ('+d.prof.name+')':'')+'.')}
    else if(!d.out||d.out.state==='disconnected'){d.out=outs.find(o=>ctlBase(o.name)===d.base)||null;if(d.out)ctlAttach(d)}}
  for(const[id,d] of[...CTL.devs]){if(seen.has(id))continue;CTL.devs.delete(id);if(d.prof&&d.prof.detach)try{d.prof.detach(d,true)}catch(e){}try{d.inp.onmidimessage=null}catch(e){}toast('Controller unplugged: '+d.name+'.')}
  ctlFbCount();if(FT_HOOKS.controllersChanged)try{FT_HOOKS.controllersChanged()}catch(e){}ctlPagePaint()}
function ctlStart(){if(CTL.started||!navigator.requestMIDIAccess)return;CTL.started=true;
  const go=(A,sx)=>{CTL.acc=A;CTL.sysex=sx;if(!UI.ctlSeen){UI.ctlSeen=1;saveUI()}ctlG();ctlScan(true);A.onstatechange=()=>ctlScan(false)};
  navigator.requestMIDIAccess({sysex:true}).then(A=>go(A,true),()=>navigator.requestMIDIAccess().then(A=>go(A,false))).catch(()=>{CTL.started=false})}
function ctlSend(d,bytes){if(!d||!d.out||ctlOff(d))return false;if(bytes[0]===0xF0&&!CTL.sysex)return false;try{d.out.send(bytes);CTL.n.out++;return true}catch(e){return false}}
/* the generic profile: what every controller did before, plus mappings for notes and pitch bend */
ctlProf({id:'generic',name:'Generic MIDI',match:()=>true,msg(d,a){const s=a[0],c=s&0xf0,ch=s&15;if(s>=0xF0)return;
  if(c===0xB0){ccLive(a[1],a[2]/127);midiCC(ch,a[1],a[2],d);return}
  if(c===0xE0){const v=(a[2]<<7)|a[1];if(ctlIn(d,'pb',ch,0,v))return;ccLive('pb',v/16383);return}
  if(c===0x90&&a[2]>0){if(ctlIn(d,'note',ch,a[1],a[2]))return;noteOn(a[1]-24,a[2]/127,'m'+a[1]);return}
  if(c===0x80||c===0x90){const ms=ctlIndex().byM.get(ctlKey('note',ch,a[1]));if(ms&&ms.some(m=>m.dev==='*'||m.dev===d.name))return;noteOff('m'+a[1])}}});
function ctlMsg(d,data){CTL.n.in++;if(ctlOff(d))return;const a=data;if(a[0]<0xF0){const c=a[0]&0xf0;CTL.last={dev:d.name,ch:a[0]&15,type:c===0xB0?'cc':c===0xE0?'pb':c===0x90||c===0x80?'note':c===0xD0||c===0xA0?'at':'other',num:c===0xE0?0:a[1],val:c===0xE0?((a[2]<<7)|a[1]):a[2],t:Date.now()};if(FT_HOOKS.controllerMessage)try{FT_HOOKS.controllerMessage(CTL.last)}catch(e){}}
  try{d.prof.msg(d,a)}catch(e){console.error('AudioLab controller '+d.name,e)}}
/* ---- learn and apply ---- */
const ctlLabel=id=>{const C=CT.get(id),l=(C&&C.label)||String(id).replace(/^[a-z0-9]+:/i,'');let dn='';try{const el=document.querySelector(`[data-c="${CSS.escape(id)}"]`)||document.querySelector(`[data-c^="pn:"][data-c$=":${CSS.escape(id)}"]`),D=el&&el.closest('.dev'),h=D&&D.querySelector(':scope>.devh>span');dn=h?h.textContent.trim():''}catch(e){}return dn&&dn!==l?dn+': '+l:l};
const ctlMsgName=m=>(m.type==='cc'?'CC '+m.num:m.type==='pb'?'Pitch bend':'Note '+m.num)+' (channel '+(m.ch+1)+')';
/* returns true when the message was used (learned or moved a mapped control) */
function ctlIn(d,type,ch,num,raw){const dn=d?d.name:'*';
  if(ML.on){if(type!=='cc'&&!ML.sel)return false;const id=ML.sel||ML.last;if(id)ctlLearn(dn,type,ch,num,raw,id);return true}
  const ms=ctlIndex().byM.get(ctlKey(type,ch,num));if(!ms)return false;let pm=ms.filter(m=>m.dev==='*'||m.dev===dn);if(!pm.length)return false;
  if(pm.some(m=>m.scope==='project'))pm=pm.filter(m=>m.scope==='project');for(const m of pm)ctlMove(m,raw);return true}
function ctlLearn(dn,type,ch,num,raw,id){id=ctlBid(id);const proj=ML.scope==='project'||(!ML.scope&&UI.ctlScope==='project');const store=proj?ctlP(true):ctlG();if(proj)pushUndo();
  for(const st of[ctlG(),ctlP(false)]){if(!st)continue;st.maps=st.maps.filter(m=>!(m.target===id&&(st===store))&&!(st===store&&m.type===type&&m.ch===ch&&m.num===num&&(m.dev===dn||m.dev==='*')))}
  const m={id:'m'+rid(),dev:dn,type,ch,num,target:id,min:0,max:1,take:type==='note'?'jump':(UI.ctlTake||'pickup'),enc:'abs',fb:true};if(type==='cc')m.auto=1;store.maps.push(m);ctlDirty();CTL.n.learn++;
  if(proj)changed(false);else saveUI();ML.sel=null;ML.scope=null;mlMark();ctlFbQ(m);ctlPagePaint();
  toast('Linked '+ctlMsgName(m)+(dn!=='*'?' on '+dn:'')+' to '+ctlLabel(id)+(proj?', in this project only.':'.'))}
/* a relative encoder sends small steps (1, 2, 3 up, 127, 126 down, or 65, 66 down): the first moves after learning tell which kind it is */
function ctlAuto(m,raw,r){(r.h=r.h||[]).push(raw);const h=r.h,lo=h.some(v=>v>=1&&v<=6),c2=h.every(v=>(v>=1&&v<=6)||v>=122),sb=h.every(v=>(v>=1&&v<=6)||(v>=65&&v<=70));
  if(lo&&c2&&h.some(v=>v>=122)){m.enc='rel2c';delete m.auto;saveSoon(m);return 'rel'}if(lo&&sb&&h.some(v=>v>=65&&v<=70)){m.enc='relsb';delete m.auto;saveSoon(m);return 'rel'}
  if(!(c2||sb)||h.length>=16){delete m.auto;saveSoon(m);return 'abs'}return 'wait'}
const saveSoon=m=>{if(m.scope==='project')changed(false);else saveUI()};
function ctlMove(m,raw){const C=CT.get(m.target);if(!C)return;let r=CTL.rt.get(m);if(!r){r={};CTL.rt.set(m,r)}
  if(m.auto){const k=ctlAuto(m,raw,r);if(k==='wait')return}
  const lo=+(m.min??0),hi=+(m.max??1),L=Math.min(lo,hi),H=Math.max(lo,hi),cur=C.spec.n(C.get());let n;
  if(r.set!=null&&Math.abs(cur-r.set)>.004)r.ok=false;/* moved by the mouse, automation or another mapping since: catch it again */
  if(m.type==='note')n=Math.abs(cur-hi)<.004?lo:hi;
  else if(m.enc&&m.enc!=='abs'){const dl=m.enc==='rel2c'?(raw<64?raw:raw-128):m.enc==='relsb'?(raw<64?raw:-(raw-64)):raw-64;n=clamp(cur+dl/127*(m.sens||1)*(H-L||1)*(hi<lo?-1:1),L,H)}
  else{const v=m.type==='pb'?raw/16383:raw/127,c=lo+v*(hi-lo),tk=m.take||'pickup',tol=Math.max(.004,(H-L)/127*1.01);
    if(tk==='jump'||r.ok)n=c;
    else if(tk==='pickup'){if(Math.abs(c-cur)<=tol||(r.lc!=null&&(r.lc-cur)*(c-cur)<=0)){r.ok=true;n=c}else{r.lc=c;r.wait=1;return}}
    else{/* scale: the control moves toward the knob's end as the knob does, until they meet */
      if(r.lc==null){r.lc=c;if(Math.abs(c-cur)<=tol){r.ok=true;n=c}else return}else{const dl=c-r.lc;n=cur;if(dl>0)n=H-r.lc>1e-6?cur+dl*(H-cur)/(H-r.lc):c;else if(dl<0)n=r.lc-L>1e-6?cur+dl*(cur-L)/(r.lc-L):c;if(Math.abs(n-c)<=tol){r.ok=true;n=c}}}
    r.lc=c}
  r.wait=0;C.set(C.spec.v(clamp(n,0,1)));r.set=C.spec.n(C.get());ctlPaintId(m.target,m)}
function ctlPaintId(id,from){CTL.mv=from||null;try{for(const el of document.querySelectorAll(`[data-c="${CSS.escape(id)}"],[data-c^="pn:"][data-c$=":${CSS.escape(id)}"]`))paintCtl(el)}finally{CTL.mv=null}
  if(from){const ms=ctlIndex().byT.get(id);if(ms)for(const m of ms)if(m!==from)ctlFbQ(m);const r=CTL.rt.get(from);if(r&&from.fb!==false)CTL.sent.set(from.id,ctlOutVal(from))}}
/* ---- feedback: a mapped control's value goes back to the controller (motor faders, LED rings, lit buttons) ---- */
function ctlDevOf(m){if(m.dev==='*'){for(const d of CTL.devs.values())if(d.out&&d.prof&&d.prof.id==='generic')return d;return null}for(const d of CTL.devs.values())if(d.name===m.dev)return d;return null}
function ctlFbCount(){let n=0;if(CTL.devs.size){const I=CTL.idx||ctlIndex();if(I)for(const ms of I.byT.values())for(const m of ms)if(m.fb!==false&&(!m.enc||m.enc==='abs')){const d=ctlDevOf(m);if(d&&d.out)n++}}CTL.fbn=n}
function ctlOutVal(m){const C=CT.get(m.target);if(!C)return null;const lo=+(m.min??0),hi=+(m.max??1),n=C.spec.n(C.get()),v=hi===lo?0:clamp((n-lo)/(hi-lo),0,1);return m.type==='pb'?Math.round(v*16383):m.type==='note'?(Math.abs(n-hi)<.004?127:0):Math.round(v*127)}
function ctlFbQ(m){if(m.fb===false||(m.enc&&m.enc!=='abs'))return;const d=ctlDevOf(m);if(!d||!d.out)return;CTL.fbq.add(m);if(!CTL.fbT)CTL.fbT=setTimeout(ctlFbFlush,33)}
function ctlFbFlush(){CTL.fbT=0;const q=[...CTL.fbq];CTL.fbq.clear();for(const m of q){const v=ctlOutVal(m);if(v==null||CTL.sent.get(m.id)===v)continue;const d=ctlDevOf(m);if(!d)continue;
  const ok=ctlSend(d,m.type==='cc'?[0xB0|m.ch,m.num,v]:m.type==='pb'?[0xE0|m.ch,v&127,v>>7]:[0x90|m.ch,m.num,v]);if(ok){CTL.sent.set(m.id,v);CTL.n.fb++}}}
function ctlFbDev(d){if(!d||!d.out)return;const I=ctlIndex();for(const ms of I.byT.values())for(const m of ms)if(m.dev===d.name||m.dev==='*'){CTL.sent.delete(m.id);ctlFbQ(m)}}
{const _p=paintCtl;paintCtl=function(el){const r=_p.apply(this,arguments);if(CTL.fbn&&el&&el.dataset)try{const ms=ctlIndex().byT.get(ctlBid(el.dataset.c));if(ms)for(const m of ms)if(m!==CTL.mv)ctlFbQ(m)}catch(e){}return r}}
/* ---- the small Controllers window (FT-C1b grows it into the full mappings page; lane B's Settings can show the same with FT_HOOKS.controllersPage) ---- */
const CTLCSS=`#ctlWin .fwb{overflow:auto;padding:10px 12px;font-size:var(--fs1);display:flex;flex-direction:column;gap:10px}#ctlWin h4{margin:0;font:var(--fw6) var(--fs1) var(--ffu);text-transform:uppercase;letter-spacing:.06em;opacity:.6}
#ctlWin .crow{display:grid;grid-template-columns:minmax(80px,1fr) minmax(120px,1.1fr) minmax(110px,1.4fr) 96px 112px 24px;gap:6px;align-items:center;padding:3px 4px;border-radius:6px}#ctlWin .crow:hover{background:rgba(255,255,255,.05)}
#ctlWin .crow.h{opacity:.55;font-weight:600}#ctlWin .crow span{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}#ctlWin select{font-size:var(--fs1);min-height:22px}#ctlWin .cdel{width:22px;min-height:22px;padding:0}
#ctlWin .cdev{display:flex;align-items:center;gap:8px;padding:3px 4px}#ctlWin .cdev b{flex:1;font-weight:500}#ctlWin .cdev em{font-style:normal;opacity:.6}#ctlWin .cnone{opacity:.6;padding:2px 4px}#ctlWin .cbar{display:flex;gap:6px;flex-wrap:wrap}`;
function ctlPage(host){ctlStart();let b=host;if(!b){if(!document.getElementById('ctlCss')){const st=document.createElement('style');st.id='ctlCss';st.textContent=CTLCSS;document.head.appendChild(st)}
  const w=fwin('ctlWin','Controllers',{x:Math.max(20,innerWidth/(ZOOM||1)/2-340),y:110,w:680,h:420});b=w.querySelector('.fwb')}
  CTL.host=b;ctlPagePaint();return b}
function ctlPagePaint(){const b=CTL.host;if(!b||!b.isConnected||(b.closest('[hidden]')))return;const all=ctlAll(),devs=[...CTL.devs.values()];
  const tk=m=>m.type==='note'?'<span title="A note or button switches the control between its two ends">Switch</span>':m.enc&&m.enc!=='abs'?'<span title="An endless knob: each step moves the control from where it is">Endless knob</span>':`<select data-ck="take" data-m="${m.id}" title="What happens when the knob and the control on screen are at different places. Pick up: nothing moves until the knob passes the control. Scale: the control moves more slowly until they meet. Jump: the control jumps to the knob."><option value="pickup"${m.take==='pickup'?' selected':''}>Pick up</option><option value="scale"${m.take==='scale'?' selected':''}>Scale</option><option value="jump"${m.take==='jump'?' selected':''}>Jump</option></select>`;
  b.innerHTML=`<div class="cbar"><button data-ck="learn" title="Turn MIDI learn on: click a control, then move a knob, fader or button on your controller (Mod+L)">${ML.on?'Stop learning':'MIDI learn'}</button>${CTL.acc?'':`<button data-ck="start" title="Ask the browser for your MIDI devices">Find MIDI devices</button>`}</div>
  <h4>Devices</h4>${devs.length?devs.map(d=>`<label class="cdev" title="${esc(d.name)}${d.out?'':' (no way back to it: no feedback)'}"><input type="checkbox" data-ck="dev" data-d="${esc(d.name)}"${ctlOff(d)?'':' checked'} title="Use this device in AudioLab"><b>${esc(d.name)}</b><em>${esc(d.prof?d.prof.name:'')}</em></label>`).join(''):`<div class="cnone">${CTL.acc?'No MIDI device is connected.':'MIDI is not on yet.'}</div>`}
  <h4>Mappings</h4>${all.length?`<div class="crow h"><span>Device</span><span>Message</span><span>Moves</span><span>Takeover</span><span>Where</span><span></span></div>`+all.map(m=>`<div class="crow"><span title="${esc(m.dev==='*'?'Any device':m.dev)}">${esc(m.dev==='*'?'Any device':m.dev)}</span><span title="${esc(ctlMsgName(m))}">${esc(ctlMsgName(m))}</span><span title="${esc(ctlLabel(m.target))}">${esc(ctlLabel(m.target))}</span>${tk(m)}<select data-ck="scope" data-m="${m.id}" title="This project only, or every project"><option value="global"${m.scope==='global'?' selected':''}>Everywhere</option><option value="project"${m.scope==='project'?' selected':''}>This project</option></select><button class="cdel" data-ck="del" data-m="${m.id}" title="Delete this mapping" aria-label="Delete this mapping">✕</button></div>`).join(''):`<div class="cnone">No mappings yet. Press MIDI learn, click a control, then move a knob on your controller.</div>`}`;
  if(!b._ck){b._ck=1;b.addEventListener('click',e=>{const x=e.target.closest('[data-ck]');if(!x)return;const k=x.dataset.ck;if(k==='learn')midiLearn();else if(k==='start')ctlStart();else if(k==='del')ctlEdit(x.dataset.m,null);ctlPagePaint()});
    b.addEventListener('change',e=>{const x=e.target.closest('[data-ck]');if(!x)return;const k=x.dataset.ck;if(k==='dev'){UI.ctlOff=UI.ctlOff||{};if(x.checked)delete UI.ctlOff[x.dataset.d];else UI.ctlOff[x.dataset.d]=1;saveUI();for(const d of CTL.devs.values())if(d.name===x.dataset.d){if(x.checked)ctlAttach(d);else if(d.prof&&d.prof.detach)try{d.prof.detach(d)}catch(er){}}}
      else ctlEdit(x.dataset.m,{[k]:x.value});ctlPagePaint()})}}
/* change or delete one mapping (null deletes); moving it between project and global keeps the rest */
function ctlEdit(mid,ch){const g=ctlG(),p=ctlP(false),inP=p&&p.maps.find(m=>m.id===mid),m=inP||g.maps.find(m=>m.id===mid);if(!m)return false;if(inP||(ch&&ch.scope==='project'))pushUndo();
  const from=inP?p:g;if(!ch){from.maps=from.maps.filter(x=>x!==m)}else{const to=ch.scope?(ch.scope==='project'?ctlP(true):g):from;for(const k in ch)if(k!=='scope')m[k]=ch[k];if(to!==from){from.maps=from.maps.filter(x=>x!==m);to.maps.push(m)}CTL.rt.delete(m)}
  ctlDirty();saveUI();if(inP||(ch&&ch.scope==='project'))changed(false);mlMark();return true}
FT_HOOKS.controllersPage=host=>ctlPage(host);FT_HOOKS.controllersPaint=()=>ctlPagePaint();
/* in the desktop app MIDI is always allowed: start it right away; in a browser only once it was allowed before */
setTimeout(()=>{if(!navigator.requestMIDIAccess)return;if(window.audiolabDesktop){ctlStart();return}if(!UI.ctlSeen)return;try{navigator.permissions.query({name:'midi',sysex:true}).then(s=>{if(s.state==='granted')ctlStart()},()=>{})}catch(e){}},1200);
addEventListener('pagehide',()=>{for(const d of CTL.devs.values())if(d.prof&&d.prof.bye)try{d.prof.bye(d)}catch(e){}});
function ctlUnmap(id){id=ctlBid(id);const g=ctlG(),p=ctlP(false);let n=0;g.maps=g.maps.filter(m=>m.target!==id||(n++,false));if(p){const k=p.maps.length;if(p.maps.some(m=>m.target===id)){pushUndo();p.maps=p.maps.filter(m=>m.target!==id);n+=k-p.maps.length;changed(false)}}ctlDirty();saveUI();mlMark();ctlPagePaint();return n}
{const _m=midiLearn;midiLearn=function(){const r=_m.apply(this,arguments);ctlPagePaint();return r}}
SCM.set('learn',SCM.get('ctl.learn'));
