# Fractal (first called Crackle), the pulse-pattern synth and effect (v0.191): measured through the app's own render.  python3 tools/engine-tests/fractal.py [index.html] [part ...]
# parts: grid levels tune alias dc click mix0 presets same cost (default: all); the Fractals demo levels are always printed first
import sys,os,json,time,numpy as np
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','remake'))
from alab import AudioLab
idx=sys.argv[1] if len(sys.argv)>1 else 'index.html';parts=set(sys.argv[2:])
want=lambda p:not parts or p in parts
al=AudioLab(idx);al.start();SR=44100
print('ver',al.version,'page errors',al.errors)
rms=lambda x:float(np.sqrt(np.mean(x.astype(np.float64)**2)));db=lambda v:20*np.log10(max(v,1e-15))
al.tracks=json.loads(al.run("JSON.stringify(Object.fromEntries(S.tracks.map(t=>[t.name,t.id])))"))
kx,_=al.render(b0=64,b1=96,only='Kick');bx,_=al.render(b0=64,b1=96,only='Bass')
print('Fractals Kick %.5f dB'%db(rms(kx)));print('Fractals Bass %.5f dB'%db(rms(bx)))
LAT=al.run("CRKC.LAT")
def fxp(**o):
    d=json.loads(al.run("JSON.stringify(FXPRE.crk.draw[1])"));d.update(o);return d
def audio_track(sig,beats,fx,name='A'):
    bid=al.add_audio(np.vstack([sig,sig]).astype(np.float32),SR)
    return {'name':name,'kind':'audio','fx':fx,'clips':[{'start':0,'len':beats,'buf':bid,'dur':len(sig)/SR,'gain':0,'fi':0,'fo':0}]}
def build(tracks,bpm=120):al.build({'bpm':bpm,'tracks':tracks})
def ren(b0,b1,tail=0,only=None):
    x,sr=al.render(b0=b0,b1=b1,tail=tail,only=only);return x.astype(np.float64)
def instp(k,ov=None):
    al.run("(()=>{const I=S.tracks[S.tracks.length-1].inst;for(const k in I)if(k!=='preset')delete I[k];Object.assign(I,crkParams('%s'),%s);I.ipk='%s';changed(true)})()"%(k,json.dumps(ov or {}),k))
if want('grid'):
    print('--- pulses on the grid (effect, sharp square pulses, Smooth 0, a steady input; onset = where the level crosses half the pulse, read between samples)')
    for bpm in (90,120,137,174):
        beats=8;n=int(beats*60/bpm*SR)+SR;sig=np.full(n,.5)
        for spd,lab,div in ((35,'1/16',.25),(30,'1/8T',1/3),(45,'1/32',.125)):
            build([audio_track(sig,beats+2,[{'type':'crk','p':fxp(ns=4,l1=100,l2=50,l3=100,l4=25,spd=spd,len=50,shp=0,sm=0)}])],bpm)
            x=ren(0,beats)[0];step=div*60/bpm*SR;lv=[1,.5,1,.25];err=[];found=0;ref=x[int(4.25*step)+LAT]
            for k in range(1,int(beats/div)-1):
                t=k*step+LAT;half=.5*lv[k%4]*ref;i0=int(t)-30
                seg=x[i0:i0+60];j=np.where((seg[:-1]<half)&(seg[1:]>=half))[0]
                if len(j):i=j[0];f=i0+i+(half-seg[i])/(seg[i+1]-seg[i]);err.append(f-t);found+=1
            print('%3d bpm %-5s %3d onsets found of %3d, largest distance from the grid %.3f samples (the delay of %d samples that the app makes up for is taken off)'%(bpm,lab,found,int(beats/div)-2,np.abs(err).max(),LAT))
if want('levels'):
    print('--- per-step levels measured in the middle of each pulse, against the dials')
    for lv in ([35,100,65],[100,0,50,25,80],[10,20,30,40,50,60,70,80]):
        o=dict(ns=len(lv),spd=25,len=60,shp=20,sm=1);o.update({'l%d'%(i+1):v for i,v in enumerate(lv)})
        sig=np.full(SR*6,.5);build([audio_track(sig,12,[{'type':'crk','p':fxp(**o)}])],120)
        x=ren(0,8)[0];step=.5*60/120*SR;ref=al.run('0')
        build([audio_track(sig,12,[])],120);ref=ren(0,8)[0][SR];got=[x[int((k+.3)*step)+LAT]/ref*100 for k in range(len(lv),2*len(lv))]
        print('dials',lv,'measured',[round(float(v),4) for v in got])
    # pump: the dip and the way back
    sig=np.full(SR*6,.5);build([audio_track(sig,12,[{'type':'crk','p':fxp(md='s',ns=4,l1=100,l2=100,l3=100,l4=100,spd=15,len=70,shp=45,sm=2)}])],120)
    x=ren(0,8)[0];build([audio_track(sig,12,[])],120);x=x/ren(0,8)[0][SR];spb=.5*SR
    print('Pump on every beat: level at 0, 1 ms, 5 ms, 50 ms, 150 ms, 300 ms, 400 ms after the beat:',' '.join('%.3f'%x[int(2*spb+LAT+t*SR)] for t in (0,.001,.005,.05,.15,.3,.4)))
if want('tune'):
    print('--- the buzz is in tune with the key (instrument, sine source so only the pulses add overtones). "off" = strongest thing that is not a multiple of the expected spacing')
    def spec(x,f0,space):
        seg=x[SR//2:SR//2+65536];N=len(seg);w=np.kaiser(N,25);X=2*np.abs(np.fft.rfft(seg*w))/w.sum();fr=np.fft.rfftfreq(N,1/SR)
        keep=np.ones(len(X),bool)
        for k in range(0,int(SR/2/space)+2):keep&=np.abs(fr-k*space)>12*SR/N
        keep&=fr<0.43*SR;ref=X.max();i=np.argmax(X*keep);return db(X[i]/ref)
    def amp(x,f):
        seg=x[SR//2:SR//2+65536];n=np.arange(len(seg));w=np.kaiser(len(seg),25);return 2*abs(np.sum(seg*w*np.exp(-2j*np.pi*f*n/SR)))/w.sum()
    for p in (45,52,57):
        f0=440*2**((p-69)/12)
        for N,lv,kf in ((2,[100,100],'p'),(2,[100,40],'p'),(3,[30,100,60],'p'),(4,[100,40,80,20],'p'),(3,[30,100,60],'c')):
            build([{'name':'C','preset':'crk','clips':[{'start':0,'len':8,'notes':[{'p':p,'s':0,'l':6,'v':1}]}]}])
            o={'wv':'sin','kf':kf,'ns':N,'len':40,'shp':0,'sm':0,'tone':20000,'att':.005};o.update({'l%d'%(i+1):v for i,v in enumerate(lv)});instp('draw',o)
            x=ren(0,6)[0];rate=f0 if kf=='p' else f0*N;space=rate/N
            sub=max(db(amp(x,k*space)/amp(x,rate)) if True else 0 for k in range(1,N)) if N>1 else -999
            print('key %d (%.1f Hz) %d steps %-16s pulses at %7.1f Hz: lower tone at rate/%d %6.1f dB against the pulse rate; off the expected lines %6.1f dB'%(p,f0,N,str(lv)+' '+('pulse=key' if kf=='p' else 'pattern=key'),rate,N,sub,spec(x,f0,space)))
if want('alias'):
    print('--- aliasing at high rates (effect on a sine; everything that is not at |sine +- k x pulse rate| counts, below 0.43 x sample rate)')
    def worst(x,fc,fm):
        seg=x[SR:SR+65536];N=len(seg);w=np.kaiser(N,25);X=2*np.abs(np.fft.rfft(seg*w))/w.sum();fr=np.fft.rfftfreq(N,1/SR);keep=np.ones(len(X),bool)
        for k in range(-400,401):keep&=np.abs(fr-abs(fc+k*fm))>12*SR/N
        keep&=fr<.43*SR;ref=X.max();i=np.argmax(X*keep);return db(X[i]/ref),fr[i]
    for fc,fm,dl in ((5000,1500,50),(9000,3100,30),(2000,777,10),(15000,2900,50)):
        sig=.5*np.sin(2*np.pi*fc*np.arange(SR*4)/SR);hz=fm;spd=60+40*np.log(hz/(120*16/60))/np.log(4000/(120*16/60))
        build([audio_track(sig,8,[{'type':'crk','p':fxp(ns=1,l1=100,spd=float(spd),len=dl,shp=0,sm=0)}])],120)
        x=ren(0,6)[0];w,f=worst(x,fc,hz)
        # the same chop done the plain way (square pulses at the sample rate, no band limiting) for comparison
        t=np.arange(len(sig))/SR;g=((t*hz)%1<dl/100).astype(float);w2,f2=worst(sig*g,fc,hz)
        print('sine %5d Hz, square pulses at %4d Hz, length %d%%: worst %.1f dB at %.0f Hz   (plain chop: %.1f dB at %.0f Hz)'%(fc,hz,dl,w,f,w2,f2))
if want('dc'):
    print('--- DC and peaks of every instrument preset (a phrase: held note, short notes, a chord)')
    PRE=al.run("Object.keys(CRKIPRE)");worst=-999;pk=0
    for k in PRE:
        build([{'name':'C','preset':'crk','clips':[{'start':0,'len':8,'notes':[{'p':45,'s':0,'l':2,'v':1},{'p':45,'s':2,'l':.5,'v':1},{'p':52,'s':2.5,'l':.5,'v':1},{'p':48,'s':3,'l':.25,'v':1},{'p':57,'s':4,'l':2,'v':1},{'p':60,'s':4,'l':2,'v':1},{'p':64,'s':4,'l':2,'v':1}]}]}]);instp(k)
        x=ren(0,8,tail=1);d=db(abs(x[0].mean())/max(1e-9,np.abs(x).max()));p=np.abs(x).max();worst=max(worst,d);pk=max(pk,p)
        print('%-9s peak %6.1f dBFS  DC %6.1f dB under the peak  NaN %s'%(k,db(p),d,bool(np.isnan(x).any())))
    print('instrument presets: highest peak %.1f dBFS, most DC %.1f dB under the peak'%(db(pk),worst))
if want('click'):
    print('--- clicks: largest jump between two samples, against that of the steady sine (1.0 = no click). Effect on a 110 Hz sine, 1/8 pulses')
    sig=.5*np.sin(2*np.pi*110*np.arange(SR*4)/SR);st=np.abs(np.diff(sig)).max()
    for shp,sm,lab in ((0,0,'square, Smooth 0 (asks for clicks)'),(0,.6,'square, Smooth 0.6 ms'),(0,2,'square, Smooth 2 ms'),(15,.6,'default: shape 15%, Smooth 0.6 ms'),(60,0,'shape 60%, Smooth 0')):
        build([audio_track(sig,8,[{'type':'crk','p':fxp(ns=2,l1=100,l2=60,spd=25,len=50,shp=shp,sm=sm)}])],120)
        x=ren(0,6)[0];print('%-36s %.2f'%(lab,np.abs(np.diff(x[SR//2:])).max()/st))
if want('mix0'):
    print('--- Mix 0 passes the sound untouched')
    sig=(np.random.RandomState(1).rand(SR*3)*2-1)*.5
    build([audio_track(sig,6,[])]);a=ren(0,5)
    build([audio_track(sig,6,[{'type':'crk','p':fxp(mix=0,pha=50,spr=100,dep=5)}])]);b=ren(0,5)
    print('Mix 0 against no effect: largest difference',np.abs(a-b).max(),' identical',bool(np.array_equal(a,b)))
    build([audio_track(sig,6,[{'type':'crk','p':fxp(mix=100,ns=2,l1=100,l2=100,len=100,shp=0,sm=0,spd=35)}])]);c=ren(0,5)
    aa=a[0,:-LAT][SR//4:SR*2];cc=c[0,LAT:][SR//4:SR*2];A=np.fft.rfft(aa);Cc=np.fft.rfft(cc);fr=np.fft.rfftfreq(len(aa),1/SR);r=np.abs(Cc)/np.maximum(np.abs(A),1e-12)
    def band(f0,f1):m=(fr>=f0)&(fr<f1);return 20*np.log10(np.median(r[m]))
    m=(fr>20)&(fr<18000);print('Mix 100, every pulse 100%% long at full level (the gate stays open): the input %d samples later; level against the input, largest difference of a third-octave band 20 Hz to 18 kHz %.4f dB; 18-19 kHz %+.2f dB, 19-20 kHz %+.2f dB, 20-21 kHz %+.2f dB, 21-22 kHz %+.2f dB'%(LAT,max(abs(band(f,f*2**(1/3))) for f in 20*2**(np.arange(30)/3) if f*2**(1/3)<=18000),band(18000,19000),band(19000,20000),band(20000,21000),band(21000,22000)))
if want('presets'):
    print('--- every effect preset on a saw pad and a bass line: no NaN, no clip, peak against the dry sound')
    tr=[{'name':'P','preset':'saw','clips':[{'start':0,'len':8,'notes':[{'p':p,'s':0,'l':8,'v':.9} for p in (45,52,57,60)]}]}]
    build(tr);dry=ren(0,8);dp=np.abs(dry).max()
    for k in al.run("Object.keys(FXPRE.crk)"):
        tr[0]['fx']=[{'type':'crk','p':json.loads(al.run("JSON.stringify(FXPRE.crk['%s'][1])"%k))}];build(tr);x=ren(0,8,tail=1)
        print('%-9s peak %6.1f dBFS (dry %6.1f)  NaN %s  rms %6.1f dB  DC %6.1f dB under the peak'%(k,db(np.abs(x).max()),db(dp),bool(np.isnan(x).any()),db(rms(x)),db(abs(x[0].mean())/np.abs(x).max())))
if want('same'):
    print('--- two renders bit-identical, and a note moved by 293 samples sounds the same (Restart on)')
    for k in ('draw','crackle','growl','space','pump4'):
        build([{'name':'C','preset':'crk','clips':[{'start':0,'len':8,'notes':[{'p':45,'s':0,'l':2,'v':1},{'p':48,'s':2,'l':2,'v':.8},{'p':52,'s':4,'l':1,'v':1}]}]}]);instp(k)
        a=ren(0,8,tail=1);b=ren(0,8,tail=1);print('%-8s identical %s'%(k,bool(np.array_equal(a,b))),end='   ')
        sh=293/SR*2  # beats at 120 bpm
        build([{'name':'C','preset':'crk','clips':[{'start':0,'len':8,'notes':[{'p':45,'s':1,'l':2,'v':1}]}]}]);instp(k,{'rtg':True,'rl':0,'rt':0})
        a=ren(0,6);build([{'name':'C','preset':'crk','clips':[{'start':0,'len':8,'notes':[{'p':45,'s':1+sh,'l':2,'v':1}]}]}]);instp(k,{'rtg':True,'rl':0,'rt':0});b=ren(0,6)
        print('moved by 293 samples: largest difference %.2e'%np.abs(a[:,22050:22050+60000]-b[:,22050+293:22050+293+60000]).max())
    sig=(np.random.RandomState(2).rand(SR*6)*2-1)*.4
    for k in ('tg16','crackle','space'):
        build([audio_track(sig,12,[{'type':'crk','p':json.loads(al.run("JSON.stringify(FXPRE.crk['%s'][1])"%k))}])]);a=ren(0,10);b=ren(0,10);print('effect %-8s two renders identical %s'%(k,bool(np.array_equal(a,b))))
if want('cost'):
    print('--- cost: 32 s of sound (64 beats at 120 bpm)')
    build([{'name':'C','preset':'crk','clips':[{'start':0,'len':64,'notes':[{'p':45,'s':0,'l':.1,'v':1}]}]}]);t=time.time();ren(0,64);base=time.time()-t
    for k in ('draw','crackle','growl','space'):
        build([{'name':'C','preset':'crk','clips':[{'start':0,'len':64,'notes':[{'p':45+(i%3)*3,'s':i,'l':.9,'v':1} for i in range(64)]}]}]);instp(k)
        t=time.time();ren(0,64);print('instrument %-8s %.2f s (one short note: %.2f s)'%(k,time.time()-t,base))
    sig=(np.random.RandomState(3).rand(SR*33)*2-1)*.3;build([audio_track(sig,66,[])]);t=time.time();ren(0,64);b2=time.time()-t
    for k in ('tg16','buzz','space'):
        build([audio_track(sig,66,[{'type':'crk','p':json.loads(al.run("JSON.stringify(FXPRE.crk['%s'][1])"%k))}])]);t=time.time();ren(0,64);print('effect %-8s %.2f s (same audio without it: %.2f s)'%(k,time.time()-t,b2))
print('page errors',al.errors)
al.stop()
