// A small JSON reader for the engine core (task NB-N3a): device settings, chains, test cases.
#pragma once
#include <cstdlib>
#include <map>
#include <memory>
#include <string>
#include <vector>

namespace al {

struct JValue {
    enum Type { Undefined, Null, Bool, Number, String, Array, Object } t = Undefined;
    bool b = false;
    double n = 0;
    std::string s;
    std::vector<JValue> a;
    std::vector<std::pair<std::string, JValue>> o;  // keeps the order

    const JValue* get(const std::string& k) const {
        for (auto& kv : o) if (kv.first == k) return &kv.second;
        return nullptr;
    }
    const JValue& operator[](const std::string& k) const {
        static const JValue undef;
        const JValue* v = get(k);
        return v ? *v : undef;
    }
    std::string str(const std::string& def = "") const { return t == String ? s : def; }
    double num(double def = 0) const { return t == Number ? n : def; }
};

struct JParser {
    const std::string& s;
    size_t i = 0;
    std::string err;
    explicit JParser(const std::string& src) : s(src) {}
    void ws() { while (i < s.size() && (s[i] == ' ' || s[i] == '\t' || s[i] == '\r' || s[i] == '\n')) i++; }
    bool fail(const char* m) { if (err.empty()) err = std::string(m) + " at " + std::to_string(i); return false; }
    static void utf8(std::string& o, unsigned cp) {
        if (cp < 0x80) o += (char)cp;
        else if (cp < 0x800) { o += (char)(0xC0 | (cp >> 6)); o += (char)(0x80 | (cp & 63)); }
        else if (cp < 0x10000) { o += (char)(0xE0 | (cp >> 12)); o += (char)(0x80 | ((cp >> 6) & 63)); o += (char)(0x80 | (cp & 63)); }
        else { o += (char)(0xF0 | (cp >> 18)); o += (char)(0x80 | ((cp >> 12) & 63)); o += (char)(0x80 | ((cp >> 6) & 63)); o += (char)(0x80 | (cp & 63)); }
    }
    bool str(std::string& o) {
        if (s[i] != '"') return fail("expected string");
        i++;
        while (i < s.size() && s[i] != '"') {
            char c = s[i++];
            if (c == '\\' && i < s.size()) {
                char e = s[i++];
                if (e == 'n') o += '\n'; else if (e == 't') o += '\t'; else if (e == 'r') o += '\r';
                else if (e == 'b') o += '\b'; else if (e == 'f') o += '\f';
                else if (e == 'u' && i + 4 <= s.size()) {
                    unsigned cp = (unsigned)strtoul(s.substr(i, 4).c_str(), nullptr, 16); i += 4;
                    if (cp >= 0xD800 && cp < 0xDC00 && i + 6 <= s.size() && s[i] == '\\' && s[i + 1] == 'u') {
                        unsigned lo = (unsigned)strtoul(s.substr(i + 2, 4).c_str(), nullptr, 16); i += 6;
                        cp = 0x10000 + ((cp - 0xD800) << 10) + (lo - 0xDC00);
                    }
                    utf8(o, cp);
                } else o += e;
            } else o += c;
        }
        if (i >= s.size()) return fail("unterminated string");
        i++;
        return true;
    }
    bool val(JValue& v) {
        ws();
        if (i >= s.size()) return fail("unexpected end");
        char c = s[i];
        if (c == '{') {
            v.t = JValue::Object; i++; ws();
            if (i < s.size() && s[i] == '}') { i++; return true; }
            while (true) {
                ws(); std::string k; if (!str(k)) return false;
                ws(); if (i >= s.size() || s[i] != ':') return fail("expected :"); i++;
                JValue x; if (!val(x)) return false;
                v.o.emplace_back(std::move(k), std::move(x));
                ws(); if (i < s.size() && s[i] == ',') { i++; continue; }
                if (i < s.size() && s[i] == '}') { i++; return true; }
                return fail("expected , or }");
            }
        }
        if (c == '[') {
            v.t = JValue::Array; i++; ws();
            if (i < s.size() && s[i] == ']') { i++; return true; }
            while (true) {
                JValue x; if (!val(x)) return false;
                v.a.push_back(std::move(x));
                ws(); if (i < s.size() && s[i] == ',') { i++; continue; }
                if (i < s.size() && s[i] == ']') { i++; return true; }
                return fail("expected , or ]");
            }
        }
        if (c == '"') { v.t = JValue::String; return str(v.s); }
        if (s.compare(i, 4, "true") == 0) { v.t = JValue::Bool; v.b = true; i += 4; return true; }
        if (s.compare(i, 5, "false") == 0) { v.t = JValue::Bool; v.b = false; i += 5; return true; }
        if (s.compare(i, 4, "null") == 0) { v.t = JValue::Null; i += 4; return true; }
        char* end = nullptr;
        double d = strtod(s.c_str() + i, &end);  // strtod rounds correctly, like JSON.parse
        if (end == s.c_str() + i) return fail("bad value");
        v.t = JValue::Number; v.n = d; i = (size_t)(end - s.c_str());
        return true;
    }
};

inline bool parseJson(const std::string& src, JValue& out, std::string& err) {
    JParser p(src);
    if (!p.val(out)) { err = p.err; return false; }
    return true;
}

}  // namespace al
