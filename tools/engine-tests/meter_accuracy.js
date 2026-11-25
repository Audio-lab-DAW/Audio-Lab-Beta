/* Accuracy of the loudness meter worklet ('al-meter', class Met in WLSRC) against ITU-R BS.1770 and EBU Tech 3341 / 3342.
   Runs the worklet code itself in Node (no browser): the worklet bundle is taken from index.html, the processor is fed
   the test signals block by block and its messages are read back.
     node tools/engine-tests/meter_accuracy.js [index.html]            */
const fs=require('fs'),path=require('path');
const html=fs.readFileSync(process.argv[2]||path.join(__dirname,'..','..','index.html'),'utf8');
const line=html.split('\n').find(l=>l.startsWith('const WLSRC="'));
const WLSRC=eval('('+line.slice('const WLSRC='.length).replace(/;\s*$/,'')+')');
function load(fsr){const P={};const ctx={sampleRate:fsr,currentTime:0,currentFrame:0,registerProcessor:(n,c)=>{P[n]=c},
  AudioWorkletProcessor:class{constructor(){this.port={postMessage:m=>{(this._msgs||(this._msgs=[])).push(m)},onmessage:null}}},console,Math,Float32Array,Float64Array,Int32Array,Uint8Array,Uint32Array,Int16Array,Array,Object,Date,WebAssembly:undefined,performance:{now:()=>0}};
  const fn=new Function(...Object.keys(ctx),WLSRC);fn(...Object.values(ctx));return P}
function meter(fsr){const P=load(fsr);const m=new P['al-meter']({processorOptions:{p:{}}});m._msgs=[];return m}
function run(m,L,R,bs=128){const n=L.length,oL=new Float32Array(bs),oR=new Float32Array(bs);for(let o=0;o+bs<=n;o+=bs){m.process([[L.subarray(o,o+bs),R.subarray(o,o+bs)]],[[oL,oR]])}return m._msgs}
const db2a=d=>Math.pow(10,d/20);
function tone(fsr,segs,f=1000,ch='both'){/* segs: [[seconds, dBFS peak or null for silence]] */let n=0;for(const[s] of segs)n+=Math.round(s*fsr);const L=new Float32Array(n),R=new Float32Array(n);let i=0;
  for(const[s,d] of segs){const k=Math.round(s*fsr),a=d==null?0:db2a(d);for(let j=0;j<k;j++,i++){const v=a*Math.sin(2*Math.PI*f*i/fsr);if(ch!=='R')L[i]=v;if(ch!=='L')R[i]=v}}return[L,R]}
const out=[];const ok=(name,got,want,tol,tolLo)=>{const lo=tolLo==null?tol:tolLo,pass=got>=want-lo&&got<=want+tol;out.push({name,got:+got.toFixed(3),want,tol:tolLo==null?'±'+tol:'+'+tol+'/-'+lo,pass});return pass};
const last=(ms,k)=>{for(let i=ms.length-1;i>=0;i--)if(ms[i][k]!==undefined)return ms[i][k]};
const maxOf=(ms,k,from=0)=>{let v=-1e9;for(const q of ms.slice(from))if(q[k]!==undefined&&q[k]>v)v=q[k];return v};
const FS=48000;
/* calibration */
for(const[nm,f,d,ch,w] of [['997 Hz sine -18 dBFS, both channels: integrated',997,-18,'both',-18],['997 Hz sine -18 dBFS, left only: integrated',997,-18,'L',-21.01],['997 Hz sine 0 dBFS, left only: integrated',997,0,'L',-3.01]]){const m=meter(FS);const[L,R]=tone(FS,[[10,d]],f,ch);const ms=run(m,L,R);ok(nm,last(ms,'I'),w,.05);ok(nm.replace('integrated','short-term'),last(ms,'S'),w,.05);ok(nm.replace('integrated','momentary'),last(ms,'M'),w,.05)}
for(const sr of [44100,48000,96000]){const m=meter(sr);const[L,R]=tone(sr,[[10,-23]]);const ms=run(m,L,R);ok('Tech 3341 #1 at '+sr+' Hz: I',last(ms,'I'),-23,.1)}
{const m=meter(FS);const[L,R]=tone(FS,[[20,-33]]);const ms=run(m,L,R);ok('Tech 3341 #2: M',last(ms,'M'),-33,.1);ok('Tech 3341 #2: S',last(ms,'S'),-33,.1);ok('Tech 3341 #2: I',last(ms,'I'),-33,.1)}
{const m=meter(FS);const[L,R]=tone(FS,[[20,-23]]);const ms=run(m,L,R);ok('Tech 3341 #1: M',last(ms,'M'),-23,.1);ok('Tech 3341 #1: S',last(ms,'S'),-23,.1)}
{const m=meter(FS);const[L,R]=tone(FS,[[10,-36],[60,-23],[10,-36]]);ok('Tech 3341 #3: I',last(run(m,L,R),'I'),-23,.1)}
{const m=meter(FS);const[L,R]=tone(FS,[[10,-72],[10,-36],[60,-23],[10,-36],[10,-72]]);ok('Tech 3341 #4: I',last(run(m,L,R),'I'),-23,.1)}
{const m=meter(FS);const[L,R]=tone(FS,[[20,-26],[20.1,-20],[20,-26]]);ok('Tech 3341 #5: I',last(run(m,L,R),'I'),-23,.1)}
{const segs=[];for(let i=0;i<5;i++)segs.push([1.34,-20],[1.66,-30]);const m=meter(FS);const[L,R]=tone(FS,segs);const ms=run(m,L,R);const S=ms.slice(32).map(q=>q.S);ok('Tech 3341 #9: S lowest after 3 s',Math.min(...S),-23,.1);ok('Tech 3341 #9: S highest after 3 s',Math.max(...S),-23,.1)}
{const segs=[];for(let i=0;i<25;i++)segs.push([.18,-20],[.22,-30]);const m=meter(FS);const[L,R]=tone(FS,segs);const ms=run(m,L,R);const M=ms.slice(11).map(q=>q.M);ok('Tech 3341 #12: M lowest after 1 s',Math.min(...M),-23,.1);ok('Tech 3341 #12: M highest after 1 s',Math.max(...M),-23,.1)}
/* LRA (Tech 3342) */
for(const[nm,segs,w] of [['Tech 3342 #1',[[20,-20],[20,-30]],10],['Tech 3342 #2',[[20,-20],[20,-15]],5],['Tech 3342 #3',[[20,-40],[20,-20]],20],['Tech 3342 #4',[[20,-50],[20,-35],[20,-20],[20,-35],[20,-50]],15]]){const m=meter(FS);const[L,R]=tone(FS,segs.concat([[1.5,null]]));ok(nm+': LRA',last(run(m,L,R),'LRA'),w,1)}
/* true peak (Tech 3341 #15 to #19, 48 kHz) */
function tpSig(fsr,fr,amp,ph,sec=1){const n=Math.round(sec*fsr),L=new Float32Array(n),fd=Math.round(.01*fsr);for(let i=0;i<n;i++){const e=Math.min(1,i/fd,(n-1-i)/fd);L[i]=amp*e*Math.sin(2*Math.PI*fr*i/fsr+ph*Math.PI/180)}return[L,L.slice()]}
for(const[nm,fr,a,ph,w] of [['#15 fs/4 0.5 FS 0°',FS/4,.5,0,-6],['#16 fs/4 0.5 FS 45°',FS/4,.5,45,-6],['#17 fs/6 0.5 FS 60°',FS/6,.5,60,-6],['#18 fs/8 0.5 FS 67.5°',FS/8,.5,67.5,-6],['#19 fs/4 1.41 FS 45°',FS/4,1.41,45,3]]){const m=meter(FS);const[L,R]=tpSig(FS,fr,a,ph);ok('Tech 3341 '+nm+': true peak',last(run(m,L,R),'tpL'),w,.2,.4)}
/* #20 to #23: fs/6 at 0.5 plus one period of fs/4 at 1.0, made at 4 fs, low-passed, taken at offsets 0..3 */
{const F4=FS*4,n=F4,x=new Float64Array(n);let ph=0;const p0=Math.round(n/2);for(let i=0;i<n;i++){const inP=i>=p0&&i<p0+16;const fr=inP?FS/4:FS/6,a=inP?1:.5;ph+=2*Math.PI*fr/F4;x[i]=a*Math.sin(ph)}
 const T=255,hh=new Float64Array(T);for(let k=0;k<T;k++){const t=k-(T-1)/2,wv=.42-.5*Math.cos(2*Math.PI*k/(T-1))+.08*Math.cos(4*Math.PI*k/(T-1));hh[k]=(t===0?1:Math.sin(Math.PI*t*.95/4)/(Math.PI*t*.95/4))*wv}let sh=0;for(const v of hh)sh+=v;
 let gt=0;for(let c=T;c<n-T;c++){let s=0;for(let k=0;k<T;k++)s+=x[c-k+(T-1)/2]*hh[k];gt=Math.max(gt,Math.abs(s/sh))}out.push({name:'#20 to #23 as made here: true peak of the 4x signal',got:+(20*Math.log10(gt)).toFixed(3),want:'(reference)',tol:'',pass:true});
 for(let off=0;off<4;off++){const m=FS,L=new Float32Array(m);for(let j=0;j<m;j++){const c=j*4+off;let s=0;for(let k=0;k<T;k++){const q=c-k+(T-1)/2;if(q>=0&&q<n)s+=x[q]*hh[k]}L[j]=s/sh}const mm=meter(FS);ok('Tech 3341 #'+(20+off)+' (offset '+off+'): true peak',last(run(mm,L,L.slice()),'tpL'),+(20*Math.log10(gt)).toFixed(2),.2,.4)}}
/* correlation */
{const m=meter(FS);const[L,R]=tone(FS,[[2,-12]],440);ok('correlation, identical channels',last(run(m,L,R),'corr'),1,.01)}
{const m=meter(FS);const[L,R]=tone(FS,[[2,-12]],440);for(let i=0;i<R.length;i++)R[i]=-R[i];ok('correlation, inverted right channel',last(run(m,L,R),'corr'),-1,.01)}
{const m=meter(FS);const[L]=tone(FS,[[2,-12]],440);const R=new Float32Array(L.length);for(let i=0;i<R.length;i++)R[i]=Math.cos(2*Math.PI*440*i/FS)*db2a(-12);ok('correlation, 90° apart',last(run(m,L,R),'corr'),0,.02)}
/* pass-through: the meter's own output must equal its input */
{const m=meter(FS);const L=new Float32Array(FS),R=new Float32Array(FS);for(let i=0;i<FS;i++){L[i]=Math.sin(i*.01)*.9+(Math.random()-.5)*.1;R[i]=Math.cos(i*.013)*.7}const bs=128,oL=new Float32Array(bs),oR=new Float32Array(bs);let same=true;for(let o=0;o+bs<=FS;o+=bs){m.process([[L.subarray(o,o+bs),R.subarray(o,o+bs)]],[[oL,oR]]);for(let i=0;i<bs;i++)if(oL[i]!==L[o+i]||oR[i]!==R[o+i])same=false}ok('worklet output equals input (bit for bit)',same?1:0,1,0)}
/* cost: time to process 60 s of stereo audio (noise, and a loud limited mix-like signal), each measured after a warm-up run */
{const n=FS*60,N1=new Float32Array(n),N2=new Float32Array(n),M1=new Float32Array(n),M2=new Float32Array(n);for(let i=0;i<n;i++){N1[i]=Math.random()-.5;N2[i]=Math.random()-.5;const k=Math.tanh(3*(Math.sin(2*Math.PI*50*i/FS)*Math.exp(-((i%20690)/4000))+.3*(Math.random()-.5)));M1[i]=k*.9;M2[i]=k*.88}
 for(const[nm,L,R] of [['noise',N1,N2],['loud mix-like signal',M1,M2]])for(const ext of [0,1]){const m=meter(FS);if(ext)m.cmd('ext',{});run(m,L,R);run(m,L,R);const t=process.hrtime.bigint();run(m,L,R);const ms=Number(process.hrtime.bigint()-t)/1e6;out.push({name:'cost, 60 s of '+nm+(ext?', extended readings on':''),got:+ms.toFixed(1),want:'ms ('+(ms/600).toFixed(2)+'% of one core)',tol:'',pass:true})}}
let bad=0;for(const r of out){if(!r.pass)bad++;console.log((r.pass?'PASS ':'FAIL ')+r.name.padEnd(58)+String(r.got).padStart(9)+'  want '+r.want+' '+r.tol)}console.log(bad?bad+' failed':'all passed');
