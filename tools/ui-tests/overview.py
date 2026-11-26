import sys,json
from playwright.sync_api import sync_playwright
OUT='/tmp/'
def boot(p,scale=1,w=1600,h=1000):
    src=open(sys.argv[1] if len(sys.argv)>1 else 'index.html',encoding='utf-8').read()
    b=p.chromium.launch();pg=b.new_page(viewport={'width':w,'height':h},device_scale_factor=scale);errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e)[:300]));pg.on('console',lambda m:errs.append('C:'+m.text[:300]) if m.type=='error' and 'net::' not in m.text and '404' not in m.text else None)
    pg.route('https://app.test/**',lambda r:r.fulfill(status=200,content_type='text/html',body=src.encode()) if r.request.url.endswith('.html') else r.fulfill(status=404,body=b''))
    pg.add_init_script("localStorage.setItem('audiolab-ui',JSON.stringify({splash:false,lat3:1}))")
    pg.goto('https://app.test/index.html');pg.wait_for_timeout(9000)
    return b,pg,errs
def run(pg,code):
    return pg.evaluate("c=>window.AudioLab.run(c)",code)
# overview mode test (v0.163): python3 tools/ui-tests/overview.py index.html
import time
def st(pg):
    return run(pg,"JSON.stringify({on:OVW.on,e:+OVW.e.toFixed(2),z:+OVW.z.toFixed(2),ox:OVW.x&&+OVW.x.toFixed(1),oy:OVW.y,V,pos,selT:(S.tracks.find(t=>t.id===selT)||{}).name,play:play.on})")
with sync_playwright() as p:
    b,pg,errs=boot(p,scale=1)
    run(pg,"(()=>{const c=document.getElementById('liteNote');if(c)c.remove();selectTrack(S.tracks[4].id);V.ppb=6;V.x=200;V.y=300;V.th=60;clampV();dirty=true})()");pg.wait_for_timeout(300)
    V0=run(pg,"JSON.stringify(V)");print('V0',V0)
    # 1 wheel zoom out to the far end then beyond
    pg.mouse.move(800,250)
    pg.keyboard.down('Control')
    n=0
    for i in range(60):
        pg.mouse.wheel(0,100);pg.wait_for_timeout(260);n+=1
        if run(pg,"OVW.on"):break
    pg.keyboard.up('Control')
    print('notches to enter',n,st(pg))
    Vfar=run(pg,"JSON.stringify(OVW.sv)");print('saved',Vfar)
    pg.wait_for_timeout(400);pg.screenshot(path=OUT+'d_over.png')
    print('top el',pg.evaluate("()=>{const e=document.elementFromPoint(800,250),f=document.elementFromPoint(60,200);return [e&&e.id,f&&f.id]}"))
    # zoom out more in overview: nothing
    pg.keyboard.down('Control');pg.mouse.wheel(0,100);pg.wait_for_timeout(300);print('out more',st(pg))
    # zoom in within overview
    pg.mouse.move(1000,300);pg.mouse.wheel(0,-60);pg.wait_for_timeout(400);print('in1',st(pg));pg.keyboard.up('Control')
    pg.screenshot(path=OUT+'e_over_zoom.png')
    # pan
    pg.mouse.wheel(120,0);pg.wait_for_timeout(300);print('pan',st(pg))
    # click to place playhead + select track
    pg.mouse.click(1000,300);pg.wait_for_timeout(200);print('click',st(pg))
    pg.mouse.click(60,214);pg.wait_for_timeout(200);print('tab click',st(pg))
    # drag pan
    pg.mouse.move(900,300);pg.mouse.down();pg.mouse.move(700,300,steps=5);pg.mouse.up();pg.wait_for_timeout(200);print('drag',st(pg))
    # play
    pg.keyboard.press('Space');pg.wait_for_timeout(1200);print('play',st(pg),run(pg,"curDisp().toFixed(1)"));pg.screenshot(path=OUT+'f_play.png');pg.keyboard.press('Space');pg.wait_for_timeout(300)
    # zoom in past the top: leave at pointer
    hit=run(pg,"JSON.stringify((()=>{const H=ovwAt({x:1000,y:300});return {b:H.b,ti:H.ti}})())");print('under pointer',hit)
    pg.mouse.move(1000,300);pg.keyboard.down('Control')
    for i in range(20):
        pg.mouse.wheel(0,-100);pg.wait_for_timeout(260)
        if not run(pg,"OVW.on"):break
    pg.keyboard.up('Control');pg.wait_for_timeout(500)
    print('left after',i+1,st(pg));print('now under pointer',run(pg,"JSON.stringify({b:V.x+(1000-X0)/V.ppb,ti:trackAt(300-AY+V.y)})"),'cls',pg.evaluate("document.body.className"))
    pg.screenshot(path=OUT+'g_back.png')
    # key command + Esc
    pg.keyboard.press('Shift+O');pg.wait_for_timeout(80);pg.screenshot(path=OUT+'h_anim.png');pg.wait_for_timeout(400);print('key',st(pg))
    pg.keyboard.press('Escape');pg.wait_for_timeout(500);print('esc',st(pg))
    # zoom keys
    run(pg,"scSet('zoomout','G');scSet('zoomin','H')")
    k=0
    for i in range(30):
        pg.keyboard.press('g');pg.wait_for_timeout(230);k+=1
        if run(pg,"OVW.on"):break
    print('key presses',k,st(pg))
    for i in range(40):  # v0.194: the overview starts at the normal view's scale, so from a far zoom-out it takes more steps
        pg.keyboard.press('h');pg.wait_for_timeout(230)
        if not run(pg,"OVW.on"):break
    pg.wait_for_timeout(400);print('zoom-in keys to leave',i+1,st(pg))
    # dblclick + chip
    run(pg,"ovwToggle()");pg.wait_for_timeout(400);pg.mouse.dblclick(1200,180);pg.wait_for_timeout(500);print('dbl',st(pg),run(pg,"JSON.stringify({b:V.x+(1200-X0)/V.ppb,ti:trackAt(180-AY+V.y)})"))
    pg.screenshot(path=OUT+'i_dbl.png')
    run(pg,"ovwToggle()");pg.wait_for_timeout(400);pg.click('#ovwChip');pg.wait_for_timeout(500);print('chip',st(pg))
    # menus
    pg.mouse.click(800,430,button='right');pg.wait_for_timeout(300);print('menu',pg.evaluate("()=>document.getElementById('ctxm').innerText.replace(/\\n/g,' | ')"));pg.keyboard.press('Escape')
    print(errs[:8]);b.close()
