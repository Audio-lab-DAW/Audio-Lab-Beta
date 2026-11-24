const fs=require('fs');
(async()=>{const m=await WebAssembly.instantiate(fs.readFileSync('k.wasm'),{env:{abort(){}}});const X=m.instance.exports;X.init(48000);
const NV=8,NO=7,ph=new Float64Array(NV*NO),df=new Float64Array(NV*NO),gl=new Float32Array(NV*NO),gr=new Float32Array(NV*NO),z=new Float64Array(NV*4),L=new Float32Array(2048),R=new Float32Array(2048);
for(let v=0;v<NV;v++)for(let o=0;o<NO;o++){const i=v*NO+o;ph[i]=.5;df[i]=110*Math.pow(2,v*3/12)*Math.pow(2,(o/6*2-1)*28/1200)/48000;gl[i]=.26*(.3+o/10);gr[i]=.26*(1-o/10)}
function run(n,b0,b1,a1,a2,e){for(let i=0;i<n;i++){L[i]=0;R[i]=0}
 for(let v=0;v<NV;v++){let z1l=z[v*4],z2l=z[v*4+1],z1r=z[v*4+2],z2r=z[v*4+3];
  for(let i=0;i<n;i++){let xl=0,xr=0;for(let o=0;o<NO;o++){const k=v*NO+o;let t=ph[k];const d=df[k];let s=2*t-1;if(t<d){const x=t/d;s-=2*x-x*x-1}else if(t>1-d){const x=(t-1)/d;s-=x*x+2*x+1}t+=d;if(t>=1)t-=1;ph[k]=t;xl+=s*gl[k];xr+=s*gr[k]}
   const yl=b0*xl+z1l;z1l=b1*xl-a1*yl+z2l;z2l=b0*xl-a2*yl;const yr=b0*xr+z1r;z1r=b1*xr-a1*yr+z2r;z2r=b0*xr-a2*yr;L[i]+=yl*e;R[i]+=yr*e}
  z[v*4]=z1l;z[v*4+1]=z2l;z[v*4+2]=z1r;z[v*4+3]=z2r}}
const w=6.283*2000/48000,cs=Math.cos(w),al=Math.sin(w)/2,ia=1/(1+al),b1=(1-cs)*ia,b0=b1/2,a1=-2*cs*ia,a2=(1-al)*ia;
const N=128,BL=375*20;/* 20 s of audio */
for(let r=0;r<3;r++){let t=process.hrtime.bigint();for(let b=0;b<BL;b++)run(N,b0,b1,a1,a2,.5);const js=Number(process.hrtime.bigint()-t)/1e6;
 t=process.hrtime.bigint();for(let b=0;b<BL;b++)X.run(N,b0,b1,a1,a2,.5);const wa=Number(process.hrtime.bigint()-t)/1e6;
 console.log('20 s of 8 voices x 7 saws: JS',js.toFixed(0),'ms, WASM',wa.toFixed(0),'ms, ratio',(js/wa).toFixed(2))}
const wl=new Float32Array(X.memory.buffer,X.lptr(),8);console.log('sample check',L[5].toFixed(5),wl[5].toFixed(5))})()
