"""For lane K (seen in task LT-2): syncGraph sets each track's compensation delay with N.pdc.delayTime.setValueAtTime(d, ctx.currentTime);
on the build machine a later change sometimes does not take (N.pdcV says the new value, the param keeps the old one), on v0.289 before LT-2 too.
Adds and removes a resonance suppressor on the Bass six times and prints [heard delay ms, intended ms] for the Kick.
Run: python3 tools/engine-lab/lt/pdc_set_probe.py <index.html>"""
import sys,os,json
sys.path.insert(0,'/home/claude/audio-lab-beta/tools/remake')
from alab import AudioLab
al=AudioLab(sys.argv[1]).start()
print(al.run("""(async()=>{const w=ms=>new Promise(r=>setTimeout(r,ms));UI.buf=256;UI.ltPlayBuf=0;restartAudio(true);ensureCtx();await ctx.resume();await w(500);const out=[];
for(let k=0;k<6;k++){const kick=S.tracks.find(t=>t.name==='Kick'),bs=S.tracks.find(t=>t.name==='Bass');const f=mkFx('reson');bs.fx.push(f);changed(true);syncGraph();await w(500);
 const N=NODES.get(kick.id);out.push([+(N.pdc.delayTime.value*1000).toFixed(2),+(N.pdcV*1000).toFixed(2)]);bs.fx.pop();changed(true);syncGraph();await w(500);out.push([+(N.pdc.delayTime.value*1000).toFixed(2),+(N.pdcV*1000).toFixed(2),NODES.get(kick.id)===N])}
return JSON.stringify(out)})()"""))
al.stop()
