import sys,asyncio
from playwright.sync_api import sync_playwright
p='file://'+sys.argv[1]
with sync_playwright() as pw:
  b=pw.chromium.launch();pg=b.new_page(viewport={'width':1400,'height':900},device_scale_factor=1)
  errs=[];pg.on('console',lambda m:errs.append(m.text) if m.type=='error' else None);pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.goto(p);pg.wait_for_timeout(1500)
  for i,el in enumerate(pg.query_selector_all('.mkw')):
    el.scroll_into_view_if_needed();pg.wait_for_timeout(400);el.screenshot(path=sys.argv[2]+'/m%d.png'%(i+1))
  # light W1 and a keyboard try on W3
  pg.click('.lay[data-id=W1] .sk button[data-v=light]');pg.wait_for_timeout(200);pg.query_selector_all('.mkw')[0].screenshot(path=sys.argv[2]+'/m1l.png')
  s=pg.query_selector_all('.scr')[2];s.click(position={'x':5,'y':5});pg.keyboard.type('sh');pg.keyboard.press('Enter');pg.wait_for_timeout(200);pg.query_selector_all('.mkw')[2].screenshot(path=sys.argv[2]+'/m3k.png')
  pg.click('.lay[data-id=W2] .rp');pg.wait_for_timeout(900);pg.query_selector_all('.mkw')[1].screenshot(path=sys.argv[2]+'/m2r.png')
  pg.set_viewport_size({'width':400,'height':800});pg.wait_for_timeout(300)
  print('scrollW',pg.evaluate('document.documentElement.scrollWidth'))
  print('errors',errs)
