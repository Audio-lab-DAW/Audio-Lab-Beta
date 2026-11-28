# screenshots of the pick page (served locally) at a few moments, dark and light
import sys, subprocess, time
from playwright.sync_api import sync_playwright
srv=subprocess.Popen(['python3','-m','http.server','8811'],cwd=sys.argv[1] if len(sys.argv)>1 else '.',stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
out=sys.argv[2] if len(sys.argv)>2 else '.'
try:
  with sync_playwright() as p:
    b=p.chromium.launch();
    for th in ('dark','light'):
      pg=b.new_page(viewport={'width':1400,'height':1000},color_scheme=th);errs=[];pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('console',lambda m:errs.append(m.text) if m.type=='error' else None)
      pg.goto('http://localhost:8811/stem-split.html');pg.wait_for_timeout(1500)
      pg.click('#spd button[data-v="16"]');pg.wait_for_timeout(4200)
      pg.screenshot(path=f'{out}/shot_{th}_mid.png',full_page=False,clip={'x':0,'y':380,'width':1400,'height':620})
      pg.wait_for_timeout(4000);pg.evaluate("document.getElementById('fam-G').scrollIntoView()");pg.wait_for_timeout(300)
      pg.screenshot(path=f'{out}/shot_{th}_done.png')
      pg.evaluate("document.getElementById('fam-S').scrollIntoView()");pg.wait_for_timeout(300);pg.screenshot(path=f'{out}/shot_{th}_S.png')
      print(th,errs[:5])
    pg=b.new_page(viewport={'width':400,'height':900});pg.goto('http://localhost:8811/stem-split.html');pg.wait_for_timeout(2000);print('phone scrollW',pg.evaluate('document.documentElement.scrollWidth'));pg.screenshot(path=f'{out}/shot_phone.png')
    b.close()
finally: srv.kill()
