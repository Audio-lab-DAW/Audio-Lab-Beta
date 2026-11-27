"""Key press to sound in the web engine, measured inside the page (task AE2).
A real key press (Playwright keyboard -> Chromium input pipeline -> the app's keydown handler -> noteOn) on an armed track;
a tap worklet on the track's input finds the first sample of the note. Times:
  input   = handler time - the event's own timeStamp (main thread queue)
  sched   = context time of the first sample - ctx.currentTime at the handler (the app's +2 ms, the wait for the render quantum, the worklet message hop)
  ahead   = how far the render runs ahead of what is heard (ctx.currentTime - getOutputTimestamp().contextTime): Chrome's buffers + the device as reported
  total   = when the first sample is heard (per getOutputTimestamp) - the event's timeStamp
Run: python3 latency_chain.py [presses]"""
import sys,json,statistics as st
from common import *
N=int(sys.argv[1]) if len(sys.argv)>1 else 12
al=start();fractals(al)
TAP="""class T extends AudioWorkletProcessor{constructor(){super();this.arm=0;this.port.onmessage=e=>{this.arm=e.data}}process(I){const x=I[0]&&I[0][0];if(this.arm&&x){for(let i=0;i<x.length;i++)if(Math.abs(x[i])>1e-5){this.port.postMessage({f:currentFrame+i,q:x.length});this.arm=0;break}}return true}}registerProcessor('ae2-tap',T)"""
al.run("""(async()=>{window.AE2={};AE2.src=%s;return 1})()"""%json.dumps(TAP))
SETUP="""(async()=>{const w=ms=>new Promise(r=>setTimeout(r,ms));UI.buf=%d;UI.abuf=%d;UI.hq=false;restartAudio(true);ensureCtx();await ctx.resume();
await ctx.audioWorklet.addModule(URL.createObjectURL(new Blob([AE2.src],{type:'text/javascript'})));
for(const t of S.tracks)t.arm=false;const t=S.tracks.find(t=>t.name===%s);t.arm=true;changed(true);syncGraph();await w(600);
const N=NODES.get(t.id);const tap=new AudioWorkletNode(ctx,'ae2-tap');const z=ctx.createGain();z.gain.value=0;N.in.connect(tap);tap.connect(z);z.connect(ctx.destination);
AE2.tap=tap;AE2.res=[];tap.port.onmessage=e=>{AE2.cur.f=e.data.f;AE2.cur.q=e.data.q;AE2.res.push(AE2.cur)};
if(!AE2.l){AE2.l=1;window.addEventListener('keydown',e=>{if(!AE2.on||e.repeat)return;const o=ctx.getOutputTimestamp();AE2.cur={ev:e.timeStamp,h:performance.now(),ct:ctx.currentTime,oc:o.contextTime,op:o.performanceTime,sr:ctx.sampleRate};AE2.tap.port.postMessage(1)},true)}
if(%s){pos=%f;start()}await w(1500);AE2.on=1;return {rq:ctx.renderQuantumSize,base:ctx.baseLatency*1000,out:(ctx.outputLatency||0)*1000}})()"""
def one(buf,abuf,track,busy,label):
    info=al.run(SETUP%(buf,abuf,json.dumps(track),'true' if busy else 'false',(81-1)*4.0))
    for i in range(N):
        al.page.keyboard.down('z');al.page.wait_for_timeout(180);al.page.keyboard.up('z');al.page.wait_for_timeout(260)
    r=al.run("""(()=>{AE2.on=0;try{stop()}catch(e){}const o=AE2.res.map(c=>{const ts=c.f/c.sr;const heard=c.op+(ts-c.oc)*1000;return{input:c.h-c.ev,sched:(ts-c.ct)*1000,ahead:(c.ct-c.oc)*1000-(c.h-c.op),total:heard-c.ev}});try{AE2.tap.disconnect()}catch(e){}return o})()""")
    def s(k):
        v=[x[k] for x in r];return {'med':round(st.median(v),2),'min':round(min(v),2),'max':round(max(v),2)} if v else None
    row={'case':label,'buf':buf if buf>0 else ('auto '+str(abuf)),'track':track,'busy':busy,'n':len(r),**{k:round(v,2) for k,v in info.items()},'input':s('input'),'sched':s('sched'),'ahead':s('ahead'),'total':s('total')}
    print(json.dumps(row),flush=True);return row
rows=[]
for buf,abuf in [(128,256),(-1,256),(512,256),(1024,256)]:
    rows.append(one(buf,abuf,'Lead',False,'idle'))
for buf,abuf in [(128,256),(-1,256)]:
    rows.append(one(buf,abuf,'Kick',False,'idle, drum'))
    rows.append(one(buf,abuf,'Lead high',True,'song playing (bar 81, the played track silent in the song)'))
json.dump(rows,open('latency_chain_result.json','w'),indent=1)
al.stop()
