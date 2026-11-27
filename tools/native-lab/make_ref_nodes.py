"""Web references for Chromium's source nodes and wave shaper on their own (task NB-N3g).

    python3 tools/native-lab/make_ref_nodes.py outdir        # writes cases.json and web/<case>.wav
    build/alnodes outdir/cases.json outdir/native && python3 tools/native-lab/compare_nodes.py outdir

Plain Chromium (no app needed): an OfflineAudioContext with one OscillatorNode (or ConstantSourceNode), set as the
case says, optionally into a WaveShaperNode, rendered mono. Covers the four waveforms at frequencies that reach
each interpolation path (5-point under 0.16 table steps a frame, 3-point to 0.3, the 4-frame kernel above), start
times between frames, stops, detune, the edges (0 Hz, negative, Nyquist), 44.1, 48 and 96 kHz, quanta 128 and 512.
"""
import base64, hashlib, json, os, struct, sys
import numpy as np
from playwright.sync_api import sync_playwright

JS = r"""async (c) => {
  const oc = c.quantum === 128 ? new OfflineAudioContext(1, c.frames, c.sr) : new OfflineAudioContext({numberOfChannels: 1, length: c.frames, sampleRate: c.sr, renderSizeHint: c.quantum});
  let src;
  if (c.osc) { src = oc.createOscillator(); src.type = c.osc.type; src.frequency.value = c.osc.freq; src.detune.value = c.osc.detune || 0;
               src.start(c.osc.start || 0); if (c.osc.stop != null) src.stop(c.osc.stop) }
  else { src = oc.createConstantSource(); src.offset.value = c.const.offset; src.start(c.const.start || 0); if (c.const.stop != null) src.stop(c.const.stop) }
  let last = src;
  if (c.shape) { const ws = oc.createWaveShaper(); ws.curve = new Float32Array(c.shape.curve); last.connect(ws); last = ws }
  last.connect(oc.destination);
  const o = await oc.startRendering(), d = o.getChannelData(0);
  let s = ''; const u = new Uint8Array(d.buffer); for (let i = 0; i < u.length; i += 32768) s += String.fromCharCode.apply(null, u.subarray(i, i + 32768));
  return btoa(s);
}"""


def wav_write(path, sr, x):
    d = np.ascontiguousarray(x.astype("<f4")).tobytes()
    with open(path, "wb") as f:
        f.write(b"RIFF" + struct.pack("<I", 36 + len(d)) + b"WAVEfmt " + struct.pack("<IHHIIHH", 16, 3, 1, sr, sr * 4, 4, 32) + b"data" + struct.pack("<I", len(d)) + d)


def side_curve(depth, shape):   # the Sidechain device's curve (mkFxNode 'side' in index.html)
    d, rel, N = depth / 100, max(.05, shape / 100), 512
    cv = []
    for j in range(N):
        x = j / (N - 1) * 2 - 1; ph = x / 2 if x >= 0 else 1 + x / 2; e = (1 - ph / rel) ** 2 if ph < rel else 0
        cv.append(float(np.float32(1 - d * e)))
    return cv


def cases():
    out = []
    def add(name, **k):
        c = {"name": name, "sr": 48000, "quantum": 128, "frames": 48000}; c.update(k); out.append(c)
    for t in ("sine", "square", "sawtooth", "triangle"):
        for f in (0.5, 2.4166666666666665, 9.666666666666666, 110, 440, 1234.5, 5000, 15000):
            add("%s-%g" % (t, f), osc={"type": t, "freq": f})
    add("saw-start-between", osc={"type": "sawtooth", "freq": 2.4166666666666665, "start": 0.01 + 0.4137931034482759})
    add("saw-start-odd", osc={"type": "sawtooth", "freq": 440, "start": 0.123456789})
    add("saw-stop", osc={"type": "sawtooth", "freq": 300, "start": 0.05, "stop": 0.7777777})
    add("sine-detune", osc={"type": "sine", "freq": 440, "detune": 37})
    add("square-negative", osc={"type": "square", "freq": -220})
    add("tri-zero", osc={"type": "triangle", "freq": 0})
    add("saw-nyquist", osc={"type": "sawtooth", "freq": 30000})
    add("saw-44k", sr=44100, frames=44100, osc={"type": "sawtooth", "freq": 2.4166666666666665})
    add("saw-96k", sr=96000, frames=96000, osc={"type": "sawtooth", "freq": 333})
    add("sine-22k", sr=22050, frames=22050, osc={"type": "sine", "freq": 1000})
    add("saw-q512", quantum=512, osc={"type": "sawtooth", "freq": 9.666666666666666, "start": 0.0137})
    add("saw-q512-slow", quantum=512, osc={"type": "sawtooth", "freq": 2.4166666666666665, "start": 0.4237931})
    # a start inside the first quantum, where the values just set make the params sample-accurate
    add("saw-start-q0", osc={"type": "sawtooth", "freq": 440, "start": 0.0013})
    add("sine-start-q0-detune", osc={"type": "sine", "freq": 9.666666666666666, "detune": -500, "start": 0.00071})
    add("tri-q512-start0", quantum=512, osc={"type": "triangle", "freq": 777, "detune": 3})
    add("const-stop", **{"const": {"offset": 1, "stop": 0.4237931}})
    add("const-start-stop", **{"const": {"offset": 0.75, "start": 0.1, "stop": 0.333333}})
    add("shape-pump", osc={"type": "sawtooth", "freq": 2.4166666666666665, "start": 0.4237931}, shape={"curve": side_curve(100, 24)})
    add("shape-pump-fast", osc={"type": "sawtooth", "freq": 9.666666666666666, "start": 0.0137}, shape={"curve": side_curve(35, 40)})
    add("shape-silent-src", osc={"type": "sawtooth", "freq": 2.4, "start": 0.9}, shape={"curve": side_curve(25, 40)})
    return out


def main():
    out = sys.argv[1]
    os.makedirs(os.path.join(out, "web"), exist_ok=True); os.makedirs(os.path.join(out, "native"), exist_ok=True)
    cs = cases()
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(); pg.goto("about:blank")
        ua = pg.evaluate("navigator.userAgent")
        for c in cs:
            x = np.frombuffer(base64.b64decode(pg.evaluate(JS, c)), dtype="<f4")
            wav_write(os.path.join(out, "web", c["name"] + ".wav"), c["sr"], x)
        b.close()
    json.dump({"userAgent": ua, "cases": cs}, open(os.path.join(out, "cases.json"), "w"))
    print(len(cs), "node cases,", ua)


if __name__ == "__main__":
    main()
