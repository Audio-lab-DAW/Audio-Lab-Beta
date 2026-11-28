# v0.207 (task Y): the centred update window. Usage: python3 updwin.py ../../index.html outdir
# Over-the-air update (audiolabHost.updateReady) and desktop app updates (audiolabHost.appUpdate) are simulated with a fake audiolabDesktop.
import sys,json,os
import sys as _ws_sys, os as _ws_os; _ws_sys.path.insert(0, _ws_os.path.join(_ws_os.path.dirname(_ws_os.path.abspath(__file__)), '../test-songs')); from alsong import alsong  # task WS-F: the test songs
from playwright.sync_api import sync_playwright
src=open(sys.argv[1],encoding='utf-8').read();out=sys.argv[2];os.makedirs(out,exist_ok=True)
root=os.path.dirname(os.path.abspath(sys.argv[1]))
errs=[];res={}
COM=json.dumps([{"commit":{"message":"v0.207: update window (task Y): the update notice is a centred window with the logo, the versions, what is new and what to do\n\nmore"}},{"commit":{"message":"backlog log"}},{"commit":{"message":"v0.206: AI voices for Voice (task Z2): make a voice from an example clip and a recording sings or talks with that voice while keeping its notes and note edits; OpenVoice V2, ONNX fp16 66 MB downloaded once"}},{"commit":{"message":"v0.205: mixer sidechain window and cable menus (task AB)"}},{"commit":{"message":"v0.204: loop bar fix (task AC)"}}])
with sync_playwright() as p:
    b=p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required']);cx=b.new_context(viewport={'width':1600,'height':1000},device_scale_factor=2);pg=cx.new_page()
    pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('console',lambda m:errs.append('console: '+m.text) if m.type=='error' and 'net::' not in m.text and 'Failed to load resource' not in m.text else None)
    pg.route('https://api.github.com/**',lambda r:r.fulfill(status=200,content_type='application/json',headers={'access-control-allow-origin':'*'},body=COM))
    pg.route('https://raw.githubusercontent.com/**',lambda r:r.abort())
    def app(r):
        u=r.request.url.split('?')[0].replace('https://app.test/','')
        if u=='index.html':return r.fulfill(status=200,content_type='text/html',body=src.encode())
        f=os.path.join(root,u)
        if os.path.isfile(f):return r.fulfill(status=200,body=open(f,'rb').read(),content_type='image/png' if f.endswith('.png') else 'application/octet-stream')
        r.fulfill(status=404,body=b'')
    pg.route('https://app.test/**',alsong(app))
    pg.add_init_script("localStorage.getItem('audiolab-ui')||localStorage.setItem('audiolab-ui',JSON.stringify({splash:false,lat3:1}))")
    pg.goto('https://app.test/index.html');pg.wait_for_function("() => window.AudioLab && window.AudioLab.version",timeout=90000);pg.wait_for_timeout(5000)
    run=lambda js:pg.evaluate("js=>window.AudioLab.run(js)",js)
    res['load-errors']=list(errs)
    res['version']=run('VERSION')
    W="(()=>{const m=document.getElementById('uywM');if(!m)return 'none';return m.querySelector('h3').textContent+' | '+m.querySelector('.uywv').innerText.replace(/\\n/g,' ')+' | steps: '+[...m.querySelectorAll('.uywst li')].map(l=>l.textContent).join(' / ')+' | note: '+((m.querySelector('.uywnote')||{}).textContent||'-')+' | buttons: '+[...m.querySelectorAll('.uywb button')].map(b=>b.textContent).join('/')+' | rel: '+m.querySelectorAll('.uywrl li').length+' | logo: '+!!m.querySelector('.uywlogo img')})()"
    badge="(()=>{const b=document.getElementById('uywB');return !b?'none':b.hidden?'hidden':b.textContent})()"
    tips="[...document.querySelectorAll('#uywM button,#uywB')].filter(b=>!b.title).length"
    # a desktop app (Mac, older app build 0.170) with a downloaded program update
    run("(()=>{window.__calls=[];localStorage.removeItem('al-upd-later');window.audiolabDesktop={isDesktop:true,platform:'darwin',version:async()=>'0.170.0',applyUpdate:async()=>{window.__calls.push('apply');return true},updateApp:async()=>{window.__calls.push('updateApp');return 'page'},installApp:async()=>{window.__calls.push('installApp');return true},checkForUpdates:async()=>{}}})()")
    res['ota-ret']=run("window.audiolabHost.updateReady('0.999','The update notice is now a window in the middle with the logo, the versions and what is new.')");pg.wait_for_timeout(900)
    res['ota-window']=run(W);res['ota-no-tooltip']=run(tips)
    pg.locator('#uywM .uyww').screenshot(path=f'{out}/ota.png');pg.screenshot(path=f'{out}/ota-full.png')
    res['ota-centre']=run("(()=>{const r=document.querySelector('#uywM .uyww').getBoundingClientRect();return [Math.round(r.left+r.width/2-innerWidth/2),Math.round(r.top+r.height/2-innerHeight/2)]})()")
    pg.click('#uywM .uywrl li');res['rel-expand']=run("document.querySelector('#uywM .uywrl li').classList.contains('open')")
    pg.keyboard.press('Escape');pg.wait_for_timeout(200);res['esc']=run(W)+' / badge: '+run(badge)
    pg.click('#uywB');pg.wait_for_timeout(500);res['badge-opens']=run(W)[:40]
    pg.click('#uywM .uywx');pg.wait_for_timeout(200);res['x']=run(W)+' / badge: '+run(badge)
    run("window.audiolabHost.updateReady('0.999','n')");pg.wait_for_timeout(300);res['again-after-x-same-session']=run(W)
    pg.click('#uywB');pg.wait_for_timeout(400);pg.click('#uywM [data-uy=later]');pg.wait_for_timeout(200);res['later']=run("localStorage.getItem('al-upd-later')")+' / '+run(W)
    run("UYW.closed=''");run("window.audiolabHost.updateReady('0.999','n')");pg.wait_for_timeout(300);res['again-after-later']=run(W)+' / badge: '+run(badge)
    pg.click('#uywB');pg.wait_for_timeout(400);pg.click('#uywM [data-uy=go]');pg.wait_for_timeout(300);res['restart-now']=run("JSON.stringify(window.__calls)")+' / done flag: '+run("localStorage.getItem('al-upd-done')");run("localStorage.removeItem('al-upd-done');document.getElementById('uywM')&&uywClose()")
    # playback: no window while playing, only the badge; no keys taken; opens after the sound stops
    run("(()=>{localStorage.removeItem('al-upd-later');UYW.closed='';document.getElementById('uywB').hidden=true;start()})()");pg.wait_for_timeout(500)
    run("window.audiolabHost.updateReady('1.000','n')");pg.wait_for_timeout(1500);res['while-playing']=run(W)+' / badge: '+run(badge)+' / playing: '+str(run('play.on'))
    pg.screenshot(path=f'{out}/playing-badge.png',clip={'x':1200,'y':20,'width':400,'height':90})
    pg.keyboard.press('Escape');pg.keyboard.press('Space');pg.wait_for_timeout(300);res['space-while-playing-stops']=str(run('play.on'))+' (false = Space reached the transport)'
    pg.wait_for_timeout(2500);res['after-stop']=run(W)[:60]
    pg.keyboard.press('Space');pg.wait_for_timeout(900);res['play-while-open-folds']=run(W)+' / badge: '+run(badge)+' / playing: '+str(run('play.on'))
    run('stop()');pg.wait_for_timeout(2500);res['reopens-after-stop']=run(W)[:60];run("document.getElementById('uywM')&&uywClose()")
    # Mac, new desktop app needed (older app 0.170: the icon changed since)
    run("(()=>{UYW.appV='';window.audiolabHost.appUpdate({version:'0.300',stage:'needed',auto:false,app:'0.170.0',notes:'This version needs the new desktop app.'})})()");pg.wait_for_timeout(700)
    res['mac-app']=run(W);pg.locator('#uywM .uyww').screenshot(path=f'{out}/mac-app.png')
    pg.click('#uywM [data-uy=dl]');pg.wait_for_timeout(200);res['mac-dl']=run("JSON.stringify(window.__calls)");run("uywClose()")
    run("(()=>{UYW.appV='';window.audiolabHost.appUpdate({version:'0.301',stage:'needed',auto:false,app:'0.207.0',notes:'n'})})()");pg.wait_for_timeout(500);res['mac-app-new-icon-already']=run(W).split('| note: ')[1][:5];run("uywClose()")
    # Windows: the app downloads by itself, then Restart and install
    run("(()=>{window.__calls=[];window.audiolabDesktop.platform='win32';UYW.appV='';window.audiolabHost.appUpdate({version:'0.300',stage:'needed',auto:true,app:'0.206.0',notes:'n'})})()");pg.wait_for_timeout(500);res['win-needed']=run(W);pg.locator('#uywM .uyww').screenshot(path=f'{out}/win-needed.png');pg.click('#uywM [data-uy=later]');pg.wait_for_timeout(200)
    run("window.audiolabHost.appUpdate({version:'0.300',stage:'ready',auto:true,app:'0.206.0',notes:'The new app is here.'})");pg.wait_for_timeout(500);res['win-ready']=run(W);pg.locator('#uywM .uyww').screenshot(path=f'{out}/win-ready.png')
    pg.click('#uywM [data-uy=install]');pg.wait_for_timeout(300);res['win-install']=run("JSON.stringify(window.__calls)");run("uywClose()")
    # automatic installing keeps its own card
    run("(()=>{UI.updAuto=true;localStorage.removeItem('al-upd-later');UYW.closed=''})()");run("window.audiolabHost.updateReady('1.001','n')");pg.wait_for_timeout(300);res['auto-mode']=run(W)+' / card: '+str(run("!document.getElementById('updCard').hidden"));run("(()=>{UI.updAuto=false;clearInterval(UPD.autoT);document.getElementById('updCard').hidden=true})()")
    # the Updates window (Check for updates) has the logo
    run("delete window.audiolabDesktop");run("updOpen()");pg.wait_for_timeout(1200);res['updOpen-logo']=run("!!document.querySelector('#updDlg .updh .uywlogo img')");pg.locator('#updDlg .sheet').screenshot(path=f'{out}/updopen.png');run("updClose()")
    # browser with another icon picked in Settings
    run("(()=>{localStorage.setItem('audiolab-app-icon','blueprint');UYW.pic=null;UYW.closed='';localStorage.removeItem('al-upd-later')})()");run("window.audiolabHost.updateReady('1.002','n')");pg.wait_for_timeout(1200)
    res['picked-logo']=run("(()=>{const i=document.querySelector('#uywM .uywlogo img');return i.className+' '+i.getAttribute('src').slice(0,60)+' loaded:'+(i.naturalWidth>0)})()");pg.locator('#uywM .uyww').screenshot(path=f'{out}/picked.png');run("uywClose();localStorage.removeItem('audiolab-app-icon')")
    res['errors']=errs
    b.close()
print(json.dumps(res,indent=1))
