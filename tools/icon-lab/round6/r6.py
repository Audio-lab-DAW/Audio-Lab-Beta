"""AudioLab app icon, round 6 (task IC10): a small software 3D renderer for the icon lab.

Rounds 2 to 5 drew SVG strokes and let rsvg-convert paint them, so a ring could only be a stroke cut into pieces.
Round 6 paints the pixels itself: every ring, orbit and field line is a round tube in space, every body a sphere,
seen through one camera, with a depth buffer. So the taper, the dimming with distance, the shading across a tube,
what hides what at a crossing and behind the nucleus all come from the same geometry.

  design frame : 0..1024 square (the tile), y down, z toward the viewer
  camera       : screen = C + (p.xy - C) * D / (D - z)   (C the picture centre, D the camera distance)
  Canvas       : px * ss samples; RGBA premultiplied + depth; binary coverage per sample, averaged down (anti-aliasing)
  tube()       : a polyline of 3D points with a radius, drawn as capsules; per sample the tube's surface normal and depth
  flat()       : a see-through flat line (field hairlines): blended over what is behind it and under what is in front
  sphere()     : a lit ball
Only numpy, scipy.ndimage (blur) and Pillow are needed.
"""
import numpy as np
from scipy import ndimage

F = np.float32


def hexc(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)], dtype=F)


def mix(a, b, t):
    return a + (b - a) * t


def norm(v):
    v = np.asarray(v, dtype=np.float64)
    return v / np.linalg.norm(v)


def smooth(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3 - 2 * t)


class Canvas:
    def __init__(self, px, ss, tile=None, cam=(512.0, 512.0, 2600.0)):
        self.px, self.ss = px, ss
        self.N = px * ss
        tx, ty, ts = tile if tile else (0.0, 0.0, float(px))
        self.k = ts / 1024.0 * ss            # samples per design unit
        self.ox, self.oy = tx * ss, ty * ss  # tile origin in samples
        self.col = np.zeros((self.N, self.N, 4), dtype=F)
        self.z = np.full((self.N, self.N), -1e9, dtype=F)
        self.cam = cam
        self.knocks = []                     # (sx, sy, r, z): nothing farther than z is drawn within r (the halo round a moon)
        self.glow = None                     # f(X, Y samples) -> (rgb, alpha) laid over fragments behind glow_z
        self.glow_z = 0.0

    # design 3D -> sample coords, depth, scale
    def project(self, p):
        p = np.asarray(p, dtype=np.float64)
        cx, cy, D = self.cam
        f = D / (D - p[..., 2])
        sx = (cx + (p[..., 0] - cx) * f) * self.k + self.ox
        sy = (cy + (p[..., 1] - cy) * f) * self.k + self.oy
        return sx, sy, p[..., 2], f

    def _bbox(self, x0, x1, y0, y1):
        i0 = max(0, int(np.floor(x0))); i1 = min(self.N, int(np.ceil(x1)) + 1)
        j0 = max(0, int(np.floor(y0))); j1 = min(self.N, int(np.ceil(y1)) + 1)
        if i1 <= i0 or j1 <= j0:
            return None
        return i0, i1, j0, j1

    def _write(self, j0, j1, i0, i1, m, rgb, a, z, X, Y, opaque=True, noknock=False):
        """blend fragments (rgb (..,3), a (..) straight alpha, z depth) where m: over if nearer, under if farther"""
        if not m.any():
            return
        zb = self.z[j0:j1, i0:i1]
        cb = self.col[j0:j1, i0:i1]
        for (kx, ky, kr, kz) in ([] if noknock else self.knocks):
            m = m & ~(((X - kx) ** 2 + (Y - ky) ** 2 < kr * kr) & (z < kz))
        if self.glow is not None:
            g_rgb, g_a = self.glow(X, Y)
            ga = (g_a * (z < self.glow_z))[..., None]
            rgb = rgb * (1 - ga) + g_rgb * ga
        front = m & (z > zb)
        back = m & ~front
        a = np.broadcast_to(a, m.shape)
        src = np.concatenate([rgb * a[..., None], a[..., None]], axis=-1).astype(F)
        if front.any():
            s = src[front]; d = cb[front]
            cb[front] = s + d * (1 - s[:, 3:4])
            if opaque:
                zb[front] = z[front]
        if back.any():
            s = src[back]; d = cb[back]
            cb[back] = d + s * (1 - d[:, 3:4])

    def tube(self, pts, rad, shade, alpha=1.0, taper=None, zbias=0.0, minr=0.0):
        """pts (n,3) design units; rad: radius in design units (scalar or (n,)); shade(nx, ny, nz, u) -> rgb, with u the
        position along the tube 0..1; alpha scalar or (n,); taper(zs) -> factor on the radius (exaggerated perspective)."""
        pts = np.asarray(pts, dtype=np.float64)
        n = len(pts)
        sx, sy, zs, f = self.project(pts)
        r = np.broadcast_to(np.asarray(rad, dtype=np.float64), (n,)) * f
        if taper is not None:
            r = r * taper(zs)
        rs = np.maximum(r * self.k, minr)       # radius in samples
        al = np.broadcast_to(np.asarray(alpha, dtype=np.float64), (n,))
        uu = np.linspace(0, 1, n)
        rm = rs.max() + 1
        bb = self._bbox(sx.min() - rm, sx.max() + rm, sy.min() - rm, sy.max() + rm)
        if bb is None:
            return
        I0, I1, J0, J1 = bb
        shp = (J1 - J0, I1 - I0)
        # one pass over the whole tube: each sample keeps the piece whose axis it is closest to (in tube radii),
        # so the pieces join without ribs
        Q = np.full(shp, 1.0, dtype=F)
        NX = np.zeros(shp, dtype=F); NY = np.zeros(shp, dtype=F); ZC = np.zeros(shp, dtype=F)
        RW = np.zeros(shp, dtype=F); UU = np.zeros(shp, dtype=F); AA = np.zeros(shp, dtype=F)
        for i in range(n - 1):
            ax, ay, bx, by = sx[i], sy[i], sx[i + 1], sy[i + 1]
            ra, rb = rs[i], rs[i + 1]
            rmx = max(ra, rb) + 1
            bb = self._bbox(min(ax, bx) - rmx, max(ax, bx) + rmx, min(ay, by) - rmx, max(ay, by) + rmx)
            if bb is None:
                continue
            i0, i1, j0, j1 = bb
            Y, X = np.mgrid[j0:j1, i0:i1].astype(F)
            X += 0.5; Y += 0.5
            dx, dy = bx - ax, by - ay
            L2 = dx * dx + dy * dy
            t = np.clip(((X - ax) * dx + (Y - ay) * dy) / L2, 0, 1) if L2 > 1e-9 else np.zeros_like(X)
            rr = ra + t * (rb - ra)
            ox = X - (ax + t * dx); oy = Y - (ay + t * dy)
            q = (ox * ox + oy * oy) / (rr * rr)
            sl = (slice(j0 - J0, j1 - J0), slice(i0 - I0, i1 - I0))
            up = q < Q[sl]
            if not up.any():
                continue
            Q[sl][up] = q[up]
            NX[sl][up] = (ox / rr)[up]; NY[sl][up] = (oy / rr)[up]
            ZC[sl][up] = (zs[i] + t * (zs[i + 1] - zs[i]))[up]
            RW[sl][up] = (rr / self.k)[up]
            UU[sl][up] = (uu[i] + t * (uu[i + 1] - uu[i]))[up]
            AA[sl][up] = (al[i] + t * (al[i + 1] - al[i]))[up]
        m = Q < 1.0
        if not m.any():
            return
        nz = np.sqrt(np.clip(1 - Q, 0, 1))
        z = ZC + RW * nz + zbias
        rgb = shade(NX, NY, nz, UU)
        Y, X = np.mgrid[J0:J1, I0:I1].astype(F)
        X += 0.5; Y += 0.5
        self._write(J0, J1, I0, I1, m, rgb, AA, z.astype(F), X, Y)

    def flat(self, pts, width, rgb, alpha=1.0, taper=None, minw=0.0, zoff=0.0):
        """a flat see-through line: one coverage pass for the whole polyline (no double-blended joints), then blended
        with a depth test. width in design units (scalar or (n,)), alpha scalar or (n,)."""
        pts = np.asarray(pts, dtype=np.float64)
        n = len(pts)
        sx, sy, zs, f = self.project(pts)
        zs = zs + zoff
        r = np.broadcast_to(np.asarray(width, dtype=np.float64), (n,)) * 0.5 * f
        if taper is not None:
            r = r * taper(zs)
        rs = np.maximum(r * self.k, minw * 0.5)
        al = np.broadcast_to(np.asarray(alpha, dtype=np.float64), (n,))
        rm = rs.max() + 1
        bb = self._bbox(sx.min() - rm, sx.max() + rm, sy.min() - rm, sy.max() + rm)
        if bb is None:
            return
        I0, I1, J0, J1 = bb
        A = np.zeros((J1 - J0, I1 - I0), dtype=F)
        Z = np.full((J1 - J0, I1 - I0), -1e9, dtype=F)
        for i in range(n - 1):
            ax, ay, bx, by = sx[i], sy[i], sx[i + 1], sy[i + 1]
            ra, rb = rs[i], rs[i + 1]
            rmx = max(ra, rb) + 1
            bb = self._bbox(min(ax, bx) - rmx, max(ax, bx) + rmx, min(ay, by) - rmx, max(ay, by) + rmx)
            if bb is None:
                continue
            i0, i1, j0, j1 = bb
            Y, X = np.mgrid[j0:j1, i0:i1].astype(F)
            X += 0.5; Y += 0.5
            dx, dy = bx - ax, by - ay
            L2 = dx * dx + dy * dy
            t = np.clip(((X - ax) * dx + (Y - ay) * dy) / L2, 0, 1) if L2 > 1e-9 else np.zeros_like(X)
            rr = ra + t * (rb - ra)
            ox = X - (ax + t * dx); oy = Y - (ay + t * dy)
            m = ox * ox + oy * oy < rr * rr
            if not m.any():
                continue
            a = (al[i] + t * (al[i + 1] - al[i])).astype(F)
            As = A[j0 - J0:j1 - J0, i0 - I0:i1 - I0]; Zs = Z[j0 - J0:j1 - J0, i0 - I0:i1 - I0]
            up = m & (a > As)
            As[up] = a[up]
            Zs[up] = (zs[i] + t * (zs[i + 1] - zs[i]))[up]
        m = A > 0
        if not m.any():
            return
        Y, X = np.mgrid[J0:J1, I0:I1].astype(F)
        X += 0.5; Y += 0.5
        col = np.broadcast_to(np.asarray(rgb, dtype=F), m.shape + (3,))
        self._write(J0, J1, I0, I1, m, col, A, Z, X, Y, opaque=False)

    def sphere(self, c, R, shade, alpha=1.0, persp=True, noknock=False):
        """c (3,) design units, R design units; shade(nx, ny, nz) -> rgb"""
        sx, sy, zc, f = self.project(np.asarray(c, dtype=np.float64))
        rs = R * (f if persp else 1.0) * self.k
        bb = self._bbox(sx - rs - 1, sx + rs + 1, sy - rs - 1, sy + rs + 1)
        if bb is None:
            return
        i0, i1, j0, j1 = bb
        Y, X = np.mgrid[j0:j1, i0:i1].astype(F)
        X += 0.5; Y += 0.5
        ox = (X - sx) / rs; oy = (Y - sy) / rs
        d2 = ox * ox + oy * oy
        m = d2 < 1
        nz = np.sqrt(np.clip(1 - d2, 0, 1))
        z = (zc + R * nz).astype(F)
        self._write(j0, j1, i0, i1, m, shade(ox, oy, nz), alpha, z, X, Y, noknock=noknock)

    def knock(self, c, r, zmargin=0.0):
        sx, sy, zc, f = self.project(np.asarray(c, dtype=np.float64))
        self.knocks.append((sx, sy, r * f * self.k, zc + zmargin))

    def down(self):
        """average the samples down to px * px: premultiplied RGBA"""
        s = self.ss
        return self.col.reshape(self.px, s, self.px, s, 4).mean(axis=(1, 3))

    def grid(self, ss=1):
        """design coordinates of the output pixels (or ss sub-samples each) -> X, Y arrays"""
        n = self.px * ss
        v = (np.arange(n, dtype=F) + 0.5) / ss
        X = (v - self.ox / self.ss) * 1024.0 / (self.k / self.ss * 1024.0)
        Y = (v - self.oy / self.ss) * 1024.0 / (self.k / self.ss * 1024.0)
        return np.meshgrid(X, Y)


# ---------- materials ----------
def lit_ball(col, dark, L, hi=0.6, spec=0.0, stops=None):
    """a softly lit sphere (the nucleus, the electron): bright spot toward the light, the body colour, a darker limb"""
    L = norm(L)
    c_hi = mix(col, np.ones(3, dtype=F), hi)
    c_mid = col
    c_lo = mix(col, dark, 0.2)
    c_far = mix(col, dark, 0.46)
    H = norm(L + np.array([0, 0, 1.0]))

    def sh(nx, ny, nz):
        d = nx * L[0] + ny * L[1] + nz * L[2]
        t = (1 - d) * 0.5
        t = t[..., None]
        c = np.where(t < 0.2, mix(c_hi, c_mid, smooth(0.0, 0.2, t)),
                     np.where(t < 0.6, mix(c_mid, c_lo, (t - 0.2) / 0.4), mix(c_lo, c_far, (t - 0.6) / 0.4)))
        if spec:
            s = np.clip(nx * H[0] + ny * H[1] + nz * H[2], 0, 1) ** 60 * spec
            c = c + (1 - c) * s[..., None]
        return c.astype(F)
    return sh


def planet(col, night, L, hi=0.45, term=0.09, limb=0.25, rimcol=None):
    """a body lit by the Sun from direction L: a day side, a soft terminator, a night side that stays visible"""
    L = norm(L)
    c_hi = mix(col, np.ones(3, dtype=F), hi)

    def sh(nx, ny, nz):
        d = nx * L[0] + ny * L[1] + nz * L[2]
        day = smooth(-term, term, d)[..., None]
        dd = np.clip(d, 0, 1)[..., None]
        cday = mix(mix(col, night, 0.22), col, np.clip(dd * 1.6, 0, 1))
        cday = mix(cday, c_hi, smooth(0.72, 1.0, dd))
        cday = cday * (1 - limb * (1 - nz[..., None]) ** 2)
        c = mix(night, cday, day)
        if rimcol is not None:
            c = c + (rimcol - c) * ((1 - nz[..., None]) ** 3 * 0.5 * (1 - day))
        return c.astype(F)
    return sh


def tube_mat(lit, shadow, L, spec=0.0, wrap=0.35, edge=0.0, edgecol=None):
    """a round tube: its lit side in `lit`, the side away from the light toward `shadow`, an optional highlight"""
    L = norm(L)
    H = norm(L + np.array([0, 0, 1.0]))

    def sh(nx, ny, nz, u):
        d = nx * L[0] + ny * L[1] + nz * L[2]
        s = np.clip((d + wrap) / (1 + wrap), 0, 1)[..., None]
        c = mix(shadow, lit, s)
        if edge:
            c = mix(c, edgecol, (edge * (1 - nz) ** 2)[..., None])
        if spec:
            hl = np.clip(nx * H[0] + ny * H[1] + nz * H[2], 0, 1) ** 24 * spec
            c = c + (1 - c) * hl[..., None]
        return c.astype(F)
    return sh


# ---------- the tile ----------
def squircle_f(X, Y, n=5.0):
    """1 at the tile's edge, < 1 inside (superellipse of exponent n in the 0..1024 frame)"""
    x = np.abs(X - 512.0) / 512.0
    y = np.abs(Y - 512.0) / 512.0
    return (x ** n + y ** n) ** (1.0 / n)


def tile_mask(cv, ss=4):
    X, Y = cv.grid(ss)
    m = (squircle_f(X, Y) < 1.0).astype(F)
    return m.reshape(cv.px, ss, cv.px, ss).mean(axis=(1, 3))


def edge_dist(X, Y):
    """approximate distance (design units) from the tile edge, inward positive"""
    f = squircle_f(X, Y)
    e = 2.0
    gx = (squircle_f(X + e, Y) - squircle_f(X - e, Y)) / (2 * e)
    gy = (squircle_f(X, Y + e) - squircle_f(X, Y - e)) / (2 * e)
    g = np.sqrt(gx * gx + gy * gy) + 1e-6
    return (1.0 - f) / g


def blur(a, sigma):
    return ndimage.gaussian_filter(a, sigma, mode='constant')


def to_img(rgb, alpha=None, dither=True, seed=1):
    """float rgb (h,w,3) 0..1 (+ alpha) -> 8-bit, with half a step of noise so the dark gradients do not band"""
    from PIL import Image
    a = np.clip(rgb, 0, 1) * 255.0
    if dither:
        rng = np.random.default_rng(seed)
        a = a + (rng.random(a.shape[:2] + (1,), dtype=F) - 0.5) * 0.9
    a = np.clip(np.round(a), 0, 255).astype(np.uint8)
    if alpha is None:
        return Image.fromarray(a, 'RGB')
    al = np.clip(np.round(alpha * 255.0), 0, 255).astype(np.uint8)
    return Image.fromarray(np.dstack([a, al]), 'RGBA')
