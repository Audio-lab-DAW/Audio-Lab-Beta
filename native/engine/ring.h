// A ring for audio between the thread that receives sound and the device's own thread (task NB-N1).
// One writer, one reader, no locks. Stereo frames, interleaved.
//
// "Exact" hand-over: the samples go to the device untouched. Two clocks (the sender's and the device's) drift
// apart by a few parts in a million, so now and then the fill level leaves its band; then the ring corrects
// itself once (drops what is too much, or waits and plays silence) and counts it. Between corrections every
// sample is the one that was sent.
#pragma once
#include "follow.h"
#include <atomic>
#include <cstdint>
#include <cstring>
#include <vector>

namespace al {

struct Ring {
    std::vector<float> buf;
    size_t frames = 0;
    std::atomic<uint64_t> w{0}, r{0};
    std::atomic<uint64_t> underruns{0}, skips{0}, skippedFrames{0}, silentFrames{0};
    std::atomic<bool> primed{false};
    size_t target = 2400, high = 9600;   // frames: start playing at target, drop back to target above high
    // task NB-N2b: "follow" mode (follow.h). The reader moves at 1 + u samples per output sample, u steered by the fill.
    std::atomic<bool> follow{false};
    double frac = 0, rate = 48000;
    Steer steer;
    std::atomic<int64_t> ppmMilli{0};    // the last steering value in thousandths of a part per million (for status)
    std::atomic<int64_t> ppmMinMilli{0}, ppmMaxMilli{0};
    // task NB-R2 (review C5): requests from other threads, carried out by the reader itself
    std::atomic<bool> steerResetReq{false};
    // task NB-R5: the smallest fill seen while playing (reader only writes it; reset on request), so the app can see
    // how close the ring came to running empty and pick its target from measurements
    std::atomic<uint64_t> fillMin{UINT64_MAX}; std::atomic<bool> fillMinResetReq{false};
    void noteFill(size_t have) { if (fillMinResetReq.exchange(false)) fillMin = UINT64_MAX; if (have < fillMin.load()) fillMin = have; }
    void requestSteerReset() { steerResetReq = true; }
    // reader only: forget everything not yet played (used while the page's rate does not match the device's)
    size_t drain() { uint64_t wp = w.load(), rp = r.load(); r.store(wp); primed = false; return (size_t)(wp - rp); }
    static constexpr size_t HISTORY = 160; // frames behind the read position the writer must leave alone (the interpolator looks back)

    void init(size_t capacityFrames, size_t targetFrames, size_t highFrames) {
        frames = capacityFrames; buf.assign(frames * 2, 0.f); w = 0; r = 0; primed = false;
        target = targetFrames; high = highFrames;
        underruns = 0; skips = 0; skippedFrames = 0; silentFrames = 0;
        frac = 0; steer.reset(); ppmMilli = 0; ppmMinMilli = 0; ppmMaxMilli = 0; fillMin = UINT64_MAX; fillMinResetReq = false;
    }
    size_t fill() const { return (size_t)(w.load() - r.load()); }
    // writer: returns frames taken (drops what does not fit)
    size_t write(const float* interleaved, size_t n) {
        size_t f = fill(), space = f + HISTORY < frames ? frames - f - HISTORY : 0; if (n > space) n = space;
        uint64_t wp = w.load();
        for (size_t i = 0; i < n; i++) { size_t k = (size_t)((wp + i) % frames) * 2; buf[k] = interleaved[2 * i]; buf[k + 1] = interleaved[2 * i + 1]; }
        w.store(wp + n);
        return n;
    }
    // reader (device thread): always fills n frames
    void read(float* L, float* R, size_t n) {
        if (follow.load()) { readFollow(L, R, n); return; }
        size_t have = fill();
        if (!primed.load()) {
            if (have < target) { memset(L, 0, n * sizeof(float)); memset(R, 0, n * sizeof(float)); silentFrames += n; return; }
            primed = true;
        }
        noteFill(have);
        if (have > high) { size_t drop = have - target; r.store(r.load() + drop); skips++; skippedFrames += drop; have = target; }
        size_t take = n < have ? n : have;
        uint64_t rp = r.load();
        for (size_t i = 0; i < take; i++) { size_t k = (size_t)((rp + i) % frames) * 2; L[i] = buf[k]; R[i] = buf[k + 1]; }
        r.store(rp + take);
        if (take < n) { memset(L + take, 0, (n - take) * sizeof(float)); memset(R + take, 0, (n - take) * sizeof(float)); underruns++; silentFrames += n - take; primed = false; }
    }

    // task NB-N2b: the follower. Reads between the samples at a steered speed (follow.h).
    void readFollow(float* L, float* R, size_t n) {
        const SincTable& S = SincTable::get();
        if (steerResetReq.exchange(false)) steer.reset();
        const int H = SincTable::HALF, T = SincTable::TAPS, P = SincTable::PHASES;
        size_t have = fill();
        if (!primed.load()) {
            if (have < target + H) { memset(L, 0, n * sizeof(float)); memset(R, 0, n * sizeof(float)); silentFrames += n; return; }
            // task NB-R5: the steering is kept when the ring primes again after running empty: the sender's clock it
            // learned is still right, and starting over from zero made a slow sender run empty again and again
            // (14 times in 4 minutes at -1000 ppm in the selftest). init() and a clock switch still start over.
            primed = true; frac = 0;
        }
        noteFill(have);
        if (have > high) { size_t drop = have - target; r.store(r.load() + drop); skips++; skippedFrames += drop; have = target; steer.holdIntegral(); }   // task NB-R5: keep the learned clock, forget the fill's history
        double u = steer.update(((double)have - frac) / rate, (double)target / rate, (double)n / rate);
        int64_t pm = (int64_t)std::llround(u * 1e9);
        ppmMilli = pm; if (pm < ppmMinMilli.load()) ppmMinMilli = pm; if (pm > ppmMaxMilli.load()) ppmMaxMilli = pm;
        double step = 1.0 + u;
        uint64_t rp = r.load(); const uint64_t wp = w.load(); const int64_t F = (int64_t)frames;
        size_t i = 0;
        for (; i < n; i++) {
            if (rp + (uint64_t)H >= wp) break;                   // the interpolator needs H frames ahead
            if (frac == 0.0 && step == 1.0) {               // task NB-R5: speed exactly 1 on a whole sample: the sample itself, bit for bit (even -0.0)
                const float* fr = &buf[(size_t)((rp + 0) % frames) * 2]; L[i] = fr[0]; R[i] = fr[1]; rp++; continue;
            }
            double pf = frac * P; int p = (int)pf; if (p >= P) p = P - 1; float a = (float)(pf - p);
            const float* k0 = &S.t[(size_t)p * T]; const float* k1 = k0 + T;
            int64_t base = (int64_t)rp - (H - 1);
            int64_t idx = base % F; if (idx < 0) idx += F;
            float l = 0, rr = 0;
            for (int k = 0; k < T; k++) {
                float c = k0[k] + a * (k1[k] - k0[k]);
                const float* fr = &buf[(size_t)idx * 2];
                l += fr[0] * c; rr += fr[1] * c;
                if (++idx == F) idx = 0;
            }
            L[i] = l; R[i] = rr;
            frac += step;
            while (frac >= 1.0) { frac -= 1.0; rp++; }
        }
        r.store(rp);
        if (i < n) { memset(L + i, 0, (n - i) * sizeof(float)); memset(R + i, 0, (n - i) * sizeof(float)); underruns++; silentFrames += n - i; primed = false; }
    }
};

}  // namespace al
