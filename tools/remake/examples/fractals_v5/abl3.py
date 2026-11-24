"""ablation on the new engine (note cache on): what still costs audio time? 4 bars, single runs"""
from eng import *
import song,sys
B=int(sys.argv[1]) if len(sys.argv)>1 else 81
al=start();R=song.recipe();build(al,R)
js="""(async()=>{mapAnalyze=()=>{};MAP.busy=1;const b0=%d,b1=%d,dur=secSpan(b0,b1),out=[];ensureCtx();UI.noteCache=true;UI.kRate=false;ncScan();while(NC.q.length||NC.busy)await new Promise(r=>setTimeout(r,50));NC.bench=true;
const T=async(fast)=>{let m=1e9;for(let k=0;k<3;k++){const a=performance.now();await renderMix(44100,b0,b1,0,false,null,!!fast);m=Math.min(m,performance.now()-a)}return Math.round(m)};
await T();const a1=await T(),a2=await T();out.push(['ALL (run 1)',a1]);out.push(['ALL (run 2)',a2]);out.push(['no effects at all',await T(true)]);
const allfx=()=>S.tracks.flatMap(t=>t.fx).concat(S.mfx||[]);
for(const ty of ['eq','side','ott','imager','clip','reverb','tdelay']){const L=allfx().filter(f=>f.type===ty&&f.on!==false);if(!L.length)continue;L.forEach(f=>f.on=false);out.push(['without '+ty+' x'+L.length,await T()]);L.forEach(f=>f.on=true)}
const grp=n=>S.tracks.filter(t=>{const g=grpOf(t);return g&&g.name===n});
for(const n of []){const L=grp(n);L.forEach(t=>t.mute=true);out.push(['without '+n+' tracks ('+L.length+')',await T()]);L.forEach(t=>t.mute=false)}
for(const n of ['Pad','Reverb (shared)']){const t=S.tracks.find(x=>x.name===n);if(!t)continue;t.mute=true;out.push(['without track '+n,await T()]);t.mute=false}
NC.bench=false;return JSON.stringify({dur,out})})()"""%(song.bar(B),song.bar(B+4))
r=json.loads(al.run(js));all_=min(r['out'][0][1],r['out'][1][1])
print('bars %d, %.1f s of audio'%(B,r['dur']))
for n,t in r['out']:print('%-38s %6d ms  %4.0f%% rt   saves %5d ms (%3.0f%% rt)'%(n,t,t/10/r['dur'],all_-t,(all_-t)/10/r['dur']),flush=True)
al.stop()
