/* ===== settings step S9 (task ST-S9), v0.278: the help line at the foot of the window =====
   docs/settings-round-1.md (D4c): pointing at a setting, or moving to it with Tab, shows at once (no hover delay) in a line at the foot of
   the Settings window what it does, its default and where it is kept (this song, this computer, a starting value for new projects, or the
   same in every project). Pages do not get longer. Every setting of the settings table that had no help line gets one (ST9H, written into the
   table, so search reads it too), and every other control in the window (buttons, links, read-outs) gets one (ST9C, then TIPS, then its
   title). Tooltips stay as they are. ST_HOOKS.helpFor(element) gives {label, text, def, scope} for lane F's window-wide help line (OV6).
   Nothing runs while Settings is closed; one delegated mouseover and focusin listener, the line is only rewritten when the target changes. */
const STS9={v:'0.278'};
/*HELP*/
const ST9={last:null,
 clean:t=>String(t||'').split('|')[0].replace(/\s+/g,' ').trim(),
 fill(){for(const r of STT){if(!ST9.clean(r.h)&&ST9H[r.id])r.h=ST9H[r.id]}},
 SC:{project:'Kept with this song',computer:'Belongs to this computer',new:'Starting value for new projects'},
 scope(r){let k='';try{k=ST8.kind(r)}catch(e){}if(k&&ST9.SC[k])return ST9.SC[k];if(r.sc==='session')return 'Only until AudioLab closes';if(r.sc==='project')return ST9.SC.project;return 'The same in every project'},
 def(r){if(!('d' in r)||r.t==='list'||r.d===''||r.d==null)return '';try{const t=ST7.vtxt(r,r.d);return t?'Default: '+t:''}catch(e){return ''}},
 tip(el){for(const sel of Object.keys(ST9C)){try{if(el.matches(sel)||(sel[0]!=='['&&el.id===sel)){const v=ST9C[sel],t=typeof v==='function'?v(el):v;if(t)return t}}catch(e){}}
  if(typeof TIPS==='object'){for(const sel of Object.keys(TIPS)){try{if(el.matches(sel)){const p=String(TIPS[sel]).split('|');return(p[1]||p[0]||'').trim()}}catch(e){}}}
  const t=el.getAttribute('title')||el.dataset.tip||'';return ST9.clean(t)},
 name(el){const a=el.getAttribute('aria-label');if(a)return a.trim();const b=el.querySelector&&el.querySelector('b,strong');let t=(b?b.textContent:el.textContent)||'';
  t=t.replace(/[⌘⇧⌥⌃]+\S*/g,'').replace(/\s+/g,' ').trim();if(!t&&el.closest('label'))t=el.closest('label').textContent.replace(/\s+/g,' ').trim();return t.length>40?t.slice(0,39)+'…':t},
 /* what the line says about an element of the Settings window (null: nothing to say) */
 helpFor(el){if(!el||!el.closest)return null;
  const small=el.closest('.st7rs,.st8t');if(small)return{label:'',text:ST9.clean(small.title||small.dataset.tip),def:'',scope:''};
  const row=el.closest('[data-stid]'),r=row&&STX.get(row.dataset.stid);
  if(r){const text=ST9.clean(r.h)||ST9H[r.id]||ST9.tip(el);return{label:r.l,text,def:ST9.def(r),scope:r.own?'':ST9.scope(r)}}
  const c=el.closest('button,input,select,textarea,a,label,[title],[data-tip]');if(!c||!c.closest('#set'))return null;
  const ctl=c.matches('label')?(c.querySelector('input,select')||c):c;
  if(ctl!==c&&ctl.closest('[data-stid]'))return ST9.helpFor(ctl);
  const up=c.parentElement&&c.parentElement.closest('[title]'),text=ST9.tip(ctl)||ST9.tip(c)||(up&&up.closest('#set')?ST9.clean(up.title):'');if(!text)return null;return{label:ST9.name(ctl),text,def:'',scope:''}},
 IDLE:'Changes apply right away. Point at a setting, or move to it with Tab, to read what it does.',
 show(el){const h=document.getElementById('st9Help');if(!h)return;const tgt=el&&el.closest?el.closest('[data-stid],.st7rs,.st8t,button,input,select,textarea,a,label,[title],[data-tip]'):null;
  if(tgt===ST9.last)return;ST9.last=tgt;const x=tgt?ST9.helpFor(tgt):null;
  if(!x||!x.text){if(h.dataset.on){delete h.dataset.on;h.textContent=ST9.IDLE;h.title=''}return}
  h.dataset.on=1;h.textContent='';if(x.label&&!x.text.toLowerCase().startsWith(x.label.toLowerCase())){const b=document.createElement('b');b.textContent=x.label;h.append(b,' ')}
  h.append(x.text);const m=[x.def,x.scope].filter(Boolean).join(' · ');if(m){const s=document.createElement('span');s.className='st9m';s.textContent=m;h.append(' ',s)}
  h.title=h.textContent},
 build(){if(document.getElementById('st9Help'))return;const f=document.querySelector('#set .setsf');if(!f)return;const sp=[...f.children].find(e=>e.tagName==='SPAN'&&/apply right away/.test(e.textContent));
  const h=document.createElement('span');h.id='st9Help';h.className='st9h';h.textContent=ST9.IDLE;if(sp){sp.hidden=true;sp.after(h)}else{const d=document.getElementById('setDone');d?d.before(h):f.appendChild(h)}
  const st=document.getElementById('set');
  st.addEventListener('mouseover',e=>{if(e.target.closest&&e.target.closest('.setsf'))return;ST9.show(e.target)});
  st.addEventListener('mouseleave',()=>ST9.show(null));
  st.addEventListener('focusin',e=>{const t=e.target;ST9.show(t);if(t&&t.matches&&t.matches('input,select,button,textarea')&&!t.getAttribute('aria-describedby'))t.setAttribute('aria-describedby','st9Help')})}};
const ST_HOOKS={helpFor:el=>{try{return ST9.helpFor(el)}catch(e){return null}}};
try{ST9.fill()}catch(e){console.warn('settings help line (ST-S9)',e)}
{const _o9=openSettings;openSettings=function(){const x=_o9.apply(this,arguments);try{ST9.fill();ST9.build();ST9.last=undefined;ST9.show(null)}catch(e){console.warn('settings help line (ST-S9)',e)}return x}}
