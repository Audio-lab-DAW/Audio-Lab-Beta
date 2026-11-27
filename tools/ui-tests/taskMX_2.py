#!/usr/bin/env python3
"""Task MX-2 (lane K, mixing engine): device automation in export; delay compensation for every path (X5); latency you can see (X6).
- Automation: a Pro EQ's output swept by automation, a track's volume, a macro driving the EQ: the export follows them (it did not before),
  and a live recording follows the same curve (how close is printed).
- Alignment: impulses on seven tracks, each through another path (straight, a group with look-ahead, a post send and a pre send into a return
  with a Compressor, a return with a look-ahead Ducker, an output into a track with a Drive): every one arrives on the same sample in export,
  and live they add up to one spike. A Ducker's trigger from a latent track ducks at the same moment as from a plain one.
- A latency change while playing moves under a short dip (no step in a 1 kHz tone); Delay compensation off in Settings turns it all off;
  lane J's played-track hook (LT_HOOKS.pdcLive) keeps a played track out of it; the read-out on the track's first device; Fractals.
   python3 tools/ui-tests/taskMX_2.py [index.html] [out dir]"""
import sys, os, json, base64, hashlib
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
        if (m.type == 'error' and 'fetching the script' not in m.text) or (m.type == 'warning' and 'nominal range' not in m.text and 'GPU stall' not in m.text and 'willReadFrequently' not in m.text): logs.append(m.type + ': ' + m.text[:200])
    pg.on('console', con); pg.on('pageerror', lambda e: logs.append('pageerror: ' + str(e)[:300]))
    pg.route('https://app.test/**', lambda r: r.fulfill(status=200, content_type='text/html', body=SRC) if r.request.url.endswith('.html') else r.fulfill(status=404, body=''))
    pg.add_init_script(INIT)
    pg.goto('https://app.test/index.html'); pg.wait_for_function("()=>window.AudioLab&&window.AudioLab.version", timeout=120000); pg.wait_for_timeout(3500)
    pg.evaluate("()=>{for(const i of['splash','liteNote']){const s=document.getElementById(i);if(s)s.remove()}}")
    R = lambda c: pg.evaluate("c=>AudioLab.run(c)", c)
    return b, pg, logs, R
J = lambda R, c: json.loads(R("JSON.stringify(" + c + ")"))
db = lambda v: 20 * np.log10(max(v, 1e-12))
def render(pg, b0, b1, sr, only=None):
    h = pg.evaluate("o=>AudioLab.render(o)", {'b0': b0, 'b1': b1, 'sr': sr, 'only': only, 'single': True}); ch = []
    for c in range(h['ch']):
        parts = []
        for off in range(0, h['len'], 1 << 18):
            n = min(1 << 18, h['len'] - off); parts.append(np.frombuffer(base64.b64decode(pg.evaluate("a=>AudioLab.pull(a[0],a[1],a[2],a[3])", [h['id'], c, off, n])), dtype=np.float32))
        ch.append(np.concatenate(parts))
    pg.evaluate("i=>AudioLab.free(i)", h['id']); return np.stack(ch)
def hsh(x): return hashlib.md5(b''.join(c.tobytes() for c in x)).hexdigest()[:12]
def rms_db(x): return db(float(np.sqrt(np.mean(x.astype(np.float64) ** 2))))

# a recorder on the live master: plays from beat 0 for `secs` and returns the left channel
REC = r"""window.__rec=null;(async()=>{ensureCtx();await ctx.resume();syncGraph();if(!window.MXREC){const code="class R extends AudioWorkletProcessor{constructor(){super();this.on=false;this.port.onmessage=e=>{this.on=e.data}}process(i){if(this.on&&i[0]&&i[0][0])this.port.postMessage(i[0][0].slice(0));return true}}registerProcessor('mxrec',R)";
  await ctx.audioWorklet.addModule(URL.createObjectURL(new Blob([code],{type:'application/javascript'})));MXREC=new AudioWorkletNode(ctx,'mxrec',{numberOfInputs:1,numberOfOutputs:1,channelCount:2,channelCountMode:'explicit'});const z=ctx.createGain();z.gain.value=0;MXREC.connect(z);z.connect(ctx.destination);master.connect(MXREC);MXREC.port.onmessage=e=>{if(window.__chunks)__chunks.push(e.data)}}
  __chunks=[];pos=0;MXREC.port.postMessage(true);start();await new Promise(r=>setTimeout(r,%d));%s;await new Promise(r=>setTimeout(r,%d));stop();MXREC.port.postMessage(false);await new Promise(r=>setTimeout(r,150));
  const n=__chunks.reduce((a,c)=>a+c.length,0),o=new Float32Array(n);let k=0;for(const c of __chunks){o.set(c,k);k+=c.length}let s='';const u=new Uint8Array(o.buffer);for(let i=0;i<u.length;i+=8192)s+=String.fromCharCode.apply(null,u.subarray(i,i+8192));window.__rec=btoa(s)})().catch(e=>{window.__rec='err '+e});0"""
def live_rec(pg, R, ms_a, mid='0', ms_b=0):
    R(REC % (ms_a, mid, ms_b)); pg.wait_for_function("()=>window.__rec!==null", timeout=60000); v = pg.evaluate("()=>window.__rec")
    assert not v.startswith('err'), v
    return np.frombuffer(base64.b64decode(v), dtype=np.float32)

SCENE = r"""(()=>{ensureCtx();S.bpm=120;const sr=ctx.sampleRate,spb=.5,len=Math.round(8*spb*sr);
 const imp=(()=>{const b=ctx.createBuffer(2,len,sr);const k=Math.round(1*spb*sr);for(let c=0;c<2;c++)b.getChannelData(c)[k]=.5;return addBuf(b)})(),
  tone=(()=>{const b=ctx.createBuffer(2,len,sr);for(let c=0;c<2;c++){const d=b.getChannelData(c);for(let i=0;i<len;i++)d[i]=.25*Math.sin(2*Math.PI*1000*i/sr)}return addBuf(b)})();
 const trk=(name,color,buf)=>{const t=mkTrack('audio',null,name,color);t.vol=1;t.pan=0;if(buf)t.clips.push(mkClip({start:0,len:8,name,buf,dur:len/sr,gain:0,fi:0,fo:0}));return t},
  bus=(kind,name,color)=>({id:rid(),kind,name,color,vol:1,pan:0,mute:false,solo:false,fx:[],clips:[]}),fx=(type,p)=>{const f=mkFx(type);Object.assign(f.p,p||{});return f};
 const A=trk('A straight','#ffd166',imp),B=trk('B post send','#ff9a3c',imp),C=trk('C pre send','#ff6b6b',imp),D=trk('D in group','#9be38a',imp),E=trk('E out to track','#c39bff',imp),Fx=trk('F to Ducker return','#7fd0ff',imp),
  sink=trk('Sink','#888'),Y=trk('Y resample','#b583ff'),G=bus('group','Glue','#9be38a'),R1=bus('return','Comp bus','#4cc9f0'),R2=bus('return','Look bus','#3ecf8e');
 sink.mute=true;R1.fx.push(fx('comp',{threshold:0,ratio:1,makeup:0,attack:1,release:20}));R2.fx.push(fx('duck',{la:3,amt:0}));G.fx.push(fx('duck',{la:2,amt:0}));Y.fx.push(fx('duck',{la:1,amt:0}));
 B.out=sink.id;B.sends={[R1.id]:1};C.vol=0;C.sends={[R1.id]:1};C.sendPre={[R1.id]:true};D.grp=G.id;E.out=Y.id;Fx.out=sink.id;Fx.sends={[R2.id]:1};
 S.tracks=[A,B,C,G,D,E,Y,Fx,sink,R1,R2];S.mfx=[];S.master=0;S.loop=false;S.pauto={};window.MXT={A,B,C,D,E,Fx,sink,Y,G,R1,R2,tone,imp,trk,fx};changed(true);syncGraph();
 return{sr,ids:[A.id,B.id,C.id,D.id,E.id,Fx.id]}})()"""
SRCS = ['A', 'B', 'C', 'D', 'E', 'Fx']
def solo_src(R, name):
    R("for(const k of %s)MXT[k].mute=k!==%s;changed(true);syncGraph();0" % (json.dumps(SRCS), json.dumps(name)))

with sync_playwright() as p:
    b, pg, logs, R = boot(p)
    v = R("VERSION"); ok(tuple(map(int, v.split('.'))) >= (0, 295), 'version 0.295 or later', v)
    # ---- Fractals ----
    ids = J(R, "Object.fromEntries(S.tracks.map(t=>[t.name,t.id]))")
    for nm, ref in (('Kick', 'fb577dd5202b'), ('Bass', '392ec52590c7')):
        x = render(pg, 64, 96, 44100, ids[nm]); ok(hsh(x) == ref, 'Fractals %s %.5f dB %s (reference %s)' % (nm, rms_db(x), hsh(x), ref))
    render(pg, 64, 72, 44100)  # the first render of a session differs on v0.294 too (warm-up); not compared
    x = render(pg, 64, 96, 44100); ok(abs(rms_db(x) - -20.37603) < 0.005, 'Fractals full mix beats 64 to 96: %.5f dB (v0.294: -20.37603 dB, a5d0e1bfe9bd; now %s: at 44.1 kHz the Compressor is lined up on its real 264 samples, not 265)' % (rms_db(x), hsh(x)))
    fm = J(R, "(()=>{const M=pdcMap(44100);return{T:M.target,e:[...M.edge].map(([k,v])=>[k,v])}})()")
    ok(fm['T'] == 264, 'Fractals: the longest path 264 samples at 44.1 kHz (the Drums and Kick & Bass groups), as before', fm)
    ok(len(fm['e']) == 3 and all(v == 264 for k, v in fm['e']), 'Fractals: three sends from tracks in the latent Drums group now wait 264 samples for their group', fm['e'])
    ok(J(R, "S.tracks.some(t=>t.name==='Clap')&&S.tracks.filter(t=>t.name==='Lead').every(t=>(MXPML||pdcMap(ctx.sampleRate,true)).get(t.id)>0)"), 'Fractals live map in step (tracks outside the latent groups delayed)')

    # ---- automation in export ----
    sr = J(R, SCENE)['sr']
    R("(()=>{const t=MXT.A;t.mute=false;t.clips=[mkClip({start:0,len:8,name:'tone',buf:MXT.tone,dur:4,gain:0,fi:0,fo:0})];for(const k of['B','C','D','E','Fx'])MXT[k].mute=true;const f=mkFx('eq');t.fx.push(f);window.MXQ=f;changed(true);syncGraph();S.pauto={['f:'+t.id+':'+f.id+':out']:[{b:0,v:0},{b:8,v:1}]}})();0")
    x = render(pg, 0, 8, sr); spb = .5
    lv = [rms_db(x[:, int(bt * spb * sr):int(bt * spb * sr) + 960]) for bt in (0.5, 2, 4, 6, 7.5)]
    base = J(R, "20*Math.log10(.25/Math.SQRT2)+20*Math.log10(masterGain())")
    exp = [base - 12 + 24 * bt / 8 for bt in (0.5, 2, 4, 6, 7.5)]
    ok(all(abs(a - e) < 0.15 for a, e in zip(lv, exp)), 'device automation in export: the Pro EQ output follows the sweep -12 to +12 dB', ['%.2f/%.2f' % (a, e) for a, e in zip(lv, exp)])
    lr = live_rec(pg, R, 4300)
    # live: the level along the sweep, every 50 ms, against the export (aligned by the onset of the tone)
    on = int(np.argmax(np.abs(lr) > 1e-4)); xo = int(np.argmax(np.abs(x[0]) > 1e-4)); W = int(.05 * sr); dif = []
    for k in range(4, 70):
        a = lr[on + k * W:on + (k + 1) * W]; e = x[0, xo + k * W:xo + (k + 1) * W]
        if len(a) == W and len(e) == W: dif.append(rms_db(a) - rms_db(e))
    md = max(abs(d) for d in dif) if dif else 99
    ok(len(dif) > 50 and md < 1.0, 'live follows the same sweep: largest difference %.2f dB over 3.3 s in 50 ms windows (live sets it every 33 ms)' % md)
    R("S.pauto={['t:'+MXT.A.id+':vol']:[{b:0,v:SPEC_VOL.n(1)},{b:8,v:SPEC_VOL.n(.25)}]};MXT.A.fx=[];changed(true);syncGraph();0")
    x = render(pg, 0, 8, sr); a0 = rms_db(x[:, int(.2 * spb * sr):int(.2 * spb * sr) + 960]); a1 = rms_db(x[:, int(7.8 * spb * sr):int(7.8 * spb * sr) + 960])
    ok(a1 < a0 - 6, 'track volume automation in export (%.2f to %.2f dB)' % (a0, a1))
    R("(()=>{const t=MXT.A,f=mkFx('eq');t.fx=[f];t.macro={items:[{id:'mq',name:'Tone',v:.5,routes:[{pid:'f:'+t.id+':'+f.id+':out',a:0,b:1}]}]};S.pauto={['x:'+t.id+':mq']:[{b:0,v:0},{b:8,v:1}]};changed(true);syncGraph()})();0")
    x = render(pg, 0, 8, sr); m0 = rms_db(x[:, int(.5 * spb * sr):int(.5 * spb * sr) + 960]); m1 = rms_db(x[:, int(7.5 * spb * sr):int(7.5 * spb * sr) + 960])
    ok(abs((m1 - m0) - 21) < 0.3, 'macro automation reaches the device it drives in export (%.2f dB over the sweep, expected 21)' % (m1 - m0))
    R("S.pauto={};MXT.A.fx=[];delete MXT.A.macro;MXT.A.clips=[mkClip({start:0,len:8,name:'imp',buf:MXT.imp,dur:4,gain:0,fi:0,fo:0})];changed(true);syncGraph();0")

    # ---- X5: one impulse per path ----
    M = J(R, "(()=>{const M=pdcMap(ctx.sampleRate);return{T:M.target,d:Object.fromEntries([...M].map(([k,v])=>[trkById(k).name,v])),e:Object.fromEntries(M.edge),pre:[...M.pre]}})()")
    print('map', M)
    imp_at = int(round(1 * .5 * sr)); T = M['T']
    ok(T == J(R, "Math.floor(.006*ctx.sampleRate+1e-6)"), 'longest path = the Compressor return (6 ms) in this scene', T)
    pk = {}
    for nm in SRCS:
        solo_src(R, nm); x = render(pg, 0, 4, sr); pk[nm] = int(np.argmax(np.abs(x[0])))
    ok(all(v == imp_at + T for v in pk.values()), 'export: every path arrives on the same sample (%d = impulse + %d)' % (imp_at + T, T), pk)
    R("for(const k of %s)MXT[k].mute=false;changed(true);syncGraph();0" % json.dumps(SRCS))
    x = render(pg, 0, 4, sr); a = np.abs(x[0]); top = a.max(); spots = np.nonzero(a > .1 * top)[0]
    ok(len(spots) == 1, 'export: all six together make one spike (%d places over 10 %%)' % len(spots), list(spots[:10]))
    lr = live_rec(pg, R, 1500); a = np.abs(lr); top = a.max(); spots = np.nonzero(a > .1 * top)[0]
    ok(top > .5 and len(spots) == 1, 'live: all six together make one spike, so they arrive on the same sample live too (%d places, peak %.2f)' % (len(spots), top), list(spots[:10]))
    old = J(R, "(()=>{UI.pdc=false;changed(true);syncGraph();const M=pdcMap(ctx.sampleRate);return M.target+M.edge.size})()")
    x = render(pg, 0, 4, sr); a = np.abs(x[0]); spots = np.nonzero(a > .1 * a.max())[0]
    ok(old == 0 and len(spots) > 1, 'Delay compensation off in Settings: no delays, the paths fall apart again (%d places)' % len(spots))
    R("delete UI.pdc;changed(true);syncGraph();0")
    # lane J's played-track hook
    lt = J(R, "(()=>{const had=LT_HOOKS.pdcLive;LT_HOOKS.pdcLive=()=>new Set([MXT.A.id]);const a=pdcMap(ctx.sampleRate,true).get(MXT.A.id),b=pdcMap(ctx.sampleRate).get(MXT.A.id);if(had)LT_HOOKS.pdcLive=had;else delete LT_HOOKS.pdcLive;return[a,b]})()")
    ok(lt[0] == 0 and lt[1] > 0, "lane J's LT_HOOKS.pdcLive: a played track gets no delay live, the export still lines it up", lt)
    # Ducker trigger from a latent track: ducks at the same place relative to the song
    def duck_onset(lat):
        R("""(()=>{const K=MXT.trk('Kick','#ff4d6d',MXT.imp),H=MXT.trk('Hold','#4c8dff',MXT.tone),d=MXT.fx('duck',{amt:100,th:-40,gain:0,at:0,hd:20,rl:40,la:0,fo:'all'});d.p.src=K.id;H.fx.push(d);if(%s)K.fx.push(MXT.fx('drive',{drive:0,mix:0}));K.mute=true;
          S.tracks=[K,H];changed(true);syncGraph()})();0""" % ('true' if lat else 'false'))
        T = J(R, "pdcMap(ctx.sampleRate).target"); x = render(pg, 0, 4, sr); env = np.abs(x[0]); i0 = imp_at
        w = int(sr / 1000); e2 = np.sqrt(np.convolve(x[0].astype(np.float64) ** 2, np.ones(w) / w, 'same')); seg = e2[i0 - 2000:i0 + 6000]; base = np.median(seg[:1500]); on = int(np.argmax(seg < .5 * base)) + i0 - 2000
        return on - T, T, J(R, "(()=>{const M=pdcMap(ctx.sampleRate);return[[...M.edge],[...M.pre]]})()")
    o0, t0, m0 = duck_onset(False); o1, t1, m1 = duck_onset(True)
    ok(t1 == 192 and o0 == o1, 'a Ducker keyed from a track with a Drive (192 samples) ducks at the same place in the song as from a plain one (%d / %d)' % (o0, o1), m1)
    kd = J(R, "(()=>{const H=S.tracks[1],f=H.fx[0],X=NODES.get(H.id).fxm.get(f.id),N=NODES.get(H.id);return[!!N.mxPdOn,N.mxPd?Math.round(N.mxPd.delayTime.value*ctx.sampleRate):null,X.kdl?Math.round(X.kdl.delayTime.value*ctx.sampleRate):0]})()")
    ok(kd[0] and kd[1] == 192 and kd[2] == 0, 'live: the keyed track is delayed before its devices (192 samples), the trigger needs no extra', kd)

    # ---- a latency change while playing: no step in a tone ----
    R("""(()=>{const H=MXT.trk('Tone','#ffd166',MXT.tone),L=MXT.trk('Latent','#888',MXT.imp),d=MXT.fx('duck',{la:2,amt:0});L.fx.push(d);L.mute=true;S.tracks=[H,L];window.MXL=d;changed(true);syncGraph()})();0""")
    lr = live_rec(pg, R, 900, "MXL.p.la=5;changed(false);syncGraph()", 900)
    dd = np.abs(np.diff(lr)); slope = 2 * np.pi * 1000 * .25 / sr
    d0 = J(R, "Math.round(NODES.get(S.tracks[0].id).pdc.delayTime.value*ctx.sampleRate)")
    ok(d0 == J(R, "Math.round(.005*ctx.sampleRate)") and dd.max() < 1.6 * slope, 'latency 2 to 5 ms while playing: the tone moves under a short dip, no step (largest change between samples %.4f, a 1 kHz tone at most %.4f)' % (dd.max(), slope))

    # ---- X6: the read-out on the track's first device ----
    R("selT=S.tracks[1].id;renderFx();0"); pg.wait_for_timeout(400)
    ro = J(R, "(()=>{const e=document.querySelector('#fxin .tdev2 .mxlat');return e?[e.textContent,e.title]:null})()")
    ok(ro and ro[0] == '5.0 ms' and 'delay its sound by 5.0 ms' in ro[1] and 'Longest path in the song: 5.0 ms (Latent, Ducker)' in ro[1], 'read-out on the latent track: 5.0 ms, tooltip with samples and the longest path', ro)
    pg.screenshot(path=os.path.join(OUT, 'mx2_readout.png'))
    R("selT=S.tracks[0].id;renderFx();0"); pg.wait_for_timeout(300)
    ok(J(R, "!document.querySelector('#fxin .tdev2 .mxlat')"), 'no read-out on a track without latency')
    R("selT=S.tracks[1].id;renderFx();MXL.p.la=0;changed(false);syncGraph();0"); pg.wait_for_timeout(300)
    ok(J(R, "!document.querySelector('#fxin .tdev2 .mxlat')"), 'the read-out goes when the latency goes')
    hk = J(R, "[MX_HOOKS.lat(S.tracks[1]),MX_HOOKS.devLat(S.tracks[1],S.tracks[1].fx[0]),MX_HOOKS.pathLat().smp,typeof MX_HOOKS.pdc]")
    ok(hk[0]['smp'] == 0 and hk[1]['smp'] == 0 and hk[3] == 'function', 'hooks lat, devLat, pathLat, pdc', hk)
    ok(len(logs) == 0, 'no console errors', logs[:5])
    b.close()
print('%d checks, %d failed' % (N[0], len(FAIL)))
for f in FAIL: print('  FAILED:', f)
sys.exit(1 if FAIL else 0)
