"""The deepest integer format on the wire (task NB-N1c), on the null device. Pure Python, runs anywhere.

    python3 tools/native-lab/engine_deepest_test.py path/to/alengine

The user's reports 6 and 7: the iFi Gryphon ran at 16-bit integer on the wire, so macOS turned the float mix into
16 bits before the DAC. With "bits":"deepest" alengine sets the deepest integer format the device offers at the rate it
runs (24-bit on the null device, which offers 16 and 24 bits mixed by the system, and 16 and 24 bits not mixed),
reports the depth it could have (deepestIntegerBits), and keeps the deepest after a rate change from outside.
Checks:
  - a device left at 16-bit integer (as the Gryphon was): status says onTheWire 16-bit and deepestIntegerBits 24;
  - open with bits "deepest": 24-bit integer, mixable; keepsDeepest true;
  - with integer true: 24-bit integer, not mixable, and the stream is handed 24-bit integer (the integer path);
  - another program changes the rate: the engine sets the deepest format again at the new rate (event "deepest");
  - a plain open with bits 16 still means 16 and turns keeping the deepest off; a wrong word is refused.
"""
import json, os, subprocess, sys, threading, time

exe = sys.argv[1]
results = []


def check(ok, what, extra=None):
    results.append(bool(ok))
    print(("ok   " if ok else "FAIL ") + what + ("" if ok or extra is None else "  (" + json.dumps(extra)[:500] + ")"), flush=True)


class Engine:
    def __init__(self):
        self.p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, bufsize=1)
        self.answers, self.events = [], []
        self.cv = threading.Condition()
        threading.Thread(target=self._read, daemon=True).start()

    def _read(self):
        for line in self.p.stdout:
            try: m = json.loads(line)
            except Exception: continue
            with self.cv:
                (self.events if "ev" in m else self.answers).append(m); self.cv.notify_all()

    def cmd(self, timeout=10, **o):
        self.p.stdin.write(json.dumps(o) + "\n"); self.p.stdin.flush()
        t = time.time() + timeout
        with self.cv:
            while True:
                for a in self.answers:
                    if a.get("re") == o["cmd"]:
                        self.answers.remove(a); return a
                left = t - time.time()
                if left <= 0: return {"ok": False, "error": "no answer to " + o["cmd"]}
                self.cv.wait(left)

    def wait_event(self, ev, timeout=4, since=0):
        t = time.time() + timeout
        with self.cv:
            while True:
                for e in self.events[since:]:
                    if e.get("ev") == ev: return e
                left = t - time.time()
                if left <= 0: return None
                self.cv.wait(left)


e = Engine()
r = e.cmd(cmd="open", uid="al-null-1", rate=48000, bits=16)   # as the user's Gryphon was set in Audio MIDI Setup
st = e.cmd(cmd="status")
check(r.get("ok") and "16-bit integer" in st.get("onTheWire", "") and st.get("deepestIntegerBits") == 24 and st.get("keepsDeepest") is False,
      "a device at 16-bit integer: status says so, and that 24 bits are offered at this rate", st)

r = e.cmd(cmd="open", uid="al-null-1", rate=48000, bits="deepest")
st = e.cmd(cmd="status")
check(r.get("ok") and r.get("notes") == "" and "24-bit integer" in st.get("onTheWire", "") and "mixable" in st.get("onTheWire", "")
      and "not mixable" not in st.get("onTheWire", "") and st.get("keepsDeepest") is True,
      "bits \"deepest\": the deepest integer format (24-bit), mixed by the system", st)

r = e.cmd(cmd="open", uid="al-null-1", rate=96000, bits="deepest", integer=True, exclusive=True)
st = e.cmd(cmd="status")
check(r.get("ok") and "24-bit integer" in st.get("onTheWire", "") and "not mixable" in st.get("onTheWire", "") and "24-bit integer" in st.get("handedToUs", ""),
      "with integer true: 24-bit integer not mixed, and the engine writes the DAC's own bytes (handed 24-bit integer)", st)

n = len(e.events)
x = e.cmd(cmd="null", change="rate", value=44100, id=1)   # the user or another program switches the rate
ev = e.wait_event("deepest", 4, n)
time.sleep(0.3)
st = e.cmd(cmd="status")
check(x.get("ok") and ev is not None and st.get("rate") == 44100 and "24-bit integer" in st.get("onTheWire", "") and "44100" in st.get("onTheWire", ""),
      "a rate change from outside: the deepest integer format is set again at the new rate", {"event": ev, "status": st})

r = e.cmd(cmd="open", uid="al-null-1", rate=48000, bits=16)
st = e.cmd(cmd="status")
check(r.get("ok") and "16-bit integer" in st.get("onTheWire", "") and st.get("keepsDeepest") is False, "bits 16 still means 16, and keeping the deepest is off", st)

r = e.cmd(cmd="open", uid="al-null-1", bits="deep")
check(r.get("ok") is False and "bits" in r.get("error", ""), "a wrong word for bits is refused", r)

r = e.cmd(cmd="open", uid="al-null-2", rate=48000, bits="deepest")
st = e.cmd(cmd="status")
check(r.get("ok") and "24-bit integer" in st.get("onTheWire", ""), "the second device (the Zoom's stand-in) too", st)

e.cmd(cmd="quit", timeout=3)
try: e.p.wait(3)
except Exception: e.p.kill()
print(json.dumps({"re": "engine_deepest", "ok": all(results), "passed": sum(results), "failed": len(results) - sum(results)}))
sys.exit(0 if all(results) else 1)
