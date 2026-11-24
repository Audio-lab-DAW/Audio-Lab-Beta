"""v4: original psytrance parts in A phrygian over the original's drums, bass and structure -> compose.json
Research basis: rolling K-B-B-B bass with a plucky filter envelope; phrygian (plus the harmonic-minor G#) leads built
from short 16th motifs in call-and-response; syncopated / 3-against-4 sequences; saw plucks with long delays;
changes every 8/16 bars; risers, downlifters, impacts and snare rolls for tension and release."""
import json,numpy as np
BPB=4
# ---------------- arrangement (bars, 1-based inclusive) ----------------
LEAD=[(73,88,'A'),(105,120,'AB'),(161,192,'AB'),(209,240,'AB'),(257,268,'B')]
SEQ=[(33,48),(73,88),(105,120),(145,160),(161,192),(209,232),(273,280)]
ACID=[(21,27,'p1'),(49,69,'p1'),(89,104,'p2'),(145,160,'p2'),(177,192,'p1'),(225,256,'p2')]
PAD=[(1,27),(28,32),(121,144),(193,208),(257,288)]
BDLEAD=[(125,140),(195,206)]
DROPS=[17,33,49,73,89,105,145,161,209,257]
RISE=[(13,16),(29,32),(45,48),(70,72),(85,88),(101,104),(137,144),(157,160),(201,208),(253,256)]
UPLIFT=[(141,144),(205,208)]
ROLL=[(141,144),(205,208)]
ZAPS=[b for a,c in [(33,69),(73,120),(145,192),(209,256)] for b in range(a+7,c+1,8)]
SHAKE=[(49,69),(73,88),(105,120),(161,192),(209,256)]
def inr(R,b):
    for r in R:
        if r[0]<=b<=r[1]:return r
# ---------------- notes ----------------
A3=57
def ph(n):  # A phrygian degree -> midi relative to A3
    o=[0,1,3,5,7,8,10];return A3+12*(n//7)+o[n%7]
# main lead: 4-bar call and response (step, midi, len in 16ths)
CALL=[(0,69,2),(3,69,1),(4,67,2),(6,65,2),(8,64,2),(11,65,1),(12,64,2),(14,60,2),
      (16,62,3),(19,64,1),(20,65,2),(22,64,2),(24,62,2),(26,60,2),(28,58,2),(30,60,2)]
RESP_A=[(32,69,2),(35,69,1),(36,70,2),(38,69,2),(40,67,2),(43,69,1),(44,67,2),(46,65,2),
        (48,64,4),(52,65,2),(54,64,2),(56,62,1),(57,64,1),(58,65,2),(60,68,2),(62,69,2)]
RESP_B=[(32,72,2),(35,72,1),(36,70,2),(38,69,2),(40,70,2),(43,72,1),(44,74,2),(46,76,2),
        (48,77,3),(51,76,1),(52,74,2),(54,72,2),(56,70,2),(58,69,2),(60,68,2),(62,69,2)]
ACC_LEAD={0,16,32,48}
# acid: one-bar patterns (midi or None, accent, slide)
AC1=[(45,1,0),(45,0,0),(57,1,1),(45,0,0),(None,0,0),(45,0,0),(48,1,0),(45,0,1),(46,0,0),(45,0,0),(57,1,0),(None,0,0),(43,0,0),(45,0,1),(53,1,0),(52,0,0)]
AC2=[(45,1,0),(57,0,1),(55,0,0),(45,0,0),(46,1,0),(45,0,0),(None,0,0),(57,1,1),(58,0,0),(57,0,0),(45,0,0),(48,1,0),(45,0,0),(None,0,0),(52,1,1),(53,0,0)]
SEQ3=[81,76,72]          # A5 E5 C5: a three-note cycle over 16ths = 3 against 4
SEQ3B=[81,77,72]         # with F on the second half of each 8 bars
PADCH=[[57,60,64,69],[58,62,65,70],[55,58,62,67],[57,60,64,69]]   # Am  Bb  Gm  Am, 4 bars each
BDMEL=[(0,76,8),(8,77,4),(12,76,4),(16,74,8),(24,72,4),(28,70,4),(32,69,12),(44,68,4),(48,69,16)]   # in beats, 16 bars... uses 64 beats
def events():
    E={k:[] for k in ['Lead','Sequence','Acid','Pad','Breakdown lead','Riser','Uplifter','Impact','Sub boom','Downlifter','Reverse crash','Zaps','Shaker','Snare roll']}
    for b in range(1,289):
        beat=(b-1)*BPB
        r=inr(LEAD,b)
        if r and (b-r[0])%4==0:
            ph4=((b-r[0])//4)
            resp=RESP_B if ('B' in r[2] and (r[2]=='B' or ph4%2==1)) else RESP_A
            for st,p,l in CALL+resp:
                E['Lead'].append((p,beat+st/4,l/4*.9,.95 if st in ACC_LEAD else .78))
        r=inr(SEQ,b)
        if r:
            cyc=SEQ3B if (b-1)%8>=4 else SEQ3
            for i in range(16):
                g=(b-1)*16+i;E['Sequence'].append((cyc[g%3],beat+i/4,.18,.9 if i%4==2 else .65))
        r=inr(ACID,b)
        if r:
            pat=AC1 if r[2]=='p1' else AC2
            if (b-r[0])%4==3:pat=pat[:12]+[(57,1,0),(55,0,1),(53,0,0),(52,1,1)]   # turnaround every 4th bar
            for i,(p,a,s) in enumerate(pat):
                if p is None:continue
                E['Acid'].append((p,beat+i/4,.25*(1.3 if s else .55),.95 if a else .7))
        if inr(PAD,b) and (b-1)%4==0:
            ch=PADCH[((b-1)//4)%4]
            for p in ch:E['Pad'].append((p,beat,15.8,.7))
        r=inr(BDLEAD,b)
        if r and (b-r[0])%16==0:
            for st,p,l in BDMEL:E['Breakdown lead'].append((p,beat+st,l*.95,.85))
    for a,c in RISE:E['Riser'].append((60,(a-1)*BPB,(c-a+1)*BPB,.9))
    for a,c in UPLIFT:E['Uplifter'].append((57,(a-1)*BPB,(c-a+1)*BPB,.85))
    for d in DROPS:
        E['Impact'].append((45,(d-1)*BPB,2,1));E['Sub boom'].append((33,(d-1)*BPB,4,.9))
        E['Downlifter'].append((60,(d-1)*BPB,8,.8));E['Reverse crash'].append((60,(d-2)*BPB,4,.85))
    for i,b in enumerate(ZAPS):E['Zaps'].append(([69,76,72,81][i%4],(b-1)*BPB+3,1,.75))
    for a,c in SHAKE:
        for b in range(a,c+1):
            for i in range(16):
                if i%4==2:E['Shaker'].append((60,(b-1)*BPB+i/4,.1,.8))
                elif i%2==1:E['Shaker'].append((60,(b-1)*BPB+i/4,.1,.35))
    for a,c in ROLL:
        n=(c-a+1)
        for k in range(n):
            div=[2,4,4,8][min(3,k*4//n)]
            for j in range(4*div//1):
                t=(a-1+k)*BPB+j/div
                E['Snare roll'].append((60,t,.1,round(.35+.6*((k*4*div+j)/(n*4*div)),3)))
    return E
def clips(name,ev,env=None,blk=8):
    by={}
    for p,s,l,v in ev:by.setdefault(int(s//(blk*BPB)),[]).append((p,s,l,v))
    out=[]
    for k in sorted(by):
        s0=k*blk*BPB;c={'start':s0,'len':blk*BPB,'name':f'{name} {k*blk+1}','notes':[{'p':int(p),'s':round(s-s0,4),'l':round(l,4),'v':v} for p,s,l,v in by[k]]}
        if env:
            pts=env(k*blk+1)
            if pts:c['env']={'cut':pts};c['envShow']=None
        out.append(c)
    return out
def ramp(R,lo,hi,blk=8):
    """filter that opens from lo to hi over each range R (cut env, 0..1 = 30 Hz..20 kHz)"""
    def f(b0):
        r=inr(R,b0) or inr(R,b0+blk-1)
        if not r:return None
        pts=[]
        for i in range(blk+1):
            b=b0+i;x=np.clip((b-r[0])/max(1,r[1]-r[0]+1),0,1);pts.append({'b':i*BPB,'v':round(float(lo+(hi-lo)*x),3)})
        return pts
    return f
DLY=lambda t,fb,mix,lc=300,hc=6500:{'type':'delay','p':{'time':t,'feedback':fb,'mix':mix,'lowcut':lc,'highcut':hc}}
RVB=lambda d,mix,pd=20,dmp=6000:{'type':'reverb','p':{'decay':d,'predelay':pd,'damp':dmp,'lowcut':250,'mix':mix}}
D316=60/145*.75; D18=60/145*.5
def plant(**k):
    b=dict(w1='sawtooth',w2='sawtooth',morph=0,uni=1,det=0,width=0,cut=4000,res=.5,fenv=0,a=.003,d=.2,s=.5,r=.1,lfo=.3,lamt=0,space=0,sub=0,noise=0,fm=0,ratio=2,gain=.5);b.update(k);return b
def sfx(kind,tone=60,space=35,gain=.5):return {'kind':kind,'tone':tone,'space':space,'gain':gain}
E=events()
T=[
 {'name':'Lead','preset':'plant','color':'#4cc9f0','vol':.5,'inst':plant(uni=2,det=11,width=70,cut=3400,res=1.5,fenv=55,a=.002,d=.17,s=.35,r=.09),
  'fx':[DLY(D316,42,30),RVB(2.2,14)],'clips':clips('Lead',E['Lead'],ramp([(257,268)],.85,.62))},
 {'name':'Sequence','preset':'plant','color':'#9be564','vol':.4,'pan':.15,'inst':plant(w1='square',w2='sawtooth',morph=.4,cut=2600,res=3,fenv=60,a=.001,d=.09,s=.1,r=.05),
  'fx':[DLY(D18,30,22,600,8000)],'clips':clips('Seq',E['Sequence'],ramp(SEQ,.58,.93))},
 {'name':'Acid','preset':'acid','color':'#ff9a3c','vol':.45,'inst':{'wave':'sawtooth','cut':420,'res':21,'env':78,'dec':.14,'acc':70,'slide':.035,'dist':50,'gain':.35},
  'fx':[DLY(D316,25,16,400,5000)],'clips':clips('Acid',E['Acid'],ramp([(a,c) for a,c,_ in ACID],.62,.95))},
 {'name':'Pad','preset':'plant','color':'#7a8bff','vol':.4,'inst':plant(uni=4,det=18,width=100,cut=1900,res=.3,a=1.4,d=.8,s=1,r=2.4,lamt=12,lfo=.15,gain=.4),
  'fx':[RVB(5,38,40,4500)],'clips':clips('Pad',E['Pad'],ramp([(1,27),(121,144),(193,208)],.6,.9))},
 {'name':'Breakdown lead','preset':'plant','color':'#b583ff','vol':.45,'inst':plant(uni=3,det=14,width=80,cut=3600,res=.8,a=.25,d=.6,s=.85,r=1.2,lamt=8,lfo=5.5,gain=.45),
  'fx':[DLY(D316,45,28),RVB(4.5,32,30,5500)],'clips':clips('Theme',E['Breakdown lead'])},
 {'name':'Riser','preset':'sfx','color':'#f5c84c','vol':.45,'inst':sfx('riser',60,30),'clips':clips('Riser',E['Riser'])},
 {'name':'Uplifter','preset':'sfx','color':'#f5c84c','vol':.35,'inst':sfx('uplift',55,30),'clips':clips('Uplift',E['Uplifter'])},
 {'name':'Impact','preset':'sfx','color':'#ff4d6d','vol':.5,'inst':sfx('impact',55,45),'clips':clips('Impact',E['Impact'])},
 {'name':'Sub boom','preset':'sfx','color':'#ff4d6d','vol':.45,'inst':sfx('boom',50,10),'clips':clips('Boom',E['Sub boom'])},
 {'name':'Downlifter','preset':'sfx','color':'#3ecf8e','vol':.35,'inst':sfx('downer',55,40),'clips':clips('Down',E['Downlifter'])},
 {'name':'Reverse crash','preset':'sfx','color':'#3ecf8e','vol':.4,'inst':sfx('revcrash',65,20),'clips':clips('Rev',E['Reverse crash'])},
 {'name':'Zaps','preset':'sfx','color':'#ff7ac8','vol':.3,'pan':-.2,'inst':sfx('laser',60,35),'fx':[DLY(D316,55,40,500,9000)],'clips':clips('Zap',E['Zaps'])},
 {'name':'Shaker','preset':'sfx','color':'#8b8f9c','vol':.25,'pan':.25,'inst':sfx('shaker',70,5),'clips':clips('Shaker',E['Shaker'])},
 {'name':'Snare roll','preset':'zsnare','color':'#ff7ac8','vol':.4,'inst':{},'fx':[RVB(1.5,18)],'clips':clips('Roll',E['Snare roll'],ramp(ROLL,.55,1.0))},
]
json.dump(T,open('compose.json','w'))
print({t['name']:sum(len(c['notes']) for c in t['clips']) for t in T})
