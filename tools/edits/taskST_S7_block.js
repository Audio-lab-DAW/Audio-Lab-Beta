/* ===== settings step S7 (task ST-S7), v0.262: the changed mark, reset per setting and per page, Reset all with a list and a backup first =====
   docs/settings-round-1.md (D2, all three): a blue bar on every row whose value differs from how it came, with a ↺ beside it that puts that one
   setting back; "Reset this page" in the page title (with Undo for 10 s); the sidebar counts the changed settings of each page. "Reset all
   settings…" now lists what it resets (the changed settings in the window and the options outside Settings that go back too) and saves a backup
   of every setting first; General › Settings backup and restore keeps the last 3 backups on this computer, restores one or saves it as a file
   (S18 builds the settings file with tick boxes on the same format). Rows are read from the settings table (STT, S4): only rows with a default,
   never the glass chain's rows (Performance and the Glass block) and never the block lists (layout, mixer, meters, shortcuts: their own Reset
   buttons stay). Every reset goes through the control, so the existing handlers run and store as before. Nothing per frame: the marks are
   redrawn after a change in the window and once a second while Settings is open. No audio code. */
const STS7={v:'0.262'};
const ST7={BK:'audiolab-settings-backups',undo:null,ut:0,tq:0,
 RS:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M2.5 8a5.5 5.5 0 1 0 1.7-4"/><path d="M2.5 2.5v3h3"/></svg>',
 ok(r){return !!r&&('d' in r)&&!r.own&&r.t!=='list'&&!!r.c},
 changed(r){return ST7.ok(r)&&SETT.isDefault(r.id)===false},
 host(r){const el=SETT.row(r.id);if(!el)return null;if(r.t==='cards')return el.closest('.cprow,.zsc,.phrow,.pnlrow,label')||el;return el},
 vtxt(r,v){if(v===undefined||v===null)return '';const el=SETT.ctl(r.id);let t;
  if(r.t==='check')t=(v===true||v==='true')?'on':'off';
  else if(r.t==='select'&&el){const o=[...el.options].find(o=>o.value===String(v));t=o?o.textContent:String(v)}
  else if(r.t==='cards'&&el){const b=[...el.querySelectorAll('button')].find(b=>{const k=Object.keys(b.dataset)[0];return k&&b.dataset[k]===String(v)});t=b?((b.querySelector('b,strong')||{}).textContent||b.getAttribute('aria-label')||b.textContent):String(v)}
  else if(r.t==='text')t='“'+v+'”';else t=String(v);
  t=String(t).replace(/\s+/g,' ').trim();return t.length>34?t.slice(0,33)+'…':t},
 /* the marks: blue bar and ↺ on each changed row, the count on each page button, the page's reset button */
 mark(){const st=document.getElementById('set');if(!st||st.hidden||!ST5.done)return;const per={},hosts=new Map(),seen=new Set();
  for(const r of STT){if(!ST7.ok(r))continue;const h=ST7.host(r);if(!h)continue;const ch=SETT.isDefault(r.id)===false;
   if(!hosts.has(h))hosts.set(h,[]);if(ch){hosts.get(h).push(r);if(!r.same)per[r.pg]=(per[r.pg]||0)+1}seen.add(r.id);
   let b=st.querySelector('.st7rs[data-st7="'+r.id+'"]');
   if(ch&&!b){b=document.createElement('button');b.type='button';b.className='st7rs';b.dataset.st7=r.id;b.innerHTML=ST7.RS;
    const ctl=SETT.ctl(r.id);if(h===ctl||(r.t==='cards'&&h===SETT.row(r.id)&&!h.matches('label,.cprow,.zsc,.phrow,.pnlrow'))){b.classList.add('st7af');h.after(b)}else h.appendChild(b)}
   if(b){b.hidden=!ch;if(ch){const tip='Back to the default: '+ST7.vtxt(r,r.d)+' (now '+ST7.vtxt(r,SETT.val(r.id))+')';if(b.title!==tip){b.title=tip;b.setAttribute('aria-label','Reset '+r.l+' to the default, '+ST7.vtxt(r,r.d))}}}}
  for(const[h,a]of hosts){const on=a.length>0;if(h.classList.contains('st7chg')!==on)h.classList.toggle('st7chg',on);if(on){const t='Changed from the default';if(h.dataset.st7t!==t)h.dataset.st7t=t}}
  for(const n of document.querySelectorAll('#setNav [data-tab]')){const c=per[n.dataset.tab]||0;let i=n.querySelector('.st7n');
   if(c&&!i){i=document.createElement('i');i.className='st7n';n.appendChild(i)}if(i){i.hidden=!c;const s=String(c);if(i.dataset.n!==s)i.dataset.n=s;/* drawn from data-n, so the page names (search, paths) keep their text */i.title=c+' setting'+(c>1?'s':'')+' on this page differ from the default'}}
  const pb=document.getElementById('st7Pg');if(pb){const pg=ST5.cur,has=STT.some(r=>r.pg===pg&&ST7.ok(r)),c=per[pg]||0,u=ST7.undo&&ST7.undo.pg===pg;
   pb.hidden=!has&&!u;pb.disabled=!c&&!u;const t=u?'Undo the reset':'Reset this page'+(c?' ('+c+')':'');if(pb.lastChild.textContent!==t)pb.lastChild.textContent=t;
   pb.title=u?'Puts the settings on this page back to how they were before the reset.':c?'Puts the '+c+' setting'+(c>1?'s':'')+' on this page that differ from the default back to the default. Other pages are untouched; you can undo it for 10 seconds.':'Every setting on this page is at its default.';
   pb.classList.toggle('st7u',!!u)}
  ST7.count=per},
 soon(){if(ST7.tq)return;ST7.tq=setTimeout(()=>{ST7.tq=0;try{ST7.mark()}catch(e){}},80)},
 one(id){const r=SETT.get(id);if(!ST7.ok(r))return false;const was=ST7.vtxt(r,SETT.val(id)),ok=SETT.reset(id);if(ok)toast(r.l+' is back at the default ('+ST7.vtxt(r,r.d)+'; it was '+was+').');ST7.mark();return ok},
 page(){const pg=ST5.cur;if(ST7.undo&&ST7.undo.pg===pg){const u=ST7.undo;ST7.undo=null;clearTimeout(ST7.ut);for(const x of u.list)SETT.set(x.id,x.v);toast(ST5.name(pg)+' is back as it was before the reset.');ST7.mark();return u.list.length}
  const rows=STT.filter(r=>r.pg===pg&&!r.same&&ST7.changed(r)),list=[];
  for(const r of rows){const v=SETT.val(r.id);if(SETT.reset(r.id))list.push({id:r.id,v})}
  if(!list.length){ST7.mark();return 0}
  ST7.undo={pg,list};clearTimeout(ST7.ut);ST7.ut=setTimeout(()=>{ST7.undo=null;ST7.mark()},10000);
  toast(list.length+' setting'+(list.length>1?'s':'')+' on '+ST5.name(pg)+' back at the default. Other pages are untouched.');ST7.mark();return list.length},
 /* backups of every setting, the last 3, on this computer */
 backups(){try{const a=JSON.parse(localStorage.getItem(ST7.BK)||'[]');return Array.isArray(a)?a.filter(b=>b&&b.UI&&typeof b.UI==='object'):[]}catch(e){return[]}},
 backup(why){try{saveUINow()}catch(e){}const b={kind:'audiolab-settings-backup',app:'AudioLab Pro',v:VERSION,at:Date.now(),why:why||'',UI:JSON.parse(JSON.stringify(UI))};
  const a=ST7.backups();a.unshift(b);while(a.length>3)a.pop();
  try{localStorage.setItem(ST7.BK,JSON.stringify(a))}catch(e){try{localStorage.setItem(ST7.BK,JSON.stringify([b]))}catch(e2){return null}}ST7.bkDraw();return b},
 when(b){try{return new Date(b.at).toLocaleString(undefined,{day:'numeric',month:'short',year:'numeric',hour:'2-digit',minute:'2-digit'})}catch(e){return String(b.at)}},
 file(b){try{const d=new Date(b.at),p=n=>String(n).padStart(2,'0'),nm='AudioLab settings backup '+d.getFullYear()+'-'+p(d.getMonth()+1)+'-'+p(d.getDate())+' '+p(d.getHours())+'-'+p(d.getMinutes())+'.json';
   const u=URL.createObjectURL(new Blob([JSON.stringify(b,null,1)],{type:'application/json'})),a=document.createElement('a');a.href=u;a.download=nm;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(u),4000);return nm}catch(e){toast('The backup could not be saved as a file.');return ''}},
 async restore(b){if(!b)return;const r=await askChoice('Restore the settings from '+ST7.when(b)+'?','Every setting goes back to how it was then and AudioLab reloads. Your settings as they are now are backed up first, so you can go back. Your projects and their files are not touched.',[{label:'Cancel',v:null},{label:'Restore',v:1,cls:'pri'}],ST7.RS.replace('viewBox="0 0 16 16"','viewBox="0 0 16 16" width="20" height="20"'));if(r!==1)return false;
  ST7.backup('before a restore');const u=JSON.parse(JSON.stringify(b.UI));if(!Array.isArray(u.order)||u.order.length!==4)u.order=['arr','fx','tr','map'];
  for(const k of Object.keys(UI))delete UI[k];Object.assign(UI,u);saveUINow();location.reload();return true},
 sel(){const s=document.getElementById('st7BkSel'),a=ST7.backups();return a[s?+s.value||0:0]||null},
 bkDraw(){const t=document.getElementById('st7BkT');if(!t)return;const a=ST7.backups(),s=document.getElementById('st7BkSel');
  t.textContent=a.length?'AudioLab keeps the last 3 backups on this computer. Reset all settings makes one before it resets.':'No backup yet. Reset all settings makes one before it resets; Back up now makes one at any time.';
  s.hidden=!a.length;s.innerHTML=a.map((b,i)=>'<option value="'+i+'">'+esc(ST7.when(b)+(b.why?', '+b.why:'')+(b.v?' (v'+b.v+')':''))+'</option>').join('');
  for(const id of['st7BkRes','st7BkFile']){const e=document.getElementById(id);if(e)e.disabled=!a.length}},
 build(){if(document.getElementById('st7Bk')||!ST5.done)return;const g=ST5.sec('general');if(!g)return;
  const c=ST5.card('st7Bk','Settings backup and restore','<p class="hint" id="st7BkT"></p><select id="st7BkSel" aria-label="Backups" title="The backups AudioLab keeps on this computer, newest first"></select><div class="st5btns"><button type="button" id="st7BkNow" title="Saves a copy of every setting on this computer now (the last 3 are kept)">Back up now</button><button type="button" id="st7BkRes" title="Puts every setting back to how it was in the chosen backup. Your settings as they are now are backed up first.">Restore…</button><button type="button" id="st7BkFile" title="Saves the chosen backup as a file you can keep or carry to another computer">Save as a file…</button></div>');
  g.appendChild(c);ST7.bkDraw();
  c.addEventListener('click',e=>{const b=e.target.closest('button');if(!b)return;if(b.id==='st7BkNow'){if(ST7.backup('made by hand'))toast('Settings backed up.');else toast('There is no room left for a backup in this browser. Save the settings as a file instead.')}
   else if(b.id==='st7BkRes')ST7.restore(ST7.sel());else if(b.id==='st7BkFile'){const n=ST7.file(ST7.sel());if(n)toast('Saved as “'+n+'”.')}});
  {const h=document.getElementById('st5Head');if(h&&!document.getElementById('st7Pg')){const b=document.createElement('button');b.type='button';b.id='st7Pg';b.innerHTML=ST7.RS+'<span>Reset this page</span>';h.appendChild(b)}}},
 /* what Reset all resets, in plain words */
 OUT:[['Metronome and count-in',['clickPlay','clickRec','clickCount','countIn','countBars','clickSnd','clickHi','clickLo','clickPat','clickLvl']],['Capture',['capPlace','capQ','capMax','capGap','retroOn','retroLen','retroSrc','retroSec']],
  ['Transport bar layout',['trOrder','trCompact','trHide','trX','trPalPos','flashSrc']],['Track controls in the headers',['hcz']],['Mixer view',['mxCompact','mxView','mxOpt','mxCol','mxCapW','mxFullH','mxAutoV','w9pf','fd7','fd22']],
  ['Visualizer',['vizW','vizH','vizMode','vxSnap','vcap']],['Map and master lane',['mapH','mapView','mapBeats']],['Piano roll',['prMem','prDev','prDH','prMode','prW','prLock','ghostGrey','velHF','velH']],
  ['Devices panel',['fxHide','fxOpt','fx','fxDH','fxBand','eqAll','ibFxSrc','devPop']],['Instrument browser',['ibSize','ibPos','ibAuto','ibGroups','ibPhrase','ibPP2']],['Keyboard piano',['kbPiano','kbMode','kbw','kbCompact','kbHidden']],
  ['MIDI controllers and learned mappings',['ctl','ctlAs','ctlTpl','ctlOff','ctlStop','ctlTake','ctlOn','ctlTplSeen','ctlScope','ctlSeen','midiMap','a2m']],['Window sizes and places',['win','winSized','winMoved','setSize','tmGeo']]],
 plan(){const rows=STT.filter(r=>('d' in r)&&r.t!=='list'&&!r.same&&SETT.isDefault(r.id)===false);
  const tk=new Set(STT.filter(r=>r.k&&r.k.startsWith('UI.')).map(r=>r.k.split('.')[1])),gk=new Set(),out=[];
  for(const[n,ks]of ST7.OUT){ks.forEach(k=>gk.add(k));if(ks.some(k=>UI[k]!==undefined))out.push(n)}
  const other=Object.keys(UI).filter(k=>k!=='keys'&&!tk.has(k)&&!gk.has(k)).length;return{rows,out,other}},
 fill(p){const P=document.getElementById('cdP');if(!P)return;const d=document.createElement('span');d.className='st7list';const add=(h,items)=>{const s=document.createElement('b');s.textContent=h;d.appendChild(s);const u=document.createElement('span');u.className='st7ul';for(const t of items){const i=document.createElement('span');i.textContent=t;u.appendChild(i)}d.appendChild(u)};
  if(p.rows.length){const byPg={};for(const r of p.rows)(byPg[r.pg]=byPg[r.pg]||[]).push(r);const items=[];
   for(const pg of ST5P.map(x=>x[0]))for(const r of byPg[pg]||[])items.push(ST5.name(pg)+' › '+r.l+': '+ST7.vtxt(r,SETT.val(r.id))+', back to '+ST7.vtxt(r,r.d));
   add('Changed in Settings ('+p.rows.length+')',items)}else add('Changed in Settings',['Nothing in this window differs from how it came.']);
  const o=p.out.slice();if(p.other)o.push(p.other+' other remembered choice'+(p.other>1?'s':'')+' (last used options, panel sizes)');
  if(o.length)add('Also back to how they came, outside Settings',o);
  add('Kept',['Your projects and their files','Your keyboard shortcuts']);P.appendChild(d)},
 async all(){const p=ST7.plan(),pr=askChoice('Reset all settings?','AudioLab first saves a backup of every setting, then puts them back to how they came and reloads. The backup can be restored or saved as a file in General › Settings backup and restore.',[{label:'Cancel',v:null},{label:'Back up and reset',v:1,cls:'dng pri'}],ST7.RS.replace('viewBox="0 0 16 16"','viewBox="0 0 16 16" width="20" height="20"'));
  try{ST7.fill(p)}catch(e){}const r=await pr;if(r!==1)return false;
  if(!ST7.backup('before Reset all')){const r2=await askChoice('The backup could not be saved','This browser has no room left for it. Save the settings as a file first, or reset without a backup.',[{label:'Cancel',v:null},{label:'Save as a file',v:2,cls:'pri'},{label:'Reset without a backup',v:1,cls:'dng'}]);
   if(r2===2){ST7.file({kind:'audiolab-settings-backup',app:'AudioLab Pro',v:VERSION,at:Date.now(),why:'before Reset all',UI:JSON.parse(JSON.stringify(UI))});return false}if(r2!==1)return false}
  const keep=UI.keys||{};for(const k of Object.keys(UI))delete UI[k];UI.keys=keep;saveUINow();location.reload();return true}};
{const gr=document.getElementById('genReset');if(gr){gr.onclick=()=>{ST7.all()};gr.title='Reset all settings: lists what goes back to how it came, saves a backup of every setting first, then resets and reloads. Your projects, files and shortcuts stay.'}
 const st=document.getElementById('set');if(st){for(const ev of['input','change'])st.addEventListener(ev,()=>ST7.soon(),true);
  st.addEventListener('click',e=>{const b=e.target.closest&&e.target.closest('.st7rs');if(b){e.preventDefault();e.stopPropagation();ST7.one(b.dataset.st7);return}
   if(e.target.closest&&e.target.closest('#st7Pg')){e.preventDefault();ST7.page();return}ST7.soon()},true)}
 const _s7=ST5.show;ST5.show=function(){const x=_s7.apply(this,arguments);try{ST7.build();ST7.mark()}catch(e){console.warn('settings marks (ST-S7)',e)}return x};
 const _o7=openSettings;openSettings=function(){const x=_o7.apply(this,arguments);setTimeout(()=>{try{ST7.build();ST7.bkDraw();ST7.mark()}catch(e){console.warn('settings marks (ST-S7)',e)}},0);return x};
 setInterval(()=>{try{ST7.mark()}catch(e){}},1000)}
