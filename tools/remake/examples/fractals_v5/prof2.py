"""per track: nodes created, main-thread build time, audio render time (offline, 8 bars). min of 2 runs."""
from eng import *
import song,sys
B=int(sys.argv[1]) if len(sys.argv)>1 else 81
al=start();R=song.recipe();build(al,R)
js="""(async()=>{MAP.busy=1;const b0=%d,b1=%d,out=[];const dur=secSpan(b0,b1);let cnt=0,tS=0;
const P=BaseAudioContext.prototype;for(const k of Object.getOwnPropertyNames(P)){if(k.startsWith('create')&&typeof P[k]==='function'){const f=P[k];P[k]=function(){cnt++;return f.apply(this,arguments)}}}
const sr0=OfflineAudioContext.prototype.startRendering;OfflineAudioContext.prototype.startRendering=function(){tS=performance.now();return sr0.apply(this,arguments)};
const run=async(id,fast)=>{let best=null;for(let k=0;k<1;k++){cnt=0;const a=performance.now();await renderMix(44100,b0,b1,0,false,id,fast);const e=performance.now();const r={n:cnt,build:tS-a,rend:e-tS};if(!best||r.build+r.rend<best.build+best.rend)best=r}return best};
const g=S.tracks.find(t=>t.kind==='group'&&t.name==='FX');const base=await run(g.id,true);
for(const t of S.tracks){if(!t.clips||!t.clips.some(c=>c.start<b1&&c.start+c.len>b0))continue;const f=await run(t.id,false),d=await run(t.id,true);out.push([t.name,f.n,Math.round(f.build),Math.round(f.rend),d.n,Math.round(d.build),Math.round(d.rend),t.fx.map(x=>x.type).join('+')])}
const all=await run(null,false);
return JSON.stringify({dur,base,all,out})})()"""%(song.bar(B),song.bar(B+8))
r=json.loads(al.run(js));b=r['base']
print('bars %d: %.1f s of audio. empty track: %d nodes, build %d ms, render %d ms'%(B,r['dur'],b['n'],b['build'],b['rend']))
print('WHOLE MIX: %d nodes, build %d ms, render %d ms = %.0f%% of real time'%(r['all']['n'],r['all']['build'],r['all']['rend'],r['all']['rend']/10/r['dur']))
print('%-16s %6s %7s %7s | %6s %7s %7s | fx'%('track','nodes','build','render','nodes','build','render'))
for n,fn,fb,fr,dn,dbd,dr,fx in sorted(r['out'],key=lambda x:-(x[3]+x[2])):
    print('%-16s %6d %7d %7d | %6d %7d %7d | %s'%(n,fn,fb,fr-b['rend'],dn,dbd,dr-b['rend'],fx))
al.stop()
