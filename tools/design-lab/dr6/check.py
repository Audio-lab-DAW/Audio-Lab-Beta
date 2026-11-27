"""DR6 pick page check: loads the page headless at 1280 px (1x, 1.75x, 2x) and 400 px, reports console errors,
clicks through every design and row option, and saves screenshots.
    python3 tools/design-lab/dr6/check.py [outdir]"""
import sys, os
from playwright.sync_api import sync_playwright
here = os.path.dirname(os.path.abspath(__file__))
page_path = os.path.join(here, 'arrangement-lines.html')
out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, 'shots')
os.makedirs(out, exist_ok=True)
html = '<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head><body>' + open(page_path, encoding='utf-8').read() + '</body></html>'
errs = []
with sync_playwright() as p:
    b = p.chromium.launch()
    for (w, h, dpr, tag) in [(1280, 900, 1, 'w1280-1x'), (1280, 900, 1.75, 'w1280-175x'), (1280, 900, 2, 'w1280-2x'), (400, 860, 2, 'w400')]:
        pg = b.new_page(viewport={'width': w, 'height': h}, device_scale_factor=dpr)
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' and 'fonts' not in m.text else None)
        pg.set_content(html)
        pg.wait_for_timeout(1200)
        pg.screenshot(path=os.path.join(out, f'{tag}-top.png'))
        if tag == 'w1280-1x':
            for lid in ['L0', 'L1', 'L2', 'L3', 'L4', 'L5', 'L6', 'L7', 'L8']:
                pg.click(f'#segL button[data-v="{lid}"]'); pg.wait_for_timeout(250)
                pg.locator('#stageCv').screenshot(path=os.path.join(out, f'stage-{lid}.png'))
            for k, ids in [('R', 5), ('P', 4), ('S', 4), ('T', 5), ('Z', 5)]:
                for i in range(ids):
                    pg.click(f'#seg{k} button[data-v="{k}{i}"]'); pg.wait_for_timeout(120)
            pg.click('#rec'); pg.wait_for_timeout(300)
            for z in ['song', '64', '4', '1']:
                pg.click(f'#segFit button[data-v="{z}"]'); pg.wait_for_timeout(300)
                pg.locator('#stageCv').screenshot(path=os.path.join(out, f'stage-rec-{z}.png'))
            pg.click('#segTheme button[data-v="light"]'); pg.wait_for_timeout(300)
            pg.locator('#stageCv').screenshot(path=os.path.join(out, 'stage-rec-light.png'))
            pg.click('#segTheme button[data-v="dark"]')
            # wheel zoom and drag a clip
            box = pg.locator('#stageCv').bounding_box()
            pg.mouse.move(box['x'] + 700, box['y'] + 300); pg.mouse.wheel(0, -300); pg.wait_for_timeout(200)
            pg.click('#segFit button[data-v="64"]'); pg.wait_for_timeout(200)
            for sec in ['gL', 'gR', 'gP', 'gS', 'gT', 'gZ', 'gPx']:
                pg.locator('#' + sec).scroll_into_view_if_needed(); pg.wait_for_timeout(400)
                pg.locator('#' + sec).screenshot(path=os.path.join(out, f'sec-{sec}.png'))
            print('line:', pg.inner_text('#line'), '| readout:', pg.inner_text('#readout'), '| cost:', pg.inner_text('#cost'))
        if tag == 'w1280-175x':
            pg.click('#rec'); pg.wait_for_timeout(300)
            pg.locator('#stageCv').screenshot(path=os.path.join(out, 'stage-rec-175x.png'))
            pg.locator('#gPx').scroll_into_view_if_needed(); pg.wait_for_timeout(300)
            pg.locator('#gPx').screenshot(path=os.path.join(out, 'sec-gPx-175x.png'))
        sw = pg.evaluate('document.documentElement.scrollWidth')
        print(tag, 'scrollWidth', sw, 'viewport', w)
        pg.close()
    b.close()
print('errors:', errs[:10] if errs else 'none')
