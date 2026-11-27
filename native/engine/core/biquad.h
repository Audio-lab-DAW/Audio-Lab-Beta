// Chromium's BiquadFilterNode, ported for the native engine (task NB-N3e).
//
// The app's Pro EQ (mkEQ2 in index.html) is a chain of the browser's own BiquadFilterNodes, so its sound is
// Chromium's arithmetic, not JavaScript's. This is a statement-by-statement port of Chromium 158.0.8127.36
// (identical on main, 27 Nov 2026):
//   third_party/blink/renderer/platform/audio/biquad.cc          the filter and its coefficient formulas
//   third_party/blink/renderer/modules/webaudio/biquad_filter_handler.cc   when coefficients are worked out
//   third_party/fdlibm (native/third_party/fdlibm)                the sin, cos and exp the formulas call
// What decides the bits, each one a line below:
//   - the parameters are AudioParams: frequency, Q and gain are stored as float, then widened to double;
//   - pow10() is fdlibm::expf(x * ln10): the argument and the result are rounded to float;
//   - coefficients are double; on Linux and Windows the state is double but every output is rounded to float
//     and that float is what is fed back (y1 = y); on the Mac Chromium calls Accelerate's vDSP_deq22D on
//     doubles in slices of up to 1024 frames and keeps the double output as the state. The engine does the same
//     per platform (on the Mac it calls the same vDSP function), so each matches its own platform's browser;
//   - coefficients are worked out at the first quantum and again only in a quantum where a parameter's value
//     changed (fixed values; automation of the EQ's parameters is not ported yet);
//   - Chromium's "flush denormal" at the end of a call converts the double state through float (a no-op on
//     values the loop already rounded to float).
#pragma once
#include <cfloat>
#include <cmath>
#include <complex>
#include <vector>
#include "../../third_party/fdlibm/ieee754.h"
#if defined(__APPLE__)
#include <Accelerate/Accelerate.h>
#endif

namespace al {
namespace cr {

constexpr double kPi = 3.141592653589793;     // std::numbers::pi
constexpr double kLn10 = 2.302585092994046;   // std::numbers::ln10
inline double pow10f(double x) { return fdlibm::expf((float)(x * kLn10)); }
inline double clamp01(double v) { return v < 0.0 ? 0.0 : (v > 1.0 ? 1.0 : v); }

enum class BiquadType { Lowpass, Highpass, Bandpass, Lowshelf, Highshelf, Peaking, Notch, Allpass };
inline bool biquadTypeOf(const std::string& s, BiquadType& t) {
    static const char* N[] = {"lowpass", "highpass", "bandpass", "lowshelf", "highshelf", "peaking", "notch", "allpass"};
    for (int i = 0; i < 8; i++) if (s == N[i]) { t = (BiquadType)i; return true; }
    return false;
}

// blink::Biquad, one channel, fixed coefficients (index 0).
class Biquad {
public:
    double b0 = 1, b1 = 0, b2 = 0, a1 = 0, a2 = 0;
    Biquad() { reset(); }
    void reset() {
        x1_ = x2_ = y1_ = y2_ = 0;
#if defined(__APPLE__)
        in_[0] = in_[1] = 0; out_[0] = out_[1] = 0;
#endif
    }
    void setNormalized(double nb0, double nb1, double nb2, double na0, double na1, double na2) {
        double inv = 1 / na0;
        b0 = nb0 * inv; b1 = nb1 * inv; b2 = nb2 * inv; a1 = na1 * inv; a2 = na2 * inv;
    }
    void setLowpass(double cutoff, double resonance) {
        cutoff = clamp01(cutoff);
        if (cutoff == 1) setNormalized(1, 0, 0, 1, 0, 0);
        else if (cutoff > 0) {
            resonance = pow10f(resonance / 20);
            double theta = kPi * cutoff;
            double alpha = fdlibm::sin(theta) / (2 * resonance);
            double cosw = fdlibm::cos(theta);
            double beta = (1 - cosw) / 2;
            double nb0 = beta, nb1 = 2 * beta, nb2 = beta;
            double na0 = 1 + alpha, na1 = -2 * cosw, na2 = 1 - alpha;
            setNormalized(nb0, nb1, nb2, na0, na1, na2);
        } else setNormalized(0, 0, 0, 1, 0, 0);
    }
    void setHighpass(double cutoff, double resonance) {
        cutoff = clamp01(cutoff);
        if (cutoff == 1) setNormalized(0, 0, 0, 1, 0, 0);
        else if (cutoff > 0) {
            resonance = pow10f(resonance / 20);
            double theta = kPi * cutoff;
            double alpha = fdlibm::sin(theta) / (2 * resonance);
            double cosw = fdlibm::cos(theta);
            double beta = (1 + cosw) / 2;
            double nb0 = beta, nb1 = -2 * beta, nb2 = beta;
            double na0 = 1 + alpha, na1 = -2 * cosw, na2 = 1 - alpha;
            setNormalized(nb0, nb1, nb2, na0, na1, na2);
        } else setNormalized(1, 0, 0, 1, 0, 0);
    }
    void setLowShelf(double frequency, double dbGain) {
        frequency = clamp01(frequency);
        double a = pow10f(dbGain / 40);
        if (frequency == 1) setNormalized(a * a, 0, 0, 1, 0, 0);
        else if (frequency > 0) {
            double w0 = kPi * frequency;
            double s = 1;
            double alpha = 0.5 * fdlibm::sin(w0) * std::sqrt((a + 1 / a) * (1 / s - 1) + 2);
            double k = fdlibm::cos(w0);
            double k2 = 2 * std::sqrt(a) * alpha;
            double ap1 = a + 1, am1 = a - 1;
            double nb0 = a * (ap1 - am1 * k + k2);
            double nb1 = 2 * a * (am1 - ap1 * k);
            double nb2 = a * (ap1 - am1 * k - k2);
            double na0 = ap1 + am1 * k + k2;
            double na1 = -2 * (am1 + ap1 * k);
            double na2 = ap1 + am1 * k - k2;
            setNormalized(nb0, nb1, nb2, na0, na1, na2);
        } else setNormalized(1, 0, 0, 1, 0, 0);
    }
    void setHighShelf(double frequency, double dbGain) {
        frequency = clamp01(frequency);
        double a = pow10f(dbGain / 40);
        if (frequency == 1) setNormalized(1, 0, 0, 1, 0, 0);
        else if (frequency > 0) {
            double w0 = kPi * frequency;
            double s = 1;
            double alpha = 0.5 * fdlibm::sin(w0) * std::sqrt((a + 1 / a) * (1 / s - 1) + 2);
            double k = fdlibm::cos(w0);
            double k2 = 2 * std::sqrt(a) * alpha;
            double ap1 = a + 1, am1 = a - 1;
            double nb0 = a * (ap1 + am1 * k + k2);
            double nb1 = -2 * a * (am1 + ap1 * k);
            double nb2 = a * (ap1 + am1 * k - k2);
            double na0 = ap1 - am1 * k + k2;
            double na1 = 2 * (am1 - ap1 * k);
            double na2 = ap1 - am1 * k - k2;
            setNormalized(nb0, nb1, nb2, na0, na1, na2);
        } else setNormalized(a * a, 0, 0, 1, 0, 0);
    }
    void setPeaking(double frequency, double q, double dbGain) {
        frequency = clamp01(frequency);
        q = std::max(0.0, q);
        double a = pow10f(dbGain / 40);
        if (frequency > 0 && frequency < 1) {
            if (q > 0) {
                double w0 = kPi * frequency;
                double alpha = fdlibm::sin(w0) / (2 * q);
                double k = fdlibm::cos(w0);
                double nb0 = 1 + alpha * a, nb1 = -2 * k, nb2 = 1 - alpha * a;
                double na0 = 1 + alpha / a, na1 = -2 * k, na2 = 1 - alpha / a;
                setNormalized(nb0, nb1, nb2, na0, na1, na2);
            } else setNormalized(a * a, 0, 0, 1, 0, 0);
        } else setNormalized(1, 0, 0, 1, 0, 0);
    }
    void setAllpass(double frequency, double q) {
        frequency = clamp01(frequency);
        q = std::max(0.0, q);
        if (frequency > 0 && frequency < 1) {
            if (q > 0) {
                double w0 = kPi * frequency;
                double alpha = fdlibm::sin(w0) / (2 * q);
                double k = fdlibm::cos(w0);
                setNormalized(1 - alpha, -2 * k, 1 + alpha, 1 + alpha, -2 * k, 1 - alpha);
            } else setNormalized(-1, 0, 0, 1, 0, 0);
        } else setNormalized(1, 0, 0, 1, 0, 0);
    }
    void setNotch(double frequency, double q) {
        frequency = clamp01(frequency);
        q = std::max(0.0, q);
        if (frequency > 0 && frequency < 1) {
            if (q > 0) {
                double w0 = kPi * frequency;
                double alpha = fdlibm::sin(w0) / (2 * q);
                double k = fdlibm::cos(w0);
                setNormalized(1, -2 * k, 1, 1 + alpha, -2 * k, 1 - alpha);
            } else setNormalized(0, 0, 0, 1, 0, 0);
        } else setNormalized(1, 0, 0, 1, 0, 0);
    }
    void setBandpass(double frequency, double q) {
        frequency = std::max(0.0, frequency);
        q = std::max(0.0, q);
        if (frequency > 0 && frequency < 1) {
            double w0 = kPi * frequency;
            if (q > 0) {
                double alpha = fdlibm::sin(w0) / (2 * q);
                double k = fdlibm::cos(w0);
                setNormalized(alpha, 0, -alpha, 1 + alpha, -2 * k, 1 - alpha);
            } else setNormalized(1, 0, 0, 1, 0, 0);
        } else setNormalized(0, 0, 0, 1, 0, 0);
    }
    // SetBiquadParams in biquad_filter_handler.cc
    void setParams(BiquadType t, double freq, double q, double gain) {
        switch (t) {
            case BiquadType::Lowpass: setLowpass(freq, q); return;
            case BiquadType::Highpass: setHighpass(freq, q); return;
            case BiquadType::Bandpass: setBandpass(freq, q); return;
            case BiquadType::Lowshelf: setLowShelf(freq, gain); return;
            case BiquadType::Highshelf: setHighShelf(freq, gain); return;
            case BiquadType::Peaking: setPeaking(freq, q, gain); return;
            case BiquadType::Notch: setNotch(freq, q); return;
            case BiquadType::Allpass: setAllpass(freq, q); return;
        }
    }

    // Biquad::Process, fixed coefficients. n <= kMaxQuantum.
    void process(const float* src, float* dst, int n) {
#if defined(__APPLE__)
        double coef[5] = {b0, b1, b2, a1, a2};
        int done = 0;
        while (done < n) {
            const int m = std::min(n - done, kSlice);
            for (int i = 0; i < m; i++) in_[i + 2] = src[done + i];
            vDSP_deq22D(in_, 1, coef, out_, 1, (vDSP_Length)m);
            in_[0] = in_[m]; in_[1] = in_[m + 1];
            out_[0] = out_[m]; out_[1] = out_[m + 1];
            for (int i = 0; i < m; i++) dst[done + i] = (float)out_[i + 2];
            done += m;
        }
#else
        double x1 = x1_, x2 = x2_, y1 = y1_, y2 = y2_;
        const double c0 = b0, c1 = b1, c2 = b2, d1 = a1, d2 = a2;
        for (int k = 0; k < n; ++k) {
            float x = src[k];
            float y = c0 * x + c1 * x1 + c2 * x2 - d1 * y1 - d2 * y2;
            dst[k] = y;
            x2 = x1; x1 = x; y2 = y1; y1 = y;
        }
        // DenormalDisabler::FlushDenormalFloatToZero(float): with hardware flushing it returns its float argument
        x1_ = (float)x1; x2_ = (float)x2; y1_ = (float)y1; y2_ = (float)y2;
#endif
    }

    // Biquad::GetFrequencyResponse, for the EQ's auto gain (frequency normalised to Nyquist). Complex
    // arithmetic written out as libc++ (Chromium's C++ library) does it, so it does not depend on the
    // compiler's own complex division.
    void response(const float* f, float* mag, int n) const {
        for (int k = 0; k < n; ++k) {
            if (f[k] < 0 || f[k] > 1) { mag[k] = NAN; continue; }
            double omega = -kPi * f[k];
            double zr = fdlibm::cos(omega), zi = fdlibm::sin(omega);
            // numerator = b0 + (b1 + b2 * z) * z
            double tr = b1 + b2 * zr, ti = b2 * zi;
            double nr, ni; cmul(tr, ti, zr, zi, nr, ni); nr = b0 + nr;
            // denominator = complex(1, 0) + (a1 + a2 * z) * z
            double ur = a1 + a2 * zr, ui = a2 * zi;
            double dr, di; cmul(ur, ui, zr, zi, dr, di); dr = 1 + dr; di = 0 + di;
            double rr, ri; cdiv(nr, ni, dr, di, rr, ri);
            mag[k] = (float)std::hypot(rr, ri);
        }
    }

private:
    static void cmul(double a, double b, double c, double d, double& x, double& y) {
        double ac = a * c, bd = b * d, ad = a * d, bc = b * c;
        x = ac - bd; y = ad + bc;
    }
    static void cdiv(double a, double b, double c, double d, double& x, double& y) {
        int ilogbw = 0;
        double logbw = std::logb(std::fmax(std::fabs(c), std::fabs(d)));
        if (std::isfinite(logbw)) { ilogbw = (int)logbw; c = std::scalbn(c, -ilogbw); d = std::scalbn(d, -ilogbw); }
        double denom = c * c + d * d;
        x = std::scalbn((a * c + b * d) / denom, -ilogbw);
        y = std::scalbn((b * c - a * d) / denom, -ilogbw);
    }
    double x1_, x2_, y1_, y2_;
#if defined(__APPLE__)
    static constexpr int kSlice = 1024;   // kBiquadBufferSize
    double in_[kSlice + 2], out_[kSlice + 2];
#endif
};

// One BiquadFilterNode: one Biquad per channel, its AudioParams' values as floats, coefficients worked out at the
// first quantum and whenever a value changed (BiquadFilterHandler::Process, the fixed-value branch).
class BiquadNode {
public:
    BiquadType type = BiquadType::Lowpass;
    float frequency = 350.f, Q = 1.f, gain = 0.f, detune = 0.f;
    explicit BiquadNode(double sampleRate) : sr_((float)sampleRate), nyquist_(0.5 * (float)sampleRate) {}
    // AudioParam.value = v: a float, clamped to the parameter's range when read (FinalValue)
    void setType(BiquadType t) { if (t == type) return; type = t; for (auto& b : ch_) b.reset(); justReset_ = true; }
    void setFrequency(double v) { frequency = (float)v; }
    void setQ(double v) { Q = (float)v; }
    void setGain(double v) { gain = (float)v; }
    void process(const float* const* in, float* const* out, int channels, int n) {
        if ((int)ch_.size() != channels) { ch_.assign(channels, Biquad()); justReset_ = true; }   // channel count change: Uninitialize + Initialize
        const float f = std::min(std::max(frequency, 0.f), (float)nyquist_), q = Q, g = std::min(gain, kGainMax), dt = detune;
        bool dirty = false;
        if (justReset_) { dirty = true; justReset_ = false; pf_ = NAN; pq_ = NAN; pg_ = NAN; pd_ = NAN; }
        else if (pf_ != f || pq_ != q || pg_ != g || pd_ != dt) { dirty = true; pf_ = f; pq_ = q; pg_ = g; pd_ = dt; }
        if (dirty) {
            double nf = (double)f / nyquist_;
            if (dt) nf = nf * std::exp2(dt / 1200);
            for (auto& b : ch_) b.setParams(type, nf, q, g);
        }
        for (int c = 0; c < channels; c++) ch_[c].process(in[c], out[c], n);
    }
    // getFrequencyResponse(frequencyHz -> magnitude), from the parameters' current values
    void response(const float* hz, float* mag, int n) const {
        Biquad k;
        double nf = (double)frequency / nyquist_;
        if (detune) nf = nf * std::exp2(detune / 1200);
        k.setParams(type, nf, Q, gain);
        std::vector<float> fr(n);
        for (int i = 0; i < n; i++) fr[i] = (float)(hz[i] / nyquist_);
        k.response(fr.data(), mag, n);
    }

private:
    static constexpr float kGainMax = 1541.27519f;   // 40 * log10(FLT_MAX), the gain parameter's maximum
    float sr_;
    double nyquist_;
    std::vector<Biquad> ch_;
    bool justReset_ = true;
    float pf_ = NAN, pq_ = NAN, pg_ = NAN, pd_ = NAN;
};

}  // namespace cr
}  // namespace al
