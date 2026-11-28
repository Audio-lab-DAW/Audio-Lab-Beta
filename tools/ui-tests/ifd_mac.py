# v0.172: the Mac desktop paths with a stand-in for the app's bridge (device info, device rate, volume link). Usage: python3 ifd_mac.py ../../index.html outdir
import sys,json,os
import sys as _ws_sys, os as _ws_os; _ws_sys.path.insert(0, _ws_os.path.join(_ws_os.path.dirname(_ws_os.path.abspath(__file__)), '../test-songs')); from alsong import alsong  # task WS-F: the test songs
from playwright.sync_api import sync_playwright
src=open(sys.argv[1],encoding='utf-8').read();out=sys.argv[2];os.makedirs(out,exist_ok=True);errs=[];res={}
FAKE="""window.__dev={uid:'u1',name:'Fake Default Audio Output',maker:'x',transport:'usb',out:4,in:0,rate:48000,rates:[44100,48000,96000],bits:24,hog:-1,defaultOut:true,defaultIn:false,volume:.6,hasVolume:true,default:true};window.__log=[];
window.audiolabDesktop={isDesktop:true,platform:'darwin',version:async()=>'0.172.0',updateCheck:async()=>({status:'current',installed:'0.172',latest:'0.172',at:Date.now()}),updateStatus:async()=>({}),applyUpdate:async()=>false,checkForUpdates:async()=>{},displayHz:async()=>60,isFullScreen:async()=>false,onDock(){},onFromChild(){},onDockHover(){},
 dac:{list:async()=>({devices:[window.__dev]}),get:async()=>({volume:window.__dev.volume}),set:async(u,v)=>{window.__dev.volume=v;window.__log.push('vol '+v);return{ok:true,volume:v}},info:async()=>({devices:[window.__dev]}),rate:async(u,hz)=>{window.__log.push('rate '+hz);window.__dev.rate=hz;return{ok:true,rate:hz}}}};"""
with sync_playwright() as p:
    b=p.chromium.launch(args=['--use-fake-device-for-media-stream','--use-fake-ui-for-media-stream','--autoplay-policy=no-user-gesture-required']);cx=b.new_context(viewport={'width':1600,'height':1000},permissions=['microphone']);pg=cx.new_page()
    pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('https://app.test/**',alsong(lambda r:r.fulfill(status=200,content_type='text/html',body=src.encode()) if r.request.url.endswith('.html') else r.fulfill(status=404,body=b'')))
    pg.add_init_script(FAKE+"localStorage.getItem('audiolab-ui')||localStorage.setItem('audiolab-ui',JSON.stringify({splash:false,lat3:1}))")
    pg.goto('https://app.test/index.html');pg.wait_for_function("() => window.AudioLab && window.AudioLab.version",timeout=90000);pg.wait_for_timeout(6000)
    run=lambda js:pg.evaluate("js=>window.AudioLab.run(js)",js)
    run("(()=>{ensureCtx();const g=navigator.mediaDevices.getUserMedia({audio:true});openSettings('dac')})()");pg.wait_for_timeout(2500)
    res['cur']=run("JSON.stringify((o=>o&&[o.label,o.type,o.full,o.rate,o.ch,o.bits,o.vol])(adCur()))");res['engine']=run("ctx.sampleRate")
    res['checklist']=run("document.getElementById('ifdBp').innerText.replace(/\\n+/g,' | ')");pg.locator('#set .sheet').screenshot(path=f'{out}/mac-dac-top.png')
    res['rate-btn']=run("!!document.querySelector('#ifd [data-ifa=rate]')")
    if res['rate-btn']:
        pg.click('#ifd [data-ifa=rate]');pg.wait_for_timeout(1500);res['after-rate']=run("JSON.stringify(window.__log)+' | '+document.getElementById('ifdBp').innerText.split('\\n').filter(x=>/run at|runs at/.test(x)).join(' ')")
    # automatic switching: device back to 48k, engine fixed at 96k
    run("(()=>{window.__dev.rate=48000;window.__log=[];const c=document.getElementById('ifdRf');c.click()})()");pg.wait_for_timeout(1500);res['follow-on']=run("JSON.stringify({ui:UI.rateFollow,log:window.__log,vis:!document.getElementById('ifdRfL').hidden})")
    run("(()=>{window.__log=[];const s=document.getElementById('lockSr');s.value='96000';s.dispatchEvent(new Event('change'))})()");pg.wait_for_timeout(3000);res['follow-96']=run("JSON.stringify({ctx:ctx.sampleRate,log:window.__log,dev:window.__dev.rate})")
    # volume link, both ways
    run("(()=>{const r=document.getElementById('ifdVolR');r.value=80;r.dispatchEvent(new Event('input',{bubbles:true}))})()");pg.wait_for_timeout(600);res['vol-set']=run("JSON.stringify({dev:window.__dev.volume,DAC:DAC.v})")
    run("(()=>{const b=document.querySelector('#ifd [data-ifa=vol100]');if(b)b.click()})()");pg.wait_for_timeout(1500);res['vol100']=run("JSON.stringify({dev:window.__dev.volume,row:document.getElementById('ifdBp').innerText.split('\\n').filter(x=>/volume/.test(x)).join(' ')})")
    run("document.querySelector('#setBody').scrollTop=600");pg.wait_for_timeout(300);pg.locator('#set .sheet').screenshot(path=f'{out}/mac-dac-mid.png')
    # output pair with a 4 channel device (headless reports 2, so the routing itself is forced once to see it builds without errors)
    res['pairs']=run("JSON.stringify({max:ctx.destination.maxChannelCount,pairs:outPairs()})")
    res['general']=run("(()=>{openSettings('general');return JSON.stringify({auto:!!document.getElementById('updAutoChk'),btn:!document.getElementById('genUpd').hidden})})()");pg.wait_for_timeout(300);pg.locator('#set .sheet').screenshot(path=f'{out}/mac-general.png')
    run("(()=>{closeSet();audDevOpen()})()");pg.wait_for_timeout(1200);pg.locator('#audWin').screenshot(path=f'{out}/mac-devices.png')
    b.close()
res['errors']=errs;print(json.dumps(res,indent=1))
