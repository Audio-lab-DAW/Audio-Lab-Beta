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

struct BusLayout { int audioIns = 0, audioOuts = 0, mainInChannels = 0, mainOutChannels = 0, eventIns = 0, eventOuts = 0; };

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

}  // namespace al
