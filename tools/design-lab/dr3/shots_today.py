# task DR3: headless screenshots of today's app (index.html at HEAD) for the design-directions research.
#   python3 tools/design-lab/dr3/shots_today.py index.html tools/design-lab/dr3/today
import sys,os
import sys as _ws_sys, os as _ws_os; _ws_sys.path.insert(0, _ws_os.path.join(_ws_os.path.dirname(_ws_os.path.abspath(__file__)), '../../test-songs')); from alsong import alsong  # task WS-F: the test songs
from playwright.sync_api import sync_playwright
f=sys.argv[1];out=sys.argv[2];src=open(f,encoding='utf-8').read()
with sync_playwright() as p:
    b=p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required','--use-gl=swiftshader','--enable-unsafe-swiftshader'])
    for w,h in [(1280,720),(1920,1080)]:
        pg=b.new_page(viewport={'width':w,'height':h});errs=[]
        pg.on('pageerror',lambda e:errs.append(str(e)[:200]))
        pg.route('https://app.test/**',alsong(lambda r:r.fulfill(status=200,content_type='text/html',body=src.encode()) if r.request.url.endswith('.html') else r.fulfill(status=404,body=b'')))
        pg.add_init_script("if(!localStorage.getItem('audiolab-ui'))localStorage.setItem('audiolab-ui',JSON.stringify({splash:false,lat3:1}))")
        pg.goto('https://app.test/index.html');pg.wait_for_timeout(9000)
        R=lambda c:pg.evaluate("c=>window.AudioLab.run(c)",c)
        print(w,h,'version',R("VERSION"),'errors',errs)
        R("(()=>{const c=document.getElementById('liteNote');if(c)c.remove()})()")
        pg.screenshot(path=os.path.join(out,f'arrangement_{w}.png'))
        try:
            R("(()=>{try{togglePlay&&togglePlay()}catch(e){}})()");pg.wait_for_timeout(1500)
            pg.screenshot(path=os.path.join(out,f'playing_{w}.png'))
            R("(()=>{try{togglePlay&&togglePlay()}catch(e){}})()")
        except Exception as e:print('play',e)
        try:
            R("openMixer()");pg.wait_for_timeout(1500);pg.screenshot(path=os.path.join(out,f'mixer_{w}.png'))
        except Exception as e:print('mixer',e)
        pg.close()
    b.close()
