// alnodes (task NB-N3g): Chromium's source nodes and wave shaper on their own, for comparison with the browser.
//   alnodes cases.json outdir      cases: [{name, sr, quantum, frames, osc:{type, freq, detune, start, stop},
//                                           const:{offset, start, stop}, shape:{curve:[...]}}]
// One case renders an oscillator (or a constant source), optionally through a wave shaper, mono, 32-bit float.
#include <chrono>
#include <cstdio>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>
#include "core/json_value.h"
#include "core/device.h"
#include "core/webnodes.h"

using namespace al;

static bool readFile(const std::string& p, std::string& out) { std::ifstream f(p, std::ios::binary); if (!f) return false; std::stringstream s; s << f.rdbuf(); out = s.str(); return true; }
static void wavWrite(const std::string& path, int sr, const std::vector<float>& x) {
    FILE* f = fopen(path.c_str(), "wb"); if (!f) return;
    const uint32_t n = (uint32_t)x.size() * 4; uint32_t u; uint16_t h;
    fwrite("RIFF", 1, 4, f); u = 36 + n; fwrite(&u, 4, 1, f); fwrite("WAVEfmt ", 1, 8, f);
    u = 16; fwrite(&u, 4, 1, f); h = 3; fwrite(&h, 2, 1, f); h = 1; fwrite(&h, 2, 1, f); u = sr; fwrite(&u, 4, 1, f);
    u = sr * 4; fwrite(&u, 4, 1, f); h = 4; fwrite(&h, 2, 1, f); h = 32; fwrite(&h, 2, 1, f);
    fwrite("data", 1, 4, f); fwrite(&n, 4, 1, f); fwrite(x.data(), 4, x.size(), f); fclose(f);
}

int main(int argc, char** argv) {
    if (argc < 3) { fprintf(stderr, "usage: alnodes cases.json outdir\n"); return 2; }
    std::string src, err; if (!readFile(argv[1], src)) return 2;
    JValue cj; if (!parseJson(src, cj, err)) { fprintf(stderr, "%s\n", err.c_str()); return 2; }
    for (auto& c : cj["cases"].a) {
        const double sr = c["sr"].num(48000); const size_t Q = (size_t)c["quantum"].num(128), N = (size_t)c["frames"].num(48000);
        NodeFloatState fz;
        std::unique_ptr<cr::Oscillator> osc; std::unique_ptr<cr::ConstantSource> cs;
        if (c["osc"].t == JValue::Object) {
            const JValue& o = c["osc"]; cr::OscType t; if (!cr::oscTypeOf(o["type"].str(), t)) t = cr::OscType::Sine;
            osc.reset(new cr::Oscillator((float)sr, t)); osc->setFrequency(o["freq"].num(440)); osc->setDetune(o["detune"].num(0));
            osc->sched.startAt(o["start"].num(0), 0); if (o["stop"].t == JValue::Number) osc->sched.stopAt(o["stop"].num(0));
        } else {
            const JValue& o = c["const"]; cs.reset(new cr::ConstantSource((float)sr)); cs->setOffset(o["offset"].num(1));
            cs->sched.startAt(o["start"].num(0), 0); if (o["stop"].t == JValue::Number) cs->sched.stopAt(o["stop"].num(0));
        }
        std::vector<float> curve; bool shape = c["shape"].t == JValue::Object;
        if (shape) for (auto& v : c["shape"]["curve"].a) curve.push_back((float)v.num(0));
        std::vector<float> out(((N + Q - 1) / Q) * Q), q(Q);
        auto t0 = std::chrono::steady_clock::now();
        for (size_t p = 0; p < out.size(); p += Q) {
            if (osc) osc->process(p, Q, q.data()); else cs->process(p, Q, q.data());
            if (shape) cr::waveShape(q.data(), q.data(), Q, curve);
            std::copy(q.begin(), q.end(), out.begin() + p);
        }
        double us = std::chrono::duration<double, std::micro>(std::chrono::steady_clock::now() - t0).count();
        out.resize(N);
        wavWrite(std::string(argv[2]) + "/" + c["name"].str() + ".wav", (int)sr, out);
        printf("{\"name\":\"%s\",\"us\":%.1f}\n", c["name"].str().c_str(), us);
    }
    return 0;
}
