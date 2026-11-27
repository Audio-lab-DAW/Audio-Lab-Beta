/* ===================== ADVANCED SETTINGS LIST (v0.000, task XT-DL3) =====================
   The everything list of the Workshop (docs/extensions-plan.md 9.6 a and f, 9.7 DL3; the user's picks K2b its own window, K3a "Workshop",
   K4a always in the menu). One searchable list of every setting by a stable id:
   - every row of the settings table STT (task ST-S4), changed through SETT.set, so the Settings window's own handler runs and nothing is
     written twice; the glass chain's rows (own:'glass') and the list rows are shown, but changed only in Settings;
   - XT_SET_OWN: values with no control in Settings (some have none at all, some are set by a menu or a drag elsewhere), and the locked values
     (the script sandbox's limits), shown read-only with the reason.
   Ids: XT_SET_NS names each STT row once (page.id, frozen at v0.000 so a row that moves to another page keeps its id); docs/settings-ids.md
   lists every released id. A released id is never renamed or reused (9.4 rule 1). A new STT row without a name here is shown as settings.<id>
   and tools/ui-tests/taskXT_DL3.py asks for a row in XT_SET_NS and docs/settings-ids.md.
   Storage: a value with no key of its own lives in UI.xtSet (differences only); with nothing changed UI.xtSet does not exist.
   Cost: nothing runs at start, per frame or per key. xtV(id, default) is one property test where a constant was. The list is built when the
   Workshop opens. Safe mode (DL4) will skip UI.xtSet. */
const XT_SET_NS=__NS__;
const XT_SET_OWN=[
 {id:'edit.undoSteps',l:'How many steps Undo keeps',t:'num',d:80,min:20,max:400,step:10,u:'steps',kind:'none',w:'undo history memory steps',
  h:'Undo keeps this many steps of the open project. More steps use more memory; the oldest step goes first.'},
 {id:'performance.frozenMemoryMB',k:'bgfMB',l:'Memory for frozen tracks',t:'num',d:384,min:64,max:4096,step:64,u:'MB',kind:'none',w:'background freeze memory cpu cache',
  h:'Background freeze keeps finished renders of tracks in memory up to this size; the least recently played go first when it is full.'},
 {id:'workshop.consoleLines',l:'Commands kept in the run log',t:'num',d:50,min:10,max:500,step:10,u:'lines',kind:'none',w:'console log commands history',
  h:'How many of the last commands the run log keeps (runCommand). The Workshop console shows them.'},
 {id:'capture.phraseGapS',k:'capGap',l:'Capture: a phrase ends after a silence of',t:'num',d:10,min:2,max:60,step:1,u:'s',kind:'else',where:'the Capture menu (4, 10 or 30 seconds)',w:'capture retro phrase silence gap'},
 {id:'capture.maxMinutes',k:'capMax',l:'Capture: longest phrase kept',t:'num',d:5,min:1,max:30,step:1,u:'min',kind:'else',where:'the Capture menu (1, 5 or 30 minutes)',w:'capture retro length minutes'},
 {id:'metronome.countInBars',k:'countBars',l:'Count-in length',t:'num',d:1,min:1,max:4,step:1,u:'bars',kind:'else',where:'the metronome menu',w:'count in bars metronome pre roll'},
 {id:'arrange.mapHeight',k:'mapH',l:'Height of the Map',t:'num',d:110,min:60,max:400,step:5,u:'px',kind:'else',where:'dragging the Map\'s edge',w:'map overview height',
  apply:()=>{try{applyMapH()}catch(e){}}},
 {id:'pianoRoll.velocityHeight',k:'velH',l:'Height of the velocity lane in the piano roll',t:'num',d:64,min:32,max:400,step:4,u:'px',kind:'else',where:'dragging the lane\'s edge',w:'piano roll velocity lane height',
  apply:()=>{try{dirty=true}catch(e){}}},
 {id:'scripts.timeLimitMs',l:'Time a script may run before you are asked to wait or stop it',t:'num',d:2000,u:'ms',kind:'lock',w:'script sandbox time limit safety',
  why:'Keeps a script from freezing AudioLab. At the limit you choose: wait longer, or stop it.'},
 {id:'scripts.maxLogLines',l:'Lines a script may print in one run',t:'num',d:200,u:'lines',kind:'lock',w:'script sandbox console log safety',why:'Keeps a runaway script from filling memory.'},
 {id:'scripts.maxChanges',l:'Changes a script may ask for in one run',t:'num',d:10000,u:'changes',kind:'lock',w:'script sandbox changes safety',why:'Every change is checked before it is applied; this keeps that check quick.'},
 {id:'scripts.maxCodeKB',l:'Largest script that can run',t:'num',d:256,u:'kB',kind:'lock',w:'script sandbox size safety',why:'Keeps the script sandbox small and quick to start.'}];
const XT_WS={el:null,q:'',f:'all',err:null,rows:null,listening:false};
/* a value with no key of its own: the user's value, or the default */
function xtV(id,def){const o=UI.xtSet;return o&&o[id]!==undefined?o[id]:def}
/* the rows of the list: {id, l, t, d, min, max, step, u, kind: set (in Settings) | glass | none (no control) | else (elsewhere) | lock, ...} */
function xtSetRows(){if(XT_WS.rows&&XT_WS.n===STT.length)return XT_WS.rows;const R=[];
  for(const r of STT){if(r.same)continue;const id=XT_SET_NS[r.id]||'settings.'+r.id;R.push({id,st:r.id,l:r.l,t:r.t,d:r.d,h:r.h||'',w:(r.w||'')+' '+r.b,sc:r.sc,pg:r.pg,kind:r.own?'glass':r.t==='list'?'list':'set'})}
  for(const o of XT_SET_OWN)R.push(Object.assign({sc:'app'},o,{d:o.kind==='lock'?xtSetLockVal(o.id,o.d):o.d}));
  XT_WS.rows=R;XT_WS.n=STT.length;return R}
function xtSetLockVal(id,d){try{if(id==='scripts.maxLogLines')return XT_SBX.MAXLOG;if(id==='scripts.maxChanges')return XT_SBX.MAXCHG;if(id==='scripts.maxCodeKB')return Math.round(XT_SBX.MAXCODE/1024)}catch(e){}return d}
function xtSetRow(id){return xtSetRows().find(r=>r.id===id)||null}
/* the value now: through the Settings control for an STT row, else the key or UI.xtSet */
function xtSetGet(id){const r=xtSetRow(id);if(!r)return undefined;if(r.st)return SETT.val(r.st);if(r.kind==='lock')return r.d;if(r.k){const v=UI[r.k];return v==null?r.d:v}return xtV(id,r.d)}
function xtSetChanged(id){const r=xtSetRow(id);if(!r||r.kind==='lock')return false;if(r.st)return SETT.isDefault(r.st)===false;const v=xtSetGet(id);return v!==undefined&&JSON.stringify(v)!==JSON.stringify(r.d)}
/* set a value; {ok, why}. Checks type and range; a refused value changes nothing */
function xtSetPut(id,v){const r=xtSetRow(id);if(!r)return{ok:false,why:'There is no setting with this id.'};
  if(r.kind==='lock')return{ok:false,why:'This value is locked: '+r.why};
  if(r.kind==='glass'||r.kind==='list')return{ok:false,why:'Change this one in Settings.'};
  if(r.st){if(r.t==='range'||r.t==='number'){const el=SETT.ctl(r.st),n=Number(v);if(String(v).trim()===''||!isFinite(n))return{ok:false,why:'Type a number.'};
     const lo=el&&el.min!==''?+el.min:-Infinity,hi=el&&el.max!==''?+el.max:Infinity;if(n<lo||n>hi)return{ok:false,why:'Between '+lo+' and '+hi+'.'}}
    return SETT.set(r.st,v)?{ok:true}:{ok:false,why:'Settings did not accept this value.'}}
  const n=Number(v);if(String(v).trim()===''||!isFinite(n))return{ok:false,why:'Type a number.'};if(n<r.min||n>r.max)return{ok:false,why:'Between '+r.min+' and '+r.max+' '+r.u+'.'};
  const q=Math.round(n/r.step)*r.step;if(r.k){if(q===r.d)delete UI[r.k];else UI[r.k]=q}
  else{const o=UI.xtSet||{};if(q===r.d)delete o[id];else o[id]=q;if(Object.keys(o).length)UI.xtSet=o;else delete UI.xtSet}
  saveUI();if(r.apply)r.apply();return{ok:true}}
function xtSetReset(id){const r=xtSetRow(id);if(!r||r.kind==='lock'||r.kind==='glass'||r.kind==='list')return false;if(r.st)return SETT.reset(r.st);
  if(r.k)delete UI[r.k];else if(UI.xtSet){delete UI.xtSet[id];if(!Object.keys(UI.xtSet).length)delete UI.xtSet}saveUI();if(r.apply)r.apply();return true}
/* the choices of a select or cards row, from its live control: [[value, text]] */
function xtSetOpts(r){const el=SETT.ctl(r.st);if(!el)return[];if(r.t==='select')return[...el.options].map(o=>[o.value,o.textContent.trim()]);
  if(r.t==='cards')return[...el.querySelectorAll('button')].map(b=>{const k=Object.keys(b.dataset)[0];return k?[b.dataset[k],(b.getAttribute('title')&&b.textContent.trim().length<2?b.getAttribute('title'):b.textContent.trim().replace(/\s+/g,' '))]:null}).filter(Boolean);return[]}
function xtSetShow(r,v){if(v===undefined||v===null)return'';if(r.t==='check')return v?'on':'off';if(r.t==='select'||r.t==='cards'){const o=xtSetOpts(r).find(o=>o[0]===String(v));return o?o[1]:String(v)}
  if(r.u)return(+v).toLocaleString('en-US')+' '+r.u;return String(v)}
/* what the user's settings file would hold: only what differs from the default (9.6 a) */
function xtSetFile(){const mine={},proj={};for(const r of xtSetRows()){if(!xtSetChanged(r.id))continue;(r.sc==='project'?proj:mine)[r.id]=xtSetGet(r.id)}return{mine,proj}}
/* ---------- the Workshop window (DL3: the settings list; DL10 adds the other tabs) ---------- */
function xtWsOpen(q){const z=ZOOM,vw=innerWidth/z,vh=innerHeight/z,W=Math.round(Math.min(900,vw*.8)),H=Math.round(Math.min(640,vh*.78));
  const w=fwin('xtWs','Workshop',{x:Math.round((vw-W)/2),y:Math.round(Math.max(20,(vh-H)/2)),w:W,h:H});
  if(XT_WS.el!==w){XT_WS.el=w;w.classList.add('xtws');w.querySelector('.fwt').title='The Workshop: AudioLab\'s advanced layer. Every setting by its id, including some with no normal control';
    w.querySelector('.fwc').title='Close the Workshop';
    w.querySelector('.fwx').innerHTML='<span class="xtadv" title="An advanced feature: changes here take effect at once. Each one can be put back with ↺">Advanced</span>';
    w.querySelector('.fwb').innerHTML=`<div class="xtwb"><div class="xttabs" role="tablist"><button role="tab" aria-selected="true" class="on" title="Every setting by its id, with its default and range">Settings list</button></div>
      <div class="xtfirst" hidden><b>This is an advanced feature.</b> The list holds every setting of AudioLab by its id: the ones in Settings, a few you can only change here (marked <i class="xttag n">no control</i>), and the locked safety values (<i class="xttag l">locked</i>). A change takes effect at once and is kept like any setting. To undo one, press ↺ on its row: it goes back to AudioLab's default. The filter Changed shows everything you have changed.<button data-xw="seen" title="Hide this note. It does not come back">Got it</button></div>
      <div class="xtbar"><input type="search" class="xtq" placeholder="Search settings by id or words" aria-label="Search settings by id or words" title="Search by id, name or what it does: try meter, undo or ms" spellcheck="false">
       <span class="xtseg" role="group" aria-label="Show"></span></div>
      <div class="xtmain"><div class="xtlist" role="list" aria-label="Settings"></div>
       <div class="xtfile"><div class="xtfh" title="Only what differs from the default is kept, so an update that improves a default reaches you">What is kept</div><pre class="xtpre"></pre></div></div></div>`;
    const qi=w.querySelector('.xtq');qi.addEventListener('input',()=>{XT_WS.q=qi.value;xtWsDraw()});
    w.querySelector('.xtseg').addEventListener('click',e=>{const b=e.target.closest('[data-xf]');if(!b)return;XT_WS.f=b.dataset.xf;xtWsDraw()});
    w.querySelector('[data-xw="seen"]').onclick=()=>{UI.xtWsSeen=1;saveUI();w.querySelector('.xtfirst').hidden=true};
    const L=w.querySelector('.xtlist');
    L.addEventListener('change',e=>{const c=e.target.closest('[data-xs]');if(!c)return;const id=c.dataset.xs,v=c.type==='checkbox'?c.checked:c.value;const res=xtSetPut(id,v);XT_WS.err=res.ok?null:{id,why:res.why};xtWsDraw(id)});
    L.addEventListener('click',e=>{const b=e.target.closest('button[data-xa]');if(!b)return;const id=b.dataset.id;
      if(b.dataset.xa==='reset'){xtSetReset(id);XT_WS.err=null;xtWsDraw()}
      else if(b.dataset.xa==='show'){const r=xtSetRow(id);if(r&&r.st){openSettings(r.pg);setTimeout(()=>{const el=SETT.row(r.st);if(el){el.scrollIntoView({block:'center'});el.classList.add('xtflash');setTimeout(()=>el.classList.remove('xtflash'),1600)}},120)}}});
    if(!XT_WS.listening){XT_WS.listening=true;/* a setting changed in Settings while the Workshop is open: redraw the values (only when it is open) */
      document.addEventListener('change',e=>{const W=XT_WS.el;if(!W||W.hidden||W.contains(e.target))return;if(e.target.closest&&e.target.closest('#set'))setTimeout(()=>xtWsDraw(),0)},true)}}
  xtSetPrime();
  w.querySelector('.xtfirst').hidden=!!UI.xtWsSeen;if(q!=null){XT_WS.q=String(q);w.querySelector('.xtq').value=XT_WS.q}
  xtWsDraw();return w}
/* the Settings window builds and fills its pages when it opens; until it has opened once, its controls do not show the stored values.
   So the first time the Workshop opens in a session, Settings is opened and closed once in the same task (it is never drawn). */
function xtSetPrime(){if(XT_WS.primed)return;XT_WS.primed=true;const st=document.getElementById('set');if(!st||!st.hidden)return;try{openSettings();closeSet()}catch(e){console.warn('AudioLab Workshop: settings',e)}}
function xtWsClose(){if(XT_WS.el)XT_WS.el.hidden=true}
function xtWsVisible(){const all=xtSetRows(),ws=XT_WS.q.trim().toLowerCase().split(/\s+/).filter(Boolean);
  return all.filter(r=>{if(XT_WS.f==='chg'&&!xtSetChanged(r.id))return false;if(XT_WS.f==='none'&&r.kind!=='none'&&r.kind!=='else')return false;if(XT_WS.f==='lock'&&r.kind!=='lock')return false;
    const hay=(r.id+' '+r.l+' '+(r.h||'')+' '+(r.w||'')+' '+(r.where||'')).toLowerCase();return ws.every(x=>hay.includes(x))})}
function xtWsRowHtml(r){const v=xtSetGet(r.id),did='xts-'+r.id.replace(/[^A-Za-z0-9]/g,'-'),lab=esc(r.l),chg=xtSetChanged(r.id);let ed='';
  const tip=esc((r.h||r.l).replace(/\s+/g,' '));
  if(r.kind==='lock')ed=`<span class="xtro" title="${esc(r.why)}">${esc(xtSetShow(r,v))}</span>`;
  else if(r.kind==='list'||r.kind==='glass'||(r.st&&!SETT.ctl(r.st)))ed=`<span class="xtro" title="Change this one in Settings">${r.kind==='list'?'a list':esc(xtSetShow(r,v))}</span>`;
  else if(r.t==='check')ed=`<label class="xtsw" title="${tip}"><input type="checkbox" id="${did}" data-xs="${r.id}" aria-label="${lab}"${v?' checked':''}><i></i></label>`;
  else if(r.t==='select'||r.t==='cards')ed=`<select id="${did}" data-xs="${r.id}" aria-label="${lab}" title="${tip}">${xtSetOpts(r).map(o=>`<option value="${esc(o[0])}"${o[0]===String(v)?' selected':''}>${esc(o[1])}</option>`).join('')}</select>`;
  else if(r.t==='text')ed=`<input type="text" id="${did}" data-xs="${r.id}" aria-label="${lab}" title="${tip}" value="${esc(v==null?'':v)}" spellcheck="false">`;
  else{let lo=r.min,hi=r.max,st=r.step;if(r.st){const el=SETT.ctl(r.st);if(el){lo=el.min;hi=el.max;st=el.step}}
    ed=`<input type="number" id="${did}" data-xs="${r.id}" aria-label="${lab}" title="${tip}" value="${esc(v==null?'':v)}"${lo!==''&&lo!=null?` min="${lo}"`:''}${hi!==''&&hi!=null?` max="${hi}"`:''}${st?` step="${st}"`:''}>${r.u?`<span class="xtu">${esc(r.u)}</span>`:''}`}
  const tags=(r.kind==='none'?'<i class="xttag n" title="There is no control for this anywhere else in AudioLab">no control</i>':'')
    +(r.kind==='else'?`<i class="xttag e" title="Not in Settings. Also set by ${esc(r.where||'')}">elsewhere</i>`:'')
    +(r.kind==='lock'?'<i class="xttag l" title="Locked for safety. Shown so you can see it exists and why">locked</i>':'')
    +(r.kind==='glass'?'<i class="xttag g" title="Part of the glass and performance settings. Change it in Settings">in Settings</i>':'')
    +(r.sc==='project'?'<i class="xttag p" title="Kept in the project file, so it travels with the song">project</i>':r.sc==='session'?'<i class="xttag s" title="Not kept: back to the default when AudioLab starts">not kept</i>':'')
    +(chg?'<i class="xttag c" title="You changed this. ↺ puts it back">changed</i>':'');
  let rng='';if(r.kind!=='lock'&&(r.t==='num'||r.t==='range'||r.t==='number')){let lo=r.min,hi=r.max;if(r.st){const el=SETT.ctl(r.st);if(el){lo=el.min;hi=el.max}}if(lo!==''&&lo!=null&&hi!==''&&hi!=null)rng=' · '+lo+' to '+hi+(r.u?' '+r.u:'')}
  const def=r.d===undefined||r.kind==='list'?'':(r.kind==='lock'?'always ':'default ')+xtSetShow(r,r.d);
  const err=XT_WS.err&&XT_WS.err.id===r.id?`<span class="xterr" role="alert">${esc(XT_WS.err.why)}</span>`:'';
  const acts=(chg&&r.kind!=='glass'&&r.kind!=='list'?`<button data-xa="reset" data-id="${r.id}" title="Back to the default (${esc(xtSetShow(r,r.d))})" aria-label="Reset ${r.id}">↺</button>`:'')
    +(r.st?`<button data-xa="show" data-id="${r.id}" title="Show this setting in the Settings window" aria-label="Show ${r.id} in Settings">↗</button>`:'');
  return`<div class="xtrow${chg?' chg':''}" role="listitem" data-row="${r.id}"><span class="xtid" title="${tip}"><b>${esc(r.id)}</b><small>${lab}${def?' · '+esc(def):''}${esc(rng)}${r.kind==='lock'?' · '+esc(r.why):''}</small></span><span class="xttags">${tags}</span><span class="xted">${ed}</span><span class="xtacts">${acts}</span>${err}</div>`}
function xtWsDraw(focusId){const w=XT_WS.el;if(!w||w.hidden)return;const all=xtSetRows(),L=w.querySelector('.xtlist');
  const nN=all.filter(r=>r.kind==='none'||r.kind==='else').length,nL=all.filter(r=>r.kind==='lock').length,nC=all.filter(r=>xtSetChanged(r.id)).length;
  const F=[['all','All '+all.length,'Every setting'],['chg','Changed '+nC,'Only what you have changed'],['none','Not in Settings '+nN,'Values with no control in the Settings window'],['lock','Locked '+nL,'Safety values nothing can change']];
  w.querySelector('.xtseg').innerHTML=F.map(f=>`<button data-xf="${f[0]}" aria-pressed="${XT_WS.f===f[0]}" title="${f[2]}">${f[1]}</button>`).join('');
  const rows=xtWsVisible();const st=L.scrollTop;
  L.innerHTML=rows.length?rows.map(xtWsRowHtml).join(''):`<div class="xtnone">${XT_WS.f==='chg'&&!XT_WS.q?'Nothing is changed: every setting has AudioLab\'s default.':'Nothing matches. Try meter, undo or ms.'}</div>`;L.scrollTop=st;
  const f=xtSetFile(),J=o=>JSON.stringify(o,null,2);
  w.querySelector('.xtpre').textContent='settings · yours, on this computer\n'+J({audiolab:'settings',version:1,values:f.mine})+'\n\ninside the project file · travels with the song\n'+J({settings:f.proj});
  if(focusId){const el=L.querySelector(`[data-xs="${focusId}"]`);if(el)el.focus()}}
XT_CMD_EXTRA.push({id:'view.workshop',g:'view',l:'Workshop: advanced settings by id',run:()=>xtWsOpen()});
const XT_HOOKS={openWorkshop:q=>xtWsOpen(q),val:xtV};/* for lane B: a link at the foot of Settings may call XT_HOOKS.openWorkshop() (9.6 f) */
