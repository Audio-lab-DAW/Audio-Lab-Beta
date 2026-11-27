"""Compares what the null device played (AL_NULL_RECORD) with what the page sent (task NB-R3).

    python3 tools/native-lab/feeder_check.py <rec.wav> <sent.raw>     prints one JSON line

sent.raw: float32 stereo interleaved, the page's noise. Walks both: frames equal bit for bit are counted; silent
frames inside the sound are gaps (the ring ran empty); a frame that is neither is resynchronised by looking it up
in what was sent (frames lost on the way). The sound's tail after the last sent frame is ignored.
"""
import json, struct, sys
import numpy as np


def read_wav(p):
    b = open(p, "rb").read()
    assert b[:4] == b"RIFF" and b[8:12] == b"WAVE"
    i, fmt, data = 12, None, None
    while i + 8 <= len(b):
        cid, n = b[i:i + 4], struct.unpack("<I", b[i + 4:i + 8])[0]
        if cid == b"fmt ": fmt = struct.unpack("<HHIIHH", b[i + 8:i + 24])
        if cid == b"data": data = b[i + 8:i + 8 + n]
        i += 8 + n + (n & 1)
    tag, ch, sr, _, _, bits = fmt
    a = np.frombuffer(data, "<f4" if tag == 3 or (tag == 0xFFFE and bits == 32) else "<i2")
    return a.reshape(-1, ch), sr


rec, sr = read_wav(sys.argv[1])
sent = np.fromfile(sys.argv[2], "<f4").reshape(-1, 2)
rv = rec.view(np.uint32) if rec.dtype == np.float32 else rec
sv = sent.view(np.uint32)
key = {}
for j in range(len(sv)):
    key.setdefault((int(sv[j, 0]), int(sv[j, 1])), j)
nz = np.nonzero(np.any(rec != 0, axis=1))[0]
R = {"recFrames": len(rec), "sentFrames": len(sent), "rate": sr}
if not len(nz):
    R.update(ok=False, error="nothing but silence was recorded"); print(json.dumps(R)); sys.exit(0)
i = int(nz[0]); j = key.get((int(rv[i, 0]), int(rv[i, 1])), -1)
R["startsAtSent"] = j
same = gaps = gapFrames = lost = lostEvents = wrong = 0; inGap = False; gapList = []
while i < len(rv) and 0 <= j < len(sv):
    if rv[i, 0] == sv[j, 0] and rv[i, 1] == sv[j, 1]:
        same += 1; i += 1; j += 1; inGap = False; continue
    if rec[i, 0] == 0 and rec[i, 1] == 0:
        if not inGap: gaps += 1; gapList.append([i, 0]); inGap = True
        gapFrames += 1; gapList[-1][1] += 1; i += 1; continue
    k = key.get((int(rv[i, 0]), int(rv[i, 1])), -1)
    if k > j: lost += k - j; lostEvents += 1; j = k; inGap = False; continue
    wrong += 1; i += 1
R.update(identical=same, gaps=gaps, gapFrames=gapFrames, gapMsList=[round(n * 1000 / sr, 1) for _, n in gapList[:20]],
         lostFrames=lost, lostEvents=lostEvents, wrongFrames=wrong, reachedSentEnd=j >= len(sv) - 1, firstSent=int(R["startsAtSent"]))
R["ok"] = R["startsAtSent"] == 0 and gaps == 0 and lost == 0 and wrong == 0 and same == len(sent)
print(json.dumps(R))
