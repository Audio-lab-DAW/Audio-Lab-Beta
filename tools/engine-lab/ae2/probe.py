import sys,json;sys.path.insert(0,'/home/claude/alpro/tools/remake')
from alab import AudioLab
al=AudioLab('/home/claude/alpro/index.html').start()
print(al.version)
print(al.run("""(async()=>{const w=ms=>new Promise(r=>setTimeout(r,ms));const o=[];
for(const [buf,hq] of [[-1,false],[128,false],[256,false],[512,false],[1024,false],[0,false],[0,true]]){UI.buf=buf;UI.abuf=256;UI.hq=hq;restartAudio(true);ensureCtx();await ctx.resume();await w(800);const ts=ctx.getOutputTimestamp();
o.push({buf,hq,sr:ctx.sampleRate,rq:ctx.renderQuantumSize,base:+(ctx.baseLatency*1000).toFixed(2),out:+((ctx.outputLatency||0)*1000).toFixed(2),lag:+((ctx.currentTime-ts.contextTime)*1000).toFixed(2),perfLag:+((performance.now()-ts.performanceTime)).toFixed(2),hint:ctx.__hint})}
return JSON.stringify(o)})()"""))
al.stop()
