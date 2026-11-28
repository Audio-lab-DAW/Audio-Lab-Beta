"""Changing a preset keeps the devices panel where it was (task AA): python3 tools/ui-tests/preset_scroll.py [index.html] [out dir]
Fractals demo at 1280 x 900. The device row and the row of track tabs are both scrolled; then the preset is changed in every way the user can:
the instrument's preset menu (mouse on the menu, then the keyboard on it), the arrow buttons of an effect and of the Kick designer, an effect's menu,
the Change browser (a click on another instrument, arrow keys, Escape back, Enter to keep), stopped and while playing. After each change, and again
0.5 s later, both scroll positions must be the same as before, and the device that was changed must still be in view."""
import sys, os, json
import sys as _ws_sys, os as _ws_os; _ws_sys.path.insert(0, _ws_os.path.join(_ws_os.path.dirname(_ws_os.path.abspath(__file__)), '../test-songs')); from alsong import alsong  # task WS-F: the test songs
from playwright.sync_api import sync_playwright
F = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
OUT = sys.argv[2] if len(sys.argv) > 2 else '.'
os.makedirs(OUT, exist_ok=True)
SRC = open(F, encoding='utf-8').read()
FAIL = []
def ok(c, m):
    print(('ok   ' if c else 'FAIL ') + m, flush=True)
    if not c: FAIL.append(m)
with sync_playwright() as p:
    b = p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required']); pg = b.new_page(viewport={'width': 1280, 'height': 900}); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)[:400]))
    pg.route('https://app.test/**', alsong(lambda r: r.fulfill(status=200, content_type='text/html', body=SRC.encode()) if r.request.url.endswith('.html') else r.fulfill(status=404, body=b'')))
    pg.add_init_script("if(!localStorage.getItem('audiolab-ui'))localStorage.setItem('audiolab-ui',JSON.stringify({splash:false,lat3:1}))")
    pg.goto('https://app.test/index.html'); pg.wait_for_timeout(7000)
    pg.evaluate("()=>{const c=document.getElementById('liteNote');if(c)c.remove()}")
    ok(not errs, 'no page errors on load ' + '; '.join(errs))
    R = lambda c: pg.evaluate("c=>window.AudioLab.run(c)", c)
    M = pg.mouse; K = pg.keyboard
    POS = "JSON.stringify([fxin.scrollLeft,(document.querySelector('#fxTitle .fxsc')||{scrollLeft:-1}).scrollLeft,fxin.scrollTop])"
    def sel(name):
        if not R("(()=>!![...document.querySelectorAll('#fxTitle .fxsc button')].find(b=>b.title.startsWith(%s+':')))()" % json.dumps(name)):
            print('    (no tab for %s; tabs: %s)' % (name, R("[...document.querySelectorAll('#fxTitle .fxsc button')].map(b=>b.title.split(':')[0]).slice(0,40).join(', ')+' | '+(S.tracks.map(t=>t.name).join(','))")))
        # pick the track by clicking its tab (scroll the tab row so it can be clicked)
        R("(()=>{const b=[...document.querySelectorAll('#fxTitle .fxsc button')].find(b=>b.title.startsWith(%s+':'));b.scrollIntoView({inline:'center',block:'nearest'});return 1})()" % json.dumps(name)); pg.wait_for_timeout(250)
        x, y = json.loads(R("(()=>{const b=[...document.querySelectorAll('#fxTitle .fxsc button')].find(b=>b.title.startsWith(%s+':'));if(!b)return '[0,0]';const r=b.getBoundingClientRect();return JSON.stringify([r.left+r.width/2,r.top+r.height/2])})()" % json.dumps(name)))
        if x: M.click(x, y); pg.wait_for_timeout(500)
        else: print('    (tab gone; tabs: %s)' % R("[...document.querySelectorAll('#fxTitle .fxsc button')].length+' '+document.querySelector('#fxTitle').innerHTML.slice(0,300)"))
        if not R("(()=>{const t=curT();return !!t&&t.name===%s})()" % json.dumps(name)): R("(()=>{selectTrack(S.tracks.find(t=>t.name===%s).id);return 1})()" % json.dumps(name)); pg.wait_for_timeout(300)
    def place(q, nth=0):
        """scroll the device row so the device that matches q is in the middle, and the row is not at its start"""
        R("(()=>{const d=[...fxin.querySelectorAll(%s)][%d].closest('.dev');const R0=fxin.getBoundingClientRect(),r=d.getBoundingClientRect();fxin.scrollLeft+=r.left-R0.left-(R0.width-r.width)/2;if(fxin.scrollLeft<40)fxin.scrollLeft=40;return 1})()" % (json.dumps(q), nth))
        pg.wait_for_timeout(250)
    def inview(q, nth=0):
        return R("(()=>{const e=[...fxin.querySelectorAll(%s)][%d];if(!e)return false;const d=e.closest('.dev'),R0=fxin.getBoundingClientRect(),r=d.getBoundingClientRect();return r.right>R0.left+40&&r.left<R0.right-40})()" % (json.dumps(q), nth))
    def center(q, nth=0):
        return json.loads(R("(()=>{const e=[...fxin.querySelectorAll(%s)][%d];const r=e.getBoundingClientRect();return JSON.stringify([r.left+r.width/2,r.top+r.height/2])})()" % (json.dumps(q), nth)))
    def check(what, q, nth=0):
        a = json.loads(R(POS)); pg.wait_for_timeout(500); c = json.loads(R(POS))
        good = a == before[0] and c == before[0] and (before[0][0] > 0 or before[0][2] > 0)
        ok(good, '%-58s devices %d > %d > %d, tabs %d > %d > %d%s%s' % (what, before[0][0], a[0], c[0], before[0][1], a[1], c[1], (', down %d > %d > %d' % (before[0][2], a[2], c[2])) if before[0][2] or a[2] or c[2] else '', '' if inview(q, nth) else ', DEVICE OUT OF VIEW'))
    before = [None]
    def mark(): before[0] = json.loads(R(POS))
    for mode in ('stopped', 'playing'):
        if mode == 'playing':
            K.press('Space'); pg.wait_for_timeout(1500); ok(R("play.on"), 'the song plays')
        # 1. the instrument preset menu on Lead (Plant): mouse, then keys
        sel('Lead'); place('.dev[data-d=inst] select[data-s=ipre]'); mark()
        R("(()=>{const s=fxin.querySelector('.dev[data-d=inst] select[data-s=ipre]');s.focus();s.selectedIndex=(s.selectedIndex+3)%s.options.length;s.dispatchEvent(new Event('input',{bubbles:true}));s.dispatchEvent(new Event('change',{bubbles:true}));return 1})()")
        check(mode + ': Lead, instrument preset menu', '.dev[data-d=inst] select[data-s=ipre]')
        place('.dev[data-d=inst] select[data-s=ipre]'); mark()
        x, y = center('.dev[data-d=inst] select[data-s=ipre]'); R("fxin.querySelector('.dev[data-d=inst] select[data-s=ipre]').focus();1"); K.press('ArrowDown'); pg.wait_for_timeout(300)
        check(mode + ': Lead, instrument preset with the arrow key', '.dev[data-d=inst] select[data-s=ipre]')
        R("document.activeElement&&document.activeElement.blur();1")
        # the row of track tabs scrolled away from Lead's tab, both ways: it must stay where the user put it
        for where in ('0', 'sc.scrollWidth'):
            place('.dev[data-d=inst] select[data-s=ipre]'); R("(()=>{const sc=document.querySelector('#fxTitle .fxsc');sc.scrollLeft=%s;return 1})()" % where); pg.wait_for_timeout(250); mark()
            R("(()=>{const s=fxin.querySelector('.dev[data-d=inst] select[data-s=ipre]');s.selectedIndex=(s.selectedIndex+1)%s.options.length;s.dispatchEvent(new Event('change',{bubbles:true}));return 1})()")
            check(mode + ': Lead, preset menu, track tabs scrolled to the ' + ('start' if where == '0' else 'end'), '.dev[data-d=inst] select[data-s=ipre]')
        # 2. arrows of an effect (Pro EQ, the second effect) and its menu
        place('.dev[data-d=fx] button[title="Next preset"]', 1); mark()
        M.click(*center('.dev[data-d=fx] button[title="Next preset"]', 1)); pg.wait_for_timeout(300)
        check(mode + ': Lead, next preset of an effect', '.dev[data-d=fx] button[title="Next preset"]', 1)
        place('.dev[data-d=fx] button[title="Previous preset"]', 1); mark()
        M.click(*center('.dev[data-d=fx] button[title="Previous preset"]', 1)); pg.wait_for_timeout(300)
        check(mode + ': Lead, previous preset of an effect', '.dev[data-d=fx] button[title="Previous preset"]', 1)
        place('.dev[data-d=fx] select', 1); mark()
        R("(()=>{const s=[...fxin.querySelectorAll('.dev[data-d=fx] select')][1];s.selectedIndex=(s.selectedIndex+2)%s.options.length;s.dispatchEvent(new Event('change',{bubbles:true}));return 1})()")
        check(mode + ': Lead, effect preset menu', '.dev[data-d=fx] select', 1)
        # 3. Kick designer arrows on the Kick track
        sel('Kick'); place('.dev[data-d=inst] [data-kk=next]'); mark()
        M.click(*center('.dev[data-d=inst] [data-kk=next]')); pg.wait_for_timeout(300)
        check(mode + ': Kick, next Kick designer preset', '.dev[data-d=inst] [data-kk=next]')
        # 4. Change browser on Bass: a click on another instrument, keys, Escape back; then once more and keep it with Enter
        sel('Bass'); place('.dev[data-d=inst] .duchg'); mark()
        M.click(*center('.dev[data-d=inst] .duchg')); pg.wait_for_timeout(900)
        opened = R("!!document.querySelector('#ibPlane .ibc')")
        if opened:
            K.press('ArrowRight'); pg.wait_for_timeout(400); K.press('ArrowRight'); pg.wait_for_timeout(400)
            K.press('Escape'); pg.wait_for_timeout(800)
            check(mode + ': Bass, Change, arrow keys, Escape back', '.dev[data-d=inst] .duchg')
            place('.dev[data-d=inst] .duchg'); mark()
            M.click(*center('.dev[data-d=inst] .duchg')); pg.wait_for_timeout(900)
            K.press('ArrowRight'); pg.wait_for_timeout(400); K.press('Enter'); pg.wait_for_timeout(900)
            if R("!!document.querySelector('#ibPlane .ibc')&&document.querySelector('#ibPlane').offsetParent"): K.press('Escape'); pg.wait_for_timeout(600)
            check(mode + ': Bass, Change, another instrument kept', '.dev[data-d=inst]')
            R("(()=>{undo();return 1})()"); pg.wait_for_timeout(600)
        else: ok(False, 'the Change browser opened')
        # 5. the Devices window, where the devices wrap into rows and the window scrolls down
        sel('Lead'); R("(()=>{devPop(true);renderFx();return 1})()"); pg.wait_for_timeout(800)
        R("(()=>{fxin.scrollTop=fxin.scrollHeight;return 1})()"); pg.wait_for_timeout(250); mark()
        R("(()=>{const s=[...fxin.querySelectorAll('.dev[data-d=fx] select')].pop();s.selectedIndex=(s.selectedIndex+1)%s.options.length;s.dispatchEvent(new Event('change',{bubbles:true}));return 1})()")
        check(mode + ': Devices window scrolled down, last effect preset', '.dev[data-d=fx] select', -1 if False else 0)
        R("(()=>{fxin.scrollTop=fxin.scrollHeight;return 1})()"); pg.wait_for_timeout(250); mark()
        R("(()=>{const s=fxin.querySelector('.dev[data-d=inst] select[data-s=ipre]');s.selectedIndex=(s.selectedIndex+1)%s.options.length;s.dispatchEvent(new Event('change',{bubbles:true}));return 1})()")
        check(mode + ': Devices window scrolled down, instrument preset', '.dev[data-d=fx] select', 0)
        R("(()=>{devPop(false);renderFx();return 1})()"); pg.wait_for_timeout(600)
        pg.screenshot(path=os.path.join(OUT, 'scroll_%s.png' % mode))
    K.press('Space'); pg.wait_for_timeout(300)
    ok(not errs, 'no page errors ' + '; '.join(errs[:3]))
    b.close()
print('\n%d failures' % len(FAIL)); sys.exit(1 if FAIL else 0)
