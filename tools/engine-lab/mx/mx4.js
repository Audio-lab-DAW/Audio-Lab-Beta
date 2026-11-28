/* ===== task MX-4 (lane K, mixing engine): X3 the Ducker's Spectral focus, X19's Bass mono switch =====
   Plan and tests: docs/mixing-build.md, tools/ui-tests/taskMX_4.py. Names start with mx / MX.
   - Spectral focus: the Ducker's "Listen to" menu gets "Spectral (32 bands)": the track goes down only in the bands where the trigger plays
     (built in the Ducker's worklet, abxWLF.mxSp). Its latency (one frame) goes through fxLat, so MX-2 lines everything up, live and in export.
   - Bass mono: t.bmono = {on, f} on a track, S.bmono on the master (both optional: without them nothing is built). Below f the side goes away
     (the side through a Linkwitz-Riley high-pass of 48 dB per octave, the mid through the matching all-pass, so the sum stays flat).
     Live it sits inside the track's utility (after width and phase, before the trim) and at the start of the master chain; renderMix builds the same.
   - MX_HOOKS.bandFilter(ctx, lo, hi, order) for lane E's band listen (X17) and the low-band correlation (X19's meter); MX_HOOKS.bassMono(t). */
function mxSpecN(sr){return sr>64000?2048:1024}
AGIC.spec='<path d="M4 20v-5M8 20V8M12 20v-9M16 20V5M20 20v-7"/>';
const MXBMF=[50,80,100,120,150,200,300,500];
const mxBmOf=t=>t&&(t.kind==='master'?S.bmono:t.bmono);
function mxBmOn(t){const b=mxBmOf(t);return!!(b&&b.on)}
function mxBmF(b){const f=+(b&&b.f);return isFinite(f)&&f>0?Math.max(50,Math.min(500,Math.round(f))):120}
/* Linkwitz-Riley = a Butterworth filter twice. Order 4: Butterworth 2 (Q 0.7071); order 8: Butterworth 4 (Q 1.3066 and 0.5412).
   The browser's lowpass and highpass take Q in dB; its allpass takes it as a plain number. */
const MXLRQ={4:[Math.SQRT1_2],8:[1.3065629648763766,0.5411961001461970]};
function mxLRB(c,type,f,ord,src,fl){const Q=MXLRQ[ord]||MXLRQ[4];let prev=src;for(let r=0;r<2;r++)for(const q of Q){const b=c.createBiquadFilter();b.type=type;b.frequency.value=f;b.Q.value=20*Math.log10(q);if(prev)prev.connect(b);prev=b;if(fl)fl.push(b)}return prev}
function mxBmChain(c,f){const G=(v,n)=>{const g=c.createGain();g.gain.value=v;g.channelCount=n||1;g.channelCountMode='explicit';g.channelInterpretation=n?'speakers':'discrete';return g};
  const i=G(1,2),sp=c.createChannelSplitter(2),mg=c.createChannelMerger(2),mid=G(1),side=G(1),lm=G(.5),rm=G(.5),ls=G(.5),rs=G(-.5),oL=G(1),oR=G(1),ns=G(-1),fl=[];
  i.connect(sp);sp.connect(lm,0);sp.connect(ls,0);sp.connect(rm,1);sp.connect(rs,1);lm.connect(mid);rm.connect(mid);ls.connect(side);rs.connect(side);
  let a=mid;for(const q of MXLRQ[8]){const b=c.createBiquadFilter();b.type='allpass';b.frequency.value=f;b.Q.value=q;a.connect(b);a=b;fl.push(b)}
  const h=mxLRB(c,'highpass',f,8,side,fl);a.connect(oL);a.connect(oR);h.connect(oL);h.connect(ns);ns.connect(oR);oL.connect(mg,0,0);oR.connect(mg,0,1);
  return{i,out:mg,f,fl,setF(v){if(v===this.f)return;this.f=v;const now=c.currentTime;for(const b of fl)b.frequency.setTargetAtTime(v,now,.02)}}}
/* export: the same chain after the utility (tracks) and before the master's effects */
function mxBmOff(c,t,src){const b=t?t.bmono:S.bmono;if(!(b&&b.on))return src;const B=mxBmChain(c,mxBmF(b));src.connect(B.i);return B.out}
/* live, tracks: inside the utility, between its width and phase stage and its trim (MX-4 named the utility's merger mxM) */
let MXBMM=null;
function mxBmSync(){if(!ctx)return;for(const t of S.tracks){const N=NODES.get(t.id),U=N&&N.ut;if(!U||!U.mxM)continue;const on=mxBmOn(t);
   if(on&&U.mxBM){U.mxBM.setF(mxBmF(t.bmono));continue}if(!on&&!U.mxBM)continue;
   if(U.mxBM){try{U.mxM.disconnect(U.mxBM.i)}catch(e){}try{U.mxBM.out.disconnect()}catch(e){}U.mxBM=null;U.mxM.connect(U.out)}
   else{const B=mxBmChain(ctx,mxBmF(t.bmono));try{U.mxM.disconnect(U.out)}catch(e){}U.mxM.connect(B.i);B.out.connect(U.out);U.mxBM=B}}
  const mo=mxBmOn({kind:'master'});if(mo!==!!MXBMM||(MXBMM&&MXBMM.c!==ctx))routeMaster();else if(MXBMM)MXBMM.setF(mxBmF(S.bmono))}
/* live, master: routeMaster starts its chain from here */
function mxBmMst(src){if(!mxBmOn({kind:'master'})){if(MXBMM){try{MXBMM.out.disconnect()}catch(e){}MXBMM=null}return src}
  if(!MXBMM||MXBMM.c!==ctx){MXBMM=mxBmChain(ctx,mxBmF(S.bmono));MXBMM.c=ctx}else MXBMM.setF(mxBmF(S.bmono));try{MXBMM.out.disconnect()}catch(e){}src.connect(MXBMM.i);return MXBMM.out}
{const _sg=syncGraph;syncGraph=function(){const r=_sg.apply(this,arguments);try{mxBmSync()}catch(e){console.error('AudioLab bass mono',e)}return r}}
function mxBmSet(t,on,f){if(!t)return;pushUndo();const b={on:!!on,f:mxBmF({f:f!=null?f:(mxBmOf(t)||{}).f})};if(t.kind==='master')S.bmono=b;else t.bmono=b;changed(true);syncGraph();try{mxBmUI()}catch(e){}}
const MXBMTIP='Bass mono: below this frequency the left and right sides play the same bass, so the low end stays solid in mono, on club systems and on a phone. Above it nothing changes. Click to turn it on or off; right-click or click the number to choose the frequency';
function mxBmMenu(t,x,y){const b=mxBmOf(t),cur=mxBmF(b);openMenu(x,y,[{head:'Bass mono below'},...MXBMF.map(f=>({label:f+' Hz',check:!!(b&&b.on)&&f===cur,sub:f<=100?'Only the deepest bass':f<=150?'Kick and bass (usual)':'Bass and low mids',act:()=>mxBmSet(t,true,f)})),'-',{label:'Off',check:!(b&&b.on),act:()=>mxBmSet(t,false,cur)}])}
function mxBmBtn(t){const b=mxBmOf(t),on=!!(b&&b.on),f=mxBmF(b),e=document.createElement('button');e.type='button';e.className='mxbm'+(on?' on':'');e.dataset.mxbm=t.kind==='master'?'master':t.id;
  e.setAttribute('aria-pressed',on?'true':'false');e.innerHTML='<span>Bass mono</span><b data-mxbmf>'+f+' <span class="lku">Hz</span></b>';e.title=MXBMTIP;return e}
/* the switch: in the track's first device (under Mono), and above the master's devices */
function mxBmUI(){const D=document.querySelector('#fxin .tdev2[data-id]');document.querySelectorAll('#fxin .mxbm').forEach(e=>e.remove());
  if(D){const t=trkById(D.dataset.id);if(!t||t.kind==='master')return;const g=D.querySelector('.tdbs');if(g)g.appendChild(mxBmBtn(t));return}
  if(typeof selT!=='undefined'&&selT==='__m'){const m=mxBmBtn({kind:'master'});m.classList.add('mxbmm');fxin.prepend(m)}}
{const _rf=renderFx;renderFx=function(){const r=_rf.apply(this,arguments);try{mxBmUI();mxSpecUI()}catch(e){console.error('AudioLab bass mono switch',e)}return r}}
document.addEventListener('click',e=>{const b=e.target.closest&&e.target.closest('.mxbm[data-mxbm]');if(!b)return;e.stopPropagation();e.preventDefault();const t=b.dataset.mxbm==='master'?{kind:'master'}:trkById(b.dataset.mxbm);if(!t)return;
  if(e.target.closest('[data-mxbmf]')){const r=b.getBoundingClientRect();mxBmMenu(t,r.left,r.bottom+2);return}mxBmSet(t,!mxBmOn(t))},true);
document.addEventListener('contextmenu',e=>{const b=e.target.closest&&e.target.closest('.mxbm[data-mxbm]');if(!b)return;e.stopPropagation();e.preventDefault();const t=b.dataset.mxbm==='master'?{kind:'master'}:trkById(b.dataset.mxbm);if(t)mxBmMenu(t,e.clientX,e.clientY)},true);
/* the Spectral focus: a tooltip on the Listen to menu of each Ducker */
const MXSPTIP='Spectral (32 bands): this track goes down only in the frequencies where the trigger plays, so a kick takes the bass out under itself and leaves the rest of the bass alone. Adds about 20 ms of latency, which the other tracks wait for';
function mxSpecUI(){for(const o of fxin.querySelectorAll('.dev select option[value="spec"]')){o.title=MXSPTIP;const s=o.parentElement;if(s&&!s.dataset.mxsp){s.dataset.mxsp='1';s.title='Listen to: which part of the trigger makes this track duck. '+MXSPTIP}}}
Object.assign(MX_HOOKS,{
  /* a Linkwitz-Riley band (order 4 by default, or 8): lo 0 for no high-pass, hi 0 for no low-pass; {in, out} */
  bandFilter(c,lo,hi,ord){const i=c.createGain();let p=i;if(lo>0)p=mxLRB(c,'highpass',lo,ord===8?8:4,p);if(hi>0&&hi<c.sampleRate/2)p=mxLRB(c,'lowpass',hi,ord===8?8:4,p);if(p===i){const o=c.createGain();i.connect(o);p=o}return{in:i,out:p}},
  /* Bass mono of a track or of the master ({kind:'master'}): {on, f} */
  bassMono(t){const b=mxBmOf(t);return{on:!!(b&&b.on),f:mxBmF(b)}},
  setBassMono(t,on,f){mxBmSet(t,on,f)},
  /* the Spectral Ducker's 32 band gains while playing (1 = not ducked), for lane E's drawing; the band edges in Hz */
  specBands(t,f){const N=t&&NODES.get(t.id),X=N&&f&&N.fxm.get(f.id);return X&&X.mxSB&&X.m&&performance.now()-X.m.t<400?X.mxSB:null},
  specEdges(){return Array.from({length:33},(_,b)=>20*Math.pow(1000,b/32))}});
