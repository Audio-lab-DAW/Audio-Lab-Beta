// VST3 behind the AudioLab plug-in interface (plugin_api.h). Task NM1.
// Built on Steinberg's VST 3 SDK (MIT licence since 3.8) and its hosting helpers.
#include "plugin_api.h"

#include "pluginterfaces/gui/iplugview.h"
#include "pluginterfaces/vst/ivstaudioprocessor.h"
#include "pluginterfaces/vst/ivstcomponent.h"
#include "pluginterfaces/vst/ivsteditcontroller.h"
#include "pluginterfaces/vst/ivstevents.h"
#include "pluginterfaces/vst/ivstprocesscontext.h"
#include "pluginterfaces/vst/vstspeaker.h"
#include "public.sdk/source/common/memorystream.h"
#include "public.sdk/source/vst/hosting/eventlist.h"
#include "public.sdk/source/vst/hosting/hostclasses.h"
#include "public.sdk/source/vst/hosting/module.h"
#include "public.sdk/source/vst/hosting/parameterchanges.h"
#include "public.sdk/source/vst/hosting/plugprovider.h"
#include "public.sdk/source/vst/hosting/processdata.h"
#include "public.sdk/source/vst/utility/stringconvert.h"

#include <atomic>
#include <cstring>
#include <filesystem>
#include <mutex>

using namespace Steinberg;
using namespace Steinberg::Vst;

namespace al {

static HostApplication& hostApp() {
    static HostApplication app;
    static bool set = false;
    if (!set) { PluginContextFactory::instance().setPluginContext(&app); set = true; }
    return app;
}

// What the plug-in tells the host: a control was moved in its own window, or it must be restarted.
struct Handler : public IComponentHandler {
    ParameterChangeTransfer* transfer = nullptr;
    std::mutex* lock = nullptr;
    std::atomic<int> edits{0}, begins{0}, ends{0}, restarts{0}, valueRestarts{0};
    std::atomic<uint32_t> lastId{0};
    std::atomic<double> lastValue{0};
    std::atomic<bool> latencyChanged{false};
    tresult PLUGIN_API beginEdit(ParamID) override { begins++; return kResultOk; }
    tresult PLUGIN_API performEdit(ParamID id, ParamValue v) override {
        if (transfer) { std::lock_guard<std::mutex> g(*lock); transfer->addChange(id, v, 0); }
        lastId = id; lastValue = v;
        edits++;
        return kResultOk;
    }
    tresult PLUGIN_API endEdit(ParamID) override { ends++; return kResultOk; }
    tresult PLUGIN_API restartComponent(int32 flags) override {
        restarts++;
        if (flags & kParamValuesChanged) valueRestarts++;
        if (flags & kLatencyChanged) latencyChanged = true;
        return kResultOk;
    }
    tresult PLUGIN_API queryInterface(const TUID iid, void** obj) override {
        if (FUnknownPrivate::iidEqual(iid, IComponentHandler::iid) || FUnknownPrivate::iidEqual(iid, FUnknown::iid)) { *obj = static_cast<IComponentHandler*>(this); return kResultOk; }
        *obj = nullptr; return kNoInterface;
    }
    uint32 PLUGIN_API addRef() override { return 1000; }
    uint32 PLUGIN_API release() override { return 1000; }
};

// The plug-in's window asks to be resized through this.
struct Frame : public IPlugFrame {
    std::function<void(int, int)> onResize;
    tresult PLUGIN_API resizeView(IPlugView* view, ViewRect* r) override {
        if (!view || !r) return kInvalidArgument;
        if (onResize) onResize(r->getWidth(), r->getHeight());
        view->onSize(r);
        return kResultOk;
    }
    tresult PLUGIN_API queryInterface(const TUID iid, void** obj) override {
        if (FUnknownPrivate::iidEqual(iid, IPlugFrame::iid) || FUnknownPrivate::iidEqual(iid, FUnknown::iid)) { *obj = static_cast<IPlugFrame*>(this); return kResultOk; }
        *obj = nullptr; return kNoInterface;
    }
    uint32 PLUGIN_API addRef() override { return 1000; }
    uint32 PLUGIN_API release() override { return 1000; }
};

class Vst3Instance : public PluginInstance {
public:
    PluginInfo pinfo;
    VST3::Hosting::Module::Ptr module;
    IPtr<PlugProvider> provider;
    IPtr<IComponent> component;
    IPtr<IEditController> controller;
    IPtr<IAudioProcessor> processor;
    IPtr<IPlugView> view;
    Handler handler;
    Frame frame;
    HostProcessData data;
    EventList events{512};
    ParameterChanges inChanges{64}, outChanges{64};
    ParameterChangeTransfer transfer{512};
    std::mutex transferLock;
    Vst::ProcessContext pctx{};
    bool active = false;
    int maxBlock = 0;
    int latency = 0;
    int64_t tail = 0;

    ~Vst3Instance() override {
        closeEditor();
        if (active && processor) { processor->setProcessing(false); component->setActive(false); }
        data.unprepare();
        if (controller) controller->setComponentHandler(nullptr);
        processor = nullptr; component = nullptr; controller = nullptr;
        provider = nullptr;   // terminates the plug-in
        module = nullptr;
    }
    const PluginInfo& info() const override { return pinfo; }

    BusLayout buses() const override {
        BusLayout b;
        b.audioIns = component->getBusCount(kAudio, kInput); b.audioOuts = component->getBusCount(kAudio, kOutput);
        b.eventIns = component->getBusCount(kEvent, kInput); b.eventOuts = component->getBusCount(kEvent, kOutput);
        BusInfo bi{};
        if (b.audioIns && component->getBusInfo(kAudio, kInput, 0, bi) == kResultOk) b.mainInChannels = bi.channelCount;
        if (b.audioOuts && component->getBusInfo(kAudio, kOutput, 0, bi) == kResultOk) b.mainOutChannels = bi.channelCount;
        return b;
    }
    std::vector<ParamInfo> params() const override {
        std::vector<ParamInfo> v;
        if (!controller) return v;
        int n = controller->getParameterCount();
        for (int i = 0; i < n; i++) {
            ParameterInfo pi{};
            if (controller->getParameterInfo(i, pi) != kResultOk) continue;
            ParamInfo p;
            p.id = pi.id; p.name = VST3::StringConvert::convert(pi.title); p.units = VST3::StringConvert::convert(pi.units);
            p.defaultValue = pi.defaultNormalizedValue; p.steps = pi.stepCount;
            p.automatable = (pi.flags & ParameterInfo::kCanAutomate) != 0; p.readOnly = (pi.flags & ParameterInfo::kIsReadOnly) != 0;
            p.isBypass = (pi.flags & ParameterInfo::kIsBypass) != 0; p.hidden = (pi.flags & ParameterInfo::kIsHidden) != 0;
            v.push_back(p);
        }
        return v;
    }
    double getParam(uint32_t id) const override { return controller ? controller->getParamNormalized(id) : 0; }
    void setParam(uint32_t id, double value) override {
        if (controller) controller->setParamNormalized(id, value);
        std::lock_guard<std::mutex> g(transferLock);
        transfer.addChange(id, value, 0);
    }
    std::string paramText(uint32_t id, double value) const override {
        String128 s = {0};
        if (!controller || controller->getParamStringByValue(id, value, s) != kResultOk) return "";
        return VST3::StringConvert::convert(s);
    }

    bool prepare(double sr, int block, bool offline, std::string& err) override {
        if (active) { processor->setProcessing(false); component->setActive(false); active = false; }
        // ask for stereo on the main buses; a plug-in may say no and keep its own layout
        int nIn = component->getBusCount(kAudio, kInput), nOut = component->getBusCount(kAudio, kOutput);
        std::vector<SpeakerArrangement> ins(nIn), outs(nOut);
        for (int i = 0; i < nIn; i++) { processor->getBusArrangement(kInput, i, ins[i]); if (i == 0) ins[i] = SpeakerArr::kStereo; }
        for (int i = 0; i < nOut; i++) { processor->getBusArrangement(kOutput, i, outs[i]); if (i == 0) outs[i] = SpeakerArr::kStereo; }
        processor->setBusArrangements(nIn ? ins.data() : nullptr, nIn, nOut ? outs.data() : nullptr, nOut);
        for (int i = 0; i < nIn; i++) component->activateBus(kAudio, kInput, i, i == 0);
        for (int i = 0; i < nOut; i++) component->activateBus(kAudio, kOutput, i, i == 0);
        for (int i = 0; i < component->getBusCount(kEvent, kInput); i++) component->activateBus(kEvent, kInput, i, i == 0);
        ProcessSetup setup{offline ? kOffline : kRealtime, kSample32, block, sr};
        if (processor->canProcessSampleSize(kSample32) != kResultOk) { err = "the plug-in cannot work with 32-bit float audio"; return false; }
        tresult r = processor->setupProcessing(setup);
        if (r != kResultOk && r != kNotImplemented) { err = "setupProcessing failed"; return false; }
        if (component->setActive(true) != kResultOk) { err = "setActive failed"; return false; }
        processor->setProcessing(true);
        active = true; maxBlock = block;
        data.unprepare();
        data.prepare(*component, block, kSample32);    // buffers for every bus, owned by the host
        data.inputEvents = &events; data.inputParameterChanges = &inChanges; data.outputParameterChanges = &outChanges;
        data.processContext = &pctx; data.processMode = setup.processMode; data.symbolicSampleSize = kSample32;
        latency = (int)processor->getLatencySamples();
        uint32 t = processor->getTailSamples();
        tail = t == kInfiniteTail ? -1 : (int64_t)t;
        handler.latencyChanged = false;
        return true;
    }

    bool process(const float* const* in, int inCh, float** out, int outCh, int frames, const NoteEvent* notes, int noteCount, const al::ProcessContext& c) override {
        if (!active || frames > maxBlock) return false;
        for (int i = 0; i < noteCount; i++) {
            Event e{};
            e.busIndex = 0; e.sampleOffset = notes[i].offset; e.flags = Event::kIsLive;
            if (notes[i].on) { e.type = Event::kNoteOnEvent; e.noteOn.channel = (int16)notes[i].channel; e.noteOn.pitch = (int16)notes[i].pitch; e.noteOn.velocity = notes[i].velocity; e.noteOn.noteId = -1; }
            else { e.type = Event::kNoteOffEvent; e.noteOff.channel = (int16)notes[i].channel; e.noteOff.pitch = (int16)notes[i].pitch; e.noteOff.velocity = 0; e.noteOff.noteId = -1; }
            events.addEvent(e);
        }
        if (transferLock.try_lock()) { transfer.transferChangesTo(inChanges); transferLock.unlock(); }
        pctx.state = (c.playing ? Vst::ProcessContext::kPlaying : 0) | Vst::ProcessContext::kTempoValid | Vst::ProcessContext::kTimeSigValid | Vst::ProcessContext::kProjectTimeMusicValid | Vst::ProcessContext::kContTimeValid;
        pctx.sampleRate = c.sampleRate; pctx.tempo = c.tempo; pctx.projectTimeSamples = c.samplePos; pctx.continousTimeSamples = c.samplePos;
        pctx.projectTimeMusic = (double)c.samplePos / c.sampleRate * c.tempo / 60.0; pctx.timeSigNumerator = 4; pctx.timeSigDenominator = 4;
        data.numSamples = frames;
        for (int b = 0; b < data.numInputs; b++) {
            data.inputs[b].silenceFlags = 0;
            for (int ch = 0; ch < data.inputs[b].numChannels; ch++) {
                float* d = data.inputs[b].channelBuffers32[ch];
                if (!d) continue;
                if (b == 0 && inCh > 0) memcpy(d, in[ch < inCh ? ch : inCh - 1], sizeof(float) * frames);   // mono plug-in input gets the left channel; extra channels a copy
                else memset(d, 0, sizeof(float) * frames);
            }
        }
        for (int b = 0; b < data.numOutputs; b++) {
            data.outputs[b].silenceFlags = 0;
            for (int ch = 0; ch < data.outputs[b].numChannels; ch++) if (data.outputs[b].channelBuffers32[ch]) memset(data.outputs[b].channelBuffers32[ch], 0, sizeof(float) * frames);
        }
        tresult r = processor->process(data);
        if (data.numOutputs > 0) {
            int have = data.outputs[0].numChannels;
            for (int ch = 0; ch < outCh; ch++) {
                if (have > 0 && data.outputs[0].channelBuffers32[ch < have ? ch : have - 1]) memcpy(out[ch], data.outputs[0].channelBuffers32[ch < have ? ch : have - 1], sizeof(float) * frames);
                else memset(out[ch], 0, sizeof(float) * frames);
            }
        } else for (int ch = 0; ch < outCh; ch++) memset(out[ch], 0, sizeof(float) * frames);
        events.clear(); inChanges.clearQueue(); outChanges.clearQueue();
        return r == kResultOk;
    }
    int latencySamples() const override { return latency; }
    int64_t tailSamples() const override { return tail; }

    // Project file format of a plug-in's state: "ALV3", then the processor part and the controller part, each
    // with its length. Both parts are the plug-in's own bytes, untouched.
    bool getState(std::vector<uint8_t>& out) const override {
        MemoryStream a, b;
        if (component->getState(&a) != kResultOk) return false;
        bool hasB = controller && controller->getState(&b) == kResultOk;
        uint32_t la = (uint32_t)a.getSize(), lb = hasB ? (uint32_t)b.getSize() : 0;
        out.clear(); out.insert(out.end(), {'A', 'L', 'V', '3'});
        auto put = [&](uint32_t v) { for (int i = 0; i < 4; i++) out.push_back((uint8_t)(v >> (8 * i))); };
        put(la); out.insert(out.end(), (uint8_t*)a.getData(), (uint8_t*)a.getData() + la);
        put(lb); if (lb) out.insert(out.end(), (uint8_t*)b.getData(), (uint8_t*)b.getData() + lb);
        return true;
    }
    bool setState(const std::vector<uint8_t>& in) override {
        if (in.size() < 12 || memcmp(in.data(), "ALV3", 4)) return false;
        auto get = [&](size_t p) { return (uint32_t)in[p] | ((uint32_t)in[p + 1] << 8) | ((uint32_t)in[p + 2] << 16) | ((uint32_t)in[p + 3] << 24); };
        uint32_t la = get(4); if (8 + (size_t)la + 4 > in.size()) return false;
        uint32_t lb = get(8 + la); if (12 + (size_t)la + lb > in.size()) return false;
        MemoryStream a((void*)(in.data() + 8), la);
        bool ok = component->setState(&a) == kResultOk;
        if (controller) {
            MemoryStream a2((void*)(in.data() + 8), la);
            controller->setComponentState(&a2);
            if (lb) { MemoryStream b((void*)(in.data() + 12 + la), lb); controller->setState(&b); }
        }
        return ok;
    }

    bool hasEditor() override {
        if (!controller) return false;
        if (view) return true;
        IPtr<IPlugView> v = owned(controller->createView(ViewType::kEditor));
        return v != nullptr;
    }
    bool openEditor(void* parent, int& w, int& h, std::function<void(int, int)> onResize, std::string& err) override {
        if (!controller) { err = "the plug-in has no controller"; return false; }
        closeEditor();
        view = owned(controller->createView(ViewType::kEditor));
        if (!view) { err = "the plug-in has no window of its own"; return false; }
#if defined(__APPLE__)
        FIDString type = kPlatformTypeNSView;
#elif defined(_WIN32)
        FIDString type = kPlatformTypeHWND;
#else
        FIDString type = kPlatformTypeX11EmbedWindowID;
#endif
        if (view->isPlatformTypeSupported(type) != kResultTrue) { err = "the plug-in's window does not support this system's window type"; view = nullptr; return false; }
        frame.onResize = onResize;
        view->setFrame(&frame);
        ViewRect r{};
        if (view->getSize(&r) == kResultOk) { w = r.getWidth(); h = r.getHeight(); }
        if (parent) {
            if (view->attached(parent, type) != kResultOk) { err = "the plug-in refused to attach its window"; view->setFrame(nullptr); view = nullptr; return false; }
            if (view->getSize(&r) == kResultOk && r.getWidth() > 0) { w = r.getWidth(); h = r.getHeight(); }
        }
        attached = parent != nullptr;
        return true;
    }
    void closeEditor() override {
        if (!view) return;
        view->setFrame(nullptr);
        if (attached) view->removed();
        view = nullptr; attached = false;
    }
    bool attached = false;
    bool takeLatencyChanged() override {
        if (!handler.latencyChanged.exchange(false)) return false;
        latency = (int)processor->getLatencySamples();
        return true;
    }
    int editsFromEditor() const override { return handler.edits.load(); }
    EditStats editStats() const override {
        EditStats s;
        s.performs = handler.edits.load(); s.begins = handler.begins.load(); s.ends = handler.ends.load();
        s.restarts = handler.restarts.load(); s.valueRestarts = handler.valueRestarts.load();
        s.lastId = handler.lastId.load(); s.lastValue = handler.lastValue.load();
        return s;
    }
};

class Vst3Format : public PluginFormat {
public:
    std::string name() const override { return "vst3"; }
    std::vector<std::string> defaultFolders() const override {
        std::vector<std::string> v;
        const char* home = getenv("HOME");
#if defined(__APPLE__)
        if (home) v.push_back(std::string(home) + "/Library/Audio/Plug-Ins/VST3");
        v.push_back("/Library/Audio/Plug-Ins/VST3");
        v.push_back("/Network/Library/Audio/Plug-Ins/VST3");
#else
        if (home) v.push_back(std::string(home) + "/.vst3");
        v.push_back("/usr/lib/vst3"); v.push_back("/usr/local/lib/vst3");
#endif
        return v;
    }
    std::vector<std::string> findBundles(const std::vector<std::string>& folders) const override {
        std::vector<std::string> out;
        namespace fs = std::filesystem;
        std::function<void(const fs::path&, int)> walk = [&](const fs::path& dir, int depth) {
            std::error_code ec;
            if (depth > 6 || !fs::is_directory(dir, ec)) return;
            std::vector<fs::path> items;
            for (fs::directory_iterator it(dir, fs::directory_options::skip_permission_denied, ec), end; !ec && it != end; it.increment(ec)) items.push_back(it->path());
            std::sort(items.begin(), items.end());
            for (auto& p : items) {
                if (p.extension() == ".vst3") out.push_back(p.string());      // a bundle (a folder) or a single file: do not look inside
                else if (fs::is_directory(p, ec)) walk(p, depth + 1);
            }
        };
        for (auto& f : folders) {
            if (fs::path(f).extension() == ".vst3") out.push_back(f); else walk(f, 0);
        }
        return out;
    }
    ScanResult scanInProcess(const std::string& path) override {
        ScanResult r; r.path = path; r.archs = bundleArchs(path);
        hostApp();
        std::string err;
        auto mod = VST3::Hosting::Module::create(path, err);
        if (!mod) { r.error = err.empty() ? "the bundle could not be loaded" : err; return r; }
        for (auto& c : mod->getFactory().classInfos()) {
            if (c.category() != kVstAudioEffectClass) continue;
            PluginInfo p;
            p.format = "vst3"; p.path = path; p.uid = c.ID().toString(); p.name = c.name(); p.vendor = c.vendor().empty() ? mod->getFactory().info().vendor() : c.vendor();
            p.version = c.version(); p.sdk = c.sdkVersion(); p.categories = c.subCategoriesString();
            p.isInstrument = p.categories.find("Instrument") != std::string::npos;
            p.isEffect = !p.isInstrument || p.categories.find("Fx") != std::string::npos;
            r.plugins.push_back(p);
        }
        r.ok = true;
        return r;
    }
    std::unique_ptr<PluginInstance> create(const PluginInfo& info, std::string& err) override {
        hostApp();
        auto inst = std::make_unique<Vst3Instance>();
        inst->pinfo = info;
        inst->module = VST3::Hosting::Module::create(info.path, err);
        if (!inst->module) { if (err.empty()) err = "the bundle could not be loaded"; return nullptr; }
        auto factory = inst->module->getFactory();
        bool found = false;
        for (auto& c : factory.classInfos()) {
            if (c.category() != kVstAudioEffectClass) continue;
            if (!info.uid.empty() && c.ID().toString() != info.uid) continue;
            if (info.uid.empty() && !info.name.empty() && c.name() != info.name) continue;
            inst->provider = owned(new PlugProvider(factory, c, true));
            if (!inst->provider->initialize()) { err = "the plug-in failed to initialise"; return nullptr; }
            inst->pinfo.uid = c.ID().toString(); inst->pinfo.name = c.name(); inst->pinfo.vendor = c.vendor(); inst->pinfo.version = c.version();
            inst->pinfo.categories = c.subCategoriesString(); inst->pinfo.sdk = c.sdkVersion(); inst->pinfo.format = "vst3";
            inst->pinfo.isInstrument = inst->pinfo.categories.find("Instrument") != std::string::npos;
            inst->pinfo.isEffect = !inst->pinfo.isInstrument || inst->pinfo.categories.find("Fx") != std::string::npos;
            found = true;
            break;
        }
        if (!found) { err = "no such plug-in in this bundle"; return nullptr; }
        inst->component = inst->provider->getComponentPtr();
        inst->controller = inst->provider->getControllerPtr();
        if (!inst->component) { err = "the plug-in gave no audio component"; return nullptr; }
        inst->processor = FUnknownPtr<IAudioProcessor>(inst->component);
        if (!inst->processor) { err = "the plug-in gave no audio processor"; return nullptr; }
        inst->handler.transfer = &inst->transfer; inst->handler.lock = &inst->transferLock;
        if (inst->controller) inst->controller->setComponentHandler(&inst->handler);
        return inst;
    }
};

PluginFormat* vst3Format() { static Vst3Format f; return &f; }

}  // namespace al
