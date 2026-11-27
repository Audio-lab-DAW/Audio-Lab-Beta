/* ===== v0.276: display-first devices, step 3 (task DV-3): On the picture, and the Pro EQ =====
   docs/devices-display-first.md sections 7 and 10 (the user's pick DD3 for the Pro EQ).
   On the picture is the closed state where each control sits at the part of the picture it changes, as small glass chips; controls without a place
   go to a More drawer. It shows only while the rail is closed and the device's mode is On the picture (right-click the eye); the rail open hides it.
   The mechanism (DVPIC): a device type gets an entry { lay(D, own, B) } that places its own controls (the same elements, so parameters, presets,
   automation and undo work exactly as on the rail) and returns the drawer's sections; every chip has the class dvface and is a glass face of the
   devices engine (DVG) over the display's flat picture. Devices without an entry keep hover reveal (the menu says so).
   Pro EQ: the band editor is a capsule under the selected dot and follows it (above the dot when there is no room under it); several selected bands
   get the capsule at their middle; with no band selected a small hint sits at the bottom of the graph. Gain is a slim fader at the right edge.
   The preset arrows and Change float at the top left; the band chips, the analyser, Auto, Scale and Out are in the More drawer.
   With the rail closed the Pro EQ's pill (pin on top, the eye under it) stands in the column right of the graph, clear of lane E's labels.
   No sound, parameter or stored value changes here; only where the controls are drawn. */
const DV3={more:new Set(),n:{lay:0,cap:0,more:0},capQ:0};
function dvPicOn(D){return D.classList.contains('dvshut')&&D.dataset.dvm==='picture'}
{const _fr=dvFrame;dvFrame=function(D,t,fl){const r=_fr.apply(this,arguments);try{dvPic(D,t)}catch(e){console.error('AudioLab on the picture',e)}return r}}
function dvPic(D,t){const B=D.querySelector(':scope>.devb');if(!B||!D.classList.contains('dvf'))return;const own=dvOwnOf(D,t);if(!own)return;const ty=dvType(D,own),P=DVPIC[ty];
  D.dataset.dvt=ty;
  /* a closed Pro EQ: the pill stands in the column right of the graph, the pin on top as on every device, the eye under it */
  if(ty==='eq'&&D.dataset.d==='fx'&&D.classList.contains('dvshut')){const T=B.querySelector(':scope>.dvtr'),pn=T&&T.querySelector(':scope>.pinbtn');if(pn&&pn!==T.firstElementChild)T.prepend(pn)}
  const on=!!P&&dvPicOn(D);D.classList.toggle('dvpic',on);if(!on)return;DV3.n.lay++;
  const V=B.querySelector(':scope>.dvval');if(V)V.remove();
  const more=P.lay(D,own,B)||[];if(more.length)dvPicMore(D,own,B,more);
  for(const el of B.querySelectorAll(':scope>.dvface'))dvPicFace(el)}
/* a chip: one glass face of the devices engine; a press on its empty part does not pan the devices panel */
function dvPicFace(el){if(el._dvp)return;el._dvp=1;el._dvgKind='pill';el._dvgRad=parseFloat(getComputedStyle(el).borderTopLeftRadius)||10;
  el.addEventListener('pointerdown',e=>{if(!e.target.closest('[data-c],input,select,button,label,.eqc,canvas'))e.stopPropagation()})}
/* the More drawer: a button at the top right of the picture and a panel with the controls that have no place in it */
function dvPicMore(D,own,B,secs){const id=D.dataset.d==='fx'?own.id:'inst',open=DV3.more.has(id);
  const btn=document.createElement('button');btn.type='button';btn.className='dvmore';btn.innerHTML='<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="5" cy="12" r="1.8"/><circle cx="12" cy="12" r="1.8"/><circle cx="19" cy="12" r="1.8"/></svg>More';
  btn.title='More: the controls that have no place in the picture ('+secs.map(s=>s.head).join(', ')+')';btn.setAttribute('aria-expanded',String(open));btn.setAttribute('aria-haspopup','true');
  const dr=document.createElement('div');dr.className='dvface dvdrw'+(open?' on':'');dr.setAttribute('role','group');dr.setAttribute('aria-label','More controls');
  for(const s of secs){const els=(s.els||[]).filter(Boolean);if(!els.length)continue;const h=document.createElement('h5');h.textContent=s.head;const w=document.createElement('div');w.className='dvdsec';w.append(...els);dr.append(h,w)}
  const pre=B.querySelector(':scope>.dvpre');if(pre)pre.append(btn);else{btn.classList.add('dvface');B.append(btn)}B.append(dr)}
function dvMoreToggle(D,force){const own=dvOwnOf(D);if(!own)return;const id=D.dataset.d==='fx'?own.id:'inst',on=force===undefined?!DV3.more.has(id):force;DV3.n.more++;
  if(on)DV3.more.add(id);else DV3.more.delete(id);const dr=D.querySelector(':scope>.devb>.dvdrw'),b=D.querySelector(':scope>.devb .dvmore');
  if(dr)dr.classList.toggle('on',on);if(b)b.setAttribute('aria-expanded',String(on));dvgDirty();return on}
addEventListener('click',e=>{const b=e.target.closest&&e.target.closest('#fxin .dev.dvpic>.devb .dvmore');if(!b)return;e.preventDefault();e.stopPropagation();
  const D=b.closest('.dev');if(dvMoreToggle(D)){const f=D.querySelector(':scope>.devb>.dvdrw :is(button,input,select,[tabindex="0"])');if(f&&e.detail===0)f.focus({preventScroll:true})}},true);
addEventListener('keydown',e=>{if(e.key!=='Escape')return;const dr=e.target.closest&&e.target.closest('#fxin .dev.dvpic>.devb>.dvdrw.on');if(!dr)return;e.preventDefault();e.stopPropagation();const D=dr.closest('.dev');dvMoreToggle(D,false);const b=D.querySelector(':scope>.devb .dvmore');if(b)b.focus({preventScroll:true})},true);

/* ---- Pro EQ on the picture (DD3) ---- */
DVPIC.eq={lay:dvpEq};
function dvpEq(D,own,B){const side=B.querySelector(':scope>.eqside'),cv=B.querySelector('canvas.eqv');if(!side||!cv)return[];
  const pr=side.querySelector(':scope>.dspr'),eqb=side.querySelector(':scope>.eqb'),bands=side.querySelector(':scope>.eqbands'),ov2=side.querySelector('.eqov2');
  let an=null,au=null;
  if(pr){an=pr.querySelector('.eqan');au=pr.querySelector(':scope>label.tgl');if(an)an.remove();if(au)au.remove();pr.classList.add('dvface','dvpre');B.append(pr)}
  if(eqb){eqb.classList.add('dvface','dvcap');
    if(eqb.classList.contains('eqnone')){const p=eqb.querySelector(':scope>p'),b=eqb.querySelector(':scope>b');
      if(!eqb.querySelector('.eqrow')){eqb.classList.add('dvhint');if(b)b.textContent='Click a dot to edit its band, double-click the graph to add one'}
      eqb.title=p?p.textContent.trim():''}
    else{const del=eqb.querySelector('[data-eq=del]');if(del&&!del.getAttribute('aria-label'))del.setAttribute('aria-label','Delete this band')}
    B.append(eqb);dvCapPos(D)}
  const g=B.querySelector(':scope>.dug');if(g)g.classList.add('dvface','dvslim');
  return[{head:'Bands',els:[bands]},{head:'Analyser',els:[an,au]},{head:'Whole EQ',els:[ov2]}]}
/* the capsule sits under the selected dot (the dot's place as the EQ's own hit test computes it), above it when there is no room */
function dvCapPos(D){const B=D.querySelector(':scope>.devb'),C=B&&B.querySelector(':scope>.dvcap'),cv=B&&B.querySelector('canvas.eqv');if(!C||!cv||!cv.offsetWidth)return;
  const f=dvOwnOf(D);if(!f||!f.p||!f.p.bands)return;DV3.n.cap++;
  const z=ZOOM||1,cr=cv.getBoundingClientRect(),br=B.getBoundingClientRect(),ox=(cr.left-br.left)/z-B.clientLeft,oy=(cr.top-br.top)/z-B.clientTop,w=cv.clientWidth,h=cv.clientHeight;
  const gs=(f.p.gs??100)/100,X=vizInst(f),sel=[...eqSel(f)].filter(i=>f.p.bands[i]);
  const pts=sel.map(i=>{const b=f.p.bands[i],gl=(/shelf|peak|tilt/.test(b.t)?b.g*gs:0)+(X&&X.dyn&&X.dyn[i]||0);return[fX(b.f,w),h/2-gl/24*(h/2-12)]});
  const cw=C.offsetWidth,ch=C.offsetHeight,BW=B.clientWidth,BH=B.clientHeight;let x,y;
  if(!pts.length){x=ox+(w-cw)/2;y=oy+h-ch-44}
  else{const px=pts.reduce((a,q)=>a+q[0],0)/pts.length,lo=Math.max(...pts.map(q=>q[1])),hi=Math.min(...pts.map(q=>q[1]));x=ox+px-cw/2;y=oy+lo+14;if(y+ch>BH-4)y=oy+hi-14-ch}
  x=Math.max(4,Math.min(x,BW-cw-36));y=Math.max(32,Math.min(y,BH-ch-4));
  const L=Math.round(x)+'px',T=Math.round(y)+'px';if(C.style.left!==L||C.style.top!==T){C.style.left=L;C.style.top=T;dvgDirty()}}
/* the capsule follows the dot while it is dragged or scrolled */
{const fi=document.getElementById('fxin');if(fi){const q=e=>{const D=e.target.closest&&e.target.closest('.dev.eq2.dvpic');if(!D||DV3.capQ)return;if(e.type==='pointermove'&&!e.buttons)return;DV3.capQ=1;requestAnimationFrame(()=>{DV3.capQ=0;dvCapPos(D)})};
  for(const ty of['pointermove','pointerup','wheel'])fi.addEventListener(ty,q,{capture:true,passive:true})}}
