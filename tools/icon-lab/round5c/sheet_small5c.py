"""Magnified sheet of the small versions: python3 sheet_small5c.py out.png P2 -> each ES at 16, 16@2x, 20, 24, 32, 32@2x (real pixels, magnified)."""
import subprocess, sys, os, tempfile, json
from PIL import Image, ImageDraw
out, P = sys.argv[1], (sys.argv[2] if len(sys.argv) > 2 else 'P2')
d = os.path.dirname(os.path.abspath(__file__)); tmp = tempfile.mkdtemp()
cells = [(16, None, 8), (32, 16, 4), (20, None, 6), (24, None, 5), (32, None, 4), (64, 32, 2)]
ids = json.loads(subprocess.check_output(['node', '-e', "console.log(JSON.stringify(require('./small5c.js').IDS))"], cwd=d))
W = sum(px * k for px, pt, k in cells) + 20 * (len(cells) + 1); H = (128 + 36) * len(ids) + 20
im = Image.new('RGB', (W, H), (43, 45, 53) if P == 'P2' else (205, 210, 218)); dr = ImageDraw.Draw(im)
for r, sid in enumerate(ids):
    x = 20; y = 20 + r * 164
    for px, pt, k in cells:
        f = os.path.join(tmp, f'{sid}{px}{pt}.png')
        js = f"process.stdout.write(require('./small5c.js').smallSvg('{sid}','{P}',{px},'full',{{pt:{pt or px}}}))"
        svg = subprocess.check_output(['node', '-e', js], cwd=d)
        subprocess.run(['rsvg-convert', '-o', f], input=svg, check=True)
        t = Image.open(f).convert('RGBA').resize((px * k, px * k), Image.NEAREST)
        im.paste(t, (x, y), t); dr.text((x, y + 130), f'{sid} {pt or px}' + ('@2x' if pt else ''), fill=(220, 220, 230) if P == 'P2' else (30, 30, 40)); x += px * k + 20
im.save(out)
