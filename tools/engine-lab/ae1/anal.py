# Analysis helpers for task AE1 (sound quality): aliasing against harmonics, true peak, spectra.
import numpy as np
from scipy.signal import resample_poly
from scipy.signal.windows import kaiser

db = lambda v: float(20 * np.log10(max(float(v), 1e-30)))
rms = lambda x: float(np.sqrt(np.mean(np.asarray(x, np.float64) ** 2)))
BETA = 20.0   # Kaiser window: side lobes near -150 dB, main lobe about +-6.5 bins
HALF = 9      # bins on each side of a harmonic counted as that harmonic


def _spec(x):
    x = np.asarray(x, np.float64)
    w = kaiser(len(x), BETA)
    X = np.fft.rfft(x * w)
    P = (np.abs(X) ** 2) / (w.sum() ** 2) * 4   # a sine of amplitude A reads A^2 summed over its lobe ~ (A^2)*enbw
    return P, w


def _peak(P, b):
    b = int(round(b)); lo = max(1, b - HALF); hi = min(len(P) - 2, b + HALF)
    k = lo + int(np.argmax(P[lo:hi + 1]))
    a, m, c = np.log(P[k - 1] + 1e-300), np.log(P[k] + 1e-300), np.log(P[k + 1] + 1e-300)
    d = .5 * (a - c) / (a - 2 * m + c) if (a - 2 * m + c) != 0 else 0
    return k + d


def alias_report(x, sr, f0, harmonics=None, lo_hz=20.0):
    """Power of everything that is not a harmonic of f0 (aliases, images, noise) against the power of the harmonics.
    harmonics=1: only the fundamental counts as signal (for resampling tests)."""
    x = np.asarray(x, np.float64)
    N = len(x); P, w = _spec(x); bw = sr / N
    f = _peak(P, f0 / bw) * bw
    # refine with higher harmonics so that k*f lands on the k-th harmonic far up
    if harmonics != 1:
        for k in (3, 9, 27, 81):
            if k * f < sr * .45:
                f = _peak(P, k * f / bw) * bw / k
    nyq = sr / 2
    mask = np.zeros(len(P), bool)
    K = 1 if harmonics == 1 else int(nyq // f)
    hp = []
    for k in range(1, K + 1):
        c = k * f / bw; lo = max(0, int(c) - HALF); hi = min(len(P), int(c) + HALF + 2)
        mask[lo:hi] = True; hp.append(P[lo:hi].sum())
    sig = float(np.sum(hp)); fund = float(hp[0])
    fr = np.arange(len(P)) * bw
    rest = (~mask) & (fr > lo_hz)
    al_ = float(P[rest].sum())
    al16 = float(P[rest & (fr < 16000)].sum())
    if rest.any():
        k = int(np.argmax(np.where(rest, P, 0)))
        worst = float(P[k]); worst_hz = float(fr[k])
    else:
        worst, worst_hz = 1e-30, 0
    pk_f = float(P[int(round(f / bw)) - HALF:int(round(f / bw)) + HALF + 1].max())
    return {'f0': float(f), 'alias_db': 10 * np.log10(al_ / sig + 1e-30), 'alias16_db': 10 * np.log10(al16 / sig + 1e-30),
            'worst_db': 10 * np.log10(worst / pk_f + 1e-30), 'worst_hz': worst_hz,
            'harm_db': 10 * np.log10((sig - fund) / fund + 1e-30)}


def spectrum_db(x, sr, beta=BETA):
    x = np.asarray(x, np.float64); w = kaiser(len(x), beta)
    X = np.fft.rfft(x * w); P = np.abs(X) ** 2 / (w ** 2).sum() / (sr / 2) * (sr / len(x))   # power per bin, noise-calibrated
    return np.fft.rfftfreq(len(x), 1 / sr), 10 * np.log10(P + 1e-300)


def spectrum_peak_db(x, sr, beta=BETA):
    """amplitude spectrum calibrated for sines: a full-scale sine reads 0 dB"""
    x = np.asarray(x, np.float64); w = kaiser(len(x), beta)
    X = np.fft.rfft(x * w); A = 2 * np.abs(X) / w.sum()
    return np.fft.rfftfreq(len(x), 1 / sr), 20 * np.log10(A + 1e-300)


def upsample(y, os):
    return resample_poly(np.atleast_2d(y), os, 1, axis=1, window=('kaiser', 12.0))


def true_peak(y, os=4):
    return db(np.abs(upsample(y, os)).max())


def overs_per_s(y, sr, ceil_db, os=16):
    u = np.abs(upsample(y, os)).max(axis=0) > 10 ** (ceil_db / 20) * 1.0001
    if not u.any():
        return 0.0
    edges = np.flatnonzero(np.diff(u.astype(np.int8)) == 1)
    return float((len(edges) + int(u[0])) / (y.shape[-1] / sr))
