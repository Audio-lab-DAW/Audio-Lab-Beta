/* ===================== SAFE MODE, WHAT IS CHANGED, RESET (v0.000, task XT-DL4) =====================
   docs/extensions-plan.md 9.6 g and 9.7 DL4; the user's picks K11 a, b and c. Three doors into safe mode:
   - the logo menu "Restart in safe mode…" (and the command help.safeMode);
   - holding Shift while AudioLab starts (a Shift key or a click with Shift before the first frame): AudioLab asks, then restarts in safe mode;
   - offered by itself when the last start did not reach its first frame (al-xt-start, set by the early half next to where UI is read).
   In safe mode (XT_SAFE.on) every customisation starts at its default (the early half); nothing is deleted. A bar across the top says so,
   with "What is changed" and "Leave safe mode". Safe mode ends when you leave it or quit.
   "What is changed" is a tab of the Workshop: one list across every kind (settings, the Workshop's own values, keyboard shortcuts, the layout of
   the transport bar, track headers, mixer and devices), each entry with its own ✕. "Reset my customisations" asks first, keeps a dated backup
   (the settings backups of Settings › General, ST7), and can be undone from the same tab.
   Cost: with nothing customised and outside safe mode, three listeners until the first frame and two small localStorage writes per start;
   nothing per frame or per key. The tab is built when it opens. */
const XT_SFM={bar:null,tab:'set',offerShown:false,RESET:'al-xt-reset',
 LAY:[['Transport bar layout',['trOrder','trCompact','trHide','trX'],'the order, size and hidden parts of the transport bar',()=>{try{trApply()}catch(e){}try{trMini()}catch(e){}}],
  ['Track controls in the headers',['hcz'],'which controls the track headers show',()=>{try{renderHeaders()}catch(e){}}],
  ['Mixer view options',['mxOpt'],'what the mixer\'s views show',()=>{try{dirty=true}catch(e){}}],
  ['Device panel parts',['fxHide'],'which parts of the device panel are hidden',()=>{try{renderFx()}catch(e){}}]]};
/* ---------- the doors ---------- */
async function xtSafeAsk(why){if(XT_SAFE.on){xtSafeLeave();return}
  const r=await askChoice('Restart in safe mode?',(why?why+' ':'')+'AudioLab restarts as it came: every setting, keyboard shortcut and layout at its default. Nothing is deleted: your changes come back when you leave safe mode or start AudioLab again. Your open projects are kept.',
    [{label:'Cancel',v:null},{label:'Restart in safe mode',v:1,cls:'pri'}]);if(r!==1)return false;xtSafeGo();return true}
/* is this change set aside by safe mode? (Light mode is not: it protects a slow computer) */
function xtSafeAside(c){if(c.kind!=='set')return true;if(c.st){const r=STT.find(r=>r.id===c.st);const k=r&&r.k&&r.k.startsWith('UI.')?r.k.split('.')[1]:null;return!!k&&XT_SAFE.K.includes(k)}
  const o=XT_SET_OWN.find(o=>o.id===c.id);return!o||!o.k||XT_SAFE.K.includes(o.k)}
function xtSafeGo(){/* the list of what is set aside is taken now, while the controls still show it */try{xtSetPrime();sessionStorage.setItem('al-safe-list',JSON.stringify(xtChgList(false).filter(xtSafeAside).map(c=>Object.assign({},c,{x:false,st:null}))))}catch(e){try{sessionStorage.removeItem('al-safe-list')}catch(e2){}}
  try{sessionStorage.setItem('al-safe','1')}catch(e){}try{localStorage.removeItem('al-xt-start')}catch(e){}restartApp()}
async function xtSafeLeave(){const r=await askChoice('Leave safe mode?','AudioLab restarts with your settings, shortcuts and layout as they were. Changes to them made in safe mode are not kept.',
    [{label:'Stay in safe mode',v:null},{label:'Leave safe mode',v:1,cls:'pri'}]);if(r!==1)return false;try{sessionStorage.removeItem('al-safe');sessionStorage.removeItem('al-safe-list')}catch(e){}try{localStorage.removeItem('al-xt-start')}catch(e){}restartApp();return true}
/* the start: Shift held, or the last start did not finish. Listeners live until the first frame (plus 1.5 s for a slow hand), then go */
{const shift=e=>{if(XT_SAFE.on||XT_SAFE.shift)return;if(e.type==='keydown'?e.key==='Shift':e.shiftKey){XT_SAFE.shift=true;setTimeout(()=>xtSafeOffer('shift'),0)}};
 const evs=['keydown','pointerdown','pointermove'],off=()=>{for(const t of evs)removeEventListener(t,shift,true)};
 const ready=()=>{try{localStorage.removeItem('al-xt-start')}catch(e){}setTimeout(off,1500);
   if(XT_SAFE.on)xtSafeBar();else if(XT_SAFE.offer)xtSafeOffer('crash')};
 if(!CHILD){for(const t of evs)addEventListener(t,shift,true);addEventListener('pagehide',()=>{try{localStorage.removeItem('al-xt-start')}catch(e){}});
  const go=()=>requestAnimationFrame(()=>requestAnimationFrame(ready));if(document.readyState==='complete')go();else addEventListener('load',go,{once:true})}}
/* the offer: a small bar, never a dialog in the way of a start that may be broken */
function xtSafeOffer(kind){if(XT_SAFE.on||XT_SFM.offerShown||CHILD)return;XT_SFM.offerShown=true;
  const b=document.createElement('div');b.className='xtsafe offer';b.id='xtSafeOffer';b.setAttribute('role','alertdialog');b.setAttribute('aria-label','Safe mode');
  b.innerHTML=`<i class="xtsfb" title="Safe mode starts AudioLab as it came, without deleting anything">Safe mode?</i><span>${kind==='shift'?'You held Shift while AudioLab started. Restart in safe mode, with every setting, shortcut and layout at its default?':'The last start of AudioLab did not finish. Restart in safe mode, with every setting, shortcut and layout at its default? Nothing is deleted.'}</span>
   <button data-xsf="go" class="pri" title="Restart now in safe mode. Your changes come back when you leave it">Restart in safe mode</button><button data-xsf="no" title="Keep going as you are">${kind==='shift'?'No':'Start normally'}</button>`;
  b.addEventListener('click',e=>{const k=e.target.closest('[data-xsf]');if(!k)return;b.remove();if(k.dataset.xsf==='go')xtSafeGo()});document.body.appendChild(b);return b}
/* the bar of safe mode, across the top; × folds it to its badge */
function xtSafeBar(){if(!XT_SAFE.on||XT_SFM.bar)return XT_SFM.bar;const b=document.createElement('div');b.className='xtsafe';b.id='xtSafeBar';b.setAttribute('role','status');
  const n=xtChgList(true).length;
  b.innerHTML=`<button class="xtsfb" data-xsf="fold" title="Safe mode is on. Click to fold or unfold this bar">Safe mode</button><span class="xtsft">AudioLab started as it came. ${n?n+' customisation'+(n>1?'s are':' is'):'Nothing is'} set aside, not deleted: ${n?'they come':'it all comes'} back when you leave.</span>
   <button data-xsf="chg" title="Show what is changed: every customisation that is set aside now">What is changed</button><button data-xsf="leave" class="pri" title="Restart with your settings, shortcuts and layout">Leave safe mode</button>`;
  b.addEventListener('click',e=>{const k=e.target.closest('[data-xsf]');if(!k)return;const a=k.dataset.xsf;if(a==='fold')b.classList.toggle('fold');else if(a==='chg')xtChgOpen();else if(a==='leave')xtSafeLeave()});
  document.body.appendChild(b);XT_SFM.bar=b;return b}
/* ---------- what is changed: one list across every kind ---------- */
/* [{kind, id, l (what it is), v (now), d (default), x (true: ✕ puts it back here), why}]; stored=true lists what safe mode set aside */
function xtChgList(stored){const out=[],U=stored?(XT_SAFE.stored||{}):UI,same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
  if(stored){try{const a=JSON.parse(sessionStorage.getItem('al-safe-list')||'null');if(Array.isArray(a))return a}catch(e){}}
  if(stored){/* in safe mode the controls show defaults; the stored keys tell what comes back */
    const lab={};try{for(const r of STT)if(r.k&&r.k.startsWith('UI.')){const k=r.k.split('.')[1];lab[k]=lab[k]||r.l}}catch(e){}
    try{for(const o of XT_SET_OWN)if(o.k)lab[o.k]=o.l}catch(e){}
    for(const k of XT_SAFE.K){if(!(k in U)||k==='keys'||k==='xtSet'||XT_SFM.LAY.some(L=>L[1].includes(k)))continue;if(k in XT_UI0&&same(U[k],XT_UI0[k]))continue;
      out.push({kind:'set',id:k,l:lab[k]||k,v:'',d:'',x:false})}
    for(const id of Object.keys(U.xtSet||{}))out.push({kind:'set',id,l:id,v:String(U.xtSet[id]),d:'',x:false})}
  else{for(const r of xtSetRows()){if(r.kind==='list'||!xtSetChanged(r.id))continue;
    out.push({kind:'set',id:r.id,l:r.l,v:xtSetShow(r,xtSetGet(r.id)),d:xtSetShow(r,r.d),x:r.kind!=='glass',st:r.st,pg:r.pg})}}
  for(const id of Object.keys(U.keys||{})){let a=null;try{a=SCA.find(q=>q.id===id)}catch(e){}const c=U.keys[id];if(a&&(c||'')===(a.d||''))continue;
    out.push({kind:'key',id,l:a?a.l:id,v:xtKeyShow(c),d:xtKeyShow(a?a.d:''),x:!stored})}
  for(const[n,ks,what]of XT_SFM.LAY){const has=ks.filter(k=>{const v=U[k];return v!=null&&!(typeof v==='object'&&!Object.keys(v).length)});if(!has.length)continue;
    let v='changed';if(ks.includes('trHide')){const h=Object.keys(U.trHide||{}).filter(k=>U.trHide[k]).length;v=[h?h+' part'+(h>1?'s':'')+' hidden':'',U.trOrder?'order changed':'',U.trCompact&&Object.values(U.trCompact).some(Boolean)?'some parts compact':''].filter(Boolean).join(', ')||'changed'}
    else if(ks.includes('fxHide')){const h=Object.keys(U.fxHide||{}).filter(k=>U.fxHide[k]).length;v=h?h+' part'+(h>1?'s':'')+' hidden':'changed'}
    out.push({kind:'lay',id:ks[0],l:n,v,d:'as it came',x:!stored,why:what})}
  return out}
function xtKeyShow(c){if(!c)return'no key';return String(c).replace(/Mod/g,navigator.platform&&/Mac/.test(navigator.platform)?'⌘':'Ctrl').replace(/\+/g,' + ')}
/* ✕ on one entry: back to the default, at once where the part can redraw */
function xtChgUndo(kind,id){if(kind==='set'){const ok=xtSetReset(id);if(ok)saveUI();return ok}
  if(kind==='key'){if(!UI.keys||!(id in UI.keys))return false;delete UI.keys[id];if(!Object.keys(UI.keys).length)delete UI.keys;saveUI();try{scRender()}catch(e){}return true}
  if(kind==='lay'){const L=XT_SFM.LAY.find(L=>L[1][0]===id);if(!L)return false;for(const k of L[1])delete UI[k];saveUI();L[3]();return true}return false}
/* ---------- reset my customisations, with a backup, and its undo ---------- */
async function xtChgResetAll(){const n=xtChgList(XT_SAFE.on).length;if(!n){toast('Nothing to reset: everything is as it came.');return false}
  const r=await askChoice('Reset my customisations?','All '+n+' customisation'+(n>1?'s':'')+' in this list go back to AudioLab\'s defaults: settings, the Workshop\'s values, keyboard shortcuts and layout. A backup is kept first, so “Bring them back” in this tab undoes it. Your projects are not touched. AudioLab restarts.',
    [{label:'Cancel',v:null},{label:'Reset my customisations',v:1,cls:'dng pri'}]);if(r!==1)return false;
  let b=null;try{b=ST7.backup('before Reset my customisations')}catch(e){}
  if(!b){const r2=await askChoice('The backup could not be saved','This browser has no room left for it, so the reset could not be undone. Reset anyway?',[{label:'Cancel',v:null},{label:'Reset without a backup',v:1,cls:'dng'}]);if(r2!==1)return false}
  try{if(b)localStorage.setItem(XT_SFM.RESET,String(b.at));else localStorage.removeItem(XT_SFM.RESET)}catch(e){}
  if(XT_SAFE.on){XT_SAFE.drop=true;try{sessionStorage.removeItem('al-safe')}catch(e){}}
  for(const k of XT_SAFE.K)delete UI[k];saveUINow();restartApp();return true}
function xtChgBackup(){let at=null;try{at=+localStorage.getItem(XT_SFM.RESET)}catch(e){}if(!at)return null;let a=[];try{a=ST7.backups()}catch(e){}return a.find(b=>b.at===at)||null}
async function xtChgBringBack(){const b=xtChgBackup();if(!b)return false;
  const r=await askChoice('Bring your customisations back?','Your settings, shortcuts and layout go back to how they were before the reset of '+ST7.when(b)+'. AudioLab restarts.',[{label:'Cancel',v:null},{label:'Bring them back',v:1,cls:'pri'}]);if(r!==1)return false;
  if(XT_SAFE.on){XT_SAFE.drop=true;try{sessionStorage.removeItem('al-safe')}catch(e){}}
  for(const k of XT_SAFE.K){if(k in b.UI)UI[k]=JSON.parse(JSON.stringify(b.UI[k]));else delete UI[k]}try{localStorage.removeItem(XT_SFM.RESET)}catch(e){}saveUINow();restartApp();return true}
/* ---------- the tab in the Workshop ---------- */
function xtChgOpen(){const w=xtWsOpen();xtChgTab('chg');return w}
function xtChgTab(t){const w=XT_WS.el;if(!w)return;XT_SFM.tab=t;const wb=w.querySelector('.xtwb');xtChgMount();wb.classList.toggle('xtchgon',t==='chg');
  for(const b of w.querySelectorAll('.xttabs [data-xt]')){const on=b.dataset.xt===t;b.classList.toggle('on',on);b.setAttribute('aria-selected',on)}if(t==='chg')xtChgDraw();else xtWsDraw()}
function xtChgMount(){const w=XT_WS.el;if(!w||w.querySelector('.xtchg'))return;const tabs=w.querySelector('.xttabs'),first=tabs.querySelector('button');first.dataset.xt='set';
  first.addEventListener('click',()=>xtChgTab('set'));
  const b=document.createElement('button');b.setAttribute('role','tab');b.setAttribute('aria-selected','false');b.dataset.xt='chg';b.textContent='What is changed';
  b.title='Everything you have changed from AudioLab\'s defaults, of every kind, each with its own ✕; safe mode; reset with a backup';b.addEventListener('click',()=>xtChgTab('chg'));tabs.appendChild(b);
  const p=document.createElement('div');p.className='xtchg';p.setAttribute('role','tabpanel');p.setAttribute('aria-label','What is changed');w.querySelector('.xtwb').appendChild(p);
  p.addEventListener('click',e=>{const k=e.target.closest('button[data-xc]');if(!k)return;const a=k.dataset.xc;
    if(a==='x'){xtChgUndo(k.dataset.kind,k.dataset.id);xtChgDraw()}else if(a==='show'){openSettings(k.dataset.pg)}else if(a==='safe')xtSafeAsk();else if(a==='leave')xtSafeLeave();
    else if(a==='reset')xtChgResetAll();else if(a==='back')xtChgBringBack()})}
function xtChgDraw(){const w=XT_WS.el;if(!w||w.hidden)return;const p=w.querySelector('.xtchg');if(!p)return;xtSetPrime();const safe=XT_SAFE.on,L=xtChgList(safe),bk=xtChgBackup();
  const K={set:'Settings',key:'Keyboard shortcuts',lay:'Layout'},rows=['set','key','lay'].map(kind=>{const g=L.filter(c=>c.kind===kind);if(!g.length)return'';
    return`<div class="xtcg">${K[kind]} <span>${g.length}</span></div>`+g.map(c=>`<div class="xtcr" role="listitem"><span class="xtid"><b>${esc(c.l)}</b><small>${c.kind==='set'&&!safe?esc(c.id)+' · ':''}${c.v?esc(c.v):''}${c.d?esc((c.v?', ':'')+'default '+c.d):''}${c.why?esc(' · '+c.why):''}</small></span>
      <span class="xtacts">${c.x?`<button data-xc="x" data-kind="${c.kind}" data-id="${esc(c.id)}" title="Put ${esc(c.l)} back to the default" aria-label="Put ${esc(c.l)} back to the default">✕</button>`:''}${!c.x&&c.st&&!safe?`<button data-xc="show" data-pg="${esc(c.pg||'')}" title="Change this one in Settings" aria-label="Show ${esc(c.l)} in Settings">↗</button>`:''}</span></div>`).join('')}).join('');
  p.innerHTML=`<div class="xtcbar">${safe?'<i class="xtsfb">Safe mode</i><span>AudioLab started as it came. What is listed here is set aside, not deleted: it all comes back when you leave safe mode.</span><button data-xc="leave" class="pri" title="Restart with your settings, shortcuts and layout">Leave safe mode</button>'
      :'<span>Everything that differs from how AudioLab came. ✕ puts one back. Safe mode starts AudioLab as it came, without deleting anything; you can also hold Shift while it starts.</span><button data-xc="safe" title="Restart AudioLab as it came. Nothing is deleted: your changes come back when you leave safe mode">Restart in safe mode…</button>'}</div>
    ${bk?`<div class="xtcbk">Your customisations were reset on ${esc(ST7.when(bk))}. <button data-xc="back" title="Undo the reset: your settings, shortcuts and layout as they were before it">Bring them back</button></div>`:''}
    <div class="xtcl" role="list" aria-label="What is changed">${rows||`<div class="xtnone">Nothing is changed: AudioLab is as it came.</div>`}</div>
    <div class="xtcfoot"><span>${L.length} customisation${L.length===1?'':'s'}. Projects are never part of this list.</span><button data-xc="reset" class="dng" title="Every customisation in this list back to the default, after a backup that “Bring them back” restores"${L.length?'':' disabled'}>Reset my customisations…</button></div>`}
/* keep the tab in step when a value changes in the list or in Settings */
{const _d=xtWsDraw;xtWsDraw=function(){if(XT_SFM.tab==='chg'&&XT_WS.el&&XT_WS.el.querySelector('.xtchg'))return xtChgDraw();return _d.apply(this,arguments)}}
XT_CMD_EXTRA.push({id:'help.safeMode',g:'help',l:'Restart in safe mode (or leave it)',run:()=>xtSafeAsk()},{id:'view.whatIsChanged',g:'view',l:'What is changed: every customisation, with reset',run:()=>xtChgOpen()});
XT_HOOKS.safeMode=()=>XT_SAFE.on;XT_HOOKS.whatIsChanged=()=>xtChgOpen();
