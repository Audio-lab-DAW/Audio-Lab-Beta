"""Vector Delay (v0.179): offline render checks. python3 tools/engine-tests/vector_delay.py [index.html]"""
import sys,os,time,json,numpy as np
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','remake'))
from alab import AudioLab
IDX=sys.argv[1] if len(sys.argv)>1 else 'index.html'
al=AudioLab(IDX);al.start()
print('ver',al.version,'errors after load',al.errors)
# a short pluck every two beats, then silence, so the repeats and the tail can be measured
notes=[{'p':60,'s':0,'l':.25,'v':.9},{'p':67,'s':2,'l':.25,'v':.8},{'p':63,'s':4,'l':.25,'v':.85},{'p':72,'s':6,'l':.25,'v':.8}]
rec={'bpm':120,'tracks':[{'name':'V','preset':'pluck','clips':[{'start':0,'len':32,'notes':notes}],'fx':[{'type':'vdelay','p':{}}]}]}
try: al.build(rec)
except Exception as e:
    rec['tracks'][0].pop('preset');al.build(rec)
print('instrument',al.run("S.tracks[0].inst.preset"),'fx',al.run("S.tracks[0].fx.map(f=>f.type).join()"))
def rms(x): return float(np.sqrt((x**2).mean()))
def db(v): return 20*np.log10(max(v,1e-9))
def jump(x): return float(np.abs(np.diff(x,axis=1)).max())
def cen(x,sr):
    X=np.abs(np.fft.rfft(x[0]*np.hanning(x.shape[1])));f=np.fft.rfftfreq(x.shape[1],1/sr);return float((X*f).sum()/max(X.sum(),1e-12))
setp=lambda k:al.run("(()=>{const f=S.tracks[0].fx[0];Object.assign(f.p,JSON.parse(JSON.stringify(FXPRE.vdelay['%s'][1])));f.p.pre='%s';changed(false);return 1})()"%(k,k))
setv=lambda js:al.run("(()=>{const p=S.tracks[0].fx[0].p;%s;changed(false);return 1})()"%js)
al.run("S.tracks[0].fx[0].on=false;changed(false)");dry,sr=al.render(b0=0,b1=24)
al.run("S.tracks[0].fx[0].on=true;changed(false)")
print('dry: rms %.4f (%.1f dB) peak %.3f, last 4 s %.6f'%(rms(dry),db(rms(dry)),np.abs(dry).max(),rms(dry[:,-4*sr:])))
keys=al.run("Object.keys(FXPRE.vdelay).join(',')").split(',')
for k in keys:
    setp(k);t0=time.time();a,sr=al.render(b0=0,b1=24);dt=time.time()-t0;b,_=al.render(b0=0,b1=24)
    if not np.array_equal(a,b):c,_=al.render(b0=0,b1=24);print('   two renders differ by %g; a third equals the first %s, the second %s'%(float(np.abs(a-b).max()),bool(np.array_equal(a,c)),bool(np.array_equal(b,c))))
    w=a-dry[:,:a.shape[1]]
    print('%-7s rms %.4f (%6.1f dB) peak %.3f wet %6.1f dB nan %s equal %s step %.3f L/R %.3f %.3f tail(beats 8-12) %6.1f dB, last 2 s %6.1f dB  %.2fs'%(k,rms(a),db(rms(a)),np.abs(a).max(),db(rms(w)),bool(np.isnan(a).any()),bool(np.array_equal(a,b)),jump(a),rms(a[0]),rms(a[1]),db(rms(a[:,4*sr:6*sr])),db(rms(a[:,-2*sr:])),dt))
# seed
setp('cloud');a,_=al.render(b0=0,b1=12);setv("p.seed=2");b,_=al.render(b0=0,b1=12);setv("p.seed=1");c,_=al.render(b0=0,b1=12)
print('seed 1 twice equal',bool(np.array_equal(a,c)),'seed 2 differs',not np.array_equal(a,b))
# a part rendered alone must have the particles where a render from the start has them (the field belongs to the song time).
# One line, 5 ms, X drives pan: the left-right balance of the sound is the X of particle 1. Compared with the same steps worked out on the main thread.
al.run("(()=>{const t=S.tracks[0];t._sv=JSON.stringify(t.fx[0].p);t._nv=JSON.stringify(t.clips[0].notes);t._iv=JSON.stringify(t.inst);t.clips[0].notes=[{p:60,s:16,l:16,v:.9}];Object.assign(t.inst,{s:1,d:.01,r:.05});Object.assign(t.fx[0].p,FXPRE.vdelay.cloud[1],{mix:100,num:1,sync:'free',time:5,fb:0,ft:'off',tx:'pan',ax:100,ty:'off',td:'off'});changed(false)})()")
exp=json.loads(al.run("(()=>{const C=vdlC(),P=vdlSp(S.tracks[0].fx[0].p,{}),s=C.sim(P.seed),o=[],av=[0,0,0,0,0];for(let k=1;k<=1600;k++){C.step(s,P);if(k%50===0){vmC().attr(s.F,P,0,av);o.push(av[0])}}return JSON.stringify(o)})()"))
a,_=al.render(b0=0,b1=32);b,_=al.render(b0=16,b1=32)
def balx(x,t0):
    o=[]
    for i in range(16,31):
        c=int((i+1)*.5*sr)-int(t0*sr);seg=x[:,c-1000:c+1000];o.append(float(np.arctan2(rms(seg[1])+1e-12,rms(seg[0])+1e-12)/(np.pi/4)-1))
    return np.array(o)
ex=np.array(exp[16:31]);ba=balx(a,0);bb=balx(b,8)
print('X of particle 1 heard as pan, seconds 8.5 to 15.5: render from the start differs from the expected X by at most %.4f, render of the second half alone by at most %.4f (X moves between %.2f and %.2f)'%(float(np.abs(ba-ex).max()),float(np.abs(bb-ex).max()),ex.min(),ex.max()))
al.run("(()=>{const t=S.tracks[0];Object.assign(t.fx[0].p,JSON.parse(t._sv));t.clips[0].notes=JSON.parse(t._nv);Object.assign(t.inst,JSON.parse(t._iv));delete t._sv;delete t._nv;delete t._iv;changed(false)})()")
# mix 0 = the dry sound, mix 100 = no dry sound
setp('cloud');setv("p.mix=0");a,_=al.render(b0=0,b1=8);print('mix 0: difference to dry %g'%float(np.abs(a-dry[:,:a.shape[1]]).max()))
setv("p.mix=100;p.fb=0;p.sync='free';p.time=500;p.spd=0;p.ad=0;p.ax=0;p.ay=0;p.num=1;p.ft='off'");a,_=al.render(b0=0,b1=8)
i0=int(np.argmax(np.abs(dry[0])>1e-4));i1=int(np.argmax(np.abs(a[0])>1e-4));print('mix 100, one line, 500 ms: first sound %.1f ms later than dry; before that peak %g'%((i1-i0)/sr*1000,float(np.abs(a[:,:i1-10]).max()) if i1>10 else 0))
n=min(a.shape[1]-i1,dry.shape[1]-i0,sr//2);print('  the line is a copy of the dry sound: biggest difference %.5f (dry peak %.3f, line peak %.3f)'%(float(np.abs(a[:,i1:i1+n]/max(np.abs(a).max(),1e-9)-dry[:,i0:i0+n]/np.abs(dry).max()).max()),np.abs(dry).max(),np.abs(a).max()))
# tempo sync: 1/4 at 120 = 500 ms
setv("p.sync='1/4'");b,_=al.render(b0=0,b1=8);print('synced 1/4 equals 500 ms:',bool(np.allclose(a,b,atol=1e-6)))
# pitch: +12 doubles the spectral centre of the line, recycle keeps rising
setv("p.sync='free';p.time=500");c0=cen(a[:,i1:i1+sr//3],sr);setv("p.pitch=12");b,_=al.render(b0=0,b1=8);c1=cen(b[:,i1:i1+sr//3],sr);setv("p.pitch=-12");d,_=al.render(b0=0,b1=8);c2=cen(d[:,i1:i1+sr//3],sr)
print('spectral centre of the first repeat: pitch 0 %.0f Hz, +12 %.0f Hz, -12 %.0f Hz'%(c0,c1,c2))
al.run("S.tracks[0].clips[0].notes=[{p:60,s:0,l:.25,v:.9}];changed(false)")
setv("p.pitch=7;p.fb=70;p.rec=false");a,_=al.render(b0=0,b1=12);setv("p.rec=true");b,_=al.render(b0=0,b1=12)
seg=lambda x,k:cen(x[:,int((.02+.5*k)*sr):int((.02+.5*k+.3)*sr)],sr)
print('pitch +7, feedback 70, centre of repeats 1 to 5: recycle off',[round(seg(a,k)) for k in range(1,6)],'recycle on',[round(seg(b,k)) for k in range(1,6)])
# reverse changes the sound, feedback 100 with a resonant filter stays bounded
setv("p.pitch=0;p.rec=false;p.fb=40");a,_=al.render(b0=0,b1=8);setv("p.rev=true");b,_=al.render(b0=0,b1=8);print('reverse changes the sound',not np.array_equal(a,b),'rms %.4f %.4f peak %.3f'%(rms(a),rms(b),np.abs(b).max()))
setp('comb');setv("p.fb=100;p.q=12;p.ft='bp';p.cut=900;p.gain=100;p.mix=100;p.num=16;p.ad=0;p.damp=false");a,_=al.render(b0=0,b1=32);print('feedback 100, Q 12, 16 equal lines, 16 s: peak %.3f nan %s last second %.1f dB'%(np.abs(a).max(),bool(np.isnan(a).any()),db(rms(a[:,-sr:]))))
# every target, glide, emitter
al.run("S.tracks[0].clips[0].notes=%s;changed(false)"%json.dumps(notes))
for tg in ['time','pitch','pan','gain','cut']:
    setp('cloud');setv("p.tx='%s';p.ty='off';p.td='off'"%tg);a,_=al.render(b0=0,b1=10);print('X drives %-5s rms %.4f peak %.3f nan %s L-R %.4f'%(tg,rms(a),np.abs(a).max(),bool(np.isnan(a).any()),rms(a[0]-a[1])))
setp('cloud');setv("p.glide=200");a,_=al.render(b0=0,b1=10);print('glide 200 ms: rms %.4f peak %.3f nan %s step %.3f'%(rms(a),np.abs(a).max(),bool(np.isnan(a).any()),jump(a)))
setp('burst');a,_=al.render(b0=0,b1=10);setv("p.em=false");b,_=al.render(b0=0,b1=10);print('emitter on/off differ',not np.array_equal(a,b))
# cost: 16 lines, pitch shifted, not recycled (four readings per line), filter on
setp('cloud');setv("p.num=16;p.pitch=5;p.rec=false");t0=time.time();a,_=al.render(b0=0,b1=40);dt=time.time()-t0;setv("p.mix=0");t0=time.time();b,_=al.render(b0=0,b1=40);d0=time.time()-t0
print('heavy case: %.1f s of sound in %.2f s (the same with mix 0 and lines still running: %.2f s)'%(a.shape[1]/sr,dt,d0))
al.run("S.tracks[0].fx.length=0;changed(true)");t0=time.time();b,_=al.render(b0=0,b1=40);print('  without the effect: %.2f s'%(time.time()-t0))
print('errors',al.errors);al.stop()
al=AudioLab(IDX);al.start()
al.tracks=json.loads(al.run("JSON.stringify(Object.fromEntries(S.tracks.map(t=>[t.name,t.id])))"))
for nm in ('Kick','Bass'):
    x,sr=al.render(b0=64,b1=96,only=nm);print('Fractals %s %.5f dB'%(nm,db(rms(x))))
print('errors',al.errors);al.stop()
