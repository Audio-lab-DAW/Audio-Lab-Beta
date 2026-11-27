#!/usr/bin/env python3
"""Task DR5: headless screenshots of every overlay as it is today (menus, dialogs, tooltips, toasts, drop feedback, notices).
   python3 tools/design-lab/dr5/shots_today.py [index.html] [out dir]
Reads index.html only; changes nothing in the app."""
import sys, os
from playwright.sync_api import sync_playwright
F = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
OUT = sys.argv[2] if len(sys.argv) > 2 else 'dr5-today'
os.makedirs(OUT, exist_ok=True)
URL = os.environ.get('DR5_URL', 'http://127.0.0.1:8765/' + os.path.basename(F))
ARGS = ["--autoplay-policy=no-user-gesture-required", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"]
INIT = "if(!localStorage.getItem('audiolab-ui'))localStorage.setItem('audiolab-ui',JSON.stringify({splash:false,lat3:1}))"
with sync_playwright() as p:
    b = p.chromium.launch(args=ARGS + ["--no-proxy-server"])
    pg = b.new_context(viewport={'width': 1600, 'height': 1000}).new_page()
    pg.route('**/fonts.googleapis.com/**', lambda r: r.abort()); pg.route('**/fonts.gstatic.com/**', lambda r: r.abort())
    pg.add_init_script("if(!sessionStorage.getItem('d5')){sessionStorage.setItem('d5','1');" + INIT + "}")
    pg.goto(URL, wait_until='commit'); pg.wait_for_function("()=>window.AudioLab&&window.AudioLab.version", timeout=120000); pg.wait_for_timeout(4000)
    R = lambda c: pg.evaluate("c=>AudioLab.run(c)", c)
    clean = "()=>{for(const i of['splash','liteNote']){const s=document.getElementById(i);if(s)s.remove()}}"
    pg.evaluate(clean); R("openDemoFractals()"); pg.wait_for_timeout(6000); pg.evaluate(clean)
    def shot(name, js, wait=500, after="closeMenu();for(const m of document.querySelectorAll('.modal'))m.hidden=true;const q=document.getElementById('stq');if(q)q.remove();"):
        try:
            R(js); pg.wait_for_timeout(wait); pg.screenshot(path=f'{OUT}/{name}.png'); print('ok', name, flush=True)
        except Exception as e: print('FAIL', name, str(e)[:200])
        try:
            pg.keyboard.press('Escape'); R(after); pg.wait_for_timeout(200)
        except Exception: pass
    ONLY = os.environ.get('DR5_ONLY')
    _shot = shot
    def shot(n, *a, **k):
        if not ONLY or n[:2] in ONLY.split(','): _shot(n, *a, **k)
    shot('01-track-menu', "trackMenu(420,300,S.tracks[1],4)")
    shot('02-clip-menu', "(()=>{for(const t of S.tracks)for(const c of t.clips){clipMenu(700,320,t,c,c.start+0.5);return}})()")
    shot('03-quick-actions', "$('#bLogo').dispatchEvent(new MouseEvent('contextmenu',{bubbles:true,clientX:20,clientY:20}))")
    shot('04-mixer-view-menu', "openMenu(500,200,mxMenuItems(UI.mxView||'wave'));ctxm.classList.add('mxvm')")
    shot('05-toast', "toast('Bounced Kick to a new audio track.')", 600)
    shot('06-ask-close', "void askChoice('Close “Fractals_remake”?','Save it as a .audiolab file first, or close it without saving.',[{label:'Cancel',v:null},{label:'Don’t save',v:'del',cls:'dng'},{label:'Save…',v:'save',cls:'pri'}],ICSAVE)", 500)
    shot('07-ask-text', "void askText('Project name','Fractals')", 500)
    shot('08-stems', "void stemAsk('Lead vocal')", 600)
    shot('09-a2m', "(()=>{for(const t of S.tracks)for(const c of t.clips)if(c.buf&&BUFS.has(c.buf)){setTimeout(()=>openA2M(t,c),0);return 'a'}toast('no audio clip in Fractals')})()", 1500)
    shot('10-update-card', "updCard('0.229','Glass step 4 and the new menus.')", 600, "const c=document.getElementById('updCard');if(c)c.remove()")
    shot('11-settings-export', "openSettings('export')", 1200, "closeSet()")
    shot('12-settings-keys', "openSettings('keys')", 1200, "closeSet()")
    shot('13-drop-ghost', "FDRAG={ghost:true,row:S.tracks.length,b:8};dirty=true", 600, "FDRAG=null;dirty=true")
    shot('14-lite-notice', "setTimeout(()=>liteNotice('three projects are open on a slower computer'),0)", 800)
    # tooltip: hover a transport button with a title
    try:
        el = pg.query_selector('#tr button[title], #tr [data-tip], button[title]')
        el.hover(); pg.wait_for_timeout(900); pg.screenshot(path=f'{OUT}/15-tooltip.png'); print('ok 15-tooltip')
    except Exception as e: print('FAIL tooltip', e)
    b.close()
