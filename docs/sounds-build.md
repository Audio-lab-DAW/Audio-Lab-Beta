# Built-in sounds: the build plan (task SND, lane L)

Plan for the user's AE4 picks of 27 November 2026, 21:13 Brussels: **everything**, `B1` to `B37` and the new devices `N1` to `N6`.
Research, measurements and options: `docs/research-built-in-sounds.md` (section 3 the audit, section 4 the findings with sources, section 5 the options, section 7 the task order, "The user's picks" at the end). Pick page source with the reference prototypes: `tools/engine-lab/ae4/page/pick.html`. Before and after test: `tools/engine-lab/ae4/measure.py` and `results.json`.

Lane L owns the worklet DSP of instruments and effects: the processors registered in `wlLoad`, their parameters in `FXDEF`, the shared DSP kit (`sndKitCore`, worklet name `SNDK`) and the new devices. Not the device frame (lane I), not what is drawn inside displays (lane E, fed through `SND_HOOKS`), not sidechain routing or the Ducker (lane K), not Settings rows (lane B). Prefix `snd`. Edit scripts in `tools/engine-lab/snd/`, tests in `tools/ui-tests/taskSND_<n>.py`, A/B renders in `tools/engine-lab/snd/renders/`.

## Status

One step per run, in the order of section 7 of the research. A step that does not fit one run is split into parts (a, b).

| Step | Picks | What | Status |
|---|---|---|---|
| SND-0 | N5 (kit), groundwork for B12, B19, B28, B36 | shared DSP kit: ZDF ladder, diode ladder, SVF, Sallen-Key, comb, formant; ADAA tanh, fold, hard clip; halfband 2x and 4x; parameter smoothing; one worklet module; unit tests against the analog responses | claimed (27 Nov) |
| SND-1 | B37, N5 | Filter v2 on the shared set (new device), Auto Filter models (v2) | |
| SND-2 | B26 | Compressor v2 (Giannoulis design, styles, sidechain input through lane K's `mxScPick` when released, else `SND_HOOKS`, mix) | |
| SND-3 | B27 | OTT and Multiband on the Compressor v2 core, real upward compression | |
| SND-4 | B22, B23 | Pro EQ matched bands (Vicanek) and true Butterworth cuts, v2 | |
| SND-5 | B24, B25 | dynamic EQ in the worklet with a sidechain per band; linear-phase mode (web engine first) | |
| SND-6 | B1, B2, B3, B7 | Psy Bass v2 (driven ladder, pitch blip, snap attack); Sub top layer | |
| SND-7 | B8, B9 | Acid v2 (diode ladder, accent sweep, 2x with drive inside, squelch controls) | |
| SND-8 | B4, B5, B6, B20, B21 | Kick designer curves, click layer, 4x ADAA drive (lane C's F18 analysis if released); Hat designer band-limited metal; drum velocity to tone, round robin | |
| SND-9 | B10, B12 | Venom 16-voice unison (first measure why unison 7 reads -43 dB), 2x oversampled distortion and filter drive | |
| SND-10 | B11, B14 | wavetable import and edit, cubic interpolation; Wavetable full-band tables | |
| SND-11 | B13 | Venom modulation: 16 slots, 4 envelopes, MSEG, audio-rate FM | |
| SND-12 | B15, B16 | live al-poly parameters; analog v2 voice | |
| SND-13 | N1 | Hall: FDN and plate reverb with modulation, shimmer, freeze, duck | |
| SND-14 | B34, B35, B36 | delay diffusion, ducking, tape mode with oversampled drive | |
| SND-15 | B31, B32, B33 | Space reverb ducking and synced pre-delay, early reflections; Convolution Reverb IR import, true stereo | |
| SND-16 | N2, B28, B29 | Saturate (multiband, 10 models, ADAA + 2x); ADAA on all waveshapers (v2); Drive tone, bias, modes | |
| SND-17 | N3, B17 | FM6 six-operator FM; Vector FM and Orbit per-sample index, averaged feedback | |
| SND-18 | N4, B18, B19 | Comb and Resonator; Growl live voice and 2x ADAA fold | |
| SND-19 | N6, B30 | Clouds granular effect; Limiter 4x polyphase true peak (with AE3) | |

After the last step the run says "built-in sounds complete".

## Rules every step keeps

- **No silent changes.** An improvement that changes the sound is a `v2` engine mode or a new device. Old projects keep v1 and render bit-identically (the release gate's export check, Fractals Kick -19.05560 dB and Bass -35.48685 dB at master -10 dB). New instances default to v2 only where the research doc says so for that card.
- **Plain arithmetic, portable to the native engine (task NB) bit for bit.** Only `+ - * /`, `Math.sqrt`, `Math.abs`, comparisons, and the fdlibm functions V8 uses for `Math.exp`, `Math.log`, `Math.log1p`, `Math.tan`, `Math.tanh`, `Math.sin`, `Math.cos` (native: `native/third_party/fdlibm`, `ieee754::` names). No `Math.pow` (V8 has its own), no `Math.random` in the audio path (the worklet's seeded stream only), no fused multiply-add (native build with `-ffp-contract=off`), denormals kept (no flush to zero; states below 1e-30 are zeroed explicitly by `flush()`), evaluation order as written.
- **Licences.** The kit is my own implementation from the papers. Where a design follows an open project (HIIR, WTFPL) it says so in the code and here.
- AE1 (engine sound quality) has no user picks recorded yet; when it has, its oversampling, resampling and dither rules apply to the steps after it.
- CPU per voice measured; v1 not worse. No per-frame work while idle. Dark and Light, plain language, no em dashes in UI text, a tooltip on every new control.
- Release per step: VERSION + 0.001, `node desktop/scripts/sync-app.js` (never `desktop/app-version.json`), one line in `desktop/update-notes.txt`, a `task SND-<n>` entry in `docs/backlog-log.md` with what is left and what NB must port, a line in "Where it stands" of `docs/device-backlog-2026-11-25.md`, this table updated.
