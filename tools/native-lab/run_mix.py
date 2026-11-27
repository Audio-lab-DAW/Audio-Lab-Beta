"""The native engine core against the web engine's mixer (task NB-N3b).

    python3 tools/native-lab/run_mix.py path/to/almix [outdir]

For every scene in ref/mix (made by make_mix_ref.py from the app itself) almix renders the same mix, and the
two are compared bit for bit: identical samples, and for any that differ the largest difference in units in the
last place and in dB below full scale. Pure Python (no numpy), so it runs on the macOS build machine as is.
"""
import json, math, os, struct, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
REF = os.path.join(HERE, "ref", "mix")


def wav(path):
    b = open(path, "rb").read(); i = b.index(b"data"); n = int.from_bytes(b[i + 4:i + 8], "little")
    return b[i + 8:i + 8 + n]


def main():
    exe = sys.argv[1]; out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "out-mix")
    os.makedirs(out, exist_ok=True)
    res = {}; ok_all = True
    for f in sorted(os.listdir(REF)):
        if not f.startswith("scene_"): continue
        name = f[6:-4]; got = os.path.join(out, "native_%s.wav" % name)
        web = wav(os.path.join(REF, "web_%s.wav" % name))
        lines = open(os.path.join(REF, f)).read().splitlines(); ntr = sum(1 for l in lines if '"track"' in l)
        p = subprocess.run([exe, f, got, "--reps", "5"], cwd=REF, capture_output=True, text=True)
        if p.returncode: res[name] = {"error": p.stderr.strip()}; ok_all = False; continue
        run = json.loads(p.stdout.strip().splitlines()[-1]); order = None
        if wav(got) != web and 2 <= ntr <= 6:
            # the web engine's own order of the tracks changes between renders (mix_graph.h): find the one it used
            import itertools
            for perm in itertools.permutations(range(ntr)):
                if list(perm) == list(range(ntr)): continue
                h = json.loads(lines[0]); h["order"] = ",".join(map(str, perm))
                tmp = os.path.join(out, "scene_order.txt"); open(tmp, "w").write("\n".join([json.dumps(h)] + lines[1:]) + "\n")
                q = subprocess.run([exe, tmp, got], cwd=REF, capture_output=True, text=True)
                if q.returncode == 0 and wav(got) == web: order = list(perm); break
            if order is None: subprocess.run([exe, f, got], cwd=REF, capture_output=True)
        a, b = web, wav(got)
        n = min(len(a), len(b)) // 4
        ua = struct.unpack("<%dI" % n, a[:n * 4]); ub = struct.unpack("<%dI" % n, b[:n * 4])
        fa = struct.unpack("<%df" % n, a[:n * 4]); fb = struct.unpack("<%df" % n, b[:n * 4])
        same = sum(1 for i in range(n) if ua[i] == ub[i])
        worst_ulp = 0; worst = 0.0
        for i in range(n):
            if ua[i] != ub[i]:
                d = abs(fa[i] - fb[i]); worst = max(worst, d)
                # distance in floats of the same sign
                if (ua[i] >> 31) == (ub[i] >> 31): worst_ulp = max(worst_ulp, abs((ua[i] & 0x7fffffff) - (ub[i] & 0x7fffffff)))
                else: worst_ulp = max(worst_ulp, 1 << 30)
        r = {"samples": n, "identical": same, "different": n - same, "lengthsMatch": len(a) == len(b),
             "worstUlp": worst_ulp, "worstDbFS": round(20 * math.log10(worst), 1) if worst > 0 else None,
             "timesRealTime": round(run["timesRealTime"], 1), "orderTheWebUsed": order}
        res[name] = r
        ok_all = ok_all and r["different"] == 0 and r["lengthsMatch"]
        print(name, json.dumps(r))
    json.dump(res, open(os.path.join(out, "mix_compare.json"), "w"), indent=1)
    print("ALL IDENTICAL" if ok_all else "NOT ALL IDENTICAL")
    sys.exit(0 if ok_all else 1)


main()
