"""live playback in the test browser: audio-thread load reported by the browser itself (renderCapacity), underruns, main-thread scheduling time"""
from eng import *
import song,sys,time
al=start();R=song.recipe();build(al,R)
print(al.run("(()=>{ensureCtx();return JSON.stringify({rc:!!ctx.renderCapacity,ps:!!ctx.playbackStats,sr:ctx.sampleRate,base:ctx.baseLatency,ua:navigator.userAgent.match(/Chrome\\/[0-9.]+/)[0],cores:navigator.hardwareConcurrency})})()"))
def run(label,bar,secs,setup):
    al.run(setup)
    js="""(async()=>{mapAnalyze=()=>{};const L=[];const rc=ctx.renderCapacity;const h=e=>{L.push([e.averageLoad,e.peakLoad,e.underrunRatio])};if(rc){rc.addEventListener('update',h);rc.start({updateInterval:1})}
    let sch=0,n=0;const _sc=schedule;schedule=function(){const a=performance.now();const r=_sc.apply(this,arguments);sch+=performance.now()-a;n++;return r};
    const ps0=ctx.playbackStats?ctx.playbackStats.underrunEvents:0;const late0=CPU.late;
    pos=%f;if(play.on)stop();await ctx.resume();start();await new Promise(r=>setTimeout(r,1500));const a0=ctx.currentTime,w0=performance.now();let fr=0,worst=0,lastF=performance.now(),run=true;(function f(){if(!run)return;const n=performance.now();worst=Math.max(worst,n-lastF);lastF=n;fr++;setTimeout(f,4)})();await new Promise(r=>setTimeout(r,%d));run=false;const slip=((performance.now()-w0)/1000-(ctx.currentTime-a0));slpTick(true);const nodes=NGC.reduce((s,x)=>s+x.L.length,0);stop();schedule=_sc;if(rc){rc.removeEventListener('update',h);rc.stop()}
    const avg=L.reduce((s,x)=>s+x[0],0)/Math.max(1,L.length),pk=Math.max(0,...L.map(x=>x[1])),ur=L.reduce((s,x)=>s+x[2],0)/Math.max(1,L.length);
    return JSON.stringify({audioFellBehindSec:+slip.toFixed(2),worstMainThreadStallMs:Math.round(worst),avg:+avg.toFixed(2),peak:+pk.toFixed(2),underrunRatio:+ur.toFixed(3),underruns:(ctx.playbackStats?ctx.playbackStats.underrunEvents:0)-ps0,late:CPU.late-late0,schedMsPerSec:+(sch/%d*1000).toFixed(1),liveNoteNodes:nodes,nc:[NC.hits,NC.miss,NC.map.size]})})()"""%(song.bar(bar),secs*1000,secs*1000)
    print(label.ljust(34),al.run(js),flush=True)
mode=sys.argv[1]
if mode=="old":al.run("UI.eqAll=true;UI.noteCache=false;UI.fxSleep=false;0")
else:
    al.run("UI.noteCache=true;0")
build(al,R)   # rebuild so the effect chains are made with these settings
if mode!='old':al.run("(async()=>{NC.scanRev=-1;pos=0;ncScan();while(NC.q.length||NC.busy)await new Promise(r=>setTimeout(r,50));return NC.map.size})()")
for B in (1,81,161):run(mode+' engine, from bar %d'%B,B,12,"0")
al.stop()
