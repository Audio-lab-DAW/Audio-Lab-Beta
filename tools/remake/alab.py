"""AudioLab bridge client.

Opens AudioLab Studio in a headless browser and talks to `window.AudioLab` (the bridge built into the app,
v0.131 and later). With it a script can build a project from plain data, look at or change anything inside
the app, render through the app's real audio engine, and save the result as an .audiolab file.

    from alab import AudioLab
    al = AudioLab("/path/to/index.html"); al.start()
    al.build(recipe)                      # tempo, sections, tracks, instruments, effects, clips, notes
    x, sr = al.render(b0=0, b1=64)        # numpy array (2, n): the mix, rendered by the app itself
    kick, sr = al.render(b0=0, b1=64, only="Kick")
    al.save("song.audiolab"); al.stop()
"""
import base64, json, os, time
import sys as _ws_sys, os as _ws_os; _ws_sys.path.insert(0, _ws_os.path.join(_ws_os.path.dirname(_ws_os.path.abspath(__file__)), '../test-songs')); from alsong import alsong  # task WS-F: the test songs
import numpy as np
from playwright.sync_api import sync_playwright

CHUNK = 1 << 20  # samples per pull


class AudioLab:
    def __init__(self, index_html, width=1600, height=1000):
        self.index = os.path.abspath(index_html)
        self.size = (width, height)
        self.tracks = {}      # name -> id (after build)
        self.fx = {}          # name -> [fx ids]

    # ---- life cycle -------------------------------------------------------
    def start(self):
        self._pw = sync_playwright().start()
        self.browser = self._pw.chromium.launch(args=["--autoplay-policy=no-user-gesture-required"])
        self.page = self.browser.new_page(viewport={"width": self.size[0], "height": self.size[1]})
        self.errors = []
        self.page.on("pageerror", lambda e: self.errors.append(str(e)[:400]))
        src = open(self.index, encoding="utf-8").read()

        def handle(route):
            u = route.request.url
            if u.endswith("/") or u.endswith("index.html"):
                route.fulfill(body=src, content_type="text/html")
            else:
                route.fulfill(status=404, body="")

        self.page.route("https://app.test/**", alsong(handle))
        self.page.goto("https://app.test/")
        self.page.wait_for_function("() => window.AudioLab && window.AudioLab.version", timeout=60000)
        self.page.wait_for_timeout(2500)
        self.version = self.js("() => AudioLab.version")
        return self

    def stop(self):
        try:
            self.browser.close()
        finally:
            self._pw.stop()

    # ---- raw access -------------------------------------------------------
    def js(self, fn, arg=None):
        """Run a JS function in the page (page scope)."""
        return self.page.evaluate(fn, arg)

    def run(self, code):
        """Run code in the app's own scope: every internal function and variable is reachable.
        The value of the last expression is returned (it must be JSON-serialisable)."""
        return self.page.evaluate("c => AudioLab.run(c)", code)

    def state(self):
        return self.page.evaluate("() => JSON.parse(JSON.stringify(AudioLab.state()))")

    def screenshot(self, path, clip=None):
        self.page.screenshot(path=path, clip=clip)

    # ---- build ------------------------------------------------------------
    def build(self, recipe):
        """Replace the current project. See README.md for the recipe format."""
        out = self.page.evaluate("r => AudioLab.build(r)", recipe)
        self.tracks = {t["name"]: t["id"] for t in out["tracks"]}
        self.fx = {t["name"]: t["fx"] for t in out["tracks"]}
        if self.errors:
            raise RuntimeError("AudioLab error after build: " + self.errors[-1])
        return out

    def tid(self, name_or_id):
        return self.tracks.get(name_or_id, name_or_id)

    # ---- audio in ---------------------------------------------------------
    def add_audio(self, x, sr):
        """Put audio (channels, n) float32 into the app; returns the buffer id for an audio clip's `buf`."""
        x = np.atleast_2d(np.asarray(x, dtype=np.float32))
        aid = self.page.evaluate("a => AudioLab.audioNew(a[0],a[1],a[2])", [x.shape[0], x.shape[1], sr])
        for ch in range(x.shape[0]):
            for off in range(0, x.shape[1], CHUNK):
                b = base64.b64encode(x[ch, off:off + CHUNK].tobytes()).decode()
                self.page.evaluate("a => AudioLab.audioPut(a[0],a[1],a[2],a[3])", [aid, ch, off, b])
        return self.page.evaluate("a => AudioLab.audioDone(a)", aid)

    # ---- render -----------------------------------------------------------
    def render(self, b0=0, b1=None, sr=44100, only=None, tracks=None, tail=0, lim=False, fast=False, single=False):
        """Render beats b0..b1 through the app's engine. `only`: one track alone (with its effects and the
        master chain). `tracks`: several tracks together. Returns (array (2, n), sr)."""
        o = {"b0": b0, "sr": sr, "tail": tail, "lim": lim, "fast": fast, "single": single}
        if b1 is not None:
            o["b1"] = b1
        if only:
            o["only"] = self.tid(only)
        if tracks:
            o["tracks"] = [self.tid(t) for t in tracks]
        t0 = time.time()
        h = self.page.evaluate("o => AudioLab.render(o)", o)
        out = np.zeros((h["ch"], h["len"]), dtype=np.float32)
        for ch in range(h["ch"]):
            for off in range(0, h["len"], CHUNK):
                n = min(CHUNK, h["len"] - off)
                b = self.page.evaluate("a => AudioLab.pull(a[0],a[1],a[2],a[3])", [h["id"], ch, off, n])
                out[ch, off:off + n] = np.frombuffer(base64.b64decode(b), dtype=np.float32)
        self.page.evaluate("i => AudioLab.free(i)", h["id"])
        self.last_render_s = time.time() - t0
        if self.errors:
            raise RuntimeError("AudioLab error during render: " + self.errors[-1])
        return out, h["sr"]

    # ---- save -------------------------------------------------------------
    def save(self, path):
        h = self.page.evaluate("() => AudioLab.pack()")
        with open(path, "wb") as f:
            for off in range(0, h["len"], CHUNK * 3):
                b = self.page.evaluate("a => AudioLab.pull(a[0],-1,a[1],a[2])", [h["id"], off, CHUNK * 3])
                f.write(base64.b64decode(b))
        self.page.evaluate("i => AudioLab.free(i)", h["id"])
        return path

    # ---- catalogue of what the app offers ----------------------------------
    def catalog(self):
        """Instruments, their presets and parameters, effects and their parameter ranges."""
        return self.run("""(()=>{const safe=o=>JSON.parse(JSON.stringify(o));const g=n=>{try{return safe(eval(n))}catch(e){return null}};
          return {presets:g('PRESETS'),fx:g('Object.fromEntries(Object.entries(FXDEF).map(([k,D])=>[k,{name:D.name,p:D.p}]))'),fxPresets:g('FXPRE'),
            plant:g('PLPRE'),ipar:g('IPAR')}})()""")
