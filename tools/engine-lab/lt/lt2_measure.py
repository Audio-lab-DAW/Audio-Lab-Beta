"""Task LT-2: the played track and delay compensation, before and after, on any index.html (the Fractals remake v6).
 A) the delay the engine applies to the armed Lead (its N.pdc delay), as built and with a resonance suppressor on the Bass (52 ms)
 B) key press to the first sample after the Lead's compensation delay (a tap on its utility input), with the suppressor on the Bass
 C) recording: the song plays with the suppressor on the Bass, notes are pressed on the armed Lead; each recorded note's position is
    compared with the song position that was coming out of the speakers at the moment of the press (from getOutputTimestamp and the
    compensation the graph applies): the error is how far the take lands from what was heard.
Run: python3 tools/engine-lab/lt/lt2_measure.py <index.html> <label>   (appends to lt2_measure_result.json)"""
import sys,os,json,statistics as st
HERE=os.path.dirname(os.path.abspath(__file__));sys.path.insert(0,os.path.join(HERE,'../ae2'))
import common
from alab import AudioLab
IDX=sys.argv[1];LABEL=sys.argv[2]
al=AudioLab(IDX).start();common.fractals(al)
row={'label':LABEL,'version':al.version}
# A
row['A']=al.run("""(async()=>{const w=ms=>new Promise(r=>setTimeout(r,ms));UI.buf=256;UI.ltPlayBuf=0;restartAudio(true);ensureCtx();await ctx.resume();const sr=ctx.sampleRate;
 for(const t of S.tracks)t.arm=false;const lead=S.tracks.find(t=>t.name==='Lead');lead.arm=true;changed(true);syncGraph();await w(500);
 const d=()=>+(NODES.get(lead.id).pdc.delayTime.value*1000).toFixed(2);const o={target_ms:+((CPU.pdc||0)*1000).toFixed(2),lead_ms:d()};
 const b=S.tracks.find(t=>t.name==='Bass');const f=mkFx('reson');b.fx.push(f);changed(true);syncGraph();await w(500);o.reson_target_ms=+((CPU.pdc||0)*1000).toFixed(2);o.reson_lead_ms=d();
 lead.arm=false;changed(true);syncGraph();await w(500);o.reson_lead_disarmed_ms=d();lead.arm=true;changed(true);syncGraph();await w(500);return o})()""")
print(json.dumps(row['A']),flush=True)
# B: two taps, on the Lead's input (before its devices and the compensation delay) and after the compensation delay; presses 1.2 s apart
TAP="""class T extends AudioWorkletProcessor{constructor(){super();this.arm=0;this.port.onmessage=e=>{this.arm=e.data}}process(I){const x=I[0]&&I[0][0];if(this.arm&&x){for(let i=0;i<x.length;i++)if(Math.abs(x[i])>1e-4){this.port.postMessage({f:currentFrame+i});this.arm=0;break}}return true}}registerProcessor('lt2-tap',T)"""
al.run("""(async()=>{const w=ms=>new Promise(r=>setTimeout(r,ms));window.LT2={src:%s};await ctx.audioWorklet.addModule(URL.createObjectURL(new Blob([LT2.src],{type:'text/javascript'})));
 const lead=S.tracks.find(t=>t.name==='Lead'),N=NODES.get(lead.id);LT2.res=[];LT2.taps={};
 for(const[k,src]of[['pre',N.in],['post',N.pdc]]){const tap=new AudioWorkletNode(ctx,'lt2-tap'),z=ctx.createGain();z.gain.value=0;src.connect(tap);tap.connect(z);z.connect(ctx.destination);LT2.taps[k]=tap;tap.port.onmessage=e=>{if(LT2.cur)LT2.cur[k]=e.data.f}}
 window.addEventListener('keydown',e=>{if(!LT2.on||e.repeat)return;const o=ctx.getOutputTimestamp();LT2.cur={ev:e.timeStamp,oc:o.contextTime,op:o.performanceTime,sr:ctx.sampleRate};LT2.res.push(LT2.cur);for(const k in LT2.taps)LT2.taps[k].port.postMessage(1)},true);await w(800);LT2.on=1;return 1})()"""%json.dumps(TAP))
for i in range(10):
    al.page.keyboard.down('z');al.page.wait_for_timeout(100);al.page.keyboard.up('z');al.page.wait_for_timeout(1100)
r=al.run("(()=>{LT2.on=0;for(const k in LT2.taps)try{LT2.taps[k].disconnect()}catch(e){}return LT2.res.filter(c=>c.pre!=null&&c.post!=null).map(c=>({pre:c.op+(c.pre/c.sr-c.oc)*1000-c.ev,post:c.op+(c.post/c.sr-c.oc)*1000-c.ev,comp:(c.post-c.pre)/c.sr*1000}))})()")
def S_(k):
    v=[x[k] for x in r];return {'med':round(st.median(v),2),'min':round(min(v),2),'max':round(max(v),2)} if v else None
row['B']={'n':len(r),'key_to_track_input_ms':S_('pre'),'key_to_after_compensation_ms':S_('post'),'compensation_on_the_played_note_ms':S_('comp')}
print(json.dumps(row['B']),flush=True)
# C
row['C']=al.run("""(async()=>{const w=ms=>new Promise(r=>setTimeout(r,ms));S.loop=false;UI.recOff=0;UI.countIn=0;UI.metro=false;const lead=S.tracks.find(t=>t.name==='Lead');
 const n0=lead.clips.length;pos=(81-1)*4;recStart();await w(2500);const P=[];
 for(let i=0;i<10;i++){await w(180+Math.random()*120);const pn=performance.now(),o=ctx.getOutputTimestamp(),spk=o.contextTime+(pn-o.performanceTime)/1000,tgt=CPU.pdc||0;
  const heard=beatOf(secOf(play.b0)+(spk-tgt-play.t0));noteOn(60+i%5,.8,'lt2k'+i);P.push(heard);await w(90);noteOff('lt2k'+i)}
 await w(300);stop();await w(400);const c=lead.clips.slice(n0).find(c=>/take/.test(c.name));if(!c)return{err:'no take',n:lead.clips.length-n0};
 const got=c.notes.map(n=>c.start+n.s).sort((a,b)=>a-b);const spb=60/S.bpm;const e=got.map((g,i)=>(g-P[i])*spb*1000);
 return{n:e.length,err_ms:e.map(x=>+x.toFixed(2)),target_ms:+((CPU.pdc||0)*1000).toFixed(2)}})()""")
c=row['C']
if c.get('err_ms'):
    e=c['err_ms'];c['median_ms']=round(st.median(e),2);c['worst_abs_ms']=round(max(abs(x) for x in e),2)
print(json.dumps({k:v for k,v in c.items() if k!='err_ms'}),flush=True)
P=os.path.join(HERE,'lt2_measure_result.json')
try:rows=json.load(open(P))
except Exception:rows=[]
rows.append(row);json.dump(rows,open(P,'w'),indent=1)
print('errors',al.errors[:3])
al.stop()
