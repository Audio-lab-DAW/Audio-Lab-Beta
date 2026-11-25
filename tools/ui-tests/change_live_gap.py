"""Change with live browsing (v0.183): is there a gap or a click when the instrument is swapped while long notes sound?
The track's output is recorded across each swap. python3 tools/ui-tests/change_live_gap.py [index.html]"""
import sys,os,json
import numpy as np
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','remake'))
from alab import AudioLab
al=AudioLab(sys.argv[1] if len(sys.argv)>1 else 'index.html');al.start()
notes=[{'p':p,'s':i*8,'l':7.95,'v':.8} for i in range(8) for p in (48,55,60)]
al.build({'bpm':120,'tracks':[{'name':'Pad','preset':'pad','clips':[{'start':0,'len':64,'notes':notes}]}]})
R=al.run;W=al.page.wait_for_timeout
R("(()=>{const t=S.tracks[0];selT=t.id;changed(true);renderFx();ensureCtx();syncGraph();const N=NODES.get(t.id);N.__a=ctx.createAnalyser();N.__a.fftSize=32768;N.pan.connect(N.__a);openBrowser(t);return 1})()");W(700)
R("pos=0;start();1");W(2500)
print('%-8s %-8s | level before, dB | lowest 5 ms block around the swap, dB | level after, dB | biggest step around the swap / before / after'%('from','to'))
prev='pad'
for k in ('strings','sub','keys','wtab','saw','venom','orb','plant','reese','acid','sampler','pad'):
    ts=R("(()=>{document.querySelector('#ibPlane .ibc[data-k=%s]').click();return ctx.currentTime})()"%k);W(430)
    d=json.loads(R("(()=>{const a=NODES.get(S.tracks[0].id).__a,b=new Float32Array(32768);a.getFloatTimeDomainData(b);return JSON.stringify({t:ctx.currentTime,sr:ctx.sampleRate,x:Array.from(b,v=>+v.toFixed(5))})})()"))
    x=np.array(d['x']);sr=d['sr'];i0=int(len(x)-(d['t']-ts)*sr);w=int(sr*.005)
    rms=lambda a:20*np.log10(np.sqrt(np.mean(a*a))+1e-9)
    blocks=[rms(x[i:i+w]) for i in range(max(0,i0-int(.02*sr)),min(len(x)-w,i0+int(.12*sr)),w//2)]
    st=lambda a:float(np.max(np.abs(np.diff(a)))) if len(a)>1 else 0
    print('%-8s %-8s | %6.1f | %6.1f | %6.1f | %.3f / %.3f / %.3f | holds %s'%(prev,k,rms(x[max(0,i0-int(.15*sr)):i0-int(.02*sr)]),min(blocks),rms(x[i0+int(.15*sr):]),st(x[i0-int(.02*sr):i0+int(.1*sr)]),st(x[:i0-int(.02*sr)]),st(x[i0+int(.15*sr):]),R("S.tracks[0].inst.preset")))
    prev=k;W(1500)
# Escape while playing: back to the pad it started with
R("document.querySelector('#ibPlane .ibc[data-k=saw]').click();1");W(800);al.page.keyboard.press('Escape');W(900)
print('Escape while playing: holds',R("S.tracks[0].inst.preset"),'| playing',R("play.on"),'| level',R("(()=>{const a=NODES.get(S.tracks[0].id).__a,b=new Float32Array(4096);a.getFloatTimeDomainData(b);let s=0;for(const v of b)s+=v*v;return (10*Math.log10(s/4096+1e-12)).toFixed(1)})()"))
print('errors',al.errors);al.stop()
