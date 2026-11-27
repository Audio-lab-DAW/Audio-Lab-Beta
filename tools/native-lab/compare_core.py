"""Compare the native engine core's renders with the web engine's (task NB-N3a).

    python3 tools/native-lab/compare_core.py <dir>      # dir has cases.json, web/, native/, native.jsonl
Prints one line per case and writes <dir>/compare.json. Exit 1 if any case is not bit for bit.
"Bit for bit" means every 32-bit float of both channels is the same bit pattern.
"""
import json, os, struct, sys
import numpy as np


def wav(path):
    b = open(path, "rb").read()
    p = 12
    while p + 8 <= len(b):
        cid, ln = b[p:p + 4], struct.unpack("<I", b[p + 4:p + 8])[0]
        if cid == b"data":
            return np.frombuffer(b[p + 8:p + 8 + ln], dtype="<f4").reshape(-1, 2).T
        p += 8 + ln + (ln & 1)
    raise ValueError("no data in " + path)


def main():
    d = sys.argv[1]
    cases = json.load(open(os.path.join(d, "cases.json")))["cases"]
    timing = {}
    tp = os.path.join(d, "native.jsonl")
    if os.path.exists(tp):
        for line in open(tp):
            line = line.strip()
            if line.startswith("{"):
                j = json.loads(line); timing[j["name"]] = j
    res, same, total = {}, 0, 0
    for c in cases:
        n = c["name"]; total += 1
        npath = os.path.join(d, "native", n + ".wav")
        if not os.path.exists(npath):
            res[n] = {"ok": False, "why": timing.get(n, {}).get("error", "no native output")}
            print("%-28s MISSING %s" % (n, res[n]["why"])); continue
        w, v = wav(os.path.join(d, "web", n + ".wav")), wav(npath)
        bw, bv = w.view(np.uint32), v.view(np.uint32)
        diff = bw != bv
        k = int(diff.sum())
        r = {"ok": k == 0, "samplesDiffer": k, "of": int(diff.size), "usPerBlock": timing.get(n, {}).get("usPerBlock")}
        if k:
            dd = np.abs(w.astype(np.float64) - v.astype(np.float64))
            pk = float(np.max(np.abs(w))) or 1.0
            r["firstFrame"] = int(np.argmax(diff.any(axis=0)))
            r["maxDiff"] = float(dd.max())
            r["maxDiffDbRelPeak"] = float(20 * np.log10(dd.max() / pk)) if dd.max() > 0 else None
            # differences of one unit in the last place
            r["maxUlp"] = int(np.max(np.abs(bw.astype(np.int64) - bv.astype(np.int64))[diff]))
        else:
            same += 1
        res[n] = r
        print("%-28s %s" % (n, "bit for bit" if k == 0 else "%d of %d samples differ, first at frame %d, max %.3g (%.1f dB under the peak), max %d ulp" % (
            k, diff.size, r["firstFrame"], r["maxDiff"], -(r["maxDiffDbRelPeak"] or 0), r["maxUlp"])))
    json.dump({"same": same, "total": total, "cases": res}, open(os.path.join(d, "compare.json"), "w"), indent=1)
    print("%d of %d cases bit for bit" % (same, total))
    sys.exit(0 if same == total else 1)


if __name__ == "__main__":
    main()
