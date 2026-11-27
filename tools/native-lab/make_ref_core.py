"""Web engine references for the native engine core (task NB-N3a).

Runs the real app (index.html) in headless Chromium and renders a test signal through each ported device, once
for the factory settings and once for every preset the app has for it (plus a few settings no preset uses), with
the app's own code: mkFx (a new device as the app makes it), the preset merged in, mkFxNode in an
OfflineAudioContext, the app's worklet bundle. For each case it records the settings exactly as the page posts
them to the worklet (the device's `sp` mapping), which is what the native engine is given.

    python3 tools/native-lab/make_ref_core.py [outdir] [types]   # default outdir tools/native-lab/out/core
writes  in.wav, cases.json, web/<case>.wav, web.json (sha-256 of each web output, the app version, the browser)
"""
import base64, hashlib, json, os, struct, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "remake"))

SR = 48000
N = 128 * 2438  # 312,064 frames, 6.5 s, whole render quanta

TYPES = ["limit", "gate", "trans", "deess", "crush"]
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
}
CHAINS = {
    "chain-drums": [("gate", "kick"), ("trans", "punch"), ("crush", "12bit"), ("limit", "loud")],
    "chain-voice": [("deess", "voc"), ("gate", "room"), ("limit", "trans")],
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


JS = """async ({b64, N, SR, chain}) => {
  const raw = Uint8Array.from(atob(b64), c => c.charCodeAt(0)), f = new Float32Array(raw.buffer);
  const c = new OfflineAudioContext(2, N, SR), buf = c.createBuffer(2, N, SR);
  buf.copyToChannel(f.subarray(0, N), 0); buf.copyToChannel(f.subarray(N, 2 * N), 1);
  const src = c.createBufferSource(); src.buffer = buf;
  const A = window.__alref, posted = [];
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
  return {out: btoa(s), posted};
}"""


def main():
    from alab import AudioLab
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "out", "core")
    types = sys.argv[2].split(",") if len(sys.argv) > 2 else TYPES
    os.makedirs(os.path.join(out, "web"), exist_ok=True)
    x = make_input()
    wav_write(os.path.join(out, "in.wav"), x)
    al = AudioLab(os.path.join(ROOT, "index.html")); al.start()
    al.run("window.__alref={FXPRE,mkFx,mkFxNode,wlLoad};1")
    presets = al.run("(()=>{const o={};for(const t of %s)o[t]=Object.keys(FXPRE[t]||{});return o})()" % json.dumps(types))
    jobs = []
    for t in types:
        jobs.append((t + "-new", [{"type": t}]))
        for k in presets[t]:
            jobs.append((t + "-" + k, [{"type": t, "pre": k}]))
        for k, e in EXTRA.get(t, {}).items():
            jobs.append((t + "-" + k, [{"type": t, "extra": e}]))
    for name, ch in CHAINS.items():
        if all(d in types for d, _ in ch):
            jobs.append((name, [{"type": d, "pre": k} for d, k in ch]))
    b64 = base64.b64encode(np.ascontiguousarray(x).tobytes()).decode()
    cases, info = [], {"app": al.version, "userAgent": al.js("() => navigator.userAgent"), "sr": SR, "frames": N,
                       "input_sha256": hashlib.sha256(np.ascontiguousarray(x).tobytes()).hexdigest(), "cases": {}}
    for name, ch in jobs:
        r = al.js(JS, {"b64": b64, "N": N, "SR": SR, "chain": ch})
        y = np.frombuffer(base64.b64decode(r["out"]), dtype="<f4").reshape(2, N)
        wav_write(os.path.join(out, "web", name + ".wav"), y)
        cases.append({"name": name, "chain": r["posted"]})
        info["cases"][name] = {"sha256": hashlib.sha256(y.tobytes()).hexdigest(), "peak": float(np.max(np.abs(y))),
                               "changed": bool(np.any(y != x))}
        print(name, "peak %.4f" % info["cases"][name]["peak"], "changed" if info["cases"][name]["changed"] else "UNCHANGED", flush=True)
    al.stop()
    json.dump({"sr": SR, "cases": cases}, open(os.path.join(out, "cases.json"), "w"), indent=1)
    json.dump(info, open(os.path.join(out, "web.json"), "w"), indent=1)
    print(len(cases), "cases written to", out)


if __name__ == "__main__":
    main()
