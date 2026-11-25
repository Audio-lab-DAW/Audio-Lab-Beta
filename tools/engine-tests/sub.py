# Sub, the sub bass instrument (v0.186): everything measured through the app's own render.  python3 tools/engine-tests/sub.py [index.html] [part ...]
# parts: tune spec dc click phase mono level same cost (default: all); the Fractals demo levels are always printed first
import sys,os,json,time,numpy as np
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','remake'))
from alab import AudioLab
idx=sys.argv[1] if len(sys.argv)>1 else 'index.html';parts=set(sys.argv[2:])
want=lambda p:not parts or p in parts
al=AudioLab(idx);al.start()
print('ver',al.version,'presets',al.run("Object.keys(SBSPRE).length"))
rms=lambda x:float(np.sqrt(np.mean(x.astype(np.float64)**2)));db=lambda v:20*np.log10(max(v,1e-12))
hz=lambda p:440*2**((p-69)/12)
PRE=al.run("Object.keys(SBSPRE)")
# the demo that is open at the start (Fractals): its Kick and Bass alone, beats 64 to 96. Must not change, and the kick is what the presets are compared with
al.tracks=json.loads(al.run("JSON.stringify(Object.fromEntries(S.tracks.map(t=>[t.name,t.id])))"))
kx,ksr=al.render(b0=64,b1=96,only='Kick');bx,_=al.render(b0=64,b1=96,only='Bass')
print('Fractals Kick %.5f dB'%db(rms(kx)));print('Fractals Bass %.5f dB'%db(rms(bx)))
def build(notes,tempo=120,ln=16,extra=None):
    tr=[{'name':'S','preset':'sbass','clips':[{'start':0,'len':ln,'notes':notes}]}]
    if extra:tr=extra+tr
    al.build({'bpm':tempo,'tracks':tr})
def setp(k,ov=None):
    al.run("(()=>{const I=S.tracks[S.tracks.length-1].inst;for(const k in I)if(k!=='preset')delete I[k];Object.assign(I,sbsParams('%s'),%s);I.ipk='%s';changed(true)})()"%(k,json.dumps(ov or {}),k))
def ren(b0=0,b1=8,tail=0,**kw):
    x,sr=al.render(b0=b0,b1=b1,tail=tail,**kw);return x.astype(np.float64),sr
def amp_at(seg,sr,f,w):
    n=np.arange(len(seg));return 2*abs(np.sum(seg*w*np.exp(-2j*np.pi*f*n/sr)))/w.sum()
def spec(seg,sr,f0):
    """levels of the harmonics (dB, the first relative to full scale and the others relative to the first) and the strongest thing that is not a harmonic (dB under the fundamental)"""
    N=len(seg);w=np.kaiser(N,30);X=2*np.abs(np.fft.rfft(seg*w))/w.sum();fr=np.fft.rfftfreq(N,1/sr);a1=amp_at(seg,sr,f0,w)
    keep=np.ones(len(X),bool);wd=22*sr/N
    for k in range(0,int(sr/2/f0)+2):keep&=np.abs(fr-k*f0)>wd
    hs=[db(amp_at(seg,sr,k*f0,w)/a1) for k in range(2,7) if k*f0<sr/2]
    i=np.argmax(X*keep);return db(a1),hs,db(X[i]/a1),fr[i]

if want('tune'):
    print('--- tuning (pure sub, 4 s note, frequency from the phase of the wave)')
    for p in (24,29,31,33,40,48,60,72):
        build([{'p':p,'s':0,'l':10,'v':1}]);x,sr=ren(0,10);seg=x[0][int(.5*sr):int(4.5*sr)];f0=hz(p);n=np.arange(len(seg))
        z=seg*np.exp(-2j*np.pi*f0*n/sr);B=int(sr*.25);ph=np.unwrap(np.angle([z[i:i+B].sum() for i in range(0,len(z)-B,B)]));sl=np.polyfit(np.arange(len(ph))*B/sr,ph,1)[0]/(2*np.pi)
        print('key %2d  should be %9.4f Hz  is %9.4f Hz  off by %+.5f Hz'%(p,f0,f0+sl,sl))
if want('spec'):
    print('--- spectrum of every preset, envelope held at full and pitch drop off (steady tone, 1.5 s window). "other" is the strongest thing that is not an overtone, in dB under the note')
    worst=-999
    for k in PRE:
        row=[]
        for p in (24,33,72,96):
            build([{'p':p,'s':0,'l':8,'v':1}]);setp(k,{'sus':1,'pa':0,'vs':0});x,sr=ren(0,8);N=65536;seg=x[0][int(1.0*sr):int(1.0*sr)+N];a1,hs,oth,fo=spec(seg,sr,hz(p));worst=max(worst,oth)
            row.append((p,a1,hs,oth,fo))
        p,a1,hs,oth,fo=row[1]
        print('%-7s key 33 (55 Hz): note %6.1f dBFS, overtones 2 to 6: %s | other: key 24 %6.1f, key 33 %6.1f, key 72 %6.1f, key 96 %6.1f dB'%(k,a1,' '.join('%6.1f'%h for h in hs),row[0][3],row[1][3],row[2][3],row[3][3]))
    print('strongest thing that is not an overtone, all presets and keys: %.1f dB under the note'%worst)
    # the drive with the wave pushed hard, the stress case
    for p in (24,48,84):
        build([{'p':p,'s':0,'l':8,'v':1}]);setp('pure',{'shp':100,'wv':'s','drv':100,'asy':60,'ss':100,'oct':50});x,sr=ren(0,8);seg=x[0][int(1.0*sr):int(1.0*sr)+65536];a1,hs,oth,fo=spec(seg,sr,hz(p));print('stress (saw 100%%, drive 100%%, asymmetry 60%%, small speakers 100%%, octave 50%%) key %d: other %.1f dB at %.0f Hz'%(p,oth,fo))
    # pitch drop on a high key: nothing may fold back while the pitch sweeps. Shown as the level above 20 kHz and of the whole
    build([{'p':72,'s':0,'l':2,'v':1}]);setp('pure',{'shp':100,'wv':'s','pa':48,'pt':.3});x,sr=ren(0,2);print('pitch drop of 48 st on key 72 with a full saw: peak %.3f, no NaN %s'%(np.abs(x).max(),not np.isnan(x).any()))
if want('dc'):
    print('--- DC (mean over whole cycles of a held note, against the level of the note)')
    for k in PRE:
        build([{'p':33,'s':0,'l':8,'v':1}]);setp(k,{'sus':1,'pa':0});x,sr=ren(0,8);per=sr/hz(33);n=int(round(per*100));seg=x[0][int(sr):int(sr)+n];w=np.kaiser(len(seg),30);dc=abs(np.sum(seg*w)/w.sum());print('%-7s DC %7.1f dB under the peak'%(k,db(dc/np.abs(seg).max())),end=';  ' if PRE.index(k)%3!=2 else '\n')
    print()
def steps(x,sr,f,A):
    d1=np.abs(np.diff(x)).max();d2=np.abs(np.diff(x,2)).max();w=2*np.pi*f/sr;return d1/(A*w),d2/(A*w*w)
if want('click'):
    print('--- clicks: the largest step from one sample to the next, and the largest change of that step, against the same for the steady wave (1.0 = as smooth as the wave itself; a step of -60 dB would read about 80 in the second number)')
    def case(name,notes,ov,tempo=120,b1=8,f=hz(33),pk='pure'):
        build(notes,tempo);setp(pk,ov);x,sr=ren(0,b1,tail=.5);y=x[0];A=np.abs(y).max();a,b=steps(y,sr,f,A);print('%-58s step %.3f, change of step %.3f'%(name,a,b))
    case('one note, start and end',[{'p':33,'s':1,'l':2,'v':1}],{})
    case('one note, attack 1 ms, release 5 ms',[{'p':33,'s':1,'l':2,'v':1}],{'att':.001,'rel':.005})
    case('two notes back to back (second starts where first ends)',[{'p':33,'s':1,'l':1,'v':1},{'p':33,'s':2,'l':1,'v':1}],{})
    case('overlapping notes, Glide off (old note is faded, new starts)',[{'p':33,'s':1,'l':2,'v':1},{'p':33,'s':2,'l':2,'v':1}],{'gm':'o'})
    case('overlapping notes, Legato, glide 60 ms, 7 semitones up',[{'p':26,'s':1,'l':2,'v':1},{'p':33,'s':2,'l':2,'v':1}],{'gm':'l'})
    case('overlapping notes, Legato, glide 0 ms',[{'p':26,'s':1,'l':2,'v':1},{'p':33,'s':2,'l':2,'v':1}],{'gm':'l','gl':0})
    case('glide Always between separate notes, 140 ms',[{'p':26,'s':1,'l':.9,'v':1},{'p':33,'s':2,'l':1,'v':1}],{'gm':'a','gl':.14})
    case('a note inside a longer note (legato there and back)',[{'p':33,'s':1,'l':4,'v':1},{'p':28,'s':2,'l':1,'v':1}],{'gm':'l'})
    case('16th notes at 145 BPM, psytrance sub layer',[{'p':33,'s':i*.25,'l':.25,'v':1} for i in range(1,24) if i%4],{},tempo=145,pk='psy')
    case('16th notes at 145 BPM, long release 0.5 s (tails are cut by the next note)',[{'p':33,'s':i*.25,'l':.2,'v':1} for i in range(1,24)],{'rel':.5},tempo=145)
    case('Same start off, notes back to back',[{'p':33,'s':1+i*.37,'l':.37,'v':1} for i in range(8)],{'rt':False})
    case('808 with knock (pitch drop 24 st), against the top pitch',[{'p':33,'s':1,'l':2,'v':1},{'p':33,'s':4,'l':2,'v':1}],{'drv':0,'h3':0},f=hz(57),pk='k808')
if want('phase'):
    print('--- the same phase at every note start')
    N=[{'p':33,'s':1+i*.613,'l':.4,'v':1} for i in range(9)]
    for rt in (True,False):
        build(N);setp('pure',{'rt':rt,'rel':.3});x,sr=ren(0,8);y=x[0];segs=[]
        for n in N:
            s0=int(round(n['s']*.5*sr));segs.append(y[s0+int(.02*sr):s0+int(.18*sr)])  # from 20 ms in: the tail of the note before is cut within 10 ms
        dv=max(np.abs(s-segs[0]).max() for s in segs[1:])/np.abs(segs[0]).max()
        print('Same start %-5s: nine notes at uneven distances, largest difference between any note and the first (20 to 180 ms of the note): %.2e of the peak'%('on' if rt else 'off',dv))
    build(N);setp('pure',{'ph':90});x,sr=ren(0,8);s0=int(round(N[0]['s']*.5*sr));print('Start phase 90: first samples of the note %s (a cosine start rises at once and then follows the fade-in)'%np.round(x[0][s0+1:s0+41:8],5))
if want('mono'):
    print('--- left and right')
    for k in PRE:
        build([{'p':33,'s':0,'l':8,'v':1}]);setp(k,{'sus':1});x,sr=ren(0,8);N=65536;L=x[0][sr:sr+N];R=x[1][sr:sr+N];w=np.kaiser(N,30);fr=np.fft.rfftfreq(N,1/sr);FL=np.fft.rfft(L*w);FR=np.fft.rfft(R*w);lo=fr<150;hi=fr>=150
        print('%-7s whole render identical %-5s | below 150 Hz: difference %7.1f dB under the signal | above 150 Hz: side %6.1f dB under mid'%(k,np.array_equal(x[0],x[1]),db(np.abs(FL-FR)[lo].max()/np.abs(FL+FR)[lo].max()),db((np.abs(FL-FR)[hi]**2).sum()**.5/max((np.abs(FL+FR)[hi]**2).sum()**.5,1e-30))))
    build([{'p':33,'s':0,'l':8,'v':1}]);setp('wide',{'sus':1,'wid':100});x,sr=ren(0,8);m=x[0]+x[1];print('Width 100%%: mono sum against left alone, level %.2f dB (no hole when summed)'%(db(rms(m[sr:3*sr])/2)-db(rms(x[0][sr:3*sr]))))
if want('level'):
    print('--- level of every preset: 16th notes with the kick left out, key 31 (49 Hz), 145 BPM, full velocity, against the Fractals kick')
    kp=db(np.abs(kx).max());kr=db(rms(kx));print('Fractals Kick: peak %.1f dBFS, average %.1f dB | Fractals Bass: peak %.1f dBFS, average %.1f dB'%(kp,kr,db(np.abs(bx).max()),db(rms(bx))))
    for k in PRE:
        build([{'p':31,'s':i*.25,'l':.25,'v':1} for i in range(32) if i%4],145,8);setp(k);x,sr=ren(0,8);l1=(db(np.abs(x).max()),db(rms(x)))
        build([{'p':31,'s':0,'l':8,'v':1}],145,8);setp(k);x,sr=ren(0,8);l2=(db(np.abs(x).max()),db(rms(x)))
        build([{'p':24,'s':0,'l':4,'v':1},{'p':43,'s':4,'l':4,'v':1}],145,8);setp(k);x,sr=ren(0,8)
        print('%-7s 16ths: peak %6.1f dBFS (%+5.1f to kick), average %6.1f dB (%+5.1f) | held 8 beats: peak %6.1f, average %6.1f | lowest and highest bass key (24, 43): peak %6.1f'%(k,l1[0],l1[0]-kp,l1[1],l1[1]-kr,l2[0],l2[1],db(np.abs(x).max())))
    # duck to kick: the app's sidechain follower on the track volume
    kick=[{'name':'Kick','preset':'kick','clips':[{'start':0,'len':8,'notes':[{'p':36,'s':i,'l':.5,'v':1} for i in range(8)]}]}]
    build([{'p':31,'s':0,'l':8,'v':1}],145,8,extra=kick)
    nm=al.run("(()=>{const t=S.tracks[1],a=sbsKick(t),f=mkFx('side');f.p.src=a.id;t.fx.push(f);changed(true);return a.name+', '+sbsDuck(t).length+' effect'})()")
    x,sr=al.render(b0=0,b1=8,only='S');y=np.abs(x[0].astype(np.float64));bt=60/145*sr;win=lambda i,o:y[int((i+o)*bt):int((i+o)*bt)+int(.03*sr)].max();x2,_=al.render(b0=0,b1=8,only='S')
    print('Duck to kick (kick track found: %s): level of the held sub 0.03 beats after a beat %.1f dB, 0.25 beats after %.1f dB, 0.8 beats after %.1f dB; two renders identical %s'%(nm,np.mean([db(win(i,.03)) for i in range(2,7)]),np.mean([db(win(i,.25)) for i in range(2,7)]),np.mean([db(win(i,.8)) for i in range(2,7)]),np.array_equal(x,x2)))
if want('same'):
    print('--- two renders, and a note moved in time')
    N=[{'p':31,'s':0,'l':1,'v':1},{'p':34,'s':.9,'l':1,'v':.8},{'p':29,'s':2.5,'l':.5,'v':1},{'p':31,'s':3,'l':.25,'v':.6},{'p':41,'s':3.25,'l':2,'v':1}]
    for k in ('pure','k808','phone','wide','g808','psys'):
        build(N);setp(k);a,sr=ren(0,8,tail=1);b,_=ren(0,8,tail=1);print('%-6s two renders identical: %s'%(k,np.array_equal(a,b)),end='; ')
    print()
    for sh in (293,1000,77):
        d=sh/44100*2;build([{'p':31,'s':1,'l':1,'v':1}]);setp('phone');a,sr=ren(0,8);build([{'p':31,'s':1+d,'l':1,'v':1}]);setp('phone');b,_=ren(0,8);s0=int(round(.5*sr));s1=int(round((1+d)*.5*sr));n=int(.8*sr)
        print('note moved by %d samples (not a multiple of any block): largest difference %.2e'%(s1-s0,np.abs(a[0][s0:s0+n]-b[0][s1:s1+n]).max()),end='; ')
    print()
if want('cost'):
    print('--- cost (time to render, with the app around it; the empty project takes its own share)')
    build([{'p':90,'s':0,'l':.1,'v':.01}],120,64);setp('pure');t0=time.time();ren(0,64);base=time.time()-t0
    for k,ov in (('pure',{}),('phone',{}),('k808',{}),('wide',{}),('pure',{'shp':100,'wv':'s','drv':80,'wid':100,'ss':100})):
        build([{'p':31,'s':i*.5,'l':.45,'v':1} for i in range(128)],120,64);setp(k,ov);t0=time.time();x,sr=ren(0,64);dt=time.time()-t0
        print('%-6s%s 32 s of sound in %.2f s (%.1f ms per second of sound; the same project with one short note: %.2f s)'%(k,' heaviest setting' if ov else '',dt,dt/32*1000,base))
print('errors',al.errors);al.stop()
