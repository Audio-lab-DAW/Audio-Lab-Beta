"""Compares what was sent to the engine with what came out of the loop-back device (tasks NB-N1, NB-N2a).

    python3 tools/native-lab/stream_compare.py sent.raw recorded.wav [result.json]

Both are 32-bit float stereo. The recording starts earlier and may hold gaps (a ring that ran empty, a device
cycle the machine dropped); the two are lined up, walked side by side, and re-aligned after each gap.
Works on the raw bytes, so "identical" means the same bits. Gives up after 2,000 gaps and says so.
"""
import json, sys


def wav_data(path):
    b = open(path, "rb").read()
    i = b.index(b"data"); n = int.from_bytes(b[i + 4:i + 8], "little")
    return b[i + 8:i + 8 + n]


def compare(want, got):
    want = want[:len(want) // 8 * 8]; got = got[:len(got) // 8 * 8]
    zero = b"\x00" * 8
    first = 0
    while first < len(want) and want[first:first + 8] == zero:
        first += 8
    r = {"sentSamples": len(want) // 4, "recordedSamples": len(got) // 4, "lineUpFound": False, "comparedSamples": 0, "identical": 0, "different": 0, "gapsInTheRecording": 0, "gaveUp": False}
    probe = want[first:first + 256]
    g = -1; k = 0
    while True:
        k = got.find(probe, k)
        if k < 0 or k % 8 == 0:
            g = k; break
        k += 1
    if g < 0:
        return r
    r["lineUpFound"] = True
    w = first; same = diff = gaps = lost = 0; B = 4096
    while w < len(want) and g < len(got):
        n = min(B, len(want) - w, len(got) - g)
        if want[w:w + n] == got[g:g + n]:
            same += n // 4; w += n; g += n; continue
        k = 0
        while k < n and want[w + k:w + k + 4] == got[g + k:g + k + 4]:
            k += 4
        same += k // 4; w += k; g += k
        if w >= len(want) or g >= len(got):
            break
        p = want[w:w + 256]; f = -1
        if len(p) == 256 and p.strip(b"\x00"):
            s = g
            while True:
                s = got.find(p, s, g + 96000 * 8)
                if s < 0 or (s - g) % 4 == 0:
                    f = s; break
                s += 1
        if f >= 0:
            gaps += 1; g = f
        else:
            # nothing later in the recording matches: maybe sent samples never arrived. Look for the recording's next piece later in what was sent
            p2 = got[g:g + 256]; f2 = -1
            if len(p2) == 256 and p2.strip(b"\x00"):
                s2 = w
                while True:
                    s2 = want.find(p2, s2, w + 96000 * 8)
                    if s2 < 0 or (s2 - w) % 4 == 0:
                        f2 = s2; break
                    s2 += 1
            if f2 >= 0:
                lost += (f2 - w) // 4; gaps += 1; w = f2
            else:
                diff += 1; w += 4; g += 4
        if gaps > 2000 or diff > 200000:
            r["gaveUp"] = True; break
    r.update({"comparedSamples": same + diff, "identical": same, "different": diff, "gapsInTheRecording": gaps, "sentButNeverArrived": lost})
    return r


if __name__ == "__main__":
    r = compare(open(sys.argv[1], "rb").read(), wav_data(sys.argv[2]))
    print(json.dumps(r))
    if len(sys.argv) > 3:
        json.dump(r, open(sys.argv[3], "w"), indent=1)
