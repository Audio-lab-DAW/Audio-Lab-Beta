import sys,json
import sys as _ws_sys, os as _ws_os; _ws_sys.path.insert(0, _ws_os.path.join(_ws_os.path.dirname(_ws_os.path.abspath(__file__)), '../test-songs')); from alsong import alsong  # task WS-F: the test songs
from playwright.sync_api import sync_playwright
src=open(sys.argv[1],encoding='utf-8').read()
with sync_playwright() as p:
    b=p.chromium.launch();pg=b.new_page(viewport={'width':1600,'height':1000})
    pg.route('https://app.test/**',alsong(lambda r:r.fulfill(status=200,content_type='text/html',body=src.encode()) if r.request.url.endswith('.html') else r.fulfill(status=404,body=b'')))
    pg.add_init_script("localStorage.setItem('audiolab-ui',JSON.stringify({splash:false,lat3:1}))")
    pg.goto('https://app.test/index.html');pg.wait_for_timeout(9000)
    r=pg.evaluate("""()=>{window.AudioLab.run("(()=>{UI.lite=false;document.body.classList.remove('lite');applyTrans()})()");const o={};for(const id of ['arr','arrBack','hglass','fx','tr','mapw','vizp','dockB','dockT','hdr']){const e=document.getElementById(id);if(!e){o[id]=null;continue}const r=e.getBoundingClientRect(),cs=getComputedStyle(e);o[id]=[Math.round(r.left),Math.round(r.top),Math.round(r.right),Math.round(r.bottom),cs.backdropFilter.slice(0,30),cs.clipPath,cs.boxShadow.slice(0,30)]}return o}""")
    for k,v in r.items():print(k,v)
    b.close()
