from eng import *
import song,json
al=start();R=song.recipe();build(al,R)
print(al.run("""(async()=>{ensureCtx();await ctx.resume();const sr=ctx.sampleRate,b0=%f,b1=%f;
const ren=async()=>{const b=await renderMix(sr,b0,b1,2,false,null,false,null);return [b.getChannelData(0).slice(),b.getChannelData(1).slice()]};
const diff=(A,B)=>{const W=Math.round(sr*.05);let ea=0,eb=0,dev=[],n=Math.round(secSpan(b0,b1)*sr);for(let i=0;i+W<=n;i+=W){let a=0,b=0;for(let c=0;c<2;c++)for(let j=i;j<i+W;j++){a+=A[c][j]*A[c][j];b+=B[c][j]*B[c][j]}ea+=a;eb+=b;if(a/W/2>1e-4)dev.push(Math.abs(10*Math.log10((b+1e-12)/(a+1e-12))))}dev.sort((x,y)=>x-y);return {levelDb:+(10*Math.log10(eb/ea)).toFixed(2),env50:+(dev[dev.length>>1]||0).toFixed(2),env95:+(dev[Math.floor(dev.length*.95)]||0).toFixed(2)}};
const A=await ren(),A2=await ren(),out={sr,again:diff(A,A2),tracks:[]};
for(const [nm,mode] of %s){const t=S.tracks.find(q=>q.name===nm);if(!t){out.tracks.push({nm,missing:1});continue}const fx=t.fx.map(f=>f.type).join(',');const t0=performance.now();await freezeTrack(t,mode);const ms=Math.round(performance.now()-t0);
 if(!t.frz){out.tracks.push({nm,failed:1});continue}const B=await ren();const o={nm,mode,fx,inst:t.frz.clips&&S.tracks.includes(t)?(t.inst&&t.inst.preset):'',ms,clipSec:+(t.clips[0].dur).toFixed(1),frozen:diff(A,B)};await freezeTrack(t);const C=await ren();o.unfrozen=diff(A,C);out.tracks.push(o)}
return JSON.stringify(out)})()"""%(song.bar(81),song.bar(83),json.dumps([["Bass","post"],["Lead","post"],["Hat","post"]]))))
al.stop()
