"""Fractals: turn the fitted gains into track volumes, EQ output gains and the master limiter; then score sections."""
from common import *
from alab import AudioLab
from fit import eq_bands
import build,sys,os
C=json.load(open('core_tune.json'));F=json.load(open('followers.json'))
base={'Kick':.8,'Bass':.8,'Hats':.5,'Open hat':.5,'Clap':.5,'Snare & fills':.5}
need={n:base[n]*C['gain'].get(n,1) for n in base};need['Snare & fills']=need['Clap']*1.2
extra=json.load(open('trim.json')) if os.path.exists('trim.json') else {}
for n,K in F['gain'].items():need[n]=.8*K
for n,x in extra.get('gain',{}).items():need[n]=need.get(n,1)*x
M=max(need.values())/3.98
mix={}
for n,g in need.items():
    r=g/M;vol=min(1,r);out=20*np.log10(r/vol) if r>vol else 0
    mix[n]={'vol':round(float(max(.02,vol)),3),'out':round(float(out),2)}
for n in ('Kick','Bass','Hats','Open hat'):
    mix[n]['fx']=[{'type':'eq','p':{'an':'off','bands':eq_bands(C['eq'][n])}}]
mix['master']=0;mix['mfx']=[{'type':'clip','p':{'gain':float(extra.get('clip_gain',14)),'thr':float(extra.get('clip_thr',-8)),'ceil':-1.8,'shape':'tanh','os':'4x','bias':0,'mix':100,'out':0}}]
json.dump(mix,open('mix.json','w'),indent=0)
print('M %.2f'%M,mix['mfx'][0]['p']['gain'],{n:(v['vol'],v['out']) for n,v in mix.items() if isinstance(v,dict)})
if len(sys.argv)>1 and sys.argv[1]=='score':
    al=AudioLab('/home/claude/audiolab/index.html').start();al.build(build.recipe());res={}
    for b in [1,9,17,25,33,41,49,65,73,89,105,121,129,137,145,161,185,193,201,209,233,257,273,281]:
        x,_=al.render(b0=bar(b),b1=bar(b+8));r=cut('mix',bar(b),bar(b+8));c=compare(r,x,SR);res[b]=c;save(f'out/sec{b:03d}.wav',x)
        print(fmt(c,f'bars {b}-{b+7}'),f'[{al.last_render_s:.0f}s]',flush=True)
    json.dump(res,open('score.json','w'));print('MEAN score %.1f  mean |dLUFS| %.1f  mean mel %.1f'%(np.mean([c['score'] for c in res.values()]),np.mean([abs(c['d_lufs']) for c in res.values()]),np.mean([c['mel_dist'] for c in res.values()])))
    al.stop()
