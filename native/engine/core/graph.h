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
constexpr int kMaxBlock = 4096;

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
        if (params.t == JValue::Object) s.dev->proc().init(params);
        slots_.push_back(std::move(s));
        return true;
    }
    size_t size() const { return slots_.size(); }
    RenderContext& ctx() { return ctx_; }
    ChainSlot& slot(size_t i) { return slots_[i]; }
    // One block in place (n <= kMaxBlock).
    void process(float* L, float* R, int n) {
        float tL[kMaxBlock], tR[kMaxBlock];
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

// Offline render of planar stereo through a chain, in whole blocks (like an OfflineAudioContext, the last
// block is padded with silence and the output cut to the input's length). The web engine always uses 128;
// other sizes are for the block-size test (task NB-N3c): a device that gives the same bits at 32, 64 and 512
// can run at the audio device's own buffer with no 128-frame adapter.
inline void renderChain(Chain& ch, const std::vector<float>& inL, const std::vector<float>& inR, std::vector<float>& outL, std::vector<float>& outR, int block = kQuantum) {
    const size_t N = inL.size();
    if (block < 1) block = 1;
    if (block > kMaxBlock) block = kMaxBlock;
    outL.assign(N, 0); outR.assign(N, 0);
    std::vector<float> Lv(block), Rv(block);
    float* L = Lv.data(); float* R = Rv.data();
    for (size_t pos = 0; pos < N; pos += block) {
        const size_t m = std::min((size_t)block, N - pos);
        for (size_t i = 0; i < (size_t)block; i++) { L[i] = i < m ? inL[pos + i] : 0.f; R[i] = i < m ? inR[pos + i] : 0.f; }
        ch.ctx().currentFrame = (double)pos;
        ch.process(L, R, block);
        for (size_t i = 0; i < m; i++) { outL[pos + i] = L[i]; outR[pos + i] = R[i]; }
    }
}

}  // namespace al
