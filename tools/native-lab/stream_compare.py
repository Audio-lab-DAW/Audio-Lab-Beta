"""Compares what was sent to the engine with what came out of the loop-back device (task NB-N1).

    python3 tools/native-lab/stream_compare.py sent.raw recorded.wav [result.json]

Both are 32-bit float stereo. The recording starts earlier and may hold gaps (a ring that ran empty, a device
cycle the machine dropped); the two are lined up, walked side by side, and re-aligned after each gap.
"""
import json, struct, sys


def floats(b):
    return struct.unpack("<%df" % (len(b) // 4), b[:len(b) // 4 * 4])


def wav_data(path):
    b = open(path, "rb").read()
    i = b.index(b"data"); n = struct.unpack("<I", b[i + 4:i + 8])[0]
    return b[i + 8:i + 8 + n]


def compare(want, got):
    first = next((i for i in range(0, len(want), 2) if want[i] != 0.0 or want[i + 1] != 0.0), 0)
    off = -1
    for i in range(0, max(0, len(got) - 64), 2):
        if got[i] == want[first] and got[i + 1] == want[first + 1] and got[i + 2:i + 34] == want[first + 2:first + 34]:
            off = i - first; break
    same = diff = gaps = 0
    if off >= 0:
        gi, wi = off + first, first
        while wi < len(want) and gi < len(got):
            if struct.pack("<f", got[gi]) == struct.pack("<f", want[wi]):
                same += 1; gi += 1; wi += 1; continue
            probe = want[wi:wi + 32]; found = -1
            if len(probe) == 32 and any(probe):
                for k in range(gi, min(len(got) - 32, gi + 96000)):
                    if got[k] == probe[0] and got[k:k + 32] == probe:
                        found = k; break
            if found >= 0:
                gaps += 1; gi = found
            else:
                diff += 1; gi += 1; wi += 1
    return {"sentSamples": len(want), "recordedSamples": len(got), "lineUpFound": off >= 0, "comparedSamples": same + diff, "identical": same, "different": diff, "gapsInTheRecording": gaps}


if __name__ == "__main__":
    r = compare(floats(open(sys.argv[1], "rb").read()), floats(wav_data(sys.argv[2])))
    print(json.dumps(r))
    if len(sys.argv) > 3:
        json.dump(r, open(sys.argv[3], "w"), indent=1)
