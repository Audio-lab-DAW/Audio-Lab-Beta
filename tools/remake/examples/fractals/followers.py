"""Fractals: the synth and FX layers as 'followers'. Everything melodic in the original sits on one note (A),
and what changes is rhythm and tone. So each layer is a saw drone on A through a fixed band-pass, and its
clip volume envelope follows the energy the original has in that band (64th-note resolution)."""
from common import *
from alab import AudioLab
from scipy.signal import butter,sosfiltfilt
NB=288;R=4            # envelope points per 16th
BANDS_F=[(80,160),(160,320),(320,640),(640,1280),(1280,2560),(2560,5120),(5120,10240),(10240,16000)]
def bp(x,lo,hi):return sosfiltfilt(butter(4,[lo,min(hi,SR/2*.95)],'band',fs=SR,output='sos'),x)
def env(y,n):
    w=SPB/4/R*SR;E=np.zeros(n)
    for i in range(n):
        a=int(round(T0*SR+i*w));seg=y[a:a+int(round(w))];E[i]=np.sqrt((seg**2).mean()+1e-16) if len(seg) else 0
    return E
def carrier(lo,hi,wide):
    # one saw per side (two voices, a few cents apart, panned hard left and right: wide, and no voices beating inside one channel), slow attack and
    # release so the note that starts each bar crossfades with the one before
    inst=dict(w1='sawtooth',w2='sawtooth',morph=0,uni=2 if wide else 1,det=6 if wide else 0,width=100 if wide else 0,cut=18000,res=.5,fenv=0,a=.03,d=.1,s=1,r=.09,lfo=.3,lamt=0,space=0,sub=0,noise=0,fm=0,ratio=2,gain=.5)
    eq={'type':'eq','p':{'an':'off','bands':[{'t':'highpass','f':lo,'q':.7,'on':True,'sl':24},None,None,None,None,None,{'t':'lowpass','f':hi,'q':.7,'on':True,'sl':24}]}}
    fx=[eq]
    return inst,fx
def drone_clip(start_bar,nbars,pts,name):
    notes=[{'p':33,'s':b*4,'l':4.08,'v':1} for b in range(nbars)]   # a little longer than the bar: the release overlaps the next attack, so there is no dip
    c={'start':start_bar*4,'len':nbars*4,'name':name,'notes':notes}
    if pts is not None:c['env']={'vol':pts};c['envShow']='vol'
    return c
def simplify(v):
    """keep a point only where a straight line between its kept neighbours would be off by more than 0.012"""
    keep=[0];n=len(v)
    for i in range(1,n-1):
        a=keep[-1];j=i+1
        lin=v[a]+(v[j]-v[a])*(i-a)/(j-a)
        if abs(lin-v[i])>.012:keep.append(i)
    keep.append(n-1);return keep
if __name__=='__main__':
    tgt=mono(stem('other'))+mono(stem('vocals'));n=NB*16*R
    defs=[(f'Synth {lo}-{hi} Hz',lo,hi,lo>=320,tgt,None) for lo,hi in BANDS_F]
    S=json.load(open('song.json'));db=np.zeros(NB,bool);db[S['drone_bars']]=True;db[:4]=True
    defs.append(('Sub drone',30,250,False,mono(stem('bass')),db))
    al=AudioLab('/home/claude/audiolab/index.html').start()
    cal={'bpm':BPM,'tracks':[]}
    for name,lo,hi,wide,_,_ in defs:
        inst,fx=carrier(lo,hi,wide);cal['tracks'].append({'name':name,'preset':'plant','inst':inst,'vol':.8,'fx':fx,'clips':[drone_clip(0,2,None,'cal')]})
    al.build(cal);tracks=[];info={}
    for (name,lo,hi,wide,src,mask),col in zip(defs,['#b583ff','#9d7bff','#7a8bff','#4c8dff','#4cc9f0','#3ecf8e','#9be564','#f5c84c','#8b8f9c']):
        x,_=al.render(b0=1,b1=7,only=name,single=True);rc=np.sqrt((bp(mono(x),lo,hi)**2).mean())
        E=env(bp(src,lo,hi),n)
        if mask is not None:E=E*np.repeat(mask,16*R)
        g=E/rc;K=max(1e-9,np.percentile(g,99.7)/1.6);v=np.clip(.75*np.sqrt(g/K),0,1)
        inst,fx=carrier(lo,hi,wide);clips=[]
        for k in range(NB//8):
            seg=v[k*8*16*R:(k+1)*8*16*R]
            if seg.max()<.04:continue
            idx=simplify(seg);pts=[{'b':round(i/(4*R),4),'v':round(float(seg[i]),3)} for i in idx]
            clips.append(drone_clip(k*8,8,pts,f'{name.split(" Hz")[0]} · {k*8+1}'))
        tracks.append({'name':name,'preset':'plant','color':col,'inst':inst,'fx':fx,'clips':clips,'vol':.8});info[name]={'K':float(K),'rc':float(rc),'pts':sum(len(c['env']['vol']) for c in clips)}
        print(name,'carrier rms %.4f'%rc,'gain K %.2f'%K,'clips',len(clips),'points',info[name]['pts'],flush=True)
    json.dump({'tracks':tracks,'gain':{k:v['K'] for k,v in info.items()}},open('followers.json','w'))
    al.stop()
