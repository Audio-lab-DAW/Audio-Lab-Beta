from eng import *
import song,json
al=start();R=song.recipe();build(al,R)
print(al.run("""(async()=>{const w=ms=>new Promise(r=>setTimeout(r,ms));const o=[];
for(const [buf,rq] of [[1024,0],[1024,undefined],[1024,0],[1024,undefined],[512,0],[512,undefined]]){UI.buf=buf;UI.rq=rq;restartAudio(true);ensureCtx();await ctx.resume();await w(2500);pos=%f;start();await w(1500);CPU.pkMax=0;const a=[];for(let i=0;i<6;i++){await w(1000);if(CPU.aud!=null)a.push(CPU.aud)}stop();
o.push({buf,rq:ctx.renderQuantumSize,bl:Math.round((ctx.baseLatency||0)*ctx.sampleRate),avg:a.length?+(a.reduce((x,y)=>x+y)/a.length).toFixed(3):null,pk:+(CPU.pkMax||0).toFixed(3),late:CPU.late,drops:URS.total})}
return JSON.stringify(o)})()"""%song.bar(81)))
al.stop()
