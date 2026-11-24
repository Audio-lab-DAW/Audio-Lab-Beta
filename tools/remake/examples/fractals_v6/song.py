"""Fractals remake v6: melodic full-on psytrance at 145 BPM in A minor, written from the project doc "psytrance-rules-in-numbers"
(checklist numbers in brackets). Rule of this version: few parts, one melodic idea at a time, bass fixed on the root."""
import json,numpy as np
BPM=145.0;NB=288
bar=lambda b:(b-1)*4.0
def inr(R,b):
    for r in R:
        if r[0]<=b<=r[1]:return r
    return None
SECTIONS=[('Intro',1,16,'#4cc9f0'),('Kick and bass',17,12,'#7a8bff'),('Break',29,4,'#b583ff'),('Drop 1',33,16,'#ff6b6b'),('Groove',49,20,'#ff9a3c'),('Short break',69,4,'#b583ff'),
 ('Full',73,16,'#f5c84c'),('Part 2: hooks',89,16,'#ff6b6b'),('Part 2: lead',105,16,'#f5c84c'),('Breakdown',121,16,'#b583ff'),('Build',137,8,'#ff7ac8'),('Drop 2',145,16,'#ff6b6b'),
 ('Peak',161,32,'#ff4d6d'),('Break 2',193,16,'#b583ff'),('Final',209,48,'#ff4d6d'),('Reprise',257,16,'#f5c84c'),('Outro',273,16,'#3ecf8e')]
KICK=[(17,31),(33,70),(73,120),(145,192),(209,288)]
BIG=[33,73,145,209]                      # drops after a break: the bar before has no kick or bass, fill on beats 1-2, silence on 3-4 [53]
DROPS=[33,49,73,89,105,145,161,177,209,225,241,257]
HATS=[(25,31),(33,70),(73,120),(145,192),(209,280)]          # closed hats [20]
CLAP=[(33,68),(73,120),(145,192),(209,272)]                  # clap + snare on 2 and 4 [19]
OPEN=[(41,68),(73,88),(105,120),(153,192),(209,264)]         # open hat on the offbeat [21]
PERC=[(49,68),(73,88),(97,120),(161,192),(209,256)]          # syncopated percussion [22]
SHAK=[(241,256)]                                             # the climax's one extra layer
LEAD=[(57,68),(73,88),(105,120),(145,160),(177,192),(209,224),(241,256)]   # main question/answer melody
LEADF=[(129,144),(197,208)]                                  # the same melody low-passed in the breaks
LOWONLY=[(257,272)]                                          # lead stripped: only the octave-down layer [39]
UPPER=[(177,192),(209,224),(241,256)]                        # upper copy +12 [34]
HOOK=[(89,104),(161,176),(225,240)]                          # two short hooks answering each other, left and right [39]
ARP=[(41,56)]                                                # first hook: root-fifth-octave cell
ACID=[(161,192),(225,256)]                                   # peak only [43]
PADS=[(1,16),(29,32),(121,144),(193,208)]
E_={}
def add(tr,p,t,l,v):E_.setdefault(tr,[]).append((int(p),float(t),float(l),float(v)))
ST=.25
def gapbar(b):return (b+1) in BIG
# ---------------- kick and bass [5-18]
for b in range(1,NB+1):
    if not inr(KICK,b):continue
    t0=bar(b)
    for st in range(16):
        if gapbar(b):continue
        if b%16==8 and st>=12:continue                         # bar 8 of each 16: last beat without kick and bass [26]
        if st%4==0:add('Kick',36,t0+st*ST,.25,1.0)
        else:
            if b%4==0 and st==15:continue                      # silence the last 16th every 4th bar [18]
            add('Bass',33,t0+st*ST,.145,.8 if st%4==1 else 1.0)
# ---------------- drums [19-27]
HV=[.47,.63,.9,.63]
for b in range(1,NB+1):
    t0=bar(b);g=gapbar(b)
    if inr(HATS,b) and not g:
        for st in range(16):
            if b%16==8 and st>=12:break
            if inr(OPEN,b) and st%4==2:add('Open hat',60,t0+st*ST,.2,.85)
            else:add('Hat',60,t0+st*ST,.08,HV[st%4])
    if inr(CLAP,b) and not g:
        for st in (4,12):
            if b%16==8 and st>=12:continue
            add('Clap',60,t0+st*ST,.2,1.0);add('Snare',60,t0+st*ST,.15,.9)
        for st in (3,11):add('Snare',60,t0+st*ST,.1,.4)         # ghost before beats 2 and 4 [24]
    if inr(PERC,b) and not g:
        for st,p in zip((3,6,7,10,11,12),(62,60,62,60,62,64)):
            if not(b%16==8 and st>=12):add('Percussion',p,t0+st*ST,.2,.75 if st in(3,10) else .6)
    if inr(SHAK,b) and not g:
        for st in range(16):add('Shaker',60,t0+st*ST,.1,[.3,.55,.9,.55][st%4])
    if inr(KICK,b) and b%16==8:
        add('Toms',45,t0+3.0,.2,.8);add('Toms',40,t0+3.5,.2,.9)  # two tom hits [26]
    if b%16==1 and inr(KICK,b) and b>17:add('Crash',49,t0,2,1.0 if b in DROPS else .65)   # [25]
def roll(b0):
    """4-bar roll: 8ths, 16ths, 16ths, 32nds; quiet to loud; in-between hits softer [52]. Ends after beat 2 of the last bar."""
    for k,div in enumerate([2,4,4,8]):
        for j in range(4*div):
            if k==3 and j>=2*div:break
            x=(k*4+j/div)/14;on=(j%div==0)
            add('Snare roll',60,bar(b0+k)+j/div,.1,round((.15+.85*x)*(1 if on else .65),3))
for d in BIG:roll(d-4)
roll(69)
# ---------------- lead: question and answer [28-32]
A4,C5,D5,E5,F5,G5,Gs5,A5,Bb5=69,72,74,76,77,79,80,81,82
S=.5   # short note = half a step
def mel(end):
    """8 bars. The low A is the call, the high notes are the response; low notes short, high notes longer."""
    q1=[(0,A4,S),(3,A4,S),(6,E5,2),(8,A4,S),(11,A4,S),(14,G5,1)]
    q2=[(0,A4,S),(3,A4,S),(6,G5,2),(8,A4,S),(11,F5,S),(14,E5,2)]          # stops on E, the fifth: a question
    a1=[(0,A4,S),(3,A4,S),(6,E5,2),(8,A4,S),(11,A4,S),(14,G5,1)]          # the answer starts like the question
    a2=[(0,A4,S),(3,A4,S),(6,Bb5,2),(8,A5,6)]                            # B flat falls onto the high A and stays: home
    a2b=[(0,A4,S),(3,A4,S),(6,Gs5,2),(8,A5,6)]                           # second time: G sharp rises onto A
    return [q1,q2,a1,a2,q1,q2,a1,a2b if end else a2]
MEL=mel(True)
def lead(R,tracks,vel=1.0):
    for a,c in R:
        for b in range(a,c+1):
            if gapbar(b):continue
            for st,p,l in MEL[(b-a)%8]:
                v=(1.0 if l>=2 else .8)*vel
                for tr,dp,dv in tracks:add(tr,p+dp,bar(b)+st*ST,l*ST*.95,v*dv)
lead(LEAD,[('Lead',0,1),('Lead low',-12,1)])
lead(LEADF,[('Lead',0,.9)])
lead(LOWONLY,[('Lead low',-12,1)])
lead(UPPER,[('Lead high',12,.9)])
# two short hooks, hard left and hard right, one bar each [39]
for a,c in HOOK:
    for b in range(a,c+1):
        if gapbar(b):continue
        if (b-a)%2==0:
            for st,p,l in [(0,A5,S),(3,G5,S),(6,E5,2)]:add('Hook left',p,bar(b)+st*ST,l*ST*.95,.9)
        else:
            for st,p,l in ([(0,E5,S),(3,G5,S),(6,A5,2)] if (b-a)%4==1 else [(0,E5,S),(3,Bb5,S),(6,A5,2)]):add('Hook right',p,bar(b)+st*ST,l*ST*.95,.9)
# first hook: root, fifth, octave, fifth in 16ths [3.4]
for a,c in ARP:
    for b in range(a,c+1):
        for st in range(16):
            if b%16==8 and st>=12:break
            add('Arp',[A4,E5,A5,E5][st%4],bar(b)+st*ST,S*ST,[1,.8,1,.9][st%4]*.9)
# acid on the root: accents and slides from the report's grid [43]
ACC="x.....x...x..x..";SLD="..x....x....x..x"
for a,c in ACID:
    for b in range(a,c+1):
        if gapbar(b):continue
        for st in range(16):
            if b%16==8 and st>=12:break
            acc=ACC[st]=='x';sl=SLD[st]=='x'
            add('Acid',57 if acc else 45,bar(b)+st*ST,ST*(1.3 if sl else .55),1.0 if acc else .7)
# pads: Am F C G, two bars each; last 8 bars before a drop F G Am Am [41-42]
CH={'Am':[57,60,64],'F':[57,60,65],'C':[55,60,64],'G':[55,59,62]}
def pad(a,c,prog):
    for i,b in enumerate(range(a,c+1,2)):
        for p in CH[prog[i%len(prog)]]:add('Pad',p,bar(b),7.9,.8)
pad(1,16,['Am','F','C','G']);pad(29,32,['F','G']);pad(121,136,['Am','F','C','G']);pad(137,144,['F','G','Am','Am']);pad(193,200,['Am','F','C','G']);pad(201,208,['F','G','Am','Am'])
# ---------------- effects: one gesture per change [45-47, 52-53]
for d in DROPS:
    big=d in BIG
    add('Riser',57,bar(d-8 if big else d-2),32 if big else 8,.9 if big else .6)
    add('Reverse crash',60,bar(d)-4,4,.85)
    add('Impact',45,bar(d),4,1.0 if big else .7);add('Downlifter',57,bar(d),4,.8)
for b in range(33,281,4):
    if inr(KICK,b) and b%16!=1:add('Blip',[81,76,84,88][(b//4)%4],bar(b)+3.5,.5,.6)    # one small blip every 4 bars
for a,c in [(1,16),(121,136),(193,200)]:add('Wind',57,bar(a),(c-a+1)*4,.7)
# ---------------- recipe
def clips(name,blk=8,env=None):
    by={}
    for p,s,l,v in sorted(E_.get(name,[]),key=lambda n:n[1]):by.setdefault(int(s//(blk*4)),[]).append((p,s,l,v))
    out=[]
    for k in sorted(by):
        s0=k*blk*4;c={'start':s0,'len':blk*4,'name':f'{name} {k*blk+1}','notes':[{'p':p,'s':round(s-s0,4),'l':round(l,4),'v':round(v,3)} for p,s,l,v in by[k]]}
        mx=max(n['s']+n['l'] for n in c['notes'])
        if mx>c['len']:c['len']=float(np.ceil(mx/4)*4)
        if env:
            e=env(k*blk+1,blk)
            if e:c['env']=e;c['envShow']=None
        out.append(c)
    return out
def ramp(R,lo,hi):
    def f(b0,blk):
        r=inr(R,b0) or inr(R,b0+blk-1)
        if not r:return None
        return {'cut':[{'b':i*4,'v':round(float(lo+(hi-lo)*np.clip((b0+i-r[0])/max(1,r[1]-r[0]+1),0,1)),3)} for i in range(blk+1)]}
    return f
def first(*fs):
    def f(b0,blk):
        for g in fs:
            r=g(b0,blk)
            if r:return r
    return f
def plant(**k):
    b=dict(w1='sawtooth',w2='sawtooth',morph=0,uni=1,det=0,width=0,cut=4000,res=.5,fenv=0,a=.003,d=.2,s=.5,r=.1,lfo=.3,lamt=0,space=0,sub=0,noise=0,fm=0,ratio=2,gain=.5);b.update(k);return b
sfx=lambda kind,tone=60,space=35,gain=.5:{'kind':kind,'tone':tone,'space':space,'gain':gain}
FXp=lambda t,**p:{'type':t,'p':p}
HP=lambda f,lp=None:{'type':'eq','p':{'an':'off','bands':[{'t':'highpass','f':f,'q':.7,'on':True,'sl':24}]+([{'t':'lowpass','f':lp,'q':.7,'on':True,'sl':12}] if lp else [])}}
PUMP=lambda d,sh=45:FXp('side',depth=d,shape=sh,punch=0,sustain=0,sync='1/4')
DLY=lambda mix,fb=33:FXp('tdelay',sync='1/8 dotted',feedback=fb,mix=mix,lowcut=400,highcut=4000,drive=0,wow=0,rate=.6,width=100,ping=True)   # 3/16 ping-pong, echoes 400 Hz-4 kHz [36]
GAIN={}
try:GAIN=json.load(open('gain.json'))
except Exception:pass
RV='Plate reverb'
def T(name,preset,inst,color,icon,grp=None,fx=None,pan=0,env=None,sends=None,blk=8,kind=None):
    t={'name':name,'color':color,'icon':icon,'vol':.8,'pan':pan,'fx':fx or []}
    if kind:t['kind']=kind
    else:t.update(preset=preset,inst=inst,clips=clips(name,blk,env))
    if grp:t['grp']=grp
    if sends:t['sends']=sends
    g=GAIN.get(name)
    if g and not kind:
        e=float(np.clip(g,-12,12));r=g-e
        if abs(r)>.01 and isinstance(t.get('inst'),dict) and 'gain' in t['inst']:t['inst']=dict(t['inst'],gain=round(t['inst']['gain']*10**(r/20),4))
        t['fx']=t['fx']+[{'type':'eq','p':{'an':'off','out':round(e,2)}}]
    return t
LEADP=plant(uni=3,det=5,width=35,cut=600,res=4,fenv=62,a=.001,d=.5,s=.75,r=.07,gain=.5)   # 3 saws, low detune, low-pass 600 Hz with resonance, filter decay about 200 ms [33]
OPENF=[(57,68),(73,88),(105,120),(145,160),(177,192),(209,224),(241,256)]
def tracks():
    return [
 T('Kick & Bass',0,0,'#ff6b6b','activity',kind='group',fx=[FXp('comp',threshold=-10,ratio=1.5,attack=30,release=100,makeup=0)]),   # [17]
 T('Kick','kick',dict(tune=33,start=2400,sweep=.045,bend=82,len=.17,tail=34,click=55,drive=12,ctype='snap',kt=False,gain=.9),'#ff6b6b','drum','Kick & Bass',
   env=first(ramp([(17,28)],.5,.95),ramp([(273,288)],.95,.55))),
 T('Bass','plant',plant(cut=500,res=1.5,fenv=20,a=.001,d=.07,s=0,r=.03,gain=.6),'#4c8dff','t-wave-saw-tool','Kick & Bass',fx=[HP(30),PUMP(100,24)],   # one saw, 500 Hz, one octave of envelope [9-15]
   env=first(ramp([(17,28)],.42,.8),ramp([(273,288)],.8,.45))),
 T('Drums',0,0,'#f5c84c','t-metronome',kind='group',fx=[FXp('comp',threshold=-18,ratio=2,attack=25,release=120,makeup=1)]),
 T('Clap','zclap',dict(bursts=5,spread=12,bd=6,tail=.2,freq=1500,q=1.6,room=35,drive=18,gain=.8),'#f5c84c','asterisk','Drums',sends={RV:.1}),
 T('Snare','zsnare',dict(tune=220,sweep=50,body=50,tone=50,snap=100,nhp=3500,nd=.14,rattle=55,click=65,dec=.16,drive=45,gain=.8),'#ff9a3c','target','Drums'),
 T('Hat','zhat',dict(pitch=9,tone=9500,hp=7800,noise=22,dec=.04,drive=12,gain=.7),'#3ecf8e','disc','Drums',pan=-.1),
 T('Open hat','zhat',dict(pitch=10,tone=10000,hp=7000,noise=24,dec=.2,drive=18,gain=.7),'#3ecf8e','disc-3','Drums',pan=.1),
 T('Percussion','ztom',dict(kt=1,tune=310,sweep=20,body=90,skin=60,click=55,noise=15,dec=.2,drive=10,gain=.8),'#ff7ac8','cylinder','Drums',pan=-.3),
 T('Shaker','zhat',dict(pitch=7,tone=6500,hp=5000,noise=85,dec=.08,drive=5,gain=.7),'#8b8f9c','hourglass','Drums',pan=.3),
 T('Toms','ztom',dict(kt=1,tune=120,sweep=80,body=100,skin=30,click=60,noise=10,dec=.2,drive=45,gain=.8),'#b583ff','cuboid','Drums',pan=.15),
 T('Crash','drums',{},'#4cc9f0','bell-ring','Drums',sends={RV:.15}),
 T('Snare roll','zsnare',dict(tune=200,sweep=45,body=60,tone=50,snap=85,nhp=2600,nd=.15,rattle=45,click=45,dec=.16,drive=25,gain=.8),'#ff7ac8','repeat','Drums',sends={RV:.15},blk=4,
   env=lambda b0,blk:ramp([(d-4,d-1) for d in BIG]+[(69,72)],.6,1.0)(b0,blk)),
 T('Music',0,0,'#7a8bff','music',kind='group',fx=[PUMP(35,40)]),                                   # leads ducked a few dB by the kick [38]
 T('Lead','plant',LEADP,'#4cc9f0','message-circle','Music',fx=[HP(250),DLY(22)],sends={RV:.18},
   env=first(ramp([(129,144)],.55,.85),ramp([(197,208)],.55,.85))),                                # in the breaks: low-passed, opening [50]
 T('Lead low','plant',dict(LEADP,cut=500,uni=1,det=0,width=0),'#4c8dff','audio-waveform','Music',fx=[HP(150,3000)]),
 T('Lead high','plant',dict(LEADP,cut=900,width=60),'#cfd3db','star','Music',fx=[HP(1000),DLY(30)],sends={RV:.2}),
 T('Hook left','plant',dict(LEADP,w2='square',morph=.35),'#9be564','megaphone','Music',pan=-.8,fx=[HP(250),DLY(18)],sends={RV:.15}),
 T('Hook right','plant',dict(LEADP,w2='square',morph=.35),'#ffd166','megaphone','Music',pan=.8,fx=[HP(250),DLY(18)],sends={RV:.15}),
 T('Arp','plant',plant(w1='square',w2='sawtooth',morph=.4,cut=1800,res=3,fenv=50,a=.001,d=.09,s=.1,r=.05,gain=.5),'#9be564','list-music','Music',fx=[HP(300),DLY(20)],
   env=ramp(ARP,.6,.9)),
 T('Acid','acid',dict(wave='sawtooth',cut=420,res=20,env=76,dec=.14,acc=70,slide=.06,dist=45,gain=.35),'#ff9a3c','biohazard','Music',fx=[HP(150)],
   env=first(ramp([(161,192)],.6,.92),ramp([(225,256)],.6,.95))),                                 # opens slowly over 32 bars [43]
 T('Pad','plant',plant(uni=2,det=6,width=100,cut=1200,res=.9,a=.3,d=.8,s=1,r=1.5,lamt=8,lfo=.1,gain=.4),'#7a8bff','cloud','Music',fx=[HP(200)],sends={RV:.35},
   env=first(ramp([(1,16)],.6,.8),ramp([(121,144)],.6,.9),ramp([(193,208)],.6,.9))),
 T('FX',0,0,'#f5c84c','sparkles',kind='group',fx=[HP(300),PUMP(25,40)]),                            # FX high-passed at 300 Hz [54]
 T('Riser','sfx',sfx('riser',60,25),'#f5c84c','rocket','FX',blk=4),
 T('Reverse crash','sfx',sfx('revcrash',65,15),'#3ecf8e','tornado','FX',blk=4),
 T('Impact','sfx',sfx('impact',55,35),'#ff4d6d','hammer',blk=4),
 T('Downlifter','sfx',sfx('downer',55,30),'#3ecf8e','cloud-rain','FX',blk=4),
 T('Blip','sfx',sfx('laser',60,20),'#ff7ac8','zap','FX',pan=-.2,sends={RV:.15}),
 T('Wind','sfx',sfx('wind',50,30),'#8b8f9c','wind','FX',blk=4),
 T(RV,0,0,'#b583ff','mountain',kind='return',fx=[FXp('reverb',decay=1.0,predelay=15,damp=7000,lowcut=500,mix=100)]),   # plate, about 1 s, return high-passed 500 Hz [37, 54]
 ]
MFX=[FXp('comp',threshold=-12,ratio=1.5,attack=30,release=120,makeup=0),FXp('clip',gain=0.0,thr=-4,ceil=-1.0,shape='tanh',os='4x',bias=0,mix=100,out=0)]
try:MFX=json.load(open('mfx.json'))
except Exception:pass
def recipe():
    return {'bpm':BPM,'name':'Fractals remake v6','sections':[{'name':n,'start':bar(a),'len':l*4,'color':c} for n,a,l,c in SECTIONS],'tracks':tracks(),'mfx':MFX}
if __name__=='__main__':
    R=recipe();print(len(R['tracks']),'tracks');print({t['name']:sum(len(c['notes']) for c in t.get('clips',[])) for t in R['tracks']})
