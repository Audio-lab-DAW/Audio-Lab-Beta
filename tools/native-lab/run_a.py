"""Test A driver (task NM1): renders the Bitcrusher natively for every case in ref/crush_ref.json, twice
(with this machine's own pow() and exp(), and with the numbers the web engine worked out), compares each
render with the web engine's file bit for bit, and writes results as JSON and as text.

    python3 tools/native-lab/run_a.py path/to/alnative outdir
"""
import json, os, platform, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
exe, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
ref = json.load(open(os.path.join(HERE, "ref", "crush_ref.json")))

def run(*a):
    r = subprocess.run([exe, *a], capture_output=True, text=True)
    try:
        return json.loads(r.stdout)
    except Exception:
        return {"error": (r.stdout + r.stderr).strip()[:400], "code": r.returncode}

res = {"machine": platform.machine(), "system": platform.platform(), "web": {"app": ref["app"], "browser": ref["userAgent"]}, "cases": {}}
lines = []
for name, c in ref["cases"].items():
    p = c["p"]
    args = ["--in", os.path.join(HERE, "ref", "crush_in.wav")]
    for k, web in (("bits", "bits"), ("rate", "rate"), ("jit", "jit"), ("dith", "dith"), ("drive", "drive"), ("mix", "mix"), ("out", "out"), ("pre", "aa"), ("post", "post"), ("shape", "shape")):
        args += ["--" + k, str(p[web])]
    webfile = os.path.join(HERE, "ref", "crush_%s_web.wav" % name)
    o1 = os.path.join(out, "crush_%s_native_own_maths.wav" % name)
    o2 = os.path.join(out, "crush_%s_native_web_numbers.wav" % name)
    r1 = run("crush", *args, "--to", o1, "--reps", "200")
    coef = ",".join(c["coef"][k] for k in ("q", "dr", "go", "pc", "oc"))
    r2 = run("crush", *args, "--to", o2, "--coef", coef)
    c1, c2 = run("compare", webfile, o1), run("compare", webfile, o2)
    same_coef = {k: (r1.get("ownCoef", {}).get(k) == c["coef"][k]) for k in ("q", "dr", "go", "pc", "oc")}
    res["cases"][name] = {"settings": p, "webNumbers": c["coef"], "nativeNumbers": r1.get("ownCoef"), "numbersSame": same_coef,
                          "ownMaths": c1, "webNumbersRender": c2, "timesRealTime": r1.get("timesRealTime")}
    def say(c):
        if c.get("identical"): return "identical, all %d samples" % c["samples"]
        if "error" in c: return "FAILED: " + c["error"]
        return "%d of %d samples differ, largest difference %.1f dB" % (c["differing"], c["samples"], c["maxDifferenceDb"])
    lines.append("%-7s own maths: %s | web numbers: %s | pow/exp results same as the browser: %s | speed %.0f x real time" % (
        name, say(c1), say(c2), "yes" if all(same_coef.values()) else "no (" + ", ".join(k for k, v in same_coef.items() if not v) + ")", r1.get("timesRealTime") or 0))
res["text"] = lines
json.dump(res, open(os.path.join(out, "test_a_crush.json"), "w"), indent=1)
print("\n".join(lines))
