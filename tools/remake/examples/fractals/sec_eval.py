from common import *
from alab import AudioLab
import build,sys
al=AudioLab('/home/claude/audiolab/index.html').start();al.build(build.recipe())
for b in [int(a) for a in sys.argv[1:]]:
    x,_=al.render(b0=bar(b),b1=bar(b+8));r=cut('mix',bar(b),bar(b+8));m=min(r.shape[1],x.shape[1]);print(fmt(compare(r[:,:m],x[:,:m],SR),f'bars {b}'),'peak %.2f'%np.abs(x).max(),flush=True)
    save(f'out/s{b}.wav',x)
al.stop()
