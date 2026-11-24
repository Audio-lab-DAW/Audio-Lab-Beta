from common import *
from alab import AudioLab
from fit import fit_params,mel_loss
n=int(round(SPB*SR))
bs=stem('bass')
tmpl=np.mean([bs[:,int(round((T0+b*SPB)*SR)):int(round((T0+b*SPB)*SR))+n] for b in range(bar(37),bar(47))],0)
target=np.concatenate([tmpl,tmpl],1);save('bass_ref.wav',target)
st=n//4;lv=[rms_db(tmpl[:,i*st:(i+1)*st]) for i in range(4)];print('bass step levels dB',np.round(lv,1))
vel=[10**((l-max(lv[1:]))/20) for l in lv[1:]];print('velocities',np.round(vel,2))
al=AudioLab('/home/claude/audiolab/index.html').start()
def recipe(L):
    notes=[{'p':33,'s':b+o,'l':L,'v':float(v)} for b in range(2) for o,v in zip((.25,.5,.75),vel)]
    return {'bpm':BPM,'tracks':[{'name':'Bass','preset':'plant','vol':.8,'inst':{'w1':'sawtooth','w2':'square','morph':.1,'uni':1,'det':0,'width':0,'cut':420,'res':7,'fenv':75,'a':.001,'d':.11,'s':0,'r':.05,'lfo':.3,'lamt':0,'space':0,'sub':45,'noise':0,'fm':0,'ratio':2,'gain':.55},
      'fx':[{'type':'drive','p':{'drive':20,'mix':100}}],'clips':[{'start':0,'len':2,'name':'b','notes':notes}]}]}
al.build(recipe(.2))
keys=['morph','cut','res','fenv','d','s','r','sub','gain']
def apply(v):
    I=dict(zip(keys,v[:9]));al.run(f"Object.assign(S.tracks[0].inst,{json.dumps(I)});S.tracks[0].fx[0].p.drive={v[9]};for(const n of S.tracks[0].clips[0].notes)n.l={v[10]};0")
def render():
    x,_=al.render(b0=0,b1=2,only='Bass',single=True);return x
x0=[.1,420,7,75,.11,0,.05,45,.55,30,.2]
lo=[0,80,.5,0,.02,0,.01,0,.08,0,.08];hi=[1,4000,14,100,.5,1,.25,100,1,100,.25]
apply(x0);print('start loss',mel_loss(render(),target,SR,fmax=10000,level_free=True))
best,l=fit_params(apply,render,target,SR,x0,lo,hi,iters=3,log=[1,4],loss_kw={'fmax':10000,'level_free':True})
res=dict(zip(keys+['drive','notelen'],best));res['vel']=vel;res['loss']=l;json.dump(res,open('bass_fit.json','w'));print(res)
x=render();save('bass_model.wav',x)
print('bands ref ',band_db(target,SR).round(0));print('bands mod ',band_db(x,SR).round(0));print('lufs',lufs(np.tile(target,8),SR),lufs(np.tile(x[:,:target.shape[1]],8),SR))
al.stop()
