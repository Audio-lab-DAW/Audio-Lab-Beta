"""Shrinks the renders: 256-colour palette PNGs (alpha kept). Run after render4.js."""
import glob, os
from PIL import Image
root = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'renders')
for f in glob.glob(root + '/**/*.png', recursive=True):
    im = Image.open(f).convert('RGBA')
    if im.width <= 64: continue
    im.quantize(256, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.FLOYDSTEINBERG).save(f, optimize=True)
