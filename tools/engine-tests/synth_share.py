from eng import *
import song,json
al=start();R=song.recipe();build(al,R)
print(al.run("""(async()=>{const w=ms=>new Promise(r=>setTimeout(r,ms));const o=[];UI.buf=1024;restartAudio(true);ensureCtx();await ctx.resume();await w(2000);
const syn=S.tracks.filter(t=>t.inst&&(t.inst.preset==='plant'||NCGEN.has(t.inst.preset)));
for(const mode of ['nc-off','all','nc-off','all','all','nc-off']){for(const t of syn)t.mute=mode==='noSynth';UI.noteCache=mode!=='nc-off';changed(true);pos=%f;start();await w(1500);CPU.pkMax=0;const a=[];for(let i=0;i<6;i++){await w(1000);if(CPU.aud!=null)a.push(CPU.aud)}stop();await w(800);
o.push({mode,avg:a.length?+(a.reduce((x,y)=>x+y)/a.length).toFixed(3):null,pk:+(CPU.pkMax||0).toFixed(3)})}
return JSON.stringify({nSynth:syn.length,presets:[...new Set(syn.map(t=>t.inst.preset))],o})})()"""%song.bar(81)))
al.stop()
