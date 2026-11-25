# Settings search finds "Reset all settings" in the footer, and the Edit button on the Transport block of the layout picture (v0.173):
# python3 tools/ui-tests/setfind.py index.html [outdir]
import sys,json,os
from playwright.sync_api import sync_playwright
F=sys.argv[1] if len(sys.argv)>1 else 'index.html';OUT=sys.argv[2] if len(sys.argv)>2 else '.';os.makedirs(OUT,exist_ok=True)
def boot(p,f=F,scale=2,w=1600,h=1000,ui='{splash:false,lat3:1}'):
    src=open(f,encoding='utf-8').read()
    b=p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required']);pg=b.new_page(viewport={'width':w,'height':h},device_scale_factor=scale);errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e)[:400]));pg.on('console',lambda m:errs.append('C:'+m.text[:300]) if m.type=='error' and 'net::' not in m.text and '404' not in m.text else None)
    pg.route('https://app.test/**',lambda r:r.fulfill(status=200,content_type='text/html',body=src.encode()) if r.request.url.endswith('.html') else r.fulfill(status=404,body=b''))
    pg.add_init_script("if(!localStorage.getItem('audiolab-ui'))localStorage.setItem('audiolab-ui',JSON.stringify(%s))"%ui)
    pg.goto('https://app.test/index.html');pg.wait_for_timeout(9000)
    return b,pg,errs
def run(pg,code): return pg.evaluate("c=>window.AudioLab.run(c)",code)
tab=lambda pg:pg.evaluate("()=>{const b=document.querySelector('#setNav [data-tab].on,#setNav [data-tab][aria-selected=true]');const s=[...document.querySelectorAll('#setBody section[data-page]')].find(x=>x.offsetParent);return (b?b.dataset.tab:'?')+'/'+(s?s.dataset.page:'?')}")
hits=lambda pg:pg.evaluate("()=>[...document.querySelectorAll('#setQR button')].map(b=>b.querySelector('b').textContent+' ['+b.querySelector('small').textContent+']')")
with sync_playwright() as p:
    b,pg,errs=boot(p);pg.evaluate("()=>{const c=document.getElementById('liteNote');if(c)c.remove()}")
    # --- search
    for start in ['audio','layout']:
        run(pg,"openSettings('%s')"%start);pg.wait_for_timeout(500)
        pg.click('#setQ');pg.keyboard.type('reset');pg.wait_for_timeout(300);print('on tab',tab(pg),'typed "reset":',hits(pg))
        if start=='audio':pg.screenshot(path=OUT+'/find1.png')
        i=pg.evaluate("()=>[...document.querySelectorAll('#setQR button')].findIndex(b=>/Reset all settings/.test(b.textContent))")
        pg.click('#setQR button >> nth=%d'%i);pg.wait_for_timeout(250)
        print('  chosen: tab now',tab(pg),'| button flashes:',pg.evaluate("()=>document.getElementById('genReset').classList.contains('sflash')"),'| flashing elements:',pg.evaluate("()=>[...document.querySelectorAll('.sflash')].map(e=>e.id||e.className)"),'| settings open:',pg.evaluate("()=>!document.getElementById('set').hidden"))
        if start=='audio':pg.screenshot(path=OUT+'/find2.png')
        pg.wait_for_timeout(2000);print('  after 2 s flash gone:',pg.evaluate("()=>!document.querySelector('.sflash')"))
    for q in ['reset all','all settings','factory','reset','buffer']:
        pg.click('#setQ');pg.keyboard.type(q);pg.wait_for_timeout(250);print('"%s":'%q,hits(pg)[:4]);pg.keyboard.press('Escape');pg.evaluate("()=>{const q=document.getElementById('setQ');q.value='';q.dispatchEvent(new Event('input'))}")
    # keyboard: type and press Enter on the first hit
    run(pg,"openSettings('audio')");pg.wait_for_timeout(300);pg.click('#setQ');pg.keyboard.type('reset all');pg.wait_for_timeout(250);pg.keyboard.press('Enter');pg.wait_for_timeout(250)
    print('Enter: tab',tab(pg),'flash',pg.evaluate("()=>document.getElementById('genReset').classList.contains('sflash')"),'question open:',pg.evaluate("()=>{const d=document.getElementById('cdlg');return !!d&&!d.hidden}"))
    # another result still switches tab and flashes as before
    pg.wait_for_timeout(1900);pg.click('#setQ');pg.keyboard.type('buffer');pg.wait_for_timeout(250);pg.click('#setQR button >> nth=0');pg.wait_for_timeout(300);print('other result: tab',tab(pg),'flashing',pg.evaluate("()=>[...document.querySelectorAll('.sflash')].map(e=>e.tagName+'.'+e.className)"))
    # --- Edit button on the Transport block
    run(pg,"openSettings('layout')");pg.wait_for_timeout(700)
    G="()=>{const m=document.getElementById('mini'),t=m.querySelector('.mb.k-tr'),e=t.querySelectorAll('.mbedit'),q=t.getBoundingClientRect(),r=e[0]&&e[0].getBoundingClientRect(),over=(a,b)=>!(a.right<=b.left||b.right<=a.left||a.bottom<=b.top||b.bottom<=a.top);return JSON.stringify({buttons:e.length,x:r&&[Math.round(r.left-q.left),Math.round(r.right-q.left)],y:r&&[Math.round(r.top-q.top),Math.round(r.bottom-q.top)],blockH:Math.round(q.height),covers:r?[...t.children].filter(c=>c!==e[0]&&over(r,c.getBoundingClientRect())).map(c=>c.className):null,order:UI.order.join()})}"
    print('picture',run(pg,"("+G+")()"));pg.locator('#mini').screenshot(path=OUT+'/mini1.png')
    run(pg,"(()=>{renderMini();renderMini();applyLayout();renderMini()})()");print('after renderMini x3',run(pg,"("+G+")()"))
    c=pg.evaluate("()=>{const r=document.querySelector('#mini .mbedit').getBoundingClientRect();return [r.left+r.width/2,r.top+r.height/2]}")
    # press and drag on the button: the block must not move
    pg.mouse.move(c[0],c[1]);pg.mouse.down();pg.mouse.move(c[0],c[1]-120,steps=6);d=pg.evaluate("()=>document.querySelector('#mini .mb.drag')?'DRAG STARTED':'no drag'");pg.mouse.up();pg.wait_for_timeout(200)
    print('press on button and pull up:',d,run(pg,"("+G+")()"),'editor open:',pg.evaluate("()=>document.body.classList.contains('tredit')"))
    # the block itself still drags
    t=pg.evaluate("()=>{const r=document.querySelector('#mini .mb.k-tr').getBoundingClientRect();return [r.left+60,r.top+r.height/2]}")
    pg.mouse.move(t[0],t[1]);pg.mouse.down();pg.mouse.move(t[0],t[1]-150,steps=8);pg.wait_for_timeout(100);pg.locator('#mini').screenshot(path=OUT+'/mini2.png');pg.mouse.up();pg.wait_for_timeout(300)
    print('block dragged up:',run(pg,"("+G+")()"));pg.locator('#mini').screenshot(path=OUT+'/mini3.png')
    run(pg,"(()=>{UI.order=['arr','fx','tr','map'];saveUI();applyLayout();renderMini();renderPres()})()");pg.wait_for_timeout(200);print('order back:',run(pg,"("+G+")()"))
    # hover look, then click opens the editor
    c=pg.evaluate("()=>{const r=document.querySelector('#mini .mbedit').getBoundingClientRect();return [r.left+r.width/2,r.top+r.height/2]}")
    pg.mouse.move(c[0],c[1]);pg.wait_for_timeout(200);pg.locator('#mini').screenshot(path=OUT+'/mini4.png')
    pg.mouse.click(c[0],c[1]);pg.wait_for_timeout(500);print('click: editor open',pg.evaluate("()=>document.body.classList.contains('tredit')"),'settings hidden',pg.evaluate("()=>document.getElementById('set').hidden"));pg.screenshot(path=OUT+'/tredit.png')
    pg.keyboard.press('Escape');pg.wait_for_timeout(400);print('after Escape: editor open',pg.evaluate("()=>document.body.classList.contains('tredit')"))
    run(pg,"(()=>{if(TRE.on&&typeof trEditClose==='function')trEditClose()})()");run(pg,"openSettings('layout')");pg.wait_for_timeout(500)
    print('old Edit button in the row below:',pg.evaluate("()=>{const b=document.getElementById('trEditBtn');return b?b.textContent+' visible:'+!!b.offsetParent:'missing'}"));print('reopened picture',run(pg,"("+G+")()"))
    pg.click('#trEditBtn');pg.wait_for_timeout(400);print('row button: editor open',pg.evaluate("()=>document.body.classList.contains('tredit')"))
    # keyboard: focus and Enter
    print('errors',errs);b.close()
