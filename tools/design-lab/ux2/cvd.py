#!/usr/bin/env python3
"""Task UX2: how today's track colours separate for the three common colour-vision deficiencies, and colour-blind safe candidates.
   python3 tools/design-lab/ux2/cvd.py [out dir] [screenshot.png]
Simulation: Machado, Oliveira and Fernandes 2009, severity 1.0 (dichromacy, the worst case), applied in linear sRGB.
Distance: CIEDE2000 between each pair of track colours, as drawn: a clip body is the track colour at clipA 36 % over the lane,
the header strip and clip edge are the full colour. Both are scored. Under ~10 a pair is hard to tell apart at a glance; under ~5 it is the same colour.
Writes cvd.json and, with a screenshot, the screenshot simulated three times (<name>-protan.png ...)."""
import sys, json, itertools, random, colorsys, os
import numpy as np
from skimage.color import rgb2lab, deltaE_ciede2000

OUT = sys.argv[1] if len(sys.argv) > 1 else 'ux2-out'
SHOT = sys.argv[2] if len(sys.argv) > 2 else None
os.makedirs(OUT, exist_ok=True)

M = {
    'protan': np.array([[0.152286, 1.052583, -0.204868], [0.114503, 0.786281, 0.099216], [-0.003882, -0.048116, 1.051998]]),
    'deutan': np.array([[0.367322, 0.860646, -0.227968], [0.280085, 0.672501, 0.047413], [-0.011820, 0.042940, 0.968881]]),
    'tritan': np.array([[1.255528, -0.076749, -0.178779], [-0.078411, 0.930809, 0.147602], [0.004733, 0.691367, 0.303900]]),
}
def lin(c): c = np.asarray(c, float) / 255; return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
def enc(c): c = np.clip(c, 0, 1); return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055) * 255
def sim(rgb, k): return rgb if k == 'normal' else enc(lin(rgb) @ M[k].T)
def hx(h): h = h.lstrip('#'); return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], float)
def tohex(c): return '#' + ''.join(f'{int(round(max(0, min(255, v)))):02x}' for v in c)
LANE = np.array([26, 31, 38], float)  # TH.lane0 at bgL 40 (hsl 215 11% 13%)
def body(c, a=.36): return c * a + LANE * (1 - a)

def lab(cs): return rgb2lab(np.asarray(cs, float).reshape(1, -1, 3) / 255).reshape(-1, 3)

def score(pal, kinds=('normal', 'protan', 'deutan', 'tritan')):
    res = {}
    for k in kinds:
        for part, f in (('edge', lambda c: c), ('body', body)):
            L = lab([sim(f(hx(c)), k) for c in pal])
            d = [(float(deltaE_ciede2000(L[i], L[j])), i, j) for i, j in itertools.combinations(range(len(pal)), 2)]
            d.sort()
            res[(k, part)] = d
    return res

def summary(pal, name):
    s = score(pal); out = {'name': name, 'pal': pal, 'by': {}}
    for (k, part), d in s.items():
        out['by'][f'{k}/{part}'] = {'min': round(d[0][0], 1), 'pair': [pal[d[0][1]], pal[d[0][2]]],
                                    'under10': [[pal[i], pal[j], round(v, 1)] for v, i, j in d if v < 10]}
    out['worst_edge'] = min(v['min'] for kk, v in out['by'].items() if kk.endswith('edge'))
    out['worst_body'] = min(v['min'] for kk, v in out['by'].items() if kk.endswith('body'))
    out['sim'] = {k: [tohex(sim(hx(c), k)) for c in pal] for k in M}
    return out

TODAY = ['#4c8dff', '#3ecf8e', '#f5c84c', '#ff6b6b', '#ff9a3c', '#b583ff', '#4cc9f0', '#ff7ac8']
NAMES = ['blue', 'green', 'yellow', 'red', 'orange', 'violet', 'cyan', 'pink']
OKABE = ['#56B4E9', '#009E73', '#F0E442', '#D55E00', '#E69F00', '#CC79A7', '#0072B2', '#BBBBBB']
# Okabe-Ito lifted for a dark ground: the same hues, the two dark ones (blue #0072B2, green #009E73) lighter so they read on lanes
OKABE_D = ['#56b4e9', '#14b386', '#f0e442', '#e2661c', '#eea52b', '#d78fb8', '#3f7fd9', '#c8c8d0']

# oklab helpers for the tuned palette
def to_oklch(c):
    r, g, b = lin(c)
    l = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b; m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b; s = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b
    l, m, s = np.cbrt(l), np.cbrt(m), np.cbrt(s)
    L = 0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s; a = 1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s; bb = 0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s
    return np.array([L, np.hypot(a, bb), np.degrees(np.arctan2(bb, a)) % 360])
def from_oklch(L, C, H):
    a, b = C * np.cos(np.radians(H)), C * np.sin(np.radians(H))
    l = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3; m = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3; s = (L - 0.0894841775 * a - 1.2914855480 * b) ** 3
    rgb = np.array([4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s, -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s, -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s])
    return enc(rgb)

def tune(base, seed=7, iters=2500, dh=16, dl=.09, dc=.035):
    """keep each colour near today's (hue within dh degrees, lightness within dl, chroma within dc, in OKLCH) and spread them for all four visions:
    maximise the smallest CIEDE2000 distance over normal, protan, deutan and tritan, edges and clip bodies, by random hill climbing"""
    rnd = random.Random(seed); o = [to_oklch(hx(c)) for c in base]
    def mk(p): return [tohex(from_oklch(*v)) for v in p]
    def fit(p):
        pal = mk(p); s = score(pal)
        return min(d[0][0] for d in s.values()) + 0.02 * sum(d[0][0] for d in s.values())
    cur = [v.copy() for v in o]; best = fit(cur)
    for it in range(iters):
        i = rnd.randrange(len(cur)); v = cur[i].copy()
        v += np.array([rnd.gauss(0, .02), rnd.gauss(0, .01), rnd.gauss(0, 4)])
        v[0] = np.clip(v[0], max(.64, o[i][0] - dl), min(.93, o[i][0] + dl)); v[1] = np.clip(v[1], max(.06, o[i][1] - dc), o[i][1] + dc)
        dhh = (v[2] - o[i][2] + 180) % 360 - 180; v[2] = (o[i][2] + max(-dh, min(dh, dhh))) % 360
        if np.any(np.abs(from_oklch(*v) - np.clip(from_oklch(*v), 0, 255)) > 0.5): continue  # stay in sRGB
        trial = cur[:]; trial[i] = v; f = fit(trial)
        if f >= best: cur, best = trial, f
    return mk(cur)

if __name__ == '__main__':
    res = {'today': summary(TODAY, 'Today (AudioLab theme)'), 'okabe': summary(OKABE, 'Okabe-Ito as published'),
           'okabe_dark': summary(OKABE_D, 'Okabe-Ito lifted for a dark ground')}
    tuned = tune(TODAY); res['tuned'] = summary(tuned, 'Today tuned (hues within 16°, lightness within 0.09)')
    res['names'] = NAMES
    for k, v in res.items():
        if k == 'names': continue
        print(f"== {v['name']}: {v['pal']}  worst edge {v['worst_edge']}, worst body {v['worst_body']}")
        for kk, b in v['by'].items(): print(f"   {kk:14s} min {b['min']:5.1f} {b['pair']}  under 10: {len(b['under10'])}")
    json.dump(res, open(f'{OUT}/cvd.json', 'w'), indent=1)
    if SHOT:
        from PIL import Image
        im = np.asarray(Image.open(SHOT).convert('RGB')).astype(float)
        base = os.path.splitext(os.path.basename(SHOT))[0]
        for k in M:
            s = enc(lin(im) @ M[k].T)
            Image.fromarray(s.astype(np.uint8)).save(f'{OUT}/{base}-{k}.png')
