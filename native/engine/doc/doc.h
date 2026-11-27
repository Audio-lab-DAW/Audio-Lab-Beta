// The project document in the engine (task NB-R7, review RN5 A10): the state the engine will own.
//
// The document is the app's project object `S` exactly as JSON carries it. It changes only through numbered edits,
// each a short list of operations that carry their own inverse, so undo and redo are the same operations backwards.
// The design, the protocol and the proofs are in docs/native-state-protocol.md. The page's side is
// native/bridge/doc-sync.js; both sides compute the same structural hash, so "page and engine hold the same state" is
// checked by comparing 16 hex digits.
//
// Never touched by the audio thread: the audio graph is built from the document on another thread and swapped in.
#pragma once
#include <algorithm>
#include <cerrno>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <memory>
#include <string>
#include <utility>
#include <vector>
#include <fcntl.h>
#include <unistd.h>

namespace al {
namespace doc {

// ---------------------------------------------------------------- values
struct Val {
    enum Type : uint8_t { Null, Bool, Number, String, Array, Object } t = Null;
    bool b = false;
    double n = 0;
    std::string s;                                   // WTF-8: lone surrogates kept as 3-byte sequences, as in JS
    std::vector<Val> a;
    std::vector<std::pair<std::string, Val>> o;      // insertion order, keys unique

    static Val num(double d) { Val v; v.t = Number; v.n = d; return v; }
    static Val str(std::string x) { Val v; v.t = String; v.s = std::move(x); return v; }
    Val* find(const std::string& k) { for (auto& kv : o) if (kv.first == k) return &kv.second; return nullptr; }
    const Val* find(const std::string& k) const { for (auto& kv : o) if (kv.first == k) return &kv.second; return nullptr; }
    const Val* get(const std::string& k) const { return t == Object ? find(k) : nullptr; }
};

inline bool equal(const Val& x, const Val& y) {
    if (x.t != y.t) return false;
    switch (x.t) {
        case Val::Null: return true;
        case Val::Bool: return x.b == y.b;
        case Val::Number: return x.n == y.n;               // -0 == 0, as JSON cannot tell them apart either
        case Val::String: return x.s == y.s;
        case Val::Array:
            if (x.a.size() != y.a.size()) return false;
            for (size_t i = 0; i < x.a.size(); i++) if (!equal(x.a[i], y.a[i])) return false;
            return true;
        case Val::Object:
            if (x.o.size() != y.o.size()) return false;
            for (auto& kv : x.o) { const Val* w = y.find(kv.first); if (!w || !equal(kv.second, *w)) return false; }
            return true;
    }
    return false;
}

// ---------------------------------------------------------------- reading JSON
struct Reader {
    const char* p; const char* e; std::string err; int depth = 0;
    Reader(const char* b, size_t n) : p(b), e(b + n) {}
    bool fail(const char* m) { if (err.empty()) err = m; return false; }
    void ws() { while (p < e && (*p == ' ' || *p == '\t' || *p == '\r' || *p == '\n')) p++; }
    static void put(std::string& o, uint32_t cp) {   // generalized UTF-8 (WTF-8): a lone surrogate gets its 3 bytes
        if (cp < 0x80) o += (char)cp;
        else if (cp < 0x800) { o += (char)(0xC0 | (cp >> 6)); o += (char)(0x80 | (cp & 63)); }
        else if (cp < 0x10000) { o += (char)(0xE0 | (cp >> 12)); o += (char)(0x80 | ((cp >> 6) & 63)); o += (char)(0x80 | (cp & 63)); }
        else { o += (char)(0xF0 | (cp >> 18)); o += (char)(0x80 | ((cp >> 12) & 63)); o += (char)(0x80 | ((cp >> 6) & 63)); o += (char)(0x80 | (cp & 63)); }
    }
    bool hex4(uint32_t& v) {
        if (e - p < 4) return fail("short \\u escape");
        v = 0;
        for (int k = 0; k < 4; k++) {
            char h = p[k]; v <<= 4;
            if (h >= '0' && h <= '9') v |= (uint32_t)(h - '0'); else if (h >= 'a' && h <= 'f') v |= (uint32_t)(h - 'a' + 10);
            else if (h >= 'A' && h <= 'F') v |= (uint32_t)(h - 'A' + 10); else return fail("bad \\u escape");
        }
        p += 4; return true;
    }
    bool string(std::string& o) {
        if (p >= e || *p != '"') return fail("expected a string");
        p++;
        while (true) {
            if (p >= e) return fail("unterminated string");
            unsigned char c = (unsigned char)*p++;
            if (c == '"') return true;
            if (c < 0x20) return fail("control character in a string");
            if (c != '\\') { o += (char)c; continue; }
            if (p >= e) return fail("unterminated escape");
            char x = *p++;
            switch (x) {
                case '"': o += '"'; break; case '\\': o += '\\'; break; case '/': o += '/'; break;
                case 'b': o += '\b'; break; case 'f': o += '\f'; break; case 'n': o += '\n'; break;
                case 'r': o += '\r'; break; case 't': o += '\t'; break;
                case 'u': {
                    uint32_t cp; if (!hex4(cp)) return false;
                    if (cp >= 0xD800 && cp < 0xDC00 && e - p >= 6 && p[0] == '\\' && p[1] == 'u') {
                        const char* save = p; p += 2; uint32_t lo;
                        if (hex4(lo) && lo >= 0xDC00 && lo < 0xE000) cp = 0x10000 + ((cp - 0xD800) << 10) + (lo - 0xDC00);
                        else { p = save; err.clear(); }
                    }
                    put(o, cp); break;
                }
                default: return fail("bad escape");
            }
        }
    }
    bool value(Val& v) {
        ws();
        if (p >= e) return fail("unexpected end");
        if (++depth > 512) return fail("nested too deeply");
        bool ok = true;
        char c = *p;
        if (c == '{') {
            v.t = Val::Object; p++; ws();
            if (p < e && *p == '}') p++;
            else while (true) {
                ws(); std::string k; if (!string(k)) { ok = false; break; }
                ws(); if (p >= e || *p != ':') { ok = fail("expected :"); break; } p++;
                Val x; if (!value(x)) { ok = false; break; }
                if (Val* dup = v.find(k)) *dup = std::move(x);          // JSON.parse keeps the last one
                else v.o.emplace_back(std::move(k), std::move(x));
                ws(); if (p < e && *p == ',') { p++; continue; }
                if (p < e && *p == '}') { p++; break; }
                ok = fail("expected , or }"); break;
            }
        } else if (c == '[') {
            v.t = Val::Array; p++; ws();
            if (p < e && *p == ']') p++;
            else while (true) {
                v.a.emplace_back();
                if (!value(v.a.back())) { ok = false; break; }
                ws(); if (p < e && *p == ',') { p++; continue; }
                if (p < e && *p == ']') { p++; break; }
                ok = fail("expected , or ]"); break;
            }
        } else if (c == '"') { v.t = Val::String; ok = string(v.s); }
        else if (e - p >= 4 && !memcmp(p, "true", 4)) { v.t = Val::Bool; v.b = true; p += 4; }
        else if (e - p >= 5 && !memcmp(p, "false", 5)) { v.t = Val::Bool; v.b = false; p += 5; }
        else if (e - p >= 4 && !memcmp(p, "null", 4)) { v.t = Val::Null; p += 4; }
        else {
            // JSON's number grammar, then strtod (correctly rounded on glibc and Apple, as JSON.parse)
            const char* q = p;
            if (q < e && *q == '-') q++;
            if (q >= e || !(*q >= '0' && *q <= '9')) return fail("bad value");
            if (*q == '0') q++; else while (q < e && *q >= '0' && *q <= '9') q++;
            if (q < e && *q == '.') { q++; if (q >= e || !(*q >= '0' && *q <= '9')) return fail("bad number"); while (q < e && *q >= '0' && *q <= '9') q++; }
            if (q < e && (*q == 'e' || *q == 'E')) { q++; if (q < e && (*q == '+' || *q == '-')) q++; if (q >= e || !(*q >= '0' && *q <= '9')) return fail("bad number"); while (q < e && *q >= '0' && *q <= '9') q++; }
            std::string tok(p, q);
            v.t = Val::Number; v.n = strtod(tok.c_str(), nullptr);
            if (!std::isfinite(v.n)) return fail("number out of range");
            p = q;
        }
        depth--;
        return ok;
    }
};

inline bool parse(const std::string& src, Val& out, std::string& err) {
    Reader r(src.data(), src.size());
    out = Val();
    if (!r.value(out)) { err = r.err + " at byte " + std::to_string(r.p - src.data()); return false; }
    r.ws();
    if (r.p != r.e) { err = "text after the value"; return false; }
    return true;
}

// ---------------------------------------------------------------- writing JSON
inline void writeString(std::string& o, const std::string& s) {
    o += '"';
    const unsigned char* p = (const unsigned char*)s.data(); const unsigned char* e = p + s.size();
    while (p < e) {
        unsigned char c = *p;
        if (c == '"') { o += "\\\""; p++; }
        else if (c == '\\') { o += "\\\\"; p++; }
        else if (c < 0x20) {
            static const char* hx = "0123456789abcdef";
            if (c == '\n') o += "\\n"; else if (c == '\r') o += "\\r"; else if (c == '\t') o += "\\t";
            else if (c == '\b') o += "\\b"; else if (c == '\f') o += "\\f";
            else { o += "\\u00"; o += hx[c >> 4]; o += hx[c & 15]; }
            p++;
        } else if (c == 0xED && e - p >= 3 && p[1] >= 0xA0) {   // a lone surrogate (WTF-8): back to \uXXXX, as JSON.stringify
            uint32_t cp = ((uint32_t)(c & 15) << 12) | ((uint32_t)(p[1] & 63) << 6) | (uint32_t)(p[2] & 63);
            char b[8]; snprintf(b, sizeof b, "\\u%04x", cp); o += b; p += 3;
        } else { o += (char)c; p++; }
    }
    o += '"';
}

inline void writeNumber(std::string& o, double d) {
    if (!std::isfinite(d)) { o += "null"; return; }             // JSON.stringify does the same; never in a document
    if (d == 0) { o += '0'; return; }
    char b[40];
    if (d == std::floor(d) && std::fabs(d) < 1e15) { snprintf(b, sizeof b, "%.0f", d); o += b; return; }   // whole numbers as JSON.stringify writes them
    // the shortest text that reads back to the same double (as JSON.stringify), found by trying 1 to 17 digits
    for (int prec = 1; prec <= 17; prec++) {
        snprintf(b, sizeof b, "%.*g", prec, d);
        if (strtod(b, nullptr) == d) break;
    }
    o += b;
}

inline void write(std::string& o, const Val& v) {
    switch (v.t) {
        case Val::Null: o += "null"; break;
        case Val::Bool: o += v.b ? "true" : "false"; break;
        case Val::Number: writeNumber(o, v.n); break;
        case Val::String: writeString(o, v.s); break;
        case Val::Array:
            o += '[';
            for (size_t i = 0; i < v.a.size(); i++) { if (i) o += ','; write(o, v.a[i]); }
            o += ']'; break;
        case Val::Object:
            o += '{';
            for (size_t i = 0; i < v.o.size(); i++) { if (i) o += ','; writeString(o, v.o[i].first); o += ':'; write(o, v.o[i].second); }
            o += '}'; break;
    }
}
inline std::string toJson(const Val& v) { std::string o; write(o, v); return o; }

// ---------------------------------------------------------------- the structural hash
// Two FNV-1a 32-bit lanes over a byte stream that describes the value; object keys sorted by their bytes, so key
// order does not matter; numbers as the 8 bytes of the double (little end first), -0 as 0. The page computes the
// same in doc-sync.js (hashDoc). 64 bits: a check that two copies agree, not a cryptographic digest.
struct Hasher {
    uint32_t a = 0x811c9dc5u, b = 0x6b43a9b5u;
    void byte(uint8_t x) { a = (a ^ x) * 0x01000193u; b = (b ^ x) * 0x01000193u; b ^= b >> 15; }
    void bytes(const void* p, size_t n) { const uint8_t* q = (const uint8_t*)p; for (size_t i = 0; i < n; i++) byte(q[i]); }
    void u32(uint32_t v) { for (int i = 0; i < 4; i++) byte((uint8_t)(v >> (8 * i))); }
    void str(const std::string& s) { byte('s'); u32((uint32_t)s.size()); bytes(s.data(), s.size()); }
    void val(const Val& v) {
        switch (v.t) {
            case Val::Null: byte('n'); break;
            case Val::Bool: byte(v.b ? 't' : 'f'); break;
            case Val::Number: {
                double d = v.n == 0 ? 0.0 : v.n; uint64_t u; memcpy(&u, &d, 8);
                byte('d'); for (int i = 0; i < 8; i++) byte((uint8_t)(u >> (8 * i)));
                break;
            }
            case Val::String: str(v.s); break;
            case Val::Array: byte('a'); u32((uint32_t)v.a.size()); for (auto& x : v.a) val(x); break;
            case Val::Object: {
                byte('o'); u32((uint32_t)v.o.size());
                std::vector<const std::pair<std::string, Val>*> kv; kv.reserve(v.o.size());
                for (auto& x : v.o) kv.push_back(&x);
                std::sort(kv.begin(), kv.end(), [](auto* x, auto* y) { return x->first < y->first; });   // bytewise
                for (auto* x : kv) { str(x->first); val(x->second); }
                break;
            }
        }
    }
    std::string hex() const { char o[17]; snprintf(o, sizeof o, "%08x%08x", a, b); return o; }
};
inline std::string hashOf(const Val& v) { Hasher h; h.val(v); return h.hex(); }

// ---------------------------------------------------------------- operations
// One change at one place. p is the path: strings are object keys, numbers array indices.
//   set  p v [w]  put v at p; w is the value it replaces (no w: the key is new). On an array p ends in an index < length.
//   del  p w      remove the object key at p; w is its value.
//   ins  p v      insert v into the array at index p.back() (0 to length).
//   rm   p w      remove the array element at index p.back(); w is its value.
// The old values (w) make every operation its own inverse's input, and they are checked: an edit whose w does not
// match the engine's copy is refused whole, so a page and an engine that drifted apart find out at once.
struct Seg { bool isIndex = false; size_t i = 0; std::string k; };
struct Op {
    enum Kind : uint8_t { Set, Del, Ins, Rm } kind = Set;
    std::vector<Seg> p;
    bool hasV = false, hasW = false;
    Val v, w;
};

inline bool readOp(const Val& j, Op& op, std::string& err) {
    if (j.t != Val::Object) { err = "an operation must be an object"; return false; }
    const Val* o = j.find("o"); const Val* p = j.find("p");
    if (!o || o->t != Val::String) { err = "operation without o"; return false; }
    if (o->s == "set") op.kind = Op::Set; else if (o->s == "del") op.kind = Op::Del;
    else if (o->s == "ins") op.kind = Op::Ins; else if (o->s == "rm") op.kind = Op::Rm;
    else { err = "unknown operation " + o->s; return false; }
    if (!p || p->t != Val::Array) { err = "operation without a path"; return false; }
    for (auto& s : p->a) {
        Seg g;
        if (s.t == Val::String) g.k = s.s;
        else if (s.t == Val::Number && s.n >= 0 && s.n < 4294967296.0 && s.n == std::floor(s.n)) { g.isIndex = true; g.i = (size_t)s.n; }
        else { err = "bad path segment"; return false; }
        op.p.push_back(std::move(g));
    }
    if (const Val* v = j.find("v")) { op.hasV = true; op.v = *v; }
    if (const Val* w = j.find("w")) { op.hasW = true; op.w = *w; }
    if ((op.kind == Op::Set || op.kind == Op::Ins) && !op.hasV) { err = "set or ins without v"; return false; }
    if ((op.kind == Op::Del || op.kind == Op::Rm) && !op.hasW) { err = "del or rm without w"; return false; }
    if ((op.kind == Op::Ins || op.kind == Op::Rm) && (op.p.empty() || !op.p.back().isIndex)) { err = "ins or rm needs an index"; return false; }
    if (op.kind == Op::Del && (op.p.empty() || op.p.back().isIndex)) { err = "del needs a key"; return false; }
    return true;
}

inline Val opToJson(const Op& op) {
    Val j; j.t = Val::Object;
    static const char* names[] = {"set", "del", "ins", "rm"};
    j.o.emplace_back("o", Val::str(names[op.kind]));
    Val p; p.t = Val::Array;
    for (auto& s : op.p) p.a.push_back(s.isIndex ? Val::num((double)s.i) : Val::str(s.k));
    j.o.emplace_back("p", std::move(p));
    if (op.hasV) j.o.emplace_back("v", op.v);
    if (op.hasW) j.o.emplace_back("w", op.w);
    return j;
}

inline Op inverse(const Op& op) {
    Op r; r.p = op.p;
    switch (op.kind) {
        case Op::Set:
            if (op.hasW) { r.kind = Op::Set; r.hasV = true; r.v = op.w; r.hasW = true; r.w = op.v; }
            else { r.kind = Op::Del; r.hasW = true; r.w = op.v; }
            break;
        case Op::Del: r.kind = Op::Set; r.hasV = true; r.v = op.w; break;
        case Op::Ins: r.kind = Op::Rm; r.hasW = true; r.w = op.v; break;
        case Op::Rm: r.kind = Op::Ins; r.hasV = true; r.v = op.w; break;
    }
    return r;
}

// Applies one operation; on a refusal the document is unchanged and err says why.
inline bool apply(Val& root, const Op& op, std::string& err) {
    if (op.p.empty()) {                                     // the whole document
        if (op.kind != Op::Set) { err = "only set may address the root"; return false; }
        if (!op.hasW || !equal(root, op.w)) { err = "old value differs at the root"; return false; }
        root = op.v; return true;
    }
    Val* c = &root;
    for (size_t k = 0; k + 1 < op.p.size(); k++) {
        const Seg& s = op.p[k];
        if (s.isIndex) { if (c->t != Val::Array || s.i >= c->a.size()) { err = "path not found"; return false; } c = &c->a[s.i]; }
        else { if (c->t != Val::Object) { err = "path not found"; return false; } c = c->find(s.k); if (!c) { err = "path not found"; return false; } }
    }
    const Seg& last = op.p.back();
    switch (op.kind) {
        case Op::Set:
            if (last.isIndex) {
                if (c->t != Val::Array || last.i >= c->a.size()) { err = "index out of range"; return false; }
                if (!op.hasW || !equal(c->a[last.i], op.w)) { err = "old value differs"; return false; }
                c->a[last.i] = op.v;
            } else {
                if (c->t != Val::Object) { err = "not an object"; return false; }
                Val* x = c->find(last.k);
                if (op.hasW) { if (!x || !equal(*x, op.w)) { err = "old value differs"; return false; } *x = op.v; }
                else { if (x) { err = "key exists already"; return false; } c->o.emplace_back(last.k, op.v); }
            }
            return true;
        case Op::Del: {
            if (c->t != Val::Object) { err = "not an object"; return false; }
            for (size_t i = 0; i < c->o.size(); i++)
                if (c->o[i].first == last.k) {
                    if (!equal(c->o[i].second, op.w)) { err = "old value differs"; return false; }
                    c->o.erase(c->o.begin() + (ptrdiff_t)i); return true;
                }
            err = "key not found"; return false;
        }
        case Op::Ins:
            if (c->t != Val::Array || last.i > c->a.size()) { err = "index out of range"; return false; }
            c->a.insert(c->a.begin() + (ptrdiff_t)last.i, op.v); return true;
        case Op::Rm:
            if (c->t != Val::Array || last.i >= c->a.size()) { err = "index out of range"; return false; }
            if (!equal(c->a[last.i], op.w)) { err = "old value differs"; return false; }
            c->a.erase(c->a.begin() + (ptrdiff_t)last.i); return true;
    }
    return false;
}

// All or nothing: on a refusal every operation already applied is undone, so the document is as before.
inline bool applyAll(Val& root, const std::vector<Op>& ops, std::string& err, size_t* failedAt = nullptr) {
    for (size_t i = 0; i < ops.size(); i++) {
        if (!apply(root, ops[i], err)) {
            for (size_t k = i; k-- > 0;) { std::string e2; apply(root, inverse(ops[k]), e2); }
            if (failedAt) *failedAt = i;
            return false;
        }
    }
    return true;
}

inline std::vector<Op> inverseAll(const std::vector<Op>& ops) {
    std::vector<Op> r; r.reserve(ops.size());
    for (size_t k = ops.size(); k-- > 0;) r.push_back(inverse(ops[k]));
    return r;
}

// ---------------------------------------------------------------- the document with its history
// seq counts every change the document has taken (from the page, or the engine's own undo and redo). An edit
// names the seq it was made on (base); the engine takes it only if that is still the current one, otherwise the
// sender has missed something and must catch up first. Undo works in steps: the edits that share a step id (one
// pushUndo in the app, for example a whole knob drag) are undone together.
struct Edit { uint64_t seq = 0; std::string step, label, origin; std::vector<Op> ops; size_t bytes = 0; };

inline size_t approxBytes(const Val& v) {
    size_t n = sizeof(Val) + v.s.size();
    for (auto& x : v.a) n += approxBytes(x);
    for (auto& kv : v.o) n += kv.first.size() + approxBytes(kv.second);
    return n;
}
inline size_t approxBytes(const std::vector<Op>& ops) {
    size_t n = 0;
    for (auto& op : ops) { n += sizeof(Op) + op.p.size() * sizeof(Seg); if (op.hasV) n += approxBytes(op.v); if (op.hasW) n += approxBytes(op.w); }
    return n;
}

struct Document {
    Val root;
    uint64_t seq = 0;
    std::vector<Edit> undo, redo;                 // whole edits, newest last
    size_t historyBytes = 0, historyLimit = 64u << 20;
    uint64_t savedSeq = 0;                        // the seq last written to disk (autosave)

    void load(Val v) { root = std::move(v); seq++; undo.clear(); redo.clear(); historyBytes = 0; }

    // an edit from the page: checked against base, applied whole or not at all
    bool edit(uint64_t base, const std::string& step, const std::string& label, std::vector<Op> ops, std::string& err) {
        if (base != seq) { err = "stale"; return false; }
        if (!applyAll(root, ops, err)) return false;
        seq++;
        Edit e; e.seq = seq; e.step = step; e.label = label; e.origin = "page"; e.bytes = approxBytes(ops); e.ops = std::move(ops);
        historyBytes += e.bytes;
        undo.push_back(std::move(e));
        redo.clear();
        trim();
        return true;
    }
    uint64_t droppedSteps = 0;                    // whole steps dropped from the oldest end by the size limit
    void trim() {
        // whole steps only: half a step undone would leave a state the app never had
        while (historyBytes > historyLimit && undo.size() > 1) {
            std::string step = undo.front().step;
            size_t n = 0;
            while (n < undo.size() - 1 && (n == 0 || (!step.empty() && undo[n].step == step))) n++;
            for (size_t k = 0; k < n; k++) historyBytes -= undo[k].bytes;
            undo.erase(undo.begin(), undo.begin() + (ptrdiff_t)n);
            droppedSteps++;
        }
    }
    // undo the newest step: returns the operations applied (to send to the page), empty if nothing to undo
    std::vector<Op> undoStep(std::string& label) {
        std::vector<Op> applied;
        if (undo.empty()) return applied;
        std::string step = undo.back().step;
        label = undo.back().label;
        while (!undo.empty() && undo.back().step == step) {
            Edit e = std::move(undo.back()); undo.pop_back(); historyBytes -= e.bytes;
            std::vector<Op> inv = inverseAll(e.ops);
            std::string err;
            if (!applyAll(root, inv, err)) { undo.push_back(std::move(e)); historyBytes += undo.back().bytes; break; }   // cannot happen: the history holds exact inverses
            applied.insert(applied.end(), inv.begin(), inv.end());
            redo.push_back(std::move(e));
            if (step.empty()) break;              // edits without a step id are steps of their own
        }
        if (!applied.empty()) seq++;
        return applied;
    }
    std::vector<Op> redoStep(std::string& label) {
        std::vector<Op> applied;
        if (redo.empty()) return applied;
        std::string step = redo.back().step;
        label = redo.back().label;
        while (!redo.empty() && redo.back().step == step) {
            Edit e = std::move(redo.back()); redo.pop_back();
            std::string err;
            if (!applyAll(root, e.ops, err)) { redo.push_back(std::move(e)); break; }
            applied.insert(applied.end(), e.ops.begin(), e.ops.end());
            historyBytes += e.bytes;
            undo.push_back(std::move(e));
            if (step.empty()) break;
        }
        if (!applied.empty()) seq++;
        return applied;
    }
};

// ---------------------------------------------------------------- saving without ever losing the last good copy
// Writes path.tmp, flushes it to the disk, then renames it over path (atomic on one volume), after moving the
// previous copies along: path.1 is the one before, up to path.<keep>. A crash at any moment leaves either the old
// file or the new one whole, never half of each. The directory is flushed too, so the rename itself survives.
inline bool writeAll(int fd, const std::string& s) {
    size_t off = 0;
    while (off < s.size()) {
        ssize_t w = ::write(fd, s.data() + off, s.size() - off);
        if (w < 0) { if (errno == EINTR) continue; return false; }
        off += (size_t)w;
    }
    return true;
}
inline bool saveAtomic(const std::string& path, const std::string& text, int keep, std::string& err, bool stopBeforeRename = false) {
    std::string tmp = path + ".tmp";
    int fd = ::open(tmp.c_str(), O_WRONLY | O_CREAT | O_TRUNC, 0644);
    if (fd < 0) { err = std::string("cannot write ") + tmp + ": " + strerror(errno); return false; }
    bool ok = writeAll(fd, text);
#ifdef __APPLE__
    if (ok) ok = fcntl(fd, F_FULLFSYNC) == 0 || fsync(fd) == 0;   // fsync alone does not reach the disk on macOS
#else
    if (ok) ok = fsync(fd) == 0;
#endif
    ::close(fd);
    if (!ok) { err = std::string("write failed: ") + strerror(errno); ::unlink(tmp.c_str()); return false; }
    if (stopBeforeRename) return true;            // for the test: a crash between the write and the rename
    for (int k = keep; k >= 2; k--) {             // path.(k-1) -> path.k
        std::string from = path + "." + std::to_string(k - 1), to = path + "." + std::to_string(k);
        if (::access(from.c_str(), F_OK) == 0) ::rename(from.c_str(), to.c_str());
    }
    if (keep >= 1 && ::access(path.c_str(), F_OK) == 0) {   // path -> path.1 as a second name: path itself stays until the rename
        std::string one = path + ".1";
        ::unlink(one.c_str());
        if (::link(path.c_str(), one.c_str()) != 0) {   // a volume without hard links: copy instead
            FILE* in = fopen(path.c_str(), "rb"); FILE* out = fopen(one.c_str(), "wb");
            if (in && out) { char buf[65536]; size_t n; while ((n = fread(buf, 1, sizeof buf, in)) > 0) fwrite(buf, 1, n, out); }
            if (in) fclose(in);
            if (out) fclose(out);
        }
    }
    if (::rename(tmp.c_str(), path.c_str()) != 0) { err = std::string("rename failed: ") + strerror(errno); return false; }
    std::string dir = path.find('/') == std::string::npos ? "." : path.substr(0, path.rfind('/'));
    if (dir.empty()) dir = "/";
    int dfd = ::open(dir.c_str(), O_RDONLY);
    if (dfd >= 0) { fsync(dfd); ::close(dfd); }
    return true;
}

}  // namespace doc
}  // namespace al
