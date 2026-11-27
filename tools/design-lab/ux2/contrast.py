#!/usr/bin/env python3
"""Task UX2: contrast of every visible text in today's app (WCAG 2 ratio and APCA Lc), from shoot_measure.py's text-<mode>.json,
plus the colour pairs drawn on canvases (ruler, grid labels, displays), taken from the code (LOOK, TH, INS).
   python3 tools/design-lab/ux2/contrast.py <out dir>      -> <out dir>/contrast.json and a printed summary
APCA: the APCA-W3 0.0.98G-4g constants (Myndex/apca-w3). WCAG: relative luminance with the sRGB curve.
Physical size on the user's screen: 32 inch 16:9 panel, 3840 px over 708.5 mm = 0.1845 mm per device pixel; 1.75 device px per CSS px."""
import sys, json, re, math, collections

OUT = sys.argv[1] if len(sys.argv) > 1 else 'ux2-out'

def parse(c):
    m = re.match(r'rgba?\(([^)]+)\)', c.strip())
    if m:
        v = [float(x) for x in re.split(r'[ ,/]+', m.group(1).strip()) if x]
        return v[:3], (v[3] if len(v) > 3 else 1.0)
    c = c.lstrip('#')
    if len(c) == 3: c = ''.join(ch * 2 for ch in c)
    return [int(c[i:i + 2], 16) for i in (0, 2, 4)], (int(c[6:8], 16) / 255 if len(c) == 8 else 1.0)

def over(fg, a, bg): return [f * a + b * (1 - a) for f, b in zip(fg, bg)]

def rl(c):
    def ch(v):
        v /= 255
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(x) for x in c)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b

def wcag(a, b):
    la, lb = rl(a), rl(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)

def apca(txt, bg):
    def y(c):
        r, g, b = (x / 255 for x in c)
        return 0.2126729 * r ** 2.4 + 0.7151522 * g ** 2.4 + 0.0721750 * b ** 2.4
    def clamp(v): return v if v > 0.022 else v + (0.022 - v) ** 1.414
    yt, yb = clamp(y(txt)), clamp(y(bg))
    if abs(yb - yt) < 0.0005: return 0.0
    if yb > yt:
        s = (yb ** 0.56 - yt ** 0.57) * 1.14
        return 0.0 if s < 0.1 else (s - 0.027) * 100
    s = (yb ** 0.65 - yt ** 0.62) * 1.14
    return 0.0 if s > -0.1 else (s + 0.027) * 100

# APCA "Bronze/Silver" font lookup (APCA-W3 0.1.9 table, min Lc for content text) for weights 400, 500, 600 by px size
LUT = {  # px: (w400, w500, w600, w700)
    10: (None, None, None, None), 11: (None, None, None, None), 12: (None, None, None, None),
    14: (100, 100, 90, 75), 15: (100, 90, 75, 70), 16: (90, 75, 70, 60), 18: (75, 70, 60, 55), 21: (70, 60, 55, 50), 24: (60, 55, 50, 45)}

MMPX = 708.5 / 3840 * 1.75  # mm per CSS px on the user's screen
DIST = 700  # mm, a typical viewing distance for a 32 inch screen at a desk

def arcmin(mm): return math.degrees(math.atan(mm / DIST)) * 60

import numpy as np
from PIL import Image
D = 1.75
def sample_bg(img, it, fg):
    """background behind a text run: the most common colour in the text box plus a 1 px ring, leaving out pixels close to the text colour
    (glyph cores and their anti-aliased edges), quantised in steps of 4"""
    x0, y0 = int(max(0, (it['x'] - 1) * D)), int(max(0, (it['y'] - 1) * D))
    x1, y1 = int(min(img.shape[1], (it['x'] + it['w'] + 1) * D)), int(min(img.shape[0], (it['y'] + it['h'] + 1) * D))
    if x1 - x0 < 2 or y1 - y0 < 2: return None
    reg = img[y0:y1, x0:x1].reshape(-1, 3).astype(np.int32)
    far = np.abs(reg - np.array(fg)).max(axis=1) > 48
    if far.sum() < 6: return None
    reg = reg[far]
    q = reg // 4; keys = q[:, 0] * 65536 + q[:, 1] * 256 + q[:, 2]
    vals, cnt = np.unique(keys, return_counts=True); k = vals[cnt.argmax()]
    return [int(v) for v in reg[keys == k].mean(axis=0)]

def analyse(mode):
    items = json.load(open(f'{OUT}/text-{mode}.json'))
    imgs = {v: np.asarray(Image.open(f'{OUT}/{mode}-{v}.png').convert('RGB')) for v in ('arr', 'mix')}
    rows = []
    for it in items:
        fg, a = parse(it['c'])
        it['bg'] = sample_bg(imgs['mix' if it.get('view') == 'mixer' else 'arr'], it, fg)
        if not it.get('bg'): continue
        fgc = over(fg, a * it.get('o', 1), it['bg'])
        rows.append(dict(t=it['t'], id=it['id'], cls=it['cls'], view=it.get('view', 'arr'), fs=round(it['fs'], 2), fw=it['fw'],
                         fg=[round(x) for x in fgc], bg=it['bg'], wcag=round(wcag(fgc, it['bg']), 2), lc=round(apca(fgc, it['bg']), 1)))
    return rows

CANVAS = [  # name, fg, bg, px, weight   (from LOOK, TH defaults with bgL 40, INS)
    ('ruler bar numbers (TH.rulerTxt on TH.ruler)', 'hsl', None, 11, 500),
    ('LOOK.mut on display black #0b0c10', '#8b8b97', '#0b0c10', 10, 500),
    ('LOOK.lab on display black', '#b7b7c2', '#0b0c10', 10, 500),
    ('LOOK.tick (rgba 255 .32) labels on display black', 'rgba(255,255,255,.32)', '#0b0c10', 9, 500),
    ('LOOK.unit amber on display black', '#ffb547', '#0b0c10', 10, 600),
    ('LOOK.ink on panel #121216', '#ececf1', '#121216', 12, 400),
    ('--mut on panel #121216', '#8b8b97', '#121216', 11, 400),
    ('--mut on --pn2 #18181d', '#8b8b97', '#18181d', 11, 400),
    ('--ov-mut on menu glass (about #1b1d24)', '#8b8b97', '#1b1d24', 11, 400),
    ('clip title white on clip (blue at clipA 36 over lane)', '#ffffff', 'clipblue', 11, 600),
    ('selection yellow #f5c84c on lane', '#f5c84c', 'lane', 11, 600),
    ('over red #ff6b6b on display black', '#ff6b6b', '#0b0c10', 10, 600),
]

def hsl(h, s, l):
    import colorsys
    r, g, b = colorsys.hls_to_rgb(h / 360, l / 100, s / 100)
    return [r * 255, g * 255, b * 255]

def canvas_pairs():
    H, sat, b = 215, round(.25 * 45), 12.0
    lane = hsl(H, sat, b + 1); ruler = hsl(H, sat, b + 5); rtx = hsl(H, sat, max(70, b + 55))
    clip = over([0x4c, 0x8d, 0xff], .36, lane)
    out = []
    for n, f, bg, px, w in CANVAS:
        if f == 'hsl': fg, bgc = rtx, ruler
        else:
            fc, a = parse(f)
            bgc = lane if bg == 'lane' else clip if bg == 'clipblue' else parse(bg)[0]
            fg = over(fc, a, bgc)
        out.append(dict(t=n, fs=px, fw=w, fg=[round(x) for x in fg], bg=[round(x) for x in bgc], wcag=round(wcag(fg, bgc), 2), lc=round(apca(fg, bgc), 1)))
    return out

res = {}
for mode in ('dark', 'lite', 'bright'):
    try: rows = analyse(mode)
    except FileNotFoundError: continue
    n = len(rows)
    lt45 = [r for r in rows if r['wcag'] < 4.5]; lt3 = [r for r in rows if r['wcag'] < 3]
    lc60 = [r for r in rows if abs(r['lc']) < 60]; lc45 = [r for r in rows if abs(r['lc']) < 45]; lc30 = [r for r in rows if abs(r['lc']) < 30]
    sizes = collections.Counter(round(r['fs'] * 2) / 2 for r in rows)
    # unique worst pairs
    seen, worst = set(), []
    for r in sorted(rows, key=lambda r: abs(r['lc'])):
        k = (tuple(r['fg']), tuple(r['bg']))
        if k in seen: continue
        seen.add(k); worst.append(r)
        if len(worst) >= 25: break
    res[mode] = dict(n=n, wcag_lt_4_5=len(lt45), wcag_lt_3=len(lt3), apca_lt_60=len(lc60), apca_lt_45=len(lc45), apca_lt_30=len(lc30),
                     sizes=sorted(sizes.items()), smallest=sorted(rows, key=lambda r: r['fs'])[:12], worst=worst,
                     median_lc=sorted(abs(r['lc']) for r in rows)[n // 2] if n else None)
    print(f'== {mode}: {n} text runs; WCAG <4.5: {len(lt45)} ({len(lt45)/n:.0%}), <3: {len(lt3)}; |Lc|<60: {len(lc60)} ({len(lc60)/n:.0%}), <45: {len(lc45)}, <30: {len(lc30)}; median |Lc| {res[mode]["median_lc"]}')
    print('   sizes (px: count):', sorted(sizes.items()))
    for r in worst[:12]: print(f'   Lc {r["lc"]:6.1f}  {r["wcag"]:5.2f}:1  {r["fs"]}px/{r["fw"]}  fg{r["fg"]} bg{r["bg"]}  "{r["t"]}" #{r["id"]} .{r["cls"]}')
res['canvas'] = canvas_pairs()
print('== canvas pairs')
for r in res['canvas']: print(f'   Lc {r["lc"]:6.1f}  {r["wcag"]:5.2f}:1  {r["fs"]}px  {r["t"]}')
sz = {}
for px in (9, 9.5, 10, 11, 12, 13, 15):
    xh = px * 0.546 * MMPX  # Inter x-height 0.546 em
    sz[px] = dict(device_px=round(px * 1.75, 1), cap_mm=round(px * 0.727 * MMPX, 2), xheight_mm=round(xh, 2), xheight_arcmin=round(arcmin(xh), 1))
res['physical'] = sz
print('== physical size at 70 cm:', json.dumps(sz))
json.dump(res, open(f'{OUT}/contrast.json', 'w'), indent=1)
