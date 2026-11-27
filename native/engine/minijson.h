// Reads one flat JSON object per line: {"cmd":"open","rate":48000,"exclusive":true}. Task NB-N1.
#pragma once
#include <cstdint>
#include <cstdlib>
#include <map>
#include <string>

namespace al {
struct Msg {
    std::map<std::string, std::string> v;   // strings without quotes; numbers and true/false as text
    bool has(const char* k) const { return v.count(k) > 0; }
    std::string str(const char* k, const char* d = "") const { auto it = v.find(k); return it == v.end() ? d : it->second; }
    double num(const char* k, double d = 0) const { auto it = v.find(k); return it == v.end() ? d : atof(it->second.c_str()); }
    bool flag(const char* k, bool d = false) const { auto it = v.find(k); return it == v.end() ? d : (it->second == "true" || it->second == "1"); }
};
inline bool parseMsg(const std::string& s, Msg& m) {
    size_t i = 0, n = s.size();
    auto ws = [&]() { while (i < n && (s[i] == ' ' || s[i] == '\t' || s[i] == '\r' || s[i] == '\n')) i++; };
    auto readStr = [&](std::string& out) {
        if (i >= n || s[i] != '"') return false;
        i++; out.clear();
        while (i < n && s[i] != '"') {
            if (s[i] == '\\' && i + 1 < n) {
                i++; char c = s[i];
                if (c == 'u') {   // task NB-R4 (review C10): \uXXXX to UTF-8, surrogate pairs joined
                    auto hex4 = [&](size_t at, uint32_t& v) { if (at + 4 > n) return false; v = 0; for (size_t k = at; k < at + 4; k++) { char h = s[k]; v <<= 4; if (h >= '0' && h <= '9') v |= (uint32_t)(h - '0'); else if (h >= 'a' && h <= 'f') v |= (uint32_t)(h - 'a' + 10); else if (h >= 'A' && h <= 'F') v |= (uint32_t)(h - 'A' + 10); else return false; } return true; };
                    uint32_t cp; if (!hex4(i + 1, cp)) return false; i += 4;
                    if (cp >= 0xD800 && cp < 0xDC00) { uint32_t lo; if (i + 2 < n && s[i + 1] == '\\' && s[i + 2] == 'u' && hex4(i + 3, lo) && lo >= 0xDC00 && lo < 0xE000) { cp = 0x10000 + ((cp - 0xD800) << 10) + (lo - 0xDC00); i += 6; } else cp = 0xFFFD; }
                    else if (cp >= 0xDC00 && cp < 0xE000) cp = 0xFFFD;
                    if (cp < 0x80) out += (char)cp;
                    else if (cp < 0x800) { out += (char)(0xC0 | (cp >> 6)); out += (char)(0x80 | (cp & 0x3F)); }
                    else if (cp < 0x10000) { out += (char)(0xE0 | (cp >> 12)); out += (char)(0x80 | ((cp >> 6) & 0x3F)); out += (char)(0x80 | (cp & 0x3F)); }
                    else { out += (char)(0xF0 | (cp >> 18)); out += (char)(0x80 | ((cp >> 12) & 0x3F)); out += (char)(0x80 | ((cp >> 6) & 0x3F)); out += (char)(0x80 | (cp & 0x3F)); }
                }
                else out += c == 'n' ? '\n' : c == 't' ? '\t' : c == 'r' ? '\r' : c == 'b' ? '\b' : c == 'f' ? '\f' : c;
            }
            else out += s[i];
            i++;
        }
        if (i >= n) return false;
        i++; return true;
    };
    ws(); if (i >= n || s[i] != '{') return false; i++;
    while (true) {
        ws(); if (i < n && s[i] == '}') return true;
        std::string k, val;
        if (!readStr(k)) return false;
        ws(); if (i >= n || s[i] != ':') return false; i++; ws();
        if (i < n && s[i] == '"') { if (!readStr(val)) return false; }
        else { size_t st = i; while (i < n && s[i] != ',' && s[i] != '}') i++; val = s.substr(st, i - st); while (!val.empty() && (val.back() == ' ' || val.back() == '\r')) val.pop_back(); }
        m.v[k] = val;
        ws(); if (i < n && s[i] == ',') { i++; continue; }
        if (i < n && s[i] == '}') return true;
        return false;
    }
}
}  // namespace al
