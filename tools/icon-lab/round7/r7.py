"""AudioLab app icon, round 7 (task IC11): the renderer.

Round 6 drew tubes with an exaggerated taper. Round 7 draws a small real scene, in Earth radii, through one true
perspective camera, with one Sun:

  Cam      : eye, target, focal length -> screen position, depth, scale
  Canvas   : px * ss samples; an opaque layer with a depth buffer (spheres, tubes), then march() carries the see-through
             things (the belts, the magnetopause) as volumes along every sample's ray, stopping at the opaque depth
  sphere() : a lit ball (the Earth, the Moon); the shader also gets the world normal (for the globe's graticule)
  tube()   : a round tube round a curve in space (field lines, the Moon's orbit): width by true perspective only
  march()  : front-to-back emission and absorption; a belt is denser near its skin, so it reads as a lit glass shell
             (bright rim, see-through middle) and a cutaway shows its crescent section

Only numpy, scipy.ndimage and Pillow are needed.
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


def rot(ax, deg):
    a = np.radians(deg); c, s = np.cos(a), np.sin(a)
    if ax == 'x':
        return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
    if ax == 'y':
        return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


class Cam:
    """world: x right, y up, z toward the viewer (Earth radii). az turns the eye round y, el lifts it."""
    def __init__(self, dist=14.0, az=0.0, el=20.0, target=(0, 0, 0), f=2400.0, c=(512.0, 512.0), roll=0.0):
        a, e = np.radians(az), np.radians(el)
        self.target = np.asarray(target, dtype=np.float64)
        self.eye = self.target + dist * np.array([np.sin(a) * np.cos(e), np.sin(e), np.cos(a) * np.cos(e)])
        self.fwd = norm(self.target - self.eye)
        r = norm(np.cross(self.fwd, [0, 1, 0])); u = np.cross(r, self.fwd)
        if roll:
            q = np.radians(roll)
            r, u = r * np.cos(q) + u * np.sin(q), u * np.cos(q) - r * np.sin(q)
        self.right, self.up = r, u
        self.f, self.c, self.dist = f, c, dist

    def project(self, p):
        d = np.asarray(p, dtype=np.float64) - self.eye
        w = d @ self.fwd
        x = self.c[0] + self.f * (d @ self.right) / w
        y = self.c[1] - self.f * (d @ self.up) / w
        return x, y, w, self.f / w

    def to_cam(self, v):
        """a world direction in screen axes (x right, y down, z toward the viewer)"""
        v = np.asarray(v, dtype=np.float64)
        return np.array([v @ self.right, -(v @ self.up), -(v @ self.fwd)])

    def px(self, n):
        """n design units at the target's depth, in Earth radii"""
        return n * self.dist / self.f


class Canvas:
    def __init__(self, px, ss, cam, tile=None):
        self.px, self.ss, self.cam = px, ss, cam
        self.N = px * ss
        tx, ty, ts = tile if tile else (0.0, 0.0, float(px))
        self.k = ts / 1024.0 * ss
        self.ox, self.oy = tx * ss, ty * ss
        self.col = np.zeros((self.N, self.N, 3), dtype=F)
        self.cov = np.zeros((self.N, self.N), dtype=bool)
        self.z = np.full((self.N, self.N), 1e9, dtype=F)
        self.fields = []

    def project(self, p):
        x, y, w, s = self.cam.project(p)
        return x * self.k + self.ox, y * self.k + self.oy, w, s * self.k

    def _bbox(self, x0, x1, y0, y1):
        i0 = max(0, int(np.floor(x0))); i1 = min(self.N, int(np.ceil(x1)) + 1)
        j0 = max(0, int(np.floor(y0))); j1 = min(self.N, int(np.ceil(y1)) + 1)
        if i1 <= i0 or j1 <= j0:
            return None
        return i0, i1, j0, j1

    def _put(self, j0, j1, i0, i1, m, rgb, z):
        zb = self.z[j0:j1, i0:i1]
        m = m & (z < zb)
        if m.any():
            self.col[j0:j1, i0:i1][m] = rgb[m]
            zb[m] = z[m]
            self.cov[j0:j1, i0:i1][m] = True

    def sphere(self, c, R, shade):
        """shade(n_screen (3 arrays), n_world (..,3)) -> rgb"""
        sx, sy, w, s = self.project(c)
        rs = R * s
        bb = self._bbox(sx - rs - 1, sx + rs + 1, sy - rs - 1, sy + rs + 1)
        if bb is None:
            return
        i0, i1, j0, j1 = bb
        Y, X = np.mgrid[j0:j1, i0:i1].astype(F)
        ox = (X + 0.5 - sx) / rs; oy = (Y + 0.5 - sy) / rs
        d2 = ox * ox + oy * oy
        m = d2 < 1
        nz = np.sqrt(np.clip(1 - d2, 0, 1))
        cm = self.cam
        nw = ox[..., None] * cm.right - oy[..., None] * cm.up - nz[..., None] * cm.fwd
        self._put(j0, j1, i0, i1, m, shade(ox, oy, nz, nw).astype(F), (w - R * nz).astype(F))

    def tube(self, pts, rad, shade, minr=0.0):
        """pts (n,3) world; rad world radius (scalar or (n,)); minr: smallest radius in output pixels.
        shade(nx, ny, nz, u, w) -> rgb, u the place along the tube 0..1, w the depth"""
        pts = np.asarray(pts, dtype=np.float64)
        n = len(pts)
        sx, sy, ws, s = self.project(pts)
        ok = ws > 0.2
        rw = np.broadcast_to(np.asarray(rad, dtype=np.float64), (n,))
        rs = np.maximum(rw * s, minr * self.ss)
        uu = np.linspace(0, 1, n)
        for i in range(n - 1):
            if not (ok[i] and ok[i + 1]):
                continue
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
            ox = (X - (ax + t * dx)) / rr; oy = (Y - (ay + t * dy)) / rr
            q = ox * ox + oy * oy
            m = q < 1
            if not m.any():
                continue
            nz = np.sqrt(np.clip(1 - q, 0, 1))
            wc = ws[i] + t * (ws[i + 1] - ws[i])
            rwc = rw[i] + t * (rw[i + 1] - rw[i])
            z = (wc - rwc * nz).astype(F)
            self._put(j0, j1, i0, i1, m, shade(ox, oy, nz, uu[i] + t * (uu[i + 1] - uu[i]), wc).astype(F), z)

    def march(self, bound, steps=72, seed=3):
        """the see-through things: self.fields = [f(P (..,3)) -> (sigma (..), rgb (..,3) or (3,))], inside the sphere
        `bound` round the origin. Returns premultiplied RGBA (N, N, 4) of everything (volumes over the opaque layer)."""
        N, cm = self.N, self.cam
        out = np.zeros((N, N, 4), dtype=F)
        cov = self.cov.astype(F)
        if not self.fields:
            out[..., :3] = self.col * cov[..., None]; out[..., 3] = cov
            return out
        rng = np.random.default_rng(seed)
        e = cm.eye.astype(F)
        ee = float(e @ e)
        xs = ((np.arange(N, dtype=F) + 0.5 - self.ox) / self.k - cm.c[0]) / cm.f
        CH = max(8, int(3.0e5 // N))
        for j0 in range(0, N, CH):
            j1 = min(N, j0 + CH)
            ys = -((np.arange(j0, j1, dtype=F) + 0.5 - self.oy) / self.k - cm.c[1]) / cm.f
            d = (xs[None, :, None] * cm.right.astype(F) + ys[:, None, None] * cm.up.astype(F) + cm.fwd.astype(F))
            dd = (d * d).sum(-1); de = d @ e
            disc = de * de - dd * (ee - bound * bound)
            hit = disc > 0
            sq = np.sqrt(np.maximum(disc, 0))
            t0 = np.maximum((-de - sq) / dd, 0.05); t1 = (-de + sq) / dd
            zb = self.z[j0:j1]
            t1 = np.minimum(t1, zb)
            hit &= t1 > t0
            T = np.ones(t0.shape, dtype=F); C = np.zeros(t0.shape + (3,), dtype=F)
            if hit.any():
                dh = d[hit]; t0h = t0[hit]
                dt = (t1[hit] - t0h) / steps
                ln = dt * np.sqrt(dd[hit])
                jit = rng.random(t0h.shape, dtype=F)
                Th = np.ones(t0h.shape, dtype=F); Ch = np.zeros(t0h.shape + (3,), dtype=F)
                for i in range(steps):
                    t = t0h + (i + jit) * dt
                    P = e + dh * t[..., None]
                    sig = np.zeros(t0h.shape, dtype=F); cc = np.zeros(t0h.shape + (3,), dtype=F)
                    for f in self.fields:
                        s_, c_ = f(P)
                        sig += s_; cc += s_[..., None] * c_
                    a = 1 - np.exp(-sig * ln)
                    Ch += (Th * a / np.maximum(sig, 1e-6))[..., None] * cc
                    Th *= 1 - a
                T[hit] = Th; C[hit] = Ch
            cv_ = cov[j0:j1]
            out[j0:j1, :, :3] = C + (T * cv_)[..., None] * self.col[j0:j1]
            out[j0:j1, :, 3] = 1 - T * (1 - cv_)
        return out

    def down(self, a):
        s = self.ss
        return a.reshape(self.px, s, self.px, s, -1).mean(axis=(1, 3))

    def grid(self, ss=1):
        """design coordinates (the tile's 0..1024 frame) of the output pixels"""
        n = self.px * ss
        v = (np.arange(n, dtype=F) + 0.5) / ss
        return np.meshgrid((v - self.ox / self.ss) * self.ss / self.k, (v - self.oy / self.ss) * self.ss / self.k)


# ---------- materials ----------
def planet(col, night, L, hi=0.4, term=0.10, limb=0.3, rim=None, amb=0.0):
    """a body in sunlight from L (screen axes): day side, soft terminator, a night side that stays visible"""
    L = norm(L); c_hi = mix(col, np.ones(3, dtype=F), hi)

    def sh(nx, ny, nz, nw=None):
        d = nx * L[0] + ny * L[1] + nz * L[2]
        day = smooth(-term, term * 1.6, d)[..., None]
        dd = np.clip(d, 0, 1)[..., None]
        c = mix(mix(col, night, 0.25), col, np.clip(dd * 1.7, 0, 1))
        c = mix(c, c_hi, smooth(0.62, 1.0, dd) * 0.9)
        c = c * (1 - limb * (1 - nz[..., None]) ** 2.2)
        c = mix(mix(night, col, amb), c, day)
        if rim is not None:
            c = c + (rim - c) * ((1 - nz[..., None]) ** 3.5 * 0.55 * (1 - day))
        return c
    return sh


def tube_mat(near, far, L, w0, w1, wrap=0.45, shade=0.45, dark=None):
    """a lit round tube whose value falls with distance: `near` at depth w0, `far` at depth w1 (depth by value)"""
    L = norm(L)
    dark = far * 0.5 if dark is None else dark

    def sh(nx, ny, nz, u, w):
        d = nx * L[0] + ny * L[1] + nz * L[2]
        s = np.clip((d + wrap) / (1 + wrap), 0, 1)[..., None]
        base = mix(near, far, smooth(w0, w1, w)[..., None])
        return mix(mix(base, dark, shade), base, s)
    return sh


# ---------- volumes ----------
def belt(axis, L1, L2, lat, col, rimcol, dens, rim, skin=0.10, cut=None, capcol=None, cap=0.0, e1=None, light=None,
         lk=0.32, capw=0.09, window=None):
    """a radiation belt: the space between the dipole shells L1 and L2 (r = L cos^2(latitude)) up to the magnetic
    latitude `lat`; denser in a skin under its surface. cut=(a0, a1): the longitudes (degrees round the axis, from e1)
    taken away, their cut faces capped."""
    a = norm(axis).astype(F)
    if e1 is None:
        e1 = np.cross(a, [0, 0, 1.0])
    e1 = norm(e1 - (e1 @ a) * a).astype(F); e2 = np.cross(a, e1).astype(F)
    cmin = np.cos(np.radians(lat)) ** 2
    col = np.asarray(col, dtype=F); rimcol = np.asarray(rimcol, dtype=F)
    capcol = rimcol if capcol is None else np.asarray(capcol, dtype=F)
    lt = None if light is None else norm(light).astype(F)
    wv = None if window is None else norm(window[0]).astype(F)   # window = (toward the eye, r0, r1, strength)

    def f(P):
        z = P @ a
        r2 = (P * P).sum(-1)
        c2 = 1 - z * z / np.maximum(r2, 1e-6)
        r = np.sqrt(r2)
        Lv = r / np.maximum(c2, 1e-3)
        d = np.minimum(np.minimum(Lv - L1, L2 - Lv) * c2, (c2 - cmin) * r * 1.2)
        ins = smooth(0.0, 0.035, d)
        sk = np.exp(-(d / skin) ** 2)
        sig = ins * (dens + rim * sk)
        t = sk[..., None]
        c = col + (rimcol - col) * t
        if light is not None:
            c = c * (1 + lk * ((P @ lt) / np.maximum(r, 1e-6)))[..., None]
        if window is not None:
            tv = P @ wv
            perp = np.sqrt(np.maximum(r2 - tv * tv, 0))
            sig = sig * (1 - window[3] * smooth(window[2], window[1], perp) * (tv > 0))
        if cut is not None:
            ph = np.degrees(np.arctan2(P @ e2, P @ e1))
            mid = (cut[0] + cut[1]) / 2; half = (cut[1] - cut[0]) / 2
            dp = np.abs((ph - mid + 180) % 360 - 180) - half           # < 0 inside the cut
            rho = np.sqrt(np.maximum(r2 - z * z, 1e-6))
            dist = np.radians(dp) * rho                                  # distance from the cut face, outside positive
            sig = sig * (dist > 0)
            if cap:
                k = np.exp(-(dist / capw) ** 2) * ins * (dist > 0)
                sig = sig + cap * k
                c = c + (capcol - c) * (k / (k + 0.25))[..., None]
        return sig.astype(F), c.astype(F)
    return f


def shell(rfun, sunward, col, dens, width=0.12, xfade=None):
    """a thin see-through surface r = rfun(cos theta), theta from the sunward axis (the magnetopause)"""
    sdir = norm(sunward).astype(F); col = np.asarray(col, dtype=F)

    def f(P):
        r = np.sqrt((P * P).sum(-1))
        x = P @ sdir
        ct = x / np.maximum(r, 1e-6)
        sig = dens * np.exp(-((r - rfun(ct)) / width) ** 2)
        if xfade is not None:
            sig = sig * smooth(xfade[0], xfade[1], x)
        return sig.astype(F), col
    return f


# ---------- the tile ----------
def squircle_f(X, Y, n=5.0):
    x = np.abs(X - 512.0) / 512.0; y = np.abs(Y - 512.0) / 512.0
    return (x ** n + y ** n) ** (1.0 / n)


def tile_mask(cv, ss=4):
    X, Y = cv.grid(ss)
    m = (squircle_f(X, Y) < 1.0).astype(F)
    return m.reshape(cv.px, ss, cv.px, ss).mean(axis=(1, 3))


def edge_dist(X, Y):
    f = squircle_f(X, Y); e = 2.0
    gx = (squircle_f(X + e, Y) - squircle_f(X - e, Y)) / (2 * e)
    gy = (squircle_f(X, Y + e) - squircle_f(X, Y - e)) / (2 * e)
    return (1.0 - f) / (np.sqrt(gx * gx + gy * gy) + 1e-6)


def blur(a, sigma):
    return ndimage.gaussian_filter(a, sigma, mode='constant')


def to_img(rgb, alpha=None, dither=True, seed=1):
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
