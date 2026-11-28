/* ==SNDR-js== v0.000 task SND-R (lane L): one random stream per device (the user's D2, docs/review-native.md A2).
   Before: the worklet module had ONE generator (Math.random replaced by sfc32 with fixed constants) shared by every processor, so the
   numbers a device got depended on how many every other device drew before it in the browser's render order (and on the block size).
   Now: every processor instance gets its own sfc32 stream, seeded from the project's export seed and the device's key; when its
   constructor, its process() or its port message handler starts, Math.random is set to that stream (only when it is not already;
   nothing is restored after, so a song with one random device writes nothing per block).
   The key is processorOptions.sndKey when the code that makes the node gives one (hook for any lane: a device id), otherwise
   '<processor name>#<n>', n = how many nodes of that processor this audio context made before (an offline render builds the graph
   in project order: tracks top to bottom, devices left to right, then the master, so n is the device's place in the song).
   Seed: the 4 words of seedRng's hash of 'sndr|<S.seed>|<key>' (Fixed seed off in Export: 4 random words). The worklet runs
   sfc32 on them and drops 15 numbers, exactly as seedRng does, so stream k of a device = seedRng('sndr|'+S.seed+'|'+key).
   Plain integer arithmetic (Math.imul, shifts, xor, |0), the same in the native engine (task NB: native/ sfc32 of al_crush.h).
   Own implementation; sfc32 is Chris Doty-Humphrey's public-domain PractRand generator, as the page's sfc32 already says. */
function sndRHash(str){let h1=1779033703,h2=3144134277,h3=1013904242,h4=2773480762;for(let i=0;i<str.length;i++){const k=str.charCodeAt(i);h1=h2^Math.imul(h1^k,597399067);h2=h3^Math.imul(h2^k,2869860233);h3=h4^Math.imul(h3^k,951274213);h4=h1^Math.imul(h4^k,2716044179)}
  h1=Math.imul(h3^(h1>>>18),597399067);h2=Math.imul(h4^(h2>>>22),2869860233);h3=Math.imul(h1^(h3>>>17),951274213);h4=Math.imul(h2^(h4>>>19),2716044179);
  return[(h1^h2^h3^h4)>>>0,(h2^h1)>>>0,(h3^h1)>>>0,(h4^h1)>>>0]}
/* the seed of one new node (main thread); c = its audio context, name = its processor, o = its options (already copied) */
function sndRSeed(c,name,o){const po=o&&o.processorOptions;let key=po&&po.sndKey!=null?String(po.sndKey):null;
  if(key==null){const N=c.__sndRN||(c.__sndRN=Object.create(null)),k=N[name]|0;N[name]=k+1;key=name+'#'+k}
  if(typeof UI!=='undefined'&&UI&&UI.exSeed===false)return[0,0,0,0].map(()=>(Math.random()*4294967296)>>>0);
  const s=typeof S!=='undefined'&&S&&S.seed!=null?S.seed:0;return sndRHash('sndr|'+s+'|'+key)}
/* worklet side: runs once at the top of the worklet module, before any processor is registered (never called on the main thread) */
function sndRWL(){const G=globalThis,R0=Math.random,rp=G.registerProcessor;if(typeof rp!=='function'||rp.__sndR)return;
  const mk=w=>{let a=w[0]|0,b=w[1]|0,c=w[2]|0,d=w[3]|0;const r=()=>{let t=(a+b)|0;a=b^(b>>>9);b=(c+(c<<3))|0;c=(c<<21)|(c>>>11);d=(d+1)|0;t=(t+d)|0;c=(c+t)|0;return(t>>>0)/4294967296};for(let i=0;i<15;i++)r();return r};
  const reg=function(name,C){if(typeof C!=='function'||!C.prototype||typeof C.prototype.process!=='function')return rp(name,C);
    const pr=C.prototype.process;
    class W extends C{constructor(o){const w=o&&o.processorOptions&&o.processorOptions.sndSeed,r=w&&w.length===4?mk(w):R0;Math.random=r;super(o);
      this.__sndR=r;const P=this.port,h=P&&P.onmessage;if(h)P.onmessage=function(e){if(Math.random!==r)Math.random=r;return h.call(this,e)}}}
    W.prototype.process=function(i,o,p){const r=this.__sndR;if(Math.random!==r)Math.random=r;return pr.call(this,i,o,p)};
    return rp(name,W)};
  reg.__sndR=1;G.registerProcessor=reg}
const SNDR_WL='('+sndRWL.toString()+')();\n';
/* main thread: every AudioWorkletNode made from now on carries its seed (processorOptions.sndSeed); nothing else of its options changes */
function sndRInstall(){const A=typeof window!=='undefined'&&window.AudioWorkletNode;if(!A||A.__sndR)return;
  class W extends A{constructor(c,n,o){const q=Object.assign({},o||{});q.processorOptions=Object.assign({},q.processorOptions||{});let s=null;try{s=sndRSeed(c,n,q)}catch(e){}if(s)q.processorOptions.sndSeed=s;super(c,n,q)}}
  W.__sndR=1;window.AudioWorkletNode=W}
sndRInstall();
SND_HOOKS.rseed=sndRSeed;/* any lane: pass processorOptions.sndKey (a device id) to give a node a key that does not depend on the order nodes are made */
/* ==SNDR-js-end== */
