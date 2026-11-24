"""old engine vs new engine: whole-mix render time (a stand-in for audio-thread load), node counts, and a null test"""
from eng import *
import song,sys
B=int(sys.argv[1]) if len(sys.argv)>1 else 81
al=start();R=song.recipe();build(al,R)
js="""(async()=>{mapAnalyze=()=>{};MAP.busy=1;const b0=%d,b1=%d,dur=secSpan(b0,b1),out={dur};let cnt=0;
const P=BaseAudioContext.prototype;for(const k of ['createGain','createBiquadFilter','createOscillator','createBufferSource','createStereoPanner']){const f=P[k];P[k]=function(){cnt++;return f.apply(this,arguments)}}
const T=async(fast)=>{let m=1e9,buf=null,n=0;for(let k=0;k<2;k++){cnt=0;const a=performance.now();buf=await renderMix(44100,b0,b1,0,false,null,!!fast);m=Math.min(m,performance.now()-a);n=cnt}return{ms:Math.round(m),nodes:n,buf}};
const rms=(a,b)=>{let s=0,r=0;const x=a.getChannelData(0),y=b.getChannelData(0);for(let i=0;i<x.length;i++){const d=x[i]-y[i];s+=d*d;r+=x[i]*x[i]}return[10*Math.log10(s/x.length+1e-20),10*Math.log10(r/x.length+1e-20)]};
ensureCtx();UI.noteCache=false;await T();const A=await T();out.old={ms:A.ms,nodes:A.nodes};
const Bk=A;
UI.noteCache=true;const t0=performance.now();ncScan();while(NC.q.length||NC.busy)await new Promise(r=>setTimeout(r,50));out.cache={entries:NC.map.size,mb:+(NC.bytes/1e6).toFixed(1),buildMs:Math.round(performance.now()-t0)};
NC.bench=true;NC.hits=0;NC.miss=0;const C=await T();NC.bench=false;out.nc={ms:C.ms,nodes:C.nodes,hits:NC.hits,miss:NC.miss,diff:rms(Bk.buf,C.buf)};
NC.bench=true;const D=await T(true);NC.bench=false;out.ncNoFx={ms:D.ms,nodes:D.nodes};
return JSON.stringify(out)})()"""%(song.bar(B),song.bar(B+8))
r=json.loads(al.run(js));d=r['dur']
print('bars %d-%d, %.1f s of audio'%(B,B+7,d))
for k,lab in [('old','note cache off'),('nc','note cache on'),('ncNoFx','  (same, effects off)')]:
    x=r[k];print('%-26s %6d ms = %4.0f%% of real time   %6d nodes   %s'%(lab,x['ms'],x['ms']/10/d,x['nodes'],('hits %d miss %d'%(x['hits'],x['miss']) if 'hits' in x else '')+(' difference %.1f dB vs signal %.1f dB'%tuple(x['diff']) if 'diff' in x else '')))
print('cache:',r['cache'])
al.stop()
