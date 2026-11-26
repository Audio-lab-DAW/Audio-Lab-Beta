"""App activity and freeze in the background (task AO, v0.218): python3 tools/ui-tests/taskAO.py [index.html] [out dir] [quick]
Headless Chromium, Fractals demo. The page's visibility and focus are emulated (document.visibilityState, document.hidden, document.hasFocus and the
events), every native requestAnimationFrame, setInterval and setTimeout call-back is counted underneath the app, and the desktop app's events are mocked.
- the button logo and the Settings logo move in every 5 s sample for more than 2 minutes with the mouse at rest (also in the Lighter look), stand still
  in the background and move again on return;
- another app in front (blur), hidden or minimised (visibilitychange), and the desktop app's own events: drawing stops at once, after about 2 s every
  frame and timer is gone and the audio engine is suspended; the return brings a frame within one screen frame, the same audio engine, no errors;
- playing in the background: no frames, the sound is the same as in front (recorded from the master, compared sample by sample), no dropouts;
  Play, a key or MIDI from the frozen state wakes the sound without the drawing; after Stop it freezes again;
- an armed track keeps the audio engine on and says why; the two switches in Settings work and have tooltips; a page that never had the focus is left alone;
- an export started and then sent to the background finishes with the same samples; Fractals demo levels unchanged."""
import sys, os, json, base64, hashlib, time
import numpy as np
from playwright.sync_api import sync_playwright
F = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
OUT = sys.argv[2] if len(sys.argv) > 2 else '.'
QUICK = len(sys.argv) > 3 and sys.argv[3] == 'quick'
os.makedirs(OUT, exist_ok=True)
SRC = open(F, encoding='utf-8').read()
FAIL = []
def ok(c, m):
    print(('ok   ' if c else 'FAIL ') + m, flush=True)
    if not c: FAIL.append(m)
INIT = r"""
(()=>{
 const T=window.__t={hidden:false,focus:true,raf:0,iv:0,to:0,ivBy:{},frames:[]};
 Object.defineProperty(Document.prototype,'visibilityState',{configurable:true,get(){return T.hidden?'hidden':'visible'}});
 Object.defineProperty(Document.prototype,'hidden',{configurable:true,get(){return T.hidden}});
 Document.prototype.hasFocus=function(){return T.focus&&!T.hidden};
 const raf=window.requestAnimationFrame.bind(window);
 window.requestAnimationFrame=function(f){return raf(function(t){T.raf++;if(T.t0&&!T.began)T.began=performance.now()-T.t0;return f(t)})};
 const si=window.setInterval.bind(window);
 window.setInterval=function(f,ms,...a){const k=ms+' ms '+String(f).slice(0,70);return si(function(){T.iv++;T.ivBy[k]=(T.ivBy[k]||0)+1;return f.apply(this,arguments)},ms,...a)};
 const st=window.setTimeout.bind(window);
 window.setTimeout=function(f,ms,...a){return st(function(){T.to++;return typeof f==='function'?f.apply(this,arguments):0},ms,...a)};
 /* 'blur': another app in front, the window still visible. 'hide': minimised or on another desktop. 'front': back. 'hostblur', 'hostmin', 'hostfront': only the desktop app says so. */
 window.__go=function(kind){T.t0=performance.now();T.began=0;T.first=0;const h=window.__host;
  if(kind==='front'){T.hidden=false;T.focus=true;if(h)h.say({focused:true,visible:true,minimized:false});document.dispatchEvent(new Event('visibilitychange'));window.dispatchEvent(new Event('pageshow'));window.dispatchEvent(new Event('focus'))}
  else if(kind==='blur'){T.focus=false;window.dispatchEvent(new Event('blur'));document.documentElement.dispatchEvent(new MouseEvent('mouseleave'))}
  else if(kind==='hide'){T.focus=false;T.hidden=true;window.dispatchEvent(new Event('blur'));document.dispatchEvent(new Event('visibilitychange'))}
  else if(kind==='hostblur'){T.focus=false;h.say({focused:false,visible:true,minimized:false})}
  else if(kind==='hostmin'){T.focus=false;h.say({focused:false,visible:false,minimized:true})}
  else if(kind==='hostother'){T.focus=false;h.say({focused:true,visible:true,minimized:false})}};
})();
if(!localStorage.getItem('audiolab-ui'))localStorage.setItem('audiolab-ui',JSON.stringify({splash:false,lat3:1}))
"""
HOST = """window.__host={cb:null,sets:[],st:{focused:true,visible:true,minimized:false},say(d){this.st=d;if(this.cb)this.cb(d)}};
window.audiolabDesktop={isDesktop:true,platform:'darwin',version:()=>Promise.resolve('0.218.0'),programVersion:()=>Promise.resolve('0.218'),updateCheck:()=>Promise.resolve({status:'current'}),updateStatus:()=>Promise.resolve({}),
 onDock:()=>{},onFromChild:()=>{},onDockHover:()=>{},dac:null,displayHz:()=>Promise.resolve(60),
 activity:{on:cb=>{window.__host.cb=cb;return()=>{}},get:()=>Promise.resolve(window.__host.st),set:s=>{window.__host.sets.push(s)}}};"""
ST = "JSON.stringify({fg:AOS.fg,lv:AOS.lv,gate:AO.gate,alv:AO.lv,ctx:ctx?ctx.state:'none',q:AO.q.size,ivOff:[...AO.iv.values()].filter(r=>r.off).length,iv:AO.iv.size,held:AO.held.size,cls:document.documentElement.className,why:AOS.why,keep:AOS.keep,susp:AOS.susp,play:play.on})"
HASH = """(()=>{const h=c=>{if(!c||!c.width)return null;const d=c.getContext('2d').getImageData(0,0,c.width,c.height).data;let s=0;for(let i=0;i<d.length;i+=17)s=(s*31+d[i])|0;return s};return JSON.stringify({a:h(document.getElementById('atomC')),n:h(document.getElementById('navAtomC')),set:!document.getElementById('set').hidden})})()"""
REC = """(async()=>{if(!window.__rec){const src="class R extends AudioWorkletProcessor{process(I){const a=I[0];if(a&&a[0])this.port.postMessage([a[0].slice(0),(a[1]||a[0]).slice(0)]);return true}}registerProcessor('ao-rec',R)";
 await ctx.audioWorklet.addModule(URL.createObjectURL(new Blob([src],{type:'application/javascript'})));const n=new AudioWorkletNode(ctx,'ao-rec',{numberOfInputs:1,numberOfOutputs:0,channelCount:2,channelCountMode:'explicit'});
 window.__rec={n,L:[],on:false};n.port.onmessage=e=>{if(window.__rec.on)window.__rec.L.push(e.data[0])};outBus.connect(n)}window.__rec.L=[];window.__rec.on=true;return 1})()"""
RECGET = """(()=>{const R=window.__rec;R.on=false;const n=R.L.reduce((a,b)=>a+b.length,0),o=new Float32Array(n);let k=0;for(const b of R.L){o.set(b,k);k+=b.length}const u=new Uint8Array(o.buffer);let s='';for(let i=0;i<u.length;i+=32768)s+=String.fromCharCode.apply(null,u.subarray(i,i+32768));return btoa(s)})()"""

def open_page(p, host=False, scale=1):
    b = p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required']); pg = b.new_page(viewport={'width': 1600, 'height': 1000}, device_scale_factor=scale); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)[:400]))
    pg.on('console', lambda m: errs.append('console: ' + m.text[:300]) if m.type == 'error' and '404' not in m.text and 'fetching the script' not in m.text else None)
    pg.route('https://app.test/**', lambda r: r.fulfill(status=200, content_type='text/html', body=SRC.encode()) if r.request.url.endswith('.html') else r.fulfill(status=404, body=b''))
    pg.add_init_script(INIT + (HOST if host else ''))
    pg.goto('https://app.test/index.html'); pg.wait_for_timeout(8000)
    R = lambda c: pg.evaluate("c=>window.AudioLab.run(c)", c)
    R("(()=>{const c=document.getElementById('liteNote');if(c)c.remove();pmSetOn(false);AOG.boot=0;return 1})()")
    pg.mouse.click(800, 30); pg.wait_for_timeout(1200)
    return b, pg, errs, R
def counts(pg): return pg.evaluate("()=>({raf:__t.raf,iv:__t.iv,to:__t.to})")
def rate(pg, ms=2000):
    a = counts(pg); pg.wait_for_timeout(ms); b = counts(pg); return {k: (b[k] - a[k]) * 1000.0 / ms for k in a}
WHY = []
def wait_lv(pg, R, lv, limit=40):
    t0 = time.time(); del WHY[:]
    while time.time() - t0 < limit:
        s = json.loads(R(ST))
        if s['lv'] == lv: return time.time() - t0
        if not WHY or WHY[-1][1] != s['why']: WHY.append(('%.1f' % (time.time() - t0), s['why']))
        pg.wait_for_timeout(100)
    return None
def go(pg, kind): pg.evaluate("k=>window.__go(k)", kind)
def front(pg, R):
    """come back and measure: time to the first frame, and that the audio engine was told to resume before it"""
    pg.evaluate("""()=>{const T=window.__t;T.first=0;T.ctxAt=0;const c=window.AudioLab.run('ctx');T.wasSusp=c.state;const t0=performance.now();window.__go('front');T.t0=t0;T.goMs=performance.now()-t0;
      c.addEventListener('statechange',function h(){if(c.state==='running'){T.ctxAt=performance.now()-t0;c.removeEventListener('statechange',h)}});
      requestAnimationFrame(()=>{T.first=performance.now()-t0})}""")
    pg.wait_for_timeout(700)
    return pg.evaluate("()=>({began:__t.began,first:__t.first,ctxAt:__t.ctxAt,goMs:__t.goMs,was:__t.wasSusp})")

with sync_playwright() as p:
    # ---------- 1. the logos ----------
    b, pg, errs, R = open_page(p)
    ok(not errs, 'no page errors on load ' + '; '.join(errs))
    print('version', R('VERSION'))
    pg.click('#bLogo'); pg.wait_for_timeout(1200); pg.mouse.move(900, 600)
    N = 6 if QUICK else 26
    for look, lite in (('Full effects', False), ('Lighter', True)):
        if lite: R("(()=>{pmSetStop(1);return 1})()"); pg.wait_for_timeout(800)
        n = N if not lite else 5; prev = json.loads(R(HASH)); mv = {'a': 0, 'n': 0}
        for i in range(n):
            pg.wait_for_timeout(5000); cur = json.loads(R(HASH))
            for k in mv: mv[k] += cur[k] != prev[k]
            prev = cur
        ok(mv['a'] == n and mv['n'] == n and prev['set'], '%s: mouse at rest for %d s, Settings open: the button logo moved in %d of %d samples, the Settings logo in %d of %d' % (look, n * 5, mv['a'], n, mv['n'], n))
    R("(()=>{pmSetOn(false);return 1})()"); pg.wait_for_timeout(500)
    go(pg, 'blur'); pg.wait_for_timeout(700); h0 = json.loads(R(HASH)); pg.wait_for_timeout(1500); h1 = json.loads(R(HASH))
    ok(h0['a'] == h1['a'] and h0['n'] == h1['n'], 'in the background both logos stand still')
    paused = pg.evaluate("()=>getComputedStyle(document.getElementById('bLogo')).animationPlayState")
    ok(paused == 'paused', 'in the background CSS animations are paused (the button glow: %s)' % paused)
    go(pg, 'front'); pg.wait_for_timeout(600); h2 = json.loads(R(HASH)); pg.wait_for_timeout(600); h3 = json.loads(R(HASH))
    ok(h2['a'] != h3['a'] and h2['n'] != h3['n'], 'back in front both logos move again')
    cost = json.loads(R("(()=>{const a=document.getElementById('atomC'),n=document.getElementById('navAtomC');let t=performance.now();for(let i=0;i<200;i++)paintAtom(a,28,Math.min(4,devicePixelRatio*ZOOM*2),AT.btn,i/30);const ta=(performance.now()-t)/200;t=performance.now();for(let i=0;i<100;i++)paintAtom(n,132,Math.min(2.5,devicePixelRatio)*ZOOM,AT.big,i/30);return JSON.stringify({btn:ta,big:(performance.now()-t)/100})})()"))
    print('     cost of one logo picture: button %.3f ms (30 a second = %.1f %% of one core), Settings logo %.3f ms' % (cost['btn'], cost['btn'] * 30 / 10, cost['big']))
    R("(()=>{closeSet();return 1})()")
    # ---------- 2. freeze: another app in front, hidden ----------
    base = rate(pg)
    print('     in front, idle: %.0f frames, %.0f timer ticks, %.1f one-shot timers a second' % (base['raf'], base['iv'], base['to']))
    ctx_id = R("(()=>{window.__c0=ctx;return ctx.state+' '+ctx.sampleRate})()")
    snap0 = R("JSON.stringify({pos,sel:selT,n:S.tracks.length,vx:V.x,ppb:V.ppb,pj:PJ.cur})"); wdn = R("WD.log.length+WD.rec.length")
    for kind in ('blur', 'hide'):
        go(pg, kind); pg.wait_for_timeout(450); s = json.loads(R(ST)); r1 = rate(pg, 600)
        ok(s['lv'] >= 1 and s['gate'] and r1['raf'] == 0, '%s: drawing stops at once (level %d, %.0f frames a second)' % (kind, s['lv'], r1['raf']))
        t = wait_lv(pg, R, 2); s = json.loads(R(ST))
        ok(t is not None, '%s: frozen %.1f s after the drawing stopped (%s)' % (kind, (t or 0) + 1.05, s['why']))
        pg.wait_for_timeout(1500); pg.evaluate("()=>{__t.ivBy={}}"); r2 = rate(pg, 5000); s = json.loads(R(ST)); by = pg.evaluate("()=>__t.ivBy")
        app_iv = sum(v for k, v in by.items() if 'aoEval' not in k)
        ok(r2['raf'] == 0 and app_iv == 0, '%s, frozen: %.0f frames a second, %d of the app\'s %d repeating timers still tick (only the 1 s watch of the freeze itself: %.1f ticks a second), %.1f one-shot timers a second' % (kind, r2['raf'], s['iv'] - s['ivOff'], s['iv'], r2['iv'], r2['to']))
        ok(s['ctx'] == 'suspended' and s['susp'], '%s, frozen: the audio engine is suspended (%s)' % (kind, s['ctx']))
        ok(s['cls'] == 'aobg', '%s, frozen: the root element has the class that pauses CSS animations' % kind)
        f = front(pg, R); s = json.loads(R(ST))
        ok(0 < f['began'] <= 20, '%s, back: the first frame starts %.1f ms after the return (one frame is 16.7 ms here) and the whole first picture is done after %.1f ms; the audio engine was told to resume before that, in the same call (%.2f ms), and ran again after %.0f ms' % (kind, f['began'], f['first'], f['goMs'], f['ctxAt']))
        ok(s['lv'] == 0 and not s['gate'] and s['ctx'] == 'running' and s['ivOff'] == 0 and s['held'] == 0 and s['cls'] == '', '%s, back: everything runs again (%d timers, audio %s)' % (kind, s['iv'], s['ctx']))
        r3 = rate(pg, 1500); ok(r3['raf'] > base['raf'] * .6 and r3['iv'] > base['iv'] * .6, '%s, back: %.0f frames and %.0f timer ticks a second (before: %.0f and %.0f)' % (kind, r3['raf'], r3['iv'], base['raf'], base['iv']))
    ok(R("ctx===window.__c0?1:0") == 1 and R("WD.log.length+WD.rec.length") == wdn, 'the same audio engine after both returns, the watchdog did not step in')
    ok(R("JSON.stringify({pos,sel:selT,n:S.tracks.length,vx:V.x,ppb:V.ppb,pj:PJ.cur})") == snap0, 'position, selection, view and project unchanged')
    red = pg.evaluate("""()=>{const run=c=>window.AudioLab.run(c);window.__dr=0;return 1}""")
    R("(()=>{const _d=drawArr;window.__dr=0;drawArr=function(){window.__dr++;return _d.apply(this,arguments)};const _m=drawMixer;window.__dm=0;drawMixer=function(){window.__dm++;return _m.apply(this,arguments)};return 1})()")
    go(pg, 'hide'); wait_lv(pg, R, 2); R("(()=>{window.__dr=0;window.__dm=0;return 1})()"); pg.wait_for_timeout(600); z = R("window.__dr+window.__dm"); front(pg, R)
    ok(z == 0 and R("window.__dr") >= 1 and R("window.__dm") >= 1, 'frozen: no arrangement or mixer drawing; back: the arrangement is drawn again (%d full pass in 0.7 s) and the mixer too' % R("window.__dr"))
    # the mouse over the unfocused window counts as in front
    go(pg, 'blur'); wait_lv(pg, R, 2); pg.mouse.move(700, 400); pg.wait_for_timeout(300); s = json.loads(R(ST))
    ok(s['lv'] == 0 and s['ctx'] in ('running',), 'another app has the focus, the mouse moves over the window: in front again (level %d, audio %s)' % (s['lv'], s['ctx']))
    pg.evaluate("()=>document.documentElement.dispatchEvent(new MouseEvent('mouseleave'))"); t = wait_lv(pg, R, 2)
    ok(t is not None, 'the mouse leaves the unfocused window: frozen again after %.1f s' % ((t or 0)))
    go(pg, 'front'); pg.wait_for_timeout(500)
    # ---------- 3. playing in the background ----------
    R("(()=>{for(const t of S.tracks)t.solo=t.name==='Kick';changed(false);syncGraph();return 1})()"); pg.wait_for_timeout(600)
    def record(mode):
        R("(()=>{stop();pos=64;return 1})()"); pg.wait_for_timeout(2600)
        if mode == 'frozen': go(pg, 'blur'); t = wait_lv(pg, R, 2); assert t is not None
        pg.evaluate("c=>window.AudioLab.run(c)", REC); u0 = R("typeof urNow==='function'?urNow():-1")
        R("(()=>{window.__cb=0;pos=64;start();window.__k0=[ctx.currentTime,performance.now(),window.__pa||0];return 1})()")
        if mode == 'frozen': pg.wait_for_timeout(120); s = json.loads(R(ST)); ok(s['lv'] == 1 and s['gate'] and s['play'] and s['ctx'] == 'running', 'Play from the frozen state (as from a controller): the sound wakes without the drawing (level %d, audio %s)' % (s['lv'], s['ctx']))
        if mode == 'away': pg.wait_for_timeout(1000); go(pg, 'blur')
        r = None
        if mode != 'front': pg.wait_for_timeout(900); r = rate(pg, 3000); pg.wait_for_timeout(1100 if mode == 'away' else 2000)
        else: pg.wait_for_timeout(6000)
        beat = R("curBeat()"); s = json.loads(R(ST)); u1 = R("typeof urNow==='function'?urNow():-1")
        k = json.loads(R("JSON.stringify([ctx.currentTime-window.__k0[0],(performance.now()-window.__k0[1])/1000,(window.__pa||0)-window.__k0[2]])"))
        x = np.frombuffer(base64.b64decode(R(RECGET)), dtype=np.float32).copy(); R("(()=>{stop();return 1})()")
        return x, r, beat, s, (u0, u1, k[0] / k[1], k[2] / k[1])
    def onset(x): return int(np.argmax(np.abs(x - np.median(x[:2000])) > 0.3))   # the first kick (a stopped voice can leave a small offset, which is not it)
    N4 = 44100 * 4
    def best(a, oa, c, oc):
        """smallest difference over a few samples of shift: two live plays never start on the same fraction of a sample"""
        A = a[oa:oa + N4].astype(np.float64); r = None
        for sh in range(-40, 41):
            if oc + sh < 0: continue
            C = c[oc + sh:oc + sh + N4].astype(np.float64)
            if len(C) < len(A) or len(A) < N4 * .9: continue
            d = float(np.sqrt(np.mean((A - C) ** 2)))
            if r is None or d < r: r = d
        return 20 * np.log10(max(1e-12, r)) if r is not None else 0.0
    R("(()=>{const _p=paTick;window.__pa=0;paTick=function(){window.__pa++;return _p.apply(this,arguments)};return 1})()")
    ref, _, beat0, _, u = record('front'); o0 = onset(ref); refs = [record('front')[0] for i in range(2)]
    lev = 20 * np.log10(float(np.sqrt(np.mean(ref[o0:o0 + N4].astype(np.float64) ** 2)))); base = [best(ref, o0, x, onset(x)) for x in refs]; base_d = max(base)
    print('     plays in front (solo Kick from beat 64, 4 s from the first hit, recorded from the master): signal %.1f dB; two more plays differ from the first by %s dB (live plays are never identical); audio clock against the wall clock %.4f; the automation and modulator step ran %.0f times a second' % (lev, ' and '.join('%.1f' % v for v in base), u[2], u[3]))
    for mode, label in (('away', 'sent to the background 1 s after Play'), ('frozen', 'Play started while frozen')):
        x, r, beat, s, u = record(mode); o1 = onset(x); dif = best(ref, o0, x, o1)
        ok(r['raf'] == 0 and s['lv'] == 1 and s['play'], '%s: %.0f frames a second while it plays (level %d), %.0f timer ticks a second for the sound' % (label, r['raf'], s['lv'], r['iv']))
        ok(dif < base_d + 6 and dif < lev - 20, '%s: the same 4 s differ from the play in front by %.1f dB (plays in front among themselves: up to %.1f dB)' % (label, dif, base_d))
        ok(abs(u[2] - 1) < .01 and u[1] - u[0] <= 2, '%s: no dropout (the audio clock ran at %.4f of the wall clock; underruns counted by the browser %s before, %s after)' % (label, u[2], u[0], u[1]))
        ok(u[3] > 15, '%s: automation and modulators keep being applied without the frame loop (%.0f times a second)' % (label, u[3]))
        t0 = time.time(); t = wait_lv(pg, R, 2); dt = time.time() - t0; pg.wait_for_timeout(250); s = json.loads(R(ST))
        ok(t is not None and s['ctx'] == 'suspended' and dt < 8, '%s: after Stop the app freezes again, %.1f s later (audio %s; on the way: %s)' % (label, dt, s['ctx'], ', '.join(w for _, w in WHY)))
        go(pg, 'front'); pg.wait_for_timeout(400)
    R("(()=>{for(const t of S.tracks)t.solo=false;changed(false);syncGraph();return 1})()")
    # a key from a MIDI controller while frozen
    go(pg, 'hide'); wait_lv(pg, R, 2); R("(()=>{AOG.midi=9000;noteOn(36,.8,'m60');return 1})()"); pg.wait_for_timeout(250); s = json.loads(R(ST)); r = rate(pg, 800)
    ok(s['lv'] == 1 and s['ctx'] == 'running' and s['gate'] and r['raf'] == 0, 'a MIDI key while frozen: the audio engine runs again (%s), still no drawing' % s['ctx'])
    R("(()=>{noteOff('m60');return 1})()"); pg.wait_for_timeout(6200); s = json.loads(R(ST))
    ok(s['lv'] == 1 and 'MIDI' in s['keep'], 'after the key: the audio engine stays on for a while (%s)' % s['keep'])
    t = wait_lv(pg, R, 2); ok(t is not None, 'then it freezes again'); go(pg, 'front'); pg.wait_for_timeout(400); R("(()=>{AOG.midi=30000;AOS.midiT=-1e9;return 1})()")
    # ---------- 4. armed track ----------
    R("(()=>{const t=S.tracks.find(t=>t.name==='Kick');t.arm=true;changed(false);return 1})()"); n0 = R("WD.log.length")
    go(pg, 'blur'); pg.wait_for_timeout(5000); s = json.loads(R(ST)); r = rate(pg, 1000)
    ok(s['lv'] == 1 and s['ctx'] == 'running' and 'armed' in s['keep'] and r['raf'] == 0, 'an armed track: drawing stops, the audio engine stays on (%s)' % s['keep'])
    ok('Kick' in R("WD.log[0]?WD.log[0].msg:''"), 'and the audio engine log says so: ' + R("WD.log[0]?WD.log[0].msg:''"))
    R("(()=>{const t=S.tracks.find(t=>t.name==='Kick');t.arm=false;changed(false);return 1})()"); t = wait_lv(pg, R, 2)
    ok(t is not None, 'disarmed: frozen after %.1f s' % (t or 0)); go(pg, 'front'); pg.wait_for_timeout(400)
    # ---------- 5. Settings ----------
    R("(()=>{openSettings('perf');return 1})()"); pg.wait_for_timeout(700)
    rows = json.loads(R("JSON.stringify(['aoFrz','aoVis'].map(id=>{const e=document.getElementById(id),r=e&&e.closest('.pmr');return e?{on:e.checked,vis:!!r.offsetParent,tip:r.title,name:r.querySelector('.pmq').textContent}:null}).concat([{inf:(document.getElementById('aoInf')||{}).textContent,tip:(document.getElementById('aoInf')||{}).title}]))"))
    ok(rows[0] and rows[0]['on'] and rows[0]['vis'] and len(rows[0]['tip']) > 40 and rows[0]['name'] == 'Freeze when in the background', 'Settings, Performance: "Freeze when in the background" is there, on, with a tooltip')
    ok(rows[1] and not rows[1]['on'] and len(rows[1]['tip']) > 40, 'and "Keep visuals in the background", off, with a tooltip')
    ok('frozen after' in (rows[2]['inf'] or '') or 'drawing stopped' in (rows[2]['inf'] or ''), 'the line under them says what happened last time: ' + str(rows[2]['inf']))
    txt = rows[0]['tip'] + rows[1]['tip'] + (rows[2]['inf'] or ''); ok('—' not in txt and '–' not in txt, 'no dashes in the new texts')
    pg.screenshot(path=os.path.join(OUT, 'taskAO_settings.png'))
    pg.click('#aoVis', force=True); pg.wait_for_timeout(200); R("(()=>{closeSet();return 1})()")
    go(pg, 'blur'); wait_lv(pg, R, 2); pg.wait_for_timeout(300); s = json.loads(R(ST)); r = rate(pg, 1500)
    ok(R("UI.aoVisuals===true?1:0") == 1 and r['raf'] > 20 and s['ctx'] == 'suspended' and not s['gate'], 'Keep visuals on: the drawing goes on in the background (%.0f frames a second), only the audio engine pauses (%s)' % (r['raf'], s['ctx']))
    go(pg, 'front'); pg.wait_for_timeout(400); R("(()=>{UI.aoVisuals=false;UI.aoFreeze=false;saveUI();aoEval('test');return 1})()")
    go(pg, 'hide'); pg.wait_for_timeout(5000); s = json.loads(R(ST)); r = rate(pg, 1500)
    ok(s['lv'] == 0 and r['raf'] > 20 and s['ctx'] == 'running', 'Freeze switched off: nothing stops in the background (%.0f frames a second, audio %s)' % (r['raf'], s['ctx']))
    go(pg, 'front'); R("(()=>{UI.aoFreeze=true;saveUI();aoEval('test');return 1})()"); pg.wait_for_timeout(300)
    # ---------- 6. an export sent to the background ----------
    kid = R("S.tracks.find(t=>t.name==='Kick').id"); o = {"b0": 64, "b1": 96, "sr": 44100, "tail": 0, "lim": False, "fast": False, "single": False, "only": kid}
    def pull(h):
        out = []
        for ch in range(h['ch']):
            for off in range(0, h['len'], 200000):
                out.append(base64.b64decode(pg.evaluate("a=>AudioLab.pull(a[0],a[1],a[2],a[3])", [h['id'], ch, off, min(200000, h['len'] - off)])))
        pg.evaluate("i=>AudioLab.free(i)", h['id']); return b''.join(out)
    h = pg.evaluate("o=>AudioLab.render(o)", o); a = pull(h); x = np.frombuffer(a, dtype=np.float32); lv_k = 20 * np.log10(float(np.sqrt(np.mean(x.astype(np.float64) ** 2))))
    bid = R("S.tracks.find(t=>t.name==='Bass').id"); ob = dict(o); ob['only'] = bid; x2 = np.frombuffer(pull(pg.evaluate("o=>AudioLab.render(o)", ob)), dtype=np.float32); lv_b = 20 * np.log10(float(np.sqrt(np.mean(x2.astype(np.float64) ** 2))))
    # the export that goes to the background: the Kick alone over the whole song, beats 0 to 384 (long enough to still be working well after the window is gone).
    # A long render is not always the same twice even in front (seen on v0.215 before this work: 1 of 4 differed), so the reference is made twice.
    o = {"b0": 0, "b1": 384, "sr": 44100, "tail": 0, "lim": False, "fast": False, "single": False, "only": kid}
    refs = []; t0 = time.time()
    for i in range(2): refs.append(hashlib.md5(pull(pg.evaluate("o=>AudioLab.render(o)", o))).hexdigest()[:12])
    if refs[0] != refs[1]: refs.append(hashlib.md5(pull(pg.evaluate("o=>AudioLab.render(o)", o))).hexdigest()[:12])
    t_front = (time.time() - t0) / len(refs)
    pg.evaluate("o=>{window.__ex=null;window.__exT=performance.now();AudioLab.render(o).then(h=>{window.__ex=h;window.__exD=performance.now()-window.__exT})}", o)
    pg.wait_for_timeout(60); go(pg, 'hide'); pg.wait_for_timeout(500); s = json.loads(R(ST)); seen = [s['why']]
    lvs = set(); fr = rate(pg, 1500)
    for i in range(3000):
        if pg.evaluate("()=>!!window.__ex"): break
        pg.wait_for_timeout(100)
        if i % 5 == 0: z = json.loads(R(ST)); seen.append(z['why']); lvs.add(z['lv'])
    h2 = pg.evaluate("()=>window.__ex"); ex_s = (pg.evaluate("()=>window.__exD") or 0) / 1000
    ok(h2 is not None and 'working' in seen and lvs == {1}, 'an export (Kick alone, beats 0 to 384) sent to the background 60 ms after its start carried on and finished: %.1f s (in front, with the transfer to the test: %.1f s); the app stayed at level %s (%s), %.0f frames a second' % (ex_s, t_front, sorted(lvs), ', '.join(sorted(set(seen))), fr['raf']))
    c = hashlib.md5(pull(h2)).hexdigest()[:12] if h2 else ''
    ok(c in refs, 'and it is the same to the last bit as the export made in front (%s; in front: %s)' % (c, ', '.join(refs)))
    t = wait_lv(pg, R, 2); ok(t is not None, 'after the export the app freezes (%.1f s later)' % (t or 0)); go(pg, 'front'); pg.wait_for_timeout(400)
    ok(abs(lv_k - (-9.75669)) < 6e-6 and abs(lv_b - (-25.48699)) < 6e-6, 'Fractals demo unchanged: solo Kick %.5f dB, Bass %.5f dB (beats 64 to 96)' % (lv_k, lv_b))
    ok(not errs, 'no page or console errors in the whole run ' + '; '.join(errs[:4]))
    b.close()
    # ---------- 7. the desktop app's events (mocked) ----------
    b, pg, errs, R = open_page(p, host=True)
    ok(R("AOS.ha?1:0") == 1, 'desktop app with the new events: the page listens to them')
    pg.evaluate("()=>{__t.focus=false;document.documentElement.dispatchEvent(new MouseEvent('mouseleave'))}"); pg.wait_for_timeout(4500); s = json.loads(R(ST))
    ok(s['lv'] == 0 and s['fg'], 'a page without the focus that was never seen going away (opened with the cursor in the address bar) is not frozen (level %d)' % s['lv'])
    pg.evaluate("()=>{__t.focus=true}")
    go(pg, 'hostblur'); pg.wait_for_timeout(400); s = json.loads(R(ST)); t = wait_lv(pg, R, 2); pg.wait_for_timeout(250); s2 = json.loads(R(ST))
    ok(s['lv'] >= 1 and t is not None and s2['ctx'] == 'suspended', 'the desktop app says another app has the focus (window still visible): drawing off, then frozen after %.1f s' % ((t or 0) + .4))
    go(pg, 'hostother'); pg.wait_for_timeout(300); s = json.loads(R(ST))
    ok(s['lv'] == 0 and s['ctx'] == 'running', 'the desktop app says another AudioLab window has the focus: this window is in front too')
    go(pg, 'hostmin'); t = wait_lv(pg, R, 2); ok(t is not None, 'the desktop app says the window is minimised or hidden: frozen after %.1f s' % (t or 0))
    f = front(pg, R); ok(0 < f['began'] <= 20, 'restored: the first frame starts after %.1f ms' % f['began'])
    R("(()=>{start();return 1})()"); pg.wait_for_timeout(300); go(pg, 'hostmin'); pg.wait_for_timeout(1500); R("(()=>{stop();return 1})()"); wait_lv(pg, R, 2); go(pg, 'front'); pg.wait_for_timeout(300)
    sets = pg.evaluate("()=>window.__host.sets"); seq = ' > '.join(('playing' if x['playing'] else 'frozen' if x['frozen'] else 'idle') for x in sets)
    ok(any(x['playing'] for x in sets) and any(x['frozen'] for x in sets) and not sets[-1]['frozen'] and not sets[-1]['playing'], 'the page tells the desktop app when it plays and when it is frozen: ' + seq)
    ok(not errs, 'no errors with the desktop events ' + '; '.join(errs[:4]))
    b.close()
print('\n%d failed' % len(FAIL) if FAIL else '\nall passed')
for m in FAIL: print('  FAIL', m)
sys.exit(1 if FAIL else 0)
