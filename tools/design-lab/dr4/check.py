# DR4: headless check of the pick page: console errors, calibration with the 1 kHz sine, screenshots of every family (dark), one phone-width shot.
import sys,os,json
from playwright.sync_api import sync_playwright
H=os.path.dirname(os.path.abspath(__file__));out=sys.argv[1] if len(sys.argv)>1 else os.path.join(H,'shots');os.makedirs(out,exist_ok=True)
src=open(os.path.join(H,'instruments.html'),encoding='utf-8').read()
page='<!doctype html><html><head><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1"></head><body>'+src+'</body></html>'
with sync_playwright() as p:
    b=p.chromium.launch()
    for scheme,w in (('dark',1300),('light',400)):
        cx=b.new_context(viewport={'width':w,'height':900},color_scheme=scheme,device_scale_factor=1);pg=cx.new_page();errs=[]
        pg.on('pageerror',lambda e:errs.append(str(e)[:300]));pg.on('console',lambda m:errs.append('C:'+m.text[:300]) if m.type=='error' else None)
        pg.route('https://t.test/**',lambda r:r.fulfill(status=200,content_type='text/html',body=page))
        pg.goto('https://t.test/p.html');pg.wait_for_timeout(1500)
        if scheme=='dark':
            pg.select_option('#sigSel','tone');pg.evaluate("()=>{document.getElementById('fam-L').scrollIntoView()}");pg.wait_for_timeout(4500)
            v=pg.evaluate("()=>{const E=__dr4.E,r=E.rec;return {pk:r.pk,tp:r.tp,rms:r.rms,vu:r.vu,ppm:r.ppm,M:E.M,S:E.S,I:E.I,corr:r.corr,t:E.t}}");print('tone',json.dumps(v))
            pg.select_option('#sigSel','pink');pg.wait_for_timeout(4000)
            v=pg.evaluate("()=>{const E=__dr4.E,r=E.rec;return {rms:r.rms,M:E.M,S:E.S,corr:r.corr,width:r.width}}");print('pink',json.dumps(v))
            pg.select_option('#sigSel','mix');pg.wait_for_timeout(500)
            for f in 'MLSOGEVCD':
                pg.evaluate("f=>document.getElementById('fam-'+f).scrollIntoView()",f);pg.wait_for_timeout(2500)
                pg.locator('#fam-'+f).screenshot(path=os.path.join(out,'fam_'+f+'.png'))
            ms=pg.evaluate("()=>__dr4.CARDS.filter(k=>k.ms.length).map(k=>[k.id,+(k.ms.slice().sort((a,b)=>a-b)[k.ms.length>>1]).toFixed(3)])");print('ms',ms)
            pg.click('#useRec');print(pg.inner_text('#picks'))
        else:
            pg.wait_for_timeout(1500);pg.screenshot(path=os.path.join(out,'phone_top.png'));sw=pg.evaluate("()=>[document.documentElement.scrollWidth,innerWidth]");print('phone scroll width',sw)
        print(scheme,'errors',errs[:6]);cx.close()
    b.close()
