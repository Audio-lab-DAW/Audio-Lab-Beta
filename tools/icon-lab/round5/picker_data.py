"""Collects today's in-app icon picker (desktop/icon-assets/picker/icons.json) for the keep-or-remove review:
every icon with its group, name, design code, its 128 px thumbnail (thumb/<id>.png, as the picker shows it) and a
32 px picture (small/<id>-32.png where IC6 drew one, otherwise the 512 px picture reduced with Lanczos, as the
desktop shell does for the window and taskbar). Writes picker-review.json (data URIs) next to this file."""
import base64, io, json, os
from PIL import Image
d = os.path.dirname(os.path.abspath(__file__))
pk = os.path.join(d, '..', '..', '..', 'desktop', 'icon-assets', 'picker')
j = json.load(open(os.path.join(pk, 'icons.json')))
def uri(im):
    b = io.BytesIO(); im.save(b, 'PNG', optimize=True); return 'data:image/png;base64,' + base64.b64encode(b.getvalue()).decode()
groups = []
for g in j['groups']:
    out = []
    for ic in g['icons']:
        t = Image.open(os.path.join(pk, 'thumb', ic['id'] + '.png')).convert('RGBA')
        sp = os.path.join(pk, 'small', ic['id'] + '-32.png')
        s32 = Image.open(sp).convert('RGBA') if os.path.exists(sp) else Image.open(os.path.join(pk, ic['file'])).convert('RGBA').resize((32, 32), Image.LANCZOS)
        out.append({'id': ic['id'], 'name': ic['name'], 'code': ic.get('design_code', ''), 'added': ic.get('added', ''), 'own32': os.path.exists(sp), 't128': uri(t), 't32': uri(s32)})
    groups.append({'key': g['key'], 'name': g['name'], 'icons': out})
json.dump({'default': j['default'], 'groups': groups}, open(os.path.join(d, 'picker-review.json'), 'w'))
print(sum(len(g['icons']) for g in groups), 'icons', os.path.getsize(os.path.join(d, 'picker-review.json')))
