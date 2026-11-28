// Chromium's AudioParam timeline, ported for the native engine (task NB-N3j).
//
// Every automated value in the web engine goes through it: the clips' volume, pan and filter envelopes (schedEnv:
// setValueAtTime then linearRampToValueAtTime), the fades (setValueCurveAtTime), the instruments' envelopes, the
// Kick's choke (setValueAtTime, then a 4 ms ramp to 0), the Timeless delay's glide (setTargetAtTime). A statement-by-
// statement port of modules/webaudio/audio_param_handler.cc and audio_param.cc in Chromium 158.0.8127.36:
//   - the value setter: param.value = v clamps v, stores it, and also inserts setValueAtTime(v, currentTime)
//     (AudioParam::setValue), so a value set before rendering is an event at time 0;
//   - InsertEvent (events kept sorted by time, a later event at the same time goes after the earlier ones; past
//     events dropped first; a ramp into an empty list gets a SetValue of the current value at the current time),
//     ClampNewEventsToCurrentTime, HandleAllEventsInThePast (at least one event always kept), HandleFirstEvent,
//     IsEventCurrent, ProcessSetTargetFollowedByRamp;
//   - ProcessLinearRamp, ProcessExponentialRamp, ProcessSetTarget, ProcessSetValueCurve with their x86 vector paths
//     (four frames at a time in float, as Chromium's SSE code does) and the scalar paths (ARM, and the rest);
//   - HasSampleAccurateValues (decides whether a node takes the per-frame path in a render quantum),
//     ValueForContextTime / FinalValue (the k-rate value of a quantum, at the control rate), Vclip to the range.
// Not ported: cancelScheduledValues and cancelAndHoldAtTime (the app's export does not call them), connections into
// a param (those are summed by the node that owns it: dev_side.h, the LFOs).
// Build with -ffp-contract=off.
#pragma once
#include <algorithm>
#include <cmath>
#include <cstddef>
#include <limits>
#include <memory>
#include <set>
#include <vector>
#include "../../third_party/fdlibm/ieee754.h"

namespace al {
namespace cr {
namespace au {
// audio_utilities.cc
inline double DiscreteTimeConstantForSampleRateTL(double time_constant, double sample_rate) {
    return 1 - fdlibm::exp(-1 / (sample_rate * time_constant));
}
}  // namespace au

class ParamTimeline {
public:
    enum class Type { SetValue, LinearRamp, ExpRamp, SetTarget, SetValueCurve, SetValueCurveEnd, Last };
    struct Event {
        Type type;
        float value = 0;
        double time = 0;
        float initial = 0;
        double callTime = 0;
        double tc = 0;          // time constant
        double duration = 0;
        double pointsPerSecond = 0;
        float curveEnd = 0;
        std::vector<float> curve;
    };

    ParamTimeline(float defaultValue, float minValue, float maxValue, bool audioRate = true)
        : intrinsic_(defaultValue), default_(defaultValue), min_(minValue), max_(maxValue), aRate_(audioRate) {}

    float intrinsic() const { return intrinsic_; }
    float defaultValue() const { return default_; }
    bool audioRate() const { return aRate_; }
    void setAudioRate(bool a) { aRate_ = a; }

    // ---- the page's calls (now: the context's currentTime in seconds) ----
    // AudioParam.value = v
    void setValue(double v, double now) { setIntrinsic((float)v); setValueAtTime(intrinsic_, now, now); }
    void setValueAtTime(double v, double t, double now) {
        if (!(t >= 0)) return;
        Event e; e.type = Type::SetValue; e.value = (float)v; e.time = std::max(t, now);
        insert(std::move(e), now);
    }
    void linearRampToValueAtTime(double v, double t, double now) {
        if (!(t >= 0)) return;
        Event e; e.type = Type::LinearRamp; e.value = (float)v; e.time = std::max(t, now); e.initial = intrinsic_; e.callTime = now;
        insert(std::move(e), now);
    }
    void exponentialRampToValueAtTime(double v, double t, double now) {
        if (!(t >= 0) || (float)v == 0) return;
        Event e; e.type = Type::ExpRamp; e.value = (float)v; e.time = std::max(t, now); e.initial = intrinsic_; e.callTime = now;
        insert(std::move(e), now);
    }
    void setTargetAtTime(double target, double t, double tc, double now) {
        if (!(t >= 0) || !(tc >= 0)) return;
        Event e; e.time = std::max(t, now);
        if (tc == 0) { e.type = Type::SetValue; e.value = (float)target; }
        else { e.type = Type::SetTarget; e.value = (float)target; e.tc = tc; }
        insert(std::move(e), now);
    }
    // the curve as the page gives it (a Float32Array: floats)
    bool setValueCurveAtTime(const std::vector<float>& curve, double t, double duration, double now) {
        if (!(t >= 0) || !(duration > 0) || curve.size() < 2) return false;
        Event e; e.type = Type::SetValueCurve; e.time = std::max(t, now); e.duration = duration; e.curve = curve;
        e.pointsPerSecond = (curve.size() - 1) / duration; e.curveEnd = curve.back();
        const double end = e.time + duration;
        const float last = curve.back();
        if (!insert(std::move(e), now)) return false;
        Event f; f.type = Type::SetValueCurveEnd; f.value = last; f.time = end;
        insert(std::move(f), now);
        return true;
    }

    // ---- the audio thread ----
    // HasSampleAccurateValues (no connections into the param)
    bool hasSampleAccurateValues(size_t currentFrame, double sr, unsigned Q) const {
        const size_t n = ev_.size();
        if (n == 0) return false;
        const Event& e0 = *ev_[0];
        if (e0.time > (currentFrame + Q) / sr) {
            if (e0.type == Type::SetTarget || e0.type == Type::SetValue || e0.type == Type::SetValueCurve) return false;
        }
        if (n >= 2) return true;
        switch (e0.type) {
            case Type::SetTarget: return e0.time <= (currentFrame + Q) / sr;
            case Type::SetValue: case Type::LinearRamp: case Type::ExpRamp: case Type::SetValueCurveEnd:
                return !(e0.time < currentFrame / sr);
            case Type::SetValueCurve: {
                const double end = e0.time + e0.duration, now = currentFrame / sr;
                return e0.time <= now && now < end;
            }
            default: return true;
        }
    }
    // CalculateSampleAccurateValues for an a-rate param (CalculateTimelineValues): values for frames start..start+n
    void sampleAccurate(size_t startFrame, float* values, size_t n, double sr, unsigned Q) {
        if (!aRate_) { const float v = finalValue(startFrame, sr, Q); std::fill(values, values + n, v); return; }
        setIntrinsic(valuesForFrameRange(startFrame, startFrame + n, intrinsic_, values, n, sr, sr, Q));
    }
    // FinalValue / Value(): the quantum's k-rate value
    float finalValue(size_t startFrame, double sr, unsigned Q) {
        float value = intrinsic_;
        if (!ev_.empty() && !(startFrame / sr < ev_[0]->time)) {
            float v = 0;
            value = valuesForFrameRange(startFrame, startFrame + 1, intrinsic_, &v, 1, sr, sr / Q, Q);
        }
        setIntrinsic(value);
        return intrinsic_;
    }
    size_t events() const { return ev_.size(); }

private:
    static constexpr float kTimeConstantsToConverge = 10.0f;
    static constexpr float kSetTargetThreshold = 4.539992976248485e-05f;
    using EvP = std::unique_ptr<Event>;

    void setIntrinsic(float v) { intrinsic_ = v < min_ ? min_ : v > max_ ? max_ : v; }   // ClampTo (NaN stays)
    static bool converged(float value, float target, double now, double start, double tc) {
        if (now > start + kTimeConstantsToConverge * tc) return true;
        if (target == 0 && std::fabs(value) < kSetTargetThreshold) return true;
        if (target != 0 && std::fabs(target - value) < kSetTargetThreshold * std::fabs(value)) return true;
        return false;
    }
    static bool isCurrent(const Event* e, const Event* next, size_t frame, double sr) {
        if (!next) return true;
        if (next->time * sr >= (double)frame) return true;
        const double ef = e->time * sr;
        return (e->type == Type::SetValue || e->type == Type::SetValueCurveEnd) && ef <= (double)frame && (double)frame < ef + 1;
    }
    void removeOld(size_t count) {
        const size_t n = ev_.size();
        if (n > 1) {
            const size_t r = std::min(count, n - 1);
            for (size_t k = 0; k < r; k++) newEv_.erase(ev_[k].get());
            ev_.erase(ev_.begin(), ev_.begin() + r);
        }
    }
    bool insert(Event e, double now) {
        const double t = e.time;
        if (!ev_.empty()) {
            const size_t frame = currentFrameOf(now);
            size_t skipped = 0;
            for (size_t i = 0; i < ev_.size(); i++) {
                const Event* nx = i + 1 < ev_.size() ? ev_[i + 1].get() : nullptr;
                if (isCurrent(ev_[i].get(), nx, frame, sr_)) break;
                skipped++;
            }
            if (skipped) removeOld(skipped);
        }
        if (ev_.empty() && (e.type == Type::LinearRamp || e.type == Type::ExpRamp)) {
            EvP s(new Event); s->type = Type::SetValue; s->value = e.initial; s->time = now;
            newEv_.insert(s.get()); ev_.insert(ev_.begin(), std::move(s));
        }
        if (ev_.empty()) { EvP p(new Event(std::move(e))); newEv_.insert(p.get()); ev_.push_back(std::move(p)); return true; }
        size_t idx = ev_.size();
        long ub = (long)idx - 1;
        if (ev_.back()->time > t) {
            idx = (size_t)(std::upper_bound(ev_.begin(), ev_.end(), t, [](double v, const EvP& x) { return v < x->time; }) - ev_.begin());
            ub = (long)idx;
        }
        if (e.type == Type::SetValueCurve) {
            const double end = e.time + e.duration;
            for (long i = ub; i >= 0; i--) {
                const Event& x = *ev_[(size_t)i];
                if (x.type == Type::SetValueCurveEnd) continue;
                if (x.type == Type::SetValueCurve) {
                    const double te = x.time + x.duration;
                    if (e.time < te && x.time < end) return false;
                } else if (x.time > e.time && x.time < end) return false;
                if (x.time < t) break;
            }
        } else {
            for (long i = ub; i >= 0; i--) {
                const Event& x = *ev_[(size_t)i];
                if (x.type == Type::SetValueCurveEnd) continue;
                if (x.type == Type::SetValueCurve) {
                    const double te = x.time + x.duration;
                    if (e.type != Type::SetValueCurveEnd && e.time >= x.time && e.time < te) return false;
                }
                if (x.time < t) break;
            }
        }
        EvP p(new Event(std::move(e)));
        newEv_.insert(p.get());
        ev_.insert(ev_.begin() + idx, std::move(p));
        return true;
    }
    // the destination's current frame for a call made at `now` (calls between quanta: the quantum boundary)
    size_t currentFrameOf(double now) const { return (size_t)std::llround(now * sr_); }

public:
    // the context's rate, for the page's calls (set once by the node's owner)
    void setSampleRate(double sr) { sr_ = sr; }

private:
    float valuesForFrameRange(size_t start, size_t end, float def, float* values, size_t n, double sr, double controlRate, unsigned Q) {
        impl(start, end, def, values, n, sr, controlRate, Q);
        for (size_t i = 0; i < n; i++) { float x = values[i]; x = x < max_ ? x : max_; values[i] = x > min_ ? x : min_; }   // Vclip
        return values[n - 1];
    }
    void clampNew(double now) {
        bool any = false;
        for (Event* e : newEv_) {
            if (e->type == Type::SetValueCurve || e->type == Type::SetValueCurveEnd) continue;
            if (e->time < now) { e->time = now; any = true; }
        }
        if (any) std::stable_sort(ev_.begin(), ev_.end(), [](const EvP& a, const EvP& b) { return a->time < b->time; });
        newEv_.clear();
    }
    bool allInThePast(double now, double sr, float& def, float* values, size_t n, unsigned Q) {
        const Event& last = *ev_.back();
        if (last.time + 1.5 * Q / sr < now) {
            if (last.type == Type::SetTarget) {
                if (converged(def, last.value, now, last.time, last.tc)) def = last.value;
                else return false;
            }
            std::fill(values, values + n, def);
            removeOld(ev_.size());
            return true;
        }
        return false;
    }
    void impl(size_t start, size_t end, float def, float* values, size_t n, double sr, double controlRate, unsigned Q) {
        if (ev_.empty() || (end / sr <= ev_[0]->time)) { std::fill(values, values + n, def); return; }
        size_t nev = ev_.size();
        if (!newEv_.empty()) clampNew(start / sr);
        if (nev > 0 && allInThePast(start / sr, sr, def, values, n, Q)) return;
        size_t cur = start, w = 0;
        // HandleFirstEvent
        {
            const double t0 = ev_[0]->time;
            if (t0 > start / sr) {
                size_t fe = end;
                const double ff = std::ceil(t0 * sr);
                if ((double)end > ff) fe = (size_t)ff;
                size_t fill = std::min(fe - start, n);
                std::fill(values + w, values + fill, def);
                w = fill; cur += fill;
            }
        }
        float value = def;
        size_t skipped = 0;
        for (size_t i = 0; i < nev && w < n; ++i) {
            Event* e = ev_[i].get();
            Event* nx = i + 1 < nev ? ev_[i + 1].get() : nullptr;
            if (!isCurrent(e, nx, cur, sr)) { skipped++; continue; }
            // ProcessSetTargetFollowedByRamp
            const Type nt = nx ? nx->type : Type::Last;
            if (e->type == Type::SetTarget && (nt == Type::LinearRamp || nt == Type::ExpRamp)) {
                if (std::fabs(2 * sr * e->time - 2 * (double)cur + 1) <= 1)
                    value = e->value + (value - e->value) * fdlibm::exp(-((double)cur / sr - e->time) / e->tc);
                else {
                    const float dc = (float)au::DiscreteTimeConstantForSampleRateTL(e->tc, controlRate);
                    value += (e->value - value) * dc;
                }
                EvP s(new Event); s->type = Type::SetValue; s->value = value; s->time = (double)cur / sr;
                newEv_.erase(e);
                ev_[i] = std::move(s);
                e = ev_[i].get();
            }
            const float value1 = e->value;
            const double time1 = e->time;
            const float value2 = nx ? nx->value : value1;
            const double time2 = nx ? nx->time : end / sr + 1;
            const size_t fillEnd = (double)end > time2 * sr ? (size_t)std::ceil(time2 * sr) : end;
            const size_t fill = std::min(fillEnd - start, n);
            if (nt == Type::LinearRamp) linearRamp(fill, time1, time2, value1, value2, sr, values, cur, value, w);
            else if (nt == Type::ExpRamp) expRamp(fill, time1, time2, value1, value2, sr, values, cur, value, w);
            else {
                switch (e->type) {
                    case Type::SetValue: case Type::SetValueCurveEnd: case Type::LinearRamp: case Type::ExpRamp:
                        cur = fillEnd; value = e->value;
                        std::fill(values + w, values + fill, value); w = fill;
                        break;
                    case Type::SetTarget: setTarget(fill, time1, value1, sr, controlRate, fillEnd, e, values, cur, value, w); break;
                    case Type::SetValueCurve: valueCurve(fill, time1, sr, start, end, fillEnd, e, values, n, cur, value, w); break;
                    default: break;
                }
            }
        }
        if (skipped) removeOld(skipped);
        std::fill(values + w, values + n, value);
    }
    static void linearRamp(size_t fill, double time1, double time2, float value1, float value2, double sr, float* values,
                           size_t& cur, float& value, size_t& w) {
        const double dt = time2 - time1;
        const float k = dt <= std::numeric_limits<float>::min() ? 0.f : (float)(1 / dt);
        const float vd = value2 - value1;
#if defined(__x86_64__) || defined(_M_X64) || defined(__i386__)
        if (fill > w) {
            const float inv = (float)(1 / sr), off = (float)((double)cur / sr - time1), kv = k * vd, v1 = value1;
            float v[4];
            for (int j = 0; j < 4; j++) { float x = inv * (float)j; x = x + off; x = x * kv; v[j] = x + v1; }   // mul, add, mul, add
            const float inc = (float)(4 / sr * (double)k * (double)vd);
            const size_t trunc = w + ((fill - w) / 4) * 4;
            cur += trunc - w;
            for (; w < trunc; w += 4) { for (int j = 0; j < 4; j++) { values[w + j] = v[j]; v[j] = v[j] + inc; } }
        }
        if (w >= 1) value = values[w - 1];
#endif
        for (; w < fill; w++) {
            const float x = (float)(((double)cur / sr - time1) * (double)k);
            value = value1 + x * vd;
            ++cur;
            values[w] = value;
        }
    }
    static void expRamp(size_t fill, double time1, double time2, float value1, float value2, double sr, float* values,
                        size_t& cur, float& value, size_t& w) {
        if (value1 * value2 <= 0 || time1 >= time2) { value = value1; std::fill(values + w, values + fill, value); w = fill; return; }
        const double dt = time2 - time1, nf = dt * sr;
        const double mult = fdlibm::pow(value2 / value1, 1.0 / nf);
        value = (float)(value1 * fdlibm::pow(value2 / (double)value1, ((double)cur / sr - time1) / dt));
        double acc = value;
        for (; w < fill; w++) { value = (float)acc; acc *= mult; ++cur; values[w] = value; }
        if ((double)cur > time2 * sr - 0.5) value = value2;
    }
    static void setTarget(size_t fill, double time1, float value1, double sr, double controlRate, size_t fillEnd, const Event* e,
                          float* values, size_t& cur, float& value, size_t& w) {
        const float target = value1;
        const float tc = (float)e->tc;
        const float dc = (float)au::DiscreteTimeConstantForSampleRateTL(tc, controlRate);
        {
            const double rs = time1 * sr;
            if (rs <= (double)cur && (double)cur < rs + 1) value = target + (value - target) * fdlibm::exp(-((double)cur / sr - time1) / tc);
            else value += (target - value) * dc;
        }
        if (converged(value, target, (double)cur / sr, time1, tc)) {
            cur += fill - w;
            std::fill(values + w, values + fill, target);
            w = fill;
            return;
        }
#if defined(__x86_64__) || defined(_M_X64) || defined(__i386__)
        if (fill > w) {
            const float c0 = dc, c1 = c0 * (2 - c0), c2 = c0 * ((c0 - 3) * c0 + 3), c3 = c0 * (c0 * ((4 - c0) * c0 - 6) + 4);
            const size_t trunc = w + ((fill - w) / 4) * 4;
            for (; w < trunc; w += 4) {
                const float delta = target - value;
                const float p0 = delta * 0.f, p1 = delta * c0, p2 = delta * c1, p3 = delta * c2;
                values[w] = value + p0; values[w + 1] = value + p1; values[w + 2] = value + p2; values[w + 3] = value + p3;
                value += delta * c3;
            }
        }
#endif
        for (; w < fill; w++) { const float v = value; value += (target - value) * dc; values[w] = v; }
        if (w >= 1) value = values[w - 1];
        cur = fillEnd;
    }
    static void valueCurve(size_t fill, double time1, double sr, size_t start, size_t end, size_t fillEnd, const Event* e, float* values,
                           size_t n, size_t& cur, float& value, size_t& w) {
        const std::vector<float>& c = e->curve;
        const float cev = e->curveEnd;
        const double duration = e->duration, ppf = e->pointsPerSecond / sr;
        if (c.empty() || duration <= 0 || sr <= 0) { cur = fillEnd; std::fill(values + w, values + fill, value); w = fill; return; }
        const size_t nextFill = fill;
        {
            const double cef = std::ceil(sr * (time1 + duration));
            fillEnd = (double)end > cef ? (size_t)cef : end;
        }
        fill = fillEnd < start ? 0 : fillEnd - start;
        fill = std::min({fill, n, nextFill});
        double cvi = 0;
        if (time1 < (double)cur / sr) cvi = ppf * ((double)cur - time1 * sr);
        value = cev;
        size_t k = 0;
#if defined(__x86_64__) || defined(_M_X64) || defined(__i386__)
        if (fill > w) {
            const float vcvi = (float)cvi, vppf = (float)ppf, nm1 = (float)(c.size() - 1);
            float vk[4] = {0, 1, 2, 3};
            const size_t steps = ((fill - w) / 4) * 4, trunc = w + steps;
            for (; w < trunc; w += 4) {
                for (int j = 0; j < 4; j++) {
                    float pr = vk[j] * vppf; const float cvx = vcvi + pr;
                    vk[j] = vk[j] + 4.0f;
                    const float m0 = cvx < nm1 ? cvx : nm1;   // _mm_min_ps(a, b): a < b ? a : b
                    const float a1 = cvx + 1.0f;
                    const float m1 = a1 < nm1 ? a1 : nm1;
                    const int i0 = cvtt(m0), i1 = cvtt(m1);
                    const float c0 = c[(size_t)i0], c1 = c[(size_t)i1];
                    float d = cvx - (float)i0; d = d < 1.0f ? d : 1.0f;
                    float diff = c1 - c0; diff = diff * d;
                    values[w + j] = c0 + diff;
                }
            }
            k = steps;
        }
        if (w >= 1) value = values[w - 1];
#endif
        for (; w < fill; w++) {
            const double cv = cvi + (double)k * ppf;
            size_t i0 = cv < (double)c.size() ? (size_t)cv : c.size() - 1;
            const size_t i1 = std::min(i0 + 1, c.size() - 1);
            const float c0 = c[i0], c1 = c[i1];
            const double d = std::min(cv - (double)i0, 1.0);
            ++k;
            value = (float)(c0 + (c1 - c0) * d);
            values[w] = value;
        }
        w = fill;
        if (w < nextFill) { value = cev; std::fill(values + w, values + nextFill, value); w = nextFill; }
        cur += nextFill;
    }
    static int cvtt(float x) {   // _mm_cvttps_epi32: truncation, out of range or NaN gives INT_MIN
        if (std::isnan(x) || x >= 2147483648.0f || x < -2147483648.0f) return std::numeric_limits<int>::min();
        return (int)x;
    }

    float intrinsic_, default_, min_, max_;
    bool aRate_;
    double sr_ = 48000;
    std::vector<EvP> ev_;
    std::set<Event*> newEv_;
};

}  // namespace cr
}  // namespace al
