"""Emit (v0.174): offline render checks. python3 tools/engine-tests/emit.py [index.html] [shots dir]"""
import sys,os,numpy as np
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','remake'))
from alab import AudioLab
al=AudioLab(sys.argv[1] if len(sys.argv)>1 else 'index.html');al.start()
print('ver',al.version,'errors after load',al.errors)
rec={'bpm':120,'tracks':[{'name':'E','preset':'emit','clips':[{'start':0,'len':16,'notes':[{'p':60,'s':0,'l':4,'v':.9},{'p':67,'s':4,'l':2,'v':.7},{'p':55,'s':8,'l':3,'v':.8}]}]}]}
al.build(rec)
def rms(x): return float(np.sqrt((x**2).mean()))
def db(v): return 20*np.log10(max(v,1e-9))
x1,sr=al.render(b0=0,b1=20);x2,_=al.render(b0=0,b1=20)
print('default: rms %.4f (%.1f dB) peak %.3f nan %s equal %s maxdiff %g'%(rms(x1),db(rms(x1)),np.abs(x1).max(),bool(np.isnan(x1).any()),bool(np.array_equal(x1,x2)),float(np.abs(x1-x2).max())))
seg=lambda a,b:rms(x1[:,int(a*sr):int(b*sr)])
print('  level per second:',' '.join('%.3f'%seg(i,i+1) for i in range(10)))
print('  left/right rms %.4f %.4f'%(rms(x1[0]),rms(x1[1])))
keys=al.run("Object.keys(EMPRE).join(',')").split(',')
for k in keys:
    al.run("(()=>{const I=S.tracks[0].inst;Object.assign(I,JSON.parse(JSON.stringify(emParams('%s'))),{ipk:'%s'});changed(false);return 1})()"%(k,k))
    a,_=al.render(b0=0,b1=20);b,_=al.render(b0=0,b1=20)
    print('%-8s rms %.4f (%6.1f dB) peak %.3f nan %s equal %s tail(last s) %.5f'%(k,rms(a),db(rms(a)),np.abs(a).max(),bool(np.isnan(a).any()),bool(np.array_equal(a,b)),rms(a[:,-sr:])))
# another seed gives another result, the same seed the same
al.run("(()=>{const I=S.tracks[0].inst;Object.assign(I,JSON.parse(JSON.stringify(emParams('spin'))),{ipk:'spin'});changed(false)})()")
a,_=al.render(b0=0,b1=8);al.run("S.tracks[0].inst.seed=2;changed(false)");b,_=al.render(b0=0,b1=8);al.run("S.tracks[0].inst.seed=1;changed(false)");c,_=al.render(b0=0,b1=8)
print('seed 1 twice equal',bool(np.array_equal(a,c)),'seed 2 differs',not np.array_equal(a,b))
# keys change pitch: an octave up moves the spectrum up
def cen(x):
    n=min(x.shape[1],sr);X=np.abs(np.fft.rfft(x[0][:n]*np.hanning(n)));f=np.fft.rfftfreq(n,1/sr);return float((X*f).sum()/X.sum())
al.run("(()=>{const I=S.tracks[0].inst;I.fw1=8;I.frc1=0;I.ma1=0;S.tracks[0].clips[0].notes=[{p:60,s:0,l:4,v:.9}];changed(false)})()");lo,_=al.render(b0=0,b1=4)
al.run("S.tracks[0].clips[0].notes[0].p=72;changed(false)");hi,_=al.render(b0=0,b1=4)
al.run("S.tracks[0].inst.kf=false;changed(false)");same,_=al.render(b0=0,b1=4)
print('centre Hz: C3 %.0f, C4 %.0f, C4 with keys off %.0f'%(cen(lo),cen(hi),cen(same)))
# cost: the heaviest case (two emitters, 48 grains each, three notes)
import time
al.run("(()=>{const I=S.tracks[0].inst;Object.assign(I,JSON.parse(JSON.stringify(emParams('duo'))),{grn1:48,grn2:48,rate1:30,rate2:30,life1:3,life2:3,kf:true});S.tracks[0].clips[0].notes=[{p:60,s:0,l:8,v:.9},{p:64,s:0,l:8,v:.9},{p:67,s:0,l:8,v:.9}];changed(false)})()")
t0=time.time();h,_=al.render(b0=0,b1=8);dt=time.time()-t0
print('heavy case: %.1f s of sound in %.2f s (includes the app\'s own render overhead), rms %.4f peak %.3f'%(h.shape[1]/sr,dt,rms(h),np.abs(h).max()))
print('errors',al.errors);al.stop()
# the demo must be unchanged
al=AudioLab(sys.argv[1] if len(sys.argv)>1 else 'index.html');al.start()
import json;al.tracks=json.loads(al.run("JSON.stringify(Object.fromEntries(S.tracks.map(t=>[t.name,t.id])))"))
for nm in ('Kick','Bass'):
    x,sr=al.render(b0=64,b1=96,only=nm);print('Fractals %s %.5f dB'%(nm,db(rms(x))))
print('errors',al.errors);al.stop()
