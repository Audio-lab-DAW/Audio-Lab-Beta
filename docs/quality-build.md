# Sound quality: the build plan (task SQ, lane N, prefix `sq`)

The user's AE1 picks (27 November 2026, 21:48 Brussels), at the end of `docs/research-engine-sound.md`:
`Q0aa Q0ba Q1a Q2a Q3a Q4a Q5a Q6a Q7a Q8a Q9b Q10a Q11a Q12a Q13a Q14a Q15a Q16b` (a = now, b = later).

Lane N owns: the Quality switch per device and per song, the sample resampler (built-in sounds, bounces, stems, the export rate, pitched reads), the export post-processing (`postProc`: the safety limiter, true peak, the report, dither) and the Limiter's true-peak style. The device DSP itself (Q1 to Q8) is lane L's (`docs/sounds-build.md`); lane L's "v2 modes" are this Quality switch. Q9 (64-bit summing) goes to task NB; Q16 (shaped dither) waits.

One step per run; each run does the next step not yet logged as "task SQ<n>" in `docs/backlog-log.md`.

| Step | What | Status |
|---|---|---|
| SQ1 | The Quality switch (Q0a + Q0b) and the DC blocker after biased shapers (Q10) | **done**, v0.294 |
| SQ3 | Resample once (Q11): a windowed-sinc resampler in a worker; built-in sounds, bounces, stem results and export-rate buffers converted once and cached per rate, under the song's quality (Classic keeps the linear path bit for bit) | next |
| SQ3b | The sinc (or cubic) read for pitched samples (Q12), under the device's quality | |
| SQ4 | The Limiter style "True peak 4x" (Q13: BS.1770 detection with the meter's filter from lane E, 4x final clip); the export safety limiter replaced by it at -1 dBTP (Q14: only exports that would clip change); the export report (Q15: true peak, overs, clipped samples) through lane F's notification or dialog code. Then: sound quality complete | |

(There is no SQ2: al-poly's Clean oscillators and Acid went to lane L with the picks.)

## SQ1: the Quality switch (done, v0.294)

### What the user sees
- A small **Classic / Clean** chip in the title strip of every device that has a Clean sound (for now the Soft Clipper; lane L adds its devices). Click: switch this device (one undo step). Right-click (or Shift+F10, or the menu key): Clean, Classic, and for the whole song Use Clean everywhere / Use Classic everywhere. The tooltip says what Clean changes on that device.
- **Settings > Project > Sound quality**: "This song" Classic (as before) or Clean, how many devices with a Clean sound are Clean and Classic, and the buttons Use Clean everywhere and Use Classic everywhere (each one undo step). The row is in the settings table (`songQuality`), so search finds it and it carries the "project" mark.
- The command list: "Use Clean sound everywhere in this song" (`sq.cleanAll`) and "Use Classic sound everywhere in this song" (`sq.classicAll`).

### The data
- Song: `S.sq` = `'classic'` or `'clean'`. Missing = Classic: every song saved before v0.294, the demos, the Fractals song, the templates as saved, and songs built by scripts (`AudioLab.build`). Songs made in the New project window (empty, audio, instruments) start Clean.
- Effect: `f.q` = `'classic'` or `'clean'` (on the device object, beside `type`, `on`, `p`).
- Instrument: `t.inst.quality`. Not `q`: an instrument's own parameters sit on the same object, and the Clap, the Growl, Vector FM and Orbit already use `q` as a number (filter Q). Everyone reads the quality with `sqOf(device)` (or `SQ_HOOKS.of`), never `.q` directly.
- Missing on a device = follow the song. New devices (anything added after the song was opened: browser, paste of a device without one, menus, the Assistant, lessons) are stamped Clean, except in a song set to Classic by hand (`S.sq==='classic'`), where they are stamped Classic. A new song object (opened, switched, undone, built by a script) is taken as it is: nothing is stamped when a song opens.
- The audio code gets it as `p._sq` on each effect's parameter object: a non-enumerable mirror (never in the file, in undo or in `Object.keys`), refreshed in `changed()`, `syncGraph`, `renderMix` and `renderMixChunked` (wrapped, not changed). A node keeps the last value it saw, so a parameter copy without the mirror keeps the device's quality.

### Q10, the first Clean feature
The Soft Clipper with Asymmetry not 0: in Clean, a one-pole DC blocker at 5 Hz after its output. Classic goes through a gain of exactly 1.

| Asymmetry | DC, Classic | DC, Clean | Level, Classic / Clean |
|---|---|---|---|
| 0 % | -98.5 dBFS | -98.5 dBFS (no blocker: the shaper is symmetric) | -1.169 / -1.169 dB |
| 25 % | -23.8 dBFS | -197.4 dBFS | -1.171 / -1.176 dB |
| 50 % | -17.8 dBFS | -189.5 dBFS | -1.182 / -1.188 dB |

110 Hz sine at -4.4 dBFS, Gain +12 dB, 3 s at 48 kHz, the last second measured (the research doc's case; its -23.8 and -17.8 dBFS reproduced). Classic is bit-identical to the device without the switch at all three settings.

### For the other lanes
- Lane L (SND): your v2 modes are Clean. Read `sqOf(f)` / `sqOf(t.inst)` (or `p._sq` inside an effect's `set(p)`), register each device whose Clean sound differs with `SQ_HOOKS.reg(key, 'Clean: what changes')` (key: the effect type, or `'inst:'+preset` for an instrument) so its chip shows. Biased shapers: `SQ_HOOKS.dc(ctx)` gives the same DC blocker node, or use the formula below inside a worklet. Worklets do not see `p._sq` through `postMessage`: send the quality yourself.
- Lane I (DV): the chip is put after the device name in `.devh` by lane N, with a rotated style for the side strip (`.ds`). To place it in your own frame: set `DV_HOOKS.placesQuality=true` and call `SQ_HOOKS.chip(deviceElement)`, which returns the button (or null for a device without a Clean sound); the click and menu handlers are delegated and keep working wherever it sits.
- Lane B (ST): the card uses `ST5.card`, `ST5.sec('files')`, the table (`STT`, `STX`) and wraps `ST5.show` and `openSettings` as ST-S8 does; it sits after "New projects start with".
- Lane K (MX): `syncGraph`, `renderMix` and `renderMixChunked` are wrapped only to refresh the mirror before they run; nothing in them changed.

### What NB must port
- The field: effect `q`, instrument `quality`, song `sq`; missing = follow the song, the song missing = Classic; the stamping rule for new devices.
- The DC blocker: `y[n] = x[n] - x[n-1] + R*y[n-1]`, `R = 1 - 2*pi*5/sr`, state and arithmetic in double (Chromium's IIRFilterNode runs direct form I in double), output rounded to float, after the Soft Clipper's output gain (after the dry/wet sum), only when Clean and Asymmetry is not 0; the switch takes effect at the next parameter set, the filter's state starts at zero when it is switched in. Classic: no stage at all.

## Decisions taken without asking (the user can change them)
- New devices are Clean even in an old Classic song (Q0a: "new devices start in Clean"), unless the song was set to Classic by hand; the song setting is the default for devices without their own choice (Q0b).
- The chip shows only on devices whose Clean sound differs, so it never switches nothing.
- The Soft Clipper's blocker runs only while Asymmetry is not 0: a symmetric shaper makes no DC (-98.5 dBFS), and the blocker would otherwise shift the phase of the lowest notes for nothing.
- A device set to Clean takes later Clean improvements of that device when the app updates (Clean means "the improved sound"); Classic never changes. If the user wants Clean frozen per version too, a version number next to the field can be added later (`SQ.LV` is reserved for it).
- The demos made from the New project window ("demo", "beat") stay Classic: they are the demos.
