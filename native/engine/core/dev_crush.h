// Bitcrusher 'al-crush' (class Crush in WLSRC) on the engine core's interface (task NB-N3a).
// Same arithmetic as native/dsp/al_crush.h (test A, NM1), with the settings read with JavaScript semantics.
#pragma once
#include <string>
#include "device.h"

namespace al {
namespace fx {
using namespace js;

struct Crush : Processor {
    double sr;
    WorkletRandom* rnd;
    double ph = 1, hl[2] = {0, 0}, pl[2] = {0, 0}, po[2] = {0, 0}, rndField = 1;
    explicit Crush(RenderContext& ctx) : sr(ctx.sampleRate), rnd(&ctx.random) {}
    void process(const float* L, const float* R, float* oL, float* oR, int n) override {
        const double bits = js::max(1, js::min(24, p.orNum("bits", 8))), q = std::pow(2.0, bits - 1),
                     rt = js::max(1, p.orNum("rate", 1)), jt = p.orNum("jit", 0) / 100, dith = p.orNum("dith", 0) / 100 / q,
                     dr = dB(p.orNum("drive", 0)), mix = p.nnNum("mix", 100) / 100, go = dB(p.orNum("out", 0));
        const double pre = p.num("pre"), post = p.num("post");
        const double pc = pre > 0 ? 1 - std::exp(-TAU * js::min(sr * .45, pre) / sr) : 1,
                     oc = post > 0 ? 1 - std::exp(-TAU * js::min(sr * .45, post) / sr) : 1;
        const std::string mode = p.orStr("shape", "round");
        const int md = mode == "floor" ? 1 : mode == "trunc" ? 2 : mode == "fold" ? 3 : 0;
        const bool dithOn = !(dith == 0 || std::isnan(dith));
        for (int i = 0; i < n; i++) {
            const double xs[2] = {(double)L[i], (double)R[i]};
            ph += 1;
            if (ph >= rt * (1 + (rnd->next() * 2 - 1) * jt)) {
                ph -= rt;
                for (int c = 0; c < 2; c++) {
                    pl[c] += pc * (xs[c] * dr - pl[c]);
                    double v = pl[c], d = 0;
                    if (dithOn) { const double r1 = rnd->next(); const double r2 = rnd->next(); d = (r1 - r2) * dith; }
                    v = md == 1 ? std::floor((v + d) * q) / q : md == 2 ? std::trunc((v + d) * q) / q : js::round((v + d) * q) / q;
                    if (md == 3) v = js::abs(std::fmod(std::fmod(v + 1, 4.0) + 4, 4.0) - 2) - 1;
                    hl[c] = v > 1 ? 1 : v < -1 ? -1 : v;
                }
            }
            for (int c = 0; c < 2; c++) {
                po[c] += oc * (hl[c] - po[c]);
                const double wet = po[c] * go, y = xs[c] * (1 - mix) + wet * mix;
                (c ? oR : oL)[i] = f32(y);
            }
        }
    }
    void flushTiny() override { z(ph); for (int c = 0; c < 2; c++) { z(hl[c]); z(pl[c]); z(po[c]); } z(rndField); }
};

}  // namespace fx
}  // namespace al
