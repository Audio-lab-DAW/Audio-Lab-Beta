# Visualizer docks and sharpness, the map / visualizer right-click menu, the glass preview loops, the overview zoom (v0.194, task U).
#   python3 tools/ui-tests/taskU.py [index.html] [outdir] [part ...]   parts: viz menu glass zoom (default: all)
import sys,os,json,time
from playwright.sync_api import sync_playwright
idx=sys.argv[1] if len(sys.argv)>1 else 'index.html';out=sys.argv[2] if len(sys.argv)>2 else '/tmp/taskU';os.makedirs(out,exist_ok=True)
parts=set(sys.argv[3:]);want=lambda k:not parts or k in parts
src=open(idx,encoding='utf-8').read().encode()
def boot(p,scale=1):
    b=p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required']);pg=b.new_page(viewport={'width':1600,'height':1000},device_scale_factor=scale);errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e)[:300]))
    pg.route('https://app.test/**',lambda r:r.fulfill(status=200,content_type='text/html',body=src) if r.request.url.endswith('.html') else r.fulfill(status=404,body=b''))
    pg.add_init_script("localStorage.setItem('audiolab-ui',JSON.stringify({splash:false,lat3:1}))")
    pg.goto('https://app.test/index.html');pg.wait_for_function("()=>window.AudioLab&&window.AudioLab.version",timeout=60000);pg.wait_for_timeout(4500)
    R=lambda c:pg.evaluate("c=>AudioLab.run(c)",c)
    R("(()=>{pmSetOn(false);const c=document.getElementById('liteNote');if(c)c.remove();document.querySelectorAll('.toast').forEach(t=>t.remove())})()");pg.wait_for_timeout(600)
    return b,pg,errs,R
with sync_playwright() as p:
    if want('viz'):
        for sc in (1,2):
            b,pg,errs,R=boot(p,sc);print('dpr',sc,'errors on load',errs)
            R("(()=>{pos=64;start()})()")
            for dock in ('top','bottom'):
                R("(()=>{UI.viz=true;UI.vizDock='%s';UI.vizMode='all';vizApply()})()"%dock);pg.wait_for_timeout(1800)
                r=R("(()=>{const e=VZ.el,r=e.getBoundingClientRect(),s=document.getElementById('stage').getBoundingClientRect();return JSON.stringify({parent:e.parentElement.id,cls:e.className,top:Math.round(r.top),bottom:Math.round(r.bottom),stageTop:Math.round(s.top),stageBottom:Math.round(s.bottom),cv:[VZ.cv.width,VZ.cv.height,VZ.cv.clientWidth],sg:VZ.sg&&[VZ.sg.width,VZ.sg.height]})})()")
                print(' ',dock,r);pg.screenshot(path=f'{out}/viz_{dock}_x{sc}.png')
            # cost of one visualizer frame (All modules), 60 frames
            for dp in ((1,2) if sc==2 else (1,)):
                ms=R("(()=>{const o=vzDp;vzDp=()=>%d;VZ.sg=null;let t=performance.now();for(let i=0;i<60;i++){VZ.last=0;vizFrame(performance.now()+1e6);cancelAnimationFrame(VZ.raf)}const m=(performance.now()-t)/60;vzDp=o;VZ.raf=requestAnimationFrame(vizFrame);return m.toFixed(2)})()"%dp)
                print('  one visualizer frame at %d device pixels per point: %s ms'%(dp,ms))
            R("stop()");b.close()
    if want('menu'):
        b,pg,errs,R=boot(p,1)
        R("(()=>{UI.viz=true;UI.vizDock='top';vizApply()})()");pg.wait_for_timeout(500)
        m=pg.locator('#mapw .cv').bounding_box();pg.mouse.click(m['x']+300,m['y']+20,button='right');pg.wait_for_timeout(200)
        print('map menu:',R("[...ctxm.querySelectorAll('.mlab,.mh')].map(e=>e.firstChild.textContent).join(' | ')"));pg.screenshot(path=f'{out}/menu_map.png')
        pg.locator('#ctxm button',has_text='Visualizer').first.click();pg.wait_for_timeout(300);print('visualizer off from the map menu:',R("!UI.viz&&!VZ.el.isConnected"))
        pg.keyboard.press('Escape');R("closeMenu()")
        R("(()=>{UI.viz=true;UI.vizDock='bottom';vizApply()})()");pg.wait_for_timeout(500)
        v=pg.locator('#vizp canvas').bounding_box();pg.mouse.click(v['x']+200,v['y']+40,button='right');pg.wait_for_timeout(200);pg.screenshot(path=f'{out}/menu_viz.png')
        pg.locator('#ctxm button',has_text='Map').first.click();pg.wait_for_timeout(300);print('map off from the visualizer menu:',R("!!UI.mapOff&&document.getElementById('mapw').hidden"))
        pg.locator('#ctxm button',has_text='At the top').first.click();pg.wait_for_timeout(300);print('visualizer moved to the top:',R("UI.vizDock==='top'&&VZ.el.parentElement.id==='topOut'"))
        v=pg.locator('#vizp canvas').bounding_box();pg.mouse.click(v['x']+200,v['y']+40,button='right');pg.wait_for_timeout(200);pg.locator('#ctxm button',has_text='Map').first.click();pg.wait_for_timeout(300)
        print('map back on:',R("!UI.mapOff&&!document.getElementById('mapw').hidden"),'| settings boxes follow:',R("$('#layMap').checked&&$('#layViz').checked&&$('#layVizDock').value==='top'"))
        print('page errors',errs);b.close()
    if want('glass'):
        b,pg,errs,R=boot(p,2)
        R("openSettings('glass')");pg.wait_for_timeout(800)
        for k in ('now','3','2','1','0'):
            pg.locator(f'#gpvCh [data-gv="{k}"]').click();pg.wait_for_timeout(700)
            box=pg.locator('#gpv').bounding_box();pg.screenshot(path=f'{out}/glass_{k}.png',clip={'x':box['x']-4,'y':box['y']-4,'width':box['width']+8,'height':box['height']+50})
            print(' preview',k,R("(()=>{const V=[...GPVV.c.values()].pop();return V.desc+' | made in '+V.ms.toFixed(0)+' ms'})()"))
        # playback cost: time spent in gpDraw per second while the preview loops
        r=R("(async()=>{const o=gpDraw;let t=0,n=0;gpDraw=function(x){const a=performance.now();o(x);t+=performance.now()-a;n++};await new Promise(r=>setTimeout(r,2000));gpDraw=o;return JSON.stringify({msPerSecond:+(t/2).toFixed(1),calls:n})})()")
        print(' playback cost',r)
        print(' pictures in memory',R("GPVV.c.size"),'| page errors',errs);b.close()
    if want('zoom'):
        b,pg,errs,R=boot(p,1)
        R("(()=>{selectTrack(S.tracks[1].id);V.ppb=4;V.x=0;V.y=0;V.th=60;clampV();dirty=true})()");pg.wait_for_timeout(300)
        # zoom out until the overview opens
        pg.mouse.move(900,400);pg.keyboard.down('Control')
        for i in range(80):
            pg.mouse.wheel(0,100);pg.wait_for_timeout(120)
            if R("OVW.on"):break
        pg.keyboard.up('Control');pg.wait_for_timeout(600)
        print('beat 64 on screen: normal view %.1f px, overview %.1f px'%tuple(json.loads(R("JSON.stringify([(UI.tracksRight?0:HDRW)+(64-OVW.sv.x)*OVW.sv.ppb,(()=>{const G=ovwGeo();return G.X+(64-G.x)*G.ppb})()])"))))
        print('entered after',i+1,'notches; normal scale',R("+OVW.sv.ppb.toFixed(3)"),'overview scale',R("+ovwGeo().ppb.toFixed(3)"))
        pg.screenshot(path=f'{out}/zoom_overview.png')
        # pick a clip of the "Pads" breakdown (or any clip) and zoom in around it
        info=json.loads(R("""JSON.stringify((()=>{const G=ovwGeo();let best=null;for(let j=0;j<G.n;j++){const t=S.tracks[G.vis[j]];if(!t.clips.length||t.kind==='group')continue;for(const c of t.clips){const x=G.X+(c.start-G.x)*G.ppb,y=G.AY+j*G.rh-G.y;if(x>G.X+200&&x<G.w-300&&y>G.AY+40&&y<G.ah){best={id:c.id,t:t.name,c:c.name,x,y,w:c.len*G.ppb,h:G.rh};break}}if(best&&/pad|break/i.test(best.t+best.c))break}return best})())"""))
        print('chosen clip',info)
        mx=info['x']+min(30,info['w']/2);my=info['y']+info['h']/2;r=pg.locator('#arr').bounding_box();pg.mouse.move(r['x']+mx,r['y']+my)
        geo=lambda:json.loads(R("""JSON.stringify((()=>{const id='%s';if(OVW.on){const G=ovwGeo();for(let j=0;j<G.n;j++){const t=S.tracks[G.vis[j]];const c=t.clips.find(c=>c.id===id);if(c)return{mode:'overview',x:G.X+(c.start-G.x)*G.ppb,w:c.len*G.ppb,y:G.AY+j*G.rh-G.y,h:G.rh}}}
          layoutRows();for(let i=0;i<S.tracks.length;i++){const t=S.tracks[i],c=t.clips.find(c=>c.id===id);if(c){const g=clipGeom(i,c);return{mode:'normal',x:g.x,w:g.w,y:g.y,h:g.h}}}})())"""%info['id']))
        R("(()=>{const o=ovwLeave,id='%s';window.__lv=null;const cg=()=>{if(OVW.on){const G=ovwGeo();for(let j=0;j<G.n;j++){const t=S.tracks[G.vis[j]],c=t.clips.find(c=>c.id===id);if(c)return{x:G.X+(c.start-G.x)*G.ppb,w:c.len*G.ppb,y:G.AY+j*G.rh-G.y,h:G.rh-2}}}layoutRows();for(let i=0;i<S.tracks.length;i++){const c=S.tracks[i].clips.find(c=>c.id===id);if(c){const g=clipGeom(i,c);return{x:g.x,w:g.w,y:g.y,h:g.h}}}};ovwLeave=function(p,m){const a=cg(),G=ovwGeo();const r=o.apply(this,arguments);window.__lv={before:a,after:cg(),ppbO:G.ppb,ppbN:V.ppb,rh:G.rh,th:V.th,mode:m};ovwLeave=o;return r}})()"%info['id'])
        pg.keyboard.down('Control');before=None;after=None
        for i in range(120):
            g0=geo();pg.mouse.wheel(0,-30);pg.wait_for_timeout(90);g1=geo()
            if g0['mode']=='overview' and g1['mode']=='normal':before,after=g0,g1;break
        pg.keyboard.up('Control')
        lv=json.loads(R("JSON.stringify(window.__lv)"));print('at the moment of leaving',lv)
        if lv:B,A=lv['before'],lv['after'];print('clip on screen just before / just after leaving: x %.1f -> %.1f, width %.1f -> %.1f, top %.1f -> %.1f, height %.1f -> %.1f'%(B['x'],A['x'],B['w'],A['w'],B['y'],A['y'],B['h'],A['h']))
        pg.screenshot(path=f'{out}/zoom_back.png')
        print('page errors',errs);b.close()
