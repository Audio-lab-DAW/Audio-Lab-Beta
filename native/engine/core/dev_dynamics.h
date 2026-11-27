// The dynamics family of the web engine's worklets, ported statement by statement (task NB-N3a):
//   limit -> 'al-limit' (class Lim), gate -> 'al-gate' (Gate), trans -> 'al-trans' (Trn), deess -> 'al-deess' (Dss)
// Source: WLSRC in index.html (v0.229). Rules: every JavaScript number is a double here, every Float32Array
// is float, the order of operations is the JavaScript order, no fused multiply-add (-ffp-contract=off).
// Meter fields are kept because they are state the interface reads (the engine keeps all state).
#pragma once
#include <vector>
#include "device.h"

namespace al {
namespace dyn {
using namespace js;

// 4x inter-sample peak estimate on the segment between s1 and s2 (tpk in WLSRC)
inline double tpk(double s0, double s1, double s2, double s3) {
    return js::max(js::abs((-s0 + 9 * s1 + 9 * s2 - s3) / 16), js::abs((-9 * s0 + 111 * s1 + 29 * s2 - 3 * s3) / 128),
                   js::abs((-3 * s0 + 29 * s1 + 111 * s2 - 9 * s3) / 128));
}

// ---------- true-peak look-ahead limiter ----------
struct Lim : Processor {
    double sr;
    int D;
    std::vector<float> dl[2];
    double h[2][4] = {{0, 0, 0, 0}, {0, 0, 0, 0}};
    double e1 = 1, e2 = 1, a = 0, ap = 0, am = 0, mn = 1, ip = 0, op = 0, c = 0;
    // reset(L)
    int L = 0, W = 0;
    std::vector<float> ring;
    double sum = 0;
    std::vector<double> dq;
    std::vector<float> dv;
    int qh = 0, qt = 0;
    double nn = 0;  // this.n
    int w = 0;
    explicit Lim(RenderContext& ctx) : sr(ctx.sampleRate) {
        D = (int)js::ceil(sr * .03) + 16;
        dl[0].assign(D, 0); dl[1].assign(D, 0);
        reset(2);
    }
    void reset(int look) {
        L = look; W = look + 1;
        ring.assign(W, 1.0f); sum = W;
        dq.assign((size_t)D * 2, 0); dv.assign((size_t)D * 2, 0);
        qh = 0; qt = 0; nn = 0;
        std::fill(dl[0].begin(), dl[0].end(), 0.0f); std::fill(dl[1].begin(), dl[1].end(), 0.0f);
        w = 0;
    }
    void process(const float* Lin, const float* Rin, float* oL, float* oR, int n) override {
        const double gi = dB(p.orNum("gain", 0)), go = dB(p.orNum("out", 0)), ce = dB(p.nnNum("ceil", -.3));
        const bool tp = p.notFalse("tp");
        const std::string st = p.orStr("style", "clean");
        double look = js::max(1, js::round(p.orNum("look", 2) * sr / 1000));
        if (st == "aggressive") look = js::max(1, js::shr(look, 2));
        if (look != L) reset((int)look);
        const int lk = (int)look;
        const double rel = js::max(5, p.orNum("rel", 120)) / 1000, rc1 = 1 - std::exp(-1 / (rel * .12 * sr)),
                     rc2 = 1 - std::exp(-1 / (rel * sr));
        const int Q = D * 2;
        const bool smooth2 = (st == "transparent" || st == "clean");
        for (int i = 0; i < n; i++) {
            const double l = Lin[i] * gi, r = Rin[i] * gi;
            double* h0 = h[0]; double* h1 = h[1];
            h0[0] = h0[1]; h0[1] = h0[2]; h0[2] = h0[3]; h0[3] = l;
            h1[0] = h1[1]; h1[1] = h1[2]; h1[2] = h1[3]; h1[3] = r;
            double pk = js::max(js::abs(l), js::abs(r));
            if (tp) pk = js::max(pk, tpk(h0[0], h0[1], h0[2], h0[3]), tpk(h1[0], h1[1], h1[2], h1[3]));
            if (pk > ip) ip = pk;
            const double need = pk > ce ? ce / pk : 1;
            while (qt != qh && (double)dv[(qt - 1 + Q) % Q] >= need) qt = (qt - 1 + Q) % Q;
            dq[qt] = nn; dv[qt] = f32(need); qt = (qt + 1) % Q;
            while (dq[qh] <= nn - W) qh = (qh + 1) % Q;
            const double m = dv[qh];
            const int k = (int)std::fmod(nn, (double)W);
            sum += m - (double)ring[k]; ring[k] = f32(m);
            const double ga = sum / W;
            double g;
            if (smooth2) {
                e1 = ga < e1 ? ga : e1 + (ga - e1) * rc1;
                e2 = ga < e2 ? ga : e2 + (ga - e2) * rc2;
                g = (e1 + e2) * .5;
            } else {
                e1 = ga < e1 ? ga : e1 + (ga - e1) * rc2 * 1.6;
                e2 = e1; g = e1;
            }
            dl[0][w] = f32(l); dl[1][w] = f32(r);
            const int rp = (w - lk + D) % D;
            double yl = (double)dl[0][rp] * g * go, yr = (double)dl[1][rp] * g * go;
            const double cl = ce * go;
            if (yl > cl) yl = cl; else if (yl < -cl) yl = -cl;
            if (yr > cl) yr = cl; else if (yr < -cl) yr = -cl;
            oL[i] = f32(yl); oR[i] = f32(yr);
            const double apk = js::max(js::abs(yl), js::abs(yr));
            if (apk > op) op = apk;
            if (g < mn) mn = g;
            w = (w + 1) % D;
            nn++;
        }
        c += n;
        if (c >= 1024) { c = 0; lastIn = ip; lastOut = op; lastGain = mn; ip = op = 0; mn = 1; }
    }
    double lastIn = 0, lastOut = 0, lastGain = 1;
    std::vector<std::pair<std::string, double>> meters() const override { return {{"i", lastIn}, {"o", lastOut}, {"g", lastGain}}; }
    void flushTiny() override {
        for (auto& hh : h) for (double& v : hh) z(v);
        z(e1); z(e2); z(a); z(ap); z(am); z(mn); z(ip); z(op); z(c); z(sum);
    }
};

// ---------- gate / expander ----------
struct Gate : Processor {
    double sr;
    int D;
    std::vector<float> dl[2];
    int w = 0;
    double lv = 0, g = 0;
    bool open = false;
    double hold = 0, hp[2] = {0, 0}, lp[2] = {0, 0}, c = 0, mg = 1, ml = 0, mo = 0;
    explicit Gate(RenderContext& ctx) : sr(ctx.sampleRate) {
        D = (int)js::ceil(sr * .02) + 8;
        dl[0].assign(D, 0); dl[1].assign(D, 0);
    }
    void process(const float* L, const float* R, float* oL, float* oR, int n) override {
        const double thr = p.nnNum("thr", -40), hy = p.nnNum("hyst", 4), fl = dB(p.nnNum("floor", -80)),
                     lookd = js::round(p.orNum("look", 0) * sr / 1000),
                     ca = 1 - std::exp(-1 / (js::max(.05, p.orNum("att", 1)) / 1000 * sr)),
                     cr = 1 - std::exp(-1 / (js::max(1, p.orNum("rel", 120)) / 1000 * sr)),
                     holdv = p.orNum("hold", 40) / 1000 * sr,
                     hpc = 1 - std::exp(-TAU * p.orNum("hpf", 20) / sr),
                     lpc = 1 - std::exp(-TAU * js::min(sr * .45, p.orNum("lpf", 20000)) / sr);
        const bool ex = p.is("mode", "expander"), listen = p.truthy("listen");
        const double ra = p.orNum("ratio", 2), dec = std::exp(-1 / (.005 * sr));
        const int look = (int)lookd;
        for (int i = 0; i < n; i++) {
            double d = ((double)L[i] + (double)R[i]) * .5;
            hp[0] += hpc * (d - hp[0]); d -= hp[0];
            lp[0] += lpc * (d - lp[0]); d = lp[0];
            const double a = js::abs(d);
            lv = a > lv ? a : lv * dec + a * (1 - dec);
            const double ldb = lg(lv);
            if (!open && ldb > thr) { open = true; hold = holdv; }
            else if (open) { if (ldb > thr - hy) hold = holdv; else if (--hold <= 0) open = false; }
            double tg;
            if (ex) { const double under = js::max(0, thr - ldb); tg = js::max(fl, dB(-under * (ra - 1))); }
            else tg = open ? 1 : fl;
            if (ex && open) tg = 1;
            g += (tg - g) * (tg > g ? ca : cr);
            dl[0][w] = L[i]; dl[1][w] = R[i];
            const int rp = (w - look + D) % D;
            const double gg = g;
            if (listen) { oL[i] = f32(d); oR[i] = f32(d); }
            else { oL[i] = f32((double)dl[0][rp] * gg); oR[i] = f32((double)dl[1][rp] * gg); }
            w = (w + 1) % D;
            if (gg < mg) mg = gg;
            if (ldb > ml) ml = ldb;
            if (open) mo = 1;
        }
        c += n;
        if (c >= 512) { c = 0; lastLv = ml; lastG = mg; lastOpen = mo; mg = 1; ml = -120; mo = 0; }
    }
    double lastLv = -120, lastG = 1, lastOpen = 0;
    std::vector<std::pair<std::string, double>> meters() const override { return {{"lv", lastLv}, {"g", lastG}, {"open", lastOpen}}; }
    void flushTiny() override { z(lv); z(g); z(hold); z(hp[0]); z(hp[1]); z(lp[0]); z(lp[1]); z(c); z(mg); z(ml); z(mo); }
};

// ---------- transient shaper ----------
struct Trn : Processor {
    double sr;
    double f = 0, s = 0, g = 1, c = 0, mg = 1, mx = 0, fl = 0;
    explicit Trn(RenderContext& ctx) : sr(ctx.sampleRate) {}
    void process(const float* L, const float* R, float* oL, float* oR, int n) override {
        const double sp = js::max(.2, p.orNum("speed", 1)), A = p.orNum("attack", 0) / 100, S = p.orNum("sustain", 0) / 100,
                     go = dB(p.orNum("out", 0)),
                     fa = 1 - std::exp(-1 / (.0008 * sr / sp)), fr = 1 - std::exp(-1 / (.02 * sr / sp)),
                     sa = 1 - std::exp(-1 / (.012 * sr / sp)), sr2 = 1 - std::exp(-1 / (.14 * sr / sp)),
                     gc = 1 - std::exp(-1 / (.0006 * sr));
        for (int i = 0; i < n; i++) {
            const double a = js::max(js::abs(L[i]), js::abs(R[i]));
            f += (a > f ? fa : fr) * (a - f);
            s += (a > s ? sa : sr2) * (a - s);
            const double df = lg(f) - lg(s);
            // (the worklet also works out an unused 'gate' value here; it has no effect)
            double tg = 0;
            if (df > 0) tg = A * df * .9; else tg = S * (-df) * .5;
            if (s < 1e-4) tg = 0;
            tg = js::max(-18, js::min(18, tg));
            const double t2 = dB(tg);
            g += (t2 - g) * gc;
            oL[i] = f32((double)L[i] * g * go); oR[i] = f32((double)R[i] * g * go);
            if (g < mg) mg = g;
            if (g > mx) mx = g;
        }
        c += n;
        if (c >= 512) { c = 0; lastLo = mg; lastHi = mx; mg = 1; mx = 1; }
    }
    double lastLo = 1, lastHi = 1;
    std::vector<std::pair<std::string, double>> meters() const override { return {{"f", f}, {"s", s}, {"g", g}, {"lo", lastLo}, {"hi", lastHi}}; }
    void flushTiny() override { z(f); z(s); z(g); z(c); z(mg); z(mx); z(fl); }
};

// ---------- de-esser ----------
struct Dss : Processor {
    double sr;
    double zst[4] = {0, 0, 0, 0}, zz[4] = {0, 0, 0, 0};
    double env = 0, gr = 0, c = 0, mx = 0, dl = 0;
    struct K { double b0, b2, a1, a2; };
    explicit Dss(RenderContext& ctx) : sr(ctx.sampleRate) {}
    K bp(double f, double q) const {
        const double w = TAU * f / sr, al = std::sin(w) / (2 * q), a0 = 1 + al;
        return {al / a0, -al / a0, -2 * std::cos(w) / a0, (1 - al) / a0};
    }
    double bq(int ch, double x, const K& k) {
        const int o = ch * 2;
        const double y = k.b0 * x + zz[o];
        zz[o] = zz[o + 1] - k.a1 * y;
        zz[o + 1] = k.b2 * x - k.a2 * y;
        return y;
    }
    void process(const float* L, const float* R, float* oL, float* oR, int n) override {
        const K k = bp(js::min(sr * .45, p.orNum("freq", 6500)), js::max(.3, p.orNum("q", 1.5)));
        const double thr = p.nnNum("thr", -30), rt = p.orNum("ratio", 4), rg = p.nnNum("range", 12),
                     ca = 1 - std::exp(-1 / (js::max(.1, p.orNum("att", 1)) / 1000 * sr)),
                     cr = 1 - std::exp(-1 / (js::max(1, p.orNum("rel", 60)) / 1000 * sr)),
                     go = dB(p.orNum("out", 0));
        const bool split = p.is("mode", "split"), listen = p.truthy("listen");
        double* z = zst;
        for (int i = 0; i < n; i++) {
            const double m = ((double)L[i] + (double)R[i]) * .5, y = k.b0 * m + z[0];
            z[0] = z[1] - k.a1 * y;
            z[1] = k.b2 * m - k.a2 * y;
            const double a = js::abs(y);
            env = a > env ? env + (a - env) * .2 : env * .9995 + a * .0005;
            const double d = lg(env * 1.4);
            const double over = js::max(0, d - thr), grt = js::min(rg, over * (1 - 1 / rt));
            gr += (grt - gr) * (grt > gr ? ca : cr);
            const double g = dB(-gr);
            if (listen) { oL[i] = oR[i] = f32(y * go); }
            else if (split) {
                const double bl = bq(0, L[i], k), br = bq(1, R[i], k);
                oL[i] = f32(((double)L[i] + (g - 1) * bl) * go);
                oR[i] = f32(((double)R[i] + (g - 1) * br) * go);
            } else { oL[i] = f32((double)L[i] * g * go); oR[i] = f32((double)R[i] * g * go); }
            if (gr > mx) mx = gr;
            dl = js::max(dl, d);
        }
        c += n;
        if (c >= 512) { c = 0; lastGr = mx; lastDet = dl; mx = 0; dl = -120; }
    }
    double lastGr = 0, lastDet = -120;
    std::vector<std::pair<std::string, double>> meters() const override { return {{"gr", lastGr}, {"det", lastDet}}; }
    void flushTiny() override { for (double& v : zst) z(v); for (double& v : zz) z(v); z(env); z(gr); z(c); z(mx); z(dl); }
};

}  // namespace dyn
}  // namespace al
