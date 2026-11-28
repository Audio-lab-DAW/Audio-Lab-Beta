"""AudioLab app icon, round 6 (task IC10): renders everything the pick page shows into renders/ and writes
renders/manifest.json. Run: python3 render6.py  (about ten minutes on two cores), then python3 build_page.py."""
import json, os, sys
from multiprocessing import Pool
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'renders')
BIG = ['K6a', 'K6b', 'K6c', 'K6d', 'E6a', 'E6b', 'E6c', 'E6d', 'E6e']
PALS = ['P2', 'P8']


def save(im, rel, q=None):
    p = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    if rel.endswith('.webp'):
        im.save(p, 'WEBP', quality=q or 92, method=6)
    else:
        im.save(p, optimize=True)
    return rel


def big_job(a):
    id, pid = a
    import designs6 as D
    out = {}
    for px in (1024, 512):
        out['%s-%s-%d' % (id, pid, px)] = save(D.render(id, pid, px), 'big/%s-%s-%d.webp' % (id, pid, px), 93)
    for px in (128, 64):
        out['%s-%s-%d' % (id, pid, px)] = save(D.render(id, pid, px), 'big/%s-%s-%d.png' % (id, pid, px))
    # the Apple grid: 256 for the macOS 26 styles (Default; Dark is the same navy for P2, the P8N entry for P8),
    # 128 for the Dock (64 pt at 2x)
    out['%s-%s-mac-256' % (id, pid)] = save(D.render(id, pid, 256, 'mac'), 'big/%s-%s-mac-256.png' % (id, pid))
    out['%s-%s-mac-128' % (id, pid)] = save(D.render(id, pid, 128, 'mac'), 'big/%s-%s-mac-128.png' % (id, pid))
    if pid == 'P8':
        out['%s-P8-mac-256-dark' % id] = save(D.render(id, 'P8', 256, 'mac', 'dark'), 'big/%s-P8N-mac-256.png' % id)
    print(id, pid, flush=True)
    return out


def small_job(a):
    id, pid = a
    import small6 as S
    out = {}
    for pt in S.PTS:
        for sc in (1, 2):
            for fr in ('full', 'mac'):
                k = '%s-%s-%d@%dx%s' % (id, pid, pt, sc, '-mac' if fr == 'mac' else '')
                out[k] = save(S.small(id, pid, pt, sc, fr), 'small/%s.png' % k)
    if pid == 'P2':
        for sc in (1, 2):
            k = '%s-tpl-16@%dx' % (id, sc)
            out[k] = save(S.template(id, 16, sc), 'small/%s.png' % k)
    print(id, pid, flush=True)
    return out


def refs():
    """K5a and M5d as picked in round 5 (flat), for the compare view"""
    out = {}
    for id in ('K5a', 'M5d'):
        for pid in PALS:
            src = os.path.join(HERE, '..', 'round5', 'renders', id, '%s-%s-1024.png' % (id, pid))
            im = Image.open(src).convert('RGBA')
            out['%s-%s-1024' % (id, pid)] = save(im, 'ref/%s-%s-1024.webp' % (id, pid), 93)
            for px in (512, 128, 64):
                srcp = os.path.join(HERE, '..', 'round5', 'renders', id, '%s-%s-%d.png' % (id, pid, px))
                im2 = Image.open(srcp).convert('RGBA')
                out['%s-%s-%d' % (id, pid, px)] = save(im2, 'ref/%s-%s-%d.%s' % (id, pid, px, 'webp' if px == 512 else 'png'), 93)
    return out


if __name__ == '__main__':
    import small6 as S
    what = sys.argv[1] if len(sys.argv) > 1 else 'all'
    man = {}
    mp = os.path.join(OUT, 'manifest.json')
    if os.path.exists(mp):
        man = json.load(open(mp))
    with Pool(2) as pool:
        if what in ('all', 'big'):
            ids = sys.argv[2].split(',') if len(sys.argv) > 2 else BIG
            for o in pool.imap_unordered(big_job, [(i, p) for i in ids for p in PALS]):
                man.update(o)
        if what in ('all', 'small'):
            for o in pool.imap_unordered(small_job, [(i, p) for i in S.ORDER for p in PALS]):
                man.update(o)
    if what in ('all', 'ref'):
        man.update(refs())
    json.dump(man, open(mp, 'w'), indent=0, sort_keys=True)
    print(len(man), 'pictures')
