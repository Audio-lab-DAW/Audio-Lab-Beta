# task WS-0d: screenshots of the final pick page and its console errors.
# usage: python3 shot4.py <abs path to start4.html> <out dir> [stage|times|cards|bench|all] [ids,comma separated]
# stage: every drawing in the start screen (W1) at 100 % (1254 x 651), Dark, then Light and Reduce motion. times: each drawing in the band at several times of its
# own clock. cards: the grid. bench: ms per picture. all: everything, plus the phone-width check.
import sys,json
from playwright.sync_api import sync_playwright
page,out=sys.argv[1],sys.argv[2];what=sys.argv[3] if len(sys.argv)>3 else 'all';only=sys.argv[4].split(',') if len(sys.argv)>4 else None
TIMES={'PH4':[4,11.6,17,24,30,36.5,42,49],'FS1':[3,6.6,10.3,15,21.5],'N1':[.2,.6,8.14,16.1,24.3,32.08,40.72],'N2':[.5,1.0,1.18,1.6,3,10.4,19.6,28.5],'N4':[5,10.9,15,25,35,46,55]}
with sync_playwright() as p:
    b=p.chromium.launch();errs=[]
    ctx=b.new_context(viewport={'width':1312,'height':1000},color_scheme='dark',device_scale_factor=1);pg=ctx.new_page()
    pg.on('console',lambda m: errs.append(m.text) if m.type=='error' else None);pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto('file://'+page);pg.wait_for_timeout(1200);pg.add_style_tag(content='.pbar{display:none!important}')
    ids=only or pg.evaluate("ITEMS.map(i=>i[0]).concat(KEPT.map(i=>i[0]))");mk=pg.locator('.mkw')
    if what in('stage','all'):
        for i in ids:
            pg.evaluate(f"show('{i}')");pg.wait_for_timeout(2400);mk.screenshot(path=f'{out}/w1_{i}.png')
        pg.click('header [data-sw="mode"] button[data-v="light"]');pg.wait_for_timeout(300)
        for i in ids:
            pg.evaluate(f"show('{i}')");pg.wait_for_timeout(350);pg.locator('.band').screenshot(path=f'{out}/light_{i}.png')
        pg.click('header [data-sw="mode"] button[data-v="dark"]');pg.click('header [data-sw="motion"] button[data-v="still"]');pg.wait_for_timeout(300)
        for i in ids:
            pg.evaluate(f"show('{i}')");pg.wait_for_timeout(350);pg.locator('.band').screenshot(path=f'{out}/still_{i}.png')
        pg.click('header [data-sw="motion"] button[data-v="on"]')
    if what in('times',):
        for i in ids:
            for t in TIMES.get(i,[20,40]):
                pg.evaluate(f"__at('{i}',{t})");pg.wait_for_timeout(260);pg.locator('.band').screenshot(path=f'{out}/t_{i}_{t}.png')
                c=pg.locator(f'.dc[data-id="{i}"] .dv')
                if c.count():c.scroll_into_view_if_needed();pg.evaluate(f"__at('{i}',{t})");pg.wait_for_timeout(260);c.screenshot(path=f'{out}/c_{i}_{t}.png');mk.scroll_into_view_if_needed()
    if what in('cards','all'):
        g=pg.locator('#grid');n=pg.locator('#grid .dc').count()
        for j in range(0,n,6):
            pg.locator('#grid .dc').nth(j).scroll_into_view_if_needed();pg.wait_for_timeout(2500);pg.screenshot(path=f'{out}/cards_{j//6}.png')
        pg.evaluate('scrollTo(0,0)');pg.wait_for_timeout(400);pg.screenshot(path=f'{out}/top.png')
    if what in('bench','all'):
        print('bench',json.dumps(pg.evaluate('__bench(240)')))
    print('line',pg.locator('#pline').inner_text());ctx.close()
    if what=='all':
        ctx=b.new_context(viewport={'width':400,'height':800},color_scheme='light',device_scale_factor=2);pg=ctx.new_page();pg.on('pageerror',lambda e:errs.append('phone: '+str(e)))
        pg.goto('file://'+page);pg.wait_for_timeout(1500);print('phone overflow',pg.evaluate('document.documentElement.scrollWidth-innerWidth'));pg.screenshot(path=f'{out}/phone.png');ctx.close()
    print('errors',errs)
