"""Task ST-S3 (settings rebuild, step S3): what was out of sync is in sync.
Mono and L/R swap: Settings ticks repaint the master strip buttons and are exclusive as on the strip; the strip ticks Settings.
Follow: Settings shows all six ways of the menu (an older profile on 'lead' or 'edge' lights its card), the 'follow again' switch is shared
with the menu, the command refreshes an open Settings window. Visualizer: its header X and place select update Settings, Settings updates the header.
Older profile values load, search finds the moved words, dark and Light level, screenshots, no console errors.
  python3 tools/ui-tests/taskST_S3.py [repo dir] [out dir]"""
import sys,os,mimetypes,json
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
J=lambda pg,c:json.loads(R(pg,"JSON.stringify("+c+")"))
def ctx(b,lite,old):
    c=b.new_context(viewport={'width':1600,'height':1000});pg=c.new_page();errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e)[:300]));pg.on('console',lambda m:m.type=='error' and 'fetching the script' not in m.text and 'net::' not in m.text and errs.append('console '+m.text[:200]))
    pg.route('https://app.test/**',serve)
    u=dict(old,order=['arr','fx','tr','map'],splash=False,lat3=1,lite=lite,liteMan=lite)
    pg.add_init_script("if(!sessionStorage.getItem('t3')){sessionStorage.setItem('t3','1');localStorage.setItem('audiolab-ui',JSON.stringify(%s))}"%json.dumps(u))
    pg.goto('https://app.test/index.html');pg.wait_for_function("()=>window.AudioLab&&window.AudioLab.version",timeout=90000);pg.wait_for_timeout(3000)
    pg.evaluate("()=>{const n=document.getElementById('liteNote');n&&n.remove()}")
    return c,pg,errs
def tab(pg,t):R(pg,"openSettings('%s')"%t);pg.click('#setNav [data-tab=%s]'%t);pg.wait_for_timeout(400)
STRIP="(()=>{const o={};for(const b of document.querySelectorAll('#mixWin [data-mon]'))o[b.dataset.mon]=b.classList.contains('on');return o})()"
LIT="[...document.querySelectorAll('#setFollowC .on')].map(b=>b.dataset.fm)"
with sync_playwright() as p:
    b=p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
    for lite in (False,True):
        L='light' if lite else 'dark'
        old={'monoChk':True,'swapChk':False,'follow':True,'followMode':'lead','followResume':False,'viz':True,'vizDock':'bottom','mapZoom':'picture','ceil':-1}
        c,pg,errs=ctx(b,lite,old)
        ck(f'{L}: version',R(pg,"VERSION")=='0.236')
        ck(f'{L}: older profile values load',J(pg,"[UI.monoChk,UI.swapChk,UI.follow,UI.followMode,UI.followResume,UI.viz,UI.vizDock]")==[True,False,True,'lead',False,True,'bottom'])
        # A. Mono and swap
        R(pg,"openMixer()");pg.wait_for_timeout(1200)
        ck(f'{L}: strip shows the stored Mono',J(pg,STRIP).get('mono')==True,J(pg,STRIP))
        tab(pg,'dac')
        ck(f'{L}: Settings shows the stored Mono',J(pg,"[$('#monoChk').checked,$('#swapChk').checked]")==[True,False])
        pg.click('#monoChk');pg.wait_for_timeout(150)
        ck(f'{L}: untick Mono in Settings: strip button goes dark',J(pg,STRIP).get('mono')==False and R(pg,"UI.monoChk")==False,J(pg,STRIP))
        pg.click('#swapChk');pg.wait_for_timeout(150)
        ck(f'{L}: tick swap in Settings: strip L-R lights',J(pg,STRIP).get('swap')==True and R(pg,"UI.swapChk")==True)
        pg.click('#monoChk');pg.wait_for_timeout(150)
        ck(f'{L}: Mono in Settings clears swap, as on the strip',J(pg,"[UI.monoChk,UI.swapChk,$('#swapChk').checked]")==[True,False,False] and J(pg,STRIP)=={**J(pg,STRIP),'mono':True,'swap':False})
        ck(f'{L}: monitor gains follow (mono: LR and RL at half)',J(pg,"MON?MON.G.map(g=>+g.gain.value.toFixed(3)):null") in (None,[0.5,0.5,0.5,0.5]),J(pg,"MON?MON.G.map(g=>g.gain.value):null"))
        R(pg,"document.querySelector('#mixWin [data-mon=swap]').click()");pg.wait_for_timeout(200)
        ck(f'{L}: strip L-R ticks Settings and unticks Mono there',J(pg,"[$('#monoChk').checked,$('#swapChk').checked]")==[False,True])
        R(pg,"document.querySelector('#mixWin [data-mon=swap]').click()");pg.wait_for_timeout(150)
        ck(f'{L}: swap has a help text in the page',"'#swapChk':'Swap left and right|" in open(os.path.join(ROOT,'index.html'),encoding='utf-8').read())
        pg.locator('#set .sheet').screenshot(path=f'{OUT}/s3_dac_{L}.png')
        # B. Follow
        tab(pg,'nav')
        ck(f'{L}: six Follow cards in the menu order',J(pg,"[...$('#setFollowC').children].map(b=>b.dataset.fm)")==['center','stay','lead','page','edge','off'])
        ck(f'{L}: the stored Look ahead lights its card',J(pg,LIT)==['lead'])
        ck(f'{L}: every card has a tooltip',all(len(t)>25 for t in J(pg,"[...$('#setFollowC').children].map(b=>b.title)")))
        ck(f'{L}: follow again switch shows the stored off',R(pg,"$('#setFollowRes').checked")==False and len(R(pg,"$('#setFollowRes').closest('label').title"))>30)
        pg.click('#setFollowC [data-fm=edge]');pg.wait_for_timeout(100)
        ck(f'{L}: Push at the edge card sets the mode',J(pg,"[UI.follow,UI.followMode]")==[True,'edge'] and J(pg,LIT)==['edge'])
        pg.click('#setFollowRes');ck(f'{L}: follow again switch sets the value',R(pg,"UI.followResume")==True)
        pg.wait_for_timeout(200);pg.locator('#set .sheet').screenshot(path=f'{OUT}/s3_nav_{L}.png')
        R(pg,"SCM.get('follow').run()");pg.wait_for_timeout(100)
        ck(f'{L}: the Follow command refreshes Settings (off lit)',R(pg,"UI.follow")==False and J(pg,LIT)==['off'])
        R(pg,"SCM.get('follow').run()");pg.wait_for_timeout(100)
        ck(f'{L}: command again: back to Push at the edge',J(pg,LIT)==['edge'])
        R(pg,"followMenu(400,300)");pg.wait_for_timeout(200)
        clicked=pg.evaluate("()=>{const it=[...document.querySelectorAll('#ctxm *')].find(e=>e.children.length<4&&/Follow again 3 s/.test(e.textContent));if(!it)return false;it.click();return true}")
        pg.wait_for_timeout(150);pg.keyboard.press('Escape')
        ck(f'{L}: the menu switch refreshes Settings',clicked and R(pg,"UI.followResume")==False and R(pg,"$('#setFollowRes').checked")==False,clicked)
        R(pg,"followMenu(400,300)");pg.wait_for_timeout(200)
        clicked=pg.evaluate("()=>{const it=[...document.querySelectorAll('#ctxm *')].find(e=>e.children.length<4&&/^Look ahead/.test(e.textContent.trim()));if(!it)return false;it.click();return true}")
        pg.wait_for_timeout(150)
        ck(f'{L}: menu Look ahead lights the card',clicked and J(pg,LIT)==['lead'])
        pg.keyboard.press('Escape');pg.wait_for_timeout(100);R(pg,"(()=>{const m=document.getElementById('ctxm');if(m)m.classList.remove('on');try{closeMenu()}catch(e){}return 1})()");pg.wait_for_timeout(100)
        # C. Visualizer
        tab(pg,'layout')
        ck(f'{L}: Settings shows the visualizer on',J(pg,"[$('#layViz').checked,$('#layVizDock').value]")==[True,'bottom'])
        R(pg,"(()=>{const s=VZ.el.querySelector('.vzdock');s.value='right';s.dispatchEvent(new Event('change',{bubbles:true}));return 1})()");pg.wait_for_timeout(300)
        ck(f'{L}: header place select updates Settings',R(pg,"$('#layVizDock').value")=='right')
        R(pg,"(()=>{const s=$('#layVizDock');s.value='left';s.dispatchEvent(new Event('change',{bubbles:true}));return 1})()");pg.wait_for_timeout(300)
        ck(f'{L}: Settings place updates the header select',R(pg,"VZ.el.querySelector('.vzdock').value")=='left')
        R(pg,"VZ.el.querySelector('.vzx').click()");pg.wait_for_timeout(300)
        ck(f'{L}: header X unticks Settings',R(pg,"UI.viz")==False and R(pg,"$('#layViz').checked")==False and R(pg,"$('#layVizDock').disabled")==True)
        pg.locator('#set .sheet').screenshot(path=f'{OUT}/s3_layout_{L}.png')
        # D. search
        for q,exp in (('look ahead','Zoom and playhead'),('push at the edge','Zoom and playhead'),('follow again','Zoom and playhead'),('swap','Interface and DAC'),('mono','Interface and DAC')):
            pg.evaluate("q=>{const e=document.getElementById('setQ');e.value=q;e.dispatchEvent(new Event('input'))}",q);pg.wait_for_timeout(250)
            h=pg.evaluate("()=>[...document.querySelectorAll('#setQR button')].map(b=>b.textContent)")
            ck(f'{L}: search "{q}" finds {exp}',any(exp in t for t in h),h[:4])
        pg.evaluate("()=>{const e=document.getElementById('setQ');e.value='';e.dispatchEvent(new Event('input'))}")
        # E. stored after restart
        R(pg,"(()=>{try{saveUINow()}catch(e){}return 1})()");pg.wait_for_timeout(500);pg.reload();pg.wait_for_function("()=>window.AudioLab&&window.AudioLab.version",timeout=90000);pg.wait_for_timeout(2500)
        ck(f'{L}: after a restart the choices stay',J(pg,"[UI.monoChk,UI.swapChk,UI.followMode,UI.followResume,UI.viz,UI.vizDock]")==[False,False,'lead',False,False,'left'],J(pg,"[UI.monoChk,UI.swapChk,UI.followMode,UI.followResume,UI.viz,UI.vizDock]"))
        ck(f'{L}: no console errors',not errs,errs)
        c.close()
    b.close()
print(f'{N[1]}/{N[0]} checks pass');sys.exit(1 if FAIL else 0)
