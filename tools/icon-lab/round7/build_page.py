"""Builds the self-contained pick page (pick-page.html) from page.src.html: every picture of renders/ as a data URI
(run render7.py first) and the names of renders/manifest.json. REC holds the recommendations preselected on the page."""
import base64, json, os
d = os.path.dirname(os.path.abspath(__file__))
REC = dict(main='G7', other='G1', small='S1')
man = json.load(open(os.path.join(d, 'renders', 'manifest.json')))
man['rec'] = REC
MIME = {'.png': 'image/png', '.webp': 'image/webp'}
img = {}
for sub in ('big', 'small'):
    for fn in sorted(os.listdir(os.path.join(d, 'renders', sub))):
        k, ext = os.path.splitext(fn)
        if ext in MIME:
            img[k] = 'data:%s;base64,%s' % (MIME[ext], base64.b64encode(open(os.path.join(d, 'renders', sub, fn), 'rb').read()).decode())
s = open(os.path.join(d, 'page.src.html')).read()
s = s.replace('/*IMG*/{}', json.dumps(img), 1).replace('/*MAN*/{}', json.dumps(man), 1)
open(os.path.join(d, 'pick-page.html'), 'w').write(s)
print(len(s), 'bytes,', len(img), 'pictures')
