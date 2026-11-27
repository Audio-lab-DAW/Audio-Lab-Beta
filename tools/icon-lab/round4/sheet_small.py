"""renders/sheet-small.png: IC4's small master and S1 to S4 in P2 and P8 at real pixels, magnified 6 times
(16 pt and 32 pt at 1x; their 2x versions magnified 3 times, so each pair shows at the same size), then at 1x."""
import os
from PIL import Image, ImageDraw
d = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'renders', 'small')
rows = [(i, p) for i in ['IC4', 'S1', 'S2', 'S3', 'S4'] for p in ['P2', 'P8']]
cells = [('16', 6), ('32-at16', 3), ('32', 6), ('64-at32', 3)]
W = 8 + 96 + 12 + 96 + 12 + 192 + 12 + 192 + 12 + 16 + 8 + 32 + 8 + 90
im = Image.new('RGB', (W, len(rows) * 204 + 8), (43, 45, 53)); dr = ImageDraw.Draw(im); y = 8
for i, p in rows:
    x = 8
    for name, k in cells:
        t = Image.open(f'{d}/{i}-{p}-{name}.png').convert('RGBA'); t2 = t.resize((t.width * k, t.height * k), Image.NEAREST)
        im.paste(t2, (x, y), t2); x += t2.width + 12
    for name in ('16', '32'):
        t = Image.open(f'{d}/{i}-{p}-{name}.png').convert('RGBA'); im.paste(t, (x, y), t); x += t.width + 8
    dr.text((x + 4, y + 40), f'{i} {p}', fill=(220, 220, 220)); y += 204
im.save(os.path.join(os.path.dirname(d), 'sheet-small.png'))
