// Task NL7: checks of native/host/live_tools.h (the text clean-up, the safety limiter, the event ring, the slowest
// blocks, the parameter poll) without a plug-in, a window or a sound card. Built and run by tools/native-lab/nl7/run.sh,
// normally and under AddressSanitizer + UndefinedBehaviorSanitizer, and ThreadSanitizer (the ring with 4 writers).
#include "../../../native/host/live_tools.h"
#include <cmath>
#include <cstdio>
#include <thread>
#include <vector>
using namespace al;
static int fails = 0;
static void check(bool ok, const char* what) { printf("%s %s\n", ok ? "PASS" : "FAIL", what); if (!ok) fails++; }

int main() {
    // text
    check(asciiClean("17.1\xE2\x80\xAFms") == "17.1 ms", "U+202F narrow no-break space -> space (Phase Plant's '17.1 ms')");
    check(asciiClean("\xE2\x88\x92" "3.26\xC2\xA0" "dB") == "-3.26 dB", "U+2212 minus and U+00A0 no-break space");
    check(asciiClean("Caf\xC3\xA9") == "Caf\xC3\xA9" && !isAscii(asciiClean("Caf\xC3\xA9")), "an accented letter stays (the report then gets a byte order mark)");
    check(asciiClean("a\xFF" "b\xE2\x80") == "a?b??", "bytes that are not UTF-8 become '?'");
    check(asciiClean("\xC0\xAF") == "??", "an overlong sequence is refused");
    check(asciiClean("x\xE2\x80\x94y\xE2\x80\xA6") == "x-y...", "em dash and ellipsis");
    // task NL8: the symbols of report 8 (kHs Phase Distortion's Spread "21 deg"), as UTF-8 and as Mac Roman mojibake
    check(asciiClean("21\xC2\xB0") == "21 deg", "NL8: U+00B0 degree sign -> ' deg' ('21 deg')");
    check(asciiClean("\xC2\xB5s \xC2\xB1" "3 \xC3\x97" "2 \xE2\x88\x9E m\xC2\xB2 m\xC2\xB3") == "us +/-3 x2 inf m2 m3", "NL8: micro, plus-minus, times, infinity, squared, cubed");
    check(asciiClean("21\xC2\xAC\xE2\x88\x9E") == "21 deg", "NL8: '21' + Mac Roman mojibake of the degree sign (what report 8 showed before the 0.5 clean-up) -> '21 deg'");
    check(asciiClean("\xC2\xAC\xC2\xB5s \xC2\xAC\xC2\xB1" "3 \xE2\x88\x9A\xC3\xB3" "2 \xE2\x80\x9A\xC3\xA0\xC3\xBB m\xC2\xAC\xE2\x89\xA4 m\xC2\xAC\xE2\x89\xA5 17.1\xE2\x80\x9A\xC3\x84\xC3\x98ms") == "us +/-3 x2 inf m2 m3 17.1 ms", "NL8: the same symbols as Mac Roman mojibake are repaired");
    check(asciiClean("\xC2\xAC") == "\xC2\xAC", "NL8: a lone 'not' sign stays");
    check(isAscii(asciiClean("21\xC2\xB0 \xC2\xB5 \xC2\xB1 \xC3\x97 \xE2\x88\x9E \xC2\xB2 \xC2\xB3")), "NL8: after the clean-up the symbols are plain ASCII (no byte order mark needed)");
    // limiter: a +28 dBFS sine (Phase Plant's +27.9) after the half level never passes full scale
    {
        SafetyLimiter lim; lim.setRate(44100);
        std::vector<float> L(512), R(512); float* ch[2] = {L.data(), R.data()};
        float pk = 0; double ph = 0;
        for (int b = 0; b < 200; b++) {
            for (int i = 0; i < 512; i++) { float v = (float)(25.0 * std::sin(ph)); ph += 2 * M_PI * 220 / 44100; L[i] = v * 0.5f; R[i] = -v * 0.5f; }
            if (b == 50) L[7] = NAN;
            if (b == 51) R[9] = INFINITY;
            pk = std::max(pk, lim.process(ch, 2, 512));
            for (int i = 0; i < 512; i++) if (!(std::fabs(L[i]) <= 0.9801f) || !(std::fabs(R[i]) <= 0.9801f)) { pk = 9; }
        }
        char b[200]; snprintf(b, sizeof b, "limiter on +28 dBFS: output peak %.4f <= 0.98 (one rounding step allowed; full scale is 1.0), engaged %llu time(s) (once, it never rested), %llu bad samples silenced, most %.1f dB",
                              pk, (unsigned long long)lim.engaged.load(), (unsigned long long)lim.badSamples.load(), lim.deepestDb.load());
        check(pk <= 0.9801f && lim.engaged.load() == 1 && lim.badSamples.load() == 2, b);
        // quiet sound passes untouched
        SafetyLimiter q; q.setRate(48000);
        for (int i = 0; i < 512; i++) { L[i] = 0.3f * (float)std::sin(i * 0.05); R[i] = L[i]; }
        std::vector<float> keep = L;
        q.process(ch, 2, 512);
        bool same = true; for (int i = 0; i < 512; i++) if (L[i] != keep[i]) same = false;
        check(same && q.engaged.load() == 0, "limiter leaves sound below the ceiling bit for bit");
        // three separate bursts engage it three times
        SafetyLimiter t; t.setRate(48000);
        for (int burst = 0; burst < 3; burst++) {
            for (int b = 0; b < 4; b++) { for (int i = 0; i < 512; i++) { L[i] = 2.0f * (float)std::sin(i * 0.1); R[i] = L[i]; } t.process(ch, 2, 512); }
            for (int b = 0; b < 100; b++) { for (int i = 0; i < 512; i++) { L[i] = 0.01f; R[i] = 0.01f; } t.process(ch, 2, 512); }
        }
        check(t.engaged.load() == 3, "three loud bursts with rests between: engaged 3 times");
    }
    // event ring: 4 writer threads, a reader at the same time
    {
        static EventRing ring;
        std::vector<std::thread> th;
        std::atomic<bool> go{true};
        std::thread reader([&] { while (go.load()) { auto v = ring.between(0, UINT64_MAX); (void)v; } });
        for (int k = 0; k < 4; k++) th.emplace_back([k] { for (int i = 0; i < 5000; i++) ring.push(evGestureBegin + k, (uint32_t)i); });
        for (auto& t : th) t.join();
        go = false; reader.join();
        bool back = true;
        auto v = ring.between(0, UINT64_MAX, &back);
        bool sorted = true; for (size_t i = 1; i < v.size(); i++) if (v[i].t < v[i - 1].t) sorted = false;
        char b[160]; snprintf(b, sizeof b, "event ring: 20000 events from 4 threads, the last %zu kept in time order; reaches back to time 0: %s", v.size(), back ? "yes" : "no");
        check(v.size() == (size_t)EventRing::N && sorted && !back, b);
        EventRing r2; r2.push(evWindowOpened, 0, 1000); r2.push(evPresetLoaded, 3, 2000); r2.push(evWindowClosed, 0, 5000);
        auto w = r2.between(1500, 4000, &back);
        check(w.size() == 1 && w[0].kind == evPresetLoaded && w[0].arg == 3 && back, "event ring: a time window picks the right event");
    }
    // slowest blocks
    {
        SlowBlocks s;
        uint64_t t = 1000000000ull;
        for (int i = 0; i < 1000; i++) s.offer(t + (uint64_t)i * 11600000ull, 500000);
        s.offer(t + 100 * 11600000ull, 5400000);          // the spike
        s.offer(t + 101 * 11600000ull, 5000000);          // the next block of the same spike: merged
        s.offer(t + 500 * 11600000ull, 3000000);
        s.offer(t + 800 * 11600000ull, 2000000);
        s.offer(t + 900 * 11600000ull, 1000000);          // slower than the rest, but 3 are kept
        auto v = s.get();
        check(v.size() == 3 && v[0].ns == 5400000 && v[1].ns == 3000000 && v[2].ns == 2000000 && v[0].start == t + 100 * 11600000ull, "slowest blocks: the 3 slowest, at least 100 ms apart, slowest first");
    }
    // parameter poll
    {
        ParamWatch pw; pw.setParams({1, 2, 3}, {"A", "B", "Meter"}, {false, false, true});
        double val[4] = {0, 0.1, 0.2, 0.3};
        auto get = [&](uint32_t id) { return val[id]; };
        pw.poll(get, {}, false);
        val[1] = 0.5; val[3] = 0.9;                       // A changed unreported; the meter (read-only) does not count
        auto f1 = pw.poll(get, {}, false);
        val[2] = 0.7; auto f2 = pw.poll(get, {2}, false);  // B reported through performEdit
        val[1] = 0.6; val[2] = 0.8; auto f3 = pw.poll(get, {}, true);   // a preset (restartComponent): not counted
        val[1] = 0.65; auto f4 = pw.poll(get, {}, false);
        check(pw.changes == 2 && f1.size() == 1 && f1[0] == "A" && f2.empty() && f3.empty() && f4.empty() && pw.firstNames.size() == 1, "parameter poll: unreported change counted, reported, read-only and preset changes not");
    }
    printf("%s: %d failed\n", fails ? "FAILED" : "all passed", fails);
    return fails ? 1 : 0;
}
