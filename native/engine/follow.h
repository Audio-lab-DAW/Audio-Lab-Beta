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

// Kaiser-windowed sinc, 128 taps (beta 13), cut off at the top frequency itself, 4096 phases, linear between
// phases (task NB-R5, review C3; it was 48 taps cut at 0.92, which took 4.2 dB off 20 kHz at 44.1 kHz). Flat to
// 20 kHz at 44.1 kHz and above (level within 0.001 dB, error against the ideal about -120 dB, measured in the
// selftest); 21 kHz at 44.1 kHz within 0.04 dB. Cut at the top frequency, the kernel at a whole sample is the
// sample itself, so the response changes smoothly as the read position slips past a sample (the old table forced
// that row and jumped). The design is in fractions of the rate, so one table serves every rate.
// Cost: 128 multiply-adds per channel per sample (the selftest measures it).
struct SincTable {
    static constexpr int HALF = 64, TAPS = 2 * HALF, PHASES = 4096;
    std::vector<float> t;   // (PHASES + 1) rows of TAPS: row p is the kernel for a fraction p / PHASES
    static double bessel0(double x) { double s = 1, term = 1; for (int k = 1; k < 40; k++) { term *= (x / (2 * k)) * (x / (2 * k)); s += term; } return s; }
    SincTable(double cutoff = 1.0, double beta = 13.0) {
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
        // frac 0 (and frac 1, the next sample): the sample untouched. With the cut at the top frequency this is what the
        // kernel gives anyway (sin(pi k) is 0 at whole k) up to rounding near 1e-17; set exactly
        for (int k = 0; k < TAPS; k++) { t[k] = (k == HALF - 1) ? 1.f : 0.f; t[(size_t)PHASES * TAPS + k] = (k == HALF) ? 1.f : 0.f; }
    }
    static const SincTable& get() { static SincTable s; return s; }
};

// The steering. Works in seconds of fill so that it behaves the same at every rate.
// fill' = d - u, u = kp*e + ki*integral(e): natural frequency sqrt(ki), critically damped with kp = 2*sqrt(ki).
// Task NB-R5 (review C4): kp 0.1, ki 0.0025 (0.05 rad/s): within 1 % of the sender's clock in about two minutes
// (the old 0.04 / 0.0004 needed more than five, and with a sender 1000 ppm off the fill stood 19 ms over its
// target after one). The speed's wobble from blocks arriving in bursts (pauses of 25 ms each second, as the
// shell's feeder measured under load) stays 5 to 15 parts per million: under three hundredths of a cent, far too
// small and slow to hear.
struct Steer {
    double kp = 0.1, ki = 0.0025, limit = 0.002;    // limit: 2000 parts per million
    double integ = 0, smooth = -1, u = 0;
    // task NB-R5: acquisition. For the first acquireSec after a reset the loop runs acquireX times faster (kp x, ki x^2),
    // so a sender far off (1000 ppm) is caught before the fill sinks far (about 2.5 ms instead of 7); then it hands over
    // to the slow loop without a jump in the speed (the integral is rescaled so kp*e + ki*integral stays the same).
    double acquireSec = 30, acquireX = 3, elapsed = 0; bool acquiring = true;
    double tau = 2.0;                               // the fill is smoothed over about a second (blocks make it jump)
    void reset() { integ = 0; smooth = -1; u = 0; elapsed = 0; acquiring = true; }
    void holdIntegral() { smooth = -1; }   // task NB-R5: after a jump in the fill (a drop), measure the fill afresh but keep the learned speed
    // fillSec: what the ring holds now, targetSec: where it should be, dt: seconds since the last call
    bool fixed = false; double fixedU = 0;          // for tests: hold the speed
    double update(double fillSec, double targetSec, double dt) {
        if (fixed) { u = fixedU; return u; }
        if (smooth < 0) smooth = fillSec;
        double a = dt / (tau + dt); smooth += a * (fillSec - smooth);
        double e = smooth - targetSec;
        elapsed += dt;
        if (acquiring && elapsed >= acquireSec) { acquiring = false; integ *= acquireX * acquireX; }   // ki drops by x^2: the integral grows by x^2, u unchanged
        const double g = acquiring ? acquireX : 1.0, kpe = kp * g, kie = ki * g * g;
        double ni = integ + e * dt;
        double nu = kpe * e + kie * ni;
        if (nu > limit) nu = limit; else if (nu < -limit) nu = -limit; else integ = ni;   // no wind-up at the limit
        u = nu;
        return u;
    }
};

}  // namespace al
