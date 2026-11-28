"""AudioLab app icon, round 6 (task IC10): the small icons, for 32 px and below.

Each design is its own drawing for 16, 20, 24 and 32 pt, at 1x and 2x, on the full tile (Windows .ico, favicon) and on
the Apple grid (the icns small slots). Nothing is the big icon scaled down. The same 3D renderer as the big icons
(r6.py) paints them, so the nucleus is always a lit sphere with a glow (never a flat disc) and the lines are tapered
tubes, but every measure here is in pixels of the size it is drawn for:

  - nucleus and electron (Earth and Moon) have whole-pixel diameters; an odd diameter is centred on a pixel centre,
    an even one on a pixel corner, so their edges are sharp;
  - line widths are given per size in pixels, near side and far side (the taper is about 2 to 1 at 32, gentle at 16,
    because a line thinner than a pixel turns grey);
  - a ring's or field line's outermost point is moved onto the pixel grid;
  - the 2x picture of a point size is that size's drawing with twice the pixels (not the next size's drawing), its
    lines 1.75 times wider instead of twice.

KS6..KS8 : the K family (the atom of K6).   ES5..ES7 : the Earth and Moon family (E6).
small(id, pid, pt, scale=1, frame='full'|'mac') -> PIL RGBA image of pt * scale pixels
"""
import numpy as np
from r6 import Canvas, hexc, mix, norm, smooth, lit_ball, planet, tube_mat, tile_mask, edge_dist, blur, to_img, F
from designs6 import PAL, LIGHT, SUN, WHITE, rot, glow_alpha, dipole_line

PTS = (16, 20, 24, 32)
INSET = {16: 1, 20: 2, 24: 2, 32: 3}        # the Apple grid margin in pixels at 1x


def fit_c(v, d):
    """centre for a disc of whole-pixel diameter d near v: on a pixel centre if d is odd, on a corner if even"""
    return (np.floor(v) + 0.5) if d % 2 else float(np.round(v))


# per design, per point size. Lengths in pixels of the full 1x tile; on the Apple grid they shrink with the tile and
# are fitted again. c: nucleus centre (share of the tile); nd, ed: nucleus and electron diameters; w: line width near
# and far side; R: ring radius (atom) or the field lines' reach L (field), in pixels.
KS = {
    'KS6': dict(fam='K', name='The crop, tapered', star=True, kind='atom',
                note='S1\'s crop (the atom zoomed into its top right, the electron in the corner) with the rings of K6: '
                     'thicker and brighter where they come toward you, the nucleus lit with a glow.',
                c=(0.40, 0.61), rot=-6, zoom={16: 0.50, 20: 0.50, 24: 0.49, 32: 0.48},
                nd={16: 5, 20: 6, 24: 7, 32: 9}, ed={16: 3, 20: 3, 24: 4, 32: 5},
                w={16: (1.35, 1.0), 20: (1.6, 1.0), 24: (1.8, 1.0), 32: (2.2, 1.05)}, far={16: 0.82, 20: 0.74, 24: 0.66, 32: 0.6},
                glow=(1.9, 0.34), el=(0, 6)),
    'KS7': dict(fam='K', name='The whole atom', kind='atom',
                note='The whole atom in the middle, nothing cut: two rings at 16 and 20 px, three from 24. The bigger '
                     'lit nucleus carries it. The clearest link to the big icon, the least detail.',
                c=(0.47, 0.53), rot=0, zoom={16: 0.40, 20: 0.40, 24: 0.39, 32: 0.39},
                nd={16: 5, 20: 6, 24: 7, 32: 9}, ed={16: 3, 20: 3, 24: 4, 32: 5},
                w={16: (1.3, 1.0), 20: (1.5, 1.0), 24: (1.7, 1.0), 32: (2.1, 1.05)}, far={16: 0.84, 20: 0.76, 24: 0.68, 32: 0.62},
                rings={16: (0, 1), 20: (0, 1), 24: (0, 1, 2), 32: (0, 1, 2)}, glow=(1.9, 0.36), el=(0, 4)),
    'KS8': dict(fam='K', name='Closer, glowing', kind='atom',
                note='Further in: a big glowing nucleus low left, two heavy ring arcs sweeping past it out of the tile, '
                     'the electron lit with its own glow, a light top edge from 24 px.',
                c=(0.37, 0.63), rot=-8, zoom={16: 0.60, 20: 0.60, 24: 0.58, 32: 0.57},
                nd={16: 6, 20: 7, 24: 9, 32: 11}, ed={16: 3, 20: 4, 24: 4, 32: 6},
                w={16: (1.5, 1.05), 20: (1.75, 1.05), 24: (2.0, 1.1), 32: (2.5, 1.15)}, far={16: 0.84, 20: 0.76, 24: 0.68, 32: 0.62},
                glow=(2.3, 0.48), el=(0, 6), elGlow=True, edge=True),
    'ES5': dict(fam='E', name='MS2, lit and tapered', star=True, kind='field',
                note='Your MS2 (the zoom, the lit one), redrawn: the Earth low left, lit, with a glow; the field tilted 24 '
                     'degrees; two white lines, the outer one running out of the tile; the Moon on the inner line. The '
                     'lines are tubes now: thick toward you on the right, thin on the far side.',
                c=(0.35, 0.64), tilt=24, phi=24,
                nd={16: 6, 20: 7, 24: 9, 32: 11}, ed={16: 3, 20: 4, 24: 4, 32: 5},
                Ls={16: (8.4, 16.0), 20: (10.4, 19.6), 24: (12.2, 23.4), 32: (15.8, 30.2)},
                w={16: (1.35, 1.0), 20: (1.55, 1.0), 24: (1.8, 1.0), 32: (2.2, 1.05)}, far={16: 0.85, 20: 0.78, 24: 0.7, 32: 0.62},
                glow=(2.0, 0.4), moon=(0, 55), edge=True),
    'ES6': dict(fam='E', name='A small M5c', kind='field',
                note='The whole of M5c, simplified as it shrinks: the glowing core in the middle, the half orbits left and '
                     'right, the Moon on the right. One orbit pair at 16, two at 20 and 24, three at 32.',
                c=(0.47, 0.53), tilt=10, phi=13,
                nd={16: 5, 20: 6, 24: 7, 32: 9}, ed={16: 3, 20: 3, 24: 4, 32: 5},
                Ls={16: (6.8,), 20: (5.9, 9.0), 24: (7.0, 10.8), 32: (7.2, 10.8, 14.6)},
                w={16: (1.3, 1.05), 20: (1.4, 1.05), 24: (1.6, 1.1), 32: (1.85, 1.15)}, far={16: 0.95, 20: 0.92, 24: 0.86, 32: 0.8},
                glow=(2.4, 0.5), moon=(-1, 62), elGlow=True),
    'ES7': dict(fam='E', name='Day and night', kind='field',
                note='ES5 lit by the Sun from the left, as E6b and E6d: the Earth with a day and a night side, the Moon '
                     'showing the same phase. At 16 px the night side is two or three darker pixels.',
                c=(0.36, 0.63), tilt=24, phi=24, sun=True,
                nd={16: 6, 20: 7, 24: 9, 32: 11}, ed={16: 3, 20: 4, 24: 5, 32: 6},
                Ls={16: (8.6, 16.2), 20: (10.6, 19.8), 24: (12.4, 23.6), 32: (16.0, 30.4)},
                w={16: (1.35, 1.0), 20: (1.55, 1.0), 24: (1.8, 1.0), 32: (2.2, 1.05)}, far={16: 0.85, 20: 0.78, 24: 0.7, 32: 0.62},
                glow=(1.9, 0.34), moon=(0, 55), edge=True),
}
ORDER = ['KS6', 'KS7', 'KS8', 'ES5', 'ES6', 'ES7']


def small_rgba(id, pid, pt, scale=1, frame='full', ss=None, want_fg=False):
    q = KS[id]
    P = PAL[pid]
    px = pt * scale
    ins = INSET[pt] if frame == 'mac' else 0
    T = pt - 2 * ins                         # the tile in 1x pixels
    ss = ss or (12 if px <= 32 else 8)
    cv = Canvas(px, ss, (ins * scale, ins * scale, T * scale))
    U = 1024.0 / T                           # design units per 1x pixel
    f = T / float(pt)                        # the Apple grid shrinks the drawing
    lw = 1.0 if scale == 1 else 0.875        # 2x: lines 1.75 times wider, not twice
    nuc, el, det, sh_ = hexc(P['nuc']), hexc(P['el']), hexc(P['det']), hexc(P['shade'])
    lit, shd = hexc(P['ring_lit']), mix(hexc(P['ring_lit']), hexc(P['ring_sh']), 0.6)
    nd = max(4, int(round(q['nd'][pt] * f))); ed = max(2, int(round(q['ed'][pt] * f)))
    if scale == 2:
        nd2, ed2 = nd * 2, ed * 2
    cx = fit_c(q['c'][0] * T, nd); cy = fit_c(q['c'][1] * T, nd)
    c = np.array([cx * U, cy * U, 0.0])
    nr = nd / 2.0 * U; er = ed / 2.0 * U
    wn, wf = q['w'][pt]
    wn = max(1.0, wn * (0.5 + 0.5 * f)) * lw; wf = max(0.9, wf) * lw
    wb = (wn + wf) / 2 * U; kt = (wn - wf) / (wn + wf)
    far = q['far'][pt]
    sun = SUN if q.get('sun') else None
    Lt = sun if sun else LIGHT
    mat = tube_mat(lit, shd, Lt, wrap=0.8)
    gR, gop = q['glow']
    if not P['dark']:
        gop *= 0.5
    gcol = mix(nuc, WHITE, 0.1) if P['glow'] else nuc
    glow = (c[0], c[1], nr, nr * gR, gcol, gop)

    def gfn(X, Y):
        sx, sy, _, _ = cv.project(c)
        d = np.hypot(X - sx, Y - sy) / cv.k
        return gcol, glow_alpha(np.maximum(d, nr), nr, nr * gR, gop).astype(F)
    cv.glow = gfn; cv.glow_z = 0.0
    egl = None

    if q['kind'] == 'atom':
        R = q['zoom'][pt] * T
        # the ring's long axis ends on the pixel grid: R to the nearest half pixel beyond the nucleus centre
        R = np.round(R * 2) / 2.0
        ci = 150.0 / 360.0; si = np.sqrt(1 - ci * ci)
        cv.cam = (c[0], c[1], 5.0 * R * U)
        zmax = R * U * si
        tt = np.linspace(0, 2 * np.pi, 241)
        rings = []
        for k, ang in enumerate((-30, 30, 90)):
            a = np.radians(ang + q.get('rot', 0))
            u = np.array([np.cos(a), np.sin(a), 0.0]); v = np.array([-np.sin(a) * ci, np.cos(a) * ci, si])
            Rk = R * U * (1 + (-0.03, 0.0, 0.03)[k])
            rings.append((k, c + Rk * (np.outer(np.cos(tt), u) + np.outer(np.sin(tt), v)), u, v, Rk))
        ek, et = q['el']
        _, _, u, v, Rk = rings[ek]
        ep = c + Rk * (np.cos(np.radians(et)) * u + np.sin(np.radians(et)) * v)
        # the electron on the pixel grid too
        epx = fit_c(ep[0] / U, ed); epy = fit_c(ep[1] / U, ed)
        ep = np.array([epx * U, epy * U, ep[2]])
        cv.knock(ep, er + 0.8 * U, zmargin=1e9)
        for k, pts, u, v, Rk in rings:
            if k not in q.get('rings', {}).get(pt, (0, 1, 2)):
                continue
            zn = pts[:, 2] / zmax
            cv.tube(pts, wb / 2, mat, alpha=mix(far, 1.0, smooth(-0.85, 0.3, zn)), taper=lambda z: 1.0 + kt * np.clip(z / zmax, -1, 1))
    else:
        M = rot('z', q['tilt']) @ rot('x', -8.0)
        phi = q['phi']
        Ls = [v * f for v in q['Ls'][pt]]
        cv.cam = (c[0], c[1], 6.0 * Ls[-1] * U)
        zref = Ls[-1] * U * np.sin(np.radians(phi))
        mi, mth = q['moon']
        r = Ls[mi] * U * np.sin(np.radians(mth)) ** 2
        ph = np.radians(phi); th = np.radians(mth)
        ep = M @ np.array([r * np.sin(th) * np.cos(ph), -r * np.cos(th), r * np.sin(th) * np.sin(ph)]) + c
        # the Moon moves out along its line until a pixel of ground shows between it and the Earth
        for _ in range(40):
            if np.hypot(ep[0] - c[0], ep[1] - c[1]) >= nr + er + 1.0 * U:
                break
            th += np.radians(2.0)
            r = Ls[mi] * U * np.sin(th) ** 2
            ep = M @ np.array([r * np.sin(th) * np.cos(ph), -r * np.cos(th), r * np.sin(th) * np.sin(ph)]) + c
        epx = fit_c(ep[0] / U, ed); epy = fit_c(ep[1] / U, ed)
        ep = np.array([epx * U, epy * U, ep[2]])
        cv.knock(ep, er + 0.8 * U, zmargin=1e9)
        for i, Lq in enumerate(Ls):
            for ph_ in (phi, phi + 180.0):
                pts, _ = dipole_line(Lq * U, ph_, nr * 0.9, n=160, M=M, c=c)
                cv.tube(pts, wb / 2, mat, alpha=mix(far, 1.0, smooth(-0.9, 0.25, pts[:, 2] / zref)),
                        taper=lambda z: 1.0 + kt * np.clip(z / zref, -1, 1))
    if sun:
        cv.sphere(c, nr, planet(nuc, mix(nuc, sh_, 0.5), sun, hi=0.45, term=0.2), persp=False)
        cv.sphere(ep, er, planet(el, mix(el, sh_, 0.52), sun, hi=0.4, term=0.25), persp=False, noknock=True)
    else:
        cv.sphere(c, nr, lit_ball(nuc, sh_, LIGHT, hi=0.62), persp=False)
        cv.sphere(ep, er, lit_ball(el, sh_, LIGHT, hi=0.5), persp=False, noknock=True)
    if q.get('elGlow') and pt >= 24:
        egl = (ep, er, er * 2.2, el, 0.34 if P['dark'] else 0.16)

    X, Y = cv.grid()
    bg0, bg1 = hexc(P['bg'][0]), hexc(P['bg'][1])
    t = np.clip((0.35 * X / 1024 + Y / 1024) / (0.35 * 0.35 + 1.0), 0, 1)[..., None]
    img = mix(bg0, bg1, t)
    if P['glow']:
        d = np.hypot(X - 512, Y - 512) / 1024
        img = mix(img, hexc(P['glow']), (0.2 * np.clip(1 - d / 0.55, 0, 1))[..., None])
    ga = glow_alpha(np.maximum(np.hypot(X - c[0], Y - c[1]), nr), nr, nr * gR, gop)
    img = mix(img, gcol, ga[..., None])
    if egl:
        ga = glow_alpha(np.maximum(np.hypot(X - ep[0], Y - ep[1]), er), er, egl[2], egl[4])
        img = mix(img, el, ga[..., None])
    fg = cv.down()
    img = img * (1 - fg[..., 3:4]) + fg[..., :3]
    # the rim: a hairline in the detail colour so a dark tile holds on a dark ground (and paper on a light one)
    ed_ = edge_dist(X, Y) / U                 # in 1x pixels
    rim = np.clip(1 - ed_ / (0.9 if pt < 24 else 1.0), 0, 1)
    img = mix(img, hexc(P['det']), (rim * (0.5 if P['dark'] else 0.34))[..., None])
    if q.get('edge') and pt >= 24:
        a = np.clip(1 - ed_ / 1.0, 0, 1) * np.clip(1 - (Y / 1024) / 0.3, 0, 1) * 0.55
        img = img + (1 - img) * a[..., None]
    m = tile_mask(cv, 8)
    if want_fg:
        return img, m, fg[..., 3]
    return img, m


def small(id, pid, pt, scale=1, frame='full'):
    rgb, al = small_rgba(id, pid, pt, scale, frame)
    return to_img(rgb, al, dither=False)


def template(id, pt, scale=1):
    """the mark alone in one colour (black, with its coverage as alpha): what a menu bar or tray item would use"""
    rgb, al, fg = small_rgba(id, 'P2', pt, scale, 'full', want_fg=True)
    return to_img(np.zeros(fg.shape + (3,), dtype=F), np.clip(fg * 1.15, 0, 1), dither=False)


if __name__ == '__main__':
    import sys
    from PIL import Image
    out = sys.argv[1]
    pid = sys.argv[2] if len(sys.argv) > 2 else 'P2'
    frame = sys.argv[3] if len(sys.argv) > 3 else 'full'
    Z = 6
    rows = ORDER
    W = Image.new('RGB', (1560, len(rows) * (32 * Z + 16) + 10), (38, 40, 48))
    for r, id in enumerate(rows):
        y = 10 + r * (32 * Z + 16); x = 10
        for pt in PTS:
            im = small(id, pid, pt, 1, frame).resize((pt * Z, pt * Z), Image.NEAREST)
            W.paste(im, (x, y), im); x += pt * Z + 14
        for pt in PTS:
            im = small(id, pid, pt, 2, frame).resize((pt * Z, pt * Z), Image.NEAREST)
            W.paste(im, (x, y), im); x += pt * Z + 14
        for pt in PTS:
            im = small(id, pid, pt, 1, frame)
            W.paste(im, (x, y), im)
            im2 = small(id, pid, pt, 2, frame)
            W.paste(im2, (x, y + 40), im2); x += 2 * pt + 6
    W.save(out)
