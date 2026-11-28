# Load time and splash time (v0.195, task U). python3 tools/ui-tests/loadtime.py index.html [cpu slowdown, e.g. 4] [runs]
# Runs reuse one browser profile, so from the second run on it is a normal start (the first run is a first start with the new-demo setup).
# Prints the moments (ms after navigation) the splash appears, the code is ready, the splash fades out and is removed, and the loading steps.
# From v0.224 (task SP1) the splash stays about 1.5 s after loading is done: 'rdy' is the moment loading is done (the app behind is usable), 'out' the start of the fade.
# load time and splash time: python3 load.py index.html [throttle] [runs]
import sys,json
import sys as _ws_sys, os as _ws_os; _ws_sys.path.insert(0, _ws_os.path.join(_ws_os.path.dirname(_ws_os.path.abspath(__file__)), '../test-songs')); from alsong import alsong  # task WS-F: the test songs
from playwright.sync_api import sync_playwright
idx=sys.argv[1];thr=float(sys.argv[2]) if len(sys.argv)>2 else 1;runs=int(sys.argv[3]) if len(sys.argv)>3 else 3
src=open(idx,encoding='utf-8').read().encode()
INIT="""if(!localStorage.getItem('audiolab-ui'))localStorage.setItem('audiolab-ui',JSON.stringify({lat3:1}));window.__T={};
new MutationObserver(()=>{const s=document.getElementById('splash');const n=performance.now();if(s&&!__T.show)__T.show=n;if(s&&s.classList.contains('rdy')&&!__T.rdy)__T.rdy=n;if(s&&s.classList.contains('out')&&!__T.out)__T.out=n;if(__T.show&&!s&&!__T.gone)__T.gone=n}).observe(document,{childList:true,subtree:true,attributes:true,attributeFilter:['class']});
addEventListener('DOMContentLoaded',()=>__T.dcl=performance.now());addEventListener('load',()=>__T.load=performance.now());
(function f(){if(window.AudioLab&&window.AudioLab.version&&!__T.api)__T.api=performance.now();if(!__T.gone)requestAnimationFrame(f)})();
new PerformanceObserver(l=>{for(const e of l.getEntries())if(e.name==='first-contentful-paint')__T.fcp=e.startTime}).observe({type:'paint',buffered:true});"""
with sync_playwright() as p:
    b=p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required']);cx=b.new_context(viewport={'width':1600,'height':1000})
    for r in range(runs):
        pg=cx.new_page();errs=[]
        pg.on('pageerror',lambda e:errs.append(str(e)[:300]))
        if thr>1:
            c=pg.context.new_cdp_session(pg);c.send('Emulation.setCPUThrottlingRate',{'rate':thr})
        pg.route('https://app.test/**',alsong(lambda r:r.fulfill(status=200,content_type='text/html',body=src) if r.request.url.endswith('.html') else r.fulfill(status=404,body=b'')))
        pg.add_init_script(INIT)
        pg.goto('https://app.test/index.html');pg.wait_for_function("()=>window.__T&&window.__T.gone",timeout=120000)
        T=pg.evaluate("window.__T");print(pg.evaluate("JSON.stringify(window.AudioLab.run(\"JSON.stringify(BOOTU)\"))"));print(json.dumps({k:round(v) for k,v in T.items()}),'errors',errs)
        pg.close()
    b.close()
