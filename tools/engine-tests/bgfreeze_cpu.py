"""Background freeze (v0.201): audio-thread load while playing, with and without background freeze (switching it off drops the recordings, so each run with it waits until they are made again).
Measured as the processor time of Chromium's real-time audio thread (Linux /proc), in % of one core.
python3 tools/engine-tests/bgfreeze_cpu.py [index.html]"""
import sys,os,json,time,glob
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','remake'))
from alab import AudioLab
def threads():
    out={}
    for p in glob.glob('/proc/[0-9]*/task/*'):
        try:
            comm=open(p+'/comm').read().strip();st=open(p+'/stat').read().rsplit(')',1)[1].split();out[p]=(comm,int(st[11])+int(st[12]))
        except Exception: pass
    return out
def rt(sec):
    a=threads();time.sleep(sec);b=threads();v=0
    for k,(c,u) in b.items():
        if k in a and c.startswith('Realtime Audio'): v+=u-a[k][1]
    return v/sec  # % of one core (clock ticks are 1/100 s)
al=AudioLab(sys.argv[1] if len(sys.argv)>1 else 'index.html');al.start()
print('version',al.version,'errors after load',al.errors)
al.run("(async()=>{ensureCtx();await ctx.resume();return 1})()")
def ready(b0):
    return al.run("""(()=>{let n=0,m=0;const st=performance.now();for(const t of S.tracks){if(!bgfTrackOK(t))continue;const s=BGF.tsig.get(t.id);if(!s)return -1;for(const c of t.clips){if(!bgfClipOK(t,c))continue;if(c.start+c.len<%f||c.start>%f)continue;m++;if(BGF.cache.has(bgfKey(s.s,c)))n++}}return m?n/m:1})()"""%(b0,b0+24))
def measure(label,b0,sec=8):
    out={}
    for on in (True,False,True,False):
        if on:
            al.run("(()=>{UI.bgFreeze=true;pos=%f;return 1})()"%b0);t0=time.time()
            while time.time()-t0<120 and ready(b0)<1: time.sleep(1)
        al.run("(()=>{UI.bgFreeze=%s;pos=%f;start();return 1})()"%('true' if on else 'false',b0));time.sleep(1.5)
        v=rt(sec);fr=al.run("BGF.act.size");al.run("stop();1");time.sleep(1.2)
        out.setdefault(on,[]).append((v,fr))
    on=[v for v,_ in out[True]];off=[v for v,_ in out[False]]
    print('%s: audio thread %.1f %% with background freeze (%s clips from recordings at the end), %.1f %% without; runs %s / %s'%(label,sum(on)/2,[f for _,f in out[True]],sum(off)/2,[round(x,1) for x in on],[round(x,1) for x in off]),flush=True)
    al.run("UI.bgFreeze=true;1")
for b0 in (160,288):
    al.run("(()=>{pos=%f;return 1})()"%b0);t0=time.time()
    while time.time()-t0<120 and ready(b0)<1: time.sleep(2)
    print('Fractals from beat %d: %.0f %% of the clips in the next 24 beats recorded after %.0f s; tracks that may freeze: %s'%(b0,ready(b0)*100,time.time()-t0,al.run("S.tracks.filter(t=>BGF.ok.has(t.id)).map(t=>t.name).join(', ')")),flush=True)
    measure('Fractals from beat %d'%b0,b0)
print('memory %.0f MB, %s'%(al.run("BGF.bytes")/1048576,al.run("JSON.stringify(BGF.st)")))
# particle instruments
notes=[{'p':48+(k*5)%17,'s':k*.25,'l':.75,'v':.8} for k in range(64)]
rec={'bpm':120,'tracks':[{'name':'Sel','preset':'saw','clips':[]}]+[{'name':p,'preset':p,'clips':[{'start':0,'len':16,'notes':notes},{'start':16,'len':16,'notes':notes}]} for p in ('vfm','orb','bball','vgrain','wtab','crk')]}
al.build(rec);al.run("(()=>{selT=S.tracks[0].id;pos=0;return 1})()");t0=time.time()
while time.time()-t0<120 and ready(0)<1: time.sleep(2)
print('six particle and wavetable tracks: recorded after %.0f s'%(time.time()-t0))
measure('six particle and wavetable tracks',0)
print('errors',al.errors)
al.stop()
