"""Web engine references for the native engine core (task NB-N3b): the mixer.

Runs the real app (index.html) in headless Chromium and builds each scene the way the app's export does
(renderMix): an OfflineAudioContext with the export's render size, a master GainNode, and per track in project
order input GainNode -> devices (mkFxNode, the app's own worklets) -> volume GainNode -> StereoPannerNode ->
master. Writes the inputs, the web renders and one scene file per case for almix to ref/mix/.

    python3 tools/native-lab/make_mix_ref.py      # needs numpy and Playwright Chromium
"""
import base64, json, os, struct, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "remake"))
from alab import AudioLab

SR = 48000
N = 12000            # a quarter of a second: enough for 23 quanta of 512 and 93 of 128
OUT = os.path.join(HERE, "ref", "mix")

CRUSH_FILTER = dict(bits=8, rate=2.5, jit=0, dith=0, drive=6, mix=70, out=-3, aa=6000, post=9000, shape="round")
CRUSH_DITHER = dict(bits=5, rate=4, jit=30, dith=50, drive=9, mix=100, out=0, aa=0, post=0, shape="fold")

# name: (quantum, master, [(input, vol, pan, [devices])])
CASES = {
    "one":      (512, 0.7, [("st_a", 0.8, -0.3, [])]),
    "two":      (512, 1.0, [("st_a", 0.8, 0.25, []), ("st_b", 1.3, -0.6, [])]),
    "pans":     (512, 0.5, [("st_a", 0.9, -1.0, []), ("st_b", 0.6, -0.37, []), ("st_c", 1.1, 0.0, []), ("st_a", 0.33, 0.5, []), ("st_b", 0.75, 1.0, [])]),
    "mono":     (512, 0.8, [("mono_a", 0.7, 0.25, []), ("mono_b", 1.2, -0.6, [])]),
    "mixed":    (128, 0.9, [("mono_a", 0.5, 0.0, []), ("st_c", 0.8, 0.8, [])]),
    "silent":   (512, 0.8, [("st_a", 0.0, 0.2, []), ("st_b", 0.9, 0.1, [])]),
    "crushone": (512, 1.0, [("st_a", 1.3, 0.4, [CRUSH_FILTER])]),
    "crushdry": (512, 1.0, [("st_a", 1.0, 0.0, [CRUSH_FILTER])]),
    "crush":    (512, 0.6, [("st_a", 1.3, 0.4, [CRUSH_FILTER]), ("st_b", 0.9, -0.2, [])]),
    "crush128": (128, 0.6, [("st_a", 1.3, 0.4, [CRUSH_FILTER]), ("st_c", 0.7, 0.3, [CRUSH_DITHER])]),
}


def wav_write(path, x):  # x: (ch, n) float32
    ch = x.shape[0]
    d = np.ascontiguousarray(x.T.astype("<f4")).tobytes()
    with open(path, "wb") as f:
        f.write(b"RIFF" + struct.pack("<I", 36 + len(d)) + b"WAVEfmt " + struct.pack("<IHHIIHH", 16, 3, ch, SR, SR * 4 * ch, 4 * ch, 32) + b"data" + struct.pack("<I", len(d)) + d)


def gen(seed, ch, f1, f2):
    # integer generator and exact shapes, so the inputs are the same on every machine
    out = np.zeros((ch, N), dtype=np.float32); st = seed
    for c in range(ch):
        for i in range(N):
            st = (st * 1664525 + 1013904223) & 0xFFFFFFFF
            noise = (st >> 8) / 16777216.0 * 2 - 1
            tri = abs(((i * (f1 + f2 * c)) % 960) / 480.0 - 1) * 2 - 1
            out[c, i] = np.float32((tri * 0.55 + noise * 0.3) * (1.0 - (i / N) * 0.6))
    return out


INPUTS = {"st_a": gen(0x13572468, 2, 37, 11), "st_b": gen(0x2468ace1, 2, 23, 7), "st_c": gen(0x0badf00d, 2, 51, 5),
          "mono_a": gen(0x31415926, 1, 29, 0), "mono_b": gen(0x27182818, 1, 61, 0)}


JS = """async ({spec, b64, N, SR}) => {
            const oc = spec.Q > 128 ? new OfflineAudioContext({numberOfChannels: 2, length: N, sampleRate: SR, renderSizeHint: spec.Q}) : new OfflineAudioContext(2, N, SR);
            await wlLoad(oc);
            const mst = oc.createGain(); mst.gain.value = spec.master; mst.connect(oc.destination);
            const coefs = [], pns = [];
            for (const t of spec.tracks) {
                const raw = Uint8Array.from(atob(b64[t.in]), c => c.charCodeAt(0)), f = new Float32Array(raw.buffer);
                const buf = oc.createBuffer(t.ch, N, SR); for (let c = 0; c < t.ch; c++) buf.copyToChannel(f.subarray(c * N, (c + 1) * N), c);
                const tin = oc.createGain(), vol = oc.createGain(), pn = oc.createStereoPanner(); vol.gain.value = t.vol; pn.pan.value = t.pan;
                let prev = tin;
                for (const p of t.fx) { const x = mkFxNode(oc, 'crush'); x.set(p); prev.connect(x.in); prev = x.out;
                    const hex = v => { const d = new DataView(new ArrayBuffer(8)); d.setFloat64(0, v); return d.getBigUint64(0).toString(16).padStart(16, '0') };
                    const TAU = Math.PI * 2, dB = x => Math.pow(10, x / 20);
                    coefs.push([hex(Math.pow(2, Math.max(1, Math.min(24, p.bits || 8)) - 1)), hex(dB(p.drive || 0)), hex(dB(p.out || 0)),
                        hex(p.aa > 0 ? 1 - Math.exp(-TAU * Math.min(SR * .45, p.aa) / SR) : 1), hex(p.post > 0 ? 1 - Math.exp(-TAU * Math.min(SR * .45, p.post) / SR) : 1)].join(',')) }
                prev.connect(vol); vol.connect(pn); pns.push(pn);
                const src = oc.createBufferSource(); src.buffer = buf; src.connect(tin); src.start(0);
            }
            for (const pn of pns) pn.connect(mst);          // the export connects the tracks to the master in project order, after building them
            const o = await oc.startRendering();
            const out = new Float32Array(2 * N); out.set(o.getChannelData(0), 0); out.set(o.getChannelData(1), N);
            let s = ''; const u = new Uint8Array(out.buffer); for (let i = 0; i < u.length; i += 32768) s += String.fromCharCode.apply(null, u.subarray(i, i + 32768));
            return { out: btoa(s), coefs, quantum: o.length && oc.renderQuantumSize || 128 };
        }"""


def main():
    os.makedirs(OUT, exist_ok=True)
    for k, x in INPUTS.items():
        wav_write(os.path.join(OUT, "in_%s.wav" % k), x)
    al = AudioLab(os.path.join(ROOT, "index.html")); al.start()
    info = {"app": al.version, "sr": SR, "frames": N, "userAgent": al.js("() => navigator.userAgent"), "cases": {}}
    b64 = {k: base64.b64encode(np.ascontiguousarray(x).tobytes()).decode() for k, x in INPUTS.items()}
    for name, (Q, master, tracks) in CASES.items():
        spec = {"Q": Q, "master": master, "tracks": [{"in": i, "ch": INPUTS[i].shape[0], "vol": v, "pan": p, "fx": fx} for i, v, p, fx in tracks]}
        render = lambda: al.js(JS, {"spec": spec, "b64": b64, "N": N, "SR": SR})
        r = render(); r2 = render()   # twice: is the web engine's own render the same bits each time?
        y = np.frombuffer(base64.b64decode(r["out"]), dtype="<f4").reshape(2, N)
        y2 = np.frombuffer(base64.b64decode(r2["out"]), dtype="<f4").reshape(2, N)
        rep = int(np.count_nonzero(y.view("<u4") != y2.view("<u4")))
        wav_write(os.path.join(OUT, "web_%s.wav" % name), y)
        lines = [json.dumps({"sr": SR, "frames": N, "quantum": Q, "master": master})]
        ci = 0
        for i, v, p, fx in tracks:
            lines.append(json.dumps({"track": i, "in": "in_%s.wav" % i, "vol": v, "pan": p}))
            for d in fx:
                lines.append(json.dumps({"device": "crush", "bits": d["bits"], "rate": d["rate"], "jit": d["jit"], "dith": d["dith"], "drive": d["drive"], "mix": d["mix"],
                                         "out": d["out"], "pre": d["aa"], "post": d["post"], "shape": d["shape"], "coef": r["coefs"][ci]})); ci += 1
        open(os.path.join(OUT, "scene_%s.txt" % name), "w").write("\n".join(lines) + "\n")
        info["cases"][name] = {"quantum": Q, "webQuantum": r["quantum"], "master": master, "tracks": len(tracks), "peak": float(np.max(np.abs(y))),
                              "webRendersTwiceSame": rep == 0, "webSamplesDifferingBetweenTwoRenders": rep}
        print(name, info["cases"][name])
    al.stop()
    json.dump(info, open(os.path.join(OUT, "mix_ref.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
