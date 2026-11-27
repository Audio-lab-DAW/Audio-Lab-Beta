// Task NL5: why does an instrument stay silent in this host? Measured, not guessed.
// probeSilence renders a fresh instance of a plug-in under several host set-ups and reports each one, so a report from
// the user's Mac says which part of the host set-up a plug-in depends on. Also: the [diag] lines for one instance, and a
// plain listing of CLAP and Audio Unit bundles (decision D5), without loading any of them.
#include "plugin_api.h"
#include "../common/json.h"
#include <chrono>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <algorithm>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <fcntl.h>
#include <signal.h>
#include <sys/wait.h>
#include <thread>
#include <unistd.h>

namespace al {

static std::string db(double v) { if (v <= 0) return "silent (0)"; char b[32]; snprintf(b, sizeof b, "%.1f dB", 20 * std::log10(v)); return b; }
static const char* rcName(int r) {
    switch (r) { case 0: return "ok"; case 1: return "false"; case 2: return "invalid argument"; case 3: return "not implemented"; case 4: return "internal error"; case 5: return "not initialised"; case 6: return "out of memory"; case -999: return "not called"; default: return "other"; }
}

std::string diagText(const std::string& name, const HostDiag& d) {
    std::string o;
    for (auto& l : d.setup) o += "[diag] " + name + ": " + l + "\n";
    char b[900];
    snprintf(b, sizeof b, "[diag] %s: %llu blocks processed; the plug-in's own main output held sound in %llu of them (peak %s, measured before this app copies or halves it); other output buses held sound in %llu (peak %s); "
             "blocks with a silence flag set by the plug-in: %llu; process() not ok: %llu (last result: %s); notes handed over: %llu on, %llu off, %llu refused by the event list; parameter changes handed over: %llu; "
             "messages between its two parts: %d to the processor, %d to the controller, %d of them from a thread other than the main thread, %d dropped",
             name.c_str(), (unsigned long long)d.blocks, (unsigned long long)d.blocksMainNonZero, db(d.peakMain).c_str(), (unsigned long long)d.blocksOtherNonZero, db(d.peakOther).c_str(),
             (unsigned long long)d.blocksSilenceFlag, (unsigned long long)d.processNotOk, rcName(d.lastProcessResult), (unsigned long long)d.noteOns, (unsigned long long)d.noteOffs, (unsigned long long)d.eventsRejected,
             (unsigned long long)d.paramChanges, d.msgToProcessor, d.msgToController, d.msgOffMainThread, d.msgDropped);
    o += b; o += "\n";
    return o;
}

std::vector<ProbeVariant> probeSilence(const PluginInfo& info, double sr, int block, double seconds, bool withPreset, const std::function<void(double)>& idle) {
    struct V { const char* key; const char* what; HostOptions o; bool playing; bool preset; };
    HostOptions h5;
    std::vector<V> vs;
    vs.push_back({"host-0.5", "the 0.5 host (as JUCE and the SDK's validator)", h5, true, false});
    vs.push_back({"host-0.4", "the 0.4 host (as on your Mac in reports 4 and 5)", HostOptions::legacy04(), true, false});
    { HostOptions o = h5; o.syncControllerState = false; vs.push_back({"no-state-sync", "0.5 without giving the controller the processor's state", o, true, false}); }
    { HostOptions o = h5; o.messagesAnyThread = false; vs.push_back({"main-thread-messages", "0.5 but messages from other threads dropped (the SDK's proxy)", o, true, false}); }
    { HostOptions o = h5; o.validatorOrder = false; o.preferredArrangements = false; vs.push_back({"old-bus-setup", "0.5 but buses set up as in 0.4 (stereo forced, before setupProcessing)", o, true, false}); }
    { HostOptions o = h5; o.uniqueNoteIds = true; vs.push_back({"unique-note-ids", "0.5 with a unique id on every note", o, true, false}); }
    { HostOptions o = h5; o.allAudioBuses = true; vs.push_back({"all-buses", "0.5 with every audio bus active", o, true, false}); }
    vs.push_back({"transport-stopped", "0.5 with the transport stopped", h5, false, false});
    if (withPreset) vs.push_back({"first-preset", "0.5 after loading its first factory preset", h5, true, true});

    std::vector<ProbeVariant> out;
    const int seq[8] = {48, 60, 55, 63, 67, 60, 72, 63};
    for (auto& v : vs) {
        ProbeVariant pv; pv.key = v.key; pv.what = v.what;
        std::string err;
        auto p = vst3Format()->createWith(info, v.o, err);
        if (!p) { pv.error = "could not load: " + err; out.push_back(pv); continue; }
        if (v.preset) {
            auto ps = p->presets();
            if (ps.empty()) { pv.error = "no factory preset reachable through VST3 (no program list, no .vstpreset file)"; out.push_back(pv); continue; }
            if (!p->loadPreset(ps[0], err)) { pv.error = "preset \"" + ps[0].name + "\" not loaded: " + err; out.push_back(pv); continue; }
            pv.what += " (\"" + ps[0].name + "\")";
        }
        if (!p->prepare(sr, block, false, err)) { pv.error = "could not be started: " + err; pv.d = p->diag(); out.push_back(pv); continue; }
        for (int i = 0; i < 8; i++) idle(0.05);      // 0.4 s for work a plug-in does on the main thread or in the background after loading
        size_t total = (size_t)(seconds * sr), stepLen = (size_t)(sr * 0.25);
        std::vector<float> iL(block, 0), iR(block, 0), oL(block), oR(block);
        int curNote = -1, curStep = -1, blk = 0;
        for (size_t pos = 0; pos < total; pos += block, blk++) {
            int n = (int)std::min<size_t>(block, total - pos);
            NoteEvent ev[8]; int ne = 0;
            for (int i = 0; i < n && ne < 6; i++) {
                int step = (int)((pos + i) / stepLen);
                if (step == curStep) continue;
                if (curNote >= 0) { ev[ne].offset = i; ev[ne].on = false; ev[ne].pitch = curNote; ev[ne].channel = 0; ev[ne].velocity = 0; ne++; }
                curStep = step; curNote = seq[step & 7];
                ev[ne].offset = i; ev[ne].on = true; ev[ne].pitch = curNote; ev[ne].channel = 0; ev[ne].velocity = 0.8f; ne++;
            }
            const float* in[2] = {iL.data(), iR.data()}; float* o2[2] = {oL.data(), oR.data()};
            ProcessContext c; c.sampleRate = sr; c.tempo = 120; c.samplePos = (int64_t)pos; c.playing = v.playing;
            p->process(in, 2, o2, 2, n, ev, ne, c);
            for (int i = 0; i < n; i++) { double a = std::max(std::fabs(oL[i]), std::fabs(oR[i])); if (a > pv.peak) pv.peak = a; }
            if (pv.peak > 0 && pv.firstSoundBlock < 0) pv.firstSoundBlock = blk;
            idle(0);
        }
        pv.ran = true;
        pv.d = p->diag();
        out.push_back(pv);
        p.reset();
        idle(0.02);
    }
    return out;
}

std::string probeText(const std::string& name, const std::vector<ProbeVariant>& v) {
    std::string o;
    char b[900];
    for (auto& x : v) {
        if (!x.ran) { o += "[probe] " + name + ", " + x.what + ": " + x.error + "\n"; continue; }
        snprintf(b, sizeof b, "[probe] %s, %s: %s%s; its main output held sound in %llu of %llu blocks, other buses in %llu; messages %d to the processor, %d to the controller, %d from other threads, %d dropped; controller given the state: %s",
                 name.c_str(), x.what.c_str(), x.peak > 0 ? "SOUND, peak " : "SILENT", x.peak > 0 ? db(x.peak).c_str() : "", (unsigned long long)x.d.blocksMainNonZero, (unsigned long long)x.d.blocks,
                 (unsigned long long)x.d.blocksOtherNonZero, x.d.msgToProcessor, x.d.msgToController, x.d.msgOffMainThread, x.d.msgDropped, rcName(x.d.setComponentStateResult));
        o += b; o += "\n";
    }
    // the conclusion, in one line
    auto find = [&](const char* k) -> const ProbeVariant* { for (auto& x : v) if (x.key == k) return &x; return nullptr; };
    const ProbeVariant* h5 = find("host-0.5"); const ProbeVariant* h4 = find("host-0.4");
    std::string c;
    if (h5 && h5->ran && h4 && h4->ran) {
        bool s5 = h5->peak > 0, s4 = h4->peak > 0;
        std::string needs;
        for (auto& x : v) if (x.ran && x.key != "host-0.5" && x.key != "host-0.4" && x.key != "first-preset" && s5 && x.peak <= 0) needs += (needs.empty() ? "" : "; ") + x.what;
        if (s5 && !s4) c = "the 0.4 host's set-up was the cause: it sounds with 0.5, not with 0.4." + (needs.empty() ? std::string(" No single change alone brings the silence back.") : " Silent again with: " + needs + ".");
        else if (s5 && s4) c = "it sounds with both hosts here." + (needs.empty() ? std::string("") : " Silent with: " + needs + ".") + " If it was silent while you played, the difference is elsewhere (its patch, or what it was doing at that moment).";
        else if (!s5 && !s4) {
            const ProbeVariant* fp = find("first-preset");
            if (fp && fp->ran && fp->peak > 0) c = "silent with its start patch under every host set-up, but it SOUNDS after its first factory preset: the start patch is empty or quiet.";
            else {
                bool any = false; for (auto& x : v) if (x.ran && x.peak > 0) any = true;
                c = any ? "silent with both hosts, but one variant above sounds: see which." : "silent under every host set-up tried: the host's set-up is not the cause. Load a preset in its own window and play again, and check that it is authorised (a demo or an unlicensed copy can be silent).";
            }
        } else c = "it sounds with 0.4 but not with 0.5: please send this report.";
    }
    if (!c.empty()) o += "[probe] " + name + ", conclusion: " + c + "\n";
    return o;
}

std::string probeJson(const PluginInfo& info, double sr, int block, const std::vector<ProbeVariant>& v) {
    std::string s = "{\"name\":" + jstr(info.name) + ",\"vendor\":" + jstr(info.vendor) + ",\"sampleRate\":" + jnum(sr) + ",\"block\":" + std::to_string(block) + ",\"variants\":[";
    for (size_t i = 0; i < v.size(); i++) {
        auto& x = v[i];
        s += std::string(i ? "," : "") + "\n {\"key\":" + jstr(x.key) + ",\"what\":" + jstr(x.what) + ",\"ran\":" + (x.ran ? "true" : "false") + ",\"error\":" + jstr(x.error) + ",\"peak\":" + jnum(x.peak) +
             ",\"firstSoundBlock\":" + std::to_string(x.firstSoundBlock) + ",\"blocks\":" + std::to_string(x.d.blocks) + ",\"blocksMainNonZero\":" + std::to_string(x.d.blocksMainNonZero) +
             ",\"blocksOtherNonZero\":" + std::to_string(x.d.blocksOtherNonZero) + ",\"silenceFlagBlocks\":" + std::to_string(x.d.blocksSilenceFlag) + ",\"processNotOk\":" + std::to_string(x.d.processNotOk) +
             ",\"msgToProcessor\":" + std::to_string(x.d.msgToProcessor) + ",\"msgToController\":" + std::to_string(x.d.msgToController) + ",\"msgOffMainThread\":" + std::to_string(x.d.msgOffMainThread) +
             ",\"msgDropped\":" + std::to_string(x.d.msgDropped) + ",\"setComponentState\":" + jstr(rcName(x.d.setComponentStateResult)) + ",\"setup\":[";
        for (size_t k = 0; k < x.d.setup.size(); k++) s += std::string(k ? "," : "") + jstr(x.d.setup[k]);
        s += "]}";
    }
    return s + "\n]}\n";
}

bool probeChildMain(int argc, char** argv, int& exitCode, const std::function<void(double)>& idle) {
    if (argc < 7 || strcmp(argv[1], "--al-probe")) return false;
    PluginInfo pi; pi.format = "vst3"; pi.path = argv[2]; pi.uid = argv[3];
    double sr = atof(argv[4]); int block = atoi(argv[5]);
    std::string outFile = argv[6];
    alarm(180);
    std::string err;
    { auto p = vst3Format()->create(pi, err); if (p) pi = p->info(); }
    auto v = probeSilence(pi, sr, block, 2.0, true, idle);
    std::string text = probeText(pi.name, v);
    { std::ofstream f(outFile + ".txt", std::ios::binary); f << text; }
    { std::ofstream f(outFile, std::ios::binary); f << probeJson(pi, sr, block, v); }
    fputs(text.c_str(), stdout); fflush(stdout);
    exitCode = 0;
    _exit(0);      // as the scanner: skip unload code, some plug-ins crash there
    return true;
}

std::string probeOutOfProcess(const std::string& selfExe, const PluginInfo& info, double sr, int block, const std::string& outFile, int timeoutSeconds, std::string& err) {
    unlink((outFile + ".txt").c_str());
    pid_t pid = fork();
    if (pid == 0) {
        int nul = open("/dev/null", 1); if (nul >= 0) { dup2(nul, 1); dup2(nul, 2); }
        std::string r = std::to_string(sr), b = std::to_string(block);
        execl(selfExe.c_str(), selfExe.c_str(), "--al-probe", info.path.c_str(), info.uid.c_str(), r.c_str(), b.c_str(), outFile.c_str(), (char*)nullptr);
        _exit(127);
    }
    if (pid < 0) { err = "could not start the probe"; return ""; }
    int status = 0; auto t0 = std::chrono::steady_clock::now();
    while (true) {
        pid_t w = waitpid(pid, &status, WNOHANG);
        if (w == pid) break;
        if (std::chrono::steady_clock::now() - t0 > std::chrono::seconds(timeoutSeconds)) { kill(pid, SIGKILL); waitpid(pid, &status, 0); err = "the probe took longer than " + std::to_string(timeoutSeconds) + " s and was stopped"; return ""; }
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
    }
    if (WIFSIGNALED(status)) { err = "the probe crashed (signal " + std::to_string(WTERMSIG(status)) + "): the plug-in crashed in one of the set-ups"; }
    std::ifstream f(outFile + ".txt", std::ios::binary);
    std::string text((std::istreambuf_iterator<char>(f)), std::istreambuf_iterator<char>());
    if (text.empty() && err.empty()) err = "the probe gave no answer";
    return text;
}

std::vector<ListedBundle> listOtherFormat(const std::string& format, std::vector<std::string>& folders) {
    namespace fs = std::filesystem;
    std::vector<ListedBundle> out;
    folders.clear();
    const char* home = getenv("HOME");
    std::string sub = format == "clap" ? "CLAP" : "Components", ext = format == "clap" ? ".clap" : ".component";
#if defined(__APPLE__)
    if (home) folders.push_back(std::string(home) + "/Library/Audio/Plug-Ins/" + sub);
    folders.push_back("/Library/Audio/Plug-Ins/" + sub);
#else
    if (format == "clap") { if (home) folders.push_back(std::string(home) + "/.clap"); folders.push_back("/usr/lib/clap"); }
#endif
    for (auto& f : folders) {
        std::error_code ec;
        if (!fs::is_directory(f, ec)) continue;
        std::vector<fs::path> found;
        for (fs::recursive_directory_iterator it(f, fs::directory_options::skip_permission_denied, ec), end; !ec && it != end; it.increment(ec)) {
            if (it->path().extension() == ext) { found.push_back(it->path()); if (it->is_directory(ec)) it.disable_recursion_pending(); }
            if (it.depth() > 4) it.disable_recursion_pending();
        }
        std::sort(found.begin(), found.end());
        for (auto& p : found) {
            ListedBundle b; b.path = p.string(); b.name = p.stem().string(); b.archs = bundleArchs(p.string());
            // an Audio Unit names itself and its kind in its Info.plist (AudioComponents: name "Maker: Name", type aumu/aufx/aumf/...)
            if (format == "au") {
                std::ifstream pl(p / "Contents" / "Info.plist", std::ios::binary);
                std::string t((std::istreambuf_iterator<char>(pl)), std::istreambuf_iterator<char>());
                size_t k = t.find("<key>AudioComponents</key>");
                if (k != std::string::npos) {
                    auto val = [&](const char* key) { size_t a = t.find(std::string("<key>") + key + "</key>", k); if (a == std::string::npos) return std::string(); a = t.find("<string>", a); size_t e = t.find("</string>", a); return a == std::string::npos || e == std::string::npos ? std::string() : t.substr(a + 8, e - a - 8); };
                    std::string nm = val("name"), ty = val("type");
                    if (!nm.empty()) b.name = nm;
                    b.kind = ty == "aumu" ? "instrument" : ty == "aufx" ? "effect" : ty == "aumf" ? "effect with MIDI" : ty == "aumi" ? "MIDI processor" : ty == "augn" ? "generator" : ty.empty() ? "" : ty;
                }
            }
            out.push_back(b);
        }
    }
    return out;
}

}  // namespace al
