// alengine: the AudioLab Engine, first part (task NB-N1). A native program that owns the audio output.
// It is driven by one JSON object per line on its standard input and answers the same way, so the desktop
// app (or a test) can run it as a helper:
//   {"cmd":"devices"}                                    every device with rates, buffer range, volume, formats
//   {"cmd":"open","uid":"...","rate":96000,"buffer":64,"exclusive":true,"bits":24,"integer":false}
//   {"cmd":"source","type":"tone"|"file"|"socket"|"silence","path":"...","prefillMs":30,"highMs":120,"clock":"exact"|"follow",
//    "pageRate":48000}   (task NB-R2: a socket source must say its rate; refused unless it equals the device's)
//   {"cmd":"clock","mode":"exact"|"follow"}   (task NB-N2b: follow the sender's clock smoothly, see follow.h)
//   {"cmd":"volume","value":0.5,"confirm":false}   {"cmd":"mute","on":true}   {"cmd":"status"}   {"cmd":"close"}   {"cmd":"quit"}
// Protocol 1 (task NB-R4): "ready" says "protocol":1; a command may carry "req":<number>, its answer carries the same.
// The device volume moves in a ramp, and above the loudest level the device has had it needs "confirm":true.
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
#include <map>
#include <mutex>
#include <string>
#include <thread>
#include "../common/coreaudio.h"   // on the Mac Core Audio; elsewhere the null device (common/nulldevice.cpp, task NB-R2)
#ifndef __APPLE__
#include "../common/nulldevice.h"
#endif
#include <sys/socket.h>
#include <sys/un.h>
#include <unistd.h>

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
    int bad = 0; std::string notes, notesInfo;
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
    // task NB-N2b: the follower. (1) held at speed 1 it hands every sample over untouched; (2) between the samples it is clean;
    // (3) against a sender whose clock is off by up to 1000 parts per million it never runs empty or drops, for 5 simulated minutes.
    { Ring r; r.init(48000, 480, 24000); r.follow = true; r.rate = 48000; r.steer.fixed = true; r.steer.fixedU = 0;
      std::vector<float> in(4000 * 2), L(256), R(256); for (size_t i = 0; i < in.size(); i++) in[i] = (float)std::sin(0.001 * (double)i * (double)i) * 0.7f;
      r.write(in.data(), 4000); bool ok = true; size_t got = 0;
      for (int k = 0; k < 10; k++) { r.read(L.data(), R.data(), 256); for (int i = 0; i < 256; i++, got++) if (L[i] != in[2 * got] || R[i] != in[2 * got + 1]) ok = false; }
      check(ok && r.underruns.load() == 0, "follower at speed 1 is bit for bit"); }
    for (double f : {997.0, 15000.0}) {
      Ring r; r.init(96000, 480, 90000); r.follow = true; r.rate = 48000; r.steer.fixed = true; r.steer.fixedU = 100e-6;
      size_t N = 60000; std::vector<float> in(N * 2); for (size_t i = 0; i < N; i++) in[2 * i] = in[2 * i + 1] = (float)(0.5 * std::sin(2 * M_PI * f * (double)i / 48000));
      r.write(in.data(), N); std::vector<float> L(48000), R(48000); r.read(L.data(), R.data(), 48000);
      double worst = 0; for (size_t i = 100; i < 48000; i++) { double want = 0.5 * std::sin(2 * M_PI * f * (double)i * (1 + 100e-6) / 48000); double e = std::fabs(L[i] - want); if (e > worst) worst = e; }
      double db = 20 * std::log10(worst / 0.5 + 1e-30);
      notesInfo += std::string(notesInfo.empty() ? "" : ", ") + "follower error at " + jnum(f) + " Hz " + jnum(std::round(db * 10) / 10) + " dB";
      check(db < (f < 5000 ? -110 : -80), f < 5000 ? "follower is clean at 997 Hz (error below -110 dB)" : "follower is clean at 15 kHz (error below -80 dB)");
    }
    for (double d : {250e-6, -250e-6, 1000e-6, -1000e-6}) {
      const double SR = 48000; Ring r; r.init((size_t)SR * 2, (size_t)(SR * 0.05), (size_t)(SR * 0.5)); r.follow = true; r.rate = SR;
      std::vector<float> blk(128 * 2), L(256), R(256); double tp = 0, tc = 0, ph = 0; size_t fmin = (size_t)-1, fmax = 0; double sumPpm = 0; int nPpm = 0;
      const double total = 300;
      while (tc < total) {
        if (tp <= tc) { for (int i = 0; i < 128; i++) { float v = (float)(0.3 * std::sin(ph)); ph += 2 * M_PI * 440 / SR; blk[2 * i] = blk[2 * i + 1] = v; } r.write(blk.data(), 128); tp += 128 / (SR * (1 + d)); }
        else { r.read(L.data(), R.data(), 256); tc += 256 / SR; if (tc > 120) { size_t fl = r.fill(); if (fl < fmin) fmin = fl; if (fl > fmax) fmax = fl; } if (tc > total - 60) { sumPpm += r.ppmMilli.load() / 1000.0; nPpm++; } }
      }
      double endPpm = nPpm ? sumPpm / nPpm : 0;
      bool ok = r.underruns.load() == 0 && r.skips.load() == 0 && std::fabs(endPpm - d * 1e6) < 10 + 0.025 * std::fabs(d * 1e6) && fmin + 960 > r.target && fmax < r.target + 960;
      notesInfo += ", sender off by " + jnum(d * 1e6) + " ppm: steered to " + jnum(std::round(endPpm * 10) / 10) + " ppm (mean of the last minute), fill " + std::to_string(fmin) + " to " + std::to_string(fmax) + " frames after two minutes (target " + std::to_string(r.target) + "), ran empty " + std::to_string(r.underruns.load()) + ", dropped " + std::to_string(r.skips.load());
      check(ok, "follower keeps up with a sender whose clock is off");
    }
    { Msg m; check(parseMsg("{\"cmd\":\"open\",\"rate\":96000,\"exclusive\":true,\"uid\":\"a b\\\"c\"}", m) && m.str("cmd") == "open" && m.num("rate") == 96000 && m.flag("exclusive") && m.str("uid") == "a b\"c", "message reader"); }
    { Msg m; check(parseMsg("{\"uid\":\"caf\\u00e9 \\ud83d\\ude00\\n\"}", m) && m.str("uid") == "caf\xc3\xa9 \xf0\x9f\x98\x80\n", "message reader: \\u escapes to UTF-8 (task NB-R4)"); }
    say(std::string("{\"re\":\"selftest\",\"ok\":") + tf(bad == 0) + ",\"failed\":" + std::to_string(bad) + ",\"notes\":" + jstr(notes) + ",\"measured\":" + jstr(notesInfo) + "}");
    return bad ? 1 : 0;
}

// The engine itself. Runs on the Mac with Core Audio, and anywhere else with the null device (task NB-R2), so the
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
    std::atomic<int> inRender{0};
    Wav file; std::atomic<size_t> filePos{0};
    Ring ring;
    int listenFd = -1; std::thread sockThread; std::atomic<bool> sockRun{false}; std::atomic<uint64_t> sockFrames{0}; std::atomic<bool> sockClient{false};
    std::mutex clientLock; int clientFd = -1;   // task NB-R3: the connected sender, so stopSocket can end a read that would never return
    std::string sockPath;
    std::atomic<float> peak{0};
    // task NB-R4: output protection (C6), the stream restarted on a format change (C7), the device volume's ramp and ceiling
    std::atomic<uint64_t> nonFinite{0}, clipped{0}, formatRestarts{0};
    std::mutex devLock;                      // open, close and the format restart
    std::thread fmtThread;
    std::thread rampThread; std::atomic<bool> ramping{false}, rampStop{false};
    std::map<uint32_t, double> ceiling;      // per device: the loudest level it has had (command thread only)
    std::mutex ceilLock;
};
static Eng E;

static void render(void*, float** out, int, int frames) {
    E.inRender.store(1);
    int src = E.source.load();
    if (src == 1) {
        double inc = 440.0 / E.rate.load();
        for (int i = 0; i < frames; i++) { float v = (float)(std::sin(E.tonePhase * 6.283185307179586) * 0.1); out[0][i] = v; out[1][i] = v; E.tonePhase += inc; if (E.tonePhase >= 1) E.tonePhase -= 1; }
    } else if (src == 2 && E.file.frames()) {
        size_t n = E.file.frames(), p = E.filePos.load();
        for (int i = 0; i < frames; i++) { out[0][i] = E.file.data[2 * p]; out[1][i] = E.file.data[2 * p + 1]; if (++p >= n) p = 0; }
        E.filePos.store(p);
    } else if (src == 3 && E.rateOk.load()) {
        E.ring.read(out[0], out[1], (size_t)frames);
    } else if (src == 3) {   // the page renders at another rate: silence, never sound at the wrong speed
        E.mismatchFrames += E.ring.drain();
        memset(out[0], 0, sizeof(float) * frames); memset(out[1], 0, sizeof(float) * frames);
    } else { memset(out[0], 0, sizeof(float) * frames); memset(out[1], 0, sizeof(float) * frames); }
    // task NB-R4 (review C6): NaN and infinity become silence, anything past full scale is held at full scale. Every legal
    // sample (-1 to 1, and -0) passes untouched, so this costs nothing in bit-perfect terms.
    uint32_t nf = 0, cl = 0;
    for (int c = 0; c < 2; c++) { float* o = out[c]; for (int i = 0; i < frames; i++) { float x = o[i]; if (!std::isfinite(x)) { o[i] = 0.f; nf++; } else if (x > 1.f) { o[i] = 1.f; cl++; } else if (x < -1.f) { o[i] = -1.f; cl++; } } }
    if (nf) E.nonFinite += nf;
    if (cl) E.clipped += cl;
    float pk = E.peak.load();
    for (int i = 0; i < frames; i++) { float a = std::fabs(out[0][i]), b = std::fabs(out[1][i]); if (a > pk) pk = a; if (b > pk) pk = b; }
    E.peak.store(pk);
    E.inRender.store(0);
}

// Takes the device's thread off every source and waits until it has left render (review C1). Sequentially
// consistent on both sides: either render saw source 0, or this sees inRender 1 and waits. No sleep guesses.
static void quiesce() {
    E.source = 0;
    for (int i = 0; E.inRender.load() && i < 200000; i++) std::this_thread::sleep_for(std::chrono::microseconds(50));
}

static void stopSocket() {
    E.sockRun = false;
    if (E.listenFd >= 0) { shutdown(E.listenFd, SHUT_RDWR); close(E.listenFd); E.listenFd = -1; }
    // a sender that stopped sending (frozen, hung) would keep the socket thread in read() and this join waiting
    { std::lock_guard<std::mutex> g(E.clientLock); if (E.clientFd >= 0) shutdown(E.clientFd, SHUT_RDWR); }
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
            { std::lock_guard<std::mutex> g(E.clientLock); if (!E.sockRun.load()) { close(c); break; } E.clientFd = c; }
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
            { std::lock_guard<std::mutex> g(E.clientLock); E.clientFd = -1; close(c); }
            E.sockClient = false;
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
static double ceilingOf(uint32_t dev) { std::lock_guard<std::mutex> g(E.ceilLock); auto it = E.ceiling.find(dev); return it == E.ceiling.end() ? -1 : it->second; }
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
static std::string statusJson() {
    DeviceInfo d = E.dev ? deviceInfo(E.dev) : DeviceInfo();
    uint64_t cb = E.stream.callbacks.load();
    double vol = -1; getVolume(E.dev, vol); bool mute = false; getMute(E.dev, mute);
    std::string s = std::string("\"open\":") + tf(E.isOpen) + ",\"device\":" + jstr(d.name) + ",\"uid\":" + jstr(d.uid) + ",\"rate\":" + jnum(d.rate) + ",\"buffer\":" + std::to_string(d.buffer) +
        ",\"exclusive\":" + tf(d.hogPid == (int)getpid()) + ",\"exclusiveOwner\":" + std::to_string(d.hogPid) + ",\"onTheWire\":" + jstr(d.physicalFormat) + ",\"handedToUs\":" + jstr(E.stream.formatText) +
        ",\"volume\":" + jnum(vol) + ",\"mute\":" + tf(mute) + ",\"latencyFrames\":" + std::to_string(d.latency + d.safetyOffset + d.streamLatency + d.buffer) +
        // task NB-R4 (review C8): the figure above is the device's part only; sound from the page also waits in the ring
        ",\"deviceLatencyFrames\":" + std::to_string(d.latency + d.safetyOffset + d.streamLatency + d.buffer) +
        ",\"ringLatencyFrames\":" + std::to_string(E.source.load() == 3 && E.ring.frames ? E.ring.fill() : 0) +
        ",\"latencyNote\":" + jstr("device part (buffer, device, safety and stream latency) plus, for sound from the page, the ring; the page's own output buffering is not included") +
        ",\"protect\":{\"nonFinite\":" + std::to_string(E.nonFinite.load()) + ",\"clipped\":" + std::to_string(E.clipped.load()) + "}" +
        ",\"dither\":" + tf(E.stream.dither16) + ",\"formatRestarts\":" + std::to_string(E.formatRestarts.load()) + ",\"volumeCeiling\":" + jnum(ceilingOf(E.dev)) + ",\"ramping\":" + tf(E.ramping.load()) +
        ",\"callbacks\":" + std::to_string(cb) + ",\"framesPerCallbackMin\":" + std::to_string(cb ? E.stream.minFrames.load() : 0) + ",\"framesPerCallbackMax\":" + std::to_string(E.stream.maxFrames.load()) +
        ",\"overloads\":" + std::to_string(E.stream.overloads.load()) + ",\"renderAvgMicroseconds\":" + jnum(cb ? E.stream.sumNs.load() / 1000.0 / cb : 0) + ",\"renderWorstMicroseconds\":" + jnum(E.stream.worstNs.load() / 1000.0) +
        ",\"source\":" + std::to_string(E.source.load()) + ",\"peak\":" + jnum(E.peak.load()) +
        ",\"pageRate\":" + jnum(E.pageRate.load()) + ",\"rateOk\":" + tf(E.source.load() != 3 || E.rateOk.load()) + ",\"framesAtWrongRate\":" + std::to_string(E.mismatchFrames.load()) +
        ",\"ring\":{\"fill\":" + std::to_string(E.ring.frames ? E.ring.fill() : 0) + ",\"received\":" + std::to_string(E.sockFrames.load()) + ",\"ranEmpty\":" + std::to_string(E.ring.underruns.load()) +
        ",\"droppedTimes\":" + std::to_string(E.ring.skips.load()) + ",\"droppedFrames\":" + std::to_string(E.ring.skippedFrames.load()) + ",\"silentFrames\":" + std::to_string(E.ring.silentFrames.load()) + ",\"connected\":" + tf(E.sockClient.load()) +
        ",\"clock\":" + jstr(E.ring.follow.load() ? "follow" : "exact") + ",\"ppm\":" + jnum(E.ring.ppmMilli.load() / 1000.0) + ",\"ppmMin\":" + jnum(E.ring.ppmMinMilli.load() / 1000.0) + ",\"ppmMax\":" + jnum(E.ring.ppmMaxMilli.load() / 1000.0) + "}";
    return s;
}

static void closeDeviceLocked(bool releaseHog);
static void closeDevice(bool releaseHog) { std::lock_guard<std::mutex> g(E.devLock); closeDeviceLocked(releaseHog); }
static void closeDeviceLocked(bool releaseHog) {
    if (E.isOpen) { E.stream.stop(); E.isOpen = false; }
    if (releaseHog && E.hog && E.dev) { int o; std::string e; setHog(E.dev, false, o, e); E.hog = false; }
}
static void resetCounters() {
    E.stream.callbacks = 0; E.stream.framesTotal = 0; E.stream.overloads = 0; E.stream.minFrames = 0xffffffffu; E.stream.maxFrames = 0; E.stream.worstNs = 0; E.stream.sumNs = 0; E.peak = 0;
}
static std::string openDevice(const Msg& m) {
    auto t0 = std::chrono::steady_clock::now();
    uint32_t want = 0; std::string bad; double x = 0;
    if (m.has("id") && !m.has("uid") && !numArg(m, "id", 1, 4294967295.0, true, x, bad)) return "\"ok\":false,\"error\":" + jstr(bad);
    if (m.has("buffer") && !numArg(m, "buffer", 1, 65536, true, x, bad)) return "\"ok\":false,\"error\":" + jstr(bad);
    if (m.has("bits") && !numArg(m, "bits", 8, 32, true, x, bad)) return "\"ok\":false,\"error\":" + jstr(bad);
    if (m.has("rate") && !numArg(m, "rate", 0, 10000000, false, x, bad)) return "\"ok\":false,\"error\":" + jstr(bad);
    std::lock_guard<std::mutex> dl(E.devLock);
    if (m.has("uid")) want = deviceByUid(m.str("uid"));
    else if (m.has("id")) want = (uint32_t)m.num("id");
    else want = defaultOutputDevice();
    if (!want) return "\"ok\":false,\"error\":\"no such device\"";
    std::string notes, err;
    if (want != E.dev) stopRamp();
    closeDeviceLocked(want != E.dev || !m.flag("exclusive"));
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
    if (E.source.load() == 3) E.rateOk = E.pageRate.load() == E.rate.load();   // another device or rate: the contract is checked again
    resetCounters();
    { double v0 = -1; if (getVolume(want, v0)) { std::lock_guard<std::mutex> g(E.ceilLock); if (!E.ceiling.count(want)) E.ceiling[want] = v0; } }
    E.stream.dither16 = m.flag("dither", false);   // task NB-R4 (review C7): off unless asked for
    E.nonFinite = 0; E.clipped = 0;
    bool ok = E.stream.start(want, render, nullptr, err);
    E.isOpen = ok;
    E.watcher.watchDevice(want);
    double ms = std::chrono::duration<double, std::milli>(std::chrono::steady_clock::now() - t0).count();
    return std::string("\"ok\":") + tf(ok) + ",\"error\":" + jstr(err) + ",\"notes\":" + jstr(notes) + ",\"tookMilliseconds\":" + jnum(ms) + "," + statusJson();
}

static void onWatch(void*, const char* what, uint32_t dev) {
    std::string w = what;
    if (w == "volume" || w == "mute") {
        if (E.ramping.load()) return;   // task NB-R4: the ramp's own steps; one event comes when it ends
        double v = -1; getVolume(E.dev, v); bool mu = false; getMute(E.dev, mu);
        raiseCeiling(E.dev, v);         // a level set outside the engine (the user in Audio MIDI Setup, the DAC's knob reported back)
        say("{\"ev\":\"volume\",\"value\":" + jnum(v) + ",\"mute\":" + tf(mu) + "}");
    }
    else if (w == "format") {
        // task NB-R4 (review C7): another program, Audio MIDI Setup or a re-plug changed the format: start the stream
        // again so it writes the new layout (never the old bytes into a new format). Not on the listener's thread.
        if (E.fmtThread.joinable()) E.fmtThread.join();
        E.fmtThread = std::thread([] {
            std::lock_guard<std::mutex> g(E.devLock);
            if (!E.isOpen) return;
            std::string now = virtualFormatText(E.dev);
            if (now == E.stream.formatText) { say("{\"ev\":\"format\",\"handedToUs\":" + jstr(now) + ",\"restarted\":false}"); return; }
            bool d16 = E.stream.dither16; E.stream.stop(); E.stream.dither16 = d16;
            std::string err; bool ok = E.stream.start(E.dev, render, nullptr, err); E.isOpen = ok; E.formatRestarts++;
            say("{\"ev\":\"format\",\"handedToUs\":" + jstr(E.stream.formatText) + ",\"restarted\":" + tf(ok) + ",\"error\":" + jstr(err) + "}");
        });
    }
    else if (w == "rate") {
        // task NB-R2: the device changed rate (the user, Audio MIDI Setup, another program). While the page sends at the
        // old rate the device plays silence; the page is told to make its context again at the new rate and send
        // "source" again. If the device comes back to the page's rate, sound resumes by itself.
        DeviceInfo d = deviceInfo(E.dev); E.rate = d.rate;
        bool sock = E.source.load() == 3; double pr = E.pageRate.load(); bool ok = !sock || pr == d.rate; bool was = E.rateOk.exchange(ok);
        say("{\"ev\":\"rate\",\"value\":" + jnum(d.rate) + (sock ? ",\"pageRate\":" + jnum(pr) + ",\"soundPaused\":" + tf(!ok) + ",\"resumed\":" + tf(ok && !was) : std::string()) + "}");
    }
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
    SincTable::get();   // built here, not on the device's thread the first time follow mode reads (review C2)
    E.watcher.start(onWatch, nullptr);
#ifdef __APPLE__
    const char* backend = "coreaudio";
#else
    const char* backend = "null";
#endif
    say("{\"ev\":\"ready\",\"engine\":\"alengine 0.5\",\"devices\":\"" + std::string(backend) + "\",\"rateContract\":true,\"protocol\":1,\"pid\":" + std::to_string((int)getpid()) + "}");
    std::string line;
    while (std::getline(std::cin, line)) {
        if (line.empty()) continue;
        Msg m;
        // task NB-R4 (review A10): "req" comes back in the answer, so a caller matches answers by number, not by name
        if (!parseMsg(line, m)) {
            std::string rq; size_t k = line.find("\"req\":");
            if (k != std::string::npos) { char* e = nullptr; double v = strtod(line.c_str() + k + 6, &e); if (e != line.c_str() + k + 6 && std::isfinite(v)) rq = ",\"req\":" + jnum(v); }
            say("{\"re\":\"?\"" + rq + ",\"ok\":false,\"error\":\"not a JSON object\"}"); continue;
        }
        std::string c = m.str("cmd"), rq;
        { double v = 0; std::string e; if (m.has("req") && numArg(m, "req", -9007199254740991.0, 9007199254740991.0, false, v, e)) rq = ",\"req\":" + jnum(v); }
        std::string re = "{\"re\":" + jstr(c) + rq + ",";
        if (c == "devices") say(re + "\"defaultOutput\":" + std::to_string(defaultOutputDevice()) + ",\"devices\":" + devicesJson(listDevices()) + "}");
        else if (c == "formats") { double x = 0; std::string e; if (m.has("id") && !m.has("uid") && !numArg(m, "id", 1, 4294967295.0, true, x, e)) { say(re + "\"ok\":false,\"error\":" + jstr(e) + "}"); continue; }
            uint32_t d = m.has("uid") ? deviceByUid(m.str("uid")) : m.has("id") ? (uint32_t)x : E.dev.load(); say(re + "\"formats\":" + formatsJson(d) + "}"); }
        else if (c == "open") say(re + openDevice(m) + "}");
        else if (c == "close") { closeDevice(true); say(re + "\"ok\":true}"); }
        else if (c == "volume") {
            // task NB-R4 (review C6): a ramp, never a jump; louder than the device has been only with "confirm":true
            double want = 0, cur = -1; std::string e; uint32_t dev = E.dev.load();
            if (!numArg(m, "value", 0, 1, false, want, e)) { getVolume(dev, cur); say(re + "\"ok\":false,\"error\":" + jstr(e) + ",\"value\":" + jnum(cur) + "}"); continue; }
            if (!getVolume(dev, cur)) { bool ok = setVolume(dev, want, e); say(re + "\"ok\":" + tf(ok) + ",\"error\":" + jstr(e) + ",\"value\":-1}"); continue; }
            double ceil = ceilingOf(dev); if (ceil < 0) { raiseCeiling(dev, cur); ceil = ceilingOf(dev); }
            if (want > ceil + 1e-6 && !m.flag("confirm")) {
                say(re + "\"ok\":false,\"needsConfirm\":true,\"ceiling\":" + jnum(ceil) + ",\"value\":" + jnum(cur) + ",\"error\":" + jstr("louder than this device has been (" + jnum(ceil) + "): ask the user, then send it again with confirm") + "}");
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
                say("{\"ev\":\"volume\",\"value\":" + jnum(v) + ",\"mute\":" + tf(mu) + ",\"ramped\":true}");
            });
            int steps = (int)std::ceil(std::fabs(want - cur) / 0.02);
            say(re + "\"ok\":true,\"error\":\"\",\"value\":" + jnum(cur) + ",\"target\":" + jnum(want) + ",\"ramping\":true,\"rampMilliseconds\":" + std::to_string(steps * 5) + ",\"ceiling\":" + jnum(ceilingOf(dev)) + "}");
        }
        else if (c == "mute") { bool ok = setMute(E.dev, m.flag("on")); bool mu = false; getMute(E.dev, mu); say(re + "\"ok\":" + tf(ok) + ",\"mute\":" + tf(mu) + "}"); }
        else if (c == "source") {
            // task NB-R2: every switch stops the socket's thread first and waits for the device's thread to leave
            // render (quiesce), so nothing touches the ring or the file while they are replaced (review C1)
            std::string t = m.str("type"), err, extra; bool ok = true;
            if (t == "tone") { stopSocket(); E.source = 1; }
            else if (t == "file") { Wav w; ok = wavRead(m.str("path"), w, err) && w.ch == 2; if (ok) { stopSocket(); quiesce(); E.file = w; E.filePos = 0; E.source = 2; } else if (err.empty()) err = "needs a stereo 32-bit float WAV"; }
            else if (t == "socket") {
                double dr = E.rate.load(); if (!(dr > 0)) dr = 48000;
                double pr = m.num("pageRate", 0), pf = 30, hm = 120, lp = 2000; std::string be;
                // task NB-R4 (review C10): the ring's sizes come from these, so they are checked first (the ring holds 2 s)
                if (m.has("prefillMs") && !numArg(m, "prefillMs", 1, 1000, false, pf, be)) { ok = false; err = be; }
                if (ok && m.has("highMs") && !numArg(m, "highMs", 2, 1900, false, hm, be)) { ok = false; err = be; }
                if (ok && hm <= pf) { ok = false; err = "highMs must be above prefillMs"; }
                if (ok && m.has("limitPpm") && !numArg(m, "limitPpm", 0, 20000, false, lp, be)) { ok = false; err = be; }
                if (!ok) { say(re + "\"ok\":false,\"error\":" + jstr(err) + ",\"type\":\"socket\"}"); continue; }
                if (!(pr > 0)) { ok = false; err = "the page's sample rate is missing (pageRate); the device runs " + jnum(dr) + " Hz"; }
                else if (pr != dr) { ok = false; err = "the page renders at " + jnum(pr) + " Hz but the device runs " + jnum(dr) + " Hz: make the page's AudioContext at " + jnum(dr) + " Hz"; }
                extra = ",\"pageRate\":" + jnum(pr) + ",\"deviceRate\":" + jnum(dr);
                if (ok) {
                    stopSocket(); quiesce();
                    E.ring.init((size_t)(dr * 2), (size_t)(dr * pf / 1000), (size_t)(dr * hm / 1000));
                    E.ring.rate = dr; E.ring.follow = m.str("clock") == "follow";   // task NB-N2b: "exact" (default) or "follow"
                    E.ring.steer.limit = lp / 1e6;
                    E.pageRate = pr; E.rateOk = true; E.mismatchFrames = 0;
                    ok = startSocket(m.str("path"), err);
                    if (ok) E.source = 3;
                }
            } else { stopSocket(); quiesce(); }
            say(re + "\"ok\":" + tf(ok) + ",\"error\":" + jstr(err) + ",\"type\":" + jstr(t) + extra + "}");
        }
        else if (c == "clock") { std::string mo = m.str("mode"); bool ok = mo == "follow" || mo == "exact"; if (ok) { E.ring.requestSteerReset(); E.ring.follow = mo == "follow"; } say(re + "\"ok\":" + tf(ok) + ",\"mode\":" + jstr(E.ring.follow.load() ? "follow" : "exact") + "}"); }
        else if (c == "status") say(re + statusJson() + "}");
        else if (c == "reset") { resetCounters(); say(re + "\"ok\":true}"); }
        else if (c == "selftest") selftest();
#ifndef __APPLE__
        // the null device only: change a pretend device as another program would ({"change":"rate","value":96000})
        else if (c == "null") { double x = 0; std::string e; if (m.has("id") && !numArg(m, "id", 1, 4294967295.0, true, x, e)) { say(re + "\"ok\":false,\"error\":" + jstr(e) + "}"); continue; }
            e = nullExternal(m.str("change"), m.num("value", 0), m.has("id") ? (uint32_t)x : E.dev.load()); say(re + "\"ok\":" + tf(e.empty()) + ",\"error\":" + jstr(e) + "}"); }
#endif
        else if (c == "quit") { say(re + "\"ok\":true}"); break; }
        else say(re + "\"ok\":false,\"error\":\"unknown command\"}");
    }
    E.source = 0;
    stopRamp();
    stopSocket();
    E.watcher.stop();
    if (E.fmtThread.joinable()) E.fmtThread.join();
    closeDevice(true);
    return 0;
}

int main(int argc, char** argv) {
    if (argc > 1 && std::string(argv[1]) == "selftest") return selftest();
    return run();
}
