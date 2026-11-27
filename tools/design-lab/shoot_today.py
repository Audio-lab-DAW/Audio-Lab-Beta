# DR2: headless screenshots of today's arrangement, piano roll, browser and transport
# python3 tools/design-lab/shoot_today.py [index.html]  -> tools/design-lab/today/*.png
import sys,json,os
from playwright.sync_api import sync_playwright
SRC=sys.argv[1] if len(sys.argv)>1 else 'index.html'
OUT=os.path.join(os.path.dirname(__file__),'today')
src=open(SRC,encoding='utf-8').read()
def page(b,lite):
    pg=b.new_page(viewport={'width':1600,'height':900},device_scale_factor=1);errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e)[:200]))
    pg.route('https://app.test/**',lambda r:r.fulfill(status=200,content_type='text/html',body=src.encode()) if r.request.url.endswith('.html') else r.fulfill(status=404,body=b''))
    pg.add_init_script("localStorage.setItem('audiolab-ui',JSON.stringify(%s))"%json.dumps({'splash':False,'lat3':1,'lite':lite,'liteMan':lite}))
    pg.goto('https://app.test/index.html');pg.wait_for_function("()=>window.AudioLab&&window.AudioLab.version",timeout=90000);pg.wait_for_timeout(4000)
    # hold the look: the headless machine is slow, so the app would switch itself to Light mode
    pg.evaluate("l=>window.AudioLab.run('(()=>{UI.lite='+l+';UI.liteMan='+l+';applyLite();const n=document.getElementById(\"liteNote\");if(n)n.remove();return 1})()')",'true' if lite else 'false');pg.wait_for_timeout(800)
    return pg,errs
R=lambda pg,c:pg.evaluate("c=>window.AudioLab.run(c)",c)
def rect(pg,sel):
    return pg.evaluate("s=>{const e=document.querySelector(s);if(!e)return null;const r=e.getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height}}",sel)
with sync_playwright() as p:
    b=p.chromium.launch()
    for lite,tag in ((False,'dark'),(True,'light')):
        pg,errs=page(b,lite)
        print(tag,'version',pg.evaluate("window.AudioLab.version"))
        R(pg,"(()=>{const c=document.getElementById('liteNote');if(c)c.remove();return 1})()")
        pg.screenshot(path=f'{OUT}/full_{tag}.png')
        r=rect(pg,'#tr');print('tr',r)
        if r: pg.screenshot(path=f'{OUT}/transport_{tag}.png',clip={'x':0,'y':r['y'],'width':1600,'height':r['height']+4})
        r=rect(pg,'#arr');print('arr',r)
        if r: pg.screenshot(path=f'{OUT}/arrangement_{tag}.png',clip={'x':0,'y':r['y'],'width':1600,'height':min(r['height'],520)})
        R(pg,"(()=>{const t=S.tracks.find(t=>t.clips&&t.clips.some(c=>c.notes&&c.notes.length))||S.tracks[1];openPR(t,t.clips.find(c=>c.notes&&c.notes.length)||t.clips[0]);return 1})()");pg.wait_for_timeout(900)
        pg.screenshot(path=f'{OUT}/pianoroll_{tag}.png')
        pg.keyboard.press('Escape');pg.wait_for_timeout(400)
        R(pg,"(()=>{document.querySelectorAll('[id^=pr]').forEach(()=>0);openBrowser();return 1})()");pg.wait_for_timeout(900)
        pg.screenshot(path=f'{OUT}/browser_{tag}.png')
        print(tag,'errors',errs[:4]);pg.close()
    b.close()
