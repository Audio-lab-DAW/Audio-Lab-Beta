# mixer strip rework (task S1, v0.194): python3 tools/ui-tests/mixstrip.py index.html
# pan styles and the live balance marker, width field with test signals, master pin, compact height, double-click and double right-click
import sys,json
from playwright.sync_api import sync_playwright
F=sys.argv[1] if len(sys.argv)>1 else 'index.html'
def boot(p,w=1920,h=1080):
    src=open(F,encoding='utf-8').read();b=p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required']);pg=b.new_page(viewport={'width':w,'height':h});errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e)[:400]))
    pg.route('https://app.test/**',lambda r:r.fulfill(status=200,content_type='text/html',body=src.encode()) if r.request.url.endswith('.html') else r.fulfill(status=404,body=b''))
    pg.add_init_script("if(!localStorage.getItem('audiolab-ui'))localStorage.setItem('audiolab-ui',JSON.stringify({splash:false,lat3:1}))")
    pg.goto('https://app.test/index.html');pg.wait_for_timeout(9000);pg.evaluate("()=>{const c=document.getElementById('liteNote');if(c)c.remove()}");return b,pg,errs
def run(pg,c): return pg.evaluate("c=>window.AudioLab.run(c)",c)
def ctr(pg,sel): return json.loads(run(pg,"(()=>{const e=document.querySelector(%s);const r=e.getBoundingClientRect();return JSON.stringify([r.left+r.width/2,r.top+r.height/2])})()"%json.dumps(sel)))
SIG={'mono':"(c,L,R)=>{const o=c.createOscillator();o.connect(L);o.connect(R);o.start();return [o]}",
'phase':"(c,L,R)=>{const o=c.createOscillator();const g=c.createGain();g.gain.value=-1;o.connect(L);o.connect(g);g.connect(R);o.start();return [o]}",
'left':"(c,L,R)=>{const o=c.createOscillator();const p=c.createStereoPanner();p.pan.value=-.5;const sp=c.createChannelSplitter(2);o.connect(p);p.connect(sp);sp.connect(L,0);sp.connect(R,1);o.start();return [o]}"}
with sync_playwright() as p:
    b,pg,errs=boot(p);ids=json.loads(run(pg,"JSON.stringify(S.tracks.map(t=>t.id))"))
    print('defaults',run(pg,"JSON.stringify([mxsO().fd,mxsO().panst,mxsO().pin])"))
    run(pg,"(()=>{start();setTimeout(stop,300);return 1})()");pg.wait_for_timeout(800)
    for k,f in SIG.items():
        run(pg,"(()=>{const N=NODES.get(curT().id);window._ts=("+f+")(ctx,N.aL,N.aR);return 1})()");pg.wait_for_timeout(700)
        print('device strip',k,'balance',run(pg,"document.querySelector('#fxin .hb.pan')._bk"),'field max bin',run(pg,"S1H.indexOf(Math.max(...S1H))"),'of 40')
        run(pg,"(()=>{for(const s of window._ts){s.stop();s.disconnect()}return 1})()");pg.wait_for_timeout(400)
    pg.click('#mBtn');pg.wait_for_timeout(800);print('transport button on',run(pg,"document.getElementById('mBtn').classList.contains('on')"))
    run(pg,"(()=>{UI.follow=false;pos=256;start();return 1})()");pg.wait_for_timeout(1500)
    print('balance (Hat L10, Open hat R10)',run(pg,"[...document.querySelectorAll('#mixWin .mxp')].slice(6,8).map(p=>p._bk).join(' ')"))
    for st in ['slider','half','full']:
        run(pg,"(()=>{mxsSet('panst','%s');S.tracks[5].pan=0;paintAll(document.getElementById('mixWin'));document.querySelector('#mixWin .mxs').scrollLeft=0;return 1})()"%st);pg.wait_for_timeout(300)
        c=ctr(pg,'#mixWin .mx[data-id="%s"] .mxp [data-c]'%ids[5]);pg.mouse.move(c[0],c[1]);pg.mouse.down();pg.mouse.move(c[0]+(0 if st=='full' else 20),c[1]-(30 if st=='full' else 0),steps=6);pg.mouse.up();pg.wait_for_timeout(200)
        print(st,run(pg,"document.querySelector('#mixWin').dataset.pk"),'pan after drag',round(run(pg,"S.tracks[5].pan"),3))
    run(pg,"stop();mxsSet('panst','auto')")
    h0=run(pg,"document.getElementById('mixWin').offsetHeight");pg.click('#mxCmp');pg.wait_for_timeout(600);print('compact height',h0,'->',run(pg,"document.getElementById('mixWin').offsetHeight"),'pan kind',run(pg,"document.querySelector('#mixWin').dataset.pk"))
    run(pg,"document.querySelector('#mixWin .mxs').scrollLeft=99999");pg.wait_for_timeout(200)
    print('compact end: last channel right, master left',run(pg,"(()=>{const ms=document.querySelector('#mixWin .mxs'),a=[...ms.querySelectorAll('.mx:not(.master)')];return [Math.round(a[a.length-1].getBoundingClientRect().right),Math.round(ms.querySelector('.mx.master').getBoundingClientRect().left)]})()"))
    pg.click('#mxCmp');pg.wait_for_timeout(600);print('back',run(pg,"document.getElementById('mixWin').offsetHeight"))
    run(pg,"(()=>{const w=document.getElementById('mixWin');UI.mxCapW=450;mxAutoW();return w.offsetWidth})()");pg.wait_for_timeout(300);print('narrow: unpinned',run(pg,"document.getElementById('mixWin').classList.contains('mxunpin')"))
    run(pg,"(()=>{const w=document.getElementById('mixWin');UI.mxCapW=0;mxAutoW();return w.offsetWidth})()");pg.wait_for_timeout(300);print('wide: unpinned',run(pg,"document.getElementById('mixWin').classList.contains('mxunpin')"))
    run(pg,"devHide(true);document.querySelector('#mixWin .mxs').scrollLeft=0");c=ctr(pg,'#mixWin .mx[data-id="%s"] .mxn'%ids[5]);pg.mouse.dblclick(c[0],c[1]);pg.wait_for_timeout(400)
    print('double-click strip opens its devices',run(pg,"selT===%s&&!UI.fxHide"%json.dumps(ids[5])))
    run(pg,"devHide(true)");c=ctr(pg,'#hdrin .hdr[data-id="%s"] .nm'%ids[2]);pg.mouse.dblclick(c[0],c[1]);pg.wait_for_timeout(400)
    print('double-click header opens its devices',run(pg,"selT===%s&&!UI.fxHide"%json.dumps(ids[2])))
    pg.click('#mBtn');pg.wait_for_timeout(300);c=ctr(pg,'#hdrin .hdr[data-id="%s"] .nm'%ids[3]);pg.mouse.click(c[0],c[1],button='right');pg.wait_for_timeout(100);pg.mouse.click(c[0],c[1],button='right');pg.wait_for_timeout(300)
    print('double right-click header opens the mixer on it',run(pg,"(()=>{const w=document.getElementById('mixWin');return !w.hidden&&ctxm.hidden&&selT===%s&&w.querySelector('.mx[data-id=\"%s\"]').classList.contains('mxflash')})()"%(json.dumps(ids[3]),ids[3])))
    print('errors',errs);b.close()
