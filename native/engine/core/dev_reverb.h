// The Space reverb ('reverb', mkFxNode in index.html) on the engine core's interface (task NB-N3i). Fractals'
// "Plate reverb" return is one (decay 1 s, pre-delay 15 ms, damping 7 kHz, low cut 500 Hz, mix 100 %).
//
// Browser nodes, as the app builds them:
//   in (Gain 1) -> dry (Gain 1 - mix/200) -> out;  in -> pre (DelayNode, max 1 s) -> highpass (BiquadFilterNode)
//   -> ConvolverNode -> wet (Gain mix/100 * 1.4) -> out;  wet -> analyser (only listens)
//   set(): when decay (to 2 decimals) or damping (rounded) changes the impulse is made again (irBuf) and given to the
//   convolver (at once the first time and offline; while playing 120 ms later); every other value by .value.
//   mkFxNode's wrapper adds a GainNode for 'og'.
// The impulse (irBuf): two channels of filtered noise, len = floor(sr * (decay * 1.1 + .1)) frames, each sample
// y = (1 - a) * (RND() * 2 - 1) + a * y with a one-pole coefficient a that glides from 20 kHz down to the damping,
// times exp(-6.9 t / decay). RND() is the app's generator (apprandom.h), in JavaScript's doubles, Math.exp from the
// engine's copy of V8's maths (jsmath.h), each sample stored as a float.
// The ConvolverNode is convolver.h. The whole graph runs on the browser's render quanta (GridDevice): the
// convolver's stages take exactly one quantum per call; calls off that grid hold one quantum (addedLatency).
#pragma once
#include <cstdio>
#include "convolver.h"
#include "dev_shape.h"
#include "dev_tdelay.h"

namespace al {
namespace rvb {

// irBuf(c, dec, damp) in index.html
inline std::vector<std::vector<float>> irBuf(double sr, double dec, double damp, AppRandom& rnd) {
    const size_t len = (size_t)std::floor(sr * (dec * 1.1 + .1));
    std::vector<std::vector<float>> b(2, std::vector<float>(len));
    for (int ch = 0; ch < 2; ch++) {
        float* d = b[ch].data();
        double y = 0;
        for (size_t i = 0; i < len; i++) {
            const double t = (double)i / sr;
            const double fc = damp + (20000 - damp) * js::exp(-3 * t / dec);
            const double a = js::exp(-2 * js::PI * js::min(fc, sr * .45) / sr);
            const double r = rnd.next();
            y = (1 - a) * (r * 2 - 1) + a * y;
            d[i] = (float)(y * js::exp(-6.9 * t / dec) * (1 + (1 - a) * .5));
        }
    }
    return b;
}

// Number.prototype.toFixed(2): the decimal nearest the exact value, the larger one on a tie
inline std::string toFixed2(double x) {
    if (!std::isfinite(x) || std::fabs(x) >= 1e21) { char b[64]; snprintf(b, sizeof b, "%.17g", x); return b; }
    char buf[512];
    snprintf(buf, sizeof buf, "%.60f", std::fabs(x));   // the exact binary value in decimal (glibc and Apple's libc)
    std::string s(buf);
    const size_t dot = s.find('.');
    std::string ip = s.substr(0, dot), fp = s.substr(dot + 1);
    const bool up = fp[2] >= '5';   // past half or exactly half: up (on a tie toFixed picks the larger n)
    std::string digits = ip + fp.substr(0, 2);
    if (up) {
        int i = (int)digits.size() - 1;
        while (i >= 0) { if (digits[i] == '9') { digits[i] = '0'; i--; } else { digits[i]++; break; } }
        if (i < 0) digits.insert(digits.begin(), '1');
    }
    std::string r = digits.substr(0, digits.size() - 2) + "." + digits.substr(digits.size() - 2);
    const bool zero = r.find_first_not_of("0.") == std::string::npos;
    return (x < 0 && !zero ? "-" : "") + r;
}

struct SpaceReverb : shape::GridDevice {
    unsigned Q;
    std::unique_ptr<cr::DelayLine> pre[2];
    cr::BiquadNode hp;
    std::unique_ptr<cr::Reverb> cv;
    AppRandom* rnd_;   // the context's generator when the device was made (the app draws the impulse at set())
    std::unique_ptr<AppRandom> ownRnd;
    std::string key;
    float gDry = 1, gWet = 1, gOg = 1;
    double setFrame = 0;
    bool built = false;
    size_t irLen = 0;
    std::vector<float> a_, b_, c_, d_, e_, f_;

    explicit SpaceReverb(RenderContext& c) : GridDevice(c, (unsigned)std::max(1, c.quantum)), Q((unsigned)std::max(1, c.quantum)), hp(c.sampleRate), rnd_(c.appRandom) {
        hp.setType(cr::BiquadType::Highpass);
        for (auto& d : pre) d.reset(new cr::DelayLine(1, (float)c.sampleRate, Q));
        for (auto* v : {&a_, &b_, &c_, &d_, &e_, &f_}) v->assign(Q, 0.f);
    }
    AppRandom& rnd() {
        if (rnd_) return *rnd_;
        if (!ownRnd) ownRnd.reset(new AppRandom());
        return *ownRnd;
    }
    void apply() {
        const double dec = p.num("decay"), damp = p.num("damp");
        const std::string k = toFixed2(dec) + "/" + std::to_string((long long)js::round(damp));
        if (k != key) {
            key = k;
            const auto ir = irBuf(ctx.sampleRate, dec, damp, rnd());
            irLen = ir[0].size();
            cv.reset(new cr::Reverb(ir, (float)ctx.sampleRate, Q));
        }
        const double now = std::floor(ctx.currentFrame / Q) * Q;
        for (auto& d : pre) d->setDelayTime(p.num("predelay") / 1000);
        hp.setFrequency(p.num("lowcut"));
        gWet = (float)(p.num("mix") / 100 * 1.4);
        gDry = (float)(1 - p.num("mix") / 200);
        setFrame = now;
        gOg = shape::ogGain(p);
    }
    void ensure() override { if (!built) { built = true; apply(); } }
    void set(const JValue& np) override { Processor::set(np); built = true; apply(); }
    bool keepsMono() const override { return false; }   // the convolver's output is stereo

    void block(float* L, float* R, double frame) override {
        const bool sa = std::floor(frame / Q) == std::floor(setFrame / Q);
        const bool mono = monoIn;
        const int nch = mono ? 1 : 2;
        float* in[2] = {L, R};
        float* dly[2] = {a_.data(), b_.data()};
        float* hpo[2] = {c_.data(), d_.data()};
        // in (Gain 1) copies; pre (DelayNode) -> highpass
        for (int k = 0; k < nch; k++) pre[k]->process(in[k], dly[k], (int)Q, 0);
        hp.process(dly, hpo, nch, (int)Q);
        // the ConvolverNode (no impulse: a silent output)
        bool cvOn = (bool)cv;
        if (cv) cv->process(hpo[0], hpo[mono ? 0 : 1], mono, e_.data(), f_.data(), Q);
        else { std::fill(e_.begin(), e_.end(), 0.f); std::fill(f_.begin(), f_.end(), 0.f); }
        // wet, dry, out: dry.connect(out) first, then wet.connect(out); a mono dry is up-mixed (copied to both sides)
        const bool wOn = tdl::TDelay::gain(gWet, e_.data(), cvOn, e_.data(), Q, sa);
        tdl::TDelay::gain(gWet, f_.data(), cvOn, f_.data(), Q, sa);
        float* dry[2] = {a_.data(), b_.data()};
        bool dOn = tdl::TDelay::gain(gDry, L, true, dry[0], Q, sa);
        if (!mono) tdl::TDelay::gain(gDry, R, true, dry[1], Q, sa); else std::copy(dry[0], dry[0] + Q, dry[1]);
        shape::sum2(dry[0], dOn, e_.data(), wOn, L, (int)Q);
        shape::sum2(dry[1], dOn, f_.data(), wOn, R, (int)Q);
        shape::gainNode(gOg, L, L, (int)Q);
        shape::gainNode(gOg, R, R, (int)Q);
    }
    std::vector<std::pair<std::string, double>> meters() const override {
        return {{"addedLatency", (double)addedLatency()}, {"irFrames", (double)irLen}, {"stages", cv ? (double)cv->stages() : 0.0},
                {"scale", cv ? (double)cv->scale() : 0.0}};
    }
};

}  // namespace rvb
}  // namespace al
