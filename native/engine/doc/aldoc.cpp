// aldoc: the engine's project document on its own, for the protocol tests (task NB-R7).
// Reads one JSON command per line on stdin and answers one JSON line each on stdout, with the same commands
// alengine will take when the bridge carries edits (docs/native-state-protocol.md):
//   {"cmd":"doc.load","rq":1,"doc":{...}}                       -> {"rq":1,"seq":1,"hash":"..."}
//   {"cmd":"doc.edit","rq":2,"base":1,"step":"7","label":"Moved Kick 17","ops":[...],"hash":true}
//                                                                -> {"rq":2,"seq":2,"hash":"...","us":12}
//                                                                or {"rq":2,"error":"stale","seq":5}
//   {"cmd":"doc.undo","rq":3} / {"cmd":"doc.redo","rq":3}       -> {"rq":3,"ev":"doc.change","seq":3,"label":"...","ops":[...]}
//   {"cmd":"doc.hash","rq":4}                                   -> {"rq":4,"seq":3,"hash":"..."}
//   {"cmd":"doc.snapshot","rq":5}                               -> {"rq":5,"seq":3,"hash":"...","doc":{...}}
//   {"cmd":"doc.save","rq":6,"path":"x.aldoc","keep":5}         -> {"rq":6,"ok":true,"bytes":1234,"us":800}
//   {"cmd":"doc.open","rq":7,"path":"x.aldoc"}                  -> {"rq":7,"seq":1,"hash":"...","from":"x.aldoc"}
//   {"cmd":"doc.stats","rq":8}                                  -> {"rq":8,"undo":12,"redo":0,"historyBytes":4567}
//   aldoc selftest                                              -> runs the built-in checks
#include "doc.h"
#include <chrono>
#include <iostream>

using namespace al::doc;
using Clock = std::chrono::steady_clock;
static long long usSince(Clock::time_point t) { return (long long)std::chrono::duration_cast<std::chrono::microseconds>(Clock::now() - t).count(); }

static std::string opsJson(const std::vector<Op>& ops) {
    std::string o = "[";
    for (size_t i = 0; i < ops.size(); i++) { if (i) o += ','; write(o, opToJson(ops[i])); }
    return o + "]";
}
static std::string rqOf(const Val& m) {
    const Val* r = m.get("rq");
    if (!r) return "null";
    return toJson(*r);
}

static bool readSaved(const std::string& path, Val& project, uint64_t& seq, std::string& err) {
    FILE* f = fopen(path.c_str(), "rb");
    if (!f) { err = "missing"; return false; }
    std::string text; char buf[65536]; size_t n;
    while ((n = fread(buf, 1, sizeof buf, f)) > 0) text.append(buf, n);
    fclose(f);
    Val j;
    if (!parse(text, j, err)) return false;
    const Val* fmt = j.get("format"); const Val* mr = j.get("minReader"); const Val* h = j.get("hash"); const Val* p = j.get("project"); const Val* s = j.get("seq");
    if (!fmt || fmt->t != Val::String || fmt->s != "audiolab-doc") { err = "not a document file"; return false; }
    if (!mr || mr->t != Val::Number || mr->n > 1) { err = "needs a newer AudioLab"; return false; }   // minReader: refuse, never half-read
    if (!p || !h || h->t != Val::String) { err = "incomplete"; return false; }
    if (hashOf(*p) != h->s) { err = "hash does not match: damaged"; return false; }
    project = *p; seq = s && s->t == Val::Number ? (uint64_t)s->n : 0;
    return true;
}

static int selftest() {
    int fails = 0;
    auto check = [&](bool ok, const char* what) { printf("%s %s\n", ok ? "ok  " : "FAIL", what); if (!ok) fails++; };
    Val d; std::string err;
    check(parse(R"({"a":1,"b":[1,2,{"id":"x","v":-0}],"s":"é🎵\udc00","n":null,"t":true,"e":5e-324,"big":1.7976931348623157e308})", d, err), "parse");
    std::string out = toJson(d);
    Val d2; check(parse(out, d2, err) && equal(d, d2) && hashOf(d) == hashOf(d2), "write and read back the same value, the same hash");
    check(out.find("\\udc00") != std::string::npos, "a lone surrogate written back as \\udc00");
    check(out.find("5e-324") != std::string::npos && out.find("1.7976931348623157e+308") != std::string::npos, "the shortest round-trip number text");
    // key order does not change the hash
    Val x, y; parse(R"({"a":1,"b":2})", x, err); parse(R"({"b":2,"a":1})", y, err);
    check(hashOf(x) == hashOf(y), "key order does not change the hash");
    Val z; parse(R"({"a":1,"b":2.0000000000000004})", z, err);
    check(hashOf(x) != hashOf(z), "one ulp changes the hash");
    // ops and their inverses
    Document doc; doc.load(d);
    std::string h0 = hashOf(doc.root);
    std::vector<Op> ops; Val oj;
    parse(R"([{"o":"set","p":["a"],"v":2,"w":1},{"o":"ins","p":["b",0],"v":"new"},{"o":"rm","p":["b",1],"w":1},{"o":"set","p":["q"],"v":{"k":[1]}},{"o":"del","p":["n"],"w":null}])", oj, err);
    for (auto& j : oj.a) { Op op; check(readOp(j, op, err), "read an operation"); ops.push_back(op); }
    check(doc.edit(doc.seq, "1", "test", ops, err), "an edit applies");
    check(hashOf(doc.root) != h0, "the edit changed the document");
    std::string label;
    auto u = doc.undoStep(label);
    check(!u.empty() && hashOf(doc.root) == h0 && label == "test", "undo gives the same hash as before");
    auto r = doc.redoStep(label);
    check(!r.empty() && hashOf(doc.root) != h0, "redo applies it again");
    // refusals leave the document unchanged
    std::string hb = hashOf(doc.root);
    std::vector<Op> bad; Val bj;
    parse(R"([{"o":"set","p":["a"],"v":3,"w":2},{"o":"set","p":["t"],"v":false,"w":false}])", bj, err);
    for (auto& j : bj.a) { Op op; readOp(j, op, err); bad.push_back(op); }
    check(!doc.edit(doc.seq, "2", "bad", bad, err) && hashOf(doc.root) == hb, "a wrong old value refuses the whole edit, nothing changed");
    check(!doc.edit(doc.seq - 1, "2", "stale", {}, err) && err == "stale", "an edit on an old seq is refused as stale");
    // saving: atomic, rotating, a crash before the rename keeps the old file
    char tmpl[] = "/tmp/aldocXXXXXX"; char* dir = mkdtemp(tmpl);
    std::string path = std::string(dir) + "/song.aldoc";
    std::string text1 = "{\"format\":\"audiolab-doc\",\"formatVersion\":1,\"minReader\":1,\"seq\":1,\"hash\":\"" + hashOf(doc.root) + "\",\"project\":" + toJson(doc.root) + "}";
    check(saveAtomic(path, text1, 3, err), "save");
    Val back; uint64_t seq; check(readSaved(path, back, seq, err) && equal(back, doc.root), "read back equal");
    for (int k = 0; k < 4; k++) saveAtomic(path, text1, 3, err);
    check(access((path + ".3").c_str(), F_OK) == 0 && access((path + ".4").c_str(), F_OK) != 0, "three older copies kept, not more");
    check(saveAtomic(path, "{\"half", 3, err, true) && readSaved(path, back, seq, err), "a crash after writing and before the rename: the saved file is still whole");
    for (const char* sfx : {"", ".1", ".2", ".3", ".tmp"}) unlink((path + sfx).c_str());
    rmdir(dir);
    printf("%s: %d failed\n", fails ? "FAIL" : "PASS", fails);
    return fails ? 1 : 0;
}

int main(int argc, char** argv) {
    if (argc > 1 && std::string(argv[1]) == "selftest") return selftest();
    std::ios::sync_with_stdio(false);
    Document doc;
    std::string line;
    while (std::getline(std::cin, line)) {
        if (line.empty()) continue;
        Val m; std::string err;
        if (!parse(line, m, err)) { std::cout << "{\"rq\":null,\"error\":\"parse\",\"why\":"; std::string o; writeString(o, err); std::cout << o << "}\n" << std::flush; continue; }
        const Val* c = m.get("cmd");
        std::string cmd = c && c->t == Val::String ? c->s : "", rq = rqOf(m), o = "{\"rq\":" + rq;
        auto t0 = Clock::now();
        if (cmd == "doc.load") {
            const Val* d = m.get("doc");
            if (!d) o += ",\"error\":\"no doc\"";
            else { doc.load(*d); o += ",\"seq\":" + std::to_string(doc.seq) + ",\"hash\":\"" + hashOf(doc.root) + "\""; }
        } else if (cmd == "doc.edit") {
            const Val* b = m.get("base"); const Val* opsj = m.get("ops"); const Val* st = m.get("step"); const Val* lb = m.get("label");
            std::vector<Op> ops; bool ok = b && b->t == Val::Number && opsj && opsj->t == Val::Array;
            if (!ok) err = "edit needs base and ops";
            for (size_t i = 0; ok && i < opsj->a.size(); i++) { Op op; if (!readOp(opsj->a[i], op, err)) ok = false; else ops.push_back(std::move(op)); }
            if (ok) ok = doc.edit((uint64_t)b->n, st && st->t == Val::String ? st->s : "", lb && lb->t == Val::String ? lb->s : "", std::move(ops), err);
            long long us = usSince(t0);
            if (!ok) { o += ",\"error\":"; writeString(o, err); o += ",\"seq\":" + std::to_string(doc.seq); }
            else {
                o += ",\"seq\":" + std::to_string(doc.seq) + ",\"us\":" + std::to_string(us);
                const Val* wh = m.get("hash");
                if (wh && wh->t == Val::Bool && wh->b) o += ",\"hash\":\"" + hashOf(doc.root) + "\"";
            }
        } else if (cmd == "doc.undo" || cmd == "doc.redo") {
            std::string label;
            auto ops = cmd == "doc.undo" ? doc.undoStep(label) : doc.redoStep(label);
            o += ",\"ev\":\"doc.change\",\"seq\":" + std::to_string(doc.seq) + ",\"label\":"; writeString(o, label);
            o += ",\"ops\":" + opsJson(ops) + ",\"hash\":\"" + hashOf(doc.root) + "\"";
        } else if (cmd == "doc.hash") {
            std::string h = hashOf(doc.root); long long us = usSince(t0);
            o += ",\"seq\":" + std::to_string(doc.seq) + ",\"hash\":\"" + h + "\",\"us\":" + std::to_string(us);
        } else if (cmd == "doc.snapshot") {
            o += ",\"seq\":" + std::to_string(doc.seq) + ",\"hash\":\"" + hashOf(doc.root) + "\",\"doc\":" + toJson(doc.root);
        } else if (cmd == "doc.save") {
            const Val* p = m.get("path"); const Val* k = m.get("keep"); const Val* cr = m.get("crashBeforeRename");
            if (!p || p->t != Val::String) o += ",\"error\":\"no path\"";
            else {
                std::string text = "{\"format\":\"audiolab-doc\",\"formatVersion\":1,\"minReader\":1,\"seq\":" + std::to_string(doc.seq) +
                                   ",\"hash\":\"" + hashOf(doc.root) + "\",\"project\":" + toJson(doc.root) + "}";
                if (saveAtomic(p->s, text, k && k->t == Val::Number ? (int)k->n : 5, err, cr && cr->t == Val::Bool && cr->b)) {
                    doc.savedSeq = doc.seq; long long us = usSince(t0);
                    o += ",\"ok\":true,\"bytes\":" + std::to_string(text.size()) + ",\"us\":" + std::to_string(us);
                } else { o += ",\"error\":"; writeString(o, err); }
            }
        } else if (cmd == "doc.open") {
            const Val* p = m.get("path");
            std::string from, why;
            Val project; uint64_t seq = 0; bool ok = false;
            if (p && p->t == Val::String)
                for (int k = 0; k <= 5 && !ok; k++) {         // the file, then the older copies, newest first
                    std::string f = k ? p->s + "." + std::to_string(k) : p->s;
                    std::string e2;
                    if (readSaved(f, project, seq, e2)) { ok = true; from = f; } else if (k == 0) why = e2;
                }
            if (!ok) { o += ",\"error\":"; writeString(o, why.empty() ? "no path" : why); }
            else {
                doc.load(std::move(project));
                o += ",\"seq\":" + std::to_string(doc.seq) + ",\"hash\":\"" + hashOf(doc.root) + "\",\"from\":"; writeString(o, from);
                if (!why.empty()) { o += ",\"why\":"; writeString(o, why); }
            }
        } else if (cmd == "doc.stats") {
            o += ",\"seq\":" + std::to_string(doc.seq) + ",\"undo\":" + std::to_string(doc.undo.size()) + ",\"redo\":" + std::to_string(doc.redo.size()) +
                 ",\"historyBytes\":" + std::to_string(doc.historyBytes);
        } else {
            o += ",\"error\":\"unknown command\"";
        }
        o += "}\n";
        std::cout << o << std::flush;
    }
    return 0;
}
