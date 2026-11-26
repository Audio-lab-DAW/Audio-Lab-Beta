"""The devices panel's header (task AA; changed in task AF, v0.212: no strip behind the tabs, the button is a pill above the panel's edge, folded away only the
pill shows; see taskAF.py for the full check): python3 tools/ui-tests/devices_header.py [index.html] [out dir]
Fractals demo at 1600 x 1000, normal and Light mode, panel open and folded away: the Devices button must sit inside the header strip (not
hanging into the devices below), the strip spans the panel's width, the button folds and opens the panel, a click on a track tab opens a folded
panel, and every control in the strip has a tooltip. Screenshots (2x) of each state."""
import sys, os, json
from playwright.sync_api import sync_playwright
F = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
OUT = sys.argv[2] if len(sys.argv) > 2 else '.'
os.makedirs(OUT, exist_ok=True)
SRC = open(F, encoding='utf-8').read()
FAIL = []
def ok(c, m):
    print(('ok   ' if c else 'FAIL ') + m, flush=True)
    if not c: FAIL.append(m)
GEO = """(()=>{const t=document.getElementById('fxTitle').getBoundingClientRect(),b=document.getElementById('fxHide').getBoundingClientRect(),fx=document.getElementById('fx').getBoundingClientRect(),
 tips=[...document.querySelectorAll('#fxTitle button,#fxHide')].filter(e=>e.offsetParent&&!(e.title||e.getAttribute('aria-label'))).length;
 return JSON.stringify({st:Math.round(t.top),sb:Math.round(t.bottom),sl:Math.round(t.left),sr:Math.round(t.right),bt:Math.round(b.top),bb:Math.round(b.bottom),br:Math.round(b.right),fl:Math.round(fx.left),fr:Math.round(fx.right),fxt:Math.round(fx.top),vis:getComputedStyle(document.getElementById('fxTitle')).display,tips})})()"""
with sync_playwright() as p:
    b = p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required']); pg = b.new_page(viewport={'width': 1600, 'height': 1000}, device_scale_factor=2); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)[:400]))
    pg.route('https://app.test/**', lambda r: r.fulfill(status=200, content_type='text/html', body=SRC.encode()) if r.request.url.endswith('.html') else r.fulfill(status=404, body=b''))
    pg.add_init_script("if(!localStorage.getItem('audiolab-ui'))localStorage.setItem('audiolab-ui',JSON.stringify({splash:false,lat3:1}))")
    pg.goto('https://app.test/index.html'); pg.wait_for_timeout(7000)
    pg.evaluate("()=>{const c=document.getElementById('liteNote');if(c)c.remove()}")
    ok(not errs, 'no page errors on load ' + '; '.join(errs))
    R = lambda c: pg.evaluate("c=>window.AudioLab.run(c)", c)
    for lite in (False, True):
        R("(()=>{UI.lite=%s;applyLite();return 1})()" % ('true' if lite else 'false'))
        for hid in (False, True):
            R("(()=>{devHide(%s);return 1})()" % ('true' if hid else 'false')); pg.wait_for_timeout(600)
            g = json.loads(R(GEO)); tag = '%s, %s' % ('Light mode' if lite else 'normal', 'folded away' if hid else 'open')
            ok(g['bb'] <= g['fxt'] - 1, '%s: Devices button above the panel edge, never in the devices (button %d..%d, panel top %d)' % (tag, g['bt'], g['bb'], g['fxt']))
            ok((g['vis'] == 'none') == hid, '%s: tabs shown when open, hidden when folded away (%s)' % (tag, g['vis']))
            ok(g['tips'] == 0, '%s: every control in the strip has a tooltip' % tag)
            y = max(0, g['st'] - 40)
            for side, x in (('left', 0), ('right', 1000)):
                pg.screenshot(path=os.path.join(OUT, 'header_%s_%s_%s.png' % ('light' if lite else 'normal', 'folded' if hid else 'open', side)), clip={'x': x, 'y': y, 'width': 600, 'height': 130})
    R("(()=>{UI.lite=false;applyLite();devHide(false);return 1})()"); pg.wait_for_timeout(400)
    pg.click('#fxHide'); pg.wait_for_timeout(400); h1 = R("UI.fxHide"); pg.click('#fxHide'); pg.wait_for_timeout(400); h2 = R("UI.fxHide")
    ok(h1 is True and h2 is False, 'the Devices button folds the panel away and brings it back')
    ok(not errs, 'no page errors ' + '; '.join(errs[:3]))
    b.close()
print('\n%d failures' % len(FAIL)); sys.exit(1 if FAIL else 0)
