#!/usr/bin/env python3
"""Task OV2a (lane F, overlays; docs/design-round-5-overlays.md section 5, step OV2, part a): the openMenu rewrite to the picked R2.
   python3 tools/design-lab/ov/ov2a.py index.html
The user's pick R2 (command row on top), from tools/design-lab/dr5/overlays.html (.m-r2):
  - entries with crow:'<icon>' go to a row of icon buttons at the top (under the head), each with a short label; the colours sit under it;
    the rest is today's list with key chips; R2 hides the description lines (they show as the app's tooltip card instead, data-tip);
  - group heads {g:'Name'} draw as a hairline (R2 has no group labels), {g:'Advanced',adv:1} as the amber label of K12 (OV3);
  - one level of submenus: an entry with kids:[...] shows a chevron and opens in place (drill-in, '< Back' row on top): a flyout would put
    glass on glass, which the glass engine's layer rule forbids (glass plan 3.10); the menu keeps its width;
  - the APG keyboard: Up/Down by row (the command row, colours and chips count as one row each), Left/Right inside a row, Home/End,
    type-ahead (600 ms), Right/Enter opens a submenu, Left/Esc goes back, Esc closes, Tab closes, Enter/Space run; Shift+F10 and the
    Menu key open the menu of the focused element; focus returns to the trigger when the menu was opened or closed from the keyboard;
  - role menuitemcheckbox with aria-checked for check entries, aria-haspopup/aria-expanded on submenu entries.
Regrouped here: the track menu (Rename, Duplicate, Mute, Solo, Delete on the row; routing as one submenu 'Groups, returns and sends')
and the clip menu (Rename, Duplicate, Split, Mute, Delete on the row; envelopes and the warp markers as submenus). Part b: the tab,
logo, mixer and other long menus. Also fixed: in Light mode (every element has a 0.01 ms transition there) the menu read its previous place while measuring and opened
in the wrong spot (noted in OV1); the measuring place is now set before the menu is shown. Every anchor is asserted. Re-run on a fresh file after a rebase."""
import sys
F = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
s = open(F, encoding='utf-8').read()
assert 'task OV2a' not in s, 'already applied'
assert 'task OV1' in s, 'needs OV1'

def rep(old, new, n=1):
    global s
    c = s.count(old)
    assert c == n, (c, n, old[:120])
    s = s.replace(old, new)

# ---------------------------------------------------------------- openMenu: the renderer moves to ovMenuHTML (same markup per row)
OLD_OPEN = """function openMenu(cx,cy,items){
  MENU=items;ctxm.classList.remove('mcols','mxvm','mxvo');
  ctxm.innerHTML=items.map((it,i)=>it==='-'?'<hr>':it.head?`<div class="mh">${esc(it.head)}</div>`:it.chips?`<div class="mchips">${it.chips.map((c,j)=>`<button data-ci="${i}:${j}" class="${c.on?'on':''}${c.tog?' tog':''}"${c.dis?' disabled':''} title="${esc(c.tip||c.label)}">${c.ic||''}<span>${esc(c.label)}</span></button>`).join('')}</div>`:it.swatches?`<div class="sws">${PAL.map(c=>`<button data-sw="${c}" style="--c:${c}"${c===it.cur?' class="on"':''} aria-label="Colour"></button>`).join('')}</div>`:
    `<button data-i="${i}" role="menuitem"${it.danger?' class="dng"':''}${it.dis?' disabled':''}>${it.sw&&!it.ic?`<i class="swt${it.check?' on':''}"></i>`:it.ic?`<i class="mic">${it.ic}</i>`:it.check!==undefined?`<i class="ck${it.check?' on':''}" style="--c:${it.dot||'#ddd'}"></i>`:it.dot?`<i style="background:${it.dot}"></i>`:'<i></i>'}<span class="mlab">${esc(it.label)}${it.sub?`<small class="msub">${esc(it.sub)}</small>`:''}</span>${it.sw&&it.ic?`<i class="swt${it.check?' on':''}" style="margin-left:auto"></i>`:''}${it.key?`<kbd>${it.key}</kbd>`:''}</button>`).join('');
  ctxm.hidden=false;"""
NEW_OPEN = """function openMenu(cx,cy,items){
  OVM.trig=ovMTrig();OVM.stack=[];OVM.ret=false;ctxm.style.minWidth='';
  MENU=items;ctxm.classList.remove('mcols','mxvm','mxvo');
  ctxm.innerHTML=ovMenuHTML(items);queueMicrotask(ovMTips);
  ctxm.style.left='100px';ctxm.style.top='100px';
  ctxm.hidden=false;"""
rep(OLD_OPEN, NEW_OPEN)
OLD_FOCUS = """  const fb=ctxm.querySelector('button[data-i]:not(:disabled)');if(fb)fb.focus({preventScroll:true});
}
const closeMenu=()=>{ctxm.hidden=true;ctxm.classList.remove('mcols','dropup')};"""
NEW_FOCUS = """  const fb=ovMFirst();if(fb)fb.focus({preventScroll:true});
}
const closeMenu=()=>{ctxm.hidden=true;ctxm.classList.remove('mcols','dropup');ovMClosed()};"""
rep(OLD_FOCUS, NEW_FOCUS)

# ---------------------------------------------------------------- the track menu: the command row and the routing submenu
rep("{label:'Rename…',act:()=>renameTrack(t)}", "{label:'Rename…',crow:'ren',crowL:'Rename',act:()=>renameTrack(t)}")
rep("{label:t.mute?'Unmute track':'Mute track',act:", "{label:t.mute?'Unmute track':'Mute track',crow:'mute',crowL:t.mute?'Unmute':'Mute',on:!!t.mute,act:")
rep("{label:t.solo?'Unsolo track':'Solo track',act:", "{label:t.solo?'Unsolo track':'Solo track',crow:'solo',crowL:t.solo?'Unsolo':'Solo',on:!!t.solo,act:")
rep("{label:'Duplicate track',act:()=>dupTrack(t)}", "{label:'Duplicate track',crow:'dup',crowL:'Duplicate',act:()=>dupTrack(t)}")
rep("{label:'Delete track',danger:1,act:()=>delTrack(t)}", "{label:'Delete track',danger:1,crow:'del',crowL:'Delete',act:()=>delTrack(t)}")
rep("...routeItems(t)", "...ovRouteSub(routeItems(t))")
# ---------------------------------------------------------------- the clip menu
rep("{label:'Rename…',act:()=>renameClip(c)}", "{label:'Rename…',crow:'ren',crowL:'Rename',act:()=>renameClip(c)}")
rep("{label:'Duplicate',key:'⌘D',act:()=>{pushUndo();dupClip(t,c);changed(false)}}", "{label:'Duplicate',key:'⌘D',crow:'dup',crowL:'Duplicate',act:()=>{pushUndo();dupClip(t,c);changed(false)}}")
rep("{label:'Split at playhead',key:'⌥-click',dis:!inPos,", "{label:'Split at playhead',key:'⌥-click',crow:'split',crowL:'Split',dis:!inPos,")
rep("{label:c.mute?'Unmute clip':'Mute clip',act:", "{label:c.mute?'Unmute clip':'Mute clip',crow:'mute',crowL:c.mute?'Unmute':'Mute',on:!!c.mute,act:")
rep("{label:'Delete clip',key:'⌫',danger:1,act:", "{label:'Delete clip',key:'⌫',danger:1,crow:'del',crowL:'Delete',act:")
rep("...envItems(c)", "...ovEnvSub(envItems(c))")
rep("...(c.notes?[]:[{label:c.warp", "...(c.notes?[]:ovWarpSub([{label:c.warp")
rep(":[])])];\n  const tail=", ":[])]))];\n  const tail=")

# ---------------------------------------------------------------- CSS (before .dacv)
CSS = r"""/* task OV2a (lane F, overlays, pick R2): the right-click menu's command row, key chips, submenu entries, the Advanced label.
   The description lines are hidden in R2 (they show in the tooltip card, data-tip), except in the big view menus (mxvm, mxvo, mcols). */
#ctxm .ovcrow{display:flex;gap:2px;padding:2px 2px 4px;margin:0 0 3px;border-bottom:1px solid var(--ov-ln);flex:none}
#ctxm .ovcrow button{flex:1 1 0;min-width:46px;flex-direction:column;gap:3px;align-items:center;justify-content:center;padding:6px 3px 5px;min-height:46px;border-radius:var(--ov-r-item);font-size:10.5px;line-height:1.1;color:var(--ov-mut);text-align:center}
#ctxm .ovcrow button span{flex:none;white-space:nowrap}
#ctxm .ovcrow svg{width:16px;height:16px;flex:none;color:#e6e7ee}
#ctxm .ovcrow button.on svg{color:var(--blf,#4c8dff)}#ctxm .ovcrow button.on span{color:#cfe0ff}
#ctxm .ovcrow button.dng svg{color:#ff8a8a}
#ctxm .ovcrow button:hover:not(:disabled),#ctxm .ovcrow button:focus-visible{color:#fff}
#ctxm .ovcrow button:hover:not(:disabled) svg,#ctxm .ovcrow button:focus-visible svg,#ctxm .ovcrow button:hover:not(:disabled) span{color:#fff}
#ctxm:not(.mxvm):not(.mxvo):not(.mcols) .msub{display:none}
#ctxm kbd{font:500 10.5px var(--ffu,inherit);background:rgba(255,255,255,.07);border-radius:5px;padding:1px 6px;color:rgba(255,255,255,.55);flex:none}
#ctxm button:hover:not(:disabled) kbd,#ctxm button:focus-visible kbd{background:rgba(255,255,255,.2);color:#fff}
#ctxm .ovchev{margin-left:auto;padding-left:10px;color:rgba(255,255,255,.45);font-size:14px;line-height:1;flex:none}
#ctxm button:hover .ovchev,#ctxm button:focus-visible .ovchev{color:#fff}
#ctxm .ovback{color:rgba(255,255,255,.72)}#ctxm .ovback .ovchev{margin:0 2px 0 0;padding:0}
#ctxm .ovgl{font:var(--ov-lab);letter-spacing:var(--ov-labsp);text-transform:uppercase;color:var(--ov-amb);padding:6px 10px 2px;display:flex;align-items:center;gap:8px}
#ctxm .ovgl::after{content:"";flex:1;border-top:1px solid var(--ov-ln)}
body.lite #ctxm .ovcrow svg{color:#e6e7ee}
"""
rep('.dacv{display:flex;', CSS + '.dacv{display:flex;')

# ---------------------------------------------------------------- JS (before askChoice)
JS = r"""/* task OV2a (lane F, overlays, pick R2): the right-click menu engine. openMenu(x,y,items) keeps its item format; new keys:
   crow:'ren'|'dup'|'mute'|'solo'|'del'|'split'|'copy'|'cut'|'paste'|'save'|'open'|'undo'|'set' (icon on the command row; crowL its short
   label, on: shown as on), {g:'Name'} a group (a hairline; adv:1 the amber Advanced label), kids:[...] a submenu (one level).
   OVM: the open menu's trigger (focus returns to it), the submenu stack, ret (return focus on close). */
const OVM={trig:null,stack:[],ret:false,kbd:null,kcm:0,ta:'',taT:0};
const OV_IC={ren:'M4 14l9-9 3 3-9 9H4zM12 6l3 3',dup:'M7 7h9v9H7zM4 13V4h9',mute:'M3 8h3l4-3v10l-4-3H3zM14 7l4 6M18 7l-4 6',solo:'M10 3a7 7 0 100 14 7 7 0 000-14zM8 13V7h3a2 2 0 010 4H8',
  del:'M4 6h12M8 6V4h4v2M6 6l1 10h6l1-10',split:'M10 3v14M7 6.5 4 10l3 3.5M13 6.5l3 3.5-3 3.5',copy:'M7 7h9v9H7zM4 13V4h9',cut:'M6 14a2 2 0 100 4 2 2 0 000-4zM14 14a2 2 0 100 4 2 2 0 000-4zM7.5 14.5 15 3M12.5 14.5 5 3',
  paste:'M6 4h8v13H6zM8 3h4v2H8z',save:'M4 3h10l3 3v11H4zM7 3v5h6V3M7 17v-5h7v5',open:'M2 6h6l2 2h8v9H2zM2 6V4h6',undo:'M7 7H13a4 4 0 0 1 0 8H8M7 7l3-3M7 7l3 3',
  set:'M10 7a3 3 0 1 0 0 6 3 3 0 0 0 0-6zM10 2v2M10 16v2M2 10h2M16 10h2M4.2 4.2l1.4 1.4M14.4 14.4l1.4 1.4M15.8 4.2l-1.4 1.4M5.6 14.4l-1.4 1.4'};
function ovMIcon(k){const d=OV_IC[k]||OV_IC.set;return `<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="${d}"/></svg>`}
/* one row, today's markup (the CSS of v0.228 to v0.256 keeps applying), plus roles, the submenu chevron and the description as the tip */
function ovMRow(it,i){if(it==='-')return'<hr>';if(!it)return'';
  if(it.head)return `<div class="mh">${esc(it.head)}</div>`;
  if(it.g!==undefined)return it.adv?`<div class="ovgl adv" role="presentation">◇ ${esc(it.g)}</div>`:'<hr>';
  if(it.chips)return `<div class="mchips" role="group">${it.chips.map((c,j)=>`<button data-ci="${i}:${j}" role="menuitem" class="${c.on?'on':''}${c.tog?' tog':''}"${c.dis?' disabled':''} title="${esc(c.tip||c.label)}">${c.ic||''}<span>${esc(c.label)}</span></button>`).join('')}</div>`;
  if(it.swatches)return `<div class="sws" role="group" aria-label="Colour">${PAL.map(c=>`<button data-sw="${c}" role="menuitemradio" aria-checked="${c===it.cur}" style="--c:${c}"${c===it.cur?' class="on"':''} aria-label="Colour"></button>`).join('')}</div>`;
  const chk=it.check!==undefined||it.sw,role=chk?'menuitemcheckbox':'menuitem',tip=it.sub?` data-tip="${esc(it.label)}|${esc(it.sub)}"`:'';
  return `<button data-i="${i}" role="${role}"${chk?` aria-checked="${!!it.check}"`:''}${it.kids?' aria-haspopup="menu" aria-expanded="false"':''}${it.danger?' class="dng"':''}${it.dis?' disabled':''}${tip}>${it.sw&&!it.ic?`<i class="swt${it.check?' on':''}"></i>`:it.ic?`<i class="mic">${it.ic}</i>`:it.check!==undefined?`<i class="ck${it.check?' on':''}" style="--c:${it.dot||'#ddd'}"></i>`:it.dot?`<i style="background:${it.dot}"></i>`:'<i></i>'}<span class="mlab">${esc(it.label)}${it.sub?`<small class="msub">${esc(it.sub)}</small>`:''}</span>${it.sw&&it.ic?`<i class="swt${it.check?' on':''}" style="margin-left:auto"></i>`:''}${it.kids?'<span class="ovchev" aria-hidden="true">›</span>':it.key?`<kbd>${it.key}</kbd>`:''}</button>`}
/* the menu: command row under the head, then the list; separators that end up first, last or doubled are dropped */
function ovMenuHTML(items,back){const cr=[];items.forEach((it,i)=>{if(it&&it.crow)cr.push(i)});
  const crow=cr.length?`<div class="ovcrow" role="group" aria-label="Common actions">${cr.map(i=>{const it=items[i],chk=it.on!==undefined;return `<button data-i="${i}" role="${chk?'menuitemcheckbox':'menuitem'}"${chk?` aria-checked="${!!it.on}"`:''} aria-label="${esc(it.label)}" class="${it.danger?'dng':''}${it.on?' on':''}"${it.dis?' disabled':''} data-tip="${esc(it.label)}${it.key?' ('+esc(it.key)+')':''}${it.sub?'|'+esc(it.sub):''}">${ovMIcon(it.crow)}<span>${esc(it.crowL||it.label)}</span></button>`}).join('')}</div>`:'';
  const L=[];if(back)L.push([1,`<button class="ovback" data-back role="menuitem"><span class="ovchev" aria-hidden="true">‹</span><span class="mlab">${esc(back)}</span></button>`],[0,'<hr>']);
  const swi=crow?items.findIndex(it=>it&&it.swatches):-1,sw=swi>=0?ovMRow(items[swi],swi):'';
  let placed=!crow;items.forEach((it,i)=>{if(it&&it.crow||i===swi)return;if(!placed&&!(it&&it.head)){L.push([2,crow]);if(sw)L.push([2,sw]);placed=true}L.push([it==='-'||(it&&it.g!==undefined&&!it.adv)?0:1,ovMRow(it,i)])});if(!placed){L.push([2,crow]);if(sw)L.push([2,sw])}
  const out=[];let prev=1,seen=0;for(const[real,h] of L){if(!real){if(!seen||!prev)continue;prev=0;out.push(h);continue}if(real===1&&h.startsWith('<div class="mh"')&&!seen){out.push(h);continue}seen=1;prev=real===2?0:1;out.push(h)}
  while(out.length&&out[out.length-1]==='<hr>')out.pop();return out.join('')}
/* descriptions: the big view menus show them as lines, so they do not also get the tip card */
function ovMTips(){if(ctxm.hidden||!/\b(mxvm|mxvo|mcols)\b/.test(ctxm.className))return;for(const b of ctxm.querySelectorAll('button[data-tip]'))if(b.querySelector('.msub'))b.removeAttribute('data-tip')}
/* the trigger: the focused element when the menu came from the keyboard (Shift+F10, the Menu key) or keyboard focus was showing */
function ovMTrig(){if(OVM.kbd)return OVM.kbd;const a=document.activeElement;if(!a||a===document.body||ctxm.contains(a))return null;try{if(!a.matches(':focus-visible'))return null}catch(e){return null}return a}
function ovMClosed(){OVM.stack=[];const t=OVM.trig,ret=OVM.ret;OVM.trig=null;OVM.ret=false;if(!ret||!t||!t.isConnected)return;const a=document.activeElement;if(a&&a!==document.body&&!ctxm.contains(a))return;try{t.focus({preventScroll:true})}catch(e){}
  /* the entry's command may draw the track headers again: focus the new header of the same track */
  const id=t.classList&&t.classList.contains('hdr')&&t.dataset.id;if(id)setTimeout(()=>{if(t.isConnected||document.activeElement&&document.activeElement!==document.body)return;const h=document.querySelector(`#hdrin .hdr[data-id="${id}"]`);if(h){if(h.tabIndex<0)h.tabIndex=-1;try{h.focus({preventScroll:true})}catch(e){}}},0)}
/* rows for the keyboard: the command row, the colours and a chip row count as one row each */
function ovMBtns(){return[...ctxm.querySelectorAll('button')].filter(b=>!b.disabled&&b.getClientRects().length)}
function ovMRowOf(b){return b.closest('.ovcrow,.sws,.mchips')||b}
function ovMFirst(){const L=ovMBtns();return L.find(b=>b.matches('button[data-i]')&&!b.closest('.ovcrow'))||L.find(b=>b.matches('button[data-i]'))||L[0]||null}
function ovMFocus(b){if(!b)return;try{b.focus({preventScroll:true});b.scrollIntoView({block:'nearest'})}catch(e){}}
function ovMLabel(b){const l=b.querySelector('.mlab');return((l?l.firstChild&&l.firstChild.textContent:b.textContent)||'').trim().toLowerCase()}
/* submenus open in place (drill-in): '‹ <parent>' on top, Left or Esc goes back to the parent entry */
function ovMSub(i){const it=MENU[i];if(!it||!it.kids||!it.kids.length)return;const w=parseFloat(getComputedStyle(ctxm).width)||0;OVM.stack.push({items:MENU,i});MENU=it.kids;
  ctxm.style.minWidth=w?w+'px':'';ctxm.innerHTML=ovMenuHTML(MENU,it.label);ovMFit();ovMFocus(ovMBtns().find(b=>b.matches('button[data-i]'))||ovMBtns()[0])}
function ovMBack(){const p=OVM.stack.pop();if(!p)return false;MENU=p.items;ctxm.innerHTML=ovMenuHTML(MENU);if(!OVM.stack.length)ctxm.style.minWidth='';ovMFit();ovMFocus(ctxm.querySelector(`button[data-i="${p.i}"]`)||ovMFirst());return true}
function ovMFit(){const r=ctxm.getBoundingClientRect(),z=ZOOM||1;if(r.bottom>innerHeight-6)ctxm.style.top=Math.max(4,(innerHeight-6-r.height)/z)+'px'}
/* the APG keyboard */
function ovMKey(e){if(ctxm.hidden)return;const k=e.key,L=ovMBtns();if(!L.length)return;const a=document.activeElement,cur=L.includes(a)?a:null;
  const rows=[];for(const b of L){const r=ovMRowOf(b);if(!rows.length||rows[rows.length-1].r!==r)rows.push({r,b:[b]});else rows[rows.length-1].b.push(b)}
  const ri=cur?rows.findIndex(x=>x.b.includes(cur)):-1,stop=()=>{e.preventDefault();e.stopPropagation()};
  if(k==='ArrowDown'||k==='ArrowUp'){stop();const n=rows.length,j=ri<0?(k==='ArrowDown'?0:n-1):(ri+(k==='ArrowDown'?1:n-1))%n;ovMFocus(rows[j].b[0]);return}
  if(k==='Home'||k==='End'){stop();ovMFocus(k==='Home'?L[0]:L[L.length-1]);return}
  if(k==='ArrowRight'||k==='ArrowLeft'){stop();if(!cur){ovMFocus(L[0]);return}const R=rows[ri].b,ci=R.indexOf(cur);
    if(k==='ArrowRight'){if(R.length>1){ovMFocus(R[Math.min(R.length-1,ci+1)]);return}const it=cur.dataset.i!=null&&MENU[+cur.dataset.i];if(it&&it.kids)ovMSub(+cur.dataset.i);return}
    if(R.length>1&&ci>0){ovMFocus(R[ci-1]);return}if(OVM.stack.length)ovMBack();return}
  if(k==='Enter'||k===' '){if(!cur)return;stop();OVM.ret=true;cur.click();if(!ctxm.hidden)OVM.ret=false;return}
  if(k==='Escape'){stop();if(OVM.stack.length){ovMBack();return}OVM.ret=true;closeMenu();return}
  if(k==='Tab'){stop();OVM.ret=true;closeMenu();return}
  if(k.length===1&&!e.metaKey&&!e.ctrlKey&&!e.altKey&&/\S/.test(k)){stop();clearTimeout(OVM.taT);OVM.ta+=k.toLowerCase();OVM.taT=setTimeout(()=>OVM.ta='',ovMs('typeahead'));
    const P=L.filter(b=>b.matches('button[data-i],button[data-back]')&&!b.closest('.ovcrow,.mchips')),s0=Math.max(0,P.indexOf(cur)+(OVM.ta.length>1?0:1));
    for(let q=0;q<P.length;q++){const b=P[(s0+q)%P.length];if(ovMLabel(b).startsWith(OVM.ta)){ovMFocus(b);break}}}}
/* submenu entries and the back row, before the menu's own click handler; the pointer moves keyboard focus with it */
ctxm.addEventListener('click',e=>{const bk=e.target.closest('[data-back]');if(bk){e.stopImmediatePropagation();ovMBack();return}
  const b=e.target.closest('button[data-i]');if(!b)return;const it=MENU[+b.dataset.i];if(it&&it.kids){e.stopImmediatePropagation();if(!b.disabled)ovMSub(+b.dataset.i)}},true);
ctxm.addEventListener('pointermove',e=>{if(e.pointerType==='touch')return;const b=e.target.closest&&e.target.closest('button');if(b&&!b.disabled&&document.activeElement!==b&&ctxm.contains(b))try{b.focus({preventScroll:true})}catch(x){}},{passive:true});
/* Shift+F10 and the Menu key open the menu of the focused element (its contextmenu handler, at its middle); a native contextmenu that
   the same key press sends afterwards is ignored. With nothing focused: the selected track's header. Arrows while the menu is open
   but focus is elsewhere move into the menu. This listener is registered before the shortcut dispatcher (also document, capture). */
document.addEventListener('keydown',e=>{
  /* keys go to the open menu before the app's shortcuts (Home is Go to start, letters are type-ahead here) */
  if(!ctxm.hidden&&ctxm.contains(document.activeElement)){ovMKey(e);if(e.defaultPrevented)e.stopImmediatePropagation();return}
  if(!ctxm.hidden&&(e.key==='ArrowDown'||e.key==='ArrowUp')){e.preventDefault();e.stopImmediatePropagation();ovMFocus(ovMFirst());return}
  if(!(e.key==='ContextMenu'||e.key==='F10'&&e.shiftKey&&!e.metaKey&&!e.ctrlKey&&!e.altKey))return;
  let el=document.activeElement;if(el&&(el.isContentEditable||/^(INPUT|TEXTAREA|SELECT)$/.test(el.tagName))&&e.key==='ContextMenu')return;
  if(!el||el===document.body||ctxm.contains(el)){el=typeof selT!=='undefined'&&selT&&document.querySelector(`#hdrin .hdr[data-id="${selT}"]`)||null}if(!el)return;
  e.preventDefault();e.stopPropagation();const r=el.getBoundingClientRect(),x=r.left+Math.min(r.width/2,40),y=r.top+Math.min(r.height/2,14);
  OVM.kbd=el;OVM.kcm=performance.now();try{el.dispatchEvent(new MouseEvent('contextmenu',{bubbles:true,cancelable:true,clientX:x,clientY:y,button:2,buttons:0,view:window}))}finally{OVM.kbd=null}
  if(!ctxm.hidden&&!OVM.trig)OVM.trig=el},true);
document.addEventListener('contextmenu',e=>{if(e.isTrusted&&performance.now()-OVM.kcm<400){e.preventDefault();e.stopImmediatePropagation()}},true);
/* regrouping helpers for the long menus: routing becomes one submenu when it has more than three entries (fold and ungroup stay out) */
function ovRouteSub(L){const i=L.findIndex(x=>x&&x.head==='Routing');if(i<0)return L;const rest=L.slice(i+1),keep=rest.filter(x=>x&&/^(Fold group|Unfold group|Ungroup)$/.test(x.label)),kids=rest.filter(x=>!keep.includes(x));
  if(kids.length<=3)return L;return[...L.slice(0,i),{label:'Groups, returns and sends',sub:'Put the track in a group, move it, take it out, or send it to a return',kids},...keep]}
function ovEnvSub(L){if(L.length<3)return L;const ed=L[0],kids=L.slice(1),on=kids.find(x=>x&&x.check);return[ed,{label:'Show envelope',sub:on?'Shown: '+on.label.replace(/^Envelope: /,''):'Show one envelope on the clip',kids}]}
function ovWarpSub(L){if(L.length<3)return L;return[L[0],{label:'Warp markers and quantize',sub:'Reset, find the hits, quantize the audio, warp to the beat',kids:L.slice(1)}]}
"""
rep('function askChoice(title,text,btns,icon){', JS + 'function askChoice(title,text,btns,icon){')
open(F, 'w', encoding='utf-8').write(s)
print('OV2a applied')
