// alnative: test A of task NM1. A small native program that
//   devices            lists the audio devices through Core Audio (rates, buffer sizes, volume the computer can set)
//   play               opens the default output through Core Audio and plays a file for a moment
//   crush              renders AudioLab's Bitcrusher (a port of the worklet 'al-crush') to a file
//   compare            compares two 32-bit float WAV files bit for bit
// Everything prints JSON, so the workflow can collect it.
#include "../common/json.h"
#include "../common/wav.h"
#include "../dsp/al_crush.h"
#include <chrono>
#include <cinttypes>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <map>
#include <string>
#include <thread>
#ifdef __APPLE__
#include "../common/coreaudio.h"
#endif

using namespace al;

static std::string hexd(double v) { uint64_t u; memcpy(&u, &v, 8); char b[20]; snprintf(b, sizeof b, "%016" PRIx64, u); return b; }
static double unhex(const std::string& s) { uint64_t u = strtoull(s.c_str(), nullptr, 16); double v; memcpy(&v, &u, 8); return v; }

static std::map<std::string, std::string> opts(int argc, char** argv, int from) {
    std::map<std::string, std::string> m;
    for (int i = from; i < argc; i++) {
        std::string a = argv[i];
        if (a.rfind("--", 0) == 0) { std::string k = a.substr(2); if (i + 1 < argc && std::string(argv[i + 1]).rfind("--", 0) != 0) m[k] = argv[++i]; else m[k] = "1"; }
    }
    return m;
}

static int cmdCrush(int argc, char** argv) {
    auto o = opts(argc, argv, 2);
    Wav in; std::string err;
    if (!wavRead(o["in"], in, err) || in.ch != 2) { fprintf(stderr, "crush: %s\n", err.empty() ? "needs a stereo file" : err.c_str()); return 2; }
    CrushParams p;
    auto num = [&](const char* k, double& v) { if (o.count(k)) v = atof(o[k].c_str()); };
    num("bits", p.bits); num("rate", p.rate); num("jit", p.jit); num("dith", p.dith); num("drive", p.drive); num("mix", p.mix); num("out", p.out); num("pre", p.pre); num("post", p.post);
    if (o.count("shape")) p.shape = o["shape"];
    CrushCoef own = crushCoef(p, in.sr), k = own;
    // --coef q,dr,go,pc,oc as hex doubles: use the web engine's own numbers instead of this machine's pow() and exp()
    bool given = false;
    if (o.count("coef")) {
        std::string s = o["coef"]; double* f[5] = {&k.q, &k.dr, &k.go, &k.pc, &k.oc}; size_t pos = 0; int i = 0;
        while (i < 5 && pos <= s.size()) { size_t c = s.find(',', pos); if (c == std::string::npos) c = s.size(); *f[i++] = unhex(s.substr(pos, c - pos)); pos = c + 1; }
        given = i == 5;
    }
    size_t n = in.frames();
    std::vector<float> L(n), R(n), oL(n), oR(n);
    for (size_t i = 0; i < n; i++) { L[i] = in.data[2 * i]; R[i] = in.data[2 * i + 1]; }
    WorkletRandom rnd; Crush fx; fx.rnd = &rnd;
    int block = o.count("block") ? atoi(o["block"].c_str()) : 128;
    int reps = o.count("reps") ? atoi(o["reps"].c_str()) : 1;
    auto t0 = std::chrono::steady_clock::now();
    for (int r = 0; r < reps; r++) {
        if (r) { fx = Crush(); rnd = WorkletRandom(); fx.rnd = &rnd; }
        for (size_t i = 0; i < n; i += block) { int m = (int)std::min<size_t>(block, n - i); fx.process(p, k, &L[i], &R[i], &oL[i], &oR[i], m); }
    }
    double sec = std::chrono::duration<double>(std::chrono::steady_clock::now() - t0).count() / reps;
    Wav out; out.sr = in.sr; out.ch = 2; out.data.resize(n * 2);
    for (size_t i = 0; i < n; i++) { out.data[2 * i] = oL[i]; out.data[2 * i + 1] = oR[i]; }
    if (!wavWrite(o["to"], out)) { fprintf(stderr, "crush: cannot write %s\n", o["to"].c_str()); return 2; }
    printf("{\"frames\":%zu,\"sr\":%d,\"block\":%d,\"coefFrom\":%s,\"ownCoef\":{\"q\":\"%s\",\"dr\":\"%s\",\"go\":\"%s\",\"pc\":\"%s\",\"oc\":\"%s\"},\"renderSeconds\":%s,\"timesRealTime\":%s}\n",
           n, in.sr, block, given ? "\"web\"" : "\"own\"", hexd(own.q).c_str(), hexd(own.dr).c_str(), hexd(own.go).c_str(), hexd(own.pc).c_str(), hexd(own.oc).c_str(),
           jnum(sec).c_str(), jnum(sec > 0 ? (double)n / in.sr / sec : 0).c_str());
    return 0;
}

static int cmdCompare(int argc, char** argv) {
    if (argc < 4) return 2;
    Wav a, b; std::string err;
    if (!wavRead(argv[2], a, err) || !wavRead(argv[3], b, err)) { fprintf(stderr, "compare: %s\n", err.c_str()); return 2; }
    size_t n = std::min(a.data.size(), b.data.size()), diff = 0, first = (size_t)-1;
    double maxd = 0, peak = 0, se = 0;
    for (size_t i = 0; i < n; i++) {
        uint32_t x, y; memcpy(&x, &a.data[i], 4); memcpy(&y, &b.data[i], 4);
        if (x != y) { diff++; if (first == (size_t)-1) first = i; }
        double d = std::fabs((double)a.data[i] - (double)b.data[i]); if (d > maxd) maxd = d; se += d * d;
        if (std::fabs(a.data[i]) > peak) peak = std::fabs(a.data[i]);
    }
    bool same = diff == 0 && a.data.size() == b.data.size();
    printf("{\"identical\":%s,\"samples\":%zu,\"sameLength\":%s,\"differing\":%zu,\"firstDifference\":%ld,\"maxDifference\":%s,\"maxDifferenceDb\":%s,\"rmsDifferenceDb\":%s,\"peak\":%s}\n",
           same ? "true" : "false", n, a.data.size() == b.data.size() ? "true" : "false", diff, first == (size_t)-1 ? -1L : (long)first, jnum(maxd).c_str(),
           maxd > 0 ? jnum(20 * std::log10(maxd)).c_str() : "null", se > 0 ? jnum(10 * std::log10(se / n)).c_str() : "null", jnum(peak).c_str());
    return same ? 0 : 1;
}

#ifdef __APPLE__
struct PlayCtx { const Wav* w; size_t pos = 0; float gain = 0.1f; };
static void playRender(void* u, float** out, int, int frames) {
    PlayCtx* c = (PlayCtx*)u; size_t n = c->w->frames();
    for (int i = 0; i < frames; i++) {
        if (c->pos < n) { out[0][i] = c->w->data[2 * c->pos] * c->gain; out[1][i] = c->w->data[2 * c->pos + 1] * c->gain; c->pos++; }
        else { out[0][i] = 0; out[1][i] = 0; }
    }
}
static int cmdDevices() {
    auto v = listDevices();
    printf("{\"devices\":%s,\"defaultOutput\":%u}\n", devicesJson(v).c_str(), defaultOutputDevice());
    return 0;
}
static int cmdPlay(int argc, char** argv) {
    auto o = opts(argc, argv, 2);
    Wav w; std::string err;
    if (!wavRead(o["in"], w, err) || w.ch != 2) { printf("{\"opened\":false,\"why\":%s}\n", jstr("cannot read the file to play: " + err).c_str()); return 0; }
    uint32_t dev = o.count("device") ? (uint32_t)atoi(o["device"].c_str()) : defaultOutputDevice();
    if (!dev) { printf("{\"opened\":false,\"why\":\"this machine has no default output device\"}\n"); return 0; }
    DeviceInfo me; for (auto& d : listDevices()) if (d.id == dev) me = d;
    std::string s = "{\"device\":" + deviceJson(me);
    // 1. the device's own buffer size: ask for 64 frames (the web engine cannot ask at all)
    if (o.count("buffer")) {
        uint32_t now = 0; std::string e; bool ok = setDeviceBuffer(dev, (uint32_t)atoi(o["buffer"].c_str()), now, e);
        s += ",\"bufferAsked\":" + o["buffer"] + ",\"bufferSet\":" + (ok ? "true" : "false") + ",\"bufferNow\":" + std::to_string(now) + ",\"bufferError\":" + jstr(e);
    }
    // 2. the device's sample rate: switch it, then back
    if (o.count("try-rate")) {
        double want = atof(o["try-rate"].c_str()), now = 0, back = 0; std::string e, e2;
        bool ok = setDeviceRate(dev, want, now, e);
        s += ",\"rateAsked\":" + jnum(want) + ",\"rateSet\":" + (ok ? "true" : "false") + ",\"rateNow\":" + jnum(now) + ",\"rateError\":" + jstr(e);
        bool okb = setDeviceRate(dev, me.rate, back, e2);
        s += ",\"rateRestored\":" + std::string(okb ? "true" : "false") + ",\"rateAfter\":" + jnum(back);
    }
    // 3. exclusive use ("hog mode"): take it, then give it back
    if (o.count("try-hog")) {
        int owner = -1; std::string e, e2; bool ok = setHog(dev, true, owner, e);
        s += ",\"hogTaken\":" + std::string(ok ? "true" : "false") + ",\"hogOwner\":" + std::to_string(owner) + ",\"hogError\":" + jstr(e);
        bool okb = setHog(dev, false, owner, e2);
        s += ",\"hogReleased\":" + std::string(okb ? "true" : "false");
    }
    PlayCtx ctx; ctx.w = &w;
    OutputStream st;
    bool ok = st.start(dev, playRender, &ctx, err);
    s += ",\"opened\":" + std::string(ok ? "true" : "false");
    if (!ok) s += ",\"why\":" + jstr(err);
    else {
        double secs = o.count("seconds") ? atof(o["seconds"].c_str()) : 1.0;
        std::this_thread::sleep_for(std::chrono::milliseconds((int)(secs * 1000)));
        st.stop();
        uint64_t cb = st.callbacks.load();
        s += ",\"seconds\":" + jnum(secs) + ",\"callbacks\":" + std::to_string(cb) + ",\"framesPlayed\":" + std::to_string(st.framesTotal.load()) +
             ",\"framesPerCallbackMin\":" + std::to_string(cb ? st.minFrames.load() : 0) + ",\"framesPerCallbackMax\":" + std::to_string(st.maxFrames.load()) +
             ",\"overloads\":" + std::to_string(st.overloads.load()) + ",\"renderAvgMicroseconds\":" + jnum(cb ? st.sumNs.load() / 1000.0 / cb : 0) +
             ",\"renderWorstMicroseconds\":" + jnum(st.worstNs.load() / 1000.0);
    }
    printf("%s}\n", s.c_str());
    return 0;
}
#endif

int main(int argc, char** argv) {
    std::string c = argc > 1 ? argv[1] : "";
    if (c == "crush") return cmdCrush(argc, argv);
    if (c == "compare") return cmdCompare(argc, argv);
#ifdef __APPLE__
    if (c == "devices") return cmdDevices();
    if (c == "play") return cmdPlay(argc, argv);
#else
    if (c == "devices" || c == "play") { printf("{\"opened\":false,\"why\":\"Core Audio exists only on macOS\"}\n"); return 0; }
#endif
    fprintf(stderr, "usage: alnative devices | play --in f.wav [--buffer 64] [--try-rate 96000] [--try-hog] | crush --in a.wav --to b.wav [settings] [--coef hex,hex,hex,hex,hex] | compare a.wav b.wav\n");
    return 2;
}
