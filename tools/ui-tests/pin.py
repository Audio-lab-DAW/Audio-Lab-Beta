"""Pinned devices (v0.185): pin an instrument, an effect and an analyser from two tracks, select a third, check the pictures run, turn a knob,
move a window, remove and undo, reload, unpin from the window and from the panel, and count the redraws.
    python3 tools/ui-tests/pin.py [index.html] [out dir]"""
import sys,os,json
import sys as _ws_sys, os as _ws_os; _ws_sys.path.insert(0, _ws_os.path.join(_ws_os.path.dirname(_ws_os.path.abspath(__file__)), '../test-songs')); from alsong import alsong  # task WS-F: the test songs
from playwright.sync_api import sync_playwright
def boot(p,f=(sys.argv[1] if len(sys.argv)>1 else "index.html"),scale=1,w=1600,h=1000,ui='{splash:false,lat3:1}'):
    src=open(f,encoding='utf-8').read()
    b=p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required']);pg=b.new_page(viewport={'width':w,'height':h},device_scale_factor=scale);errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e)[:400]));pg.on('console',lambda m:errs.append('C:'+m.text[:300]) if m.type=='error' and 'net::' not in m.text and '404' not in m.text else None)
    pg.route('https://app.test/**',alsong(lambda r:r.fulfill(status=200,content_type='text/html',body=src.encode()) if r.request.url.endswith('.html') else r.fulfill(status=404,body=b'')))
    pg.add_init_script("if(!localStorage.getItem('audiolab-ui'))localStorage.setItem('audiolab-ui',JSON.stringify(%s))"%ui)
    pg.goto('https://app.test/index.html');pg.wait_for_timeout(9000)
    return b,pg,errs
def run(pg,code): return pg.evaluate("c=>window.AudioLab.run(c)",code)
F=sys.argv[1] if len(sys.argv)>1 else 'index.html'
OUT=sys.argv[2] if len(sys.argv)>2 else '.'

def ctr(pg,sel):
    r=pg.evaluate("s=>{const e=document.querySelector(s);if(!e)return null;const r=e.getBoundingClientRect();return [r.left+r.width/2,r.top+r.height/2,r.left,r.top,r.width,r.height]}",sel);return r
def click(pg,sel):
    pg.evaluate("s=>{const e=document.querySelector(s);if(e&&!e.closest('.pinw'))e.scrollIntoView({block:'nearest',inline:'nearest'})}",sel);pg.wait_for_timeout(150)
    c=ctr(pg,sel);assert c,sel;pg.mouse.click(c[0],c[1]);pg.wait_for_timeout(450)
def sel(pg,name): run(pg,"(()=>{const t=S.tracks.find(t=>t.name==='%s');selectTrack(t.id);renderFx()})()"%name);pg.wait_for_timeout(400)
def cvh(pg,s): return pg.evaluate("s=>{const c=document.querySelector(s);if(!c)return 'none';const d=c.getContext('2d').getImageData(0,0,c.width,c.height).data;let h=0;for(let i=0;i<d.length;i+=97)h=(h*31+d[i])|0;return h}",s)
def st(pg): return run(pg,"JSON.stringify({pins:PIN.list.map(p=>[pinTrk(p.tid).name,p.fid,p.x,p.y]),wins:[...PIN.wins.values()].map(w=>[w.dataset.pk,!!(w._dev&&w._dev.isConnected),w.querySelector('.pinn').textContent]),ph:[...fxin.querySelectorAll('.pinph')].length,sel:curT().name})")
with sync_playwright() as p:
    b,pg,errs=boot(p,F)
    pg.evaluate("()=>{const c=document.getElementById('liteNote');if(c)c.remove()}")
    run(pg,"(()=>{const t=S.tracks.find(t=>t.name==='Kick');pushUndo();t.fx.push(mkFx('spec'));const o=mkTrack('inst','orb','Orbit');S.tracks.push(o);changed(true);pos=36*4;})()");pg.wait_for_timeout(600)
    sel(pg,'Orbit');click(pg,'#fxin .dev[data-d=inst] .pinbtn');print('1',st(pg))
    pg.screenshot(path=os.path.join(OUT,'a_panel_pinned.png'))
    sel(pg,'Kick');click(pg,'#fxin .dev.eq2 .pinbtn');print('2',st(pg))
    sid=run(pg,"curT().fx.find(f=>f.type==='spec').id")
    click(pg,'#fxin .dev[data-id="%s"] .pinbtn'%sid);print('3',st(pg))
    sel(pg,'Bass');print('4 third track',st(pg))
    def drag(sel,x,y):
        pk=pg.evaluate("s=>document.querySelector(s).dataset.pk",sel);run(pg,"pinFront(%s)"%json.dumps(pk))
        h=ctr(pg,sel+' .pinh .pinn');pg.mouse.move(h[0],h[1]);pg.mouse.down();w=ctr(pg,sel);pg.mouse.move(h[0]+(x-w[2]),h[1]+(y-w[3]),steps=6);pg.mouse.up();pg.wait_for_timeout(150)
    run(pg,"(()=>{const P=PIN.list;const L=[[20,330],[300,40],[1000,60]];P.forEach((p,i)=>{p.x=L[i][0];p.y=L[i][1];pinClamp(PIN.wins.get(pinKey(p.tid,p.fid)))})})()")
    print('4a placed',st(pg))
    drag('.pinw[data-pk$="/inst"]',40,300)
    eid0=run(pg,"PIN.list.find(p=>p.fid!=='inst'&&pinObj(p).o.type==='eq').fid");drag('.pinw[data-pk$="%s"]'%eid0,300,40)
    print('4b arranged',st(pg))
    # pictures update while playing
    run(pg,"start()");pg.wait_for_timeout(1500)
    sc='.pinw[data-pk$="%s"] canvas.viz'%sid; ic='.pinw[data-pk$="/inst"] canvas.ivz'
    h1=(cvh(pg,sc),cvh(pg,ic));pg.wait_for_timeout(700);h2=(cvh(pg,sc),cvh(pg,ic));print('5 pictures change while playing (spec, inst):',h1[0]!=h2[0],h1[1]!=h2[1],h1,h2)
    # redraw counts
    def rate(ms):
        a=run(pg,"JSON.stringify([PIN.stat.draws,PIN.stat.frames,FRN,PIN.stat.cv])");pg.wait_for_timeout(ms);bb=run(pg,"JSON.stringify([PIN.stat.draws,PIN.stat.frames,FRN,PIN.stat.cv])");a=json.loads(a);bb=json.loads(bb);s=ms/1000;return 'window draws/s %.1f, pin passes/s %.1f, app frames/s %.1f, canvases/s %.1f'%((bb[0]-a[0])/s,(bb[1]-a[1])/s,(bb[2]-a[2])/s,(bb[3]-a[3])/s)
    print('6 playing:',rate(3000))
    pg.screenshot(path=os.path.join(OUT,'b_three_windows.png'))
    run(pg,"stop()");pg.wait_for_timeout(500);print('6 stopped, mouse moving:',rate(2000));pg.wait_for_timeout(6500);print('6 stopped, calm:',rate(3000),run(pg,"JSON.stringify([play.on,LIVE.size,Math.round(performance.now()-LINT),ctx.currentTime-LHIT])"))
    # knob in pinned window (Lead instrument)
    h=ctr(pg,'.pinw[data-pk$="/inst"] .pinh .pinn');pg.mouse.click(h[0],h[1])
    kn='.pinw[data-pk$="/inst"] .kn[data-c]'
    cid=pg.evaluate("s=>document.querySelector(s).dataset.c",kn);v0=run(pg,"CT.get(%s).get()"%json.dumps(cid))
    c=ctr(pg,kn);pg.mouse.move(c[0],c[1]);pg.mouse.down();pg.mouse.move(c[0],c[1]-40,steps=6);pg.mouse.up();pg.wait_for_timeout(300)
    v1=run(pg,"CT.get(%s).get()"%json.dumps(cid));print('7 knob',cid,v0,'->',v1, 'undo steps',run(pg,"UNDO.length"))
    # the other way round: set the same parameter from outside, the window knob follows
    lab=pg.evaluate("s=>document.querySelector(s).querySelector('output').textContent",kn)
    run(pg,"(()=>{const C=CT.get(%s);C.set(C.spec.v(.15))})()"%json.dumps(cid));pg.wait_for_timeout(400)
    lab2=pg.evaluate("s=>document.querySelector(s).querySelector('output').textContent",kn);print('7b outside change shows in window:',lab,'->',lab2)
    # drag window by handle, and off screen
    h=ctr(pg,'.pinw[data-pk$="/inst"] .pinh .pinn');w0=ctr(pg,'.pinw[data-pk$="/inst"]')
    pg.mouse.move(h[0],h[1]);pg.mouse.down();pg.mouse.move(h[0]+300,h[1]+120,steps=8);pg.mouse.up();pg.wait_for_timeout(200);w1=ctr(pg,'.pinw[data-pk$="/inst"]')
    print('8 moved by',round(w1[2]-w0[2]),round(w1[3]-w0[3]))
    h=ctr(pg,'.pinw[data-pk$="/inst"] .pinh .pinn');pg.mouse.move(h[0],h[1]);pg.mouse.down();pg.mouse.move(h[0]+3000,h[1]+3000,steps=8);pg.mouse.up();pg.wait_for_timeout(200);w2=ctr(pg,'.pinw[data-pk$="/inst"]')
    print('8b off screen clamp: right',round(w2[2]+w2[4]),'bottom',round(w2[3]+w2[5]),'viewport 1600x1000')
    h=ctr(pg,'.pinw[data-pk$="/inst"] .pinh .pinn');pg.mouse.move(h[0],h[1]);pg.mouse.down();pg.mouse.move(h[0]-2000,h[1]-2000,steps=8);pg.mouse.up();pg.wait_for_timeout(200);w2=ctr(pg,'.pinw[data-pk$="/inst"]');print('8c top-left clamp',round(w2[2]),round(w2[3]))
    pg.mouse.move(h[0]-900,h[1]-500);pg.mouse.down();pg.mouse.up()
    h=ctr(pg,'.pinw[data-pk$="/inst"] .pinh .pinn');pg.mouse.move(h[0],h[1]);pg.mouse.down();pg.mouse.move(h[0]+500,h[1]+200,steps=5);pg.mouse.up();pg.wait_for_timeout(200)
    # remove pinned EQ with its X, then undo
    eid=run(pg,"PIN.list.find(p=>p.fid!=='inst'&&pinObj(p).o.type==='eq').fid")
    h=ctr(pg,'.pinw[data-pk$="%s"] .pinh .pinn'%eid);pg.mouse.click(h[0],h[1]);click(pg,'.pinw[data-pk$="%s"] .devh>.x'%eid);print('9 removed EQ',st(pg))
    run(pg,"undo()");pg.wait_for_timeout(500);print('9b undo',st(pg))
    run(pg,"redo()");pg.wait_for_timeout(500);print('9c redo',st(pg))
    run(pg,"undo()");pg.wait_for_timeout(500);print('9d undo',st(pg))
    pg.wait_for_timeout(800)
    pg.reload();pg.wait_for_timeout(9000);pg.evaluate("()=>{const c=document.getElementById('liteNote');if(c)c.remove()}")
    print('10 after reload',st(pg))
    pg.screenshot(path=os.path.join(OUT,'c_reload.png'))
    # close up
    run(pg,"pinFront([...PIN.wins.keys()].find(k=>k.endsWith('%s')))"%sid);c=ctr(pg,'.pinw[data-pk$="%s"]'%sid);run(pg,"pos=36*4;start()");pg.wait_for_timeout(2500)
    x0=max(0,c[2]-10);pg.screenshot(path=os.path.join(OUT,'d_closeup.png'),clip={'x':x0,'y':max(0,c[3]-40),'width':min(1600-x0,c[4]+20),'height':c[5]+50});run(pg,"stop()")
    # unpin from window
    run(pg,"pinFront([...PIN.wins.keys()].find(k=>k.endsWith('/inst')))");click(pg,'.pinw[data-pk$="/inst"] .pinun');print('11 unpin from window',st(pg))
    sel(pg,'Orbit');print('11b orbit panel has instrument back:',run(pg,"!!fxin.querySelector(':scope>.dev[data-d=inst]')"),'knob value in panel', run(pg,"(()=>{const e=fxin.querySelector('.dev[data-d=inst] .kn[data-c=\"%s\"] output');return e&&e.textContent})()"%cid.split(':',2)[2] if cid.startswith('pn:') else ''))
    # unpin from panel placeholder
    sel(pg,'Kick');click(pg,'#fxin .pinph .devh .pinbtn');print('12 unpin from panel',st(pg))
    click(pg,'#fxin .pinph .pinphb');print('12b front',run(pg,"document.querySelector('.pinw[data-pk$=\"%s\"]').style.zIndex+' '+FWZ"%sid))
    print('errors',errs);b.close()
