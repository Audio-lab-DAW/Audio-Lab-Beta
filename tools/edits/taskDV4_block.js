/* ===== v0.296: display-first devices, step 4 (task DV-4): the bottom dock, the values line clear of the handles, and On the picture for the
   Compressor, Sidechain, Echo delay and Space reverb =====
   docs/devices-display-first.md sections 7 and 10 (the user's picks DD4 for the Compressor and the Echo delay, their families the Sidechain and the Reverb).
   Hover reveal as a bottom dock (DD4 with DD1's dock): the controls in one row, each knob with its label over its value, Gain after a hairline, all on
   one glass panel (the rail's panel, so the devices engine draws it as before); the preset row floats as a pill at the top. Both are placed clear of
   the picture's own handles (HND, and the Echo delay's own geometry), so a handle can still be dragged while the dock is shown.
   The values line (rail closed, at rest) leaves out what the picture already writes in words and sits where no handle and none of the picture's own
   words are (bottom first, then under the picture's top line).
   On the picture (DD3): each control is a chip beside the handle it shapes (Threshold and Ratio on the curve, Attack and Release on their dots, Makeup
   at the output; Time, Mix and Feedback at the echoes, the cuts at the filter band; Pre-delay, Decay, Damp, Mix and Low cut at theirs; Depth, Shape
   and Punch on the pump); the preset, Gain and what has no handle are in the More drawer. Chips move with their handles; the one being dragged stays.
   Everything is placed by one routine (dvPlace) from the handles, so later steps only add a device's anchors (DVANC) and its own words (DVTXT).
   No sound, parameter or stored value changes here; only where the controls are drawn. */
const DV4={n:{dock:0,val:0,pic:0,place:0},q:0};
const DVDOCK=new Set(['comp','side','delay','reverb']);
/* the picture's own words: left out of the values line (skip) and kept clear by the values line, chips and More (clear: rectangles in canvas pixels) */
const DVTXT={comp:{skip:['Threshold','Ratio'],clear:(w,h)=>[[8,0,165,19],[w-70,8,64,22]]},
  delay:{skip:['Time','Feedback','Mix'],clear:(w,h,p)=>[[6,0,110,18],[w-(p&&p.ping?190:136),0,190,18],[0,h-22,w,22]]},
  reverb:{skip:['Decay','Pre-delay'],clear:(w,h)=>[[6,0,175,20],[w-66,h-34,66,16]]},
  side:{skip:[],clear:(w,h)=>[[0,h-15,175,15],[w-116,0,116,18]]}};
/* which handle each control belongs to (the index in the device's handle list) */
const DVANC={comp:{threshold:0,ratio:1,makeup:2,attack:3,release:4},reverb:{predelay:0,decay:1,damp:2,mix:3,lowcut:4},
  side:{depth:0,shape:0,punch:1},delay:{time:0,mix:0,feedback:1,lowcut:2,highcut:3}};
/* the Echo delay's handles, from its own drawing's geometry (dGeo): the first echo (time and mix), the second (feedback), the two cuts */
function dvDelayH(p,w,h){const G=dGeo(p,w,h),ht=p.mix/100*G.amp,x0=G.X(G.dt),y0=G.mid-(p.ping?ht+1:ht)-1,x1=G.X(2*G.dt),y1=G.mid-Math.max(1.5,ht*p.feedback/100);
  return[{x:x0,y:y0,l:'Time'},{x:x1<w-16?x1:Math.min(w-16,x0+24),y:y1,l:'Feedback'},{x:G.F(p.lowcut),y:h-12,l:'Low cut'},{x:G.F(p.highcut),y:h-12,l:'High cut'}]}
/* the handles of a device's picture, in the device body's pixels */
function dvHandles(D,own,ty){const B=D.querySelector(':scope>.devb'),cv=B&&B.querySelector('canvas.viz');if(!cv||!cv.clientWidth||!own||!own.p)return null;const w=cv.clientWidth,h=cv.clientHeight;let L;
  try{L=ty==='delay'?dvDelayH(own.p,w,h):HND[ty]?HND[ty](own.p,w,h):[]}catch(e){return null}
  const z=ZOOM||1,cr=cv.getBoundingClientRect(),br=B.getBoundingClientRect(),ox=(cr.left-br.left)/z-B.clientLeft,oy=(cr.top-br.top)/z-B.clientTop;
  const T=DVTXT[ty],clear=T?T.clear(w,h,own.p).map(r=>[r[0]+ox,r[1]+oy,r[2],r[3]]):[];
  return{cv,w,h,ox,oy,clear,L:L.map((q,i)=>({x:q.x+ox,y:q.y+oy,l:q.l,i}))}}
function dvHit(a,b,m){return a[0]<b[0]+b[2]+m&&b[0]<a[0]+a[2]+m&&a[1]<b[1]+b[3]+m&&b[1]<a[1]+a[3]+m}
/* how bad a place is: outside the body 100, over a handle 10, over another placed control 20, over the picture's own words 2 */
function dvScore(r,ctx){let s=0;if(r[0]<4||r[1]<ctx.top||r[0]+r[2]>ctx.BW-4||r[1]+r[3]>ctx.BH-3)s+=100;for(const q of ctx.H)if(dvHit(r,[q.x-9,q.y-9,18,18],1))s+=10;
  for(const u of ctx.used)if(dvHit(r,u,3))s+=20;for(const c of ctx.clear)if(dvHit(r,c,0))s+=2;return s}
function dvBest(cands,ctx){let best=null,bs=1e9;for(const c of cands){const r=c.map(Math.round),s=dvScore(r,ctx);if(s<bs){bs=s;best=r;if(!s)break}}return best}
/* a chip beside its handle: right, left, above or below it, then a step further out, whichever is clear (each place first held inside the body) */
function dvNear(x,y,w,h,ctx){const g=12,c=[];for(const dy of[0,-h-6,h+6,-2*h-12,2*h+12])for(const dx of[g,-g-w])c.push([x+dx,y-h/2+dy,w,h]);c.splice(2,0,[x-w/2,y-g-h,w,h],[x-w/2,y+g,w,h]);
  for(const r of c){r[0]=Math.max(4,Math.min(r[0],ctx.BW-w-4));r[1]=Math.max(ctx.top,Math.min(r[1],ctx.BH-h-4))}const r=dvBest(c,ctx);ctx.used.push(r);return r}
function dvPos(el,r){if(!r)return;const L=r[0]+'px',T=r[1]+'px';if(el.style.left!==L||el.style.top!==T){el.style.left=L;el.style.top=T;dvgDirty()}}
function dvCtx(B,Hd){const pill=B.querySelector(':scope>.dvtr');return{H:Hd?Hd.L:[],clear:Hd?Hd.clear:[],used:pill?[[pill.offsetLeft,pill.offsetTop,pill.offsetWidth,pill.offsetHeight]]:[],BW:B.clientWidth,BH:B.clientHeight,top:3}}
{const _fr=dvFrame;dvFrame=function(D,t,fl){const r=_fr.apply(this,arguments);try{dv4(D,t)}catch(e){console.error('AudioLab bottom dock',e)}return r}}
function dv4(D,t){const B=D.querySelector(':scope>.devb');D.classList.remove('dvdock');if(!B||!D.classList.contains('dvf'))return;const own=dvOwnOf(D,t);if(!own)return;const ty=dvType(D,own);
  if(D.dataset.d!=='fx'||!DVDOCK.has(ty)||!D.classList.contains('dvshut'))return;
  if(D.classList.contains('dvpic')){dvChipPlace(D,own,B);return}
  dvDock(D,own,B,ty);dvValPlace(D)}
/* ---- hover reveal: the bottom dock ---- */
const DVTIP={sync:'Rate: how often the sound ducks, in notes of the song (1/4 = on every beat)'};
function dvTips(B){for(const e of B.querySelectorAll('select[data-x],button[data-x]'))if(!e.title){const l=e.closest('label');e.title=DVTIP[e.dataset.x]||(l?l.textContent.trim().split('\n')[0]+': choose from the list':'')}}
function dvDock(D,own,B,ty){const S=B.querySelector(':scope>.dfs');if(!S)return;DV4.n.dock++;D.classList.add('dvdock');dvTips(B);
  const pr=S.querySelector(':scope>.dspr');if(pr){pr.classList.add('dvface','dvdpre');B.append(pr);dvPicFace(pr)}
  dvDockPlace(D,own,B,ty)}
function dvDockPlace(D,own,B,ty){const S=B.querySelector(':scope>.dfs'),G=B.querySelector(':scope>.dug'),pr=B.querySelector(':scope>.dvdpre');if(!S)return;
  const sw=S.offsetWidth,gw=G?G.offsetWidth:0,tot=sw+gw;if(tot+16>B.clientWidth)B.style.minWidth=(tot+16)+'px';
  const dh=Math.max(S.offsetHeight,G?G.offsetHeight:0),Hd=dvHandles(D,own,ty),ctx=dvCtx(B,Hd),BW=ctx.BW,BH=ctx.BH,left=Math.max(8,Math.round((BW-tot)/2));
  /* the lowest place that covers no handle (at the bottom, just above or just under a handle, under the top row); when every place covers one,
     the one that covers the fewest */
  const bs=[8];for(const q of ctx.H){bs.push(Math.ceil(BH-(q.y-12)));bs.push(Math.floor(BH-(q.y+12)-dh))}
  let bot=8,bn=1e9;for(const b of bs.filter(b=>b>=4&&BH-b-dh>=34).sort((a,b)=>a-b)){const r=[left,BH-b-dh,tot,dh],n=ctx.H.filter(q=>dvHit(r,[q.x-9,q.y-9,18,18],2)).length;if(n<bn){bn=n;bot=b;if(!n)break}}
  const v=[['--dvdl',left+'px'],['--dvgl',(left+sw)+'px'],['--dvdb',bot+'px'],['--dvdh',dh+'px']];let ch=0;for(const[k,x]of v)if(B.style.getPropertyValue(k)!==x){B.style.setProperty(k,x);ch=1}
  ctx.used.push([left,BH-bot-dh,tot,dh]);
  if(pr){const w=pr.offsetWidth,h=pr.offsetHeight,pl=ctx.used[0];dvPos(pr,dvBest([[8,4,w,h],[Math.round((BW-w)/2),4,w,h],[pl?pl[0]-w-6:BW-w-60,4,w,h],[8,BH-bot-dh-h-6,w,h]],{...ctx,clear:[]}))}
  dvRail(D);if(ch)dvgDirty()}
/* ---- the values line: what the picture does not already write, where no handle and none of its words are ---- */
function dvSkip(B,label){const D=B.closest('.dev'),own=D&&dvOwnOf(D),T=own&&DVTXT[dvType(D,own)];return!!T&&T.skip.includes(label)}
function dvValPlace(D){const B=D.querySelector(':scope>.devb'),V=B&&B.querySelector(':scope>.dvval');if(!V||D.classList.contains('dvpic'))return;const own=dvOwnOf(D);if(!own)return;const ty=dvType(D,own);if(!DVTXT[ty])return;
  const Hd=dvHandles(D,own,ty);if(!Hd)return;DV4.n.val++;const ctx=dvCtx(B,Hd),BW=ctx.BW,BH=ctx.BH,lh=17;
  const w0=V.style.width;V.style.width='max-content';const tw=Math.min(V.scrollWidth+2,BW-20);V.style.width=w0;
  const ys=[BH-lh-5,Hd.oy+20,Hd.oy+38,BH-lh-26],c=[];for(const y of ys){c.push([10,y,tw,lh]);c.push([BW-10-tw,y,tw,lh])}
  const r=dvBest(c,ctx);const st={left:r[0]+'px',top:r[1]+'px',width:r[2]+'px',right:'auto',bottom:'auto'};for(const k in st)if(V.style[k]!==st[k])V.style[k]=st[k];V.dataset.dvp=r[1]>BH/2?'bottom':'top'}
{const _v=dvVals;dvVals=function(D){const r=_v.apply(this,arguments);try{if(D&&D.classList.contains('dvdock'))dvValPlace(D)}catch(e){}return r}}
/* ---- On the picture: the four devices' controls as chips at their handles ---- */
for(const ty of['comp','side','delay','reverb'])DVPIC[ty]={lay:dvpAnchored};
function dvpAnchored(D,own,B){const ty=dvType(D,own),A=DVANC[ty],S=B.querySelector(':scope>.dfs'),G=B.querySelector(':scope>.dug');if(!S||!A)return[];DV4.n.pic++;dvTips(S);
  const rest=[];for(const el of[...S.querySelectorAll('.pgrid [data-c]')]){const k=el.dataset.c.split(':').pop();if(k in A){el.classList.add('dvface','dvchip');el.dataset.dva=A[k];B.append(el)}else rest.push(el)}
  const pr=S.querySelector(':scope>.dspr'),tb=S.querySelector(':scope>.ndtb');if(G)G.classList.add('dvdgain');
  return[{head:'Preset',els:[pr]},{head:'Rhythm',els:[tb]},{head:'Other controls',els:rest},{head:'Output',els:[G]}]}
function dvChipPlace(D,own,B){own=own||dvOwnOf(D);if(!own)return;const ty=dvType(D,own),Hd=dvHandles(D,own,ty);if(!Hd)return;DV4.n.place++;const ctx=dvCtx(B,Hd),BW=ctx.BW,BH=ctx.BH;
  const drag=typeof cd!=='undefined'&&cd?cd.el:null;
  for(const el of B.querySelectorAll(':scope>.dvchip')){if(el===drag){ctx.used.push([el.offsetLeft,el.offsetTop,el.offsetWidth,el.offsetHeight]);continue}const q=Hd.L[+el.dataset.dva];if(!q)continue;dvPos(el,dvNear(q.x,q.y,el.offsetWidth,el.offsetHeight,ctx))}
  const mb=B.querySelector(':scope>.dvmore'),pl=B.querySelector(':scope>.dvtr');if(mb){const w=mb.offsetWidth,h=mb.offsetHeight,px=pl?pl.offsetLeft-w-6:BW-w-60;
    const r=dvBest([[px,6,w,h],[Math.round((BW-w)/2),6,w,h],[8,6,w,h],[px,BH-h-6,w,h],[8,BH-h-6,w,h]],ctx);dvPos(mb,r);ctx.used.push(r);
    const dr=B.querySelector(':scope>.dvdrw');if(dr){const dw=258,x=Math.max(4,Math.min(r[0]+w-dw,BW-dw-4)),up=r[1]>BH/2,st=up?{left:x+'px',top:'auto',bottom:(BH-r[1]+6)+'px',maxHeight:(r[1]-10)+'px'}:{left:x+'px',top:(r[1]+h+6)+'px',bottom:'auto',maxHeight:(BH-r[1]-h-12)+'px'};
      for(const k in st)if(dr.style[k]!==st[k])dr.style[k]=st[k]}}}
/* the chips and the dock follow the handles while one is dragged or scrolled (one frame at most per input), and after a knob or a fader is let go;
   on the window, because the pictures' own handle drag stops the event at the devices panel */
{const fi=document.getElementById('fxin');if(fi){const q=e=>{const D=e.target.closest&&e.target.closest('#fxin .dev.dvf.dvshut');if(!D||!(D.classList.contains('dvdock')||(D.classList.contains('dvpic')&&DVANC[D.dataset.dvt])))return;if(e.type==='pointermove'&&!e.buttons)return;
    if(D._dv4q)return;D._dv4q=1;requestAnimationFrame(()=>{D._dv4q=0;const own=dvOwnOf(D),B=D.querySelector(':scope>.devb');if(!own||!B)return;if(D.classList.contains('dvpic'))dvChipPlace(D,own,B);else{dvDockPlace(D,own,B,dvType(D,own));dvValPlace(D)}})};
  for(const ty of['pointermove','pointerup','wheel','input','change'])addEventListener(ty,q,{capture:true,passive:true})}}
/* a fader in the dock, on a chip or in the drawer is short: dragged over 150 px for its whole range, as a knob is, not over its own few pixels */
addEventListener('pointermove',()=>{if(typeof cd==='undefined'||!cd||cd._dv4||!cd.el||!cd.el.classList||!cd.el.classList.contains('vb'))return;cd._dv4=1;if(cd.el.closest('#fxin .dev.dvdock,#fxin .dev.dvpic'))cd.h=Math.max(cd.h,150)},true);
