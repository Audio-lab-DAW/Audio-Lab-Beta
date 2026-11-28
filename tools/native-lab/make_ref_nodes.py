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
  // task NB-N3j: automated params, buffer sources, automated gain and biquad
  // Playwright hands a Python 0.0 over as -0: every number is made +0 first (x + 0), as the native side reads it
  const ap = (p, ev) => { for (const e0 of ev) { const e = e0.map(x => typeof x === 'number' ? x + 0 : Array.isArray(x) ? x.map(y => y + 0) : x), k = e[0];
    if (k === 'v') p.value = e[1]; else if (k === 'set') p.setValueAtTime(e[1], e[2]); else if (k === 'lin') p.linearRampToValueAtTime(e[1], e[2]);
    else if (k === 'exp') p.exponentialRampToValueAtTime(e[1], e[2]); else if (k === 'tgt') p.setTargetAtTime(e[1], e[2], e[3]);
    else if (k === 'curve') p.setValueCurveAtTime(new Float32Array(e[1]), e[2], e[3]) } };
  const gen = b => { const B = oc.createBuffer(1, b.len, b.sr), d = B.getChannelData(0); for (let i = 0; i < b.len; i++) d[i] = ((i * 7919 + b.gen * 104729) % 2001 - 1000) / 1000; return B };
  if (c.param || c.src) {
    let last;
    if (c.param) { const one = oc.createConstantSource(); const g = oc.createGain(); if (c.param.krate) g.gain.automationRate = 'k-rate'; ap(g.gain, c.param.ev); one.connect(g); one.start(0); last = g }
    else { const s = oc.createBufferSource(); if (c.src.rate) ap(s.playbackRate, c.src.rate); if (c.src.detune) ap(s.detune, c.src.detune);
      if (c.src.loop) { s.loop = true; s.loopStart = c.src.loop[0]; s.loopEnd = c.src.loop[1] } s.buffer = gen(c.src.buf);
      const st = c.src.start || [0]; s.start(...st); if (c.src.stop != null) s.stop(c.src.stop); last = s;
      if (c.gain) { const g = oc.createGain(); ap(g.gain, c.gain); last.connect(g); last = g }
      if (c.bq) { const f = oc.createBiquadFilter(); f.type = c.bq.type; if (c.bq.freq) ap(f.frequency, c.bq.freq); if (c.bq.q) ap(f.Q, c.bq.q); if (c.bq.gain) ap(f.gain, c.bq.gain); if (c.bq.detune) ap(f.detune, c.bq.detune); last.connect(f); last = f } }
    last.connect(oc.destination);
    const o = await oc.startRendering(), d = o.getChannelData(0);
    let s = ''; const u = new Uint8Array(d.buffer); for (let i = 0; i < u.length; i += 32768) s += String.fromCharCode.apply(null, u.subarray(i, i + 32768));
    return btoa(s);
  }
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


def cases_auto():
    """task NB-N3j: Chromium's AudioParam timeline, AudioBufferSourceNode, automated GainNode and BiquadFilterNode"""
    out = []
    def add(name, **k):
        for sr in (44100, 48000):
            for Q in (128, 512):
                d = dict(name="%s-%d-%d" % (name, sr // 100, Q), sr=sr, quantum=Q, frames=k.pop("frames", None) or sr); d.update(k); out.append(d)
    fade32 = [((i / 31) ** 1.8) for i in range(32)]
    curve128 = [0.3 + 0.7 * abs(((i * 37) % 128) / 127 - 0.5) for i in range(128)]
    P = lambda *ev, **k: dict(param=dict(ev=list(ev), **k))
    add("p-value", **P(["v", 0.5]))
    add("p-value0", **P(["v", 0]))
    add("p-choke", **P(["v", 0.9], ["set", 0.9, 0.4097931034482776], ["lin", 0, 0.4137931034482776]))
    add("p-env", **P(["v", 20000], ["set", 774.5966692414834, 0], ["lin", 985.281318980778, 0.2551724137931034], ["lin", 1261.4463392443804, 0.5103448275862069],
                     ["lin", 1615.0177986111737, 0.7655172413793105], ["lin", 300, 0.77]))
    add("p-lin-frac", **P(["set", 0.25, 0.01234567], ["lin", 1.5, 0.0128], ["lin", -0.75, 0.0131], ["lin", 0.33, 0.5]))
    add("p-lin-first", **P(["lin", 2.0, 0.3]))
    add("p-tgt", **P(["v", 1], ["tgt", 0.1, 0.05, 0.02]))
    add("p-tgt-ramp", **P(["v", 1], ["tgt", 0.2, 0.05, 0.03], ["lin", 0.8, 0.31]))
    add("p-curve", **P(["v", 1], ["set", 0, 0.1234], ["curve", fade32, 0.1234, 0.05], ["curve", list(reversed(fade32)), 0.6, 0.123]))
    add("p-curve128", **P(["set", 0.3, 0.2], ["curve", curve128, 0.2, 0.7]))
    add("p-exp", **P(["v", 0.001], ["set", 0.001, 0.05], ["exp", 1.0, 0.4], ["exp", 0.01, 0.9]))
    add("p-krate", **P(["v", 0.9], ["set", 0.9, 0.11], ["lin", 0.1, 0.35], krate=True))
    add("p-late", **P(["v", 0.7], ["set", 0.2, 0.9]))
    B = lambda sr=None, length=9000, g=1: dict(sr=sr, len=length, gen=g)
    def S(name, buf=None, **k):
        for sr in (44100, 48000):
            for Q in (128, 512):
                b = dict(buf or B()); b["sr"] = b["sr"] or sr
                src = dict(buf=b); src.update(k.get("src", {}))
                d = dict(name="%s-%d-%d" % (name, sr // 100, Q), sr=sr, quantum=Q, frames=sr, src=src)
                for x in ("gain", "bq"):
                    if x in k: d[x] = k[x]
                out.append(d)
    S("s-start0")
    S("s-frac", src=dict(start=[0.38243217]))
    S("s-offset", src=dict(start=[0.1, 0.0371]))
    S("s-dur", src=dict(start=[0.2, 0.05, 0.1]))
    S("s-stop", src=dict(start=[0.05], stop=0.1234))
    S("s-44k", buf=B(sr=44100, length=30000), src=dict(start=[0.0123]))
    S("s-48k", buf=B(sr=48000, length=30000), src=dict(start=[0.0101, 0.01]))
    S("s-rate", buf=B(length=30000), src=dict(rate=[["v", 1.3]], start=[0.02]))
    S("s-rate-auto", buf=B(length=40000), src=dict(rate=[["v", 0.8], ["set", 1.25, 0.2], ["lin", 0.5, 0.6]], start=[0.0]))
    S("s-detune", buf=B(length=30000), src=dict(detune=[["v", -700]], start=[0.01]))
    S("s-loop", buf=B(length=5000), src=dict(loop=[0.01, 0.05], start=[0.0], stop=0.8))
    S("g-choke", buf=B(length=7506), src=dict(start=[0.18233766]), gain=[["v", 0.9], ["set", 0.9, 0.3097931034482776], ["lin", 0, 0.3137931034482776]])
    S("bq-env", buf=B(length=48000), src=dict(start=[0.0]), bq=dict(type="lowpass", q=[["v", 0.9]], freq=[["v", 20000], ["set", 774.5966692414834, 0],
        ["lin", 985.281318980778, 0.2551724137931034], ["lin", 1261.4463392443804, 0.5103448275862069], ["lin", 5448.139854853323, 0.9]]))
    S("bq-q", buf=B(length=48000, g=3), src=dict(start=[0.0]), bq=dict(type="highpass", freq=[["v", 800]], q=[["v", 1], ["lin", 12, 0.6]]))
    S("bq-peak", buf=B(length=48000, g=5), src=dict(start=[0.0]), bq=dict(type="peaking", freq=[["v", 2500]], gain=[["set", -6, 0.1], ["lin", 9, 0.7]]))
    S("bq-fixed-after", buf=B(length=48000, g=7), src=dict(start=[0.0]), bq=dict(type="lowpass", freq=[["v", 3000], ["set", 3000, 0.05], ["lin", 600, 0.2]]))
    S("bq-detune", buf=B(length=48000, g=9), src=dict(start=[0.0]), bq=dict(type="bandpass", freq=[["v", 1000]], detune=[["set", 0, 0.0], ["lin", 1200, 0.5]]))
    return out


def main():
    out = sys.argv[1]
    os.makedirs(os.path.join(out, "web"), exist_ok=True); os.makedirs(os.path.join(out, "native"), exist_ok=True)
    cs = cases() + cases_auto()   # task NB-N3j
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
