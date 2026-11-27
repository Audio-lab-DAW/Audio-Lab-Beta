"""RF1 inventory: loads index.html headless, dumps effects (FXDEF), instruments (PRESETS), MIDI effects, the About
'Under the hood' feature rows, and takes screenshots of the main views.
  python3 tools/feature-lab/rf1/inventory.py [repo dir] [out dir]"""
import sys,os,mimetypes,json
from playwright.sync_api import sync_playwright
ROOT=os.path.abspath(sys.argv[1] if len(sys.argv)>1 else '.');OUT=sys.argv[2] if len(sys.argv)>2 else 'tools/feature-lab/rf1/shots'
os.makedirs(OUT,exist_ok=True)
def serve(route):
    p=route.request.url.split('https://app.test/',1)[1].split('?')[0] or 'index.html'
    f=os.path.join(ROOT,p)
    if p.endswith('coi-serviceworker.js') or not os.path.isfile(f): return route.fulfill(status=404,body=b'')
    route.fulfill(status=200,body=open(f,'rb').read(),content_type=mimetypes.guess_type(f)[0] or 'application/octet-stream')
with sync_playwright() as p:
    b=p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
    c=b.new_context(viewport={'width':1500,'height':950},device_scale_factor=1);pg=c.new_page();errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e)[:300]));pg.route('https://app.test/**',serve)
    pg.add_init_script("localStorage.setItem('audiolab-ui',JSON.stringify(%s))"%json.dumps({'splash':False,'lat3':1}))
    pg.goto('https://app.test/index.html');pg.wait_for_function("()=>window.AudioLab&&window.AudioLab.version",timeout=60000);pg.wait_for_timeout(3000)
    pg.evaluate("()=>{const n=document.getElementById('liteNote');n&&n.remove()}")
    inv={'version':pg.evaluate("()=>AudioLab.version")}
    def run(js):
        return pg.evaluate("j=>{try{return AudioLab.run(j)}catch(e){return 'ERR '+e}}",js)
    inv['fx']=run("Object.entries(FXDEF).map(([k,v])=>k+': '+v.name+' ['+Object.keys(v.p||{}).join(',')+']')")
    inv['presets']=run("Object.entries(PRESETS).map(([k,v])=>k+': '+v.name+' ('+(v.cat||'')+') '+(v.desc||'').slice(0,90))")
    inv['midifx']=run("[...MIDIFX].map(k=>k+': '+((FXDEF[k]||{}).name||''))")
    inv['ND']=run("Object.keys(ND)")
    pg.screenshot(path=f'{OUT}/01_arrangement.png')
    run('showAbout()');pg.wait_for_timeout(1500)
    try: pg.click('#abMore');pg.wait_for_timeout(1200)
    except Exception as e: print('abMore',e)
    inv['about']=pg.evaluate("()=>[...document.querySelectorAll('#splash .abR')].map(r=>r.innerText.replace(/\\s+/g,' ').trim())")
    pg.screenshot(path=f'{OUT}/02_about.png');pg.keyboard.press('Escape');pg.wait_for_timeout(800)
    for i,(name,js) in enumerate([('mixer','openMixer()'),('settings',"openSettings('general')")]):
        r=run(js);pg.wait_for_timeout(1200);pg.screenshot(path=f'{OUT}/0{3+i}_{name}.png');print(name,r);pg.keyboard.press('Escape');pg.wait_for_timeout(600)
    inv['settingsTabs']=pg.evaluate("()=>[...document.querySelectorAll('[data-st],.stTab,.sttab')].map(e=>e.textContent.trim()).slice(0,40)")
    inv['errors']=errs
    json.dump(inv,open(f'{OUT}/../inventory.json','w'),indent=1)
    print(json.dumps({k:(v if not isinstance(v,list) else len(v)) for k,v in inv.items()}))
    b.close()
