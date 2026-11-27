// The modulation and time family of the web engine's worklets, ported statement by statement (task NB-N3c):
//   chorus -> 'al-chorus' (Cho), imager -> 'al-imager' (Img with Sp4), fshift -> 'al-fshift' (FSh),
//   vocoder -> 'al-voc' (Voc), tstop -> 'al-tstop' (Tps)
// Source: WLSRC in index.html (v0.230, the same text as v0.229). Same rules as dev_dynamics.h: JavaScript numbers
// are doubles, Float32Array elements are floats, the JavaScript order of operations, no fused multiply-add.
// flushTiny() lists what the bundle's dnFlush reaches: own numbers, plain number arrays and Float64Arrays up to
// 64 long (nested up to 5 levels); not Float32Arrays and not longer arrays (FSh's 126-long buffers are not reached).
#pragma once
#include <array>
#include <string>
#include <vector>
#include "device.h"

namespace al {
namespace mod {
using namespace js;

// ---------- chorus / flanger / ensemble ----------
struct Cho : Processor {
    double sr;
    static constexpr int M = 8192;
    std::vector<float> ln[4][2];
    int w = 0;
    double ph = 0, ph2 = 0, fbv[4][2] = {{0, 0}, {0, 0}, {0, 0}, {0, 0}}, hp[2] = {0, 0}, lp[2] = {0, 0}, c = 0;
    explicit Cho(RenderContext& ctx) : sr(ctx.sampleRate) {
        for (auto& v : ln) for (auto& x : v) x.assign(M, 0.f);
    }
    void process(const float* L, const float* R, float* oL, float* oR, int n) override {
        const std::string mode = p.orStr("mode", "chorus");
        const bool fl = mode == "flanger", ens = mode == "ensemble", dim = mode == "dimension";
        const int V = fl ? 1 : ens ? 3 : dim ? 4 : 2;
        const double rate = js::max(.01, p.orNum("rate", .6)), dph = rate / sr, dm = js::max(0, p.orNum("depth", 0)) / 100,
                     bd = js::max(.3, p.orNum("delay", 8)), fb = p.orNum("fb", 0) / 100,
                     wid = js::max(0, js::min(1, p.nnNum("width", 80) / 100)), mix = p.nnNum("mix", 50) / 100,
                     hpc = 1 - js::exp(-TAU * p.orNum("lowcut", 20) / sr),
                     lpc = 1 - js::exp(-TAU * js::min(sr * .45, p.orNum("highcut", 20000)) / sr);
        const bool tri = p.is("shape", "triangle");
        static const double OE[4] = {0, 1.0 / 3, 2.0 / 3, 0}, OD[4] = {0, .25, .5, .75}, OF[4] = {0, 0, 0, 0}, OC[4] = {0, .5, 0, 0};
        const double* off = ens ? OE : dim ? OD : fl ? OF : OC;
        const double range = fl ? js::min(bd * .92, bd * dm) : dim ? bd * .18 * dm : js::min(bd * .9, dm * js::min(bd * .6, 8));
        for (int i = 0; i < n; i++) {
            ph = std::fmod(ph + dph, 1.0);
            ph2 = std::fmod(ph2 + dph * .37, 1.0);
            const double ins[2] = {(double)L[i], (double)R[i]};
            double o[2] = {0, 0};
            for (int v = 0; v < V; v++)
                for (int ch = 0; ch < 2; ch++) {
                    const double pp = std::fmod(ph + off[v] + (ch ? wid * .5 : 0), 1.0),
                                 s = tri ? 1 - 4 * js::abs(std::fmod(pp + .25, 1.0) - .5) : js::sin(TAU * pp),
                                 s2 = ens ? js::sin(TAU * (ph2 + off[v])) : 0,
                                 d = (bd + range * (s * .75 + s2 * .25)) * sr / 1000;
                    std::vector<float>& l = ln[v][ch];
                    double rp = w - d;
                    rp = std::fmod(std::fmod(rp, (double)M) + M, (double)M);
                    const double i0 = std::floor(rp), fr = rp - i0;
                    const int ii = (int)i0;
                    const double y = (double)l[ii] * (1 - fr) + (double)l[(ii + 1) % M] * fr;
                    l[w] = f32(ins[ch] + fbv[v][ch] * fb * (fl ? 1 : .5));
                    fbv[v][ch] = y;
                    o[ch] += y * (fl ? 1 : 1 / std::sqrt((double)V));
                }
            for (int ch = 0; ch < 2; ch++) {
                hp[ch] += hpc * (o[ch] - hp[ch]);
                double y = o[ch] - hp[ch];
                lp[ch] += lpc * (y - lp[ch]);
                y = lp[ch];
                (ch ? oR : oL)[i] = f32(ins[ch] * (1 - mix * .5) + y * mix);
            }
            w = (w + 1) % M;
        }
        c += n;
        if (c >= 1024) c = 0;
    }
    std::vector<std::pair<std::string, double>> meters() const override { return {{"ph", ph}}; }
    void flushTiny() override {
        z(ph); z(ph2); z(c);
        for (auto& a : fbv) { z(a[0]); z(a[1]); }
        z(hp[0]); z(hp[1]); z(lp[0]); z(lp[1]);
    }
};

// ---------- stereo imager: 4-band LR4, per-band width ----------
struct Sp4 {
    struct K { double b0, b1, b2, a1, a2; };
    double z[8][2] = {};
    double lo = 0, hi = 0;
    static K coef(bool t, double f, double sr) {
        const double w = TAU * f / sr, c = js::cos(w), s = js::sin(w), al = s / (2 * .70710678), a0 = 1 + al;
        K k;
        if (t) { k.b0 = (1 + c) / 2 / a0; k.b1 = -(1 + c) / a0; k.b2 = (1 + c) / 2 / a0; }
        else { k.b0 = (1 - c) / 2 / a0; k.b1 = (1 - c) / a0; k.b2 = (1 - c) / 2 / a0; }
        k.a1 = -2 * c / a0;
        k.a2 = (1 - al) / a0;
        return k;
    }
    static double bq(const K& k, double x, double* zz) {
        const double y = k.b0 * x + zz[0];
        zz[0] = k.b1 * x - k.a1 * y + zz[1];
        zz[1] = k.b2 * x - k.a2 * y;
        return y;
    }
    void run(int ch, double x, const K& kl, const K& kh) {
        const int o = ch * 4;
        lo = bq(kl, bq(kl, x, z[o]), z[o + 1]);
        hi = bq(kh, bq(kh, x, z[o + 2]), z[o + 3]);
    }
    double ap(int ch, double x, const K& kl, const K& kh) { run(ch, x, kl, kh); return lo + hi; }
    void flush() { for (auto& a : z) { Processor::z(a[0]); Processor::z(a[1]); } Processor::z(lo); Processor::z(hi); }
};

struct Img : Processor {
    double sr;
    Sp4 s2, s1, s3, a3[2], a1[2];
    bool haveK = false;
    int xp = -1;
    Sp4::K l1, h1, l2, h2, l3, h3;
    double w[4] = {0, 0, 0, 0}, bl[4] = {0, 0, 0, 0}, br[4] = {0, 0, 0, 0};
    explicit Img(RenderContext& ctx) : sr(ctx.sampleRate) {}
    void process(const float* L, const float* R, float* oL, float* oR, int n) override {
        if (xp != pv || !haveK) {
            xp = pv;
            const double f1 = js::max(30, p.orNum("x1", 120)), f2 = js::max(f1 * 1.3, p.orNum("x2", 1000)), f3 = js::max(f2 * 1.3, p.orNum("x3", 6000));
            l1 = Sp4::coef(false, f1, sr); h1 = Sp4::coef(true, f1, sr);
            l2 = Sp4::coef(false, f2, sr); h2 = Sp4::coef(true, f2, sr);
            l3 = Sp4::coef(false, f3, sr); h3 = Sp4::coef(true, f3, sr);
            haveK = true;
        }
        const int sol = js::toInt32(p.num("solo"));
        const double gm = dB(p.orNum("mg", 0)), gs = dB(p.orNum("sg", 0)), go = dB(p.orNum("out", 0));
        w[0] = p.nnNum("w1", 100) / 100; w[1] = p.nnNum("w2", 100) / 100; w[2] = p.nnNum("w3", 100) / 100; w[3] = p.nnNum("w4", 100) / 100;
        if (p.truthy("bmono")) w[0] = 0;
        for (int i = 0; i < n; i++) {
            for (int c = 0; c < 2; c++) {
                const double xx = c ? R[i] : L[i];
                s2.run(c, xx, l2, h2);
                const double lo = s2.lo, hi = s2.hi;
                s1.run(c, lo, l1, h1);
                double b1 = s1.lo, b2 = s1.hi;
                s3.run(c, hi, l3, h3);
                double b3 = s3.lo, b4 = s3.hi;
                b1 = a3[0].ap(c, b1, l3, h3); b2 = a3[1].ap(c, b2, l3, h3); b3 = a1[0].ap(c, b3, l1, h1); b4 = a1[1].ap(c, b4, l1, h1);
                double* t = c ? br : bl;
                t[0] = b1; t[1] = b2; t[2] = b3; t[3] = b4;
            }
            double oL1 = 0, oR1 = 0;
            for (int b = 0; b < 4; b++) {
                const double l = bl[b], r = br[b], m = (l + r) * .5, s = (l - r) * .5;
                if (sol && sol != b + 1) continue;
                const double m2 = m * gm, sv = s * w[b] * gs;
                oL1 += m2 + sv;
                oR1 += m2 - sv;
            }
            oL[i] = f32(oL1 * go); oR[i] = f32(oR1 * go);
        }
        // (the band and output correlation meters of the worklet are not ported yet; they do not touch the sound)
    }
    void flushTiny() override {
        s2.flush(); s1.flush(); s3.flush(); a3[0].flush(); a3[1].flush(); a1[0].flush(); a1[1].flush();
        for (int i = 0; i < 4; i++) { z(w[i]); z(bl[i]); z(br[i]); }
    }
};

// ---------- frequency shifter / ring modulator ----------
struct FSh : Processor {
    double sr;
    static constexpr int N = 63;
    double h[N];
    std::vector<double> buf[2];
    int w = 0;
    double ph = 0, lf = 0, fbv[2] = {0, 0}, c = 0;
    explicit FSh(RenderContext& ctx) : sr(ctx.sampleRate) {
        for (int i = 0; i < N; i++) {
            const double k = i - (N - 1) / 2.0;
            h[i] = (k == 0 || std::fmod(k, 2.0) == 0) ? 0
                 : 2 / (PI * k) * (.42 - .5 * js::cos(TAU * i / (N - 1)) + .08 * js::cos(2 * TAU * i / (N - 1)));
        }
        buf[0].assign(N * 2, 0); buf[1].assign(N * 2, 0);
    }
    void process(const float* L, const float* R, float* oL, float* oR, int n) override {
        const double mix = p.nnNum("mix", 100) / 100, fb = p.orNum("fb", 0) / 100;
        const bool ring = p.is("mode", "ring"), both = p.is("mode", "both"), down = p.is("dir", "down");
        const double go = dB(p.orNum("out", 0)), lr = p.orNum("lfoRate", 0), ld = p.orNum("lfoDepth", 0), shift = p.orNum("shift", 0);
        const int dly = (N - 1) / 2;
        for (int i = 0; i < n; i++) {
            lf = std::fmod(lf + lr / sr, 1.0);
            const double sh = shift + js::sin(TAU * lf) * ld;
            ph = std::fmod(ph + sh / sr, 1.0);
            const double cs = js::cos(TAU * ph), sn = js::sin(TAU * ph);
            const double ins[2] = {(double)L[i], (double)R[i]};
            for (int ch = 0; ch < 2; ch++) {
                std::vector<double>& bf = buf[ch];
                const double xin = ins[ch] + fbv[ch] * fb;
                bf[w] = xin; bf[w + N] = xin;
                double im = 0;
                const int base = w + N;
                for (int k = 0; k < N; k++) im += h[k] * bf[base - k];
                const double re = bf[base - dly];
                double y;
                if (ring) y = xin * js::cos(TAU * ph);
                else {
                    y = down ? re * cs + im * sn : re * cs - im * sn;
                    if (both) y = (y + xin * cs) * .7;
                }
                fbv[ch] = y;
                (ch ? oR : oL)[i] = f32((ins[ch] * (1 - mix) + y * mix) * go);
            }
            w = (w + 1) % N;
        }
    }
    void flushTiny() override { for (double& v : h) z(v); z(ph); z(lf); z(fbv[0]); z(fbv[1]); z(c); }
};

// ---------- vocoder ----------
struct Voc : Processor {
    double sr;
    RenderContext* ctx;
    int nb = 0;
    double phArr[6] = {0, 0, 0, 0, 0, 0}, nzField = 0, c = 0, lp = 0, hpz = 0, q = 0;
    std::vector<float> me, ce, gs;
    std::vector<double> fc, mz, cz;
    bool cf = false;
    int ckNb = -1; double ckFsh = NAN, ckBw = NAN;  // this.ck = nb+'|'+fsh+'|'+bw
    std::vector<std::array<double, 4>> mk, ck2;
    int vp = -1;
    bool haveVfr = false;
    std::vector<double> vfr, ph2;
    explicit Voc(RenderContext& cx) : sr(cx.sampleRate), ctx(&cx) { build(16); }
    void build(int n) {
        nb = n;
        me.assign(n, 0.f); ce.assign(n, 0.f); gs.assign(n, 0.f);
        const double lo = 90, hi = js::min(12000, sr * .45);
        fc.clear();
        for (int i = 0; i < n; i++) fc.push_back(lo * js::pow(hi / lo, (double)i / (n - 1)));
        mz.assign((size_t)n * 2, 0); cz.assign((size_t)n * 2, 0);
        q = 0;
    }
    std::array<double, 4> coef(double f, double qq) const {
        const double w = TAU * f / sr, al = js::sin(w) / (2 * qq), a0 = 1 + al;
        return {al / a0, -al / a0, -2 * js::cos(w) / a0, (1 - al) / a0};
    }
    void process(const float* L, const float* R, float* oL, float* oR, int n) override {
        const int nbw = (int)js::max(4, js::min(32, js::round(p.orNum("bands", 16))));
        if (nbw != nb) build(nbw);
        const double fsh = js::pow(2.0, p.orNum("formant", 0) / 12), bw = p.orNum("bw", 1.2), qq = js::max(.5, nb / (6 / bw)),
                     ca = 1 - js::exp(-1 / (js::max(.2, p.orNum("att", 3)) / 1000 * sr)),
                     cr = 1 - js::exp(-1 / (js::max(1, p.orNum("rel", 40)) / 1000 * sr)),
                     mix = p.nnNum("mix", 100) / 100, go = dB(p.orNum("out", 0)), un = p.orNum("sib", 0) / 100,
                     det = p.orNum("detune", 0), nz = p.orNum("noise", 0) / 100;
        const std::string cm = p.orStr("carrier", "saw");
        const int cmi = cm == "saw" ? 0 : cm == "pulse" ? 1 : cm == "square" ? 2 : 3;
        if (!cf || ckNb != nb || !(ckFsh == fsh) || !(ckBw == bw)) {
            ckNb = nb; ckFsh = fsh; ckBw = bw;
            mk.clear(); ck2.clear();
            for (double f : fc) mk.push_back(coef(f, qq));
            for (double f : fc) ck2.push_back(coef(js::min(sr * .45, f * fsh), qq));
            cf = true;
        }
        if (vp != pv || !haveVfr) {
            vp = pv; haveVfr = true;
            const double pi = p.nnNum("pitch", 48);
            const JValue& chv = p.at("chord");
            std::vector<double> cc;
            if (Params::truthy(chv) && chv.t == JValue::Array) for (auto& e : chv.a) cc.push_back(Params::toNumber(e));
            vfr.assign(1 + cc.size(), 0);
            vfr[0] = 440 * js::pow(2.0, (pi - 69) / 12);
            for (size_t j = 0; j < cc.size(); j++) vfr[j + 1] = 440 * js::pow(2.0, (pi + cc[j] - 69) / 12);
        }
        const double oct = p.orNum("oct", 0);
        if (ph2.empty() || ph2.size() != vfr.size()) { ph2.assign(vfr.size(), 0); for (auto& v : ph2) v = ctx->random.next(); }
        const int nv = (int)vfr.size();
        for (int i = 0; i < n; i++) {
            const double m = ((double)L[i] + (double)R[i]) * .5;
            double car = 0;
            for (int v = 0; v < nv; v++) {
                const double f = vfr[v] * js::pow(2.0, oct + (v % 2 ? det : -det) / 1200);
                ph2[v] = std::fmod(ph2[v] + f / sr, 1.0);
                const double ph = ph2[v];
                car += cmi == 0 ? (2 * ph - 1) : cmi == 1 ? (ph < .3 ? 1 : -1) : cmi == 2 ? (ph < .5 ? 1 : -1) : js::sin(TAU * ph);
            }
            car /= js::max(1, nv) * .7;
            const double noi = ctx->random.next() * 2 - 1;
            car = car * (1 - nz) + noi * nz;
            double o = 0, oo = 0;
            for (int b = 0; b < nb; b++) {
                const auto& a = mk[b];
                const auto& a2 = ck2[b];
                const double yb = a[0] * m + mz[b * 2];
                mz[b * 2] = mz[b * 2 + 1] - a[2] * yb;
                mz[b * 2 + 1] = a[1] * m - a[3] * yb;
                const double e = js::abs(yb);
                me[b] = f32((double)me[b] + (e > me[b] ? ca : cr) * (e - (double)me[b]));
                const double yc = a2[0] * car + cz[b * 2];
                cz[b * 2] = cz[b * 2 + 1] - a2[2] * yc;
                cz[b * 2 + 1] = a2[1] * car - a2[3] * yc;
                const double g = (double)me[b] * 3.2;
                o += yc * g * (b % 2 ? .8 : 1);
                oo += yc * g * (b % 2 ? 1 : .8);
            }
            const double hp = m - lp;
            lp += .35 * hp * 0 + (m - lp) * .6;
            const double hf = m - lp, he = js::abs(hf);
            hpz += (he > hpz ? ca : cr) * (he - hpz);
            const double sib = noi * hpz * un * 3;
            oL[i] = f32((double)L[i] * (1 - mix) + (o / nb * 2.2 + sib) * mix * go);
            oR[i] = f32((double)R[i] * (1 - mix) + (oo / nb * 2.2 + sib) * mix * go);
        }
        c += n;
        if (c >= 1024) c = 0;
    }
    std::vector<std::pair<std::string, double>> meters() const override {
        std::vector<std::pair<std::string, double>> r;
        for (int b = 0; b < nb; b++) r.push_back({"b" + std::to_string(b), me[b]});
        return r;
    }
    void flushTiny() override {
        for (double& v : phArr) z(v);
        z(nzField); z(c); z(lp); z(hpz); z(q);
        for (double& v : fc) z(v);
        for (double& v : mz) z(v);
        for (double& v : cz) z(v);
        for (double& v : ph2) z(v);
        for (double& v : vfr) z(v);
        for (auto& a : mk) for (double& v : a) z(v);
        for (auto& a : ck2) for (double& v : a) z(v);
    }
};

// ---------- tape stop / half-time / stutter / reverse (transport-synced) ----------
struct Tps : Processor {
    double sr;
    RenderContext* ctx;
    int N;
    std::vector<float> b[2];
    int w = 0;
    bool eng = false;
    double rp = 0, sp = 1, lpF = 0, ls = 0, fade = 1, t0 = 0, c = 0, stt = 0, fl = 0, lastL = NAN, lastR = NAN;
    explicit Tps(RenderContext& cx) : sr(cx.sampleRate), ctx(&cx) {
        N = (int)js::ceil(sr * 4);
        b[0].assign(N, 0.f); b[1].assign(N, 0.f);
    }
    bool runsOnSilence() const override { return true; }
    void process(const float* L, const float* R, float* oL, float* oR, int n) override {
        const double bpm = p.orNum("bpm", 120), spb = 60 / bpm, st = p.orNum("rate", .25), ms = sr / 1000;
        const JValue& stv = p.at("steps");
        std::vector<double> steps;
        if (Params::truthy(stv) && stv.t == JValue::Array) for (auto& e : stv.a) steps.push_back(Params::truthy(e) ? 1 : 0);
        const std::string fx = p.orStr("fx", "tape");
        const int fxi = fx == "tape" ? 0 : fx == "half" ? 1 : fx == "double" ? 2 : fx == "rev" ? 3 : fx == "stutter" ? 4 : 5;
        const bool run = p.truthy("run"), hold = p.truthy("hold");
        const double pt0 = p.num("t0"), now = winStart / sr;  // currentTime of the 128-frame window
        const double Nd = N;
        for (int i = 0; i < n; i++) {
            b[0][w] = L[i]; b[1][w] = R[i];
            const double tm = now + (winOff + i) / sr, beat = run ? (tm - pt0) / spb : -1;
            bool on = hold;
            if (beat >= 0 && !steps.empty()) {
                const double idx = std::floor(beat / st + 1e-6), sl = (double)steps.size();
                const double k = std::fmod(std::fmod(idx, sl) + sl, sl);
                on = on || steps[(size_t)k] != 0;
            }
            if (on && !eng) {
                eng = true; rp = w; sp = 1; ls = w; stt = 0;
                fl = js::max(64, js::round(p.orNum("len", 1.0 / 8) * spb * sr));
            } else if (!on && eng) { eng = false; fade = 0; }
            double yl = L[i], yr = R[i];
            if (eng) {
                stt++;
                if (fxi == 0) { const double stopS = js::max(20, p.orNum("stop", 400)) * ms; sp = js::max(0, 1 - stt / stopS); sp = sp * sp; }
                else if (fxi == 1) sp = .5;
                else if (fxi == 2) sp = 2;
                else if (fxi == 3) sp = -1;
                else if (fxi == 4) sp = 1;
                if (fxi == 4) {
                    rp += 1;
                    if (rp >= ls + 0) rp = ls - fl;
                    if (rp < 0) rp += Nd;
                } else {
                    rp += sp;
                    if (rp >= w + Nd - 1) rp = w + 1;
                }
                double q = rp;
                q = std::fmod(std::fmod(q, Nd) + Nd, Nd);
                const double i0 = std::floor(q), fr = q - i0;
                const int i1 = (int)std::fmod(i0 + 1, Nd);
                const int a0 = (int)std::fmod(std::fmod(i0, Nd) + Nd, Nd);
                yl = (double)b[0][a0] * (1 - fr) + (double)b[0][i1] * fr;
                yr = (double)b[1][a0] * (1 - fr) + (double)b[1][i1] * fr;
                if (stt < 64) { const double f = stt / 64; yl = yl * f + (double)L[i] * (1 - f); yr = yr * f + (double)R[i] * (1 - f); }
                if (fxi == 0 && sp < .02) { yl *= sp * 50; yr *= sp * 50; }
            } else if (fade < 1) {
                fade = js::min(1, fade + 1.0 / 64);
                const double f = fade;
                yl = (double)L[i] * f + lastL * (1 - f);
                yr = (double)R[i] * f + lastR * (1 - f);
            }
            lastL = yl; lastR = yr;
            oL[i] = f32(yl); oR[i] = f32(yr);
            w = (w + 1) % N;
        }
        c += n;
        if (c >= 1024) c = 0;
    }
    std::vector<std::pair<std::string, double>> meters() const override { return {{"eng", eng ? 1.0 : 0.0}, {"sp", sp}}; }
    void flushTiny() override { z(rp); z(sp); z(lpF); z(ls); z(fade); z(t0); z(c); z(stt); z(fl); z(lastL); z(lastR); }
};

}  // namespace mod
}  // namespace al
