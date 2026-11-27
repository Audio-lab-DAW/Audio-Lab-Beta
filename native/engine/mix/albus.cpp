// albus: renders a mixer scene with groups, sends, returns, delay compensation and the master's devices
// (task NB-N3d). Offline, no sound card; macOS and Linux. The scene is one JSON file, as make_bus_ref.py writes it:
//   {"sr":48000,"frames":24000,"quantum":512,"master":0.8,
//    "masterFx":[{"type":"limit","p":{...}}],
//    "nodes":[{"id":"a","kind":"audio","in":"in_st_a.wav","vol":0.7,"pan":-0.4,"fx":[{"type":"chorus","p":{...}}],"delay":0}, ...],
//    "inputs":{"g":[{"from":"a"},{"from":"b"}], "r":[{"from":"a","send":0.5}], "@master":[{"from":"g"},{"from":"r"}]},
//    "order":{"@master":[2,0,1]}}                       (order: optional, the summing order of a bus's inputs)
// Device settings ("p") are the ones the page posts to the worklet. Paths are relative to the scene's folder.
//   albus scene.json out.wav [--reps N] [--order bus=2,0,1]
#include "../../common/json.h"
#include "../../common/wav.h"
#include "../core/json_value.h"
#include "bus_graph.h"
#include <chrono>
#include <cstdio>
#include <fstream>
#include <sstream>

using namespace al;

static bool load(const std::string& path, BusGraph& g, size_t& frames, std::vector<std::pair<std::string, std::vector<int>>> extraOrder, std::string& err) {
    std::ifstream f(path); if (!f) { err = "cannot read " + path; return false; }
    std::stringstream ss; ss << f.rdbuf();
    JValue s; if (!parseJson(ss.str(), s, err)) return false;
    std::string dir = path.find('/') == std::string::npos ? "." : path.substr(0, path.rfind('/'));
    g.sr = s["sr"].num(48000); g.quantum = (int)s["quantum"].num(512); g.master = (float)s["master"].num(1); frames = (size_t)s["frames"].num(0);
    g.ctx.sampleRate = g.sr; g.ctx.quantum = g.quantum;
    g.ctx.bpm = s["bpm"].num(120); g.ctx.beat0 = s["beat0"].num(0);   // the song's tempo (task NB-N3g)
    auto chainOf = [&](const JValue& fx, std::unique_ptr<Chain>& ch) -> bool {
        ch.reset(new Chain(g.ctx));
        if (fx.t != JValue::Array) return true;
        for (auto& d : fx.a) if (!ch->add(d["type"].str(), d["p"], err)) return false;
        return true;
    };
    if (!chainOf(s["masterFx"], g.masterChain)) return false;
    for (auto& n : s["nodes"].a) {
        BusNode b; b.id = n["id"].str(); b.kind = n["kind"].str("audio");
        b.vol = (float)n["vol"].num(1); b.pan = (float)n["pan"].num(0); b.delay = (int)n["delay"].num(0);
        if (n["in"].t == JValue::String) {
            Wav w; if (!wavRead(dir + "/" + n["in"].s, w, err)) return false;
            size_t m = w.frames(); b.srcL.resize(m); b.srcR.resize(m);
            for (size_t i = 0; i < m; i++) { b.srcL[i] = w.data[i * w.ch]; b.srcR[i] = w.ch > 1 ? w.data[i * w.ch + 1] : b.srcL[i]; }
            b.hasSrc = true; b.srcMono = w.ch == 1;
        }
        if (!chainOf(n["fx"], b.chain)) return false;
        g.nodes.push_back(std::move(b));
    }
    const JValue& ins = s["inputs"];
    for (auto& kv : ins.o) {
        std::vector<BusConn> v;
        for (auto& c : kv.second.a) {
            BusConn bc; bc.from = g.find(c["from"].str());
            if (bc.from < 0) { err = "input from an unknown node " + c["from"].str(); return false; }
            if (c["send"].t == JValue::Number) { bc.send = true; bc.level = (float)c["send"].n; }
            v.push_back(bc);
        }
        auto reorder = [&](const std::vector<int>& ord) -> bool {
            if (ord.size() != v.size()) { err = "order for " + kv.first + " names " + std::to_string(ord.size()) + " inputs, it has " + std::to_string(v.size()); return false; }
            std::vector<BusConn> r; for (int k : ord) { if (k < 0 || k >= (int)v.size()) { err = "bad order"; return false; } r.push_back(v[k]); }
            v = r; return true;
        };
        const JValue& o = s["order"][kv.first];
        if (o.t == JValue::Array) { std::vector<int> ord; for (auto& x : o.a) ord.push_back((int)x.n); if (!reorder(ord)) return false; }
        for (auto& eo : extraOrder) if (eo.first == kv.first && !reorder(eo.second)) return false;
        if (kv.first == "@master") g.masterIn = v;
        else { int t = g.find(kv.first); if (t < 0) { err = "inputs for an unknown node " + kv.first; return false; } g.nodes[t].in = v; }
    }
    return g.prepare(err);
}

int main(int argc, char** argv) {
    if (argc < 3) { fprintf(stderr, "usage: albus scene.json out.wav [--reps N] [--order bus=2,0,1]...\n"); return 2; }
    int reps = 1;
    std::vector<std::pair<std::string, std::vector<int>>> orders;
    for (int i = 3; i + 1 < argc; i++) {
        std::string a = argv[i];
        if (a == "--reps") reps = atoi(argv[++i]);
        else if (a == "--order") {
            std::string o = argv[++i]; size_t eq = o.find('='); if (eq == std::string::npos) continue;
            std::vector<int> v; std::string l = o.substr(eq + 1); size_t p = 0;
            while (p <= l.size() && !l.empty()) { size_t k = l.find(',', p); if (k == std::string::npos) k = l.size(); v.push_back(atoi(l.substr(p, k - p).c_str())); p = k + 1; }
            orders.push_back({o.substr(0, eq), v});
        }
    }
    std::vector<float> L, R; double best = 1e9; size_t frames = 0; std::string err;
    BusGraph* last = nullptr; std::unique_ptr<BusGraph> keep;
    for (int r = 0; r < reps; r++) {
        keep.reset(new BusGraph());
        if (!load(argv[1], *keep, frames, orders, err)) { fprintf(stderr, "%s\n", err.c_str()); return 2; }
        L.assign(frames, 0); R.assign(frames, 0);
        auto t0 = std::chrono::steady_clock::now();
        keep->render(frames, L.data(), R.data());
        double s = std::chrono::duration<double>(std::chrono::steady_clock::now() - t0).count(); if (s < best) best = s;
        last = keep.get();
    }
    Wav out; out.sr = (int)last->sr; out.ch = 2; out.data.resize(frames * 2);
    for (size_t i = 0; i < frames; i++) { out.data[2 * i] = L[i]; out.data[2 * i + 1] = R[i]; }
    if (!wavWrite(argv[2], out)) { fprintf(stderr, "cannot write %s\n", argv[2]); return 2; }
    size_t devs = last->masterChain ? last->masterChain->size() : 0; for (auto& n : last->nodes) devs += n.chain ? n.chain->size() : 0;
    printf("{\"frames\":%zu,\"nodes\":%zu,\"devices\":%zu,\"quantum\":%d,\"renderSeconds\":%s,\"timesRealTime\":%s}\n", frames, last->nodes.size(), devs, last->quantum,
           jnum(best).c_str(), jnum(best > 0 ? frames / last->sr / best : 0).c_str());
    return 0;
}
