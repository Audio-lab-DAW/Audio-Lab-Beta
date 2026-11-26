"""Level trims for the effect presets (preset library part 3), from the JSON that fx_presets.py writes.
python3 tools/engine-tests/fx_trims.py result.json [old FXLV as JSON]  -> prints FXLV as JS
Rules: effects with an Output (ott, crush, mband, trans, deess, vocoder, fshift, conv, imager, clip colour and drum presets): the change in
loudness against the dry material should be 0 LU; a preset more than 1 LU away gets a trim (to 0.5 dB, inside the knob's range).
Compressor: Web Audio's compressor adds its own make-up gain (more with a lower threshold and higher ratio), and Make-up cannot go below 0,
so the presets are matched to each other: Make-up = max(0, 4 LU - the change without make-up).
Left alone: the first preset of each effect (what a new effect sounds like) unless it is more than 6 LU off, keys the demos use, the Limiter (its gain is the point) and
the Soft Clipper's mastering presets (louder on purpose)."""
import sys, json
R = json.load(open(sys.argv[1])); OLD = json.loads(open(sys.argv[2]).read()) if len(sys.argv) > 2 else {}
OUTK = {'comp': 'makeup', 'ott': 'out', 'clip': 'out', 'crush': 'out', 'mband': 'out', 'trans': 'out', 'deess': 'out', 'vocoder': 'out', 'fshift': 'out', 'conv': 'out', 'imager': 'out'}
KEEP = {'ott': {'air', 'gentle'}, 'conv': {'vplate'}, 'comp': {'init'}, 'clip': {'safe', 'master3', 'sine', 'edm', 'psymaster'}}   # demos, louder on purpose
FIRST = {'ott': 'classic', 'conv': 'small', 'clip': 'gentle', 'crush': '8bit', 'mband': 'glue', 'trans': 'punch', 'deess': 'voc', 'vocoder': 'robot', 'fshift': 'barber', 'imager': 'nat'}
MAK = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}   # comp: the make-up each preset had when measured
out = {}
for t, ok in OUTK.items():
    if t not in R: continue
    for k, r in R[t].items():
        if k.startswith('_') or k in KEEP.get(t, ()): continue
        old = OLD.get(t, {}).get(k, 0.0)
        if FIRST.get(t) == k and abs(r['dlu']) <= 6 and not old: continue   # a new effect keeps its sound unless its level is clearly wrong
        if t == 'comp':
            mk = MAK.get(k, 0.0); d0 = r['dlu'] - mk
            want = max(0.0, 4.0 - d0); tr = round((want - mk) * 2) / 2 + old
        else:
            if abs(r['dlu']) <= 1.0: tr = old
            else: tr = old - round(r['dlu'] * 2) / 2
        if abs(tr) >= .25: out.setdefault(t, {})[k] = tr
print('FXLV=' + json.dumps(out, separators=(',', ':')) + ';')
