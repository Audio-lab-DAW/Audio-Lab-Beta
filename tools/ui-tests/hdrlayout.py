import sys,json
from playwright.sync_api import sync_playwright
SP='/tmp/'
def boot(p,scale=1,w=1600,h=1000,ui='{splash:false,lat3:1}',f=(sys.argv[1] if len(sys.argv)>1 else 'index.html')):
    src=open(f,encoding='utf-8').read()
    b=p.chromium.launch();pg=b.new_page(viewport={'width':w,'height':h},device_scale_factor=scale);errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e)[:400]));pg.on('console',lambda m:errs.append('C:'+m.text[:300]) if m.type=='error' and 'net::' not in m.text and '404' not in m.text else None)
    pg.route('https://app.test/**',lambda r:r.fulfill(status=200,content_type='text/html',body=src.encode()) if r.request.url.endswith('.html') else r.fulfill(status=404,body=b''))
    pg.add_init_script("if(!localStorage.getItem('audiolab-ui'))localStorage.setItem('audiolab-ui',JSON.stringify(%s))"%ui)
    pg.goto('https://app.test/index.html');pg.wait_for_timeout(9000)
    return b,pg,errs
def run(pg,code):
    return pg.evaluate("c=>window.AudioLab.run(c)",code)
# track header layout editor test (v0.164): python3 tools/ui-tests/hdrlayout.py index.html
import json
with sync_playwright() as p:
    b,pg,errs=boot(p,scale=1,w=1400,h=900)
    run(pg,"(()=>{const c=document.getElementById('liteNote');if(c)c.remove();V.th=96;clampV();layoutRows();renderHeaders();dirty=true})()")
    J=lambda c:json.loads(run(pg,"JSON.stringify("+c+")"))
    # right-click empty space of a header
    hb=pg.locator('#hdrin .hdr').nth(2).bounding_box()
    pg.mouse.click(hb['x']+150,hb['y']+hb['height']-8,button='right');pg.wait_for_timeout(300)
    print('ctx',pg.evaluate("()=>[...ctxm.querySelectorAll('.mh,button .mlab')].map(x=>x.textContent).slice(0,4)"));pg.screenshot(path=SP+'ctx.png')
    pg.evaluate("()=>[...ctxm.querySelectorAll('button')].find(b=>b.textContent.includes('Customise')).click()");pg.wait_for_timeout(300)
    print('opened by ctx',pg.evaluate("()=>!document.getElementById('hczEd').hidden"))
    # menu elsewhere must not carry the item
    pg.mouse.click(900,300,button='right');pg.wait_for_timeout(300);print('arr menu has item',pg.evaluate("()=>ctxm.textContent.includes('Customise track controls')"));pg.keyboard.press('Escape');pg.wait_for_timeout(200)
    print('ed open after esc on menu',pg.evaluate("()=>!document.getElementById('hczEd').hidden"))
    pg.keyboard.press('Escape');pg.wait_for_timeout(200);print('ed open after 2nd esc',pg.evaluate("()=>!document.getElementById('hczEd').hidden"))
    # settings card
    run(pg,"openSettings('layout')");pg.wait_for_timeout(500);pg.evaluate("()=>document.getElementById('hczCard').scrollIntoView({block:'center'})");pg.wait_for_timeout(300);pg.screenshot(path=SP+'set.png')
    pg.locator('#hczSetB').click();pg.wait_for_timeout(400);print('from settings',pg.evaluate("()=>[document.getElementById('set').hidden,!document.getElementById('hczEd').hidden]"))
    # presets through the panel
    pg.locator('#hczEd [data-zp="all"]').click();pg.wait_for_timeout(300);print('all',J("UI.hcz.order.length"),pg.evaluate("()=>document.querySelector('#hczEd [data-zp=all]').className"))
    pg.locator('#hczEd [data-zp="min"]').click();pg.wait_for_timeout(300);print('min',J("UI.hcz"))
    # title drag
    t=pg.locator('#hczEd .zeh').bounding_box();pg.mouse.move(t['x']+60,t['y']+12);pg.mouse.down();pg.mouse.move(t['x']+400,t['y']+150,steps=5);pg.mouse.up();print('moved',pg.locator('#hczEd').bounding_box())
    # undo/redo keeps layout; play with meter hidden
    pg.locator('#hczEd .zes[data-zo="meter"] [data-v="0"]').click();pg.locator('#hczEd .zes[data-zo="pan"] [data-v="round"]').click();pg.locator('#hczEd [data-za="pan"]').click();pg.wait_for_timeout(200)
    run(pg,"pushUndo();S.tracks[1].mute=true;changed(true)");pg.wait_for_timeout(200);run(pg,"undo()");pg.wait_for_timeout(300)
    print('after undo',run(pg,"hdrin.className+' zw:'+hdrin.querySelectorAll('.zw').length+' hm:'+hdrin.querySelectorAll('.hm').length+' kn:'+hdrin.querySelectorAll('.zw .kn').length"))
    pg.keyboard.press('Escape');pg.mouse.click(900,400);pg.keyboard.press('Space');pg.wait_for_timeout(2500);pg.screenshot(path=SP+'play.png');pg.keyboard.press('Space');pg.wait_for_timeout(300)
    # mixer open + mixer pan -> header knob
    run(pg,"(()=>{const C=CT.get('mx:'+S.tracks[1].id+':pan');if(C){C.set(0.3)}else{try{$('#bMix')&&$('#bMix').click()}catch(e){}}})()");pg.wait_for_timeout(300)
    print('mixer pan',J("[S.tracks[1].pan,!!CT.get('mx:'+S.tracks[1].id+':pan'),document.querySelectorAll('#hdrin .hdr')[1].querySelector('.kn output').textContent]"))
    # tracks on the right
    run(pg,"document.body.classList.add('tr-right');dirty=true");pg.wait_for_timeout(400);run(pg,"hczSet(JSON.parse(JSON.stringify(HCZP.all.c)));hczOpen()");pg.wait_for_timeout(400);pg.screenshot(path=SP+'right.png');run(pg,"document.body.classList.remove('tr-right');hczClose()")
    # persistence
    run(pg,"hczSet({order:['mute','solo','vol','pan','freeze'],icon:'big',pan:'half',ms:'large',meter:1});saveUINow()");
    pg.reload();pg.wait_for_timeout(9000)
    print('after reload',J("UI.hcz"),run(pg,"hdrin.className+' zw:'+hdrin.querySelectorAll('.zw').length+' hpd:'+hdrin.querySelectorAll('.zw .hpd').length"))
    pg.screenshot(path=SP+'reload.png')
    # reset -> legacy DOM
    run(pg,"hczOpen()");pg.locator('#hczEd [data-ze="reset"]').click();pg.wait_for_timeout(400)
    print('reset',J("UI.hcz===undefined"),run(pg,"hdrin.className+' zw:'+hdrin.querySelectorAll('.zw').length+' hm:'+hdrin.querySelectorAll('.hm').length+' std:'+document.querySelector('#hczEd [data-zp=std]').className"))
    pg.screenshot(path=SP+'reset.png')
    print(errs)
