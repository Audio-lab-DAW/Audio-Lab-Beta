"""Vector Grain (v0.175): offline render checks. python3 tools/engine-tests/vector_grain.py [index.html]"""
import sys,os,time,json,numpy as np
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','remake'))
from alab import AudioLab
al=AudioLab(sys.argv[1] if len(sys.argv)>1 else 'index.html');al.start()
print('ver',al.version,'errors after load',al.errors)
rec={'bpm':120,'tracks':[{'name':'V','preset':'vgrain','clips':[{'start':0,'len':16,'notes':[{'p':60,'s':0,'l':4,'v':.9},{'p':67,'s':4,'l':2,'v':.7},{'p':55,'s':8,'l':3,'v':.8},{'p':62,'s':8,'l':3,'v':.8}]}]}]}
al.build(rec)
def rms(x): return float(np.sqrt((x**2).mean()))
def db(v): return 20*np.log10(max(v,1e-9))
def jump(x): return float(np.abs(np.diff(x,axis=1)).max())
setp=lambda k:al.run("(()=>{const I=S.tracks[0].inst;Object.assign(I,JSON.parse(JSON.stringify(vgParams('%s'))),{ipk:'%s'});changed(false);return 1})()"%(k,k))
keys=al.run("Object.keys(VGPRE).join(',')").split(',')
for k in keys:
    setp(k);a,sr=al.render(b0=0,b1=24);b,_=al.render(b0=0,b1=24)
    print('%-8s rms %.4f (%6.1f dB) peak %.3f nan %s equal %s biggest step %.3f L/R %.3f %.3f tail(last s) %.5f'%(k,rms(a),db(rms(a)),np.abs(a).max(),bool(np.isnan(a).any()),bool(np.array_equal(a,b)),jump(a),rms(a[0]),rms(a[1]),rms(a[:,-sr:])))
setp('swarm');a,_=al.render(b0=0,b1=8);al.run("S.tracks[0].inst.seed=2;changed(false)");b,_=al.render(b0=0,b1=8);al.run("S.tracks[0].inst.seed=1;changed(false)");c,_=al.render(b0=0,b1=8)
print('seed 1 twice equal',bool(np.array_equal(a,c)),'seed 2 differs',not np.array_equal(a,b))
# the note start inside an audio block must not matter: shift the clip by a fraction of a beat and compare the shifted sound
al.run("S.tracks[0].clips[0].notes=[{p:60,s:0,l:4,v:.9}];changed(false)");a,_=al.render(b0=0,b1=8)
al.run("S.tracks[0].clips[0].notes=[{p:60,s:0.0133,l:4,v:.9}];changed(false)");b,_=al.render(b0=0,b1=8)
i0=int(np.argmax(np.abs(a[0])>1e-7));i1=int(np.argmax(np.abs(b[0])>1e-7));n=min(a.shape[1]-i0,b.shape[1]-i1)-10
print('start moved by %d samples; same sound after shifting: maxdiff %g'%(i1-i0,float(np.abs(a[:,i0:i0+n]-b[:,i1:i1+n]).max())))
# keys change pitch
def cen(x):
    n=min(x.shape[1],sr);X=np.abs(np.fft.rfft(x[0][:n]*np.hanning(n)));f=np.fft.rfftfreq(n,1/sr);return float((X*f).sum()/X.sum())
setp('frozen');al.run("S.tracks[0].clips[0].notes=[{p:60,s:0,l:4,v:.9}];changed(false)");lo,_=al.render(b0=0,b1=4)
al.run("S.tracks[0].clips[0].notes[0].p=72;changed(false)");hi,_=al.render(b0=0,b1=4)
al.run("S.tracks[0].inst.kf=false;changed(false)");same,_=al.render(b0=0,b1=4)
print('centre Hz: C3 %.0f, C4 %.0f, C4 with keys off %.0f'%(cen(lo),cen(hi),cen(same)))
# what the vectors do: X on pan gives a wide picture, X off gives the same left and right
setp('orbit');a,_=al.render(b0=0,b1=4);al.run("S.tracks[0].inst.ax=0;changed(false)");b,_=al.render(b0=0,b1=4)
print('X on pan: left-right difference %.4f, with X at 0: %.6f'%(rms(a[0]-a[1]),rms(b[0]-b[1])))
al.run("S.tracks[0].inst.spd=0;changed(false)");c,_=al.render(b0=0,b1=4);al.run("S.tracks[0].inst.rev=true;changed(false)");d,_=al.render(b0=0,b1=4)
print('reverse changes the sound',not np.array_equal(c,d),'rms %.4f %.4f'%(rms(c),rms(d)))
# one particle per key: 20 keys at once (more than 16) must not break
setp('keys');al.run("S.tracks[0].clips[0].notes=Array.from({length:20},(_,i)=>({p:48+i,s:i*.1,l:3,v:.7}));changed(false)");a,_=al.render(b0=0,b1=10)
print('20 keys, one particle each: rms %.4f peak %.3f nan %s biggest step %.3f'%(rms(a),np.abs(a).max(),bool(np.isnan(a).any()),jump(a)))
# cost: 16 grains, six notes
setp('swarm');al.run("S.tracks[0].inst.num=16;S.tracks[0].clips[0].notes=[48,52,55,60,64,67].map(p=>({p,s:0,l:8,v:.8}));changed(false)")
t0=time.time();h,_=al.render(b0=0,b1=8);dt=time.time()-t0
print('heavy case: %.1f s of sound in %.2f s, rms %.4f peak %.3f'%(h.shape[1]/sr,dt,rms(h),np.abs(h).max()))
print('errors',al.errors);al.stop()
al=AudioLab(sys.argv[1] if len(sys.argv)>1 else 'index.html');al.start()
al.tracks=json.loads(al.run("JSON.stringify(Object.fromEntries(S.tracks.map(t=>[t.name,t.id])))"))
for nm in ('Kick','Bass'):
    x,sr=al.render(b0=64,b1=96,only=nm);print('Fractals %s %.5f dB'%(nm,db(rms(x))))
print('errors',al.errors);al.stop()
