"""Task LT-3b (lane J): exports of the instruments whose worklet processors LT-3b now wraps (for fast MIDI notes) must not change.
Renders one clip on each (twice, to show which are repeatable on their own) and prints level and a checksum. Run on two builds and compare.
  python3 tools/engine-lab/lt/lt3b_exports.py [index.html] [--seed] [--toggle]
  --toggle: each line renders once with lane J's worklet piece and once without it, in the same page (the two must be the same)"""
import sys, os, hashlib
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'remake'))
from alab import AudioLab
al = AudioLab(next((a for a in sys.argv[1:] if not a.startswith('--')), 'index.html'))
# the page's own random numbers are not seeded (Emit and Vector grains make their sounds with them, so two page loads of the same build
# differ): with --seed they are, before the page starts, and two builds can be compared sample for sample
if '--seed' in sys.argv:
    from playwright.sync_api import sync_playwright
    al._pw = sync_playwright().start(); al.browser = al._pw.chromium.launch(args=["--autoplay-policy=no-user-gesture-required"])
    al.page = al.browser.new_page(viewport={"width": al.size[0], "height": al.size[1]}); al.errors = []
    al.page.on("pageerror", lambda e: al.errors.append(str(e)[:400]))
    al.page.add_init_script("(()=>{let a=12345;Math.random=()=>{a=(a*1103515245+12345)%2147483648;return a/2147483648}})()")
    src = open(al.index, encoding="utf-8").read()
    al.page.route("https://app.test/**", lambda r: r.fulfill(body=src, content_type="text/html") if r.request.url.endswith("/") or r.request.url.endswith("index.html") else r.fulfill(status=404, body=""))
    al.page.goto("https://app.test/"); al.page.wait_for_function("() => window.AudioLab && window.AudioLab.version", timeout=60000); al.page.wait_for_timeout(2500)
    al.version = al.js("() => AudioLab.version")
else:
    al.start()
rms = lambda x: float(np.sqrt(np.mean(x.astype(np.float64) ** 2))); db = lambda v: 20 * np.log10(max(v, 1e-12))
notes = [{'p': p, 's': i * 2, 'l': 1.7, 'v': .8} for i in range(4) for p in (48, 55, 60)]
for name, pre in (('Wavetable', 'wtab'), ('Sampler grains', 'sampler~grain'), ('Emit', 'emit'), ('Vector grains', 'vgrain'), ('Vector FM', 'vfm'), ('Orbit', 'orb'), ('Sub bass', 'sbass'), ('Psy bass', 'psyb'), ('Crackle', 'crk'), ('Bouncing ball', 'bball'), ('Plant', 'plant'), ('Drum kit', 'drums')):   # Plant and the Drum kit last: their first render is not repeatable on any build
    out = []
    for k in range(2):
        if '--toggle' in sys.argv:   # the same page: the first render with lane J's worklet piece (window.LT_WL), the second without it
            al.run("window.__ltwl=window.__ltwl||window.LT_WL;window.LT_WL=%s;WLU=null;0" % ('window.__ltwl' if k == 0 else "''"))
        t = {'name': name, 'preset': pre.split('~')[0], 'clips': [{'start': 0, 'len': 8, 'notes': notes}]}
        if '~' in pre: t['inst'] = {'mode': 'grain'}
        al.build({'bpm': 120, 'tracks': [t]})
        x, sr = al.render(b0=0, b1=8, tail=1); out.append('%.5f dB %s' % (db(rms(x)), hashlib.md5(x.tobytes()).hexdigest()[:12]))
    print('%-15s %s' % (name, '  |  '.join(out)))
print('errors', al.errors); al.stop()
