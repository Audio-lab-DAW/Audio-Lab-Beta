"""Task UX1: open the pick page headless, try every mock-up once, report console errors, take screenshots (dark and light, desktop and phone)."""
import sys
from playwright.sync_api import sync_playwright
P = sys.argv[1] if len(sys.argv) > 1 else 'speed-feel.html'; OUT = sys.argv[2] if len(sys.argv) > 2 else '.'
html = '<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"></head><body>' + open(P, encoding='utf-8').read() + '</body></html>'
with sync_playwright() as p:
    b = p.chromium.launch(); errs = []
    for scheme, w, h, name in (('dark', 1400, 900, 'desk-dark'), ('light', 1400, 900, 'desk-light'), ('dark', 400, 800, 'phone-dark')):
        pg = b.new_page(viewport={'width': w, 'height': h}, color_scheme=scheme)
        pg.on('pageerror', lambda e: errs.append(name + ': ' + str(e)))
        pg.on('console', lambda m: errs.append(name + ' console: ' + m.text) if m.type == 'error' else None)
        pg.set_content(html); pg.wait_for_timeout(1200)
        if name == 'desk-dark':
            pg.click('#m1 [data-a=dup]'); pg.click('#m1 [data-a=del]')
            pg.focus('#q3'); pg.keyboard.type('rev'); pg.keyboard.press('ArrowDown'); pg.keyboard.press('Enter')
            pg.click('#m5 .hrow[data-n=Bass]', button='right'); pg.click('#m5 .menu [data-to=Kick]')
            pg.focus('#m7'); [pg.keyboard.press(k) for k in ('s', ']', 'g', 'm', 'Enter')]
            pg.focus('#m8'); [pg.keyboard.press(k) for k in ('1', '5', 'Control+d', '.')]
            pg.click('#m9 [data-a=pinch]'); pg.click('#m12 [data-a="1"]'); pg.click('#m13 [data-a=run]'); pg.wait_for_timeout(4500)
            pg.focus('#m15'); [pg.keyboard.press(k) for k in 'asdf']
            pg.wait_for_timeout(500); print('m9', pg.inner_text('#l9a'), pg.inner_text('#l9b')); print('m13', pg.inner_text('#a13'), '|', pg.inner_text('#b13'), '| m14', pg.inner_text('#t14'), '| m3', pg.inner_text('#c3'), '| m15', pg.inner_text('#c15'), '| m8', pg.inner_text('#m8 .count'))
            print('overflow', pg.evaluate("document.documentElement.scrollWidth>innerWidth"))
        if name == 'phone-dark': print('phone overflow', pg.evaluate("document.documentElement.scrollWidth-innerWidth"))
        pg.screenshot(path=f'{OUT}/ux1-{name}.png', full_page=True); pg.close()
    print('errors', errs[:10]); b.close()
