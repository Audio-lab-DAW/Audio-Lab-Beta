// v0.240 (task ST-S4): settings step S4, one settings table in the code. STT (above) has one row per setting in the Settings window:
// id, label, page, block, scope (app, project or session), stored key, control, kind, default (as a fresh profile shows it), help line, search words,
// 'own' (glass: Performance and the Glass block, rebuilt by the glass chain) and 'same' (a second control for the same setting, until S10).
// SETT reads, sets (through the control, so the existing handlers run and nothing is written twice), finds, resets one row to its default,
// marks each row in the window (data-stid, data-stsc: no visible change) and draws a new row from the table (draw: for the new pages of S5).
// No visible change in this step; nothing per frame; the audio path is not touched.
const STS4={v:'0.240'};
const STX=new Map(STT.map(r=>[r.id,r]));
const SETT={
 list:()=>STT,
 get:id=>STX.get(id),
 ctl(id){const r=STX.get(id);if(!r||!r.c)return null;try{return document.querySelector(r.c)}catch(e){return null}},
 row(id){const r=STX.get(id),el=SETT.ctl(id);if(!el)return null;if(r.t==='cards'||r.t==='list')return el;return el.closest('label.chk,.cprow,.pnlrow,.phrow,.zsc,.row,label')||el},
 key(id){const r=STX.get(id);if(!r||!r.k)return undefined;const p=r.k.split('.');let o=p[0]==='S'?S:p[0]==='UI'?UI:null;for(let i=1;o!=null&&i<p.length;i++)o=o[p[i]];return o},
 val(id){const r=STX.get(id),el=SETT.ctl(id);if(!r||!el)return undefined;if(r.t==='check')return el.checked;if(r.t==='cards'){const b=el.querySelector('button.on,[aria-pressed=true]');if(!b)return null;const k=Object.keys(b.dataset)[0];return k?b.dataset[k]:null}if(r.t==='list')return undefined;return el.value},
 isDefault(id){const r=STX.get(id);if(!r||!('d' in r))return null;const v=SETT.val(id);return v===undefined?null:JSON.stringify(v)===JSON.stringify(r.d)},
 set(id,v){const r=STX.get(id),el=SETT.ctl(id);if(!r||!el)return false;
  if(r.t==='check'){if(el.checked!==!!v){el.checked=!!v;el.dispatchEvent(new Event('input',{bubbles:true}));el.dispatchEvent(new Event('change',{bubbles:true}))}return true}
  if(r.t==='cards'){const b=[...el.querySelectorAll('button')].find(b=>{const k=Object.keys(b.dataset)[0];return k&&b.dataset[k]===String(v)});if(!b)return false;b.click();return true}
  if(r.t==='list')return false;
  if(el.tagName==='SELECT'&&![...el.options].some(o=>o.value===String(v)))return false;
  el.value=String(v);el.dispatchEvent(new Event('input',{bubbles:true}));el.dispatchEvent(new Event('change',{bubbles:true}));return true},
 reset(id){const r=STX.get(id);return !!r&&('d' in r)&&!r.own&&SETT.set(id,r.d)},
 find(q){const ws=String(q||'').toLowerCase().split(/\s+/).filter(Boolean);if(!ws.length)return[];return STT.filter(r=>{const t=(r.l+' '+(r.h||'')+' '+(r.w||'')+' '+r.b).toLowerCase();return ws.every(w=>t.includes(w))}).map(r=>r.id)},
 page:pg=>STT.filter(r=>r.pg===pg).map(r=>r.id),
 bind(){let n=0;for(const r of STT){const el=SETT.row(r.id);if(el&&!el.dataset.stid){el.dataset.stid=r.id;el.dataset.stsc=r.sc;n++}}return n},
 draw(id){const r=STX.get(id),live=SETT.ctl(id);if(!r||!live||!['check','select','range','number','text'].includes(r.t))return null;
  const tip=(r.h||r.l).replace(/\s+/g,' ');let el,c;
  if(r.t==='check'){el=document.createElement('label');el.className='chk';c=document.createElement('input');c.type='checkbox';c.checked=live.checked;el.append(c,' '+r.l)}
  else{el=document.createElement('div');el.className='row';const s=document.createElement('span');s.textContent=r.l;
   if(r.t==='select'){c=document.createElement('select');for(const o of live.options){const n=document.createElement('option');n.value=o.value;n.textContent=o.textContent;c.appendChild(n)}}
   else{c=document.createElement('input');c.type=r.t==='range'?'range':r.t==='number'?'number':'text';for(const a of['min','max','step'])if(live.hasAttribute(a))c.setAttribute(a,live.getAttribute(a))}
   c.value=live.value;c.setAttribute('aria-label',r.l);el.append(s,c)}
  el.title=tip;el.dataset.stid=r.id;el.dataset.stsc=r.sc;
  c.addEventListener(r.t==='check'?'change':'input',()=>SETT.set(id,r.t==='check'?c.checked:c.value));
  const back=()=>{if(!el.isConnected){live.removeEventListener('change',back);live.removeEventListener('input',back);return}if(r.t==='check')c.checked=live.checked;else if(document.activeElement!==c)c.value=live.value};
  live.addEventListener('change',back);live.addEventListener('input',back);return el}
};
{const _o4=openSettings;openSettings=function(){const r=_o4.apply(this,arguments);setTimeout(()=>{try{SETT.bind()}catch(e){}},0);return r}
 const nv=document.getElementById('setNav');if(nv)nv.addEventListener('click',()=>setTimeout(()=>{try{SETT.bind()}catch(e){}},0))}
