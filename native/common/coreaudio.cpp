// Core Audio (HAL) device list and output stream. Task NM1. Uses the HAL directly (AudioObject properties and
// an IOProc on the device), the lowest public level: the same level that gives exclusive use, the device's
// real formats and its own buffer size.
#ifdef __APPLE__
#include "coreaudio.h"
#include "json.h"
#include <CoreAudio/CoreAudio.h>
#include <CoreFoundation/CoreFoundation.h>
#include <mach/mach_time.h>
#include <unistd.h>

namespace al {

static AudioObjectPropertyAddress addr(AudioObjectPropertySelector s, AudioObjectPropertyScope sc = kAudioObjectPropertyScopeGlobal, UInt32 el = kAudioObjectPropertyElementMain) {
    AudioObjectPropertyAddress a = {s, sc, el};
    return a;
}
static bool has(AudioObjectID id, AudioObjectPropertyAddress a) { return AudioObjectHasProperty(id, &a); }
static bool settable(AudioObjectID id, AudioObjectPropertyAddress a) {
    Boolean s = false;
    if (!AudioObjectHasProperty(id, &a)) return false;
    return AudioObjectIsPropertySettable(id, &a, &s) == noErr && s;
}
template <class T> static bool get(AudioObjectID id, AudioObjectPropertyAddress a, T& v) {
    UInt32 sz = sizeof(T);
    if (!AudioObjectHasProperty(id, &a)) return false;
    return AudioObjectGetPropertyData(id, &a, 0, nullptr, &sz, &v) == noErr;
}
static std::vector<uint8_t> getBytes(AudioObjectID id, AudioObjectPropertyAddress a) {
    std::vector<uint8_t> b;
    UInt32 sz = 0;
    if (!AudioObjectHasProperty(id, &a)) return b;
    if (AudioObjectGetPropertyDataSize(id, &a, 0, nullptr, &sz) != noErr || !sz) return b;
    b.resize(sz);
    if (AudioObjectGetPropertyData(id, &a, 0, nullptr, &sz, b.data()) != noErr) b.clear(); else b.resize(sz);
    return b;
}
static std::string str(AudioObjectID id, AudioObjectPropertyAddress a) {
    CFStringRef s = nullptr;
    if (!get(id, a, s) || !s) return "";
    char buf[512] = {0};
    CFStringGetCString(s, buf, sizeof buf, kCFStringEncodingUTF8);
    CFRelease(s);
    return buf;
}
static std::string transportName(UInt32 t) {
    switch (t) {
        case kAudioDeviceTransportTypeBuiltIn: return "built-in";
        case kAudioDeviceTransportTypeUSB: return "USB";
        case kAudioDeviceTransportTypeBluetooth: return "Bluetooth";
        case kAudioDeviceTransportTypeBluetoothLE: return "Bluetooth LE";
        case kAudioDeviceTransportTypeHDMI: return "HDMI";
        case kAudioDeviceTransportTypeDisplayPort: return "DisplayPort";
        case kAudioDeviceTransportTypeAirPlay: return "AirPlay";
        case kAudioDeviceTransportTypeThunderbolt: return "Thunderbolt";
        case kAudioDeviceTransportTypeFireWire: return "FireWire";
        case kAudioDeviceTransportTypePCI: return "PCI";
        case kAudioDeviceTransportTypeAggregate: return "aggregate";
        case kAudioDeviceTransportTypeVirtual: return "virtual";
        case kAudioDeviceTransportTypeAVB: return "AVB";
        default: {
            char c[5] = {(char)(t >> 24), (char)(t >> 16), (char)(t >> 8), (char)t, 0};
            return t ? std::string(c) : "unknown";
        }
    }
}
static int channels(AudioObjectID id, AudioObjectPropertyScope sc) {
    auto b = getBytes(id, addr(kAudioDevicePropertyStreamConfiguration, sc));
    if (b.size() < sizeof(UInt32)) return 0;
    const AudioBufferList* l = (const AudioBufferList*)b.data();
    int n = 0;
    for (UInt32 i = 0; i < l->mNumberBuffers; i++) n += (int)l->mBuffers[i].mNumberChannels;
    return n;
}
static std::string fmtName(const AudioStreamBasicDescription& f) {
    char b[160];
    const char* kind = f.mFormatID != kAudioFormatLinearPCM ? "not PCM" : (f.mFormatFlags & kAudioFormatFlagIsFloat) ? "float" : "integer";
    snprintf(b, sizeof b, "%u-bit %s, %u ch, %.0f Hz, %s", (unsigned)f.mBitsPerChannel, kind, (unsigned)f.mChannelsPerFrame, f.mSampleRate,
             (f.mFormatFlags & kAudioFormatFlagIsNonMixable) ? "not mixable (exclusive format)" : "mixable");
    return b;
}

uint32_t defaultOutputDevice() {
    AudioObjectID d = kAudioObjectUnknown;
    get(kAudioObjectSystemObject, addr(kAudioHardwarePropertyDefaultOutputDevice), d);
    return d;
}

std::vector<DeviceInfo> listDevices() {
    std::vector<DeviceInfo> out;
    auto b = getBytes(kAudioObjectSystemObject, addr(kAudioHardwarePropertyDevices));
    AudioObjectID defOut = defaultOutputDevice(), defIn = kAudioObjectUnknown;
    get(kAudioObjectSystemObject, addr(kAudioHardwarePropertyDefaultInputDevice), defIn);
    size_t n = b.size() / sizeof(AudioObjectID);
    const AudioObjectID* ids = (const AudioObjectID*)b.data();
    for (size_t i = 0; i < n; i++) {
        AudioObjectID id = ids[i];
        DeviceInfo d;
        d.id = id;
        d.name = str(id, addr(kAudioObjectPropertyName));
        d.manufacturer = str(id, addr(kAudioObjectPropertyManufacturer));
        d.uid = str(id, addr(kAudioDevicePropertyDeviceUID));
        UInt32 t = 0; get(id, addr(kAudioDevicePropertyTransportType), t); d.transport = transportName(t);
        const AudioObjectPropertyScope O = kAudioObjectPropertyScopeOutput, I = kAudioObjectPropertyScopeInput;
        d.outChannels = channels(id, O); d.inChannels = channels(id, I);
        Float64 r = 0; get(id, addr(kAudioDevicePropertyNominalSampleRate), r); d.rate = r;
        d.rateSettable = settable(id, addr(kAudioDevicePropertyNominalSampleRate));
        auto rb = getBytes(id, addr(kAudioDevicePropertyAvailableNominalSampleRates));
        const AudioValueRange* vr = (const AudioValueRange*)rb.data();
        for (size_t k = 0; k < rb.size() / sizeof(AudioValueRange); k++) {
            if (vr[k].mMinimum == vr[k].mMaximum) d.rates.push_back(vr[k].mMinimum);
            else d.rateRanges.push_back({vr[k].mMinimum, vr[k].mMaximum});
        }
        UInt32 u = 0;
        if (get(id, addr(kAudioDevicePropertyBufferFrameSize), u)) d.buffer = u;
        d.bufferSettable = settable(id, addr(kAudioDevicePropertyBufferFrameSize));
        AudioValueRange br = {0, 0};
        if (get(id, addr(kAudioDevicePropertyBufferFrameSizeRange), br)) { d.bufferMin = (uint32_t)br.mMinimum; d.bufferMax = (uint32_t)br.mMaximum; }
        const AudioObjectPropertyScope S = d.outChannels ? O : I;
        if (get(id, addr(kAudioDevicePropertyLatency, S), u)) d.latency = u;
        if (get(id, addr(kAudioDevicePropertySafetyOffset, S), u)) d.safetyOffset = u;
        // volume: on the main element, or per channel (1 and 2)
        if (d.outChannels) {
            Float32 v = 0;
            if (has(id, addr(kAudioDevicePropertyVolumeScalar, O, kAudioObjectPropertyElementMain))) {
                d.hasVolume = true; d.volumeWhere = "main";
                d.volumeSettable = settable(id, addr(kAudioDevicePropertyVolumeScalar, O, kAudioObjectPropertyElementMain));
                if (get(id, addr(kAudioDevicePropertyVolumeScalar, O, kAudioObjectPropertyElementMain), v)) d.volume = v;
            } else if (has(id, addr(kAudioDevicePropertyVolumeScalar, O, 1))) {
                d.hasVolume = true; d.volumeWhere = "channels 1+2";
                d.volumeSettable = settable(id, addr(kAudioDevicePropertyVolumeScalar, O, 1));
                if (get(id, addr(kAudioDevicePropertyVolumeScalar, O, 1), v)) d.volume = v;
            }
            d.hasMute = has(id, addr(kAudioDevicePropertyMute, O, kAudioObjectPropertyElementMain)) || has(id, addr(kAudioDevicePropertyMute, O, 1));
            auto sb = getBytes(id, addr(kAudioDevicePropertyStreams, O));
            if (sb.size() >= sizeof(AudioStreamID)) {
                AudioStreamID st = *(const AudioStreamID*)sb.data();
                AudioStreamBasicDescription f = {};
                if (get(st, addr(kAudioStreamPropertyPhysicalFormat), f)) d.physicalFormat = fmtName(f);
                auto fb = getBytes(st, addr(kAudioStreamPropertyAvailablePhysicalFormats));
                d.physicalFormats = (int)(fb.size() / sizeof(AudioStreamRangedDescription));
                if (get(st, addr(kAudioStreamPropertyLatency), u)) d.streamLatency = u;
            }
        }
        pid_t hp = -1;
        if (get(id, addr(kAudioDevicePropertyHogMode), hp)) d.hogPid = (int)hp;
        d.hogSettable = settable(id, addr(kAudioDevicePropertyHogMode));
        d.isDefaultOutput = id == defOut; d.isDefaultInput = id == defIn;
        out.push_back(d);
    }
    return out;
}

std::string deviceJson(const DeviceInfo& d) {
    std::string s = "{";
    s += "\"id\":" + std::to_string(d.id) + ",\"name\":" + jstr(d.name) + ",\"maker\":" + jstr(d.manufacturer) + ",\"uid\":" + jstr(d.uid) + ",\"transport\":" + jstr(d.transport);
    s += ",\"outChannels\":" + std::to_string(d.outChannels) + ",\"inChannels\":" + std::to_string(d.inChannels);
    s += ",\"defaultOutput\":" + std::string(d.isDefaultOutput ? "true" : "false") + ",\"defaultInput\":" + std::string(d.isDefaultInput ? "true" : "false");
    s += ",\"rate\":" + jnum(d.rate) + ",\"rateSettable\":" + (d.rateSettable ? "true" : "false") + ",\"rates\":[";
    for (size_t i = 0; i < d.rates.size(); i++) s += (i ? "," : "") + jnum(d.rates[i]);
    s += "],\"rateRanges\":[";
    for (size_t i = 0; i < d.rateRanges.size(); i++) s += std::string(i ? "," : "") + "[" + jnum(d.rateRanges[i].first) + "," + jnum(d.rateRanges[i].second) + "]";
    s += "],\"buffer\":" + std::to_string(d.buffer) + ",\"bufferMin\":" + std::to_string(d.bufferMin) + ",\"bufferMax\":" + std::to_string(d.bufferMax) + ",\"bufferSettable\":" + (d.bufferSettable ? "true" : "false");
    s += ",\"latencyFrames\":" + std::to_string(d.latency) + ",\"safetyOffsetFrames\":" + std::to_string(d.safetyOffset) + ",\"streamLatencyFrames\":" + std::to_string(d.streamLatency);
    s += ",\"hasVolume\":" + std::string(d.hasVolume ? "true" : "false") + ",\"volumeSettable\":" + (d.volumeSettable ? "true" : "false") + ",\"volumeWhere\":" + jstr(d.volumeWhere) + ",\"volume\":" + jnum(d.volume);
    s += ",\"hasMute\":" + std::string(d.hasMute ? "true" : "false");
    s += ",\"hogPid\":" + std::to_string(d.hogPid) + ",\"hogSettable\":" + (d.hogSettable ? "true" : "false");
    s += ",\"physicalFormat\":" + jstr(d.physicalFormat) + ",\"physicalFormats\":" + std::to_string(d.physicalFormats) + "}";
    return s;
}
std::string devicesJson(const std::vector<DeviceInfo>& v) {
    std::string s = "[";
    for (size_t i = 0; i < v.size(); i++) s += (i ? ",\n  " : "\n  ") + deviceJson(v[i]);
    return s + "\n]";
}

static std::string osErr(OSStatus e) {
    char c[5] = {(char)(e >> 24), (char)(e >> 16), (char)(e >> 8), (char)e, 0};
    bool printable = true;
    for (int i = 0; i < 4; i++) if (c[i] < 32 || c[i] > 126) printable = false;
    return printable ? std::string("'") + c + "'" : std::to_string((int)e);
}

bool setDeviceRate(uint32_t dev, double rate, double& now, std::string& err) {
    AudioObjectPropertyAddress a = addr(kAudioDevicePropertyNominalSampleRate);
    Float64 r = rate;
    OSStatus e = AudioObjectSetPropertyData(dev, &a, 0, nullptr, sizeof r, &r);
    if (e != noErr) { err = "error " + osErr(e); }
    // the change is not instant: wait up to 2 seconds for the device to report it
    for (int i = 0; i < 40; i++) {
        Float64 g = 0; get(dev, a, g); now = g;
        if (g == rate) break;
        usleep(50000);
    }
    return e == noErr && now == rate;
}
bool setDeviceBuffer(uint32_t dev, uint32_t frames, uint32_t& now, std::string& err) {
    AudioObjectPropertyAddress a = addr(kAudioDevicePropertyBufferFrameSize);
    UInt32 f = frames;
    OSStatus e = AudioObjectSetPropertyData(dev, &a, 0, nullptr, sizeof f, &f);
    if (e != noErr) err = "error " + osErr(e);
    UInt32 g = 0; get(dev, a, g); now = g;
    return e == noErr && g == frames;
}
bool setHog(uint32_t dev, bool take, int& ownerPid, std::string& err) {
    AudioObjectPropertyAddress a = addr(kAudioDevicePropertyHogMode);
    pid_t p = take ? getpid() : -1;
    OSStatus e = AudioObjectSetPropertyData(dev, &a, 0, nullptr, sizeof p, &p);
    if (e != noErr) err = "error " + osErr(e);
    pid_t g = -1; get(dev, a, g); ownerPid = (int)g;
    return e == noErr && (take ? g == getpid() : g == -1);
}

static OSStatus ioProc(AudioObjectID, const AudioTimeStamp*, const AudioBufferList*, const AudioTimeStamp*, AudioBufferList* out, const AudioTimeStamp*, void* ctx) {
    OutputStream* s = (OutputStream*)ctx;
    if (!out || !out->mNumberBuffers) return noErr;
    // frames in this cycle, from the first buffer
    const AudioBuffer& b0 = out->mBuffers[0];
    UInt32 nch0 = b0.mNumberChannels ? b0.mNumberChannels : 1;
    UInt32 frames = b0.mDataByteSize / (sizeof(Float32) * nch0);
    if (frames > s->scratch[0].size()) frames = (UInt32)s->scratch[0].size();
    float* ch[2] = {s->scratch[0].data(), s->scratch[1].data()};
    uint64_t t0 = mach_absolute_time();
    s->fn(s->user, ch, 2, (int)frames);
    uint64_t dt = mach_absolute_time() - t0;
    static mach_timebase_info_data_t tb = {0, 0};
    if (!tb.denom) mach_timebase_info(&tb);
    uint64_t ns = dt * tb.numer / tb.denom;
    s->sumNs += ns;
    if (ns > s->worstNs) s->worstNs = ns;
    // the device's buffers: one interleaved buffer, or one buffer per channel / stream. Left and right go to
    // the first two channels, everything else is silence.
    UInt32 chanIndex = 0;
    for (UInt32 i = 0; i < out->mNumberBuffers; i++) {
        AudioBuffer& b = out->mBuffers[i];
        UInt32 nch = b.mNumberChannels ? b.mNumberChannels : 1;
        Float32* d = (Float32*)b.mData;
        UInt32 fr = b.mDataByteSize / (sizeof(Float32) * nch);
        if (!d) { chanIndex += nch; continue; }
        for (UInt32 c = 0; c < nch; c++, chanIndex++) {
            if (chanIndex < 2) { const float* src = ch[chanIndex]; for (UInt32 k = 0; k < fr; k++) d[k * nch + c] = k < frames ? src[k] : 0.f; }
            else for (UInt32 k = 0; k < fr; k++) d[k * nch + c] = 0.f;
        }
    }
    s->callbacks++;
    s->framesTotal += frames;
    if (frames < s->minFrames) s->minFrames = frames;
    if (frames > s->maxFrames) s->maxFrames = frames;
    return noErr;
}
static OSStatus overloadListener(AudioObjectID, UInt32, const AudioObjectPropertyAddress*, void* ctx) {
    ((OutputStream*)ctx)->overloads++;
    return noErr;
}

bool OutputStream::start(uint32_t device, RenderFn f, void* u, std::string& err) {
    dev = device; fn = f; user = u;
    scratch[0].assign(16384, 0.f); scratch[1].assign(16384, 0.f);
    AudioDeviceIOProcID pid = nullptr;
    OSStatus e = AudioDeviceCreateIOProcID(dev, ioProc, this, &pid);
    if (e != noErr || !pid) { err = "AudioDeviceCreateIOProcID: error " + osErr(e); return false; }
    procId = (void*)pid;
    AudioObjectPropertyAddress a = addr(kAudioDeviceProcessorOverload);
    AudioObjectAddPropertyListener(dev, &a, overloadListener, this);
    e = AudioDeviceStart(dev, pid);
    if (e != noErr) { err = "AudioDeviceStart: error " + osErr(e); AudioDeviceDestroyIOProcID(dev, pid); procId = nullptr; return false; }
    running = true;
    return true;
}
void OutputStream::stop() {
    if (!procId) return;
    AudioDeviceIOProcID pid = (AudioDeviceIOProcID)procId;
    AudioDeviceStop(dev, pid);
    AudioObjectPropertyAddress a = addr(kAudioDeviceProcessorOverload);
    AudioObjectRemovePropertyListener(dev, &a, overloadListener, this);
    AudioDeviceDestroyIOProcID(dev, pid);
    procId = nullptr; running = false;
}

}  // namespace al
#endif
