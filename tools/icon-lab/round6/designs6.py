"""AudioLab app icon, round 6 (task IC10): the big designs.

K6a..K6d : K5a (soft glass) with its three rings as real tubes in space (the user, 28 Nov 01:13: tapered, never flat,
           "so it looks like it's in 3D anatomically correct").
E6a..E6e : M5d (field to the edge) as the Earth (yellow) and the Moon (blue) (the user, 01:14), its field lines true
           dipole lines in space, tapered by depth.
Palettes P2 Orbit night and P8 Chart paper (and P8N, P8's Dark entry) are round 2's, unchanged.

render(id, pid, px, frame='full'|'mac', style='default'|'dark') -> PIL image (RGBA)
"""
import numpy as np
from scipy import ndimage
from r6 import (Canvas, hexc, mix, norm, smooth, lit_ball, planet, tube_mat, tile_mask, edge_dist, squircle_f, blur,
                to_img, F)

PAL = {
    'P2': dict(id='P2', name='Orbit night', bg=('#132044', '#070910'), ring='#EAF1FF', nuc='#FFC43C', el='#4CC9F0',
               det='#6096FF', glow='#6096FF', dark=True, ring_lit='#F7FAFF', ring_sh='#9DAFD8', far=0.50, shade='#070910'),
    'P8': dict(id='P8', name='Chart paper', bg=('#F7F3EA', '#E4DCCA'), ring='#1B2340', nuc='#C8610A', el='#2F6BFF',
               det='#1B2340', glow=None, dark=False, ring_lit='#414E7A', ring_sh='#141A33', far=0.46, shade='#1B2340'),
    'P8N': dict(id='P8N', name='Chart paper, night', bg=('#1E2742', '#0C1020'), ring='#F3EEE2', nuc='#F08A2C',
                el='#6E9BFF', det='#D9CDB4', glow=None, dark=True, ring_lit='#FBF7EE', ring_sh='#A9A592', far=0.50, shade='#0C1020'),
}
WHITE = np.ones(3, dtype=F)
BOOST = [1.0]                    # line weight at 100 to 200 px (the Dock): everything drawn, lines a third heavier
LIGHT = (-0.45, -0.60, 0.66)     # K5a's light: from the top left, in front


def lod_for(px):
    return 3 if px >= 128 else 2 if px >= 48 else 1


def rot(ax, deg):
    a = np.radians(deg); c, s = np.cos(a), np.sin(a)
    if ax == 'x':
        return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
    if ax == 'y':
        return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


# ---------- the flat field behind the atom (K family): J3's dipole lines, as in K5a ----------
def fline2d(c, Leq, tilt, Rs, side, n=160, win=0.0):
    t0 = np.arcsin(min(1.0, np.sqrt(Rs / Leq)))
    if win:
        t0 = max(t0, np.radians(win))
    th = np.linspace(t0, np.pi - t0, n)
    r = Leq * np.sin(th) ** 2
    x = side * r * np.sin(th); y = -r * np.cos(th)
    a = np.radians(tilt)
    return np.stack([c[0] + x * np.cos(a) - y * np.sin(a), c[1] + x * np.sin(a) + y * np.cos(a), np.zeros_like(x)], axis=1)


class Scene:
    """what a design hands to the compositor"""
    def __init__(self):
        self.glow = None        # (cx, cy, r0, r1, rgb, op)
        self.shadow = 0.6
        self.sheen = True
        self.knock_px = 12.0    # gap cut in the flat field round the 3D parts (design units); 0 = none
        self.extra_glows = []


def k_scene(cv, cvb, P, L, p):
    S = Scene()
    c = np.array([512.0, 512.0, 0.0]); s = p.get('s', 0.86)
    R = 360.0 * s
    ci = 150.0 / 360.0; si = np.sqrt(1 - ci * ci)
    nuc, el, det, bg1 = hexc(P['nuc']), hexc(P['el']), hexc(P['det']), hexc(P['shade'])
    lit, shd = hexc(P['ring_lit']), hexc(P['ring_sh'])
    nr = 80.0 * s * (1 if L == 3 else 1.12)
    er = 46.0 * s * (1 if L == 3 else 1.15)
    w = p.get('w', 22.5) * (BOOST[0] if L == 3 else p.get('w2k', 1.62))
    kt = p.get('kt', 0.5) * (1 if L == 3 else 0.86)
    M = p.get('M', np.eye(3))
    D = p.get('cam', 1500.0)
    cv.cam = (512.0, 512.0, D)
    zmax = R * si

    # --- the flat field (behind everything) ---
    tilt = p.get('tilt', 10)
    fc = det
    Rs = nr + (24 if L == 3 else 30)
    if L == 3:
        Ls = [150, 212, 300, 430, 620, 900]; sw = 4.4 * BOOST[0]; op = 0.59
    else:
        Ls = [244, 430, 682]; sw = 11.0; op = 0.64
    for Leq in Ls:
        for side in (1, -1):
            pts = fline2d(c, Leq, tilt, Rs, side)
            d = np.hypot(pts[:, 0] - c[0], pts[:, 1] - c[1])
            a = op * (0.3 + 0.7 * smooth(Rs, Rs + 60, d))
            if Leq > 262 * s / 0.86:
                a = a * smooth(322, 392, d)
                cvb.flat(pts, sw, fc, a)
            else:
                # the inner lines run on under the rings, unbroken (far behind everything in the 3D layer)
                cv.flat(pts, sw, fc, a * (0.85 if L == 3 else 1.0), zoff=-5000.0)
    if L == 3:
        a = np.radians(tilt); ax = np.array([np.sin(a), -np.cos(a), 0.0])
        for sg in (1, -1):
            cvb.flat(np.array([c + sg * ax * (nr + 12), c + sg * ax * (nr + 62)]), 4.4, fc, 0.6)
        # a few trapped particles on the outer lines (K5a's, placed by hand)
        for (Leq, side, thd, colr) in [(430, 1, 104, el), (430, -1, 118, nuc), (620, -1, 60, el), (620, 1, 121, nuc),
                                       (900, 1, 114, el), (900, -1, 73, nuc), (900, -1, 112, el)]:
            th = np.radians(thd); r = Leq * np.sin(th) ** 2
            x = side * r * np.sin(th); y = -r * np.cos(th)
            px_, py_ = c[0] + x * np.cos(a) - y * np.sin(a), c[1] + x * np.sin(a) + y * np.cos(a)
            cvb.sphere((px_, py_, 0), 7.5, lambda nx, ny, nz, cc=colr: np.broadcast_to(cc, nx.shape + (3,)), alpha=0.92)

    # --- the nucleus glow, laid over whatever is behind the nucleus ---
    gcol = mix(nuc, WHITE, 0.1) if P['glow'] else nuc
    gop = (0.36 if P['dark'] else 0.2) * p.get('glowOp', 1.0)
    S.glow = (c[0], c[1], nr, nr * (p.get('glowR', 3.2) if L == 3 else 2.4), gcol, gop)
    set_glow(cv, S.glow, 0.0)

    # --- rings ---
    far = P['far'] if L == 3 else min(0.78, P['far'] + 0.2)
    mat = tube_mat(lit, shd, LIGHT, spec=p.get('spec', 0.0), wrap=p.get('wrap', 0.5),
                   edge=p.get('edge', 0.0), edgecol=shd)
    taper = lambda z: 1.0 + kt * np.clip(z / zmax, -1.2, 1.2)
    tt = np.linspace(0, 2 * np.pi, 361)
    rings = []
    for k, ang in enumerate(p.get('angs', (-30, 30, 90))):
        a = np.radians(ang)
        sg = p.get('sg', (1, 1, 1))[k]
        u = np.array([np.cos(a), np.sin(a), 0.0]); v = np.array([-np.sin(a) * ci, np.cos(a) * ci, sg * si])
        if 'planes' in p:
            u, v = p['planes'][k]
        u = M @ u; v = M @ v
        Rk = R * (1 + p.get('dR', (0, 0, 0))[k])
        pts = c + Rk * (np.outer(np.cos(tt), u) + np.outer(np.sin(tt), v))
        rings.append((pts, u, v, Rk))
    # the electron: on ring e_ring at angle e_t (degrees from the ring's u axis)
    ek, et = p.get('el', (0, 0))
    pts, u, v, Rk = rings[ek]
    ep = c + Rk * (np.cos(np.radians(et)) * u + np.sin(np.radians(et)) * v)
    cv.knock(ep, er + (12 if L == 3 else 16) * s, zmargin=1e9)
    for pts, u, v, Rk in rings:
        zn = pts[:, 2] / zmax
        alpha = mix(far, 1.0, smooth(-0.85, 0.35, zn))
        cv.tube(pts, w / 2, mat, alpha=alpha, taper=taper)
    cv.sphere(c, nr, lit_ball(nuc, bg1, LIGHT, hi=0.58), persp=False)
    cv.sphere(ep, er, lit_ball(el, bg1, LIGHT, hi=0.55), noknock=True)
    if p.get('elGlow') and L >= 2:
        S.extra_glows.append((ep, er, er * 2.4, el, 0.3))
    S.shadow = p.get('shadow', 0.6)
    return S


def set_glow(cv, g, zplane):
    cx, cy, r0, r1, rgb, op = g
    sx, sy, _, _ = cv.project(np.array([cx, cy, 0.0]))
    k = cv.k

    def fn(X, Y):
        d = np.hypot(X - sx, Y - sy) / k
        return rgb, glow_alpha(d, r0, r1, op).astype(F)
    cv.glow = fn
    cv.glow_z = zplane


def glow_alpha(d, r0, r1, op):
    t = np.clip((d - r0) / (r1 - r0), 0, 1)
    return op * (1 - t) ** 2.2 * (d < r1)


DESIGNS = {}


def design(id, fam, name, short, note, scene, p, star=False):
    DESIGNS[id] = dict(id=id, fam=fam, name=name, short=short, note=note, scene=scene, p=p, star=star)


design('K6a', 'K', 'Woven tubes', 'three round tubes, woven like a pinwheel; near side thick and bright',
       'K5a with every ring a round tube in space. The three rings tip the same way round the centre, so each one '
       'passes over its neighbour on one side and under on the other. Thick and white where a ring comes toward you '
       '(34 px), thin and dim where it goes away (11 px), about 3 to 1 like the shipped logo.',
       k_scene, dict(dR=(-0.035, 0.0, 0.035), el=(0, 12)), star=True)
design('K6b', 'K', 'Seen from above', 'all three rings tip their lower half toward you',
       'One atom seen a little from above: the lower half of every ring is the near half, so the picture is heavy '
       'at the bottom and light at the top, like a real object lit on a table. The closest to round 5b\'s K5a-T2.',
       k_scene, dict(dR=(-0.035, 0.0, 0.035), sg=(1, 1, -1), el=(0, 14)))
design('K6c', 'K', 'Turned in space', 'the whole atom turned a little: the three ellipses differ',
       'The same three rings as one rigid object, turned 11 degrees to the side and 7 toward you. The ellipses are '
       'no longer three copies: one opens up, one closes. The most spatial, the least like the flat emblem.',
       k_scene, dict(dR=(-0.035, 0.0, 0.035), M=rot('y', -11) @ rot('x', 7), el=(0, 10), cam=1300.0))
design('K6d', 'K', 'Bold taper, lit', 'the strongest taper, tubes with a highlight',
       'The weight of the shipped Ocean Yellow rings: 48 px where near, 11 px where far (4 to 1), each tube with a '
       'soft highlight along its lit side and a darker edge, so it reads as a solid ring even at Dock size.',
       k_scene, dict(dR=(-0.045, 0.0, 0.045), w=30.0, kt=0.62, spec=0.75, edge=0.8, wrap=0.15, el=(0, 12)))


# ---------- the Earth and the Moon (E family): M5d's field as true dipole lines in space ----------
SUN = (-0.94, -0.10, 0.30)       # sunlight: from the left, a little toward the viewer (one direction for every body)


def dipole_line(L_, phi_deg, r_in, n=200, M=None, c=(512.0, 512.0, 0.0)):
    """one half of a dipole field line r = L sin^2(theta) in the meridian plane at longitude phi (0 = to the right,
    90 = toward the viewer), from where it leaves the sphere r_in round to where it enters it again."""
    t0 = np.arcsin(min(1.0, np.sqrt(r_in / L_)))
    th = np.linspace(t0, np.pi - t0, n)
    r = L_ * np.sin(th) ** 2
    ph = np.radians(phi_deg)
    p = np.stack([r * np.sin(th) * np.cos(ph), -r * np.cos(th), r * np.sin(th) * np.sin(ph)], axis=1)
    if M is not None:
        p = p @ M.T
    return p + np.asarray(c), th


def circle3(c, R, u, v, n=361, t0=0.0, t1=2 * np.pi):
    tt = np.linspace(t0, t1, n)
    return np.asarray(c) + R * (np.outer(np.cos(tt), u) + np.outer(np.sin(tt), v))


def dashed(cv, pts, width, rgb, alpha, dash, gap, taper=None):
    """a dashed flat line: pts resampled by arc length (design units)"""
    pts = np.asarray(pts, dtype=float)
    seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    s = np.concatenate([[0], np.cumsum(seg)])
    pos = 0.0
    while pos < s[-1]:
        a, b = pos, min(pos + dash, s[-1])
        ss = np.linspace(a, b, max(2, int((b - a) / 4) + 2))
        q = np.stack([np.interp(ss, s, pts[:, i]) for i in range(3)], axis=1)
        al = np.interp(ss, s, np.broadcast_to(alpha, (len(pts),))) if np.ndim(alpha) else alpha
        cv.flat(q, width, rgb, al, taper=taper)
        pos += dash + gap


def e_scene(cv, cvb, P, L, p):
    S = Scene(); S.knock_px = 0
    k = 0.86
    c = np.array(p.get('c', (512.0, 512.0)) + (0.0,))
    nuc, el, det, sh_ = hexc(P['nuc']), hexc(P['el']), hexc(P['det']), hexc(P['shade'])
    lit, shd = hexc(P['ring_lit']), hexc(P['ring_sh'])
    Re = p.get('Re', 88.0 * k) * (1 if L == 3 else 1.09)
    mr = p.get('moonR', 42.0 * k) * (1 if L == 3 else p.get('moon2', 1.13))
    lean, tip, phi0 = p.get('lean', 12.0), p.get('tip', 12.0), p.get('phi', 28.0)
    M = rot('z', lean) @ rot('x', -tip)            # magnetic frame -> picture: north leans right and tips toward you
    D = p.get('cam', 2400.0)
    cv.cam = (c[0], c[1], D)
    sun = p.get('sun')                              # None: K5a's soft light from the top left
    Lt = sun if sun else LIGHT
    if L == 3:
        bold = [v * k for v in p.get('bold', (236, 360, 520))]; bw = [v * k for v in p.get('bw', (18, 16, 13))]
        fine = [v * k for v in p.get('fine', (300, 445, 640, 880, 1200))]; fw = 4.4 * BOOST[0]; fop = 0.6
        bw = [v * BOOST[0] for v in bw]
    else:
        bold = [v * k for v in p.get('bold2', (236, 380, 540))]; bw = [v * k for v in p.get('bw2', (30, 27, 24))]
        fine = [v * k for v in p.get('fine2', (820,))]; fw = 11.0; fop = 0.62
    zref = bold[-1] * abs(np.sin(np.radians(phi0))) + 1e-6
    kt = p.get('kt', 0.5) * (1 if L == 3 else 0.8)
    taper = lambda z: 1.0 + kt * np.clip(z / zref, -1.15, 1.15)
    far = P['far'] if L == 3 else min(0.8, P['far'] + 0.22)
    dim = lambda z: mix(far, 1.0, smooth(-0.9, 0.25, z / zref))

    # the Moon: on the middle bold line, on the near side
    mi = min(p.get('moonLine', 1), len(bold) - 1)
    mth = np.radians(p.get('moonTh', 60.0))
    r = bold[mi] * np.sin(mth) ** 2
    ph = np.radians(phi0)
    mp = M @ np.array([r * np.sin(mth) * np.cos(ph), -r * np.cos(mth), r * np.sin(mth) * np.sin(ph)]) + c
    if p.get('orbit'):
        o = p['orbit']
        Mo = rot('x', -o.get('view', 16.0)) @ rot('z', o.get('incl', 5.1))
        ou = Mo @ np.array([1.0, 0, 0]); ov = Mo @ np.array([0, 0, 1.0])
        Ro = o['R'] * Re
        ta = np.radians(o.get('at', 35.0))
        mp = c + Ro * (np.cos(ta) * ou + np.sin(ta) * ov)
    cv.knock(mp, mr + (22 if L == 3 else 26) * k, zmargin=1e9 if p.get('moonHalo', True) else mr)

    gcol = mix(nuc, WHITE, 0.1) if P['glow'] else nuc
    gop = (0.36 if P['dark'] else 0.2) * p.get('glowOp', 1.0)
    S.glow = (c[0], c[1], Re, Re * (p.get('glowR', 3.0) if L == 3 else 2.3), gcol, gop)
    set_glow(cv, S.glow, 0.0)

    # the Earth first (so the hairlines know what is in front of them)
    if sun:
        night = mix(nuc, sh_, p.get('night', 0.74))
        e_mat = planet(nuc, night, sun, hi=0.5, rimcol=mix(nuc, WHITE, 0.2))
        m_mat = planet(el, mix(el, sh_, 0.8), sun, hi=0.5)
    else:
        e_mat = lit_ball(nuc, sh_, LIGHT, hi=0.58)
        m_mat = lit_ball(el, sh_, LIGHT, hi=0.55)
    cv.sphere(c, Re, e_mat, persp=False)

    # graticule and axes (the globe): parallels round the rotation axis, on the sphere's surface
    if p.get('globe') and L == 3:
        rax = M @ rot('z', -p.get('axisGap', 9.2)) @ np.array([0, -1.0, 0])     # the rotation axis, 9.2 degrees from the magnetic one
        a1 = norm(np.cross(rax, [0.3, 0.2, 1.0])); a2 = np.cross(rax, a1)
        gcolr = mix(nuc, sh_, 0.55)
        for lat in (-66.6, -23.4, 0, 23.4, 66.6):
            la = np.radians(lat)
            pts = circle3(c - rax * (-np.sin(la)) * Re * 1.0, Re * np.cos(la) * 1.004, a1, a2, n=181)
            cv.tube(pts, 1.1 if lat else 1.7, lambda nx, ny, nz, u: np.broadcast_to(gcolr, nx.shape + (3,)), alpha=0.5 if lat else 0.7, zbias=1.0)
        mer = lambda lo: circle3(c, Re * 1.004, rax, np.cos(np.radians(lo)) * a1 + np.sin(np.radians(lo)) * a2, n=181)
        for lo in (0, 30, 60, 90, 120, 150):
            cv.tube(mer(lo), 1.0, lambda nx, ny, nz, u: np.broadcast_to(gcolr, nx.shape + (3,)), alpha=0.4, zbias=1.0)
    if p.get('axes'):
        mag = M @ np.array([0, -1.0, 0])
        rax = M @ rot('z', -p.get('axisGap', 9.2)) @ np.array([0, -1.0, 0])
        w_ax = 5.0 if L == 3 else 12.0
        axc = hexc(P['ring'])
        for sg in (1, -1):
            cv.flat(np.array([c + sg * mag * Re * 0.98, c + sg * mag * Re * (2.75 if L == 3 else 2.2)]), w_ax, mix(nuc, WHITE if P['dark'] else sh_, 0.25), 0.95)
            if L == 3:
                dashed(cv, np.array([c + sg * rax * Re * 0.98, c + sg * rax * Re * 2.75]), 4.0, axc, 0.8, 16, 11)
        if L == 3:
            # the arc between the two axes, at 2.3 Earth radii
            g = np.radians(np.linspace(0, p.get('axisGap', 9.2), 12))
            arc = np.stack([M @ rot('z', -np.degrees(a)) @ np.array([0, -1.0, 0]) for a in g]) * Re * 2.45 + c
            cv.flat(arc, 3.4, axc, 0.9)
    elif L == 3 and p.get('stubs', True):
        mag = M @ np.array([0, -1.0, 0])
        for sg in (1, -1):
            cv.flat(np.array([c + sg * mag * (Re + 4), c + sg * mag * (Re + 58)]), 4.4, det, 0.6)

    # the bold lines: tubes, both sides of the meridian plane (phi0: the right side comes toward you)
    mat = tube_mat(lit, shd, Lt, spec=p.get('spec', 0.0), wrap=p.get('wrap', 0.5), edge=p.get('edge', 0.0), edgecol=shd)
    planes = p.get('planes', (phi0, phi0 + 180.0))
    for i, Lq in enumerate(bold):
        for ph_ in planes:
            pts, th = dipole_line(Lq, ph_, Re * 0.9, M=M, c=c)
            cv.tube(pts, bw[i] / 2, mat, alpha=dim(pts[:, 2]), taper=taper)
    for (Lq, ph_, wq) in (p.get('cage', ()) if L == 3 else ()):
        pts, th = dipole_line(Lq * k, ph_, Re * 0.9, M=M, c=c)
        cv.tube(pts, wq * k / 2, mat, alpha=dim(pts[:, 2]) * 0.9, taper=taper)

    # the Moon's orbit as a tube (E6e): a circle inclined 5.1 degrees to the ecliptic
    if p.get('orbit'):
        o = p['orbit']
        pts = circle3(c, Ro, ou, ov)
        zo = Ro * np.sin(np.radians(o.get('view', 16.0)))
        omat = tube_mat(mix(el, WHITE, 0.25 if P['dark'] else 0.0), mix(el, sh_, 0.45), Lt, wrap=0.5)
        wo = o.get('w', 15.0) * (1 if L == 3 else 1.9)
        cv.tube(pts, wo / 2, omat, alpha=mix(far, 1.0, smooth(-0.9, 0.3, pts[:, 2] / zo)),
                taper=lambda z: 1.0 + 0.5 * np.clip(z / zo, -1.1, 1.1))
        if L == 3:
            ue = rot('x', -o.get('view', 16.0)) @ np.array([1.0, 0, 0]); ve = rot('x', -o.get('view', 16.0)) @ np.array([0, 0, 1.0])
            dashed(cv, circle3(c, Ro, ue, ve), 3.2, det, 0.55, 5, 13)     # the ecliptic, dotted

    # the fine lines: hairlines in the same planes, out past the tile edge; dimmer and thinner with distance
    for i, Lq in enumerate(fine):
        t_ = i / (len(fine) - 1) if len(fine) > 1 else 0
        for ph_ in planes:
            pts, th = dipole_line(Lq, ph_, Re + 4, n=260, M=M, c=c)
            d = np.linalg.norm(pts - c, axis=1)
            zr = Lq * abs(np.sin(np.radians(phi0))) + 1e-6
            a = fop * (1 - 0.35 * t_) * (0.3 + 0.7 * smooth(Re, Re + 90 * k, d)) * mix(0.55, 1.0, smooth(-0.8, 0.4, pts[:, 2] / zr))
            cv.flat(pts, fw, det, a, taper=lambda z, zr=zr: 1.0 + 0.4 * np.clip(z / zr, -1.1, 1.1))
    for (Lq, ph_) in (p.get('fineCage', ()) if L == 3 else ()):
        pts, th = dipole_line(Lq * k, ph_, Re + 4, n=220, M=M, c=c)
        d = np.linalg.norm(pts - c, axis=1)
        cv.flat(pts, fw * 0.9, det, 0.42 * (0.3 + 0.7 * smooth(Re, Re + 90 * k, d)))

    cv.sphere(mp, mr, m_mat, noknock=True)
    if p.get('elGlow') and L >= 2:
        S.extra_glows.append((mp, mr, mr * 2.4, el, 0.3))
    S.shadow = p.get('shadow', 0.6)
    return S


# ---------- the magnetosphere (E6d): dipole + image dipole (Chapman-Ferraro) + tail current sheet ----------
def mag_field(x, z, s=1.0, Bt=4.0e-3, h=0.8):
    """field in the noon-midnight meridian plane, in Earth radii; x toward the Sun, z north. The Earth's dipole
    (equatorial surface field = 1) plus an image dipole 28 times as strong, 26 Earth radii toward the Sun (the
    classic image-dipole model of the magnetopause, scaled so its nose sits near 7 Earth radii: a storm-time
    magnetosphere; 40 Earth radii gives the quiet 10), plus a tail sheet: lobe field Bt toward the Earth above the
    sheet and away below it, growing in from x = -2.5 to -7.5. s scales the model about the Earth."""
    x = x / s; z = z / s

    def dip(x, z):
        r2 = x * x + z * z; r5 = r2 ** 2.5
        return -3 * x * z / r5, (r2 - 3 * z * z) / r5
    bx, bz = dip(x, z)
    ix, iz = dip(x - 26.0, z)
    bx = bx + 28.0 * ix; bz = bz + 28.0 * iz
    g = np.clip((-x - 2.5) / 5.0, 0, 1)
    g = g * g * (3 - 2 * g)
    bx = bx + Bt * np.tanh(z / h) * g
    return bx, bz


def trace(x0, z0, sgn, s=1.0, step=0.04, nmax=5000, xmin=-16.0):
    pts = [(x0, z0)]
    x, z = x0, z0

    def dirn(x, z):
        bx, bz = mag_field(x, z, s)
        n = np.hypot(bx, bz) + 1e-30
        return sgn * bx / n, sgn * bz / n
    for _ in range(nmax):
        k1 = dirn(x, z); k2 = dirn(x + 0.5 * step * k1[0], z + 0.5 * step * k1[1])
        k3 = dirn(x + 0.5 * step * k2[0], z + 0.5 * step * k2[1]); k4 = dirn(x + step * k3[0], z + step * k3[1])
        x += step * (k1[0] + 2 * k2[0] + 2 * k3[0] + k4[0]) / 6
        z += step * (k1[1] + 2 * k2[1] + 2 * k3[1] + k4[1]) / 6
        pts.append((x, z))
        if x * x + z * z < 0.9 or x < xmin or abs(z) > 14 or x > 12:
            break
    return np.array(pts)


_FL = {}


def field_line_from(lat_deg, side, s=1.0):
    """the line that leaves the northern hemisphere at magnetic latitude lat on the day (side=+1) or night side"""
    key = (lat_deg, side, s)
    if key not in _FL:
        la = np.radians(lat_deg)
        x0, z0 = side * np.cos(la), np.sin(la)
        bx, bz = mag_field(x0, z0, s)
        sgn = 1.0 if (bx * x0 + bz * z0) > 0 else -1.0     # go outward
        _FL[key] = trace(x0 * 1.001, z0 * 1.001, sgn, s)
    return _FL[key]


def shue(r0=6.5, alpha=0.58, tmax=150):
    th = np.radians(np.linspace(-tmax, tmax, 240))
    r = r0 * (2 / (1 + np.cos(th))) ** alpha
    return r * np.cos(th), r * np.sin(th)


def mag_scene(cv, cvb, P, L, p):
    S = Scene(); S.knock_px = 0
    nuc, el, det, sh_ = hexc(P['nuc']), hexc(P['el']), hexc(P['det']), hexc(P['shade'])
    lit, shd = hexc(P['ring_lit']), hexc(P['ring_sh'])
    c = np.array([p.get('cx', 446.0), 512.0, 0.0])
    Re0 = p.get('Re', 54.0)
    Re = Re0 * (1 if L == 3 else 1.3)
    d_mp = 1.0
    lean = p.get('lean', 9.2)
    psi = p.get('psi', 20.0)                 # the day side turned toward you by psi
    M = rot('y', -psi) @ rot('z', lean)      # (x_sun, z_north) -> picture
    cv.cam = (512.0, 512.0, p.get('cam', 2400.0))
    sun = norm(rot('y', -psi) @ np.array([-1.0, 0.0, 0.0]))

    def to3(xz):
        # x toward the Sun = picture left; z north = picture up
        q = np.stack([-xz[:, 0] * Re0, -xz[:, 1] * Re0, np.zeros(len(xz))], axis=1)
        return q @ M.T + c
    zref = 6.0 * Re0 * np.sin(np.radians(psi))
    kt = 0.45
    taper = lambda z: 1.0 + kt * np.clip(z / zref, -1.3, 1.1)
    far = P['far'] if L == 3 else min(0.8, P['far'] + 0.22)
    dim = lambda z: mix(far, 1.0, smooth(-1.6, 0.2, z / zref))

    mr = p.get('moonR', 27.0) * (1 if L == 3 else 1.35)
    mp = to3(np.array([[-p.get('moonX', 9.4), p.get('moonZ', 0.0)]]))[0]
    cv.knock(mp, mr + 18, zmargin=1e9)
    gcol = mix(nuc, WHITE, 0.1) if P['glow'] else nuc
    S.glow = (c[0], c[1], Re, Re * 2.8, gcol, (0.3 if P['dark'] else 0.16))
    set_glow(cv, S.glow, 0.0)
    night = mix(nuc, sh_, 0.74)
    cv.sphere(c, Re, planet(nuc, night, sun, hi=0.5, rimcol=mix(nuc, WHITE, 0.2)), persp=False)

    mat = tube_mat(lit, shd, sun, wrap=0.45)
    if L == 3:
        bold = [(58.0, 1, 15), (66.0, 1, 13.5), (72.5, 1, 12), (58.0, -1, 15), (64.0, -1, 13.5), (68.0, -1, 12)]
        fine = [(76.5, 1), (82, 1), (85, 1), (88.5, 1), (70.0, -1), (72.0, -1), (75, -1), (80, -1), (85, -1)]
        fw, fop = 4.4 * BOOST[0], 0.62
        bold = [(a_, b_, c_ * BOOST[0]) for (a_, b_, c_) in bold]
    else:
        bold = [(62.0, 1, 27), (71.0, 1, 23), (60.0, -1, 27), (67.5, -1, 23)]
        fine = [(82, 1), (72.0, -1), (80, -1)]
        fw, fop = 11.0, 0.62
    def inside(xz):
        # a line ends where it would leave the magnetopause
        r = np.hypot(xz[:, 0], xz[:, 1]); th = np.arctan2(xz[:, 1], xz[:, 0])
        out = r > 7.15 * (2 / (1 + np.cos(th) + 1e-9)) ** 0.58 * 0.985
        return xz[:np.argmax(out)] if out.any() else xz
    for hemi in (1, -1):
        for (lat, side, w) in bold:
            xz = field_line_from(lat, side, d_mp)
            xz = xz * np.array([1, hemi])
            if hemi == -1 and xz[-1, 0] ** 2 + xz[-1, 1] ** 2 < 1.0:
                continue                      # a closed line was already drawn whole from the north
            pts = to3(xz)
            cv.tube(pts, w / 2, mat, alpha=dim(pts[:, 2]), taper=taper)
        for (lat, side) in fine:
            xz = field_line_from(lat, side, d_mp) * np.array([1, hemi])
            if hemi == -1 and xz[-1, 0] ** 2 + xz[-1, 1] ** 2 < 1.0:
                continue
            xz = inside(xz)
            if len(xz) < 3:
                continue
            pts = to3(xz)
            dd = np.linalg.norm(pts - c, axis=1)
            a = fop * (0.3 + 0.7 * smooth(Re, Re + 70, dd)) * mix(0.6, 1.0, smooth(-1.6, 0.3, pts[:, 2] / zref))
            cv.flat(pts, fw, det, a, taper=lambda z: 1.0 + 0.35 * np.clip(z / zref, -1.3, 1.1))
    # the magnetopause (Shue et al. 1997), dashed; and the solar wind as three short hairlines
    sx, sz = shue(7.15, 0.58)
    pts = to3(np.stack([sx, sz], axis=1))
    dashed(cv, pts, 5.0 if L == 3 else 11.0, mix(det, WHITE if P['dark'] else sh_, 0.25), 0.8, 26 if L == 3 else 40, 16 if L == 3 else 30)
    cv.sphere(mp, mr, planet(el, mix(el, sh_, 0.8), sun, hi=0.5), noknock=True)
    S.shadow = 0.5
    return S


design('E6a', 'E', 'The dipole in space', 'M5d with its field lines as tubes in space, tapered by depth',
       'M5d as picked, now true: three shells of the Earth\'s dipole field (they cross the magnetic equator at 2.7, '
       '4.1 and 5.9 Earth radii) in a meridian plane turned 28 degrees, the axis leaning 12 degrees. The right '
       'side comes toward you: thick, bright, in front of the Earth. The left goes away: thin, dim, its feet '
       'hidden behind the Earth. The Moon rides where the electron was.',
       e_scene, dict(), star=True)
design('E6b', 'E', 'Day and night', 'one Sun for everything: the Earth and the Moon show the same phase',
       'E6a lit by the Sun from the left. The Earth has a day side and a night side, and the Moon shows the same '
       'phase, as it must: both are lit by the same far light. The tubes of the field are lit from the same side.',
       e_scene, dict(sun=SUN, wrap=0.3), star=True)
design('E6c', 'E', 'Two axes, the globe', 'the Earth as a globe; rotation axis dashed, magnetic axis solid, 9.2 degrees apart',
       'The science that makes it the Earth: a graticule turns the yellow ball into a globe, the dashed line is the '
       'rotation axis and the solid line the magnetic axis, 9.2 degrees apart (the 2025 value). The field hangs on '
       'the magnetic axis, not on the poles of the globe.',
       e_scene, dict(globe=True, axes=True, lean=12.0, stubs=False))
design('E6d', 'E', 'The magnetosphere', 'the solar wind squeezes the day side and draws the night side into a tail',
       'The field as the Sun shapes it: a model of the dipole inside a magnetopause, with a tail current sheet. The '
       'day side (left) is squeezed, the night side stretched into the tail, the polar lines open into the lobes. '
       'The dashed curve is the magnetopause (Shue 1997), drawn at 7 Earth radii as in a strong solar storm '
       '(10 on a quiet day). The Earth and the Moon are lit from the Sun\'s side; the Moon sits in the tail, as at '
       'full Moon.',
       mag_scene, dict())
design('E6e', 'E', 'The Moon on its orbit', 'the Moon\'s path as a blue ring round the field, 5.1 degrees to the ecliptic',
       'The Moon gets its own ring: its orbit in its own blue, a tube that is thick in front of the Earth and thin '
       'behind it, inclined 5.1 degrees to the dotted ecliptic. Inside it the white dipole field. Lit by the Sun, '
       'so the Moon shows the Earth\'s phase.',
       e_scene, dict(sun=SUN, wrap=0.3, bold=(236, 360), bw=(17, 15), fine=(300, 445, 640, 880, 1200),
                     orbit=dict(R=5.25, at=38.0, view=15.0, w=15.0), bold2=(236, 380), bw2=(29, 26), lean=12.0, tip=10.0))


# ---------- compositing ----------
def render_rgba(id, pid, px, frame='full', style='default', ss=None, lod=None):
    Dz = DESIGNS[id]
    P = PAL['P8N' if (style == 'dark' and pid == 'P8') else pid]
    L = lod or lod_for(px)
    if ss is None:
        ss = 3 if px >= 1024 else 4 if px >= 512 else 6 if px >= 200 else 8
    tile = None
    if frame == 'mac':
        tile = (px * 100.0 / 1024, px * 100.0 / 1024, px * 824.0 / 1024)
    tpx = tile[2] if tile else px
    BOOST[0] = 1.42 if tpx < 110 else 1.3 if tpx < 200 else 1.0
    cv = Canvas(px, ss, tile)
    cvb = Canvas(px, ss, tile)
    S = Dz['scene'](cv, cvb, P, L, Dz['p'])
    X, Y = cv.grid()
    bg0, bg1 = hexc(P['bg'][0]), hexc(P['bg'][1])
    t = np.clip((0.35 * X / 1024 + Y / 1024) / (0.35 * 0.35 + 1.0), 0, 1)[..., None]
    img = mix(bg0, bg1, t)
    if P['glow']:
        d = np.hypot(X - 512, Y - 512) / 1024
        img = mix(img, hexc(P['glow']), (0.2 * np.clip(1 - d / 0.55, 0, 1))[..., None])
    fg = cv.down()
    back = cvb.down()
    if S.knock_px:
        kpx = S.knock_px * (1 if L == 3 else 1.6) * cv.k / cv.ss
        K = np.clip(blur(fg[..., 3], max(0.3, kpx * 0.55)) * 3.2, 0, 1)
        back = back * (1 - K[..., None])
    img = img * (1 - back[..., 3:4]) + back[..., :3]
    if S.glow:
        cx, cy, r0, r1, rgb, op = S.glow
        ga = glow_alpha(np.maximum(np.hypot(X - cx, Y - cy), r0), r0, r1, op)
        img = mix(img, rgb, ga[..., None])
    for (ep, r0, r1, rgb, op) in S.extra_glows:
        sx, sy, _, _ = cv.project(np.asarray(ep, dtype=float))
        ex = (sx - cv.ox) / cv.k; ey = (sy - cv.oy) / cv.k
        ga = glow_alpha(np.maximum(np.hypot(X - ex, Y - ey), r0), r0, r1, op)
        img = mix(img, rgb, ga[..., None])
    if S.shadow and L >= 2:
        dpx = 10.0 * cv.k / cv.ss
        sh = blur(fg[..., 3], dpx * 1.15)
        sh = ndimage.shift(sh, (dpx, dpx * 0.2), order=1, mode='constant')
        img = img * (1 - (S.shadow * (0.5 if P['dark'] else 0.2)) * sh[..., None])
    img = img * (1 - fg[..., 3:4]) + fg[..., :3]
    # the glass: a sheen from the top and a light edge (K5a's soft glass)
    if S.sheen and L >= 2:
        sh = (0.13 if P['dark'] else 0.35) * 0.55
        a = sh * np.clip(1 - (Y / 1024) / 0.26, 0, 1)
        img = img + (1 - img) * a[..., None]
        ed = edge_dist(X, Y)
        wd = 4.2 * (1 if L == 3 else 1.9)
        ty = Y / 1024
        eo = np.where(ty < 0.3, mix(0.5, 0.065, ty / 0.3), np.where(ty < 0.7, mix(0.065, 0.0, (ty - 0.3) / 0.4), mix(0.0, 0.14, (ty - 0.7) / 0.3)))
        a = eo * np.clip(1 - ed / wd, 0, 1) ** 1.3 * (ed > -3)
        if not P['dark']:
            a = a * 0.9
        img = img + (1 - img) * a[..., None]
    elif L == 1:
        pass
    m = tile_mask(cv, 4)
    if frame == 'mac':
        # the tile's own soft shadow on the Apple grid
        spx = px / 1024.0
        shd = ndimage.shift(blur(m, 12 * spx), (10 * spx, 0), order=1, mode='constant') * 0.32
        al = m + (1 - m) * shd
        rgb = img * (m / np.maximum(al, 1e-6))[..., None]
        return rgb, al
    return img, m


def render(id, pid, px, frame='full', style='default', **kw):
    rgb, al = render_rgba(id, pid, px, frame, style, **kw)
    return to_img(rgb, al)


if __name__ == '__main__':
    import sys, time
    from PIL import Image
    out = sys.argv[1]
    ids = sys.argv[2].split(',')
    px = int(sys.argv[3]) if len(sys.argv) > 3 else 512
    pids = (sys.argv[4] if len(sys.argv) > 4 else 'P2').split(',')
    small = [int(v) for v in sys.argv[5].split(',')] if len(sys.argv) > 5 else []
    W = Image.new('RGB', (px * len(ids), (px + (max(small) + 10 if small else 0)) * len(pids)), (40, 42, 50))
    for r, pid in enumerate(pids):
        y0 = r * (px + (max(small) + 10 if small else 0))
        for k, i in enumerate(ids):
            t0 = time.time()
            im = render(i, pid, px)
            W.paste(im, (k * px, y0), im)
            x = k * px + 6
            for s_ in small:
                im = render(i, pid, s_)
                W.paste(im, (x, y0 + px + 5), im); x += s_ + 8
            print(i, pid, round(time.time() - t0, 1), 's')
    W.save(out)
