// The Sidechain device ('side', mkFxNode in index.html) on the engine core's interface (task NB-N3g).
//
// Browser nodes, as the app builds them (offline render: sync() runs once, before rendering):
//   in (GainNode 1) -> dry (GainNode) ------------------------------> sum (GainNode 1) -> duck (GainNode) -> out
//   in -> pc (compressor, only while punch > 0) -> pg (GainNode) ---> sum
//   in -> sc (compressor, only while sustain > 0) -> sg (GainNode) -> sum
//   duck.gain = 0 + shaper(sawtooth oscillator) + constant source 1 (stopped when the oscillator starts)
// The oscillator runs at 1 / (sync in beats x 60 / bpm) Hz and starts on the first beat boundary 10 ms or more into
// the render, counted from the beat the render starts at; its start is worked out before the settings arrive, so
// its grid is one beat whatever the sync. The shaper's curve turns the sawtooth into the duck: 1 - depth x
// (1 - phase / shape)^2 for the first part of each period.
// Chromium details that change the bits, each one below:
//   - the compressors' outputs always have two channels, so `sum` is stereo and a mono input comes out stereo;
//   - `sum` adds its connections in connection order, the first one copied, and skips one flagged silent (a GainNode
//     at a fixed 0, or the constant source after it stopped);
//   - the wave shaper keeps running on the oscillator's silence before it starts (its tail is endless because the
//     curve is not 0 at 0), so until then duck.gain = 1 + curve(0): about 1.5 at full depth;
//   - every AudioParam set by the app is a setValueAtTime(v, 0), so in the first quantum the GainNodes take their
//     sample-accurate path (a multiply, also by 1 and by 0) and nothing is flagged silent there;
//   - the gain curve is made one render quantum at a time on the context's grid, so any call size gives the same bits.
#pragma once
#include <memory>
#include "../../dsp/al_mix.h"
#include "device.h"
#include "dyncomp.h"
#include "webnodes.h"

namespace al {
namespace side {

struct Side : Processor {
    RenderContext& ctx;
    double sr;
    cr::Oscillator osc;
    cr::ConstantSource k;
    cr::DynamicsCompressor pc, sc;
    std::vector<float> curve;
    float dryG = 1, pgG = 0, sgG = 0;
    bool cP = false, cS = false;
    // the current quantum's duck gain
    std::vector<float> g, q1, q2;
    size_t qStart = (size_t)-1;
    std::vector<float> tL, tR, pL, pR, sL, sR;

    explicit Side(RenderContext& c) : ctx(c), sr(c.sampleRate), osc((float)c.sampleRate, cr::OscType::Sawtooth), k((float)c.sampleRate),
                                      pc((float)c.sampleRate), sc((float)c.sampleRate) {
        // pc.attack=.03; pc.release=.12; pc.ratio=20; pc.threshold=-40; sc.attack=.001; sc.release=.25; sc.ratio=12; sc.threshold=-36
        pc.setAttack(.03); pc.setRelease(.12); pc.setRatio(20); pc.setThreshold(-40);
        sc.setAttack(.001); sc.setRelease(.25); sc.setRatio(12); sc.setThreshold(-36);
        // sync(-(SIDE_B0||0)*60/S.bpm), before set(): cur={} so the period is one beat
        const double bpm = c.bpm;
        const double P = 1 * 60 / bpm;
        double s = -(c.beat0) * 60 / bpm;
        const double now = 0 + .01;   // c.currentTime + .01 (an offline context at 0)
        if (s < now) s += std::ceil((now - s) / P) * P;
        osc.setFrequency(1 / P, 0);
        osc.sched.startAt(s, 0);
        k.setOffset(1);
        k.sched.startAt(0, 0);
        k.sched.stopAt(s);
    }
    bool worklet() const override { return false; }

    static double syncBeats(const JValue& v) {   // SYNCS[...]||1
        if (v.t != JValue::String) return 1;
        const std::string& s = v.s;
        double b = s == "1/2" ? 2 : s == "1/4" ? 1 : s == "1/4 dotted" ? 1.5 : s == "1/4 triplet" ? 2.0 / 3 : s == "1/8" ? .5 :
                   s == "1/8 dotted" ? .75 : s == "1/8 triplet" ? 1.0 / 3 : s == "1/16" ? .25 : 0;
        return b ? b : 1;
    }
    void apply() {
        const double d = p.num("depth") / 100, rel = js::max(.05, p.num("shape") / 100);
        const int N = 512;
        curve.assign(N, 0.f);
        for (int j = 0; j < N; j++) {
            const double x = (double)j / (N - 1) * 2 - 1, ph = x >= 0 ? x / 2 : 1 + x / 2, e = ph < rel ? js::pow(1 - ph / rel, 2) : 0;
            curve[j] = (float)(1 - d * e);
        }
        const double pu = p.num("punch") / 100, su = p.num("sustain") / 100;
        pgG = (float)(pu > 0 ? pu * 2.2 : 0);
        dryG = (float)(1 + (pu < 0 ? pu * .6 : 0) + (su < 0 ? su * .5 : 0));
        sgG = (float)(su > 0 ? su * 3 : 0);
        osc.setFrequency(1 / (syncBeats(p.at("sync")) * 60 / ctx.bpm), 0);
        cP = pu > 0; cS = su > 0;
    }
    bool built = false;
    void ensure() { if (!built) { built = true; apply(); } }
    void set(const JValue& np) override { Processor::set(np); built = true; apply(); }

    // duck.gain for the quantum starting at qs: 0 + shaper(osc) + constant source
    void gainQuantum(size_t qs, size_t Q) {
        g.assign(Q, 0.f); q1.assign(Q, 0.f); q2.assign(Q, 0.f);
        osc.process(qs, Q, q1.data());          // silent or not, the shaper runs
        cr::waveShape(q1.data(), q1.data(), Q, curve);
        for (size_t i = 0; i < Q; i++) g[i] = g[i] + q1[i];
        if (k.process(qs, Q, q2.data())) for (size_t i = 0; i < Q; i++) g[i] = g[i] + q2[i];
    }

    void process(const float* L, const float* R, float* oL, float* oR, int n) override {
        NodeFloatState fz;
        ensure();
        const size_t Q = (size_t)std::max(1, ctx.quantum);
        for (auto* v : {&tL, &tR, &pL, &pR, &sL, &sR}) if ((int)v->size() < n) v->resize(n);
        const float* inR = monoIn ? L : R;
        // the compressors run on the input whenever they are connected (their own 32-frame grid)
        if (cP) pc.process(L, monoIn ? nullptr : R, pL.data(), pR.data(), (unsigned)n);
        if (cS) sc.process(L, monoIn ? nullptr : R, sL.data(), sR.data(), (unsigned)n);
        const size_t f0 = (size_t)ctx.currentFrame;
        for (int i = 0; i < n; i++) {
            const size_t f = f0 + i, qs = f / Q * Q;
            if (qs != qStart) { qStart = qs; gainQuantum(qs, Q); }
            const bool first = qs == 0;   // the quantum of the setValueAtTime(v, 0) events
            float a, b; bool any = false;
            auto add = [&](float x, float y) { if (!any) { a = x; b = y; any = true; } else { a = a + x; b = b + y; } };
            // dry: sample-accurate multiply in the first quantum; then a copy at 1, silence at 0, a multiply otherwise
            if (first || dryG != 0) { const float x = L[i], y = inR[i]; add(first || dryG != 1 ? x * dryG : x, first || dryG != 1 ? y * dryG : y); }
            // pg, sg: their compressor's output (zeros while not connected) through a GainNode
            const float px = cP ? pL[i] : 0.f, py = cP ? pR[i] : 0.f;
            if (first || pgG != 0) add(px * pgG, py * pgG);
            const float sx = cS ? sL[i] : 0.f, sy = cS ? sR[i] : 0.f;
            if (first || sgG != 0) add(sx * sgG, sy * sgG);
            if (!any) { a = 0; b = 0; }
            const float gg = g[f - qs];
            oL[i] = a * gg; oR[i] = b * gg;
        }
        monoOut = false;
    }
    void flushTiny() override {}
    std::vector<std::pair<std::string, double>> meters() const override { return {{"gain", g.empty() ? 1.0 : (double)g[0]}}; }
};

}  // namespace side
}  // namespace al
