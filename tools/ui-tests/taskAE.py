# task AE (v0.208): change several channels and tracks together.
#   python3 tools/ui-tests/taskAE.py index.html [outdir]
# selection in the mixer and the track headers (shared), faders relative in dB, pan relative, Option for the same value, Cmd/Ctrl for one,
# buttons set all to the same state, one undo step, header controls, wheel and double-click, the right-click menu (duplicate, delete), the bottom tab
import sys,os,json
from playwright.sync_api import sync_playwright
f=sys.argv[1] if len(sys.argv)>1 else 'index.html';out=sys.argv[2] if len(sys.argv)>2 else '.'
def boot(p,w=1600,h=1000):
    src=open(f,encoding='utf-8').read()
    b=p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required']);pg=b.new_page(viewport={'width':w,'height':h});errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e)[:400]));pg.on('console',lambda m:errs.append('C:'+m.text[:300]) if m.type=='error' and 'net::' not in m.text and '404' not in m.text and 'fetching the script' not in m.text else None)
    pg.route('https://app.test/**',lambda r:r.fulfill(status=200,content_type='text/html',body=src.encode()) if r.request.url.endswith('.html') else r.fulfill(status=404,body=b''))
    pg.add_init_script("if(!localStorage.getItem('audiolab-ui'))localStorage.setItem('audiolab-ui',JSON.stringify({splash:false,lat3:1}))")
    pg.goto('https://app.test/index.html');pg.wait_for_timeout(9000)
    return b,pg,errs,(lambda c:pg.evaluate("c=>window.AudioLab.run(c)",c))
with sync_playwright() as p:
    b,pg,errs,R=boot(p);print('load errors',errs,'version',R("VERSION"))
    R("(()=>{const c=document.getElementById('liteNote');if(c)c.remove();openMixer()})()");pg.wait_for_timeout(1500)
    ids=dict(json.loads(R("JSON.stringify(S.tracks.map(t=>[t.name,t.id]))")));K,B,C=ids['Kick'],ids['Bass'],ids['Clap']
    R(f"(()=>{{trkById('{K}').vol=Math.pow(10,-3/20);trkById('{B}').vol=Math.pow(10,-9/20);trkById('{C}').vol=Math.pow(10,-14/20);trkById('{B}').pan=-.2;trkById('{C}').pan=.5;changed(true);renderMixer()}})()");pg.wait_for_timeout(300)
    box=lambda s:pg.locator(s).first.bounding_box();nm=lambda i:f'#mixWin .mx[data-id="{i}"] .mxn'
    db=lambda:R(f"JSON.stringify(['{K}','{B}','{C}'].map(i=>{{const v=trkById(i).vol;return v<=1e-4?-999:+(20*Math.log10(v)).toFixed(2)}}))")
    pans=lambda:R(f"JSON.stringify(['{K}','{B}','{C}'].map(i=>+trkById(i).pan.toFixed(3)))")
    st=lambda k:R(f"JSON.stringify(['{K}','{B}','{C}'].map(i=>!!trkById(i).{k}))")
    pg.locator(nm(K)).click();pg.keyboard.down('Control');pg.locator(nm(B)).click();pg.locator(nm(C)).click();pg.keyboard.up('Control');pg.wait_for_timeout(200)
    print('selected in the mixer:',R("JSON.stringify([...TSEL].map(i=>trkById(i).name))"),'strips marked',R("document.querySelectorAll('#mixWin .mx.msel').length"),'headers marked',R("document.querySelectorAll('#hdrin .hdr.msel').length"),'pill',repr(R("(document.querySelector('#mixWin .aecnt')||{}).innerText")))
    print('volumes (Kick, Bass, Clap) dB',db());u0=R("UNDO.length")
    f=box(f'[data-c="mx:{K}:vol"]');x=f['x']+f['width']/2;y=f['y']+f['height']*.2;pg.mouse.move(x,y);pg.mouse.down()
    for i in range(8):pg.mouse.move(x,y+i*4+4);pg.wait_for_timeout(30)
    print('  dragging the Kick fader down',db())
    for i in range(30):pg.mouse.move(x,y-60-i*3);pg.wait_for_timeout(20)
    print('  far up, Kick stops at +6',db())
    pg.mouse.move(x,y+12);pg.wait_for_timeout(60);print('  back down, offsets back',db());pg.mouse.up();pg.wait_for_timeout(100)
    print('  undo steps',R("UNDO.length")-u0);R("undo()");print('  after one undo',db())
    print('pans',pans())
    def pdrag(dx,key=None):
        if key:pg.keyboard.down(key)
        f=box(f'[data-c="mx:{K}:pan"]');pg.mouse.move(f['x']+f['width']/2,f['y']+f['height']/2);pg.mouse.down();pg.mouse.move(f['x']+f['width']/2+dx,f['y']+5,steps=5);pg.wait_for_timeout(60);pg.mouse.up()
        if key:pg.keyboard.up(key)
    pdrag(15);print('  pan dragged right (relative)',pans());pdrag(-10,'Alt');print('  with Option/Alt (same value)',pans());pdrag(20,'Control');print('  with Cmd/Ctrl (only Kick)',pans())
    u0=R("UNDO.length");pg.locator(f'#mixWin .mx[data-id="{B}"] .mxb [data-a="mute"]').click();pg.wait_for_timeout(200);print('mute clicked on Bass in the mixer',st('mute'),'undo steps',R("UNDO.length")-u0)
    pg.keyboard.down('Control');pg.locator(f'#mixWin .mx[data-id="{B}"] .mxb [data-a="solo"]').click();pg.keyboard.up('Control');pg.wait_for_timeout(200);print('Cmd/Ctrl-click solo on Bass (only Bass)',st('solo'))
    pg.locator(f'#mixWin .mx[data-id="{C}"] .mxb [data-a="solo"]').click();pg.wait_for_timeout(200);print('solo clicked on Clap (Clap was off, so all on)',st('solo'))
    R("undo()");R("undo()");R("undo()");print('three undos',st('mute'),st('solo'))
    r=json.loads(R("JSON.stringify(document.getElementById('mixWin').getBoundingClientRect())"))
    pg.screenshot(path=os.path.join(out,'ae_mixer.png'),clip={'x':r['x'],'y':r['y']-30,'width':min(r['width'],1000),'height':r['height']+40})
    pg.screenshot(path=os.path.join(out,'ae_tab.png'),clip={'x':r['x']+r['width']/2-330,'y':r['y']+r['height']-60,'width':660,'height':75})
    lg,tb=json.loads(R("JSON.stringify([document.querySelector('#mixWin .cablg').getBoundingClientRect(),document.querySelector('#mixWin .abxtab').getBoundingClientRect()])"))
    print('legend bottom %.0f, tab top %.0f: %s'%(lg['bottom'],tb['top'],'clear' if tb['top']>=lg['bottom'] else 'OVERLAP'),'tab height',tb['height'])
    R("document.querySelector('#mixWin .fwc').click()");pg.wait_for_timeout(300)
    print('arrangement shows the same selection',R("JSON.stringify([...document.querySelectorAll('#hdrin .hdr.msel')].map(e=>trkById(e.dataset.id).name))"))
    f=box(f'[data-c="hd:{B}"]');u0=R("UNDO.length");pg.mouse.move(f['x']+f['width']/2,f['y']+f['height']/2);pg.mouse.down();pg.mouse.move(f['x']+f['width']/2-30,f['y']+f['height']/2,steps=6);pg.wait_for_timeout(400);pg.mouse.up();pg.wait_for_timeout(200)
    print('header volume of Bass dragged left',db(),'undo steps',R("UNDO.length")-u0);R("undo()");print('  undo',db())
    pg.mouse.move(f['x']+f['width']/2,f['y']+f['height']/2);pg.mouse.wheel(0,-100);pg.wait_for_timeout(200);print('wheel up on Bass',db())
    pg.mouse.dblclick(f['x']+f['width']/2,f['y']+f['height']/2);pg.wait_for_timeout(200);print('double-click resets all',db())
    pg.locator(f'#hdrin .hdr[data-id="{K}"] [data-a="mute"]').click();pg.wait_for_timeout(150);print('header mute on Kick',st('mute'))
    pg.locator(f'#hdrin .hdr[data-id="{K}"] .nm').click();pg.wait_for_timeout(100);print('plain click clears, selected now',R("TSEL.size"))
    pg.keyboard.down('Shift');pg.locator(f'#hdrin .hdr[data-id="{C}"] .nm').click();pg.keyboard.up('Shift');pg.wait_for_timeout(200)
    print('Shift-click range in the headers',R("JSON.stringify([...TSEL].map(i=>trkById(i).name))"))
    n0=R("S.tracks.length");pg.locator(f'#hdrin .hdr[data-id="{B}"] .nm').click(button='right');pg.wait_for_timeout(200)
    print('menu:',R("document.getElementById('ctxm').innerText").replace('\n',' | ')[:330]);pg.screenshot(path=os.path.join(out,'ae_menu.png'))
    pg.locator('#ctxm >> text=/^Duplicate 4 tracks/').first.click();pg.wait_for_timeout(300);print('duplicate: tracks',n0,'->',R("S.tracks.length"),'selected',R("JSON.stringify([...TSEL].map(i=>trkById(i).name))"))
    R("undo()");print('one undo: tracks',R("S.tracks.length"))
    R(f"(()=>{{TSEL.clear();for(const i of ['{K}','{B}','{C}'])TSEL.add(i);hdrMark()}})()");R(f"trackMenu(300,300,trkById('{K}'))");pg.wait_for_timeout(150)
    pg.locator('#ctxm >> text=/^Delete 3 tracks/').first.click();pg.wait_for_timeout(300);print('delete 3: tracks',R("S.tracks.length"));R("undo()");print('one undo: tracks',R("S.tracks.length"),'Kick back',R(f"!!trkById('{K}')"))
    print('errors',errs);b.close()
