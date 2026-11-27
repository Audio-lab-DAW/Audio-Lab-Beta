// Small pieces of the test app 0.7 (task NL7) that need no window and no sound card, so they are tested on Linux too
// (tools/native-lab/nl7/live_tools_test.cpp, also under AddressSanitizer, UndefinedBehaviorSanitizer and ThreadSanitizer):
//   asciiClean    every string that comes from a plug-in, made plain ASCII where a plain character means the same
//   SafetyLimiter the app's own output never past full scale (nothing inside the plug-in is changed)
//   EventRing     what happened in the app and the plug-in's window, with times, written without locks
//   SlowBlocks    the slowest audio blocks and when they started (written by the audio thread only)
//   ParamWatch    parameter values that changed although the plug-in never told the host (no performEdit)
#pragma once
#include <algorithm>
#include <atomic>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <functional>
#include <set>
#include <string>
#include <vector>

namespace al {

// One clock for the audio thread and the window: steady_clock (on macOS mach time, read without a lock or a system call).
inline uint64_t nowNs() { return (uint64_t)std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::steady_clock::now().time_since_epoch()).count(); }

// ---- text --------------------------------------------------------------------------------------------------
// Narrow and no-break spaces become spaces, the minus sign and dashes a hyphen-minus, and so on (the same table as the
// app's own text since 0.5). Letters outside ASCII (an accented name) stay as they are, in UTF-8; whoever writes the
// text into a file then starts it with a byte order mark. Bytes that are not valid UTF-8 become '?'.
inline std::string asciiClean(const std::string& s) {
    struct M { uint32_t cp; const char* to; };
    static const M map[] = {
        {0x202F, " "}, {0x00A0, " "}, {0x2009, " "}, {0x2007, " "}, {0x2002, " "}, {0x2003, " "}, {0x200A, " "}, {0x2008, " "}, {0x2006, " "}, {0x2005, " "}, {0x2004, " "},
        {0x200B, ""}, {0xFEFF, ""}, {0x2060, ""},
        {0x2212, "-"}, {0x2010, "-"}, {0x2011, "-"}, {0x2012, "-"}, {0x2013, "-"}, {0x2014, "-"}, {0x2015, "-"},
        {0x2026, "..."}, {0x00D7, "x"}, {0x2018, "'"}, {0x2019, "'"}, {0x201A, ","}, {0x201C, "\""}, {0x201D, "\""}, {0x201E, "\""},
        {0x00B5, "u"}, {0x03BC, "u"}, {0x00B0, " deg"}, {0x2032, "'"}, {0x2033, "\""}, {0x221E, "inf"}, {0x2318, "Cmd"}, {0x26A0, "!"}, {0x00B1, "+/-"},
        {0x2192, "->"}, {0x2190, "<-"}, {0x00BD, "1/2"}, {0x00BC, "1/4"}, {0x00BE, "3/4"}, {0x2022, "*"}, {0x00B7, "."}, {0x2122, "(TM)"}, {0x00AE, "(R)"}, {0x00A9, "(C)"},
        {0x266F, "#"}, {0x266D, "b"}, {0x00B2, "2"}, {0x00B3, "3"}, {0x00B9, "1"}, {0x2030, " per mille"}};
    std::string o; o.reserve(s.size());
    size_t i = 0, n = s.size();
    while (i < n) {
        unsigned char c = (unsigned char)s[i];
        if (c < 0x80) { o += (char)c; i++; continue; }
        int len = (c & 0xE0) == 0xC0 ? 2 : (c & 0xF0) == 0xE0 ? 3 : (c & 0xF8) == 0xF0 ? 4 : 0;
        bool ok = len > 0 && i + len <= n;
        uint32_t cp = len == 2 ? (c & 0x1F) : len == 3 ? (c & 0x0F) : (c & 0x07);
        for (int k = 1; ok && k < len; k++) { unsigned char d = (unsigned char)s[i + k]; if ((d & 0xC0) != 0x80) ok = false; else cp = (cp << 6) | (d & 0x3F); }
        if (ok && ((len == 2 && cp < 0x80) || (len == 3 && cp < 0x800) || (len == 4 && cp < 0x10000) || cp > 0x10FFFF || (cp >= 0xD800 && cp <= 0xDFFF))) ok = false;
        if (!ok) { o += '?'; i++; continue; }
        const char* to = nullptr;
        for (const M& m : map) if (m.cp == cp) { to = m.to; break; }
        if (to) o += to; else o.append(s, i, len);
        i += len;
    }
    return o;
}
inline bool isAscii(const std::string& s) { for (unsigned char c : s) if (c >= 0x80) return false; return true; }

// ---- the app's output never past full scale ---------------------------------------------------------------------
// A peak limiter on the app's own output (after the plug-in, after the app's half level): stereo linked, instant
// attack (the gain follows each sample, so no sample passes the ceiling), 150 ms release, then a hard clip at full
// scale as the last guard, and NaN or infinity made silent. "Engaged" counts each time it starts to act after resting.
struct SafetyLimiter {
    float ceiling = 0.98f;                    // -0.18 dBFS
    float rel = 0.9998f;                      // set by setRate
    float env = 0;                            // the level the gain is computed from
    bool acting = false;
    std::atomic<uint64_t> engaged{0}, samplesLimited{0}, badSamples{0};
    std::atomic<float> deepestDb{0};          // the most gain reduction so far, in dB (negative)
    void setRate(double sr) { rel = (float)std::exp(-1.0 / (0.150 * (sr > 0 ? sr : 48000))); }
    void reset() { env = 0; acting = false; engaged = 0; samplesLimited = 0; badSamples = 0; deepestDb = 0; }
    // returns the block's output peak after limiting
    float process(float** ch, int nch, int frames) {
        float pk = 0, deep = 0; uint64_t lim = 0, bad = 0;
        for (int i = 0; i < frames; i++) {
            float a = 0;
            for (int c = 0; c < nch; c++) {
                float v = ch[c][i];
                if (!std::isfinite(v)) { ch[c][i] = 0; bad++; v = 0; }
                float x = v < 0 ? -v : v; if (x > a) a = x;
            }
            env *= rel; if (a > env) env = a;            // never below this sample: the gain below keeps it under the ceiling
            if (env < ceiling) env = env < 1e-9f ? 0 : env;
            float g = env > ceiling ? ceiling / env : 1.0f;
            if (g < 0.99999f) {
                if (!acting) { acting = true; engaged.fetch_add(1, std::memory_order_relaxed); }
                lim++;
                float db = 20.0f * std::log10(g); if (db < deep) deep = db;
            } else if (acting && env < ceiling * 0.98f) acting = false;   // rested: the next push engages it again
            for (int c = 0; c < nch; c++) {
                float v = ch[c][i] * g;
                if (v > 1.0f) v = 1.0f; else if (v < -1.0f) v = -1.0f;
                ch[c][i] = v;
                float x = v < 0 ? -v : v; if (x > pk) pk = x;
            }
        }
        if (lim) samplesLimited.fetch_add(lim, std::memory_order_relaxed);
        if (bad) badSamples.fetch_add(bad, std::memory_order_relaxed);
        if (deep < deepestDb.load(std::memory_order_relaxed)) deepestDb.store(deep, std::memory_order_relaxed);
        return pk;
    }
};

// ---- what happened, when -------------------------------------------------------------------------------------------
// A ring of recent events (window opened or closed, preset or program loaded, restartComponent, state set, parameter
// gestures, device switches...). Any thread may write (the plug-in calls the host from its own threads), nobody waits:
// a writer takes a slot with one atomic add; a reader skips a slot that is being written. Only numbers are stored;
// the app turns them into words when it writes the report.
enum EventKind : uint32_t {
    evNone = 0, evWindowOpened, evWindowClosed, evPresetLoaded, evRestart, evStateSet, evGestureBegin, evGestureEnd,
    evDeviceSwitch, evPluginLoaded, evPatternOn, evPatternOff, evMouseInWindow, evParamFromHost, evFormatChanged, evRateChanged, evBufferChanged, evProbe
};
struct EventRing {
    static const int N = 1024;
    struct Slot { std::atomic<uint64_t> seq{0}, t{0}; std::atomic<uint32_t> kind{0}, arg{0}; };
    Slot slots[N];
    std::atomic<uint64_t> w{0};
    void push(uint32_t kind, uint32_t arg, uint64_t t = 0) {
        if (!t) t = nowNs();
        uint64_t i = w.fetch_add(1, std::memory_order_relaxed);
        Slot& s = slots[i % N];
        s.seq.store(0, std::memory_order_release);           // being written
        s.t.store(t, std::memory_order_relaxed); s.kind.store(kind, std::memory_order_relaxed); s.arg.store(arg, std::memory_order_relaxed);
        s.seq.store(i + 1, std::memory_order_release);
    }
    struct Ev { uint64_t t; uint32_t kind, arg; };
    // events with from <= t <= to, oldest first; reachesBack: false when the ring no longer holds that time
    std::vector<Ev> between(uint64_t from, uint64_t to, bool* reachesBack = nullptr) const {
        std::vector<Ev> v;
        uint64_t end = w.load(std::memory_order_acquire), begin = end > (uint64_t)N ? end - N : 0;
        uint64_t oldest = UINT64_MAX;
        for (uint64_t i = begin; i < end; i++) {
            const Slot& s = slots[i % N];
            uint64_t q = s.seq.load(std::memory_order_acquire);
            if (q != i + 1) continue;
            Ev e{s.t.load(std::memory_order_relaxed), s.kind.load(std::memory_order_relaxed), s.arg.load(std::memory_order_relaxed)};
            if (s.seq.load(std::memory_order_acquire) != q) continue;
            if (e.t < oldest) oldest = e.t;
            if (e.t >= from && e.t <= to) v.push_back(e);
        }
        std::sort(v.begin(), v.end(), [](const Ev& a, const Ev& b) { return a.t < b.t; });
        if (reachesBack) *reachesBack = end <= (uint64_t)N || oldest <= from;
        return v;
    }
};

// ---- the slowest blocks ------------------------------------------------------------------------------------------------
// The audio thread offers each block (start time and duration); the 3 slowest are kept, at least 100 ms apart (a spike
// that lasts several blocks counts once, with its slowest block). Written by one thread; read by the window.
struct SlowBlocks {
    static const int K = 3;
    std::atomic<uint64_t> ns[K], start[K];
    SlowBlocks() { reset(); }
    void reset() { for (int i = 0; i < K; i++) { ns[i].store(0); start[i].store(0); } }
    void offer(uint64_t t0, uint64_t d) {
        if (d <= ns[K - 1].load(std::memory_order_relaxed)) return;   // not slower than any kept one (nor than a near one)
        uint64_t n[K], s[K];
        for (int i = 0; i < K; i++) { n[i] = ns[i].load(std::memory_order_relaxed); s[i] = start[i].load(std::memory_order_relaxed); }
        int near = -1;
        for (int i = 0; i < K; i++) if (s[i] && (t0 > s[i] ? t0 - s[i] : s[i] - t0) < 100000000ull) { near = i; break; }
        if (near >= 0) { if (d <= n[near]) return; for (int i = near; i < K - 1; i++) { n[i] = n[i + 1]; s[i] = s[i + 1]; } n[K - 1] = 0; s[K - 1] = 0; }
        int pos = K - 1; while (pos > 0 && d > n[pos - 1]) pos--;
        for (int i = K - 1; i > pos; i--) { n[i] = n[i - 1]; s[i] = s[i - 1]; }
        n[pos] = d; s[pos] = t0;
        for (int i = 0; i < K; i++) { ns[i].store(n[i], std::memory_order_relaxed); start[i].store(s[i], std::memory_order_relaxed); }
    }
    struct B { uint64_t ns, start; };
    std::vector<B> get() const { std::vector<B> v; for (int i = 0; i < K; i++) { uint64_t n = ns[i].load(std::memory_order_relaxed); if (n) v.push_back({n, start[i].load(std::memory_order_relaxed)}); } std::sort(v.begin(), v.end(), [](const B& a, const B& b) { return a.ns > b.ns; }); return v; }
};

// ---- parameters that change without the host being told --------------------------------------------------------------
// The window polls every parameter (getParamNormalized: cheap, main thread) every 200 ms while the plug-in's window is
// open. A value that changed since the last poll counts unless the plug-in reported it (performEdit), the host set it
// itself, or the plug-in said all values changed (restartComponent with kParamValuesChanged, a preset). Read-only
// parameters (meters) are left out.
struct ParamWatch {
    std::vector<uint32_t> ids; std::vector<std::string> names; std::vector<bool> skip;
    std::vector<double> last; bool have = false;
    uint64_t changes = 0; std::set<uint32_t> seen; std::vector<std::string> firstNames;
    void setParams(const std::vector<uint32_t>& i, const std::vector<std::string>& n, const std::vector<bool>& readOnly) { ids = i; names = n; skip = readOnly; last.assign(ids.size(), 0); have = false; changes = 0; seen.clear(); firstNames.clear(); }
    void forget() { have = false; }               // the window was closed: the next poll only takes the values
    // touched: ids the plug-in reported (performEdit) or the host set since the last poll. Returns the names newly seen
    // changing without a report (each name once), for a live line.
    std::vector<std::string> poll(const std::function<double(uint32_t)>& get, const std::set<uint32_t>& touched, bool allChanged) {
        std::vector<std::string> fresh;
        for (size_t k = 0; k < ids.size(); k++) {
            if (skip[k]) continue;
            double v = get(ids[k]);
            if (have && !allChanged && std::fabs(v - last[k]) > 1e-9 && !touched.count(ids[k])) {
                changes++;
                if (seen.insert(ids[k]).second) { if (firstNames.size() < 5) firstNames.push_back(names[k]); fresh.push_back(names[k]); }
            }
            last[k] = v;
        }
        have = true;
        return fresh;
    }
};

}  // namespace al
