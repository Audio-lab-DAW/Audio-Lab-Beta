"""Pull the AudioLab atom geometry (three tapered rings, nucleus, electron) out of the
shipped icon sources, so round 2 draws the exact same mark. Writes geom.json.
Tiers L/M/S/XS come from desktop/icon-assets/source/icon-*.svg (normal logo);
W7L/W7M/W7S come from desktop/icon-assets/shortcut/shortcut-*.svg (the thinner W7 rings).
All coordinates are in the mark's own 1024 frame: nucleus at (512,512); 'off' is the
optical-centre shift the shipped icons apply."""
import re, json, os
R = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'desktop', 'icon-assets')
out = {}
def grab(path, name):
    s = open(path).read()
    paths = re.findall(r'<path d="([^"]+)"', s)
    circ = [tuple(map(float, c)) for c in re.findall(r'<circle cx="([\d.]+)" cy="([\d.]+)" r="([\d.]+)"', s)]
    off = re.search(r'translate\((-?[\d.]+) (-?[\d.]+)\) translate\(512 512\)', s).groups()
    out[name] = dict(rings=paths, nr=circ[0][2], er=circ[2][2], halo=circ[1][2],
                     e=[circ[2][0], circ[2][1]], off=[float(off[0]), float(off[1])])
for t in 'L M S XS'.split():
    grab(f'{R}/source/icon-{t}.svg', t)
for t in 'L M S'.split():
    grab(f'{R}/shortcut/shortcut-{t}.svg', 'W7' + t)
json.dump(out, open(os.path.join(os.path.dirname(__file__), 'geom.json'), 'w'), separators=(',', ':'))
print({k: (v['nr'], v['er'], v['halo'], v['off']) for k, v in out.items()})
