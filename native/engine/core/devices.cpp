// The devices the engine core has so far (task NB-N3a). Each line: the app's device type, the ported processor.
#include "dev_crush.h"
#include "dev_dynamics.h"

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
}
}  // namespace al
