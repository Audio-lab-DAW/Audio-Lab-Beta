// AudioLab VST3 test (task NM1, test C). A small native Mac app, not the DAW:
// it lists the VST3 plug-ins found on this Mac (each bundle is scanned in a separate process), loads one,
// opens the plug-in's own window, plays notes from the computer keyboard or a test pattern through the
// chosen output device (Core Audio, straight on the device), and writes a report file.
// 0.4 (task NL4): a search over the list (name, maker, kind; Cmd+F, Escape), sort and group by maker, a kind
// filter, recently loaded plug-ins on top; parameter moves from a plug-in's own window counted and logged per
// plug-in; notes sent to each instrument logged; a warning when the output runs at 16 kHz or less (Bluetooth call mode).
#import <Cocoa/Cocoa.h>
#include "../common/coreaudio.h"
#include "../host/plugin_api.h"
#include <algorithm>
#include <atomic>
#include <cmath>
#include <mutex>
#include <string>
#include <unordered_map>
#include <sys/sysctl.h>
#include <time.h>
#include <vector>

using namespace al;

static NSString* S(const std::string& s) { return [NSString stringWithUTF8String:s.c_str()] ?: @""; }
static std::string U(NSString* s) { return s ? std::string([s UTF8String]) : std::string(); }

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
    std::atomic<uint32_t> notesPattern{0}, notesKeys{0}, fedBlocks{0};   // note-ons that reached the plug-in; blocks of test sound fed to an effect
    void pushNote(int pitch, bool on) { uint32_t w = noteW.load(); notes[w & 255] = {pitch, on}; noteW.store(w + 1); }
};
static Engine G;

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
        uint64_t t0 = clock_gettime_nsec_np(CLOCK_UPTIME_RAW);
        bool ok = G.plug->process(inp, 2, out, 2, frames, ev, n, c);
        uint64_t ns = clock_gettime_nsec_np(CLOCK_UPTIME_RAW) - t0;
        G.blocks++; G.sumNs += ns; if (ns > G.worstNs) G.worstNs = ns;
        G.budgetNs = (uint64_t)(frames / G.sr * 1e9);
        if (!ok) G.failed++;
        float pk = G.peak.load();
        for (int i = 0; i < frames; i++) {
            for (int ch = 0; ch < 2; ch++) {
                float v = out[ch][i] * 0.5f;                        // half level, and never above full scale: this is a test of unknown plug-ins
                if (!(v == v)) v = 0;
                if (v > 1) v = 1; else if (v < -1) v = -1;
                out[ch][i] = v;
                float a = v < 0 ? -v : v; if (a > pk) pk = a;
            }
        }
        G.peak.store(pk);
        G.pos += frames;
    }
    G.lock.unlock();
}

// ---- the window --------------------------------------------------------------------------------------
struct Row { std::string name, vendor, kind, status, path, uid, archs; bool ok = false, instrument = false; };
// what the table shows: a plug-in (idx into _rows) or a group heading (idx -1)
struct ViewRow { int idx = -1; std::string heading; };
static NSString* fold(NSString* s) { return [s stringByFoldingWithOptions:NSCaseInsensitiveSearch | NSDiacriticInsensitiveSearch locale:nil] ?: @""; }

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
}

- (void)say:(NSString*)line {
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
    NSString* full = [S(_report) stringByAppendingString:[self liveFigures]];
    [full writeToFile:[self reportPath] atomically:YES encoding:NSUTF8StringEncoding error:nil];
}
- (NSString*)liveFigures {
    NSString* a = [self audioFigures];
    NSString* p = [self plugSummary];
    return p.length ? [NSString stringWithFormat:@"%@%@\n", a, p] : a;
}
- (NSString*)audioFigures {
    uint64_t b = G.blocks.load();
    if (!b) return @"\n[audio] no audio block has run through a plug-in yet\n";
    double avg = G.sumNs.load() / 1000.0 / b, worst = G.worstNs.load() / 1000.0, budget = G.budgetNs.load() / 1000.0;
    return [NSString stringWithFormat:@"\n[audio] plug-in %s: %llu blocks, average %.1f microseconds per block (%.2f %% of the block), worst %.1f (%.1f %%), block lasts %.0f microseconds, failed blocks %llu, overloads reported by the device %llu, device callbacks %llu, frames per callback %u to %u, peak level %.3f\n",
            _loaded.c_str(), b, avg, budget ? avg / budget * 100 : 0, worst, budget ? worst / budget * 100 : 0, budget, G.failed.load(), _stream.overloads.load(), _stream.callbacks.load(),
            _stream.callbacks.load() ? _stream.minFrames.load() : 0, _stream.maxFrames.load(), G.peak.load()];
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
    }
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
    [self button:@"Show report file" action:@selector(showReport:) frame:NSMakeRect(W - 300, 208, 140, 30)];
    [self button:@"Copy report" action:@selector(copyReport:) frame:NSMakeRect(W - 156, 208, 140, 30)];
    [self label:@"Keys A W S E D F T G Y H U J K play notes, C to C (click the list first, not the search field). Sound comes out at half level." frame:NSMakeRect(16, 184, W - 32, 18)];
    _cpu = [self label:@"" frame:NSMakeRect(16, 162, W - 32, 18)];
    _cpu.font = [NSFont monospacedDigitSystemFontOfSize:12 weight:NSFontWeightRegular];

    NSScrollView* lv = [[NSScrollView alloc] initWithFrame:NSMakeRect(16, 16, W - 32, 138)]; lv.hasVerticalScroller = YES; lv.borderType = NSBezelBorder;
    _log = [[NSTextView alloc] initWithFrame:lv.bounds]; _log.editable = NO; _log.autoresizingMask = NSViewWidthSizable; lv.documentView = _log; [_win.contentView addSubview:lv];
    [_win makeKeyAndOrderFront:nil];
    [NSApp activateIgnoringOtherApps:YES];

    __weak App* me = self;
    [NSEvent addLocalMonitorForEventsMatchingMask:NSEventMaskKeyDown | NSEventMaskKeyUp handler:^NSEvent*(NSEvent* e) { return [me key:e] ? nil : e; }];
    // the mouse in the plug-in's own window: counted, so the report can say "knobs were touched but no move reached the host"
    [NSEvent addLocalMonitorForEventsMatchingMask:NSEventMaskLeftMouseDown | NSEventMaskRightMouseDown | NSEventMaskLeftMouseDragged | NSEventMaskScrollWheel handler:^NSEvent*(NSEvent* e) { [me plugMouse:e]; return e; }];
    [NSTimer scheduledTimerWithTimeInterval:0.25 repeats:YES block:^(NSTimer* t) { [me tick]; }];

    gApp = self;
    _watch.start(watchCb, nullptr);
    [self machineInfo];
    [self loadDevices];
    [self scan:nil];
}

- (void)machineInfo {
    char model[128] = {0}, cpu[128] = {0}; size_t l = sizeof model; sysctlbyname("hw.model", model, &l, nullptr, 0); l = sizeof cpu; sysctlbyname("machdep.cpu.brand_string", cpu, &l, nullptr, 0);
    [self say:@"AudioLab VST3 test 0.4 (tasks NM1, NB-N1 and NL4). Report file: paste all of it back."];
    [self say:[NSString stringWithFormat:@"[machine] %s, %s, macOS %@, this app runs as %s", model, cpu, NSProcessInfo.processInfo.operatingSystemVersionString, hostArch().c_str()]];
}

- (void)loadDevices {
    _devs.clear(); [_devPop removeAllItems];
    uint32_t def = defaultOutputDevice(); int sel = -1;
    for (auto& d : listDevices()) {
        std::string rates; for (double r : d.rates) rates += (rates.empty() ? "" : " ") + std::to_string((int)r);
        for (auto& rr : d.rateRanges) rates += (rates.empty() ? "" : " ") + std::to_string((int)rr.first) + "-" + std::to_string((int)rr.second);
        [self say:[NSString stringWithFormat:@"[device] %s (%s, %s): out %d ch, in %d ch, now %.0f Hz, rates offered: %s, rate can be set: %s, buffer %u (range %u to %u), volume the computer can set: %s%s, format on the wire: %s (%d formats offered), exclusive use can be taken: %s%s",
                   d.name.c_str(), d.manufacturer.c_str(), d.transport.c_str(), d.outChannels, d.inChannels, d.rate, rates.c_str(), d.rateSettable ? "yes" : "no", d.buffer, d.bufferMin, d.bufferMax,
                   d.hasVolume ? (d.volumeSettable ? "yes" : "has one but fixed") : "no", d.hasVolume ? (" (" + d.volumeWhere + ")").c_str() : "", d.physicalFormat.c_str(), d.physicalFormats, d.hogSettable ? "yes" : "no", d.isDefaultOutput ? ", DEFAULT OUTPUT" : ""]];
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
- (void)startDevice:(const DeviceInfo&)d0 {
    // ask the device again: a list made when the device was plugged in can hold the rate it had for a moment only
    DeviceInfo d = deviceInfo(d0.id); if (!d.id) d = d0;
    _stream.stop();
    if (_hog && _dev && _dev != d.id) { int o; std::string e; setHog(_dev, false, o, e); _hog = NO; }
    { std::lock_guard<std::mutex> g(G.lock); G.sr = d.rate > 0 ? d.rate : 48000; if (G.plug) { std::string e; G.ready = G.plug->prepare(G.sr, G.maxBlock, false, e); } }
    _dev = d.id;
    std::string err;
    bool ok = _stream.start(d.id, renderCb, nullptr, err);
    DeviceInfo now = d; for (auto& x : listDevices()) if (x.id == d.id) now = x;
    NSString* item = [NSString stringWithFormat:@"%u", now.buffer]; if ([_bufPop itemWithTitle:item]) [_bufPop selectItemWithTitle:item];
    [self say:[NSString stringWithFormat:@"[output] %s: %s, %.0f Hz, buffer %u frames (%.2f ms), device latency %u + safety %u + stream %u frames%s", d.name.c_str(), ok ? "opened" : "COULD NOT BE OPENED", now.rate, now.buffer,
               now.rate ? now.buffer / now.rate * 1000 : 0, now.latency, now.safetyOffset, now.streamLatency, ok ? "" : (" (" + err + ")").c_str()]];
    _watch.watchDevice(d.id);
    [self fillControls:now];
    [self checkOutput:now];
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
    if (w.empty()) { _warn.stringValue = [NSString stringWithFormat:@"Output %s at %.0f Hz.", d.name.c_str(), d.rate]; _warn.textColor = NSColor.secondaryLabelColor; _warn.toolTip = nil; return; }
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
    _volLbl.stringValue = has ? [NSString stringWithFormat:@"%.0f %%%s", v * 100, d.volumeSettable ? "" : " (fixed)"] : @"this device has none";
}
- (void)rateChanged:(id)s {
    double want = _ratePop.titleOfSelectedItem.doubleValue, now = 0; std::string err;
    _stream.stop();
    bool ok = setDeviceRate(_dev, want, now, err);
    [self say:[NSString stringWithFormat:@"[rate] asked for %.0f Hz: %s, the device now runs %.0f Hz%s", want, ok ? "switched" : "NOT switched", now, err.empty() ? "" : (" " + err).c_str()]];
    [self startDevice:deviceInfo(_dev)];
}
- (void)exclChanged:(id)s {
    bool on = _exclBtn.state == NSControlStateValueOn; int owner = -1; std::string err;
    bool ok = setHog(_dev, on, owner, err); _hog = on && ok;
    [self say:[NSString stringWithFormat:@"[exclusive] %s: %s (the device is now held by process %d, this app is %d)%s. While it is on, no other program can play through this device.", on ? "asked for exclusive use" : "gave exclusive use back", ok ? "done" : "NOT done", owner, (int)getpid(), err.empty() ? "" : (" " + err).c_str()]];
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
        for (auto& d : listDevices()) { if (d.outChannels < 1) continue; if (d.id == _dev) { here = true; sel = (int)outs.size(); } outs.push_back(d); }
        if (_dev) [self checkOutput:deviceInfo(_dev)];
        if (outs.size() == _devs.size() && here) { bool same = true; for (size_t i = 0; i < outs.size(); i++) if (outs[i].id != _devs[i].id) same = false; if (same) return; }
        _devs = outs; [_devPop removeAllItems];
        for (auto& d : _devs) [_devPop addItemWithTitle:S(d.name + "  (" + std::to_string((int)d.rate) + " Hz)")];
        std::string names; for (auto& d : _devs) names += (names.empty() ? "" : ", ") + d.name;
        [self say:[NSString stringWithFormat:@"[devices] the list changed: %zu output(s) now: %s", _devs.size(), names.c_str()]];
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
    bool ok = setDeviceBuffer(_dev, want, now, err);
    double sr = G.sr;
    [self say:[NSString stringWithFormat:@"[buffer] asked for %u frames: %s, the device now runs %u frames (%.2f ms at %.0f Hz)%s", want, ok ? "accepted" : "not accepted", now, sr ? now / sr * 1000 : 0, sr, err.empty() ? "" : (" " + err).c_str()]];
    G.blocks = 0; G.sumNs = 0; G.worstNs = 0; _stream.minFrames = 0xffffffffu; _stream.maxFrames = 0;
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
        [self say:[NSString stringWithFormat:@"[scan] PROBLEM %s [%s]: %s", r.path.c_str(), r.archs.c_str(), r.error.c_str()]];
    }
    for (auto& p : r.plugins) {
        Row row; row.name = p.name; row.vendor = p.vendor; row.kind = p.isInstrument ? "instrument" : "effect"; row.instrument = p.isInstrument; row.ok = true; row.path = r.path; row.uid = p.uid; row.archs = r.archs;
        row.status = "found (" + (r.archs.empty() ? std::string("?") : r.archs) + ", version " + p.version + ")";
        _rows.push_back(row);
        [self say:[NSString stringWithFormat:@"[scan] found %s by %s, %s, version %s [%s] in %s (%.2f s)", p.name.c_str(), p.vendor.c_str(), row.kind.c_str(), p.version.c_str(), r.archs.c_str(), file.c_str(), r.seconds]];
    }
    _status.stringValue = [NSString stringWithFormat:@"Scanning plug-ins: %d of %d", i, n];
    [self refilter];
}
- (void)scanDone:(int)n folders:(std::vector<std::string>)folders {
    int ok = 0, plugs = 0; for (auto& r : _scan) { if (r.ok) ok++; plugs += (int)r.plugins.size(); }
    _bundles = n; _bundlesOk = ok;
    std::string fl; for (auto& f : folders) fl += (fl.empty() ? "" : ", ") + f;
    [self say:[NSString stringWithFormat:@"[scan] done: %d bundle(s) in %s; %d could be read, %d could not; %d plug-in(s). The app itself was never at risk: every bundle was opened in a separate process.", n, fl.c_str(), ok, n - ok, plugs]];
    _status.stringValue = [NSString stringWithFormat:@"%d plug-in(s) found", plugs];
    _scanBtn.enabled = YES;
    if (_selftest) {     // leave the main window alone for two seconds so the build machine can take a picture of it
        [self writeMarker:@"scanned"];
        __weak App* me = self;
        dispatch_after(dispatch_time(DISPATCH_TIME_NOW, (int64_t)(2.5 * NSEC_PER_SEC)), dispatch_get_main_queue(), ^{ [me selftestStart]; });
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
    if (!x.ok) { [self say:[NSString stringWithFormat:@"[load] %s cannot be loaded: %s", x.name.c_str(), x.status.c_str()]]; return NO; }
    [self closePlugWindow];
    [self flushPlugSummary];
    { std::lock_guard<std::mutex> g(G.lock); G.ready = false; G.plug.reset(); }
    PluginInfo pi; pi.format = "vst3"; pi.path = x.path; pi.uid = x.uid; pi.name = x.name;
    std::string err;
    CFAbsoluteTime t0 = CFAbsoluteTimeGetCurrent();
    std::unique_ptr<PluginInstance> p = vst3Format()->create(pi, err);
    double ms = (CFAbsoluteTimeGetCurrent() - t0) * 1000;
    if (!p) { x.status = "FAILED to load: " + err; [_table reloadData]; [self say:[NSString stringWithFormat:@"[load] FAILED %s: %s", x.name.c_str(), err.c_str()]]; return NO; }
    BusLayout b = p->buses();
    bool inst = p->info().isInstrument && b.eventIns > 0;
    bool ok = p->prepare(G.sr, G.maxBlock, false, err);
    auto ps = p->params();
    std::vector<uint8_t> st; bool gotState = p->getState(st);
    int lat = p->latencySamples();
    std::string names; for (size_t i = 0; i < ps.size() && i < 8; i++) names += (i ? ", " : "") + ps[i].name;
    [self say:[NSString stringWithFormat:@"[load] %s %s in %.0f ms: %s, audio in %d ch, out %d ch, note inputs %d, %zu parameters (first: %s), state %s (%zu bytes), latency %d samples%s",
               x.name.c_str(), ok ? "loaded" : "loaded but could not be started", ms, inst ? "instrument" : "effect", b.mainInChannels, b.mainOutChannels, b.eventIns, ps.size(), names.c_str(), gotState ? "saved" : "NOT saved", st.size(), lat,
               ok ? "" : (" (" + err + ")").c_str()]];
    x.status = ok ? "loaded" : "FAILED to start: " + err;
    _paramNames.clear(); for (auto& q : ps) _paramNames[q.id] = q.name;
    _plugMouse = 0; _plugDrags = 0; _lastMoves = 0; _windowOpened = NO; _firstMoveLogged = NO;
    G.blocks = 0; G.sumNs = 0; G.worstNs = 0; G.failed = 0; G.peak = 0; G.notesPattern = 0; G.notesKeys = 0; G.fedBlocks = 0;
    { std::lock_guard<std::mutex> g(G.lock); G.plug = std::move(p); G.instrument = inst; G.ready = ok; G.patStep = -1; G.patNote = -1; }
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
    if (!ok) { [self say:[NSString stringWithFormat:@"[window] %s: no window (%s)", _loaded.c_str(), err.c_str()]]; _plugWin = nil; return; }
    if (w > 0 && h > 0) [_plugWin setContentSize:NSMakeSize(w, h)];
    // next to the main window if there is room, otherwise wherever it fits on the screen
    NSRect mf = _win.frame, vis = (_win.screen ?: NSScreen.mainScreen).visibleFrame, pf = _plugWin.frame;
    CGFloat x = NSMaxX(mf) + 12; if (x + pf.size.width > NSMaxX(vis)) x = NSMaxX(vis) - pf.size.width; if (x < NSMinX(vis)) x = NSMinX(vis);
    CGFloat top = NSMaxY(mf); if (top - pf.size.height < NSMinY(vis)) top = NSMinY(vis) + pf.size.height; if (top > NSMaxY(vis)) top = NSMaxY(vis);
    [_plugWin setFrameTopLeftPoint:NSMakePoint(x, top)];
    [_plugWin makeKeyAndOrderFront:nil];
    _windowOpened = YES;
    [self say:[NSString stringWithFormat:@"[window] %s: its own window is open, %d x %d", _loaded.c_str(), w, h]];
}
- (void)closePlugWindow {
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
    _patBtn.title = on ? @"Stop test pattern" : @"Play test pattern";
    [self say:on ? @"[pattern] test pattern on" : [@"[pattern] test pattern off. " stringByAppendingString:[[self liveFigures] stringByTrimmingCharactersInSet:NSCharacterSet.newlineCharacterSet]]];
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
    EditStats es; if (G.plug) es = G.plug->editStats();
    if (G.plug && es.performs > 0 && !_firstMoveLogged) {
        _firstMoveLogged = YES;
        [self say:[NSString stringWithFormat:@"[param] %s: first move from its window: %s", _loaded.c_str(), [self paramDesc:es.lastId value:es.lastValue].c_str()]];
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
- (void)plugMouse:(NSEvent*)e {
    if (!_plugWin || e.window != _plugWin) return;
    if (e.type == NSEventTypeLeftMouseDragged) _plugDrags++; else _plugMouse++;
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
    NSString* restarts = es.restarts ? [NSString stringWithFormat:@"; it asked the host to restart %d time(s), %d of them because all its values changed", es.restarts, es.valueRestarts] : @"";
    if (es.performs > 0)
        [o appendFormat:@"[param] %s: %d moves from its window (gestures begun %d, ended %d), last: %s%@", nm, es.performs, es.begins, es.ends, [self paramDesc:es.lastId value:es.lastValue].c_str(), restarts];
    else if (_plugMouse + _plugDrags > 0)
        [o appendFormat:@"[param] %s: NO parameter moves reached the host from its window, although the mouse was used in it %d time(s) (%d click(s) or scroll(s), %d drag step(s)); gestures begun %d%@. If you turned knobs, this plug-in does not tell the host about them (or not through VST3's component handler)", nm, _plugMouse + _plugDrags, _plugMouse, _plugDrags, es.begins, restarts];
    else if (_windowOpened)
        [o appendFormat:@"[param] %s: no moves from its window (the mouse was not used in it)%@", nm, restarts];
    else
        [o appendFormat:@"[param] %s: its window was not opened, so no moves from it%@", nm, restarts];
    uint32_t np = G.notesPattern.load(), nk = G.notesKeys.load();
    float pk = G.peak.load();
    if (G.instrument) {
        [o appendFormat:@"\n[notes] %s: %u notes sent (%u from the test pattern, %u from the keys), output peak %.3f", nm, np + nk, np, nk, pk];
        if (np + nk == 0) [o appendString:@": no notes were sent to it"];
        else if (pk <= 0) {
            if (G.sr < 44100) [o appendFormat:@": SILENT although the notes reached it. The output runs at %.0f Hz; some instruments make no sound at such a low rate (Pigments played at 44.1 kHz in an earlier report and was silent at 16 kHz; Surge XT and mda JX10 do sound at 16 kHz). Choose an output at 44.1 kHz or more and play again", G.sr];
            else [o appendString:@": SILENT although the notes reached it. Check its patch (an empty start patch makes no sound) and its own volume"];
        } else [o appendString:@": it sounded"];
    } else {
        uint32_t fb = G.fedBlocks.load();
        [o appendFormat:@"\n[notes] %s: an effect, no notes sent; the test sound ran through it for %u block(s), output peak %.3f%s", nm, fb, pk,
         fb == 0 ? " (silence is expected: nothing was fed into it; play the test pattern while it is loaded)" : (pk <= 0 ? " (SILENT although the test sound was fed into it)" : "")];
    }
    return o;
}
- (void)flushPlugSummary { NSString* p = [self plugSummary]; if (p.length) [self say:p]; }
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
        [self say:[NSString stringWithFormat:@"[selftest] search \"%@\": %@, first: %s", t, _countLbl.stringValue, _table.selectedRow >= 0 ? _rows[[self plugIndexAtViewRow:_table.selectedRow]].name.c_str() : "(none)"]];
    }
    [_sortPop selectItemAtIndex:2]; _search.stringValue = @""; [self refilter];
    int heads = 0; for (auto& v : _view) if (v.idx < 0) heads++;
    [self say:[NSString stringWithFormat:@"[selftest] grouped by maker: %d group heading(s), %zu rows", heads, _view.size()]];
    [_sortPop selectItemAtIndex:0]; [self refilter];
    for (NSInteger r = 0; r < (NSInteger)_view.size(); r++) if (_view[r].idx == pick) { [_table selectRowIndexes:[NSIndexSet indexSetWithIndex:r] byExtendingSelection:NO]; [_table scrollRowToVisible:r]; }
    BOOL ok = [self loadRow:pick];
    [self say:[NSString stringWithFormat:@"[selftest] load %s", ok ? "ok" : "FAILED"]];
    __weak App* me = self;
    dispatch_after(dispatch_time(DISPATCH_TIME_NOW, (int64_t)(1.0 * NSEC_PER_SEC)), dispatch_get_main_queue(), ^{
        [me openEditor:nil]; [me togglePattern:nil];
        dispatch_after(dispatch_time(DISPATCH_TIME_NOW, (int64_t)(5.0 * NSEC_PER_SEC)), dispatch_get_main_queue(), ^{
            [me say:@"[selftest] five seconds of the pattern played"];
            [me selftestDrags];
            [me writeMarker:@"ready-for-screenshot"];
            dispatch_after(dispatch_time(DISPATCH_TIME_NOW, (int64_t)(6.0 * NSEC_PER_SEC)), dispatch_get_main_queue(), ^{ [me togglePattern:nil]; [me selftestEnd]; });
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
- (void)writeMarker:(NSString*)name { [@"1" writeToFile:[S(_selfOut) stringByAppendingPathComponent:name] atomically:YES encoding:NSUTF8StringEncoding error:nil]; }
- (void)selftestEnd { [self say:@"[selftest] end"]; [self writeMarker:@"done"]; [NSApp terminate:nil]; }
@end

int main(int argc, char** argv) {
    int code = 0;
    if (scannerChildMain(argc, argv, code)) return code;     // this same program is the scanner child
    @autoreleasepool {
        NSApplication* app = [NSApplication sharedApplication];
        [app setActivationPolicy:NSApplicationActivationPolicyRegular];
        App* d = [App new];
        app.delegate = d;
        [app run];
    }
    return 0;
}
