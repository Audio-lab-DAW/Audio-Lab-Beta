import sys,json
import sys as _ws_sys, os as _ws_os; _ws_sys.path.insert(0, _ws_os.path.join(_ws_os.path.dirname(_ws_os.path.abspath(__file__)), '../test-songs')); from alsong import alsong  # task WS-F: the test songs
from playwright.sync_api import sync_playwright
def boot(p,f=(sys.argv[1] if len(sys.argv)>1 else "index.html"),scale=1,w=1600,h=1000,ui='{splash:false,lat3:1}'):
    src=open(f,encoding='utf-8').read()
    b=p.chromium.launch();pg=b.new_page(viewport={'width':w,'height':h},device_scale_factor=scale);errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e)[:400]));pg.on('console',lambda m:errs.append('C:'+m.text[:300]) if m.type=='error' and 'net::' not in m.text and '404' not in m.text else None)
    pg.route('https://app.test/**',alsong(lambda r:r.fulfill(status=200,content_type='text/html',body=src.encode()) if r.request.url.endswith('.html') else r.fulfill(status=404,body=b'')))
    pg.add_init_script("if(!localStorage.getItem('audiolab-ui'))localStorage.setItem('audiolab-ui',JSON.stringify(%s))"%ui)
    pg.goto('https://app.test/index.html');pg.wait_for_timeout(9000)
    return b,pg,errs
def run(pg,code): return pg.evaluate("c=>window.AudioLab.run(c)",code)
# mixer cable lane test (v0.165): python3 tools/ui-tests/cables2.py index.html   (screenshots go to the current folder)
with sync_playwright() as p:
    b,pg,errs=boot(p)
    run(pg,"(()=>{const c=document.getElementById('liteNote');if(c)c.remove();openMixer()})()");pg.wait_for_timeout(1500)
    g=pg.locator('#mixWin .cabrz').bounding_box()
    pg.mouse.move(g['x']+700,g['y']+3);pg.mouse.down();pg.mouse.move(g['x']+700,g['y']-110,steps=8);pg.mouse.up();pg.wait_for_timeout(700)
    print(run(pg,"JSON.stringify({h:cabH(),st:UI.mxs,win:UI.win.mixWin})"))
    pg.screenshot(path='m5.png',clip={'x':0,'y':80,'width':1600,'height':620})
    pg.click('#mixWin .cablg [data-cl=sel]');pg.wait_for_timeout(300)
    run(pg,"selectTrack(S.tracks[7].id)");pg.wait_for_timeout(400);pg.screenshot(path='m6.png',clip={'x':0,'y':380,'width':1600,'height':320})
    pg.click('#mixWin .cablg [data-cl=sel]');pg.click('#mixWin .cablg [data-cl=out]');pg.wait_for_timeout(400);pg.screenshot(path='m7.png',clip={'x':0,'y':380,'width':1600,'height':320})
    pg.click('#mixWin .cablg [data-cl=out]');pg.click('#mixWin .cablg [data-cl=sty]');pg.wait_for_timeout(400);pg.screenshot(path='m8.png',clip={'x':0,'y':380,'width':1600,'height':320})
    pg.click('#mixWin .cablg [data-cl=sty]');pg.wait_for_timeout(300)
    pt=pg.evaluate("()=>{for(const p of document.querySelectorAll('#mixWin svg.cabs .chit')){const L=p.getTotalLength(),q=p.getPointAtLength(L*.03),m=p.getScreenCTM();const x=q.x*m.a+m.e,y=q.y*m.d+m.f+14;if(x>300&&x<1200){const el=document.elementFromPoint(x,y);return [x,y,el&&(el.tagName+'.'+(el.getAttribute('class')||''))]}}}");print(pt)
    pg.mouse.move(pt[0],pt[1]);pg.wait_for_timeout(400);pg.screenshot(path='m9.png',clip={'x':0,'y':380,'width':1600,'height':320})
    pg.mouse.click(pt[0],pt[1]);pg.wait_for_timeout(300);print('pop',pg.evaluate("()=>{const p=document.getElementById('cabPop');return p&&p.textContent.slice(0,80)}"))
    pg.keyboard.press('Escape')
    # drag a new cable from socket of track 2 to last return
    print('before',run(pg,"cabList().length"))
    sk=pg.locator('#mixWin svg.cabs .cabsk').nth(4).bounding_box();tg=pg.locator('#mixWin .mx[data-id]').nth(9).bounding_box()
    pg.mouse.move(sk['x']+5,sk['y']+5);pg.mouse.down();pg.mouse.move(tg['x']+40,tg['y']+200,steps=8);pg.wait_for_timeout(200);pg.screenshot(path='m10.png',clip={'x':0,'y':80,'width':1600,'height':620});pg.mouse.up();pg.wait_for_timeout(300)
    print('menu',pg.evaluate("()=>!ctxm.hidden&&ctxm.textContent.slice(0,120)"));pg.keyboard.press('Escape')
    pg.locator('#mixWin .cabrz').dblclick(position={'x':700,'y':3});pg.wait_for_timeout(500);print(run(pg,"JSON.stringify({h:cabH(),st:UI.mxs})"))
    # compact + reload persistence
    run(pg,"mxsSet('cabH',120)");pg.reload();pg.wait_for_timeout(9000)
    run(pg,"(()=>{const c=document.getElementById('liteNote');if(c)c.remove();openMixer()})()");pg.wait_for_timeout(1500);print('after reload',run(pg,"cabH()"))
    run(pg,"mxsSet('compact',1)");pg.wait_for_timeout(600);pg.screenshot(path='m11.png',clip={'x':0,'y':80,'width':1600,'height':620})
    run(pg,"mxsSet('cab',0)");pg.wait_for_timeout(400);print('off',pg.evaluate("()=>[!!document.querySelector('#mixWin svg.cabs'),!!document.querySelector('#mixWin .cabrz'),!!document.querySelector('#mixWin .cablg')]"))
    run(pg,"mxsSet('cab',1)");pg.wait_for_timeout(400)
    print(errs);b.close()
