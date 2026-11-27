#!/usr/bin/env python3
"""Task LK: screenshots for the look tokens, before and after.
  python3 tools/design-lab/lk/shots.py index.html OUTDIR [--dens dense,today,roomy]
At the user's size (2194 x 1139 CSS px at 1.75x), Fractals open. For Dark (glass) and Light mode:
  arr.png   the whole window (arrangement, header column, device panel, transport)
  arrz.png  the arrangement zoomed in (bar 33, 1 bar = 160 px) with a clip and a range selected (grid, hairlines, selection)
  pr.png    the piano roll on a Lead clip, two notes selected
  mix.png   the mixer
  dev.png   the device panel with the Pro EQ (Bass track)
  empty.png a new empty project (empty arrangement and device panel)
With --dens: the arrangement at each density (dens-<name>.png), Dark only.
Not committed: the pictures (the script makes them again)."""
import sys, os, json
from playwright.sync_api import sync_playwright
F = sys.argv[1]; OUT = sys.argv[2]; os.makedirs(OUT, exist_ok=True)
DENS = sys.argv[sys.argv.index('--dens') + 1].split(',') if '--dens' in sys.argv else []
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
    print('version', R("VERSION"), R("JSON.stringify({th:V.th,dpr:devicePixelRatio})"))
    for mode in ['dark', 'light']:
        R("pmSetOn(%s)" % ('true' if mode == 'light' else 'false')); pg.wait_for_timeout(1500); clean()
        R("(()=>{const t=S.tracks.find(t=>/^bass/i.test(t.name))||S.tracks[1];selectTrack(t.id)})()"); pg.wait_for_timeout(1200)
        pg.screenshot(path=f'{OUT}/{mode}-arr.png')
        R("(()=>{V.ppb=40;V.x=128;V.y=0;clampV();const t=S.tracks.find(t=>t.clips.some(c=>c.start<=140&&c.start+c.len>132));if(t){const c=t.clips.find(c=>c.start<=140&&c.start+c.len>132);selC=c.id;selT=t.id}SELR={b0:150,b1:156,r0:2,r1:4};dirty=true})()"); pg.wait_for_timeout(900)
        pg.screenshot(path=f'{OUT}/{mode}-arrz.png'); R("SELR=null;selC=null;dirty=true")
        R("(()=>{const t=S.tracks.find(t=>t.clips.some(c=>c.notes&&c.notes.length>8&&t.inst&&t.inst.preset!=='drums'));const c=t.clips.find(c=>c.notes&&c.notes.length>8);openPR(t,c);c.notes.slice(2,4).forEach(n=>n.sel=true);dirty=true})()"); pg.wait_for_timeout(1500)
        pg.screenshot(path=f'{OUT}/{mode}-pr.png'); R("(()=>{const o=prClip&&prClip();if(o)o.c.notes.forEach(n=>n.sel=false);closePR()})()"); pg.wait_for_timeout(500)
        R("openMixer()"); pg.wait_for_timeout(2000); pg.screenshot(path=f'{OUT}/{mode}-mix.png'); R("(()=>{const w=document.getElementById('mixWin');if(w)w.hidden=true})()"); pg.wait_for_timeout(400)
        R("(()=>{const t=S.tracks.find(t=>t.fx&&t.fx.some(f=>f.type==='eq2'||f.type==='eq'))||S.tracks.find(t=>t.fx&&t.fx.length);if(t)selectTrack(t.id)})()"); pg.wait_for_timeout(1500)
        r = json.loads(R("JSON.stringify((()=>{const r=document.getElementById('fxglass').getBoundingClientRect();return[r.left,r.top,r.width,r.height]})())"))
        pg.screenshot(path=f'{OUT}/{mode}-dev.png', clip={'x': r[0], 'y': r[1], 'width': r[2], 'height': r[3]})
    R("pmSetOn(false)"); pg.wait_for_timeout(800)
    for d in DENS:
        R("(()=>{const e=document.getElementById('lkDens');if(e){e.value='%s';e.dispatchEvent(new Event('change',{bubbles:true}))}})()" % d); pg.wait_for_timeout(1200); clean()
        print('density', d, R("JSON.stringify({th:V.th,row:getComputedStyle(document.documentElement).getPropertyValue('--lk-row')})"))
        pg.screenshot(path=f'{OUT}/dens-{d}.png')
    if DENS: R("(()=>{const e=document.getElementById('lkDens');if(e){e.value='dense';e.dispatchEvent(new Event('change',{bubbles:true}))}})()")
    for mode in ['dark', 'light']:
        R("pmSetOn(%s)" % ('true' if mode == 'light' else 'false')); pg.wait_for_timeout(800)
        R("npT='empty';npOpen();npGo0()"); pg.wait_for_timeout(4000); clean(); pg.wait_for_timeout(800)
        pg.screenshot(path=f'{OUT}/{mode}-empty.png')
    print('errors', logs)
