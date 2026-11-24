"""Original (not transcribed) music for the Fractals remake: A natural minor, A pedal bass, i-VI-III-VII. -> compose.json"""
import json,numpy as np
OFF=[0,2,3,5,7,8,10]
def mid(n,base=57):return base+12*(n//7)+OFF[n%7]
PROG=[0,5,2,6]            # Am F C G, 2 bars each
def dp(d):return d if d<=2 else d-7
ARP=[0,7,4,7, 0,7,2,7, 0,7,4,7, 6,7,4,2]
ACC=[1,.62,.8,.62]*4
LEADA=[(4,0,6),(2,6,2),(0,8,4),(2,12,4),(4,16,6),(5,22,2),(4,24,4),(2,28,4)]
LEADB=[(7,0,4),(4,4,4),(2,8,4),(4,12,4),(7,16,8),(6,24,2),(4,26,2),(2,28,4)]
ARP_R=[(9,16,.5),(17,27,.7),(33,69,.85),(73,120,.9),(131,144,.85),(145,192,1),(209,272,1)]
LEAD_R=[(28,32,.8),(41,69,.9),(73,88,.95),(97,120,.95),(121,144,.9),(153,192,1),(193,208,.9),(209,256,1),(257,272,.9)]
PAD_R=[(1,36),(67,72),(105,160),(193,208),(257,288)]
def rng(R,b):
    for r in R:
        if r[0]<=b<=r[1]:return r
def build():
    tr={'Arp':[],'Lead':[],'Pad':[]};NB=288
    for b in range(1,NB+1):
        k=((b-1)//2)%4;d=dp(PROG[k]);beat=(b-1)*4
        r=rng(ARP_R,b)
        if r:
            for i in range(16):
                n=d+ARP[i]+(0 if True else 0);tr['Arp'].append((mid(n),beat+i/4,.2,round(ACC[i]*r[2],3)))
        r=rng(LEAD_R,b)
        if r and (b-1)%2==0:
            ph=LEADA if ((b-1)//2)%2==0 else LEADB
            for deg,st,ln in ph:
                n=7+d+deg
                tr['Lead'].append((mid(n),beat+st/4,ln/4*.92,round(.85*r[2]+.1*(st%8==0),3)))
        if any(a<=b<=c for a,c in PAD_R) and (b-1)%2==0:
            for deg in (0,2,4,7):
                n=d+deg;vol=.8
                tr['Pad'].append((mid(n),beat,7.9,.8 if deg!=7 else .5))
    return tr
def clips(name,notes,env=None):
    by={}
    for p,s,l,v in notes:by.setdefault(int(s//32),[]).append((p,s,l,v))
    out=[]
    for k in sorted(by):
        c={'start':k*32,'len':32,'name':f'{name} {k*8+1}','notes':[{'p':int(p),'s':round(s-k*32,4),'l':round(l,4),'v':v} for p,s,l,v in by[k]]}
        if env:
            e=env(k)
            if e:c['env']=e;c['envShow']=None
        out.append(c)
    return out
def arp_env(k):
    # filter opens over each 8-bar block (v .6 -> .88): 30*666^v Hz
    pts=[{'b':round(i*4,2),'v':round(.6+.28*i/8,3)} for i in range(9)]
    return {'cut':pts}
T=build()
tracks=[
 {'name':'Arp','preset':'plant','color':'#b583ff','inst':dict(w1='sawtooth',w2='square',morph=.25,uni=1,det=0,width=0,cut=2500,res=.4,fenv=0,a=.002,d=.13,s=.3,r=.05,lfo=.3,lamt=0,space=0,sub=0,noise=0,fm=0,ratio=2,gain=.5),'vol':.5,
  'fx':[{'type':'delay','p':{'time':.2069,'feedback':32,'mix':22,'lowcut':250,'highcut':6500}}],'clips':clips('Arp',T['Arp'],arp_env)},
 {'name':'Lead','preset':'plant','color':'#4cc9f0','inst':dict(w1='sawtooth',w2='sawtooth',morph=0,uni=3,det=14,width=80,cut=5500,res=.25,fenv=0,a=.01,d=.3,s=.7,r=.25,lfo=.3,lamt=0,space=0,sub=0,noise=0,fm=0,ratio=2,gain=.5),'vol':.5,
  'fx':[{'type':'delay','p':{'time':.3103,'feedback':38,'mix':28,'lowcut':300,'highcut':6000}},{'type':'reverb','p':{'decay':2.4,'predelay':20,'damp':7000,'lowcut':200,'mix':20}}],'clips':clips('Lead',T['Lead'])},
 {'name':'Pad','preset':'plant','color':'#7a8bff','inst':dict(w1='sawtooth',w2='sawtooth',morph=0,uni=4,det=18,width=100,cut=2000,res=.15,fenv=0,a=.9,d=.5,s=1,r=1.8,lfo=.3,lamt=0,space=0,sub=0,noise=0,fm=0,ratio=2,gain=.4),'vol':.5,
  'fx':[{'type':'reverb','p':{'decay':4.5,'predelay':30,'damp':5000,'lowcut':200,'mix':35}}],'clips':clips('Pad',T['Pad'])}]
json.dump(tracks,open('compose.json','w'))
print({t['name']:sum(len(c['notes']) for c in t['clips']) for t in tracks})
