"""Preset library part 3: what must not change. Run on the old and the new index.html and compare the output.
Prints the Fractals demo (loaded at start) solo Kick and Bass levels for beats 64 to 96 with checksums, the settings of every effect on
every track of the two demo songs built by code ("Psytrance demo", "Shrine Legion") and of the Fractals demo, and the settings a new
effect of every type starts with.
python3 tools/engine-tests/fx_demo_same.py index.html > out.txt"""
import sys, os, json, hashlib
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'remake'))
from alab import AudioLab
al = AudioLab(sys.argv[1] if len(sys.argv) > 1 else 'index.html'); al.start()
print('errors after load', al.errors)
rms = lambda x: float(np.sqrt(np.mean(x.astype(np.float64) ** 2))); db = lambda v: 20 * np.log10(max(v, 1e-12))
al.tracks = json.loads(al.run("JSON.stringify(Object.fromEntries(S.tracks.map(t=>[t.name,t.id])))"))
for nm in ('Kick', 'Bass'):
    x, sr = al.render(b0=64, b1=96, only=nm); print('Fractals %s %.5f dB %s' % (nm, db(rms(x)), hashlib.md5(x.tobytes()).hexdigest()[:12]))
FX = "JSON.stringify(S.tracks.map(t=>[t.name,(t.fx||[]).map(f=>[f.type,f.on,Object.fromEntries(Object.entries(f.p).filter(([k])=>k!=='pre').sort())])]))"
print('Fractals fx', hashlib.md5(al.run(FX).encode()).hexdigest()[:12])
for fn in ('demo', 'demoImperial'):
    al.run("%s();changed(false);1" % fn); al.page.wait_for_timeout(400)
    s = al.run(FX); print(fn, 'fx', hashlib.md5(s.encode()).hexdigest()[:12])
new = json.loads(al.run("JSON.stringify(Object.fromEntries(Object.keys(FXDEF).map(t=>{const p=mkFx(t).p;delete p.pre;return[t,p]})))"))
for t in sorted(new): print('new', t, hashlib.md5(json.dumps(new[t], sort_keys=True).encode()).hexdigest()[:12])
print('errors', al.errors); al.stop()
