"""Task DV-2: display-first devices, step 2 (docs/devices-display-first.md sections 7 and 10).
  python3 tools/ui-tests/taskDV_2.py [index.html] [out dir]
Checks: starting states for a device added by one user action (Compressor, Sidechain, Echo delay, Space reverb closed with hover reveal; Pro EQ
closed, on the picture; Voice open; other effects untouched), none for a bulk of new devices or a script build; the Kick designer's Click menu and
Key track on the rail and still working; the pictures of the drum designers and Voice fill their box and never shrink; fixed-width devices (Psy Bass,
Orbit, Vector FM, Bounce, Sub, Fractal) keep the gain and the pin inside; the values line writes units in amber (L2), hairlines from --lk-hair (W1);
widths of the picked devices; no console errors."""
import sys, os, json
from playwright.sync_api import sync_playwright
SRC = open(sys.argv[1] if len(sys.argv) > 1 else 'index.html', encoding='utf-8').read()
OUT = sys.argv[2] if len(sys.argv) > 2 else '.'; os.makedirs(OUT, exist_ok=True)
N = [0, 0]; FAIL = []
def ok(c, m, info=''):
    N[0] += 1
    if c: N[1] += 1; print('ok   ', m, info if info != '' else '')
    else: FAIL.append(m); print('FAIL ', m, info)
INIT = "if(!sessionStorage.getItem('dv2')){sessionStorage.setItem('dv2','1');localStorage.setItem('audiolab-ui',JSON.stringify({splash:false,lat3:1}))}"
with sync_playwright() as p:
    b = p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required']); pg = b.new_page(viewport={'width': 1800, 'height': 1000}); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)[:300]))
    pg.add_init_script(INIT)
    pg.route('https://app.test/**', lambda r: r.fulfill(body=SRC, content_type='text/html') if r.request.url.endswith('/') or r.request.url.endswith('index.html') else r.fulfill(status=404, body=''))
    pg.goto('https://app.test/'); pg.wait_for_function('() => window.AudioLab && window.AudioLab.version', timeout=60000); pg.wait_for_timeout(2500)
    R = lambda c: pg.evaluate('c => AudioLab.run(c)', c); J = lambda c: json.loads(R('JSON.stringify(' + c + ')'))
    ok(tuple(map(int, R('VERSION').split('.'))) >= (0, 276), 'version 0.276 or later', R('VERSION'))
    pg.evaluate('r => AudioLab.build(r)', {'tracks': [{'name': 'P', 'preset': 'pluck', 'fx': [{'type': 'comp'}, {'type': 'delay'}]}, {'name': 'K', 'preset': 'kick'}]}); pg.wait_for_timeout(1000)
    ok(J("curT().fx.map(f=>f.kOpen===undefined&&f.kMode===undefined)") == [True, True], 'a script build keeps the devices as given (no starting state)')
    # a button whose click adds effects: a real (trusted) click, as from the browser or a menu
    R("(()=>{const b=document.createElement('button');b.id='dvT';b.textContent='add';b.style.cssText='position:fixed;left:4px;top:4px;z-index:99999';b.onclick=()=>{const t=curT();for(const k of (window.DVADD||[]))t.fx.push(mkFx(k));changed(true);renderFx()};document.body.append(b);return 1})()")
    st = {}
    for k in ['comp', 'side', 'delay', 'reverb', 'eq', 'voice', 'drive']:
        R("window.DVADD=['%s'];1" % k); pg.click('#dvT'); pg.wait_for_timeout(350)
        st[k] = J("(f=>[f.type,f.kOpen===undefined?null:f.kOpen,f.kMode||null])(curT().fx[curT().fx.length-1])")
    ok(st['comp'] == ['comp', False, None] and st['side'] == ['side', False, None], 'Compressor and Sidechain start closed with hover reveal', (st['comp'], st['side']))
    ok(st['delay'] == ['delay', False, None] and st['reverb'] == ['reverb', False, None], 'Echo delay and Space reverb start closed with hover reveal', (st['delay'], st['reverb']))
    ok(st['eq'] == ['eq', False, 'picture'], 'Pro EQ starts closed, on the picture', st['eq'])
    ok(st['voice'] == ['voice', True, None], 'Voice starts with the rail open', st['voice'])
    ok(st['drive'] == ['drive', None, None], 'other effects keep today\'s state until their group step', st['drive'])
    cls = J("[...fxin.querySelectorAll(':scope>.dev[data-d=fx]')].slice(-7).map(d=>d.classList.contains('dvshut'))")
    ok(cls == [True, True, True, True, True, False, False], 'the panel shows them that way', cls)
    n0 = J("curT().fx.length"); R("window.DVADD=['comp','comp','delay'];1"); pg.click('#dvT'); pg.wait_for_timeout(350)
    ok(J("curT().fx.slice(%d).every(f=>f.kOpen===undefined)" % n0), 'three new devices in one action (a template, a demo) keep the stored state')
    # Kick designer
    R("selT=S.tracks[1].id;renderFx();fxin.scrollLeft=0;1"); pg.wait_for_timeout(700)
    k = J("(()=>{const D=fxin.querySelector('.dev[data-d=inst]'),c=D.querySelector('.dfv canvas'),dfv=D.querySelector('.dfv'),rail=D.querySelector('.dvrail');return{side:!!D.querySelector('.dfv .kside'),row:!!D.querySelector('.dfs>.dvkrow select[data-s=kclk]'),kt:!!D.querySelector('.dfs>.dvkrow [data-s=kkt]'),cw:Math.round(c.getBoundingClientRect().width),gap:Math.round(rail.getBoundingClientRect().left-dfv.getBoundingClientRect().right),w:D.offsetWidth,tt:D.querySelector('.dvkrow select').title}})()")
    ok(not k['side'] and k['row'] and k['kt'], 'Kick designer: Click menu and Key track moved onto the rail', k)
    ok(k['cw'] >= 430, 'Kick designer: the picture takes the room (was 380 px)', k['cw'])
    ok(k['w'] == 877, 'Kick designer keeps its width (877)', k['w'])
    ok(k['tt'] != '', 'the Click menu has a tooltip', k['tt'])
    pg.select_option('#fxin .dvkrow select[data-s=kclk]', 'snap'); pg.wait_for_timeout(300)
    ok(J("curT().inst.ctype") == 'snap', 'the Click menu still works from the rail')
    ov = J("(()=>{const D=fxin.querySelector('.dev[data-d=inst]'),S=D.querySelector('.dfs'),R=S.getBoundingClientRect();return[...S.querySelectorAll('.kn,.vb,select,button')].filter(e=>e.offsetParent).some(e=>{const q=e.getBoundingClientRect();return q.bottom>R.bottom+1||q.right>R.right+1})})()")
    ok(not ov, 'nothing sticks out of the Kick designer\'s rail')
    pg.screenshot(path=os.path.join(OUT, 'dv2_kick.png'))
    # the other drum designers, Voice; fixed-width devices
    res = {}
    for pr in ['zsnare', 'zclap', 'zhat', 'ztom', 'psyb', 'orb', 'vfm', 'bball', 'sbass', 'crk']:
        R("(()=>{const t=S.tracks[1];for(const key of Object.keys(t.inst))delete t.inst[key];Object.assign(t.inst,JSON.parse(JSON.stringify(PRESETS['%s'])),{preset:'%s'});changed(true);renderFx();return 1})()" % (pr, pr)); pg.wait_for_timeout(500)
        res[pr] = J("(()=>{const D=fxin.querySelector('.dev[data-d=inst]'),R=D.getBoundingClientRect(),c=D.querySelector('.dfv canvas'),g=D.querySelector('.dug').getBoundingClientRect(),p=D.querySelector('.dvtr').getBoundingClientRect(),dfv=D.querySelector('.dfv').getBoundingClientRect();return{fill:D.classList.contains('dvfill'),cw:Math.round(c.getBoundingClientRect().width),dw:Math.round(dfv.width),g:Math.round(R.right-g.right),p:Math.round(R.right-p.right)}})()")
    ok(all(res[k]['fill'] and res[k]['cw'] >= 380 and res[k]['dw'] - res[k]['cw'] <= 2 for k in ['zsnare', 'zclap', 'zhat', 'ztom']), 'Snare, Clap, Hat and Tom designers: the picture fills its box, never under 380 px', {k: (res[k]['cw'], res[k]['dw']) for k in ['zsnare', 'zclap', 'zhat', 'ztom']})
    ok(all(res[k]['g'] >= 0 and res[k]['p'] >= 2 for k in ['psyb', 'orb', 'vfm', 'bball', 'sbass', 'crk']), 'fixed-width devices keep the gain and the pin inside the device', {k: (res[k]['g'], res[k]['p']) for k in ['psyb', 'orb', 'vfm', 'bball', 'sbass', 'crk']})
    R("selT=S.tracks[0].id;renderFx();1"); pg.wait_for_timeout(500)
    v = J("(()=>{const D=[...fxin.querySelectorAll('.dev[data-d=fx]')].find(d=>d.classList.contains('dvfill'));if(!D)return null;const c=D.querySelector('.dfv canvas');return{cw:Math.round(c.getBoundingClientRect().width)}})()")
    ok(v is not None and v['cw'] >= 600, 'Voice: the picture fills its box', v)
    # L2 and W1
    u = J("(()=>{const V=fxin.querySelector('.dev.dvshut .dvval');if(!V)return null;const i=V.querySelector('b i');return{t:V.textContent,unit:i&&i.textContent,col:i&&getComputedStyle(i).color}})()")
    ok(u and u['unit'] and u['col'] == 'rgb(255, 181, 71)', 'values line: units in amber (L2)', u)
    w = J("getComputedStyle(fxin.querySelector('.dvrail')).boxShadow")
    ok('inset' in w, 'rail edge is a hairline (W1)', w[:80])
    errs = [e for e in errs if 'fetching the script' not in e]
    ok(not errs, 'no console errors', errs[:3])
    b.close()
print('%d of %d checks pass' % (N[1], N[0]))
if FAIL: print('FAILED:', FAIL); sys.exit(1)
