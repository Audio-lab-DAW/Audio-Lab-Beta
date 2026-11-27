// A ring for audio between the thread that receives sound and the device's own thread (task NB-N1).
// One writer, one reader, no locks. Stereo frames, interleaved.
//
// "Exact" hand-over: the samples go to the device untouched. Two clocks (the sender's and the device's) drift
// apart by a few parts in a million, so now and then the fill level leaves its band; then the ring corrects
// itself once (drops what is too much, or waits and plays silence) and counts it. Between corrections every
// sample is the one that was sent.
#pragma once
#include <atomic>
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

    void init(size_t capacityFrames, size_t targetFrames, size_t highFrames) {
        frames = capacityFrames; buf.assign(frames * 2, 0.f); w = 0; r = 0; primed = false;
        target = targetFrames; high = highFrames;
        underruns = 0; skips = 0; skippedFrames = 0; silentFrames = 0;
    }
    size_t fill() const { return (size_t)(w.load() - r.load()); }
    // writer: returns frames taken (drops what does not fit)
    size_t write(const float* interleaved, size_t n) {
        size_t space = frames - fill(); if (n > space) n = space;
        uint64_t wp = w.load();
        for (size_t i = 0; i < n; i++) { size_t k = (size_t)((wp + i) % frames) * 2; buf[k] = interleaved[2 * i]; buf[k + 1] = interleaved[2 * i + 1]; }
        w.store(wp + n);
        return n;
    }
    // reader (device thread): always fills n frames
    void read(float* L, float* R, size_t n) {
        size_t have = fill();
        if (!primed.load()) {
            if (have < target) { memset(L, 0, n * sizeof(float)); memset(R, 0, n * sizeof(float)); silentFrames += n; return; }
            primed = true;
        }
        if (have > high) { size_t drop = have - target; r.store(r.load() + drop); skips++; skippedFrames += drop; have = target; }
        size_t take = n < have ? n : have;
        uint64_t rp = r.load();
        for (size_t i = 0; i < take; i++) { size_t k = (size_t)((rp + i) % frames) * 2; L[i] = buf[k]; R[i] = buf[k + 1]; }
        r.store(rp + take);
        if (take < n) { memset(L + take, 0, (n - take) * sizeof(float)); memset(R + take, 0, (n - take) * sizeof(float)); underruns++; silentFrames += n - take; primed = false; }
    }
};

}  // namespace al
