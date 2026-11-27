// The clock follower (task NB-N2b). When the sound comes from a sender with its own clock (the web engine
// inside the desktop shell runs on the clock of whatever device the page plays into) and the engine plays on
// another device, the two clocks drift by some parts per million. The "exact" ring (ring.h) then drops or
// waits once every few minutes. The follower instead reads the ring at a rate that is steered, very slowly,
// by how full the ring is: a windowed-sinc interpolator reads between the samples, and a PI controller keeps
// the fill at its target. No gaps, no drops; the price is that samples are no longer the ones that were sent
// (the change is a few parts per million in speed, far below hearing, but not bit-perfect).
//
// Bit-perfect playback stays possible in two ways: the ring's "exact" mode, and N3 (the native engine makes
// the sound itself on the device's own clock, so there is nothing to follow).
#pragma once
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <vector>

namespace al {

// Kaiser-windowed sinc, 48 taps, 4096 phases, linear between phases. Passes up to 0.92 of the top frequency
// (22 kHz at 48 kHz); error against the ideal below -110 dB in the band that matters (measured in the selftest).
struct SincTable {
    static constexpr int HALF = 24, TAPS = 2 * HALF, PHASES = 4096;
    std::vector<float> t;   // (PHASES + 1) rows of TAPS: row p is the kernel for a fraction p / PHASES
    static double bessel0(double x) { double s = 1, term = 1; for (int k = 1; k < 40; k++) { term *= (x / (2 * k)) * (x / (2 * k)); s += term; } return s; }
    SincTable(double cutoff = 0.92, double beta = 11.0) {
        t.resize((size_t)(PHASES + 1) * TAPS);
        double i0b = bessel0(beta);
        for (int p = 0; p <= PHASES; p++) {
            double frac = (double)p / PHASES;
            for (int k = 0; k < TAPS; k++) {
                double x = (double)(k - (HALF - 1)) - frac;          // tap k sits at offset k-(HALF-1) from the read position's left sample
                double s = std::fabs(x) < 1e-12 ? cutoff : std::sin(M_PI * cutoff * x) / (M_PI * x);
                double u = x / HALF; double w = std::fabs(u) >= 1 ? 0 : bessel0(beta * std::sqrt(1 - u * u)) / i0b;
                t[(size_t)p * TAPS + k] = (float)(s * w);
            }
            // each row sums to 1, so DC passes at exactly unity and frac 0 is the sample itself
            double sum = 0; for (int k = 0; k < TAPS; k++) sum += t[(size_t)p * TAPS + k];
            for (int k = 0; k < TAPS; k++) t[(size_t)p * TAPS + k] = (float)(t[(size_t)p * TAPS + k] / sum);
        }
        // frac 0 (and frac 1, the next sample) must give the sample untouched
        for (int k = 0; k < TAPS; k++) { t[k] = (k == HALF - 1) ? 1.f : 0.f; t[(size_t)PHASES * TAPS + k] = (k == HALF) ? 1.f : 0.f; }
    }
    static const SincTable& get() { static SincTable s; return s; }
};

// The steering. Works in seconds of fill so that it behaves the same at every rate.
// fill' = d - u, u = kp*e + ki*integral(e): critically damped with kp = 2*sqrt(ki); settles in about a minute.
// Slow on purpose: the fill jumps by whole blocks on both sides, and the beat between the two block sizes is slow
// enough to pass any filter; with kp 0.04 a beat of one 128-frame block (2.7 ms) moves the speed by about 50 parts
// per million, a pitch change of under a tenth of a cent, too slow and too small to hear.
struct Steer {
    double kp = 0.04, ki = 0.0004, limit = 0.002;   // limit: 2000 parts per million
    double integ = 0, smooth = -1, u = 0;
    double tau = 2.0;                               // the fill is smoothed over about a second (blocks make it jump)
    void reset() { integ = 0; smooth = -1; u = 0; }
    // fillSec: what the ring holds now, targetSec: where it should be, dt: seconds since the last call
    bool fixed = false; double fixedU = 0;          // for tests: hold the speed
    double update(double fillSec, double targetSec, double dt) {
        if (fixed) { u = fixedU; return u; }
        if (smooth < 0) smooth = fillSec;
        double a = dt / (tau + dt); smooth += a * (fillSec - smooth);
        double e = smooth - targetSec;
        double ni = integ + e * dt;
        double nu = kp * e + ki * ni;
        if (nu > limit) nu = limit; else if (nu < -limit) nu = -limit; else integ = ni;   // no wind-up at the limit
        u = nu;
        return u;
    }
};

}  // namespace al
