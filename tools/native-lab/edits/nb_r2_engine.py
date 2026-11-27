"""Task NB-R2: the rate contract, the source hand-shake (review C1, C2, C5) and the engine on the null device.
Anchored edits of native/engine/engine_main.cpp and native/engine/ring.h; every anchor must occur once."""
import sys
def edit(path, reps):
    s = open(path).read()
    for a, b in reps:
        n = s.count(a)
        assert n == 1, (path, n, a[:80])
        s = s.replace(a, b)
    open(path, 'w').write(s)

edit('native/engine/ring.h', [
("""    static constexpr size_t HISTORY = 128;""",
"""    // task NB-R2 (review C5): requests from other threads, carried out by the reader itself
    std::atomic<bool> steerResetReq{false};
    void requestSteerReset() { steerResetReq = true; }
    // reader only: forget everything not yet played (used while the page's rate does not match the device's)
    size_t drain() { uint64_t wp = w.load(), rp = r.load(); r.store(wp); primed = false; return (size_t)(wp - rp); }
    static constexpr size_t HISTORY = 128;"""),
("""        const SincTable& S = SincTable::get();
        const int H""",
"""        const SincTable& S = SincTable::get();
        if (steerResetReq.exchange(false)) steer.reset();
        const int H"""),
])

edit('native/engine/engine_main.cpp', [
("""#ifdef __APPLE__
#include "../common/coreaudio.h"
#include <sys/socket.h>
#include <sys/un.h>
#include <unistd.h>
#endif""",
"""#include "../common/coreaudio.h"   // on the Mac Core Audio; elsewhere the null device (common/nulldevice.cpp, task NB-R2)
#ifndef __APPLE__
#include "../common/nulldevice.h"
#endif
#include <sys/socket.h>
#include <sys/un.h>
#include <unistd.h>"""),
("""#ifdef __APPLE__
struct Eng {
    OutputStream stream; Watcher watcher;
    uint32_t dev = 0; bool isOpen = false, hog = false, fallback = true;
    std::atomic<int> source{0};     // 0 silence, 1 tone, 2 file, 3 socket
    double rate = 48000, tonePhase = 0;""",
"""// The engine itself. Runs on the Mac with Core Audio, and anywhere else with the null device (task NB-R2), so the
// same code is tested on every push.
struct Eng {
    OutputStream stream; Watcher watcher;
    std::atomic<uint32_t> dev{0}; bool isOpen = false, hog = false, fallback = true;   // dev is read by the listener thread (review C5)
    std::atomic<int> source{0};     // 0 silence, 1 tone, 2 file, 3 socket
    std::atomic<double> rate{48000};  // the device's rate; written by the listener thread, read by the device's thread (review C5)
    double tonePhase = 0;
    // task NB-R2, the rate contract (review A1): the page says at which rate it renders; sound plays only while that
    // equals the device's rate. Otherwise the device plays silence and what arrives is thrown away and counted.
    std::atomic<double> pageRate{0}; std::atomic<bool> rateOk{true}; std::atomic<uint64_t> mismatchFrames{0};
    // task NB-R2, the hand-shake that replaces the 30 ms sleep (review C1): the device's thread marks itself inside render
    std::atomic<int> inRender{0};"""),
("""static void render(void*, float** out, int, int frames) {
    int src = E.source.load();
    if (src == 1) {
        double inc = 440.0 / E.rate;""",
"""static void render(void*, float** out, int, int frames) {
    E.inRender.store(1);
    int src = E.source.load();
    if (src == 1) {
        double inc = 440.0 / E.rate.load();"""),
("""    } else if (src == 3) {
        E.ring.read(out[0], out[1], (size_t)frames);
    } else""",
"""    } else if (src == 3 && E.rateOk.load()) {
        E.ring.read(out[0], out[1], (size_t)frames);
    } else if (src == 3) {   // the page renders at another rate: silence, never sound at the wrong speed
        E.mismatchFrames += E.ring.drain();
        memset(out[0], 0, sizeof(float) * frames); memset(out[1], 0, sizeof(float) * frames);
    } else"""),
("""    E.peak.store(pk);
}
""",
"""    E.peak.store(pk);
    E.inRender.store(0);
}

// Takes the device's thread off every source and waits until it has left render (review C1). Sequentially
// consistent on both sides: either render saw source 0, or this sees inRender 1 and waits. No sleep guesses.
static void quiesce() {
    E.source = 0;
    for (int i = 0; E.inRender.load() && i < 200000; i++) std::this_thread::sleep_for(std::chrono::microseconds(50));
}
"""),
("""        ",\\"source\\":" + std::to_string(E.source.load()) + ",\\"peak\\":" + jnum(E.peak.load()) +""",
"""        ",\\"source\\":" + std::to_string(E.source.load()) + ",\\"peak\\":" + jnum(E.peak.load()) +
        ",\\"pageRate\\":" + jnum(E.pageRate.load()) + ",\\"rateOk\\":" + tf(E.source.load() != 3 || E.rateOk.load()) + ",\\"framesAtWrongRate\\":" + std::to_string(E.mismatchFrames.load()) +"""),
("""    E.rate = deviceInfo(want).rate;
    resetCounters();""",
"""    E.rate = deviceInfo(want).rate;
    if (E.source.load() == 3) E.rateOk = E.pageRate.load() == E.rate.load();   // another device or rate: the contract is checked again
    resetCounters();"""),
("""    else if (w == "rate") { DeviceInfo d = deviceInfo(E.dev); E.rate = d.rate; say("{\\"ev\\":\\"rate\\",\\"value\\":" + jnum(d.rate) + "}"); }""",
"""    else if (w == "rate") {
        // task NB-R2: the device changed rate (the user, Audio MIDI Setup, another program). While the page sends at the
        // old rate the device plays silence; the page is told to make its context again at the new rate and send
        // "source" again. If the device comes back to the page's rate, sound resumes by itself.
        DeviceInfo d = deviceInfo(E.dev); E.rate = d.rate;
        bool sock = E.source.load() == 3; double pr = E.pageRate.load(); bool ok = !sock || pr == d.rate; bool was = E.rateOk.exchange(ok);
        say("{\\"ev\\":\\"rate\\",\\"value\\":" + jnum(d.rate) + (sock ? ",\\"pageRate\\":" + jnum(pr) + ",\\"soundPaused\\":" + tf(!ok) + ",\\"resumed\\":" + tf(ok && !was) : std::string()) + "}");
    }"""),
("""static int run() {
    E.watcher.start(onWatch, nullptr);
    say("{\\"ev\\":\\"ready\\",\\"engine\\":\\"alengine 0.2\\",\\"pid\\":" + std::to_string((int)getpid()) + "}");""",
"""static int run() {
    SincTable::get();   // built here, not on the device's thread the first time follow mode reads (review C2)
    E.watcher.start(onWatch, nullptr);
#ifdef __APPLE__
    const char* backend = "coreaudio";
#else
    const char* backend = "null";
#endif
    say("{\\"ev\\":\\"ready\\",\\"engine\\":\\"alengine 0.3\\",\\"devices\\":\\"" + std::string(backend) + "\\",\\"rateContract\\":true,\\"pid\\":" + std::to_string((int)getpid()) + "}");"""),
("""        else if (c == "formats") { uint32_t d = m.has("uid") ? deviceByUid(m.str("uid")) : m.has("id") ? (uint32_t)m.num("id") : E.dev; say""",
"""        else if (c == "formats") { uint32_t d = m.has("uid") ? deviceByUid(m.str("uid")) : m.has("id") ? (uint32_t)m.num("id") : E.dev.load(); say"""),
("""            std::string t = m.str("type"), err; bool ok = true;
            if (t == "tone") E.source = 1;
            else if (t == "file") { Wav w; ok = wavRead(m.str("path"), w, err) && w.ch == 2; if (ok) { E.source = 0; std::this_thread::sleep_for(std::chrono::milliseconds(30)); E.file = w; E.filePos = 0; E.source = 2; } else if (err.empty()) err = "needs a stereo 32-bit float WAV"; }
            else if (t == "socket") {
                E.source = 0; std::this_thread::sleep_for(std::chrono::milliseconds(30));
                double r = E.rate > 0 ? E.rate : 48000;
                E.ring.init((size_t)(r * 2), (size_t)(r * m.num("prefillMs", 30) / 1000), (size_t)(r * m.num("highMs", 120) / 1000));
                E.ring.rate = r; E.ring.follow = m.str("clock") == "follow";   // task NB-N2b: "exact" (default) or "follow"
                E.ring.steer.limit = m.num("limitPpm", 2000) / 1e6;
                ok = startSocket(m.str("path"), err);
                if (ok) E.source = 3;
            } else { E.source = 0; }
            say(re + "\\"ok\\":" + tf(ok) + ",\\"error\\":" + jstr(err) + ",\\"type\\":" + jstr(t) + "}");""",
"""            // task NB-R2: every switch stops the socket's thread first and waits for the device's thread to leave
            // render (quiesce), so nothing touches the ring or the file while they are replaced (review C1)
            std::string t = m.str("type"), err, extra; bool ok = true;
            if (t == "tone") { stopSocket(); E.source = 1; }
            else if (t == "file") { Wav w; ok = wavRead(m.str("path"), w, err) && w.ch == 2; if (ok) { stopSocket(); quiesce(); E.file = w; E.filePos = 0; E.source = 2; } else if (err.empty()) err = "needs a stereo 32-bit float WAV"; }
            else if (t == "socket") {
                double dr = E.rate.load(); if (!(dr > 0)) dr = 48000;
                double pr = m.num("pageRate", 0);
                if (!(pr > 0)) { ok = false; err = "the page's sample rate is missing (pageRate); the device runs " + jnum(dr) + " Hz"; }
                else if (pr != dr) { ok = false; err = "the page renders at " + jnum(pr) + " Hz but the device runs " + jnum(dr) + " Hz: make the page's AudioContext at " + jnum(dr) + " Hz"; }
                extra = ",\\"pageRate\\":" + jnum(pr) + ",\\"deviceRate\\":" + jnum(dr);
                if (ok) {
                    stopSocket(); quiesce();
                    E.ring.init((size_t)(dr * 2), (size_t)(dr * m.num("prefillMs", 30) / 1000), (size_t)(dr * m.num("highMs", 120) / 1000));
                    E.ring.rate = dr; E.ring.follow = m.str("clock") == "follow";   // task NB-N2b: "exact" (default) or "follow"
                    E.ring.steer.limit = m.num("limitPpm", 2000) / 1e6;
                    E.pageRate = pr; E.rateOk = true; E.mismatchFrames = 0;
                    ok = startSocket(m.str("path"), err);
                    if (ok) E.source = 3;
                }
            } else { stopSocket(); quiesce(); }
            say(re + "\\"ok\\":" + tf(ok) + ",\\"error\\":" + jstr(err) + ",\\"type\\":" + jstr(t) + extra + "}");"""),
("""if (ok) { E.ring.steer.reset(); E.ring.follow = mo == "follow"; }""",
"""if (ok) { E.ring.requestSteerReset(); E.ring.follow = mo == "follow"; }"""),
("""        else if (c == "selftest") selftest();
        else if (c == "quit")""",
"""        else if (c == "selftest") selftest();
#ifndef __APPLE__
        // the null device only: change a pretend device as another program would ({"change":"rate","value":96000})
        else if (c == "null") { std::string e = nullExternal(m.str("change"), m.num("value", 0), m.has("id") ? (uint32_t)m.num("id") : E.dev.load()); say(re + "\\"ok\\":" + tf(e.empty()) + ",\\"error\\":" + jstr(e) + "}"); }
#endif
        else if (c == "quit")"""),
("""    E.watcher.stop();
    return 0;
}
#endif

int main(int argc, char** argv) {
    if (argc > 1 && std::string(argv[1]) == "selftest") return selftest();
#ifdef __APPLE__
    return run();
#else
    fprintf(stderr, "alengine needs macOS for sound; on this system only 'alengine selftest' runs.\\n");
    return 2;
#endif
}""",
"""    E.watcher.stop();
    return 0;
}

int main(int argc, char** argv) {
    if (argc > 1 && std::string(argv[1]) == "selftest") return selftest();
    return run();
}"""),
])
print('ok')
