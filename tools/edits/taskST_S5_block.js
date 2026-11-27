/* ===== settings step S5 (task ST-S5), v0.250: the new pages in the picked structure A3 =====
   docs/settings-round-1.md (A3) and docs/settings-audit.md section 6: 13 pages in four groups (Program, Working, Sound, Project), each page
   built from cards that use the width, under a strip of live read-outs (engine rate, buffer, CPU, frame rate, glass level, output); each
   read-out opens its page. Every block is moved whole (the same elements, ids and handlers: nothing is drawn twice, no stored key changes).
   The old page names stay as search words, and the old page ids still open the right page (glass and colors open Appearance at their card).
   Performance and the Glass block belong to the glass chain (G4): they are moved as they are, never changed here. */
const STS5={v:'0.250'};
const ST5P=[/* id, name, group, icon colour, icon (null: keep today's), old names and extra search words */
 ['general','General','Program',null,null,'general help tooltips splash tour closing about'],
 ['appearance','Appearance','Program','#ff7fb8','<path d="M10 3a7 7 0 1 0 0 14c1 0 1.5-.8 1.5-1.5s-.6-1.2-.6-2c0-.8.7-1.5 1.5-1.5H14a3 3 0 0 0 3-3c0-3.3-3.1-6-7-6zM6.5 9.5h0M9 6.5h0M13 7h0"/>','Glass & light Colours & clips colors look theme interface size scale glass blur transparency edge light background tint hue clip transparency grid app icon dock logo daw ableton fl studio cubase logic bitwig'],
 ['perf','Performance','Program',null,null,'performance light mode speed frame rate fps'],
 ['layout','Layout','Program',null,null,'Interface layout panels map visualizer transport bar track controls presets'],
 ['keys','Keyboard shortcuts','Program',null,null,'keys hotkeys'],
 ['nav','Navigation','Working',null,null,'Zoom and playhead zoom scroll keys follow playhead look'],
 ['editing','Editing','Working','#f5c84c','<path d="M4 16l1-4 8.5-8.5a2.1 2.1 0 0 1 3 3L8 15z"/><path d="M12 5l3 3"/>','editing playback chase pick up notes piano roll snap'],
 ['mixer','Mixer and meters','Working','#3ecf8e','<path d="M5 3v14M10 3v14M15 3v14"/><rect x="3.3" y="10" width="3.4" height="2.6" rx=".8"/><rect x="8.3" y="5.5" width="3.4" height="2.6" rx=".8"/><rect x="13.3" y="12" width="3.4" height="2.6" rx=".8"/>','Interface mixer channels strips meters level meters faders pan'],
 ['audio','Audio','Sound',null,null,'Audio system driver output device buffer latency sample rate test tone'],
 ['dac','DAC and audio interface','Sound',null,null,'Interface and DAC dac audio interface bit perfect protection limiter ceiling'],
 ['recording','Recording and metronome','Sound','#ff6b6b','<circle cx="10" cy="10" r="6.5"/><circle cx="10" cy="10" r="2.6" fill="currentColor"/>','recording record inputs microphone metronome click count-in capture latency offset midi controllers learn mappings'],
 ['files','Project','Project',null,null,'Project file save open autosave template'],
 ['export','Export','Project',null,null,'Export audio mixdown bounce render']];
const ST5W=Object.fromEntries(ST5P.map(p=>[p[0],p[5]]));
const ST5A={glass:['appearance','#st5Glass'],colors:['appearance','#st5Bg']};/* old page ids that live on as a card */
const ST5={done:false,cur:'general',tmr:0,
 alias(t){return ST5A[t]?ST5A[t]:[t,null]},
 name(t){const p=ST5P.find(x=>x[0]===t);return p?p[1]:t},
 sec(t){return document.querySelector('#setBody>section[data-page="'+t+'"]')},
 card(id,title,html,cls){const d=document.createElement('div');d.className='sbox'+(cls?' '+cls:'');d.id=id;d.innerHTML='<h4>'+title+'</h4>'+html;return d},
 build(){if(ST5.done)return;const body=document.getElementById('setBody'),nav=document.getElementById('setNav');if(!body||!nav)return;
  try{if(typeof stfBuild==='function')stfBuild()}catch(e){}try{if(typeof fxBuild==='function')fxBuild()}catch(e){}try{if(typeof pmBuild==='function')pmBuild()}catch(e){}
  const S0=t=>document.querySelector('#setBody section[data-page="'+t+'"]');
  if(!S0('general')||!S0('layout')||!S0('audio')||!S0('dac'))return;ST5.done=true;
  const boxOf=sel=>{const e=typeof sel==='string'?document.querySelector(sel):sel;return e?e.closest('.sbox'):null};
  const mk=(id,after)=>{let s=S0(id);if(!s){s=document.createElement('section');s.dataset.page=id;s.hidden=true;(after&&after.parentNode===body?after.after(s):body.appendChild(s))}return s};
  /* Appearance: theme, interface size, glass (the glass chain's section, as it is), background, clips, grid, app icon */
  const app=mk('appearance',S0('general'));
  {const th=boxOf('#dawPres'),sc=S0('layout').querySelector('.stfsc'),gl=S0('glass'),co=S0('colors');
   if(th){th.classList.add('st5w');app.appendChild(th)}
   if(sc){if(!sc.querySelector(':scope>h4')){const h=document.createElement('h4');h.textContent='Interface size';sc.prepend(h)}app.appendChild(sc)}
   {/* task LK's Density and motion rows (LK_HOOKS.appearanceRows: their page is Appearance); only their own block moves */const dn=document.getElementById('lkDens'),db=dn&&dn.closest('.sbox');if(db&&!db.classList.contains('stfl')&&!db.querySelector('#setScale,#layMap,#trEditBtn'))app.appendChild(db)}
   if(gl){gl.hidden=false;gl.classList.add('sbox','st5sec','st5w');if(!gl.querySelector(':scope>h4.st5h')){const h=document.createElement('h4');h.className='st5h';h.id='st5Glass';h.textContent='Glass';gl.prepend(h)}app.appendChild(gl)}
   if(co){co.hidden=false;co.classList.add('st5in');const b=co.querySelector('.sbox');if(b)b.id=b.id||'st5Bg';app.appendChild(co)}}
  /* Layout keeps the layout picture, the panels, the transport bar and the track controls; the zoom keys go to Navigation */
  const navS=S0('nav'),zs=document.getElementById('zsBox');
  if(navS&&zs){const c=document.createElement('div');c.className='sbox st5zs';c.appendChild(zs);const z=boxOf('#setZoom');(z?z.after(c):navS.prepend(c))}
  {const st=S0('layout').querySelector('.stfl');if(st)st.classList.add('st5w')}
  /* Editing: playback behaviour from Audio system, and where the editing options live */
  const ed=mk('editing',navS);
  {const ch=boxOf('#chaseChk')||boxOf(SETT.ctl&&SETT.ctl('chase'));if(ch)ed.appendChild(ch);
   ed.appendChild(ST5.card('st5Pr','Piano roll','<p class="hint">Snap, chords, ghost notes and the scale lock are in the piano roll’s own header, where you use them. AudioLab remembers them; the scale and root are kept in the project.</p>'))}
  /* Mixer and meters: the mixer and level meter blocks from Interface, with a way to the mixer itself */
  const mx=mk('mixer',ed);
  {mx.appendChild(ST5.card('st5Mx','The mixer','<p class="hint">Compact channels, cables, Mono, Dim and the loudness target are on the mixer itself.</p><div class="st5btns"><button type="button" id="st5ShowMix" title="Close Settings and show the mixer">Show the mixer</button></div>','st5w st5slim'));
   const a=boxOf('#mxsSet'),b=boxOf('#mtrSet');if(a){a.classList.add('st5w');mx.appendChild(a)}if(b){b.classList.add('st5w');mx.appendChild(b)}}
  /* DAC and audio interface: the protection block (the safety limiter) joins the hardware page */
  {const d=S0('dac'),li=boxOf(SETT.ctl&&SETT.ctl('limiter'));const ifd=document.getElementById('ifd');if(ifd)ifd.classList.add('st5w');if(d&&li){const h=li.querySelector('h4');if(h&&h.textContent.trim()==='Safety and monitoring')h.textContent='Protection';d.appendChild(li)}}
  /* Recording and metronome: what exists today, linked where it lives */
  const rec=mk('recording',S0('dac'));
  {rec.appendChild(ST5.card('st5In','Inputs','<p class="hint">Record from, the input channels and input monitoring are on DAC and audio interface, in Interface mode.</p><div class="st5btns"><button type="button" data-pmgo="dac" title="Open DAC and audio interface">DAC and audio interface</button></div>'));
   rec.appendChild(ST5.card('st5Lat','Latency','<p class="hint">The recording latency offset moves recorded audio earlier so it lines up with what you heard. It is in the audio driver panel on Audio.</p><div class="st5btns"><button type="button" data-pmgo="audio" title="Open Audio">Audio</button></div>'));
   rec.appendChild(ST5.card('st5Met','Count-in and metronome','<p class="hint">The click sound, its level, the count-in and the patterns for each time signature. Metronome and count-in are switched on in the transport bar.</p><div class="st5btns"><button type="button" id="st5Mset" title="Open the Metronome setup">Metronome setup…</button></div>'));
   rec.appendChild(ST5.card('st5Cap','Capture','<p class="hint">Capture keeps what you played while nothing was recording. Its source, length and options are in the Capture panel of the transport bar.</p><div class="st5btns"><button type="button" id="st5CapB" title="Close Settings and open the Capture panel">Show the Capture panel</button></div>'));
   if(typeof FT_HOOKS==='object'&&FT_HOOKS.controllersPage)rec.appendChild(ST5.card('st5Ctl','MIDI controllers','<p class="hint">Your MIDI keyboards and control surfaces, MIDI learn and every learned mapping, with its range and takeover, are in the Controllers window.</p><div class="st5btns"><button type="button" id="st5CtlB" title="Close Settings and open the Controllers window">Controllers…</button></div>'))}
  /* the pages that become card grids */
  for(const t of['general','appearance','layout','nav','editing','mixer','audio','dac','recording','files'])S0(t)&&S0(t).classList.add('st5g');
  /* the sidebar: four groups, today's icons kept */
  {const old=[...nav.querySelectorAll('[data-tab]')],ic={};for(const b of old){const i=b.querySelector('.nic');if(i)ic[b.dataset.tab]=i.outerHTML}
   ic.appearance=ic.colors||ic.appearance;for(const b of old)b.remove();for(const h of[...nav.querySelectorAll('.navh')])h.remove();
   const atom=nav.querySelector('.navAtom');let g='',html='';
   for(const[id,n,grp,col,svg]of ST5P){if(grp!==g){html+=`<small class="navh${g?' navsep':''}">${grp}</small>`;g=grp}
    const i=svg||!ic[id]?`<i class="nic" style="--ic:${col||'#cfd3db'}"><svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${svg||''}</svg></i>`:ic[id];
    html+=`<button type="button" data-tab="${id}"${grp==='Project'?' class="navex"':''} title="${esc(n)}">${i}${esc(n)}</button>`}
   const f=document.createElement('div');f.id='st5Nav';f.innerHTML=html;(atom?atom.before(...f.childNodes):nav.append(...f.childNodes))}
  /* the live read-outs */
  {const sh=document.querySelector('#set .setw>.sh');if(sh&&!document.getElementById('st5Strip')){sh.parentNode.classList.add('st5s');const s=document.createElement('div');s.id='st5Strip';s.setAttribute('role','group');s.setAttribute('aria-label','Live read-outs');
    const B=(k,u,pg,tip)=>`<button type="button" data-st5r="${k}" data-tab5="${pg}" title="${tip}"><i>${u}</i><span>–</span></button>`;
    s.innerHTML=B('rate','Engine','audio','The sample rate the audio engine runs at now. Opens Audio.')+B('buf','Buffer','audio','The buffer the browser reports for the engine, in samples and milliseconds. Smaller reacts faster, bigger plays steadier. Opens Audio.')+
     B('cpu','CPU','perf','How busy the audio engine is (the same number as the CPU read-out in the transport bar). Opens Performance.')+B('fps','Frame','perf','Pictures a second that AudioLab draws now. Opens Performance.')+
     B('glass','Glass','perf','The glass level now: Glass, Light or Solid. Opens Performance.')+B('out','Out','dac','The output device AudioLab plays through now. Opens DAC and audio interface.');sh.after(s)}}
  {const h=document.createElement('div');h.id='st5Head';h.innerHTML='<b id="st5T"></b><small id="st5Sub"></small>';body.prepend(h)}
  /* the table knows where each row lives now; the old page name stays a search word */
  try{for(const r of STT){const el=SETT.ctl(r.id),s=el&&el.closest('#setBody>section[data-page]');if(!s)continue;const np=s.dataset.page;if(np!==r.pg){const on={audio:'Audio system',dac:'Interface and DAC',layout:'Interface',glass:'Glass & light',colors:'Colours & clips',nav:'Zoom and playhead',files:'Project file',export:'Export audio'}[r.pg];if(on&&!(r.w||'').includes(on.toLowerCase()))r.w=(r.w||'')+' '+on.toLowerCase();r.p0=r.pg;r.pg=np}}}catch(e){}
  /* one click handler for the sidebar (it replaces today's: same work for Export and Layout) */
  nav.onclick=e=>{const b=e.target.closest('[data-tab]');if(!b)return;ST5.show(b.dataset.tab)};
  document.getElementById('set').addEventListener('click',e=>{const r=e.target.closest&&e.target.closest('[data-tab5]');if(r){ST5.go(r.dataset.tab5);return}
   if(e.target.closest&&e.target.closest('#st5ShowMix')){ST5.close();try{if(!document.getElementById('mixWin')||document.getElementById('mixWin').hidden)openMixer()}catch(err){}return}
   if(e.target.closest&&e.target.closest('#st5Mset')){const m=document.getElementById('mpat');if(m)m.click();return}
   if(e.target.closest&&e.target.closest('#st5CtlB')){ST5.close();setTimeout(()=>{try{ctlPage()}catch(err){}},60);return}
   if(e.target.closest&&e.target.closest('#st5CapB')){ST5.close();setTimeout(()=>{try{if(typeof CAPP==='undefined'||!CAPP)capOpen()}catch(err){}},60)}});
  ST5.show(ST5.cur,true)},
 close(){const x=document.getElementById('setX');if(x)x.click();else{const s=document.getElementById('set');if(s)s.hidden=true}},
 show(t,quiet){const[pg]=ST5.alias(t);if(!ST5.sec(pg))return;ST5.cur=pg;
  for(const b of document.querySelectorAll('#setNav [data-tab]'))b.classList.toggle('on',b.dataset.tab===pg);
  for(const s of document.querySelectorAll('#setBody>section[data-page]'))s.hidden=s.dataset.page!==pg;
  if(!quiet){if(pg==='export'){try{ensureCtx();exUI()}catch(e){}}if(pg==='layout'){try{renderMini()}catch(e){}}}
  const p=ST5P.find(x=>x[0]===pg),n=STT.filter(r=>r.pg===pg&&!r.same).length;
  const T=document.getElementById('st5T'),Sb=document.getElementById('st5Sub');if(T&&p){T.textContent=p[1];Sb.textContent=p[2]+(n?' · '+n+' setting'+(n>1?'s':''):'')}
  const bd=document.getElementById('setBody');if(bd&&!quiet)bd.scrollTop=0;ST5.tick()},
 go(t,focus){/* used by the strip, the old page ids and the quick routes */const[pg,card]=ST5.alias(t);const b=document.querySelector('#setNav [data-tab="'+pg+'"]');if(b)b.click();else ST5.show(pg);
  const sel=focus||card;if(sel){requestAnimationFrame(()=>{const c=document.querySelector(sel),el=c&&(c.closest('.sbox')||c);if(!el)return;el.scrollIntoView({block:'start'});el.classList.remove('sflash');void el.offsetWidth;el.classList.add('sflash');setTimeout(()=>el.classList.remove('sflash'),1800)})}},
 tick(){const st=document.getElementById('set'),s=document.getElementById('st5Strip');if(!st||st.hidden||!s||document.hidden)return;
  const put=(k,v,tip)=>{const b=s.querySelector('[data-st5r="'+k+'"] span');if(b&&b.textContent!==v)b.textContent=v;if(tip!=null){const bb=b&&b.parentNode;if(bb&&bb.dataset.full!==tip){bb.dataset.full=tip}}};
  const c=typeof ctx!=='undefined'?ctx:null,sr=c?c.sampleRate:0;
  put('rate',c?(sr/1000)+' kHz'+(c.state!=='running'?' · '+(c.state==='suspended'?'paused':c.state):''):'not started');
  {const bl=c&&c.baseLatency?c.baseLatency:0;put('buf',c?(bl?Math.round(bl*sr)+' smp · '+(bl*1000).toFixed(1)+' ms':'not reported'):'–')}
  {const v=document.getElementById('cpuV');put('cpu',v&&/\d/.test(v.textContent)?v.textContent.replace(/\s*%$/,'')+' %':'–')}
  put('fps',typeof FPS==='object'&&FPS.fps?FPS.fps+' fps':'–');
  {let lv='';try{lv=GLE.lv}catch(e){}put('glass',{glass:'Glass',light:'Light',solid:'Solid'}[lv]||'–')}
  {let n='';const nm=document.getElementById('ifdName');if(nm&&nm.textContent.trim()&&nm.textContent.trim()!=='–')n=nm.textContent.trim();
   if(!n){const o=document.getElementById('outSel');if(o&&o.selectedOptions&&o.selectedOptions[0])n=o.selectedOptions[0].textContent.trim()}
   if(!n)n='System default';put('out',n.length>30?n.slice(0,29)+'…':n,n)}}};
{const _o5=openSettings;openSettings=function(tab){try{ST5.build()}catch(e){console.error('AudioLab settings pages (ST-S5)',e)}
  const[pg,card]=tab?ST5.alias(tab):[null,null];const r=_o5.call(this,pg||undefined);if(!pg){try{ST5.show(ST5.cur,true)}catch(e){}}
  if(card)ST5.go(pg,card);try{ST5.tick()}catch(e){}return r}}
setTimeout(()=>{try{ST5.build()}catch(e){console.error('AudioLab settings pages (ST-S5)',e)}},1500);
ST5.tmr=setInterval(()=>{try{ST5.tick()}catch(e){}},500);
