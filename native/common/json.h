// Tiny helpers for writing JSON by hand (task NM1 tests).
#pragma once
#include <cstdio>
#include <string>
namespace al {
inline std::string jstr(const std::string& s) {
    std::string o = "\"";
    for (unsigned char c : s) {
        if (c == '"' || c == '\\') { o += '\\'; o += (char)c; }
        else if (c == '\n') o += "\\n";
        else if (c == '\r') o += "\\r";
        else if (c == '\t') o += "\\t";
        else if (c < 0x20) { char b[8]; snprintf(b, sizeof b, "\\u%04x", c); o += b; }
        else o += (char)c;
    }
    return o + "\"";
}
inline std::string jnum(double v) { char b[64]; snprintf(b, sizeof b, "%.10g", v); return b; }
}  // namespace al
