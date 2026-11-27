#!/usr/bin/env python3
"""Writes the Icon Composer document for macOS 26: AppIcon.icon/icon.json and Assets/mark.png.
Task IC1 made it for W7 on Ocean blue; task IC4 (27 Nov 2026) makes it for J3, the dipole field in Orbit night (P2).

Run:  python3 tools/icon-lab/ic4/ship.py  (renders the layer and calls this), or
      python3 desktop/icon-assets/mac-icon/make_icon.py <J3 layer PNG, 1024 px, full bleed, square>   (needs Pillow, numpy)

What Icon Composer gets:
  - the fill: Orbit night's top colour #132044 (navy), written ONLY as fill-specializations, the same value for the default,
    the dark and the tinted appearance (IC1's lesson: with a plain 'fill' key beside them the dark entry is ignored and macOS
    draws its black tile). So Dark stays navy, never black.
  - one layer, mark.png, full bleed (macOS cuts the squircle and adds the margin itself): the whole J3 picture taken apart
    against the fill. Every pixel T of the picture becomes a colour C at opacity a with a*C + (1-a)*F = T exactly, with the
    smallest a that keeps C a real colour: the tile's gradient and glow become a faint layer (lighter or darker than the fill),
    the field lines, the rings at their 90 % (so the field still shows through them, as the user likes) and the nucleus and
    the electron come out nearly opaque. Laid over the fill the layer gives the picture back (checked below).
  - Tinted and Clear are the system's: it keeps the layer's shapes and brightness and replaces the colours."""
import json, os, sys
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, '..', '..', '..', 'tools', 'icon-lab', 'ic4', 'out', 'png', 'j3-layer-1024.png')
OUT = os.path.join(HERE, 'AppIcon.icon')
FILL = (0x13, 0x20, 0x44)
p = np.asarray(Image.open(SRC).convert('RGB')).astype(np.float64)
assert p.shape == (1024, 1024, 3), p.shape
F = np.array(FILL, dtype=np.float64)
# per channel, the opacity needed: toward white when lighter than the fill, toward black when darker
need = np.where(p >= F, (p - F) / (255.0 - F), (F - p) / F)
a = np.clip(need.max(axis=2), 0, 1)
with np.errstate(divide='ignore', invalid='ignore'):
    c = F + (p - F) / a[..., None]
c = np.where(a[..., None] > 1e-6, c, F)
rgba = np.dstack([np.clip(np.rint(c), 0, 255), np.rint(a * 255)]).astype(np.uint8)
os.makedirs(os.path.join(OUT, 'Assets'), exist_ok=True)
Image.fromarray(rgba, 'RGBA').save(os.path.join(OUT, 'Assets', 'mark.png'), optimize=True)
back = rgba[..., :3].astype(np.float64) * (rgba[..., 3:4] / 255.0) + F * (1 - rgba[..., 3:4] / 255.0)
worst = np.abs(back - p).max()
print('mark.png written; worst difference to the picture when laid over the fill: %.2f of 255' % worst)
assert worst <= 2.5, worst
fill = {'solid': 'srgb:%.5f,%.5f,%.5f,1.00000' % tuple(v / 255.0 for v in FILL)}
doc = {
    'fill-specializations': [
        {'value': fill},
        {'appearance': 'dark', 'value': fill},
        {'appearance': 'tinted', 'value': fill},
    ],
    'groups': [{
        'name': 'Mark',
        'layers': [{'name': 'mark', 'image-name': 'mark.png', 'glass': False, 'hidden': False, 'blend-mode': 'normal'}],
        'lighting': 'individual',
        'specular': False,
        'shadow': {'kind': 'none', 'opacity': 0.5},
        'translucency': {'enabled': False, 'value': 0.5},
    }],
    'supported-platforms': {'squares': ['macOS']},
}
json.dump(doc, open(os.path.join(OUT, 'icon.json'), 'w'), indent=2); open(os.path.join(OUT, 'icon.json'), 'a').write('\n')
print(open(os.path.join(OUT, 'icon.json')).read())
