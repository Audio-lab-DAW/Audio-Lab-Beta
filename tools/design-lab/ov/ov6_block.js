/* task OV6a (lane F, overlays, pick T3): tooltips become callouts with a leader. The card hangs from the control by an amber
   hairline with a dot, like a callout on a technical drawing: the name in small mono capitals with its key on the right, the value
   now as a read-out with its unit in amber, the sentence, DEFAULT and SCOPE (Settings rows, through lane B's ST_HOOKS.helpFor), and
   the small picture when there is one. Times are LOOK entries (ovMs): 500 ms before the first, then at once for 300 ms after one
   closed (warm); 80 ms fade, none with reduced motion, Motion "Signal only" or Light mode. It stays while the pointer is on it or
   on the way to it, so it can be read; Esc hides it (the key still reaches whatever else uses it); keyboard focus (Tab, arrows)
   shows it too, linked by aria-describedby. Same texts as before (TIPS, title, data-tip), same switch (Settings, tooltips off),
   tipShow and tipHide keep their names for every caller. */
var OV_T3={rt:new WeakMap(),src:null,kb:false,vis:false,ptr:false,warm:0,dis:null,ld:null,desc:null,br:null,cmd:null,cn:-1,key:{k:'',t:0}};
function ovT3In(t){return!!(t&&t.nodeType===1&&t.closest&&t.closest('#tip,#ovLead'))}
function ovT3Delay(){return performance.now()<OV_T3.warm?0:ovMs('tipDelay')}
/* the shortcut of a control: the command whose run() clicks this element's id (so a key the user changed shows as changed) */
function ovT3Cmd(el){const P=OV_T3;if(!el||!el.id||typeof SCA==='undefined')return null;
  if(!P.cmd||P.cn!==SCA.length){P.cmd=new Map();P.cn=SCA.length;for(const a of SCA){let s='';try{s=String(a.run)}catch(e){}const m=s.match(/\$\(['"]#([\w-]+)['"]\)\.click\(\)/);if(m&&!P.cmd.has(m[1]))P.cmd.set(m[1],a)}}
  return P.cmd.get(el.id)||(el.id==='bPlay'?SCA.find(a=>a.id==='play')||null:null)}
const OV_T3K=/^(?:[⌘⇧⌥⌃]{1,3}\S{1,9}|[A-Z0-9?\/]|Space|Home|End|Esc|Tab|Enter|Return|Delete|Backspace|F\d{1,2}|(?:Shift|Ctrl|Cmd|Alt|Option|Mod)\+\S{1,9})$/;
/* the control's own short name: aria-label, a menu row's label, or its text (empty when long or missing) */
function ovT3Lab(el){if(!el||!el.getAttribute)return'';let t=el.getAttribute('aria-label')||'';
  if(!t){const l=el.querySelector&&el.querySelector('.mlab');t=l?(l.firstChild&&l.firstChild.nodeType===3?l.firstChild.textContent:l.textContent):(el.children.length<3?el.textContent:'')}
  t=String(t||'').replace(/[⌘⇧⌥⌃]+\S*/g,'').replace(/\s+/g,' ').trim();return t.length>1&&t.length<=34?t:''}
function ovT3Parse(el,raw){const p=String(raw).split('|'),ti=(p[0]||'').trim(),de=(p[1]||'').trim();let nm='',tx='',key='';
  if(de){nm=ti;tx=de}
  else{const m=ti.match(/^(.+?)\.\s+(?=\S)/),c=ti.match(/^([^.:]{2,24}):\s+(?=\S)/),fs=m?m[1]:ti.replace(/\.$/,''),w=fs.replace(/\([^()]*\)/g,'').trim().split(/\s+/).length;
    if(fs.length<=34&&w<=5&&!/^(Double-click|Click|Right-click|Drag|Hold|Press|Scroll|Shift|Tap)\b/.test(fs)){nm=fs;tx=m?ti.slice(m[0].length):''}
    else if(c&&c[1].trim().split(/\s+/).length<=3&&ti.length-c[0].length>20){nm=c[1].trim();tx=ti.slice(c[0].length);tx=tx[0].toUpperCase()+tx.slice(1)}
    else{nm=ovT3Lab(el);tx=ti}}
  const k=nm.match(/\s*\(([^()]{1,16})\)/);if(k&&OV_T3K.test(k[1].trim())){key=k[1].trim();nm=(nm.slice(0,k.index)+nm.slice(k.index+k[0].length)).trim()}
  const a=ovT3Cmd(el);if(a){const b=typeof scBind==='function'?scBind(a):a.d;key=b?ovKeyTx(b):''}
  let df='',sc='';if(el.closest&&el.closest('#set')&&typeof ST_HOOKS==='object'&&ST_HOOKS.helpFor){const h=ST_HOOKS.helpFor(el);if(h){df=String(h.def||'').replace(/^Default:\s*/i,'');sc=h.scope||'';if(!nm&&h.label)nm=h.label}}
  return{nm,tx,key,df,sc,vi:p[2]||'',v:ovT3Val(el)}}
/* the value now, as a read-out: one control (the element or the only control inside it) */
function ovT3Val(el){if(!el||!el.matches)return null;const S='input[type=range],input[type=number],input[type=checkbox],select,[role=slider],[role=switch],[aria-valuetext],[aria-pressed]';let c=null;
  if(el.matches(S))c=el;else{const L=el.querySelectorAll(S);if(L.length===1)c=L[0]}if(!c)return null;let t='';
  if(c.matches('select')){const o=c.selectedOptions&&c.selectedOptions[0];t=o?o.textContent.trim():''}
  else if(c.matches('input[type=checkbox],[role=switch]'))t=(c.checked||c.getAttribute('aria-checked')==='true')?'ON':'OFF';
  else if(c.hasAttribute('aria-valuetext'))t=c.getAttribute('aria-valuetext');
  else if(c.matches('input'))t=String(c.value)+(c.dataset.unit?' '+c.dataset.unit:'');
  else if(c.hasAttribute('aria-valuenow'))t=c.getAttribute('aria-valuenow');
  else if(c.hasAttribute('aria-pressed'))t=c.getAttribute('aria-pressed')==='true'?'ON':'OFF';
  t=String(t||'').replace(/\s+/g,' ').trim();if(!t)return null;const m=t.match(/^([-+−]?\d[\d.,:]*)\s*([A-Za-z%°µ][\w%/·]{0,5})?$/);
  return m?{n:m[1],u:m[2]||''}:{n:t.length>24?t.slice(0,23)+'…':t,u:''}}
function ovT3Show(el){const raw=tipText(el)||OV_T3.rt.get(el);if(!raw||UI.tips===false||(typeof TUT!=='undefined'&&TUT.on))return;const P=OV_T3,d=ovT3Parse(el,raw);
  if(!TIPEL){TIPEL=document.createElement('div');TIPEL.id='tip';TIPEL.setAttribute('role','tooltip');document.body.appendChild(TIPEL)}
  if(!P.ld){P.ld=document.createElement('div');P.ld.id='ovLead';P.ld.setAttribute('aria-hidden','true');P.ld.hidden=true;document.body.appendChild(P.ld)}
  const vh=d.v?`<div class="ovtv">${esc(d.v.n)}${d.v.u?`<u>${esc(d.v.u)}</u>`:''}</div>`:'',dh=(d.df||d.sc)?`<div class="ovtd">${d.df?'DEFAULT '+esc(d.df):''}${d.df&&d.sc?' · ':''}${esc(d.sc)}</div>`:'';
  TIPEL.innerHTML=(d.nm||d.key?`<div class="ovtn"><span>${esc(d.nm)}</span>${d.key?`<kbd>${esc(d.key)}</kbd>`:''}</div>`:'')+vh+(d.tx?`<span class="ovtx">${esc(d.tx)}</span>`:'')+dh+(d.vi&&TV[d.vi]?`<div class="tv">${TV[d.vi]}</div>`:'');
  const mine=el===P.src;P.ptr=mine&&!P.kb;TIPEL.className='on ovt3'+(P.ptr?' hov':'')+(ovStill()||document.body.classList.contains('lite')?' still':'');
  const r=el.getBoundingClientRect(),z=ZOOM||1,tw=TIPEL.offsetWidth,th=TIPEL.offsetHeight,W=innerWidth/z,H=innerHeight/z,g=18,cx=(r.left+r.width/2)/z,L=P.ld,
    still=TIPEL.classList.contains('still'),menu=el.closest&&el.closest('#ctxm');let x,y,lead=true,cls='';
  if(menu){/* a menu row: the card stands beside the menu, so it never covers the rows below; the leader runs sideways */
    const mr=menu.getBoundingClientRect();x=mr.right/z+g;let lf=false;if(x+tw>W-6){x=mr.left/z-tw-g;lf=true}x=clamp(x,6,W-tw-6);
    const cy=(r.top+r.height/2)/z;y=clamp(cy-12,6,H-th-6);const ly=clamp(cy,y+5,y+th-5),a=lf?x+tw:mr.right/z+1,b=lf?mr.left/z-1:x;
    if(b-a>3){L.style.left=a+'px';L.style.top=ly+'px';L.style.width=(b-a)+'px';L.style.height='0px';cls='side'+(lf?' lf':'')}else lead=false}
  else{y=r.bottom/z+g;let up=false;if(y+th>H-6){y=r.top/z-th-g;up=true}if(y<6){y=6;lead=false}
    x=clamp(cx-tw/2,6,W-tw-6);const lx=clamp(cx,x+6,x+tw-6),t0=up?y+th:r.bottom/z+2,t1=up?r.top/z-2:y;
    if(lead&&t1-t0>3&&r.width>0){L.style.left=lx+'px';L.style.top=t0+'px';L.style.height=(t1-t0)+'px';L.style.width='';cls=up?'up':''}else lead=false}
  TIPEL.style.left=x+'px';TIPEL.style.top=y+'px';
  if(lead){L.className=cls+(still?' still':'');L.hidden=false;try{const zi=parseInt(getComputedStyle(TIPEL).zIndex,10);if(zi)L.style.zIndex=String(zi-1)}catch(e){}}else L.hidden=true;
  P.vis=true;if(mine){const db=(el.getAttribute('aria-describedby')||'').split(/\s+/).filter(Boolean);if(!db.includes('tip')){db.push('tip');el.setAttribute('aria-describedby',db.join(' '));P.desc=el}}
  if(P.ptr){const tr=TIPEL.getBoundingClientRect();P.br=menu?(tr.left>=r.left?{x0:menu.getBoundingClientRect().right-8,x1:tr.left+2,y0:Math.min(r.top,tr.top),y1:Math.max(r.bottom,tr.bottom)}:{x0:tr.right-2,x1:menu.getBoundingClientRect().left+8,y0:Math.min(r.top,tr.top),y1:Math.max(r.bottom,tr.bottom)}):{x0:tr.left-8,x1:tr.right+8,y0:r.bottom-2,y1:tr.top+2};if(!menu&&tr.bottom<r.top)P.br={x0:tr.left-8,x1:tr.right+8,y0:tr.bottom-2,y1:r.top+2};document.addEventListener('pointermove',ovT3Move,{capture:true,passive:true})}}
/* called by tipHide: the card is gone, the next one within 300 ms shows at once */
function ovT3Off(){let P;try{P=OV_T3}catch(e){return}if(!P)return;if(P.vis){P.vis=false;P.warm=performance.now()+ovMs('tipWarm')}P.ptr=false;P.br=null;P.src=null;P.kb=false;
  if(P.ld)P.ld.hidden=true;document.removeEventListener('pointermove',ovT3Move,{capture:true});
  if(P.desc){const e=P.desc,db=(e.getAttribute('aria-describedby')||'').split(/\s+/).filter(x=>x&&x!=='tip');if(db.length)e.setAttribute('aria-describedby',db.join(' '));else e.removeAttribute('aria-describedby');P.desc=null}}
/* the control a tooltip belongs to; a Settings row without a tooltip of its own reads its line from the settings table (lane B's
   ST_HOOKS.helpFor), kept aside here (no attribute written into lane B's rows) */
function ovT3Tgt(t){let el=null;try{el=tipTarget(t)}catch(e){}const row=t&&t.closest&&t.closest('#set [data-stid]');
  if(row&&(!el||el.contains(row))&&typeof ST_HOOKS==='object'&&ST_HOOKS.helpFor){if(el===row)return el;const h=ST_HOOKS.helpFor(row);if(h&&h.text){OV_T3.rt.set(row,(h.label||'')+'|'+h.text);return row}}
  return el}
function ovT3Start(t,kb){const P=OV_T3,el=ovT3Tgt(t);if(!el)return;if(el===P.dis)return;P.dis=null;tipText(el);tipFor=el;P.src=el;P.kb=!!kb;tipT=setTimeout(()=>{if(tipFor===el)tipShow(el)},ovT3Delay())}
function ovT3Br(e){const b=OV_T3.br;return!!b&&e.clientX>=Math.min(b.x0,b.x1)&&e.clientX<=Math.max(b.x0,b.x1)&&e.clientY>=Math.min(b.y0,b.y1)&&e.clientY<=Math.max(b.y0,b.y1)}
function ovT3Move(e){const P=OV_T3;if(!P.vis||!P.ptr)return;const t=e.target;if(ovT3In(t)||(tipFor&&tipFor.contains(t))||ovT3Br(e))return;tipHide();if(e.pointerType!=='touch')ovT3Start(t)}
function ovT3Over(e){const P=OV_T3,t=e.target;if(P.vis&&P.ptr)return;if(ovT3In(t))return;const el=ovT3Tgt(t);if(el&&el===tipFor)return;if(el!==P.dis)P.dis=null;tipHide();if(el)ovT3Start(t)}
function ovT3Out(e){const P=OV_T3;if(!e.relatedTarget){if(P.dis&&!P.vis)P.dis=null;tipHide();return}if(P.vis&&P.ptr)return;if(tipFor&&!tipFor.contains(e.relatedTarget)&&!ovT3In(e.relatedTarget))tipHide()}
document.addEventListener('keydown',e=>{const P=OV_T3;P.key={k:e.key,t:performance.now()};if(e.key==='Escape'&&(P.vis||tipFor)){P.dis=tipFor;tipHide()}},true);
document.addEventListener('focusin',e=>{const P=OV_T3,t=e.target;if(!t||t.nodeType!==1||t===document.body)return;
  if(performance.now()-P.key.t>400||!/^(Tab|ArrowUp|ArrowDown|ArrowLeft|ArrowRight|Home|End)$/.test(P.key.k))return;
  if(t.matches('input:not([type=range]):not([type=checkbox]):not([type=radio]):not([type=button]),textarea,[contenteditable=""],[contenteditable=true]'))return;
  const el=ovT3Tgt(t);if(!el||el===tipFor)return;tipHide();P.dis=null;ovT3Start(t,true)},true);
document.addEventListener('focusout',e=>{const P=OV_T3;if(P.kb&&tipFor&&!(e.relatedTarget&&tipFor.contains(e.relatedTarget)))tipHide()},true);
