# Bounce, the bouncing-ball instrument (v0.189): everything measured through the app's own render.  python3 tools/engine-tests/bounce_instrument.py [index.html] [part ...]
# parts: same presets grid impact shift hold auto voices cost (default: all); the Fractals demo levels are always printed first
import sys,os,json,time,numpy as np
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','remake'))
from alab import AudioLab
idx=sys.argv[1] if len(sys.argv)>1 else 'index.html';parts=set(sys.argv[2:])
want=lambda p:not parts or p in parts
al=AudioLab(idx);al.start()
print('ver',al.version,'errors after load',al.errors,'presets',al.run("Object.keys(BBIPRE).length"))
db=lambda v:20*np.log10(max(v,1e-12));rms=lambda x:float(np.sqrt(np.mean(x.astype(np.float64)**2)))
al.tracks=json.loads(al.run("JSON.stringify(Object.fromEntries(S.tracks.map(t=>[t.name,t.id])))"))
kx,_=al.render(b0=64,b1=96,only='Kick');bx,_=al.render(b0=64,b1=96,only='Bass')
print('Fractals Kick %.5f dB'%db(rms(kx)));print('Fractals Bass %.5f dB'%db(rms(bx)))
PRE=json.loads(al.run("JSON.stringify(Object.keys(BBIPRE))"))
def build(notes,ov=None,pk='marimba',tempo=120,ln=16):
    al.build({'bpm':tempo,'tracks':[{'name':'B','preset':'bball','clips':[{'start':0,'len':ln,'notes':notes}]}]})
    al.run("(()=>{const I=S.tracks[0].inst;for(const k in I)if(k!=='preset')delete I[k];Object.assign(I,bbiParams('%s'),%s);I.ipk='%s';bbiTail(I);changed(true)})()"%(pk,json.dumps(ov or {}),pk))
def ren(b0=0,b1=8,tail=0):
    x,sr=al.render(b0=b0,b1=b1,tail=tail);return x.astype(np.float64),sr
jr=lambda x:int(np.floor(x+.5))  # rounding as in JavaScript
def onsets(y,quiet=1e-7,gap=40):
    a=np.abs(y);on=[]
    for i in np.nonzero(a>quiet*10)[0]:
        if i>=gap and a[i-gap:i].max()<quiet and (not on or i-on[-1]>gap):on.append(int(i))
    return on
if want('same'):
    r=al.run("""(()=>{let worst=0,n=0;for(const sync of ['off','1/16','1/8 triplet','1/4','1/2','1 bar'])for(const bmode of ['free','steady','half','third','round'])for(const fric of [0,20,60])for(const grav of [.3,1,3])for(const vel of [.3,.9]){
      const p=Object.assign({},BN0,{sync,bmode,fric,grav,speed:1.3,mass:1.7,life:9}),B=bnBalls(p,[{p:60,s:0,l:1,v:vel}],.5)[0],P=bbiPar(Object.assign(bbiParams('marimba'),{sync,bmode,fric,grav,speed:1.3,mass:1.7,life:9}),1),C=BBIC.ball(P,vel,.5);
      if(B.tk.length!==C.tk.length||B.end!==C.end)return 'differs at '+[sync,bmode,fric,grav];for(let k=0;k<B.tk.length;k++){worst=Math.max(worst,Math.abs(B.tk[k]-C.tk[k]),Math.abs(B.vk[k]-C.vk[k]));n++}}
     return n+' landings compared, largest difference '+worst})()""")
    print('--- landing times and speeds of Bounce against Bouncy Notes (same formulas):',r)
if want('presets'):
    print('--- every preset: a phrase of single notes and a chord; peak, level, NaN, the end of the sound, two renders the same')
    notes=[{'p':60,'s':0,'l':1,'v':.9},{'p':64,'s':1,'l':1,'v':.7},{'p':67,'s':2,'l':1,'v':.8},{'p':72,'s':3,'l':1,'v':1},{'p':48,'s':4,'l':2,'v':1},{'p':55,'s':4,'l':2,'v':1},{'p':64,'s':4,'l':2,'v':1},{'p':72,'s':4,'l':2,'v':1}]
    for k in PRE:
        build(notes,pk=k);tl=float(al.run("S.tracks[0].inst.r"))
        x,sr=ren(0,8,tail=tl+1);y,_=ren(0,8,tail=tl+1);n=x.shape[1]
        print('%-8s peak %6.1f dBFS  rms %6.1f dB  NaN %-5s  last 0.5 s %8.1f dB  identical %s  (tail %.1f s)'%(k,db(np.abs(x).max()),db(rms(x)),np.isnan(x).any(),db(np.abs(x[:,-int(.5*sr):]).max()),np.array_equal(x,y),tl))
if want('grid'):
    print('--- landings on the grid: one note at beat 1, drum with 30 ms decay so every hit starts from silence; frame of every hit against the formula')
    for tempo in (120,90,137,174):
        for sync,bm in (('1/4','steady'),('1/8 triplet','steady'),('1/16','steady'),('1/8','third'),('1/2','half'),('1 bar','round')):
            build([{'p':69,'s':1,'l':3.9,'v':1}],{'mat':'d','dec':.03,'clk':0,'dmp':0,'sync':sync,'bmode':bm,'life':30,'hold':'n'},tempo=tempo)
            x,sr=ren(0,6,.3);on=onsets(x[0]);spb=60/tempo
            T=json.loads(al.run("JSON.stringify((()=>{const P=bbiPar(S.tracks[0].inst,1),B=BBIC.ball(P,1,60/S.bpm);return B.tk.map(t=>t/B.sp)})())"))
            want_=[jr((spb+t)*sr) for t in T if t<3.9*spb-1e-9];gap_ok=[w for w in want_ if True]
            # hits closer than 4 decay times blur into each other, so compare the ones the detector can see: every onset must be a formula frame, and the first ones all present
            ok=all(o in want_ for o in on);first=on[0]==jr(spb*sr)
            grid=sync in ("1/4","1/8 triplet","1/16") and all(abs(w-jr((1+i*float(al.run("SDIV['%s']"%sync)))*spb*sr))==0 for i,w in enumerate(want_))
            print('%3d bpm %-11s %-6s hits %2d of %2d seen, first on beat 1 %s, every hit on a formula frame %s%s'%(tempo,sync,bm,len(on),len(want_),first,ok,(', on the grid of the song %s'%grid) if sync in ('1/4','1/8 triplet','1/16') else ''))
if want('impact'):
    print('--- loudness and brightness follow the impact: 1/4 halving, Dynamics 50%, Brightness 60%; level and brightness (centroid) of each hit')
    build([{'p':60,'s':1,'l':4,'v':1}],{'mat':'m','dec':.25,'clk':0,'sync':'1/4','bmode':'half','life':30})
    x,sr=ren(0,6,.3);y=x[0];spb=.5;T=[0,1,1.5,1.75,1.875]
    for i,t in enumerate(T):
        a=jr((1+t)*spb*sr);b=a+int(.04*sr);seg=y[a:b];X=np.abs(np.fft.rfft(seg*np.hanning(len(seg))));f=np.fft.rfftfreq(len(seg),1/sr)
        print('hit %d at beat %.3f: peak %6.1f dB, brightness (centroid) %6.0f Hz'%(i+1,1+t,db(np.abs(seg).max()),(X*f).sum()/X.sum()))
    build([{'p':60,'s':1,'l':4,'v':1}],{'mat':'m','dec':.25,'clk':0,'sync':'1/4','bmode':'half','life':30,'dyn':0,'bfol':0})
    x,sr=ren(0,6,.3);y=x[0];print('Dynamics 0% and Brightness 0%: peaks',' '.join('%.1f'%db(np.abs(y[jr((1+t)*spb*sr):jr((1+t)*spb*sr)+int(.04*sr)]).max()) for t in T))
    for v in (1,.5,.25):
        build([{'p':60,'s':1,'l':1,'v':v}],{'mat':'w','sync':'1/4','bmode':'steady','hold':'n'});x,sr=ren(0,3,.5);print('velocity %.2f: peak %.1f dB'%(v,db(np.abs(x).max())))
    print('--- pitch from the key: strongest partial of a long glass hit')
    for p in (48,60,69,81):
        build([{'p':p,'s':1,'l':1,'v':1}],{'mat':'s','dec':3,'clk':0,'sync':'1/4','bmode':'steady','hold':'n','hard':20});x,sr=ren(0,4,0);seg=x[0][int(.6*sr):int(.6*sr)+65536]
        X=np.abs(np.fft.rfft(seg*np.hanning(len(seg))));f=np.fft.rfftfreq(len(seg),1/sr);i=np.argmax(X);print('key %d: should be %.2f Hz, strongest at %.2f Hz'%(p,440*2**((p-69)/12),f[i]))
if want('shift'):
    print('--- a phrase moved by 293 samples sounds exactly the same, moved (nothing depends on where the audio blocks start)')
    for pk in ('marimba','rain','ratchet','tabla'):
        n1=[{'p':60,'s':1,'l':1.5,'v':.9},{'p':67,'s':2,'l':1.5,'v':.7}];d=293/44100/0.5
        build(n1,pk=pk);x,sr=ren(0,8,0);build([dict(n,s=n['s']+d) for n in n1],pk=pk);y,_=ren(0,8,0)
        print('%-8s largest difference %.2e (peak %.3f)'%(pk,np.abs(y[:,293:]-x[:,:-293]).max(),np.abs(x).max()))
if want('hold'):
    print('--- "Ball stops: at note end": no hit after the end of the note; "when it rests": the ball goes on')
    for h in ('n','r'):
        build([{'p':69,'s':1,'l':1.6,'v':1}],{'mat':'d','dec':.03,'clk':0,'sync':'1/4','bmode':'steady','hold':h,'life':30});x,sr=ren(0,8,0);on=onsets(x[0])
        print('hold %s: hits at beats %s'%(h,[round(o/sr/.5,3) for o in on]))
if want('auto'):
    print('--- Auto: a key held for 2 beats drops a new ball every 1/4 (each one bounces 1/8 steady until the note ends): balls at 1 and 2')
    build([{'p':69,'s':1,'l':2,'v':1}],{'mat':'d','dec':.03,'clk':0,'sync':'1/8','bmode':'steady','hold':'n','auto':True,'ivl':'1/4','life':30});x,sr=ren(0,6,0);on=onsets(x[0])
    print('hits at beats',[round(o/sr/.5,3) for o in on],'(should be 1, 1.5, 2, 2.5; at 2 and 2.5 two balls land together)')
if want('voices'):
    print('--- Voices: a new ball takes the place of the oldest; Voices 1 with notes on beats 1 (A) and 2 (E), steady 1/4: the A ball stops when the E ball comes')
    build([{'p':69,'s':1,'l':.5,'v':1},{'p':76,'s':2,'l':.5,'v':1}],{'mat':'d','dec':.03,'clk':0,'sync':'1/4','bmode':'steady','life':30,'voices':1});x,sr=ren(0,5,0);y=x[0]
    for b in (1,1.25,1.5,2,2.25,3,3.25,4):
        a=jr(b*.5*sr);seg=y[a:a+2048];X=np.abs(np.fft.rfft(seg*np.hanning(2048)));f=np.fft.rfftfreq(2048,1/sr);print('beat %.2f: %s'%(b,'%.0f Hz'%f[np.argmax(X)] if np.abs(seg).max()>1e-4 else 'silent'),end='; ')
    print()
if want('cost'):
    print('--- cost: 32 s of sound')
    rows=[{'p':60+(i*7)%24,'s':i*.5,'l':.5,'v':.8} for i in range(64)]
    for pk in ('marimba','chimes','rain','pluck8'):
        build(rows,pk=pk,ln=32);t0=time.time();x,sr=ren(0,64,0);dt=time.time()-t0;print('%-8s 64 notes, 32 s: rendered in %.2f s, peak %.1f dB'%(pk,dt,db(np.abs(x).max())))
    al.build({'bpm':120,'tracks':[{'name':'B','preset':'bball','clips':[{'start':0,'len':32,'notes':[{'p':60,'s':0,'l':.1,'v':.8}]}]}]});t0=time.time();x,sr=ren(0,64,0);print('one short note, 32 s: rendered in %.2f s'%(time.time()-t0))
print('errors',al.errors);al.stop()
