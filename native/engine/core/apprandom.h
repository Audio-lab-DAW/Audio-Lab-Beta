// The app's RND() (index.html, task NB-N3i): during an export, a bounce and the native engine's tests it is a seeded
// sfc32 generator made by seedRng(string) (a hash of the project seed and the render range); otherwise
// Math.random. Every random part of the sound comes from it (noise, grains, round robin, the reverbs' impulses,
// dither), in the order the app asks for numbers, so the engine must draw them in the same order to get the same
// sound. The arithmetic is JavaScript's 32-bit integer arithmetic (Math.imul, >>>, ^, |0), exactly.
#pragma once
#include <cstdint>
#include <random>
#include <string>
#include <vector>

namespace al {

class AppRandom {
public:
    AppRandom() { std::random_device rd; a_ = rd(); b_ = rd(); c_ = rd(); d_ = rd(); }   // Math.random: any numbers
    explicit AppRandom(const std::string& seedStr) { seed(seedStr); }
    // seedRng(str): the string's UTF-16 code units hashed, sfc32 started from the hash, 15 numbers dropped
    void seed(const std::string& str) {
        uint32_t h1 = 1779033703u, h2 = 3144134277u, h3 = 1013904242u, h4 = 2773480762u;
        for (uint32_t k : utf16(str)) {
            h1 = h2 ^ (uint32_t)(h1 ^ k) * 597399067u;
            h2 = h3 ^ (uint32_t)(h2 ^ k) * 2869860233u;
            h3 = h4 ^ (uint32_t)(h3 ^ k) * 951274213u;
            h4 = h1 ^ (uint32_t)(h4 ^ k) * 2716044179u;
        }
        h1 = (h3 ^ (h1 >> 18)) * 597399067u;
        h2 = (h4 ^ (h2 >> 22)) * 2869860233u;
        h3 = (h1 ^ (h3 >> 17)) * 951274213u;
        h4 = (h2 ^ (h4 >> 19)) * 2716044179u;
        a_ = h1 ^ h2 ^ h3 ^ h4; b_ = h2 ^ h1; c_ = h3 ^ h1; d_ = h4 ^ h1;
        for (int i = 0; i < 15; i++) next();
    }
    // sfc32's next number in [0, 1)
    double next() {
        drawn_++;
        uint32_t t = a_ + b_;
        a_ = b_ ^ (b_ >> 9);
        b_ = c_ + (c_ << 3);
        c_ = (c_ << 21) | (c_ >> 11);
        d_ = d_ + 1;
        t = t + d_;
        c_ = c_ + t;
        return (double)t / 4294967296.0;
    }
    double operator()() { return next(); }
    uint64_t drawn() const { return drawn_; }

private:
    static std::vector<uint32_t> utf16(const std::string& s) {   // UTF-8 in, JavaScript's code units out
        std::vector<uint32_t> o;
        for (size_t i = 0; i < s.size();) {
            const unsigned char c = (unsigned char)s[i];
            uint32_t cp; int n;
            if (c < 0x80) { cp = c; n = 1; } else if ((c >> 5) == 6) { cp = c & 31; n = 2; } else if ((c >> 4) == 14) { cp = c & 15; n = 3; } else { cp = c & 7; n = 4; }
            for (int j = 1; j < n && i + j < s.size(); j++) cp = (cp << 6) | ((unsigned char)s[i + j] & 63);
            i += n;
            if (cp >= 0x10000) { cp -= 0x10000; o.push_back(0xD800 + (cp >> 10)); o.push_back(0xDC00 + (cp & 1023)); } else o.push_back(cp);
        }
        return o;
    }
    uint32_t a_ = 0, b_ = 0, c_ = 0, d_ = 0;
    uint64_t drawn_ = 0;
};

}  // namespace al
