// Chromium's GainNode and BiquadFilterNode with automated parameters (task NB-N3j).
//
// The clips' envelopes and the instruments move these nodes' values over time (timeline.h). Ported from Chromium
// 158.0.8127.36: gain_handler.cc (Process: the sample-accurate path when the gain has events in this quantum, else
// the quantum's value, 0 a silent bus, 1 a copy), audio_bus.cc (CopyWithGainFrom, CopyWithSampleAccurateGainValues-
// From), biquad_filter_handler.cc (Process: per-frame coefficients when a parameter changes inside the quantum, one
// set when it is constant there, the fixed values otherwise) and biquad.cc (Process: the per-frame loop with double
// coefficients and float state; on the Mac the fixed path is vDSP_deq22D with its state handed over from the
// per-frame path, as Chromium does).
#pragma once
#include <algorithm>
#include <cfloat>
#include <cmath>
#include <vector>
#include "biquad.h"
#include "timeline.h"
#if defined(__APPLE__)
#include <Accelerate/Accelerate.h>
#endif

namespace al {
namespace cr {

class GainNodeA {
public:
    ParamTimeline gain{1.f, -FLT_MAX, FLT_MAX};
    GainNodeA(double sr, unsigned Q) : sr_(sr), Q_(Q), g_(Q) { gain.setSampleRate(sr); }
    // One quantum at frame qs: in may equal out. inSilent: the input is a silent bus (or not connected). Returns
    // whether the output is non-silent.
    bool process(size_t qs, const float* const* in, bool inSilent, float* const* out, unsigned nch, size_t n) {
        const bool sa = gain.hasSampleAccurateValues(qs, sr_, Q_);
        if (sa && gain.audioRate()) {
            gain.sampleAccurate(qs, g_.data(), n, sr_, Q_);
            if (inSilent) { zero(out, nch, n); return false; }
            for (unsigned c = 0; c < nch; c++) for (size_t i = 0; i < n; i++) out[c][i] = in[c][i] * g_[i];   // Vmul
            return true;
        }
        const float g = gain.finalValue(qs, sr_, Q_);
        if (inSilent) { zero(out, nch, n); return false; }
        if (g == 0) { zero(out, nch, n); return false; }
        if (g == 1) { for (unsigned c = 0; c < nch; c++) if (out[c] != in[c]) std::copy(in[c], in[c] + n, out[c]); return true; }
        for (unsigned c = 0; c < nch; c++) for (size_t i = 0; i < n; i++) out[c][i] = g * in[c][i];   // Vsmul
        return true;
    }
    // ProcessOnlyAudioParams: a node skipped on silence still moves its timeline
    void advance(size_t qs, size_t n) { gain.sampleAccurate(qs, g_.data(), n, sr_, Q_); }

private:
    static void zero(float* const* out, unsigned nch, size_t n) { for (unsigned c = 0; c < nch; c++) std::fill(out[c], out[c] + n, 0.f); }
    double sr_;
    unsigned Q_;
    std::vector<float> g_;
};

class BiquadNodeA {
public:
    BiquadType type = BiquadType::Lowpass;
    ParamTimeline frequency, Q, gain, detune;
    BiquadNodeA(double sr, unsigned quantum)
        : frequency(350.f, 0.f, (float)(0.5 * (float)sr)), Q(1.f, -FLT_MAX, FLT_MAX), gain(0.f, -FLT_MAX, 1541.27519f),
          detune(0.f, -153600.f, 153600.f), sr_(sr), nyq_(0.5 * (float)sr), Qf_(quantum), f_(quantum), q_(quantum), g_(quantum), d_(quantum) {
        for (auto* p : {&frequency, &Q, &gain, &detune}) p->setSampleRate(sr);
        // the frequency's maximum is the Nyquist frequency as a float (BiquadFilterNode::Create: sample_rate / 2)
    }
    void process(size_t qs, const float* const* in, float* const* out, unsigned nch, size_t n) {
        if (ch_.size() != nch) { ch_.assign(nch, State()); justReset_ = true; }
        bool dirty = false, sa = false, aRate = false;
        if (frequency.hasSampleAccurateValues(qs, sr_, Qf_) || Q.hasSampleAccurateValues(qs, sr_, Qf_) ||
            gain.hasSampleAccurateValues(qs, sr_, Qf_) || detune.hasSampleAccurateValues(qs, sr_, Qf_)) {
            dirty = true; sa = true;
            aRate = frequency.audioRate() || Q.audioRate() || gain.audioRate() || detune.audioRate();
        } else if (justReset_) {
            pf_ = pq_ = pg_ = pd_ = NAN; dirty = true; justReset_ = false;
        } else {
            const float a = frequency.finalValue(qs, sr_, Qf_), b = Q.finalValue(qs, sr_, Qf_), c = gain.finalValue(qs, sr_, Qf_), d = detune.finalValue(qs, sr_, Qf_);
            if (pf_ != a || pq_ != b || pg_ != c || pd_ != d) { dirty = true; pf_ = a; pq_ = b; pg_ = c; pd_ = d; }
        }
        if (dirty) {
            if (sa && aRate) {
                frequency.sampleAccurate(qs, f_.data(), n, sr_, Qf_);
                Q.sampleAccurate(qs, q_.data(), n, sr_, Qf_);
                gain.sampleAccurate(qs, g_.data(), n, sr_, Qf_);
                detune.sampleAccurate(qs, d_.data(), n, sr_, Qf_);
                const bool constant = isConst(f_, n) && isConst(q_, n) && isConst(g_, n) && isConst(d_, n);
                const size_t need = constant ? 1 : n;
                for (auto& s : ch_) {
                    s.sa = need > 1;
                    s.resize(Qf_);
                    for (size_t k = 0; k < need; ++k) setCoef(s, k, norm(f_[k], d_[k]), q_[k], g_[k]);
                }
            } else {
                f_[0] = frequency.finalValue(qs, sr_, Qf_); q_[0] = Q.finalValue(qs, sr_, Qf_);
                g_[0] = gain.finalValue(qs, sr_, Qf_); d_[0] = detune.finalValue(qs, sr_, Qf_);
                for (auto& s : ch_) { s.sa = false; s.resize(Qf_); setCoef(s, 0, norm(f_[0], d_[0]), q_[0], g_[0]); }
            }
        }
        for (unsigned c = 0; c < nch; c++) run(ch_[c], in[c], out[c], n);
    }

private:
    struct State {
        std::vector<double> b0, b1, b2, a1, a2;
        bool sa = false;
        double x1 = 0, x2 = 0, y1 = 0, y2 = 0;
#if defined(__APPLE__)
        double in[1024 + 2] = {0}, out[1024 + 2] = {0};
#endif
        void resize(size_t n) { if (b0.size() < n) { b0.resize(n); b1.resize(n); b2.resize(n); a1.resize(n); a2.resize(n); } }
    };
    static bool isConst(const std::vector<float>& v, size_t n) {   // audio_utilities::HasConstantValues
        for (size_t i = 1; i < n; i++) if (v[i] != v[0]) return false;
        return true;
    }
    double norm(float f, float dt) const { const double nf = f / nyq_; return dt ? nf * std::exp2(dt / 1200) : nf; }
    void setCoef(State& s, size_t k, double nf, double q, double g) {
        Biquad t; t.setParams(type, nf, q, g);
        s.b0[k] = t.b0; s.b1[k] = t.b1; s.b2[k] = t.b2; s.a1[k] = t.a1; s.a2[k] = t.a2;
    }
    static void run(State& s, const float* src, float* dst, size_t n) {
        if (s.sa) {
            double x1 = s.x1, x2 = s.x2, y1 = s.y1, y2 = s.y2;
            for (size_t k = 0; k < n; ++k) {
                float x = src[k];
                float y = s.b0[k] * x + s.b1[k] * x1 + s.b2[k] * x2 - s.a1[k] * y1 - s.a2[k] * y2;
                dst[k] = y;
                x2 = x1; x1 = x; y2 = y1; y1 = y;
            }
            s.x1 = (float)x1; s.x2 = (float)x2; s.y1 = (float)y1; s.y2 = (float)y2;
            return;
        }
#if defined(__APPLE__)
        s.in[0] = s.x2; s.in[1] = s.x1; s.out[0] = s.y2; s.out[1] = s.y1;
        double coef[5] = {s.b0[0], s.b1[0], s.b2[0], s.a1[0], s.a2[0]};
        size_t done = 0;
        while (done < n) {
            const size_t m = std::min(n - done, (size_t)1024);
            for (size_t i = 0; i < m; i++) s.in[i + 2] = src[done + i];
            vDSP_deq22D(s.in, 1, coef, s.out, 1, (vDSP_Length)m);
            s.in[0] = s.in[m]; s.in[1] = s.in[m + 1];
            s.out[0] = s.out[m]; s.out[1] = s.out[m + 1];
            for (size_t i = 0; i < m; i++) dst[done + i] = (float)s.out[i + 2];
            done += m;
        }
        s.x1 = s.in[1]; s.x2 = s.in[0]; s.y1 = s.out[1]; s.y2 = s.out[0];
#else
        double x1 = s.x1, x2 = s.x2, y1 = s.y1, y2 = s.y2;
        const double c0 = s.b0[0], c1 = s.b1[0], c2 = s.b2[0], d1 = s.a1[0], d2 = s.a2[0];
        for (size_t k = 0; k < n; ++k) {
            float x = src[k];
            float y = c0 * x + c1 * x1 + c2 * x2 - d1 * y1 - d2 * y2;
            dst[k] = y;
            x2 = x1; x1 = x; y2 = y1; y1 = y;
        }
        s.x1 = (float)x1; s.x2 = (float)x2; s.y1 = (float)y1; s.y2 = (float)y2;
#endif
    }
    double sr_, nyq_;
    unsigned Qf_;
    std::vector<State> ch_;
    bool justReset_ = true;
    float pf_ = NAN, pq_ = NAN, pg_ = NAN, pd_ = NAN;
    std::vector<float> f_, q_, g_, d_;
};

}  // namespace cr
}  // namespace al
