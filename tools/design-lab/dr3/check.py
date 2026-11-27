# task DR3: headless check of the pick page (wrapped in the artifact skeleton), screenshots at 1280x720 and 1920x1080.
#   python3 tools/design-lab/dr3/check.py tools/design-lab/dr3 outdir
import sys,os,http.server,threading,functools
from playwright.sync_api import sync_playwright
d=sys.argv[1];out=sys.argv[2];os.makedirs(out,exist_ok=True)
body=open(os.path.join(d,'directions.html'),encoding='utf-8').read()
page='<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"></head><body>'+body+'</body></html>'
open(os.path.join(d,'_check.html'),'w',encoding='utf-8').write(page)
srv=http.server.ThreadingHTTPServer(('127.0.0.1',8765),functools.partial(http.server.SimpleHTTPRequestHandler,directory=d))
threading.Thread(target=srv.serve_forever,daemon=True).start()
with sync_playwright() as p:
    b=p.chromium.launch()
    for w,h,mode in [(1280,720,'dark'),(1920,1080,'dark'),(1280,720,'bright'),(1280,720,'lite'),(400,800,'dark')]:
        pg=b.new_page(viewport={'width':w,'height':h});errs=[]
        pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('console',lambda m:errs.append(m.text) if m.type=='error' else None)
        pg.goto('http://127.0.0.1:8765/_check.html');pg.wait_for_timeout(2500)
        if mode!='dark':pg.click(f'#m-{mode}');pg.wait_for_timeout(1200)
        sw=pg.evaluate('document.documentElement.scrollWidth')
        print(w,h,mode,'errors',errs[:5],'scrollWidth',sw)
        pg.screenshot(path=f'{out}/top_{w}_{mode}.png')
        for code in ['ds1','ds2','ds3','ds4','ds5','ds6','ds7','ds8']:
            if w==1280 and mode=='dark' or (w==1920 and code in('ds7','ds2')) or (mode!='dark' and code in ('ds7','ds3','ds4')):
                pg.evaluate(f"document.getElementById('{code}').scrollIntoView()");pg.wait_for_timeout(700)
                pg.screenshot(path=f'{out}/{code}_{w}_{mode}.png')
        if w==1280 and mode=='dark':
            pg.click('#takeall');pg.wait_for_timeout(500);pg.evaluate("document.getElementById('details').scrollIntoView()");pg.wait_for_timeout(700)
            pg.screenshot(path=f'{out}/details_{w}.png');print('line:',pg.inner_text('#line'))
            print('ms:',pg.evaluate("[...document.querySelectorAll('td[data-ms]')].map(e=>e.dataset.ms+' '+e.textContent)"))
        pg.close()
    b.close()
srv.shutdown();os.remove(os.path.join(d,'_check.html'))
