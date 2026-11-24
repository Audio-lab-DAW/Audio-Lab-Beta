from common import *
from alab import AudioLab
import build,vox,sys
al=AudioLab('/home/claude/audiolab/index.html').start();vox.load(al);R=build.recipe();al.build(R)
names=[t['name'] for t in R['tracks']];print(names)
for B0 in [int(a) for a in sys.argv[1:]]:
    ref=cut('other',bar(B0),bar(B0+8))+cut('vocals',bar(B0),bar(B0+8));print(B0,'ref other+vocals %.1f dB'%(20*np.log10(np.sqrt((ref**2).mean()))))
    for n in names:
        if n in ('Kick','Hats','Open hat','Clap','Snare & fills','Sub drone'):continue
        x,_=al.render(b0=bar(B0),b1=bar(B0+8),only=n,single=True);r=np.sqrt((x**2).mean())
        if r>1e-5:print('  %-18s %.1f dB  peak %.2f'%(n,20*np.log10(r),np.abs(x).max()))
al.stop()
