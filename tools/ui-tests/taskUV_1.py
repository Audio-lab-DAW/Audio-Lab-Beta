#!/usr/bin/env python3
"""Task UV-1 (lane O, view engine): S9 direct trackpad and S13 zoom without page layout (and E19 calmer Follow page turns).

The real app at the user's size (2194 x 1139 CSS px at 1.75x), Fractals open, glass engine on (SwiftShader), as frametime.py.
Checks:
  S9   a pinch is applied in the frame it arrives in (V changes inside the event, by the same factor as before: Speed kept);
       a notched mouse wheel is still eased, now with tau 15 ms: 90 % reached after about 35 ms at 240 Hz (was about 92 ms);
       with reduced motion a notched wheel is applied at once; a two-finger scroll is applied at once as before;
       the end position of every zoom (pinch in and out, Speed 50 % and 200 %, Zoom around the playhead, Invert, Ableton zoom style,
       track height with Option, clip width with Shift, sideways) is the one the old eased path (tau 40) reaches, to 1e-9
       (V.y, rounded to a whole pixel at rest, within that pixel);
       "Trackpad pinch zooms" off still ignores a pinch; the piano roll and the overview take a pinch at once.
  S13  while a pinch goes on the header keeps its layout (--th not written, no size class change), every row is moved by a transform
       to where the arrangement draws its track (within 0.6 px) and is clipped to its new height; style and layout per pinch frame
       are measured against the same pinch with the hold switched off; 90 ms after the last step the header is laid out once:
       --th is the new height, no transforms are left, each row's top is its track's top.
  E19  Follow "Page" turns at 90 % of the view and moves it by 80 % (the last fifth of the old page stays in view); no turn while a
       pointer edit is held, the turn comes when it is let go.
  At rest the arrangement canvas and the header column are pixel for pixel what a fresh drawing gives (all clip pictures and the
  headers drawn again), in the dark look and in Light; no timer or eased step is left running; no console errors.
  python3 tools/ui-tests/taskUV_1.py [repo dir] [out dir]
"""
import sys, os, json, time, hashlib
from playwright.sync_api import sync_playwright
ROOT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else '.')
OUT = sys.argv[2] if len(sys.argv) > 2 else '.'; os.makedirs(OUT, exist_ok=True)
SRC = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()
ARGS = ["--autoplay-policy=no-user-gesture-required", "--enable-gpu-rasterization", "--ignore-gpu-blocklist", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"]
INIT = "if(!localStorage.getItem('audiolab-ui'))localStorage.setItem('audiolab-ui',JSON.stringify({splash:false,lat3:1}))"
N = [0, 0]; FAIL = []
def ck(name, ok, info=''):
    N[0] += 1
    if ok: N[1] += 1; print('  ok  ', name, info if info != '' else '')
    else: FAIL.append(name); print('  FAIL', name, info)

# in-page helpers: a wheel event on an element at a point (fraction of its box), synchronous; the view as a plain object
HELP = r"""
window.__uv={wheel(el,o){const r=el.getBoundingClientRect();const e=new WheelEvent('wheel',Object.assign({clientX:r.left+r.width*(o.fx??.55),clientY:r.top+r.height*(o.fy??.45),bubbles:true,cancelable:true},o));el.dispatchEvent(e)},
 v(){return{x:V.x,ppb:V.ppb,th:V.th,y:V.y}},
 set(s){Object.assign(V,s);clampV();dirty=true},
 drain(){let t=performance.now();for(let k=0;k<4000&&SZ.size;k++){t+=1000/240;szStep(t)}SZraf=0;SZt=0;uvRest(true);clampV()}};0
"""

def main():
    with sync_playwright() as p:
        b = p.chromium.launch(args=ARGS)
        ctx = b.new_context(viewport={'width': 2194, 'height': 1139}, device_scale_factor=1.75); pg = ctx.new_page(); errs = []
        pg.on('console', lambda m: errs.append(m.text[:200]) if m.type == 'error' and 'fetching the script' not in m.text else None)
        pg.on('pageerror', lambda e: errs.append('pageerror: ' + str(e)[:300]))
        pg.route('https://app.test/**', lambda r: r.fulfill(status=200, content_type='text/html', body=SRC) if r.request.url.endswith('.html') else r.fulfill(status=404, body=''))
        pg.add_init_script(INIT); pg.set_default_timeout(300000)
        pg.goto('https://app.test/index.html'); pg.wait_for_function("()=>window.AudioLab&&window.AudioLab.version", timeout=120000); pg.wait_for_timeout(4000)
        pg.evaluate("()=>{for(const i of['splash','liteNote']){const s=document.getElementById(i);if(s)s.remove()}}")
        R = lambda c: pg.evaluate("c=>AudioLab.run(c)", c)
        R("openDemoFractals()"); pg.wait_for_timeout(7000); pg.evaluate("()=>{const s=document.getElementById('liteNote');if(s)s.remove()}")
        R("pmSetOn(false);UI.follow=false;stop();0"); pg.wait_for_timeout(800)
        R(HELP)
        print('version', R("VERSION"), 'tracks', R("S.tracks.length"))
        J = lambda c: json.loads(R("JSON.stringify(" + c + ")"))
        HOME = {'x': 40, 'ppb': 24, 'th': 64, 'y': 0}
        def home(): R("__uv.set(%s);__uv.drain();0" % json.dumps(HOME)); pg.wait_for_timeout(250)

        # ---------- S9: same frame
        home(); v0 = J("__uv.v()")
        v1 = J("(()=>{__uv.wheel(arr,{deltaY:-6,ctrlKey:true});return __uv.v()})()")
        ck('a pinch changes the view inside its own event (no easing step)', abs(v1['ppb'] / v0['ppb'] - 2.718281828 ** (6 * .0085)) < 1e-9, '%.6f' % (v1['ppb'] / v0['ppb']))
        ck('the pinch zooms time and track height together (AudioLab zoom style)', abs(v1['th'] / v0['th'] - v1['ppb'] / v0['ppb']) < 1e-9)
        ck('nothing is left to ease after a pinch', R("SZ.size") == 0)
        R("__uv.drain();0")
        home(); v0 = J("__uv.v()")
        EASE = """(tau)=>{const _t=UV.tau;UV.tau=tau;ZSK.c=true;const p0=V.ppb;__uv.wheel(arr,{deltaY:120,ctrlKey:true});ZSK.c=false;const same=V.ppb===p0;let t=1000,n=0;SZt=0;const tot=Math.log(Math.exp(-60*.0085));
          let t90=null;for(;n<400&&SZ.size;n++){szStep(t);if(t90==null&&Math.log(V.ppb/p0)<=.9*tot+1e-12)t90=t-1000+1000/240;t+=1000/240}SZraf=0;SZt=0;UV.tau=_t;return{same,t90,fin:Math.log(V.ppb/p0)/tot}}"""
        r40 = pg.evaluate("(f)=>AudioLab.run('('+f+')(40)')", EASE); R("__uv.drain();0"); home()
        r = pg.evaluate("(f)=>AudioLab.run('('+f+')(UV.tau)')", EASE)
        ck('a notched mouse wheel with Ctrl is still eased (nothing moves inside the event)', r['same'])
        ck('the eased wheel reaches 90 % at 240 Hz in well under half the time of tau 40', r['t90'] is not None and r['t90'] <= .45 * r40['t90'], '%.1f ms (tau 40: %.1f ms)' % (r['t90'] or -1, r40['t90']))
        ck('the eased wheel ends exactly where it was going', abs(r['fin'] - 1) < 1e-9, r['fin'])
        R("__uv.drain();0")
        home(); v0 = J("__uv.v()")
        v1 = J("(()=>{__uv.wheel(arr,{deltaX:12,deltaY:0});return __uv.v()})()")
        ck('a two-finger scroll is applied at once, 1:1 (as before)', abs((v1['x'] - v0['x']) * v0['ppb'] - 12) < 1e-9)
        pg.emulate_media(reduced_motion='reduce')
        home(); v0 = J("__uv.v()")
        v1 = J("(()=>{ZSK.c=true;__uv.wheel(arr,{deltaY:120,ctrlKey:true});ZSK.c=false;return __uv.v()})()")
        ck('with reduced motion a notched wheel is applied at once', abs(v1['ppb'] / v0['ppb'] - 2.718281828459045 ** (-.51)) < 1e-9, '%.6f' % (v1['ppb'] / v0['ppb']))
        pg.emulate_media(reduced_motion='no-preference'); R("__uv.drain();0")

        # ---------- S9: same end positions as the old eased path (tau 40, every input eased)
        CASES = [
            ('pinch in and out at the pointer', "{}", [('arr', {'deltaY': -6, 'ctrlKey': True})] * 5 + [('arr', {'deltaY': 4, 'ctrlKey': True, 'fx': .3, 'fy': .7})] * 3),
            ('pinch with Speed 50 %', "{speed:50}", [('arr', {'deltaY': -8, 'ctrlKey': True})] * 4),
            ('pinch with Speed 200 %', "{speed:200}", [('arr', {'deltaY': 5, 'ctrlKey': True, 'fx': .8})] * 4),
            ('pinch around the playhead', "{anchor:'play'}", [('arr', {'deltaY': -7, 'ctrlKey': True, 'fx': .9})] * 4),
            ('pinch over the map', "{}", [('map', {'deltaY': -5, 'ctrlKey': True})] * 3),
            ('Option + trackpad: track height', "{}", [('arr', {'deltaY': 9, 'altKey': True})] * 4),
            ('Shift + trackpad: clip width', "{}", [('arr', {'deltaY': -9, 'shiftKey': True})] * 4),
            ('Ctrl+Shift + trackpad: sideways', "{}", [('arr', {'deltaY': 14, 'ctrlKey': True, 'shiftKey': True, 'real': 1})] * 4),
            ('Invert on, Ctrl + trackpad', "{inv:true}", [('arr', {'deltaY': -6, 'ctrlKey': True, 'real': 1})] * 4),
            ('Ableton zoom style, pinch', "{}", [('arr', {'deltaY': -6, 'ctrlKey': True})] * 4),
        ]
        for name, zs, evs in CASES:
            abl = 'Ableton' in name
            res = {}
            for mode in ('old', 'new'):
                R("UI.zs=Object.assign({},ZSD,%s);ZSC=null;UI.mapZoom=%s;pos=60;0" % (zs, "'ableton'" if abl else "UI.mapZoom==='ableton'?'':UI.mapZoom"))
                home()
                js = []
                for el, o in evs:
                    o = dict(o); real = o.pop('real', 0)
                    if mode == 'old': real = 1 if o.get('ctrlKey') else real   # the old path eased everything; a held Ctrl is the eased twin of a pinch
                    js.append("ZSK.c=%s;__uv.wheel(%s,%s);ZSK.c=false;%s" % ('true' if real else 'false', el, json.dumps(o), "__uv.drain();" if mode == 'old' else ''))
                pre = "const _e=uvEase,_t=UV.tau;uvEase=()=>true;UV.tau=40;" if mode == 'old' else ""
                post = "uvEase=_e;UV.tau=_t;" if mode == 'old' else ""
                res[mode] = J("(()=>{" + pre + "".join(js) + "__uv.drain();" + post + "return __uv.v()})()")
            o, n = res['old'], res['new']
            ok = all(abs(o[k] - n[k]) <= 1e-9 * max(1, abs(o[k])) for k in ('x', 'ppb', 'th')) and abs(o['y'] - n['y']) <= 1
            moved = any(abs(n[k] - HOME[k]) > 1e-6 for k in ('x', 'ppb', 'th'))
            ck('same end position as the old eased zoom: ' + name, ok and moved, json.dumps({k: [round(o[k], 6), round(n[k], 6)] for k in o}))
        R("UI.zs=Object.assign({},ZSD);ZSC=null;UI.mapZoom='';0")
        home(); v0 = J("__uv.v()")
        R("zsSet({pinch:false});__uv.wheel(arr,{deltaY:-6,ctrlKey:true});0"); v1 = J("__uv.v()")
        ck('"Trackpad pinch zooms" off: a pinch does nothing', v1 == v0)
        R("zsSet({pinch:true});delete UI.zs;ZSC=null;0")

        # ---------- piano roll and overview
        R("{const t=S.tracks.find(t=>t.kind==='inst'&&t.clips.some(c=>c.notes&&c.notes.length));openPR(t,t.clips.find(c=>c.notes&&c.notes.length))};0"); pg.wait_for_timeout(1200)
        r = J("(()=>{const p0=PR.ppb;__uv.wheel(prc,{deltaY:-6,ctrlKey:true});return{r:PR.ppb/p0,sz:SZ.size}})()")
        ck('the piano roll takes a pinch at once', abs(r['r'] - 2.718281828459045 ** (6 * .0085)) < 1e-6 and r['sz'] == 0, r)
        R("closePR();__uv.drain();0"); pg.wait_for_timeout(400)

        # ---------- S13: the header during a pinch
        home()
        th0 = R("hdrin.style.getPropertyValue('--th')"); cls0 = R("hdrin.className")
        cdp = ctx.new_cdp_session(pg); cdp.send('Performance.enable')
        def metr(): return {x['name']: x['value'] for x in cdp.send('Performance.getMetrics')['metrics']}
        PIN = """(a)=>new Promise(res=>{const n=a[0];let k=0;const f=()=>{AudioLab.run("__uv.wheel(arr,{deltaY:"+(k<n/2?-3:2)+",ctrlKey:true,fx:.5,fy:.35});0");k++;if(k<n)requestAnimationFrame(f);else res(a[1]?AudioLab.run(a[1]):1)};requestAnimationFrame(f)})"""
        CAP = """(()=>{drawArr(false);const hs=[...hdrin.querySelectorAll('.hdr')],rt=hdrin.getBoundingClientRect(),z=ZOOM;let err=0,n=0,tr=0,cp=0;
          hs.forEach(h=>{const i=S.tracks.findIndex(t=>t.id===h.dataset.id);if(i<0||HIDT.has(S.tracks[i]))return;const y=(h.getBoundingClientRect().top-rt.top)/z;err=Math.max(err,Math.abs(y-TRY[i]));n++;if(h.style.transform)tr++;if(h.style.clipPath)cp++});
          return{hold:UV.hold,th:hdrin.style.getPropertyValue('--th'),cls:hdrin.className,vth:V.th,err,n,tr,cp,uvz:hdrin.classList.contains('uvz')}})()"""
        m0 = metr(); st = pg.evaluate(PIN, [30, CAP]); m1 = metr()
        lay_new = (m1['LayoutDuration'] - m0['LayoutDuration'] + m1['RecalcStyleDuration'] - m0['RecalcStyleDuration']) * 1000 / 30
        ck('during a pinch the header keeps its layout (--th and size classes not written)', st['hold'] and st['th'] == th0 and st['cls'].replace(' uvz', '') == cls0.replace(' uvz', ''), (th0, st['th'], round(st['vth'], 2)))
        ck('every row is moved by a transform to its track (within 0.6 px)', st['tr'] > 5 and st['err'] < .6, 'rows %d, worst %.3f px' % (st['n'], st['err']))
        ck('rows are clipped to their new height while the tracks are lower than before, and are their own layers', st['uvz'] and (st['cp'] > 0) == (st['vth'] < float(th0[:-2]) - .01))
        t0 = time.time(); pg.wait_for_function("()=>AudioLab.run('!UV.hold&&!dirty')", timeout=10000); rest_ms = (time.time() - t0) * 1000; pg.wait_for_timeout(100)
        st = J("""(()=>{const hs=[...hdrin.querySelectorAll('.hdr')],rt=hdrin.getBoundingClientRect();let err=0,tr=0;hs.forEach(h=>{const i=S.tracks.findIndex(t=>t.id===h.dataset.id);if(i<0||HIDT.has(S.tracks[i]))return;err=Math.max(err,Math.abs((h.getBoundingClientRect().top-rt.top)/ZOOM-TRY[i]));if(h.style.transform||h.style.clipPath)tr++});
          return{hold:UV.hold,th:hdrin.style.getPropertyValue('--th'),vth:V.th,err,tr,tm:UV.tm,sz:SZ.size,uvz:hdrin.classList.contains('uvz')}})()""")
        ck('90 ms after the last step the header is laid out once: --th is the new height, no transforms left', not st['hold'] and st['th'] == str(st['vth']) + 'px' and st['tr'] == 0 and not st['uvz'], (st['th'], st['vth']))
        ck('each row sits at its track again (layout)', st['err'] < .6, '%.3f px' % st['err'])
        ck('nothing left running at rest (no timer, no eased step)', st['tm'] == 0 and st['sz'] == 0, 'let go %.0f ms after the test read the last frame' % rest_ms)
        # the same pinch with the hold switched off (the old header path), for style + layout per frame
        home(); R("window.__uvh=uvHold;uvHold=()=>{};0")
        m0 = metr(); pg.evaluate(PIN, [30, None]); m1 = metr(); R("uvHold=window.__uvh;0"); pg.wait_for_timeout(300)
        lay_old = (m1['LayoutDuration'] - m0['LayoutDuration'] + m1['RecalcStyleDuration'] - m0['RecalcStyleDuration']) * 1000 / 30
        ck('style and layout per pinch frame: well under half of the header laid out every frame', lay_new < .5 * lay_old, 'held %.2f ms against %.2f ms' % (lay_new, lay_old))

        # ---------- E19 calmer Follow page turns (Follow "Page")
        home(); R("UI.follow=true;UI.followMode='page';0")
        x0, vis = J("[V.x,arrW/V.ppb]")
        R("pos=V.x+arrW/V.ppb*.86;start();0")
        try:
            pg.wait_for_function("()=>AudioLab.run('V.x!==%r')" % x0, timeout=15000); x1 = J("V.x")
        except Exception: x1 = x0
        R("stop();0")
        ck('Follow Page turns at 90 % and keeps the last fifth of the old page in view (moves 80 % of the view)', abs((x1 - x0) / vis - .8) < 1e-6, '%.4f of the view' % ((x1 - x0) / vis))
        home(); R("UI.follow=true;UI.followMode='page';0"); x0 = J("V.x")
        R("ad={k:'pan'};pos=V.x+arrW/V.ppb*.93;start();0"); pg.wait_for_timeout(1500); xe = J("V.x")
        R("ad=null;0")
        try:
            pg.wait_for_function("()=>AudioLab.run('V.x!==%r')" % x0, timeout=8000); xa = J("V.x")
        except Exception: xa = x0
        R("stop();UI.followMode='center';UI.follow=false;0")
        ck('no page turn while a pointer edit is held; the turn comes when it is let go', xe == x0 and xa != x0, (x0, xe, xa))
        R("__uv.drain();0")

        # ---------- pixels at rest: after a pinch against a fresh drawing (every clip picture and header drawn again)
        HASH = "(()=>{const g=arr.getContext('2d'),d=g.getImageData(0,0,arr.width,arr.height).data;let h=2166136261>>>0;const u=new Uint32Array(d.buffer);for(let i=0;i<u.length;i++){h^=u[i];h=Math.imul(h,16777619)>>>0}return h+':'+arr.width+'x'+arr.height})()"
        def stable():
            """waveform pictures for a new zoom are finished in the background (about 2 s here): wait until two reads 700 ms apart agree"""
            h = R(HASH)
            for _ in range(20):
                pg.wait_for_timeout(700); h2 = R(HASH)
                if h2 == h: return h
                h = h2
            return h
        def hdrshot(fn):
            bx = pg.evaluate("()=>{const r=document.getElementById('hdrcol').getBoundingClientRect(),db=document.getElementById('dockB'),bt=db&&db.offsetHeight?db.getBoundingClientRect().top:innerHeight;return{x:r.left,y:r.top,width:r.width,height:Math.min(r.height,bt-r.top)-2}}")
            pg.screenshot(path=fn, clip=bx, animations='disabled'); return hashlib.sha256(open(fn, 'rb').read()).hexdigest()[:16]
        for look in ('dark', 'light'):
            if look == 'light': R("UI.lite=true;UI.liteMan=true;applyLite();dirty=true;0"); pg.wait_for_timeout(800)
            home(); pg.evaluate(PIN, [24, None]); pg.wait_for_timeout(500); stable()
            a = R(HASH); ha = hdrshot(os.path.join(OUT, 'uv1_hdr_%s_after.png' % look)); pg.screenshot(path=os.path.join(OUT, 'uv1_%s_after.png' % look))
            R("CLC.clear();renderHeaders();dirty=true;0"); pg.wait_for_timeout(600); stable()
            b_ = R(HASH); hb = hdrshot(os.path.join(OUT, 'uv1_hdr_%s_fresh.png' % look))
            ck('at rest (%s) the arrangement is pixel for pixel a fresh drawing' % look, a == b_, (a, b_))
            ck('at rest (%s) the track headers are pixel for pixel freshly laid out ones' % look, ha == hb, (ha, hb))
        R("UI.lite=false;UI.liteMan=false;applyLite();dirty=true;0"); pg.wait_for_timeout(300)
        ck('no console errors', not errs, errs[:5])
        b.close()
    print('%d/%d checks passed' % (N[1], N[0]))
    if FAIL: print('FAILED:', FAIL); sys.exit(1)
main()
