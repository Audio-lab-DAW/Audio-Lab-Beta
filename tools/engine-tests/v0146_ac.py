from eng import *
import json
al=start()
logs=[];al.page.on('console',lambda m:logs.append(m.text));al.page.on('pageerror',lambda e:logs.append('ERR '+str(e)))
print(al.run("""(async()=>{const w=ms=>new Promise(r=>setTimeout(r,ms));
const mk=(pre,nm,ov)=>{const t=mkTrack('inst',pre,nm);const notes=[];for(let i=0;i<16;i++)notes.push({p:36+(i*5)%12,s:i*.5,l:ov?.6:.4,v:i%4===0?.95:.7});t.clips.push(mkClip({start:0,len:8,name:nm,notes}));return t};
S.tracks=[mk('acid','A',0),mk('acid','A slide',1),mk('plant','P',0)];changed(true);ensureCtx();await ctx.resume();await w(800);
const st=b=>{let pk=0,e=0;const d=b.getChannelData(0);for(const x of d){pk=Math.max(pk,Math.abs(x));e+=x*x}return [+pk.toFixed(3),+Math.sqrt(e/d.length).toFixed(4)]};
const o={};for(const t of S.tracks.slice(0,2)){o[t.name]={};for(const on of [false,true]){UI.poly=on;const t0=performance.now();const b=await renderMix(48000,0,8,1,false,t.id,false,null);o[t.name][on?'pooled':'old']=st(b).concat(Math.round(performance.now()-t0))}}
UI.poly=true;
// held note on the plant track
const pt=S.tracks[2],an=()=>{const a=NODES.get(pt.id).an,d=new Float32Array(256);a.getFloatTimeDomainData(d);let p=0;for(const x of d)p=Math.max(p,Math.abs(x));return +p.toFixed(3)};
const h=voiceOn(pt,60,.8);await w(700);const held=an();h.off();await w(2500);const after=an();
const h2=voiceOn(S.tracks[0],40,.8);await w(400);const a1=(()=>{const a=NODES.get(S.tracks[0].id).an,d=new Float32Array(256);a.getFloatTimeDomainData(d);let p=0;for(const x of d)p=Math.max(p,Math.abs(x));return +p.toFixed(3)})();h2.off();await w(300);
const a2=(()=>{const a=NODES.get(S.tracks[0].id).an,d=new Float32Array(256);a.getFloatTimeDomainData(d);let p=0;for(const x of d)p=Math.max(p,Math.abs(x));return +p.toFixed(3)})();
o.held={plantHeld:held,plantAfterRelease:after,acidHeld:a1,acidAfter:a2};return JSON.stringify(o)})()"""))
print([l for l in logs if 'ERR' in l or 'poly' in l][:4])
al.stop()
