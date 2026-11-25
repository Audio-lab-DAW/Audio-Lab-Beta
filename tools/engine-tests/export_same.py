"""Exports must not change: renders the Fractals demo (Kick and Bass alone, beats 64 to 96) and one clip on each voice engine,
and prints level and a checksum of the samples. Run it on two versions and compare the output.
  python3 tools/engine-tests/export_same.py [index.html]"""
import sys, os, json, hashlib
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'remake'))
from alab import AudioLab
al = AudioLab(sys.argv[1] if len(sys.argv) > 1 else 'index.html'); al.start()
rms = lambda x: float(np.sqrt(np.mean(x.astype(np.float64) ** 2))); db = lambda v: 20 * np.log10(max(v, 1e-12))
al.tracks = json.loads(al.run("JSON.stringify(Object.fromEntries(S.tracks.map(t=>[t.name,t.id])))"))
for nm in ('Kick', 'Bass'):
    x, sr = al.render(b0=64, b1=96, only=nm); print('Fractals %s %.5f dB  %s' % (nm, db(rms(x)), hashlib.md5(x.tobytes()).hexdigest()[:12]))
notes = [{'p': p, 's': i * 2, 'l': 1.7, 'v': .8} for i in range(4) for p in (48, 55, 60)]
for name, pre, ov in (('Saw', 'saw', {}), ('Pad', 'pad', {}), ('Plant', 'plant', {}), ('Acid', 'acid', {}), ('Wavetable', 'wtab', {}), ('Sampler grains', 'sampler', {'mode': 'grain'}), ('Sampler', 'sampler', {}), ('Venom', 'venom', {}), ('Drum kit', 'drums', {})):
    t = {'name': name, 'preset': pre, 'clips': [{'start': 0, 'len': 8, 'notes': notes}]}
    if ov: t['inst'] = ov
    al.build({'bpm': 120, 'tracks': [t]})
    x, sr = al.render(b0=0, b1=8, tail=1); print('%-15s %.5f dB  %s' % (name, db(rms(x)), hashlib.md5(x.tobytes()).hexdigest()[:12]))
print('errors', al.errors); al.stop()
