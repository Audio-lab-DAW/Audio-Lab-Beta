"""Task AI: levels of the Fractals song that opens at the start.
Prints the master value, solo Kick and Bass (beats 64 to 96) as the song is and with the master put back to 0 dB,
and peak, true peak and loudness of the whole song after the master.
  python3 tools/engine-tests/taskAI_levels.py [index.html] [--vox] [--quick]
--vox serves the vox/*.wav files next to the app (versions before 0.220 fetch the vocal samples); --quick skips the whole song."""
import sys, os, json, hashlib
import sys as _ws_sys, os as _ws_os; _ws_sys.path.insert(0, _ws_os.path.join(_ws_os.path.dirname(_ws_os.path.abspath(__file__)), '../test-songs')); from alsong import alsong  # task WS-F: the test songs
import numpy as np
from scipy.signal import resample_poly
import pyloudnorm as pyln
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, '..', '..')
sys.path.insert(0, os.path.join(HERE, '..', 'remake'))
from alab import AudioLab
args = [a for a in sys.argv[1:] if not a.startswith('--')]; VOX = '--vox' in sys.argv; QUICK = '--quick' in sys.argv
al = AudioLab(args[0] if args else os.path.join(ROOT, 'index.html'))
_start = al.start
def start():
    from playwright.sync_api import sync_playwright
    al._pw = sync_playwright().start(); al.browser = al._pw.chromium.launch(args=["--autoplay-policy=no-user-gesture-required"])
    al.page = al.browser.new_page(viewport={"width": 1600, "height": 1000}); al.errors = []
    al.page.on("pageerror", lambda e: al.errors.append(str(e)[:400]))
    src = open(al.index, encoding="utf-8").read()
    def handle(route):
        u = route.request.url
        if u.endswith("/") or u.endswith("index.html"): route.fulfill(body=src, content_type="text/html")
        elif VOX and "/vox/" in u: route.fulfill(body=open(os.path.join(ROOT, "vox", u.rsplit("/", 1)[1]), "rb").read(), content_type="audio/wav")
        else: route.fulfill(status=404, body="")
    al.page.route("https://app.test/**", alsong(handle)); al.page.goto("https://app.test/")
    al.page.wait_for_function("() => window.AudioLab && window.AudioLab.version", timeout=60000)
    for i in range(300):
        if al.page.evaluate("() => AudioLab.run(\"S.tracks.some(t=>t.name==='Vocals (original)')&&S.tracks.some(t=>t.name==='Lead low')\")"): break
        al.page.wait_for_timeout(200)
    al.page.wait_for_timeout(1500)
start()
rms = lambda x: float(np.sqrt(np.mean(x.astype(np.float64) ** 2))); db = lambda v: 20 * np.log10(max(v, 1e-12))
info = json.loads(al.run("JSON.stringify({v:VERSION,master:S.master,tabs:PJ.list.map(p=>p.name),n:S.tracks.length,end:Math.max(...S.tracks.flatMap(t=>t.clips.map(c=>c.start+c.len))),mfx:S.mfx.map(f=>f.type+(f.on?'':' (off)')),headroom:UI.headroom??-6,bp:!!UI.bitPerfect})"))
print('version', info['v'], '| open songs', info['tabs'], '| tracks', info['n'], '| master', info['master'], 'dB | master effects', info['mfx'], '| output trim', info['headroom'], 'dB')
al.tracks = json.loads(al.run("JSON.stringify(Object.fromEntries(S.tracks.map(t=>[t.name,t.id])))"))
def solo(tag):
    for nm in ('Kick', 'Bass'):
        x, sr = al.render(b0=64, b1=96, only=nm); print('%s: Fractals %s %.5f dB  %s' % (tag, nm, db(rms(x)), hashlib.md5(x.tobytes()).hexdigest()[:12]))
solo('as it opens (master %g dB)' % info['master'])
if info['master'] != 0:
    al.run("S.master=0;0"); solo('master put back to 0 dB'); al.run("S.master=%g;0" % info['master'])
if not QUICK:
    end = int(np.ceil(info['end'] / 4) * 4); parts = []
    for i, b0 in enumerate(range(0, end, 128)):   # 32 bars at a time, a fresh page every 2 pieces (a page that renders a lot runs out of memory)
        if i % 2 == 0: al.stop(); start()
        x, sr = al.render(b0=b0, b1=min(end, b0 + 128), tail=0); parts.append(x); print('  rendered beats', b0, 'to', min(end, b0 + 128), flush=True)
    x = np.concatenate(parts, axis=1)
    tp = float(np.abs(resample_poly(x.astype(np.float64), 4, 1, axis=1)).max())
    print('whole song, beats 0 to %d (%.1f s): sample peak %.2f dBFS, true peak %.2f dBTP, loudness %.2f LUFS, RMS %.2f dB  %s' % (
        end, x.shape[1] / sr, db(float(np.abs(x).max())), db(tp), pyln.Meter(sr).integrated_loudness(x.T.astype(np.float64)), db(rms(x)), hashlib.md5(x.tobytes()).hexdigest()[:12]))
    k = int(np.argmax(np.abs(x).max(axis=0))); print('loudest sample at beat %.1f' % (k / sr * 145 / 60))
    for a, b, nm in ((64, 96, 'beats 64 to 96'), (640, 704, 'beats 640 to 704')):
        if b <= end:
            y, _ = al.render(b0=a, b1=b, tail=0); print('mix %s: peak %.2f dBFS, RMS %.2f dB, loudness %.2f LUFS' % (nm, db(float(np.abs(y).max())), db(rms(y)), pyln.Meter(sr).integrated_loudness(y.T.astype(np.float64))))
print('errors', al.errors); al.stop()
