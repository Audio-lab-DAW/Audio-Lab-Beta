"""Unit tests of the shared DSP kit (task SND-0) against the published analog responses.
Every TPT filter is the bilinear transform of its analog prototype, prewarped at the cutoff, so the digital response must
equal H_a(j tan(w/2) / g) to rounding (Zavalishin, The Art of VA Filter Design, ch. 3 to 5). The halfbands are checked
against their design (tools/engine-lab/snd/halfband_design.py), the ADAA shapers against the plain shapers and by aliasing.
  python3 tools/engine-lab/snd/kit_test.py [index.html | tools/engine-lab/snd/kit_src.js] [results.json]
Exit code 1 when a check fails."""
import sys, os, json, base64, subprocess, math
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import halfband_design as HD
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, '..', '..', '..', 'index.html')
OUTJ = sys.argv[2] if len(sys.argv) > 2 else None
N = [0, 0]; FAIL = []; NUM = {}
def ok(c, m, info=''):
    N[0] += 1
    if c: N[1] += 1; print('ok   ', m, info)
    else: FAIL.append(m); print('FAIL ', m, info)
SR = 48000
jobs = []
def job(**k): jobs.append(k); return k['id']
# ---------- jobs ----------
FCS = [50, 440, 3000, 12000, 20000]
for fc in FCS:
    for q in (0.5, 0.7071, 6):
        for m in range(7): job(id=f'svf{fc}_{q}_{m}', name='svf', p=[fc, q, m], sig='imp', n=1 << 16)
for fc in FCS:
    for r in (0, 0.5, 0.9):
        L = 1 << (18 if fc < 100 else 16)  # a long enough window for the slow decay at 50 Hz
        job(id=f'lad{fc}_{r}', name='ladder', p=[fc, r, 1, 0], sig='imp', n=L)
        job(id=f'dio{fc}_{r}', name='diode', p=[fc, r, 1, 0], sig='imp', n=L)
        job(id=f'sk{fc}_{r}', name='sk', p=[fc, r, 1, 0], sig='imp', n=L)
        for nm in ('ladder', 'diode', 'sk'): job(id=f'nlq_{nm}{fc}_{r}', name=nm, p=[fc, r, 1, 1], sig='imp', a=1e-5, n=L)
for nm in ('ladder', 'diode', 'sk'):
    job(id=f'loud_{nm}', name=nm, p=[800, 1.1, 4, 1], sig='noise', a=1, n=48000)
    job(id=f'osc_{nm}', name=nm, p=[1000, 1.03, 1, 1], sig='imp', a=1e-3, n=96000)
    job(id=f'pk_{nm}', name=nm, p=[2000, 0.995, 1, 0], sig='imp', n=1 << 18)
for fc in (200, 1000, 5000): job(id=f'op{fc}', name='onepole', p=[fc, 0], sig='imp', n=1 << 15)
job(id='combfb', name='comb', p=[100, 0.5, 1e9, 0], sig='imp', n=1000)
job(id='combfr', name='comb', p=[100.5, 0.9, 1e9, 0], sig='imp', n=1 << 16)
job(id='combff', name='comb', p=[37, -0.7, 1e9, 1], sig='imp', n=1 << 12)
job(id='combdamp', name='comb', p=[240, 0.95, 3000, 0], sig='imp', n=1 << 16)
for v in range(5): job(id=f'form{v}', name='formant', p=[v, 1], sig='imp', n=1 << 15)
for nm in ('os2', 'os4'):
    job(id=f'rt_{nm}', name=nm, p=[], sig='imp', n=1 << 14, sr=44100)
    job(id=f'img_{nm}', name=nm, sig='up2', f=15000, n=1 << 14, sr=44100)
    job(id=f'ali_{nm}', name=nm, sig='down2', f=30000, n=1 << 14, sr=44100)
F0 = 4500
for t in range(3):
    for os_ in (1, 2, 4):
        for ad in (0, 1): job(id=f'sh{t}_{os_}_{ad}', name='shaper', p=[t, 4, os_, ad], sig='sine', f=F0, a=0.5, n=1 << 15)
    job(id=f'ramp{t}', name='shaper', p=[t, 1, 1, 1], sig='ramp', a=3, n=48000)
job(id='sm', sig='smooth', ms=10, n=24000)
for nm, p in [('svf', [1000, 0.7, 0]), ('ladder', [1000, 0.5, 1, 0]), ('ladder', [1000, 0.5, 2, 1]), ('diode', [1000, 0.5, 1, 0]), ('diode', [1000, 0.5, 2, 1]),
              ('sk', [1000, 0.5, 2, 1]), ('comb', [300, 0.8, 4000, 0]), ('formant', [1.5, 1]), ('shaper', [0, 4, 1, 1]), ('shaper', [0, 4, 2, 1]), ('shaper', [0, 4, 4, 1]), ('os2', []), ('os4', [])]:
    job(id='cpu_' + nm + '_' + '_'.join(str(v) for v in p), name=nm, p=p, sig='cpu', n=48000)
r = subprocess.run(['node', os.path.join(HERE, 'kit_run.js'), SRC], input=json.dumps(jobs), capture_output=True, text=True)
if r.returncode: print(r.stderr); sys.exit(1)
RES = json.loads(r.stdout)
def get(i): return np.frombuffer(base64.b64decode(RES[i]), dtype=np.float64)
def spec(y): return np.fft.rfft(y)
def wgrid(n): return np.linspace(0, math.pi, n // 2 + 1)
def bltS(w, g): return 1j * np.tan(w / 2) / g
def cmp_db(h, ha, floor=-80):
    m = (np.abs(ha) > 10 ** (floor / 20))
    m[-1] = False  # Nyquist (tan blows up)
    m[0] = m[0] and True
    return np.max(np.abs(20 * np.log10(np.abs(h[m]) + 1e-300) - 20 * np.log10(np.abs(ha[m]) + 1e-300)))
def pw(fc, sr=SR): return math.tan(math.pi * min(max(fc, 1e-3), sr * 0.49) / sr)

# ---------- plain arithmetic ----------
allowed = {'Math.exp', 'Math.log', 'Math.log1p', 'Math.tan', 'Math.tanh', 'Math.sin', 'Math.cos', 'Math.sqrt', 'Math.abs', 'Math.floor'}
used = set(RES['_math'])
ok(used <= allowed, 'the kit uses only plain arithmetic and fdlibm functions (no Math.pow, no Math.random)', sorted(used))
core = open(SRC, encoding='utf-8').read(); core = core[core.index('function sndKitCore(){'):core.index('\nfunction sndWL(){')]
ok('**' not in core and 'Math.random' not in core and '`' not in core and '${' not in core, 'no ** operator, no Math.random, no template strings in the kit')

# ---------- SVF ----------
worst = 0
for fc in FCS:
    for q in (0.5, 0.7071, 6):
        k = 1 / q; g = pw(fc)
        for m in range(7):
            y = get(f'svf{fc}_{q}_{m}'); w = wgrid(len(y)); s = bltS(w, g); d = s * s + k * s + 1
            ha = [1 / d, k * s / d, s * s / d, (s * s + 1) / d, (1 - s * s) / d, (s * s - k * s + 1) / d, s / d][m]
            e = cmp_db(spec(y), ha); worst = max(worst, e)
ok(worst < 1e-6, 'SVF: all 7 outputs at 5 cutoffs and 3 Q match the analog prototype through the prewarped bilinear transform', '%.2e dB' % worst)
NUM['svf_max_err_db'] = worst
# one-pole
worst = 0
for fc in (200, 1000, 5000):
    y = get(f'op{fc}'); w = wgrid(len(y)); s = bltS(w, pw(fc)); worst = max(worst, cmp_db(spec(y), 1 / (1 + s)))
ok(worst < 1e-6, 'one-pole low-pass matches 1/(1+s)', '%.2e dB' % worst)

# ---------- ladders ----------
A0 = np.array([[-2, 1, 0, 0], [1, -2, 1, 0], [0, 1, -2, 1], [0, 0, 1, -1]], float)
DW = math.sqrt(10 / 7); DK = 901 / 49
def diodeH(s, k):
    A = A0.copy(); A[0, 3] -= k; out = np.empty(len(s), complex)
    for i, sv in enumerate(s): out[i] = np.linalg.solve(sv * np.eye(4) - A, np.array([1, 0, 0, 0], complex))[3]
    return out
def model(nm, fc, r, w):
    if nm == 'ladder': s = bltS(w, pw(fc)); return 1 / ((1 + s) ** 4 + 4 * r)
    if nm == 'sk': s = bltS(w, pw(fc)); return 1 / (s * s + (2 - 2 * r) * s + 1)
    s = bltS(w, pw(fc) / DW); return diodeH(s, DK * r)
for nm, tag in (('ladder', 'lad'), ('diode', 'dio'), ('sk', 'sk')):
    worst = 0; worstnl = 0
    for fc in FCS:
        for r in (0, 0.5, 0.9):
            y = get(f'{tag}{fc}_{r}'); w = wgrid(len(y))
            if nm == 'diode': st = len(y) >> 12; w2 = w[::st]; h = spec(y)[::st]
            else: w2 = w; h = spec(y)
            e = cmp_db(h, model(nm, fc, r, w2)); worst = max(worst, e)
            yq = get(f'nlq_{nm}{fc}_{r}') / 1e-5; worstnl = max(worstnl, cmp_db(spec(yq), spec(y), -60))
    ok(worst < 1e-8, f'{nm}: linear response matches its analog model at 5 cutoffs and 3 resonances', '%.2e dB' % worst)
    ok(worstnl < 0.01, f'{nm}: the driven (nonlinear) mode equals the linear filter for quiet signals', '%.4f dB' % worstnl)
    NUM[nm + '_max_err_db'] = worst; NUM[nm + '_nl_quiet_err_db'] = worstnl
    y = get(f'loud_{nm}')
    ok(np.all(np.isfinite(y)) and np.max(np.abs(y)) < 20, f'{nm}: driven mode stays bounded with full-scale noise past self-oscillation (res 1.1, drive 4)', '%.2f' % np.max(np.abs(y)))
    y = get(f'osc_{nm}')[48000:]; Y = np.abs(np.fft.rfft(y * np.hanning(len(y)))); f = np.argmax(Y) * SR / len(y)
    rms = np.sqrt(np.mean(y ** 2))
    ok(rms > 0.01 and abs(f / 1000 - 1) < 0.03, f'{nm}: res 1.03 in driven mode self-oscillates near the cutoff (1000 Hz)', '%.1f Hz, rms %.3f' % (f, rms))
    y = get(f'pk_{nm}'); Y = np.abs(spec(y)); f = np.argmax(Y) * SR / len(y)
    ok(abs(f / 2000 - 1) < 0.005, f'{nm}: the resonance peak sits at the cutoff (2000 Hz, res 0.995)', '%.1f Hz' % f)
    NUM[nm + '_peak_hz_at_2000'] = f

# ---------- comb ----------
y = get('combfb')
ok(y[0] == 1 and abs(y[100] - 0.5) < 1e-15 and abs(y[200] - 0.25) < 1e-15 and np.max(np.abs(np.delete(y[:301], [0, 100, 200, 300]))) < 1e-15, 'comb: integer delay 100, feedback 0.5 gives 1, 0.5, 0.25 at 0, 100, 200')
y = get('combfr'); Y = np.abs(spec(y)); fr = np.fft.rfftfreq(len(y), 1 / SR)
pk = [fr[np.argmax(Y * (np.abs(fr - h * SR / 100.5) < 100))] for h in (1, 2, 3)]
ok(all(abs(p / (h * SR / 100.5) - 1) < 0.003 for h, p in zip((1, 2, 3), pk)), 'comb: fractional delay 100.5 puts the peaks at multiples of 477.6 Hz', ['%.1f' % p for p in pk])
y = get('combff'); w = wgrid(len(y)); ha = 1 - 0.7 * np.exp(-1j * w * 37)
ok(cmp_db(spec(y), ha) < 1e-9, 'comb: feed-forward |1 - 0.7 z^-37| exact')
y = get('combdamp'); ok(np.all(np.isfinite(y)) and abs(y[0] - 1) < 1e-12 and np.max(np.abs(y[20000:])) < np.max(np.abs(y[240:1000])), 'comb: damped feedback decays')

# ---------- formant ----------
Fv = [[600, 1040], [400, 1620], [250, 1750], [400, 750], [350, 600]]
errs = []
for v in range(5):
    y = get(f'form{v}'); Y = 20 * np.log10(np.abs(spec(y)) + 1e-12); fr = np.fft.rfftfreq(len(y), 1 / SR)
    for F in Fv[v]:
        band = np.abs(fr - F) < F * 0.15; fp = fr[band][np.argmax(Y[band])]; errs.append(abs(fp / F - 1))
ok(max(errs) < 0.04, 'formant: the first two formants of a e i o u sit at the table frequencies', '%.1f %% worst' % (100 * max(errs)))

# ---------- halfbands ----------
for nm, sr in (('os2', 44100), ('os4', 44100)):
    y = get(f'rt_{nm}'); Y = np.abs(spec(y)); fr = np.fft.rfftfreq(len(y), 1 / sr)
    pb = 20 * np.log10(Y[fr <= 20000])
    ok(np.max(np.abs(pb)) < 0.001, f'{nm}: up and down again is flat to 20 kHz at 44.1 kHz', '%.1e dB' % np.max(np.abs(pb)))
    m = 2 if nm == 'os2' else 4
    y = get(f'img_{nm}'); n = len(y); wn = np.blackman(n); Y = np.abs(np.fft.rfft(y * wn)); fr = np.fft.rfftfreq(n, 1 / (sr * m))
    main = np.max(Y); img = np.max(Y[fr > 24000]) if True else 0
    ok(20 * np.log10(img / main) < -110, f'{nm}: the up-sampler images of a 15 kHz tone are below -110 dB', '%.1f dB' % (20 * np.log10(img / main)))
    NUM[nm + '_image_db'] = 20 * np.log10(img / main)
    y = get(f'ali_{nm}')[2000:]; ok(20 * np.log10(np.max(np.abs(y)) + 1e-300) < -100, f'{nm}: a 30 kHz tone at the high rate is gone after down-sampling (below -100 dB)', '%.1f dB' % (20 * np.log10(np.max(np.abs(y)) + 1e-300)))
    NUM[nm + '_alias_30k_db'] = 20 * np.log10(np.max(np.abs(y)) + 1e-300)
# design check of the hard-coded sets
for nb, tbw, lim in ((12, 0.0245, -129), (6, 0.13, -116)):
    cf = HD.coefs(nb, tbw); _, smax = HD.report(cf, tbw); ok(smax < lim, f'halfband design {nb} coefficients, transition {tbw}: stop band {smax:.1f} dB')

# ---------- ADAA ----------
def alias_db(y, f0, sr=SR):
    y = y[4096:]; n = len(y); wn = np.blackman(n); P = np.abs(np.fft.rfft(y * wn)) ** 2; fr = np.fft.rfftfreq(n, 1 / sr)
    keep = np.zeros(len(P), bool)
    for h in range(1, 40):
        fh = h * f0
        if fh >= sr / 2: break
        keep |= np.abs(fr - fh) < 60
    keep |= fr < 20
    return 10 * np.log10(P[~keep].sum() / P[keep].sum())
names = ['tanh', 'hard clip', 'fold']
AL = {}
for t in range(3):
    for os_ in (1, 2, 4):
        for ad in (0, 1): AL[(t, os_, ad)] = alias_db(get(f'sh{t}_{os_}_{ad}'), F0)
    row = ', '.join(f'{os_}x {"ADAA" if ad else "plain"} {AL[(t, os_, ad)]:.1f}' for os_ in (1, 2, 4) for ad in (0, 1))
    print('      aliasing of a 4.5 kHz sine at drive 4 (dB against the harmonics):', names[t], row)
    ok(AL[(t, 1, 1)] < AL[(t, 1, 0)] - 6, f'ADAA {names[t]}: less aliasing than the plain shaper at 1x', f'{AL[(t,1,0)]:.1f} -> {AL[(t,1,1)]:.1f} dB')
    ok(AL[(t, 2, 1)] < AL[(t, 2, 0)] - 3 and AL[(t, 4, 1)] < AL[(t, 1, 0)] - 25, f'ADAA {names[t]}: 2x and 4x with ADAA beat the same without', f'2x {AL[(t,2,0)]:.1f} -> {AL[(t,2,1)]:.1f}, 4x {AL[(t,4,0)]:.1f} -> {AL[(t,4,1)]:.1f} dB')
    for os_ in (1, 2, 4):
        for ad in (0, 1): NUM[f'alias_{names[t].replace(" ","")}_{os_}x_{"adaa" if ad else "plain"}_db'] = AL[(t, os_, ad)]
    y = get(f'ramp{t}'); n = len(y); x = -3 + 6 * np.arange(n) / (n - 1); xm = np.concatenate([[0.5 * x[0]], 0.5 * (x[1:] + x[:-1])])
    f = [np.tanh, lambda v: np.clip(v, -1, 1), lambda v: (lambda t_: np.where(t_ < 2, t_ - 1, 3 - t_))((v + 1) - 4 * np.floor((v + 1) / 4))][t](xm)
    ok(np.max(np.abs(y[1:] - f[1:])) < 2e-4, f'ADAA {names[t]}: on a slow ramp it equals the shaper half a sample late', '%.1e' % np.max(np.abs(y[1:] - f[1:])))

# ---------- smoothing ----------
y = get('sm'); n = len(y) // 2; s, rp = y[:n], y[n:]
ok(abs(s[479] - (1 - math.exp(-1))) < 0.002 and s[-1] == 1.0, 'Smooth: 63 % after one time constant (10 ms), lands exactly on the target', '%.4f' % s[479])
ok(rp[479] == 1.0 and abs(rp[239] - 0.5) < 1e-12 and np.all(np.diff(rp[:480]) > 0), 'Ramp: linear, exactly on the target after 10 ms')

# ---------- cost ----------
for k, v in RES.items():
    if k.startswith('cpu_'): NUM[k + '_ns_per_sample'] = v['ns']; print('      cost', k[4:], '%.1f ns per sample (Node)' % v['ns'])
print(f'{N[1]} of {N[0]} checks passed')
if OUTJ: json.dump({'checks': N, 'fail': FAIL, 'numbers': NUM}, open(OUTJ, 'w'), indent=1)
sys.exit(1 if FAIL else 0)
