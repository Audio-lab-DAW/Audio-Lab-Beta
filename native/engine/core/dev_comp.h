// The Compressor ('comp', mkFxNode in index.html) on the engine core's interface (task NB-N3f).
//
// Browser nodes, as the app builds it:
//   in (GainNode at 1) -> DynamicsCompressorNode (knee 6 dB) -> out (GainNode at 10^(makeup/20))
//   threshold = p.threshold, ratio = p.ratio, attack = p.attack / 1000, release = p.release / 1000 (each an
//   AudioParam: the JavaScript number rounded to float). The analyser on the input only listens.
// The compressor's output always has two channels (a mono input is read as both), so the device makes a mono
// input stereo. It is 6 ms late (288 frames at 48 kHz): the app's fxLat says Math.round(.006 * sr), which is
// the same at 48 kHz and 1 frame more than Chromium's 264 at 44.1 kHz (0.006f * 44100 = 264.6, truncated).
// The meter: Chromium's reduction (dB), what the app's gain-reduction display reads.
#pragma once
#include <memory>
#include "../../dsp/al_mix.h"
#include "device.h"
#include "dyncomp.h"

namespace al {
namespace comp {

struct Comp : Processor {
    cr::DynamicsCompressor k;
    float makeup = 1.f;
    explicit Comp(RenderContext& ctx) : k((float)ctx.sampleRate) {}
    bool worklet() const override { return false; }

    void apply() {
        // fx.set(p): k.threshold.value=p.threshold; k.ratio.value=p.ratio; k.knee.value=6;
        // k.attack.value=p.attack/1000; k.release.value=p.release/1000; g.gain.value=Math.pow(10,p.makeup/20)
        k.setThreshold(p.num("threshold"));
        k.setRatio(p.num("ratio"));
        k.setKnee(6);
        k.setAttack(p.num("attack") / 1000);
        k.setRelease(p.num("release") / 1000);
        makeup = (float)js::pow(10, p.num("makeup") / 20);
    }
    bool built = false;
    void ensure() { if (!built) { built = true; apply(); } }
    void set(const JValue& np) override { Processor::set(np); built = true; apply(); }

    void process(const float* L, const float* R, float* oL, float* oR, int n) override {
        NodeFloatState fz;
        ensure();
        k.process(L, monoIn ? nullptr : R, oL, oR, (unsigned)n);
        monoOut = false;
        // GainNode: exactly 1 copies, anything else multiplies (gainFixed: 0 writes silence)
        if (makeup != 1.f) { gainFixed(makeup, oL, oL, n); gainFixed(makeup, oR, oR, n); }
    }
    void flushTiny() override {}
    std::vector<std::pair<std::string, double>> meters() const override {
        return {{"reduction", (double)k.reduction()}, {"latency", (double)k.latencyFrames()}};
    }
};

}  // namespace comp
}  // namespace al
