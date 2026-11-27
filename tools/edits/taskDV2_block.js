/* ===== v0.276: display-first devices, step 2 (task DV-2): starting states, the rail-open picks =====
   docs/devices-display-first.md sections 7 and 10.
   - Starting states (section 7 table) for devices the user adds: Compressor, Sidechain, Echo delay and Space reverb start with the rail closed and
     hover reveal; Pro EQ closed, on the picture; Voice, Psy Bass and the drum designers with the rail open (the default). Only a device made by one
     user action (a click, a key, a drop: one or two new devices) gets it; a project being opened, a demo song or a script keeps every device as stored,
     so old projects open exactly as before. The rule for the other devices comes with their groups (DV-5 to DV-11).
   - The rail-open picks: the picture fills the display box (Kick, Snare, Clap, Hat and Tom designers, Voice; Psy Bass already did); the Kick
     designer's Click menu and Key track move from the picture onto the rail, and the rail is fitted again.
   - The frame takes the LOOK tokens of task LK: W1 hairlines on the rail and the pill (--lk-hair), L2 units in amber small caps in the values line.
   The drawing inside the displays is lane E's; only the boxes are sized here. */
const DVSTART={comp:{open:false},side:{open:false},delay:{open:false},reverb:{open:false},eq:{open:false,mode:'picture'},voice:{open:true}};
const DVFILL=new Set(['kick','zsnare','zclap','zhat','ztom','voice','psyb']);
const DV2={q:[],ev:null,n:0,applied:0};
/* new effects made inside one trusted user event are queued; the next render gives them their starting state */
{const _mk=mkFx;mkFx=function(type){const f=_mk.apply(this,arguments);try{const ev=window.event;if(ev&&ev.isTrusted&&f&&DVSTART[type]){if(DV2.ev!==ev){DV2.ev=ev;DV2.n=0;DV2.q=[]}DV2.n++;DV2.q.push(f)}}catch(e){}return f}}
function dvStartApply(){if(!DV2.q.length)return;const q=DV2.q,n=DV2.n;DV2.q=[];DV2.ev=null;DV2.n=0;if(n>2)return;
  for(const f of q){const s=DVSTART[f.type];if(!s||f.kOpen!==undefined||f.kMode!==undefined)continue;f.kOpen=s.open;if(s.mode)f.kMode=s.mode;DV2.applied++}}
{const _rf=renderFx;renderFx=function(){try{dvStartApply()}catch(e){}return _rf.apply(this,arguments)}}
/* the picked rail-open devices: controls that sat in the picture go onto the rail, the picture fills its box */
function dvPre(D,t){const own=dvOwnOf(D,t);if(!own)return;const ty=dvType(D,own);if(!DVFILL.has(ty))return;
  /* a picture never gets narrower than it is: it only grows into the room the frame gives it */
  for(const el of D.querySelectorAll(':scope>.devb>.dfv>canvas,:scope>.devb>.dfv>.pzc'))if(el.offsetWidth)el.style.minWidth=el.offsetWidth+'px';
  D._dvw0=D.offsetWidth;
  D.classList.add('dvfill');
  const B=D.querySelector(':scope>.devb'),S=B&&B.querySelector(':scope>.dfs'),ks=B&&B.querySelector(':scope>.dfv>.kside');
  if(ks&&S){const row=document.createElement('div');row.className='dvkrow';row.append(...ks.children);const pr=S.querySelector(':scope>.dspr');if(pr)pr.after(row);else S.prepend(row);ks.remove();
    for(const el of row.querySelectorAll('select'))if(!el.title&&!(el.closest('label')||{}).title)el.title='Click: the sound at the very start of the kick';
    try{duFit(D)}catch(e){}}}
{const _fr=dvFrame;dvFrame=function(D,t,fl){try{dvPre(D,t)}catch(e){console.error('AudioLab display-first step 2',e)}const r=_fr.apply(this,arguments);try{dvFitBox(D)}catch(e){}return r}}
/* devices with a set width (Psy Bass, Emit, the vector synths...): the display box never runs past the device's edge (DV-1 gave it the old strip's
   26 px on top of a width the device had already fixed, which cut off the gain and the pin) */
function dvFitBox(D){const B=D.querySelector(':scope>.devb');if(!B||!D.classList.contains('dvf'))return;
  /* a picked device whose controls moved onto the rail keeps the width it had (the picture gives up the difference) */
  if(D._dvw0&&!D.classList.contains('dvshut')){const d=D.offsetWidth-D._dvw0;if(d>0){const w=B.offsetWidth-d;B.style.minWidth=w+'px';B.style.maxWidth=w+'px';dvRail(D)}}
  const over=B.offsetLeft+B.offsetWidth-D.clientWidth;if(over<=0)return;
  const w=Math.max(0,B.offsetWidth-over);B.style.minWidth=w+'px';B.style.maxWidth=w+'px';B.style.flex='none';dvRail(D)}
/* L2: the values line writes units in amber small caps */
{const _vv=dvVals;dvVals=function(D){const r=_vv.apply(this,arguments);const V=D&&D.querySelector(':scope>.devb>.dvval');if(V&&V._h!==V._l2h)dvL2(V);return r}}
function dvL2(V){for(const b of V.querySelectorAll('b')){if(b.querySelector('i'))continue;const m=/^(.*?\d)\s?([A-Za-zµ%°][A-Za-z%°/]*)$/.exec(b.textContent);if(m){b.textContent=m[1];const i=document.createElement('i');i.textContent=m[2];b.append(i)}}V._l2h=V._h}
