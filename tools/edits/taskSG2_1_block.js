/* ===================== stem split lanes, step 1 (v0.000, task SG2-1, lane R; docs/stem-split-progress.md) =====================
   The loading bar of a stem split is the spectrogram of every stem, filled at the true song position as the splitter gets there.
   sgColsOf makes the columns: one 4096-point FFT per column (one column per lane pixel), folded into 96 log-frequency rows from
   32 Hz to 16 kHz, Uint8 dB (-84 dB = 0, 0 dB = 255; a full-scale sine reads 0 dB), row 0 at the top (16 kHz). It is self-contained:
   the workers (NEUW and the quick split's SGW) carry a copy of its source.
   Messages {t:'cols', i, n, s0, s1, pe, fin:[c0,c1], prov:[c1,c2], rows:96, ns, cw, cols}: after chunk (or block) i of n, samples
   s0..s1 are final; columns c0..c1 are final, c1..c2 are the draft stretch (P1: still to be cross-faded with the next chunk);
   cols holds them for each kept stem: stem j at j*96*(c2-c0), row r, column c at r*(c2-c0)+(c-c0).
   stemSplit(buf,prog,P,onCols) and neuSeparate(buf,kind,keep,prog,onCols): onCols(msg) gets every such message; onCols.cw sets
   the number of columns over the whole clip (default 512). SG_HOOKS.onChunk(job,msg) lets other code listen to every job's chunks.
   The quick split now runs in a worker (SGW): its blocks were main-thread pauses of about 0.45 s each. */
function sgColsOf(get,total,sr,cw,c0,c1,out,o,stride){const N=4096,R=96;let T=sgColsOf.T;
  if(!T||T.sr!==sr){const cs=new Float32Array(N/2),sn=new Float32Array(N/2),rv=new Uint16Array(N),w=new Float32Array(N),lo=new Int32Array(R),hi=new Int32Array(R),bw=sr/N;
    for(let i=0;i<N/2;i++){cs[i]=Math.cos(2*Math.PI*i/N);sn[i]=-Math.sin(2*Math.PI*i/N)}
    for(let i=0;i<N;i++){let x=i,y=0;for(let b=0;b<12;b++){y=(y<<1)|(x&1);x>>=1}rv[i]=y;w[i]=.5-.5*Math.cos(2*Math.PI*i/N)}
    for(let r=0;r<R;r++){const a=Math.round(32*Math.pow(500,r/R)/bw),b=Math.round(32*Math.pow(500,(r+1)/R)/bw);lo[r]=Math.min(N/2,a);hi[r]=Math.min(N/2+1,Math.max(a+1,b))}
    T=sgColsOf.T={sr,cs,sn,rv,w,lo,hi,re:new Float32Array(N),im:new Float32Array(N),mg:new Float32Array(N/2+1)}}
  const cs=T.cs,sn=T.sn,rv=T.rv,w=T.w,lo=T.lo,hi=T.hi,re=T.re,im=T.im,mg=T.mg;
  for(let c=c0;c<c1;c++){const p0=Math.floor((c+.5)*total/cw)-N/2;
    for(let i=0;i<N;i++){const q=p0+i;re[i]=q>=0&&q<total?get(q)*w[i]:0;im[i]=0}
    for(let i=0;i<N;i++){const j=rv[i];if(i<j){const t=re[i];re[i]=re[j];re[j]=t}}
    for(let sz=2;sz<=N;sz<<=1){const h=sz>>1,st=N/sz;for(let i=0;i<N;i+=sz)for(let j=0,k=0;j<h;j++,k+=st){const wr=cs[k],wi=sn[k],a=i+j,b=a+h,tr=re[b]*wr-im[b]*wi,ti=re[b]*wi+im[b]*wr;re[b]=re[a]-tr;im[b]=im[a]-ti;re[a]+=tr;im[a]+=ti}}
    for(let k=0;k<=N/2;k++)mg[k]=Math.hypot(re[k],im[k])*4/N;
    for(let r=0;r<R;r++){let m=0;for(let k=lo[r];k<hi[r];k++)if(mg[k]>m)m=mg[k];const v=Math.round((20*Math.log10(m+1e-12)+84)/84*255);out[o+(R-1-r)*stride+(c-c0)]=v<0?0:v>255?255:v}}}
/* which columns a finished stretch makes final: a column is final when its whole FFT window is inside the final samples */
function sgColEnds(total,cw,fc,fe,pe){const mid=c=>Math.floor((c+.5)*total/cw);let c1=fc;while(c1<cw&&(fe>=total||mid(c1)+2048<=fe))c1++;let c2=c1;while(c2<cw&&mid(c2)<pe)c2++;return[c1,c2]}
/* the quick split's worker: the mix's own columns (drawn before any model is there) and the quick split itself, block by block */
const SG2={seq:0,wh:new Map(),wk:null,neuRej:null,jobs:new Set()};
function sgWSrc(){return `'use strict';const STFT=${JSON.stringify(STFT)};const STF={cos:null,sin:null,rev:null,win:null,${STF.init.toString()},${STF.fft.toString()}};
${sgColsOf.toString()}
${sgColEnds.toString()}
${sgQuickCore.toString()}
onmessage=e=>{const d=e.data;try{
 if(d.t==='mix'){const L=d.L,R=d.R,n=L.length,out=new Uint8Array(96*d.cw);sgColsOf(q=>(L[q]+R[q])*.5,n,d.sr,d.cw,0,d.cw,out,0,d.cw);postMessage({t:'mix',id:d.id,cols:out},[out.buffer]);return}
 if(d.t==='quick'){const len=d.L.length,cw=d.cw|0,ks=d.ks||[0,1,2,3],nb=Math.ceil(len/(1<<18));let fc=0,fe0=0,i=0;
  const out=sgQuickCore(d.L,d.R,d.sr,d.P,(s0,s1,O)=>{if(cw){const e=sgColEnds(len,cw,fc,s1,s1),n=e[1]-fc,cols=new Uint8Array(ks.length*96*n);
     ks.forEach((k,j)=>{const A=O[k][0],B=O[k][1];sgColsOf(q=>(A[q]+B[q])*.5,len,d.sr,cw,fc,e[1],cols,j*96*n,n)});
     postMessage({t:'cols',id:d.id,i,n:nb,s0:fe0,s1,pe:s1,fin:[fc,e[0]],prov:[e[0],e[1]],rows:96,ns:ks.length,cw,cols},[cols.buffer]);fc=e[0];fe0=s1}
    i++;postMessage({t:'p',id:d.id,p:s1/len})});
  const tr=[];for(const O of out)for(const D of O)tr.push(D.buffer);postMessage({t:'done',id:d.id,out},tr)}}
 catch(err){postMessage({t:'err',id:d.id,m:String(err&&err.message||err)})}};`}
function sgWorker(){if(!SG2.wk){SG2.wk=new Worker(URL.createObjectURL(new Blob([sgWSrc()],{type:'application/javascript'})));
    SG2.wk.onmessage=e=>{const h=SG2.wh.get(e.data.id);if(h)h(e.data)};SG2.wk.onerror=e=>{const m=e.message||'the stem split worker failed';for(const h of[...SG2.wh.values()])h({t:'err',m})}}
  return SG2.wk}
/* stop every job of the quick worker (Stop in the Split sheet): the worker is thrown away and made again next time */
function sgStopQuick(){if(SG2.wk){SG2.wk.terminate();SG2.wk=null}for(const h of[...SG2.wh.values()])h({t:'err',m:'stopped',stopped:1})}
function sgStopNeural(){if(NEUWK){NEUWK.terminate();NEUWK=null}if(SG2.neuRej){const r=SG2.neuRej;SG2.neuRej=null;const e=new Error('stopped');e.stopped=1;r(e)}}
function sgReq(msg,tr,on){const id=++SG2.seq,w=sgWorker();msg.id=id;return new Promise((res,rej)=>{SG2.wh.set(id,d=>{if(d.t==='done'||d.t==='mix'){SG2.wh.delete(id);res(d)}else if(d.t==='err'){SG2.wh.delete(id);const e=new Error(d.m);if(d.stopped)e.stopped=1;rej(e)}else if(on)on(d)});w.postMessage(msg,tr)})}
function sgLR(buf){const L=buf.getChannelData(0).slice(),R=(buf.numberOfChannels>1?buf.getChannelData(1):buf.getChannelData(0)).slice();return[L,R]}
/* the mix's own columns, in the worker */
async function sgMixCols(buf,cw){const[L,R]=sgLR(buf);const d=await sgReq({t:'mix',L,R,sr:buf.sampleRate,cw},[L.buffer,R.buffer]);return d.cols}
const SG_HOOKS={onChunk:(job,msg)=>{}};/* for any lane: SG_HOOKS.onChunk(job,msg) is called after every chunk of every stem split job (replace or wrap it) */
