// The devices the engine core has so far (task NB-N3a). Each line: the app's device type, the ported processor.
#include "dev_comp.h"
#include "dev_crush.h"
#include "dev_dynamics.h"
#include "dev_eq.h"
#include "dev_modulation.h"
#include "dev_side.h"
#include "dev_shape.h"

namespace al {
template <class T> static ProcessorFactory mk() { return [](RenderContext& c) { return std::unique_ptr<Processor>(new T(c)); }; }
void registerCoreDevices() {
    static bool done = false;
    if (done) return;
    done = true;
    deviceRegistry()["limit"] = mk<dyn::Lim>();
    deviceRegistry()["gate"] = mk<dyn::Gate>();
    deviceRegistry()["trans"] = mk<dyn::Trn>();
    deviceRegistry()["deess"] = mk<dyn::Dss>();
    deviceRegistry()["crush"] = mk<fx::Crush>();
    // task NB-N3c: modulation and time
    deviceRegistry()["chorus"] = mk<mod::Cho>();
    deviceRegistry()["imager"] = mk<mod::Img>();
    deviceRegistry()["fshift"] = mk<mod::FSh>();
    deviceRegistry()["vocoder"] = mk<mod::Voc>();
    deviceRegistry()["tstop"] = mk<mod::Tps>();
    // task NB-N3e: the first device made of browser nodes (Chromium's BiquadFilterNode and GainNode)
    deviceRegistry()["eq"] = mk<eq::ProEQ>();
    // task NB-N3f: Chromium's DynamicsCompressorNode
    deviceRegistry()["comp"] = mk<comp::Comp>();
    // task NB-N3g: the Sidechain device (an oscillator, a wave shaper and a constant source on a GainNode's gain)
    deviceRegistry()["side"] = mk<side::Side>();
    // task NB-N3g: Chromium's WaveShaperNode (oversampled, with its FFT) and DelayNode
    deviceRegistry()["clip"] = mk<shape::Clip>();
    deviceRegistry()["drive"] = mk<shape::Drive>();
}
}  // namespace al
