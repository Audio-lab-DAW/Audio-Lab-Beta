#!/usr/bin/env python3
"""Task UX2: what today's screen asks of an OLED panel. From the screenshots of shoot_measure.py:
average picture level (APL: mean linear luminance, % of full white), the share of the screen that is bright, and the bright parts that never move
(bright in the frame and not in the 'changed while playing' mask): those are what ages one set of subpixels faster than the rest.
   python3 tools/design-lab/ux2/oled.py <out dir>      -> oled.json and oled-static-<mode>.png (bright static pixels in white)"""
import sys, json
import numpy as np
from PIL import Image
from scipy import ndimage

OUT = sys.argv[1] if len(sys.argv) > 1 else 'ux2-out'
def lin(c): c = c / 255; return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
res = {}
mov = np.asarray(Image.open(f'{OUT}/motion-playing.png')) > 0
for name in ('dark-arr', 'dark-mix', 'bright-arr', 'lite-arr'):
    im = np.asarray(Image.open(f'{OUT}/{name}.png').convert('RGB')).astype(float)
    L = lin(im); Y = L @ np.array([0.2126, 0.7152, 0.0722])
    sub = L.mean(axis=(0, 1))  # mean drive per channel (red, green, blue subpixels)
    r = {'apl_pct': round(float(Y.mean()) * 100, 2), 'over50_pct': round(float((Y > .5).mean()) * 100, 2), 'over25_pct': round(float((Y > .25).mean()) * 100, 2),
         'mean_drive_rgb_pct': [round(float(v) * 100, 2) for v in sub]}
    if name.startswith('dark-arr') or name.startswith('bright-arr') or name.startswith('lite-arr'):
        m = mov if mov.shape == Y.shape else np.zeros_like(Y, bool)
        st = (Y > .25) & ~ndimage.binary_dilation(m, iterations=4)
        lab, n = ndimage.label(ndimage.binary_dilation(st, iterations=3))
        objs = ndimage.find_objects(lab); big = []
        for i, sl in enumerate(objs):
            area = int((lab[sl] == i + 1).sum())
            if area > 2500: big.append({'x': sl[1].start / 1.75, 'y': sl[0].start / 1.75, 'w': (sl[1].stop - sl[1].start) / 1.75, 'h': (sl[0].stop - sl[0].start) / 1.75, 'area_px': area,
                                         'mean_Y_pct': round(float(Y[sl][st[sl]].mean()) * 100, 1) if st[sl].any() else 0})
        big.sort(key=lambda b: -b['area_px'])
        r['static_bright_pct'] = round(float(st.mean()) * 100, 2); r['static_bright_regions'] = big[:12]
        Image.fromarray((st * 255).astype(np.uint8)).resize((im.shape[1] // 2, im.shape[0] // 2)).save(f'{OUT}/oled-static-{name}.png')
    res[name] = r
    print(name, json.dumps({k: v for k, v in r.items() if k != 'static_bright_regions'}))
    for b in r.get('static_bright_regions', [])[:8]: print('   ', b)
json.dump(res, open(f'{OUT}/oled.json', 'w'), indent=1)
