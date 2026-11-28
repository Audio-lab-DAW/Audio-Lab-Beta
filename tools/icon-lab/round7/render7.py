"""AudioLab app icon, round 7 (task IC11): every picture into renders/ and renders/manifest.json.
python3 render7.py [ids]   (about 25 minutes on two cores)"""
import os, sys, json
from multiprocessing import Pool
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'renders')


def big(job):
    import designs7 as d
    i, pid = job
    B = os.path.join(OUT, 'big'); os.makedirs(B, exist_ok=True)
    im = d.render(i, pid, 1024)
    im.save(os.path.join(B, '%s-%s-1024.webp' % (i, pid)), quality=90, method=6)
    im.resize((512, 512), Image.LANCZOS).save(os.path.join(B, '%s-%s-512.webp' % (i, pid)), quality=90, method=6)
    for px in (128, 64):
        d.render(i, pid, px).save(os.path.join(B, '%s-%s-%d.png' % (i, pid, px)), optimize=True)
    for px in (128, 64, 32):
        d.render(i, pid, px, frame='mac').save(os.path.join(B, '%s-%s-mac-%d.png' % (i, pid, px)), optimize=True)
    return i, pid


def smalls():
    import small7 as s
    S = os.path.join(OUT, 'small'); os.makedirs(S, exist_ok=True)
    for i in s.ORDER:
        for pid in ('P2', 'P8'):
            for pt in s.PTS:
                for sc in (1, 2):
                    for fr in ('full', 'mac'):
                        s.small(i, pid, pt, sc, fr).save(os.path.join(S, '%s-%s-%d@%dx%s.png' % (i, pid, pt, sc, '-mac' if fr == 'mac' else '')), optimize=True)


if __name__ == '__main__':
    import designs7 as d, small7 as s
    ids = sys.argv[1].split(',') if len(sys.argv) > 1 else list(d.DESIGNS)
    jobs = [(i, p) for i in ids for p in ('P2', 'P8') if p == 'P2' or d.DESIGNS[i]['p8']]
    smalls()
    with Pool(2) as pool:
        for r in pool.imap_unordered(big, jobs):
            print(r, flush=True)
    man = dict(big=[dict(id=i, name=v['name'], line=v['line'], star=v['star'], p8=v['p8']) for i, v in d.DESIGNS.items()],
               small=[dict(id=i, name=s.SMALL[i]['name'], line=s.SMALL[i]['line'], star=s.SMALL[i].get('star', False)) for i in s.ORDER])
    json.dump(man, open(os.path.join(OUT, 'manifest.json'), 'w'), indent=1)
