"""Fractals export flake (lane D, 28 Nov): two offline renders that start at the same time must not share their start beat.
renderMix set the global SIDE_B0 before awaiting wlLoad; a second render starting meanwhile overwrote it, and the Sidechain effect
of the first was built on the second's beat (Fractals Bass at 0 dB: -26.74483 dB instead of -25.48699 dB).
  python3 tools/ui-tests/taskNI_sideb0.py [index.html]"""
import sys, os, json, hashlib
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'remake'))
from alab import AudioLab
al = AudioLab(sys.argv[1] if len(sys.argv) > 1 else 'index.html'); al.start()
res = []
def ok(name, c, d=''):
    res.append(bool(c)); print(('  ok  ' if c else 'FAIL  ') + name, d)
rms = lambda x: float(np.sqrt(np.mean(x.astype(np.float64) ** 2))); db = lambda v: 20 * np.log10(max(v, 1e-12))
al.page.wait_for_timeout(8000)  # let the overview map's background render finish first
al.tracks = json.loads(al.run("JSON.stringify(Object.fromEntries(S.tracks.map(t=>[t.name,t.id])))"))
al.run("S.master=0;0")
x, sr = al.render(b0=64, b1=96, only='Bass'); h0 = hashlib.md5(x.tobytes()).hexdigest()[:12]
ok('Bass alone at 0 dB is the reference', h0 == '09e0415bec5e', '%.5f dB %s' % (db(rms(x)), h0))
bid = al.tracks['Bass']
# the race, forced: another render changes SIDE_B0 while this one waits for its worklets (as the overview map's background render
# or a parallel export piece does); the start beats are off the beat grid, a whole-beat shift would not show (the pump repeats every beat)
def lvl(name, code):
    al.run("window.__nisb=null;(async()=>{try{const id=" + json.dumps(bid) + ";" + code + ";const d=a.getChannelData(0);let s=0;for(let i=0;i<d.length;i++)s+=d[i]*d[i];window.__nisb=JSON.stringify({db:20*Math.log10(Math.sqrt(s/d.length))})}catch(e){window.__nisb=JSON.stringify({err:String(e)})}})();0")
    al.page.wait_for_function("()=>window.__nisb", timeout=120000); r = json.loads(al.page.evaluate("()=>window.__nisb")); return r.get('db', r.get('err'))
ref = lvl('alone', "const a=await renderMix(44100,64,96,0,false,id,false)")
for nm, code in (('set by another render right after this one started', "const p=renderMix(44100,64,96,0,false,id,false);SIDE_B0=64.5;const a=await p"),
                 ('set by another render while the worklets load', "const _w=wlLoad;wlLoad=function(oc){return _w(oc).then(r=>{SIDE_B0=7.37;return r})};let a;try{a=await renderMix(44100,64,96,0,false,id,false)}finally{wlLoad=_w}"),
                 ('a real second render started in the same task', "const [a]=await Promise.all([renderMix(44100,64,96,0,false,id,false),renderMix(44100,7.37,9,0,false,null,true)])")):
    v = lvl(nm, code); ok('SIDE_B0 %s: the Bass is the same as alone' % nm, isinstance(v, float) and abs(v - ref) < 1e-9, '%s vs %.5f dB' % (v, ref))
x, sr = al.render(b0=0, b1=96, only='Bass'); h1 = hashlib.md5(x.tobytes()).hexdigest()
x, sr = al.render(b0=0, b1=96, only='Bass'); h2 = hashlib.md5(x.tobytes()).hexdigest()
ok('a long render in pieces side by side is the same twice', h1 == h2)
ok('no console errors', not al.errors, al.errors)
al.stop()
print('%d of %d checks pass' % (sum(res), len(res))); sys.exit(0 if all(res) else 1)
