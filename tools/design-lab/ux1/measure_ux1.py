#!/usr/bin/env python3
"""Task UX1 (speed and feel research): input-to-paint latency and frame times of the real app at the user's size.

  python3 tools/design-lab/ux1/measure_ux1.py [index.html] [--out ux1.json] [--n 24] [--win 3]

Same set-up as tools/ui-tests/frametime.py: 2194 x 1139 CSS px at 1.75x (3840 x 1993 device px), Fractals open, glass engine on
(SwiftShader WebGL2). This machine has no graphics card, so absolute numbers are slower than the user's M4; the useful parts are
(a) what the app's own code adds on top of the browser (easing, waiting for a frame, handler time) and (b) the comparisons.

Inputs are real browser input (Chrome DevTools Protocol Input.dispatchMouseEvent / dispatchKeyEvent), so they travel the same path
as a trackpad, a mouse or a key on the Mac: browser process -> renderer -> the app's own listeners -> the next frame.

Latency (per input, --n samples each, spaced 250 ms apart so every one starts from rest):
  scroll   two-finger trackpad scroll sideways (one wheel event, deltaX 12 px, pixel mode)
  wheel    a notched mouse wheel with Shift (deltaY 100): the app eases it (smoothPan)
  pinch    a trackpad pinch (wheel with ctrlKey, no Control key down; deltaY -6): the app eases it (smoothZoom, tau 40 ms)
  drag     one pointer move of 12 px while a clip is held
  key      a key of the computer-keyboard piano (Z) -> noteOn on the selected instrument track
  For each: 'queue' = from the event's own time stamp to the app's first listener; 'drawn' = to the end of the first arrangement
  drawing that shows the change; for the eased inputs also 't50' and 't90' = until half and 90 % of the final change is drawn.
  Add one screen frame (4.2 ms at 240 Hz) for the compositor and the display.

Frame times (continuous input for --win seconds, real input events): scroll, pinch-zoom, clip drag; and idle / playing with the
mixer open, with the computer-keyboard key latency measured while playing (the 'latency when playing' the user names).
"""
import sys, json, time, argparse, statistics as stt
from playwright.sync_api import sync_playwright
ap = argparse.ArgumentParser()
ap.add_argument('index', nargs='?', default='index.html'); ap.add_argument('--out', default='ux1.json')
ap.add_argument('--n', type=int, default=24); ap.add_argument('--w', type=int, default=2194); ap.add_argument('--h', type=int, default=1139); ap.add_argument('--dsf', type=float, default=1.75); ap.add_argument('--win', type=float, default=3.0); ap.add_argument('--only', default='')
A = ap.parse_args()
SRC = open(A.index, encoding='utf-8').read()
ARGS = ["--autoplay-policy=no-user-gesture-required", "--enable-gpu-rasterization", "--ignore-gpu-blocklist", "--use-angle=swiftshader",
        "--enable-unsafe-swiftshader", "--disable-frame-rate-limit", "--disable-gpu-vsync"]
INIT = "if(!localStorage.getItem('audiolab-ui'))localStorage.setItem('audiolab-ui',JSON.stringify({splash:false,lat3:1}))"

# in-page probe: listeners first in line (capture on window, added before nothing else can stop them) and a wrapped drawArr
PROBE = r"""
window.__U={ev:[],dr:[],notes:[]};
for(const t of ['wheel','pointermove','keydown'])window.addEventListener(t,e=>{__U.ev.push({t,ts:e.timeStamp,at:performance.now()})},{capture:true,passive:true});
{const o=drawArr;drawArr=function(ph){const r=o.apply(this,arguments);if(!ph){const f=selC&&findClip(selC);__U.dr.push({at:performance.now(),x:V.x,y:V.y,ppb:V.ppb,cs:f?f.c.start:null})}return r}}
{const o=noteOn;noteOn=function(){__U.notes.push(performance.now());return o.apply(this,arguments)}}
"""
REC = r"""(ms)=>new Promise(res=>{const iv=[];let last=performance.now(),t0=last;const f=()=>{const n=performance.now();iv.push(n-last);last=n;if(n-t0<ms)requestAnimationFrame(f);else res(iv)};requestAnimationFrame(f)})"""

W = lambda k: not A.only or k in A.only.split(',')

def q(v, p):
    v = sorted(v); return v[min(len(v) - 1, int(len(v) * p))] if v else 0

def main():
    out = {'meta': {}, 'latency': {}, 'frames': {}}
    with sync_playwright() as p:
        b = p.chromium.launch(args=ARGS)
        ctx = b.new_context(viewport={'width': A.w, 'height': A.h}, device_scale_factor=A.dsf); pg = ctx.new_page(); errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)[:200]))
        pg.route('https://app.test/**', lambda r: r.fulfill(status=200, content_type='text/html', body=SRC) if r.request.url.endswith('.html') else r.fulfill(status=404, body=''))
        pg.add_init_script(INIT)
        pg.goto('https://app.test/index.html'); pg.wait_for_function("()=>window.AudioLab&&window.AudioLab.version", timeout=120000); pg.wait_for_timeout(4000)
        pg.evaluate("()=>{for(const i of['splash','liteNote']){const s=document.getElementById(i);if(s)s.remove()}}")
        R = lambda c: pg.evaluate("c=>AudioLab.run(c)", c)
        R("openDemoFractals()"); pg.wait_for_timeout(7000); pg.evaluate("()=>{const s=document.getElementById('liteNote');if(s)s.remove()}")
        R("pmSetOn(false)"); pg.wait_for_timeout(1000)
        R(PROBE)
        cdp = ctx.new_cdp_session(pg); cdp.send('Performance.enable')
        out['meta'] = json.loads(R("JSON.stringify({v:VERSION,tracks:S.tracks.length,clips:S.tracks.reduce((a,t)=>a+t.clips.length,0),dpr:devicePixelRatio,w:innerWidth,h:innerHeight,zs:ZS(),sr:ctx?ctx.sampleRate:0,base:ctx?ctx.baseLatency:null,hint:UI.hq?'balanced':'interactive'})"))
        out['meta']['chromium'] = b.version; print(json.dumps(out['meta']), flush=True)
        box = pg.evaluate("()=>{const r=arr.getBoundingClientRect();return{l:r.left,t:r.top,w:r.width,h:r.height}}")
        cx, cy = box['l'] + box['w'] * 0.55, box['t'] + box['h'] * 0.45

        def wheel(dx, dy, mods=0, x=cx, y=cy):
            cdp.send('Input.dispatchMouseEvent', {'type': 'mouseWheel', 'x': x, 'y': y, 'deltaX': dx, 'deltaY': dy, 'modifiers': mods})

        def reset():
            R("__U.ev.length=0;__U.dr.length=0;__U.notes.length=0")

        def sample(kind, fire, field):
            rows = []
            for i in range(A.n):
                pg.wait_for_timeout(250); reset(); s0 = json.loads(R("JSON.stringify({x:V.x,y:V.y,ppb:V.ppb,cs:(selC&&findClip(selC))?findClip(selC).c.start:null})"))
                fire(i); pg.wait_for_timeout(420)
                d = json.loads(R("JSON.stringify(__U)"))
                ev = [e for e in d['ev'] if e['t'] == {'scroll': 'wheel', 'wheel': 'wheel', 'pinch': 'wheel', 'drag': 'pointermove', 'key': 'keydown'}[kind]]
                if not ev: continue
                e0 = ev[0]; ts = e0['ts']
                r = {'queue': e0['at'] - ts}
                if kind == 'key':
                    if d['notes']: r['drawn'] = d['notes'][0] - ts
                    rows.append(r); continue
                v0 = s0[field]; ch = [(x['at'], x[field]) for x in d['dr'] if x[field] is not None and abs(x[field] - v0) > 1e-9]
                if not ch: continue
                fin = ch[-1][1]; tot = fin - v0
                r['drawn'] = ch[0][0] - ts
                for pc in (.5, .9):
                    hit = next((t for t, v in ch if abs(v - v0) >= pc * abs(tot) - 1e-12), ch[-1][0]); r['t%d' % int(pc * 100)] = hit - ts
                r['draws'] = len(ch); rows.append(r)
            agg = {}
            for k in ('queue', 'drawn', 't50', 't90', 'draws'):
                v = [r[k] for r in rows if k in r]
                if v: agg[k] = {'med': round(stt.median(v), 2), 'p90': round(q(v, .9), 2), 'max': round(max(v), 2)}
            agg['n'] = len(rows); out['latency'][kind] = agg
            print('%-6s %s' % (kind, json.dumps(agg)), flush=True)

        R("UI.follow=false")
        if W('scroll'): sample('scroll', lambda i: wheel(12 if i % 2 == 0 else -12, 0), 'x')
        if W('wheel'): sample('wheel', lambda i: wheel(0, 100 if i % 2 == 0 else -100, 8), 'x')       # Shift (8) + a notched wheel step
        if W('pinch'): sample('pinch', lambda i: wheel(0, -6 if i % 2 == 0 else 6, 2), 'ppb')        # ctrlKey without a Control key down = pinch
        # clip drag: hold the first clip that is fully in view, move 12 px per sample
        R("V.ppb=32;V.x=120;clampV();dirty=true"); pg.wait_for_timeout(600)
        clip = json.loads(R("""(()=>{for(let i=0;i<S.tracks.length;i++){const t=S.tracks[i];if(t.hidden)continue;const y=AY+TRY[i]-V.y+V.th/2;if(y<AY+10||y>arr.clientHeight-40)continue;
          for(const c of t.clips){const a=Math.max(X0+40,X0+(c.start-V.x)*V.ppb),z=Math.min(X0+arrW-40,X0+(c.start+c.len-V.x)*V.ppb);if(z-a>80){return JSON.stringify({x:(a+z)/2,y,cid:c.id})}}}return 'null'})()"""))
        if clip and W('drag'):
            px, py = box['l'] + clip['x'] * 1, box['t'] + clip['y'] * 1
            pg.mouse.move(px, py); pg.mouse.down(); pg.wait_for_timeout(200)
            st = {'x': px}
            def mv(i):
                st['x'] += 12 if (i // 6) % 2 == 0 else -12; pg.mouse.move(st['x'], py)
            sample('drag', mv, 'cs')
            pg.mouse.up(); R("undo()")
        # computer-keyboard piano on the first instrument track
        R("{const t=S.tracks.find(t=>t.kind==='inst'&&!t.mute);if(t){selT=t.id;t.arm=true;renderHeaders()}}"); pg.wait_for_timeout(300)
        def key(i): cdp.send('Input.dispatchKeyEvent', {'type': 'keyDown', 'code': 'KeyZ', 'key': 'z', 'text': 'z', 'windowsVirtualKeyCode': 90}); pg.wait_for_timeout(60); cdp.send('Input.dispatchKeyEvent', {'type': 'keyUp', 'code': 'KeyZ', 'key': 'z', 'windowsVirtualKeyCode': 90})
        if W('key'): sample('key', key, 'x')

        # ---- frame times under continuous real input
        def metrics():
            return {x['name']: x['value'] for x in cdp.send('Performance.getMetrics')['metrics']}
        def window_(name, driver=None):
            m0 = metrics(); t0 = time.time()
            pg.evaluate("(ms)=>{window.__ivp=("+REC+")(ms)}", A.win * 1000)
            if driver:
                k = 0
                while time.time() - t0 < A.win: driver(k); k += 1
            iv = pg.evaluate("()=>window.__ivp")[2:] or [0]; m1 = metrics(); n = len(iv)
            o = {'fps': round(n / (sum(iv) / 1000), 1), 'med': round(q(iv, .5), 2), 'p95': round(q(iv, .95), 2), 'worst': round(max(iv), 1),
                 'main': round((m1['TaskDuration'] - m0['TaskDuration']) * 1000 / n, 2), 'js': round((m1['ScriptDuration'] - m0['ScriptDuration']) * 1000 / n, 2),
                 'layout': round((m1['LayoutDuration'] + m1['RecalcStyleDuration'] - m0['LayoutDuration'] - m0['RecalcStyleDuration']) * 1000 / n, 2),
                 'events': k if driver else 0}
            out['frames'][name] = o; print('%-10s %s' % (name, json.dumps(o)), flush=True)
        reset()
        if W('idle'): window_('idle')
        if W('scroll'): window_('scroll', lambda k: wheel(8 if (k // 40) % 2 == 0 else -8, 0))
        if W('pinch'): window_('pinch', lambda k: wheel(0, -4 if (k // 40) % 2 == 0 else 4, 2))
        if clip and W('drag'):
            pg.mouse.move(px, py); pg.mouse.down(); st = {'x': px}
            def dr(k):
                st['x'] += 6 if (k // 30) % 2 == 0 else -6; pg.mouse.move(st['x'], py)
            window_('drag', dr); pg.mouse.up(); R("undo()")
        R("openMixer()"); pg.wait_for_timeout(1000); R("if(play.on)stop();pos=128;start()"); pg.wait_for_timeout(1500)
        window_('playmix')
        # key latency while playing with the mixer open: the input waits for whatever the main thread is doing
        rows = []
        for i in range(A.n):
            reset(); pg.wait_for_timeout(97 + (i * 13) % 50); key(i); pg.wait_for_timeout(150)
            d = json.loads(R("JSON.stringify(__U)")); ev = [e for e in d['ev'] if e['t'] == 'keydown']
            if ev and d['notes']: rows.append({'queue': ev[0]['at'] - ev[0]['ts'], 'drawn': d['notes'][0] - ev[0]['ts']})
        agg = {k: {'med': round(stt.median([r[k] for r in rows]), 2), 'p90': round(q([r[k] for r in rows], .9), 2), 'max': round(max(r[k] for r in rows), 2)} for k in ('queue', 'drawn')} if rows else {}
        agg['n'] = len(rows); out['latency']['key_playing_mixer'] = agg; print('key_playmix', json.dumps(agg), flush=True)
        R("stop()")
        out['errors'] = errs[:10]
        json.dump(out, open(A.out, 'w'), indent=1); print('errors', errs[:5]); b.close()
main()
