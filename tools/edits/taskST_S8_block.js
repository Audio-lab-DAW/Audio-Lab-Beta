/* ===== settings step S8 (task ST-S8), v0.262: scope, the marks and the Project group =====
   docs/settings-round-1.md (D5c): a small mark on each row says where a setting lives: "project" (kept in this song and its .audiolab file),
   "computer" (belongs to this machine: audio devices, rate, buffer, the DAC page, interface size) and "new" (the starting value for new
   projects); no mark = your own taste, the same in every project. The Project page (in the sidebar's Project group) gets two cards:
   "This song" (loudness target, key, the tempo and time signature lane) and "New projects start with" (tempo, loudness target, tempo lane).
   The loudness target (UI.lufsP) and the tempo lane (UI.tempoLane) move into the project: they stay readable under their old names (an
   accessor on UI), so every place that reads or sets them (master strip, Loudness window, menus, the lane) works unchanged and now acts on
   the open song. Migration: the old global values become the defaults for new projects, and every project open now is stamped with them,
   so nothing changes on screen. The key was already per project (S2, S.prKey). No audio code. */
const STS8={v:'0.262'};
const ST8={
 COMP:new Set(['sink','buf','rq','sr','headroom','recOff','keepAwake','ifMode','dac','bitPerfect','rateFollow','dcBlock','ceil','hq','inDev','inCh','inMon','outPair','scale']),
 nd(){if(!UI.stNew||typeof UI.stNew!=='object'||Array.isArray(UI.stNew))UI.stNew={};return UI.stNew},
 okL:v=>typeof LMT!=='undefined'&&LMT.some(x=>x[0]===v),
 defL(){const n=ST8.nd();return ST8.okL(n.lufs)?n.lufs:'spot'},
 defT(){return ST8.nd().tempoLane===true},
 st:null,
 save(){clearTimeout(ST8.st);ST8.st=setTimeout(()=>{try{saveProjects()}catch(e){}},400)},
 install(){if(ST8.done)return;ST8.done=true;const n=ST8.nd(),oL=UI.lufsP,oT=UI.tempoLane;
  if(n.lufs===undefined&&ST8.okL(oL))n.lufs=oL;if(n.tempoLane===undefined&&typeof oT==='boolean')n.tempoLane=oT;
  delete UI.lufsP;delete UI.tempoLane;
  Object.defineProperty(UI,'lufsP',{configurable:true,enumerable:true,get(){return typeof S==='object'&&S&&ST8.okL(S.lufsP)?S.lufsP:ST8.defL()},
   set(v){if(!ST8.okL(v)||typeof S!=='object'||!S||S.lufsP===v)return;S.lufsP=v;try{changed(false)}catch(e){}ST8.save()}});
  Object.defineProperty(UI,'tempoLane',{configurable:true,enumerable:true,get(){return typeof S==='object'&&S&&typeof S.tempoLane==='boolean'?S.tempoLane:ST8.defT()},
   set(v){if(typeof S!=='object'||!S)return;v=!!v;if(S.tempoLane===v)return;S.tempoLane=v;ST8.save()}});
  try{saveUI()}catch(e){}},
 stamp(s){if(!s||typeof s!=='object')return;if(!ST8.okL(s.lufsP))s.lufsP=ST8.defL();if(typeof s.tempoLane!=='boolean')s.tempoLane=ST8.defT()},
 stampAll(){try{ST8.stamp(S);if(typeof PJ==='object'&&PJ&&Array.isArray(PJ.list))for(const p of PJ.list)ST8.stamp(p.S)}catch(e){}},
 /* the table learns the new rows (search, marks, reset and S18's file read them from there) */
 ROWS:[
  {id:'songLufs',l:'Loudness target of this song',pg:'files',b:'This song',sc:'project',k:'S.lufsP',c:'#st8Lufs',t:'select',h:'The loudness this song aims at. The master strip and the loudness read-out measure against it. Each song keeps its own.',w:'loudness target lufs spotify apple club podcast broadcast master song per project'},
  {id:'songRoot',l:'Key of this song: root',pg:'files',b:'This song',sc:'project',k:'S.prKey.root',c:'#st8Root',t:'select',h:'The root note of the song’s key, the same as in the piano roll. Each song keeps its own.',w:'key root tonic note scale song piano roll'},
  {id:'songScale',l:'Key of this song: scale',pg:'files',b:'This song',sc:'project',k:'S.prKey.scale',c:'#st8Scale',t:'select',h:'The scale of the song’s key, the same as in the piano roll. Each song keeps its own.',w:'key scale major minor mode song piano roll'},
  {id:'songLane',l:'Show the tempo and time signature lane',pg:'files',b:'This song',sc:'project',k:'S.tempoLane',c:'#st8Lane',t:'check',h:'A lane above the tracks for tempo and time signature changes. Each song remembers whether it shows.',w:'tempo lane time signature lane bpm changes show hide'},
  {id:'newBpm',l:'Tempo for new projects',pg:'files',b:'New projects start with',sc:'app',nw:1,k:'UI.stNew.bpm',c:'#st8NBpm',t:'number',d:'',h:'The tempo the New project window starts with. Empty: the tempo of the song that is open, as before.',w:'tempo bpm new project default start'},
  {id:'newLufs',l:'Loudness target for new projects',pg:'files',b:'New projects start with',sc:'app',nw:1,k:'UI.stNew.lufs',c:'#st8NLufs',t:'select',d:'spot',h:'The loudness target a new project starts with. Songs you already have keep theirs.',w:'loudness target lufs new project default'},
  {id:'newLane',l:'Show the tempo lane in new projects',pg:'files',b:'New projects start with',sc:'app',nw:1,k:'UI.stNew.tempoLane',c:'#st8NLane',t:'check',d:false,h:'Whether new projects start with the tempo and time signature lane shown.',w:'tempo lane new project default'}],
 rows(){for(const r of ST8.ROWS)if(!STX.has(r.id)){const x=Object.assign({},r);STT.push(x);STX.set(x.id,x)}},
 q:id=>document.getElementById(id),
 lopts(){return LMT.map(x=>'<option value="'+x[0]+'">'+esc(x[1])+' ('+(x[2]<0?'−':'')+Math.abs(x[2])+' LUFS)</option>').join('')},
 build(){if(ST8.q('st8Song')||typeof ST5!=='object'||!ST5.done)return;const pg=ST5.sec('files');if(!pg)return;
  const pr=ST8.q('prRoot'),ps=ST8.q('prScale');
  const a=ST5.card('st8Song','This song','<p class="hint">Kept in this project and its .audiolab file: each song has its own. They are also where you use them: the loudness target on the master strip, the key in the piano roll, the tempo lane in the time signature menu.</p>'+
   '<div class="cprow st8r" title="'+esc(ST8.ROWS[0].h)+'"><span>Loudness target</span><select id="st8Lufs" aria-label="Loudness target of this song">'+ST8.lopts()+'</select></div>'+
   '<div class="cprow st8r" title="The key of the song, the same as in the piano roll. Each song keeps its own."><span>Key</span><span class="st8two"><select id="st8Root" aria-label="Key of this song: root">'+(pr?pr.innerHTML:'')+'</select><select id="st8Scale" aria-label="Key of this song: scale">'+(ps?ps.innerHTML:'')+'</select></span></div>'+
   '<label class="chk" title="'+esc(ST8.ROWS[3].h)+'"><input type="checkbox" id="st8Lane"> Show the tempo and time signature lane</label>');
  const b=ST5.card('st8New','New projects start with','<p class="hint">Starting values for projects you create from now on. Songs you already have keep their own.</p>'+
   '<div class="cprow st8r" title="'+esc(ST8.ROWS[4].h)+'"><span>Tempo</span><span class="st8two"><input type="number" id="st8NBpm" min="40" max="240" step="1" placeholder="open song" aria-label="Tempo for new projects"><i class="st8u">BPM</i></span></div>'+
   '<div class="cprow st8r" title="'+esc(ST8.ROWS[5].h)+'"><span>Loudness target</span><select id="st8NLufs" aria-label="Loudness target for new projects">'+ST8.lopts()+'</select></div>'+
   '<label class="chk" title="'+esc(ST8.ROWS[6].h)+'"><input type="checkbox" id="st8NLane"> Show the tempo lane</label>');
  pg.prepend(a,b);
  const on=(id,f)=>ST8.q(id).addEventListener('change',e=>{try{f(e.target)}catch(err){console.warn('settings scope (ST-S8)',err)}ST8.sync()});
  on('st8Lufs',el=>{UI.lufsP=el.value;saveUI();const s=ST8.q('lmSel');if(s)s.value=el.value;try{lmPaint()}catch(e){}});
  on('st8Root',el=>{PR.root=+el.value;try{STS2.prSync()}catch(e){}try{changed(false)}catch(e){}});
  on('st8Scale',el=>{PR.scale=el.value;try{STS2.prSync()}catch(e){}try{changed(false)}catch(e){}});
  on('st8Lane',el=>{tempoLaneShow(el.checked)});
  on('st8NBpm',el=>{const n=ST8.nd(),v=String(el.value).trim();if(v===''||!isFinite(+v))delete n.bpm;else n.bpm=Math.max(40,Math.min(240,Math.round(+v)));saveUI()});
  on('st8NLufs',el=>{ST8.nd().lufs=el.value;saveUI()});
  on('st8NLane',el=>{ST8.nd().tempoLane=el.checked;saveUI()});
  ST8.sync()},
 sync(){const g=ST8.q,set=(id,v)=>{const e=g(id);if(!e||document.activeElement===e)return;if(e.type==='checkbox'){if(e.checked!==!!v)e.checked=!!v}else if(e.value!==String(v))e.value=String(v)};
  if(!g('st8Song'))return;set('st8Lufs',UI.lufsP);try{set('st8Root',PR.root);set('st8Scale',PR.scale)}catch(e){}set('st8Lane',UI.tempoLane);
  const n=ST8.nd();set('st8NBpm',n.bpm==null?'':n.bpm);set('st8NLufs',ST8.defL());set('st8NLane',ST8.defT())},
 /* the marks: project, computer, new */
 TAG:{project:['project','Kept in this project: it travels with the song and its .audiolab file. Each song has its own.'],computer:['computer','Belongs to this computer and its audio hardware, not to the song.'],new:['new','The starting value for new projects. Songs you already have keep theirs.']},
 kind(r){if(r.own)return '';if(r.nw)return 'new';if(r.sc==='project')return 'project';const k=(r.k||'').split('.');if(k[0]==='UI'&&ST8.COMP.has(k[1]))return 'computer';return ''},
 mark(){const st=ST8.q('set');if(!st||st.hidden)return;for(const r of STT){const kd=ST8.kind(r);if(!kd)continue;const el=SETT.row(r.id);if(!el||el.querySelector(':scope .st8t'))continue;
  const t=document.createElement('i');t.className='st8t st8'+kd;t.dataset.t=ST8.TAG[kd][0];t.title=ST8.TAG[kd][1];t.setAttribute('aria-label',ST8.TAG[kd][0]);
  if(kd==='computer'){/* one mark on the card's title: every row of these cards belongs to the computer */const bx=el.closest('.sbox'),h=bx&&bx.querySelector('h4');if(h&&!h.querySelector('.st8t')){t.title='Everything in this card belongs to this computer and its audio hardware, not to the song.';h.appendChild(t)}continue}
  const host=r.t==='cards'?null:el;if(!host||host===SETT.ctl(r.id))continue;
  if(host.matches('label')){const tn=[...host.childNodes].filter(n=>n.nodeType===3&&n.textContent.trim()).pop();if(tn)tn.after(t);else{const rs=host.querySelector('.st7rs');rs?rs.before(t):host.appendChild(t)}}
  else{const s=host.querySelector(':scope>span,:scope>b,:scope>label');if(s&&!s.contains(SETT.ctl(r.id)))s.appendChild(t);else{const rs=host.querySelector(':scope>.st7rs');rs?rs.before(t):host.appendChild(t)}}}}};
ST8.install();ST8.rows();
{const nb=ST8.q('np');if(nb)new MutationObserver(()=>{if(nb.hidden)return;const n=ST8.nd(),e=ST8.q('npBpm');if(e&&n.bpm!=null&&!(typeof npT==='string'&&npT.startsWith('tpl:')))e.value=n.bpm}).observe(nb,{attributes:true,attributeFilter:['hidden']});
 const _sp=switchProject;switchProject=function(){const r=_sp.apply(this,arguments);try{ST8.stamp(S);lmPaint();const s=ST8.q('lmSel');if(s)s.value=UI.lufsP;renderHeaders();dirty=true;ST8.sync()}catch(e){}return r};
 for(const id of['prRoot','prScale','lmSel'])ST8.q(id)&&ST8.q(id).addEventListener('change',()=>setTimeout(ST8.sync,0));
 const _s8=ST5.show;ST5.show=function(){const x=_s8.apply(this,arguments);try{ST8.build();ST8.sync();ST8.mark()}catch(e){console.warn('settings scope (ST-S8)',e)}return x};
 const _o8=openSettings;openSettings=function(){const x=_o8.apply(this,arguments);setTimeout(()=>{try{ST8.build();ST8.sync();ST8.mark()}catch(e){console.warn('settings scope (ST-S8)',e)}},0);return x};
 setTimeout(ST8.stampAll,0);setTimeout(ST8.stampAll,4000);
 setInterval(()=>{const s=ST8.q('set');if(s&&!s.hidden&&!document.hidden)try{ST8.sync()}catch(e){}},1000)}
