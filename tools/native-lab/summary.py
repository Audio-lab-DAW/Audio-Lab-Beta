"""Turns the JSON files of a native lab run into one plain text page (task NM1).

    python3 tools/native-lab/summary.py out > out/RESULTS.md
"""
import glob, json, os, sys
out = sys.argv[1]

def load(name):
    try:
        return json.load(open(os.path.join(out, name)))
    except Exception:
        return None

def text(name):
    try:
        return open(os.path.join(out, name)).read().strip()
    except Exception:
        return ""

L = ["# Native lab results", "", "```", text("machine.txt"), "```", ""]

L += ["## Test A: one effect, native against the web engine", "", "```", text("a.txt") or "did not run", "```", ""]
for name, title in (("devices.json", "Devices of the build machine as it comes"), ("devices_with_blackhole.json", "Devices after adding the virtual device BlackHole")):
    d = load(name)
    L += ["### " + title, ""]
    if not d:
        L += ["no result", ""]
        continue
    if not d["devices"]:
        L += ["The machine reports no audio device at all.", ""]
    for x in d["devices"]:
        rates = ", ".join("%g" % r for r in x["rates"]) + "".join(" %g to %g" % (a, b) for a, b in x["rateRanges"])
        L.append("- **%s** (%s%s): out %d ch, in %d ch, %g Hz now; rates offered: %s; rate can be set: %s; buffer %d (range %d to %d, can be set: %s); volume the computer can set: %s; on the wire: %s; exclusive use can be taken: %s" % (
            x["name"], x["transport"], ", default output" if x["defaultOutput"] else "", x["outChannels"], x["inChannels"], x["rate"], rates or "none listed", "yes" if x["rateSettable"] else "no",
            x["buffer"], x["bufferMin"], x["bufferMax"], "yes" if x["bufferSettable"] else "no",
            ("yes (%s)" % x["volumeWhere"]) if x["volumeSettable"] else ("has one, fixed" if x["hasVolume"] else "no"), x["physicalFormat"] or "?", "yes" if x["hogSettable"] else "no"))
    L.append("")
for name, title in (("play.json", "Opening the default output"), ("play_blackhole.json", "Opening BlackHole")):
    p = load(name)
    L += ["### " + title, ""]
    if not p:
        L += ["no result", ""]
        continue
    if not p.get("opened"):
        L += ["Not opened: %s" % p.get("why", "?"), ""]
    else:
        L.append("- opened **%s** through Core Audio and played %.1f s: %d callbacks, %d to %d frames per callback, %d overloads, render %.1f microseconds on average" % (
            p["device"]["name"], p["seconds"], p["callbacks"], p["framesPerCallbackMin"], p["framesPerCallbackMax"], p["overloads"], p["renderAvgMicroseconds"]))
    if "bufferAsked" in p:
        L.append("- buffer: asked for %s frames, device now runs %s (%s)" % (p["bufferAsked"], p["bufferNow"], "accepted" if p["bufferSet"] else "not accepted " + p.get("bufferError", "")))
    if "rateAsked" in p:
        L.append("- sample rate: asked for %g Hz, device then ran %g Hz (%s); put back to %g Hz (%s)" % (p["rateAsked"], p["rateNow"], "switched" if p["rateSet"] else "not switched " + p.get("rateError", ""), p["rateAfter"], "ok" if p["rateRestored"] else "not restored"))
    if "hogTaken" in p:
        L.append("- exclusive use: %s; given back: %s" % ("taken" if p["hogTaken"] else "not taken " + p.get("hogError", ""), "yes" if p.get("hogReleased") else "no"))
    L.append("")

L += ["## Test B: command line VST3 host", ""]
s = load("scan.json")
if s:
    L.append("Scan: %d bundles, %d read, %d failed, %d plug-ins. The host stayed alive: %s." % (s["bundlesFound"], s["bundlesOk"], s["bundlesFailed"], s["pluginsFound"], "yes" if s["hostStillAlive"] else "no"))
    for b in s["bundles"]:
        nm = os.path.basename(b["path"])
        if b["ok"]:
            L.append("- %s [%s], %.2f s: %s" % (nm, b["archs"], b["seconds"], ", ".join("%s (%s)" % (p["name"], "instrument" if p["instrument"] else "effect") for p in b["plugins"][:8]) + (" and %d more" % (len(b["plugins"]) - 8) if len(b["plugins"]) > 8 else "")))
        else:
            L.append("- %s [%s]: FAILED, %s" % (nm, b["archs"], b["error"]))
    L.append("")
else:
    L += ["scan: no result", ""]

def cmp(c):
    if not c: return "not run"
    if c["identical"]: return "identical"
    return "differs (largest difference %.1f dB)" % c["maxDifferenceDb"] if c["maxDifferenceDb"] is not None else "differs"

for f in sorted(glob.glob(os.path.join(out, "b", "*.json"))):
    try:
        d = json.load(open(f))
    except Exception:
        L += ["- %s: unreadable result" % os.path.basename(f)]; continue
    if not d.get("loaded"):
        L += ["### %s" % os.path.basename(d["bundle"]), "", "NOT LOADED: %s" % d.get("error", "?"), ""]; continue
    L += ["### %s (%s, %s) [%s]" % (d["name"], d["vendor"], d["kind"], d["archs"]), ""]
    if "realtime" not in d:
        L += ["stopped: %s" % d.get("error", "?"), ""]; continue
    pr, st, rt = d["parameters"], d["state"], d["realtime"]
    L.append("- loaded in %.0f ms; audio in %d ch, out %d ch, note inputs %d; latency %d samples" % (d["loadMilliseconds"], d["buses"]["mainInChannels"], d["buses"]["mainOutChannels"], d["buses"]["eventIn"], d["latencySamples"]))
    L.append("- parameters: %d (%d can be automated); first: %s" % (pr["count"], pr["automatable"], ", ".join("%s = %s%s" % (p["name"], p["text"], (" " + p["units"]) if p["units"] else "") for p in pr["first"][:6])))
    L.append("- sound: %s, peak %.1f dB, %d blocks of %d frames at %g Hz, %d failed" % ("notes played" if d["kind"] == "instrument" else "audio run through", rt["peakDb"] if rt["peakDb"] is not None else float("-inf"), rt["blocks"], d["block"], d["sampleRate"], rt["failedBlocks"]))
    c = rt["cpu"]
    L.append("- time per block: average %.1f microseconds (%.2f %% of the block), 99th percentile %.1f, worst %.1f (%.1f %%)" % (c["avgMicroseconds"], c["avgPercentOfBlock"], c["p99Microseconds"], c["worstMicroseconds"], c["worstPercentOfBlock"]))
    L.append("- state: saved %s (%d bytes), restored into a new copy %s; two fresh copies sound: %s; fresh against restored: %s" % ("yes" if st["saved"] else "NO", st["bytes"], "yes" if st["restored"] else "NO", cmp(st.get("twoFreshPluginsSameSound")), cmp(st.get("restoredPluginSameSound"))))
    ch = st.get("changedSetting")
    if ch:
        L.append("- a changed setting (%s: %.3f to %.3f) %s in the saved state (read back %.3f in a new copy)" % (ch["name"], ch["before"], ch["setTo"], "travels" if ch["carried"] else "DID NOT travel", ch["afterRestoreInNewPlugin"]))
    ex = d.get("export")
    if ex:
        L.append("- export mode: %s, peak %.1f dB; against the real-time render: %s" % ("ok" if ex["ok"] else "FAILED", ex["peakDb"] if ex["peakDb"] is not None else float("-inf"), cmp(d.get("exportSameAsRealtime"))))
    o = d.get("at96kBlock32")
    if o:
        L.append("- switched the running plug-in to 96 kHz and 32 frames: %s, peak %.1f dB, average %.2f %% of the block" % ("ok" if o["ok"] else "FAILED", o["peakDb"] if o["peakDb"] is not None else float("-inf"), o["cpu"]["avgPercentOfBlock"]))
    L.append("")

L += ["## Test C: the test app on the build machine", ""]
rep = text("c/AudioLab-VST3-test-report.txt")
L += ["```", rep or "the app did not write a report (see the job log)", "```", ""]
print("\n".join(L))
