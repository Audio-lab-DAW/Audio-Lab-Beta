#!/usr/bin/env python3
"""Task UV-2 (lane O, view engine): S14 tiled arrangement, part a (the 2D arrangement canvas).
Run on a fresh index.html that already has UV-1: python3 tools/design-lab/uv/uv_2.py [index.html]. Every anchor must occur exactly once.
Lane A's drawArr, drawClipC and the other drawers are not edited: drawArr, arrSnap and snapTo are wrapped."""
import sys
P = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
s = open(P, encoding='utf-8').read()
assert 'task UV-1 (lane O' in s, 'UV-1 must be in this file first'
assert 'task UV-2 (lane O' not in s, 'UV-2 is already in this file'

def rep(old, new, cnt=1):
    global s
    n = s.count(old)
    assert n == cnt, (n, old[:120])
    s = s.replace(old, new)

# the anchors the wrapper relies on (lane A's code, read only): drawArr's preamble and its one call of arrSnap
for a in ["function drawArr(phOnly){DPX=(window.devicePixelRatio||1)*ZOOM;",
          "const{g,w,h}=fit(arr);X0=UI.tracksRight?0:HDRW;TY=$('#dockT').offsetHeight;BY=$('#dockB').offsetHeight;AY=TY+RUL+SECH+TMPH();arrW=Math.max(10,w-HDRW);laneH=Math.max(40,h-AY-BY);",
          "if(play.on&&UI.follow&&(UI.followMode==='center'||UI.followMode==='stay'))ARRWH=null;else arrSnap();arrPH(g,w,h);",
          "function arrSnap(){ARRC=snapTo(arr,ARRC);ARRWH=arr.width+'x'+arr.height}"]:
    assert s.count(a) == 1, a[:80]

JS = r"""/* ---------- task UV-2 (lane O, view engine; the user's UX1 pick S14: tiled arrangement), part a ----------
   The arrangement keeps the picture it drew last (ARRC, lane A's own snapshot without the playhead) and, when only the view moved,
   shifts it by whole device pixels and lets lane A's drawArr paint only what is new: the strip that scrolled in, the bands outside the
   scrolling area (ruler, sections, track header column, the bottom dock), the master lane (it samples per screen column), clips that
   cross the left edge (their names stay in view), empty tracks' hints and the track colour stripe. When nothing moved but clips changed
   (an edit in the piano roll, a nudge, a selection, the hover), only those clips' boxes (old and new) are painted again.
   Lane A's code runs unchanged under a clip region: what it draws is never changed, only where the pixels are kept.
   Anything else that changed (a setting, the theme, the tracks, the loop, a drag with its ghosts, recording, the zoom) draws in full.
   UV.rest ms after the last tiled frame the arrangement is drawn once in full, so at rest every pixel is a fresh drawing.
   The picture kept is the canvas itself (the playhead has its own layer, PHL), or lane A's snapshot ARRC when that layer is off.
   On only where a graphics card draws the canvas (UVT.on 'auto', uvGpu): on a software renderer the copies cost more than they save.
   Hooks: UV_HOOKS.bump() for lane A (any drawing change that the signature below cannot see: drop the kept picture);
   UV_HOOKS.tiles() = what the last frame drew ({mode:'full'|'shift'|'edit', dx, dy in device px, rects [[x,y,w,h]...]}) for the glass engine (part b). */
const UVT={why:'',on:'auto',gpu:null,bb:null,bbOk:'',base:null,clip:0,force:0,tm:0,insnap:0,bad:0,last:{mode:'full',dx:0,dy:0,rects:null},n:{full:0,shift:0,edit:0},px:{drawn:0,all:0},maxF:.6,sticky:4};
UV_HOOKS.bump=()=>{UV.ver++;UVT.base=null;dirty=true};
UV_HOOKS.tiles=()=>UVT.last;
/* what decides the whole picture, besides the view's position: any change draws in full */
function uvSig(w,h){const L=typeof loopShow==='function'?loopShow():null,T=S.tracks,o=[UV.ver,w,h,arr.width,arr.height,DPX,X0,AY,TY,BY,HDRW,arrW,V.ppb,V.th,TOTH,LH,TRY.join(','),selT,T.length,songEnd(),
  L?L.a+':'+L.b+':'+L.on:0,S.bpm,UI.lite,UI.clipA,UI.gridB,UI.subTicks,UI.bars4,UI.tempoLane,UI.mapView,UI.tracksRight,TH.bg,TH.lane0,TH.lane1,TH.laneSel,TH.under,thUnder.k,
  SELR?JSON.stringify(SELR):0,(S.sections||[]).length,SELCS.size,BOOTF,!!PREVMAP,!!CAPDRAG,!!(typeof FDRAG!=='undefined'&&FDRAG),!!RS,!!ad,REC.on];
  for(const t of T)o.push(t.id,t.color,t.mute,t.solo,t.kind,t.fold,t.lanes?t.lanes.join('/'):'',HIDT.has(t)?1:0,t.clips.length?1:0);return o.join('|')}
/* the clips that can be on screen: id -> [x,y,w,h,signature] in content units (the box on screen is x-V.x*V.ppb, y-V.y) */
function uvClips(w,h,vx,vy){const m=new Map(),T=S.tracks;
  for(let i=0;i<T.length;i++){const t=T[i];if(HIDT.has(t))continue;const cy=AY+(TRY[i]??i*V.th),y=cy-vy;if(y>h||y+V.th<AY)continue;
    for(const c of t.clips){const cx=X0+c.start*V.ppb,x=cx-vx*V.ppb,cw=c.len*V.ppb;if(x>w||x+cw<0)continue;
      m.set(c.id,[cx,cy+2,cw,V.th-5,clipSig(t,c)+'|'+(c.id===selC||SELCS.has(c.id))+'|'+(c.id===hovC),!!c.notes,t])}}
  return m}
/* device-pixel rectangles, clipped to the canvas */
function uvR(a,x,y,w,h,D,W,H){const x0=Math.max(0,Math.floor(x*D)),y0=Math.max(0,Math.floor(y*D)),x1=Math.min(W,Math.ceil((x+w)*D)),y1=Math.min(H,Math.ceil((y+h)*D));if(x1>x0&&y1>y0)a.push([x0,y0,x1-x0,y1-y0])}
function uvArea(rs){let a=0;for(const r of rs)a+=r[2]*r[3];return a}
function uvDedup(rs){const k=new Set(),o=[];for(const r of rs){const s=r.join(',');if(!k.has(s)){k.add(s);o.push(r)}}return o}
/* decide, before lane A's drawArr paints: full, shift (the view moved) or edit (clips changed); sets the clip region for the last two */
function uvPrep(){UVT.last={mode:'full',dx:0,dy:0,rects:null};
  DPX=(window.devicePixelRatio||1)*ZOOM;const{g,w,h}=fit(arr);X0=UI.tracksRight?0:HDRW;TY=$('#dockT').offsetHeight;BY=$('#dockB').offsetHeight;AY=TY+RUL+SECH+TMPH();arrW=Math.max(10,w-HDRW);laneH=Math.max(40,h-AY-BY);
  if(!initFit){UVT.why='fit';return null}clampV();layoutRows();
  const D=(window.devicePixelRatio||1)*ZOOM,W=arr.width,H=arr.height,sig=uvSig(w,h),cl=uvClips(w,h,V.x,V.y),pre={X0,AY,TY,BY,arrW,w,h};
  /* the picture kept: while the playhead has its own layer (PHL) the canvas holds no playhead: an edit paints over the canvas itself,
     a scroll copies from UVT.bb (a copy taken after frames that moved; copying the canvas onto itself costs three times as much). Else lane A's snapshot ARRC. */
  const own=typeof PHL==='object'&&PHL.on&&!PHL.keep,src=own?(UVT.bbOk===W+'x'+H?UVT.bb:arr):(ARRC&&ARRWH===W+'x'+H?ARRC:null);
  const B=UVT.base,ok=(UVT.on===true||(UVT.on==='auto'&&uvGpu()))&&!UVT.bad&&!UVT.force&&B&&B.S===S&&B.sig===sig&&B.wh===W+'x'+H&&src&&!(typeof OVW==='object'&&(OVW.on||OVW.a))&&!(play.on&&UI.follow&&(UI.followMode==='center'||UI.followMode==='stay'));
  UVT.why=!ok?(!B?'nobase':B.sig!==sig?'sig':!src?'src':'off'):'';UVT.force=0;UVT.next={vx:V.x,vy:V.y,sig,cl,S,pre,wh:W+'x'+H};if(!ok)return null;
  /* B.vx, B.vy: the view the kept picture shows (it moves by whole device pixels, so its view may differ from V by under half a pixel) */
  const dxU=(B.vx-V.x)*V.ppb,dyU=B.vy-V.y,dx=Math.round(dxU*D),dy=Math.round(dyU*D),moved=Math.abs(dxU)>1e-9||Math.abs(dyU)>1e-9;
  const pvx=B.vx-dx/D/V.ppb,pvy=B.vy-dy/D,R=[];
  /* clips that changed, appeared or went: their old box (where the kept picture now has it) and their new box, with the picture's margin */
  const P=5;let ch=0;const box=(a,vx,vy)=>{uvR(R,a[0]-vx*V.ppb-P,a[1]-vy-P,a[2]+2*P,a[3]+2*P,D,W,H);
    /* its bar in the lane of every group it plays through (drawn from the edge with its whole length when it starts left of it) */
    let gt=a[6]&&grpOf(a[6]),k=0;while(gt&&k++<8){const gi=S.tracks.indexOf(gt);if(gi>=0&&!HIDT.has(gt)){const x=a[0]-vx*V.ppb,x0=Math.max(X0,x);uvR(R,x0-2,AY+TRY[gi]-V.y,a[2]+(x0-x)+4,V.th,D,W,H)}gt=grpOf(gt)}};
  for(const[id,a] of cl){const b=B.cl.get(id);if(b&&b[4]===a[4]&&b[0]===a[0]&&b[1]===a[1]&&b[2]===a[2])continue;ch++;box(a,V.x,V.y);if(b)box(b,pvx,pvy)}
  for(const[id,b] of B.cl)if(!cl.has(id)){ch++;box(b,pvx,pvy)}
  if(!moved&&!ch){UVT.why='nochange';return null}/* something this cannot see changed: draw in full */
  /* the scrolling area: right of the track headers, under the ruler, above the bottom dock */
  const ax0=X0,ax1=X0+arrW,ay0=AY,ay1=TH.under?h-BY:h;/* under the bottom dock the rows go on, unless the look paints that band over (thUnder) */
  /* kept: inside the area, not the track colour stripe, and where the old picture was inside the area too */
  /* whole device pixels only, one in from every edge: a half-covered pixel at an edge blends with what was there before (the window's
     2194 CSS px at 1.75 end in the middle of a device pixel), so it is painted again every time, as without tiles */
  let kx0=Math.ceil((ax0+UVT.sticky)*D)+1,ky0=Math.ceil(ay0*D)+1,kx1=Math.floor(Math.min(ax1,w)*D)-1,ky1=Math.floor(Math.min(ay1,h)*D)-1;
  kx0=Math.max(kx0,kx0+dx);kx1=Math.min(kx1,kx1+dx);ky0=Math.max(ky0,ky0+dy);ky1=Math.min(ky1,ky1+dy);
  if(moved&&(kx1-kx0<64||ky1-ky0<32)){UVT.why='far';return null}
  /* an edit with the view still: only the changed clips' boxes (anything else that changed sets dirty again and draws in full) */
  if(!moved)kx0=0,ky0=0,kx1=W,ky1=H;
  /* always painted: outside the kept box */
  if(ky0>0)R.push([0,0,W,ky0]);if(ky1<H)R.push([0,ky1,W,H-ky1]);if(kx0>0)R.push([0,ky0,kx0,ky1-ky0]);if(kx1<W)R.push([kx1,ky0,W-kx1,ky1-ky0]);
  /* the master lane (drawn per screen column) */
  if(moved){{const MH=mshOf(),my=AY+TOTH+MSY0-V.y;if(my<h&&my+MH>AY)uvR(R,0,my-1,w,MH+2,D,W,H)}/* clips crossing the left edge (drawn without their picture, names kept in view), now or before */
    for(const[id,a] of cl){const b=B.cl.get(id),x=a[0]-V.x*V.ppb,xb=b?b[0]-B.vx*V.ppb:1e9,cn=x<X0+.5,cb=xb<X0+.5;if(!cn&&!cb&&(a[2]+8)*D<=4096)continue;
      /* its name, its marks and whether its note count fits all follow the part in view */
      uvR(R,x-P,a[1]-V.y-P,a[2]+2*P,a[3]+2*P,D,W,H)}
    /* group lanes: a member clip that starts left of the edge has its bar drawn from the edge with the clip's whole length (lane A's drawGroupLanes), now or before */
    S.tracks.forEach((t,i)=>{if(t.kind!=='group'||HIDT.has(t))return;const y=AY+TRY[i]-V.y;if(y>h||y+V.th<AY)return;for(const m of grpMembers(t,true))for(const c of m.clips){const cw=c.len*V.ppb,xn=X0+(c.start-V.x)*V.ppb;if(xn<X0+1||X0+(c.start-B.vx)*V.ppb<X0+1){const a=Math.max(X0-2,Math.min(xn+cw,X0)-2);uvR(R,a,y,X0+cw+Math.abs(dxU)+3-a,V.th,D,W,H)}}});
    /* while playing, automation lanes can be written live: painted again */
    if(play.on)S.tracks.forEach((t,i)=>{if(!t.lanes||!t.lanes.length||HIDT.has(t))return;const y=AY+TRY[i]+V.th-V.y;uvR(R,0,y,w,t.lanes.length*LH,D,W,H)});
    /* empty tracks' hint text sits at the left edge */
    S.tracks.forEach((t,i)=>{if(t.clips.length||HIDT.has(t))return;const y=AY+TRY[i]-V.y;if(y>h||y+V.th<AY)return;uvR(R,X0,y,Math.min(w-X0,520),V.th,D,W,H)})}
  /* worth it only when most of the picture is kept */
  const RR=uvDedup(R);R.length=0;R.push(...RR);const area=uvArea(R);if(area>W*H*UVT.maxF){UVT.why='area '+(area/W/H).toFixed(2);return null}
  g.save();g.setTransform(1,0,0,1,0,0);
  if(moved&&src===arr){UVT.why='nobb';return null}/* no copy kept yet: this frame draws in full and keeps one */
  if(moved&&(dx||dy)){g.save();g.beginPath();g.rect(kx0,ky0,kx1-kx0,ky1-ky0);g.clip();if(!uvOpaque())g.globalCompositeOperation='copy';g.drawImage(src,kx0-dx,ky0-dy,kx1-kx0,ky1-ky0,kx0,ky0,kx1-kx0,ky1-ky0);g.restore()}
  else if(!own){/* the canvas holds last frame's playhead: start from the kept picture */g.save();g.globalCompositeOperation='copy';g.drawImage(src,0,0);g.restore()}
  g.beginPath();for(const r of R)g.rect(r[0],r[1],r[2],r[3]);g.clip();UVT.clip=1;
  UVT.last={mode:moved?'shift':'edit',dx,dy,rects:R};
  /* the kept picture is the old one moved by whole device pixels: remember the view its pixels show (the new strips are drawn at V, under half a pixel apart) */
  UVT.next.vx=pvx;UVT.next.vy=pvy;
  return{area}}
/* lane A clears every clip picture when what they show changed without a clip changing (a waveform analysis that finished): drop the kept picture too */
{const _uvCc=CLC.clear;CLC.clear=function(){UVT.base=null;return _uvCc.apply(this,arguments)}}
/* the look's background is opaque: every pixel of the picture is, and a plain copy (source-over, twice as fast as 'copy') gives the same pixels */
function uvOpaque(){const b=String(TH.bg||'');return/^#[0-9a-f]{6}$/i.test(b)||/^rgb\(/i.test(b)}
/* keep a copy of the picture for the next scroll frame: only after a frame in which the view moved (no cost at rest or while editing) */
function uvKeep(){const W=arr.width,H=arr.height;if(!UVT.bb)UVT.bb=document.createElement('canvas');const b=UVT.bb;if(b.width!==W||b.height!==H){b.width=W;b.height=H}
  const x=b.getContext('2d');x.setTransform(1,0,0,1,0,0);x.globalCompositeOperation='copy';x.drawImage(arr,0,0);x.globalCompositeOperation='source-over';UVT.bbOk=W+'x'+H}
/* tiles pay only where the canvas is drawn by a graphics card: on a software renderer copying the picture costs as much as drawing it (task GS3, UV-2) */
function uvGpu(){if(UVT.gpu!=null)return UVT.gpu;let ok=false,name='';try{const c=document.createElement('canvas'),gl=c.getContext('webgl',{failIfMajorPerformanceCaveat:true});
    if(gl){const d=gl.getExtension('WEBGL_debug_renderer_info');name=String(d?gl.getParameter(d.UNMASKED_RENDERER_WEBGL):gl.getParameter(gl.RENDERER));ok=!/swiftshader|llvmpipe|softpipe|software|basic render/i.test(name);const e=gl.getExtension('WEBGL_lose_context');if(e)e.loseContext()}}catch(e){ok=false}
  UVT.gpuName=name;return UVT.gpu=ok}
function uvUnclip(){if(UVT.clip){UVT.clip=0;arr.getContext('2d').restore()}}
{const _uvSnap=arrSnap;arrSnap=function(){uvUnclip();UVT.insnap=1;try{return _uvSnap.apply(this,arguments)}finally{UVT.insnap=0}}}
{const _uvSnapTo=snapTo;snapTo=function(cv,cache){if(cv===arr&&!UVT.insnap)UVT.base=null;/* someone else kept a copy (it may hold the playhead) */return _uvSnapTo.apply(this,arguments)}}
{const _uvDa=drawArr;drawArr=function(phOnly){if(phOnly){/* only the playhead: its own layer leaves the canvas alone; anything else drew the canvas again */const f0=typeof PHL==='object'?PHL.n.fast:-1,r=_uvDa.apply(this,arguments);if(typeof PHL!=='object'||PHL.n.fast===f0)UVT.base=null;return r}
  if(!(UVT.on===true||(UVT.on==='auto'&&uvGpu()))||UVT.bad){UVT.base=null;UVT.bbOk='';UVT.last={mode:'full',dx:0,dy:0,rects:null};UVT.n.full++;return _uvDa.apply(this,arguments)}/* off: lane A's drawing as it was, nothing added */
  let p=null;try{p=uvPrep()}catch(e){p=null;UVT.bad=1;console.warn('AudioLab UV-2: tiles off',e)}
  const W=arr.width,H=arr.height;let r;
  try{r=_uvDa.apply(this,arguments)}finally{if(UVT.clip){uvUnclip();UVT.base=null;dirty=true}}
  const N=UVT.next,q=N&&N.pre;
  const B0=UVT.base;
  if(N&&q&&!(typeof OVW==='object'&&(OVW.on||OVW.a))&&q.X0===X0&&q.AY===AY&&q.TY===TY&&q.BY===BY&&q.arrW===arrW&&N.wh===arr.width+'x'+arr.height){UVT.base={vx:N.vx,vy:N.vy,sig:N.sig,cl:N.cl,S:N.S,wh:N.wh};
    /* the view moved (or this was a scroll frame) and the tiles are on here: keep a copy for the next one */
    const mv=UVT.last.mode==='shift'||(B0&&(B0.vx!==V.x||B0.vy!==V.y));if(mv&&!ad&&!RS&&typeof PHL==='object'&&PHL.on&&!PHL.keep)uvKeep();else UVT.bbOk=''}
  else{UVT.base=null;UVT.bbOk='';if(p)dirty=true}/* drawArr laid out differently than the preparation: this frame may be stale, draw again in full */
  UVT.next=null;UVT.px.all+=W*H;
  if(p){UVT.n[UVT.last.mode]++;UVT.px.drawn+=p.area;if(UVT.tm)clearTimeout(UVT.tm);UVT.tm=setTimeout(()=>{UVT.tm=0;UVT.force=1;dirty=true},UV.rest)}
  else{UVT.n.full++;UVT.px.drawn+=W*H;if(UVT.tm){clearTimeout(UVT.tm);UVT.tm=0}}
  return r}}
"""
rep("function askChoice(title,text,btns,icon){", JS + "function askChoice(title,text,btns,icon){")
open(P, 'w', encoding='utf-8').write(s)
print('UV-2a applied to', P)
