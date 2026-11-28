# DR2: extra 'Today' shots: arrangement zoomed in, effect browser, a device preset menu; dark, then Light mode
import sys,json,os
import sys as _ws_sys, os as _ws_os; _ws_sys.path.insert(0, _ws_os.path.join(_ws_os.path.dirname(_ws_os.path.abspath(__file__)), '../test-songs')); from alsong import alsong  # task WS-F: the test songs
sys.path.insert(0,os.path.dirname(__file__))
from playwright.sync_api import sync_playwright
SRC=sys.argv[1] if len(sys.argv)>1 else 'index.html'
OUT=os.path.join(os.path.dirname(__file__),'today')
src=open(SRC,encoding='utf-8').read()
R=lambda pg,c:pg.evaluate("c=>window.AudioLab.run(c)",c)
with sync_playwright() as p:
  b=p.chromium.launch()
  for lite,tag in ((False,'dark'),(True,'light')):
    pg=b.new_page(viewport={'width':1600,'height':900});errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e)[:200]))
    pg.route('https://app.test/**',alsong(lambda r:r.fulfill(status=200,content_type='text/html',body=src.encode()) if r.request.url.endswith('.html') else r.fulfill(status=404,body=b'')))
    pg.add_init_script("localStorage.setItem('audiolab-ui',JSON.stringify({splash:false,lat3:1,lite:%s,liteMan:%s}"%('true' if lite else 'false','true' if lite else 'false')+"))")
    pg.goto('https://app.test/index.html');pg.wait_for_function("()=>window.AudioLab&&window.AudioLab.version",timeout=90000);pg.wait_for_timeout(4000)
    # hold the look: the headless machine is slow, so the app would switch itself to Light mode
    pg.evaluate("l=>window.AudioLab.run('(()=>{UI.lite='+l+';UI.liteMan='+l+';applyLite();const n=document.getElementById(\"liteNote\");if(n)n.remove();return 1})()')",'true' if lite else 'false');pg.wait_for_timeout(800)
    print(R(pg,"(()=>{const n=document.getElementById('liteNote');if(n)n.remove();V.ppb=25;V.x=64;V.y=0;clampV();dirty=true;return JSON.stringify(S.tracks.map(t=>t.name+':'+(t.clips||[]).length+(t.clips&&t.clips[0]&&t.clips[0].buf?'A':'')))})()"))
    pg.wait_for_timeout(800);pg.screenshot(path=f'{OUT}/arr_zoom_'+tag+'.png',clip={'x':0,'y':30,'width':1600,'height':440})
    R(pg,"(()=>{const n=document.getElementById('liteNote');if(n)n.remove();return 1})()");pg.mouse.click(895,511);pg.wait_for_timeout(700);pg.screenshot(path=f'{OUT}/presetmenu_'+tag+'.png')
    pg.keyboard.press('Escape');pg.wait_for_timeout(300)
    R(pg,"(()=>{const n=document.getElementById('liteNote');if(n)n.remove();return 1})()");R(pg,"openFxBrowser(S.tracks[1]);1");pg.wait_for_timeout(900);pg.screenshot(path=f'{OUT}/fxbrowser_'+tag+'.png')
    print(tag,errs[:4]);pg.close()
  b.close()
