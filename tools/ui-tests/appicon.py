"""App icon picker (v0.203, task V), in the browser and with a pretend desktop host.
  python3 tools/ui-tests/appicon.py [repo dir] [out dir]
Serves the repository folder as https://app.test/, so the favicons and desktop/icon-assets/picker/ load like on the website."""
import sys, os, json, mimetypes
import sys as _ws_sys, os as _ws_os; _ws_sys.path.insert(0, _ws_os.path.join(_ws_os.path.dirname(_ws_os.path.abspath(__file__)), '../test-songs')); from alsong import alsong  # task WS-F: the test songs
from playwright.sync_api import sync_playwright
ROOT = sys.argv[1] if len(sys.argv) > 1 else '.'
OUT = sys.argv[2] if len(sys.argv) > 2 else '.'
def serve(route):
    p = route.request.url.split('https://app.test/', 1)[1].split('?')[0] or 'index.html'
    R = os.path.abspath(ROOT); f = os.path.abspath(os.path.join(R, p))
    if p.endswith('coi-serviceworker.js'): return route.fulfill(status=404, body=b'')   # as in the other tests: no service worker
    if not f.startswith(R + os.sep) or not os.path.isfile(f):
        return route.fulfill(status=404, body=b'')
    route.fulfill(status=200, body=open(f, 'rb').read(), content_type=mimetypes.guess_type(f)[0] or 'application/octet-stream')
HOST = """window.__calls=[];window.audiolabDesktop={isDesktop:true,platform:'darwin',version:()=>Promise.resolve('0.203.0'),programVersion:()=>Promise.resolve('0.203'),
 updateCheck:()=>Promise.resolve({status:'current'}),updateStatus:()=>Promise.resolve({}),onDock:()=>{},onFromChild:()=>{},onDockHover:()=>{},dac:null,
 listAppIcons:async()=>{const j=await (await fetch('desktop/icon-assets/picker/icons.json')).json();return{default:j.default,current:window.__cur||j.default,base:'desktop/icon-assets/picker/',platform:'darwin',groups:j.groups}},
 setAppIcon:async id=>{window.__calls.push(id);window.__cur=id;return{ok:true,current:id}}};"""
OLD = """window.audiolabDesktop={isDesktop:true,platform:'darwin',version:()=>Promise.resolve('0.190.0'),onDock:()=>{},onFromChild:()=>{},onDockHover:()=>{},dac:null};"""
def boot(b, init=None):
    ctx = b.new_context(viewport={'width': 1500, 'height': 950}, device_scale_factor=2); pg = ctx.new_page(); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)[:300])); pg.route('https://app.test/**', alsong(serve))
    pg.add_init_script("if(!localStorage.getItem('audiolab-ui'))localStorage.setItem('audiolab-ui',JSON.stringify({splash:false,lat3:1}))")
    if init: pg.add_init_script(init)
    pg.goto('https://app.test/index.html'); pg.wait_for_function("()=>window.AudioLab&&window.AudioLab.version", timeout=60000); pg.wait_for_timeout(2500)
    return ctx, pg, errs
def run(pg, c): return pg.evaluate("c=>window.AudioLab.run(c)", c)
def open_colours(pg):
    run(pg, "openSettings('colors')"); pg.wait_for_timeout(300)
    pg.evaluate("()=>document.getElementById('apicBox').scrollIntoView()"); pg.wait_for_timeout(1500)
FAV = "()=>[...document.querySelectorAll('link[rel~=icon],link[rel=apple-touch-icon]')].map(l=>l.getAttribute('href')).join(' ')"
STATE = "()=>JSON.stringify({groups:[...document.querySelectorAll('#apicBox .apicg')].map(e=>e.textContent),tiles:document.querySelectorAll('#apicBox [data-apic]').length,on:[...document.querySelectorAll('#apicBox .apict.on')].map(b=>b.dataset.apic),def:[...document.querySelectorAll('#apicBox .apict em')].map(e=>e.closest('[data-apic]').dataset.apic+':'+e.textContent),untitled:[...document.querySelectorAll('#apicBox [data-apic]')].filter(b=>!b.title).length,codes:/\\b(KX|KP|VA|FE)\\d/.test(document.getElementById('apicBox').textContent),loaded:[...document.querySelectorAll('#apicBox img')].filter(i=>i.complete&&i.naturalWidth>0).length,note:(document.querySelector('#apicBox .apicnote')||{}).textContent||document.getElementById('apicBox').textContent})"
with sync_playwright() as p:
    b = p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
    # 1. browser
    ctx, pg, errs = boot(b)
    print('version', run(pg, 'VERSION'), 'errors on load', errs, 'favicons', pg.evaluate(FAV))
    print('picker before opening Settings', pg.evaluate("()=>document.querySelectorAll('#apicBox [data-apic]').length"), 'images requested', pg.evaluate("()=>performance.getEntriesByType('resource').filter(e=>e.name.includes('icon-assets')).length"))
    open_colours(pg); print('web picker', pg.evaluate(STATE))
    pg.screenshot(path=os.path.join(OUT, 'appicon_picker.png'))
    pg.click('#apicBox [data-apic=sputnik]'); pg.wait_for_timeout(300)
    print('after click: on', pg.evaluate("()=>[...document.querySelectorAll('#apicBox .apict.on')].map(b=>b.dataset.apic)"), 'stored', pg.evaluate("()=>localStorage.getItem('audiolab-app-icon')"), 'favicons', pg.evaluate(FAV))
    pg.reload(); pg.wait_for_function("()=>window.AudioLab&&window.AudioLab.version", timeout=60000); pg.wait_for_timeout(2000)
    print('after reload: favicons', pg.evaluate(FAV)); open_colours(pg); print('after reload: on', pg.evaluate("()=>[...document.querySelectorAll('#apicBox .apict.on')].map(b=>b.dataset.apic)"))
    pg.click('#apicBox [data-apic=ocean-yellow]'); pg.wait_for_timeout(200); print('back to default: favicons', pg.evaluate(FAV))
    pg.fill('#setQ', 'app icon'); pg.wait_for_timeout(200); print('search "app icon":', pg.evaluate("()=>[...document.querySelectorAll('#setQR [data-qi] b')].map(e=>e.textContent).slice(0,3)"))
    pg.keyboard.press('Enter'); pg.wait_for_timeout(600); print('search took you to', pg.evaluate("()=>document.querySelector('#setNav .on').textContent.trim()"), 'picker visible', pg.evaluate("()=>{const r=document.getElementById('apicBox').getBoundingClientRect();return r.top<innerHeight&&r.bottom>0}"))
    pg.fill('#setQ', 'dock'); pg.wait_for_timeout(200); print('search "dock":', pg.evaluate("()=>[...document.querySelectorAll('#setQR [data-qi] b')].map(e=>e.textContent).slice(0,3)"))
    print('errors after use', errs); ctx.close()
    # 2. new desktop app (pretend host)
    ctx, pg, errs = boot(b, HOST); open_colours(pg); print('desktop picker', pg.evaluate(STATE))
    pg.click('#apicBox [data-apic=ink-electric]'); pg.wait_for_timeout(300)
    print('host calls', pg.evaluate("()=>window.__calls"), 'on', pg.evaluate("()=>[...document.querySelectorAll('#apicBox .apict.on')].map(b=>b.dataset.apic)"), 'favicons unchanged', pg.evaluate(FAV), 'errors', errs)
    pg.screenshot(path=os.path.join(OUT, 'appicon_desktop.png'), clip={'x': 0, 'y': 0, 'width': 1500, 'height': 950}); ctx.close()
    # 3. older desktop app
    ctx, pg, errs = boot(b, OLD); open_colours(pg); print('older app shows:', pg.evaluate("()=>document.getElementById('apicBox').textContent"), 'errors', errs); ctx.close()
    b.close()
