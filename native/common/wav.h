// Minimal 32-bit float WAV reading and writing (task NM1 tests).
#pragma once
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <string>
#include <vector>

namespace al {
struct Wav {
    int sr = 48000, ch = 2;
    std::vector<float> data;  // interleaved
    size_t frames() const { return ch ? data.size() / ch : 0; }
};

inline bool wavRead(const std::string& path, Wav& w, std::string& err) {
    FILE* f = fopen(path.c_str(), "rb");
    if (!f) { err = "cannot open " + path; return false; }
    std::vector<uint8_t> b;
    uint8_t tmp[65536]; size_t n;
    while ((n = fread(tmp, 1, sizeof tmp, f)) > 0) b.insert(b.end(), tmp, tmp + n);
    fclose(f);
    if (b.size() < 44 || memcmp(b.data(), "RIFF", 4) || memcmp(b.data() + 8, "WAVE", 4)) { err = "not a WAV file"; return false; }
    size_t p = 12; uint16_t fmt = 0, bits = 0;
    while (p + 8 <= b.size()) {
        uint32_t len; memcpy(&len, &b[p + 4], 4);
        if (!memcmp(&b[p], "fmt ", 4)) {
            uint16_t ch; uint32_t sr; memcpy(&fmt, &b[p + 8], 2); memcpy(&ch, &b[p + 10], 2); memcpy(&sr, &b[p + 12], 4); memcpy(&bits, &b[p + 22], 2);
            w.ch = ch; w.sr = (int)sr;
        } else if (!memcmp(&b[p], "data", 4)) {
            if (fmt != 3 || bits != 32) { err = "only 32-bit float WAV is supported"; return false; }
            if (p + 8 + len > b.size()) len = (uint32_t)(b.size() - p - 8);
            w.data.resize(len / 4); memcpy(w.data.data(), &b[p + 8], (len / 4) * 4);
            return true;
        }
        p += 8 + len + (len & 1);
    }
    err = "no data in WAV file"; return false;
}

inline bool wavWrite(const std::string& path, const Wav& w) {
    FILE* f = fopen(path.c_str(), "wb");
    if (!f) return false;
    uint32_t dl = (uint32_t)(w.data.size() * 4), u32; uint16_t u16;
    fwrite("RIFF", 1, 4, f); u32 = 36 + dl; fwrite(&u32, 4, 1, f); fwrite("WAVEfmt ", 1, 8, f);
    u32 = 16; fwrite(&u32, 4, 1, f); u16 = 3; fwrite(&u16, 2, 1, f); u16 = (uint16_t)w.ch; fwrite(&u16, 2, 1, f);
    u32 = (uint32_t)w.sr; fwrite(&u32, 4, 1, f); u32 = (uint32_t)(w.sr * w.ch * 4); fwrite(&u32, 4, 1, f);
    u16 = (uint16_t)(w.ch * 4); fwrite(&u16, 2, 1, f); u16 = 32; fwrite(&u16, 2, 1, f);
    fwrite("data", 1, 4, f); fwrite(&dl, 4, 1, f); fwrite(w.data.data(), 4, w.data.size(), f);
    fclose(f); return true;
}
}  // namespace al
