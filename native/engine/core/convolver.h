// Chromium's ConvolverNode, ported for the native engine (task NB-N3i).
//
// The app's Space reverb ('reverb', on Fractals' "Plate reverb" return) is a ConvolverNode fed with an impulse the
// app generates (irBuf in index.html). This is a statement-by-statement port of Chromium 158.0.8127.36:
//   modules/webaudio/convolver_handler.cc         the node: render slice = the render quantum, max FFT 8192, normalize
//   platform/audio/reverb.cc                      the normalisation scale (RMS power, -58 dB, 44.1 kHz) and the
//                                                 input -> response -> output channel cases
//   platform/audio/reverb_convolver.cc            the stages: a direct convolver for the first 64 frames, then FFT
//                                                 stages of 128, 128, 256, ... up to 8192 points
//   platform/audio/reverb_convolver_stage.cc      each stage's pre-delay and post-delay (render phase per channel)
//   platform/audio/reverb_accumulation_buffer.cc  where the stages add their output
//   platform/audio/fft_convolver.cc               overlap-add on FFTFrame (part 1's RustFFT wrapper, webnodes.h)
//   platform/audio/direct_convolver.cc            waveshaper.h's DirectConvolver (Conv with the reversed kernel)
//   platform/audio/vector_math (x86, mac, neon)   Vsvesq for the normalisation: on x86 Chromium splits the buffer
//                                                 by its alignment into scalar, SSE (4 lanes) and AVX (8 lanes) parts,
//                                                 each summed on its own; on the Mac vDSP_svesq
// What decides the bits:
//   - the normalisation scale is one float from a sum of squares whose order depends on the CPU (AVX or not) and on
//     where the AudioBuffer's channel data starts (measured: 32-byte aligned in Chromium 158, alignment offset 0);
//   - every stage runs on whole render quanta (the direct convolver takes exactly one), so the node must run on the
//     browser's grid of render quanta (128 frames, 512 in the app's export): dev_reverb.h holds the calls to it;
//   - each stage's pre-delay is chosen from its "render phase" (the second channel's stages start one quantum later),
//     which changes how the input is cut into FFT blocks and so the rounding: the port keeps it exactly.
// Not ported: Chromium stops a ConvolverNode (and the nodes before it) once its input has been flagged silent for
// longer than the impulse (its tail time); when sound comes back the stages resume where they stopped, so their
// FFT blocks are cut at another place than a node that never stopped. That needs the graph's silence flags (sources
// that end), which come with clips as sources (N3 later); a buffer source that plays through, as in the tests and
// the app's export of a clip-free bus, never sets them.
// Build with -ffp-contract=off.
#pragma once
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <memory>
#include <vector>
#include "../../third_party/fdlibm/ieee754.h"
#include "waveshaper.h"   // vm::Conv, Vadd, Vsmul; DirectConvolver; FFTFrame helpers
#if defined(__APPLE__)
#include <Accelerate/Accelerate.h>
#endif
#if defined(__SSE2__) || defined(_M_X64)
#include <immintrin.h>
#endif

namespace al {
namespace cr {

namespace vm {
inline bool cpuSupportsAVX() {
#if (defined(__x86_64__) || defined(__i386__)) && (defined(__GNUC__) || defined(__clang__))
    static const bool s = __builtin_cpu_supports("avx");
    return s;
#else
    return false;
#endif
}
inline float vsvesqScalar(const float* x, size_t n) {
    float sum = 0;
    for (size_t i = 0; i < n; i++) { const float p = x[i] * x[i]; sum += p; }
    return sum;
}
// sse::Vsvesq / avx::Vsvesq: L lanes summed from 0, then the lanes added in order into a float from 0
inline float vsvesqLanes(const float* x, size_t n, size_t L) {
    float lane[8] = {0, 0, 0, 0, 0, 0, 0, 0};
    for (size_t i = 0; i + L <= n; i += L)
        for (size_t j = 0; j < L; j++) { const float p = x[i + j] * x[i + j]; lane[j] = lane[j] + p; }
    float sum = 0;
    for (size_t j = 0; j < L; j++) sum += lane[j];
    return sum;
}
// Vsvesq: the sum of squares. alignOffset: the buffer's start in floats past a 32-byte boundary (x86 only).
inline float Vsvesq(const float* x, size_t n, size_t alignOffset = 0) {
#if defined(__APPLE__)
    (void)alignOffset;
    float sum = 0;
    vDSP_svesq(x, 1, &sum, n);
    return sum;
#elif defined(__x86_64__) || defined(_M_X64) || defined(__i386__)
    // x86::SplitFramesToProcess
    const size_t total = (8 - (alignOffset & 7)) & 7;   // (kPackedFloatsPerRegister - offset) & ~kFramesToProcessMask
    const size_t scalarAl = total & 3, sseAl = total & ~(size_t)3;
    size_t left = n;
    const bool avx = cpuSupportsAVX() && left >= scalarAl + sseAl + 8;
    const bool sse = avx || left >= scalarAl + 4;
    size_t cScalarAl = 0, cSseAl = 0, cAvx = 0, cSse = 0;
    if (sse) {
        cScalarAl = scalarAl; left -= cScalarAl;
        if (avx) { cSseAl = sseAl; left -= cSseAl; cAvx = left & ~(size_t)7; left -= cAvx; }
        cSse = left & ~(size_t)3; left -= cSse;
    }
    float sum = 0;
    size_t o = 0;
    if (cScalarAl) { sum += vsvesqScalar(x + o, cScalarAl); o += cScalarAl; }
    if (cSseAl) { sum += vsvesqLanes(x + o, cSseAl, 4); o += cSseAl; }
    if (cAvx) { sum += vsvesqLanes(x + o, cAvx, 8); o += cAvx; }
    if (cSse) { sum += vsvesqLanes(x + o, cSse, 4); o += cSse; }
    if (left) { sum += vsvesqScalar(x + o, left); o += left; }
    return sum;
#else
    // neon::Vsvesq: four lanes (multiply, then add), the halves added pairwise, the tail scalar
    (void)alignOffset;
    const size_t tail = n % 4, al = n - tail;
    float sum = 0;
    if (al >= 4) {
        float lane[4] = {0, 0, 0, 0};
        for (size_t i = 0; i < al; i += 4)
            for (size_t j = 0; j < 4; j++) { const float p = x[i + j] * x[i + j]; lane[j] = lane[j] + p; }
        const float t0 = lane[0] + lane[2], t1 = lane[1] + lane[3];
        sum = t0 + t1;
    }
    if (tail) sum += vsvesqScalar(x + al, tail);
    return sum;
#endif
}
}  // namespace vm

// ---- FFTConvolver (fft_convolver.cc) ----------------------------------------------------------------------------
class FFTConvolver {
public:
    explicit FFTConvolver(unsigned fftSize) : frame_(fftSize), in_(fftSize, 0.f), out_(fftSize, 0.f), overlap_(fftSize / 2, 0.f) {}
    void process(FFTFrame& kernel, const float* src, float* dst, size_t n) {
        const size_t half = frame_.size() / 2;
        while (n) {
            const size_t k = std::min(n, half - rw_);
            std::copy(src, src + k, in_.begin() + rw_);
            std::copy(out_.begin() + rw_, out_.begin() + rw_ + k, dst);
            src += k; dst += k; n -= k;
            rw_ += k;
            if (rw_ == half) {
                frame_.doFFT(in_.data());
                fftMultiply(frame_, kernel);
                frame_.doInverseFFT(out_.data());
                vm::Vadd(out_.data(), overlap_.data(), out_.data(), half);
                std::copy(out_.begin() + half, out_.begin() + 2 * half, overlap_.begin());
                rw_ = 0;
            }
        }
    }
    void reset() { std::fill(overlap_.begin(), overlap_.end(), 0.f); rw_ = 0; }

private:
    FFTFrame frame_;
    std::vector<float> in_, out_, overlap_;   // in_'s second half stays zero
    size_t rw_ = 0;
};

// ---- ReverbAccumulationBuffer (reverb_accumulation_buffer.cc) ---------------------------------------------------
class ReverbAccumulationBuffer {
public:
    explicit ReverbAccumulationBuffer(size_t n) : b_(n, 0.f) {}
    void readAndClear(float* dst, size_t n) {
        const size_t L = b_.size(), avail = L - r_, n1 = std::min(n, avail), n2 = n - n1;
        std::copy(b_.begin() + r_, b_.begin() + r_ + n1, dst);
        std::fill(b_.begin() + r_, b_.begin() + r_ + n1, 0.f);
        if (n2) { std::copy(b_.begin(), b_.begin() + n2, dst + n1); std::fill(b_.begin(), b_.begin() + n2, 0.f); }
        r_ = (r_ + n) % L;
    }
    void updateReadIndex(uint32_t& ri, size_t n) const { ri = (uint32_t)((ri + n) % b_.size()); }
    void accumulate(const float* src, size_t n, uint32_t& ri, size_t delay) {
        const size_t L = b_.size(), w = (ri + delay) % L;
        ri = (uint32_t)((ri + n) % L);
        const size_t n1 = std::min(n, L - w), n2 = n - n1;
        vm::Vadd(src, b_.data() + w, b_.data() + w, n1);
        if (n2) vm::Vadd(src + n1, b_.data(), b_.data(), n2);
    }

private:
    std::vector<float> b_;
    size_t r_ = 0;
};

// ---- ReverbConvolverStage (reverb_convolver_stage.cc) -----------------------------------------------------------
class ReverbConvolverStage {
public:
    ReverbConvolverStage(const float* ir, size_t totalLatency, size_t offset, unsigned length, unsigned fftSize, size_t renderPhase,
                         unsigned slice, ReverbAccumulationBuffer* acc, float scale, bool direct)
        : acc_(acc), direct_(direct), tmp_(slice, 0.f) {
        if (!direct_) {
            kernel_.reset(new FFTFrame(fftSize));
            fftPadded(*kernel_, ir + offset, length);
            if (scale != 1) { vm::Vsmul(kernel_->real().data(), scale, kernel_->real().data(), kernel_->real().size());
                              vm::Vsmul(kernel_->imag().data(), scale, kernel_->imag().data(), kernel_->imag().size()); }
            fft_.reset(new FFTConvolver(fftSize));
        } else {
            std::vector<float> k(fftSize / 2, 0.f);
            std::copy(ir, ir + length, k.begin());
            if (scale != 1) vm::Vsmul(k.data(), scale, k.data(), length);
            directConv_.reset(new DirectConvolver(slice, std::move(k)));
        }
        size_t totalDelay = offset + totalLatency;
        const size_t half = fftSize / 2;
        if (!direct_ && totalDelay >= half) totalDelay -= half;
        const size_t maxPre = std::min(half, totalDelay);
        pre_ = totalDelay > 0 ? renderPhase % maxPre : 0;
        if (slice > 0) pre_ = (pre_ / slice) * slice;
        if (pre_ > totalDelay) pre_ = 0;
        post_ = totalDelay - pre_;
        size_t dbs = pre_ < fftSize ? fftSize : pre_;
        dbs = dbs < slice ? slice : dbs;
        preBuf_.assign(dbs, 0.f);
    }
    void process(const float* src, size_t n) {
        const float* preSrc;
        float* preDst = nullptr;
        float* tmp;
        if (pre_ > 0) {
            if (preRW_ + n > preBuf_.size()) return;
            if (n > tmp_.size()) return;
            preDst = preBuf_.data() + preRW_;
            preSrc = preDst;
            tmp = tmp_.data();
        } else {
            preSrc = src;
            tmp = preBuf_.data();
            if (n > preBuf_.size()) return;
        }
        if (done_ < pre_) {
            acc_->updateReadIndex(ri_, n);
        } else {
            if (direct_) directConv_->process(preSrc, tmp);   // exactly one render quantum
            else fft_->process(*kernel_, preSrc, tmp, n);
            acc_->accumulate(tmp, n, ri_, post_);
        }
        if (pre_ > 0) {
            std::copy(src, src + n, preDst);
            preRW_ += n;
            if (preRW_ >= pre_) preRW_ = 0;
        }
        done_ += n;
    }

private:
    ReverbAccumulationBuffer* acc_;
    bool direct_;
    std::unique_ptr<FFTFrame> kernel_;
    std::unique_ptr<FFTConvolver> fft_;
    std::unique_ptr<DirectConvolver> directConv_;
    std::vector<float> preBuf_, tmp_;
    size_t pre_ = 0, post_ = 0, preRW_ = 0, done_ = 0;
    uint32_t ri_ = 0;
};

// ---- ReverbConvolver (reverb_convolver.cc) ----------------------------------------------------------------------
class ReverbConvolver {
public:
    static constexpr unsigned kMinFFTSize = 128;
    ReverbConvolver(const float* ir, size_t len, unsigned slice, unsigned maxFft, size_t phase, float scale) : acc_(len + slice) {
        size_t off = 0;
        int i = 0;
        unsigned fft = kMinFFTSize;
        while (off < len) {
            unsigned sz = fft / 2;
            if (sz + off > len) sz = (unsigned)(len - off);
            const size_t rp = phase + (size_t)i * slice;
            const bool direct = !off;
            stages_.emplace_back(new ReverbConvolverStage(ir, 0, off, sz, fft, rp, slice, &acc_, scale, direct));
            off += sz;
            ++i;
            if (!direct) fft *= 2;
            if (fft > maxFft) fft = maxFft;
        }
    }
    void process(const float* src, float* dst, size_t n) {
        for (auto& s : stages_) s->process(src, n);
        acc_.readAndClear(dst, n);
    }
    size_t stages() const { return stages_.size(); }

private:
    ReverbAccumulationBuffer acc_;
    std::vector<std::unique_ptr<ReverbConvolverStage>> stages_;
};

// ---- Reverb (reverb.cc) for a 1- or 2-channel impulse (the app makes 2) -----------------------------------------
class Reverb {
public:
    static constexpr float kGainCalibration = -58;
    static constexpr float kGainCalibrationSampleRate = 44100;
    static constexpr float kMinPower = 0.000125f;
    // CalculateNormalizationScale
    static float normalizationScale(const std::vector<std::vector<float>>& ch, float sampleRate, size_t alignOffset = 0) {
        const unsigned nch = (unsigned)ch.size();
        const uint32_t length = (uint32_t)ch[0].size();
        float power = 0;
        for (unsigned i = 0; i < nch; ++i) { const float cp = vm::Vsvesq(ch[i].data(), length, alignOffset); power += cp; }
        power = std::sqrt(power / (float)(nch * length));   // float / unsigned -> float; sqrt(float)
        if (!std::isfinite(power) || power < kMinPower) power = kMinPower;
        float scale = 1 / power;
        scale *= fdlibm::powf(10, kGainCalibration * 0.05f);
        if (sampleRate) scale *= kGainCalibrationSampleRate / sampleRate;
        if (nch == 4) scale *= 0.5f;
        return scale;
    }
    static constexpr unsigned kMaxFftSize = 8192;   // convolver_handler.cc
    // ConvolverHandler::SetBuffer: Reverb::TryCreate(bus, RenderQuantumFrames(), kMaxFftSize, normalize)
    Reverb(const std::vector<std::vector<float>>& ir, float sampleRate, unsigned slice, bool normalize = true, size_t alignOffset = 0)
        : nresp_((unsigned)ir.size()), slice_(slice) {
        const float scale = normalize ? normalizationScale(ir, sampleRate, alignOffset) : 1.f;
        scale_ = scale;
        const unsigned nconv = std::max(nresp_, 2u);
        size_t phase = 0;
        for (unsigned i = 0; i < nconv; ++i) {
            const std::vector<float>& c = ir[std::min(i, nresp_ - 1)];
            conv_.emplace_back(new ReverbConvolver(c.data(), c.size(), slice, kMaxFftSize, phase, scale));
            phase += slice;
        }
    }
    // Process for a 1- or 2-channel input and 2 output channels (cases 2, 4 and 5 of reverb.cc)
    void process(const float* inL, const float* inR, bool monoIn, float* outL, float* outR, size_t n) {
        if (!monoIn) { conv_[0]->process(inL, outL, n); conv_[1]->process(inR, outR, n); }
        else if (nresp_ == 2) { conv_[0]->process(inL, outL, n); conv_[1]->process(inL, outR, n); }
        else { conv_[0]->process(inL, outL, n); std::copy(outL, outL + n, outR); }   // case 1 then up-mixed (1 response, mono in)
    }
    float scale() const { return scale_; }
    size_t stages() const { return conv_.empty() ? 0 : conv_[0]->stages(); }

private:
    unsigned nresp_, slice_;
    float scale_ = 1;
    std::vector<std::unique_ptr<ReverbConvolver>> conv_;
};

}  // namespace cr
}  // namespace al
