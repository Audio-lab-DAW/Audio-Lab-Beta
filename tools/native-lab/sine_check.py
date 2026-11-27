"""Checks a loop-back recording of a 997 Hz sine for clicks, gaps and drops (task NB-N2b, the clock follower).

    python3 tools/native-lab/sine_check.py recorded.wav [result.json]

The follower changes the speed by parts per million, so the recording is no longer sample for sample what was
sent; what must hold is that it is one clean, unbroken sine. Every 10 ms block (after the first half second
of sound) is fitted with a sine and cosine at 997 Hz plus an offset; a gap, a dropped piece or a click leaves a
residual far above the fit's own error. Pure Python, no numpy.
"""
import json, math, struct, sys


def wav_left(path):
    b = open(path, "rb").read()
    i = b.index(b"data"); n = int.from_bytes(b[i + 4:i + 8], "little")
    d = b[i + 8:i + 8 + n]
    v = struct.unpack("<%df" % (len(d) // 4), d[:len(d) // 4 * 4])
    return v[0::2]


def main():
    x = wav_left(sys.argv[1]); SR = 48000; F = 997.0; B = 480
    start = next((i for i, v in enumerate(x) if abs(v) > 0.01), None)
    r = {"recordedSeconds": round(len(x) / SR, 2)}
    if start is None:
        r["error"] = "no sound in the recording"
    else:
        end = len(x)
        while end > start and abs(x[end - 1]) < 0.01:
            end -= 1
        r["soundSeconds"] = round((end - start) / SR, 3)
        # frequency from zero crossings over the whole sound: the speed the follower settled on
        a, b = start + SR // 2, end - SR // 2
        zc = [i for i in range(a, b) if x[i - 1] < 0 <= x[i]]
        if len(zc) > 10:
            f = (len(zc) - 1) * SR / ((zc[-1] - x[zc[-1] - 1] / (x[zc[-1]] - x[zc[-1] - 1])) - (zc[0] - x[zc[0] - 1] / (x[zc[0]] - x[zc[0] - 1])))
            r["frequencyHz"] = round(f, 4); r["speedPartsPerMillion"] = round((F / f - 1) * 1e6, 1)
            fr = r.get("frequencyHz", F)
        else:
            fr = F
        w = 2 * math.pi * fr / SR
        worst = -999.0; bad = 0; blocks = 0; worstAt = 0
        i = start + SR // 2
        while i + B <= end - SR // 20:
            # least squares on sin, cos, 1 (the three are nearly orthogonal over 10 ms at 997 Hz; solved properly anyway)
            s = [math.sin(w * k) for k in range(B)]; c = [math.cos(w * k) for k in range(B)]
            y = x[i:i + B]
            Sss = sum(v * v for v in s); Scc = sum(v * v for v in c); Ssc = sum(s[k] * c[k] for k in range(B))
            Ss = sum(s); Sc = sum(c); n = float(B)
            Sys = sum(y[k] * s[k] for k in range(B)); Syc = sum(y[k] * c[k] for k in range(B)); Sy = sum(y)
            M = [[Sss, Ssc, Ss], [Ssc, Scc, Sc], [Ss, Sc, n]]; v = [Sys, Syc, Sy]
            # Cramer
            def det(m): return m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1]) - m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0]) + m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0])
            D = det(M); sol = []
            for j in range(3):
                Mj = [row[:] for row in M]
                for k in range(3): Mj[k][j] = v[k]
                sol.append(det(Mj) / D)
            res = math.sqrt(sum((y[k] - sol[0] * s[k] - sol[1] * c[k] - sol[2]) ** 2 for k in range(B)) / B)
            amp = math.hypot(sol[0], sol[1]) / math.sqrt(2)
            db = 20 * math.log10(res / max(amp, 1e-9) + 1e-12)
            blocks += 1
            if db > worst: worst = db; worstAt = i
            if db > -60: bad += 1
            i += B
        r.update({"blocks": blocks, "worstBlockResidualDb": round(worst, 1), "worstBlockAtSeconds": round((worstAt - start) / SR, 3), "blocksAboveMinus60Db": bad})
    print(json.dumps(r))
    if len(sys.argv) > 2:
        json.dump(r, open(sys.argv[2], "w"), indent=1)


main()
