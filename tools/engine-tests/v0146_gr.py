from eng import *
import json
al=start()
logs=[];al.page.on('console',lambda m:logs.append(m.text));al.page.on('pageerror',lambda e:logs.append('ERR '+str(e)))
print(al.run("""(async()=>{const w=ms=>new Promise(r=>setTimeout(r,ms));
const t=mkTrack('inst','sampler','G');t.inst.mode='grain';const notes=[];for(let i=0;i<8;i++)for(const d of [0,4,7])notes.push({p:55+(i*5)%7+d,s:i*1,l:.9,v:.8});t.clips.push(mkClip({start:0,len:8,name:'g',notes}));S.tracks=[t];changed(true);ensureCtx();await ctx.resume();await w(800);
const I=t.inst;const o={inst:{buf:String(I.buf).slice(0,20),dens:I.dens,size:I.size,ftype:I.ftype,mode:I.mode}};
const st=b=>{let pk=0,e=0,e2=0;const d=b.getChannelData(0),r=b.getChannelData(1);for(let i=0;i<d.length;i++){pk=Math.max(pk,Math.abs(d[i]));e+=d[i]*d[i];e2+=r[i]*r[i]}return [+pk.toFixed(3),+Math.sqrt(e/d.length).toFixed(4),+Math.sqrt(e2/d.length).toFixed(4)]};
for(const dens of [18,60]){I.dens=dens;for(const on of [false,true,false,true]){UI.poly=on;const t0=performance.now();const b=await renderMix(48000,0,8,1,false,t.id,false,null);o[(on?'engine':'old')+dens]=st(b).concat(Math.round(performance.now()-t0))}}
UI.poly=true;I.dens=40;changed(true);
let nodes=0;const P=BaseAudioContext.prototype,oc=P.createBufferSource;P.createBufferSource=function(){if(this===ctx)nodes++;return oc.apply(this,arguments)};
S.loop=false;pos=0;start();await w(4000);const an=NODES.get(t.id).an,d=new Float32Array(256);an.getFloatTimeDomainData(d);let lp=0;for(const x of d)lp=Math.max(lp,Math.abs(x));stop();
o.live={sourcesCreated:nodes,peakNow:+lp.toFixed(3),engines:(GVS.get(ctx)||new Map()).size,late:CPU.late};
UI.poly=false;nodes=0;pos=0;start();await w(4000);stop();o.liveOld={sourcesCreated:nodes};UI.poly=true;P.createBufferSource=oc;
const h=voiceOn(t,60,.8);await w(900);an.getFloatTimeDomainData(d);let hp=0;for(const x of d)hp=Math.max(hp,Math.abs(x));h.off();await w(2500);an.getFloatTimeDomainData(d);let ap=0;for(const x of d)ap=Math.max(ap,Math.abs(x));o.held=[+hp.toFixed(3),+ap.toFixed(4)];
return JSON.stringify(o)})()"""))
print([l for l in logs if 'ERR' in l or 'poly' in l or 'worklet' in l][:4])
al.stop()
