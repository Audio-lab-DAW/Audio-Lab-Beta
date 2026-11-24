from eng import *
import song,json
al=start();R=song.recipe();build(al,R)
print(al.run("""(async()=>{ensureCtx();await ctx.resume();const sr=48000,b0=%f,b1=%f,o={};let nconv=0;
const oc0=BaseAudioContext.prototype.createConvolver;BaseAudioContext.prototype.createConvolver=function(){nconv++;return oc0.apply(this,arguments)};
const rms=b=>{let e=0;const d=b.getChannelData(0);for(const v of d)e+=v*v;return Math.sqrt(e/d.length)};
for(const sh of [false,true,false,true,false,true]){UI.spaceShared=sh;nconv=0;const t=performance.now();const b=await renderMix(sr,b0,b1,1,false,null,false,null);const ms=performance.now()-t;const k=sh?'shared':'perTrack';o[k]=o[k]||{ms:1e9};o[k].ms=Math.min(o[k].ms,Math.round(ms));o[k].conv=nconv;o[k].rms=+rms(b).toFixed(4)}
UI.spaceShared=true;return JSON.stringify(o)})()"""%(song.bar(81),song.bar(89))))
al.stop()
