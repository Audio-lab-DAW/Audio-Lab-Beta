"""Task NB-R3 (review RN5 A8, test from section 6: "case A again with the main process blocked for 50 ms every
second: no gap"). Runs the real Electron shell with the real alengine on the null device, four times:

  A  the feeder, main process blocked 50 ms every second (waiting, as on sync I/O), 20 s: every frame bit for bit,
     no gap, the ring never empty
  B  the same with 250 ms every second
  E  the feeder, main process spinning 50 ms every second (a handler using a whole core, like hashing a download):
     strict on a machine with 4 or more cores; on fewer it is reported only, because the spin then takes half the
     machine from the page's audio thread (measured here on 2 cores: 2 of 8 runs had one short gap, every one of them
     upstream of the feeder: the blocks reached the feeder up to 74 ms apart)
  C  the comparison: the old path through the main process, held 50 ms every second (reported, not a pass/fail:
     it shows what A8 was about when the hold lands at a bad moment)
  D  the feeder frozen (SIGSTOP) at second 4: the watchdog starts a new feeder, the page hands it a new port,
     the sound comes back by itself and is bit for bit again after the gap

    python3 tools/native-lab/feeder_test.py <electron> <alengine> <outdir>     exit code 0 when all checks pass
Linux needs a display (xvfb-run) and --no-sandbox; the script adds --no-sandbox off the Mac.
"""
import json, os, subprocess, sys

electron, engine, out = sys.argv[1], os.path.abspath(sys.argv[2]), os.path.abspath(sys.argv[3])
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MAIN = os.path.join(ROOT, "tools", "native-lab", "electron-feeder", "main.js")
CHECK = os.path.join(ROOT, "tools", "native-lab", "feeder_check.py")
results = []


def check(ok, what, extra=None):
    results.append(bool(ok))
    print(("ok   " if ok else "FAIL ") + what + ("" if ok or extra is None else "  (" + json.dumps(extra)[:600] + ")"), flush=True)


def run(name, seconds, hold, stop_at=0, in_main=False, kind="wait"):
    d = os.path.join(out, name); os.makedirs(d, exist_ok=True)
    rec = os.path.join(d, "rec.wav")
    env = dict(os.environ, AL_ENGINE=engine, AL_ENGINE_TEST="1", AL_NULL_RECORD=rec)
    env.pop("AL_FEED_IN_MAIN", None)
    if in_main: env["AL_FEED_IN_MAIN"] = "1"
    cmd = [electron] + (["--no-sandbox"] if sys.platform != "darwin" else []) + [MAIN, d, str(seconds), str(hold), str(stop_at), kind]
    p = subprocess.run(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=seconds + 90)
    open(os.path.join(d, "electron-stderr.txt"), "w").write(p.stderr[-20000:])
    try: R = json.load(open(os.path.join(d, "feeder.json")))
    except Exception: R = {"error": "no result; stderr: " + p.stderr[-800:]}
    C = {}
    if os.path.exists(rec) and os.path.exists(os.path.join(d, "sent.raw")):
        C = json.loads(subprocess.run([sys.executable, CHECK, rec, os.path.join(d, "sent.raw")], stdout=subprocess.PIPE, text=True).stdout)
    last = (R.get("statuses") or [{}])[-1]
    print("  " + name + ": " + json.dumps({k: C.get(k) for k in ("identical", "sentFrames", "gaps", "gapMsList", "lostFrames", "wrongFrames")}) +
          " ranEmpty " + str(last.get("ranEmpty")) + ", tap " + str(last.get("tapPath")) + ", worst gap between blocks " + str(last.get("worstGapMs")) + " ms" +
          ", back-pressure " + str(last.get("backPressure")) + ", holds " + str(R.get("holds")) + " of " + str(sorted(set(R.get("blocks") or []))[-1:] or "-") + " ms", flush=True)
    return R, C, last


print("machine: %d cores" % (os.cpu_count() or 0), flush=True)
A, CA, la = run("A-feeder-50ms", 20, 50)
check(not A.get("error") and A["page"]["sound"]["feeder"], "A: the sound path is the feeder process", A.get("error") or A["page"].get("sound"))
check(la.get("tapPath") == "feeder" and la.get("feederPid"), "A: the engine's status names the feeder and its process", la)
check(A.get("holds", 0) >= 18 and min(A.get("blocks") or [0]) >= 49, "A: the main process was blocked 50 ms every second (" + str(A.get("holds")) + " times)", A.get("blocks"))
check(CA.get("ok"), "A: every one of " + str(CA.get("sentFrames")) + " frames came out of the device bit for bit, no gap, nothing lost", CA)
check(la.get("ranEmpty") == 0 and la.get("droppedFrames") == 0, "A: the engine's ring never ran empty, the feeder dropped nothing", la)

B, CB, lb = run("B-feeder-250ms", 12, 250)
check(CB.get("ok") and lb.get("ranEmpty") == 0, "B: main process blocked 250 ms every second: still bit for bit, no gap", [CB, lb])

E, CE, le = run("E-feeder-busy-50ms", 20, 50, kind="busy")
eok = CE.get("ok") and le.get("ranEmpty") == 0
if (os.cpu_count() or 0) >= 4:
    check(eok, "E: main process spinning 50 ms every second: still bit for bit, no gap", [CE, le])
else:
    print("  E, reported only (%d cores): %s" % (os.cpu_count() or 0, "bit for bit, no gap" if eok else "gaps " + str(CE.get("gapMsList")) + " ms, blocks reached the feeder up to " + str(le.get("worstGapMs")) + " ms apart"), flush=True)

C, CC, lc = run("C-main-50ms", 20, 50, in_main=True, kind="busy")
check(lc.get("tapPath") == "main" and not C.get("error"), "C: the comparison ran through the main process (the path before NB-R3)", lc)
print("  C, for comparison: " + ("the old path made " + str(CC.get("gaps")) + " gap(s) (" + str(CC.get("gapMsList")) + " ms), the ring ran empty " + str(lc.get("ranEmpty")) + " time(s)"
      if (CC.get("gaps") or lc.get("ranEmpty")) else "the old path made no gap in this run (it depends on where the hold lands against the ring's 30 ms prefill)"), flush=True)

D, CD, ld = run("D-feeder-frozen", 14, 50, stop_at=4)
ev = [e for e in (D.get("page") or {}).get("events", []) if e.get("ev") == "feeder-restarted"]
check(D.get("stopped") and D["stopped"].get("pid"), "D: the feeder was frozen at second 4", D.get("stopped"))
check(len(ev) == 1 and ev[0].get("ok") and ev[0].get("needPort"), "D: the watchdog started a new feeder and told the page ('feeder-restarted', needPort)", ev)
check((D.get("page") or {}).get("tapInfo", {}).get("reconnects") == 1, "D: the page handed the new feeder a new port", (D.get("page") or {}).get("tapInfo"))
check(ld.get("feederPid") and ld.get("feederPid") != D["stopped"].get("pid") and ld.get("blocks", 0) > 0, "D: a new feeder process carries the sound", ld)
check(CD.get("wrongFrames") == 0 and CD.get("gaps", 0) >= 1 and CD.get("reachedSentEnd") and CD.get("identical", 0) > 8 * 48000,
      "D: the sound came back by itself, bit for bit after the gap (" + str(CD.get("gapMsList")) + " ms silent, " + str(CD.get("lostFrames")) + " frames lost while frozen, never a wrong sample)", CD)
try:
    os.kill(D["stopped"]["pid"], 0); alive = True
except Exception:
    alive = False
check(not alive, "D: the frozen feeder was killed, not left behind")

summary = {"re": "feeder_test", "ok": all(results), "passed": sum(results), "failed": len(results) - sum(results),
           "cores": os.cpu_count(), "A": CA, "B": CB, "E": CE, "C": CC, "C_ranEmpty": lc.get("ranEmpty"), "D": CD}
json.dump(summary, open(os.path.join(out, "summary.json"), "w"), indent=1)
print(json.dumps({k: summary[k] for k in ("re", "ok", "passed", "failed")}))
sys.exit(0 if summary["ok"] else 1)
