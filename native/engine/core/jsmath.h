// JavaScript number semantics for ported worklet code (task NB-N3a).
// The web engine's devices are JavaScript: every value is a double, arrays of samples are float. A port that
// must give the same bits keeps the same operations in the same order; these helpers are the few places where
// JavaScript and C++ differ (Math.max with NaN and signed zero, Math.round, the >> operator, % on doubles).
// Build with -ffp-contract=off (no fused multiply-add).
#pragma once
#include <cmath>
#include <cstdint>
#ifndef LIBC_NAMESPACE
#define LIBC_NAMESPACE __llvm_libc_al
#endif
#ifndef AL_MATH_SYSTEM
#include "shared/math/cos.h"  // native/third_party/llvm-libc (the include path is set by CMake)
#include "shared/math/exp.h"
#include "shared/math/log.h"
#include "shared/math/log10.h"
#include "shared/math/sin.h"
#endif

namespace al {
namespace js {

constexpr double PI = 3.141592653589793;
constexpr double TAU = PI * 2;

// Math.max / Math.min: NaN wins, +0 is larger than -0.
inline double max(double a, double b) {
    if (std::isnan(a) || std::isnan(b)) return NAN;
    if (a == b) return (a == 0 && std::signbit(a)) ? b : a;
    return a > b ? a : b;
}
inline double max(double a, double b, double c) { return max(max(a, b), c); }
inline double min(double a, double b) {
    if (std::isnan(a) || std::isnan(b)) return NAN;
    if (a == b) return (a == 0 && !std::signbit(a)) ? b : a;
    return a < b ? a : b;
}
inline double abs(double x) { return std::fabs(x); }

// Math.round: nearest whole number, halves up, sign of zero kept.
inline double round(double x) {
    if (!std::isfinite(x)) return x;
    double r = std::floor(x);
    if (x - r >= 0.5) r += 1.0;
    if (r == 0.0 && (x < 0.0 || std::signbit(x))) return -0.0;
    return r;
}
inline double ceil(double x) { return std::ceil(x); }

// ToInt32 (for >>, |0).
inline int32_t toInt32(double x) {
    if (!std::isfinite(x)) return 0;
    double t = std::trunc(x);
    double m = std::fmod(t, 4294967296.0);
    if (m < 0) m += 4294967296.0;
    uint32_t u = (uint32_t)m;
    return (int32_t)u;
}
inline double shr(double x, int s) { return (double)(toInt32(x) >> (s & 31)); }

// The maths functions JavaScript calls. Every device calls these, never std::, so the engine has one
// implementation of its own on every system (found in task NB-N3c, measured against Chromium 158):
//   Math.sin, cos, exp, log10: V8 takes them from LLVM's libc, correctly rounded. glibc differs on about 0.15 %
//     of arguments, Node's older V8 on about 3 %. The engine carries the same LLVM functions
//     (native/third_party/llvm-libc), so they give the browser's bits on Linux, macOS and Windows alike.
//   Math.pow: V8 handles y == 2 (x*x) and y == 0.5 (sqrt(x+0)) itself and otherwise calls the system's own pow
//     (flag use_std_math_pow). So the engine calls std::pow too: Apple's on the Mac, as the desktop app does there.
// AL_MATH_SYSTEM (a test switch) uses the system library for everything, to show what the vendored code changes.
#ifdef AL_MATH_SYSTEM
inline double sin(double x) { return std::sin(x); }
inline double cos(double x) { return std::cos(x); }
inline double exp(double x) { return std::exp(x); }
inline double log10(double x) { return std::log10(x); }
#else
inline double sin(double x) { return LIBC_NAMESPACE::shared::sin(x); }
inline double cos(double x) { return LIBC_NAMESPACE::shared::cos(x); }
inline double exp(double x) { return LIBC_NAMESPACE::shared::exp(x); }
inline double log10(double x) { return LIBC_NAMESPACE::shared::log10(x); }
#endif
// Math.log: LLVM's libc too (task NB-N3j: V8's ieee754::log; glibc's log differs from the browser's on 10 of 300,000
// arguments of the Kick's kind, Chromium's fdlibm on 3,498). Math.tanh: V8 calls the system's own (std::tanh): 0 of
// 300,000 differ on Linux, Chromium's fdlibm::tanh differs on 101 (so the system's, Apple's on the Mac).
#ifdef AL_MATH_SYSTEM
inline double log(double x) { return std::log(x); }
#else
inline double log(double x) { return LIBC_NAMESPACE::shared::log(x); }
#endif
inline double tanh(double x) { return std::tanh(x); }
inline double pow(double x, double y) {
    if (std::isnan(y)) return NAN;
    if (std::isinf(y) && (x == 1 || x == -1)) return NAN;
    if (std::isnan(x)) x = NAN;
    if (y == 2) return x * x;
    if (y == 0.5) return std::isinf(x) ? INFINITY : std::sqrt(x + 0);
    return std::pow(x, y);
}

// The worklet bundle's own helpers (WLSRC in index.html):
//   dB = x => Math.pow(10, x/20),  lg = x => 20*Math.log10(Math.max(1e-9, x))
inline double dB(double x) { return js::pow(10.0, x / 20); }
inline double lg(double x) { return 20 * js::log10(max(1e-9, x)); }

// Float32Array store: round to float.
inline float f32(double v) { return (float)v; }

}  // namespace js

// The worklet bundle replaces Math.random with this seeded generator (wlLoad in index.html). One per audio
// context: every worklet of one render shares it.
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

}  // namespace al
