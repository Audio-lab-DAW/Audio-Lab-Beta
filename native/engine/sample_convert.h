// Float to the device's own sample format (task NB-N1). Used when the device runs an integer format that the
// system does not mix (exclusive, "integer mode"): then the engine itself writes the bytes that go to the DAC.
// Rule: value * 2^(bits-1), rounded to nearest, clamped. A 24-bit sample that came from a 24-bit file goes
// through unchanged. 16-bit can be dithered (TPDF, seeded, so a test gives the same bytes twice).
#pragma once
#include <cmath>
#include <cstdint>
#include <cstring>

namespace al {

struct SampleFormat {
    bool isFloat = true;
    int bits = 32;            // valid bits
    int bytes = 4;            // bytes per sample in the buffer
    bool alignedHigh = true;  // valid bits sit at the top of the container (24 in 32)
    bool bigEndian = false;
};

struct Dither {
    uint32_t s = 0x1234abcdu;
    double next() { s = s * 1664525u + 1013904223u; return (double)(s >> 8) / 16777216.0; }   // 0..1
    double tpdf() { double a = next(); double b = next(); return a - b; }                 // -1..1, triangular
};

inline int32_t floatToInt(float v, int bits, Dither* d) {
    double scale = (double)((int64_t)1 << (bits - 1));
    double x = (double)v * scale;
    if (d) x += d->tpdf();
    double r = std::floor(x + 0.5);
    double hi = scale - 1, lo = -scale;
    if (r > hi) r = hi; else if (r < lo) r = lo;
    if (!(r == r)) r = 0;
    return (int32_t)r;
}

// Writes n samples of one channel into an interleaved buffer: dst points at this channel's first sample,
// stride is the size of one frame in bytes.
inline void writeChannel(const float* src, int n, uint8_t* dst, int stride, const SampleFormat& f, Dither* d) {
    if (f.isFloat) { for (int i = 0; i < n; i++) memcpy(dst + (size_t)i * stride, &src[i], 4); return; }
    for (int i = 0; i < n; i++) {
        int32_t s = floatToInt(src[i], f.bits, d);
        uint32_t u = (uint32_t)s;
        int shift = f.alignedHigh ? f.bytes * 8 - f.bits : 0;
        if (shift > 0) u <<= shift;
        uint8_t* p = dst + (size_t)i * stride;
        for (int b = 0; b < f.bytes; b++) p[f.bigEndian ? f.bytes - 1 - b : b] = (uint8_t)(u >> (8 * b));
    }
}

}  // namespace al
