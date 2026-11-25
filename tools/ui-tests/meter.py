"""Meter (v0.186): put the Meter on the master chain of the demo, play, and take a picture of every view and every preset,
in the panel and pinned; count redraws; check page errors.
    python3 tools/ui-tests/meter.py [index.html] [out dir]"""
import sys,os,json
from playwright.sync_api import sync_playwright
F=sys.argv[1] if len(sys.argv)>1 else 'index.html'
OUT=sys.argv[2] if len(sys.argv)>2 else '.'
def boot(p,w=1600,h=1000):
    src=open(F,encoding='utf-8').read()
    b=p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required']);pg=b.new_page(viewport={'width':w,'height':h});errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e)[:400]));pg.on('console',lambda m:errs.append('C:'+m.text[:300]) if m.type=='error' and 'net::' not in m.text and '404' not in m.text else None)
    pg.route('https://app.test/**',lambda r:r.fulfill(status=200,content_type='text/html',body=src.encode()) if r.request.url.endswith('.html') else r.fulfill(status=404,body=b''))
    pg.add_init_script("if(!localStorage.getItem('audiolab-ui'))localStorage.setItem('audiolab-ui',JSON.stringify({splash:false,lat3:1}))")
    pg.goto('https://app.test/index.html');pg.wait_for_timeout(9000)
    return b,pg,errs
def run(pg,code): return pg.evaluate("c=>window.AudioLab.run(c)",code)
def shot(pg,sel,name):
    pg.evaluate("s=>{const e=document.querySelector(s);if(e&&!e.closest('.pinw'))e.scrollIntoView({block:'nearest',inline:'nearest'})}",sel);pg.wait_for_timeout(120)
    r=pg.evaluate("s=>{const e=document.querySelector(s);if(!e)return null;const r=e.getBoundingClientRect();return [r.left,r.top,r.width,r.height]}",sel)
    if not r: print('no element',sel);return
    pg.screenshot(path=os.path.join(OUT,name+'.png'),clip={'x':max(0,r[0]-4),'y':max(0,r[1]-4),'width':min(1600,r[2]+8),'height':r[3]+8})
with sync_playwright() as p:
    b,pg,errs=boot(p)
    pg.evaluate("()=>{const c=document.getElementById('liteNote');if(c)c.remove()}")
    print('version',run(pg,"VERSION"),'errors after load',errs)
    LITE=os.environ.get('LITE')=='1';run(pg,"UI.lite=%s"%('true' if LITE else 'false'));print('light mode',LITE)
    run(pg,"(()=>{pushUndo();S.mfx.push(mkFx('measure'));selectTrack('__m');changed(true);renderFx()})()");pg.wait_for_timeout(800)
    fid=run(pg,"S.mfx.find(f=>f.type==='measure').id");dev='#fxin .dev[data-id="%s"]'%fid
    print('device',fid,run(pg,"JSON.stringify(S.mfx.find(f=>f.type==='measure').p)"))
    run(pg,"pos=48*4;start()");pg.wait_for_timeout(9000)
    print('readings',run(pg,"(()=>{const X=MFXM.get(%s);return JSON.stringify({I:X.I,S:X.S,M:X.M,tp:X.tp,LRA:X.LRA,psr:X.psr,crest:X.crest,corr:X.corr,n:X.n,LM:[LM.I,LM.tpMax]})})()"%json.dumps(fid)))
    views=['over','loud','lev','spec','low','sgram','st','wave','mini']
    for v in views:
        run(pg,"(()=>{const f=S.mfx.find(f=>f.type==='measure');f.p.view='%s';renderFx()})()"%v);pg.wait_for_timeout(1600)
        shot(pg,dev,'view_'+v)
    for k in ['club','psy','stream','mix','low','stereo','levels','mini']:
        run(pg,"(()=>{const f=S.mfx.find(f=>f.type==='measure');Object.assign(f.p,FXPRE.measure['%s'][1]);f.p.pre='%s';renderFx()})()"%(k,k));pg.wait_for_timeout(1400)
        shot(pg,dev,'preset_'+k)
    # pinned
    run(pg,"(()=>{const f=S.mfx.find(f=>f.type==='measure');Object.assign(f.p,FXPRE.measure.club[1]);renderFx()})()");pg.wait_for_timeout(500)
    pg.evaluate("s=>document.querySelector(s+' .pinbtn').click()",dev);pg.wait_for_timeout(1200)
    run(pg,"(()=>{const t=S.tracks.find(t=>t.name==='Bass');selectTrack(t.id);renderFx()})()");pg.wait_for_timeout(1500)
    pg.screenshot(path=os.path.join(OUT,'pinned_overview_screen.png'))
    def wsel(v):  # change Show in the pinned window like a user does
        pg.evaluate("v=>{const s=document.querySelector('.pinw select[data-x=view]');s.value=v;s.dispatchEvent(new Event('change',{bubbles:true}))}",v);pg.wait_for_timeout(1500)
    for v in ['over','mini','loud','st']:
        wsel(v);shot(pg,'.pinw','pinned_'+v)
    print('view after choosing in the window:',run(pg,"S.mfx.find(f=>f.type==='measure').p.view"))
    wsel('mini');c=pg.evaluate("()=>{const r=document.querySelector('.pinw .duar').getBoundingClientRect();return [r.left+r.width/2,r.top+r.height/2]}");pg.mouse.click(c[0],c[1]);pg.wait_for_timeout(1500)
    shot(pg,'.pinw','pinned_mini_shut');print('pinned Minimal, parameters shut: window',pg.evaluate("()=>{const r=document.querySelector('.pinw').getBoundingClientRect();return [Math.round(r.width),Math.round(r.height)]}"))
    pg.mouse.click(c[0],c[1]);pg.wait_for_timeout(600)
    # redraws per second and time per picture, pinned and in the panel, playing and stopped
    run(pg,"(()=>{const d=VIZX.measure;window.__md={n:0,t:0};VIZX.measure=function(){const t0=performance.now();d.apply(this,arguments);__md.t+=performance.now()-t0;__md.n++}})()")
    def rate(label,ms=3000):
        a=json.loads(run(pg,"JSON.stringify(__md)"));pg.wait_for_timeout(ms);bb=json.loads(run(pg,"JSON.stringify(__md)"));n=bb['n']-a['n'];print('%-34s %5.1f pictures/s, %.2f ms each'%(label,n/(ms/1000),(bb['t']-a['t'])/max(1,n)))
    for v in ['over','mini']:
        run(pg,"(()=>{const f=S.mfx.find(f=>f.type==='measure');f.p.view='%s';renderFx()})()"%v);pg.wait_for_timeout(800)
        rate('pinned, playing, '+v)
    run(pg,"stop()");pg.wait_for_timeout(600);rate('pinned, stopped (mouse just moved)');pg.wait_for_timeout(7000);rate('pinned, stopped and calm');print(run(pg,"JSON.stringify([play.on,LIVE.size,Math.round(performance.now()-LINT),ctx.currentTime-LHIT])"))
    pg.evaluate("()=>{const b=document.querySelector('.pinw .pinh .pinp, .pinw .pinh button');if(b)b.click()}");pg.wait_for_timeout(400)
    run(pg,"(()=>{for(const p of [...PIN.list])pinOff(pinKey(p.tid,p.fid));renderFx()})()")
    pg.wait_for_timeout(400);run(pg,"(()=>{selectTrack('__m');const f=S.mfx.find(f=>f.type==='measure');f.p.view='over';renderFx()})()");pg.wait_for_timeout(600)
    print('pins left',run(pg,"PIN.list.length"))
    run(pg,"pos=48*4;start()");pg.wait_for_timeout(1500);rate('in the panel, playing, over')
    run(pg,"(()=>{const t=S.tracks.find(t=>t.name==='Bass');selectTrack(t.id);renderFx()})()");pg.wait_for_timeout(600);rate('panel shows another track, playing')
    run(pg,"(()=>{selectTrack('__m');renderFx()})()");run(pg,"stop()");pg.wait_for_timeout(600);rate('in the panel, stopped');pg.wait_for_timeout(7000);rate('in the panel, stopped and calm')
    print('errors',errs)
    b.close()
