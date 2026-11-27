"""Task LT-1: key press to sound on the armed Lead, before and after the playing buffer.
The method of tools/engine-lab/ae2/latency_chain.py (a real key press, a tap worklet on the track's input, getOutputTimestamp), on any index.html:
the engine is first left to settle in the buffer it picks for an armed track (LT-1: the playing buffer), then the tap is attached.
Run: python3 tools/engine-lab/lt/lt1_measure.py <index.html> <label> [presses]   (appends to lt1_measure_result.json)"""
import sys,os,json,statistics as st
HERE=os.path.dirname(os.path.abspath(__file__));sys.path.insert(0,os.path.join(HERE,'../ae2'))
import common
from alab import AudioLab
IDX=sys.argv[1];LABEL=sys.argv[2];N=int(sys.argv[3]) if len(sys.argv)>3 else 16
al=AudioLab(IDX).start();common.fractals(al)
TAP="""class T extends AudioWorkletProcessor{constructor(){super();this.arm=0;this.port.onmessage=e=>{this.arm=e.data}}process(I){const x=I[0]&&I[0][0];if(this.arm&&x){for(let i=0;i<x.length;i++)if(Math.abs(x[i])>1e-5){this.port.postMessage({f:currentFrame+i,q:x.length});this.arm=0;break}}return true}}registerProcessor('lt1-tap',T)"""
SETUP="""(async()=>{const w=ms=>new Promise(r=>setTimeout(r,ms));window.AE2={src:%s};UI.buf=-1;UI.abuf=256;UI.hq=false;for(const t of S.tracks)t.arm=false;restartAudio(true);ensureCtx();await ctx.resume();await w(400);
const t=S.tracks.find(t=>t.name==='Lead');t.arm=true;changed(true);syncGraph();try{ltSoon(20)}catch(e){}await w(1500);
await ctx.audioWorklet.addModule(URL.createObjectURL(new Blob([AE2.src],{type:'text/javascript'})));
const N=NODES.get(t.id);const tap=new AudioWorkletNode(ctx,'lt1-tap');const z=ctx.createGain();z.gain.value=0;N.in.connect(tap);tap.connect(z);z.connect(ctx.destination);
AE2.tap=tap;AE2.res=[];tap.port.onmessage=e=>{AE2.cur.f=e.data.f;AE2.cur.q=e.data.q;AE2.res.push(AE2.cur)};
window.addEventListener('keydown',e=>{if(!AE2.on||e.repeat)return;const o=ctx.getOutputTimestamp();AE2.cur={ev:e.timeStamp,h:performance.now(),ct:ctx.currentTime,oc:o.contextTime,op:o.performanceTime,sr:ctx.sampleRate};AE2.tap.port.postMessage(1)},true);
await w(800);AE2.on=1;return {rq:ctx.renderQuantumSize,base:+(ctx.baseLatency*1000).toFixed(2),mode:typeof LT==='object'?LT.cur:'(none)'}})()"""
info=al.run(SETUP%json.dumps(TAP))
for i in range(N):
    al.page.keyboard.down('z');al.page.wait_for_timeout(150);al.page.keyboard.up('z');al.page.wait_for_timeout(200)
r=al.run("""(()=>{AE2.on=0;return AE2.res.map(c=>{const ts=c.f/c.sr;const heard=c.op+(ts-c.oc)*1000;return{input:c.h-c.ev,sched:(ts-c.ct)*1000,ahead:(c.ct-c.oc)*1000-(c.h-c.op),total:heard-c.ev}})})()""")
info2=al.run("({rq:ctx.renderQuantumSize,mode:typeof LT==='object'?LT.cur:'(none)'})")
def s(k):
    v=[x[k] for x in r];return {'med':round(st.median(v),2),'min':round(min(v),2),'max':round(max(v),2)} if v else None
row={'label':LABEL,'version':al.version,'case':'idle, Lead armed, Auto 256','n':len(r),**info,'after':info2,'input':s('input'),'sched':s('sched'),'ahead':s('ahead'),'total':s('total')}
print(json.dumps(row),flush=True)
P=os.path.join(HERE,'lt1_measure_result.json')
try:rows=json.load(open(P))
except Exception:rows=[]
rows.append(row);json.dump(rows,open(P,'w'),indent=1)
al.stop()
