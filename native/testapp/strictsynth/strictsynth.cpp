// "AL Strict Synth" (task NL5): a test instrument for the host, never shipped. It behaves the way we suspect Phase Plant
// and Pigments behave: its processor makes no sound until its controller has sent it the patch, and the controller only
// does that after the host has given it the processor's state (setComponentState), from a loader thread, as a big
// patch would be prepared off the main thread. A host that skips setComponentState, or drops messages that do not
// come from the main thread (the SDK's ConnectionProxy, used by test apps 0.1 to 0.4), gets silence.
#include "public.sdk/source/main/pluginfactory.h"
#include "public.sdk/source/vst/vstaudioeffect.h"
#include "public.sdk/source/vst/vsteditcontroller.h"
#include "pluginterfaces/vst/ivstevents.h"
#include "pluginterfaces/vst/ivstmessage.h"
#include "base/source/fstreamer.h"
#include <atomic>
#include <chrono>
#include <cmath>
#include <thread>

using namespace Steinberg;
using namespace Steinberg::Vst;

static const FUID ProcUID(0x4A1C0D01, 0x5E3B4F21, 0x9A7C2B11, 0x7D30AA01);
static const FUID CtrlUID(0x4A1C0D02, 0x5E3B4F21, 0x9A7C2B11, 0x7D30AA02);

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
        if (d.inputEvents) {
            int n = d.inputEvents->getEventCount();
            for (int i = 0; i < n; i++) {
                Event e{}; if (d.inputEvents->getEvent(i, e) != kResultOk) continue;
                if (e.type == Event::kNoteOnEvent && e.noteOn.velocity > 0) { freq = 440.0 * std::pow(2.0, (e.noteOn.pitch - 69) / 12.0); env = e.noteOn.velocity; }
                else if (e.type == Event::kNoteOffEvent || (e.type == Event::kNoteOnEvent && e.noteOn.velocity == 0)) env *= 0.3;
            }
        }
        if (d.numOutputs < 1 || d.outputs[0].numChannels < 1) return kResultOk;
        for (int i = 0; i < d.numSamples; i++) {
            float v = 0;
            if (armed && env > 1e-4) { v = (float)(std::sin(phase * 2 * M_PI) * env * gain); phase += freq / sr; if (phase >= 1) phase -= 1; env *= 0.99995; }
            for (int c = 0; c < d.outputs[0].numChannels; c++) d.outputs[0].channelBuffers32[c][i] = v;
        }
        d.outputs[0].silenceFlags = 0;
        return kResultOk;
    }
    std::atomic<bool> armed{false};
    std::atomic<float> gain{0};
    double sr = 48000, phase = 0, freq = 440, env = 0;
};

class StrictController : public EditController {
public:
    static FUnknown* make(void*) { return (IEditController*)new StrictController; }
    tresult PLUGIN_API setComponentState(IBStream*) override {
        // prepare the patch on a loader thread, then send it to the processor from that thread
        if (loader.joinable()) loader.join();
        loader = std::thread([this] {
            std::this_thread::sleep_for(std::chrono::milliseconds(20));
            if (IPtr<IMessage> m = owned(allocateMessage())) { m->setMessageID("patch"); m->getAttributes()->setInt("gain", 50); sendMessage(m); }
        });
        return kResultOk;
    }
    tresult PLUGIN_API terminate() override { if (loader.joinable()) loader.join(); return EditController::terminate(); }
    std::thread loader;
};

BEGIN_FACTORY_DEF("AudioLab test", "https://github.com/Audio-lab-DAW", "mailto:none@example.com")
DEF_CLASS2(INLINE_UID_FROM_FUID(ProcUID), PClassInfo::kManyInstances, kVstAudioEffectClass, "AL Strict Synth", Vst::kDistributable, "Instrument|Synth", "0.5.0", kVstVersionString, StrictProcessor::make)
DEF_CLASS2(INLINE_UID_FROM_FUID(CtrlUID), PClassInfo::kManyInstances, kVstComponentControllerClass, "AL Strict Synth Controller", 0, "", "0.5.0", kVstVersionString, StrictController::make)
END_FACTORY
