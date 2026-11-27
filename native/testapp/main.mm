// AudioLab VST3 test (task NM1, test C). A small native Mac app, not the DAW:
// it lists the VST3 plug-ins found on this Mac (each bundle is scanned in a separate process), loads one,
// opens the plug-in's own window, plays notes from the computer keyboard or a test pattern through the
// chosen output device (Core Audio, straight on the device), and writes a report file.
// 0.4 (task NL4): a search over the list (name, maker, kind; Cmd+F, Escape), sort and group by maker, a kind
// filter, recently loaded plug-ins on top; parameter moves from a plug-in's own window counted and logged per
// plug-in; notes sent to each instrument logged; a warning when the output runs at 16 kHz or less (Bluetooth call mode).
// 0.5 (task NL5): the host gives the controller the processor's state and delivers messages between the two from any
// thread (0.4 skipped the first and dropped the second, as the SDK's PlugProvider does); buses set up in the validator's
// order; [diag] lines per plug-in; a silence probe in a child process; factory presets; a [device] line for devices
// plugged in later; the Intel-only and broken bundles listed at the end; CLAP and Audio Unit folders listed (not loaded);
// the report in plain ASCII.
// 0.7 (task NL7): a [warning] and a red over-mark on the meter when a plug-in's own output passes 0 dBFS, and a safety
// limiter on the app's output only; the slowest blocks tied to what happened in the 100 ms before them (a lock-free ring
// of events); every string from a plug-in cleaned like the app's own text (0.5 decoded them as Mac Roman: "17.1\u201a\u00c4\u00d8ms");
// the DAC's bit depth with a warning and a menu item "Use the deepest format"; a device that appears without a name waits
// up to 2 s; [param] lines for values that change without the host being told; the report without empty lines.
#import <Cocoa/Cocoa.h>
#include "../common/coreaudio.h"
#include "../host/plugin_api.h"
#include "../host/live_tools.h"
#include <algorithm>
#include <atomic>
#include <cmath>
#include <cstdarg>
#include <mutex>
#include <set>
#include <string>
#include <map>
#include <unordered_map>
#include <sys/sysctl.h>
#include <time.h>
#include <vector>

using namespace al;

static const char* kVersion = "0.7";
static NSString* S(const std::string& s) { return [NSString stringWithUTF8String:s.c_str()] ?: @""; }
static std::string U(NSString* s) { return s ? std::string([s UTF8String]) : std::string(); }
// Formatting for the report: printf into UTF-8 bytes. 0.5 used [NSString stringWithFormat:] whose %s reads a C string
// as Mac Roman, so a plug-in's U+202F (bytes E2 80 AF) came out as three letters; here the bytes stay UTF-8.
static std::string fmt(const char* f, ...) __attribute__((format(printf, 1, 2)));
static std::string fmt(const char* f, ...) {
    va_list a, b; va_start(a, f); va_copy(b, a);
    int n = vsnprintf(nullptr, 0, f, a); va_end(a);
    std::string s(n > 0 ? (size_t)n : 0, '\0');
    if (n > 0) vsnprintf(&s[0], (size_t)n + 1, f, b);
    va_end(b);
    return s;
}
#define NSF(...) S(asciiClean(fmt(__VA_ARGS__)))
// The report in plain ASCII where it can be: narrow and no-break spaces become spaces, the minus sign and dashes a
// hyphen-minus, and so on (one table, asciiClean in native/host/live_tools.h, also used for every plug-in string);
// what is left (accented names) is written with a UTF-8 byte order mark, so it reads right wherever it is opened.
static NSString* asciiish(NSString* src) { return S(asciiClean(U(src))); }

// ---- the audio side ---------------------------------------------------------------------------------
struct Engine {
    std::mutex lock;                      // the audio thread only tries it; if busy it plays silence
    std::unique_ptr<PluginInstance> plug;
    bool instrument = true, ready = false;
    double sr = 48000;
    int maxBlock = 4096;
    std::atomic<bool> pattern{false};
    std::atomic<uint32_t> noteW{0}, noteR{0};
    struct KN { int pitch; bool on; } notes[256];
    int64_t pos = 0;
    int patStep = -1, patNote = -1;
    double srcPhase = 0, srcEnv = 0; int srcStep = -1;
    std::vector<float> in[2];
    // figures for the report
    std::atomic<uint64_t> blocks{0}, sumNs{0}, worstNs{0}, budgetNs{0}, failed{0};
    std::atomic<float> peak{0};
    std::atomic<uint32_t> notesPattern{0}, notesKeys{0}, fedBlocks{0};
    bool silentChecked = false;   // note-ons that reached the plug-in; blocks of test sound fed to an effect
    // 0.7: the plug-in's own output past 0 dBFS (before the app's half level), the app's safety limiter, the meter,
    // and the slowest blocks with their start times (for the events before them)
    std::atomic<uint64_t> overBlocks{0}, overFirstT{0}, overLastT{0};
    std::atomic<float> overPeak{0}, meterPeak{0}, ownPeak{0};
    SafetyLimiter lim;
    SlowBlocks slow;
    void pushNote(int pitch, bool on) { uint32_t w = noteW.load(); notes[w & 255] = {pitch, on}; noteW.store(w + 1); }
};
static Engine G;
static EventRing gEvents;      // what happened in the window and the plug-in, written without locks (live_tools.h)

static void renderCb(void*, float** out, int, int frames) {
    memset(out[0], 0, sizeof(float) * frames); memset(out[1], 0, sizeof(float) * frames);
    if (!G.lock.try_lock()) return;
    if (G.plug && G.ready && frames <= G.maxBlock) {
        NoteEvent ev[64]; int n = 0;
        uint32_t r = G.noteR.load(), w = G.noteW.load();
        while (r != w && n < 60) { ev[n].offset = 0; ev[n].on = G.notes[r & 255].on; ev[n].pitch = G.notes[r & 255].pitch; ev[n].velocity = 0.8f; ev[n].channel = 0; if (ev[n].on) G.notesKeys.fetch_add(1, std::memory_order_relaxed); n++; r++; }
        G.noteR.store(r);
        bool pat = G.pattern.load();
        const int seq[8] = {48, 60, 55, 63, 67, 60, 72, 63};
        size_t stepLen = (size_t)(G.sr * 0.25);
        if ((int)G.in[0].size() < frames) { G.in[0].assign(frames, 0); G.in[1].assign(frames, 0); }
        for (int i = 0; i < frames; i++) {
            int64_t s = G.pos + i;
            float x = 0;
            if (pat) {
                int step = (int)(s / stepLen);
                if (G.instrument) {
                    if (step != G.patStep && n < 62) {
                        if (G.patNote >= 0) { ev[n].offset = i; ev[n].on = false; ev[n].pitch = G.patNote; ev[n].channel = 0; ev[n].velocity = 0; n++; }
                        G.patNote = seq[step & 7]; G.patStep = step;
                        ev[n].offset = i; ev[n].on = true; ev[n].pitch = G.patNote; ev[n].channel = 0; ev[n].velocity = 0.8f; n++;
                        G.notesPattern.fetch_add(1, std::memory_order_relaxed);
                    }
                } else {
                    // for an effect: a plucked saw line as the sound to run through it
                    if (step != G.srcStep) { G.srcStep = step; G.srcEnv = 1; }
                    double f = 440.0 * std::pow(2.0, (seq[step & 7] - 69) / 12.0);
                    G.srcPhase += f / G.sr; if (G.srcPhase >= 1) G.srcPhase -= 1;
                    G.srcEnv *= std::exp(-1.0 / (0.12 * G.sr));
                    x = (float)((G.srcPhase * 2 - 1) * G.srcEnv * 0.4);
                }
            } else if (G.patNote >= 0 && n < 62) { ev[n].offset = i; ev[n].on = false; ev[n].pitch = G.patNote; ev[n].channel = 0; ev[n].velocity = 0; n++; G.patNote = -1; G.patStep = -1; }
            G.in[0][i] = x; G.in[1][i] = x;
        }
        if (pat && !G.instrument) G.fedBlocks.fetch_add(1, std::memory_order_relaxed);
        const float* inp[2] = {G.in[0].data(), G.in[1].data()};
        ProcessContext c; c.sampleRate = G.sr; c.tempo = 120; c.samplePos = G.pos; c.playing = true;
        uint64_t t0 = nowNs();                                      // the same clock as the event ring; no lock, no system call
        bool ok = G.plug->process(inp, 2, out, 2, frames, ev, n, c);
        uint64_t ns = nowNs() - t0;
        G.blocks++; G.sumNs += ns; if (ns > G.worstNs) G.worstNs = ns;
        G.slow.offer(t0, ns);
        G.budgetNs = (uint64_t)(frames / G.sr * 1e9);
        if (!ok) G.failed++;
        // the plug-in's own output, before this app touches it: past 0 dBFS?
        float own = 0;
        for (int ch = 0; ch < 2; ch++) for (int i = 0; i < frames; i++) { float a = std::fabs(out[ch][i]); if (a > own) own = a; }
        if (own > G.ownPeak.load(std::memory_order_relaxed)) G.ownPeak.store(own, std::memory_order_relaxed);
        if (own > 1.0f) {
            G.overBlocks.fetch_add(1, std::memory_order_relaxed);
            if (own > G.overPeak.load(std::memory_order_relaxed)) G.overPeak.store(own, std::memory_order_relaxed);
            if (!G.overFirstT.load(std::memory_order_relaxed)) G.overFirstT.store(t0, std::memory_order_relaxed);
            G.overLastT.store(t0, std::memory_order_relaxed);
        }
        // half level (this is a test of unknown plug-ins), then the safety limiter: the app's output never passes full scale
        for (int ch = 0; ch < 2; ch++) for (int i = 0; i < frames; i++) out[ch][i] *= 0.5f;
        float bpk = G.lim.process(out, 2, frames);
        if (bpk > G.peak.load(std::memory_order_relaxed)) G.peak.store(bpk, std::memory_order_relaxed);
        if (bpk > G.meterPeak.load(std::memory_order_relaxed)) G.meterPeak.store(bpk, std::memory_order_relaxed);
        G.pos += frames;
    }
    G.lock.unlock();
}

// ---- the window --------------------------------------------------------------------------------------
struct Row { std::string name, vendor, kind, status, path, uid, archs; bool ok = false, instrument = false; };
// what the table shows: a plug-in (idx into _rows) or a group heading (idx -1)
struct ViewRow { int idx = -1; std::string heading; };
static NSString* fold(NSString* s) { return [s stringByFoldingWithOptions:NSCaseInsensitiveSearch | NSDiacriticInsensitiveSearch locale:nil] ?: @""; }

// The app's output meter (after the safety limiter), with a red OVER mark when the plug-in's own output passed 0 dBFS.
// The mark stays until it is clicked.
@interface ALMeter : NSView
@property double level;
@property BOOL over;
@property (copy) void (^onClick)(void);
@end
@implementation ALMeter
- (void)drawRect:(NSRect)dirty {
    NSRect b = self.bounds;
    [[NSColor colorWithWhite:0.16 alpha:1] setFill]; NSRectFill(b);
    CGFloat ow = 40;
    NSRect bar = NSMakeRect(1, 2, b.size.width - ow - 4, b.size.height - 4);
    double db = self.level > 0 ? 20 * std::log10(self.level) : -120;
    double f = std::max(0.0, std::min(1.0, (db + 60) / 60));
    [(db > -1 ? NSColor.systemOrangeColor : NSColor.systemGreenColor) setFill];
    NSRectFill(NSMakeRect(bar.origin.x, bar.origin.y, bar.size.width * f, bar.size.height));
    NSRect ov = NSMakeRect(b.size.width - ow - 1, 1, ow, b.size.height - 2);
    [(self.over ? NSColor.systemRedColor : [NSColor colorWithWhite:0.32 alpha:1]) setFill]; NSRectFill(ov);
    NSDictionary* at = @{NSFontAttributeName: [NSFont systemFontOfSize:9 weight:NSFontWeightBold], NSForegroundColorAttributeName: self.over ? NSColor.whiteColor : [NSColor colorWithWhite:0.62 alpha:1]};
    NSString* t = @"OVER"; NSSize ts = [t sizeWithAttributes:at];
    [t drawAtPoint:NSMakePoint(NSMidX(ov) - ts.width / 2, NSMidY(ov) - ts.height / 2) withAttributes:at];
}
- (void)mouseDown:(NSEvent*)e { if (self.onClick) self.onClick(); }
@end

@interface App : NSObject <NSApplicationDelegate, NSTableViewDataSource, NSTableViewDelegate, NSWindowDelegate, NSSearchFieldDelegate>
- (void)outside:(NSString*)what;
@end
static __weak App* gApp;
// something changed outside the app (a device was plugged in, the volume was turned, the rate was switched)
static void watchCb(void*, const char* what, uint32_t) {
    NSString* w = [NSString stringWithUTF8String:what];
    dispatch_async(dispatch_get_main_queue(), ^{ [gApp outside:w]; });
}

@implementation App {
    NSWindow* _win; NSWindow* _plugWin;
    NSTableView* _table; NSPopUpButton* _devPop; NSPopUpButton* _bufPop;
    NSTextView* _log; NSTextField* _status; NSTextField* _cpu;
    NSButton* _loadBtn; NSButton* _openBtn; NSButton* _patBtn; NSButton* _scanBtn;
    std::vector<Row> _rows;
    std::vector<DeviceInfo> _devs;
    OutputStream _stream;
    uint32_t _dev;
    std::string _report, _loaded, _selfOut, _selfName;
    std::vector<ScanResult> _scan;
    NSPopUpButton* _ratePop; NSButton* _exclBtn; NSSlider* _vol; NSTextField* _volLbl;
    Watcher _watch; BOOL _hog;
    NSMutableSet* _down;
    BOOL _selftest;
    int _bundles, _bundlesOk;
    // 0.4: the list's search, sort, kind filter and recently loaded
    NSSearchField* _search; NSPopUpButton* _sortPop; NSPopUpButton* _kindPop; NSTextField* _countLbl;
    std::vector<ViewRow> _view;
    NSMutableArray<NSString*>* _recent;
    // 0.4: the output warning, and what the loaded plug-in did
    NSTextField* _warn; std::string _warnText;
    std::unordered_map<uint32_t, std::string> _paramNames;
    int _plugMouse, _plugDrags, _lastMoves; BOOL _windowOpened, _firstMoveLogged;
    // 0.5
    NSMutableSet* _seenDevs;
    NSPopUpButton* _presetPop; NSButton* _probeBtn; NSButton* _diagBtn;
    std::vector<PresetInfo> _presets;
    PluginInfo _loadedInfo; size_t _loadStateBytes; BOOL _probing, _probedThis;
    std::string _selfProbe;
    // 0.7
    ALMeter* _meter; double _meterShown; uint64_t _overSeen; BOOL _overWarned;
    double _wall0; uint64_t _up0;                          // wall clock and nowNs() at the start, to print times
    ParamWatch _pw; uint64_t _lastValueRestarts; int _polls; double _pollWorstMs, _pollSumMs;
    BOOL _latencyNoted; int _paramLiveLines;
    NSMutableSet* _pendingDevs; NSMutableSet* _formatLogged;
    std::map<uint32_t, std::string> _devNames;
    std::vector<std::string> _selfSets;                    // --set-param "name=value" (the build machine)
    BOOL _selfDeepest;
}

- (void)say:(NSString*)line {
    line = asciiish(line);
    _report += U(line) + "\n";
    NSAttributedString* a = [[NSAttributedString alloc] initWithString:[line stringByAppendingString:@"\n"] attributes:@{NSFontAttributeName: [NSFont monospacedSystemFontOfSize:11 weight:NSFontWeightRegular], NSForegroundColorAttributeName: NSColor.textColor}];
    [_log.textStorage appendAttributedString:a];
    [_log scrollRangeToVisible:NSMakeRange(_log.string.length, 0)];
    [self writeReport];
}
- (NSString*)reportPath {
    if (!_selfOut.empty()) return [S(_selfOut) stringByAppendingPathComponent:@"AudioLab-VST3-test-report.txt"];
    return [[NSHomeDirectory() stringByAppendingPathComponent:@"Desktop"] stringByAppendingPathComponent:@"AudioLab-VST3-test-report.txt"];
}
- (void)writeReport {
    NSString* full = asciiish([S(_report) stringByAppendingString:[self liveFigures]]);
    NSMutableData* d = [NSMutableData data];
    if (![full canBeConvertedToEncoding:NSASCIIStringEncoding]) { const unsigned char bom[3] = {0xEF, 0xBB, 0xBF}; [d appendBytes:bom length:3]; }   // UTF-8, said so at the start
    [d appendData:[full dataUsingEncoding:NSUTF8StringEncoding]];
    [d writeToFile:[self reportPath] atomically:YES];
}
- (NSString*)liveFigures {
    NSString* a = [self audioFigures];
    NSString* p = [self plugSummary];
    NSString* lists = [self bundleLists];
    return [NSString stringWithFormat:@"%@%@%@", a, p.length ? [p stringByAppendingString:@"\n"] : @"", lists];   // each part ends with one newline: no empty lines
}
// At the end of every report: the bundles this app cannot load, in a plain list.
- (NSString*)bundleLists {
    if (_scan.empty()) return @"";
    std::string intel, broken; int ni = 0, nb = 0;
    for (auto& r : _scan) {
        if (r.ok) continue;
        std::string file = r.path.substr(r.path.find_last_of('/') + 1);
        if (r.wrongArch) { intel += "\n  " + file + "  (" + r.path + ")"; ni++; }
        else { broken += "\n  " + file + ": " + r.error + "  (" + r.path + ")"; nb++; }
    }
    NSMutableString* o = [NSMutableString string];
    if (ni) [o appendString:NSF("[rosetta] %d bundle(s) are built for Intel (x86_64) only. These need Rosetta: a helper comes later. Until then they cannot load here:%s\n", ni, intel.c_str())];
    if (nb) [o appendString:NSF("[broken] %d bundle(s) could not be read at all (damaged, or not a plug-in):%s\n", nb, broken.c_str())];
    return o;
}
- (NSString*)audioFigures {
    uint64_t b = G.blocks.load();
    if (!b) return @"[audio] no audio block has run through a plug-in yet\n";
    double avg = G.sumNs.load() / 1000.0 / b, worst = G.worstNs.load() / 1000.0, budget = G.budgetNs.load() / 1000.0;
    NSString* line = NSF("[audio] plug-in %s: %llu blocks, average %.1f microseconds per block (%.2f %% of the block), worst %.1f (%.1f %%), block lasts %.0f microseconds, failed blocks %llu, overloads reported by the device %llu, device callbacks %llu, frames per callback %u to %u, peak level %.3f\n",
            _loaded.c_str(), b, avg, budget ? avg / budget * 100 : 0, worst, budget ? worst / budget * 100 : 0, budget, G.failed.load(), _stream.overloads.load(), _stream.callbacks.load(),
            _stream.callbacks.load() ? _stream.minFrames.load() : 0, _stream.maxFrames.load(), G.peak.load());
    return [line stringByAppendingString:[self slowText]];
}
// 0.7: when the slowest blocks happened, and what happened in the window, the plug-in's controls or the devices in the
// 100 ms before each one (and during it). Report 7: worst 5.4 ms of 11.6 ms while the plug-in windows were in use.
- (std::string)clockText:(uint64_t)t {
    double secs = _wall0 + ((double)t - (double)_up0) / 1e9;
    time_t whole = (time_t)secs; struct tm tmv; localtime_r(&whole, &tmv);
    return fmt("%02d:%02d:%02d.%03d", tmv.tm_hour, tmv.tm_min, tmv.tm_sec, (int)((secs - (double)whole) * 1000));
}
- (std::string)eventText:(const EventRing::Ev&)e {
    auto pname = [&](uint32_t id) { auto it = _paramNames.find(id); return it != _paramNames.end() ? it->second : "parameter " + std::to_string(id); };
    switch (e.kind) {
        case evWindowOpened: return "the plug-in's window opened";
        case evWindowClosed: return "the plug-in's window closed";
        case evPresetLoaded: return "a factory preset or program was loaded by the host";
        case evRestart: {
            static const char* names[] = {"reload", "buses changed", "all values changed (a preset)", "latency changed", "parameter titles changed", "MIDI assignments changed", "note expression changed", "bus titles changed", "prefetch support changed", "routing changed", "key switches changed", "parameter ids changed"};
            std::string f; for (int i = 0; i < 12; i++) if (e.arg & (1u << i)) f += (f.empty() ? "" : ", ") + std::string(names[i]);
            return "the plug-in asked the host to restart (" + (f.empty() ? fmt("flags %u", e.arg) : f) + ")";
        }
        case evStateSet: return "the host set the plug-in's state";
        case evGestureBegin: return "a gesture began on " + pname(e.arg);
        case evGestureEnd: return "a gesture ended on " + pname(e.arg);
        case evDeviceSwitch: { auto it = _devNames.find(e.arg); return "the output device was opened" + (it != _devNames.end() ? ": " + it->second : std::string()); }
        case evPluginLoaded: return "a plug-in was loaded";
        case evPatternOn: return "the test pattern started";
        case evPatternOff: return "the test pattern stopped";
        case evMouseInWindow: return "a click in the plug-in's window";
        case evFormatChanged: return "the device's format was changed";
        case evRateChanged: return "the device's rate was changed";
        case evBufferChanged: return "the device's buffer was changed";
        case evProbe: return "the silence probe started a child process";
        default: return fmt("event %u", e.kind);
    }
}
- (NSString*)slowText {
    auto v = G.slow.get();
    if (v.empty()) return @"";
    double budget = G.budgetNs.load() / 1000.0;
    std::string o = "[audio] the slowest blocks (at least 100 ms apart) and what happened in the 100 ms before each, and during it:\n";
    for (size_t i = 0; i < v.size(); i++) {
        double us = v[i].ns / 1000.0;
        o += fmt("[audio]   %zu) %.1f microseconds (%.1f %% of the block) at %s: ", i + 1, us, budget ? us / budget * 100 : 0, [self clockText:v[i].start].c_str());
        bool back = true;
        auto evs = gEvents.between(v[i].start > 100000000ull ? v[i].start - 100000000ull : 0, v[i].start + v[i].ns, &back);
        if (evs.empty()) o += back ? "nothing happened in the window, the plug-in's controls or the devices (the plug-in's own work, or the system)" : "the event list no longer reaches back that far";
        else {
            // newest first; the same thing several times is said once with a count
            std::vector<std::pair<std::string, int>> said; std::vector<double> whenMs;
            for (auto it = evs.rbegin(); it != evs.rend(); ++it) {
                std::string t = [self eventText:*it];
                bool dup = false; for (auto& x : said) if (x.first == t) { x.second++; dup = true; }
                if (!dup && said.size() < 6) { said.push_back({t, 1}); whenMs.push_back(it->t >= v[i].start ? -1 : (v[i].start - it->t) / 1e6); }
            }
            for (size_t k = 0; k < said.size(); k++)
                o += (k ? "; " : "") + said[k].first + (said[k].second > 1 ? fmt(" (%d times, the latest ", said[k].second) : std::string(" (")) +
                     (whenMs[k] < 0 ? std::string("during the block)") : fmt("%.0f ms before)", whenMs[k]));
        }
        o += "\n";
    }
    return S(asciiClean(o));
}

- (NSButton*)button:(NSString*)t action:(SEL)a frame:(NSRect)f {
    NSButton* b = [NSButton buttonWithTitle:t target:self action:a]; b.frame = f; [_win.contentView addSubview:b]; return b;
}
- (NSTextField*)label:(NSString*)t frame:(NSRect)f {
    NSTextField* l = [NSTextField labelWithString:t]; l.frame = f; l.lineBreakMode = NSLineBreakByTruncatingTail; [_win.contentView addSubview:l]; return l;
}

- (void)applicationDidFinishLaunching:(NSNotification*)n {
    NSArray<NSString*>* args = NSProcessInfo.processInfo.arguments;
    for (NSUInteger i = 1; i < args.count; i++) {
        if ([args[i] isEqualToString:@"--selftest"] && i + 1 < args.count) { _selftest = YES; _selfOut = U(args[i + 1]); }
        if ([args[i] isEqualToString:@"--plugin-name"] && i + 1 < args.count) _selfName = U(args[i + 1]);
        if ([args[i] isEqualToString:@"--probe"]) _selfProbe = "1";
        if ([args[i] isEqualToString:@"--set-param"] && i + 1 < args.count) _selfSets.push_back(U(args[i + 1]));   // "name=value", after loading
        if ([args[i] isEqualToString:@"--deepest"]) _selfDeepest = YES;                                              // try "Use the deepest format"
    }
    _wall0 = [NSDate date].timeIntervalSince1970; _up0 = nowNs();
    _pendingDevs = [NSMutableSet set]; _formatLogged = [NSMutableSet set];
    _down = [NSMutableSet set];
    // menu with Quit
    NSMenu* bar = [NSMenu new]; NSMenuItem* appItem = [NSMenuItem new]; [bar addItem:appItem];
    NSMenu* appMenu = [NSMenu new]; [appMenu addItemWithTitle:@"Quit AudioLab VST3 test" action:@selector(terminate:) keyEquivalent:@"q"]; appItem.submenu = appMenu; NSApp.mainMenu = bar;
    // Edit menu, so copy, paste and select all work in the search field
    NSMenuItem* editItem = [NSMenuItem new]; [bar addItem:editItem];
    NSMenu* edit = [[NSMenu alloc] initWithTitle:@"Edit"];
    [edit addItemWithTitle:@"Cut" action:@selector(cut:) keyEquivalent:@"x"]; [edit addItemWithTitle:@"Copy" action:@selector(copy:) keyEquivalent:@"c"];
    [edit addItemWithTitle:@"Paste" action:@selector(paste:) keyEquivalent:@"v"]; [edit addItemWithTitle:@"Select All" action:@selector(selectAll:) keyEquivalent:@"a"];
    [edit addItem:NSMenuItem.separatorItem]; [edit addItemWithTitle:@"Find Plug-in" action:@selector(focusSearch:) keyEquivalent:@"f"];
    editItem.submenu = edit;
    // 0.7: the Device menu
    NSMenuItem* devItem = [NSMenuItem new]; [bar addItem:devItem];
    NSMenu* devMenu = [[NSMenu alloc] initWithTitle:@"Device"];
    [devMenu addItemWithTitle:@"Use the deepest format" action:@selector(useDeepestFormat:) keyEquivalent:@""];
    devItem.submenu = devMenu;

    const CGFloat W = 980, H = 700;
    _win = [[NSWindow alloc] initWithContentRect:NSMakeRect(0, 0, W, H) styleMask:NSWindowStyleMaskTitled | NSWindowStyleMaskClosable | NSWindowStyleMaskMiniaturizable backing:NSBackingStoreBuffered defer:NO];
    _win.title = @"AudioLab VST3 test"; _win.delegate = self; [_win center];
    [self label:@"Output" frame:NSMakeRect(16, H - 40, 50, 20)];
    _devPop = [[NSPopUpButton alloc] initWithFrame:NSMakeRect(66, H - 44, 330, 26) pullsDown:NO]; _devPop.target = self; _devPop.action = @selector(deviceChanged:); [_win.contentView addSubview:_devPop];
    [self label:@"Buffer" frame:NSMakeRect(410, H - 40, 46, 20)];
    _bufPop = [[NSPopUpButton alloc] initWithFrame:NSMakeRect(456, H - 44, 100, 26) pullsDown:NO]; _bufPop.target = self; _bufPop.action = @selector(bufferChanged:); [_win.contentView addSubview:_bufPop];
    for (NSString* b in @[@"32", @"64", @"128", @"256", @"512", @"1024"]) [_bufPop addItemWithTitle:b];
    _scanBtn = [self button:@"Scan again" action:@selector(scan:) frame:NSMakeRect(W - 130, H - 46, 114, 30)];
    _status = [self label:@"Starting" frame:NSMakeRect(570, H - 40, W - 710, 20)];

    [self label:@"Rate" frame:NSMakeRect(16, H - 74, 50, 20)];
    _ratePop = [[NSPopUpButton alloc] initWithFrame:NSMakeRect(66, H - 78, 130, 26) pullsDown:NO]; _ratePop.target = self; _ratePop.action = @selector(rateChanged:); [_win.contentView addSubview:_ratePop];
    _exclBtn = [NSButton checkboxWithTitle:@"Exclusive use of the device" target:self action:@selector(exclChanged:)]; _exclBtn.frame = NSMakeRect(214, H - 76, 210, 22); [_win.contentView addSubview:_exclBtn];
    [self label:@"Device volume" frame:NSMakeRect(440, H - 74, 96, 20)];
    _vol = [NSSlider sliderWithValue:1 minValue:0 maxValue:1 target:self action:@selector(volChanged:)]; _vol.frame = NSMakeRect(536, H - 76, 220, 22); _vol.continuous = YES; [_win.contentView addSubview:_vol];
    _volLbl = [self label:@"" frame:NSMakeRect(764, H - 74, W - 780, 20)];
    _warn = [self label:@"" frame:NSMakeRect(16, H - 104, W - 32, 20)];
    _warn.font = [NSFont systemFontOfSize:12 weight:NSFontWeightSemibold];
    // the list's search row
    _search = [[NSSearchField alloc] initWithFrame:NSMakeRect(16, H - 140, 360, 26)];
    _search.placeholderString = @"Search name, maker, instrument or effect  (\u2318F)";
    _search.target = self; _search.action = @selector(searchChanged:); _search.delegate = self;
    _search.sendsSearchStringImmediately = YES; _search.sendsWholeSearchString = NO;
    [_win.contentView addSubview:_search];
    _kindPop = [[NSPopUpButton alloc] initWithFrame:NSMakeRect(388, H - 141, 140, 26) pullsDown:NO]; _kindPop.target = self; _kindPop.action = @selector(searchChanged:);
    [_kindPop addItemsWithTitles:@[@"All kinds", @"Instruments", @"Effects", @"Cannot load"]]; [_win.contentView addSubview:_kindPop];
    _sortPop = [[NSPopUpButton alloc] initWithFrame:NSMakeRect(536, H - 141, 170, 26) pullsDown:NO]; _sortPop.target = self; _sortPop.action = @selector(searchChanged:);
    [_sortPop addItemsWithTitles:@[@"Sort by name", @"Sort by maker", @"Group by maker"]]; [_win.contentView addSubview:_sortPop];
    _countLbl = [self label:@"" frame:NSMakeRect(716, H - 136, W - 732, 20)];
    _countLbl.font = [NSFont monospacedDigitSystemFontOfSize:12 weight:NSFontWeightRegular];
    @try { NSArray* r = [NSUserDefaults.standardUserDefaults arrayForKey:@"recentPlugins"]; _recent = r ? [r mutableCopy] : [NSMutableArray array]; } @catch (NSException* e) { _recent = [NSMutableArray array]; }
    NSScrollView* sv = [[NSScrollView alloc] initWithFrame:NSMakeRect(16, 250, W - 32, H - 400)]; sv.hasVerticalScroller = YES; sv.borderType = NSBezelBorder;
    _table = [[NSTableView alloc] initWithFrame:sv.bounds]; _table.dataSource = self; _table.delegate = self; _table.usesAlternatingRowBackgroundColors = YES; _table.doubleAction = @selector(load:); _table.target = self;
    for (NSArray* c in @[@[@"name", @"Plug-in", @270], @[@"vendor", @"Maker", @170], @[@"kind", @"Kind", @90], @[@"status", @"Found / problem", @380]]) {
        NSTableColumn* col = [[NSTableColumn alloc] initWithIdentifier:c[0]]; col.title = c[1]; col.width = [c[2] doubleValue]; col.editable = NO; [_table addTableColumn:col];
    }
    sv.documentView = _table; [_win.contentView addSubview:sv];

    _loadBtn = [self button:@"Load" action:@selector(load:) frame:NSMakeRect(16, 208, 90, 30)];
    _openBtn = [self button:@"Open its window" action:@selector(openEditor:) frame:NSMakeRect(110, 208, 140, 30)];
    _patBtn = [self button:@"Play test pattern" action:@selector(togglePattern:) frame:NSMakeRect(254, 208, 150, 30)];
    _presetPop = [[NSPopUpButton alloc] initWithFrame:NSMakeRect(410, 210, 150, 26) pullsDown:NO]; _presetPop.target = self; _presetPop.action = @selector(presetChosen:);
    [_presetPop addItemWithTitle:@"Factory preset"]; _presetPop.enabled = NO; _presetPop.toolTip = @"The plug-in's own programs and .vstpreset files, when it offers any through VST3. Most synths keep their presets in their own window: choose one there.";
    [_win.contentView addSubview:_presetPop];
    _probeBtn = [self button:@"Why silent?" action:@selector(probe:) frame:NSMakeRect(564, 208, 112, 30)];
    _probeBtn.toolTip = @"Loads the plug-in again in a separate process and plays it under the 0.5 host, the 0.4 host and one change at a time; writes [probe] lines into the report.";
    [self button:@"Show report file" action:@selector(showReport:) frame:NSMakeRect(W - 300, 208, 140, 30)];
    [self button:@"Copy report" action:@selector(copyReport:) frame:NSMakeRect(W - 156, 208, 140, 30)];
    [self label:@"Keys A W S E D F T G Y H U J K play notes, C to C (click the list first, not the search field). Sound comes out at half level." frame:NSMakeRect(16, 184, W - 260, 18)];
    _diagBtn = [NSButton checkboxWithTitle:@"Diagnostic lines in the report" target:nil action:nil]; _diagBtn.frame = NSMakeRect(W - 236, 182, 220, 22); _diagBtn.state = NSControlStateValueOn; [_win.contentView addSubview:_diagBtn];
    _cpu = [self label:@"" frame:NSMakeRect(16, 162, W - 32 - 236, 18)];
    _cpu.font = [NSFont monospacedDigitSystemFontOfSize:12 weight:NSFontWeightRegular];
    [self label:@"Output" frame:NSMakeRect(W - 236, 162, 46, 18)];
    _meter = [[ALMeter alloc] initWithFrame:NSMakeRect(W - 188, 162, 172, 16)];
    _meter.toolTip = @"The app's output after its safety limiter. OVER turns red when the plug-in's own output passed 0 dBFS; click to clear it.";
    [_win.contentView addSubview:_meter];

    NSScrollView* lv = [[NSScrollView alloc] initWithFrame:NSMakeRect(16, 16, W - 32, 138)]; lv.hasVerticalScroller = YES; lv.borderType = NSBezelBorder;
    _log = [[NSTextView alloc] initWithFrame:lv.bounds]; _log.editable = NO; _log.autoresizingMask = NSViewWidthSizable; lv.documentView = _log; [_win.contentView addSubview:lv];
    [_win makeKeyAndOrderFront:nil];
    [NSApp activateIgnoringOtherApps:YES];

    __weak App* me = self;
    [NSEvent addLocalMonitorForEventsMatchingMask:NSEventMaskKeyDown | NSEventMaskKeyUp handler:^NSEvent*(NSEvent* e) { return [me key:e] ? nil : e; }];
    // the mouse in the plug-in's own window: counted, so the report can say "knobs were touched but no move reached the host"
    [NSEvent addLocalMonitorForEventsMatchingMask:NSEventMaskLeftMouseDown | NSEventMaskRightMouseDown | NSEventMaskLeftMouseDragged | NSEventMaskScrollWheel handler:^NSEvent*(NSEvent* e) { [me plugMouse:e]; return e; }];
    [NSTimer scheduledTimerWithTimeInterval:0.25 repeats:YES block:^(NSTimer* t) { [me tick]; }];
    [NSTimer scheduledTimerWithTimeInterval:1.0 / 30 repeats:YES block:^(NSTimer* t) { [me meterTick]; }];
    [NSTimer scheduledTimerWithTimeInterval:0.2 repeats:YES block:^(NSTimer* t) { [me pollParams]; }];
    _meter.onClick = ^{ [me clearOver]; };

    gApp = self;
    _watch.start(watchCb, nullptr);
    [self machineInfo];
    [self loadDevices];
    [self scan:nil];
}

- (void)machineInfo {
    char model[128] = {0}, cpu[128] = {0}; size_t l = sizeof model; sysctlbyname("hw.model", model, &l, nullptr, 0); l = sizeof cpu; sysctlbyname("machdep.cpu.brand_string", cpu, &l, nullptr, 0);
    [self say:NSF("AudioLab VST3 test %s (tasks NM1, NB-N1, NL4, NL5 and NL7). Report file: paste all of it back.", kVersion)];
    [self say:NSF("[machine] %s, %s, macOS %s, this app runs as %s", model, cpu, U(NSProcessInfo.processInfo.operatingSystemVersionString).c_str(), hostArch().c_str())];
}

- (void)loadDevices {
    _devs.clear(); [_devPop removeAllItems];
    uint32_t def = defaultOutputDevice(); int sel = -1;
    for (auto& d : listDevices()) {
        [self deviceLine:d later:NO];
        if (d.outChannels < 1) continue;
        if (d.id == def) sel = (int)_devs.size();
        _devs.push_back(d);
        [_devPop addItemWithTitle:S(d.name + "  (" + std::to_string((int)d.rate) + " Hz)")];
    }
    if (_devs.empty()) { [self say:@"[device] this Mac reports no output device"]; return; }
    if (sel < 0) sel = 0;
    [_devPop selectItemAtIndex:sel];
    [self startDevice:_devs[sel]];
}
// One [device] line per device, the first time it is seen: at the start, and for a device plugged in or switched on later.
// 0.7: a device that appears without a name or at 0 Hz (report 7: "(, unknown) ... now 0 Hz" during a Bluetooth
// reconnect) is asked again every 250 ms for up to 2 s before its line is written, and left out if it went away.
- (void)deviceLine:(const DeviceInfo&)d later:(BOOL)later { [self deviceLine:d later:later waited:NO]; }
- (void)deviceLine:(const DeviceInfo&)d later:(BOOL)later waited:(BOOL)waited {
    if (!_seenDevs) _seenDevs = [NSMutableSet set];
    if (!d.name.empty()) _devNames[d.id] = d.name;
    NSString* key = NSF("%u %s", d.id, d.name.c_str());
    if ([_seenDevs containsObject:key]) return;
    if (later && !waited && (d.name.empty() || d.rate <= 0)) { [self waitForDevice:d.id tries:0]; return; }
    [_seenDevs addObject:key];
    std::string rates; for (double r : d.rates) rates += (rates.empty() ? "" : " ") + std::to_string((int)r);
    for (auto& rr : d.rateRanges) rates += (rates.empty() ? "" : " ") + std::to_string((int)rr.first) + "-" + std::to_string((int)rr.second);
    [self say:NSF("[device] %s%s (%s, %s): out %d ch, in %d ch, now %.0f Hz, rates offered: %s, rate can be set: %s, buffer %u (range %u to %u), volume the computer can set: %s%s, format on the wire: %s (%d formats offered), exclusive use can be taken: %s%s",
               later ? "appeared: " : "", d.name.empty() ? "(no name after 2 s)" : d.name.c_str(), d.manufacturer.c_str(), d.transport.c_str(), d.outChannels, d.inChannels, d.rate, rates.c_str(), d.rateSettable ? "yes" : "no", d.buffer, d.bufferMin, d.bufferMax,
               d.hasVolume ? (d.volumeSettable ? "yes" : "has one but fixed") : "no", d.hasVolume ? (" (" + d.volumeWhere + ")").c_str() : "", d.physicalFormat.c_str(), d.physicalFormats, d.hogSettable ? "yes" : "no", d.isDefaultOutput ? ", DEFAULT OUTPUT" : "")];
}
- (void)waitForDevice:(uint32_t)devId tries:(int)n {
    NSNumber* k = @(devId);
    if (n == 0) { if ([_pendingDevs containsObject:k]) return; [_pendingDevs addObject:k]; }
    __weak App* me = self;
    dispatch_after(dispatch_time(DISPATCH_TIME_NOW, (int64_t)(0.25 * NSEC_PER_SEC)), dispatch_get_main_queue(), ^{ [me recheckDevice:devId tries:n]; });
}
- (void)recheckDevice:(uint32_t)devId tries:(int)n {
    bool still = false; DeviceInfo x;
    for (auto& y : listDevices()) if (y.id == devId) { still = true; x = y; }
    if (!still) { [_pendingDevs removeObject:@(devId)]; return; }          // it went away again: no line
    if ((!x.name.empty() && x.rate > 0) || n + 1 >= 8) { [_pendingDevs removeObject:@(devId)]; [self deviceLine:x later:YES waited:YES]; return; }
    [self waitForDevice:devId tries:n + 1];
}
- (void)startDevice:(const DeviceInfo&)d0 {
    // ask the device again: a list made when the device was plugged in can hold the rate it had for a moment only
    DeviceInfo d = deviceInfo(d0.id); if (!d.id) d = d0;
    _stream.stop();
    if (_hog && _dev && _dev != d.id) { int o; std::string e; setHog(_dev, false, o, e); _hog = NO; }
    { std::lock_guard<std::mutex> g(G.lock); G.sr = d.rate > 0 ? d.rate : 48000; G.lim.setRate(G.sr); if (G.plug) { std::string e; G.ready = G.plug->prepare(G.sr, G.maxBlock, false, e); } }
    _dev = d.id;
    if (!d.name.empty()) _devNames[d.id] = d.name;
    gEvents.push(evDeviceSwitch, d.id);
    std::string err;
    bool ok = _stream.start(d.id, renderCb, nullptr, err);
    DeviceInfo now = d; for (auto& x : listDevices()) if (x.id == d.id) now = x;
    NSString* item = [NSString stringWithFormat:@"%u", now.buffer]; if ([_bufPop itemWithTitle:item]) [_bufPop selectItemWithTitle:item];
    [self say:NSF("[output] %s: %s, %.0f Hz, buffer %u frames (%.2f ms), device latency %u + safety %u + stream %u frames%s", d.name.c_str(), ok ? "opened" : "COULD NOT BE OPENED", now.rate, now.buffer,
               now.rate ? now.buffer / now.rate * 1000 : 0, now.latency, now.safetyOffset, now.streamLatency, ok ? "" : (" (" + err + ")").c_str())];
    _watch.watchDevice(d.id);
    [self fillControls:now];
    [self checkOutput:now];
    [self formatCheck:now];
}
// ---- 0.7: the DAC's bit depth --------------------------------------------------------------------------------
// Report 6: the iFi Gryphon ran at "16-bit integer" on the wire at 44.1 kHz although it offers 60 formats. macOS mixes in
// 32-bit float and hands the DAC the physical format set in Audio MIDI Setup; nothing deeper reaches it.
static int formatBits(const std::string& f, bool& isInt) { int bits = 0; char kind[24] = {0}; sscanf(f.c_str(), "%d-bit %23s", &bits, kind); isInt = strncmp(kind, "integer", 7) == 0; return bits; }
static int deepestInteger(const DeviceInfo& d, bool mixable) {
    int best = 0;
    for (auto& f : listPhysicalFormats(d.id)) if (!f.isFloat && f.mixable == mixable && std::fabs(f.rate - d.rate) < 0.5 && f.bits > best) best = f.bits;
    return best;
}
- (void)formatCheck:(const DeviceInfo&)d {
    if (d.outChannels < 1) return;
    NSString* key = NSF("%u %s", d.id, d.physicalFormat.c_str());
    if ([_formatLogged containsObject:key]) return;
    [_formatLogged addObject:key];
    bool isInt = false; int bits = formatBits(d.physicalFormat, isInt);
    bool mix = d.physicalFormat.find("not mixable") == std::string::npos;
    int deep = deepestInteger(d, mix);
    [self say:NSF("[format] %s: on the wire %s (%d formats offered); the deepest integer format at %.0f Hz: %s", d.name.c_str(), d.physicalFormat.empty() ? "(not given)" : d.physicalFormat.c_str(), d.physicalFormats, d.rate,
                  deep ? fmt("%d-bit", deep).c_str() : "none (float only, or not offered)")];
    if (isInt && deep > bits)
        [self say:NSF("[warning] %s gets only %d bits: macOS mixes in 32-bit float and hands this DAC %d-bit integer, although it takes %d-bit integer at %.0f Hz. Fix: Audio MIDI Setup > %s > Format: %d-bit Integer at %.1f kHz, or this app's menu Device > Use the deepest format.",
                      d.name.c_str(), bits, bits, deep, d.rate, d.name.c_str(), deep, d.rate / 1000)];
}
- (void)useDeepestFormat:(id)s {
    if (!_dev) { [self say:@"[format] no output device is open"]; return; }
    DeviceInfo d = deviceInfo(_dev);
    bool isInt = false; int bits = formatBits(d.physicalFormat, isInt);
    bool mix = d.physicalFormat.find("not mixable") == std::string::npos;
    int deep = deepestInteger(d, mix);
    if (!deep) { [self say:NSF("[format] %s: no integer format at %.0f Hz to choose (on the wire: %s); nothing changed", d.name.c_str(), d.rate, d.physicalFormat.c_str())]; return; }
    if (isInt && deep == bits) { [self say:NSF("[format] %s: already the deepest integer format (%s); nothing changed", d.name.c_str(), d.physicalFormat.c_str())]; return; }
    [self say:NSF("[format] %s: before: %s; asking for %d-bit integer at %.0f Hz (%s), as you chose", d.name.c_str(), d.physicalFormat.c_str(), deep, d.rate, mix ? "mixable" : "not mixable")];
    _stream.stop();
    gEvents.push(evFormatChanged, _dev);
    std::string now, err;
    bool ok = setPhysicalFormat(_dev, d.rate, deep, mix, now, err);
    [self say:NSF("[format] %s: %s; after: %s%s", d.name.c_str(), ok ? "switched" : "NOT switched", now.c_str(), err.empty() ? "" : (" (" + err + ")").c_str())];
    [self startDevice:deviceInfo(_dev)];
}
// A plain warning when the output runs at 16 kHz or less, most often a Bluetooth speaker in call mode.
- (void)checkOutput:(const DeviceInfo&)d {
    std::string w;
    if (d.rate > 0 && d.rate <= 16000) {
        std::string bt;
        for (auto& x : listDevices()) {
            if (x.transport.find("Bluetooth") == std::string::npos || x.name.empty()) continue;
            if (x.id == d.id || d.name.find(x.name) != std::string::npos) { bt = x.name; break; }
        }
        char buf[900];
        if (!bt.empty())
            snprintf(buf, sizeof buf, "%s runs at %.0f Hz: the Bluetooth speaker %s is in call mode because an app has its microphone open, so music and plug-ins lose everything above %.0f kHz and some instruments stay silent. Fix: in System Settings > Sound > Input choose another input (or quit the app using the microphone); this app follows the rate when it comes back.",
                     d.name.c_str(), d.rate, bt.c_str(), d.rate / 2000);
        else
            snprintf(buf, sizeof buf, "%s runs at %.0f Hz, too low for music: plug-ins lose everything above %.0f kHz and some instruments stay silent. Fix: set the Rate above to 44100 Hz or more (or in Audio MIDI Setup), or choose another output.",
                     d.name.c_str(), d.rate, d.rate / 2000);
        w = buf;
    }
    if (w == _warnText) return;
    _warnText = w;
    if (w.empty()) { _warn.stringValue = NSF("Output %s at %.0f Hz.", d.name.c_str(), d.rate); _warn.textColor = NSColor.secondaryLabelColor; _warn.toolTip = nil; return; }
    _warn.stringValue = S("\u26A0 " + w); _warn.textColor = NSColor.systemRedColor; _warn.toolTip = S(w);
    [self say:S("[warning] " + w)];
}
- (void)fillControls:(const DeviceInfo&)d {
    [_ratePop removeAllItems];
    std::vector<double> rates = d.rates;
    for (auto& rr : d.rateRanges) for (double r : {44100.0, 48000.0, 88200.0, 96000.0, 176400.0, 192000.0}) if (r >= rr.first && r <= rr.second) rates.push_back(r);
    for (double r : rates) { NSString* t = [NSString stringWithFormat:@"%.0f Hz", r]; if (![_ratePop itemWithTitle:t]) [_ratePop addItemWithTitle:t]; }
    NSString* cur = [NSString stringWithFormat:@"%.0f Hz", d.rate]; if (![_ratePop itemWithTitle:cur]) [_ratePop addItemWithTitle:cur];
    [_ratePop selectItemWithTitle:cur]; _ratePop.enabled = d.rateSettable;
    _exclBtn.enabled = d.hogSettable; _exclBtn.state = (d.hogPid == (int)getpid()) ? NSControlStateValueOn : NSControlStateValueOff;
    double v = -1; bool has = getVolume(d.id, v);
    _vol.enabled = has && d.volumeSettable; if (has) _vol.doubleValue = v;
    _volLbl.stringValue = has ? NSF("%.0f %%%s", v * 100, d.volumeSettable ? "" : " (fixed)") : @"this device has none";
}
- (void)rateChanged:(id)s {
    double want = _ratePop.titleOfSelectedItem.doubleValue, now = 0; std::string err;
    _stream.stop();
    gEvents.push(evRateChanged, _dev);
    bool ok = setDeviceRate(_dev, want, now, err);
    [self say:NSF("[rate] asked for %.0f Hz: %s, the device now runs %.0f Hz%s", want, ok ? "switched" : "NOT switched", now, err.empty() ? "" : (" " + err).c_str())];
    [self startDevice:deviceInfo(_dev)];
}
- (void)exclChanged:(id)s {
    bool on = _exclBtn.state == NSControlStateValueOn; int owner = -1; std::string err;
    bool ok = setHog(_dev, on, owner, err); _hog = on && ok;
    [self say:NSF("[exclusive] %s: %s (the device is now held by process %d, this app is %d)%s. While it is on, no other program can play through this device.", on ? "asked for exclusive use" : "gave exclusive use back", ok ? "done" : "NOT done", owner, (int)getpid(), err.empty() ? "" : (" " + err).c_str())];
    [self fillControls:deviceInfo(_dev)];
}
- (void)volChanged:(id)s {
    std::string err; setVolume(_dev, _vol.doubleValue, err);
    double v = -1; getVolume(_dev, v);
    _volLbl.stringValue = [NSString stringWithFormat:@"%.0f %%", v * 100];
}
- (void)outside:(NSString*)what {
    if ([what isEqualToString:@"volume"] || [what isEqualToString:@"mute"]) {
        double v = -1; if (getVolume(_dev, v)) { _vol.doubleValue = v; _volLbl.stringValue = [NSString stringWithFormat:@"%.0f %%", v * 100]; }
    } else if ([what isEqualToString:@"rate"]) {
        DeviceInfo d = deviceInfo(_dev);
        if (d.rate > 0 && d.rate != G.sr) { [self say:[NSString stringWithFormat:@"[rate] the device was switched to %.0f Hz from outside this app; following it", d.rate]]; [self startDevice:d]; }
    } else if ([what isEqualToString:@"devices"] || [what isEqualToString:@"alive"]) {
        std::vector<DeviceInfo> outs; bool here = false; int sel = -1;
        auto all = listDevices();
        for (auto& d : all) [self deviceLine:d later:YES];      // a device that appeared since the start gets its own line, with the same details
        for (auto& d : all) { if (d.outChannels < 1) continue; if (d.id == _dev) { here = true; sel = (int)outs.size(); } outs.push_back(d); }
        if (_dev) [self checkOutput:deviceInfo(_dev)];
        if (outs.size() == _devs.size() && here) { bool same = true; for (size_t i = 0; i < outs.size(); i++) if (outs[i].id != _devs[i].id) same = false; if (same) return; }
        _devs = outs; [_devPop removeAllItems];
        for (auto& d : _devs) [_devPop addItemWithTitle:S(d.name + "  (" + std::to_string((int)d.rate) + " Hz)")];
        std::string names; for (auto& d : _devs) names += (names.empty() ? "" : ", ") + d.name;
        [self say:NSF("[devices] the list changed: %zu output(s) now: %s", _devs.size(), names.c_str())];
        if (here) [_devPop selectItemAtIndex:sel];
        else if (!_devs.empty()) {
            uint32_t def = defaultOutputDevice(); int k = 0; for (int i = 0; i < (int)_devs.size(); i++) if (_devs[i].id == def) k = i;
            [self say:@"[devices] the device in use is gone; moving to the default output"];
            _hog = NO; [_devPop selectItemAtIndex:k]; [self startDevice:_devs[k]];
        }
    }
}
- (void)deviceChanged:(id)s { NSInteger i = _devPop.indexOfSelectedItem; if (i >= 0 && i < (NSInteger)_devs.size()) [self startDevice:_devs[i]]; }
- (void)bufferChanged:(id)s {
    uint32_t want = (uint32_t)_bufPop.titleOfSelectedItem.intValue, now = 0; std::string err;
    gEvents.push(evBufferChanged, _dev);
    bool ok = setDeviceBuffer(_dev, want, now, err);
    double sr = G.sr;
    [self say:NSF("[buffer] asked for %u frames: %s, the device now runs %u frames (%.2f ms at %.0f Hz)%s", want, ok ? "accepted" : "not accepted", now, sr ? now / sr * 1000 : 0, sr, err.empty() ? "" : (" " + err).c_str())];
    G.blocks = 0; G.sumNs = 0; G.worstNs = 0; _stream.minFrames = 0xffffffffu; _stream.maxFrames = 0;
    { std::lock_guard<std::mutex> g(G.lock); G.slow.reset(); }
}

- (void)scan:(id)s {
    _scanBtn.enabled = NO; _status.stringValue = @"Scanning plug-ins";
    _rows.clear(); _scan.clear(); [self refilter];
    std::string exe = U(NSBundle.mainBundle.executablePath);
    __weak App* me = self;
    dispatch_async(dispatch_get_global_queue(QOS_CLASS_USER_INITIATED, 0), ^{
        PluginFormat* F = vst3Format();
        auto folders = F->defaultFolders();
        auto bundles = F->findBundles(folders);
        std::vector<ScanResult> res;
        for (size_t i = 0; i < bundles.size(); i++) {
            ScanResult r = scanOutOfProcess(exe, bundles[i], 30);
            res.push_back(r);
            dispatch_async(dispatch_get_main_queue(), ^{ [me addScan:r done:(int)(i + 1) of:(int)bundles.size()]; });
        }
        dispatch_async(dispatch_get_main_queue(), ^{ [me scanDone:(int)bundles.size() folders:folders]; });
    });
}
- (void)addScan:(const ScanResult&)r done:(int)i of:(int)n {
    _scan.push_back(r);
    std::string file = r.path.substr(r.path.find_last_of('/') + 1);
    if (!r.ok) {
        Row row; row.name = file; row.kind = "cannot load"; row.status = "PROBLEM: " + r.error; row.path = r.path; row.archs = r.archs; _rows.push_back(row);
        [self say:NSF("[scan] PROBLEM %s [%s]: %s", r.path.c_str(), r.archs.c_str(), r.error.c_str())];
    }
    for (auto& p : r.plugins) {
        Row row; row.name = p.name; row.vendor = p.vendor; row.kind = p.isInstrument ? "instrument" : "effect"; row.instrument = p.isInstrument; row.ok = true; row.path = r.path; row.uid = p.uid; row.archs = r.archs;
        row.status = "found (" + (r.archs.empty() ? std::string("?") : r.archs) + ", version " + p.version + ")";
        _rows.push_back(row);
        [self say:NSF("[scan] found %s by %s, %s, version %s [%s] in %s (%.2f s)", p.name.c_str(), p.vendor.c_str(), row.kind.c_str(), p.version.c_str(), r.archs.c_str(), file.c_str(), r.seconds)];
    }
    _status.stringValue = [NSString stringWithFormat:@"Scanning plug-ins: %d of %d", i, n];
    [self refilter];
}
- (void)scanDone:(int)n folders:(std::vector<std::string>)folders {
    int ok = 0, plugs = 0; for (auto& r : _scan) { if (r.ok) ok++; plugs += (int)r.plugins.size(); }
    _bundles = n; _bundlesOk = ok;
    std::string fl; for (auto& f : folders) fl += (fl.empty() ? "" : ", ") + f;
    [self say:NSF("[scan] done: %d bundle(s) in %s; %d could be read, %d could not; %d plug-in(s). The app itself was never at risk: every bundle was opened in a separate process.", n, fl.c_str(), ok, n - ok, plugs)];
    _status.stringValue = [NSString stringWithFormat:@"%d plug-in(s) found", plugs];
    _scanBtn.enabled = YES;
    int ni = 0, nb = 0; for (auto& r : _scan) if (!r.ok) { if (r.wrongArch) ni++; else nb++; }
    if (ni + nb) [self say:[NSString stringWithFormat:@"[scan] %d bundle(s) are Intel-only (they need Rosetta: a helper comes later) and %d could not be read: both lists are at the end of this report", ni, nb]];
    [self listOtherFormats];
    if (_selftest) {     // leave the main window alone for two seconds so the build machine can take a picture of it
        [self writeMarker:@"scanned"];
        __weak App* me = self;
        dispatch_after(dispatch_time(DISPATCH_TIME_NOW, (int64_t)(2.5 * NSEC_PER_SEC)), dispatch_get_main_queue(), ^{ [me selftestStart]; });
    }
}

// Decision D5 (CLAP or Audio Units next): list what is installed in both formats, without loading anything.
- (void)listOtherFormats {
    for (NSString* f in @[@"clap", @"au"]) {
        std::vector<std::string> folders;
        auto v = listOtherFormat(U(f), folders);
        std::string fl; for (auto& x : folders) fl += (fl.empty() ? "" : ", ") + x;
        int arm = 0, intel = 0; std::map<std::string, int> kinds;
        for (auto& b : v) { if (b.archs.find("arm64") != std::string::npos) arm++; else if (!b.archs.empty()) intel++; if (!b.kind.empty()) kinds[b.kind]++; }
        std::string ks; for (auto& k : kinds) ks += (ks.empty() ? "" : ", ") + std::to_string(k.second) + " " + k.first;
        BOOL clap = [f isEqualToString:@"clap"];
        [self say:NSF("[%s] %zu %s bundle(s) in %s (listed, not loaded): %d for Apple Silicon, %d Intel-only%s%s", U(f).c_str(), v.size(), clap ? "CLAP" : "Audio Unit", fl.c_str(), arm, intel,
                   ks.empty() ? "" : "; kinds: ", ks.c_str())];
        std::string names; int n = 0;
        for (auto& b : v) { names += (n ? "; " : "") + b.name + (b.kind.empty() ? "" : " (" + b.kind + ")") + (b.archs.empty() || b.archs.find("arm64") != std::string::npos ? "" : " [" + b.archs + " only]"); n++; }
        if (n) [self say:NSF("[%s] names: %s", U(f).c_str(), names.c_str())];
    }
}

// ---- the list: search, kind filter, sort or group by maker, recently loaded on top ------------------------
- (NSString*)recentKey:(const Row&)x { return S(x.path + "\n" + x.uid + "\n" + x.name); }
- (int)plugIndexAtViewRow:(NSInteger)r { return (r >= 0 && r < (NSInteger)_view.size()) ? _view[r].idx : -1; }
- (void)searchChanged:(id)s { [self refilter]; }
- (void)focusSearch:(id)s { [_win makeKeyAndOrderFront:nil]; [_win makeFirstResponder:_search]; }
- (void)refilter {
    int keep = [self plugIndexAtViewRow:_table.selectedRow];
    NSArray<NSString*>* words = [[fold(_search.stringValue) stringByTrimmingCharactersInSet:NSCharacterSet.whitespaceCharacterSet] componentsSeparatedByCharactersInSet:NSCharacterSet.whitespaceCharacterSet];
    NSInteger kind = _kindPop.indexOfSelectedItem, sort = _sortPop.indexOfSelectedItem;
    std::vector<int> hits;
    int total = 0, shownOk = 0, shownBad = 0;
    for (int i = 0; i < (int)_rows.size(); i++) {
        const Row& x = _rows[i];
        if (x.ok) total++;
        if (kind == 1 && !(x.ok && x.instrument)) continue;
        if (kind == 2 && !(x.ok && !x.instrument)) continue;
        if (kind == 3 && x.ok) continue;
        NSString* hay = fold(S(x.name + " " + x.vendor + " " + x.kind + " " + x.path.substr(x.path.find_last_of('/') + 1)));
        bool all = true;
        for (NSString* w in words) if (w.length && [hay rangeOfString:w].location == NSNotFound) { all = false; break; }
        if (!all) continue;
        hits.push_back(i);
        if (x.ok) shownOk++; else shownBad++;
    }
    auto lower = [&](const std::string& a) { return U(fold(S(a))); };
    std::stable_sort(hits.begin(), hits.end(), [&](int a, int b) {
        const Row &x = _rows[a], &y = _rows[b];
        if (x.ok != y.ok) return x.ok;                                     // the ones that cannot load go last
        if (sort >= 1) { std::string vx = lower(x.vendor), vy = lower(y.vendor); if (vx != vy) return vx < vy; }
        return lower(x.name) < lower(y.name);
    });
    // recently loaded first, newest on top
    std::vector<int> recent, rest;
    for (int i : hits) ([_recent indexOfObject:[self recentKey:_rows[i]]] != NSNotFound ? recent : rest).push_back(i);
    std::sort(recent.begin(), recent.end(), [&](int a, int b) { return [_recent indexOfObject:[self recentKey:_rows[a]]] < [_recent indexOfObject:[self recentKey:_rows[b]]]; });
    _view.clear();
    bool group = sort == 2;
    if (!recent.empty()) { if (group) { ViewRow h; h.heading = "Recently loaded"; _view.push_back(h); } for (int i : recent) { ViewRow v; v.idx = i; _view.push_back(v); } }
    std::string cur = "\x01";
    for (int i : rest) {
        if (group) {
            const Row& x = _rows[i];
            std::string g = x.ok ? (x.vendor.empty() ? std::string("(no maker given)") : x.vendor) : std::string("Cannot load");
            if (g != cur) {
                int n = 0; for (int j : rest) { const Row& y = _rows[j]; std::string gy = y.ok ? (y.vendor.empty() ? std::string("(no maker given)") : y.vendor) : std::string("Cannot load"); if (gy == g) n++; }
                ViewRow h; h.heading = g + "  (" + std::to_string(n) + ")"; _view.push_back(h); cur = g;
            }
        }
        ViewRow v; v.idx = i; _view.push_back(v);
    }
    [_table reloadData];
    _countLbl.stringValue = shownBad ? [NSString stringWithFormat:@"%d of %d  (+%d cannot load)", shownOk, total, shownBad] : [NSString stringWithFormat:@"%d of %d", shownOk, total];
    // keep the selection, or pick the first match while searching
    NSInteger sel = -1;
    for (NSInteger r = 0; r < (NSInteger)_view.size(); r++) if (_view[r].idx >= 0 && _view[r].idx == keep) { sel = r; break; }
    if (sel < 0 && _search.stringValue.length) for (NSInteger r = 0; r < (NSInteger)_view.size(); r++) if (_view[r].idx >= 0) { sel = r; break; }
    if (sel >= 0) { [_table selectRowIndexes:[NSIndexSet indexSetWithIndex:sel] byExtendingSelection:NO]; [_table scrollRowToVisible:sel]; }
    else [_table deselectAll:nil];
}
- (void)noteRecent:(const Row&)x {
    NSString* k = [self recentKey:x];
    [_recent removeObject:k]; [_recent insertObject:k atIndex:0];
    while (_recent.count > 8) [_recent removeLastObject];
    @try { [NSUserDefaults.standardUserDefaults setObject:_recent forKey:@"recentPlugins"]; } @catch (NSException* e) {}
}
// Enter in the search field loads the selected match; the down arrow moves into the list.
- (BOOL)control:(NSControl*)c textView:(NSTextView*)tv doCommandBySelector:(SEL)cmd {
    if (c != _search) return NO;
    if (cmd == @selector(insertNewline:)) { [self load:nil]; return YES; }
    if (cmd == @selector(moveDown:)) { [_win makeFirstResponder:_table]; return YES; }
    if (cmd == @selector(cancelOperation:)) { _search.stringValue = @""; [self refilter]; return YES; }
    return NO;
}
- (NSInteger)numberOfRowsInTableView:(NSTableView*)t { return (NSInteger)_view.size(); }
- (id)tableView:(NSTableView*)t objectValueForTableColumn:(NSTableColumn*)c row:(NSInteger)r {
    if (r < 0 || r >= (NSInteger)_view.size()) return @"";
    const ViewRow& v = _view[r];
    if (v.idx < 0) return c == nil || [c.identifier isEqualToString:@"name"] ? S(v.heading) : @"";
    const Row& x = _rows[v.idx]; NSString* k = c.identifier;
    if ([k isEqualToString:@"status"] && [_recent indexOfObject:[self recentKey:x]] != NSNotFound) return S("recently loaded · " + x.status);
    return S([k isEqualToString:@"name"] ? x.name : [k isEqualToString:@"vendor"] ? x.vendor : [k isEqualToString:@"kind"] ? x.kind : x.status);
}
- (BOOL)tableView:(NSTableView*)t isGroupRow:(NSInteger)r { return r >= 0 && r < (NSInteger)_view.size() && _view[r].idx < 0; }
- (NSCell*)tableView:(NSTableView*)t dataCellForTableColumn:(NSTableColumn*)c row:(NSInteger)r {
    if (c == nil) { if ([self tableView:t isGroupRow:r]) { NSTextFieldCell* cell = [[NSTextFieldCell alloc] initTextCell:@""]; cell.font = [NSFont boldSystemFontOfSize:12]; return cell; } return nil; }
    return [c dataCellForRow:r];
}
- (BOOL)tableView:(NSTableView*)t shouldSelectRow:(NSInteger)r { return ![self tableView:t isGroupRow:r]; }

- (void)load:(id)s {
    int r = [self plugIndexAtViewRow:_table.selectedRow];
    if (r < 0 || r >= (int)_rows.size()) { [self say:@"[load] pick a plug-in in the list first"]; return; }
    [self loadRow:r];
}
- (BOOL)loadRow:(int)r {
    Row& x = _rows[r];
    if (!x.ok) { [self say:NSF("[load] %s cannot be loaded: %s", x.name.c_str(), x.status.c_str())]; return NO; }
    [self closePlugWindow];
    [self flushPlugSummary];
    { std::lock_guard<std::mutex> g(G.lock); G.ready = false; G.plug.reset(); }
    PluginInfo pi; pi.format = "vst3"; pi.path = x.path; pi.uid = x.uid; pi.name = x.name;
    std::string err;
    CFAbsoluteTime t0 = CFAbsoluteTimeGetCurrent();
    std::unique_ptr<PluginInstance> p = vst3Format()->create(pi, err);     // the 0.5 host (HostOptions defaults)
    double ms = (CFAbsoluteTimeGetCurrent() - t0) * 1000;
    if (!p) { x.status = "FAILED to load: " + err; [_table reloadData]; [self say:NSF("[load] FAILED %s: %s", x.name.c_str(), err.c_str())]; return NO; }
    p->setEventSink([](uint32_t k, uint32_t a) { gEvents.push(k, a); });   // gestures, restarts, state, presets: no lock, any thread
    gEvents.push(evPluginLoaded, 0);
    BusLayout b = p->buses();
    bool inst = p->info().isInstrument && b.eventIns > 0;
    bool ok = p->prepare(G.sr, G.maxBlock, false, err);
    auto ps = p->params();
    std::vector<uint8_t> st; bool gotState = p->getState(st);
    int lat = p->latencySamples();
    std::string names; for (size_t i = 0; i < ps.size() && i < 8; i++) names += (i ? ", " : "") + ps[i].name;
    std::string latText = fmt("latency %d samples (%.2f ms at %.0f Hz)", lat, G.sr > 0 ? lat / G.sr * 1000 : 0, G.sr);
    if (lat > 0 && !_latencyNoted) { _latencyNoted = YES; latText += ": the app will compensate this later"; }   // said once per report
    [self say:NSF("[load] %s %s in %.0f ms: %s, audio in %d ch, out %d ch, note inputs %d, %zu parameters (first: %s), state %s (%zu bytes), %s%s",
               x.name.c_str(), ok ? "loaded" : "loaded but could not be started", ms, inst ? "instrument" : "effect", b.mainInChannels, b.mainOutChannels, b.eventIns, ps.size(), names.c_str(), gotState ? "saved" : "NOT saved", st.size(), latText.c_str(),
               ok ? "" : (" (" + err + ")").c_str())];
    x.status = ok ? "loaded" : "FAILED to start: " + err;
    _loadedInfo = p->info(); _loadStateBytes = st.size(); _probedThis = NO;
    if (_diagBtn.state == NSControlStateValueOn) {
        std::string t = diagText(x.name, p->diag());
        size_t cut = t.rfind("[diag]");                  // the last line holds the live counters: written later, at the summary
        for (NSString* l in [S(t.substr(0, cut)) componentsSeparatedByString:@"\n"]) if (l.length) [self say:l];
    }
    _presets = p->presets();
    [_presetPop removeAllItems];
    [_presetPop addItemWithTitle:_presets.empty() ? @"No presets via VST3" : [NSString stringWithFormat:@"Factory preset (%zu)", _presets.size()]];
    for (size_t i = 0; i < _presets.size() && i < 300; i++) [_presetPop addItemWithTitle:NSF("%zu. %s", i + 1, _presets[i].name.c_str())];
    _presetPop.enabled = !_presets.empty();
    [self say:NSF("[presets] %s: %zu reachable through VST3%s", x.name.c_str(), _presets.size(),
               _presets.empty() ? " (no program list, no .vstpreset file): to rule out an empty start patch, choose a preset in its own window, then play the pattern" : (" (first: \"" + _presets[0].name + "\"); choose one in the Factory preset menu").c_str())];
    _paramNames.clear(); for (auto& q : ps) _paramNames[q.id] = q.name;
    {   // 0.7: the poll for values that change without the host being told (read-only parameters, meters, left out)
        std::vector<uint32_t> ids; std::vector<std::string> nm; std::vector<bool> ro;
        for (auto& q : ps) { ids.push_back(q.id); nm.push_back(q.name); ro.push_back(q.readOnly); }
        _pw.setParams(ids, nm, ro); _paramLiveLines = 0; _polls = 0; _pollWorstMs = 0; _pollSumMs = 0; _lastValueRestarts = 0;
    }
    _plugMouse = 0; _plugDrags = 0; _lastMoves = 0; _windowOpened = NO; _firstMoveLogged = NO;
    G.blocks = 0; G.sumNs = 0; G.worstNs = 0; G.failed = 0; G.peak = 0; G.notesPattern = 0; G.notesKeys = 0; G.fedBlocks = 0;
    _overWarned = NO; _overSeen = 0; _meter.over = NO; [_meter setNeedsDisplay:YES];
    { std::lock_guard<std::mutex> g(G.lock); G.plug = std::move(p); G.instrument = inst; G.ready = ok; G.patStep = -1; G.patNote = -1;
      G.overBlocks = 0; G.overFirstT = 0; G.overLastT = 0; G.overPeak = 0; G.ownPeak = 0; G.lim.reset(); G.lim.setRate(G.sr); G.slow.reset(); }
    _loaded = x.name;
    _status.stringValue = S("Loaded: " + x.name);
    if (ok) [self noteRecent:x];
    [self refilter];
    return ok;
}

- (void)openEditor:(id)s {
    if (!G.plug) { [self say:@"[window] load a plug-in first"]; return; }
    [self closePlugWindow];
    NSRect fr = NSMakeRect(0, 0, 600, 400);
    _plugWin = [[NSWindow alloc] initWithContentRect:fr styleMask:NSWindowStyleMaskTitled | NSWindowStyleMaskClosable | NSWindowStyleMaskMiniaturizable backing:NSBackingStoreBuffered defer:NO];
    _plugWin.releasedWhenClosed = NO; _plugWin.delegate = self; _plugWin.title = S(_loaded);
    NSView* host = [[NSView alloc] initWithFrame:fr]; _plugWin.contentView = host;
    int w = 0, h = 0; std::string err;
    __weak NSWindow* pw = _plugWin;
    bool ok = G.plug->openEditor((__bridge void*)host, w, h, [pw](int nw, int nh) { if (nw > 0 && nh > 0) [pw setContentSize:NSMakeSize(nw, nh)]; }, err);
    if (!ok) { [self say:NSF("[window] %s: no window (%s)", _loaded.c_str(), err.c_str())]; _plugWin = nil; return; }
    if (w > 0 && h > 0) [_plugWin setContentSize:NSMakeSize(w, h)];
    // next to the main window if there is room, otherwise wherever it fits on the screen
    NSRect mf = _win.frame, vis = (_win.screen ?: NSScreen.mainScreen).visibleFrame, pf = _plugWin.frame;
    CGFloat x = NSMaxX(mf) + 12; if (x + pf.size.width > NSMaxX(vis)) x = NSMaxX(vis) - pf.size.width; if (x < NSMinX(vis)) x = NSMinX(vis);
    CGFloat top = NSMaxY(mf); if (top - pf.size.height < NSMinY(vis)) top = NSMinY(vis) + pf.size.height; if (top > NSMaxY(vis)) top = NSMaxY(vis);
    [_plugWin setFrameTopLeftPoint:NSMakePoint(x, top)];
    [_plugWin makeKeyAndOrderFront:nil];
    _windowOpened = YES;
    gEvents.push(evWindowOpened, 0);
    _pw.forget();
    [self say:NSF("[window] %s: its own window is open, %d x %d", _loaded.c_str(), w, h)];
}
- (void)closePlugWindow {
    if (_plugWin) gEvents.push(evWindowClosed, 0);
    if (G.plug) G.plug->closeEditor();
    if (_plugWin) { _plugWin.delegate = nil; [_plugWin orderOut:nil]; _plugWin = nil; }
}
- (BOOL)windowShouldClose:(NSWindow*)w {
    if (w == _plugWin) { [self closePlugWindow]; return NO; }
    return YES;
}
- (void)windowWillClose:(NSNotification*)n { if (n.object == _win) [NSApp terminate:nil]; }
- (BOOL)applicationShouldTerminateAfterLastWindowClosed:(NSApplication*)a { return YES; }
- (void)applicationWillTerminate:(NSNotification*)n {
    [self writeReport];          // its end holds the loaded plug-in's [param] and [notes] lines
    _stream.stop();
    _watch.stop();
    if (_hog && _dev) { int o; std::string e; setHog(_dev, false, o, e); }
    [self closePlugWindow];
    { std::lock_guard<std::mutex> g(G.lock); G.ready = false; G.plug.reset(); }
}

- (void)togglePattern:(id)s {
    if (!G.plug && !G.pattern.load()) { [self say:@"[pattern] nothing to play yet: click a plug-in in the list and Load first"]; _status.stringValue = @"Load a plug-in first"; return; }
    bool on = !G.pattern.load(); G.pattern = on;
    gEvents.push(on ? evPatternOn : evPatternOff, 0);
    _patBtn.title = on ? @"Stop test pattern" : @"Play test pattern";
    [self say:on ? @"[pattern] test pattern on" : [@"[pattern] test pattern off. " stringByAppendingString:[[NSString stringWithFormat:@"%@%@", [self audioFigures], [self plugSummary]] stringByTrimmingCharactersInSet:NSCharacterSet.newlineCharacterSet]]];
    // an instrument that stayed silent although notes reached it: probe it once, by itself
    if (!on && G.plug && G.instrument && !_probedThis && !_selftest && G.peak.load() <= 0 && G.notesPattern.load() + G.notesKeys.load() >= 8) [self probe:nil];
}
- (BOOL)key:(NSEvent*)e {
    if (e.window != _win) return NO;      // keys typed in the plug-in's own window belong to the plug-in
    NSEventModifierFlags mods = e.modifierFlags & (NSEventModifierFlagCommand | NSEventModifierFlagControl | NSEventModifierFlagOption);
    if (e.type == NSEventTypeKeyDown && mods == NSEventModifierFlagCommand && [e.charactersIgnoringModifiers.lowercaseString isEqualToString:@"f"]) { [_win makeFirstResponder:_search]; return YES; }
    if (e.type == NSEventTypeKeyDown && e.keyCode == 53 && _search.stringValue.length) { _search.stringValue = @""; [self refilter]; [_win makeFirstResponder:_table]; return YES; }   // Escape clears the search
    if (mods) return NO;
    NSResponder* fr = _win.firstResponder;
    if ([fr isKindOfClass:NSText.class] || fr == _search) return NO;     // typing in the search field is not notes
    static NSString* keys = @"awsedftgyhujk";
    NSString* c = e.charactersIgnoringModifiers.lowercaseString;
    if (c.length != 1) return NO;
    NSRange r = [keys rangeOfString:c];
    if (r.location == NSNotFound) return NO;
    int pitch = 60 + (int)r.location; NSNumber* k = @(pitch);
    if (e.type == NSEventTypeKeyDown) { if (!e.isARepeat && ![_down containsObject:k]) { [_down addObject:k]; G.pushNote(pitch, true); } }
    else { [_down removeObject:k]; G.pushNote(pitch, false); }
    return YES;
}
- (void)tick {
    // 0.7: the plug-in's own output past full scale: one [warning], and the red mark until it is clicked
    uint64_t ob = G.overBlocks.load();
    if (G.plug && ob > 0 && !_overWarned) {
        _overWarned = YES;
        [self say:NSF("[warning] %s: its own output passed full scale (0 dBFS): peak %+.1f dBFS at %s. This app's safety limiter keeps what reaches the device at or below -0.2 dBFS (nothing inside the plug-in is changed); turn the plug-in's own volume down. The red OVER mark on the meter stays until you click it.",
                      _loaded.c_str(), 20 * std::log10(std::max(G.overPeak.load(), 1e-9f)), [self clockText:G.overFirstT.load()].c_str())];
    }
    if (ob != _overSeen && ob > 0) { _overSeen = ob; if (!_meter.over) { _meter.over = YES; [_meter setNeedsDisplay:YES]; } }
    EditStats es; if (G.plug) es = G.plug->editStats();
    if (G.plug && es.performs > 0 && !_firstMoveLogged) {
        _firstMoveLogged = YES;
        [self say:NSF("[param] %s: first move from its window: %s", _loaded.c_str(), [self paramDesc:es.lastId value:es.lastValue].c_str())];
    }
    if (G.plug && es.performs != _lastMoves) { _lastMoves = es.performs; [self writeReport]; }
    uint32_t notes = G.notesPattern.load() + G.notesKeys.load();
    NSString* plugPart = G.plug ? [NSString stringWithFormat:@"   moves in its window: %d   notes sent: %u", es.performs, notes] : @"";
    uint64_t b = G.blocks.load();
    if (!b) { _cpu.stringValue = G.plug ? [@"Loaded. Play the test pattern or press keys." stringByAppendingString:plugPart] : @"No plug-in loaded."; return; }
    double avg = G.sumNs.load() / 1000.0 / b, worst = G.worstNs.load() / 1000.0, budget = G.budgetNs.load() / 1000.0;
    _cpu.stringValue = [NSString stringWithFormat:@"Time per block: avg %.1f µs (%.2f %%), worst %.1f µs (%.1f %%)   block %.2f ms at %.0f Hz   overloads %llu   level %.2f%@",
                        avg, budget ? avg / budget * 100 : 0, worst, budget ? worst / budget * 100 : 0, budget / 1000, G.sr, _stream.overloads.load(), G.peak.load(), plugPart];
}
- (void)meterTick {
    float pk = G.meterPeak.exchange(0.0f);
    double shown = std::max((double)pk, _meterShown * 0.80);
    if (std::fabs(shown - _meterShown) > 1e-4 || (shown > 0 && shown < 1e-4)) { _meterShown = shown < 1e-4 ? 0 : shown; _meter.level = _meterShown; [_meter setNeedsDisplay:YES]; }
}
- (void)clearOver {
    _overSeen = G.overBlocks.load();
    _meter.over = NO; [_meter setNeedsDisplay:YES];
}
// 0.7: every 200 ms while the plug-in's window is open, all its values (getParamNormalized, main thread); a change that
// never came through performEdit (and was not the host's own, nor a preset the plug-in announced) gets a [param] line.
- (void)pollParams {
    if (!G.plug || !_plugWin) { _pw.forget(); return; }
    EditStats es = G.plug->editStats();
    bool all = (uint64_t)es.valueRestarts != _lastValueRestarts; _lastValueRestarts = (uint64_t)es.valueRestarts;
    std::set<uint32_t> touched = G.plug->takeTouchedParams();
    PluginInstance* p = G.plug.get();
    uint64_t t0 = nowNs();
    std::vector<std::string> fresh = _pw.poll([p](uint32_t id) { return p->getParam(id); }, touched, all);
    double ms = (nowNs() - t0) / 1e6;
    _polls++; _pollSumMs += ms; if (ms > _pollWorstMs) _pollWorstMs = ms;
    for (auto& n : fresh) if (_paramLiveLines++ < 5) [self say:NSF("[param] %s: changed without telling the host: %s", _loaded.c_str(), n.c_str())];
}
- (void)plugMouse:(NSEvent*)e {
    if (!_plugWin || e.window != _plugWin) return;
    if (e.type == NSEventTypeLeftMouseDragged) _plugDrags++; else { _plugMouse++; if (e.type != NSEventTypeScrollWheel) gEvents.push(evMouseInWindow, 0); }
}
- (std::string)paramDesc:(uint32_t)pid value:(double)v {
    auto it = _paramNames.find(pid);
    std::string name = it != _paramNames.end() ? it->second : "parameter " + std::to_string(pid);
    char buf[64]; snprintf(buf, sizeof buf, "%.2f", v);
    std::string t = G.plug ? G.plug->paramText(pid, v) : "";
    return name + " = " + buf + (t.empty() ? "" : " (" + t + ")");
}
// The per plug-in lines of the report: parameter moves from its own window, and the notes it was sent.
- (NSString*)plugSummary {
    if (!G.plug || _loaded.empty()) return @"";
    EditStats es = G.plug->editStats();
    const char* nm = _loaded.c_str();
    NSMutableString* o = [NSMutableString string];
    std::string restarts = es.restarts ? fmt("; it asked the host to restart %d time(s), %d of them because all its values changed", es.restarts, es.valueRestarts) : std::string();
    if (es.performs > 0)
        [o appendString:NSF("[param] %s: %d moves from its window (gestures begun %d, ended %d), last: %s%s", nm, es.performs, es.begins, es.ends, [self paramDesc:es.lastId value:es.lastValue].c_str(), restarts.c_str())];
    else if (_plugMouse + _plugDrags > 0)
        [o appendString:NSF("[param] %s: NO parameter moves reached the host from its window, although the mouse was used in it %d time(s) (%d click(s) or scroll(s), %d drag step(s)); gestures begun %d%s. If you turned knobs, this plug-in does not tell the host about them (or not through VST3's component handler)", nm, _plugMouse + _plugDrags, _plugMouse, _plugDrags, es.begins, restarts.c_str())];
    else if (_windowOpened)
        [o appendString:NSF("[param] %s: no moves from its window (the mouse was not used in it)%s", nm, restarts.c_str())];
    else
        [o appendString:NSF("[param] %s: its window was not opened, so no moves from it%s", nm, restarts.c_str())];
    // 0.7: values that changed although the plug-in never told the host
    if (_polls > 0) {
        std::string first; for (auto& n : _pw.firstNames) first += (first.empty() ? "" : ", ") + n;
        if (_pw.changes > 0)
            [o appendString:NSF("\n[param] %s: %llu change(s) without telling the host (no performEdit) in %zu parameter(s), first: %s; seen by polling its %zu values every 200 ms while its window was open (%d polls, %.2f ms on average, worst %.2f ms)",
                                nm, (unsigned long long)_pw.changes, _pw.seen.size(), first.c_str(), _pw.ids.size(), _polls, _pollSumMs / _polls, _pollWorstMs)];
        else
            [o appendString:NSF("\n[param] %s: no value changed without telling the host (polled its %zu values every 200 ms while its window was open: %d polls, %.2f ms on average, worst %.2f ms)", nm, _pw.ids.size(), _polls, _pollSumMs / _polls, _pollWorstMs)];
    }
    uint32_t np = G.notesPattern.load(), nk = G.notesKeys.load();
    float pk = G.peak.load();
    if (G.instrument) {
        if (np + nk == 0) [o appendString:NSF("\n[notes] %s: not played: play the pattern to test it (0 notes sent)", nm)];
        else {
            [o appendString:NSF("\n[notes] %s: %u notes sent (%u from the test pattern, %u from the keys), output peak %.3f", nm, np + nk, np, nk, pk)];
            if (pk <= 0) {
                if (G.sr < 44100) [o appendString:NSF(": SILENT although the notes reached it. The output runs at %.0f Hz; some instruments make no sound at such a low rate (Pigments played at 44.1 kHz in an earlier report and was silent at 16 kHz; Surge XT and mda JX10 do sound at 16 kHz). Choose an output at 44.1 kHz or more and play again", G.sr)];
                else [o appendString:@": SILENT although the notes reached it"];
            } else [o appendString:@": it sounded"];
            if (pk <= 0 && !_probedThis) [o appendString:@". Press \"Why silent?\" (it also runs by itself once you stop the pattern) for [probe] lines that say which part of the host set-up it needs"];
        }
    } else {
        uint32_t fb = G.fedBlocks.load();
        [o appendString:NSF("\n[notes] %s: an effect, no notes sent; the test sound ran through it for %u block(s), output peak %.3f%s", nm, fb, pk,
         fb == 0 ? " (not played: play the pattern to test it)" : (pk <= 0 ? " (SILENT although the test sound was fed into it)" : ""))];
    }
    // 0.7: loudness: the plug-in's own output, and the app's safety limiter
    if (G.blocks.load() > 0) {
        uint64_t ob = G.overBlocks.load();
        float own = G.ownPeak.load();
        std::string lim = fmt("the app's safety limiter engaged %llu time(s)%s; the app's output peak %.3f (%+.1f dBFS), never past full scale",
                              (unsigned long long)G.lim.engaged.load(), G.lim.engaged.load() ? fmt(" (most %.1f dB of gain reduction)", G.lim.deepestDb.load()).c_str() : "", pk, 20 * std::log10(std::max(pk, 1e-9f)));
        if (ob > 0)
            [o appendString:NSF("\n[level] %s: its own output passed 0 dBFS in %llu of %llu blocks, peak %+.1f dBFS (first at %s, last at %s); %s", nm, (unsigned long long)ob, (unsigned long long)G.blocks.load(),
                                20 * std::log10(std::max(G.overPeak.load(), 1e-9f)), [self clockText:G.overFirstT.load()].c_str(), [self clockText:G.overLastT.load()].c_str(), lim.c_str())];
        else
            [o appendString:NSF("\n[level] %s: its own output stayed at or below 0 dBFS (peak %+.1f dBFS); %s", nm, own > 0 ? 20 * std::log10(own) : -144.0, lim.c_str())];
    }
    if (_diagBtn.state == NSControlStateValueOn) {
        std::string t = diagText(nm, G.plug->diag());
        size_t cut = t.rfind("[diag]");
        std::string last = t.substr(cut); while (!last.empty() && last.back() == '\n') last.pop_back();
        [o appendString:NSF("\n%s", last.c_str())];
        std::vector<uint8_t> st; if (G.plug->getState(st) && st.size() != _loadStateBytes)
            [o appendString:NSF("\n[state] %s: its state is now %zu bytes (%zu when loaded): a preset or patch was loaded or changed since", nm, st.size(), _loadStateBytes)];
    }
    return o;
}
- (void)flushPlugSummary { NSString* p = [self plugSummary]; if (p.length) [self say:p]; }

// ---- 0.5: factory presets and the silence probe ---------------------------------------------------------
- (void)presetChosen:(id)s {
    NSInteger i = _presetPop.indexOfSelectedItem - 1;
    if (!G.plug || i < 0 || i >= (NSInteger)_presets.size()) return;
    std::string err; bool ok;
    { std::lock_guard<std::mutex> g(G.lock); ok = G.plug->loadPreset(_presets[i], err); }
    [self say:NSF("[preset] %s: \"%s\" (%s) %s%s", _loaded.c_str(), _presets[i].name.c_str(), _presets[i].source.c_str(), ok ? "loaded" : "NOT loaded: ", ok ? "" : err.c_str())];
}
- (void)probe:(id)s {
    if (!G.plug || _loadedInfo.path.empty()) { [self say:@"[probe] load a plug-in first"]; return; }
    if (_probing) return;
    _probing = YES; _probedThis = YES; _probeBtn.enabled = NO;
    gEvents.push(evProbe, 0);
    _status.stringValue = NSF("Probing %s (about 10 to 40 s)", _loaded.c_str());
    [self say:NSF("[probe] %s: loading it again in a separate process and playing it under several host set-ups at %.0f Hz (your sound keeps playing meanwhile)", _loaded.c_str(), G.sr)];
    std::string exe = U(NSBundle.mainBundle.executablePath);
    PluginInfo pi = _loadedInfo; double sr = G.sr; std::string name = _loaded;
    std::string out = U([NSTemporaryDirectory() stringByAppendingPathComponent:[NSString stringWithFormat:@"audiolab-probe-%d.json", (int)getpid()]]);
    __weak App* me = self;
    dispatch_async(dispatch_get_global_queue(QOS_CLASS_USER_INITIATED, 0), ^{
        std::string err;
        std::string text = probeOutOfProcess(exe, pi, sr, 512, out, 200, err);
        dispatch_async(dispatch_get_main_queue(), ^{ [me probeDone:text error:err name:name]; });
    });
}
- (void)probeDone:(std::string)text error:(std::string)err name:(std::string)name {
    _probing = NO; _probeBtn.enabled = YES;
    for (NSString* l in [S(text) componentsSeparatedByString:@"\n"]) if (l.length) [self say:l];
    if (!err.empty()) [self say:NSF("[probe] %s: %s", name.c_str(), err.c_str())];
    _status.stringValue = NSF("Probe of %s done: see the report", name.c_str());
    if (_selftest && !_selfProbe.empty()) [self selftestEnd];
}
- (void)showReport:(id)s { [self writeReport]; [NSWorkspace.sharedWorkspace selectFile:[self reportPath] inFileViewerRootedAtPath:@""]; }
- (void)copyReport:(id)s {
    [self writeReport];
    NSString* full = [S(_report) stringByAppendingString:[self liveFigures]];
    [NSPasteboard.generalPasteboard clearContents]; [NSPasteboard.generalPasteboard setString:full forType:NSPasteboardTypeString];
    _status.stringValue = @"Report copied";
}

// ---- self test (used by the build machine, which has nobody to click) ---------------------------------
- (void)selftestStart {
    int pick = -1;
    for (int i = 0; i < (int)_rows.size(); i++) { if (!_rows[i].ok) continue; if (!_selfName.empty() ? _rows[i].name == _selfName : _rows[i].instrument) { pick = i; break; } }
    if (pick < 0) for (int i = 0; i < (int)_rows.size(); i++) if (_rows[i].ok) { pick = i; break; }
    if (pick < 0) { [self say:@"[selftest] no plug-in to load"]; [self selftestEnd]; return; }
    // the search: case and accents do not matter, every word must match name, maker or kind
    NSString* q = S(_rows[pick].name); q = [q.uppercaseString stringByReplacingOccurrencesOfString:@"U" withString:@"\u00DC"];
    for (NSString* t in @[q, @"instrument", @"effect", @"zzzz-nothing"]) {
        _search.stringValue = t; [self refilter];
        [self say:NSF("[selftest] search \"%s\": %s, first: %s", U(t).c_str(), U(_countLbl.stringValue).c_str(), _table.selectedRow >= 0 ? _rows[[self plugIndexAtViewRow:_table.selectedRow]].name.c_str() : "(none)")];
    }
    [_sortPop selectItemAtIndex:2]; _search.stringValue = @""; [self refilter];
    int heads = 0; for (auto& v : _view) if (v.idx < 0) heads++;
    [self say:[NSString stringWithFormat:@"[selftest] grouped by maker: %d group heading(s), %zu rows", heads, _view.size()]];
    [_sortPop selectItemAtIndex:0]; [self refilter];
    for (NSInteger r = 0; r < (NSInteger)_view.size(); r++) if (_view[r].idx == pick) { [_table selectRowIndexes:[NSIndexSet indexSetWithIndex:r] byExtendingSelection:NO]; [_table scrollRowToVisible:r]; }
    BOOL ok = [self loadRow:pick];
    [self say:NSF("[selftest] load %s", ok ? "ok" : "FAILED")];
    // 0.7: parameters set by name (the test instrument's loud and sneaky modes), and the "Use the deepest format" item
    for (auto& kv : _selfSets) {
        size_t eq = kv.rfind('='); std::string name = kv.substr(0, eq); double v = eq == std::string::npos ? 1.0 : atof(kv.substr(eq + 1).c_str());
        int64_t id = -1; for (auto& pn : _paramNames) if (pn.second == name) id = pn.first;
        if (id >= 0 && G.plug) G.plug->setParam((uint32_t)id, v);
        [self say:NSF("[selftest] set \"%s\" = %.2f: %s", name.c_str(), v, id >= 0 ? "done" : "no such parameter")];
    }
    if (_selfDeepest) [self useDeepestFormat:nil];
    __weak App* me = self;
    dispatch_after(dispatch_time(DISPATCH_TIME_NOW, (int64_t)(1.0 * NSEC_PER_SEC)), dispatch_get_main_queue(), ^{
        [me openEditor:nil]; [me togglePattern:nil];
        dispatch_after(dispatch_time(DISPATCH_TIME_NOW, (int64_t)(5.0 * NSEC_PER_SEC)), dispatch_get_main_queue(), ^{
            [me say:@"[selftest] five seconds of the pattern played"];
            [me selftestDrags];
            [me writeMarker:@"ready-for-screenshot"];
            dispatch_after(dispatch_time(DISPATCH_TIME_NOW, (int64_t)(6.0 * NSEC_PER_SEC)), dispatch_get_main_queue(), ^{ [me togglePattern:nil]; [me selftestProbeOrEnd]; });
        });
    });
}
// Drags with the mouse over a grid of points in the plug-in's window, as a person turning knobs would
// (events sent to the window by the app itself; a JUCE plug-in such as Surge XT turns its knobs on them).
- (void)selftestDrags {
    if (!_plugWin) { [self say:@"[selftest] no plug-in window to drag in"]; return; }
    NSView* v = _plugWin.contentView; NSRect b = v.bounds; NSInteger wn = _plugWin.windowNumber;
    int before = G.plug ? G.plug->editStats().performs : 0;
    auto ev = [&](NSEventType t, NSPoint p) {
        NSEvent* e = [NSEvent mouseEventWithType:t location:p modifierFlags:0 timestamp:NSProcessInfo.processInfo.systemUptime windowNumber:wn context:nil eventNumber:0 clickCount:1 pressure:t == NSEventTypeLeftMouseUp ? 0 : 1];
        if (e) [NSApp sendEvent:e];
    };
    for (int gy = 1; gy <= 4; gy++) for (int gx = 1; gx <= 6; gx++) {
        NSPoint p = NSMakePoint(b.size.width * gx / 7, b.size.height * gy / 5);
        ev(NSEventTypeLeftMouseDown, p);
        for (int k = 1; k <= 4; k++) ev(NSEventTypeLeftMouseDragged, NSMakePoint(p.x, p.y + 6 * k));
        ev(NSEventTypeLeftMouseUp, NSMakePoint(p.x, p.y + 24));
    }
    // JUCE hands the moves to the host a moment later, from its message loop: count after half a second
    __weak App* me = self;
    dispatch_after(dispatch_time(DISPATCH_TIME_NOW, (int64_t)(0.5 * NSEC_PER_SEC)), dispatch_get_main_queue(), ^{
        int after = G.plug ? G.plug->editStats().performs : 0;
        [me say:[NSString stringWithFormat:@"[selftest] 24 drags in the plug-in's window: %d parameter move(s) reached the host", after - before]];
    });
}
- (void)selftestProbeOrEnd { if (_selfProbe.empty()) [self selftestEnd]; else { [self flushPlugSummary]; [self probe:nil]; } }
- (void)writeMarker:(NSString*)name { [@"1" writeToFile:[S(_selfOut) stringByAppendingPathComponent:name] atomically:YES encoding:NSUTF8StringEncoding error:nil]; }
- (void)selftestEnd { [self say:@"[selftest] end"]; [self writeMarker:@"done"]; [NSApp terminate:nil]; }
@end

int main(int argc, char** argv) {
    int code = 0;
    if (scannerChildMain(argc, argv, code)) return code;     // this same program is the scanner child
    // ... and the silence probe's child: the plug-in on its main thread, with the run loop turning between blocks
    if (probeChildMain(argc, argv, code, [](double s) { @autoreleasepool { if (s > 0) CFRunLoopRunInMode(kCFRunLoopDefaultMode, s, false); else CFRunLoopRunInMode(kCFRunLoopDefaultMode, 0, true); } })) return code;
    @autoreleasepool {
        NSApplication* app = [NSApplication sharedApplication];
        [app setActivationPolicy:NSApplicationActivationPolicyRegular];
        App* d = [App new];
        app.delegate = d;
        [app run];
    }
    return 0;
}
