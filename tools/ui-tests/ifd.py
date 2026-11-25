# v0.172: update window, Audio devices window, "Interface and DAC" settings. Usage: python3 ifd.py ../../index.html outdir
import sys,json,os
from playwright.sync_api import sync_playwright
src=open(sys.argv[1],encoding='utf-8').read();out=sys.argv[2];os.makedirs(out,exist_ok=True)
errs=[];res={}
MAN=json.dumps({"version":"0.999","sha256":"x","size":2300000,"minShell":"0.147.0","notes":"Test notes."})
COM=json.dumps([{"commit":{"message":"v0.999: a test release with a new thing\n\nmore"}},{"commit":{"message":"backlog log"}},{"commit":{"message":"v0.172: update window, audio devices, Interface and DAC"}}])
with sync_playwright() as p:
    b=p.chromium.launch(args=['--use-fake-device-for-media-stream','--use-fake-ui-for-media-stream','--autoplay-policy=no-user-gesture-required']);cx=b.new_context(viewport={'width':1600,'height':1000},permissions=['microphone']);pg=cx.new_page()
    pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('console',lambda m:errs.append('console: '+m.text) if m.type=='error' and 'net::' not in m.text and 'Failed to load resource' not in m.text else None)
    mode={'gh':'ok'}
    def gh(r):
        if mode['gh']=='down': return r.abort()
        u=r.request.url
        r.fulfill(status=200,content_type='application/json',headers={'access-control-allow-origin':'*'},body=MAN if 'app-version' in u else COM)
    pg.route('https://raw.githubusercontent.com/**',gh);pg.route('https://api.github.com/**',gh)
    pg.route('https://app.test/**',lambda r:r.fulfill(status=200,content_type='text/html',body=src.encode()) if r.request.url.endswith('.html') else r.fulfill(status=404,body=b''))
    pg.add_init_script("localStorage.getItem('audiolab-ui')||localStorage.setItem('audiolab-ui',JSON.stringify({splash:false,lat3:1}))")
    pg.goto('https://app.test/index.html');pg.wait_for_function("() => window.AudioLab && window.AudioLab.version",timeout=90000);pg.wait_for_timeout(6000)
    run=lambda js:pg.evaluate("js=>window.AudioLab.run(js)",js)
    res['version']=run('VERSION')
    # update window in the browser: newer version online
    run("openSettings('general')");pg.wait_for_timeout(400);res['genUpd']=run("JSON.stringify({hidden:document.getElementById('genUpd').hidden,auto:!!document.getElementById('updAutoChk')})")
    pg.click('#genUpd');pg.wait_for_timeout(1500);res['upd-web-new']=run("document.querySelector('#updDlg .upds').textContent+' | '+document.querySelector('#updDlg .updg').innerText.replace(/\\n/g,' ')+' | '+[...document.querySelectorAll('#updDlg .cdb button')].map(b=>b.textContent).join('/')");pg.locator('#updDlg .sheet').screenshot(path=f'{out}/upd-web-new.png')
    pg.keyboard.press('Escape');pg.wait_for_timeout(200);res['upd-closed']=run("!document.getElementById('updDlg')")
    mode['gh']='down';run("UPD.notes=null;updOpen()");pg.wait_for_timeout(1500);res['upd-web-offline']=run("document.querySelector('#updDlg .upds').textContent");pg.locator('#updDlg .sheet').screenshot(path=f'{out}/upd-web.png');run("updClose()")
    # pretend to be an older desktop app build (no updateCheck): available, then offline
    mode['gh']='ok';run("(()=>{window.__calls=[];window.audiolabDesktop={isDesktop:true,platform:'darwin',version:async()=>'0.170.0',checkForUpdates:async()=>{window.__calls.push('check')},applyUpdate:async()=>{window.__calls.push('apply')},dac:null};UPD.notes=null;updOpen()})()");pg.wait_for_timeout(1500)
    res['upd-old-new']=run("document.querySelector('#updDlg .upds').textContent+' | '+[...document.querySelectorAll('#updDlg .cdb button')].map(b=>b.textContent).join('/')");pg.locator('#updDlg .sheet').screenshot(path=f'{out}/upd-old-new.png')
    pg.click('#updDlg [data-up=go]');pg.wait_for_timeout(400);res['upd-old-go']=run("JSON.stringify(window.__calls)+' | '+document.querySelector('#updDlg .upds').textContent");pg.locator('#updDlg .sheet').screenshot(path=f'{out}/upd-old-go.png');run("updClose()")
    mode['gh']='down';run("updOpen()");pg.wait_for_timeout(1500);res['upd-old-down']=run("document.querySelector('#updDlg .upds').textContent+' | '+[...document.querySelectorAll('#updDlg .cdb button')].map(b=>b.textContent).join('/')");pg.locator('#updDlg .sheet').screenshot(path=f'{out}/upd-old-down.png');run("updClose()")
    # automatic installing with an old build: updateReady arrives, waits while playing, applies when idle
    run("(()=>{window.__calls=[];UI.updAuto=true;LACT=0;start()})()");pg.wait_for_timeout(500);res['auto-ret']=run("window.audiolabHost.updateReady('0.999','n')");pg.wait_for_timeout(3000);res['auto-while-playing']=run("JSON.stringify(window.__calls)+' card:'+!document.getElementById('updCard').hidden");pg.screenshot(path=f'{out}/auto-card.png',clip={'x':1280,'y':30,'width':320,'height':180})
    run("(()=>{stop();LACT=0})()");pg.wait_for_timeout(3500);res['auto-after-stop']=run("JSON.stringify(window.__calls)+' flag:'+localStorage.getItem('al-upd-done')");run("(()=>{UI.updAuto=false;localStorage.removeItem('al-upd-done');clearInterval(UPD.autoT);delete window.audiolabDesktop})()")
    # About button
    run("closeSet();showSplash(true)");pg.wait_for_timeout(600);pg.click('#abUpd');pg.wait_for_timeout(800);res['about-click']=run("!!document.getElementById('updDlg')");pg.screenshot(path=f'{out}/about-upd.png');run("updClose();hideSplash()");mode['gh']='ok'
    # Audio devices window
    run("audDevOpen()");pg.wait_for_timeout(1500);res['devs']=run("JSON.stringify({outs:ADV.outs.map(o=>[o.label,o.type,o.use,o.def,o.ch,o.rate]),ins:ADV.ins.map(o=>[o.label,o.type,o.use,o.cap]),named:ADV.named})");pg.locator('#audWin').screenshot(path=f'{out}/devices.png')
    res['dev-btns']=run("JSON.stringify({test:document.querySelectorAll('#audWin .adtest').length,use:document.querySelectorAll('#audWin .aduse').length,on:document.querySelectorAll('#audWin .adon').length})")
    if run("!!document.querySelector('#audWin [data-ad=listen]')"):
        pg.click('#audWin [data-ad=listen]');pg.wait_for_timeout(900);res['listen']=run("(()=>{const b=document.querySelector('#audWin .adlv:not([hidden]) u');return b?b.style.width:'no bar'})()");pg.locator('#audWin').screenshot(path=f'{out}/devices-listen.png')
    # fake a rich device list to see the icons and profiles (drawing only)
    run("""(()=>{const mk=(label,kind,extra)=>{const o=Object.assign({id:'x'+Math.random(),gid:'',label,kind,hw:null,full:false,def:false,use:false,cap:null},extra||{});o.prof=devProf(label);o.type=devKind(label,kind,o.hw,o.prof);o.rate=o.rate||0;o.ch=o.ch||0;o.bits=o.bits||0;o.vol=o.vol==null?null:o.vol;return o};
      window.__fake={outs:[mk('MacBook Pro Speakers (Built-in)','out',{def:true,rate:48000,ch:2,vol:.5}),mk('External Headphones (Built-in)','out'),mk('iFi (by AMR) HD USB Audio (20b1:3008)','out',{use:true,rate:96000,bits:32,ch:2,vol:-1}),mk('Mojo 2','out'),mk('ZOOM AMS-24','out'),mk('Scarlett 2i2 USB (1235:8210)','out'),mk('AirPods Pro (Bluetooth)','out'),mk('LG HDR 4K (DisplayPort)','out'),mk('BlackHole 2ch (Virtual)','out'),mk('USB Audio Device (0d8c:0014)','out')],ins:[mk('MacBook Pro Microphone (Built-in)','in',{def:true,use:true,cap:{ch:1,sr:48000}}),mk('ZOOM AMS-24','in',{cap:{ch:2,sr:96000}}),mk('Scarlett 2i2 USB (1235:8210)','in'),mk('Yeti Stereo Microphone (046d:0ab7)','in')]};
      const real=adScan;adScan=async()=>{Object.assign(ADV,window.__fake,{named:true,cur:'x',at:performance.now(),curLabel:'iFi (by AMR) HD USB Audio (20b1:3008)'});return ADV};window.__real=real;audDevRender(null,true)})()""");pg.wait_for_timeout(800)
    res['fake-types']=run("JSON.stringify(ADV.outs.concat(ADV.ins).map(o=>[o.label.slice(0,22),o.type,o.prof&&o.prof.n]))");run("(()=>{const w=document.getElementById('audWin');w.style.height='860px';w.style.top='20px'})()");pg.wait_for_timeout(300);pg.locator('#audWin').screenshot(path=f'{out}/devices-fake.png')
    # settings page, DAC mode (with the fake Gryphon as current)
    run("(()=>{document.getElementById('audWin').hidden=true;openSettings('dac')})()");pg.wait_for_timeout(900);res['ifd-mode']=run("JSON.stringify({mode:ifdMode(),why:document.getElementById('ifdWhy').textContent.slice(0,90),nav:document.querySelector('#setNav [data-tab=dac]').textContent.trim(),bp:document.getElementById('ifdBp').innerText.split('\\n')[0]})")
    pg.locator('#set .sheet').screenshot(path=f'{out}/ifd-dac-top.png');run("document.querySelector('#setBody').scrollTop=520");pg.wait_for_timeout(300);pg.locator('#set .sheet').screenshot(path=f'{out}/ifd-dac-mid.png');run("document.querySelector('#setBody').scrollTop=9999");pg.wait_for_timeout(300);pg.locator('#set .sheet').screenshot(path=f'{out}/ifd-dac-bottom.png')
    # linked controls: bit-perfect, sample rate, buffer
    run("document.querySelector('#setBody').scrollTop=0");pg.click('#ifdSeg [data-ifm=int]');pg.wait_for_timeout(400);res['int-mode']=ifm=run("JSON.stringify({mode:ifdMode(),dacHidden:document.querySelector('[data-ifp=dac]').hidden,intHidden:document.querySelector('[data-ifp=int]').hidden})")
    pg.locator('#set .sheet').screenshot(path=f'{out}/ifd-int-top.png');run("document.querySelector('#setBody').scrollTop=9999");pg.wait_for_timeout(300);pg.locator('#set .sheet').screenshot(path=f'{out}/ifd-int-bottom.png')
    pg.select_option('#ifdBuf','512');pg.wait_for_timeout(900);res['buf-link']=run("JSON.stringify({ui:UI.buf,cp:document.getElementById('bufSel').value,mine:document.getElementById('ifdBuf').value,base:Math.round(ctx.baseLatency*ctx.sampleRate)})")
    pg.select_option('#ifdSr','44100');pg.wait_for_timeout(900);res['sr-link']=run("JSON.stringify({ui:UI.sr,cp:document.getElementById('srSel').value,lock:document.getElementById('lockSr').value,ctx:ctx.sampleRate})")
    run("(()=>{const s=document.getElementById('srSel');s.value='0';s.dispatchEvent(new Event('change'))})()");pg.wait_for_timeout(900);res['sr-back']=run("JSON.stringify({mine:document.getElementById('ifdSr').value,lock:document.getElementById('lockSr').value})")
    run("(()=>{const s=document.getElementById('ifdOff');s.value='12';s.dispatchEvent(new Event('change'))})()");res['off-link']=run("JSON.stringify({ui:UI.recOff,cp:document.getElementById('recOff').value})");run("(()=>{UI.recOff=0;saveUI();cpSync()})()")
    # round trip (the fake input has no click in it: must report that, not hang)
    pg.click('#ifdRtGo');pg.wait_for_timeout(3500);res['roundtrip']=run("document.getElementById('ifdRt').textContent")
    # input channel and monitoring on an armed audio track
    res['arm']=run("""(async()=>{pushUndo();const t={id:rid(),name:'Audio in',kind:'audio',clips:[],vol:1,pan:0,fx:[],color:'#4c8dff'};S.tracks.push(t);window.__t=t;await armTrack(t);const a={raw:!!t._micRaw,same:t._mic===t._micRaw};
      UI.inCh='l';UI.inMon=true;inWireAll();a.mono={diff:t._mic!==t._micRaw,ch:t._mic.getAudioTracks()[0].getSettings().channelCount,nodes:t._inN&&t._inN.length};UI.inCh='st';UI.inMon=false;inWireAll();a.back=t._mic===t._micRaw&&!t._inN;await armTrack(t);a.off={mic:t._mic,raw:t._micRaw};S.tracks.pop();return JSON.stringify(a)})()""")
    # output pair: nothing changes at the default, and the routing code runs when a pair is forced
    res['outpair']=run("JSON.stringify({max:ctx.destination.maxChannelCount,pairs:outPairs(),op:ctx._op||0})")
    # DAC mode again: bit-perfect toggle and master fader reflected
    pg.click('#ifdSeg [data-ifm=dac]');pg.wait_for_timeout(300);run("document.querySelector('#setBody').scrollTop=0")
    run("(()=>{const c=document.getElementById('bpChk');c.checked=true;c.dispatchEvent(new Event('change'))})()");pg.wait_for_timeout(1600);res['bp-on']=run("document.getElementById('ifdBp').innerText.replace(/\\n+/g,' | ').slice(0,260)");pg.locator('#set .sheet').screenshot(path=f'{out}/ifd-dac-bp.png')
    run("(()=>{const c=document.getElementById('bpChk');c.checked=false;c.dispatchEvent(new Event('change'))})()")
    pg.click('#ifdSeg [data-ifm=auto]');res['errs-before-reload']=list(errs)
    res['textcheck']=run("JSON.stringify([...document.querySelectorAll('#ifd *,#audWin *')].filter(e=>/—/.test((e.title||'')+(e.children.length?'':e.textContent))).length)")
    b.close()
res['errors']=errs
print(json.dumps(res,indent=1))
