import sys,json
import sys as _ws_sys, os as _ws_os; _ws_sys.path.insert(0, _ws_os.path.join(_ws_os.path.dirname(_ws_os.path.abspath(__file__)), '../test-songs')); from alsong import alsong  # task WS-F: the test songs
from playwright.sync_api import sync_playwright
src=open(sys.argv[1],encoding='utf-8').read()
with sync_playwright() as p:
    b=p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required']);pg=b.new_page(viewport={'width':1600,'height':1000});errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('https://app.test/**',alsong(lambda r:r.fulfill(status=200,content_type='text/html',body=src.encode()) if r.request.url.endswith('.html') else r.fulfill(status=404,body=b'')))
    pg.add_init_script("localStorage.setItem('audiolab-ui',JSON.stringify({splash:false,lat3:1}))")
    pg.goto('https://app.test/index.html');pg.wait_for_timeout(40000)
    r=pg.evaluate("""async()=>{const A=window.AudioLab;A.run("(()=>{UI.lite=false;document.body.classList.remove('lite');applyTrans();openMixer();UI.follow=false;pos=beatOf?16*4:64;start()})()");await new Promise(r=>setTimeout(r,3000));
     let draws=0;const P=CanvasRenderingContext2D.prototype,o=P.fillRect;const seen=new Set();P.fillRect=function(){if(this.canvas.classList.contains('mxv'))seen.add(this.canvas.dataset.id);return o.apply(this,arguments)};await new Promise(r=>setTimeout(r,1500));P.fillRect=o;
     const pk=document.querySelectorAll('.vm i u').length,vis=[...document.querySelectorAll('.vm i u')].filter(u=>u.style.display!=='none').length;A.run('stop()');return {v:A.run('VERSION'),mixerChannelsDrawn:seen.size,of:document.querySelectorAll('canvas.mxv').length,peakLines:pk,peakVisible:vis}}""")
    print(json.dumps(r),errs[:3]);pg.screenshot(path='/tmp/pat/mp.png');b.close()
