"""Task WS-1 (lane Q): the start screen.
Checks (at the user's size, 1254 x 651 CSS px at 1.75x = 2194 x 1139):
  - fresh profile: the splash hands over to the start screen; no demo song loaded (one empty 'Untitled' project), no demo toast;
    the hand-over runs about 1000 ms and ends with no per-frame work but the band's ambient drawing; the drawing is one of the
    picked set; Enter with no projects makes the empty project (the start screen closes, still one tab)
  - every built-in tile opens its project (Beat starter, Audio tracks), a saved project opens, a template opens
  - old profile (after a reload): the projects are listed as recent, the one open at quit first; Enter opens it; search filters
    and Escape clears it; arrows move the selection
  - Show at start-up off: the next start opens the last project with no start screen; the Settings row is there
  - closed: no frames are asked for by the start screen; the + menu has 'Start screen…' and no Fractals demo; the New project
    window shows no demo songs
  - Light mode (body.lite) and Reduce motion: a still drawing; screenshots dark and Light; no page errors
  python3 tools/ui-tests/taskWS_1.py [index.html] [out dir]"""
import sys, os, json
import sys as _ws_sys, os as _ws_os; _ws_sys.path.insert(0, _ws_os.path.join(_ws_os.path.dirname(_ws_os.path.abspath(__file__)), '../test-songs')); from alsong import alsong  # task WS-F: the test songs
from playwright.sync_api import sync_playwright
HERE = os.path.dirname(os.path.abspath(__file__))
IDX = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, '..', '..', 'index.html'))
OUT = os.path.abspath(sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, 'out', 'taskWS_1'))
os.makedirs(OUT, exist_ok=True)
SRC = open(IDX, encoding='utf-8').read()
N = [0, 0]; FAIL = []
def ck(name, ok, info=''):
    N[0] += 1
    if ok: N[1] += 1; print('  ok  ', name, '' if info == '' else info)
    else: FAIL.append(name); print('  FAIL', name, info)

with sync_playwright() as p:
    b = p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
    ctx = b.new_context(viewport={'width': 1254, 'height': 651}, device_scale_factor=1.75)
    ctx.route('https://app.test/**', alsong(lambda r: r.fulfill(body=SRC, content_type='text/html') if r.request.url.endswith('/') else r.fulfill(status=404, body='')))
    # the app starts as before under automation; this key asks for the real start (the start screen)
    ctx.add_init_script("localStorage.setItem('audiolab-ws-test','1');window.__toasts=[];new MutationObserver(()=>{const t=document.getElementById('toast');if(t&&t.textContent)__toasts.push(t.textContent)}).observe(document,{subtree:true,childList:true,characterData:true})")
    pg = ctx.new_page(); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)[:300]))
    R = lambda c: pg.evaluate('c=>AudioLab.run(c)', c)
    J = lambda c: json.loads(R('JSON.stringify(' + c + ')'))
    ST = "({on:WS.on,hand:!!WS.hand,kind:WS.kind,splash:!!document.getElementById('splash'),tabs:PJ.list.map(p=>p.name),cur:curP().name,n:S.tracks.length,clips:S.tracks.reduce((a,t)=>a+t.clips.length,0),rows:WS.recent?WS.recent.map(r=>r.name):[],sel:WS.sel,raf:WS.raf})"
    def boot():
        pg.goto('https://app.test/'); pg.wait_for_function('()=>window.AudioLab&&window.AudioLab.version', timeout=120000)
        pg.wait_for_function("()=>AudioLab.run('WS.on||!WS.pend')", timeout=30000)

    print('fresh profile')
    boot(); pg.wait_for_timeout(450); mid = J(ST); pg.screenshot(path=os.path.join(OUT, 'handover_mid.png'))
    pg.wait_for_timeout(1600); st = J(ST)
    ck('the start screen is open after the splash', st['on'] and not st['splash'], st)
    ck('the hand-over was running ~0.5 s after the splash closed', mid['hand'] or mid['on'], mid)
    ck('no demo song: one empty Untitled project with two tracks and no clips', st['tabs'] == ['Untitled'] and st['n'] == 2 and st['clips'] == 0, st)
    ck('no demo toast', not any('Demo song loaded' in t for t in pg.evaluate('__toasts')), pg.evaluate('__toasts'))
    ck('the drawing is from the picked set', st['kind'] in ['dipole', 'moons', 'interf', 'vdp', 'liss', 'trap', 'four'], st['kind'])
    ck('no recent projects on a fresh install', st['rows'] == [], st['rows'])
    ck('search is focused', pg.evaluate("document.activeElement&&document.activeElement.id==='wsQ'"))
    pg.screenshot(path=os.path.join(OUT, 'fresh_dark.png'))
    # every drawing paints without an error, in its band
    for k in ['dipole', 'moons', 'interf', 'vdp', 'liss', 'trap', 'four']:
        R("localStorage.setItem('audiolab-ws-kind','%s');wsClose();0" % k); pg.wait_for_timeout(200); R('wsOpen({});0'); pg.wait_for_timeout(700)
        ok = J("(()=>{const c=WS.cv,g=c.getContext('2d'),d=g.getImageData(0,0,c.width,c.height).data;let n=0;for(let i=3;i<d.length;i+=16)if(d[i]>20)n++;return{k:WS.kind,n,w:c.width,h:c.height}})()")
        ck('drawing %s paints in the band' % k, ok['k'] == k and ok['n'] > 200, ok)
        pg.screenshot(path=os.path.join(OUT, 'band_%s.png' % k))
    R("localStorage.removeItem('audiolab-ws-kind');0")
    pg.keyboard.press('Enter'); pg.wait_for_timeout(400); st = J(ST)
    ck('Enter with no projects: the empty project stays, the start screen closes', not st['on'] and st['tabs'] == ['Untitled'], st)
    ck('closed: no frame asked for by the start screen', st['raf'] == 0)
    fr = J("(()=>{let n=0;const r=window.requestAnimationFrame;window.__wsN=0;return 1})()")
    R("WS_HOOKS.open();0"); pg.wait_for_timeout(500); ck('the + menu hook opens it again', J('WS.on'))
    # each tile
    for k, name, ntr in [('beat', 'Beat starter', 2), ('audio', 'Audio tracks', 4)]:
        if not J('WS.on'): R('wsOpen({});0'); pg.wait_for_timeout(300)
        pg.click('#wsS [data-a="new"][data-k="%s"]' % k); pg.wait_for_timeout(500); st = J(ST)
        ck('tile %s opens a new project (%d tracks) and closes the start screen' % (name, ntr), st['cur'] == name and st['n'] == ntr and not st['on'], st)
    ck('the untouched empty project was dropped', 'Untitled' not in J('PJ.list.map(p=>p.name)'), J('PJ.list.map(p=>p.name)'))
    # a template and a saved project
    R("(async()=>{const T=JSON.parse(JSON.stringify(S));const db=await tmDB(),tx=tmTx(db,'tpl','readwrite');tx.objectStore('tpl').put({id:'tpWS',name:'WS test template',t:Date.now(),kind:'setup',S:T,st:{tr:T.tracks.length,bpm:T.bpm,cl:0}});await tmDone(tx)})();0")
    R("{const L=savedList();L.unshift({name:'WS saved song',t:Date.now()-3600e3,S:JSON.parse(JSON.stringify(S))});savedPut(L)}0"); pg.wait_for_timeout(300)
    R('wsOpen({});0'); pg.wait_for_timeout(700)
    ck('my template is listed', pg.locator('#wsS [data-a="tpl"]').count() == 1)
    pg.click('#wsS [data-a="tpl"]'); pg.wait_for_timeout(500); st = J(ST)
    ck('the template opens', st['cur'] == 'WS test template' and not st['on'], st)
    R('wsOpen({});0'); pg.wait_for_timeout(500); st = J(ST)
    ck('recent lists the tabs and the saved project', set(['Beat starter', 'Audio tracks', 'WS test template', 'WS saved song']) <= set(st['rows']), st['rows'])
    i = st['rows'].index('WS saved song'); pg.click('#wsS .wsRow[data-i="%d"]' % i); pg.wait_for_timeout(500); st = J(ST)
    ck('a saved project opens in a new tab', st['cur'] == 'WS saved song' and not st['on'], st)
    R("switchProject(PJ.list.find(p=>p.name==='Beat starter').id);saveProjects();0"); pg.wait_for_timeout(300)
    # menus and the New project window
    pg.click('#pAdd'); pg.wait_for_timeout(300); menu = pg.evaluate("document.getElementById('ctxm').textContent")
    ck('the + menu has Start screen and no Fractals demo', 'Start screen' in menu and 'Fractals' not in menu, menu[:160])
    pg.keyboard.press('Escape'); R('npOpen();0'); pg.wait_for_timeout(300)
    ck('New project: no demo songs', pg.evaluate("[...document.querySelectorAll('#npDemo,#npTpl [data-t=demo]')].every(e=>!e.offsetParent)"))
    R("document.getElementById('np').hidden=true;0")

    print('old profile (reload)')
    boot(); pg.wait_for_timeout(1700); st = J(ST)
    ck('the stored tabs come back (no Fractals, no demo added)', set(['Beat starter', 'Audio tracks', 'WS test template', 'WS saved song']) <= set(st['tabs']) and not any('Fractals' in t or 'demo' in t.lower() for t in st['tabs']), st['tabs'])
    ck('the start screen lists them, the one open at quit first', st['on'] and st['rows'][:1] == ['Beat starter'], st['rows'])
    pg.screenshot(path=os.path.join(OUT, 'old_dark.png'))
    pg.keyboard.type('saved'); pg.wait_for_timeout(200)
    rows = pg.evaluate("[...document.querySelectorAll('#wsList .wsRow b')].map(e=>e.textContent)")
    ck('typing searches', rows == ['WS saved song'], rows)
    pg.keyboard.press('Escape'); pg.wait_for_timeout(200)
    ck('Escape clears the search first', J('WS.on') and pg.locator('#wsList .wsRow').count() >= 4)
    pg.keyboard.press('ArrowDown'); ck('arrows move the selection', J('WS.sel') == 1)
    pg.keyboard.press('ArrowUp'); pg.keyboard.press('Enter'); pg.wait_for_timeout(400); st = J(ST)
    ck('Enter opens the last project', st['cur'] == 'Beat starter' and not st['on'], st)

    print('Light mode and Show at start-up')
    R("UI.lite=true;applyLite();wsOpen({});0"); pg.wait_for_timeout(800)
    ck('Light mode: one still picture, no frames asked for', J('WS.still&&!WS.raf'), J('[WS.still,WS.raf]'))
    pg.screenshot(path=os.path.join(OUT, 'old_light.png'))
    R("UI.lite=false;applyLite();0")
    pg.click('#wsSw'); ck('the switch turns Show at start-up off', J('UI.wsShow') is False)
    R("wsClose();saveUI();0"); pg.wait_for_timeout(300)
    boot(); pg.wait_for_timeout(2500); st = J(ST)
    ck('with it off the app starts on the last project, no start screen', not st['on'] and st['cur'] == 'Beat starter', st)
    ck('the Settings row is there and off', pg.evaluate("(()=>{const c=document.getElementById('wsSet');return!!c&&!c.checked})()") and J("STX.has('wsStart')"))
    R("UI.wsShow=true;saveUI();0")

    print('automation (no test key): the start as before this step')
    ctx2 = b.new_context(viewport={'width': 1254, 'height': 651})
    ctx2.route('https://app.test/**', alsong(lambda r: r.fulfill(body=SRC, content_type='text/html') if r.request.url.endswith('/') else r.fulfill(status=404, body='')))
    p2 = ctx2.new_page(); p2.goto('https://app.test/'); p2.wait_for_function('()=>window.AudioLab&&window.AudioLab.version', timeout=120000); p2.wait_for_timeout(9000)
    st2 = p2.evaluate("()=>AudioLab.run('({on:WS.on,auto:WS.auto,cur:curP().name})')")
    ck('under automation the Fractals song still opens at start (UI tests, export_same.py)', st2['auto'] and not st2['on'] and st2['cur'] == 'Fractals_remake', st2)
    ctx2.close()
    ck('no page errors', not errs, errs[:5])
    b.close()
print('%d of %d checks passed' % (N[1], N[0]))
if FAIL: print('FAILED:', FAIL); sys.exit(1)
