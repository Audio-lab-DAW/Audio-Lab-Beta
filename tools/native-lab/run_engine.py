"""Test of the engine's first part (task NB-N1): drives alengine through its JSON lines on the build machine.

    python3 tools/native-lab/run_engine.py build/alengine build/alnative outdir

What it proves, with the virtual loop-back device BlackHole as the "DAC":
  1. hand-over: sound sent to the engine through its socket comes out of the device as the same samples
  2. device control: rate, buffer, format, volume (set, read back, and noticed when changed from outside)
  3. exclusive use: a second program is kept out while the engine holds the device
  4. switching: how long a change of device takes while sound plays
"""
import json, os, socket, struct, subprocess, sys, threading, time
HERE = os.path.dirname(os.path.abspath(__file__))
eng_path, alnative, out = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(out, exist_ok=True)
R = {"steps": {}}


class Engine:
    def __init__(self, path):
        self.p = subprocess.Popen([path], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)
        self.events, self.replies = [], []
        self.cv = threading.Condition()
        threading.Thread(target=self._read, daemon=True).start()

    def _read(self):
        for line in self.p.stdout:
            try:
                m = json.loads(line)
            except Exception:
                continue
            with self.cv:
                (self.events if "ev" in m else self.replies).append(m)
                self.cv.notify_all()

    def cmd(self, timeout=15, **kw):
        with self.cv:
            n = len(self.replies)
        self.p.stdin.write(json.dumps(kw) + "\n"); self.p.stdin.flush()
        with self.cv:
            self.cv.wait_for(lambda: len(self.replies) > n, timeout)
            return self.replies[n] if len(self.replies) > n else {"ok": False, "error": "no answer"}

    def wait_event(self, name, timeout=5, since=0):
        with self.cv:
            self.cv.wait_for(lambda: any(e["ev"] == name for e in self.events[since:]), timeout)
            return next((e for e in self.events[since:] if e["ev"] == name), None)

    def quit(self):
        try:
            self.cmd(cmd="quit", timeout=5)
        except Exception:
            pass
        try:
            self.p.wait(5)
        except Exception:
            self.p.kill()


def wav_read(path):
    b = open(path, "rb").read()
    i = b.index(b"data"); n = struct.unpack("<I", b[i + 4:i + 8])[0]
    return b[i + 8:i + 8 + n]


def wav_floats(path):
    d = wav_read(path)
    return struct.unpack("<%df" % (len(d) // 4), d)


e = Engine(eng_path)
ready = e.wait_event("ready", 10)
R["engine"] = ready
devs = e.cmd(cmd="devices")
names = [d["name"] for d in devs.get("devices", [])]
bh = next((d for d in devs.get("devices", []) if "BlackHole" in d["name"]), None)
R["devices"] = names
print("devices:", names)
if not bh:
    R["error"] = "the loop-back device BlackHole is not on this machine; the hand-over test cannot run"
    json.dump(R, open(os.path.join(out, "engine.json"), "w"), indent=1); print(R["error"]); e.quit(); sys.exit(0)

# ---- 1. hand-over ------------------------------------------------------------------------------------
o = e.cmd(cmd="open", uid=bh["uid"], rate=48000, buffer=256)   # a shared virtual machine: a roomy buffer for the sample-exact test
R["steps"]["open"] = {k: o.get(k) for k in ("ok", "error", "notes", "tookMilliseconds", "device", "rate", "buffer", "onTheWire", "handedToUs", "latencyFrames")}
print("open:", R["steps"]["open"])
sock = os.path.join("/tmp", "alengine-test-%d.sock" % os.getpid())
s = e.cmd(cmd="source", type="socket", path=sock, prefillMs=150, highMs=1500, pageRate=48000)
sent = wav_read(os.path.join(HERE, "ref", "crush_plain_web.wav")) + wav_read(os.path.join(HERE, "ref", "crush_filter_web.wav")) + wav_read(os.path.join(HERE, "ref", "crush_dither_web.wav"))
sent = sent * 2                                     # 3 seconds of the web engine's own renders
rec = subprocess.Popen([alnative, "record", "--device", str(bh["id"]), "--seconds", "5", "--to", os.path.join(out, "loopback.wav")], stdout=subprocess.PIPE, text=True)
time.sleep(0.6)
c = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM); c.connect(sock)
chunk = 480 * 8                                     # 10 ms
t0 = time.time(); pos = 0; lead = 0.4               # stay 400 ms ahead of real time
while pos < len(sent):
    due = (time.time() - t0 + lead) * 48000 * 8
    while pos < len(sent) and pos < due:
        c.sendall(sent[pos:pos + chunk]); pos += chunk
    time.sleep(0.004)
time.sleep(0.7)
st = e.cmd(cmd="status")
c.close()
rec.wait(20)
got = wav_floats(os.path.join(out, "loopback.wav")) if os.path.exists(os.path.join(out, "loopback.wav")) else ()
want = struct.unpack("<%df" % (len(sent) // 4), sent)
# line the recording up with what was sent: find the first sent frame that is not silence
first = next(i for i in range(0, len(want), 2) if want[i] != 0.0 or want[i + 1] != 0.0)
off = -1
for i in range(0, max(0, len(got) - 64), 2):
    if got[i] == want[first] and got[i + 1] == want[first + 1] and got[i + 2:i + 34] == want[first + 2:first + 34]:
        off = i - first; break
same = diff = gaps = 0
if off >= 0:
    # walk both streams; where they part (a gap put in by an empty ring or a dropped device cycle), find the place again
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
ring = st.get("ring", {})
R["steps"]["handOver"] = {"sentSamples": len(want), "recordedSamples": len(got), "lineUpFound": off >= 0, "comparedSamples": same + diff, "identical": same, "different": diff, "gapsInTheRecording": gaps,
                          "ranEmpty": ring.get("ranEmpty"), "droppedTimes": ring.get("droppedTimes"), "droppedFrames": ring.get("droppedFrames"), "received": ring.get("received"),
                          "overloads": st.get("overloads"), "framesPerCallback": [st.get("framesPerCallbackMin"), st.get("framesPerCallbackMax")], "renderAvgMicroseconds": st.get("renderAvgMicroseconds")}
print("hand-over:", R["steps"]["handOver"])

# ---- 2. device control -------------------------------------------------------------------------------
n0 = len(e.events)
v = e.cmd(cmd="volume", value=0.5)
ev = e.wait_event("volume", 3, n0)
R["steps"]["volumeSet"] = {"asked": 0.5, "readBack": v.get("value"), "ok": v.get("ok"), "eventSeen": ev}
# someone else turns the volume: a second engine
e2 = Engine(eng_path); e2.wait_event("ready", 10)
e2.cmd(cmd="open", uid=bh["uid"])
n0 = len(e.events)
e2.cmd(cmd="volume", value=0.8)
ev = e.wait_event("volume", 3, n0)
R["steps"]["volumeFromOutside"] = {"setByOtherProgram": 0.8, "eventInEngine": ev}
e2.cmd(cmd="close")
print("volume:", R["steps"]["volumeSet"], R["steps"]["volumeFromOutside"])
e.cmd(cmd="volume", value=1.0)
n0 = len(e.events)
o = e.cmd(cmd="open", uid=bh["uid"], rate=96000, buffer=32)
R["steps"]["rate96k"] = {k: o.get(k) for k in ("ok", "notes", "tookMilliseconds", "rate", "buffer", "onTheWire")}
R["steps"]["rate96k"]["eventSeen"] = e.wait_event("rate", 3, n0)
f = e.cmd(cmd="formats")
R["steps"]["formats"] = {"count": len(f.get("formats", [])), "notMixable": sum(1 for x in f.get("formats", []) if not x["mixable"]), "integer": sum(1 for x in f.get("formats", []) if not x["float"])}
print("rate:", R["steps"]["rate96k"], "formats:", R["steps"]["formats"])

# ---- 3. exclusive use --------------------------------------------------------------------------------
o = e.cmd(cmd="open", uid=bh["uid"], rate=48000, exclusive=True)
e.cmd(cmd="source", type="tone")
time.sleep(0.5)
o2 = e2.cmd(cmd="open", uid=bh["uid"])
time.sleep(0.5)
s2 = e2.cmd(cmd="status")
R["steps"]["exclusive"] = {"taken": o.get("exclusive"), "notes": o.get("notes"), "otherProgramOpened": o2.get("ok"), "otherProgramError": o2.get("error"), "otherProgramCallbacks": s2.get("callbacks")}
e2.cmd(cmd="close")
print("exclusive:", R["steps"]["exclusive"])

# ---- 4. switching while sound plays ------------------------------------------------------------------
others = [d for d in devs["devices"] if d["outChannels"] > 0 and d["id"] != bh["id"]]
sw = []
for d in (others[:2] + [bh]):
    o = e.cmd(cmd="open", uid=d["uid"])
    time.sleep(0.3)
    st = e.cmd(cmd="status")
    sw.append({"to": d["name"], "ok": o.get("ok"), "tookMilliseconds": o.get("tookMilliseconds"), "callbacksAfter300ms": st.get("callbacks"), "exclusiveReleased": not o.get("exclusive")})
R["steps"]["switching"] = sw
print("switching:", sw)
e.cmd(cmd="close")
e2.quit(); e.quit()
R["events"] = [x for x in e.events if x["ev"] not in ("ready",)][:40]
json.dump(R, open(os.path.join(out, "engine.json"), "w"), indent=1)
