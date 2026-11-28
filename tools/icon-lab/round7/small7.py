"""AudioLab app icon, round 7 (task IC11): the small icons S1..S4, for 32 px and below.

The KS8 direction (the user, 28 Nov): zoomed in, the big circle (the Earth) in the bottom left corner, the blue circle
(the Moon) in the top right corner, the glow visible. Each size is its own drawing, measured in pixels:

  - the Earth and the Moon have whole-pixel diameters; an even diameter is centred on a pixel corner, an odd one on a
    pixel centre, so their edges are sharp; the Earth keeps the same margin to the left and bottom edges
  - line widths are given per size in pixels (1.5 at 16, 2.5 at 32); nothing is thinner than a pixel
  - a pixel of ground stays free round the Moon wherever a line or a belt meets it
  - 2x is its point size's drawing on twice the pixels (not the next size's drawing), lines 1.75 times wider
  - on the Apple grid (icns) the tile is smaller (14 px at 16 pt), so everything is measured and fitted again

small(id, pid, pt, scale=1, frame='full'|'mac') -> PIL RGBA of pt * scale pixels
"""
import numpy as np
from r7 import hexc, mix, norm, smooth, planet, squircle_f, to_img, F
from designs7 import PAL, LIGHT, WHITE

PTS = (16, 20, 24, 32)
INSET = {16: 1, 20: 2, 24: 2, 32: 3}
# per point size, pixels of the full 1x tile: Earth diameter and centre, Moon diameter and centre, line width
BASE = {16: dict(ed=8, ec=(5, 11), md=4, mc=(12, 4), lw=1.5),
        20: dict(ed=10, ec=(6, 14), md=5, mc=(15.5, 4.5), lw=1.75),
        24: dict(ed=12, ec=(8, 16), md=6, mc=(18, 6), lw=2.0),
        32: dict(ed=16, ec=(10, 22), md=8, mc=(25, 7), lw=2.5)}
SMALL = {
    'S1': dict(name='Field loops', line='Field loops reach for the Moon', star=True),
    'S2': dict(name='Belt', line='A belt between Earth and Moon', star=True),
    'S3': dict(name='Orbit', line='The orbit passes behind and in front'),
    'S4': dict(name='Two bodies', line='Only Earth, Moon and glow'),
}
ORDER = ['S1', 'S2', 'S3', 'S4']


def fit_c(v, d):
    return (np.floor(v) + 0.5) if d % 2 else float(np.floor(v + 0.5))


def seg_dist(X, Y, pts):
    """distance from every sample to a polyline, and the place along it (0..1) of the nearest point"""
    D = np.full(X.shape, 1e9, dtype=F); U = np.zeros(X.shape, dtype=F)
    n = len(pts)
    for i in range(n - 1):
        ax, ay = pts[i]; bx, by = pts[i + 1]
        dx, dy = bx - ax, by - ay
        L2 = dx * dx + dy * dy
        if L2 < 1e-12:
            continue
        t = np.clip(((X - ax) * dx + (Y - ay) * dy) / L2, 0, 1)
        d = np.hypot(X - (ax + t * dx), Y - (ay + t * dy))
        m = d < D
        D[m] = d[m]; U[m] = ((i + t) / (n - 1))[m]
    return D, U


def small_rgba(id, pid, pt, scale=1, frame='full', ss=None):
    P = PAL[pid]; b = BASE[pt]
    px = pt * scale
    ss = ss or (12 if px <= 32 else 8)
    ins = INSET[pt] if frame == 'mac' else 0
    T = pt - 2 * ins; f = T / float(pt)
    N = px * ss
    v = (np.arange(N, dtype=F) + 0.5) / (ss * scale)           # sample centres in 1x pixels
    X, Y = np.meshgrid(v, v)
    ed = max(5, int(round(b['ed'] * f))); md = max(3, int(round(b['md'] * f)))
    E = np.array([ins + fit_c(b['ec'][0] * f, ed), ins + fit_c(b['ec'][1] * f, ed)])
    M = np.array([ins + fit_c(b['mc'][0] * f, md), ins + fit_c(b['mc'][1] * f, md)])
    er, mr = ed / 2.0, md / 2.0
    lw = max(1.0, b['lw'] * (0.5 + 0.5 * f)) * (1.0 if scale == 1 else 0.875)
    q = norm(np.append(M - E, 0))[:2]; perp = np.array([-q[1], q[0]])     # toward the Moon; and to its lower right
    if perp[1] < 0:
        perp = -perp
    dEM = float(np.hypot(*(M - E)))
    dark = P['dark']
    earth, moon = hexc(P['earth']), hexc(P['moon'])
    line = hexc(P['line']); bg0, bg1 = hexc(P['bg'][0]), hexc(P['bg'][1])
    beltc = hexc('#7AA8FF' if dark else '#44589C'); beltl = hexc('#C2D6FF' if dark else '#1B2A66')
    innc = hexc('#FFB648' if dark else '#D57A22')

    # the ground
    tx, ty = (X - ins) / T, (Y - ins) / T
    t = np.clip((0.35 * tx + ty) / (0.35 * 0.35 + 1.0), 0, 1)[..., None]
    img = mix(bg0, bg1, t).astype(F)
    if P['cglow']:
        d = np.hypot(X - E[0], Y - E[1]) / T
        img = mix(img, hexc(P['cglow']), (0.16 * np.clip(1 - d / 0.8, 0, 1))[..., None])

    def over(rgb, a):
        nonlocal img
        img = img + (rgb - img) * np.clip(a, 0, 1)[..., None]

    def cov(d):                         # coverage of a shape from its signed distance (inside negative), in 1x pixels
        return (d < 0).astype(F)

    def glow(c, r0, r1, rgb, op):
        d = np.maximum(np.hypot(X - c[0], Y - c[1]), r0)
        tt = np.clip((d - r0) / (r1 - r0), 0, 1)
        over(rgb, op * (1 - tt) ** 2.0)

    gk = 1.0 if dark else 0.45
    strong = id == 'S4'
    glow(E, er, er * (2.5 if strong else 2.25), mix(earth, WHITE, 0.12), (0.62 if strong else 0.52) * gk)
    glow(M, mr, mr * (2.6 if strong else 2.3), moon, (0.55 if strong else 0.45) * gk)

    dM = np.hypot(X - M[0], Y - M[1])
    dE = np.hypot(X - E[0], Y - E[1])
    clear_m = dM > mr + (0.9 if pt < 24 else 1.1)              # a pixel of ground round the Moon
    front = []                                                  # things drawn over the Earth

    def stroke(pts, w, rgb, a=1.0, mask=None, lay=None):
        D, U = seg_dist(X, Y, pts)
        c = (D < w / 2).astype(F) * a
        if mask is not None:
            c = c * mask
        if lay is None:
            over(rgb, c)
        else:
            lay.append((rgb, c))

    def loop(Lr, n=90):
        l0 = np.arccos(np.sqrt(min(1.0, (er + 0.9) / Lr)))
        lam = np.linspace(-l0, l0, n)
        r = Lr * np.cos(lam) ** 2
        return E + np.outer(r * np.cos(lam), q) + np.outer(r * np.sin(lam), perp)

    if id == 'S1':
        stroke(loop(dEM), lw * (1.0 if pt < 32 else 1.08), line, mask=clear_m)
    elif id == 'S2':
        vx, vy = X - E[0], Y - E[1]
        r = np.maximum(dE, 1e-3)
        cl = (vx * q[0] + vy * q[1]) / r
        c2 = cl * cl
        Lv = r / np.maximum(c2, 1e-3)
        lt = ((vx * LIGHT[0] + vy * LIGHT[1]) / dEM)

        def crescent(La, Lb, lat, c0, c1):
            m = (cl > 0) & (Lv > La) & (Lv < Lb) & (c2 > np.cos(np.radians(lat)) ** 2) & clear_m
            col = mix(c0, c1, np.clip(0.45 + 0.9 * lt, 0, 1)[..., None])
            over(col, m.astype(F))
        Lb = dEM - mr - (0.9 if pt < 24 else 1.1)
        th = {16: 2.0, 20: 2.5, 24: 3.0, 32: 3.6}[pt] * (0.5 + 0.5 * f)
        if pt >= 32:
            crescent(er + 1.5, er + 3.5, 50, innc, mix(innc, WHITE, 0.45) if dark else innc)
        crescent(Lb - th, Lb, 60, beltc, beltl)
    elif id == 'S3':
        th = np.radians(np.linspace(0, 360, 181))
        a_, b_ = dEM, dEM * 0.30
        ell = E + np.outer(a_ * np.cos(th), q) + np.outer(b_ * np.sin(th), perp)
        orb = hexc(P['orbit'])
        stroke(ell[90:], max(1.0, lw * 0.72), mix(orb, bg0, 0.42), mask=clear_m)                 # the far half
        stroke(ell[:91], lw, mix(orb, WHITE, 0.25) if dark else orb, mask=clear_m, lay=front)   # the near half

    # the Earth and the Moon: lit balls
    def ball(c, rr, col, night, hi):
        nx = (X - c[0]) / rr; ny = (Y - c[1]) / rr
        d2 = nx * nx + ny * ny
        nz = np.sqrt(np.clip(1 - d2, 0, 1))
        sh = planet(col, night, LIGHT, hi=hi, amb=0.42, limb=0.22, term=0.2)
        over(sh(nx, ny, nz), (d2 < 1).astype(F))
    ball(E, er, earth, hexc(P['night']), 0.5 if dark else 0.3)
    for rgb, c in front:
        over(rgb, c)
    ball(M, mr, moon, hexc(P['mnight']), 0.5 if dark else 0.3)

    # the tile: a hairline rim, from 24 px a light top edge; the shape
    sq = squircle_f(tx * 1024, ty * 1024)
    edge_px = (1 - sq) * T / 2.0                                 # about the distance from the edge, in 1x pixels
    rim = (edge_px < 1.0 / scale) & (sq < 1)
    over(hexc('#7AA8FF') if dark else hexc(P['line']), rim.astype(F) * (0.34 if dark else 0.22))
    if pt >= 24:
        over(WHITE, rim.astype(F) * np.clip(1 - ty / 0.3, 0, 1) * 0.35)
    m = (sq < 1).astype(F)
    rgb = img.reshape(px, ss, px, ss, 3).mean(axis=(1, 3))
    al = m.reshape(px, ss, px, ss).mean(axis=(1, 3))
    return rgb, al


def small(id, pid, pt, scale=1, frame='full'):
    rgb, al = small_rgba(id, pid, pt, scale, frame)
    return to_img(rgb, al, dither=False)


if __name__ == '__main__':
    import sys
    from PIL import Image
    out = sys.argv[1]; pid = sys.argv[2] if len(sys.argv) > 2 else 'P2'
    Z = 6
    W = Image.new('RGB', (4 * (32 * Z + 12) * 2 + 20, len(ORDER) * (32 * Z + 50)), (58, 60, 68))
    for r, i in enumerate(ORDER):
        x = 6
        for sc in (1, 2):
            for pt in PTS:
                im = small(i, pid, pt, sc)
                z = Z if sc == 1 else Z // 2
                W.paste(im.resize((pt * sc * z, pt * sc * z), Image.NEAREST), (x, r * (32 * Z + 50) + 4), im.resize((pt * sc * z, pt * sc * z), Image.NEAREST))
                W.paste(im, (x, r * (32 * Z + 50) + 32 * Z + 10), im)
                x += 32 * Z + 12
    W.save(out)
