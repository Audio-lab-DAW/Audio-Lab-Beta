"""Background freeze (v0.201, task E part 2): the mix with clips played from background recordings against the mix played live.
python3 tools/engine-tests/bgfreeze_match.py [index.html]
For every instrument the background freeze may record, a 120 bpm song with two clips (one with a clip volume line), one track with
effects after it (they stay live) is rendered three ways by the app's own renderer (renderMix):
  A  as an export does (every note made live),
  B  every clip replaced by its background recording, rendered with the same block phase as A (the recording starts on a block edge as in A),
  C  every clip replaced by the recording exactly as live playback uses it (made from the clip start, started on the nearest sample).
B against A shows whether the recording is the same sound; C against A shows what block phase alone changes."""
import sys,os,json
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','remake'))
from alab import AudioLab
al=AudioLab(sys.argv[1] if len(sys.argv)>1 else 'index.html');al.start()
print('version',al.version,'errors after load',al.errors)
notes=[{'p':48,'s':0,'l':2,'v':.8},{'p':55,'s':0,'l':2,'v':.7},{'p':60,'s':1,'l':1.5,'v':.9},{'p':63,'s':2.5,'l':.5,'v':.6},{'p':67,'s':3,'l':.75,'v':.8},{'p':52,'s':4,'l':3,'v':.75},{'p':59,'s':5.5,'l':.5,'v':.7},{'p':64,'s':6,'l':1.5,'v':.85}]
JS=r"""(async(trs)=>{ensureCtx();const sr=48000,b0=4,b1=40,tail=4,rq=RQOK?(UI.rqOff||512):128;
 const mix=async()=>{const b=await renderMix(sr,b0,b1,tail,false,null,false);return[b.getChannelData(0).slice(),b.getChannelData(1).slice()]};
 const cmp=(A,B)=>{let m=0,e=0,s=0;for(let c=0;c<2;c++)for(let i=0;i<A[c].length;i++){const d=Math.abs(A[c][i]-B[c][i]);if(d>m)m=d;e+=d*d;s+=A[c][i]*A[c][i]}return{max:m,maxDb:m>0?+(20*Math.log10(m)).toFixed(1):null,relDb:e>0?+(10*Math.log10(e/s)).toFixed(1):null,same:m===0}};
 const A=await mix(),A2=await mix(),out={again:cmp(A,A2),tracks:[]};
 const T=new Map();for(const t of S.tracks){if(!t.inst)continue;const ok=bgfTrackOK(t)||t.id===selT;out.tracks.push({name:t.name,preset:t.inst.preset,ok});if(!ok)continue;
   for(const c of t.clips){if(!bgfClipOK(t,c))continue;const F=Math.round(secSpan(b0,c.start)*sr),pad=F%rq;const r1=await bgfRender(t,c,sr,pad),r0=await bgfRender(t,c,sr,0);T.set(c.id,{r1,r0,F,pad})}}
 const play=(which)=>(oc,t,c,tin,b)=>{const e=T.get(c.id);if(!e)return false;const r=which?e.r1:e.r0;if(!r.buf)return false;const g=oc.createGain();g.channelCount=2;g.channelCountMode='explicit';g.channelInterpretation='speakers';g.connect(tin);const s=oc.createBufferSource();s.buffer=r.buf;s.connect(g);s.start(which?(e.F-e.pad)/sr:e.F/sr);return true};
 BGF.tst=play(1);let B;try{B=await mix()}finally{BGF.tst=null}
 BGF.tst=play(0);let C;try{C=await mix()}finally{BGF.tst=null}
 out.B=cmp(A,B);out.C=cmp(A,C);out.clips=T.size;out.mono=[...T.values()].filter(e=>e.r0.mono).length;out.loud=[...T.values()].filter(e=>e.r0.loud).length;return JSON.stringify(out)})(%s)"""
presets=sys.argv[2].split(',') if len(sys.argv)>2 else ['emit','vgrain','vfm','orb','growl','wtab','sbass','bball','psyb','crk','venom','plant','plant0','acid','saw','square','bass','reese','strings','pluck','keys','sub','pad','kick','zsnare','zclap','zhat','ztom','sfx']
res={}
for pr0 in presets:
    pr=pr0.rstrip('0');ins={'space':0} if pr0.endswith('0') else {}
    rec={'bpm':120,'tracks':[{'name':'Sel','preset':'saw','clips':[]},{'name':pr,'preset':pr,'inst':ins,'clips':[{'start':8,'len':8,'notes':notes,'env':{'vol':[{'b':0,'v':.75},{'b':8,'v':.4}]}},{'start':24,'len':8,'notes':notes}]},
         {'name':pr+' fx','preset':pr,'inst':ins,'fx':[{'type':'tdelay'},{'type':'reverb'}],'clips':[{'start':16,'len':8,'notes':notes}]}]}
    if pr=='saw': rec['tracks'][1]['fx']=[{'type':'bnotes'}]
    al.build(rec);al.run("(()=>{selT=S.tracks[0].id;return 1})()")
    r=json.loads(al.run(JS.replace("(%s)","(null)")));res[pr0]=r
    print('%-7s clips %d (mono %d, still ringing %d)  A again: %s  B (same block phase): %s  C (as live): max %s dB, %s dB of the signal'%(pr0,r['clips'],r['mono'],r['loud'],'same' if r['again']['same'] else r['again'],'identical' if r['B']['same'] else 'max %s dB, %s dB rel'%(r['B']['maxDb'],r['B']['relDb']),r['C']['maxDb'],r['C']['relDb']),flush=True)
print('errors',al.errors)
al.stop()
