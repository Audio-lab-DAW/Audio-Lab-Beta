"""Closed loop: render each 8-bar block, compare band by band with the original, and correct the follower
layer of that band in that block. Repeating this pulls the tonal balance and the loudness of every block
towards the original, whatever the master clipper and stem leakage do."""
from common import *
from alab import AudioLab
from followers import BANDS_F
from fit import band_matrix
import build,sys,os
iters=int(sys.argv[1]) if len(sys.argv)>1 else 2
BG=json.load(open('blockgain.json')) if os.path.exists('blockgain.json') else {}
names=[f'Synth {lo}-{hi} Hz' for lo,hi in BANDS_F]
al=AudioLab('/home/claude/audiolab/index.html').start()
for it in range(iters):
    al.build(build.recipe());errs=[];sc=[]
    for k in range(36):
        b0=k*32;x,_=al.render(b0=b0,b1=b0+32);r=cut('mix',b0,b0+32);n=min(x.shape[1],r.shape[1])
        Pm=band_matrix(x[:,:n],SR,BANDS_F);Pr=band_matrix(r[:,:n],SR,BANDS_F);d=10*np.log10((Pr+1e-12)/(Pm+1e-12))
        errs.append(np.abs(d).mean())
        for nm,dd in zip(names,d):
            cur=BG.setdefault(nm,{}).get(str(k),0);BG[nm][str(k)]=float(np.clip(cur+np.clip(dd,-6,6)*.8,-18,10))
        if it==iters-1:sc.append(compare(r[:,:n],x[:,:n],SR))
    json.dump(BG,open('blockgain.json','w'));print(f'iteration {it+1}: mean |band error| before correction {np.mean(errs):.2f} dB',flush=True)
al.stop()
