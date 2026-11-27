"""Task ST-S9 (settings rebuild, step S9): the help line at the foot of the Settings window (D4c). Pointing at a setting shows at once what it
does, its default and where it is kept; Tab does the same; leaving the rows brings back the idle line; every row of the settings table has a
help line and every visible control on every page has something to say (fails when a control has none); search reads the new lines; an older
profile still loads; ST_HOOKS.helpFor works for lane F; dark and Light level; no console errors.
  python3 tools/ui-tests/taskST_S9.py [repo dir] [out dir]"""
import sys,os,mimetypes,json
from playwright.sync_api import sync_playwright
ROOT=os.path.abspath(sys.argv[1] if len(sys.argv)>1 else '.');OUT=sys.argv[2] if len(sys.argv)>2 else '.';os.makedirs(OUT,exist_ok=True)
N=[0,0];FAIL=[]
def ck(name,ok,info=''):
    N[0]+=1
    if ok:N[1]+=1
    else:FAIL.append(name);print('  FAIL',name,str(info)[:700])
def serve(route):
    p=route.request.url.split('https://app.test/',1)[1].split('?')[0] or 'index.html';f=os.path.join(ROOT,p)
    if p.endswith('coi-serviceworker.js') or not os.path.isfile(f): return route.fulfill(status=404,body=b'')
    route.fulfill(status=200,body=open(f,'rb').read(),content_type='text/html' if f.endswith('.html') else (mimetypes.guess_type(f)[0] or 'application/octet-stream'))
R=lambda pg,c:pg.evaluate("c=>window.AudioLab.run(c)",c)
J=lambda pg,c:json.loads(R(pg,"JSON.stringify("+c+")"))
HL=lambda pg:pg.evaluate("()=>{const h=document.getElementById('st9Help');return h?{t:h.textContent,on:!!h.dataset.on,vis:h.offsetWidth>0}:null}")
with sync_playwright() as p:
    b=p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
    for lite in (False,True):
        L='light' if lite else 'dark'
        c=b.new_context(viewport={'width':1600,'height':1000});pg=c.new_page();errs=[]
        pg.on('pageerror',lambda e:errs.append(str(e)[:300]));pg.on('console',lambda m:m.type=='error' and 'fetching the script' not in m.text and 'net::' not in m.text and 'icons.json' not in m.text and errs.append('console '+m.text[:200]))
        pg.route('https://app.test/**',serve)
        u=dict(order=['arr','fx','tr','map'],splash=False,lat3=1,lite=lite,liteMan=lite,chase=False,asMin=5,keepAwake=True)
        pg.add_init_script("if(!sessionStorage.getItem('t9')){sessionStorage.setItem('t9','1');localStorage.setItem('audiolab-ui',JSON.stringify(%s))}"%json.dumps(u))
        pg.goto('https://app.test/index.html');pg.wait_for_function("()=>window.AudioLab&&window.AudioLab.version",timeout=90000);pg.wait_for_timeout(2500)
        pg.evaluate("()=>{const n=document.getElementById('liteNote');n&&n.remove()}")
        ck(f'{L}: version',float(R(pg,"VERSION"))>=0.278)
        R(pg,"openSettings('general')");pg.wait_for_timeout(500)
        st=J(pg,"{chase:UI.chase,as:UI.asMin,ka:UI.keepAwake}")
        ck(f'{L}: an older profile still loads',st=={'chase':False,'as':5,'ka':True},st)
        h=HL(pg);ck(f'{L}: the help line sits in the foot with its idle text',h and h['vis'] and not h['on'] and 'Point at a setting' in h['t'],h)
        ck(f'{L}: "Changes apply right away" is kept in the idle line',h and 'Changes apply right away' in h['t'],h)
        miss=J(pg,"STT.filter(r=>!ST9.clean(r.h)).map(r=>r.id)");ck(f'{L}: every row of the settings table has a help line',miss==[],miss)
        # every visible control on every page has something to say
        pages=J(pg,"ST5P.map(p=>p[0])");bad=[];total=0
        for t in pages:
            R(pg,"ST5.show('%s')"%t);pg.wait_for_timeout(200)
            res=J(pg,"""(()=>{const out=[];let n=0;for(const e of document.querySelectorAll('#setBody>section[data-page="%s"] button,#setBody>section[data-page="%s"] input,#setBody>section[data-page="%s"] select,#setBody>section[data-page="%s"] textarea')){
              const vis=e.offsetParent!==null||(e.type==='checkbox'&&e.closest('label')&&e.closest('label').offsetParent!==null);if(!vis)continue;n++;const x=ST_HOOKS.helpFor(e);
              if(!x||!x.text||x.text.length<12)out.push([e.id,e.tagName,(e.getAttribute('aria-label')||e.textContent||'').trim().slice(0,40),Object.keys(e.dataset).join(',')])}return{n,out}})()"""%(t,t,t,t))
            total+=res['n'];bad+=[[t]+x for x in res['out']]
        ck(f'{L}: every visible control in Settings has a help line ({total} checked)',total>150 and not bad,bad[:20])
        # pointing shows it at once, with default and scope
        R(pg,"ST5.show('dac')");pg.wait_for_timeout(300)
        pg.hover('#ceilSel');h=HL(pg)
        ck(f'{L}: pointing at a setting shows its line, default and scope at once',h['on'] and 'Headphone safety ceiling' in h['t'] and 'Default: ' in h['t'] and 'Belongs to this computer' in h['t'],h)
        pg.locator('#set .setw').screenshot(path=f'{OUT}/s9_dac_ceiling_{L}.png')
        R(pg,"ST5.show('editing')");pg.wait_for_timeout(200)
        pg.hover('#chaseChk');h=HL(pg)
        ck(f'{L}: a taste setting says it is the same in every project',h['on'] and 'already sounding' in h['t'] and 'Default: on' in h['t'] and 'The same in every project' in h['t'],h)
        R(pg,"ST5.show('files')");pg.wait_for_timeout(300)
        pg.hover('#st8Lufs');h=HL(pg);ck(f'{L}: a song setting says it is kept with this song',h['on'] and 'Kept with this song' in h['t'],h)
        pg.locator('#set .setw').screenshot(path=f'{OUT}/s9_project_lufs_{L}.png')
        pg.hover('#pfSaveAs');h=HL(pg);ck(f'{L}: a button gets its line too',h['on'] and 'new .audiolab file' in h['t'],h)
        pg.hover('#setNav [data-tab="dac"]');h=HL(pg);ck(f'{L}: the sidebar pages speak too',h['on'] and len(h['t'])>5,h)
        pg.mouse.move(5,5);pg.wait_for_timeout(100);h=HL(pg);ck(f'{L}: leaving the window brings back the idle line',not h['on'] and 'Point at a setting' in h['t'],h)
        # keyboard
        R(pg,"ST5.show('general')");pg.wait_for_timeout(200)
        R(pg,"document.getElementById('setTips').focus();0");pg.wait_for_timeout(100);h=HL(pg)
        ck(f'{L}: moving to a setting with the keyboard shows its line',h['on'] and 'explanation' in h['t'],h)
        ck(f'{L}: the focused control is described by the line',R(pg,"document.getElementById('setTips').getAttribute('aria-describedby')")=='st9Help')
        pg.keyboard.press('Tab');pg.wait_for_timeout(100);h2=HL(pg);ck(f'{L}: Tab moves the line on',h2['t']!=h['t'],[h,h2])
        pg.locator('#set .setw').screenshot(path=f'{OUT}/s9_general_tab_{L}.png')
        # search reads the new lines
        r=pg.evaluate("q=>{const e=document.getElementById('setQ');e.focus();e.value=q;e.dispatchEvent(new Event('input'));return[...document.querySelectorAll('#setQR button')].map(b=>b.querySelector('b').textContent)}",'first note is not cut off')
        ck(f'{L}: search finds a setting by its new help line',any('awake' in x.lower() for x in r),r)
        pg.evaluate("()=>{const e=document.getElementById('setQ');e.value='';e.dispatchEvent(new Event('input'))}")
        x=J(pg,"ST_HOOKS.helpFor(document.getElementById('bufSel'))");ck(f'{L}: ST_HOOKS.helpFor gives label, text, default and scope',x and x['label']=='Buffer size' and x['text'] and x['scope'],x)
        R(pg,"closeSet();0");pg.wait_for_timeout(200)
        ck(f'{L}: no console errors',not errs,errs)
        c.close()
    b.close()
print(f'{N[1]}/{N[0]} passed');sys.exit(1 if FAIL else 0)
