#!/usr/bin/env python3
"""Glass step 3 (task GS3, v0.228): the old lens code is gone, the frame-time fixes, the frame-rate read-out.
   python3 tools/ui-tests/taskGS3.py [index.html] [out dir]
The cloud machine has no graphics card (SwiftShader): frame rates here say nothing about the Mac; what is checked is correctness, counts of drawings
and of frames the compositor really put together (tools/ui-tests/frametime.py has the timing table)."""
import sys, os, json, time, re
import sys as _ws_sys, os as _ws_os; _ws_sys.path.insert(0, _ws_os.path.join(_ws_os.path.dirname(_ws_os.path.abspath(__file__)), '../test-songs')); from alsong import alsong  # task WS-F: the test songs
from playwright.sync_api import sync_playwright
F = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
OUT = sys.argv[2] if len(sys.argv) > 2 else '.'
os.makedirs(OUT, exist_ok=True)
SRC = open(F, encoding='utf-8').read()
ARGS = ["--autoplay-policy=no-user-gesture-required", "--enable-gpu-rasterization", "--ignore-gpu-blocklist", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"]
FAIL = []; N = [0]
def ok(c, m, d=''):
    N[0] += 1; print(('ok   ' if c else 'FAIL ') + m + (('   ' + str(d)[:300]) if d != '' else ''), flush=True)
    if not c: FAIL.append(m)
INIT = "if(!localStorage.getItem('audiolab-ui'))localStorage.setItem('audiolab-ui',JSON.stringify({splash:false,lat3:1}))"
OLDUI = "localStorage.setItem('audiolab-ui',JSON.stringify({splash:false,lat3:1,blur:30,glPlay:false,glBack:false,refr:0,trans:50,edge:60}))"
BF = r"""()=>{let n=0,ex=[],all=0;for(const e of document.querySelectorAll('*')){all++;for(const ps of[null,'::before','::after']){const c=getComputedStyle(e,ps),v=c.backdropFilter||c.webkitBackdropFilter;if(v&&v!=='none'){n++;if(ex.length<6)ex.push((e.id||e.className||e.tagName)+(ps||''))}}}return{n,ex,all}}"""

def boot(p, init=INIT, w=1600, h=1000, dsf=1):
    b = p.chromium.launch(args=ARGS)
    ctx = b.new_context(viewport={'width': w, 'height': h}, device_scale_factor=dsf); pg = ctx.new_page(); logs = []
    def con(m):
        if (m.type == 'error' and 'fetching the script' not in m.text) or (m.type == 'warning' and 'nominal range' not in m.text and 'GPU stall due to ReadPixels' not in m.text and 'willReadFrequently' not in m.text): logs.append(m.type + ': ' + m.text[:200])
    pg.on('console', con); pg.on('pageerror', lambda e: logs.append('pageerror: ' + str(e)[:300]))
    pg.route('https://app.test/**', alsong(lambda r: r.fulfill(status=200, content_type='text/html', body=SRC) if r.request.url.endswith('.html') else r.fulfill(status=404, body='')))
    pg.add_init_script("if(!sessionStorage.getItem('gs3i')){sessionStorage.setItem('gs3i','1');" + init + "}")
    pg.goto('https://app.test/index.html'); pg.wait_for_function("()=>window.AudioLab&&window.AudioLab.version", timeout=120000); pg.wait_for_timeout(4000)
    pg.evaluate("()=>{for(const i of['splash','liteNote']){const s=document.getElementById(i);if(s)s.remove()}}")
    R = lambda c: pg.evaluate("c=>AudioLab.run(c)", c)
    R("openDemoFractals()"); pg.wait_for_timeout(6000); pg.evaluate("()=>{const s=document.getElementById('liteNote');if(s)s.remove()}")
    R("pmSetOn(false)"); pg.wait_for_timeout(1200)
    return b, pg, logs, R

def swaps(b, pg, ms):
    b.start_tracing(page=pg, categories=['viz', 'gpu']); t = time.time(); pg.wait_for_timeout(ms); buf = b.stop_tracing(); wall = time.time() - t
    ev = json.loads(buf)['traceEvents']
    return round(sum(1 for e in ev if e.get('name') in ('SkiaOutputSurfaceImplOnGpu::SwapBuffers', 'SoftwareRenderer::SwapBuffers') and e.get('ph') == 'X') / wall, 1)

with sync_playwright() as p:
    b, pg, logs, R = boot(p)
    v = R("VERSION")
    ok(tuple(map(int, v.split('.'))) >= (0, 228), 'version 0.228 or later', v)
    # ---- 1. the old lens code is gone ----
    s = json.loads(R("JSON.stringify({rfx:typeof RFX,b:typeof rfBuild,m:typeof rfMap,st:typeof rfStyle,att:typeof rfAttach,attSrc:String(rfAttach).length,ab:typeof abDraw,abl:typeof ABL,pic:typeof fxBlurPic,gpv:typeof GPVV,svg:!!document.querySelector('svg filter[id^=rf]'),arrBlur:!!document.getElementById('arrBlur')})"))
    ok(s['rfx'] == 'undefined' and s['b'] == s['m'] == s['st'] == 'undefined', 'rfBuild, rfMap, rfStyle and the lens table RFX are gone', s)
    ok(s['att'] == 'function' and s['attSrc'] < 30, 'rfAttach is only an empty call left for older code', s['attSrc'])
    ok(s['ab'] == 'undefined' and s['abl'] == 'undefined' and s['pic'] == 'undefined' and not s['arrBlur'], 'the blurred picture (#arrBlur, abDraw, fxBlurPic) is gone', s)
    ok(not s['svg'] and s['gpv'] == 'undefined', 'no SVG lens filter in the page, the Glass preview code is gone', s)
    ok("mk('feImage'" not in SRC and 'function rfMap(' not in SRC and 'function gpvGet' not in SRC, 'no feImage map, no rfMap, no preview code in the file')
    decl = re.findall(r'(?:-webkit-)?backdrop-filter\s*:[^;}"\'`]*', SRC)
    ok(len(decl) == 2 and all('none' in d for d in decl), 'the only backdrop-filter declarations left are the guard rule that sets it to none', decl)
    r = pg.evaluate(BF)
    ok(r['n'] == 0, 'no element or pseudo element has a backdrop-filter (Full effects)', r)
    s = json.loads(R("JSON.stringify({on:GLE.on,lv:GLE.lv,cv:!!document.getElementById('glassCv'),back:(()=>{const c=document.getElementById('arrBack');return c?[c.width,c.height]:null})()})"))
    ok(s['on'] and s['lv'] == 'glass' and s['cv'] and s['back'] == [2, 2], 'the glass engine draws the docked panels as before; #arrBack is the empty 2 x 2 click layer', s)
    R("openMixer()"); pg.wait_for_timeout(1500)
    s = json.loads(R("JSON.stringify({act:GLF.act,L:GLF.L.filter(Boolean).length,up:GLF.L.filter(Boolean).map(L=>L.g.stats.uploads)})"))
    ok(s['act'] and s['L'] >= 1, 'the mixer gets its glass from a floating engine layer as before', s)
    r = pg.evaluate(BF); ok(r['n'] == 0, 'no backdrop-filter with the mixer open', r)
    R("document.getElementById('mixWin').hidden=true"); pg.wait_for_timeout(500)

    # ---- 2. Settings: the dead settings are gone, the rest is there ----
    R("openSettings('glass')"); pg.wait_for_timeout(1500)
    s = json.loads(R("JSON.stringify({cards:[...document.querySelectorAll('#setBody section[data-page=glass] .gcard b')].map(e=>e.textContent),prev:!!document.querySelector('#setBody .gprev,#gpv,#gpVid'),blur:!!document.getElementById('setBlur'),refr:!!document.getElementById('setRefr'),glPlay:!!document.getElementById('glPlay'),glBack:!!document.getElementById('glBack'),txt:document.querySelector('#setBody section[data-page=glass]').innerText})"))
    ok(s['cards'] == ['Transparency', 'Edge light'], 'Glass and light: the Transparency and Edge light cards only (Blur and Refraction changed nothing any more)', s['cards'])
    ok(not s['prev'] and not s['blur'] and not s['refr'] and not s['glPlay'] and not s['glBack'], 'no Glass preview (it imitated the old levels), no Blur or Refraction slider, no old blur switches', s)
    pg.screenshot(path=os.path.join(OUT, 'gs3_settings_glass.png'))
    R("openSettings('perf')"); pg.wait_for_timeout(1500)
    s = json.loads(R("JSON.stringify({rows:[...document.querySelectorAll('#setBody section[data-page=perf] .pmr')].map(r=>r.dataset.pr),heads:[...document.querySelectorAll('#setBody section[data-page=perf] .pmh')].map(e=>e.textContent),hud:!!document.getElementById('fpsHudChk'),tip:(document.getElementById('fpsHudRow')||{}).title||'',caps:PMD,txt:document.querySelector('#setBody section[data-page=perf]').innerText})"))
    ok(not any(k in s['rows'] for k in ('refr', 'blur', 'glPlay', 'glBack')), 'Performance: the rows that changed nothing (Refraction, Blur, Softer blur while playing, Half-size picture) are gone', s['rows'])
    ok(all(k in s['rows'] for k in ('edge', 'anim', 'ncOn', 'slpOn', 'gl_lv', 'gl_lens', 'gl_blur')), 'Performance: glass level, lens, frosting, edge light, animations, note cache, sleeping tracks are there', s['rows'])
    ok('Other effects' in s['heads'] and not any('Windows, sheets and menus: other' in h for h in s['heads']), 'the heading of the remaining effects says "Other effects"', s['heads'])
    ok(not any('blur from a ready-made picture' in c or 'live blur' in c for c in s['caps']), 'the texts of the Light mode stops no longer describe the old blur', s['caps'])
    ok(s['hud'] and len(s['tip']) > 40, 'Performance: the "Frame-rate read-out on screen" switch is there, with a tooltip', s['tip'][:80])
    ok('—' not in s['txt'] and '—' not in s['tip'], 'no em dash in the Performance tab')
    pg.screenshot(path=os.path.join(OUT, 'gs3_settings_perf.png'))

    # ---- 3. the read-out ----
    R("document.getElementById('fpsHudChk').click()"); pg.wait_for_timeout(1500)
    s = json.loads(R("JSON.stringify({ui:UI.fpsHud,saved:JSON.parse(localStorage.getItem('audiolab-ui')||'{}').fpsHud,el:(()=>{const e=document.getElementById('fpsHud');if(!e)return null;const r=e.getBoundingClientRect(),c=getComputedStyle(e);return{t:e.innerText,x:r.right,y:r.bottom,w:r.width,pe:c.pointerEvents,pos:c.position,z:+c.zIndex}})(),iw:innerWidth,ih:innerHeight})"))
    e = s['el'] or {}
    ok(s['ui'] is True and e, 'switching it on shows the read-out and saves the choice', [s['ui'], s['saved']])
    ok(re.search(r'\d+ fps', e.get('t', '')) and re.search(r'slowest [\d.]+ ms', e.get('t', '')), 'it shows the frames per second and the slowest frame of the last 5 seconds', e.get('t'))
    ok(e.get('pos') == 'fixed' and e.get('pe') == 'none' and 0 < e.get('x', 0) <= s['iw'] and 0 < e.get('y', 0) <= s['ih'] and e.get('z', 0) > 9000, 'it sits in the bottom right corner on top of everything and never takes a click', e)
    R("closeSet()"); pg.wait_for_timeout(300)
    R("{const t0=performance.now();let n=0;window.__fh=[];const f=()=>{__fh.push(document.getElementById('fpsHud').innerText);if(performance.now()-t0<2600)setTimeout(f,500)};f()}"); pg.wait_for_timeout(3000)
    fh = R("__fh"); ok(len(set(fh)) >= 2, 'it is updated while the app runs (about twice a second)', fh[:4])
    w = R("fhudWorst(performance.now(),5000)"); ok(w > 0, 'the slowest frame is taken from the last 5 seconds', w)
    pg.screenshot(path=os.path.join(OUT, 'gs3_readout.png'))
    R("fhudSet(false)"); pg.wait_for_timeout(300)
    ok(not R("!!document.getElementById('fpsHud')") and R("UI.fpsHud") is False, 'switching it off removes it')

    # ---- 4. drawing the same picture again: the master meter, the Settings logo, the capture dot ----
    R("window.__mt=0;{const g=document.getElementById('mtr').getContext('2d'),o=g.fillRect;g.fillRect=function(){__mt++;return o.apply(this,arguments)}}")
    pg.wait_for_timeout(2500); n_idle = R("__mt")
    ok(n_idle == 0, 'the master meter draws nothing while nothing plays (it drew 120 times a second)', n_idle)
    R("UI.follow=false;pos=128;start()"); pg.wait_for_timeout(1500); R("__mt=0;window.__lv=[];window.__lvi=setInterval(()=>__lv.push(Math.round(MT2.l)),100)"); pg.wait_for_timeout(2000); n_play = R("__mt"); lv = R("clearInterval(__lvi);__lv"); R("stop()")
    moving = len(set(lv)) > 2 and R("document.getElementById('mtr').clientWidth>2")   # in some layouts the top bar has no room for it (then it is not drawn at all)
    ok((n_play > 50) if moving else True, 'it still moves while the song plays, where it is shown (%d drawings in 2 s; levels seen: %s; width %s)' % (n_play, sorted(set(lv))[:6], R("document.getElementById('mtr').clientWidth")), n_play)
    R("window.__pa=0;{const o=paintAtom;paintAtom=function(c){if(c&&c.id==='navAtomC')__pa++;return o.apply(this,arguments)}}")
    R("openSettings('general')"); pg.wait_for_timeout(1000); R("__pa=0;window.__ab2=typeof AB2!=='undefined'?AB2.n.atom:0;window.__fr=FRN"); t0 = time.time(); pg.wait_for_timeout(3000); dt = time.time() - t0; pa = R("__pa+(typeof AB2!=='undefined'?AB2.n.atom-__ab2:0)") / dt; fr = R("FRN-__fr") / dt   # from v0.229 (task AB2) the card draws the fine atom itself, at most 30 a second
    ok(0 < pa <= 62 and (fr < 70 or pa < fr * .9), 'the logo in Settings still moves, at most 60 pictures a second (%.1f a second at %.1f frames a second here)' % (pa, fr), pa)
    R("closeSet()"); pg.wait_for_timeout(500)
    s = json.loads(R("JSON.stringify({ls:!!document.querySelector('#bCap.ls'),an:document.getAnimations().filter(a=>a.playState==='running').map(a=>[a.animationName,Object.keys((a.effect.getKeyframes()[0])||{}).filter(k=>!/offset|easing|composite/.test(k))])})"))
    ok(not any('opacity' in k for _, k in s['an']), 'no animation of opacity runs while the app is idle (the compositor would put the window together again on every screen frame)', s['an'])
    ok(any(n == 'cpl2' for n, _ in s['an']) if s['ls'] else True, 'the capture button still pulses while it listens (colour in 12 steps)', s)
    R("MAP.busy=0;mapAnalyze=function(){};mapSchedule=function(){}"); pg.wait_for_timeout(1500)
    fr = swaps(b, pg, 3000)
    ok(fr <= 42, 'idle: the compositor puts together about the logo\'s 30 frames a second, not every screen frame (%.1f a second here at 60 Hz; v0.227: about 47)' % fr, fr)

    # ---- 5. the kept layout answers give the same places as asking the page ----
    s = json.loads(R("(()=>{dirty=true;drawArr(false);const ab=hdrin.querySelector('.addrow button'),ar=ab&&ab.closest('.addrow');const direct=ab&&ar?ar.offsetTop+ab.offsetTop+ab.offsetHeight/2:TOTH+34;return JSON.stringify({kept:ascAddY(),direct,h:ascHcH(document.getElementById('hdrcol'),0),hd:document.getElementById('hdrcol').clientHeight})})()"))
    ok(abs(s['kept'] - s['direct']) < 0.01 and s['h'] == s['hd'], 'the kept "add track" place and header height are the ones the page gives', s)
    n0 = R("ASC.gen"); R("changed(false)"); ok(R("ASC.gen") == n0 + 1, 'an edit asks the page again (the count of edits goes up)')
    R("UI.th0=V.th;V.th=V.th+20;dirty=true"); pg.wait_for_timeout(600)
    s = json.loads(R("(()=>{const ab=hdrin.querySelector('.addrow button'),ar=ab&&ab.closest('.addrow');return JSON.stringify({kept:ascAddY(),direct:ab&&ar?ar.offsetTop+ab.offsetTop+ab.offsetHeight/2:TOTH+34})})()"))
    ok(abs(s['kept'] - s['direct']) < 0.01, 'after a new track height the place is asked again and still right', s)
    R("V.th=UI.th0;dirty=true"); pg.wait_for_timeout(400)

    # ---- 6. screenshots: Glass and Light levels (dark theme) ----
    R("gleSet('lv','glass')"); pg.wait_for_timeout(1200); pg.screenshot(path=os.path.join(OUT, 'gs3_glass.png'))
    R("openMixer()"); pg.wait_for_timeout(1200); pg.screenshot(path=os.path.join(OUT, 'gs3_glass_mixer.png'))
    R("gleSet('lv','light')"); pg.wait_for_timeout(1200); ok(R("GLE.lv") == 'light', 'level Light still works'); pg.screenshot(path=os.path.join(OUT, 'gs3_light_mixer.png'))
    R("document.getElementById('mixWin').hidden=true;gleSet('lv','glass')"); pg.wait_for_timeout(600)
    errs = list(logs); ok(not errs, 'no console errors', errs[:5]); b.close()

    # ---- 7. old stored settings of the removed controls ----
    b, pg, logs, R = boot(p, init=OLDUI)
    s = json.loads(R("JSON.stringify({ui:['blur','glPlay','glBack'].filter(k=>k in UI),saved:Object.keys(JSON.parse(localStorage.getItem('audiolab-ui')||'{}')).filter(k=>['blur','glPlay','glBack'].includes(k)),on:GLE.on,trans:UI.trans,edge:UI.edge})"))
    ok(not s['ui'] and not s['saved'] and s['on'] and s['trans'] == 50 and s['edge'] == 60, 'old stored Blur, "Lighter glass while playing" and "Efficient glass" choices are dropped once; Transparency and Edge light kept', s)
    R("UI.follow=false;pos=128;start()"); pg.wait_for_timeout(1500); R("stop()")
    ok(not logs, 'no console errors with the old stored settings', logs[:5]); b.close()

    # ---- 8. the user's window size (2194 x 1139 at 1.75x) with the read-out on ----
    b, pg, logs, R = boot(p, w=2194, h=1139, dsf=1.75)
    R("window.__mt=0;{const g=document.getElementById('mtr').getContext('2d'),o=g.fillRect;g.fillRect=function(){__mt++;return o.apply(this,arguments)}}")
    pg.wait_for_timeout(2000); n_idle = R("__mt"); R("UI.follow=false;pos=128;start()"); pg.wait_for_timeout(1500); R("__mt=0"); pg.wait_for_timeout(2000); n_play = R("__mt"); R("stop()")
    ok(R("document.getElementById('mtr').clientWidth") > 2 and n_idle == 0 and n_play > 50, "at the user's size the master meter is shown: nothing drawn while idle, drawn while playing (%d in 2 s)" % n_play, [n_idle, n_play])
    R("fhudSet(true);openSettings('perf')"); pg.wait_for_timeout(2500)
    pg.screenshot(path=os.path.join(OUT, 'gs3_user_size_perf.png'))
    ok(not logs, 'no console errors at the user\'s size', logs[:5]); R("fhudSet(false)"); b.close()

print('\n%d checks, %d failed' % (N[0], len(FAIL)))
for f in FAIL: print('FAILED:', f)
sys.exit(1 if FAIL else 0)
