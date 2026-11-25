# Effect levels, since v0.186 on the Settings tab "Performance" (Light mode switch and the slider Lightest | Lighter, Optimised, Full effects).
# Usage: python3 tools/ui-tests/fxlevels.py index.html outdir
import sys,json,os
from playwright.sync_api import sync_playwright
src=open(sys.argv[1],encoding='utf-8').read();out=sys.argv[2];os.makedirs(out,exist_ok=True)
errs=[]
with sync_playwright() as p:
    b=p.chromium.launch();pg=b.new_page(viewport={'width':1600,'height':1000})
    pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('console',lambda m:errs.append('console: '+m.text) if m.type=='error' and 'fetching the script' not in m.text else None)
    pg.route('https://app.test/**',lambda r:r.fulfill(status=200,content_type='text/html',body=src.encode()) if r.request.url.endswith('.html') else r.fulfill(status=404,body=b''))
    pg.add_init_script("localStorage.getItem('audiolab-ui')||localStorage.setItem('audiolab-ui',JSON.stringify({order:['arr','fx','tr','map'],splash:false,lat3:1,pm:{on:true,st:2,user:true}}))")
    pg.goto('https://app.test/index.html');pg.wait_for_function("() => window.AudioLab && window.AudioLab.version",timeout=90000);pg.wait_for_timeout(6000)
    run=lambda js:pg.evaluate("js=>window.AudioLab.run(js)",js)
    pg.evaluate("()=>{const c=document.getElementById('liteNote');if(c)c.remove()}")
    # what each stop does to the page: elements with a backdrop filter, large see-through panels, outer shadows, glass layers in the page
    info=lambda:json.loads(run("""JSON.stringify((()=>{let bf=0,lens=0,see=[],sh=0;for(const e of document.querySelectorAll('body *')){if(!e.getClientRects().length)continue;const cs=getComputedStyle(e);const v=cs.backdropFilter;if(v&&v!=='none'){bf++;if(/url\\(/.test(v))lens++}
      const r=e.getBoundingClientRect();if(r.width*r.height<40000)continue;const m=cs.backgroundColor.match(/rgba\\((.*)\\)/),al=m?+m[1].split(',')[3]:1;if(m&&al>.2&&al<1)see.push(e.id||String(e.className).slice(0,20));if(cs.boxShadow!=='none'&&!/inset/.test(cs.boxShadow))sh++}
      return{pm:UI.pm,fx:UI.fx,lite:UI.lite,cls:document.body.className,bf,lens,see,sh,layers:{rf:!!(rfSvg&&rfSvg.isConnected),arrBlur:!!document.getElementById('arrBlur'),arrBack:!!document.getElementById('arrBack')}}})())"""))
    res={}
    run("(()=>{const t=S.tracks.find(t=>t.name==='Kick');selectTrack(t.id);renderFx();openMixer()})()");pg.wait_for_timeout(800)
    for st in [3,2,1,0]:
        run("(()=>{UI.pm={on:true,st:%d,user:true};pmApply()})()"%st);pg.wait_for_timeout(1200);res['stop%d'%st]=info();pg.screenshot(path=f'{out}/app-stop{st}.png')
    run("(()=>{UI.pm={on:false,st:0,user:true};pmApply()})()");pg.wait_for_timeout(800);res['off']=info()
    # the tab at each stop
    run("openSettings('perf')");pg.wait_for_timeout(800)
    for st in [0,1,2,3]:
        pg.click('#pmSl [data-st="%d"] i'%st);pg.wait_for_timeout(600);res['click%d'%st]=[run("UI.pm.st"),run("document.getElementById('pmCap').textContent")];pg.locator('#set .sheet').screenshot(path=f'{out}/tab-stop{st}.png')
    pg.click('.pmsw i');pg.wait_for_timeout(400);res['switch-off']=info()['fx'];pg.locator('#set .sheet').screenshot(path=f'{out}/tab-off.png')
    pg.click('.pmsw i');pg.wait_for_timeout(400);res['switch-on']=info()['pm']
    # effect toggles: refraction, blur, edge light, animations and the savers
    pg.click('#pmSl [data-st="2"] i');pg.wait_for_timeout(300)
    for sel in ['[data-pr=refr] .bpsw i','#pmBlur [data-bm=live]','[data-pr=edge] .bpsw i','[data-pr=anim] .bpsw i']:
        pg.click(sel);pg.wait_for_timeout(300);res['toggle '+sel]=[run("JSON.stringify(UI.fx)"),run("UI.pm.st")]
    t0=run("JSON.stringify([UI.glBack!==false,UI.glPlay!==false,UI.fxSleep!==false,UI.noteCache!==false])")
    for sel in ['[data-pr=glBack] .bpsw i','[data-pr=glPlay] .bpsw i','[data-pr=slpOn] .bpsw i','[data-pr=ncOn] .bpsw i']:pg.click(sel);pg.wait_for_timeout(250)
    res['savers']=[t0,run("JSON.stringify([UI.glBack!==false,UI.glPlay!==false,UI.fxSleep!==false,UI.noteCache!==false])")]
    for sel in ['[data-pr=glBack] .bpsw i','[data-pr=glPlay] .bpsw i','[data-pr=slpOn] .bpsw i','[data-pr=ncOn] .bpsw i']:pg.click(sel);pg.wait_for_timeout(250)
    # Automatic: never Lightest, Undo restores
    pg.click('#pmSl [data-st="0"] i');pg.wait_for_timeout(300)
    for fake in [None,60,20]:
        if fake:run("(()=>{window._ff=window._ff||fxFps;fxFps=ms=>new Promise(r=>setTimeout(()=>r(%d),ms));FPS.real=60})()"%fake)
        before=run("JSON.stringify(UI.pm)");pg.click('#pmAuto');pg.wait_for_timeout(500);pg.wait_for_function("()=>!window.AudioLab.run('PM.busy')",timeout=30000)
        res['auto fps=%s'%fake]=[run("UI.pm.st"),run("document.getElementById('pmRep').textContent")];pg.locator('#set .sheet').screenshot(path=f'{out}/tab-auto-{fake}.png')
        pg.click('#pmUndo');pg.wait_for_timeout(300);res['undo fps=%s'%fake]=run("JSON.stringify(UI.pm)")==before
    run("(()=>{if(window._ff)fxFps=window._ff;FPS.real=0})()")
    # the logo in Settings: frames painted in two seconds while the mouse rests
    res['logo']=run("(()=>{const o=paintAtom;let n=0;paintAtom=function(c){if(c.id==='navAtomC')n++;return o.apply(this,arguments)};return new Promise(r=>setTimeout(()=>{paintAtom=o;r(n)},2000))})()")
    run("closeSet()")
    run("(()=>{UI.pm={on:true,st:2,user:true};pmApply();try{start()}catch(e){}})()");pg.wait_for_timeout(2500);pg.screenshot(path=f'{out}/play-opt.png');run("(()=>{try{stop()}catch(e){}})()")
    pg.reload();pg.wait_for_function("() => window.AudioLab && window.AudioLab.version",timeout=90000);pg.wait_for_timeout(4000);res['after-reload']=run("JSON.stringify(UI.pm)")
    b.close()
print(json.dumps(res,indent=1));print('ERRORS',json.dumps(errs,indent=1))
