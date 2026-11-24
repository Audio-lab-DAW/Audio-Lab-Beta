from eng import *
import json
al=start()
logs=[];al.page.on('pageerror',lambda e:logs.append('ERR '+str(e)))
print(al.run("""(async()=>{const w=ms=>new Promise(r=>setTimeout(r,ms));const sr=48000;
const mk=(nm)=>{const t=mkTrack('inst','zhat',nm);t.clips.push(mkClip({start:0,len:4,name:nm,notes:[{p:60,s:1,l:.2,v:.9}]}));return t};
const A=mk('A'),B=mk('B'),C=mk('C'),D=mk('D');S.tracks=[A,B,C,D];
const add=(t,type,p)=>{const f=mkFx(type);Object.assign(f.p,p||{});t.fx.push(f)};add(A,'comp',{threshold:0,ratio:1});add(C,'limit',{look:10,gain:0});add(D,'pshift',{});
changed(true);ensureCtx();await ctx.resume();await w(500);
const onset=async(t)=>{for(const x of S.tracks)x.mute=x!==t;const b=await renderMix(sr,0,4,0,false,null,false,null);const d=b.getChannelData(0);let pk=0;for(const v of d)pk=Math.max(pk,Math.abs(v));for(let i=0;i<d.length;i++)if(Math.abs(d[i])>pk*.2)return i;return -1};
const o={};for(const on of [false,true]){UI.pdc=on;const r={};for(const t of S.tracks)r[t.name]=await onset(t);o[on?'pdcOn':'pdcOff']=r}
for(const x of S.tracks)x.mute=false;UI.pdc=true;changed(true);await w(300);
o.live={target_ms:+(CPU.pdc*1000).toFixed(2),delays:S.tracks.map(t=>+(NODES.get(t.id).pdc.delayTime.value*sr*ctx.sampleRate/sr).toFixed(0))};
return JSON.stringify(o)})()"""))
print(logs[:3]);al.stop()
