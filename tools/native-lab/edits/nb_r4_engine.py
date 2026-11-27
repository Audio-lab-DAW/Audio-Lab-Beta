"""Task NB-R4a, part 2: alengine 0.5, hardening (review RN5 C6, C7, C8, C10, A10). Anchors asserted once.
- protect (C6): NaN and infinity become silence and are counted, samples past full scale are held at +-1.0 and counted;
  every legal sample passes untouched (bit-transparent)
- device volume (C6): changes are ramped (at most 0.02 every 5 ms) and anything above the loudest level the device
  has had (its level when the engine first opened it, a level confirmed with "confirm":true, or a level the user set
  outside the engine) is refused unless confirmed; the ramp's own steps do not flood the page with events
- format changes (C7): a "format" event from the device layer restarts the stream in the new format; dither is off
  unless "dither":true is given to open
- latency (C8): status names the device's part and the ring's part instead of one figure that left the ring out
- numbers (C10): buffer, id, bits, rate, value, prefillMs, highMs, limitPpm checked (whole, finite, in range) before use
- protocol (A10): "protocol":1 in ready; a "req" number in a command comes back in its answer, also on a parse error
"""
import os
p = os.path.join(os.path.dirname(__file__), "..", "..", "..", "native", "engine", "engine_main.cpp")
s = open(p).read()
def rep(a, b):
    global s
    assert s.count(a) == 1, a[:80]; s = s.replace(a, b)

rep("""//   {"cmd":"volume","value":0.5}   {"cmd":"mute","on":true}   {"cmd":"status"}   {"cmd":"close"}   {"cmd":"quit"}""",
"""//   {"cmd":"volume","value":0.5,"confirm":false}   {"cmd":"mute","on":true}   {"cmd":"status"}   {"cmd":"close"}   {"cmd":"quit"}
// Protocol 1 (task NB-R4): "ready" says "protocol":1; a command may carry "req":<number>, its answer carries the same.
// The device volume moves in a ramp, and above the loudest level the device has had it needs "confirm":true.""")
rep("#include <iostream>\n", "#include <iostream>\n#include <map>\n")
rep("""    std::atomic<float> peak{0};
};""", """    std::atomic<float> peak{0};
    // task NB-R4: output protection (C6), the stream restarted on a format change (C7), the device volume's ramp and ceiling
    std::atomic<uint64_t> nonFinite{0}, clipped{0}, formatRestarts{0};
    std::mutex devLock;                      // open, close and the format restart
    std::thread fmtThread;
    std::thread rampThread; std::atomic<bool> ramping{false}, rampStop{false};
    std::map<uint32_t, double> ceiling;      // per device: the loudest level it has had (command thread only)
    std::mutex ceilLock;
};""")
rep("""    float pk = E.peak.load();
    for (int i = 0; i < frames; i++)""", """    // task NB-R4 (review C6): NaN and infinity become silence, anything past full scale is held at full scale. Every legal
    // sample (-1 to 1, and -0) passes untouched, so this costs nothing in bit-perfect terms.
    uint32_t nf = 0, cl = 0;
    for (int c = 0; c < 2; c++) { float* o = out[c]; for (int i = 0; i < frames; i++) { float x = o[i]; if (!std::isfinite(x)) { o[i] = 0.f; nf++; } else if (x > 1.f) { o[i] = 1.f; cl++; } else if (x < -1.f) { o[i] = -1.f; cl++; } } }
    if (nf) E.nonFinite += nf;
    if (cl) E.clipped += cl;
    float pk = E.peak.load();
    for (int i = 0; i < frames; i++)""")
rep("""",\\"volume\\":" + jnum(vol) + ",\\"mute\\":" + tf(mute) + ",\\"latencyFrames\\":" + std::to_string(d.latency + d.safetyOffset + d.streamLatency + d.buffer) +""",
"""",\\"volume\\":" + jnum(vol) + ",\\"mute\\":" + tf(mute) + ",\\"latencyFrames\\":" + std::to_string(d.latency + d.safetyOffset + d.streamLatency + d.buffer) +
        // task NB-R4 (review C8): the figure above is the device's part only; sound from the page also waits in the ring
        ",\\"deviceLatencyFrames\\":" + std::to_string(d.latency + d.safetyOffset + d.streamLatency + d.buffer) +
        ",\\"ringLatencyFrames\\":" + std::to_string(E.source.load() == 3 && E.ring.frames ? E.ring.fill() : 0) +
        ",\\"latencyNote\\":" + jstr("device part (buffer, device, safety and stream latency) plus, for sound from the page, the ring; the page's own output buffering is not included") +
        ",\\"protect\\":{\\"nonFinite\\":" + std::to_string(E.nonFinite.load()) + ",\\"clipped\\":" + std::to_string(E.clipped.load()) + "}" +
        ",\\"dither\\":" + tf(E.stream.dither16) + ",\\"formatRestarts\\":" + std::to_string(E.formatRestarts.load()) + ",\\"volumeCeiling\\":" + jnum(ceilingOf(E.dev)) + ",\\"ramping\\":" + tf(E.ramping.load()) +""")
rep("""static std::string statusJson() {""", """static double ceilingOf(uint32_t dev) { std::lock_guard<std::mutex> g(E.ceilLock); auto it = E.ceiling.find(dev); return it == E.ceiling.end() ? -1 : it->second; }
static void raiseCeiling(uint32_t dev, double v) { if (!(v >= 0)) return; std::lock_guard<std::mutex> g(E.ceilLock); auto it = E.ceiling.find(dev); if (it == E.ceiling.end() || v > it->second) E.ceiling[dev] = v; }
static void stopRamp() { E.rampStop = true; if (E.rampThread.joinable()) E.rampThread.join(); E.rampStop = false; E.ramping = false; }

// task NB-R4 (review C10): a number from the page is used only when it is a plain finite number in range
static bool numArg(const Msg& m, const char* k, double lo, double hi, bool whole, double& out, std::string& err) {
    std::string raw = m.str(k); char* end = nullptr;
    double v = raw.empty() ? NAN : strtod(raw.c_str(), &end);
    if (raw.empty() || (end && *end) || !std::isfinite(v) || v < lo || v > hi || (whole && v != std::floor(v))) {
        err = std::string(k) + " must be " + (whole ? "a whole number" : "a number") + " from " + jnum(lo) + " to " + jnum(hi) + " (got " + (raw.empty() ? "nothing" : raw) + ")";
        return false;
    }
    out = v; return true;
}
static std::string statusJson() {""")
# open: checked numbers, dither, ceiling, lock
rep("""    uint32_t want = 0;
    if (m.has("uid")) want = deviceByUid(m.str("uid"));
    else if (m.has("id")) want = (uint32_t)m.num("id");""", """    uint32_t want = 0; std::string bad; double x = 0;
    if (m.has("id") && !m.has("uid") && !numArg(m, "id", 1, 4294967295.0, true, x, bad)) return "\\"ok\\":false,\\"error\\":" + jstr(bad);
    if (m.has("buffer") && !numArg(m, "buffer", 1, 65536, true, x, bad)) return "\\"ok\\":false,\\"error\\":" + jstr(bad);
    if (m.has("bits") && !numArg(m, "bits", 8, 32, true, x, bad)) return "\\"ok\\":false,\\"error\\":" + jstr(bad);
    if (m.has("rate") && !numArg(m, "rate", 0, 10000000, false, x, bad)) return "\\"ok\\":false,\\"error\\":" + jstr(bad);
    std::lock_guard<std::mutex> dl(E.devLock);
    if (m.has("uid")) want = deviceByUid(m.str("uid"));
    else if (m.has("id")) want = (uint32_t)m.num("id");""")
rep("""    closeDevice(want != E.dev || !m.flag("exclusive"));""", """    if (want != E.dev) stopRamp();
    closeDevice(want != E.dev || !m.flag("exclusive"));""")
rep("""    resetCounters();
    bool ok = E.stream.start(want, render, nullptr, err);""", """    resetCounters();
    { double v0 = -1; if (getVolume(want, v0)) { std::lock_guard<std::mutex> g(E.ceilLock); if (!E.ceiling.count(want)) E.ceiling[want] = v0; } }
    E.stream.dither16 = m.flag("dither", false);   // task NB-R4 (review C7): off unless asked for
    E.nonFinite = 0; E.clipped = 0;
    bool ok = E.stream.start(want, render, nullptr, err);""")
rep("""static void closeDevice(bool releaseHog) {""", """static void closeDeviceLocked(bool releaseHog);
static void closeDevice(bool releaseHog) { std::lock_guard<std::mutex> g(E.devLock); closeDeviceLocked(releaseHog); }
static void closeDeviceLocked(bool releaseHog) {""")
rep("""    if (want != E.dev) stopRamp();
    closeDevice(want != E.dev || !m.flag("exclusive"));""", """    if (want != E.dev) stopRamp();
    closeDeviceLocked(want != E.dev || !m.flag("exclusive"));""")
# watch: volume events during a ramp, ceiling from outside, format
rep("""    if (w == "volume" || w == "mute") { double v = -1; getVolume(E.dev, v); bool mu = false; getMute(E.dev, mu); say("{\\"ev\\":\\"volume\\",\\"value\\":" + jnum(v) + ",\\"mute\\":" + tf(mu) + "}"); }""",
"""    if (w == "volume" || w == "mute") {
        if (E.ramping.load()) return;   // task NB-R4: the ramp's own steps; one event comes when it ends
        double v = -1; getVolume(E.dev, v); bool mu = false; getMute(E.dev, mu);
        raiseCeiling(E.dev, v);         // a level set outside the engine (the user in Audio MIDI Setup, the DAC's knob reported back)
        say("{\\"ev\\":\\"volume\\",\\"value\\":" + jnum(v) + ",\\"mute\\":" + tf(mu) + "}");
    }
    else if (w == "format") {
        // task NB-R4 (review C7): another program, Audio MIDI Setup or a re-plug changed the format: start the stream
        // again so it writes the new layout (never the old bytes into a new format). Not on the listener's thread.
        if (E.fmtThread.joinable()) E.fmtThread.join();
        E.fmtThread = std::thread([] {
            std::lock_guard<std::mutex> g(E.devLock);
            if (!E.isOpen) return;
            std::string now = virtualFormatText(E.dev);
            if (now == E.stream.formatText) { say("{\\"ev\\":\\"format\\",\\"handedToUs\\":" + jstr(now) + ",\\"restarted\\":false}"); return; }
            bool d16 = E.stream.dither16; E.stream.stop(); E.stream.dither16 = d16;
            std::string err; bool ok = E.stream.start(E.dev, render, nullptr, err); E.isOpen = ok; E.formatRestarts++;
            say("{\\"ev\\":\\"format\\",\\"handedToUs\\":" + jstr(E.stream.formatText) + ",\\"restarted\\":" + tf(ok) + ",\\"error\\":" + jstr(err) + "}");
        });
    }""")
rep("""\\"rateContract\\":true,\\"pid\\":""", """\\"rateContract\\":true,\\"protocol\\":1,\\"pid\\":""")
rep("alengine 0.4", "alengine 0.5")
rep("""        if (!parseMsg(line, m)) { say("{\\"re\\":\\"?\\",\\"ok\\":false,\\"error\\":\\"not a JSON object\\"}"); continue; }
        std::string c = m.str("cmd"), re = "{\\"re\\":" + jstr(c) + ",";""",
"""        // task NB-R4 (review A10): "req" comes back in the answer, so a caller matches answers by number, not by name
        if (!parseMsg(line, m)) {
            std::string rq; size_t k = line.find("\\"req\\":");
            if (k != std::string::npos) { char* e = nullptr; double v = strtod(line.c_str() + k + 6, &e); if (e != line.c_str() + k + 6 && std::isfinite(v)) rq = ",\\"req\\":" + jnum(v); }
            say("{\\"re\\":\\"?\\"" + rq + ",\\"ok\\":false,\\"error\\":\\"not a JSON object\\"}"); continue;
        }
        std::string c = m.str("cmd"), rq;
        { double v = 0; std::string e; if (m.has("req") && numArg(m, "req", -9007199254740991.0, 9007199254740991.0, false, v, e)) rq = ",\\"req\\":" + jnum(v); }
        std::string re = "{\\"re\\":" + jstr(c) + rq + ",";""")
rep("""        else if (c == "formats") { uint32_t d = m.has("uid") ? deviceByUid(m.str("uid")) : m.has("id") ? (uint32_t)m.num("id") : E.dev.load(); say(re + "\\"formats\\":" + formatsJson(d) + "}"); }""",
"""        else if (c == "formats") { double x = 0; std::string e; if (m.has("id") && !m.has("uid") && !numArg(m, "id", 1, 4294967295.0, true, x, e)) { say(re + "\\"ok\\":false,\\"error\\":" + jstr(e) + "}"); continue; }
            uint32_t d = m.has("uid") ? deviceByUid(m.str("uid")) : m.has("id") ? (uint32_t)x : E.dev.load(); say(re + "\\"formats\\":" + formatsJson(d) + "}"); }""")
rep("""        else if (c == "volume") { std::string e; bool ok = setVolume(E.dev, m.num("value"), e); double v = -1; getVolume(E.dev, v); say(re + "\\"ok\\":" + tf(ok) + ",\\"error\\":" + jstr(e) + ",\\"value\\":" + jnum(v) + "}"); }""",
"""        else if (c == "volume") {
            // task NB-R4 (review C6): a ramp, never a jump; louder than the device has been only with "confirm":true
            double want = 0, cur = -1; std::string e; uint32_t dev = E.dev.load();
            if (!numArg(m, "value", 0, 1, false, want, e)) { getVolume(dev, cur); say(re + "\\"ok\\":false,\\"error\\":" + jstr(e) + ",\\"value\\":" + jnum(cur) + "}"); continue; }
            if (!getVolume(dev, cur)) { bool ok = setVolume(dev, want, e); say(re + "\\"ok\\":" + tf(ok) + ",\\"error\\":" + jstr(e) + ",\\"value\\":-1}"); continue; }
            double ceil = ceilingOf(dev); if (ceil < 0) { raiseCeiling(dev, cur); ceil = ceilingOf(dev); }
            if (want > ceil + 1e-6 && !m.flag("confirm")) {
                say(re + "\\"ok\\":false,\\"needsConfirm\\":true,\\"ceiling\\":" + jnum(ceil) + ",\\"value\\":" + jnum(cur) + ",\\"error\\":" + jstr("louder than this device has been (" + jnum(ceil) + "): ask the user, then send it again with confirm") + "}");
                continue;
            }
            if (m.flag("confirm")) raiseCeiling(dev, want);
            stopRamp(); E.ramping = true;
            E.rampThread = std::thread([dev, cur, want] {
                double x = cur; const double step = 0.02;
                while (!E.rampStop.load()) {
                    if (std::fabs(want - x) <= step) x = want; else x += want > x ? step : -step;
                    std::string er; setVolume(dev, x, er);
                    if (x == want) break;
                    std::this_thread::sleep_for(std::chrono::milliseconds(5));
                }
                std::this_thread::sleep_for(std::chrono::milliseconds(20));   // the last step's own event passes while ramping is still set
                E.ramping = false;
                double v = -1; getVolume(dev, v); bool mu = false; getMute(dev, mu);
                say("{\\"ev\\":\\"volume\\",\\"value\\":" + jnum(v) + ",\\"mute\\":" + tf(mu) + ",\\"ramped\\":true}");
            });
            int steps = (int)std::ceil(std::fabs(want - cur) / 0.02);
            say(re + "\\"ok\\":true,\\"error\\":\\"\\",\\"value\\":" + jnum(cur) + ",\\"target\\":" + jnum(want) + ",\\"ramping\\":true,\\"rampMilliseconds\\":" + std::to_string(steps * 5) + ",\\"ceiling\\":" + jnum(ceilingOf(dev)) + "}");
        }""")
rep("""                double pr = m.num("pageRate", 0);""", """                double pr = m.num("pageRate", 0), pf = 30, hm = 120, lp = 2000; std::string be;
                // task NB-R4 (review C10): the ring's sizes come from these, so they are checked first (the ring holds 2 s)
                if (m.has("prefillMs") && !numArg(m, "prefillMs", 1, 1000, false, pf, be)) { ok = false; err = be; }
                if (ok && m.has("highMs") && !numArg(m, "highMs", 2, 1900, false, hm, be)) { ok = false; err = be; }
                if (ok && hm <= pf) { ok = false; err = "highMs must be above prefillMs"; }
                if (ok && m.has("limitPpm") && !numArg(m, "limitPpm", 0, 20000, false, lp, be)) { ok = false; err = be; }
                if (!ok) { say(re + "\\"ok\\":false,\\"error\\":" + jstr(err) + ",\\"type\\":\\"socket\\"}"); continue; }""")
rep("""                    E.ring.init((size_t)(dr * 2), (size_t)(dr * m.num("prefillMs", 30) / 1000), (size_t)(dr * m.num("highMs", 120) / 1000));""",
"""                    E.ring.init((size_t)(dr * 2), (size_t)(dr * pf / 1000), (size_t)(dr * hm / 1000));""")
rep("""                    E.ring.steer.limit = m.num("limitPpm", 2000) / 1e6;""", """                    E.ring.steer.limit = lp / 1e6;""")
rep("""        else if (c == "null") { std::string e = nullExternal(m.str("change"), m.num("value", 0), m.has("id") ? (uint32_t)m.num("id") : E.dev.load()); say(re + "\\"ok\\":" + tf(e.empty()) + ",\\"error\\":" + jstr(e) + "}"); }""",
"""        else if (c == "null") { double x = 0; std::string e; if (m.has("id") && !numArg(m, "id", 1, 4294967295.0, true, x, e)) { say(re + "\\"ok\\":false,\\"error\\":" + jstr(e) + "}"); continue; }
            e = nullExternal(m.str("change"), m.num("value", 0), m.has("id") ? (uint32_t)x : E.dev.load()); say(re + "\\"ok\\":" + tf(e.empty()) + ",\\"error\\":" + jstr(e) + "}"); }""")
rep("""    E.source = 0;
    stopSocket();
    closeDevice(true);
    E.watcher.stop();""", """    E.source = 0;
    stopRamp();
    stopSocket();
    E.watcher.stop();
    if (E.fmtThread.joinable()) E.fmtThread.join();
    closeDevice(true);""")
rep("""    say(std::string("{\\"re\\":\\"selftest\\",\\"ok\\":") + tf(bad == 0)""", """    { Msg m; check(parseMsg("{\\"uid\\":\\"caf\\\\u00e9 \\\\ud83d\\\\ude00\\\\n\\"}", m) && m.str("uid") == "caf\\xc3\\xa9 \\xf0\\x9f\\x98\\x80\\n", "message reader: \\\\u escapes to UTF-8 (task NB-R4)"); }
    say(std::string("{\\"re\\":\\"selftest\\",\\"ok\\":") + tf(bad == 0)""")
open(p, "w").write(s)
print("nb_r4_engine: ok")
