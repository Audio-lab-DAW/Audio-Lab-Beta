// almix: renders a scene through the native mixer to a file (task NB-N3b; written as N3a in a parallel run, see the backlog log). Offline, no sound card,
// runs on macOS and Linux. The scene is one flat JSON object per line:
//   {"sr":48000,"frames":24000,"quantum":512,"master":0.7,"order":"2,0,1"}   (order: optional, see mix_graph.h)
//   {"track":"Lead","in":"lead.wav","vol":0.8,"pan":-0.3,"mono":false}
//   {"device":"crush","bits":6,"rate":3,"jit":0,"dith":0,"drive":0,"mix":100,"out":0,"pre":0,"post":0,"shape":"round"}   (goes on the last track)
//     a device line may carry "coef":"q,dr,go,pc,oc" (hex doubles) to use the web engine's own pow() and exp() results
//   almix scene.txt out.wav [--reps N]
#include "../../common/wav.h"
#include "../../common/json.h"
#include "../minijson.h"
#include "mix_graph.h"
#include <chrono>
#include <cstdio>
#include <fstream>
#include <iostream>

using namespace al;

static double unhexd(const std::string& h) { uint64_t u = strtoull(h.c_str(), nullptr, 16); double d; memcpy(&d, &u, 8); return d; }

int main(int argc, char** argv) {
    if (argc < 3) { fprintf(stderr, "usage: almix scene.txt out.wav [--reps N]\n"); return 2; }
    int reps = 1; for (int i = 3; i + 1 < argc; i++) if (std::string(argv[i]) == "--reps") reps = atoi(argv[i + 1]);
    std::ifstream f(argv[1]); if (!f) { fprintf(stderr, "cannot read %s\n", argv[1]); return 2; }
    MixGraph g; size_t frames = 0; std::string line, err; int lineNo = 0;
    std::vector<std::vector<std::string>> coefs;   // per device, in order
    while (std::getline(f, line)) {
        lineNo++; if (line.empty() || line[0] == '#') continue;
        Msg m; if (!parseMsg(line, m)) { fprintf(stderr, "line %d is not a flat JSON object\n", lineNo); return 2; }
        if (m.has("sr")) { g.sr = m.num("sr"); frames = (size_t)m.num("frames"); g.quantum = (int)m.num("quantum", 128); g.master = (float)m.num("master", 1);
            auto list = [](const std::string& o, std::vector<int>& v) { size_t pos = 0; while (!o.empty() && pos <= o.size()) { size_t k = o.find(',', pos); if (k == std::string::npos) k = o.size(); v.push_back(atoi(o.substr(pos, k - pos).c_str())); pos = k + 1; } };
            list(m.str("order"), g.order); }
        else if (m.has("track")) {
            Track t; t.name = m.str("track"); t.vol = (float)m.num("vol", 1); t.pan = (float)m.num("pan", 0);
            Wav w; if (!wavRead(m.str("in"), w, err)) { fprintf(stderr, "track %s: %s\n", t.name.c_str(), err.c_str()); return 2; }
            size_t n = w.frames(); t.srcL.resize(n); t.srcR.resize(n);
            for (size_t i = 0; i < n; i++) { t.srcL[i] = w.data[i * w.ch]; t.srcR[i] = w.ch > 1 ? w.data[i * w.ch + 1] : t.srcL[i]; }
            t.mono = w.ch == 1 || m.flag("mono");
            g.tracks.push_back(std::move(t));
        } else if (m.has("device")) {
            if (g.tracks.empty()) { fprintf(stderr, "line %d: a device before any track\n", lineNo); return 2; }
            Device d; d.kind = m.str("device");
            if (d.kind != "crush") { fprintf(stderr, "line %d: device '%s' is not ported yet\n", lineNo, d.kind.c_str()); return 2; }
            CrushParams& p = d.cp;
            p.bits = m.num("bits", 8); p.rate = m.num("rate", 1); p.jit = m.num("jit", 0); p.dith = m.num("dith", 0); p.drive = m.num("drive", 0);
            p.mix = m.num("mix", 100); p.out = m.num("out", 0); p.pre = m.num("pre", 0); p.post = m.num("post", 0); p.shape = m.str("shape", "round");
            g.tracks.back().chain.push_back(d);
            std::vector<std::string> c; std::string s = m.str("coef"); size_t pos = 0;
            while (!s.empty() && pos <= s.size()) { size_t k = s.find(',', pos); if (k == std::string::npos) k = s.size(); c.push_back(s.substr(pos, k - pos)); pos = k + 1; }
            coefs.push_back(c);
        }
    }
    std::vector<float> L(frames), R(frames);
    double best = 1e9;
    for (int r = 0; r < reps; r++) {
        g.prepare();
        size_t di = 0;
        for (auto& t : g.tracks) for (auto& d : t.chain) { auto& c = coefs[di++]; if (c.size() == 5) { d.ck.q = unhexd(c[0]); d.ck.dr = unhexd(c[1]); d.ck.go = unhexd(c[2]); d.ck.pc = unhexd(c[3]); d.ck.oc = unhexd(c[4]); } }
        auto t0 = std::chrono::steady_clock::now();
        g.render(frames, L.data(), R.data());
        double s = std::chrono::duration<double>(std::chrono::steady_clock::now() - t0).count(); if (s < best) best = s;
    }
    Wav out; out.sr = (int)g.sr; out.ch = 2; out.data.resize(frames * 2);
    for (size_t i = 0; i < frames; i++) { out.data[2 * i] = L[i]; out.data[2 * i + 1] = R[i]; }
    if (!wavWrite(argv[2], out)) { fprintf(stderr, "cannot write %s\n", argv[2]); return 2; }
    if (!g.order.empty() && g.order.size() != g.tracks.size()) { fprintf(stderr, "order names %zu tracks, the scene has %zu\n", g.order.size(), g.tracks.size()); return 2; }
    printf("{\"frames\":%zu,\"tracks\":%zu,\"quantum\":%d,\"renderSeconds\":%s,\"timesRealTime\":%s}\n", frames, g.tracks.size(), g.quantum, jnum(best).c_str(), jnum(best > 0 ? frames / g.sr / best : 0).c_str());
    return 0;
}
