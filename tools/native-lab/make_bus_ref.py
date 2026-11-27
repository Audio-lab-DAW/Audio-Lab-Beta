"""Web engine references for the native mixer's buses (task NB-N3d): groups, sends, returns, the master's chain,
delay compensation, muted and soloed tracks.

Runs the real app (index.html) in headless Chromium and builds each scene the way the app's export routes it
(renderMix): per track that is heard, in project order, input GainNode -> its devices (mkFxNode, the app's
worklets) -> a DelayNode when delay compensation asks for one (pdc, from the app's own fxLat) -> volume GainNode
-> StereoPannerNode; then each track's pan into its group's input (or the master), and each send as a GainNode
from the track's pan into the return's input; the master GainNode -> the master's devices -> the output.
Tracks that are not heard (muted, or not soloed) are not built, as in renderMix. The sources are buffers
connected straight to the track's input (clips come in a later part).

For every device it records the settings exactly as the page posts them to the worklet (the device's `sp`
mapping), which is what the native engine is given. Each scene is rendered twice: with three or more
connections into one bus, Chromium's own order of summing them changes between renders (N3b), so the web
engine is not always the same bits as itself; the scene says so.

    python3 tools/native-lab/make_bus_ref.py [outdir] [scene,scene]   # default tools/native-lab/ref/bus, every scene
writes in_<name>.wav, scene_<name>.json (for albus), web_<name>.wav, bus_ref.json
"""
import base64, json, os, struct, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "remake"))
sys.path.insert(0, HERE)
from make_mix_ref import gen, wav_write as _wav_write_mono_or_stereo  # same inputs as N3b

SR = 48000
N = 24000            # half a second: 46 quanta of 512, 187 of 128

INPUTS = {"st_a": gen(0x13572468, 2, 37, 11), "st_b": gen(0x2468ace1, 2, 23, 7), "st_c": gen(0x0badf00d, 2, 51, 5),
          "st_d": gen(0x5eed1234, 2, 19, 13), "mono_a": gen(0x31415926, 1, 29, 0), "mono_b": gen(0x27182818, 1, 61, 0)}
# gen() makes N3b's 12000 frames; these scenes are longer, so the inputs are repeated
INPUTS = {k: np.tile(v, (1, (N + v.shape[1] - 1) // v.shape[1]))[:, :N].astype(np.float32) for k, v in INPUTS.items()}


def T(i, src=None, kind=None, vol=1.0, pan=0.0, grp=None, sends=None, fx=(), mute=False, solo=False):
    return {"id": i, "kind": kind or "audio", "src": src, "vol": vol, "pan": pan, "grp": grp, "sends": sends or {},
            "fx": [fxd(f) for f in fx], "mute": mute, "solo": solo}


def fxd(f):  # ("type", "preset"), ("type", None, {settings merged in}) or "type"
    if not isinstance(f, tuple): return {"type": f}
    d = {"type": f[0]}
    if f[1]: d["pre"] = f[1]
    if len(f) > 2: d["extra"] = f[2]
    return d


# task NB-N3e: Pro EQ settings (see make_ref_core.py EXTRA["eq"])
def _B(t, f, g=0, q=1, on=True, sl=12, pl="st"):
    return dict(t=t, f=f, g=g, q=q, on=on, sl=sl, pl=pl)
EQ_BELLS = {"bands": [_B("peaking", 120, 4.5, 0.8), _B("peaking", 900, -6, 2.5), _B("peaking", 3200, 3, 0.4)]}
EQ_PASS = {"bands": [_B("highpass", 80, q=0.7, sl=24), _B("lowpass", 7000, q=1.2, sl=12)], "out": 1.5}
EQ_MS = {"bands": [_B("highpass", 200, q=0.7, sl=24, pl="s"), _B("peaking", 2000, 4, 1.2, pl="m"), _B("lowshelf", 100, 3)]}
EQ_SIDE = {"bands": [_B("peaking", 5000, -8, 3, pl="s"), _B("highshelf", 9000, 5, pl="m")], "out": 2}
EQ_TILT = {"bands": [_B("tilt", 1200, 5)], "auto": True}
EQ_SHELF = {"bands": [_B("lowshelf", 60, 2), _B("highshelf", 12000, -1.5)], "out": -0.5}


# name: (quantum, master gain, master devices, tracks in project order)
SCENES = {
    "group2": (512, 0.8, [], [T("g", kind="group", vol=0.9, pan=0.2), T("a", "st_a", vol=0.7, pan=-0.4, grp="g"), T("b", "st_b", vol=1.1, pan=0.3, grp="g")]),
    "groupfx": (512, 1.0, [], [T("g", kind="group", vol=0.8, pan=-0.1, fx=[("chorus", None), ("limit", "loud")]),
                               T("a", "st_a", vol=0.9, pan=0.5, grp="g", fx=[("crush", "12bit")]), T("b", "mono_a", vol=0.6, grp="g")]),
    "nested": (128, 0.9, [], [T("g1", kind="group", vol=0.85, pan=0.25), T("g2", kind="group", vol=1.2, pan=-0.3, grp="g1", fx=[("imager", None)]),
                              T("a", "st_c", vol=0.5, pan=0.1, grp="g2"), T("b", "st_a", vol=0.75, grp="g1")]),
    "send": (512, 0.7, [], [T("a", "st_a", vol=0.8, pan=-0.2, sends={"r": 0.5}), T("r", kind="return", vol=0.9, fx=[("chorus", None)])]),
    "send2": (128, 0.6, [], [T("a", "st_b", vol=0.8, pan=0.6, sends={"r": 0.35}), T("b", "mono_b", vol=0.9, pan=-0.5, sends={"r": 0.8}),
                             T("r", kind="return", vol=0.7, pan=0.1, fx=[("fshift", None)])]),
    "master": (512, 0.6, [("imager", None), ("limit", "trans")], [T("a", "st_a", vol=0.9, pan=0.2), T("b", "st_d", vol=0.8, pan=-0.7)]),
    "pdc": (512, 1.0, [], [T("a", "st_a", vol=0.8, pan=-0.3, fx=[("limit", "loud")]), T("b", "st_b", vol=0.9, pan=0.4)]),
    "pdcgrp": (512, 0.9, [], [T("g", kind="group", vol=0.9, fx=[("gate", "kick")]), T("a", "st_c", vol=0.8, grp="g", fx=[("limit", "trans")]),
                              T("b", "st_b", vol=0.7, pan=0.5)]),
    "mute": (512, 1.0, [], [T("a", "st_a", vol=0.8), T("b", "st_b", vol=0.9, mute=True), T("c", "st_c", vol=0.6, pan=0.4)]),
    "solo": (512, 1.0, [], [T("g", kind="group", vol=0.9), T("a", "st_a", vol=0.8, grp="g", solo=True), T("b", "st_b", vol=0.9, grp="g"),
                            T("c", "st_c", vol=0.6, sends={"r": 0.5}), T("r", kind="return", vol=0.8, fx=[("chorus", None)])]),
    "mutedgroup": (512, 1.0, [], [T("g", kind="group", vol=0.9, mute=True), T("a", "st_a", grp="g"), T("b", "st_d", vol=0.7, pan=-0.2)]),
    # three or more connections into one bus: Chromium's summing order is its own (see the docstring)
    "song": (512, 0.75, [("limit", "trans")],
             [T("drums", kind="group", vol=0.9, fx=[("trans", "punch")]), T("k", "mono_a", vol=1.0, grp="drums", fx=[("gate", "kick")]),
              T("h", "st_c", vol=0.5, pan=0.3, grp="drums", sends={"rv": 0.2}),
              T("music", kind="group", vol=0.8, pan=-0.05), T("bs", "mono_b", vol=0.9, grp="music"),
              T("ld", "st_a", vol=0.7, pan=-0.35, grp="music", fx=[("chorus", None)], sends={"rv": 0.4}),
              T("rv", kind="return", vol=0.6, fx=[("imager", None)])]),
}
SCENES["song128"] = (128,) + SCENES["song"][1:]
# task NB-N3e: the Pro EQ on the buses: stereo, a mono source kept mono through it, mid/side on a group and on a mono
# source (its splitter gives silence on the right), a return with tilt and auto gain, the master's EQ before its limiter
SCENES["eqbus"] = (512, 0.8, [("eq", None, EQ_SHELF), ("limit", "trans")],
                   [T("g", kind="group", vol=0.9, pan=0.1, fx=[("eq", None, EQ_MS)]), T("a", "st_a", vol=0.7, pan=-0.3, grp="g", fx=[("eq", None, EQ_BELLS)]),
                    T("m", "mono_a", vol=0.8, pan=0.4, fx=[("eq", None, EQ_PASS)], sends={"r": 0.4}),
                    T("ms", "mono_b", vol=0.6, pan=-0.2, fx=[("eq", None, EQ_SIDE)]),
                    T("r", kind="return", vol=0.7, fx=[("eq", None, EQ_TILT)])])
SCENES["eqbus128"] = (128,) + SCENES["eqbus"][1:]
# every ported device somewhere on the buses, two levels of groups, two returns, delay compensation from a limiter
SCENES["wide"] = (512, 0.7, [("imager", None), ("limit", "loud")],
                  [T("bus", kind="group", vol=0.9, pan=0.05, fx=[("deess", "voc")]), T("sub", kind="group", vol=0.95, grp="bus", fx=[("tstop", None)]),
                   T("v1", "st_a", vol=0.6, pan=-0.6, grp="sub", fx=[("gate", "room"), ("trans", "punch")], sends={"r1": 0.3, "r2": 0.15}),
                   T("v2", "st_d", vol=0.7, pan=0.6, grp="sub", fx=[("limit", "loud")], sends={"r1": 0.25}),
                   T("v3", "mono_b", vol=0.8, grp="bus", fx=[("fshift", None)]),
                   T("r1", kind="return", vol=0.5, fx=[("chorus", None)]), T("r2", kind="return", vol=0.4, pan=0.3, fx=[("vocoder", None)])])

JS = r"""async ({sc, b64, N, SR}) => {
  const A = window.__alref;
  const oc = sc.Q > 128 ? new OfflineAudioContext({numberOfChannels: 2, length: N, sampleRate: SR, renderSizeHint: sc.Q}) : new OfflineAudioContext(2, N, SR);
  await A.wlLoad(oc);
  const posted = {}, mk = (d, owner) => { const q = A.mkFx(d.type).p;
      if (d.pre) { const e = (A.FXPRE[d.type] || {})[d.pre]; if (!e) throw new Error('no preset ' + d.type + ' ' + d.pre); Object.assign(q, JSON.parse(JSON.stringify(e[1]))); q.pre = d.pre }
      if (d.extra) Object.assign(q, JSON.parse(JSON.stringify(d.extra)));
      const x = A.mkFxNode(oc, d.type); x.set(q); (posted[owner] = posted[owner] || []).push({type: d.type, p: JSON.parse(JSON.stringify(x.sp ? x.sp(q) : q)), lat: A.fxLat({type: d.type, on: true, p: q}, SR)}); return x };
  // renderMix: the master
  const mst = oc.createGain(); mst.gain.value = sc.master; let out = mst;
  for (const d of sc.mfx) { const x = mk(d, '@master'); out.connect(x.in); out = x.out }
  out.connect(oc.destination);
  const byId = new Map(sc.tracks.map(t => [t.id, t]));
  const grpOf = t => { const g = t.grp && byId.get(t.grp); return g && g.kind === 'group' && g !== t ? g : null };
  const anc = t => { const r = []; let g = grpOf(t); while (g && !r.includes(g)) { r.push(g); g = grpOf(g) } return r };
  const members = g => sc.tracks.filter(t => anc(t).includes(g));
  const solo = sc.tracks.some(t => t.solo);
  const audible = t => { if (t.mute || anc(t).some(g => g.mute)) return false; if (!solo) return true; if (t.kind === 'return') return true;
      if (t.solo || anc(t).some(g => g.solo)) return true; if (t.kind === 'group' && members(t).some(m => m.solo && !m.mute)) return true; return false };
  // delay compensation as pdcMap: devices are made first so their latency is known
  const NN = new Map(), lat = new Map(), built = [];
  for (const t of sc.tracks) { if (!audible(t)) continue; const xs = t.fx.map(d => mk(d, t.id)); built.push([t, xs]); lat.set(t.id, (posted[t.id] || []).reduce((a, f) => a + f.lat, 0)) }
  const src = sc.tracks.filter(t => t.kind !== 'group' && t.kind !== 'return'), path = new Map(); let target = 0;
  for (const t of src) { let n = lat.get(t.id) || 0; for (const g of anc(t)) n += lat.get(g.id) || 0; path.set(t.id, n); if (n > target) target = n }
  const pdc = new Map(); if (target > 0) for (const t of src) pdc.set(t.id, Math.min(SR, target - path.get(t.id)));
  for (const [t, xs] of built) {
    const tin = oc.createGain(), vol = oc.createGain(), pn = oc.createStereoPanner(); vol.gain.value = t.vol; pn.pan.value = t.pan; let prev = tin;
    for (const x of xs) { prev.connect(x.in); prev = x.out }
    const d = pdc.get(t.id) || 0; if (d > 0) { const dl = oc.createDelay(1); dl.delayTime.value = d / SR; prev.connect(dl); prev = dl }
    prev.connect(vol); vol.connect(pn); NN.set(t.id, {tin, pn, delay: d});
  }
  const conn = {};   // the order the export connects each bus's inputs, for the native scene
  const add = (bus, x) => (conn[bus] = conn[bus] || []).push(x);
  for (const t of sc.tracks) { const n = NN.get(t.id); if (!n) continue; const gp = grpOf(t), G = gp && NN.get(gp.id);
    n.pn.connect(G ? G.tin : mst); add(G ? gp.id : '@master', {from: t.id});
    if (t.kind !== 'return') for (const rid in t.sends) { const R = NN.get(rid), lv = t.sends[rid]; if (!R || !(lv > 0) || rid === t.id) continue;
      const sg = oc.createGain(); sg.gain.value = lv; n.pn.connect(sg); sg.connect(R.tin); add(rid, {from: t.id, send: lv}) }
    if (t.src) { const raw = Uint8Array.from(atob(b64[t.src.name]), c => c.charCodeAt(0)), f = new Float32Array(raw.buffer);
      const buf = oc.createBuffer(t.src.ch, N, SR); for (let c = 0; c < t.src.ch; c++) buf.copyToChannel(f.subarray(c * N, (c + 1) * N), c);
      const s = oc.createBufferSource(); s.buffer = buf; s.connect(n.tin); s.start(0) } }
  const o = await oc.startRendering();
  const res = new Float32Array(2 * N); res.set(o.getChannelData(0), 0); res.set(o.getChannelData(1), N);
  let s = ''; const u = new Uint8Array(res.buffer); for (let i = 0; i < u.length; i += 32768) s += String.fromCharCode.apply(null, u.subarray(i, i + 32768));
  return {out: btoa(s), posted, conn, built: [...NN.keys()], delays: Object.fromEntries([...NN].map(([k, v]) => [k, v.delay]))};
}"""


def wav_write(path, x):
    _wav_write_mono_or_stereo(path, x)


def main():
    from alab import AudioLab
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "ref", "bus")
    os.makedirs(out, exist_ok=True)
    import make_mix_ref; make_mix_ref.SR = SR
    for k, x in INPUTS.items(): wav_write(os.path.join(out, "in_%s.wav" % k), x)
    b64 = {k: base64.b64encode(np.ascontiguousarray(x).tobytes()).decode() for k, x in INPUTS.items()}
    al = AudioLab(os.path.join(ROOT, "index.html")); al.start()
    al.run("window.__alref={FXPRE,mkFx,mkFxNode,wlLoad,fxLat};1")
    only = sys.argv[2].split(",") if len(sys.argv) > 2 and sys.argv[2] else None   # some scenes only; the others' entries are kept
    info = {"app": al.version, "userAgent": al.js("() => navigator.userAgent"), "sr": SR, "frames": N, "scenes": {}}
    old = os.path.join(out, "bus_ref.json")
    if only and os.path.exists(old): info["scenes"] = json.load(open(old)).get("scenes", {})
    for name, (Q, master, mfx, tracks) in SCENES.items():
        if only and name not in only: continue
        sc = {"Q": Q, "master": master, "mfx": [fxd(f) for f in mfx],
              "tracks": [dict(t, src=({"name": t["src"], "ch": int(INPUTS[t["src"]].shape[0])} if t["src"] else None)) for t in tracks]}
        r = al.js(JS, {"sc": sc, "b64": b64, "N": N, "SR": SR}); r2 = al.js(JS, {"sc": sc, "b64": b64, "N": N, "SR": SR})
        y = np.frombuffer(base64.b64decode(r["out"]), dtype="<f4").reshape(2, N)
        y2 = np.frombuffer(base64.b64decode(r2["out"]), dtype="<f4").reshape(2, N)
        rep = int(np.count_nonzero(y.view("<u4") != y2.view("<u4")))
        wav_write(os.path.join(out, "web_%s.wav" % name), y)
        scene = {"sr": SR, "frames": N, "quantum": Q, "master": master, "masterFx": r["posted"].get("@master", []), "nodes": []}
        for t in tracks:
            if t["id"] not in r["built"]: continue
            scene["nodes"].append({"id": t["id"], "kind": t["kind"], "in": ("in_%s.wav" % t["src"]) if t["src"] else None,
                                   "vol": t["vol"], "pan": t["pan"], "fx": r["posted"].get(t["id"], []), "delay": r["delays"].get(t["id"], 0)})
        scene["inputs"] = r["conn"]   # per bus: the connections in the order the export makes them
        json.dump(scene, open(os.path.join(out, "scene_%s.json" % name), "w"), indent=1)
        busMax = max(len(v) for v in r["conn"].values())
        info["scenes"][name] = {"quantum": Q, "built": r["built"], "delays": r["delays"], "largestBus": busMax, "peak": float(np.max(np.abs(y))),
                                "webRendersTwiceSame": rep == 0, "webSamplesDifferingBetweenTwoRenders": rep}
        print(name, json.dumps(info["scenes"][name]), flush=True)
    al.stop()
    json.dump(info, open(os.path.join(out, "bus_ref.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
