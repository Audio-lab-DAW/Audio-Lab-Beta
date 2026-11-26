# Psy Bass, the psytrance rolling bass instrument (v0.190): everything measured through the app's own render.
#   python3 tools/engine-tests/psybass.py [index.html] [part ...]
# parts: tune same gap env alias dc roll level compare bits cost (default: all); the Fractals demo levels are always printed first
import sys,os,json,time,numpy as np
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','remake'))
from alab import AudioLab
idx=sys.argv[1] if len(sys.argv)>1 else 'index.html';parts=set(sys.argv[2:])
want=lambda p:not parts or p in parts
al=AudioLab(idx);al.start()
print('ver',al.version,'presets',al.run("Object.keys(PSBPRE).length"),'page errors',al.errors)
rms=lambda x:float(np.sqrt(np.mean(np.asarray(x,np.float64)**2)));db=lambda v:20*np.log10(max(v,1e-30))
hz=lambda p:440*2**((p-69)/12)
PRE=al.run("Object.keys(PSBPRE)")
# the tempo each preset is made for (from its tooltip) and the pattern it is meant to play
TEMPO={'fo145':145,'fo150':150,'fract':145,'imper':145,'fobr':147,'fosq':145,'fosub':145,'prog':138,'progoff':136,'dark':150,'forest':155,'darkgal':150,'hitech':180,'hitsub':185,'goa':145,'goasq':140,'trip':145,'acid':147}
KEY={'imper':29,'fract':33}
al.tracks=json.loads(al.run("JSON.stringify(Object.fromEntries(S.tracks.map(t=>[t.name,t.id])))"))
kx,ksr=al.render(b0=64,b1=96,only='Kick');bx,_=al.render(b0=64,b1=96,only='Bass')
print('Fractals Kick %.5f dB'%db(rms(kx)));print('Fractals Bass %.5f dB'%db(rms(bx)))
DEMO=al.run("(()=>{const t=S.tracks.find(t=>t.name==='Bass');const o=[];for(const c of t.clips)for(const n of c.notes)if(!n.m){const b=c.start+n.s-c.off;if(b>=64&&b<96)o.push({p:n.p,s:b-64,l:n.l,v:n.v})}return JSON.stringify(o)})()")
DEMO=json.loads(DEMO)
def build(notes,tempo=145,ln=16,extra=None):
    tr=[{'name':'P','preset':'psyb','clips':[{'start':0,'len':ln,'notes':notes}]}]
    if extra:tr=extra+tr
    al.build({'bpm':tempo,'tracks':tr})
def setp(k,ov=None):
    al.run("(()=>{const I=S.tracks[S.tracks.length-1].inst;for(const k in I)if(k!=='preset')delete I[k];Object.assign(I,psbParams('%s'),%s);I.ipk='%s';changed(true)})()"%(k,json.dumps(ov or {}),k))
def ren(b0=0,b1=8,tail=0,**kw):
    x,sr=al.render(b0=b0,b1=b1,tail=tail,**kw);return np.asarray(x,np.float64),sr
def kbbb(n,ln=.25):return[{'p':33,'s':i*.25,'l':ln,'v':1} for i in range(n) if i%4]
def pat_notes(k,key,beats):
    """the clip each preset is meant for: K-B-B-B 16ths, offbeat 8ths, galloping, or one long note for the triplet roll"""
    if k=='progoff':return[{'p':key,'s':b+.5,'l':.5,'v':1} for b in range(beats)]
    if k=='darkgal':return[{'p':key,'s':i*.25,'l':.25,'v':1} for i in range(beats*4) if i%4>=2]
    if k=='trip':return[{'p':key,'s':0,'l':beats,'v':1}]
    return[{'p':key,'s':i*.25,'l':.25,'v':.8 if i%4==1 else 1} for i in range(beats*4) if i%4]
def amp_at(seg,sr,f,w):
    n=np.arange(len(seg));return 2*abs(np.sum(seg*w*np.exp(-2j*np.pi*f*n/sr)))/w.sum()

if want('tune'):
    print('--- tuning (held note, filter open, 4 s, frequency from the phase of the wave)')
    for p in (24,28,29,31,33,40,45,52,57):
        build([{'p':p,'s':0,'l':10,'v':1}],120);setp('fo145',{'go':False,'as':1,'cut':8000,'fe':0,'sat':0,'tk':0});x,sr=ren(0,10);seg=x[0][int(.5*sr):int(4.5*sr)];f0=hz(p);n=np.arange(len(seg))
        z=seg*np.exp(-2j*np.pi*f0*n/sr);B=int(sr*.25);ph=np.unwrap(np.angle([z[i:i+B].sum() for i in range(0,len(z)-B,B)]));sl=np.polyfit(np.arange(len(ph))*B/sr,ph,1)[0]/(2*np.pi)
        print('key %2d  should be %9.4f Hz  is %9.4f Hz  off by %+.5f Hz'%(p,f0,f0+sl,sl))

if want('same'):
    print('--- every note of a 16th roll the same, sample for sample (from 1 ms before a note to 1 ms before the next step)')
    for k in ('fo145','fract','dark','hitech','forest','acid'):
        T=TEMPO[k];build([{'p':KEY.get(k,33),'s':i*.25,'l':.25,'v':1} for i in range(64) if i%4],T);setp(k,{'pon':False});x,sr=ren(0,16);y=x[0]
        st=60/T/4;F=[int(round(i*st*sr)) for i in range(64) if i%4];a=int(.001*sr);L=int(st*sr)-2*a
        seg=[y[f-a:f+L] for f in F];d=max(np.abs(s-seg[0]).max() for s in seg[1:])
        print('%-7s %d BPM: %d notes, largest difference from the first note %.3g (peak %.3f); left and right identical %s'%(k,T,len(F),d,np.abs(y).max(),np.array_equal(x[0],x[1])))
    build([{'p':33,'s':i*.25,'l':.25,'v':1} for i in range(64) if i%4],145);setp('fo145',{'rt':False});x,sr=ren(0,16);y=x[0];st=60/145/4;F=[int(round(i*st*sr)) for i in range(64) if i%4];a=int(.001*sr);L=int(st*sr)-2*a
    seg=[y[f-a:f+L] for f in F];print('Restart off (free running): largest difference %.3g of the peak (should differ)'%(max(np.abs(s-seg[0]).max() for s in seg[1:])/np.abs(y).max()))

if want('gap'):
    print('--- every preset at its tempo: is the bass below -60 dB (against its own peak) before each kick? Level in the last millisecond before the kick, and how long it is quiet before it')
    worst=-999
    for k in PRE:
        T=TEMPO[k];key=KEY.get(k,31);build(pat_notes(k,key,16),T);setp(k,{'pon':k=='trip'});x,sr=ren(0,16);y=np.abs(x[0]);pk=y.max();bt=60/T*sr
        lv=[];qt=[]
        for b in range(1,16):
            kf=int(round(b*bt));lv.append(db(y[kf-int(.001*sr):kf].max()/pk));w=y[kf-int(bt):kf]>pk*1e-3;qt.append((len(w)-1-np.nonzero(w)[0][-1])/sr*1000 if w.any() else bt/sr*1000)
        worst=max(worst,max(lv));print('%-7s %3d BPM key %d: last ms before a kick %7.1f dB at most; quiet (under -60 dB) for %5.1f to %5.1f ms before each kick'%(k,T,key,max(lv),min(qt),max(qt)))
    print('worst of all presets: %.1f dB'%worst)
    build(pat_notes('fo145',33,8),145);setp('fo145',{'go':False,'ad':.3,'ar':.2});x,sr=ren(0,8);y=np.abs(x[0]);pk=y.max();bt=60/145*sr;print('for comparison, Gate off with a 300 ms decay and 200 ms release: last ms before a kick %.1f dB'%max(db(y[int(round(b*bt))-int(.001*sr):int(round(b*bt))].max()/pk) for b in range(1,8)))

if want('env'):
    print('--- envelope times measured from the output against the knobs (key 69, 440 Hz, filter open, so the level is seen within a few ms)')
    def one(ov,ln=1.0,T=120):
        build([{'p':69,'s':1,'l':ln,'v':1}],T);setp('fo145',dict({'go':False,'cut':8000,'fe':0,'sat':0,'tk':0,'res':0,'kt':0},**ov));x,sr=ren(0,4);return x[0],sr,int(round(.5*sr))
    for aa in (.002,.01,.03):
        y,sr,s0=one({'aa':aa,'ad':1,'as':1,'ac':0});e=np.maximum.accumulate(np.abs(y[s0:s0+int(.1*sr)]));t=np.argmax(e>=.995*e[-1])/sr*1000;print('attack %5.1f ms (straight): reaches 99.5%% of full level after %5.2f ms'%(aa*1000,t))
    for ad,ac in ((.04,0),(.075,60),(.15,60),(.3,100)):
        y,sr,s0=one({'aa':.0001,'ad':ad,'as':0,'ac':ac});a=np.abs(y);nz=np.nonzero(a>1e-9)[0];pk=a.max();m60=np.nonzero(a>pk*1e-3)[0]
        print('decay %5.0f ms, curve %3d%%: sound ends (exact zero) %6.2f ms after the start; under -60 dB after %6.2f ms'%(ad*1000,ac,(nz[-1]-s0)/sr*1000,(m60[-1]-s0)/sr*1000))
    for ar in (.01,.02,.05,.15):
        y,sr,s0=one({'aa':.0005,'ad':1,'as':1,'ar':ar,'ac':60},ln=.2);a=np.abs(y);nz=np.nonzero(a>1e-9)[0];e0=s0+int(round(.2*.5*sr))
        print('release %5.0f ms: sound ends %6.2f ms after the note ends'%(ar*1000,(nz[-1]-e0)/sr*1000))
    # filter envelope: key 69 (440 Hz), cutoff 1 kHz opening 2 octaves; the level of the 4th overtone (1760 Hz) over time, Hann window of 3 cycles
    for fd in (.03,.045,.1):
        build([{'p':69,'s':1,'l':1,'v':1}],120);setp('fo145',{'go':False,'as':1,'ad':1,'fd':fd,'fe':2,'fc':0,'sat':0,'tk':0,'res':0,'cut':1000,'kt':0});x,sr=ren(0,4);y=x[0];s0=int(round(.5*sr))
        f=4*440;W=int(round(3*sr/440));n=np.arange(W);hw=np.hanning(W);hop=int(.0005*sr);lv=[]
        for i in range(0,int(.25*sr),hop):lv.append(db(2*abs(np.sum(y[s0+i:s0+i+W]*hw*np.exp(-2j*np.pi*f*n/sr)))/hw.sum()))
        lv=np.array(lv);fin=lv[-1];t=np.nonzero(np.abs(lv-fin)>.5)[0];print('filter close time %5.0f ms (straight): the 4th overtone is within 0.5 dB of its final level %5.1f ms after the start (the 6.8 ms window ends there)'%(fd*1000,(t[-1]+1)*.5+W/sr*1000 if len(t) else 0))

def other(seg,sr,f0,fmax):
    N=len(seg);w=np.kaiser(N,38);X=np.abs(np.fft.rfft(seg*w));fr=np.fft.rfftfreq(N,1/sr);ref=X.max();wd=16*sr/N
    keep=(fr<fmax)&(fr>12)
    for k in range(0,int(sr/2/f0)+2):keep&=np.abs(fr-k*f0)>wd
    i=np.argmax(X*keep);return db(X[i]/ref),fr[i]
if want('alias'):
    print('--- aliasing: strongest thing that is not an overtone of the note, below 17 kHz, in dB under the strongest overtone. Note held (sustain 100%%), filter at rest and filter held fully open (Stays open 100%%)')
    worst=-999
    for k in PRE:
        row=[]
        for p in (28,40,57):
            for fs in (0,1):
                build([{'p':p,'s':0,'l':8,'v':1}],120);setp(k,{'go':False,'as':1,'fs':fs,'pon':False});x,sr=ren(0,8);seg=x[0][int(1.0*sr):int(1.0*sr)+131072];o,fo=other(seg,sr,hz(p),17000);row.append(o);worst=max(worst,o)
        print('%-7s key 28 (41 Hz) rest %6.1f open %6.1f | key 40 (82 Hz) %6.1f %6.1f | key 57 (220 Hz) %6.1f %6.1f'%((k,)+tuple(row)))
    print('worst of all presets: %.1f dB'%worst)
    for nm,ov in (('saw, filter open 8 kHz, drive 100%, resonance 50%',{'cut':8000,'fe':0,'drv':100,'res':50,'sat':0}),('saw + square, 8 kHz, drive 100%, saturation 60%',{'cut':8000,'fe':0,'mix':50,'drv':100,'sat':60}),('stress: 8 kHz, drive 100%, saturation 100%, resonance 60%',{'cut':8000,'fe':0,'drv':100,'sat':100,'res':60})):
        r=[]
        for p in (28,45,57,69,81):
            build([{'p':p,'s':0,'l':8,'v':1}],120);setp('fo145',dict({'go':False,'as':1},**ov));x,sr=ren(0,8);seg=x[0][int(1.0*sr):int(1.0*sr)+131072];r.append('%d: %6.1f'%(p,other(seg,sr,hz(p),17000)[0]))
        print('%-58s %s'%(nm,' | '.join(r)))

if want('dc'):
    print('--- DC (mean over whole cycles of a held note, against the peak)')
    out=[]
    for k in PRE:
        build([{'p':33,'s':0,'l':8,'v':1}],120);setp(k,{'go':False,'as':1,'fs':.5,'pon':False});x,sr=ren(0,8);per=sr/hz(33);n=int(round(per*200));seg=x[0][int(sr):int(sr)+n];out.append('%s %.0f'%(k,db(abs(seg.mean())/np.abs(seg).max())))
    print('dB under the peak: '+', '.join(out))
    build(kbbb(64),145);setp('dark');x,sr=ren(0,16);print('rolling dark preset, mean of the whole render: %.1f dB under the peak'%db(abs(x[0].mean())/np.abs(x[0]).max()))

if want('roll'):
    print('--- the roll pattern: one long note gives the 16ths, exactly on the grid of the song')
    def onsets(y,sr,thr):
        """a note starts where the sound rises above thr after at least 5 ms below it"""
        a=(np.abs(y)>thr).astype(np.int64);c=np.concatenate([[0],np.cumsum(a)]);W=int(.005*sr);i=np.arange(len(a));prev=c[i]-c[np.maximum(0,i-W)]
        return np.nonzero((a==1)&(prev==0))[0]
    for T,pk,pdv,start in ((145,'kbbb',4,0),(138,'kbbb',4,0),(150,'gal',4,0),(145,'trip',3,0),(145,'kbbb',4,1.37)):
        build([{'p':33,'s':start,'l':16-start,'v':1}],T);setp('fo145',{'pon':True});al.run("(()=>{const I=S.tracks[0].inst,q=PSBPAT['%s'];I.ppk='%s';I.pat=q[1].padEnd(16,'0');I.poc=q[2].padEnd(16,'0');I.pdv=q[3];changed(true)})()"%(pk,pk))
        x,sr=ren(0,16);y=x[0];on=onsets(y,sr,np.abs(y).max()*1e-3)
        pat=al.run("PSBPAT['%s'][1]"%pk);n=pdv*4;sb=1/pdv;exp=[j*sb*60/T for j in range(int(np.ceil(start/sb-1e-6)),int(16/sb)) if pat[j%n]!='0']
        ef=np.array([int(round(t*sr)) for t in exp]);ok=len(on)==len(ef);d=(on-ef) if ok else None
        print('%3d BPM %-5s note from beat %.2f: %d notes, expected %d; onset minus grid (samples): %s'%(T,pk,start,len(on),len(ef),('all %d'%d[0]) if ok and np.all(d==d[0]) else (d[:12] if ok else on[:8]/sr)))
    # live tempo against the pattern: the playing note picks the tempo at its start
    build([{'p':33,'s':0,'l':8,'v':1}],145);setp('fo145',{'pon':True});a,sr=ren(0,8);b,_=ren(0,8);print('two renders of the roll identical:',np.array_equal(a,b))

if want('level'):
    print('--- level of every preset against the Fractals kick: K-B-B-B 16ths (the pattern each is meant for) at its tempo, full velocity')
    kp=db(np.abs(kx).max());kr=db(rms(kx));print('Fractals Kick: peak %.1f dBFS, average %.1f dB | Fractals Bass: peak %.1f dBFS, average %.1f dB'%(kp,kr,db(np.abs(bx).max()),db(rms(bx))))
    for k in PRE:
        T=TEMPO[k];build(pat_notes(k,KEY.get(k,31),8),T);setp(k,{'pon':k=='trip'});x,sr=ren(0,8);l1=(db(np.abs(x).max()),db(rms(x)))
        build(pat_notes(k,24,4)+[{'p':43,'s':4+n['s'],'l':n['l'],'v':1} for n in pat_notes(k,43,4)],T);setp(k,{'pon':k=='trip'});x2,sr=ren(0,8)
        print('%-7s peak %6.1f dBFS (%+5.1f to the kick peak), average %6.1f dB (%+5.1f) | keys 24 and 43 peak %6.1f'%(k,l1[0],l1[0]-kp,l1[1],l1[1]-kr,db(np.abs(x2).max())))

if want('compare'):
    print('--- the default preset against the Fractals demo\'s Bass track (Plant), on the same track (same EQ, sidechain and volume), same notes, beats 64 to 96 alone')
    sr=ksr;st=60/145/4
    def profile(y):
        """per note: level over the 16th in 5 ms steps (dB against the note's peak), and the spectrum of the notes in bands"""
        N=[n for n in DEMO];env=[];spec=[]
        for n in N:
            s=int(round((n['s'])*60/145*sr));seg=y[s:s+int(st*sr)]
            if len(seg)<int(st*sr):continue
            env.append([rms(seg[i:i+int(.005*sr)]) for i in range(0,int(st*sr)-int(.005*sr),int(.005*sr))])
            X=np.abs(np.fft.rfft(seg*np.hanning(len(seg)),8192))**2;fr=np.fft.rfftfreq(8192,1/sr);spec.append([X[(fr>=a)&(fr<b)].sum() for a,b in BANDS])
        env=np.mean(env,0);spec=np.mean(spec,0);return env,spec
    BANDS=[(30,70),(70,140),(140,280),(280,560),(560,1120),(1120,2240),(2240,4480),(4480,9000)]
    pe,ps=profile(bx[0].astype(np.float64))
    al.run("(openDemoFractals(),1)");al.page.wait_for_timeout(4000)
    al.tracks=json.loads(al.run("JSON.stringify(Object.fromEntries(S.tracks.map(t=>[t.name,t.id])))"))
    print('level over a 16th in 5 ms steps (dB against the loudest step), then the spectrum of the notes in octave bands from %s Hz (dB against the 30-70 Hz band)'%', '.join(str(a) for a,b in BANDS))
    print('  %-22s peak %5.1f average %5.1f | '%('Plant (the demo)',db(np.abs(bx).max()),db(rms(bx)))+' '.join('%4.0f'%v for v in 20*np.log10(pe/pe.max()+1e-9))+' | '+' '.join('%5.1f'%v for v in 10*np.log10(ps/ps[0])))
    for k in json.loads(os.environ.get('PSB_CMP','["fo145","fract"]')):
        ov=json.loads(os.environ.get('PSB_OV','{}')) if k=='fract' else {}
        al.run("(()=>{const t=S.tracks.find(t=>t.name==='Bass');t.inst=Object.assign({preset:'psyb'},psbParams('%s'),%s,{ipk:'%s'});changed(true)})()"%(k,json.dumps(ov),k))
        nx,_=al.render(b0=64,b1=96,only='Bass');nx=np.asarray(nx,np.float64);ne,ns=profile(nx[0])
        print('  %-22s peak %5.1f average %5.1f | '%('Psy Bass '+k,db(np.abs(nx).max()),db(rms(nx)))+' '.join('%4.0f'%v for v in 20*np.log10(ne/ne.max()+1e-9))+' | '+' '.join('%5.1f'%v for v in 10*np.log10(ns/ns[0])))

if want('bits'):
    print('--- two renders bit-identical, and a note moved in time sounds the same')
    N=[{'p':31,'s':0,'l':1,'v':1},{'p':33,'s':1.25,'l':.25,'v':.8},{'p':29,'s':2.5,'l':.5,'v':1},{'p':31,'s':3,'l':.25,'v':.6},{'p':41,'s':3.25,'l':2,'v':1}]
    for k in ('fo145','goa','forest','hitsub','trip','acid'):
        build(N);setp(k);a,sr=ren(0,8,tail=1);b,_=ren(0,8,tail=1);print('%-6s two renders identical: %s'%(k,np.array_equal(a,b)),end='; ')
    print()
    for sh in (293,1000,77):
        d=sh/sr*2;build([{'p':31,'s':1,'l':.25,'v':1}],120);setp('fo145');a,sr=ren(0,8);build([{'p':31,'s':1+d,'l':.25,'v':1}],120);setp('fo145');b,_=ren(0,8);s0=int(round(.5*sr));s1=int(round((1+d)*.5*sr));n=int(.2*sr)
        print('note moved by %d samples: largest difference %.2e'%(s1-s0,np.abs(a[0][s0-50:s0+n]-b[0][s1-50:s1+n]).max()),end='; ')
    print()

if want('cost'):
    print('--- cost: 64 beats of rolling bass against the same project with one short note')
    def tm(notes,k='fo145'):
        build(notes,145,64);setp(k);ren(0,2);t=time.time();ren(0,64);return time.time()-t
    t0=min(tm([{'p':33,'s':0,'l':.25,'v':1}]) for _ in range(2));sec=64*60/145
    for k in ('fo145','dark','fosub'):
        t1=min(tm(kbbb(256),k) for _ in range(2));print('%-6s %.1f s of sound: %.2f s against %.2f s empty, so %.1f ms per second of sound'%(k,sec,t1,t0,(t1-t0)/sec*1000))
    build([{'p':33,'s':0,'l':64,'v':1}],145,64);setp('fo145',{'pon':True});ren(0,2);t=time.time();ren(0,64);print('roll from one note: %.2f s'%(time.time()-t))
print('page errors at the end:',al.errors)
al.stop()
