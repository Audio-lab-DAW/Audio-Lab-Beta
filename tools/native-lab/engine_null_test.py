"""The real engine (alengine) on the null device, end to end (task NB-R2). Runs on any machine; CI runs it on every
push, also with ThreadSanitizer. Pure Python, no packages.

    python3 tools/native-lab/engine_null_test.py path/to/alengine [outdir]

Checks:
  rate contract (review A1): a socket source without pageRate, or at another rate (16 kHz into 48 kHz, eqMac's case),
    is refused with both rates named; at the device's rate it plays;
  hand-over: what is sent comes out of the device bit for bit (exact mode, recorded by the null device);
  the device changes rate while sound plays: the engine says soundPaused, plays silence (never sound at the wrong
    speed), counts what it threw away, and resumes by itself when the rate comes back;
  a new source at the new rate plays again;
  device volume both ways, unplugging, exclusive use held by someone else;
  source switching under load (review C1): 300 switches between socket, tone, file and silence while a sender writes,
    and clock-mode flips: the engine answers every command and does not hang;
  a sender that stopped sending and never closes (a frozen feeder, task NB-R3) does not hold a source switch;
  task NB-R4b (review C9): with the engine's output unread (a full pipe) it still takes commands and sound; 40 format
    changes against 40 opens; a file at another rate refused;
  task NB-R4 (review C6 to C10, A10): protocol 1 and request numbers (also on a parse error); bad numbers refused
  without harm; the device volume ramps and needs a confirmation above the loudest level the device has had; NaN,
  infinity and samples past full scale never reach the device (counted), legal samples untouched; dither off by
  default; a format change from outside restarts the stream, and 24-bit samples go through the integer path bit
  for bit; a broken WAV file is refused cleanly.
"""
import json, os, socket, struct, subprocess, sys, tempfile, threading, time, math

exe = sys.argv[1]
out = sys.argv[2] if len(sys.argv) > 2 else tempfile.mkdtemp()
os.makedirs(out, exist_ok=True)
REC = os.path.join(out, "null_record.wav")
results = []


def check(ok, what, extra=None):
    results.append((bool(ok), what))
    print(("ok   " if ok else "FAIL ") + what + ("" if ok or extra is None else "  (" + json.dumps(extra)[:400] + ")"), flush=True)


class Engine:
    def __init__(self):
        env = dict(os.environ, AL_NULL_RECORD=REC)
        self.p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1, env=env)
        self.lock = threading.Lock(); self.answers = []; self.events = []; self.cv = threading.Condition(self.lock)
        threading.Thread(target=self._read, daemon=True).start()
        self.stderr = []
        threading.Thread(target=lambda: self.stderr.extend(self.p.stderr), daemon=True).start()

    hold = threading.Event()   # task NB-R4b: set = this side stops reading the engine's output (the pipe fills up)

    def _read(self):
        for line in self.p.stdout:
            while self.hold.is_set(): time.sleep(0.01)
            try: m = json.loads(line)
            except Exception: continue
            with self.cv:
                (self.events if "ev" in m else self.answers).append(m); self.cv.notify_all()

    def cmd(self, timeout=10, **o):
        with self.cv:
            n = len(self.answers)
        self.p.stdin.write(json.dumps(o) + "\n"); self.p.stdin.flush()
        t = time.time() + timeout
        with self.cv:
            while True:
                for a in self.answers[n:]:
                    if a.get("re") == o["cmd"]:
                        self.answers.remove(a); return a
                left = t - time.time()
                if left <= 0: return {"ok": False, "error": "no answer to " + o["cmd"]}
                self.cv.wait(left)

    def wait_event(self, ev, timeout=3, since=0, pred=lambda e: True):
        t = time.time() + timeout
        with self.cv:
            while True:
                for e in self.events[since:]:
                    if e.get("ev") == ev and pred(e): return e
                left = t - time.time()
                if left <= 0: return None
                self.cv.wait(left)


def sender(path, frames_iter, rate, stop, sent):
    """Sends stereo float frames at real-time pace, 128 frames a block, 100 ms ahead."""
    c = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM); c.connect(path)
    t0 = time.time(); n = 0
    try:
        for blk in frames_iter:
            if stop.is_set(): break
            due = t0 + n / rate - 0.1
            d = due - time.time()
            if d > 0: time.sleep(d)
            c.sendall(blk); n += len(blk) // 8; sent.append(blk)
    except (BrokenPipeError, ConnectionResetError):
        pass
    finally:
        c.close()


def blocks(total, start=0):
    """A signal whose every sample is unique: a slow ramp in the left, its negative in the right."""
    for b in range(start, start + total, 128):
        fr = []
        for i in range(b, b + 128):
            v = ((i % 1000000) + 1) / 2000000.0
            fr += [v, -v]
        yield struct.pack("<%df" % len(fr), *fr)


def wav_floats(path):
    b = open(path, "rb").read(); i = b.index(b"data"); n = int.from_bytes(b[i + 4:i + 8], "little")
    sr = int.from_bytes(b[24:28], "little")
    return sr, struct.unpack("<%df" % (n // 4), b[i + 8:i + 8 + n])


if os.path.exists(REC): os.remove(REC)
e = Engine()
ready = e.wait_event("ready", 5)
check(ready and ready.get("rateContract"), "the engine starts on the null device and says it keeps the rate contract", ready)
check(ready and ready.get("protocol") == 1, "ready says protocol 1 (task NB-R4)", ready)
o = e.cmd(cmd="open", uid="al-null-1", rate=48000, buffer=128)
check(o.get("ok") and o.get("rate") == 48000, "open the null output at 48 kHz, 128 frames", o)
sock = os.path.join(tempfile.gettempdir(), "al-null-%d.sock" % os.getpid())

# ---- the rate contract ----------------------------------------------------------------------------------
r = e.cmd(cmd="source", type="socket", path=sock)
check(not r.get("ok") and "pageRate" in r.get("error", ""), "a socket source without pageRate is refused", r)
r = e.cmd(cmd="source", type="socket", path=sock, pageRate=16000)
check(not r.get("ok") and "16000" in r["error"] and "48000" in r["error"] and r.get("deviceRate") == 48000, "16 kHz into a device at 48 kHz is refused, both rates named", r)
r = e.cmd(cmd="source", type="socket", path=sock, pageRate=48000, prefillMs=60, highMs=600)
check(r.get("ok"), "the page at the device's rate is accepted", r)

# ---- hand-over, bit for bit -------------------------------------------------------------------------------
stop = threading.Event(); sent = []
th = threading.Thread(target=sender, args=(sock, blocks(48000 * 2), 48000, stop, sent)); th.start(); th.join()
time.sleep(0.3)
st = e.cmd(cmd="status")
check(st.get("ring", {}).get("received") == 96000 and st.get("rateOk") is True, "2 s sent, every frame received, rate ok", st.get("ring"))

# ---- the device changes rate while sound plays -------------------------------------------------------------
n0 = len(e.events)
stop2 = threading.Event(); sent2 = []
th2 = threading.Thread(target=sender, args=(sock, blocks(48000 * 3, 96000), 48000, stop2, sent2)); th2.start()
time.sleep(0.8)
x = e.cmd(cmd="null", change="rate", value=96000)
ev = e.wait_event("rate", 3, n0)
check(x.get("ok") and ev and ev.get("value") == 96000 and ev.get("soundPaused") is True and ev.get("pageRate") == 48000, "the device goes to 96 kHz while sound plays: rate event with soundPaused", ev)
time.sleep(0.8)
st = e.cmd(cmd="status")
check(st.get("rateOk") is False and st.get("framesAtWrongRate", 0) > 10000 and st.get("rate") == 96000, "while the rates differ: silence, the page's frames thrown away and counted", {k: st.get(k) for k in ("rateOk", "framesAtWrongRate", "rate")})
pk0 = e.cmd(cmd="reset")
time.sleep(0.4)
st = e.cmd(cmd="status")
check(st.get("peak", 1) == 0, "nothing reaches the device at the wrong rate (peak 0 since the reset)", st.get("peak"))
n1 = len(e.events)
e.cmd(cmd="null", change="rate", value=48000)
ev = e.wait_event("rate", 3, n1)
check(ev and ev.get("resumed") is True and ev.get("soundPaused") is False, "the device comes back to 48 kHz: sound resumes by itself", ev)
time.sleep(0.4)
st = e.cmd(cmd="status")
check(st.get("rateOk") is True and st.get("peak", 0) > 0, "after the rate came back the page's sound plays again", {k: st.get(k) for k in ("rateOk", "peak")})
th2.join()

# ---- a new rate, a new source -------------------------------------------------------------------------------
o = e.cmd(cmd="open", uid="al-null-1", rate=96000, buffer=64)
st = e.cmd(cmd="status")
check(o.get("ok") and st.get("rateOk") is False, "open at 96 kHz while the page sends 48 kHz: the contract is checked again (silence)", {k: st.get(k) for k in ("rate", "rateOk")})
r = e.cmd(cmd="source", type="socket", path=sock, pageRate=96000)
check(r.get("ok") and r.get("deviceRate") == 96000, "the page made again at 96 kHz is accepted", r)
stop3 = threading.Event(); sent3 = []
th3 = threading.Thread(target=sender, args=(sock, blocks(96000), 96000, stop3, sent3)); th3.start(); th3.join(); time.sleep(0.3)
st = e.cmd(cmd="status")
check(st.get("ring", {}).get("received") == 96000 and st.get("rateOk") is True, "1 s at 96 kHz received, rate ok", st.get("ring"))

# ---- device volume both ways, exclusive use, unplugging ------------------------------------------------------------
n2 = len(e.events)
v = e.cmd(cmd="volume", value=0.25)
evr = e.wait_event("volume", 3, n2, lambda x: x.get("ramped"))
check(v.get("ok") and v.get("target") == 0.25 and evr and abs(evr.get("value", 0) - 0.25) < 1e-9, "volume set (in a ramp) and read back", [v, evr])
n2 = len(e.events)
e.cmd(cmd="null", change="volume", value=0.75)
ev = e.wait_event("volume", 3, n2, lambda x: abs(x.get("value", 0) - 0.75) < 1e-9)
check(ev is not None, "volume changed outside the engine: the engine tells at once", ev)
o2 = e.cmd(cmd="open", uid="al-null-2", rate=48000)
v2 = e.cmd(cmd="volume", value=0.5)
check(o2.get("ok") and not v2.get("ok") and "no volume" in v2.get("error", ""), "a device without a volume the computer can set says so (like the Zoom)", v2)
e.cmd(cmd="null", change="hog", value=4242, id=1)
o3 = e.cmd(cmd="open", uid="al-null-1", rate=48000, exclusive=True)
check(o3.get("ok") and "held by process 4242" in o3.get("notes", ""), "exclusive use held by another program: opened, and the note says who holds it", o3.get("notes"))
e.cmd(cmd="null", change="hog", value=-1, id=1)
n3 = len(e.events)
e.cmd(cmd="null", change="unplug", id=1)
ev = e.wait_event("devices", 3, n3)
check(ev and ev.get("ourDeviceStillThere") is False, "the device in use is unplugged: the engine says so", ev)
e.cmd(cmd="null", change="plug", id=1)
o = e.cmd(cmd="open", uid="al-null-1", rate=48000, buffer=128)
check(o.get("ok"), "plugged back and opened again", o)

# ---- source switching under load (review C1) ---------------------------------------------------------------------------
wav = os.path.join(out, "tone.wav")
fr = struct.pack("<%df" % 9600, *([0.1, -0.1] * 4800))
with open(wav, "wb") as f:
    f.write(b"RIFF" + struct.pack("<I", 36 + len(fr)) + b"WAVEfmt " + struct.pack("<IHHIIHH", 16, 3, 2, 48000, 48000 * 8, 8, 32) + b"data" + struct.pack("<I", len(fr)) + fr)
t0 = time.time(); bad = 0
for k in range(300):
    kind = ["socket", "socket", "tone", "socket", "file", "silence"][k % 6]   # socket after socket: the old sender is still streaming
    if kind == "socket":
        r = e.cmd(cmd="source", type="socket", path=sock, pageRate=48000, clock="follow" if k % 8 == 0 else "exact", prefillMs=5, highMs=50)
        if r.get("ok"):
            st4 = threading.Event()
            threading.Thread(target=sender, args=(sock, blocks(48000), 480000, st4, []), daemon=True).start()   # ten times too fast for 0.1 s: the ring fills, the socket thread writes all the time
            time.sleep(0.02)
            e.cmd(cmd="clock", mode="exact" if k % 3 else "follow")
    elif kind == "file":
        r = e.cmd(cmd="source", type="file", path=wav)
    else:
        r = e.cmd(cmd="source", type=kind)
    if not r.get("ok"): bad += 1
took = time.time() - t0
st = e.cmd(cmd="status")
check(bad == 0 and st.get("open") is True, "300 source switches under load in %.1f s: every one answered, the engine alive" % took, {"failed": bad})

# ---- a sender that stopped sending does not hold a source switch (task NB-R3: a frozen feeder process) -------------------
r = e.cmd(cmd="source", type="socket", path=sock, pageRate=48000, clock="exact", prefillMs=30, highMs=120)
frozen = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM); frozen.connect(sock); frozen.sendall(b"\0" * 8 * 480)
time.sleep(0.2)   # connected, sent a little, then nothing more and never closes (as a SIGSTOPped feeder)
t1 = time.time(); r2 = e.cmd(cmd="source", type="socket", path=sock + "2", pageRate=48000, clock="exact", prefillMs=30, highMs=120, timeout=5); took1 = time.time() - t1
check(r.get("ok") and r2.get("ok") and took1 < 0.5, "a sender that stopped sending (and never closes) does not hold a source switch (%.0f ms)" % (took1 * 1000), {"took": took1, "r2": r2})
fresh = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM); fresh.connect(sock + "2"); fresh.sendall(b"\0" * 8 * 4800); time.sleep(0.3)
st = e.cmd(cmd="status")
check(st.get("ring", {}).get("connected") is True, "the new sender is connected and stays connected", st.get("ring"))
frozen.close(); fresh.close(); e.cmd(cmd="source", type="silence")

# ---- task NB-R4: hardening (review C6, C7, C8, C10, A10) ---------------------------------------------------------------
o = e.cmd(cmd="open", uid="al-null-1", rate=48000, buffer=128)
st = e.cmd(cmd="status", req=41)
check(st.get("req") == 41 and st.get("open") is True, "a request number comes back in the answer", st.get("req"))
check(st.get("dither") is False and "deviceLatencyFrames" in st and "ringLatencyFrames" in st and "latencyNote" in st, "dither off by default; latency given as the device's part and the ring's part", {k: st.get(k) for k in ("dither", "deviceLatencyFrames", "ringLatencyFrames")})
with e.cv: na = len(e.answers)
e.p.stdin.write('{"cmd":"status","req":77,,}\n'); e.p.stdin.flush(); time.sleep(0.3)
with e.cv: bad = [a for a in e.answers[na:] if a.get("re") == "?"]
check(bad and bad[0].get("req") == 77 and bad[0].get("ok") is False, "a line that is not JSON is answered with its request number, not left waiting", bad)
for a in bad: e.answers.remove(a)
refused = []
for kw in ({"buffer": -5}, {"buffer": 1e12}, {"buffer": 3.5}, {"buffer": "abc"}, {"bits": 99}, {"rate": -48000}, {"id": -1}):
    r = e.cmd(cmd="open", **(kw if "id" in kw else dict(kw, uid="al-null-1")))
    refused.append(not r.get("ok") and list(kw)[0] in r.get("error", ""))
st = e.cmd(cmd="status")
check(all(refused) and st.get("open") is True and st.get("rate") == 48000, "bad numbers (negative, huge, fractions, text, out of range) are refused by name; the device keeps running", refused)
r1 = e.cmd(cmd="source", type="socket", path=sock, pageRate=48000, prefillMs=1e9)
r2 = e.cmd(cmd="source", type="socket", path=sock, pageRate=48000, prefillMs=100, highMs=50)
v1 = e.cmd(cmd="volume", value=float("nan")); v2 = e.cmd(cmd="volume", value=2)
check(not r1.get("ok") and not r2.get("ok") and not v1.get("ok") and not v2.get("ok"), "a ring size out of range, a ring with its top below its prefill, a volume of NaN or 2: refused", [r1.get("error"), r2.get("error"), v1.get("error"), v2.get("error")])
# the volume: ramp and ceiling (the device has been at 0.75, set outside the engine above)
ceil0 = e.cmd(cmd="status").get("volumeCeiling")
v = e.cmd(cmd="volume", value=0.9)
check(not v.get("ok") and v.get("needsConfirm") and abs(v.get("ceiling", 0) - 0.75) < 1e-9, "louder than the device has been (0.75): refused until confirmed", v)
n5 = len(e.events)
t5 = time.time(); v = e.cmd(cmd="volume", value=0.9, confirm=True); mid = e.cmd(cmd="status").get("volume")
evr = e.wait_event("volume", 3, n5, lambda x: x.get("ramped")); took5 = time.time() - t5
steps = [x for x in e.events[n5:] if x.get("ev") == "volume" and not x.get("ramped")]
check(v.get("ok") and v.get("ramping") and evr and abs(evr["value"] - 0.9) < 1e-9, "confirmed: the volume goes to 0.9 in a ramp (%d ms)" % (took5 * 1000), [v, evr])
check(mid is not None and mid < 0.9, "half way through the ramp the device is not yet at 0.9 (%.2f)" % (mid or -1), mid)
check(len(steps) == 0, "the ramp's own steps do not flood the page with events (one event at the end)", len(steps))
v = e.cmd(cmd="volume", value=0.95)
check(not v.get("ok") and v.get("needsConfirm") and abs(v.get("ceiling", 0) - 0.9) < 1e-9, "the confirmed level is the new ceiling (0.95 needs a confirmation again)", v)
v = e.cmd(cmd="volume", value=0.2); evr = e.wait_event("volume", 3, len(e.events) - 0, lambda x: x.get("ramped") and abs(x.get("value", 0) - 0.2) < 1e-9)
check(v.get("ok"), "quieter needs no confirmation", v)
# output protection
r = e.cmd(cmd="source", type="socket", path=sock, pageRate=48000, prefillMs=30, highMs=120)
special = [float("nan"), float("inf"), float("-inf"), 2.0, -3.0, 1.0, -1.0, -0.0, 0.5, 1e30]
def blocksP(total):
    for k in range(total // 128):
        fr = [0.25, -0.25] * 128
        if k == 20: fr[:len(special)] = special
        yield struct.pack("<%df" % len(fr), *fr)
stP = threading.Event(); thP = threading.Thread(target=sender, args=(sock, blocksP(48000), 48000, stP, [])); thP.start(); thP.join(); time.sleep(0.4)
st = e.cmd(cmd="status")
pr = st.get("protect", {})
check(pr.get("nonFinite") == 3 and pr.get("clipped") == 3 and st.get("peak", 9) <= 1.0, "NaN and infinity never reach the device (3 counted), samples past full scale held at full scale (3 counted), peak at most 1.0", {"protect": pr, "peak": st.get("peak")})
# a format change from outside: the stream starts again in the new format; 24-bit samples pass the integer path bit for bit
r = e.cmd(cmd="source", type="silence")
n6 = len(e.events)
x = e.cmd(cmd="null", change="format", value=24, id=1)
ev = e.wait_event("format", 3, n6)
st = e.cmd(cmd="status")
check(x.get("ok") and ev and ev.get("restarted") is True and "24-bit integer" in ev.get("handedToUs", "") and st.get("formatRestarts") == 1, "another program sets 24-bit integer: the engine restarts its stream in that format", ev)
r = e.cmd(cmd="source", type="socket", path=sock, pageRate=48000, prefillMs=60, highMs=600)
sent24 = []
def blocks24(total):
    for b in range(0, total, 128):
        fr = []
        for i in range(b, b + 128):
            v = ((i * 977) % 8388607 - 4194303) / 8388608.0   # exact 24-bit values
            fr += [v, -v]
        yield struct.pack("<%df" % len(fr), *fr)
st24 = threading.Event()
th24 = threading.Thread(target=sender, args=(sock, blocks24(48000), 48000, st24, sent24)); th24.start(); th24.join(); time.sleep(0.4)
e.cmd(cmd="source", type="silence")
d16 = e.cmd(cmd="open", uid="al-null-1", rate=48000, dither=True); st = e.cmd(cmd="status")
check(st.get("dither") is True, "dither only when asked for", st.get("dither"))
e.cmd(cmd="null", change="format", value=32, id=1)
# a broken WAV file (format chunk longer than the file) is refused, nothing read past the end
bw = os.path.join(out, "broken.wav")
open(bw, "wb").write(b"RIFF" + struct.pack("<I", 30) + b"WAVEfmt " + struct.pack("<I", 1000) + b"\x03\x00\x02\x00")
r = e.cmd(cmd="source", type="file", path=bw)
check(not r.get("ok") and e.cmd(cmd="status").get("open") is True, "a broken WAV file is refused, the engine keeps running", r)

# ---- task NB-R4b: what the engine says never holds the sound (review C9); the format restart never waits in the listener ----
check(ready and ready.get("engine") == "alengine 0.6", "ready says alengine 0.6", ready)
o = e.cmd(cmd="open", uid="al-null-1", rate=48000, buffer=128)
r = e.cmd(cmd="source", type="socket", path=sock, pageRate=48000, prefillMs=30, highMs=600)
with e.cv: na = len(e.answers)
e.hold.set()                                       # the shell stops reading (busy, hung): the output pipe fills
def flood():
    for k in range(3000):
        e.p.stdin.write(json.dumps({"cmd": "null", "change": "volume", "value": 0.3 + (k % 2) * 0.01, "id": 1}) + "\n")
    e.p.stdin.flush()
thF = threading.Thread(target=flood, daemon=True); thF.start(); thF.join(4)
check(not thF.is_alive(), "with its output unread the engine still takes every command (3,000 written)")   # before NB-R4b it stopped reading here
time.sleep(0.8)
stopH = threading.Event(); sentH = []
t3 = time.time()
thH = threading.Thread(target=sender, args=(sock, blocks(72000), 48000, stopH, sentH), daemon=True); thH.start()   # connecting makes the socket thread say "sound-connected"
thH.join(6); tookH = time.time() - t3; doneH = not thH.is_alive()
check(r.get("ok") and doneH and tookH < 2.5, "with the output pipe full and unread, a new sender connects and 1.5 s of sound goes in at its own pace (%.2f s)" % tookH, {"done": doneH, "took": tookH})
e.hold.clear(); stopH.set(); thH.join(3); thF.join(10)
time.sleep(0.5)
with e.cv: nulls = [a for a in e.answers[na:] if a.get("re") == "null"]
st = e.cmd(cmd="status")
outq = st.get("output", {})
check(st.get("ring", {}).get("received") == 72064 and st.get("ring", {}).get("droppedFrames", 1) == 0 and st.get("ring", {}).get("ranEmpty", 9) <= 1, "every frame of it reached the ring (563 blocks), nothing dropped, empty only when the sender stopped", st.get("ring"))
check(len(nulls) == 3000 and outq.get("waitingMax", 0) > 1000, "once read again, all 3,000 answers arrive (none dropped; up to %d lines waited, %d events dropped and counted)" % (outq.get("waitingMax", 0), outq.get("eventsDropped", 0)), {"answers": len(nulls), "output": outq})
with e.cv:
    for a in nulls: e.answers.remove(a)
e.cmd(cmd="source", type="silence")
# format changes while the command thread opens the device again and again: every command answered, no deadlock
t4 = time.time(); okc = 0
for k in range(40):
    e.cmd(cmd="null", change="format", value=24 if k % 2 == 0 else 32, id=1)
    if e.cmd(cmd="open", uid="al-null-1", rate=48000, buffer=128, timeout=5).get("ok"): okc += 1
time.sleep(0.5); st = e.cmd(cmd="status")
check(okc == 40 and st.get("open") is True and time.time() - t4 < 20, "40 format changes from outside while the device is opened 40 times: every open answered (%.1f s), restarts %d" % (time.time() - t4, st.get("formatRestarts", 0)), {"ok": okc, "st": st.get("formatRestarts")})
e.cmd(cmd="null", change="format", value=32, id=1); time.sleep(0.2)
# a file at another rate than the device would play at the wrong speed: refused (anyRate lets it)
wav441 = os.path.join(out, "tone441.wav")
fr = struct.pack("<%df" % 8820, *([0.1, -0.1] * 4410))
with open(wav441, "wb") as f:
    f.write(b"RIFF" + struct.pack("<I", 36 + len(fr)) + b"WAVEfmt " + struct.pack("<IHHIIHH", 16, 3, 2, 44100, 44100 * 8, 8, 32) + b"data" + struct.pack("<I", len(fr)) + fr)
f1 = e.cmd(cmd="source", type="file", path=wav441); f2 = e.cmd(cmd="source", type="file", path=wav441, anyRate=True)
check(f1.get("ok") is False and "44100" in f1.get("error", "") and "48000" in f1.get("error", "") and f2.get("ok"), "a 44.1 kHz file on a 48 kHz device is refused with both rates named (anyRate plays it)", [f1.get("error"), f2.get("ok")])
e.cmd(cmd="source", type="silence")

q = e.cmd(cmd="quit")
try: e.p.wait(5)
except subprocess.TimeoutExpired: e.p.kill()
check(e.p.returncode == 0, "the engine quits cleanly", e.p.returncode)
err = "".join(e.stderr)
open(os.path.join(out, "engine_stderr.txt"), "w").write(err)
check("WARNING: ThreadSanitizer" not in err and "ERROR: AddressSanitizer" not in err and "runtime error" not in err, "no sanitizer report", err[-1500:])

# ---- the recording: the first 2 s must be in it bit for bit ---------------------------------------------------------------------------
if os.path.exists(REC):
    sr, rec = wav_floats(REC)
    want = struct.unpack("<%df" % (len(b"".join(sent)) // 4), b"".join(sent))
    # find the first sent sample in the recording, then compare the run
    first = want[0]; pos = -1
    for i in range(0, len(rec), 2):
        if rec[i] == first: pos = i; break
    same = 0
    if pos >= 0:
        for j in range(len(want)):
            if pos + j >= len(rec) or rec[pos + j] != want[j]: break
            same += 1
    check(same == len(want), "the first 2 s came out of the device bit for bit (%d of %d samples)" % (same, len(want)), {"pos": pos})
else:
    check(False, "the null device wrote a recording")
# task NB-R4: the stream that ran 24-bit integer wrote its own recording (path.N.wav); the 1 s sent must be in it bit for bit
want24 = struct.unpack("<%df" % (len(b"".join(sent24)) // 4), b"".join(sent24))
found = -1
for f in sorted(x for x in os.listdir(out) if x.startswith("null_record.wav.")):
    sr, rec = wav_floats(os.path.join(out, f))
    try: pos = rec.index(want24[0])
    except ValueError: continue
    if rec[pos:pos + len(want24)] == want24: found = len(want24); break
    found = max(found, sum(1 for a, b in zip(rec[pos:pos + len(want24)], want24) if a == b))
check(found == len(want24), "24-bit samples through the integer path (the engine writes the DAC's bytes) come out bit for bit (%d of %d)" % (max(found, 0), len(want24)))

ok = all(r[0] for r in results)
print(json.dumps({"re": "engine_null_test", "ok": ok, "passed": sum(r[0] for r in results), "failed": sum(not r[0] for r in results)}))
sys.exit(0 if ok else 1)
