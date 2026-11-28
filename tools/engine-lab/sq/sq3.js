/* ===== lane N (task SQ3): resample once (the user's AE1 pick Q11; docs/quality-build.md) =====
   A buffer whose rate is not the rate it plays at (the built-in sampler and drum sounds made at 44.1 kHz, bounces rendered at 44.1 kHz,
   the stem splitter's 44.1 kHz results, songs saved at another rate, every clip when the export rate differs from the engine's) is
   played by Chromium's AudioBufferSourceNode with linear interpolation: images at -20 dB for a 10 kHz tone (research doc, section 4).
   With Hi-Fi on for the song (S.sq==='clean'), each such buffer is converted ONCE to the rate it plays at, with a windowed-sinc
   resampler (Kaiser, 32 zero crossings, beta 10, cut-off at 0.96 of the lower Nyquist), in a worker, and cached per rate
   (WeakMap: the copy goes when the buffer goes). Hi-Fi off (every loaded song, the demos, the Fractals song) is today's linear path,
   untouched: the buffer setter passes the very same buffer.
   How it reaches the audio code without changing anyone's code: AudioBufferSourceNode's buffer setter is wrapped. In a Hi-Fi song it
   hands the node the converted copy for its context's rate if there is one. Live, a buffer without a copy plays as before and its copy
   is made in the worker for the next time. Offline renders that make files (renderMix, renderMixChunked, bounceRender, the stem
   splitter's neuTo44) first wait for the worker to convert every loaded buffer to their rate; a buffer made during the render (a
   drum sound made on demand) is converted on the spot by the same code, so a render never depends on timing. The worker and the main
   thread run the same function: the same bits.
   Nothing runs per frame: conversions start when a buffer is loaded or made (BUFS.set, SBUF.set), when the song turns Hi-Fi on, and
   before an offline render. */
const SQRS={v:1,Z:32,beta:10,cut:.96,MAXU:8192,cache:new WeakMap(),made:new WeakSet(),w:null,wbad:false,jobs:new Map(),seq:0,exp:0,off:false,desc:null,
 BK:new Map(),S:null,q:null,soon:new Set(),tm:0,n:{hit:0,sync:0,work:0,miss:0,pass:0,ms:0,smp:0}};
/* the core, plain arithmetic for NB to port bit for bit (docs/quality-build.md, "What NB must port"):
   output sample i sits at input position i*D/U (U/D = outSr/inSr reduced by their gcd); its phase ph = (i*D) mod U picks one of U
   filters of T = 2*W taps (W = ceil(Z/fc)); each filter is the Kaiser-windowed sinc at the exact offsets, normalised to a sum of 1;
   taps outside the buffer read 0; double sums in tap order, rounded to float once. */
function sqRsGcd(a,b){a=Math.abs(a);b=Math.abs(b);while(b){const t=a%b;a=b;b=t}return a}
function sqRsI0(x){let s=1,t=1;for(let k=1;k<64;k++){const q=x/(2*k);t*=q*q;s+=t;if(t<1e-21*s)break}return s}
function sqRsBank(a,b,Z,beta,cut,BK){const key=a+'>'+b+':'+Z+':'+beta+':'+cut;if(BK&&BK.has(key))return BK.get(key);
 const g=sqRsGcd(a,b),U=b/g,D=a/g,fc=Math.min(1,b/a)*cut,W=Math.ceil(Z/fc),T=2*W,h=new Float64Array(U*T),i0b=sqRsI0(beta);
 for(let ph=0;ph<U;ph++){const fr=ph/U,o=ph*T;let s=0;
  for(let t=0;t<T;t++){const d=fr+(W-1-t),u=fc*d;let v=0;if(Math.abs(u)<Z){const r=u/Z,sn=u===0?1:Math.sin(Math.PI*u)/(Math.PI*u);v=sn*sqRsI0(beta*Math.sqrt(1-r*r))/i0b}h[o+t]=v;s+=v}
  for(let t=0;t<T;t++)h[o+t]/=s}
 const B={U,D,W,T,h};if(BK)BK.set(key,B);return B}
function sqRsLen(n,a,b){const g=sqRsGcd(a,b),U=b/g,D=a/g;return Math.ceil(n*U/D)}
function sqRsRun(x,a,b,Z,beta,cut,BK){const B=sqRsBank(a,b,Z,beta,cut,BK),U=B.U,D=B.D,W=B.W,T=B.T,h=B.h,L=x.length,n=sqRsLen(L,a,b),y=new Float32Array(n);
 let k=0,ph=0;for(let i=0;i<n;i++){const j0=k-W+1,o=ph*T;let s=0;
  if(j0>=0&&j0+T<=L){for(let t=0;t<T;t++)s+=h[o+t]*x[j0+t]}else{for(let t=0;t<T;t++){const j=j0+t;if(j>=0&&j<L)s+=h[o+t]*x[j]}}
  y[i]=s;ph+=D;if(ph>=U){const q=Math.floor(ph/U);k+=q;ph-=q*U}}
 return y}
function sqRsOk(a,b){if(!(a>0&&b>0)||a===b||a%1||b%1)return false;const g=sqRsGcd(a,b);return b/g<=SQRS.MAXU&&a/g<=SQRS.MAXU*8}
function sqRsHas(b,sr){const m=SQRS.cache.get(b),v=m&&m.get(sr);return v&&typeof v==='object'&&v.sampleRate===sr?v:null}
function sqRsPut(b,sr,chs){const o=new AudioBuffer({numberOfChannels:chs.length,length:Math.max(1,chs[0].length),sampleRate:sr});chs.forEach((c,i)=>o.copyToChannel(c,i));
 SQRS.made.add(o);let m=SQRS.cache.get(b);if(!m){m=new Map();SQRS.cache.set(b,m)}m.set(sr,o);return o}
/* on the spot (offline renders that make files, or when the worker cannot start) */
function sqRsSync(b,sr){const h=sqRsHas(b,sr);if(h)return h;if(!sqRsOk(b.sampleRate,sr))return null;const t0=performance.now(),chs=[];
 for(let c=0;c<b.numberOfChannels;c++)chs.push(sqRsRun(b.getChannelData(c),b.sampleRate,sr,SQRS.Z,SQRS.beta,SQRS.cut,SQRS.BK));
 SQRS.n.sync++;SQRS.n.ms+=performance.now()-t0;SQRS.n.smp+=b.length*b.numberOfChannels;return sqRsPut(b,sr,chs)}
/* the worker: the same functions, as text */
function sqRsWorker(){if(SQRS.w||SQRS.wbad)return SQRS.w;try{
 const src='"use strict";'+[sqRsGcd,sqRsI0,sqRsBank,sqRsLen,sqRsRun].map(f=>f.toString()).join('\n')+
  '\nconst BK=new Map();onmessage=e=>{const d=e.data;try{const out=d.ch.map(x=>sqRsRun(x,d.a,d.b,d.Z,d.beta,d.cut,BK));postMessage({id:d.id,out},out.map(o=>o.buffer))}catch(err){postMessage({id:d.id,err:String(err)})}}';
 const w=new Worker(URL.createObjectURL(new Blob([src],{type:'text/javascript'})));
 w.onmessage=e=>{const d=e.data,J=SQRS.jobs.get(d.id);if(!J)return;SQRS.jobs.delete(d.id);if(d.err||!d.out){J.no(new Error(d.err||'resample'));return}
  SQRS.n.work++;SQRS.n.ms+=performance.now()-J.t0;SQRS.n.smp+=J.b.length*J.b.numberOfChannels;J.ok(sqRsHas(J.b,J.sr)||sqRsPut(J.b,J.sr,d.out))};
 w.onerror=e=>{SQRS.wbad=true;SQRS.w=null;for(const J of SQRS.jobs.values())J.no(new Error('worker'));SQRS.jobs.clear()};
 SQRS.w=w}catch(e){SQRS.wbad=true;SQRS.w=null}return SQRS.w}
/* the converted copy of b at sr, made once: a promise (the worker), the same promise for every caller */
function sqRsGet(b,sr){const h=sqRsHas(b,sr);if(h)return Promise.resolve(h);if(!b||!sqRsOk(b.sampleRate,sr))return Promise.resolve(null);
 let m=SQRS.cache.get(b);if(!m){m=new Map();SQRS.cache.set(b,m)}const v=m.get(sr);if(v&&typeof v.then==='function')return v;
 const p=new Promise((ok,no)=>{const w=sqRsWorker();if(!w){ok(sqRsSync(b,sr));return}const id=++SQRS.seq,ch=[];
  for(let c=0;c<b.numberOfChannels;c++)ch.push(b.getChannelData(c).slice());
  SQRS.jobs.set(id,{b,sr,ok,no,t0:performance.now()});w.postMessage({id,a:b.sampleRate,b:sr,Z:SQRS.Z,beta:SQRS.beta,cut:SQRS.cut,ch},ch.map(x=>x.buffer))})
  .catch(()=>sqRsSync(b,sr)).then(o=>{const mm=SQRS.cache.get(b);if(mm&&mm.get(sr)===p){if(o)mm.set(sr,o);else mm.delete(sr)}return o});
 m.set(sr,p);return p}
/* the buffers a song can play: clips (BUFS), built-in sounds (SBUF), warped copies (WARPBUF) */
function sqRsAll(){const out=new Set(),add=b=>{if(b&&typeof b==='object'&&typeof b.getChannelData==='function'&&!SQRS.made.has(b))out.add(b)};
 try{for(const v of BUFS.values())add(v&&v.buf)}catch(e){}try{for(const v of SBUF.values())add(v&&v.buf?v.buf:v)}catch(e){}try{for(const v of WARPBUF.values())add(v&&v.buf)}catch(e){}return[...out]}
function sqRsWarm(sr){if(!sr||sqProj()!=='clean')return Promise.resolve(0);const L=sqRsAll().filter(b=>b.sampleRate!==sr&&sqRsOk(b.sampleRate,sr)&&!sqRsHas(b,sr));
 return Promise.all(L.map(b=>sqRsGet(b,sr))).then(()=>L.length)}
/* live: a buffer that was just loaded or made gets its copy for the engine's rate soon (batched, off the main thread) */
function sqRsSoon(b){if(!b||sqProj()!=='clean'||typeof ctx!=='object'||!ctx||!ctx.sampleRate)return;if(typeof b.getChannelData!=='function'||SQRS.made.has(b)||b.sampleRate===ctx.sampleRate)return;
 SQRS.soon.add(b);if(SQRS.tm)return;SQRS.tm=setTimeout(()=>{SQRS.tm=0;const L=[...SQRS.soon];SQRS.soon.clear();if(sqProj()!=='clean'||!ctx)return;for(const x of L)sqRsGet(x,ctx.sampleRate).catch(()=>{})},50)}
/* the buffer setter: the only place where a source gets its buffer */
function sqRsPick(node,b){if(SQRS.off||!b||typeof b!=='object'||SQRS.made.has(b))return b;let c=null;try{c=node.context}catch(e){}const sr=c&&c.sampleRate;
 if(!sr||b.sampleRate===sr||sqProj()!=='clean'){SQRS.n.pass++;return b}
 const h=sqRsHas(b,sr);if(h){SQRS.n.hit++;return h}
 if(SQRS.exp>0&&typeof OfflineAudioContext!=='undefined'&&c instanceof OfflineAudioContext){const o=sqRsSync(b,sr);return o||b}
 SQRS.n.miss++;sqRsGet(b,sr).catch(()=>{});return b}
{const d=typeof AudioBufferSourceNode!=='undefined'&&Object.getOwnPropertyDescriptor(AudioBufferSourceNode.prototype,'buffer');
 if(d&&d.set&&d.get&&d.configurable){SQRS.desc=d;Object.defineProperty(AudioBufferSourceNode.prototype,'buffer',{configurable:true,enumerable:d.enumerable,get:d.get,set(b){d.set.call(this,sqRsPick(this,b))}})}}
SQ_HOOKS.resample=(b,sr)=>sqRsGet(b,sr);SQ_HOOKS.resampleNow=(b,sr)=>sqRsSync(b,sr);SQ_HOOKS.warm=sr=>sqRsWarm(sr);
/* offline renders that make files: wait for the copies at their rate first (Hi-Fi songs only; Hi-Fi off calls straight through) */
function sqRsWrap(fn,rate){return function(){const sr=rate(arguments);if(SQRS.off||sqProj()!=='clean')return fn.apply(this,arguments);const self=this,args=arguments;
 return sqRsWarm(sr).catch(()=>0).then(()=>{SQRS.exp++;let r;try{r=fn.apply(self,args)}catch(e){SQRS.exp--;throw e}return Promise.resolve(r).finally(()=>{SQRS.exp--})})}}
{renderMix=sqRsWrap(renderMix,a=>+a[0]||(ctx&&ctx.sampleRate)||0);renderMixChunked=sqRsWrap(renderMixChunked,a=>+a[0]||(ctx&&ctx.sampleRate)||0);
 bounceRender=sqRsWrap(bounceRender,()=>44100);neuTo44=sqRsWrap(neuTo44,()=>44100);
 for(const M of[BUFS,SBUF]){const _s=M.set;M.set=function(k,v){const r=_s.call(this,k,v);try{sqRsSoon(v&&v.buf?v.buf:v)}catch(e){}return r}}
 /* the song turned Hi-Fi on, or a Hi-Fi song was opened: copies for the engine's rate */
 const _sc=sqScan;sqScan=function(){const r=_sc.apply(this,arguments);try{const q=sqProj();if((q!==SQRS.q||S!==SQRS.S)){SQRS.q=q;SQRS.S=S;if(q==='clean'&&ctx&&ctx.sampleRate)setTimeout(()=>sqRsWarm(ctx.sampleRate).catch(()=>{}),0)}}catch(e){}return r};
 const RT=' With Hi-Fi on, sounds made at another sample rate (built-in sounds, bounces, stems, exports at another rate) are converted once with a cleaner method.';
 if(!SQROW.h.includes(RT))SQROW.h+=RT;const r=typeof STX==='object'&&STX.get&&STX.get('songHiFi');if(r&&!r.h.includes(RT))r.h+=RT}
/* the Hi-Fi row's stable settings id (lane H's registry, docs/settings-ids.md), named once: project.songHiFi */
setTimeout(()=>{try{if(typeof XT_SET_NS==='object'&&XT_SET_NS&&!XT_SET_NS.songHiFi)XT_SET_NS.songHiFi='project.songHiFi'}catch(e){}},0);
/* ===== end of lane N SQ3 ===== */
