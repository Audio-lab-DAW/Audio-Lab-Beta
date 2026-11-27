# AudioLab built-in sounds: what to improve and add (task AE4, 27 November 2026)

**Pick page:** https://claude.ai/artifact/FvHhoQUsfCPEayHp5uwabg (title "AudioLab built-in sounds: what to improve and add"). One card per device with its grade today and numbered improvements **B1 to B37**, six new devices **N1 to N6**, A/B demos (today = rendered by the app, prototype = computed in the page on the same notes), CPU cost, what happens to old projects, stars, and a picks bar (`AE4 picks: ...`).

This was a research and pick-page task. Nothing in `index.html`, `desktop/` or `native/` was changed. Files: this document, `tools/engine-lab/ae4/` (`measure.py` and `results.json`: the measurements; `demos.py`: the "today" half of the demos, written to `page/demos/`; `page/pick.html`: the pick page source).

Parallel tasks started from the same request (27 Nov, 20:02 Brussels) and not repeated here: **AE1** sound quality (engine-wide sample rate, resampling, dither, oversampling policy), **AE2** performance (`docs/research-engine-performance.md`), **AE3** mixing (`docs/research-mixing.md`: sidechain routing, delay compensation, gain staging, reference and loudness). AE1's document was not in the repository when this was written. Where a card here touches their ground it says so: the Limiter's true-peak (B30) is checked with AE3, and the sidechain *source menu* for the Compressor is AE3's X1 (task MX-3); Compressor v2 (B26) only provides the detector input and its high-pass filter that X1 plugs into.

## 1. Summary

- **The newest engines are clean.** Psy Bass (2× with a halfband filter, 4-point polyBLEP), Sub (exact harmonics), Venom and Wavetable (mip-mapped tables) and the saw lead have aliasing at C7 between −63 dB and −157 dB below the note. Psy Bass, Sub and Venom are the devices that already stand next to the plug-ins.
- **Four places sound worse than they should, and all four are measurable:**
  1. **Acid**: two biquads in series (not a ladder or diode filter) and distortion without oversampling: aliasing at C7 goes from −48 dB to −30 dB once Distortion is on.
  2. **Pro EQ**: plain RBJ biquads cramp near Nyquist: a +12 dB bell at 16 kHz (Q 1) is +1.8 dB at 8 kHz (analog +4.0) and +3.4 dB at 20 kHz (analog +9.7). The 24 dB cuts are −6 dB at their corner (two Q 0.707 stages).
  3. **Compressor** (and OTT, Multiband, Sidechain punch): the browser's `DynamicsCompressorNode`. At 8:1 with a tone 24 dB over the threshold, the level falls only 3.5 to 4.3 dB against 1:1, where about 21 dB is expected: the browser adds its own make-up gain, so Threshold and Ratio do not do what they say. Knee and look-ahead are fixed, there is no sidechain and no mix.
  4. **Reverbs**: Space reverb and Convolution Reverb are generated noise impulse responses. The tail is clean (noise-flat, no metallic ring, fully decorrelated) but static: no early reflections, no build-up, no modulation, no freeze or shimmer. There is no algorithmic reverb at all.
- **What psytrance needs most that is missing:** a driven ladder in Psy Bass (B1), a real 303 filter in Acid (B8), drawn and key-snapped kick curves with a click layer (B4, B5), Serum-class unison in Venom (B10), live parameters in the al-poly synths (B15), diffusion in the delay feedback (B34), and new devices: an algorithmic reverb (N1), multiband saturation (N2) and one shared filter set (N5).
- **No silent changes:** every improvement that alters the sound is a `v2` engine mode (old projects stay on v1) or a new device; new controls start at a value that gives today's sound.
- **Both engines:** the native engine (NB) ports devices bit for bit. All DSP changes here should be written once as a small, plain-arithmetic core (no `Math.random` in the audio path without the shared seeded stream, no browser nodes) so NB can port them. The ones that replace browser nodes (Compressor v2, Matched EQ, Hall, Filter v2) make the native port *easier*, because a browser node (DynamicsCompressorNode, BiquadFilterNode, ConvolverNode) has to be reproduced from Chromium's source otherwise.

## 2. How it was measured

`python3 tools/engine-lab/ae4/measure.py index.html [inst|fx|alias|extra]` opens the app headless (the `window.AudioLab` bridge, `tools/remake/alab.py`), builds one-track projects and renders them with the app's own engine at 48 kHz. Measured on v0.263 (the demos were rendered on v0.264; v0.264 changed only the EQ display).

- **Aliasing.** One held note at C7 (2093 Hz), 0.1 to 0.45 s. A note this high has no real partials below its fundamental, so the energy between 40 Hz and 0.45 × f0 (below an octave-down sub too) is folded-back aliasing, plus any noise layer. Reported against the whole sound. A first attempt that counted "energy away from harmonics" was dropped: detune and unison fooled it.
- **Envelope.** One note C2 at beat 1: time to 90 % of the peak, time to fall 40 dB.
- **Stereo.** Correlation of L and R over a chord (or a 16th line for mono instruments).
- **Cost.** Offline render time per second of audio, minus an empty render. Rough; AE2 owns real CPU numbers.
- **Effects.** A 4.5 kHz sine at −3 dBFS into Drive, Soft Clipper and Timeless delay's drive (aliasing below 2 kHz). An impulse into the reverbs and Blur (RT60 by Schroeder integration, L/R correlation of the tail, echo density after Abel and Huang, and the tail's spectral peak over median as a colour check: Gaussian noise gives about 2.77). The Pro EQ by the impulse response divided by the same render with the band at 0 dB, against the analog prototype. The Compressor by a 1 kHz step from −40 to −6 dBFS, divided by the same render at 1:1.

## 3. The audit table

| Device | Engine (from the code) | Measured | Grade |
|---|---|---|---|
| Psy Bass (psyb) | `al-psb`: polyBLEP saw/square, whole voice at 2× with a halfband filter, linear ZDF 24 dB ladder or 12 dB SVF, tanh after the filter | aliasing C7 −63 dB; 90 % of peak 8.4 ms; −40 dB after 58 ms (default preset) | B+ |
| Kick designer (kick) | per-note JS render: sine with a curved log sweep per sample, tanh drive with no oversampling, normalised to 0.95 | attack instant (0.04 ms to 90 %) | B− |
| Sub (sbass) | `al-sbs`: exact harmonics (sine recursion), drive as harmonics, glide | aliasing C7 −157 dB | A− |
| Acid (acid) | `al-poly` (or nodes): 2 × 12 dB biquads, tanh after the filter, no oversampling; accent = velocity > 0.88 | aliasing C7 −39 dB (preset), −48 dB with Distortion 0, −30 dB at 55 and 100 | C |
| Venom (venom) | `al-venom`: 2 wavetables, 16 frames, 8 mip levels, linear interpolation; ZDF ladder and SVF with tanh; 8-slot matrix; no oversampling; unison clamped to 7 in the code while the knob goes to 16 | aliasing C7 −71 dB (init); with unison 7 the energy below the note rises to −43 dB (cause to check: drift or aliasing); L/R corr. 0.82 at unison 7 | B+ |
| Wavetable (wtab) | `al-poly`: 12 tables × 8 frames × 63 harmonics, 7 mip levels × 1024 points | aliasing C7 −114 dB; but 63 harmonics stop a 55 Hz note at 3.5 kHz | C |
| Plant and the classic synths (plant, saw, square, sub, bass, reese, pad, strings, pluck, keys) | `al-poly`: 2-point polyBLEP, naive triangle, RBJ 12 dB low-pass every 16 samples, parameters read at note start, no glide, 1 LFO (Plant, to cutoff) | saw lead −81 dB, Reese −61 dB, Plant −40 dB; classic synths L = R; Plant L/R 0.63 | C |
| Vector FM, Orbit (vfm, orb) | `al-vfm`, `al-orb`: phase modulation on 2048-point tables, linear interpolation, control every 64 samples | −32 dB at E7, −140 dB at C7; L/R 0.83 | B |
| Growl (growl) | per-note render: 2-op FM, formant SVFs, tanh, fold, no oversampling | −26 dB at E7, −45 dB at C7 | B− |
| Fractal (crk) | `al-crki`: BLEP saw, pulse gate, 2× with 91-tap halfband | −71 dB | B |
| Drum kit and designers (drums, zhat, zsnare, zclap, ztom) | kit: OscillatorNodes (band-limited) pre-rendered in 3 variants; designers: per-note JS, Hat designer with 6 naive squares, tanh drive without oversampling | not measured separately | C+ |
| Pro EQ (eq) | chains of BiquadFilterNodes; cuts as stacked Q 0.707 stages; dynamic EQ by a 30 ms main-thread timer | +12 dB bell at 16 kHz: +1.8 dB at 8 kHz (analog +4.0), +12.0 at 16 kHz, +3.4 at 20 kHz (analog +9.7), +0.8 at 22 kHz (analog +8.2) | B− |
| Compressor (comp), OTT, Multiband, Sidechain punch | DynamicsCompressorNode (knee 6, 6 ms look-ahead fixed); OTT's "up" is make-up gain | attack 63 % at 2, 10, 47 ms for 1, 10, 50 ms set; 8:1 at +24 dB over threshold: −3.5 to −4.3 dB against 1:1 (about −21 dB expected) | C− |
| Limiter (limit) | `al-limit`: look-ahead, sliding minimum, 2-stage release, 4-point true-peak estimate, hard clip; native port bit for bit | not re-measured (NB proved it) | B+ |
| Drive (drive) | WaveShaper `(1+k)x/(1+k|x|)`, 4× | 4.5 kHz sine, full drive: aliasing −40 dB | C+ |
| Soft Clipper (clip) | WaveShaper, 4× by default | −128 dB at the same input | A− |
| Timeless delay (tdelay) | DelayNodes, filters and a 256-point tanh WaveShaper in the loop (no oversampling), wow LFO | drive at 100: aliasing −35 dB | B− |
| Echo delay (delay) | 2 DelayNodes, HP/LP in the loop, ping-pong; no drive, no modulation | n/a | C+ |
| Space reverb (reverb) | ConvolverNode, generated filtered-noise IR, rebuilt 120 ms after a change | RT60 2.0 s (2.2 s set); tail L/R corr. 0.003; tail peak/median 2.79 (noise: 2.77); dense within 10 ms (no early reflections) | C+ |
| Convolution Reverb (conv) | ConvolverNode, generated IR with a few early taps, 8 rooms | default room RT60 0.26 s; tail L/R 0.09 | C |
| Blur (blur) | 4 DelayNodes with feedback and a low-pass | RT60 2.0 s, tail peak/median 1.5 | B− |
| Low-pass filter (filter) | one BiquadFilterNode, values set without smoothing | n/a | D |
| Auto Filter (afilt) | biquads (12/24, vowel by 3 bandpasses), drive WaveShaper without oversampling | n/a | C |

Not graded (no psytrance gap found, or covered by other research): Phaser, Chorus/Flanger, Bitcrusher (aliasing on purpose), Gate, Transient Shaper, De-Esser, Vocoder, Frequency Shifter, Pitch & Formant, Pitch Correction, Resonance Suppressor, Tape Stop, Stereo Imager, Ducker, Voice (see `docs/voice-research.md`), Vector Delay, Bounce Delay, Percussion and Bounce (modal, clean), Emit, Vector Grain, Sampler, Grid, FX.

Code details (line numbers in `index.html` v0.263): FXDEF 3536; `irBuf` 3901; `mkEQ2` 6758; al-poly 9608 to 9690; Growl 10879 to 10991; al-vfm 12032 to 12127; al-sbs 13380 to 13540; al-psb 14290 to 14429; Kick designer 3968 to 4006; drum designers 25025 to 25110; Wavetable 24956 to 25022; al-venom 25131; effect worklet bundle 24317; native ports in `native/engine/core/dev_dynamics.h` (limit, gate, trans, deess), `dev_crush.h` (crush), `dev_modulation.h` (chorus, imager, fshift, vocoder, tstop). No instrument and none of the core FXDEF effects has a native port yet.

## 4. Findings with sources

### 4.1 Oscillators and wavetables
- polyBLEP is the cheap standard; the 4-point B-spline version in Psy Bass measures −63 dB at C7, the 2-point version in al-poly is enough for a plain saw (−81 dB) but not with drive after it. Sources: Välimäki and Huovilainen, "Antialiasing Oscillators in Subtractive Synthesis", IEEE SPM 2007; Välimäki, Pekonen, Nam, JASA 2012 (https://mac.kaist.ac.kr/pubs/ValimakiPeknenNam-jasa2012.pdf); polyBLAMP for corners and hard sync: Esqueda, Välimäki, Bilbao, DAFx-16 (https://core.ac.uk/download/77046163.pdf).
- Wavetables: one band-limited table per octave, read with linear or cubic interpolation, crossfaded between frames (Electric Druid on Korg DWGS, https://electricdruid.net/?p=224). AudioLab's Wavetable keeps only 63 harmonics per table, which is fine at C7 but dull below C3. Serum uses 2048-sample frames; a table with up to 1024 harmonics covers a 20 Hz note.
- Unison: Szabo's JP-8000 analysis (2010; discussed at https://www.kvraudio.com/forum/viewtopic.php?p=4644620): non-linear detune spacing (−0.110, −0.063, −0.020, 0, +0.020, +0.062, +0.107 of the detune amount), free or random phase per voice, a mix of the centre voice against the sides, a key-tracked high-pass. Secondary: A. Shore's analysis of the Super Saw (linked from the KVR thread). The Szabo PDF itself has no stable URL.

### 4.2 Filters
- Zero-delay-feedback (TPT) filters track their cutoff without cramping and stay stable under fast modulation: Zavalishin, *The Art of VA Filter Design* rev. 2.1.0, free PDF (https://www.native-instruments.com/fileadmin/ni_media/downloads/pdf/VAFilterDesign_2.1.0.pdf), covering the SVF, the ladder and the diode ladder; Simper (Cytomic), "SvfLinearTrapOptimised2" (http://cytomic.com/files/dsp/SvfLinearTrapOptimised2.pdf; the extracted text was garbled, so the formulas were not checked from it).
- Nonlinear ladder: Huovilainen, DAFx-04 (https://dafx.de/paper-archive/2004/P_061.PDF): tanh in each stage. Stilson and Smith 1996 for the linear analysis (https://ccrma.stanford.edu/~jos/Mohonk05/Moog_VCF_Root_Locus.html).
- 303: Open303 by Robin Schmidt; the JC303 README says the Open303 engine is MIT (https://github.com/amadeusp/jc303; the rest of JC303 is GPL-3). The licence was only seen second-hand: check the Open303 files before copying. Pirkle's diode-ladder brief (AES) is paywalled and was not read.
- Today AudioLab has a true ZDF ladder only in Venom (with tanh) and Psy Bass (linear). Everything else uses RBJ biquads, which have no drive in the loop.

### 4.3 EQ
- Matched second-order filters fit the analog response up to Nyquist in closed form, at the cost of a biquad: Vicanek 2016 (https://www.vicanek.de/articles/BiquadFits.pdf; shelves: https://www.vicanek.de/articles/2poleShelvingFits.pdf). Orfanidis 1997 (prescribed Nyquist gain, AES, paywalled). RBJ cookbook: https://www.w3.org/TR/audio-eq-cookbook.
- Pro-Q's modes for comparison (https://www.fabfilter.com/help/pro-q/using/processingmode): Zero Latency matches analog magnitude with a small deviation above 18 kHz; Natural Phase matches magnitude and phase; Linear Phase costs 70 to 1509 ms of latency at 44.1 kHz.

### 4.4 Distortion and oversampling
- Antiderivative antialiasing (ADAA): Parker, Zavalishin, Le Bivic, DAFx-16 (https://dafx.de/paper-archive/details/vem_XXF5qBbfiWOH2RVVAA); Bilbao, Esqueda, Parker, Välimäki, IEEE SPL 2017 (https://core.ac.uk/download/322479137.pdf); Chowdhury's notebook (https://ccrma.stanford.edu/~jatin/Notebooks/adaa.html): y = (F(x[n]) − F(x[n−1])) / (x[n] − x[n−1]), the midpoint when the difference is tiny, half a sample of delay. Vicanek on AA distortion: https://www.vicanek.de/articles/AADistortion.pdf.
- Halfband polyphase IIR for 2× and 4×: HIIR by Laurent de Soras, WTFPL (http://ldesoras.free.fr/prod.html, mirror https://github.com/unevens/hiir).
- chowdsp_utils mixes licences per module: core and maths BSD, but filters, EQ, compressor and reverb are GPL-3, so not copyable.

### 4.5 FM
- Chowning 1973 (https://web.eecs.umich.edu/~fessler/course/100/misc/chowning-73-tso.pdf). Dexed is GPL-3, but its msfa engine stays Apache 2.0 (https://github.com/asb2m10/dexed): usable with the licence and NOTICE kept. Feedback FM is usually steadied by averaging the last two outputs (DX7-style code); I did not find a citable paper for that.

### 4.6 Reverb and delay
- Dattorro, "Effect Design Part 1" (https://ccrma.stanford.edu/~dattorro/EffectDesignPart1.pdf): the plate. Jot and Chaigne 1991 (FDN). Schlecht and Habets, modal decomposition of FDNs (https://arxiv.org/pdf/1901.08865).
- Valhalla's reading list and design notes (https://valhalladsp.com/2021/09/22/getting-started-with-reverb-design-part-2-the-foundations/): slow random modulation of delay lengths (Stautner and Puckette), a damping filter per line so all lines decay at the same rate (Jot). Supermassive's modes are FDN variants with a DENSITY control (https://valhalladsp.com/2020/05/07/valhallasupermassive-the-modes/).
- Signalsmith, "Let's Write a Reverb" (ADC 2021, https://signalsmith-audio.co.uk/writing/2021/lets-write-a-reverb): a 4-step diffuser (delay, shuffle and polarity flip, Hadamard mix) and an 8-channel Householder feedback loop. Signalsmith DSP is MIT; the example repository's licence was not verified.
- Usable code: Freeverb (public domain), CloudSeed v1 (MIT, https://github.com/ValdemarOrn/CloudSeed), CloudSeedCore (MIT, credit to Ghost Note Audio asked, https://github.com/GhostNoteAudio/CloudSeedCore), Airwindows (MIT, seen second-hand). Dragonfly Reverb: treat as GPL until checked.
- ValhallaDelay's modes (https://valhalladsp.com/2019/04/16/valhalladelay-the-mode-control): tape wow and flutter scale with delay time; Ghost adds frequency shift and diffusion. Putting allpass diffusion inside the feedback loop (B34) is my design, built from the Signalsmith diffuser; no source states where Valhalla puts it.

### 4.7 Dynamics
- Giannoulis, Massberg, Reiss, "Digital Dynamic Range Compressor Design: A Tutorial and Analysis", JAES 2012 (https://www.aes.org/e-lib/browse.cfm?elib=16354): soft-knee gain computer, peak or RMS detector, branching or decoupled smoothing in the log domain. This is the basis for Compressor v2 (B26).
- True peak: ITU-R BS.1770-5, 11/2023 (https://www.itu.int/dms_pubrec/itu-r/rec/bs/R-REC-BS.1770-5-202311-I!!PDF-E.pdf).
- The hidden make-up gain is measured, not read from Chromium's source. It matches the automatic make-up the Web Audio spec gives `DynamicsCompressorNode`; whoever builds B26 should confirm in the spec text.

### 4.8 Kicks, sub, psytrance practice
- Kick 3 (https://www.sonicacademy.com/products/kick/): 5 layers, Bézier pitch and amp envelopes with pitch snap to key, phase align and lock, sub harmonics, length synced to tempo, a click layer, analyse-and-resynthesise.
- SubLab XL (https://www.soundonsound.com/news/sublab-xl-future-audio-workshop): a VA layer with supersaw and unison over the sub, a sampler with pitch detection, six distortions.
- Psytrance rolling bass, Bonedo workshop (https://www.bonedo.de/artikel/psytrance-produzieren-workshop-1-kick-bass-percussion/): kick on every quarter and three 16th bass notes (KBBB); bass notes about a 16th long, the kick no longer than an 8th; the filter envelope closes within milliseconds; the first bass note after the kick plays quieter; the kick tail matches the bass root. No source specific to Electric Universe was found.
- Plug-in references: Phase Plant (https://kilohearts.com/docs/phase_plant): up to 32 generator modules, analog, wavetable, sample, granular and noise generators, 3 snapin lanes, audio-rate modulation. Serum 2 (https://synthtopia.com/content/2025/03/17/serum-2-gets-massive-update-and-its-free-for-existing-users, https://cdm.link/serum-2/): wavetable, multisample, sample, granular and spectral oscillators, two filters including combs and a diffuser, 3 FX buses, chaos modulators. Pigments 7 (https://www.arturia.com/products/software-instruments/pigments/overview): modal, granular, wavetable, sample, harmonic and VA engines.

### 4.9 Open-source licences (checked through repository pages or metadata; GitHub API was blocked)
| Project | Licence | Usable in AudioLab |
|---|---|---|
| Freeverb | public domain | yes |
| CloudSeed, CloudSeedCore | MIT (Core asks for credit) | yes |
| Signalsmith DSP | MIT | yes |
| HIIR | WTFPL | yes |
| DaisySP | MIT (the separate DaisySP-LGPL is not) | yes |
| Q (cycfi) | Boost 1.0 | yes |
| Mutable Instruments (STM32 code incl. Plaits, Clouds) | MIT (AVR code GPL-3) | STM32 code only |
| msfa (Dexed's engine) | Apache 2.0 | yes, keep licence and NOTICE |
| Open303 engine | MIT (second-hand) | check the files first |
| Airwindows | MIT (second-hand) | check first |
| Surge XT, Vital, Odin 2, Dexed | GPL-3 | ideas only |
| chowdsp_utils DSP modules | GPL-3 (core BSD) | core only |
| Faust libraries, stmlib, Dragonfly | not verified | check first |

## 5. Options (the pick page's cards)

Stars: ★★★ most value for psytrance. "v2" = a new engine mode, old projects stay on v1. "off" = a new control that starts at today's sound. "same" = the sound does not change with the settings unchanged. "new" = a new device; the old one stays. **Both** = belongs in the native engine too (NB ports it bit for bit); every card is Both except B25 (linear-phase EQ: web engine first, its latency path differs).

| Id | Device | Improvement | ★ | CPU | Old projects |
|---|---|---|---|---|---|
| B1 | Psy Bass | driven ladder (tanh per stage, at the existing 2×) | 3 | +0.3 % | v2 |
| B2 | Psy Bass | pitch blip per note | 2 | tiny | off |
| B3 | Psy Bass | snap attack to 0.3 ms with anti-click | 1 | none | off |
| B4 | Kick designer | drawn pitch and level curves, end note snapped to key | 3 | none | same |
| B5 | Kick designer | click layer (noise, FM zap or sample) | 2 | +0.05 % | off |
| B6 | Kick designer | 4× ADAA drive and a clipper | 2 | +0.1 % | v2 |
| B7 | Sub | top layer for small speakers | 1 | +0.1 % | off |
| B8 | Acid | diode ladder, accent sweep, 2× with drive inside | 3 | +0.4 % | v2 |
| B9 | Acid | squelch controls (accent decay, tracking, soft attack, sub) | 2 | none | off |
| B10 | Venom | 16-voice unison, JP-8000 spacing, phase, spread, blend | 3 | +3 % at 16 | same |
| B11 | Venom | import and edit wavetables, cubic interpolation | 2 | none | same |
| B12 | Venom | 2× oversampled distortion and filter drive | 2 | +40 % of a voice | v2 |
| B13 | Venom | 16 slots, 4 envelopes, MSEG, audio-rate FM | 2 | depends | same |
| B14 | Wavetable | full-band tables, shared import (or retire into Venom) | 2 | small | v2 |
| B15 | al-poly synths | live parameters for sounding notes | 3 | +0.1 % | same |
| B16 | al-poly synths | analog v2 voice (ZDF filter, 4-point BLEP, glide, LFOs, unison) | 2 | +0.2 %/voice | v2 |
| B17 | Vector FM, Orbit | per-sample index, averaged feedback, 2× at high index | 2 | +0.3 % | v2 |
| B18 | Growl | live voice in a worklet | 2 | +0.4 % | same |
| B19 | Growl | 2× ADAA fold and drive | 1 | +0.1 % | v2 |
| B20 | Hat designer | band-limited metal, 2× drive | 2 | none | v2 |
| B21 | Drum designers | velocity to tone, round robin | 2 | none | off |
| B22 | Pro EQ | matched bands (Vicanek) | 3 | none | v2 |
| B23 | Pro EQ | true Butterworth cuts | 2 | none | v2 |
| B24 | Pro EQ | dynamic EQ in the audio thread, sidechain per band | 2 | +0.2 % | v2 |
| B25 | Pro EQ | linear-phase mode | 1 | +1 to 2 % | off |
| B26 | Compressor | Compressor v2 (Giannoulis design, styles, sidechain, mix) | 3 | +0.2 % | v2 |
| B27 | OTT, Multiband | same core, real upward compression | 2 | +0.5 % | v2 |
| B28 | all waveshapers | first-order ADAA with the existing oversampling | 2 | +0.05 % each | v2 |
| B29 | Drive | tone, bias and modes | 1 | none | off |
| B30 | Limiter | 4× polyphase true-peak detection (check with AE3) | 1 | +0.3 % | v2 |
| B31 | Space reverb | ducking, synced pre-delay | 2 | tiny | off |
| B32 | Space reverb | early reflections and build-up in the IR | 1 | none | v2 |
| B33 | Convolution Reverb | load your own IRs, true stereo | 2 | same | same |
| B34 | Echo and Timeless delay | diffusion in the feedback loop | 3 | +0.1 % | off |
| B35 | Echo and Timeless delay | ducking | 2 | tiny | off |
| B36 | Timeless delay | tape mode, oversampled drive | 1 | +0.1 % | v2 |
| B37 | Filters | Filter v2 on the shared set; Auto Filter gets the models | 3 | +0.1 % | new |
| N1 | new | Hall: FDN and plate reverb with modulation, shimmer, freeze, duck | 3 | +0.5 to 1 % | new |
| N2 | new | Saturate: multiband saturation, 10 models, ADAA + 2× | 3 | +0.5 % | new |
| N3 | new | FM6: six-operator FM | 2 | ~1 % for 8 voices | new |
| N4 | new | Comb and Resonator | 2 | +0.1 to 0.3 % | new |
| N5 | new | one shared filter set (ladder, diode, SVF, Sallen-Key, comb, formant) | 3 | none by itself | new |
| N6 | new | Clouds: granular texture effect | 2 | +0.5 to 1 % | new |

"Take all ★★★" on the page gives: `AE4 picks: B1 B4 B8 B10 B15 B22 B26 B34 B37 N1 N2 N5`.

Not repeated from the feature picks (already planned): F14 MPE, F16 volume shaper, F17 multi-shaper, F18 kick and bass lab (B4 builds on its analysis, `NI_HOOKS.kickBass`), F19 step FX, F22 spectral editing, F23 slicing, F24 multisample zones, F33 racks with macros, F36 plug-ins.

## 6. The demos on the pick page

The "today" half of each demo is rendered by the app (v0.264, `tools/engine-lab/ae4/demos.py`, 32 kHz). The prototype half is simplified DSP in the page, written for the comparison, not the final code. It plays the same notes:
- **Rolling bass** (B1): F1, K-B-B-B at 145 BPM, today's Psy Bass default against a polyBLEP saw into a tanh-per-stage ladder at 2×.
- **Acid** (B8): the acid line of the app's own psy demo (pattern AS, cut 520, dist 65) against a nonlinear ladder at 2× with an accent capacitor and slide.
- **Kick** (B4 to B6): the demo song's kick (psyzap, tune 29) against a drawn sweep, a noise click layer and ADAA drive.
- **Supersaw** (B10): F minor chord, Venom unison 7, against 7 voices with JP-8000 spacing, random phase and spread.
- **Reverb** (N1): a pluck arpeggio through Space reverb (3.2 s, 35 %) against an 8-line FDN with 4 input allpasses and two modulated lines.
- **Aliasing** (N2, B28): a 1 to 8 kHz sine sweep into hard tanh, naive against ADAA at 2×. Both halves are computed in the page.
- **EQ** (B22): today's biquad curve with the 5 points measured in the app, against the analog shape a matched design follows.

## 7. Proposed tasks (one session each; only the picked ones are built)

Order: the shared pieces first, then the devices that use them. Every task: worklet code written as a plain-arithmetic core NB can port; a headless test using `tools/engine-lab/ae4/measure.py` (before and after numbers); the Fractals demo levels unchanged; a v1/v2 switch where the sound changes; a line in `docs/backlog-log.md`. All of them edit `index.html`, so each needs a lane (a new "sound" lane, prefix `snd`, is suggested; it would own the worklet DSP of instruments and effects but not their displays, which stay with lanes E and I).

1. **SND-0 shared DSP kit** (for N5, B28, B12, B19, B36): ZDF ladder, diode ladder, SVF, Sallen-Key, comb, formant; ADAA tanh, fold and hard-clip; halfband 2×/4× (HIIR design, WTFPL); parameter smoothing. One worklet module, unit tests against Zavalishin's responses. Both engines.
2. **SND-1 Filter v2 and Auto Filter models** (B37).
3. **SND-2 Compressor v2** (B26), then **SND-3 OTT and Multiband** on it (B27). Replaces DynamicsCompressorNode for new devices; NB then ports a plain core instead of Chromium's node.
4. **SND-4 Matched Pro EQ** (B22, B23), then **SND-5 dynamic EQ in the worklet** (B24).
5. **SND-6 Psy Bass v2** (B1 to B3) and **SND-7 Acid v2** (B8, B9).
6. **SND-8 Kick designer curves and click** (B4 to B6), using F18's analysis.
7. **SND-9 Venom unison and oversampling** (B10, B12), **SND-10 wavetable import** (B11, B14), **SND-11 Venom modulation** (B13).
8. **SND-12 live al-poly parameters and analog v2 voice** (B15, B16).
9. **SND-13 Hall reverb** (N1), **SND-14 delay diffusion, ducking, tape** (B34 to B36), **SND-15 reverb options and IR import** (B31 to B33).
10. **SND-16 Saturate** (N2) with Drive's modes (B28, B29).
11. **SND-17 FM6** (N3), **SND-18 Comb and Resonator** (N4), **SND-19 Clouds** (N6).
12. Smaller ones folded into the nearest task: B7 (Sub), B17 (Vector FM), B18 and B19 (Growl), B20 and B21 (drums), B30 (Limiter, with AE3).

## 8. Limits of this work

- "Today" was measured with default presets and a few settings, not every preset. Grades are my judgement from the measurements, the code and the plug-ins' published features; nothing was A/B tested against the plug-ins themselves (they are on the user's Mac, not here).
- Venom's unison-7 reading (−43 dB below the note) is not explained yet: random drift between voices or aliasing. The B10 task should measure it first.
- The cost column is offline render time; AE2 gives real numbers.
- Licences marked second-hand or unverified must be checked in the repositories before any code is copied.

## 9. Sources

All links are in section 4. Main ones: Zavalishin (VA filter design), Huovilainen (DAFx-04), Välimäki et al. (polyBLEP, polyBLAMP), Vicanek (matched biquads, AA distortion), Parker, Zavalishin and Le Bivic (ADAA), Bilbao et al. (ADAA), Giannoulis, Massberg and Reiss (compressors), Dattorro (plate), Jot and Chaigne, Schlecht and Habets (FDN), Signalsmith (reverb), Valhalla DSP blog (reverb and delay modes), ITU-R BS.1770-5, Chowning (FM), Szabo via KVR (supersaw), Bonedo (psytrance bass), Kilohearts, Xfer press coverage, Arturia, Sonic Academy and Future Audio Workshop product pages.

## The user's picks

(to be filled in when the user answers)
