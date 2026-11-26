"""Every preset of every instrument, measured (preset library, part 1: the synths; parts 2 and 3 add their instruments to INSTS).

python3 tools/engine-tests/presets_all.py [index.html] [inst,inst,...] [--json out.json]

For every preset: a short phrase that fits its role (bass, lead, pad ...) is rendered twice through the app's own engine.
Checks: no NaN, not silent, no clipping (peak under 1.0), the sound ends after the notes end (the last second is at least
50 dB under the loudest part), the two renders are identical. Measures: loudness (BS.1770 K-weighted, gated, in LUFS of the
rendered phrase), peak, attack time (first note, from 10 % to 50 % of its loudest 5 ms: movement later in the note does not count), spectral centre, share of energy under
200 Hz. Level: the loudest 100 ms of the phrase (K-weighted; short enough that short notes count by their body), the number the level trims are set from.
Then a probe (C3 held 1 s, then a short C5) is rendered for every preset and the presets of one instrument are compared
(spectrum in 24 bands over 12 time slices, mean difference in dB): the closest pairs are listed.
Role, group, tooltip and the psytrance mark come from PSMETA (the preset library block in index.html)."""
import sys, os, json, numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'remake'))
from alab import AudioLab

_av = sys.argv[1:]
if '--json' in _av: _i = _av.index('--json'); _av = _av[:_i] + _av[_i+2:]
args = [a for a in _av if not a.startswith('--')]
IDX = args[0] if args else 'index.html'
INSTS = (args[1].split(',') if len(args) > 1 else
         ['saw', 'square', 'pad', 'strings', 'pluck', 'keys', 'sub', 'bass', 'reese', 'plant', 'wtab', 'acid', 'venom', 'growl', 'vfm', 'orb'])
JOUT = sys.argv[sys.argv.index('--json') + 1] if '--json' in sys.argv else None
BPM = 120
BEAT = 60 / BPM

# phrases: (pitch, start beat, length in beats, velocity)
def ph_bass(o=0): return [(36+o, 0, .5, .85), (36+o, 1, .5, .85), (43+o, 2, .5, .85), (41+o, 3, .5, .85), (39+o, 4, 2, .85)]
PHR = {
    'bass': (ph_bass(), 14), 'sub': (ph_bass(-12), 14), 'acid': ([(36+[0, 0, 12, 0, 3, 0, 7, 12][i % 8], i*.5, .3, .95 if i % 4 == 0 else .7) for i in range(12)], 14),
    'lead': ([(60, 0, .5, .85), (63, .5, .5, .85), (67, 1, .5, .85), (70, 1.5, .5, .85), (72, 2, .5, .85), (67, 2.5, 2, .85)], 14),
    'pluck': ([(p, i*.25, .2, .85) for i, p in enumerate([60, 67, 72, 75]*3)], 14),
    'pad': ([(p, 0, 4, .8) for p in (57, 60, 64)], 24),
    'keys': ([(p, 0, 1, .8) for p in (60, 64, 67)] + [(p, 1.5, 1, .8) for p in (60, 64, 67)] + [(p, 3, 1, .8) for p in (57, 60, 64)], 18),
    'fx': ([(60, 0, 2, .85)], 24),
}
PROBE = ([(48, 0, 2, .85), (72, 3, .25, .85)], 4)

al = AudioLab(IDX); al.start()
print('version', al.version, 'errors after load', al.errors); ERRS = []
def notes_js(ns): return json.dumps([{'p': p, 's': s, 'l': l, 'v': v} for p, s, l, v in ns])

def kfilter(x, sr):
    from scipy.signal import lfilter
    import math
    f0, G, Q = 1681.974450955533, 3.999843853973347, 0.7071752369554196
    K = math.tan(math.pi*f0/sr); Vh = 10**(G/20); Vb = Vh**0.4996667741545416; a0 = 1+K/Q+K*K
    b = [(Vh+Vb*K/Q+K*K)/a0, 2*(K*K-Vh)/a0, (Vh-Vb*K/Q+K*K)/a0]; a = [1, 2*(K*K-1)/a0, (1-K/Q+K*K)/a0]
    y = lfilter(b, a, x, axis=-1)
    f0, Q = 38.13547087602444, 0.5003270373238773; K = math.tan(math.pi*f0/sr)
    a = [1, 2*(K*K-1)/(1+K/Q+K*K), (1-K/Q+K*K)/(1+K/Q+K*K)]
    return lfilter([1, -2, 1], a, y, axis=-1)

def lufs(x, sr):
    y = kfilter(x, sr); ms = (y**2).sum(axis=0)
    n, h = int(.4*sr), int(.1*sr)
    bl = np.array([ms[i:i+n].mean() for i in range(0, max(1, len(ms)-n), h)])
    if not len(bl): return -120.0
    lk = -0.691+10*np.log10(np.maximum(bl, 1e-12)); g = bl[lk > -70]
    if not len(g): return -120.0
    rel = -0.691+10*np.log10(g.mean())-10; g2 = bl[lk > rel]
    return float(-0.691+10*np.log10(max(g2.mean(), 1e-12)))

def momax(x, sr):
    y = kfilter(x, sr); ms = (y**2).sum(axis=0); n, h = int(.1*sr), int(.025*sr)
    return float(-0.691+10*np.log10(max(max(ms[i:i+n].mean() for i in range(0, max(1, len(ms)-n), h)), 1e-12)))

def env5(x, sr):
    m = (x**2).sum(axis=0); n = int(.005*sr); k = len(m)//n
    return np.sqrt(m[:k*n].reshape(k, n).mean(axis=1))

def feats(x, sr):
    m = x.mean(axis=0); nf = 2048; hop = len(m)//12
    bands = np.geomspace(40, 16000, 25); f = np.fft.rfftfreq(nf, 1/sr); out = []
    for t in range(12):
        seg = m[t*hop:t*hop+nf]
        if len(seg) < nf: seg = np.pad(seg, (0, nf-len(seg)))
        X = np.abs(np.fft.rfft(seg*np.hanning(nf)))**2
        out.append([X[(f >= bands[i]) & (f < bands[i+1])].sum()+1e-12 for i in range(24)])
    a = 10*np.log10(np.array(out)); return np.maximum(a, a.max()-60)

meta = al.run("JSON.stringify(typeof PSMETA!=='undefined'?PSMETA:{})"); meta = json.loads(meta)
ROLEOF = {'Bass': 'bass', 'Sub': 'sub', 'Lead': 'lead', 'Pluck': 'pluck', 'Arp': 'pluck', 'Pad': 'pad', 'Strings': 'pad', 'Keys': 'keys',
          'Organ': 'keys', 'Chord': 'keys', 'Stab': 'keys', 'FX': 'fx', 'Acid': 'acid', 'Init': 'lead', 'Start here': 'lead', 'Bells': 'keys'}
RESULTS = {}; fails = []; LV = {}
ANCHOR = {'plant': ('lush', 'supersaw'), 'acid': ('psy',), 'growl': ('yoi',), 'vfm': ('glass',), 'orb': ('sun',)}
ROLEANCH = {'plant': ('pluck',)}  # the demo's short rolling bass (psybass) does not set the level of the other basses
KEEP = {'plant': ('lush', 'supersaw', 'psybass', 'pluck'), 'acid': ('psy',), 'growl': ('yoi',), 'vfm': ('glass',), 'orb': ('sun',)}
for _i in INSTS: KEEP.setdefault(_i, ('def', 'init'))
def fresh(inst):
    global al, ERRS
    ERRS += al.errors; al.stop(); al = AudioLab(IDX); al.start()
    for _try in range(3):
        try:
            al.build({'bpm': BPM, 'tracks': [{'name': 'T', 'preset': inst, 'clips': [{'start': 0, 'len': 32, 'notes': []}]}]}); return
        except Exception as e:
            print('build failed, again:', str(e)[:120]); al.page.wait_for_timeout(1500); al.errors.clear()

for inst in INSTS:
    fresh(inst)
    keys = al.run("Object.keys(IPRE['%s'][0])" % inst); M = meta.get(inst, {}); rows = []; F = {}
    names = al.run("Object.fromEntries(Object.entries(IPRE['%s'][0]).map(([k,p])=>[k,String(p.n||k).replace(/^[^·]*· /,'')]))" % inst)
    oldlv = al.run("JSON.stringify(typeof PSLV!=='undefined'&&PSLV['%s']||{})" % inst); oldlv = json.loads(oldlv)
    for ki, k in enumerate(keys):
        if ki and ki % 12 == 0: fresh(inst)  # a new page now and then: long runs crashed the page
        mk = M.get(k, {}); role = mk.get('r') or ROLEOF.get(mk.get('g', ''), 'lead')
        if inst == 'acid' and role == 'bass': role = 'acid'
        al.run("(()=>{const I=S.tracks[0].inst;Object.assign(I,JSON.parse(JSON.stringify(IPRE['%s'][1]('%s'))),{ipk:'%s'});changed(false);return 1})()" % (inst, k, k))
        ns, nb = PHR[role]; tr = int(mk.get('tr', 0)); ns = [(p+tr, s0, l, v) for p, s0, l, v in ns]
        al.run("S.tracks[0].clips[0].notes=%s;changed(false)" % notes_js(ns))
        a, sr = al.render(b0=0, b1=nb); b, _ = al.render(b0=0, b1=nb)
        nan = bool(np.isnan(a).any()); pk = float(np.abs(a).max()) if not nan else 9
        L = lufs(a, sr) if not nan else -120; MM = momax(a, sr) if not nan else -120
        e = env5(a, sr); emax = e.max() if len(e) else 0
        end = max(s+l for _, s, l, _ in ns)*BEAT
        last = a[:, -sr:]; tail_db = 20*np.log10(max(np.sqrt((last**2).mean()), 1e-12)/max(emax, 1e-12))
        # attack of the first note: 10 % to 90 % of the loudest 5 ms inside the first note (or the first 4 s for a pad)
        w = int(((ns[0][2]*BEAT) if role != 'pad' else 4)/.005); e1 = e[:max(2, w)]; m1 = e1.max()
        i10 = int(np.argmax(e1 >= .1*m1)); i50 = int(np.argmax(e1 >= .5*m1)); att = (i50-i10)*5
        act = a[:, :int(end*sr)+int(.2*sr)].mean(axis=0); X = np.abs(np.fft.rfft(act))**2; f = np.fft.rfftfreq(len(act), 1/sr)
        cen = float((X*f).sum()/max(X.sum(), 1e-12)); low = float(X[f < 200].sum()/max(X.sum(), 1e-12))
        bit = bool(np.array_equal(a, b)); dmax = float(np.abs(a-b).max()); same = dmax <= 1e-6  # Plant's voices differ in the last bit from run to run (1e-8, also before v0.191)
        al.run("S.tracks[0].clips[0].notes=%s;changed(false)" % notes_js(PROBE[0]))
        p, _ = al.render(b0=0, b1=PROBE[1]); F[k] = feats(p, sr)
        r = dict(k=k, n=names.get(k, k), mom=round(MM, 2), g=mk.get('g', ''), role=role, psy=bool(mk.get('p')), lufs=round(L, 2), peak=round(pk, 3), att=att, cen=round(cen), low=round(low, 3), tail=round(float(tail_db), 1), same=same, bit=bit, dmax=dmax, nan=nan)
        bad = []
        if nan: bad.append('NaN')
        if emax < 1e-4: bad.append('silent')
        if pk >= 1.0: bad.append('clips')
        if tail_db > -50: bad.append('does not end (%.0f dB)' % tail_db)
        if not same: bad.append('not the same twice (%.2g)' % dmax)
        if role in ('bass', 'sub', 'acid') and low < .1 and role != 'acid': bad.append('little bass energy (%.2f)' % low)
        if role in ('lead', 'pluck', 'bass', 'sub', 'acid', 'keys') and att > 60: bad.append('slow attack %d ms' % att)
        if role == 'pad' and att < 60 and mk.get('slow', 1): bad.append('fast attack for a pad (%d ms)' % att)
        r['bad'] = bad; rows.append(r)
        if bad: fails.append('%s/%s: %s' % (inst, k, ', '.join(bad)))
    # loudness table
    OFF = {'bass': 0, 'sub': 0, 'acid': 0, 'lead': 0, 'pluck': -1, 'keys': -1.5, 'pad': -3, 'fx': -2}
    rel = [r['mom']-OFF[r['role']] for r in rows]; spread = max(rel)-min(rel)
    anc = [v for r, v in zip(rows, rel) if r['k'] in ANCHOR.get(inst, ('def', 'init'))]
    tgt = float(np.mean(anc)) if anc else float(np.median(rel))  # the instrument's default (or the demo presets) sets the level
    print('\n=== %s: %d presets; level (loudest 100 ms, against its role) target %.1f (from the default preset), spread %.1f dB ===' % (inst, len(rows), tgt, spread))
    print('%-10s %-9s %-6s %-26s %6s %6s %6s %5s %6s %5s %5s %5s %s' % ('key', 'group', 'role', 'name', 'level', 'LUFS', 'peak', 'att', 'centre', 'low', 'tail', 'trim', 'problems'))
    newlv = {}
    for r, v in zip(rows, rel):
        rt = [x['mom'] for x in rows if x['k'] in ANCHOR.get(inst, ('def', 'init')) + ROLEANCH.get(inst, ()) and x['role'] == r['role']]  # a kept preset of the same role (a demo preset) sets that role's level
        t = round(float(np.clip(oldlv.get(r['k'], 0)+(float(np.mean(rt))-r['mom'] if rt else tgt-v), -14, 12)), 1); r['trim'] = t
        if r['k'] not in KEEP.get(inst, ()) and abs(t) >= .3: newlv[r['k']] = t
        print('%-10s %-9s %-6s %-26s %6.1f %6.1f %6.3f %5d %6d %5.2f %5.0f %5.1f %s' % (r['k'], r['g'][:9], r['role'], (r['n']+(' *' if r['psy'] else ''))[:26], r['mom'], r['lufs'], r['peak'], r['att'], r['cen'], r['low'], r['tail'], t, '; '.join(r['bad'])))
    LV[inst] = newlv
    # nearest pairs
    ks = list(F); pairs = []
    for i in range(len(ks)):
        for j in range(i+1, len(ks)):
            pairs.append((float(np.abs(F[ks[i]]-F[ks[j]]).mean()), ks[i], ks[j]))
    pairs.sort()
    nb = sum(1 for r in rows if r['bit']); print('bit-identical twice: %d of %d (the rest differ by at most %.2g)' % (nb, len(rows), max([r['dmax'] for r in rows] + [0])))
    print('closest pairs (mean difference in dB over 24 bands x 12 slices):', ', '.join('%s~%s %.1f' % (a, b, d) for d, a, b in pairs[:6]))
    for d, a2, b2 in pairs:
        if d < 1.5: fails.append('%s: %s and %s nearly the same (%.2f dB)' % (inst, a2, b2, d))
    RESULTS[inst] = dict(rows=rows, pairs=pairs[:10])
print('\npage errors:', ERRS + al.errors)
print('PROBLEMS (%d):' % len(fails)); [print('  ' + f) for f in fails]
if JOUT: json.dump(dict(results=RESULTS, levels=LV), open(JOUT, 'w'), indent=1)
al.stop()
