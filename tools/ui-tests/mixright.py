import sys,json
from playwright.sync_api import sync_playwright
def boot(p,f=(sys.argv[1] if len(sys.argv)>1 else "index.html"),scale=1,w=1600,h=1000,ui='{splash:false,lat3:1}'):
    src=open(f,encoding='utf-8').read()
    b=p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required']);pg=b.new_page(viewport={'width':w,'height':h},device_scale_factor=scale);errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e)[:400]));pg.on('console',lambda m:errs.append('C:'+m.text[:300]) if m.type=='error' and 'net::' not in m.text and '404' not in m.text else None)
    pg.route('https://app.test/**',lambda r:r.fulfill(status=200,content_type='text/html',body=src.encode()) if r.request.url.endswith('.html') else r.fulfill(status=404,body=b''))
    pg.add_init_script("if(!localStorage.getItem('audiolab-ui'))localStorage.setItem('audiolab-ui',JSON.stringify(%s))"%ui)
    pg.goto('https://app.test/index.html');pg.wait_for_timeout(9000)
    return b,pg,errs
def run(pg,code): return pg.evaluate("c=>window.AudioLab.run(c)",code)
# mixer cable lane test (v0.165): python3 tools/ui-tests/cables2.py index.html   (screenshots go to the current folder)
with sync_playwright() as p:
    b,pg,errs=boot(p)
# mixer anchored to the right and Settings > Interface (v0.167): python3 tools/ui-tests/mixright.py index.html
def st(pg): return run(pg,"(()=>{const w=document.getElementById('mixWin'),r=w.getBoundingClientRect(),h=w.querySelector(':scope>.fwh').getBoundingClientRect(),ms=w.querySelector('.mxs'),M=ms.querySelector('.mx.master').getBoundingClientRect();return JSON.stringify({n:S.tracks.length,l:Math.round(r.left),r:Math.round(r.right),w:Math.round(r.width),hl:Math.round(h.left),hr:Math.round(h.right),sw:ms.scrollWidth,cw:ms.clientWidth,Mr:Math.round(M.right),cls:w.className})})()")
with sync_playwright() as p:
    b,pg,errs=boot(p);pg.evaluate("()=>{const c=document.getElementById('liteNote');if(c)c.remove()}")
    pg.click('#mBtn');pg.wait_for_timeout(1200)
    pg.click('#mxSetB');pg.wait_for_timeout(400);pg.screenshot(path='d1.png')
    pg.click('#mxsPop .fdsel');pg.wait_for_timeout(300);pg.screenshot(path='d2.png')
    pg.click('#fdPop [data-fd="13"]');pg.wait_for_timeout(300)
    print('popup still open',pg.evaluate("()=>[!document.getElementById('mxsPop').hidden,document.getElementById('fdPop').hidden]"),run(pg,"mxsO().fd"))
    pg.keyboard.press('Escape');pg.wait_for_timeout(200)
    # scroll with sticky master
    run(pg,"document.querySelector('#mixWin .mxs').scrollLeft=900");pg.wait_for_timeout(500);pg.screenshot(path='d3.png');print('scrolled',st(pg))
    # drag left edge to narrow (cap)
    r=pg.evaluate("()=>{const r=document.getElementById('mixWin').getBoundingClientRect();return [r.left,r.top,r.height]}")
    pg.mouse.move(r[0]+2,r[1]+r[2]/2);pg.mouse.down();pg.mouse.move(r[0]+500,r[1]+r[2]/2,steps=6);pg.mouse.up();pg.wait_for_timeout(500);print('cap',st(pg),run(pg,"UI.mxCapW"))
    run(pg,"(()=>{pushUndo();const t=S.tracks.pop();changed(true);renderMixer()})()");pg.wait_for_timeout(400);print('cap -1 track',st(pg))
    r=pg.evaluate("()=>{const r=document.getElementById('mixWin').getBoundingClientRect();return [r.left,r.top,r.height]}")
    pg.mouse.move(r[0]+2,r[1]+r[2]/2);pg.mouse.down();pg.mouse.move(2,r[1]+r[2]/2,steps=6);pg.mouse.up();pg.wait_for_timeout(500);print('uncap',st(pg),run(pg,"UI.mxCapW||0"))
    # move the window by its tab, then compact
    h=pg.evaluate("()=>{const r=document.querySelector('#mixWin>.fwh').getBoundingClientRect();return [r.left+8,r.top+17]}")
    pg.mouse.move(h[0],h[1]);pg.mouse.down();pg.mouse.move(h[0]+150,h[1]-200,steps=5);pg.mouse.up();pg.wait_for_timeout(400);print('moved',st(pg))
    pg.click('#mxCmp');pg.wait_for_timeout(500);print('compact',st(pg));pg.screenshot(path='d4.png')
    pg.click('#mxCmp');pg.wait_for_timeout(500);print('normal',st(pg))
    # reset button
    run(pg,"openSettings('audio')");pg.wait_for_timeout(400);pg.click('#genReset');pg.wait_for_timeout(400);print('dlg',pg.evaluate("()=>{const d=document.getElementById('cdlg');return !d.hidden&&d.textContent.slice(0,90)}"));pg.keyboard.press('Escape')
    pg.reload();pg.wait_for_timeout(9000);print('after reload fd',run(pg,"mxsO().fd"),run(pg,"document.getElementById('hdrin').className"))
    print(errs);b.close()
