// alengine: the AudioLab Engine, first part (task NB-N1). A native program that owns the audio output.
// It is driven by one JSON object per line on its standard input and answers the same way, so the desktop
// app (or a test) can run it as a helper:
//   {"cmd":"devices"}                                    every device with rates, buffer range, volume, formats
//   {"cmd":"open","uid":"...","rate":96000,"buffer":64,"exclusive":true,"bits":24,"integer":false}
//   {"cmd":"source","type":"tone"|"file"|"socket"|"silence","path":"...","prefillMs":30,"highMs":120}
//   {"cmd":"volume","value":0.5}   {"cmd":"mute","on":true}   {"cmd":"status"}   {"cmd":"close"}   {"cmd":"quit"}
// Things that change outside the program arrive as {"ev":"volume","value":0.4}, {"ev":"devices"}, ...
// Sound reaches it through a local socket as plain 32-bit float stereo at the device's rate and is handed to
// the device untouched (see ring.h).
#include "../common/json.h"
#include "../common/wav.h"
#include "minijson.h"
#include "ring.h"
#include "sample_convert.h"
#include <atomic>
#include <chrono>
#include <cmath>
#include <cstdio>
#include <iostream>
#include <mutex>
#include <string>
#include <thread>
#ifdef __APPLE__
#include "../common/coreaudio.h"
#include <sys/socket.h>
#include <sys/un.h>
#include <unistd.h>
#endif

using namespace al;

static std::mutex outLock;
static void say(const std::string& line0) {
    std::string line = line0;                       // one answer is one line: text inside strings is escaped, so any line break here is layout only
    for (auto& c : line) if (c == '\n' || c == '\r') c = ' ';
    std::lock_guard<std::mutex> g(outLock); fputs(line.c_str(), stdout); fputc('\n', stdout); fflush(stdout);
}
static const char* tf(bool b) { return b ? "true" : "false"; }

// ---- checks that need no sound card (also run on Linux) ------------------------------------------------
static int selftest() {
    int bad = 0; std::string notes;
    auto check = [&](bool ok, const char* what) { if (!ok) { bad++; notes += std::string(notes.empty() ? "" : "; ") + what; } };
    // 24-bit: every 24-bit value survives float and back
    { SampleFormat f; f.isFloat = false; f.bits = 24; f.bytes = 3; uint8_t out[3]; bool ok = true;
      for (int32_t v = -8388608; v <= 8388607; v += 4099) { float x = (float)v / 8388608.0f; writeChannel(&x, 1, out, 3, f, nullptr); int32_t got = (int32_t)((uint32_t)out[0] | ((uint32_t)out[1] << 8) | ((uint32_t)out[2] << 16)); if (got & 0x800000) got |= ~0xffffff; if (got != v) ok = false; }
      check(ok, "24-bit packed round trip"); }
    // 24 in a 32-bit container, valid bits at the top
    { SampleFormat f; f.isFloat = false; f.bits = 24; f.bytes = 4; f.alignedHigh = true; uint8_t out[4]; float x = 0.5f; writeChannel(&x, 1, out, 4, f, nullptr);
      uint32_t u; memcpy(&u, out, 4); check(u == 0x40000000u, "24 in 32, aligned high"); }
    { SampleFormat f; f.isFloat = false; f.bits = 32; f.bytes = 4; uint8_t out[4]; float x = -1.0f; writeChannel(&x, 1, out, 4, f, nullptr); uint32_t u; memcpy(&u, out, 4); check(u == 0x80000000u, "32-bit full scale negative");
      x = 1.0f; writeChannel(&x, 1, out, 4, f, nullptr); memcpy(&u, out, 4); check(u == 0x7fffffffu, "32-bit clamps at full scale positive"); }
    { SampleFormat f; f.isFloat = false; f.bits = 16; f.bytes = 2; uint8_t out[2]; float x = 0.25f; writeChannel(&x, 1, out, 2, f, nullptr); check(out[0] == 0x00 && out[1] == 0x20, "16-bit without dither");
      Dither d1, d2; uint8_t a[2], b[2]; float y = 0.1234567f; writeChannel(&y, 1, a, 2, f, &d1); writeChannel(&y, 1, b, 2, f, &d2); check(a[0] == b[0] && a[1] == b[1], "16-bit dither is the same twice"); }
    { SampleFormat f; uint8_t out[4]; float x = 0.3f, y; writeChannel(&x, 1, out, 4, f, nullptr); memcpy(&y, out, 4); check(y == x, "float passes untouched"); }
    // the ring: what goes in comes out, in order, untouched; too little gives silence and counts; too much is dropped once
    { Ring r; r.init(48000, 480, 4800); std::vector<float> in(2000 * 2), L(256), R(256); for (size_t i = 0; i < in.size(); i++) in[i] = (float)i;
      r.read(L.data(), R.data(), 256); check(L[0] == 0 && r.silentFrames.load() == 256, "ring is silent until filled");
      r.write(in.data(), 2000); bool ok = true; size_t got = 0;
      for (int k = 0; k < 7; k++) { r.read(L.data(), R.data(), 256); for (int i = 0; i < 256; i++, got++) if (L[i] != in[2 * got] || R[i] != in[2 * got + 1]) ok = false; }
      check(ok, "ring hands samples over in order");
      r.read(L.data(), R.data(), 256); check(r.underruns.load() == 1, "ring counts running empty");
      std::vector<float> big(6000 * 2, 1.f); r.write(big.data(), 6000); r.read(L.data(), R.data(), 256); check(r.skips.load() == 1 && r.fill() == 480 - 256, "ring drops back to its target when too full"); }
    { Msg m; check(parseMsg("{\"cmd\":\"open\",\"rate\":96000,\"exclusive\":true,\"uid\":\"a b\\\"c\"}", m) && m.str("cmd") == "open" && m.num("rate") == 96000 && m.flag("exclusive") && m.str("uid") == "a b\"c", "message reader"); }
    say(std::string("{\"re\":\"selftest\",\"ok\":") + tf(bad == 0) + ",\"failed\":" + std::to_string(bad) + ",\"notes\":" + jstr(notes) + "}");
    return bad ? 1 : 0;
}

#ifdef __APPLE__
struct Eng {
    OutputStream stream; Watcher watcher;
    uint32_t dev = 0; bool isOpen = false, hog = false, fallback = true;
    std::atomic<int> source{0};     // 0 silence, 1 tone, 2 file, 3 socket
    double rate = 48000, tonePhase = 0;
    Wav file; std::atomic<size_t> filePos{0};
    Ring ring;
    int listenFd = -1; std::thread sockThread; std::atomic<bool> sockRun{false}; std::atomic<uint64_t> sockFrames{0}; std::atomic<bool> sockClient{false};
    std::string sockPath;
    std::atomic<float> peak{0};
};
static Eng E;

static void render(void*, float** out, int, int frames) {
    int src = E.source.load();
    if (src == 1) {
        double inc = 440.0 / E.rate;
        for (int i = 0; i < frames; i++) { float v = (float)(std::sin(E.tonePhase * 6.283185307179586) * 0.1); out[0][i] = v; out[1][i] = v; E.tonePhase += inc; if (E.tonePhase >= 1) E.tonePhase -= 1; }
    } else if (src == 2 && E.file.frames()) {
        size_t n = E.file.frames(), p = E.filePos.load();
        for (int i = 0; i < frames; i++) { out[0][i] = E.file.data[2 * p]; out[1][i] = E.file.data[2 * p + 1]; if (++p >= n) p = 0; }
        E.filePos.store(p);
    } else if (src == 3) {
        E.ring.read(out[0], out[1], (size_t)frames);
    } else { memset(out[0], 0, sizeof(float) * frames); memset(out[1], 0, sizeof(float) * frames); }
    float pk = E.peak.load();
    for (int i = 0; i < frames; i++) { float a = std::fabs(out[0][i]), b = std::fabs(out[1][i]); if (a > pk) pk = a; if (b > pk) pk = b; }
    E.peak.store(pk);
}

static void stopSocket() {
    E.sockRun = false;
    if (E.listenFd >= 0) { shutdown(E.listenFd, SHUT_RDWR); close(E.listenFd); E.listenFd = -1; }
    if (E.sockThread.joinable()) E.sockThread.join();
    if (!E.sockPath.empty()) unlink(E.sockPath.c_str());
}
static bool startSocket(const std::string& path, std::string& err) {
    stopSocket();
    int fd = socket(AF_UNIX, SOCK_STREAM, 0);
    if (fd < 0) { err = "could not make a socket"; return false; }
    sockaddr_un a; memset(&a, 0, sizeof a); a.sun_family = AF_UNIX;
    if (path.size() >= sizeof a.sun_path) { err = "the socket path is too long"; close(fd); return false; }
    strncpy(a.sun_path, path.c_str(), sizeof a.sun_path - 1);
    unlink(path.c_str());
    if (bind(fd, (sockaddr*)&a, sizeof a) != 0 || listen(fd, 1) != 0) { err = "could not open the socket at " + path; close(fd); return false; }
    E.listenFd = fd; E.sockPath = path; E.sockRun = true; E.sockFrames = 0;
    E.sockThread = std::thread([fd]() {
        std::vector<uint8_t> buf(65536); size_t carry = 0;
        while (E.sockRun.load()) {
            int c = accept(fd, nullptr, nullptr);
            if (c < 0) break;
            E.sockClient = true; carry = 0;
            say("{\"ev\":\"sound-connected\"}");
            while (E.sockRun.load()) {
                ssize_t n = read(c, buf.data() + carry, buf.size() - carry);
                if (n <= 0) break;
                size_t have = carry + (size_t)n, frames = have / 8;
                size_t done = 0;
                while (done < frames && E.sockRun.load()) {          // if the ring is full, wait for the device to take some
                    size_t took = E.ring.write((const float*)(buf.data() + done * 8), frames - done);
                    done += took;
                    if (took == 0) usleep(1000);
                }
                E.sockFrames += frames;
                carry = have - frames * 8;
                if (carry) memmove(buf.data(), buf.data() + frames * 8, carry);
            }
            close(c); E.sockClient = false;
            say("{\"ev\":\"sound-disconnected\"}");
        }
    });
    return true;
}

static std::string formatsJson(uint32_t dev) {
    std::string s = "[";
    auto v = listPhysicalFormats(dev);
    for (size_t i = 0; i < v.size(); i++) s += std::string(i ? "," : "") + "{\"rate\":" + jnum(v[i].rate) + ",\"bits\":" + std::to_string(v[i].bits) + ",\"float\":" + tf(v[i].isFloat) + ",\"mixable\":" + tf(v[i].mixable) + ",\"channels\":" + std::to_string(v[i].channels) + "}";
    return s + "]";
}
static std::string statusJson() {
    DeviceInfo d = E.dev ? deviceInfo(E.dev) : DeviceInfo();
    uint64_t cb = E.stream.callbacks.load();
    double vol = -1; getVolume(E.dev, vol); bool mute = false; getMute(E.dev, mute);
    std::string s = std::string("\"open\":") + tf(E.isOpen) + ",\"device\":" + jstr(d.name) + ",\"uid\":" + jstr(d.uid) + ",\"rate\":" + jnum(d.rate) + ",\"buffer\":" + std::to_string(d.buffer) +
        ",\"exclusive\":" + tf(d.hogPid == (int)getpid()) + ",\"exclusiveOwner\":" + std::to_string(d.hogPid) + ",\"onTheWire\":" + jstr(d.physicalFormat) + ",\"handedToUs\":" + jstr(E.stream.formatText) +
        ",\"volume\":" + jnum(vol) + ",\"mute\":" + tf(mute) + ",\"latencyFrames\":" + std::to_string(d.latency + d.safetyOffset + d.streamLatency + d.buffer) +
        ",\"callbacks\":" + std::to_string(cb) + ",\"framesPerCallbackMin\":" + std::to_string(cb ? E.stream.minFrames.load() : 0) + ",\"framesPerCallbackMax\":" + std::to_string(E.stream.maxFrames.load()) +
        ",\"overloads\":" + std::to_string(E.stream.overloads.load()) + ",\"renderAvgMicroseconds\":" + jnum(cb ? E.stream.sumNs.load() / 1000.0 / cb : 0) + ",\"renderWorstMicroseconds\":" + jnum(E.stream.worstNs.load() / 1000.0) +
        ",\"source\":" + std::to_string(E.source.load()) + ",\"peak\":" + jnum(E.peak.load()) +
        ",\"ring\":{\"fill\":" + std::to_string(E.ring.frames ? E.ring.fill() : 0) + ",\"received\":" + std::to_string(E.sockFrames.load()) + ",\"ranEmpty\":" + std::to_string(E.ring.underruns.load()) +
        ",\"droppedTimes\":" + std::to_string(E.ring.skips.load()) + ",\"droppedFrames\":" + std::to_string(E.ring.skippedFrames.load()) + ",\"silentFrames\":" + std::to_string(E.ring.silentFrames.load()) + ",\"connected\":" + tf(E.sockClient.load()) + "}";
    return s;
}

static void closeDevice(bool releaseHog) {
    if (E.isOpen) { E.stream.stop(); E.isOpen = false; }
    if (releaseHog && E.hog && E.dev) { int o; std::string e; setHog(E.dev, false, o, e); E.hog = false; }
}
static void resetCounters() {
    E.stream.callbacks = 0; E.stream.framesTotal = 0; E.stream.overloads = 0; E.stream.minFrames = 0xffffffffu; E.stream.maxFrames = 0; E.stream.worstNs = 0; E.stream.sumNs = 0; E.peak = 0;
}
static std::string openDevice(const Msg& m) {
    auto t0 = std::chrono::steady_clock::now();
    uint32_t want = 0;
    if (m.has("uid")) want = deviceByUid(m.str("uid"));
    else if (m.has("id")) want = (uint32_t)m.num("id");
    else want = defaultOutputDevice();
    if (!want) return "\"ok\":false,\"error\":\"no such device\"";
    std::string notes, err;
    closeDevice(want != E.dev || !m.flag("exclusive"));
    E.dev = want; E.fallback = m.flag("fallback", true);
    DeviceInfo before = deviceInfo(want);
    if (before.outChannels < 1) return "\"ok\":false,\"error\":\"this device has no outputs\"";
    if (m.flag("exclusive") && !E.hog) { int owner = -1; std::string e; bool ok = setHog(want, true, owner, e); E.hog = ok; if (!ok) notes += "exclusive use not taken (" + (e.empty() ? "held by process " + std::to_string(owner) : e) + "); "; }
    double rate = m.num("rate", 0);
    if (rate > 0 && rate != before.rate) { double now = 0; std::string e; if (!setDeviceRate(want, rate, now, e)) notes += "rate not set, the device runs " + jnum(now) + " Hz" + (e.empty() ? "" : " (" + e + ")") + "; "; }
    if (m.has("bits")) {
        double r2 = deviceInfo(want).rate; std::string now, e;
        if (!setPhysicalFormat(want, r2, (int)m.num("bits"), !m.flag("integer"), now, e)) notes += "format not set, the device runs " + now + (e.empty() ? "" : " (" + e + ")") + "; ";
    }
    if (m.has("buffer")) { uint32_t now = 0; std::string e; if (!setDeviceBuffer(want, (uint32_t)m.num("buffer"), now, e)) notes += "buffer not set, the device runs " + std::to_string(now) + " frames; "; }
    E.rate = deviceInfo(want).rate;
    resetCounters();
    bool ok = E.stream.start(want, render, nullptr, err);
    E.isOpen = ok;
    E.watcher.watchDevice(want);
    double ms = std::chrono::duration<double, std::milli>(std::chrono::steady_clock::now() - t0).count();
    return std::string("\"ok\":") + tf(ok) + ",\"error\":" + jstr(err) + ",\"notes\":" + jstr(notes) + ",\"tookMilliseconds\":" + jnum(ms) + "," + statusJson();
}

static void onWatch(void*, const char* what, uint32_t dev) {
    std::string w = what;
    if (w == "volume" || w == "mute") { double v = -1; getVolume(E.dev, v); bool mu = false; getMute(E.dev, mu); say("{\"ev\":\"volume\",\"value\":" + jnum(v) + ",\"mute\":" + tf(mu) + "}"); }
    else if (w == "rate") { DeviceInfo d = deviceInfo(E.dev); E.rate = d.rate; say("{\"ev\":\"rate\",\"value\":" + jnum(d.rate) + "}"); }
    else if (w == "buffer") { say("{\"ev\":\"buffer\",\"value\":" + std::to_string(deviceInfo(E.dev).buffer) + "}"); }
    else if (w == "exclusive") { say("{\"ev\":\"exclusive\",\"owner\":" + std::to_string(deviceInfo(E.dev).hogPid) + "}"); }
    else if (w == "default-output") { say("{\"ev\":\"default-output\",\"id\":" + std::to_string(defaultOutputDevice()) + ",\"name\":" + jstr(deviceInfo(defaultOutputDevice()).name) + "}"); }
    else if (w == "devices" || w == "alive") {
        bool here = false; for (auto& d : listDevices()) if (d.id == E.dev) here = true;
        say(std::string("{\"ev\":\"devices\",\"ourDeviceStillThere\":") + tf(here || !E.dev) + "}");
    }
    (void)dev;
}

static int run() {
    E.watcher.start(onWatch, nullptr);
    say("{\"ev\":\"ready\",\"engine\":\"alengine 0.1\",\"pid\":" + std::to_string((int)getpid()) + "}");
    std::string line;
    while (std::getline(std::cin, line)) {
        if (line.empty()) continue;
        Msg m;
        if (!parseMsg(line, m)) { say("{\"re\":\"?\",\"ok\":false,\"error\":\"not a JSON object\"}"); continue; }
        std::string c = m.str("cmd"), re = "{\"re\":" + jstr(c) + ",";
        if (c == "devices") say(re + "\"defaultOutput\":" + std::to_string(defaultOutputDevice()) + ",\"devices\":" + devicesJson(listDevices()) + "}");
        else if (c == "formats") { uint32_t d = m.has("uid") ? deviceByUid(m.str("uid")) : m.has("id") ? (uint32_t)m.num("id") : E.dev; say(re + "\"formats\":" + formatsJson(d) + "}"); }
        else if (c == "open") say(re + openDevice(m) + "}");
        else if (c == "close") { closeDevice(true); say(re + "\"ok\":true}"); }
        else if (c == "volume") { std::string e; bool ok = setVolume(E.dev, m.num("value"), e); double v = -1; getVolume(E.dev, v); say(re + "\"ok\":" + tf(ok) + ",\"error\":" + jstr(e) + ",\"value\":" + jnum(v) + "}"); }
        else if (c == "mute") { bool ok = setMute(E.dev, m.flag("on")); bool mu = false; getMute(E.dev, mu); say(re + "\"ok\":" + tf(ok) + ",\"mute\":" + tf(mu) + "}"); }
        else if (c == "source") {
            std::string t = m.str("type"), err; bool ok = true;
            if (t == "tone") E.source = 1;
            else if (t == "file") { Wav w; ok = wavRead(m.str("path"), w, err) && w.ch == 2; if (ok) { E.source = 0; std::this_thread::sleep_for(std::chrono::milliseconds(30)); E.file = w; E.filePos = 0; E.source = 2; } else if (err.empty()) err = "needs a stereo 32-bit float WAV"; }
            else if (t == "socket") {
                E.source = 0; std::this_thread::sleep_for(std::chrono::milliseconds(30));
                double r = E.rate > 0 ? E.rate : 48000;
                E.ring.init((size_t)(r * 2), (size_t)(r * m.num("prefillMs", 30) / 1000), (size_t)(r * m.num("highMs", 120) / 1000));
                ok = startSocket(m.str("path"), err);
                if (ok) E.source = 3;
            } else { E.source = 0; }
            say(re + "\"ok\":" + tf(ok) + ",\"error\":" + jstr(err) + ",\"type\":" + jstr(t) + "}");
        }
        else if (c == "status") say(re + statusJson() + "}");
        else if (c == "reset") { resetCounters(); say(re + "\"ok\":true}"); }
        else if (c == "selftest") selftest();
        else if (c == "quit") { say(re + "\"ok\":true}"); break; }
        else say(re + "\"ok\":false,\"error\":\"unknown command\"}");
    }
    E.source = 0;
    stopSocket();
    closeDevice(true);
    E.watcher.stop();
    return 0;
}
#endif

int main(int argc, char** argv) {
    if (argc > 1 && std::string(argv[1]) == "selftest") return selftest();
#ifdef __APPLE__
    return run();
#else
    fprintf(stderr, "alengine needs macOS for sound; on this system only 'alengine selftest' runs.\n");
    return 2;
#endif
}
