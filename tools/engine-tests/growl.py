# Growl instrument (v0.168): renders every preset through the app and prints level, brightness, sub share and stereo width.  python3 tools/engine-tests/growl.py index.html
import sys,numpy as np
import os;sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','remake'))
from alab import AudioLab
al=AudioLab(sys.argv[1] if len(sys.argv)>1 else 'index.html');al.start()
print('ver',al.version,al.run("!!PRESETS.growl+' '+Object.keys(GWPRE).length"))
rec={'tempo':174,'tracks':[{'name':'G','preset':'growl','clips':[{'start':0,'len':8,'notes':[{'p':36,'s':0,'l':2,'v':.9},{'p':36,'s':4,'l':2,'v':.9}]}]}]}
try: al.build(rec)
except Exception as e: print('build',e)
print(al.run("JSON.stringify(Object.keys(S.tracks[0].inst).slice(0,12))"))
def rms(x): return float(np.sqrt((x**2).mean()))
res={}
for k in al.run("Object.keys(GWPRE)"):
    t=al.run("(()=>{const t0=performance.now();const I=S.tracks[0].inst;for(const k in I)if(k!=='preset')delete I[k];Object.assign(I,grwParams('%s'));I.ipk='%s';changed(true);GWC.clear();grwBuf(I,36,.69,48000);return performance.now()-t0})()"%(k,k))
    x,sr=al.render(b0=0,b1=4)
    res[k]=x
    seg=x[:, :int(sr*.69)];m=seg.mean(0)
    sp=np.abs(np.fft.rfft(m*np.hanning(len(m))));fr=np.fft.rfftfreq(len(m),1/sr)
    cent=float((sp*fr).sum()/sp.sum());sub=float(sp[fr<110].sum()/sp.sum())
    side=rms(seg[0]-seg[1])/(rms(seg[0]+seg[1])+1e-9)
    print('%-9s render %5.1f ms  rms %.3f peak %.3f  centroid %5.0f Hz  below110 %.2f  side/mid %.2f nan %s'%(k,t,rms(seg),np.abs(seg).max(),cent,sub,side,bool(np.isnan(x).any())))
x1,_=al.render(b0=0,b1=4);print('repeat equal',bool(np.array_equal(x1,res['init'])))
print('errors',al.errors);al.stop()
