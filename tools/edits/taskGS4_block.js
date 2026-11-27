/* ====================== v@VER@ (task GS4, glass step 4): the device panel and the transport float, the transport gets the lens ======================
   The user's look at v0.228 on the Mac: in the bottom left corner the glass did not blur and did not bend. Cause: the track header rows (#hdrclip) run on
   down behind the device panel and the transport, and they are page elements, not part of the engine's picture, so they showed sharp through the
   see-through panels (and so did the 6 px of device glass under the device cards). Now:
   - the device panel and the transport are floating glass: GS4.ins px in from the left and right window edges (the tab band starts there too), corners of
     GS4.rad px, GS4.gap px between them; the arrangement shows beside them and in their corners.
   - the engine's canvas now lies ABOVE the arrangement canvas and its playhead layer (and under the track header column): its faces cover what is under
     the glass, and around them the real arrangement shows, so nothing is cut out of the arrangement canvas any more (no clip, no copy into #arrCol). A
     clip with rounded holes was tried first: right on screen, but a clip of that shape makes the compositor mask the full-window canvas on every frame
     (measured: idle 63-74 down to 38-40 frames a second on the cloud machine). Only the header rows (#hdrclip, a narrow layer that repaints rarely) are
     cut away under the glass, with such a path.
   - the transport's lens bends on every edge; GS4.lensY makes the bend along the top and bottom edges a little stronger on the transport and the device
     panel (engine 2.4, lensY). These are the numbers to change. */
const GS4={ins:10,rad:12,gap:4,lensY:{tr:1.3,fxglass:1.2},seg:6,holes:[],fresh:true,n:{clip:0,hdr:0}};
document.documentElement.style.setProperty('--gs4i',GS4.ins+'px');document.documentElement.style.setProperty('--gs4r',GS4.rad+'px');document.documentElement.style.setProperty('--gs4g',GS4.gap+'px');
/* the floating look applies to the docked device panel and transport (not to devices popped out into a window or shown in the piano roll) */
function gs4Dock(el){if(!el)return false;if(el.id==='tr')return true;const fx=document.getElementById('fx');return!!fx&&!fx.classList.contains('popped')&&!fx.classList.contains('prdev')}
/* the device glass ends GS4.gap px above the transport */
{const _fg=fxGlassSync;fxGlassSync=function(){const r=_fg.apply(this,arguments);try{const fx=document.getElementById('fx'),g=document.getElementById('fxglass');if(fx&&g){const d=gs4Dock(g);if(g.classList.contains('gs4')!==d)g.classList.toggle('gs4',d);const h=Math.max(0,fx.offsetHeight-2-(d?GS4.gap:0))+'px';if(g.style.height!==h)g.style.height=h}}catch(e){}return r}}
/* the glass shapes over the arrangement, in CSS px relative to the arrangement canvas (which has the size and place of #main) */
function gs4Shapes(){const a=arr.getBoundingClientRect(),z=ZOOM,out=[];if(!a.width||!a.height)return out;
  for(const id of['fxglass','tr']){const el=document.getElementById(id);if(!el||!el.getClientRects().length)continue;const cs=getComputedStyle(el);if(cs.display==='none'||cs.visibility==='hidden')continue;
    const r=el.getBoundingClientRect();if(r.width<a.width*.5||r.height<4||r.bottom<=a.top+1||r.top>=a.bottom-1)continue;
    out.push({id,x:(r.left-a.left)/z,y:(r.top-a.top)/z,w:r.width/z,h:r.height/z,r:Math.min(parseFloat(cs.borderTopLeftRadius)||0,r.height/z/2,r.width/z/2)})}
  return out}
/* a rounded rectangle as a polygon (GS4.seg steps per corner), clockwise */
function gs4Poly(s){const{x,y,w,h,r}=s,n=GS4.seg,P=[];if(!(r>.5))return[[x,y],[x+w,y],[x+w,y+h],[x,y+h]];
  for(const[cx,cy,a0] of[[x+w-r,y+r,-90],[x+w-r,y+h-r,0],[x+r,y+h-r,90],[x+r,y+r,180]])for(let i=0;i<=n;i++){const t=(a0+90*i/n)*Math.PI/180;P.push([cx+r*Math.cos(t),cy+r*Math.sin(t)])}
  return P}
/* the part of a convex polygon inside a rectangle (Sutherland and Hodgman) */
function gs4Cut(P,x0,y0,x1,y1){const E=[[p=>p[0]>=x0,(a,b)=>[x0,a[1]+(b[1]-a[1])*(x0-a[0])/(b[0]-a[0])]],[p=>p[0]<=x1,(a,b)=>[x1,a[1]+(b[1]-a[1])*(x1-a[0])/(b[0]-a[0])]],
  [p=>p[1]>=y0,(a,b)=>[a[0]+(b[0]-a[0])*(y0-a[1])/(b[1]-a[1]),y0]],[p=>p[1]<=y1,(a,b)=>[a[0]+(b[0]-a[0])*(y1-a[1])/(b[1]-a[1]),y1]]];
  for(const[inside,cross] of E){if(!P.length)break;const Q=[];for(let i=0;i<P.length;i++){const a=P[i],b=P[(i+1)%P.length],ia=inside(a),ib=inside(b);if(ia){Q.push(a);if(!ib)Q.push(cross(a,b))}else if(ib)Q.push(cross(a,b))}P=Q}
  return P}
/* clip-path (for the header rows) that shows the rectangle [x0,y0,x1,y1] of an element except the glass shapes (dx, dy: where the element's box starts, in arrangement px) */
function gs4Path(x0,y0,x1,y1,S,dx,dy){const f=v=>(Math.round(v*10)/10);let d=`M${f(x0)} ${f(y0)}H${f(x1)}V${f(y1)}H${f(x0)}Z`,holes=0;
  for(const s of S){const P=gs4Cut(gs4Poly({x:s.x-dx,y:s.y-dy,w:s.w,h:s.h,r:s.r}),x0,y0,x1,y1);if(P.length<3)continue;holes++;d+='M'+P.map(p=>f(p[0])+' '+f(p[1])).join('L')+'Z'}
  return holes?`path(evenodd,'${d}')`:(x0>0||y0>0?null:'')}
/* no cut any more: the engine's canvas lies above the arrangement (CSS body.gle #glassCv), its faces cover what is under the glass */
gbClip=function(){let hd=false;if(GS4.fresh){GS4.fresh=false;GS4.holes=gs4Shapes();hd=true}
  if(GB.clip){GB.clip='';arr.style.clipPath='';GS4.n.clip++}if(GB.col&&GB.col.style.display!=='none')GB.col.style.display='none';
  if(hd)gs4Hdr(GS4.holes)};
/* the header rows: cut away under the glass (a path with the rounded holes), so that only the engine's frosted picture is there */
function gs4Hdr(S){const hc=document.getElementById('hdrclip');if(!hc)return;let cl='';
  if(S&&S.length&&GB.on){const a=arr.getBoundingClientRect(),r=hc.getBoundingClientRect(),z=ZOOM;if(r.width>2&&r.height>2)cl=gs4Path(0,0,r.width/z,r.height/z,S,(r.left-a.left)/z,(r.top-a.top)/z)||''}
  if(hc._gs4!==cl){hc._gs4=cl;hc.style.clipPath=cl;GS4.n.hdr++}}
/* the header column copy is not needed: the arrangement canvas itself shows above the first and below the last track */
gbCol=function(){};
/* the engine off (Solid, no WebGL2): nothing is cut */
{const _gl=gbLayout;gbLayout=function(){GS4.fresh=true;const r=_gl.apply(this,arguments);try{if(!GB.on){GS4.holes=[];gs4Hdr(null)}}catch(e){}return r}}
/* the floating panels bend on every edge, the docked ones as before */
{const _ge=gleEdges;gleEdges=function(id){if((id==='tr'||id==='fxglass')&&GS4.holes.some(s=>s.id===id))return'trbl';return _ge.apply(this,arguments)}}
{const _gs=gleSync;gleSync=function(){const r=_gs.apply(this,arguments);const g=GLE.g;if(g&&GLE.on)for(const id of['tr','fxglass']){if(!g.hasPanel(id))continue;const el=document.getElementById(id),fl=!!el&&gs4Dock(el),rad=fl?(parseFloat(getComputedStyle(el).borderTopLeftRadius)||0):0;
  g.updatePanel(id,{radius:rad>0?rad+1:0,lensY:fl?GS4.lensY[id]:1})}return r}}
/* a window or menu over the floating panels sees them with their rounded corners */
function gs4Rad(id){const el=document.getElementById(id);if(!el||(id!=='tr'&&id!=='fxglass')||!gs4Dock(el))return 0;return parseFloat(getComputedStyle(el).borderTopLeftRadius)||0}
try{setTimeout(()=>{try{fxGlassSync();GB.lt=0;gbCopy()}catch(e){}},0)}catch(e){}
