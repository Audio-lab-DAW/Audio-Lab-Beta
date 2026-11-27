# Task AE1 (sound quality research): what AudioLab's engine does today, measured through the app's own render.
#   python3 tools/engine-lab/ae1/measure_app.py [index.html] [part ...]
# parts: osc acid drive clip limit sum resample dither dc (default: all). Results: tools/engine-lab/ae1/results/app.json
# Every number comes from the app (AudioLab bridge, tools/remake/alab.py): offline renders at 48 kHz unless noted.
import sys, os, json, base64, io, wave
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'remake'))
from alab import AudioLab
from anal import alias_report, true_peak, db, rms, spectrum_db

idx = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1].endswith('.html') else 'index.html'
parts = set(a for a in sys.argv[1:] if not a.endswith('.html'))
want = lambda p: not parts or p in parts
SR = 48000
OUT = os.path.join(HERE, 'results', 'app.json')
os.makedirs(os.path.dirname(OUT), exist_ok=True)
R = json.load(open(OUT)) if os.path.exists(OUT) else {}

al = AudioLab(idx); al.start()
R['version'] = al.version
print('AudioLab', al.version)
hz = lambda p: 440 * 2 ** ((p - 69) / 12)


def ren(b0, b1, **kw):
    x, sr = al.render(b0=b0, b1=b1, sr=SR, **kw)
    return np.asarray(x, np.float64), sr


def offline(js, n):
    """run an offline graph in the app scope; js builds it on `oc` (an OfflineAudioContext 2ch n frames at SR) and
    must leave the render promise to us; returns (2, n) float64"""
    code = """(async()=>{const oc=new OfflineAudioContext(2,%d,%d);await wlLoad(oc);{%s};const b=await oc.startRendering();
      const enc=a=>{const u=new Uint8Array(a.buffer);let s='';for(let i=0;i<u.length;i+=32768)s+=String.fromCharCode.apply(null,u.subarray(i,i+32768));return btoa(s)};
      return JSON.stringify([enc(b.getChannelData(0)),enc(b.getChannelData(1))])})()""" % (n, SR, js)
    a = json.loads(al.page.evaluate("c => AudioLab.run(c)", code))
    return np.array([np.frombuffer(base64.b64decode(s), np.float32) for s in a], np.float64)


def put(x):
    """a float32 array into the page as window.__x[k]; returns the JS expression"""
    x = np.asarray(x, np.float32)
    k = al.page.evaluate("()=>{window.__x=window.__x||[];window.__x.push(null);return window.__x.length-1}")
    b = base64.b64encode(x.tobytes()).decode()
    al.page.evaluate("a=>{const s=atob(a[1]),u=new Uint8Array(s.length);for(let i=0;i<s.length;i++)u[i]=s.charCodeAt(i);window.__x[a[0]]=new Float32Array(u.buffer)}", [k, b])
    return 'window.__x[%d]' % k


# ---------------------------------------------------------------- oscillators (al-poly: Plant, basic synths)
if want('osc'):
    print('--- al-poly saw (Plant, one oscillator, filter at 18 kHz, envelope flat): aliasing against the harmonics')
    rows = []
    for p in (33, 45, 57, 69, 81, 88, 93, 100, 105):
        inst = {'w1': 'sawtooth', 'w2': 'sawtooth', 'morph': 0, 'uni': 1, 'det': 0, 'width': 0, 'cut': 18000, 'res': 0,
                'fenv': 0, 'a': .001, 'd': 1, 's': 1, 'r': .05, 'lfo': 0, 'lamt': 0, 'space': 0, 'sub': 0, 'noise': 0, 'fm': 0, 'gain': .5}
        al.build({'bpm': 120, 'tracks': [{'name': 'S', 'preset': 'plant', 'inst': inst, 'clips': [{'start': 0, 'len': 8, 'notes': [{'p': p, 's': 0, 'l': 6, 'v': 1}]}]}]})
        x, sr = ren(0, 6)
        r = alias_report(x[0][int(.5 * sr):int(2.5 * sr)], sr, hz(p))
        r['note'] = p; rows.append(r)
        print('note %3d %7.1f Hz  alias total %6.1f dB  worst alias %6.1f dB at %7.0f Hz  audible-band (<16k) total %6.1f dB' % (p, hz(p), r['alias_db'], r['worst_db'], r['worst_hz'], r['alias16_db']))
    R['osc_saw'] = rows
    # the spectrum of one high note for the page's plot
    al.build({'bpm': 120, 'tracks': [{'name': 'S', 'preset': 'plant', 'inst': dict(inst), 'clips': [{'start': 0, 'len': 8, 'notes': [{'p': 93, 's': 0, 'l': 6, 'v': 1}]}]}]})
    x, sr = ren(0, 6); np.save(os.path.join(HERE, 'results', 'app_saw93.npy'), x[0][int(.5 * sr):int(2.5 * sr)].astype(np.float32))

# ---------------------------------------------------------------- Acid (al-poly with drive)
if want('acid'):
    print('--- al-poly Acid (psy preset, drive 55 %, envelope off, cut 2 kHz): aliasing of the drive at 1x')
    rows = []
    for p in (33, 45, 57, 69):
        a = {'wave': 'sawtooth', 'cut': 2000, 'res': 12, 'env': 0, 'dec': 1, 'acc': 0, 'slide': 0, 'dist': 55, 'gain': .35}
        al.build({'bpm': 120, 'tracks': [{'name': 'A', 'preset': 'acid', 'inst': a, 'clips': [{'start': 0, 'len': 8, 'notes': [{'p': p, 's': 0, 'l': 6, 'v': .8}]}]}]})
        x, sr = ren(0, 6)
        r = alias_report(x[0][int(.5 * sr):int(2.5 * sr)], sr, hz(p))
        r['note'] = p; rows.append(r)
        print('note %3d %7.1f Hz  alias total %6.1f dB  worst %6.1f dB at %7.0f Hz  (<16k) %6.1f dB' % (p, hz(p), r['alias_db'], r['worst_db'], r['worst_hz'], r['alias16_db']))
    R['acid'] = rows

# ---------------------------------------------------------------- Drive effect (WaveShaper 4x) and Soft Clipper
if want('drive'):
    print('--- Drive effect (WaveShaperNode, oversample 4x, 2048 points) on a sine; input over 0 dBFS hits the end of the curve')
    rows = []
    n = SR * 2
    for f0, lvl, drv in ((1013, -6, 30), (2531, -6, 60), (4057, -6, 60), (2531, 3, 60), (5003, 3, 100), (110.3, 3, 100), (110.3, -6, 30)):
        t = np.arange(n) / SR; s = 10 ** (lvl / 20) * np.sin(2 * np.pi * f0 * t)
        X = put(s)
        js = ("const b=oc.createBuffer(1,%d,%d);b.copyToChannel(%s,0);const s=oc.createBufferSource();s.buffer=b;"
              "const x=mkFxNode(oc,'drive');const f=mkFx('drive');f.p.drive=%d;x.set(f.p);s.connect(x.in);x.out.connect(oc.destination);s.start()") % (n, SR, X, drv)
        y = offline(js, n)[0][SR // 2: SR // 2 + SR]
        r = alias_report(y, SR, f0); r.update({'f0': f0, 'level': lvl, 'drive': drv}); rows.append(r)
        print('sine %5d Hz %+3d dBFS drive %3d: alias total %6.1f dB, worst %6.1f dB at %6.0f Hz' % (f0, lvl, drv, r['alias_db'], r['worst_db'], r['worst_hz']))
    R['drive'] = rows

if want('clip'):
    print('--- Soft Clipper (WaveShaperNode): oversampling none / 2x / 4x, tanh, +6 dB drive, 2.5 kHz sine')
    rows = []
    n = SR * 2
    keys = al.run("JSON.stringify(Object.keys(mkFx('clip').p))")
    print('clip params', keys)
    for os_ in ('none', '2x', '4x'):
        for f0 in (2531, 5003):
            t = np.arange(n) / SR; s = .5 * np.sin(2 * np.pi * f0 * t); X = put(s)
            js = ("const b=oc.createBuffer(1,%d,%d);b.copyToChannel(%s,0);const s=oc.createBufferSource();s.buffer=b;"
                  "const x=mkFxNode(oc,'clip');const f=mkFx('clip');f.p.shape='tanh';f.p.os='%s';f.p.gain=12;x.set(f.p);s.connect(x.in);x.out.connect(oc.destination);s.start()") % (n, SR, X, os_)
            y = offline(js, n)[0][SR // 2: SR // 2 + SR]
            r = alias_report(y, SR, f0); r.update({'os': os_, 'f0': f0}); rows.append(r)
            print('os %-4s sine %5d Hz: alias total %6.1f dB, worst %6.1f dB at %6.0f Hz' % (os_, f0, r['alias_db'], r['worst_db'], r['worst_hz']))
    R['clip'] = rows

# ---------------------------------------------------------------- Limiter: true peak after al-limit
if want('limit'):
    print('--- Limiter (al-limit, transparent, tp on, ceiling -0.3 dBFS) on the Shrine Legion demo pushed +6 / +10 dB; true peak (BS.1770 4x and 16x)')
    al.run("demoImperial();changed(true)")
    al.tracks = json.loads(al.run("JSON.stringify(Object.fromEntries(S.tracks.map(t=>[t.name,t.id])))"))
    mix, sr = ren(4 * 144, 4 * 160)   # Climax: bars 146..161
    mix = mix / np.abs(mix).max() * 10 ** (-1 / 20)
    n = mix.shape[1]
    XL, XR = put(mix[0]), put(mix[1])
    rows = []
    for push in (6, 10):
        for style, tp in (('transparent', True), ('transparent', False), ('aggressive', True)):
            js = ("const b=oc.createBuffer(2,%d,%d);b.copyToChannel(%s,0);b.copyToChannel(%s,1);const s=oc.createBufferSource();s.buffer=b;const g=oc.createGain();g.gain.value=%f;"
                  "const x=mkFxNode(oc,'limit');const f=mkFx('limit');f.p.style='%s';f.p.tp=%s;x.set(f.p);s.connect(g);g.connect(x.in);x.out.connect(oc.destination);s.start()") % (
                n, SR, XL, XR, 10 ** (push / 20), style, 'true' if tp else 'false')
            if not rows:
                print('limit params', al.run("JSON.stringify(mkFx('limit').p)"))
            y = offline(js, n)
            sp = db(np.abs(y).max()); tp4 = true_peak(y, 4); tp16 = true_peak(y, 16)
            over = float(np.mean(np.abs(np.repeat(y, 1, 1)) > 10 ** (-.3 / 20) + 1e-6))
            r = {'push': push, 'style': style, 'tp': tp, 'sample_peak': sp, 'tp4': tp4, 'tp16': tp16}
            # how many true-peak overs above the ceiling, per second
            from anal import overs_per_s
            r['overs_per_s'] = overs_per_s(y, SR, -.3)
            rows.append(r)
            print('push %+d dB  %-11s tp=%-5s  sample peak %6.2f dBFS  true peak 4x %6.2f  16x %6.2f dBTP  overs above ceiling %5.1f /s' % (push, style, tp, sp, tp4, tp16, r['overs_per_s']))
    # the export option "safety limiter" (a DynamicsCompressor)
    for push in (6, 10):
        js = ("const b=oc.createBuffer(2,%d,%d);b.copyToChannel(%s,0);b.copyToChannel(%s,1);const s=oc.createBufferSource();s.buffer=b;const g=oc.createGain();g.gain.value=%f;"
              "const k=oc.createDynamicsCompressor();k.threshold.value=-1;k.knee.value=0;k.ratio.value=20;k.attack.value=.001;k.release.value=.08;s.connect(g);g.connect(k);k.connect(oc.destination);s.start()") % (n, SR, XL, XR, 10 ** (push / 20))
        y = offline(js, n)
        r = {'push': push, 'style': 'export option (DynamicsCompressor)', 'sample_peak': db(np.abs(y).max()), 'tp4': true_peak(y, 4), 'tp16': true_peak(y, 16)}
        rows.append(r); print('push %+d dB  export safety limiter: sample peak %6.2f dBFS, true peak %6.2f dBTP' % (push, r['sample_peak'], r['tp16']))
    R['limit'] = rows
    np.save(os.path.join(HERE, 'results', 'demo_climax.npy'), mix.astype(np.float32))

# ---------------------------------------------------------------- Summing precision
if want('sum'):
    print('--- Summing: 64 tracks (GainNode volume, StereoPanner, master gain) in Web Audio Float32 against the same sum in Float64')
    rng = np.random.default_rng(7)
    n = SR * 2
    T = 64
    srcs = []
    t = np.arange(n) / SR
    for k in range(T):
        f = 40 * 2 ** (rng.uniform(0, 8)); a = 10 ** (rng.uniform(-30, -12) / 20)
        x = a * (np.sin(2 * np.pi * f * t + rng.uniform(0, 6)) + .3 * rng.standard_normal(n) * .1)
        srcs.append(x.astype(np.float32))
    vols = rng.uniform(.3, 1, T); pans = rng.uniform(-1, 1, T); master = 10 ** (-6 / 20)
    names = [put(s) for s in srcs]
    js = "const m=oc.createGain();m.gain.value=%r;m.connect(oc.destination);" % master
    for k in range(T):
        js += ("{const b=oc.createBuffer(1,%d,%d);b.copyToChannel(%s,0);const s=oc.createBufferSource();s.buffer=b;const v=oc.createGain();v.gain.value=%r;const p=oc.createStereoPanner();p.pan.value=%r;s.connect(v);v.connect(p);p.connect(m);s.start()}" % (n, SR, names[k], float(vols[k]), float(pans[k])))
    y = offline(js, n)
    # reference: the same graph in float64 (equal-power pan as the spec: mono input, x = (pan+1)/2)
    ref = np.zeros((2, n))
    for k in range(T):
        x = srcs[k].astype(np.float64) * np.float64(np.float32(vols[k]))
        pp = (np.float32(pans[k]) + 1) / 2
        ref[0] += x * np.cos(pp * np.pi / 2); ref[1] += x * np.sin(pp * np.pi / 2)
    ref *= np.float64(np.float32(master))
    e = y - ref
    r = {'tracks': T, 'mix_rms_db': db(rms(ref)), 'mix_peak_db': db(np.abs(ref).max()), 'err_rms_db': db(rms(e)), 'err_peak_db': db(np.abs(e).max())}
    # the theoretical floor of storing the result in float32 once
    q = ref.astype(np.float32).astype(np.float64) - ref
    r['one_rounding_rms_db'] = db(rms(q))
    R['sum'] = r
    print('mix %.1f dBFS rms, error %.1f dBFS rms (peak %.1f); storing the exact result in float32 once: %.1f dBFS rms' % (r['mix_rms_db'], r['err_rms_db'], r['err_peak_db'], r['one_rounding_rms_db']))

# ---------------------------------------------------------------- Resampling
if want('resample'):
    print('--- Resampling: a 44.1 kHz buffer in a 48 kHz render (AudioBufferSourceNode), a 7-semitone playbackRate, decodeAudioData 44.1 -> 48 kHz')
    rows = []
    for f0 in (1000, 5000, 10000, 15000):
        n0 = 44100 * 2; t = np.arange(n0) / 44100; s = .5 * np.sin(2 * np.pi * f0 * t); X = put(s)
        js = "const b=oc.createBuffer(1,%d,44100);b.copyToChannel(%s,0);const s=oc.createBufferSource();s.buffer=b;s.connect(oc.destination);s.start()" % (n0, X)
        y = offline(js, SR * 2)[0][SR // 2: SR // 2 + SR]
        r = alias_report(y, SR, f0, harmonics=1); r.update({'case': 'buffer 44.1k in 48k', 'f0': f0}); rows.append(r)
        print('44.1k buffer in 48k: %5d Hz tone -> images/aliases total %6.1f dB, worst %6.1f dB at %6.0f Hz' % (f0, r['alias_db'], r['worst_db'], r['worst_hz']))
    for f0 in (1000, 5000, 10000):
        n0 = SR * 3; t = np.arange(n0) / SR; s = .5 * np.sin(2 * np.pi * f0 * t); X = put(s)
        rate = 2 ** (7 / 12)
        js = "const b=oc.createBuffer(1,%d,%d);b.copyToChannel(%s,0);const s=oc.createBufferSource();s.buffer=b;s.playbackRate.value=%r;s.connect(oc.destination);s.start()" % (n0, SR, X, rate)
        y = offline(js, SR * 2)[0][SR // 2: SR // 2 + SR]
        fo = f0 * rate
        r = alias_report(y, SR, fo, harmonics=1); r.update({'case': 'playbackRate +7 semitones', 'f0': f0}); rows.append(r)
        print('pitched +7 st: %5d Hz -> %7.1f Hz: images/aliases total %6.1f dB, worst %6.1f dB at %6.0f Hz' % (f0, fo, r['alias_db'], r['worst_db'], r['worst_hz']))
    # decodeAudioData: a 44.1 kHz 24-bit WAV decoded by a 48 kHz context
    for f0 in (5000, 15000):
        n0 = 44100 * 2; t = np.arange(n0) / 44100; s = .5 * np.sin(2 * np.pi * f0 * t)
        bio = io.BytesIO(); w = wave.open(bio, 'wb'); w.setnchannels(1); w.setsampwidth(3); w.setframerate(44100)
        iv = np.round(s * 8388607).astype(np.int32); w.writeframes(b''.join(int(v).to_bytes(3, 'little', signed=True) for v in iv)); w.close()
        b64 = base64.b64encode(bio.getvalue()).decode()
        code = """(async()=>{const s=atob('%s'),u=new Uint8Array(s.length);for(let i=0;i<s.length;i++)u[i]=s.charCodeAt(i);const c=new OfflineAudioContext(1,48000,48000);const b=await c.decodeAudioData(u.buffer);const d=b.getChannelData(0);
          const v=new Uint8Array(d.buffer);let o='';for(let i=0;i<v.length;i+=32768)o+=String.fromCharCode.apply(null,v.subarray(i,i+32768));return JSON.stringify([b.sampleRate,btoa(o)])})()""" % b64
        rate, enc = json.loads(al.page.evaluate("c => AudioLab.run(c)", code))
        y = np.frombuffer(base64.b64decode(enc), np.float32).astype(np.float64)[SR // 2: SR // 2 + SR]
        r = alias_report(y, SR, f0, harmonics=1); r.update({'case': 'decodeAudioData 44.1k -> 48k', 'f0': f0}); rows.append(r)
        print('decodeAudioData -> %d Hz: %5d Hz tone: images total %6.1f dB, worst %6.1f dB at %6.0f Hz' % (rate, f0, r['alias_db'], r['worst_db'], r['worst_hz']))
    R['resample'] = rows

# ---------------------------------------------------------------- Dither
if want('dither'):
    print('--- Export dither (postProc): noise floor and spectrum at 16 bits; a -90 dBFS 1 kHz tone')
    rows = []
    n = SR * 2; t = np.arange(n) / SR; s = 10 ** (-90 / 20) * np.sin(2 * np.pi * 1000 * t)
    X = put(s)
    for dith in ('off', 'tpdf', 'ns'):
        code = """(()=>{const b=new AudioBuffer({length:%d,numberOfChannels:2,sampleRate:%d});b.copyToChannel(%s,0);b.copyToChannel(%s,1);const r=postProc(b,16,'%s','off');
          const d=r.ch[0];const v=new Uint8Array(new Float32Array(d).buffer);let o='';for(let i=0;i<v.length;i+=32768)o+=String.fromCharCode.apply(null,v.subarray(i,i+32768));return btoa(o)})()""" % (n, SR, X, X, dith)
        y = np.frombuffer(base64.b64decode(al.run(code)), np.float32).astype(np.float64)
        e = y - s
        F, S = spectrum_db(e, SR)
        lo = S[(F > 200) & (F < 4000)].mean(); hi = S[(F > 15000) & (F < 20000)].mean()
        # distortion: harmonics of the tone in the output
        r = alias_report(y, SR, 1000)
        rr = {'dither': dith, 'err_rms_db': db(rms(e)), 'noise_lo_db_per_bin': float(lo), 'noise_hi_db_per_bin': float(hi), 'harm_db': r['harm_db']}
        rows.append(rr)
        print('%-4s error %6.1f dBFS rms; noise per bin 0.2-4 kHz %6.1f, 15-20 kHz %6.1f dB; harmonics of the tone %6.1f dB' % (dith, rr['err_rms_db'], lo, hi, rr['harm_db']))
    R['dither'] = rows
    R['dither_default'] = al.run("String((UI.exOpt||{}).exDit||'tpdf')")

# ---------------------------------------------------------------- DC
if want('dc'):
    print('--- DC: Soft Clipper with asymmetry, Drive on an asymmetric input (a kick-like burst), Acid')
    rows = []
    n = SR * 2; t = np.arange(n) / SR; s = .6 * np.sin(2 * np.pi * 110 * t); X = put(s)
    pk = json.loads(al.run("JSON.stringify(mkFx('clip').p)"))
    print('clip defaults', pk)
    for asym in (0, 25, 50):
        js = ("const b=oc.createBuffer(1,%d,%d);b.copyToChannel(%s,0);const s=oc.createBufferSource();s.buffer=b;"
              "const x=mkFxNode(oc,'clip');const f=mkFx('clip');f.p.bias=%d;f.p.gain=12;x.set(f.p);s.connect(x.in);x.out.connect(oc.destination);s.start()") % (n, SR, X, asym)
        y = offline(js, n)[0][SR // 2:]
        rows.append({'dev': 'clip', 'bias': asym, 'dc_db': db(abs(y.mean())), 'rms_db': db(rms(y))})
        print('clip bias %3d: DC %6.1f dBFS (signal %5.1f dBFS rms)' % (asym, rows[-1]['dc_db'], rows[-1]['rms_db']))
    R['dc'] = rows

json.dump(R, open(OUT, 'w'), indent=1, default=float)
print('page errors', al.errors[-3:])
al.stop()
