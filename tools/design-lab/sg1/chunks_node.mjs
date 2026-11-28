// the app's worker loop (index.html NEUW) run in Node with the same onnxruntime-web 1.20.1 WASM engine: chunk timings + stems
import * as ort from 'onnxruntime-web';
import fs from 'fs';
const th=+process.argv[2]||2, kind=process.argv[3]||'n4', lim=+process.argv[4]||99;
const file=kind==='n6'?'../model/htdemucs_6s.onnx':'../model/htdemucs_fp16weights.onnx';
ort.env.wasm.numThreads=th;
const T0=performance.now();let t0=T0;
const sess=await ort.InferenceSession.create(new Uint8Array(fs.readFileSync(file)),{executionProviders:['wasm'],graphOptimizationLevel:'disabled'});
const init=performance.now()-t0;
const raw=fs.readFileSync('../out/mix.f32');const mix=new Float32Array(raw.buffer,raw.byteOffset,raw.length/4);const total=mix.length/2;const L=mix.subarray(0,total),R=mix.subarray(total);
const N=343980,OV=Math.floor(N/4),ST=N-OV,nc=Math.max(1,Math.ceil(total/ST));
let ns=0,out=null;const wt=new Float32Array(total),win=new Float32Array(N).fill(1);for(let i=0;i<OV;i++){win[i]=i/OV;win[N-1-i]=i/OV}
const cb=new Float32Array(2*N),ev=[];
for(let i=0;i<Math.min(nc,lim);i++){const s0=i*ST,e0=Math.min(s0+N,total),cl=e0-s0;if(cl<=0)break;cb.fill(0);cb.set(L.subarray(s0,e0),0);cb.set(R.subarray(s0,e0),N);
 t0=performance.now();const r=await sess.run({mix:new ort.Tensor('float32',cb,[1,2,N])}),st=r.stems.data;const run=performance.now()-t0;
 ns=r.stems.dims[1];if(!out)out=Array.from({length:ns},()=>[new Float32Array(total),new Float32Array(total)]);
 const t1=performance.now();
 for(let k=0;k<ns;k++){const O=out[k],ro=k*2*N;for(let c=0;c<2;c++){const D=O[c],off=ro+c*N;for(let s=0;s<cl;s++)D[s0+s]+=st[off+s]*win[s]}}
 for(let s=0;s<cl;s++)wt[s0+s]+=win[s];
 ev.push({i,s0,e0,run,add:performance.now()-t1,at:performance.now()-T0});console.log(kind,th,'chunk',i,Math.round(run),'ms')}
const res={kind,th,init,nc,N,OV,ST,total,ev,rss:process.memoryUsage().rss};
fs.writeFileSync(`../out/full_${kind}_${th}.json`,JSON.stringify(res));
if(lim>=nc){const buf=Buffer.alloc(ns*2*total*4);const f=new Float32Array(buf.buffer,buf.byteOffset,ns*2*total);
 for(let k=0;k<ns;k++)for(let c=0;c<2;c++){const D=out[k][c];for(let s=0;s<total;s++)f[(k*2+c)*total+s]=D[s]/Math.max(wt[s],1e-8)}
 fs.writeFileSync(`../out/stems_${kind}.f32`,buf);console.log('saved',ns)}
