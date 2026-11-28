"""AudioLab app icon, round 7 (task IC11): the big designs G1..G7.

One small scene in Earth radii: the Earth (yellow) at the origin, the Moon (blue), the Van Allen belts as see-through
lit shells between dipole field shells, field lines and the Moon's orbit as round tubes, one light from the upper left.
Distances are compressed so the Earth stays the focal point (docs/app-icon-round-7.md has the table).

render(id, pid, px, frame='full'|'mac') -> PIL RGBA
"""
import numpy as np
from scipy import ndimage
from r7 import (Cam, Canvas, hexc, mix, norm, smooth, rot, planet, tube_mat, belt, shell, tile_mask, edge_dist, blur,
                to_img, F)

PAL = {
    'P2': dict(id='P2', name='Orbit night', dark=True, bg=('#132044', '#070910'), line='#EAF1FF', earth='#FFC43C',
               moon='#4CC9F0', det='#6096FF', shade='#070910', night='#5B3A14', mnight='#123A56',
               outer=('#3F6FE0', '#A9C4FF'), inner=('#F2A73A', '#FFE2A0'), far='#33488A', grat='#A8650C',
               orbit='#4CC9F0', orbit_far='#1F6C8C', pause='#7FA6FF', cglow='#6096FF'),
    'P8': dict(id='P8', name='Chart paper', dark=False, bg=('#F7F3EA', '#E4DCCA'), line='#1B2340', earth='#C8610A',
               moon='#2F6BFF', det='#1B2340', shade='#1B2340', night='#6E3406', mnight='#173A99',
               outer=('#5E78C8', '#1B2A66'), inner=('#E39A4E', '#A84E06'), far='#9AA0B4', grat='#7A3A04',
               orbit='#2F6BFF', orbit_far='#93AEEB', pause='#3A4C8C', cglow=None),
}
WHITE = np.ones(3, dtype=F)
STEPS = [0]
LIGHT = norm((-0.62, -0.50, 0.60))        # the one light, in screen axes: upper left, in front
Y = np.array([0.0, 1.0, 0.0])
ROT_AXIS = rot('z', -23.44) @ Y           # the Earth's rotation axis: 23.44 degrees from the ecliptic's normal
MAG_AXIS = rot('z', -23.44 + 9.21) @ Y    # the magnetic (dipole) axis: 9.21 degrees from it (WMM 2025)


def lod_for(tpx):
    return 3 if tpx >= 120 else 2 if tpx >= 44 else 1


def frame_of(axis, ref=(0, 0, 1.0)):
    a = norm(axis)
    e1 = np.cross(a, ref); e1 = norm(e1)
    return a, e1, np.cross(a, e1)


def field_line(axis, L, phi, r_in=1.0, n=300, half=None, e1=None):
    """a dipole field line r = L cos^2(lat) in the meridian at longitude phi (degrees round the axis)"""
    a, b1, b2 = frame_of(axis)
    if e1 is not None:
        b1 = norm(e1 - (e1 @ a) * a); b2 = np.cross(a, b1)
    l0 = np.arccos(np.sqrt(min(1.0, r_in / L)))
    lam = np.linspace(-l0, l0, n)
    if half == 'n':
        lam = np.linspace(0, l0, n)
    r = L * np.cos(lam) ** 2
    ph = np.radians(phi)
    eq = np.cos(ph) * b1 + np.sin(ph) * b2
    return np.outer(r * np.cos(lam), eq) + np.outer(r * np.sin(lam), a)


def circle(R, normal, n=721, c=(0, 0, 0), t0=0.0, t1=360.0, ref=(0, 0, 1.0)):
    a, e1, e2 = frame_of(normal, ref)
    t = np.radians(np.linspace(t0, t1, n))
    return np.asarray(c) + R * (np.outer(np.cos(t), e1) + np.outer(np.sin(t), e2))


class Scene:
    def __init__(self, cv, P, lod):
        self.cv, self.P, self.lod, self.cam = cv, P, lod, cv.cam
        self.glows = []          # (world point, r0, r1 world, rgb, op)
        self.bound = 6.0
        self.steps = 150
        self.boost = 1.0 if lod == 3 else 1.5 if lod == 2 else 2.0
        self.minr = 0.0 if lod == 3 else 0.55

    def c(self, k):
        v = self.P[k]
        return hexc(v) if isinstance(v, str) else tuple(hexc(x) for x in v)

    def earth(self, R=1.0, globe=False, c=(0, 0, 0), glow=(2.6, 0.42)):
        P = self.P; col = self.c('earth')
        base = planet(col, self.c('night'), LIGHT, hi=0.5 if P['dark'] else 0.3, amb=0.3,
                      rim=mix(col, WHITE, 0.3) if P['dark'] else None)
        if globe and self.lod == 3:
            a, e1, e2 = frame_of(ROT_AXIS)
            g = self.c('grat'); lw = self.cam.px(2.6) / R

            def sh(nx, ny, nz, nw):
                cc = base(nx, ny, nz)
                lat = np.degrees(np.arcsin(np.clip(nw @ a, -1, 1)))
                lon = np.degrees(np.arctan2(nw @ e2, nw @ e1))
                cl = np.sqrt(np.clip(1 - (nw @ a) ** 2, 1e-4, 1))
                dlat = np.abs((lat + 15) % 30 - 15) * np.pi / 180
                dlon = np.abs((lon + 15) % 30 - 15) * np.pi / 180 * cl
                d = np.minimum(dlat, dlon)
                k = (1 - smooth(lw * 0.5, lw * 1.2, d)) * 0.62 * smooth(0.0, 0.3, nz)
                return cc + (g - cc) * k[..., None]
            self.cv.sphere(c, R, sh)
        else:
            self.cv.sphere(c, R, lambda nx, ny, nz, nw: base(nx, ny, nz))
        if glow:
            self.glows.append((c, R, R * glow[0], mix(col, WHITE, 0.12), glow[1] * (1.0 if P['dark'] else 0.45)))

    def moon(self, pos, R=0.42, glow=(2.3, 0.34)):
        P = self.P; col = self.c('moon')
        if self.lod < 3:
            R *= 1.2
        sh = planet(col, self.c('mnight'), LIGHT, hi=0.5 if P['dark'] else 0.3, amb=0.42)
        self.cv.sphere(pos, R, lambda nx, ny, nz, nw: sh(nx, ny, nz))
        if glow:
            self.glows.append((pos, R, R * glow[0], col, glow[1] * (1.0 if P['dark'] else 0.4)))
        return R

    def line(self, pts, wpx, near=None, far=None, wspan=None, shade=0.26):
        """a lit tube wpx design units wide at the target's depth"""
        cam = self.cam
        near = self.c('line') if near is None else near
        far = self.c('far') if far is None else far
        w0, w1 = wspan if wspan else (cam.dist - 3.0, cam.dist + 3.5)
        m = tube_mat(near, far, LIGHT, w0, w1, shade=shade, dark=mix(far, self.c('shade'), 0.5))
        self.cv.tube(pts, cam.px(wpx * self.boost) / 2, m, minr=self.minr)

    def lightw(self):
        cm = self.cam
        return cm.right * LIGHT[0] - cm.up * LIGHT[1] - cm.fwd * LIGHT[2]

    def belts(self, axis=MAG_AXIS, inner=(1.4, 1.9, 34), outer=(2.5, 3.7, 42), cut=None, e1=None, ki=1.0, ko=1.0,
              fill=1.0, skin=0.10, cap=1.0, window=None):
        """ki, ko: strength of the inner and outer belt (0 = not drawn); fill: how milky the inside is"""
        P = self.P
        oc, orim = self.c('outer'); ic, irim = self.c('inner')
        d = (1.0 if P['dark'] else 1.25) * (1.0 if self.lod == 3 else 1.6)
        lw = self.lightw()
        win = (self.cam.eye, window[0], window[1], window[2]) if window else None
        if ko:
            self.cv.fields.append(belt(axis, outer[0], outer[1], outer[2], oc, orim, 0.10 * d * ko * fill, 1.25 * d * ko,
                                       skin=skin, cut=cut, cap=9.0 * cap if cut else 0, capcol=mix(oc, orim, 0.5), e1=e1, light=lw, window=win))
        if ki:
            self.cv.fields.append(belt(axis, inner[0], inner[1], inner[2], ic, irim, 0.22 * d * ki * fill, 1.9 * d * ki,
                                       skin=skin * 0.7, cut=cut, cap=11.0 * cap if cut else 0, capcol=mix(ic, irim, 0.55), e1=e1, light=lw, window=win))
        self.bound = (outer[1] if ko else inner[1]) + 0.06

    def orbit(self, R, normal, at, wpx=8, moonR=0.42, ref=(0, 0, 1.0), arc=(0, 360), glow=(2.3, 0.34)):
        """the Moon's path as a lit tube in the Moon's blue, the Moon on it at `at` degrees"""
        orb = circle(R, normal, t0=arc[0], t1=arc[1], ref=ref)
        mp = circle(R, normal, n=2, t0=at, t1=at, ref=ref)[0]
        d = self.cam.dist
        self.line(orb, wpx, near=self.c('orbit'), far=self.c('orbit_far'), wspan=(d - R * 0.8, d + R * 0.9))
        self.moon(mp, moonR, glow=glow)
        return mp

    def dashed(self, a, b, wpx, dash, gap, **kw):
        a = np.asarray(a, float); b = np.asarray(b, float)
        Ln = np.linalg.norm(b - a); u = (b - a) / Ln; pos = 0.0
        while pos < Ln:
            e = min(pos + dash, Ln)
            self.line(np.array([a + u * pos, a + u * e]), wpx, **kw)
            pos += dash + gap


DESIGNS = {}
ORBIT_N = rot('z', -5.145) @ Y            # the Moon's orbit: 5.145 degrees to the ecliptic


def design(id, name, line, star=False, p8=True):
    def deco(fn):
        DESIGNS[id] = dict(id=id, name=name, line=line, star=star, fn=fn, p8=p8)
        return fn
    return deco


def start(px, ss, tile, P, lod, **cam):
    return Scene(Canvas(px, ss, Cam(**cam), tile), P, lod)


@design('G1', 'Belts cut open', 'Both belts cut open, the Moon passing', star=True)
def g1(*a):
    S = start(*a, dist=17.0, az=0, el=22, f=1700.0, c=(506.0, 536.0))
    S.earth()
    S.belts(cut=(-150, -30), e1=np.array([1.0, 0, 0]))
    S.orbit(4.5, ORBIT_N, 36, wpx=9, moonR=0.46)
    return S


@design('G2', 'Moon on its orbit', 'The Moon circles the glass belts')
def g2(*a):
    S = start(*a, dist=12.0, az=-14, el=17, f=1200.0, c=(500.0, 516.0))
    S.earth()
    S.belts(inner=(1.4, 1.85, 30), outer=(2.4, 3.4, 40), ki=0.7, ko=0.9, fill=0.5, window=(1.15, 2.0, 0.93))
    S.orbit(4.3, ORBIT_N, 287, wpx=11, moonR=0.40)
    return S


def shue(r0, al):
    return lambda ct: r0 * (2.0 / (1.0 + np.clip(ct, -0.985, 1.0))) ** al


@design('G3', 'Magnetosphere', 'Solar wind shapes the field, Moon behind', p8=False)
def g3(*a):
    S = start(*a, dist=20.0, az=14, el=12, f=1900.0, c=(430.0, 516.0))
    P = S.P
    S.earth()
    ax = rot('z', -9.0) @ Y
    S.belts(axis=ax, inner=(1.35, 1.75, 32), outer=(2.1, 2.9, 40), ki=0.7, ko=0.9, fill=0.5, window=(1.1, 1.8, 0.93))
    sun = np.array([-1.0, 0, 0])
    S.cv.fields.append(shell(shue(3.75, 0.58), sun, S.c('pause'), 0.5 if P['dark'] else 0.7, width=0.10, xfade=(-8.5, -2.0)))
    S.bound = 10.0; S.steps = 260
    # field lines in the noon-midnight plane: squeezed toward the Sun, drawn out into the tail
    def warp(p, L):
        q = p.copy(); x = q[:, 0]
        q[:, 0] = np.where(x < 0, x * (1 - 0.05 * L), x * (1 + 0.075 * L * L / 3.0))
        return q
    e1 = np.array([1.0, 0, 0])
    for L, w in (((3.3, 8.0), (4.6, 8.0)) if S.lod == 3 else ((3.9, 8.0),)):
        for ph in (0, 180):
            S.line(warp(field_line(ax, L, ph, r_in=1.04, e1=e1), L), w)
    if S.lod == 3:
        for sg in (1, -1):                       # open lines of the polar caps, swept into the tail lobes
            t = np.linspace(0, 1, 80)
            p = np.stack([0.26 * (1 - t) + 8.0 * t ** 1.5, sg * (1.0 + 2.2 * (1 - np.exp(-t * 3.4))), np.zeros_like(t)], axis=1)
            p[0] = norm(p[0]) * 1.03
            S.line(p, 6.0)
    S.moon(np.array([5.15, -0.25, 1.0]), 0.42)
    S.gcentre = (430, 516)
    return S


@design('G4', 'Globe, two axes', 'Rotation and magnetic axes, 9 degrees apart', star=True)
def g4(*a):
    S = start(*a, dist=12.0, az=0, el=15, f=1900.0, c=(490.0, 560.0))
    S.earth(globe=True, glow=(2.0, 0.4))
    S.belts(inner=(1.42, 1.85, 30), outer=(2.35, 3.3, 38), cut=(-165, -15), e1=np.array([1.0, 0, 0]))
    if S.lod == 3:
        S.dashed(ROT_AXIS * 1.03, ROT_AXIS * 2.2, 5.0, 0.13, 0.09)
        S.dashed(-ROT_AXIS * 1.03, -ROT_AXIS * 1.85, 5.0, 0.13, 0.09)
        t = np.linspace(0, 1, 16)
        S.line(np.array([norm(ROT_AXIS * (1 - u) + MAG_AXIS * u) * 2.05 for u in t]), 4.0)
    ec = mix(S.c('earth'), WHITE, 0.25) if S.P['dark'] else S.c('earth')
    S.line(np.array([MAG_AXIS * 1.03, MAG_AXIS * 2.35]), 8.0, near=ec, far=ec)
    S.line(np.array([-MAG_AXIS * 1.03, -MAG_AXIS * 1.95]), 8.0, near=ec, far=ec)
    S.moon(np.array([2.35, 2.25, 0.6]), 0.40)
    return S


@design('G5', 'From above', 'Seen from above: rings, slot and orbit')
def g5(*a):
    S = start(*a, dist=15.0, az=0, el=58, f=1560.0, c=(512.0, 512.0))
    S.earth(glow=(2.0, 0.4))
    S.belts(axis=rot('x', 6.0) @ MAG_AXIS, inner=(1.45, 1.95, 30), outer=(2.55, 3.6, 36), ki=0.8, ko=1.0, fill=0.6, window=(1.1, 1.7, 0.9))
    S.orbit(4.35, ORBIT_N, 48, wpx=9, moonR=0.40)
    return S


@design('G6', 'Close-up', 'Close on the Earth, the Moon beyond')
def g6(*a):
    S = start(*a, dist=9.0, az=0, el=15, f=1350.0, c=(300.0, 716.0))
    ax = rot('z', 40.0) @ Y
    e1 = rot('z', 40.0) @ np.array([1.0, 0, 0])
    S.earth(glow=(2.2, 0.5))
    S.belts(axis=ax, inner=(1.4, 1.85, 32), outer=(2.3, 3.2, 40), cut=(-180, 0), e1=e1)
    for L in (2.07, 3.45):
        S.line(field_line(ax, L, 0, r_in=1.04, e1=e1) + np.array([0, 0, 0.03]), 9.0, wspan=(7.0, 11.0))
    S.moon(e1 * 4.45 + np.array([0, 0.1, 0]), 0.5)
    S.gcentre = (300, 716)
    return S


@design('G7', 'Half shell', 'Belts cut in half, field lines shown', star=True)
def g7(*a):
    S = start(*a, dist=17.0, az=0, el=9, f=2040.0, c=(506.0, 530.0))
    ax = rot('z', -11.0) @ Y
    e1 = np.array([1.0, 0, 0])
    S.earth()
    S.belts(axis=ax, cut=(-180, 0), e1=e1, inner=(1.4, 1.9, 36), outer=(2.5, 3.6, 44))
    for L in ((2.2, 4.0) if S.lod == 3 else (4.0,)):
        for ph in (0, 180):
            S.line(field_line(ax, L, ph, r_in=1.04, e1=e1) + np.array([0, 0, 0.03]), 8.0)
    S.moon(np.array([3.3, 2.75, 0.0]), 0.42)
    return S


# ---------- compositing ----------
def glow_alpha(d, r0, r1, op):
    t = np.clip((d - r0) / (r1 - r0), 0, 1)
    return op * (1 - t) ** 2.2 * (d < r1)


def render_rgba(id, pid, px, frame='full', ss=None, lod=None):
    Dz = DESIGNS[id]; P = PAL[pid]
    tile = (px * 100.0 / 1024, px * 100.0 / 1024, px * 824.0 / 1024) if frame == 'mac' else None
    tpx = tile[2] if tile else px
    L = lod or lod_for(tpx)
    if ss is None:
        ss = 2 if px >= 1024 else 3 if px >= 512 else 4 if px >= 200 else 6 if px >= 100 else 8
    S = Dz['fn'](px, ss, tile, P, L)
    cv = S.cv
    X, Yg = cv.grid()
    bg0, bg1 = hexc(P['bg'][0]), hexc(P['bg'][1])
    t = np.clip((0.35 * X / 1024 + Yg / 1024) / (0.35 * 0.35 + 1.0), 0, 1)[..., None]
    img = mix(bg0, bg1, t)
    if P['cglow']:
        gc = getattr(S, 'gcentre', (512, 512))
        d = np.hypot(X - gc[0], Yg - gc[1]) / 1024
        img = mix(img, hexc(P['cglow']), (0.2 * np.clip(1 - d / 0.6, 0, 1))[..., None])
    fg = cv.down(cv.march(S.bound, steps=STEPS[0] or (S.steps if px >= 200 else max(60, S.steps // 2))))
    for (pw, r0, r1, rgb, op) in S.glows:
        gx, gy, w, s = cv.cam.project(np.asarray(pw, dtype=float))
        ga = glow_alpha(np.maximum(np.hypot(X - gx, Yg - gy), r0 * s), r0 * s, r1 * s, op)
        img = mix(img, rgb, ga[..., None])
    img = img * (1 - fg[..., 3:4]) + fg[..., :3]
    # the tile's glass: a soft sheen from the top left and a light edge (drawn, so Icon Composer's specular stays off)
    if L >= 2:
        a = (0.07 if P['dark'] else 0.18) * np.clip(1 - (Yg / 1024 + 0.25 * X / 1024) / 0.34, 0, 1)
        img = img + (1 - img) * a[..., None]
        ed = edge_dist(X, Yg)
        wd = 4.2 * (1 if L == 3 else 1.9)
        ty = Yg / 1024
        eo = np.where(ty < 0.3, mix(0.5, 0.065, ty / 0.3), np.where(ty < 0.7, mix(0.065, 0.0, (ty - 0.3) / 0.4), mix(0.0, 0.14, (ty - 0.7) / 0.3)))
        a = eo * np.clip(1 - ed / wd, 0, 1) ** 1.3 * (ed > -3)
        img = img + (1 - img) * (a * (1.0 if P['dark'] else 0.9))[..., None]
    m = tile_mask(cv, 4)
    if frame == 'mac':
        spx = px / 1024.0
        shd = ndimage.shift(blur(m, 12 * spx), (10 * spx, 0), order=1, mode='constant') * 0.32
        al = m + (1 - m) * shd
        return img * (m / np.maximum(al, 1e-6))[..., None], al
    return img, m


def render(id, pid, px, frame='full', **kw):
    rgb, al = render_rgba(id, pid, px, frame, **kw)
    return to_img(rgb, al)


if __name__ == '__main__':
    import sys, time, os
    QUICK = dict(ss=2) if os.environ.get('QUICK') else {}
    if QUICK:
        STEPS[0] = 80
    from PIL import Image
    out = sys.argv[1]; ids = sys.argv[2].split(','); px = int(sys.argv[3]) if len(sys.argv) > 3 else 512
    pids = (sys.argv[4] if len(sys.argv) > 4 else 'P2').split(',')
    small = [int(v) for v in sys.argv[5].split(',')] if len(sys.argv) > 5 else []
    rowh = px + (max(small) + 10 if small else 0)
    W = Image.new('RGB', (px * len(ids), rowh * len(pids)), (40, 42, 50))
    for r, pid in enumerate(pids):
        for k, i in enumerate(ids):
            t0 = time.time()
            im = render(i, pid, px, **QUICK)
            W.paste(im, (k * px, r * rowh), im)
            x = k * px + 6
            for s_ in small:
                im = render(i, pid, s_)
                W.paste(im, (x, r * rowh + px + 5), im); x += s_ + 8
            print(i, pid, round(time.time() - t0, 1), 's', flush=True)
    W.save(out)
