"""Task WS-1b (lane Q): choose which drawings the start screen picks from.
Checks (at the user's size, 1254 x 651 CSS px at 1.75x = 2194 x 1139):
  - Settings, General: 'Start screen drawings…' sits right under 'Show the start screen at start-up', closed by default,
    one switch per drawing (7), all on by default (UI.wsDraw missing)
  - 'Only this one' leaves one drawing on; the last one cannot be turned off; the start screen then always picks it
  - two drawings on: the start screen alternates between them only (never twice in a row)
  - 'All on' goes back to the default (UI.wsDraw removed); the choice survives a reload
  - the hooks: WS_HOOKS.drawings(), WS_HOOKS.settingsRows (two rows in the S4 shape), localStorage audiolab-ws-draw for the splash
  - screenshots dark and Light of the open line; no page errors
  python3 tools/ui-tests/taskWS_1b.py [index.html] [out dir]"""
import sys, os, json
import sys as _ws_sys, os as _ws_os; _ws_sys.path.insert(0, _ws_os.path.join(_ws_os.path.dirname(_ws_os.path.abspath(__file__)), '../test-songs')); from alsong import alsong  # task WS-F: the test songs
from playwright.sync_api import sync_playwright
HERE = os.path.dirname(os.path.abspath(__file__))
IDX = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, '..', '..', 'index.html'))
OUT = os.path.abspath(sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, 'out', 'taskWS_1b'))
os.makedirs(OUT, exist_ok=True)
SRC = open(IDX, encoding='utf-8').read()
N = [0, 0]; FAIL = []
ALL = ['dipole', 'moons', 'interf', 'vdp', 'liss', 'trap', 'four']
def ck(name, ok, info=''):
    N[0] += 1
    if ok: N[1] += 1; print('  ok  ', name, '' if info == '' else info)
    else: FAIL.append(name); print('  FAIL', name, info)

with sync_playwright() as p:
    b = p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
    ctx = b.new_context(viewport={'width': 1254, 'height': 651}, device_scale_factor=1.75)
    ctx.route('https://app.test/**', alsong(lambda r: r.fulfill(body=SRC, content_type='text/html') if r.request.url.endswith('/') else r.fulfill(status=404, body='')))
    ctx.add_init_script("localStorage.setItem('audiolab-ws-test','1')")
    pg = ctx.new_page(); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)[:300]))
    R = lambda c: pg.evaluate('c=>AudioLab.run(c)', c)
    J = lambda c: json.loads(R('JSON.stringify(' + c + ')'))
    def boot():
        pg.goto('https://app.test/'); pg.wait_for_function('()=>window.AudioLab&&window.AudioLab.version', timeout=120000)
        pg.wait_for_function("()=>AudioLab.run('WS.on||!WS.pend')", timeout=30000); pg.wait_for_timeout(1500)
    def picks(n):
        out = []
        for _ in range(n):
            R("wsClose();0"); pg.wait_for_timeout(150); R("wsOpen({});0"); pg.wait_for_timeout(250); out.append(R('WS.kind'))
        R("wsClose();0"); return out
    boot()
    R("localStorage.removeItem('audiolab-ws-kind');wsClose();openSettings();0"); pg.wait_for_timeout(500)
    st = J("(()=>{const d=document.getElementById('wsDraw'),s=document.getElementById('wsSet');const lb=s&&s.closest('label');return{has:!!d,under:!!(d&&lb&&lb.nextElementSibling===d),open:d?d.open:null,n:d?d.querySelectorAll('input[data-k]').length:0,on:d?[...d.querySelectorAll('input[data-k]')].filter(c=>c.checked).length:0,ui:UI.wsDraw===undefined,sum:d?d.querySelector('summary').textContent:''}})()")
    ck("'Start screen drawings…' is right under the start screen's row, closed", st['has'] and st['under'] and st['open'] is False, st)
    ck('seven switches, all on by default', st['n'] == 7 and st['on'] == 7 and st['ui'], st)
    R("document.getElementById('wsDraw').open=true;0"); pg.wait_for_timeout(200)
    R("document.getElementById('wsDraw').scrollIntoView({block:'center'});0"); pg.wait_for_timeout(200)
    pg.screenshot(path=os.path.join(OUT, 'settings_dark.png'))
    R("UI.lite=true;applyLite();0"); pg.wait_for_timeout(300); pg.screenshot(path=os.path.join(OUT, 'settings_light.png'))
    R("UI.lite=false;applyLite();0")
    # Only this one
    pg.click('#wsDraw [data-only="liss"]'); pg.wait_for_timeout(100)
    st = J("({ui:UI.wsDraw,dis:document.querySelector('#wsDraw input[data-k=liss]').disabled,on:[...document.querySelectorAll('#wsDraw input[data-k]')].filter(c=>c.checked).map(c=>c.dataset.k),ls:localStorage.getItem('audiolab-ws-draw'),hk:WS_HOOKS.drawings()})")
    ck("'Only this one' leaves Lissajous alone, its switch locked on", st['ui'] == ['liss'] and st['on'] == ['liss'] and st['dis'], st)
    ck('the hooks follow: WS_HOOKS.drawings() and audiolab-ws-draw', st['hk'] == ['liss'] and json.loads(st['ls'] or '[]') == ['liss'], st)
    R("(()=>{const c=document.querySelector('#wsDraw input[data-k=liss]');c.disabled=false;c.click()})();0"); pg.wait_for_timeout(100)
    ck('the last drawing cannot be turned off', J("UI.wsDraw") == ['liss'] and R("document.querySelector('#wsDraw input[data-k=liss]').checked"))
    R("$('#set').hidden=true;0")
    ck('the start screen always picks it', set(picks(5)) == {'liss'})
    # two on
    R("openSettings();0"); pg.wait_for_timeout(300); R("document.getElementById('wsDraw').open=true;0")
    pg.click('#wsDraw input[data-k="trap"]'); pg.wait_for_timeout(100)
    ck('two drawings on', J("UI.wsDraw") == ['liss', 'trap'] and not R("document.querySelector('#wsDraw input[data-k=liss]').disabled"), J("UI.wsDraw"))
    R("$('#set').hidden=true;0")
    pk = picks(6)
    ck('only those two, never twice in a row', set(pk) <= {'liss', 'trap'} and all(pk[i] != pk[i + 1] for i in range(len(pk) - 1)), pk)
    ck('the summary counts them', '2 of 7' in R("document.querySelector('#wsDraw summary').textContent"))
    # reload keeps it
    R("saveUINow();0"); boot()
    ck('the choice survives a reload', J("UI.wsDraw") == ['liss', 'trap'] and R('WS.kind') in ('liss', 'trap'), [J("UI.wsDraw"), R('WS.kind')])
    R("wsClose();openSettings();0"); pg.wait_for_timeout(300)
    ck('the switches show it after the reload', J("[...document.querySelectorAll('#wsDraw input[data-k]')].filter(c=>c.checked).map(c=>c.dataset.k)") == ['liss', 'trap'])
    pg.click('#wsDraw summary'); pg.wait_for_timeout(100); pg.click('#wsDraw [data-all]'); pg.wait_for_timeout(100)
    ck("'All on' is the default again", R("UI.wsDraw===undefined") and J("WS_HOOKS.drawings()") == ALL)
    rows = J("WS_HOOKS.settingsRows.map(r=>[r.id,r.pg,r.k,r.t])")
    ck('two rows for lane B in the S4 shape', rows == [['wsStart', 'general', 'UI.wsShow', 'check'], ['wsDraw', 'general', 'UI.wsDraw', 'list']], rows)
    ck('the drawings row is not in the Settings table (a little hidden)', not R("STX.has('wsDraw')") and R("STX.has('wsStart')"))
    # a junk value falls back to all on
    R("UI.wsDraw=['nope'];0"); ck('a stored list with no known drawing means all on', J("wsDrawOn()") == ALL)
    R("delete UI.wsDraw;0")
    ck('no page errors', not errs, errs)
    b.close()
print('%d of %d' % (N[1], N[0]))
if FAIL: print('FAILED:', FAIL); sys.exit(1)
