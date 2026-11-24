"""Fitting AudioLab sounds to a target by rendering through the app and measuring the difference.

fit_params(al, apply, x0, bounds, target, render) runs a bounded pattern search: `apply(values)` writes the
candidate into the open project (through the bridge), `render()` returns audio, and the loss is the
distance between log-mel spectrograms (level included, so volume is fitted too).
automix(...) solves for track volumes so that a set of rendered tracks adds up to a target's band energies.
"""
import numpy as np, librosa
from scipy.optimize import nnls


def mel_db(x, sr, n_mels=64, hop=128, fmin=30, fmax=16000, n_fft=1024):
    x = x.mean(0) if x.ndim == 2 else x
    m = librosa.feature.melspectrogram(y=x, sr=sr, n_fft=n_fft, hop_length=hop, n_mels=n_mels, fmin=fmin, fmax=fmax)
    return 10 * np.log10(m + 1e-9)


def mel_loss(a, b, sr, floor=60, level_free=False, **kw):
    """Mean absolute difference between log-mel spectrograms in dB. level_free=True first removes the overall
    level difference (use it to fit the character of a sound; the level is set later by automix)."""
    n = min(a.shape[-1], b.shape[-1])
    A, B = mel_db(a[..., :n], sr, **kw), mel_db(b[..., :n], sr, **kw)
    if level_free:
        A = A - A.max() + B.max()
    fl = max(A.max(), B.max()) - floor
    return float(np.mean(np.abs(np.maximum(A, fl) - np.maximum(B, fl))))


def fit_params(apply, render, target, sr, x0, lo, hi, iters=3, steps=(.25, .1, .04), log=None, loss_kw=None, verbose=True):
    """Bounded coordinate (pattern) search. x0/lo/hi: lists. `log`: indexes searched on a log scale.
    Returns (best values, best loss). Cheap in renders: about 2 per parameter per pass."""
    lo, hi = np.array(lo, float), np.array(hi, float)
    log = set(log or [])
    to_u = lambda v: np.array([(np.log(v[i] / lo[i]) / np.log(hi[i] / lo[i])) if i in log else (v[i] - lo[i]) / (hi[i] - lo[i]) for i in range(len(v))])
    to_v = lambda u: np.array([lo[i] * (hi[i] / lo[i]) ** u[i] if i in log else lo[i] + u[i] * (hi[i] - lo[i]) for i in range(len(u))])
    kw = loss_kw or {}

    def f(u):
        apply(to_v(np.clip(u, 0, 1)).tolist())
        return mel_loss(render(), target, sr, **kw)

    u = np.clip(to_u(np.array(x0, float)), 0, 1)
    best = f(u)
    n_eval = 1
    for it in range(iters):
        st = steps[min(it, len(steps) - 1)]
        improved = True
        while improved:
            improved = False
            for i in range(len(u)):
                for d in (st, -st):
                    c = u.copy()
                    c[i] = np.clip(c[i] + d, 0, 1)
                    if c[i] == u[i]:
                        continue
                    v = f(c)
                    n_eval += 1
                    if v < best - 1e-3:
                        best, u, improved = v, c, True
                        break
        if verbose:
            print(f"  pass {it + 1}: loss {best:.3f} dB after {n_eval} renders", to_v(u).round(3).tolist(), flush=True)
    apply(to_v(u).tolist())
    return to_v(u).tolist(), best


def band_matrix(x, sr, bands, frame_s=None):
    """Mean power per band (and per time frame when frame_s is given), flattened."""
    from scipy.signal import stft
    x = x.mean(0) if x.ndim == 2 else x
    f, t, Z = stft(x, sr, nperseg=4096, noverlap=2048)
    P = np.abs(Z) ** 2
    rows = [P[(f >= a) & (f < b)].sum(0) for a, b in bands]
    M = np.array(rows)
    if frame_s:
        k = max(1, int(round(frame_s * sr / 2048)))
        n = M.shape[1] // k
        M = M[:, : n * k].reshape(len(bands), n, k).mean(2)
    else:
        M = M.mean(1, keepdims=True)
    return M.ravel()


def automix(stems, target, sr, bands, frame_s=None, max_gain=4.0):
    """Non-negative least squares on band powers: gains (linear amplitude) for each rendered track so
    their sum matches the target's band energies. stems: {name: audio}. Powers add when tracks are uncorrelated."""
    names = list(stems)
    A = np.stack([band_matrix(stems[n], sr, bands, frame_s) for n in names], 1)
    b = band_matrix(target, sr, bands, frame_s)
    w = 1 / np.sqrt(b + b.max() * 1e-3)  # between absolute and relative error: loud bands lead, quiet ones still count
    g2, _ = nnls(A * w[:, None], b * w)
    return {n: float(min(max_gain, np.sqrt(v))) for n, v in zip(names, g2)}


EQ_F = [45, 90, 180, 360, 720, 1440, 2880, 5760, 11520]


def eq_bands(gains, freqs=EQ_F, q=1.2):
    """Pro EQ band list (9 bells, one per octave) from gains in dB."""
    return [{"t": "peaking", "f": f, "g": round(float(np.clip(g, -24, 24)), 1), "q": q, "on": True, "sl": 12, "pl": "st"} for f, g in zip(freqs, gains)]


def octave_db(x, sr, freqs=EQ_F):
    from scipy.signal import welch
    x = x.mean(0) if x.ndim == 2 else x
    f, p = welch(x, sr, nperseg=8192)
    return np.array([10 * np.log10(p[(f >= c / 2 ** .5) & (f < c * 2 ** .5)].sum() + 1e-16) for c in freqs])


def eq_match(render, target, sr, set_gains, iters=3, floor_db=45, level_free=True, lo=-18, hi=12):
    """Find Pro EQ gains so that the rendered sound has the target's octave balance.
    render(): audio with the current EQ; set_gains(g): writes gains (dB per octave band) into the project.
    Bands where the target is more than floor_db below its loudest band are left alone."""
    g = np.zeros(len(EQ_F))
    set_gains(g.tolist())
    T = octave_db(target, sr)
    use = T > T.max() - floor_db
    w = np.clip(1 - (T.max() - T) / 24, 0, 1)   # the level is anchored on the bands that carry the sound
    for _ in range(iters):
        M = octave_db(render(), sr)
        d = T - M
        if level_free:
            d = d - np.sum(d * w) / np.sum(w)
        d[~use] = np.minimum(d[~use], 0) * .5
        g = np.clip(g + .8 * d, lo, hi)
        set_gains(g.tolist())
    return g.round(1).tolist()
