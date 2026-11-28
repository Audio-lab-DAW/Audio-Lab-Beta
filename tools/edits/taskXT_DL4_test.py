"""Task XT-DL4: safe mode, what is changed, reset with a backup (docs/extensions-plan.md 9.6 g, 9.7 DL4; picks K11 a, b and c).
Fails when safe mode deletes or rewrites a customisation, when it does not start AudioLab as it came, when a door into it is missing
(the menu, Shift at start, the offer after a start that did not finish), when "What is changed" misses a kind or its ✕ does not put one
back, when Reset my customisations keeps no backup or cannot be undone, or when any of it costs something with nothing customised.
  python3 tools/ui-tests/taskXT_DL4.py [index.html] [out dir]"""
import sys, os, json, re, time
import sys as _ws_sys, os as _ws_os; _ws_sys.path.insert(0, _ws_os.path.join(_ws_os.path.dirname(_ws_os.path.abspath(__file__)), '../test-songs')); from alsong import alsong  # task WS-F: the test songs
from playwright.sync_api import sync_playwright
SRC = open(sys.argv[1] if len(sys.argv) > 1 else 'index.html', encoding='utf-8').read()
OUT = sys.argv[2] if len(sys.argv) > 2 else '.'; os.makedirs(OUT, exist_ok=True)
N = [0, 0]; FAIL = []
def ok(c, m, info=''):
    N[0] += 1
    if c: N[1] += 1; print('ok   ', m, info if info != '' else '')
    else: FAIL.append(m); print('FAIL ', m, info)
INIT = "if(!sessionStorage.getItem('dl4')){sessionStorage.setItem('dl4','1');localStorage.setItem('audiolab-ui',JSON.stringify({splash:false,lat3:1,xtWsSeen:1}))}"
with sync_playwright() as p:
    b = p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required']); pg = b.new_page(viewport={'width': 1600, 'height': 1000}); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)[:300]))
    pg.on('console', lambda m: errs.append('console: ' + m.text[:300]) if m.type == 'error' and 'fetching the script' not in m.text and 'Failed to load resource' not in m.text else None)
    pg.add_init_script(INIT)
    pg.route('https://app.test/**', alsong(lambda r: r.fulfill(body=SRC, content_type='text/html') if r.request.url.split('?')[0].endswith('/') else r.fulfill(status=404, body='')))
    R = lambda c: pg.evaluate('c => AudioLab.run(c)', c); J = lambda c: json.loads(R('JSON.stringify(' + c + ')'))
    def ready(t=2500):
        pg.wait_for_function('() => window.AudioLab && window.AudioLab.version', timeout=90000); pg.wait_for_timeout(t)
    def restarted(click_sel):
        """click a dialog button that restarts AudioLab and wait for the new page"""
        with pg.expect_navigation(timeout=60000):
            pg.click(click_sel)
        ready()
    stored = lambda: json.loads(pg.evaluate("localStorage.getItem('audiolab-ui')") or '{}')
    pg.goto('https://app.test/'); ready()
    ok(tuple(map(int, R('VERSION').split('.'))) >= (0, 296), 'version 0.296 or later', R('VERSION'))
    ok(J("!XT_SAFE.on&&!XT_SAFE.offer&&!document.getElementById('xtSafeBar')&&!document.getElementById('xtSafeOffer')&&!Object.getOwnPropertyDescriptor(UI,'toJSON')"),
       'a normal start: not in safe mode, no bar, no offer, settings saved as before (no toJSON)')
    ok(pg.evaluate("localStorage.getItem('al-xt-start')") is None, 'the start mark is gone once the first frame is drawn')
    ok(J("XT_SAFE.K.length>60&&['buf','keys','xtSet','trHide','hcz','mxOpt','fxHide','tips'].every(k=>XT_SAFE.K.includes(k))&&!XT_SAFE.K.includes('lite')"), 'safe mode covers every setting, the Workshop values, shortcuts and the four layout systems; Light mode stays (it protects a slow computer)', J("XT_SAFE.K.length"))
    L0 = J("(xtSetPrime(),xtChgList(false).map(c=>c.id))")
    ok(all(i in ('performance.lite', 'dac.steady') for i in L0), 'with nothing customised, What is changed is empty (but for what AudioLab sets itself on a weak computer: Light mode, steadier playback)', L0)
    # customise one of each kind
    R("xtSetPrime();SETT.set('tips',false);xtSetPut('edit.undoSteps',200);UI.keys={play:'P'};UI.trHide={tempo:true};trApply();UI.hcz=Object.assign({},UI.hcz||{},{xt:1});saveUINow()")
    L = J("xtChgList(false).map(c=>c.kind+':'+c.id)")
    ok(all(any(x.startswith(k) for x in L) for k in ('set:general.tips', 'set:edit.undoSteps', 'key:play', 'lay:trOrder', 'lay:hcz')), 'What is changed lists every kind: settings, Workshop values, a shortcut, layout', L)
    R("runCommand('view.whatIsChanged')"); pg.wait_for_timeout(400)
    ok(J("!$('#xtWs').hidden&&$('#xtWs .xtwb').classList.contains('xtchgon')&&$('#xtWs .xttabs [data-xt=chg]').classList.contains('on')"), 'the command opens the Workshop on its What is changed tab')
    nr = J("document.querySelectorAll('#xtWs .xtcr').length"); ok(nr == len(L), 'one row per change', (nr, len(L)))
    ok(J("[...document.querySelectorAll('#xtWs .xtchg button,#xtWs .xttabs button')].every(b=>b.title)"), 'every button of the tab has a tooltip')
    ok('—' not in J("$('#xtWs .xtchg').textContent"), 'no em dash')
    pg.screenshot(path=os.path.join(OUT, 'xt_dl4_changed.png'))
    pg.click('#xtWs [data-xc=x][data-kind=key]'); pg.wait_for_timeout(150)
    ok(J("UI.keys===undefined&&document.querySelectorAll('#xtWs .xtcr').length") == nr - 1, '✕ on a shortcut puts it back')
    pg.click('#xtWs [data-xc=x][data-kind=lay][data-id=trOrder]'); pg.wait_for_timeout(150)
    ok(J("UI.trHide===undefined&&UI.trOrder===undefined"), '✕ on the transport layout puts it back')
    pg.click('#xtWs [data-xc=x][data-id="edit.undoSteps"]'); pg.wait_for_timeout(150)
    ok(J("xtV('edit.undoSteps',80)===80&&UI.xtSet===undefined"), '✕ on a Workshop value puts it back')
    R("xtSetPut('edit.undoSteps',200);UI.keys={play:'P'};UI.trHide={tempo:true};trApply();saveUINow();xtChgDraw()")
    pg.click('#xtWs .xttabs [data-xt=set]'); ok(J("!$('#xtWs .xtwb').classList.contains('xtchgon')&&getComputedStyle($('#xtWs .xtmain')).display!=='none'&&document.querySelectorAll('#xtWs .xtrow').length>100"), 'the Settings list tab comes back')
    # the menu door (K11b)
    R("closeMenu&&closeMenu();xtWsClose()")
    pg.click('#bLogo', button='right'); pg.wait_for_timeout(300)
    R("(()=>{const b=[...ctxm.querySelectorAll('button[aria-haspopup=menu]')].find(b=>/^Restart/.test(b.textContent.trim()));b.click()})()"); pg.wait_for_timeout(150)
    sub = J("[...ctxm.querySelectorAll('button[data-i]')].map(b=>b.textContent.trim())")
    ok(any(s.startswith('Restart in safe mode…') for s in sub) and sub[:2][0] == 'Restart audio engine', 'the Restart submenu has "Restart in safe mode…" after the two restarts', sub)
    pg.locator('#ctxm button[data-i]', has_text='Restart in safe mode').first.click(); pg.wait_for_timeout(300)
    ok(J("!$('#cdlg').hidden&&/Nothing is deleted/.test($('#cdP').textContent)"), 'it asks first and says nothing is deleted')
    before = stored()
    restarted('#cdB button.pri')
    # in safe mode
    ok(J("XT_SAFE.on&&!!document.getElementById('xtSafeBar')"), 'AudioLab restarted in safe mode, with its bar across the top')
    ok(J("UI.tips===undefined||UI.tips===true") and J("UI.keys===undefined&&UI.trHide===undefined&&xtV('edit.undoSteps',80)===80"), 'safe mode starts as it came: settings, shortcuts, layout and Workshop values at their defaults')
    ok(J("SETT.isDefault('tips')!==false") if J("(()=>{try{xtSetPrime();return true}catch(e){return false}})()") else False, 'the Settings control shows the default too')
    s1 = stored(); ok(s1.get('tips') is False and s1.get('keys') == {'play': 'P'} and s1.get('trHide') == {'tempo': True} and (s1.get('xtSet') or {}).get('edit.undoSteps') == 200, 'nothing is deleted: the stored customisations are untouched', {k: s1.get(k) for k in ('tips', 'keys', 'trHide', 'xtSet')})
    R("UI.splash=true;UI.tips=false;saveUINow()"); s2 = stored()
    ok(s2.get('keys') == {'play': 'P'} and s2.get('trHide') == {'tempo': True} and s2.get('tips') is False, 'saving in safe mode keeps every stored customisation (a change in safe mode is not kept)')
    R("UI.tips=undefined;delete UI.tips;UI.splash=false;saveUINow()")
    bt = J("$('#xtSafeBar').textContent"); ok('not deleted' in bt and 'Leave safe mode' in bt and '—' not in bt, 'the bar says it is safe mode, nothing is deleted, and offers to leave', bt[:160])
    ok(J("[...document.querySelectorAll('#xtSafeBar button')].every(b=>b.title)"), 'every button of the bar has a tooltip')
    pg.screenshot(path=os.path.join(OUT, 'xt_dl4_safe_bar.png'))
    pg.click('#xtSafeBar [data-xsf=chg]'); pg.wait_for_timeout(400)
    sl = J("[...document.querySelectorAll('#xtWs .xtcr b')].map(b=>b.textContent)")
    ok('Light mode' not in sl and len(sl) >= 4 and J("document.querySelectorAll('#xtWs .xtcr [data-xc=x]').length") == 0, 'What is changed in safe mode lists what is set aside, without ✕', sl)
    pg.screenshot(path=os.path.join(OUT, 'xt_dl4_safe_changed.png'))
    pg.click('#xtSafeBar [data-xsf=fold]'); ok(J("$('#xtSafeBar').classList.contains('fold')"), 'the bar folds to its badge')
    pg.click('#xtSafeBar [data-xsf=fold]')
    pg.click('#xtSafeBar [data-xsf=leave]'); pg.wait_for_timeout(200)
    restarted('#cdB button.pri')
    ok(J("!XT_SAFE.on&&!document.getElementById('xtSafeBar')"), 'Leave safe mode restarts normally')
    ok(J("UI.tips===false&&UI.keys.play==='P'&&UI.trHide.tempo===true&&xtV('edit.undoSteps',80)===200"), 'every customisation is back after leaving safe mode')
    # reset my customisations, with a backup, and its undo
    R("xtChgOpen()"); pg.wait_for_timeout(300)
    nb = J("ST7.backups().length")
    pg.click('#xtWs [data-xc=reset]'); pg.wait_for_timeout(200)
    ok(J("/backup/.test($('#cdP').textContent)"), 'Reset my customisations asks first and says a backup is kept')
    restarted('#cdB button.pri')
    ok(J("UI.keys===undefined&&UI.trHide===undefined&&UI.xtSet===undefined&&UI.tips===undefined"), 'after the reset every customisation is at its default')
    ok(J("ST7.backups().length") == min(3, nb + 1) and J("ST7.backups()[0].why") == 'before Reset my customisations', 'a dated backup was kept (Settings › General lists it)')
    R("xtChgOpen()"); pg.wait_for_timeout(300)
    ok(J("!!document.querySelector('#xtWs [data-xc=back]')"), 'the tab offers "Bring them back"')
    pg.screenshot(path=os.path.join(OUT, 'xt_dl4_reset.png'))
    pg.click('#xtWs [data-xc=back]'); pg.wait_for_timeout(200)
    restarted('#cdB button.pri')
    ok(J("UI.tips===false&&UI.keys.play==='P'&&UI.trHide.tempo===true&&xtV('edit.undoSteps',80)===200"), '"Bring them back" undoes the reset')
    ok(J("!xtChgBackup()"), 'and the offer is gone')
    # the offer after a start that did not finish (K11c)
    pg.evaluate("addEventListener('pagehide',()=>localStorage.setItem('al-xt-start',String(Date.now())))")  # a start that died: its mark stays (a normal close clears it)
    pg.reload(); ready()
    ok(J("!!document.getElementById('xtSafeOffer')&&/did not finish/.test($('#xtSafeOffer').textContent)&&!XT_SAFE.on"), 'after a start that did not finish, safe mode is offered (a bar, not a dialog in the way)')
    ok(J("[...document.querySelectorAll('#xtSafeOffer button')].every(b=>b.title)"), 'its buttons have tooltips')
    pg.screenshot(path=os.path.join(OUT, 'xt_dl4_offer.png'))
    pg.click('#xtSafeOffer [data-xsf=no]'); ok(J("!document.getElementById('xtSafeOffer')&&!XT_SAFE.on"), '"Start normally" keeps going as it is')
    ok(pg.evaluate("localStorage.getItem('al-xt-start')") is None, 'and the start mark is gone')
    # Shift held while AudioLab starts (K11a)
    pg.evaluate("location.reload()"); t0 = time.time(); seen = False
    while time.time() - t0 < 60:
        try:
            pg.keyboard.press('Shift')
            if pg.evaluate("!!document.getElementById('xtSafeOffer')"): seen = True; break
        except Exception: pass
        pg.wait_for_timeout(100)
    ready(800)
    ok(seen and J("/held Shift/.test($('#xtSafeOffer').textContent)"), 'holding Shift while AudioLab starts offers safe mode')
    restarted('#xtSafeOffer [data-xsf=go]')
    ok(J("XT_SAFE.on&&!!document.getElementById('xtSafeBar')"), 'and "Restart in safe mode" there starts it')
    pg.click('#xtSafeBar [data-xsf=leave]'); pg.wait_for_timeout(200); restarted('#cdB button.pri')
    ok(J("!XT_SAFE.on&&UI.keys.play==='P'"), 'left again, nothing lost')
    pg.keyboard.press('Shift'); pg.wait_for_timeout(300)
    ok(J("!document.getElementById('xtSafeOffer')"), 'Shift after the start does nothing (the listeners are gone)')
    ok(J("xtCommands().has('help.safeMode')&&xtCommands().has('view.whatIsChanged')"), 'the commands help.safeMode and view.whatIsChanged exist')
    ok(not errs, 'no console errors', errs[:5])
    b.close()
print('%d of %d' % (N[1], N[0]))
if FAIL: print('FAILED:', FAIL); sys.exit(1)
