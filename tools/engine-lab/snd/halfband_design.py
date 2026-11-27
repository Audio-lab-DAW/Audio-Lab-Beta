"""Polyphase IIR halfband design (task SND-0).
Method: Valenzuela and Constantinides (1983), as implemented by Laurent de Soras in HIIR
(PolyphaseIir2Designer, WTFPL licence). This file is my own implementation of that method; it
prints the coefficient sets the kit hard-codes and checks each one by measuring its response."""
import math, numpy as np, sys

def transition_param(tbw):
    k = math.tan((1 - tbw * 2) * math.pi / 4); k *= k
    kk = (1 - k * k) ** 0.25
    e = 0.5 * (1 - kk) / (1 + kk); e2 = e * e; e4 = e2 * e2
    q = e * (1 + e4 * (2 + e4 * (15 + 150 * e4)))
    return k, q

def acc_num(q, order, c):
    i, j, acc = 0, 1, 0.0
    while True:
        t = q ** (i * (i + 1)) * math.sin((i * 2 + 1) * c * math.pi / order) * j
        acc += t; j = -j; i += 1
        if abs(t) <= 1e-100: return acc

def acc_den(q, order, c):
    i, j, acc = 1, -1, 0.0
    while True:
        t = q ** (i * i) * math.cos(i * 2 * c * math.pi / order) * j
        acc += t; j = -j; i += 1
        if abs(t) <= 1e-100: return acc

def coefs(nb, tbw):
    k, q = transition_param(tbw)
    order = nb * 2 + 1
    out = []
    for idx in range(nb):
        c = idx + 1
        num = acc_num(q, order, c) * q ** 0.25
        den = acc_den(q, order, c) + 0.5
        ww = num / den; w2 = ww * ww
        x = math.sqrt((1 - w2 * k) * (1 - w2 / k)) / (1 + w2)
        out.append((1 - x) / (1 + x))
    return out

def response(cf, w):
    """H(e^jw) of the halfband 0.5*(A0(z^2) + z^-1 A1(z^2)); even coefs in path 0."""
    z = np.exp(1j * w); z2 = z * z
    a0 = np.ones_like(z); a1 = np.ones_like(z)
    for i, c in enumerate(cf):
        ap = (c + 1 / z2) / (1 + c / z2)
        if i % 2 == 0: a0 = a0 * ap
        else: a1 = a1 * ap
    return 0.5 * (a0 + a1 / z)

def report(cf, tbw):
    pas = np.linspace(1e-4, (0.25 - tbw) * 2 * math.pi, 2000)
    stp = np.linspace((0.25 + tbw) * 2 * math.pi, math.pi, 2000)
    hp = 20 * np.log10(np.abs(response(cf, pas))); hs = 20 * np.log10(np.abs(response(cf, stp)))
    return hp.min(), hs.max()

if __name__ == '__main__':
    for nb, tbw, name in [(12, 0.0245, '2x (first stage): pass 0 to 20 kHz at 44.1 kHz'),
                          (6, 0.13, '4x second stage: pass 0 to 20 kHz at 88.2 kHz'),
                          (8, 0.0245 * 2, 'cheap 2x')]:
        cf = coefs(nb, tbw); pmin, smax = report(cf, tbw)
        print(name, nb, tbw, 'passband min %.2e dB, stopband max %.1f dB' % (pmin, smax))
        print('[' + ','.join(repr(c) for c in cf) + ']')
