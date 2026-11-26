"""Preset library, part 2: every Bouncy Notes preset in front of Soft keys.
python3 tools/engine-tests/bnotes_presets.py [index.html]
For each preset: the notes it makes from one held C4 (at 120 BPM), rendered twice. Checks: no NaN, not silent, no clipping, the sound
ends, two renders identical, the note lists of two presets are not the same; prints the number of notes, the first gaps and the keys."""
import sys, os, json, numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'remake'))
from alab import AudioLab
al = AudioLab(sys.argv[1] if len(sys.argv) > 1 else 'index.html'); al.start()
print('version', al.version, 'errors after load', al.errors)
al.build({'bpm': 120, 'tracks': [{'name': 'T', 'preset': 'keys', 'clips': [{'start': 0, 'len': 32, 'notes': [{'p': 60, 's': 0, 'l': 2, 'v': .9}]}]}]})
al.run("(()=>{const t=S.tracks[0];t.fx.unshift(mkFx('bnotes'));changed(true);return 1})()")
keys = al.run("Object.keys(FXPRE.bnotes)"); bad = []; seen = {}
for k in keys:
    nl = al.run("(()=>{const t=S.tracks[0],f=t.fx[0];Object.assign(f.p,JSON.parse(JSON.stringify(FXPRE.bnotes['%s'][1])),{pre:'%s'});changed(false);return JSON.stringify(mfxNotes(t,t.clips[0].notes).map(n=>[n.p,+n.s.toFixed(3),+n.l.toFixed(3),+n.v.toFixed(2)]))})()" % (k, k))
    nl = json.loads(nl)
    a, sr = al.render(b0=0, b1=40); b, _ = al.render(b0=0, b1=40)
    nan = bool(np.isnan(a).any()); pk = float(np.abs(a).max()); last = a[:, -sr:]
    tail = 20*np.log10(max(np.sqrt((last**2).mean()), 1e-12)/max(pk, 1e-12))
    gaps = [round(nl[i+1][1]-nl[i][1], 3) for i in range(min(5, len(nl)-1))]
    pr = []
    if nan: pr.append('NaN')
    if pk < 1e-3: pr.append('silent')
    if pk >= 1: pr.append('clips')
    if tail > -50: pr.append('does not end (%.0f dB)' % tail)
    if not np.array_equal(a, b): pr.append('not the same twice')
    sig = json.dumps(nl)
    if sig in seen: pr.append('same notes as ' + seen[sig])
    seen[sig] = k
    print('%-9s %-44s notes %3d  gaps(beats) %-34s keys %-28s peak %.3f %s' % (k, al.run("FXPRE.bnotes['%s'][0]" % k)[:44], len(nl), gaps, sorted(set(n[0] for n in nl))[:8], pk, '; '.join(pr)))
    if pr: bad.append(k + ': ' + ', '.join(pr))
print('page errors', al.errors)
print('PROBLEMS', bad if bad else 'none')
al.stop()
