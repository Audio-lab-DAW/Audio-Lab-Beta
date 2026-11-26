# task AB (v0.203): mixer sidechain window and cable menus.
#   python3 tools/ui-tests/taskAB.py index.html [outdir]
# 1. drag a cable Kick -> Pad: direction text and arrow while dragging, menu with icons, choosing the sidechain adds a Ducker and opens the window
# 2. render (beats 96 to 128, Pad with Kick muted as trigger): ducking measured per beat, and the window settings change it
# 3. linked faders light up while playing, live gain reduction in the window follows the amount
# 4. right-click menu on a cable, window moved and remembered, menu to a return channel
# 5. fader drag follows the pointer every frame, Shift fine without a jump
# 6. bottom edge: the tab changes the cable area, the rest of the edge and the corner resize the window
import sys,os,json,math
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','remake'))
import numpy as np
from playwright.sync_api import sync_playwright
f=sys.argv[1] if len(sys.argv)>1 else 'index.html';out=sys.argv[2] if len(sys.argv)>2 else '.'
def boot(p,w=2560,h=1100):
    src=open(f,encoding='utf-8').read()
    b=p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required']);pg=b.new_page(viewport={'width':w,'height':h});errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e)[:400]));pg.on('console',lambda m:errs.append('C:'+m.text[:300]) if m.type=='error' and 'net::' not in m.text and '404' not in m.text and 'fetching the script' not in m.text else None)
    pg.route('https://app.test/**',lambda r:r.fulfill(status=200,content_type='text/html',body=src.encode()) if r.request.url.endswith('.html') else r.fulfill(status=404,body=b''))
    pg.add_init_script("if(!localStorage.getItem('audiolab-ui'))localStorage.setItem('audiolab-ui',JSON.stringify({splash:false,lat3:1}))")
    pg.goto('https://app.test/index.html');pg.wait_for_timeout(9000)
    return b,pg,errs,(lambda c:pg.evaluate("c=>window.AudioLab.run(c)",c))
def render(pg,R,ids,b0=96,b1=128):
    o={'b0':b0,'b1':b1,'sr':44100,'tail':0,'lim':False,'fast':False,'single':False,'tracks':[ids['Pad']]}
    h=pg.evaluate("o=>AudioLab.render(o)",o);x=np.zeros((h['ch'],h['len']),dtype=np.float32)
    import base64
    for ch in range(h['ch']):
        for off in range(0,h['len'],1<<20):
            n=min(1<<20,h['len']-off);x[ch,off:off+n]=np.frombuffer(base64.b64decode(pg.evaluate("a=>AudioLab.pull(a[0],a[1],a[2],a[3])",[h['id'],ch,off,n])),dtype=np.float32)
    pg.evaluate("i=>AudioLab.free(i)",h['id']);return x
def env(x,sr=44100,w=.005):
    m=(x[0]**2+x[1]**2)/2;n=int(sr*w);k=len(m)//n;return 10*np.log10(m[:k*n].reshape(k,n).mean(1)+1e-12)
def duckstats(e0,e1,bpm):
    d=e1-e0;spb=60/bpm;fr=.005;mx=[];late=[]
    for b in range(1,31):
        i=int(b*spb/fr);L=int(spb/fr);seg=d[i:i+L];ok=e0[i:i+L]>-70
        if ok.sum()<10:continue
        mx.append(seg[ok].min());j=int(.75*L)
        if ok[j]:late.append(seg[j])
    return np.median(mx),np.median(late)
with sync_playwright() as p:
    b,pg,errs,R=boot(p);print('load errors',errs,'version',R("VERSION"))
    shot=lambda n,c=None:pg.screenshot(path=os.path.join(out,n+'.png'),clip=c)
    R("(()=>{const c=document.getElementById('liteNote');if(c)c.remove();openMixer()})()");pg.wait_for_timeout(1200)
    R("(()=>{const w=document.getElementById('mixWin');w.style.left='10px';w.style.width='2500px';mxFit();renderMixer()})()");pg.wait_for_timeout(800);R("document.querySelector('#mixWin .mxs').scrollLeft=0");pg.wait_for_timeout(300)
    ids=dict(json.loads(R("JSON.stringify(S.tracks.map(t=>[t.name,t.id]))")));kick,pad=ids['Kick'],ids['Pad'];bpm=R("S.bpm")
    # 1. drag
    sk=pg.locator(f'#mixWin svg.cabs .cabsk[data-sk="{kick}"]').bounding_box();pr=json.loads(R(f"JSON.stringify(document.querySelector('#mixWin .mx[data-id=\"{pad}\"]').getBoundingClientRect())"))
    pg.mouse.move(sk['x']+6,sk['y']+6);pg.mouse.down();pg.mouse.move(pr['x']+pr['width']/2,pr['y']+pr['height']-60,steps=15);pg.wait_for_timeout(200)
    print('while dragging:',repr(R("(document.getElementById('abxD')||{}).innerText")),'arrow:',R("!!document.querySelector('#mixWin svg.cabs .abxtar')"))
    shot('ab_drag',{'x':1700,'y':0,'width':860,'height':700})
    pg.mouse.up();pg.wait_for_timeout(400);print('menu:',repr(R("(document.getElementById('abxM')||{}).innerText")[:300]),'icons',R("document.querySelectorAll('#abxM .abxo svg').length"))
    shot('ab_menu',{'x':1700,'y':0,'width':860,'height':800})
    pg.locator('#abxM .abxo.main').first.click();pg.wait_for_timeout(900)
    print('Pad effects:',R(f"JSON.stringify(trkById('{pad}').fx.map(f=>[f.type,f.p.src||'']))"),'windows open:',R("ABXW.size"),'leader line:',R("!!document.querySelector('#abxLead .abxln')"))
    fid=R(f"trkById('{pad}').fx.find(f=>f.type==='duck').id")
    # 2. render: duck measured and settings change it
    R(f"(()=>{{const f=abxFind('{fid}').f;f.on=false;changed(true)}})()");e0=env(render(pg,R,ids))
    R(f"(()=>{{const f=abxFind('{fid}').f;f.on=true;changed(true)}})()");e1=env(render(pg,R,ids));a,l=duckstats(e0,e1,bpm);print('render, default (amount 75%%): deepest %.2f dB per beat, at 3/4 beat %.2f dB'%(a,l))
    for k,v in (('amt',40),('rl',60),('th',0)):
        R(f"(()=>{{const F=abxFind('{fid}');F.f.p.{k}={v};if({str(k=='rl').lower()})F.f.p.hd=0;abxSet(F.t,F.f)}})()");e2=env(render(pg,R,ids));a,l=duckstats(e0,e2,bpm);print('  %s=%s: deepest %.2f dB, at 3/4 beat %.2f dB'%(k,v,a,l))
    R(f"(()=>{{const F=abxFind('{fid}');Object.assign(F.f.p,{{amt:75,rl:180,hd:30,th:-30}});abxSet(F.t,F.f);abxBuild(ABXW.get('{fid}'))}})()")
    # 3. play: lights and live reduction
    R("(()=>{pmSetOn&&pmSetOn(false);pos=100;start()})()");pg.wait_for_timeout(3000)
    L=[R(f"JSON.stringify([...document.querySelectorAll('#mixWin .mx.abxl')].map(e=>[e.dataset.id==='{pad}'?'Pad':e.dataset.id==='{kick}'?'Kick':e.dataset.id,e.style.getPropertyValue('--abxp')]))") for _ in range(4) if not pg.wait_for_timeout(90)]
    print('lit faders while playing:',L)
    GR=f"(()=>{{const F=abxFind('{fid}');const X=abxX(F.t,F.f);let m=1;for(const g of X.H.g)m=Math.min(m,g);return -20*Math.log10(Math.max(1e-4,m))}})()"
    print('live deepest reduction %.2f dB'%R(GR));R(f"(()=>{{const F=abxFind('{fid}');F.f.p.amt=20;abxSet(F.t,F.f);paintAll(ABXW.get('{fid}').el)}})()");pg.wait_for_timeout(2500);print('after Duck amount 20%%: %.2f dB'%R(GR))
    shot('ab_window_playing',{'x':1700,'y':0,'width':860,'height':800});R("stop()");pg.wait_for_timeout(300)
    # 4. move the window, close, open: same place
    hb=pg.locator('.abxw .abxwh .abxch').first.bounding_box();o0=R(f"JSON.stringify(abxFind('{fid}').f.abw)")
    pg.mouse.move(hb['x']+5,hb['y']+5);pg.mouse.down();pg.mouse.move(hb['x']-195,hb['y']+65,steps=8);pg.mouse.up();pg.wait_for_timeout(300)
    o1=R(f"JSON.stringify(abxFind('{fid}').f.abw)");r1=R("JSON.stringify(document.querySelector('.abxw').getBoundingClientRect())");R(f"abxClose('{fid}')");R(f"abxOpen('{fid}')");pg.wait_for_timeout(200);r2=R("JSON.stringify(document.querySelector('.abxw').getBoundingClientRect())")
    print('window offset',o0,'->',o1,'same place after reopening:',json.loads(r1)['x']==json.loads(r2)['x'] and json.loads(r1)['y']==json.loads(r2)['y'])
    shot('ab_window_moved',{'x':1500,'y':0,'width':1060,'height':800})
    i=R("CAB.list.findIndex(c=>c.fx&&c.fx.type==='duck')");R(f"abxCabMenu(CAB.list[{i}],1200,400)");pg.wait_for_timeout(200);print('right-click menu:',repr(R("document.getElementById('abxM').innerText")[:260]));shot('ab_cable_menu',{'x':1000,'y':250,'width':700,'height':600});R("abxMClose()")
    R(f"abxConnect(trkById('{kick}'),S.tracks.find(t=>t.kind==='return'),1200,400)");pg.wait_for_timeout(200);print('menu to a return:',repr(R("document.getElementById('abxM').innerText")[:260]));shot('ab_return_menu',{'x':1000,'y':250,'width':700,'height':700});R("abxMClose()")
    b.close()
    # 5, 6 at a normal size
    b,pg,errs2,R=boot(p,1600,1000);R("(()=>{const c=document.getElementById('liteNote');if(c)c.remove();openMixer()})()");pg.wait_for_timeout(1500)
    info=lambda:json.loads(R("JSON.stringify((()=>{const w=document.getElementById('mixWin'),mx=w.querySelector('.mxs .mx');return{win:[w.offsetLeft,w.offsetTop,w.offsetWidth,w.offsetHeight],tot:cs2T(),strip:mx.offsetHeight}})())"))
    el=pg.locator('#mixWin .mx[data-id] .fv').nth(1).bounding_box();x=el['x']+el['width']/2;y0=el['y']+el['height']*.3;pg.mouse.move(x,y0);pg.mouse.down();rows=[]
    RV="()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(()=>r(AudioLab.run('S.tracks[1].vol')))))"
    for i in range(1,21):pg.mouse.move(x,y0+i*4);rows.append(round(20*math.log10(max(1e-6,pg.evaluate(RV))),2))
    pg.keyboard.down('Shift')
    for i in range(1,5):pg.mouse.move(x,y0+80-i*10);rows.append(('shift',round(20*math.log10(max(1e-6,pg.evaluate(RV))),2)))
    pg.keyboard.up('Shift');pg.mouse.up();print('fader dB after each 4 px move (one frame each), then Shift with 10 px moves back up:',rows)
    R("(()=>{const w=document.getElementById('mixWin');w.style.top='60px';w.style.height='560px';mxFit()})()");pg.wait_for_timeout(600)
    a=info();tb=pg.locator('#mixWin>.abxtab').bounding_box();cx,cy=tb['x']+tb['width']/2,tb['y']+tb['height']/2;pg.mouse.move(cx,cy);pg.mouse.down();pg.mouse.move(cx,cy+100,steps=10);pg.mouse.up();pg.wait_for_timeout(600);c=info()
    print('tab down 100: window',a['win'][3],'->',c['win'][3],'cable area',a['tot'],'->',c['tot'],'channels',a['strip'],'->',c['strip'])
    shot('ab_tab',{'x':0,'y':0,'width':1300,'height':760})
    a=c;bb=pg.locator('#mixWin>.rz-s').bounding_box()
    for xx in (bb['x']+60,bb['x']+bb['width']-60):
        a=info();yy=bb['y']+bb['height']/2;pg.mouse.move(xx,yy);pg.mouse.down();pg.mouse.move(xx,yy-60,steps=8);pg.mouse.up();pg.wait_for_timeout(600);c=info();bb=pg.locator('#mixWin>.rz-s').bounding_box()
        print('bottom edge away from the tab, up 60: window',a['win'][3],'->',c['win'][3],'cable area',a['tot'],'->',c['tot'])
    a=info();bx=pg.locator('#mixWin>.rz-se').bounding_box();x,y=bx['x']+bx['width']/2,bx['y']+bx['height']/2;pg.mouse.move(x,y);pg.mouse.down();pg.mouse.move(x-40,y+50,steps=8);pg.mouse.up();pg.wait_for_timeout(600);c=info()
    print('corner: window',a['win'],'->',c['win'],'cable area',a['tot'],'->',c['tot'])
    print('errors',errs,errs2);b.close()
