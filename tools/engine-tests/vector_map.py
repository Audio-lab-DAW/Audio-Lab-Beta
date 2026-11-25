"""Vector Map (v0.177): the modulator in offline renders. python3 tools/engine-tests/vector_map.py [index.html]"""
import sys,numpy as np,json,time
import os;sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','remake'))
from alab import AudioLab
al=AudioLab(sys.argv[1] if len(sys.argv)>1 else 'index.html');al.start()
print('ver',al.version,'| effect types with crush:',al.run("Object.keys(FXDEF).filter(k=>/crush/.test(k)).join(',')"))
notes=[{'p':48+(i%4)*5,'s':i*.5,'l':.5,'v':.9} for i in range(64)]
al.build({'tempo':120,'tracks':[{'name':'T','preset':'saw' if 'saw' in al.run("Object.keys(PRESETS).join(',')").split(',') else 'pluck','clips':[{'start':0,'len':32,'notes':notes}]}]})
print('preset',al.run("S.tracks[0].inst.preset"))
al.run("(()=>{const t=S.tracks[0];t.fx.push(mkFx('filter'));const c=mkFx('bitcrush'in FXDEF?'bitcrush':Object.keys(FXDEF).find(k=>/crush/.test(k)));c.on=false;t.fx.push(c);selT=t.id;UI.modC=false;renderFx();paScan(performance.now());return 1})()");al.page.wait_for_timeout(500)
rms=lambda x:float(np.sqrt((x**2).mean()))
db=lambda v:20*np.log10(max(v,1e-12))
def seg(x,sr,n=16):
    L=x.shape[1]//n;return [x[:,i*L:(i+1)*L] for i in range(n)]
def bal(x,sr):return [round(db(rms(s[0]))-db(rms(s[1])),1) for s in seg(x,sr,8)]
def lev(x,sr):return [round(db(rms(s)),1) for s in seg(x,sr,8)]
def cen(x,sr):
    out=[]
    for s in seg(x,sr,8):
        m=np.abs(np.fft.rfft(s.mean(0)*np.hanning(s.shape[1])));f=np.fft.rfftfreq(s.shape[1],1/sr);out.append(int((m*f).sum()/max(m.sum(),1e-12)))
    return out
def setmod(routes,p=None):
    al.run("(()=>{const t=S.tracks[0],m=modNew('vmap');Object.assign(m.p,%s);m.routes=%s;for(const r of m.routes){if(r.pid==='PAN')r.pid='t:'+t.id+':pan';if(r.pid==='VOL')r.pid='t:'+t.id+':vol';if(r.pid.startsWith('FX0:'))r.pid='f:'+t.id+':'+t.fx[0].id+':'+r.pid.slice(4);if(r.pid.startsWith('FX1:'))r.pid='f:'+t.id+':'+t.fx[1].id+':'+r.pid.slice(4)}t.mods=[m];return 1})()"%(json.dumps(p or {}),json.dumps(routes)))
def chk(name,x,x2):
    print(' ',name,'rms dB',round(db(rms(x)),2),'peak',round(float(np.abs(x).max()),3),'nan',bool(np.isnan(x).any()),'equal twice',bool(np.array_equal(x,x2)),'maxdiff',float(np.abs(x-x2).max()))
B0,B1=0,32
x0,sr=al.render(b0=B0,b1=B1);print('no modulator: level per 2 s',lev(x0,sr),'L-R',bal(x0,sr))
x0b,_=al.render(b0=B0,b1=B1);print('  equal twice',bool(np.array_equal(x0,x0b)))
# 1. pan follows X of particle 1
setmod([{'pid':'PAN','d':1,'pt':0,'at':'x'}],{'spd':150})
t0=time.time();x,_=al.render(b0=B0,b1=B1);dt=time.time()-t0;x2,_=al.render(b0=B0,b1=B1)
print('pan <- X: L-R per 2 s',bal(x,sr),'(render %.1f s)'%dt);chk('pan',x,x2)
al.run("S.tracks[0].mods[0].p.seed=2;1");x3,_=al.render(b0=B0,b1=B1);print('  seed 2 differs',not np.array_equal(x,x3),'L-R',bal(x3,sr));al.run("S.tracks[0].mods[0].p.seed=1;1")
# the second half rendered alone must match the second half of the whole (same song time, same movement)
xh,_=al.render(b0=16,b1=32);n=xh.shape[1];full=x[:,x.shape[1]-n:] if x.shape[1]>=2*n else x[:,n:2*n]
print('  second half alone: L-R',[round(db(rms(s[0]))-db(rms(s[1])),1) for s in seg(xh,sr,4)],'whole, second half',bal(x,sr)[4:])
# what the picture / live playback uses at the same song time
print('  picture value and export value at 5 s:',al.run("(()=>{const t=S.tracks[0],m=t.mods[0],P=vmPar(m),o=[0,0,0,0,0],a=vmOut(vmAt(m,5,P),P,m.routes[0],o),b=[...vmOffSums().values()][0];return 'X '+a.toFixed(5)+', pan in the export '+vmOffVal(b,5,o).toFixed(5)+', base '+b.base.toFixed(3)})()"))
# 2. volume follows the distance of particle 2
setmod([{'pid':'VOL','d':-.6,'pt':1,'at':'d'}]);x,_=al.render(b0=B0,b1=B1);x2,_=al.render(b0=B0,b1=B1);print('volume <- distance: level per 2 s',lev(x,sr));chk('vol',x,x2)
# 3. filter cutoff (a built-in node) follows Y of particle 1
print('filter keys',al.run("JSON.stringify(S.tracks[0].fx[0].p)"))
setmod([{'pid':'FX0:freq','d':.8,'pt':0,'at':'y'}],{'spd':150});al.run("S.tracks[0].fx[0].p.freq=1200;1")
t0=time.time();x,_=al.render(b0=B0,b1=B1);dt=time.time()-t0;x2,_=al.render(b0=B0,b1=B1);x3,_=al.render(b0=B0,b1=B1)
print('cutoff <- Y: spectral centre per 2 s',cen(x,sr),'(render %.1f s) without:'%dt,cen(x0,sr));chk('cutoff',x,x2);print('  third render equal',bool(np.array_equal(x,x3)))
# 4. an effect that runs as a worklet (bit crusher)
al.run("(()=>{const t=S.tracks[0];t.fx[0].on=false;t.fx[1].on=true;return 1})()");print('crusher keys',al.run("JSON.stringify(S.tracks[0].fx[1].p)"))
al.run("S.tracks[0].mods=[];1");xs,_=al.render(b0=B0,b1=B1)
setmod([{'pid':'FX1:bits','d':.9,'pt':0,'at':'x'},{'pid':'FX1:rate','d':.9,'pt':1,'at':'y'}],{'spd':150})
x,_=al.render(b0=B0,b1=B1);x2,_=al.render(b0=B0,b1=B1);x3,_=al.render(b0=B0,b1=B1)
print('crusher <- X,Y: centre per 2 s',cen(x,sr),'static',cen(xs,sr));chk('crusher',x,x2);print('  third render equal',bool(np.array_equal(x,x3)),'differs from static',not np.array_equal(x,xs))
al.run("(()=>{const t=S.tracks[0];t.fx[0].on=false;t.fx[1].on=false;return 1})()")
# 5. an instrument knob: set per note
ids=json.loads(al.run("JSON.stringify([...PAREG.keys()].filter(k=>k.startsWith('c:')||k.startsWith('i:')))"));print('instrument controls',ids[:12])
cut=[k for k in ids if 'cut' in k.lower()]
if cut:
    al.run("S.tracks[0].mods=[];1");xs,_=al.render(b0=B0,b1=B1)
    al.run("(()=>{const t=S.tracks[0],m=modNew('vmap');m.p.spd=150;m.routes=[{pid:%s,d:.9,pt:0,at:'x'}];t.mods=[m];return 1})()"%json.dumps(cut[0]))
    before=al.run("JSON.stringify(S.tracks[0].inst)");x,_=al.render(b0=B0,b1=B1);x2,_=al.render(b0=B0,b1=B1)
    print('  instrument settings as before the export',al.run("(()=>{const t=S.tracks[0],r=t.mods[0].routes[0],e=PAREG.get(r.pid);return Math.abs(e.spec.n(e.get())-clamp(r.b+vmOut(vmSt(t.mods[0]).cur,vmSt(t.mods[0]).P,r,[0,0,0,0,0])*r.d,0,1))<.02})()"))
    print('instrument',cut[0],'centre per 2 s',cen(x,sr),'static',cen(xs,sr));chk('inst',x,x2)
# 6. the field itself: pure function of time
print('field at 7.3 s twice, with jumps between:',al.run("(()=>{const t=S.tracks[0],m=t.mods[0]||modNew('vmap'),P=vmPar(m),g=()=>{const F=vmAt(m,7.3,P);return [...F.x.slice(0,4),...F.y.slice(0,4)].map(v=>v.toFixed(9)).join(',')},a=g();vmAt(m,60,P);vmAt(m,.1,P);const b=g();VMC.delete(m.id);const c=g();return (a===b)+' '+(a===c)})()"))
print('time to work out the field at 10 minutes from nothing (ms):',al.run("(()=>{const m=modNew('vmap');m.p.num=16;const P=vmPar(m),t=performance.now();vmAt(m,600,P);return Math.round(performance.now()-t)})()"))
print('errors',al.errors);al.stop()
