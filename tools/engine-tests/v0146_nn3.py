from eng import *
import json
al=start()
print(al.run("""(async()=>{const w=ms=>new Promise(r=>setTimeout(r,ms));const o={};
const pres=Object.keys(PRESETS);S.tracks=[];for(const pre of pres){try{const t=mkTrack('inst',pre,pre);const notes=[];for(let i=0;i<8;i++)notes.push({p:48+(i*5)%12,s:i*1,l:.5,v:.8});t.clips.push(mkClip({start:0,len:8,name:pre,notes}));S.tracks.push(t)}catch(e){o[pre]={err:String(e)}}}
changed(true);ensureCtx();await ctx.resume();await w(1500);
const _sb=synthB;synthB=function(c,I,...a){const n0=NREC?NREC.length:0;const r=_sb.call(this,c,I,...a);if(c===ctx&&NREC){const e=o[I.preset]||(o[I.preset]={notes:0,nodes:0});e.notes++;e.nodes+=NREC.length-n0}return r};
S.loop=false;pos=0;start();await w(6500);stop();synthB=_sb;
const out=Object.entries(o).map(([k,e])=>[k,e.notes?+(e.nodes/e.notes).toFixed(1):e.err]).sort((a,b)=>(b[1]||0)-(a[1]||0));return JSON.stringify(out)})()"""))
al.stop()
