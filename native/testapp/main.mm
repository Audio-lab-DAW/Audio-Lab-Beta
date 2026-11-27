// AudioLab VST3 test (task NM1, test C). A small native Mac app, not the DAW:
// it lists the VST3 plug-ins found on this Mac (each bundle is scanned in a separate process), loads one,
// opens the plug-in's own window, plays notes from the computer keyboard or a test pattern through the
// chosen output device (Core Audio, straight on the device), and writes a report file.
#import <Cocoa/Cocoa.h>
#include "../common/coreaudio.h"
#include "../host/plugin_api.h"
#include <atomic>
#include <cmath>
#include <mutex>
#include <string>
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
    void pushNote(int pitch, bool on) { uint32_t w = noteW.load(); notes[w & 255] = {pitch, on}; noteW.store(w + 1); }
};
static Engine G;

static void renderCb(void*, float** out, int, int frames) {
    memset(out[0], 0, sizeof(float) * frames); memset(out[1], 0, sizeof(float) * frames);
    if (!G.lock.try_lock()) return;
    if (G.plug && G.ready && frames <= G.maxBlock) {
        NoteEvent ev[64]; int n = 0;
        uint32_t r = G.noteR.load(), w = G.noteW.load();
        while (r != w && n < 60) { ev[n].offset = 0; ev[n].on = G.notes[r & 255].on; ev[n].pitch = G.notes[r & 255].pitch; ev[n].velocity = 0.8f; ev[n].channel = 0; n++; r++; }
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

@interface App : NSObject <NSApplicationDelegate, NSTableViewDataSource, NSTableViewDelegate, NSWindowDelegate>
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

    const CGFloat W = 980, H = 640;
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
    NSScrollView* sv = [[NSScrollView alloc] initWithFrame:NSMakeRect(16, 250, W - 32, H - 340)]; sv.hasVerticalScroller = YES; sv.borderType = NSBezelBorder;
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
    [self label:@"Keys A W S E D F T G Y H U J K play notes, C to C (click this window first). Sound comes out at half level." frame:NSMakeRect(16, 184, W - 32, 18)];
    _cpu = [self label:@"" frame:NSMakeRect(16, 162, W - 32, 18)];
    _cpu.font = [NSFont monospacedDigitSystemFontOfSize:12 weight:NSFontWeightRegular];

    NSScrollView* lv = [[NSScrollView alloc] initWithFrame:NSMakeRect(16, 16, W - 32, 138)]; lv.hasVerticalScroller = YES; lv.borderType = NSBezelBorder;
    _log = [[NSTextView alloc] initWithFrame:lv.bounds]; _log.editable = NO; _log.autoresizingMask = NSViewWidthSizable; lv.documentView = _log; [_win.contentView addSubview:lv];
    [_win makeKeyAndOrderFront:nil];
    [NSApp activateIgnoringOtherApps:YES];

    __weak App* me = self;
    [NSEvent addLocalMonitorForEventsMatchingMask:NSEventMaskKeyDown | NSEventMaskKeyUp handler:^NSEvent*(NSEvent* e) { return [me key:e] ? nil : e; }];
    [NSTimer scheduledTimerWithTimeInterval:0.25 repeats:YES block:^(NSTimer* t) { [me tick]; }];

    gApp = self;
    _watch.start(watchCb, nullptr);
    [self machineInfo];
    [self loadDevices];
    [self scan:nil];
}

- (void)machineInfo {
    char model[128] = {0}, cpu[128] = {0}; size_t l = sizeof model; sysctlbyname("hw.model", model, &l, nullptr, 0); l = sizeof cpu; sysctlbyname("machdep.cpu.brand_string", cpu, &l, nullptr, 0);
    [self say:@"AudioLab VST3 test 0.2 (tasks NM1 and NB-N1). Report file: paste all of it back."];
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
- (void)startDevice:(const DeviceInfo&)d {
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
    _rows.clear(); _scan.clear(); [_table reloadData];
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
        Row row; row.name = file; row.status = "PROBLEM: " + r.error; row.path = r.path; row.archs = r.archs; _rows.push_back(row);
        [self say:[NSString stringWithFormat:@"[scan] PROBLEM %s [%s]: %s", r.path.c_str(), r.archs.c_str(), r.error.c_str()]];
    }
    for (auto& p : r.plugins) {
        Row row; row.name = p.name; row.vendor = p.vendor; row.kind = p.isInstrument ? "instrument" : "effect"; row.instrument = p.isInstrument; row.ok = true; row.path = r.path; row.uid = p.uid; row.archs = r.archs;
        row.status = "found (" + (r.archs.empty() ? std::string("?") : r.archs) + ", version " + p.version + ")";
        _rows.push_back(row);
        [self say:[NSString stringWithFormat:@"[scan] found %s by %s, %s, version %s [%s] in %s (%.2f s)", p.name.c_str(), p.vendor.c_str(), row.kind.c_str(), p.version.c_str(), r.archs.c_str(), file.c_str(), r.seconds]];
    }
    _status.stringValue = [NSString stringWithFormat:@"Scanning plug-ins: %d of %d", i, n];
    [_table reloadData];
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

- (NSInteger)numberOfRowsInTableView:(NSTableView*)t { return (NSInteger)_rows.size(); }
- (id)tableView:(NSTableView*)t objectValueForTableColumn:(NSTableColumn*)c row:(NSInteger)r {
    if (r < 0 || r >= (NSInteger)_rows.size()) return @"";
    const Row& x = _rows[r]; NSString* k = c.identifier;
    return S([k isEqualToString:@"name"] ? x.name : [k isEqualToString:@"vendor"] ? x.vendor : [k isEqualToString:@"kind"] ? x.kind : x.status);
}

- (void)load:(id)s {
    NSInteger r = _table.selectedRow;
    if (r < 0 || r >= (NSInteger)_rows.size()) { [self say:@"[load] pick a plug-in in the list first"]; return; }
    [self loadRow:(int)r];
}
- (BOOL)loadRow:(int)r {
    Row& x = _rows[r];
    if (!x.ok) { [self say:[NSString stringWithFormat:@"[load] %s cannot be loaded: %s", x.name.c_str(), x.status.c_str()]]; return NO; }
    [self closePlugWindow];
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
    x.status = ok ? "loaded" : "FAILED to start: " + err; [_table reloadData];
    G.blocks = 0; G.sumNs = 0; G.worstNs = 0; G.failed = 0; G.peak = 0;
    { std::lock_guard<std::mutex> g(G.lock); G.plug = std::move(p); G.instrument = inst; G.ready = ok; G.patStep = -1; G.patNote = -1; }
    _loaded = x.name;
    _status.stringValue = S("Loaded: " + x.name);
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
    [self writeReport];
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
    if (e.modifierFlags & (NSEventModifierFlagCommand | NSEventModifierFlagControl | NSEventModifierFlagOption)) return NO;
    if (e.window != _win) return NO;      // keys typed in the plug-in's own window belong to the plug-in
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
    uint64_t b = G.blocks.load();
    if (!b) { _cpu.stringValue = G.plug ? @"Loaded. Play the test pattern or press keys." : @"No plug-in loaded."; return; }
    double avg = G.sumNs.load() / 1000.0 / b, worst = G.worstNs.load() / 1000.0, budget = G.budgetNs.load() / 1000.0;
    _cpu.stringValue = [NSString stringWithFormat:@"Plug-in time per block: average %.1f µs (%.2f %%), worst %.1f µs (%.1f %%)   block %.2f ms at %.0f Hz   overloads %llu   level %.2f   moves in its window %d",
                        avg, budget ? avg / budget * 100 : 0, worst, budget ? worst / budget * 100 : 0, budget / 1000, G.sr, _stream.overloads.load(), G.peak.load(), G.plug ? G.plug->editsFromEditor() : 0];
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
    [_table selectRowIndexes:[NSIndexSet indexSetWithIndex:pick] byExtendingSelection:NO]; [_table scrollRowToVisible:pick];
    BOOL ok = [self loadRow:pick];
    [self say:[NSString stringWithFormat:@"[selftest] load %s", ok ? "ok" : "FAILED"]];
    __weak App* me = self;
    dispatch_after(dispatch_time(DISPATCH_TIME_NOW, (int64_t)(1.0 * NSEC_PER_SEC)), dispatch_get_main_queue(), ^{
        [me openEditor:nil]; [me togglePattern:nil];
        dispatch_after(dispatch_time(DISPATCH_TIME_NOW, (int64_t)(5.0 * NSEC_PER_SEC)), dispatch_get_main_queue(), ^{
            [me say:@"[selftest] five seconds of the pattern played"];
            [me writeMarker:@"ready-for-screenshot"];
            dispatch_after(dispatch_time(DISPATCH_TIME_NOW, (int64_t)(6.0 * NSEC_PER_SEC)), dispatch_get_main_queue(), ^{ [me togglePattern:nil]; [me selftestEnd]; });
        });
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
