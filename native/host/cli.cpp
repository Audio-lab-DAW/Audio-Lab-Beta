// alvst3: test B of task NM1. A minimal VST3 host for the command line, written against plugin_api.h only.
//   alvst3 scan [--folder DIR]... [--json FILE]        finds bundles and scans each one in a child process
//   alvst3 run --plugin BUNDLE [--name NAME] --outdir DIR --tag TAG [--in FILE.wav] [--sr 48000] [--block 128] [--seconds 4]
//          loads the plug-in, lists its parameters, plays notes (instrument) or runs audio through it (effect),
//          saves and restores its state, renders in real-time and export mode, and reports the time per block.
#include "plugin_api.h"
#include "live_tools.h"
#include "../common/json.h"
#include "../common/wav.h"
#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <map>
#include <thread>
#include <unistd.h>

using namespace al;

static std::multimap<std::string, std::string> opts(int argc, char** argv, int from) {
    std::multimap<std::string, std::string> m;
    for (int i = from; i < argc; i++) {
        std::string a = argv[i];
        if (a.rfind("--", 0) == 0) { std::string k = a.substr(2); if (i + 1 < argc && std::string(argv[i + 1]).rfind("--", 0) != 0) m.insert({k, argv[++i]}); else m.insert({k, "1"}); }
    }
    return m;
}
static std::string opt(const std::multimap<std::string, std::string>& m, const char* k, const char* d = "") { auto it = m.find(k); return it == m.end() ? d : it->second; }

static std::string selfPath(char** argv) {
    char buf[4096];
    if (realpath(argv[0], buf)) return buf;
    return argv[0];
}

static int cmdScan(int argc, char** argv) {
    auto o = opts(argc, argv, 2);
    PluginFormat* F = vst3Format();
    std::vector<std::string> folders;
    for (auto r = o.equal_range("folder"); r.first != r.second; ++r.first) folders.push_back(r.first->second);
    if (folders.empty()) folders = F->defaultFolders();
    auto bundles = F->findBundles(folders);
    std::string self = selfPath(argv);
    std::string js = "{\"hostArch\":" + jstr(hostArch()) + ",\"folders\":[";
    for (size_t i = 0; i < folders.size(); i++) js += (i ? "," : "") + jstr(folders[i]);
    js += "],\"bundles\":[";
    int ok = 0, bad = 0, plugs = 0;
    std::string block;
    for (size_t i = 0; i < bundles.size(); i++) {
        ScanResult r = scanOutOfProcess(self, bundles[i], atoi(opt(o, "timeout", "30").c_str()));
        js += (i ? ",\n " : "\n ") + scanResultJson(r);
        if (r.ok) { ok++; plugs += (int)r.plugins.size(); } else { bad++; block += (block.empty() ? "" : ",") + jstr(r.path); }
        fprintf(stderr, "%s  %s  %s%s\n", r.ok ? "ok  " : "FAIL", bundles[i].c_str(), r.ok ? (std::to_string(r.plugins.size()) + " plug-in(s)").c_str() : r.error.c_str(), r.archs.empty() ? "" : ("  [" + r.archs + "]").c_str());
    }
    js += "\n],\"bundlesFound\":" + std::to_string(bundles.size()) + ",\"bundlesOk\":" + std::to_string(ok) + ",\"bundlesFailed\":" + std::to_string(bad) + ",\"pluginsFound\":" + std::to_string(plugs) +
          ",\"blocklist\":[" + block + "],\"hostStillAlive\":true}\n";
    std::string f = opt(o, "json");
    if (!f.empty()) { FILE* fp = fopen(f.c_str(), "wb"); if (fp) { fputs(js.c_str(), fp); fclose(fp); } }
    else fputs(js.c_str(), stdout);
    fprintf(stderr, "%zu bundle(s), %d ok, %d failed, %d plug-in(s)\n", bundles.size(), ok, bad, plugs);
    return 0;
}

struct Render {
    std::vector<float> L, R;
    double avgUs = 0, worstUs = 0, budgetUs = 0, p99Us = 0;
    double peak = 0, rms = 0;
    bool ok = false; std::string err;
    int blocks = 0, failedBlocks = 0;
};

static Render render(PluginInstance& p, bool instrument, const Wav* input, double sr, int block, double seconds, bool offline) {
    Render r;
    if (!p.prepare(sr, block, offline, r.err)) return r;
    size_t total = (size_t)(seconds * sr);
    r.L.assign(total, 0); r.R.assign(total, 0);
    std::vector<float> iL(block), iR(block);
    const int pitches[6] = {48, 55, 60, 63, 67, 72};
    struct Ev { size_t at; bool on; int pitch; };
    std::vector<Ev> evs;
    if (instrument) {
        size_t step = (size_t)(0.5 * sr), len = (size_t)(0.4 * sr);
        for (int k = 0; (size_t)k * step + len < total - (size_t)(0.5 * sr) && k < 64; k++) { evs.push_back({(size_t)k * step, true, pitches[k % 6]}); evs.push_back({(size_t)k * step + len, false, pitches[k % 6]}); }
        std::sort(evs.begin(), evs.end(), [](const Ev& a, const Ev& b) { return a.at < b.at; });
    }
    size_t evi = 0, inFrames = input ? input->frames() : 0, audioEnd = total > (size_t)sr ? total - (size_t)sr : total;   // the last second is silence in, to hear the tail
    std::vector<double> times;
    ProcessContext ctx; ctx.sampleRate = sr; ctx.tempo = 120;
    for (size_t pos = 0; pos < total; pos += block) {
        int n = (int)std::min<size_t>(block, total - pos);
        for (int i = 0; i < n; i++) {
            size_t s = pos + i;
            if (input && inFrames && s < audioEnd) { iL[i] = input->data[2 * (s % inFrames)]; iR[i] = input->data[2 * (s % inFrames) + 1]; } else { iL[i] = 0; iR[i] = 0; }
        }
        NoteEvent ne[32]; int nn = 0;
        while (evi < evs.size() && evs[evi].at < pos + n && nn < 32) { ne[nn].offset = (int)(evs[evi].at - pos); ne[nn].on = evs[evi].on; ne[nn].pitch = evs[evi].pitch; ne[nn].velocity = 0.8f; ne[nn].channel = 0; nn++; evi++; }
        const float* in[2] = {iL.data(), iR.data()};
        float* out[2] = {&r.L[pos], &r.R[pos]};
        ctx.samplePos = (int64_t)pos;
        auto t0 = std::chrono::steady_clock::now();
        bool ok = p.process(in, 2, out, 2, n, ne, nn, ctx);
        double us = std::chrono::duration<double, std::micro>(std::chrono::steady_clock::now() - t0).count();
        times.push_back(us);
        if (!ok) r.failedBlocks++;
        r.blocks++;
    }
    double sum = 0, se = 0;
    for (double t : times) { sum += t; if (t > r.worstUs) r.worstUs = t; }
    r.avgUs = times.empty() ? 0 : sum / times.size();
    std::sort(times.begin(), times.end());
    if (!times.empty()) r.p99Us = times[(size_t)(times.size() * 0.99)];
    r.budgetUs = block / sr * 1e6;
    for (size_t i = 0; i < total; i++) { r.peak = std::max(r.peak, (double)std::max(std::fabs(r.L[i]), std::fabs(r.R[i]))); se += (double)r.L[i] * r.L[i] + (double)r.R[i] * r.R[i]; }
    r.rms = total ? std::sqrt(se / (2 * total)) : 0;
    bool finite = std::isfinite(r.peak);
    r.ok = r.failedBlocks == 0 && finite;
    if (!finite) r.err = "the plug-in produced numbers that are not finite";
    return r;
}
static std::string renderJson(const Render& r) {
    return "{\"ok\":" + std::string(r.ok ? "true" : "false") + ",\"error\":" + jstr(r.err) + ",\"blocks\":" + std::to_string(r.blocks) + ",\"failedBlocks\":" + std::to_string(r.failedBlocks) +
           ",\"peak\":" + jnum(r.peak) + ",\"peakDb\":" + (r.peak > 0 ? jnum(20 * std::log10(r.peak)) : "null") + ",\"rmsDb\":" + (r.rms > 0 ? jnum(20 * std::log10(r.rms)) : "null") +
           ",\"cpu\":{\"avgMicroseconds\":" + jnum(r.avgUs) + ",\"p99Microseconds\":" + jnum(r.p99Us) + ",\"worstMicroseconds\":" + jnum(r.worstUs) + ",\"blockLastsMicroseconds\":" + jnum(r.budgetUs) +
           ",\"avgPercentOfBlock\":" + jnum(r.budgetUs ? r.avgUs / r.budgetUs * 100 : 0) + ",\"worstPercentOfBlock\":" + jnum(r.budgetUs ? r.worstUs / r.budgetUs * 100 : 0) + "}}";
}
static std::string compareJson(const Render& a, const Render& b) {
    size_t n = std::min(a.L.size(), b.L.size()), diff = 0; double maxd = 0;
    for (size_t i = 0; i < n; i++) {
        if (memcmp(&a.L[i], &b.L[i], 4)) diff++;
        if (memcmp(&a.R[i], &b.R[i], 4)) diff++;
        maxd = std::max(maxd, (double)std::max(std::fabs(a.L[i] - b.L[i]), std::fabs(a.R[i] - b.R[i])));
    }
    return "{\"identical\":" + std::string(diff == 0 && a.L.size() == b.L.size() ? "true" : "false") + ",\"differing\":" + std::to_string(diff) + ",\"samples\":" + std::to_string(2 * n) +
           ",\"maxDifferenceDb\":" + (maxd > 0 ? jnum(20 * std::log10(maxd)) : "null") + "}";
}
static void writeWav(const std::string& path, const Render& r, int sr) {
    Wav w; w.sr = sr; w.ch = 2; w.data.resize(r.L.size() * 2);
    for (size_t i = 0; i < r.L.size(); i++) { w.data[2 * i] = r.L[i]; w.data[2 * i + 1] = r.R[i]; }
    wavWrite(path, w);
}

static int cmdRun(int argc, char** argv) {
    auto o = opts(argc, argv, 2);
    PluginFormat* F = vst3Format();
    PluginInfo want; want.format = "vst3"; want.path = opt(o, "plugin"); want.name = opt(o, "name");
    std::string outdir = opt(o, "outdir", "."), tag = opt(o, "tag", "plugin");
    double sr = atof(opt(o, "sr", "48000").c_str()), seconds = atof(opt(o, "seconds", "4").c_str());
    int block = atoi(opt(o, "block", "128").c_str());
    std::string js = "{\"bundle\":" + jstr(want.path) + ",\"archs\":" + jstr(bundleArchs(want.path)) + ",\"hostArch\":" + jstr(hostArch());
    auto finish = [&](int code) { js += "}\n"; FILE* fp = fopen((outdir + "/" + tag + ".json").c_str(), "wb"); if (fp) { fputs(js.c_str(), fp); fclose(fp); } fputs(js.c_str(), stdout); return code; };
    std::string err;
    auto t0 = std::chrono::steady_clock::now();
    auto A = F->create(want, err);
    if (!A) { js += ",\"loaded\":false,\"error\":" + jstr(err); return finish(1); }
    double loadMs = std::chrono::duration<double, std::milli>(std::chrono::steady_clock::now() - t0).count();
    const PluginInfo& pi = A->info();
    BusLayout bl = A->buses();
    bool instrument = pi.isInstrument && bl.eventIns > 0;
    js += ",\"loaded\":true,\"loadMilliseconds\":" + jnum(loadMs) + ",\"name\":" + jstr(pi.name) + ",\"vendor\":" + jstr(pi.vendor) + ",\"version\":" + jstr(pi.version) + ",\"categories\":" + jstr(pi.categories) +
          ",\"kind\":" + (instrument ? "\"instrument\"" : "\"effect\"") + ",\"buses\":{\"audioIn\":" + std::to_string(bl.audioIns) + ",\"audioOut\":" + std::to_string(bl.audioOuts) + ",\"mainInChannels\":" + std::to_string(bl.mainInChannels) +
          ",\"mainOutChannels\":" + std::to_string(bl.mainOutChannels) + ",\"eventIn\":" + std::to_string(bl.eventIns) + ",\"eventOut\":" + std::to_string(bl.eventOuts) + "}";
    // parameters
    auto ps = A->params();
    int autom = 0; for (auto& p : ps) if (p.automatable) autom++;
    js += ",\"parameters\":{\"count\":" + std::to_string(ps.size()) + ",\"automatable\":" + std::to_string(autom) + ",\"first\":[";
    for (size_t i = 0; i < ps.size() && i < 12; i++) {
        double v = A->getParam(ps[i].id);
        js += std::string(i ? "," : "") + "{\"id\":" + std::to_string(ps[i].id) + ",\"name\":" + jstr(ps[i].name) + ",\"units\":" + jstr(ps[i].units) + ",\"value\":" + jnum(v) + ",\"text\":" + jstr(A->paramText(ps[i].id, v)) +
              ",\"default\":" + jnum(ps[i].defaultValue) + ",\"steps\":" + std::to_string(ps[i].steps) + ",\"automatable\":" + (ps[i].automatable ? "true" : "false") + "}";
    }
    js += "]}";
    Wav input; const Wav* in = nullptr;
    if (!instrument) { if (wavRead(opt(o, "in"), input, err) && input.ch == 2) in = &input; else { js += ",\"error\":" + jstr("an effect needs --in, a stereo 32-bit float WAV: " + err); return finish(1); } }
    // state of the fresh plug-in, before anything was played
    std::vector<uint8_t> S;
    bool gotState = A->getState(S);
    js += ",\"state\":{\"saved\":" + std::string(gotState ? "true" : "false") + ",\"bytes\":" + std::to_string(S.size());
    // 1. real-time render
    Render R1 = render(*A, instrument, in, sr, block, seconds, false);
    int latency = A->latencySamples(); int64_t tail = A->tailSamples();
    writeWav(outdir + "/" + tag + "_realtime.wav", R1, (int)sr);
    // 2. a second fresh plug-in: is the plug-in the same twice in a row at all?
    std::string cmpFresh = "null", cmpState = "null", cmpOffline = "null", offlineJs = "null", otherJs = "null";
    { auto C = F->create(want, err); if (C) { Render R3 = render(*C, instrument, in, sr, block, seconds, false); cmpFresh = compareJson(R1, R3); } }
    // 3. a new plug-in that gets the saved state
    bool restored = false;
    { auto B = F->create(want, err); if (B && gotState) { restored = B->setState(S); Render R2 = render(*B, instrument, in, sr, block, seconds, false); cmpState = compareJson(R1, R2); } }
    js += ",\"restored\":" + std::string(restored ? "true" : "false") + ",\"twoFreshPluginsSameSound\":" + cmpFresh + ",\"restoredPluginSameSound\":" + cmpState;
    // 4. a changed setting travels inside the state
    {
        const ParamInfo* pick = nullptr;
        for (auto& p : ps) if (p.automatable && !p.readOnly && !p.isBypass && !p.hidden) { pick = &p; break; }
        if (pick) {
            double before = A->getParam(pick->id), target = before < 0.5 ? 0.9 : 0.1;
            A->setParam(pick->id, target);
            // let the audio side take the change
            { std::vector<float> z(block, 0), o1(block), o2(block); const float* ii[2] = {z.data(), z.data()}; float* oo[2] = {o1.data(), o2.data()}; ProcessContext c; c.sampleRate = sr; A->process(ii, 2, oo, 2, block, nullptr, 0, c); }
            std::vector<uint8_t> S2; A->getState(S2);
            auto D = F->create(want, err);
            double got = -1; bool ok2 = false;
            if (D) { ok2 = D->setState(S2); got = D->getParam(pick->id); }
            js += ",\"changedSetting\":{\"name\":" + jstr(pick->name) + ",\"before\":" + jnum(before) + ",\"setTo\":" + jnum(A->getParam(pick->id)) + ",\"afterRestoreInNewPlugin\":" + jnum(got) +
                  ",\"carried\":" + (ok2 && std::fabs(got - A->getParam(pick->id)) < 1e-6 ? "true" : "false") + ",\"stateBytes\":" + std::to_string(S2.size()) + ",\"stateDiffersFromFresh\":" + (S2 != S ? "true" : "false") + "}";
        }
    }
    js += "}";
    // 5. export mode (offline), the same block size, so only the mode differs
    { auto E = F->create(want, err); if (E) { if (gotState) E->setState(S); Render R4 = render(*E, instrument, in, sr, block, seconds, true); writeWav(outdir + "/" + tag + "_export.wav", R4, (int)sr); offlineJs = renderJson(R4); cmpOffline = compareJson(R1, R4); } }
    // 6. another sample rate and a small buffer on the plug-in that is already running
    { Render R5 = render(*A, instrument, in, 96000, 32, 1.5, false); otherJs = renderJson(R5); }
    js += ",\"latencySamples\":" + std::to_string(latency) + ",\"tailSamples\":" + std::to_string(tail) + ",\"sampleRate\":" + jnum(sr) + ",\"block\":" + std::to_string(block) + ",\"seconds\":" + jnum(seconds) +
          ",\"realtime\":" + renderJson(R1) + ",\"export\":" + offlineJs + ",\"exportSameAsRealtime\":" + cmpOffline + ",\"at96kBlock32\":" + otherJs;
    if (opt(o, "editor") == "1") js += ",\"hasOwnWindow\":" + std::string(A->hasEditor() ? "true" : "false");
    return finish(R1.ok && R1.peak > 0 ? 0 : 1);
}

// alvst3 diag --plugin BUNDLE [--name NAME] [--sr 48000] [--block 512] [--seconds 2] --outdir DIR --tag TAG
// task NL5: the plug-in under the 0.5 host, the 0.4 host and one change at a time; what it asked for and what it got.
static int cmdDiag(int argc, char** argv) {
    auto o = opts(argc, argv, 2);
    PluginInfo want; want.format = "vst3"; want.path = opt(o, "plugin"); want.name = opt(o, "name");
    std::string outdir = opt(o, "outdir", "."), tag = opt(o, "tag", "plugin");
    double sr = atof(opt(o, "sr", "48000").c_str()), seconds = atof(opt(o, "seconds", "2").c_str());
    int block = atoi(opt(o, "block", "512").c_str());
    std::string err;
    auto p = vst3Format()->create(want, err);
    if (!p) { fprintf(stderr, "could not load: %s\n", err.c_str()); return 1; }
    PluginInfo pi = p->info();
    std::string diag0;
    { std::string e; if (p->prepare(sr, block, false, e)) diag0 = diagText(pi.name, p->diag()); }
    auto ps = p->presets();
    p.reset();
    auto v = probeSilence(pi, sr, block, seconds, true, [](double s) { if (s > 0) usleep((useconds_t)(s * 1e6)); });
    std::string text = diag0 + "[presets] " + pi.name + ": " + std::to_string(ps.size()) + " reachable through VST3" + (ps.empty() ? "" : " (first: \"" + ps[0].name + "\", " + ps[0].source + ")") + "\n" + probeText(pi.name, v);
    std::string js = probeJson(pi, sr, block, v);
    FILE* f = fopen((outdir + "/" + tag + "_diag.json").c_str(), "wb"); if (f) { fputs(js.c_str(), f); fclose(f); }
    f = fopen((outdir + "/" + tag + "_diag.txt").c_str(), "wb"); if (f) { fputs(text.c_str(), f); fclose(f); }
    fputs(text.c_str(), stdout);
    for (auto& x : v) if (x.key == "host-0.5") return x.ran && x.peak > 0 ? 0 : 1;
    return 1;
}

// alvst3 nl7 --plugin AL-STRICT-SYNTH-BUNDLE [--sr 48000] [--outdir DIR --tag TAG]
// task NL7: the parts of test app 0.7 that need no window and no sound card, on the test instrument:
//   1 plug-in strings cleaned (U+202F, U+2212, U+00A0 and an accented letter), 2 a plug-in at +20 dBFS and the app's
//   safety limiter, 3 a parameter that changes without performEdit, found by polling, 4 the event ring (state set, preset)
static int cmdNl7(int argc, char** argv) {
    auto o = opts(argc, argv, 2);
    PluginInfo want; want.format = "vst3"; want.path = opt(o, "plugin"); want.name = opt(o, "name");
    double sr = atof(opt(o, "sr", "48000").c_str()); int block = 512;
    std::string out; int fails = 0;
    auto line = [&](bool ok, const std::string& s) { out += std::string("[nl7] ") + (ok ? "PASS " : "FAIL ") + s + "\n"; if (!ok) fails++; };
    auto clean = [](const std::string& s) { return s.find("\xE2\x80\xAF") == std::string::npos && s.find("\xE2\x88\x92") == std::string::npos && s.find("\xC2\xA0") == std::string::npos; };
    // 1. the clean-up itself
    std::string t = asciiClean("17.1\xE2\x80\xAFms \xE2\x88\x92" "3.26\xC2\xA0" "dB caf\xC3\xA9");
    line(t == "17.1 ms -3.26 dB caf\xC3\xA9", "text: \"17.1<U+202F>ms <U+2212>3.26<U+00A0>dB caf<e acute>\" -> \"" + t + "\" (the accented letter stays: a report holding it starts with a byte order mark: " + (isAscii(t) ? "no" : "yes") + ")");
    std::string err;
    auto p = vst3Format()->create(want, err);
    if (!p) { fprintf(stderr, "could not load: %s\n", err.c_str()); return 1; }
    EventRing ring;
    p->setEventSink([&](uint32_t k, uint32_t a) { ring.push(k, a); });
    if (!p->prepare(sr, block, false, err)) { fprintf(stderr, "could not start: %s\n", err.c_str()); return 1; }
    // let the loader thread's message arrive
    std::this_thread::sleep_for(std::chrono::milliseconds(100));
    auto ps = p->params();
    bool allClean = true; std::string shown;
    std::map<std::string, uint32_t> byName;
    for (auto& q : ps) {
        double v = p->getParam(q.id);
        std::string vt = p->paramText(q.id, v);
        byName[q.name] = q.id;
        allClean = allClean && clean(q.name) && clean(q.units) && clean(vt);
        shown += (shown.empty() ? "" : "; ") + q.name + (q.units.empty() ? "" : " [" + q.units + "]") + " = \"" + vt + "\"";
    }
    auto pr = p->presets();
    for (auto& x : pr) { allClean = allClean && clean(x.name); shown += "; program \"" + x.name + "\""; }
    line(allClean && !ps.empty(), "plug-in strings (titles, units, value texts, program names) carry none of U+202F, U+2212, U+00A0: " + shown);
    // 2. loud: the plug-in's own output past 0 dBFS; the app's output never
    auto find = [&](const char* n) -> int64_t { auto it = byName.find(n); return it == byName.end() ? -1 : (int64_t)it->second; };
    int64_t loudId = find("Loud (+20 dBFS)"), sneakyId = find("Sneaky drift"), levelId = find("Level");
    if (loudId >= 0) {
        p->setParam((uint32_t)loudId, 1.0);
        SafetyLimiter lim; lim.setRate(sr);
        std::vector<float> L(block), R(block), z(block, 0);
        float plugPk = 0, appPk = 0; int over = 0;
        ProcessContext ctx; ctx.sampleRate = sr;
        int blocks = (int)(1.5 * sr / block);
        for (int b = 0; b < blocks; b++) {
            NoteEvent ne[2]; int nn = 0;
            if (b % 20 == 0) { ne[0].on = true; ne[0].pitch = 60 + (b / 20) % 12; ne[0].offset = 0; nn = 1; }
            if (b % 20 == 15) { ne[0].on = false; ne[0].pitch = 60 + (b / 20) % 12; ne[0].offset = 0; nn = 1; }
            const float* in[2] = {z.data(), z.data()}; float* oo[2] = {L.data(), R.data()};
            ctx.samplePos = (int64_t)b * block;
            p->process(in, 2, oo, 2, block, ne, nn, ctx);
            float bp = 0; for (int i = 0; i < block; i++) bp = std::max(bp, std::max(std::fabs(L[i]), std::fabs(R[i])));
            if (bp > 1.0f) over++;
            plugPk = std::max(plugPk, bp);
            for (int i = 0; i < block; i++) { L[i] *= 0.5f; R[i] *= 0.5f; }
            appPk = std::max(appPk, lim.process(oo, 2, block));
        }
        char b[400];
        snprintf(b, sizeof b, "loud mode: the plug-in's own output peaked at %+.1f dBFS (%d of %d blocks past 0 dBFS); after the app's half level and safety limiter the output peaked at %.3f (%+.2f dBFS), limiter engaged %llu time(s), most %.1f dB",
                 20 * std::log10(std::max(plugPk, 1e-9f)), over, blocks, appPk, 20 * std::log10(std::max(appPk, 1e-9f)), (unsigned long long)lim.engaged.load(), lim.deepestDb.load());
        line(plugPk > 9.0f && appPk <= 1.0f && lim.engaged.load() >= 1, b);
        p->setParam((uint32_t)loudId, 0.0);
    } else line(false, "loud mode: no parameter \"Loud (+20 dBFS)\" (not the test instrument?)");
    // 3. a parameter that changes without performEdit, found by polling every 200 ms
    if (sneakyId >= 0) {
        ParamWatch pw;
        std::vector<uint32_t> ids; std::vector<std::string> names; std::vector<bool> ro;
        for (auto& q : ps) { ids.push_back(q.id); names.push_back(q.name); ro.push_back(q.readOnly); }
        pw.setParams(ids, names, ro);
        auto get = [&](uint32_t id) { return p->getParam(id); };
        pw.poll(get, p->takeTouchedParams(), false);
        p->setParam((uint32_t)sneakyId, 1.0);                 // the host's own change: must not count
        for (int k = 0; k < 6; k++) {
            std::this_thread::sleep_for(std::chrono::milliseconds(200));
            if (k == 2 && levelId >= 0) p->setParam((uint32_t)levelId, 0.7);   // the host's own change again
            pw.poll(get, p->takeTouchedParams(), false);
        }
        p->setParam((uint32_t)sneakyId, 0.0);
        std::string nm; for (auto& n : pw.firstNames) nm += (nm.empty() ? "" : ", ") + n;
        bool ok = pw.changes >= 3 && pw.firstNames.size() == 1 && pw.firstNames[0].find("rive") != std::string::npos;
        line(ok, "sneaky mode: " + std::to_string(pw.changes) + " change(s) without telling the host, in: " + nm + " (the host's own changes to Sneaky drift and Level not counted)");
    } else line(false, "sneaky mode: no parameter \"Sneaky drift\"");
    // 4. the event ring: the host sets the state and loads a program
    std::vector<uint8_t> st; p->getState(st); p->setState(st);
    if (!pr.empty()) p->loadPreset(pr[0], err);
    bool back = false;
    auto evs = ring.between(0, UINT64_MAX, &back);
    int nState = 0, nPreset = 0; for (auto& e : evs) { if (e.kind == evStateSet) nState++; if (e.kind == evPresetLoaded) nPreset++; }
    line(nState == 1 && nPreset == (pr.empty() ? 0 : 1), "events recorded: " + std::to_string(evs.size()) + " (state set " + std::to_string(nState) + ", preset loaded " + std::to_string(nPreset) + ")");
    fputs(out.c_str(), stdout);
    std::string outdir = opt(o, "outdir");
    if (!outdir.empty()) { FILE* f = fopen((outdir + "/" + opt(o, "tag", "nl7") + "_nl7.txt").c_str(), "wb"); if (f) { fputs(out.c_str(), f); fclose(f); } }
    return fails ? 1 : 0;
}

int main(int argc, char** argv) {
    int code = 0;
    if (scannerChildMain(argc, argv, code)) return code;
    if (probeChildMain(argc, argv, code, [](double s) { if (s > 0) usleep((useconds_t)(s * 1e6)); })) return code;
    std::string c = argc > 1 ? argv[1] : "";
    if (c == "scan") return cmdScan(argc, argv);
    if (c == "run") return cmdRun(argc, argv);
    if (c == "diag") return cmdDiag(argc, argv);
    if (c == "nl7") return cmdNl7(argc, argv);
    fprintf(stderr, "usage: alvst3 scan [--folder DIR]... [--json FILE] | alvst3 run --plugin BUNDLE [--name NAME] --outdir DIR --tag TAG [--in FILE.wav]\n");
    return 2;
}
