// "AL Strict Synth" (tasks NL5 and NL7): a test instrument for the host, never shipped. It behaves the way we suspect Phase Plant
// and Pigments behave: its processor makes no sound until its controller has sent it the patch, and the controller only
// does that after the host has given it the processor's state (setComponentState), from a loader thread, as a big
// patch would be prepared off the main thread. A host that skips setComponentState, or drops messages that do not
// come from the main thread (the SDK's ConnectionProxy, used by test apps 0.1 to 0.4), gets silence.
// 0.7 (task NL7) adds what the test app 0.7 must cope with:
//   "Loud (+20 dBFS)"  on: the output peaks at +20 dBFS (10.0), as Phase Plant's patch did at +27.9 dBFS on the user's Mac
//   "Sneaky drift"     on: the controller keeps changing "Derive" (spelt with an accent) without telling the host (no performEdit)
//   strings outside ASCII, as Phase Plant's: value texts with U+2212 (minus) and U+202F (narrow no-break space) ("-8.0 dB"),
//   U+00A0 (no-break space) ("12.5 ms"), a parameter title and a program name with an accented letter
//   a program list (two programs) and a window of its own (empty), so the app can open it and poll while it is open
#include "public.sdk/source/main/pluginfactory.h"
#include "public.sdk/source/vst/vstaudioeffect.h"
#include "public.sdk/source/vst/vsteditcontroller.h"
#include "public.sdk/source/common/pluginview.h"
#include "pluginterfaces/gui/iplugview.h"
#include "pluginterfaces/vst/ivstevents.h"
#include "pluginterfaces/vst/ivstmessage.h"
#include "pluginterfaces/vst/ivstparameterchanges.h"
#include "base/source/fstreamer.h"
#include <atomic>
#include <chrono>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <thread>

using namespace Steinberg;
using namespace Steinberg::Vst;

static const FUID ProcUID(0x4A1C0D01, 0x5E3B4F21, 0x9A7C2B11, 0x7D30AA01);
static const FUID CtrlUID(0x4A1C0D02, 0x5E3B4F21, 0x9A7C2B11, 0x7D30AA02);
enum : ParamID { kLevel = 1, kLoud = 2, kSneaky = 3, kDrift = 4, kPrograms = 100 };

class StrictProcessor : public AudioEffect {
public:
    StrictProcessor() { setControllerClass(CtrlUID); }
    static FUnknown* make(void*) { return (IAudioProcessor*)new StrictProcessor; }
    tresult PLUGIN_API initialize(FUnknown* ctx) override {
        tresult r = AudioEffect::initialize(ctx);
        if (r != kResultOk) return r;
        addAudioOutput(STR16("Stereo Out"), SpeakerArr::kStereo);
        addEventInput(STR16("Notes"), 16);
        return kResultOk;
    }
    tresult PLUGIN_API notify(IMessage* m) override {
        if (m && strcmp(m->getMessageID(), "patch") == 0) { int64 g = 0; if (m->getAttributes()->getInt("gain", g) == kResultOk) { gain = (float)g / 100.f; armed = true; } return kResultOk; }
        return AudioEffect::notify(m);
    }
    tresult PLUGIN_API setupProcessing(ProcessSetup& s) override { sr = s.sampleRate; return AudioEffect::setupProcessing(s); }
    tresult PLUGIN_API getState(IBStream* st) override { IBStreamer s(st, kLittleEndian); s.writeInt32(42); return kResultOk; }
    tresult PLUGIN_API setState(IBStream* st) override { IBStreamer s(st, kLittleEndian); int32 v; return s.readInt32(v) ? kResultOk : kResultFalse; }
    tresult PLUGIN_API process(ProcessData& d) override {
        if (d.inputParameterChanges) {
            for (int32 i = 0, n = d.inputParameterChanges->getParameterCount(); i < n; i++) {
                IParamValueQueue* q = d.inputParameterChanges->getParameterData(i);
                if (!q || q->getPointCount() < 1) continue;
                int32 off = 0; ParamValue v = 0;
                if (q->getPoint(q->getPointCount() - 1, off, v) != kResultOk) continue;
                if (q->getParameterId() == kLevel) level = (float)(v * 2.0);
                else if (q->getParameterId() == kLoud) loud = v > 0.5;
            }
        }
        if (d.inputEvents) {
            int n = d.inputEvents->getEventCount();
            for (int i = 0; i < n; i++) {
                Event e{}; if (d.inputEvents->getEvent(i, e) != kResultOk) continue;
                if (e.type == Event::kNoteOnEvent && e.noteOn.velocity > 0) { freq = 440.0 * std::pow(2.0, (e.noteOn.pitch - 69) / 12.0); env = e.noteOn.velocity; vel = e.noteOn.velocity; }
                else if (e.type == Event::kNoteOffEvent || (e.type == Event::kNoteOnEvent && e.noteOn.velocity == 0)) env *= 0.3;
            }
        }
        if (d.numOutputs < 1 || d.outputs[0].numChannels < 1) return kResultOk;
        for (int i = 0; i < d.numSamples; i++) {
            float v = 0;
            if (armed && env > 1e-4) {
                double s = std::sin(phase * 2 * M_PI);
                // loud: the note starts at 10.0 (+20 dBFS) whatever its velocity, the way a patch far over full scale does
                v = loud ? (float)(s * (env / (vel > 0 ? vel : 1)) * 10.0) : (float)(s * env * gain * level);
                phase += freq / sr; if (phase >= 1) phase -= 1; env *= 0.99995;
            }
            for (int c = 0; c < d.outputs[0].numChannels; c++) d.outputs[0].channelBuffers32[c][i] = v;
        }
        d.outputs[0].silenceFlags = 0;
        return kResultOk;
    }
    std::atomic<bool> armed{false};
    std::atomic<float> gain{0};
    float level = 1.0f; bool loud = false;
    double sr = 48000, phase = 0, freq = 440, env = 0, vel = 0.8;
};

// An empty window of the plug-in's own (the host opens it; the app polls the parameters only while it is open).
class StrictView : public CPluginView {
public:
    explicit StrictView(const ViewRect* r) : CPluginView(r) {}
    tresult PLUGIN_API isPlatformTypeSupported(FIDString type) override {
        if (!type) return kResultFalse;
        return (strcmp(type, kPlatformTypeNSView) == 0 || strcmp(type, kPlatformTypeHWND) == 0 || strcmp(type, kPlatformTypeX11EmbedWindowID) == 0) ? kResultTrue : kResultFalse;
    }
};

static void put16(String128 out, const char16_t* s) { int i = 0; for (; s[i] && i < 127; i++) out[i] = (TChar)s[i]; out[i] = 0; }
static void ascii16(String128 out, int& at, const char* s) { for (; *s && at < 127; s++) out[at++] = (TChar)*s; out[at] = 0; }

class StrictController : public EditControllerEx1 {
public:
    static FUnknown* make(void*) { return (IEditController*)new StrictController; }
    tresult PLUGIN_API initialize(FUnknown* ctx) override {
        tresult r = EditControllerEx1::initialize(ctx);
        if (r != kResultOk) return r;
        String128 t;
        parameters.addParameter(STR16("Level"), STR16("dB"), 0, 0.5, ParameterInfo::kCanAutomate, kLevel);
        parameters.addParameter(STR16("Loud (+20 dBFS)"), nullptr, 1, 0, ParameterInfo::kCanAutomate, kLoud);
        parameters.addParameter(STR16("Sneaky drift"), nullptr, 1, 0, ParameterInfo::kCanAutomate, kSneaky);
        put16(t, u"Dérive");                                   // "Derive" with an e acute
        parameters.addParameter(t, STR16("ms"), 0, 0.25, ParameterInfo::kCanAutomate, kDrift);
        addUnit(new Unit(STR16("Root"), kRootUnitId, kNoParentUnitId, kPrograms));
        auto* list = new ProgramList(STR16("Factory"), kPrograms, kRootUnitId);
        put16(t, u"Café Init"); list->addProgram(t);
        put16(t, u"Loud − test"); list->addProgram(t);
        addProgramList(list);
        parameters.addParameter(list->getParameter());
        return kResultOk;
    }
    tresult PLUGIN_API setComponentState(IBStream*) override {
        // prepare the patch on a loader thread, then send it to the processor from that thread
        if (loader.joinable()) loader.join();
        loader = std::thread([this] {
            std::this_thread::sleep_for(std::chrono::milliseconds(20));
            if (IPtr<IMessage> m = owned(allocateMessage())) { m->setMessageID("patch"); m->getAttributes()->setInt("gain", 50); sendMessage(m); }
        });
        return kResultOk;
    }
    // value texts the way Phase Plant writes them: U+2212 for minus, U+202F before the unit; U+00A0 before "ms"
    tresult PLUGIN_API getParamStringByValue(ParamID id, ParamValue v, String128 out) override {
        if (id == kLevel) {
            double g = v * 2.0 * 0.4, db = g > 0 ? 20 * std::log10(g) : -144;
            char b[32]; snprintf(b, sizeof b, "%.1f", std::fabs(db));
            int at = 0; if (db < -0.05) out[at++] = (TChar)0x2212;
            ascii16(out, at, b); out[at++] = (TChar)0x202F; ascii16(out, at, "dB");
            return kResultOk;
        }
        if (id == kDrift) {
            char b[32]; snprintf(b, sizeof b, "%.1f", v * 50.0);
            int at = 0; ascii16(out, at, b); out[at++] = (TChar)0x00A0; ascii16(out, at, "ms");
            return kResultOk;
        }
        return EditControllerEx1::getParamStringByValue(id, v, out);
    }
    // "Derive" changes by itself while "Sneaky drift" is on, and the host is never told (no performEdit, no restart)
    ParamValue PLUGIN_API getParamNormalized(ParamID id) override {
        if (id == kDrift) return drift.load();
        return EditControllerEx1::getParamNormalized(id);
    }
    tresult PLUGIN_API setParamNormalized(ParamID id, ParamValue v) override {
        if (id == kDrift) drift = v;
        if (id == kSneaky) { if (v > 0.5) startDrift(); else stopDrift(); }
        return EditControllerEx1::setParamNormalized(id, v);
    }
    IPlugView* PLUGIN_API createView(FIDString name) override {
        if (name && strcmp(name, ViewType::kEditor) == 0) { ViewRect r(0, 0, 420, 160); return new StrictView(&r); }
        return nullptr;
    }
    void startDrift() {
        if (drifting.exchange(true)) return;
        drifter = std::thread([this] {
            while (drifting.load()) {
                std::this_thread::sleep_for(std::chrono::milliseconds(150));
                double d = drift.load() + 0.05; if (d > 1) d -= 1; drift = d;
            }
        });
    }
    void stopDrift() { drifting = false; if (drifter.joinable()) drifter.join(); }
    tresult PLUGIN_API terminate() override { stopDrift(); if (loader.joinable()) loader.join(); return EditControllerEx1::terminate(); }
    std::thread loader, drifter;
    std::atomic<bool> drifting{false};
    std::atomic<double> drift{0.25};
};

BEGIN_FACTORY_DEF("AudioLab test", "https://github.com/Audio-lab-DAW", "mailto:none@example.com")
DEF_CLASS2(INLINE_UID_FROM_FUID(ProcUID), PClassInfo::kManyInstances, kVstAudioEffectClass, "AL Strict Synth", Vst::kDistributable, "Instrument|Synth", "0.7.0", kVstVersionString, StrictProcessor::make)
DEF_CLASS2(INLINE_UID_FROM_FUID(CtrlUID), PClassInfo::kManyInstances, kVstComponentControllerClass, "AL Strict Synth Controller", 0, "", "0.7.0", kVstVersionString, StrictController::make)
END_FACTORY
