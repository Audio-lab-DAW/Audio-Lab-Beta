/* ===== v0.300: display-first devices, step 5 (task DV-5): the synths =====
   docs/devices-display-first.md sections 7 and 10. The rule for devices not in the pick table: the rail starts open when a device has more than about
   eight parameters or has pages, otherwise it starts closed with hover reveal.
   - Venom (16 and an editor), Plant (12), Wavetable (18), Orbit, Vector FM and Bounce (pages): rail open, as today. Orbit, Vector FM and Bounce already
     draw their picture on under the rail; Venom, Plant and Wavetable draw fixed panels beside it, so their pictures stay as they are. Closed, they show
     DV-1's revealed panel (too many controls for one row); On the picture falls back to hover reveal on them (their pictures have no place for most
     controls).
   - Saw lead, Square lead, Soft pad, Strings, Pluck and Soft keys (8 controls): they start closed with hover reveal when the user adds one (the
     instrument browser's Add or Use, a drop, a click; never a project being opened, a demo, a template or a script). Hover reveal is the bottom dock in
     two rows (Cutoff, Resonance, Detune; Attack, Decay, Sustain, Release, Level; Gain after a hairline), the preset row and Wave as a pill on top.
     On the picture: Cutoff and Resonance at the filter's corner, Attack at the top of the envelope, Decay where it falls to the sustain level,
     Sustain on that level, Release on the way down; the preset, Wave, Detune, Level and Gain in More. The values line leaves out what the picture
     writes (Attack and Release; the cutoff it writes sits under the eye's pill, so the line keeps it).
   Built on DV-4's placing routine (dvDock, dvValPlace, dvChipPlace, dvNear); only the basic instruments' anchors (dvBasicH) and words are added here.
   No sound, parameter or stored value changes; only where the controls are drawn and the starting state of a newly added instrument. */
const DV5={n:{dock:0,pic:0,start:0},q:[],ev:null,cnt:0};
const DVBASIC=new Set(['saw','square','pad','strings','pluck','keys']);
/* the rule applied to the synths (DV-12's check reads this table): open = the rail starts open */
const DVIRULE={venom:{open:true},plant:{open:true},wtab:{open:true},orb:{open:true},vfm:{open:true},bball:{open:true},
  saw:{open:false},square:{open:false},pad:{open:false},strings:{open:false},pluck:{open:false},keys:{open:false}};
/* the basic instruments' picture writes Attack and Release ("5 ms up, 250 ms down"); its own words, in canvas pixels */
for(const ty of DVBASIC){DVTXT[ty]={skip:['Attack','Release'],clear:(w,h)=>{const tall=h>=150,x1=tall?0:w/2,y1=tall?h/2:0,W=tall?w:w/2;return[[4,0,54,17],[W-62,0,62,17],[x1+4,y1,64,18],[x1+W-150,y1,150,18]]}};
  DVANC[ty]={cutoff:0,res:0,a:1,d:2,s:3,r:4}}
/* the picture fills its box (rail open or closed), as on the rail-open picks of DV-2 */
for(const ty of DVBASIC)DVFILL.add(ty);
/* the places in the basic instruments' picture (duBasicDraw's own geometry): the filter's corner, the envelope's top, the fall to the sustain level,
   the sustain level, the way down */
function dvBasicH(I,w,h){const P=PRESETS[I.preset]||{},v=k=>I[k]??P[k]??IPAR[k][2],tall=h>=150,B=tall?[[0,0,w,h/2],[0,h/2,w,h/2]]:[[0,0,w/2,h],[w/2,0,w/2,h]],L=[];
  {const[x0,y0,W,H]=B[0],fc=clamp(v('cutoff'),30,20000),Lx=x0+8,R=x0+W-8,T=y0+20,Bt=y0+H-10,X=f=>Lx+(R-Lx)*Math.log(f/30)/Math.log(20000/30),Y=db=>T+(Bt-T)*(18-clamp(db,-42,18))/60;
   L.push({x:X(fc),y:Y(v('res')),l:'Cutoff'})}
  {const[x0,y0,W,H]=B[1],a=v('a'),d=v('d'),s=v('s'),r=v('r'),Lx=x0+8,R=x0+W-8,T=y0+22,Bt=y0+H-10,f=t=>Math.pow(t,.45),wa=f(a),wd=f(d),wr=f(r),tot=wa+wd+.55+wr,sx=(R-Lx)/tot,xa=Lx+wa*sx,xd=xa+wd*sx,xh=xd+.55*sx,Y=l=>Bt-(Bt-T)*l;
   L.push({x:xa,y:T,l:'Attack'},{x:xd,y:Y(s),l:'Decay'},{x:(xd+xh)/2,y:Y(s),l:'Sustain'},{x:xh+(R-xh)*.3,y:Y(s*.45),l:'Release'})}
  return L}
{const _h=dvHandles;dvHandles=function(D,own,ty){if(!D||D.dataset.d!=='inst'||!DVBASIC.has(ty))return _h.apply(this,arguments);
  const B=D.querySelector(':scope>.devb'),cv=B&&B.querySelector('canvas.duviz');if(!cv||!cv.clientWidth||!own)return null;const w=cv.clientWidth,h=cv.clientHeight;let L;try{L=dvBasicH(own,w,h)}catch(e){return null}
  const z=ZOOM||1,cr=cv.getBoundingClientRect(),br=B.getBoundingClientRect(),ox=(cr.left-br.left)/z-B.clientLeft,oy=(cr.top-br.top)/z-B.clientTop;
  /* the picture has no handles to drag: its places matter to the chips only, so the dock sits at the bottom (DD4) */
  if(!D.classList.contains('dvpic'))L=[];
  const clear=DVTXT[ty].clear(w,h).map(r=>[r[0]+ox,r[1]+oy,r[2],r[3]]);return{cv,w,h,ox,oy,clear,L:L.map((q,i)=>({x:q.x+ox,y:q.y+oy,l:q.l,i}))}}}
/* ---- starting state: a basic instrument the user adds starts closed with hover reveal ---- */
function dv5Q(I){try{const ev=window.event;if(!ev||!ev.isTrusted||!I||!DVIRULE[I.preset])return;if(DV5.ev!==ev){DV5.ev=ev;DV5.cnt=0;DV5.q=[]}DV5.cnt++;DV5.q.push(I)}catch(e){}}
{const _mt=mkTrack;mkTrack=function(kind){const t=_mt.apply(this,arguments);if(kind==='inst'&&t)dv5Q(t.inst);return t}}
{const _ci=chooseIB;chooseIB=function(){const tr=ib&&ib.mode==='inst'?ib.track:null;const r=_ci.apply(this,arguments);if(tr&&tr.inst&&tr.inst.kOpen===undefined&&tr.inst.kMode===undefined)dv5Q(tr.inst);return r}}
function dv5Start(){if(!DV5.q.length)return;const q=DV5.q,n=DV5.cnt;DV5.q=[];DV5.ev=null;DV5.cnt=0;if(n>2)return;
  for(const I of q){const s=DVIRULE[I.preset];if(!s||I.kOpen!==undefined||I.kMode!==undefined)continue;if(!s.open){I.kOpen=false;DV5.n.start++}}}
{const _rf=renderFx;renderFx=function(){try{dv5Start()}catch(e){}return _rf.apply(this,arguments)}}
/* ---- the dock and On the picture for the basic instruments ---- */
{const _fr=dvFrame;dvFrame=function(D,t,fl){const r=_fr.apply(this,arguments);try{dv5(D,t)}catch(e){console.error('AudioLab display-first step 5',e)}return r}}
function dv5(D,t){if(D.dataset.d!=='inst'||!D.classList.contains('dvf')||!D.classList.contains('dvshut'))return;const B=D.querySelector(':scope>.devb'),own=dvOwnOf(D,t);if(!B||!own)return;const ty=dvType(D,own);if(!DVBASIC.has(ty))return;
  if(D.classList.contains('dvpic')){DV5.n.pic++;dvChipPlace(D,own,B);return}
  DV5.n.dock++;const S=B.querySelector(':scope>.dfs'),tb=S&&S.querySelector(':scope>.ndtb'),pr=S&&S.querySelector(':scope>.dspr');if(tb&&pr){tb.classList.add('dvdtb');pr.append(tb)}
  dvDock(D,own,B,ty);
  /* the device is never narrower than the pill (preset, Change, Wave) beside the eye */
  const P=B.querySelector(':scope>.dvdpre'),T=B.querySelector(':scope>.dvtr');if(P&&T){const need=P.offsetWidth+T.offsetWidth+26;if(B.clientWidth<need){B.style.minWidth=need+'px';dvDockPlace(D,own,B,ty)}}
  dvValPlace(D)}
DVPIC.saw=DVPIC.square=DVPIC.pad=DVPIC.strings=DVPIC.pluck=DVPIC.keys={lay:dvpBasic};
function dvpBasic(D,own,B){const ty=dvType(D,own),A=DVANC[ty],S=B.querySelector(':scope>.dfs'),G=B.querySelector(':scope>.dug');if(!S||!A)return[];dvTips(S);
  const rest=[];for(const el of[...S.querySelectorAll('.pgrid [data-c]')]){const k=el.dataset.c.split(':').pop();if(k in A){el.classList.add('dvface','dvchip');el.dataset.dva=A[k];B.append(el)}else rest.push(el)}
  const pr=S.querySelector(':scope>.dspr'),tb=S.querySelector(':scope>.ndtb'),lv=rest.filter(e=>/:gain$/.test(e.dataset.c)),snd=rest.filter(e=>!lv.includes(e));if(G)G.classList.add('dvdgain');
  return[{head:'Preset',els:[pr]},{head:'Sound',els:[tb,...snd]},{head:'Output',els:[...lv,G]}]}
