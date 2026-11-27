# Engine sound quality: what AudioLab does today and what to improve (task AE1)

Research task, 27 November 2026, AudioLab v0.263. This is the sound-quality part of the user's engine questions (20:02 Brussels: "Ask me some more questions about the audio engine. Maybe we can improve some more things and do some research"). The sibling tasks are AE2 (performance and playing latency), mixing workflow, and built-in sounds. Nothing in `index.html`, `desktop/` or `native/` was changed.

- Pick page: **AudioLab sound quality: what to improve**, https://claude.ai/artifact/EveKcsa3xrtaedKUCShSqW. It has live A/B tests and the measured plots, and gives one line to paste: `AE1 picks: Q0a? Q0b? Q1? … Q16?`.
- Scripts, all re-runnable: `tools/engine-lab/ae1/`. The page is built from the same `dsp.js` that the measurements used.

## Summary

The user listens on revealing gear (iFi Gryphon DAC, Stax electrostatics) and makes psytrance and EDM. Every number below comes from one of two sources:
- the app's own offline render (the AudioLab bridge, 48 kHz);
- a port of the app's code. Each port was checked against the app and gives the same number to 0.1 dB.

**The biggest findings, in the order a psytrance producer would hear them:**

1. **Built-in samples, bounces and stem-splitter results play through linear interpolation.**
   - These buffers are made at 44.1 kHz. In a 48 kHz engine, Chromium's AudioBufferSourceNode converts them by linear interpolation.
   - Result: false tones at −62 dB next to a 1 kHz partial, −34 dB next to 5 kHz, −20 dB next to 10 kHz and −11 dB next to 15 kHz. These are hats, cymbals and air.
   - The same happens to every audio clip when exporting at a rate other than the engine's, and to every pitched sample (+7 semitones: −36 dB at 5 kHz, −22 dB at 10 kHz).
   - A windowed-sinc conversion, done once when the buffer is loaded, gives −112 to −121 dB.
   - Files the user imports are fine: decodeAudioData already uses a sinc (−74 to −87 dB).
2. **The pooled synth (al-poly) aliases.** It plays the demo's rolling bass, Acid, lead, pads and plucks.
   - Its saw is a 2-point PolyBLEP. Below 16 kHz the aliasing is −55 dB on A1 and −39 dB on A7.
   - Acid's drive (a hard clip, then tanh at 8 to 9 times gain) runs at the engine rate. On A1 to A4 the aliasing below 16 kHz is −52 to −43 dB.
   - Fix: a table BLEP oscillator gives −123 to −142 dB. Acid at 2x with ADAA gives −96 to −104 dB.
   - Psy Bass and Fractal already work this way. The demo does not use them.
3. **The limiter's "true peak" mode lets inter-sample peaks through, and the export "safety limiter" is not a limiter.**
   - al-limit estimates inter-sample peaks with a 4-point cubic, then hard-clips at the sample level. The demo's Climax pushed into it reads **+0.13 dBTP** against a −0.3 dB ceiling, with 19 to 23 overs a second.
   - The export option "Keeps the exported file from clipping" is on by default. It is a DynamicsCompressor. Pushed 6 and 10 dB, the demo came out at **+0.69 and +1.36 dBFS**, so 16 and 24-bit files clip.
4. **The demo kick's attack aliases.** It is a sine from 2.6 kHz driven through tanh at about 8x gain, at the engine rate. In its first 30 ms the error against a 32x render is −20 dB. At 4x it is −60 dB, and the kick is rendered once, so 4x costs nothing during playback.

**What needs no work:**
- **Summing.** A 64-track Float32 mix differs from a Float64 sum by −152 dBFS rms, 136 dB under the mix.
- **The meter.** It is exact BS.1770-5.
- **Dither.** Correct TPDF.
- **The Soft Clipper at 4x.** −72 to −83 dB.
- **Psy Bass, Fractal and Sub.** Already band-limited.

**How old projects stay the same.** Every change that alters the sound goes behind a per-device **Quality: Classic / Clean** switch:
- old projects open in Classic, which is today's exact bits;
- new devices start in Clean.

This follows the rule in `docs/native-mac-picks.md`: the sound never changes without the user's yes, and exports are the reference. The export fixes (Q14, Q15) change only files that clip today.

## How it was measured

| Script | What it does |
|---|---|
| `measure_app.py` | Drives the app through `tools/remake/alab.py`. It builds tiny projects and renders them through `renderMix` at 48 kHz, or runs single devices in an OfflineAudioContext with the app's own `mkFxNode`/`wlLoad`. Output: `results/app.json`. |
| `dsp.js` | Today's algorithms copied from index.html (al-poly saw and filter, Acid drive, kickRender, al-limit, postProc dither, Chromium's linear interpolation), plus the candidates. |
| `lab.js` | Runs both sets on test signals and measures CPU (ns per sample, best of 5, on a 2.1 GHz cloud Xeon). The code is unoptimised JavaScript, so treat the costs as upper bounds and as ratios. |
| `lab_anal.py` | Writes `results/lab.json` and the page's plot data. |
| `build_page.py` | Builds the page. |

**Aliasing metric.** The power of everything that is not a harmonic of the note (±9 bins around each harmonic), against the power of the harmonics. It uses 1 s of signal with a Kaiser window, β 20.
- The analyser's floor is −165 dB (an ideal additive saw).
- A naive saw reads −29 dB at 55 Hz and −13 dB at 1760 Hz.
- Test tones are chosen so that aliases do not land on harmonics (2531 Hz, not 2500 Hz).

**Port checks against the app:**
- The saw reads the same at all nine notes.
- Acid reads the same (−45.3 dB at A1).
- The limiter reads the same (+0.13 dBTP, 19.4 overs/s).
- Linear resampling reads the same at all frequencies.
- The Drive effect's 4x within 0.3 dB.

## Findings

### 1. Anti-aliasing

**Pooled synth oscillators (al-poly, index.html PWL).**
- The saw and square are a 2-point PolyBLEP (`s-=2*x-x*x-1`). The triangle is naive. Sine and wavetable come from tables; the wavetable has 7 mip levels of up to 64 harmonics.
- There is no oversampling. Measured in the app, single saw, filter at 18 kHz:

| Note | A1 | A2 | A3 | A4 | A5 | E6 | A6 | E7 | A7 |
|---|---|---|---|---|---|---|---|---|---|
| Whole band (dB) | −50.0 | −47.0 | −43.9 | −40.9 | −37.8 | −35.9 | −34.5 | −32.6 | −31.2 |
| Below 16 kHz (dB) | −54.9 | −51.9 | −49.0 | −45.7 | −43.0 | −41.5 | −40.6 | −39.5 | −39.0 |
| Table BLEP, below 16 kHz (dB) | −142 | −139 | −135 | −132 | −129 | −126 | −126 | −123 | −123 |

- 2x PolyBLEP (with a 47-tap half-band) gives −70 to −52 dB over the whole band.
- The table BLEP gives −100 to −80 dB over the whole band. What remains is the half-band's transition between 20 and 24 kHz.
- What this does to the sound: on leads and high plucks the aliases are inharmonic tones that do not follow the note. They make a saw sound glassy or "digital", and they beat against the delay and reverb. On the rolling bass at F1 they sit near −55 dB and are hard to hear alone, but they add up under drive.
- How others do it:
  - Ableton Wavetable's raw oscillators are "perfectly band-limited", and Operator has an Antialias mode on by default ([Live 12 instrument reference](https://www.ableton.com/en/live-manual/12/live-instrument-reference/)).
  - u-he Repro band-limits its edges with a linear-phase method ([Urs Heckmann, KVR](https://www.kvraudio.com/forum/viewtopic.php?p=6736612)).
  - Integrated B-spline BLEP is alias-free to a 7.8 kHz fundamental at 44.1 kHz ([Välimäki, Pekonen, Nam 2012](https://mac.kaist.ac.kr/pubs/ValimakiPeknenNam-jasa2012.pdf)).
- Cost:
  - The BLEP's work is per edge, not per sample: the same as today at 110 Hz (10.5 ns per sample), and 2.4x at 3 kHz.
  - A whole voice: about 5 to 25 % more (**estimate**, not measured with unison).
  - Latency: the linear-phase BLEP needs 16 samples (0.33 ms) inside the voice. A minimum-phase BLEP needs none.

**Acid's drive (al-poly, `dg`).**
- The code is `tanh(clamp(y)*dg)*dn` with dg = 1 + round(dist/10)/10·12, which is 8.2 at the default 55 %. It runs at 1x.
- Measured in the app, below 16 kHz: −51.8, −48.8, −44.7, −42.6 dB at A1, A2, A3, A4.
- 2x with first-order ADAA: −104.4, −101.5, −98.5, −95.8 dB.
- ADAA alone at 1x gains about 10 dB. 2x alone gains about 15 dB. Both together gain about 50 dB below 16 kHz.
- What remains above 16 kHz is the half-band's transition band, not audible.
- ADAA: [Parker, Zavalishin, Le Bivic, DAFx-16](https://dafx.de/paper-archive/2016/dafxpapers/20-DAFx-16_paper_41-PN.pdf). Practical notes: [Chowdhury](https://ccrma.stanford.edu/~jatin/Notebooks/adaa.html). ADAA delays by half a sample and needs a fallback for tiny steps.
- Cost: 73 → 211 ns per sample per voice (2.9x), which is 0.35 % → 1.0 % of one build-machine core per voice.
- The sound: the squelch keeps its bite, but the fizz and the whistle on resonant sweeps go away.

**The kick designer (kickRender).**
- The demo kick: psyzap, tune 29 (F1), start 2.6 kHz, drive 45, so tanh gain 7.3.
- The tanh runs on the buffer at the engine rate.
- First 30 ms against a 32x render: −19.9 dB at 1x, −51.0 dB at 2x, −59.5 dB at 4x, −67.0 dB at 8x.
- The buffer is rendered once and cached, so the cost is only at render time: 1.3 → 11.5 ms per kick sound.
- The same applies to percussion pads (pzDrive) and Growl (grwRender, tanh and fold at 1x).

**The Drive effect.**
- It is a WaveShaperNode at 4x with the curve (1+k)x/(1+k|x|), k = 1.5·drive, 2048 points, and input clamped to ±1.
- Chromium's 4x is two 2x stages of Blackman-windowed sinc: 128-tap up, 256-tap half-band down ([UpSampler](https://chromium.googlesource.com/chromium/blink/+/main/Source/platform/audio/UpSampler.cpp), [DownSampler](https://chromium.googlesource.com/chromium/blink/+/main/Source/platform/audio/DownSampler.cpp)).
- At drive 60 % the knee is sharp, so harmonics fall slowly and fold from above 96 kHz. Measured in the app:

| Input | Aliasing today (app) |
|---|---|
| 2.5 kHz at −6 dBFS | −39.8 dB |
| 4 kHz at −6 dBFS | −34.4 dB |
| 5 kHz at +3 dBFS, drive 100 % | −26.2 dB |
| 1 kHz, drive 30 % | −63.6 dB (fine) |

- 4x plus ADAA in the lab gives −56 dB at 2.5 and 4 kHz. 8x alone gives −52 and −46 dB.
- Input above 0 dBFS hits the end of the curve, which is a hard clip. Neither change fixes that. Extending the curve beyond ±1, as the Soft Clipper already does (input scaled by 1/4), would (**estimate**).

**Shapers with no oversampling.**
- These have none: the Timeless delay's tanh in its feedback, the Auto Filter's drive, the Grid's crush (drive and fold already use 2x), the tom kit, Acid's main-thread fallback, and the live master safety limiter.
- The Soft Clipper shows what oversampling is worth (2.5 kHz, tanh, +12 dB):

| Oversampling | Aliasing |
|---|---|
| none | −40.3 dB |
| 2x | −66.3 dB |
| 4x | −82.7 dB |

**Others, published:**
- Ableton: Saturator, Pedal and Dynamic Tube have Hi-Quality modes; Glue and EQ Eight oversample 2x ([effect reference](https://www.ableton.com/en/live-manual/12/live-audio-effect-reference/)).
- Bitwig's Grid runs at 4x ([user guide](https://www.bitwig.com/userguide/bws44-504/on_grid_signals)).
- FabFilter Saturn 2: 8x (Good) and 32x (Superb) ([help](https://fabfilter.com/help/saturn/using/inputoutput)).
- u-he: Repro-1's filter is 8x at 44.1/48 kHz, minimum-phase so latency-free; Satin runs inside at 352 to 384 kHz ([KVR](https://www.kvraudio.com/forum/viewtopic.php?p=8846893)).
- Vital: "1x to 2x will be the biggest changes" ([forum](https://forum.vital.audio/t/getting-best-audio-quality-from-vital/5852)).
- Choosing the oversampling filters: [Kahles, Esqueda, Välimäki, JAES 2019](https://acris.aalto.fi/ws/portalfiles/portal/34665796/ELEC_Kahles2019_Oversampling_JAES.pdf).
- Not found: Kilohearts and Serum 2 publish no factors.

### 2. Filters

**al-poly's low-pass.**
- It is an RBJ cookbook biquad (transposed direct form II), with Q in dB (G = 10^(q/20)).
- Its coefficients are recomputed every 16 samples with no interpolation. The cut-off is clamped to [20, 0.49·sr].
- At a fixed cut-off a TPT/ZDF state-variable filter has the same response (both are bilinear with prewarping; [Zavalishin §3.11](https://www.native-instruments.com/fileadmin/ni_media/downloads/pdf/VAFilterDesign_2.1.0.pdf)). The difference appears under modulation:
  - fast acid envelope, 9 kHz → 300 Hz in 40 ms at 21 dB resonance: RBJ every 16 samples against SVF every sample differ by −38.6 dB;
  - RBJ every sample against SVF: −43.3 dB, so most of the difference is the topology, not the 16-sample steps;
  - cut-off swept at 300 Hz: −7.7 dB, but al-poly's LFO is control-rate, so this cannot happen today.
- The verdict is a small character difference, not a fault. Cost: 7 → 20 ns per sample per stage.
- Psy Bass, Sub and the FM synths (al-vfm, al-orb) already use ZDF SVFs with tan prewarping.

**Pro EQ near the top.**
- The bells and shelves are BiquadFilterNodes, RBJ formulas, with Chromium's double-precision coefficients and state ([Biquad.cpp](https://chromium.googlesource.com/chromium/blink/+/main/Source/platform/audio/Biquad.cpp)). The bilinear transform squeezes them towards Nyquist.
- Measured (the digital response minus the analog prototype):

| Bell | at 15 kHz | at 18 kHz | at 20 kHz |
|---|---|---|---|
| 12 kHz, +6 dB, Q 1, 48 kHz | −1.41 dB | −2.28 dB | −2.32 dB |
| 12 kHz, +6 dB, Q 1, 44.1 kHz | −1.81 dB | −2.70 dB | −2.62 dB |
| 16 kHz, +6 dB, Q 1, 48 kHz | | | −3.35 dB |

- On Stax, an "air" boost sounds narrower and duller than the curve drawn.
- FabFilter Pro-Q 4's zero-latency mode follows the analog curve "except for a small deviation above 18 kHz" ([help](https://prod.fabfilter.com/help/pro-q/using/processingmode)).
- The usual fix is matched second-order design (M. Vicanek, "Matched Second Order Digital Filters", 2016; known from the literature, not fetched for this task) or computing the bell at 2x. Neither adds latency.
- BiquadFilterNode does not take coefficients, so this needs a worklet or an IIRFilterNode. An IIRFilterNode cannot be automated.

**Pro EQ slopes.**
- The 24 and 48 dB/oct pass filters stack Q 0.707 stages: a Linkwitz-Riley shape.
- At the handle's frequency they read −6.1 and −12.1 dB; a Butterworth reads −3.0 dB.
- An octave below, they read −0.6 and −1.1 dB; a Butterworth reads 0.0 dB.
- It is a legitimate shape, but the handle is not at the −3 dB point. Either use Butterworth Q values or label the handle.

### 3. Summing, DC, denormals

**Summing.** 64 sources at −30 to −12 dBFS go through GainNode, StereoPannerNode and a master gain of −6 dB, rendered by Chromium in Float32:
- mix: −16.2 dBFS rms;
- difference from a Float64 reference of the same graph: **−152.5 dBFS rms, −133.1 dBFS peak**;
- rounding the exact result to Float32 once: −168.1 dBFS.

So the summing loses about 16 dB of float headroom over one rounding, and still sits 14 dB under one 24-bit step (−138.5 dBFS).

How others do it:
- Ableton sums at 64-bit but processes at 32-bit ([audio fact sheet](https://www.ableton.com/en/live-manual/12/audio-fact-sheet/)).
- Cubase has an optional 64-bit engine ([Steinberg](https://www.steinberg.help/r/cubase-9.5-64-bit-double-precision-audio-processing)).
- MeterPlugs computes a worst case of −114 dBFS for 32 tracks and expects no audible difference ([blog](https://www.meterplugs.com/blog/2017/02/03/does-64-bit-summing-sound-better.html)).

The native engine mixes in float to stay bit for bit with the web engine (`native/engine/mix/mix_graph.h`). A 64-bit bus there would change the last bits of every project and gain nothing measurable. **Not recommended.**

**DC.**
- The Soft Clipper puts a 7 Hz high-pass before its shaper and subtracts the curve's static offset. A biased shaper still creates a DC that follows the signal:

| Bias | DC out (110 Hz sine at −4.4 dBFS, +12 dB drive) |
|---|---|
| 0 % | −79.8 dBFS |
| 25 % | −23.8 dBFS |
| 50 % | −17.8 dBFS |

- The result is a slow thump under the envelope. It wastes headroom and makes the limiter work on one side.
- Cubase Distroyer has a separate DC filter for this ([Steinberg](https://archive.steinberg.help/nuendo_plugin_reference/v13/en/_shared/topics/plug_ref/distroyer_r.html)). A 5 Hz one-pole DC blocker ([J. O. Smith](https://ccrma.stanford.edu/~jos/fp/DC_Blocker.html)) costs two multiplies per sample.
- Other DC blockers already exist: Vector Delay (.9975), Fractal (3 Hz), Psy Bass (ZDF low cut), and the output's optional 4 Hz high-pass (live only).

**Denormals.**
- WLSRC's dnGuard zeroes state below 1e-30 every 16 blocks. al-poly and Venom flush their filter states every block.
- The native policy is already decided (`docs/research-native-mac.md`, E3): flush-to-zero off for AudioLab's own devices, so the bits match; on around plug-in calls.
- Nothing new is proposed. One D4 note: offline renders use 512-frame quanta, so the "every 16 blocks" flush happens at different sample times live and offline. That is harmless for the sound and already known.

### 4. Sample-rate conversion

**AudioBufferSourceNode.**
- Chromium interpolates linearly for any rate other than 1. This applies both to a buffer at another rate and to playbackRate ([WebKit source](https://chromium.googlesource.com/external/Webkit/+/master/Source/WebCore/Modules/webaudio/AudioBufferSourceNode.cpp); the spec leaves the method open).
- Measured in the app:

| Case | 1 kHz | 5 kHz | 10 kHz | 15 kHz |
|---|---|---|---|---|
| 44.1 kHz buffer in a 48 kHz render | −62.4 dB | −33.9 dB | −20.4 dB | −11.1 dB |
| playbackRate +7 semitones | −63.9 dB | −35.5 dB | −22.2 dB | |

- A 32-zero-crossing Kaiser sinc (β 10) gives −112 to −121 dB.

**Where it happens today** (from the code; `sampleBuf`, `bounceRender`, `neuTo44`, `renderMix`):
- The built-in sampler and drum sounds are synthesised at 44.1 kHz.
- Bounce-in-place renders at a fixed 44.1 kHz.
- The stem splitter's results are 44.1 kHz.
- Every audio clip is affected when the export rate differs from the engine rate. Buffers are decoded at the live context's rate; renderMix renders at the export rate.
- The Sampler and drum pads pitch by playbackRate. The grain, emit and vgrain worklets read with linear interpolation too.

At 48 kHz the images fall in the audible band. At 96 kHz most fall above 22 kHz (**reasoning, not measured**).

**decodeAudioData** resamples imported files to the context rate with Chromium's sinc resampler. Measured: −86.7 dB at 5 kHz and −74.0 dB at 15 kHz, which is fine.

The only real resampler in the app today is the Voice AI's (Kaiser sinc, 16 zero crossings).

How others do it:
- Ableton exports through the SoX resampler; its Hi-Q clip interpolation is clean to about ±19 semitones ([fact sheet](https://www.ableton.com/en/live-manual/12/audio-fact-sheet/)).
- REAPER offers r8brain ([r8brain-free-src](https://github.com/avaneev/r8brain-free-src/)).

Cost: zero during playback if each buffer is converted once in a worker. In this unoptimised lab code it takes 334 ns per sample, about 8 s for a 4-minute stereo file. An optimised worker would take an **estimated** 1 to 2 s.

### 5. True peak, export, dither

**al-limit** (WLSRC `Lim`).
- Defaults: ceiling −0.3 dB, gain +3 dB, look-ahead 3 ms, release 150 ms, style transparent, `tp` on.
- How it works:
  - It takes the sample peak, plus (with `tp`) a 4-point cubic estimate at three positions between samples.
  - The gain is the running minimum over the look-ahead, smoothed by a boxcar, then released by two one-poles.
  - The output is **hard-clipped at the ceiling at the sample level**.
- The demo's Climax (bars 146 to 161), normalised to −1 dBFS, pushed through it:

| Push | Mode | Sample peak | True peak | Overs above the ceiling |
|---|---|---|---|---|
| +6 dB | tp on | −0.30 dBFS | +0.13 dBTP | 19.4/s |
| +6 dB | tp off | −0.30 dBFS | +0.54 dBTP | 23.6/s |
| +10 dB | Aggressive | −0.30 dBFS | +0.25 dBTP | 48.3/s |

- Candidate 1: detect with the meter's own BS.1770-5 filter (48 taps, 4 phases): −0.19 dBTP, 2.4 to 2.9 overs/s.
- Candidate 2: candidate 1 plus a 4x oversampled final clip: −0.28/−0.26 dBTP, 0.3 to 0.5 overs/s. It is 0.2 dB less loud (−6.98 → −7.20 dBFS rms).
- Cost: detection 69 → 120 ns per sample; the oversampled clip is about 1 µs naive, an **estimated** 150 ns optimised. Latency +26 samples (0.5 ms), reported to delay compensation.
- Why it matters:
  - A DAC's reconstruction filter and every lossy encode see the peaks between samples. MP3 at 320 kbps adds about +1.7 dB and at 160 kbps about +2.3 dB ([Nielsen and Lund 2003](https://cdn.mediavalet.com/aunsw/musictribe/2_NUqQYNUUWwJY6ZM2wn8w/RQNWR1o9v0S7uLbTbCNagg/Original/nielsen_lund_2003_overload.pdf)).
  - 61 % of electronica tracks in a 107k-track scan exceed 0 dBTP ([Archimago 2025](https://archimago.blogspot.com/2025/08/a-look-at-music-library-how-much.html)).
- What the standards and others say:
  - [BS.1770-5 Annex 2](https://www.itu.int/dms_pubrec/itu-r/rec/bs/R-REC-BS.1770-5-202311-I!!PDF-E.pdf): 4x can under-read by up to 0.69 dB at the band edge.
  - EBU R128 asks for −1 dBTP ([Tech 3343](https://tech.ebu.ch/docs/tech/tech3343.pdf)).
  - FabFilter Pro-L 2's true-peak mode, at 4x with at least 0.1 ms of look-ahead, stays within 0.1 dB ([help](https://www.fabfilter.com/help/pro-l/using/truepeaklimiting)).

**Export "safety limiter"** (`#exLim`, on by default).
- It is `DynamicsCompressor(threshold −1, knee 0, ratio 20, attack 1 ms, release 80 ms)`.
- Pushed +6 and +10 dB, the demo came out at **+0.69 and +1.36 dBFS sample peak** (+0.88 and +1.43 dBTP).
- `toInt` then clamps, so the 16 and 24-bit file is hard-clipped exactly where the option promises it will not be. It only bites when the master is hot and has no limiter of its own; with al-limit on the master it does nothing.

**Dither** (postProc).
- TPDF ±1 LSB from a seeded sfc32 (`dither|seed|bits`). 'ns' is first-order error feedback, reset per channel.
- Measured on a −90 dBFS tone at 16 bits:

| Mode | Total | Noise 1 to 5 kHz | Noise 15 to 20 kHz | Harmonics of the tone |
|---|---|---|---|---|
| off | | | | −10.7 dB (truncation distortion) |
| TPDF | −96.3 dBFS | −143 dB/bin | −143 dB/bin | none (only noise in those bins) |
| ns (first order) | | −151 dB/bin | −138 dB/bin | |
| 9-tap F-weighted, Wannamaker 1992 (candidate) | −77.9 dBFS | −162 dB/bin | −127 dB/bin | |

- So the implementation is right ([Lipshitz, Wannamaker, Vanderkooy 1992](https://hajim.rochester.edu/ece/sites/zduan/teaching/ece472/reading/Lipshitz_1992.pdf)).
- At 24 bits (the default export) TPDF noise is about −141 dBFS, below any DAC, so shaping only matters for 16-bit files.
- The 9 coefficients are the commonly quoted Wannamaker set. They are quoted from memory of the literature, not fetched; check them before shipping.

## Options (the pick page's Q numbers)

| Q | Option | ★ | Measured gain | Old projects | Engine |
|---|---|---|---|---|---|
| Q0a | Quality switch per device (Classic = today's bits, Clean); old projects Classic, new devices Clean | 5 | — | unchanged | web + native |
| Q0b | One project-wide quality instead | 3 | — | unchanged | web + native |
| Q1 | Table-BLEP oscillators in al-poly (and BLAMP triangle) | 5 | −43 → −129 dB (A5, <16 kHz) | Quality switch | web + native |
| Q2 | Acid at 2x + ADAA drive | 5 | −49 → −102 dB (A2, <16 kHz) | Quality switch | web + native |
| Q3 | Kick, pads, Growl rendered at 4x | 4 | −20 → −60 dB (attack) | Quality switch | web + native |
| Q4 | Drive effect: ADAA on 4x, curve beyond ±1 | 3 | −34 → −56 dB (4 kHz) | Quality switch | web + native |
| Q5 | Oversample the remaining shapers | 3 | −40 → −83 dB (Soft Clipper analogue) | Quality switch | web + native |
| Q6 | ZDF SVF in al-poly | 2 | character, −39 dB difference | Quality switch | web + native |
| Q7 | Pro EQ analog-matched top end | 3 | 2.3 dB → about 0 at 18 kHz | per band or device | web + native |
| Q8 | Pro EQ Butterworth slopes or a label | 1 | −6 dB → −3 dB at the handle | switch or label | web + native |
| Q9 | 64-bit summing | 0 | −152 dBFS today; nothing audible | would change bits | native |
| Q10 | DC blocker after biased shapers | 3 | −24 → under −90 dBFS DC | Quality switch | web + native |
| Q11 | Resample buffers once with a sinc (built-in sounds, bounces, stems, export rate) | 5 | −20 → −117 dB (10 kHz) | project-wide Classic/Clean | web + native |
| Q12 | Sinc (or cubic) read for pitched samples | 4 | −22 → −113 dB (+7 st, 10 kHz) | Quality switch | web + native |
| Q13 | True-peak limiter style: BS.1770 detection + 4x clip | 5 | +0.13 → −0.28 dBTP | new style; old kept | web + native |
| Q14 | Export safety limiter → Q13 at −1 dBTP | 5 | +1.36 dBFS → ≤ −1 dBTP | only clipping exports change | web + native |
| Q15 | Export report: true peak, overs, clipped samples | 4 | — | none | web + native |
| Q16 | 9-tap shaped dither for 16-bit | 2 | −143 → −162 dB/bin at 1 to 5 kHz | new menu choice | web + native |

★ 4–5 are recommended now; ★ 3 later; ★ 0–2 not now.

## Proposed tasks

None of these fits the nine UI lanes in `CLAUDE.md`: the DSP inside the worklets (al-poly, al-limit, kickRender, postProc, the resampler) has no owner in the lane table. The proposal is a new **engine lane "SQ" (prefix `sq`)**, one task at a time, with the native port following through task NB as each device is ported.

| Task | Scope | Size | Lane / engine |
|---|---|---|---|
| SQ1 | The Quality switch (Q0a): the field `q:'classic'\|'clean'` on instruments and effects, Classic for loaded projects and Clean for new devices, project-wide "Use Clean everywhere" with undo, render hashes of the three demos unchanged in Classic. Includes Q10 (DC blocker) as the first Clean feature. | like an NB-R task | SQ; UI bits by lane I (device frame: a small Quality chip) through a hook |
| SQ2 | al-poly Clean: table BLEP saw/square, BLAMP triangle (Q1), Acid 2x + ADAA (Q2). Tests: this task's aliasing script at 9 notes, CPU per voice, Classic bit-identical. | 1 task | SQ, then NB port |
| SQ3 | Resample once (Q11): a sinc resampler in a worker; sampleBuf, bounce, stem results and export-rate buffers converted and cached per rate; project-wide Classic/Clean. | 1 task | SQ; NB resamples on load the same way |
| SQ4 | Limiter "True peak 4x" style (Q13) with the meter's TPH filter, the export safety limiter replaced (Q14), the export report (Q15). | 1 task | SQ + lane E (shares the meter filter) + lane F (the notice) |
| SQ5 | Kick, pads, Growl at 4x (Q3); Drive ADAA and the extended curve (Q4); remaining shapers oversampled (Q5). | 1 task | SQ |
| SQ6 | Later: pitched-sample interpolation (Q12), Pro EQ matched top (Q7), shaped dither (Q16), ZDF filter in al-poly (Q6). | 1 to 2 tasks | SQ + lane E (EQ drawing) + lane B (dither menu) |

Every SQ task keeps the release-gate rules in `CLAUDE.md`, and keeps the Fractals/Shrine Legion Classic hashes unchanged as its proof.

## Side findings (outside sound quality, for other tasks)

- **Device parameter automation seems not to be rendered in exports.** `S.pauto` is applied by `paApply` from the main thread every 33 ms while playing. A search found no use of it in `renderMix`/`renderMixChunked`. This was found from the code, not confirmed with a render. If it holds, an export differs from what plays. Owner: lane C (features), or whoever owns renderMix.
- The live master safety limiter (a WaveShaper with a tanh knee, no oversampling) is not in the export path, so live and export differ above its knee. That is by design, but worth a line in the help text.

## Open points and guesses

- CPU numbers come from unoptimised JavaScript on a 2.1 GHz Xeon. The production costs marked "estimate" are guesses from the operation count. The M4 is estimated two to three times faster per core.
- Q12's cubic figure (−50 to −60 dB) is a guess and was not measured.
- Q4's gain from extending the curve is a guess.
- The Vicanek matched-filter reference and the Wannamaker coefficients come from memory of the literature and were not fetched in this task.
- Infinite Wave's SRC comparison site is geo-blocked from the research machine, so no per-DAW SRC plots were read.
- The images at 96 kHz were reasoned, not measured.

## Sources

- Anti-aliasing:
  - [DAFx-16 ADAA](https://dafx.de/paper-archive/2016/dafxpapers/20-DAFx-16_paper_41-PN.pdf)
  - [Chowdhury ADAA](https://ccrma.stanford.edu/~jatin/Notebooks/adaa.html)
  - [Kahles et al. 2019](https://acris.aalto.fi/ws/portalfiles/portal/34665796/ELEC_Kahles2019_Oversampling_JAES.pdf)
  - [Välimäki et al. 2012](https://mac.kaist.ac.kr/pubs/ValimakiPeknenNam-jasa2012.pdf)
  - [Chromium UpSampler](https://chromium.googlesource.com/chromium/blink/+/main/Source/platform/audio/UpSampler.cpp)
  - [Chromium DownSampler](https://chromium.googlesource.com/chromium/blink/+/main/Source/platform/audio/DownSampler.cpp)
  - [Chromium PeriodicWave](https://chromium.googlesource.com/chromium/blink/+/HEAD/Source/modules/webaudio/PeriodicWave.cpp)
- Filters:
  - [Zavalishin, The Art of VA Filter Design 2.1.0](https://www.native-instruments.com/fileadmin/ni_media/downloads/pdf/VAFilterDesign_2.1.0.pdf)
  - [RBJ cookbook](https://webaudio.github.io/Audio-EQ-Cookbook/audio-eq-cookbook.html)
  - [Cytomic SVF thread](https://www.kvraudio.com/forum/viewtopic.php?p=8830096)
  - [Pro-Q 4 processing modes](https://prod.fabfilter.com/help/pro-q/using/processingmode)
  - [Chromium Biquad](https://chromium.googlesource.com/chromium/blink/+/main/Source/platform/audio/Biquad.cpp)
- Summing:
  - [Ableton fact sheet](https://www.ableton.com/en/live-manual/12/audio-fact-sheet/)
  - [Steinberg 64-bit](https://www.steinberg.help/r/cubase-9.5-64-bit-double-precision-audio-processing)
  - [REAPER about](https://www.reaper.fm/about.php)
  - [MeterPlugs](https://www.meterplugs.com/blog/2017/02/03/does-64-bit-summing-sound-better.html)
- Resampling:
  - [WebKit AudioBufferSourceNode](https://chromium.googlesource.com/external/Webkit/+/master/Source/WebCore/Modules/webaudio/AudioBufferSourceNode.cpp)
  - [Blink SincResampler](https://chromium.googlesource.com/chromium/blink/+/main/Source/platform/audio/SincResampler.cpp)
  - [r8brain-free-src](https://github.com/avaneev/r8brain-free-src/)
  - [SRC comparison FAQ](https://megapro17.github.io/src/faq.html)
  - [Web Audio spec](https://www.w3.org/TR/WebAudio/)
- True peak and dither:
  - [BS.1770-5](https://www.itu.int/dms_pubrec/itu-r/rec/bs/R-REC-BS.1770-5-202311-I!!PDF-E.pdf)
  - [EBU Tech 3343](https://tech.ebu.ch/docs/tech/tech3343.pdf)
  - [Pro-L 2 true peak](https://www.fabfilter.com/help/pro-l/using/truepeaklimiting)
  - [Ozone 9 Maximizer](https://downloads.izotope.com/docs/ozone9/en/maximizer/index.html)
  - [Archimago 2025](https://archimago.blogspot.com/2025/08/a-look-at-music-library-how-much.html)
  - [Nielsen and Lund 2003](https://cdn.mediavalet.com/aunsw/musictribe/2_NUqQYNUUWwJY6ZM2wn8w/RQNWR1o9v0S7uLbTbCNagg/Original/nielsen_lund_2003_overload.pdf)
  - [Lipshitz et al. 1992](https://hajim.rochester.edu/ece/sites/zduan/teaching/ece472/reading/Lipshitz_1992.pdf)
  - [Logic dither](https://support.apple.com/en-kz/guide/logicpro/about-dithering-algorithms-lgcp44da971f/10.7/mac)
  - [Apple Digital Masters](https://apple.com/itunes/docs/apple-digital-masters.pdf)
- Devices and DC:
  - [Ableton effects](https://www.ableton.com/en/live-manual/12/live-audio-effect-reference/)
  - [Ableton instruments](https://www.ableton.com/en/live-manual/12/live-instrument-reference/)
  - [Bitwig Grid](https://www.bitwig.com/userguide/bws44-504/on_grid_signals)
  - [Distroyer](https://archive.steinberg.help/nuendo_plugin_reference/v13/en/_shared/topics/plug_ref/distroyer_r.html)
  - [Saturn 2](https://fabfilter.com/help/saturn/using/inputoutput)
  - [Pro-L 2 oversampling](https://www.fabfilter.com/help/pro-l/using/oversampling)
  - [Urs Heckmann on Repro-1](https://www.kvraudio.com/forum/viewtopic.php?p=6736612)
  - [Urs Heckmann on Satin](https://www.kvraudio.com/forum/viewtopic.php?p=8846893)
  - [Vital forum](https://forum.vital.audio/t/getting-best-audio-quality-from-vital/5852)
  - [J. O. Smith DC blocker](https://ccrma.stanford.edu/~jos/fp/DC_Blocker.html)
- AudioLab:
  - `docs/native-mac-plan.md`, `docs/native-mac-picks.md` (sound changes need the user's yes; exports are the reference)
  - `docs/review-native.md` (D2 one random stream per device, D4 the block grid)
  - `docs/research-native-mac.md` (denormals, FMA)
  - `native/engine/mix/mix_graph.h` (float mixing for the bit match)

## The user's picks (27 November 2026, 21:48 Brussels)

`AE1 picks: Q0aa Q0ba Q1a Q2a Q3a Q4a Q5a Q6a Q7a Q8a Q9b Q10a Q11a Q12a Q13a Q14a Q15a Q16b` (the last letter: a = now, b = later)

- **Now:** Q0a a Quality switch per device (Classic = today's bits, Clean) AND Q0b one project-wide quality as well (both: the project setting is the default and "Use Clean everywhere", each device can still differ); Q1 table-BLEP oscillators and BLAMP triangle in al-poly; Q2 Acid at 2x with ADAA drive; Q3 Kick, pads and Growl at 4x; Q4 Drive ADAA and the curve beyond ±1; Q5 the remaining shapers oversampled; Q6 ZDF SVF in al-poly; Q7 Pro EQ analog-matched top end; Q8 Pro EQ Butterworth slopes or a label; Q10 DC blocker; Q11 resample buffers once with a sinc; Q12 sinc read for pitched samples; Q13 true-peak limiter style; Q14 the export safety limiter at -1 dBTP; Q15 the export report.
- **Later:** Q9 64-bit summing (native engine), Q16 shaped dither for 16-bit.

Who builds it: a new lane N, task **SQ** (sound quality infrastructure, prefix `sq`): SQ1 the Quality switch per device and per project (with Q10 as its first Clean feature); SQ3 resample once (Q11) and SQ3b the pitched-sample read (Q12); SQ4 the true-peak limiter style (Q13), the export safety limiter (Q14) and the export report (Q15). The device DSP items go to lane L (SND), which owns those worklets and already improves the same devices: Q1, Q2 and Q6 (al-poly and Acid, with SND-7 and SND-12), Q3 (Kick, pads, Growl, with SND-8 and the Growl fold-in), Q4 and Q5 (Drive and shapers, with SND-16), Q7 and Q8 (Pro EQ, with SND-4). SND's "v2 modes" ARE the Clean quality: one switch, defined by SQ1. Q9 goes to task NB, Q16 waits.

Side finding to fix first: device parameter automation (`S.pauto`) seems not to be rendered in exports. Lane K (MX, owner of renderMix) verifies it with a render and fixes it so an export equals what plays.

## The switch's name (the user, 27 Nov 2026, 23:00 Brussels): one switch, "Hi-Fi"

The user asked for one on/off switch instead of two named modes ("a switch that says Hi-Fi, you switch it on, but there is no Classic mode, it's just on or off"). Decided: **one switch labelled "Hi-Fi"**, per device and per project. The internal field stays `q:'classic'|'clean'` (off = classic, on = clean), so no stored data changes; only the labels in the interface say Hi-Fi on or off.
- **Off**: the device sounds exactly as the song was made, and it is the lighter setting.
- **On (Hi-Fi)**: cleaner (oversampling, band-limited oscillators, better filters, fewer harsh digital artefacts) and costs more processing on the parts it changes (measured in this research: about 2 to 3 times on those parts, for example Acid's drive 73 to 211 ns per sample per voice, a ZDF filter stage 7 to 20 ns, band-limited oscillators the same at low notes and 2.4 times at 3 kHz; resampling costs nothing while playing because it is done once when a sample loads).
- Loaded projects open with Hi-Fi off (unchanged sound); new devices start with Hi-Fi on; the project has "Hi-Fi everywhere" with one undo step. Tooltip: "Hi-Fi: cleaner sound, uses more processing. Off: lighter, and exactly as the song was made."
- Not "Lossless": that word means lossless compression (like FLAC) and would promise something else.
