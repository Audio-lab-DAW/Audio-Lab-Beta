# v0.171: themes. Usage: python3 tools/ui-tests/themes.py index.html outdir
# Every theme in every effect level with the mixer open and music playing, the Settings cards, the level meter colours,
# what a theme sets (fader design, meter colours), slider take-over, saving across reload. Prints the results and any page errors.
import sys,json,os
from playwright.sync_api import sync_playwright
src=open(sys.argv[1],encoding='utf-8').read();out=sys.argv[2];os.makedirs(out,exist_ok=True)
IDS=['audiolab','ableton','fl','cubase','logic','bitwig','protools','reaper'];errs=[];res={}
with sync_playwright() as p:
    b=p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required']);pg=b.new_page(viewport={'width':1600,'height':1000})
    pg.on('pageerror',lambda e:errs.append(str(e)[:400]));pg.on('console',lambda m:errs.append('console: '+m.text[:300]) if m.type=='error' and 'fetching the script' not in m.text and 'net::' not in m.text else None)
    pg.route('https://app.test/**',lambda r:r.fulfill(status=200,content_type='text/html',body=src.encode()) if r.request.url.endswith('.html') else r.fulfill(status=404,body=b''))
    pg.add_init_script("localStorage.getItem('audiolab-ui')||localStorage.setItem('audiolab-ui',JSON.stringify({splash:false,lat3:1}))")
    def load():
        pg.goto('https://app.test/index.html');pg.wait_for_function("() => window.AudioLab && window.AudioLab.version",timeout=90000);pg.wait_for_timeout(6000)
        pg.evaluate("()=>{const c=document.getElementById('liteNote');if(c)c.remove()}")
    run=lambda js:pg.evaluate("js=>window.AudioLab.run(js)",js)
    load();res['version']=run("VERSION");res['counts']=run("JSON.stringify([THEMES.length,FDS.length,HFD.length,Object.keys(MCOLS)])")
    run("(()=>{UI.lite=false;UI.liteMan=true;applyLite();try{selT=null;renderFx()}catch(e){}})()")
    pg.click('#mBtn');pg.wait_for_timeout(1000);run("(()=>{try{start()}catch(e){}})()");pg.wait_for_timeout(1200)
    for lv in ['zero','light','full']:
        for i in IDS:
            run("(()=>{thPick('%s');UI.fx=fxPre('%s');applyTrans()})()"%(i,lv));pg.wait_for_timeout(1300)
            run("(()=>{const t=document.getElementById('toast');if(t)t.hidden=true})()");pg.screenshot(path=f'{out}/{lv}-{i}.png')
            res[lv+'-'+i]=json.loads(run("JSON.stringify({cls:document.body.className,fd:mxsO().fd,mcol:mtrO().col,lv:fxLevel(),blue:getComputedStyle(document.documentElement).getPropertyValue('--blue').trim(),gtr:getComputedStyle(document.documentElement).getPropertyValue('--gtr').trim(),lane:TH.lane0,under:TH.under||null})"))
    run("(()=>{try{stop()}catch(e){}})()")
    # Settings: the cards, then a theme picked by a real click; the user changes the design afterwards and it stays
    run("(()=>{thPick('audiolab');UI.fx=fxPre('zero');applyTrans();openSettings('layout')})()");pg.wait_for_timeout(1200)
    run("document.getElementById('dawPres').scrollIntoView({block:'center'})");pg.wait_for_timeout(400);pg.locator('#set .sheet').screenshot(path=f'{out}/cards.png')
    res['cards']=run("document.querySelectorAll('#dawPres [data-thp] svg').length")
    pg.click('[data-thp=cubase]');pg.wait_for_timeout(900);res['click-cubase']=run("JSON.stringify([UI.dawLook,mxsO().fd,mtrO().col,document.querySelector('#dawPres .on').dataset.thp,[...document.querySelectorAll('[data-mxm=col]')].map(e=>e.value)])")
    pg.locator('#set .sheet').screenshot(path=f'{out}/cards-cubase.png')
    run("(()=>{mxsSet('fd',3);UI.mtr=Object.assign({},UI.mtr,{col:'heat'});saveUI();mtrUI()})()");pg.wait_for_timeout(300)
    run("document.getElementById('mtrSet').scrollIntoView({block:'end'})");pg.wait_for_timeout(400);pg.locator('#set .sheet').screenshot(path=f'{out}/meters.png')
    # the background sliders take over from the fixed colours
    run("(()=>{const e=document.getElementById('setBg');e.value=30;e.dispatchEvent(new Event('input',{bubbles:true}))})()");pg.wait_for_timeout(400)
    res['slider']=run("JSON.stringify([UI.dawTint,TH.lane0,document.documentElement.style.getPropertyValue('--blue')])")
    run("closeSet()");load()
    res['after-reload']=run("JSON.stringify([UI.dawLook,UI.dawTint,mxsO().fd,mtrO().col,document.body.className,document.documentElement.style.getPropertyValue('--blue')])")
    # recolour the tracks with a theme, then undo
    res['recolour']=run("(()=>{const a=S.tracks.slice(0,3).map(t=>t.color);UI.dawRecol=true;thPick('bitwig');const b=S.tracks.slice(0,3).map(t=>t.color);undo();const c=S.tracks.slice(0,3).map(t=>t.color);UI.dawRecol=false;thPick('audiolab');return JSON.stringify([a,b,c,UI.dawLook,document.body.className])})()")
    b.close()
print(json.dumps(res,indent=1));print('ERRORS',json.dumps(errs,indent=1))
