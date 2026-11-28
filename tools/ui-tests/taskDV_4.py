"""Task DV-4: display-first devices, step 4: the bottom dock, the values line clear of the handles, On the picture for the Compressor, Sidechain,
Echo delay and Space reverb (docs/devices-display-first.md sections 7 and 10, the user's picks DD4 and DD3).
  python3 tools/ui-tests/taskDV_4.py [index.html] [out dir] [old index.html for the old-project check]
Checks, on each of the four devices: closed with Hover reveal, the dock is hidden at rest and the values line shows, without the values the picture
already writes, clear of every handle and of the picture's own words; on hover the dock shows its controls in one row (knob, label over value), Gain
after them, all inside the device and clear of every handle, on one glass panel; the preset pill shows with it, clear of the handles; Tab and a tap
on the picture reveal it too; a knob and a short fader in the dock change their values at a sensible speed; a handle under the hovered device can
still be dragged (the Echo delay's low cut, the Compressor's attack); On the picture: one chip per control that has a handle, each beside its handle,
none over another or over a handle, the chips follow a dragged handle, More holds the preset and Gain, which work; the eye menu offers On the
picture as ready; the rail open shows the rail (no dock, no chips) and keeps the mode; tooltips on every control; Solid; nothing read or uploaded
at rest; switching states never changes a value; kOpen/kMode saved; an old project opens the same; screenshots of the three states at Glass,
Light and Solid; no console errors."""
import sys, os, json, math
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
INIT = "if(!sessionStorage.getItem('dv4')){sessionStorage.setItem('dv4','1');localStorage.setItem('audiolab-ui',JSON.stringify({splash:false,lat3:1}))}"
TYPES = ['comp', 'side', 'delay', 'reverb']
NAMES = {'comp': 'Compressor', 'side': 'Sidechain', 'delay': 'Echo delay', 'reverb': 'Space reverb'}
RECIPE = {'tracks': [{'name': 'P', 'preset': 'pluck', 'fx': [{'type': t} for t in TYPES],
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
        R0("(()=>{const q=S.tracks[0].fx;q[0].kOpen=false;q[0].p.threshold=-30;q[1].kOpen=false;q[1].kMode='picture';q[2].kOpen=true;q[3].kOpen=false;q[3].kMode='hover';renderFx();return 1})()")
        old_state = json.loads(R0("JSON.stringify(S.tracks[0].fx.map(f=>({ty:f.type,k:f.kOpen===undefined?null:f.kOpen,m:f.kMode||null,p:f.p})))"))
        pg0.evaluate("()=>AudioLab.run('packProject(curP()).then(b=>b.arrayBuffer()).then(a=>{const u=new Uint8Array(a);let s=\"\";for(let i=0;i<u.length;i+=32768)s+=String.fromCharCode.apply(null,u.subarray(i,i+32768));window.__pk=btoa(s)})')")
        pg0.wait_for_timeout(800); old_file = pg0.evaluate('() => window.__pk'); b0.close()
    b, pg, errs = page(p, SRC)
    R = lambda c: pg.evaluate('c => AudioLab.run(c)', c); J = lambda c: json.loads(R('JSON.stringify(' + c + ')'))
    ok(tuple(map(int, R('VERSION').split('.'))) >= (0, 295), 'version 0.295 or later', R('VERSION'))
    pg.evaluate('r => AudioLab.build(r)', RECIPE); pg.wait_for_timeout(1200)
    E = lambda i: "fxin.querySelector('.dev[data-id=\"'+curT().fx[%d].id+'\"]')" % i
    FID = lambda i: J("curT().fx[%d].id" % i)
    def scroll_to(i):
        R("(()=>{const D=%s;fxin.scrollLeft+=D.getBoundingClientRect().left-fxin.getBoundingClientRect().left-40;return 1})()" % E(i)); pg.wait_for_timeout(250)
    def box(i, sel=None):
        return J("(()=>{const D=%s,e=%s;if(!e)return null;const r=e.getBoundingClientRect();return[r.left,r.top,r.width,r.height]})()" % (E(i), ("D.querySelector('%s')" % sel) if sel else 'D'))
    def shot(i, name):
        bx = box(i); pg.screenshot(path=os.path.join(OUT, name + '.png'), clip={'x': bx[0] - 4, 'y': bx[1] - 4, 'width': bx[2] + 8, 'height': bx[3] + 8})
    def setall(k, m):
        R("(()=>{for(const f of curT().fx){f.kOpen=%s;f.kMode='%s'}renderFx();return 1})()" % ('true' if k else 'false', m)); pg.wait_for_timeout(400)
    def hover(i, dx=None, dy=40):
        bx = box(i); pg.mouse.move(bx[0] + (dx if dx is not None else bx[2] / 2), bx[1] + dy); pg.wait_for_timeout(450)
    # handles, dock, values line and pill in the device body's pixels, from the page
    GEO = """(()=>{const D=%s,B=D.querySelector('.devb'),own=dvOwnOf(D),Hd=dvHandles(D,own,own.type),r=e=>e?[e.offsetLeft,e.offsetTop,e.offsetWidth,e.offsetHeight]:null,
      S=B.querySelector(':scope>.dfs'),G=B.querySelector(':scope>.dug'),V=B.querySelector(':scope>.dvval'),P=B.querySelector(':scope>.dvdpre'),R=B.querySelector(':scope>.dvrail');
      const dk=S&&G?[S.offsetLeft,S.offsetTop,G.offsetLeft+G.offsetWidth-S.offsetLeft,Math.max(S.offsetHeight,G.offsetHeight)]:null;
      return{BW:B.clientWidth,BH:B.clientHeight,H:Hd?Hd.L.map(q=>[q.x,q.y,q.l]):[],clear:Hd?Hd.clear:[],dock:dk,val:r(V),valT:V?V.textContent:'',pre:r(P),rail:R&&!R.hidden?r(R):null,
        op:S?+getComputedStyle(S).opacity:-1,pop:P?+getComputedStyle(P).opacity:-1,vop:V?+getComputedStyle(V).opacity:-1,cls:D.className}})()"""
    def hits(rc, H, m=9):
        return [h for h in H if rc[0] - m < h[0] < rc[0] + rc[2] + m and rc[1] - m < h[1] < rc[1] + rc[3] + m]
    def over(a, b2, m=0):
        return a[0] < b2[0] + b2[2] + m and b2[0] < a[0] + a[2] + m and a[1] < b2[1] + b2[3] + m and b2[1] < a[1] + a[3] + m
    P0 = J("JSON.stringify(curT().fx.map(f=>f.p))")
    # ---------- Hover reveal: the bottom dock ----------
    setall(False, 'hover')
    for i, ty in enumerate(TYPES):
        nm = NAMES[ty]; scroll_to(i); pg.mouse.move(5, 5); pg.wait_for_timeout(350)
        g = J(GEO % E(i))
        ok('dvdock' in g['cls'] and g['op'] < .05 and g['pop'] < .05 and g['vop'] > .5, nm + ': closed with Hover reveal, the dock and the preset pill hidden at rest, the values line shown', (g['op'], g['pop'], g['vop']))
        v = g['val']; hv = hits(v, g['H'], 7) if v else ['none']; cl = [c for c in g['clear'] if over(v, c)] if v else []
        ok(v and not hv and not cl and v[0] >= 0 and v[0] + v[2] <= g['BW'], nm + ': the values line is clear of every handle and of the picture\'s own words', (v, hv, cl))
        sk = {'comp': ['Threshold', 'Ratio'], 'delay': ['Time', 'Feedback', 'Mix'], 'reverb': ['Decay', 'Pre-delay'], 'side': []}[ty]
        ok(all(s + ' ' not in g['valT'] for s in sk) and len(g['valT']) > 8, nm + ': the values line leaves out what the picture already writes', g['valT'])
        shot(i, 'dv4_%s_hover_rest' % ty)
        hover(i, dy=30); g = J(GEO % E(i))
        row = J("(()=>{const D=%s,B=D.querySelector('.devb'),c=[...B.querySelectorAll(':scope>:is(.dfs,.dug) :is(.kn,.vb)')].map(e=>{const r=e.getBoundingClientRect();return r.top+r.height/2}),lv=[...B.querySelectorAll(':scope>.dfs .kn')].map(e=>{const a=e.querySelector(':scope>span').getBoundingClientRect(),o=e.querySelector(':scope>output').getBoundingClientRect();return a.bottom<=o.top+1&&Math.abs(a.left-o.left)<2});return{n:c.length,spread:Math.max(...c)-Math.min(...c),lv}})()" % E(i))
        ok(g['op'] > .95 and row['n'] >= 5 and row['spread'] < 4 and all(row['lv']), nm + ': on hover the dock shows every control in one row, each knob\'s label over its value', row)
        d = g['dock']; hd = hits(d, g['H'], 8)
        ok(d[0] >= 4 and d[0] + d[2] <= g['BW'] - 4 and d[1] >= 0 and d[1] + d[3] <= g['BH'] and not hd, nm + ': the dock lies inside the device and over no handle', (d, g['BW'], g['BH'], hd))
        rl = g['rail']; ok(rl and rl[0] <= d[0] and rl[1] <= d[1] + 1 and rl[0] + rl[2] >= d[0] + d[2] and rl[1] + rl[3] >= d[1] + d[3] - 1, nm + ': one glass panel behind the whole dock', (rl, d))
        pr = g['pre']; ok(pr and g['pop'] > .95 and not hits(pr, g['H'], 8) and not over(pr, d), nm + ': the preset pill shows with the dock, over no handle and clear of the dock', (pr, g['pop']))
        ok(g['vop'] < .05, nm + ': the values line steps aside while the dock shows', g['vop'])
        shot(i, 'dv4_%s_hover_revealed' % ty)
        pg.mouse.move(5, 5); pg.wait_for_timeout(350)
    # keyboard and touch
    scroll_to(0); pg.mouse.move(5, 5); pg.wait_for_timeout(300)
    R("%s.querySelector('.dfs .kn').setAttribute('tabindex','0');%s.querySelector('.dfs .kn').focus();1" % (E(0), E(0))); pg.wait_for_timeout(350)
    ok(J(GEO % E(0))['op'] > .95, 'keyboard focus inside the dock shows it')
    R("document.activeElement.blur();1"); pg.wait_for_timeout(300)
    bx = box(2); tx, ty_ = bx[0] + bx[2] * .6, bx[1] + 60
    # a synthetic touch has no real pointer behind it, so the panel's own setPointerCapture is let through quietly for this one tap
    R("(()=>{const el=%s.querySelector('.dvval'),sp=Element.prototype.setPointerCapture;Element.prototype.setPointerCapture=function(){try{sp.apply(this,arguments)}catch(e){}};try{for(const t of['pointerdown','pointerup'])el.dispatchEvent(new PointerEvent(t,{bubbles:true,cancelable:true,pointerType:'touch',clientX:%f,clientY:%f,isPrimary:true}))}finally{Element.prototype.setPointerCapture=sp}return 1})()" % (E(2), tx, ty_)); pg.wait_for_timeout(350)
    ok(J(GEO % E(2))['op'] > .95, 'a tap on the picture shows the dock (touch)')
    R("%s.classList.remove('dvshow');1" % E(2)); pg.wait_for_timeout(300)
    # the dock's controls
    scroll_to(0); hover(0, dy=30)
    k = box(0, '.dfs .kn[data-c$=":attack"]'); a0 = J("curT().fx[0].p.attack")
    pg.mouse.move(k[0] + 12, k[1] + 13); pg.mouse.down(); pg.mouse.move(k[0] + 12, k[1] - 27, steps=5); pg.mouse.up(); pg.wait_for_timeout(300)
    ok(J("curT().fx[0].p.attack") > a0, 'a knob in the dock changes its value (Attack)', (a0, J("curT().fx[0].p.attack")))
    hover(0, dy=30); v = box(0, '.dfs .vb[data-c$=":makeup"]'); m0 = J("curT().fx[0].p.makeup")
    pg.mouse.move(v[0] + 4, v[1] + 15); pg.mouse.down(); pg.mouse.move(v[0] + 4, v[1] - 15, steps=5); pg.mouse.up(); pg.wait_for_timeout(300)
    m1 = J("curT().fx[0].p.makeup")
    ok(m1 > m0 and m1 - m0 < 9, 'a short fader in the dock moves over 150 px for its range, not over its own 30 (Makeup 30 px up)', (m0, m1))
    # a handle under the hovered device can still be dragged: the Echo delay's low cut and the Compressor's attack dot
    scroll_to(2); hover(2, dy=30); g = J(GEO % E(2)); bx = box(2); B0 = J("(()=>{const r=%s.querySelector('.devb').getBoundingClientRect();return[r.left,r.top]})()" % E(2))
    lc = [h for h in g['H'] if h[2] == 'Low cut'][0]; l0 = J("curT().fx[2].p.lowcut")
    pg.mouse.move(B0[0] + lc[0], B0[1] + lc[1]); pg.mouse.down(); pg.mouse.move(B0[0] + lc[0] + 40, B0[1] + lc[1], steps=6); pg.mouse.up(); pg.wait_for_timeout(300)
    ok(J("curT().fx[2].p.lowcut") > l0 * 1.2, 'with the dock shown, the Echo delay\'s low-cut handle is still dragged', (l0, J("curT().fx[2].p.lowcut")))
    scroll_to(0); hover(0, dy=30); g = J(GEO % E(0)); B0 = J("(()=>{const r=%s.querySelector('.devb').getBoundingClientRect();return[r.left,r.top]})()" % E(0))
    at = [h for h in g['H'] if h[2] == 'Attack'][0]; t0 = J("curT().fx[0].p.attack")
    pg.mouse.move(B0[0] + at[0], B0[1] + at[1]); pg.mouse.down(); pg.mouse.move(B0[0] + at[0] + 30, B0[1] + at[1], steps=6); pg.mouse.up(); pg.wait_for_timeout(300)
    ok(J("curT().fx[0].p.attack") > t0, 'with the dock shown, the Compressor\'s attack dot is still dragged', (t0, J("curT().fx[0].p.attack")))
    pg.mouse.move(5, 5); pg.wait_for_timeout(300)
    # ---------- On the picture ----------
    R("(()=>{const q=curT().fx;q.forEach((f,i)=>f.p=JSON.parse(%s)[i]);renderFx();return 1})()" % json.dumps(P0)); pg.wait_for_timeout(300)
    setall(False, 'picture')
    ANC = J("DVANC")
    for i, ty in enumerate(TYPES):
        nm = NAMES[ty]; scroll_to(i); pg.mouse.move(5, 5); pg.wait_for_timeout(350)
        ch = J("""(()=>{const D=%s,B=D.querySelector('.devb'),own=dvOwnOf(D),Hd=dvHandles(D,own,own.type);return{pic:D.classList.contains('dvpic'),dock:D.classList.contains('dvdock'),val:!!B.querySelector(':scope>.dvval'),
          H:Hd.L.map(q=>[q.x,q.y,q.l]),c:[...B.querySelectorAll(':scope>.dvchip')].map(e=>({k:e.dataset.c.split(':').pop(),a:+e.dataset.dva,r:[e.offsetLeft,e.offsetTop,e.offsetWidth,e.offsetHeight],op:+getComputedStyle(e).opacity})),
          more:(()=>{const m=B.querySelector(':scope>.dvmore');return m?[m.offsetLeft,m.offsetTop,m.offsetWidth,m.offsetHeight]:null})(),BW:B.clientWidth,BH:B.clientHeight}})()""" % E(i))
        ks = sorted(c['k'] for c in ch['c'])
        ok(ch['pic'] and not ch['dock'] and not ch['val'] and ks == sorted(ANC[ty].keys()) and all(c['op'] > .9 for c in ch['c']), nm + ': On the picture shows one chip per control with a handle, no dock, no values line', ks)
        far = []; ovl = []; onh = []
        for c in ch['c']:
            h = ch['H'][c['a']]; r = c['r']; dx = max(r[0] - h[0], 0, h[0] - r[0] - r[2]); dy = max(r[1] - h[1], 0, h[1] - r[1] - r[3])
            if math.hypot(dx, dy) > 60: far.append((c['k'], round(math.hypot(dx, dy))))
            if hits(r, ch['H'], 6): onh.append(c['k'])
            for c2 in ch['c']:
                if c2 is not c and over(r, c2['r'], -1): ovl.append(c['k'])
            if not (r[0] >= 0 and r[1] >= 0 and r[0] + r[2] <= ch['BW'] and r[1] + r[3] <= ch['BH']): far.append((c['k'], 'outside'))
        ok(not far, nm + ': each chip sits beside its handle, inside the device', far)
        ok(not ovl and not onh and ch['more'] and not any(over(ch['more'], c['r']) for c in ch['c']), nm + ': no chip covers another chip, a handle or More', (ovl, onh))
        shot(i, 'dv4_%s_picture' % ty)
    # the chips follow a dragged handle (the Compressor's threshold dot); the chip being dragged stays under the mouse
    scroll_to(0); pg.mouse.move(5, 5); pg.wait_for_timeout(300)
    B0 = J("(()=>{const r=%s.querySelector('.devb').getBoundingClientRect();return[r.left,r.top]})()" % E(0)); g = J(GEO % E(0)); th = g['H'][0]
    c0 = box(0, '.dvchip[data-dva="0"]'); pg.mouse.move(B0[0] + th[0], B0[1] + th[1]); pg.mouse.down(); pg.mouse.move(B0[0] + th[0] - 70, B0[1] + th[1], steps=8); pg.wait_for_timeout(150)
    c1 = box(0, '.dvchip[data-dva="0"]'); h1 = J("(()=>{const D=%s,B=D.querySelector('.devb'),r=B.getBoundingClientRect(),q=dvHandles(D,dvOwnOf(D),'comp').L[0];return[r.left+q.x,r.top+q.y]})()" % E(0)); pg.mouse.up(); pg.wait_for_timeout(300)
    dd = max(c1[0] - h1[0], 0, h1[0] - c1[0] - c1[2]) + max(c1[1] - h1[1], 0, h1[1] - c1[1] - c1[3])
    ok(J("curT().fx[0].p.threshold") < -25 and c1[0] != c0[0] and dd < 40, 'the Threshold chip follows its dot while the dot is dragged (it stays beside the moving dot)', (c0[0], c1[0], h1, J("curT().fx[0].p.threshold")))
    # More: the preset and Gain
    fid = FID(0); pg.click('#fxin .dev[data-id="%s"] .dvmore' % fid); pg.wait_for_timeout(300)
    mo = J("(()=>{const D=%s,d=D.querySelector('.dvdrw');return{on:d.classList.contains('on')&&d.offsetWidth>0,h:[...d.querySelectorAll('h5')].map(h=>h.textContent),g:!!d.querySelector('.dug [data-c]'),pre:!!d.querySelector('[data-dup=next]'),in:(()=>{const a=d.getBoundingClientRect(),b=D.querySelector('.devb').getBoundingClientRect();return a.top>=b.top-1&&a.bottom<=b.bottom+1})()}})()" % E(0))
    ok(mo['on'] and mo['h'][0] == 'Preset' and mo['h'][-1] == 'Output' and mo['g'] and mo['pre'] and mo['in'], 'More opens a drawer with the preset and Gain, inside the device', mo)
    gv = box(0, '.dvdrw .dug .vb'); og0 = J("curT().fx[0].p.og||0")
    pg.mouse.move(gv[0] + 4, gv[1] + 15); pg.mouse.down(); pg.mouse.move(gv[0] + 4, gv[1] - 5, steps=4); pg.mouse.up(); pg.wait_for_timeout(300)
    ok((J("curT().fx[0].p.og||0")) > og0, 'Gain works from the drawer', (og0, J("curT().fx[0].p.og||0")))
    pr0 = J("curT().fx[0].p.pre||''"); pg.click('#fxin .dev[data-id="%s"] .dvdrw [data-dup=next]' % fid); pg.wait_for_timeout(500)
    ok(J("curT().fx[0].p.pre||''") != pr0, 'the next-preset arrow works from the drawer', (pr0, J("curT().fx[0].p.pre||''")))
    pg.keyboard.press('Escape'); R("(()=>{const D=%s;if(D.querySelector('.dvdrw.on'))dvMoreToggle(D,false);return 1})()" % E(0)); pg.wait_for_timeout(200)
    # the eye menu
    for i, ty in enumerate(TYPES):
        R("(()=>{const e=%s.querySelector('.dveye');e.dispatchEvent(new MouseEvent('contextmenu',{bubbles:true,cancelable:true,clientX:900,clientY:500}));return 1})()" % E(i)); pg.wait_for_timeout(250)
        mt = R("(document.querySelector('.ctxm,.menu,[role=menu]')||{}).textContent||''"); pg.keyboard.press('Escape'); pg.wait_for_timeout(150)
        ok('On the picture' in mt and 'Not ready' not in mt, NAMES[ty] + ': the eye menu offers On the picture as ready', mt[:60])
    # tooltips on every control (picture, dock and drawer)
    bad = []
    for m in ['picture', 'hover']:
        setall(False, m)
        bad += J("(()=>{const bad=[];for(const D of fxin.querySelectorAll(':scope>.dev.dvf')){const B=D.querySelector('.devb'),d=B.querySelector('.dvdrw');if(d)d.classList.add('on');for(const e of B.querySelectorAll('button,input,select,[data-c]')){if(!(e.title||e.getAttribute('aria-label')||e.dataset.tip||e.closest('[title],[data-tip]')))bad.push(e.outerHTML.slice(0,60))}if(d)d.classList.remove('on')}return bad})()")
    ok(not bad, 'every control has a tooltip, in the dock, on the picture and in the drawer', bad[:4])
    # the rail open
    setall(False, 'picture'); fid = FID(1)
    pg.click('#fxin .dev[data-id="%s"] .dveye' % fid); pg.wait_for_timeout(500)
    ro = J("(()=>{const D=%s;return{pic:D.classList.contains('dvpic'),dock:D.classList.contains('dvdock'),chips:D.querySelectorAll('.devb>.dvchip').length,side:D.querySelector('.dfs').offsetWidth,k:curT().fx[1].kOpen,m:curT().fx[1].kMode}})()" % E(1))
    ok(not ro['pic'] and not ro['dock'] and ro['chips'] == 0 and ro['side'] > 100 and ro['k'] is True and ro['m'] == 'picture', 'the rail open: no chips, no dock, the controls on the rail, the mode kept', ro)
    pg.click('#fxin .dev[data-id="%s"] .dveye' % fid); pg.wait_for_timeout(500)
    ok(J("%s.classList.contains('dvpic')&&curT().fx[1].kOpen===false" % E(1)), 'closed again: back on the picture')
    # engine and no cost at rest
    eng = J("{on:!!DVG.g}")
    if eng['on']:
        setall(False, 'hover'); scroll_to(0); pg.mouse.move(5, 5); pg.wait_for_timeout(2800)
        a = J("{s:DVG.n.sync,f:DVG.n.flatDirty,u:DVG.g.stats.flatUploads,p:DV4.n.place,v:DV4.n.val}"); pg.wait_for_timeout(1500)
        b2 = J("{s:DVG.n.sync,f:DVG.n.flatDirty,u:DVG.g.stats.flatUploads,p:DV4.n.place,v:DV4.n.val}")
        ok(a == b2, 'Hover reveal at rest: no page reads, no picture refreshes, no uploads, no placing', (a, b2))
        hover(0, dy=30); pg.wait_for_timeout(200)
        fc = J("(()=>{const D=%s,R=D.querySelector('.devb>.dvrail'),P=D.querySelector('.devb>.dvdpre');return{r:DVG.faces.has(R._dvg),p:DVG.faces.has(P._dvg)}})()" % E(0))
        ok(fc['r'] and fc['p'], 'the dock and the preset pill are glass faces of the devices engine', fc)
        pg.mouse.move(5, 5); setall(False, 'picture'); scroll_to(0); pg.wait_for_timeout(2800)
        a = J("{s:DVG.n.sync,f:DVG.n.flatDirty,u:DVG.g.stats.flatUploads,p:DV4.n.place}"); pg.wait_for_timeout(1500)
        b2 = J("{s:DVG.n.sync,f:DVG.n.flatDirty,u:DVG.g.stats.flatUploads,p:DV4.n.place}")
        ok(a == b2, 'On the picture at rest: no page reads, no picture refreshes, no uploads, no placing', (a, b2))
    else:
        ok(True, 'engine not on in this browser'); ok(True, 'no engine faces'); ok(True, 'no engine: nothing to upload')
    # screenshots: the three states at Glass and Light, and Solid
    for lv in ['glass', 'light', 'solid']:
        R("(()=>{UI.gl=Object.assign({},UI.gl||{},{lv:'%s'});gleApply();renderFx();return 1})()" % lv); pg.wait_for_timeout(500)
        for i, ty in enumerate(TYPES):
            if lv == 'solid' and ty in ('side', 'reverb'): continue
            setall(True, 'hover'); scroll_to(i); pg.mouse.move(5, 5); pg.wait_for_timeout(400); shot(i, 'dv4_%s_%s_1_rail' % (ty, lv))
            setall(False, 'hover'); scroll_to(i); hover(i, dy=30); shot(i, 'dv4_%s_%s_2_hover' % (ty, lv)); pg.mouse.move(5, 5); pg.wait_for_timeout(300)
            setall(False, 'picture'); scroll_to(i); pg.wait_for_timeout(300); shot(i, 'dv4_%s_%s_3_picture' % (ty, lv))
        if lv == 'solid':
            setall(False, 'hover'); scroll_to(0); hover(0, dy=30)
            so = J("(()=>{const D=%s,c=D.querySelector('.devb>.dvrail'),P=D.querySelector('.devb>.dvdpre');const al=e=>{const m=/rgba?\\(([^)]+)\\)/.exec(getComputedStyle(e).backgroundColor);const a=m?m[1].split(',').map(Number):[0,0,0,0];return a.length>3?a[3]:1};return{dvg:document.body.classList.contains('dvg'),r:al(c),p:al(P)}})()" % E(0))
            ok(not so['dvg'] and so['r'] >= .85 and so['p'] >= .85, 'Solid: no engine, the dock and the preset pill on a near-solid tint', so)
            pg.mouse.move(5, 5)
    R("(()=>{UI.gl=Object.assign({},UI.gl||{},{lv:'glass'});gleApply();return 1})()"); pg.wait_for_timeout(300)
    # values never change by switching states; kOpen and kMode saved as set
    R("(()=>{const q=curT().fx;q.forEach((f,i)=>f.p=JSON.parse(%s)[i]);renderFx();return 1})()" % json.dumps(P0)); pg.wait_for_timeout(300)
    for _ in range(3):
        for m in ['picture', 'hover']:
            R("(()=>{for(const f of curT().fx){f.kMode='%s';f.kOpen=!f.kOpen}renderFx();return 1})()" % m); pg.wait_for_timeout(80)
    ok(J("JSON.stringify(curT().fx.map(f=>f.p))") == P0, 'switching between the three states never changes any of the four devices\' values')
    R("(()=>{const q=curT().fx;q[0].kOpen=false;q[0].kMode='picture';q[1].kOpen=false;q[1].kMode='hover';renderFx();renderFx();return 1})()")
    sv = J("(()=>{const q=JSON.parse(JSON.stringify(S)).tracks[0].fx;return[q[0].kOpen,q[0].kMode,q[1].kOpen,q[1].kMode]})()")
    ok(sv == [False, 'picture', False, 'hover'], 'kOpen and kMode are saved as set', sv)
    # an old project
    if old_file:
        R("(()=>{const u=Uint8Array.from(atob('%s'),c=>c.charCodeAt(0));openProjectBlob(new File([u],'old-dv4.audiolab'));return 1})()" % old_file)
        pg.wait_for_timeout(4000)
        now = J("S.tracks[0].fx.map(f=>({ty:f.type,k:f.kOpen===undefined?null:f.kOpen,m:f.kMode||null,p:f.p}))")
        ok(now == old_state, 'an old project opens with the same values, rails and modes', (len(json.dumps(now)), len(json.dumps(old_state))))
        st = J("[...fxin.querySelectorAll(':scope>.dev[data-d=fx]')].map(D=>[D.classList.contains('dvdock'),D.classList.contains('dvpic'),D.classList.contains('dvshut')])")
        ok(st == [[True, False, True], [False, True, True], [False, False, False], [True, False, True]], 'its devices show the dock, the chips or the rail as stored', st)
    errs = [e for e in errs if 'fetching the script' not in e and 'Failed to load resource' not in e]
    ok(not errs, 'no console errors', errs[:3])
    b.close()
print('%d of %d checks pass' % (N[1], N[0]))
if FAIL: print('FAILED:', FAIL); sys.exit(1)
