"""Task DV-1: display-first devices, the shared frame (docs/devices-display-first.md sections 7 and 10).
  python3 tools/ui-tests/taskDV_1.py [index.html] [out dir] [old index.html for the old-project check]
Checks: every device in the panel has the frame (no right strip, the eye and the pin in a pill, tooltips); a click on the eye opens and closes the
rail; right-click, a long press and Shift+F10 open the menu; Hover reveal and On the picture are kept per instance (kMode) and saved; a closed
device's controls are hidden at rest and shown on hover, on keyboard focus and after a tap; kOpen is never left changed by a render; nothing is read
or drawn at rest with the rail closed; widths kept; an old project (saved by the old build) opens with the same rails and parameters; no console errors."""
import sys, os, json, base64
import sys as _ws_sys, os as _ws_os; _ws_sys.path.insert(0, _ws_os.path.join(_ws_os.path.dirname(_ws_os.path.abspath(__file__)), '../test-songs')); from alsong import alsong  # task WS-F: the test songs
from playwright.sync_api import sync_playwright
SRC = open(sys.argv[1] if len(sys.argv) > 1 else 'index.html', encoding='utf-8').read()
OUT = sys.argv[2] if len(sys.argv) > 2 else '.'; os.makedirs(OUT, exist_ok=True)
OLD = sys.argv[3] if len(sys.argv) > 3 else None
N = [0, 0]; FAIL = []
def ok(c, m, info=''):
    N[0] += 1
    if c: N[1] += 1; print('ok   ', m, info if info != '' else '')
    else: FAIL.append(m); print('FAIL ', m, info)
INIT = "if(!sessionStorage.getItem('dv1')){sessionStorage.setItem('dv1','1');localStorage.setItem('audiolab-ui',JSON.stringify({splash:false,lat3:1}))}"
RECIPE = {'tracks': [{'name': 'P', 'preset': 'psyb', 'fx': [{'type': 'eq'}, {'type': 'comp'}, {'type': 'delay'}, {'type': 'voice'}],
                      'clips': [{'start': 0, 'len': 4, 'notes': [{'p': 40, 's': 0, 'l': 1, 'v': .9}]}]},
                     {'name': 'K', 'preset': 'kick', 'clips': [{'start': 0, 'len': 4, 'notes': [{'p': 36, 's': 0, 'l': 1, 'v': .9}]}]}]}
def page(p, src):
    b = p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required']); pg = b.new_page(viewport={'width': 1800, 'height': 1000}); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)[:300]))
    pg.on('console', lambda m: errs.append('console: ' + m.text[:300]) if m.type == 'error' else None)
    pg.add_init_script(INIT)
    pg.route('https://app.test/**', alsong(lambda r: r.fulfill(body=src, content_type='text/html') if r.request.url.endswith('/') or r.request.url.endswith('index.html') else r.fulfill(status=404, body='')))
    pg.goto('https://app.test/'); pg.wait_for_function('() => window.AudioLab && window.AudioLab.version', timeout=60000); pg.wait_for_timeout(2500)
    return b, pg, errs
with sync_playwright() as p:
    old_file = None
    if OLD:
        b0, pg0, e0 = page(p, open(OLD, encoding='utf-8').read())
        pg0.evaluate('r => AudioLab.build(r)', RECIPE); pg0.wait_for_timeout(800)
        R0 = lambda c: pg0.evaluate('c => AudioLab.run(c)', c)
        R0("(()=>{const t=S.tracks[0];t.fx[1].kOpen=false;t.fx[3].kOpen=false;t.inst.kOpen=true;t.fx[1].p.ratio=6;renderFx();return 1})()")
        old_state = json.loads(R0("JSON.stringify(S.tracks.map(t=>({k:t.inst&&t.inst.kOpen,fx:t.fx.map(f=>({ty:f.type,k:f.kOpen,p:f.p}))})))"))
        pg0.evaluate("()=>AudioLab.run('packProject(curP()).then(b=>b.arrayBuffer()).then(a=>{const u=new Uint8Array(a);let s=\"\";for(let i=0;i<u.length;i+=32768)s+=String.fromCharCode.apply(null,u.subarray(i,i+32768));window.__pk=btoa(s)});1')")
        pg0.wait_for_timeout(800); old_file = pg0.evaluate('() => window.__pk'); b0.close()
    b, pg, errs = page(p, SRC)
    R = lambda c: pg.evaluate('c => AudioLab.run(c)', c); J = lambda c: json.loads(R('JSON.stringify(' + c + ')'))
    ok(tuple(map(int, R('VERSION').split('.'))) >= (0, 262), 'version 0.262 or later', R('VERSION'))
    pg.evaluate('r => AudioLab.build(r)', RECIPE); pg.wait_for_timeout(1200)
    Q = "[...fxin.querySelectorAll(':scope>.dev[data-d=inst],:scope>.dev[data-d=fx]')]"
    fr = J(Q + ".map(d=>({c:d.className,dsr:!!d.querySelector(':scope>.dsr'),eye:!!d.querySelector('.dvtr>.dveye'),pin:!!d.querySelector('.dvtr>.pinbtn'),et:(d.querySelector('.dveye')||{}).title||'',pt:(d.querySelector('.dvtr .pinbtn')||{}).title||'',w:d.offsetWidth}))")
    ok(len(fr) == 5 and all('dvf' in d['c'] for d in fr), 'every device in the panel has the frame', [d['c'].split(' ')[:3] for d in fr])
    ok(all(not d['dsr'] for d in fr), 'the right-hand Parameters strip is gone')
    ok(all(d['eye'] and d['pin'] for d in fr), 'eye and pin in the top-right pill')
    ok(all('Right-click' in d['et'] and d['pt'] for d in fr), 'tooltips on the eye and the pin', fr[0]['et'])
    ok(all('—' not in d['et'] for d in fr), 'no em dash in the eye tooltip')
    ok([d['w'] for d in fr] == [970, 982, 602, 602, 1116], 'open widths are the same as before (970, 982, 602, 602, 1116)', [d['w'] for d in fr])
    # the eye inside the display, at the top right
    pos = J("(()=>{const d=%s[2],b=d.querySelector(':scope>.devb').getBoundingClientRect(),e=d.querySelector('.dvtr').getBoundingClientRect();return[Math.round(b.right-e.right),Math.round(e.top-b.top)]})()" % Q)
    ok(0 <= pos[0] <= 10 and 0 <= pos[1] <= 10, 'the pill sits at the top right of the display', pos)
    # rail open: one rail panel behind the controls and the gain
    rl = J("(()=>{const d=%s[2],R=d.querySelector('.dvrail').getBoundingClientRect(),s=d.querySelector('.dfs').getBoundingClientRect(),g=d.querySelector('.dug').getBoundingClientRect();return[R.left<=s.left,R.right>=g.right-1,R.top<=s.top,R.bottom>=s.bottom-1]})()" % Q)
    ok(all(rl), 'the rail panel covers the controls and the gain', rl)
    # click the eye on the Compressor: closed
    cid = J(Q + "[2].dataset.id")
    eye = pg.locator('#fxin .dev[data-id="%s"] .dveye' % cid)
    eye.click(); pg.wait_for_timeout(500)
    st = J("(()=>{const f=curT().fx.find(q=>q.id==='%s'),d=fxin.querySelector('.dev[data-id=\"%s\"]');return{k:f.kOpen,c:d.className,w:d.offsetWidth,op:getComputedStyle(d.querySelector('.dfs')).opacity,pe:getComputedStyle(d.querySelector('.dfs')).pointerEvents,val:(d.querySelector('.dvval')||{}).textContent||'',pressed:d.querySelector('.dveye').getAttribute('aria-pressed')}})()" % (cid, cid))
    ok(st['k'] is False and 'dvshut' in st['c'], 'a click on the eye closes the rail (kOpen false)', st['k'])
    ok(st['w'] == 500, 'closed width as before (500)', st['w'])
    ok(st['pressed'] == 'false', 'the eye says it is off (aria-pressed)')
    pg.mouse.move(5, 5); pg.wait_for_timeout(400)
    st = J("(()=>{const d=fxin.querySelector('.dev[data-id=\"%s\"]');return{op:getComputedStyle(d.querySelector('.dfs')).opacity,pe:getComputedStyle(d.querySelector('.dfs')).pointerEvents,val:(d.querySelector('.dvval')||{}).textContent||''}})()" % cid)
    ok(st['op'] == '0' and st['pe'] == 'none', 'closed: the controls are hidden at rest', st)
    ok('Attack' in st['val'] and 'Release' in st['val'], 'closed: a line of values on the picture (since DV-4 without Threshold and Ratio, which the picture writes itself)', st['val'])
    box = J("(r=>[r.left+r.width*.3,r.top+r.height*.5])(fxin.querySelector('.dev[data-id=\"%s\"]').getBoundingClientRect())" % cid)
    pg.mouse.move(box[0], box[1]); pg.wait_for_timeout(450)
    op = J("getComputedStyle(fxin.querySelector('.dev[data-id=\"%s\"] .dfs')).opacity" % cid)
    ok(op == '1', 'hover reveal: the controls show under the mouse', op)
    # the knobs still work in the revealed panel (same control, same parameter)
    k0 = J("curT().fx.find(q=>q.id==='%s').p.attack" % cid)
    kn = J("(()=>{const e=fxin.querySelector('.dev[data-id=\"%s\"] .dfs [data-c*=\"attack\"]');if(!e)return null;const r=e.getBoundingClientRect();return[r.left+r.width/2,r.top+r.height/2]})()" % cid)
    if kn:
        pg.mouse.move(kn[0], kn[1]); pg.mouse.down(); pg.mouse.move(kn[0], kn[1] - 30, steps=6); pg.mouse.up(); pg.wait_for_timeout(300)
    k1 = J("curT().fx.find(q=>q.id==='%s').p.attack" % cid)
    ok(kn is not None and k1 != k0, 'a knob in the revealed panel changes its parameter', (k0, k1))
    pg.mouse.move(5, 5); pg.wait_for_timeout(400)
    v2 = J("fxin.querySelector('.dev[data-id=\"%s\"] .dvval').textContent" % cid)
    ok(v2 != st['val'], 'the values line follows the change', v2[:40])
    # keyboard: focus a control inside reveals
    R("fxin.querySelector('.dev[data-id=\"%s\"] .dfs button, .dev[data-id=\"%s\"] .dfs select, .dev[data-id=\"%s\"] .dvdpre button').focus();1" % (cid, cid, cid)); pg.wait_for_timeout(400)
    ok(J("getComputedStyle(fxin.querySelector('.dev[data-id=\"%s\"] .dfs')).opacity" % cid) == '1', 'keyboard: Tab into a control shows the controls')
    R("document.activeElement.blur();1"); pg.wait_for_timeout(400)
    # touch: a tap on the picture
    cv = J("(r=>[r.left+r.width*.4,r.top+r.height*.4])(fxin.querySelector('.dev[data-id=\"%s\"] .dfv').getBoundingClientRect())" % cid)
    R("(()=>{const d=fxin.querySelector('.dev[data-id=\"%s\"] .dfv canvas'),o={bubbles:true,pointerType:'touch',clientX:%f,clientY:%f,pointerId:7,isPrimary:true};d.dispatchEvent(new PointerEvent('pointerdown',o));d.dispatchEvent(new PointerEvent('pointerup',o));return 1})()" % (cid, cv[0], cv[1])); pg.wait_for_timeout(400)
    ok(J("fxin.querySelector('.dev[data-id=\"%s\"]').classList.contains('dvshow')" % cid) and J("getComputedStyle(fxin.querySelector('.dev[data-id=\"%s\"] .dfs')).opacity" % cid) == '1', 'touch: a tap on the picture shows the controls')
    R("(()=>{const d=document.querySelector('#arr')||document.body,o={bubbles:true,pointerType:'touch',clientX:5,clientY:5,pointerId:8};d.dispatchEvent(new PointerEvent('pointerdown',o));d.dispatchEvent(new PointerEvent('pointerup',o));return 1})()"); pg.wait_for_timeout(300)
    ok(not J("fxin.querySelector('.dev[data-id=\"%s\"]').classList.contains('dvshow')" % cid), 'a tap elsewhere hides them again')
    # right-click menu
    eye = pg.locator('#fxin .dev[data-id="%s"] .dveye' % cid)
    eye.click(button='right'); pg.wait_for_timeout(300)
    m = J("{shown:!ctxm.hidden,t:ctxm.innerText+' '+ctxm.textContent}")
    ok(m['shown'] and 'Open the glass rail' in m['t'] and 'Hover reveal' in m['t'] and 'On the picture' in m['t'], 'right-click on the eye: the menu', m['t'].replace('\n', ' | ')[:160])
    hasp = J("!!DVPIC[curT().fx.find(q=>q.id==='%s').type]" % cid)  # the Compressor has positions from DV-4
    ok(('Not ready on this device yet' in m['t']) != hasp, 'On the picture says whether this device has positions yet', hasp)
    R("[...ctxm.querySelectorAll('button[data-i]')].find(b=>b.textContent.includes('On the picture')).click();1"); pg.wait_for_timeout(400)
    ok(J("curT().fx.find(q=>q.id==='%s').kMode" % cid) == 'picture', 'On the picture is kept on this device (kMode)')
    ok(J("curT().fx.filter(q=>q.id!=='%s').every(q=>q.kMode===undefined)" % cid), 'only on this instance')
    ok(J("fxin.querySelector('.dev[data-id=\"%s\"]').dataset.dvm" % cid) == ('picture' if hasp else 'hover'), 'it shows On the picture where the device has positions, otherwise hover reveal')
    # Shift+F10 on the focused eye
    R("fxin.querySelector('.dev[data-id=\"%s\"] .dveye').focus();1" % cid); pg.keyboard.press('Shift+F10'); pg.wait_for_timeout(300)
    ok(J("!ctxm.hidden&&ctxm.innerText.includes('Hover reveal')"), 'Shift+F10 on the eye opens the menu')
    R("[...ctxm.querySelectorAll('button[data-i]')].find(b=>b.textContent.includes('Open the glass rail')).click();1"); pg.wait_for_timeout(500)
    ok(J("curT().fx.find(q=>q.id==='%s').kOpen" % cid) is True, 'Open the glass rail from the menu')
    # long press (touch) on the eye
    e2 = J("(r=>[r.left+5,r.top+5])(fxin.querySelector('.dev[data-id=\"%s\"] .dveye').getBoundingClientRect())" % cid)
    R("(()=>{const d=fxin.querySelector('.dev[data-id=\"%s\"] .dveye');d.dispatchEvent(new PointerEvent('pointerdown',{bubbles:true,pointerType:'touch',clientX:%f,clientY:%f,pointerId:9}));return 1})()" % (cid, e2[0], e2[1])); pg.wait_for_timeout(700)
    ok(J("!ctxm.hidden&&ctxm.innerText.includes('Close the glass rail')"), 'a long press on the eye opens the menu')
    R("closeMenu();(()=>{const d=fxin.querySelector('.dev[data-id=\"%s\"] .dveye');d.dispatchEvent(new PointerEvent('pointerup',{bubbles:true,pointerType:'touch',pointerId:9}));d.click();return 1})()" % cid); pg.wait_for_timeout(300)
    ok(J("curT().fx.find(q=>q.id==='%s').kOpen" % cid) is True, 'the click after a long press does not toggle the rail')
    # renders never leave kOpen changed; the project JSON has the closed state
    R("(()=>{const t=curT();t.fx[3].kOpen=false;t.inst.kOpen=false;renderFx();renderFx();return 1})()"); pg.wait_for_timeout(300)
    ok(J("(()=>{const t=curT();return[t.inst.kOpen,t.fx[3].kOpen,JSON.parse(JSON.stringify(S)).tracks[0].fx[3].kOpen]})()") == [False, False, False], 'a render never leaves kOpen changed (instrument and effect)')
    ok(J("JSON.parse(JSON.stringify(S)).tracks[0].fx.find(q=>q.id==='%s').kMode" % cid) == 'picture', 'kMode is saved with the project')
    # no cost at rest: all closed, mouse away
    # (from DV-3 the Pro EQ, from DV-4 the Compressor really show On the picture: their chips cover the picture; set to hover reveal here, DV-3's and DV-4's tests cover the picture)
    R("(()=>{const t=curT();t.inst.kOpen=false;t.fx.forEach(f=>{f.kOpen=false;if(DVPIC[f.type])f.kMode='hover'});renderFx();return 1})()"); pg.mouse.move(5, 5); pg.wait_for_timeout(1200)
    a = J("{s:DVG.n.sync,f:DVG.n.flatDirty,d:DVG.g?DVG.g.stats.flatUploads:0,v:DV.n.vals}"); pg.wait_for_timeout(1500)
    b2 = J("{s:DVG.n.sync,f:DVG.n.flatDirty,d:DVG.g?DVG.g.stats.flatUploads:0,v:DV.n.vals}")
    ok(a == b2, 'rail closed, at rest: no page reads, no picture refreshes, no uploads, no value updates', (a, b2))
    ok(J("DVG.flats.size") == 0, 'no flat pictures while nothing covers a display')
    # glass engine: a face for an open rail, a picture under the revealed panel
    eng = J("{on:!!DVG.g,fail:DVG.fail,gle:GLE.on}")
    if eng['gle']:
        R("(()=>{const t=curT();t.inst.kOpen=true;renderFx();return 1})()"); pg.wait_for_timeout(500); R("fxin.scrollLeft=0;1"); pg.wait_for_timeout(700)
        ok(J("DVG.faces.size") >= 1 and J("DVG.flats.size") >= 1, 'engine: a glass face on the open rail, its display fed as a flat picture', J("[DVG.faces.size,DVG.flats.size]"))
        R("(()=>{const t=curT();t.inst.kOpen=false;renderFx();return 1})()"); pg.wait_for_timeout(500)
        ok(J("DVG.flats.size") == 0, 'closed again: the picture is no longer fed')
    else:
        ok(True, 'engine not on in this browser (no WebGL2): the panels keep their solid tint', eng)
    # Kick designer track
    R("selT=S.tracks[1].id;renderFx();1"); pg.wait_for_timeout(600)
    ok(J("fxin.querySelector('.dev[data-d=inst]').classList.contains('dvf')"), 'Kick designer has the frame')
    pg.screenshot(path=os.path.join(OUT, 'dv1_kick.png'))
    # an old project
    if old_file:
        R("(()=>{const u=Uint8Array.from(atob('%s'),c=>c.charCodeAt(0));openProjectBlob(new File([u],'old-dv.audiolab'));return 1})()" % old_file)
        pg.wait_for_timeout(4000)
        new_state = J("S.tracks.map(t=>({k:t.inst&&t.inst.kOpen,fx:t.fx.map(f=>({ty:f.type,k:f.kOpen,p:f.p}))}))")
        ok(new_state == old_state, 'an old project opens with the same rails and parameters', [(x.get('k'), [f.get('k') for f in x['fx']]) for x in new_state])
        R("selT=S.tracks[0].id;renderFx();1"); pg.wait_for_timeout(600)
        cls = J(Q + ".map(d=>d.classList.contains('dvshut'))")
        ok(cls == [False, False, True, False, True], 'its closed devices show closed, the others with the rail', cls)
    # the synthetic touch events above have no real pointer behind them, so a canvas's setPointerCapture complains; the service worker fetch fails on the test origin
    errs = [e for e in errs if 'setPointerCapture' not in e and 'fetching the script' not in e]
    ok(not errs, 'no console errors', errs[:3])
    b.close()
print('%d of %d checks pass' % (N[1], N[0]))
if FAIL: print('FAILED:', FAIL); sys.exit(1)
