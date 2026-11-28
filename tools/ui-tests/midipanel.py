"""MIDI panel rework (v0.191, task Q): the piano roll docked above the devices panel, devices hidden, MIDI alone, window mode small and large,
at four window sizes; checks that no control is clipped or covered, drags the divider, the top edge and a window corner, and measures frame time
with the glass band on and off.
    python3 tools/ui-tests/midipanel.py [index.html] [out dir] [sizes, e.g. 1280x720,1440x900]"""
import sys, os, json, time
import sys as _ws_sys, os as _ws_os; _ws_sys.path.insert(0, _ws_os.path.join(_ws_os.path.dirname(_ws_os.path.abspath(__file__)), '../test-songs')); from alsong import alsong  # task WS-F: the test songs
from playwright.sync_api import sync_playwright
F = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
OUT = sys.argv[2] if len(sys.argv) > 2 else '.'
SIZES = [tuple(map(int, s.split('x'))) for s in (sys.argv[3] if len(sys.argv) > 3 else '1280x720,1440x900,1920x1080,2560x1440').split(',')]
os.makedirs(OUT, exist_ok=True)
SRC = open(F, encoding='utf-8').read()

def boot(p, w, h, ui='{splash:false,lat3:1}'):
    b = p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required']); pg = b.new_page(viewport={'width': w, 'height': h}); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)[:400]))
    pg.route('https://app.test/**', alsong(lambda r: r.fulfill(status=200, content_type='text/html', body=SRC.encode()) if r.request.url.endswith('.html') else r.fulfill(status=404, body=b'')))
    pg.add_init_script("if(!localStorage.getItem('audiolab-ui'))localStorage.setItem('audiolab-ui',JSON.stringify(%s))" % ui)
    pg.goto('https://app.test/index.html'); pg.wait_for_timeout(8000)
    pg.evaluate("()=>{const c=document.getElementById('liteNote');if(c)c.remove()}")
    return b, pg, errs

def run(pg, c): return pg.evaluate("c=>window.AudioLab.run(c)", c)
OPEN = "(()=>{const t=S.tracks.find(t=>t.clips.some(c=>c.notes&&c.notes.length));const c=t.clips.find(c=>c.notes);openPR(t,c);return t.name})()"
# every control of the MIDI editor: visible, fully inside the panel (or its window head), not covered by anything else
CHECK = r"""(()=>{const pr=$('#pr'),P=pr.getBoundingClientRect(),hd=document.getElementById('prHead'),H=hd&&!hd.hidden&&pr.classList.contains('float')?hd.getBoundingClientRect():null,vw=innerWidth,vh=innerHeight;
 const sel='.prbar button,.prbar select,.prbar label.prsel,#prHead button,#pr .cv select';const bad=[];let n=0;
 for(const e of pr.querySelectorAll(sel)){if(e.closest('label.prsel')&&e.tagName==='SELECT'&&!e.offsetWidth)continue;const cs=getComputedStyle(e);
   if(e.id==='prDev'&&!pr.classList.contains('full'))continue;if(cs.display==='none'||e.closest('[hidden]'))continue;n++;
   const r=e.getBoundingClientRect(),nm=e.id||e.dataset.tool||e.dataset.fm||e.getAttribute('aria-label')||e.className;
   if(r.width<6||r.height<6){bad.push(nm+' tiny');continue}
   const inP=r.left>=P.left-.5&&r.right<=P.right+.5&&r.top>=P.top-.5&&r.bottom<=P.bottom+.5,inH=H&&r.left>=H.left-.5&&r.right<=H.right+.5&&r.top>=H.top-.5&&r.bottom<=H.bottom+.5;
   if(!inP&&!inH){bad.push(nm+' outside '+[r.left,r.top,r.right,r.bottom].map(Math.round));continue}
   if(r.left<0||r.top<0||r.right>vw+.5||r.bottom>vh+.5){bad.push(nm+' off screen');continue}
   for(const [fx,fy] of[[.5,.5],[.2,.5],[.8,.5]]){const x=r.left+r.width*fx,y=r.top+r.height*fy,t=document.elementFromPoint(x,y);if(!t||!(e===t||e.contains(t)||t.contains(e)&&t.tagName==='LABEL')){bad.push(nm+' covered by '+(t?(t.id||t.className||t.tagName):'nothing'));break}}
   if(!e.title&&!e.closest('[title]')&&!(e.tagName==='SELECT')&&!TIPS_HAS(e))bad.push(nm+' no tooltip')}
 return JSON.stringify({n,bad,pr:[P.left,P.top,P.width,P.height].map(Math.round),cls:pr.className})})()""".replace('TIPS_HAS(e)', "(typeof TIPS==='object'&&Object.keys(TIPS).some(k=>{try{return e.matches(k)}catch(x){return false}}))")
GEO = "JSON.stringify(['#pr','#fx','#fxband','#tr','#stage'].map(s=>{const e=document.querySelector(s);const r=e.getBoundingClientRect();return [s,Math.round(r.top),Math.round(r.bottom)]}))"

def shot(pg, name): pg.screenshot(path=os.path.join(OUT, name + '.png'))

def check(pg, tag, res):
    c = json.loads(run(pg, CHECK)); ok = not c['bad'] and c['n'] >= 20
    res.append((tag, ok, c['n'], c['bad'][:6], c['pr'])); print(('OK  ' if ok else 'BAD ') + tag, c['n'], 'controls', c['pr'], c['bad'][:6])

res = []
with sync_playwright() as p:
    for (w, h) in SIZES:
        b, pg, errs = boot(p, w, h)
        print('--', w, h, 'load errors:', errs)
        run(pg, OPEN); pg.wait_for_timeout(700)
        check(pg, f'{w}x{h} both open', res); shot(pg, f'{w}_a_both'); print('  ', run(pg, GEO))
        top0 = run(pg, "Math.round($('#pr').getBoundingClientRect().top)")
        run(pg, "devHide(true)"); pg.wait_for_timeout(500)
        check(pg, f'{w}x{h} devices hidden', res); shot(pg, f'{w}_b_devhidden')
        top1 = run(pg, "Math.round($('#pr').getBoundingClientRect().top)"); print('   top edge stays:', top0, top1, abs(top0 - top1) <= 3)
        res.append((f'{w}x{h} top edge stays', abs(top0 - top1) <= 3, top0, top1, ''))
        run(pg, "devHide(false)"); pg.wait_for_timeout(500)
        top2 = run(pg, "Math.round($('#pr').getBoundingClientRect().top)"); res.append((f'{w}x{h} back after devices shown', abs(top0 - top2) <= 1, top0, top2, ''))
        run(pg, "devPop(true)"); pg.wait_for_timeout(700)
        run(pg, "(()=>{const w=document.getElementById('devWin');if(w)w.style.display='none'})()")  # the devices window is wherever the user put it; out of the way here
        check(pg, f'{w}x{h} MIDI alone (devices in a window)', res); shot(pg, f'{w}_c_alone')
        run(pg, "(()=>{const w=document.getElementById('devWin');if(w)w.style.display=''})()"); run(pg, "devPop(false)"); pg.wait_for_timeout(600)
        # window mode small and large
        run(pg, "prMode('float')"); pg.wait_for_timeout(300)
        run(pg, "(()=>{const el=$('#pr');Object.assign(el.style,{left:'60px',top:'120px',width:'640px',height:'330px'});prAll()})()"); pg.wait_for_timeout(400)
        check(pg, f'{w}x{h} window small', res); shot(pg, f'{w}_d_win_small')
        cs = run(pg, "$('#pr').classList.contains('prcmp')"); res.append((f'{w}x{h} small window compact', cs, '', '', ''))
        W, Hh = min(1500, w - 120), min(760, h - 140)
        run(pg, "(()=>{const el=$('#pr');Object.assign(el.style,{left:'60px',top:'80px',width:'%dpx',height:'%dpx'});prAll()})()" % (W, Hh)); pg.wait_for_timeout(400)
        check(pg, f'{w}x{h} window large {W}x{Hh}', res); shot(pg, f'{w}_e_win_large')
        big = W >= 1000 and Hh >= 460; cl = run(pg, "$('#pr').classList.contains('prcmp')"); res.append((f'{w}x{h} large window buttons ({"normal" if big else "compact"})', cl == (not big), '', '', ''))
        run(pg, "prMode('dock')"); pg.wait_for_timeout(400)
        check(pg, f'{w}x{h} docked again', res)
        b.close()
        if errs: res.append((f'{w}x{h} page errors', False, errs, '', ''))

    # ---- drags (1440 x 900) ----
    b, pg, errs = boot(p, 1440, 900)
    run(pg, OPEN); pg.wait_for_timeout(700)
    def ctr(s): return pg.evaluate("s=>{const r=document.querySelector(s).getBoundingClientRect();return [r.left+r.width/2,r.top+r.height/2]}", s)
    g0 = json.loads(run(pg, GEO)); c = ctr('#prDiv')
    pg.mouse.move(c[0], c[1]); pg.mouse.down(); pg.mouse.move(c[0], c[1] + 40, steps=8); pg.mouse.up(); pg.wait_for_timeout(400)
    g1 = json.loads(run(pg, GEO)); print('divider drag 40 down:', g0, '->', g1, run(pg, "JSON.stringify([UI.prDH,UI.fxDH])"))
    ok = abs(g1[0][1] - g0[0][1]) <= 1 and abs((g1[0][2] - g0[0][2]) - 40) <= 2 and abs((g1[1][2] - g1[1][1]) - (g0[1][2] - g0[1][1] - 40)) <= 2
    res.append(('divider drag: piano roll +40, devices -40, top stays', ok, g0, g1, '')); shot(pg, 'f_divider')
    c = ctr('#prTopH'); pg.mouse.move(c[0], c[1] - 1); pg.mouse.down(); pg.mouse.move(c[0], c[1] - 81, steps=8); pg.mouse.up(); pg.wait_for_timeout(400)
    g2 = json.loads(run(pg, GEO)); ok = abs((g2[0][2] - g2[0][1]) - (g1[0][2] - g1[0][1] + 80)) <= 2 and abs(g2[1][1] - g1[1][1]) <= 1
    res.append(('top edge drag: piano roll +80, devices unchanged', ok, g1, g2, ''))
    run(pg, "devHide(true)"); pg.wait_for_timeout(400); g3 = json.loads(run(pg, GEO)); run(pg, "devHide(false)"); pg.wait_for_timeout(400)
    res.append(('after drags, devices hidden: top stays', abs(g3[0][1] - g2[0][1]) <= 3, g2[0], g3[0], ''))
    pg.wait_for_timeout(600); pg.reload(); pg.wait_for_timeout(8000); pg.evaluate("()=>{const c=document.getElementById('liteNote');if(c)c.remove()}")
    run(pg, OPEN); pg.wait_for_timeout(700); g4 = json.loads(run(pg, GEO))
    res.append(('sizes remembered after reload', abs(g4[0][1] - g2[0][1]) <= 2 and abs(g4[1][1] - g2[1][1]) <= 2, g2, g4, ''))
    # double-click the divider: same heights again
    c = ctr('#prDiv'); pg.mouse.dblclick(c[0], c[1]); pg.wait_for_timeout(400); g5 = json.loads(run(pg, GEO))
    res.append(('double-click divider: back to the devices height', abs((g5[0][2] - g5[0][1]) - (g5[1][2] - g5[1][1])) <= 2, g5, '', ''))
    # window: resize from the corner, across the compact threshold, position and size remembered
    run(pg, "prMode('float')"); pg.wait_for_timeout(300)
    run(pg, "(()=>{const el=$('#pr');Object.assign(el.style,{left:'100px',top:'120px',width:'700px',height:'380px'});prAll()})()"); pg.wait_for_timeout(1700)
    k0 = run(pg, "$('#pr').classList.contains('prcmp')"); c = ctr('#pr>.rz-se')
    pg.mouse.move(c[0], c[1]); pg.mouse.down(); pg.mouse.move(c[0] + 420, c[1] + 160, steps=10); pg.mouse.up(); pg.wait_for_timeout(500)
    sz = run(pg, "JSON.stringify([$('#pr').offsetWidth,$('#pr').offsetHeight,$('#pr').classList.contains('prcmp')])"); print('corner resize:', k0, sz)
    s = json.loads(sz); res.append(('window corner resize 700x380 -> bigger, compact -> normal buttons', k0 and not s[2] and s[0] >= 1100 and s[1] >= 530, k0, sz, ''))
    c = ctr('#prHead .prgrip'); pg.mouse.move(c[0], c[1]); pg.mouse.down(); pg.mouse.move(c[0] - 40, c[1] + 50, steps=6); pg.mouse.up(); pg.wait_for_timeout(500)
    pos = run(pg, "JSON.stringify([$('#pr').offsetLeft,$('#pr').offsetTop])"); print('head drag ->', pos)
    c = ctr('#prHead .prgrip'); pg.mouse.move(c[0], c[1]); pg.mouse.down(); pg.mouse.move(c[0], c[1] - 600, steps=6); pg.mouse.up(); pg.wait_for_timeout(300)
    hy = run(pg, "Math.round(document.getElementById('prHead').getBoundingClientRect().top)"); res.append(('head cannot leave the top of the screen', hy >= 0, hy, '', ''))
    pg.wait_for_timeout(600); w0 = run(pg, "JSON.stringify(UI.prW)"); pg.reload(); pg.wait_for_timeout(8000); pg.evaluate("()=>{const c=document.getElementById('liteNote');if(c)c.remove()}")
    run(pg, OPEN); pg.wait_for_timeout(700); w1 = run(pg, "JSON.stringify([$('#pr').offsetLeft,$('#pr').offsetTop,$('#pr').offsetWidth,$('#pr').offsetHeight,UI.prMode])")
    print('window remembered', w0, w1); res.append(('window position and size remembered', json.loads(w0)['w'] == json.loads(w1)[2] and json.loads(w1)[4] == 'float', w0, w1, ''))
    run(pg, "prMode('dock')"); pg.wait_for_timeout(300)
    if errs: res.append(('page errors in drag test', False, errs, '', ''))
    b.close()

    # ---- glass: every performance level, and frame time with the band on and off (playing, 1600 x 1000) ----
    b, pg, errs = boot(p, 1600, 1000)
    run(pg, OPEN); pg.wait_for_timeout(500); run(pg, "closePR()")
    for st, nm in [(3, 'full'), (2, 'optimised'), (1, 'lighter'), (0, 'lightest')]:
        run(pg, "pmSetStop(%d)" % st); pg.wait_for_timeout(900)
        info = run(pg, "(()=>{const b=document.getElementById('fxband'),cs=getComputedStyle(b);return JSON.stringify({cls:b.className,bf:cs.backdropFilter,bg:cs.backgroundColor,clip:arr.style.clipPath,abl:ABL.cv?ABL.cv.style.display+'|'+ABL.clip:'none'})})()")
        print('glass', nm, info); shot(pg, 'g_' + nm)
        j = json.loads(info)
        if nm in ('lighter', 'lightest'): res.append(('glass ' + nm + ': solid, no filter', 'bsolid' in j['cls'] and j['bf'] in ('none', ''), j, '', ''))
        else: res.append(('glass ' + nm + ': picture behind the band', 'bpic' in j['cls'] and 'blur' not in j['bf'], j, '', ''))
    run(pg, "pmSetStop(3)"); pg.wait_for_timeout(600); run(pg, "start()"); pg.wait_for_timeout(1500)
    FT = "new Promise(r=>{const t=[];let l=performance.now();const f=n=>{t.push(n-l);l=n;if(t.length<180)requestAnimationFrame(f);else{t.sort((a,b)=>a-b);r(JSON.stringify({mean:+(t.reduce((a,b)=>a+b,0)/t.length).toFixed(2),p90:+t[Math.floor(t.length*.9)].toFixed(2)}))}};requestAnimationFrame(f)})"
    out = {}
    for rep in range(2):
        for on in (True, False):
            run(pg, "(()=>{UI.fxBand=%s;const b=document.getElementById('fxband');b._k='';fxBandSync();GB.lt=0;gbCopy()})()" % ('true' if on else 'false')); pg.wait_for_timeout(800)
            out.setdefault(on, []).append(json.loads(pg.evaluate(FT)))
    print('frame time ms (Full effects, playing) band on:', out[True], 'band off:', out[False])
    run(pg, "stop();UI.fxBand=true;fxBandSync()")
    res.append(('frame time band on vs off (info)', True, out[True], out[False], ''))
    if errs: res.append(('page errors in glass test', False, errs, '', ''))
    b.close()

print('\n==== summary ====')
bad = 0
for r in res:
    print('OK ' if r[1] else 'BAD', r[0], '' if r[1] else r[2:])
    bad += not r[1]
print('failures:', bad)
