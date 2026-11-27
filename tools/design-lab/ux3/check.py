#!/usr/bin/env python3
"""Headless check of the learn mode pick page: console errors, each mock's main interaction, screenshots.
   python3 tools/design-lab/ux3/check.py <built.html> <shots dir>"""
import sys, os
from playwright.sync_api import sync_playwright
F, OUT = os.path.abspath(sys.argv[1]), sys.argv[2]; os.makedirs(OUT, exist_ok=True)
errs = []; ok = []
def chk(c, msg):
    (ok if c else errs).append(msg); print(('PASS ' if c else 'FAIL ') + msg, flush=True)
with sync_playwright() as p:
    b = p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required', '--no-proxy-server'])
    for W in (1280, 400):
        pg = b.new_context(viewport={'width': W, 'height': 900}).new_page()
        pg.route('**/fonts.g*/**', lambda r: r.abort())
        pg.on('pageerror', lambda e: errs.append('pageerror ' + str(e)))
        pg.on('console', lambda m: m.type == 'error' and 'fonts' not in m.text and errs.append('console ' + m.text))
        pg.goto('file://' + F); pg.wait_for_timeout(800)
        sw = pg.evaluate('document.documentElement.scrollWidth'); chk(sw <= W, f'{W}px: no horizontal scroll ({sw})')
        if W == 400:
            pg.screenshot(path=f'{OUT}/mobile.png'); continue
        # P: the decay step is running; turn decay down with the keyboard
        P = '#st-P .app'
        chk(pg.locator(f'{P} .gcard').count() == 1, 'P: a lesson card is shown')
        chk('Decay' in pg.inner_text(f'{P} .gcard') or 'shorter' in pg.inner_text(f'{P} .gcard'), 'P: card is on the Decay step')
        pg.locator('#st-P').scroll_into_view_if_needed(); pg.screenshot(path=f'{OUT}/P1.png', clip=pg.locator('#st-P').bounding_box())
        pg.focus(f'{P} [data-sl="bass.decay"]'); pg.keyboard.press('Home'); pg.wait_for_timeout(1500)
        t = pg.inner_text(f'{P} .gcard'); chk('Cutoff' in t, 'P: after Decay down the guide moved on to Cutoff by itself')
        # the knob was usable while pointed at (value changed)
        chk(pg.get_attribute(f'{P} [data-sl="bass.decay"]', 'aria-valuenow') == '20', 'P: knob stayed usable (20 ms)')
        for m in ('P0', 'P2', 'P3'):
            pg.click(f'#seg-P button[data-v="{m}"]'); pg.click('#p-restart'); pg.wait_for_timeout(300)
            pg.screenshot(path=f'{OUT}/{m}.png', clip=pg.locator('#st-P').bounding_box())
        # P0 blocks: drag on the knob does nothing
        pg.click('#seg-P button[data-v="P0"]'); pg.click('#p-restart'); pg.wait_for_timeout(200)
        pg.locator('#st-P').scroll_into_view_if_needed(); pg.wait_for_timeout(100)
        v0 = pg.get_attribute(f'{P} [data-sl="bass.decay"]', 'aria-valuenow')
        bb = pg.locator(f'{P} [data-sl="bass.decay"]').bounding_box(); pg.mouse.move(bb['x']+bb['width']/2, bb['y']+12); pg.mouse.down(); pg.mouse.move(bb['x']+bb['width']/2, bb['y']-60); pg.mouse.up()
        chk(pg.get_attribute(f'{P} [data-sl="bass.decay"]', 'aria-valuenow') == v0, 'P0: today\'s style blocks the knob')
        pg.click('#seg-P button[data-v="P1"]'); pg.click('#p-restart'); pg.wait_for_timeout(200)
        bb = pg.locator(f'{P} [data-sl="bass.decay"]').bounding_box(); pg.mouse.move(bb['x']+bb['width']/2, bb['y']+12); pg.mouse.down(); pg.mouse.move(bb['x']+bb['width']/2, bb['y']+80); pg.mouse.up()
        chk(pg.get_attribute(f'{P} [data-sl="bass.decay"]', 'aria-valuenow') != v0, 'P1: drag turns the knob under the guide')
        # card never covers its control
        cr = pg.locator(f'{P} .gcard').bounding_box(timeout=3000); kr = pg.locator(f'{P} [data-sl="bass.cutoff"]').bounding_box()
        inter = not (cr['x']+cr['width'] < kr['x'] or kr['x']+kr['width'] < cr['x'] or cr['y']+cr['height'] < kr['y'] or kr['y']+kr['height'] < cr['y'])
        chk(not inter, 'P1: card does not cover the control it points at')
        # H: help menu, search, show me
        H = '#st-H .app'
        pg.click('#seg-H button[data-v="H1"]'); pg.click(f'{H} [data-al="help.button"]'); pg.wait_for_timeout(200)
        chk(pg.locator(f'{H} .pop .row').count() >= 8, 'H1: help menu opens with rows')
        pg.locator('#st-H').scroll_into_view_if_needed(); pg.screenshot(path=f'{OUT}/H1.png', clip=pg.locator('#st-H').bounding_box())
        pg.keyboard.type('reso'); pg.wait_for_timeout(100); pg.screenshot(path=f'{OUT}/H1-search.png', clip=pg.locator('#st-H').bounding_box())
        pg.keyboard.press('Enter'); pg.wait_for_timeout(200)
        chk('Resonance' in pg.inner_text(f'{H} .gcard'), 'H1: search result points at Resonance')
        pg.screenshot(path=f'{OUT}/H1-showme.png', clip=pg.locator('#st-H').bounding_box())
        pg.keyboard.press('Escape')
        for m in ('H2', 'H3', 'H0'):
            pg.click(f'#seg-H button[data-v="{m}"]'); pg.click(f'{H} [data-al="help.button"]'); pg.wait_for_timeout(250)
            pg.screenshot(path=f'{OUT}/{m}.png', clip=pg.locator('#st-H').bounding_box())
            if m == 'H0': pg.click(f'{H} .blkbar button')
            elif m == 'H2': pg.click(f'{H} .side .x')
            else: pg.keyboard.press('Escape')
        pg.click('#seg-H button[data-v="H1"]')
        # W: identify, knob still works
        W1 = '#st-W .app'
        pg.click('#seg-W button[data-v="W1"]'); pg.click('#w-on'); pg.hover(f'{W1} [data-sl="pump.depth"]'); pg.wait_for_timeout(200)
        chk('Depth' in pg.inner_text(f'{W1} .gcard'), 'W1: hover shows Depth in a callout')
        pg.focus(f'{W1} [data-sl="pump.depth"]'); pg.keyboard.press('End'); pg.wait_for_timeout(200)
        chk('100' in pg.inner_text(f'{W1} .gcard .val'), 'W1: card value follows the knob (100 %)')
        pg.locator('#st-W').scroll_into_view_if_needed(); pg.hover(f'{W1} [data-sl="pump.depth"]'); pg.screenshot(path=f'{OUT}/W1.png', clip=pg.locator('#st-W').bounding_box())
        pg.keyboard.press('Escape')
        pg.click('#seg-W button[data-v="W3"]'); pg.click('#w-on'); pg.hover(f'{W1} [data-sl="bass.decay"]'); pg.wait_for_timeout(150)
        chk('Decay' in pg.inner_text(f'{W1} .hl'), 'W3: help line explains Decay'); pg.screenshot(path=f'{OUT}/W3.png', clip=pg.locator('#st-W').bounding_box()); pg.click('#w-on')
        pg.click('#seg-W button[data-v="W1"]')
        # L: lessons, shuffle, hide devices, already done
        L = '#st-L .app'
        pg.click('#seg-L button[data-v="L1"]'); pg.click('#lessonpick button[data-v="side"]'); pg.wait_for_timeout(200)
        chk('Play' in pg.inner_text(f'{L} .gcard'), 'L1: sidechain lesson starts at Play')
        pg.click(f'{L} [data-al="transport.play"]'); pg.wait_for_timeout(1400)
        chk('pump on' in pg.inner_text(f'{L} .gcard') or 'Sidechain pump' in pg.inner_text(f'{L} .gcard'), 'L1: Play detected, next step is the pump')
        pg.click(f'{L} [data-al="pump.power"]'); pg.wait_for_timeout(1400)
        chk('Duck' in pg.inner_text(f'{L} .gcard'), 'L1: pump on detected, next is Depth')
        pg.click('#shuffle'); pg.wait_for_timeout(200)
        cr = pg.locator(f'{L} .gring').bounding_box(); kr = pg.locator(f'{L} [data-sl="pump.depth"]').bounding_box()
        chk(abs(cr['x']+4*cr['width']/(kr['width']+8)-kr['x']) < 12 or abs(cr['x']-kr['x']) < 12, 'L: after shuffle the ring is still on Depth')
        pg.locator('#st-L').scroll_into_view_if_needed(); pg.screenshot(path=f'{OUT}/L1.png', clip=pg.locator('#st-L').bounding_box())
        pg.click('#hidedev'); pg.wait_for_timeout(200)
        chk('Not on screen' in pg.inner_text(f'{L} .gcard'), 'L: hidden devices: card offers to show them')
        pg.click(f'{L} .gcard [data-g="reveal"]'); pg.wait_for_timeout(200)
        chk(pg.locator(f'{L} .dev').is_visible(), 'L: reveal runs view.devices')
        pg.click(f'{L} [data-al="transport.play"]')
        pg.click('#seg-L button[data-v="L3"]'); pg.wait_for_timeout(200); pg.screenshot(path=f'{OUT}/L3.png', clip=pg.locator('#st-L').bounding_box())
        pg.click('#seg-L button[data-v="L2"]'); pg.wait_for_timeout(200); pg.screenshot(path=f'{OUT}/L2.png', clip=pg.locator('#st-L').bounding_box())
        pg.click('#seg-L button[data-v="L1"]')
        # picks bar
        pg.click('#rec'); chk(pg.inner_text('#pline').startswith('Learn picks: N1 H1 P1 W1 L1 G1'), 'picks bar: ★ line')
        pg.screenshot(path=f'{OUT}/page.png', full_page=False)
    b.close()
print('\n%d passed, %d problems' % (len(ok), len(errs)))
for e in errs: print('  ', e)
