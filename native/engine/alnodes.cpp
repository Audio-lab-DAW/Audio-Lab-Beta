// alnodes (task NB-N3g): Chromium's source nodes and wave shaper on their own, for comparison with the browser.
//   alnodes cases.json outdir      cases: [{name, sr, quantum, frames, osc:{type, freq, detune, start, stop},
//                                           const:{offset, start, stop}, shape:{curve:[...]}}]
// One case renders an oscillator (or a constant source), optionally through a wave shaper, mono, 32-bit float.
// Task NB-N3j adds: param (a constant source of 1 into a GainNode whose gain is automated: the output is the
// timeline's values), src (an AudioBufferSourceNode), bgain (a buffer source into an automated GainNode), bq (a
// buffer source into a BiquadFilterNode with automated parameters). Events: ["v", x] (.value = x), ["set", x, t],
// ["lin", x, t], ["exp", x, t], ["tgt", x, t, tc], ["curve", [..], t, dur]. Buffers: {sr, len, gen} with
// x[i] = float(((i * 7919 + gen * 104729) % 2001 - 1000) / 1000), the same numbers the page makes.
#include <chrono>
#include <cstdio>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>
#include "core/json_value.h"
#include "core/device.h"
#include "core/webnodes.h"
#include "core/bufsrc.h"
#include "core/nodes_auto.h"

using namespace al;

static bool readFile(const std::string& p, std::string& out) { std::ifstream f(p, std::ios::binary); if (!f) return false; std::stringstream s; s << f.rdbuf(); out = s.str(); return true; }
static void wavWrite(const std::string& path, int sr, const std::vector<float>& x) {
    FILE* f = fopen(path.c_str(), "wb"); if (!f) return;
    const uint32_t n = (uint32_t)x.size() * 4; uint32_t u; uint16_t h;
    fwrite("RIFF", 1, 4, f); u = 36 + n; fwrite(&u, 4, 1, f); fwrite("WAVEfmt ", 1, 8, f);
    u = 16; fwrite(&u, 4, 1, f); h = 3; fwrite(&h, 2, 1, f); h = 1; fwrite(&h, 2, 1, f); u = sr; fwrite(&u, 4, 1, f);
    u = sr * 4; fwrite(&u, 4, 1, f); h = 4; fwrite(&h, 2, 1, f); h = 32; fwrite(&h, 2, 1, f);
    fwrite("data", 1, 4, f); fwrite(&n, 4, 1, f); fwrite(x.data(), 4, x.size(), f); fclose(f);
}

static void applyEvents(cr::ParamTimeline& p, const JValue& ev) {
    for (auto& e : ev.a) {
        const std::string k = e.a[0].str();
        auto n = [&](size_t i) { return e.a.size() > i ? e.a[i].num(0) : 0.0; };
        if (k == "v") p.setValue(n(1), 0);
        else if (k == "set") p.setValueAtTime(n(1), n(2), 0);
        else if (k == "lin") p.linearRampToValueAtTime(n(1), n(2), 0);
        else if (k == "exp") p.exponentialRampToValueAtTime(n(1), n(2), 0);
        else if (k == "tgt") p.setTargetAtTime(n(1), n(2), n(3), 0);
        else if (k == "curve") { std::vector<float> c; for (auto& v : e.a[1].a) c.push_back((float)v.num(0)); p.setValueCurveAtTime(c, n(2), n(3), 0); }
    }
}
static std::shared_ptr<cr::AudioBufferData> genBuf(const JValue& b) {
    auto d = std::make_shared<cr::AudioBufferData>();
    d->sampleRate = (float)b["sr"].num(48000);
    const long len = (long)b["len"].num(1000), g = (long)b["gen"].num(0);
    d->ch.assign(1, std::vector<float>(len));
    for (long i = 0; i < len; i++) d->ch[0][i] = (float)((double)((i * 7919 + g * 104729) % 2001 - 1000) / 1000);
    return d;
}
static std::unique_ptr<cr::BufferSource> mkSrc(const JValue& s, double sr, unsigned Q) {
    std::unique_ptr<cr::BufferSource> b(new cr::BufferSource(sr, Q));
    if (s["rate"].t == JValue::Array) applyEvents(b->playbackRate(), s["rate"]);
    if (s["detune"].t == JValue::Array) applyEvents(b->detune(), s["detune"]);
    if (s["loop"].t == JValue::Array) b->setLoop(true, s["loop"].a[0].num(0), s["loop"].a[1].num(0));
    b->setBuffer(genBuf(s["buf"]));
    const JValue& st = s["start"];
    if (st.t == JValue::Array) b->start(st.a.size() > 0 ? st.a[0].num(0) : 0, st.a.size() > 1 ? st.a[1].num(0) : 0, st.a.size() > 2 ? st.a[2].num(0) : 0, st.a.size() > 2, 0);
    else b->start(0);
    if (s["stop"].t == JValue::Number) b->stop(s["stop"].num(0));
    return b;
}
// task NB-N3j: the timeline, buffer source, automated gain and biquad cases
static bool runAuto(const JValue& c, double sr, size_t Q, size_t N, std::vector<float>& out) {
    out.assign(((N + Q - 1) / Q) * Q, 0.f);
    std::vector<float> q(Q), o(Q);
    float* qp[1] = {q.data()}; float* op[1] = {o.data()};
    if (c["param"].t == JValue::Object) {
        const JValue& p = c["param"];
        cr::GainNodeA g(sr, (unsigned)Q);
        if (p["krate"].t == JValue::Bool && p["krate"].b) g.gain.setAudioRate(false);
        applyEvents(g.gain, p["ev"]);
        cr::ConstantSource one((float)sr); one.setOffset(1); one.sched.startAt(0, 0);
        for (size_t f = 0; f < out.size(); f += Q) {
            one.process(f, Q, q.data());
            const float* ip[1] = {q.data()};
            const bool on = g.process(f, ip, false, op, 1, Q);
            std::copy(o.begin(), o.end(), out.begin() + f); (void)on;
        }
        return true;
    }
    if (c["src"].t == JValue::Object) {
        auto b = mkSrc(c["src"], sr, (unsigned)Q);
        std::unique_ptr<cr::GainNodeA> g; std::unique_ptr<cr::BiquadNodeA> bq;
        if (c["gain"].t == JValue::Array) { g.reset(new cr::GainNodeA(sr, (unsigned)Q)); applyEvents(g->gain, c["gain"]); }
        if (c["bq"].t == JValue::Object) {
            const JValue& d = c["bq"]; bq.reset(new cr::BiquadNodeA(sr, (unsigned)Q));
            cr::BiquadType t; if (cr::biquadTypeOf(d["type"].str(), t)) bq->type = t;
            if (d["freq"].t == JValue::Array) applyEvents(bq->frequency, d["freq"]);
            if (d["q"].t == JValue::Array) applyEvents(bq->Q, d["q"]);
            if (d["gain"].t == JValue::Array) applyEvents(bq->gain, d["gain"]);
            if (d["detune"].t == JValue::Array) applyEvents(bq->detune, d["detune"]);
        }
        for (size_t f = 0; f < out.size(); f += Q) {
            const bool on = b->process(f, qp, Q);
            const float* ip[1] = {q.data()};
            if (g) { g->process(f, ip, !on, op, 1, Q); std::copy(o.begin(), o.end(), q.begin()); }
            if (bq) { bq->process(f, ip, op, 1, Q); std::copy(o.begin(), o.end(), q.begin()); }
            std::copy(q.begin(), q.end(), out.begin() + f);
        }
        return true;
    }
    return false;
}

int main(int argc, char** argv) {
    if (argc < 3) { fprintf(stderr, "usage: alnodes cases.json outdir\n"); return 2; }
    std::string src, err; if (!readFile(argv[1], src)) return 2;
    JValue cj; if (!parseJson(src, cj, err)) { fprintf(stderr, "%s\n", err.c_str()); return 2; }
    for (auto& c : cj["cases"].a) {
        const double sr = c["sr"].num(48000); const size_t Q = (size_t)c["quantum"].num(128), N = (size_t)c["frames"].num(48000);
        NodeFloatState fz;
        {
            std::vector<float> ao;
            auto t1 = std::chrono::steady_clock::now();
            if (runAuto(c, sr, Q, N, ao)) {
                double us = std::chrono::duration<double, std::micro>(std::chrono::steady_clock::now() - t1).count();
                ao.resize(N);
                wavWrite(std::string(argv[2]) + "/" + c["name"].str() + ".wav", (int)sr, ao);
                printf("{\"name\":\"%s\",\"us\":%.1f}\n", c["name"].str().c_str(), us);
                continue;
            }
        }
        std::unique_ptr<cr::Oscillator> osc; std::unique_ptr<cr::ConstantSource> cs;
        if (c["osc"].t == JValue::Object) {
            const JValue& o = c["osc"]; cr::OscType t; if (!cr::oscTypeOf(o["type"].str(), t)) t = cr::OscType::Sine;
            osc.reset(new cr::Oscillator((float)sr, t)); osc->setFrequency(o["freq"].num(440)); osc->setDetune(o["detune"].num(0));
            osc->sched.startAt(o["start"].num(0), 0); if (o["stop"].t == JValue::Number) osc->sched.stopAt(o["stop"].num(0));
        } else {
            const JValue& o = c["const"]; cs.reset(new cr::ConstantSource((float)sr)); cs->setOffset(o["offset"].num(1));
            cs->sched.startAt(o["start"].num(0), 0); if (o["stop"].t == JValue::Number) cs->sched.stopAt(o["stop"].num(0));
        }
        std::vector<float> curve; bool shape = c["shape"].t == JValue::Object;
        if (shape) for (auto& v : c["shape"]["curve"].a) curve.push_back((float)v.num(0));
        std::vector<float> out(((N + Q - 1) / Q) * Q), q(Q);
        auto t0 = std::chrono::steady_clock::now();
        for (size_t p = 0; p < out.size(); p += Q) {
            if (osc) osc->process(p, Q, q.data()); else cs->process(p, Q, q.data());
            if (shape) cr::waveShape(q.data(), q.data(), Q, curve);
            std::copy(q.begin(), q.end(), out.begin() + p);
        }
        double us = std::chrono::duration<double, std::micro>(std::chrono::steady_clock::now() - t0).count();
        out.resize(N);
        wavWrite(std::string(argv[2]) + "/" + c["name"].str() + ".wav", (int)sr, out);
        printf("{\"name\":\"%s\",\"us\":%.1f}\n", c["name"].str().c_str(), us);
    }
    return 0;
}
