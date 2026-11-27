// Chromium's WaveShaperNode (with its 2x and 4x oversampling) and DelayNode, ported for the native engine
// (task NB-N3g).
//
// The app's Soft Clipper ('clip', on Fractals' master) and Drive ('drive') are browser nodes: a WaveShaperNode
// oversampled 4x, a DelayNode that keeps the dry path in time with it, a highpass BiquadFilterNode (biquad.h) and
// GainNodes. This is a statement-by-statement port of Chromium 158.0.8127.36:
//   modules/webaudio/wave_shaper_handler.cc   the node: sub-blocks of 128 frames, the curve lookup, the stages
//   platform/audio/up_sampler.cc, down_sampler.cc   the half-band resamplers and their windowed-sinc kernels
//   platform/audio/direct_convolver.cc, simple_fft_convolver.cc   the two ways they convolve
//   platform/audio/fft_frame.cc + rustfft_ffi.rs     the FFT (Chromium's own Rust code on rustfft 6.4.1: part 1's
//                                                    FFTFrame in webnodes.h, native/third_party/rustfft_ffi)
//   platform/audio/delay.cc + cpu/x86/delay_sse2.cc, cpu/arm/delay_neon.cc   the DelayNode (a-rate, vector path)
//   platform/audio/vector_math*.h                    the vector helpers: plain float loops in the same order as
//                                                    Chromium's SSE/AVX code on Linux and Windows; on the Mac the
//                                                    same Accelerate (vDSP) calls Chromium makes there
// What decides the bits:
//   - the 4x path's second stage convolves by FFT (blocks of 256 and 512 samples), so every output sample of a
//     sub-block depends on the whole sub-block: the node must run on the same 128-frame sub-blocks as the browser,
//     counted from the context's first frame (dev_shape.h holds the calls to that grid);
//   - the FFT is Chromium's own code on the same crate, so it picks the same algorithm and SIMD path (AVX+FMA,
//     SSE or NEON) on the same machine;
//   - every value is a float; the kernels are worked out in double with fdlibm's sin and cos, then stored as float;
//   - the DelayNode's delay time is an a-rate AudioParam (the default), so Chromium runs its vector path: read
//     position, index and interpolation all in float (not the scalar path's double), on a buffer of
//     quantum + 0.05 s frames.
// Build with -ffp-contract=off. Not ported: changing the curve while the node runs at another size, the tail after
// the input is disconnected (with a connected input the node always runs), automation of the delay time.
#pragma once
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <vector>
#include "../../third_party/fdlibm/ieee754.h"
#if defined(__APPLE__)
#include <Accelerate/Accelerate.h>
#endif
#if defined(__SSE2__) || defined(_M_X64)
#include <emmintrin.h>
#endif

#include "webnodes.h"   // FFTFrame: Chromium's RustFFT wrapper (task NB-N3g part 1, native/third_party/rustfft_ffi)

namespace al {
namespace cr {

// ---- vector_math: Chromium's helpers, the same arithmetic per element ------------------------------------------
namespace vm {
// Conv: dest[k] = sum over m of source[k + m] * filter[size - 1 - m], each lane summed from +0 in the order of m
// (sse::Conv and avx::Conv in cpu/x86/vector_math_impl.h); on the Mac vDSP_conv with the filter read backwards.
inline void Conv(const float* source, const float* filter, size_t filterSize, float* dest, size_t frames) {
#if defined(__APPLE__)
    vDSP_conv(source, 1, filter + filterSize - 1, -1, dest, 1, frames, filterSize);
#else
    // eight outputs at a time, as eight lanes (the same per-lane order: the compiler may vectorise across lanes
    // without reassociating anything)
    size_t k = 0;
#if defined(__SSE2__) || defined(_M_X64)
    // Chromium's sse::Conv, with two registers of lanes: per lane a multiply, then an add, in the order of m
    for (; k + 8 <= frames; k += 8) {
        __m128 s0 = _mm_setzero_ps(), s1 = _mm_setzero_ps();
        const float* s = source + k;
        for (size_t m = 0; m < filterSize; m++) {
            const __m128 f = _mm_set1_ps(filter[filterSize - 1 - m]);
            s0 = _mm_add_ps(s0, _mm_mul_ps(f, _mm_loadu_ps(s + m)));
            s1 = _mm_add_ps(s1, _mm_mul_ps(f, _mm_loadu_ps(s + m + 4)));
        }
        _mm_storeu_ps(dest + k, s0);
        _mm_storeu_ps(dest + k + 4, s1);
    }
#endif
    for (; k + 8 <= frames; k += 8) {
        float sum[8] = {0.f, 0.f, 0.f, 0.f, 0.f, 0.f, 0.f, 0.f};
        const float* s = source + k;
        for (size_t m = 0; m < filterSize; m++) {
            const float f = filter[filterSize - 1 - m];
            for (int j = 0; j < 8; j++) { const float product = f * s[m + j]; sum[j] = sum[j] + product; }
        }
        for (int j = 0; j < 8; j++) dest[k + j] = sum[j];
    }
    for (; k < frames; k++) {
        float sum = 0.f;
        const float* s = source + k;
        for (size_t m = 0; m < filterSize; m++) {
            const float product = filter[filterSize - 1 - m] * s[m];
            sum = sum + product;
        }
        dest[k] = sum;
    }
#endif
}
inline void Vadd(const float* a, const float* b, float* d, size_t n) {
#if defined(__APPLE__)
    vDSP_vadd(a, 1, b, 1, d, 1, n);
#else
    for (size_t i = 0; i < n; i++) d[i] = a[i] + b[i];
#endif
}
// d = a - b
inline void Vsub(const float* a, const float* b, float* d, size_t n) {
#if defined(__APPLE__)
    vDSP_vsub(b, 1, a, 1, d, 1, n);
#else
    for (size_t i = 0; i < n; i++) d[i] = a[i] - b[i];
#endif
}
inline void Vmul(const float* a, const float* b, float* d, size_t n) {
#if defined(__APPLE__)
    vDSP_vmul(a, 1, b, 1, d, 1, n);
#else
    for (size_t i = 0; i < n; i++) d[i] = a[i] * b[i];
#endif
}
inline void Vsmul(const float* a, float s, float* d, size_t n) {
#if defined(__APPLE__)
    vDSP_vsmul(a, 1, &s, d, 1, n);
#else
    for (size_t i = 0; i < n; i++) d[i] = s * a[i];
#endif
}
inline void Vsadd(const float* a, float s, float* d, size_t n) {
#if defined(__APPLE__)
    vDSP_vsadd(a, 1, &s, d, 1, n);
#else
    for (size_t i = 0; i < n; i++) d[i] = a[i] + s;
#endif
}
// Vclip: the SSE/AVX code is max(min(x, high), low); the inputs here are never NaN
inline void Vclip(const float* a, float lo, float hi, float* d, size_t n) {
#if defined(__APPLE__)
    vDSP_vclip(a, 1, &lo, &hi, d, 1, n);
#else
    for (size_t i = 0; i < n; i++) { float x = a[i]; x = x < hi ? x : hi; d[i] = x > lo ? x : lo; }
#endif
}
// complex multiply: real = r1*r2 - i1*i2, imag = r1*i2 + i1*r2 (MULTIPLY_ALL in vector_math_impl.h)
inline void Zvmul(const float* r1, const float* i1, const float* r2, const float* i2, float* rd, float* id, size_t n) {
#if defined(__APPLE__)
    DSPSplitComplex a{const_cast<float*>(r1), const_cast<float*>(i1)}, b{const_cast<float*>(r2), const_cast<float*>(i2)}, c{rd, id};
    vDSP_zvmul(&a, 1, &b, 1, &c, 1, n, 1);
#else
    for (size_t i = 0; i < n; i++) {
        const float a = r1[i], b = i1[i], c = r2[i], d = i2[i];
        const float re = a * c - b * d;
        const float im = a * d + b * c;
        rd[i] = re; id[i] = im;
    }
#endif
}
}  // namespace vm

constexpr double kPiD = 3.141592653589793;          // std::numbers::pi
constexpr double kTwoPiD = 2 * 3.141592653589793;   // kTwoPiDouble

// ---- FFTFrame::DoPaddedFFT and FFTFrame::Multiply (fft_frame.cc) on part 1's FFTFrame (webnodes.h) ----------
inline void fftPadded(FFTFrame& f, const float* data, size_t len) {
    std::vector<float> padded(f.size(), 0.f);
    std::copy(data, data + len, padded.begin());
    f.doFFT(padded.data());
}
// the packed DC and Nyquist (real[0], imag[0]) are multiplied apart, after the complex multiply wrote over them
inline void fftMultiply(FFTFrame& a, FFTFrame& b) {
    std::vector<float>& r1 = a.real(); std::vector<float>& i1 = a.imag();
    const std::vector<float>& r2 = b.real(); const std::vector<float>& i2 = b.imag();
    const float real0 = r1[0], imag0 = i1[0];
    vm::Zvmul(r1.data(), i1.data(), r2.data(), i2.data(), r1.data(), i1.data(), r1.size());
    r1[0] = real0 * r2[0];
    i1[0] = imag0 * i2[0];
}

// ---- DirectConvolver (direct_convolver.cc) ---------------------------------------------------------------------
class DirectConvolver {
public:
    DirectConvolver(size_t block, std::vector<float> kernel) : block_(block), k_(std::move(kernel)), buf_(k_.size() - 1 + block, 0.f) {}
    size_t kernelSize() const { return k_.size(); }
    void process(const float* src, float* dst) {
        const size_t h = k_.size() - 1;
        std::copy(src, src + block_, buf_.begin() + h);
        vm::Conv(buf_.data(), k_.data(), k_.size(), dst, block_);
        std::copy(buf_.begin() + block_, buf_.begin() + block_ + h, buf_.begin());   // memmove semantics: forward copy ok
    }
    void reset() { std::fill(buf_.begin(), buf_.end(), 0.f); }

private:
    size_t block_;
    std::vector<float> k_, buf_;
};

// ---- SimpleFFTConvolver (simple_fft_convolver.cc) -------------------------------------------------------------
class SimpleFFTConvolver {
public:
    SimpleFFTConvolver(unsigned block, const std::vector<float>& kernel)
        : ksize_(kernel.size()), kern_(2 * block), frame_(2 * block), in_(2 * block, 0.f), out_(2 * block, 0.f), overlap_(block, 0.f) {
        fftPadded(kern_, kernel.data(), kernel.size());
    }
    size_t kernelSize() const { return ksize_; }
    void process(const float* src, float* dst) {
        const unsigned half = frame_.size() / 2;
        std::copy(src, src + half, in_.begin());
        frame_.doFFT(in_.data());
        fftMultiply(frame_, kern_);
        frame_.doInverseFFT(out_.data());
        vm::Vadd(out_.data(), overlap_.data(), dst, half);
        std::copy(out_.begin() + half, out_.begin() + 2 * half, overlap_.begin());
    }
    void reset() { std::fill(overlap_.begin(), overlap_.end(), 0.f); }

private:
    size_t ksize_;
    FFTFrame kern_, frame_;
    std::vector<float> in_, out_, overlap_;
};

// ---- UpSampler (up_sampler.cc) and DownSampler (down_sampler.cc) -----------------------------------------------
inline std::vector<float> upKernel(size_t size) {
    std::vector<float> k(size);
    const double alpha = 0.16, a0 = 0.5 * (1.0 - alpha), a1 = 0.5, a2 = 0.5 * alpha;
    const int n = (int)k.size(), half = n / 2;
    const double off = -0.5;
    for (int i = 0; i < n; ++i) {
        double s = kPiD * (i - half - off);
        double sinc = !s ? 1.0 : fdlibm::sin(s) / s;
        double x = (i - off) / n;
        double window = a0 - a1 * fdlibm::cos(kTwoPiD * x) + a2 * fdlibm::cos(kTwoPiD * 2.0 * x);
        k[i] = (float)(sinc * window);
    }
    return k;
}
inline std::vector<float> downKernel(int size) {
    std::vector<float> k(size / 2);
    const double alpha = 0.16, a0 = 0.5 * (1.0 - alpha), a1 = 0.5, a2 = 0.5 * alpha;
    const int n = size, half = n / 2;
    const double scale = 0.5;
    for (int i = 1; i < n; i += 2) {
        double s = scale * kPiD * (i - half);
        double sinc = !s ? 1.0 : fdlibm::sin(s) / s;
        sinc *= scale;
        double x = (double)i / n;
        double window = a0 - a1 * fdlibm::cos(kTwoPiD * x) + a2 * fdlibm::cos(kTwoPiD * 2.0 * x);
        k[(i - 1) / 2] = (float)(sinc * window);
    }
    return k;
}

class UpSampler {
public:
    static constexpr size_t kKernel = 128;
    explicit UpSampler(unsigned block) : block_(block), tmp_(block, 0.f), ib_(kKernel / 2 + block, 0.f) {
        std::vector<float> k = upKernel(kKernel);
        if (block_ <= kKernel) direct_.reset(new DirectConvolver(block_, k));
        else fft_.reset(new SimpleFFTConvolver(block_, k));
    }
    // source: block frames, dest: 2 * block frames (may be a different buffer only)
    void process(const float* src, float* dst) {
        const size_t h = kKernel / 2;
        std::copy(src, src + block_, ib_.begin() + h);
        for (size_t i = 0; i < block_; ++i) dst[i * 2] = ib_[i];
        if (direct_) direct_->process(src, tmp_.data()); else fft_->process(src, tmp_.data());
        for (size_t i = 0; i < block_; ++i) dst[i * 2 + 1] = tmp_[i];
        std::copy(ib_.begin() + block_, ib_.begin() + block_ + h, ib_.begin());
    }
    void reset() { if (direct_) direct_->reset(); if (fft_) fft_->reset(); std::fill(ib_.begin(), ib_.end(), 0.f); }
    size_t latencyFrames() const { return (direct_ ? direct_->kernelSize() : fft_->kernelSize()) / 2; }

private:
    size_t block_;
    std::unique_ptr<DirectConvolver> direct_;
    std::unique_ptr<SimpleFFTConvolver> fft_;
    std::vector<float> tmp_, ib_;
};

class DownSampler {
public:
    static constexpr size_t kKernel = 256;
    explicit DownSampler(unsigned block) : block_(block), tmp_(block / 2, 0.f), ib_(kKernel / 2 + block, 0.f) {
        std::vector<float> k = downKernel((int)kKernel);
        if (block_ <= kKernel) direct_.reset(new DirectConvolver(block_ / 2, k));
        else fft_.reset(new SimpleFFTConvolver(block_ / 2, k));
    }
    // source: block frames, dest: block / 2 frames
    void process(const float* src, float* dst) {
        const size_t h = kKernel / 2, d = block_ / 2;
        std::copy(src, src + block_, ib_.begin() + h);
        for (size_t i = 0; i < d; ++i) tmp_[i] = ib_[h - 1 + i * 2];
        if (direct_) direct_->process(tmp_.data(), dst); else fft_->process(tmp_.data(), dst);
        for (size_t i = 0; i < d; ++i) dst[i] += 0.5f * ib_[i * 2];
        std::copy(ib_.begin() + block_, ib_.begin() + block_ + h, ib_.begin());
    }
    void reset() { if (direct_) direct_->reset(); if (fft_) fft_->reset(); std::fill(ib_.begin(), ib_.end(), 0.f); }
    size_t latencyFrames() const { return (direct_ ? direct_->kernelSize() : fft_->kernelSize()) / 2; }

private:
    size_t block_;
    std::unique_ptr<DirectConvolver> direct_;
    std::unique_ptr<SimpleFFTConvolver> fft_;
    std::vector<float> tmp_, ib_;
};

// ---- the WaveShaperNode (wave_shaper_handler.cc) ---------------------------------------------------------------
enum class Oversample { None, X2, X4 };
inline Oversample oversampleOf(const std::string& s) { return s == "2x" ? Oversample::X2 : s == "4x" ? Oversample::X4 : Oversample::None; }

// GetSubBlockFrames: 128 when the quantum is a multiple of it, else the largest divisor up to 64
inline unsigned subBlockFrames(unsigned quantum) {
    if (quantum % 128 == 0) return 128;
    const unsigned mx = std::min(quantum, 64u);
    for (unsigned b = mx; b > 1; --b) if (quantum % b == 0) return b;
    return 1;
}

class WaveShaper {
public:
    explicit WaveShaper(unsigned quantum) : sub_(subBlockFrames(quantum)) {}
    unsigned subBlock() const { return sub_; }
    // ws.curve = Float32Array (SetCurve copies it)
    void setCurve(const std::vector<float>& c) { curve_ = c; }
    // ws.oversample = ... (SetOversample: lazy set-up, resets of stages that are no longer used)
    void setOversample(Oversample o) {
        os_ = o;
        for (auto& k : kernels_) applyOversample(*k);
    }
    Oversample oversample() const { return os_; }
    // frames of latency the node has (LatencyTime * sampleRate)
    size_t latencyFrames() const {
        if (os_ == Oversample::None) return 0;
        Kernel k(sub_);
        size_t a = k.up1.latencyFrames() + k.down1.latencyFrames();
        if (os_ == Oversample::X2) return a;
        return a + (k.up2.latencyFrames() + k.down2.latencyFrames()) / 2;
    }
    // One sub-block (exactly subBlock() frames, on the browser's grid) for `channels` channels; in may equal out.
    void processSubBlock(const float* const* in, float* const* out, int channels) {
        if ((int)kernels_.size() != channels) {   // CheckNumberOfChannelsForInput: Uninitialize, Initialize
            kernels_.clear();
            for (int c = 0; c < channels; c++) { kernels_.emplace_back(new Kernel(sub_)); applyOversample(*kernels_.back()); }
        }
        const unsigned n = sub_;
        for (int c = 0; c < channels; c++) {
            if (curve_.empty()) { if (out[c] != in[c]) std::copy(in[c], in[c] + n, out[c]); continue; }
            Kernel& k = *kernels_[c];
            switch (os_) {
                case Oversample::None: curveValues(out[c], in[c], n); break;
                case Oversample::X2:
                    k.up1.process(in[c], k.t1.data());
                    curveValues(k.t1.data(), k.t1.data(), n * 2);
                    k.down1.process(k.t1.data(), out[c]);
                    break;
                case Oversample::X4:
                    k.up1.process(in[c], k.t1.data());
                    k.up2.process(k.t1.data(), k.t2.data());
                    curveValues(k.t2.data(), k.t2.data(), n * 4);
                    k.down2.process(k.t2.data(), k.t1.data());
                    k.down1.process(k.t1.data(), out[c]);
                    break;
            }
        }
    }

private:
    struct Kernel {
        std::vector<float> t1, t2;
        UpSampler up1, up2;
        DownSampler down1, down2;
        explicit Kernel(unsigned sub) : t1(sub * 2), t2(sub * 4), up1(sub), up2(sub * 2), down1(sub * 2), down2(sub * 4) {}
    };
    void applyOversample(Kernel& k) {
        // the stages always exist here (LazyInitializeOversampling makes all four); what SetOversample resets:
        if (os_ == Oversample::None) { k.up1.reset(); k.down1.reset(); k.up2.reset(); k.down2.reset(); }
        else if (os_ == Oversample::X2) { k.up2.reset(); k.down2.reset(); }
    }
    // WaveShaperCurveValues (the SSE / NEON index path and the vector helpers): dest may equal source
    void curveValues(float* dest, const float* src, unsigned n) {
        vi_.resize(n); idx_.resize(n); v1_.resize(n); v2_.resize(n); f_.resize(n);
        const size_t len = curve_.size();
        vm::Vsadd(src, 1.0f, vi_.data(), n);
        vm::Vsmul(vi_.data(), (float)(0.5 * (double)(len - 1)), vi_.data(), n);
        vm::Vclip(vi_.data(), 0.f, (float)(len - 1), vi_.data(), n);
        const int maxIndex = (int)(len - 1);
        for (unsigned k = 0; k < n; ++k) {
            // _mm_cvttps_epi32 / vcvtq_s32_f32: truncation; the index stored back as a float
            int32_t i1 = (int32_t)vi_[k];
            int32_t i2 = i1 + 1;
            idx_[k] = (float)i1;
            i1 = std::min(std::max(i1, 0), maxIndex);
            i2 = std::min(std::max(i2, 0), maxIndex);
            v1_[k] = curve_[i1];
            v2_[k] = curve_[i2];
        }
        vm::Vsub(vi_.data(), idx_.data(), f_.data(), n);
        vm::Vsub(v2_.data(), v1_.data(), v2_.data(), n);
        vm::Vmul(f_.data(), v2_.data(), v2_.data(), n);
        vm::Vadd(v2_.data(), v1_.data(), dest, n);
    }
    unsigned sub_;
    Oversample os_ = Oversample::None;
    std::vector<float> curve_;
    std::vector<std::unique_ptr<Kernel>> kernels_;
    std::vector<float> vi_, idx_, v1_, v2_, f_;
};

// ---- the DelayNode (delay.cc, delay_sse2.cc / delay_neon.cc), one channel per line ------------------------------
// TimeToSampleFrame(t, sr, kRoundUp) (audio_utilities.cc)
inline size_t timeToSampleFrameUp(double t, double sr) {
    const double over = 1024;
    double frame = std::round(t * sr * over) / over;
    return (size_t)std::ceil(frame);
}
class DelayLine {
public:
    // maxDelay: the DelayNode's maxDelayTime (seconds), sr: the context's rate (float), quantum: its render quantum
    DelayLine(double maxDelay, float sr, unsigned quantum) : sr_(sr), q_(quantum), buf_(quantum + timeToSampleFrameUp(maxDelay, sr), 0.f) {}
    // delayTime.value = v (a float AudioParam, a-rate)
    void setDelayTime(double v) { dt_ = (float)v; }
    // Frames on the browser's grid: `posInQuantum` is the first frame's place in its render quantum. Each frame is
    // written, then read, exactly as the browser's block code computes it (writes of a whole quantum first do not
    // change what is read: the read position is always at least the delay behind).
    void process(const float* in, float* out, int n, int posInQuantum) {
        const size_t L = buf_.size();
        const unsigned vecFrames = (q_ / 4) * 4;   // the vector path covers whole groups of 4; the rest is scalar
        for (int i = 0; i < n; i++) {
            buf_[w_] = in[i];
            const unsigned pq = (unsigned)((posInQuantum + i) % (int)q_);
            float y;
            if (pq < vecFrames) {
                const float delay = dt_ > 0.f ? dt_ : 0.f;   // _mm_max_ps(delay, 0)
                const float desired = delay * sr_;
                float rp = (float)(int32_t)w_ + ((float)L - desired);
                if (rp >= (float)L) rp -= (float)L;
                int32_t r1 = (int32_t)rp;   // truncation
                if (r1 >= (int32_t)L) r1 -= (int32_t)L;
                int32_t r2 = r1 + 1;
                if (r2 >= (int32_t)L) r2 -= (int32_t)L;
                const float f = rp - (float)r1;
                const float s1 = buf_[(size_t)r1], s2 = buf_[(size_t)r2];
                y = s1 + f * (s2 - s1);
            } else {
                double delay_time = std::fmax((double)dt_, 0);
                double desired = delay_time * (double)sr_;
                double rp = (double)w_ + (double)L - desired;
                if (rp >= (double)L) rp -= (double)L;
                size_t r1 = (size_t)rp, r2 = r1 + 1;
                if (r2 >= L) r2 -= L;
                const float f = (float)(rp - (double)r1);
                const float s1 = buf_[r1], s2 = buf_[r2];
                y = s1 + f * (s2 - s1);
            }
            out[i] = y;
            if (++w_ >= L) w_ -= L;
        }
    }
    void reset() { std::fill(buf_.begin(), buf_.end(), 0.f); }

private:
    float sr_;
    unsigned q_;
    std::vector<float> buf_;
    size_t w_ = 0;
    float dt_ = 0.f;
};

}  // namespace cr
}  // namespace al
