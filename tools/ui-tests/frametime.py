#!/usr/bin/env python3
"""Frame-time harness (task GS3): where the app's own drawing spends its time.

  python3 tools/ui-tests/frametime.py [index.html] [--out results.json] [--win 4] [--scen idle,scroll,scrollset,play,playmix]
                                      [--parts all,arr,meters,wave,set,glass,timers,mixer] [--profile] [--reps 1]

The real app at the user's size (2194 x 1139 CSS px at 1.75x, 3840 x 1993 device px), Fractals song open, "Full effects",
glass engine at Glass (SwiftShader WebGL2, so the engine is on as on the Mac).

Scenes
  idle       nothing moves, nothing plays
  scroll     the arrangement is scrolled sideways on every frame (what a trackpad does, through the same V.x / dirty path)
  edit       edit while scrolled (task UV-2): the view in the middle of the song, a clip in view moved by a beat and back on every frame
  pinch      a trackpad pinch over the arrangement: one ctrlKey wheel event per frame (deltaY 4, in for 60 frames, then out), through the
             app's own wheel listener (task UV-1)
  scrollset  the same with Settings open over it (Performance page)
  play       playing from beat 128, Follow off
  playmix    playing with the mixer open

Parts (one switched off at a time, as the engine test page does; 'all' = nothing switched off)
  arr     the 2D arrangement canvas (drawArr, drawMap)
  meters  level meters (meters, trackMeters, miniMeter)
  wave    clip waveforms and notes inside clips (drawClipC)
  set     the Settings window's own drawing (its logo loop) and the sheet itself
  glass   the glass engine canvases (docked engine and floating layers)
  timers  the repeating timers that only update the screen (the ones the background freeze stops at level 1)
  mixer   the mixer's own drawing (drawMixer)

Numbers per row (one window of --win seconds)
  fps        screen frames delivered per second (rAF; this machine has no graphics card and no vsync limit here, so the
             absolute number is set by the software renderer and means little for the Mac)
  main ms/f  main-thread time per frame (script + style + layout + paint recording + tasks, from Chromium's own counters):
             this is what has to fit in 4.17 ms at 240 Hz on the Mac, and what a fix lowers
  js ms/f    script time per frame;  style+layout ms/f
  app ms/f   the app's own frame callback (frame0), measured inside the page
  kept %     frames that came within 1.5x the median frame interval of this window
  worst ms   longest frame interval
  presented  frames the compositor really put together and showed, per second (from a trace): a frame in which nothing on screen changed is not
             put together at all, so an idle app should show close to the logo's 30 here, not the screen rate
The CPU profile (--profile) is taken of the slowest scene and printed as the top functions by self time.
"""
import sys, os, json, time, argparse
import sys as _ws_sys, os as _ws_os; _ws_sys.path.insert(0, _ws_os.path.join(_ws_os.path.dirname(_ws_os.path.abspath(__file__)), '../test-songs')); from alsong import alsong  # task WS-F: the test songs
from playwright.sync_api import sync_playwright
ap = argparse.ArgumentParser()
ap.add_argument('index', nargs='?', default='index.html'); ap.add_argument('--out', default=None); ap.add_argument('--win', type=float, default=4.0)
ap.add_argument('--scen', default='idle,scroll,scrollset,play,playmix'); ap.add_argument('--parts', default='all')
ap.add_argument('--profile', action='store_true'); ap.add_argument('--reps', type=int, default=1)
ap.add_argument('--w', type=int, default=2194); ap.add_argument('--h', type=int, default=1139); ap.add_argument('--dsf', type=float, default=1.75)
ap.add_argument('--pre', default='', help='script run in the app after Fractals is open (e.g. "UVT.on=true" to force the tiles of task UV-2 on)')
ap.add_argument('--capped', action='store_true', help='keep the 60 Hz frame limit')
ap.add_argument('--drawbench', action='store_true', help='also time single arrangement drawings (full; and shifted: the tiles of task UV-2, or the experimental GS3 build, each finished by a 1-pixel read-back so the raster work is included')
A = ap.parse_args()
SRC = open(A.index, encoding='utf-8').read()
ARGS = ["--autoplay-policy=no-user-gesture-required", "--enable-gpu-rasterization", "--ignore-gpu-blocklist", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"]
if not A.capped: ARGS += ["--disable-frame-rate-limit", "--disable-gpu-vsync"]
INIT = "if(!localStorage.getItem('audiolab-ui'))localStorage.setItem('audiolab-ui',JSON.stringify({splash:false,lat3:1}))"

# switch one part off / on again (inside the app's scope; the original is kept in window.__FT)
PART = {
 'arr':    ("__FT.drawArr=drawArr;__FT.drawMap=drawMap;drawArr=function(){};drawMap=function(){}", "drawArr=__FT.drawArr;drawMap=__FT.drawMap;dirty=true"),
 'meters': ("__FT.m=[meters,trackMeters,miniMeter];meters=trackMeters=miniMeter=function(){}", "[meters,trackMeters,miniMeter]=__FT.m"),
 'wave':   ("__FT.dc=drawClipC;drawClipC=function(){};dirty=true", "drawClipC=__FT.dc;dirty=true"),
 'set':    ("__FT.sl=setLoop;setLoop=function(){};{const s=document.getElementById('set');__FT.sv=s.style.visibility;s.style.visibility='hidden'}", "setLoop=__FT.sl;document.getElementById('set').style.visibility=__FT.sv||'';if(!document.getElementById('set').hidden)requestAnimationFrame(setLoop)"),
 'glass':  ("__FT.gr=[];for(const g of[GLE.g,...(GLF.L||[]).map(L=>L&&L.g)].filter(Boolean)){__FT.gr.push([g,g.render]);g.render=function(){}}", "for(const[g,r]of __FT.gr)g.render=r"),
 'timers': ("AO.ivOff(aoVisIv)", "AO.ivOn(aoVisIv)"),
 'mixer':  ("__FT.dm=drawMixer;drawMixer=function(){}", "drawMixer=__FT.dm"),
}
# in-page recorder: rAF intervals, and the app's own frame time (frame0 wrapped once)
REC = r"""(ms)=>{window.__ftres=new Promise(res=>{const iv=[];let last=performance.now(),t0=last;const s0=(window.__ftapp||{t:0,n:0});const a0=s0.t,n0=s0.n;
  const f=()=>{const n=performance.now();iv.push(n-last);last=n;if(n-t0<ms)requestAnimationFrame(f);else{const s=window.__ftapp||{t:0,n:0};res({iv,app:(s.t-a0)/Math.max(1,s.n-n0),appn:s.n-n0})}};requestAnimationFrame(f)})}"""
WRAP = "if(!window.__ftapp){window.__ftapp={t:0,n:0};const o=frame0;frame0=function(now){const t=performance.now();try{return o(now)}finally{__ftapp.t+=performance.now()-t;__ftapp.n++}}}"
# scroll driver: sideways, a few px a frame, back and forth, through the same path the wheel uses (V.x, clampV, dirty)
SCROLL_ON = "window.__ftsc={on:true,k:0};(function f(){if(!__ftsc.on)return;__ftsc.k++;const d=(Math.floor(__ftsc.k/90)%2?-1:1)*6;V.x+=d/V.ppb;clampV();dirty=true;requestAnimationFrame(f)})()"
SCROLL_OFF = "if(window.__ftsc)__ftsc.on=false"
# pinch driver (task UV-1): a trackpad pinch over the middle of the arrangement, one wheel event with ctrlKey (no Control key down) per frame, in and out
PINCH_ON = "window.__ftpi={on:true,k:0};(function f(){if(!__ftpi.on)return;__ftpi.k++;const r=arr.getBoundingClientRect(),d=(Math.floor(__ftpi.k/60)%2?1:-1)*4;arr.dispatchEvent(new WheelEvent('wheel',{deltaY:d,ctrlKey:true,clientX:r.left+r.width*.55,clientY:r.top+r.height*.45,bubbles:true,cancelable:true}));requestAnimationFrame(f)})()"
PINCH_OFF = "if(window.__ftpi)__ftpi.on=false"
# edit while scrolled (task UV-2): the view in the middle of the song, one clip in view moved by a beat and back on every frame (what a nudge or a
# piano roll edit does to the arrangement: the clip changes, the view does not), through the same dirty path
EDIT_ON = "window.__fted={on:true,k:0};V.x=160;clampV();{let c=null;S.tracks.forEach((t,i)=>{for(const q of t.clips){const G=clipGeom(i,q);if(!c&&G.x>X0+40&&G.x+G.w<arr.width/((window.devicePixelRatio||1)*ZOOM)-40&&G.y>AY+10)c=q}});__fted.c=c}(function f(){if(!__fted.on)return;__fted.k++;if(__fted.c){__fted.c.start+=(__fted.k%2?1:-1);dirty=true}requestAnimationFrame(f)})()"
EDIT_OFF = "if(window.__fted){__fted.on=false;if(__fted.c&&__fted.k%2)__fted.c.start-=1;dirty=true}"

def swaps(buf, wall):
    """frames the compositor really put on the screen per second (each one is the whole window put together again on the Mac)"""
    try: ev = json.loads(buf)['traceEvents']
    except Exception: return 0
    n = sum(1 for e in ev if e.get('name') in ('SkiaOutputSurfaceImplOnGpu::SwapBuffers', 'SoftwareRenderer::SwapBuffers') and e.get('ph') == 'X')
    return round(n / wall, 1)

def q(v, p):
    v = sorted(v); return v[min(len(v) - 1, int(len(v) * p))] if v else 0

def main():
    out = A.out or 'frametime.json'
    res = {'meta': {}, 'rows': [], 'profile': None}
    with sync_playwright() as p:
        b = p.chromium.launch(args=ARGS)
        ctx = b.new_context(viewport={'width': A.w, 'height': A.h}, device_scale_factor=A.dsf); pg = ctx.new_page(); errs = []
        pg.on('console', lambda m: errs.append(m.type + ': ' + m.text[:200]) if m.type == 'error' and 'fetching the script' not in m.text else None)
        pg.on('pageerror', lambda e: errs.append('pageerror: ' + str(e)[:300]))
        pg.route('https://app.test/**', alsong(lambda r: r.fulfill(status=200, content_type='text/html', body=SRC) if r.request.url.endswith('.html') else r.fulfill(status=404, body='')))
        pg.add_init_script(INIT)
        pg.goto('https://app.test/index.html'); pg.wait_for_function("()=>window.AudioLab&&window.AudioLab.version", timeout=120000); pg.wait_for_timeout(4000)
        pg.evaluate("()=>{for(const i of['splash','liteNote']){const s=document.getElementById(i);if(s)s.remove()}}")
        R = lambda c: pg.evaluate("c=>AudioLab.run(c)", c)
        R("openDemoFractals()"); pg.wait_for_timeout(7000); pg.evaluate("()=>{const s=document.getElementById('liteNote');if(s)s.remove()}")
        R("pmSetOn(false)"); pg.wait_for_timeout(1500)
        R("window.__FT={};" + WRAP)
        if A.pre: print('pre:', A.pre, '->', R(A.pre + ";'done'"), flush=True)
        cdp = ctx.new_cdp_session(pg); cdp.send('Performance.enable')
        meta = json.loads(R("JSON.stringify({v:VERSION,gle:typeof GLE==='object'?{on:GLE.on,lv:GLE.lv}:null,dpr:devicePixelRatio,iw:innerWidth,ih:innerHeight,arr:[arr.width,arr.height],tracks:S.tracks.length,clips:S.tracks.reduce((a,t)=>a+t.clips.length,0)})"))
        meta['cores'] = pg.evaluate("()=>navigator.hardwareConcurrency"); meta['chromium'] = b.version; meta['win'] = A.win
        res['meta'] = meta; print(json.dumps(meta), flush=True)

        def metrics():
            m = {x['name']: x['value'] for x in cdp.send('Performance.getMetrics')['metrics']}
            return m
        def scene_on(sc):
            if sc in ('scrollset',): R("openSettings('general')"); pg.wait_for_timeout(1200)
            if sc == 'playmix': R("openMixer()"); pg.wait_for_timeout(1200)
            if sc in ('play', 'playmix'): R("UI.follow=false;if(play.on)stop();pos=128;start()"); pg.wait_for_timeout(1200)
            if sc in ('scroll', 'scrollset'): R(SCROLL_ON); pg.wait_for_timeout(400)
            if sc == 'pinch': R(PINCH_ON); pg.wait_for_timeout(400)
            if sc == 'edit': R(EDIT_ON); pg.wait_for_timeout(400)
        def scene_off(sc):
            if sc in ('scroll', 'scrollset'): R(SCROLL_OFF)
            if sc == 'pinch': R(PINCH_OFF); pg.wait_for_timeout(300)
            if sc == 'edit': R(EDIT_OFF); pg.wait_for_timeout(300)
            if sc in ('play', 'playmix'): R("stop()")
            if sc == 'scrollset': R("closeSet()")
            if sc == 'playmix': R("{const w=document.getElementById('mixWin');if(w)w.hidden=true}")
            pg.wait_for_timeout(800)
        def window_(label):
            b.start_tracing(page=pg, categories=['viz', 'gpu']); m0 = metrics(); t0 = time.time()
            pg.evaluate(REC, A.win * 1000); r = pg.evaluate("()=>window.__ftres"); wall = time.time() - t0
            m1 = metrics(); sw = swaps(b.stop_tracing(), wall)
            iv = r['iv'][2:] or [0]; n = len(iv); med = q(iv, .5)
            d = lambda k: (m1.get(k, 0) - m0.get(k, 0)) * 1000   # seconds -> ms
            o = {'frames': n, 'fps': round(n / (sum(iv) / 1000), 1) if sum(iv) else 0, 'med': round(med, 2), 'p95': round(q(iv, .95), 2), 'worst': round(max(iv), 1),
                 'kept': round(100 * sum(1 for x in iv if x <= 1.5 * med) / n, 1),
                 'main': round(d('TaskDuration') / n, 2), 'js': round(d('ScriptDuration') / n, 2), 'style_layout': round((d('RecalcStyleDuration') + d('LayoutDuration')) / n, 2),
                 'app': round(r['app'], 2), 'busy_pct': round(d('TaskDuration') / (wall * 1000) * 100, 1),
                 'layouts': round((m1.get('LayoutCount', 0) - m0.get('LayoutCount', 0)) / n, 2), 'styles': round((m1.get('RecalcStyleCount', 0) - m0.get('RecalcStyleCount', 0)) / n, 2)}
            o['presented'] = sw
            return o
        if A.drawbench:
            # one arrangement drawing at a time, scrolled 6 CSS px sideways before each; a 1 px read-back makes the browser finish drawing it, so raster work is counted too
            DB = r"""(on)=>{const res=[];const g=arr.getContext('2d');const has=typeof ASC==='object'&&'fc' in ASC,uvt=typeof UVT==='object';if(has){ASC.on=on;ASC.force=1}const uv0=uvt?UVT.on:0;if(uvt){UVT.on=on;UVT.force=1}dirty=false;drawArr(false);g.getImageData(0,0,1,1);
              for(let i=0;i<40;i++){V.x+=(i%20<10?6:-6)/V.ppb;clampV();if(has&&on&&ASC.fc>=40)ASC.fc=0;const t=performance.now();drawArr(false);g.getImageData(0,0,1,1);res.push(performance.now()-t)}
              if(has)ASC.on=true;if(uvt)UVT.on=uv0;res.sort((a,b)=>a-b);return{med:res[20],p90:res[36],min:res[0]}}"""
            R("UI.follow=false"); pg.wait_for_timeout(300)
            for rep in range(2):
                for on in ((False, True) if R("typeof ASC==='object'&&'fc' in ASC||typeof UVT==='object'") else (False,)):
                    r = pg.evaluate("(f)=>AudioLab.run('('+f+')('+%s+')')" % ('true' if on else 'false'), DB)
                    res.setdefault('drawbench', []).append(dict(r, shifted=on, rep=rep))
                    print('one drawing of the arrangement, %-8s median %.2f ms, 90%% %.2f ms, best %.2f ms' % ('shifted' if on else 'full', r['med'], r['p90'], r['min']), flush=True)
        prof_target = None
        for sc in A.scen.split(','):
            scene_on(sc)
            for part in A.parts.split(','):
                if part == 'mixer' and sc != 'playmix': continue
                if part == 'set' and sc != 'scrollset': continue
                if part != 'all': R(PART[part][0]); pg.wait_for_timeout(300)
                for rep in range(-1 if part == 'all' and A.reps > 0 else 0, A.reps):
                    o = window_(sc + '/' + part)
                    if rep < 0: continue
                    o.update(scen=sc, part=part, rep=rep); res['rows'].append(o)
                    print('%-9s %-7s fps %6.1f  presented %6.1f/s  main %6.2f ms/f  js %5.2f  sty+lay %5.2f  app %5.2f  kept %5.1f%%  worst %6.1f ms  busy %5.1f%%  layouts/f %.2f' % (
                        sc, part, o['fps'], o['presented'], o['main'], o['js'], o['style_layout'], o['app'], o['kept'], o['worst'], o['busy_pct'], o['layouts']), flush=True)
                if part != 'all': R(PART[part][1]); pg.wait_for_timeout(300)
            if A.profile and (prof_target is None or max((r['main'] for r in res['rows'] if r['scen'] == sc and r['part'] == 'all'), default=0) > prof_target[1]):
                prof_target = (sc, max((r['main'] for r in res['rows'] if r['scen'] == sc and r['part'] == 'all'), default=0))
            scene_off(sc)
        if A.profile and prof_target:
            sc = prof_target[0]; scene_on(sc)
            cdp.send('Profiler.enable'); cdp.send('Profiler.setSamplingInterval', {'interval': 200}); cdp.send('Profiler.start')
            pg.wait_for_timeout(int(A.win * 1000))
            prof = cdp.send('Profiler.stop')['profile']; scene_off(sc)
            nodes = {n['id']: n for n in prof['nodes']}; self_ = {}
            dt = prof.get('timeDeltas', []); smp = prof.get('samples', [])
            for sid, d in zip(smp, dt):
                cf = nodes[sid]['callFrame']; k = (cf['functionName'] or '(anon)') + ' :' + str(cf['lineNumber'] + 1)
                self_[k] = self_.get(k, 0) + d
            tot = sum(self_.values()) or 1
            top = sorted(self_.items(), key=lambda x: -x[1])[:30]
            res['profile'] = {'scene': sc, 'top': [[k, round(v / 1000, 1), round(100 * v / tot, 1)] for k, v in top]}
            print('CPU profile of the slowest scene:', sc)
            for k, ms, pc in res['profile']['top']: print('  %6.1f ms %5.1f%%  %s' % (ms, pc, k))
        res['errors'] = errs
        json.dump(res, open(out, 'w'), indent=1)
        print('errors:', errs[:10]); b.close()
main()
