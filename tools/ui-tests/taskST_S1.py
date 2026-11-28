"""Task ST-S1 (settings rebuild, step S1): no copies inside Settings.
An older profile (v0.229 keys: UI.dac, UI.mtr, mixer settings, buffer, output) is loaded and must come through unchanged.
Checks: the Mixer block in Settings has no Level meters list, the Level meters block exists once and works, the gear popover keeps its list;
no hidden DAC profile select; one Audio devices button in Settings, the DAC page's 'Change output' opens Audio system;
Export audio has no Save, Save as, Open and links to Project file, which keeps all three; search still finds the moved names;
no console errors. Normal and Light level, screenshots to the out dir.
  python3 tools/ui-tests/taskST_S1.py [repo dir] [out dir]"""
import sys,os,mimetypes,json
import sys as _ws_sys, os as _ws_os; _ws_sys.path.insert(0, _ws_os.path.join(_ws_os.path.dirname(_ws_os.path.abspath(__file__)), '../test-songs')); from alsong import alsong  # task WS-F: the test songs
from playwright.sync_api import sync_playwright
ROOT=os.path.abspath(sys.argv[1] if len(sys.argv)>1 else '.');OUT=sys.argv[2] if len(sys.argv)>2 else '.';os.makedirs(OUT,exist_ok=True)
N=[0,0];FAIL=[]
def ck(name,ok,info=''):
    N[0]+=1
    if ok:N[1]+=1
    else:FAIL.append(name);print('  FAIL',name,info)
def serve(route):
    p=route.request.url.split('https://app.test/',1)[1].split('?')[0] or 'index.html';f=os.path.join(ROOT,p)
    if p.endswith('coi-serviceworker.js') or not os.path.isfile(f): return route.fulfill(status=404,body=b'')
    route.fulfill(status=200,body=open(f,'rb').read(),content_type=mimetypes.guess_type(f)[0] or 'application/octet-stream')
R=lambda pg,c:pg.evaluate("c=>window.AudioLab.run(c)",c)
OLD={'order':['arr','fx','tr','map'],'splash':False,'lat3':1,'dac':'gryphon','mtr':{'spd':'smooth','alg':'rms','hold':'3','col':'heat'},'mxs':{'w':120,'fd':3},'buf':-1,'recOff':7,'keepAwake':True,'autosave':True,'asMin':5}
def page(b,lite):
    c=b.new_context(viewport={'width':1600,'height':1000},device_scale_factor=1);pg=c.new_page();errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e)[:300]));pg.on('console',lambda m:m.type=='error' and 'fetching the script' not in m.text and 'net::' not in m.text and errs.append('console '+m.text[:200]))
    pg.route('https://app.test/**',alsong(serve))
    o=dict(OLD,lite=lite,liteMan=lite);pg.add_init_script("localStorage.setItem('audiolab-ui',JSON.stringify(%s))"%json.dumps(o))
    pg.goto('https://app.test/index.html');pg.wait_for_function("()=>window.AudioLab&&window.AudioLab.version",timeout=90000);pg.wait_for_timeout(3000)
    pg.evaluate("()=>{const n=document.getElementById('liteNote');n&&n.remove()}")
    return c,pg,errs
def tab(pg):return pg.evaluate("()=>{const b=document.querySelector('#setNav [data-tab].on');return b?b.dataset.tab:'?'}")
def search(pg,q):
    pg.evaluate("q=>{const i=document.getElementById('setQ');i.focus();i.value=q;i.dispatchEvent(new Event('input'))}",q);pg.wait_for_timeout(150)
    h=pg.evaluate("()=>[...document.querySelectorAll('#setQR button')].map(b=>b.querySelector('b').textContent+' | '+b.querySelector('small').textContent)")
    pg.evaluate("()=>{const i=document.getElementById('setQ');i.value='';i.dispatchEvent(new Event('input'));i.blur()}");return h
with sync_playwright() as p:
    b=p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
    for lite in (False,True):
        L='light' if lite else 'dark';cx,pg,errs=page(b,lite)
        st=json.loads(R(pg,"JSON.stringify({dac:UI.dac,mtr:mtrO(),w:mxsO().w,fd:mxsO().fd,buf:UI.buf,recOff:UI.recOff,ka:UI.keepAwake,asMin:UI.asMin,lite:!!UI.lite})"))
        ck(f'{L}: old profile kept (dac, meters, mixer, buffer, offset, keep awake, autosave)',st['dac']=='gryphon' and st['mtr']['spd']=='smooth' and st['mtr']['alg']=='rms' and st['mtr']['hold']=='3' and st['mtr']['col']=='heat' and st['w']==120 and st['fd']==3 and st['buf']==-1 and st['recOff']==7 and st['ka'] is True and st['asMin']==5,st)
        ck(f'{L}: Light level as asked',st['lite']==lite,st)
        # 1. level meters once
        R(pg,"openSettings(typeof ST5==='object'?'mixer':'layout')");pg.wait_for_timeout(700)  # v0.250 (ST-S5): Mixer and meters has its own page
        g=pg.evaluate("""()=>({set:document.querySelectorAll('#mxsSet [data-mxm]').length,setH5:[...document.querySelectorAll('#mxsSet h5')].map(h=>h.textContent),
          mtr:document.querySelectorAll('#setBody #mtrSet').length,mtrH4:[...document.querySelectorAll('#setBody>section:not([hidden]) h4')].filter(h=>h.textContent.trim()==='Level meters').length,
          cols:[...document.querySelectorAll('#mtrSet .mgcol h5')].map(h=>h.textContent.trim()),on:[...document.querySelectorAll('#mtrSet [data-mset]')].map(m=>{const o=m.querySelector('.on');return m.dataset.mset+'='+(o?o.dataset.v:'-')})})""")
        ck(f'{L}: Settings Mixer block has no Level meters list',g['set']==0 and 'Level meters' not in g['setH5'],g)
        ck(f'{L}: one Level meters block with its four columns',g['mtr']==1 and g['mtrH4']==1 and len(g['cols'])==4,g)
        ck(f'{L}: Level meters block shows the stored choices',sorted(g['on'])==sorted(['spd=smooth','alg=rms','hold=3','col=heat']),g['on'])
        pg.evaluate("()=>{const e=document.getElementById('mxsSet');e.scrollIntoView({block:'start'})}");pg.wait_for_timeout(300)
        pg.locator('#set .sheet').screenshot(path=f'{OUT}/s1_mixer_{L}.png')
        pg.evaluate("()=>{document.getElementById('mtrSet').scrollIntoView({block:'center'})}");pg.wait_for_timeout(200)
        pg.click('#mtrSet [data-mset=spd] [data-v=instant]');pg.wait_for_timeout(200)
        ck(f'{L}: the Level meters block still changes the setting',R(pg,'mtrO().spd')=='instant')
        R(pg,"UI.mtr=Object.assign({},UI.mtr,{spd:'smooth'});saveUI();mtrUI&&mtrUI()")
        # popover keeps its short list
        R(pg,"closeSet()");pg.wait_for_timeout(200)
        R(pg,'openMixer()');pg.wait_for_timeout(600)
        R(pg,"(()=>{const p=document.getElementById('mxsPop');if(!p||p.hidden)mxsPop();return 1})()");pg.wait_for_timeout(300)
        pp=pg.evaluate("()=>{const p=document.getElementById('mxsPop');return p?[p.querySelectorAll('[data-mxm]').length,p.querySelector('[data-mxm=spd]')&&p.querySelector('[data-mxm=spd]').value]:null}")
        ck(f'{L}: the gear popover keeps its four Level meters selects, in sync',pp and pp[0]==4 and pp[1]=='smooth',pp)
        R(pg,"(()=>{const p=document.getElementById('mxsPop');if(p)p.hidden=true;return 1})()")
        # 2. hidden DAC select gone, profile kept
        R(pg,"openSettings('dac')");pg.wait_for_timeout(800)
        d=pg.evaluate("()=>({sel:!!document.getElementById('dacSel'),card:!!document.getElementById('dacCard'),hid:[...document.querySelectorAll('#setBody section[data-page=dac] [hidden]')].filter(e=>e.querySelector('select')).length,prof:(document.getElementById('ifdProfSel')||{}).value,btn:(()=>{const x=document.getElementById('ifdDevs');return x?[x.textContent,x.dataset.pmgo,x.title]:null})()})")
        ck(f'{L}: no hidden old Profile select or card',not d['sel'] and not d['card'],d)
        ck(f'{L}: Device profile still shows the stored Gryphon',d['prof']=='gryphon',d)
        ck(f'{L}: DAC page button is a link to Audio system, with a tooltip',d['btn'] and d['btn'][0]=='Change output' and d['btn'][1]=='audio' and len(d['btn'][2])>20,d['btn'])
        pg.locator('#set .sheet').screenshot(path=f'{OUT}/s1_dac_{L}.png')
        pg.click('#ifdDevs');pg.wait_for_timeout(400)
        ck(f'{L}: Change output opens Audio system with the one Audio devices button',tab(pg)=='audio' and pg.evaluate("()=>!!document.getElementById('findDev').offsetParent"),tab(pg))
        ck(f'{L}: one Audio devices button in Settings',pg.evaluate("()=>[...document.querySelectorAll('#setBody button')].filter(b=>b.textContent.trim()==='Audio devices').length")==1)
        pg.click('#findDev');pg.wait_for_timeout(700)
        ck(f'{L}: that button still opens the Audio devices window',pg.evaluate("()=>{const w=document.getElementById('audWin');return !!w&&!w.hidden&&w.getBoundingClientRect().width>100}"))
        R(pg,"(()=>{const w=document.getElementById('audWin');if(w){const x=w.querySelector('.fwc,[data-fwc],.fwclose');if(x)x.click();else w.remove()}return 1})()")
        # 3. Export audio: no file buttons, link to Project file
        R(pg,"openSettings('export')");pg.wait_for_timeout(500)
        e=pg.evaluate("()=>{const s=document.querySelector('#setBody section[data-page=export]');const l=s.querySelector('.pmlink button[data-pmgo=files]');return{pf:s.querySelectorAll('.pfbtns,[data-pf]').length,link:!!l,tip:l?l.title:'',ptip:l?l.closest('p').title:''}}")
        ck(f'{L}: Export audio has no Save, Save as, Open',e['pf']==0,e)
        ck(f'{L}: Export audio links to Project file, with tooltips',e['link'] and len(e['tip'])>10 and len(e['ptip'])>10,e)
        pg.locator('#set .sheet').screenshot(path=f'{OUT}/s1_export_{L}.png')
        pg.click('#setBody section[data-page=export] .pmlink button');pg.wait_for_timeout(400)
        ck(f'{L}: the link opens Project file with Save, Save as and Open',tab(pg)=='files' and pg.evaluate("()=>['pfSave','pfSaveAs','pfOpen'].every(i=>!!document.getElementById(i).offsetParent)"),tab(pg))
        ck(f'{L}: Save, Save as, Open appear once in Settings',pg.evaluate("()=>[...document.querySelectorAll('#setBody .pfbtns button')].filter(b=>/^(Save|Save as|Open)/.test(b.textContent.trim())&&!/template/.test(b.textContent)).length")==3)
        # 4. search still finds the moved names
        for q,want in [('peak hold','Interface'),('speed','Interface'),('level meters','Interface'),('audio devices','Audio'),('change output','Interface and DAC'),('profile','Interface and DAC'),('save as','Project'),('open','Project'),('gryphon','Interface and DAC')]:
            h=search(pg,q);W2={'Interface':'Mixer and meters','Interface and DAC':'DAC and audio interface'}.get(want,'@');ck(f'{L}: search "{q}" finds it ({want})',any(want.lower() in x.lower() or W2.lower() in x.lower() for x in h),h[:4])  # v0.250 (ST-S5): new page names
        # 5. errors
        ck(f'{L}: no console errors',not errs,errs[:3])
        cx.close()
    b.close()
print(f'{N[1]}/{N[0]} checks passed');sys.exit(1 if FAIL else 0)
