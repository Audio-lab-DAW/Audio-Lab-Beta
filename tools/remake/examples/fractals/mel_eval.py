from common import *
from alab import AudioLab
import build,sys
B0=int(sys.argv[1]) if len(sys.argv)>1 else 105
al=AudioLab('/home/claude/audiolab/index.html').start();R=build.recipe();al.build(R)
ref=cut('other',bar(B0),bar(B0+8))+cut('vocals',bar(B0),bar(B0+8))
xs=[]
for n in ['Mel low','Mel mid','Mel high']:
    x,_=al.render(b0=bar(B0),b1=bar(B0+8),only=n,single=True);xs.append(x);print(n,'rms dB %.1f'%(20*np.log10(np.sqrt((x**2).mean())+1e-9)))
m=min(len(ref[0]),xs[0].shape[1]);y=sum(x[:,:m] for x in xs)
print('ref rms dB %.1f'%(20*np.log10(np.sqrt((ref**2).mean()))),'mix rms dB %.1f'%(20*np.log10(np.sqrt((y**2).mean()))))
g=np.sqrt((ref[:,:m]**2).mean()/(y**2).mean());y=y*g;print('gain applied',20*np.log10(g))
print(fmt(compare(ref[:,:m],y,SR),f'melody-only bars {B0}'))
sf.write(f'out/mel_{B0}.wav',y.T,SR);sf.write(f'out/melref_{B0}.wav',ref[:,:m].T,SR)
plot_compare(ref[:,:m],y,SR,f'out/mel_cmp_{B0}.png',f'melody bars {B0}')
al.stop()
