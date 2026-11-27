// The ring under two real threads (task NB-R1, review RN5). The selftest drives the ring from one thread; here a
// writer thread and a reader thread run at the same time, as the socket thread and the device's thread do in
// alengine, with block sizes and timing that wander, for a few seconds per mode. Built with -fsanitize=thread in
// CI, so any data race between the two sides is reported; the checks below hold in every build:
//   exact mode: every sample the reader gets is either silence (counted) or the next one the writer sent, except
//               right after a counted drop; left and right stay paired; nothing arrives that was never sent.
//   follow mode: no torn frames (left and right of the input are tied, so the output's must be too), nothing
//               outside the input's range, and the reader keeps moving.
//   ring_stress [seconds per mode]      prints one JSON line, exit code 0 when every check held
#include "../engine/ring.h"
#include <atomic>
#include <chrono>
#include <cmath>
#include <cstdio>
#include <random>
#include <string>
#include <thread>
#include <vector>

using namespace al;
using clk = std::chrono::steady_clock;

struct Result { std::string mode; uint64_t sent = 0, got = 0, silent = 0, bad = 0, torn = 0, outside = 0, underruns = 0, skips = 0, jumps = 0; };

static Result run(bool follow, double seconds, unsigned seed) {
    Result res; res.mode = follow ? "follow" : "exact";
    Ring ring; ring.init(8192, 1024, 4096); ring.rate = 48000;
    ring.follow = follow;
    if (follow) SincTable::get();             // built before the threads start (review C2: not on the audio thread)
    std::atomic<bool> stop{false};
    std::atomic<uint64_t> sent{0};
    // writer: blocks of 1 to 300 frames, sample value = frame number (left) and its negative (right), small sleeps
    std::thread writer([&] {
        std::mt19937 rng(seed); std::vector<float> blk(600);
        uint64_t n = 0;
        while (!stop.load(std::memory_order_relaxed)) {
            size_t want = 1 + rng() % 300;
            for (size_t i = 0; i < want; i++) { float v = (float)((n + i) % 1000000 + 1); blk[2 * i] = v; blk[2 * i + 1] = -v; }
            size_t took = ring.write(blk.data(), want);
            n += took; sent.store(n, std::memory_order_relaxed);
            if (took < want) std::this_thread::sleep_for(std::chrono::microseconds(200));
            else if (rng() % 4 == 0) std::this_thread::sleep_for(std::chrono::microseconds(rng() % 400));
        }
    });
    // reader: blocks of 16 to 512 frames, as a device thread would ask
    std::thread reader([&] {
        std::mt19937 rng(seed * 7 + 1); std::vector<float> L(512), R(512);
        float last = 0; uint64_t skipsSeen = 0, underSeen = 0;
        const auto t0 = clk::now();
        while (std::chrono::duration<double>(clk::now() - t0).count() < seconds) {
            size_t n = 16 + rng() % 497;
            ring.read(L.data(), R.data(), n);
            const uint64_t sk = ring.skips.load(), un = ring.underruns.load();
            for (size_t i = 0; i < n; i++) {
                const float l = L[i], r = R[i];
                if (l == 0 && r == 0) { res.silent++; continue; }
                res.got++;
                if (follow) {
                    if (std::fabs(l + r) > 1e-3f * std::fabs(l) + 1e-3f) res.torn++;
                    if (!std::isfinite(l)) res.outside++;   // (the ramp's wrap-around is a step, so the interpolator rings there: only finiteness is checked)
                    continue;
                }
                if (r != -l) { res.torn++; continue; }
                if (l < 1 || l > 1000000) { res.outside++; continue; }
                bool next = last == 0 || l == last + 1 || (last == 1000000 && l == 1);
                if (!next) {
                    // allowed only after a drop or an underrun the ring has counted since the last check
                    if (sk > skipsSeen || un > underSeen) res.jumps++; else res.bad++;
                }
                last = l;
            }
            skipsSeen = sk; underSeen = un;
            if (rng() % 3 == 0) std::this_thread::sleep_for(std::chrono::microseconds(rng() % 2000));
        }
        stop = true;
    });
    reader.join(); writer.join();
    res.sent = sent.load(); res.underruns = ring.underruns.load(); res.skips = ring.skips.load();
    return res;
}

int main(int argc, char** argv) {
    double sec = argc > 1 ? atof(argv[1]) : 3.0;
    bool ok = true; std::string out = "{\"re\":\"ring_stress\",\"modes\":[";
    int k = 0;
    for (bool follow : {false, true}) {
        Result r = run(follow, sec, 12345u + k);
        bool good = r.bad == 0 && r.torn == 0 && r.outside == 0 && r.got > 1000;
        ok = ok && good;
        char b[512];
        snprintf(b, sizeof b, "%s{\"mode\":\"%s\",\"ok\":%s,\"sent\":%llu,\"got\":%llu,\"silent\":%llu,\"wrongSample\":%llu,\"torn\":%llu,\"outside\":%llu,\"jumpsAfterCountedFix\":%llu,\"underruns\":%llu,\"drops\":%llu}",
                 k ? "," : "", r.mode.c_str(), good ? "true" : "false", (unsigned long long)r.sent, (unsigned long long)r.got, (unsigned long long)r.silent,
                 (unsigned long long)r.bad, (unsigned long long)r.torn, (unsigned long long)r.outside, (unsigned long long)r.jumps,
                 (unsigned long long)r.underruns, (unsigned long long)r.skips);
        out += b; k++;
    }
    out += std::string("],\"ok\":") + (ok ? "true" : "false") + "}";
    puts(out.c_str());
    return ok ? 0 : 1;
}
