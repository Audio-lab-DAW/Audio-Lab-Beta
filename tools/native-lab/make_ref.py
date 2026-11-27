"""Web engine reference for the native test (task NM1, test A).

Runs the real app (index.html) in headless Chromium, builds the Bitcrusher device exactly as the app does
(mkFxNode(c,'crush') in an OfflineAudioContext, the app's own worklet bundle), feeds it ref/crush_in.wav and
writes the output as 32-bit float WAV plus ref/crush_ref.json (settings, and the filter and gain numbers as
JavaScript worked them out, as hex doubles).

    python3 tools/native-lab/make_ref.py            # needs numpy and Playwright Chromium
"""
import base64, json, os, struct, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "remake"))
from alab import AudioLab

SR = 48000
N = 24000  # half a second

CASES = {
    # only + - * / floor and compares: must be the same bits everywhere (both filters off, which the
    # app's own dials cannot do: their lowest value is 200 Hz; the worklet accepts 0 = off)
    "plain":  dict(bits=6, rate=3, jit=0, dith=0, drive=0, mix=100, out=0, aa=0, post=0, shape="round"),
    # exp() and pow() set the filters and gains: depends on the maths library
    "filter": dict(bits=8, rate=2.5, jit=0, dith=0, drive=6, mix=70, out=-3, aa=6000, post=9000, shape="round"),
    # the worklet's seeded random numbers (jitter and dither) and the fold shape
    "dither": dict(bits=5, rate=4, jit=30, dith=50, drive=9, mix=100, out=0, aa=0, post=0, shape="fold"),
}


def wav_write(path, x):  # x: (2, n) float32
    d = np.ascontiguousarray(x.T.astype("<f4")).tobytes()
    with open(path, "wb") as f:
        f.write(b"RIFF" + struct.pack("<I", 36 + len(d)) + b"WAVEfmt " + struct.pack("<IHHIIHH", 16, 3, 2, SR, SR * 8, 8, 32) + b"data" + struct.pack("<I", len(d)) + d)


def make_input():
    # integer-only generator, so the file is the same on every machine
    s = np.uint32(0x13572468)
    out = np.zeros((2, N), dtype=np.float32)
    st = 0x13572468
    for c in range(2):
        acc = 0.0
        for i in range(N):
            st = (st * 1664525 + 1013904223) & 0xFFFFFFFF
            noise = (st >> 8) / 16777216.0 * 2 - 1          # exact in float
            tri = abs(((i * (37 + 11 * c)) % 960) / 480.0 - 1) * 2 - 1   # a 1.85 / 2.4 kHz triangle, exact
            env = 1.0 - (i / N) * 0.75
            out[c, i] = np.float32((tri * 0.6 + noise * 0.25) * env)
    return out


def main():
    os.makedirs(os.path.join(HERE, "ref"), exist_ok=True)
    x = make_input()
    wav_write(os.path.join(HERE, "ref", "crush_in.wav"), x)
    al = AudioLab(os.path.join(ROOT, "index.html")); al.start()
    info = {"app": al.version, "sr": SR, "frames": N, "userAgent": al.js("() => navigator.userAgent"), "cases": {}}
    b64 = base64.b64encode(np.ascontiguousarray(x).tobytes()).decode()
    for name, p in CASES.items():
        r = al.js("""async ({b64, p, N, SR}) => {
            const raw = Uint8Array.from(atob(b64), c => c.charCodeAt(0)), f = new Float32Array(raw.buffer);
            const c = new OfflineAudioContext(2, N, SR), buf = c.createBuffer(2, N, SR);
            buf.copyToChannel(f.subarray(0, N), 0); buf.copyToChannel(f.subarray(N, 2 * N), 1);
            const src = c.createBufferSource(); src.buffer = buf;
            const fx = mkFxNode(c, 'crush'); fx.set(p); await wlLoad(c);
            src.connect(fx.in); fx.out.connect(c.destination); src.start(0);
            const o = await c.startRendering();
            const out = new Float32Array(2 * N); out.set(o.getChannelData(0), 0); out.set(o.getChannelData(1), N);
            const hex = v => { const d = new DataView(new ArrayBuffer(8)); d.setFloat64(0, v); return d.getBigUint64(0).toString(16).padStart(16, '0') };
            const TAU = Math.PI * 2, dB = x => Math.pow(10, x / 20);
            const co = { q: Math.pow(2, Math.max(1, Math.min(24, p.bits || 8)) - 1), dr: dB(p.drive || 0), go: dB(p.out || 0),
                pc: p.aa > 0 ? 1 - Math.exp(-TAU * Math.min(SR * .45, p.aa) / SR) : 1, oc: p.post > 0 ? 1 - Math.exp(-TAU * Math.min(SR * .45, p.post) / SR) : 1 };
            const ch = {}; for (const k in co) ch[k] = hex(co[k]);
            let s = ''; const u = new Uint8Array(out.buffer); for (let i = 0; i < u.length; i += 32768) s += String.fromCharCode.apply(null, u.subarray(i, i + 32768));
            return { out: btoa(s), coef: ch, coefDec: co };
        }""", {"b64": b64, "p": p, "N": N, "SR": SR})
        y = np.frombuffer(base64.b64decode(r["out"]), dtype="<f4").reshape(2, N)
        wav_write(os.path.join(HERE, "ref", "crush_%s_web.wav" % name), y)
        pk = float(np.max(np.abs(y)))
        info["cases"][name] = {"p": p, "coef": r["coef"], "coefDec": r["coefDec"], "peak": pk, "differsFromInput": bool(np.any(y != x))}
        print(name, "peak", pk, "changed", bool(np.any(y != x)), r["coef"])
    al.stop()
    json.dump(info, open(os.path.join(HERE, "ref", "crush_ref.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
