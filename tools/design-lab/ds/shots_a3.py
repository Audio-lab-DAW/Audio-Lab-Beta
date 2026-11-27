#!/usr/bin/env python3
"""Task DS-A3: screenshots of the clips, before and after.
  python3 tools/design-lab/ds/shots_a3.py index.html OUTDIR
At the user's size (2194 x 1139 CSS px at 1.75x), Fractals open. For Dark (glass) and Light mode:
  arr.png   the whole window
  arrz.png  the arrangement zoomed in (1 bar = 100 px, as the pick page) with one clip selected and one muted
  arrt.png  the arrangement crop of arrz (for the side-by-side with the pick page's AC3 mock-up)
Not committed: the pictures (the script makes them again)."""
import sys, os, json
from playwright.sync_api import sync_playwright
F = sys.argv[1]; OUT = sys.argv[2]; os.makedirs(OUT, exist_ok=True)
SRC = open(F, encoding='utf-8').read()
ARGS = ["--autoplay-policy=no-user-gesture-required", "--enable-gpu-rasterization", "--ignore-gpu-blocklist", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"]
INIT = "if(!localStorage.getItem('audiolab-ui'))localStorage.setItem('audiolab-ui',JSON.stringify({splash:false,lat3:1}))"
with sync_playwright() as p:
    b = p.chromium.launch(args=ARGS); ctx = b.new_context(viewport={'width': 2194, 'height': 1139}, device_scale_factor=1.75); pg = ctx.new_page(); logs = []
    pg.on('console', lambda m: logs.append(m.text[:300]) if m.type == 'error' and 'fetching the script' not in m.text else None)
    pg.on('pageerror', lambda e: logs.append('pageerror: ' + str(e)[:300]))
    pg.route('https://app.test/**', lambda r: r.fulfill(status=200, content_type='text/html', body=SRC) if r.request.url.endswith('.html') else r.fulfill(status=404, body=''))
    pg.add_init_script(INIT); pg.goto('https://app.test/index.html'); pg.wait_for_function("()=>window.AudioLab&&window.AudioLab.version", timeout=90000); pg.wait_for_timeout(3000)
    R = lambda c: pg.evaluate("c=>AudioLab.run(c)", c)
    clean = lambda: pg.evaluate("()=>{for(const i of['splash','liteNote','toast']){const s=document.getElementById(i);if(s&&i!=='toast')s.remove();else if(s)s.style.display='none'}}")
    clean(); R("pmSetOn(false)"); R("openDemoFractals()"); pg.wait_for_timeout(7000); clean()
    print('version', R("VERSION"))
    for mode in ['dark', 'light']:
        R("pmSetOn(%s)" % ('true' if mode == 'light' else 'false')); pg.wait_for_timeout(1500); clean()
        R("(()=>{selC=null;SELCS.clear();V.ppb=12;V.x=0;V.y=0;clampV();dirty=true})()"); pg.wait_for_timeout(900)
        pg.screenshot(path=f'{OUT}/{mode}-arr.png')
        r = json.loads(R("""JSON.stringify((()=>{V.ppb=25;V.x=128;V.y=0;clampV();const L=[];S.tracks.forEach((t,i)=>{const c=t.clips.find(c=>c.start<=136&&c.start+c.len>130);if(c)L.push([i,c.id])});
          if(L[1])selC=L[1][1];const m=L[3]&&S.tracks[L[3][0]].clips.find(c=>c.id===L[3][1]);if(m){m.mute=true}dirty=true;
          const a=arr.getBoundingClientRect();return{x:a.left+X0,y:a.top+AY,m:m?m.id:null}})())"""))
        pg.wait_for_timeout(900)
        pg.screenshot(path=f'{OUT}/{mode}-arrz.png')
        pg.screenshot(path=f'{OUT}/{mode}-arrt.png', clip={'x': r['x'], 'y': r['y'], 'width': 900, 'height': 420})
        R("(()=>{for(const t of S.tracks)for(const c of t.clips)if(c.id===%s)c.mute=false;selC=null;dirty=true})()" % json.dumps(r['m']))
    print('errors', logs)
