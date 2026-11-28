// The Timeless delay ('tdelay', mkFxNode in index.html) on the engine core's interface (task NB-N3h).
//
// Browser nodes, as the app builds them:
//   in (Gain) -> out (Gain);  in -> splitter -> inL, inR (Gains) -> L.d, R.d (DelayNodes, max 4 s)
//   per side X: X.d -> highpass -> lowpass -> WaveShaper (256 points, tanh) -> X.self (Gain) -> X.d   (feedback)
//               L.sh -> R.cross -> L.d and R.sh -> L.cross -> R.d: the "ping-pong" GainNodes feed each side's
//               shaper back into its own delay, so ping-pong (inR at 0, self at 0) leaves the right side dry
//   L.sh, R.sh -> merger -> wet (Gain) -> out;  an LFO (sine) -> lg, lg2 (Gains) -> L.d.delayTime, R.d.delayTime
//   set(): delayTime.setTargetAtTime(tm, now, .05) (R: tm * (1 + width * .06)); every other value by .value.
// What decides the bits (Chromium 158.0.8127.36):
//   - the feedback loop. AudioHandler::ProcessIfNecessary marks a node as processed before it pulls its inputs, so a
//     node pulled again in the same render quantum hands out its output of the quantum before: each delay's two
//     feedback GainNodes read the previous quantum of its shaper (one render quantum of delay added to the loop).
//     The loop is therefore computed one whole render quantum at a time (128 frames, 512 in the app's export);
//   - the delay time is an a-rate AudioParam: Chromium's timeline for setTargetAtTime (audio_param_handler.cc,
//     ProcessSetTarget: the exact value at the event's first frame, then v += (target - v) * c per frame; on x86 four
//     frames at a time with the constants c0..c3 as Chromium unrolls it, on ARM one by one; converged after 10 time
//     constants, then the target itself), clamped to [0, 4], the LFO's GainNode summed in, clamped again;
//   - the DelayNode's a-rate path (delay.cc with delay_sse2.cc / delay_neon.cc): the quantum copied in first, then
//     read position, index and interpolation in float for whole groups of four frames, the scalar double path for
//     the rest;
//   - GainNodes: the quantum where .value was set runs the sample-accurate multiply; after that a gain of 0 is a
//     silent bus (skipped by a sum), 1 a copy, else a multiply; a node whose input is silent is silent.
// Calls on the browser's quantum grid run directly; others hold one quantum (GridDevice, addedLatency).
#pragma once
#include "dev_shape.h"
#include "dyncomp.h"
#include "webnodes.h"

namespace al {
namespace tdl {

// An AudioParam whose timeline holds setTargetAtTime events only (the delay time here).
class SetTargetParam {
public:
    SetTargetParam(float def, float mn, float mx) : value_(def), min_(mn), max_(mx) {}
    // setTargetAtTime(target, time, tau): an event at the same time replaces the earlier one (InsertEvent)
    void setTarget(double target, double time, double tau) {
        for (auto& e : ev_) if (e.time == time) { e.target = (float)target; e.tau = tau; return; }
        ev_.push_back({(float)target, time, tau});
        std::stable_sort(ev_.begin(), ev_.end(), [](const Ev& a, const Ev& b) { return a.time < b.time; });
    }
    // CalculateTimelineValues for one quantum: values[0..n) for frames start..start+n
    void quantum(size_t start, size_t n, double sr, unsigned Q, float* values) {
        float def = value_;
        timeline(start, start + n, def, values, n, sr, Q);
        for (size_t i = 0; i < n; i++) values[i] = clampF(values[i]);   // ValuesForFrameRange's Vclip
        value_ = values[n - 1];
    }
    float clampF(float v) const { v = v < max_ ? v : max_; return v > min_ ? v : min_; }

private:
    struct Ev { float target; double time; double tau; };
    static constexpr float kTimeConstantsToConverge = 10.0f;
    static constexpr float kSetTargetThreshold = 4.539992976248485e-05f;
    static bool converged(float value, float target, double now, double start, double tc) {
        if (now > start + kTimeConstantsToConverge * tc) return true;
        if (target == 0 && std::fabs(value) < kSetTargetThreshold) return true;
        if (target != 0 && std::fabs(target - value) < kSetTargetThreshold * std::fabs(value)) return true;
        return false;
    }
    void timeline(size_t start, size_t end, float& def, float* values, size_t n, double sr, unsigned Q) {
        if (ev_.empty() || (end / sr <= ev_[0].time)) { std::fill(values, values + n, def); return; }
        const double now = start / sr;
        // HandleAllEventsInThePast
        {
            const Ev& last = ev_.back();
            if (last.time + 1.5 * Q / sr < now) {
                if (converged(def, last.target, now, last.time, (float)last.tau)) {
                    def = last.target;
                    std::fill(values, values + n, def);
                    ev_.clear();
                    return;
                }
            }
        }
        size_t cur = start, w = 0;
        // HandleFirstEvent
        if (ev_[0].time > start / sr) {
            size_t fillEnd = end;
            const double ff = std::ceil(ev_[0].time * sr);
            if ((double)end > ff) fillEnd = (size_t)ff;
            size_t fill = std::min(fillEnd - start, n);
            std::fill(values, values + fill, def);
            w = fill; cur += fill;
        }
        float value = def;
        size_t skipped = 0;
        for (size_t i = 0; i < ev_.size() && w < n; i++) {
            const Ev& e = ev_[i];
            const Ev* nx = i + 1 < ev_.size() ? &ev_[i + 1] : nullptr;
            if (nx && !(nx->time * sr >= (double)cur)) { skipped++; continue; }   // IsEventCurrent (a SetTarget)
            const double time2 = nx ? nx->time : end / sr + 1;
            const size_t fillEnd = (double)end > time2 * sr ? (size_t)std::ceil(time2 * sr) : end;
            const size_t fill = std::min(fillEnd - start, n);
            processSetTarget(fill, e.time, e.target, (float)e.tau, sr, fillEnd, values, cur, value, w);
        }
        if (skipped) ev_.erase(ev_.begin(), ev_.begin() + skipped);
        std::fill(values + w, values + n, value);
    }
    static void processSetTarget(size_t fill, double time1, float target, float tc, double sr, size_t fillEnd, float* values,
                                 size_t& cur, float& value, size_t& w) {
        const float c = (float)cr::au::DiscreteTimeConstantForSampleRate(tc, sr);
        {
            const double r = time1 * sr;
            if (r <= (double)cur && (double)cur < r + 1) value = target + (value - target) * fdlibm::exp(-((double)cur / sr - time1) / tc);
            else value += (target - value) * c;
        }
        if (converged(value, target, cur / sr, time1, tc)) {
            cur += fill - w;
            std::fill(values + w, values + fill, target);
            w = fill;
            return;
        }
#if defined(__x86_64__) || defined(_M_X64) || defined(__i386__)
        if (fill > w) {
            const float c0 = c, c1 = c0 * (2 - c0), c2 = c0 * ((c0 - 3) * c0 + 3), c3 = c0 * (c0 * ((4 - c0) * c0 - 6) + 4);
            const size_t trunc = w + ((fill - w) / 4) * 4;
            for (; w < trunc; w += 4) {
                const float delta = target - value;
                // _mm_add_ps(value, _mm_mul_ps(delta, {0, c0, c1, c2}))
                const float p0 = delta * 0.f, p1 = delta * c0, p2 = delta * c1, p3 = delta * c2;
                values[w] = value + p0; values[w + 1] = value + p1; values[w + 2] = value + p2; values[w + 3] = value + p3;
                value += delta * c3;
            }
        }
#endif
        for (; w < fill; w++) { const float v = value; value += (target - value) * c; values[w] = v; }
        if (w >= 1) value = values[w - 1];
        cur = fillEnd;
    }
    float value_, min_, max_;
    std::vector<Ev> ev_;
};

// Chromium's Delay (one channel), the a-rate path for one render quantum
class DelayKernel {
public:
    DelayKernel(double maxDelay, float sr, unsigned Q) : sr_(sr), buf_(Q + cr::timeToSampleFrameUp(maxDelay, sr), 0.f) {}
    void process(const float* src, const float* dt, float* dst, size_t n) {
        const size_t L = buf_.size();
        // CopyToCircularBuffer
        const size_t rem = L - w_, first = std::min(n, rem);
        std::copy(src, src + first, buf_.begin() + w_);
        if (n > rem) std::copy(src + rem, src + n, buf_.begin());
        const size_t vec = (n / 4) * 4;
        const float Lf = (float)L;
        size_t k = 0;
        for (; k < vec; k++) {
            size_t wi = w_ + k; if (wi >= L) wi -= L;
            const float delay = dt[k] > 0.f ? dt[k] : 0.f;   // _mm_max_ps(delay, 0)
            const float desired = delay * sr_;
            float rp = (float)(int32_t)wi + (Lf - desired);
            if (rp >= Lf) rp -= Lf;
            int32_t r1 = (int32_t)rp; if (r1 >= (int32_t)L) r1 -= (int32_t)L;
            int32_t r2 = r1 + 1; if (r2 >= (int32_t)L) r2 -= (int32_t)L;
            const float f = rp - (float)r1;
            const float s1 = buf_[(size_t)r1], s2 = buf_[(size_t)r2];
            dst[k] = s1 + f * (s2 - s1);
        }
        size_t wi = w_ + k; if (wi >= L) wi -= L;
        for (; k < n; k++) {   // ProcessARateScalar
            double delay_time = std::fmax((double)dt[k], 0);
            double desired = delay_time * (double)sr_;
            double rp = (double)wi + (double)L - desired;
            if (rp >= (double)L) rp -= (double)L;
            size_t r1 = (size_t)rp, r2 = r1 + 1; if (r2 >= L) r2 -= L;
            const float f = (float)(rp - (double)r1);
            const float s1 = buf_[r1], s2 = buf_[r2];
            if (++wi >= L) wi -= L;
            dst[k] = s1 + f * (s2 - s1);
        }
        w_ = wi;
    }

private:
    float sr_;
    std::vector<float> buf_;
    size_t w_ = 0;
};

struct TDelay : shape::GridDevice {
    struct Side {
        std::unique_ptr<DelayKernel> d;
        cr::BiquadNode hp, lp;
        cr::WaveShaper sh;
        SetTargetParam dt{0.f, 0.f, 4.f};
        std::vector<float> prev, cur, tmp, times, in;
        bool prevOn = false;
        Side(double sr, unsigned Q) : d(new DelayKernel(4, (float)sr, Q)), hp(sr), lp(sr), sh(Q), prev(Q, 0.f), cur(Q), tmp(Q), times(Q), in(Q) {
            hp.setType(cr::BiquadType::Highpass); lp.setType(cr::BiquadType::Lowpass); sh.setOversample(cr::Oversample::None);
        }
    };
    unsigned Q;
    Side S[2];
    cr::Oscillator lfo;
    float gOg = 1, gInL = 1, gInR = 1, gSelf = 0, gCross = 0, gLg = 0, gLg2 = 0, gWet = 1;
    double setFrame = 0;   // the quantum holding the .value events (sample-accurate GainNodes)
    bool built = false;
    std::vector<float> a_, b_, c_, l1_, l2_, o_;

    explicit TDelay(RenderContext& c) : GridDevice(c, (unsigned)std::max(1, c.quantum)), Q((unsigned)std::max(1, c.quantum)),
        S{Side(c.sampleRate, Q), Side(c.sampleRate, Q)}, lfo((float)c.sampleRate, cr::OscType::Sine) {
        lfo.sched.startAt(0, 0);
        for (auto* v : {&a_, &b_, &c_, &l1_, &l2_, &o_}) v->assign(Q, 0.f);
    }
    static double syncs(const std::string& s) {   // SYNCS (undefined: NaN)
        return s == "1/2" ? 2 : s == "1/4" ? 1 : s == "1/4 dotted" ? 1.5 : s == "1/4 triplet" ? 2.0 / 3 : s == "1/8" ? .5 :
               s == "1/8 dotted" ? .75 : s == "1/8 triplet" ? 1.0 / 3 : s == "1/16" ? .25 : s == "free" ? 0 : NAN;
    }
    void apply() {
        const JValue& sy = p.at("sync");
        const bool synced = Params::truthy(sy) && !(sy.t == JValue::String && sy.s == "free");
        const double tm = synced ? (sy.t == JValue::String ? syncs(sy.s) : NAN) * 60 / ctx.bpm : p.num("time");
        const double fb = p.num("feedback") / 100, wd = p.num("width") / 100;
        const double now = std::floor(ctx.currentFrame / Q) * Q / ctx.sampleRate;   // c.currentTime at the quantum
        S[0].dt.setTarget(tm, now, .05);
        S[1].dt.setTarget(tm * (1 + wd * .06), now, .05);
        const double k = 1 + p.num("drive") / 100 * 6;
        std::vector<float> cv(256);
        for (int j = 0; j < 256; j++) { const double x = j / 127.5 - 1; cv[j] = (float)(fdlibm::tanh(x * k) / fdlibm::tanh(k)); }
        const bool ping = Params::truthy(p.at("ping"));
        for (auto& X : S) {
            X.hp.setFrequency(p.num("lowcut")); X.lp.setFrequency(p.num("highcut"));
            X.sh.setCurve(cv);
        }
        gSelf = ping ? 0.f : (float)fb; gCross = ping ? (float)fb : 0.f;
        gInL = 1; gInR = ping ? 0.f : 1.f;
        lfo.setFrequency(p.num("rate"), now);
        gLg = (float)(p.num("wow") / 100 * .004); gLg2 = (float)(-p.num("wow") / 100 * .004 * wd);
        gWet = (float)(p.num("mix") / 100);
        setFrame = now * ctx.sampleRate;
        gOg = shape::ogGain(p);
    }
    void ensure() override { if (!built) { built = true; apply(); } }
    void set(const JValue& np) override { Processor::set(np); built = true; apply(); }

    // a GainNode: returns whether its output is non-silent
    static bool gain(float g, const float* in, bool inOn, float* out, size_t n, bool sa) {
        if (!inOn) { std::fill(out, out + n, 0.f); return false; }
        if (sa) { for (size_t i = 0; i < n; i++) out[i] = in[i] * g; return true; }
        if (g == 0.f) { std::fill(out, out + n, 0.f); return false; }
        if (g == 1.f) { if (out != in) std::copy(in, in + n, out); return true; }
        for (size_t i = 0; i < n; i++) out[i] = in[i] * g;
        return true;
    }
    // an input with several connections: silent ones skipped, the first copied, the rest added in order
    static void sum(float* out, size_t n, std::initializer_list<std::pair<const float*, bool>> ins) {
        bool any = false;
        for (auto& x : ins) {
            if (!x.second) continue;
            if (!any) { std::copy(x.first, x.first + n, out); any = true; }
            else for (size_t i = 0; i < n; i++) { float v = out[i]; v += x.first[i]; out[i] = v; }
        }
        if (!any) std::fill(out, out + n, 0.f);
    }
    // the delay time of side X for this quantum, with its LFO GainNode summed in
    void delayTimes(Side& X, size_t qs, const float* lfoOut, bool lfoOn, float g, bool sa) {
        X.dt.quantum(qs, Q, ctx.sampleRate, Q, X.times.data());
        if (gain(g, lfoOut, lfoOn, o_.data(), Q, sa)) for (size_t i = 0; i < Q; i++) X.times[i] = X.times[i] + o_[i];
        for (size_t i = 0; i < Q; i++) { float v = X.times[i]; if (std::isnan(v)) v = 0.f; X.times[i] = X.dt.clampF(v); }
    }
    void side(Side& X, const float* in, size_t qs, const float* lfoOut, bool lfoOn, float g, bool sa) {
        delayTimes(X, qs, lfoOut, lfoOn, g, sa);
        X.d->process(in, X.times.data(), X.tmp.data(), Q);
        { const float* i1[1] = {X.tmp.data()}; float* o1[1] = {X.in.data()}; X.hp.process(i1, o1, 1, (int)Q); }
        { const float* i1[1] = {X.in.data()}; float* o1[1] = {X.tmp.data()}; X.lp.process(i1, o1, 1, (int)Q); }
        for (unsigned o = 0; o < Q; o += X.sh.subBlock()) {   // the shaper in its sub-blocks (128 when Q is 512)
            const float* i2[1] = {X.tmp.data() + o}; float* o2[1] = {X.cur.data() + o};
            X.sh.processSubBlock(i2, o2, 1);
        }
    }
    void block(float* L, float* R, double frame) override {
        const size_t qs = (size_t)frame;
        const bool sa = std::floor(frame / Q) == std::floor(setFrame / Q);
        Side &A = S[0], &B = S[1];
        // the LFO (pulled by R.d's delay time first; one output for both)
        std::vector<float>& lfoOut = l1_;
        const bool lfoOn = lfo.process(qs, Q, lfoOut.data());
        // inL, inR from the splitter (a mono input: the right output is silent)
        const bool mono = monoIn;
        const bool inLOn = gain(gInL, L, true, A.in.data(), Q, sa);
        const bool inROn = gain(gInR, R, !mono, B.in.data(), Q, sa);
        // The app connects L.sh -> R.cross -> L.d and R.sh -> L.cross -> R.d: each "cross" GainNode feeds its own
        // side's shaper back into its own delay (so with ping-pong on, inR at 0, the right side stays silent: the web
        // engine's own sound, kept). Both loops read the previous quantum of their shaper (stale when re-entered);
        // the merger pulls the left side first.
        const bool lsOn = gain(gSelf, A.prev.data(), A.prevOn, a_.data(), Q, sa);
        const bool rcOn = gain(gCross, A.prev.data(), A.prevOn, c_.data(), Q, sa);
        sum(l2_.data(), Q, {{A.in.data(), inLOn}, {a_.data(), lsOn}, {c_.data(), rcOn}});
        side(A, l2_.data(), qs, lfoOut.data(), lfoOn, gLg, sa);
        const bool rsOn = gain(gSelf, B.prev.data(), B.prevOn, b_.data(), Q, sa);
        const bool lcOn = gain(gCross, B.prev.data(), B.prevOn, c_.data(), Q, sa);
        sum(l2_.data(), Q, {{B.in.data(), inROn}, {b_.data(), rsOn}, {c_.data(), lcOn}});
        side(B, l2_.data(), qs, lfoOut.data(), lfoOn, gLg2, sa);
        // merger -> wet -> out (in copied, wet added)
        const bool wOn = gain(gWet, A.cur.data(), true, a_.data(), Q, sa);
        gain(gWet, B.cur.data(), true, b_.data(), Q, sa);
        for (size_t i = 0; i < Q; i++) {
            const float dl = L[i], dr = mono ? L[i] : R[i];
            if (wOn) { float x = dl; x += a_[i]; float y = dr; y += b_[i]; L[i] = x; R[i] = y; }
            else { L[i] = dl; R[i] = dr; }
        }
        if (gOg != 1.f) for (size_t i = 0; i < Q; i++) { L[i] = L[i] * gOg; R[i] = R[i] * gOg; }
        std::swap(A.prev, A.cur); std::swap(B.prev, B.cur); A.prevOn = B.prevOn = true;
    }
    bool keepsMono() const override { return false; }
    std::vector<std::pair<std::string, double>> meters() const override {
        return {{"addedLatency", (double)addedLatency()}};
    }
};

}  // namespace tdl
}  // namespace al
