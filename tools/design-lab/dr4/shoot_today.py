# DR4: headless screenshots of today's meters, scopes and analyzers (v0.2xx). python3 shoot_today.py ../../../index.html today
import sys,os
import sys as _ws_sys, os as _ws_os; _ws_sys.path.insert(0, _ws_os.path.join(_ws_os.path.dirname(_ws_os.path.abspath(__file__)), '../../test-songs')); from alsong import alsong  # task WS-F: the test songs
from playwright.sync_api import sync_playwright
f=sys.argv[1];out=sys.argv[2];os.makedirs(out,exist_ok=True);src=open(f,encoding='utf-8').read().encode()
R=lambda pg,c:pg.evaluate("c=>window.AudioLab.run(c)",c)
def shot(pg,sel,name,pad=0):
    try:
        bb=pg.locator(sel).first.bounding_box()
        if not bb or bb['width']<2:print('no box',sel);return
        pg.screenshot(path=os.path.join(out,name+'.png'),clip={'x':max(0,bb['x']-pad),'y':max(0,bb['y']-pad),'width':bb['width']+2*pad,'height':bb['height']+2*pad})
    except Exception as e:print('fail',sel,str(e)[:200])
with sync_playwright() as p:
    b=p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
    cx=b.new_context(viewport={'width':1600,'height':1000},device_scale_factor=1);pg=cx.new_page();errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e)[:200]))
    pg.route('https://app.test/**',alsong(lambda r:r.fulfill(status=200,content_type='text/html',body=src) if r.request.url.endswith('.html') else r.fulfill(status=404,body=b'')))
    pg.add_init_script("localStorage.setItem('audiolab-ui',JSON.stringify({splash:false,lat3:1}))")
    pg.goto('https://app.test/index.html');pg.wait_for_timeout(9000)
    pg.evaluate("()=>{const n=document.getElementById('liteNote');if(n)n.remove()}")
    R(pg,"S.mfx.push(mkFx('eq'));S.mfx.push(mkFx('limit'));S.mfx.push(mkFx('loud'));const t=S.tracks[0];t.fx.push(mkFx('comp'));changed(true);")
    R(pg,"pos=48*4;start()");pg.wait_for_timeout(6000)
    pg.screenshot(path=os.path.join(out,'full_arrange.png'))
    shot(pg,'#mtr','transport_meter',30);shot(pg,'#lufsB','lufs_box',6);shot(pg,'#cpu','cpu',6);shot(pg,'#peakBox','peakbox',6)
    R(pg,"selectTrack(S.tracks[0].id);renderFx()");pg.wait_for_timeout(1500);pg.screenshot(path=os.path.join(out,'devices_comp.png'))
    R(pg,"selectTrack('__m');renderFx()");pg.wait_for_timeout(2500);pg.screenshot(path=os.path.join(out,'devices_master.png'))
    R(pg,"openMixer()");pg.wait_for_timeout(2500);shot(pg,'#mixWin','mixer')
    R(pg,"UI.mxView='stereo';try{drawMixer()}catch(e){}");pg.wait_for_timeout(2000);shot(pg,'#mixWin','mixer_stereo')
    R(pg,"UI.mxView='spec'");pg.wait_for_timeout(1500);shot(pg,'#mixWin','mixer_spec')
    R(pg,"UI.mxView='meter'");
    R(pg,"try{closeMixer()}catch(e){document.getElementById('mixWin').hidden=true}")
    R(pg,"UI.viz=true;UI.vizMode='all';vizApply()");pg.wait_for_timeout(2500);pg.screenshot(path=os.path.join(out,'visualizer.png'))
    R(pg,"lmOpen()");pg.wait_for_timeout(1500);shot(pg,'#lufsPop','lufs_pop',4)
    R(pg,"spoOpen('master')");pg.wait_for_timeout(2500);pg.screenshot(path=os.path.join(out,'spectrum_overlay.png'))
    print('errors',errs[:5])
    b.close()
