import sys,json
import sys as _ws_sys, os as _ws_os; _ws_sys.path.insert(0, _ws_os.path.join(_ws_os.path.dirname(_ws_os.path.abspath(__file__)), '../test-songs')); from alsong import alsong  # task WS-F: the test songs
from playwright.sync_api import sync_playwright
src=open(sys.argv[1],encoding='utf-8').read()
with sync_playwright() as p:
    b=p.chromium.launch();pg=b.new_page(viewport={'width':1600,'height':1000},device_scale_factor=2);errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('https://app.test/**',alsong(lambda r:r.fulfill(status=200,content_type='text/html',body=src.encode()) if r.request.url.endswith('.html') else r.fulfill(status=404,body=b'')))
    pg.add_init_script("localStorage.setItem('audiolab-ui',JSON.stringify({splash:false,lat3:1}))")
    pg.goto('https://app.test/index.html');pg.wait_for_timeout(9000)
    pg.evaluate("""()=>{window.AudioLab.run("(()=>{UI.lite=false;document.body.classList.remove('lite');applyTrans()})()")}""");pg.wait_for_timeout(500)
    pg.screenshot(path='/tmp/pat/m0.png',clip={'x':0,'y':820,'width':500,'height':80})
    pg.evaluate("""()=>{window.AudioLab.run("(()=>{const w=document.getElementById('mixWin');openMixer()})()")}""");pg.wait_for_timeout(1500)
    r=pg.evaluate("""()=>{const w=document.getElementById('mixWin');if(!w)return null;const r=w.getBoundingClientRect();return [r.left,r.top,r.width,r.height,w.className,[...w.children].map(c=>c.className+':'+Math.round(c.getBoundingClientRect().top)+'-'+Math.round(c.getBoundingClientRect().bottom))]}""")
    print(r,errs[:2])
    if r: pg.screenshot(path='/tmp/pat/m1.png',clip={'x':max(0,r[0]-10),'y':max(0,r[1]-50),'width':1590,'height':110})
    b.close()
