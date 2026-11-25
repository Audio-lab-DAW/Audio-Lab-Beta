import sys,numpy as np
import os;sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','remake'))
from alab import AudioLab
al=AudioLab(sys.argv[1] if len(sys.argv)>1 else 'index.html');al.start()
print('ver',al.version)
rec={'tempo':120,'tracks':[{'name':'T','preset':'pluck','clips':[{'start':0,'len':16,'notes':[{'p':60,'s':0,'l':1,'v':.9},{'p':67,'s':4,'l':1,'v':.6}]}]}]}
try:
    al.build(rec)
except Exception as e: print('build',e)
def rms(x): return float(np.sqrt((x**2).mean()))
x0,sr=al.render(b0=0,b1=16);print('dry',rms(x0),np.abs(x0).max())
print(al.run("(()=>{const t=S.tracks[0];t.fx.unshift(mkFx('bnotes'));changed(true);const o=mfxNotes(t,t.clips[0].notes);return o.length+' '+JSON.stringify(o.slice(0,5).map(n=>[n.p,+n.s.toFixed(3),+n.v.toFixed(2)]))})()"))
x1,_=al.render(b0=0,b1=16);x2,_=al.render(b0=0,b1=16)
print('wet',rms(x1),np.abs(x1).max(),'nan',bool(np.isnan(x1).any()),'equal',bool(np.array_equal(x1,x2)),'maxdiff',float(np.abs(x1-x2).max()))
on=lambda x:[int(i) for i in np.where((np.abs(x[0,1:])>1e-4)&(np.abs(x[0,:-1])<=1e-4))[0][:1]]
print('first sound dry/wet (s)',on(x0)[0]/sr if on(x0) else None,on(x1)[0]/sr if on(x1) else None)
print(al.run("(()=>{const t=S.tracks[0],f=t.fx[0];Object.assign(f.p,FXPRE.bnotes.scatter[1]);const a=JSON.stringify(mfxNotes(t,t.clips[0].notes));f.p.seed=2;const b=JSON.stringify(mfxNotes(t,t.clips[0].notes));f.p.seed=1;const c=JSON.stringify(mfxNotes(t,t.clips[0].notes));return [a===c,a!==b,JSON.parse(a).length,[...new Set(JSON.parse(a).map(n=>n.p))].join(',')].join(' ')})()"))
print('errors',al.errors);al.stop()
