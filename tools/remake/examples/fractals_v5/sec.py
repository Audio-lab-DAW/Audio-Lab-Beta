"""render sections of the mix; compare tonal balance and loudness with the reference's matching section"""
from eng import *
import song,sys,librosa
sys.path.insert(0,'/home/claude/audio-lab-beta/tools/remake')
from measure import *
REF,_=sf.read('/home/claude/remake/fractals/ref.wav');REF=REF.T.astype(np.float32);RSPB=60/145
al=start();R=song.recipe()
if '--vox' in sys.argv:
    import vox;vox.load(al,R)
build(al,R)
for b in [int(a) for a in sys.argv[1:] if a.isdigit()]:
    x,_=al.render(b0=song.bar(b),b1=song.bar(b+8));r=REF[:,int(song.bar(b)*RSPB*SR):int(song.bar(b+8)*RSPB*SR)]
    m=x.mean(0);crest=20*np.log10(pk(x)/(np.sqrt((x**2).mean())+1e-9))
    c=compare(r,x[:,:r.shape[1]] if x.shape[1]>r.shape[1] else x,SR) if r.shape[1]>SR else None
    import time;print('bars %d-%d peak %.2f crest %.1f dB  t=%s'%(b,b+7,pk(x),crest,time.strftime('%H:%M:%S')),flush=True)
    if c:print('   ',fmt(c,''),flush=True)
    sf.write(f'out/sec{b}.wav',x.T,SR)
al.stop()
