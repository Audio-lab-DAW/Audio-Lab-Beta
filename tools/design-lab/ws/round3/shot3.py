# task WS-0c: screenshots of the round 3 pick page and its console errors.
# usage: python3 shot3.py <abs path to start3.html> <out dir> [stage|cards|bench|all]
# stage: every drawing in the start screen (W1) at 100 % (1254 x 651), Dark; Light and Reduce motion for a few. cards: each family's cards. bench: ms per picture.
import sys,json
from playwright.sync_api import sync_playwright
page,out=sys.argv[1],sys.argv[2];what=sys.argv[3] if len(sys.argv)>3 else 'all'
with sync_playwright() as p:
    b=p.chromium.launch();errs=[]
    ctx=b.new_context(viewport={'width':1312,'height':900},color_scheme='dark',device_scale_factor=1);pg=ctx.new_page()
    pg.on('console',lambda m: errs.append(m.text) if m.type=='error' else None);pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto('file://'+page);pg.wait_for_timeout(1200);pg.add_style_tag(content='.pbar{display:none!important}')
    fams=pg.evaluate("Object.fromEntries(Object.entries(FAM).map(([f,v])=>[f,v.items.map(i=>i[0])]))")
    if what in('stage','all'):
        for f,ids in fams.items():
            st=pg.locator(f'.stage[data-fam="{f}"]');st.scroll_into_view_if_needed()
            for i in ids:
                st.locator(f'.tabs button[data-id="{i}"]').click();pg.wait_for_timeout(2600);st.locator('.mkw').screenshot(path=f'{out}/w1_{i}.png')
        pg.click('header [data-sw="mode"] button[data-v="light"]');pg.wait_for_timeout(300)
        for f,ids in fams.items():
            st=pg.locator(f'.stage[data-fam="{f}"]');st.scroll_into_view_if_needed()
            for i in ids[1:]:
                st.locator(f'.tabs button[data-id="{i}"]').click();pg.wait_for_timeout(250);st.locator('.mkw').screenshot(path=f'{out}/w1_light_{i}.png')
        pg.click('header [data-sw="mode"] button[data-v="dark"]');pg.click('header [data-sw="motion"] button[data-v="still"]');pg.wait_for_timeout(300)
        for f,ids in fams.items():
            st=pg.locator(f'.stage[data-fam="{f}"]');st.scroll_into_view_if_needed();pg.wait_for_timeout(250);st.locator('.mkw').screenshot(path=f'{out}/w1_still_{f}.png')
        pg.click('header [data-sw="motion"] button[data-v="on"]')
    if what in('cards','all'):
        for f in fams:
            g=pg.locator(f'[data-cards="{f}"]');g.scroll_into_view_if_needed();pg.wait_for_timeout(2500);g.screenshot(path=f'{out}/cards_{f}.png')
        pg.locator('header.top').screenshot(path=f'{out}/header.png')
    if what in('bench','all'):
        print('bench',json.dumps(pg.evaluate('__bench(240)')))
    print('line',pg.locator('#pline').inner_text());ctx.close()
    if what=='all':
        ctx=b.new_context(viewport={'width':400,'height':800},color_scheme='light',device_scale_factor=2);pg=ctx.new_page();pg.on('pageerror',lambda e:errs.append('phone: '+str(e)))
        pg.goto('file://'+page);pg.wait_for_timeout(1500);print('phone overflow',pg.evaluate('document.documentElement.scrollWidth-innerWidth'));pg.screenshot(path=f'{out}/phone.png');ctx.close()
    print('errors',errs)
