from eng import *
import song,json
al=start();R=song.recipe();build(al,R)
print(al.run("""(async()=>{ensureCtx();await ctx.resume();const sr=48000,b0=%f,b1=%f,o={};
const diff=(A,B)=>{const W=Math.round(sr*.05);let ea=0,eb=0,dev=[],n=A[0].length;for(let i=0;i+W<=n;i+=W){let a=0,b=0;for(let c=0;c<2;c++)for(let j=i;j<i+W;j++){a+=A[c][j]*A[c][j];b+=B[c][j]*B[c][j]}ea+=a;eb+=b;if(a/W/2>1e-4)dev.push(Math.abs(10*Math.log10((b+1e-12)/(a+1e-12))))}dev.sort((x,y)=>x-y);return {levelDb:+(10*Math.log10(eb/ea)).toFixed(2),env50:+(dev[dev.length>>1]||0).toFixed(2),env95:+(dev[Math.floor(dev.length*.95)]||0).toFixed(2)}};
const keep={};
for(const on of [false,true,false,true,false,true]){UI.poly=on;PVN.n=0;const t=performance.now();const b=await renderMix(sr,b0,b1,1,false,null,false,null);const ms=performance.now()-t;const k=on?'pooled':'old';o[k]=o[k]||{ms:1e9};o[k].ms=Math.min(o[k].ms,Math.round(ms));o[k].notes=PVN.n;keep[k]=[b.getChannelData(0).slice(),b.getChannelData(1).slice()]}
o.mix=diff(keep.old,keep.pooled);
// per track
const tr={};for(const t of S.tracks){if(!t.inst||!pvOK(t.inst))continue;const r=[];for(const on of [false,true]){UI.poly=on;const b=await renderMix(sr,b0,b1,1,false,t.id,false,null);r.push([b.getChannelData(0).slice(),b.getChannelData(1).slice()])}const d=diff(r[0],r[1]);let pk=0;for(const x of r[1][0])pk=Math.max(pk,Math.abs(x));if(pk>1e-4)tr[t.name]=d}
UI.poly=true;o.tracks=tr;return JSON.stringify(o)})()"""%(song.bar(81),song.bar(89))))
al.stop()
