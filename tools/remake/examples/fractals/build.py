"""Fractals: build the AudioLab recipe from song.json (+ followers.json when present)."""
from common import *
import os
NB=288
SECTIONS=[('Intro',1,16,'#4cc9f0'),('Filtered groove',17,16,'#7a8bff'),('Drop 1',33,16,'#ff6b6b'),('Groove',49,24,'#ff9a3c'),('Full',73,16,'#f5c84c'),
 ('Part 2',89,16,'#ff6b6b'),('Part 2 full',105,16,'#f5c84c'),('Breakdown',121,24,'#b583ff'),('Drop 2',145,16,'#ff6b6b'),('Peak',161,32,'#ff4d6d'),
 ('Break 2',193,16,'#b583ff'),('Final',209,48,'#ff4d6d'),('Reprise',257,16,'#f5c84c'),('Outro',273,16,'#3ecf8e')]
def clips_from_steps(lst,pitch,length,name,blk=8,vel_scale=1.0,pitch_fn=None):
    """lst: [[step index (16ths from song start), velocity]] -> clips of `blk` bars."""
    by={}
    for i,v in lst:by.setdefault(i//(16*blk),[]).append((i,v))
    out=[]
    for k in sorted(by):
        s0=k*16*blk;notes=[{'p':int(pitch_fn(i) if pitch_fn else pitch),'s':round((i-s0)/4,4),'l':length,'v':round(float(min(1,max(.02,v*vel_scale))),3)} for i,v in by[k]]
        out.append({'start':k*blk*4,'len':blk*4,'name':f'{name} {k*blk+1}','notes':notes})
    return out
def recipe(mix=None,parts=None):
    S=json.load(open('song.json'));K=json.load(open('kick_fit.json'));B=json.load(open('bass_fit.json'))
    mix=mix or (json.load(open('mix.json')) if os.path.exists('mix.json') else {})
    V=lambda n,d:float(mix.get(n,{}).get('vol',d))
    FX=lambda n:mix.get(n,{}).get('fx',[])
    tr=[]
    kick_inst={k:(round(K[k],4) if k!='ctype' else K[k]) for k in K};kick_inst.update(gain=.9,kt=False)
    kc=clips_from_steps(S['kick'],36,.25,'Kick');kb=S.get('kick_bright')
    if kb:
        for c in kc:
            b0=c['start']//4;pts=[]
            for b in range(b0,min(NB,b0+8)):
                r=kb[b] if kb[b] is not None else 1
                pts.append({'b':(b-b0)*4,'v':round(float(np.clip(.4+(np.log10(max(r,.01))+1)/(np.log10(.8)+1)*.6,.36,1)),3)})
            if any(p['v']<1 for p in pts):c['env']={'cut':pts};c['envShow']='cut'
    tr.append({'name':'Kick','preset':'kick','color':'#ff6b6b','inst':kick_inst,'vol':V('Kick',.8),'fx':FX('Kick'),'clips':kc})
    bass_inst=dict(w1='sawtooth',w2='square',morph=B['morph'],uni=1,det=0,width=0,cut=B['cut'],res=B['res'],fenv=B['fenv'],a=.001,d=B['d'],s=B['s'],r=B['r'],lfo=.3,lamt=0,space=0,sub=B['sub'],noise=0,fm=0,ratio=2,gain=.55)
    bass_inst.update(mix.get('Bass',{}).get('inst',{}))
    bc=clips_from_steps(S['bass'],33,B['notelen'],'Bass')
    # filter per bar from the measured brightness (the intro groove is low-passed and opens up)
    br=np.array(S['bass_bright']);ref=np.median(br[32:120])
    for c in bc:
        b0=c['start']//4;pts=[]
        for b in range(b0,min(NB,b0+8)):
            r=br[b]/ref
            if r<.8:pts.append({'b':(b-b0)*4,'v':round(float(np.clip(.2+.35*r,.25,.6)),3)})
            else:pts.append({'b':(b-b0)*4,'v':1})
        if any(p['v']<1 for p in pts):c['env']={'cut':pts};c['envShow']='cut'
    tr.append({'name':'Bass','preset':'plant','color':'#4c8dff','inst':bass_inst,'vol':V('Bass',.8),'fx':FX('Bass'),'clips':bc})
    tr.append({'name':'Hats','preset':'zhat','color':'#f5c84c','inst':mix.get('Hats',{}).get('inst',{}),'vol':V('Hats',.5),'fx':FX('Hats'),'clips':clips_from_steps(S['hat'],60,.1,'Hats')})
    oh={'dec':.22,'hp':8500,'tone':11000};oh.update(mix.get('Open hat',{}).get('inst',{}))
    tr.append({'name':'Open hat','preset':'zhat','color':'#3ecf8e','inst':oh,'vol':V('Open hat',.5),'fx':FX('Open hat'),'clips':clips_from_steps(S['ohat'],60,.2,'Open hat')})
    tr.append({'name':'Clap','preset':'zclap','color':'#ff9a3c','inst':mix.get('Clap',{}).get('inst',{}),'vol':V('Clap',.5),'fx':FX('Clap'),'clips':clips_from_steps(S['clap'],60,.2,'Clap')})
    tr.append({'name':'Snare & fills','preset':'zsnare','color':'#ff7ac8','inst':mix.get('Snare & fills',{}).get('inst',{}),'vol':V('Snare & fills',.5),'fx':FX('Snare & fills'),'clips':clips_from_steps(S['snare'],60,.15,'Fill')})
    if os.path.exists('melody.json') and not os.environ.get('NOMEL'):
        MEL=json.load(open('melody.json'));MP=json.load(open('melpatch.json')) if os.path.exists('melpatch.json') else {}
        for nm,lo,hi,col in [('Mel low',52,60,'#b583ff'),('Mel mid',61,71,'#7a8bff'),('Mel high',72,99,'#4cc9f0')]:
            by={}
            for p,st,l,v in MEL:
                if lo<=p<=hi:by.setdefault(st//128,[]).append((p,st,l,v))
            cl=[]
            for k in sorted(by):
                s0=k*128;cl.append({'start':k*32,'len':32,'name':f'{nm} {k*8+1}','notes':[{'p':p,'s':round((st-s0)/4,4),'l':round(max(.2,l/4*.95),4),'v':round(v,3)} for p,st,l,v in by[k]]})
            inst=dict(w1='sawtooth',w2='sawtooth',morph=0,uni=2,det=10,width=70,cut=4200,res=.25,fenv=0,a=.004,d=.2,s=.7,r=.08,lfo=.3,lamt=0,space=0,sub=0,noise=0,fm=0,ratio=2,gain=.5)
            inst.update(MP.get(nm,{}))
            tr.append({'name':nm,'preset':'plant','color':col,'inst':inst,'vol':V(nm,.5),'fx':FX(nm),'clips':cl})
    if os.path.exists('followers.json'):
        F=json.load(open('followers.json'))
        BG=json.load(open('blockgain.json')) if os.path.exists('blockgain.json') else {}
        for t in F['tracks']:
            if os.path.exists('melody.json') and not os.environ.get('NOMEL') and t['name']!='Sub drone':continue
            t=dict(t);t['vol']=V(t['name'],t.get('vol',.8));bg=BG.get(t['name'],{})
            if bg:
                cl=[]
                for c in t['clips']:
                    k=str(c['start']//32);c=dict(c)
                    if k in bg and abs(bg[k])>.05:
                        f=10**(bg[k]/40);c['env']={'vol':[{'b':p['b'],'v':round(min(1,p['v']*f),3)} for p in c['env']['vol']]}
                    cl.append(c)
                t['clips']=cl
            if FX(t['name']):t['fx']=t.get('fx',[])+FX(t['name'])
            for c in t['clips']:c['envShow']=None   # the envelopes work without being drawn; thousands of points per clip would slow the arrangement down
            tr.append(t)
    for t in tr:   # output gain of a track lives in its EQ ('out', dB)
        o=mix.get(t['name'],{}).get('out')
        if o is not None:
            eq=next((f for f in t.get('fx',[]) if f['type']=='eq'),None)
            if eq is None:eq={'type':'eq','p':{'an':'off'}};t.setdefault('fx',[]).append(eq)
            eq['p']['out']=round(float(o),2)
    if parts:tr=[t for t in tr if t['name'] in parts]
    mfx=mix.get('mfx',[])
    return {'name':'Fractals (remake)','bpm':BPM,'master':float(mix.get('master',0)),'mfx':mfx,'sections':[{'name':n,'start':(a-1)*4,'len':l*4,'color':c} for n,a,l,c in SECTIONS],'tracks':tr}
if __name__=='__main__':
    r=recipe();print([(t['name'],len(t['clips']),sum(len(c.get('notes',[])) for c in t['clips'])) for t in r['tracks']])
