from eng import *
al=start()
print(al.run("""(async()=>{const w=ms=>new Promise(r=>setTimeout(r,ms));
const t=mkTrack('inst','saw','S');t.clips.push(mkClip({start:0,len:16,name:'s',notes:[{p:57,s:0,l:16,v:.8}]}));S.tracks=[t];const f=mkFx('limit');t.fx.push(f);changed(true);ensureCtx();await ctx.resume();await w(600);
const lvl=()=>{const a=NODES.get(t.id).an,d=new Float32Array(256);a.getFloatTimeDomainData(d);let p=0;for(const x of d)p=Math.max(p,Math.abs(x));return +p.toFixed(4)};
S.loop=false;pos=0;start();await w(1500);const a=lvl();f.p.gain=-24;changed(false);syncGraph();await w(1200);const b=lvl();stop();
return JSON.stringify({gain0:a,gainMinus24:b,windowP:typeof window.p})})()"""))
al.stop()
