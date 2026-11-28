// Chromium's AudioBufferSourceNode, ported for the native engine (task NB-N3j).
//
// The web engine plays every recorded or pre-rendered sound through one: audio clips (with an offset into the file
// and a duration), the Kick and the drum machines (a rendered hit at the note's time), the note cache, sampler
// slices. A statement-by-statement port of Chromium 158.0.8127.36's modules/webaudio/audio_buffer_source_handler.cc
// (Process, RenderFromBuffer, ProcessFastPath, ProcessInterpolatedPath, StartSource, ClampGrainParameters,
// ComputePlaybackRate, UpdateEffectiveLoopPoints) and audio_scheduled_source_handler.cc (UpdateSchedulingInfo):
//   - a start time between two frames starts on the next frame and reads the buffer that much later, so the
//     whole hit is interpolated (in double, stored as float): a note at 1.3824 s is not the same samples as one at
//     1.3824 s rounded to a frame;
//   - a buffer at another rate than the context plays at the ratio of the two (44.1 kHz files in a 48 kHz project);
//   - playbackRate and detune are k-rate (their FinalValue per quantum), the rate clamped to +-1024;
//   - the offset and duration of start(when, offset, duration), the end of the buffer, stop().
// Loops are ported (the sampler's), not yet tested against the browser.
#pragma once
#include <algorithm>
#include <cmath>
#include <limits>
#include <memory>
#include <vector>
#include "../../third_party/fdlibm/ieee754.h"
#include "timeline.h"
#include "webnodes.h"

namespace al {
namespace cr {

// An AudioBuffer: channels of floats at a rate
struct AudioBufferData {
    float sampleRate = 48000;
    std::vector<std::vector<float>> ch;
    size_t length() const { return ch.empty() ? 0 : ch[0].size(); }
    double duration() const { return length() / (double)sampleRate; }
};

class BufferSource {
public:
    static constexpr double kMaxRate = 1024;
    BufferSource(double contextRate, unsigned quantum)
        : sr_(contextRate), Q_(quantum), rate_(1, -3.4028235e38f, 3.4028235e38f, false), detune_(0, -153600, 153600, false) {
        rate_.setSampleRate(contextRate); detune_.setSampleRate(contextRate);
    }
    ParamTimeline& playbackRate() { return rate_; }
    ParamTimeline& detune() { return detune_; }
    void setBuffer(std::shared_ptr<const AudioBufferData> b) {
        buf_ = std::move(b);
        loopPoints();
        if (sched_.state != Schedule::Unscheduled) clampGrain();
    }
    void setLoop(bool l, double loopStart = 0, double loopEnd = 0) { loop_ = l; loopStart_ = loopStart; loopEnd_ = loopEnd; loopPoints(); }
    // start(when, offset, duration): durationGiven false for start(when) / start(when, offset)
    void start(double when, double offset = 0, double duration = 0, bool durationGiven = false, double now = 0) {
        if (sched_.state != Schedule::Unscheduled || when < 0 || offset < 0 || duration < 0) return;
        durGiven_ = durationGiven; grainOffset_ = offset; grainDur_ = duration;
        sched_.startAt(when, now);
        if (buf_) clampGrain();
    }
    void stop(double when) { sched_.stopAt(when); }
    unsigned channels() const { return buf_ ? (unsigned)buf_->ch.size() : 1u; }
    bool finished() const { return sched_.state == Schedule::Finished; }
    // One render quantum starting at frame qstart: out[c] for each of channels(). Returns false when the output is a
    // silent bus (not started, finished, no buffer: Chromium's Zero()).
    bool process(size_t qstart, float* const* out, size_t frames) {
        const unsigned nch = channels();
        if (!buf_) { zero(out, nch, frames); if (sched_.state != Schedule::Unscheduled) sched_.finish(); return false; }
        size_t off = 0, n = 0; double sfo = 0;
        if (!update(qstart, frames, out, nch, off, n, sfo)) return false;
        if (!n) return true;   // zeroed, not flagged silent? Chromium zeroes the bus (silent) when nothing plays
        if (!render(out, nch, off, n, sfo, qstart, frames)) { zero(out, nch, frames); return false; }
        return true;
    }

private:
    static void zero(float* const* out, unsigned nch, size_t frames) { for (unsigned c = 0; c < nch; c++) std::fill(out[c], out[c] + frames, 0.f); }
    // UpdateSchedulingInfo (several channels)
    bool update(size_t qstart, size_t Q, float* const* out, unsigned nch, size_t& offset, size_t& n, double& sfo) {
        offset = 0; n = 0; sfo = 0;
        const size_t qend = qstart + Q;
        const size_t start_frame = Schedule::toFrame(sched_.start < 0 ? 0 : sched_.start, sr_);
        const size_t end_frame = sched_.end < 0 ? 0 : Schedule::toFrame(sched_.end, sr_);
        if (sched_.end >= 0 && end_frame <= qstart) sched_.finish();
        if (sched_.state == Schedule::Unscheduled || sched_.state == Schedule::Finished || start_frame >= qend) { zero(out, nch, Q); return false; }
        if (sched_.state == Schedule::Scheduled) { sched_.state = Schedule::Playing; sfo = sched_.start * sr_ - (double)start_frame; }
        offset = start_frame > qstart ? start_frame - qstart : 0;
        offset = std::min(offset, Q);
        n = Q - offset;
        if (!n) { zero(out, nch, Q); return false; }
        if (offset) for (unsigned c = 0; c < nch; c++) std::fill(out[c], out[c] + offset, 0.f);
        if (sched_.end >= 0 && end_frame >= qstart && end_frame <= qend) {
            if (end_frame < qend) {
                const size_t zs = end_frame - qstart, tz = Q - zs;
                n = tz > n ? 0 : n - tz;
                for (unsigned c = 0; c < nch; c++) std::fill(out[c] + zs, out[c] + Q, 0.f);
            }
            sched_.finish();
        }
        if (!n) { zero(out, nch, Q); return false; }   // Process(): !buffer_frames_to_process -> output_bus->Zero()
        return true;
    }
    double computeRate(size_t qstart) {
        const double srf = buf_ ? buf_->sampleRate / sr_ : 1.0;
        const double base = rate_.finalValue(qstart, sr_, Q_);
        double r = srf * base;
        r *= fdlibm::pow(2, detune_.finalValue(qstart, sr_, Q_) / 1200);
        r = std::min(std::max(r, -kMaxRate), kMaxRate);
        return r;
    }
    void clampGrain() {
        const double d = buf_->duration();
        grainOffset_ = std::min(std::max(grainOffset_, 0.0), d);
        if (!durGiven_) grainDur_ = std::numeric_limits<double>::infinity();
        else grainDur_ = std::max(grainDur_, 0.0);
        if (rate_.intrinsic() == 1.0f && detune_.intrinsic() == 0.0f) vri_ = (double)toFrameNearest(grainOffset_, buf_->sampleRate);
        else vri_ = grainOffset_ * buf_->sampleRate;
    }
    // audio_utilities::TimeToSampleFrame with its default rounding, kRoundToNearest
    static size_t toFrameNearest(double time, double sr) {
        double frame = ::round(time * sr * 1024.0) / 1024.0;
        frame = ::round(frame);
        if (frame >= (double)std::numeric_limits<size_t>::max()) return std::numeric_limits<size_t>::max();
        return (size_t)frame;
    }
    void loopPoints() {
        if (!buf_) { vls_ = 0; vle_ = 0; return; }
        const double d = buf_->duration(), bsr = buf_->sampleRate, len = (double)buf_->length();
        vls_ = 0; vle_ = len;
        if (!loop_) return;
        const double s = std::min(std::max(loopStart_, 0.0), d);
        const double e = loopEnd_ == 0.0 ? d : std::min(std::max(loopEnd_, 0.0), d);
        if (s < e) {
            if (s > 0) vls_ = s * bsr;   // TimeToFloatingSampleFrame
            if (e < d) vle_ = e * bsr;
        }
        if (vls_ >= vle_) { vls_ = 0; vle_ = len; }
    }
    // RenderFromBuffer
    bool render(float* const* out, unsigned nch, unsigned dstOff, uint32_t frames, double sto, size_t qstart, size_t Q) {
        const uint32_t blen = (uint32_t)buf_->length();
        unsigned w = dstOff;
        const double vs = vls_, ve = vle_, vd = ve - vs;
        const double rate = computeRate(qstart);
        if (std::fabs(rate) > vd) return false;
        double vri = vri_;
        int toProcess = (int)frames;
        if (rate >= 0) {
            if (loop_ && vri >= ve) { vri = vs; vri = std::min(vri, (double)(blen - 1)); vri_ = vri; }
            if (sto < 0 && rate != 0) { const double sk = std::fabs(sto * rate); vri += sk; played_ += sk; }
        } else {
            if (loop_ && vri < vs) { vri = vs; vri_ = vri; }
            if (sto < 0) { const double sk = std::fabs(sto * rate); vri -= sk; played_ += sk; }
            while (toProcess > 0 && vri >= blen) { for (unsigned c = 0; c < nch; c++) out[c][w] = 0.f; ++w; vri += rate; toProcess--; }
        }
        bool stopping = false;
        if (durGiven_) {
            const double maxFrames = grainDur_ * buf_->sampleRate, left = maxFrames - played_;
            if (left <= 0.0) { toProcess = 0; stopping = true; }
            else if (rate != 0.0) {
                const double until = std::ceil(left / std::fabs(rate));
                if (until < toProcess) { toProcess = (int)until; stopping = true; }
            }
        }
        if (!loop_ && ((rate >= 0 && vri >= blen) || (rate < 0 && vri < 0))) {
            vri = std::min(std::max(vri, 0.0), (double)blen);
            toProcess = 0; stopping = true;
        }
        if (rate == 1 && vri == std::floor(vri) && vd == std::floor(vd) && ve == std::floor(ve)) fastPath(vd, ve, blen, nch, toProcess, w, vri, out, Q);
        else interpPath(vs, vd, ve, blen, nch, rate, toProcess, w, vri, out, Q);
        if (rate != 0) played_ += (w - dstOff) * std::fabs(rate);
        if (stopping) { for (unsigned c = 0; c < nch; c++) std::fill(out[c] + w, out[c] + dstOff + frames, 0.f); sched_.finish(); }
        vri_ = vri;
        return true;
    }
    void silenceAndFinish(float* const* out, unsigned nch, size_t idx, size_t n) {
        if (n > 0) for (unsigned c = 0; c < nch; c++) std::fill(out[c] + idx, out[c] + idx + n, 0.f);
        sched_.finish();
    }
    void fastPath(double vd, double ve, uint32_t blen, unsigned nch, int toProcess, unsigned& w, double& vri, float* const* out, size_t) {
        unsigned ri = (unsigned)vri;
        const unsigned dfr = (unsigned)vd, ef = (unsigned)ve;
        while (toProcess > 0) {
            const int toEnd = (int)ef - (int)ri;
            const int now = std::min(std::max(toEnd, 0), toProcess);
            for (unsigned c = 0; c < nch; c++) std::copy(buf_->ch[c].begin() + ri, buf_->ch[c].begin() + ri + now, out[c] + w);
            w += now; ri += now; toProcess -= now;
            double t = ri;
            if (dfr <= 0) { sched_.finish(); break; }
            if (t >= ef) {
                if (!loop_) { silenceAndFinish(out, nch, w, (size_t)toProcess); ri = std::min(ri, blen); break; }
                const double over = t - ef;
                t = ef - dfr + std::fmod(over, (double)dfr);
            }
            ri = (unsigned)t;
        }
        vri = ri;
    }
    void interpPath(double vs, double vd, double ve, uint32_t blen, unsigned nch, double rate, int toProcess, unsigned& w, double& vri,
                    float* const* out, size_t) {
        const unsigned maxIndex = blen - 1;
        for (int i = 0; i < toProcess; ++i) {
            const uint32_t remaining = (uint32_t)(toProcess - i - 1);
            unsigned ri = (unsigned)vri;
            const double f = vri - ri;
            unsigned ri2 = ri + 1;
            if (loop_ && ri < ve && ri2 >= ve) {
                double wrapped = 0.0;
                if (vd >= 1.0) wrapped = vri + 1.0 - vd;
                else if (vd > 0) wrapped = vs + std::fmod(vri + 1.0 - vs, vd);
                else wrapped = vs;
                ri2 = wrapped >= 0 ? (unsigned)wrapped : 0;
            } else if (ri2 >= blen) ri2 = ri;
            ri = std::min(ri, maxIndex);
            ri2 = std::min(ri2, maxIndex);
            for (unsigned c = 0; c < nch; ++c) {
                const std::vector<float>& s = buf_->ch[c];
                double sample;
                if (ri == ri2 && ri >= 1) { const double s1 = s[ri - 1], s2 = s[ri]; sample = s2 + (s2 - s1) * f; }
                else { const double s1 = s[ri], s2 = s[ri2]; sample = (1.0 - f) * s1 + f * s2; }
                out[c][w] = clampToFloat(sample);
            }
            ++w;
            vri += rate;
            if (vd <= 0) { sched_.finish(); break; }
            if (rate >= 0 && vri >= ve) {
                if (!loop_) { silenceAndFinish(out, nch, w, remaining); vri = std::min(vri, (double)blen); break; }
                const double over = vri - ve;
                vri = ve - vd + std::fmod(over, vd);
            } else if (rate < 0 && vri < vs) {
                if (!loop_) { silenceAndFinish(out, nch, w, remaining); vri = std::max(0.0, vri); break; }
                const double over = vs - vri;
                vri = vs + vd - std::fmod(over, vd);
            }
        }
    }
    static float clampToFloat(double v) {   // ClampTo<float>
        if (std::isnan(v)) return 0.f;   // base::saturated_cast: NaN to 0
        if (v > 3.4028234663852886e38) return 3.4028235e38f;
        if (v < -3.4028234663852886e38) return -3.4028235e38f;
        return (float)v;
    }

    double sr_;
    unsigned Q_;
    ParamTimeline rate_, detune_;
    std::shared_ptr<const AudioBufferData> buf_;
    Schedule sched_;
    bool loop_ = false, durGiven_ = false;
    double loopStart_ = 0, loopEnd_ = 0, vls_ = 0, vle_ = 0;
    double grainOffset_ = 0, grainDur_ = std::numeric_limits<double>::infinity();
    double vri_ = 0, played_ = 0;
};

}  // namespace cr
}  // namespace al
