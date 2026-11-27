#!/usr/bin/env python3
"""Task IC4: renders the shipped app icon and writes every file the app, the installers and the website use.
   python3 tools/icon-lab/ic4/ship.py            (needs node, rsvg-convert, Pillow, numpy)
Steps: node svgs.js -> out/svg; rsvg-convert -> out/png; then the files:
  desktop/icon-assets/icon.icns, icon.ico, icon.png, dock-icon.png, web-*.png, shortcut/ (kept as the W7 record, untouched)
  desktop/build/icon.icns, icon.ico, icon.png; desktop/dock-icon.png
  favicon-16/32/48.png, apple-touch-icon.png, icon-192.png, icon-512.png (website)
  desktop/icon-assets/picker/<id>.png (512, Apple margin), thumb/<id>.png (128), small/<id>-{16,32,48}.png, icons.json
  desktop/icon-assets/mac-icon/AppIcon.icon (via mac-icon/make_icon.py)
and out/compare-*.png (old against new) for the log."""
import io, json, os, shutil, struct, subprocess, sys
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
D = os.path.join(ROOT, 'desktop'); IA = os.path.join(D, 'icon-assets')
OUT = os.path.join(HERE, 'out'); SVG = os.path.join(OUT, 'svg'); PNG = os.path.join(OUT, 'png')
shutil.rmtree(OUT, ignore_errors=True); os.makedirs(PNG)
subprocess.run(['node', os.path.join(HERE, 'svgs.js'), SVG], check=True)
man = json.load(open(os.path.join(SVG, 'manifest.json')))
opts = man.pop('__options')
def render(name):
    px = man[name]; out = os.path.join(PNG, name + '.png')
    subprocess.run(['rsvg-convert', '-w', str(px), '-h', str(px), os.path.join(SVG, name + '.svg'), '-o', out], check=True)
    return out
files = {n: render(n) for n in man}
def raw(name): return open(files[name], 'rb').read()

# ---- keep the old files for the comparison sheets before anything is replaced
# the files as they were before IC4 (commit 3f4ea04, W7 on Ocean blue)
OLDREF = os.environ.get('IC4_OLD', '3f4ea04')
old = {k: subprocess.run(['git', '-C', ROOT, 'show', '%s:desktop/build/icon.%s' % (OLDREF, k)], stdout=subprocess.PIPE, check=True).stdout for k in ('ico', 'icns')}

# ---- size plans
def mac(px):      # Apple grid pictures for icon.icns
    if px <= 64: return 'j3s-mac-%d' % px
    return 'j3-mac-%d' % px
def full(px):     # edge-to-edge pictures for icon.ico and the website
    if px <= 64: return 'j3s-full-%d' % px
    return 'j3-full-%d' % px
for n in ['j3-mac-1024', 'j3-mac-512', 'j3-mac-256', 'j3-mac-128', 'j3s-mac-64', 'j3s-mac-32', 'j3s-mac-16']: assert n in man, n

def icns(out):
    # (type, pixels, picture): 16 and 32 pt at 1x and 2x from the small master; 128 pt and up J3
    plan = [('icp4', 16, 'j3s-mac-16'), ('ic11', 32, 'j3s-mac-32'), ('icp5', 32, 'j3s-mac-32'), ('ic12', 64, 'j3s-mac-64'),
            ('ic07', 128, 'j3-mac-128'), ('ic13', 256, 'j3-mac-256'), ('ic08', 256, 'j3-mac-256'), ('ic14', 512, 'j3-mac-512'),
            ('ic09', 512, 'j3-mac-512'), ('ic10', 1024, 'j3-mac-1024')]
    ch = b''
    for t, px, n in plan:
        d = raw(n); assert Image.open(io.BytesIO(d)).size == (px, px), (n, px)
        ch += t.encode() + struct.pack('>I', len(d) + 8) + d
    open(out, 'wb').write(b'icns' + struct.pack('>I', len(ch) + 8) + ch)
def ico(out, sizes=(16, 20, 24, 32, 40, 48, 64, 96, 128, 256)):
    imgs = [raw(full(s)) for s in sizes]
    hdr = struct.pack('<HHH', 0, 1, len(sizes)); off = 6 + 16 * len(sizes); ent = b''
    for s, d in zip(sizes, imgs):
        ent += struct.pack('<BBBBHHII', s % 256, s % 256, 0, 0, 1, 32, len(d), off); off += len(d)
    open(out, 'wb').write(hdr + ent + b''.join(imgs))
for n in ['j3-full-256', 'j3-full-128', 'j3-full-96']: assert n in man

icns(os.path.join(IA, 'icon.icns')); ico(os.path.join(IA, 'icon.ico'))
shutil.copy(files['j3-mac-1024'], os.path.join(IA, 'icon.png'))
shutil.copy(files['j3-mac-1024'], os.path.join(IA, 'dock-icon.png'))
for f in ('icon.icns', 'icon.ico', 'icon.png'): shutil.copy(os.path.join(IA, f), os.path.join(D, 'build', f))
shutil.copy(files['j3-mac-1024'], os.path.join(D, 'dock-icon.png'))
# the website: favicons from the small master, the bigger ones from J3, edge to edge as before
def resized(name, px):
    im = Image.open(files[name]).convert('RGBA')
    if im.size != (px, px): im = im.resize((px, px), Image.LANCZOS)
    b = io.BytesIO(); im.save(b, 'PNG', optimize=True); return b.getvalue()
web = {16: raw('j3s-full-16'), 32: raw('j3s-full-32'), 48: raw('j3s-full-48'), 180: resized('j3-full-256', 180), 192: resized('j3-full-256', 192), 512: raw('j3-full-512')}
for px, d in web.items(): open(os.path.join(IA, 'web-%d.png' % px), 'wb').write(d)
for name, px in [('favicon-16.png', 16), ('favicon-32.png', 32), ('favicon-48.png', 48), ('apple-touch-icon.png', 180), ('icon-192.png', 192), ('icon-512.png', 512)]:
    open(os.path.join(ROOT, name), 'wb').write(web[px])

# ---- the picker
PK = os.path.join(IA, 'picker'); os.makedirs(os.path.join(PK, 'small'), exist_ok=True)
for o in opts:
    i = o['id']
    shutil.copy(files['opt-%s-512' % i], os.path.join(PK, i + '.png'))
    shutil.copy(files['opt-%s-thumb' % i], os.path.join(PK, 'thumb', i + '.png'))
    for z in (16, 32, 48): shutil.copy(files['opt-%s-s%d' % (i, z)], os.path.join(PK, 'small', '%s-%d.png' % (i, z)))
J = json.load(open(os.path.join(PK, 'icons.json')))
J['groups'] = [g for g in J['groups'] if g.get('key') != 'dipole']
grp = {'key': 'dipole', 'name': 'Dipole field', 'icons': []}
for o in opts:
    grp['icons'].append({'id': o['id'], 'name': o['name'], 'file': o['id'] + '.png',
                         'small': {str(z): 'small/%s-%d.png' % (o['id'], z) for z in (16, 32, 48)},
                         'design_code': '%s %s' % (o['design'], o['palette'])})
J['groups'].insert(0, grp)
J['default'] = 'dipole-field'
# the default before IC4: a choice saved as this id before IC4 meant "the default" (see main.js savedIcon)
J['previous_default'] = 'ocean-yellow'
json.dump(J, open(os.path.join(PK, 'icons.json'), 'w'), indent=1); open(os.path.join(PK, 'icons.json'), 'a').write('\n')
n = sum(len(g['icons']) for g in J['groups']); print('picker:', n, 'icons, default', J['default'])

# ---- Icon Composer document
subprocess.run([sys.executable, os.path.join(IA, 'mac-icon', 'make_icon.py'), files['j3-layer-1024']], check=True)

# ---- comparison sheets for the log: old and new at 16 and 32, 1x and 2x
def ico_sizes(b):
    n = struct.unpack('<H', b[4:6])[0]; r = {}
    for k in range(n):
        w, h, _, _, _, _, ln, of = struct.unpack('<BBBBHHII', b[6 + 16 * k: 22 + 16 * k]); r[w or 256] = Image.open(io.BytesIO(b[of:of + ln])).convert('RGBA')
    return r
def icns_parts(b):
    r = {}; p = 8
    while p < len(b):
        t = b[p:p + 4].decode('latin1'); ln = struct.unpack('>I', b[p + 4:p + 8])[0]
        try: r[t] = Image.open(io.BytesIO(b[p + 8:p + ln])).convert('RGBA')
        except Exception: pass
        p += ln
    return r
from PIL import ImageDraw
def sheet(pairs, out, k=8, bg=(46, 48, 56)):
    # pairs: [(label, image)], each shown magnified (nearest) and at 1:1
    W = sum(im.size[0] * k + 24 for _, im in pairs) + 24; H = max(im.size[1] * k for _, im in pairs) + 120
    s = Image.new('RGBA', (W, H), bg + (255,)); d = ImageDraw.Draw(s); x = 24
    for lab, im in pairs:
        big = im.resize((im.size[0] * k, im.size[1] * k), Image.NEAREST); s.alpha_composite(big, (x, 16))
        s.alpha_composite(im, (x, 28 + big.size[1])); d.text((x, H - 40), lab, fill=(220, 222, 230)); x += big.size[0] + 24
    s.save(out)
oi, ni = ico_sizes(old['ico']), ico_sizes(open(os.path.join(IA, 'icon.ico'), 'rb').read())
on, nn = icns_parts(old['icns']), icns_parts(open(os.path.join(IA, 'icon.icns'), 'rb').read())
sheet([('old 32 (ico)', oi[32]), ('new 32 (ico)', ni[32]), ('old 16', oi[16]), ('new 16', ni[16])], os.path.join(OUT, 'compare-win-1x.png'), k=8)
sheet([('old 32@2x (icns)', on['ic12']), ('new 32@2x', nn['ic12']), ('old 16@2x', on['ic11']), ('new 16@2x', nn['ic11'])], os.path.join(OUT, 'compare-mac-2x.png'), k=4)
sheet([('old 32 (icns)', on['icp5']), ('new 32', nn['icp5']), ('old 16', on['icp4']), ('new 16', nn['icp4'])], os.path.join(OUT, 'compare-mac-1x.png'), k=8)
ladder = [(str(s), ni[s]) for s in (256, 128, 96, 64, 48, 40, 32, 24, 20, 16)]
lw = sum(im.size[0] + 16 for _, im in ladder) + 16; L = Image.new('RGBA', (lw, 300), (46, 48, 56, 255)); d = ImageDraw.Draw(L); x = 16
for lab, im in ladder: L.alpha_composite(im, (x, 16)); d.text((x, 280), lab, fill=(220, 222, 230)); x += im.size[0] + 16
L.save(os.path.join(OUT, 'ladder-ico.png'))
print('written; sheets in', OUT)
