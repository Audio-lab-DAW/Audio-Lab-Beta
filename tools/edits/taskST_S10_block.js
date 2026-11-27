/* ===== settings step S10 (task ST-S10), v0.288: the Audio page, one copy of each audio setting, "Keep?" for device, rate and buffer =====
   docs/settings-round-1.md S10 (D1b) and docs/settings-audit.md 6 (Audio: output device, buffer with "Larger playback buffer", sample rate,
   processing block, headroom, keep awake, status, test tone). The Control Panel pop-up is folded into the page: its rows move whole (same
   elements, ids and handlers) into the cards Audio driver, Running now and Advanced. The copies on DAC and audio interface (engine sample rate,
   buffer, rate, recording offset and keep awake in Speed and delay and Protection, Play through) leave the page for a hidden holder, so the old
   code that fills them keeps working, and a read-out with a link to Audio takes their place. Their names stay as search words of the one row.
   D1b: changes apply at once; a new sample rate, buffer or larger playback buffer, and a device used for the first time, ask "Keep?" and go
   back by themselves after 15 s. A device used before switches at once with no question (the user's answer 4 of 27 Nov). Closing Settings
   keeps the change. No stored key moves; UI.st10Seen (new) remembers the devices that were kept. No engine code: only the selects' own
   handlers run, the same as before. */
const STS10={v:'0.288'};
/* the table: the copies leave (they were marked 'same' until this step), their names stay as search words of the one row */
(()=>{const gone={dacRate:'rate',dacRate2:'rate',dacBuffer:'buffer',dacRecOffset:'recOffset',dacKeepAwake:'keepAwake',playThrough:'outDev'};
 for(const[id,to]of Object.entries(gone)){const i=STT.findIndex(r=>r.id===id);if(i<0)continue;const r=STT[i],t=STX.get(to);
  if(t){const add=(r.l+' '+(r.w||'')+' '+(r.b||'')).toLowerCase().replace(/[()]/g,' ');t.w=((t.w||'')+' '+add).replace(/\s+/g,' ').trim()}
  STT.splice(i,1);STX.delete(id)}})();
function ST10HELP(){const p=ST10.os();return p==='mac'?'Choose the output in the Sound menu in the menu bar or in System Settings, Sound; AudioLab then follows the system output.':p==='win'?'Choose the output with the speaker icon on the taskbar or in Settings, System, Sound; AudioLab then follows the system output.':'Choose the output in the system\'s sound settings; AudioLab then follows the system output.'}
const ST10={done:false,pend:null,tmr:0,quiet:false,SEC:15,
 os(){const s=((navigator.userAgentData&&navigator.userAgentData.platform)||navigator.platform||navigator.userAgent||'').toLowerCase();return/mac|iphone|ipad/.test(s)?'mac':/win/.test(s)?'win':'other'},
 $:id=>document.getElementById(id),
 hold(){let h=ST10.$('st10Old');if(!h){h=document.createElement('div');h.id='st10Old';h.hidden=true;h.setAttribute('aria-hidden','true');h.inert=true;document.body.appendChild(h)}return h},
 row(id){const e=ST10.$(id);return e?e.closest('.cprow,label.chk'):null},
 card(id,title,html){const d=document.createElement('div');d.className='sbox st10c';d.id=id;d.innerHTML='<h4>'+title+'</h4>'+html;return d},
 go(sel){/* the read-outs on DAC and audio interface: open Audio and ring the control */try{ST5.go('audio',sel)}catch(e){}},
 build(){if(ST10.done)return;const $=ST10.$,sec=typeof ST5==='object'&&ST5.sec('audio'),dac=typeof ST5==='object'&&ST5.sec('dac'),cp=$('cp');
  if(!sec||!dac||!cp||!$('ifd')||!$('outSel'))return;ST10.done=true;const H=ST10.hold();
  /* Audio driver: output device, buffer and larger playback buffer, sample rate, the Audio devices window */
  const drv=$('outSel').closest('.sbox');
  if(drv){const d=drv.querySelector('.drv'),cb=$('cpBtn');if(cb){cb.hidden=true;H.appendChild(cb)}
   const at=drv.querySelector('.devrow')||null,put=e=>{if(e)drv.insertBefore(e,at)};
   put(ST10.row('bufSel'));
   {const hq=ST10.row('hqChk');if(hq){const t=[...hq.childNodes].find(n=>n.nodeType===3&&n.textContent.trim());if(t)t.textContent=' Larger playback buffer: steadier when the mix is heavy (adds delay when you play live)';hq.classList.add('st10sub');put(hq)}}
   put(ST10.row('ltPbSel'));/* lane J's playing buffer (LT-1) stays next to the buffer */
   put(ST10.row('srSel'));
   const hint=[...cp.querySelectorAll('p.hint')].find(p=>/restarts the audio engine/.test(p.textContent));
   if(hint){hint.textContent='Changes apply at once and restart the audio engine. A new sample rate or buffer, and a device used for the first time, ask "Keep?" and go back by themselves after '+ST10.SEC+' s. The browser rounds the buffer to what it supports, so the read-outs show the real one.';put(hint)}
   if(d){const o=$('outSel'),r=document.createElement('div');r.className='cprow st10out';r.innerHTML='<span>Output device</span>';d.before(r);r.appendChild(o);{const oc=ST10.row('ltOcChk');if(oc)r.after(oc)}/* lane J's output check (LT-1) under the device */H.appendChild(d)}}
  /* Running now: what the engine really does, refreshed with the strip while the page is open */
  const os=ST10.os(),ex=os==='win'?'Exclusive use of the device (WASAPI exclusive mode) and ASIO drivers need the desktop helper, which is not built yet.':os==='mac'?'Exclusive use of the device (hog mode) needs the desktop helper, which is not built yet.':'Exclusive use of the device needs the desktop helper, which is not built yet.';
  const now=ST10.card('st10Now','Running now','<div class="st10g">'+[['st10Sr','Engine runs at','The sample rate the audio engine runs at now, and whether it follows the device or a rate you fixed.'],['st10Buf','Buffer','The buffer the browser gives the engine, in samples and milliseconds. It can differ from the size you asked for: the browser rounds it to what the device supports.'],['st10Lat','Output latency','The time from the engine to your ears: the buffer plus the delay the system and the device report.'],['st10Dev','Plays through','The output device AudioLab plays through now.'],['st10Drop','Dropouts','Gaps in the sound since AudioLab started, as the browser counts them. If they grow, choose a bigger buffer.']].map(r=>'<div class="cprow" title="'+r[2]+'"><span>'+r[1]+'</span><b id="'+r[0]+'">–</b></div>').join('')+'</div><p class="hint st10ex">AudioLab plays through the system\'s shared mixer, on a Mac and on Windows. '+ex+'</p>');
  /* Advanced: processing block, headroom, recording offset, keep awake */
  const adv=ST10.card('st10Adv','Advanced','');
  for(const id of['rqSel','hdSel','recOff','kaChk']){const r=ST10.row(id);if(r)adv.appendChild(r)}
  adv.insertAdjacentHTML('beforeend','<p class="hint">Bit-perfect output, the safety ceiling, the DC blocker and balance are on <button type="button" class="st10lk" data-pmgo="dac" title="Open DAC and audio interface">DAC and audio interface</button>.</p>');
  {const tt=$('ttOn'),tb=tt&&tt.closest('.sbox'),ref=tb&&tb.parentNode===sec?tb:null;if(drv&&drv.parentNode===sec)drv.after(now);else sec.insertBefore(now,ref);now.after(adv)}
  /* what is left of the pop-up goes to the holder (the read-outs that latency() still writes, the old hint) */
  for(const id of['srO','latO','clkO']){const r=ST10.row(id);if(r)H.appendChild(r)}
  /* any other row another lane put into the pop-up stays visible, in Advanced */
  for(const r of[...cp.querySelectorAll('.cprow,label.chk')])if(r.querySelector('select,input'))adv.insertBefore(r,adv.querySelector('p.hint'))
  H.appendChild(cp);cp.hidden=true;
  /* DAC and audio interface: the copies leave, read-outs with a link take their place */
  const ro=(id,label,sel,tip)=>{const d=document.createElement('div');d.className='cprow st10ro';d.innerHTML='<span>'+label+'</span><div class="cpin"><b id="'+id+'">–</b><button type="button" class="mini" data-st10go="'+sel+'" title="'+tip+'">Change on Audio</button></div>';return d};
  {const lr=ST10.row('lockSr'),g=$('ifdRateG');if(lr&&g){g.insertBefore(ro('st10DSr','Engine sample rate','#srSel','The engine\'s sample rate is set once, on Audio. Opens it.'),lr);H.appendChild(lr)}}
  {const k=ST10.row('ifdKa');if(k)H.appendChild(k)}
  {const sp=$('ifdSpd');if(sp){const b=ST10.row('ifdBuf');if(b){sp.insertBefore(ro('st10DBuf','Buffer and sample rate','#bufSel','Buffer size and sample rate are set once, on Audio. Opens it.'),b);H.appendChild(b)}
   const s=ST10.row('ifdSr');if(s)H.appendChild(s);const o=ST10.row('ifdOff');if(o){sp.insertBefore(ro('st10DOff','Recording latency offset','#recOff','The recording latency offset is set once, on Audio, in Advanced. Measure the round trip here and Use it fills it in.'),o);H.appendChild(o)}}}
  {const o=ST10.row('ifdOut');if(o){o.parentNode.insertBefore(ro('st10DOut','Play through','#outSel','The output device is chosen once, on Audio. Opens it.'),o);H.appendChild(o)}}
  /* the recording page's link card points to the new place */
  {const p=document.querySelector('#st5Lat p.hint');if(p)p.textContent='The recording latency offset moves recorded audio earlier so it lines up with what you heard. It is on Audio, in Advanced; Interface mode on DAC and audio interface can measure it.'}
  /* the strip's output opens Audio, where the device is chosen now */
  {const b=document.querySelector('#st5Strip [data-st5r="out"]');if(b){b.dataset.tab5='audio';b.title='The output device AudioLab plays through now. Opens Audio.'}}
  /* the table follows the page */
  const set=(id,o)=>{const r=STX.get(id);if(r)Object.assign(r,o)};
  set('steady',{l:'Larger playback buffer',pg:'audio',b:'Audio driver',w:((STX.get('steady')||{}).w||'')+' steadier playback lossless listening high-quality playback larger buffer'});
  for(const id of['renderBlocks','headroom','recOffset','keepAwake'])set(id,{pg:'audio',b:'Advanced'});
  for(const id of['buffer','renderBlocks','rate','headroom','recOffset','keepAwake']){const r=STX.get(id);if(r&&!/control panel/.test(r.w||''))r.w=((r.w||'')+' control panel audio system').trim()}
  for(const id of['outDev','buffer','rate','steady']){const r=STX.get(id);if(r&&r.h&&!/Keep\?/.test(r.h))r.h=r.h.replace(/\|.*$/,'')+(id==='outDev'?' A device used for the first time asks "Keep?" and goes back by itself after '+ST10.SEC+' s; a device used before switches at once.':' A change asks "Keep?" and goes back by itself after '+ST10.SEC+' s.')}
  {const r=STX.get('outDev');if(r&&!r.h)r.h='The device AudioLab plays through. A device used for the first time asks "Keep?" and goes back by itself after '+ST10.SEC+' s; a device used before switches at once.'}
  /* the keep bar sits above the window's foot */
  {const f=document.querySelector('#set .setsf');if(f&&!$('st10Keep')){const k=document.createElement('div');k.id='st10Keep';k.className='st10k';k.hidden=true;k.setAttribute('role','alertdialog');k.setAttribute('aria-live','polite');k.setAttribute('aria-label','Keep the new audio settings?');
    k.innerHTML='<span class="st10kt"></span><button type="button" class="pri" data-st10k="keep" title="Keeps the new setting">Keep</button><button type="button" data-st10k="back" title="Goes back to the setting before, at once">Go back</button>';f.before(k)}}
  /* handlers: the selects keep their own; these only watch and can undo */
  ST10.wrapSel('bufSel','buf');ST10.wrapSel('srSel','rate');ST10.wrapSel('hqChk','hq');
  if(typeof adUseOut==='function'&&!adUseOut.__st10){const f=adUseOut;adUseOut=async function(id){const prev=UI.sink||'';const r=await f.apply(this,arguments);if((UI.sink||'')!==prev)ST10.outChanged(prev,UI.sink||'');return r};adUseOut.__st10=f}
  const st=$('set');
  st.addEventListener('click',e=>{const g=e.target.closest&&e.target.closest('[data-st10go]');if(g){ST10.go(g.dataset.st10go);return}
   const k=e.target.closest&&e.target.closest('[data-st10k]');if(k){k.dataset.st10k==='keep'?ST10.keep():ST10.back(false)}});
  ST10.seen(UI.sink||'',true);ST10.sync()},
 val(kind){return kind==='buf'?(UI.buf||0):kind==='rate'?(UI.sr||0):kind==='hq'?!!UI.hq:(UI.sink||'')},
 wrapSel(id,kind){const e=ST10.$(id),f=e&&e.onchange;if(!f||f.__st10)return;const g=function(ev){const prev=ST10.val(kind),r=f.call(this,ev);if(ST10.val(kind)!==prev)ST10.ask(kind,prev);ST10.sync();return r};g.__st10=f;e.onchange=g},
 seen(id,add){if(!id||id==='default')return true;const L=Array.isArray(UI.st10Seen)?UI.st10Seen:[];if(L.includes(id))return true;if(add){UI.st10Seen=[id].concat(L).slice(0,40);try{saveUI()}catch(e){}}return false},
 outChanged(prev,now){/* ST_HOOKS.outChanged: called by the output select after a switch that worked */ST10.sync();if(ST10.quiet||prev===now)return;if(ST10.seen(now))return;ST10.ask('dev',prev)},
 open(){const s=ST10.$('set');return !!s&&!s.hidden},
 ask(kind,prev){if(ST10.quiet||!ST10.open())return;const P=ST10.pend||(ST10.pend={k:{}});if(!(kind in P.k))P.k[kind]=prev;else if(P.k[kind]===ST10.val(kind))delete P.k[kind];
  if(!Object.keys(P.k).length){ST10.clear();return}P.t=ST10.SEC;ST10.bar();clearInterval(ST10.tmr);ST10.tmr=setInterval(()=>{if(!ST10.pend){clearInterval(ST10.tmr);return}if(!ST10.open()){ST10.keep();return}if(--ST10.pend.t<=0)ST10.back(true);else ST10.bar()},1000)},
 what(kind){const t=id=>{const e=ST10.$(id),o=e&&e.selectedOptions&&e.selectedOptions[0];return o?o.textContent.split(':')[0].replace(/\s*\(recommended\)/,'').trim():''};
  return kind==='buf'?'buffer '+t('bufSel'):kind==='rate'?'sample rate '+t('srSel'):kind==='hq'?'larger playback buffer '+(UI.hq?'on':'off'):'output '+(t('outSel')||'System default')},
 bar(){const k=ST10.$('st10Keep'),P=ST10.pend;if(!k)return;if(!P){k.hidden=true;return}const ks=Object.keys(P.k),w=ks.map(ST10.what);let s=w.join(', ');s=s.charAt(0).toUpperCase()+s.slice(1);
  k.dataset.mode='ask';k.querySelector('.st10kt').innerHTML='<b>'+esc(s)+'.</b> Keep '+(ks.length>1?'these':'it')+'? Going back in <span class="st10n">'+P.t+'</span> s.';for(const b of k.querySelectorAll('button'))b.hidden=false;k.hidden=false},
 clear(){clearInterval(ST10.tmr);ST10.tmr=0;ST10.pend=null;const k=ST10.$('st10Keep');if(k&&k.dataset.mode!=='done')k.hidden=true},
 keep(){const P=ST10.pend;if(P&&'dev' in P.k)ST10.seen(UI.sink||'',true);ST10.clear()},
 async back(auto){const P=ST10.pend;if(!P)return;ST10.clear();ST10.quiet=true;const ks=Object.keys(P.k);
  try{for(const kind of ks){const prev=P.k[kind];
    if(kind==='dev'){try{ensureCtx();let to=prev;if(ctx.setSinkId&&(typeof ctx.sinkId!=='string'||ctx.sinkId!==prev)){try{await ctx.setSinkId(prev)}catch(e){to='';await ctx.setSinkId('')}}UI.sink=to;saveUI();const o=ST10.$('outSel');if(o){try{await listOuts()}catch(e){}o.value=to}}catch(e){}}
    else{const id=kind==='buf'?'bufSel':kind==='rate'?'srSel':'hqChk',e=ST10.$(id),f=e&&e.onchange&&(e.onchange.__st10||e.onchange);if(!e||!f)continue;
     if(kind==='hq')e.checked=!!prev;else e.value=String(prev);f.call(e,{target:e})}}}finally{ST10.quiet=false}
  try{ifdSync()}catch(e){}ST10.sync();
  const k=ST10.$('st10Keep');if(k){k.dataset.mode='done';k.querySelector('.st10kt').innerHTML='<b>'+(auto?'No answer, so AudioLab went back':'Went back')+'</b> to the settings before.';for(const b of k.querySelectorAll('button'))b.hidden=true;k.hidden=false;
   setTimeout(()=>{if(k.dataset.mode==='done'){k.hidden=true;k.dataset.mode=''}},4000)}},
 outName(){let n='';const nm=ST10.$('ifdName');if(nm&&nm.textContent.trim()&&nm.textContent.trim()!=='–'&&!/^No output/.test(nm.textContent.trim()))n=nm.textContent.trim();
  if(!n){const o=ST10.$('outSel');if(o&&o.selectedOptions&&o.selectedOptions[0]&&o.value)n=o.selectedOptions[0].textContent.trim()}return n||'System default'},
 sync(){/* the read-outs on DAC and audio interface */const $=ST10.$,put=(id,v)=>{const e=$(id);if(e&&e.textContent!==v)e.textContent=v};if(!ST10.done)return;
  const opt=id=>{const e=$(id),o=e&&e.selectedOptions&&e.selectedOptions[0];return o?o.textContent.split(':')[0].replace(/\s*\(recommended\)/,'').trim():'–'};
  const c=typeof ctx!=='undefined'&&ctx?ctx:null,sr=c?c.sampleRate:0;
  put('st10DSr',opt('srSel')+(c?' · '+(sr/1000)+' kHz now':''));put('st10DBuf',opt('bufSel')+(UI.hq?', larger playback buffer':'')+' · '+opt('srSel'));
  put('st10DOff',(UI.recOff||0)+' ms');put('st10DOut',ST10.outName())},
 live(){/* Running now, with the strip's tick (twice a second) while Audio or DAC and audio interface is on screen */
  if(!ST10.done||typeof ST5!=='object'||(ST5.cur!=='audio'&&ST5.cur!=='dac')||!ST10.open())return;if(ST5.cur==='dac'){ST10.sync();return}
  const put=(id,v)=>{const e=ST10.$(id);if(e&&e.textContent!==v)e.textContent=v};const c=typeof ctx!=='undefined'&&ctx?ctx:null;
  if(!c){put('st10Sr','not started yet');put('st10Buf','–');put('st10Lat','–')}
  else{const sr=c.sampleRate,bl=c.baseLatency||0,ol=c.outputLatency||0;
   put('st10Sr',(sr/1000)+' kHz · '+(UI.sr?'fixed by you':'follows the device')+(c.state!=='running'?' · '+(c.state==='suspended'?'paused':c.state):''));
   put('st10Buf',bl?Math.round(bl*sr)+' samples · '+(bl*1000).toFixed(1)+' ms'+(UI.buf===-1?' · Auto':UI.buf>0&&Math.abs(Math.round(bl*sr)-UI.buf)>8?' (asked for '+UI.buf+')':''):'not reported by this browser');
   put('st10Lat',bl+ol>0?((bl+ol)*1000).toFixed(1)+' ms'+(ol?'':' (the device delay is not reported)'):'not reported by this browser')}
  put('st10Dev',ST10.outName());
  {let n=-1;try{n=urNow()>=0?URS.total:-1}catch(e){}put('st10Drop',n>=0?String(n)+' since start':'not counted by this browser')}}};
const ST10_HOOKS={outChanged:(p,n)=>ST10.outChanged(p,n)};
try{if(typeof ST_HOOKS==='object')ST_HOOKS.outChanged=ST10_HOOKS.outChanged}catch(e){}
{const _o10=openSettings;openSettings=function(){const x=_o10.apply(this,arguments);try{ST10.build();ST10.sync()}catch(e){console.warn('settings audio page (ST-S10)',e)}return x}}
{const _c10=closeSet;closeSet=function(){try{if(ST10.pend)ST10.keep()}catch(e){}return _c10.apply(this,arguments)}}
{const _t10=ST5.tick;ST5.tick=function(){const x=_t10.apply(this,arguments);try{ST10.live()}catch(e){}return x}}
/* ===== end of settings step S10 ===== */
