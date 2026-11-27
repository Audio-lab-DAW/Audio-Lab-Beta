// AudioLab plug-in host layer: the one interface the engine talks to, whatever the plug-in format is.
// Task NM1. Today there is one implementation (VST3, vst3_format.cpp). Audio Units, CLAP and VST2 are meant
// to be added as further PluginFormat classes behind this same header; nothing in here names a format's
// own types, so the engine, the mixer, the project file and the tests do not change when one is added.
#pragma once
#include <cstdint>
#include <functional>
#include <memory>
#include <string>
#include <vector>

namespace al {

struct PluginInfo {
    std::string format;      // "vst3" (later "au", "clap", "vst2")
    std::string path;        // the bundle or file on disk
    std::string uid;         // the format's own id of this plug-in inside the bundle
    std::string name, vendor, version, categories, sdk;
    bool isInstrument = false, isEffect = false;
};

struct ParamInfo {
    uint32_t id = 0;
    std::string name, units;
    double defaultValue = 0;    // all values are 0..1 ("normalised"), as every format can express
    int steps = 0;              // 0 = continuous
    bool automatable = true, readOnly = false, isBypass = false, hidden = false;
};

struct NoteEvent { int offset = 0; bool on = true; int channel = 0, pitch = 60; float velocity = 0.8f; };

struct ProcessContext {
    double sampleRate = 48000, tempo = 120;
    int64_t samplePos = 0;
    bool playing = true;
};

// What a plug-in told the host from its own window (VST3: IComponentHandler).
struct EditStats {
    int performs = 0;          // performEdit: a control was moved
    int begins = 0, ends = 0;  // beginEdit / endEdit: a gesture started / ended
    int restarts = 0;          // restartComponent, any reason
    int valueRestarts = 0;     // restartComponent with "parameter values changed"
    uint32_t lastId = 0;       // the last parameter moved, and its value (0..1)
    double lastValue = 0;
};

struct BusLayout { int audioIns = 0, audioOuts = 0, mainInChannels = 0, mainOutChannels = 0, eventIns = 0, eventOuts = 0; };

// How the host sets a plug-in up (task NL5). The defaults are the 0.5 host, which follows the SDK's validator and
// JUCE's VST3 host. Each switch puts one 0.4 behaviour back, so a silent instrument can be measured against each.
struct HostOptions {
    bool syncControllerState = true;   // controller->setComponentState(the processor's state) after both are set up (0.4: never)
    bool messagesAnyThread = true;     // controller <-> processor messages delivered from any thread (0.4: the SDK's proxy dropped all but the main thread's)
    bool validatorOrder = true;        // setupProcessing, setBusArrangements, activateBus, setActive, setProcessing (0.4: arrangements and buses first)
    bool preferredArrangements = true; // give each bus the arrangement the plug-in asks for (0.4: stereo forced on the main buses)
    bool allEventInputs = true;        // every event input bus active (0.4: only the first)
    bool uniqueNoteIds = false;        // false: noteId -1, as JUCE; true: a new id per note, its note-off carrying the same id
    bool allAudioBuses = false;        // also activate aux audio buses (normally only main buses are active; aux buses get buffers anyway)
    bool fullContext = true;           // system time and bar position in the process context (0.4: without)
    static HostOptions legacy04() { HostOptions o; o.syncControllerState = false; o.messagesAnyThread = false; o.validatorOrder = false; o.preferredArrangements = false; o.allEventInputs = false; o.fullContext = false; return o; }
};

// What the host measured about one plug-in instance (task NL5): set-up lines, then live counters from the audio thread.
struct HostDiag {
    std::vector<std::string> setup;    // plain lines: what the plug-in asked for, what the host gave, the result of every call
    uint64_t blocks = 0, blocksMainNonZero = 0, blocksOtherNonZero = 0, blocksSilenceFlag = 0, processNotOk = 0;
    uint64_t noteOns = 0, noteOffs = 0, eventsRejected = 0, paramChanges = 0;
    float peakMain = 0, peakOther = 0;  // the plug-in's own output buffers, before the host copies or scales anything
    int lastProcessResult = 0;
    int msgToProcessor = 0, msgToController = 0, msgOffMainThread = 0, msgDropped = 0;   // IConnectionPoint traffic
    int setComponentStateResult = -999;  // -999: not called
    int stateBytes = 0;
};
struct PresetInfo { std::string name, source; int index = 0; };   // source: "program list" or a .vstpreset path

class PluginInstance {
public:
    virtual ~PluginInstance() {}
    virtual const PluginInfo& info() const = 0;
    virtual BusLayout buses() const = 0;
    virtual std::vector<ParamInfo> params() const = 0;
    virtual double getParam(uint32_t id) const = 0;
    virtual void setParam(uint32_t id, double value) = 0;            // from the host (automation, the device strip)
    virtual std::string paramText(uint32_t id, double value) const = 0;
    // Sets sample rate, largest block and real time / export. May be called again when the device changes.
    virtual bool prepare(double sampleRate, int maxBlock, bool offline, std::string& err) = 0;
    // Audio thread. in / out are planar; a plug-in with fewer channels gets what it has.
    virtual bool process(const float* const* in, int inChannels, float** out, int outChannels, int frames,
                         const NoteEvent* notes, int noteCount, const ProcessContext& ctx) = 0;
    virtual int latencySamples() const = 0;                          // for delay compensation
    virtual int64_t tailSamples() const = 0;                         // -1 = endless
    virtual bool getState(std::vector<uint8_t>& out) const = 0;      // goes into the project file as is
    virtual bool setState(const std::vector<uint8_t>& in) = 0;
    // The plug-in's own window. parent is an NSView* on macOS (an HWND on Windows later).
    virtual bool hasEditor() = 0;
    virtual bool openEditor(void* parent, int& width, int& height, std::function<void(int, int)> onResize, std::string& err) = 0;
    virtual void closeEditor() = 0;
    // Things the plug-in told the host since the last call (latency changed, parameters changed from its window).
    virtual bool takeLatencyChanged() = 0;
    virtual int editsFromEditor() const = 0;
    virtual EditStats editStats() const { EditStats s; s.performs = editsFromEditor(); return s; }
    // task NL5: host options (call before prepare), the host's measurements, factory presets
    virtual void setHostOptions(const HostOptions&) {}
    virtual HostDiag diag() const { return HostDiag(); }
    virtual std::vector<PresetInfo> presets() { return {}; }
    virtual bool loadPreset(const PresetInfo&, std::string& err) { err = "not supported"; return false; }
};

struct ScanResult {
    std::string path, archs;          // archs: "arm64", "x86_64", "arm64 x86_64" or "" when not known
    bool ok = false, crashed = false, timedOut = false, wrongArch = false;
    std::string error;
    std::vector<PluginInfo> plugins;
    double seconds = 0;
};

class PluginFormat {
public:
    virtual ~PluginFormat() {}
    virtual std::string name() const = 0;
    virtual std::vector<std::string> defaultFolders() const = 0;
    virtual std::vector<std::string> findBundles(const std::vector<std::string>& folders) const = 0;
    // Loads the bundle in THIS process and lists what is inside. Only the scanner child process calls this.
    virtual ScanResult scanInProcess(const std::string& path) = 0;
    virtual std::unique_ptr<PluginInstance> create(const PluginInfo& info, std::string& err) = 0;
    // task NL5: with host options that matter while the plug-in is set up (state given to the controller, messages)
    virtual std::unique_ptr<PluginInstance> createWith(const PluginInfo& info, const HostOptions& o, std::string& err) { auto p = create(info, err); if (p) p->setHostOptions(o); return p; }
};

PluginFormat* vst3Format();

// --- scanning in a separate process, so a bad plug-in cannot take the app down -----------------------
// The scanner child: call this first thing in main(); if the arguments say "scan one bundle" it does so,
// prints the result and returns true (the caller then exits).
bool scannerChildMain(int argc, char** argv, int& exitCode);
// Runs the scanner child (this same program) on one bundle with a time limit.
ScanResult scanOutOfProcess(const std::string& selfExe, const std::string& bundle, int timeoutSeconds);
std::string scanResultJson(const ScanResult& r);
// Which processor kinds a bundle's program holds (macOS). "" on other systems.
std::string bundleArchs(const std::string& bundle);
std::string hostArch();

// --- task NL5: why is an instrument silent? -----------------------------------------------------------
// Renders a fresh instance of the plug-in under several host set-ups (the 0.5 host, the 0.4 host, and the 0.5 host with
// one thing changed at a time), with notes, and measures each. idle() is called between blocks so the caller can pump
// its main run loop (plug-ins that do work there). Runs in the calling thread, which must be the main thread.
struct ProbeVariant { std::string key, what; bool ran = false; std::string error; HostDiag d; double peak = 0; int firstSoundBlock = -1; };
std::vector<ProbeVariant> probeSilence(const PluginInfo& info, double sampleRate, int block, double seconds, bool withPreset, const std::function<void(double)>& idle);
std::string probeJson(const PluginInfo& info, double sampleRate, int block, const std::vector<ProbeVariant>& v);
std::string probeText(const std::string& name, const std::vector<ProbeVariant>& v);   // plain lines for a report
// The probe in a child process (so a plug-in that crashes cannot take the app down):
//   <self> --al-probe <bundle> <uid> <rate> <block> <out.json>
bool probeChildMain(int argc, char** argv, int& exitCode, const std::function<void(double)>& idle);
// Runs probeChildMain in a child process (this same program) and returns its text (the [probe] lines).
std::string probeOutOfProcess(const std::string& selfExe, const PluginInfo& info, double sampleRate, int block, const std::string& outFile, int timeoutSeconds, std::string& err);
std::string diagText(const std::string& name, const HostDiag& d);      // the [diag] lines for one instance
// Lists bundles of other formats without loading them (decision D5): CLAP folders and Audio Units (Components).
struct ListedBundle { std::string path, name, archs, kind; };
std::vector<ListedBundle> listOtherFormat(const std::string& format, std::vector<std::string>& foldersOut);

}  // namespace al
