"""AudioLab psytrance track v5 ("Fractals" structure, original music). 148 BPM, A minor.
Everything here is written from research notes (see the project doc "psytrance-production-brief"):
 - kick + rolling bass as one pulse: short tuned kick, sine sub + filtered saw top, identical notes, quiet first note
 - groove from hats/shaker/percussion only (swing 56 %, accents, ghost notes); kick and clap stay on the grid
 - lead as question and answer: the question stops on the 2nd or 7th degree and leaves a gap, the answer repeats
   its opening and lands on the tonic; two different voices take the two halves
 - every transition is one gesture: riser + roll + gap -> impact + boom + crash + downlifter, lead pickup into the 1
"""
import json,numpy as np
BPM=148.0;NB=288
bar=lambda b:(b-1)*4.0
rng=np.random.default_rng(11)
def inr(R,b):
    for r in R:
        if r[0]<=b<=r[1]:return r
    return None
# ------------------------------------------------------------------ arrangement
SECTIONS=[('Intro',1,16,'#4cc9f0'),('Filtered groove',17,12,'#7a8bff'),('Break',29,4,'#b583ff'),('Drop 1',33,16,'#ff6b6b'),('Groove',49,20,'#ff9a3c'),('Mini break',69,4,'#b583ff'),
 ('Full',73,16,'#f5c84c'),('Part 2',89,16,'#ff6b6b'),('Part 2 full',105,16,'#f5c84c'),('Breakdown',121,16,'#b583ff'),('Build',137,8,'#ff7ac8'),('Drop 2',145,16,'#ff6b6b'),
 ('Peak',161,32,'#ff4d6d'),('Break 2',193,16,'#b583ff'),('Final',209,48,'#ff4d6d'),('Reprise',257,16,'#f5c84c'),('Outro',273,16,'#3ecf8e')]
KICK=[(17,28),(33,70),(73,120),(137,142),(145,175),(177,192),(209,284)]
GAP={48:8,88:8,104:8,120:12,160:8,192:8,224:8,240:8,256:8,272:12}       # bar -> first silent 16th (kick and bass stop, fill takes over)
DROPS=[17,33,49,73,89,105,145,161,177,209,225,241,257]                  # bars that start with an impact
BIG=[33,73,145,209]                                                    # drops after a break
LVL=[(17,20,1),(21,28,2),(33,40,2),(41,56,3),(57,68,4),(69,70,2),(73,80,4),(81,88,5),(89,96,'B'),(97,104,'B2'),(105,120,5),(137,142,1),
     (145,152,3),(153,160,4),(161,175,5),(177,192,5),(209,224,4),(225,256,5),(257,264,3),(265,280,2),(281,284,1)]
CHF=[(161,192),(209,256)]                    # the bass follows the chords here
LEADA=[(57,64),(73,88),(161,176),(209,224),(241,256)]      # main question/answer melody
LEADB=[(105,120),(177,192),(225,240)]                      # offbeat variation
SEQ=[(9,16),(33,48),(65,68),(73,88),(105,120),(137,143),(145,160),(169,192),(209,224),(241,264),(273,280)]
ACID=[(41,56,1),(89,104,2),(145,160,2),(177,192,1),(225,240,2),(257,272,1)]
STAB=[(89,104),(161,176),(241,256)]
PADL=[(1,32),(121,144),(193,208),(273,288)]               # long chords (4 bars)
PADS=[(57,68),(73,88),(105,120),(161,192),(209,256),(257,272)]  # quiet bed under the leads (2 bars)
THEME=[(121,136,8),(193,204,6)]                            # breakdown theme: the melody at half speed (units of 2 bars)
CH=[('Am',[57,60,64]),('F',[53,57,60]),('G',[55,59,62]),('Am',[57,60,64])]
def chord(b,slow=False):return ((b-1)//(4 if slow else 2))%4
def lvl(b):
    r=inr(LVL,b);return r[2] if r else 0
def kick_on(b,st):
    if not inr(KICK,b):return False
    if b in GAP and st>=GAP[b]:return False
    return True
# ------------------------------------------------------------------ groove
def gv(t,sw=56,j=.003):
    """swing on the odd 16ths plus a little human timing; returns the new beat position"""
    st=int(round(t*4))
    if abs(t*4-st)<1e-6 and st%2==1:t+=(sw-50)/100*2*.25
    return round(max(0,t+rng.normal(0,j)),4)
def hv(v,j=.07):return round(float(np.clip(v*(1+rng.normal(0,j)),.05,1)),3)
E_={}
def add(tr,p,t,l,v):E_.setdefault(tr,[]).append((int(p),float(t),float(l),float(v)))
# ------------------------------------------------------------------ kick and bass
ROOT=[33,29,31,33]
for b in range(1,NB+1):
    if not inr(KICK,b):continue
    t0=bar(b);L=lvl(b);root=ROOT[chord(b)] if inr(CHF,b) else 33
    for st in range(16):
        if not kick_on(b,st):continue
        if st%4==0:add('Kick',36,t0+st/4,.25,1.0)
        else:
            if L=='B' and st%8 in (5,):continue                       # Part 2: one note out per half bar = a hole the percussion fills
            p=root;v=.5 if st%4==1 else 1.0
            if b%8==4 and st==15:continue                              # breath: last 16th muted every 8 bars
            if b%8==0 and b not in GAP and st in (13,15):p=root+12     # octave flick at the end of each 8-bar phrase
            add('Bass sub',p,t0+st/4,.13,v);add('Bass top',p,t0+st/4,.13,v)
    if b%16==0 and b not in GAP and inr(KICK,b+1):                     # pickup kick before a 16-bar change
        add('Kick',36,t0+3.5,.25,.8)
        for k in ('Bass sub','Bass top'):E_[k]=[n for n in E_[k] if not (abs(n[1]-(t0+3.5))<.01 or abs(n[1]-(t0+3.25))<.01)]
# ------------------------------------------------------------------ drums
HB=[0,.42,0,.34,0,.5,0,.36,0,.44,0,.32,0,.52,0,.4]     # ghost 16ths between the offbeats
TOMF=[[(10,45),(12,43),(13,43),(14,40),(15,38)],[(8,47),(10,45),(11,45),(13,43),(14,40),(15,40)],[(12,45),(13,47),(14,43),(15,40)]]
CONGA=[[(3,62,.8),(6,60,.6),(11,62,.9),(14,60,.7)],[(3,62,.8),(6,60,.6),(9,62,.5),(11,64,.9),(14,60,.7),(15,62,.45)]]
for b in range(1,NB+1):
    L=lvl(b);t0=bar(b)
    if not L:continue
    fill=(b%8==0);gap=GAP.get(b,16)
    n=L if isinstance(L,int) else 3
    for st in range(16):
        if st>=gap:break
        t=t0+st/4
        if n>=2 and L!='B':
            if st%4==2:add('Hat',60,gv(t,50),.1,hv(.92 if st in (2,10) else .82))         # offbeat 8ths: the drive
            elif st%2==1:add('Hat ghost',60,gv(t),.08,hv(HB[st]*(1.25 if n>=4 else 1)))
            elif n>=5 and st%4==0:add('Hat ghost',60,gv(t,50),.08,hv(.3))
        if n==1 and st%4==2 and b>=19:add('Hat ghost',60,gv(t,50),.08,hv(.35))
        if (n>=3 or L in('B','B2')) and st%4==2:add('Open hat',60,gv(t-.01,50,.002),.2,hv(.85 if st in (2,10) else .7,.04))
        if n>=3 and st in (4,12):
            add('Clap',60,t,.2,1.0);add('Snare',60,t,.15,.9)
        if n>=3 and ((st==15 and b%2==0) or (st==7 and b%4==0)):add('Snare',60,gv(t),.1,hv(.22))   # ghost before the beat
        if n>=4:add('Shaker',60,gv(t),.1,hv([.3,.55,.9,.55][st%4]))
        if n>=5 and st%4==2:add('Ride',51,gv(t,50),.3,hv(.7))
    if n>=4 or L in('B','B2'):
        for st,p,v in CONGA[(b-1)%2]:
            if st<gap:add('Congas',p,gv(t0+st/4,54),.2,hv(v*(1.1 if L in('B','B2') else .9)))
    if L in('B','B2'):
        for st,p,v in [(7,43,.8),(10,45,.6)] if b%2 else [(5,40,.7),(7,43,.8),(13,45,.6)]:add('Toms',p,gv(t0+st/4,54),.2,hv(v))
        if L=='B2':
            for st in range(16):
                if st%2==1:add('Hat ghost',60,gv(t0+st/4),.08,hv(HB[st]))
    if fill and n>=2 and gap==16:
        for st,p in TOMF[(b//8)%3]:add('Toms',p,t0+st/4,.2,hv(.7+.02*st,.03))
        add('Open hat',60,t0+3.75,.2,.6)
# crashes on drops, a softer one every 16 bars inside long sections
for d in DROPS:add('Crash',49,bar(d),2,1.0)
for b in range(1,NB+1):
    if b%16==1 and b not in DROPS and lvl(b) and lvl(b)!=1:add('Crash',49,bar(b),2,.6)
# snare rolls: long before the big drops, half a bar inside the gaps
def roll(b0,b1,stop=16):
    nb=b1-b0+1
    for k in range(nb):
        div=[2,4,4,8][min(3,k*4//nb)] if nb>1 else 4
        for j in range(4*div):
            st16=j*4/div
            if k==nb-1 and st16>=stop:break
            x=(k*4+j/div)/(nb*4)
            add('Snare roll',60,bar(b0+k)+j/div,.1,round(.3+.7*x,3))
roll(31,32,14);roll(71,72,14);roll(141,144,8);roll(205,208,14)
for b,g in GAP.items():
    for st in range(g,16):
        add('Snare roll',60,bar(b)+st/4,.1,round(.45+.5*(st-g)/(16-g),3))
        if st>=14:add('Snare roll',60,bar(b)+st/4+.125,.1,round(.5+.5*(st-g)/(16-g),3))
# ------------------------------------------------------------------ lead: question and answer
R332=[(0,3),(3,3),(6,2),(8,3),(11,3),(14,2)]
def unit(p6,p3,last,hold):
    """two bars: six notes in 3-3-2, three more, then the note the phrase stops on"""
    ev=[(st,l,p) for (st,l),p in zip(R332,p6)]
    ev+=[(16+st,l,p) for (st,l),p in zip(R332[:3],p3)]
    ev.append((24,hold,last));return ev
MEL=[('Q',unit([69,72,76,76,74,72],[72,74,76],71,6)),      # Am: climbs, stops on B (2nd degree) -> asks
     ('A',unit([69,72,77,77,76,72],[72,74,72],69,7)),      # F : same opening, lands on A -> answers
     ('Q',unit([71,74,79,79,77,74],[74,76,77],79,6)),      # G : higher, stops on G (7th) -> asks again
     ('A',unit([81,79,76,76,74,72],[72,71,68],69,8))]      # Am: peak note first, G sharp leads home to A
OFF=[2,6,10,14]
def unitB(p4,p3,last):
    ev=[(st,3,p) for st,p in zip(OFF,p4)]+[(16+st,3,p) for st,p in zip(OFF[:3],p3)]
    ev.append((26,6,last));return ev
MELB=[('Q',unitB([76,76,74,76],[72,72,74],71)),('A',unitB([77,77,76,77],[72,72,74],69)),
      ('Q',unitB([79,79,77,79],[74,76,79],83)),('A',unitB([81,81,79,81],[76,72,68],69))]
def lead_notes(R,M):
    for a,c in R:
        for b in range(a,c+1,2):
            who,ev=M[((b-a)//2)%4];t0=bar(b)
            for st,l,p in ev:
                long=l>=6;v=1.0 if (st%16 in (0,8) or long) else .8
                tr='Lead question' if who=='Q' else 'Lead answer'
                ln=(l/4)*(.97 if long else (.62 if p<72 else .8))      # low notes shorter, high notes longer
                add(tr,p,t0+st/4,ln,v)
                add('Lead body',p-12,t0+st/4,ln*.9,v*.9)
                if long or st%16 in (0,8):add('Lead air',p+12,t0+st/4,ln,v*.8)
lead_notes(LEADA,MEL);lead_notes(LEADB,MELB)
# pickup: three 16ths that walk into the first note of the melody after a gap or a break
for a,c in LEADA+LEADB:
    if a-1 in GAP or a in BIG or a in (161,241):
        for k,p in enumerate([64,67,68]):add('Lead question',p,bar(a)-.75+k/4,.2,.7+.1*k)
# breakdown theme: the same melody at half speed, soft voice
for a,c,nu in THEME:
    for u in range(nu):
        who,ev=MEL[u%4];t0=bar(a+u*2)
        for st,l,p in ev:add('Theme',p,bar(a)+u*16+st/2,l/2*.95,.9 if l>=6 else .75)
# build 137-144: the question's first three notes, repeated, then a climbing roll into the gap
for b in range(137,141):
    for (st,l),p in zip(R332[:3],[69,72,76]):add('Lead question',p,bar(b)+st/4,l/4*.8,.8)
    for (st,l),p in zip(R332[3:],[76,74,72] if b%2 else [76,79,81]):add('Lead answer',p,bar(b)+st/4,l/4*.8,.8)
for i,p in enumerate([69,69,72,72,76,76,81,81,76,76,81,81,84,84,88,88,81,84,88,93,81,84,88,93]):
    add('Lead question',p,bar(141)+i*.5 if i<16 else bar(143)+(i-16)*.25,.2,.6+.4*i/24)
# ------------------------------------------------------------------ sequence, acid, stabs, pads
ARP={'Am':[81,76,72],'F':[81,77,72],'G':[83,79,74]}
for a,c in SEQ:
    for b in range(a,c+1):
        cyc=ARP[CH[chord(b)][0]]
        for st in range(16):
            if b in GAP and st>=GAP[b]:break
            g=(b-1)*16+st;add('Sequence',cyc[g%3],bar(b)+st/4,.17,.9 if st%4==2 else .62)
AX={'Am':dict(X=48,Y=52,Z=55),'F':dict(X=48,Y=53,Z=57),'G':dict(X=47,Y=50,Z=55)}
AP={1:"R- .- O+ R- .- R- X+ R~ Y- R- O+ .- R- R~ Z+ Y-".split(),2:"R+ O~ Z- R- X+ R- .- O~ Y+ O- R- X+ R- .- Y~ Z+".split()}
TURN="O+ Z~ Y- X~".split()
for a,c,k in ACID:
    for b in range(a,c+1):
        pat=list(AP[k]);ax=AX[CH[chord(b)][0]]
        if (b-a)%4==3:pat[12:]=TURN
        for st,s in enumerate(pat):
            if s[0]=='.' or (b in GAP and st>=GAP[b]):continue
            p={'R':45,'O':57}.get(s[0]) or ax[s[0]]
            add('Acid',p,bar(b)+st/4,.25*(1.3 if s[1]=='~' else .55),.95 if s[1]=='+' else .7)
SR_=[0,3,6,8,11,13]
for a,c in STAB:
    for b in range(a,c+1):
        if a==89 and (b-a)%2==1:continue                               # Part 2: stabs call in the odd bars, zaps and acid answer in the even ones
        ch=CH[chord(b)][1]
        for st in SR_:
            if b in GAP and st>=GAP[b]:break
            for p in ch+[ch[0]+12]:add('Stabs',p,bar(b)+st/4,.16,.9 if st in (0,8) else .7)
for a,c in PADL:
    for b in range(a,c+1,4):
        ch=CH[chord(b,True)][1]
        for p in ch+[ch[0]+12,ch[0]-12]:add('Pad',p,bar(b),15.8,1.0)
for a,c in PADS:
    for b in range(a,c+1,2):
        ch=CH[chord(b)][1];ln=7.8 if not (b+1 in GAP) else 4+GAP[b+1]/4-.2
        for p in ch+[ch[0]+12]:add('Pad',p,bar(b),ln,.42)
# ------------------------------------------------------------------ effects that hand over to each other
def trans(d,big):
    n=8 if big else 4
    add('Riser',57,bar(d-n),n*4,.9)                                    # rises to the drop ...
    add('Uplifter',69,bar(d-2),8,.85)
    add('Reverse crash',60,bar(d)-4,4,.85)                             # ... the reversed crash arrives on the 1 ...
    add('Impact',45,bar(d),2,1.0);add('Sub boom',33,bar(d),4,.9)       # ... impact, boom and crash land together ...
    add('Downlifter',57,bar(d),8,.8)                                   # ... and the downlifter carries the energy back down
    add('Zaps',81,bar(d)+1.5,1,.6)
for d in DROPS:trans(d,d in BIG)
add('Reverse crash',60,bar(121)-4,4,.8);add('Impact',45,bar(121),2,.9);add('Downlifter',57,bar(121),16,.9);add('Sub boom',33,bar(121),4,.9)
add('Reverse crash',60,bar(193)-4,4,.8);add('Impact',45,bar(193),2,.9);add('Downlifter',57,bar(193),16,.9);add('Sub boom',33,bar(193),4,.9)
add('Sweep',57,bar(137),32,.8);add('Sweep',57,bar(201),32,.8);add('Sweep',57,bar(9),32,.6)
# zaps answer the melody: in the hole after the answer's last note (bar 8 of each phrase), tuned to the chord
ZP=[81,76,84,88]
for a,c in LEADA+LEADB+STAB:
    for b in range(a,c+1):
        if b%8==0 and b not in GAP:add('Zaps',ZP[(b//8)%4],bar(b)+2.5,1,.75);add('Zaps',ZP[(b//8+1)%4],bar(b)+3.25,.5,.5)
        if b%8==4:add('Pew',ZP[(b//8)%4]-12,bar(b)+3.5,.5,.5)
for b in range(89,105):
    if (b-89)%2==1:add('Zaps',[81,84,88,76][((b-89)//2)%4],bar(b)+.75,.75,.7);add('Pew',69,bar(b)+2.75,.5,.55)
for a,c in [(1,16),(121,136),(193,204),(281,288)]:add('Wind',57,bar(a),(c-a+1)*4,.7)
# ------------------------------------------------------------------ recipe
def clips(name,blk=8,env=None):
    by={}
    for p,s,l,v in sorted(E_.get(name,[]),key=lambda n:n[1]):by.setdefault(int(s//(blk*4)),[]).append((p,s,l,v))
    out=[]
    for k in sorted(by):
        s0=k*blk*4;c={'start':s0,'len':blk*4,'name':f'{name} {k*blk+1}','notes':[{'p':p,'s':round(s-s0,4),'l':round(min(l,blk*4-(s-s0)) if name not in('Pad','Riser','Sweep','Wind','Downlifter','Theme','Uplifter') else l,4),'v':round(v,3)} for p,s,l,v in by[k]]}
        mx=max(n['s']+n['l'] for n in c['notes'])
        if mx>c['len']:c['len']=float(np.ceil(mx/4)*4)
        if env:
            e=env(k*blk+1,blk)
            if e:c['env']=e;c['envShow']=None
        out.append(c)
    return out
def ramp(R,lo,hi,key='cut'):
    """clip filter (0..1 = 30 Hz..20 kHz) or volume that moves from lo to hi across each range in R"""
    def f(b0,blk):
        r=inr(R,b0) or inr(R,b0+blk-1)
        if not r:return None
        return {key:[{'b':i*4,'v':round(float(lo+(hi-lo)*np.clip((b0+i-r[0])/max(1,r[1]-r[0]+1),0,1)),3)} for i in range(blk+1)]}
    return f
def plant(**k):
    b=dict(w1='sawtooth',w2='sawtooth',morph=0,uni=1,det=0,width=0,cut=4000,res=.5,fenv=0,a=.003,d=.2,s=.5,r=.1,lfo=.3,lamt=0,space=0,sub=0,noise=0,fm=0,ratio=2,gain=.5);b.update(k);return b
sfx=lambda kind,tone=60,space=35,gain=.5:{'kind':kind,'tone':tone,'space':space,'gain':gain}
FXp=lambda t,**p:{'type':t,'p':p}
HP=lambda f:{'type':'eq','p':{'an':'off','bands':[{'t':'highpass','f':f,'q':.7,'on':True,'sl':24}]}}
PUMP=lambda d,sh=45:FXp('side',depth=d,shape=sh,punch=0,sustain=0,sync='1/4')
def T(name,preset,inst,color,icon,grp=None,fx=None,pan=0,env=None,sends=None,blk=8,kind=None,vol=.8):
    t={'name':name,'color':color,'icon':icon,'vol':vol,'pan':pan,'fx':fx or []}
    if kind:t['kind']=kind
    else:t.update(preset=preset,inst=inst,clips=clips(name,blk,env))
    if grp:t['grp']=grp
    g=GAIN.get(name)
    if g and not kind:
        e=float(np.clip(g,-12,12));r=g-e
        if abs(r)>.01 and isinstance(t.get('inst'),dict) and 'gain' in t['inst']:t['inst']=dict(t['inst'],gain=round(t['inst']['gain']*10**(r/20),4))
        t['fx']=t['fx']+[{'type':'eq','p':{'an':'off','out':round(e,2)}}]
    if sends:t['sends']=sends
    return t
GAIN={'Kick':7.3,'Bass sub':5.7,'Bass top':-6.2,'Clap':0,'Snare':-.6,'Hat':-6.2,'Hat ghost':-7.2,'Open hat':-2.7,'Shaker':-14.4,'Ride':5.6,'Congas':-7.5,'Toms':-10.2,'Crash':6,'Snare roll':-4.3,
 'Lead question':7,'Lead answer':7.5,'Lead body':2,'Lead air':-.6,'Theme':5,'Sequence':3,'Acid':1.5,'Stabs':1,'Pad':-1.3,'Riser':2.5,'Uplifter':-2,'Sweep':3.6,'Reverse crash':2,'Impact':1.5,'Sub boom':4.7,'Downlifter':1,'Zaps':-4.6,'Pew':-3,'Wind':22}
try:GAIN.update(json.load(open('gain.json')))
except Exception:pass
RV='Reverb (shared)';DL='Delay (shared)'
def tracks():
    return [
 T('Kick & Bass',0,0,'#ff6b6b','activity',kind='group',fx=[FXp('drive',drive=8,mix=100),FXp('comp',threshold=-10,ratio=1.5,attack=30,release=100,makeup=0),{'type':'eq','p':{'an':'off','out':1.5}}]),
 T('Kick','kick',dict(tune=33,start=2400,sweep=.045,bend=82,len=.145,tail=34,click=55,drive=12,ctype='snap',kt=False,gain=.9),'#ff6b6b','drum','Kick & Bass',
   env=ramp([(17,28)],.5,.92) if False else (lambda b0,blk:(ramp([(17,28)],.52,.95)(b0,blk) or ramp([(137,142)],.45,.85)(b0,blk) or ramp([(273,284)],.95,.5)(b0,blk)))),
 T('Bass sub','plant',plant(w1='sine',w2='sine',cut=6000,res=.1,a=.002,d=.075,s=0,r=.03,gain=.6),'#4c8dff','t-wave-sine','Kick & Bass',fx=[PUMP(60,22)]),
 T('Bass top','plant',plant(w1='sawtooth',w2='square',morph=.12,cut=430,res=2.2,fenv=27,a=.001,d=.055,s=0,r=.03,gain=.5),'#4cc9f0','t-wave-saw-tool','Kick & Bass',
   fx=[HP(85),FXp('drive',drive=22,mix=100),PUMP(60,22)],
   env=lambda b0,blk:(ramp([(17,28)],.42,.8)(b0,blk) or ramp([(137,142)],.4,.75)(b0,blk) or ramp([(33,48),(49,68),(73,88),(89,104),(105,120),(145,160),(161,192),(209,224),(225,256)],.72,.9)(b0,blk) or ramp([(257,284)],.85,.45)(b0,blk))),
 T('Drums',0,0,'#f5c84c','t-metronome',kind='group',fx=[FXp('comp',threshold=-20,ratio=2,attack=25,release=120,makeup=1),FXp('imager',x1=150,x2=1000,x3=5000,w1=100,w2=120,w3=150,w4=180,mg=0,sg=0,out=0,bmono=False,solo=0)]),
 T('Clap','zclap',dict(bursts=5,spread=12,bd=6,tail=.2,freq=1500,q=1.6,room=35,drive=18,gain=.8),'#f5c84c','asterisk','Drums',sends={RV:.2}),
 T('Snare','zsnare',dict(tune=220,sweep=50,body=50,tone=50,snap=100,nhp=3500,nd=.14,rattle=55,click=65,dec=.16,drive=45,gain=.8),'#ff9a3c','target','Drums'),
 T('Hat','zhat',dict(pitch=9,tone=9500,hp=7800,noise=22,dec=.045,drive=12,gain=.7),'#3ecf8e','disc','Drums',pan=-.2),
 T('Hat ghost','zhat',dict(pitch=11,tone=10500,hp=9000,noise=14,dec=.026,drive=10,gain=.7),'#3ecf8e','disc-2','Drums',pan=.22,fx=[FXp('chorus',rate=.7,depth=35,delay=7,fb=0,width=100,mix=30)]),
 T('Open hat','zhat',dict(pitch=10,tone=10000,hp=7000,noise=24,dec=.2,drive=18,gain=.7),'#3ecf8e','disc-3','Drums',pan=.05,sends={RV:.1}),
 T('Shaker','zhat',dict(pitch=7,tone=6500,hp=5000,noise=85,dec=.08,drive=5,gain=.7),'#8b8f9c','hourglass','Drums',pan=.3,fx=[FXp('chorus',rate=.5,depth=35,delay=9,fb=0,width=100,mix=35)]),
 T('Ride','drums',{},'#4cc9f0','bell','Drums',pan=-.2),
 T('Congas','ztom',dict(kt=1,tune=310,sweep=20,body=90,skin=60,click=55,noise=15,dec=.2,drive=10,gain=.8),'#ff7ac8','cylinder','Drums',pan=-.3,sends={RV:.1}),
 T('Toms','ztom',dict(kt=1,tune=120,sweep=80,body=100,skin=30,click=60,noise=10,dec=.2,drive=45,gain=.8),'#b583ff','cuboid','Drums',pan=.15,sends={RV:.1}),
 T('Crash','drums',{},'#4cc9f0','bell-ring','Drums',sends={RV:.2}),
 T('Snare roll','zsnare',dict(tune=200,sweep=45,body=60,tone=50,snap=85,nhp=2600,nd=.15,rattle=45,click=45,dec=.16,drive=25,gain=.8),'#ff7ac8','repeat','Drums',sends={RV:.22},
   env=lambda b0,blk:ramp([(31,32),(71,72),(141,144),(205,208)],.6,1.0)(b0,blk)),
 T('Music',0,0,'#7a8bff','music',kind='group',fx=[PUMP(42,42),FXp('ott',depth=22,time=160,up=30,down=35,lo=0,mid=0,hi=0,out=0),{'type':'eq','p':{'an':'off','out':-1.5}}]),
 T('Lead question','plant',plant(uni=3,det=12,width=55,cut=2600,res=2.2,fenv=46,a=.003,d=.24,s=.45,r=.14,gain=.5),'#4cc9f0','message-circle','Music',pan=-.12,
   fx=[HP(180),FXp('phaser',rate=.22,depth=60,fb=40,mix=38),FXp('ott',depth=38,time=120,up=55,down=50,lo=0,mid=0,hi=1,out=0),FXp('tdelay',sync='1/8 dotted',feedback=42,mix=24,lowcut=350,highcut=6500,drive=10,wow=8,rate=.6,width=100,ping=True)],
   sends={RV:.22},env=lambda b0,blk:(ramp([(137,144)],.6,.95)(b0,blk) or ramp([(57,64)],.78,.93)(b0,blk))),
 T('Lead answer','plant',plant(w1='square',w2='sawtooth',morph=.45,uni=2,det=9,width=45,cut=3000,res=1.6,fenv=40,a=.004,d=.3,s=.5,r=.18,fm=12,ratio=2,gain=.5),'#ffd166','megaphone','Music',pan=.14,
   fx=[HP(180),FXp('chorus',rate=.5,depth=40,delay=9,fb=0,width=90,mix=35),FXp('ott',depth=34,time=120,up=50,down=50,lo=0,mid=0,hi=1,out=0),FXp('tdelay',sync='1/8',feedback=38,mix=22,lowcut=350,highcut=7000,drive=10,wow=8,rate=.6,width=100,ping=True)],
   sends={RV:.24,DL:.12},env=lambda b0,blk:ramp([(137,144)],.6,.95)(b0,blk)),
 T('Lead body','plant',plant(cut=1300,res=.8,fenv=30,a=.004,d=.22,s=.5,r=.12,gain=.5),'#4c8dff','audio-waveform','Music',fx=[HP(120)]),
 T('Lead air','plant',plant(w1='triangle',w2='sawtooth',morph=.3,cut=7000,res=.5,a=.01,d=.3,s=.6,r=.3,gain=.4),'#cfd3db','star','Music',
   fx=[HP(900),FXp('tdelay',sync='1/8 dotted',feedback=55,mix=45,lowcut=900,highcut=9000,drive=0,wow=5,rate=.6,width=100,ping=True)],sends={RV:.3}),
 T('Theme','plant',plant(uni=3,det=14,width=80,cut=3200,res=.8,a=.18,d=.6,s=.85,r=1.1,lamt=6,lfo=5.2,gain=.45),'#b583ff','moon','Music',
   fx=[HP(200),FXp('tdelay',sync='1/4 dotted',feedback=45,mix=26,lowcut=300,highcut=6000,drive=10,wow=10,rate=.6,width=100,ping=True)],sends={RV:.4}),
 T('Sequence','plant',plant(w1='square',w2='sawtooth',morph=.4,cut=2400,res=3,fenv=55,a=.001,d=.09,s=.1,r=.05,gain=.5),'#9be564','list-music','Music',pan=.2,
   fx=[HP(300),FXp('tdelay',sync='1/8',feedback=30,mix=24,lowcut=600,highcut=8000,drive=5,wow=5,rate=.6,width=100,ping=True)],sends={RV:.1},
   env=lambda b0,blk:(ramp([(9,16)],.45,.7)(b0,blk) or ramp([(137,143)],.5,.9)(b0,blk) or ramp([(273,280)],.8,.5)(b0,blk) or ramp(SEQ,.6,.92)(b0,blk))),
 T('Acid','acid',dict(wave='sawtooth',cut=420,res=20,env=76,dec=.14,acc=70,slide=.035,dist=45,gain=.35),'#ff9a3c','biohazard','Music',pan=-.18,
   fx=[HP(150),FXp('chorus',rate=.4,depth=30,delay=8,fb=0,width=100,mix=25),FXp('tdelay',sync='1/8 dotted',feedback=24,mix=14,lowcut=400,highcut=5000,drive=10,wow=5,rate=.6,width=100,ping=True)],env=lambda b0,blk:ramp([(a,c) for a,c,_ in ACID],.6,.95)(b0,blk)),
 T('Stabs','plant',plant(uni=7,det=24,width=100,cut=3800,res=.6,fenv=30,a=.002,d=.12,s=.25,r=.07,gain=.4),'#ff7ac8','t-wave-square','Music',
   fx=[HP(250),FXp('phaser',rate=.12,depth=50,fb=30,mix=30)],sends={RV:.2,DL:.18},env=lambda b0,blk:ramp(STAB,.66,.9)(b0,blk)),
 T('Pad','plant',plant(uni=5,det=18,width=100,cut=1700,res=.3,a=1.0,d=.8,s=1,r=2.2,lamt=10,lfo=.15,gain=.4),'#7a8bff','cloud','Music',fx=[HP(160)],sends={RV:.4},
   env=lambda b0,blk:(ramp([(1,28)],.58,.82)(b0,blk) or ramp([(121,144)],.6,.9)(b0,blk) or ramp([(193,208)],.6,.9)(b0,blk) or ramp([(273,288)],.8,.5)(b0,blk))),
 T('FX',0,0,'#f5c84c','sparkles',kind='group',fx=[PUMP(28,40)]),
 T('Riser','sfx',sfx('riser',60,30),'#f5c84c','rocket','FX',blk=4),
 T('Uplifter','sfx',sfx('uplift',55,30),'#f5c84c','plane','FX',blk=4),
 T('Sweep','sfx',sfx('sweep',55,40),'#cfd3db','waves-vertical','FX',blk=4),
 T('Reverse crash','sfx',sfx('revcrash',65,20),'#3ecf8e','tornado','FX',blk=4),
 T('Impact','sfx',sfx('impact',55,45),'#ff4d6d','hammer','FX'),
 T('Sub boom','sfx',sfx('boom',50,10),'#ff4d6d','waves','FX'),
 T('Downlifter','sfx',sfx('downer',55,40),'#3ecf8e','cloud-rain','FX',blk=4),
 T('Zaps','sfx',sfx('laser',60,30),'#ff7ac8','zap','FX',pan=-.25,sends={DL:.45,RV:.15}),
 T('Pew','sfx',sfx('pew',60,30),'#ff7ac8','crosshair','FX',pan=.25,sends={DL:.4,RV:.15}),
 T('Wind','sfx',sfx('wind',50,40),'#8b8f9c','wind','FX',blk=4),
 T(RV,0,0,'#b583ff','mountain',kind='return',fx=[FXp('reverb',decay=2.8,predelay=25,damp=6500,lowcut=350,mix=100),PUMP(45,45)]),
 T(DL,0,0,'#b583ff','infinity',kind='return',fx=[FXp('tdelay',sync='1/8 dotted',feedback=48,mix=100,lowcut=400,highcut=6000,drive=15,wow=12,rate=.6,width=100,ping=True),PUMP(45,45)]),
 ]
MFX=[FXp('comp',threshold=-12,ratio=2,attack=30,release=150,makeup=0),FXp('clip',gain=3.0,thr=-4,ceil=-.3,shape='tanh',os='4x',bias=0,mix=100,out=0)]
try:MFX=json.load(open('mfx.json'))
except Exception:pass
def recipe():
    return {'bpm':BPM,'name':'Fractals remake v5','sections':[{'name':n,'start':bar(a),'len':l*4,'color':c} for n,a,l,c in SECTIONS],'tracks':tracks(),'mfx':MFX}
if __name__=='__main__':
    R=recipe();print(len(R['tracks']),'tracks');print({t['name']:sum(len(c['notes']) for c in t.get('clips',[])) for t in R['tracks']})
