"""Task XT-DL3: the advanced settings list in the Workshop window (docs/extensions-plan.md 9.6 a, docs/settings-ids.md).
Fails when a released settings id disappears, when a setting has no stable id (a new STT row needs a row in XT_SET_NS and in
docs/settings-ids.md), when the list stops changing settings through Settings' own controls, when a value out of range or a locked
value is accepted, or when the Workshop costs anything before it is opened.
  python3 tools/ui-tests/taskXT_DL3.py [index.html] [out dir]"""
import sys, os, json, re
import sys as _ws_sys, os as _ws_os; _ws_sys.path.insert(0, _ws_os.path.join(_ws_os.path.dirname(_ws_os.path.abspath(__file__)), '../test-songs')); from alsong import alsong  # task WS-F: the test songs
from playwright.sync_api import sync_playwright
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = open(sys.argv[1] if len(sys.argv) > 1 else 'index.html', encoding='utf-8').read()
OUT = sys.argv[2] if len(sys.argv) > 2 else '.'; os.makedirs(OUT, exist_ok=True)
N = [0, 0]; FAIL = []
def ok(c, m, info=''):
    N[0] += 1
    if c: N[1] += 1; print('ok   ', m, info if info != '' else '')
    else: FAIL.append(m); print('FAIL ', m, info)
REL = []
for l in open(os.path.join(HERE, '..', '..', 'docs', 'settings-ids.md'), encoding='utf-8'):
    m = re.match(r'^\|\s*`([a-z][A-Za-z0-9]*(?:\.[A-Za-z0-9]+)+)`\s*\|', l)
    if m: REL.append(m.group(1))
INIT = "if(!sessionStorage.getItem('dl3')){sessionStorage.setItem('dl3','1');localStorage.setItem('audiolab-ui',JSON.stringify({splash:false,lat3:1}))}"
with sync_playwright() as p:
    b = p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required']); pg = b.new_page(viewport={'width': 1600, 'height': 1000}); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)[:300]))
    pg.on('console', lambda m: errs.append('console: ' + m.text[:300]) if m.type == 'error' and 'fetching the script' not in m.text and 'Failed to load resource' not in m.text else None)
    pg.add_init_script(INIT)
    pg.route('https://app.test/**', alsong(lambda r: r.fulfill(body=SRC, content_type='text/html') if r.request.url.endswith('/') else r.fulfill(status=404, body='')))
    pg.goto('https://app.test/'); pg.wait_for_function('() => window.AudioLab && window.AudioLab.version', timeout=90000); pg.wait_for_timeout(2500)
    R = lambda c: pg.evaluate('c => AudioLab.run(c)', c); J = lambda c: json.loads(R('JSON.stringify(' + c + ')'))
    ok(tuple(map(int, R('VERSION').split('.'))) >= (0, 295), 'version 0.295 or later', R('VERSION'))
    ok(J("XT_WS.el===null&&XT_WS.rows===null&&!document.getElementById('xtWs')&&UI.xtSet===undefined&&!XT_WS.listening"),
       'before the Workshop is opened nothing of it exists (no window, no list, no listener, nothing stored): it costs nothing')
    # ids
    rows = J("xtSetRows().map(r=>({id:r.id,st:r.st||null,kind:r.kind,t:r.t,l:r.l}))")
    ids = [r['id'] for r in rows]
    ok(len(ids) == len(set(ids)), 'every setting has one id, used once', len(ids))
    bad = [i for i in ids if not re.match(r'^[a-z][A-Za-z0-9]*(\.[a-zA-Z][A-Za-z0-9]*)+$', i)]
    ok(not bad, 'every id is namespaced (section.name)', bad)
    nst = J("STT.filter(r=>!r.same).length")
    ok(len([r for r in rows if r['st']]) == nst, 'every row of the settings table (STT, without its second controls) is in the list', nst)
    unn = [r['st'] for r in rows if r['id'].startswith('settings.')]
    ok(not unn, 'every row of the settings table has a stable name in XT_SET_NS (a new row needs one, and a row in docs/settings-ids.md)', unn)
    gone = [i for i in REL if i not in ids]
    ok(len(REL) >= 100 and not gone, 'every released settings id in docs/settings-ids.md is still in the list', (len(REL), gone))
    new = [i for i in ids if i not in REL]
    ok(not new, 'every id in the list is in docs/settings-ids.md', new)
    ok(all(r['l'] and '—' not in r['l'] for r in rows), 'every setting has a plain sentence (no em dash)')
    ok(J("['none','else','lock'].every(k=>xtSetRows().some(r=>r.kind===k))"), 'the list has values with no control, values set elsewhere, and locked values')
    # the door: logo menu (K4a) and the command
    pg.click('#bLogo', button='right'); pg.wait_for_timeout(300)
    it = pg.locator('#ctxm >> text=Workshop…')
    ok(it.count() == 1, 'the logo menu has "Workshop…" (always in the menu, K4a)')
    sub = J("[...document.querySelectorAll('#ctxm *')].map(e=>e.textContent).find(t=>/^Workshop…/.test(t))||''")
    ok('advanced' in sub, 'the menu entry says it is advanced', sub[:80])
    it.first.click(); pg.wait_for_timeout(400)
    ok(J("!!document.getElementById('xtWs')&&!$('#xtWs').hidden"), 'it opens the Workshop, a window of its own (K2b)')
    ok(J("$('#xtWs .fwt').textContent") == 'Workshop' and J("!!$('#xtWs .xtadv')&&$('#xtWs .xtadv').textContent==='Advanced'"), 'named Workshop (K3a), marked Advanced in its title bar')
    ok(J("!$('#xtWs .xtfirst').hidden&&/advanced feature/.test($('#xtWs .xtfirst').textContent)&&/↺/.test($('#xtWs .xtfirst').textContent)"), 'the first time, a note says it is advanced and how to undo a change')
    pg.screenshot(path=os.path.join(OUT, 'xt_dl3_dark.png'))
    pg.click('#xtWs [data-xw="seen"]'); ok(J("$('#xtWs .xtfirst').hidden&&UI.xtWsSeen===1"), '"Got it" hides the note for good')
    n0 = J("[...document.querySelectorAll('#xtWs .xtrow')].length"); ok(n0 == len(rows), 'the list shows every setting', (n0, len(rows)))
    # controls: titles, no em dashes
    nt = J("[...$('#xtWs').querySelectorAll('button,input,select')].filter(e=>!(e.title||e.dataset.tip||e.closest('[title],[data-tip]'))).map(e=>e.outerHTML.slice(0,80))")
    ok(not nt, 'every control in the Workshop has a tooltip', nt[:3])
    ok('—' not in J("$('#xtWs').innerText") and '—' not in J("[...$('#xtWs').querySelectorAll('[title],[data-tip]')].map(e=>(e.title||'')+(e.dataset.tip||'')).join(' ')"), 'no em dash in the Workshop text or tooltips')
    # search
    def search(q):
        pg.fill('#xtWs .xtq', q); pg.wait_for_timeout(80); return J("[...document.querySelectorAll('#xtWs .xtrow')].map(e=>e.dataset.row)")
    ok('edit.undoSteps' in search('undo'), 'search "undo" finds edit.undoSteps')
    ok('audio.buffer' in search('latency'), 'search by words: "latency" finds audio.buffer (Buffer size)')
    ok(search('qqqzzz') == [] and 'Nothing matches' in J("$('#xtWs .xtlist').textContent"), 'no match says so')
    search('')
    # a check row through Settings' own control
    pre = J("xtSetRows().filter(r=>xtSetChanged(r.id)).map(r=>[r.id,xtSetGet(r.id),r.d])")
    ENV = {'general.splash', 'performance.lite', 'dac.steady'}  # set by the test's profile (no splash) or by this machine (Light level and steady output on a headless GPU)
    ok(all(r[0] in ENV for r in pre), 'a fresh profile: nothing is marked changed (except what the test profile and this machine set)', pre)
    pre = [r[0] for r in pre]
    t0 = J("UI.tips!==false")
    pg.click('#xtWs [data-row="general.tips"] .xtsw'); pg.wait_for_timeout(150)
    ok(J("UI.tips!==false") != t0 and J("$('#setTips').checked") != t0, 'switching general.tips in the list changes the setting and the Settings window shows it')
    ok(J("$('#xtWs [data-row=\"general.tips\"]').classList.contains('chg')&&!!$('#xtWs [data-row=\"general.tips\"] [data-xa=reset]')"), 'the row is marked changed and has ↺')
    ok('"general.tips": false' in J("$('#xtWs .xtpre').textContent"), 'the file shows only what differs from the default', J("$('#xtWs .xtpre').textContent")[:120])
    pg.click('#xtWs [data-xf="chg"]'); pg.wait_for_timeout(80)
    ok(J("[...document.querySelectorAll('#xtWs .xtrow')].map(e=>e.dataset.row)")  == [i for i in ids if i in pre or i == 'general.tips'], 'filter Changed shows exactly what was changed')
    pg.click('#xtWs [data-row="general.tips"] [data-xa=reset]'); pg.wait_for_timeout(150)
    ok(J("UI.tips!==false") == t0 and J("$('#setTips').checked") == t0 and J("[...document.querySelectorAll('#xtWs .xtrow')].map(e=>e.dataset.row)") == [i for i in ids if i in pre], '↺ puts it back; it leaves the Changed filter')
    pg.click('#xtWs [data-xf="all"]')
    # a select row
    sel = J("xtSetRows().find(r=>r.st&&r.t==='select'&&r.pg==='export'&&xtSetOpts(r).length>1).id")
    o = J("(()=>{const r=xtSetRow('%s');return xtSetOpts(r).map(o=>o[0]).find(v=>v!==String(xtSetGet(r.id)))})()" % sel)
    v0 = J("xtSetGet('%s')" % sel)
    pg.select_option('#xtWs [data-xs="%s"]' % sel, o); pg.wait_for_timeout(150)
    ok(J("xtSetGet('%s')" % sel) == o and J("SETT.val(xtSetRow('%s').st)" % sel) == o, 'a select row (%s) changes the Settings control' % sel, (v0, o))
    J("xtSetReset('%s')" % sel); ok(J("xtSetGet('%s')" % sel) == v0, 'and goes back with reset')
    # Settings changed while the Workshop is open: the list follows
    R("(()=>{const c=$('#setTips');c.checked=!c.checked;c.dispatchEvent(new Event('change',{bubbles:true}))})()"); pg.wait_for_timeout(150)
    ok(J("$('#xtWs [data-xs=\"general.tips\"]').checked") == J("$('#setTips').checked"), 'a change made in Settings shows in the open list')
    R("(()=>{const c=$('#setTips');c.checked=!c.checked;c.dispatchEvent(new Event('change',{bubbles:true}))})()")
    # an opened constant: Undo's depth
    def put(id, v):
        pg.fill('#xtWs [data-xs="%s"]' % id, str(v)); pg.press('#xtWs [data-xs="%s"]' % id, 'Enter'); pg.wait_for_timeout(120)
    put('edit.undoSteps', 9999)
    ok(J("UI.xtSet===undefined") and 'Between 20 and 400' in J("$('#xtWs [data-row=\"edit.undoSteps\"]').textContent"), 'a value out of range is refused with a sentence and changes nothing')
    put('edit.undoSteps', 'abc') if False else None
    put('edit.undoSteps', 200)
    ok(J("UI.xtSet&&UI.xtSet['edit.undoSteps']") == 200, 'a value in range is kept in UI.xtSet (differences only)')
    n = J("(()=>{UNDO.length=0;for(let i=0;i<260;i++)pushUndo();return UNDO.length})()")
    ok(n == 200, 'Undo now keeps 200 steps', n)
    J("xtSetReset('edit.undoSteps')"); n = J("(()=>{pushUndo();return UNDO.length})()")
    ok(n == 80 and J("UI.xtSet===undefined"), 'reset: back to 80 steps, and nothing stored', n)
    J("UNDO.length=0")
    # the run log's length
    J("xtSetPut('workshop.consoleLines',10)"); R("(()=>{for(let i=0;i<30;i++)runCommand('no.such')})()")
    ok(J("XT_CMD_LOG.length") == 10, 'workshop.consoleLines 10: the run log keeps 10')
    J("xtSetReset('workshop.consoleLines')")
    # a value with its own key: the Map's height, applied at once
    mh0 = J("$('#mapw').style.height")
    put('arrange.mapHeight', 200)
    ok(J("UI.mapH") == 200 and J("$('#mapw').style.height") == '200px', 'arrange.mapHeight 200: the Map is 200 px at once', J("$('#mapw').style.height"))
    J("xtSetReset('arrange.mapHeight')"); ok(J("UI.mapH===undefined") and J("$('#mapw').style.height") == mh0, 'reset: the Map is back to its height', (mh0, J("$('#mapw').style.height")))
    put('capture.phraseGapS', 15); ok(J("UI.capGap") == 15, 'capture.phraseGapS writes the key the Capture menu uses'); J("xtSetReset('capture.phraseGapS')")
    # locked
    ok(J("xtSetPut('scripts.timeLimitMs',99999).ok") is False and J("[...document.querySelectorAll('#xtWs [data-row=\"scripts.timeLimitMs\"] input,#xtWs [data-row=\"scripts.timeLimitMs\"] select')].length") == 0,
       'a locked value has no editor and is refused by the code too')
    ok(J("xtSetGet('scripts.maxLogLines')===XT_SBX.MAXLOG&&xtSetGet('scripts.maxCodeKB')===XT_SBX.MAXCODE/1024"), 'the locked values shown are the sandbox\'s real limits')
    gl = J("xtSetRows().find(r=>r.kind==='glass').id")
    ok(J("xtSetPut('%s',true).ok" % gl) is False and J("[...document.querySelectorAll('#xtWs [data-row=\"%s\"] input')].length" % gl) == 0, 'the glass chain\'s rows are shown, changed only in Settings')
    pg.click('#xtWs [data-xf="lock"]'); ok(J("[...document.querySelectorAll('#xtWs .xtrow')].length") == 4, 'filter Locked shows the four locked values'); pg.click('#xtWs [data-xf="all"]')
    # show in Settings
    pg.click('#xtWs [data-row="audio.buffer"] [data-xa=show]'); pg.wait_for_timeout(500)
    ok(J("!$('#set').hidden"), '↗ opens the setting in the Settings window'); R("closeSet()")
    # the command
    R("xtWsClose()"); ok(J("$('#xtWs').hidden"), 'closes')
    ok(J("runCommand('view.workshop','test')") and J("!$('#xtWs').hidden"), 'command view.workshop opens it')
    ok(J("typeof XT_HOOKS.openWorkshop==='function'&&XT_HOOKS.val('nope',7)===7"), 'XT_HOOKS for other lanes (openWorkshop, val)')
    # Light level and narrow
    R("document.body.classList.add('lite')"); pg.wait_for_timeout(200); pg.screenshot(path=os.path.join(OUT, 'xt_dl3_light.png'))
    R("document.body.classList.remove('lite')")
    R("(()=>{const w=$('#xtWs');w.style.width='520px'})()"); pg.wait_for_timeout(250)
    ok(J("getComputedStyle($('#xtWs .xtfile')).display") == 'none' and J("$('#xtWs .xtlist').scrollWidth<=$('#xtWs .xtlist').clientWidth+1"), 'narrow window: the file pane folds away and nothing scrolls sideways')
    pg.screenshot(path=os.path.join(OUT, 'xt_dl3_narrow.png'))
    # kept across a restart
    J("xtSetPut('edit.undoSteps',120).ok"); R("saveUINow()"); pg.reload(); pg.wait_for_function('() => window.AudioLab && window.AudioLab.version', timeout=90000); pg.wait_for_timeout(1500)
    ok(J("UI.xtSet&&UI.xtSet['edit.undoSteps']") == 120 and J("UI.xtWsSeen") == 1 and J("XT_WS.el===null"), 'a change and "Got it" are kept after a restart; the Workshop stays closed')
    J("xtSetReset('edit.undoSteps')")
    ok(not errs, 'no console errors', errs[:3])
    b.close()
print('%d of %d' % (N[1], N[0]))
sys.exit(1 if FAIL else 0)
