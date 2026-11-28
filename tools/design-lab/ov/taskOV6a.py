#!/usr/bin/env python3
"""Task OV6a (lane F, overlays, pick T3): tooltips as callouts with a leader. Times (500 ms, warm 300 ms), the card's parts (name, key,
value, sentence, DEFAULT and SCOPE), the leader touching control and card, hover onto the card keeps it, Esc hides it, keyboard focus
shows it with aria-describedby, menu rows put it beside the menu, no text lost for any control with a tooltip, tooltips off, Light mode,
Solid, reduced motion, open time; no console errors.
   python3 tools/ui-tests/taskOV6a.py [index.html] [shots-dir]
At the user's size (2194 x 1139 CSS px at 1.75x) with Fractals. SwiftShader: times for comparison only."""
import sys, os, json, re
from playwright.sync_api import sync_playwright
F = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
OUT = sys.argv[2] if len(sys.argv) > 2 else ''
SRC = open(F, encoding='utf-8').read()
ARGS = ["--autoplay-policy=no-user-gesture-required", "--enable-gpu-rasterization", "--ignore-gpu-blocklist", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"]
INIT = "if(!localStorage.getItem('audiolab-ui'))localStorage.setItem('audiolab-ui',JSON.stringify({splash:false,lat3:1}))"
FAIL = []; N = [0]
def ok(c, m, d=''):
    N[0] += 1; print(('ok   ' if c else 'FAIL ') + m + (('   ' + str(d)) if d != '' else ''), flush=True)
    if not c: FAIL.append(m)

def load(p, logs, reduced=False):
    b = p.chromium.launch(args=ARGS)
    ctx = b.new_context(viewport={'width': 2194, 'height': 1139}, device_scale_factor=1.75, reduced_motion='reduce' if reduced else 'no-preference'); pg = ctx.new_page()
    pg.on('console', lambda m: logs.append(m.text[:300]) if m.type == 'error' and 'fetching the script' not in m.text else None)
    pg.on('pageerror', lambda e: logs.append('pageerror: ' + str(e)[:300]))
    pg.route('https://app.test/**', lambda r: r.fulfill(status=200, content_type='text/html', body=SRC) if r.request.url.endswith('.html') else r.fulfill(status=404, body=''))
    pg.add_init_script(INIT); pg.goto('https://app.test/index.html'); pg.wait_for_function("()=>window.AudioLab&&window.AudioLab.version", timeout=90000); pg.wait_for_timeout(3000)
    pg.evaluate("()=>{for(const i of['splash','liteNote']){const s=document.getElementById(i);if(s)s.remove()}}")
    R = lambda c: pg.evaluate("c=>AudioLab.run(c)", c)
    R("pmSetOn(false)"); R("openDemoFractals()"); pg.wait_for_timeout(6000)
    return b, pg, R

VIS = "(()=>{const t=document.getElementById('tip');return!!t&&t.classList.contains('ovt3')})()"
CARD = "(()=>{const t=document.getElementById('tip'),l=document.getElementById('ovLead'),q=s=>{const e=t.querySelector(s);return e?e.textContent:''};const r=t.getBoundingClientRect(),lr=l&&!l.hidden?l.getBoundingClientRect():null;return{vis:t.classList.contains('ovt3'),hov:t.classList.contains('hov'),still:t.classList.contains('still'),nm:q('.ovtn span'),key:q('.ovtn kbd'),val:q('.ovtv'),unit:q('.ovtv u'),tx:q('.ovtx'),df:q('.ovtd'),r:[r.left,r.top,r.right,r.bottom],lead:lr&&[lr.left,lr.top,lr.right,lr.bottom],lcls:l?l.className:'',bf:getComputedStyle(t).backdropFilter,bg:getComputedStyle(t).backgroundColor,tr:getComputedStyle(t).transitionDuration}})()"

with sync_playwright() as p:
    logs = []
    b, pg, R = load(p, logs)
    J = lambda c: json.loads(R("JSON.stringify(" + c + ")"))
    print('version', R("VERSION"))
    ok(J("[ovMs('tipDelay'),ovMs('tipWarm'),ovLook().ms.tip]") == [500, 300, 80], 'times from LOOK: 500 ms, warm 300 ms, 80 ms fade')
    box = lambda s: pg.locator(s).bounding_box()
    mid = lambda bb: (bb['x'] + bb['width'] / 2, bb['y'] + bb['height'] / 2)
    pg.mouse.move(1100, 600); pg.wait_for_timeout(500)
    lb = box('#bLoop'); pg.mouse.move(*mid(lb)); pg.wait_for_timeout(330)
    ok(not J(VIS), 'nothing at 330 ms')
    pg.wait_for_timeout(400)
    c = J(CARD)
    pressed = J("document.getElementById('bLoop').getAttribute('aria-pressed')")
    ok(c['vis'] and c['hov'] and c['nm'].lower() == 'cycle' and c['key'] == '⇧L', 'after 500 ms: the callout, name CYCLE with its key ⇧L', (c['nm'], c['key']))
    ok(c['val'] == ('ON' if pressed == 'true' else 'OFF') and len(c['tx']) > 30, 'the value now (ON/OFF from the button) and the sentence', (c['val'], c['tx'][:50]))
    lt, ll = c['lead'], lb
    up = c['r'][3] <= lb['y']
    touch = lt and abs(lt[0] - (lb['x'] + lb['width'] / 2)) < 2 and ((abs(lt[1] - c['r'][3]) < 3 and abs(lt[3] - lb['y']) < 4) if up else (abs(lt[1] - (lb['y'] + lb['height'])) < 4 and abs(lt[3] - c['r'][1]) < 3))
    ok(touch and ('up' in c['lcls']) == up, 'the amber leader runs from the button to the card', (lt, c['r'], [lb['x'], lb['y']], c['lcls']))
    ok(J("document.getElementById('bLoop').getAttribute('aria-describedby')").split().count('tip') == 1 and J("document.getElementById('tip').getAttribute('role')") == 'tooltip', 'aria-describedby links it, role tooltip')
    ok(c['bf'] == 'none' and c['bg'].startswith('rgba(20, 21, 27') , 'drawn solid with the tokens, no backdrop-filter', (c['bf'], c['bg']))
    if OUT: pg.screenshot(path=os.path.join(OUT, 'ov6a_dark_loop.png'), clip={'x': lb['x'] - 250, 'y': c['r'][1] - 30, 'width': 560, 'height': lb['y'] - c['r'][1] + 80})
    # warm: the next one at once, the key from the shortcut list
    pb = box('#bPlay'); pg.mouse.move(*mid(pb)); pg.wait_for_timeout(70)
    c = J(CARD)
    ok(c['vis'] and c['nm'].lower() == 'play' and c['key'] == 'Space', 'warm: the next control within 300 ms shows at once (Play, Space)', (c['vis'], c['nm'], c['key']))
    ok(J("document.getElementById('bLoop').getAttribute('aria-describedby')") is None, 'the old control lost aria-describedby')
    # hover onto the card through the gap
    c = J(CARD); x0, y0 = mid(pb)
    tx_, ty_ = (c['r'][0] + c['r'][2]) / 2, (c['r'][1] + c['r'][3]) / 2
    pg.mouse.move(x0, (c['r'][1] + 4) if c['r'][1] > y0 else (c['r'][3] - 4), steps=8); pg.wait_for_timeout(80)
    pg.mouse.move(tx_, ty_, steps=6); pg.wait_for_timeout(600)
    ok(J(VIS) and J(CARD)['nm'].lower() == 'play', 'the pointer can move onto the card: it stays (can be read)')
    pg.mouse.move(1100, 500, steps=4); pg.wait_for_timeout(200)
    ok(not J(VIS) and J("document.getElementById('ovLead').hidden"), 'leaving the card hides it and its leader')
    # Esc
    pg.wait_for_timeout(400); pg.mouse.move(*mid(lb)); pg.wait_for_timeout(650)
    ok(J(VIS), 'shown again after 500 ms')
    pg.keyboard.press('Escape'); pg.wait_for_timeout(60)
    ok(not J(VIS), 'Esc hides it')
    pg.mouse.move(mid(lb)[0] + 3, mid(lb)[1] + 2); pg.wait_for_timeout(700)
    ok(not J(VIS), 'moving on the same control does not bring it back')
    pg.mouse.move(*mid(pb)); pg.wait_for_timeout(650)
    ok(J(VIS) and J(CARD)['nm'].lower() == 'play', 'another control shows its own')
    # pointerdown and wheel hide
    pg.mouse.move(1100, 500); pg.wait_for_timeout(500); pg.mouse.move(*mid(lb)); pg.wait_for_timeout(650)
    pg.mouse.wheel(0, 30); pg.wait_for_timeout(60)
    ok(not J(VIS), 'the wheel hides it')
    # keyboard focus
    pg.mouse.move(1100, 500); pg.wait_for_timeout(500)
    R("document.getElementById('bHome').focus()"); pg.wait_for_timeout(700)
    ok(not J(VIS), 'focus set by the code (no key) shows nothing')
    order = J("(()=>{const h=document.getElementById('bHome');const L=[...document.querySelectorAll('button,[tabindex]')].filter(e=>e.tabIndex>=0&&e.offsetParent);const i=L.indexOf(h);return L.slice(i+1,i+3).map(e=>e.id)})()")
    pg.keyboard.press('Tab'); pg.wait_for_timeout(300)
    f1 = J("document.activeElement.id")
    ok(not J(VIS), 'Tab: nothing yet at 300 ms', f1)
    pg.wait_for_timeout(350)
    c = J(CARD); has = J("(document.activeElement.getAttribute('aria-describedby')||'').split(' ').includes('tip')")
    ok(c['vis'] and not c['hov'] and has, 'Tab: the focused control shows its callout after 500 ms, linked by aria-describedby', (f1, c['nm']))
    pg.keyboard.press('Tab'); pg.wait_for_timeout(80)
    c2 = J(CARD); f2 = J("document.activeElement.id")
    ok(c2['vis'] and (c2['nm'] != c['nm'] or c2['tx'] != c['tx']), 'Tab again: the next one at once (warm)', (f2, c2['nm']))
    R("document.activeElement.blur()"); pg.wait_for_timeout(80)
    ok(not J(VIS), 'focus leaving hides it')
    # a menu row: beside the menu, leader sideways
    R("trackMenu(420,300,S.tracks[1],4)"); pg.wait_for_timeout(300)
    it = J("(()=>{const m=document.getElementById('ctxm');const e=[...m.querySelectorAll('[data-tip]')].filter(x=>x.offsetParent).sort((a,b)=>b.offsetWidth-a.offsetWidth)[0];if(!e)return null;const r=e.getBoundingClientRect(),mr=m.getBoundingClientRect();return{x:r.left+r.width/2,y:r.top+r.height/2,mr:[mr.left,mr.right]}})()")
    if it:
        pg.mouse.move(it['x'], it['y']); pg.wait_for_timeout(650)
        c = J(CARD)
        beside = c['vis'] and (c['r'][0] >= it['mr'][1] + 4 or c['r'][2] <= it['mr'][0] - 4)
        ok(beside and 'side' in c['lcls'] and c['lead'] and abs((c['lead'][1] + c['lead'][3]) / 2 - it['y']) < 14, 'a menu row: the card stands beside the menu (rows below stay visible), the leader runs sideways', (c['r'], it['mr'], c['lcls']))
        if OUT: pg.screenshot(path=os.path.join(OUT, 'ov6a_dark_menu.png'), clip={'x': 300, 'y': 200, 'width': 900, 'height': 700})
        ok(c['lead'] and abs(c['lead'][0] - it['mr'][1]) < 3, 'the sideways leader starts at the menu edge, not across other entries', (c['lead'], it['mr']))
        pg.mouse.move(c['r'][0] + 20, it['y'], steps=8); pg.wait_for_timeout(500)
        ok(J(VIS), 'the pointer can move from the menu row onto its card')
        pg.mouse.move(it['x'] + 2, it['y'] + 30, steps=3); pg.wait_for_timeout(100)
        ok(J("!document.getElementById('ctxm').hidden"), 'the menu stays open')
    else:
        ok(False, 'a menu row with a description to point at')
    R("closeMenu()"); pg.mouse.move(1100, 500); pg.wait_for_timeout(400)
    # no text lost: every visible control with a tooltip in the main window
    lost = J(r"""(()=>{const out=[];let n=0;const els=[...document.querySelectorAll('[title],[data-tip]')].filter(e=>e.offsetParent&&!e.closest('#set'));
      for(const sel in TIPS)for(const e of document.querySelectorAll(sel))if(e.offsetParent&&!els.includes(e))els.push(e);
      for(const e of els){const raw=tipText(e);if(!raw)continue;n++;const d=ovT3Parse(e,raw),got=(d.nm+' '+d.tx).toLowerCase(),p=raw.split('|');
        const words=((p[0]||'')+' '+(p[1]||'')).toLowerCase().replace(/\([^()]{1,16}\)/g,' ').split(/[^a-z0-9%]+/).filter(w=>w.length>2);
        const miss=words.filter(w=>!got.includes(w));if(miss.length)out.push([e.id||e.className,miss.slice(0,3)])}return{n,out:out.slice(0,6),bad:out.length}})()""")
    ok(lost['n'] > 80 and lost['bad'] == 0, 'no text lost: name and sentence hold every word of every tooltip in the window', lost)
    # Settings rows: DEFAULT and SCOPE from the settings table
    R("openSettings('general')"); pg.wait_for_timeout(700)
    row = J("(()=>{for(const r of document.querySelectorAll('#set [data-stid]')){if(!r.offsetParent)continue;const c=r.querySelector('input[type=checkbox],select,input[type=range]');const h=ST_HOOKS.helpFor(c||r);if(h&&h.def&&c){const b=c.getBoundingClientRect();if(b.width>4)return{id:r.dataset.stid,x:b.left+b.width/2,y:b.top+b.height/2,def:h.def,sc:h.scope}}}return null})()")
    if row:
        pg.mouse.move(row['x'], row['y']); pg.wait_for_timeout(700)
        c = J(CARD)
        ok(c['vis'] and c['df'].upper().startswith('DEFAULT') and (not row['sc'] or row['sc'].upper() in c['df'].upper()) and c['val'] != '', 'a Settings row: value now, DEFAULT and SCOPE from the settings table', (row['id'], c['val'], c['df']))
        if OUT: pg.screenshot(path=os.path.join(OUT, 'ov6a_dark_setting.png'), clip={'x': max(0, row['x'] - 400), 'y': max(0, row['y'] - 260), 'width': 800, 'height': 520})
    else:
        ok(False, 'a Settings row with a default to point at')
    R("closeSet()"); pg.mouse.move(1100, 500); pg.wait_for_timeout(400)
    # tooltips off
    R("UI.tips=false"); pg.mouse.move(*mid(lb)); pg.wait_for_timeout(700)
    ok(not J(VIS), 'Settings: tooltips off shows none')
    R("UI.tips=true"); pg.mouse.move(1100, 500); pg.wait_for_timeout(400)
    # an old direct caller (tipShow on an element of its own) still works
    R("(()=>{const e=document.createElement('div');e.id='ov6probe';e.dataset.tip='Probe|A direct caller';e.style.cssText='position:fixed;left:600px;top:400px;width:20px;height:20px';document.body.appendChild(e);tipShow(e)})()")
    c = J(CARD)
    ok(c['vis'] and not c['hov'] and c['nm'] == 'Probe' and c['tx'] == 'A direct caller', 'tipShow called directly (as the map and clip-name callers do) shows the card, not hoverable', c['nm'])
    R("tipHide();document.getElementById('ov6probe').remove()")
    # open time
    t = J(r"""(()=>{const e=document.getElementById('bLoop'),T=[];for(let i=0;i<15;i++){tipHide();const t0=performance.now();tipShow(e);T.push(performance.now()-t0)}tipHide();T.sort((a,b)=>a-b);return T[7]})()""")
    ok(t < 3, 'open call under 3 ms (median of 15)', round(t, 2))
    ok(not logs, 'no console errors (dark)', logs[:5])
    # Light mode
    R("pmSetOn(true)"); pg.wait_for_timeout(1200); pg.mouse.move(1100, 500); pg.wait_for_timeout(500); pg.mouse.move(*mid(lb)); pg.wait_for_timeout(700)
    c = J(CARD)
    ok(c['vis'] and c['still'] and all(float(x.strip()[:-1]) < 0.001 for x in c['tr'].split(',')) and 'still' in c['lcls'], 'Light mode: the callout without a fade', (c['still'], c['tr']))
    if OUT: pg.screenshot(path=os.path.join(OUT, 'ov6a_lite_loop.png'), clip={'x': lb['x'] - 250, 'y': c['r'][1] - 30, 'width': 560, 'height': lb['y'] - c['r'][1] + 80})
    R("pmSetOn(false)"); pg.mouse.move(1100, 500); pg.wait_for_timeout(1000)
    # Solid
    R("(()=>{UI.gl={...(UI.gl||{}),lv:'solid'};gleApply()})()"); pg.wait_for_timeout(800); pg.mouse.move(*mid(pb)); pg.wait_for_timeout(700)
    c = J(CARD)
    ok(c['vis'] and c['bf'] == 'none', 'Solid: the callout, no backdrop-filter')
    if OUT: pg.screenshot(path=os.path.join(OUT, 'ov6a_solid_play.png'), clip={'x': pb['x'] - 250, 'y': min(c['r'][1], pb['y']) - 30, 'width': 560, 'height': 420})
    R("(()=>{UI.gl={...(UI.gl||{}),lv:'glass'};gleApply()})()"); pg.mouse.move(1100, 500); pg.wait_for_timeout(500)
    ok(not logs, 'no console errors (Light mode, Solid)', logs[:5])
    b.close()
    logs2 = []
    b, pg, R = load(p, logs2, reduced=True)
    J = lambda c: json.loads(R("JSON.stringify(" + c + ")"))
    lb = pg.locator('#bLoop').bounding_box(); pg.mouse.move(lb['x'] + 10, lb['y'] + 10); pg.wait_for_timeout(700)
    c = J(CARD)
    ok(c['vis'] and c['still'] and all(float(x.strip()[:-1]) < 0.001 for x in c['tr'].split(',')), 'reduced motion: no fade', c['tr'])
    ok(not logs2, 'no console errors (reduced motion)', logs2[:5])
    b.close()
print(f'{N[0]-len(FAIL)} of {N[0]} passed' + ('' if not FAIL else ': FAILED ' + '; '.join(FAIL)))
sys.exit(1 if FAIL else 0)
