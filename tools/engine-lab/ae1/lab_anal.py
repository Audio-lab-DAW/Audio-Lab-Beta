# Task AE1: analyse the signals lab.js wrote (results/sig) and the app's own renders; write results/lab.json and the
# plot data the pick page embeds (results/plots.json).   python3 tools/engine-lab/ae1/lab_anal.py
import os, json
import numpy as np
from scipy.signal import freqz, bilinear, butter
from anal import alias_report, true_peak, overs_per_s, db, rms, spectrum_peak_db, spectrum_db

HERE = os.path.dirname(os.path.abspath(__file__)); SIG = os.path.join(HERE, 'results', 'sig')
ld = lambda n: np.fromfile(os.path.join(SIG, n + '.f64'))
sr = 48000; hz = lambda p: 440 * 2 ** ((p - 69) / 12)
R = {}; P = {}
APP = json.load(open(os.path.join(HERE, 'results', 'app.json')))


def logspec(x, sr, npts=420, fmin=20, beta=20.0, floor=-160):
    F, S = spectrum_peak_db(x, sr, beta)
    edges = np.geomspace(fmin, sr / 2, npts + 1); out = []
    for a, b in zip(edges[:-1], edges[1:]):
        m = (F >= a) & (F < b)
        out.append(round(float(max(S[m].max(), floor)) if m.any() else floor, 1))
    return {'f': [round(float(v), 1) for v in np.sqrt(edges[:-1] * edges[1:])], 'db': out}


def linspec(x, sr, npts=240, fmax=24000, beta=20.0, floor=-160):
    F, S = spectrum_peak_db(x, sr, beta)
    edges = np.linspace(0, fmax, npts + 1); out = []
    for a, b in zip(edges[:-1], edges[1:]):
        m = (F >= a) & (F < b); out.append(round(float(max(S[m].max(), floor)) if m.any() else floor, 1))
    return {'f0': 0, 'df': fmax / npts, 'db': out}


seg = lambda x: x[sr // 2: sr // 2 + sr]


def split_spec(x, sr, f0, npts=240, fmax=24000, floor=-160):
    """(harmonics only, everything else) as peak-calibrated binned spectra: the aliasing drawn apart from the note"""
    from scipy.signal.windows import kaiser
    from anal import _peak, HALF
    x = np.asarray(x, np.float64); w = kaiser(len(x), 20.0); X = np.fft.rfft(x * w); A = 20 * np.log10(2 * np.abs(X) / w.sum() + 1e-300)
    bw = sr / len(x); P = np.abs(X) ** 2; f = _peak(P, f0 / bw) * bw
    for k in (3, 9, 27, 81):
        if k * f < sr * .45: f = _peak(P, k * f / bw) * bw / k
    m = np.zeros(len(A), bool)
    for k in range(1, int(sr / 2 // f) + 1):
        c = int(k * f / bw); m[max(0, c - HALF):c + HALF + 2] = True
    F = np.arange(len(A)) * bw; edges = np.linspace(0, fmax, npts + 1); h, r = [], []
    for a, b in zip(edges[:-1], edges[1:]):
        sel = (F >= a) & (F < b)
        hh = A[sel & m]; rr = A[sel & ~m]
        h.append(round(float(max(hh.max(), floor)) if hh.size else floor, 1)); r.append(round(float(max(rr.max(), floor)) if rr.size else floor, 1))
    return {'f0': 0, 'df': fmax / npts, 'db': h}, {'f0': 0, 'df': fmax / npts, 'db': r}

# ---- oscillators: the port against the app (validation), and the candidates
rows = []
for p in (33, 45, 57, 69, 81, 88, 93, 100, 105):
    r = {'note': p, 'hz': hz(p)}
    for k in ('today', 'blep', 'pb2x'):
        a = alias_report(seg(ld('osc_%s_%d' % (k, p))), sr, hz(p)); r[k] = round(a['alias_db'], 1); r[k + '16'] = round(a['alias16_db'], 1)
    app = [o for o in APP['osc_saw'] if o['note'] == p][0]; r['app'] = round(app['alias_db'], 1); r['app16'] = round(app['alias16_db'], 1)
    rows.append(r); print('saw %3d  app %6.1f  port %6.1f  | BLEP %6.1f  2x PolyBLEP %6.1f   (<16k: app %6.1f BLEP %6.1f)' % (p, r['app'], r['today'], r['blep'], r['pb2x'], r['app16'], r['blep16']))
R['osc'] = rows
_h, _a = split_spec(seg(ld('osc_today_93')), sr, hz(93)); _, _b = split_spec(seg(ld('osc_blep_93')), sr, hz(93)); P['osc93'] = {'harm': _h, 'today': _a, 'blep': _b}

# ---- acid
rows = []
for p in (33, 45, 57, 69):
    r = {'note': p}
    for k in ('today', 'adaa1x', '2x', '2xadaa', 'hq', '4xadaa'):
        a = alias_report(seg(ld('acid_%s_%d' % (k, p))), sr, hz(p)); r[k] = round(a['alias_db'], 1); r[k + '16'] = round(a['alias16_db'], 1)
    app = [o for o in APP['acid'] if o['note'] == p][0]; r['app'] = round(app['alias_db'], 1)
    rows.append(r); print('   <16k: today %6.1f ADAA1x %6.1f 2x+ADAA %6.1f HQ %6.1f' % (r['today16'], r['adaa1x16'], r['2xadaa16'], r['hq16']));print('acid %d app %6.1f port %6.1f | ADAA 1x %6.1f  2x %6.1f  2x+ADAA %6.1f  HQ(2x,BLEP,SVF,ADAA) %6.1f  4x %6.1f' % (p, r['app'], r['today'], r['adaa1x'], r['2x'], r['2xadaa'], r['hq'], r['4xadaa']))
R['acid'] = rows
_h, _a = split_spec(seg(ld('acid_today_57')), sr, hz(57)); _, _b = split_spec(seg(ld('acid_hq_57')), sr, hz(57)); P['acid57'] = {'harm': _h, 'today': _a, 'hq': _b}

# ---- drive effect
rows = []
for f0, drv in ((2531, 60), (4057, 60), (5003, 100), (1013, 30)):
    r = {'f0': f0, 'drive': drv}
    for k in ('1x', '4x', '4xadaa', '8x'):
        r[k] = round(alias_report(seg(ld('drive_%s_%d_%d' % (k, f0, drv))), sr, f0)['alias_db'], 1)
    app = [o for o in APP['drive'] if abs(o['f0'] - f0) < 1 and o['drive'] == drv]; r['app'] = round(app[0]['alias_db'], 1) if app else None
    rows.append(r); print('drive %d Hz d%d: app(WaveShaper 4x) %s  1x %6.1f  4x %6.1f  4x+ADAA %6.1f  8x %6.1f' % (f0, drv, r['app'], r['1x'], r['4x'], r['4xadaa'], r['8x']))
R['drive'] = rows
_h, _a = split_spec(seg(ld('drive_4x_4057_60')), sr, 4057); _, _b = split_spec(seg(ld('drive_4xadaa_4057_60')), sr, 4057); P['drive4057'] = {'harm': _h, 'today': _a, 'hq': _b}

# ---- kick: everything above 18 kHz and the difference against a 16x reference in the first 20 ms
k1, k2, k4, k8, kr = ld('kick_1x'), ld('kick_2x'), ld('kick_4x'), ld('kick_8x'), ld('kick_ref')
n = min(len(k1), len(k4), len(kr)); w = slice(0, int(.03 * sr))
def kerr(a):  # error against the 16x reference, first 30 ms, in dB relative to the reference's level there
    return db(rms(a[w] - kr[w]) / rms(kr[w]))
R['kick'] = {'err_2x_db': kerr(k2), 'err_1x_db': kerr(k1), 'err_4x_db': kerr(k4), 'err_8x_db': kerr(k8)}
print('kick 2x %.1f' % R['kick']['err_2x_db']);print('kick: first 30 ms against a 32x reference: 1x %.1f dB, 4x %.1f dB, 8x %.1f dB' % (R['kick']['err_1x_db'], R['kick']['err_4x_db'], R['kick']['err_8x_db']))
P['kick'] = {'harm': linspec(kr[:int(.03 * sr)], sr, beta=8), 'today': linspec(k1[:int(.03 * sr)] - kr[:int(.03 * sr)], sr, beta=8), 'hq': linspec(k4[:int(.03 * sr)] - kr[:int(.03 * sr)], sr, beta=8)}

# ---- filter: per-16 coefficients against per-sample (the difference is the zipper / modulation error)
a, b1, s = ld('flt_rbj16'), ld('flt_rbj1'), ld('flt_svf')
R['filter'] = {'rbj16_vs_svf_db': db(rms(a - s) / rms(s)), 'rbj1_vs_svf_db': db(rms(b1 - s) / rms(s)), 'rbj16_vs_rbj1_db': db(rms(a - b1) / rms(b1))}
a2, s2 = ld('flt2_rbj16'), ld('flt2_svf')
R['filter']['audio_rate_db'] = db(rms(a2 - s2) / rms(s2))
print('filter env sweep: RBJ per 16 vs SVF %.1f dB, RBJ per sample vs SVF %.1f dB; audio-rate cut-off FM: %.1f dB' % (R['filter']['rbj16_vs_svf_db'], R['filter']['rbj1_vs_svf_db'], R['filter']['audio_rate_db']))
P['filter_fm'] = {'today': linspec(a2[sr // 4:], sr), 'hq': linspec(s2[sr // 4:], sr)}

# ---- EQ near the top: RBJ bilinear bell and the analog prototype; Pro EQ's cascade Q
def rbj_peak(f0, g, q, fs):
    A = 10 ** (g / 40); w = 2 * np.pi * f0 / fs; al = np.sin(w) / (2 * q)
    b = [1 + al * A, -2 * np.cos(w), 1 - al * A]; a = [1 + al / A, -2 * np.cos(w), 1 - al / A]; return b, a
def analog_peak(f, f0, g, q):
    A = 10 ** (g / 40); s = 1j * f / f0; return (s * s + s * (A / q) + 1) / (s * s + s / (A * q) + 1)
F = np.geomspace(1000, 24000, 300); eq = {}
for f0, g, q, fs in ((12000, 6, 1, 48000), (16000, 6, 1, 48000), (12000, 6, 1, 44100), (10000, 4, .7, 48000)):
    b_, a_ = rbj_peak(f0, g, q, fs); _, H = freqz(b_, a_, worN=F, fs=fs); Ha = analog_peak(F, f0, g, q)
    m = F < fs / 2 * .99
    dev = 20 * np.log10(np.abs(H[m])) - 20 * np.log10(np.abs(Ha[m]))
    at = lambda fx: float(np.interp(fx, F[m], dev))
    key = '%d_%d_%g_%d' % (f0, g, q, fs)
    eq[key] = {'at_15k': at(15000), 'at_18k': at(18000), 'at_20k': at(20000), 'max_abs': float(np.abs(dev).max())}
    if key == '12000_6_1_48000':
        P['eq'] = {'f': [round(float(v)) for v in F[m]], 'rbj': [round(float(v), 2) for v in 20 * np.log10(np.abs(H[m]))], 'analog': [round(float(v), 2) for v in 20 * np.log10(np.abs(Ha[m]))]}
    print('bell %s: RBJ - analog at 15k %.2f dB, 18k %.2f, 20k %.2f' % (key, eq[key]['at_15k'], eq[key]['at_18k'], eq[key]['at_20k']))
# Pro EQ's pass filters: round(sl/12) 2nd-order stages, Q .707 except the last = max(.3, b.q) with b.q .7 by default
cas = {}
for sl in (24, 48):
    st = sl // 12; w = np.geomspace(20, 20000, 2000); fc = 1000
    H = np.ones_like(w, complex)
    for i in range(st):
        q = .707 if i < st - 1 else .7
        s = 1j * w / fc; H *= 1 / (s * s + s / q + 1)
    bw = butter(2 * st, 2 * np.pi * fc, 'low', analog=True); _, Hb = __import__('scipy.signal', fromlist=['freqs']).freqs(*bw, worN=2 * np.pi * w)
    cas[sl] = {'at_fc_db': float(20 * np.log10(abs(np.interp(fc, w, np.abs(H))))), 'butter_at_fc_db': float(20 * np.log10(abs(np.interp(fc, w, np.abs(Hb))))),
               'oct_below_db': float(20 * np.log10(np.interp(fc / 2, w, np.abs(H)))), 'butter_oct_below_db': float(20 * np.log10(np.interp(fc / 2, w, np.abs(Hb))))}
    print('Pro EQ low-pass %d dB/oct at its frequency: %.2f dB (Butterworth %.2f); one octave below %.2f dB (Butterworth %.2f)' % (sl, cas[sl]['at_fc_db'], cas[sl]['butter_at_fc_db'], cas[sl]['oct_below_db'], cas[sl]['butter_oct_below_db']))
R['eq'] = {'bell': eq, 'cascade': cas}

# ---- resampling
rows = []
for f0 in (1000, 5000, 10000, 15000):
    r = {'case': '44.1k in 48k', 'f0': f0, 'lin': round(alias_report(seg(ld('rs_lin_%d' % f0)), sr, f0, harmonics=1)['alias_db'], 1), 'sinc': round(alias_report(seg(ld('rs_sinc_%d' % f0)), sr, f0, harmonics=1)['alias_db'], 1)}
    app = [o for o in APP['resample'] if o['case'].startswith('buffer') and o['f0'] == f0]; r['app'] = round(app[0]['alias_db'], 1) if app else None
    rows.append(r); print('44.1k->48k %5d Hz: app %s  linear port %6.1f  sinc %6.1f' % (f0, r['app'], r['lin'], r['sinc']))
rate = 2 ** (7 / 12)
for f0 in (1000, 5000, 10000):
    r = {'case': '+7 semitones', 'f0': f0, 'lin': round(alias_report(seg(ld('rp_lin_%d' % f0)), sr, f0 * rate, harmonics=1)['alias_db'], 1), 'sinc': round(alias_report(seg(ld('rp_sinc_%d' % f0)), sr, f0 * rate, harmonics=1)['alias_db'], 1)}
    app = [o for o in APP['resample'] if o['case'].startswith('playback') and o['f0'] == f0]; r['app'] = round(app[0]['alias_db'], 1) if app else None
    rows.append(r); print('+7 st %5d Hz: app %s  linear port %6.1f  sinc %6.1f' % (f0, r['app'], r['lin'], r['sinc']))
R['resample'] = rows
_h, _a = split_spec(seg(ld('rs_lin_10000')), sr, 10000); _, _b = split_spec(seg(ld('rs_sinc_10000')), sr, 10000); P['rs10k'] = {'harm': _h, 'today': _a, 'hq': _b}

# ---- limiter
rows = []
for push in (6, 10):
    for mode in ('today', 'tp4', 'tp4clip'):
        y = np.vstack([ld('lim_%s_%d_L' % (mode, push)), ld('lim_%s_%d_R' % (mode, push))])
        r = {'push': push, 'mode': mode, 'sample_peak': db(np.abs(y).max()), 'tp4': true_peak(y, 4), 'tp16': true_peak(y, 16), 'overs_per_s': overs_per_s(y, sr, -.3), 'rms_db': db(rms(y))}
        rows.append(r); print('limiter push %d %-8s sample %6.2f  TP16 %6.2f dBTP  overs %5.1f/s  rms %6.2f' % (push, mode, r['sample_peak'], r['tp16'], r['overs_per_s'], r['rms_db']))
        if push == 10 and mode in ('today', 'tp4clip'):
            from anal import upsample
            u = np.abs(upsample(y[:, sr * 10:sr * 14], 16)).max(axis=0); W = 16 * sr // 100   # true peak per 10 ms, 4 s of the Climax (10 to 14 s)
            P.setdefault('lim', {})[mode] = [round(db(u[i:i + W].max()), 2) for i in range(0, len(u) - W + 1, W)]
R['limit'] = rows

# ---- dither
rows = []
x = 10 ** (-90 / 20) * np.sin(2 * np.pi * 1000 * np.arange(96000) / sr)
for m in ('off', 'tpdf', 'ns', 'ns9'):
    y = ld('dith_' + m); e = y - x; F, S = spectrum_db(e, sr, beta=12)
    band = lambda a, b: float(10 * np.log10(np.mean(10 ** (S[(F > a) & (F < b)] / 10))))
    # audibility proxy: noise power weighted by an ISO 226-like curve is beyond scope; report the 1-5 kHz band (ear most sensitive) and total
    r = {'mode': m, 'total_db': db(rms(e)), 'b1_5k': band(1000, 5000), 'b15_20k': band(15000, 20000)}
    rows.append(r); print('dither %-4s total %6.1f dBFS, noise density 1-5 kHz %6.1f, 15-20 kHz %6.1f dB/bin' % (m, r['total_db'], r['b1_5k'], r['b15_20k']))
    P.setdefault('dith', {})[m] = logspec(e, sr, npts=120, beta=12)
R['dither'] = rows

json.dump(R, open(os.path.join(HERE, 'results', 'lab.json'), 'w'), indent=1)
json.dump(P, open(os.path.join(HERE, 'results', 'plots.json'), 'w'))
print('written; plots.json %.0f kB' % (os.path.getsize(os.path.join(HERE, 'results', 'plots.json')) / 1024))
