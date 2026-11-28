#!/usr/bin/env python3
"""Task LK helper: open the app at the user's size with Fractals and print/evaluate expressions. python3 probe.py index.html 'expr' ..."""
import sys, json
import sys as _ws_sys, os as _ws_os; _ws_sys.path.insert(0, _ws_os.path.join(_ws_os.path.dirname(_ws_os.path.abspath(__file__)), '../../test-songs')); from alsong import alsong  # task WS-F: the test songs
from playwright.sync_api import sync_playwright
F = sys.argv[1]; EX = sys.argv[2:]
SRC = open(F, encoding='utf-8').read()
ARGS = ["--autoplay-policy=no-user-gesture-required", "--enable-gpu-rasterization", "--ignore-gpu-blocklist", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"]
INIT = "if(!localStorage.getItem('audiolab-ui'))localStorage.setItem('audiolab-ui',JSON.stringify({splash:false,lat3:1}))"
with sync_playwright() as p:
    b = p.chromium.launch(args=ARGS); ctx = b.new_context(viewport={'width': 2194, 'height': 1139}, device_scale_factor=1.75); pg = ctx.new_page(); logs = []
    pg.on('console', lambda m: logs.append(m.text[:300]) if m.type == 'error' and 'fetching the script' not in m.text else None)
    pg.on('pageerror', lambda e: logs.append('pageerror: ' + str(e)[:300]))
    pg.route('https://app.test/**', alsong(lambda r: r.fulfill(status=200, content_type='text/html', body=SRC) if r.request.url.endswith('.html') else r.fulfill(status=404, body='')))
    pg.add_init_script(INIT); pg.goto('https://app.test/index.html'); pg.wait_for_function("()=>window.AudioLab&&window.AudioLab.version", timeout=90000); pg.wait_for_timeout(3000)
    R = lambda c: pg.evaluate("c=>AudioLab.run(c)", c)
    pg.evaluate("()=>{for(const i of['splash','liteNote']){const s=document.getElementById(i);if(s)s.remove()}}")
    print('empty:', R("JSON.stringify({th:V.th,n:S.tracks.length,laneH,ppb:V.ppb})"))
    R("pmSetOn(false)"); R("openDemoFractals()"); pg.wait_for_timeout(7000)
    for e in EX: print(e, '=>', R(e))
    print('errors', logs)
