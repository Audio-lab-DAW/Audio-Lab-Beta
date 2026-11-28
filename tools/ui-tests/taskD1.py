# task D1 (v0.222): "Flat bars" (design 7) is the standard fader and meter design again; the one-time move to "Flat bars 2" (22) is undone once.
#   python3 tools/ui-tests/taskD1.py index.html [outdir]
# Each case starts the app with its own saved settings (localStorage 'audiolab-ui') and reads the design in use after the start and after a second start.
import sys,os,json
import sys as _ws_sys, os as _ws_os; _ws_sys.path.insert(0, _ws_os.path.join(_ws_os.path.dirname(_ws_os.path.abspath(__file__)), '../test-songs')); from alsong import alsong  # task WS-F: the test songs
from playwright.sync_api import sync_playwright
f=sys.argv[1] if len(sys.argv)>1 else 'index.html';out=sys.argv[2] if len(sys.argv)>2 else '.'
src=open(f,encoding='utf-8').read()
fails=[]
def ck(name,ok,extra=''):
    print(('PASS ' if ok else 'FAIL ')+name,extra)
    if not ok:fails.append(name)
STATE="JSON.stringify({o:mxsO().fd,saved:(UI.mxs||{}).fd===undefined?null:UI.mxs.fd,fd7:UI.fd7||0,fd22:UI.fd22||0,cls:[...document.getElementById('mixWin').classList].filter(c=>/^fd\\d+$/.test(c)),name:FDS[mxsO().fd-1].n,on:[...document.querySelectorAll('[data-fd].on')].map(e=>+e.dataset.fd).filter((v,i,a)=>a.indexOf(v)===i),hfd:document.getElementById('hdrin').classList.contains('hfd'),theme:(THEMES.find(t=>t.id==='audiolab')||{}).fd,ls:JSON.parse(localStorage.getItem('audiolab-ui')||'{}')})"
def case(p,label,ui,shot=None):
    b=p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required']);cx=b.new_context(viewport={'width':2000,'height':1100});pg=cx.new_page();errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e)[:400]));pg.on('console',lambda m:errs.append('C:'+m.text[:300]) if m.type=='error' and 'net::' not in m.text and '404' not in m.text and 'fetching the script' not in m.text else None)
    pg.route('https://app.test/**',alsong(lambda r:r.fulfill(status=200,content_type='text/html',body=src.encode()) if r.request.url.endswith('.html') else r.fulfill(status=404,body=b'')))
    # seed the saved settings once (first load only), through a blank page on the same origin
    pg.route('https://app.test/seed',lambda r:r.fulfill(status=200,content_type='text/html',body=b'<html></html>'))
    pg.goto('https://app.test/seed')
    if ui is not None:pg.evaluate("u=>localStorage.setItem('audiolab-ui',u)",json.dumps(dict(ui,order=['arr','fx','tr','map'])))   # the app only reads saved settings that have the panel order
    R=lambda c:pg.evaluate("c=>window.AudioLab.run(c)",c)
    def load():
        pg.goto('https://app.test/index.html');pg.wait_for_timeout(8000)
        R("(()=>{const c=document.getElementById('liteNote');if(c)c.remove();const s=document.getElementById('splash');if(s)s.remove();openMixer()})()");pg.wait_for_timeout(1000)
        return json.loads(R(STATE))
    st=load();print(label,'->',{k:st[k] for k in('o','saved','fd7','fd22','cls','name','on','hfd')},'stored',(st['ls'].get('mxs') or {}).get('fd'),st['ls'].get('fd7'))
    if shot:
        R("(()=>{const w=document.getElementById('mixWin');w.style.left='10px';w.style.width='1900px';mxFit();renderMixer()})()");pg.wait_for_timeout(800)
        pg.screenshot(path=os.path.join(out,shot))
    return b,pg,R,load,st,errs
with sync_playwright() as p:
    # 1. fresh profile (nothing saved at all)
    b,pg,R,load,st,errs=case(p,'fresh',None,'d1_fresh.png')
    print('version',R("VERSION"))
    ck('fresh profile: Flat bars (7) in use',st['o']==7 and st['name']=='Flat bars' and st['cls']==['fd7'],st['name'])
    ck('fresh profile: nothing forced into the saved settings',st['saved'] is None and st['fd7']==1)
    ck('AudioLab theme sets Flat bars (7)',st['theme']==7)
    ck('the designs are all still there (22, Flat bars 2 last)',R("FDS.length")==22 and R("FDS[21].n")=='Flat bars 2' and R("FDS[6].n")=='Flat bars')
    # a deliberate choice of Flat bars 2 after the step is kept over a restart
    pg.locator('#mxSetB').click();pg.wait_for_timeout(500)
    ck('fresh profile: the design button in the mixer settings names 7 Flat bars',' '.join(pg.locator('#mxsPop .fdsel .fdselt b').inner_text().split())=='7 Flat bars',pg.locator('#mxsPop .fdsel .fdselt b').inner_text())
    pg.locator('#mxsPop .fdsel').click();pg.wait_for_timeout(500)
    ck('fresh profile: the design list marks 7',json.loads(R(STATE))['on']==[7],json.loads(R(STATE))['on'])
    pg.screenshot(path=os.path.join(out,'d1_picker.png'))
    pg.locator('#fdPop [data-fd="22"]').click();pg.wait_for_timeout(500)
    ck('picking Flat bars 2 by hand works',json.loads(R(STATE))['o']==22)
    st=load();ck('deliberate Flat bars 2 after this version: kept after a restart',st['o']==22 and st['cls']==['fd22'] and st['fd7']==1,st['name'])
    ck('fresh: no console errors',errs==[],errs);b.close()
    # 2. profile as the migration left it (fd22 flag set, Flat bars 2 saved)
    b,pg,R,load,st,errs=case(p,'migrated',{'splash':False,'lat3':1,'fd22':1,'mxs':{'fd':22,'w':110}},'d1_migrated.png')
    ck('migrated profile: back to Flat bars (7)',st['o']==7 and st['saved']==7 and st['cls']==['fd7'] and st['fd7']==2,st['name'])
    ck('migrated profile: the change is saved, other mixer settings kept',(st['ls'].get('mxs') or {}).get('fd')==7 and st['ls']['mxs'].get('w')==110 and st['ls'].get('fd7')==2)
    ck('migrated profile: track headers follow (header fader look on)',st['hfd'] is True)
    st=load();ck('migrated profile: still Flat bars after a second start',st['o']==7 and st['fd7']==2)
    R("mxsSet('fd',22)");pg.wait_for_timeout(300);st=load()
    ck('migrated profile: Flat bars 2 picked again afterwards is kept',st['o']==22 and st['saved']==22,st['name'])
    ck('migrated: no console errors',errs==[],errs);b.close()
    # 3. profile from v0.221 that never touched the design (flag set, nothing saved): gets the new standard
    b,pg,R,load,st,errs=case(p,'v0.221 untouched',{'splash':False,'lat3':1,'fd22':1})
    ck('v0.221 profile with no saved design: Flat bars (7)',st['o']==7 and st['saved'] is None and st['fd7']==1,st['name']);ck('untouched: no console errors',errs==[],errs);b.close()
    # 4. other saved designs are left alone
    b,pg,R,load,st,errs=case(p,'LED ladder',{'splash':False,'lat3':1,'fd22':1,'mxs':{'fd':3}})
    ck('another saved design (3) is kept',st['o']==3 and st['saved']==3 and st['fd7']==1,st['name']);b.close()
    # 5. profile older than the migration (no flag) with Classic saved: no longer moved to Flat bars 2
    b,pg,R,load,st,errs=case(p,'old Classic',{'splash':False,'lat3':1,'mxs':{'fd':1}})
    ck('old profile with Classic saved: stays Classic',st['o']==1 and st['saved']==1 and st['fd22']==1,st['name']);b.close()
    b,pg,R,load,st,errs=case(p,'old Flat bars',{'splash':False,'lat3':1,'mxs':{'fd':7}})
    ck('old profile with Flat bars saved: stays Flat bars',st['o']==7 and st['saved']==7,st['name']);ck('old: no console errors',errs==[],errs);b.close()
print('FAILED:',fails) if fails else print('ALL PASS')
sys.exit(1 if fails else 0)
