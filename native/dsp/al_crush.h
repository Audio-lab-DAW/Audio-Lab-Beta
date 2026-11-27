// AudioLab Bitcrusher, a port of the worklet 'al-crush' (class Crush in WLSRC, index.html).
// Task NM1, test A. The aim is the same bits as the web engine, so this file follows the JavaScript
// statement by statement: all state is double (JavaScript numbers), inputs and outputs are float
// (Float32Array), and the order of every operation is kept. Build with -ffp-contract=off: on Apple
// chips the compiler otherwise fuses a*b+c into one instruction, which rounds differently.
#pragma once
#include <cmath>
#include <cstdint>
#include <cstring>
#include <string>

namespace al {

// The worklet bundle replaces Math.random with this seeded generator (wlLoad in index.html).
struct WorkletRandom {
    uint32_t a = 0x9e3779b9u, b = 0x243f6a88u, c = 0xb7e15162u, d = 0x7f4a7c15u;
    double next() {
        uint32_t t = a + b;
        a = b ^ (b >> 9);
        b = c + (c << 3);
        c = (c << 21) | (c >> 11);
        d = d + 1;
        t = t + d;
        c = c + t;
        return (double)t / 4294967296.0;
    }
};

// JavaScript Math.round: to the nearest whole number, halves go up, the sign of zero is kept.
inline double jsRound(double x) {
    double r = std::floor(x);
    if (x - r >= 0.5) r += 1.0;
    if (r == 0.0 && (x < 0.0 || std::signbit(x))) return -0.0;
    return r;
}

struct CrushParams {
    double bits = 8, rate = 1, jit = 0, dith = 0, drive = 0, mix = 100, out = 0, pre = 20000, post = 20000;
    std::string shape = "round";
};

// The numbers the worklet works out from the settings with pow() and exp(). They can be given from
// outside (the web engine's own values) so both sides run the same arithmetic.
struct CrushCoef {
    double q = 0, dr = 1, go = 1, pc = 1, oc = 1;
};

inline CrushCoef crushCoef(const CrushParams& p, double sr) {
    const double TAU = 3.141592653589793 * 2;
    CrushCoef k;
    double bits = std::fmax(1, std::fmin(24, p.bits != 0 ? p.bits : 8));
    k.q = std::pow(2.0, bits - 1);
    k.dr = std::pow(10.0, p.drive / 20);
    k.go = std::pow(10.0, p.out / 20);
    k.pc = p.pre > 0 ? 1 - std::exp(-TAU * std::fmin(sr * .45, p.pre) / sr) : 1;
    k.oc = p.post > 0 ? 1 - std::exp(-TAU * std::fmin(sr * .45, p.post) / sr) : 1;
    return k;
}

struct Crush {
    double ph = 1, hl[2] = {0, 0}, pl[2] = {0, 0}, po[2] = {0, 0};
    int blocks = 0;
    WorkletRandom* rnd = nullptr;  // shared by all worklets of one engine, as in the page

    // One render block (the web engine uses 128 frames).
    void process(const CrushParams& p, const CrushCoef& k, const float* L, const float* R, float* oL, float* oR, int n) {
        const double q = k.q, rt = std::fmax(1, p.rate != 0 ? p.rate : 1), jt = p.jit / 100, dith = p.dith / 100 / q,
                     dr = k.dr, mix = p.mix / 100, go = k.go, pc = k.pc, oc = k.oc;
        const int mode = p.shape == "floor" ? 1 : p.shape == "trunc" ? 2 : p.shape == "fold" ? 3 : 0;
        for (int i = 0; i < n; i++) {
            const double xs[2] = {(double)L[i], (double)R[i]};
            ph += 1;
            if (ph >= rt * (1 + (rnd->next() * 2 - 1) * jt)) {
                ph -= rt;
                for (int c = 0; c < 2; c++) {
                    pl[c] += pc * (xs[c] * dr - pl[c]);
                    double v = pl[c], d = 0;
                    if (dith != 0) { double r1 = rnd->next(); double r2 = rnd->next(); d = (r1 - r2) * dith; }
                    v = mode == 1 ? std::floor((v + d) * q) / q : mode == 2 ? std::trunc((v + d) * q) / q : jsRound((v + d) * q) / q;
                    if (mode == 3) v = std::fabs(std::fmod(std::fmod(v + 1, 4.0) + 4, 4.0) - 2) - 1;
                    hl[c] = v > 1 ? 1 : v < -1 ? -1 : v;
                }
            }
            for (int c = 0; c < 2; c++) {
                po[c] += oc * (hl[c] - po[c]);
                const double wet = po[c] * go, y = xs[c] * (1 - mix) + wet * mix;
                (c ? oR : oL)[i] = (float)y;
            }
        }
        // dnGuard / dnFlush in the bundle: every 16 blocks, state below 1e-30 is set to exactly zero.
        if (++blocks >= 16) {
            blocks = 0;
            auto z = [](double& v) { if (v < 1e-30 && v > -1e-30 && v != 0) v = 0; };
            for (int c = 0; c < 2; c++) { z(hl[c]); z(pl[c]); z(po[c]); }
            z(ph);
        }
    }
};

}  // namespace al
