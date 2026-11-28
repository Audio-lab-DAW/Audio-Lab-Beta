# for: task DV-5
"""Task DV-5: display-first devices, step 5: the synths (docs/devices-display-first.md sections 7 and 10).
  python3 tools/ui-tests/taskDV_5.py [index.html] [out dir] [old index.html for the old-project check]
Checks: the rule (DVIRULE): Venom, Plant, Wavetable, Orbit, Vector FM, Bounce start with the rail open; Saw lead, Square lead, Soft pad, Strings,
Pluck, Soft keys start closed with hover reveal when the user adds one from the instrument browser (a real click), while a script-built track keeps
no stored state; for each basic instrument: closed, the dock hidden at rest and the values line shown without Attack and Release, the picture filling
the box; on hover the dock in two rows (the three knobs, then the envelope and Level) with Gain after it, inside the device, at the bottom, the preset
pill with Wave clear of the eye's pill; Tab reveals it; a knob and a short fader in the dock change values; On the picture: six chips beside their
places, none over another or over More, More holds the preset, Wave, Detune, Level and Gain; the eye menu offers On the picture as ready; the rail open
shows no dock and no chips; tooltips on every control; the big synths open and close with no error and fall back to hover reveal; switching states
never changes a value; kOpen/kMode saved; an old project opens the same; screenshots of the three states at Glass, Light and Solid; no console errors."""
import sys, os, json, math
from playwright.sync_api import sync_playwright
SRC = open(sys.argv[1] if len(sys.argv) > 1 else 'index.html', encoding='utf-8').read()
OUT = sys.argv[2] if len(sys.argv) > 2 else '.'; os.makedirs(OUT, exist_ok=True)
OLD = sys.argv[3] if len(sys.argv) > 3 else None
N = [0, 0]; FAIL = []
def ok(c, m, info=''):
    N[0] += 1
    if c: N[1] += 1; print('ok   ', m, info if info != '' else '')
    else: FAIL.append(m); print('FAIL ', m, info)
INIT = "if(!sessionStorage.getItem('dv5')){sessionStorage.setItem('dv5','1');localStorage.setItem('audiolab-ui',JSON.stringify({splash:false,lat3:1}))}"
BASIC = ['saw', 'square', 'pad', 'strings', 'pluck', 'keys']
BIG = ['venom', 'plant', 'wtab', 'orb', 'vfm', 'bball']
ALL = BASIC + BIG
RECIPE = {'tracks': [{'name': t, 'preset': t, 'clips': [{'start': 0, 'len': 4, 'notes': [{'p': 52, 's': 0, 'l': 1, 'v': .9}]}]} for t in ALL]}
def page(p, src):
    b = p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required']); pg = b.new_page(viewport={'width': 1800, 'height': 1000}); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)[:300]))
    pg.on('console', lambda m: errs.append('console: ' + m.text[:300]) if m.type == 'error' else None)
    pg.add_init_script(INIT)
    pg.route('https://app.test/**', lambda r: r.fulfill(body=src, content_type='text/html') if r.request.url.endswith('/') or r.request.url.endswith('index.html') else r.fulfill(status=404, body=''))
    pg.goto('https://app.test/'); pg.wait_for_function('() => window.AudioLab && window.AudioLab.version', timeout=60000); pg.wait_for_timeout(2500)
    return b, pg, errs
D = "fxin.querySelector('.dev[data-d=inst]')"
with sync_playwright() as p:
    old_file = None; old_state = None
    if OLD:
        b0, pg0, e0 = page(p, open(OLD, encoding='utf-8').read())
        pg0.evaluate('r => AudioLab.build(r)', RECIPE); pg0.wait_for_timeout(800)
        R0 = lambda c: pg0.evaluate('c => AudioLab.run(c)', c)
        R0("(()=>{const T=S.tracks;T[0].inst.kOpen=false;T[0].inst.cutoff=900;T[1].inst.kOpen=false;T[1].inst.kMode='picture';T[2].inst.kOpen=true;T[6].inst.kOpen=false;return 1})()")
        old_state = json.loads(R0("JSON.stringify(S.tracks.map(t=>t.inst))"))
        pg0.evaluate("()=>AudioLab.run('packProject(curP()).then(b=>b.arrayBuffer()).then(a=>{const u=new Uint8Array(a);let s=\"\";for(let i=0;i<u.length;i+=32768)s+=String.fromCharCode.apply(null,u.subarray(i,i+32768));window.__pk=btoa(s)})')")
        pg0.wait_for_timeout(800); old_file = pg0.evaluate('() => window.__pk'); b0.close()
    b, pg, errs = page(p, SRC)
    R = lambda c: pg.evaluate('c => AudioLab.run(c)', c); J = lambda c: json.loads(R('JSON.stringify(' + c + ')'))
    ok(tuple(map(int, R('VERSION').split('.'))) >= (0, 315), 'version 0.315 or later', R('VERSION'))
    pg.evaluate('r => AudioLab.build(r)', RECIPE); pg.wait_for_timeout(1200)
    ok(J("S.tracks.every(t=>t.inst.kOpen===undefined&&t.inst.kMode===undefined)"), 'a script-built song keeps no stored rail state (it opens as stored)')
    ok(J("Object.keys(DVIRULE).sort()") == sorted(ALL) and J("BIG=%s,BIG.every(k=>DVIRULE[k].open)&&!%s.some(k=>DVIRULE[k].open)" % (json.dumps(BIG), json.dumps(BASIC))), 'the rule: the big synths start open, the basic ones closed')
    def sel(i):
        R("(()=>{selectTrack(S.tracks[%d].id);renderFx();return 1})()" % i); pg.wait_for_timeout(350)
    def setst(i, k, m):
        R("(()=>{const I=S.tracks[%d].inst;I.kOpen=%s;I.kMode='%s';selectTrack(S.tracks[%d].id);renderFx();return 1})()" % (i, 'true' if k else 'false', m, i)); pg.wait_for_timeout(350)
    def box(sel_=None):
        return J("(()=>{const e=%s;if(!e)return null;const r=e.getBoundingClientRect();return[r.left,r.top,r.width,r.height]})()" % ((D + ".querySelector('%s')" % sel_) if sel_ else D))
    def shot(name):
        bx = box(); pg.screenshot(path=os.path.join(OUT, name + '.png'), clip={'x': bx[0] - 4, 'y': bx[1] - 4, 'width': min(bx[2] + 8, 1795 - bx[0]), 'height': bx[3] + 8})
    def hover(dy=60):
        bx = box(); pg.mouse.move(bx[0] + bx[2] / 2, bx[1] + dy); pg.wait_for_timeout(450)
    def over(a, b2, m=0):
        return a[0] < b2[0] + b2[2] + m and b2[0] < a[0] + a[2] + m and a[1] < b2[1] + b2[3] + m and b2[1] < a[1] + a[3] + m
    GEO = """(()=>{const D=%s,B=D.querySelector('.devb'),r=e=>e?[e.offsetLeft,e.offsetTop,e.offsetWidth,e.offsetHeight]:null,S=B.querySelector(':scope>.dfs'),G=B.querySelector(':scope>.dug'),
      V=B.querySelector(':scope>.dvval'),P=B.querySelector(':scope>.dvdpre'),T=B.querySelector(':scope>.dvtr'),cv=B.querySelector('canvas.duviz'),kn=S?[...S.querySelectorAll('.pg-kn .kn')].map(e=>e.getBoundingClientRect().top):[],
      vb=S?[...S.querySelectorAll('.pg-env [data-c],.pg-lv [data-c]')].map(e=>e.getBoundingClientRect().top):[];
      return{BW:B.clientWidth,BH:B.clientHeight,dfs:r(S),dug:r(G),val:r(V),valT:V?V.textContent:'',pre:r(P),eye:r(T),wave:!!(P&&P.querySelector('select[data-x],.dvdtb select')),cvw:cv?cv.clientWidth:0,
        op:S?+getComputedStyle(S).opacity:-1,pop:P?+getComputedStyle(P).opacity:-1,vop:V?+getComputedStyle(V).opacity:-1,kn,vb,cls:D.className}})()""" % D
    # ---------- the starting state from the instrument browser (a real click on Add) ----------
    for k in ['pluck', 'wtab']:
        n0 = J("S.tracks.length")
        R("(()=>{openBrowser(null);ib.sel='%s';$('#ibAdd').disabled=false;return 1})()" % k); pg.wait_for_timeout(400)
        pg.click('#ibAdd'); pg.wait_for_timeout(700)
        st = J("(()=>{const t=S.tracks.find(t=>t.id===selT);return{n:S.tracks.length,p:t&&t.inst.preset,k:t&&t.inst.kOpen===undefined?null:t&&t.inst.kOpen,shut:!!fxin.querySelector('.dev[data-d=inst].dvshut')}})()")
        if k == 'pluck': ok(st['n'] == n0 + 1 and st['p'] == 'pluck' and st['k'] is False and st['shut'], 'Pluck added from the browser starts closed with hover reveal', st)
        else: ok(st['n'] == n0 + 1 and st['p'] == 'wtab' and st['k'] is None and not st['shut'], 'Wavetable added from the browser starts with the rail open', st)
        R("(()=>{const t=S.tracks.find(t=>t.id===selT);S.tracks.splice(S.tracks.indexOf(t),1);selectTrack(S.tracks[0].id);renderFx();return 1})()"); pg.wait_for_timeout(300)
    P0 = J("JSON.stringify(S.tracks.map(t=>t.inst))")
    # ---------- the basic instruments: hover reveal, the dock ----------
    for i, ty in enumerate(BASIC):
        setst(i, False, 'hover'); pg.mouse.move(5, 5); pg.wait_for_timeout(350); g = J(GEO)
        ok('dvdock' in g['cls'] and g['op'] < .05 and g['pop'] < .05 and g['vop'] > .5 and g['cvw'] > g['BW'] * .8, ty + ': closed, the dock and pill hidden at rest, the values line shown, the picture fills the box', (g['op'], g['pop'], g['vop'], g['cvw'], g['BW']))
        ok('Attack' not in g['valT'] and 'Release' not in g['valT'] and 'Resonance' in g['valT'], ty + ': the values line leaves out what the picture writes', g['valT'])
        hover(); g = J(GEO)
        d, gg, pr, ey = g['dfs'], g['dug'], g['pre'], g['eye']
        inside = d[0] >= 0 and gg[0] + gg[2] <= g['BW'] and d[1] + d[3] <= g['BH'] and d[1] > g['BH'] * .45
        rows = len(g['kn']) == 3 and len(g['vb']) == 5 and max(g['kn']) < min(g['vb']) and max(g['kn']) - min(g['kn']) < 3
        ok(g['op'] > .95 and inside and rows and gg[0] >= d[0] + d[2] - 2, ty + ': on hover the dock shows in two rows (knobs, then envelope and Level), Gain after it, at the bottom inside the device', (d, gg, g['kn'], g['vb']))
        ok(g['pop'] > .95 and g['wave'] and not over(pr, ey) and pr[0] >= 0, ty + ': the preset pill with Wave shows, clear of the eye', (pr, ey))
        if i == 0: shot('dv5_%s_dock' % ty)
        pg.mouse.move(5, 5); pg.wait_for_timeout(300)
    # Tab into the dock
    setst(0, False, 'hover'); pg.mouse.move(5, 5); pg.wait_for_timeout(300)
    R("(()=>{%s.querySelector('.dvdpre select').focus();return 1})()" % D); pg.keyboard.press('Tab'); pg.wait_for_timeout(400)
    ok(J(GEO)['op'] > .95, 'Tab (keyboard focus inside) shows the dock')
    R("document.activeElement.blur();1"); pg.wait_for_timeout(300)
    # a knob and a short fader in the dock
    hover(); k = box('.dfs .kn[data-c$=":cutoff"]'); c0 = J("S.tracks[0].inst.cutoff")
    pg.mouse.move(k[0] + 12, k[1] + 13); pg.mouse.down(); pg.mouse.move(k[0] + 12, k[1] - 27, steps=5); pg.mouse.up(); pg.wait_for_timeout(300)
    ok(J("S.tracks[0].inst.cutoff") > c0, 'a knob in the dock changes its value (Cutoff)', (c0, J("S.tracks[0].inst.cutoff")))
    hover(); v = box('.dfs .vb[data-c$=":s"]'); s0 = J("S.tracks[0].inst.s")
    pg.mouse.move(v[0] + 4, v[1] + 15); pg.mouse.down(); pg.mouse.move(v[0] + 4, v[1] + 45, steps=5); pg.mouse.up(); pg.wait_for_timeout(300)
    s1 = J("S.tracks[0].inst.s")
    ok(s1 < s0 and s0 - s1 < .3, 'a short fader in the dock moves over 150 px for its range (Sustain 30 px down)', (s0, s1))
    pg.mouse.move(5, 5); pg.wait_for_timeout(300)
    # ---------- On the picture ----------
    R("(()=>{const P=JSON.parse(%s);S.tracks.forEach((t,i)=>Object.assign(t.inst,P[i]));renderFx();return 1})()" % json.dumps(P0)); pg.wait_for_timeout(200)
    for i, ty in enumerate(BASIC):
        setst(i, False, 'picture'); pg.mouse.move(5, 5); pg.wait_for_timeout(350)
        ch = J("""(()=>{const D=%s,B=D.querySelector('.devb'),own=dvOwnOf(D),Hd=dvHandles(D,own,own.preset);return{pic:D.classList.contains('dvpic'),dock:D.classList.contains('dvdock'),val:!!B.querySelector(':scope>.dvval'),
          H:Hd.L.map(q=>[q.x,q.y,q.l]),c:[...B.querySelectorAll(':scope>.dvchip')].map(e=>({k:e.dataset.c.split(':').pop(),a:+e.dataset.dva,r:[e.offsetLeft,e.offsetTop,e.offsetWidth,e.offsetHeight]})),
          more:(()=>{const m=B.querySelector(':scope>.dvmore');return m?[m.offsetLeft,m.offsetTop,m.offsetWidth,m.offsetHeight]:null})(),BW:B.clientWidth,BH:B.clientHeight}})()""" % D)
        ks = sorted(c['k'] for c in ch['c'])
        ok(ch['pic'] and not ch['dock'] and not ch['val'] and ks == sorted(['cutoff', 'res', 'a', 'd', 's', 'r']), ty + ': On the picture shows six chips, no dock, no values line', ks)
        far = []; ovl = []
        for c in ch['c']:
            h = ch['H'][c['a']]; r = c['r']; dd = math.hypot(max(r[0] - h[0], 0, h[0] - r[0] - r[2]), max(r[1] - h[1], 0, h[1] - r[1] - r[3]))
            if dd > 75: far.append((c['k'], round(dd)))
            if not (r[0] >= 0 and r[1] >= 0 and r[0] + r[2] <= ch['BW'] and r[1] + r[3] <= ch['BH']): far.append((c['k'], 'outside'))
            for c2 in ch['c']:
                if c2 is not c and over(r, c2['r'], -1): ovl.append(c['k'])
        ok(not far, ty + ': each chip sits near its place in the picture, inside the device', far)
        ok(not ovl and ch['more'] and not any(over(ch['more'], c['r']) for c in ch['c']), ty + ': no chip covers another chip or More', ovl)
    setst(0, False, 'picture'); pg.click('#fxin .dev[data-d=inst] .dvmore'); pg.wait_for_timeout(300)
    mo = J("(()=>{const d=%s.querySelector('.dvdrw');return{on:d.classList.contains('on')&&d.offsetWidth>0,h:[...d.querySelectorAll('h5')].map(h=>h.textContent),k:[...d.querySelectorAll('[data-c]')].map(e=>e.dataset.c.split(':').pop()),wave:!!d.querySelector('.ndtb select'),pre:!!d.querySelector('.dspr select')}})()" % D)
    ok(mo['on'] and mo['h'] == ['Preset', 'Sound', 'Output'] and 'det' in mo['k'] and 'gain' in mo['k'] and mo['wave'] and mo['pre'], 'More holds the preset, Wave and Detune, Level and Gain', mo)
    dv = box('.dvdrw .kn[data-c$=":det"]'); d0 = J("S.tracks[0].inst.det")
    pg.mouse.move(dv[0] + 12, dv[1] + 12); pg.mouse.down(); pg.mouse.move(dv[0] + 12, dv[1] - 28, steps=5); pg.mouse.up(); pg.wait_for_timeout(300)
    ok(J("S.tracks[0].inst.det") > d0, 'Detune works from the drawer', (d0, J("S.tracks[0].inst.det")))
    R("(()=>{const D=%s;if(D.querySelector('.dvdrw.on'))dvMoreToggle(D,false);return 1})()" % D)
    R("(()=>{const e=%s.querySelector('.dveye');e.dispatchEvent(new MouseEvent('contextmenu',{bubbles:true,cancelable:true,clientX:900,clientY:500}));return 1})()" % D); pg.wait_for_timeout(250)
    mt = R("(document.querySelector('.ctxm,.menu,[role=menu]')||{}).textContent||''"); pg.keyboard.press('Escape'); pg.wait_for_timeout(150)
    ok('On the picture' in mt and 'Not ready' not in mt, 'the eye menu offers On the picture as ready on the basic instruments', mt[:60])
    # tooltips
    bad = []
    for m in ['picture', 'hover']:
        for i in range(len(BASIC)):
            setst(i, False, m)
            bad += J("(()=>{const bad=[],D=%s,B=D.querySelector('.devb'),d=B.querySelector('.dvdrw');for(const e of B.querySelectorAll('button,input,select,[data-c]')){if(!(e.title||e.getAttribute('aria-label')||e.dataset.tip||e.closest('[title],[data-tip]')))bad.push(e.outerHTML.slice(0,60))}return bad})()" % D)
    ok(not bad, 'every control has a tooltip, in the dock, on the picture and in the drawer', bad[:4])
    # the rail open
    setst(1, False, 'picture'); pg.click('#fxin .dev[data-d=inst] .dveye'); pg.wait_for_timeout(500)
    ro = J("(()=>{const D=%s;return{pic:D.classList.contains('dvpic'),dock:D.classList.contains('dvdock'),chips:D.querySelectorAll('.devb>.dvchip').length,side:D.querySelector('.dfs').offsetWidth,k:S.tracks[1].inst.kOpen,m:S.tracks[1].inst.kMode}})()" % D)
    ok(not ro['pic'] and not ro['dock'] and ro['chips'] == 0 and ro['side'] > 100 and ro['k'] is True and ro['m'] == 'picture', 'the rail open: no chips, no dock, the controls on the rail, the mode kept', ro)
    # ---------- the big synths ----------
    bigok = []
    for j, ty in enumerate(BIG):
        i = len(BASIC) + j
        for k, m in [(True, 'hover'), (False, 'hover'), (False, 'picture')]:
            setst(i, k, m); st = J("(()=>{const D=%s;return[D.classList.contains('dvshut'),D.dataset.dvm,D.classList.contains('dvdock'),D.classList.contains('dvpic')]})()" % D)
            if st != [not k, 'hover', False, False]: bigok.append((ty, k, m, st))
    ok(not bigok, 'the big synths open and close; closed they show the revealed panel, and On the picture falls back to hover reveal', bigok)
    # no cost at rest (engine)
    if J("!!DVG.g"):
        setst(0, False, 'hover'); pg.mouse.move(5, 5); pg.wait_for_timeout(2800)
        a = J("{s:DVG.n.sync,f:DVG.n.flatDirty,u:DVG.g.stats.flatUploads,d:DV5.n.dock}"); pg.wait_for_timeout(1500)
        b2 = J("{s:DVG.n.sync,f:DVG.n.flatDirty,u:DVG.g.stats.flatUploads,d:DV5.n.dock}")
        ok(a == b2, 'hover reveal at rest: no page reads, no picture refreshes, no uploads, no placing', (a, b2))
    else: ok(True, 'engine not on in this browser')
    # screenshots
    for lv in ['glass', 'light', 'solid']:
        R("(()=>{UI.gl=Object.assign({},UI.gl||{},{lv:'%s'});gleApply();renderFx();return 1})()" % lv); pg.wait_for_timeout(500)
        for i, ty in enumerate(BASIC + ['wtab', 'orb']):
            if lv != 'glass' and ty not in ('saw', 'keys', 'wtab'): continue
            ii = ALL.index(ty)
            setst(ii, True, 'hover'); pg.mouse.move(5, 5); pg.wait_for_timeout(400); shot('dv5_%s_%s_1_rail' % (ty, lv))
            setst(ii, False, 'hover'); hover(); shot('dv5_%s_%s_2_hover' % (ty, lv)); pg.mouse.move(5, 5); pg.wait_for_timeout(300); shot('dv5_%s_%s_2_rest' % (ty, lv))
            if ty in BASIC: setst(ii, False, 'picture'); pg.wait_for_timeout(300); shot('dv5_%s_%s_3_picture' % (ty, lv))
    R("(()=>{UI.gl=Object.assign({},UI.gl||{},{lv:'glass'});gleApply();return 1})()"); pg.wait_for_timeout(300)
    # values never change by switching states; kOpen/kMode saved
    R("(()=>{const P=JSON.parse(%s);S.tracks.forEach((t,i)=>Object.assign(t.inst,P[i]));return 1})()" % json.dumps(P0))
    V0 = J("JSON.stringify(S.tracks.map(t=>{const o={...t.inst};delete o.kOpen;delete o.kMode;return o}))")
    for i in range(len(ALL)):
        for m in ['picture', 'hover']:
            R("(()=>{const I=S.tracks[%d].inst;I.kMode='%s';I.kOpen=!(I.kOpen!==false);selectTrack(S.tracks[%d].id);renderFx();return 1})()" % (i, m, i)); pg.wait_for_timeout(60)
    ok(J("JSON.stringify(S.tracks.map(t=>{const o={...t.inst};delete o.kOpen;delete o.kMode;return o}))") == V0, 'switching between the three states never changes a value of the twelve synths')
    R("(()=>{const T=S.tracks;T[0].inst.kOpen=false;T[0].inst.kMode='picture';T[7].inst.kOpen=false;T[7].inst.kMode='hover';renderFx();return 1})()")
    sv = J("(()=>{const q=JSON.parse(JSON.stringify(S)).tracks;return[q[0].inst.kOpen,q[0].inst.kMode,q[7].inst.kOpen,q[7].inst.kMode]})()")
    ok(sv == [False, 'picture', False, 'hover'], 'kOpen and kMode are saved as set', sv)
    if old_file:
        R("(()=>{const u=Uint8Array.from(atob('%s'),c=>c.charCodeAt(0));openProjectBlob(new File([u],'old-dv5.audiolab'));return 1})()" % old_file)
        pg.wait_for_timeout(4000)
        now = J("S.tracks.map(t=>t.inst)")
        ok(now == old_state, 'an old project opens with the same instruments, values, rails and modes', (len(json.dumps(now)), len(json.dumps(old_state))))
        sh = []
        for i in [0, 1, 2, 6]:
            sel(i); sh.append(J("(()=>{const D=%s;return[D.classList.contains('dvshut'),D.classList.contains('dvdock'),D.classList.contains('dvpic')]})()" % D))
        ok(sh == [[True, True, False], [True, False, True], [False, False, False], [True, False, False]], 'its instruments show the dock, the chips, the rail or the panel as stored', sh)
    errs = [e for e in errs if 'fetching the script' not in e and 'Failed to load resource' not in e]
    ok(not errs, 'no console errors', errs[:3])
    b.close()
print('%d of %d checks pass' % (N[1], N[0]))
if FAIL: print('FAILED:', FAIL); sys.exit(1)
