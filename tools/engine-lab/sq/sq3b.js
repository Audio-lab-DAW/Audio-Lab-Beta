/* ===== lane N (task SQ3b, part a): the pitched read (the user's AE1 pick Q12; docs/quality-build.md) =====
   A sample played at another pitch is read by Chromium's AudioBufferSourceNode with linear interpolation (playbackRate): at +7 semitones
   a 10 kHz tone has images at -22 dB (research doc, section 4). With Hi-Fi on for the DEVICE (sqOf(inst)==='clean'), a note of the
   Sampler (Classic and One shot modes) or of a drum designer with Key tracking on gets, once per pitch, a copy of its sample already
   read at that pitch with a windowed sinc (Kaiser, 32 zero crossings, beta 10, the cut-off lowered to 0.96 of the new Nyquist when the
   pitch goes up, so nothing folds back), at the rate it plays at; the source then plays the copy at rate 1, with its start, length and
   loop points scaled the same way. One step: the copy also does SQ3's rate change (a 44.1 kHz sound in a 48 kHz engine).
   Hi-Fi off is today's path, untouched (the very same nodes and values).
   How, without changing anyone's code: sampPlay and pzPlay are wrapped; while a Hi-Fi note is being built, the context's
   createBufferSource hands out nodes whose buffer is held back until start(), where the pitch is known (a node takes one buffer only).
   Live, a pitch without its copy yet plays as before and its copy is made in a worker for the next time (and when the song starts, the
   notes of Hi-Fi Samplers are converted ahead); renders that make files (renderMix, renderMixChunked, bounceRender) convert a missing
   pitch on the spot with the same function (the same bits as the worker), so a file never depends on timing.
   Copies are cached per sample, rate and pitch (WeakMap on the sample; at most 160 MB in all, the oldest dropped first).
   Nothing runs per frame. The grain, emit and vgrain worklets come in part b. */
const SQP={v:1,Z:32,beta:10,cut:.96,L:2048,T:null,cache:new WeakMap(),orig:new WeakMap(),lru:new Map(),bytes:0,MAXB:160*1048576,MAXONE:24*1048576,
 w:null,wbad:false,jobs:new Map(),seq:0,exp:0,off:false,n:{hit:0,sync:0,work:0,miss:0,pass:0,big:0,ms:0,smp:0}};
/* the core, plain arithmetic for NB to port bit for bit (docs/quality-build.md):
   K(u) = sinc(u) * I0(beta*sqrt(1-(u/Z)^2)) / I0(beta) for |u| < Z, else 0, tabulated at L points per unit (index i is u = i/L).
   R = input samples per output sample (playbackRate * buffer rate / output rate); fc = min(1, 1/R) * cut; W = ceil(Z/fc).
   Output i sits at input position pos = i*R (a fresh product, never summed up), k = floor(pos), fr = pos - k; taps j = k+t, t = -W+1..W,
   at distance d = |t - fr| * fc * L in table units; weight w = T[a] + (T[a+1]-T[a]) * (d - a), a = floor(d) (0 when a >= Z*L);
   the sum of w*x[j] (x = 0 outside the buffer) divided by the sum of w, both in double in tap order, rounded to float once.
   Output length ceil(n / R). */
function sqPrTab(Z,beta,L){const n=Z*L+2,T=new Float64Array(n),i0b=sqRsI0(beta);
 for(let i=0;i<n;i++){const u=i/L;let v=0;if(u<Z){const r=u/Z,sn=u===0?1:Math.sin(Math.PI*u)/(Math.PI*u);v=sn*sqRsI0(beta*Math.sqrt(1-r*r))/i0b}T[i]=v}
 return T}
function sqPrLen(n,R){return Math.max(1,Math.ceil(n/R))}
function sqPrRun(x,R,Z,cut,L,T){const n=x.length,m=sqPrLen(n,R),y=new Float32Array(m),fc=Math.min(1,1/R)*cut,W=Math.ceil(Z/fc),fl=fc*L,E=Z*L;
 for(let i=0;i<m;i++){const pos=i*R,k=Math.floor(pos),fr=pos-k;let s=0,ws=0;
  for(let t=1-W;t<=W;t++){const d=Math.abs(t-fr)*fl,a=Math.floor(d);if(a>=E)continue;const ta=T[a],w=ta+(T[a+1]-ta)*(d-a),j=k+t;ws+=w;if(j>=0&&j<n)s+=w*x[j]}
  y[i]=ws>0?s/ws:0}
 return y}
function sqPrTabGet(){return SQP.T||(SQP.T=sqPrTab(SQP.Z,SQP.beta,SQP.L))}
function sqPrKey(sr,r){return sr+':'+r}
function sqPrRatio(b,sr,r){return r*b.sampleRate/sr}
function sqPrBytes(b,sr,r){return sqPrLen(b.length,sqPrRatio(b,sr,r))*b.numberOfChannels*4}
function sqPrOk(b,sr,r){if(!b||typeof b.getChannelData!=='function'||!(sr>0)||!(r>0)||!isFinite(r)||r===1)return false;const R=sqPrRatio(b,sr,r);return R>=1/16&&R<=64&&sqPrBytes(b,sr,r)<=SQP.MAXONE}
function sqPrHas(b,sr,r){const m=SQP.cache.get(b),v=m&&m.get(sqPrKey(sr,r));if(v&&typeof v==='object'&&typeof v.getChannelData==='function'){const e=SQP.lru.get(v);if(e){SQP.lru.delete(v);SQP.lru.set(v,e)}return v}return null}
function sqPrPut(b,sr,r,chs){const o=new AudioBuffer({numberOfChannels:chs.length,length:Math.max(1,chs[0].length),sampleRate:sr});chs.forEach((c,i)=>o.copyToChannel(c,i));
 try{SQRS.made.add(o)}catch(e){}let m=SQP.cache.get(b);if(!m){m=new Map();SQP.cache.set(b,m)}const k=sqPrKey(sr,r);m.set(k,o);
 const by=o.length*o.numberOfChannels*4;SQP.lru.set(o,{b,k,by});SQP.bytes+=by;
 while(SQP.bytes>SQP.MAXB&&SQP.lru.size>1){const[x,e]=SQP.lru.entries().next().value;SQP.lru.delete(x);SQP.bytes-=e.by;const mm=SQP.cache.get(e.b);if(mm&&mm.get(e.k)===x)mm.delete(e.k)}
 return o}
/* on the spot: renders that make files, or when no worker can start */
function sqPrSync(b,sr,r){const h=sqPrHas(b,sr,r);if(h)return h;if(!sqPrOk(b,sr,r))return null;const t0=performance.now(),R=sqPrRatio(b,sr,r),T=sqPrTabGet(),chs=[];
 for(let c=0;c<b.numberOfChannels;c++)chs.push(sqPrRun(b.getChannelData(c),R,SQP.Z,SQP.cut,SQP.L,T));
 SQP.n.sync++;SQP.n.ms+=performance.now()-t0;SQP.n.smp+=b.length*b.numberOfChannels;return sqPrPut(b,sr,r,chs)}
/* the worker: the same functions, as text */
function sqPrWorker(){if(SQP.w||SQP.wbad)return SQP.w;try{
 const src='"use strict";'+[sqRsI0,sqPrTab,sqPrLen,sqPrRun].map(f=>f.toString()).join('\n')+
  '\nconst TB=new Map();onmessage=e=>{const d=e.data;try{const k=d.Z+":"+d.beta+":"+d.L;let T=TB.get(k);if(!T){T=sqPrTab(d.Z,d.beta,d.L);TB.set(k,T)}const out=d.ch.map(x=>sqPrRun(x,d.R,d.Z,d.cut,d.L,T));postMessage({id:d.id,out},out.map(o=>o.buffer))}catch(err){postMessage({id:d.id,err:String(err)})}}';
 const w=new Worker(URL.createObjectURL(new Blob([src],{type:'text/javascript'})));
 w.onmessage=e=>{const d=e.data,J=SQP.jobs.get(d.id);if(!J)return;SQP.jobs.delete(d.id);if(d.err||!d.out){J.no(new Error(d.err||'pitch'));return}
  SQP.n.work++;SQP.n.ms+=performance.now()-J.t0;SQP.n.smp+=J.b.length*J.b.numberOfChannels;J.ok(sqPrHas(J.b,J.sr,J.r)||sqPrPut(J.b,J.sr,J.r,d.out))};
 w.onerror=()=>{SQP.wbad=true;SQP.w=null;for(const J of SQP.jobs.values())J.no(new Error('worker'));SQP.jobs.clear()};
 SQP.w=w}catch(e){SQP.wbad=true;SQP.w=null}return SQP.w}
/* the copy of sample b read at playbackRate r for output rate sr, made once: a promise, the same one for every caller */
function sqPrGet(b,sr,r){const h=sqPrHas(b,sr,r);if(h)return Promise.resolve(h);if(!sqPrOk(b,sr,r)){SQP.n.big++;return Promise.resolve(null)}
 let m=SQP.cache.get(b);if(!m){m=new Map();SQP.cache.set(b,m)}const k=sqPrKey(sr,r),v=m.get(k);if(v&&typeof v.then==='function')return v;
 const p=new Promise((ok,no)=>{const w=sqPrWorker();if(!w){ok(sqPrSync(b,sr,r));return}const id=++SQP.seq,ch=[];
  for(let c=0;c<b.numberOfChannels;c++)ch.push(b.getChannelData(c).slice());
  SQP.jobs.set(id,{b,sr,r,ok,no,t0:performance.now()});w.postMessage({id,R:sqPrRatio(b,sr,r),Z:SQP.Z,beta:SQP.beta,cut:SQP.cut,L:SQP.L,ch},ch.map(x=>x.buffer))})
  .catch(()=>sqPrSync(b,sr,r)).then(o=>{const mm=SQP.cache.get(b);if(mm&&mm.get(k)===p){if(o)mm.set(k,o);else mm.delete(k)}return o});
 m.set(k,p);return p}
/* the node: its buffer is held back until start(), where the pitch is known */
function sqPrNode(s){const d=SQRS.desc||Object.getOwnPropertyDescriptor(AudioBufferSourceNode.prototype,'buffer');let held=null;
 Object.defineProperty(s,'buffer',{configurable:true,enumerable:true,get(){return held},set(v){held=v}});
 s.start=function(){const a=Array.prototype.slice.call(arguments);let fb=held;try{fb=sqPrSwap(this,held,a)}catch(e){fb=held}
  delete this.buffer;delete this.start;if(fb)this.buffer=fb;return this.start.apply(this,a)}}
/* start(when, offset, duration): pick the copy for the node's pitch; offset, duration and the loop points are in seconds of the sample,
   so on the copy they are divided by the pitch ratio */
function sqPrSwap(s,b,a){if(SQP.off||!b)return b;const r=s.playbackRate.value;if(!(r>0)||s.detune.value!==0){SQP.n.pass++;return b}
 const c=s.context,sr=c&&c.sampleRate,b0=SQP.orig.get(b)||b,offl=typeof OfflineAudioContext!=='undefined'&&c instanceof OfflineAudioContext;
 /* the note at the sample's own pitch: only the rate change, SQ3's copy (one copy per rate, whatever the song's Hi-Fi) */
 if(r===1){if(b.sampleRate===sr||b0.sampleRate===sr||!sqRsOk(b0.sampleRate,sr)){SQP.n.pass++;return b}let o=sqRsHas(b0,sr);
  if(!o){if(offl&&SQP.exp>0)o=sqRsSync(b0,sr);else{SQP.n.miss++;sqRsGet(b0,sr).catch(()=>{});return b}}if(o)SQP.n.hit++;return o||b}
 let o=sqPrHas(b0,sr,r);
 if(!o){
  if(offl&&SQP.exp>0)o=sqPrSync(b0,sr,r);else{SQP.n.miss++;sqPrGet(b0,sr,r).catch(()=>{});return b}
  if(!o){SQP.n.big++;return b}}
 SQP.n.hit++;const ls=s.loopStart,le=s.loopEnd;s.playbackRate.value=1;
 if(a.length>1&&a[1]!==undefined)a[1]=(+a[1]||0)/r;if(a.length>2&&a[2]!==undefined)a[2]=+a[2]/r;
 if(ls)s.loopStart=ls/r;if(le)s.loopEnd=le/r;return o}
/* a Hi-Fi note: the sources made while it is built are held as above */
function sqPrCall(fn,self,args,c){if(SQP.off||!c||typeof c.createBufferSource!=='function')return fn.apply(self,args);
 const own=Object.prototype.hasOwnProperty.call(c,'createBufferSource'),prev=c.createBufferSource;
 c.createBufferSource=function(){const s=prev.apply(this,arguments);try{sqPrNode(s)}catch(e){}return s};
 try{return fn.apply(self,args)}finally{if(own)c.createBufferSource=prev;else delete c.createBufferSource}}
const sqPrSamp=I=>!!I&&I.preset==='sampler'&&I.mode!=='grain'&&sqOf(I)==='clean';
const sqPrPz=I=>{try{return!!I&&!!PZD[I.preset]&&!!I.kt&&sqOf(I)==='clean'}catch(e){return false}};
/* ahead of time (the song starts, a Hi-Fi song or device is set): the pitches of the notes of Hi-Fi Samplers and key-tracked drum designers */
function sqPrWarm(sr){if(SQP.off||!sr||typeof S!=='object'||!S)return Promise.resolve(0);const L=[];
 for(const t of S.tracks||[]){const I=t.inst;if(!I)continue;let B=null,tu=0;
  if(sqPrSamp(I)){try{B=sampleBuf(I.buf);if(B&&I.rev)B=sampRev(B)}catch(e){B=null}tu=+I.tune||0}
  else if(sqPrPz(I)){try{const ab=ctx&&PZAB.get(ctx);B=ab&&ab.get(pzKey(I))||null}catch(e){B=null}}
  if(!B)continue;const P=new Set();for(const c of t.clips||[])for(const n of c.notes||[])if(n&&isFinite(n.p))P.add(n.p);
  for(const p of P){const r=Math.fround(Math.pow(2,(p-60+tu)/12));if(r!==1&&sqPrOk(B,sr,r)&&!sqPrHas(B,sr,r))L.push([B,r])}}
 return Promise.all(L.slice(0,64).map(([B,r])=>sqPrGet(B,sr,r).catch(()=>null))).then(()=>Math.min(64,L.length))}
{const _sp=sampPlay;sampPlay=function(c,I){return sqPrSamp(I)?sqPrCall(_sp,this,arguments,c):_sp.apply(this,arguments)};
 const _pz=pzPlay;pzPlay=function(c,I){return sqPrPz(I)?sqPrCall(_pz,this,arguments,c):_pz.apply(this,arguments)};
 /* the copies keep a link to the sample they came from (SQ3's copies too), so a pitch is read from the original in one step */
 const _put=sqRsPut;sqRsPut=function(b){const o=_put.apply(this,arguments);try{SQP.orig.set(o,b)}catch(e){}return o};
 const xw=fn=>function(){SQP.exp++;let r;try{r=fn.apply(this,arguments)}catch(e){SQP.exp--;throw e}return Promise.resolve(r).finally(()=>{SQP.exp--})};
 renderMix=xw(renderMix);renderMixChunked=xw(renderMixChunked);bounceRender=xw(bounceRender);
 const _ws=warmSounds;warmSounds=function(){const r=_ws.apply(this,arguments);try{if(ctx&&ctx.sampleRate)setTimeout(()=>sqPrWarm(ctx.sampleRate).catch(()=>{}),0)}catch(e){}return r};
 const T1='the notes it plays away from the sample\'s own pitch are read with a cleaner method, so high notes keep their top end without harsh extra tones (Classic and One shot modes).',
  T2='with Key tracking on, notes away from the root are pitched with a cleaner method, without harsh extra tones.';
 SQ.DEV['inst:sampler']=T1;SQ.DEV['inst:ztom']=T2}
SQ_HOOKS.pitched=(b,sr,r)=>sqPrGet(b,sr,r);SQ_HOOKS.pitchedNow=(b,sr,r)=>sqPrSync(b,sr,r);SQ_HOOKS.warmPitched=sr=>sqPrWarm(sr);
/* ===== end of lane N SQ3b ===== */
