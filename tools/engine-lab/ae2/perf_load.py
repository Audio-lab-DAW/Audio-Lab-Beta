"""CPU per track and where a big project runs out (task AE2).
1) per track: 8 bars of the Peak section (bars 161-168) rendered alone in one OfflineAudioContext (one thread),
   time per second of sound = the share of one core that track needs (the master chain is included in every solo render, so the
   cheapest track is the floor).
2) the whole song at x1, x2 and x4 (copies of every track): the same 8 bars in one context (one core: what the live engine has)
3) live: playing bars 161- at buffer Auto 256 and 512 for 8 s: the app's load meter, dropouts, main-thread long tasks.
Run: python3 perf_load.py"""
import json,sys
from common import *
B0=(161-1)*4.0;B1=B0+32;SEC=32*60/145.0
out={'per_track':[],'song':[],'live':[]}
def rt(al,o):
    return al.page.evaluate("async o=>{const t=performance.now();const h=await AudioLab.render(o);const ms=performance.now()-t;AudioLab.free(h.id);return ms}",o)
al=start();R=fractals(al)
for t in R['tracks']:
    if t.get('kind'):continue
    ms=min(rt(al,{'b0':B0,'b1':B1,'single':True,'only':al.tid(t['name'])}) for _ in range(2))
    row={'track':t['name'],'preset':t.get('preset'),'fx':[f.get('type') for f in t.get('fx',[])],'ms_per_s':round(ms/SEC,1)}
    out['per_track'].append(row);print(json.dumps(row),flush=True)
LIVE="""(async()=>{const w=ms=>new Promise(r=>setTimeout(r,ms));UI.buf=%d;UI.abuf=256;restartAudio(true);ensureCtx();await ctx.resume();await w(1500);
let lt=0,ln=0,lmax=0;const po=new PerformanceObserver(l=>{for(const e of l.getEntries()){lt+=e.duration;ln++;lmax=Math.max(lmax,e.duration)}});po.observe({type:'longtask',buffered:false});
const d0=URS.total||0;pos=%f;start();await w(1500);CPU.pkMax=0;const a=[];for(let i=0;i<8;i++){await w(1000);if(CPU.aud!=null)a.push(CPU.aud)}stop();po.disconnect();
return{buf:%d,rq:ctx.renderQuantumSize,load_avg:a.length?+(a.reduce((x,y)=>x+y)/a.length).toFixed(3):null,load_peak:+(CPU.pkMax||0).toFixed(3),dropouts:(URS.total||0)-d0,longtasks:ln,longtask_ms:Math.round(lt),longtask_max:Math.round(lmax)}})()"""
for k in (1,2,4):
    if k>1:R=fractals(al,k)
    ms=rt(al,{'b0':B0,'b1':B1,'single':True})
    row={'copies':k,'tracks':len(R['tracks']),'ms_per_s':round(ms/SEC,1),'core_share':round(ms/SEC/1000,3)}
    out['song'].append(row);print(json.dumps(row),flush=True)
    for buf in (-1,512):
        r=al.run(LIVE%(buf,B0,buf));r['copies']=k;out['live'].append(r);print(json.dumps(r),flush=True)
json.dump(out,open('perf_load_result.json','w'),indent=1)
al.stop()
