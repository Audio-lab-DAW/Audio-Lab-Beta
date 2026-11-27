/* v0.235 (task FT-C1b): the mappings page. ctlPagePaint draws the full page into the Controllers window or any host (lane B: FT_HOOKS.controllersPage):
   defaults for new mappings, filter by device, a live "last message" line, every mapping with an edit row (range, knob kind, speed of endless knobs,
   feedback, learn the controller message again), devices with their switch. Feedback also follows automation while playing (a check every 66 ms,
   only while playing and only when a mapping sends feedback). Styles are scoped to .ctlpg so the page looks the same inside Settings. */
const CTLCSS2=`.ctlpg{overflow:auto;padding:10px 12px;font-size:var(--fs1);display:flex;flex-direction:column;gap:9px;min-width:0}
.ctlpg h4{margin:4px 0 0;font:var(--fw6) var(--fs1) var(--ffu);text-transform:uppercase;letter-spacing:.06em;opacity:.6}
.ctlpg .cmbar{display:flex;gap:8px;flex-wrap:wrap;align-items:center}.ctlpg .cmbar label{display:flex;gap:5px;align-items:center;opacity:.85}
.ctlpg select,.ctlpg input[type=number]{font-size:var(--fs1);min-height:22px}.ctlpg input[type=number]{width:56px;background:#0b0c0f;border:1px solid #2b2c34;border-radius:4px;padding:1px 4px;color:inherit}
.ctlpg .cmlast{padding:5px 8px;border-radius:6px;background:rgba(0,0,0,.25);border:1px solid rgba(255,255,255,.07);font-variant-numeric:tabular-nums;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.ctlpg .cmlast b{font-weight:var(--fw6)}.ctlpg .cmlast.hot{border-color:rgba(181,131,255,.6)}
.ctlpg .cmr{display:grid;grid-template-columns:minmax(80px,1fr) minmax(120px,1.1fr) minmax(110px,1.5fr) 104px 112px 24px 24px;gap:6px;align-items:center;padding:3px 4px;border-radius:6px}
.ctlpg .cmr:hover{background:rgba(255,255,255,.05)}.ctlpg .cmr.h{opacity:.55;font-weight:var(--fw6)}.ctlpg .cmr.h:hover{background:none}.ctlpg .cmr.op{background:rgba(255,255,255,.06)}
.ctlpg .cmr span{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.ctlpg .cmr button{width:22px;min-height:22px;padding:0}.ctlpg .cmr .rng{opacity:.6}
.ctlpg .cmd{display:flex;flex-wrap:wrap;gap:8px 16px;align-items:center;padding:6px 8px 8px 12px;margin:-2px 0 4px 4px;border-left:2px solid rgba(181,131,255,.55)}
.ctlpg .cmd label{display:flex;gap:5px;align-items:center}.ctlpg .cmd small{opacity:.6}.ctlpg .cmd .rl.on{background:linear-gradient(#b583ff,#8d5ee0);color:#120a1c}
.ctlpg .cmdev{display:flex;align-items:center;gap:8px;padding:3px 4px}.ctlpg .cmdev b{flex:1;font-weight:var(--fw5)}.ctlpg .cmdev em{font-style:normal;opacity:.6}.ctlpg .cmnone{opacity:.6;padding:2px 4px}`;
const CTLU={open:new Set(),filter:'',lt:0};
const ctlPct=v=>Math.round(clamp(+v||0,0,1)*1000)/10;
function ctlValTxt(id,n){const C=CT.get(id);if(!C)return'';try{return C.spec.f(C.spec.v(clamp(n,0,1)))}catch(e){return''}}
function ctlLastTxt(){const L=CTL.last;if(!L)return'Last message: nothing yet. Move a knob or press a key on a controller.';
  const nm=L.type==='cc'?'CC '+L.num:L.type==='pb'?'Pitch bend':L.type==='note'?'Note '+L.num+(L.val?'':' off'):L.type==='at'?'Aftertouch':'Other';
  return`Last message: <b>${esc(L.dev)}</b>, ${esc(nm)} (channel ${L.ch+1}), value ${L.val}`}
function ctlLastSoon(){const b=CTL.host;if(!b||!b.isConnected)return;if(CTLU.lt)return;CTLU.lt=setTimeout(()=>{CTLU.lt=0;const e=b.querySelector('.cmlast');if(e){e.innerHTML=ctlLastTxt();e.classList.toggle('hot',!!CTL.relearn)}},50)}
ctlPagePaint=function(){const b=CTL.host;if(!b||!b.isConnected||b.closest('[hidden]'))return;
  if(!document.getElementById('ctlCss2')){const st=document.createElement('style');st.id='ctlCss2';st.textContent=CTLCSS2;document.head.appendChild(st)}
  b.classList.add('ctlpg');const devs=[...CTL.devs.values()],names=[...new Set(devs.map(d=>d.name).concat(ctlAll().map(m=>m.dev)))];
  if(CTLU.filter&&!names.includes(CTLU.filter))CTLU.filter='';
  const all=ctlAll().filter(m=>!CTLU.filter||m.dev===CTLU.filter).sort((a,c)=>(a.dev>c.dev)-(a.dev<c.dev)||(a.type>c.type)-(a.type<c.type)||a.ch-c.ch||a.num-c.num);
  const dn=d=>d==='*'?'Any device':d,o=(v,cur,l)=>`<option value="${v}"${String(cur)===String(v)?' selected':''}>${l}</option>`;
  const take=m=>m.type==='note'?'<span title="A note or button switches the control between the two ends of its range">Switch</span>':m.enc&&m.enc!=='abs'?'<span title="An endless knob: each step moves the control from where it is">Endless knob</span>':
    `<select data-k2="take" data-m="${m.id}" title="When the knob and the control on screen are at different places. Pick up: nothing moves until the knob passes the control. Scale: the control moves more slowly until they meet. Jump: the control jumps to the knob.">${o('pickup',m.take,'Pick up')+o('scale',m.take,'Scale')+o('jump',m.take,'Jump')}</select>`;
  const det=m=>{const lo=+(m.min??0),hi=+(m.max??1),rl=CTL.relearn===m.id;return`<div class="cmd" data-for="${m.id}">
    <label title="The part of the control's range the knob covers, in percent. A start above the end turns the knob around.">Range <input type="number" min="0" max="100" step="1" data-k2="min" data-m="${m.id}" value="${ctlPct(lo)}" title="Where the range starts, in percent of the control"><small>${esc(ctlValTxt(m.target,lo))}</small> to <input type="number" min="0" max="100" step="1" data-k2="max" data-m="${m.id}" value="${ctlPct(hi)}" title="Where the range ends, in percent of the control"><small>${esc(ctlValTxt(m.target,hi))}</small></label>
    ${m.type==='cc'?`<label title="How the controller sends this knob. Most knobs and faders send their place (0 to 127); endless knobs send steps, in one of three ways.">Knob <select data-k2="enc" data-m="${m.id}" title="Kind of knob">${o('abs',m.enc||'abs','Knob or fader')+o('rel2c',m.enc,'Endless (1 up, 127 down)')+o('relsb',m.enc,'Endless (1 up, 65 down)')+o('rel64',m.enc,'Endless (65 up, 63 down)')}</select></label>`:''}
    ${m.enc&&m.enc!=='abs'?`<label title="How far one step of the endless knob moves the control">Speed <select data-k2="sens" data-m="${m.id}" title="Speed of the endless knob">${o(.25,m.sens||1,'Very fine')+o(.5,m.sens||1,'Fine')+o(1,m.sens||1,'Normal')+o(2,m.sens||1,'Fast')+o(4,m.sens||1,'Very fast')}</select></label>`:''}
    ${(!m.enc||m.enc==='abs')?`<label title="Send the control's value back to the controller, for motor faders, LED rings and lit buttons"><input type="checkbox" data-k2="fb" data-m="${m.id}"${m.fb!==false?' checked':''} title="Send the value back to the controller"> Send back</label>`:''}
    <button class="rl${rl?' on':''}" data-k2="relearn" data-m="${m.id}" title="Use another knob, fader or button for this: click, then move it on the controller. Esc stops.">${rl?'Move a knob now…':'Learn again'}</button></div>`};
  b.innerHTML=`<div class="cmbar"><button data-k2="learn" title="MIDI learn: click a control in AudioLab, then move a knob, fader or button on your controller (Mod+L)">${ML.on?'Stop learning':'MIDI learn'}</button>${CTL.acc?'':`<button data-k2="start" title="Ask the browser for your MIDI devices">Find MIDI devices</button>`}
    <label title="What new mappings do when the knob and the control are at different places">New mappings <select data-k2="dtake" title="Takeover for new mappings">${o('pickup',UI.ctlTake||'pickup','Pick up')+o('scale',UI.ctlTake,'Scale')+o('jump',UI.ctlTake,'Jump')}</select></label>
    <label title="Where new mappings are kept. Shift-click while learning keeps one in this project only either way.">kept <select data-k2="dscope" title="Where new mappings are kept">${o('global',UI.ctlScope||'global','for every project')+o('project',UI.ctlScope,'in this project')}</select></label></div>
  <div class="cmlast" title="The last message any controller sent, to see which knob sends what">${ctlLastTxt()}</div>
  <h4>Devices</h4>${devs.length?devs.map(d=>`<label class="cmdev" title="${esc(d.name)}${d.out?'':' (AudioLab cannot send to it: no feedback)'}"><input type="checkbox" data-k2="dev" data-d="${esc(d.name)}"${ctlOff(d)?'':' checked'} title="Use this device in AudioLab"><b>${esc(d.name)}</b><em>${esc(d.prof?d.prof.name:'')}</em></label>`).join(''):`<div class="cmnone">${CTL.acc?'No MIDI device is connected.':'MIDI is not on yet.'}</div>`}
  <h4>Mappings</h4><div class="cmbar"><label title="Show the mappings of one device">Show <select data-k2="filter" title="Show the mappings of one device">${o('',CTLU.filter,'All devices')+names.map(n=>o(esc(n),CTLU.filter,esc(dn(n)))).join('')}</select></label><span class="cmn">${all.length} of ${ctlAll().length}</span></div>
  ${all.length?`<div class="cmr h"><span>Device</span><span>Message</span><span>Moves</span><span>Takeover</span><span>Where</span><span></span><span></span></div>`+all.map(m=>{const op=CTLU.open.has(m.id),lo=+(m.min??0),hi=+(m.max??1),rg=lo!==0||hi!==1?` <i class="rng">${ctlPct(lo)} to ${ctlPct(hi)}%</i>`:'';
    return`<div class="cmr${op?' op':''}" data-m="${m.id}"><span title="${esc(dn(m.dev))}">${esc(dn(m.dev))}</span><span title="${esc(ctlMsgName(m))}">${esc(ctlMsgName(m))}</span><span title="${esc(ctlLabel(m.target))}">${esc(ctlLabel(m.target))}${rg}</span>${take(m)}<select data-k2="scope" data-m="${m.id}" title="This project only, or every project">${o('global',m.scope,'Everywhere')+o('project',m.scope,'This project')}</select><button data-k2="open" data-m="${m.id}" title="${op?'Close the settings of this mapping':'Range, knob kind, feedback, learn again'}" aria-label="Edit this mapping" aria-expanded="${op}">${op?'▴':'▾'}</button><button data-k2="del" data-m="${m.id}" title="Delete this mapping" aria-label="Delete this mapping">✕</button></div>${op?det(m):''}`}).join(''):`<div class="cmnone">${CTLU.filter?'No mappings for this device.':'No mappings yet. Press MIDI learn, click a control, then move a knob on your controller.'}</div>`}`;
  if(b._k2)return;b._k2=1;
  b.addEventListener('click',e=>{const x=e.target.closest('[data-k2]');if(!x||x.tagName==='SELECT'||x.tagName==='INPUT')return;const k=x.dataset.k2,id=x.dataset.m;
    if(k==='learn')midiLearn();else if(k==='start')ctlStart();else if(k==='del'){CTLU.open.delete(id);if(CTL.relearn===id)CTL.relearn=null;ctlEdit(id,null)}
    else if(k==='open'){if(CTLU.open.has(id))CTLU.open.delete(id);else CTLU.open.add(id)}else if(k==='relearn'){CTL.relearn=CTL.relearn===id?null:id;if(CTL.relearn){ctlStart();if(ML.on)midiLearn(false)}}
    ctlPagePaint()});
  b.addEventListener('change',e=>{const x=e.target.closest('[data-k2]');if(!x)return;const k=x.dataset.k2,id=x.dataset.m;
    if(k==='dev'){UI.ctlOff=UI.ctlOff||{};if(x.checked)delete UI.ctlOff[x.dataset.d];else UI.ctlOff[x.dataset.d]=1;saveUI();for(const d of CTL.devs.values())if(d.name===x.dataset.d){if(x.checked)ctlAttach(d);else if(d.prof&&d.prof.detach)try{d.prof.detach(d)}catch(er){}}}
    else if(k==='filter')CTLU.filter=x.value;else if(k==='dtake'){UI.ctlTake=x.value;saveUI()}else if(k==='dscope'){UI.ctlScope=x.value;saveUI()}
    else if(k==='min'||k==='max'){const v=clamp((parseFloat(x.value)||0)/100,0,1);ctlEdit(id,{[k]:v})}
    else if(k==='enc')ctlEdit(id,{enc:x.value,auto:undefined});else if(k==='sens')ctlEdit(id,{sens:+x.value});else if(k==='fb'){ctlEdit(id,{fb:x.checked});ctlFbCount()}
    else ctlEdit(id,{[k]:x.value});
    const m=ctlAll().find(q=>q.id===id);if(m&&(k==='min'||k==='max'||k==='fb')){CTL.sent.delete(m.id);ctlFbQ(m)}ctlPagePaint()})};
/* learn again from the list: the next message from any enabled controller becomes this mapping's message */
{const _i=ctlIn;ctlIn=function(d,type,ch,num,raw){const rl=CTL.relearn;if(!rl||ML.on)return _i.apply(this,arguments);CTL.relearn=null;
  const m=ctlAll().find(x=>x.id===rl);if(!m)return _i.apply(this,arguments);const dn=d?d.name:'*',proj=m.scope==='project',st=proj?ctlP(false):ctlG();if(proj)pushUndo();
  st.maps=st.maps.filter(x=>x===m||!(x.type===type&&x.ch===ch&&x.num===num&&(x.dev===dn||x.dev==='*')));
  const wasNote=m.type==='note';Object.assign(m,{dev:dn,type,ch,num,enc:'abs'});if(type==='note')m.take='jump';else if(wasNote)m.take=UI.ctlTake||'pickup';if(type==='cc')m.auto=1;else delete m.auto;
  CTL.rt.delete(m);CTL.sent.delete(m.id);ctlDirty();if(proj)changed(false);else saveUI();toast(ctlMsgName(m)+(dn!=='*'?' on '+dn:'')+' now moves '+ctlLabel(m.target)+'.');ctlPagePaint();ctlFbQ(m);return true}}
{const _m=ctlMsg;ctlMsg=function(){const r=_m.apply(this,arguments);ctlLastSoon();return r}}
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&CTL.relearn){CTL.relearn=null;ctlPagePaint()}});
/* while playing, automation can move a mapped control that is not drawn: its value still goes back to the controller (a check every 66 ms, only while playing) */
function ctlPoll(){if(CTL.pollT)return;const tick=()=>{CTL.pollT=0;if(!play.on||!CTL.fbn)return;const I=ctlIndex();for(const ms of I.byT.values())for(const m of ms){if(m.fb===false||(m.enc&&m.enc!=='abs'))continue;const v=ctlOutVal(m);if(v!=null&&CTL.sent.get(m.id)!==v)ctlFbQ(m)}CTL.pollN=(CTL.pollN||0)+1;CTL.pollT=setTimeout(tick,66)};CTL.pollT=setTimeout(tick,66)}
{const _s=start;start=function(){const r=_s.apply(this,arguments);try{if(CTL.fbn)ctlPoll()}catch(e){}return r}}
