from eng import *
import song,sys,vox
sys.path.insert(0,'/home/claude/audio-lab-beta/tools/remake')
from measure import *
import pyloudnorm as pyln
al=start();R=song.recipe();vox.load(al,R);build(al,R);m=pyln.Meter(SR)
for b in [int(a) for a in sys.argv[1:]]:
    x,_=al.render(b0=song.bar(b),b1=song.bar(b+8));crest=20*np.log10(pk(x)/(np.sqrt((x**2).mean())+1e-9))
    print('bars %d-%d  LUFS %.1f  peak %.2f  crest %.1f dB'%(b,b+7,m.integrated_loudness(x.T),pk(x),crest),flush=True)
al.run("V.x=0;0");al.save('out_v6.audiolab')
al.stop()
