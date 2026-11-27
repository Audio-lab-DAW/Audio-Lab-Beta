"""Task SND-1 (lane L): before and after numbers for Filter v2 and the Auto Filter's Clean mode, through the app's own render (48 kHz).
  python3 tools/engine-lab/snd/snd1_measure.py index.html out.json [classic]
- classic: the Auto Filter in Classic (every saved one) with 12 of its presets, and the old Low-pass filter: level and checksum.
  Run on the build before and after: the lines must be the same (old projects unchanged).
- the rest (only where Filter v2 exists): every model's response to a quiet impulse against its analog curve (sndFltResp), the
  aliasing of a 4.5 kHz sine at -3 dBFS with full drive (2x against Off, and the Auto Filter Classic's drive for comparison),
  and the cost: offline render time of 8 s of stereo noise, minus an empty render."""
import sys, os, json, time, hashlib
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'remake'))
from alab import AudioLab
IDX = sys.argv[1]; OUT = sys.argv[2]; ONLY_CLASSIC = len(sys.argv) > 3 and sys.argv[3] == 'classic'
SR = 48000; BPM = 120
db = lambda v: 20 * np.log10(max(float(v), 1e-12))
al = AudioLab(IDX); al.start(); R = {'version': al.version, 'errors0': al.errors}
print('version', al.version)
def fxrun(sig, fx, beats=8, tail=0):
    bid = al.add_audio(np.vstack([sig, sig]).astype(np.float32) if sig.ndim == 1 else sig.astype(np.float32), SR)
    rec = {'bpm': BPM, 'tracks': [{'name': 'A', 'kind': 'audio', 'fx': fx, 'clips': [{'start': 0, 'len': beats, 'buf': bid, 'dur': sig.shape[-1] / SR, 'gain': 0, 'fi': 0, 'fo': 0}]}]}
    al.build(rec); t = time.time(); x, _ = al.render(b0=0, b1=beats, sr=SR, tail=tail); return x.astype(np.float64), time.time() - t
def alias_db(y, f0, lo=40):
    w = np.blackman(len(y)); X = np.abs(np.fft.rfft(y * w)) ** 2; f = np.fft.rfftfreq(len(y), 1 / SR)
    A = X[(f > lo) & (f < .45 * f0)].sum(); T = X[f > lo].sum(); return 10 * np.log10(max(A, 1e-30) / max(T, 1e-30))
rng = np.random.default_rng(5); n = 4 * SR; tt = np.arange(n) / SR
mat = .25 * rng.standard_normal(n) + .3 * (2 * ((110 * tt) % 1) - 1); mat[:480] *= np.linspace(0, 1, 480)
# 1 Classic: must not move
pres = json.loads(al.run("JSON.stringify(Object.fromEntries(Object.entries(FXPRE.afilt).map(([k,v])=>[k,v[1]])))"))
keys = ['lpslow', 'hpriser', 'dj', 'bpwah', 'autowah', 'funk', 'wobble', 'acid', 'vowel', 'talk', 'flangec', 'negc', 'notch', 'peak', 'lofi']
C = {}
for k in keys:
    if k not in pres: continue
    p = dict(pres[k]); p.pop('pre', None); p['q'] = 'classic'
    x, _ = fxrun(mat, [{'type': 'afilt', 'p': p}], 8); C['afilt ' + k] = '%.5f dB  %s' % (db(np.sqrt(np.mean(x ** 2))), hashlib.md5(x.astype(np.float32).tobytes()).hexdigest()[:12])
for fq, q in ((2500, 1), (400, 8)):
    x, _ = fxrun(mat, [{'type': 'filter', 'p': {'freq': fq, 'q': q}}], 8); C['filter %d q%g' % (fq, q)] = '%.5f dB  %s' % (db(np.sqrt(np.mean(x ** 2))), hashlib.md5(x.astype(np.float32).tobytes()).hexdigest()[:12])
R['classic'] = C
for k, v in C.items(): print('%-22s %s' % (k, v))
has2 = al.run("typeof FXDEF.filter2==='object'")
if has2 and not ONLY_CLASSIC:
    MODELS = ['ladder', 'diode', 'ms20', 'svf12', 'svf24', 'comb', 'formant']
    # 2 response against the analog curve (impulse at -26 dBFS so the drive-free filters are linear)
    imp = np.zeros(SR); imp[int(.1 * SR)] = .05
    resp = {}
    x0, _ = fxrun(imp, [], 2); H0 = np.abs(np.fft.rfft(x0[0][int(.1 * SR) - 64:int(.1 * SR) - 64 + (1 << 15)], 1 << 15))  # the track's own gain
    for m in MODELS + ['svf12 bp', 'svf12 hp', 'svf24 hp', 'ms20 bp']:
        mm, md = (m.split(' ') + ['lp'])[:2]
        p = {'model': mm, 'mode': md, 'freq': 220 if mm == 'comb' else 1000, 'res': 50, 'drive': 0, 'mix': 100, 'out': 0, 'os': '2x', 'vowel': 1.5}
        x, _ = fxrun(imp, [{'type': 'filter2', 'p': p}], 2)
        h = x[0][int(.1 * SR) - 64:int(.1 * SR) - 64 + (1 << 15)]; H = np.abs(np.fft.rfft(h, 1 << 15)) / H0; f = np.fft.rfftfreq(1 << 15, 1 / SR)
        sel = (f >= 30) & (f <= 8000); fr = f[sel]; ana = np.array(json.loads(al.run("JSON.stringify(Array.from(sndFltResp(sndF2Map(%s),new Float64Array(%s),new Float64Array(%d))))" % (json.dumps(p), json.dumps(fr.tolist()), len(fr)))))
        d = 20 * np.log10(np.maximum(H[sel], 1e-9)) - 20 * np.log10(np.maximum(ana, 1e-9)); keep = 20 * np.log10(np.maximum(ana, 1e-9)) > -40
        resp[m] = {'max_dev_dB_30Hz_8kHz': float(np.abs(d[keep]).max()), 'at_cutoff_dB': float(20 * np.log10(H[np.argmin(abs(f - p['freq']))] + 1e-12)), 'analog_at_cutoff_dB': float(20 * np.log10(ana[np.argmin(abs(fr - p['freq']))] + 1e-12))}
        print('resp', m, {k: round(v, 3) for k, v in resp[m].items()})
    R['response'] = resp
    # 3 aliasing: 4.5 kHz sine at -3 dBFS, full drive, cutoff 18 kHz (the filter passes the tone; the drive makes the harmonics)
    n2 = 2 * SR; sine = .7 * np.sin(2 * np.pi * 4500 * np.arange(n2) / SR); sine[:240] *= np.linspace(0, 1, 240)
    AL = {}
    def al_of(fx):
        x, _ = fxrun(sine, fx, 4); y = x[0][int(.3 * SR):int(1.3 * SR)]; return {'alias_4k5_dB': round(alias_db(y, 4500), 2), 'peak_dB': round(db(np.abs(y).max()), 2)}
    AL['afilt Classic lp24 drive 100'] = al_of([{'type': 'afilt', 'p': {'type': 'lp24', 'freq': 18000, 'res': .707, 'drive': 100, 'mix': 100, 'lamt': 0, 'env': 0, 'q': 'classic'}}])
    AL['afilt Clean lp24 drive 100'] = al_of([{'type': 'afilt', 'p': {'type': 'lp24', 'freq': 18000, 'res': .707, 'drive': 100, 'mix': 100, 'lamt': 0, 'env': 0, 'q': 'clean'}}])
    for m in ('ladder', 'diode', 'ms20', 'svf12'):
        for os_ in ('2x', '1x'):
            AL['filter2 %s drive 100 %s' % (m, os_)] = al_of([{'type': 'filter2', 'p': {'model': m, 'mode': 'lp', 'freq': 18000, 'res': 0, 'drive': 100, 'mix': 100, 'os': os_}}])
    for lv in (-3, -20):
        sg = 10 ** (lv / 20) * np.sin(2 * np.pi * 220 * np.arange(n2) / SR)
        for dv in (0, 50, 100):
            x, _ = fxrun(sg, [{'type': 'filter2', 'p': {'model': 'ladder', 'freq': 18000, 'res': 0, 'drive': dv}}], 4)
            AL['ladder 220 Hz at %d dBFS, drive %d: rms dB' % (lv, dv)] = round(db(np.sqrt(np.mean(x[0][int(.3 * SR):int(1.3 * SR)] ** 2))), 2)
    for k, v in AL.items(): print('%-34s %s' % (k, v))
    R['alias'] = AL
    # 4 cost: 8 s of stereo noise, offline render time minus an empty one (rough; the same machine for every line)
    nz = np.vstack([.3 * rng.standard_normal(8 * SR), .3 * rng.standard_normal(8 * SR)])
    def cost(fx, rep=3):
        ts = []
        for _ in range(rep): _, t = fxrun(nz, fx, 16); ts.append(t)
        return min(ts)
    t0 = cost([]); CO = {'empty_s': round(t0, 3)}
    CO['afilt Classic lp24'] = cost([{'type': 'afilt', 'p': {'q': 'classic'}}]) - t0
    CO['afilt Clean lp24'] = cost([{'type': 'afilt', 'p': {'q': 'clean'}}]) - t0
    CO['afilt Clean lp24, LFO on'] = cost([{'type': 'afilt', 'p': {'q': 'clean', 'lamt': 50}}]) - t0
    for m in MODELS:
        CO['filter2 %s 2x' % m] = cost([{'type': 'filter2', 'p': {'model': m, 'drive': 0}}]) - t0
    CO['filter2 ladder 2x drive 50'] = cost([{'type': 'filter2', 'p': {'model': 'ladder', 'drive': 50}}]) - t0
    CO['filter2 ladder 1x'] = cost([{'type': 'filter2', 'p': {'model': 'ladder', 'os': '1x'}}]) - t0
    CO['filter (old Low-pass)'] = cost([{'type': 'filter'}]) - t0
    for k in list(CO):
        if k != 'empty_s': CO[k] = {'s_per_s': round(max(CO[k], 0) / 8, 4), 'pct_core': round(max(CO[k], 0) / 8 * 100, 2)}
    for k, v in CO.items(): print('%-30s %s' % (k, v))
    R['cost'] = CO
R['errors'] = al.errors; print('errors', al.errors)
json.dump(R, open(OUT, 'w'), indent=1, default=float); al.stop()
