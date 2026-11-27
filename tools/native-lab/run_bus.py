"""The native mixer's buses against the web engine (task NB-N3d).

    python3 tools/native-lab/run_bus.py path/to/albus [outdir] [refdir]     # refdir: default ref/bus (made on Linux)

For every scene in ref/bus (made by make_bus_ref.py from the app itself) albus renders the same mix and the two
are compared bit for bit. A bus with three or more inputs is summed by Chromium in an order of its own that can
change between renders (N3b); when a scene differs, the orders of those buses are tried until one reproduces the
web render, and the result says which. Pure Python, so it runs on the macOS build machine as is.
"""
import itertools, json, math, os, struct, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
REF = os.path.join(HERE, "ref", "bus")


def wav(path):
    b = open(path, "rb").read(); i = b.index(b"data"); n = int.from_bytes(b[i + 4:i + 8], "little")
    return b[i + 8:i + 8 + n]


def compare(a, b):
    n = min(len(a), len(b)) // 4
    ua = struct.unpack("<%dI" % n, a[:n * 4]); ub = struct.unpack("<%dI" % n, b[:n * 4])
    fa = struct.unpack("<%df" % n, a[:n * 4]); fb = struct.unpack("<%df" % n, b[:n * 4])
    same = 0; worst = 0.0; first = None
    for i in range(n):
        if ua[i] == ub[i]: same += 1
        else:
            worst = max(worst, abs(fa[i] - fb[i]))
            if first is None: first = i
    return {"samples": n, "identical": same, "different": n - same, "lengthsMatch": len(a) == len(b),
            "worstDbFS": round(20 * math.log10(worst), 1) if worst > 0 else None, "firstDifferentFrame": None if first is None else first // 2}


def main():
    global REF
    exe = os.path.abspath(sys.argv[1]); out = os.path.abspath(sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "out-bus"))
    if len(sys.argv) > 3: REF = os.path.abspath(sys.argv[3])
    os.makedirs(out, exist_ok=True)
    info = json.load(open(os.path.join(REF, "bus_ref.json")))
    res = {}; ok_all = True
    for f in sorted(os.listdir(REF)):
        if not (f.startswith("scene_") and f.endswith(".json")): continue
        name = f[6:-5]; got = os.path.join(out, "native_%s.wav" % name); web = wav(os.path.join(REF, "web_%s.wav" % name))
        p = subprocess.run([exe, os.path.join(REF, f), got, "--reps", "3"], capture_output=True, text=True)
        if p.returncode: res[name] = {"error": p.stderr.strip()}; ok_all = False; print(name, res[name]); continue
        run = json.loads(p.stdout.strip().splitlines()[-1]); used = None
        if wav(got) != web:
            sc = json.load(open(os.path.join(REF, f)))
            big = [(k, len(v)) for k, v in sc["inputs"].items() if len(v) >= 3]
            choices = [[(k, perm) for perm in itertools.permutations(range(n))] for k, n in big]
            for combo in itertools.product(*choices):
                args = []
                for k, perm in combo: args += ["--order", "%s=%s" % (k, ",".join(map(str, perm)))]
                q = subprocess.run([exe, os.path.join(REF, f), got] + args, capture_output=True, text=True)
                if q.returncode == 0 and wav(got) == web: used = {k: list(perm) for k, perm in combo}; break
            if used is None: subprocess.run([exe, os.path.join(REF, f), got], capture_output=True)
        r = compare(web, wav(got))
        r.update({"timesRealTime": round(run["timesRealTime"], 1), "devices": run["devices"], "orderTheWebUsed": used,
                  "webSameTwice": info["scenes"][name]["webRendersTwiceSame"]})
        res[name] = r; ok_all = ok_all and r["different"] == 0 and r["lengthsMatch"]
        print(name, json.dumps(r), flush=True)
    json.dump(res, open(os.path.join(out, "bus_compare.json"), "w"), indent=1)
    print("ALL IDENTICAL" if ok_all else "NOT ALL IDENTICAL")
    sys.exit(0 if ok_all else 1)


main()
