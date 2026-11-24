"""Python ports of AudioLab sound models that are simple enough to copy exactly.
Fitting against a port is thousands of times faster than rendering through the browser; the result is
always checked afterwards with a real render through the bridge."""
import numpy as np


def kick(I, sr=44100):
    """Port of kickRender() (Kick designer). I: tune,start,sweep,bend,len,tail,click,drive,ctype."""
    n = int(np.ceil(I["len"] * sr)) + 8
    t = np.arange(n) / sr
    fE = 440 * 2 ** ((I["tune"] - 69) / 12)
    fS = max(fE * 1.02, I["start"])
    cp = 1 + I["bend"] / 100 * 5
    hold = I["len"] * (.04 + .22 * I["tail"] / 100)
    tp = 2.8 - 2.4 * I["tail"] / 100
    fade = min(.006, I["len"] * .05)
    x = np.minimum(1, t / I["sweep"])
    f = np.exp(np.log(fE) + (np.log(fS) - np.log(fE)) * (1 - x) ** cp)
    ph = np.cumsum(2 * np.pi * f / sr)
    a = np.where(t < .0005, t / .0005, 1.0)
    y = np.clip((t - hold) / max(1e-4, I["len"] - hold), 0, 1)
    a = a * (1 - y) ** tp
    a = np.where(t > I["len"] - fade, a * np.maximum(0, (I["len"] - t) / fade), a)
    d = np.sin(ph) * a
    cl = I["click"] / 100 * .9
    ct = I.get("ctype", "tick")
    if cl > 0 and ct != "off":
        m = min(n, int(np.ceil(sr * .06)))
        seed = 12345
        nz = np.zeros(m)
        for i in range(m):
            seed = (seed * 1103515245 + 12345) & 0x7fffffff
            nz[i] = seed / 0x3fffffff - 1
        tt = t[:m]
        s = np.zeros(m)
        xp = yp = lp = 0.0
        for i in range(m):
            if ct == "tick":
                yp = .92 * (yp + nz[i] - xp); xp = nz[i]
                s[i] = np.sin(2 * np.pi * 3400 * tt[i]) * np.exp(-tt[i] / .0012) * .9 + yp * np.exp(-tt[i] / .0018) * .6
            elif ct == "snap":
                yp = .8 * (yp + nz[i] - xp); xp = nz[i]; lp += .45 * (yp - lp)
                s[i] = lp * np.exp(-tt[i] / .007) * 1.4
            elif ct == "knock":
                s[i] = np.sin(2 * np.pi * (260 - 1200 * tt[i]) * tt[i]) * np.exp(-tt[i] / .018) * .9
            else:
                yp = .97 * (yp + nz[i] - xp); xp = nz[i]
                s[i] = yp * np.exp(-tt[i] / .012) * .5
        d[:m] += s * cl
    g = 1 + I["drive"] / 100 * 14
    d = np.tanh(d * g) / np.tanh(g)
    pk = np.abs(d).max()
    return d * (.95 / pk if pk > 0 else 1)
