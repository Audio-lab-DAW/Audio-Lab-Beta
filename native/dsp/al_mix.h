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

// Which web engine the mixer matches (task NB-N3d found it, task NB-N3e traced it to the source).
// Chromium is built with -ffp-contract=off on every platform (build/config/compiler/BUILD.gn at 158.0.8127.36, the
// is_clang block: "-ffp-contract=off"), so its own C++ never fuses. What fuses on the Mac is Accelerate: the panner's
// fixed-value path calls vector_math::Vsma, which on the Mac is vDSP_vsma (vector_math_mac.h), one rounding on Apple
// Silicon; on Linux and Windows it is a multiply then an add. So: AL_WEB_PAN_FUSED (the fixed path's Vsma) defaults
// to 1 on the Mac, 0 elsewhere, and on the Mac the engine calls vDSP_vsma itself. The sample-accurate path is plain C++
// in Chromium (not fused); AL_WEB_PAN_SA_FUSED=1 fuses it anyway, kept as a switch in case the Mac's own references
// ever show a difference in the first render quantum. Either can be set with -D to compare against another machine.
#ifndef AL_WEB_PAN_FUSED
#if defined(__APPLE__)
#define AL_WEB_PAN_FUSED 1
#else
#define AL_WEB_PAN_FUSED 0
#endif
#endif
#ifndef AL_WEB_PAN_SA_FUSED
#define AL_WEB_PAN_SA_FUSED 0
#endif
#include "../third_party/fdlibm/ieee754.h"   // the pan gains: fdlibm::cos and sin, as stereo_panner.cc (task NB-N3e)
#if defined(__APPLE__)
#include <Accelerate/Accelerate.h>
#endif

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
    return { fdlibm::cos(rad), fdlibm::sin(rad) };
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
#if AL_WEB_PAN_SA_FUSED
        else if (pan <= 0) { for (size_t i = 0; i < n; i++) { float a = inL[i], b = inR[i]; outL[i] = (float)std::fma((double)b, g.l, (double)a); outR[i] = (float)(b * g.r); } }
        else { for (size_t i = 0; i < n; i++) { float a = inL[i], b = inR[i]; outL[i] = (float)(a * g.l); outR[i] = (float)std::fma((double)a, g.r, (double)b); } }
#else
        else if (pan <= 0) { for (size_t i = 0; i < n; i++) { float a = inL[i], b = inR[i]; outL[i] = (float)(a + b * g.l); outR[i] = (float)(b * g.r); } }
        else { for (size_t i = 0; i < n; i++) { float a = inL[i], b = inR[i]; outL[i] = (float)(a * g.l); outR[i] = (float)(b + a * g.r); } }
#endif
        return;
    }
    const float gl = (float)g.l, gr = (float)g.r;
    if (mono) { for (size_t i = 0; i < n; i++) { float x = inL[i]; outL[i] = x * gl; outR[i] = x * gr; } }
#if AL_WEB_PAN_FUSED
    // PanToTargetValue: a copy, then Vsma (dest += src * gain) and Vsmul. On the Mac Vsma is vDSP_vsma (one rounding);
    // the Mac's own web engine showed it (native-ci run 46056395016: every bus scene differed from the second render
    // quantum on, at about -138 dB, and only there).
#if defined(__APPLE__)
    else if (pan <= 0) { if (outL != inL) for (size_t i = 0; i < n; i++) outL[i] = inL[i]; vDSP_vsma(inR, 1, &gl, outL, 1, outL, 1, (vDSP_Length)n); for (size_t i = 0; i < n; i++) outR[i] = inR[i] * gr; }
    else { if (outR != inR) for (size_t i = 0; i < n; i++) outR[i] = inR[i]; vDSP_vsma(inL, 1, &gr, outR, 1, outR, 1, (vDSP_Length)n); for (size_t i = 0; i < n; i++) outL[i] = inL[i] * gl; }
#else
    else if (pan <= 0) { for (size_t i = 0; i < n; i++) { float a = inL[i], b = inR[i]; outL[i] = std::fmaf(b, gl, a); outR[i] = b * gr; } }
    else { for (size_t i = 0; i < n; i++) { float a = inL[i], b = inR[i]; outL[i] = a * gl; outR[i] = std::fmaf(a, gr, b); } }
#endif
#else
    else if (pan <= 0) { for (size_t i = 0; i < n; i++) { float a = inL[i], b = inR[i]; outL[i] = a + b * gl; outR[i] = b * gr; } }
    else { for (size_t i = 0; i < n; i++) { float a = inL[i], b = inR[i]; outL[i] = a * gl; outR[i] = b + a * gr; } }
#endif
}
inline void addInto(const float* in, float* acc, size_t n) { for (size_t i = 0; i < n; i++) acc[i] += in[i]; }

}  // namespace al
