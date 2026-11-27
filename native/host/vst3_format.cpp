// VST3 behind the AudioLab plug-in interface (plugin_api.h). Task NM1.
// Built on Steinberg's VST 3 SDK (MIT licence since 3.8) and its hosting helpers.
#include "plugin_api.h"
#include "live_tools.h"

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
#include "public.sdk/source/vst/vstpresetfile.h"
#include "pluginterfaces/vst/ivstunits.h"
#include "pluginterfaces/vst/ivstmessage.h"
#include "public.sdk/source/vst/hosting/processdata.h"
#include "public.sdk/source/vst/utility/stringconvert.h"

#include <algorithm>
#include <atomic>
#include <chrono>
#include <cmath>
#include <thread>
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
    // task NL7: events as they happen, and the parameters reported since the window last asked
    std::function<void(uint32_t, uint32_t)> onEvent;
    std::mutex touchedLock; std::set<uint32_t> touched;
    void touch(uint32_t id) { std::lock_guard<std::mutex> g(touchedLock); if (touched.size() < 100000) touched.insert(id); }
    tresult PLUGIN_API beginEdit(ParamID id) override { begins++; if (onEvent) onEvent(evGestureBegin, id); return kResultOk; }
    tresult PLUGIN_API performEdit(ParamID id, ParamValue v) override {
        if (transfer) { std::lock_guard<std::mutex> g(*lock); transfer->addChange(id, v, 0); }
        lastId = id; lastValue = v;
        edits++;
        touch(id);
        return kResultOk;
    }
    tresult PLUGIN_API endEdit(ParamID id) override { ends++; if (onEvent) onEvent(evGestureEnd, id); return kResultOk; }
    tresult PLUGIN_API restartComponent(int32 flags) override {
        restarts++;
        if (flags & kParamValuesChanged) valueRestarts++;
        if (flags & kLatencyChanged) latencyChanged = true;
        if (onEvent) onEvent(evRestart, (uint32_t)flags);
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

static const char* rc(tresult r) {
    switch (r) {
        case kResultOk: return "ok";
        case kResultFalse: return "false";
        case kNotImplemented: return "not implemented";
        case kInvalidArgument: return "invalid argument";
        case kNoInterface: return "no interface";
        case kInternalError: return "internal error";
        case kNotInitialized: return "not initialised";
        case kOutOfMemory: return "out of memory";
        default: return "unknown code";
    }
}
static std::string arrName(SpeakerArrangement a) {
    if (a == SpeakerArr::kEmpty) return "empty";
    if (a == SpeakerArr::kMono) return "mono";
    if (a == SpeakerArr::kStereo) return "stereo";
    char b[48]; snprintf(b, sizeof b, "%d ch (0x%llx)", SpeakerArr::getChannelCount(a), (unsigned long long)a); return b;
}
static SpeakerArrangement arrFor(int ch) { return ch == 1 ? SpeakerArr::kMono : ch == 2 ? SpeakerArr::kStereo : ch <= 0 ? SpeakerArr::kEmpty : (SpeakerArrangement)((1ull << ch) - 1); }

// Between the plug-in's processor and its controller (IConnectionPoint). The SDK's own ConnectionProxy (used by
// PlugProvider in test apps 0.1 to 0.4) silently DROPS every message not sent from the thread that made it; JUCE's
// host connects the two directly. This link delivers like JUCE (or drops like the SDK, as an option) and counts.
struct Link : public IConnectionPoint {
    IConnectionPoint* src = nullptr;   // the side that sends through this link
    IConnectionPoint* dst = nullptr;   // the side that receives
    std::thread::id mainId;
    const bool* anyThread = nullptr;
    std::atomic<int>* count = nullptr; std::atomic<int>* off = nullptr; std::atomic<int>* dropped = nullptr;
    tresult PLUGIN_API connect(IConnectionPoint* other) override { if (!other) return kInvalidArgument; dst = other; return kResultTrue; }
    tresult PLUGIN_API disconnect(IConnectionPoint* other) override { if (other == dst) dst = nullptr; return kResultTrue; }
    tresult PLUGIN_API notify(IMessage* m) override {
        if (count) (*count)++;
        bool onMain = std::this_thread::get_id() == mainId;
        if (!onMain && off) (*off)++;
        if (!onMain && anyThread && !*anyThread) { if (dropped) (*dropped)++; return kResultFalse; }
        return dst ? dst->notify(m) : kResultFalse;
    }
    tresult PLUGIN_API queryInterface(const TUID iid, void** obj) override {
        if (FUnknownPrivate::iidEqual(iid, IConnectionPoint::iid) || FUnknownPrivate::iidEqual(iid, FUnknown::iid)) { *obj = static_cast<IConnectionPoint*>(this); return kResultOk; }
        *obj = nullptr; return kNoInterface;
    }
    uint32 PLUGIN_API addRef() override { return 1000; }
    uint32 PLUGIN_API release() override { return 1000; }
};

class Vst3Instance : public PluginInstance {
public:
    PluginInfo pinfo;
    VST3::Hosting::Module::Ptr module;
    VST3::UID classId;
    IPtr<IComponent> component;
    IPtr<IEditController> controller;
    IPtr<IAudioProcessor> processor;
    IPtr<IPlugView> view;
    bool singleObject = false, connected = false;
    IPtr<IConnectionPoint> compCP, ctrlCP;
    Link toController, toProcessor;     // toController: the processor's messages; toProcessor: the controller's
    Handler handler;
    Frame frame;
    HostProcessData data;
    EventList events{512};
    ParameterChanges inChanges{64}, outChanges{64};
    ParameterChangeTransfer transfer{512};
    std::mutex transferLock;
    Vst::ProcessContext pctx{};
    HostOptions opt;
    bool active = false;
    int maxBlock = 0;
    int latency = 0;
    int64_t tail = 0;
    // diagnostics
    std::vector<std::string> createLines, prepareLines;
    std::atomic<uint64_t> dBlocks{0}, dMainNZ{0}, dOtherNZ{0}, dSilFlag{0}, dNotOk{0}, dOn{0}, dOff{0}, dRej{0}, dParams{0};
    std::atomic<float> dPeakMain{0}, dPeakOther{0};
    std::atomic<int> dLastRes{0};
    std::atomic<int> mToProc{0}, mToCtrl{0}, mOff{0}, mDrop{0};
    int syncRes = -999, stateBytes = 0;
    int32 nextNoteId = 1;
    int32 liveIds[16][128];

    Vst3Instance() { for (auto& c : liveIds) for (auto& x : c) x = -1; }
    ~Vst3Instance() override {
        closeEditor();
        if (active && processor) { processor->setProcessing(false); component->setActive(false); }
        data.unprepare();
        if (controller) controller->setComponentHandler(nullptr);
        if (connected) { if (compCP) compCP->disconnect(&toController); if (ctrlCP) ctrlCP->disconnect(&toProcessor); }
        compCP = nullptr; ctrlCP = nullptr;
        processor = nullptr;
        if (controller && !singleObject) { controller->terminate(); }
        controller = nullptr;
        if (component) component->terminate();
        component = nullptr;
        module = nullptr;
    }
    const PluginInfo& info() const override { return pinfo; }
    void setHostOptions(const HostOptions& o) override { opt = o; }

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
            p.id = pi.id; p.name = asciiClean(VST3::StringConvert::convert(pi.title)); p.units = asciiClean(VST3::StringConvert::convert(pi.units));
            p.defaultValue = pi.defaultNormalizedValue; p.steps = pi.stepCount;
            p.automatable = (pi.flags & ParameterInfo::kCanAutomate) != 0; p.readOnly = (pi.flags & ParameterInfo::kIsReadOnly) != 0;
            p.isBypass = (pi.flags & ParameterInfo::kIsBypass) != 0; p.hidden = (pi.flags & ParameterInfo::kIsHidden) != 0;
            v.push_back(p);
        }
        return v;
    }
    double getParam(uint32_t id) const override { return controller ? controller->getParamNormalized(id) : 0; }
    void setParam(uint32_t id, double value) override {
        handler.touch(id);
        if (controller) controller->setParamNormalized(id, value);
        std::lock_guard<std::mutex> g(transferLock);
        transfer.addChange(id, value, 0);
    }
    std::string paramText(uint32_t id, double value) const override {
        String128 s = {0};
        if (!controller || controller->getParamStringByValue(id, value, s) != kResultOk) return "";
        return asciiClean(VST3::StringConvert::convert(s));
    }

    std::string busLine(MediaType t, BusDirection d, int i) const {
        BusInfo bi{};
        tresult r = component->getBusInfo(t, d, i, bi);
        char b[400];
        if (r != kResultOk) { snprintf(b, sizeof b, "%s %s %d: getBusInfo = %s", t == kAudio ? "audio" : "event", d == kInput ? "in" : "out", i, rc(r)); return b; }
        snprintf(b, sizeof b, "%s %s %d \"%s\": %s, %d ch%s", t == kAudio ? "audio" : "event", d == kInput ? "in" : "out", i, asciiClean(VST3::StringConvert::convert(bi.name)).c_str(),
                 bi.busType == kMain ? "main" : "aux", bi.channelCount, (bi.flags & BusInfo::kDefaultActive) ? ", default active" : ", default inactive");
        return b;
    }

    bool prepare(double sr, int block, bool offline, std::string& err) override {
        std::vector<std::string>& L = prepareLines; L.clear();
        char b[600];
        if (active) { processor->setProcessing(false); component->setActive(false); active = false; }
        int nIn = component->getBusCount(kAudio, kInput), nOut = component->getBusCount(kAudio, kOutput);
        int nEvIn = component->getBusCount(kEvent, kInput), nEvOut = component->getBusCount(kEvent, kOutput);
        std::string asked = "buses the plug-in offers:";
        for (int i = 0; i < nIn; i++) asked += " [" + busLine(kAudio, kInput, i) + "]";
        for (int i = 0; i < nOut; i++) asked += " [" + busLine(kAudio, kOutput, i) + "]";
        for (int i = 0; i < nEvIn; i++) asked += " [" + busLine(kEvent, kInput, i) + "]";
        for (int i = 0; i < nEvOut; i++) asked += " [" + busLine(kEvent, kOutput, i) + "]";
        L.push_back(asked);
        if (processor->canProcessSampleSize(kSample32) != kResultOk) { err = "the plug-in cannot work with 32-bit float audio"; L.push_back("canProcessSampleSize(32-bit) = no"); return false; }
        ProcessSetup setup{offline ? kOffline : kRealtime, kSample32, block, sr};
        auto doSetup = [&]() -> bool {
            tresult r = processor->setupProcessing(setup);
            snprintf(b, sizeof b, "setupProcessing(%s, 32-bit float, %.0f Hz, largest block %d) = %s", offline ? "offline" : "realtime", sr, block, rc(r)); L.push_back(b);
            if (r != kResultOk && r != kNotImplemented) { err = std::string("setupProcessing failed: ") + rc(r); return false; }
            return true;
        };
        auto doBuses = [&]() {
            std::vector<SpeakerArrangement> ins(nIn), outs(nOut);
            std::string pref;
            for (int i = 0; i < nIn; i++) {
                BusInfo bi{}; component->getBusInfo(kAudio, kInput, i, bi);
                tresult r = processor->getBusArrangement(kInput, i, ins[i]);
                if (r != kResultOk) ins[i] = arrFor(bi.channelCount);
                pref += " in " + std::to_string(i) + ": " + arrName(ins[i]) + (r != kResultOk ? std::string(" (getBusArrangement = ") + rc(r) + ")" : "");
                if (!opt.preferredArrangements && i == 0) ins[i] = SpeakerArr::kStereo;
            }
            for (int i = 0; i < nOut; i++) {
                BusInfo bi{}; component->getBusInfo(kAudio, kOutput, i, bi);
                tresult r = processor->getBusArrangement(kOutput, i, outs[i]);
                if (r != kResultOk) outs[i] = arrFor(bi.channelCount);
                pref += " out " + std::to_string(i) + ": " + arrName(outs[i]) + (r != kResultOk ? std::string(" (getBusArrangement = ") + rc(r) + ")" : "");
                if (!opt.preferredArrangements && i == 0) outs[i] = SpeakerArr::kStereo;
            }
            L.push_back("arrangements the plug-in prefers:" + (pref.empty() ? std::string(" none") : pref));
            SpeakerArrangement none = SpeakerArr::kEmpty;     // some plug-ins crash on a null pointer here (JUCE's note)
            tresult r = processor->setBusArrangements(nIn ? ins.data() : &none, nIn, nOut ? outs.data() : &none, nOut);
            std::string gave;
            for (int i = 0; i < nIn; i++) gave += " in " + std::to_string(i) + ": " + arrName(ins[i]);
            for (int i = 0; i < nOut; i++) gave += " out " + std::to_string(i) + ": " + arrName(outs[i]);
            std::string now;
            for (int i = 0; i < nIn; i++) { SpeakerArrangement a = 0; processor->getBusArrangement(kInput, i, a); now += " in " + std::to_string(i) + ": " + arrName(a); }
            for (int i = 0; i < nOut; i++) { SpeakerArrangement a = 0; processor->getBusArrangement(kOutput, i, a); now += " out " + std::to_string(i) + ": " + arrName(a); }
            L.push_back(std::string("setBusArrangements(") + (gave.empty() ? " none" : gave) + " ) = " + rc(r) + "; the plug-in now has" + (now.empty() ? " none" : now));
            std::string act = "activateBus:";
            for (int dir = 0; dir < 2; dir++) {
                BusDirection d = dir == 0 ? kInput : kOutput; int n = dir == 0 ? nIn : nOut;
                for (int i = 0; i < n; i++) {
                    BusInfo bi{}; component->getBusInfo(kAudio, d, i, bi);
                    bool on = opt.preferredArrangements ? (opt.allAudioBuses || (bi.busType == kMain && (i == 0 || (bi.flags & BusInfo::kDefaultActive)))) : (i == 0 || opt.allAudioBuses);   // main buses the plug-in wants on; aux buses off (they still get buffers)
                    tresult ar = component->activateBus(kAudio, d, i, on);
                    act += std::string(" audio ") + (d == kInput ? "in " : "out ") + std::to_string(i) + (on ? " on" : " off") + " = " + rc(ar) + ";";
                }
            }
            for (int i = 0; i < nEvIn; i++) {
                bool on = opt.allEventInputs || i == 0;
                tresult ar = component->activateBus(kEvent, kInput, i, on);
                act += " event in " + std::to_string(i) + (on ? " on" : " off") + " = " + rc(ar) + ";";
            }
            L.push_back(act);
        };
        if (opt.validatorOrder) { if (!doSetup()) return false; doBuses(); }
        else { doBuses(); if (!doSetup()) return false; }
        tresult ra = component->setActive(true);
        snprintf(b, sizeof b, "setActive(true) = %s", rc(ra)); L.push_back(b);
        if (ra != kResultOk) { err = std::string("setActive failed: ") + rc(ra); return false; }
        tresult rp = processor->setProcessing(true);
        snprintf(b, sizeof b, "setProcessing(true) = %s%s", rc(rp), rp == kNotImplemented ? " (allowed)" : ""); L.push_back(b);
        active = true; maxBlock = block;
        data.unprepare();
        data.prepare(*component, block, kSample32);    // buffers for every bus (aux buses too, active or not), owned by the host
        data.inputEvents = &events; data.inputParameterChanges = &inChanges; data.outputParameterChanges = &outChanges;
        data.processContext = &pctx; data.processMode = setup.processMode; data.symbolicSampleSize = kSample32;
        std::string bufs = "process data: ";
        for (int i = 0; i < data.numInputs; i++) bufs += "in bus " + std::to_string(i) + " " + std::to_string(data.inputs[i].numChannels) + " ch; ";
        for (int i = 0; i < data.numOutputs; i++) bufs += "out bus " + std::to_string(i) + " " + std::to_string(data.outputs[i].numChannels) + " ch; ";
        bufs += "event list, parameter changes in and out, process context (tempo 120, 4/4, playing" + std::string(opt.fullContext ? ", system time, bar position" : "") + "), note ids " + (opt.uniqueNoteIds ? "unique" : "-1");
        L.push_back(bufs);
        latency = (int)processor->getLatencySamples();
        uint32 t = processor->getTailSamples();
        tail = t == kInfiniteTail ? -1 : (int64_t)t;
        handler.latencyChanged = false;
        dBlocks = 0; dMainNZ = 0; dOtherNZ = 0; dSilFlag = 0; dNotOk = 0; dPeakMain = 0; dPeakOther = 0;
        return true;
    }

    bool process(const float* const* in, int inCh, float** out, int outCh, int frames, const NoteEvent* notes, int noteCount, const al::ProcessContext& c) override {
        if (!active || frames > maxBlock) return false;
        for (int i = 0; i < noteCount; i++) {
            Event e{};
            int ch = notes[i].channel & 15, pitch = notes[i].pitch & 127;
            e.busIndex = 0; e.sampleOffset = std::max(0, std::min(frames - 1, notes[i].offset)); e.flags = Event::kIsLive;
            if (notes[i].on) {
                int32 id = -1;
                if (opt.uniqueNoteIds) { id = nextNoteId++; if (nextNoteId > 0x3fffffff) nextNoteId = 1; liveIds[ch][pitch] = id; }
                e.type = Event::kNoteOnEvent; e.noteOn.channel = (int16)ch; e.noteOn.pitch = (int16)pitch; e.noteOn.velocity = std::max(0.f, std::min(1.f, notes[i].velocity)); e.noteOn.noteId = id; e.noteOn.length = 0; e.noteOn.tuning = 0;
                dOn++;
            } else {
                int32 id = -1;
                if (opt.uniqueNoteIds) { id = liveIds[ch][pitch]; liveIds[ch][pitch] = -1; }
                e.type = Event::kNoteOffEvent; e.noteOff.channel = (int16)ch; e.noteOff.pitch = (int16)pitch; e.noteOff.velocity = 0; e.noteOff.noteId = id; e.noteOff.tuning = 0;
                dOff++;
            }
            if (events.addEvent(e) != kResultOk) dRej++;
        }
        if (transferLock.try_lock()) { transfer.transferChangesTo(inChanges); transferLock.unlock(); }
        if (inChanges.getParameterCount() > 0) dParams += inChanges.getParameterCount();
        double ppq = (double)c.samplePos / c.sampleRate * c.tempo / 60.0;
        pctx.state = (c.playing ? Vst::ProcessContext::kPlaying : 0) | Vst::ProcessContext::kTempoValid | Vst::ProcessContext::kTimeSigValid | Vst::ProcessContext::kProjectTimeMusicValid | Vst::ProcessContext::kContTimeValid;
        pctx.sampleRate = c.sampleRate; pctx.tempo = c.tempo; pctx.projectTimeSamples = c.samplePos; pctx.continousTimeSamples = c.samplePos;
        pctx.projectTimeMusic = ppq; pctx.timeSigNumerator = 4; pctx.timeSigDenominator = 4;
        if (opt.fullContext) {
            pctx.state |= Vst::ProcessContext::kSystemTimeValid | Vst::ProcessContext::kBarPositionValid;
            pctx.systemTime = (int64)std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::steady_clock::now().time_since_epoch()).count();
            pctx.barPositionMusic = std::floor(ppq / 4.0) * 4.0;
        } else { pctx.systemTime = 0; pctx.barPositionMusic = 0; }
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
        // measure what the plug-in wrote, before the host touches it
        dBlocks++; dLastRes = (int)r; if (r != kResultOk) dNotOk++;
        for (int b = 0; b < data.numOutputs; b++) {
            float pk = 0;
            for (int ch = 0; ch < data.outputs[b].numChannels; ch++) {
                const float* d = data.outputs[b].channelBuffers32[ch]; if (!d) continue;
                for (int i = 0; i < frames; i++) { float a = std::fabs(d[i]); if (a > pk) pk = a; }
            }
            if (data.outputs[b].silenceFlags) dSilFlag++;
            if (b == 0) { if (pk > 0) dMainNZ++; if (pk > dPeakMain.load()) dPeakMain = pk; }
            else { if (pk > 0) dOtherNZ++; if (pk > dPeakOther.load()) dPeakOther = pk; }
        }
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

    HostDiag diag() const override {
        HostDiag d;
        d.setup = createLines; d.setup.insert(d.setup.end(), prepareLines.begin(), prepareLines.end());
        d.blocks = dBlocks; d.blocksMainNonZero = dMainNZ; d.blocksOtherNonZero = dOtherNZ; d.blocksSilenceFlag = dSilFlag; d.processNotOk = dNotOk;
        d.noteOns = dOn; d.noteOffs = dOff; d.eventsRejected = dRej; d.paramChanges = dParams;
        d.peakMain = dPeakMain; d.peakOther = dPeakOther; d.lastProcessResult = dLastRes;
        d.msgToProcessor = mToProc; d.msgToController = mToCtrl; d.msgOffMainThread = mOff; d.msgDropped = mDrop;
        d.setComponentStateResult = syncRes; d.stateBytes = stateBytes;
        return d;
    }

    // ---- factory presets: the plug-in's program list, then .vstpreset files in the standard folders ----
    std::vector<PresetInfo> presets() override {
        std::vector<PresetInfo> v;
        if (controller) {
            FUnknownPtr<IUnitInfo> ui(controller);
            ProgramListID listId = kNoProgramListId;
            bool hasPc = false;
            for (int i = 0, n = controller->getParameterCount(); i < n; i++) { ParameterInfo pi{}; if (controller->getParameterInfo(i, pi) == kResultOk && (pi.flags & ParameterInfo::kIsProgramChange)) { hasPc = true; break; } }
            if (ui && hasPc) {
                for (int32 i = 0; i < ui->getUnitCount(); i++) { UnitInfo u{}; if (ui->getUnitInfo(i, u) == kResultOk && u.id == kRootUnitId) listId = u.programListId; }
                if (listId == kNoProgramListId && ui->getProgramListCount() > 0) { ProgramListInfo li{}; if (ui->getProgramListInfo(0, li) == kResultOk) listId = li.id; }
                for (int32 i = 0; i < ui->getProgramListCount(); i++) {
                    ProgramListInfo li{}; if (ui->getProgramListInfo(i, li) != kResultOk || li.id != listId) continue;
                    for (int32 k = 0; k < li.programCount && k < 512; k++) {
                        String128 nm = {0}; ui->getProgramName(li.id, k, nm);
                        PresetInfo p; p.name = asciiClean(VST3::StringConvert::convert(nm)); p.source = "program list"; p.index = k; v.push_back(p);
                    }
                }
            }
        }
        namespace fs = std::filesystem;
        std::vector<std::string> roots;
        const char* home = getenv("HOME");
#if defined(__APPLE__)
        if (home) roots.push_back(std::string(home) + "/Library/Audio/Presets");
        roots.push_back("/Library/Audio/Presets");
#else
        if (home) roots.push_back(std::string(home) + "/.vst3/presets");
        roots.push_back("/usr/share/vst3/presets"); roots.push_back("/usr/local/share/vst3/presets");
#endif
        int files = 0;
        for (auto& r : roots) {
            fs::path dir = fs::path(r) / pinfo.vendor / pinfo.name;
            std::error_code ec;
            if (!fs::is_directory(dir, ec)) continue;
            std::vector<std::string> found;
            for (fs::recursive_directory_iterator it(dir, fs::directory_options::skip_permission_denied, ec), end; !ec && it != end; it.increment(ec))
                if (it->path().extension() == ".vstpreset") found.push_back(it->path().string());
            std::sort(found.begin(), found.end());
            for (auto& f : found) { if (files++ > 500) break; PresetInfo p; p.name = asciiClean(fs::path(f).stem().string()); p.source = f; v.push_back(p); }
        }
        return v;
    }
    bool loadPreset(const PresetInfo& p, std::string& err) override {
        if (handler.onEvent) handler.onEvent(evPresetLoaded, (uint32_t)p.index);
        if (p.source == "program list") {
            if (!controller) { err = "no controller"; return false; }
            int n = controller->getParameterCount();
            for (int i = 0; i < n; i++) {
                ParameterInfo pi{};
                if (controller->getParameterInfo(i, pi) != kResultOk || !(pi.flags & ParameterInfo::kIsProgramChange)) continue;
                double v = pi.stepCount > 0 ? std::min(1.0, (double)p.index / pi.stepCount) : 0;
                setParam(pi.id, v);
                return true;
            }
            err = "the plug-in lists programs but has no program-change parameter"; return false;
        }
        IPtr<IBStream> st = owned(FileStream::open(p.source.c_str(), "rb"));
        if (!st) { err = "could not open " + p.source; return false; }
        if (!PresetFile::loadPreset(st, FUID::fromTUID(classId.data()), component, controller)) { err = "the preset file was not accepted (another plug-in's, or damaged)"; return false; }
        return true;
    }

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
        if (handler.onEvent) handler.onEvent(evStateSet, (uint32_t)in.size());
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
    void setEventSink(std::function<void(uint32_t, uint32_t)> f) override { handler.onEvent = std::move(f); }
    std::set<uint32_t> takeTouchedParams() override { std::lock_guard<std::mutex> g(handler.touchedLock); std::set<uint32_t> t; t.swap(handler.touched); return t; }
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
            p.format = "vst3"; p.path = path; p.uid = c.ID().toString(); p.name = asciiClean(c.name()); p.vendor = asciiClean(c.vendor().empty() ? mod->getFactory().info().vendor() : c.vendor());
            p.version = asciiClean(c.version()); p.sdk = c.sdkVersion(); p.categories = c.subCategoriesString();
            p.isInstrument = p.categories.find("Instrument") != std::string::npos;
            p.isEffect = !p.isInstrument || p.categories.find("Fx") != std::string::npos;
            r.plugins.push_back(p);
        }
        r.ok = true;
        return r;
    }
    std::unique_ptr<PluginInstance> create(const PluginInfo& info, std::string& err) override { return createWith(info, HostOptions(), err); }
    std::unique_ptr<PluginInstance> createWith(const PluginInfo& info, const HostOptions& o, std::string& err) override {
        FUnknown* ctx = static_cast<IHostApplication*>(&hostApp());
        auto inst = std::make_unique<Vst3Instance>();
        inst->pinfo = info; inst->opt = o;
        inst->module = VST3::Hosting::Module::create(info.path, err);
        if (!inst->module) { if (err.empty()) err = "the bundle could not be loaded"; return nullptr; }
        auto factory = inst->module->getFactory();
        bool found = false;
        char b[400];
        auto& L = inst->createLines;
        for (auto& c : factory.classInfos()) {
            if (c.category() != kVstAudioEffectClass) continue;
            if (!info.uid.empty() && c.ID().toString() != info.uid) continue;
            if (info.uid.empty() && !info.name.empty() && c.name() != info.name && asciiClean(c.name()) != info.name) continue;
            inst->classId = c.ID();
            inst->pinfo.uid = c.ID().toString(); inst->pinfo.name = asciiClean(c.name()); inst->pinfo.vendor = asciiClean(c.vendor().empty() ? factory.info().vendor() : c.vendor()); inst->pinfo.version = asciiClean(c.version());
            inst->pinfo.categories = c.subCategoriesString(); inst->pinfo.sdk = c.sdkVersion(); inst->pinfo.format = "vst3";
            inst->pinfo.isInstrument = inst->pinfo.categories.find("Instrument") != std::string::npos;
            inst->pinfo.isEffect = !inst->pinfo.isInstrument || inst->pinfo.categories.find("Fx") != std::string::npos;
            found = true;
            break;
        }
        if (!found) { err = "no such plug-in in this bundle"; return nullptr; }
        snprintf(b, sizeof b, "plug-in: %s by %s, version %s, built with %s, categories %s", inst->pinfo.name.c_str(), inst->pinfo.vendor.c_str(), inst->pinfo.version.c_str(), inst->pinfo.sdk.c_str(), inst->pinfo.categories.c_str());
        L.push_back(b);
        // the processor part ("component")
        inst->component = factory.createInstance<IComponent>(inst->classId);
        if (!inst->component) { err = "the plug-in gave no audio component"; return nullptr; }
        tresult r = inst->component->initialize(ctx);
        snprintf(b, sizeof b, "component initialize = %s", rc(r)); L.push_back(b);
        if (r != kResultOk) { err = std::string("the plug-in failed to initialise: ") + rc(r); inst->component = nullptr; return nullptr; }
        inst->processor = FUnknownPtr<IAudioProcessor>(inst->component);
        if (!inst->processor) { err = "the plug-in gave no audio processor"; return nullptr; }
        // the controller part: the same object, or a second class made from its id
        IEditController* same = nullptr;
        if (inst->component->queryInterface(IEditController::iid, (void**)&same) == kResultOk && same) {
            inst->controller = owned(same); inst->singleObject = true;
            L.push_back("controller: the same object as the processor (single component)");
        } else {
            TUID cid;
            if (inst->component->getControllerClassId(cid) == kResultOk) {
                inst->controller = factory.createInstance<IEditController>(VST3::UID(cid));
                if (inst->controller) {
                    tresult rc2 = inst->controller->initialize(ctx);
                    snprintf(b, sizeof b, "controller: a separate object, initialize = %s", rc(rc2)); L.push_back(b);
                    if (rc2 != kResultOk) inst->controller = nullptr;
                } else L.push_back("controller: its class could not be created");
            } else L.push_back("controller: none (the plug-in names no controller class)");
        }
        inst->handler.transfer = &inst->transfer; inst->handler.lock = &inst->transferLock;
        if (inst->controller) inst->controller->setComponentHandler(&inst->handler);
        // connect the two parts through counting links (only when they are separate objects)
        if (inst->controller && !inst->singleObject) {
            inst->compCP = FUnknownPtr<IConnectionPoint>(inst->component);
            inst->ctrlCP = FUnknownPtr<IConnectionPoint>(inst->controller);
            if (inst->compCP && inst->ctrlCP) {
                auto tid = std::this_thread::get_id();
                inst->toController.mainId = tid; inst->toController.anyThread = &inst->opt.messagesAnyThread;
                inst->toController.count = &inst->mToCtrl; inst->toController.off = &inst->mOff; inst->toController.dropped = &inst->mDrop;
                inst->toProcessor.mainId = tid; inst->toProcessor.anyThread = &inst->opt.messagesAnyThread;
                inst->toProcessor.count = &inst->mToProc; inst->toProcessor.off = &inst->mOff; inst->toProcessor.dropped = &inst->mDrop;
                inst->toController.src = inst->compCP; inst->toController.dst = inst->ctrlCP;
                inst->toProcessor.src = inst->ctrlCP; inst->toProcessor.dst = inst->compCP;
                tresult c1 = inst->compCP->connect(&inst->toController);
                tresult c2 = inst->ctrlCP->connect(&inst->toProcessor);
                inst->connected = true;
                snprintf(b, sizeof b, "processor and controller connected (IConnectionPoint): processor = %s, controller = %s; messages from other threads: %s", rc(c1), rc(c2),
                         o.messagesAnyThread ? "delivered (as JUCE's host)" : "dropped (as the SDK's proxy in 0.4)");
                L.push_back(b);
            } else L.push_back(std::string("processor and controller NOT connected: IConnectionPoint on the processor ") + (inst->compCP ? "yes" : "no") + ", on the controller " + (inst->ctrlCP ? "yes" : "no"));
        }
        // give the controller the processor's state, so both start from the same patch (JUCE: synchroniseStates)
        if (inst->controller && o.syncControllerState) {
            MemoryStream st;
            tresult g = inst->component->getState(&st);
            inst->stateBytes = (int)st.getSize();
            if (g == kResultOk) {
                st.seek(0, IBStream::kIBSeekSet, nullptr);
                tresult sr2 = inst->controller->setComponentState(&st);
                inst->syncRes = (int)sr2;
                snprintf(b, sizeof b, "controller->setComponentState(the processor's state, %d bytes) = %s", inst->stateBytes, rc(sr2)); L.push_back(b);
            } else { snprintf(b, sizeof b, "component->getState = %s, so the controller was not given it", rc(g)); L.push_back(b); }
        } else if (inst->controller) L.push_back("controller->setComponentState: not called (as in 0.4)");
        int np = inst->controller ? inst->controller->getParameterCount() : 0;
        snprintf(b, sizeof b, "parameters: %d; messages so far: %d to the processor, %d to the controller, %d from other threads, %d dropped", np, inst->mToProc.load(), inst->mToCtrl.load(), inst->mOff.load(), inst->mDrop.load());
        L.push_back(b);
        return inst;
    }
};

PluginFormat* vst3Format() { static Vst3Format f; return &f; }

}  // namespace al
