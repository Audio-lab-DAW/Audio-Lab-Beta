"""v0.181: Bouncy Notes tied to the rhythm, melody and harmony; Bounce Delay. python3 tools/engine-tests/bounce_rhythm.py [index.html]"""
import sys,os,time,json,numpy as np
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','remake'))
from alab import AudioLab
IDX=sys.argv[1] if len(sys.argv)>1 else 'index.html'
al=AudioLab(IDX);al.start();print('ver',al.version,'errors after load',al.errors)
al.build({'bpm':120,'tracks':[{'name':'B','preset':'pluck','clips':[{'start':0,'len':16,'notes':[{'p':60,'s':0,'l':8,'v':.9}]}]}]})
al.run("(()=>{const t=S.tracks[0];t.fx.unshift(mkFx('bnotes'));changed(true);return 1})()")
def notes(js,n=9):
    al.run("(()=>{const p=S.tracks[0].fx[0].p;Object.assign(p,JSON.parse(JSON.stringify(FXPRE.bnotes.one[1])),%s);changed(false);return 1})()"%js)
    return json.loads(al.run("(()=>{const t=S.tracks[0];return JSON.stringify(mfxNotes(t,t.clips[0].notes).slice(0,%d).map(n=>[Math.round(n.s*10000)/10000,n.p,Math.round(n.v*100)/100]))})()"%n))
r=notes("{}");print('free (as before): starts',[x[0] for x in r][:6])
r=notes("{sync:'1/4',bmode:'steady',life:30}");print('1/4 steady: starts',[x[0] for x in r])
r=notes("{sync:'1/4',bmode:'half'}");print('1/4 halving: starts',[x[0] for x in r][:7],'gaps',[round(r[i+1][0]-r[i][0],4) for i in range(5)])
r=notes("{sync:'1/4',bmode:'third'}");print('1/4 two thirds: gaps',[round(r[i+1][0]-r[i][0],4) for i in range(5)])
r=notes("{sync:'1 bar',bmode:'round',fric:30,life:30}",40);print('whole round in a bar: first gaps',[round(r[i+1][0]-r[i][0],4) for i in range(4)],'last start %.4f of %d bounces (the row ends at beat 4)'%(r[-1][0],len(r)))
r=notes("{sync:'1/8 triplet',bmode:'steady',life:30,speed:2.5,grav:3}");print('1/8 triplet steady with other Speed and Gravity: starts',[x[0] for x in r][:6])
al.run("S.bpm=90;changed(false)");r=notes("{sync:'1/4',bmode:'steady',life:30}");print('at 90 bpm, 1/4 steady: starts (beats)',[x[0] for x in r][:5]);al.run("S.bpm=120;changed(false)")
r=notes("{sync:'1/4',bmode:'steady',life:30,walk:'up',scale:'major'}");print('melody up the major scale from C: keys',[x[1] for x in r][:8])
r=notes("{sync:'1/4',bmode:'steady',life:30,walk:'updown',scale:'minor pentatonic'}");print('up and down, minor pentatonic: keys',[x[1] for x in r])
r=notes("{sync:'1/2',bmode:'steady',life:30,harm:'triad',scale:'major'}",9);print('chords: (start, key)',[(x[0],x[1]) for x in r])
r=notes("{sync:'1/2',bmode:'steady',life:30,harm:'7th',scale:'minor',walk:'down'}",8);print('four-note chords walking down in minor:',[(x[0],x[1]) for x in r])
r=notes("{sync:'1/4',bmode:'steady',life:30,thru:true}",5);print('with Thru on the first note is not doubled:',[(x[0],x[1]) for x in r])
def rms(x): return float(np.sqrt((x**2).mean()))
a,sr=al.render(b0=0,b1=8);b,_=al.render(b0=0,b1=8);print('render with the ratchet preset state: peak %.3f nan %s equal twice %s'%(np.abs(a).max(),bool(np.isnan(a).any()),bool(np.array_equal(a,b))))
# ---- Bounce Delay ----
al.build({'bpm':120,'tracks':[{'name':'D','preset':'pluck','clips':[{'start':0,'len':32,'notes':[{'p':72,'s':0,'l':.1,'v':.9}]}],'fx':[{'type':'bdelay','p':{}}]}]})
al.run("(()=>{const I=S.tracks[0].inst;I.d=.03;I.s=0;I.r=.02;changed(false)})()")
al.run("S.tracks[0].fx[0].on=false;changed(false)");dry,sr=al.render(b0=0,b1=12);al.run("S.tracks[0].fx[0].on=true;changed(false)")
from scipy.signal import lfilter
kd=1-np.exp(-2*np.pi*18000/sr)
for k in al.run("Object.keys(FXPRE.bdelay).join(',')").split(','):
    al.run("(()=>{const f=S.tracks[0].fx[0];Object.assign(f.p,JSON.parse(JSON.stringify(FXPRE.bdelay['%s'][1])),{mix:100,fb:0,tone:18000});f.p.pre='%s';changed(false)})()"%(k,k))
    exp=json.loads(al.run("JSON.stringify(bdTaps(S.tracks[0].fx[0].p,S.bpm).taps.map(x=>[x.t,x.g,x.pan]))"));a,_=al.render(b0=0,b1=24);b,_=al.render(b0=0,b1=24)
    # what the formula says: the dry sound again at every landing time, with its level and pan
    n=a.shape[1];want=np.zeros((2,n));d=dry[:,:n] if dry.shape[1]>=n else np.pad(dry,((0,0),(0,n-dry.shape[1])))
    for tt,g,pan in exp:
        dl=max(1,int(round(tt*sr)));ang=(pan+1)*np.pi/4
        if dl<n:
            want[0,dl:]+=d[0,:n-dl]*g*np.cos(ang)*1.41421356;want[1,dl:]+=d[1,:n-dl]*g*np.sin(ang)*1.41421356
    want=lfilter([kd],[1,-(1-kd)],want,axis=1)
    print('%-8s %2d bounces at %s ... %.3f s: difference to the formula %.2e (peak %.3f), nan %s, equal twice %s'%(k,len(exp),[round(x[0],3) for x in exp[:4]],exp[-1][0],float(np.abs(a-want).max()),np.abs(a).max(),bool(np.isnan(a).any()),bool(np.array_equal(a,b))))
al.run("(()=>{const f=S.tracks[0].fx[0];Object.assign(f.p,JSON.parse(JSON.stringify(FXPRE.bdelay.bar[1])));changed(false)})()");print('one round in a bar at 120 bpm: total %.4f s (2.0 expected)'%float(al.run("bdTaps(S.tracks[0].fx[0].p,S.bpm).total")))
al.run("(()=>{const f=S.tracks[0].fx[0];Object.assign(f.p,JSON.parse(JSON.stringify(FXPRE.bdelay.even[1])),{fb:80,mix:100});changed(false)})()");a,_=al.render(b0=0,b1=32);print('feedback 80%%, 16 s: peak %.3f nan %s last second %.1f dB'%(np.abs(a).max(),bool(np.isnan(a).any()),20*np.log10(rms(a[:,-sr:])+1e-9)))
al.run("(()=>{const f=S.tracks[0].fx[0];Object.assign(f.p,JSON.parse(JSON.stringify(FXPRE.bdelay.ball[1])),{mix:0});changed(false)})()");a,_=al.render(b0=0,b1=12);print('mix 0: difference to dry %g'%float(np.abs(a-dry[:,:a.shape[1]]).max()))
t0=time.time();al.run("(()=>{const f=S.tracks[0].fx[0];Object.assign(f.p,{mix:50,taps:24});changed(false)})()");a,_=al.render(b0=0,b1=32);print('24 bounces: 16 s of sound in %.2f s'%(time.time()-t0))
print('errors',al.errors);al.stop()
al=AudioLab(IDX);al.start();al.tracks=json.loads(al.run("JSON.stringify(Object.fromEntries(S.tracks.map(t=>[t.name,t.id])))"))
for nm in ('Kick','Bass'):
    x,sr=al.render(b0=64,b1=96,only=nm);print('Fractals %s %.5f dB'%(nm,20*np.log10(max(rms(x),1e-9))))
print('errors',al.errors);al.stop()
