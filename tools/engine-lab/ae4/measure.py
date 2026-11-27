# Task AE4 (built-in sounds research): measure the app's own instruments and effects, headless, through its own render.
#   python3 tools/engine-lab/ae4/measure.py [index.html] [part ...]   parts: inst fx   (default both)
# Writes tools/engine-lab/ae4/results.json. Nothing in index.html is changed.
import sys,os,json,time,numpy as np
HERE=os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0,os.path.join(HERE,'..','..','remake'))
from alab import AudioLab
idx=sys.argv[1] if len(sys.argv)>1 and sys.argv[1].endswith('.html') else 'index.html'
parts=set(a for a in sys.argv[1:] if not a.endswith('.html'));want=lambda p:not parts or p in parts
SR=48000;BPM=120;SPB=60/BPM
db=lambda v:20*np.log10(max(float(v),1e-12))
al=AudioLab(idx);al.start();print('version',al.version,'errors',al.errors)
RP=os.path.join(HERE,'results.json')
R=json.load(open(RP)) if os.path.exists(RP) else {}
R['version']=al.version;R.setdefault('inst',{});R.setdefault('fx',{})
def mono(x):return x.astype(np.float64).mean(0)
def alias_db(y,f0,lo=40):
    # aliasing proxy that detune, unison and filters cannot fake: a high note (C7) has no real partials below its fundamental,
    # so energy between 40 Hz and 0.45 x f0 (below an octave-down sub too) is folded-back aliasing (plus noise layers, if any).
    # Returned in dB against the whole signal.
    w=np.blackman(len(y));X=np.abs(np.fft.rfft(y*w))**2;f=np.fft.rfftfreq(len(y),1/SR)
    A=X[(f>lo)&(f<.45*f0)].sum();T=X[f>lo].sum();return 10*np.log10(max(A,1e-30)/max(T,1e-30))
def render_t(recipe,b0,b1,tail=0):
    al.build(recipe);t=time.time();x,sr=al.render(b0=b0,b1=b1,sr=SR,tail=tail);return x,time.time()-t
INST=[('saw','Saw lead (al-poly)',{}),('reese','Reese bass',{}),('acid','Acid',{}),('plant','Plant',{}),('wtab','Wavetable',{}),
      ('venom','Venom',{}),('psyb','Psy Bass',{}),('sbass','Sub',{}),('vfm','Vector FM',{}),('growl','Growl',{}),('kick','Kick designer',{}),('crk','Fractal',{})]
MONO={'acid','psyb','sbass','kick','growl'}
if want('inst'):
    _,t_empty=render_t({'bpm':BPM,'tracks':[{'name':'E','preset':'saw','clips':[{'start':0,'len':16,'notes':[]}]}]},0,16)
    R['t_empty_16beats']=t_empty
    for key,name,ov in INST:
        r={'name':name}
        try:
            tr=lambda notes,ln=16:{'bpm':BPM,'tracks':[{'name':'I','preset':key,'inst':ov,'clips':[{'start':0,'len':ln,'notes':notes}]}]}
            # 1 aliasing: one high note (C7, 2093 Hz), 0.1 to 0.45 s
            x,_=render_t(tr([{'p':96,'s':0,'l':1,'v':.9}],4),0,2);y=mono(x)[int(.1*SR):int(.45*SR)]
            r['peak_C7_dB']=db(np.abs(y).max());r['alias_C7_dB']=alias_db(y,440*2**((96-69)/12)) if np.abs(y).max()>1e-4 else None
            x,_=render_t(tr([{'p':84,'s':0,'l':1,'v':.9}],4),0,2);y=mono(x)[int(.1*SR):int(.45*SR)]
            r['alias_C6_dB']=alias_db(y,440*2**((84-69)/12)) if np.abs(y).max()>1e-4 else None
            # 2 onset: one note C2 at beat 1; time to 90% of the peak envelope; first-ms jump
            x,_=render_t(tr([{'p':36,'s':1,'l':.25,'v':1}],4),0,3);y=mono(x);s0=int(SPB*SR);seg=np.abs(y[s0:s0+int(.25*SR)])
            env=np.maximum.accumulate(seg);pk=seg.max()
            if pk>1e-5:
                r['t90_ms']=float(np.argmax(env>=.9*pk)/SR*1000)
                e=np.array([np.abs(y[s0+i:s0+i+96]).max() for i in range(0,int(.2*SR),96)])
                r['t_minus40_ms']=float(np.argmax((e<pk*.01)&(np.arange(len(e))*96/SR>.01))*96/SR*1000) if (e<pk*.01).any() else None
                r['pre_onset_dB']=db(np.abs(y[s0-int(.002*SR):s0]).max())
            # 3 stereo and cost: a chord (or a 16th line for mono instruments), 16 beats
            notes=[{'p':36,'s':b*.25,'l':.2,'v':.9} for b in range(64)] if key in MONO else [{'p':p,'s':b*4,'l':3.5,'v':.8} for b in range(4) for p in (57,60,64,67,72)]
            x,t=render_t(tr(notes),0,16);x=x.astype(np.float64);L,Rr=x[0],x[1]
            r['corr_LR']=float(np.corrcoef(L,Rr)[0,1]) if L.std()>1e-7 and Rr.std()>1e-7 else None
            r['side_mid_dB']=db(np.sqrt(np.mean((L-Rr)**2))/max(np.sqrt(np.mean((L+Rr)**2)),1e-12))
            r['render_s_per_s']=max(t-t_empty,0)/(16*SPB);r['voices']=1 if key in MONO else 5
        except Exception as e:r['error']=str(e)[:200]
        R['inst'][key]=r;print(key,json.dumps({k:(round(v,2) if isinstance(v,float) else v) for k,v in r.items()}))
def fxrun(sig,fx,beats=8,tail=0):
    bid=al.add_audio(np.vstack([sig,sig]).astype(np.float32),SR)
    rec={'bpm':BPM,'tracks':[{'name':'A','kind':'audio','fx':fx,'clips':[{'start':0,'len':beats,'buf':bid,'dur':len(sig)/SR,'gain':0,'fi':0,'fo':0}]}]}
    al.build(rec);t=time.time();x,_=al.render(b0=0,b1=beats,sr=SR,tail=tail);return x.astype(np.float64),time.time()-t
def ir_stats(x,start):
    L,Rr=x[0][start:],x[1][start:];e=L**2+Rr**2;sch=np.cumsum(e[::-1])[::-1];sch=10*np.log10(sch/sch[0]+1e-30)
    i5=np.argmax(sch<-5);i35=np.argmax(sch<-35);rt=(i35-i5)/SR*2 if i35>i5 else None
    tail=slice(int(.1*SR),int(.6*SR));c=float(np.corrcoef(L[tail],Rr[tail])[0,1])
    # echo density (Abel and Huang): share of samples beyond one standard deviation in 20 ms windows, normalised so Gaussian noise = 1
    from math import erfc,sqrt
    nd=[];W=int(.02*SR)
    for a in range(0,int(.2*SR),W//2):
        s=L[a:a+W];sd=s.std()
        if sd>0:nd.append((np.abs(s)>sd).mean()/erfc(1/sqrt(2)))
    t_dense=next((i*W/2/SR*1000 for i,v in enumerate(nd) if v>.9),None)
    # colour: peakiness of the tail spectrum, 200 Hz to 8 kHz (max over median of a 1/12-octave smoothed magnitude)
    seg=L[int(.2*SR):int(1.2*SR)];X=np.abs(np.fft.rfft(seg*np.hanning(len(seg))));f=np.fft.rfftfreq(len(seg),1/SR);m=(f>200)&(f<8000)
    pk=float(np.percentile(X[m],99.5)/np.median(X[m]))
    return {'rt60_s':rt,'corr_tail':c,'t_dense_ms':t_dense,'echo_density_first20ms':nd[0] if nd else None,'tail_peak_over_median':pk}
if want('fx'):
    n=int(2*SR);t_=np.arange(n)/SR;sine=.7*np.sin(2*np.pi*4500*t_);sine[:240]*=np.linspace(0,1,240)
    for key,fx in [('drive',[{'type':'drive','p':{'drive':100}}]),('clip',[{'type':'clip'}]),('tdelay_drive',[{'type':'tdelay','p':{'drive':100,'mix':100,'feedback':0}}])]:
        try:
            x,t=fxrun(sine,fx,4);y=x[0][int(.3*SR):int(1.3*SR)];r={'alias_4k5_dB':alias_db(y,4500),'peak_dB':db(np.abs(y).max())}
        except Exception as e:r={'error':str(e)[:200]}
        R['fx'][key]=r;print(key,r)
    imp=np.zeros(int(8*SR));imp[int(.1*SR)]=.9
    for key,fx in [('reverb',[{'type':'reverb','p':{'mix':100,'decay':2.2,'predelay':0}}]),('conv',[{'type':'conv'}]),('blur',[{'type':'blur','p':{'mix':100}}])]:
        try:
            x,t=fxrun(imp,fx,16);s=int(.1*SR);r=ir_stats(x,s);r['render_s']=t
        except Exception as e:r={'error':str(e)[:200]}
        R['fx'][key]=r;print(key,r)
    # Pro EQ: +12 dB bell at 16 kHz, Q 1 (band 4), impulse response divided by the same render with the band off, against the analog prototype
    try:
        sm=np.zeros(SR);sm[int(.1*SR)]=.05
        def resp(on):
            x,_=fxrun(sm,[{'type':'eq','p':{'bands':[None,None,None,None,{'t':'peaking','f':16000,'g':12 if on else 0,'q':1,'on':True}]}}],2)
            h=x[0][int(.1*SR)-2000:int(.1*SR)+14000];return np.abs(np.fft.rfft(h,1<<15))
        H=resp(True)/np.maximum(resp(False),1e-12);f=np.fft.rfftfreq(1<<15,1/SR)
        def ana(ff,f0=16000,G=12,Q=1):
            A=10**(G/40);s_=1j*ff/f0;return np.abs((s_*s_+s_*A/Q+1)/(s_*s_+s_/(A*Q)+1))
        out={}
        for ff in (8000,12000,16000,20000,22000):
            i=np.argmin(abs(f-ff));out['%dk'%(ff//1000)]={'app_dB':round(db(H[i]),2),'analog_dB':round(db(ana(ff)),2)}
        R['fx']['eq_bell16k']=out;print('eq',out)
    except Exception as e:R['fx']['eq_bell16k']={'error':str(e)[:200]};print('eq err',e)
    # Compressor: a 1 kHz tone stepping from -40 to -6 dBFS; gain = compressed / uncompressed render; time to 63% of the final gain reduction (attack 10 ms set)
    try:
        tt=np.arange(int(3*SR))/SR;st=np.where(tt<1,.01,.5)*np.sin(2*np.pi*1000*tt)
        def envof(ratio,att=10):
            x,_=fxrun(st,[{'type':'comp','p':{'threshold':-30,'ratio':ratio,'attack':att,'release':200,'makeup':0}}],6);y=x[0]
            return np.array([np.abs(y[i:i+48]).max() for i in range(0,len(y)-48,48)])
        ref=envof(1)
        for att in (1,10,50):
            g=envof(8,att)/np.maximum(ref,1e-9);i1=int(1*SR/48);gdb=20*np.log10(np.maximum(g[i1:i1+int(.4*SR/48)],1e-9));fin=gdb[-40:].mean();k=int(np.argmax(gdb<=fin*.63))
            R['fx']['comp_step_att%d'%att]={'final_gr_dB':float(fin),'t63_ms':k*48/SR*1000,'gain_first_ms_dB':float(gdb[:2].max())};print('comp',att,R['fx']['comp_step_att%d'%att])
    except Exception as e:R['fx']['comp_step']={'error':str(e)[:200]};print('comp err',e)
if want('inst') or want('fx'):json.dump(R,open(os.path.join(HERE,'results.json'),'w'),indent=1,default=float)
if want('alias'):
    for key,name,ov in INST:
        for p in (96,100):
            x,_=render_t({'bpm':BPM,'tracks':[{'name':'I','preset':key,'inst':ov,'clips':[{'start':0,'len':4,'notes':[{'p':p,'s':0,'l':1,'v':.9}]}]}]},0,2)
            y=mono(x)[int(.1*SR):int(.45*SR)];R['inst'][key]['alias_%d_dB'%p]=alias_db(y,440*2**((p-69)/12)) if np.abs(y).max()>1e-5 else None
        print(key,R['inst'][key].get('alias_100_dB'),R['inst'][key].get('alias_96_dB'))
# extra: the same alias measure on settings that matter for psytrance (run with part 'extra')
if want('extra'):
    R.setdefault('extra',{})
    def one(key,ov,p,lab,dur=.35):
        x,t=render_t({'bpm':BPM,'tracks':[{'name':'I','preset':key,'inst':ov,'clips':[{'start':0,'len':4,'notes':[{'p':p,'s':0,'l':1.5,'v':.9}]}]}]},0,2)
        y=mono(x)[int(.05*SR):int((.05+dur)*SR)];L,Rr=x[0].astype(float),x[1].astype(float)
        r={'alias_dB':alias_db(y,440*2**((p-69)/12)) if np.abs(y).max()>1e-5 else None,'peak_dB':db(np.abs(y).max()),'corr_LR':float(np.corrcoef(L,Rr)[0,1]) if L.std()>0 and Rr.std()>0 and not np.allclose(L,Rr) else 1.0}
        R['extra'][lab]=r;print(lab,{k:(round(v,2) if isinstance(v,float) else v) for k,v in r.items()})
    for d in (0,55,100):one('acid',{'dist':d,'cut':3000},96,'acid dist %d cut 3k note 96'%d)
    one('psyb',{},96,'psyb note 96')
    one('reese',{},96,'reese note 96')
    one('plant',{'uni':1},96,'plant uni1 note 96')
    one('growl',{},96,'growl note 96')
    one('wtab',{'uni':5,'det':20,'width':100},96,'wtab uni5 note 96')
    one('venom',{'aun':7,'aud':.3},96,'venom unison7 note 96')
    one('saw',{},100,'saw note 100 (E7)')
    one('square',{},96,'square note 96')
    json.dump(R,open(os.path.join(HERE,'results.json'),'w'),indent=1,default=float)
al.stop()
