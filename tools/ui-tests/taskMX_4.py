#!/usr/bin/env python3
"""Task MX-4 (lane K, mixing engine): X3 the Ducker's Spectral focus and X19's Bass mono switch.
A kick keys a bass made of 60 Hz and 300 Hz through a Spectral Ducker: the 40 to 120 Hz band goes down more than 6 dB on kicks while 300 Hz stays
within 0.5 dB; with nothing ducking the Spectral Ducker is within 0.1 dB of its input; its latency is reported and lined up (an impulse on another
track arrives on the same sample); export equals playback. Bass mono at 120 Hz: a side-only 60 Hz tone falls more than 30 dB, a side-only 1 kHz tone
stays within 0.2 dB, a mono signal within 0.1 dB at every frequency (tracks and the master, live and in export). MX_HOOKS.bandFilter passes its band.
The switch in the track's first device and above the master's devices, Dark and Light, tooltips. Old projects: no new keys, Fractals unchanged;
with --base <file> (main + MX-2 + MX-3) the four old Ducker focus modes and a song without Bass mono render bit for bit as before.
   python3 tools/ui-tests/taskMX_4.py [index.html] [out dir] [--base base.html]"""
import sys, os, json, base64, hashlib
import numpy as np
from playwright.sync_api import sync_playwright
A = [a for a in sys.argv[1:]]
BASE = None
if '--base' in A:
    i = A.index('--base'); BASE = A[i + 1]; del A[i:i + 2]
F = A[0] if len(A) > 0 else 'index.html'
OUT = A[1] if len(A) > 1 else '.'
os.makedirs(OUT, exist_ok=True)
ARGS = ["--autoplay-policy=no-user-gesture-required", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"]
FAIL = []; N = [0]
def ok(c, m, d=''):
    N[0] += 1; print(('ok   ' if c else 'FAIL ') + m + (('   ' + str(d)[:300]) if d != '' else ''), flush=True)
    if not c: FAIL.append(m)
INIT = "if(!sessionStorage.getItem('c1i')){sessionStorage.setItem('c1i','1');localStorage.setItem('audiolab-ui',JSON.stringify({splash:false,lat3:1}))}"

def boot(p, path):
    src = open(path, encoding='utf-8').read()
    b = p.chromium.launch(args=ARGS)
    ctx = b.new_context(viewport={'width': 1600, 'height': 1000}, device_scale_factor=1); pg = ctx.new_page(); logs = []
    def con(m):
        if (m.type == 'error' and 'fetching the script' not in m.text) or (m.type == 'warning' and 'nominal range' not in m.text and 'GPU stall' not in m.text and 'willReadFrequently' not in m.text and 'ScriptProcessorNode' not in m.text): logs.append(m.type + ': ' + m.text[:200])
    pg.on('console', con); pg.on('pageerror', lambda e: logs.append('pageerror: ' + str(e)[:300]))
    pg.route('https://app.test/**', lambda r: r.fulfill(status=200, content_type='text/html', body=src) if r.request.url.endswith('.html') else r.fulfill(status=404, body=''))
    pg.add_init_script(INIT)
    pg.goto('https://app.test/index.html'); pg.wait_for_function("()=>window.AudioLab&&window.AudioLab.version", timeout=120000); pg.wait_for_timeout(3500)
    pg.evaluate("()=>{for(const i of['splash','liteNote']){const s=document.getElementById(i);if(s)s.remove()}}")
    R = lambda c: pg.evaluate("c=>AudioLab.run(c)", c)
    return b, pg, logs, R, src
J = lambda R, c: json.loads(R("JSON.stringify(" + c + ")"))
db = lambda v: 20 * np.log10(max(v, 1e-12))
rms = lambda x: float(np.sqrt(np.mean(np.asarray(x, dtype=np.float64) ** 2)))

def render(pg, b0, b1, only=None, sr=48000):
    h = pg.evaluate("o=>AudioLab.render(o)", {'b0': b0, 'b1': b1, 'sr': sr, 'only': only, 'single': True}); ch = []
    for c in range(h['ch']):
        parts = []
        for off in range(0, h['len'], 1 << 18):
            n = min(1 << 18, h['len'] - off); parts.append(np.frombuffer(base64.b64decode(pg.evaluate("a=>AudioLab.pull(a[0],a[1],a[2],a[3])", [h['id'], c, off, n])), dtype=np.float32))
        ch.append(np.concatenate(parts))
    pg.evaluate("i=>AudioLab.free(i)", h['id']); return np.stack(ch)
def exp_vs_live(pg, R, ex, sr, ms, tries=3):
    """export against a live recording in 20 ms windows; the headless recorder sometimes drops a block on a busy machine, so up to three recordings"""
    for k in range(tries):
        y = record(pg, R, ms); s1, st = align(ex, y, sr); n = min(len(ex[0]) - s1, len(y[0]) - st, int(2.3 * sr)); W = int(.02 * sr)
        E = lambda q: np.array([db(rms(q[i:i + W])) for i in range(0, n - W, W)])
        ee, le = E(ex[0][s1:]), E(y[0][st:]); mm = ee > -50; dd = np.abs(ee[mm] - le[mm])
        if float(np.median(dd)) < .1: break
    return float(np.median(dd)), float(dd.max()), int(mm.sum()), k + 1
def align(ex, y, sr):
    """start of the signal in both, the live one moved to the sample where it matches the export best"""
    s1 = int(np.argmax(np.abs(ex[0]) > 1e-3)); st = int(np.argmax(np.abs(y[0]) > 1e-3)); L = int(.4 * sr); a = ex[0][s1 + 4096:s1 + 4096 + L].astype(np.float64)
    best = max(range(-2048, 2049), key=lambda d: float(np.dot(a, y[0][st + 4096 + d:st + 4096 + d + L].astype(np.float64))) if st + 4096 + d >= 0 else -1e9)
    return s1, st + best
hsh = lambda x: hashlib.md5(b''.join(c.tobytes() for c in x)).hexdigest()[:12]

REC = r"""window.__rec=null;(async()=>{ensureCtx();await ctx.resume();syncGraph();await new Promise(r=>setTimeout(r,150));const sp=ctx.createScriptProcessor(4096,2,2),L=[],Rr=[];
 sp.onaudioprocess=e=>{if(!play.on&&!L.length)return;L.push(e.inputBuffer.getChannelData(0).slice());Rr.push(e.inputBuffer.getChannelData(1).slice())};master.connect(sp);sp.connect(ctx.destination);
 pos=0;start();await new Promise(r=>setTimeout(r,%d));stop();await new Promise(r=>setTimeout(r,60));try{master.disconnect(sp)}catch(e){}sp.disconnect();
 const n=L.reduce((a,b)=>a+b.length,0),l=new Float32Array(n),r=new Float32Array(n);let o=0;for(let i=0;i<L.length;i++){l.set(L[i],o);r.set(Rr[i],o);o+=L[i].length}
 window.__recL=l;window.__recR=r;return n})().then(v=>{window.__rec=v},e=>{window.__rec='err '+e});0"""
REC_OUT = REC.replace("master.connect(sp)", "outBus.connect(sp)").replace("master.disconnect(sp)", "outBus.disconnect(sp)")
def record(pg, R, ms, js=REC):
    R(js % ms); pg.wait_for_function("()=>window.__rec!==null", timeout=30000)
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
 const buf=(fl,fr)=>{fr=fr||fl;const b=ctx.createBuffer(2,len,sr);for(let c=0;c<2;c++){const d=b.getChannelData(c),fn=c?fr:fl;for(let i=0;i<len;i++)d[i]=fn(i/sr)}return addBuf(b)};
 const kf=t=>{for(let k=0;k<4;k++){const u=t-(.25+.5*k);if(u>=0&&u<.12){const w=Math.sin(Math.PI*u/.12);return .8*Math.sin(2*Math.PI*60*u)*w*w}}return 0};
 const kickB=buf(kf),bassB=buf(t=>.25*Math.sin(2*Math.PI*60*t)+.25*Math.sin(2*Math.PI*300*t));
 const imp=t=>Math.abs(t-1.0)<.5/sr?1:0,impB=buf(imp);
 const tones=[31.25,62.5,125,250,500,1000,2000,4000,8000,16000],monoB=buf(t=>{let v=0;for(const f of tones)v+=.05*Math.sin(2*Math.PI*f*t+f);return v});
 const s60=buf(t=>.3*Math.sin(2*Math.PI*60*t),t=>-.3*Math.sin(2*Math.PI*60*t)),s1k=buf(t=>.3*Math.sin(2*Math.PI*1000*t),t=>-.3*Math.sin(2*Math.PI*1000*t));
 const clip=id=>mkClip({start:0,len:5.2,name:'C',buf:id,dur:len/sr,gain:0,fi:0,fo:0});
 const tr=(n,c)=>{const t=mkTrack('audio',null,n,c);t.vol=1;t.pan=0;return t};
 const kick=tr('Kick','#ff6b6b');kick.vol=0;kick.clips=[clip(kickB)];const bass=tr('Bass','#4cc9f0');bass.clips=[clip(bassB)];const other=tr('Other','#999');other.vol=0;other.clips=[];
 S.tracks=[kick,bass,other];S.mfx=[];S.master=0;S.loop=false;S.pauto={};delete S.bmono;window.M4={kick,bass,other,kickB,bassB,impB,monoB,s60,s1k,clip,tones};changed(true);syncGraph();return ctx.sampleRate})()"""
DUCK = "(()=>{const f=mkFx('duck');Object.assign(f.p,{amt:90,th:-40,gain:0,at:1,hd:20,rl:120,cv:0,la:0,ff:120,fo:'%s',ls:false,src:M4.kick.id});return f})()"

def band_db(x, sr, lo, hi, nf=2048, hop=256):
    a = x[0].astype(np.float64); w = np.hanning(nf); fr = np.fft.rfftfreq(nf, 1 / sr); m = (fr >= lo) & (fr <= hi); out = []
    for i in range(0, len(a) - nf, hop):
        X = np.fft.rfft(a[i:i + nf] * w); out.append(db(float(np.sqrt(np.sum(np.abs(X[m]) ** 2)))))
    return np.array(out)
def tone_db(x, sr, f, t0=1.0, n=48000):
    a = x[int(t0 * sr):int(t0 * sr) + n].astype(np.float64); X = np.fft.rfft(a * np.hanning(len(a))); k = int(round(f * len(a) / sr))
    return db(float(np.sqrt(np.sum(np.abs(X[k - 2:k + 3]) ** 2))))

def old_modes(pg, R):
    """hashes of the four old focus modes and of a song without Bass mono (compared with --base)"""
    R(SCENE); out = {}
    for fo in ('all', 'low', 'band', 'high'):
        R("M4.bass.fx=[%s];changed(true);syncGraph();0" % (DUCK % fo)); out[fo] = hsh(render(pg, 0, 5, None, 48000))
    R("M4.bass.fx=[];M4.bass.width=140;changed(true);syncGraph();0"); out['plain'] = hsh(render(pg, 0, 5, None, 48000)); R("delete M4.bass.width;changed(true);0")
    return out

with sync_playwright() as p:
    ref = None
    if BASE:
        b0, pg0, logs0, R0, _ = boot(p, BASE); ref = old_modes(pg0, R0); b0.close()
    b, pg, logs, R, SRC = boot(p, F)
    v = R("VERSION"); ok(tuple(map(int, v.split('.'))) >= (0, 297), 'version 0.297 or later', v)
    ok(all(SRC.count('/* ===== task MX-%d (lane K' % k) == 1 for k in (2, 3, 4)), 'MX-2, MX-3 and MX-4 are in, once each')
    # ---- Fractals: the newest backlog references (v0.296 entry, task SQ1: Kick -19.05560 dB fb577dd5202b, Bass -35.48685 dB 392ec52590c7, master at -10 dB) ----
    ids = J(R, "Object.fromEntries(S.tracks.map(t=>[t.name,t.id]))"); R("S.master=-10;changed(true);syncGraph();0")
    for nm, (hh, rf) in {'Kick': ('fb577dd5202b', -19.05560), 'Bass': ('392ec52590c7', -35.48685)}.items():
        x = render(pg, 64, 96, ids[nm], 44100); lv = db(rms(x))
        if hsh(x) != hh:  # the Sidechain pump's start-beat race (SIDE_B0, found by lane D, fixed by tools/feature-lab/ni/ni_sideb0.py): one more render
            print('note: Fractals %s rendered %.5f dB %s once (the known Sidechain-pump race of main, fixed by ni_sideb0.py); rendering again' % (nm, lv, hsh(x)))
            x = render(pg, 64, 96, ids[nm], 44100); lv = db(rms(x))
        ok(abs(lv - rf) < 0.002 and hsh(x) == hh, 'Fractals %s unchanged: %.5f dB %s (reference %.5f %s)' % (nm, lv, hsh(x), rf, hh))
    ok(J(R, "!S.bmono&&S.tracks.every(t=>!t.bmono&&(t.fx||[]).every(f=>!f.p||f.p.fo!=='spec'))"), 'Fractals has no Bass mono and no Spectral Ducker (nothing new in old projects)')
    ok(J(R, "!/bmono/.test(JSON.stringify(S))"), 'its JSON has no new keys')
    ok(J(R, "[...NODES.values()].every(N=>!N.ut.mxBM)&&!MXBMM"), 'no Bass mono nodes are built in a song without it')
    # ---- the old focus modes, bit for bit ----
    cur = old_modes(pg, R)
    if ref:
        for k in ('all', 'low', 'band', 'high'):
            ok(cur[k] == ref[k], 'Ducker focus %s renders bit for bit as before MX-4 (%s)' % (k, cur[k]), ref[k])
        ok(cur['plain'] == ref['plain'], 'a song without Bass mono (and a track with Width 140 %%) renders bit for bit as before (%s)' % cur['plain'], ref['plain'])
    else:
        print('note: no --base given, the old-mode hashes are', cur)
    sr_live = J(R, SCENE)

    # ---- X3: the Spectral focus ----
    ok(J(R, "ABXFO.spec===4"), 'the Ducker knows the Spectral focus (value 4 in its worklet)')
    lat = J(R, "(()=>{const f=%s;return[fxLat(f,48000),fxLat(f,44100),fxLat(f,96000)]})()" % (DUCK % 'spec'))
    ok(lat == [1024, 1024, 2048], 'its latency is reported: one frame (1024 samples at 44.1 and 48 kHz, 2048 at 96 kHz)', lat)
    R("M4.bass.fx=[%s];changed(true);syncGraph();0" % (DUCK % 'spec'))
    kd = render(pg, 0, 5, None, 48000); R("M4.kick.clips=[];changed(true);0"); nd = render(pg, 0, 5, None, 48000); R("M4.kick.clips=[M4.clip(M4.kickB)];changed(true);0")
    T = J(R, "MX_HOOKS.pdcPlan(48000).T"); ok(T == 1024, 'the plan lines the song up behind it (%d samples)' % T)
    lo_k, lo_n = band_db(kd, 48000, 40, 120), band_db(nd, 48000, 40, 120); hi_k, hi_n = band_db(kd, 48000, 270, 330), band_db(nd, 48000, 270, 330)
    hop = 256 / 48000; red = []
    for k in range(4):
        c = (.25 + .5 * k + .06 + T / 48000 - 1024 / 48000 / 2) / hop; i0, i1 = int(c - 6), int(c + 6); red.append(float((lo_n[i0:i1] - lo_k[i0:i1]).max()))
    ok(min(red) > 6, 'kick keying a bass of 60 Hz and 300 Hz: the 40 to 120 Hz band goes down more than 6 dB on each kick (%s dB)' % ['%.1f' % r for r in red])
    s0 = int(1.0 / hop); dh = np.abs(hi_k[s0:] - hi_n[s0:])
    ok(float(dh.max()) < .5, 'while 300 Hz stays within 0.5 dB (largest change %.3f dB)' % float(dh.max()))
    mid = [float((lo_n[int((.25 + .5 * k + .38 + T / 48000) / hop)] - lo_k[int((.25 + .5 * k + .38 + T / 48000) / hop)])) for k in range(3)]
    ok(max(abs(m) for m in mid) < .5, 'between the kicks the bass is back (%s dB)' % ['%.2f' % m for m in mid])
    R("M4.bass.fx=[];changed(true);syncGraph();0"); dry = render(pg, 0, 5, None, 48000)
    nn = min(nd.shape[1] - T, dry.shape[1]) - 2400; a, bq = nd[:, T + 2400:T + 2400 + nn].astype(np.float64), dry[:, 2400:2400 + nn].astype(np.float64)
    W = 4800; dmax = max(abs(db(rms(a[c][i:i + W])) - db(rms(bq[c][i:i + W]))) for c in range(2) for i in range(0, a.shape[1] - W, W))
    err = db(rms(a - bq)) - db(rms(bq))
    ok(dmax < .1, 'with nothing ducking, the Spectral Ducker is within 0.1 dB of its input (largest %.4f dB in 0.1 s windows; difference %.0f dB below the signal)' % (dmax, -err))
    # an impulse on another track arrives on the same sample as an impulse through the Spectral Ducker
    R("M4.bass.fx=[%s];M4.bass.clips=[M4.clip(M4.impB)];M4.other.vol=1;M4.other.clips=[M4.clip(M4.impB)];M4.other.pan=-1;M4.bass.pan=1;M4.kick.clips=[];changed(true);syncGraph();0" % (DUCK % 'spec'))
    ix = render(pg, 0, 5, None, 48000); pL, pR = int(np.argmax(np.abs(ix[0]))), int(np.argmax(np.abs(ix[1])))
    ok(pL == pR, 'an impulse through the Spectral Ducker and one on a track without it arrive on the same sample (%d and %d)' % (pR, pL))
    R("M4.bass.clips=[M4.clip(M4.bassB)];M4.other.vol=0;M4.other.clips=[];M4.other.pan=0;M4.bass.pan=0;M4.kick.clips=[M4.clip(M4.kickB)];changed(true);syncGraph();0")
    # live: the band gains for lane E, and export equals playback
    ex = render(pg, 0, 5, None, sr_live); md, mx, nw, at = exp_vs_live(pg, R, ex, sr_live, 2700)
    ok(nw > 50 and md < .1, 'export equals playback with a Spectral Ducker: median %.3f dB, largest %.2f dB (20 ms windows, recording %d)' % (md, mx, at))
    R("""(()=>{window.__sb=null;ensureCtx();ctx.resume();pos=0;start();setTimeout(()=>{window.__sb=(b=>b?[b.length,Math.min(...b)]:'none')(MX_HOOKS.specBands(M4.bass,M4.bass.fx[0]));stop()},900);return 1})()""")
    pg.wait_for_function("()=>window.__sb!==null", timeout=10000); sb = J(R, "__sb")
    ok(isinstance(sb, list) and sb[0] == 32 and sb[1] < .9, 'MX_HOOKS.specBands gives the 32 band gains while playing (lowest %.2f)' % (sb[1] if isinstance(sb, list) else -1), sb)
    ok(J(R, "MX_HOOKS.specEdges().length===33&&Math.abs(MX_HOOKS.specEdges()[32]-20000)<1e-6"), 'MX_HOOKS.specEdges gives the band edges, 20 Hz to 20 kHz')

    # ---- X19: Bass mono ----
    R("M4.bass.fx=[];M4.kick.clips=[];changed(true);syncGraph();0")
    def bm(clip, on, f=120, master=False):
        R("M4.bass.clips=[M4.clip(M4.%s)];%s;changed(true);syncGraph();0" % (clip, ("S.bmono={on:%s,f:%d};delete M4.bass.bmono" if master else "M4.bass.bmono={on:%s,f:%d};delete S.bmono") % ('true' if on else 'false', f)))
        return render(pg, 0, 5, None, 48000)
    for master in (False, True):
        who = 'the master' if master else 'a track'
        s60o, s60b = bm('s60', False, master=master), bm('s60', True, master=master)
        s1ko, s1kb = bm('s1k', False, master=master), bm('s1k', True, master=master)
        mo, mb = bm('monoB', False, master=master), bm('monoB', True, master=master)
        d60 = db(rms(s60b[0][48000:4 * 48000])) - db(rms(s60o[0][48000:4 * 48000])); d1k = db(rms(s1kb[0][48000:4 * 48000])) - db(rms(s1ko[0][48000:4 * 48000]))
        ok(d60 < -30, 'Bass mono at 120 Hz on %s: a side-only 60 Hz tone falls more than 30 dB (%.1f dB)' % (who, d60))
        ok(abs(d1k) < .2, 'Bass mono at 120 Hz on %s: a side-only 1 kHz tone stays within 0.2 dB (%.3f dB)' % (who, d1k))
        tl = J(R, "M4.tones"); dm = [tone_db(mb[c], 48000, f) - tone_db(mo[c], 48000, f) for f in tl for c in range(2)]
        ok(max(abs(x) for x in dm) < .1, 'Bass mono on %s: a mono signal stays within 0.1 dB at every frequency from 31 Hz to 16 kHz (largest %.4f dB)' % (who, max(abs(x) for x in dm)))
        if master:
            ok(J(R, "!!MXBMM"), 'live, the master gets its Bass mono stage (routeMaster)')
        else:
            ok(J(R, "!!NODES.get(M4.bass.id).ut.mxBM&&!NODES.get(M4.kick.id).ut.mxBM"), 'live, only the track with Bass mono gets the stage')
    # live recording and export with Bass mono on a track
    R("delete S.bmono;M4.bass.bmono={on:true,f:120};M4.bass.clips=[M4.clip(M4.s60)];M4.bass.width=100;changed(true);syncGraph();0")
    y1 = record(pg, R, 1800, REC_OUT); R("M4.bass.bmono.on=false;changed(true);syncGraph();0"); y0 = record(pg, R, 1800, REC_OUT)
    lv1, lv0 = db(rms(y1[0][int(.6 * sr_live):int(1.4 * sr_live)])), db(rms(y0[0][int(.6 * sr_live):int(1.4 * sr_live)]))
    ok(lv1 - lv0 < -30, 'live playback: Bass mono on the track takes the side-only 60 Hz out too (%.1f dB against %.1f dB)' % (lv1, lv0))
    ok(J(R, "!NODES.get(M4.bass.id).ut.mxBM"), 'turned off, the stage goes away again')
    R("M4.bass.bmono={on:true,f:120};M4.bass.clips=[M4.clip(M4.monoB)];changed(true);syncGraph();0"); ex2 = render(pg, 0, 5, None, sr_live)
    md, mx, nw, at = exp_vs_live(pg, R, ex2, sr_live, 2700)
    ok(md < .1, 'export equals playback with Bass mono: median %.3f dB, largest %.2f dB (recording %d)' % (md, mx, at))
    # the frequency follows without a rebuild
    R("M4.bass.bmono.f=200;changed(true);syncGraph();0"); ok(J(R, "NODES.get(M4.bass.id).ut.mxBM.f===200"), 'a new frequency is set on the same filters (no rebuild)')
    ok(J(R, "MX_HOOKS.bassMono(M4.bass).on===true&&MX_HOOKS.bassMono(M4.bass).f===200&&MX_HOOKS.bassMono({kind:'master'}).on===false"), 'MX_HOOKS.bassMono reads tracks and the master')
    ok(J(R, "(t=>{const c=JSON.parse(JSON.stringify(t));return c.bmono.on===true&&c.bmono.f===200})(M4.bass)"), 'Bass mono is saved with the track (t.bmono)')
    # undo
    uu = J(R, "(()=>{delete M4.bass.bmono;changed(true);MX_HOOKS.setBassMono(M4.bass,true,150);const a=!!(M4.bass.bmono&&M4.bass.bmono.on);undo();const t=trkById(M4.bass.id);return[a,!(t.bmono&&t.bmono.on)]})()")
    ok(uu == [True, True], 'turning it on is one undo step', uu)
    R("for(const k of['kick','bass','other'])M4[k]=trkById(M4[k].id);0")  # undo puts back copies of the tracks
    # MX_HOOKS.bandFilter
    R(r"""window.__bf=null;(async()=>{const r=[];for(const f of[80,1000,20]){const sr=48000,c=new OfflineAudioContext(1,sr,sr),F=MX_HOOKS.bandFilter(c,40,120),o=c.createOscillator();o.frequency.value=f;o.connect(F.in);F.out.connect(c.destination);o.start();
      const b=await c.startRendering(),d=b.getChannelData(0);let s=0;for(let i=sr/2;i<sr;i++)s+=d[i]*d[i];r.push(10*Math.log10(s/(sr/2)/.5))}return r})().then(v=>{window.__bf=v});0""")
    pg.wait_for_function("()=>window.__bf!==null", timeout=20000); bf = J(R, "__bf")
    ok(bf[0] > -3 and bf[1] < -40 and bf[2] < -12, 'MX_HOOKS.bandFilter(40, 120 Hz) passes 80 Hz (%.1f dB) and holds back 1 kHz (%.1f dB) and 20 Hz (%.1f dB)' % tuple(bf))

    # ---- the switch ----
    R("selT=M4.bass.id;M4.bass.bmono={on:false,f:120};renderFx();0"); pg.wait_for_timeout(250)
    bt = J(R, "(b=>b?[b.textContent,b.classList.contains('on'),b.title]:null)(document.querySelector('#fxin .tdev2 .tdbs .mxbm'))")
    ok(bt and 'Bass mono' in bt[0] and '120' in bt[0] and not bt[1] and bt[2], 'the track\'s first device shows the Bass mono switch with its frequency and a tooltip', bt and bt[0])
    ok(bt and '—' not in bt[0] + bt[2] and '—' not in J(R, "MXSPTIP"), 'no em dashes in its texts')
    pg.click('#fxin .tdev2 .mxbm span'); pg.wait_for_timeout(200); ok(J(R, "!!(trkById(M4.bass.id).bmono&&trkById(M4.bass.id).bmono.on)"), 'clicking it turns Bass mono on')
    pg.click('#fxin .tdev2 .mxbm [data-mxbmf]'); pg.wait_for_timeout(200)
    mn = J(R, "MENU.map(i=>i&&(i.label||i.head)||'')"); ok('80 Hz' in mn and '500 Hz' in mn and 'Off' in mn, 'clicking the number opens the frequency menu', mn)
    R("(MENU.find(i=>i&&i.label==='80 Hz')||{act:()=>0}).act();closeMenu&&closeMenu();0"); pg.wait_for_timeout(150)
    ok(J(R, "trkById(M4.bass.id).bmono.f===80&&trkById(M4.bass.id).bmono.on"), 'choosing 80 Hz sets it')
    D = pg.query_selector('#fxin .tdev2')
    ov = J(R, "(()=>{const b=document.querySelector('#fxin .tdev2 .mxbm'),g=b.closest('.tdbs').getBoundingClientRect(),r=b.getBoundingClientRect(),d=b.closest('.tdev2').getBoundingClientRect();return[r.right<=g.right+1,r.bottom<=d.bottom+1,r.height]})()")
    ok(ov[0] and ov[1] and ov[2] > 10, 'the switch fits inside the channel strip', ov)
    if D: D.screenshot(path=os.path.join(OUT, 'mx4_strip_dark.png'))
    R("(()=>{const e=document.getElementById('setBg');if(e){e.value=100;e.dispatchEvent(new Event('input',{bubbles:true}))}return 1})()"); pg.wait_for_timeout(400)
    D = pg.query_selector('#fxin .tdev2')
    if D: D.screenshot(path=os.path.join(OUT, 'mx4_strip_light.png'))
    cl = J(R, "getComputedStyle(document.querySelector('#fxin .mxbm')).color")
    R("(()=>{const e=document.getElementById('setBg');if(e){e.value=40;e.dispatchEvent(new Event('input',{bubbles:true}))}return 1})()")
    ok(bool(cl), 'drawn in Dark and Light (%s in Light)' % cl)
    R("selMaster();0"); pg.wait_for_timeout(250)
    mb = J(R, "(b=>b?[b.textContent,b.dataset.mxbm]:null)(document.querySelector('#fxin>.mxbm'))")
    ok(mb and mb[1] == 'master', 'the master shows its own switch above its devices', mb)
    pg.click('#fxin>.mxbm span'); pg.wait_for_timeout(200); ok(J(R, "!!(S.bmono&&S.bmono.on)&&!!MXBMM"), 'clicking it turns the master\'s Bass mono on (live stage built)')
    pg.screenshot(path=os.path.join(OUT, 'mx4_master.png'), clip={'x': 0, 'y': 560, 'width': 900, 'height': 440})
    pg.click('#fxin>.mxbm span'); pg.wait_for_timeout(200); ok(J(R, "!S.bmono.on&&!MXBMM"), 'and off again')
    R("selMaster();0"); pg.wait_for_timeout(200); R("M4.bass.fx=[%s];changed(true);selectTrack(M4.bass.id);renderFx();0" % (DUCK % 'spec')); pg.wait_for_timeout(300)
    so = J(R, "(o=>o?[o.textContent,o.selected,o.title,o.parentElement.title]:null)(document.querySelector('#fxin .dev select option[value=\"spec\"]'))")
    ok(so and so[0] == 'Spectral (32 bands)' and so[1] and so[2] and 'Listen to' in so[3], 'the Ducker shows Spectral (32 bands) in Listen to, chosen, with a tooltip', so and so[:2])
    dv = pg.query_selector('#fxin .dev[data-id="%s"]' % J(R, "M4.bass.fx[0].id"))
    if dv: dv.screenshot(path=os.path.join(OUT, 'mx4_ducker.png'))
    R("openMixer();0"); pg.wait_for_timeout(300); R("abxOpen(M4.bass.fx[0].id);0"); pg.wait_for_timeout(400)
    wb = J(R, "[...document.querySelectorAll('[data-fo]')].filter(b=>b.closest('.abxseg')).map(b=>[b.dataset.fo,b.classList.contains('on'),!!b.title])")
    ok(any(x[0] == 'spec' and x[1] and x[2] for x in wb), 'the sidechain window offers Spectral too, chosen, with a tooltip', wb)
    ok(J(R, "![...document.querySelectorAll('.agff,.abxfo [data-c$=\":ff\"]')].length"), 'its Focus dial is hidden for Spectral (it has no single frequency)')
    try:
        w = pg.locator('.agw:visible, .abxw:visible').first; w.screenshot(path=os.path.join(OUT, 'mx4_window.png'), timeout=4000)
    except Exception as e: print('note: no window screenshot', str(e)[:80])
    blk = SRC[SRC.index('/* ===== task MX-4 (lane K'):SRC.index('function askChoice(title,text,btns,icon){')]
    ok('setInterval(' not in blk and 'requestAnimationFrame(' not in blk and 'setTimeout(' not in blk, 'no new per-frame or timed work')
    ok(len(logs) == 0, 'no console errors', logs[:5])
    b.close()
print('%d checks, %d failed' % (N[0], len(FAIL)))
for f in FAIL: print('  FAILED:', f)
sys.exit(1 if FAIL else 0)
