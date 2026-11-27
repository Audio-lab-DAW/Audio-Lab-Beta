/* ====================== v0.227 (task GS2, glass step 2): windows, sheets and menus on the glass engine ======================
   Plan: docs/glass-engine-plan.md (3.1 "Step 2", 2.4 option a; 3.2 to 3.5 are binding), module: docs/glass-engine-module.md section 4 "Step 2".
   backdrop-filter is used nowhere in the app any more, at no level (one CSS rule: *,*::before,*::after{backdrop-filter:none!important}).
   The floating glass (floating windows such as the mixer and the sidechain window, the spectrum windows, pinned devices, sheets such as Settings,
   askChoice and the audio to MIDI pop-up, the update window, menus and pop-ups) gets its frosted, bent backdrop from the glass engine:
   - A LAYER is one more engine on one full-window canvas (.glfCv), put into the page's stacking order directly under the floating elements it serves
     (same z-index, just before them in the page), above the docked panels' DOM. Its backdrop is the same rectangle scene as the docked engine's
     (sent once per edit; scroll, zoom and playhead are uniforms), drawn on the graphics card. Nothing is uploaded on this path.
   - Each floating element is one face (one quad) in its layer. Moving a window is one quad redraw: no rectangle list, no backdrop, no blur pyramid.
   - GLASS NEVER SAMPLES GLASS. The engine reads only its own backdrop picture, never a canvas it draws to. Where floating glass covers DOM, the engine is fed
     a flat picture of what is underneath (plan 2.4 option a): the docked panels as their colour, the device displays and the piano roll as small copies
     of their canvases (the engine reduces them to a quarter before the upload; refreshed only where a face covers them, at most 20 times a second),
     and floating elements of a lower layer as their colour. An element that overlaps another floating element goes into the next layer up, so its face
     covers the lower element's DOM instead of showing it through. At most three layers; a fourth level of overlap is drawn solid.
   - The element on top keeps its own tint, border, shadow and content. Opaque elements need no face (they are only what is underneath for others).
   - Levels follow the docked panels (Glass, Light, Solid; Solid or no WebGL2: the floating elements are solid too). Lens and frosting presets are shared.
   - The mixer: the tab above the window gets a face too (it reaches under the window, so the window's square corner is glass as well); the nested blurs
     of the tab and of the pan handles are gone with the rule above.
   The old lens code (rfAttach, rfBuild, rfMap, rfStyle, the feImage lens) stays in the file but is not used: rfAttach makes nothing any more. Step 3 deletes it
   after the user's frame-rate check on the Mac.
   Debug and bench only: GLF.mode='face' gives every floating element its own engine on a canvas only as large as the element (setOrigin), the other way
   the task asked to measure; it rebuilds the backdrop whenever a window moves. glfReset() applies a change of mode. */
const GLF={L:[],mode:'layer',max:3,act:false,fail:'',seq:0,cand:null,candT:0,slowT:0,dispT:0,sig:0,src:'scene',srcT:0,off:null,vw:null,items:[],st:'',err:0,
  n:{tick:0,regroup:0,made:0,scene:0,view:0,ph:0,flatSet:0,flatDirty:0,solid:0,move:0}};
/* what is floating glass, and what kind of face it gets ('tab' = the mixer's tab: a window face that reaches under its window) */
const GLFSEL=[['.fwin','window'],['.abxw','window'],['.spov','window'],['.pinw>.pinb','window'],['#mixWin>.fwh','tab'],['.modal>.sheet','sheet'],['#uywM .uyww','sheet'],['#ctxm','menu'],['.pop','menu'],['#w9m','menu']];
const GLFDOCK=['hglass','tr','fxglass','fxband'];
function glfCands(n){if(GLF.cand&&n-GLF.candT<400)return GLF.cand;GLF.candT=n;const L=[],seen=new Set();for(const[s,k] of GLFSEL)for(const el of document.querySelectorAll(s))if(!seen.has(el)){seen.add(el);L.push([el,k])}return GLF.cand=L}
/* shown at all? hidden attributes first (no layout needed), then the box */
function glfShown(el){if(!el.isConnected)return false;for(let t=el;t&&t!==document.body;t=t.parentElement)if(t.hidden)return false;return el.getClientRects().length>0}
/* the element's place in the page's stacking order: the z-index of its outermost ancestor that has one, and the child of <body> it sits in */
function glfInfo(el,n){let c=el._glfI;if(c&&n-c.t<250)return c;let z=0,top=el;for(let t=el;t&&t!==document.body;t=t.parentElement){top=t;const s=getComputedStyle(t).zIndex;if(s!=='auto')z=parseInt(s)||0}
  const cs=getComputedStyle(el),tc=el.classList.contains('spov')&&el.querySelector('.spgl')||el,bs=tc===el?cs:getComputedStyle(tc),bg=gleCol(bs.backgroundColor||'transparent'),img=bs.backgroundImage&&bs.backgroundImage!=='none';
  c=el._glfI={t:n,z,top,cs,tcs:top!==el?getComputedStyle(top):null,rad:Math.max(parseFloat(cs.borderTopLeftRadius)||0,parseFloat(cs.borderBottomLeftRadius)||0),bg,opaque:!img&&bg[3]>=.985};return c}
const glfOvl=(a,b)=>a[0]<b[0]+b[2]-1&&b[0]<a[0]+a[2]-1&&a[1]<b[1]+b[3]-1&&b[1]<a[1]+a[3]-1;
/* one layer: an engine on its own canvas */
function glfLayer(i){let L=GLF.L[i];if(L)return L;if(GLF.fail)return null;const c=document.createElement('canvas');c.className='glfCv';c.setAttribute('aria-hidden','true');c.hidden=true;document.body.prepend(c);let g=null;
  try{g=AudioLabGlass.create(c,{level:GLE.lv==='light'?'light':'glass',lens:gleLens(),blur:gleBlur(),maxDpr:2,
    kinds:{window:{shadow:0,tint:0},sheet:{shadow:0,tint:0},menu:{shadow:0,tint:0},pill:{shadow:0,tint:0}}})}catch(e){console.warn('AudioLab glass engine (floating): '+(e&&e.message||e))}
  if(!g||g.mode!=='gl'){GLF.fail=(g&&g.reason)||'no webgl2';try{if(g)g.destroy()}catch(e){}c.remove();return null}
  L=GLF.L[i]={i,cv:c,g,z:null,before:null,ids:new Set(),flats:new Map(),vis:false,sig:-1,src:'',fit:null,view:'',ph:null};GLF.n.made++;return L}
function glfKill(){for(const L of GLF.L)if(L){try{L.g.destroy()}catch(e){}L.cv.remove()}GLF.L=[];GLF.act=false;GLF.st='';for(const it of GLF.items)if(it.el.classList.contains('glfsol'))it.el.classList.remove('glfsol');GLF.items=[]}
function glfReset(){glfKill();GLF.fail='';GLF.cand=null}
/* the scene of a layer: the same rectangle list as the docked engine's (made by gleBuild), shifted to where the arrangement is on the page */
function glfFeed(L,full){const g=L.g,v=GLF.vw;if(!g||!v||!GLF.LL)return;
  if(GLF.src==='scene'){if(L.src!=='scene'){L.src='scene';g.setBackdrop(null);L.sig=-1;L.view=''}
    if(full||L.sig!==GLF.sig){L.sig=GLF.sig;g.setBackdropColor(gleCol(TH.bg||'#0b0c10'));g.setScene({lanes:GLF.LL.lanes,clips:GLF.LL.clips,bg:gleCol(TH.bg),titleH:0,bodyAlpha:1,playheadColor:gleCol(v.pc),playheadW:v.pw});GLF.n.scene++}
    const o=GLF.off||[0,0],k=[v.x,v.y,v.z,v.w,v.h,v.ay,v.x0,o[0],o[1]].join(',');
    if(k!==L.view){L.view=k;g.setView({scrollX:v.x,scrollY:v.y,zoom:v.z,rect:[o[0],o[1]+v.ay,v.w,Math.max(1,v.h-v.ay)],originX:v.x0});GLF.n.view++}
    if(L.ph!==v.ph){L.ph=v.ph;g.setPlayhead(v.ph);GLF.n.ph++}}}
/* where the arrangement canvas and the docked engine's canvas are on the page (in CSS px of the zoomed page); read only now and then, never per frame */
function glfOff(){const c=GLE.cv;if(!c)return;const m=c.getBoundingClientRect(),z=ZOOM,o=[Math.round(m.left/z*100)/100,Math.round(m.top/z*100)/100];if(!GLF.off||o[0]!==GLF.off[0]||o[1]!==GLF.off[1])GLF.off=o}
/* the page rectangle of an element in the engine's units */
function glfR(r){const z=ZOOM,q=v=>Math.round(v/z*100)/100;return[q(r.left),q(r.top),q(r.width),q(r.height)]}
/* flat pictures for one layer: what its faces may cover that is not the arrangement. Only changes are passed on (each change rebuilds the flats' blur). */
function glfFlat(L,key,d,sig,seen){seen.add(key);if(L.flats.get(key)===sig)return;L.flats.set(key,sig);L.g.setFlat(key,d);GLF.n.flatSet++}
function glfFlats(L,items,disp,dock){const seen=new Set(),g=L.g;
  for(const f of dock)glfFlat(L,f.k,{rect:f.R,radius:0,color:f.c},f.s,seen);
  for(const f of disp)glfFlat(L,f.k,{rect:f.R,radius:2,source:f.cv},f.s,seen);
  for(const it of items)if(it.lv<L.i){const c=it.bg,a=Math.max(c[3],.85),col=[c[0],c[1],c[2],a];glfFlat(L,'w:'+it.id,{rect:it.R,radius:it.rad,color:col},it.R.join(',')+'|'+it.rad+'|'+col.join(','),seen)}
  for(const k of [...L.flats.keys()])if(!seen.has(k)){L.flats.delete(k);g.removeFlat(k)}}
/* the docked panels and the canvases under the floating glass (read a few times a second, not per frame) */
function glfSlow(n){GLF.slowT=n;glfOff();const dock=[],disp=[],vw=innerWidth,vh=innerHeight,base='rgb('+(getComputedStyle(document.documentElement).getPropertyValue('--gtr2').trim()||'22,28,42')+')';
  for(const id of GLFDOCK){const el=document.getElementById(id);if(!el||!el.getClientRects().length)continue;const r=el.getBoundingClientRect();if(r.width<4||r.height<4||r.right<0||r.bottom<0||r.left>vw||r.top>vh)continue;
    const c=gleCol(el.classList.contains('glsol')?getComputedStyle(el).backgroundColor:base),col=[c[0],c[1],c[2],el.classList.contains('glsol')?1:.85],R=glfR(r);dock.push({k:'d:'+id,R,c:col,s:R.join(',')+'|'+col.join(',')})}
  const cvs=[...document.querySelectorAll('#fxin canvas')];const pr=document.getElementById('prc');if(pr&&!document.body.classList.contains('prfull'))cvs.push(pr);
  for(const cv of cvs){if(!cv.width||!cv.height||!cv.getClientRects().length)continue;const r=cv.getBoundingClientRect();if(r.width<24||r.height<16||r.right<0||r.bottom<0||r.left>vw||r.top>vh)continue;
    const R=glfR(r);if(!cv._glfS)cv._glfS='s:'+(++GLF.seq);disp.push({k:cv._glfS,R,cv,s:R.join(',')+'|'+cv.width+'x'+cv.height,a:R[2]*R[3]})}
  /* at most 12 displays, the largest */
  disp.sort((a,b)=>b.a-a.a);if(disp.length>12)disp.length=12;GLF.dock=dock;GLF.disp=disp}
/* where the backdrop comes from: the rectangle scene; in the overview a small copy of the arrangement canvas; with the piano roll in full screen a small copy of it */
function glfSrc(){return GLE.ovw?'ovw':document.body.classList.contains('prfull')?'pr':'scene'}
function glfSetSrc(L){const s=GLF.src;if(s==='scene'){glfFeed(L,false);return}const cv=s==='ovw'?arr:document.getElementById('prc');if(!cv)return;
  const R=glfR(cv.getBoundingClientRect()),k=s+'|'+R.join(',');if(L.src!==k){L.src=k;L.sig=-1;L.view='';L.g.setBackdrop(cv,{rect:R})}}
/* once per screen frame, from the app's frame loop */
function glfTick(now){const on=GLE.on&&!!GLE.g&&!GLF.fail;if(!on){if(GLF.act||GLF.L.length)glfKill();return}
  const C=glfCands(now),items=[];let vis=0;
  for(const[el,k] of C){if(!glfShown(el))continue;const r=el.getBoundingClientRect();if(r.width<8||r.height<8||r.right<0||r.bottom<0||r.left>innerWidth||r.top>innerHeight)continue;
    const I=glfInfo(el,now);if(I.cs.visibility==='hidden')continue;const op=(+I.cs.opacity)*(I.tcs?+I.tcs.opacity:1);if(!(op>.01))continue;
    if(!el._glf)el._glf='f'+(++GLF.seq);const R=glfR(r);if(k==='tab')R[3]+=14;items.push({el,k,id:el._glf,R,z:I.z,top:I.top,rad:I.rad,op:Math.min(1,op),bg:I.bg,opaque:I.opaque&&k!=='tab',lv:0});vis++}
  GLF.n.tick++;
  if(!vis&&!GLF.act)return;
  if(now-GLF.slowT>250||!GLF.dock)glfSlow(now);
  /* stacking order: z-index, then place in the page */
  items.sort((a,b)=>a.z-b.z||(a.top===b.top?(a.k==='tab')-(b.k==='tab'):(a.top.compareDocumentPosition(b.top)&4?-1:1)));
  /* levels: an element that overlaps an element below it goes one layer above that one. Face mode: one layer per element. */
  const face=GLF.mode==='face',tl=new Map();let nx=0;
  for(let i=0;i<items.length;i++){const it=items[i];if(tl.has(it.top)){it.lv=tl.get(it.top);continue}let k=0;
    if(face)k=it.opaque?-1:nx++;else for(let j=0;j<i;j++){const o=items[j];if(o.top!==it.top&&glfOvl(o.R,it.R))k=Math.max(k,o.lv+1)}
    it.lv=k;tl.set(it.top,k)}
  const max=face?8:GLF.max;GLF.src=glfSrc();
  /* per layer: which faces, where the canvas goes in the page */
  const want=[];for(const it of items){const sol=!it.opaque&&it.lv>=max;if(it.el.classList.contains('glfsol')!==sol){it.el.classList.toggle('glfsol',sol);if(sol)GLF.n.solid++}
    if(it.opaque||it.lv<0||it.lv>=max)continue;(want[it.lv]||(want[it.lv]=[])).push(it)}
  if(GLF.items.length){const now2=new Set(items.map(x=>x.el));for(const it of GLF.items)if(!now2.has(it.el)&&it.el.classList.contains('glfsol'))it.el.classList.remove('glfsol')}
  const st=items.map(it=>it.id+':'+it.lv).join(' ');if(st!==GLF.st){GLF.st=st;GLF.n.regroup++}
  GLF.items=items;let any=false;
  for(let i=0;i<Math.max(want.length,GLF.L.length);i++){const W=want[i]||[];let L=GLF.L[i];
    if(!W.length){if(L&&L.vis){L.vis=false;L.cv.hidden=true;for(const id of L.ids)L.g.removePanel(id);L.ids.clear()}continue}
    if(!L){L=glfLayer(i);if(!L)break}
    any=true;const g=L.g,lo=W[0];
    if(String(lo.z)!==L.z){L.z=String(lo.z);L.cv.style.zIndex=L.z}
    if(L.before!==lo.top||L.cv.nextSibling!==lo.top){L.before=lo.top;if(lo.top.parentElement===document.body)document.body.insertBefore(L.cv,lo.top)}
    /* face mode: the canvas is only as large as its element (plus a margin), moved with it; the backdrop then has to be drawn again on every move */
    if(face){let x0=1e9,y0=1e9,x1=-1e9,y1=-1e9;for(const it of W){x0=Math.min(x0,it.R[0]);y0=Math.min(y0,it.R[1]);x1=Math.max(x1,it.R[0]+it.R[2]);y1=Math.max(y1,it.R[1]+it.R[3])}const x=Math.floor(x0)-2,y=Math.floor(y0)-2,w=Math.ceil((x1-x0+6)/8)*8,h=Math.ceil((y1-y0+6)/8)*8,fk=x+','+y+','+w+','+h;
      if(L.fit!==fk){const o=L.fit;L.fit=fk;L.cv.classList.add('fit');L.cv.style.width=w+'px';L.cv.style.height=h+'px';L.cv.style.transform='translate('+x+'px,'+y+'px)';g.setOrigin(x,y);g.setBounds([0,0,innerWidth/ZOOM,innerHeight/ZOOM]);if(o)GLF.n.move++}}
    else if(L.fit){L.fit=null;L.cv.classList.remove('fit');L.cv.style.width=L.cv.style.height=L.cv.style.transform='';g.setOrigin(0,0);g.setBounds(null)}
    if(!L.vis){L.vis=true;L.cv.hidden=false;L.sig=-1;L.view='';L.ph=null}
    glfSetSrc(L);
    const ids=new Set();W.forEach((it,j)=>{ids.add(it.id);const d={rect:it.R,radius:Math.min(it.rad,Math.min(it.R[2],it.R[3])/2),kind:it.k==='tab'?'window':it.k,opacity:it.op,z:it.k==='tab'?-1:j,visible:true,over:'flats'};
      if(L.ids.has(it.id))g.updatePanel(it.id,d);else{d.id=it.id;g.addPanel(d)}});
    for(const id of L.ids)if(!ids.has(id))g.removePanel(id);L.ids=ids;
    glfFlats(L,items,GLF.disp||[],GLF.dock||[]);
    /* the displays and the piano roll under a face are copied again at most 20 times a second while playing, twice a second when stopped (most displays stand still then);
       the overview and full-screen piano roll backdrop likewise */
    if(now-(L.dT||0)>=(play.on?50:500)){L.dT=now;for(const f of GLF.disp||[])if(L.flats.has(f.k)&&W.some(it=>glfOvl(it.R,f.R))){g.markFlatDirty(f.k);GLF.n.flatDirty++}if(GLF.src!=='scene')g.markDirty()}}
  GLF.act=any}
/* the frame: after the docked engine, each layer draws what changed (free when nothing did) */
function glfRender(now){if(!GLF.act)return;for(const L of GLF.L)if(L&&L.vis)try{L.g.render(now)}catch(e){if(!GLF.err){GLF.err=1;console.error('AudioLab glass engine (floating)',e)}}}
/* the docked engine's scene feed also feeds the layers: the list once per edit, the view and the playhead as uniforms */
{const _gb=gleBuild;gleBuild=function(){const L=_gb.apply(this,arguments);GLF.LL=L;GLF.sig++;return L}}
{const _gf=gleFeed;gleFeed=function(){const r=_gf.apply(this,arguments);try{if(GLE.g&&GLE.on){const dz=(window.devicePixelRatio||1)*ZOOM,P=phCfg(),q=(GLE.lv==='light'?4:2)/V.ppb;
    GLF.vw={x:V.x,y:V.y,z:V.ppb,w:arr.width/dz,h:arr.height/dz,ay:AY,x0:X0,pc:P.c,pw:P.w,ph:Math.round(curDisp()/q)*q};if(GLF.act)for(const L of GLF.L)if(L&&L.vis)glfFeed(L,false)}}catch(e){if(!GLF.err){GLF.err=1;console.error('AudioLab glass engine (floating)',e)}}return r}}
{const _gp=glePh;glePh=function(){const r=_gp.apply(this,arguments);if(GLF.act&&GLF.vw&&GLE.on){const q=(GLE.lv==='light'?4:2)/V.ppb,x=Math.round(curDisp()/q)*q;if(x!==GLF.vw.ph){GLF.vw.ph=x;for(const L of GLF.L)if(L&&L.vis&&GLF.src==='scene'&&L.ph!==x){L.ph=x;L.g.setPlayhead(x);GLF.n.ph++}}}return r}}
/* level, lens and frosting follow the docked panels */
{const _ga=gleApply;gleApply=function(){const r=_ga.apply(this,arguments);try{if(!GLE.on)glfKill();else for(const L of GLF.L)if(L){L.g.setLevel(GLE.lv==='light'?'light':'glass');L.g.setLensPreset(gleLens());L.g.setBlurPreset(gleBlur())}GLF.off=null;GLF.slowT=0}catch(e){console.error('AudioLab glass engine (floating)',e)}return r}}
{const _f0=frame0;frame0=function(now){const r=_f0.apply(this,arguments);try{glfTick(now);glfRender(now)}catch(e){if(!GLF.err){GLF.err=1;console.error('AudioLab glass engine (floating)',e)}}return r}}
addEventListener('resize',()=>{GLF.slowT=0;GLF.off=null});
/* the old SVG lens is not used any more: it makes no filter and no map (the code stays until step 3) */
rfAttach=function(){};
{const _ru=rfUpdate;rfUpdate=function(el){const o=RFX.get(el);if(o){clearTimeout(o.tm);o.tm=0;if(o.v){o.v='';el.style.backdropFilter='';el.style.webkitBackdropFilter=''}}}}
