// The mixer's buses (task NB-N3d): tracks, groups, returns, sends, delay compensation and the master's chain,
// with the core's devices (native/engine/core) on every track, group, return and on the master.
// Portable C++; every check runs on Linux and on the Mac (tools/native-lab/run_bus.py).
//
// The shape is the web engine's export (renderMix in index.html), node for node:
//   a node (track, group or return): input -> devices -> delay (delay compensation) -> volume -> pan
//   a track's pan goes into its group's input, or the master's; each send is a gain from the track's pan into the
//   return's input; the master: gain -> devices -> out.
// Chromium's arithmetic for these (found by comparing with the app's own render, tools/native-lab/run_bus.py):
//   - an input with one connection passes that connection's samples on untouched; with two or more it starts from
//     zero and adds each in turn (AudioNodeInput::SumAllConnections), a mono connection into a stereo input to both
//     sides; with none it is one channel of silence;
//   - the delay compensation's DelayNode, at a whole number of samples, is an exact copy (measured: a delay of
//     d/48000 s with d = 1, 7, 96, 240, 2048 gives the input d samples later, bit for bit, at 128 and 512);
//   - gains and pans as in al_mix.h (N3b).
// The order in which a bus adds its connections is the order the export connects them, but with three or more
// Chromium keeps them in a hash set and its order changes between renders (N3b): `order` per bus reproduces one.
#pragma once
#include "../../dsp/al_mix.h"
#include "../core/graph.h"
#include <functional>
#include <map>
#include <memory>
#include <string>
#include <vector>

namespace al {

struct BusConn { int from = -1; bool send = false; float level = 1; };   // a node's pan, directly or through a send gain

struct BusNode {
    std::string id, kind;                    // kind: "audio", "group", "return"
    std::vector<float> srcL, srcR; bool hasSrc = false, srcMono = false;
    std::unique_ptr<Chain> chain;
    int delay = 0;                           // delay compensation in samples
    std::vector<float> dlL, dlR; size_t dlPos = 0;
    float vol = 1, pan = 0;
    std::vector<BusConn> in;                 // the connections into this node's input, in summing order
    // this quantum's output (after the pan): always stereo
    std::vector<float> oL, oR;
};

struct BusGraph {
    double sr = 48000;
    int quantum = 512;
    float master = 1;
    RenderContext ctx;
    std::unique_ptr<Chain> masterChain;
    std::vector<BusNode> nodes;
    std::vector<BusConn> masterIn;
    std::vector<int> topo;                   // nodes in an order where every input is ready

    int find(const std::string& id) const { for (size_t i = 0; i < nodes.size(); i++) if (nodes[i].id == id) return (int)i; return -1; }

    bool prepare(std::string& err) {
        ctx.sampleRate = sr; ctx.quantum = quantum; ctx.currentFrame = 0;
        // depth-first from the master: a node after everything that feeds it
        std::vector<int> state(nodes.size(), 0);
        topo.clear();
        std::function<bool(int)> visit = [&](int i) -> bool {
            if (state[i] == 2) return true;
            if (state[i] == 1) { err = "the routing has a loop at " + nodes[i].id; return false; }
            state[i] = 1;
            for (auto& c : nodes[i].in) if (!visit(c.from)) return false;
            state[i] = 2; topo.push_back(i); return true;
        };
        for (auto& c : masterIn) if (!visit(c.from)) return false;
        for (size_t i = 0; i < nodes.size(); i++) if (!visit((int)i)) return false;   // nodes that reach nothing still run (their devices keep time)
        for (auto& n : nodes) { n.oL.assign(quantum, 0); n.oR.assign(quantum, 0); if (n.delay > 0) { n.dlL.assign(n.delay, 0); n.dlR.assign(n.delay, 0); n.dlPos = 0; } }
        return true;
    }

    // sums the connections into L/R; returns whether the result is mono (one mono connection, or none)
    bool sumInputs(const std::vector<BusConn>& in, float* L, float* R, float* tmpL, float* tmpR, int Q, bool& silentNone) {
        silentNone = in.empty();
        if (in.empty()) { for (int i = 0; i < Q; i++) L[i] = R[i] = 0.f; return true; }
        auto connOut = [&](const BusConn& c, const float*& cl, const float*& cr) {
            const BusNode& f = nodes[c.from];
            if (!c.send) { cl = f.oL.data(); cr = f.oR.data(); return; }
            gainFixed(c.level, f.oL.data(), tmpL, Q); gainFixed(c.level, f.oR.data(), tmpR, Q);
            cl = tmpL; cr = tmpR;
        };
        if (in.size() == 1) { const float *cl, *cr; connOut(in[0], cl, cr); for (int i = 0; i < Q; i++) { L[i] = cl[i]; R[i] = cr[i]; } return false; }
        for (int i = 0; i < Q; i++) L[i] = R[i] = 0.f;
        for (auto& c : in) { const float *cl, *cr; connOut(c, cl, cr); addInto(cl, L, Q); addInto(cr, R, Q); }
        return false;   // every node's output (a pan) is stereo
    }

    void render(size_t n, float* outL, float* outR) {
        const int Q = quantum;
        std::vector<float> L(Q), R(Q), tL(Q), tR(Q), vL(Q), vR(Q), sL(Q), sR(Q);
        for (size_t pos = 0; pos < n; pos += Q) {
            const size_t keep = std::min<size_t>(Q, n - pos);
            ctx.currentFrame = (double)pos;
            for (int ni : topo) {
                BusNode& nd = nodes[ni];
                bool mono;
                if (nd.hasSrc) {                 // a buffer straight into the track's input: one connection, passed on as it is
                    for (int i = 0; i < Q; i++) { size_t k = pos + i; L[i] = k < nd.srcL.size() ? nd.srcL[k] : 0.f; R[i] = nd.srcMono ? L[i] : (k < nd.srcR.size() ? nd.srcR[k] : 0.f); }
                    mono = nd.srcMono;
                } else { bool none; mono = sumInputs(nd.in, L.data(), R.data(), sL.data(), sR.data(), Q, none); }
                if (nd.chain && nd.chain->size()) {
                    bool anyOn = false; for (size_t k = 0; k < nd.chain->size(); k++) anyOn |= nd.chain->slot(k).on;
                    if (anyOn) { nd.chain->process(L.data(), R.data(), Q); mono = false; }   // a worklet device gives two channels
                }
                if (nd.delay > 0) {              // an exact whole-sample delay (DelayNode at d/sr, measured)
                    const size_t D = (size_t)nd.delay;
                    for (int i = 0; i < Q; i++) {
                        float xl = L[i], xr = R[i];
                        L[i] = nd.dlL[nd.dlPos]; R[i] = nd.dlR[nd.dlPos];
                        nd.dlL[nd.dlPos] = xl; nd.dlR[nd.dlPos] = xr;
                        if (++nd.dlPos == D) nd.dlPos = 0;
                    }
                }
                gainFixed(nd.vol, L.data(), vL.data(), Q);
                if (!mono) gainFixed(nd.vol, R.data(), vR.data(), Q);
                panFixed(nd.pan, vL.data(), vR.data(), mono, nd.oL.data(), nd.oR.data(), Q, pos == 0);   // pan.value set at the start: the first quantum is sample-accurate
            }
            bool none; sumInputs(masterIn, L.data(), R.data(), sL.data(), sR.data(), Q, none);
            gainFixed(master, L.data(), L.data(), Q);
            gainFixed(master, R.data(), R.data(), Q);
            if (masterChain && masterChain->size()) masterChain->process(L.data(), R.data(), Q);
            for (size_t i = 0; i < keep; i++) { outL[pos + i] = L[i]; outR[pos + i] = R[i]; }
        }
    }
};

}  // namespace al
