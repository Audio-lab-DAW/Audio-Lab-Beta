// Device settings with JavaScript semantics (task NB-N3a).
// A ported device reads its settings the way the worklet does: `p.x||def` (falsy: missing, null, 0, NaN,
// false, ""), `p.x??def` (missing or null), plain `p.x` (missing is NaN in arithmetic), `p.x!==false`,
// `p.x==='name'`. The settings are the object the page posts to the worklet (the device's `sp` mapping in
// index.html), so the native side receives exactly what the web side receives.
#pragma once
#include <cmath>
#include <string>
#include "json_value.h"

namespace al {

struct Params {
    JValue v;  // an object

    static double toNumber(const JValue& x) {
        switch (x.t) {
            case JValue::Undefined: return NAN;
            case JValue::Null: return 0;
            case JValue::Bool: return x.b ? 1 : 0;
            case JValue::Number: return x.n;
            case JValue::String: {
                if (x.s.empty()) return 0;
                char* e = nullptr; double d = strtod(x.s.c_str(), &e);
                return (e && *e == 0) ? d : NAN;
            }
            default: return NAN;
        }
    }
    static bool truthy(const JValue& x) {
        switch (x.t) {
            case JValue::Bool: return x.b;
            case JValue::Number: return !(x.n == 0 || std::isnan(x.n));
            case JValue::String: return !x.s.empty();
            case JValue::Array: case JValue::Object: return true;
            default: return false;
        }
    }
    const JValue& at(const char* k) const { return v[k]; }
    double num(const char* k) const { return toNumber(at(k)); }                       // p.k
    double orNum(const char* k, double d) const { const JValue& x = at(k); return truthy(x) ? toNumber(x) : d; }  // p.k||d
    double nnNum(const char* k, double d) const {                                    // p.k??d
        const JValue& x = at(k); return (x.t == JValue::Undefined || x.t == JValue::Null) ? d : toNumber(x);
    }
    bool truthy(const char* k) const { return truthy(at(k)); }                         // !!p.k
    bool notFalse(const char* k) const { const JValue& x = at(k); return !(x.t == JValue::Bool && !x.b); }  // p.k!==false
    bool is(const char* k, const char* s) const { const JValue& x = at(k); return x.t == JValue::String && x.s == s; }  // p.k==='s'
    std::string orStr(const char* k, const char* d) const { const JValue& x = at(k); return truthy(x) ? (x.t == JValue::String ? x.s : std::string("?")) : d; }
    // Object.assign(this.p, d.p): later settings override, missing ones stay.
    void assign(const JValue& o) {
        if (v.t != JValue::Object) v.t = JValue::Object;
        for (auto& kv : o.o) {
            bool found = false;
            for (auto& mine : v.o) if (mine.first == kv.first) { mine.second = kv.second; found = true; break; }
            if (!found) v.o.push_back(kv);
        }
    }
};

}  // namespace al
