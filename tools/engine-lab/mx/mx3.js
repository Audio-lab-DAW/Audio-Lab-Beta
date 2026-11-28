/* ===== task MX-3 (lane K, mixing engine): X1 sidechain from anything, X4 duck under the kick =====
   X1. Compressor, Gate, Multiband, OTT and the EQ's dynamic bands can listen to another track (f.p.sc={src,tap,dev}; absent: the device as before,
   bit for bit). Tap points: after its effects (default, as the Ducker), after its fader, before its effects, after one of its devices.
   How each device is keyed (the inventory MX-3 starts with):
   - Compressor, Multiband (3-band and Mid/Side) and OTT use the browser's compressor, which has no key input. With a source set, the browser compressor
     stays in the path but is set neutral (threshold 0 dB, no knee, 1:1: a pure 6 ms delay), and a keyed gain stage after it (worklet al-mxkey) runs the
     same algorithm as the browser's compressor (Chromium's DynamicsCompressorKernel: knee curve, ratio, automatic make-up, detector, adaptive release),
     measured from the key. The browser's 6 ms pre-delay gives the same look-ahead as before. Multiband and OTT split the key with the same crossovers.
   - Gate is a worklet with one input: with a source set it switches to al-mxgate (the Gate's own processor, reading the level from a second input).
   - The EQ's dynamic bands measure their band on the main thread (DYNEQ): with a source set, the band's detector listens to the key instead.
     The export does not render dynamic EQ movement (before MX-3 too), so a keyed dynamic band is heard while playing only; see the log.
   Keys get MX-2's compensation (the key arrives with the sound the device works on), live and in export; the loop check covers every key.
   X4. "Duck under the kick", tuned for tails: a switch on each return (its first device on the left, and the Output menu of its mixer strip), and a choice in
   the cable menu whenever a cable is drawn to a track (to a sidechain or a Ducker): a Ducker at the end of the return, attack 0.5 ms, no hold, back in one
   16th at the song tempo (15/bpm s, re-tuned when the tempo changes), keyed from the kick. Hooks: MX_HOOKS.scBadge (lane I), duckTails (lane D, lane C),
   scSet, scPick, kick. */
const MXSCT={comp:'Compressor',gate:'Gate',mband:'Multiband',ott:'OTT',eq:'EQ'};
const MXTAP={fx:'after its effects',fader:'after its fader',pre:'before its effects',dev:'after a device'};
/* the worklets: appended to the Ducker's worklet code (one bundle, so the Gate's processor is in reach) */
function mxWLF(){
 const L2=x=>20*Math.log10(x),D2=x=>Math.pow(10,x/20),HP=Math.PI/2;
 /* the browser's compressor (Chromium DynamicsCompressorKernel), measured from a key */
 class MxCK{constructor(sr){this.sr=sr;this.det=1;this.cg=1;this.maxA=-1;this.rate=1;this.sdg=1;this.key=''}
  setp(th,ra,kn,at,rl){const key=th+'|'+ra+'|'+kn+'|'+at+'|'+rl;if(key===this.key)return;this.key=key;
   this.lt=D2(th);this.slope=1/ra;this.kth=D2(th+kn);this.kthdb=L2(this.kth);this.k=this.kAt(1/ra,th,kn);this.yk=L2(this.knee(this.kth,this.k));this.mk=Math.pow(1/this.sat(1,this.k),.6);
   this.atF=Math.max(.001,at)*this.sr;const rf=rl*this.sr,y1=rf*.09,y2=rf*.16,y3=rf*.42,y4=rf*.98;
   this.kA=.9999999999999998*y1+1.8432219684323923e-16*y2-1.9373394351676423e-16*y3+8.824516011816245e-18*y4;
   this.kB=-1.5788320352845888*y1+2.3305837032074286*y2-.9141194204840429*y3+.1623677525612032*y4;
   this.kC=.5334142869106424*y1-1.272736789213631*y2+.9258856042207512*y3-.18656310191776226*y4;
   this.kD=.08783463138207234*y1-.1694162967925622*y2+.08588057951595272*y3-.00429891410546283*y4;
   this.kE=-.042416883008123074*y1+.1115693827987602*y2-.09764676325265872*y3+.028494263462021576*y4;this.srf=.0025*this.sr}
  knee(x,k){return x<this.lt?x:this.lt+(1-Math.exp(-k*(x-this.lt)))/k}
  sat(x,k){return x<this.kth?this.knee(x,k):D2(this.yk+this.slope*(L2(x)-this.kthdb))}
  slopeAt(x,k){if(x<this.lt)return 1;const x2=x*1.001;return(L2(this.knee(x2,k))-L2(this.knee(x,k)))/(L2(x2)-L2(x))}
  kAt(ds,th,kn){const x=D2(th+kn);let mn=.1,mx=1e4,k=5;for(let i=0;i<15;i++){if(this.slopeAt(x,k)<ds)mx=k;else mn=k;k=Math.sqrt(mn*mx)}return k}
  env(){const sdg=Math.asin(Math.min(1,this.det))/HP;this.sdg=sdg;let cd=L2(this.cg/sdg);
   if(sdg>this.cg){this.maxA=-1;if(!isFinite(cd))cd=-1;let x=Math.min(0,Math.max(-12,cd));x=.25*(x+12);const x2=x*x,x3=x2*x,x4=x2*x2;this.rate=D2(5/(this.kA+this.kB*x+this.kC*x2+this.kD*x3+this.kE*x4))}
   else{if(!isFinite(cd))cd=1;if(this.maxA===-1||this.maxA<cd)this.maxA=cd;this.rate=1-Math.pow(.25/Math.max(.5,this.maxA),1/this.atF)}}
  step(a){const att=a<=1e-4?1:this.sat(a,this.k)/a,adb=Math.max(2,-L2(att)),srr=D2(adb/this.srf)-1;this.det+=(att-this.det)*(att>this.det?srr:1);if(!(this.det<=1))this.det=1;
   if(this.rate<1)this.cg+=(this.sdg-this.cg)*this.rate;else this.cg=Math.min(1,this.cg*this.rate);return Math.sin(HP*this.cg)}}
 class MxKey extends AudioWorkletProcessor{constructor(o){super(o);const q=(o&&o.processorOptions)||{};this.p=q.p||{};this.live=!!q.live;this.K=new MxCK(sampleRate);this.c=0;this.n=0;this.mg=1;
   this.port.onmessage=e=>{if(e.data&&e.data.p)this.p=e.data.p}}
  process(I,O){const a=I[0],k=I[1],o=O[0],n=o[0].length,p=this.p,K=this.K;K.setp(+p.th||0,Math.max(1,+p.ra||1),Math.max(0,+p.kn||0),+p.at||.003,+p.rl||.25);
   const aL=a&&a[0],aR=a&&(a[1]||a[0]),kL=k&&k[0],kR=k&&(k[1]||k[0]),oL=o[0],oR=o[1]||o[0],mk=K.mk;let mg=this.mg;
   for(let i=0;i<n;i++){if((this.c++&31)===0)K.env();const x=kL?Math.max(Math.abs(kL[i]),Math.abs(kR[i])):0,g=K.step(x);if(g<mg)mg=g;const t=g*mk;oL[i]=aL?aL[i]*t:0;oR[i]=aR?aR[i]*t:0}
   if(this.live){this.n+=n;if(this.n>=512){this.port.postMessage({g:mg});mg=1;this.n=0}}else mg=1;this.mg=mg;return true}}
 registerProcessor('al-mxkey',MxKey);
 /* the Gate, with its level measured from a second input (the same processor otherwise) */
 if(typeof Gate==='function'){class MxGate extends Gate{process(I,O){const x=io(I,O);if(!x)return true;const[L,R,oL,oR,n]=x,Kq=I[1]&&I[1].length?I[1]:null,KL=Kq&&Kq[0],KR=Kq&&(Kq[1]||Kq[0]),p=this.p,thr=p.thr??-40,hy=p.hyst??4,fl=dB(p.floor??-80),look=Math.round((p.look||0)*sampleRate/1000),sr=sampleRate,
    ca=1-Math.exp(-1/(Math.max(.05,p.att||1)/1000*sr)),cr=1-Math.exp(-1/(Math.max(1,p.rel||120)/1000*sr)),hold=(p.hold||40)/1000*sr,hpc=1-Math.exp(-TAU*(p.hpf||20)/sr),lpc=1-Math.exp(-TAU*Math.min(sr*.45,p.lpf||20000)/sr),ex=p.mode==='expander',ra=p.ratio||2,D=this.D,dec=Math.exp(-1/(.005*sr));
   for(let i=0;i<n;i++){let d=KL?(KL[i]+KR[i])*.5:0;this.hp[0]+=hpc*(d-this.hp[0]);d-=this.hp[0];this.lp[0]+=lpc*(d-this.lp[0]);d=this.lp[0];const a=Math.abs(d);this.lv=a>this.lv?a:this.lv*dec+a*(1-dec);const ldb=lg(this.lv);
    if(!this.open&&ldb>thr){this.open=true;this.hold=hold}else if(this.open){if(ldb>thr-hy)this.hold=hold;else if(--this.hold<=0)this.open=false}
    let tg;if(ex){const under=Math.max(0,thr-ldb);tg=Math.max(fl,dB(-under*(ra-1)))}else tg=this.open?1:fl;if(ex&&this.open)tg=1;this.g+=(tg-this.g)*(tg>this.g?ca:cr);
    this.dl[0][this.w]=L[i];this.dl[1][this.w]=R[i];const rp=(this.w-look+D)%D,g=this.g;if(p.listen){oL[i]=d;oR[i]=d}else{oL[i]=this.dl[0][rp]*g;oR[i]=this.dl[1][rp]*g}this.w=(this.w+1)%D;if(g<this.mg)this.mg=g;if(ldb>this.ml)this.ml=ldb;if(this.open)this.mo=1}
   this.c+=n;if(this.c>=512){this.c=0;this.port.postMessage({lv:this.ml,g:this.mg,open:this.mo});this.mg=1;this.ml=-120;this.mo=0}return true}}
  registerProcessor('al-mxgate',MxGate)}}
ABXWL+='\n;('+mxWLF.toString()+')();';
/* ---- which devices listen to which track ---- */
function mxScOk(f){return!!(f&&MXSCT[f.type]&&f.p&&f.p.sc&&typeof f.p.sc.src==='string'&&f.p.sc.src)}
function mxKeySrcId(f){if(!f||!f.p)return null;if(f.type==='duck')return typeof f.p.src==='string'?f.p.src:null;return mxScOk(f)?f.p.sc.src:null}
function mxTapOf(f){return f&&f.type!=='duck'&&mxScOk(f)&&MXTAP[f.p.sc.tap]?f.p.sc.tap:'fx'}
/* how much of the source's own latency is in the key (null: all of it, plus its compensation delay: the key is taken after its effects) */
function mxTapLat(s,f,sr){const tp=mxTapOf(f);if(tp==='fx'||tp==='fader')return null;if(tp==='pre'||s.fxByp)return 0;let n=0;for(const d of s.fx||[]){if(!d||!d.on)continue;n+=fxLat(d,sr);if(d.id===f.p.sc.dev)return n}return null}
function mxDevName(f){return f?(MXSCT[f.type]||(typeof FXN_NAME==='object'&&FXN_NAME[f.type])||(typeof fxName==='function'?fxName(f):f.type)):''}
/* the params of each keyed compressor stage, from the device's own settings */
function mxStages(X,f){const p=f.p||{};
 if(f.type==='comp')return[{th:+p.threshold,ra:+p.ratio,kn:6,at:p.attack/1000,rl:p.release/1000}];
 if(f.type==='ott'){const d=(+p.down||0)/100;return[0,1,2].map(()=>({th:-10-d*38,ra:2+d*14,kn:6,at:.002,rl:(+p.time||0)/1000}))}
 if(f.type==='mband')return X.mxK.fk.map(k=>({th:k.threshold.value,ra:k.ratio.value,kn:k.knee.value,at:k.attack.value,rl:k.release.value}));
 return[]}
const mxNeutral=k=>{k.threshold.value=0;k.knee.value=0;k.ratio.value=1};
function mxWhen(c,fn){if(typeof OfflineAudioContext!=='undefined'&&c instanceof OfflineAudioContext){(c._pre=c._pre||[]).push(fn);if(!c._wl)wlLoad(c)}else if(c._wl)fn();else{(c._wlq=c._wlq||[]).push(fn);wlLoad(c)}}
function mxKW(c,X,i){const n=new AudioWorkletNode(c,'al-mxkey',{numberOfInputs:2,numberOfOutputs:1,outputChannelCount:[2],channelCount:2,channelCountMode:'explicit',processorOptions:{p:X.mxK.st[i]||{},live:c===ctx}});
 const M=X.mxK;n.port.onmessage=e=>{const d=e.data;if(d&&d.g!=null)M.gr[i]=20*Math.log10(Math.max(1e-5,d.g))};return n}
/* a Linkwitz-Riley split of the key, like the device's own crossover */
function mxLR(c,src,type,f){const a=c.createBiquadFilter(),b=c.createBiquadFilter();for(const q of[a,b]){q.type=type;q.frequency.value=f;q.Q.value=.7071}src.connect(a);a.connect(b);return{out:b,set(v){a.frequency.value=v;b.frequency.value=v},n:[a,b]}}
/* key up: the device gets a key input (X.mxK.key, at once, so a render can wire it) and its keyed engine (when the worklets are ready) */
function mxKeyUp(c,X,f){if(!X||X.mxK)return X&&X.mxK;const key=c.createGain(),M={key,c,type:f.type,st:[],gr:[0,0,0,0,0],on:false,src:null,E:null,f};X.mxK=M;
 if(f.type==='comp'&&X.mxG){const k0=X.k;M.k0=k0;X.k={get reduction(){return M.on?M.gr[0]:k0.reduction},threshold:k0.threshold,ratio:k0.ratio,knee:k0.knee,attack:k0.attack,release:k0.release};
  M.s0=X.set;X.set=p=>{M.s0(p);mxKeyParams(X,f)};
  mxWhen(c,()=>{if(X.mxK!==M||M.on)return;try{M.st=mxStages(X,f);const w=mxKW(c,X,0),G=X.mxG;k0.disconnect(G);k0.connect(w,0,0);key.connect(w,0,1);w.connect(G);M.w=[w];mxNeutral(k0);M.on=true}catch(e){console.warn('AudioLab sidechain',e)}})}
 else if(f.type==='ott'&&X.mxB){M.s0=X.set;X.set=p=>{M.s0(p);mxKeyParams(X,f)};
  mxWhen(c,()=>{if(X.mxK!==M||M.on)return;try{M.st=mxStages(X,f);const lo=mxLR(c,key,'lowpass',120),m1=mxLR(c,key,'highpass',120),mi=mxLR(c,m1.out,'lowpass',2500),hi=mxLR(c,key,'highpass',2500),ks=[lo.out,mi.out,hi.out];
   M.w=X.mxB.map((B,j)=>{const w=mxKW(c,X,j);B.k.disconnect(B.g);B.k.connect(w,0,0);ks[j].connect(w,0,1);w.connect(B.g);mxNeutral(B.k);return w});M.on=true}catch(e){console.warn('AudioLab sidechain',e)}})}
 else if(f.type==='mband'&&X.B){const all=[...X.B,...(X.MC||[])];M.real=all.map(b=>b.comp);
  M.fk=all.map(b=>{const k=b.comp,P=v=>({value:v});const q={threshold:P(k.threshold.value),ratio:P(k.ratio.value),knee:P(k.knee.value),attack:P(k.attack.value),release:P(k.release.value)};const j=all.indexOf(b);Object.defineProperty(q,'reduction',{get(){return M.on?M.gr[j]:k.reduction}});return q});
  M.s0=X.set;X.set=p=>{M.s0(p);mxKeyParams(X,f)};
  mxWhen(c,()=>{if(X.mxK!==M||M.on)return;try{all.forEach((b,j)=>{for(const n of['threshold','ratio','knee','attack','release'])M.fk[j][n].value=b.comp[n].value});M.st=mxStages(X,f);const p=f.p||{},l2=mxLR(c,key,'lowpass',p.x2||2500),l1=mxLR(c,l2.out,'lowpass',p.x1||200),h1=mxLR(c,l2.out,'highpass',p.x1||200),h2=mxLR(c,key,'highpass',p.x2||2500);M.xo=[l1,h1,h2,l2];
   const sp=c.createChannelSplitter(2),mid=c.createGain(),sl=c.createGain(),sr=c.createGain(),sid=c.createGain();key.connect(sp);sp.connect(mid,0);sp.connect(mid,1);mid.gain.value=.5;sp.connect(sl,0);sp.connect(sr,1);sl.gain.value=.5;sr.gain.value=-.5;sl.connect(sid);sr.connect(sid);
   const ks=[l1.out,h1.out,h2.out,mid,sid];M.w=all.map((b,j)=>{const w=mxKW(c,X,j);b.comp.disconnect(b.mk);b.comp.connect(w,0,0);ks[j].connect(w,0,1);w.connect(b.mk);mxNeutral(b.comp);return w});
   all.forEach((b,j)=>{b.comp=M.fk[j]});M.all=all;M.on=true}catch(e){console.warn('AudioLab sidechain',e)}})}
 else if(f.type==='gate'&&X.mxO){mxWhen(c,()=>{if(X.mxK!==M||M.on||!X.node)return;try{const n0=X.node,G=new AudioWorkletNode(c,'al-mxgate',{numberOfInputs:2,numberOfOutputs:1,outputChannelCount:[2],channelCount:2,channelCountMode:'explicit',processorOptions:{p:X.sp?X.sp(X.p):X.p}});
   G.port.onmessage=n0.port.onmessage;X.in.disconnect(n0);n0.disconnect(X.mxO);X.in.connect(G,0,0);key.connect(G,0,1);G.connect(X.mxO);M.n0=n0;X.node=G;M.on=true}catch(e){console.warn('AudioLab sidechain',e)}})}
 else if(f.type==='eq'&&X.build){M.b0=X.build;X.build=p=>{M.b0(p);mxEqKey(X)};mxEqKey(X);M.on=true}
 return M}
function mxEqKey(X){const M=X.mxK;if(!M)return;for(const d of X.dets||[]){if(d.mxk)continue;try{X.in.disconnect(d.bp)}catch(e){}M.key.connect(d.bp);d.mxk=1}}
/* key down: the device as it was (only live; a render builds its nodes fresh) */
function mxKeyDown(X,f){const M=X&&X.mxK;if(!M)return;const c=M.c;try{if(M.src){try{M.src.disconnect(M.E?M.E.g:M.key)}catch(e){}}if(M.E){try{M.E.d.disconnect()}catch(e){}}
  if(M.type==='comp'){X.set=M.s0;X.k=M.k0;if(M.on){const w=M.w[0];try{M.k0.disconnect(w)}catch(e){}w.disconnect();M.k0.connect(X.mxG)}X.set(f.p)}
  else if(M.type==='ott'){X.set=M.s0;if(M.on)X.mxB.forEach((B,j)=>{const w=M.w[j];try{B.k.disconnect(w)}catch(e){}w.disconnect();B.k.connect(B.g);B.k.knee.value=6});X.set(f.p)}
  else if(M.type==='mband'){X.set=M.s0;if(M.on)M.all.forEach((b,j)=>{const w=M.w[j];b.comp=M.real[j];try{b.comp.disconnect(w)}catch(e){}w.disconnect();b.comp.connect(b.mk);b.comp.knee.value=6});X.set(f.p)}
  else if(M.type==='gate'){if(M.on){const G=X.node;try{X.in.disconnect(G)}catch(e){}G.disconnect();X.node=M.n0;X.in.connect(M.n0);M.n0.connect(X.mxO);X.set(X.p)}}
  else if(M.type==='eq'){X.build=M.b0;X.sig='';if(X.p)X.set(X.p)}
  try{M.key.disconnect()}catch(e){}}catch(e){console.warn('AudioLab sidechain',e)}X.mxK=null}
/* settings into the keyed stages; the browser compressors stay neutral */
function mxKeyParams(X,f){const M=X.mxK;if(!M)return;
 if(M.type==='mband'&&M.xo){const p=f.p||{};M.xo[0].set(p.x1);M.xo[1].set(p.x1);M.xo[2].set(p.x2);M.xo[3].set(p.x2)}
 if(!M.on)return;const st=mxStages(X,f),sg=JSON.stringify(st);if(sg!==M.sg){M.sg=sg;M.st=st;(M.w||[]).forEach((w,i)=>w.port.postMessage({p:st[i]}))}
 if(M.type==='comp')mxNeutral(M.k0);else if(M.type==='ott')X.mxB.forEach(B=>mxNeutral(B.k))}
/* the live tap on the source track */
function mxTapNode(SN,s,f){const tp=mxTapOf(f);if(tp==='pre')return SN.mxh||SN.in;if(tp==='fader')return SN.pan;if(tp==='dev'&&!s.fxByp){const d=(s.fx||[]).find(x=>x.id===f.p.sc.dev&&x.on),x=d&&SN.fxm.get(d.id);if(x)return x.out}return SN.ut.out}
/* the offline tap (renderMix: n = the source's nodes, FXN = every device built) */
function mxTapOff(n,f,FXN){const tp=mxTapOf(f);if(tp==='pre')return n.hin||n.tin;if(tp==='fader')return n.pn;if(tp==='dev'){const e=FXN.get(f.p.sc.dev);if(e&&e.x)return e.x.out}return n.pre}
/* live: every keyed device after each syncGraph (nothing runs while nothing changes) */
function mxScSync(){if(!ctx)return;const K=MXSOL,sr=ctx.sampleRate;
 for(const t of S.tracks){const N=NODES.get(t.id);if(!N)continue;for(const f of t.fx||[]){if(!MXSCT[f.type])continue;const X=N.fxm.get(f.id);if(!X)continue;const want=mxScOk(f);
   if(!want){if(X.mxK)mxKeyDown(X,f);continue}const M=X.mxK||mxKeyUp(ctx,X,f);if(!M)continue;M.f=f;mxKeyParams(X,f);
   const s=trkById(f.p.sc.src),SN=s&&s!==t?NODES.get(s.id):null,tap=SN&&!abxReach(t,s)?mxTapNode(SN,s,f):null,e=tap&&K?(K.ek.get(f.id)||0)/sr:0;
   if(e>0&&!M.E){const E=mxEdge();E.d.connect(M.key);if(M.src){try{M.src.disconnect(M.key)}catch(err){}M.src.connect(E.g)}M.E=E}
   const to=M.E?M.E.g:M.key;if(M.src!==tap){if(M.src){try{M.src.disconnect(to)}catch(err){}}M.src=tap;if(tap)tap.connect(to)}if(M.E)mxDSet(M.E.d,M.E.g,e)}}
 mxTailTune()}
{const _sg=syncGraph;syncGraph=function(){const r=_sg.apply(this,arguments);try{mxScSync()}catch(e){console.error('AudioLab sidechain',e)}return r}}
/* ---- choosing the source ---- */
function mxScCan(f,src){const me=(abxFind(f.id)||{}).t,s=trkById(src);if(!s)return{ok:false,why:'That track no longer exists.'};if(s===me)return{ok:false,why:'A device cannot listen to its own track here: choose Its own sound.'};
 if(me&&abxReach(me,s))return{ok:false,why:me.name+' already plays into '+s.name+', so this would make a loop.'};return{ok:true,why:''}}
function mxScSet(f,src,tap,dev){if(!f||!MXSCT[f.type])return{ok:false,why:'This device has no sidechain.'};
 if(!src){if(!f.p.sc)return{ok:true};pushUndo();delete f.p.sc;changed(true);try{renderFx()}catch(e){}try{cabSoon()}catch(e){}return{ok:true}}
 const c=mxScCan(f,src);if(!c.ok){try{toast(c.why)}catch(e){}return c}pushUndo();f.p.sc={src,tap:MXTAP[tap]?tap:'fx'};if(tap==='dev'&&dev)f.p.sc.dev=dev;changed(true);try{renderFx()}catch(e){}try{cabSoon()}catch(e){}return{ok:true}}
function mxScPick(f,x,y){if(!f||!MXSCT[f.type])return;const me=(abxFind(f.id)||{}).t,cur=mxScOk(f)?f.p.sc:null,dn=mxDevName(f);
 const it=[{head:'What should '+dn+(me?' on '+me.name:'')+' listen to?'},{label:'Its own sound',sub:'No sidechain: it reacts to '+(me?me.name:'this track'),check:!cur,act:()=>mxScSet(f,null)},'-'];
 const qs=S.tracks.filter(q=>q!==me&&q.kind!=='group'&&!(me&&abxReach(me,q)));
 for(const q of qs){const on=cur&&cur.src===q.id,k=[{label:'After its effects',sub:'The usual choice: '+q.name+' as you hear it, before its fader',check:on&&cur.tap==='fx',act:()=>mxScSet(f,q.id,'fx')},
   {label:'After its fader',sub:'Follows its volume and mute',check:on&&cur.tap==='fader',act:()=>mxScSet(f,q.id,'fader')},{label:'Before its effects',sub:'Its sound before any device on it',check:on&&cur.tap==='pre',act:()=>mxScSet(f,q.id,'pre')}];
  const ds=(q.fx||[]).filter(d=>d&&d.on);if(ds.length){k.push('-');for(const d of ds)k.push({label:'After '+mxDevName(d),sub:'Its sound right after this device',check:on&&cur.tap==='dev'&&cur.dev===d.id,act:()=>mxScSet(f,q.id,'dev',d.id)})}
  it.push({label:q.name,dot:q.color,check:!!on,sub:on?MXTAP[cur.tap]||'':(q.kind==='return'?'return':''),kids:k})}
 if(!qs.length)it.push({label:'No other track to listen to',dis:true});openMenu(x,y,it)}
/* the Sidechain row in each keyable device (under its presets) */
function mxScRows(){const box=document.getElementById('fxin');if(!box)return;for(const d of box.querySelectorAll('.dev.fxd[data-id],.dev.eq2[data-id]')){const fd=abxFind(d.dataset.id),f=fd&&fd.f;if(!f||!MXSCT[f.type])continue;
  const fs=d.querySelector('.dfs')||d.querySelector('.eqside');if(!fs)continue;fs.querySelector('.mxscr')?.remove();const sc=mxScOk(f)?f.p.sc:null,s=sc&&trkById(sc.src),bad=!!(s&&!mxScCan(f,s.id).ok);
  const w=document.createElement('div');w.className='mxscr';const b=document.createElement('button');b.type='button';b.className='mxscb'+(s?' set':'')+(bad?' bad':'');b.dataset.mxsc=f.id;b.style.setProperty('--sc',s?s.color||'#cfd3db':'transparent');
  b.innerHTML='<span class="mxscl">Sidechain</span><i></i><span class="mxscn">'+esc(s?s.name:'Own sound')+'</span><b aria-hidden="true">▾</b>';
  b.title='Sidechain: which sound this '+mxDevName(f)+' reacts to. Now: '+(s?s.name+', '+(MXTAP[sc.tap]||MXTAP.fx)+(sc.tap==='dev'?' ('+mxDevName((s.fx||[]).find(x=>x.id===sc.dev))+')':''):'its own sound')+'.'+(bad?' That would make a loop, so it listens to nothing for now.':'')+' Click to let another track, for example the kick, drive it.'+(f.type==='eq'?' Only the dynamic bands listen.':'');
  b.setAttribute('aria-haspopup','menu');w.appendChild(b);const pr=fs.querySelector('.dspr');if(pr)pr.after(w);else fs.appendChild(w)}}
/* ---- X4: duck under the kick, tuned for tails ---- */
function mxKick(){try{const h=typeof NI_HOOKS==='object'&&NI_HOOKS&&NI_HOOKS.kickBass;if(typeof h==='function'){const r=h();const k=r&&(r.kick||r.k);const t=typeof k==='string'?trkById(k):k&&k.id?trkById(k.id):null;if(t)return t}}catch(e){}
 return S.tracks.find(t=>t.kind!=='group'&&t.kind!=='return'&&/\bkick\b/i.test(t.name||''))||S.tracks.find(t=>t.kind!=='group'&&t.kind!=='return'&&/kick|bd\b/i.test(t.name||''))||null}
const mxTailRl=()=>Math.round(clamp(15000/(S.bpm||120),10,1500));
function mxTailOf(r){return r&&(r.fx||[]).find(f=>f.type==='duck'&&f.p&&f.p.mxTail)||null}
function mxDuckTails(ret,kick){if(!ret||ret==='master')return null;kick=kick||mxKick();if(!kick||kick===ret)return null;if(abxReach(ret,kick)){try{toast(ret.name+' already plays into '+kick.name+', so this would make a loop.')}catch(e){}return null}
 pushUndo();let f=mxTailOf(ret);if(!f){f=mkFx('duck');ret.fx.push(f)}Object.assign(f.p,{amt:70,th:-30,gain:0,at:.5,hd:0,rl:mxTailRl(),cv:0,la:0,ff:120,fo:'low',ls:false,src:kick.id,mxTail:true});f.on=true;
 changed(true);try{renderFx()}catch(e){}try{cabSoon()}catch(e){}try{toast(ret.name+' now ducks under '+kick.name+' for one 16th note on every hit.')}catch(e){}return f}
function mxTailOff(ret){const f=mxTailOf(ret);if(!f)return;pushUndo();ret.fx.splice(ret.fx.indexOf(f),1);changed(true);try{renderFx()}catch(e){}try{cabSoon()}catch(e){}}
function mxTailTune(){const rl=mxTailRl();for(const t of S.tracks)for(const f of t.fx||[])if(f.type==='duck'&&f.p&&f.p.mxTail&&f.p.rl!==rl){f.p.rl=rl;const N=ctx&&NODES.get(t.id),X=N&&N.fxm.get(f.id);if(X)X.set(f.p)}}
function mxTailToggle(ret,x,y){if(mxTailOf(ret)){mxTailOff(ret);return}const k=mxKick();if(k&&k!==ret){mxDuckTails(ret,k);return}
 const qs=S.tracks.filter(q=>q!==ret&&q.kind!=='group'&&q.kind!=='return'&&!abxReach(ret,q));openMenu(x||200,y||200,[{head:'No track called Kick: which track is the kick?'},...qs.map(q=>({label:q.name,dot:q.color,act:()=>mxDuckTails(ret,q)}))])}
const MXTAILTIP='Duck under the kick: this return dips each time the kick hits and comes back within one 16th note at the song tempo, so reverb and delay tails stay out of the way of the kick. Tuned for tails: fast attack, no hold.';
function mxTailBtn(){const D=document.querySelector('#fxin .tdev2[data-id]');if(!D)return;D.querySelector('.mxtail')?.remove();const t=trkById(D.dataset.id);if(!t||t.kind!=='return')return;const f=mxTailOf(t),k=f?trkById(f.p.src):mxKick();
 const b=document.createElement('button');b.type='button';b.className='mxtail'+(f?' on':'');b.dataset.mxtail=t.id;b.setAttribute('aria-pressed',f?'true':'false');
 b.innerHTML='<i></i><span>Duck under '+esc(k?k.name:'the kick')+'</span>';b.title=MXTAILTIP+(f?' On: click to turn it off.':k?'':' There is no track called Kick yet: click to choose one.');
 const a=D.querySelector('.tdfx');if(a)a.after(b);else{const z=D.querySelector('.tdb2');if(z)z.appendChild(b)}}
{const _rf=renderFx;renderFx=function(){const r=_rf.apply(this,arguments);try{mxScRows();mxTailBtn()}catch(e){console.error('AudioLab sidechain row',e)}return r}}
document.addEventListener('click',e=>{const b=e.target.closest&&e.target.closest('.mxscb[data-mxsc]');if(b){e.stopPropagation();e.preventDefault();const fd=abxFind(b.dataset.mxsc),r=b.getBoundingClientRect();if(fd)mxScPick(fd.f,r.left,r.bottom+2);return}
 const t=e.target.closest&&e.target.closest('.mxtail[data-mxtail]');if(t){e.stopPropagation();e.preventDefault();const r=t.getBoundingClientRect();mxTailToggle(trkById(t.dataset.mxtail),r.left,r.bottom+2)}},true);
/* the Output menu of a return's mixer strip offers the same switch */
{const _om=mxOutMenu;mxOutMenu=function(t,x,y){const r=_om.apply(this,arguments);try{if(t&&t.kind==='return'&&Array.isArray(MENU)&&!ctxm.hidden){const on=!!mxTailOf(t),k=on?trkById(mxTailOf(t).p.src):mxKick();
  openMenu(x,y,[...MENU,'-',{label:'Duck under '+(k?k.name:'the kick')+', tuned for tails',sub:MXTAILTIP,check:on,act:()=>mxTailToggle(t,x,y)}])}}catch(e){console.error(e)}return r}}
/* the cable menu: a cable to a track offers its devices' sidechains and the tails Ducker */
{const _ao=abxOpts;abxOpts=function(a,b){const it=_ao.apply(this,arguments);try{if(!a||!b||b==='master'||a===b||a==='master')return it;const loop=abxReach(b,a),add=[];
  for(const f of b.fx||[]){if(!MXSCT[f.type])continue;const cur=mxScOk(f)&&f.p.sc.src===a.id,dn=mxDevName(f);add.push({ic:'fol',col:'#ff9a3c',t:cur?dn+' already listens to '+a.name:dn+' on '+b.name+' listens to '+a.name,d:cur?'':'Sidechain: the '+dn+' reacts to '+a.name+' instead of its own sound.',dis:cur||loop,why:loop&&!cur?b.name+' already plays into '+a.name+', so this would make a loop.':'',act:()=>{mxScSet(f,a.id,'fx');try{renderFx()}catch(e){}}})}
  const tf=mxTailOf(b);add.push({ic:'duck',col:'#ff7a7a',t:tf&&tf.p.src===a.id?b.name+' already ducks under '+a.name+' for tails':'Duck under '+a.name+', tuned for tails',d:'A Ducker on '+b.name+' that dips each time '+a.name+' hits and comes back within one 16th note. Good for reverb and delay returns.',dis:loop||!!(tf&&tf.p.src===a.id),why:loop?b.name+' already plays into '+a.name+', so this would make a loop.':'',act:()=>mxDuckTails(b,a)});
  let j=-1;it.forEach((x,i)=>{if(x&&x!=='-'&&(x.ic==='duck'||x.ic==='win')&&j<0)j=i});if(j<0)it.push(...add);else it.splice(j+1,0,...add)}catch(e){console.error('AudioLab cable menu',e)}return it}}
Object.assign(MX_HOOKS,{
  /* lane I: the source shown in a device's title strip, or null */
  scBadge(t,f){const s=f&&trkById(mxKeySrcId(f));return s?{name:s.name,color:s.color||'#cfd3db',tap:f.type==='duck'?'fx':mxTapOf(f),id:s.id}:null},
  scSet:mxScSet,scCan:mxScCan,scPick:mxScPick,kick:mxKick,
  /* lane D and lane C: puts the tails Ducker on a return, keyed from the kick (or the given track), and returns it */
  duckTails:mxDuckTails,duckTailsOff:mxTailOff});
