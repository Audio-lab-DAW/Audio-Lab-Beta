"""Task LT-2 (lane J): the played track skips delay compensation (L4); recorded notes placed by the compensated clock.
Edit script with unique, asserted anchors; safe to re-run on a fresh index.html (does nothing when the step is already in). Needs LT-1.
Run from the repository root: python3 tools/engine-lab/lt/lt_2.py"""
import os,sys
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'../../..'))
P=os.path.join(ROOT,'index.html')
s=open(P,encoding='utf-8').read()
if 'task LT-2 (lane J)' in s:
    print('LT-2 already in index.html');sys.exit(0)
assert 'task LT-1 (lane J)' in s,'LT-1 first'
def rep(a,b):
    global s
    n=s.count(a);assert n==1,(n,a[:90]);s=s.replace(a,b)

# 1. pdcMap (lane K's): a live flag and one hook that only lowers the played tracks' entries; the exporter's call is unchanged
rep("function pdcMap(sr){const M=new Map();M.target=0;","function pdcMap(sr,live){const M=new Map();M.target=0;")
rep("if(M.target>0)for(const t of src)M.set(t.id,Math.min(sr,M.target-path.get(t.id)));return M}",
    "if(M.target>0)for(const t of src)M.set(t.id,Math.min(sr,M.target-path.get(t.id)));if(live)try{LT_HOOKS.pdcLive(M,sr)}catch(e){}return M}")
# 2. the live call in syncGraph passes live
rep("PDC=pdcMap(ctx.sampleRate);CPU.pdc=PDC.target/ctx.sampleRate;","PDC=pdcMap(ctx.sampleRate,1);CPU.pdc=PDC.target/ctx.sampleRate;")
# 3. the take (lane C's): notes placed by the compensated clock, beside UI.recOff
rep("s:Math.max(0,n.s-a-(UI.recOff||0)/1000*S.bpm/60),l:n.l,v:n.v}","s:Math.max(0,n.s-a-((UI.recOff||0)/1000+ltRecSec(t))*S.bpm/60),l:n.l,v:n.v}")
# 4. LT-1's own switch to the mixing buffer after dropouts at the playing buffer restarts the engine, and a restart ends a recording
#    (restartAudio calls stop, stop calls recStop): while recording it now waits; LT.heavy is set, so the next Play starts on the mixing buffer.
#    Found by the second LT-2 run (27 Nov, 23:00 UTC): with real dropouts a take was cut after about a second.
rep("setTimeout(()=>{if(!play.on||LT.cur!=='play')return;LT.forceMix=true;",
    "setTimeout(()=>{if(!play.on||LT.cur!=='play'||REC.on)return;LT.forceMix=true;")

JS=r"""/* ===== lane J, task LT-2 (lane J): the played track skips delay compensation (L4). docs/latency-build.md =====
   Delay compensation holds every track back to the slowest path (6 ms in Fractals, 52 ms with a resonance suppressor). The track you play
   (armed, or the selected one while the computer keyboard plays) now skips that hold while you play, like reduced latency when monitoring
   in other DAWs: its own devices' latency stays, the rest of the song keeps its compensation (CPU.pdc unchanged). The switch ramps the delay
   (no click). Recorded notes are placed by the compensated clock: what you heard when you pressed is the song CPU.pdc earlier than the
   output clock says, so the take moves earlier by it (ltRecSec), on top of the Recording latency offset; the press itself is read from the
   output clock at the key event, not from the display clock. Exports use pdcMap without the live
   flag, so they are untouched. Lane K owns pdcMap; this hook only lowers the played tracks' entries, so AE3's returns and sends compose. */
LT.pdcSig='';LT.pdcOut=new Map();
LT_HOOKS.pdcLive=function(M,sr){let L=[];if(UI.ltPdc!==false)try{L=liveTracks()}catch(e){}const out=new Map();
 for(const t of L){const d=M.get(t.id)||0;if(d>0){out.set(t.id,d);M.set(t.id,0)}}
 const ids=new Set([...LT.pdcOut.keys(),...out.keys()]);LT.pdcOut=out;LT.pdcSig=L.map(t=>t.id).join(',');
 if(ctx&&sr===ctx.sampleRate)for(const id of ids){const N=NODES.get(id);if(!N||!N.pdc)continue;const d=(M.get(id)||0)/sr;if(d===N.pdcV)continue;
  const p=N.pdc.delayTime,t0=ctx.currentTime,dur=Math.min(.25,Math.max(.03,Math.abs(d-(N.pdcV||0))*4));N.pdcV=d;
  try{p.cancelScheduledValues(t0);p.setValueAtTime(p.value,t0);p.linearRampToValueAtTime(d,t0+dur)}catch(e){p.value=d}}};
/* what the played tracks skip, for read-outs (lanes E, K): [{id,name,ms}] */
LT_HOOKS.pdcOut=()=>[...LT.pdcOut].map(([id,n])=>{const t=S.tracks.find(x=>x.id===id);return{id,name:t?t.name:'',ms:ctx?n/ctx.sampleRate*1000:0}});
function ltRecSec(t){try{if(UI.pdc===false||!t||t.kind!=='inst')return 0;return CPU.pdc||0}catch(e){return 0}}
/* arming, the computer keyboard and the selected track change who plays: the graph is brought up to date after the click or key */
function ltPdcEval(){clearTimeout(ltPdcEval.t);ltPdcEval.t=setTimeout(()=>{if(!ctx||UI.pdc===false||!(CPU.pdc>0))return;let sig='';try{sig=(UI.ltPdc===false?[]:liveTracks()).map(t=>t.id).join(',')}catch(e){}if(sig!==LT.pdcSig)syncGraph()},120)}
document.addEventListener('pointerup',ltPdcEval,true);document.addEventListener('keyup',ltPdcEval,true);
/* the press, placed exactly: the take used the display clock (smoothed for drawing, a frame or more behind); the note's position is moved
   to what the speakers played at the moment of the press (the key event's own time when a key started it), from getOutputTimestamp */
document.addEventListener('keydown',e=>{if(!e.repeat)LT.kdT=e.timeStamp},true);
{const _n=noteOn;noteOn=function(p,v,key){const had=LIVE.has(key),now=performance.now(),T=DISP_T;let o=null;try{if(!had&&play.on&&ctx&&ctx.getOutputTimestamp)o=ctx.getOutputTimestamp()}catch(e){}
  const r=_n.apply(this,arguments);/* the clock is read before the voice starts: starting a voice can take a few ms */
  try{const L=!had&&LIVE.get(key);if(L&&L.b!=null&&play.on&&!play.counting&&o&&o.contextTime>0&&o.performanceTime>0){const T0=T!=null?T:ctx.currentTime,
    pn=LT.kdT&&now-LT.kdT<40&&LT.kdT<=now?LT.kdT:now,spk=o.contextTime+(pn-o.performanceTime)/1000,b=beatOf(secOf(L.b)+(spk-T0));
    if(isFinite(b)&&Math.abs(secOf(b)-secOf(L.b))<.25)L.b=b}}catch(e){}return r}}
/* ===== end of lane J LT-2 ===== */
"""
rep("/* ===== end of lane J LT-1 ===== */\n","/* ===== end of lane J LT-1 ===== */\n"+JS)
open(P,'w',encoding='utf-8').write(s)
print('LT-2 applied')
