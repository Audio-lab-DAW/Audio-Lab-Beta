// Reads one flat JSON object per line: {"cmd":"open","rate":48000,"exclusive":true}. Task NB-N1.
#pragma once
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
            if (s[i] == '\\' && i + 1 < n) { i++; char c = s[i]; out += c == 'n' ? '\n' : c == 't' ? '\t' : c; }
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
