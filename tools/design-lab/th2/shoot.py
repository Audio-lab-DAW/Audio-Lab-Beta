"""Render the pick page headless and save pictures for review: every version's stage at 100 % (1600 x 806), and the page itself.
  python3 shoot.py OUTDIR [id ...]"""
import sys, os, base64, asyncio
from playwright.async_api import async_playwright
HERE = os.path.dirname(os.path.abspath(__file__))
out = sys.argv[1]; ids = sys.argv[2:]
os.makedirs(out, exist_ok=True)
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport=dict(width=1700, height=1000), device_scale_factor=1)
        errs = []
        pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None)
        pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('file://' + os.path.join(HERE, 'pick-page.html'))
        await pg.wait_for_timeout(2500)
        fonts = await pg.evaluate("['500 12px Inter','500 12px \"JetBrains Mono\"','500 12px \"IBM Plex Mono\"','600 12px \"Source Serif 4\"'].map(f=>document.fonts.check(f))")
        print('fonts loaded:', fonts, 'errors:', errs[:5])
        await pg.evaluate("live=false;full=true;document.querySelector('#cvwrap').classList.add('full')")
        all_ids = await pg.evaluate("TH.map(t=>t.id)")
        for i in (ids or all_ids):
            if i == 'page': continue
            d = await pg.evaluate("(id)=>{go(id);return document.querySelector('#cv').toDataURL('image/png')}", i)
            open(os.path.join(out, i + '.png'), 'wb').write(base64.b64decode(d.split(',')[1]))
        if not ids or 'page' in ids:
            await pg.evaluate("full=false;document.querySelector('#cvwrap').classList.remove('full');go('A1')")
            await pg.screenshot(path=os.path.join(out, 'page.png'), full_page=True)
        await b.close()
asyncio.run(main())
