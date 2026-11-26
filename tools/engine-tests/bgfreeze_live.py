"""Background freeze (v0.201, task E part 2), live: clips play from background recordings, a knob turn thaws the track at once and the
sound carries on without a gap or a click; an effect knob does not thaw (effects stay live); arming and playing keys thaw.
python3 tools/engine-tests/bgfreeze_live.py [index.html]"""
import sys,os,json,time
import numpy as np
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','remake'))
from alab import AudioLab
al=AudioLab(sys.argv[1] if len(sys.argv)>1 else 'index.html');al.start()
print('version',al.version,'errors after load',al.errors)
notes=[{'p':48+(k%5)*3,'s':k*.5,'l':1.5,'v':.8} for k in range(16)]
rec={'bpm':120,'tracks':[{'name':'Sel','preset':'saw','clips':[]},
  {'name':'VFM','preset':'vfm','fx':[{'type':'eq'}],'clips':[{'start':4,'len':8,'notes':notes},{'start':16,'len':8,'notes':notes}]},
  {'name':'Orb','preset':'orb','clips':[{'start':4,'len':8,'notes':notes},{'start':16,'len':8,'notes':notes}]},
  {'name':'Acid','preset':'acid','clips':[{'start':4,'len':8,'notes':notes}]}]}
al.build(rec)
al.run("(async()=>{ensureCtx();await ctx.resume();selT=S.tracks[0].id;renderHeaders();return 1})()")
t0=time.time()
while time.time()-t0<40:
    n=al.run("BGF.cache.size");ok=al.run("JSON.stringify([...BGF.ok])")
    if n>=5:break
    time.sleep(1)
print('after %.1f s: %d clips recorded, tracks that may freeze: %s'%(time.time()-t0,n,ok))
print('marks on headers while stopped:',al.run("[...hdrin.querySelectorAll('.hdr .bgfm')].map(e=>e.closest('.hdr').querySelector('.nm').textContent).join(', ')"))
# a recorder on the VFM track's output (after its fader)
al.run("""(async()=>{const src=`registerProcessor('tap-rec',class extends AudioWorkletProcessor{constructor(){super();this.b=new Float32Array(sampleRate*14);this.n=0;this.port.onmessage=()=>this.port.postMessage({b:this.b.slice(0,this.n),n:this.n})}process(i){const x=i[0]&&i[0][0];if(x&&this.n+x.length<=this.b.length){this.b.set(x,this.n)}this.n+=128;return true}})`;
 await ctx.audioWorklet.addModule(URL.createObjectURL(new Blob([src],{type:'text/javascript'})));const t=S.tracks.find(q=>q.name==='VFM'),N=NODES.get(t.id);const r=new AudioWorkletNode(ctx,'tap-rec',{channelCount:1,channelCountMode:'explicit'});const z=ctx.createGain();z.gain.value=0;N.pan.connect(r);r.connect(z);z.connect(ctx.destination);window.__tap=r;return 1})()""")
al.run("(()=>{pos=0;window.__t0=ctx.currentTime;start();window.__ts=play.t0;window.__tapT=ctx.currentTime;return 1})()")
time.sleep(4.2)  # beat ~8: inside the first VFM clip
st=json.loads(al.run("JSON.stringify({act:[...BGF.act].map(I=>I.bgf.t.name+'@'+I.bgf.c.start),played:BGF.st.played,thaw:BGF.st.thaw,beat:curBeat(),marks:[...hdrin.querySelectorAll('.hdr .bgfm')].map(e=>e.closest('.hdr').querySelector('.nm').textContent)})"))
print('playing at beat %.2f: from recordings: %s; marks: %s'%(st['beat'],st['act'],st['marks']))
# an effect knob on the frozen track: no thaw
al.run("(()=>{const t=S.tracks.find(q=>q.name==='VFM');t.fx[0].p.out=(t.fx[0].p.out||0)+1;changed(false);return 1})()");time.sleep(.3)
print('effect knob turned: thaws so far',al.run("BGF.st.thaw"),'(should be 0)')
# an instrument knob: thaw within a frame
r=json.loads(al.run("""(()=>{const t=S.tracks.find(q=>q.name==='VFM'),I=t.inst;const k=Object.keys(I).find(k=>typeof I[k]==='number'&&k!=='gain'&&!/^_/.test(k)&&I[k]>0);window.__k=k;window.__kt=performance.now();window.__kc=ctx.currentTime;I[k]=I[k]*1.02;return JSON.stringify({k,ct:ctx.currentTime})})()"""))
t1=time.time()
while time.time()-t1<1:
    th=al.run("BGF.st.thaw")
    if th>0:break
    time.sleep(.005)
d=json.loads(al.run("JSON.stringify({thaw:BGF.st.thaw,last:BGF.lastThaw,ms:BGF.lastThaw?BGF.lastThaw.at-__kt:null,chsT:CHS.T,picked:CHS.lastN,live:[...INST.entries()].filter(([k,I])=>k.startsWith(S.tracks.find(q=>q.name==='VFM').clips[0].id+':')).map(([k,I])=>!!I.bgf)})"))
print('instrument knob (%s) turned: thawed after %.1f ms (%s); notes picked up live: %s; that clip now live: %s'%(r['k'],d['ms'] or -1,d['last'] and d['last']['why'],d['picked'],[not b for b in d['live']]))
time.sleep(1.5)
al.run("(()=>{__tap.port.onmessage=e=>{window.__rec=e.data};__tap.port.postMessage(1);return 1})()");time.sleep(.5)
x=np.array(al.page.evaluate("()=>Array.from(window.__rec.b)"),dtype=np.float64);sr=al.run("ctx.sampleRate")
T=int(round((d['chsT']-al.run("__tapT"))*sr))
w=int(sr*.005);seg=lambda a,b:x[max(0,a):b]
rms=lambda v:float(np.sqrt((v**2).mean())) if len(v) else 0
before=rms(seg(T-int(sr*.1),T));lo=min(rms(seg(T+i*w,T+(i+1)*w)) for i in range(-4,8))
jump=np.abs(np.diff(x));jt=float(jump[max(0,T-w):T+2*w].max());jo=float(np.percentile(jump[int(sr*2.1):T-int(sr*.2)],99.9))
print('around the thaw: level in the 100 ms before %.4f, lowest 5 ms level from -20 to +40 ms %.4f (%.1f dB under), largest step from sample to sample %.4f against %.4f (99.9 %% of the frozen part before)'%(before,lo,20*np.log10(max(lo,1e-9)/max(before,1e-9)),jt,jo))
al.run("stop();1");time.sleep(.5)
# arming and keys thaw (after the changed track has been still for 8 s and is recorded again)
t2=time.time()
while time.time()-t2<30:
    if al.run("BGF.ok.size")>=3 and al.run("(()=>{const t=S.tracks.find(q=>q.name==='VFM'),st=BGF.tsig.get(t.id);return t.clips.every(c=>!!BGF.cache.get(bgfKey(st.s,c)))})()"):break
    time.sleep(1)
al.run("(()=>{pos=12;start();return 1})()");time.sleep(3.6)
a0=al.run("BGF.st.thaw");act=al.run("[...BGF.act].map(I=>I.bgf.t.name).join(',')")
al.run("(()=>{const t=S.tracks.find(q=>q.name==='Orb');const h=voiceOn(t,60,.8);setTimeout(()=>h&&h.off(),200);return 1})()");time.sleep(.3)
a1=al.run("BGF.st.thaw");print('playing from recordings: %s; a key played on Orb thawed it: %s (%s)'%(act,a1>a0,al.run("JSON.stringify(BGF.lastThaw&&BGF.lastThaw.why)")))
al.run("(()=>{const t=S.tracks.find(q=>q.name==='VFM');t.arm=true;return 1})()");time.sleep(.3)
a2=al.run("BGF.st.thaw");print('arming VFM thawed it: %s (%s)'%(a2>a1,al.run("JSON.stringify(BGF.lastThaw&&BGF.lastThaw.why)")))
al.run("stop();1")
print('stats',al.run("JSON.stringify(BGF.st)"),'memory %.1f MB'%(al.run("BGF.bytes")/1048576))
print('errors',al.errors)
al.stop()
