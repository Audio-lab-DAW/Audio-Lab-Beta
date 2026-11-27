// The mixer's arithmetic as Chromium's Web Audio does it (task NB-N3b). The app's track channel in an export is
// GainNode (the track's volume) -> StereoPannerNode (the track's pan) -> GainNode (the master), every node with
// a fixed value (renderMix in index.html). These are ports of what Chromium does for nodes whose value does not
// move, so that the native engine's mix is the same bits as the web engine's export:
//   GainNode with a fixed gain: out = in * gain, both float (vector_math::Vsmul).
//   StereoPannerNode (blink stereo_panner.cc): equal-power law, angle and gains worked out in double; see panFixed
//   for the two paths and which one runs when.
//   A summing input (several tracks into the master) adds the connections one after another in float.
// Moving values (automation, setTargetAtTime in live play) are not ported yet: N3b.
// Build with -ffp-contract=off (a fused multiply-add rounds differently).
#pragma once
#include <cmath>
#include <cstddef>

namespace al {

inline void gainFixed(float g, const float* in, float* out, size_t n) {
    if (g == 0) { for (size_t i = 0; i < n; i++) out[i] = 0.f; return; }   // Chromium writes silence (never -0)
    for (size_t i = 0; i < n; i++) out[i] = in[i] * g;
}

// pan: the AudioParam's value (a float, clamped to [-1, 1] as Chromium does). mono: the input has one channel.
struct PanGains { double l = 1, r = 0; };
inline PanGains panGains(float pan, bool mono, bool floatAdd) {
    const double PI2 = 1.5707963267948966;   // kPiOverTwoDouble
    float p = pan < -1.f ? -1.f : pan > 1.f ? 1.f : pan;
    // stereo left of centre: the fixed-value path adds pan + 1 in float, then widens; the sample-accurate path adds in
    // double. At -0.2 that is 0.800000012 against 0.799999997 and changes the last bit of every left sample (run_mix.py)
    double rad = mono ? ((double)p * 0.5 + 0.5) * PI2 : (p <= 0 ? (floatAdd ? (double)(float)(p + 1.f) : (double)p + 1) * PI2 : (double)p * PI2);
    return { std::cos(rad), std::sin(rad) };
}
// Chromium has two paths, and which one runs decides the last bit:
//  - sample-accurate (PanWithSampleAccurateValues): the gains and the products in double, stored as float. It runs
//    for a render quantum that holds an event on the pan's timeline. Setting pan.value adds such an event at the
//    time it is set, so in an export it is the first quantum.
//  - fixed value (PanToTargetValue): the gains stored as float, products and sums in float. Every later quantum.
// Found by comparing with the app's own render (tools/native-lab/run_mix.py): with the float path everywhere,
// every sample that differed was in the first 512 frames, and the double path matched all of them.
inline void panFixed(float pan, const float* inL, const float* inR, bool mono, float* outL, float* outR, size_t n, bool sampleAccurate = false) {
    PanGains g = panGains(pan, mono, !sampleAccurate);
    if (sampleAccurate) {
        if (mono) { for (size_t i = 0; i < n; i++) { float x = inL[i]; outL[i] = (float)(x * g.l); outR[i] = (float)(x * g.r); } }
        else if (pan <= 0) { for (size_t i = 0; i < n; i++) { float a = inL[i], b = inR[i]; outL[i] = (float)(a + b * g.l); outR[i] = (float)(b * g.r); } }
        else { for (size_t i = 0; i < n; i++) { float a = inL[i], b = inR[i]; outL[i] = (float)(a * g.l); outR[i] = (float)(b + a * g.r); } }
        return;
    }
    const float gl = (float)g.l, gr = (float)g.r;
    if (mono) { for (size_t i = 0; i < n; i++) { float x = inL[i]; outL[i] = x * gl; outR[i] = x * gr; } }
    else if (pan <= 0) { for (size_t i = 0; i < n; i++) { float a = inL[i], b = inR[i]; outL[i] = a + b * gl; outR[i] = b * gr; } }
    else { for (size_t i = 0; i < n; i++) { float a = inL[i], b = inR[i]; outL[i] = a * gl; outR[i] = b + a * gr; } }
}
inline void addInto(const float* in, float* acc, size_t n) { for (size_t i = 0; i < n; i++) acc[i] += in[i]; }

}  // namespace al
