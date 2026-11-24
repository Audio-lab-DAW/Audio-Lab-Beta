from common import *
from alab import AudioLab
from fit import automix,eq_match,eq_bands,octave_db
from scipy.signal import butter,sosfiltfilt
import build,os
mix=json.load(open('mix.json')) if os.path.exists('mix.json') else {}
al=AudioLab('/home/claude/audiolab/index.html').start()
R=build.recipe(mix={})
for t in R['tracks']:
    if t['name'] in ('Kick','Bass','Hats','Open hat','Clap','Snare & fills'):t['fx']=[{'type':'eq','p':{'bands':[None]*7+eq_bands([0]*9)[7:]}}]
al.build(R)
def setg(name):
    def f(g):
        bands=eq_bands(g);al.run(f"(()=>{{const t=S.tracks.find(x=>x.name==={json.dumps(name)}),e=t.fx[0];e.p.bands={json.dumps(bands)};e.p.an='off';return 0}})()")
    return f
info=al.run("JSON.stringify({m:S.master,lim:FXDEF.limit&&FXDEF.limit.p,clip:FXDEF.clip&&FXDEF.clip.p,mg:masterGain()})");print(info)
# 1 kick
K,_=sf.read('kick_ref.wav');kt=np.stack([K,K])
rk=lambda:al.render(b0=bar(33),b1=bar(33)+1,only='Kick',single=True)[0]
gk=eq_match(rk,kt,SR,setg('Kick'));print('kick eq',gk)
x=rk();print(' kick mel after eq', compare(np.tile(kt,(1,8)),np.tile(x[:,:kt.shape[1]],(1,8)),SR)['mel_dist'])
# 2 bass
b0,b1=bar(37),bar(39);bt=cut('bass',b0,b1)
rb=lambda:al.render(b0=b0,b1=b1,only='Bass',single=True)[0]
gb=eq_match(rb,bt,SR,setg('Bass'));print('bass eq',gb)
# 3 tops: one EQ shared by hats and open hat, matched to the drums stem above 2 kHz
b0,b1=bar(105),bar(109);hp=lambda x:sosfiltfilt(butter(4,2500,'high',fs=SR,output='sos'),x)
tt=hp(cut('drums',b0,b1))
def rt():
    return sum(al.render(b0=b0,b1=b1,only=n,single=True)[0] for n in ('Hats','Open hat'))
def sett(g):
    setg('Hats')(g);setg('Open hat')(g)
gt=eq_match(lambda:hp(rt()),tt,SR,sett);print('tops eq',gt)
# 4 automix on a full section
b0,b1=bar(105),bar(113);ref=cut('drums',b0,b1)+cut('bass',b0,b1);st={}
for n in ['Kick','Bass','Hats','Open hat','Clap','Snare & fills']:st[n]=al.render(b0=b0,b1=b1,only=n)[0]
g=automix(st,ref,SR,BANDS,frame_s=SPB/4,max_gain=40);print('gains',{k:round(v,2) for k,v in g.items()})
m=sum(st[n][:,:ref.shape[1]]*g[n] for n in st);print(fmt(compare(ref,m,SR),'drums+bass 105'))
print(fmt(compare(cut('bass',b0,b1),st['Bass'][:,:ref.shape[1]]*g['Bass'],SR),'bass'));print(fmt(compare(cut('drums',b0,b1),sum(st[n][:,:ref.shape[1]]*g[n] for n in st if n!='Bass'),SR),'drums'))
json.dump({'eq':{'Kick':gk,'Bass':gb,'Hats':gt,'Open hat':gt},'gain':g},open('core_tune.json','w'))
al.stop()
