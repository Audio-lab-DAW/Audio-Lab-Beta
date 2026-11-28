# task W (v0.199): picture per channel and the compact live picture menu, return channels, pan centre, effect dragging.
# python3 tools/ui-tests/taskW.py [index.html] [out-dir]
import sys,json,os
import sys as _ws_sys, os as _ws_os; _ws_sys.path.insert(0, _ws_os.path.join(_ws_os.path.dirname(_ws_os.path.abspath(__file__)), '../test-songs')); from alsong import alsong  # task WS-F: the test songs
from playwright.sync_api import sync_playwright
F=sys.argv[1] if len(sys.argv)>1 else 'index.html';OUT=sys.argv[2] if len(sys.argv)>2 else '.'
def boot(p,w=1920,h=1080,dsf=1):
    src=open(F,encoding='utf-8').read();b=p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required']);pg=b.new_page(viewport={'width':w,'height':h},device_scale_factor=dsf);errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e)[:400]))
    pg.route('https://app.test/**',alsong(lambda r:r.fulfill(status=200,content_type='text/html',body=src.encode()) if r.request.url.endswith('.html') else r.fulfill(status=404,body=b'')))
    pg.add_init_script("if(!localStorage.getItem('audiolab-ui'))localStorage.setItem('audiolab-ui',JSON.stringify({splash:false,lat3:1}))")
    pg.goto('https://app.test/index.html');pg.wait_for_timeout(9000);pg.evaluate("()=>{const c=document.getElementById('liteNote');if(c)c.remove()}");return b,pg,errs
def run(pg,c): return pg.evaluate("c=>window.AudioLab.run(c)",c)
def box(pg,sel): return json.loads(run(pg,"(()=>{const r=document.querySelector(%s).getBoundingClientRect();return JSON.stringify([r.left+r.width/2,r.top+r.height/2,r.width,r.height,r.left,r.top])})()"%json.dumps(sel)))
def gh(pg): return json.loads(run(pg,"(()=>{const g=document.querySelector('.w9gh');if(!g)return 'null';const r=g.getBoundingClientRect();return JSON.stringify([r.left,r.top,r.width,r.height])})()"))
def shot(pg,n,sel=None,pad=10):
    if sel: r=box(pg,sel);pg.screenshot(path=os.path.join(OUT,n),clip={'x':max(0,r[4]-pad),'y':max(0,r[5]-pad),'width':r[2]+2*pad,'height':r[3]+2*pad})
    else: pg.screenshot(path=os.path.join(OUT,n))
FT="""new Promise(res=>{let n=0,t0=0;const f=t=>{if(!t0)t0=t;if(++n<240)requestAnimationFrame(f);else{let a=performance.now();for(let i=0;i<40;i++)window.AudioLab.run('FRN=0;drawMixer();1');res(JSON.stringify({frame_ms:+((t-t0)/239).toFixed(2),drawMixer_ms:+((performance.now()-a)/40).toFixed(3)}))}};requestAnimationFrame(f)})"""
with sync_playwright() as p:
    b,pg,errs=boot(p,dsf=2);print('version',run(pg,"VERSION"),'errors on load',errs)
    pg.click('#mBtn');pg.wait_for_timeout(800);run(pg,"(()=>{UI.follow=false;pos=256;start();return 1})()");pg.wait_for_timeout(1200)
    # the picture menu of one channel, live
    c=box(pg,'#mixWin .mx:nth-child(3) canvas.mxv');pg.mouse.click(c[0],c[1],button='right');pg.wait_for_timeout(900);shot(pg,'w_menu_channel.png','#w9m')
    print('menu for',run(pg,"W9.id"),'previews',run(pg,"W9.pv.length"),'preview pixels lit',run(pg,"W9.pv.map(cv=>{const d=cv.getContext('2d').getImageData(0,0,cv.width,cv.height).data;let n=0;for(let i=0;i<d.length;i+=4)if(d[i]+d[i+1]+d[i+2]>60)n++;return n}).join(' ')"))
    print('frame time, menu open',pg.evaluate("()=>"+FT),'mixer open',run(pg,"!document.getElementById('mixWin').hidden"))
    pg.click('#w9m [data-w9v=stereo]');pg.wait_for_timeout(200)
    print('frame time, menu closed',pg.evaluate("()=>"+FT),'mixer open',run(pg,"!document.getElementById('mixWin').hidden"))
    for n,v in [(5,'meter'),(7,'spec'),(8,'sgram'),(9,'fun')]:
        c=box(pg,'#mixWin .mx:nth-child(%d) canvas.mxv'%n);pg.mouse.click(c[0],c[1],button='right');pg.wait_for_timeout(250);pg.click('#w9m [data-w9v=%s]'%v);pg.wait_for_timeout(100)
    pg.wait_for_timeout(1200);shot(pg,'w_per_channel.png','#mixWin')
    print('own pictures',run(pg,"JSON.stringify(S.tracks.filter(t=>t.mxv).map(t=>t.name+':'+t.mxv))"),'meter strip hides its side meters',run(pg,"getComputedStyle(document.querySelector('#mixWin .mx:nth-child(5) .fm')).display"))
    # options of an entry (right-click a preview), and the mixer-wide menu
    pg.click('#mxVw');pg.wait_for_timeout(500);shot(pg,'w_menu_all.png','#w9m')
    c=box(pg,'#w9m [data-w9v=spec]');pg.mouse.click(c[0],c[1],button='right');pg.wait_for_timeout(300);print('right-click on an entry opens',run(pg,"ctxm.hidden?'nothing':ctxm.querySelector('.mh').textContent"));pg.screenshot(path=os.path.join(OUT,'w_menu_options.png'))
    pg.keyboard.press('Escape');pg.keyboard.press('Escape');pg.wait_for_timeout(200)
    # pan right-click, fader right-click
    c=box(pg,'#mixWin .mx:nth-child(4) .mxp');pg.mouse.click(c[0],c[1],button='right');pg.wait_for_timeout(200);print('right-click pan:',run(pg,"ctxm.hidden?'nothing':ctxm.querySelector('.mh').textContent"));pg.keyboard.press('Escape')
    c=box(pg,'#mixWin .mx:nth-child(4) .fwrap');pg.mouse.click(c[0]-12,c[1],button='right');pg.wait_for_timeout(200);print('right-click fader:',run(pg,"ctxm.hidden?'nothing':ctxm.querySelector('.mh').textContent"));pg.keyboard.press('Escape')
    # saved with the project
    pg.wait_for_timeout(700);print('saved with the project',run(pg,"JSON.parse(localStorage.getItem(KEY)).tracks.filter(t=>t.mxv).length"))
    # pan centre in each style, playing and silent
    for st in ['slider','half','full']:
        run(pg,"mxsSet('panst','%s');document.querySelector('#mixWin .mxs').scrollLeft=0;1"%st);pg.wait_for_timeout(900);r=box(pg,'#mixWin .mx:nth-child(6) .mxp');pg.screenshot(path=os.path.join(OUT,'w_pan_%s.png'%st),clip={'x':r[4]-110,'y':r[5]-14,'width':520,'height':r[3]+30})
    run(pg,"mxsSet('panst','auto');document.querySelector('#mixWin .mxs').scrollLeft=99999;1");pg.wait_for_timeout(900);shot(pg,'w_return.png','#mixWin .mx.kret',pad=120)
    print('return badge',run(pg,"document.querySelector('#mixWin .mx.kret .w9rb').textContent"))
    run(pg,"stop();1");pg.wait_for_timeout(1500);run(pg,"document.querySelector('#mixWin .mxs').scrollLeft=0;1");pg.wait_for_timeout(300);r=box(pg,'#mixWin .mx:nth-child(6) .mxp');pg.screenshot(path=os.path.join(OUT,'w_pan_silent.png'),clip={'x':r[4]-110,'y':r[5]-14,'width':520,'height':r[3]+30})
    print('errors',errs);b.close()
    # dragging: grab offset and reorder changes, in the mixer and the device chain, at app zoom 100 and 125 %
    b,pg,errs=boot(p)
    names=lambda: run(pg,"S.tracks[2].fx.map(f=>FXDEF[f.type].name).join(', ')")
    for sc in [100,125]:
        run(pg,"UI.scale=%d;applyScale();1"%sc);pg.wait_for_timeout(500)
        if run(pg,"(()=>{const w=document.getElementById('mixWin');return !w||w.hidden?1:0})()"): pg.click('#mBtn');pg.wait_for_timeout(800)
        run(pg,"renderMixer();document.querySelector('#mixWin .mxs').scrollLeft=0;W9.changes=0;1");pg.wait_for_timeout(300)
        c=box(pg,'#mixWin .mx:nth-child(3) .slot[data-fid]:nth-child(3)');nb=box(pg,'#mixWin .mx:nth-child(3) .slot[data-fid]:nth-child(4)');gx,gy=c[2]*.85,c[3]*.3;x0,y0=c[4]+gx,c[5]+gy
        pg.mouse.move(x0,y0);pg.mouse.down();offs=[]
        for i in range(1,int(nb[3]*1.6)):
            pg.mouse.move(x0,y0+i);pg.wait_for_timeout(6);g=gh(pg)
            if g: offs.append((round(x0-g[0],2),round(y0+i-g[1],2)))
        for i in range(24): pg.mouse.move(x0,y0+int(nb[3]*1.6)-1+(i%2)*2);pg.wait_for_timeout(5)
        print('zoom %d%% mixer slot: grab offset %s, box seen %s (min, max over %d moves), reorder changes moving slowly across a neighbour: %d'%(sc,(round(gx,2),round(gy,2)),(min(offs),max(offs)),len(offs),run(pg,"W9.changes")))
        pg.mouse.up();pg.wait_for_timeout(300);print('  order',names());run(pg,"undo();1");pg.wait_for_timeout(200)
        run(pg,"(()=>{const w=document.getElementById('mixWin');if(w&&!w.hidden)document.getElementById('mBtn').click();selectTrack(S.tracks[2].id);return 1})()");pg.wait_for_timeout(600)
        run(pg,"(()=>{const f=document.getElementById('fxin'),d=f.querySelectorAll(':scope>.dev[data-d=fx]')[1];f.scrollLeft+=(d.getBoundingClientRect().left-f.getBoundingClientRect().left)/ZOOM-30;W9.changes=0;return 1})()");pg.wait_for_timeout(300)
        D=json.loads(run(pg,"JSON.stringify([...document.querySelectorAll('#fxin>.dev[data-d=fx]')].map(d=>{const h=d.querySelector('.devh.dsl').getBoundingClientRect(),r=d.getBoundingClientRect();return [h.left+h.width/2,h.top+h.height*.45,r.left,r.top,r.width]}))"))
        a,n=D[1],D[2];dist=int((n[2]+n[4]/2)-(a[2]+a[4])+14);pg.mouse.move(a[0],a[1]);pg.mouse.down();offs=[]
        for i in range(1,dist,2):
            pg.mouse.move(a[0]+i,a[1]);pg.wait_for_timeout(5);g=gh(pg)
            if g: offs.append((round(a[0]+i-g[0],2),round(a[1]-g[1],2)))
        if sc==100: pg.screenshot(path=os.path.join(OUT,'w_drag_devices.png'),clip={'x':0,'y':560,'width':1920,'height':330})
        print('zoom %d%% device: grab offset %s, box seen %s, reorder changes: %d'%(sc,(round(a[0]-a[2],2),round(a[1]-a[3],2)),(min(offs),max(offs)),run(pg,"W9.changes")))
        pg.mouse.up();pg.wait_for_timeout(400);print('  order',names());run(pg,"undo();1");pg.wait_for_timeout(300);print('  undo',names())
    run(pg,"UI.scale=100;applyScale();1");pg.wait_for_timeout(400)
    if run(pg,"(()=>{const w=document.getElementById('mixWin');return !w||w.hidden?1:0})()"): pg.click('#mBtn');pg.wait_for_timeout(800)
    run(pg,"renderMixer();document.querySelector('#mixWin .mxs').scrollLeft=0;1");pg.wait_for_timeout(400)
    c=box(pg,'#mixWin .mx:nth-child(3) .slot[data-fid]:nth-child(3)');d=box(pg,'#mixWin .mx:nth-child(5) .slot[data-fid]:nth-child(2)')
    pg.mouse.move(c[0],c[1]);pg.mouse.down()
    for i in range(1,41): pg.mouse.move(c[0]+(d[0]-c[0])*i/40,c[1]+(d[1]-2-c[1])*i/40);pg.wait_for_timeout(10)
    pg.wait_for_timeout(250);pg.screenshot(path=os.path.join(OUT,'w_drag_mixer.png'),clip={'x':0,'y':460,'width':800,'height':200});pg.mouse.up();pg.wait_for_timeout(300)
    print('across channels: Clap',run(pg,"S.tracks[4].fx.map(f=>FXDEF[f.type].name).join(', ')"),'| Bass',names())
    print('errors',errs);b.close()
