# v0.168: effect levels. Usage: python3 fxlevels.py ../../index.html outdir
import sys,json,os
from playwright.sync_api import sync_playwright
src=open(sys.argv[1],encoding='utf-8').read();out=sys.argv[2];os.makedirs(out,exist_ok=True)
errs=[]
with sync_playwright() as p:
    b=p.chromium.launch();pg=b.new_page(viewport={'width':1600,'height':1000})
    pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('console',lambda m:errs.append('console: '+m.text) if m.type=='error' else None)
    pg.route('https://app.test/**',lambda r:r.fulfill(status=200,content_type='text/html',body=src.encode()) if r.request.url.endswith('.html') else r.fulfill(status=404,body=b''))
    pg.add_init_script("localStorage.getItem('audiolab-ui')||localStorage.setItem('audiolab-ui',JSON.stringify({splash:false,lat3:1}))")
    pg.goto('https://app.test/index.html');pg.wait_for_function("() => window.AudioLab && window.AudioLab.version",timeout=90000);pg.wait_for_timeout(6000)
    run=lambda js:pg.evaluate("js=>window.AudioLab.run(js)",js)
    info=lambda:run("""(()=>{const bf=id=>{const e=document.getElementById(id);return e?getComputedStyle(e).backdropFilter:null};const all=[...document.querySelectorAll('*')].filter(e=>/url\\(/.test(getComputedStyle(e).backdropFilter)).map(e=>e.id||e.className);
      return JSON.stringify({level:fxLevel(),fx:UI.fx,cls:document.body.className,tr:bf('tr'),hglass:bf('hglass'),fxglass:bf('fxglass'),lens:all,arrBlur:(()=>{const c=document.getElementById('arrBlur');return c?[c.width,c.height,c.style.display,c.style.clipPath]:null})(),arrBack:(()=>{const c=document.getElementById('arrBack');return c?[c.width,c.height,c.style.display]:null})(),clip:arr.style.clipPath,elb:[...document.querySelectorAll('*')].filter(e=>e.style&&e.style.getPropertyValue('--elb')).length,ga:document.documentElement.style.getPropertyValue('--ga'),edge:document.documentElement.style.getPropertyValue('--edge')})})()""")
    res={}
    for lv in ['full','light','zero']:
        run("(()=>{UI.fx=fxPre('%s');applyTrans()})()"%lv);pg.wait_for_timeout(1500);res[lv]=json.loads(info());pg.screenshot(path=f'{out}/app-{lv}.png')
    # settings in each level
    for lv in ['full','light','zero']:
        run("(()=>{UI.fx=fxPre('%s');applyTrans();openSettings('glass')})()"%lv);pg.wait_for_timeout(1800);res['set-'+lv]=json.loads(info());pg.screenshot(path=f'{out}/set-{lv}.png')
        pg.locator('#set .sheet').screenshot(path=f'{out}/sheet-{lv}.png')
    run("(()=>{document.querySelector('#setBody').scrollTop=9999})()");pg.wait_for_timeout(500);pg.locator('#set .sheet').screenshot(path=f'{out}/sheet-bottom.png')
    # toggles and the optimise button
    run("(()=>{UI.fx=fxPre('full');applyTrans();document.querySelector('#setBody').scrollTop=0})()")
    pg.click('#fxLv [data-fxl=opt]');pg.wait_for_timeout(300);res['click-opt']=json.loads(info())['fx']
    pg.click('#fxUndo');pg.wait_for_timeout(300);res['undo']=json.loads(info())['level']
    pg.click('#fxOptB');pg.wait_for_function("!FXO_busy()",timeout=30000) if False else pg.wait_for_timeout(12000)
    res['optimise']=run("JSON.stringify({rep:document.getElementById('fxRep').textContent,fx:UI.fx,busy:FXO.busy,undo:!document.getElementById('fxUndo').hidden})");pg.locator('#set .sheet').screenshot(path=f'{out}/sheet-optimised.png')
    pg.click('#fxUndo');pg.wait_for_timeout(300);res['undo2']=json.loads(info())['level']
    # toggles in the performance box
    run("(()=>{UI.fx=fxPre('full');applyTrans();document.querySelector('#setBody').scrollTop=9999})()");pg.wait_for_timeout(300)
    t0=run("JSON.stringify([UI.glBack!==false,UI.glPlay!==false,UI.fxSleep!==false,UI.noteCache!==false,UI.fx])")
    for sel in ['[data-sw=glBack] i','[data-sw=glPlay] i','[data-sw=slpOn] i','[data-sw=ncOn] i','#fxEdge + i','#fxAnim + i','#fxBlurSeg [data-bm=copy]']:
        pg.click(sel);pg.wait_for_timeout(350)
    res['toggles']=[t0,run("JSON.stringify([UI.glBack!==false,UI.glPlay!==false,UI.fxSleep!==false,UI.noteCache!==false,UI.fx])")]
    for sel in ['[data-sw=glBack] i','[data-sw=glPlay] i','[data-sw=slpOn] i','[data-sw=ncOn] i']:
        pg.click(sel);pg.wait_for_timeout(350)
    run("(()=>{document.querySelector('#setBody').scrollTop=0})()");pg.click('#fxRefr + i');pg.wait_for_timeout(300);res['refr-switch']=json.loads(info())['fx']
    run("(()=>{UI.lite=false;UI.liteMan=false;applyLite();UI.fx=fxPre('full');applyTrans()})()")
    # logo: frames painted in one second while the mouse rests
    res['logo']=run("(()=>{const o=paintAtom;let n=0;paintAtom=function(c){if(c.id==='navAtomC')n++;return o.apply(this,arguments)};return new Promise(r=>setTimeout(()=>{paintAtom=o;r(n)},2000))})()")
    run("closeSet()");
    # playing
    run("(()=>{UI.fx=fxPre('light');applyTrans();try{start()}catch(e){}})()");pg.wait_for_timeout(2500);res['play-light']=json.loads(info());pg.screenshot(path=f'{out}/play-light.png')
    run("(()=>{UI.fx=fxPre('full');applyTrans()})()");pg.wait_for_timeout(2000);pg.screenshot(path=f'{out}/play-full.png');run("(()=>{try{stop()}catch(e){}})()")
    pg.reload();pg.wait_for_function("() => window.AudioLab && window.AudioLab.version",timeout=90000);pg.wait_for_timeout(4000);res['after-reload']=json.loads(info())['level']
    b.close()
print(json.dumps(res,indent=1));print('ERRORS',json.dumps(errs,indent=1))
