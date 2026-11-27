// The null device (task NB-R2): the same device layer as coreaudio.cpp, for machines without Core Audio (Linux
// CI, a build machine with no sound card). Two pretend outputs that behave like the user's two DACs in the ways
// the engine has to respect:
//   1 "AudioLab null output"   like the iFi Gryphon: 16 kHz to 384 kHz, volume the computer can set, exclusive use
//   2 "AudioLab null output 2" like the Zoom AMS-24: 44.1 to 96 kHz, no volume the computer can set
// A stream runs on its own thread in real time (paced by the clock, at the device's buffer size) and calls the
// engine's render function exactly like the IOProc does. With AL_NULL_RECORD=/path.wav set, what the first stream
// plays is written to that file when it stops (32-bit float, stereo, at the rate it ended with), later streams to
// /path.wav.2.wav and so on.
// nullExternal() changes a device as another program would (rate, volume, unplug): the watcher then tells the
// engine on its own thread, like a HAL listener. The engine's "null" command reaches it (Linux builds only).
#ifndef __APPLE__
#include "coreaudio.h"
#include "json.h"
#include "nulldevice.h"
#include "wav.h"
#include "../engine/sample_convert.h"
#include <chrono>
#include <condition_variable>
#include <cstdlib>
#include <cstring>
#include <deque>
#include <memory>
#include <mutex>
#include <thread>
#include <unistd.h>

namespace al {

namespace {
struct NullDev {
    uint32_t id; std::string name, uid; std::vector<double> rates; bool volume;
    double rate = 48000; uint32_t buffer = 256; double vol = 0.5; bool mute = false; int hogPid = -1; bool present = true;
    int bits = 32; bool isFloat = true, mixable = true;
};
std::mutex gLock;
std::vector<NullDev>& devs() {
    static std::vector<NullDev> d = {
        { 1, "AudioLab null output", "al-null-1", { 16000, 44100, 48000, 88200, 96000, 176400, 192000, 352800, 384000 }, true },
        { 2, "AudioLab null output 2", "al-null-2", { 44100, 48000, 88200, 96000 }, false },
    };
    return d;
}
NullDev* find(uint32_t id) { for (auto& d : devs()) if (d.id == id && d.present) return &d; return nullptr; }

// the watcher's thread: events are queued and delivered one by one, never on the caller's thread
struct Events {
    std::mutex m; std::condition_variable cv; std::deque<std::pair<std::string, uint32_t>> q; bool run = false; std::thread t;
    Watcher* w = nullptr;
} gEv;
void post(const char* what, uint32_t dev) {
    std::lock_guard<std::mutex> g(gEv.m);
    if (!gEv.run) return;
    gEv.q.emplace_back(what, dev); gEv.cv.notify_one();
}
}  // namespace

uint32_t defaultOutputDevice() { std::lock_guard<std::mutex> g(gLock); return find(1) ? 1 : find(2) ? 2 : 0; }

static DeviceInfo infoOf(const NullDev& d) {
    DeviceInfo i; i.id = d.id; i.name = d.name; i.uid = d.uid; i.transport = "virtual"; i.manufacturer = "AudioLab";
    i.outChannels = 2; i.rate = d.rate; i.rates = d.rates; i.rateSettable = true;
    i.buffer = d.buffer; i.bufferMin = 15; i.bufferMax = 4096; i.bufferSettable = true;
    i.hasVolume = d.volume; i.volumeSettable = d.volume; i.volumeWhere = d.volume ? "main" : ""; i.volume = d.volume ? d.vol : -1; i.hasMute = d.volume;
    i.hogPid = d.hogPid; i.hogSettable = true;
    i.physicalFormat = std::to_string(d.bits) + "-bit " + (d.isFloat ? "float" : "integer") + ", 2 ch, " + jnum(d.rate) + " Hz, " + (d.mixable ? "mixable" : "not mixable");
    i.physicalFormats = (int)d.rates.size() * 2;
    i.isDefaultOutput = d.id == 1 || !find(1);
    return i;
}
std::vector<DeviceInfo> listDevices() { std::lock_guard<std::mutex> g(gLock); std::vector<DeviceInfo> v; for (auto& d : devs()) if (d.present) v.push_back(infoOf(d)); return v; }
DeviceInfo deviceInfo(uint32_t dev) { std::lock_guard<std::mutex> g(gLock); NullDev* d = find(dev); return d ? infoOf(*d) : DeviceInfo(); }
uint32_t deviceByUid(const std::string& uid) { std::lock_guard<std::mutex> g(gLock); for (auto& d : devs()) if (d.present && d.uid == uid) return d.id; return 0; }

std::string deviceJson(const DeviceInfo& d) {
    std::string s = "{";
    s += "\"id\":" + std::to_string(d.id) + ",\"name\":" + jstr(d.name) + ",\"maker\":" + jstr(d.manufacturer) + ",\"uid\":" + jstr(d.uid) + ",\"transport\":" + jstr(d.transport);
    s += ",\"outChannels\":" + std::to_string(d.outChannels) + ",\"inChannels\":" + std::to_string(d.inChannels);
    s += ",\"defaultOutput\":" + std::string(d.isDefaultOutput ? "true" : "false") + ",\"defaultInput\":false";
    s += ",\"rate\":" + jnum(d.rate) + ",\"rateSettable\":" + (d.rateSettable ? "true" : "false") + ",\"rates\":[";
    for (size_t i = 0; i < d.rates.size(); i++) s += (i ? "," : "") + jnum(d.rates[i]);
    s += "],\"rateRanges\":[],\"buffer\":" + std::to_string(d.buffer) + ",\"bufferMin\":" + std::to_string(d.bufferMin) + ",\"bufferMax\":" + std::to_string(d.bufferMax) + ",\"bufferSettable\":true";
    s += ",\"latencyFrames\":0,\"safetyOffsetFrames\":0,\"streamLatencyFrames\":0";
    s += ",\"hasVolume\":" + std::string(d.hasVolume ? "true" : "false") + ",\"volumeSettable\":" + (d.volumeSettable ? "true" : "false") + ",\"volumeWhere\":" + jstr(d.volumeWhere) + ",\"volume\":" + jnum(d.volume);
    s += ",\"hasMute\":" + std::string(d.hasMute ? "true" : "false") + ",\"hogPid\":" + std::to_string(d.hogPid) + ",\"hogSettable\":true";
    s += ",\"physicalFormat\":" + jstr(d.physicalFormat) + ",\"physicalFormats\":" + std::to_string(d.physicalFormats) + ",\"null\":true}";
    return s;
}
std::string devicesJson(const std::vector<DeviceInfo>& v) {
    std::string s = "[";
    for (size_t i = 0; i < v.size(); i++) s += (i ? ",\n  " : "\n  ") + deviceJson(v[i]);
    return s + "\n]";
}

bool setDeviceRate(uint32_t dev, double rate, double& now, std::string& err) {
    bool changed = false, ok = false;
    { std::lock_guard<std::mutex> g(gLock); NullDev* d = find(dev); if (!d) { err = "no such device"; return false; }
      for (double r : d->rates) if (r == rate) ok = true;
      if (ok && d->rate != rate) { d->rate = rate; changed = true; }
      now = d->rate; if (!ok) err = "the device does not offer " + jnum(rate) + " Hz"; }
    if (changed) post("rate", dev);
    return ok;
}
bool setDeviceBuffer(uint32_t dev, uint32_t frames, uint32_t& now, std::string& err) {
    bool changed = false;
    { std::lock_guard<std::mutex> g(gLock); NullDev* d = find(dev); if (!d) { err = "no such device"; return false; }
      if (frames < 15 || frames > 4096) { now = d->buffer; err = "15 to 4096 frames"; return false; }
      changed = d->buffer != frames; d->buffer = frames; now = frames; }
    if (changed) post("buffer", dev);
    return true;
}
bool setHog(uint32_t dev, bool take, int& ownerPid, std::string& err) {
    std::lock_guard<std::mutex> g(gLock); NullDev* d = find(dev); if (!d) { err = "no such device"; return false; }
    int me = (int)getpid();
    if (take) { if (d->hogPid != -1 && d->hogPid != me) { ownerPid = d->hogPid; return false; } d->hogPid = me; }
    else if (d->hogPid == me) d->hogPid = -1;
    ownerPid = d->hogPid; return true;
}
std::vector<PhysFormat> listPhysicalFormats(uint32_t dev) {
    std::lock_guard<std::mutex> g(gLock); std::vector<PhysFormat> v; NullDev* d = find(dev); if (!d) return v;
    for (double r : d->rates) { v.push_back({ r, 32, 2, true, true }); v.push_back({ r, 24, 2, false, false }); v.push_back({ r, 16, 2, false, false }); }
    return v;
}
bool setPhysicalFormat(uint32_t dev, double rate, int bits, bool mixable, std::string& now, std::string& err) {
    std::lock_guard<std::mutex> g(gLock); NullDev* d = find(dev); if (!d) { err = "no such device"; return false; }
    if (bits != 32 && bits != 24 && bits != 16) { err = "32-bit float, 24-bit or 16-bit integer"; now = infoOf(*d).physicalFormat; return false; }
    d->bits = bits; d->isFloat = bits == 32; d->mixable = mixable; d->rate = rate > 0 ? rate : d->rate; now = infoOf(*d).physicalFormat; return true;
}
bool getVolume(uint32_t dev, double& v) { std::lock_guard<std::mutex> g(gLock); NullDev* d = find(dev); if (!d || !d->volume) return false; v = d->vol; return true; }
bool setVolume(uint32_t dev, double v, std::string& err) {
    { std::lock_guard<std::mutex> g(gLock); NullDev* d = find(dev); if (!d) { err = "no such device"; return false; }
      if (!d->volume) { err = "this device has no volume the computer can set"; return false; }
      d->vol = v < 0 ? 0 : v > 1 ? 1 : v; }
    post("volume", dev); return true;
}
bool getMute(uint32_t dev, bool& m) { std::lock_guard<std::mutex> g(gLock); NullDev* d = find(dev); if (!d || !d->volume) return false; m = d->mute; return true; }
bool setMute(uint32_t dev, bool m) { { std::lock_guard<std::mutex> g(gLock); NullDev* d = find(dev); if (!d || !d->volume) return false; d->mute = m; } post("mute", dev); return true; }
// an integer format the system does not mix is handed to the program as it is (as Core Audio does); otherwise float
static bool nullInt(const NullDev& d) { return !d.isFloat && !d.mixable; }
std::string virtualFormatText(uint32_t dev) { std::lock_guard<std::mutex> g(gLock); NullDev* d = find(dev); if (!d) return ""; return (nullInt(*d) ? std::to_string(d->bits) + "-bit integer" : std::string("32-bit float")) + ", 2 ch, " + jnum(d->rate) + " Hz (null device)"; }
bool recordInput(uint32_t, double, std::vector<float>&, double&, std::string& err) { err = "the null device has no inputs"; return false; }

void Watcher::start(WatchFn f, void* u) {
    fn = f; user = u; system = true;
    std::lock_guard<std::mutex> g(gEv.m);
    if (gEv.run) return;
    gEv.run = true; gEv.w = this;
    gEv.t = std::thread([] {
        std::unique_lock<std::mutex> lk(gEv.m);
        while (gEv.run) {
            gEv.cv.wait(lk, [] { return !gEv.run || !gEv.q.empty(); });
            while (!gEv.q.empty()) {
                auto e = gEv.q.front(); gEv.q.pop_front();
                Watcher* w = gEv.w; uint32_t wd = w ? w->dev : 0; lk.unlock();   // dev read under the lock (watchDevice writes it)
                if (w && w->fn && (e.second == 0 || e.second == wd || e.first == "devices" || e.first == "default-output")) w->fn(w->user, e.first.c_str(), e.second);
                lk.lock();
            }
        }
    });
}
void Watcher::watchDevice(uint32_t d) { std::lock_guard<std::mutex> g(gEv.m); dev = d; }
void Watcher::stop() {
    { std::lock_guard<std::mutex> g(gEv.m); if (!gEv.run) return; gEv.run = false; gEv.cv.notify_all(); }
    if (gEv.t.joinable()) gEv.t.join();
    gEv.q.clear(); gEv.w = nullptr;
}

// ---- the stream: a thread in real time ----------------------------------------------------------------
namespace {
struct StreamRun { std::thread t; std::atomic<bool> run{false}; Wav rec; bool recording = false; std::string recPath; };
std::mutex gStreamLock;
std::vector<std::pair<OutputStream*, std::unique_ptr<StreamRun>>> gStreams;
StreamRun* runOf(OutputStream* s) { for (auto& p : gStreams) if (p.first == s) return p.second.get(); return nullptr; }
}  // namespace

bool OutputStream::start(uint32_t device, RenderFn f, void* u, std::string& err) {
    stop();
    { std::lock_guard<std::mutex> g(gLock); if (!find(device)) { err = "no such device"; return false; } }
    dev = device; fn = f; user = u;
    { std::lock_guard<std::mutex> g(gLock); NullDev* d = find(device); bool in = d && nullInt(*d);
      vFloat = !in; vBits = in ? d->bits : 32; vBytes = in ? (d->bits == 16 ? 2 : 4) : 4; vAlignedHigh = true; vBigEndian = false; }
    formatText = virtualFormatText(device);
    std::lock_guard<std::mutex> g(gStreamLock);
    StreamRun* r = runOf(this); if (!r) { gStreams.emplace_back(this, std::unique_ptr<StreamRun>(new StreamRun())); r = gStreams.back().second.get(); }
    const char* rp = getenv("AL_NULL_RECORD");
    r->recording = rp && *rp; r->recPath = rp ? rp : ""; r->rec = Wav(); r->rec.ch = 2;
    r->run = true; running = true;
    OutputStream* self = this;
    r->t = std::thread([self, r] {
        using clk = std::chrono::steady_clock;
        auto next = clk::now(); std::vector<float> L(4096), R(4096); float* out[2] = { L.data(), R.data() };
        while (r->run.load()) {
            double rate; uint32_t n; bool here;
            { std::lock_guard<std::mutex> g(gLock); NullDev* d = find(self->dev); here = d != nullptr; rate = d ? d->rate : 48000; n = d ? d->buffer : 256; }
            if (!here) { std::this_thread::sleep_for(std::chrono::milliseconds(5)); continue; }   // unplugged: the device's thread stops calling
            auto t0 = clk::now();
            self->fn(self->user, out, 2, (int)n);
            uint64_t ns = (uint64_t)std::chrono::duration_cast<std::chrono::nanoseconds>(clk::now() - t0).count();
            self->callbacks++; self->framesTotal += n; self->sumNs += ns;
            if (ns > self->worstNs.load()) self->worstNs = ns;
            if (n < self->minFrames.load()) self->minFrames = n;
            if (n > self->maxFrames.load()) self->maxFrames = n;
            if (!self->vFloat) {   // task NB-R4: an integer format: the bytes are written as for the DAC, the recording is what they decode to
                SampleFormat sf; sf.isFloat = false; sf.bits = self->vBits; sf.bytes = self->vBytes; sf.alignedHigh = true;
                Dither dth; dth.s = self->ditherState; std::vector<uint8_t> by((size_t)n * sf.bytes * 2);
                for (int c = 0; c < 2; c++) writeChannel(out[c], (int)n, by.data() + c * sf.bytes, sf.bytes * 2, sf, (sf.bits <= 16 && self->dither16) ? &dth : nullptr);
                self->ditherState = dth.s;
                double sc = (double)((int64_t)1 << (sf.bits - 1));
                for (uint32_t i = 0; i < n; i++) for (int c = 0; c < 2; c++) {
                    uint32_t u = 0; const uint8_t* p = by.data() + ((size_t)i * 2 + c) * sf.bytes; for (int b = 0; b < sf.bytes; b++) u |= (uint32_t)p[b] << (8 * b);
                    int32_t s = (int32_t)u >> (sf.bytes * 8 - sf.bits);   // aligned high: the sign comes down with the value
                    out[c][i] = (float)((double)s / sc);
                }
            }
            if (r->recording) { r->rec.sr = (int)rate; for (uint32_t i = 0; i < n; i++) { r->rec.data.push_back(L[i]); r->rec.data.push_back(R[i]); } }
            next += std::chrono::nanoseconds((int64_t)(1e9 * n / rate));
            auto now = clk::now();
            if (next < now - std::chrono::milliseconds(50)) { self->overloads++; next = now; }   // fell far behind: count it, as the HAL does
            std::this_thread::sleep_until(next);
        }
    });
    return true;
}
void OutputStream::stop() {
    StreamRun* r;
    { std::lock_guard<std::mutex> g(gStreamLock); r = runOf(this); }
    if (!r || !r->run.load()) { running = false; return; }
    r->run = false;
    if (r->t.joinable()) r->t.join();
    if (r->recording && !r->rec.data.empty()) {   // the first stream writes the path itself, later ones path.2.wav, path.3.wav ...
        static int n = 0; n++;
        wavWrite(n == 1 ? r->recPath : r->recPath + "." + std::to_string(n) + ".wav", r->rec);
    }
    r->rec.data.clear();
    running = false;
}

// ---- changes from outside (the engine's "null" command, tests) -----------------------------------------
std::string nullExternal(const std::string& what, double value, uint32_t dev) {
    std::string ev;
    { std::lock_guard<std::mutex> g(gLock);
      NullDev* d = nullptr; for (auto& x : devs()) if (x.id == dev) d = &x;
      if (!d) return "no such device";
      if (what == "rate") { bool ok = false; for (double r : d->rates) if (r == value) ok = true; if (!ok) return "the device does not offer that rate"; if (d->rate == value) return ""; d->rate = value; ev = "rate"; }
      else if (what == "volume") { if (!d->volume) return "this device has no volume"; d->vol = value; ev = "volume"; }
      else if (what == "unplug") { d->present = false; if (d->hogPid != -1) d->hogPid = -1; ev = "devices"; }
      else if (what == "plug") { d->present = true; ev = "devices"; }
      else if (what == "hog") { d->hogPid = (int)value; ev = "exclusive"; }
      // task NB-R4: another program changes the device's format (32 float and mixable, or 24 or 16 integer and not mixable)
      else if (what == "format") { int b = (int)value; if (b != 32 && b != 24 && b != 16) return "32, 24 or 16"; d->bits = b; d->isFloat = b == 32; d->mixable = b == 32; ev = "format"; }
      else return "unknown change"; }
    post(ev.c_str(), dev);
    return "";
}

}  // namespace al
#endif
