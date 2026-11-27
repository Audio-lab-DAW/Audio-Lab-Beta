// Chromium's DynamicsCompressorNode, ported for the native engine (task NB-N3f).
//
// The app's Compressor ('comp', mkFxNode in index.html) is the browser's own DynamicsCompressorNode, and the
// Sidechain device ('side') uses two more, so their sound is Chromium's arithmetic. This is a statement-by-statement
// port of Chromium 158.0.8127.36:
//   third_party/blink/renderer/platform/audio/dynamics_compressor.cc     the curve, the detector, the envelope
//   third_party/blink/renderer/modules/webaudio/dynamics_compressor_handler.cc   parameters read once per quantum
//   third_party/blink/renderer/platform/audio/audio_utilities.cc         DecibelsToLinear, LinearToDecibels,
//                                                                        DiscreteTimeConstantForSampleRate
// What decides the bits, each one a line below:
//   - every value is a float, with the float constants written exactly as Chromium's source writes them;
//   - which maths library each call goes to: fdlibm::asinf and fdlibm::powf where Chromium names fdlibm; the
//     system's powf and log10f in DecibelsToLinear and LinearToDecibels (audio_utilities calls them unqualified);
//     the system's double exp in the knee and double sin in the gain warp. The engine calls the same system
//     library as the browser on the same platform (glibc on Linux, Apple's libm on the Mac);
//   - the envelope is worked out at the start of every 32-frame division. Chromium starts the divisions at the
//     start of each call (one render quantum: 128 frames while playing, 512 in the app's export, both multiples
//     of 32), so here they sit on a fixed 32-frame grid counted from the first frame, whatever the call size;
//   - the parameters are AudioParams: stored as float and clamped to their ranges (threshold -100..0 dB,
//     knee 0..40 dB, ratio 1..20, attack and release 0..1 s);
//   - 6 ms of look-ahead (the pre-delay, 288 frames at 48 kHz), the detector on the undelayed input;
//   - a mono input is read as both channels; the output always has two;
//   - the node runs with denormals flushed (NodeFloatState around the call, as Chromium's audio thread).
// Not ported: automation of the parameters (the app sets fixed values), the tail after the input is
// disconnected (with a connected input the node always runs).
#pragma once
#include <algorithm>
#include <cfloat>
#include <cmath>
#include <vector>
#include "../../third_party/fdlibm/ieee754.h"

namespace al {
namespace cr {

namespace au {
inline float DecibelsToLinear(float decibels) { return ::powf(10, 0.05f * decibels); }
inline float LinearToDecibels(float linear) { return 20 * ::log10f(linear); }
inline double DiscreteTimeConstantForSampleRate(double time_constant, double sample_rate) {
    return 1 - fdlibm::exp(-1 / (sample_rate * time_constant));
}
}  // namespace au

class DynamicsCompressor {
public:
    enum { kParamThreshold, kParamKnee, kParamRatio, kParamAttack, kParamRelease, kParamReduction, kParamLast };

    explicit DynamicsCompressor(float sample_rate) : sample_rate_(sample_rate) {
        for (auto& b : pre_delay_buffers_) b.assign(kMaxPreDelayFrames, 0.f);
        Reset();
        metering_release_k_ = static_cast<float>(au::DiscreteTimeConstantForSampleRate(kMeteringReleaseTimeConstant, sample_rate));
        parameters_[kParamThreshold] = -24;
        parameters_[kParamKnee] = 30;
        parameters_[kParamRatio] = 12;
        parameters_[kParamAttack] = 0.003f;
        parameters_[kParamRelease] = 0.250f;
        parameters_[kParamReduction] = 0;
    }

    // AudioParam.value = x: stored as float; FinalValue() clamps it to the param's range.
    void setThreshold(double v) { parameters_[kParamThreshold] = clampF((float)v, -100, 0); }
    void setKnee(double v) { parameters_[kParamKnee] = clampF((float)v, 0, 40); }
    void setRatio(double v) { parameters_[kParamRatio] = clampF((float)v, 1, 20); }
    void setAttack(double v) { parameters_[kParamAttack] = clampF((float)v, 0, 1); }
    void setRelease(double v) { parameters_[kParamRelease] = clampF((float)v, 0, 1); }
    float reduction() const { return parameters_[kParamReduction]; }
    int latencyFrames() const { return (int)last_pre_delay_frames_; }

    // One call of the node. src0/src1: the input (src1 null for a mono input); dst0, dst1: the output.
    // In place is allowed (each frame is read before it is written, and the pre-delay is never 0 frames).
    void process(const float* src0, const float* src1, float* dst0, float* dst1, unsigned frames_to_process) {
        const float db_threshold = parameters_[kParamThreshold];
        const float db_knee = parameters_[kParamKnee];
        const float ratio = parameters_[kParamRatio];
        const float attack_time = parameters_[kParamAttack];
        const float release_time = parameters_[kParamRelease];
        const float sample_rate = sample_rate_;

        const float k = UpdateStaticCurveParameters(db_threshold, db_knee, ratio);
        const float linear_post_gain = fdlibm::powf(1 / Saturate(1, k), 0.6f);
        const float attack_frames = std::max(0.001f, attack_time) * sample_rate;
        const float release_frames = sample_rate * release_time;
        const float sat_release_frames = kSatReleaseTime * sample_rate;
        const float a = release_frames * kABase;
        const float b = release_frames * kBBase;
        const float c = release_frames * kCBase;
        const float d = release_frames * kDBase;
        const float e = release_frames * kEBase;

        SetPreDelayTime(kPreDelay);

        const float* src[2] = {src0, src1 ? src1 : src0};
        float* dst[2] = {dst0, dst1};
        unsigned frame_index = 0;
        while (frame_index < frames_to_process) {
            if (div_left_ == 0) {   // the start of a 32-frame division: the envelope for it
                startDivision(a, b, c, d, e, attack_frames);
                div_left_ = kNumberOfDivisionFrames;
            }
            int pre_delay_read_index = pre_delay_read_index_;
            int pre_delay_write_index = pre_delay_write_index_;
            float detector_average = detector_average_;
            float compressor_gain = compressor_gain_;
            const float scaled_desired_gain = scaled_desired_gain_;
            const float envelope_rate = envelope_rate_;

            const unsigned loop_frames = std::min(div_left_, frames_to_process - frame_index);
            for (unsigned division_frame = 0; division_frame < loop_frames; ++division_frame) {
                float compressor_input = 0;
                for (unsigned j = 0; j < 2; ++j) {
                    const float undelayed_source = src[j][frame_index];
                    pre_delay_buffers_[j][pre_delay_write_index] = undelayed_source;
                    const float abs_undelayed_source = undelayed_source > 0 ? undelayed_source : -undelayed_source;
                    if (compressor_input < abs_undelayed_source) compressor_input = abs_undelayed_source;
                }
                const float scaled_input = compressor_input;
                const float abs_input = scaled_input > 0 ? scaled_input : -scaled_input;
                const float shaped_input = Saturate(abs_input, k);
                const float attenuation = abs_input <= 0.0001f ? 1 : shaped_input / abs_input;
                const float db_attenuation = std::max(2.0f, -au::LinearToDecibels(attenuation));
                const float db_per_frame = db_attenuation / sat_release_frames;
                const float sat_release_rate = au::DecibelsToLinear(db_per_frame) - 1;
                const bool is_release = (attenuation > detector_average);
                const float rate = is_release ? sat_release_rate : 1;
                detector_average += (attenuation - detector_average) * rate;
                detector_average = std::min(1.0f, detector_average);
                detector_average = EnsureFinite(detector_average, 1);
                if (envelope_rate < 1) {
                    compressor_gain += (scaled_desired_gain - compressor_gain) * envelope_rate;
                } else {
                    compressor_gain *= envelope_rate;
                    compressor_gain = std::min(1.0f, compressor_gain);
                }
                const float post_warp_compressor_gain = static_cast<float>(::sin(static_cast<double>(kPiOverTwoFloat * compressor_gain)));
                const float total_gain = linear_post_gain * post_warp_compressor_gain;
                const float db_real_gain = au::LinearToDecibels(post_warp_compressor_gain);
                if (db_real_gain < metering_gain_) metering_gain_ = db_real_gain;
                else metering_gain_ += (db_real_gain - metering_gain_) * metering_release_k_;
                for (unsigned j = 0; j < 2; ++j) dst[j][frame_index] = pre_delay_buffers_[j][pre_delay_read_index] * total_gain;
                frame_index++;
                pre_delay_read_index = (pre_delay_read_index + 1) & kMaxPreDelayFramesMask;
                pre_delay_write_index = (pre_delay_write_index + 1) & kMaxPreDelayFramesMask;
            }
            div_left_ -= loop_frames;
            pre_delay_read_index_ = pre_delay_read_index;
            pre_delay_write_index_ = pre_delay_write_index;
            // Chromium flushes at the end of each division; a division split over two calls is flushed at the end of
            // each part, which is the same: the values are only read back after the flush in the next part.
            detector_average_ = FlushDenormalFloatToZero(detector_average);
            compressor_gain_ = FlushDenormalFloatToZero(compressor_gain);
        }
        parameters_[kParamReduction] = metering_gain_;
    }

    void Reset() {
        detector_average_ = 0;
        compressor_gain_ = 1;
        metering_gain_ = 1;
        for (auto& b : pre_delay_buffers_) std::fill(b.begin(), b.end(), 0.f);
        pre_delay_read_index_ = 0;
        pre_delay_write_index_ = kDefaultPreDelayFrames;
        db_max_attack_compression_diff_ = -1;
        div_left_ = 0;
    }

private:
    static constexpr float kPiOverTwoFloat = 3.14159265358979323846f / 2.0f;   // std::numbers::pi_v<float> / 2.0f
    static constexpr float kMeteringReleaseTimeConstant = 0.325f;
    static constexpr float kPreDelay = 0.006f;
    static constexpr float kReleaseZone1 = 0.09f;
    static constexpr float kReleaseZone2 = 0.16f;
    static constexpr float kReleaseZone3 = 0.42f;
    static constexpr float kReleaseZone4 = 0.98f;
    static constexpr float kABase = 0.9999999999999998f * kReleaseZone1 + 1.8432219684323923e-16f * kReleaseZone2 -
                                    1.9373394351676423e-16f * kReleaseZone3 + 8.824516011816245e-18f * kReleaseZone4;
    static constexpr float kBBase = -1.5788320352845888f * kReleaseZone1 + 2.3305837032074286f * kReleaseZone2 -
                                    0.9141194204840429f * kReleaseZone3 + 0.1623677525612032f * kReleaseZone4;
    static constexpr float kCBase = 0.5334142869106424f * kReleaseZone1 - 1.272736789213631f * kReleaseZone2 +
                                    0.9258856042207512f * kReleaseZone3 - 0.18656310191776226f * kReleaseZone4;
    static constexpr float kDBase = 0.08783463138207234f * kReleaseZone1 - 0.1694162967925622f * kReleaseZone2 +
                                    0.08588057951595272f * kReleaseZone3 - 0.00429891410546283f * kReleaseZone4;
    static constexpr float kEBase = -0.042416883008123074f * kReleaseZone1 + 0.1115693827987602f * kReleaseZone2 -
                                    0.09764676325265872f * kReleaseZone3 + 0.028494263462021576f * kReleaseZone4;
    static constexpr float kSatReleaseTime = 0.0025f;
    static constexpr float kUninitializedValue = -1;
    static constexpr unsigned kNumberOfDivisionFrames = 32;
    enum { kMaxPreDelayFrames = 1024, kMaxPreDelayFramesMask = kMaxPreDelayFrames - 1, kDefaultPreDelayFrames = 256 };

    static float clampF(float v, float lo, float hi) { return v < lo ? lo : v > hi ? hi : v; }
    static float EnsureFinite(float x, float default_value) { return std::isfinite(x) ? x : default_value; }
    static float FlushDenormalFloatToZero(float x) { return (std::fabs(x) < FLT_MIN) ? 0.0f : x; }

    // The top of Chromium's division loop: the desired gain from the detector, then the envelope rate.
    void startDivision(float a, float b, float c, float d, float e, float attack_frames) {
        detector_average_ = EnsureFinite(detector_average_, 1);
        const float desired_gain = detector_average_;
        const float scaled_desired_gain = fdlibm::asinf(desired_gain) / kPiOverTwoFloat;
        float envelope_rate = 0.0f;
        const bool is_releasing = scaled_desired_gain > compressor_gain_;
        float db_compression_diff = 0.0f;
        if (scaled_desired_gain == 0) {
            db_compression_diff = is_releasing ? -1 : 1;
        } else {
            db_compression_diff = au::LinearToDecibels(compressor_gain_ / scaled_desired_gain);
        }
        if (is_releasing) {
            db_max_attack_compression_diff_ = -1;
            db_compression_diff = EnsureFinite(db_compression_diff, -1);
            float x = db_compression_diff;
            x = clampF(x, -12.0f, 0.0f);   // ClampTo<float>
            x = 0.25f * (x + 12);
            const float x2 = x * x;
            const float x3 = x2 * x;
            const float x4 = x2 * x2;
            const float calc_release_frames = a + b * x + c * x2 + d * x3 + e * x4;
            constexpr float kDbSpacing = 5;
            const float db_per_frame = kDbSpacing / calc_release_frames;
            envelope_rate = au::DecibelsToLinear(db_per_frame);
        } else {
            db_compression_diff = EnsureFinite(db_compression_diff, 1);
            if (db_max_attack_compression_diff_ == -1 || db_max_attack_compression_diff_ < db_compression_diff)
                db_max_attack_compression_diff_ = db_compression_diff;
            const float db_eff_atten_diff = std::max(0.5f, db_max_attack_compression_diff_);
            const float x = 0.25f / db_eff_atten_diff;
            envelope_rate = 1 - fdlibm::powf(x, 1 / attack_frames);
        }
        scaled_desired_gain_ = scaled_desired_gain;
        envelope_rate_ = envelope_rate;
    }

    void SetPreDelayTime(float pre_delay_time) {
        unsigned pre_delay_frames = pre_delay_time * sample_rate_;
        if (pre_delay_frames > kMaxPreDelayFrames - 1) pre_delay_frames = kMaxPreDelayFrames - 1;
        if (last_pre_delay_frames_ != pre_delay_frames) {
            last_pre_delay_frames_ = pre_delay_frames;
            for (auto& b : pre_delay_buffers_) std::fill(b.begin(), b.end(), 0.f);
            pre_delay_read_index_ = 0;
            pre_delay_write_index_ = pre_delay_frames;
        }
    }

    float KneeCurve(float x, float k) const {
        if (x < linear_threshold_) return x;
        return linear_threshold_ + (1 - static_cast<float>(::exp(static_cast<double>(-k * (x - linear_threshold_))))) / k;
    }
    float Saturate(float x, float k) const {
        if (x < knee_threshold_) return KneeCurve(x, k);
        const float db_x = au::LinearToDecibels(x);
        const float db_y = db_yknee_threshold_ + slope_ * (db_x - db_knee_threshold_);
        return au::DecibelsToLinear(db_y);
    }
    float KAtSlope(float desired_slope) const {
        const float db_x = db_threshold_ + db_knee_;
        const float x = au::DecibelsToLinear(db_x);
        float x2 = 1;
        float db_x2 = 0;
        if (!(x < linear_threshold_)) {
            x2 = x * 1.001;
            db_x2 = au::LinearToDecibels(x2);
        }
        float min_k = 0.1;
        float max_k = 10000;
        float k = 5;
        float slope = 1;
        for (int i = 0; i < 15; ++i) {
            if (!(x < linear_threshold_)) {
                const float db_y = au::LinearToDecibels(KneeCurve(x, k));
                const float db_y2 = au::LinearToDecibels(KneeCurve(x2, k));
                slope = (db_y2 - db_y) / (db_x2 - db_x);
            }
            if (slope < desired_slope) max_k = k;
            else min_k = k;
            k = ::sqrtf(min_k * max_k);
        }
        return k;
    }
    float UpdateStaticCurveParameters(float db_threshold, float db_knee, float ratio) {
        if (db_threshold != db_threshold_ || db_knee != db_knee_ || ratio != ratio_) {
            db_threshold_ = db_threshold;
            linear_threshold_ = au::DecibelsToLinear(db_threshold);
            db_knee_ = db_knee;
            ratio_ = ratio;
            slope_ = 1 / ratio_;
            const float k = KAtSlope(1 / ratio_);
            db_knee_threshold_ = db_threshold + db_knee;
            knee_threshold_ = au::DecibelsToLinear(db_knee_threshold_);
            db_yknee_threshold_ = au::LinearToDecibels(KneeCurve(knee_threshold_, k));
            knee_ = k;
        }
        return knee_;
    }

    float parameters_[kParamLast];
    float sample_rate_;
    float detector_average_ = 0, compressor_gain_ = 1;
    float metering_release_k_ = 0, metering_gain_ = 1;
    unsigned last_pre_delay_frames_ = kDefaultPreDelayFrames;
    std::vector<float> pre_delay_buffers_[2];
    int pre_delay_read_index_ = 0, pre_delay_write_index_ = kDefaultPreDelayFrames;
    float db_max_attack_compression_diff_ = -1;
    float ratio_ = kUninitializedValue, slope_ = kUninitializedValue, linear_threshold_ = kUninitializedValue,
          db_threshold_ = kUninitializedValue, db_knee_ = kUninitializedValue, knee_threshold_ = kUninitializedValue,
          db_knee_threshold_ = kUninitializedValue, db_yknee_threshold_ = kUninitializedValue, knee_ = kUninitializedValue;
    // the envelope of the current division, kept across calls that end inside a division
    unsigned div_left_ = 0;
    float scaled_desired_gain_ = 1, envelope_rate_ = 0;
};

}  // namespace cr
}  // namespace al
