// The null device's extra (task NB-R2), see nulldevice.cpp. Only in builds without Core Audio.
#pragma once
#include <cstdint>
#include <string>

namespace al {
// Changes a pretend device as another program or the user would: what = "rate", "volume", "unplug", "plug",
// "hog" (value: the process that takes exclusive use). Returns "" or what went wrong.
std::string nullExternal(const std::string& what, double value, uint32_t dev);
}
