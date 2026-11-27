// Chromium's source nodes and wave shaper, ported for the native engine (task NB-N3g).
//
// Statement-by-statement ports of Chromium 158.0.8127.36 (third_party/blink/renderer/...):
//   platform/audio/rustfft_ffi.rs + fft_frame.cc   FFTFrame: the RustFFT crate itself (native/third_party/rustfft_ffi)
//   modules/webaudio/periodic_wave_handler.cc      the band-limited tables of the four basic waveforms
//   modules/webaudio/oscillator_handler.cc         OscillatorNode, k-rate (fixed frequency and detune)
//   modules/webaudio/cpu/x86/oscillator_kernel_sse2.cc, cpu/arm/oscillator_kernel_neon.cc
//                                                  its 4-frame kernel, written out lane by lane per platform
//   modules/webaudio/audio_scheduled_source_handler.cc   start and stop on the frame grid, sub-sample start
//   modules/webaudio/constant_source_handler.cc    ConstantSourceNode, k-rate
//   modules/webaudio/wave_shaper_handler.cc        WaveShaperNode without oversampling
// What decides the bits: float AudioParams; the system's log2f and pow where Chromium calls them unqualified;
// the 4-frame kernel's float virtual index (built from the double one in double on x86, in float on ARM, as the
// two kernels do); the double virtual index re-made at every render quantum, so a source always runs whole
// quanta on the context's grid (QuantumSource) and is served to calls of any size from there.
#pragma once
#include <algorithm>
#include <cfloat>
#include <cmath>
#include <cstdint>
#include <limits>
#include <memory>
#include <string>
#include <vector>
#include "../../third_party/rustfft_ffi/rustfft_ffi.h"

namespace al {
namespace cr {

// FFTFrame (fft_frame.cc): RustFFT through Chromium's wrapper, packed real/imaginary halves.
class FFTFrame {
public:
    explicit FFTFrame(unsigned n) : n_(n), f_(al_rustfft_new(n)), re_((n + 1) / 2), im_((n + 1) / 2) {}
    ~FFTFrame() { al_rustfft_free(f_); }
    FFTFrame(const FFTFrame&) = delete;
    FFTFrame& operator=(const FFTFrame&) = delete;
    std::vector<float>& real() { return re_; }
    std::vector<float>& imag() { return im_; }
    void doFFT(const float* data) { al_rustfft_forward(f_, data, re_.data(), im_.data()); }
    void doInverseFFT(float* data) { al_rustfft_inverse(f_, re_.data(), im_.data(), data); }
    unsigned size() const { return n_; }

private:
    unsigned n_;
    AlRustFft* f_;
    std::vector<float> re_, im_;
};

enum class OscType { Sine = 0, Square = 1, Sawtooth = 2, Triangle = 3 };
inline bool oscTypeOf(const std::string& s, OscType& t) {
    if (s == "sine") t = OscType::Sine; else if (s == "square") t = OscType::Square;
    else if (s == "sawtooth") t = OscType::Sawtooth; else if (s == "triangle") t = OscType::Triangle; else return false;
    return true;
}

// PeriodicWaveHandler for the basic waveforms (GenerateBasicWaveform + CreateBandLimitedTables).
class PeriodicWave {
public:
    static constexpr unsigned kNumberOfOctaveBands = 3;
    static constexpr float kCentsPerOctave = 1200;
    static constexpr float kCentsPerRange = kCentsPerOctave / kNumberOfOctaveBands;

    PeriodicWave(float sample_rate, OscType shape)
        : size_(waveSize(sample_rate)),
          ranges_(static_cast<unsigned>(std::lround(kNumberOfOctaveBands * ::log2f(size_)))),
          lowest_(sample_rate / size_),
          rate_scale_(size_ / sample_rate) {
        generateBasic(shape);
    }
    unsigned size() const { return size_; }
    float rateScale() const { return rate_scale_; }
    float lowest() const { return lowest_; }
    unsigned ranges() const { return ranges_; }
    void table(unsigned i, const float*& t) const { t = tables_[i].data(); }

    void waveData(float fundamental_frequency, const float*& lower, const float*& higher, float& factor) const {
        fundamental_frequency = ::fabsf(fundamental_frequency);
        const float ratio = fundamental_frequency > 0 ? fundamental_frequency / lowest_ : 0.5f;
        const float cents_above_lowest_frequency = ::log2f(ratio) * kCentsPerOctave;
        const float pitch_range = std::clamp(1 + cents_above_lowest_frequency / kCentsPerRange, 0.0f, static_cast<float>(ranges_ - 1));
        const unsigned range_index1 = static_cast<unsigned>(pitch_range);
        const unsigned range_index2 = range_index1 < ranges_ - 1 ? range_index1 + 1 : range_index1;
        lower = tables_[range_index2].data();
        higher = tables_[range_index1].data();
        factor = pitch_range - range_index1;
    }

private:
    static unsigned waveSize(float sr) { return sr <= 24000 ? 2048 : sr <= 88200 ? 4096 : 16384; }

    void generateBasic(OscType shape) {
        const unsigned fft_size = size_, half_size = fft_size / 2;
        std::vector<float> real(half_size, 0.f), imag(half_size, 0.f);
        const float pi_f = 3.14159265358979323846f;   // std::numbers::pi_v<float>
        for (unsigned n = 1; n < half_size; ++n) {
            const float pi_factor = 2 / (n * pi_f);
            float b;
            switch (shape) {
                case OscType::Sine: b = (n == 1) ? 1 : 0; break;
                case OscType::Square: b = (n & 1) ? 2 * pi_factor : 0; break;
                case OscType::Sawtooth: b = pi_factor * ((n & 1) ? 1 : -1); break;
                default:
                    if (n & 1) b = 2 * (pi_factor * pi_factor) * ((((n - 1) >> 1) & 1) ? -1 : 1);
                    else b = 0;
            }
            real[n] = 0;
            imag[n] = b;
        }
        createTables(real, imag, false);
    }

    void createTables(const std::vector<float>& real_data, const std::vector<float>& imag_data, bool disable_normalization) {
        float normalization_scale = 0.5f;
        const unsigned fft_size = size_, half_size = fft_size / 2, max_number_of_partials = half_size;
        const unsigned number_of_components = std::min(static_cast<unsigned>(real_data.size()), half_size);
        FFTFrame frame(fft_size);
        tables_.assign(ranges_, {});
        for (unsigned range_index = 0; range_index < ranges_; ++range_index) {
            std::vector<float>& real = frame.real();
            std::vector<float>& imag = frame.imag();
            const float scale = fft_size;
            for (unsigned i = 0; i < number_of_components; i++) { real[i] = real_data[i] * scale; imag[i] = imag_data[i] * -scale; }   // Vsmul
            const float cents_to_cull = range_index * kCentsPerRange;
            const float culling_scale = ::pow(2, -cents_to_cull / kCentsPerOctave);
            const unsigned number_of_partials = culling_scale * max_number_of_partials;
            for (unsigned i = std::min(number_of_components, number_of_partials + 1); i < half_size; ++i) { real[i] = 0; imag[i] = 0; }
            real[0] = 0;
            imag[0] = 0;
            std::vector<float>& t = tables_[range_index];
            t.assign(size_, 0.f);
            frame.doInverseFFT(t.data());
            if (!disable_normalization && !range_index) {
                float max_value = 0;   // Vmaxmgv
                for (float v : t) max_value = std::max(max_value, std::fabs(v));
                if (max_value) normalization_scale = 1.0f / max_value;
            }
            for (float& v : t) v = v * normalization_scale;   // Vsmul
        }
    }

    unsigned size_, ranges_;
    float lowest_, rate_scale_;
    std::vector<std::vector<float>> tables_;
};

// Chromium's AudioScheduledSourceHandler::UpdateSchedulingInfo for one quantum.
struct Schedule {
    double start = -1, end = -1;   // seconds; -1: not started / no stop (kUnknownTime)
    enum State { Unscheduled, Scheduled, Playing, Finished } state = Unscheduled;
    static size_t toFrame(double time, double sr) {   // audio_utilities::TimeToSampleFrame, kRoundUp
        constexpr double oversample_factor = 1024;
        double frame = ::round(time * sr * oversample_factor) / oversample_factor;
        frame = ::ceil(frame);
        if (frame >= (double)std::numeric_limits<size_t>::max()) return std::numeric_limits<size_t>::max();
        return static_cast<size_t>(frame);
    }
    void startAt(double when, double now) { start = std::max(when, now); state = Scheduled; }
    void stopAt(double when) { end = std::max(0.0, when); }
    // out: offset (first frame that plays), n (frames that play from there), startFrameOffset; zeros what is silent
    bool update(size_t qstart, size_t Q, double sr, float* out, size_t& offset, size_t& n, double& sfo) {
        offset = 0; n = 0; sfo = 0;
        const size_t qend = qstart + Q;
        const size_t start_frame = toFrame(start < 0 ? 0 : start, sr);
        const size_t end_frame = end < 0 ? 0 : toFrame(end, sr);
        if (end >= 0 && end_frame <= qstart) finish();
        if (state == Unscheduled || state == Finished || start_frame >= qend) { std::fill(out, out + Q, 0.f); return false; }
        if (state == Scheduled) { state = Playing; sfo = start * sr - start_frame; }
        offset = start_frame > qstart ? start_frame - qstart : 0;
        offset = std::min(offset, Q);
        n = Q - offset;
        if (!n) { std::fill(out, out + Q, 0.f); return false; }
        if (offset) std::fill(out, out + offset, 0.f);
        if (end >= 0 && end_frame >= qstart && end_frame <= qend) {
            if (end_frame < qend) {
                const size_t zero_start = end_frame - qstart, to_zero = Q - zero_start;
                n = to_zero > n ? 0 : n - to_zero;
                std::fill(out + zero_start, out + Q, 0.f);
            }
            finish();
        }
        return true;   // (n may be 0 here: the output is then zeros but not flagged silent)
    }
    void finish() { state = Finished; }
};

// OscillatorNode with fixed frequency and detune (the k-rate path).
class Oscillator {
public:
    static constexpr float kInterpolate2Point = 0.3f;
    static constexpr float kInterpolate3Point = 0.16f;
    Oscillator(float sr, OscType t) : sr_(sr), wave_(new PeriodicWave(sr, t)) {}
    // AudioParam.value = v at context time `at`: Chromium records it as a setValueAtTime event, and the param counts
    // as sample-accurate in the quantum that holds the event (and any before it). The node then takes its a-rate
    // path there (different arithmetic, the same value), the k-rate path after.
    // Measured against Chromium: with one such event the param is sample-accurate only in the quantum that holds it;
    // with two (the app sets the frequency twice before the render) in the first two quanta the node computes, however
    // late it starts (taken as one quantum per event; three or more events are not measured).
    void setFrequency(double v, double at = 0) { freq_ = (float)v; freqEv_++; freqEvFrame_ = at * sr_; }
    void setDetune(double v, double at = 0) { detune_ = (float)v; detEv_++; detEvFrame_ = at * sr_; }
    Schedule sched;
    // one render quantum; returns whether the output is flagged non-silent
    bool process(size_t qstart, size_t Q, float* out) {
        size_t offset, n; double sfo;
        if (!sched.update(qstart, Q, sr_, out, offset, n, sfo)) return false;
        if (!n) { std::fill(out, out + Q, 0.f); return false; }
        double virtual_read_index = vri_;
        const float rate_scale = wave_->rateScale();
        const bool aFreq = sampleAccurate(freqEv_, freqLeft_, freqEvFrame_, qstart);
        const bool aDet = sampleAccurate(detEv_, detLeft_, detEvFrame_, qstart);
        const bool has_sample_accurate_values = aFreq || aDet;
        float frequency = 0;
        if (has_sample_accurate_values) {
            phaseIncrements(Q, aFreq, aDet);
        } else {
            frequency = freq_;
            const float detune_scale = std::exp2(detune_ / 1200);
            frequency *= detune_scale;
            frequency = clampNyq(frequency);
        }
        size_t destination_index = offset;
        unsigned cnt = (unsigned)n;
        if (sfo > 0) {
            ++destination_index; --cnt;
            virtual_read_index += (1 - sfo) * frequency * rate_scale;
        } else if (sfo < 0) {
            virtual_read_index = -sfo * frequency * rate_scale;
        }
        if (has_sample_accurate_values) vri_ = processARate((int)cnt, out + destination_index, virtual_read_index);
        else vri_ = processKRate((int)cnt, out + destination_index, virtual_read_index);
        return true;
    }

private:
    static float clampF(float v, float lo, float hi) { return v < lo ? lo : v > hi ? hi : v; }
    float clampNyq(float f) const { const float ny = sr_ / 2; return std::isnan(f) ? ny : clampF(f, -ny, ny); }

    static float doInterpolation(double virtual_read_index, float incr, unsigned read_index_mask, float table_interpolation_factor,
                                 const float* lower_wave_data, const float* higher_wave_data) {
        double sample_lower = 0, sample_higher = 0;
        unsigned read_index_0 = static_cast<unsigned>(virtual_read_index);
        if (incr >= kInterpolate2Point) {
            double interpolation_factor = static_cast<float>(virtual_read_index) - read_index_0;
            unsigned read_index2 = read_index_0 + 1;
            read_index_0 = read_index_0 & read_index_mask;
            read_index2 = read_index2 & read_index_mask;
            float sample1_lower = lower_wave_data[read_index_0], sample2_lower = lower_wave_data[read_index2];
            float sample1_higher = higher_wave_data[read_index_0], sample2_higher = higher_wave_data[read_index2];
            sample_higher = (1 - interpolation_factor) * sample1_higher + interpolation_factor * sample2_higher;
            sample_lower = (1 - interpolation_factor) * sample1_lower + interpolation_factor * sample2_lower;
        } else if (incr >= kInterpolate3Point) {
            unsigned read_index[3];
            for (int k = -1; k <= 1; ++k) read_index[k + 1] = (read_index_0 + k) & read_index_mask;
            double a[3];
            double t = virtual_read_index - read_index_0;
            a[0] = 0.5 * t * (t - 1);
            a[1] = 1 - t * t;
            a[2] = 0.5 * t * (t + 1);
            for (int k = 0; k < 3; ++k) { sample_lower += a[k] * lower_wave_data[read_index[k]]; sample_higher += a[k] * higher_wave_data[read_index[k]]; }
        } else {
            unsigned read_index[5];
            for (int k = -2; k <= 2; ++k) read_index[k + 2] = (read_index_0 + k) & read_index_mask;
            double a[5];
            double t = virtual_read_index - read_index_0;
            double t2 = t * t;
            a[0] = t * (t2 - 1) * (t - 2) / 24;
            a[1] = -t * (t - 1) * (t2 - 4) / 6;
            a[2] = (t2 - 1) * (t2 - 4) / 4;
            a[3] = -t * (t + 1) * (t2 - 4) / 6;
            a[4] = t * (t2 - 1) * (t + 2) / 24;
            for (int k = 0; k < 5; ++k) { sample_lower += a[k] * lower_wave_data[read_index[k]]; sample_higher += a[k] * higher_wave_data[read_index[k]]; }
        }
        float sample = (1 - table_interpolation_factor) * sample_higher + table_interpolation_factor * sample_lower;
        return sample;
    }

    // the 4-frame kernel: WrapVirtualIndexVector lane by lane (cvtt truncates toward zero, then one less where that
    // overshot: a floor that works for negative values)
    static float wrapF(float x, float wave_size, float inv_wave_size) {
        const float r = x * inv_wave_size;
        int32_t f = static_cast<int32_t>(r);
        if (r < static_cast<float>(f)) f -= 1;
        return x - static_cast<float>(f) * wave_size;
    }
    int processKRateVector(int n, float* destination, double& virtual_read_index, float frequency, float rate_scale) const {
#if !defined(AL_OSC_NO_VECTOR) && (defined(__x86_64__) || defined(_M_X64) || defined(__i386__) || defined(__aarch64__) || defined(__ARM_NEON))
        const unsigned periodic_wave_size = wave_->size();
        const double inv_periodic_wave_size = 1.0 / periodic_wave_size;
        const float* lower; const float* higher; float table_interpolation_factor = 0;
        const float incr = frequency * rate_scale;
        wave_->waveData(frequency, lower, higher, table_interpolation_factor);
        const float v_wave_size = (float)periodic_wave_size;
        const float v_inv_wave_size = 1.0f / periodic_wave_size;
        const uint32_t mask = periodic_wave_size - 1;
        const float v_incr = 4 * incr;
        float v[4];
#if defined(__aarch64__) || defined(__ARM_NEON)
        const float vrf = (float)virtual_read_index;   // float virtual_read_index_flt = virtual_read_index
        v[0] = vrf + 0 * incr; v[1] = vrf + 1 * incr; v[2] = vrf + 2 * incr; v[3] = vrf + 3 * incr;
#else
        v[0] = (float)virtual_read_index; v[1] = (float)(virtual_read_index + incr);   // _mm_set_ps(double...)
        v[2] = (float)(virtual_read_index + 2 * incr); v[3] = (float)(virtual_read_index + 3 * incr);
#endif
        for (float& x : v) x = wrapF(x, v_wave_size, v_inv_wave_size);
        int k = 0;
        const int n_loops = n / 4;
        for (int loop = 0; loop < n_loops; ++loop, k += 4) {
            for (int m = 0; m < 4; m++) {
#if defined(__aarch64__) || defined(__ARM_NEON)
                const uint32_t r0 = static_cast<uint32_t>(v[m]) & mask;   // vcvtq_u32_f32
#else
                const uint32_t r0 = static_cast<uint32_t>(static_cast<int32_t>(v[m])) & mask;   // _mm_cvttps_epi32
#endif
                const uint32_t r1 = (r0 + 1) & mask;
                const float s1_low = lower[r0], s2_low = lower[r1], s1_high = higher[r0], s2_high = higher[r1];
#if defined(__aarch64__) || defined(__ARM_NEON)
                const float interpolation_factor = v[m] - static_cast<float>(r0);   // vcvtq_f32_u32
#else
                const float interpolation_factor = v[m] - static_cast<float>(static_cast<int32_t>(r0));   // _mm_cvtepi32_ps
#endif
                const float sample_higher = s1_high + interpolation_factor * (s2_high - s1_high);
                const float sample_lower = s1_low + interpolation_factor * (s2_low - s1_low);
                destination[k + m] = sample_higher + table_interpolation_factor * (sample_lower - sample_higher);
            }
            for (float& x : v) x = wrapF(x + v_incr, v_wave_size, v_inv_wave_size);
        }
        virtual_read_index += k * incr;
        virtual_read_index -= ::floor(virtual_read_index * inv_periodic_wave_size) * periodic_wave_size;
        return k;
#else
        (void)n; (void)destination; (void)virtual_read_index; (void)frequency; (void)rate_scale;
        return 0;
#endif
    }
    double processKRateScalar(int start, int n, float* destination, double virtual_read_index, float frequency, float rate_scale) const {
        const unsigned periodic_wave_size = wave_->size();
        const double inv_periodic_wave_size = 1.0 / periodic_wave_size;
        const unsigned read_index_mask = periodic_wave_size - 1;
        const float* lower; const float* higher; float table_interpolation_factor = 0;
        wave_->waveData(frequency, lower, higher, table_interpolation_factor);
        const float incr = frequency * rate_scale;
        for (int k = start; k < n; ++k) {
            unsigned read_index_0 = static_cast<unsigned>(virtual_read_index);
            const float interpolation_factor = static_cast<float>(virtual_read_index) - read_index_0;
            read_index_0 &= read_index_mask;
            const unsigned read_index_1 = (read_index_0 + 1) & read_index_mask;
            const float sample1_lower = lower[read_index_0], sample2_lower = lower[read_index_1];
            const float sample1_higher = higher[read_index_0], sample2_higher = higher[read_index_1];
            const float sample_higher = sample1_higher + interpolation_factor * (sample2_higher - sample1_higher);
            const float sample_lower = sample1_lower + interpolation_factor * (sample2_lower - sample1_lower);
            destination[k] = sample_higher + table_interpolation_factor * (sample_lower - sample_higher);
            virtual_read_index += incr;
            virtual_read_index -= ::floor(virtual_read_index * inv_periodic_wave_size) * periodic_wave_size;
        }
        return virtual_read_index;
    }
    double processKRate(int n, float* destination, double virtual_read_index) const {
        const unsigned periodic_wave_size = wave_->size();
        const double inv_periodic_wave_size = 1.0 / periodic_wave_size;
        const unsigned read_index_mask = periodic_wave_size - 1;
        const float* lower; const float* higher; float table_interpolation_factor = 0;
        float frequency = freq_;
        const float detune_scale = std::exp2(detune_ / 1200);
        frequency *= detune_scale;
        frequency = clampNyq(frequency);
        wave_->waveData(frequency, lower, higher, table_interpolation_factor);
        const float rate_scale = wave_->rateScale();
        const float incr = frequency * rate_scale;
        if (incr >= kInterpolate2Point) {
            double v_index = virtual_read_index;
            int k = processKRateVector(n, destination, v_index, frequency, rate_scale);
            if (k < n) v_index = processKRateScalar(k, n, destination, v_index, frequency, rate_scale);
            virtual_read_index += n * incr;
            virtual_read_index -= ::floor(virtual_read_index * inv_periodic_wave_size) * periodic_wave_size;
        } else {
            for (int k = 0; k < n; ++k) {
                destination[k] = doInterpolation(virtual_read_index, ::fabs(incr), read_index_mask, table_interpolation_factor, lower, higher);
                virtual_read_index += incr;
                virtual_read_index -= ::floor(virtual_read_index * inv_periodic_wave_size) * periodic_wave_size;
            }
        }
        return virtual_read_index;
    }

    // CalculateSampleAccuratePhaseIncrements (fixed values: every frame the same)
    void phaseIncrements(size_t Q, bool aFreq, bool aDet) {
        inc_.assign(Q, 0.f);
        float final_scale = wave_->rateScale();
        if (aFreq) std::fill(inc_.begin(), inc_.end(), freq_);
        else final_scale *= freq_;
        if (aDet) {
            std::vector<float>& dv = aFreq ? det_ : inc_;
            dv.assign(Q, detune_);
            const float k = 1.0 / 1200;
            for (float& d : dv) d = d * k;              // Vsmul
            for (float& d : dv) d = std::exp2(d);
            if (aFreq) for (size_t i = 0; i < Q; i++) inc_[i] = dv[i] * inc_[i];   // Vmul
        } else {
            final_scale *= std::exp2(detune_ / 1200);
        }
        for (float& f : inc_) f = clampNyq(f);             // ClampFrequency
        for (float& f : inc_) f = f * final_scale;         // Vsmul
    }
    // PeriodicWaveHandler::WaveDataForFundamentalFrequency, four at a time (SSE2 on x86, NEON on ARM)
    void waveData4(const float* fundamental, const float* lower[4], const float* higher[4], float factor[4]) const {
#if defined(__aarch64__) || defined(__ARM_NEON)
        const float inv_lowest = 1 / wave_->lowest(), inv_range = 1 / PeriodicWave::kCentsPerRange;
#endif
        const float nr = (float)(wave_->ranges() - 1);
        for (int k = 0; k < 4; k++) {
            const float frequency = std::fabs(fundamental[k]);
            float ratio;
#if defined(__aarch64__) || defined(__ARM_NEON)
            ratio = frequency > 0 ? frequency * inv_lowest : 0.5f;
#else
            ratio = frequency > 0 ? frequency / wave_->lowest() : 0.5f;
#endif
            const float cents = ::log2f(ratio) * PeriodicWave::kCentsPerOctave;
#if defined(__aarch64__) || defined(__ARM_NEON)
            float pr = 1.0f + cents * inv_range;
#else
            float pr = 1.0f + cents / PeriodicWave::kCentsPerRange;
#endif
            pr = pr > 0.0f ? pr : 0.0f;     // _mm_max_ps(v, 0) / vmaxq_f32
            pr = pr < nr ? pr : nr;         // _mm_min_ps / vminq_f32
            const uint32_t i1 = static_cast<uint32_t>(pr);
            uint32_t i2 = i1 + 1; if ((float)i2 > nr) i2 = (uint32_t)nr;
            factor[k] = pr - static_cast<float>(i1);
            wave_->table(i2, lower[k]); wave_->table(i1, higher[k]);
        }
    }
    static double wrapD(double x, double wave_size, double inv_wave_size) {   // WrapVirtualIndexVectorPd / WrapVirtualIndex
#if defined(__aarch64__) || defined(__ARM_NEON)
        return x - ::floor(x * inv_wave_size) * wave_size;
#else
        const double r = x * inv_wave_size;
        int32_t f = static_cast<int32_t>(r);
        if (r < static_cast<double>(f)) f -= 1;
        return x - static_cast<double>(f) * wave_size;
#endif
    }
    double processARateVectorKernel(float* destination, double virtual_read_index, const float* phase_increments,
                                    const float* lower[4], const float* higher[4], const float* factor) const {
        const unsigned periodic_wave_size = wave_->size();
        const double inv_periodic_wave_size = 1.0 / periodic_wave_size;
        const unsigned read_index_mask = periodic_wave_size - 1;
        double incr_sum[4];
        incr_sum[0] = phase_increments[0];
        for (int m = 1; m < 4; ++m) incr_sum[m] = incr_sum[m - 1] + phase_increments[m];
        double vd[4] = {virtual_read_index, virtual_read_index + incr_sum[0], virtual_read_index + incr_sum[1], virtual_read_index + incr_sum[2]};
        for (double& x : vd) x = wrapD(x, periodic_wave_size, inv_periodic_wave_size);
        uint32_t r0[4], r1[4]; float vf[4];
#if defined(__aarch64__) || defined(__ARM_NEON)
        const float inv_f = (float)inv_periodic_wave_size;
        for (int m = 0; m < 4; m++) { vf[m] = wrapF((float)vd[m], (float)periodic_wave_size, inv_f); r0[m] = static_cast<uint32_t>(vf[m]) & read_index_mask; }
#else
        for (int m = 0; m < 4; m++) { r0[m] = static_cast<uint32_t>(static_cast<int32_t>(vd[m])); vf[m] = (float)vd[m] - static_cast<float>(static_cast<int32_t>(r0[m])); }
#endif
        for (int m = 0; m < 4; m++) {
            r1[m] = (r0[m] + 1) & read_index_mask;
            r0[m] &= read_index_mask;
#if defined(__aarch64__) || defined(__ARM_NEON)
            const float f = vf[m] - static_cast<float>(r0[m]);
#else
            const float f = vf[m];
#endif
            const float s1h = higher[m][r0[m]], s2h = higher[m][r1[m]], s1l = lower[m][r0[m]], s2l = lower[m][r1[m]];
            const float sh = s1h + f * (s2h - s1h);
            const float sl = s1l + f * (s2l - s1l);
            destination[m] = sh + factor[m] * (sl - sh);
        }
#if defined(__aarch64__) || defined(__ARM_NEON)
        return wrapD(virtual_read_index + incr_sum[3], periodic_wave_size, inv_periodic_wave_size);
#else
        virtual_read_index += incr_sum[3];
        virtual_read_index -= ::floor(virtual_read_index * inv_periodic_wave_size) * periodic_wave_size;
        return virtual_read_index;
#endif
    }
    double processARate(int n, float* destination, double virtual_read_index) const {
        const float rate_scale = wave_->rateScale();
        const float inv_rate_scale = 1 / rate_scale;
        const unsigned periodic_wave_size = wave_->size();
        const double inv_periodic_wave_size = 1.0 / periodic_wave_size;
        const unsigned read_index_mask = periodic_wave_size - 1;
        const float* pi = inc_.data();
        int k = 0;
        const int n_loops = n / 4;
        for (int loop = 0; loop < n_loops; ++loop, k += 4) {
            bool is_big_increment = true;
            float frequency[4];
            for (int m = 0; m < 4; ++m) {
                const float phase_incr = pi[k + m];
                is_big_increment = is_big_increment && (std::fabs(phase_incr) >= kInterpolate2Point);
                frequency[m] = inv_rate_scale * phase_incr;
            }
            const float* lower[4]; const float* higher[4]; float factor[4];
            waveData4(frequency, lower, higher, factor);
            if (is_big_increment) {
                virtual_read_index = processARateVectorKernel(destination + k, virtual_read_index, pi + k, lower, higher, factor);
            } else {
                for (int m = 0; m < 4; ++m) {
                    destination[k + m] = doInterpolation(virtual_read_index, std::fabs(pi[k + m]), read_index_mask, factor[m], lower[m], higher[m]);
                    virtual_read_index += pi[k + m];
                    virtual_read_index -= ::floor(virtual_read_index * inv_periodic_wave_size) * periodic_wave_size;
                }
            }
        }
        for (int m = k; m < n; ++m) {
            const float incr = pi[m];
            const float frequency = inv_rate_scale * incr;
            const float* lower; const float* higher; float factor = 0;
            wave_->waveData(frequency, lower, higher, factor);
            destination[m] = doInterpolation(virtual_read_index, std::fabs(incr), read_index_mask, factor, lower, higher);
            virtual_read_index += incr;
            virtual_read_index -= ::floor(virtual_read_index * inv_periodic_wave_size) * periodic_wave_size;
        }
        return virtual_read_index;
    }

    float sr_;
    std::unique_ptr<PeriodicWave> wave_;
    float freq_ = 440, detune_ = 0;
    int freqEv_ = 0, detEv_ = 0;   // setValueAtTime events not yet dropped
    int freqLeft_ = -1, detLeft_ = -1;   // sample-accurate quanta left once the node computes (-1: not started)
    static bool sampleAccurate(int& ev, int& left, double evFrame, size_t qstart) {
        if (ev >= 2) { left = ev; ev = 1; }
        if (left > 0) { left--; if (left == 0) ev = 0; return true; }
        if (ev == 1 && evFrame >= (double)qstart) return true;
        return false;
    }
    double freqEvFrame_ = 0, detEvFrame_ = 0;
    double vri_ = 0;
    std::vector<float> inc_, det_;
};

// ConstantSourceNode with a fixed offset.
class ConstantSource {
public:
    explicit ConstantSource(float sr) : sr_(sr) {}
    void setOffset(double v) { offset_ = (float)v; }
    Schedule sched;
    bool process(size_t qstart, size_t Q, float* out) {
        size_t offset, n; double sfo;
        if (!sched.update(qstart, Q, sr_, out, offset, n, sfo) || !n) { std::fill(out, out + Q, 0.f); return false; }
        if (offset_ == 0) { std::fill(out, out + Q, 0.f); return false; }
        std::fill(out + offset, out + offset + n, offset_);
        return true;
    }

private:
    float sr_, offset_ = 1;
};

// WaveShaperNode without oversampling: WaveShaperCurveValues on chunks of up to 128 frames (elementwise, so the
// chunking does not change the bits).
inline void waveShape(const float* source, float* destination, size_t n, const std::vector<float>& curve) {
    const size_t curve_length = curve.size();
    if (!curve_length) { std::copy(source, source + n, destination); return; }
    const int max_index = static_cast<int>(curve_length - 1);
    const float scale = static_cast<float>(0.5 * (curve_length - 1));
    const float hi = static_cast<float>(curve_length - 1);
    for (size_t k = 0; k < n; k++) {
        float v = source[k] + 1.0f;                       // Vsadd
        v = v * scale;                                    // Vsmul
        v = v < 0 ? 0.f : v > hi ? hi : v;                // Vclip (NaN stays NaN)
        int i1 = static_cast<int>(v);                     // cvtt (NaN gives INT_MIN on x86; clamped below)
        if (std::isnan(v)) i1 = std::numeric_limits<int32_t>::min();
        const int c1 = std::min(std::max(i1, 0), max_index);
        const int c2 = std::min(std::max(i1 + 1, 0), max_index);
        const float index = static_cast<float>(i1);
        const float v1 = curve[c1], v2 = curve[c2];
        const float f = v - index;                         // Vsub
        float d = v2 - v1;                                 // Vsub
        d = f * d;                                         // Vmul
        destination[k] = d + v1;                           // Vadd
    }
}

}  // namespace cr
}  // namespace al
