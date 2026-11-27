// The mixer (task NB-N3b): tracks, their device chains, the master, rendered in fixed quanta. Next: the chains here
// become the core's Chain (native/engine/core/graph.h, task NB-N3a) with the quantum as a parameter.
// Portable C++ (no Core Audio here), so every check runs on Linux too.
//
// The shape follows the web engine's export (renderMix in index.html): for each track in project order
//   input -> devices in order -> volume (GainNode) -> pan (StereoPannerNode) -> into the master,
// the master gain, then the output. The master sums the tracks in project order, as the export connects them.
//
// The block rule (research RN1, point 5): the core always runs in quanta of the size the web engine used for the
// same job, 128 frames while playing and 512 in an export (renderSizeHint), so that devices whose state changes
// per block (the worklets' denormal flush every 16 blocks) do the same thing. A device buffer of 32 or 64
// frames is served from a ring in front of the core (N3b), not by running the core in smaller pieces.
#pragma once
#include "../../dsp/al_crush.h"
#include "../../dsp/al_mix.h"
#include <memory>
#include <string>
#include <vector>

namespace al {

// One device in a chain. Only the Bitcrusher is ported so far; every port adds a kind here.
struct Device {
    std::string kind;                 // "crush"
    CrushParams cp; CrushCoef ck; Crush crush;
    bool on = true;
    void prepare(double sr, WorkletRandom* rnd) { if (kind == "crush") { ck = crushCoef(cp, sr); crush = Crush(); crush.rnd = rnd; } }
    // stereo in place
    void process(float* L, float* R, float* tL, float* tR, int n) {
        if (kind == "crush") { crush.process(cp, ck, L, R, tL, tR, n); for (int i = 0; i < n; i++) { L[i] = tL[i]; R[i] = tR[i]; } }
    }
};

struct Track {
    std::string name;
    std::vector<float> srcL, srcR;    // the input (until clips and instruments move: N3c and later)
    bool mono = false;                // a one-channel input stays one channel until something makes it stereo
    float vol = 1, pan = 0;
    std::vector<Device> chain;
};

struct MixGraph {
    double sr = 48000;
    int quantum = 128;
    float master = 1;
    std::vector<Track> tracks;
    // The order the master pulls its tracks: it is both the order they are processed (which decides how devices
    // share the engine's random numbers) and the order they are added. The export connects them in project order,
    // but Chromium keeps a node's connections in a hash set, so the web engine's order changes from one render
    // to the next (two renders of the same 5-track scene differed; tools/native-lab/run_mix.py). Empty: project order.
    std::vector<int> order;
    WorkletRandom rnd;                // one generator per engine, shared by the devices in creation order, as in the page

    void prepare() { rnd = WorkletRandom(); for (auto& t : tracks) for (auto& d : t.chain) d.prepare(sr, &rnd); }

    // Renders frames [0, n) into outL/outR.
    void render(size_t n, float* outL, float* outR) {
        const int Q = quantum;
        std::vector<float> L(Q), R(Q), tL(Q), tR(Q), vL(Q), vR(Q), pL(Q), pR(Q), mL(Q), mR(Q);
        for (size_t pos = 0; pos < n; pos += Q) {
            // always a whole quantum, as Chromium renders: devices that draw random numbers draw them for the frames
            // past the end too, which changes what the next device gets (found in run_mix.py, scene crush128)
            const int m = Q; const size_t keep = std::min<size_t>(Q, n - pos);
            bool any = false;
            for (size_t ti = 0; ti < tracks.size(); ti++) {
                Track& t = tracks[order.size() == tracks.size() ? (size_t)order[ti] : ti];
                for (int i = 0; i < m; i++) {
                    size_t k = pos + i;
                    L[i] = k < t.srcL.size() ? t.srcL[k] : 0.f;
                    R[i] = t.mono ? L[i] : (k < t.srcR.size() ? t.srcR[k] : 0.f);
                }
                bool mono = t.mono;
                for (auto& d : t.chain) if (d.on) { d.process(L.data(), R.data(), tL.data(), tR.data(), m); mono = false; }   // a worklet device gives two channels
                gainFixed(t.vol, L.data(), vL.data(), m);
                if (!mono) gainFixed(t.vol, R.data(), vR.data(), m);
                panFixed(t.pan, vL.data(), vR.data(), mono, pL.data(), pR.data(), m, pos == 0);   // the quantum where pan.value was set: sample-accurate
                if (!any) { for (int i = 0; i < m; i++) { mL[i] = pL[i]; mR[i] = pR[i]; } any = true; }
                else { addInto(pL.data(), mL.data(), m); addInto(pR.data(), mR.data(), m); }
            }
            if (!any) for (int i = 0; i < m; i++) mL[i] = mR[i] = 0.f;
            gainFixed(master, mL.data(), mL.data(), m);
            gainFixed(master, mR.data(), mR.data(), m);
            for (size_t i = 0; i < keep; i++) { outL[pos + i] = mL[i]; outR[pos + i] = mR[i]; }
        }
    }
};

}  // namespace al
