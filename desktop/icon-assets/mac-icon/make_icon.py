#!/usr/bin/env python3
"""Writes the Icon Composer document for macOS 26 (task IC1): AppIcon.icon/icon.json and Assets/mark.png.

Run from anywhere:  python3 desktop/icon-assets/mac-icon/make_icon.py   (needs rsvg-convert, Pillow, numpy)

The picture is the W7 shortcut icon (../shortcut/shortcut-L.svg) taken apart into what Icon Composer wants:
  - the tile colour (Ocean blue #1450A8) as the document's fill, the SAME for the default, dark and tinted appearance;
  - one layer, mark.png: the white rings and the yellow nucleus and electron on a transparent, full-bleed 1024 px canvas
    (no rounded corners, no margin, no shadow: macOS cuts the shape and adds the margin itself).
The blue in the source (the tile and the gap around the electron) becomes transparency exactly: every pixel of the source is
a mix a*C + (1-a)*blue with C white or yellow, and both have red = 255, so a = (R - 20) / 235.
"""
import io, json, os, re, subprocess
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, '..', 'shortcut', 'shortcut-L.svg')
OUT = os.path.join(HERE, 'AppIcon.icon')
BLUE = (0x14, 0x50, 0xA8)
svg = open(SRC).read()
# full-bleed: the rounded tile and its clip become a plain square
svg = svg.replace('<rect width="1024" height="1024" rx="230" fill="#1450A8"/>', '<rect width="1024" height="1024" fill="#1450A8"/>')
svg = svg.replace('<clipPath id="c"><rect width="1024" height="1024" rx="230"/></clipPath>', '<clipPath id="c"><rect width="1024" height="1024"/></clipPath>')
assert 'rx="230"' not in svg
png = subprocess.run(['rsvg-convert', '-w', '1024', '-h', '1024'], input=svg.encode(), stdout=subprocess.PIPE, check=True).stdout
p = np.asarray(Image.open(io.BytesIO(png)).convert('RGB')).astype(np.float64)
a = np.clip((p[..., 0] - BLUE[0]) / (255.0 - BLUE[0]), 0, 1)
blue = np.array(BLUE, dtype=np.float64)
with np.errstate(divide='ignore', invalid='ignore'):
    c = (p - (1 - a[..., None]) * blue) / a[..., None]
c = np.where(a[..., None] > 0, c, 255.0)
rgba = np.dstack([np.clip(np.rint(c), 0, 255), np.rint(a * 255)]).astype(np.uint8)
os.makedirs(os.path.join(OUT, 'Assets'), exist_ok=True)
Image.fromarray(rgba, 'RGBA').save(os.path.join(OUT, 'Assets', 'mark.png'), optimize=True)
# check: the layer over the blue gives the source back
back = rgba[..., :3].astype(np.float64) * (rgba[..., 3:4] / 255.0) + blue * (1 - rgba[..., 3:4] / 255.0)
print('mark.png written; worst difference to the source when laid over the blue: %.2f of 255' % np.abs(back - p).max())
fill = {'solid': 'srgb:%.5f,%.5f,%.5f,1.00000' % tuple(v / 255.0 for v in BLUE)}
doc = {
    # The fill is written ONLY as specializations: an entry without an appearance (the default) and the same value again for dark
    # and tinted. With a plain 'fill' key beside them the dark entry is not used and macOS falls back to its black tile (seen on CI).
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
