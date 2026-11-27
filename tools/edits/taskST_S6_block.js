/* ===== settings step S6 (task ST-S6), v0.251: search with synonyms and help text, the path in each result, in-place options with "Show me" =====
   docs/settings-round-1.md (D3b): the search at the top of Settings also reads each setting's help line and search words from the table (STT),
   shows the whole path (group › page › block) in each result, and finds the options that live in place (metronome, capture, snap, mixer
   switches, the Follow chip...). Choosing one of those closes Settings and lights the control where it lives ("Show me"). Nothing is copied. */
const STS6={v:'0.251'};
const ST6={
 IP:[/* id, label, where, search words, selector (or a function giving a rect), open before looking, what to say when it is not on screen */
  ['click','Metronome on or off','Transport bar, the metronome button','metronome click tick beat on off','#bClick',null,'The metronome button is hidden in the transport bar. Layout › Transport bar › Edit… shows it again.'],
  ['count','Count-in on or off','Transport bar, the count-in button','count-in count in precount pre-roll bars before recording metronome','#bCount',null,'The count-in button is hidden in the transport bar. Layout › Transport bar › Edit… shows it again.'],
  ['pattern','Metronome pattern','Transport bar, the pattern box next to the metronome','metronome pattern accents beats click setup','#mpat',null,'The pattern box is hidden in the transport bar. Layout › Transport bar › Edit… shows it again.'],
  ['capture','Capture','Transport bar, the Capture button','capture retro retrospective record look back buffer kept what i played','#bCap',null,'The Capture button is hidden in the transport bar. Layout › Transport bar › Edit… shows it again.'],
  ['lufs','Loudness read-out and target','Transport bar, the loudness read-out','loudness lufs target streaming spotify integrated meter','#lufsB',null,'The loudness read-out is hidden in the transport bar. Layout › Transport bar › Edit… shows it again.'],
  ['cpu','CPU read-out and the performance panel','Transport bar, the CPU read-out','cpu load processor performance light mode glass level quick switch dropouts','#cpu',null,'The CPU read-out is hidden in the transport bar. Layout › Transport bar › Edit… shows it again.'],
  ['follow','Follow the playhead on or off','The Follow chip on the ruler, next to the playhead','follow scroll playhead chip view moves with the song',()=>{const c=document.querySelector('#main canvas');if(!c||typeof FB==='undefined'||!FB)return null;const r=c.getBoundingClientRect();return{left:r.left+FB.x,top:r.top+FB.y,width:FB.w,height:FB.h}},null,'The Follow chip sits next to the playhead on the ruler and shows while the playhead is in view. Right-click it for the six ways to follow.'],
  ['compact','Compact channels','Mixer, the header','compact narrow thin strips channels mixer','#mxCmp','mixer','The mixer could not be opened here.'],
  ['cables','Cables','Mixer, the header','cables routing sends wires sidechain groups mixer','#mxCab','mixer','The mixer could not be opened here.'],
  ['monitor','Mono, Dim and swap','Mixer, the master strip','mono dim swap left right monitoring check master quieter','#mixWin .mx.master .mxmon','mixer','The mixer could not be opened here.'],
  ['snap','Snap in the piano roll','Piano roll, the header','snap grid quantize note length piano roll','#prSnap','pr','Open a MIDI clip to see the piano roll: Snap is in its header.'],
  ['scale','Scale and root','Piano roll, the header','scale key root lock piano roll','#prScale','pr','Open a MIDI clip to see the piano roll: the scale and root are in its header.']],
 grp(tab){try{const p=ST5P.find(x=>x[0]===tab);return p?p[2]:''}catch(e){return''}},
 extend(IDX){try{SETT.bind()}catch(e){}
  const have=new Set();
  for(const it of IDX){if(!it.el||it.ip)continue;const row=it.el.closest&&it.el.closest('[data-stid]'),r=row&&STX.get(row.dataset.stid);
   if(r){it.ex=(it.ex||'')+' '+r.l+' '+(r.h||'')+' '+(r.w||'');it.help=it.help||r.h||'';have.add(r.id)}it.grp=ST6.grp(it.tab)}
  for(const it of IDX)if(it.page)it.grp=ST6.grp(it.tab);
  /* a row per setting of the table that the window's text did not give (its label, block, help and words) */
  for(const r of STT){if(have.has(r.id)||r.same)continue;const el=SETT.row(r.id);if(!el)continue;const s=el.closest('#setBody>section[data-page]');if(!s)continue;
   const t=String(r.l||'').trim();if(!t)continue;const tab=s.dataset.page;if(IDX.some(x=>x.tab===tab&&x.t.toLowerCase()===t.toLowerCase()))continue;
   IDX.push({tab,tn:ST5.name(tab),el,t,head:r.b||'',ex:(r.h||'')+' '+(r.w||''),help:r.h||'',grp:ST6.grp(tab)})}
  for(const a of ST6.IP)IDX.push({ip:a[0],t:a[1],tn:a[2],head:'',ex:a[3]+' in place show me',tab:'',el:null,help:'Lives in place: '+a[2]+'. Choose it to close Settings and see it.'})},
 hl(t,v){const e=esc(t),ws=String(v||'').toLowerCase().split(/\s+/).filter(w=>w.length>1);if(!ws.length)return e;
  const re=new RegExp('('+ws.map(w=>esc(w).replace(/[.*+?^${}()|[\]\\]/g,'\\$&')).join('|')+')','ig');return e.replace(/(<[^>]*>)|([^<]+)/g,(m,tag,txt)=>tag||txt.replace(re,'<mark>$1</mark>'))},
 item(it,i,v){const path=it.ip?'In place: '+it.tn:(it.grp?it.grp+' › ':'')+it.tn+(it.head&&it.head!==it.t?' › '+it.head:'');
  return `<button role="option" data-qi="${i}" class="${i===0?'on':''}${it.ip?' st6ip':''}" title="${esc(it.help||'')}"><b>${ST6.hl(it.t,v)}</b><small>${esc(path)}${it.ip?'<em class="st6show">Show me</em>':''}</small></button>`},
 spot(r){if(!r||!(r.width>0))return false;let d=document.getElementById('st6Spot');if(!d){d=document.createElement('div');d.id='st6Spot';d.setAttribute('aria-hidden','true');document.body.appendChild(d)}
  d.style.left=(r.left-4)+'px';d.style.top=(r.top-4)+'px';d.style.width=(r.width+8)+'px';d.style.height=(r.height+8)+'px';d.classList.remove('on');void d.offsetWidth;d.classList.add('on');clearTimeout(ST6.tm);ST6.tm=setTimeout(()=>d.classList.remove('on'),2000);return true},
 show(it){const a=ST6.IP.find(x=>x[0]===it.ip);if(!a)return;try{closeSet()}catch(e){const s=document.getElementById('set');if(s)s.hidden=true}
  const look=()=>{let r=null;if(typeof a[4]==='function')r=a[4]();else{const el=document.querySelector(a[4]);if(el&&el.offsetParent){el.scrollIntoView({block:'nearest',inline:'nearest'});r=el.getBoundingClientRect()}}
   if(!ST6.spot(r))try{toast(a[6])}catch(e){}};
  if(a[5]==='mixer'){try{const w=document.getElementById('mixWin');if(!w||w.hidden)openMixer()}catch(e){}setTimeout(look,350)}
  else if(a[5]==='pr'){const p=document.getElementById('pr');if(!p||!p.classList.contains('open')){try{toast(a[6])}catch(e){}return}requestAnimationFrame(look)}
  else requestAnimationFrame(look)}};
/* the results float over the page (the sidebar scrolls and would cut them off): placed under the field on every input */
{const q=document.getElementById('setQ'),R=document.getElementById('setQR');
 const place=()=>{if(!q||!R||R.hidden)return;R.style.position='fixed';R.style.left='0px';R.style.top='0px';const a=R.getBoundingClientRect(),f=q.closest('.setsrch')||q,b=f.getBoundingClientRect();
  R.style.left=(b.left-a.left)+'px';R.style.top=(b.bottom+4-a.top)+'px';R.style.maxHeight=Math.max(160,Math.min(520,innerHeight-b.bottom-24))+'px'};
 if(q&&R){q.addEventListener('input',()=>requestAnimationFrame(place));q.addEventListener('focus',()=>requestAnimationFrame(place));addEventListener('resize',place)}}
