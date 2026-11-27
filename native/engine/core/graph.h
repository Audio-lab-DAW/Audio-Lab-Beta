// The engine core's graph, first part (task NB-N3a): a chain of devices run block by block, the way the web
// engine runs a track's effects (in series, 128-frame render quanta). Tracks, the mixer (gains, pans, sends,
// groups, returns) and the master come in the next parts; they are browser nodes in the web engine and are
// ported from Chromium's arithmetic (plan section 4.2).
#pragma once
#include <memory>
#include <string>
#include <vector>
#include "device.h"
#if defined(__x86_64__) || defined(_M_X64)
#include <xmmintrin.h>
#endif

namespace al {

void registerCoreDevices();

// The floating-point state the web engine's devices are computed with: round to nearest, denormal numbers kept
// (Chromium's worklet thread does not flush them; measured in N3c: flushing breaks every device). A plug-in may
// leave flush-to-zero on (review RN5, A7), so every chain sets the state at its start and puts the caller's back.
struct WebFloatState {
#if defined(__x86_64__) || defined(_M_X64)
    unsigned int saved;
    WebFloatState() { saved = _mm_getcsr(); _mm_setcsr((saved & ~0x8040u & ~0x6000u)); }  // FTZ, DAZ off; nearest
    ~WebFloatState() { _mm_setcsr(saved); }
#elif defined(__aarch64__)
    uint64_t saved;
    WebFloatState() { __asm__ volatile("mrs %0, fpcr" : "=r"(saved)); uint64_t v = saved & ~((1ull << 24) | (1ull << 19) | (3ull << 22)); __asm__ volatile("msr fpcr, %0" : : "r"(v)); }  // FZ, FZ16 off; nearest
    ~WebFloatState() { __asm__ volatile("msr fpcr, %0" : : "r"(saved)); }
#else
    WebFloatState() {}
#endif
    WebFloatState(const WebFloatState&) = delete;
    WebFloatState& operator=(const WebFloatState&) = delete;
};


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
    // One block in place (n <= kMaxBlock). mono (optional): in, whether the block has one channel (L, with R a
    // copy); out, whether it still has one. A worklet device always gives two channels; a browser-node device (the
    // Pro EQ) keeps one channel one, as the web engine's nodes do.
    void process(float* L, float* R, int n, bool* mono = nullptr) {
        WebFloatState fp;
        float tL[kMaxBlock], tR[kMaxBlock];
        bool m = mono && *mono;
        for (auto& s : slots_) {
            if (!s.on) continue;
            Processor& pr = s.dev->proc();
            pr.monoIn = m;
            s.dev->process(L, R, tL, tR, n);
            m = pr.worklet() ? false : pr.monoOut;
            for (int i = 0; i < n; i++) { L[i] = tL[i]; R[i] = tR[i]; }
        }
        if (mono) *mono = m;
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
