#!/usr/bin/env python3
"""Task DR5: headless checks and screenshots of the pick page tools/design-lab/dr5/overlays.html.
   python3 tools/design-lab/dr5/check.py [out dir]
Serves the folder on 127.0.0.1:8766 with the same skeleton the artifact host adds (doctype, charset, viewport)."""
import sys, os, threading, http.server, functools
from playwright.sync_api import sync_playwright
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'shots'); os.makedirs(OUT, exist_ok=True)
SRC = open(os.path.join(HERE, 'overlays.html'), encoding='utf-8').read()
class H(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        if self.path.startswith('/page.html'):
            b = ('<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><style>[hidden]{display:none!important}img{max-width:100%}</style></head><body>' + SRC + '</body></html>').encode()
            self.send_response(200); self.send_header('Content-Type', 'text/html; charset=utf-8'); self.send_header('Content-Length', str(len(b))); self.end_headers(); self.wfile.write(b); return
        return super().do_GET()
srv = http.server.ThreadingHTTPServer(('127.0.0.1', 8766), functools.partial(H, directory=HERE)); threading.Thread(target=srv.serve_forever, daemon=True).start()
FAIL = []; N = [0]
def ok(c, m, d=''):
    N[0] += 1; print(('ok   ' if c else 'FAIL ') + m + (('   ' + str(d)[:240]) if d != '' else ''), flush=True)
    if not c: FAIL.append(m)
with sync_playwright() as p:
    b = p.chromium.launch(args=['--no-proxy-server'])
    def page(w=1280, h=900, scheme='dark'):
        ctx = b.new_context(viewport={'width': w, 'height': h}, color_scheme=scheme, device_scale_factor=1)
        pg = ctx.new_page(); logs = []
        pg.on('console', lambda m: logs.append(m.text) if m.type == 'error' and 'fonts.g' not in m.text and 'ERR_' not in m.text else None)
        pg.on('pageerror', lambda e: logs.append('pageerror ' + str(e)))
        pg.route('**/fonts.googleapis.com/**', lambda r: r.abort()); pg.route('**/fonts.gstatic.com/**', lambda r: r.abort())
        pg.goto('http://127.0.0.1:8766/page.html'); pg.wait_for_timeout(400); return pg, logs
    pg, logs = page()
    ok(pg.evaluate("document.querySelectorAll('.card').length") == 29, 'all 29 cards built (6 families: R 5, D 5, T 4, N 5, X 5, K 5)', pg.evaluate("document.querySelectorAll('.card').length"))
    bf = pg.evaluate("()=>{let n=0;for(const e of document.querySelectorAll('*')){const v=getComputedStyle(e).backdropFilter;if(v&&v!=='none')n++}return n}")
    ok(bf == 0 and not __import__('re').search(r'backdrop-filter\s*:', SRC), 'no backdrop-filter anywhere on the page', bf)
    ok(pg.evaluate("document.documentElement.scrollWidth<=innerWidth"), 'no sideways scroll at 1280')
    pg.screenshot(path=f'{OUT}/page-dark-top.png')
    # ---- R ----
    for rid in ['R0', 'R1', 'R2', 'R3', 'R4']:
        c = f'.card[data-id="{rid}"]'
        pg.click(f'{c} [data-t="track"]'); pg.wait_for_timeout(150)
        n = pg.evaluate("()=>{const m=document.querySelector('#ovroot .menu');return m?m.querySelectorAll('[role=menuitem]').length:0}")
        ok(n > 5, f'{rid}: track menu opens with items', n)
        if rid == 'R1': pg.screenshot(path=f'{OUT}/r1-track-menu.png')
        if rid == 'R4':
            pg.keyboard.type('dru'); pg.wait_for_timeout(50)
            t = pg.evaluate("()=>document.querySelector('#ovroot .menu .focus')?.textContent")
            ok(t and 'Drums' in t, 'R4: typing "dru" puts Move into Drums first', t)
            pg.screenshot(path=f'{OUT}/r4-filter.png')
        else:
            f0 = pg.evaluate("()=>document.activeElement.textContent"); pg.keyboard.press('ArrowDown'); f1 = pg.evaluate("()=>document.activeElement.textContent")
            ok(f0 != f1, f'{rid}: ArrowDown moves the focus', (f0[:20], f1[:20]))
        pg.keyboard.press('Escape'); pg.wait_for_timeout(120)
        ok(pg.evaluate("!document.querySelector('#ovroot .menu')") and pg.evaluate(f"document.activeElement===document.querySelector('{c} [data-t=track]')"), f'{rid}: Esc closes and gives focus back')
        pg.click(f'{c} [data-t="mute"]'); pg.wait_for_timeout(120)
        txt = pg.evaluate("document.querySelector('#ovroot .menu').textContent")
        if rid != 'R0': ok('Hide the Mute button' in txt and 'Customise the Mute button' in txt and 'Advanced' in txt, f'{rid}: Mute menu has the named Advanced entries (K12a)')
        if rid == 'R1': pg.screenshot(path=f'{OUT}/r1-mute-menu.png')
        pg.keyboard.press('Escape')
    pg.click('.card[data-id="R1"] [data-t="track"]'); pg.wait_for_timeout(100)
    for _ in range(30):
        if pg.evaluate("document.activeElement.getAttribute('aria-haspopup')==='menu'"): break
        pg.keyboard.press('ArrowDown')
    pg.keyboard.press('ArrowRight'); pg.wait_for_timeout(80)
    ok(pg.evaluate("document.querySelectorAll('#ovroot .menu').length") == 2 and 'Move into' in pg.evaluate("document.activeElement.textContent+document.querySelectorAll('#ovroot .menu')[1].textContent"), 'R1: ArrowRight opens the Routing submenu with focus in it')
    pg.screenshot(path=f'{OUT}/r1-submenu.png'); pg.keyboard.press('Escape'); pg.keyboard.press('Escape')
    pg.click('.card[data-id="R1"] [data-t="q"]'); pg.wait_for_timeout(80); pg.keyboard.press('ArrowDown'); pg.keyboard.press('Enter'); pg.wait_for_timeout(80)
    ok(pg.evaluate("document.querySelector('.qv').textContent") == '1/32', 'R1: dropdown picks the next value with the keyboard', pg.evaluate("document.querySelector('.qv').textContent"))
    pg.click('.card[data-id="R1"] [data-hd="1"]', button='right'); pg.wait_for_timeout(80)
    ok(pg.evaluate("!!document.querySelector('#ovroot .menu')"), 'R1: right-click on a track header opens its menu'); pg.keyboard.press('Escape')
    # ---- D ----
    for did in ['D0', 'D1', 'D2', 'D3', 'D4']:
        c = f'.card[data-id="{did}"]'
        pg.click(f'{c} [data-k="close"]'); pg.wait_for_timeout(200)
        ok(pg.evaluate(f"!!document.querySelector('{c} .dlg')"), f'{did}: close dialog opens')
        if did in ('D1', 'D2'):
            for _ in range(6): pg.keyboard.press('Tab')
            ok(pg.evaluate(f"document.querySelector('{c} .dlg').contains(document.activeElement)"), f'{did}: Tab stays inside the dialog')
        pg.screenshot(path=f'{OUT}/{did.lower()}-close.png', clip=pg.evaluate(f"(()=>{{const r=document.querySelector('{c}').getBoundingClientRect();return {{x:r.x,y:r.y,width:r.width,height:r.height}}}})()"))
        pg.keyboard.press('Escape'); pg.wait_for_timeout(100)
        ok(pg.evaluate(f"!document.querySelector('{c} .dlg')"), f'{did}: Esc closes it')
        pg.click(f'{c} [data-k="stems"]'); pg.wait_for_timeout(200)
        if did == 'D3': pg.wait_for_timeout(50)
        pg.click(f'{c} [data-v="split"]'); pg.wait_for_timeout(1500)
        ok(pg.evaluate(f"!!document.querySelector('{c} .dlg .orb')"), f'{did}: Split shows the orbit loader with progress')
        if did in ('D1', 'D4'): pg.screenshot(path=f'{OUT}/{did.lower()}-stems-progress.png', clip=pg.evaluate(f"(()=>{{const r=document.querySelector('{c}').getBoundingClientRect();return {{x:r.x,y:r.y,width:r.width,height:r.height}}}})()"))
        pg.wait_for_timeout(3000)
        ok(pg.evaluate(f"!document.querySelector('{c} .dlg')") and 'Stems ready' in pg.evaluate(f"document.querySelector('{c} .said').textContent"), f'{did}: the job finishes and the dialog closes')
    pg.click('.card[data-id="D3"] [data-k="rename"]'); pg.wait_for_timeout(80); pg.keyboard.type('Neutron'); pg.keyboard.press('Enter')
    ok(pg.evaluate("document.querySelector('.card[data-id=D3] .tname').textContent") == 'Neutron', 'D3: rename in place')
    # ---- T ----
    pg.hover('.card[data-id="T1"] [data-tt="2"]'); pg.wait_for_timeout(60)
    h = pg.evaluate("document.querySelector('.card[data-id=T1] .helpln').textContent")
    ok('Tempo' in h and 'DEFAULT' in h and 'SCOPE' in h, 'T1: help line fills at once with default and scope', h[:80])
    ok(pg.evaluate("!document.querySelector('.tip')"), 'T1: no tag before 500 ms')
    pg.wait_for_timeout(600); ok(pg.evaluate("!!document.querySelector('.tip.t1')"), 'T1: tag after 500 ms')
    pg.screenshot(path=f'{OUT}/t1.png', clip=pg.evaluate("(()=>{const r=document.querySelector('.card[data-id=T1]').getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height}})()"))
    pg.keyboard.press('Escape'); ok(pg.evaluate("!document.querySelector('.tip')"), 'T1: Esc hides the tag (WCAG 1.4.13)')
    pg.hover('.card[data-id="T1"] [data-tt="3"]'); pg.wait_for_timeout(60); pg.hover('.card[data-id="T1"] [data-tt="4"]'); pg.wait_for_timeout(700)
    pg.hover('.card[data-id="T3"] [data-tt="4"]'); pg.wait_for_timeout(650)
    ok(pg.evaluate("!!document.querySelector('.tip.t3')&&!!document.querySelector('.leader')"), 'T3: callout with leader')
    pg.screenshot(path=f'{OUT}/t3.png', clip=pg.evaluate("(()=>{const r=document.querySelector('.card[data-id=T3]').getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height+60}})()"))
    pg.mouse.move(5, 5); pg.wait_for_timeout(50)
    pg.focus('.card[data-id="T2"] [data-tt="0"]'); pg.wait_for_timeout(40)
    ok('Loop' in pg.evaluate("document.querySelector('.card[data-id=T2] .helpln').textContent"), 'T2: keyboard focus fills the help line')
    # ---- N ----
    for nid in ['N0', 'N1', 'N2', 'N3', 'N4']:
        c = f'.card[data-id="{nid}"]'
        for k in ['done', 'err', 'upd', 'lite', 'job']: pg.click(f'{c} [data-n="{k}"]'); pg.wait_for_timeout(60)
        pg.wait_for_timeout(600)
        pg.screenshot(path=f'{OUT}/{nid.lower()}.png', clip=pg.evaluate(f"(()=>{{const r=document.querySelector('{c}').getBoundingClientRect();return {{x:r.x,y:r.y,width:r.width,height:r.height}}}})()"))
    ok(pg.evaluate("document.querySelectorAll('.card[data-id=N1] .nc').length") == 3, 'N1: at most three cards on screen', pg.evaluate("document.querySelectorAll('.card[data-id=N1] .nc').length"))
    pg.click('.card[data-id="N1"] [data-bell]'); pg.wait_for_timeout(60)
    ok('5 MESSAGES' in pg.evaluate("document.querySelector('.card[data-id=N1] .loglist').textContent"), 'N1: the log keeps all five')
    # ---- X ----
    for xid in ['X0', 'X1', 'X2', 'X3', 'X4']:
        c = f'.card[data-id="{xid}"]'; pg.locator(c).scroll_into_view_if_needed()
        chip = pg.locator(f'{c} [data-chip]').bounding_box(); lane = pg.locator(f'{c} .lane[data-i="2"] .lbody').bounding_box()
        pg.mouse.move(chip['x'] + 20, chip['y'] + 10); pg.mouse.down()
        pg.mouse.move(lane['x'] + 100, lane['y'] + 10, steps=6); pg.wait_for_timeout(60)
        n = pg.evaluate(f"document.querySelectorAll('{c} .dov, {c} .x1hot, {c} .x2sheet, .x3card').length")
        ok(n > 0 or xid == 'X0', f'{xid}: feedback while dragging over an audio lane', n)
        pg.screenshot(path=f'{OUT}/{xid.lower()}-drag.png', clip=pg.evaluate(f"(()=>{{const r=document.querySelector('{c}').getBoundingClientRect();return {{x:r.x,y:r.y,width:r.width,height:r.height}}}})()"))
        pg.mouse.up(); pg.wait_for_timeout(50)
        ok('Dropped' in pg.evaluate(f"document.querySelector('{c} .said').textContent"), f'{xid}: drop reported', pg.evaluate(f"document.querySelector('{c} .said').textContent"))
    pg.focus('.card[data-id="X1"] [data-chip]'); pg.keyboard.press('Space'); pg.keyboard.press('ArrowRight'); pg.keyboard.press('ArrowDown')
    ok(pg.evaluate("!!document.querySelector('.card[data-id=X1] .x1line')"), 'X1: keyboard pick-up shows the insertion line'); pg.keyboard.press('Space')
    # ---- K ----
    pg.click('.card[data-id="K1"] [data-a="pal"]'); pg.wait_for_timeout(80); pg.keyboard.type('spl')
    f = pg.evaluate("document.querySelector('.card[data-id=K1] .pal .r.focus').textContent")
    ok('Split' in f, 'K1: fuzzy "spl" finds Split first', f)
    pg.screenshot(path=f'{OUT}/k1.png', clip=pg.evaluate("(()=>{const r=document.querySelector('.card[data-id=K1]').getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height}})()"))
    pg.keyboard.press('Enter'); ok('Split' in pg.evaluate("document.querySelector('.card[data-id=K1] .said').textContent"), 'K1: Enter runs it')
    pg.click('.card[data-id="K1"] .stage .lbody'); pg.keyboard.press('Control+k'); pg.wait_for_timeout(60); pg.keyboard.type('zzqx')
    ok('Ask the Assistant' in pg.evaluate("document.querySelector('.card[data-id=K1] .pal').textContent"), 'K1: Ctrl+K opens it; no match offers the Assistant'); pg.keyboard.press('Escape')
    pg.click('.card[data-id="K2"] [data-a="pal"]'); pg.wait_for_timeout(80)
    ok('For the selection' in pg.evaluate("document.querySelector('.card[data-id=K2] .pal').textContent"), 'K2: selection actions first')
    pg.screenshot(path=f'{OUT}/k2.png', clip=pg.evaluate("(()=>{const r=document.querySelector('.card[data-id=K2]').getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height}})()")); pg.keyboard.press('Escape')
    pg.locator('.card[data-id="K3"] [data-a="hold"]').scroll_into_view_if_needed(); pg.wait_for_timeout(200); bx = pg.locator('.card[data-id="K3"] [data-a="hold"]').bounding_box(); pg.mouse.move(bx['x'] + 5, bx['y'] + 5); pg.mouse.down(); pg.wait_for_timeout(650)
    ok(pg.evaluate("document.querySelectorAll('.card[data-id=K3] .kbadge').length") >= 5, 'K3: holding shows key badges')
    pg.screenshot(path=f'{OUT}/k3.png', clip=pg.evaluate("(()=>{const r=document.querySelector('.card[data-id=K3]').getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height}})()")); pg.mouse.up()
    pg.click('.card[data-id="K4"] [data-a="sheet"]'); pg.wait_for_timeout(80); pg.keyboard.type('⇧' if False else 'shift')
    pg.screenshot(path=f'{OUT}/k4.png', clip=pg.evaluate("(()=>{const r=document.querySelector('.card[data-id=K4]').getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height}})()")); pg.keyboard.press('Escape')
    # ---- picks ----
    pg.click('#rec'); ok(pg.evaluate("document.querySelector('#pline').textContent") == 'DR5 picks: R1 D1 T1 N1 X1 K1', 'Use ★ picks gives the line', pg.evaluate("document.querySelector('#pline').textContent"))
    ok(not logs, 'no console errors (dark, 1280)', logs)
    pg.screenshot(path=f'{OUT}/page-dark-full.png', full_page=True)
    # light, phone width
    pl, logs2 = page(400, 860, 'light')
    ok(pl.evaluate("document.documentElement.scrollWidth<=innerWidth"), 'no sideways scroll at 400 px (light)', pl.evaluate("[document.documentElement.scrollWidth,innerWidth]"))
    pl.click('.card[data-id="R1"] [data-t="track"]'); pl.wait_for_timeout(100); pl.screenshot(path=f'{OUT}/phone-light-menu.png'); pl.keyboard.press('Escape')
    pl.screenshot(path=f'{OUT}/phone-light-full.png', full_page=True)
    ok(not logs2, 'no console errors (light, 400)', logs2)
    pw, _ = page(1280, 900, 'light'); pw.click('.card[data-id="R1"] [data-t="track"]'); pw.wait_for_timeout(100); pw.screenshot(path=f'{OUT}/light-r1.png'); pw.keyboard.press('Escape')
    pw.click('.card[data-id="D1"] [data-k="close"]'); pw.wait_for_timeout(250); pw.screenshot(path=f'{OUT}/light-d1.png', clip=pw.evaluate("(()=>{const r=document.querySelector('.card[data-id=D1]').getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height}})()"))
    b.close()
print(f'{N[0] - len(FAIL)} of {N[0]} checks passed'); srv.shutdown(); sys.exit(1 if FAIL else 0)
