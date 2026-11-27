# DR2: screenshots of the pick page at 1280x720 and 1920x1080 (dark and light page theme, both app looks), console errors, draw times
import sys,os,json,http.server,threading,functools
from playwright.sync_api import sync_playwright
D=os.path.join(os.path.dirname(os.path.abspath(__file__)),'page');OUT=sys.argv[1] if len(sys.argv)>1 else '/tmp/dr2shots'
os.makedirs(OUT,exist_ok=True)
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*a):pass
srv=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Q,directory=D));threading.Thread(target=srv.serve_forever,daemon=True).start()
url=f'http://127.0.0.1:{srv.server_port}/index.html'
SKEL='<!doctype html><html><head><meta charset=utf8><meta name=viewport content="width=device-width,initial-scale=1,viewport-fit=cover"></head><body>'
with sync_playwright() as p:
    b=p.chromium.launch()
    for (w,h,sch) in ((1280,720,'dark'),(1920,1080,'light'),(400,800,'dark')):
        pg=b.new_page(viewport={'width':w,'height':h},color_scheme=sch);errs=[]
        pg.on('pageerror',lambda e:errs.append(str(e)[:300]));pg.on('console',lambda m:errs.append(m.text[:200]) if m.type=='error' else None)
        pg.route('**/index.html',lambda r:r.fulfill(status=200,content_type='text/html',body=(SKEL+open(D+'/index.html',encoding='utf-8').read()).encode()))
        pg.goto(url);pg.wait_for_timeout(2500)
        print(w,h,sch,'errors',errs[:5],'scrollW',pg.evaluate('document.documentElement.scrollWidth'))
        for sec in ('A','P','B','T'):
            pg.evaluate(f"document.getElementById('{sec}').scrollIntoView()");pg.wait_for_timeout(400)
            pg.screenshot(path=f'{OUT}/{w}_{sec}.png')
            if w==1280:
                pg.screenshot(path=f'{OUT}/{w}_{sec}_full.png',full_page=False)
        if w==1280:
            pg.click('#lkL');pg.wait_for_timeout(500);pg.evaluate("document.getElementById('T').scrollIntoView()");pg.wait_for_timeout(300);pg.screenshot(path=f'{OUT}/{w}_T_lite.png')
            pg.click('#lkD');pg.click('#useRec');pg.wait_for_timeout(200);print('rec line:',pg.inner_text('#picks'))
            bench=pg.evaluate('window.__bench()');json.dump(bench,open(OUT+'/bench.json','w'));print('bench max',max(bench,key=lambda x:x[1]),'sum',round(sum(x[1] for x in bench),1))
        pg.close()
    b.close()
