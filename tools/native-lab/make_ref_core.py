"""Web engine references for the native engine core (task NB-N3a).

Runs the real app (index.html) in headless Chromium and renders a test signal through each ported device, once
for the factory settings and once for every preset the app has for it (plus a few settings no preset uses), with
the app's own code: mkFx (a new device as the app makes it), the preset merged in, mkFxNode in an
OfflineAudioContext, the app's worklet bundle. For each case it records the settings exactly as the page posts
them to the worklet (the device's `sp` mapping), which is what the native engine is given.

    python3 tools/native-lab/make_ref_core.py [outdir] [types] [quantum]   # default outdir tools/native-lab/out/core
quantum: the render quantum of the offline context (128, as while playing; 512, as the app's export uses)
writes  in.wav, cases.json, web/<case>.wav, web.json (sha-256 of each web output, the app version, the browser)
"""
import base64, hashlib, json, os, struct, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "remake"))

SR = 48000
N = 128 * 2438  # 312,064 frames, 6.5 s, whole render quanta

TYPES = ["limit", "gate", "trans", "deess", "crush", "chorus", "imager", "fshift", "vocoder", "tstop", "eq", "comp", "side", "clip", "drive"]
# settings no preset uses, so each branch of the code runs at least once (merged over the factory settings)
EXTRA = {
    "limit": {"x-punchy-notp": {"style": "punchy", "tp": False, "gain": 8, "look": 1.3},
              "x-aggressive": {"style": "aggressive", "gain": 10, "rel": 5, "look": 7, "ceil": -1.5, "out": -2},
              "x-clean": {"style": "clean", "gain": 6}},
    "gate": {"x-expander": {"mode": "expander", "ratio": 3, "thr": -30, "look": 3},
             "x-listen": {"listen": True, "hpf": 200, "lpf": 3000},
             "x-look": {"look": 5, "hold": 5, "att": 0.05, "rel": 1}},
    "trans": {"x-sustain-up": {"attack": -50, "sustain": 80, "speed": 3},
              "x-zero": {"attack": 0, "sustain": 0, "speed": 0.1, "out": 3}},
    "deess": {"x-wide": {"mode": "wide"}, "x-listen": {"listen": True, "freq": 9000, "q": 0.2},
              "x-high": {"freq": 30000, "att": 0.05, "rel": 0.5, "range": 0}},
    "crush": {"x-fold-dither": {"shape": "fold", "bits": 5, "rate": 4, "jit": 30, "dith": 50, "drive": 9},
              "x-trunc": {"shape": "trunc", "bits": 3, "rate": 7.5}, "x-floor": {"shape": "floor", "bits": 12, "mix": 40}},
    # task NB-N3c
    "chorus": {"x-flanger-tri": {"mode": "flanger", "shape": "triangle", "fb": 60, "depth": 80},
               "x-dimension": {"mode": "dimension", "width": 100}, "x-ensemble-fb": {"mode": "ensemble", "fb": 40, "lowcut": 200, "highcut": 6000}},
    "imager": {"x-solo2": {"solo": 2}, "x-bmono": {"bmono": True, "w4": 180, "sg": 3, "x1": 10, "x2": 50}},
    "fshift": {"x-ring": {"mode": "ring", "shift": 300}, "x-both-down-lfo": {"mode": "both", "dir": "down", "lfoRate": 2, "lfoDepth": 50, "fb": 40},
               "x-negative": {"shift": -120, "mix": 60}},
    "vocoder": {"x-pulse8": {"carrier": "pulse", "bands": 8, "formant": 5}, "x-noise-sib": {"carrier": "sine", "noise": 40, "sib": 60, "detune": 15},
                "x-square32": {"carrier": "square", "bands": 32, "oct": -1, "bw": 0.5}},
    "tstop": {"x-hold-rev": {"hold": True, "fx": "rev"}, "x-hold-stutter": {"hold": True, "fx": "stutter"},
              "x-hold-half": {"hold": True, "fx": "half"}, "x-hold-double": {"hold": True, "fx": "double"}, "x-hold-tape": {"hold": True, "fx": "tape", "stop": 900}},
}
# task NB-N3e: the Pro EQ (browser nodes: Chromium's BiquadFilterNode and GainNode). Settings replace the bands.
def B(t, f, g=0, q=1, on=True, sl=12, pl="st", **k):
    return dict(t=t, f=f, g=g, q=q, on=on, sl=sl, pl=pl, **k)
EXTRA["eq"] = {
    "x-bells": {"bands": [B("peaking", 120, 4.5, 0.8), B("peaking", 900, -6, 2.5), B("peaking", 3200, 3, 0.4), B("peaking", 11000, -9, 6)]},
    "x-shelves": {"bands": [B("lowshelf", 80, 6, 0.7), B("highshelf", 8000, -4.5, 0.7), B("lowshelf", 400, -12), B("highshelf", 2500, 9)], "out": -3.5},
    "x-pass12": {"bands": [B("highpass", 60, q=0.7, sl=12), B("lowpass", 9000, q=0.7, sl=12)]},
    "x-pass24": {"bands": [B("highpass", 35, q=0.7, sl=24), B("lowpass", 15000, q=1.4, sl=24)]},
    "x-pass48": {"bands": [B("highpass", 150, q=2, sl=48), B("lowpass", 4000, q=0.3, sl=48)]},
    "x-pass36-reso": {"bands": [B("highpass", 300, q=8, sl=36), B("lowpass", 6000, q=12, sl=36)]},
    "x-notch-band": {"bands": [B("notch", 1000, q=4), B("bandpass", 2500, q=0.7), B("notch", 50, q=10)]},
    "x-allpass": {"bands": [B("allpass", 700, q=0.5, sl=24)]},
    "x-tilt": {"bands": [B("tilt", 1200, 5), B("tilt", 300, -3)]},
    "x-ms": {"bands": [B("highpass", 200, q=0.7, sl=24, pl="s"), B("peaking", 2000, 4, 1.2, pl="m"), B("highshelf", 9000, 6, pl="s"), B("lowshelf", 100, 3, pl="st")]},
    "x-ms-only-side": {"bands": [B("peaking", 5000, -8, 3, pl="s")], "out": 2},
    "x-solo": {"bands": [B("peaking", 500, 6, 2), B("peaking", 3000, -6, 5, solo=True), B("highpass", 100, sl=24)]},
    "x-gs": {"bands": [B("peaking", 250, 9, 1), B("highshelf", 6000, -6)], "gs": 35},
    "x-auto": {"bands": [B("peaking", 250, 9, 1), B("highshelf", 6000, 6), B("lowshelf", 80, -4)], "auto": True},
    "x-edges": {"bands": [B("peaking", 5, 6, 0.05), B("peaking", 30000, 6, 0.1), B("lowpass", 23990, q=0.7), B("highpass", 1, q=0.7), B("peaking", 1000, 0.00005)]},
    "x-off": {"bands": [B("peaking", 1000, 12, 1, on=False), B("lowpass", 200, on=False)], "out": -6},
    "x-extreme": {"bands": [B("peaking", 60, 24, 0.1), B("peaking", 60, -24, 30), B("lowshelf", 40, 24), B("highshelf", 15000, -24)], "out": -12},
}
_FRX = json.load(open(os.path.join(HERE, "ref", "eq_fractals.json")))["eqs"]
for _i, _e in enumerate(_FRX):
    EXTRA["eq"]["frx%02d" % _i] = _e["p"]
# task NB-N3f: the Compressor (Chromium's DynamicsCompressorNode): the three of Fractals (Kick & Bass, Drums, the
# master), the ends of every range, values past the AudioParams' ranges (clamped by the browser), no compression
EXTRA["comp"] = {
    "frx-kickbass": {"threshold": -10, "ratio": 1.5, "attack": 30, "release": 100, "makeup": 0},
    "frx-drums": {"threshold": -18, "ratio": 2, "attack": 25, "release": 120, "makeup": 1},
    "frx-master": {"threshold": -12, "ratio": 1.5, "attack": 30, "release": 120, "makeup": 0},
    "x-hard": {"threshold": -60, "ratio": 20, "attack": 1, "release": 20, "makeup": 24},
    "x-slow": {"threshold": -30, "ratio": 4, "attack": 200, "release": 1000, "makeup": 6},
    "x-fast-release": {"threshold": -24, "ratio": 8, "attack": 1, "release": 20, "makeup": 0.5},
    "x-past-ranges": {"threshold": -130, "ratio": 35, "attack": 1500, "release": 4000, "makeup": 2},
    "x-none": {"threshold": 0, "ratio": 1, "attack": 10, "release": 200, "makeup": 0},
    "x-odd": {"threshold": -17.3, "ratio": 3.7, "attack": 7.7, "release": 333.3, "makeup": 3.3},
}
# task NB-N3g: the Sidechain device (an oscillator through a wave shaper on a GainNode's gain): Fractals' three
# (Bass, Music, FX), every sync, the shape and depth ends, punch and sustain with their compressors, both at once
EXTRA["side"] = {
    "frx-bass": {"depth": 100, "shape": 24, "punch": 0, "sustain": 0, "sync": "1/4"},
    "frx-music": {"depth": 35, "shape": 40, "punch": 0, "sustain": 0, "sync": "1/4"},
    "frx-fx": {"depth": 25, "shape": 40, "punch": 0, "sustain": 0, "sync": "1/4"},
    "x-16th": {"depth": 80, "shape": 10, "sync": "1/16"}, "x-8th": {"depth": 60, "shape": 30, "sync": "1/8"},
    "x-half": {"depth": 90, "shape": 70, "sync": "1/2"}, "x-dotted": {"depth": 50, "shape": 50, "sync": "1/4 dotted"},
    "x-triplet": {"depth": 70, "shape": 20, "sync": "1/8 triplet"}, "x-free": {"depth": 40, "shape": 60, "sync": "free"},
    "x-zero": {"depth": 0, "shape": 0}, "x-full-short": {"depth": 100, "shape": 1},
    "x-punch": {"depth": 50, "shape": 30, "punch": 60}, "x-sustain": {"depth": 50, "shape": 30, "sustain": 70},
    "x-neg": {"depth": 60, "shape": 30, "punch": -50, "sustain": -40},
}
# task NB-N3g: the Soft Clipper and the Drive (Chromium's WaveShaperNode oversampled 4x, 2x or not, its DelayNode, a
# highpass biquad, GainNodes): Fractals' master clipper, every shape, each oversampling, asymmetry, part-wet mixes
def CL(**k):
    d = dict(gain=6, thr=-4, ceil=-1, bias=0, mix=100, out=0, shape="tanh", os="4x"); d.update(k); return d
EXTRA["clip"] = {
    "frx-master": CL(),
    "x-cubic": CL(shape="cubic", gain=9), "x-sine": CL(shape="sine", thr=-10, ceil=-.5), "x-atan": CL(shape="atan", bias=28, mix=50),
    "x-hard": CL(shape="hard", gain=12, thr=-12), "x-fold": CL(shape="fold", gain=18, thr=-20, ceil=-3, mix=45, out=-1),
    "x-2x": CL(os="2x", gain=10, bias=-20), "x-none": CL(os="none", gain=10, mix=70), "x-mix-half": CL(mix=50, out=3),
    "x-dry": CL(mix=0, gain=3), "x-bias-max": CL(bias=50, shape="tanh", gain=8, mix=80), "x-bias-min": CL(bias=-50, shape="cubic"),
    "x-extreme": CL(gain=24, thr=-24, ceil=-12, out=12),
}
EXTRA["drive"] = {"x-zero": {"drive": 0, "mix": 100}, "x-full": {"drive": 100, "mix": 100}, "x-half-mix": {"drive": 60, "mix": 50},
                  "x-dry": {"drive": 80, "mix": 0}, "x-odd": {"drive": 33.3, "mix": 77.7}}
CHAINS = {
    "chain-drums": [("gate", "kick"), ("trans", "punch"), ("crush", "12bit"), ("limit", "loud")],
    "chain-voice": [("deess", "voc"), ("gate", "room"), ("limit", "trans")],
    "chain-space": [("fshift", None), ("chorus", None), ("imager", None), ("limit", "trans")],
    "chain-robot": [("vocoder", None), ("tstop", None), ("crush", "8bit")],
    # task NB-N3e: the EQ between worklet devices, M/S into a limiter
    "chain-eq-drums": [("gate", "kick"), ("eq", "x-bells"), ("trans", "punch"), ("eq", "x-pass24"), ("limit", "loud")],
    "chain-eq-ms": [("eq", "x-ms"), ("imager", None), ("eq", "x-tilt"), ("limit", "trans")],
    # task NB-N3f: the compressor between worklet devices and EQs, two compressors in a row
    "chain-comp-bus": [("eq", "x-bells"), ("comp", "drums-drum-bus-glue"), ("limit", "loud")],
    "chain-comp-crush": [("crush", "8bit"), ("comp", "x-hard"), ("chorus", None), ("comp", "frx-master")],
    # task NB-N3g: Fractals' Bass chain (EQ, sidechain pump) and the pump between worklet devices
    "chain-side-bass": [("eq", "frx01"), ("side", "frx-bass")],
    "chain-side-mix": [("chorus", None), ("side", "x-8th"), ("limit", "trans")],
    # task NB-N3g: Fractals' master (compressor, then the clipper), and the shapers between worklet devices and an EQ
    "chain-frx-master": [("comp", "frx-master"), ("clip", "frx-master")],
    "chain-shape": [("drive", "x-half-mix"), ("eq", "x-bells"), ("clip", "x-2x"), ("limit", "loud")],
}


def wav_write(path, x):  # x: (2, n) float32
    d = np.ascontiguousarray(x.T.astype("<f4")).tobytes()
    with open(path, "wb") as f:
        f.write(b"RIFF" + struct.pack("<I", 36 + len(d)) + b"WAVEfmt " + struct.pack("<IHHIIHH", 16, 3, 2, SR, SR * 8, 8, 32) + b"data" + struct.pack("<I", len(d)) + d)


def make_input():
    """Drum hits louder than full scale, a voice with sibilants, a tail that decays into the range the
    engine's tiny-value guard sets to zero, 3.3 s of exact silence (the worklets stop on silence after 3 s),
    then hits again."""
    rng = np.random.default_rng(20261127)
    t = np.arange(N) / SR
    x = np.zeros((2, N))
    def hits(t0, t1, every, amp):
        for k, h in enumerate(np.arange(t0, t1, every)):
            i0 = int(h * SR); n = min(int(0.18 * SR), N - i0); tt = np.arange(n) / SR
            ph = 2 * np.pi * (45 * tt + 90 * (1 - np.exp(-tt * 30)) / 30)
            body = np.sin(ph) * np.exp(-tt * 18)
            click = rng.standard_normal(n) * np.exp(-tt * 300) * 0.6
            a = amp * (0.7 + 0.3 * ((k * 7) % 5) / 4)
            x[0, i0:i0 + n] += a * (body + click)
            x[1, i0:i0 + n] += a * (0.92 * body + click * 0.8)
    hits(0.0, 1.6, 0.2, 1.35)
    # voice: a buzzy tone with a slow level ride from -50 to -6 dB, sibilant noise bursts
    v0, v1 = int(1.6 * SR), int(2.6 * SR); tv = t[v0:v1] - 1.6
    lvl = 10 ** ((-50 + 44 * np.abs(np.sin(np.pi * tv * 2.5))) / 20)
    tone = sum(np.sin(2 * np.pi * 180 * h * tv) / h for h in range(1, 12))
    x[0, v0:v1] += 0.5 * lvl * tone; x[1, v0:v1] += 0.45 * lvl * tone
    for s0 in (1.75, 2.05, 2.35):
        i0 = int(s0 * SR); n = int(0.09 * SR)
        nz = rng.standard_normal((2, n)); nz = np.diff(np.diff(nz, prepend=0), prepend=0)  # tilted to the highs
        x[:, i0:i0 + n] += 0.12 * nz * np.hanning(n)
    # tail into tiny values: 2.6 to 2.7 s, from 1e-3 down to about 1e-36
    i0, i1 = int(2.6 * SR), int(2.7 * SR); n = i1 - i0
    tail = 1e-3 * np.exp(np.linspace(0, np.log(1e-33), n)) * np.sin(2 * np.pi * 300 * np.arange(n) / SR)
    x[0, i0:i1] = tail; x[1, i0:i1] = -tail
    # 2.7 to 6.0 s: exact silence; 6.0 s to the end: hits again
    hits(6.0, 6.45, 0.15, 1.1)
    return x.astype(np.float32)


JS = """async ({b64, N, SR, chain, Q}) => {
  const raw = Uint8Array.from(atob(b64), c => c.charCodeAt(0)), f = new Float32Array(raw.buffer);
  const c = Q === 128 ? new OfflineAudioContext(2, N, SR) : new OfflineAudioContext({numberOfChannels: 2, length: N, sampleRate: SR, renderSizeHint: Q});
  if (Q !== 128 && c.renderQuantumSize !== Q) throw new Error('render quantum ' + c.renderQuantumSize + ', asked for ' + Q);
  const buf = c.createBuffer(2, N, SR);
  buf.copyToChannel(f.subarray(0, N), 0); buf.copyToChannel(f.subarray(N, 2 * N), 1);
  const src = c.createBufferSource(); src.buffer = buf;
  const A = window.__alref, posted = [];
  A.setB0(0);   // the beat the render starts at, read by the Sidechain device when it is made
  const bpm = A.bpm();   // the song's tempo as the devices read it now (the app may still be opening Fractals)
  let prev = src;
  for (const d of chain) {
    const q = A.mkFx(d.type).p;
    if (d.pre) { const e = (A.FXPRE[d.type] || {})[d.pre]; if (!e) throw new Error('no preset ' + d.type + ' ' + d.pre); Object.assign(q, JSON.parse(JSON.stringify(e[1]))); q.pre = d.pre }
    if (d.extra) Object.assign(q, d.extra);
    const fx = A.mkFxNode(c, d.type); fx.set(q);
    posted.push({type: d.type, p: JSON.parse(JSON.stringify(fx.sp ? fx.sp(q) : q))});
    prev.connect(fx.in); prev = fx.out;
  }
  await A.wlLoad(c);
  prev.connect(c.destination); src.start(0);
  const o = await c.startRendering();
  const out = new Float32Array(2 * N); out.set(o.getChannelData(0), 0); out.set(o.getChannelData(1), N);
  let s = ''; const u = new Uint8Array(out.buffer); for (let i = 0; i < u.length; i += 32768) s += String.fromCharCode.apply(null, u.subarray(i, i + 32768));
  return {out: btoa(s), posted, bpm};
}"""


def main():
    from alab import AudioLab
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "out", "core")
    types = sys.argv[2].split(",") if len(sys.argv) > 2 and sys.argv[2] else TYPES
    Q = int(sys.argv[3]) if len(sys.argv) > 3 else 128
    os.makedirs(os.path.join(out, "web"), exist_ok=True)
    x = make_input()
    wav_write(os.path.join(out, "in.wav"), x)
    al = AudioLab(os.path.join(ROOT, "index.html")); al.start()
    al.run("window.__alref={FXPRE,mkFx,mkFxNode,wlLoad,setB0:v=>{SIDE_B0=v},bpm:()=>S.bpm};1")   # SIDE_B0: the app's own background renders move it (task NB-N3g)
    presets = al.run("(()=>{const o={};for(const t of %s)o[t]=Object.keys(FXPRE[t]||{});return o})()" % json.dumps(types))
    jobs = []
    for t in types:
        jobs.append((t + "-new", [{"type": t}]))
        for k in presets[t]:
            jobs.append((t + "-" + k, [{"type": t, "pre": k}]))
        for k, e in EXTRA.get(t, {}).items():
            jobs.append((t + "-" + k, [{"type": t, "extra": e}]))  # (x- extras and, for the EQ, frxNN: the song's own)
    for name, ch in CHAINS.items():
        if all(d in types for d, _ in ch):
            jobs.append((name, [({"type": d, "extra": EXTRA[d][k]} if k and k in EXTRA.get(d, {}) else {"type": d, "pre": k} if k else {"type": d}) for d, k in ch]))
    b64 = base64.b64encode(np.ascontiguousarray(x).tobytes()).decode()
    bpm = al.run("S.bpm"); beat0 = al.run("SIDE_B0||0")
    cases, info = [], {"bpm": bpm, "beat0": beat0, "quantum": Q, "app": al.version, "userAgent": al.js("() => navigator.userAgent"), "sr": SR, "frames": N,
                       "input_sha256": hashlib.sha256(np.ascontiguousarray(x).tobytes()).hexdigest(), "cases": {}}
    for name, ch in jobs:
        r = al.js(JS, {"b64": b64, "N": N, "SR": SR, "chain": ch, "Q": Q})
        y = np.frombuffer(base64.b64decode(r["out"]), dtype="<f4").reshape(2, N)
        wav_write(os.path.join(out, "web", name + ".wav"), y)
        cases.append({"name": name, "chain": r["posted"], "bpm": r["bpm"]})
        info["cases"][name] = {"sha256": hashlib.sha256(y.tobytes()).hexdigest(), "peak": float(np.max(np.abs(y))),
                               "changed": bool(np.any(y != x))}
        print(name, "peak %.4f" % info["cases"][name]["peak"], "changed" if info["cases"][name]["changed"] else "UNCHANGED", flush=True)
    al.stop()
    json.dump({"sr": SR, "quantum": Q, "bpm": bpm, "beat0": beat0, "cases": cases}, open(os.path.join(out, "cases.json"), "w"), indent=1)
    json.dump(info, open(os.path.join(out, "web.json"), "w"), indent=1)
    print(len(cases), "cases written to", out)


if __name__ == "__main__":
    main()
