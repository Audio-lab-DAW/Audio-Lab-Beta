/* ====================== v0.223 (task GS1, glass step 1): the glass engine draws the docked panels ======================
   Plan: docs/glass-engine-plan.md (sections 3.2 to 3.5 are binding), module: docs/glass-engine-module.md, engine source: tools/glass-lab/glass-engine.js (pasted below unchanged).
   One WebGL2 canvas (#glassCv) sits where the old pictures behind the glass sat (before #arr). It draws the finished glass for the docked panels:
   track headers (#hglass), transport (#tr), tab band (#fxband, when it shows) and device panel (#fxglass). Those elements carry no backdrop-filter at any level,
   only their tint, border and content.
   The backdrop is drawn by the engine on the graphics card: lane backgrounds, clips as flat rectangles (body and title band, in the track colour), the playhead.
   The rectangle list is made from the same values drawArr uses and is sent again only after an edit (gleSig notices it); scroll and zoom are one uniform (setView),
   the playhead is one uniform (setPlayhead). No canvas is ever copied or uploaded on this path, so #arrBack is only an empty layer that passes clicks on and
   #arrBlur is not made any more.
   Levels (UI.gl.lv, else from the Light mode slider: Full and Optimised = Glass, Lighter = Light, Lightest = Solid):
     Glass = the engine with the lens; Light = the same engine, lens off, smaller backdrop refreshed 30 times a second; Solid = no engine, solid panels.
   Solid is also what a computer without WebGL2 gets. Lens presets Off, Fine, Apple, Wide (default Wide 45 px), blur presets Light (default), Regular, Heavy.
   The docked panels have square corners, so they get the engine's square lens (2.2), and only on the edges that have the open arrangement beyond them (gleEdges).
   The old glass code (rfAttach, rfBuild, rfMap, rfStyle, the feImage lens) is still there for windows, sheets and menus (glass step 2 replaces it); it no longer runs for the docked panels.
   The engine is drawn from the app's frame loop, so the background freeze (task AO) stops it together with everything else.
   Same step, from the plan's quick wins: the playhead is its own layer (#arrPhW: a thin canvas moved with a transform), so a frame in which only the playhead moved
   draws nothing on the arrangement canvas and needs no snapshot of it; Follow centre no longer redraws the arrangement in frames where the view did not move. */
/*GLASS-ENGINE*/
const GLE={g:null,cv:null,on:false,lv:'solid',fail:'',sig:null,lay:'',n:{scene:0,view:0,ph:0,sync:0,made:0}};
const GLIDS=['hglass','tr','fxglass','fxband'];
function gleOpt(){const o=UI.gl;return o&&typeof o==='object'?o:{}}
/* the level for the docked panels: a choice made by hand, else what the Light mode slider says. Lightest keeps everything solid. */
function gleLevel(){if(GLE.fail)return'solid';const e=pmEff();if(e===0)return'solid';const l=gleOpt().lv;return l==='glass'||l==='light'||l==='solid'?l:e>=2?'glass':'light'}
function gleLens(){const l=gleOpt().lens;return l==='off'||l==='fine'||l==='apple'||l==='wide'?l:'wide'}
function gleBlur(){const b=gleOpt().blur;return b==='light'||b==='regular'||b==='heavy'?b:'light'}
function gleSet(k,v){UI.gl={...gleOpt(),[k]:v};saveUI();gleApply()}
/* any CSS colour as [r,g,b,a] from 0 to 1 (the theme colours are hsl() texts); the same text gives the same array, so the engine can tell that nothing changed */
const GLC=new Map();let GLCX=null;
function gleCol(c){let v=GLC.get(c);if(v)return v;if(!GLCX)GLCX=document.createElement('canvas').getContext('2d');GLCX.fillStyle='#000';GLCX.fillStyle=c;const s=String(GLCX.fillStyle);
  if(s[0]==='#'){const n=parseInt(s.slice(1,7),16);v=[(n>>16&255)/255,(n>>8&255)/255,(n&255)/255,1]}else{const m=(s.match(/[\d.]+/g)||[0,0,0]).map(Number);v=[m[0]/255,m[1]/255,m[2]/255,m[3]==null?1:m[3]]}
  if(GLC.size>600)GLC.clear();GLC.set(c,v);return v}
function gleStr(h,s){s=String(s);for(let i=0;i<s.length;i++)h=(Math.imul(h^s.charCodeAt(i),0x9E3779B1)+0x7F4A7C15)|0;return h}
/* one number that changes whenever the rectangle list would: tracks, rows, clips, colours, mute, selection, theme. One pass over the clips, no texts made. */
function gleSig(){let h=0x2545F491;const mix=x=>{h=(Math.imul(h^(x|0),0x9E3779B1)+0x7F4A7C15)|0},P=phCfg();
  mix(V.th*16);mix(TOTH);mix(UI.clipA??36);mix(UI.lite?1:2);mix(S.tracks.length);mix(Math.max(songEnd(),loopEnd())*256);mix(BOOTF==null?-1:BOOTF*4096);mix(P.w*16);
  h=gleStr(h,P.c);h=gleStr(h,TH.bg);h=gleStr(h,TH.lane0);h=gleStr(h,TH.lane1);h=gleStr(h,TH.laneSel);h=gleStr(h,(TH.cmix||'')+'|'+(TH.hd||'')+'|'+(TH.hdk??''));
  for(let i=0;i<S.tracks.length;i++){const t=S.tracks[i];if(HIDT.has(t)){mix(-7);continue}mix(TRY[i]);mix(t.id===selT?5:6);mix(t.mute&&!t.solo?3:4);h=gleStr(h,t.color);
    const pm=PREVMAP&&(!PREVT||PREVT.has(t.id));for(const c of t.clips){mix((pm?PREVMAP(c.start):c.start)*1024);mix(c.len*1024);mix((c.mute?1:0)|(c.id===selC||SELCS.has(c.id)?2:0))}}
  return h}
/* the rectangle list, from the same values drawArr and drawClip use. Clip x and width are in beats and y in the unscrolled track stack, so scroll and zoom never need a new list. */
function gleBuild(){const lanes=[],clips=[],CA=(UI.clipA??36)/100,th=V.th,top=th>=40?14:0,BIG=1e6,dk=[8/255,9/255,12/255];
  for(let i=0;i<S.tracks.length;i++){const t=S.tracks[i];if(HIDT.has(t))continue;const y=TRY[i],tm=t.mute&&!t.solo,pm=PREVMAP&&(!PREVT||PREVT.has(t.id));
    lanes.push({y,h:th,color:gleCol(t.id===selT?TH.laneSel:(i%2?TH.lane1:TH.lane0))});
    for(const c of t.clips){if(BOOTF!=null&&hashU(c.id)>=BOOTF)continue;const mu=c.mute||tm,sel=c.id===selC||SELCS.has(c.id),col=mu?'#5b5f66':(TH.cmix?thMix(t.color):t.color),q=gleCol(col),x=pm?PREVMAP(c.start):c.start,a=mu?CA*.45:Math.min(1,CA+(sel?.12:0));
      /* body: the dark underlay and the colour on top of it, worked out as one rectangle */
      if(UI.lite)clips.push({x,y:y+2,w:c.len,h:th-5,color:q,alpha:a,titleH:0});
      else{const A=1-.7*(1-a),k=.3*(1-a);clips.push({x,y:y+2,w:c.len,h:th-5,color:[(dk[0]*k+q[0]*a)/A,(dk[1]*k+q[1]*a)/A,(dk[2]*k+q[2]*a)/A,1],alpha:A,titleH:0})}
      if(top&&TH.hd!=='none')clips.push({x,y:y+2,w:c.len,h:14,color:gleCol(sel?shade(col,-.08):shade(col,TH.hdk??-.3)),alpha:mu?.5:.92,titleH:0})}}
  /* below the last track and after the end of the song the arrangement is darker */
  lanes.push({y:TOTH,h:BIG,color:[0,0,0,.25]});
  clips.push({x:Math.max(songEnd(),loopEnd()),y:-BIG,w:BIG,h:2*BIG,color:[0,0,0,1],alpha:.42,titleH:0});
  return{lanes,clips}}
/* after a full drawing of the arrangement: a new list only when something in it changed, else just the view */
function gleFeed(){const g=GLE.g;if(!g||!GLE.on)return;const dz=(window.devicePixelRatio||1)*ZOOM,w=arr.width/dz,h=arr.height/dz,sig=gleSig();
  if(sig!==GLE.sig){GLE.sig=sig;const L=gleBuild(),P=phCfg();g.setBackdropColor(gleCol(TH.bg));g.setScene({lanes:L.lanes,clips:L.clips,bg:gleCol(TH.bg),titleH:0,bodyAlpha:1,playheadColor:gleCol(P.c),playheadW:P.w});GLE.n.scene++}
  g.setView({scrollX:V.x,scrollY:V.y,zoom:V.ppb,rect:[0,AY,w,Math.max(1,h-AY)],originX:X0});GLE.n.view++;glePh();
  /* the header glass follows the track rows: its place comes from the numbers drawArr just worked out, without asking the page */
  {const on=HGR.on&&!GLE.hgOff&&!document.body.classList.contains('ovw'),x=UI.tracksRight?w-HDRW:0,R=[x-1,HGR.t-1,HDRW+2,HGR.b-HGR.t+2];
   if(g.hasPanel('hglass'))g.updatePanel('hglass',on?{rect:R,visible:true,edges:gleEdges('hglass')}:{visible:false});else if(on)g.addPanel({id:'hglass',rect:R,radius:0,kind:'docked',tintAmount:0,edges:gleEdges('hglass')})}}
/* which edges of a docked panel bend the picture: only those that have the open arrangement beyond them (engine 2.2, plan 3.7). The track headers: the edge towards the arrangement.
   The panels across the window: the top or bottom edge that borders the part of the arrangement canvas that is not cut away (GB.t and GB.b from gbLayout). */
function gleEdges(id,y,h){if(id==='hglass')return UI.tracksRight?'l':'r';const T=GB.t||0,Bt=(GB.ah||0)-(GB.b||0);let e='';if(y>T+1&&y<=Bt+1)e+='t';if(y+h>=T-1&&y+h<Bt-1)e+='b';return e||'none'}
/* the playhead under the glass: one uniform. It is frosted there, so it moves in steps of 2 px (4 px at Light) and the backdrop is not redrawn for less. */
function glePh(){const g=GLE.g;if(!g||!GLE.on)return;const q=(GLE.lv==='light'?4:2)/V.ppb;g.setPlayhead(Math.round(curDisp()/q)*q);GLE.n.ph++}
/* is something else than the arrangement behind this panel? Then the engine has no picture for it and the panel is solid (glass over the piano roll comes with glass step 2). */
function gleCovered(id){const B=document.body.classList;if(B.contains('prfull'))return true;if(id==='fxglass'||id==='fxband'){const fx=document.getElementById('fx');if(!fx||fx.classList.contains('popped')||fx.classList.contains('prdev')||B.contains('split'))return true}return false}
/* where the docked panels are: one face per panel, 1 px larger than the element so that no seam shows where the arrangement canvas is cut away */
function gleSync(){const g=GLE.g,on=GLE.on&&!!g&&!!GLE.cv,m=on?GLE.cv.getBoundingClientRect():null,z=ZOOM,r2=v=>Math.round(v*100)/100;GLE.n.sync++;
  for(const id of GLIDS){const el=document.getElementById(id);if(!el)continue;let face=false;const can=on&&m.width>4&&m.height>4&&!gleCovered(id)&&!(id==='hglass'&&document.body.classList.contains('ovw'));
    if(id==='hglass')GLE.hgOff=!can;
    if(can&&el.offsetHeight>2&&el.offsetWidth>2){const r=el.getBoundingClientRect(),x0=Math.max(r.left,m.left),y0=Math.max(r.top,m.top),x1=Math.min(r.right,m.right),y1=Math.min(r.bottom,m.bottom);
      if(x1-x0>2&&y1-y0>2){face=true;const R=[r2((x0-m.left)/z)-1,r2((y0-m.top)/z)-1,r2((x1-x0)/z)+2,r2((y1-y0)/z)+2],E=gleEdges(id,R[1]+1,R[3]-2);if(g.hasPanel(id))g.updatePanel(id,{rect:R,visible:true,edges:E});else g.addPanel({id,rect:R,radius:0,kind:'docked',tintAmount:0,edges:E})}}
    if(!face&&g&&g.hasPanel(id))g.updatePanel(id,{visible:false});
    /* no engine face behind it: the panel is solid */
    if(el.classList.contains('glsol')===face)el.classList.toggle('glsol',!face)}}
function gleKill(){if(GLE.g){try{GLE.g.destroy()}catch(e){}GLE.g=null}if(GLE.cv){GLE.cv.remove();GLE.cv=null}}
function gleMake(){if(GLE.g||GLE.fail)return;const c=document.createElement('canvas');c.id='glassCv';c.setAttribute('aria-hidden','true');arr.parentElement.prepend(c);let g=null;
  try{g=AudioLabGlass.create(c,{level:'glass',lens:gleLens(),blur:gleBlur(),maxDpr:2,kinds:{docked:{shadow:0,tint:0,fixed:true,edges:'auto'}},
    onFallback:(on,why)=>{GLE.lost=!!on&&why==='lost'}})}catch(e){console.warn('AudioLab glass engine: '+(e&&e.message||e))}
  /* no WebGL2 (or the shaders did not build): no engine at all, the docked panels are solid */
  if(!g||g.mode!=='gl'){GLE.fail=(g&&g.reason)||'no webgl2';try{if(g)g.destroy()}catch(e){}c.remove();return}
  GLE.g=g;GLE.cv=c;GLE.n.made++}
function gleApply(){let lv=gleLevel();const B=document.body.classList;
  if(lv==='solid')gleKill();else{gleMake();const g=GLE.g;if(g){g.setLevel(lv);g.setLensPreset(gleLens());g.setBlurPreset(gleBlur());g.setBackdropColor(gleCol(TH.bg||'#0b0c10'))}else lv='solid'}
  const on=!!GLE.g&&lv!=='solid',ch=on!==GLE.on||lv!==GLE.lv;GLE.on=on;GLE.lv=lv;B.toggle('gle',on);B.toggle('gls',!on);
  document.documentElement.style.setProperty('--gad',(1-(UI.trans??50)/100).toFixed(3));
  if(ch){GLE.sig=null;GLE.lay='';GLE.ovw=0}
  try{gleSync();GB.lt=0;gbCopy()}catch(e){}dirty=true;try{gleUi()}catch(e){}}

/* ---- the old pictures behind the glass are not made any more ---- */
/* the arrangement canvas is still cut away under the docked glass (gbLayout, gbClip, #arrCol), now so that the engine's canvas shows there */
gbOn=function(){return GLE.on};
{const _fp=fxPic;fxPic=function(el){if(el&&(el.id==='tr'||el.id==='hglass'))return GLE.on&&!el.classList.contains('glsol');return _fp.apply(this,arguments)}}
{const _gl=gbLayout;gbLayout=function(){try{gleSync()}catch(e){}const r=_gl.apply(this,arguments);/* again after the layout: which edges are free depends on what was cut away */try{if(GLE.on)gleSync()}catch(e){}return r}}
/* #arrBack stays as an empty 2 x 2 layer that passes clicks on to the arrangement; nothing is copied into it */
gbCopy=function(fast){const n=performance.now();GB.last=n;GB.stale=false;let ok;if(fast&&n-(GB.lt||0)<250)ok=GB.ok;else{ok=gbLayout();GB.lt=n;GB.ok=ok}
  if(ok&&GB.cv&&GB.cv.width!==2){GB.cv.width=2;GB.cv.height=2}abDraw();elSoon()};
/* #arrBlur (the blurred picture) is gone */
abDraw=function(){const c=ABL.cv;if(c&&c.width){c.width=0;c.height=0;c.style.display='none'}if(ABL.q&&ABL.q.width){ABL.q.width=0;ABL.q.height=0}ABL.w=0;const B=document.body.classList;if(B.contains('fxpic'))B.remove('fxpic')};
/* the SVG lens never runs for the docked panels (they have no backdrop-filter at any level) */
{const _ru=rfUpdate;rfUpdate=function(el){if(el&&(el.id==='hglass'||el.id==='tr'||el.id==='fxband'||el.id==='fxglass')){const o=RFX.get(el);if(o){clearTimeout(o.tm);o.tm=0;if(o.v){o.v='';el.style.backdropFilter='';el.style.webkitBackdropFilter=''}}return}return _ru.apply(this,arguments)}}
/* live edge light for windows, sheets and menus: it used to read the blurred picture. Now it reads a tiny copy of the arrangement, made only while such a panel is open (at most 11 times a second).
   The docked panels get their rim light from the engine. */
elTick=function(){EL.t=performance.now();const f=fxGet(),e=(UI.edge??60)/100;if(!f.edge||e<=0||document.hidden||arr.width<8||arr.height<8){elClear();return}
  const L=[];for(const el of document.querySelectorAll('.lg,.fwin,#ctxm,.modal>div')){if(el.id==='gpPane'||el.id==='hglass'||el.id==='tr'||!el.getClientRects().length)continue;const r=el.getBoundingClientRect();if(r.width<8||r.height<8)continue;L.push([el,r])}
  if(!L.length){elClear();return}
  if(!EL.cv){EL.cv=document.createElement('canvas');EL.cv.width=EL.w;EL.cv.height=EL.h;EL.g=EL.cv.getContext('2d',{willReadFrequently:true})}
  /* two steps, so that only the small picture is read back from the graphics card, never the arrangement itself */
  const s=EL.sm||(EL.sm=document.createElement('canvas'));if(s.width!==384){s.width=384;s.height=216}const sg=s.getContext('2d');sg.imageSmoothingEnabled=true;sg.imageSmoothingQuality='low';sg.drawImage(arr,0,0,384,216);
  EL.g.clearRect(0,0,EL.w,EL.h);EL.g.imageSmoothingEnabled=true;EL.g.imageSmoothingQuality='medium';EL.g.drawImage(s,0,0,EL.w,EL.h);
  const Sm=elSampler(EL.g.getImageData(0,0,EL.w,EL.h).data,EL.w,EL.h,arr.getBoundingClientRect()),seen=new Set();
  for(const[el,r] of L){const st=elGrad(r,Sm,e);if(st){seen.add(el);EL.set.add(el);if(el._elb!==st){el._elb=st;el.style.setProperty('--elb',st)}}}
  for(const el of[...EL.set])if(!seen.has(el)){el.style.removeProperty('--elb');el._elb='';EL.set.delete(el)}};
{const _at=applyTrans;applyTrans=function(){const r=_at.apply(this,arguments);try{gleApply()}catch(e){console.error('AudioLab glass engine',e)}return r}}
/* moving the Light mode slider or its switch puts the docked panels back on the slider's own level */
{const _ss=pmSetStop;pmSetStop=function(){if(UI.gl&&UI.gl.lv)UI.gl={...UI.gl,lv:null};return _ss.apply(this,arguments)}}
{const _so=pmSetOn;pmSetOn=function(){if(UI.gl&&UI.gl.lv)UI.gl={...UI.gl,lv:null};return _so.apply(this,arguments)}}
/* the engine draws once per screen frame from the app's own loop: free when nothing changed, and stopped by the background freeze like every other frame */
{const _f0=frame0;frame0=function(now){const r=_f0.apply(this,arguments);const g=GLE.g;if(g)try{g.render(now)}catch(e){if(!GLE.err){GLE.err=1;console.error('AudioLab glass engine',e)}}return r}}

/* ---- the playhead as its own layer ----
   #arrPhW lies over the arrangement canvas with the same cut-out. #arrPhC holds the playhead line and the Follow button; it is painted only when their look changes
   and moved with a transform, in whole screen pixels so that it stays sharp. #arrPhJ is the small arrow at the edge when the playhead is out of view.
   The arrangement canvas itself no longer contains the playhead, so a frame in which only the playhead moved leaves that canvas alone (before: the whole canvas was
   copied back from a snapshot on every such frame, and the snapshot was made after every full drawing). The overview keeps the old way. */
const PHL={on:true,w:null,c:null,j:null,k:'',tx:'',jk:'',jt:'',cp:null,wh:'',pad:80,n:{fast:0,paint:0,move:0}};
function phlMake(){if(PHL.w&&PHL.w.isConnected)return;const w=document.createElement('div');w.id='arrPhW';w.setAttribute('aria-hidden','true');w.innerHTML='<canvas id="arrPhC" width="1" height="1"></canvas><canvas id="arrPhJ" width="1" height="1"></canvas>';arr.after(w);PHL.w=w;PHL.c=w.firstChild;PHL.j=w.lastChild;PHL.k=PHL.tx=PHL.jk=PHL.jt='';PHL.cp=null}
{const _ph=arrPH;arrPH=function(g,w,h){
  if(!PHL.on||OVW.on||OVW.a||PHL.keep||(g&&g.canvas!==arr)){if(PHL.w&&PHL.w.style.display!=='none')PHL.w.style.display='none';PHL.wh='';return _ph.apply(this,arguments)}
  phlMake();const W=PHL.w,c=PHL.c,j=PHL.j,P=phCfg(),px=X0+(curDisp()-V.x)*V.ppb,fe=performance.now()-PHF,fl=(fe<55)||(fe>=115&&fe<170),bw=FBW(),vis=px>=X0-1&&px<=w+2,d=(window.devicePixelRatio||1)*ZOOM;
  if(W.style.display==='none')W.style.display='';
  if(PHL.cp!==GB.clip){PHL.cp=GB.clip;W.style.clipPath=GB.clip||''}
  if(vis&&fe<200)dirty=true;
  FB=px>=X0-6&&px<=X0+arrW-4?{x:Math.min(px+P.w+4,X0+arrW-bw-2),y:TY+3,w:bw,h:17}:null;FBJ=null;
  if(!FB){const left=px<X0,xx=left?X0+3:X0+arrW-17;FBJ={x:xx,y:TY+4,w:14,h:15,left}}
  if(vis||FB){const pad=PHL.pad,H=Math.max(1,Math.round(h-TY)),Wc=Math.ceil(pad+Math.max(P.w+6+bw,14)+8),rel=FB?Math.round((FB.x-px)*4)/4:0,k=[Wc,H,d,P.s,P.c,P.w,vis?1:0,FB?rel:'n',UI.follow?1:0,fl?1:0].join('|');
    if(k!==PHL.k){PHL.k=k;const bw2=Math.max(1,Math.round(Wc*d)),bh2=Math.max(1,Math.round(H*d));if(c.width!==bw2||c.height!==bh2){c.width=bw2;c.height=bh2}c.style.width=Wc+'px';c.style.height=H+'px';
      const x=c.getContext('2d');x.setTransform(d,0,0,d,0,0);x.clearRect(0,0,Wc,H);
      if(vis){if(fl){x.fillStyle='rgba(120,255,190,.55)';x.fillRect(pad-1.5,0,4.5+P.w,H)}phDraw(x,pad,0,H,fl?'#ffffff':P.c,P.s,P.w)}
      if(FB)fbDraw(x,{x:pad+rel,y:3,w:bw,h:17},P);PHL.n.paint++}
    const tx=Math.round((px-pad-(SUBAP||0))*d)/d,ts='translate3d('+tx+'px,'+TY+'px,0)';
    if(ts!==PHL.tx){PHL.tx=ts;c.style.transform=ts;PHL.n.move++}
    if(c.style.display==='none')c.style.display=''}
  else if(c.style.display!=='none')c.style.display='none';
  if(FBJ){const jk=FBJ.left+'|'+d;if(jk!==PHL.jk){PHL.jk=jk;j.width=Math.round(14*d);j.height=Math.round(15*d);j.style.width='14px';j.style.height='15px';const x=j.getContext('2d');x.setTransform(d,0,0,d,0,0);x.clearRect(0,0,14,15);
      x.fillStyle='rgba(62,207,142,.85)';rr(x,0,0,14,15,3);x.fill();x.fillStyle='#04140c';x.beginPath();if(FBJ.left){x.moveTo(3,7.5);x.lineTo(9.5,3);x.lineTo(9.5,12)}else{x.moveTo(11,7.5);x.lineTo(4.5,3);x.lineTo(4.5,12)}x.fill()}
    const js='translate3d('+FBJ.x+'px,'+FBJ.y+'px,0)';if(js!==PHL.jt){PHL.jt=js;j.style.transform=js}if(j.style.display==='none')j.style.display=''}
  else if(j.style.display!=='none')j.style.display='none';
  if(g)PHL.wh=arr.width+'x'+arr.height}}
/* no snapshot of the arrangement is needed while the playhead has its own layer (the overview still uses one) */
{const _as=arrSnap;arrSnap=function(){if(PHL.on&&!OVW.on&&!OVW.a&&!PHL.keep){ARRWH=null;return}return _as.apply(this,arguments)}}
/* the overview fades from and to a picture of the arrangement: it gets that picture when it is entered and left, as before */
{const _oe=ovwEnter;ovwEnter=function(){if(!OVW.on&&PHL.on)try{ARRC=snapTo(arr,ARRC);ARRWH=arr.width+'x'+arr.height}catch(e){}return _oe.apply(this,arguments)}}
{const _ol=ovwLeave;ovwLeave=function(){PHL.keep=1;try{return _ol.apply(this,arguments)}finally{PHL.keep=0}}}
{const _d=drawArr;drawArr=function(ph){
  if(ph&&PHL.on&&PHL.wh===arr.width+'x'+arr.height&&!REC.on&&!OVW.on&&!OVW.a){/* only the playhead moved: its layer and one uniform for the glass, nothing else */
    DPX=(window.devicePixelRatio||1)*ZOOM;const ww=arr.width/DPX;arrPH(null,ww,arr.height/DPX);tmFlag(X0+(curDisp()-V.x)*V.ppb+phCfg().w/2,ww);glePh();PHL.n.fast++;return}
  const g=GLE.g,ov=OVW.on||!!OVW.a,f0=OVW.full,r=_d.apply(this,arguments);
  try{if(OVW.on||OVW.a||ov){/* the overview is another picture than the track rows: the glass takes a small (quarter-size) copy of it, only when it was painted again */
      if(PHL.w&&PHL.w.style.display!=='none'&&(OVW.on||OVW.a)){PHL.w.style.display='none';PHL.wh=''}
      if(g&&GLE.on){if(OVW.on||OVW.a){if(!GLE.ovw){GLE.ovw=1;g.setBackdrop(arr)}if(OVW.full!==f0||!ph)g.markDirty()}}}
    if(!OVW.on&&!OVW.a){if(GLE.ovw){GLE.ovw=0;if(g)g.setBackdrop(null);GLE.sig=null}gleFeed()}}
  catch(e){if(!GLE.err){GLE.err=1;console.error('AudioLab glass engine',e)}}return r}}

/* ---- Settings, Performance: the level for the docked panels, the lens and the blur ---- */
const GLTX={lv:[['glass','Glass','Glass: the docked panels (track headers, transport bar, devices) are frosted glass with a lens at the edges, drawn by the glass engine on the graphics card.'],['light','Light','Light: the same glass without the lens, from a smaller picture behind it that is refreshed 30 times a second. Costs less.'],['solid','Solid','Solid: no glass on the docked panels. Costs nothing. Also used when this computer cannot run the glass engine.']],
 lens:[['off','Off','No bending at the edges.'],['fine','Fine','A thin band, up to 12 px.'],['apple','Apple','The width Apple uses, up to 20 px.'],['wide','Wide','A wide band, up to 45 px. The standard.']],
 blur:[['light','Light','Light frosting. The standard, and the cheapest.'],['regular','Regular','Stronger frosting.'],['heavy','Heavy','The strongest frosting.']]};
function gleUi(){const sec=document.querySelector('#setBody section[data-page=perf]');if(!sec)return;let box=sec.querySelector('#glBox');
  if(!box){const seg=k=>`<div class="seg glseg" data-k="${k}" role="group">`+GLTX[k].map(([v,n,t])=>`<button type="button" data-v="${v}" title="${t}">${n}</button>`).join('')+'</div>',
      row=(k,ic,t,tip)=>`<div class="pmr glr" data-pr="gl_${k}" title="${tip}"><span class="pic">${fxSvg(ic)}</span><b class="pmq">${t}</b>${seg(k)}</div>`,first=sec.querySelector('.pmh');if(!first)return;
    const h=document.createElement('div');h.className='pmh';h.textContent='Docked panels: track headers, transport bar, devices';
    box=document.createElement('div');box.className='pmlist';box.id='glBox';
    box.innerHTML=row('lv','back','Glass level','How the docked panels are drawn. It follows the Light mode slider (Full effects and Optimised: Glass, Lighter: Light, Lightest: Solid) until you pick one here.')+
      row('lens','refr','Lens','How wide the band at the edge of the glass is that bends the picture behind it. Only at the level Glass.')+
      row('blur','blur','Frosting','How strongly the glass frosts what is behind it.')+'<p class="glnote" id="glNote" role="status"></p>';
    first.before(h,box);
    box.addEventListener('click',e=>{const b=e.target.closest('button[data-v]');if(!b||b.disabled)return;gleSet(b.parentElement.dataset.k,b.dataset.v);try{pmSync()}catch(x){}})}
  const lv=GLE.lv,min=pmEff()===0,cur={lv,lens:gleLens(),blur:gleBlur()};
  for(const s of box.querySelectorAll('.glseg')){const k=s.dataset.k;for(const b of s.children){b.classList.toggle('on',b.dataset.v===cur[k]);b.setAttribute('aria-pressed',b.dataset.v===cur[k]);
    b.disabled=k==='lv'?(b.dataset.v!=='solid'&&(min||!!GLE.fail)):k==='lens'?lv!=='glass':lv==='solid'}}
  for(const r of box.querySelectorAll('.glr')){const k=r.dataset.pr.slice(3);r.classList.toggle('on',k==='lv'?lv!=='solid':k==='lens'?lv==='glass'&&cur.lens!=='off':lv!=='solid');r.classList.remove('dis')}
  const hand=!!gleOpt().lv&&!min&&!GLE.fail;
  box.querySelector('#glNote').textContent=GLE.fail?'Solid: this computer cannot run the glass engine (no WebGL2 graphics), so the docked panels are solid.':min?'Lightest keeps every panel solid. Move the slider up to use the glass.':
    (lv==='solid'?'Solid: no glass on the docked panels.':lv==='light'?'Light: the glass engine without the lens.':'Glass: the glass engine with the lens.')+(hand?' Picked here; moving the Light mode slider puts it back on the slider.':' Follows the Light mode slider.')}
{const _ps=pmSync;pmSync=function(){const r=_ps.apply(this,arguments);try{gleUi()}catch(e){}return r}}
