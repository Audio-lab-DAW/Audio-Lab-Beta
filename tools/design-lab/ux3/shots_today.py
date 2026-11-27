#!/usr/bin/env python3
"""Task UX3 (learn mode research): headless screenshots and timings of today's tutorial mode and help button.
   Serve the repo first:  python3 -m http.server 8765   then  python3 tools/design-lab/ux3/shots_today.py
Reads index.html only; changes nothing in the app."""
import os, json
from playwright.sync_api import sync_playwright
OUT = os.environ.get('UX3_OUT', 'tools/design-lab/ux3/today'); os.makedirs(OUT, exist_ok=True)
URL = os.environ.get('UX3_URL', 'http://127.0.0.1:8765/index.html')
ARGS = ["--autoplay-policy=no-user-gesture-required", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--no-proxy-server"]
INIT = "if(!localStorage.getItem('audiolab-ui'))localStorage.setItem('audiolab-ui',JSON.stringify({splash:false,lat3:1}))"
with sync_playwright() as p:
    b = p.chromium.launch(args=ARGS)
    pg = b.new_context(viewport={'width': 1600, 'height': 1000}).new_page()
    pg.route('**/fonts.googleapis.com/**', lambda r: r.abort()); pg.route('**/fonts.gstatic.com/**', lambda r: r.abort())
    pg.add_init_script("if(!sessionStorage.getItem('u3')){sessionStorage.setItem('u3','1');" + INIT + "}")
    pg.goto(URL, wait_until='commit'); pg.wait_for_function("()=>window.AudioLab&&window.AudioLab.version", timeout=120000); pg.wait_for_timeout(4000)
    R = lambda c: pg.evaluate("c=>AudioLab.run(c)", c)
    clean = "()=>{for(const i of['splash','liteNote']){const s=document.getElementById(i);if(s)s.remove()}}"
    pg.evaluate(clean); R("openDemoFractals()"); pg.wait_for_timeout(6000); pg.evaluate(clean)
    info = {'version': pg.evaluate("AudioLab.version")}
    bb = pg.query_selector('#bTut').bounding_box(); info['button'] = bb
    pg.screenshot(path=f'{OUT}/01-help-button.jpg', quality=72, clip={'x': max(0, bb['x']-260), 'y': max(0, bb['y']-14), 'width': 520, 'height': 60})
    t0 = pg.evaluate("performance.now()"); R("tutSet(true)"); info['tutSetMs'] = pg.evaluate(f"performance.now()-{t0}")
    pg.wait_for_timeout(1200)
    info['outlines'] = R("document.querySelectorAll('#tutl i').length")
    info['scanMs'] = pg.evaluate("(()=>{const a=performance.now();for(let i=0;i<5;i++)AudioLab.run('tutScan()');return (performance.now()-a)/5})()")
    pg.screenshot(path=f'{OUT}/02-tutorial-on.jpg', quality=72)
    el = pg.query_selector('#bPlay') or pg.query_selector('#tr button')
    el.hover(); pg.wait_for_timeout(500); pg.screenshot(path=f'{OUT}/03-tutorial-hover.jpg', quality=72)
    # does a click do anything while on? try the metronome button
    before = R("JSON.stringify([typeof clickOn!=='undefined'?clickOn:null,document.getElementById('bClick').className])")
    c = pg.query_selector('#bClick')
    if c: c.click(); pg.wait_for_timeout(200)
    info["clickBlocked"] = before == R("JSON.stringify([typeof clickOn!=='undefined'?clickOn:null,document.getElementById('bClick').className])")
    info['tipsKeys'] = R("Object.keys(TIPS).length"); info['tutxKeys'] = R("Object.keys(TUTX).length")
    info['titled'] = pg.evaluate("document.querySelectorAll('[title],[data-tip]').length")
    R("tutSet(false)")
    json.dump(info, open(f'{OUT}/measure.json', 'w'), indent=1); print(json.dumps(info))
    b.close()
