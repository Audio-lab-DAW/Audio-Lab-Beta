#!/usr/bin/env python3
"""Task UX2: headless check of the pick page (1280 px at 1x and 1.75x, 400 px phone): console errors, horizontal scroll, every pick button, screenshots.
   python3 -m http.server 8765 --bind 127.0.0.1   (repo root)   then   python3 tools/design-lab/ux2/check.py [outdir]"""
import sys, os
from playwright.sync_api import sync_playwright
OUT = sys.argv[1] if len(sys.argv) > 1 else 'ux2-check'; os.makedirs(OUT, exist_ok=True)
URL = 'http://127.0.0.1:8765/tools/design-lab/ux2/long-sessions.html'
with sync_playwright() as p:
    b = p.chromium.launch(args=['--no-proxy-server'])
    for name, vw, dsf in (('1280', 1280, 1), ('1280x175', 1280, 1.75), ('phone', 400, 2)):
        pg = b.new_context(viewport={'width': vw, 'height': 900}, device_scale_factor=dsf).new_page()
        errs = []; pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None); pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.route('**/fonts.g*/**', lambda r: r.abort())
        pg.goto(URL); pg.wait_for_timeout(2500)
        sw = pg.evaluate('document.documentElement.scrollWidth'); print(name, 'scrollWidth', sw, 'errors', [e for e in errs if 'fonts' not in e][:5])
        if name == '1280':
            for btn in pg.query_selector_all('.pick'): btn.click()
            print('line:', pg.inner_text('#line'))
            pg.click('#clear'); pg.wait_for_timeout(200)
            for i in ['E2', 'E4', 'E6', 'E10', 'E14', 'E18']: pg.click(f'#o{i} .pick')
            print('line:', pg.inner_text('#line')); pg.wait_for_timeout(800)
            pg.screenshot(path=f'{OUT}/{name}-top.png')
            for i in ['oE2', 'oE6', 'oE10', 'oE16', 'oE21']:
                pg.eval_on_selector('#' + i, 'e=>e.scrollIntoView()'); pg.wait_for_timeout(900); pg.screenshot(path=f'{OUT}/{name}-{i}.png')
            print('readouts:', pg.evaluate("[...document.querySelectorAll('.ro')].map(e=>e.textContent.slice(0,110))"))
        else:
            pg.screenshot(path=f'{OUT}/{name}-top.png', full_page=False)
        pg.close()
    b.close()
