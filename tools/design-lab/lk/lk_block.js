/* ===== task LK (lane A): look tokens =====
   One object LOOK (and the CSS custom properties at the top of the style block, see the LK block before .dacv) holds the look values that the drawers read
   instead of literals, so later tasks (DS design round 2, MD1, SC, DV) change values here, not in the drawers. The user's DR3 picks (27 Nov):
   G3 drafting grid, W1 hairlines, L2 amber units, A1 yellow selection, M3 ambient motion, N3 dense. No new direction: today's colours stay.
   LOOK is declared with var and filled by lkT(), a hoisted function, so a drawer that runs before this block (at start-up) still finds it.
   The Settings look sliders that used the name LOOK before are LOOK_SL now. INS (lane E) reads LOOK through INS.look(): the keys of the same names win. */
var LOOK;
function lkMake(){return{
  v:1,
  grid:'G3',lines:'W1',labels:'L2',accent:'A1',motion:'ambient',density:'dense',dense:true,
  /* G3 drafting grid in the arrangement (alpha of white, times Grid brightness and the theme's factor): every 4 bars, bar, beat, sixteenth, and the
     faint quarter lines across each lane (graph paper). All W1 hairlines: one device pixel. kd evens the weight between 1x, 1.75x and 2x. */
  gr:{phrase:.30,bar:.16,beat:.08,six:.04,row:.028},
  /* the piano roll's three levels (bar, beat, sixteenth) and its octave line */
  pr:{bar:.24,beat:.13,six:.065,oct:.16},
  /* display grids (devices, meters' scales, science drawings): three levels, as INS names them */
  gMaj:'rgba(255,255,255,.13)',gMid:'rgba(255,255,255,.05)',gMin:'rgba(136,136,136,.07)',
  /* line weights in CSS px as INS reads them; a hairline is never thinner than one device pixel (LOOK.hair) */
  lwGrid:.5,lwLine:.5,lwCurve:1,
  /* L2: values in the normal text colour with equal-width digits, units and unit-like labels in amber, case as written (MS would read as megaseconds) */
  ink:'#ececf1',mut:'#8b8b97',lab:'#b7b7c2',tick:'rgba(255,255,255,.32)',tickHi:'rgba(255,255,255,.5)',
  ui:'Inter,system-ui,sans-serif',mono:'"JetBrains Mono",ui-monospace,Menlo,monospace',digits:'tabular',unitCase:'as written',labelCase:'sentence',
  unit:'#ffb547',meas:'#ffb547',
  /* A1: today's yellow is the one selection accent; limits keep their colours */
  sel:'#f5c84c',sel3:'245,200,76',warn:'#f5c84c',over:'#ff6b6b',ok:'#3ecf8e',
  /* N3: track height and row spacing relative to today's (96 px tracks at the user's size; the pick page's 48 against 62 px) */
  dens:{roomy:76/62,today:1,dense:48/62},th0:96,row0:28,rowMin:24,
  hair:d=>1/Math.max(1,d||1),
  ambientOK(){return lkT().motion==='ambient'&&!(typeof UI==='object'&&UI.lite)&&!(typeof AT==='object'&&AT.reduce)&&!document.hidden}
}}
function lkT(){return LOOK||(LOOK=lkMake())}
lkT();
function lkSel(a){return'rgba('+lkT().sel3+','+a+')'}
/* the arrangement's grid values for one drawing (cheap: a few multiplications per view change) */
function lkGrid(dpr){const L=lkT(),G=L.gr,kd=Math.min(1.15,Math.max(.7,Math.sqrt((dpr||1)/1.75))),gk=(typeof UI==='object'&&UI.gridB!=null?UI.gridB:50)/50,tk=(typeof TH==='object'&&TH.grk)||1;
  return{hp:L.hair(dpr),kd,phrase:G.phrase*kd,bar:G.bar*kd,beat:G.beat*kd,six:G.six*kd,rows:L.grid==='G3',rowC:'rgba('+((typeof TH==='object'&&TH.gr)||'255,255,255')+','+Math.min(1,G.row*kd*gk*tk)+')'}}
function lkPR(){const d=(window.devicePixelRatio||1)*(typeof ZOOM==='number'?ZOOM:1),L=lkT(),kd=Math.min(1.15,Math.max(.7,Math.sqrt(d/1.75))),c=a=>'rgba(255,255,255,'+Math.min(1,a*kd)+')';
  return{d,hp:L.hair(d),bar:c(L.pr.bar),beat:c(L.pr.beat),six:c(L.pr.six),oct:c(L.pr.oct)}}
/* L2 on a canvas: the value in the current fill colour, its unit after it in amber; returns the width */
const LKU=/^(.*?[0-9∞])(\s?)([A-Za-zµ%°×][A-Za-z0-9µ%°×/]*|:1)$/;
function lkVU(g,s,x,y){const m=LKU.exec(String(s));if(!m){g.fillText(s,x,y);return g.measureText(s).width}const a=m[1]+m[2],wa=g.measureText(a).width;g.fillText(a,x,y);const f=g.fillStyle;g.fillStyle=lkT().unit;g.fillText(m[3],x+wa,y);g.fillStyle=f;return wa+g.measureText(m[3]).width}
/* L2 in the page: an output's text with its unit in an amber span; the text (textContent) stays exactly the same, and nothing is touched when it did not change */
function lkOut(o,s){s=String(s);if(o.textContent===s&&(o.firstElementChild||!LKU.test(s)))return;const m=LKU.exec(s);if(!m){o.textContent=s;return}o.textContent=m[1]+m[2];const u=document.createElement('span');u.className='lku';u.textContent=m[3];o.appendChild(u)}
/* ---- density (N3) ---- */
function lkDensK(){return lkT().dens[(typeof UI==='object'&&UI.lkDens)||'dense']||lkT().dens.dense}
function lkTh(){return Math.round(lkT().th0*lkDensK())}
/* a project keeps a track height it chose itself; the default (marked thD in its view, or today's 96 px in a view from before LK) follows the Density setting */
function lkIsDef(v){if(!v||v.th==null)return true;if(v.thD!=null)return Math.abs(v.th-v.thD)<.5;return Math.abs(v.th-lkT().th0)<.5}
function lkThFix(){if(!lkIsDef(V))return false;const t=lkTh(),o=V.th;V.th=t;V.thD=t;if(o&&o!==t)V.y=V.y/o*t;try{clampV()}catch(e){}V.thD=V.th;return true}
/* ---- motion (M3) ---- */
function lkApply(){const L=lkT(),u=typeof UI==='object'?UI:{},b=document.body,r=document.documentElement.style,k=lkDensK(),d=(window.devicePixelRatio||1)*(typeof ZOOM==='number'?ZOOM:1);
  L.density=u.lkDens||'dense';L.dense=L.density==='dense';L.motion=u.lkMotion||'ambient';
  if(b){b.classList.toggle('lkm1',L.motion==='signal');b.classList.toggle('lkstill',L.motion!=='ambient')}
  r.setProperty('--lk-hair',(1/Math.max(1,d)).toFixed(4)+'px');r.setProperty('--lk-row',Math.max(L.rowMin,Math.round(L.row0*k))+'px');r.setProperty('--lk-rowpad',Math.round(5*Math.min(k,1.3))+'px');r.setProperty('--lk-dens',k.toFixed(3));
  if(typeof INS==='object')INS._lk=null}
const LK_ROWS=[
 {"id":"density","l":"Density","pg":"layout","ap":"appearance","b":"Density and motion","sc":"app","k":"UI.lkDens","c":"#lkDens","t":"select","d":"dense","h":"How tightly tracks and lists are packed. Dense fits more tracks on the screen, Roomy gives each track more height. A project where you set the track height yourself keeps it.","w":"density dense compact roomy tight spacing track height rows lists"},
 {"id":"motion","l":"Motion","pg":"layout","ap":"appearance","b":"Density and motion","sc":"app","k":"UI.lkMotion","c":"#lkMotion","t":"select","d":"ambient","h":"What may move on its own. Signal only: the playhead, meters and displays. Signal and transitions: also short animations when things open and close. Ambient: also slow drawings on empty and waiting screens, never in Light mode.","w":"motion animation ambient transitions still calm moving drawings reduce"}];
try{for(const r of LK_ROWS)if(!STX.has(r.id)){STT.push(r);STX.set(r.id,r)}}catch(e){}
const LK_HOOKS=window.LK_HOOKS=window.LK_HOOKS||{};
Object.assign(LK_HOOKS,{
  /* for lane B's new Settings window: the two rows in the S4 table's shape, page Appearance (they sit on the Layout page until that page exists) */
  appearanceRows:()=>LK_ROWS.map(r=>({...r,pg:'appearance'})),
  look:lkT,apply:lkApply,th:lkTh,isDefaultHeight:lkIsDef,ambientOK:()=>lkT().ambientOK(),sel:lkSel,unitText:lkOut,unitCanvas:lkVU,grid:lkGrid,pianoGrid:lkPR});
function lkSync(){const a=document.getElementById('lkDens'),m=document.getElementById('lkMotion');if(a)a.value=UI.lkDens||'dense';if(m)m.value=UI.lkMotion||'ambient'}
{const a=document.getElementById('lkDens'),m=document.getElementById('lkMotion');
 if(a)a.onchange=()=>{const was=lkIsDef(V);UI.lkDens=a.value;lkApply();if(was){V.thD=null;V.th=lkT().th0;lkThFix()}dirty=true;saveUI()};
 if(m)m.onchange=()=>{UI.lkMotion=m.value;lkApply();try{const s=document.getElementById('splash');if(s&&typeof SPLBG==='object'&&SPLBG.running&&!SPLBG.running()&&lkT().ambientOK())SPLBG.attach(s)}catch(e){}saveUI()};
 lkSync()}
lkApply();lkThFix();
{const _sp=switchProject;switchProject=function(id){const nx=PJ.list.find(p=>p.id===id),keep=V.thD;if(nx&&nx.view&&id!==PJ.cur)delete V.thD;const r=_sp.apply(this,arguments);if(V.thD==null&&!(nx&&nx.view))V.thD=keep;try{if(lkThFix())dirty=true}catch(e){}return r}}
addEventListener('resize',()=>{try{lkApply()}catch(e){}});
/* ===== end of task LK ===== */
