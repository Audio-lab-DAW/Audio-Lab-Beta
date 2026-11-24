from eng import *
import json
al=start()
print(al.run("""(async()=>{ensureCtx();const o={};
for(const sr of [44100,48000,96000])for(const [type,pp] of [['vocoder',{}],['pshift',{}],['pcorr',{}],['reson',{}],['limit',{look:10}],['limit',{look:10,style:'aggressive'}],['gate',{look:5}],['mband',{}],['clip',{os:'2x'}],['ott',{}]]){try{const oc=new OfflineAudioContext(2,sr,sr);await wlLoad(oc);const x=mkFxNode(oc,type);const f=mkFx(type);Object.assign(f.p,pp);x.set(f.p);
 const b=oc.createBuffer(2,sr,sr);for(let ch=0;ch<2;ch++){const d=b.getChannelData(ch);for(let i=Math.round(.2*sr);i<Math.round(.6*sr);i++)d[i]=Math.sin(2*Math.PI*1000*(i/sr-.2))*.5}
 const s=oc.createBufferSource();s.buffer=b;s.connect(x.in);x.out.connect(oc.destination);s.start();const r=await oc.startRendering();const d=r.getChannelData(0);
 let pk=0;for(const v of d)pk=Math.max(pk,Math.abs(v));let on=-1;for(let i=0;i<d.length;i++){if(Math.abs(d[i])>pk*.1){on=i;break}}
 o[type+JSON.stringify(pp)+'@'+sr]=on-Math.round(.2*sr)}catch(e){o[type+'@'+sr]='err '+String(e).slice(0,40)}}
return JSON.stringify(o)})()"""))
al.stop()
