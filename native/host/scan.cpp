// Scanning plug-ins in a separate process (task NM1). The child loads one bundle and prints what it found as
// plain lines; the parent reads them with a time limit. If the bundle crashes or hangs, only the child dies.
#include "plugin_api.h"
#include "../common/json.h"
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <filesystem>
#include <fcntl.h>
#include <fstream>
#include <signal.h>
#include <sys/wait.h>
#include <unistd.h>

namespace al {

std::string hostArch() {
#if defined(__aarch64__) || defined(__arm64__)
    return "arm64";
#elif defined(__x86_64__)
    return "x86_64";
#else
    return "other";
#endif
}

// Reads the header of the program inside a macOS bundle and says which processors it is built for.
std::string bundleArchs(const std::string& bundle) {
#ifdef __APPLE__
    namespace fs = std::filesystem;
    std::error_code ec;
    fs::path dir = fs::path(bundle) / "Contents" / "MacOS";
    std::string out;
    for (fs::directory_iterator it(dir, ec), end; !ec && it != end; it.increment(ec)) {
        std::ifstream f(it->path(), std::ios::binary);
        unsigned char h[4096] = {0};
        f.read((char*)h, sizeof h);
        size_t got = (size_t)f.gcount();
        if (got < 8) continue;
        auto be = [&](size_t p) { return ((uint32_t)h[p] << 24) | ((uint32_t)h[p + 1] << 16) | ((uint32_t)h[p + 2] << 8) | h[p + 3]; };
        auto le = [&](size_t p) { return ((uint32_t)h[p + 3] << 24) | ((uint32_t)h[p + 2] << 16) | ((uint32_t)h[p + 1] << 8) | h[p]; };
        auto nameOf = [](uint32_t cpu) { return cpu == 0x0100000c ? "arm64" : cpu == 0x01000007 ? "x86_64" : cpu == 7 ? "i386" : "other"; };
        uint32_t magic = be(0);
        if (magic == 0xcafebabe || magic == 0xcafebabf) {
            uint32_t n = be(4); size_t step = magic == 0xcafebabe ? 20 : 32;
            for (uint32_t i = 0; i < n && 8 + i * step + 4 <= got; i++) { if (!out.empty()) out += " "; out += nameOf(be(8 + i * step)); }
        } else if (le(0) == 0xfeedfacf || le(0) == 0xfeedface) out = nameOf(le(4));
        if (!out.empty()) break;
    }
    return out;
#else
    (void)bundle;
    return "";
#endif
}

static std::string clean(std::string s) { for (auto& c : s) if (c == '\t' || c == '\n' || c == '\r') c = ' '; return s; }

bool scannerChildMain(int argc, char** argv, int& exitCode) {
    if (argc < 3 || strcmp(argv[1], "--al-scan-one")) return false;
    std::string path = argv[2];
    alarm(argc > 3 ? atoi(argv[3]) : 30);   // a plug-in that hangs is stopped by the system
    const char* crash = getenv("AL_TEST_CRASH_ON");   // test hook: pretend this bundle crashes while loading
    if (crash && *crash && path.find(crash) != std::string::npos) abort();
    ScanResult r = vst3Format()->scanInProcess(path);
    printf("ARCH\t%s\n", clean(r.archs).c_str());
    if (!r.ok) printf("ERR\t%s\n", clean(r.error).c_str());
    for (auto& p : r.plugins)
        printf("PLUG\t%s\t%s\t%s\t%s\t%s\t%s\t%d\t%d\n", clean(p.uid).c_str(), clean(p.name).c_str(), clean(p.vendor).c_str(), clean(p.version).c_str(), clean(p.categories).c_str(), clean(p.sdk).c_str(), p.isInstrument ? 1 : 0, p.isEffect ? 1 : 0);
    printf("END\n");
    fflush(stdout);
    exitCode = r.ok ? 0 : 3;
    _exit(exitCode);   // leave without running the plug-in's unload code: a scanner does not need it and some plug-ins crash there
    return true;
}

ScanResult scanOutOfProcess(const std::string& selfExe, const std::string& bundle, int timeoutSeconds) {
    ScanResult r; r.path = bundle; r.archs = bundleArchs(bundle);
    auto t0 = std::chrono::steady_clock::now();
    std::string host = hostArch();
    if (!r.archs.empty() && r.archs.find(host) == std::string::npos) {
        r.wrongArch = true;
        r.error = "built for " + r.archs + " only; this program is " + host + " (it would need a helper process running under Rosetta)";
        return r;
    }
    int fd[2];
    if (pipe(fd) != 0) { r.error = "could not start the scanner"; return r; }
    pid_t pid = fork();
    if (pid == 0) {
        dup2(fd[1], 1); close(fd[0]); close(fd[1]);
        int nul = open("/dev/null", 1); if (nul >= 0) dup2(nul, 2);
        std::string t = std::to_string(timeoutSeconds);
        execl(selfExe.c_str(), selfExe.c_str(), "--al-scan-one", bundle.c_str(), t.c_str(), (char*)nullptr);
        _exit(127);
    }
    close(fd[1]);
    std::string text; char buf[4096]; ssize_t n;
    while ((n = read(fd[0], buf, sizeof buf)) > 0) text.append(buf, (size_t)n);
    close(fd[0]);
    int status = 0; waitpid(pid, &status, 0);
    r.seconds = std::chrono::duration<double>(std::chrono::steady_clock::now() - t0).count();
    bool ended = false;
    size_t pos = 0;
    while (pos < text.size()) {
        size_t e = text.find('\n', pos); if (e == std::string::npos) e = text.size();
        std::string line = text.substr(pos, e - pos); pos = e + 1;
        std::vector<std::string> f; size_t p = 0;
        while (true) { size_t t = line.find('\t', p); if (t == std::string::npos) { f.push_back(line.substr(p)); break; } f.push_back(line.substr(p, t - p)); p = t + 1; }
        if (f[0] == "ERR" && f.size() > 1) r.error = f[1];
        else if (f[0] == "ARCH" && f.size() > 1 && !f[1].empty()) r.archs = f[1];
        else if (f[0] == "PLUG" && f.size() >= 9) {
            PluginInfo pi; pi.format = "vst3"; pi.path = bundle; pi.uid = f[1]; pi.name = f[2]; pi.vendor = f[3]; pi.version = f[4]; pi.categories = f[5]; pi.sdk = f[6];
            pi.isInstrument = f[7] == "1"; pi.isEffect = f[8] == "1"; r.plugins.push_back(pi);
        } else if (f[0] == "END") ended = true;
    }
    if (WIFSIGNALED(status)) {
        int sig = WTERMSIG(status);
        if (sig == SIGALRM) { r.timedOut = true; r.error = "took longer than " + std::to_string(timeoutSeconds) + " seconds to load"; }
        else { r.crashed = true; r.error = "crashed while loading (signal " + std::to_string(sig) + ")"; }
        r.plugins.clear();
    } else if (WIFEXITED(status) && WEXITSTATUS(status) == 127) r.error = "the scanner could not be started";
    else if (ended && r.error.empty()) r.ok = true;
    else if (r.error.empty()) r.error = "the scanner gave no answer";
    return r;
}

std::string scanResultJson(const ScanResult& r) {
    std::string s = "{\"path\":" + jstr(r.path) + ",\"archs\":" + jstr(r.archs) + ",\"ok\":" + (r.ok ? "true" : "false") + ",\"crashed\":" + (r.crashed ? "true" : "false") +
                    ",\"timedOut\":" + (r.timedOut ? "true" : "false") + ",\"wrongArch\":" + (r.wrongArch ? "true" : "false") + ",\"error\":" + jstr(r.error) + ",\"seconds\":" + jnum(r.seconds) + ",\"plugins\":[";
    for (size_t i = 0; i < r.plugins.size(); i++) {
        auto& p = r.plugins[i];
        s += std::string(i ? "," : "") + "{\"name\":" + jstr(p.name) + ",\"vendor\":" + jstr(p.vendor) + ",\"version\":" + jstr(p.version) + ",\"uid\":" + jstr(p.uid) + ",\"categories\":" + jstr(p.categories) +
             ",\"instrument\":" + (p.isInstrument ? "true" : "false") + ",\"effect\":" + (p.isEffect ? "true" : "false") + "}";
    }
    return s + "]}";
}

}  // namespace al
