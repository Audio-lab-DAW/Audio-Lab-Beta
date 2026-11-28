# Built-in sounds: the build plan (task SND, lane L)

Plan for the user's AE4 picks of 27 November 2026, 21:13 Brussels: **everything**, `B1` to `B37` and the new devices `N1` to `N6`.
Research, measurements and options: `docs/research-built-in-sounds.md` (section 3 the audit, section 4 the findings with sources, section 5 the options, section 7 the task order, "The user's picks" at the end). Pick page source with the reference prototypes: `tools/engine-lab/ae4/page/pick.html`. Before and after test: `tools/engine-lab/ae4/measure.py` and `results.json`.

Lane L owns the worklet DSP of instruments and effects: the processors registered in `wlLoad`, their parameters in `FXDEF`, the shared DSP kit (`sndKitCore`, worklet name `SNDK`) and the new devices. Not the device frame (lane I), not what is drawn inside displays (lane E, fed through `SND_HOOKS`), not sidechain routing or the Ducker (lane K), not Settings rows (lane B). Prefix `snd`. Edit scripts in `tools/engine-lab/snd/`, tests in `tools/ui-tests/taskSND_<n>.py`, A/B renders in `tools/engine-lab/snd/renders/`.

## Status

One step per run, in the order of section 7 of the research. A step that does not fit one run is split into parts (a, b).

| Step | Picks | What | Status |
|---|---|---|---|
| SND-0 | N5 (kit), groundwork for B12, B19, B28, B36 | shared DSP kit: ZDF ladder, diode ladder, SVF, Sallen-Key, comb, formant; ADAA tanh, fold, hard clip; halfband 2x and 4x; parameter smoothing; one worklet module; unit tests against the analog responses | **done**, v0.281 (27 Nov): 43 unit checks, worklet bits equal the main thread; no device uses it yet |
| SND-1 | B37, N5 | Filter v2 on the shared set (new device), Auto Filter models (v2) | **done**, v0.313 (28 Nov): new device Filter (7 models, drive inside, 2x), the Auto Filter's Hi-Fi models; Classic bit for bit |
| SND-R | (the user's D2) | one random stream per device (seeded generator per device instance, plain integer arithmetic for NB) | claimed 28 Nov (step claimed) |
| SND-2 | B26 | Compressor v2 (Giannoulis design, styles, sidechain input through lane K's `mxScPick` when released, else `SND_HOOKS`, mix) | |
| SND-3 | B27 | OTT and Multiband on the Compressor v2 core, real upward compression | |
| SND-4 | B22, B23, Q7, Q8 | Pro EQ matched bands (Vicanek) and true Butterworth cuts, Clean mode | |
| SND-5 | B24, B25 | dynamic EQ in the worklet with a sidechain per band; linear-phase mode (web engine first) | |
| SND-6 | B1, B2, B3, B7 | Psy Bass v2 (driven ladder, pitch blip, snap attack); Sub top layer | |
| SND-7 | B8, B9, Q2 | Acid Clean (diode ladder, accent sweep, 2x with ADAA drive inside, squelch controls) | |
| SND-8 | B4, B5, B6, B20, B21, Q3 (Kick, pads) | Kick designer curves, click layer, 4x ADAA drive (lane C's F18 analysis if released); Hat designer band-limited metal; drum velocity to tone, round robin | |
| SND-9 | B10, B12 | Venom 16-voice unison (first measure why unison 7 reads -43 dB), 2x oversampled distortion and filter drive | |
| SND-10 | B11, B14 | wavetable import and edit, cubic interpolation; Wavetable full-band tables | |
| SND-11 | B13 | Venom modulation: 16 slots, 4 envelopes, MSEG, audio-rate FM | |
| SND-12 | B15, B16, Q1, Q6 | live al-poly parameters; analog Clean voice (table-BLEP saw and square, BLAMP triangle, ZDF SVF) | |
| SND-13 | N1 | Hall: FDN and plate reverb with modulation, shimmer, freeze, duck | |
| SND-14 | B34, B35, B36 | delay diffusion, ducking, tape mode with oversampled drive | |
| SND-15 | B31, B32, B33 | Space reverb ducking and synced pre-delay, early reflections; Convolution Reverb IR import, true stereo | |
| SND-16 | N2, B28, B29, Q4, Q5 | Saturate (multiband, 10 models, ADAA + 2x); ADAA and oversampling on the remaining shapers (Clean); Drive ADAA, the curve beyond +-1, tone, bias, modes | |
| SND-17 | N3, B17 | FM6 six-operator FM; Vector FM and Orbit per-sample index, averaged feedback | |
| SND-18 | N4, B18, B19, Q3 (Growl) | Comb and Resonator; Growl live voice and ADAA fold at 4x | |
| SND-19 | N6 | Clouds granular effect. (B30, the Limiter's true peak, is built by lane N with Q13 in SQ4, as the AE1 picks say; lane L logs it there when released.) | |

After the last step the run says "built-in sounds complete".

## Rules every step keeps

- **No silent changes.** An improvement that changes the sound is a Clean engine mode (the `q` field) or a new device. Old projects keep v1 and render bit-identically (the release gate's export check, Fractals Kick -19.05560 dB and Bass -35.48685 dB at master -10 dB). New instances default to v2 only where the research doc says so for that card.
- **Plain arithmetic, portable to the native engine (task NB) bit for bit.** Only `+ - * /`, `Math.sqrt`, `Math.abs`, comparisons, and the fdlibm functions V8 uses for `Math.exp`, `Math.log`, `Math.log1p`, `Math.tan`, `Math.tanh`, `Math.sin`, `Math.cos` (native: `native/third_party/fdlibm`, `ieee754::` names). No `Math.pow` (V8 has its own), no `Math.random` in the audio path (the worklet's seeded stream only), no fused multiply-add (native build with `-ffp-contract=off`), denormals kept (no flush to zero; states below 1e-30 are zeroed explicitly by `flush()`), evaluation order as written.
- **Licences.** The kit is my own implementation from the papers. Where a design follows an open project (HIIR, WTFPL) it says so in the code and here.
- AE1 (engine sound quality) picks are recorded (27 Nov, 21:48): the device items Q1 to Q8 are folded into the steps above (see the section at the end). **One switch:** a step's v1/v2 is lane N's Quality switch, `q:'classic'|'clean'` per device with a project-wide default (Classic for loaded projects, Clean for new devices); until SQ1 is released, lane L uses that field name and those values.
- CPU per voice measured; v1 not worse. No per-frame work while idle. Dark and Light, plain language, no em dashes in UI text, a tooltip on every new control.
- Release per step: VERSION + 0.001, `node desktop/scripts/sync-app.js` (never `desktop/app-version.json`), one line in `desktop/update-notes.txt`, a `task SND-<n>` entry in `docs/backlog-log.md` with what is left and what NB must port, a line in "Where it stands" of `docs/device-backlog-2026-11-25.md`, this table updated.

## Added from the sound-quality picks (AE1, 27 Nov 2026, 21:48 Brussels)

Read `docs/research-engine-sound.md` (picks at its end). Fold into the steps that touch the same device: **Q1** table-BLEP saw/square and BLAMP triangle, **Q6** ZDF SVF (al-poly, with SND-12), **Q2** Acid at 2x with ADAA drive (SND-7), **Q3** Kick, pads and Growl at 4x (SND-8 and the Growl fold-in), **Q4** Drive ADAA and the curve beyond ±1 and **Q5** the remaining shapers oversampled (SND-16), **Q7** Pro EQ analog-matched top end and **Q8** Butterworth slopes or a label (SND-4). Use the aliasing script and numbers in that doc as tests. **One switch:** your v1/v2 modes are the Quality switch Classic/Clean that lane N (task SQ, step SQ1) defines (`q:'classic'|'clean'` per device, a project-wide default, Classic for loaded projects, Clean for new devices); until SQ1 is released, use the same field name and values so SQ1 needs no migration. The Limiter's true peak (B30) is built by lane N with Q13: leave it to SQ4.

## The switch's name (the user, 27 Nov 2026, 23:00 Brussels): one switch, "Hi-Fi"

The user asked for one on/off switch instead of two named modes ("a switch that says Hi-Fi, you switch it on, but there is no Classic mode, it's just on or off"). Decided: **one switch labelled "Hi-Fi"**, per device and per project. The internal field stays `q:'classic'|'clean'` (off = classic, on = clean), so no stored data changes; only the labels in the interface say Hi-Fi on or off.
- **Off**: the device sounds exactly as the song was made, and it is the lighter setting.
- **On (Hi-Fi)**: cleaner (oversampling, band-limited oscillators, better filters, fewer harsh digital artefacts) and costs more processing on the parts it changes (measured in this research: about 2 to 3 times on those parts, for example Acid's drive 73 to 211 ns per sample per voice, a ZDF filter stage 7 to 20 ns, band-limited oscillators the same at low notes and 2.4 times at 3 kHz; resampling costs nothing while playing because it is done once when a sample loads).
- Loaded projects open with Hi-Fi off (unchanged sound); new devices start with Hi-Fi on; the project has "Hi-Fi everywhere" with one undo step. Tooltip and help line (the user's wish, 23:06 Brussels: a short explanation next to the switch): "Hi-Fi on: higher quality sound. Hi-Fi off: lighter and faster, good for slower computers or big projects." (The user found "exactly as the song was made" confusing, 23:07 Brussels: it sounded as if off were more perfect. Dropped from the line. Instead, when an older project opens with Hi-Fi off, the project setting shows once: "This song was made before Hi-Fi mode was implemented, so it plays as you made it. Turn Hi-Fi on for higher quality." (Wording from the user, 23:08 Brussels.)) Show the same short line under the switch in the device and in the project setting, not only on hover.
- Not "Lossless": that word means lossless compression (like FLAC) and would promise something else.

## Added from the user's decision D2 (28 November, 00:27 Brussels): step SND-R

**SND-R, one random stream per device** (docs/review-native.md A2 and D2; the user said yes): replace the shared `Math.random` in the worklet scope with a small seeded generator per device instance (seed from the project's export seed and the device id; plain integer arithmetic that NB ports bit for bit, for example xoshiro128** or a 32-bit PCG). Versioned per device (an algorithm version field): projects saved before SND-R keep the shared stream in the web engine so they render bit-identically (Fractals and Shrine Legion hashes unchanged); new devices and devices the user resets get v2. Test: two Bitcrushers with dither in one song render the same at every block size; a single device unchanged at v1. Do it as the next step after the one in progress (before NB ports any random-drawing device), and log what NB must port.

## The user's decision R1 (28 November 2026, 14:36 Brussels): one sound, no v1 kept

The user: "Let's have each sound improvement have a new sound for everything. No old songs included. What do you mean by keeping the old V1? I don't think that's necessary either."

What changes, for every lane that improves device sound (L SND, N SQ, and NB when it ports):
- **No v1 kept.** An improvement replaces the old sound, in new and old projects alike. No second code path for the old sound, no per-device algorithm version, no "old projects keep v1 bit-identically". This replaces the "No silent changes" rule at the top of docs/sounds-build.md and the v1/v2 wording in docs/research-engine-sound.md.
- **The Hi-Fi switch stays, with one meaning only:** on = the heavier extras (oversampling, the finer filters), off = lighter and faster for slow computers or big projects. Off is NOT the exact old sound any more. Improvements that cost no extra CPU are simply the sound, with Hi-Fi on or off.
- **Old projects** open with the app's normal Hi-Fi default like any project; the one-time "This song was made before Hi-Fi mode was implemented" note is no longer needed (lane N drops it, or never builds it if not yet released).
- **SND-R** (one random stream per device): no version field; every project uses the new per-device stream.
- **Tests:** drop the "Classic bit-identical" and "v1 unchanged" tests. Keep: CPU per voice, aliasing numbers, no NaN or silence, level close to before (within about 1 dB unless the step means to change level). The release gate's export check takes new reference numbers after each released sound step (docs/release-gate.md): it still catches crashes, silence, clipping and big level jumps.
- **Still kept:** old projects must open with all their tracks, notes, devices and settings; the mixer, timing and sync stay exact; stable ids.
- Work already built with a v1/v2 split may simply delete the v1 path at its next step.

## The user's decision R0 (28 November 2026, 14:37 Brussels): old projects need not open

The user: "It's really not important that the old projects must still open. We're going to ditch all of them. We are not even going to use the old projects at all."

This overrides every "old projects must still load / keep their sound / render bit-identically" rule in every plan doc (sounds-build, features-build, mixing-build, latency-build, comfort-build, quality-build, devices-display-first, ideas-build, the research docs and the release gate):
- **No migration code and no compatibility paths** for projects saved by earlier versions. A lane may change the saved project format freely; it does not write upgraders, version branches or "if the project is older than..." code. Existing compatibility code may be deleted when a lane next touches that area.
- **The release gate's test songs** (Fractals, Shrine Legion and the others) are test material, not user projects: when a format or sound change breaks one, the lane that made the change re-saves it in the current format (or the gate takes new reference numbers) in the same step. The gate still checks that the current version saves, reopens its own save and plays it.
- **The start screen** (lane Q) lists only projects the current format opens; a file it cannot open gets a short plain message, never a crash.
- **Still kept:** a project saved by the current version reopens with everything; the mixer, timing and sync stay exact; stable ids.
- From the first public release on, compatibility starts again (projects made by released versions must open); until then, none is needed.
