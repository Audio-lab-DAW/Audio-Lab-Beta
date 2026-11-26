"""Every preset of every effect and MIDI effect, measured (preset library, part 3).

python3 tools/engine-tests/fx_presets.py index.html materials.npz [type,type,...] [--json out.json] [--once]

Material: tools/engine-tests/fx_materials.py makes it (drums, kick, bass, pad, lead, vocal, mix, click, noise, glide; 8 beats at 145 BPM,
peak -6 dBFS). Each preset is played on the material that fits its group (FXMETA[type][key].r, or a word in the group name, or the
effect's own default), on an audio track, and rendered twice through the app's engine with a tail.
Checks: no NaN, no clipping (peak under 1.0), the sound ends (last second 50 dB under the loudest 400 ms; presets marked "inf" in
FXMETA are allowed to hold), the two renders are identical.
Measures: change in loudness against the dry material over the 8 beats (LU, BS.1770 gated), change of peak, the movement of the gain
(the 95th minus the 5th percentile of wet minus dry per 10 ms, in dB: how hard a dynamics preset works, or how deep a pump is), the
response in 8 octave bands on pink noise (EQ, filters, colour), and on the click material: the first echo time (delays, against the
tempo), the decay time (reverbs: time from the click's peak until the tail is 60 dB down, from a fit between -5 and -35 dB).
The closest pairs of each effect are listed: spectrum over time of left and right (24 bands by 12 slices, mean difference in dB, level taken
out), of the output, or for space and modulation effects of what they add (output minus dry). The Limiter plays a mix peaking at -1 dBFS.
MIDI effects (chord, bnotes, arp, mutil) play Soft keys with a phrase; analysis effects (spec, loud, tuner, measure) must pass the
sound through unchanged."""
import sys, os, json, time, numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'remake'))
from alab import AudioLab

av = sys.argv[1:]
JOUT = av[av.index('--json')+1] if '--json' in av else None
if '--json' in av: i = av.index('--json'); av = av[:i]+av[i+2:]
ONCE = '--once' in av
av = [a for a in av if not a.startswith('--')]
IDX = av[0] if av else 'index.html'; MAT = av[1] if len(av) > 1 else 'fx_materials.npz'
ONLY = av[2].split(',') if len(av) > 2 else None
SR = 44100; BPM = 145; NB = 8; BEAT = 60/BPM; N = int(NB*BEAT*SR)
M = dict(np.load(MAT)); M['mixhot'] = (M['mix']*10**(5/20)).astype(np.float32)   # a mix peaking at -1 dBFS for the Limiter
MIDI = ('chord', 'bnotes', 'arp', 'mutil'); ANALYSIS = ('spec', 'loud', 'tuner', 'measure')
SPACE = ('delay', 'tdelay', 'reverb', 'conv', 'blur', 'vdelay', 'bdelay')
DIFFT = SPACE + ('chorus', 'phaser', 'fshift')
DEFMAT = {'comp': 'mix', 'ott': 'mix', 'side': 'pad', 'limit': 'mix', 'clip': 'mix', 'gate': 'drums', 'mband': 'mix', 'trans': 'drums', 'deess': 'vocal',
          'reson': 'mix', 'duck': 'pad', 'delay': 'lead', 'tdelay': 'lead', 'reverb': 'lead', 'blur': 'pad', 'conv': 'lead', 'tstop': 'mix', 'vdelay': 'lead',
          'bdelay': 'lead', 'eq': 'mix', 'filter': 'mix', 'drive': 'bass', 'afilt': 'pad', 'crush': 'drums', 'pshift': 'vocal', 'pcorr': 'glide', 'voice': 'vocal',
          'phaser': 'pad', 'chorus': 'pad', 'shaper': 'pad', 'vocoder': 'vocal', 'fshift': 'pad', 'crk': 'pad', 'imager': 'mix', 'spec': 'mix', 'loud': 'mix',
          'tuner': 'lead', 'measure': 'mix'}
WORDS = [('kick', 'kick'), ('drum', 'drums'), ('snare', 'drums'), ('hat', 'drums'), ('perc', 'drums'), ('bass', 'bass'), ('sub', 'bass'),
         ('vocal', 'vocal'), ('voice', 'vocal'), ('rap', 'vocal'), ('pad', 'pad'), ('atmos', 'pad'), ('ambient', 'pad'), ('lead', 'lead'),
         ('synth', 'lead'), ('pluck', 'lead'), ('instrument', 'lead'), ('master', 'mix'), ('bus', 'mix'), ('mix', 'mix'), ('club', 'mix')]

al = AudioLab(IDX); al.start(); print('version', al.version, 'errors after load', al.errors)
TYPES = json.loads(al.run("JSON.stringify(Object.keys(FXPRE).filter(t=>FXDEF[t]).concat(['eq']).concat(FXDEF.chord?['chord']:[]))"))
TYPES = [t for t in dict.fromkeys(TYPES) if not ONLY or t in ONLY]
META = json.loads(al.run("JSON.stringify(typeof FXMETA!=='undefined'?FXMETA:{})"))
BUFS = {}
def buf(name):
    if name not in BUFS: BUFS[name] = al.add_audio(M[name], SR)
    return BUFS[name]

def kfilter(x, sr=SR):
    from scipy.signal import lfilter
    import math
    f0, G, Q = 1681.974450955533, 3.999843853973347, 0.7071752369554196
    K = math.tan(math.pi*f0/sr); Vh = 10**(G/20); Vb = Vh**0.4996667741545416; a0 = 1+K/Q+K*K
    b = [(Vh+Vb*K/Q+K*K)/a0, 2*(K*K-Vh)/a0, (Vh-Vb*K/Q+K*K)/a0]; a = [1, 2*(K*K-1)/a0, (1-K/Q+K*K)/a0]
    y = lfilter(b, a, x, axis=-1)
    f0, Q = 38.13547087602444, 0.5003270373238773; K = math.tan(math.pi*f0/sr)
    a = [1, 2*(K*K-1)/(1+K/Q+K*K), (1-K/Q+K*K)/(1+K/Q+K*K)]
    return lfilter([1, -2, 1], a, y, axis=-1)
def lufs(x):
    y = kfilter(x); ms = (y**2).sum(axis=0); n, h = int(.4*SR), int(.1*SR)
    bl = np.array([ms[i:i+n].mean() for i in range(0, max(1, len(ms)-n), h)])
    lk = -0.691+10*np.log10(np.maximum(bl, 1e-12)); g = bl[lk > -70]
    if not len(g): return -120.0
    rel = -0.691+10*np.log10(g.mean())-10; g2 = bl[lk > rel]
    return float(-0.691+10*np.log10(max(g2.mean(), 1e-12)))
def env(x, ms=10):
    m = (x.astype(np.float64)**2).sum(axis=0); n = int(ms/1000*SR); k = len(m)//n
    return 10*np.log10(np.maximum(m[:k*n].reshape(k, n).mean(axis=1), 1e-14))
def align(w, d):
    """the wet sound moved back by the effect's own delay (a lookahead or a fixed latency), found by cross-correlation, at most 50 ms"""
    a, b = w.mean(axis=0)[:N], d.mean(axis=0)[:N]; L = int(.05*SR); n = 1 << int(np.ceil(np.log2(len(a)+L)))
    c = np.fft.irfft(np.fft.rfft(a, n)*np.conj(np.fft.rfft(b, n)), n)[:L]; s = int(np.argmax(np.abs(c)))
    return w[:, s:], s
def gmove(w, d):
    w, _ = align(w, d); n = min(w.shape[1], N)
    ew, ed = env(w[:, :n]), env(d[:, :n]); ok = ed > ed.max()-35
    if ok.sum() < 5: return 0.0
    g = ew[ok]-ed[ok]; return float(np.percentile(g, 95)-np.percentile(g, 5))
def ends(x):
    e = env(x, 400/4); top = np.convolve(10**(e/10), np.ones(4)/4, 'valid').max()
    last = 10**(env(x[:, -SR:], 1000)/10).mean(); return float(10*np.log10(max(last, 1e-14)/top))
OCT = [62.5, 125, 250, 500, 1000, 2000, 4000, 8000, 16000]
def bands(w, d):
    from scipy.signal import welch
    f, pw = welch(w.mean(axis=0)[:N], SR, nperseg=8192); f, pd = welch(d.mean(axis=0)[:N], SR, nperseg=8192)
    out = []
    for i in range(8):
        s = (f >= OCT[i]) & (f < OCT[i+1]); out.append(round(float(10*np.log10(pw[s].sum()/max(pd[s].sum(), 1e-20))), 1))
    return out
def echo(w):
    """first repeat after the click: the time of the strongest peak of the envelope after 15 ms (ms)."""
    e = env(w, 1); e0 = int(np.argmax(e[:20])); t = e[e0+15:e0+2500]
    if not len(t) or t.max() < e.max()-60: return 0.0
    return float(np.argmax(t)+15)
def decay(w):
    """reverb decay: from the envelope (10 ms) after its peak, fit between -5 and -35 dB, extrapolated to 60 dB (seconds)."""
    e = env(w, 10); p = 2+int(np.argmax(e[2:])); t = e[p:]-e[p]   # the first 20 ms hold what is left of the dry click
    i5 = np.argmax(t < -5) if (t < -5).any() else 0; i35 = np.argmax(t < -35) if (t < -35).any() else len(t)-1
    if i35 <= i5+2: return float(i35*.01*60/35)
    k = np.polyfit(np.arange(i5, i35)*.01, t[i5:i35], 1)[0]
    return float(-60/k) if k < 0 else 99.0
def feats(x, ns=12, nf=2048):
    """spectrum over time of left and right (24 bands x 12 slices each), level taken out: two presets that differ only in level count as the same"""
    a = np.vstack([feats1(x[0], ns, nf), feats1(x[1], ns, nf)]); return a-a.mean()
def feats1(m, ns, nf):
    L = len(m)//ns; bd = np.geomspace(40, 16000, 25); f = np.fft.rfftfreq(nf, 1/SR); out = []; wn = np.hanning(nf)
    for t in range(ns):
        seg = m[t*L:(t+1)*L]; P = np.zeros(len(f)); c = 0
        for i in range(0, max(1, len(seg)-nf+1), nf//2):
            fr = seg[i:i+nf]
            if len(fr) < nf: fr = np.pad(fr, (0, nf-len(fr)))
            P += np.abs(np.fft.rfft(fr*wn))**2; c += 1
        out.append([P[(f >= bd[i]) & (f < bd[i+1])].sum()/max(c, 1)+1e-14 for i in range(24)])
    a = 10*np.log10(np.array(out)); return np.maximum(a, a.max()-60)

def matof(t, k, name):
    m = META.get(t, {}).get(k, {})
    if t in ('side', 'duck', 'shaper', 'crk'): return 'pad'   # volume shapes show on a held sound (on a rolling bass a psy duck is over before the first bass note)
    if m.get('r'): return m['r']
    if t == 'limit': return 'mixhot' if not m.get('r') else m['r']
    g = (m.get('g') or (name.split('|')[0] if '|' in name else '')).lower()
    for w, mt in WORDS:
        if w in g: return mt
    return DEFMAT.get(t, 'mix')

def build(t, mat):
    tr = []
    if t in MIDI:
        notes = [{'p': p, 's': s, 'l': l, 'v': .85} for p, s, l in ((57, 0, 1), (60, 0, 1), (64, 0, 1), (62, 2, 1), (65, 2, 1), (69, 2, 1), (64, 4, .5), (67, 5, .5), (72, 6, 1.5))]
        tr.append({'name': 'T', 'preset': 'keys', 'clips': [{'start': 0, 'len': NB, 'notes': notes}], 'fx': [{'type': t, 'p': {}}]})
    else:
        if t == 'duck': tr.append({'name': 'K', 'kind': 'audio', 'clips': [{'start': 0, 'len': NB, 'buf': buf('kick'), 'dur': N/SR, 'gain': 0, 'fi': 0, 'fo': 0}]})
        tr.append({'name': 'T', 'kind': 'audio', 'fx': [{'type': t, 'p': {}}], 'clips': [{'start': 0, 'len': NB, 'buf': buf(mat), 'dur': N/SR, 'gain': 0, 'fi': 0, 'fo': 0}]})
    al.build({'bpm': BPM, 'tracks': tr})
    if t == 'duck': al.run("(()=>{const T=S.tracks.find(t=>t.name==='T'),K=S.tracks.find(t=>t.name==='K');T.fx[0].p.src=K.id;changed(true)})()")
def setp(t, k):
    al.run("(()=>{const T=S.tracks.find(t=>t.name==='T'),f=T.fx[0],src=f.p.src;const fr=mkFx('%s').p;for(const q in f.p)delete f.p[q];Object.assign(f.p,fr);"
           "if('%s'==='eq'){if(EQPRE['%s'])eqApplyPreset(f,'%s')}else if('%s'==='chord'){f.p.notes=CHPRE['%s'][1].slice();f.p.cp='%s'}"
           "else Object.assign(f.p,JSON.parse(JSON.stringify(FXPRE['%s']['%s'][1])),{pre:'%s'});if(src)f.p.src=src;changed(true);return 1})()" % ((t,)+(t, k, k, t, k, k, t, k, k)))
def fxon(on): al.run("(()=>{S.tracks.find(t=>t.name==='T').fx[0].on=%s;changed(true)})()" % ('true' if on else 'false'))
def ren(t, tail):
    if t == 'duck':
        a, _ = al.render(b0=0, b1=NB, tail=tail, tracks=['K', 'T']); return a.astype(np.float64)-KICKR[:, :a.shape[1]]
    a, _ = al.render(b0=0, b1=NB, tail=tail); return a.astype(np.float64)

R = {}; FAIL = []; T0 = time.time()
for t in TYPES:
    # a fresh browser for every effect: hundreds of renders in one page run it out of memory
    try: al.stop()
    except Exception: pass
    al = AudioLab(IDX); al.start(); BUFS.clear()
    if al.errors: print('page errors on load', al.errors)
    if t == 'eq': P = json.loads(al.run("JSON.stringify(Object.fromEntries(Object.entries(EQPRE).map(([k,v])=>[k,[v[0]]])))"))
    elif t == 'chord': P = json.loads(al.run("JSON.stringify(Object.fromEntries(Object.entries(CHPRE).map(([k,v])=>[k,[v[0]]])))"))
    else: P = json.loads(al.run("JSON.stringify(Object.fromEntries(Object.entries(FXPRE['%s']).map(([k,v])=>[k,[v[0]]])))" % t))
    tail = 16 if t in SPACE else 6
    R[t] = {}; DRY = {}; feat = {}; t1 = time.time(); cur = [None]
    for k, v in P.items():
        if META.get(t, {}).get(k, {}).get('h'): continue
        mat = 'keys' if t in MIDI else matof(t, k, v[0])
        if mat not in DRY:
            build(t, mat)
            if t == 'duck':
                KICKR = al.render(b0=0, b1=NB, tail=tail, only='K')[0].astype(np.float64)
            fxon(False); DRY[mat] = ren(t, tail); fxon(True)
            if t in SPACE: build(t, 'click'); fxon(False); DRY['click'] = ren(t, tail); fxon(True)
            if t in ('eq', 'filter', 'afilt', 'drive', 'crush', 'clip', 'imager'): build(t, 'noise'); fxon(False); DRY['noise'] = ren(t, tail); fxon(True)
            build(t, mat); cur[0] = mat
        if cur[0] != mat: build(t, mat); cur[0] = mat
        setp(t, k); a = ren(t, tail); b = a if ONCE else ren(t, tail)
        d = DRY[mat]; n = min(a.shape[1], d.shape[1])
        r = dict(name=v[0], mat=mat, nan=bool(np.isnan(a).any()), peak=round(float(np.abs(a).max()), 3), same=bool(np.array_equal(a, b)),
                 diff=float(np.abs(a-b).max()) if not np.array_equal(a, b) else 0.0, ends=round(ends(a), 1),
                 dlu=round(lufs(a[:, :N])-lufs(d[:, :N]), 2), dpk=round(20*np.log10(np.abs(a[:, :N]).max()/max(np.abs(d[:, :N]).max(), 1e-9)), 2),
                 move=round(gmove(a, d), 1), lag_ms=round(align(a, d)[1]/SR*1000, 2))
        r['dplr'] = round(r['dpk']-r['dlu'], 2)
        if t not in MIDI and t not in ANALYSIS and n > 0:
            r['side'] = round(float(10*np.log10(((a[0]-a[1])**2).sum()/max(((a[0]+a[1])**2).sum(), 1e-20)+1e-12)), 1)
        if t in ANALYSIS: r['passes'] = bool(np.allclose(a[:, :n], d[:, :n], atol=1e-6))
        # space and modulation effects: what the effect adds (output minus dry); the rest: the output
        feat[k] = feats((a[:, :N+int(2*SR)]-d[:, :N+int(2*SR)]) if t in DIFFT and a.shape[1] >= N+2*SR and d.shape[1] >= N+2*SR else a[:, :N+int(2*SR)])
        if t in SPACE:
            build(t, 'click'); setp(t, k); c = ren(t, tail); w = c-DRY['click'][:, :c.shape[1]]
            r['echo_ms'] = round(echo(c), 1); r['echo_beats'] = round(r['echo_ms']/1000/BEAT, 3); r['rt60'] = round(decay(w), 2); r['ends_click'] = round(ends(c), 1)
            build(t, mat)
        if t in ('eq', 'filter', 'afilt', 'drive', 'crush', 'clip', 'imager'):
            build(t, 'noise'); setp(t, k); c = ren(t, tail); r['oct'] = bands(c, DRY['noise']); build(t, mat)
        inf = META.get(t, {}).get(k, {}).get('inf')
        bad = []
        if r['nan']: bad.append('NaN')
        if r['peak'] >= 1.0: bad.append('clips %.3f' % r['peak'])
        if r['ends'] > -50 and not inf: bad.append('does not end (%.1f dB)' % r['ends'])
        if not r['same']: bad.append('renders differ %.2g' % r['diff'])
        if t in ANALYSIS and not r['passes']: bad.append('changes the sound')
        if np.abs(a[:, :N]).max() < 1e-5 and t not in ('gate',): bad.append('silent')
        if bad: FAIL.append((t, k, bad))
        r['bad'] = bad; R[t][k] = r
    # closest pairs
    ks = list(feat); pairs = []
    for i in range(len(ks)):
        for j in range(i+1, len(ks)):
            pairs.append((float(np.abs(feat[ks[i]]-feat[ks[j]]).mean()), ks[i], ks[j]))
    pairs.sort(); R[t]['_pairs'] = pairs[:6]
    print('\n== %s: %d presets, %.0f s' % (t, len(feat), time.time()-t1))
    for k, r in R[t].items():
        if k.startswith('_'): continue
        x = ''
        if 'echo_ms' in r: x += ' echo %6.1f ms (%.3f beats) rt60 %5.2f s' % (r['echo_ms'], r['echo_beats'], r['rt60'])
        if 'oct' in r: x += ' oct ' + ' '.join('%+.0f' % v for v in r['oct'])
        if 'side' in r: x += ' side %5.1f' % r['side']
        print('  %-28s %-6s dLU %+6.2f dPk %+6.2f dPLR %+6.2f move %5.1f ends %6.1f%s %s %s' % (k[:28], r['mat'], r['dlu'], r['dpk'], r['dplr'], r['move'], r['ends'], x, r['name'], ('  BAD: '+'; '.join(r['bad'])) if r['bad'] else ''))
    print('  closest:', '; '.join('%s / %s %.2f' % (a, b, d) for d, a, b in pairs[:6]))
print('\nfailures (%d):' % len(FAIL))
for f in FAIL: print(' ', f)
print('errors', al.errors, 'total %.0f s' % (time.time()-T0))
if JOUT: json.dump(R, open(JOUT, 'w'), indent=0)
al.stop()
