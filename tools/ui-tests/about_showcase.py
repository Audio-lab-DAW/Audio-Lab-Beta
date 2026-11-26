"""About window showcase "Under the hood" (v0.209, task AD): collapsed and expanded, normal and Light mode, no page errors,
no em dashes, no sideways scroll, Settings > General > About opens it.
  python3 tools/ui-tests/about_showcase.py [repo dir] [out dir] [width] [height]"""
import sys,os,mimetypes,json
from playwright.sync_api import sync_playwright
ROOT=os.path.abspath(sys.argv[1] if len(sys.argv)>1 else '.');OUT=sys.argv[2] if len(sys.argv)>2 else '.';W=int(sys.argv[3]) if len(sys.argv)>3 else 1500;H=int(sys.argv[4]) if len(sys.argv)>4 else 950
def serve(route):
    p=route.request.url.split('https://app.test/',1)[1].split('?')[0] or 'index.html'
    f=os.path.join(ROOT,p)
    if p.endswith('coi-serviceworker.js') or not os.path.isfile(f): return route.fulfill(status=404,body=b'')
    route.fulfill(status=200,body=open(f,'rb').read(),content_type=mimetypes.guess_type(f)[0] or 'application/octet-stream')
with sync_playwright() as p:
    b=p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
    for mode in ['normal','light']:
        lite = mode=='light'
        c=b.new_context(viewport={'width':W,'height':H},device_scale_factor=1);pg=c.new_page();errs=[]
        pg.on('pageerror',lambda e:errs.append(str(e)[:300]));pg.route('https://app.test/**',serve)
        pg.add_init_script("localStorage.setItem('audiolab-ui',JSON.stringify(%s))"%json.dumps({'splash':False,'lat3':1,'lite':lite,'liteMan':lite}))
        pg.goto('https://app.test/index.html');pg.wait_for_function("()=>window.AudioLab&&window.AudioLab.version",timeout=60000);pg.wait_for_timeout(2500)
        pg.evaluate("l=>AudioLab.run('UI.lite='+l+';UI.liteMan='+l+';applyLite()')", 'true' if lite else 'false');pg.wait_for_timeout(300)
        print(mode,'version',pg.evaluate("()=>AudioLab.version"),'lite',pg.evaluate("()=>document.body.classList.contains('lite')"),'errors on load',errs)
        pg.evaluate("()=>{const n=document.getElementById('liteNote');n&&n.remove()}")
        pg.evaluate("()=>AudioLab.run('showAbout()')");pg.wait_for_timeout(1500)
        pg.screenshot(path=f'{OUT}/ad_{mode}_{W}_collapsed.png')
        print(' tiles',pg.evaluate("()=>document.querySelectorAll('#splash .ahfT').length"),'button',pg.evaluate("()=>document.getElementById('ahfMore').textContent"),'scrollH',pg.evaluate("()=>{const s=document.getElementById('splash');return [s.clientHeight,s.scrollHeight]}"))
        pg.click('#ahfMore');pg.wait_for_timeout(1200)
        pg.screenshot(path=f'{OUT}/ad_{mode}_{W}_expanded.png')
        pg.evaluate("()=>document.getElementById('splash').scrollTo(0,99999)");pg.wait_for_timeout(400)
        pg.screenshot(path=f'{OUT}/ad_{mode}_{W}_expanded_end.png')
        print(' rows',pg.evaluate("()=>document.querySelectorAll('#splash .ahfR').length"),'button',pg.evaluate("()=>document.getElementById('ahfMore').textContent"),'emdash',pg.evaluate("()=>document.getElementById('ahf').textContent.includes('—')"),'overflowX',pg.evaluate("()=>{const s=document.getElementById('splash');return s.scrollWidth-s.clientWidth}"))
        pg.keyboard.press('Escape');pg.wait_for_timeout(800)
        print(' closed',pg.evaluate("()=>!document.getElementById('splash')"))
        if mode=='normal':
            pg.evaluate("()=>AudioLab.run(\"openSettings('general')\")");pg.wait_for_timeout(600)
            pg.evaluate("()=>document.getElementById('genHood').scrollIntoView()");pg.wait_for_timeout(300)
            pg.screenshot(path=f'{OUT}/ad_settings.png')
            pg.click('#genHood');pg.wait_for_timeout(1200)
            print(' genHood opens about',pg.evaluate("()=>!!document.querySelector('#splash.ab .ahf')"))
        print(' errors after',errs)
        c.close()
