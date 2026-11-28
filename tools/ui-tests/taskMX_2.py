#!/usr/bin/env python3
"""Task MX-2 (lane K, mixing engine): X5 delay compensation for every path, X6 latency you can see, device automation in exports.
An impulse on a reference track (left) and the same impulse through one path at a time (right): through a group with a look-ahead Limiter,
a post and a pre send from a latent track into a return with a Limiter, an output into a track with a Limiter (with and without clips of its own),
a Ducker trigger from a latent kick and a Ducker after a latent device: the two arrive on the same sample, in export (48 kHz) and live (the app's
sample rate). Delay compensation off still turns it all off. A latency change while playing fades instead of clicking. Lane J's played-track hook
(LT_HOOKS.pdcLive) still keeps a played track out of compensation. Device automation (a filter sweep) and volume automation now render in the export
as they play. The read-out in the track's first device (only with latency, tooltip, Dark and Light). Fractals: Kick and Bass unchanged.
   python3 tools/ui-tests/taskMX_2.py [index.html] [out dir]"""
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

# the impulses: every half second from 0.25 s, 0.1 high; the reference track plays them on the left
IMP = r"""(()=>{ensureCtx();S.bpm=120;const sr=ctx.sampleRate,len=Math.round(4*.5*sr),mk=()=>{const b=ctx.createBuffer(2,len,sr);for(let c=0;c<2;c++){const d=b.getChannelData(c);for(let k=0;k<4;k++)d[Math.round((.25+.5*k)*sr)]=.1}return addBuf(b)};
 const clip=id=>mkClip({start:0,len:4,name:'Imp',buf:id,dur:len/sr,gain:0,fi:0,fo:0}),B=mk();
 const tr=(n,c)=>{const t=mkTrack('audio',null,n,c);t.vol=1;t.pan=0;return t},bus=(kind,name,color)=>({id:rid(),kind,name,color,vol:1,pan:1,mute:false,solo:false,fx:[],clips:[]});
 const lim=ms=>{const f=mkFx('limit');f.p.look=ms;return f};
 const ref=tr('Ref','#fff');ref.pan=-1;ref.clips.push(clip(B));
 const src=tr('Src','#ffd166');src.clips.push(clip(B));
 const grp=bus('group','Glue','#9be38a');grp.fx=[lim(5)];
 const ret=bus('return','Verb bus','#7fd0ff');ret.fx=[lim(2)];
 const sink=tr('Resample','#c39bff');sink.pan=1;sink.fx=[lim(3)];
 const dead=tr('Nowhere','#555');dead.mute=true;
 const kick=tr('Kick','#ff6b6b');kick.clips.push(clip(B));kick.vol=0;
 const pad=tr('Pad','#4cc9f0');pad.pan=1;const dk=mkFx('duck');Object.assign(dk.p,{src:kick.id,ls:true,la:0,fo:'all'});pad.fx=[dk];
 S.tracks=[ref,src,grp,ret,sink,dead,kick,pad];S.mfx=[];S.master=0;S.loop=false;window.MXT={ref,src,grp,ret,sink,dead,kick,pad,dk,B,clip,lim};changed(true);syncGraph();return ctx.sampleRate})()"""
# one path at a time: everything off but the reference and that path
SETUP = {
 'group': "MXT.src.grp=MXT.grp.id;MXT.grp.mute=false;",
 'post send': "MXT.src.fx=[(()=>{const f=mkFx('clip');f.p.os='2x';return f})()];MXT.src.out=MXT.dead.id;MXT.src.sends={[MXT.ret.id]:1};MXT.ret.mute=false;",
 'pre send': "MXT.src.fx=[(()=>{const f=mkFx('clip');f.p.os='2x';return f})()];MXT.src.out=MXT.dead.id;MXT.src.sends={[MXT.ret.id]:1};MXT.src.sendPre={[MXT.ret.id]:true};MXT.src.vol=.25;MXT.ret.mute=false;",
 'output into a track': "MXT.src.out=MXT.sink.id;MXT.sink.mute=false;",
 'output into a track with clips': "MXT.src.out=MXT.sink.id;MXT.sink.mute=false;MXT.sink.clips=[MXT.clip(MXT.B)];",
 'trigger from a late kick': "MXT.kick.fx=[MXT.lim(4)];MXT.pad.mute=false;",
 'trigger into a late Ducker': "MXT.pad.fx=[MXT.lim(5),MXT.dk];MXT.pad.mute=false;",
}
RESET = r"""(()=>{const X=MXT;delete X.src.grp;delete X.src.out;delete X.src.sendPre;X.src.sends={};X.src.fx=[];X.src.vol=1;X.src.mute=false;X.sink.clips=[];X.kick.fx=[];X.pad.fx=[X.dk];
 for(const k of['grp','ret','sink','pad'])X[k].mute=true;X.ref.mute=false;X.kick.mute=false;X.dead.mute=true;return 1})()"""
def pick(x, sr, n=4):
    """peak index of each impulse on the left and on the right, as offsets from the first left one"""
    out = []
    for c in range(2):
        a = np.abs(x[c]); idx = []
        for k in range(n):
            lo = int((.25 + .5 * k - .2) * sr); hi = int((.25 + .5 * k + .2) * sr)
            if hi > len(a): break
            seg = a[lo:hi]; idx.append(lo + int(np.argmax(seg)) if seg.max() > 1e-4 else None)
        out.append(idx)
    return out

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
def live_pairs(x, thr=5e-3):
    """live: find every impulse on the left, and the right one nearest to it; returns the differences in samples"""
    L, Rr = np.abs(x[0]), np.abs(x[1]); d = []; i = 0; n = len(L)
    while i < n:
        if L[i] > thr:
            j0 = i; seg = L[j0:j0 + 64]; li = j0 + int(np.argmax(seg))
            w = Rr[max(0, li - 2000):li + 2000]
            if w.max() > thr: d.append(max(0, li - 2000) + int(np.argmax(w)) - li)
            i = j0 + 4000
        else: i += 1
    return d

with sync_playwright() as p:
    b, pg, logs, R = boot(p)
    v = R("VERSION"); ok(tuple(map(int, v.split('.'))) >= (0, 294), 'version 0.294 or later (MX-1 in)', v)
    # ---- Fractals first: the newest backlog references (Kick, Bass at master -10 dB; single-track renders have no compensation) ----
    fr = J(R, "S.tracks.map(t=>t.name)"); ok('Kick' in fr and 'Bass' in fr, 'Fractals open', fr[:5])
    ids = J(R, "Object.fromEntries(S.tracks.map(t=>[t.name,t.id]))")
    R("S.master=-10;changed(true);syncGraph();0")
    REFS = {'Kick': ('fb577dd5202b', -19.05560), 'Bass': ('392ec52590c7', -35.48685)}
    for nm in ('Kick', 'Bass'):
        x = render(pg, 64, 96, ids[nm], 44100); lv = db(float(np.sqrt(np.mean(x.astype(np.float64) ** 2))))
        print('Fractals %s %.5f dB %s (reference %s, %.5f)' % (nm, lv, hsh(x), REFS[nm][0], REFS[nm][1]))
        ok(abs(lv - REFS[nm][1]) < 0.002, 'Fractals %s level unchanged: %.5f dB (reference %.5f)' % (nm, lv, REFS[nm][1]))
    plan = J(R, "(()=>{const X=MX_HOOKS.pdcPlan(48000),n=id=>trkById(id).name;return{T:X.T,d:[...X.d].filter(e=>e[1]>0).map(e=>[n(e[0]),e[1]]),eo:[...X.eo].map(e=>[n(e[0]),e[1]]),es:[...X.es].map(e=>[e[0].split('>').map(n).join(' > '),e[1]]),ek:[...X.ek].length,c:[...X.c].length,crit:X.crit&&[X.crit.t.name,X.crit.dev&&X.crit.dev.f.type]}})()")
    print('Fractals plan at 48 kHz:', json.dumps(plan))
    ok(plan['T'] == 288 and ['Kick', 288] not in plan['d'], 'Fractals: target 288 samples (the groups\' Compressors), tracks delayed as before', plan['T'])
    ok(len(plan['es']) == 3 and all(e[1] == 288 for e in plan['es']), 'Fractals: the three sends from the Drums group now wait for its Compressor (288 samples) so the reverb is in time with the dry sound', plan['es'])
    full = render(pg, 64, 72, None, 44100); print('Fractals full mix beats 64 to 72 at -10 dB: %.5f dB %s (changes on purpose: the sends to Plate reverb are now in time)' % (db(float(np.sqrt(np.mean(full.astype(np.float64) ** 2)))), hsh(full)))
    ok(J(R, "pdcMap(48000).target===288&&(pdcMap(48000).get(S.tracks.find(t=>t.name==='Kick').id)||0)===0&&pdcMap(48000).get(S.tracks.find(t=>t.name==='Lead').id)===288"), 'pdcMap keeps its result for tracks (Kick in its compressed group 0, Lead 288)')
    ok(J(R, "['lat','devLat','pathLat','pdcPlan'].every(k=>typeof MX_HOOKS[k]==='function')&&MX_HOOKS.pathLat().smp>0&&MX_HOOKS.links().every(l=>typeof l.lat==='number')"), 'MX_HOOKS offers lat, devLat, pathLat, pdcPlan; links() carry their delay')

    # ---- impulse alignment: every path, export and live ----
    sr_live = J(R, IMP); R(RESET)
    for name, js in SETUP.items():
        R(RESET); R(js + "changed(true);syncGraph();0")
        x = render(pg, 0, 4, None, 48000); P = pick(x, 48000)
        ex = [r - l if (l is not None and r is not None) else None for l, r in zip(P[0], P[1])]
        lat = J(R, "MX_HOOKS.pdcPlan(48000).T")
        ok(len(ex) == 4 and all(e == 0 for e in ex), 'export: %s arrives on the same sample as the reference (offsets %s, target %d samples)' % (name, ex, lat))
        if name == 'output into a track with clips':
            amp = float(np.abs(x[1]).max()); one = float(np.abs(x[0]).max())
            ok(amp > 1.7 * one, 'export: the track\'s own clips and what it receives line up (right peak %.3f, one impulse %.3f)' % (amp, one))
        y = record(pg, R, 2300); dl = live_pairs(y)
        ok(len(dl) >= 3 and all(d == 0 for d in dl), 'live (%d Hz): %s arrives on the same sample (offsets %s)' % (sr_live, name, dl))
    # the plan's delays are on links only where needed
    R(RESET); R(SETUP['post send'] + "changed(true);syncGraph();0")
    pl = J(R, "(()=>{const X=MX_HOOKS.pdcPlan(48000);return[X.T,X.eo.get(MXT.src.id)||0,[...X.es.values()],X.d.get(MXT.src.id)||0,X.d.get(MXT.ref.id)||0]})()")
    ok(pl == [224, 96, [], 0, 224], 'post send: the longest path is the send (128 + 96 samples); the track\'s direct output waits 96 samples for the return, the reference waits 224 (target, output, sends, delays)', pl)
    ok(J(R, "!NODES.get(MXT.ref.id).mxOE"), 'the reference track (no extra link delay needed) got no extra delay node')
    # compensation off
    R("UI.pdc=false;changed(true);syncGraph();0"); x = render(pg, 0, 4, None, 48000); P = pick(x, 48000)
    off = [r - l for l, r in zip(P[0], P[1]) if l is not None and r is not None]
    ok(off and all(o == 128 + 96 for o in off), 'Delay compensation off: no delays, the send path is late by its devices (%s samples)' % off)
    R("delete UI.pdc;changed(true);syncGraph();0")

    # ---- latency change while playing: a fade, no click ----
    R(RESET); R(r"""(()=>{const sr=ctx.sampleRate,len=Math.round(8*.5*sr),b=ctx.createBuffer(2,len,sr);for(let c=0;c<2;c++){const d=b.getChannelData(c);for(let i=0;i<len;i++)d[i]=.25*Math.sin(2*Math.PI*441*i/sr)}
     const id=addBuf(b);MXT.ref.clips=[mkClip({start:0,len:8,name:'Tone',buf:id,dur:b.duration,gain:0,fi:0,fo:0})];MXT.ref.pan=0;MXT.kick.mute=true;MXT.src.mute=true;MXT.sink.mute=true;MXT.sink.fx=[MXT.lim(1)];changed(true);syncGraph();return 1})()""")
    y = record(pg, R, 900, "MXT.sink.fx[0].p.look=8;changed(true);", 900)
    m = y[0][int(.15 * sr_live):-int(.25 * sr_live)]; d2 = np.abs(np.diff(m.astype(np.float64), 2)); steady = .25 * (2 * np.pi * 441 / sr_live) ** 2
    ok(len(m) > sr_live and d2.max() < 3 * steady, 'a look-ahead turned up while playing re-aligns the other tracks with a fade: no click (largest step %.5f, a clean tone %.5f)' % (d2.max(), steady))
    ok(J(R, "!!NODES.get(MXT.ref.id).mxF"), 'the fade node went in on the moved track (only after a change while playing)')
    R("MXT.ref.clips=[MXT.clip(MXT.B)];MXT.ref.pan=-1;MXT.sink.fx=[MXT.lim(3)];changed(true);syncGraph();0")

    # ---- lane J's played track stays out of compensation ----
    R(RESET); R(SETUP['group'] + "changed(true);syncGraph();0")
    a = J(R, "(()=>{const sr=48000,before=pdcMap(sr,true).get(MXT.ref.id)||0;window.LT_HOOKS=window.LT_HOOKS||{};const had=LT_HOOKS.pdcLive;LT_HOOKS.pdcLive=()=>[MXT.ref.id];const M=pdcMap(sr,true),r=[before,M.get(MXT.ref.id)||0,M.target];if(had)LT_HOOKS.pdcLive=had;else delete LT_HOOKS.pdcLive;pdcMap(sr,true);return r})()")
    ok(a[0] == 240 and a[1] == 0 and a[2] == 240, 'LT_HOOKS.pdcLive: the played track gets no delay while the others stay compensated (before %d, played %d, target %d)' % tuple(a))
    ok(J(R, "pdcMap(48000).get(MXT.ref.id)===240"), 'the export plan (no live flag) still compensates that track')

    # ---- device automation in export (the S.pauto bug) ----
    R(RESET); R(r"""(()=>{const sr=ctx.sampleRate,len=Math.round(8*.5*sr),b=ctx.createBuffer(2,len,sr);for(let c=0;c<2;c++){const d=b.getChannelData(c);for(let i=0;i<len;i++)d[i]=.25*Math.sin(2*Math.PI*2000*i/sr)}
     const id=addBuf(b);const t=MXT.src;t.clips=[mkClip({start:0,len:8,name:'Tone',buf:id,dur:b.duration,gain:0,fi:0,fo:0})];const f=mkFx('filter');f.p.freq=18000;f.p.q=1;t.fx=[f];MXT.ref.mute=true;MXT.kick.mute=true;
     S.pauto={['f:'+t.id+':'+f.id+':freq']:[{b:0,v:.95},{b:8,v:.25}],['t:'+t.id+':vol']:[{b:0,v:SPEC_VOL.n(1)},{b:4,v:SPEC_VOL.n(1)},{b:8,v:SPEC_VOL.n(.5)}]};MXT.af=f;changed(true);syncGraph();return 1})()""")
    x = render(pg, 0, 8, None, 48000)
    win = lambda a, sr, t0: float(np.sqrt(np.mean(a[int(t0 * sr):int((t0 + .1) * sr)].astype(np.float64) ** 2)))
    e_lv = [db(win(x[0], 48000, t)) for t in (.2, 1.0, 2.0, 3.0, 3.8)]
    ok(e_lv[0] - e_lv[-1] > 12, 'export: the automated filter sweep and the volume ramp are rendered (level %s dB at 0.2, 1, 2, 3 and 3.8 s)' % ['%.1f' % v for v in e_lv])
    y = record(pg, R, 4200); st = int(np.argmax(np.abs(y[0]) > 1e-3))
    # live applies automation from the main thread every 33 ms, so it follows a little later: find that lag, then compare
    env = lambda a, sr: np.array([db(float(np.sqrt(np.mean(a[int(t * sr):int((t + .02) * sr)].astype(np.float64) ** 2)))) for t in np.arange(.1, 3.85, .01)])
    ee = env(x[0], 48000); best = None
    for lag in range(0, 16):
        le = env(y[0][st + int(lag * .01 * sr_live):], sr_live); n = min(len(ee), len(le)); m = ee[:n] > -60
        err = float(np.median(np.abs(ee[:n][m] - le[:n][m]))); best = min(best, (err, lag)) if best else (err, lag)
    ok(best[0] < 0.5 and best[1] <= 12, 'playback follows the same automation: within %.2f dB (median of 10 ms windows) when live is taken %d ms later (live sets it from the screen every 33 ms and smooths it)' % (best[0], best[1] * 10))
    R("S.pauto={};changed(true);0")
    x2 = render(pg, 0, 8, None, 48000); ok(abs(db(win(x2[0], 48000, 3.8)) - db(win(x2[0], 48000, .2))) < .5, 'without automation the filter stays where it is set (no stray change)')
    R("MXT.af.p.freq=18000;changed(true);0")

    # ---- X6: the read-out in the track's first device ----
    R(RESET); R("selT=MXT.sink.id;renderFx();0"); pg.wait_for_timeout(300)
    ro = J(R, "(()=>{const o=document.querySelector('#fxin .tdev2 .mxlat');return o?[o.textContent,o.title]:null})()")
    exp_ms = '%.1f' % (J(R, "fxLat(MXT.sink.fx[0],ctx.sampleRate)") / sr_live * 1000)
    ok(ro and ro[0].startswith(exp_ms) and 'ms' in ro[0], 'a track with a Limiter shows its latency next to its name (%s)' % (ro and ro[0]))
    ok(ro and 'delay its sound by' in ro[1] and 'Longest path in the song' in ro[1] and '—' not in ro[1], 'its tooltip says what it means, in plain words, with the longest path', ro and ro[1])
    R("selT=MXT.ref.id;renderFx();0"); pg.wait_for_timeout(200)
    ok(J(R, "!document.querySelector('#fxin .tdev2 .mxlat')"), 'a track without latency shows nothing')
    R("selT=MXT.sink.id;renderFx();0"); pg.wait_for_timeout(200)
    R("MXT.sink.fx[0].p.look=6;changed(true);syncGraph();0")
    ok(J(R, "document.querySelector('#fxin .tdev2 .mxlat').textContent.startsWith((fxLat(MXT.sink.fx[0],ctx.sampleRate)/ctx.sampleRate*1000).toFixed(1))"), 'the read-out follows a latency change without a redraw of the devices')
    el = pg.query_selector('#fxin .tdev2')
    if el: el.screenshot(path=os.path.join(OUT, 'mx2_readout_dark.png'))
    col_d = J(R, "getComputedStyle(document.querySelector('#fxin .tdev2 .mxlat')).color")
    R("(()=>{const e=document.getElementById('setBg');if(e){e.value=100;e.dispatchEvent(new Event('input',{bubbles:true}))}return 1})()"); pg.wait_for_timeout(400)
    if el: el.screenshot(path=os.path.join(OUT, 'mx2_readout_light.png'))
    col_l = J(R, "getComputedStyle(document.querySelector('#fxin .tdev2 .mxlat')).color")
    ok(col_d and col_l, 'read-out drawn in Dark and Light (%s / %s)' % (col_d, col_l))
    R("(()=>{const e=document.getElementById('setBg');if(e){e.value=40;e.dispatchEvent(new Event('input',{bubbles:true}))}return 1})()")
    R("UI.pdc=false;syncGraph();0"); ok(J(R, "document.querySelector('#fxin .tdev2 .mxlat').title.includes('compensation is off')"), 'with compensation off the tooltip says the track plays late'); R("delete UI.pdc;syncGraph();0")
    # nothing new runs while idle
    ok(SRC.count('setInterval(mx') == 0 and 'requestAnimationFrame(mxLat' not in SRC, 'no new per-frame or timed work (the read-out updates on changes only)')
    ok(len(logs) == 0, 'no console errors', logs[:5])
    b.close()
print('%d checks, %d failed' % (N[0], len(FAIL)))
for f in FAIL: print('  FAILED:', f)
sys.exit(1 if FAIL else 0)
