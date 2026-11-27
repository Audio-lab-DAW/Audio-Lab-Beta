# DR4: each device on the master chain and the first track, one screenshot each (today's look)
import sys,os
from playwright.sync_api import sync_playwright
f=sys.argv[1];out=sys.argv[2];os.makedirs(out,exist_ok=True);src=open(f,encoding='utf-8').read().encode()
R=lambda pg,c:pg.evaluate("c=>window.AudioLab.run(c)",c)
with sync_playwright() as p:
    b=p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
    cx=b.new_context(viewport={'width':1600,'height':1000});pg=cx.new_page()
    pg.route('https://app.test/**',lambda r:r.fulfill(status=200,content_type='text/html',body=src) if r.request.url.endswith('.html') else r.fulfill(status=404,body=b''))
    pg.add_init_script("localStorage.setItem('audiolab-ui',JSON.stringify({splash:false,lat3:1}))")
    pg.goto('https://app.test/index.html');pg.wait_for_timeout(9000)
    pg.evaluate("()=>{const n=document.getElementById('liteNote');if(n)n.remove()}")
    R(pg,"for(const k of ['eq','limit','loud','spec','gate','ott'])S.mfx.push(mkFx(k));changed(true);")
    R(pg,"selectTrack('__m');renderFx();pos=48*4;start()");pg.wait_for_timeout(5000)
    n=pg.locator('#fxin .dev').count();print('devices',n)
    for i in range(n):
        d=pg.locator('#fxin .dev').nth(i);d.scroll_into_view_if_needed();pg.wait_for_timeout(1200)
        t=d.get_attribute('data-type') or d.get_attribute('data-k') or str(i)
        d.screenshot(path=os.path.join(out,f'dev_{i}_{t}.png'))
    b.close()
