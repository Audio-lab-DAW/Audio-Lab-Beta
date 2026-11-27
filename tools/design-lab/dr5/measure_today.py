#!/usr/bin/env python3
"""Task DR5: how long today's overlays take to open in v0.228 (JS time of the open call, and click-to-next-frame), headless.
   python3 tools/design-lab/dr5/measure_today.py [index.html]   (serves nothing itself: start  python3 -m http.server 8765 --bind 127.0.0.1  in the repo first)
The cloud machine has no graphics card: compare the numbers with each other, not with the Mac."""
import sys, os, json
from playwright.sync_api import sync_playwright
F = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
URL = os.environ.get('DR5_URL', 'http://127.0.0.1:8765/' + os.path.basename(F))
INIT = "if(!localStorage.getItem('audiolab-ui'))localStorage.setItem('audiolab-ui',JSON.stringify({splash:false,lat3:1}))"
JS = r"""async (code)=>{const out=[];const CL=()=>AudioLab.run("closeMenu();for(const m of document.querySelectorAll('.modal'))m.hidden=true");for(let i=0;i<7;i++){CL();
 await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));const t0=performance.now();AudioLab.run(code);const t1=performance.now();
 await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));out.push([t1-t0,performance.now()-t0])}
 CL();out.sort((a,b)=>a[0]-b[0]);return out[3]}"""
with sync_playwright() as p:
    b = p.chromium.launch(args=["--no-proxy-server", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
    pg = b.new_context(viewport={'width': 1600, 'height': 1000}).new_page()
    pg.route('**/fonts.googleapis.com/**', lambda r: r.abort()); pg.route('**/fonts.gstatic.com/**', lambda r: r.abort())
    pg.add_init_script("if(!sessionStorage.getItem('d5')){sessionStorage.setItem('d5','1');" + INIT + "}")
    pg.goto(URL, wait_until='commit'); pg.wait_for_function("()=>window.AudioLab&&window.AudioLab.version", timeout=120000); pg.wait_for_timeout(4000)
    R = lambda c: pg.evaluate("c=>AudioLab.run(c)", c)
    pg.evaluate("()=>{for(const i of['splash','liteNote']){const s=document.getElementById(i);if(s)s.remove()}}")
    R("openDemoFractals()"); pg.wait_for_timeout(6000)
    res = {}
    for name, code in [('track menu (27 rows)', "trackMenu(420,300,S.tracks[1],4)"),
                       ('clip menu', "(()=>{for(const t of S.tracks)for(const c of t.clips){clipMenu(700,320,t,c,c.start+0.5);return}})()"),
                       ('confirm dialog (askChoice)', "void askChoice('Close?','x',[{label:'Cancel',v:null},{label:'Save…',v:1,cls:'pri'}])"),
                       ('text dialog (askText)', "void askText('Project name','Fractals')"),
                       ('toast', "toast('Bounced Kick to a new audio track.')")]:
        res[name] = [round(x, 1) for x in pg.evaluate(JS, code)]
        print(name, 'open call', res[name][0], 'ms; to second frame', res[name][1], 'ms', flush=True)
    b.close()
