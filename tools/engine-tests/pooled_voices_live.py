from eng import *
import song,json
al=start();R=song.recipe();build(al,R)
logs=[];al.page.on('console',lambda m:logs.append(m.text))
print(al.run("""(async()=>{const w=ms=>new Promise(r=>setTimeout(r,ms));const o=[];
for(const buf of [1024,256]){UI.buf=buf;restartAudio(true);ensureCtx();await ctx.resume();await w(2500);
for(const on of [false,true,false,true]){UI.poly=on;pos=%f;PVN.n=0;const l0=CPU.late;start();await w(2000);CPU.pkMax=0;const a=[];for(let i=0;i<7;i++){await w(1000);if(CPU.aud!=null)a.push(CPU.aud)}const nodes=NGC.reduce((s,x)=>s+x.L.length,0);stop();await w(700);
o.push({buf,rq:ctx.renderQuantumSize,poly:on,avg:a.length?+(a.reduce((x,y)=>x+y)/a.length).toFixed(3):null,pk:+(CPU.pkMax||0).toFixed(3),late:CPU.late-l0,notes:PVN.n,nodesInFlight:nodes,ui:+CPU.ui.toFixed(3)})}}
return JSON.stringify(o)})()"""%song.bar(81)))
print([l for l in logs if 'poly' in l or 'worklet' in l][:3])
al.stop()
