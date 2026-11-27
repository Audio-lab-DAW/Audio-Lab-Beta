// The Pro EQ ('eq', mkEQ2 in index.html) on the engine core's interface (task NB-N3e).
//
// Not a worklet: the web engine builds it from browser nodes, so the port follows mkEQ2's graph node for node and
// each node is Chromium's arithmetic (biquad.h for BiquadFilterNode, al_mix.h for GainNode):
//   stereo placement:  in -> [band stages ...] -> out gain
//   mid/side (any band placed on M or S):
//       in -> splitter; mid = 0.5 * (L + R); side = 0.5 * (L + (-1 * R))
//       mid -> [stages of the bands on M or on both]; side -> [stages of the bands on S or on both]
//       merger: L = mid + side, R = mid + (-1 * side) -> out gain
//   a band's stages: 1, a pass filter 1 per 12 dB/oct of slope (Q 0.707 dB on all but the last), a tilt 2 shelves;
//   a soloed band alone, as one band-pass; bells and shelves at 0 dB are left out until they are first used
//   (mkEQ2's `keep`), so the chain is rebuilt (fresh filter state) only when its shape changes, as in the app.
//   out gain = 10^((out + auto) / 20); auto (the 'auto' switch) from the stages' getFrequencyResponse at 48 points.
// The analysers and the dynamic bands' detectors listen only; the dynamic bands' gain moves from a timer in live
// play (not in an export) and is not ported yet.
// The worklet bundle's rules (silence, tiny values) do not apply to browser nodes: Processor::worklet() is false.
#pragma once
#include <memory>
#include <set>
#include <string>
#include <vector>
#include "../../dsp/al_mix.h"
#include "biquad.h"
#include "device.h"

namespace al {
namespace eq {

struct Band { bool on = false, dyn = false, solo = false; std::string t, pl; double f = 1000, g = 0, q = 1, sl = 12; };
struct Stage { int bi, k, n; char ch; std::unique_ptr<cr::BiquadNode> q; };

inline double jnum(const JValue& x) { return Params::toNumber(x); }

struct ProEQ : Processor {
    double sr;
    std::vector<Band> bands;
    std::set<int> keep;
    std::string sig;
    bool ms = false;
    std::vector<Stage> stages;
    float outGain = 1.f;
    double autoDb = 0;
    explicit ProEQ(RenderContext& ctx) : sr(ctx.sampleRate) {}
    bool worklet() const override { return false; }

    static bool has(const std::string& s, const char* sub) { return s.find(sub) != std::string::npos; }
    static bool isPass(const std::string& t) { return has(t, "pass") && t != "bandpass"; }                 // /pass/.test(t)&&t!=='bandpass'
    static bool isShelfPeak(const std::string& t) { return has(t, "shelf") || has(t, "peak"); }            // /shelf|peak/
    static bool isShelfPeakTilt(const std::string& t) { return isShelfPeak(t) || has(t, "tilt"); }
    static int stagesOf(const Band& b) {                                                                  // eqStages
        if (b.t == "tilt") return 2;
        if (isPass(b.t)) return std::max(1, (int)js::round((b.sl ? b.sl : 12) / 12)); // Math.max(1,Math.round((b.sl||12)/12))
        return 1;
    }
    static bool idle(const Band& b) { return isShelfPeakTilt(b.t) && !b.dyn && js::abs(b.g ? b.g : 0) < 1e-4; }  // eqIdle (UI.eqAll off)

    void readBands() {
        bands.clear();
        const JValue& a = p.at("bands");
        for (const JValue& x : a.a) {
            Band b;
            b.on = Params::truthy(x["on"]); b.dyn = Params::truthy(x["dyn"]); b.solo = Params::truthy(x["solo"]);
            b.t = x["t"].t == JValue::String ? x["t"].s : "";
            b.pl = Params::truthy(x["pl"]) && x["pl"].t == JValue::String ? x["pl"].s : "st";                     // b.pl||'st'
            const JValue& sl = x["sl"]; b.sl = Params::truthy(sl) ? jnum(sl) : 12;                                // b.sl||12
            // if(!isFinite(b.f))b.f=1000; if(!isFinite(b.g))b.g=0; if(!isFinite(b.q)||b.q<=0)b.q=1
            b.f = jnum(x["f"]); if (!std::isfinite(b.f)) b.f = 1000;
            b.g = jnum(x["g"]); if (!std::isfinite(b.g)) b.g = 0;
            b.q = jnum(x["q"]); if (!std::isfinite(b.q) || b.q <= 0) b.q = 1;
            bands.push_back(b);
        }
    }
    int soloIndex() const { for (size_t i = 0; i < bands.size(); i++) if (bands[i].on && bands[i].solo) return (int)i; return -1; }

    void build() {
        stages.clear();
        const int solo = soloIndex();
        std::vector<int> act;
        for (size_t i = 0; i < bands.size(); i++) {
            const Band& b = bands[i];
            if (b.on && (solo < 0 || (int)i == solo) && (solo == (int)i || !idle(b) || keep.count((int)i))) act.push_back((int)i);
        }
        ms = false;
        for (int i : act) if (bands[i].pl != "st") ms = true;
        auto chain = [&](char ch) {
            for (int i : act) {
                const Band& b = bands[i];
                const char pl = b.pl == "m" ? 'm' : b.pl == "s" ? 's' : (b.pl == "st" ? 't' : '?');
                if (ms && ch != 't' && pl != 't' && pl != ch) continue;
                const int n = solo == i ? 1 : stagesOf(b);
                for (int k = 0; k < n; k++) stages.push_back(Stage{i, k, n, ch, std::unique_ptr<cr::BiquadNode>(new cr::BiquadNode(sr))});
            }
        };
        if (!ms) chain('t'); else { chain('m'); chain('s'); }
    }

    void apply() {
        readBands();
        for (size_t i = 0; i < bands.size(); i++) if (bands[i].on && !idle(bands[i])) keep.insert((int)i);
        std::string s;
        for (size_t i = 0; i < bands.size(); i++) {
            const Band& b = bands[i];
            s += (b.on ? "1" : "0") + b.t + "|" + std::to_string(b.sl) + "|" + b.pl + (b.dyn ? "D" : "d") + (b.solo ? "S" : "s") + (keep.count((int)i) ? "K" : "k") + ";";
        }
        if (s != sig) { sig = s; build(); }
        const double ny = sr / 2 - 60, gs = p.nnNum("gs", 100) / 100;
        const int solo = soloIndex();
        for (Stage& st : stages) {
            const Band& b = bands[st.bi];
            cr::BiquadNode& q = *st.q;
            const double fr = js::max(10, js::min(ny, b.f));                                   // clamp(b.f,10,ny)
            cr::BiquadType ty;
            if (solo == st.bi) { q.setType(cr::BiquadType::Bandpass); q.setFrequency(fr); q.setQ(js::max(.4, b.q)); continue; }
            const double gg = b.g * gs + 0;                                                    // + (X.dyn[i]||0): live only
            if (b.t == "tilt") {
                q.setType(st.k ? cr::BiquadType::Highshelf : cr::BiquadType::Lowshelf); q.setFrequency(fr); q.setQ(.5);
                q.setGain(st.k ? gg / 2 : -gg / 2); continue;
            }
            if (cr::biquadTypeOf(b.t, ty)) q.setType(ty);   // an unknown type: the browser keeps the old one (and warns)
            q.setFrequency(fr);
            q.setQ(isPass(b.t) ? (st.k == st.n - 1 ? js::max(.3, b.q) : .707) : js::max(.1, b.q));
            if (isShelfPeak(b.t)) q.setGain(gg);
        }
        double au = 0;
        if (Params::truthy(p.at("auto")) && !stages.empty()) {
            const int n = 48;
            float F[n], M[n], T[n];
            for (int k = 0; k < n; k++) { F[k] = (float)(40 * js::pow(400, (double)k / (n - 1))); T[k] = 1; }
            for (Stage& st : stages) { st.q->response(F, M, n); for (int k = 0; k < n; k++) T[k] = (float)((double)T[k] * M[k]); }
            double sum = 0;
            for (int k = 0; k < n; k++) sum += 20 * js::log10(js::max(1e-4, T[k]));
            au = -sum / n;
        }
        autoDb = au;
        const JValue& o = p.at("out");
        outGain = (float)js::pow(10, ((Params::truthy(o) ? Params::toNumber(o) : 0) + au) / 20);   // (p.out||0)
    }

    bool built = false;
    void ensure() { if (!built) { built = true; apply(); } }
    void set(const JValue& np) override { Processor::set(np); built = true; apply(); }

    void runChain(char ch, const float* const* in, float* const* out, int chans, int n) {
        const float* cur[2] = {in[0], chans > 1 ? in[1] : nullptr};
        bool first = true;
        for (Stage& st : stages) {
            if (st.ch != ch) continue;
            float* dst[2] = {out[0], chans > 1 ? out[1] : nullptr};
            if (!first) {   // in place: copy the previous stage's output aside
                for (int c = 0; c < chans; c++) { std::copy(cur[c], cur[c] + n, tmp_[c].begin()); cur[c] = tmp_[c].data(); }
            }
            st.q->process(cur, dst, chans, n);
            cur[0] = out[0]; if (chans > 1) cur[1] = out[1];
            first = false;
        }
        if (first) for (int c = 0; c < chans; c++) if (out[c] != in[c]) std::copy(in[c], in[c] + n, out[c]);
    }

    void process(const float* L, const float* R, float* oL, float* oR, int n) override {
        NodeFloatState fz;   // Chromium's audio nodes run with denormals flushed
        ensure();
        for (auto& v : tmp_) if ((int)v.size() < n) v.resize(n);
        for (auto& v : buf_) if ((int)v.size() < n) v.resize(n);
        const int chans = monoIn ? 1 : 2;
        if (!ms) {
            const float* in[2] = {L, R};
            float* out[2] = {oL, oR};
            runChain('t', in, out, chans, n);
            monoOut = monoIn;
        } else {
            float *m = buf_[0].data(), *s = buf_[1].data(), *nr = buf_[2].data();
            // splitter: channel 1 of a mono input is silence
            // an input with two connections: the first copied, the second added (AudioChannel::SumFrom); a mono
            // input's splitter output 1 is silent and skipped
            for (int i = 0; i < n; i++) { float l = L[i], r = monoIn ? 0.f : R[i]; nr[i] = r; m[i] = l; if (!monoIn) m[i] += r; }
            gainFixed(.5f, m, m, n);
            gainFixed(-1.f, nr, nr, n);
            for (int i = 0; i < n; i++) { s[i] = L[i]; if (!monoIn) s[i] += nr[i]; }
            gainFixed(.5f, s, s, n);
            float *mo = buf_[3].data(), *so = buf_[4].data();
            const float* im[1] = {m}; float* om[1] = {mo}; runChain('m', im, om, 1, n);
            const float* is[1] = {s}; float* os[1] = {so}; runChain('s', is, os, 1, n);
            gainFixed(-1.f, so, nr, n);   // nS
            for (int i = 0; i < n; i++) { float a = mo[i]; a += so[i]; float b = mo[i]; b += nr[i]; oL[i] = a; oR[i] = b; }
            monoOut = false;
        }
        // GainNode at exactly 1 copies (measured: tiny values pass it untouched, where a multiply under the
        // flushing state would make them zero); any other value multiplies
        if (outGain != 1.f) { gainFixed(outGain, oL, oL, n); if (!monoOut) gainFixed(outGain, oR, oR, n); }
        if (monoOut) std::copy(oL, oL + n, oR);
    }
    void flushTiny() override {}
    std::vector<std::pair<std::string, double>> meters() const override { return {{"auto", autoDb}, {"stages", (double)stages.size()}}; }

private:
    std::vector<float> tmp_[2], buf_[5];
};

}  // namespace eq
}  // namespace al
