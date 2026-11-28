// The Kick designer's hit (kickRender in index.html), ported for the native engine (task NB-N3j).
//
// The web engine renders each kick hit once into an AudioBuffer (mono, the context's rate) and plays it with an
// AudioBufferSourceNode at every note (kickPlay: a GainNode at the note's velocity times the instrument's gain; the
// previous hit choked by setValueAtTime(v, max(w0, w - .004)) and a linear ramp to 0 at w). This file makes the same
// buffer: JavaScript's doubles, Math.exp, log, sin and tanh as V8 computes them (jsmath.h), Math.pow as V8 does it
// (the system's), every sample stored into a Float32Array (rounded to float) at the points where the app stores it,
// the click's own random numbers (seed = (seed * 1103515245 + 12345) & 0x7fffffff in JavaScript's doubles: the
// product is rounded before the 32-bit and).
#pragma once
#include <cmath>
#include <string>
#include <vector>
#include "jsmath.h"

namespace al {
namespace kick {

struct KickParams {
    double tune = 33, start = 2400, sweep = 0.045, bend = 82, len = 0.17, tail = 34, click = 55, drive = 12;
    std::string ctype = "tick";
    bool kt = false;
    double gain = 0.9;
};

inline double hz(double n) { return 440 * js::pow(2, (n - 69) / 12); }
inline double clampJ(double v, double a, double b) { return js::max(a, js::min(b, v)); }   // clamp=(v,a,b)=>Math.max(a,Math.min(b,v))

// kickRender(I, sr, tr)
inline std::vector<float> render(const KickParams& I, double sr, double tr = 0) {
    const size_t n = (size_t)std::ceil(I.len * sr) + 8;
    std::vector<float> d(n, 0.f);
    const double fE = hz(I.tune + tr), fS = js::max(fE * 1.02, I.start * js::pow(2, tr / 12)), lE = js::log(fE), lS = js::log(fS);
    const double cp = 1 + I.bend / 100 * 5, att = .0005, hold = I.len * (.04 + .22 * I.tail / 100), tp = 2.8 - 2.4 * I.tail / 100,
                 fade = js::min(.006, I.len * .05), TAU = 2 * js::PI;
    double ph = 0;
    for (size_t i = 0; i < n; i++) {
        const double t = (double)i / sr, x = js::min(1, t / I.sweep), f = js::exp(lE + (lS - lE) * js::pow(1 - x, cp));
        ph += TAU * f / sr;
        if (ph > TAU) ph -= TAU;
        double a = t < att ? t / att : 1;
        const double y = clampJ((t - hold) / js::max(1e-4, I.len - hold), 0, 1);
        a *= js::pow(1 - y, tp);
        if (t > I.len - fade) a *= js::max(0, (I.len - t) / fade);
        d[i] = (float)(js::sin(ph) * a);
    }
    const double cl = I.click / 100 * .9;
    const std::string& ct = I.ctype.empty() ? std::string("tick") : I.ctype;
    if (cl > 0 && ct != "off") {
        double xp = 0, yp = 0, lp = 0;
        const size_t m = (size_t)js::min((double)n, std::ceil(sr * .06));
        double seed = 12345;
        auto rnd = [&]() { seed = (double)(js::toInt32(seed * 1103515245 + 12345) & 0x7fffffff); return seed / 0x3fffffff - 1; };
        for (size_t i = 0; i < m; i++) {
            const double t = (double)i / sr, nz = rnd();
            double s = 0;
            if (ct == "tick") { yp = .92 * (yp + nz - xp); xp = nz; s = js::sin(TAU * 3400 * t) * js::exp(-t / .0012) * .9 + yp * js::exp(-t / .0018) * .6; }
            else if (ct == "snap") { yp = .8 * (yp + nz - xp); xp = nz; lp += .45 * (yp - lp); s = lp * js::exp(-t / .007) * 1.4; }
            else if (ct == "knock") { s = js::sin(TAU * (260 - 1200 * t) * t) * js::exp(-t / .018) * .9; }
            else { yp = .97 * (yp + nz - xp); xp = nz; s = yp * js::exp(-t / .012) * .5; }
            d[i] = (float)((double)d[i] + s * cl);
        }
    }
    const double g = 1 + I.drive / 100 * 14, tg = js::tanh(g);
    double pk = 0;
    for (size_t i = 0; i < n; i++) { d[i] = (float)(js::tanh((double)d[i] * g) / tg); pk = js::max(pk, std::fabs((double)d[i])); }
    const double nm = pk > 0 ? .95 / pk : 1;
    for (size_t i = 0; i < n; i++) d[i] = (float)((double)d[i] * nm);
    return d;
}

}  // namespace kick
}  // namespace al
