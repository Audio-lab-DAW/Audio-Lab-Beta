# Sound quality: the build plan (task SQ, lane N, prefix `sq`)

The user's AE1 picks (27 November 2026, 21:48 Brussels), at the end of `docs/research-engine-sound.md`:
`Q0aa Q0ba Q1a Q2a Q3a Q4a Q5a Q6a Q7a Q8a Q9b Q10a Q11a Q12a Q13a Q14a Q15a Q16b` (a = now, b = later).

Lane N owns: the Quality switch per device and per song, the sample resampler (built-in sounds, bounces, stems, the export rate, pitched reads), the export post-processing (`postProc`: the safety limiter, true peak, the report, dither) and the Limiter's true-peak style. The device DSP itself (Q1 to Q8) is lane L's (`docs/sounds-build.md`); lane L's "v2 modes" are this Quality switch. Q9 (64-bit summing) goes to task NB; Q16 (shaped dither) waits.

One step per run; each run does the next step not yet logged as "task SQ<n>" in `docs/backlog-log.md`.

| Step | What | Status |
|---|---|---|
| SQ1 | The Quality switch (Q0a + Q0b), shown as one switch "Hi-Fi", and the DC blocker after biased shapers (Q10) | **done**, v0.296 (released 28 Nov, after the gate's freeze) |
| SQ3 | Resample once (Q11): a windowed-sinc resampler in a worker; built-in sounds, bounces, stem results and export-rate buffers converted once and cached per rate, under the song's quality (Classic keeps the linear path bit for bit) | **done**, v0.310 |
| SQ3b | The sinc (or cubic) read for pitched samples (Q12), under the device's quality | next |
| SQ4 | The Limiter style "True peak 4x" (Q13: BS.1770 detection with the meter's filter from lane E, 4x final clip); the export safety limiter replaced by it at -1 dBTP (Q14: only exports that would clip change); the export report (Q15: true peak, overs, clipped samples) through lane F's notification or dialog code. Then: sound quality complete | |

(There is no SQ2: al-poly's Hi-Fi oscillators and Acid went to lane L with the picks.)

## SQ1: the Quality switch, shown as Hi-Fi (done, v0.296)

### What the user sees (the user's naming, 27 Nov 23:00 to 23:08 Brussels: one on/off switch "Hi-Fi")
- Internally the values stay `'classic'` (Hi-Fi off) and `'clean'` (Hi-Fi on), so no stored data changes; the interface only says Hi-Fi on or off. The short line is shown next to the switch, not only on hover: "Hi-Fi on: higher quality sound." / "Hi-Fi off: lighter and faster, good for slower computers or big projects."
- In the device: a Hi-Fi switch with its line as a row at the bottom of the device's controls (the rail), on every device that has a Hi-Fi sound (for now the Soft Clipper; lane L adds its devices). A device without a rail gets a small Hi-Fi chip after its name in the title strip. Click: on or off for this device (one undo step). Right-click (or Shift+F10, or the menu key): Hi-Fi on, Hi-Fi off, and for the whole song Hi-Fi everywhere / Hi-Fi off everywhere. The tooltip adds what Hi-Fi changes on that device.
- **Settings > Project > Hi-Fi**: the switch "Hi-Fi for this song" with its line, how many devices with Hi-Fi are on and off, and the buttons Hi-Fi everywhere and Hi-Fi off everywhere (each one undo step). For a song made before Hi-Fi (no song setting) the card shows once, in one visit of the Settings window: "This song was made before Hi-Fi mode was implemented, so it plays as you made it. Turn Hi-Fi on for higher quality." (`S.sqSeen` marks it seen; no sound, no undo step.) The row is in the settings table (`songHiFi`), so search finds it ("hi-fi", "sound quality") and it carries the "project" mark.
- The command list: "Hi-Fi everywhere in this song" (`sq.cleanAll`) and "Hi-Fi off everywhere in this song" (`sq.classicAll`).

### The data
- Song: `S.sq` = `'classic'` (Hi-Fi off) or `'clean'` (Hi-Fi on). Missing = Hi-Fi off: every song saved before v0.296, the demos, the Fractals song, the templates as saved, and songs built by scripts (`AudioLab.build`). Songs made in the New project window (empty, audio, instruments) start with Hi-Fi on.
- Effect: `f.q` = `'classic'` or `'clean'` (on the device object, beside `type`, `on`, `p`).
- Instrument: `t.inst.quality`. Not `q`: an instrument's own parameters sit on the same object, and the Clap, the Growl, Vector FM and Orbit already use `q` as a number (filter Q). Everyone reads the quality with `sqOf(device)` (or `SQ_HOOKS.of`), never `.q` directly.
- Missing on a device = follow the song. New devices (anything added after the song was opened: browser, paste of a device without one, menus, the Assistant, lessons) are stamped `'clean'` (Hi-Fi on), except in a song whose Hi-Fi was turned off by hand (`S.sq==='classic'`), where they are stamped `'classic'`. A new song object (opened, switched, undone, built by a script) is taken as it is: nothing is stamped when a song opens.
- The audio code gets it as `p._sq` on each effect's parameter object: a non-enumerable mirror (never in the file, in undo or in `Object.keys`), refreshed in `changed()`, `syncGraph`, `renderMix` and `renderMixChunked` (wrapped, not changed). A node keeps the last value it saw, so a parameter copy without the mirror keeps the device's quality.

### Q10, the first Hi-Fi feature
The Soft Clipper with Asymmetry not 0: with Hi-Fi on (`clean`), a one-pole DC blocker at 5 Hz after its output. Hi-Fi off (`classic`) goes through a gain of exactly 1.

| Asymmetry | DC, Hi-Fi off | DC, Hi-Fi on | Level, off / on |
|---|---|---|---|
| 0 % | -98.5 dBFS | -98.5 dBFS (no blocker: the shaper is symmetric) | -1.169 / -1.169 dB |
| 25 % | -23.8 dBFS | -197.4 dBFS | -1.171 / -1.176 dB |
| 50 % | -17.8 dBFS | -189.5 dBFS | -1.182 / -1.188 dB |

110 Hz sine at -4.4 dBFS, Gain +12 dB, 3 s at 48 kHz, the last second measured (the research doc's case; its -23.8 and -17.8 dBFS reproduced). Hi-Fi off is bit-identical to the device without the switch at all three settings.

### For the other lanes
- Lane L (SND): your v2 modes are Hi-Fi on (`clean`). Read `sqOf(f)` / `sqOf(t.inst)` (or `p._sq` inside an effect's `set(p)`), register each device whose Hi-Fi sound differs with `SQ_HOOKS.reg(key, 'what Hi-Fi changes, as a sentence part')` (key: the effect type, or `'inst:'+preset` for an instrument) so its switch shows; in the interface say Hi-Fi on / off, never Classic / Clean. Biased shapers: `SQ_HOOKS.dc(ctx)` gives the same DC blocker node, or use the formula below inside a worklet. Worklets do not see `p._sq` through `postMessage`: send the quality yourself.
- Lane I (DV): the switch row is appended by lane N at the bottom of the rail (`.devb>.dfs`) after your frame is drawn, or a chip after the name in `.devh` where a device has no rail. To place it in your own frame: set `DV_HOOKS.placesQuality=true` and call `SQ_HOOKS.chip(deviceElement, true)` (the row: switch and line) or `SQ_HOOKS.chip(deviceElement)` (the switch alone); null for a device without a Hi-Fi sound; the click and menu handlers are delegated and keep working wherever it sits.
- Lane B (ST): the card uses `ST5.card`, `ST5.sec('files')`, the table (`STT`, `STX`) and wraps `ST5.show` and `openSettings` as ST-S8 does; it sits after "New projects start with".
- Lane K (MX): `syncGraph`, `renderMix` and `renderMixChunked` are wrapped only to refresh the mirror before they run; nothing in them changed.

### What NB must port
- The field: effect `q`, instrument `quality`, song `sq`; missing = follow the song, the song missing = Classic; the stamping rule for new devices.
- The DC blocker: `y[n] = x[n] - x[n-1] + R*y[n-1]`, `R = 1 - 2*pi*5/sr`, state and arithmetic in double (Chromium's IIRFilterNode runs direct form I in double), output rounded to float, after the Soft Clipper's output gain (after the dry/wet sum), only when Clean and Asymmetry is not 0; the switch takes effect at the next parameter set, the filter's state starts at zero when it is switched in. Classic: no stage at all.

## SQ3: resample once (done, v0.310)

### What changes
- With Hi-Fi on for the song (`S.sq==='clean'`), a buffer whose rate is not the rate it plays at is converted once to that rate, in a worker, and the copy is kept per rate. That covers the built-in sampler and drum sounds (made at 44.1 kHz), bounces (rendered at 44.1 kHz), the stem splitter's 44.1 kHz results, songs saved at another rate, and every clip when an export runs at another rate than the engine.
- Hi-Fi off (every loaded song, the demos, the Fractals song) is today's path, untouched: the source gets the very same buffer and Chromium interpolates linearly.
- Nothing new on screen: the Hi-Fi row's tooltip in Settings > Project adds "With Hi-Fi on, sounds made at another sample rate (built-in sounds, bounces, stems, exports at another rate) are converted once with a cleaner method."

### How (no other lane's code changed)
- `AudioBufferSourceNode.prototype.buffer`'s setter is wrapped (`sqRsPick`): in a Hi-Fi song it hands the node the copy for its context's rate when there is one. Live, a buffer without a copy yet plays as before and its copy is made in the worker for the next time; copies start as soon as a buffer is loaded or made (`BUFS.set` and `SBUF.set` wrapped on the two Map objects), and for every loaded buffer when the song turns Hi-Fi on or a Hi-Fi song is opened (`sqScan` wrapped).
- Offline renders that make files wait for the worker first: `renderMix`, `renderMixChunked` (lane K's, wrapped, not changed), `bounceRender` and `neuTo44` (the stem splitter's input). During them a buffer made on demand (a drum sound) is converted on the spot by the same function, so a render never depends on timing. Other offline renders (the map's analysis and the like) use a copy if there is one and never convert on the main thread outside an export.
- The cache is a WeakMap on the original buffer: a copy goes when its buffer goes. `SQ_HOOKS.resample(buffer, rate)` (promise), `SQ_HOOKS.resampleNow(buffer, rate)` and `SQ_HOOKS.warm(rate)` for other lanes.

### Measured (`tools/ui-tests/taskSQ3.py`, the research doc's analyser `alias_report`, a 0.5 sine, the middle second)

| 44.1 kHz buffer in a 48 kHz render | 1 kHz | 5 kHz | 10 kHz | 15 kHz |
|---|---|---|---|---|
| Hi-Fi off (linear, as in the research doc) | -62.4 dB | -33.9 dB | -20.4 dB | -11.1 dB |
| Hi-Fi on (sinc, once) | -119.8 dB | -119.3 dB | -118.0 dB | -127.4 dB |
| Level, off / on | -0.015 / 0.000 dB | -0.367 / 0.000 dB | -1.456 / 0.000 dB | -3.121 / 0.000 dB |

Other rates, Hi-Fi off / on: 48 to 96 kHz at 10 kHz -18.8 / -140.3 dB, at 20 kHz -4.6 / -105.4 dB; 48 to 44.1 kHz at 10 kHz -22.2 / -118.9 dB; 44.1 to 96 kHz at 15 kHz -11.1 / -127.4 dB. A constant passes within 2e-6. The linear path also loses top end (-1.5 dB at 10 kHz, -3.1 dB at 15 kHz); the sinc keeps it flat to 21 kHz. A 4-minute stereo 44.1 kHz buffer takes about 4.9 s in the worker (3.0 s on the main thread when no worker can start) on the 2-core cloud machine; the main thread stays free.

### What NB must port
- The resampler (`sqRsBank`, `sqRsRun`): U/D = out rate / in rate reduced by their gcd; fc = min(1, out/in) * 0.96; W = ceil(32/fc); T = 2W taps; for each phase ph in 0..U-1 the taps t = 0..T-1 sit at d = ph/U + (W-1-t), value sinc(fc*d) * I0(10*sqrt(1-(fc*d/32)^2)) / I0(10) when |fc*d| < 32, else 0 (sinc(0) = 1, sin from fdlibm as V8 uses it, I0 the plain series to 1e-21 relative, at most 63 terms), each phase divided by its own sum. Output i reads input taps j = k-W+1+t (0 outside the buffer), k and ph advanced exactly in integers (ph += D; k += floor(ph/U); ph -= that * U); the sum in double in tap order (no FMA), rounded to float once. Output length ceil(n*U/D).
- When: only in a Hi-Fi song, for a buffer played at another rate than its own; exports convert every buffer first. NB resamples on load the same way and keeps the copy per rate.

## Decisions taken without asking (the user can change them)
- New devices start with Hi-Fi on even in an older song (Q0a and the user's "new devices start with Hi-Fi on"), unless the song's Hi-Fi was turned off by hand; the song setting is the default for devices without their own choice (Q0b).
- The switch shows only on devices whose Hi-Fi sound differs, so it never switches nothing.
- The Soft Clipper's blocker runs only while Asymmetry is not 0: a symmetric shaper makes no DC (-98.5 dBFS), and the blocker would otherwise shift the phase of the lowest notes for nothing.
- A device with Hi-Fi on takes later Hi-Fi improvements of that device when the app updates; Hi-Fi off never changes. If the user wants Clean frozen per version too, a version number next to the field can be added later (`SQ.LV` is reserved for it).
- The demos made from the New project window ("demo", "beat") open with Hi-Fi off: they are the demos.
- Resampling follows the song's Hi-Fi, not each device's: the same buffer can feed several devices, and a copy per device would double the memory. The pitched reads (SQ3b) will follow the device.
- The switch sits in the rail rather than the title strip because the user wants its line next to it, and the side strip (28 px, vertical) has no room for a line.

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
