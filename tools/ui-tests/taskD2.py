# task D2 (v0.221): the sidechain outline (sender and receiver strips light up) shows only when the sender or the receiver is selected.
#   python3 tools/ui-tests/taskD2.py index.html [outdir]
# Kick to Pad sidechain made by dragging the cable socket. Checks: no outline with no channel selected (master selected), outline with Kick or Pad selected
# (mixer click, arrangement header click, part of a multi-selection), none with a third channel; the change happens in the same step as the selection;
# steady over 90 frames (no flicker) stopped and playing; cables the same in every state; "Selected only" hides and shows the cable as before; no console errors.
import sys,os,json
import sys as _ws_sys, os as _ws_os; _ws_sys.path.insert(0, _ws_os.path.join(_ws_os.path.dirname(_ws_os.path.abspath(__file__)), '../test-songs')); from alsong import alsong  # task WS-F: the test songs
from playwright.sync_api import sync_playwright
f=sys.argv[1] if len(sys.argv)>1 else 'index.html';out=sys.argv[2] if len(sys.argv)>2 else '.'
def boot(p,w=2600,h=1100):
    src=open(f,encoding='utf-8').read()
    b=p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required']);pg=b.new_page(viewport={'width':w,'height':h});errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e)[:400]));pg.on('console',lambda m:errs.append('C:'+m.text[:300]) if m.type=='error' and 'net::' not in m.text and '404' not in m.text and 'fetching the script' not in m.text else None)
    pg.route('https://app.test/**',alsong(lambda r:r.fulfill(status=200,content_type='text/html',body=src.encode()) if r.request.url.endswith('.html') else r.fulfill(status=404,body=b'')))
    pg.add_init_script("if(!localStorage.getItem('audiolab-ui'))localStorage.setItem('audiolab-ui',JSON.stringify({splash:false,lat3:1}))")
    pg.goto('https://app.test/index.html');pg.wait_for_timeout(9000)
    return b,pg,errs,(lambda c:pg.evaluate("c=>window.AudioLab.run(c)",c))
fails=[]
def ck(name,ok,extra=''):
    print(('PASS ' if ok else 'FAIL ')+name,extra)
    if not ok:fails.append(name)
with sync_playwright() as p:
    b,pg,errs,R=boot(p);print('load errors',errs,'version',R("VERSION"))
    R("(()=>{const c=document.getElementById('liteNote');if(c)c.remove();openMixer()})()");pg.wait_for_timeout(1200)
    R("(()=>{const w=document.getElementById('mixWin');w.style.left='10px';w.style.width='2500px';mxFit();renderMixer()})()");pg.wait_for_timeout(800);R("document.querySelector('#mixWin .mxs').scrollLeft=0");pg.wait_for_timeout(300)
    ids=dict(json.loads(R("JSON.stringify(S.tracks.map(t=>[t.name,t.id]))")));K,P,B,C=ids['Kick'],ids['Pad'],ids['Bass'],ids['Clap'];nm={K:'Kick',P:'Pad',B:'Bass',C:'Clap'}
    # make the link: drag the Kick socket onto the Pad strip, take the main choice (Sidechain)
    sk=pg.locator(f'#mixWin svg.cabs .cabsk[data-sk="{K}"]').bounding_box();pr=json.loads(R(f"JSON.stringify(document.querySelector('#mixWin .mx[data-id=\"{P}\"]').getBoundingClientRect())"))
    pg.mouse.move(sk['x']+6,sk['y']+6);pg.mouse.down();pg.mouse.move(pr['x']+pr['width']/2,pr['y']+pr['height']-60,steps=15);pg.wait_for_timeout(200);pg.mouse.up();pg.wait_for_timeout(400)
    pg.locator('#abxM .abxo.main').first.click();pg.wait_for_timeout(900)
    print('Pad effects:',R(f"JSON.stringify(trkById('{P}').fx.map(f=>[f.type,f.p.src||'']))"))
    R("(()=>{for(const id of[...ABXW.keys()])abxClose(id)})()");pg.wait_for_timeout(300)
    lit=lambda:sorted(nm.get(i,i) for i in json.loads(R("JSON.stringify([...document.querySelectorAll('#mixWin .mx.abxl')].map(e=>e.dataset.id))")))
    roles=lambda:R(f"JSON.stringify(['{K}','{P}'].map(i=>{{const e=document.querySelector('#mixWin .mx[data-id=\"'+i+'\"]');return [e.classList.contains('abxs'),e.classList.contains('abxt'),getComputedStyle(e.querySelector('.fwrap')).boxShadow!=='none']}}))")
    cab=lambda:R("JSON.stringify([...document.querySelectorAll('#mixWin svg.cabs .cbg path,#mixWin svg.cabs .cfg path')].map(e=>e.getAttribute('d')).sort())")
    name=lambda i:f'#mixWin .mx[data-id="{i}"] .mxn'
    def frames(n=90):
        return json.loads(pg.evaluate("n=>new Promise(res=>{const s=new Set();let i=0;const t=()=>{s.add([...document.querySelectorAll('#mixWin .mx.abxl')].map(e=>e.dataset.id).sort().join(','));if(++i<n)requestAnimationFrame(t);else res(JSON.stringify([...s]))};requestAnimationFrame(t)})",n))
    # 1. nothing selected (the master is selected, so no channel is)
    R("selMaster()");pg.wait_for_timeout(200);print('selT',R("selT"),'TSEL',R("TSEL.size"))
    ck('no channel selected: no outline',lit()==[],lit());c0=cab();print('  cable paths drawn',len(json.loads(c0)))
    # 2. Kick (sender) selected in the mixer
    pg.locator(name(K)).click();pg.wait_for_timeout(200);ck('Kick selected: Kick and Pad outlined',lit()==['Kick','Pad'],lit());print('  [sender mark, receiver mark, outline drawn] for Kick, Pad',roles())
    ck('  steady over 90 frames',frames()==[','.join(sorted([K,P]))]);ck('  cables the same',cab()==c0)
    pg.screenshot(path=os.path.join(out,'d2_kick.png'),clip={'x':0,'y':300,'width':2600,'height':800})
    # 3. Pad (receiver) selected
    pg.locator(name(P)).click();pg.wait_for_timeout(200);ck('Pad selected: Kick and Pad outlined',lit()==['Kick','Pad'],lit());ck('  cables the same',cab()==c0)
    # 4. a third channel
    pg.locator(name(B)).click();pg.wait_for_timeout(200);ck('Bass selected: no outline',lit()==[],lit());ck('  steady over 90 frames',frames()==['']);ck('  cables the same',cab()==c0)
    pg.screenshot(path=os.path.join(out,'d2_bass.png'),clip={'x':0,'y':300,'width':2600,'height':800})
    # 5. same step: the outline is there before any new frame is drawn, and gone again in the same step
    r=R(f"(()=>{{const q=()=>document.querySelectorAll('#mixWin .mx.abxl').length;const a=q();selectTrack('{K}');const b=q();selectTrack('{B}');const c=q();return JSON.stringify([a,b,c])}})()")
    ck('change in the same step as the selection (0, 2, 0)',json.loads(r)==[0,2,0],r)
    # 6. shared selection: several channels (Cmd or Ctrl-click), and the arrangement header
    pg.keyboard.down('Control');pg.locator(name(K)).click();pg.keyboard.up('Control');pg.wait_for_timeout(200)
    print('  multi-selection',R("JSON.stringify([...TSEL].map(i=>trkById(i).name))"),'focused',R("trkById(selT).name"))
    ck('Bass and Kick selected together: outlined',lit()==['Kick','Pad'],lit())
    pg.keyboard.down('Control');pg.locator(name(K)).click();pg.keyboard.up('Control');pg.wait_for_timeout(200);ck('Kick taken out of the selection: no outline',lit()==[],lit())
    pg.locator(name(C)).click();pg.wait_for_timeout(150)
    R(f"document.querySelector('#hdrin .hdr[data-id=\"{P}\"] .nm').click()");pg.wait_for_timeout(200);ck('Pad clicked in the arrangement header: outlined',lit()==['Kick','Pad'],lit()+[R("trkById(selT).name")])
    R(f"document.querySelector('#hdrin .hdr[data-id=\"{C}\"] .nm').click()");pg.wait_for_timeout(200);ck('Clap clicked in the arrangement header: no outline',lit()==[],lit())
    # 7. playing
    pg.keyboard.press('Space');pg.wait_for_timeout(1500);ck('playing, Clap selected: no outline over 90 frames',frames()==[''])
    pg.locator(name(K)).click();pg.wait_for_timeout(300);ck('playing, Kick selected: outlined over 90 frames',frames()==[','.join(sorted([K,P]))]);print('  light level on Pad while playing',R(f"document.querySelector('#mixWin .mx[data-id=\"{P}\"]').style.getPropertyValue('--abxp')"))
    pg.keyboard.press('Space');pg.wait_for_timeout(400)
    # 8. "Selected only": the cable count per selection (compare with the build before)
    def n():return len(json.loads(cab()))
    res=[]
    pg.locator('#mixWin [data-cl="sel"]').first.click();pg.wait_for_timeout(500)
    for i in (K,P,B):
        pg.locator(name(i)).click();pg.wait_for_timeout(500);res.append((nm[i],n(),lit()))
    R("selMaster()");pg.wait_for_timeout(500);res.append(('master',n(),lit()))
    pg.locator('#mixWin [data-cl="sel"]').first.click();pg.wait_for_timeout(500);res.append(('off again',n(),lit()));ck('Selected only off again: all cables back',cab()==c0)
    print('SELECTED-ONLY cable paths per selection:',json.dumps([[a,b] for a,b,c in res]));print('  outlines in those states:',[[a,c] for a,b,c in res])
    # 9. cost of one pass of the lights (2000 passes, per selection)
    for i,l in ((B,'third channel selected'),(K,'Kick selected')):
        print('  abxLights x2000,',l+':',R(f"(()=>{{selectTrack('{i}');const w=document.getElementById('mixWin'),t=performance.now();for(let i=0;i<2000;i++)abxLights(w);return (performance.now()-t).toFixed(1)+' ms'}})()"))
    ck('no console or page errors',errs==[],errs)
    b.close()
print('RESULT','ALL PASS' if not fails else 'FAILED: '+'; '.join(fails))
