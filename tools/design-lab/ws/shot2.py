# task WS-0b: screenshots of the round 2 pick page (sections, the hand-over at five moments, Light) and its console errors
import sys
from playwright.sync_api import sync_playwright
page,out=sys.argv[1],sys.argv[2]
with sync_playwright() as p:
    b=p.chromium.launch();errs=[]
    for theme in ('dark','light'):
        ctx=b.new_context(viewport={'width':1400,'height':900},color_scheme=theme,device_scale_factor=1);pg=ctx.new_page()
        pg.on('console',lambda m: errs.append(theme+': '+m.text) if m.type=='error' else None);pg.on('pageerror',lambda e:errs.append(theme+': '+str(e)))
        pg.goto('file://'+page);pg.wait_for_timeout(1500);pg.add_style_tag(content='.pbar{display:none!important}')
        for sid in ('fam-R','fam-F'):
            pg.locator('#'+sid).scroll_into_view_if_needed();pg.wait_for_timeout(700);pg.locator('#'+sid).screenshot(path=f'{out}/{theme}_{sid}.png')
        pg.locator('#fam-M').scroll_into_view_if_needed();pg.wait_for_timeout(300)
        if theme=='dark':
            for m in ('M1','M2','M3','M4'):
                pg.click(f'#mcards [data-id="{m}"]')
                for v in (0,250,500,750,1000):
                    pg.eval_on_selector('#scrub',f'(e)=>{{e.value={v};e.dispatchEvent(new Event("input"))}}');pg.wait_for_timeout(120)
                    pg.locator('#hmk').screenshot(path=f'{out}/hand_{m}_{v}.png')
            pg.click('#mcards [data-id="M1"]')
            pg.click('#view [data-v="band"]');pg.locator('#fam-R').scroll_into_view_if_needed();pg.wait_for_timeout(700);pg.locator('#fam-R').screenshot(path=f'{out}/dark_band.png')
        else:
            pg.click('#mtheme [data-v="light"]');pg.wait_for_timeout(3200);pg.locator('#hmk').screenshot(path=f'{out}/hand_light.png')
        print(theme,pg.locator('#pline').inner_text())
        ctx.close()
    print('errors',errs)
