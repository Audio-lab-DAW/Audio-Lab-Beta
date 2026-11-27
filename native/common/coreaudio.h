// Core Audio (HAL) device list and a plain output stream. macOS only. Task NM1.
#pragma once
#include <atomic>
#include <cstdint>
#include <string>
#include <vector>

namespace al {

struct DeviceInfo {
    uint32_t id = 0;
    std::string name, uid, transport, manufacturer;
    int outChannels = 0, inChannels = 0;
    double rate = 0;
    std::vector<double> rates;          // every rate the device offers (ranges are written as lo, hi pairs in rateRanges)
    std::vector<std::pair<double, double>> rateRanges;
    bool rateSettable = false;
    uint32_t buffer = 0, bufferMin = 0, bufferMax = 0;
    bool bufferSettable = false;
    uint32_t latency = 0, safetyOffset = 0, streamLatency = 0;
    bool hasVolume = false, volumeSettable = false;   // a volume the computer can set (on the device itself)
    std::string volumeWhere;                         // "main", "channels 1+2" or ""
    double volume = -1;
    bool hasMute = false;
    int hogPid = -1; bool hogSettable = false;
    std::string physicalFormat;                      // for example "24-bit integer, 2 ch, 96000 Hz, mixable"
    int physicalFormats = 0;
    bool isDefaultOutput = false, isDefaultInput = false;
};

std::vector<DeviceInfo> listDevices();
uint32_t defaultOutputDevice();
std::string deviceJson(const DeviceInfo& d);
std::string devicesJson(const std::vector<DeviceInfo>& v);

// Sets the device's sample rate / buffer size; returns what the device reports afterwards.
bool setDeviceRate(uint32_t dev, double rate, double& now, std::string& err);
bool setDeviceBuffer(uint32_t dev, uint32_t frames, uint32_t& now, std::string& err);
// Takes (true) or gives back (false) exclusive use of the device ("hog mode").
bool setHog(uint32_t dev, bool take, int& ownerPid, std::string& err);

// --- added for the engine (task NB-N1) ---------------------------------------------------------------
struct PhysFormat { double rate = 0; int bits = 0, channels = 0; bool isFloat = false, mixable = true; };
std::vector<PhysFormat> listPhysicalFormats(uint32_t dev);
// Picks the device's own format: rate, bit depth, and whether the system may mix other sound into it.
bool setPhysicalFormat(uint32_t dev, double rate, int bits, bool mixable, std::string& now, std::string& err);
bool getVolume(uint32_t dev, double& v);
bool setVolume(uint32_t dev, double v, std::string& err);
bool getMute(uint32_t dev, bool& m);
bool setMute(uint32_t dev, bool m);
uint32_t deviceByUid(const std::string& uid);
DeviceInfo deviceInfo(uint32_t dev);
std::string virtualFormatText(uint32_t dev);

// Tells the caller when something changes outside the program: a device comes or goes, the default output
// changes, someone turns the device's volume, the rate changes. The callback runs on a system thread.
typedef void (*WatchFn)(void* user, const char* what, uint32_t dev);
struct Watcher {
    WatchFn fn = nullptr; void* user = nullptr; uint32_t dev = 0, stream = 0; bool system = false;   // stream: its format is watched too ("format", task NB-R4)
    void start(WatchFn f, void* u);
    void watchDevice(uint32_t d);
    void stop();
};
// Records from an input device for a while (used by the loop-back test). Stereo, 32-bit float.
bool recordInput(uint32_t dev, double seconds, std::vector<float>& interleaved, double& rate, std::string& err);

// The render function fills planar buffers; called on the device's own real-time thread.
typedef void (*RenderFn)(void* user, float** out, int channels, int frames);

struct OutputStream {
    uint32_t dev = 0;
    void* procId = nullptr;
    RenderFn fn = nullptr; void* user = nullptr;
    std::atomic<uint64_t> callbacks{0}, framesTotal{0}, overloads{0};
    std::atomic<uint32_t> minFrames{0xffffffffu}, maxFrames{0};
    std::atomic<uint64_t> worstNs{0}, sumNs{0};   // time spent inside the render function
    std::vector<float> scratch[2];
    bool running = false;
    // the format the system hands this program for the device: float when the system mixes, the device's own
    // integer format when it does not
    bool vFloat = true, vAlignedHigh = true, vBigEndian = false; int vBits = 32, vBytes = 4;
    bool dither16 = false; uint32_t ditherState = 0x1234abcdu;   // task NB-R4 (review C7): off, so 16-bit material reaches a 16-bit DAC bit for bit
    std::string formatText;
    bool start(uint32_t device, RenderFn f, void* u, std::string& err);
    void stop();
};

}  // namespace al
