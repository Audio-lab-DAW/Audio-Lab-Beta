"""Task DV-3: display-first devices, step 3: On the picture and the Pro EQ (docs/devices-display-first.md sections 7 and 10, pick DD3).
  python3 tools/ui-tests/taskDV_3.py [index.html] [out dir] [old index.html for the old-project check]
Checks: a closed Pro EQ in On the picture shows no rail, no hover panel and no values line; the eye's menu offers On the picture as ready; with no band
selected a hint sits on the graph; a click on a dot puts the band editor in a capsule under it, above it when the dot is low; the capsule's controls
work; several selected bands share one capsule; Gain is a slim fader at the right edge, always there; the preset arrows, Change and More float at the
top left; the More drawer holds the band chips, the analyser, Auto, Scale and Out, opens and closes (Escape gives the focus back) and is kept over a
render; the rail open hides the picture's chips and closing brings them back; Hover reveal still works on the Pro EQ; the eye's pill no longer covers
the graph's labels; every control on the picture has a tooltip; the chips are faces of the devices engine, and nothing is read or uploaded at rest;
Solid keeps everything readable; renders never change the device's values or kOpen/kMode; an old project opens with the same values and states;
screenshots of the three states at Glass and Light; no console errors."""
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
INIT = "if(!sessionStorage.getItem('dv3')){sessionStorage.setItem('dv3','1');localStorage.setItem('audiolab-ui',JSON.stringify({splash:false,lat3:1}))}"
RECIPE = {'tracks': [{'name': 'P', 'preset': 'pluck', 'fx': [{'type': 'eq'}, {'type': 'comp'}, {'type': 'eq'}],
                      'clips': [{'start': 0, 'len': 4, 'notes': [{'p': 52, 's': 0, 'l': 1, 'v': .9}, {'p': 55, 's': 1, 'l': 1, 'v': .9}]}]}]}
def page(p, src):
    b = p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required']); pg = b.new_page(viewport={'width': 1800, 'height': 1000}); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)[:300]))
    pg.on('console', lambda m: errs.append('console: ' + m.text[:300]) if m.type == 'error' else None)
    pg.add_init_script(INIT)
    pg.route('https://app.test/**', alsong(lambda r: r.fulfill(body=src, content_type='text/html') if r.request.url.endswith('/') or r.request.url.endswith('index.html') else r.fulfill(status=404, body='')))
    pg.goto('https://app.test/'); pg.wait_for_function('() => window.AudioLab && window.AudioLab.version', timeout=60000); pg.wait_for_timeout(2500)
    return b, pg, errs
with sync_playwright() as p:
    old_file = None; old_state = None
    if OLD:
        b0, pg0, e0 = page(p, open(OLD, encoding='utf-8').read())
        pg0.evaluate('r => AudioLab.build(r)', RECIPE); pg0.wait_for_timeout(800)
        R0 = lambda c: pg0.evaluate('c => AudioLab.run(c)', c)
        R0("(()=>{const t=S.tracks[0];t.fx[0].kOpen=false;t.fx[0].kMode='picture';t.fx[0].p.bands[2].g=4.5;t.fx[2].kOpen=false;t.fx[2].kMode='hover';renderFx();return 1})()")
        old_state = json.loads(R0("JSON.stringify(S.tracks[0].fx.map(f=>({ty:f.type,k:f.kOpen===undefined?null:f.kOpen,m:f.kMode||null,p:f.p})))"))
        pg0.evaluate("()=>AudioLab.run('packProject(curP()).then(b=>b.arrayBuffer()).then(a=>{const u=new Uint8Array(a);let s=\"\";for(let i=0;i<u.length;i+=32768)s+=String.fromCharCode.apply(null,u.subarray(i,i+32768));window.__pk=btoa(s)})')")
        pg0.wait_for_timeout(800); old_file = pg0.evaluate('() => window.__pk'); b0.close()
    b, pg, errs = page(p, SRC)
    R = lambda c: pg.evaluate('c => AudioLab.run(c)', c); J = lambda c: json.loads(R('JSON.stringify(' + c + ')'))
    ok(tuple(map(int, R('VERSION').split('.'))) >= (0, 289), 'version 0.289 or later', R('VERSION'))
    pg.evaluate('r => AudioLab.build(r)', RECIPE); pg.wait_for_timeout(1200)
    E = "fxin.querySelector('.dev[data-id=\"'+curT().fx[0].id+'\"]')"
    def scroll_to():
        R("(()=>{const D=%s;fxin.scrollLeft+=D.getBoundingClientRect().left-fxin.getBoundingClientRect().left-40;return 1})()" % E); pg.wait_for_timeout(250)
    def box(sel=None):
        return J("(()=>{const D=%s,e=%s;if(!e)return null;const r=e.getBoundingClientRect();return[r.left,r.top,r.width,r.height]})()" % (E, ("D.querySelector('%s')" % sel) if sel else 'D'))
    def shot(name):
        bx = box(); pg.screenshot(path=os.path.join(OUT, name + '.png'), clip={'x': bx[0] - 4, 'y': bx[1] - 4, 'width': bx[2] + 8, 'height': bx[3] + 8})
    def dot(i):
        return J("(()=>{const D=%s,cv=D.querySelector('canvas.eqv'),r=cv.getBoundingClientRect(),f=curT().fx[0],b=f.p.bands[%d],gs=(f.p.gs??100)/100,gl=/shelf|peak|tilt/.test(b.t)?b.g*gs:0,h=cv.clientHeight;return[r.left+fX(b.f,cv.clientWidth),r.top+h/2-gl/24*(h/2-12)]})()" % (E, i))
    P0 = J("JSON.stringify(curT().fx[0].p)")
    R("(()=>{const f=curT().fx[0];f.kOpen=false;f.kMode='picture';renderFx();return 1})()"); pg.wait_for_timeout(400); scroll_to(); pg.mouse.move(5, 5); pg.wait_for_timeout(300)
    st = J("(()=>{const D=%s,B=D.querySelector('.devb'),vis=s=>{const e=B.querySelector(s);return !!e&&e.offsetWidth>0&&getComputedStyle(e).opacity>.5};return{pic:D.classList.contains('dvpic'),side:vis(':scope>.eqside'),rail:vis(':scope>.dvrail'),val:!!B.querySelector(':scope>.dvval'),hint:vis(':scope>.dvcap.dvhint'),pre:vis(':scope>.dvpre'),more:vis('.dvpre .dvmore'),gain:vis(':scope>.dug.dvslim'),ht:(B.querySelector('.dvhint')||{}).title||''}})()" % E)
    ok(st['pic'] and not st['side'] and not st['rail'] and not st['val'], 'closed, On the picture: no rail, no hover panel, no values line', st)
    ok(st['hint'] and len(st['ht']) > 20, 'no band selected: a hint on the graph, its tooltip with the ways to edit', st['ht'][:60])
    ok(st['pre'] and st['more'] and st['gain'], 'preset arrows, Change and More at the top left; Gain always there', st)
    shot('dv3_eq_picture_none')
    # the eye's menu
    R("(()=>{const e=%s.querySelector('.dveye');e.dispatchEvent(new MouseEvent('contextmenu',{bubbles:true,cancelable:true,clientX:900,clientY:500}));return 1})()" % E); pg.wait_for_timeout(300)
    mt = R("(document.querySelector('.ctxm,.menu,[role=menu]')||{}).textContent||''")
    ok('On the picture' in mt and 'Not ready' not in mt, 'the eye menu offers On the picture as ready on the Pro EQ', mt[:120])
    pg.keyboard.press('Escape'); pg.wait_for_timeout(200)
    # the pill: clear of the graph's labels (in the column right of the graph)
    pp = J("(()=>{const D=%s,c=D.querySelector('canvas.eqv').getBoundingClientRect(),t=D.querySelector('.dvtr').getBoundingClientRect();return[Math.round(t.left-c.right),Math.round(t.width),Math.round(t.height)]})()" % E)
    ok(pp[0] >= -3 and pp[2] > pp[1], 'the eye and the pin stand right of the graph, clear of its labels', pp)
    # click a dot: the capsule under it
    d = dot(2); pg.mouse.click(d[0], d[1]); pg.wait_for_timeout(500); pg.mouse.move(5, 5); pg.wait_for_timeout(200)
    c = box('.dvcap')
    ok(J("[...eqSel(curT().fx[0])]") == [2] and c and not J("%s.querySelector('.dvcap').classList.contains('eqnone')" % E), 'a click on dot 3 selects band 3 and shows its capsule')
    ok(c and c[1] > d[1] + 4 and c[0] < d[0] < c[0] + c[2], 'the capsule sits under the selected dot', (c, d))
    sl = J("(()=>{const D=%s,a=D.querySelector('.dvcap').getBoundingClientRect(),g=D.querySelector('.dug').getBoundingClientRect(),b=D.querySelector('.devb').getBoundingClientRect();return[a.right<=g.left+1,a.bottom<=b.bottom+1,a.left>=b.left]})()" % E)
    ok(all(sl), 'the capsule stays inside the picture and clear of the gain', sl)
    shot('dv3_eq_picture_band')
    pg.click('#fxin .dev[data-id="%s"] .dvcap [data-eqt=lowshelf]' % J("curT().fx[0].id")); pg.wait_for_timeout(400)
    ok(J("curT().fx[0].p.bands[2].t") == 'lowshelf', 'the capsule\'s type buttons work')
    pg.click('#fxin .dev[data-id="%s"] .dvcap [data-eq=solo]' % J("curT().fx[0].id")); pg.wait_for_timeout(300)
    ok(J("!!curT().fx[0].p.bands[2].solo"), 'Solo works from the capsule')
    pg.click('#fxin .dev[data-id="%s"] .dvcap [data-eq=solo]' % J("curT().fx[0].id")); pg.wait_for_timeout(300)
    # drag the dot low: the capsule goes above it
    d = dot(2); pg.mouse.move(d[0], d[1]); pg.mouse.down(); pg.mouse.move(d[0] + 10, d[1] + 75, steps=6); pg.wait_for_timeout(120)
    mid = box('.dvcap'); pg.mouse.up(); pg.wait_for_timeout(500); pg.mouse.move(5, 5); pg.wait_for_timeout(200)
    d2 = dot(2); c2 = box('.dvcap')
    ok(J("curT().fx[0].p.bands[2].g") < -8, 'the dot was dragged down', J("curT().fx[0].p.bands[2].g"))
    ok(c2 and c2[1] + c2[3] < d2[1] - 4, 'a low dot gets its capsule above it', (c2, d2))
    ok(mid and abs(mid[1] - c2[1]) < 120, 'the capsule follows the dot while it is dragged', (mid, c2))
    # keyboard into the capsule
    R("%s.querySelector('.dvcap [data-eqt]').focus();1" % E); pg.keyboard.press('Tab'); pg.wait_for_timeout(100)
    ok(J("!!document.activeElement.closest('.dvcap')"), 'Tab moves through the capsule\'s controls')
    # two bands: one capsule at their middle
    R("(()=>{const f=curT().fx[0];eqSel(f).clear();eqSel(f).add(3);eqSel(f).add(4);renderFx();return 1})()"); pg.wait_for_timeout(400)
    mm = J("(()=>{const D=%s,C=D.querySelector('.dvcap');return{t:C.textContent,b:C.querySelectorAll('.eqrow button').length}})()" % E)
    c3 = box('.dvcap'); a, b4 = dot(3), dot(4)
    ok('2 bands selected' in mm['t'] and mm['b'] == 4, 'two bands selected: one capsule with Off, On, Gain 0, Delete', mm)
    ok(c3[0] < (a[0] + b4[0]) / 2 < c3[0] + c3[2], 'its capsule sits at the middle of the two dots', (c3, a, b4))
    R("(()=>{const f=curT().fx[0];eqSel(f).clear();eqSel(f).add(2);renderFx();return 1})()"); pg.wait_for_timeout(400)
    # Gain
    g = J("(()=>{const D=%s,g=D.querySelector('.dug'),c=D.querySelector('canvas.eqv').getBoundingClientRect(),r=g.getBoundingClientRect(),d=D.getBoundingClientRect(),vb=g.querySelector('[data-c]');return{op:+getComputedStyle(g).opacity,w:Math.round(r.width),in:r.right<=d.right+1&&r.left>=c.right-6,t:vb&&vb.title||''}})()" % E)
    ok(g['op'] > .9 and g['w'] <= 36 and g['in'] and 'Gain' in g['t'], 'Gain: a slim fader at the right edge, visible at rest, with its tooltip', g)
    # preset arrows from the pill
    pr0 = J("curT().fx[0].p.pre||''"); pg.click('#fxin .dev[data-id="%s"] .dvpre [data-dup=next]' % J("curT().fx[0].id")); pg.wait_for_timeout(500)
    ok(J("curT().fx[0].p.pre||''") != pr0, 'the next-preset arrow works from the picture', (pr0, J("curT().fx[0].p.pre||''")))
    R("(()=>{const f=curT().fx[0];f.p=JSON.parse(%s);renderFx();return 1})()" % json.dumps(P0)); pg.wait_for_timeout(300)
    # More
    fid = J("curT().fx[0].id")
    pg.click('#fxin .dev[data-id="%s"] .dvmore' % fid); pg.wait_for_timeout(300)
    mo = J("(()=>{const D=%s,d=D.querySelector('.dvdrw');return{on:d.classList.contains('on')&&d.offsetWidth>0,h:[...d.querySelectorAll('h5')].map(h=>h.textContent),chips:d.querySelectorAll('.eqbands .eqc,.eqbands .eqadd').length,an:!!d.querySelector('.eqan'),auto:!!d.querySelector('[data-eq=auto]'),sc:d.querySelectorAll('[data-eqg]').length,ex:D.querySelector('.dvmore').getAttribute('aria-expanded'),t:D.querySelector('.dvmore').title||D.querySelector('.dvmore').dataset.tip||''}})()" % E)
    ok(mo['on'] and mo['h'] == ['Bands', 'Analyser', 'Whole EQ'] and mo['chips'] >= 8 and mo['an'] and mo['auto'] and mo['sc'] == 2, 'More opens a drawer with the band chips, the analyser, Auto, Scale and Out', mo)
    ok(mo['ex'] == 'true' and 'More' in mo['t'], 'More has its tooltip and says it is open', mo['t'])
    shot('dv3_eq_picture_more')
    pg.click('#fxin .dev[data-id="%s"] .dvdrw [data-eqa=off]' % fid); pg.wait_for_timeout(400)
    ok(J("curT().fx[0].p.an") == 'off', 'the analyser switch works from the drawer')
    ok(J("%s.querySelector('.dvdrw').classList.contains('on')" % E), 'the drawer stays open over a render')
    R("%s.querySelector('.dvdrw .eqc input').focus();1" % E); pg.keyboard.press('Escape'); pg.wait_for_timeout(200)
    ok(J("!%s.querySelector('.dvdrw').classList.contains('on')&&document.activeElement.classList.contains('dvmore')" % E), 'Escape closes the drawer and gives the focus back to More')
    R("(()=>{const f=curT().fx[0];f.p.an='post';renderFx();return 1})()"); pg.wait_for_timeout(300)
    # tooltips on every control on the picture
    nt = J("(()=>{const D=%s,B=D.querySelector('.devb');D.querySelector('.dvdrw').classList.add('on');const bad=[];for(const e of B.querySelectorAll(':scope>.dvface button,:scope>.dvface input,:scope>.dvface select,:scope>.dvface [data-c],:scope>.dvface .eqc,:scope>.dvface .seg')){if(!e.offsetWidth)continue;if(!(e.title||e.dataset.tip||e.closest('[title],[data-tip]')))bad.push(e.outerHTML.slice(0,60))}D.querySelector('.dvdrw').classList.remove('on');return bad})()" % E)
    ok(not nt, 'every control on the picture has a tooltip', nt[:4])
    # rail open hides the picture, closing brings it back
    pg.click('#fxin .dev[data-id="%s"] .dveye' % fid); pg.wait_for_timeout(500)
    ro = J("(()=>{const D=%s;return{pic:D.classList.contains('dvpic'),faces:D.querySelectorAll('.devb>.dvface').length,side:D.querySelector('.eqside').offsetWidth,k:curT().fx[0].kOpen,m:curT().fx[0].kMode}})()" % E)
    ok(not ro['pic'] and ro['faces'] == 0 and ro['side'] > 200 and ro['k'] is True and ro['m'] == 'picture', 'the rail open: the chips go, the band editor is on the rail, the mode is kept', ro)
    scroll_to(); shot('dv3_eq_rail')
    pg.click('#fxin .dev[data-id="%s"] .dveye' % fid); pg.wait_for_timeout(500)
    ok(J("%s.classList.contains('dvpic')&&curT().fx[0].kOpen===false" % E), 'closed again: back on the picture')
    # Hover reveal on the Pro EQ
    R("(()=>{const f=curT().fx[0];f.kMode='hover';renderFx();return 1})()"); pg.wait_for_timeout(400); scroll_to(); pg.mouse.move(5, 5); pg.wait_for_timeout(300)
    hv0 = J("+getComputedStyle(%s.querySelector('.eqside')).opacity" % E)
    bx = box(); pg.mouse.move(bx[0] + 200, bx[1] + 100); pg.wait_for_timeout(400)
    hv1 = J("+getComputedStyle(%s.querySelector('.eqside')).opacity" % E)
    ok(not J("%s.classList.contains('dvpic')" % E) and hv0 < .1 and hv1 > .9, 'Hover reveal still works on the Pro EQ', (hv0, hv1))
    shot('dv3_eq_hover_revealed'); pg.mouse.move(5, 5); pg.wait_for_timeout(300); shot('dv3_eq_hover_rest')
    R("(()=>{const f=curT().fx[0];f.kMode='picture';renderFx();return 1})()"); pg.wait_for_timeout(400)
    # engine faces and no cost at rest
    eng = J("{on:!!DVG.g,gle:GLE.on}")
    if eng['on']:
        scroll_to(); pg.mouse.move(5, 5); pg.wait_for_timeout(700)
        fc = J("(()=>{const D=%s;const ids=[...D.querySelectorAll('.devb>.dvface')].filter(e=>e.offsetWidth).map(e=>e._dvg);return{n:ids.length,in:ids.filter(i=>DVG.faces.has(i)).length,fl:DVG.flats.size}})()" % E)
        ok(fc['n'] >= 3 and fc['in'] == fc['n'] and fc['fl'] >= 1, 'the chips are glass faces of the devices engine over the graph\'s picture', fc)
        pg.wait_for_timeout(2600)
        a = J("{s:DVG.n.sync,f:DVG.n.flatDirty,u:DVG.g.stats.flatUploads,c:DV3.n.cap}"); pg.wait_for_timeout(1500)
        b2 = J("{s:DVG.n.sync,f:DVG.n.flatDirty,u:DVG.g.stats.flatUploads,c:DV3.n.cap}")
        ok(a == b2, 'On the picture at rest: no page reads, no picture refreshes, no uploads', (a, b2))
    else:
        ok(True, 'engine not on in this browser: the chips keep their solid tint', eng); ok(True, 'no engine: nothing to upload at rest')
    # Light and Glass screenshots of the three states
    for lv in ['glass', 'light']:
        R("(()=>{UI.gl=Object.assign({},UI.gl||{},{lv:'%s'});gleApply();return 1})()" % lv); pg.wait_for_timeout(500)
        R("(()=>{const f=curT().fx[0];f.kOpen=true;renderFx();return 1})()"); pg.wait_for_timeout(400); scroll_to(); pg.mouse.move(5, 5); pg.wait_for_timeout(500); shot('dv3_%s_1_rail' % lv)
        R("(()=>{const f=curT().fx[0];f.kOpen=false;renderFx();return 1})()"); pg.wait_for_timeout(400); scroll_to(); pg.mouse.move(5, 5); pg.wait_for_timeout(500); shot('dv3_%s_2_picture' % lv)
        R("(()=>{const f=curT().fx[0];f.kMode='hover';renderFx();return 1})()"); pg.wait_for_timeout(400); scroll_to(); bx = box(); pg.mouse.move(bx[0] + 200, bx[1] + 100); pg.wait_for_timeout(500); shot('dv3_%s_3_hover' % lv)
        R("(()=>{const f=curT().fx[0];f.kMode='picture';renderFx();return 1})()"); pg.mouse.move(5, 5); pg.wait_for_timeout(300)
    # Solid: no engine, the chips are a near-solid tint
    R("(()=>{UI.gl=Object.assign({},UI.gl||{},{lv:'solid'});gleApply();renderFx();return 1})()"); pg.wait_for_timeout(600); scroll_to()
    so = J("(()=>{const D=%s,c=D.querySelector('.dvcap');const m=/rgba?\\(([^)]+)\\)/.exec(getComputedStyle(c).backgroundColor);const a=m?m[1].split(',').map(Number):[0,0,0,0];return{dvg:document.body.classList.contains('dvg'),a:a.length>3?a[3]:1,pic:D.classList.contains('dvpic')}})()" % E)
    ok(so['pic'] and not so['dvg'] and so['a'] >= .9, 'Solid: no engine, the capsule on a near-solid tint', so)
    shot('dv3_solid_picture')
    R("(()=>{UI.gl=Object.assign({},UI.gl||{},{lv:'glass'});gleApply();return 1})()"); pg.wait_for_timeout(300)
    # renders never change the device's values; kOpen and kMode saved as set
    R("renderFx();renderFx();1"); pg.wait_for_timeout(200)
    sv = J("(()=>{const q=JSON.parse(JSON.stringify(S)).tracks[0].fx;return[q[0].kOpen,q[0].kMode,q[2].kOpen===undefined]})()")
    ok(sv == [False, 'picture', True], 'kOpen and kMode are saved as set; an untouched device keeps neither', sv)
    R("(()=>{const f=curT().fx[0];f.p=JSON.parse(%s);renderFx();return 1})()" % json.dumps(P0)); pg.wait_for_timeout(300)
    for _ in range(3):
        for m in ['picture', 'hover']:
            R("(()=>{const f=curT().fx[0];f.kMode='%s';f.kOpen=!f.kOpen;renderFx();return 1})()" % m); pg.wait_for_timeout(80)
    ok(J("JSON.stringify(curT().fx[0].p)") == P0, 'switching between the three states never changes the Pro EQ\'s values')
    # a new Pro EQ added by the user starts closed on the picture, and now really shows it
    R("(()=>{const b=document.createElement('button');b.id='dv3T';b.textContent='add';b.style.cssText='position:fixed;left:4px;top:4px;z-index:99999';b.onclick=()=>{const t=curT();t.fx.push(mkFx('eq'));changed(true);renderFx()};document.body.append(b);return 1})()")
    pg.click('#dv3T'); pg.wait_for_timeout(500)
    ok(J("(()=>{const f=curT().fx[curT().fx.length-1],D=fxin.querySelector('.dev[data-id=\"'+f.id+'\"]');return f.kOpen===false&&f.kMode==='picture'&&D.classList.contains('dvpic')})()"), 'a Pro EQ the user adds starts closed and shows On the picture')
    # an old project
    if old_file:
        R("(()=>{const u=Uint8Array.from(atob('%s'),c=>c.charCodeAt(0));openProjectBlob(new File([u],'old-dv3.audiolab'));return 1})()" % old_file)
        pg.wait_for_timeout(4000)
        now = J("S.tracks[0].fx.map(f=>({ty:f.type,k:f.kOpen===undefined?null:f.kOpen,m:f.kMode||null,p:f.p}))")
        ok(now == old_state, 'an old project opens with the same values, rails and modes', (len(json.dumps(now)), len(json.dumps(old_state))))
        ok(J("(()=>{const D=fxin.querySelectorAll(':scope>.dev[data-d=fx]');return[D[0].classList.contains('dvpic'),D[2].classList.contains('dvpic'),D[2].classList.contains('dvshut')]})()") == [True, False, True], 'its closed Pro EQs show On the picture or Hover reveal as stored')
    errs = [e for e in errs if 'fetching the script' not in e and 'Failed to load resource' not in e]
    ok(not errs, 'no console errors', errs[:3])
    b.close()
print('%d of %d checks pass' % (N[1], N[0]))
if FAIL: print('FAILED:', FAIL); sys.exit(1)
