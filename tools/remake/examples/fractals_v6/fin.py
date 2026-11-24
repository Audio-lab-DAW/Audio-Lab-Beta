from eng import *
import song,sys
sys.path.insert(0,'/home/claude/audio-lab-beta/tools/remake')
import pyloudnorm as pyln
al=start();R=song.recipe();build(al,R);al.run("V.x=0;0");al.save('v6_novox.audiolab');m=pyln.Meter(SR)
for b in (81,185):
    x,_=al.render(b0=song.bar(b),b1=song.bar(b+8));print('bars %d  LUFS %.1f  peak %.2f  crest %.1f'%(b,m.integrated_loudness(x.T),pk(x),20*np.log10(pk(x)/(np.sqrt((x**2).mean())+1e-9))),flush=True)
al.stop()
