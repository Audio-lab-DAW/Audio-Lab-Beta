"""Measuring and comparing audio: the "ears" of the remake framework.

Everything works on float arrays shaped (channels, n). `compare(ref, mix, sr)` returns numbers that say how
far a render is from the reference: loudness, tonal balance per band, spectrogram distance, rhythm
(onset-envelope correlation), harmony (chroma similarity) and stereo width, plus a single 0-100 score.
`plot_compare` draws both spectrograms and the band balance so the difference can be seen.
"""
import numpy as np, soundfile as sf, librosa
import pyloudnorm as pyln
from scipy.signal import welch, butter, sosfiltfilt

BANDS = [(20, 60), (60, 120), (120, 250), (250, 500), (500, 1000), (1000, 2000), (2000, 4000), (4000, 8000), (8000, 16000)]
BAND_NAMES = ["sub", "bass", "low-mid", "mid-lo", "mid", "mid-hi", "presence", "high", "air"]


def load(path, sr=44100):
    x, s = sf.read(path, dtype="float32", always_2d=True)
    x = x.T
    if s != sr:
        x = np.stack([librosa.resample(c, orig_sr=s, target_sr=sr) for c in x])
    if x.shape[0] == 1:
        x = np.repeat(x, 2, 0)
    return x


def save(path, x, sr=44100):
    sf.write(path, np.asarray(x).T, sr, subtype="FLOAT")


def mono(x):
    return x.mean(0) if x.ndim == 2 else x


def lufs(x, sr):
    if x.shape[-1] < sr * 0.45:
        return -70.0
    v = pyln.Meter(sr).integrated_loudness(x.T.astype(np.float64))
    return float(v) if np.isfinite(v) else -70.0


def rms_db(x):
    return float(10 * np.log10(np.mean(np.square(x)) + 1e-12))


def band_db(x, sr, bands=BANDS):
    f, p = welch(mono(x), sr, nperseg=8192)
    return np.array([10 * np.log10(p[(f >= a) & (f < b)].sum() * (f[1] - f[0]) + 1e-14) for a, b in bands])


def logmel(x, sr, n_mels=80, hop=512):
    m = librosa.feature.melspectrogram(y=mono(x), sr=sr, n_fft=2048, hop_length=hop, n_mels=n_mels, fmin=25, fmax=16000)
    return 10 * np.log10(m + 1e-10)


def onset_env(x, sr, hop=256):
    return librosa.onset.onset_strength(y=mono(x), sr=sr, hop_length=hop)


def band_env(x, sr, lo, hi, hop=128):
    y = sosfiltfilt(butter(4, [lo, hi], "band", fs=sr, output="sos"), mono(x))
    e = np.abs(y)
    n = len(e) // hop
    return e[: n * hop].reshape(n, hop).mean(1)


def chroma(x, sr):
    c = librosa.feature.chroma_cqt(y=mono(x), sr=sr, hop_length=2048, fmin=librosa.note_to_hz("C2"), n_octaves=6)
    v = c.mean(1)
    return v / (np.linalg.norm(v) + 1e-9)


def width_db(x):
    if x.ndim < 2 or x.shape[0] < 2:
        return -60.0
    m, s = (x[0] + x[1]) / 2, (x[0] - x[1]) / 2
    return float(10 * np.log10((np.mean(s * s) + 1e-12) / (np.mean(m * m) + 1e-12)))


def _corr(a, b, maxlag):
    n = min(len(a), len(b))
    a, b = a[:n] - a[:n].mean(), b[:n] - b[:n].mean()
    best = (-2.0, 0)
    for lag in range(-maxlag, maxlag + 1):
        if lag >= 0:
            u, v = a[lag:], b[: n - lag]
        else:
            u, v = a[: n + lag], b[-lag:]
        d = np.linalg.norm(u) * np.linalg.norm(v)
        c = float(np.dot(u, v) / d) if d > 0 else 0.0
        if c > best[0]:
            best = (c, lag)
    return best


def compare(ref, mix, sr):
    """How far is `mix` from `ref`? Both (2, n), same sample rate, already cut to the same span."""
    n = min(ref.shape[-1], mix.shape[-1])
    ref, mix = ref[..., :n], mix[..., :n]
    out = {}
    out["lufs_ref"], out["lufs_mix"] = lufs(ref, sr), lufs(mix, sr)
    out["d_lufs"] = out["lufs_mix"] - out["lufs_ref"]
    br, bm = band_db(ref, sr), band_db(mix, sr)
    out["band_ref"], out["band_mix"] = br.round(1).tolist(), bm.round(1).tolist()
    out["d_band"] = (bm - br).round(1).tolist()
    # tonal balance with the overall level difference taken out
    d = (bm - br) - np.mean(bm - br)
    out["d_balance"] = d.round(1).tolist()
    out["balance_err"] = float(np.mean(np.abs(d)))
    mr, mm = logmel(ref, sr), logmel(mix, sr)
    k = min(mr.shape[1], mm.shape[1])
    fl = max(mr.max(), mm.max()) - 70  # ignore what is below the noise floor of interest
    out["mel_dist"] = float(np.mean(np.abs(np.maximum(mr[:, :k], fl) - np.maximum(mm[:, :k], fl))))
    c, lag = _corr(onset_env(ref, sr), onset_env(mix, sr), 8)
    out["rhythm_corr"], out["rhythm_lag_ms"] = c, lag * 256 / sr * 1000
    c2, _ = _corr(band_env(ref, sr, 35, 120), band_env(mix, sr, 35, 120), 16)
    out["low_env_corr"] = c2
    out["chroma_sim"] = float(np.dot(chroma(ref, sr), chroma(mix, sr)))
    out["width_ref"], out["width_mix"] = width_db(ref), width_db(mix)
    out["score"] = score(out)
    return out


def score(c):
    """One number, 0-100. 100 = indistinguishable by these measures. Weights are a judgement call:
    spectrogram distance and rhythm carry most, then tonal balance, harmony, loudness and width."""
    s = 100.0
    s -= min(30, c["mel_dist"] * 2.5)
    s -= min(20, max(0, 1 - c["rhythm_corr"]) * 25)
    s -= min(15, c["balance_err"] * 3)
    s -= min(15, max(0, 1 - c["chroma_sim"]) * 40)
    s -= min(10, abs(c["d_lufs"]) * 2)
    s -= min(10, abs(c["width_mix"] - c["width_ref"]) * .7)
    return round(max(0.0, s), 1)


def fmt(c, name=""):
    b = " ".join(f"{v:+5.1f}" for v in c["d_band"])
    return (f"{name:<14} score {c['score']:5.1f} | LUFS {c['lufs_ref']:6.1f} -> {c['lufs_mix']:6.1f} ({c['d_lufs']:+.1f}) | "
            f"mel {c['mel_dist']:.1f} dB | rhythm {c['rhythm_corr']:.2f} | low-env {c['low_env_corr']:.2f} | "
            f"chroma {c['chroma_sim']:.2f} | width {c['width_ref']:.0f}->{c['width_mix']:.0f} | bands {b}")


def plot_compare(ref, mix, sr, path, title=""):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    n = min(ref.shape[-1], mix.shape[-1])
    mr, mm = logmel(ref[..., :n], sr), logmel(mix[..., :n], sr)
    vmax = max(mr.max(), mm.max())
    fig, ax = plt.subplots(3, 1, figsize=(15, 9), gridspec_kw={"height_ratios": [3, 3, 2]})
    for a, m, t in ((ax[0], mr, "original"), (ax[1], mm, "AudioLab render")):
        a.imshow(m, origin="lower", aspect="auto", vmin=vmax - 70, vmax=vmax, cmap="magma", extent=[0, n / sr, 0, m.shape[0]])
        a.set_title(f"{title}  {t}", fontsize=10)
        a.set_ylabel("mel band")
    br, bm = band_db(ref, sr), band_db(mix, sr)
    x = np.arange(len(BANDS))
    ax[2].bar(x - .2, br, .4, label="original")
    ax[2].bar(x + .2, bm, .4, label="AudioLab")
    ax[2].set_xticks(x)
    ax[2].set_xticklabels([f"{n_}\n{a}-{b}" for n_, (a, b) in zip(BAND_NAMES, BANDS)], fontsize=8)
    ax[2].set_ylim(min(br.min(), bm.min()) - 3, max(br.max(), bm.max()) + 3)
    ax[2].legend()
    ax[2].set_ylabel("dB")
    plt.tight_layout()
    plt.savefig(path, dpi=70)
    plt.close(fig)


class Ref:
    """The reference song on a beat grid: cut any span of beats out of the original or one of its stems."""

    def __init__(self, path, bpm, t0, stems=None, sr=44100):
        self.sr, self.bpm, self.t0 = sr, bpm, t0
        self.x = load(path, sr)
        self.stems = {k: load(p, sr) for k, p in (stems or {}).items()}

    def cut(self, b0, b1, stem=None):
        spb = 60 / self.bpm
        a, b = int(round((self.t0 + b0 * spb) * self.sr)), int(round((self.t0 + b1 * spb) * self.sr))
        x = self.stems[stem] if stem else self.x
        seg = x[:, max(0, a):b]
        if a < 0:
            seg = np.concatenate([np.zeros((x.shape[0], -a), dtype=x.dtype), seg], 1)
        return seg
