#!/usr/bin/env python3
"""AudioLab glass benchmark: relative frame cost of each backdrop-filter surface.

  python3 bench.py [--dsf 1|2] [--reps 3] [--win 4] [--scen a,b,c,d,e] [--out results.json] [--quick] [--sw]

Renderer:
  default  : GPU compositing through SkiaRenderer on SwiftShader (needs the container's wrapper opt-outs, set below)
  --sw     : the container's default (software compositor, viz::SoftwareRenderer)
  real GPU : ALAB_HEADED=1 ALAB_ARGS="" python3 bench.py     (plain headed Chromium, vsync on: read 'fps' and p95, the median just sits on the refresh interval;
             add ALAB_ARGS="--disable-frame-rate-limit --disable-gpu-vsync" to uncap and compare medians as here)
  ALAB_INDEX=/path/index.html picks another build. Nothing in the app folder is written; variants are a <style id=__kb> or the app's own switches.

Metrics per window: rAF interval (median, p95, max) and, from a CDP trace, frames really presented (SwapBuffers count, interval median and p95)
and GPU-thread time per presented frame (SkiaOutputSurfaceImplOnGpu::FinishPaintCurrentFrame) or SoftwareRenderer DrawFrame time.
"""
import os, sys, json, time, argparse, statistics
ap = argparse.ArgumentParser()
ap.add_argument('--dsf', type=float, default=1); ap.add_argument('--reps', type=int, default=3); ap.add_argument('--win', type=float, default=4.0)
ap.add_argument('--scen', default='a,b,e,c,d'); ap.add_argument('--out', default=None); ap.add_argument('--quick', action='store_true'); ap.add_argument('--sw', action='store_true')
ap.add_argument('--vars', default=None); ap.add_argument('--capped', action='store_true', help='keep the 60 Hz frame limit (use for idle: read CPU per second, not intervals)')
A = ap.parse_args()
if A.quick: A.reps, A.win = 1, 1.5
if not A.sw and os.environ.get('ALAB_ARGS') is None:
    os.environ['CHROMIUM_WEBGL_RENDERER'] = 'none'; os.environ['CHROMIUM_KEEP_GL_SWITCHES'] = '1'   # documented opt-outs of this container's Chromium wrapper
if A.capped: os.environ['ALAB_CAPPED'] = '1'
from common import *
import glob, re
OUT = A.out or ('results_dsf%g%s%s.json' % (A.dsf, '_sw' if A.sw else '', '_capped' if A.capped else ''))

NONE = '{backdrop-filter:none!important;-webkit-backdrop-filter:none!important}'
# name -> (css injected, app-state code)     app state: 'full' | 'norefr' | 'light' | 'zero'
VARIANTS = {
 'full':        ('', 'full'),
 'no_backdrop': ('*' + NONE, 'full'),
 'refr_off':    ('', 'norefr'),          # app switch: refraction off, live blur kept
 'app_light':   ('', 'light'),           # app preset: no refraction, blur from a ready-made picture
 'app_zero':    ('', 'zero'),            # app "Light mode": no blur, no refraction, solid panels
 'ko_hglass':   ('#hglass' + NONE, 'full'),
 'ko_tr':       ('#tr' + NONE, 'full'),
 'ko_arrBlur':  ('#arrBlur{display:none!important}', 'full'),   # the blurred-picture canvas behind the device panel (not a backdrop-filter)
 'ko_anim':     ('#bLogo,#bLogo *,.cpd{animation:none!important}', 'full'),  # the CSS animations that run inside the transport glass
 'ko_mixwin':   ('#mixWin,#mixWin .fwh' + NONE, 'full'),
 'ko_ck':       ('#mixWin .ck' + NONE, 'full'),
 'ko_mix_all':  ('#mixWin,#mixWin *' + NONE, 'full'),
}
SCEN_VARS = {
 'a': ['full', 'no_backdrop', 'refr_off', 'app_light', 'app_zero', 'ko_hglass', 'ko_tr', 'ko_arrBlur', 'ko_anim'],
 'b': ['full', 'no_backdrop', 'refr_off', 'app_light', 'app_zero', 'ko_hglass', 'ko_tr', 'ko_arrBlur'],
 'e': ['full', 'no_backdrop', 'refr_off', 'app_light', 'ko_hglass', 'ko_tr'],
 'c': ['full', 'no_backdrop', 'refr_off', 'app_light', 'ko_hglass', 'ko_tr', 'ko_mixwin', 'ko_ck', 'ko_mix_all'],
 'd': ['full', 'no_backdrop', 'refr_off', 'ko_hglass', 'ko_tr', 'ko_mixwin', 'ko_ck', 'ko_mix_all'],
}
SCEN_NAME = {'a': 'idle, stopped', 'b': 'playing', 'c': 'playing + mixer open', 'd': 'dragging the mixer window (stopped)', 'e': 'scroll + zoom arrangement (stopped)'}
STATE = {'full': "pmSetOn(false)", 'norefr': "pmSetOn(false);pmToggle({refr:false})", 'light': "UI.fxOpt=null;pmSetStop(2)", 'zero': "pmSetStop(1)"}

RAF_START = """(ms)=>{window.__raf=new Promise(res=>{const iv=[];let last=performance.now(),t0=last;const f=()=>{const n=performance.now();iv.push(n-last);last=n;if(n-t0<ms)requestAnimationFrame(f);else res(iv)};requestAnimationFrame(f)})}"""

def cpu():
    """CPU seconds used so far by each kind of Chromium process (all threads), from /proc."""
    o = {}; hz = os.sysconf('SC_CLK_TCK')
    for d in glob.glob('/proc/[0-9]*'):
        try:
            cl = open(d + '/cmdline', 'rb').read().decode('utf8', 'ignore').replace('\0', ' ')
            if not re.search(r'chrom|headless', cl.split(' ')[0], re.I): continue
            m = re.search(r'--type=([\w-]+)', cl); k = m.group(1) if m else 'browser'
            f = open(d + '/stat').read().rsplit(')', 1)[1].split()
            o[k] = o.get(k, 0) + (int(f[11]) + int(f[12])) / hz
        except Exception: pass
    return o

def q(v, p):
    v = sorted(v); return v[min(len(v) - 1, int(len(v) * p))] if v else None

def parse_trace(buf):
    ev = json.loads(buf)['traceEvents']
    swaps, paint, draw, quads = [], 0, 0, 0
    for e in ev:
        n = e.get('name')
        if n in ('SkiaOutputSurfaceImplOnGpu::SwapBuffers', 'SoftwareRenderer::SwapBuffers') and e.get('ph') == 'X': swaps.append(e['ts'] / 1000)
        elif n == 'SkiaOutputSurfaceImplOnGpu::FinishPaintCurrentFrame': paint += e.get('dur', 0)
        elif n == 'DirectRenderer::DrawFrame' and e.get('ph') == 'X': draw += e.get('dur', 0)
    swaps.sort(); iv = [b - a for a, b in zip(swaps, swaps[1:])]
    span = (swaps[-1] - swaps[0]) / 1000 if len(swaps) > 1 else 0
    return {'frames': len(swaps), 'fps': round(len(iv) / span, 1) if span else 0, 'sw_med': q(iv, .5), 'sw_p95': q(iv, .95), 'sw_max': max(iv) if iv else None,
            'gpu_ms_per_frame': round(paint / 1000 / max(1, len(swaps)), 2), 'viz_draw_ms_per_frame': round(draw / 1000 / max(1, len(swaps)), 2)}

def main():
    res = {'meta': {}, 'rows': []}
    with sync_playwright() as p:
        b, pg = launch(p, dsf=A.dsf)
        errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:300]))
        R = lambda c: run(pg, c)
        try:
            info = b.new_browser_cdp_session().send('SystemInfo.getInfo')['gpu']
            aux = info.get('auxAttributes', {})
            res['meta']['gpu'] = {'renderer': aux.get('glRenderer'), 'display': aux.get('displayType'), 'skia': aux.get('skiaBackendType'),
                                  'gpu_compositing': info['featureStatus'].get('gpu_compositing'), 'rasterization': info['featureStatus'].get('rasterization'), 'canvas2d': info['featureStatus'].get('2d_canvas')}
        except Exception as e: res['meta']['gpu'] = str(e)[:200]
        res['meta'].update(version=pg.evaluate("()=>AudioLab.version"), chromium=b.version, dsf=A.dsf, win=A.win, reps=A.reps, cores=pg.evaluate("()=>navigator.hardwareConcurrency"))
        print(json.dumps(res['meta']), flush=True)
        R("(()=>{openDemoFractals()})()"); pg.wait_for_timeout(6000)
        pg.evaluate("()=>{for(const i of['splash','liteNote']){const s=document.getElementById(i);if(s)s.remove()}}")
        R("(()=>{pmSetOn(false)})()"); pg.wait_for_timeout(1500)
        chk = R("JSON.stringify({fx:UI.fx,lite:UI.lite,cls:document.body.className,hg:getComputedStyle(document.getElementById('hglass')).backdropFilter,tr:getComputedStyle(document.getElementById('tr')).backdropFilter})")
        print('full effects:', chk, flush=True); res['meta']['full_check'] = json.loads(chk)
        if 'url(' not in json.loads(chk)['hg']: print('!! refraction is NOT active, aborting'); sys.exit(2)

        cur = {'state': 'full'}
        def apply(vn):
            css, st = VARIANTS[vn]
            if st != cur['state']: R("(()=>{%s})()" % STATE[st]); cur['state'] = st; pg.wait_for_timeout(1800)
            pg.evaluate("c=>{let s=document.getElementById('__kb');if(!s){s=document.createElement('style');s.id='__kb';document.head.appendChild(s)}s.textContent=c}", css)
            pg.wait_for_timeout(350)

        def window(scen, action=None):
            if scen in 'bc': R("(()=>{if(play.on)stop();pos=128;start()})()"); pg.wait_for_timeout(900)
            glass = pg.evaluate(LIST_GLASS)
            b.start_tracing(page=pg, categories=['viz', 'gpu'])
            pg.evaluate(RAF_START, A.win * 1000)
            t0 = time.time(); c0 = cpu()
            if action: action(t0)
            iv = pg.evaluate("()=>window.__raf")
            c1 = cpu(); wall = time.time() - t0
            tr = parse_trace(b.stop_tracing())
            if scen in 'bc': R("(()=>{stop()})()")
            iv = iv[2:] or [0]
            o = {'raf_n': len(iv), 'raf_med': q(iv, .5), 'raf_p95': q(iv, .95), 'raf_max': max(iv), 'raf_mean': sum(iv) / len(iv), 'wall': wall}
            for k in set(c0) | set(c1): o['cpu_' + k] = round((c1.get(k, 0) - c0.get(k, 0)) / wall * 1000, 1)   # CPU ms per second of wall time
            o['cpu_all'] = round(sum(c1.values()) - sum(c0.values()), 3) / wall * 1000
            o.update(tr); o['glass_px'] = sum(g['area'] for g in glass); o['glass_n'] = len(glass); o['lens_n'] = sum(1 for g in glass if g['lens'])
            return o

        def drag(t0):
            box = pg.evaluate("()=>{const r=document.querySelector('#mixWin .fwt').getBoundingClientRect();return [r.left+r.width/2,r.top+r.height/2]}")
            x0, y0 = box; pg.mouse.move(x0, y0); pg.mouse.down()
            import math
            while True:
                t = time.time() - t0
                if t > A.win - .15: break
                ph = t / A.win * 2 * math.pi
                pg.mouse.move(x0 + 150 * math.sin(ph) , y0 + 160 * (1 - math.cos(ph))); time.sleep(PACE)
            pg.mouse.move(x0, y0); pg.mouse.up()

        VIEW = []
        def scroll(t0):
            pg.mouse.move(900, 300); half = A.win / 2; i = 0; VIEW.clear(); VIEW.append(R('JSON.stringify(V)'))
            while time.time() - t0 < half - .05:               # sideways scroll, there and back
                t = (time.time() - t0) / half; pg.mouse.wheel(60 if t < .5 else -60, 0); i += 1 if t < .5 else -1; time.sleep(PACE)
                if t >= .5 and len(VIEW) < 2: VIEW.append(R('JSON.stringify(V)'))
            while i != 0: pg.mouse.wheel(-60 if i > 0 else 60, 0); i += -1 if i > 0 else 1
            pg.keyboard.down('Control'); j = 0
            while time.time() - t0 < A.win - .1:                # zoom in and out again
                t = (time.time() - t0 - half) / half; pg.mouse.wheel(0, -40 if t < .5 else 40); j += 1 if t < .5 else -1; time.sleep(PACE)
                if t >= .5 and len(VIEW) < 3: VIEW.append(R('JSON.stringify(V)'))
            while j != 0: pg.mouse.wheel(0, 40 if j > 0 else -40); j += -1 if j > 0 else 1
            pg.keyboard.up('Control')

        PACE = 0.012   # seconds between scripted input events (about 80 per second), so input never floods the page
        ACT = {'d': drag, 'e': scroll}
        for scen in A.scen.split(','):
            if scen in 'cd': R("(()=>{openMixer()})()"); pg.wait_for_timeout(1200)
            vs = [v for v in SCEN_VARS[scen] if not A.vars or v in A.vars.split(',')]
            for rep in range(-1, A.reps):                        # rep -1 is a warm-up (shader compiles, first layouts) and is not recorded
                for vn in (vs if rep % 2 == 0 else vs[::-1]):     # alternate the order so drift does not favour one variant
                    apply(vn)
                    o = window(scen, ACT.get(scen)); o.update(scen=scen, variant=vn, rep=rep)
                    if scen == 'e': o['view'] = VIEW[:]
                    if rep < 0: continue
                    res['rows'].append(o)
                    print('%s %-12s r%d raf med %.1f p95 %.1f | swaps %d fps %.1f med %.1f p95 %.1f | gpu %.2f viz %.2f ms/f | cpu/s gpu %.0f rend %.0f all %.0f | glass %d px (%d, %d lens)' % (scen, vn, rep, o['raf_med'], o['raf_p95'], o['frames'], o['fps'], o['sw_med'] or 0, o['sw_p95'] or 0, o['gpu_ms_per_frame'], o['viz_draw_ms_per_frame'], o.get('cpu_gpu-process', 0), o.get('cpu_renderer', 0), o['cpu_all'], o['glass_px'], o['glass_n'], o['lens_n']), flush=True)
                    json.dump(res, open(OUT, 'w'))
            apply('full')
            if scen == 'c' or scen == 'd':
                res['meta']['glass_' + scen] = pg.evaluate(LIST_GLASS)
            else: res['meta'].setdefault('glass_main', pg.evaluate(LIST_GLASS))
        res['meta']['errors'] = errs
        json.dump(res, open(OUT, 'w')); print('errors', errs); b.close()
main()
