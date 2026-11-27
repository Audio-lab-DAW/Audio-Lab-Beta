"""Compare alnodes' renders with the browser's (task NB-N3g). Exit 1 unless every case is bit for bit."""
import json, os, sys
import numpy as np
def wav(p):
    b = open(p, "rb").read(); i = b.index(b"data"); n = int.from_bytes(b[i + 4:i + 8], "little")
    return np.frombuffer(b[i + 8:i + 8 + n], dtype="<f4")
d = sys.argv[1]; cs = json.load(open(os.path.join(d, "cases.json")))["cases"]; same = 0
for c in cs:
    w, v = wav(os.path.join(d, "web", c["name"] + ".wav")), wav(os.path.join(d, "native", c["name"] + ".wav"))
    diff = w.view("<u4") != v.view("<u4")
    if not diff.any(): same += 1; print("%-28s bit for bit" % c["name"]); continue
    k = int(np.argmax(diff)); dd = np.abs(w.astype(float) - v.astype(float)).max()
    print("%-28s %d of %d differ, first at %d (web %r native %r), max %.3g" % (c["name"], int(diff.sum()), diff.size, k, float(w[k]), float(v[k]), dd))
print("%d of %d node cases bit for bit" % (same, len(cs)))
sys.exit(0 if same == len(cs) else 1)
