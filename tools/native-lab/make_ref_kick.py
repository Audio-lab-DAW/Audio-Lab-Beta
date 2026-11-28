"""The Kick designer's hit (kickRender in index.html) as the app makes it, for the native port (task NB-N3j).

    python3 tools/native-lab/make_ref_kick.py outdir      # writes cases.json and web/<case>.wav
    build/alnodes outdir/cases.json outdir/native && python3 tools/native-lab/compare_nodes.py outdir

Runs the real app in headless Chromium and calls its kickRender: Fractals' Kick (snap click), every click type,
drive, a transposed hit (key tracking), a long low one; at 44.1 and 48 kHz.
"""
import base64, json, os, struct, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "remake"))
from make_ref_nodes import wav_write

BASE = {"tune": 33, "start": 2400, "sweep": 0.045, "bend": 82, "len": 0.17, "tail": 34, "click": 55, "drive": 12, "ctype": "snap"}   # Fractals' Kick
VARIANTS = [("frx", {}, 0), ("tick", {"ctype": "tick"}, 0), ("knock", {"ctype": "knock", "drive": 80}, 0), ("thud", {"ctype": "thud", "click": 100}, 0),
            ("off", {"ctype": "off"}, 0), ("keytrack", {"len": 0.6, "tail": 90, "bend": 0}, 5), ("long", {"len": 2.5, "sweep": 0.3, "tune": 24}, -3),
            ("nodrive", {"drive": 0, "click": 0}, 0)]


def main():
    from alab import AudioLab
    out = sys.argv[1]
    os.makedirs(os.path.join(out, "web"), exist_ok=True); os.makedirs(os.path.join(out, "native"), exist_ok=True)
    al = AudioLab(os.path.join(ROOT, "index.html")); al.start()
    cs = []
    for sr in (44100, 48000):
        for nm, ov, tr in VARIANTS:
            I = dict(BASE); I.update(ov)
            r = al.run("(()=>{const b=kickRender(%s,%d,%s);const d=b.getChannelData(0);const u=new Uint8Array(d.buffer.slice(0));let s='';for(let i=0;i<u.length;i+=32768)s+=String.fromCharCode.apply(null,u.subarray(i,i+32768));return btoa(s)})()" % (json.dumps(I), sr, tr))
            x = np.frombuffer(base64.b64decode(r), dtype="<f4")
            name = "kick-%s-%d" % (nm, sr // 100)
            wav_write(os.path.join(out, "web", name + ".wav"), sr, x)
            cs.append({"name": name, "sr": sr, "quantum": 128, "frames": int(x.size), "kick": I, "tr": tr})
    al.stop()
    json.dump({"app": al.version, "cases": cs}, open(os.path.join(out, "cases.json"), "w"))
    print(len(cs), "kick cases, app", al.version)


if __name__ == "__main__":
    main()
