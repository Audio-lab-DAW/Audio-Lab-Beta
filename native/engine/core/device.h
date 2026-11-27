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
};

// What a ported processor implements. process() is the body of the worklet's process(); flushTiny() zeroes the
// state values dnFlush would find (own numeric fields, plain number arrays up to 64 long, Float64Arrays up to 64
// long; never Float32Arrays or longer arrays).
struct Processor {
    virtual ~Processor() = default;
    Params p;  // this.p
    virtual void set(const JValue& np) { p.assign(np); }
    virtual void process(const float* L, const float* R, float* oL, float* oR, int n) = 0;
    virtual void flushTiny() = 0;
    virtual std::vector<std::pair<std::string, double>> meters() const { return {}; }
    // A worklet whose dnGuard has run=true (the meter, tape stop) keeps running on silence.
    virtual bool runsOnSilence() const { return false; }
    static void z(double& v) { if (v < 1e-30 && v > -1e-30 && v != 0) v = 0; }
};

class WorkletShell {
public:
    WorkletShell(std::unique_ptr<Processor> proc, const RenderContext& ctx) : p_(std::move(proc)), sr_(ctx.sampleRate) {}
    Processor& proc() { return *p_; }
    void set(const JValue& np) { p_->set(np); }
    // n is the render quantum (128 in the web engine).
    void process(const float* L, const float* R, float* oL, float* oR, int n) {
        if (!p_->runsOnSilence()) {
            bool sil = true;
            for (int i = 0; i < n && sil; i++) if (L[i] != 0) sil = false;
            for (int i = 0; i < n && sil; i++) if (R[i] != 0) sil = false;
            if (sil) {
                q_ += n;
                if (q_ > sr_ * 3) {
                    for (int i = 0; i < n; i++) { oL[i] = 0; oR[i] = 0; }
                    return;
                }
            } else q_ = 0;
        }
        p_->process(L, R, oL, oR, n);
        if (++c_ >= 16) { c_ = 0; p_->flushTiny(); }
    }
    bool skipping() const { return q_ > sr_ * 3; }

private:
    std::unique_ptr<Processor> p_;
    double sr_;
    double q_ = 0;
    int c_ = 0;
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
