from eng import *
import json
al=start()
logs=[];al.page.on('console',lambda m:logs.append(m.text));al.page.on('pageerror',lambda e:logs.append('ERR '+str(e)))
print(al.run("""(async()=>{const w=ms=>new Promise(r=>setTimeout(r,ms));
const mk=(pre,nm)=>{const t=mkTrack('inst',pre,nm);const notes=[];for(let i=0;i<16;i++)notes.push({p:48+(i*5)%12,s:i*.5,l:.4,v:.8});t.clips.push(mkClip({start:0,len:8,name:nm,notes}));return t};
S.tracks=[mk('venom','V'),mk('plant','P'),mk('saw','S'),mk('pad','D')];S.tracks[1].inst.space=40;changed(true);ensureCtx();await ctx.resume();await w(800);
const st=b=>{let pk=0,e=0;const d=b.getChannelData(0);for(const x of d){pk=Math.max(pk,Math.abs(x));e+=x*x}return [+pk.toFixed(3),+Math.sqrt(e/d.length).toFixed(4)]};
const o={};for(const t of S.tracks){o[t.name]={};for(const on of [false,true]){UI.poly=on;const b=await renderMix(48000,0,8,1,false,t.id,false,null);o[t.name][on?'pooled':'old']=st(b)}}
UI.poly=true;S.loop=true;pos=0;start();await w(6000);const an=NODES.get(S.tracks[1].id).an,d=new Float32Array(256);an.getFloatTimeDomainData(d);let lp=0;for(const x of d)lp=Math.max(lp,Math.abs(x));stop();
o.live={engines:(PVS.get(ctx)||new Map()).size,venom:(VNS.get(ctx)||new Map()).size,late:CPU.late,plantPeakNow:+lp.toFixed(3)};return JSON.stringify(o)})()"""))
print([l for l in logs if 'ERR' in l or 'poly' in l or 'venom' in l][:4])
al.stop()
