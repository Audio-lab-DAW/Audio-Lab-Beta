"""Vector FM (v0.176): offline render checks. python3 tools/engine-tests/vector_fm.py [index.html]"""
import sys,os,time,json,numpy as np
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','remake'))
from alab import AudioLab
al=AudioLab(sys.argv[1] if len(sys.argv)>1 else 'index.html');al.start()
print('ver',al.version,'errors after load',al.errors)
rec={'bpm':120,'tracks':[{'name':'V','preset':'vfm','clips':[{'start':0,'len':16,'notes':[{'p':60,'s':0,'l':4,'v':.9},{'p':67,'s':4,'l':2,'v':.7},{'p':55,'s':8,'l':3,'v':.8},{'p':62,'s':8,'l':3,'v':.8}]}]}]}
al.build(rec)
def rms(x): return float(np.sqrt((x**2).mean()))
def db(v): return 20*np.log10(max(v,1e-9))
def jump(x): return float(np.abs(np.diff(x,axis=1)).max())
setp=lambda k:al.run("(()=>{const I=S.tracks[0].inst;Object.assign(I,JSON.parse(JSON.stringify(vfmParams('%s'))),{ipk:'%s'});changed(false);return 1})()"%(k,k))
seti=lambda js:al.run("(()=>{const I=S.tracks[0].inst;%s;changed(false);return 1})()"%js)
one=lambda p=60,l=4:al.run("S.tracks[0].clips[0].notes=[{p:%d,s:0,l:%g,v:.9}];changed(false)"%(p,l))
keys=al.run("Object.keys(VFMPRE).join(',')").split(',')
for k in keys:
    setp(k);a,sr=al.render(b0=0,b1=24);b,_=al.render(b0=0,b1=24);act=a[:,:int(sr*5.5)]
    print('%-7s rms while notes sound %.4f (%6.1f dB) peak %.3f nan %s equal %s biggest step %.3f L/R %.3f %.3f tail(last s) %.5f'%(k,rms(act),db(rms(act)),np.abs(a).max(),bool(np.isnan(a).any()),bool(np.array_equal(a,b)),jump(a),rms(a[0]),rms(a[1]),rms(a[:,-sr:])))
setp('pad');a,_=al.render(b0=0,b1=8);seti("I.seed=2");b,_=al.render(b0=0,b1=8);seti("I.seed=1");c,_=al.render(b0=0,b1=8)
print('seed 1 twice equal',bool(np.array_equal(a,c)),'seed 2 differs',not np.array_equal(a,b))
# the note start inside an audio block must not matter
one();a,_=al.render(b0=0,b1=8);al.run("S.tracks[0].clips[0].notes=[{p:60,s:0.0133,l:4,v:.9}];changed(false)");b,_=al.render(b0=0,b1=8)
i0=int(np.argmax(np.abs(a[0])>1e-7));i1=int(np.argmax(np.abs(b[0])>1e-7));n=min(a.shape[1]-i0,b.shape[1]-i1)-10
print('start moved by %d samples; same sound after shifting: maxdiff %g'%(i1-i0,float(np.abs(a[:,i0:i0+n]-b[:,i1:i1+n]).max())))
# tuning: Index 0, nothing driven: a plain sine at the pitch of the key
def spec(x,t0=.3,t1=1.3):
    y=x[0][int(t0*sr):int(t1*sr)];X=np.abs(np.fft.rfft(y*np.hanning(len(y))));f=np.fft.rfftfreq(len(y),1/sr);return f,X
def peak(x):
    f,X=spec(x);return float(f[int(np.argmax(X))])
def others(x):
    f,X=spec(x);i=int(np.argmax(X));m=X.copy();m[max(0,i-6):i+7]=0;return db(float(m.max()/X[i]))
plain="Object.assign(I,vfmParams('pad'),{idx:0,ft:'',tx:'',ty:'',td:'',tm:'',att:.01,sus:1,num:4})"
seti(plain);one(69);a,_=al.render(b0=0,b1=4);one(57);b,_=al.render(b0=0,b1=4);seti("I.kf=false");c,_=al.render(b0=0,b1=4);seti("I.kf=true;I.cpit=12");d,_=al.render(b0=0,b1=4)
print('Index 0: key A3 %.1f Hz (440), key A2 %.1f Hz (220), keys off %.1f Hz (261.6), Pitch +12 %.1f Hz (440); loudest other part %.0f dB below'%(peak(a),peak(b),peak(c),peak(d),others(a)))
# Index and Ratio: side parts appear at the right distance (ratio 2 on A2: 220, 660, ...; ratio 3: 220, 440, 880 ...)
def parts(x,n=5):
    f,X=spec(x);idx=[i for i in range(2,len(X)-2) if X[i]>X[i-1] and X[i]>X[i+1] and X[i]>X.max()*.03];idx.sort(key=lambda i:-X[i]);return sorted(round(float(f[i])) for i in idx[:n])
seti(plain+";I.idx=1.5;I.rat=2");one(57);a,_=al.render(b0=0,b1=4);seti("I.rat=3");b,_=al.render(b0=0,b1=4);seti("I.rat=2.6;I.rn=true");c,_=al.render(b0=0,b1=4)
print('A2, Index 1.5: ratio 2 parts',parts(a),'ratio 3',parts(b),'ratio 2.6 with N (same as 3):',bool(np.array_equal(b,c)))
# what the vectors do
seti(plain+";I.tx='pan';I.ax=100");a,_=al.render(b0=0,b1=4);seti("I.ax=0");b,_=al.render(b0=0,b1=4)
print('X on pan: left-right difference %.4f, with X at 0: %.6f'%(rms(a[0]-a[1]),rms(b[0]-b[1])))
for tg in ('ratio','index','gain','detune','cut','pitch'):
    seti(plain+";I.idx=1;I.ft='lp';I.ty='%s';I.ay=0"%tg);a,_=al.render(b0=0,b1=4);seti("I.ay=60");b,_=al.render(b0=0,b1=4)
    print('  Y on %-6s changes the sound: %s (rms %.4f -> %.4f, nan %s, biggest step %.3f)'%(tg,not np.array_equal(a,b),rms(a),rms(b),bool(np.isnan(b).any()),jump(b)))
# pitch steps: with a scale the pitch only lands on notes of the scale
seti(plain+";I.ty='pitch';I.ay=50;I.num=1;I.spd=0;I.snap='major pentatonic'");one(57);a,_=al.render(b0=0,b1=4);st=12*np.log2(peak(a)/220)
print('Y on pitch with major pentatonic, one still particle: %.2f semitones from the key (a whole number from 0 2 4 7 9)'%st)
# operators and algorithms
for ops,alg in ((1,'s'),(2,'s'),(3,'s'),(3,'i'),(3,'o'),(4,'o')):
    seti("Object.assign(I,vfmParams('stack'),{ops:%d,alg:'%s',num:12})"%(ops,alg));one(57);a,_=al.render(b0=0,b1=6)
    print('  operators %d %s: rms %.4f peak %.3f nan %s biggest step %.3f'%(ops,alg,rms(a),np.abs(a).max(),bool(np.isnan(a).any()),jump(a)))
# waves and filters
for cw in range(4):
    seti(plain+";I.cw='%d';I.mw='%d';I.idx=1"%(cw,cw));one(81);a,_=al.render(b0=0,b1=3);one(33);b,_=al.render(b0=0,b1=3)
    print('  wave %d: A5 rms %.4f peak %.3f, A0 rms %.4f peak %.3f, nan %s'%(cw,rms(a),np.abs(a).max(),rms(b),np.abs(b).max(),bool(np.isnan(a).any() or np.isnan(b).any())))
for ft in ('lp','bp','hp','no'):
    seti(plain+";I.cw='2';I.ft='%s';I.cut=800;I.q=6"%ft);one(45);a,_=al.render(b0=0,b1=3);f,X=spec(a);lo=float(X[f<400].sum());hi=float(X[f>1600].sum())
    print('  filter %s at 800 Hz on a saw: below 400 Hz %.0f, above 1600 Hz %.0f, peak %.3f nan %s'%(ft,lo,hi,np.abs(a).max(),bool(np.isnan(a).any())))
# x10 and extreme settings must stay finite
seti("Object.assign(I,vfmParams('metal'),{x10:true,idx:10,rat:16,sc:200,spd:400,num:16,ft:'bp',q:12,cut:18000})");one(96,6);a,_=al.render(b0=0,b1=8)
print('extreme settings: rms %.4f peak %.3f nan %s'%(rms(a),np.abs(a).max(),bool(np.isnan(a).any())))
# one particle per key: 20 keys at once (more than 16) must not break
setp('keys');al.run("S.tracks[0].clips[0].notes=Array.from({length:20},(_,i)=>({p:48+i,s:i*.1,l:3,v:.7}));changed(false)");a,_=al.render(b0=0,b1=10)
print('20 keys, one particle each: rms %.4f peak %.3f nan %s biggest step %.3f'%(rms(a),np.abs(a).max(),bool(np.isnan(a).any()),jump(a)))
# cost: 16 voices with a filter each, six notes
setp('pad');al.run("S.tracks[0].inst.num=16;S.tracks[0].clips[0].notes=[48,52,55,60,64,67].map(p=>({p,s:0,l:8,v:.8}));changed(false)")
t0=time.time();h,_=al.render(b0=0,b1=8);dt=time.time()-t0
print('heavy case (16 pairs, 6 notes, filters): %.1f s of sound in %.2f s, rms %.4f peak %.3f'%(h.shape[1]/sr,dt,rms(h),np.abs(h).max()))
print('errors',al.errors);al.stop()
al=AudioLab(sys.argv[1] if len(sys.argv)>1 else 'index.html');al.start()
al.tracks=json.loads(al.run("JSON.stringify(Object.fromEntries(S.tracks.map(t=>[t.name,t.id])))"))
for nm in ('Kick','Bass'):
    x,sr=al.render(b0=64,b1=96,only=nm);print('Fractals %s %.5f dB'%(nm,db(rms(x))))
print('errors',al.errors);al.stop()
