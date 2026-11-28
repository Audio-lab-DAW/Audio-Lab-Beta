"""Colour maths for the theme checks (task TH1). No dependencies beyond the standard library.

WCAG 2.2 contrast ratio (relative luminance with the 0.04045 threshold), APCA 0.1.9 (SA98G constants from Myndex/apca-w3
src/apca-w3.js), OKLab / OKLCH, CIEDE2000 and the Machado, Oliveira and Fernandes 2009 colour-vision simulation (severity 1.0,
applied in linear RGB). The same formulas are in the pick page's script, so the page and docs/research-themes.md agree."""
import math

def hx(c):
    c = c.lstrip('#')
    if len(c) == 3: c = ''.join(ch * 2 for ch in c)
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))

def to_hex(rgb):
    return '#' + ''.join('%02X' % max(0, min(255, round(v))) for v in rgb)

def mix(a, b, t):
    """a over b at opacity t, in sRGB values as a browser composites"""
    A, B = hx(a), hx(b)
    return to_hex([A[i] * t + B[i] * (1 - t) for i in range(3)])

# ---------- WCAG 2 ----------
def _lin(v):
    v /= 255
    return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4

def rel_lum(c):
    r, g, b = (_lin(v) for v in hx(c))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b

def wcag(a, b):
    la, lb = rel_lum(a), rel_lum(b)
    if la < lb: la, lb = lb, la
    return (la + 0.05) / (lb + 0.05)

# ---------- APCA 0.1.9 (SA98G) ----------
def _apca_y(c):
    r, g, b = hx(c)
    return 0.2126729 * (r / 255) ** 2.4 + 0.7151522 * (g / 255) ** 2.4 + 0.0721750 * (b / 255) ** 2.4

def apca(txt, bg):
    """Lc of text colour txt on background bg; negative for light text on dark"""
    t, b = _apca_y(txt), _apca_y(bg)
    thr, clamp = 0.022, 1.414
    if t <= thr: t += (thr - t) ** clamp
    if b <= thr: b += (thr - b) ** clamp
    if abs(b - t) < 0.0005: return 0.0
    if b > t:
        s = (b ** 0.56 - t ** 0.57) * 1.14
        out = 0.0 if s < 0.1 else s - 0.027
    else:
        s = (b ** 0.65 - t ** 0.62) * 1.14
        out = 0.0 if s > -0.1 else s + 0.027
    return out * 100

# ---------- OKLab / OKLCH ----------
def _lin01(v):
    return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4

def _gam(v):
    return 12.92 * v if v <= 0.0031308 else 1.055 * v ** (1 / 2.4) - 0.055

def lin_rgb(c):
    return [_lin01(v / 255) for v in hx(c)]

def from_lin(rgb):
    return to_hex([_gam(max(0.0, min(1.0, v))) * 255 for v in rgb])

def oklab(c):
    r, g, b = lin_rgb(c)
    l = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
    m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
    s = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b
    l, m, s = (math.copysign(abs(x) ** (1 / 3), x) for x in (l, m, s))
    return (0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s,
            1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s,
            0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s)

def oklab_to_lin(L, a, b):
    l = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3
    m = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3
    s = (L - 0.0894841775 * a - 1.2914855480 * b) ** 3
    return [4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
            -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
            -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s]

def oklch(c):
    L, a, b = oklab(c)
    return L, math.hypot(a, b), math.degrees(math.atan2(b, a)) % 360

def from_oklch(L, C, h):
    """OKLCH to hex; chroma is reduced until the colour fits in sRGB"""
    for _ in range(40):
        a, b = C * math.cos(math.radians(h)), C * math.sin(math.radians(h))
        rgb = oklab_to_lin(L, a, b)
        if all(-1e-4 <= v <= 1.0001 for v in rgb): return from_lin(rgb)
        C *= 0.94
    return from_lin(oklab_to_lin(L, 0, 0))

def set_L(c, L):
    _, C, h = oklch(c)
    return from_oklch(L, C, h)

# ---------- CIEDE2000 ----------
def _lab(c):
    r, g, b = lin_rgb(c)
    X = (0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047
    Y = (0.2126 * r + 0.7152 * g + 0.0722 * b)
    Z = (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883
    f = lambda t: t ** (1 / 3) if t > 216 / 24389 else (24389 / 27 * t + 16) / 116
    fx, fy, fz = f(X), f(Y), f(Z)
    return 116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)

def de2000(c1, c2):
    L1, a1, b1 = _lab(c1); L2, a2, b2 = _lab(c2)
    C1, C2 = math.hypot(a1, b1), math.hypot(a2, b2)
    Cb = (C1 + C2) / 2
    G = 0.5 * (1 - math.sqrt(Cb ** 7 / (Cb ** 7 + 25 ** 7)))
    a1p, a2p = (1 + G) * a1, (1 + G) * a2
    C1p, C2p = math.hypot(a1p, b1), math.hypot(a2p, b2)
    h1p = math.degrees(math.atan2(b1, a1p)) % 360
    h2p = math.degrees(math.atan2(b2, a2p)) % 360
    dLp, dCp = L2 - L1, C2p - C1p
    if C1p * C2p == 0: dhp = 0
    else:
        dhp = h2p - h1p
        if dhp > 180: dhp -= 360
        elif dhp < -180: dhp += 360
    dHp = 2 * math.sqrt(C1p * C2p) * math.sin(math.radians(dhp / 2))
    Lbp, Cbp = (L1 + L2) / 2, (C1p + C2p) / 2
    if C1p * C2p == 0: hbp = h1p + h2p
    elif abs(h1p - h2p) <= 180: hbp = (h1p + h2p) / 2
    elif h1p + h2p < 360: hbp = (h1p + h2p + 360) / 2
    else: hbp = (h1p + h2p - 360) / 2
    T = (1 - 0.17 * math.cos(math.radians(hbp - 30)) + 0.24 * math.cos(math.radians(2 * hbp))
         + 0.32 * math.cos(math.radians(3 * hbp + 6)) - 0.20 * math.cos(math.radians(4 * hbp - 63)))
    dth = 30 * math.exp(-((hbp - 275) / 25) ** 2)
    Rc = 2 * math.sqrt(Cbp ** 7 / (Cbp ** 7 + 25 ** 7))
    Sl = 1 + 0.015 * (Lbp - 50) ** 2 / math.sqrt(20 + (Lbp - 50) ** 2)
    Sc, Sh = 1 + 0.045 * Cbp, 1 + 0.015 * Cbp * T
    Rt = -math.sin(math.radians(2 * dth)) * Rc
    return math.sqrt((dLp / Sl) ** 2 + (dCp / Sc) ** 2 + (dHp / Sh) ** 2 + Rt * (dCp / Sc) * (dHp / Sh))

# ---------- colour-vision deficiency (Machado 2009, severity 1.0, linear RGB) ----------
CVD = {
    'protan': [[0.152286, 1.052583, -0.204868], [0.114503, 0.786281, 0.099216], [-0.003882, -0.048116, 1.051998]],
    'deutan': [[0.367322, 0.860646, -0.227968], [0.280085, 0.672501, 0.047413], [-0.011820, 0.042940, 0.968881]],
    'tritan': [[1.255528, -0.076749, -0.178779], [-0.078411, 0.930809, 0.147602], [0.004733, 0.691367, 0.303900]],
}

def sim(c, kind):
    if kind == 'normal': return to_hex(hx(c))
    M, v = CVD[kind], lin_rgb(c)
    return from_lin([sum(M[i][j] * v[j] for j in range(3)) for i in range(3)])

def min_de(pal, kind='normal'):
    s = [sim(c, kind) for c in pal]
    best = (999, None)
    for i in range(len(s)):
        for j in range(i + 1, len(s)):
            d = de2000(s[i], s[j])
            if d < best[0]: best = (d, (pal[i], pal[j]))
    return best
