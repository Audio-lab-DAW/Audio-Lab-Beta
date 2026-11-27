// The engine core's graph, first part (task NB-N3a): a chain of devices run block by block, the way the web
// engine runs a track's effects (in series, 128-frame render quanta). Tracks, the mixer (gains, pans, sends,
// groups, returns) and the master come in the next parts; they are browser nodes in the web engine and are
// ported from Chromium's arithmetic (plan section 4.2).
#pragma once
#include <memory>
#include <string>
#include <vector>
#include "device.h"

namespace al {

void registerCoreDevices();

constexpr int kQuantum = 128;  // the web engine's render quantum

struct ChainSlot {
    std::string type;
    bool on = true;
    std::unique_ptr<WorkletShell> dev;
};

class Chain {
public:
    explicit Chain(RenderContext& ctx) : ctx_(ctx) {}
    // Adds a device by its type in the app (FXDEF name). Returns false if the engine has no port of it yet.
    bool add(const std::string& type, const JValue& params, std::string& err) {
        registerCoreDevices();
        auto it = deviceRegistry().find(type);
        if (it == deviceRegistry().end()) { err = "no native port of device '" + type + "' yet"; return false; }
        ChainSlot s; s.type = type;
        s.dev.reset(new WorkletShell(it->second(ctx_), ctx_));
        // processorOptions.p: the settings the worklet is created with
        if (params.t == JValue::Object) s.dev->set(params);
        slots_.push_back(std::move(s));
        return true;
    }
    size_t size() const { return slots_.size(); }
    ChainSlot& slot(size_t i) { return slots_[i]; }
    // One block in place (n <= kQuantum).
    void process(float* L, float* R, int n) {
        float tL[kQuantum], tR[kQuantum];
        for (auto& s : slots_) {
            if (!s.on) continue;
            s.dev->process(L, R, tL, tR, n);
            for (int i = 0; i < n; i++) { L[i] = tL[i]; R[i] = tR[i]; }
        }
    }

private:
    RenderContext& ctx_;
    std::vector<ChainSlot> slots_;
};

// Offline render of planar stereo through a chain, in whole render quanta (like an OfflineAudioContext, the
// last quantum is padded with silence and the output cut to the input's length).
inline void renderChain(Chain& ch, const std::vector<float>& inL, const std::vector<float>& inR, std::vector<float>& outL, std::vector<float>& outR) {
    const size_t N = inL.size();
    outL.assign(N, 0); outR.assign(N, 0);
    float L[kQuantum], R[kQuantum];
    for (size_t pos = 0; pos < N; pos += kQuantum) {
        const size_t m = std::min((size_t)kQuantum, N - pos);
        for (size_t i = 0; i < (size_t)kQuantum; i++) { L[i] = i < m ? inL[pos + i] : 0.f; R[i] = i < m ? inR[pos + i] : 0.f; }
        ch.process(L, R, kQuantum);
        for (size_t i = 0; i < m; i++) { outL[pos + i] = L[i]; outR[pos + i] = R[i]; }
    }
}

}  // namespace al
