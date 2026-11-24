from eng import *
import json
al=start()
print(al.run("""(async()=>{ensureCtx();const sr=48000,o={};
for(const [type,pp] of [['limit',{gain:-12}],['limit',{gain:0}],['crush',{bits:2}],['crush',{bits:16}],['gate',{thr:0}],['gate',{thr:-80}]]){const oc=new OfflineAudioContext(2,sr*2,sr);await wlLoad(oc);const x=mkFxNode(oc,type);const f=mkFx(type);Object.assign(f.p,pp);x.set(f.p);
 const b=oc.createBuffer(2,sr*2,sr);for(let ch=0;ch<2;ch++){const d=b.getChannelData(ch);for(let i=0;i<d.length;i++)d[i]=Math.sin(2*Math.PI*220*i/sr)*.1}
 const s=oc.createBufferSource();s.buffer=b;s.connect(x.in);x.out.connect(oc.destination);s.start();const r=await oc.startRendering();const d=r.getChannelData(0);
 const rms=(a,z)=>{let e=0;for(let i=a;i<z;i++)e+=d[i]*d[i];return +Math.sqrt(e/(z-a)).toFixed(4)};o[type+JSON.stringify(pp)]=[rms(0,4800),rms(sr,sr+4800),rms(sr*2-4800,sr*2)]}
return JSON.stringify(o)})()"""))
al.stop()
