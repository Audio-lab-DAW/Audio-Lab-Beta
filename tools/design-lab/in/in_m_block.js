/* ===== lane E (task IN-M): level meters, M2 (peak and RMS in one bar) =====
   The user's pick M2 (docs/design-round-4-instruments.md): the peak bar stays as it is (same speed, reading, colours and hold settings, Flat bars and
   every other fader design kept) and gets a bright core, the RMS over 300 ms (AES17: a sine reads its peak level), with the part of the bar above it
   faint (DIGICheck style). Read-outs: peak, RMS and crest factor. The scale follows the fader taper (M1: a mark per dB from +6 to -12, every 3 dB to
   -24, then every 6). Nothing new is read from the audio: the meter engine (mtrPeak) already reads each analyser's new samples once per frame; the
   same samples now also feed a 300 ms window (INS.pr) that keeps the sum of squares and the highest sample in 10 ms pieces.
   - INS.pr: the window; INS.mbar: the one bar drawer for canvas meters (the transport meter, the mixer's meter view, the Settings preview), for
     task DS-T2's transport meter TM1 to reuse; INM.veil: the same core for the meters made of page elements (mixer fader meters, track headers, the
     device panel's track meter): a dark veil (an inset shadow along the top of the bar itself: paint only, no extra box) from the top of the bar down to the RMS level.
   - The core shows only while the reading is Peak (the default): RMS, VU and Loudness readings are averages already. Read-outs always.
   - Crest factor = highest sample over 300 ms against the true RMS of the same 300 ms (a sine reads 3.0 dB, a square 0 dB).
   - Track taps (N.aL, N.aR) hold 256 samples (5.8 ms), so a track's RMS is built from the snapshots the meters read (about half of the time at
     120 meter frames a second): within about half a dB on steady tones; the master's taps hold 2048, so it sees every sample. IN-S moves the sizes.
   - Light level: the read-outs update half as often; the core follows each meter's own drawing (nothing extra is drawn when a meter is hidden). */
INS.pr=function(st,a,i0,i1,sr){/* 300 ms window in 10 ms pieces: st.rms (dBFS, AES17), st.pk (dBFS, highest sample), st.cf (dB, crest factor) */
  if(st.sr!==sr){st.sr=sr;st.sb=Math.max(1,Math.round(sr*.01));st.nb=30;st.rs=new Float64Array(30);st.rm=new Float32Array(30);st.ri=0;st.acc=0;st.mx=0;st.cnt=0;st.sum=0}
  let acc=st.acc,mx=st.mx,cnt=st.cnt;const sb=st.sb,rs=st.rs,rm=st.rm;
  for(let i=i0;i<i1;i++){const v=a[i];acc+=v*v;const q=v<0?-v:v;if(q>mx)mx=q;if(++cnt===sb){st.sum+=acc-rs[st.ri];rs[st.ri]=acc;rm[st.ri]=mx;if(++st.ri===st.nb){st.ri=0;let s=0;for(let j=0;j<st.nb;j++)s+=rs[j];st.sum=s}acc=0;mx=0;cnt=0}}
  st.acc=acc;st.mx=mx;st.cnt=cnt;let m=0;for(let j=0;j<st.nb;j++)if(rm[j]>m)m=rm[j];const ms=Math.max(0,st.sum)/(st.nb*sb);
  st.rms=ms>1e-12?10*Math.log10(ms)+3.0103:-240;st.pk=m>1e-6?20*Math.log10(m):-240;st.cf=ms>1e-12&&m>1e-6?Math.max(0,st.pk-(st.rms-3.0103)):0;return st};
INS.mbar=function(g,x,y,w,h,p,r,fill,horiz){/* one level bar (M2): p = the peak and r = the RMS as 0..1 along the bar (r<0: no core); the part above the core faint */
  p=p>1?1:p>0?p:0;g.fillStyle=fill;if(!(r>=0)){if(horiz)g.fillRect(x,y,w*p,h);else g.fillRect(x,y+h*(1-p),w,h*p);return}
  r=Math.min(p,r);const a0=g.globalAlpha;g.globalAlpha=a0*INM.faint;if(horiz)g.fillRect(x+w*r,y,w*(p-r),h);else g.fillRect(x,y+h*(1-p),w,h*(p-r));
  g.globalAlpha=a0;if(horiz)g.fillRect(x,y,w*r,h);else g.fillRect(x,y+h*(1-r),w,h*r)};
const INM={faint:.38,/* how bright the peak part above the RMS core is on canvas meters; the page-element meters use the veil colour in the CSS (.insv) */
  n:0,nm:0,/* veil writes and mixer passes, for the test */
  st(an){/* the 300 ms window of this analyser, if the meter engine read it in the last 30 frames */const s=an&&an._ms&&an._ms.pr;return s&&s.sr&&FRN-s.f<30&&FRN>=s.f?s:null},
  core(){return mtrO().alg==='peak'},
  rdb(an){const s=INM.st(an);return s&&INM.core()?s.rms:null},
  rfr(an,map){/* the core as 0..1 along a bar drawn with map(dB) -> 0..1, or -1 */const d=INM.rdb(an);return d==null?-1:d>-60?map(d):0},
  read(an,an2){/* the louder of two channels: {pk,rms,cf} */const a=INM.st(an),b=an2?INM.st(an2):null;if(!a&&!b)return null;const s=!b||(a&&a.rms>=b.rms)?a:b;return{pk:Math.max(a?a.pk:-240,b?b.pk:-240),rms:s.rms,cf:s.cf}},
  txt(v,u){return v>-200?INS.fmt(v,u):INS.MIN+'∞'+INS.TS+u},
  VEIL:'rgba(7,8,11,.6)',
  hpx(el){/* an element's height in CSS px, read again about every 60 frames (a read can cost a layout) */if(el._hf==null||FRN-el._hf>60||FRN<el._hf){el._hf=FRN;el._hp=el.clientHeight}return el._hp},
  veil(el,y){/* the veil is an inset shadow along the top of the bar itself, y CSS px tall: paint only, no extra box, and the bar is restyled every
     frame anyway; half-pixel steps, and a move of less than 1.5 px waits up to two frames (the RMS over 300 ms moves slowly) */
    const q=y>0?Math.round(y*2)/2:0,o=el._iv;if(q===o)return;if(o!=null&&q&&o&&Math.abs(q-o)<1.5&&FRN-(el._ivf||0)<3)return;el._iv=q;el._ivf=FRN;INM.n++;el.style.boxShadow=q?`inset 0 ${q}px 0 0 ${INM.VEIL}`:''},
  fmVeil(u,an){/* a mixer fader meter (.fm u, full height, clipped to the peak by its own drawing): veil from the top down to the RMS */const d=INM.rdb(an);
    INM.veil(u,d==null||u._c==null?0:(1-dbN(d))*INM.hpx(u))},
  hdVeil(b,an){/* a bar of page elements (.vm i b, .tdm i b): its height is the peak (b._h, a percentage of the box it sits in); veil from its top down to the RMS */const d=INM.rdb(an),p=parseFloat(b._h);
    INM.veil(b,d==null||!(p>0)||!b.parentElement?0:Math.max(0,p-dbN(d)*100)/100*INM.hpx(b.parentElement))},
  tip:0};
/* the meter engine: the same new samples also feed the 300 ms window (no second read of the analyser) */
{const _mp=mtrPeak;mtrPeak=function(an){const s0=an&&an._ms,t0=s0?s0.t:-1,r=_mp.apply(this,arguments);try{const st=an&&an._ms;if(st&&st.t!==t0){const a=MTB[an.fftSize],sr=an.context.sampleRate;if(a){const p=st.pr||(st.pr={}),dt=t0>0?Math.min(.25,(st.t-t0)/1000):.016;INS.pr(p,a,INS.fresh(a,p,dt*sr),a.length,sr);p.f=FRN}}}catch(e){}return r}}
/* mixer: the fader meters of the strips on screen (and the master), after the mixer's own drawing */
{const _dmM=drawMixer;drawMixer=function(){let v=null;try{v=inmVis()}catch(e){}const r=_dmM.apply(this,arguments);try{inmMixer(v)}catch(e){}return r}}
function inmVis(){/* which strips are on screen, from positions read about every 60 frames (and when the mixer is rebuilt) and the scroll position
   kept by a scroll listener: no layout read on most frames */const w=document.getElementById('mixWin');if(!w||w.hidden||!MXV||FRN%2)return null;const ms=w.querySelector('.mxs');if(!ms)return null;
  if(!ms._inmS){ms._inmS=1;ms._inmSL=ms.scrollLeft;ms.addEventListener('scroll',()=>{ms._inmSL=ms.scrollLeft},{passive:true})}
  let G=ms._inmG;if(!G||FRN-G.f>60||FRN<G.f||G.n!==ms.childElementCount||G.v!==MXV){G=ms._inmG={f:FRN,n:ms.childElementCount,v:MXV,cw:ms.clientWidth,a:[]};ms._inmSL=ms.scrollLeft;for(const mx of ms.children)G.a.push([mx,mx.offsetLeft,mx.offsetWidth])}
  const sl=ms._inmSL,f=FRN;for(const[mx,l,wd] of G.a){const x=l-sl;mx._inmOff=x+wd<-20||x>G.cw+20?f:-1}return f}
function inmMixer(off){const w=document.getElementById('mixWin');if(!w||w.hidden||!MXV||FRN%2)return;INM.nm++;const slow=!((inmMixer.k=((inmMixer.k|0)+1))%(INS.lite()?16:8));
  for(const cv of MXV){if(!cv.isConnected)continue;const id=cv.dataset.id;if(cv.dataset.hk&&cv.dataset.hk!==id)continue;const isM=id==='master',N=!isM&&NODES.get(id),aL=isM?anL:N&&N.aL,aR=isM?anR:N&&N.aR;
    let mx=cv._inmMx;if(!mx||!mx.isConnected||!mx.contains(cv))mx=cv._inmMx=cv.closest('.mx');if(!mx)continue;if(!isM&&off!=null&&mx._inmOff===off)continue;/* off screen: nothing (as the mixer's own drawing) */
    let fm=mx._inmU;if(!fm||FRN-mx._inmUf>120||(fm.length&&!fm[0].isConnected)){fm=mx._inmU=[...mx.querySelectorAll('.fm u')];mx._inmUf=FRN}/* looked up again every 120 frames, not on every frame (strips without fader meters too) */if(fm.length===2){INM.fmVeil(fm[0],aL);INM.fmVeil(fm[1],aR)}
    if(isM&&!slow&&!(INM.lvEl&&INM.lvEl.isConnected))inmMaster(w);/* the box at once after the mixer is rebuilt; its numbers at the slow rate */
    if(slow){const q=INM.read(aL,aR);if(isM)inmMaster(w,q);let pe=mx._inmP;if(!pe||!pe.isConnected)pe=mx._inmP=mx.querySelector('.mxpkr');if(pe){const t='Highest peak of this channel in dB. Click to reset, Shift and click to reset all.'+(q?`\nNow (300 ms): peak ${INM.txt(q.pk,'dBFS')}, RMS ${INM.txt(q.rms,'dBFS')}, crest ${INS.fmt(q.cf,'dB')}`:'');if(pe._tt!==t){pe._tt=t;pe.title=t}}}}}
function inmMaster(w,q){/* the master strip: RMS and crest above the true peak, target and stereo boxes */let d=INM.lvEl;if(!d||!d.isConnected){const me=w.querySelector('.mx.master .mxme');if(!me)return;d=INM.lvEl=me.querySelector('.inslv');
  if(!d){me.insertAdjacentHTML('afterbegin','<div class="inslv" title="Level of the mix over the last 300 ms: RMS (a sine reads its peak level, AES17) and crest factor (how far the peaks stand above the RMS: a sine reads 3 dB, a squashed mix a few dB, a lively mix 10 dB and more)."><div class="mxmh"><small>RMS</small><span><b>–</b> <small>dBFS</small></span></div><div class="mxmh"><small>Crest</small><span><b>–</b> <small>dB</small></span></div></div>');d=INM.lvEl=me.querySelector('.inslv')}}
  if(q===undefined)return;const b=d._b||(d._b=d.querySelectorAll('b')),a=q&&q.rms>-200?INS.num(q.rms,1):'–',c=q&&q.rms>-200?INS.num(q.cf,1):'–';if(b[0]._t!==a){b[0]._t=a;b[0].textContent=a}if(b[1]._t!==c){b[1]._t=c;b[1].textContent=c}}
/* track headers and the device panel's track meter */
{const _tmM=trackMeters;trackMeters=function(){const r=_tmM.apply(this,arguments);try{inmHeaders()}catch(e){}return r}}
function inmHeaders(){const L=trackMeters.L;if(!L)return;const now=performance.now();if(now-(inmHeaders.t||0)<(INS.lite()?66:33))return;inmHeaders.t=now;/* 30 times a second, as the header glass repaints */for(const{id,bars} of L){const N=NODES.get(id);if(!N||!N.aL)continue;if(bars[0])INM.hdVeil(bars[0],N.aL);if(bars[1])INM.hdVeil(bars[1],N.aR);
    if(id===selT){const tb=trackMeters.tb;if(tb&&tb.isConnected)for(let ci=0;ci<2;ci++){const bb=tb.children[ci]&&tb.children[ci].firstChild;if(bb&&bb.tagName==='B')INM.hdVeil(bb,ci?N.aR:N.aL)}}}}
/* the transport's peak box: RMS and crest in its tooltip (twice a second) */
{const _mtM=meters;meters=function(){const r=_mtM.apply(this,arguments);try{const now=performance.now();if(now-INM.tip>(INS.lite()?1000:500)){INM.tip=now;const pb=document.getElementById('peakBox'),q=ctx&&anL?INM.read(anL,anR):null;
  if(pb){const t='Peak level of the master output in dB. Red means the signal is clipping (above 0 dB). Click to reset the readout.'+(q&&q.rms>-200?`\nNow (300 ms): peak ${INM.txt(q.pk,'dBFS')}, RMS ${INM.txt(q.rms,'dBFS')}, crest ${INS.fmt(q.cf,'dB')}`:'');if(pb._tt!==t){pb._tt=t;pb.title=t}}}}catch(e){}return r}}
/* the Settings preview: RMS and crest beside the peak read-out */
{const _pvM=mtrPv;mtrPv=function(){const r=_pvM.apply(this,arguments);try{const pk=document.getElementById('mtrPkV');if(pk&&pk.offsetParent){const box=pk.parentElement;let rv=document.getElementById('mtrRmV');
  if(!rv){pk.nextElementSibling&&pk.nextElementSibling.insertAdjacentHTML('afterend','<b id="mtrRmV" class="inmv">–</b><small class="inmv">RMS</small><b id="mtrCfV" class="inmv">–</b><small class="inmv">Crest</small>');rv=document.getElementById('mtrRmV')}
  const now=performance.now();if(rv&&now-(mtrPv.t9||0)>(INS.lite()?250:125)){mtrPv.t9=now;const q=play.on&&anL?INM.read(anL,anR):null,a=q&&q.rms>-200?INS.num(q.rms,1):'–',c=q&&q.rms>-200?INS.fmt(q.cf,'dB'):'–';if(rv._t!==a){rv._t=a;rv.textContent=a}const cf=document.getElementById('mtrCfV');if(cf&&cf._t!==c){cf._t=c;cf.textContent=c}}}}catch(e){}return r}}
/* ===== end of lane E IN-M ===== */
