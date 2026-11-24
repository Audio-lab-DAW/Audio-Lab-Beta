from eng import *
import song
al=start();R=song.recipe();build(al,R)
js="""(async()=>{mapAnalyze=()=>{};const b0=%d,b1=%d;UI.noteCache=false;UI.eqAll=true;const A=await renderMix(44100,b0,b1,0,false,null,false);UI.eqAll=false;changed(true);const B=await renderMix(44100,b0,b1,0,false,null,false);
let s=0,r=0;const x=A.getChannelData(0),y=B.getChannelData(0);for(let i=0;i<x.length;i++){const d=x[i]-y[i];s+=d*d;r+=x[i]*x[i]}
ensureCtx();pos=320;start();await new Promise(r=>setTimeout(r,2500));slpTick(true);const asleep=S.tracks.filter(t=>NODES.get(t.id)&&NODES.get(t.id).slp).map(t=>t.name);stop();await new Promise(r=>setTimeout(r,400));slpTick(true);const after=S.tracks.filter(t=>NODES.get(t.id)&&NODES.get(t.id).slp).length;
return JSON.stringify({diffDb:10*Math.log10(s/x.length+1e-20),sigDb:10*Math.log10(r/x.length+1e-20),asleepWhilePlayingBar81:asleep,asleepAfterStop:after})})()"""%(song.bar(81),song.bar(83))
print(al.run(js));al.stop()
