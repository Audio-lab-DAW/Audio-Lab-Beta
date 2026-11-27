// The Soft Clipper ('clip') and the Drive ('drive') on the engine core's interface (task NB-N3g).
//
// Browser nodes, as the app builds them (index.html: ND('clip', ...).node and mkFxNode's 'drive'):
//   clip:  in (Gain 1) -> pre (Gain dbA(gain)/4) -> delay (192, 128 or 0 frames as the oversampling) -> dry (Gain
//          (1-mix)*4) -> out;  pre -> highpass (7 Hz with asymmetry, else 1 Hz) -> WaveShaper (8192-point curve of
//          clipF, oversampled as chosen) -> wet (Gain mix) -> post (Gain dbA(out)) -> out
//   drive: in (Gain 1) -> delay (192 frames) -> dry (Gain 1-mix) -> out;  in -> WaveShaper (2048 points, 4x) ->
//          wet (Gain mix/(1+drive/60)) -> out
//   (the analysers only listen; mkFxNode's wrapper adds a Gain for 'og', 1 unless set)
// 'out' sums its two inputs as an AudioNodeInput does: a GainNode at exactly 0 outputs a silent bus, which the sum
// skips; the first other input is copied, the second added.
//
// The grid. The WaveShaper's 4x path convolves by FFT on 128-frame sub-blocks counted from the context's first
// frame, so a sub-block's output depends on all of its input. When the engine calls the device on that grid
// (whole sub-blocks, as the web engine's 128 and 512 quanta and the engine's usual 128 or larger buffers) it runs
// directly, with no added latency. When the calls are smaller or off the grid (a 32-frame device buffer), the
// device holds one sub-block: the output is the browser's, bit for bit, 128 frames later, and addedLatency()
// says so for delay compensation. Which of the two is decided by the first call.
#pragma once
#include <memory>
#include "../../dsp/al_mix.h"
#include "biquad.h"
#include "device.h"
#include "waveshaper.h"

namespace al {
namespace shape {

// A GainNode's output: its bus and whether Chromium marks it silent (a fixed gain of exactly 0).
inline bool gainNode(float g, const float* in, float* out, int n) {
    if (g == 0.f) { for (int i = 0; i < n; i++) out[i] = 0.f; return false; }
    if (g == 1.f) { if (out != in) std::copy(in, in + n, out); return true; }
    for (int i = 0; i < n; i++) out[i] = in[i] * g;
    return true;
}
// AudioNodeInput with two connections: silent ones skipped, the first copied, the second added
inline void sum2(const float* a, bool aOn, const float* b, bool bOn, float* out, int n) {
    if (aOn && bOn) { for (int i = 0; i < n; i++) { float v = a[i]; v += b[i]; out[i] = v; } }
    else if (aOn) std::copy(a, a + n, out);
    else if (bOn) std::copy(b, b + n, out);
    else for (int i = 0; i < n; i++) out[i] = 0.f;
}

// Runs a device's node graph on the browser's sub-block grid (see the top of this file).
struct GridDevice : Processor {
    RenderContext& ctx;
    unsigned sub;
    int mode = 0;   // 0 not decided, 1 on the grid, 2 holding a sub-block
    explicit GridDevice(RenderContext& c) : ctx(c), sub(cr::subBlockFrames((unsigned)std::max(1, c.quantum))) {}
    bool worklet() const override { return false; }
    // one sub-block (sub frames, starting at grid frame `frame`), two channels, in place
    virtual void block(float* L, float* R, double frame) = 0;
    virtual void ensure() = 0;
    int addedLatency() const override { return mode == 2 ? (int)sub : 0; }
    int maxAddedLatency() const override { return (int)sub; }

    void process(const float* L, const float* R, float* oL, float* oR, int n) override {
        NodeFloatState fz;   // Chromium's audio nodes run with denormals flushed
        ensure();
        const double f0 = ctx.currentFrame;
        if (!mode) {
            mode = (std::fmod(f0, (double)sub) == 0 && n % (int)sub == 0) ? 1 : 2;
            if (mode == 2) {   // the frames of the first sub-block before f0 are silence; the output starts sub later
                const int pre = (int)std::fmod(f0, (double)sub);
                inL_.assign(pre, 0.f); inR_.assign(pre, 0.f);
                outL_.assign(sub - pre, 0.f); outR_.assign(sub - pre, 0.f); outPos_ = 0;
                gridFrame_ = f0 - pre;
            }
        }
        if (mode == 1 && (std::fmod(f0, (double)sub) != 0 || n % (int)sub != 0)) {
            // a call off the grid after calls on it: hold a sub-block from here on (the latency changes once)
            mode = 2; lateSwitch_ = true;
            inL_.clear(); inR_.clear(); outL_.assign(sub, 0.f); outR_.assign(sub, 0.f); outPos_ = 0; gridFrame_ = f0;
        }
        const bool mono = monoIn;
        if (mode == 1) {
            for (int done = 0; done < n; done += (int)sub) {
                std::copy(L + done, L + done + sub, oL + done);
                if (mono) std::copy(L + done, L + done + sub, oR + done); else std::copy(R + done, R + done + sub, oR + done);
                block(oL + done, oR + done, f0 + done);
            }
        } else {
            for (int i = 0; i < n; i++) {
                inL_.push_back(L[i]); inR_.push_back(mono ? L[i] : R[i]);
                if (inL_.size() == sub) {
                    bL_.assign(inL_.begin(), inL_.end()); bR_.assign(inR_.begin(), inR_.end());
                    block(bL_.data(), bR_.data(), gridFrame_);
                    gridFrame_ += sub;
                    outL_.insert(outL_.end(), bL_.begin(), bL_.end()); outR_.insert(outR_.end(), bR_.begin(), bR_.end());
                    inL_.clear(); inR_.clear();
                }
                oL[i] = outL_[outPos_]; oR[i] = outR_[outPos_]; outPos_++;
                if (outPos_ >= sub) { outL_.erase(outL_.begin(), outL_.begin() + outPos_); outR_.erase(outR_.begin(), outR_.begin() + outPos_); outPos_ = 0; }
            }
        }
        monoOut = mono;   // both channels were the same; a mono input stays mono, as in the browser
    }
    void flushTiny() override {}

protected:
    bool lateSwitch_ = false;
    std::vector<float> inL_, inR_, outL_, outR_, bL_, bR_;
    size_t outPos_ = 0;
    double gridFrame_ = 0;
};

// mkFxNode's wrapper: a GainNode for p.og, set only when it is 1e-4 or more away from 1
inline float ogGain(const Params& p) {
    const double v = js::pow(10, p.orNum("og", 0) / 20);
    return std::fabs(1.0 - v) > 1e-4 ? (float)v : 1.f;
}

// ---- the Soft Clipper's curve (clipF in index.html), in JavaScript's doubles ----
struct ClipP { double thr, ceil; std::string shape; };
inline double clipF(double a, const ClipP& p) {
    const double T = js::dB(p.thr), C = js::dB(p.ceil);
    const std::string& s = p.shape.empty() ? std::string("tanh") : p.shape;
    if (a <= T) return a;
    const double u = (a - T) / js::max(1e-4, C - T);
    double y;
    if (s == "cubic") y = u < 1.5 ? u - u * u * u / 6.75 : 1;
    else if (s == "sine") y = u < js::PI / 2 ? js::sin(u) : 1;
    else if (s == "hard") y = js::min(1, u);
    else if (s == "fold") { double q = std::fmod(u, 4); y = q < 1 ? q : q < 3 ? 2 - q : q - 4; y = std::fabs(y) > 1 ? 1 : y; }
    else if (s == "atan") { y = fdlibm::atan(u * 1.6) / fdlibm::atan(1.6 * 3) * 1.55; y = js::min(1, y); }   // V8: ieee754::atan
    else y = fdlibm::tanh(u);   // V8's Math.tanh: ieee754::tanh (Chromium's fdlibm is the same code)
    return T + (C - T) * y;
}
inline double jsSign(double x) { return x > 0 ? 1 : x < 0 ? -1 : x; }

struct Clip : GridDevice {
    cr::WaveShaper ws;
    cr::BiquadNode hp;
    std::unique_ptr<cr::DelayLine> dl[2];
    float gPre = .25f, gDry = 0.f, gWet = 1.f, gPost = 1.f, gOg = 1.f;
    std::string key;
    bool built = false;
    explicit Clip(RenderContext& c) : GridDevice(c), ws((unsigned)std::max(1, c.quantum)), hp(c.sampleRate) {
        hp.setType(cr::BiquadType::Highpass);
        hp.setFrequency(7);
        for (auto& d : dl) { d.reset(new cr::DelayLine(.05, (float)c.sampleRate, (unsigned)std::max(1, c.quantum))); d->setDelayTime(192 / c.sampleRate); }
    }
    void apply() {
        gPre = (float)(js::dB(p.num("gain")) / 4);
        const std::string os = p.orStr("os", "4x");
        ws.setOversample(cr::oversampleOf(os));
        const double d = (p.is("os", "none") ? 0 : p.is("os", "2x") ? 128 : 192) / ctx.sampleRate;
        for (auto& x : dl) x->setDelayTime(d);
        ClipP cp{p.num("thr"), p.num("ceil"), p.at("shape").t == JValue::String ? p.at("shape").s : std::string()};
        const double bias = p.num("bias");
        char kb[160];
        snprintf(kb, sizeof kb, "%s,%.17g,%.17g,%.17g", cp.shape.c_str(), cp.thr, cp.ceil, bias);
        if (key != kb) {
            key = kb;
            const int N = 8192;
            std::vector<float> cv(N);
            const double b = bias / 100 * .35;
            for (int j = 0; j < N; j++) {
                const double x = ((double)j / (N - 1) * 2 - 1) * 4;
                const double y = x + b >= 0 ? clipF(std::fabs(x + b), cp) * jsSign(x + b) : -clipF(std::fabs(x + b), cp);
                const double y0 = b ? (b >= 0 ? clipF(b, cp) : -clipF(-b, cp)) : 0;
                cv[j] = (float)(y - y0);
            }
            ws.setCurve(cv);
        }
        const double m = p.num("mix") / 100;
        gWet = (float)m;
        gDry = (float)((1 - m) * 4);
        gPost = (float)(js::dB(p.num("out")) / 1);
        hp.setFrequency(Params::truthy(p.at("bias")) ? 7 : 1);
        gOg = ogGain(p);
    }
    void ensure() override { if (!built) { built = true; apply(); } }
    void set(const JValue& np) override { Processor::set(np); built = true; apply(); }
    void block(float* L, float* R, double frame) override {
        const int n = (int)sub;
        float* ch[2] = {L, R};
        const int pq = (int)std::fmod(frame, (double)std::max(1, ctx.quantum));
        std::vector<float>& a = t_[0]; std::vector<float>& b = t_[1]; std::vector<float>& c = t_[2]; std::vector<float>& e = t_[3];
        for (auto& v : t_) v.resize(2 * n);
        float* pre[2] = {a.data(), a.data() + n};
        float* hpo[2] = {b.data(), b.data() + n};
        for (int k = 0; k < 2; k++) gainNode(gPre, ch[k], pre[k], n);   // in (Gain 1) copies; pre
        hp.process(pre, hpo, 2, n);
        ws.processSubBlock(hpo, hpo, 2);
        for (int k = 0; k < 2; k++) {
            float* dly = c.data() + k * n;   // delay -> dry
            dl[k]->process(pre[k], dly, n, pq);
            const bool dryOn = gainNode(gDry, dly, dly, n);
            float* w = e.data() + k * n;      // ws -> wet -> post
            bool wetOn = gainNode(gWet, hpo[k], w, n);
            if (wetOn) wetOn = gainNode(gPost, w, w, n); else for (int i = 0; i < n; i++) w[i] = 0.f;
            sum2(dly, dryOn, w, wetOn, ch[k], n);   // dry.connect(out) first, then post.connect(out)
            gainNode(gOg, ch[k], ch[k], n);
        }
    }
    std::vector<std::pair<std::string, double>> meters() const override {
        return {{"latency", (double)ws.latencyFrames()}, {"addedLatency", (double)addedLatency()}, {"lateSwitch", lateSwitch_ ? 1.0 : 0.0}};
    }

private:
    std::vector<float> t_[4];
};

struct Drive : GridDevice {
    cr::WaveShaper ws;
    std::unique_ptr<cr::DelayLine> dl[2];
    float gDry = 0.f, gWet = 1.f, gOg = 1.f;
    double last = -1;
    bool built = false;
    explicit Drive(RenderContext& c) : GridDevice(c), ws((unsigned)std::max(1, c.quantum)) {
        ws.setOversample(cr::Oversample::X4);
        for (auto& d : dl) { d.reset(new cr::DelayLine(.05, (float)c.sampleRate, (unsigned)std::max(1, c.quantum))); d->setDelayTime(192 / c.sampleRate); }
    }
    void apply() {
        const double drive = p.num("drive");
        if (drive != last) {
            last = drive;
            const double k = drive * 1.5;
            const int n = 2048;
            std::vector<float> cu(n);
            for (int j = 0; j < n; j++) { const double x = (double)j / (n - 1) * 2 - 1; cu[j] = (float)((1 + k) * x / (1 + k * std::fabs(x))); }
            ws.setCurve(cu);
        }
        const double m = p.num("mix") / 100;
        gWet = (float)(m / (1 + drive / 60));
        gDry = (float)(1 - m);
        gOg = ogGain(p);
    }
    void ensure() override { if (!built) { built = true; apply(); } }
    void set(const JValue& np) override { Processor::set(np); built = true; apply(); }
    void block(float* L, float* R, double frame) override {
        const int n = (int)sub;
        float* ch[2] = {L, R};
        const int pq = (int)std::fmod(frame, (double)std::max(1, ctx.quantum));
        for (auto& v : t_) v.resize(2 * n);
        float* wso[2] = {t_[0].data(), t_[0].data() + n};
        const float* in[2] = {L, R};
        ws.processSubBlock(in, wso, 2);
        for (int k = 0; k < 2; k++) {
            float* dly = t_[1].data() + k * n;
            dl[k]->process(ch[k], dly, n, pq);
            const bool dryOn = gainNode(gDry, dly, dly, n);
            const bool wetOn = gainNode(gWet, wso[k], wso[k], n);
            sum2(dly, dryOn, wso[k], wetOn, ch[k], n);   // dry.connect(out) first, then wet.connect(out)
            gainNode(gOg, ch[k], ch[k], n);
        }
    }
    std::vector<std::pair<std::string, double>> meters() const override {
        return {{"latency", (double)ws.latencyFrames()}, {"addedLatency", (double)addedLatency()}, {"lateSwitch", lateSwitch_ ? 1.0 : 0.0}};
    }

private:
    std::vector<float> t_[2];
};

}  // namespace shape
}  // namespace al
