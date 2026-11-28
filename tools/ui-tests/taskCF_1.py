"""Task CF-1 (lane P, comfort modes): the map's Hide button and its overlay (docs/comfort-build.md).
  python3 tools/ui-tests/taskCF_1.py [index.html] [out dir] [old index.html for the screenshot and frame-time comparison]
Checks: the map has a Hide button with a tooltip; with Hide off the app looks as before (screenshot equal to the old build outside the button);
Hide gives the map's space back (the stage reaches where the map was, no empty strip); the map stays hidden right after the click until the pointer
has left the edge; the pointer at the edge where the map is docked brings it up as an overlay at that edge (bottom of the window, at the top under
the tabs, at the top under the transport) over the arrangement, drawn as a face of the glass engine's floating layer, usable (the map canvas is what
is under the pointer, drawn at its size); it goes away when the pointer leaves; nothing draws the map while it is hidden; Escape puts it away;
Hide again re-docks it at the same place and size; the choice survives a reload; the command view.mapHide; reduced motion shows and hides at once;
Solid draws the overlay solid; idle frame time not worse than the old build; no console errors."""
import sys, os, json
from playwright.sync_api import sync_playwright
SRC = open(sys.argv[1] if len(sys.argv) > 1 else 'index.html', encoding='utf-8').read()
OUT = sys.argv[2] if len(sys.argv) > 2 else '.'; os.makedirs(OUT, exist_ok=True)
OLD = sys.argv[3] if len(sys.argv) > 3 else None
N = [0, 0]; FAIL = []
def ok(c, m, info=''):
    N[0] += 1
    if c: N[1] += 1; print('ok   ', m, info if info != '' else '')
    else: FAIL.append(m); print('FAIL ', m, info)
INIT = "if(!sessionStorage.getItem('cf1')){sessionStorage.setItem('cf1','1');localStorage.setItem('audiolab-ui',JSON.stringify({splash:false,lat3:1}))}"
VW, VH = 1800, 1000
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
def page(p, src, reduced=False):
    b = p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
    pg = b.new_page(viewport={'width': VW, 'height': VH}, reduced_motion='reduce' if reduced else 'no-preference'); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)[:300]))
    pg.on('console', lambda m: errs.append('console: ' + m.text[:300]) if m.type == 'error' and 'fetching the script' not in m.text else None)
    pg.add_init_script(INIT)
    def serve(r):
        u = r.request.url.split('?')[0]
        if u.endswith('/') or u.endswith('index.html'): return r.fulfill(body=src, content_type='text/html')
        f = os.path.join(ROOT, u.split('https://app.test/', 1)[1])
        if os.path.isfile(f): return r.fulfill(path=f)
        r.fulfill(status=404, body='')
    pg.route('https://app.test/**', serve)
    pg.goto('https://app.test/'); pg.wait_for_function('() => window.AudioLab && window.AudioLab.version', timeout=60000); pg.wait_for_timeout(3500)
    return b, pg, errs
FT = """new Promise(res=>{const t=[];let l=0;const f=n=>{if(l)t.push(n-l);l=n;if(t.length<120)requestAnimationFrame(f);else{t.sort((a,b)=>a-b);res([t[60],t[114]])}};requestAnimationFrame(f)})"""
def shot_cmp(a, b, box):
    from PIL import Image
    import numpy as np
    A = np.asarray(Image.open(a).convert('RGB')).astype(int); B = np.asarray(Image.open(b).convert('RGB')).astype(int)
    if A.shape != B.shape: return 1.0
    d = (abs(A - B).max(axis=2) > 12)
    if box:
        x, y, w, h = [int(round(v)) for v in box]; d[max(0, y - 2):y + h + 2, max(0, x - 2):x + w + 2] = False
    return float(d.mean())
with sync_playwright() as p:
    ref_ft = None
    if OLD:
        b0, pg0, e0 = page(p, open(OLD, encoding='utf-8').read())
        pg0.mouse.move(900, 400); pg0.wait_for_timeout(1500)
        pg0.screenshot(path=os.path.join(OUT, 'cf1_old.png')); ref_ft = pg0.evaluate(FT); b0.close()
    b, pg, errs = page(p, SRC)
    R = lambda c: pg.evaluate('c => AudioLab.run(c)', c); J = lambda c: json.loads(R('JSON.stringify(' + c + ')'))
    ok(tuple(map(int, R('VERSION').split('.'))) >= (0, 295), 'version 0.295 or later', R('VERSION'))
    BOX = "(s=>{const e=document.querySelector(s);if(!e||!e.getClientRects().length)return null;const r=e.getBoundingClientRect();return[r.left,r.top,r.width,r.height]})"
    box = lambda s: J(BOX + "('%s')" % s)
    bt = J("(()=>{const b=document.getElementById('cfMapHide');return b&&{t:b.textContent,tt:b.title,in:b.parentElement.id,p:b.getAttribute('aria-pressed')}})()")
    ok(bt and bt['t'] == 'Hide' and bt['in'] == 'mapw' and len(bt['tt']) > 40 and bt['p'] == 'false', 'the map has a Hide button with a tooltip', bt)
    ok('—' not in bt['tt'], 'no em dash in the tooltip')
    ok(J("!UI.cfMapHide&&!document.body.classList.contains('cfmh')"), 'Hide is off by default')
    pg.mouse.move(900, 400); pg.wait_for_timeout(1500)
    pg.screenshot(path=os.path.join(OUT, 'cf1_new_docked.png'))
    if OLD:
        fr = shot_cmp(os.path.join(OUT, 'cf1_old.png'), os.path.join(OUT, 'cf1_new_docked.png'), box('#cfMapHide'))
        ok(fr < 0.002, 'Hide off: the window looks as before outside the new button', '%.5f of pixels differ' % fr)
    M0 = box('#mapw'); ST0 = box('#stage'); A0 = J("arr.height")
    # hide
    c = box('#cfMapHide'); pg.mouse.click(c[0] + c[2] / 2, c[1] + c[3] / 2); pg.wait_for_timeout(400)
    st = J("(()=>{const m=document.getElementById('mapw'),s=document.getElementById('stage').getBoundingClientRect(),bo=document.getElementById('botOut').getBoundingClientRect();return{h:document.body.classList.contains('cfmh'),ui:UI.cfMapHide,vis:m.getClientRects().length>0,sb:s.bottom,bo:bo.height,ih:innerHeight}})()")
    ok(st['h'] and st['ui'] and not st['vis'], 'Hide: the map is hidden and the choice is in UI.cfMapHide', st)
    ok(abs(st['sb'] - st['ih']) < 1.5 and st['bo'] < 1, 'the map\'s space is given back: the stage reaches the bottom of the window, no empty strip', st)
    pg.wait_for_timeout(300); A1 = J("arr.height")
    ok(A1 > A0, 'the arrangement canvas is taller', (A0, A1))
    ok(J("CF.show") is False, 'right after the click the map stays hidden (the pointer is still at the edge)')
    pg.screenshot(path=os.path.join(OUT, 'cf1_hidden.png'))
    # nothing draws the map while hidden
    R("(()=>{MAPK='';dirty=true;return 1})()"); pg.wait_for_timeout(500)
    ok(J("MAPK") == '', 'while hidden nothing draws the map (MAPK stays empty)')
    def reveal_at(y, name):
        pg.mouse.move(900, VH * 0.45, steps=2); pg.wait_for_timeout(150)
        pg.mouse.move(900, y, steps=4); pg.wait_for_timeout(450)
        s = J("(()=>{const m=document.getElementById('mapw'),r=m.getBoundingClientRect();return{show:CF.show,on:m.classList.contains('cfin'),r:[r.left,r.top,r.width,r.height],e:CF.edge,face:(GLF.items||[]).some(i=>i.el===m),pos:getComputedStyle(m).position,z:getComputedStyle(m).zIndex,mk:MAPK!==''}})()")
        pg.screenshot(path=os.path.join(OUT, 'cf1_' + name + '.png'))
        return s
    s = reveal_at(VH - 2, 'shown_bottom')
    ok(s['show'] and s['on'] and s['pos'] == 'fixed', 'map at the bottom: the pointer at the window\'s bottom edge brings the map up as an overlay', s)
    ok(abs(s['r'][1] + s['r'][3] - VH) < 12 and abs(s['r'][3] - M0[3]) < 3, 'it rises from the bottom edge at its docked height', (s['r'], M0))
    ok(s['face'] or J("!GLE.on||!!GLF.fail"), 'the overlay is a glass face of the floating layer (glass engine, no backdrop-filter)', s['face'])
    ok(J("getComputedStyle(document.getElementById('mapw')).backdropFilter") in ('none', '', None), 'no backdrop-filter on the overlay')
    ok(s['mk'], 'the shown map is drawn')
    # usable: the canvas is under the pointer, a double-click (fit everything) reaches the map
    mc = box('#map'); hit = J("(()=>{const e=document.elementFromPoint(%f,%f);return e&&e.id})()" % (mc[0] + mc[2] / 2, mc[1] + mc[3] / 2))
    ok(hit == 'map', 'the map canvas is what is under the pointer in the overlay', hit)
    pg.mouse.move(mc[0] + mc[2] / 2, mc[1] + mc[3] / 2, steps=3); pg.wait_for_timeout(300)
    ok(J("CF.show"), 'moving onto the map keeps it up')
    vx0 = J("V.x"); pg.mouse.down(); pg.mouse.move(mc[0] + mc[2] / 2 + 120, mc[1] + mc[3] / 2, steps=6); pg.mouse.up(); pg.wait_for_timeout(300)
    ok(J("CF.show"), 'dragging in the map keeps it up', (vx0, J("V.x")))
    R("(()=>{V.x=%s;dirty=true;return 1})()" % json.dumps(vx0))
    # leave
    pg.mouse.move(900, VH * 0.4, steps=4); pg.wait_for_timeout(400)
    ok(J("!CF.show&&!document.getElementById('mapw').classList.contains('cfon')"), 'the map goes away when the pointer leaves')
    # Escape
    s = reveal_at(VH - 2, 'shown_bottom2'); pg.keyboard.press('Escape'); pg.wait_for_timeout(300)
    ok(s['show'] and J("!CF.show"), 'Escape puts the shown map away')
    # map on top, under the tabs
    R("(()=>{UI.order=['map','arr','fx','tr'];applyLayout();return 1})()"); pg.wait_for_timeout(500)
    e = J("cfMapEdge(true)"); ok(e and e['top'], 'map on top: the edge is at the top', e)
    s = reveal_at(e['y'] + 2, 'shown_top')
    ok(s['show'] and abs(s['r'][1] - e['y']) < 12, 'map on top: the pointer at its edge brings it down from there', (s['r'], e))
    pg.mouse.move(900, VH * 0.7, steps=4); pg.wait_for_timeout(400); ok(J("!CF.show"), 'map on top: it goes away when the pointer leaves')
    st = J("(()=>{const s=document.getElementById('stage').getBoundingClientRect(),t=document.getElementById('topOut').getBoundingClientRect();return{st:s.top,tb:t.bottom,th:t.height}})()")
    ok(st['th'] < 1 and abs(st['st'] - st['tb']) < 1.5, 'map on top, hidden: no empty strip above the arrangement', st)
    # Ableton style: transport above the map
    R("(()=>{UI.order=['tr','map','arr','fx'];applyLayout();return 1})()"); pg.wait_for_timeout(500)
    e = J("cfMapEdge(true)"); trb = box('#tr')
    ok(e and e['top'] and abs(e['y'] - (trb[1] + trb[3])) < 2, 'transport above the map: the edge is under the transport', (e, trb))
    s = reveal_at(e['y'] + 1, 'shown_under_transport')
    ok(s['show'] and abs(s['r'][1] - e['y']) < 12, 'it comes down from under the transport', s['r'])
    pg.mouse.move(900, VH * 0.7, steps=4); pg.wait_for_timeout(400); ok(J("!CF.show"), 'and goes away when the pointer leaves')
    # map in the middle of the bottom zone: arrangement, map, then devices outside under it
    R("(()=>{UI.order=['arr','map','fx','tr'];applyLayout();return 1})()"); pg.wait_for_timeout(500)
    e = J("cfMapEdge(true)")
    ok(e and not e['top'] and e['y'] < VH - 20, 'map docked above other panels at the bottom: the edge is the top of what is under it', e)
    s = reveal_at(e['y'] - 2, 'shown_mid_bottom')
    ok(s['show'] and abs(s['r'][1] + s['r'][3] - e['y']) < 12, 'it rises from that edge', (s['r'], e))
    pg.mouse.move(900, VH * 0.3, steps=4); pg.wait_for_timeout(400); ok(J("!CF.show"), 'and goes away when the pointer leaves')
    R("(()=>{UI.order=['arr','fx','tr','map'];applyLayout();return 1})()"); pg.wait_for_timeout(500)
    # Solid: the overlay is solid
    R("(()=>{document.body.classList.add('gls');return 1})()"); s = reveal_at(VH - 2, 'shown_solid')
    bg = J("getComputedStyle(document.getElementById('mapw')).backgroundColor"); R("(()=>{document.body.classList.remove('gls');return 1})()")
    ok(s['show'] and bg.startswith('rgb(') , 'Solid: the overlay is drawn solid', bg)
    pg.mouse.move(900, VH * 0.4, steps=3); pg.wait_for_timeout(400)
    # remembered over a reload
    pg.reload(); pg.wait_for_function('() => window.AudioLab && window.AudioLab.version', timeout=60000); pg.wait_for_timeout(3000)
    ok(J("UI.cfMapHide===true&&document.body.classList.contains('cfmh')&&document.getElementById('cfMapHide').getAttribute('aria-pressed')==='true'"), 'Hide is remembered over a reload')
    ft_hidden = pg.evaluate(FT)
    # re-dock with the button in the overlay
    s = reveal_at(VH - 2, 'shown_after_reload'); c = box('#cfMapHide')
    ok(s['show'] and c is not None, 'after the reload the map comes up at the edge, with its Hide button', c)
    pg.mouse.move(c[0] + c[2] / 2, c[1] + c[3] / 2, steps=3); pg.mouse.click(c[0] + c[2] / 2, c[1] + c[3] / 2); pg.wait_for_timeout(500)
    M1 = box('#mapw'); st = J("(()=>{const m=document.getElementById('mapw');return{h:document.body.classList.contains('cfmh'),pos:getComputedStyle(m).position,cls:m.className,top:m.style.top,bot:m.style.bottom,p:m.parentElement.id}})()")
    ok(not st['h'] and st['pos'] == 'relative' and not st['top'] and not st['bot'] and 'cfon' not in st['cls'], 'Hide again puts the map back in its docked place', st)
    ok(M1 and all(abs(M1[i] - M0[i]) < 1.5 for i in range(4)), 'same place and size as before', (M0, M1))
    # the command
    ok(J("xtCommandId('view.mapHide')") == 'view.mapHide', 'the command view.mapHide is in the registry')
    pg.mouse.move(900, VH * 0.4, steps=2); pg.wait_for_timeout(12000)
    R("(()=>{MAPK='';dirty=true;return 1})()"); pg.wait_for_timeout(600)  # the map drawn fresh, as a re-dock draws it
    pg.screenshot(path=os.path.join(OUT, 'cf1_docked2.png'))
    R("runCommand('view.mapHide')"); pg.wait_for_timeout(400); a = J("!!UI.cfMapHide"); R("runCommand('view.mapHide')"); pg.wait_for_timeout(1200)
    ok(a and J("!UI.cfMapHide&&!document.body.classList.contains('cfmh')"), 'view.mapHide hides and puts it back')
    pg.screenshot(path=os.path.join(OUT, 'cf1_redocked.png'))
    fr = shot_cmp(os.path.join(OUT, 'cf1_docked2.png'), os.path.join(OUT, 'cf1_redocked.png'), None)
    ok(fr < 0.002, 'hidden and re-docked, the window looks exactly as before', '%.5f' % fr)
    ft_new = pg.evaluate(FT)
    if ref_ft:
        ok(ft_new[0] <= ref_ft[0] * 1.25 + 2 and ft_hidden[0] <= ref_ft[0] * 1.25 + 2, 'idle frame time not worse (p50, ms: old, new docked, new hidden)', (ref_ft, ft_new, ft_hidden))
    ok(not errs, 'no console errors', errs[:4])
    b.close()
    # reduced motion: at once
    b, pg, errs = page(p, SRC, reduced=True); R = lambda c: pg.evaluate('c => AudioLab.run(c)', c); J = lambda c: json.loads(R('JSON.stringify(' + c + ')'))
    R("(()=>{UI.cfMapHide=true;cfMapApply();CF.arm=true;return 1})()"); pg.mouse.move(900, 400); pg.wait_for_timeout(100)
    pg.mouse.move(900, VH - 2); pg.wait_for_timeout(30)
    s = J("(()=>{const m=document.getElementById('mapw');return{show:CF.show,mo:CF.mo,tr:getComputedStyle(m).transitionDuration}})()")
    ok(s['show'] and s['mo'] == 0 and all(float(x.strip()[:-1] or 0) < 0.001 for x in s['tr'].split(',')), 'reduced motion: the map comes up at once, no transition', s)
    pg.mouse.move(900, 400); pg.wait_for_timeout(30)
    ok(J("!CF.show&&!document.getElementById('mapw').classList.contains('cfon')"), 'reduced motion: it goes away at once')
    R("(()=>{UI.cfMapHide=false;cfMapApply();saveUI();return 1})()")
    ok(not errs, 'no console errors (reduced motion)', errs[:4])
    b.close()
print('%d of %d passed' % (N[1], N[0]))
if FAIL: print('FAILED:', FAIL); sys.exit(1)
