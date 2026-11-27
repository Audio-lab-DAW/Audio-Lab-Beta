/* ===== v0.262: display-first devices, the shared frame (task DV-1) =====
   docs/devices-display-first.md sections 7 and 10. Every device in the devices panel (#fxin; pinned windows keep their own look) gets one frame:
   - the sideways title strip on the left stays as it is (v0.196);
   - the right-hand Parameters strip is gone; its width goes to the display, and the display box (black) fills the device;
   - top right, over the display: a small pill with the eye and the pin. A plain click on the eye opens and closes the glass rail; right-click,
     a long press on touch, or the menu key (Shift+F10) on the eye opens a menu: Open / Close the glass rail, and what the closed state shows,
     Hover reveal or On the picture;
   - rail open (the eye on): the device's controls sit on one glass rail at the right of the display;
   - rail closed: the picture is clean, a line of values sits at its bottom, and the controls come back as a floating panel while the mouse is over
     the device, while a control inside has the keyboard focus (Tab), or after a tap on the display (touch);
   - per device instance: kOpen as before (missing or true = rail open, false = closed), and the new kMode ('hover' or 'picture'; missing = the
     device type's default from section 7). Old projects need no change. On the picture needs positions for each device's controls (DVPIC, filled
     by the device steps); until a device has them it shows hover reveal, and the menu says so.
   The glass of the rail and of the revealed panel is drawn by one more glass engine canvas over the devices panel (DVG), with the display canvases
   as flat pictures; the small pill is a plain tint (no glass at rest, so a closed device costs nothing while nothing changes).
   Nothing here touches sound, parameters, presets or automation: the controls are the device's own, only placed differently. */
const DVDEF={eq:{mode:'picture'}};
const DVPIC={};
const DV={n:{render:0,frame:0,menu:0,toggle:0,vals:0},lp:null,lpDone:0};
const DVEYE=on=>`<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M2.5 12s3.5-6.5 9.5-6.5 9.5 6.5 9.5 6.5-3.5 6.5-9.5 6.5S2.5 12 2.5 12z"/>${on?'<circle cx="12" cy="12" r="2.8"/>':'<path d="M4 20 20 4"/>'}</svg>`;
function dvOwnOf(D,t){t=t||curT();if(!t||!D)return null;return D.dataset.d==='fx'?(t.fx||[]).find(q=>q.id===D.dataset.id):t.inst}
function dvType(D,own){return D.dataset.d==='fx'?own.type:(own.preset||'')}
function dvMode(own,ty){const m=own&&own.kMode;return m==='picture'||m==='hover'?m:((DVDEF[ty]||{}).mode||'hover')}
function dvShows(own,ty){return dvMode(own,ty)==='picture'&&DVPIC[ty]?'picture':'hover'}
function dvPinned(t,o){try{const fid=o===t.inst?'inst':o.id;return PIN.list.some(p=>p.tid===t.id&&p.fid===fid)}catch(e){return false}}
/* the controls of a closed device are built as if the rail were open (so they can be revealed), and the device is then laid out closed.
   kOpen is true only while the markup is made; the pictures are drawn afterwards and read false. */
{const _rf=renderFx;renderFx=function(){if((typeof IBCTX!=='undefined'&&IBCTX)||PIN.inner)return _rf.apply(this,arguments);
  const t=curT(),fl=[];if(t)for(const o of[t.inst,...(t.fx||[])])if(o&&o.kOpen===false&&!dvPinned(t,o)){o.kOpen=true;fl.push(o)}
  let r;try{r=_rf.apply(this,arguments)}finally{for(const o of fl)o.kOpen=false}
  try{dvFrameAll(t,new Set(fl))}catch(e){console.error('AudioLab display-first frame',e)}return r}}
function dvFrameAll(t,fl){const root=document.getElementById('fxin');if(!root||!t)return;DV.n.render++;
  for(const D of root.querySelectorAll(':scope>.dev.du.ds[data-d=inst],:scope>.dev.du.ds[data-d=fx]')){try{dvFrame(D,t,fl)}catch(e){console.error('AudioLab display-first frame',e)}}
  dvgDirty()}
function dvFrame(D,t,fl){const own=dvOwnOf(D,t),B=D.querySelector(':scope>.devb');if(!own||!B||dvPinned(t,own))return;DV.n.frame++;
  const shut=fl.has(own),ty=dvType(D,own),side=B.querySelector(':scope>.dfs,:scope>.eqside'),Rs=D.querySelector(':scope>.dsr'),pin=Rs&&Rs.querySelector('.pinbtn'),dsrW=Rs?Rs.offsetWidth:0;
  D.classList.add('dvf');D.classList.toggle('dvshut',shut&&!!side);D.classList.toggle('dvopen',!shut&&!!side);D.classList.remove('dvshow');
  /* closed effects take the picture width they had closed before (the canvas size of .fxd follows .kopen) */
  if(shut&&D.classList.contains('fxd'))D.classList.remove('kopen');
  if(Rs)Rs.remove();for(const a of D.querySelectorAll('.duar'))a.remove();
  /* the pill: eye and pin */
  let P=B.querySelector(':scope>.dvtr');if(!P){P=document.createElement('div');P.className='dvtr';B.append(P)}P.replaceChildren();
  if(side){const e=document.createElement('button');e.type='button';e.className='dveye'+(shut?'':' on');e.innerHTML=DVEYE(!shut);
    const tt=(shut?'Show the controls on a glass rail':'Hide the glass rail: only the picture stays')+'. Right-click (or a long press) for what the picture shows while the rail is closed';
    e.title=tt;e.setAttribute('aria-label',shut?'Open the glass rail':'Close the glass rail');e.setAttribute('aria-pressed',String(!shut));e.setAttribute('aria-haspopup','menu');
    /* the old arrow's markers, for scripts that look for it; the frame's own click handler runs first and stops the old one */
    e.dataset[D.dataset.d==='fx'?'kt':'ikt']='';P.append(e)}
  if(pin)P.append(pin);if(!P.children.length)P.remove();
  /* the rail (one glass panel behind the controls and the gain) */
  let R=B.querySelector(':scope>.dvrail');if(side){if(!R){R=document.createElement('div');R.className='dvrail';R.setAttribute('aria-hidden','true');B.insertBefore(R,side)}}else if(R)R.remove();
  /* closed: a line of values at the bottom of the picture */
  let V=B.querySelector(':scope>.dvval');if(shut&&side){if(!V){V=document.createElement('div');V.className='dvval';B.append(V)}}else if(V)V.remove();
  D.dataset.dvm=dvShows(own,ty);
  /* the strip's width goes to the display: the device keeps its width */
  if(dsrW){B.style.minWidth='';B.style.minWidth=(B.offsetWidth+dsrW)+'px'}
  if(shut&&side){const g=B.querySelector(':scope>.dug'),gw=g?g.offsetWidth+12:6;B.style.setProperty('--dvdr',gw+'px');
    /* a closed device is never narrower than its revealed controls, so they never cover the title strip */
    const need=side.offsetWidth+gw+16;if(B.offsetWidth<need)B.style.minWidth=need+'px'}else B.style.removeProperty('--dvdr');
  /* the picture's own buttons along its bottom edge stay clear: no values line over them */
  if(V){const bb=B.getBoundingClientRect().bottom,fv=B.querySelector(':scope>.dfv');let clash=false;if(fv)for(const el of fv.querySelectorAll('button,select,input,label,.hb,.vb,.kn')){const q=el.getBoundingClientRect();if(q.width&&q.height&&q.bottom>bb-30){clash=true;break}}
    if(clash){V.remove();V=null}}
  dvRail(D);if(V)dvVals(D)}
/* the rail panel covers the controls and the gain */
function dvRail(D){const B=D.querySelector(':scope>.devb'),R=B&&B.querySelector(':scope>.dvrail');if(!R)return;const els=[...B.querySelectorAll(':scope>.dfs,:scope>.eqside,:scope>.dug')].filter(e=>e.offsetWidth);if(!els.length){R.hidden=true;return}R.hidden=false;
  let l=1e9,t=1e9,r=-1e9,b=-1e9;for(const e of els){const x=e.offsetLeft,y=e.offsetTop;l=Math.min(l,x);t=Math.min(t,y);r=Math.max(r,x+e.offsetWidth);b=Math.max(b,y+e.offsetHeight)}
  l=Math.max(2,l-6);t=Math.max(2,t-4);r=Math.min(B.clientWidth-2,r+4);b=Math.min(B.clientHeight-2,b+4);const k=l+','+t+','+(r-l)+','+(b-t);if(R._k===k)return;R._k=k;
  R.style.left=l+'px';R.style.top=t+'px';R.style.width=(r-l)+'px';R.style.height=(b-t)+'px'}
/* the values line: label and value of the first controls, as plain text */
function dvVals(D){const B=D.querySelector(':scope>.devb'),V=B&&B.querySelector(':scope>.dvval');if(!V)return;DV.n.vals++;const S=B.querySelector(':scope>.dfs,:scope>.eqside'),parts=[],seen=new Set();
  for(const el of S?S.querySelectorAll('[data-c]'):[]){const id=el.dataset.c;if(seen.has(id))continue;seen.add(id);const C=CT.get(id);if(!C||!C.label||!C.spec||typeof C.spec.f!=='function')continue;let v;try{v=C.spec.f(C.get())}catch(e){continue}if(v===undefined||v===null||v==='')continue;parts.push([String(C.label),String(v)]);if(parts.length>=8)break}
  const h=parts.map(([l,v])=>`<span>${esc(l)} <b>${esc(v)}</b></span>`).join('');if(V._h!==h){V._h=h;V.innerHTML=h;V.title=parts.length?'Values: '+parts.map(([l,v])=>l+' '+v).join(', ')+'. Point at the device to change them':'Point at the device to show its controls'}}
/* eye: plain click opens and closes the rail */
function dvToggle(D){const t=curT(),own=dvOwnOf(D,t);if(!own)return;DV.n.toggle++;const open=own.kOpen===false;own.kOpen=open;if(open)DUOPEN=D.dataset.d==='fx'?own.id:'inst';renderFx();
  requestAnimationFrame(()=>{const D2=D.dataset.d==='fx'?document.querySelector(`#fxin .dev[data-id="${own.id}"] .dveye`):document.querySelector('#fxin .dev[data-d=inst] .dveye');if(D2&&document.activeElement===document.body)D2.focus({preventScroll:true})})}
function dvSetMode(D,m){const own=dvOwnOf(D);if(!own)return;own.kMode=m;renderFx()}
function dvMenu(D,x,y){const t=curT(),own=dvOwnOf(D,t);if(!own)return;DV.n.menu++;const ty=dvType(D,own),open=own.kOpen!==false,m=dvMode(own,ty),has=!!DVPIC[ty],nm=(D.querySelector(':scope>.devh>span')||{}).textContent||'Device';
  try{tipHide()}catch(e){}
  openMenu(x,y,[{head:nm.trim()},{label:open?'Close the glass rail':'Open the glass rail',sub:'Same as a click on the eye',act:()=>dvToggle(D)},'-',{head:'When the rail is closed'},
    {label:'Hover reveal',check:m==='hover',sub:'A clean picture; the controls appear while the mouse is over the device',act:()=>dvSetMode(D,'hover')},
    {label:'On the picture',check:m==='picture',sub:has?'Each control sits at the part of the picture it changes':'Not ready on this device yet: it shows hover reveal until then',act:()=>dvSetMode(D,'picture')}])}
addEventListener('click',e=>{const b=e.target.closest&&e.target.closest('#fxin .dveye');if(!b)return;e.stopImmediatePropagation();e.preventDefault();if(performance.now()-DV.lpDone<700)return;dvToggle(b.closest('.dev'))},true);
addEventListener('contextmenu',e=>{const b=e.target.closest&&e.target.closest('#fxin .dveye');if(!b)return;e.preventDefault();e.stopImmediatePropagation();const r=b.getBoundingClientRect();dvMenu(b.closest('.dev'),e.clientX||r.left,e.clientY||r.bottom)},true);
addEventListener('keydown',e=>{const b=e.target.closest&&e.target.closest('#fxin .dveye');if(!b)return;if(e.key==='ContextMenu'||(e.key==='F10'&&e.shiftKey)){e.preventDefault();e.stopImmediatePropagation();const r=b.getBoundingClientRect();dvMenu(b.closest('.dev'),r.left,r.bottom+2)}},true);
/* touch: a long press on the eye opens the menu; a tap on a closed device's picture shows or hides its controls */
addEventListener('pointerdown',e=>{if(e.pointerType==='mouse')return;const tg=e.target.closest?e.target:null;if(!tg)return;
  const b=tg.closest('#fxin .dveye');if(b){clearTimeout(DV.lp&&DV.lp.tm);const x=e.clientX,y=e.clientY;DV.lp={x,y,tm:setTimeout(()=>{DV.lp=null;DV.lpDone=performance.now();dvMenu(b.closest('.dev'),x,y)},500)};return}
  const D=tg.closest('#fxin .dev.dvshut');for(const o of document.querySelectorAll('#fxin .dev.dvshow'))if(o!==D)o.classList.remove('dvshow');
  if(D&&!tg.closest('.dfs,.eqside,.dug,.dvtr,.devh')){DV.tap={D,x:e.clientX,y:e.clientY,t:performance.now()}}},true);
addEventListener('pointermove',e=>{if(DV.lp&&Math.hypot(e.clientX-DV.lp.x,e.clientY-DV.lp.y)>8){clearTimeout(DV.lp.tm);DV.lp=null}},true);
addEventListener('pointerup',e=>{if(DV.lp){clearTimeout(DV.lp.tm);DV.lp=null}const T=DV.tap;DV.tap=null;if(!T||e.pointerType==='mouse')return;if(Math.hypot(e.clientX-T.x,e.clientY-T.y)<10&&performance.now()-T.t<400){T.D.classList.toggle('dvshow');dvgDirty()}},true);
addEventListener('pointercancel',()=>{if(DV.lp){clearTimeout(DV.lp.tm);DV.lp=null}DV.tap=null},true);
/* the values line follows edits; the glass follows hover, focus and scrolling (a few hundred ms of reading the page, then nothing) */
{const fi=document.getElementById('fxin');if(fi){const upd=e=>{const D=e.target.closest&&e.target.closest('.dev.dvshut');if(D&&!D._dvq){D._dvq=1;requestAnimationFrame(()=>{D._dvq=0;dvVals(D)})}};
  for(const ty of['input','change','pointerup','wheel','keyup'])fi.addEventListener(ty,upd,{capture:true,passive:true});
  fi.addEventListener('mouseout',e=>{const D=e.target.closest&&e.target.closest('.dev.dvshut');if(D&&!D.contains(e.relatedTarget))dvVals(D)},{passive:true});
  for(const ty of['scroll','mouseover','mouseout','focusin','focusout','transitionend'])fi.addEventListener(ty,()=>dvgDirty(),{capture:true,passive:true})}
 addEventListener('resize',()=>dvgDirty(),{passive:true})}

/* ---- the glass over the device displays: one engine canvas over the devices panel (docs/devices-display-first.md section 8) ----
   Above the display canvases, under the controls (z-index only). Faces: the rail of each device whose rail is open, and the revealed panel of a closed
   device while it shows. The display canvases under a visible face are its flat pictures (reduced by the engine before upload), refreshed at most
   twice a second when stopped and 20 times a second while playing, and only while a face covers them. Rectangles are read from the page only for
   about 320 ms after something changed (render, scroll, hover, focus, resize); otherwise a frame costs one call that returns at once. */
const DVG={g:null,cv:null,fail:'',lv:'',lens:'',blur:'',hot:0,faces:new Map(),flats:new Map(),fT:0,bd:null,par:null,n:{sync:0,made:0,flatSet:0,flatDirty:0,faces:0}};
function dvgDirty(){DVG.hot=performance.now()+320}
function dvgKill(){if(DVG.g){try{DVG.g.destroy()}catch(e){}}if(DVG.cv)DVG.cv.remove();DVG.g=null;DVG.cv=null;DVG.faces.clear();DVG.flats.clear();DVG.lv='';document.body.classList.remove('dvg')}
function dvgMake(fi){if(DVG.fail)return null;const c=document.createElement('canvas');c.className='dvgCv';c.setAttribute('aria-hidden','true');fi.after(c);let g=null;
  try{g=AudioLabGlass.create(c,{level:GLE.lv==='light'?'light':'glass',lens:gleLens(),blur:gleBlur(),maxDpr:2,kinds:{window:{shadow:0,tint:0},pill:{shadow:0,tint:0}}})}catch(e){console.warn('AudioLab glass engine (devices): '+(e&&e.message||e))}
  if(!g||g.mode!=='gl'){DVG.fail=(g&&g.reason)||'no webgl2';try{if(g)g.destroy()}catch(e){}c.remove();return null}
  /* flats need a backdrop: a 2 x 2 picture in the display colour (section 8, finding 2) */
  const bd=document.createElement('canvas');bd.width=bd.height=2;const x=bd.getContext('2d');x.fillStyle='#06070a';x.fillRect(0,0,2,2);DVG.bd=bd;
  try{g.setBackdropColor([6/255,7/255,10/255,1]);g.setBackdrop(bd,{rect:[0,0,2,2]});g.markDirty()}catch(e){}
  DVG.g=g;DVG.cv=c;DVG.lv=GLE.lv;DVG.lens=gleLens();DVG.blur=gleBlur();DVG.n.made++;document.body.classList.add('dvg');dvgDirty();return g}
function dvgR(r,o){const z=ZOOM||1,q=v=>Math.round(v/z*100)/100;return[q(r.left-o.left),q(r.top-o.top),q(r.width),q(r.height)]}
function dvgSync(fi,now){const g=DVG.g,c=DVG.cv;DVG.n.sync++;
  const par=fi.parentElement;if(c.parentElement!==par||c.previousElementSibling!==fi)fi.after(c);
  const st=c.style,L=fi.offsetLeft+'px',T=fi.offsetTop+'px',W=fi.clientWidth+'px',H=fi.clientHeight+'px';if(st.left!==L)st.left=L;if(st.top!==T)st.top=T;if(st.width!==W)st.width=W;if(st.height!==H)st.height=H;
  {const rr=getComputedStyle(fi).borderRadius;if(st.borderRadius!==rr)st.borderRadius=rr}
  if(DVG.lens!==gleLens()){DVG.lens=gleLens();g.setLensPreset(DVG.lens)}if(DVG.blur!==gleBlur()){DVG.blur=gleBlur();g.setBlurPreset(DVG.blur)}
  const o=c.getBoundingClientRect(),seen=new Set(),fseen=new Set();
  for(const R of fi.querySelectorAll(':scope>.dev.dvf>.devb>.dvrail')){if(R.hidden)continue;const r=R.getBoundingClientRect();if(r.width<8||r.height<8||r.right<o.left||r.left>o.right)continue;
    const op=+getComputedStyle(R).opacity||0,D=R.closest('.dev');if(!R._dvg)R._dvg='r'+(++DVG.n.faces);const id=R._dvg,rect=dvgR(r,o),vis=op>.01;seen.add(id);
    const k=rect.join(',')+'|'+op.toFixed(2);if(DVG.faces.get(id)!==k){DVG.faces.set(id,k);if(g.hasPanel(id))g.updatePanel(id,{rect,opacity:op,visible:vis});else g.addPanel({id,rect,radius:12,kind:'window',over:'flats',opacity:op,visible:vis,tintAmount:0,shadow:0})}
    if(op<.99&&vis)dvgDirty();if(!vis)continue;
    for(const cv of D.querySelectorAll(':scope>.devb canvas')){if(!cv.width||!cv.height){if(cv.offsetWidth)dvgDirty();continue}const q=cv.getBoundingClientRect();if(q.width<16||q.right<=r.left||q.left>=r.right||q.bottom<=r.top||q.top>=r.bottom)continue;
      if(!cv._dvgS)cv._dvgS='c'+(++DVG.n.faces);const fk=cv._dvgS,fr=dvgR(q,o),sig=fr.join(',')+'|'+cv.width+'x'+cv.height;fseen.add(fk);if(DVG.flats.get(fk)!==sig){DVG.flats.set(fk,sig);g.setFlat(fk,{rect:fr,radius:2,source:cv});DVG.n.flatSet++}}}
  for(const id of[...DVG.faces.keys()])if(!seen.has(id)){DVG.faces.delete(id);g.removePanel(id)}
  for(const k of[...DVG.flats.keys()])if(!fseen.has(k)){DVG.flats.delete(k);g.removeFlat(k)}}
function dvgTick(now){const fi=document.getElementById('fxin'),on=GLE.on&&!!GLE.g&&!!fi&&!!fi.offsetParent&&fi.offsetParent===fi.parentElement&&!!fi.querySelector('.dev.dvf');
  if(!on){if(DVG.g||DVG.cv)dvgKill();return}
  if(!DVG.g&&!dvgMake(fi))return;
  if(DVG.lv!==GLE.lv){DVG.lv=GLE.lv;DVG.g.setLevel(GLE.lv==='light'?'light':'glass');dvgDirty()}
  if(now<DVG.hot)dvgSync(fi,now);
  /* the pictures under visible faces: refreshed at a capped rate, only while there are any */
  if(DVG.flats.size&&now-DVG.fT>(play&&play.on?50:500)){DVG.fT=now;for(const k of DVG.flats.keys()){DVG.g.markFlatDirty(k);DVG.n.flatDirty++}}
  DVG.g.render(now)}
{const _gt=glfTick;glfTick=function(now){const r=_gt.apply(this,arguments);try{dvgTick(now)}catch(e){if(!DVG.err){DVG.err=1;console.error('AudioLab glass engine (devices)',e)}}return r}}
