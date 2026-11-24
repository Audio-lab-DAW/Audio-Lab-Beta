"""Fractals: turn the stems into notes. Writes song.json."""
from common import *
from scipy.signal import butter,sosfiltfilt
NB=288;NS=NB*16;step=SPB/4
def bp(x,lo,hi):return sosfiltfilt(butter(4,[lo,hi],'band',fs=SR,output='sos'),x)
def stepE(y,frac=.7,start=0.0):
    E=np.zeros(NS)
    for i in range(NS):
        a=int(round((T0+(i+start)*step)*SR));seg=y[a:a+int(step*SR*frac)]
        E[i]=np.sqrt((seg**2).mean()+1e-14) if len(seg) else 0
    return E
d=mono(stem('drums'));bs=mono(stem('bass'))
out={}
# ---------- kick: low band at steps on the beat, needs the click too
Ek=stepE(bp(d,35,120),frac=1.6,start=.3);Ec=stepE(bp(d,2000,8000),frac=.25)
ref=np.percentile(Ek[::4],80)
kick=[]
for i in range(NS):
    b,s=divmod(i,16);on=(s%4==0)
    lvl=Ek[i]/ref
    if on and lvl>.25:kick.append([i,float(np.clip(lvl,0.3,1.0)**.8)])
# rolls: bars where 16th kicks appear between beats (kick band rises on off-beat steps with clicks)
Eks=stepE(bp(d,35,120),frac=.9)
for b in (175,223,239):   # 0-based bars 176,224,240
    for s in range(16):
        i=b*16+s
        if s%4 and Eks[i]/ref>.3 and Ec[i]>np.percentile(Ec,60):kick.append([i,float(np.clip(Eks[i]/ref,.3,1)**.8)])
kick.sort();out['kick']=kick
# ---------- bass: step energies -> notes when the bar has the rolling shape, drone otherwise
Eb=stepE(bp(bs,30,400),frac=.85);bref=np.percentile(Eb,90)
bass=[];drone_bars=[]
for b in range(NB):
    e=Eb[b*16:(b+1)*16]/bref
    if e.max()<.03:continue
    on=e.reshape(4,4)
    rolling=np.mean(on[:,1:].max(1))>2.2*np.mean(on[:,0])+1e-6
    if rolling:
        for s in range(16):
            if s%4 and e[s]>.06:bass.append([b*16+s,float(np.clip(e[s],0,1.15))])
    else:drone_bars.append(b)
out['bass']=bass;out['drone_bars']=drone_bars
# bass brightness per bar (share of energy above 180 Hz), to drive a filter in the intro
hi=stepE(bp(bs,180,2000),frac=.85);br=[float(np.sqrt((hi[b*16:(b+1)*16]**2).sum()/((Eb[b*16:(b+1)*16]**2).sum()+1e-12))) for b in range(NB)]
out['bass_bright']=br
# ---------- hats / clap / snare from the drums stem without the kick
Eh=stepE(bp(d,5000,9500),frac=.5);Ea=stepE(bp(d,10000,18000),frac=.9);Es=stepE(bp(d,1200,4000),frac=.6);Eo=stepE(bp(d,250,900),frac=.6)
href=np.percentile(Eh,95);aref=np.percentile(Ea,95);sref=np.percentile(Es,95);oref=np.percentile(Eo[np.arange(NS)%4!=0],97)
hat=[];ohat=[];clap=[];snare=[]
kset={i for i,_ in kick}
for b in range(NB):
    sl=slice(b*16,(b+1)*16);h=Eh[sl]/href;a=Ea[sl]/aref;sn=Es[sl]/sref;o=Eo[sl]/oref
    base_a=np.median(a[[0,1,3,4,5,7,8,9,11,12,13,15]])
    beat_click=np.median(sn[[0,8]])
    for s in range(16):
        i=b*16+s
        if h[s]>.12:hat.append([i,float(np.clip(h[s],0,1.1)**.7)])
        if s%4==2 and a[s]>1.35*base_a and a[s]>.25:ohat.append([i,float(np.clip(a[s]-base_a,0,1)**.7)])
        if s in (4,12) and sn[s]>1.2*beat_click and sn[s]>.3:clap.append([i,float(np.clip(sn[s]-beat_click,0,1)**.7)])
        if i not in kset and o[s]>.35 and s%4!=0:snare.append([i,float(np.clip(o[s],0,1.1)**.7)])
out.update(hat=hat,ohat=ohat,clap=clap,snare=snare)
json.dump(out,open('song.json','w'))
print({k:(len(v) if isinstance(v,list) else v) for k,v in out.items() if k!='bass_bright'})
print('drone bars',[b+1 for b in drone_bars][:60])
bb=np.array(br);print('bass brightness per 8 bars:',[round(float(bb[i:i+8].mean()),2) for i in range(0,NB,8)])
def show(name,lst,bars):
    m=dict(lst)
    for b in bars:print(f" {name} bar {b}:",''.join('.' if (b-1)*16+s not in m else str(min(9,int(m[(b-1)*16+s]*9))) for s in range(16)))
show('kick',kick,[17,33,80,87,176,224]);show('bass',bass,[17,23,33,36,80,95]);show('hat',hat,[36,41,49,57,105]);show('ohat',ohat,[41,49,57,105]);show('clap',clap,[49,57,93,105]);show('snare',snare,[48,70,71,88,105,143])
