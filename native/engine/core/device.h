// The engine core's device interface (task NB-N3a).
//
// A device takes a stereo block and writes a stereo block. The ported worklet devices are wrapped in
// WorkletShell, which repeats what the web engine's worklet bundle does around every processor (dnGuard and
// dnFlush in WLSRC, index.html):
//   - skip on silence: once the input has been exactly silent for more than 3 seconds the device is not run
//     and outputs zeros, and its state stands still until sound comes back;
//   - every 16 blocks that ran, state values below 1e-30 (in size) are set to exactly zero.
// Both change the bits of the output, so a port that leaves them out cannot match the web engine.
//
// Design rule from the picks (U-questions, NM1): the engine keeps all state and the interface is a view on it.
// So a device exposes its settings (set) and its meter values (meters) and nothing about drawing.
#pragma once
#include <algorithm>
#include <cmath>
#include <functional>
#include <map>
#include <memory>
#include <string>
#include <vector>
#include "jsmath.h"
#include "params.h"

namespace al {

struct RenderContext {
    double sampleRate = 48000;
    WorkletRandom random;  // Math.random of the worklet scope: one per audio context
    double currentFrame = 0;  // first frame of the block being rendered; currentTime = currentFrame / sampleRate
    // The web engine's render quantum, the grid its worklet bundle keeps its rules on: 128 while playing,
    // 512 in the app's export (renderSizeHint in renderMix). Up to 4096.
    int quantum = 128;
    double currentTime() const { return currentFrame / sampleRate; }
};

// What a ported processor implements. process() is the body of the worklet's process(); flushTiny() zeroes the
// state values dnFlush would find (own numeric fields, plain number arrays up to 64 long, Float64Arrays up to 64
// long; never Float32Arrays or longer arrays).
struct Processor {
    virtual ~Processor() = default;
    Params p;  // this.p
    int pv = 0;  // this.pv: counts settings that arrived as messages after the device was made
    // processorOptions.p: the settings the worklet is made with (no message, pv stays)
    void init(const JValue& np) { p.assign(np); }
    // port.onmessage {p}: Object.assign(this.p, d.p); this.pv++
    virtual void set(const JValue& np) { p.assign(np); pv++; }
    virtual void process(const float* L, const float* R, float* oL, float* oR, int n) = 0;
    virtual void flushTiny() = 0;
    virtual std::vector<std::pair<std::string, double>> meters() const { return {}; }
    // A worklet whose dnGuard has run=true (the meter, tape stop) keeps running on silence.
    virtual bool runsOnSilence() const { return false; }
    // Where the current call sits on the web engine's 128-frame grid (set by WorkletShell before each call):
    // currentTime in the worklet is winStart / sampleRate, and the call's first frame is frame winOff of it.
    double winStart = 0;
    int winOff = 0;
    static void z(double& v) { if (v < 1e-30 && v > -1e-30 && v != 0) v = 0; }
};

// WorkletShell runs a ported processor the way the web engine runs the worklet, on the web engine's grid of
// render quanta (128 frames while playing, 512 in the app's export; RenderContext::quantum), whatever the size
// of the calls it is given (task NB-N3c): a call may be 32 or 64 frames
// (the audio device's own buffer) or longer (offline render); the bundle's rules still apply per window:
//   - the silence rule looks at a whole window: when the window can be skipped (more than 3 s of silence before
//     it) and its first frames are silent, they are output as zeros; if sound arrives later in the same window,
//     the silent frames are run through the device first (their output discarded: the web engine computed them,
//     and after 3 s of silence they come out as zeros), so the device's state is exactly the web engine's;
//   - the tiny-value guard runs after every 16th window that ran, at its last frame;
//   - the processor is told where in its window each call starts (Processor::winStart, winOff), for the devices
//     that read currentTime.
// So a call size that is not 128 adds no latency and changes no bits.
class WorkletShell {
public:
    WorkletShell(std::unique_ptr<Processor> proc, const RenderContext& ctx) : p_(std::move(proc)), ctx_(ctx), sr_(ctx.sampleRate) {}
    Processor& proc() { return *p_; }
    void set(const JValue& np) { p_->set(np); }
    // ctx.currentFrame must be the frame of L[0].
    void process(const float* L, const float* R, float* oL, float* oR, int n) {
        int done = 0;
        while (done < n) {
            const double frame = ctx_.currentFrame + done;
            const int W = win();
            const int off = (int)std::fmod(frame, (double)W);
            const int m = std::min(n - done, W - off);
            piece(L + done, R + done, oL + done, oR + done, m, frame - off, off);
            done += m;
        }
    }
    bool skipping() const { return q_ > sr_ * 3; }
    long catchUpFrames() const { return catchUp_; }
    long catchUpNonZero() const { return catchUpNZ_; }
    static constexpr int kMaxWin = 4096;
    int win() const { return std::max(1, std::min(kMaxWin, ctx_.quantum)); }

private:
    void piece(const float* L, const float* R, float* oL, float* oR, int m, double winStart, int off) {
        const int W = win();
        if (off == 0) { winSilent_ = true; winRan_ = false; pend_ = 0; mayskip_ = !p_->runsOnSilence() && (q_ + W > sr_ * 3); }
        bool sil = true;
        for (int i = 0; i < m && sil; i++) if (L[i] != 0 || R[i] != 0) sil = false;
        if (!sil) winSilent_ = false;
        if (mayskip_ && winSilent_) {
            for (int i = 0; i < m; i++) { oL[i] = 0; oR[i] = 0; pL_[pend_ + i] = L[i]; pR_[pend_ + i] = R[i]; }
            pend_ += m;
        } else {
            if (pend_ > 0) {  // sound arrived inside a window that started silent: run the silent frames first
                std::vector<float>& tL = tmpL_; std::vector<float>& tR = tmpR_;
                tL.resize(kMaxWin); tR.resize(kMaxWin);
                p_->winStart = winStart; p_->winOff = off - pend_;
                p_->process(pL_.data(), pR_.data(), tL.data(), tR.data(), pend_);
                catchUp_ += pend_;
                for (int i = 0; i < pend_; i++) if (tL[i] != 0 || tR[i] != 0) catchUpNZ_++;
                pend_ = 0;
            }
            p_->winStart = winStart; p_->winOff = off;
            p_->process(L, R, oL, oR, m);
            winRan_ = true;
        }
        if (off + m == W) {  // end of the window
            if (!p_->runsOnSilence()) { if (winSilent_) q_ += W; else q_ = 0; }
            if (winRan_ && ++c_ >= 16) { c_ = 0; p_->flushTiny(); }
        }
    }
    std::unique_ptr<Processor> p_;
    const RenderContext& ctx_;
    double sr_;
    double q_ = 0;
    int c_ = 0;
    bool winSilent_ = true, winRan_ = false, mayskip_ = false;
    int pend_ = 0;
    std::vector<float> pL_ = std::vector<float>(kMaxWin), pR_ = std::vector<float>(kMaxWin);  // silent frames held back (may be -0)
    std::vector<float> tmpL_, tmpR_;
    long catchUp_ = 0, catchUpNZ_ = 0;
};

// The registry: device type (FXDEF name in the app) -> factory.
using ProcessorFactory = std::function<std::unique_ptr<Processor>(RenderContext&)>;
inline std::map<std::string, ProcessorFactory>& deviceRegistry() {
    static std::map<std::string, ProcessorFactory> r;
    return r;
}
struct RegisterDevice {
    RegisterDevice(const char* type, ProcessorFactory f) { deviceRegistry()[type] = std::move(f); }
};

}  // namespace al
