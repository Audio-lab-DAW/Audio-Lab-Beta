from eng import *
import json
al=start()
logs=[];al.page.on('pageerror',lambda e:logs.append('ERR '+str(e)));al.page.on('console',lambda m:logs.append(m.text))
print(al.run("""(async()=>{const w=ms=>new Promise(r=>setTimeout(r,ms));const o={};
const st=b=>{let pk=0,e=0;const d=b.getChannelData(0);for(const x of d){pk=Math.max(pk,Math.abs(x));e+=x*x}return [+pk.toFixed(3),+Math.sqrt(e/d.length).toFixed(4)]};
for(const pk of Object.keys(WTPRE).slice(0,6)){const t=mkTrack('inst','wtab','W');Object.assign(t.inst,JSON.parse(JSON.stringify(WTPRE[pk])));const notes=[];for(let i=0;i<8;i++)notes.push({p:45+(i*5)%12,s:i*.5,l:.45,v:.8});t.clips.push(mkClip({start:0,len:4,name:'w',notes}));S.tracks=[t];changed(true);ensureCtx();await ctx.resume();
 const r={};for(const on of [false,true]){UI.poly=on;const t0=performance.now();const b=await renderMix(48000,0,4,1,false,t.id,false,null);r[on?'new':'old']=st(b).concat(Math.round(performance.now()-t0))}o[pk]=r}
UI.poly=true;CPU.late=0;S.loop=false;pos=0;start();await w(2500);stop();o.live={late:CPU.late,lead:PLEAD.s};
return JSON.stringify(o)})()"""))
print([l for l in logs if 'ERR' in l or 'poly' in l][:3]);al.stop()
