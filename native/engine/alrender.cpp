// alrender: offline renders through the native engine core (task NB-N3a).
//   alrender list                                   the device types the core has
//   alrender cases <cases.json> <in.wav> <outdir> [block]   one output WAV per case, timing as JSON lines;
//                                                    block: frames per call (default 128, the web engine's)
// cases.json: {"cases":[{"name":"limit-trans","chain":[{"type":"limit","p":{...}}]}, ...]}
// The settings "p" are those the page posts to the worklet (see tools/native-lab/make_ref_core.py).
#include <chrono>
#include <cstdio>
#include <fstream>
#include <sstream>
#include "../common/json.h"
#include "../common/wav.h"
#include "core/graph.h"

using namespace al;

static bool readFile(const std::string& p, std::string& s) {
    std::ifstream f(p, std::ios::binary); if (!f) return false;
    std::stringstream b; b << f.rdbuf(); s = b.str(); return true;
}
static bool wavWrite(const std::string& path, int sr, const std::vector<float>& L, const std::vector<float>& R) {
    FILE* f = fopen(path.c_str(), "wb"); if (!f) return false;
    const uint32_t n = (uint32_t)L.size(), bytes = n * 8;
    auto u32 = [&](uint32_t v) { fwrite(&v, 4, 1, f); };
    auto u16 = [&](uint16_t v) { fwrite(&v, 2, 1, f); };
    fwrite("RIFF", 1, 4, f); u32(36 + bytes); fwrite("WAVEfmt ", 1, 8, f); u32(16); u16(3); u16(2); u32((uint32_t)sr); u32((uint32_t)sr * 8); u16(8); u16(32);
    fwrite("data", 1, 4, f); u32(bytes);
    std::vector<float> il(2 * (size_t)n); for (uint32_t i = 0; i < n; i++) { il[2 * i] = L[i]; il[2 * i + 1] = R[i]; }
    fwrite(il.data(), 4, il.size(), f); fclose(f); return true;
}

int main(int argc, char** argv) {
    registerCoreDevices();
    std::string cmd = argc > 1 ? argv[1] : "";
    if (cmd == "list") {
        printf("[");
        bool first = true;
        for (auto& kv : deviceRegistry()) { printf("%s%s", first ? "" : ",", jstr(kv.first).c_str()); first = false; }
        printf("]\n");
        return 0;
    }
    if (cmd == "cases" && argc >= 5) {
        std::string src, err;
        if (!readFile(argv[2], src)) { fprintf(stderr, "cannot read %s\n", argv[2]); return 2; }
        JValue cj; if (!parseJson(src, cj, err)) { fprintf(stderr, "cases: %s\n", err.c_str()); return 2; }
        Wav in; if (!wavRead(argv[3], in, err)) { fprintf(stderr, "%s\n", err.c_str()); return 2; }
        const size_t N = in.frames();
        std::vector<float> iL(N), iR(N);
        for (size_t i = 0; i < N; i++) { iL[i] = in.data[i * in.ch]; iR[i] = in.data[i * in.ch + (in.ch > 1 ? 1 : 0)]; }
        const int block = argc >= 6 ? atoi(argv[5]) : kQuantum;
        int bad = 0;
        for (auto& c : cj["cases"].a) {
            RenderContext ctx; ctx.sampleRate = in.sr;
            Chain ch(ctx);
            bool ok = true;
            for (auto& d : c["chain"].a) if (!ch.add(d["type"].str(), d["p"], err)) { ok = false; break; }
            const std::string name = c["name"].str();
            if (!ok) { printf("{\"name\":%s,\"ok\":false,\"error\":%s}\n", jstr(name).c_str(), jstr(err).c_str()); bad++; continue; }
            std::vector<float> oL, oR;
            auto t0 = std::chrono::steady_clock::now();
            renderChain(ch, iL, iR, oL, oR, block);
            double us = std::chrono::duration<double, std::micro>(std::chrono::steady_clock::now() - t0).count();
            const double blocks = (double)(N + kQuantum - 1) / kQuantum;  // time per 128 frames
            wavWrite(std::string(argv[4]) + "/" + name + ".wav", in.sr, oL, oR);
            printf("{\"name\":%s,\"ok\":true,\"usPerBlock\":%.4f,\"realtimeX\":%.1f}\n", jstr(name).c_str(), us / blocks,
                   (N / (double)in.sr) / (us / 1e6));
        }
        return bad ? 1 : 0;
    }
    fprintf(stderr, "usage: alrender list | alrender cases <cases.json> <in.wav> <outdir>\n");
    return 2;
}
