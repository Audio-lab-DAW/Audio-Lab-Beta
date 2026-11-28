"""Build the self-contained pick page of round 2: themes.json and the icons (128 px PNG data URIs) go into page.src.html.
  python3 check.py && python3 build.py   ->  pick-page.html"""
import json, os, base64, io
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
PICK = os.path.abspath(os.path.join(HERE, '..', '..', '..', 'desktop', 'icon-assets', 'picker'))
data = json.load(open(os.path.join(HERE, 'themes.json')))
for t in data['themes']:
    t.pop('src', None); t.pop('tune', None)
    for r in t['m']['rules']: r['worst'].pop('ok', None)
icons = {}
for t in data['themes']:
    for i in t['icons']:
        if i in icons: continue
        im = Image.open(os.path.join(PICK, i + '.png')).convert('RGBA').resize((128, 128), Image.LANCZOS)
        b = io.BytesIO(); im.save(b, 'PNG', optimize=True)
        icons[i] = 'data:image/png;base64,' + base64.b64encode(b.getvalue()).decode()
src = open(os.path.join(HERE, 'page.src.html')).read()
src = src.replace('/*@DATA@*/null', json.dumps(data, separators=(',', ':')))
src = src.replace('/*@ICONS@*/{}', json.dumps(icons, separators=(',', ':')))
open(os.path.join(HERE, 'pick-page.html'), 'w').write(src)
print('pick-page.html', len(src) // 1024, 'KB,', len(icons), 'icons')
