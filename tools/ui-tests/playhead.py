# Arrangement edges, playhead look and Follow (v0.192, task R).  python3 tools/ui-tests/playhead.py [index.html] [outdir]
# Checks: no page errors; time read-out format; the colon sits on the playhead line; the read-out is hidden behind project tabs and the plus button;
# every playhead shape draws; Follow toggles with a click and opens its menu with a right-click; the header column uses a rectangle clip plus the
# #arrCol strips (no polygon); frame time while playing for each shape. Screenshots of the corners go to outdir.
import sys,os,json
import sys as _ws_sys, os as _ws_os; _ws_sys.path.insert(0, _ws_os.path.join(_ws_os.path.dirname(_ws_os.path.abspath(__file__)), '../test-songs')); from alsong import alsong  # task WS-F: the test songs
from playwright.sync_api import sync_playwright
idx=sys.argv[1] if len(sys.argv)>1 else 'index.html';out=sys.argv[2] if len(sys.argv)>2 else '/tmp/phtest';os.makedirs(out,exist_ok=True)
src=open(idx,encoding='utf-8').read()
with sync_playwright() as p:
    b=p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required']);pg=b.new_page(viewport={'width':1600,'height':1000})
    errs=[];pg.on('pageerror',lambda e:errs.append(str(e)[:300]))
    pg.route('https://app.test/**',alsong(lambda r:r.fulfill(status=200,content_type='text/html',body=src.encode()) if r.request.url.endswith('.html') else r.fulfill(status=404,body=b'')))
    pg.add_init_script("localStorage.setItem('audiolab-ui',JSON.stringify({splash:false,lat3:1}))")
    pg.goto('https://app.test/index.html');pg.wait_for_function("()=>window.AudioLab&&window.AudioLab.version",timeout=60000);pg.wait_for_timeout(5000)
    R=lambda c:pg.evaluate("c=>AudioLab.run(c)",c)
    R("(()=>{pmSetOn(false);devHide(true)})()");pg.wait_for_timeout(800)
    t=R("[0,240,725,3723].map(s=>tmTime(s*S.bpm/60))");print('time read-outs',t);assert t==['00:00','04:00','12:05','1:02:03']
    R("(()=>{pos=0;V.x=-(800-X0)/V.ppb;dirty=true})()");pg.wait_for_timeout(300)
    d=R("(()=>{const s=$('#phFlag>s').getBoundingClientRect();return (s.left+s.right)/2-(X0+(curDisp()-V.x)*V.ppb+phCfg().w/2)})()");print('colon off the line by %.2f px'%d);assert abs(d)<.6
    hid=[]
    for bx in range(230,480,10):
        R("(()=>{pos=0;V.x=-(%d-X0)/V.ppb;dirty=true})()"%bx);pg.wait_for_timeout(50);hid.append(R("$('#phFlag').style.visibility"))
    print('read-out hidden behind the tabs:',all(h=='hidden' for h in hid));assert all(h=='hidden' for h in hid)
    print('clip of the arrangement',R("GB.clip"),'| strips canvas',R("!!(GB.col&&GB.col.style.display!=='none')"));assert 'polygon' not in R("GB.clip")
    for v,(x,y) in enumerate([(0,0),(40,250),(-30,0)]):
        R("(()=>{V.x=%s;V.y=%s;clampV();dirty=true})()"%(x,y));pg.wait_for_timeout(400);pg.screenshot(path=f'{out}/top{v}.png',clip={'x':0,'y':0,'width':520,'height':160})
        R("(()=>{V.x=%s;V.y=Math.max(0,TOTH-500);clampV();dirty=true})()"%x);pg.wait_for_timeout(400);pg.screenshot(path=f'{out}/bottom{v}.png',clip={'x':0,'y':300,'width':520,'height':590})
    R("(()=>{pos=48;V.x=40;V.y=0;dirty=true})()");pg.wait_for_timeout(300)
    fb=R("(()=>{const r=arr.getBoundingClientRect();return [r.left+FB.x+FB.w/2,r.top+FB.y+FB.h/2,FB.w]})()");print('Follow button width',fb[2])
    f0=R("UI.follow");pg.mouse.click(fb[0],fb[1]);pg.wait_for_timeout(100);f1=R("UI.follow");pg.mouse.click(fb[0],fb[1]);print('click toggles',f0,'->',f1);assert f0!=f1
    pg.mouse.click(fb[0],fb[1],button='right');pg.wait_for_timeout(300);m=R("[...document.querySelectorAll('#ctxm *')].map(e=>e.textContent).join('|').includes('Stay in place')");print('menu has the follow modes',m);assert m
    pg.keyboard.press('Escape')
    pg.click('#bPlay');pg.wait_for_timeout(1200);fr={}
    for s in R("PHSH.map(x=>x[0])"):
        R("UI.ph={s:'%s',w:2}"%s)
        fr[s]=pg.evaluate("()=>new Promise(res=>{const iv=[];let l=performance.now(),t0=l;const f=()=>{const n=performance.now();iv.push(n-l);l=n;if(n-t0<1000)requestAnimationFrame(f);else res(+(iv.reduce((a,b)=>a+b,0)/iv.length).toFixed(1))};requestAnimationFrame(f)})")
    pg.click('#bPlay');R("UI.ph={}");print('frame time ms while playing, per shape',json.dumps(fr))
    print('page errors',errs);assert not errs;b.close()
