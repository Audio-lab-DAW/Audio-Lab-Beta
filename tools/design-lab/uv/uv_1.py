#!/usr/bin/env python3
"""Task UV-1 (lane O, view engine): S9 direct trackpad and S13 zoom without page layout.
Run on a fresh index.html: python3 tools/design-lab/uv/uv_1.py [index.html]. Every anchor must occur exactly once."""
import sys
P = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
s = open(P, encoding='utf-8').read()
assert 'task UV-1 (lane O' not in s, 'UV-1 is already in this file'

def rep(old, new, cnt=1):
    global s
    n = s.count(old)
    assert n == cnt, (n, old[:120])
    s = s.replace(old, new)

# 1. szStep: notched wheels and buttons ease with tau 15 ms (was 40); nothing eases with reduced motion
rep("function szStep(t){SZraf=0;const dt=SZt?Math.min(64,t-SZt):16;SZt=t;const a=1-Math.exp(-dt/40);let more=false;",
    "function szStep(t){SZraf=0;const dt=SZt?Math.min(64,t-SZt):16;SZt=t;const tau=uvTau(),a=tau>0?1-Math.exp(-dt/tau):1;let more=false;")
# 2. clampV: V.y keeps its sub-pixel value while a zoom holds the header (rounded once at rest, as after an eased zoom)
rep("V.y=SZ.size?yy:Math.round(yy);", "V.y=SZ.size||(UV&&UV.hold)?yy:Math.round(yy);")
# 3. zsWheel: a pinch and a trackpad scroll with a zoom key are applied at once; only notched wheels ease
rep("""  const raw=e.deltaY||e.deltaX,ly=e.deltaMode===1?16:1;/* a held Shift turns a mouse wheel into a sideways scroll in most browsers, so either axis counts */
  if(act==='side'){if(FLOCK()){WACC=(performance.now()-WACT>400?0:WACC)+raw;WACT=performance.now();if(Math.abs(WACC)>140){WACC=0;phFlash()}}else if(raw)smoothPan('arrx',raw*ly,s=>{V.x+=s/V.ppb;clampV();dirty=true});return true}""",
"""  const raw=e.deltaY||e.deltaX,ly=e.deltaMode===1?16:1,ez=!pin&&uvEase(e);/* a held Shift turns a mouse wheel into a sideways scroll in most browsers, so either axis counts. UV-1 (S9): ez = a notched mouse wheel, eased; a pinch or a trackpad is applied in this frame */
  if(act==='side'){if(FLOCK()){WACC=(performance.now()-WACT>400?0:WACC)+raw;WACT=performance.now();if(Math.abs(WACC)>140){WACC=0;phFlash()}}else if(raw){const ap=s=>{V.x+=s/V.ppb;clampV();dirty=true};if(ez)smoothPan('arrx',raw*ly,ap);else ap(raw*ly)}return true}""")
rep("""  if(act==='zoom')smoothZoom(key,amt,f=>zoomAround(f,UI.mapZoom==='ableton'?1:f,bt,rw));
  else if(act==='th')smoothZoom(key+'v',amt*.45,f=>zoomAround(1,f,bt,rw));
  else smoothZoom(key+'h',amt,f=>zoomAround(f,1,bt,rw));
  return true}""",
"""  const go=(k,a,f)=>{if(ez)smoothZoom(k,a,f);else{SZ.delete(k);f(Math.exp(a))}};
  if(act==='zoom')go(key,amt,f=>{if(UI.mapZoom!=='ableton')uvHold();zoomAround(f,UI.mapZoom==='ableton'?1:f,bt,rw)});
  else if(act==='th')go(key+'v',amt*.45,f=>{uvHold();zoomAround(1,f,bt,rw)});
  else go(key+'h',amt,f=>zoomAround(f,1,bt,rw));
  return true}""")
# 4. the piano roll and the overview: a pinch is applied at once there too
rep("  if(e.ctrlKey||e.metaKey){smoothZoom('pr',wz(e),f=>zoomPR(f,x,y));return}\n  else if(e.altKey){smoothZoom('prv',-clamp(e.deltaY,-60,60)*.005,f=>{PR.rh*=f;clampPR();dirty=true});return}",
    "  if(e.ctrlKey||e.metaKey){uvZoomBy('pr',wz(e),f=>zoomPR(f,x,y),e);return}\n  else if(e.altKey){uvZoomBy('prv',-clamp(e.deltaY,-60,60)*.005,f=>{PR.rh*=f;clampPR();dirty=true},e);return}")
rep("    if(e.ctrlKey||e.metaKey)smoothZoom('ovw',wz(e),f=>ovwZoom(f,p.x,p.y));",
    "    if(e.ctrlKey||e.metaKey)uvZoomBy('ovw',wz(e),f=>ovwZoom(f,p.x,p.y),e);")
# 5. drawArr: while a zoom holds the header, its CSS variables and size classes stay; the rows are moved by transforms (uvHdrPose)
OLD_HDR_A = "hdrin.style.setProperty('--th',V.th+'px');{const m=mshOf();hdrin.style.setProperty('--msh',m+'px');"
OLD_HDR_B = "hdrin.classList.toggle('nano',V.th<21);"
i = s.index(OLD_HDR_A); assert s.count(OLD_HDR_A) == 1 and s.count(OLD_HDR_B) == 1 and s.index(OLD_HDR_B) > i and s.index(OLD_HDR_B) - i < 900
j = s.index(OLD_HDR_B) + len(OLD_HDR_B)
s = s[:i] + "if(!(UV&&UV.hold&&uvHdrPose())){/* UV-1 (S13): laid out at rest only */" + s[i:j] + "}" + s[j:]

# 6. E19 calmer Follow page turns (the user's long-sessions wish, as the standard Follow "Page" behaviour): turn at 90 %, keep the last fifth of the old page in view, no turn while a pointer edit is held
rep("else if(b>V.x+vis*.95||b<V.x){V.x=b-vis*.05;clampV()}", "else if(!uvEditing()&&(b>V.x+vis*.9||b<V.x)){V.x=uvPageTurn(b,vis);clampV()}")

JS = r"""/* ---------- task UV-1 (lane O, view engine; the user's UX1 picks S9 and S13) ----------
   S9 direct trackpad: a pinch (a wheel event with ctrlKey and no Control key down) and a trackpad scroll with a zoom key are applied in
   the frame they arrive in (zoomAround at once, no second easing on top of the trackpad's own smoothing). Only notched mouse wheels
   (and the zoom buttons) are eased, with tau 15 ms (was 40); with reduced motion nothing is eased. Speed, Zoom around (Anchor), Invert
   and "Trackpad pinch zooms" work as before: zsWheel still computes the amount and the anchor, only the easing is skipped.
   S13 zoom without page layout: while a zoom changes the track height, the track headers keep the layout they had (drawArr does not
   write --th, --lh, --msh, --mh or the size classes); uvHdrPose moves every row with a transform to where the new heights put it and
   clips it to its new height. The clip pictures are drawn from their cached picture scaled to the new size (uvClipStale) instead of
   being drawn again at every step. 90 ms after the last zoom step (UV.rest) uvRest lets go: the header is laid out once and the
   arrangement drawn in full, so at rest every pixel is what the drawing without UV-1 gives.
   Hooks: UV_HOOKS.holding() tells other lanes a zoom is under way (their header code can skip work). */
var UV={tau:15,rest:90,hold:false,tm:0,lf:0,th0:0,lh0:0,try0:null,toth0:0,rows:null,ver:0};
const UV_HOOKS={holding:()=>!!(UV&&UV.hold)};
let UVRM=null;
function uvStill(){try{if(!UVRM)UVRM=matchMedia('(prefers-reduced-motion: reduce)');return UVRM.matches}catch(e){return false}}
function uvTau(){return(typeof UV==='object'&&UV)?(uvStill()?0:UV.tau):40}
/* a notched mouse wheel (eased) or a trackpad (direct). Lines (deltaMode 1), the 40 px steps mouseLike knows, or a whole 120 wheelDelta on one axis */
function uvNotch(e){if(e.deltaMode)return true;if(mouseLike(e))return true;const wx=Math.abs(e.wheelDeltaX||0),wy=Math.abs(e.wheelDeltaY||0);return(wx===0)!==(wy===0)&&wx+wy>=120&&(wx+wy)%120===0}
function uvEase(e){return uvNotch(e)&&uvTau()>0}
/* zoom by exp(amt): at once for a pinch or a trackpad, eased for a notched wheel */
function uvZoomBy(key,amt,apply,e){const pin=e&&e.ctrlKey&&!e.metaKey&&!ZSK.c;if(!pin&&e&&uvEase(e))smoothZoom(key,amt,apply);else{SZ.delete(key);if(amt)apply(Math.exp(amt))}}
/* the header holds its layout from the first zoom step until UV.rest ms after the last one */
function uvHold(){if(UV.tm)clearTimeout(UV.tm);UV.tm=setTimeout(uvRest,UV.rest);UV.lf=FRN;if(UV.hold||typeof hdrin==='undefined'||!hdrin||!S.tracks.length)return;
  const th0=parseFloat(hdrin.style.getPropertyValue('--th'))||V.th,sv=V.th;V.th=th0;layoutRows();UV.th0=th0;UV.lh0=LH;UV.try0=TRY.slice();UV.toth0=TOTH;V.th=sv;layoutRows();
  const ix=new Map(S.tracks.map((t,i)=>[t.id,i])),rows=[];let j=0;
  for(const el of hdrin.children){const cl=el.classList,r={el,tr:el.style.transform,cp:el.style.clipPath};
    if(cl.contains('hdr')){r.k='h';r.i=ix.get(el.dataset.id);j=0}else if(cl.contains('lhd')){r.k='l';r.i=ix.get(el.dataset.id);r.j=j++}else r.k='a';
    if((r.k==='h'||r.k==='l')&&r.i==null)r.k='a';rows.push(r)}
  UV.rows=rows;UV.n=hdrin.childElementCount;UV.hold=true;hdrin.classList.add('uvz')}
/* called by drawArr in place of the header's CSS variables while the zoom holds; false = let go now (the header was rebuilt) */
function uvHdrPose(){const R=UV.rows;if(!R||hdrin.childElementCount!==UV.n||(R.length&&!R[0].el.isConnected)||TRY.length!==UV.try0.length){uvRest(true);return false}
  const T=TRY,T0=UV.try0,tail=TOTH-UV.toth0;
  for(const r of R){let dy=tail,cut=0;
    if(r.k==='h'){dy=T[r.i]-T0[r.i];cut=UV.th0-V.th}else if(r.k==='l'){dy=T[r.i]+V.th+r.j*LH-(T0[r.i]+UV.th0+r.j*UV.lh0);cut=UV.lh0-LH}
    const tr=Math.abs(dy)>.004?(r.tr?r.tr+' ':'')+`translate3d(0,${dy.toFixed(2)}px,0)`:r.tr,cp=cut>.01?`inset(0 0 ${cut.toFixed(2)}px 0)`:r.cp;
    if(r.el.style.transform!==tr)r.el.style.transform=tr;if(r.k!=='a'&&r.el.style.clipPath!==cp)r.el.style.clipPath=cp}
  return true}
function uvRest(now){if(UV.tm){clearTimeout(UV.tm);UV.tm=0}if(!UV.hold)return;
  if(!now){if(FRN-UV.lf<2){UV.tm=setTimeout(uvRest,UV.rest);return}/* a slow screen: wait for two frames after the last step */for(const k of SZ.keys())if(/^(arr|map)/.test(k)){UV.tm=setTimeout(uvRest,UV.rest);return}}/* an eased zoom still running */
  UV.hold=false;hdrin.classList.remove('uvz');for(const r of UV.rows||[]){if(r.el.style.transform!==r.tr)r.el.style.transform=r.tr;if(r.k!=='a'&&r.el.style.clipPath!==r.cp)r.el.style.clipPath=r.cp}UV.rows=null;clampV();dirty=true}
/* E19 (UX2 wish, lane O): Follow "Page" turns at 90 % of the view and keeps the last fifth of the old page in view (the playhead lands at 10 %),
   so a turn moves 80 % of the view instead of 95 %; a playhead outside the view (a jump) still lands at 5 %. No turn while a pointer edit
   is held in the arrangement or the piano roll: the turn comes when it is let go. */
function uvPageTurn(b,vis){return b>V.x+vis*.9&&b<V.x+vis?V.x+vis*.8:b-vis*.05}
function uvEditing(){return!!(ad||md||pd)}
/* clip pictures during the hold: the cached picture scaled to the clip's new size (lane A's drawClipC draws it again at rest) */
{const _uvDc=drawClipC;drawClipC=function(g,t,c,G,w){const d=(window.devicePixelRatio||1)*ZOOM,W=Math.ceil(G.w),cached=!(G.x<X0+.5||(W+8)*d>4096||W<3);
  if(UV.hold&&cached){const e=CLC.get(c.id);if(e&&e.uvw&&e.uvd===d){const sx=G.w/e.uvw,sy=G.h/e.uvh,P=4;e.u=FRN;g.drawImage(e.cv,G.x-P*sx,G.y-P*sy,e.cv.width/d*sx,e.cv.height/d*sy);return}}
  const r=_uvDc.apply(this,arguments);if(cached){const e=CLC.get(c.id);if(e){e.uvw=G.w;e.uvh=G.h;e.uvd=d}}return r}}
"""
rep("function askChoice(title,text,btns,icon){", JS + "function askChoice(title,text,btns,icon){")
CSS = "/* task UV-1 (lane O): while a zoom holds the track headers, every row is its own layer, so moving it costs no painting */\n#hdrin.uvz>*{will-change:transform}\n"
rep(".dacv{display:flex;", CSS + ".dacv{display:flex;")
open(P, 'w', encoding='utf-8').write(s)
print('UV-1 applied to', P)
