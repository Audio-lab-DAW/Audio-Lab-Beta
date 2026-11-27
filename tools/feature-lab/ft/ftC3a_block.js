/* v0.246 (task FT-C3a): generic controllers. Templates are mapping sets for keyboards and pad controllers: knobs on the selected device's
   parameters (8 at a time, following the device panel of the selected track), faders on the levels of a bank of 8 tracks, pads on the drum
   kit's 16 pads (when the selected track is a drum kit; otherwise they play notes as before), transport and navigation buttons. Their targets
   start with "@" and are worked out when a message arrives, so the same knob follows the selection. A known controller (Akai MPK mini,
   Arturia MiniLab 3, Novation Launchkey) gets its template the first time it is plugged in, if it has no mappings yet; every other one can
   be set up by moving its knobs in order. A template applied is ordinary mappings (tpl, slot), shown, edited and deleted on the mappings page;
   a device's mappings can be saved as the user's own template (UI.ctlTpl). Transport messages (MMC) from keyboards work too.
   Event driven like the rest of the layer: nothing runs while no MIDI arrives. */
const CTT={dev:{},bk:{},tb:0,guide:null,sel:{},saving:null};window.CTT=CTT;
const CTT_CMD={play:'Play or pause',stop:'Stop',rec:'Record',loop:'Loop on or off',click:'Metronome',undo:'Undo',redo:'Redo',devPrev:'Previous device',devNext:'Next device',bankPrev:'Previous 8 knobs',bankNext:'Next 8 knobs',tbPrev:'Faders: 8 tracks back',tbNext:'Faders: next 8 tracks',trkPrev:'Select the track above',trkNext:'Select the track below'};
function ctlTLabel(t){t=String(t);const k=+t.split(':')[1];if(t.startsWith('@dev:'))return'Selected device, knob '+(k+1);if(t.startsWith('@vol:'))return'Track '+(k+1)+' of the 8, volume';if(t.startsWith('@pan:'))return'Track '+(k+1)+' of the 8, pan';
  if(t==='@ms')return'Master level';if(t.startsWith('@pad:'))return'Drum kit pad '+(k+1);if(t.startsWith('@cmd:'))return CTT_CMD[t.slice(5)]||t.slice(5);return t}
const ctlTB=()=>clamp(CTT.tb|0,0,Math.max(0,Math.floor((S.tracks.length-1)/8)*8));
function ctlTDev(){const devs=p1bDevs();if(!devs.length)return{devs,i:-1,bank:0,nb:0,ids:[]};let i=CTT.dev[selT];if(i==null){i=devs.findIndex(x=>!x.tr);if(i<0)i=0}i=clamp(i,0,devs.length-1);
  const nb=Math.ceil(devs[i].ids.length/8),bank=clamp(CTT.bk[selT+':'+i]|0,0,nb-1);return{devs,i,bank,nb,ids:devs[i].ids.slice(bank*8,bank*8+8)}}
function ctlRes(t){const k=+t.split(':')[1];if(t.startsWith('@dev:'))return ctlTDev().ids[k]||null;
  if(t.startsWith('@vol:')||t.startsWith('@pan:')){const x=S.tracks[ctlTB()+k];return x?(t[1]==='v'?'hd:':'hp:')+x.id:null}if(t==='@ms')return'ms';return null}
function ctlTNav(c){const P=ctlTDev();
  if(c==='devPrev'||c==='devNext'){if(P.i<0){toast('The selected track shows no devices.');return}const i=clamp(P.i+(c==='devNext'?1:-1),0,P.devs.length-1);CTT.dev[selT]=i;const Q=ctlTDev();toast('Knobs: '+Q.devs[i].name+' ('+(i+1)+' of '+Q.devs.length+')'+(Q.nb>1?', knobs '+(Q.bank*8+1)+' to '+(Q.bank*8+Q.ids.length):'')+'.');return}
  if(c==='bankPrev'||c==='bankNext'){if(P.i<0)return;CTT.bk[selT+':'+P.i]=clamp(P.bank+(c==='bankNext'?1:-1),0,P.nb-1);const Q=ctlTDev();toast('Knobs: '+Q.devs[Q.i].name+', knobs '+(Q.bank*8+1)+' to '+(Q.bank*8+Q.ids.length)+'.');return}
  if(c==='tbPrev'||c==='tbNext'){CTT.tb=clamp(ctlTB()+(c==='tbNext'?8:-8),0,Math.max(0,Math.floor((S.tracks.length-1)/8)*8));const a=ctlTB();toast('Faders: tracks '+(a+1)+' to '+Math.min(S.tracks.length,a+8)+'.');return}
  if(c==='trkPrev'||c==='trkNext'){const T=S.tracks,k=T.findIndex(t=>t.id===selT),j=clamp((k<0?0:k)+(c==='trkNext'?1:-1),0,T.length-1);if(T[j])selectTrack(T[j].id);return}
  const a=SCM.get(c);if(a)a.run()}
/* a button: on press only (a CC from 0 to above 0, or a note on) */
function ctlTCmd(m,raw){let r=CTL.rt.get(m);if(!r){r={};CTL.rt.set(m,r)}const on=raw>0;if(m.type==='cc'){if(!on||r.dn){r.dn=on;return}r.dn=true}ctlTNav(m.target.slice(5));CTL.n.cmd=(CTL.n.cmd||0)+1}
{const _mv=ctlMove;ctlMove=function(m,raw){const t=m.target;if(!t||t[0]!=='@')return _mv.apply(this,arguments);if(t.startsWith('@cmd:')){ctlTCmd(m,raw);return}if(t.startsWith('@pad:'))return;
  const id=ctlRes(t);if(!id||!CT.has(id))return;let r=CTL.rt.get(m);if(r&&r.tid!==id){r={h:r.h};CTL.rt.set(m,r)}
  m.target=id;try{_mv.call(this,m,raw)}finally{m.target=t}r=CTL.rt.get(m);if(r)r.tid=id}}
/* pads: the drum kit's pads when a drum kit is selected, else the note plays the track as before */
function ctlPadOn(d,t,ch,num,k,raw){const key='ctp:'+(d?d.name:'*')+':'+ch+':'+num;if(LIVE.has(key))return;const hs=[{t,h:voiceOn(t,36+k,raw/127)}],b=play.on&&!play.counting?curDisp():null;LIVE.set(key,{p:36+k,v:raw/127,hs,b});flashArm()}
{const _i=ctlIn;ctlIn=function(d,type,ch,num,raw){if(CTT.guide&&!ML.on&&!CTL.relearn&&ctlGuideIn(d,type,ch,num,raw))return true;
  if(!ML.on&&!CTL.relearn&&type==='note'){const dn=d?d.name:'*',ms=ctlIndex().byM.get(ctlKey(type,ch,num)),pm=ms&&ms.filter(m=>m.dev==='*'||m.dev===dn);
    if(pm&&pm.length&&pm.every(m=>String(m.target).startsWith('@pad:'))){const t=p1bDT();if(!t)return false;ensurePads(t.inst);const k=+pm[0].target.slice(5);if(!(k<t.inst.pads.length))return false;ctlPadOn(d,t,ch,num,k,raw);return true}}
  return _i.apply(this,arguments)}}
function ctlMmc(d,a){if(a[1]!==0x7F||a[3]!==6)return;const c=a[4],run=id=>{const x=SCM.get(id);if(x)x.run()};CTL.n.mmc=(CTL.n.mmc||0)+1;
  if(c===1)run('stop');else if(c===2||c===3){if(!play.on)run('play')}else if(c===9){if(play.on)run('play')}else if(c===6)run('rec')}
{const G=CTL.profs.find(p=>p.id==='generic'),_g=G.msg;G.msg=function(d,a){const s=a[0],c=s&0xf0;if(s===0xF0){ctlMmc(d,a);return}
  if(c===0x80||(c===0x90&&!a[2])){const k='ctp:'+d.name+':'+(s&15)+':'+a[1];if(LIVE.has(k)){noteOff(k);return}
    const ms=ctlIndex().byM.get(ctlKey('note',s&15,a[1]));if(ms&&ms.some(m=>(m.dev==='*'||m.dev===d.name)&&String(m.target).startsWith('@pad:'))){noteOff('m'+a[1]);return}}
  return _g.apply(this,arguments)}}
/* ---- the templates ---- */
const ctlS=(l,target,type,ch,num)=>({l,target,type:type||'cc',ch:ch||0,num:num==null?null:num});
const CTS={k8:n=>Array.from({length:8},(_,i)=>ctlS('Knob '+(i+1),'@dev:'+i,'cc',0,n?n[i]:null)),f:(c,n)=>Array.from({length:c},(_,i)=>ctlS('Fader '+(i+1),'@vol:'+i,'cc',0,n?n[i]:null)),
  pads:(c,base)=>Array.from({length:c},(_,i)=>ctlS('Pad '+(i+1),'@pad:'+i,'note',9,base==null?null:base+i)),
  tr:()=>[['Play','play'],['Stop','stop'],['Record','rec'],['Loop','loop']].map(([l,c])=>ctlS(l+' button','@cmd:'+c)),
  nav:()=>[['Previous device','devPrev'],['Next device','devNext'],['Faders back 8 tracks','tbPrev'],['Faders on 8 tracks','tbNext']].map(([l,c])=>ctlS(l+' button','@cmd:'+c))};
const CTPL=[
  {id:'mpkmini',name:'Akai MPK mini',re:/mpk\s*mini/i,info:'Factory program: the 8 knobs (CC 70 to 77) move the selected device, the pads (channel 10, banks A and B from note 36) play the drum kit.',slots:[...CTS.k8([70,71,72,73,74,75,76,77]),...CTS.pads(16,36)]},
  {id:'minilab3',name:'Arturia MiniLab 3',re:/minilab\s*3/i,info:'Factory settings: the 8 knobs move the selected device, the 4 faders the levels of 4 tracks, the pads (channel 10 from note 36) play the drum kit.',slots:[...CTS.k8([74,71,76,77,93,18,19,16]),...CTS.f(4,[82,83,85,17]),...CTS.pads(8,36)]},
  {id:'launchkey',name:'Novation Launchkey',re:/launchkey/i,no:/daw|incontrol/i,info:'MIDI port, factory settings: the 8 knobs (CC 21 to 28) move the selected device, the pads in drum mode (channel 10 from note 36) play the drum kit. Faders and buttons: set up by moving.',slots:[...CTS.k8([21,22,23,24,25,26,27,28]),...CTS.pads(16,36),...CTS.f(8),ctlS('Master fader','@ms'),...CTS.tr(),...CTS.nav()]},
  {id:'minilab2',name:'Arturia MiniLab mkII',re:/minilab\s*mk\s*ii/i,info:'Set up by moving: 8 knobs for the selected device, 8 pads for the drum kit.',slots:[...CTS.k8(),...CTS.pads(8)]},
  {id:'keylab',name:'Arturia KeyLab',re:/keylab/i,info:'Set up by moving: knobs for the selected device, faders for 8 track levels and the master, transport and navigation buttons. Play, Stop and Record that send transport messages (MMC) work without it.',slots:[...CTS.k8(),...CTS.f(8),ctlS('Master fader','@ms'),...CTS.pads(8),...CTS.tr(),...CTS.nav()]},
  {id:'kontrol',name:'Komplete Kontrol (MIDI mode)',re:/komplete\s*kontrol|kontrol\s*[ams]\d/i,info:'In MIDI mode. Set up by moving: the 8 knobs for the selected device, transport and navigation buttons.',slots:[...CTS.k8(),...CTS.tr(),...CTS.nav()]},
  {id:'g88',name:'Any controller: 8 knobs and 8 faders',info:'Set up by moving: 8 knobs for the selected device, 8 faders for track levels, a master fader, transport and navigation buttons. Skip what your controller does not have.',slots:[...CTS.k8(),...CTS.f(8),ctlS('Master fader','@ms'),...CTS.tr(),...CTS.nav()]},
  {id:'gpad',name:'Any pad controller: 16 pads and 8 knobs',info:'Pads on channel 10 from note 36 (the usual drum notes) play the drum kit; the knobs: set up by moving.',slots:[...CTS.pads(16,36),...CTS.k8()]}];
const ctlTplAll=()=>CTPL.concat((Array.isArray(UI.ctlTpl)?UI.ctlTpl:[]).map(t=>Object.assign({user:1},t)));
const ctlTplFor=n=>CTPL.find(t=>t.re&&t.re.test(n)&&!(t.no&&t.no.test(n)))||null;
const ctlTplOn=dn=>{const m=ctlG().maps.find(m=>m.dev===dn&&m.tpl);return m?m.tpl:''};
/* apply a template to a device: its earlier template mappings go, messages already used by other mappings are left alone */
function ctlTplApply(dn,T){if(typeof T==='string')T=ctlTplAll().find(t=>t.id===T);if(!T)return 0;const g=ctlG();g.maps=g.maps.filter(m=>!(m.dev===dn&&m.tpl));
  const used=new Set(ctlAll().filter(m=>m.dev===dn||m.dev==='*').map(m=>ctlKey(m.type,m.ch,m.num)));let n=0;
  for(const s of T.slots){if(s.num==null)continue;const k=ctlKey(s.type,s.ch,s.num);if(used.has(k))continue;used.add(k);const knob=s.type==='cc'&&!String(s.target).startsWith('@cmd:');
    const m={id:'m'+rid(),dev:dn,type:s.type,ch:s.ch,num:s.num,target:s.target,min:0,max:1,take:s.type==='note'||!knob?'jump':(UI.ctlTake||'pickup'),enc:s.enc||'abs',fb:false,tpl:T.id,slot:s.l};if(knob&&!s.enc)m.auto=1;g.maps.push(m);n++}
  ctlDirty();saveUI();mlMark();ctlPagePaint();return n}
function ctlTplRemove(dn){const g=ctlG(),k=g.maps.length;g.maps=g.maps.filter(m=>!(m.dev===dn&&m.tpl));ctlDirty();saveUI();mlMark();ctlPagePaint();return k-g.maps.length}
function ctlTplSave(dn,name){const ms=ctlAll().filter(m=>m.dev===dn);if(!ms.length){toast('This device has no mappings to save yet.');return null}
  const T={id:'u'+rid(),name:String(name||'').trim().slice(0,60)||('My '+dn),from:dn,slots:ms.map(m=>({l:m.slot||ctlLabel(m.target),target:m.target,type:m.type,ch:m.ch,num:m.num,...(m.enc&&m.enc!=='abs'?{enc:m.enc}:{})}))};
  if(!Array.isArray(UI.ctlTpl))UI.ctlTpl=[];UI.ctlTpl.push(T);CTT.sel[dn]=T.id;saveUI();toast('Saved as your template "'+T.name+'".');ctlPagePaint();return T}
function ctlTplDel(id){if(!Array.isArray(UI.ctlTpl))return;UI.ctlTpl=UI.ctlTpl.filter(t=>t.id!==id);for(const k in CTT.sel)if(CTT.sel[k]===id)delete CTT.sel[k];saveUI();ctlPagePaint()}
/* set up by moving: each knob, fader, pad or button of the template in turn; the next new message from that device fills the slot */
function ctlGuide(dn,T){if(typeof T==='string')T=ctlTplAll().find(t=>t.id===T);if(!T)return;ctlStart();if(ML.on)midiLearn(false);CTL.relearn=null;CTT.guide={dn,T,i:0,got:new Set(),slots:T.slots.map(s=>Object.assign({},s,{num:null}))};ctlPagePaint()}
function ctlGuideIn(d,type,ch,num,raw){const G=CTT.guide;if(!d||d.name!==G.dn)return false;if(type==='pb')return true;const s=G.slots[G.i];if(!s)return true;
  const btn=String(s.target).startsWith('@cmd:'),pad=String(s.target).startsWith('@pad:');if(pad&&type!=='note')return true;if(!btn&&!pad&&type!=='cc')return true;
  const k=ctlKey(type,ch,num);if(G.got.has(k))return true;G.got.add(k);Object.assign(s,{type,ch,num});G.i++;if(G.i>=G.slots.length)ctlGuideEnd(true);else ctlPagePaint();return true}
function ctlGuideEnd(keep){const G=CTT.guide;CTT.guide=null;if(!G)return;if(keep){const n=ctlTplApply(G.dn,{id:G.T.id,slots:G.slots});CTT.sel[G.dn]=G.T.id;toast(n?G.dn+' is set up: '+n+' controls now work in AudioLab. Save it as your template to use it again.':'Nothing was set up.')}ctlPagePaint()}
const ctlGuideSkip=()=>{const G=CTT.guide;if(!G)return;G.i++;if(G.i>=G.slots.length)ctlGuideEnd(true);else ctlPagePaint()};
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&CTT.guide){ctlGuideEnd(false)}});
/* a known controller gets its template when it is first plugged in, unless it already has mappings */
{const _a=ctlAttach;ctlAttach=function(d){const r=_a.apply(this,arguments);try{if(d.prof&&d.prof.id==='generic'&&!ctlOff(d)){UI.ctlTplSeen=UI.ctlTplSeen||{};if(!UI.ctlTplSeen[d.name]){const T=ctlTplFor(d.name);
  if(T){UI.ctlTplSeen[d.name]=1;saveUI();if(T.slots.some(s=>s.num!=null)&&!ctlAll().some(m=>m.dev===d.name)){const n=ctlTplApply(d.name,T);if(n)setTimeout(()=>toast(d.name+': its knobs now move the selected device'+(T.slots.some(s=>s.target.startsWith('@pad:'))?' and its pads play the drum kit':'')+' ('+T.name+' template). Change it in Controllers.'),0)}}}}}catch(e){console.error('AudioLab controller template',e)}return r}}
/* ---- the Templates part of the mappings page ---- */
const CTLCSS3=`.ctlpg .cmtp{display:flex;flex-wrap:wrap;gap:6px 8px;align-items:center;padding:4px 4px}.ctlpg .cmtp b{font-weight:var(--fw5);min-width:120px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:200px}
.ctlpg .cmtp input[type=text]{font-size:var(--fs1);min-height:22px;width:180px;background:#0b0c0f;border:1px solid #2b2c34;border-radius:4px;padding:1px 6px;color:inherit}.ctlpg .cmtpi{opacity:.65;padding:0 4px 4px 8px;line-height:1.4}
.ctlpg .cmgd{padding:7px 10px;border-radius:6px;border:1px solid rgba(181,131,255,.6);background:rgba(181,131,255,.10);display:flex;flex-wrap:wrap;gap:6px 10px;align-items:center}.ctlpg .cmgd b{font-weight:var(--fw6)}
.ctlpg>*,.ctlpg>.cmtpl>*{flex-shrink:0}`;
function ctlTplHtml(){const o=(v,cur,l)=>`<option value="${esc(v)}"${String(cur)===String(v)?' selected':''}>${esc(l)}</option>`,G=CTT.guide;
  const devs=[...CTL.devs.values()].filter(d=>d.prof&&d.prof.id==='generic');let h='<h4>Templates</h4>';
  if(G){const s=G.slots[G.i];h+=`<div class="cmgd" title="Move each control on ${esc(G.dn)} once, in turn. A control already set is ignored, so keep going."><span>Setting up <b>${esc(G.dn)}</b> as ${esc(G.T.name)}: ${s?`move or press <b>${esc(s.l)}</b> now (${G.i+1} of ${G.slots.length})`:'done'}</span>
    <button data-k3="gskip" title="Your controller has no such control: go to the next one">Skip</button><button data-k3="gdone" title="Keep what is set up so far and stop">Finish</button><button data-k3="gstop" title="Stop and keep the mappings as they were (Esc)">Cancel</button></div>`}
  if(!devs.length)return h+`<div class="cmnone">${CTL.acc?'Connect a keyboard or pad controller to give it a template.':'MIDI is not on yet.'}${(UI.ctlTpl||[]).length?' Your templates: '+UI.ctlTpl.length+'.':''}</div>`;
  for(const d of devs){const on=ctlTplOn(d.name),m=ctlTplFor(d.name),sel=CTT.sel[d.name]!=null?CTT.sel[d.name]:(on||(m?m.id:'')),T=ctlTplAll().find(t=>t.id===sel),us=ctlTplAll().filter(t=>t.user);
    const nset=T?T.slots.filter(s=>s.num!=null).length:0,sv=CTT.saving===d.name;
    h+=`<div class="cmtp" data-d="${esc(d.name)}"><b title="${esc(d.name)}">${esc(d.name)}</b><select data-k3="tsel" title="A ready set of mappings for this controller">${o('',sel,'Choose a template')+CTPL.map(t=>o(t.id,sel,t.name+(m&&m.id===t.id?' (matches)':''))).join('')+(us.length?`<optgroup label="Yours">${us.map(t=>o(t.id,sel,t.name)).join('')}</optgroup>`:'')}</select>
      ${T?`<button data-k3="apply" title="${nset?'Map this controller with the template now':'This template has no messages yet: set it up by moving'}"${nset?'':' disabled'}>Use</button><button data-k3="guide" title="Move each knob, fader, pad and button of the template in turn, so AudioLab learns what your controller sends">Set up by moving</button>`:''}
      ${on?`<button data-k3="rm" title="Delete the mappings this template made for ${esc(d.name)}">Remove</button>`:''}
      ${sv?`<input type="text" data-k3="nm" placeholder="Name of the template" title="A name for your template" value="${esc('My '+d.name)}"><button data-k3="savego" title="Save this device's mappings as your template">Save</button><button data-k3="savex" title="Do not save">Cancel</button>`:`<button data-k3="save" title="Save every mapping of ${esc(d.name)} as your own template, to use again or on another controller">Save as my template</button>`}
      ${T&&T.user?`<button data-k3="tdel" title="Delete your template &quot;${esc(T.name)}&quot; (mappings already made stay)">Delete template</button>`:''}</div>
      <div class="cmtpi">${T?esc(T.user?'Your template, '+T.slots.length+' controls'+(T.from?', made on '+T.from:'')+'.':T.info)+(on===T.id?' In use.':''):m?'':'No known template for this controller: try "Any controller" and set it up by moving.'}</div>`}
  return h}
{const _p=ctlPagePaint;ctlPagePaint=function(){const r=_p.apply(this,arguments);const b=CTL.host;if(!b||!b.isConnected||b.closest('[hidden]'))return r;
  if(!document.getElementById('ctlCss3')){const st=document.createElement('style');st.id='ctlCss3';st.textContent=CTLCSS3;document.head.appendChild(st)}
  const mh=[...b.querySelectorAll(':scope>h4')].find(x=>x.textContent==='Mappings');if(!mh)return r;const w=document.createElement('div');w.className='cmtpl';w.style.display='contents';w.innerHTML=ctlTplHtml();mh.before(w);
  if(!b._k3){b._k3=1;b.addEventListener('click',e=>{const x=e.target.closest('[data-k3]');if(!x||x.tagName==='SELECT'||x.tagName==='INPUT')return;const k=x.dataset.k3,row=x.closest('[data-d]'),dn=row&&row.dataset.d,sel=dn!=null?(row.querySelector('[data-k3="tsel"]')||{}).value:'';
    if(k==='gskip')ctlGuideSkip();else if(k==='gdone')ctlGuideEnd(true);else if(k==='gstop')ctlGuideEnd(false);
    else if(k==='apply'){const n=ctlTplApply(dn,sel);toast(n?n+' controls of '+dn+' now work in AudioLab.':'Nothing new to map: those messages are already used by other mappings.')}
    else if(k==='guide')ctlGuide(dn,sel);else if(k==='rm'){const n=ctlTplRemove(dn);toast(n+' mappings of '+dn+' removed.')}
    else if(k==='save'){CTT.saving=dn;ctlPagePaint();const i=CTL.host.querySelector('[data-k3="nm"]');if(i){i.focus();i.select()}return}
    else if(k==='savego'){const i=row.querySelector('[data-k3="nm"]');CTT.saving=null;ctlTplSave(dn,i&&i.value)}else if(k==='savex'){CTT.saving=null}
    else if(k==='tdel')ctlTplDel(sel);ctlPagePaint()});
    b.addEventListener('change',e=>{const x=e.target.closest('[data-k3="tsel"]');if(!x)return;e.stopPropagation();CTT.sel[x.closest('[data-d]').dataset.d]=x.value;ctlPagePaint()});
    b.addEventListener('keydown',e=>{const x=e.target.closest&&e.target.closest('[data-k3="nm"]');if(!x)return;e.stopPropagation();if(e.key==='Enter'){const dn=x.closest('[data-d]').dataset.d;CTT.saving=null;ctlTplSave(dn,x.value);ctlPagePaint()}else if(e.key==='Escape'){CTT.saving=null;ctlPagePaint()}})}
  return r}}
FT_HOOKS.controllerTemplates={list:()=>ctlTplAll().map(t=>({id:t.id,name:t.name,user:!!t.user})),apply:(dn,id)=>ctlTplApply(dn,id),setup:(dn,id)=>ctlGuide(dn,id),save:(dn,name)=>ctlTplSave(dn,name),remove:dn=>ctlTplRemove(dn)};
