#!/usr/bin/env python3
"""Task MX-3 (lane K, mixing engine): X1 sidechain from anything and X4 Duck under the kick, tuned for tails.
A Compressor on a steady bass keyed from a kick reduces the bass only on kicks (more than 3 dB within 10 ms of each kick, under 0.3 dB between them);
the same through Multiband, OTT, the Gate (opens only on kicks) and a dynamic EQ band (live); the keyed Compressor matches the browser's own compressor
on a steady tone within 0.5 dB; tap points line up with MX-2's compensation; loops refused; a Compressor without a source renders bit-identically;
export equals playback within 0.1 dB; the tails Ducker (switch on a return, Output menu, cable menu) gets a 16th at the song tempo and follows a
tempo change; the Sidechain row in Dark and Light; Fractals Kick and Bass unchanged.
   python3 tools/ui-tests/taskMX_3.py [index.html] [out dir]"""
import sys, os, json, base64, hashlib
import sys as _ws_sys, os as _ws_os; _ws_sys.path.insert(0, _ws_os.path.join(_ws_os.path.dirname(_ws_os.path.abspath(__file__)), '../test-songs')); from alsong import alsong  # task WS-F: the test songs
import numpy as np
from playwright.sync_api import sync_playwright
F = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
OUT = sys.argv[2] if len(sys.argv) > 2 else '.'
os.makedirs(OUT, exist_ok=True)
SRC = open(F, encoding='utf-8').read()
ARGS = ["--autoplay-policy=no-user-gesture-required", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"]
FAIL = []; N = [0]
def ok(c, m, d=''):
    N[0] += 1; print(('ok   ' if c else 'FAIL ') + m + (('   ' + str(d)[:300]) if d != '' else ''), flush=True)
    if not c: FAIL.append(m)
INIT = "if(!sessionStorage.getItem('c1i')){sessionStorage.setItem('c1i','1');localStorage.setItem('audiolab-ui',JSON.stringify({splash:false,lat3:1}))}"

def boot(p):
    b = p.chromium.launch(args=ARGS)
    ctx = b.new_context(viewport={'width': 1600, 'height': 1000}, device_scale_factor=1); pg = ctx.new_page(); logs = []
    def con(m):
        if (m.type == 'error' and 'fetching the script' not in m.text) or (m.type == 'warning' and 'nominal range' not in m.text and 'GPU stall' not in m.text and 'willReadFrequently' not in m.text and 'ScriptProcessorNode' not in m.text): logs.append(m.type + ': ' + m.text[:200])
    pg.on('console', con); pg.on('pageerror', lambda e: logs.append('pageerror: ' + str(e)[:300]))
    pg.route('https://app.test/**', alsong(lambda r: r.fulfill(status=200, content_type='text/html', body=SRC) if r.request.url.endswith('.html') else r.fulfill(status=404, body='')))
    pg.add_init_script(INIT)
    pg.goto('https://app.test/index.html'); pg.wait_for_function("()=>window.AudioLab&&window.AudioLab.version", timeout=120000); pg.wait_for_timeout(3500)
    pg.evaluate("()=>{for(const i of['splash','liteNote']){const s=document.getElementById(i);if(s)s.remove()}}")
    R = lambda c: pg.evaluate("c=>AudioLab.run(c)", c)
    return b, pg, logs, R
J = lambda R, c: json.loads(R("JSON.stringify(" + c + ")"))
db = lambda v: 20 * np.log10(max(v, 1e-12))

def render(pg, b0, b1, only=None, sr=48000):
    h = pg.evaluate("o=>AudioLab.render(o)", {'b0': b0, 'b1': b1, 'sr': sr, 'only': only, 'single': True}); ch = []
    for c in range(h['ch']):
        parts = []
        for off in range(0, h['len'], 1 << 18):
            n = min(1 << 18, h['len'] - off); parts.append(np.frombuffer(base64.b64decode(pg.evaluate("a=>AudioLab.pull(a[0],a[1],a[2],a[3])", [h['id'], c, off, n])), dtype=np.float32))
        ch.append(np.concatenate(parts))
    pg.evaluate("i=>AudioLab.free(i)", h['id']); return np.stack(ch)
hsh = lambda x: hashlib.md5(b''.join(c.tobytes() for c in x)).hexdigest()[:12]

REC = r"""window.__rec=null;(async()=>{ensureCtx();await ctx.resume();syncGraph();await new Promise(r=>setTimeout(r,120));const sp=ctx.createScriptProcessor(4096,2,2),L=[],Rr=[];
 sp.onaudioprocess=e=>{if(!play.on&&!L.length)return;L.push(e.inputBuffer.getChannelData(0).slice());Rr.push(e.inputBuffer.getChannelData(1).slice())};master.connect(sp);sp.connect(ctx.destination);
 pos=0;start();await new Promise(r=>setTimeout(r,%d));%s await new Promise(r=>setTimeout(r,%d));stop();await new Promise(r=>setTimeout(r,60));try{master.disconnect(sp)}catch(e){}sp.disconnect();
 const n=L.reduce((a,b)=>a+b.length,0),l=new Float32Array(n),r=new Float32Array(n);let o=0;for(let i=0;i<L.length;i++){l.set(L[i],o);r.set(Rr[i],o);o+=L[i].length}
 window.__recL=l;window.__recR=r;return n})().then(v=>{window.__rec=v},e=>{window.__rec='err '+e});0"""
def record(pg, R, ms, mid_js='', ms2=0):
    R(REC % (ms, mid_js, ms2)); pg.wait_for_function("()=>window.__rec!==null", timeout=30000)
    n = pg.evaluate("()=>window.__rec"); assert not isinstance(n, str), n
    ch = []
    for k in ('__recL', '__recR'):
        parts = []
        for off in range(0, n, 1 << 18):
            c = min(1 << 18, n - off)
            parts.append(np.frombuffer(base64.b64decode(pg.evaluate("a=>{const d=window[a[0]].subarray(a[1],a[1]+a[2]);let s='';const u=new Uint8Array(d.buffer,d.byteOffset,d.byteLength);for(let i=0;i<u.length;i+=32768)s+=String.fromCharCode.apply(null,u.subarray(i,i+32768));return btoa(s)}", [k, off, c])), dtype=np.float32))
        ch.append(np.concatenate(parts))
    return np.stack(ch)

SCENE = r"""(()=>{ensureCtx();S.bpm=120;const sr=ctx.sampleRate,len=Math.round(2.6*sr);
 const buf=fn=>{const b=ctx.createBuffer(2,len,sr);for(let c=0;c<2;c++){const d=b.getChannelData(c);for(let i=0;i<len;i++)d[i]=fn(i/sr)}return addBuf(b)};
 const kickB=buf(t=>{for(let k=0;k<4;k++){const u=t-(.25+.5*k);if(u>=0&&u<.08)return .8*Math.sin(2*Math.PI*60*u)}return 0});
 const bassB=buf(t=>.25*Math.sin(2*Math.PI*80*t)),burstB=buf(t=>t>=.5&&t<1.1?.8*Math.sin(2*Math.PI*60*t):0);
 const clip=id=>mkClip({start:0,len:5.2,name:'C',buf:id,dur:len/sr,gain:0,fi:0,fo:0});
 const tr=(n,c)=>{const t=mkTrack('audio',null,n,c);t.vol=1;t.pan=0;return t};
 const kick=tr('Kick','#ff6b6b');kick.vol=0;kick.clips=[clip(kickB)];const bass=tr('Bass','#4cc9f0');bass.clips=[clip(bassB)];const copy=tr('Copy','#999');copy.vol=0;copy.clips=[clip(bassB)];
 const ret={id:rid(),kind:'return',name:'Verb',color:'#7fd0ff',vol:1,pan:0,mute:false,solo:false,fx:[],clips:[]};
 S.tracks=[kick,bass,copy,ret];S.mfx=[];S.master=0;S.loop=false;S.pauto={};window.M3={kick,bass,copy,ret,kickB,bassB,burstB,clip};changed(true);syncGraph();return ctx.sampleRate})()"""
WIN = .002
def env(x, sr, t0=0.0, t1=2.5):
    a = x[0].astype(np.float64); n = int(WIN * sr)
    return np.array([db(float(np.sqrt(np.mean(a[int(t * sr):int(t * sr) + n] ** 2)))) for t in np.arange(t0, t1, WIN)])
def keyed(R, pg, dev_js):
    """renders the bass through the device keyed from the kick, and the same with a silent kick: the gain change in dB every 2 ms, and the output delay"""
    R("M3.kick.clips=[M3.clip(M3.kickB)];M3.kick.fx=[];M3.bass.fx=[(()=>{%s})()];M3.bass.fx[0].p.sc={src:M3.kick.id,tap:'fx'};changed(true);syncGraph();0" % dev_js)
    dt = J(R, "MX_HOOKS.pdcPlan(48000).T") / 48000
    k = render(pg, 0, 5, None, 48000); R("M3.kick.clips=[];changed(true);0"); b = render(pg, 0, 5, None, 48000); R("M3.kick.clips=[M3.clip(M3.kickB)];changed(true);0")
    return env(b, 48000) - env(k, 48000), dt
def check_gr(name, gr, dt):
    on, off = [], []
    for k in range(4):
        tk = .25 + .5 * k + dt; i0 = int(round((tk - .002) / WIN)); i1 = int(round((tk + .010) / WIN))
        on.append(float(gr[i0:i1 + 1].max())); off.append(float(np.abs(gr[int((tk + .30) / WIN):int((tk + .45) / WIN)]).max()))
    ok(min(on) > 3, '%s keyed from the kick: more than 3 dB less bass within 10 ms of each kick (%s dB)' % (name, ['%.1f' % v for v in on]))
    ok(max(off) < .3, '%s keyed from the kick: under 0.3 dB between the kicks (%s dB)' % (name, ['%.2f' % v for v in off]))
COMP = "const f=mkFx('comp');Object.assign(f.p,{threshold:-40,ratio:10,attack:1,release:50,makeup:0});return f"

with sync_playwright() as p:
    b, pg, logs, R = boot(p)
    v = R("VERSION"); ok(tuple(map(int, v.split('.'))) >= (0, 294), 'version 0.294 or later', v)
    ok(SRC.count('/* ===== task MX-3 (lane K') == 1 and SRC.count('/* ===== task MX-2 (lane K') == 1, 'MX-2 and MX-3 are in, once each')
    # ---- Fractals: the newest backlog references ----
    ids = J(R, "Object.fromEntries(S.tracks.map(t=>[t.name,t.id]))"); R("S.master=-10;changed(true);syncGraph();0")
    for nm, (hh, ref) in {'Kick': ('fb577dd5202b', -19.05560), 'Bass': ('392ec52590c7', -35.48685)}.items():
        x = render(pg, 64, 96, ids[nm], 44100); lv = db(float(np.sqrt(np.mean(x.astype(np.float64) ** 2))))
        ok(abs(lv - ref) < 0.002 and hsh(x) == hh, 'Fractals %s unchanged: %.5f dB %s (reference %.5f %s)' % (nm, lv, hsh(x), ref, hh))
    ok(J(R, "S.tracks.every(t=>(t.fx||[]).every(f=>!f.p||!f.p.sc))"), 'Fractals has no sidechain set (nothing new in old projects)')
    sr_live = J(R, SCENE)

    # ---- X1: every keyable device, keyed from the kick ----
    gr, dt = keyed(R, pg, COMP); check_gr('Compressor', gr, dt)
    ok(J(R, "MX_HOOKS.links().some(l=>l.k==='sc'&&l.a===M3.kick&&l.b===M3.bass&&l.fx.type==='comp'&&l.tap==='fx')"), 'MX_HOOKS.links lists the Compressor\'s key (with its tap point)')
    ok(J(R, "(b=>b&&b.name==='Kick'&&b.tap==='fx')(MX_HOOKS.scBadge(M3.bass,M3.bass.fx[0]))"), 'MX_HOOKS.scBadge gives lane I the source\'s name and colour')
    gr, dt = keyed(R, pg, "const f=mkFx('mband');Object.assign(f.p,{t1:-40,r1:10,a1:1,l1:50,t2:0,r2:1,t3:0,r3:1});return f"); check_gr('Multiband (low band)', gr, dt)
    gr, dt = keyed(R, pg, "const f=mkFx('ott');Object.assign(f.p,{depth:100,down:100,up:0,time:50});return f"); check_gr('OTT', gr, dt)
    # Gate: opens only on kicks
    R("M3.bass.fx=[(()=>{const f=mkFx('gate');Object.assign(f.p,{thr:-30,hyst:4,floor:-60,att:.1,hold:20,rel:30,look:0,hpf:20,lpf:20000,mode:'gate'});f.p.sc={src:M3.kick.id,tap:'fx'};return f})()];changed(true);syncGraph();0")
    x = render(pg, 0, 5, None, 48000); e = env(x, 48000); opn = [float(e[int((.25 + .5 * k + .04) / WIN)]) for k in range(4)]; cls = [float(e[int((.25 + .5 * k + .35) / WIN)]) for k in range(4)]
    ok(min(opn) - max(cls) > 30, 'Gate keyed from the kick: open on the kicks, closed between them (%s / %s dB)' % (['%.1f' % v for v in opn], ['%.1f' % v for v in cls]))
    # the keyed Compressor against the browser's own compressor on a steady tone
    R("M3.bass.fx=[(()=>{const f=mkFx('comp');Object.assign(f.p,{threshold:-30,ratio:4,attack:10,release:200,makeup:0});return f})()];changed(true);syncGraph();0")
    a0 = render(pg, 0, 5, None, 48000); h0 = hsh(a0)
    R("M3.bass.fx[0].p.sc={src:M3.copy.id,tap:'fx'};changed(true);syncGraph();0"); a1 = render(pg, 0, 5, None, 48000)
    w = lambda x: db(float(np.sqrt(np.mean(x[0][int(1.0 * 48000):int(2.0 * 48000)].astype(np.float64) ** 2))))
    ok(abs(w(a0) - w(a1)) < .5, 'keyed from a copy of itself, the Compressor matches the browser\'s compressor on a steady tone within 0.5 dB (%.2f against %.2f dB)' % (w(a1), w(a0)))
    R("mxScSet(M3.bass.fx[0],null);syncGraph();0"); a2 = render(pg, 0, 5, None, 48000)
    ok(hsh(a2) == h0, 'a Compressor without a source renders bit-identically (%s, %s after a source was set and removed)' % (h0, hsh(a2)))
    ok(J(R, "(X=>!X.mxK&&X.k instanceof DynamicsCompressorNode)(NODES.get(M3.bass.id).fxm.get(M3.bass.fx[0].id))"), 'live: the device is the browser\'s compressor again once the source is removed')
    # tap points line up with the plan: a Limiter on the kick, key before or after it (the ducking measured against the same scene with a silent kick)
    R("M3.kick.fx=[(()=>{const f=mkFx('limit');f.p.look=5;return f})()];M3.bass.fx=[(()=>{%s})()];M3.bass.fx[0].p.sc={src:M3.kick.id,tap:'fx'};changed(true);syncGraph();0" % COMP)
    def onset(tap_js):
        R(tap_js + "changed(true);syncGraph();0"); k = env(render(pg, 0, 5, None, 48000), 48000); R("M3.kick.clips=[];changed(true);0"); bb = env(render(pg, 0, 5, None, 48000), 48000); R("M3.kick.clips=[M3.clip(M3.kickB)];changed(true);0")
        g = bb - k; i0 = int(.2 / WIN); dtt = J(R, "MX_HOOKS.pdcPlan(48000).T") / 48000
        return int(np.argmax(g[i0:] > 3)) - int(round(dtt / WIN)), dtt, g
    onA, _, _ = onset("M3.bass.fx[0].p.sc.tap='fx';"); onB, _, _ = onset("M3.bass.fx[0].p.sc.tap='pre';")
    pl = J(R, "MX_HOOKS.pdcPlan(48000).ek.get(M3.bass.fx[0].id)||0")
    ok(onA > 0 and abs(onA - onB) <= 1, 'tap before or after the kick\'s 5 ms Limiter: the ducking starts at the same moment of the song (%d and %d ms after 0.2 s, output delay taken out); the key before it waits %d samples' % (onA * 2, onB * 2, pl))
    onC, _, _ = onset("M3.bass.fx[0].p.sc.tap='dev';M3.bass.fx[0].p.sc.dev=M3.kick.fx[0].id;")
    ok(abs(onA - onC) <= 1, 'tap after one of its devices lines up too (%d ms)' % (onC * 2))
    _, _, gd = onset("M3.bass.fx[0].p.sc={src:M3.kick.id,tap:'fader'};")
    ok(float(np.abs(gd[int(.2 / WIN):]).max()) < .3, 'tap after its fader: the kick, turned all the way down, does not drive it (largest change %.2f dB)' % float(np.abs(gd[int(.2 / WIN):]).max()))
    R("M3.kick.vol=1;changed(true);0"); _, _, ge = onset("")
    ok(float(ge.max()) > 3, 'tap after its fader: with the kick turned up it does (%.1f dB)' % float(ge.max()))
    R("M3.kick.vol=0;M3.kick.fx=[];M3.bass.fx[0].p.sc={src:M3.kick.id,tap:'fx'};changed(true);syncGraph();0")
    # loops are refused
    lp = J(R, "(()=>{M3.bass.out=M3.kick.id;changed(true);const c=mxScCan(M3.bass.fx[0],M3.kick.id),r=MX_HOOKS.scSet(M3.bass.fx[0],M3.kick.id,'fx');delete M3.bass.out;changed(true);return[c.ok,c.why,r.ok]})()")
    ok(lp[0] is False and lp[2] is False and 'loop' in lp[1], 'a key that would make a loop is refused, in plain words', lp[1])
    # export equals playback
    R("M3.bass.fx=[(()=>{%s})()];M3.bass.fx[0].p.sc={src:M3.kick.id,tap:'fx'};changed(true);syncGraph();0" % COMP)
    ex = render(pg, 0, 5, None, sr_live); y = record(pg, R, 2700)
    st = int(np.argmax(np.abs(y[0]) > 1e-3)); s0 = int(np.argmax(np.abs(ex[0]) > 1e-3)); n = min(len(ex[0]) - s0, len(y[0]) - st, int(2.3 * sr_live))
    W = int(.02 * sr_live); E = lambda a: np.array([db(float(np.sqrt(np.mean(a[i:i + W].astype(np.float64) ** 2)))) for i in range(0, n - W, W)])
    ee, le = E(ex[0][s0:]), E(y[0][st:]); m = ee > -50; dd = np.abs(ee[m] - le[m])
    ok(m.sum() > 50 and float(np.median(dd)) < .1, 'export equals playback with a keyed Compressor: median %.3f dB, largest %.2f dB (20 ms windows)' % (float(np.median(dd)), float(dd.max())))
    # the dynamic EQ band listens to the kick (live; the export does not render dynamic EQ movement, as before)
    R(r"""(()=>{const f=mkFx('eq');f.p.bands=f.p.bands||[];const b=f.p.bands[0]||(f.p.bands[0]={});Object.assign(b,{on:true,t:'peaking',f:80,g:0,q:1,dyn:true,dr:-9,th:-30});f.p.sc={src:M3.kick.id,tap:'fx'};M3.bass.fx=[f];M3.kick.clips=[M3.clip(M3.burstB)];changed(true);syncGraph();
      window.__dq=[];const X=NODES.get(M3.bass.id).fxm.get(f.id);ensureCtx();ctx.resume();pos=0;start();const t0=performance.now();const iv=setInterval(()=>{__dq.push([(performance.now()-t0)/1000,X.dyn[0]||0]);if(performance.now()-t0>2200){clearInterval(iv);stop()}},10);return 1})()""")
    pg.wait_for_timeout(2600); dq = J(R, "__dq")
    dmin = min(v for t, v in dq if .55 < t < 1.15); dend = max(abs(v) for t, v in dq if 1.7 < t < 2.1)
    ok(dmin < -3 and dend < .3, 'a dynamic EQ band keyed from the kick dips only while the kick plays (%.1f dB during, %.2f dB after)' % (dmin, dend))
    R("M3.kick.clips=[M3.clip(M3.kickB)];changed(true);0")

    # ---- X4: duck under the kick, tuned for tails ----
    co = J(R, "abxOpts(M3.kick,M3.ret).map(i=>i&&i.t||'')")
    ok(any('Duck under Kick, tuned for tails' in t for t in co), 'a cable drawn from the kick to a return offers Duck under the kick, tuned for tails', [t for t in co if 'tails' in t])
    f4 = J(R, "(()=>{const f=MX_HOOKS.duckTails(M3.ret);return f&&[f.type,f.p.src===M3.kick.id,f.p.at,f.p.hd,f.p.rl,M3.ret.fx.indexOf(f)===M3.ret.fx.length-1]})()")
    ok(f4 == ['duck', True, .5, 0, 125, True], 'Duck under the kick puts a Ducker last on the return, keyed from Kick: attack 0.5 ms, no hold, back in a 16th (125 ms at 120 BPM)', f4)
    R("S.bpm=140;changed(true);syncGraph();0"); ok(J(R, "M3.ret.fx.find(f=>f.p.mxTail).p.rl") == 107, 'the tails Ducker follows a tempo change (107 ms at 140 BPM)')
    ok(J(R, "MX_HOOKS.links().some(l=>l.k==='sc'&&l.a===M3.kick&&l.b===M3.ret)"), 'its cable is in the links (drawn from the kick to the return)')
    R("S.bpm=120;selT=M3.ret.id;renderFx();0"); pg.wait_for_timeout(200)
    bt = J(R, "(()=>{const b=document.querySelector('#fxin .tdev2 .mxtail');return b?[b.textContent,b.classList.contains('on'),b.title]:null})()")
    ok(bt and bt[1] and 'Kick' in bt[0] and '16th' in bt[2], 'the return\'s first device shows the switch, on, with a tooltip', bt and bt[0])
    pg.click('#fxin .tdev2 .mxtail'); pg.wait_for_timeout(150); ok(J(R, "!M3.ret.fx.some(f=>f.p&&f.p.mxTail)"), 'clicking the switch turns it off (the Ducker goes)')
    pg.click('#fxin .tdev2 .mxtail'); pg.wait_for_timeout(150); ok(J(R, "M3.ret.fx.some(f=>f.p&&f.p.mxTail&&f.p.src===M3.kick.id)"), 'clicking again puts it back, keyed from Kick')
    ok(J(R, "(()=>{mxOutMenu(M3.ret,200,200);const r=MENU.some(i=>i&&i.label&&/Duck under Kick, tuned for tails/.test(i.label)&&i.check);closeMenu();return r})()"), 'the Output menu of the return\'s mixer strip offers the same switch (checked)')
    R("M3.bass.fx=[(()=>{%s})()];changed(true);0" % COMP); co2 = J(R, "abxOpts(M3.kick,M3.bass).map(i=>i&&i.t||'')")
    ok(any('Compressor on Bass listens to Kick' in t for t in co2) and any('tuned for tails' in t for t in co2), 'a cable to a track with a Compressor offers its sidechain and the tails Ducker', [t for t in co2 if 'listens' in t or 'tails' in t])

    # ---- the Sidechain row in each keyable device ----
    R("M3.bass.fx=['comp','gate','mband','ott','eq'].map(t=>mkFx(t));M3.bass.fx[0].p.sc={src:M3.kick.id,tap:'fx'};selT=M3.bass.id;changed(true);renderFx();0"); pg.wait_for_timeout(300)
    rows = J(R, "[...document.querySelectorAll('#fxin .mxscb')].map(b=>[b.textContent,b.title])")
    ok(len(rows) == 5 and 'Kick' in rows[0][0] and all('Own sound' in r[0] for r in rows[1:]), 'a Sidechain row on Compressor, Gate, Multiband, OTT and EQ (the first shows Kick)', [r[0] for r in rows])
    ok(all(r[1] and '—' not in r[1] and '—' not in r[0] for r in rows), 'every row has a tooltip in plain words, no em dashes', rows[0][1])
    el = pg.query_selector('#fxin .mxscb'); el.scroll_into_view_if_needed(); el.click(); pg.wait_for_timeout(200)
    mn = J(R, "MENU.map(i=>i&&(i.label||i.head)||'')"); kids = J(R, "(MENU.find(i=>i&&i.label==='Kick')||{}).kids||[]")
    kl = [k['label'] for k in kids if isinstance(k, dict)] if kids else []
    ok('Its own sound' in mn and 'Kick' in mn and 'Bass' not in mn, 'the menu offers Its own sound and the other tracks (not its own)', mn)
    ok(kl[:3] == ['After its effects', 'After its fader', 'Before its effects'], 'each track offers its tap points', kl)
    dev = pg.query_selector('#fxin .dev[data-id="%s"]' % J(R, "M3.bass.fx[0].id"))
    R("closeMenu();0")
    if dev: dev.screenshot(path=os.path.join(OUT, 'mx3_row_dark.png'))
    cd = J(R, "getComputedStyle(document.querySelector('#fxin .mxscb')).color")
    R("(()=>{const e=document.getElementById('setBg');if(e){e.value=100;e.dispatchEvent(new Event('input',{bubbles:true}))}return 1})()"); pg.wait_for_timeout(400)
    if dev: dev.screenshot(path=os.path.join(OUT, 'mx3_row_light.png'))
    cl = J(R, "getComputedStyle(document.querySelector('#fxin .mxscb')).color")
    R("(()=>{const e=document.getElementById('setBg');if(e){e.value=40;e.dispatchEvent(new Event('input',{bubbles:true}))}return 1})()")
    ok(cd and cl, 'the row is drawn in Dark and Light (%s / %s)' % (cd, cl))
    blk = SRC[SRC.index('/* ===== task MX-3 (lane K'):SRC.index('function askChoice(title,text,btns,icon){')]
    ok('setInterval(' not in blk and 'requestAnimationFrame(' not in blk and 'setTimeout(' not in blk, 'no new per-frame or timed work (keys are wired on changes only)')
    ok(len(logs) == 0, 'no console errors', logs[:5])
    b.close()
print('%d checks, %d failed' % (N[0], len(FAIL)))
for f in FAIL: print('  FAILED:', f)
sys.exit(1 if FAIL else 0)
