"""Every preset of every instrument, measured (preset library: part 1 the synths, part 2 drums, percussion, samplers, particle instruments,
FX, Grid, Sub, Psy Bass and Bounce; part 3 adds the effects).

python3 tools/engine-tests/presets_all.py index.html part2      (all instruments of part 2)
Part 2 adds: one-hit phrases for drums, a 16-pad phrase for kits, a 145 BPM roll for Psy Bass, and for the Kick designer the measured
pitch at the start and the end, the length (to 20 and 40 dB under the peak), the level when the first bass note of a rolling bass comes
(103.4 ms at 145 BPM) and of an offbeat bass (206.9 ms); and Bouncy Notes in front of Soft keys.

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
PART2 = ['kick', 'zsnare', 'zclap', 'zhat', 'ztom', 'perc', 'drums', 'sampler', 'emit', 'vgrain', 'sfx', 'grid', 'sbass', 'psyb', 'bball']
INSTS = (PART2 if len(args) > 1 and args[1] == 'part2' else args[1].split(',') if len(args) > 1 else
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
    'kick': ([(36, 0, .5, 1.0)], 8), 'hit': ([(60, 0, .25, .9), (60, 2, .25, .9)], 12), 'multi': ([(60+i, i*2, 1, .85) for i in range(12)], 40),
    'kit': ([(36+i, i*.5, .25, .9) for i in range(16)], 16), 'mallet': ([(p, i*.5, .4, .85) for i, p in enumerate([60, 64, 67, 72, 67, 64])], 20),
    'roll': ([(33, b+st*.25, .25, .85) for b in range(8) for st in (1, 2, 3)], 12), 'bounce': ([(72, 0, .5, .9)], 40),
}
for _r in ('house', 'techno', 'trance', 'edm', 'hard', 'dnb', 'trap', 'plain', 'offbeat', 'long'): PHR[_r] = PHR['kick']
RBPM = {'roll': 145}
PROBE = ([(48, 0, 2, .85), (72, 3, .25, .85)], 4)

al = AudioLab(IDX); al.start()
print('version', al.version, 'errors after load', al.errors); ERRS = []
def notes_js(ns): return json.dumps([{'p': p, 's': s, 'l': l, 'v': v} for p, s, l, v in ns])

def kick_an(a, sr):
    from scipy.signal import butter, sosfiltfilt
    m = a.mean(axis=0); n = int(.002*sr); k = len(m)//n
    env = np.sqrt((m[:k*n].reshape(k, n)**2).mean(axis=1)); pk = env.max(); dbe = 20*np.log10(np.maximum(env/max(pk, 1e-12), 1e-9))
    def tdb(th):
        i = np.where(dbe > th)[0]; return int((i[-1]+1)*2) if len(i) else 0
    def at(ms): i = int(ms/2); return float(dbe[i]) if i < len(dbe) else -120.0
    lp = sosfiltfilt(butter(4, 1500, fs=sr, output='sos'), m)
    zc = np.where((lp[:-1] <= 0) & (lp[1:] > 0))[0]
    lp2 = sosfiltfilt(butter(4, 300, fs=sr, output='sos'), m); zc2 = np.where((lp2[:-1] <= 0) & (lp2[1:] > 0))[0]  # the end pitch on a 300 Hz low-pass: a fully driven kick is a square wave
    def fat(t0, t1):
        z = zc2[(zc2 >= t0*sr) & (zc2 < t1*sr)]
        if len(z) < 2: return 0.0
        return float(sr/np.median(np.diff(z)))
    t20 = tdb(-20)/1000
    def fpt(t):
        z = zc; i = np.searchsorted(z, t*sr)
        if i < 1 or i >= len(z): return 0.0
        return float(sr/(z[i]-z[i-1]))
    return dict(f5=fpt(.005), f10=fpt(.010), fend=fat(max(.03, .4*t20), max(.075, t20)), t20=tdb(-20), t40=tdb(-40), at103=at(103.4), at207=at(206.9))

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

def feats_full(x, sr, ns=12, nf=2048):
    # each slice: the power spectrum averaged over the whole slice (a single window can land in a gap of a rhythm)
    m = x.mean(axis=0); L = len(m)//ns; bands = np.geomspace(40, 16000, 25); f = np.fft.rfftfreq(nf, 1/sr); out = []; w = np.hanning(nf)
    for t in range(ns):
        seg = m[t*L:(t+1)*L]; P = np.zeros(len(f)); c = 0
        for i in range(0, max(1, len(seg)-nf+1), nf//2):
            fr = seg[i:i+nf]
            if len(fr) < nf: fr = np.pad(fr, (0, nf-len(fr)))
            P += np.abs(np.fft.rfft(fr*w))**2; c += 1
        P /= max(c, 1); out.append([P[(f >= bands[i]) & (f < bands[i+1])].sum()+1e-12 for i in range(24)])
    a = 10*np.log10(np.array(out)); return np.maximum(a, a.max()-60)
ONESHOT = ('kick', 'zsnare', 'zclap', 'zhat', 'ztom')
PHRASEFEAT = ('sbass', 'psyb', 'bball', 'sfx', 'drums')
def feats(x, sr, nf=2048):
    m = x.mean(axis=0); hop = len(m)//12
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
ANCHOR = {'plant': ('lush', 'supersaw'), 'acid': ('psy',), 'growl': ('yoi',), 'vfm': ('glass',), 'orb': ('sun',),
          'kick': ('psyzap',), 'zsnare': ('t909',), 'zclap': ('c909',), 'zhat': ('c909',), 'ztom': ('t808',), 'perc': ('marimba',), 'drums': ('def',),
          'sampler': ('choir',), 'emit': ('spin',), 'vgrain': ('orbit',), 'sfx': ('riser',), 'grid': ('basic',), 'sbass': ('pure',), 'psyb': ('fo145',), 'bball': ('marimba',)}
ROLEANCH = {'plant': ('pluck',)}  # the demo's short rolling bass (psybass) does not set the level of the other basses
KEEP = {'plant': ('lush', 'supersaw', 'psybass', 'pluck'), 'acid': ('psy',), 'growl': ('yoi',), 'vfm': ('glass',), 'orb': ('sun',),
        'perc': ('tom', 'marimba'), 'sampler': ('choir', 'cloud'), 'emit': ('spin',), 'vgrain': ('orbit',), 'sfx': ('riser',)}
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
    TB = "KPRE" if inst == 'kick' else "IPRE['%s'][0]" % inst; PF = "kickParams" if inst == 'kick' else "IPRE['%s'][1]" % inst
    if inst == 'sampler': al.run("S.tracks[0].inst.buf='@choir';changed(false)")
    keys = al.run("Object.keys(%s)" % TB); M = meta.get(inst, {}); rows = []; F = {}; KICK = {}; H = {}
    names = al.run("Object.fromEntries(Object.entries(%s).map(([k,p])=>[k,String(p.n||k).replace(/^[^·]*· /,'')]))" % TB)
    oldlv = al.run("JSON.stringify(typeof PSLV!=='undefined'&&PSLV['%s']||{})" % inst); oldlv = json.loads(oldlv)
    for ki, k in enumerate(keys):
        if ki and ki % 12 == 0: fresh(inst)  # a new page now and then: long runs crashed the page
        mk = M.get(k, {}); role = mk.get('r') or ROLEOF.get(mk.get('g', ''), 'lead')
        if inst in ('zsnare', 'zclap', 'zhat', 'ztom'): role = 'hit'
        elif inst == 'drums': role = 'kit'
        elif inst == 'perc': role = 'mallet'
        elif inst == 'sfx': role = 'multi' if k == 'multi' else 'fx'
        elif inst == 'bball': role = 'bounce' if mk.get('r') != 'pad' else 'pad'
        elif inst == 'grid': role = mk.get('r') or {'Leads': 'lead', 'Basses': 'bass', 'Plucks': 'pluck', 'Keys & bells': 'keys', 'Pads': 'pad', 'Drums': 'hit', 'FX & generative': 'fx'}.get(mk.get('g'), 'lead')
        elif inst == 'psyb': role = 'roll'
        elif inst == 'sbass' and role == 'roll': pass
        if inst == 'kick': role = mk.get('r') or 'plain'
        if role in ('roll',) and inst != 'kick' and al.run('S.bpm') != 145: al.run('S.bpm=145;changed(false)')
        if (role not in ('roll',) or inst == 'kick') and al.run('S.bpm') != BPM: al.run('S.bpm=%d;changed(false)' % BPM)
        if inst == 'acid' and role == 'bass': role = 'acid'
        if inst == 'sampler' and k.startswith('y'): al.run("S.tracks[0].inst.buf='@glass';changed(false)")  # 'Your sample' presets keep the loaded sample: tested on the glass tone
        al.run("(()=>{const I=S.tracks[0].inst;Object.assign(I,JSON.parse(JSON.stringify(%s('%s'))),%s);changed(false);return 1})()" % (PF, k, "{kp:'%s'}" % k if inst == 'kick' else "{ipk:'%s'}" % k))
        ns, nb = PHR['kick' if inst == 'kick' else role]; tr = int(mk.get('tr', 0)); ns = [(p+tr, s0, l, v) for p, s0, l, v in ns]
        if inst == 'kick' and al.run("!!KPRE['%s'].kt" % k) and k != 'trap' and k != 't808d': ns = [(36 + 7, s0, l, v) for p, s0, l, v in ns]  # play G with key track
        bpm_now = al.run('S.bpm'); beat_s = 60 / bpm_now
        al.run("S.tracks[0].clips[0].notes=%s;changed(false)" % notes_js(ns))
        a, sr = al.render(b0=0, b1=nb); b, _ = al.render(b0=0, b1=nb)
        nan = bool(np.isnan(a).any()); pk = float(np.abs(a).max()) if not nan else 9
        L = lufs(a, sr) if not nan else -120; MM = momax(a, sr) if not nan else -120
        e = env5(a, sr); emax = e.max() if len(e) else 0
        end = max(s+l for _, s, l, _ in ns)*beat_s
        if inst == 'kick': KICK[k] = kick_an(a, sr)
        last = a[:, -sr:]; tail_db = 20*np.log10(max(np.sqrt((last**2).mean()), 1e-12)/max(emax, 1e-12))
        # attack of the first note: 10 % to 90 % of the loudest 5 ms inside the first note (or the first 4 s for a pad)
        w = int(((ns[0][2]*beat_s) if role != 'pad' else 4)/.005); e1 = e[:max(2, w)]; m1 = e1.max()
        i10 = int(np.argmax(e1 >= .1*m1)); i50 = int(np.argmax(e1 >= .5*m1)); att = (i50-i10)*5
        act = a[:, :int(end*sr)+int(.2*sr)].mean(axis=0); X = np.abs(np.fft.rfft(act))**2; f = np.fft.rfftfreq(len(act), 1/sr)
        cen = float((X*f).sum()/max(X.sum(), 1e-12)); low = float(X[f < 200].sum()/max(X.sum(), 1e-12))
        bit = bool(np.array_equal(a, b)); dmax = float(np.abs(a-b).max()); same = dmax <= 1e-6  # Plant's voices differ in the last bit from run to run (1e-8, also before v0.191)
        al.run("S.tracks[0].clips[0].notes=%s;changed(false)" % notes_js(PROBE[0]))
        p, _ = al.render(b0=0, b1=PROBE[1]); F[k] = feats(p, sr)
        if inst in ONESHOT: F[k] = feats(a[:, :int(.6*sr)], sr, nf=1024)  # one-shots: the first hit, 12 slices of 50 ms
        if inst == 'sbass':  # overtones 2 to 8 of the held C4 of the probe (dB under the note) and the side level above 150 Hz
            f0 = 440*2**((48-69)/12); seg = p[:, int(.15*sr):int(.85*sr)]; mm = seg.mean(axis=0); X = np.abs(np.fft.rfft(mm*np.hanning(len(mm)))); fq = np.fft.rfftfreq(len(mm), 1/sr)
            hl = [20*np.log10(max(X[np.argmin(np.abs(fq-h*f0))], 1e-9)) for h in range(1, 9)]; sd = (seg[0]-seg[1])/2
            H[k] = [max(-60, v-hl[0]) for v in hl[1:]] + [max(-60, 20*np.log10(max(np.sqrt((sd**2).mean()), 1e-9)/max(np.sqrt((mm**2).mean()), 1e-9)))]
        if inst in PHRASEFEAT: F[k] = feats_full(a[:, :int(6*sr)], sr, ns=24) if inst == 'bball' else feats_full(a, sr)  # these are compared on their own phrase (a roll, a held FX, a bounce), not on the probe
        r = dict(k=k, n=names.get(k, k), mom=round(MM, 2), g=mk.get('g', ''), role=role, psy=bool(mk.get('p')), lufs=round(L, 2), peak=round(pk, 3), att=att, cen=round(cen), low=round(low, 3), tail=round(float(tail_db), 1), same=same, bit=bit, dmax=dmax, nan=nan)
        bad = []
        if nan: bad.append('NaN')
        if emax < 1e-4: bad.append('silent')
        if pk >= 1.0: bad.append('clips')
        if tail_db > -50: bad.append('does not end (%.0f dB)' % tail_db)
        if not same: bad.append('not the same twice (%.2g)' % dmax)
        if role in ('bass', 'sub', 'acid') and low < .1 and role != 'acid': bad.append('little bass energy (%.2f)' % low)
        if role in ('lead', 'pluck', 'bass', 'sub', 'acid', 'keys') and att > 60: bad.append('slow attack %d ms' % att)
        if inst == 'kick':
            q = KICK[k]; g = mk.get('g', '')
            if role == 'roll' and q['at103'] > -20: bad.append('psy kick still %.1f dB at 103 ms' % q['at103'])
            if role == 'offbeat' and q['at207'] > -20: bad.append('kick still %.1f dB at 207 ms' % q['at207'])
            if role not in ('fx',) and not (30 <= q['fend'] <= 70): bad.append('end pitch %.1f Hz' % q['fend'])
            if role in ('roll', 'offbeat') and not (40 <= q['fend'] <= 58): bad.append('psy kick end pitch %.1f Hz outside 40 to 58' % q['fend'])
            if role in ('roll', 'offbeat') and q['f5'] < 1.5*q['fend']: bad.append('no pitch fall')
        if role == 'pad' and att < 60 and mk.get('slow', 1): bad.append('fast attack for a pad (%d ms)' % att)
        r['bad'] = bad; rows.append(r)
        if bad: fails.append('%s/%s: %s' % (inst, k, ', '.join(bad)))
    # loudness table
    OFF = {'bass': 0, 'sub': 0, 'acid': 0, 'lead': 0, 'pluck': -1, 'keys': -1.5, 'pad': -3, 'fx': -2, 'hit': 0, 'kit': 0, 'mallet': -1, 'roll': 0, 'bounce': -1}
    for _r in PHR: OFF.setdefault(_r, 0)
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
    if inst == 'kick':
        print('\nkick: pitch at 5 ms and at 10 ms, end pitch (40 ms to the -20 dB point), set pitch, length to -20 and -40 dB, level at 103.4 ms (first rolling bass note at 145 BPM) and at 206.9 ms (offbeat bass), peak')
        print('%-10s %-22s %-8s %6s %6s %6s %6s %6s %6s %7s %7s %6s' % ('key', 'group', 'role', 'f5', 'f10', 'end', 'set', 't-20', 't-40', '@103', '@207', 'peak'))
        setp = al.run("Object.fromEntries(Object.entries(KPRE).map(([k,p])=>[k,440*Math.pow(2,((p.kt?(k==='trap'||k==='t808d'?p.tune:p.tune+7):p.tune)-69)/12)]))")
        for r in rows:
            q = KICK[r['k']]
            print('%-10s %-22s %-8s %6.0f %6.0f %6.1f %6.1f %6d %6d %7.1f %7.1f %6.3f' % (r['k'], r['g'][:22], r['role'], q['f5'], q['f10'], q['fend'], setp[r['k']], q['t20'], q['t40'], q['at103'], q['at207'], r['peak']))
    # nearest pairs
    ks = [k for k in F if not M.get(k, {}).get('h')]; pairs = []  # a preset hidden from the menu (kept for old projects) is not compared
    for i in range(len(ks)):
        for j in range(i+1, len(ks)):
            pairs.append((float(np.abs(F[ks[i]]-F[ks[j]]).mean()), ks[i], ks[j]))
    pairs.sort()
    nb = sum(1 for r in rows if r['bit']); print('bit-identical twice: %d of %d (the rest differ by at most %.2g)' % (nb, len(rows), max([r['dmax'] for r in rows] + [0])))
    print('closest pairs (mean difference in dB over 24 bands x 12 slices):', ', '.join('%s~%s %.1f' % (a, b, d) for d, a, b in pairs[:6]))
    if inst == 'sbass':  # subs differ in overtones 20 to 40 dB under the note and in width: the same only if those match too (within 3 dB)
        def sameh(x, y): return max(np.abs(np.array(H[x])-np.array(H[y]))) < 3
        pairs = [(d, a2, b2) for d, a2, b2 in pairs if sameh(a2, b2)] + [(9, '', '')]
        print('sub pairs whose overtones 2 to 8 and side level are also within 3 dB:', ', '.join('%s~%s %.1f' % (b, c, d) for d, b, c in pairs[:8] if b))
    if inst == 'kick':  # kicks: the same only if the spectra match AND the end pitch is the same note (within half a semitone) AND the length within 15 %
        import math
        def samek(x, y): A, B = KICK[x], KICK[y]; return abs(12*math.log2(max(A['fend'], 1)/max(B['fend'], 1))) < .5 and abs(A['t40']-B['t40']) < .15*max(A['t40'], B['t40'])
        pairs = [(d, a2, b2) for d, a2, b2 in pairs if samek(a2, b2)] + [(9, '', '')]
        print('kick pairs on the same note (end pitch within half a semitone) and length (within 15 %), by spectral distance:', ', '.join('%s~%s %.1f' % (b, c, d) for d, b, c in pairs[:8] if b))
    for d, a2, b2 in pairs:
        if d < 1.5: fails.append('%s: %s and %s nearly the same (%.2f dB)' % (inst, a2, b2, d))
    RESULTS[inst] = dict(rows=rows, pairs=pairs[:10])
print('\npage errors:', ERRS + al.errors)
print('PROBLEMS (%d):' % len(fails)); [print('  ' + f) for f in fails]
if JOUT: json.dump(dict(results=RESULTS, levels=LV), open(JOUT, 'w'), indent=1)
al.stop()
