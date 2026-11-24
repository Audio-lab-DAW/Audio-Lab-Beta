from common import *
from alab import AudioLab
import build,vox,time
al=AudioLab('/home/claude/audiolab/index.html').start();vox.load(al);R=build.recipe();al.build(R)
al.run("V.x=0;0");al.save('out/Fractals_remake.audiolab');print('project saved',os.path.getsize('out/Fractals_remake.audiolab'),'bytes; tracks',len(R['tracks']),flush=True)
t=time.time();x,_=al.render(b0=0,b1=1152,tail=2);print('full render',x.shape,'in',round(time.time()-t),'s peak',np.abs(x).max(),flush=True)
pk=np.abs(x).max()
if pk>0.999:x=x/pk*0.999
sf.write('out/Fractals_remake_render.flac',x.T,SR,subtype='PCM_24')
r=stem('mix');n=min(x.shape[1],r.shape[1]);c=compare(r[:,:n],x[:,:n],SR);json.dump(c,open('out/full_compare.json','w'));print(fmt(c,'WHOLE SONG'),flush=True)
for b in (105,121,17):
    plot_compare(cut('mix',bar(b),bar(b+8)),x[:,int(bar(b)*SPB*SR):int(bar(b+8)*SPB*SR)],SR,f'out/compare_bars{b}.png',f'bars {b}-{b+7}')
al.stop()
