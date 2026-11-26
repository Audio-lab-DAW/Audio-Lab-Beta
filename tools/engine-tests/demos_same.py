"""The built-in demo songs must sound the same after preset changes: renders the start of the "Psytrance demo" and of
"Shrine Legion" (both built by code from preset keys) and prints level and a checksum per track.
  python3 tools/engine-tests/demos_same.py [index.html]   (run on two versions and compare)"""
import sys, os, json, hashlib
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'remake'))
from alab import AudioLab
al = AudioLab(sys.argv[1] if len(sys.argv) > 1 else 'index.html'); al.start()
rms = lambda x: float(np.sqrt(np.mean(x.astype(np.float64) ** 2))); db = lambda v: 20 * np.log10(max(v, 1e-12))
for fn in ('demo', 'demoImperial'):
    al.run("%s();changed(false);1" % fn); al.page.wait_for_timeout(500)
    al.tracks = json.loads(al.run("JSON.stringify(Object.fromEntries(S.tracks.map(t=>[t.name,t.id])))"))
    st = json.loads(al.run("JSON.stringify(Object.fromEntries(S.tracks.map(t=>[t.name,Math.min(...t.clips.map(c=>c.start),1e9)])))"))
    for nm in al.tracks:
        b0 = st[nm] if st[nm] < 1e8 else 0; b1 = b0 + 32
        x, sr = al.render(b0=b0, b1=b1, only=nm); print('%-13s %-14s beats %4d-%4d %10.5f dB  %s' % (fn, nm, b0, b1, db(rms(x)), hashlib.md5(x.tobytes()).hexdigest()[:12]))
print('errors', al.errors); al.stop()
