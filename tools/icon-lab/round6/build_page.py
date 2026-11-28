"""Builds the self-contained pick page (pick-page.html) from page.src.html: every picture of renders/manifest.json
as a data URI (run render6.py first), and the names and notes of designs6.py and small6.py."""
import base64, json, os
import designs6, small6
d = os.path.dirname(os.path.abspath(__file__))
man = json.load(open(os.path.join(d, 'renders', 'manifest.json')))
MIME = {'.png': 'image/png', '.webp': 'image/webp'}
img = {k: 'data:%s;base64,%s' % (MIME[os.path.splitext(rel)[1]], base64.b64encode(open(os.path.join(d, 'renders', rel), 'rb').read()).decode())
       for k, rel in man.items()}
des = {k: {f: v[f] for f in ('fam', 'name', 'short', 'note', 'star')} for k, v in designs6.DESIGNS.items()}
sml = {k: {'fam': v['fam'], 'name': v['name'], 'note': v['note'], 'star': v.get('star', False)} for k, v in small6.KS.items()}
s = open(os.path.join(d, 'page.src.html')).read()
s = s.replace('/*IMG*/{}', json.dumps(img), 1).replace('/*DES*/{}', json.dumps(des), 1).replace('/*SML*/{}', json.dumps(sml), 1)
open(os.path.join(d, 'pick-page.html'), 'w').write(s)
print(len(s), 'bytes,', len(img), 'pictures')
