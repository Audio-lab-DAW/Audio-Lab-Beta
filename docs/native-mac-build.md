# AudioLab native Mac: the build, stage by stage

The running list of the native Mac work (task NB). Plan: `docs/native-mac-plan.md`. The user's picks and the reports from their Mac: `docs/native-mac-picks.md`.

## Where it stands

| Stage | What | State |
|---|---|---|
| 0 | The proofs: one effect bit for bit, a VST3 host, the test app | done (task NM1), proven on the user's Mac |
| N1 | Native audio output and device control, as a helper the app can talk to | **done as a helper and proven on the build machine; not yet inside the app** |
| N2 | The bridge: the app sends its sound to the engine, with a switch back | **N2a done**: the path is proven outside the app. **N2b built**: the clock follower (proven in the engine's own tests), the shell's side and the page's side of the bridge, crash recovery; the Mac proof (cases A to D) is written but waits for a macOS build machine. **N2c** (the hook in `index.html`, the settings, `alengine` in the desktop build) waits for the design chain |
| N3 | The engine core, devices ported family by family | **N3a done**: the core's device layer, chains and offline render; the dynamics family (limiter, gate, transient shaper, de-esser) and the Bitcrusher, **119 of 119 cases bit for bit** against the web engine (every preset) on Linux, here and on GitHub's Linux machine; the Apple Silicon run waits for a build machine. **N3b built**: the mixer (track volume, pan, the master, tracks summed) from Chromium's arithmetic, **10 of 10 scenes bit for bit** against the app's own export path on Linux, including the Bitcrusher in a track at 128 and 512 frames. **N3c done**: five more devices (chorus, stereo imager, frequency shifter, vocoder, tape stop), the browser's own maths functions carried by the engine, **240 of 240 cases bit for bit**; the same bits at any buffer size from 1 to 4,096 frames on the web engine's grid (exceptions measured and explained), the export's 512 quantum. Devices native: 10 of 42. Next: N3d (sends, groups and returns; the mixer's tracks run the core's chains) |
| R1 | Review fix NB-R1: native CI on every push | **done on Linux** (task NB-R1): workflow `native-ci.yml` builds every native target normally and with AddressSanitizer + UndefinedBehaviorSanitizer, runs the engine's selftest, the ring under two real threads (also under ThreadSanitizer), the mixer's 10 scenes and all 240 device cases against the web engine (green: 240 of 240, sanitizers 240 of 240 at 128 frames, 239 of 240 at 7 as known), and 27 bridge checks against a stand-in engine. The Apple Silicon part waits for a Mac runner (D9) |
| N4 | VST3 in the app | host layer and scanner exist from stage 0, the test app is at 0.4 (search, parameter moves, notes, output warning); not in the app |
| N5 to N8 | Recording, export, packaging, polish | not started |

## What you can try now

Nothing new to try from stages N2b to N3c: they change nothing you can hear or click yet (the native engine core renders offline and is checked by machines). The newest test app is 0.4 (task NL4, see `docs/backlog-log.md`).

## What you could try with test app 0.2 (stage N1)

**AudioLab VST3 test 0.2**: https://github.com/Audio-lab-DAW/Audio-Lab-Pro-Alpha/releases/tag/native-lab-2 (file `AudioLab-VST3-test-mac-arm64.zip`; open it once through System Settings > Privacy & Security > Open Anyway, as before).

New in 0.2, the second row of the window:
1. **Rate**: switches the Gryphon's sample rate from inside the app. Try 44.1, 96 and 192 kHz with a plug-in playing.
2. **Exclusive use of the device**: tick it, then try to play something from another program through the Gryphon. It should stay silent there until you untick it.
3. **Device volume**: the Gryphon's own volume. Move it in the app and watch Audio MIDI Setup; then move it in Audio MIDI Setup and watch the app.
4. Plug the Gryphon (or the AMS-24) out and in while the app is open: the list should update by itself, and if the device in use goes away the app should move to the default output and say so.
5. "Play test pattern" with nothing loaded now says what to do.

Paste the report as before. The lines to look for start with `[rate]`, `[exclusive]`, `[devices]`.

## The user's report on test app 0.2 (27 November 2026, M4, iFi Gryphon)

"Everything works except finding the Zoom AMS-24."

- **Rate:** switched the Gryphon to 192 kHz from inside the app; Serum 2 played at 192 kHz, 0 failed blocks, 0 overloads.
- **Exclusive use:** taken ("held by process 25743, this app is 25743").
- **Plugging:** the Gryphon was pulled out while in use. The app wrote "the device in use is gone; moving to the default output" and went on; when the Gryphon came back the list showed it again and it was opened again.
- **Device volume:** not written into the report (it has no line of its own); the user reports it as working.
- **A fault found in 0.2, fixed in 0.3:** twice the report shows "block lasts 11610 microseconds" while the Gryphon ran at 48 or 192 kHz. 11,610 µs is 512 frames at 44.1 kHz: after the device was plugged in, the app took its rate from a list made a moment earlier, when the device still said 44.1 kHz, and set the plug-in up at that rate. The plug-in then ran at the wrong rate (too high in pitch) until the rate was switched by hand. 0.3 asks the device again at the moment it opens it. The engine helper (`alengine`) always did.
- **Zoom AMS-24:** not in the list in the first five reports, because macOS itself did not see the unit then. It appeared in the next report (below).

**AudioLab VST3 test 0.3**: https://github.com/Audio-lab-DAW/Audio-Lab-Pro-Alpha/releases/tag/native-lab-3

## The user's report on test app 0.3 (27 November 2026): the Zoom AMS-24 works

- **The AMS-24 appeared** as "ZOOM AMS-24 Driver" while the app was open, was opened, and played Serum 2: at 44.1 kHz with 512 and 128 frames, at 48 kHz with 128, at 88.2 kHz with 64 frames (0.73 ms). Exclusive use was taken on it. 0 failed blocks, 0 overloads on the Zoom.
- **Pulled out and put back twice** (the Zoom, then a change to the Gryphon): each time the app moved to the default output, said so, and opened the device again when it returned.
- **The 0.3 fix holds:** after each re-plug the block length in the report matches the rate the device was opened at (11,610 µs at 44.1 kHz, 333 µs at 192 kHz and 64 frames).
- **Gryphon at 192 kHz and 64 frames** (0.33 ms): 0 failed blocks. At 48 kHz and 64 frames with exclusive use, the device reported 1 overload in about 38,000 blocks.
- **The Zoom's own line** (from a later start with it connected): "ZOOM AMS-24 Driver" by ZOOM Corporation, USB; 2 outputs and 2 inputs; rates 44.1, 48, 88.2 and 96 kHz, and the rate can be set; buffer 27 to 4096 frames; 24-bit integer on the wire, 16 formats offered; exclusive use can be taken; **no volume the computer can set**.
- **What the two devices differ in**, which the engine and the app's settings must respect: the Gryphon has a volume the computer can set, the Zoom has none (its volume is the knob on the unit, so a "device volume" control must show "this device has none" there, as the test app does). The Gryphon goes to 768 kHz and 32-bit, the Zoom to 96 kHz and 24-bit. The Zoom has 2 inputs, the Gryphon none. The smallest buffer is 15 frames on the Gryphon at 48 kHz and 27 on the Zoom.

## The user's fourth report on test app 0.3 (27 November 2026), and test app 0.4 (task NL4)

The report: `tools/native-lab/reports/2026-11-27-test-app-0.3-report-4.txt`. The user's words: "I opened some VSTs and turned some knobs. I did notice I did not find Phase Plant, I think, next to VST test version, it would be nice for me to have a search function because I have a lot of VSTs."

What the report shows:
- **Phase Plant was found.** The scan lists "Phase Plant by Kilohearts, instrument, version 2.2.1" among 222 plug-ins (253 bundles, 32 that cannot load). The problem was finding it in a list of 254 lines with no search.
- **14 plug-ins loaded, none failed:** Pro-Q 3 and 4, Pro-R, Abyss, Timeless 3, Kick 3, Faturator, kHs Chorus, Melodyne, Neutron 4, OTT, Omnivocal Beta, Pigments, theTapeStop; 12 windows opened (Melodyne twice, at 812 x 600 and 1024 x 800). New figures: Faturator and kHs Chorus have about 2,086 parameters each (Kilohearts lists its MIDI-learn slots), Kick 3 3,087, Abyss 3,158; Faturator reports 38 samples of latency, OTT 2, Pigments 44.
- **Knobs turned, no line about them.** Test app 0.3 counted moves from a plug-in's window (the read-out "moves in its window") but **never wrote them into the report**. So the report could not say whether the moves arrived. That was the app's gap, not proof of a fault in the path. 0.4 logs them, and the build machine now shows the path working: drags in Surge XT's window reached the host as parameter moves (3 moves, 13 gestures begun and ended, last "A Filter Configuration = 0.57 (Dual 2)").
- **Pigments was silent (peak 0.000 over 595 blocks with the test pattern on).** Notes were sent (it was treated as an instrument, with a note input), and nothing in the app differs from the earlier report where Pigments **played at 44.1 kHz** through the same Bose speaker. The difference is the rate: this time the output was "Bose Mini II SoundLink (eqMac)" at **16,000 Hz** (the Bose in Bluetooth call mode, see the end of `docs/settings-research-audiophile.md`). So the silence is very likely Pigments not making sound at 16 kHz, not the app. On the build machine Surge XT and mda JX10 do sound at 16 kHz (peaks -5.6 and -3.7 dB), so silence at that rate is particular to some instruments. This is a likely explanation, not a proven one: it is confirmed only when Pigments sounds again at 44.1 kHz in 0.4.
- **theTapeStop's silence is expected:** it is an effect, and the test pattern was off while it was loaded, so nothing was fed into it.
- **The output ran at 16 kHz** through eqMac's copy of the Bose. Everything played lost all sound above 8 kHz.

What 0.4 changes (everything else as in 0.3):
1. **Search** above the list: filters as you type over name, maker and kind (instrument, effect, "cannot load"), any order of words, capitals and accents ignored (`SÜRGE XT` finds Surge XT). Cmd+F (also Edit > Find Plug-in) jumps to it, Escape clears it, Enter loads the selected match, the down arrow moves into the list. A kind filter (all, instruments, effects, cannot load), sort by name or by maker, or group by maker with a heading and a count per maker. "12 of 222" beside it (plug-ins that can load; the ones that cannot are counted apart). The last 8 plug-ins loaded stay on top, marked "recently loaded", kept between starts. The computer keys only play notes when the search field does not have focus.
2. **Parameter moves:** the host's component handler now counts performEdit, beginEdit, endEdit and restartComponent (and which of those said "all values changed"), and keeps the last parameter moved and its value. The read-out shows "moves in its window: N   notes sent: N". The report gets "[param] Pigments: first move from its window: …" at once, and when a plug-in is replaced or the app quits, "[param] Pigments: 37 moves from its window (gestures begun 12, ended 12), last: Macro 1 = 0.62 (62 %)". Clicks, drags and scrolls in the plug-in's window are counted too, so if the mouse was used there and nothing reached the host, the line says so plainly.
3. **Output warning:** when the chosen output runs at 16 kHz or less, a red line at the top and a `[warning]` line in the report. When the output is a Bluetooth device, or a device named after one (eqMac's copy), the line names call mode and gives the fix: choose another input in System Settings > Sound > Input, or quit the app using the microphone. The app follows the rate by itself when it comes back.
4. **Notes:** "[notes] Pigments: 48 notes sent (46 from the test pattern, 2 from the keys), output peak 0.000: SILENT although the notes reached it …", with the rate named when it is below 44.1 kHz. For an effect: how many blocks of test sound were fed into it, so "silent because nothing was fed" can be told apart from "silent although fed".

Tested on the build machine (virtual M1, macOS 15, run 45998343614, commit e58f1e8: this is the published build). A later commit (52e2af7) only rewords the silent-instrument hint ("some instruments" instead of "many") and lets the self test count drag moves after JUCE delivers them; its two runs were cancelled after 15 minutes without a Mac runner (the runners were busy), so the published zip still has the first wording. The next native-lab run with release on will carry it: the app builds and starts; search "SÜRGE XT" 2 of 2, "instrument" 1 of 2 (Surge XT), "effect" 1 of 2 (Surge XT Effects), "zzzz-nothing" 0 of 2; grouped by maker gives 1 heading; Surge XT loaded, its window opened, 45 notes sent, peak 0.187; the drags reached the host as moves. **Not tested:** anything by hand, the Bluetooth warning (the build machine has no Bluetooth device and runs at 48 kHz), and Pigments, Phase Plant or any paid plug-in.

**AudioLab VST3 test 0.4**: https://github.com/Audio-lab-DAW/Audio-Lab-Pro-Alpha/releases/tag/native-lab-4 (a pre-release; the desktop app's latest release stays v0.223.0).

What to try: search for Phase Plant, load it, turn a few knobs in its window, play the pattern, paste the report. Before that, take the Bose out of call mode (or pick the Gryphon), and load Pigments once more to see whether it sounds at 44.1 kHz.

## Stage N1: what was built (27 November 2026)

- **`alengine`** (`native/engine/`, about 500 lines of C++ with the bridge): a native program that owns the audio output. The app starts it as a helper and talks to it in one JSON object per line.
  - `devices`, `formats`: every device with its rates, buffer range, volume, and the formats it offers on the wire.
  - `open` with any of `uid`, `rate`, `buffer`, `exclusive`, `bits`, `integer`: opens a device, or moves to another one while sound plays.
  - `volume`, `mute`, `status`, `close`, `quit`.
  - Things that change outside arrive by themselves: `volume`, `rate`, `buffer`, `exclusive`, `devices`, `default-output`.
  - Sound comes in through a local socket as 32-bit float stereo and is handed to the device untouched (`ring.h`). Two clocks drift, so the ring corrects itself when it runs empty or too full, and counts each time.
  - When the device runs an integer format that the system does not mix, the engine writes the bytes itself (16, 24 and 32 bit, `sample_convert.h`).
- **`native/bridge/engine-bridge.js`**: the app's side, plain Node with nothing from Electron in it, so the desktop app's main process can use it as it is.
- **Test app 0.2**: rate, exclusive use, device volume both ways, device list that follows plugging.

## Stage N1: what was proven, and where

On GitHub's Apple Silicon machine (virtual M1, macOS 15), with the virtual loop-back device BlackHole standing in for the DAC. Run 45939789700, commit d63f144.

| Check | Result |
|---|---|
| Hand-over, fed by a test program | 287,998 of 287,998 samples came out of the device identical to what was sent (3 seconds of the web engine's own renders), no gap, nothing dropped |
| Hand-over, fed by Node through the bridge module in 128-frame pieces | the same: 287,998 of 287,998 identical, no gap. In an earlier run this check showed one gap of 1,456 samples together with one overload reported by the machine; the engine had received and passed on every frame |
| Open a device | 48 to 73 ms |
| Switch device while sound plays | 64 to 124 ms, sound running on the new device within 0.3 s |
| Sample rate | switched 48 to 96 kHz in 124 ms; the engine noticed the change by itself |
| Buffer | 256, 64 and 32 frames accepted |
| Volume | set to 0.5, read back 0.5; set by another program to 0.8, the engine was told at once |
| Exclusive use | taken; a second program could not start the device (system error 35) and got no audio |
| Checks without a sound card | 24-bit values survive unchanged, 16-bit dither is the same twice, full scale clamps, the ring keeps order and counts running empty and dropping; all pass on macOS and Linux |

On the user's Mac (stage 0, see `docs/native-mac-picks.md`): the same Core Audio layer drove Serum 2 through the iFi Gryphon at 32 frames for 170 seconds without a failed block.

## Stage N1: what is not proven

- 0.2's new controls were clicked by the user on the M4 (see the report above); the fix in 0.3 was confirmed in the user's next report.
- **The integer path** (the engine writing the DAC's own bytes) has only its arithmetic tested. No device on the build machine offers a format the system does not mix, so it never ran with sound. Whether the Gryphon's 60 formats include such ones, the engine's `formats` answer will show; the test app does not use that path yet.
- **Bit-perfect to a real DAC** cannot be shown without one. What was shown is that the engine's output equals its input sample for sample on a float loop-back device.
- **Drift over a long time.** The test lasted 3 seconds. Over minutes the two clocks drift; the ring then drops or waits once and counts it. A smooth correction (a resampler that moves by parts per million) is not built; it belongs to N2, where the web engine's clock meets the device's.
- Hot-plug was seen working on the user's Mac in the test app. The engine helper's own handling of it has not run on hardware.
- **Not inside the app.** `index.html` and `desktop/` were not touched. No setting in AudioLab uses the engine yet.

## Assumptions made (change any of them)

- The engine talks JSON lines over its standard input and output, and takes sound over a local socket. Shared memory would be a little faster; the socket needs no native add-on in the desktop app and passed the sample-exact test. It can be swapped later without changing the commands.
- The first hand-over is "exact, with rare corrections" rather than "always smooth": for listening through a DAC, untouched samples matter more than hiding one correction every few minutes.
- Exclusive use is released when the engine moves to another device or closes.
- This work was started in the session where the user said "yes continue" after the tests on their Mac, and is logged as `task NB-N1` so that task NB continues from N2 and does not repeat it.

## Stage N2a: the path from the desktop shell to the engine, proven outside the app (27 November 2026)

The risky part of N2 is not the settings page, it is the road the sound takes: out of the page's audio thread, through the desktop shell, into the engine, in time. That road was built as a small test program (`tools/native-lab/electron-tap/`) that uses the real shell (Electron 45.4.1, Chromium 156, the versions in `desktop/`) and does not touch the app.

How it works: an AudioWorklet in the page hands every 128-frame block to a message port. That port is moved into the worklet, and its other end into the shell's main process, so the blocks go **from the audio thread straight to the main process** and never wait for the page's own thread (which is busy drawing). The main process feeds the engine through `native/bridge/engine-bridge.js`.

Result on the build machine (run 45942655178), 20 seconds of a known signal, recorded at the loop-back device:

| The page's audio clock | Blocks that arrived | Page speed against real time | Ring ran empty | At the device |
|---|---|---|---|---|
| No output device at all (`sinkId: none`) | 7,500 of 7,500 | **0.59** | 79 times | 1,920,000 of 1,920,000 samples identical, in 80 pieces with silence between |
| Silence played into a real device, which gives the clock | 7,500 of 7,500 | **0.998** | 2 times (one is the end) | 1,917,384 of 1,920,000 identical; 5 gaps, with 4 overloads reported by the machine |

What this settles for N2:
- **The road works and keeps every bit.** Nothing was lost or changed between the page and the engine in either run. Moving the port into the worklet worked (the test has a fallback through the page thread; it was not needed).
- **A page with no output device cannot be the clock.** Chromium then runs the page's audio from a timer, and on the build machine that timer ran at 0.59 of real time. Whether it does better on the M4 is not known, and nothing should depend on it.
- **So in N2 the page keeps a real device as its clock** and plays silence into it, while the engine plays the sound on the chosen DAC. If both are the same device and the engine takes exclusive use, the page would stall; the page's clock device must then be another one (the Mac's own speakers are always there). This is a design decision made here; it is written down so it can be changed.
- **Two device clocks drift.** With the page on one virtual device and the engine on another, the ring's fill rose from about 4,900 to 10,000 frames in 18 seconds. Virtual devices on a shared machine say little about real ones, but the direction is the point: N2 needs the smooth correction (a resampler that follows the fill level), or the rare-correction mode with a roomy ring. Both ends are measured by the ring's own counters, which the engine already reports.
- **Sending blocks as transferred buffers does not work into the main process** (they arrive empty); sending them as copies does. A copy of 1 kB 375 times a second is nothing.

Not shown: any of this inside AudioLab, with its real master output, on a real DAC, or for longer than 20 seconds.

## Stage N2b: the clock follower and the bridge's pieces (27 November 2026)

**The clock follower.** N2a showed the page's clock and the DAC's clock drift apart. The engine's ring now has two ways of reading:

| Mode | What reaches the DAC | When |
|---|---|---|
| `exact` (default) | every sample as sent, bit for bit; when the clocks have drifted too far, one counted correction (a drop or a short wait) | the page and the engine share one device (one clock), and for listening to files later |
| `follow` | the sound read between the samples at a speed steered a few parts per million (a 48-tap windowed sinc); no gaps, no drops, not bit-perfect | the page's clock device is another one (with exclusive use on the DAC it must be) |

Measured in the engine's own tests (they run on Linux too): bit for bit at speed 1; error against the ideal -111.7 dB at 997 Hz and -116.8 dB at 15 kHz; over 5 simulated minutes against a sender 250 or 1,000 ppm off, never empty, never dropped, the fill within 20 ms of its 50 ms target, the speed settled on 254 ppm for a 250 ppm sender. The speed moves by up to about 50 ppm with the beat of the two block sizes: under a tenth of a cent, too slow and too small to hear.

**The shell's side** (`desktop/native-engine.js`): starts the engine only when the page asks, forwards its events, takes the sound from the page's audio thread and feeds the engine. If the engine crashes it is started again with the same device and settings (up to 3 times a minute), then the page is told to go back to the web engine. **The page's side** (`native/bridge/page-tap.js`): one function N2c copies into the app unchanged. **The preload** gives the page `audiolabDesktop.nativeEngine`.

Nothing of this is active in the app: the page never calls it yet, and the desktop build does not carry `alengine` yet.

**Proof on the Mac, waiting.** Workflow `native-engine.yml`, four cases with the real shell pieces on the loop-back device: A one clock, exact, bit for bit; B two clocks, follow, a clean sine; C two clocks, exact, as the contrast; D the engine killed while it plays and started again. On 27 November from about 12:36 UTC no macOS build machine was given to any run in the repository (queued 15 minutes then cancelled, or cancelled at once), so these have not run yet.

## Stage N3a: the engine core's first part, and the first family of devices (27 November 2026)

N2c (the hook in the app) still waits for the design chain, so this run started stage 3, which needs no `index.html` work: the native engine making the sound itself.

**What was built** (`native/engine/core/`, `native/engine/alrender.cpp`):
- **The device layer.** A device takes a stereo block of 128 frames and gives one back. Its settings are read with JavaScript's own rules (`p.x||default`, `p.x??default`, `p.x!==false`), from exactly the object the page posts to the web device, so the native side is given what the web side is given (`params.h`, `json_value.h`).
- **The worklet bundle's two hidden rules, repeated around every device** (`device.h`): after more than 3 seconds of exact silence a device stops and outputs zeros until sound returns; every 16 blocks, state values smaller than 1e-30 are set to exactly zero. Both change the output's bits, so a port without them cannot match. The check below proves it: with the silence rule removed 35 cases no longer match, with the tiny-value rule removed 36.
- **JavaScript's number rules** where C++ differs (`jsmath.h`): `Math.max` with NaN and signed zero, `Math.round`, the `>>` operator, the worklets' seeded `Math.random`, float stores into `Float32Array`. Built with `-ffp-contract=off`.
- **Five devices ported statement by statement** (`dev_dynamics.h`, `dev_crush.h`): Limiter (`al-limit`, true-peak look-ahead, three styles), Gate (`al-gate`, gate and expander, look-ahead, listen), Transient shaper (`al-trans`), De-esser (`al-deess`, split, wide, listen), Bitcrusher (`al-crush`). Their meter values are kept in the engine, so the interface can read them later (the engine keeps all state).
- **Chains and offline render** (`graph.h`, `alrender`): devices in series in 128-frame render quanta, the way a track's effects run in the web engine.

**How it was proven:**
- `tools/native-lab/make_ref_core.py` opens the real app (v0.229) in headless Chromium and, for each device, makes it the way the app does (`mkFx`), applies **every preset the app has for it** (98 presets), the settings a new device starts with, and 14 settings no preset uses (every style, mode and the listen switches), and renders a 6.5-second test signal with the app's own worklets: drum hits above full scale, a voice with sibilants and a slow level ride from -50 dB, a tail that fades into values below 1e-30, 3.3 s of exact silence, then hits again. Two chains (gate, transient shaper, crusher, limiter; de-esser, gate, limiter) are rendered too. 119 cases.
- `alrender` renders the same cases natively; `tools/native-lab/compare_core.py` compares every 32-bit sample.

| Where | Result |
|---|---|
| This build machine (Linux, x86-64, Chromium 158) | **119 of 119 bit for bit** |
| GitHub's Linux machine, run 46008664578 (Chromium 159) | **119 of 119 bit for bit**; its web renders are identical to the ones recorded here (119 of 119), so the reference does not depend on the Chromium version |
| The same with fused multiply-add allowed (the control) | 119 of 119 on x86-64 (that machine has no fused instruction by default); the Apple Silicon run will show whether the rule matters there |
| GitHub's Apple Silicon machine | waiting: no macOS machine was given to the run in this session (workflow `native-core.yml`) |

**Cost** on this build machine (a shared 2.1 GHz Xeon core): 2.7 to 7 microseconds per 128-frame block per device (a block lasts 2,667 microseconds at 48 kHz), so each device takes about 0.1 to 0.4 % of one core; the four-device drum chain 17 microseconds. The M4 will be faster; the web engine's cost for the same devices was not measured in this run.

**Not proven yet:** the Mac (Apple's maths library for `exp`, `pow`, `log10`, `sin`, `cos` against Chromium's; Test A in NM1 found them equal for the Bitcrusher); other sample rates than 48 kHz; settings changed while sound plays (the web engine applies them at the next block, the core does the same, but no test moves a dial during a render yet); anything you can hear, because the core is not connected to the output or the app.

**Assumptions:** the core takes the settings the page posts to the worklet (after the device's `sp` mapping), not the app's own device settings; the mapping moves into the engine when the interface starts driving it (N2c and later). A device whose input has no channels at all (the web engine's disconnected input) is treated like silence; the web worklet then leaves its output untouched, which only differs before the 3-second rule takes over, and no track in the app runs a device with no input connected.

## Stage N3b: the mixer, bit for bit (27 November 2026)

What the app's export does with a track after its devices: a volume (Chromium's GainNode), a pan (StereoPannerNode), all tracks added into the master, the master's gain. Ported in `native/dsp/al_mix.h`, put together in `native/engine/mix/` (renderer `almix`), and compared with the app itself: `tools/native-lab/make_mix_ref.py` builds each scene in the real app page exactly as `renderMix` does, `run_mix.py` compares every 32-bit sample.

**10 of 10 scenes identical** on Linux: one track; two; five at pans from hard left to hard right; mono tracks; mono and stereo mixed at 128 frames; a track at volume 0; the Bitcrusher in a track alone, dry, and with another track at 512 frames (the export's size); two dithering Bitcrushers on two tracks at 128.

What it took, found by comparing (each of these changes the last bit, so a port without them is not the same sound):
- The panner has two paths. In the first block (where the value was set) it works in double; after that its gains are stored as float and the products and sums are float.
- On the fixed path the sum `pan + 1` is done in float before it becomes an angle: at pan -0.2 that is 0.800000012 instead of 0.799999997.
- A volume of 0 writes true silence (not "minus zero").
- Chromium always renders whole blocks and cuts the end afterwards; a device that draws random numbers draws them for the frames past the end too, which changes what the next device gets.

**Found on the way: the web engine's own export is not always the same bits.** Rendering the same scene twice in the app gave different results for the five-track scene (10,465 samples differed) and for the two dithering Bitcrushers (17,912). Chromium keeps the connections into a bus in an order that changes between renders; the order decides how float sums round and in which order devices draw random numbers. Every other scene came out the same twice. The native mixer takes the order as a setting, and for each web render there is an order that reproduces it bit for bit (`run_mix.py` finds it). So "the same as the export" is exact for one or two tracks per bus; with three or more tracks, or random-drawing devices on several tracks, the web engine itself differs from render to render at about -140 dB, and the native engine matches one of its renders exactly. The native engine always uses project order, so its own renders are always the same.

Not yet: sends, groups, returns, the master's devices and limiter, volume and pan that move (automation, the 10 ms smoothing in live play), other sample rates. The Mac check is in `native-engine.yml` and waits for a build machine like the others.

## Stage N3c: the modulation and time family, the browser's maths, any buffer size (27 November 2026)

(Two NB runs worked at the same time this afternoon. This part is called N3c; the mixer's next part, sends, groups and returns, which N3b's run named N3c, is **N3d** below.)

**Five more devices ported** (`native/engine/core/dev_modulation.h`): Chorus (`al-chorus`: chorus, flanger, ensemble, dimension, triangle or sine), Stereo imager (`al-imager`: four bands in Linkwitz-Riley filters, width per band, mono bass, solo), Frequency shifter (`al-fshift`: shift up or down, ring, both, LFO, feedback), Vocoder (`al-voc`: 4 to 32 bands, chords, saw, pulse, square or sine carrier, noise, sibilants, formant), Tape stop (`al-tstop`: tape stop, half time, double, reverse, stutter, in time with the transport). **Devices native: 10 of 42; instruments: 0 of 32** (see "Port debt" below).

**What it took to give the browser's bits.** The first comparison gave 231 of 240. The rest were all one cause, found by measuring the browser itself (`tools/native-lab/math_probe.py`, `almathprobe`):
- The browser's `Math.sin`, `Math.cos`, `Math.exp` and `Math.log10` are not the system's. V8 15.8 (Chromium 158) takes them from **LLVM's libc**, correctly rounded. Over 400,000 arguments of the kinds the devices use, glibc's `sin` and `cos` differ from the browser's on 0.15 %, `exp` on 0.07 %, `log10` on **21 %**; Node's older V8 on about 3 %. The engine now carries the same LLVM functions (`native/third_party/llvm-libc/`, header only, 143 files, Apache 2.0 with LLVM exception): **0 differences** on all 400,000.
- `Math.pow` is the exception: V8 handles `x**2` and `x**0.5` itself and otherwise calls the **system's own** `pow`. So the engine does the same (`js::pow`), which on the Mac means Apple's, as in the desktop app there.
- The differences showed up in a way worth knowing: the frequency shifter's feedback dying away in silence gave samples that were 0 in both, with the opposite sign. A first guess (the browser flushes tiny numbers to zero) was wrong: with flushing every device broke, so Chromium's worklets keep them, and the engine must too.

**Any buffer size, the same bits.** The web engine's worklet bundle keeps two rules per render quantum (128 frames): the 3-second silence rule and the tiny-value guard every 16 quanta. Run at the audio device's own buffer (32 or 64 frames), a device would apply them at the wrong frames. `WorkletShell` now keeps them on the web engine's grid in sample time, whatever the call size: silence decided per quantum (if sound arrives inside a quantum that started silent, the silent frames are run through the device first, so its state is exactly the web engine's), the guard after every 16th quantum, `currentTime` of the quantum for the tape stop. No frames are held back, so this adds no latency. This is the review's (RN5) decision D4 and RN1's point 5, settled by measurement:

| Frames per call | Cases bit for bit |
|---|---|
| 128 (the web engine's) | 240 of 240 |
| 1, 7, 32, 64, 100, 512, 4096 | 239 of 240 each (see the export's quantum below for one more case) |

The one exception is `chain-robot` (vocoder, tape stop, Bitcrusher): two devices that draw random numbers in one chain. In the web engine all worklets of a song share **one** random stream (`Math.random` in the worklet scope), handed out in Chromium's render order, quantum by quantum. At other call sizes the two devices take their numbers in a different order. A single device draws the same numbers at any call size. This is the review's blocker A2; its fix (one stream per device, decision D2) needs your yes and a change in the web engine first (below).

**The export's quantum.** The app's export renders in 512-frame quanta (`renderSizeHint`), so the bundle's rules fall on a 512 grid there and the export sounds slightly different from playback in the same places. The grid is now a setting of the render (`RenderContext::quantum`, `"quantum"` in a case file), and `make_ref_core.py` can make references at 512. Measured:
- **156 of the 240 web renders change** between quantum 128 and 512: the quantum is part of the sound, as the review said (A4).
- At quantum 512 called in 512s: **240 of 240 bit for bit.**
- At quantum 512 called in pieces of 128 or 32: 209 of 240. Every difference but the random-stream chain sits in the 256 frames between the start of the quantum and the return of sound after more than 3 s of silence (my test signal; at the 128 grid its sound returns exactly on a quantum boundary, so this showed only at 512). There the web engine computes the silent frames and outputs leftovers of at most 1.5e-12 (236 dB under full scale); a live engine has already sent zeros for them, because it cannot know sound is coming without waiting. From the next frame on the state is the web engine's again.
- So: **an export runs in whole quanta and is exact; live play at any buffer is exact except for those leftovers** (and two random-drawing devices in one song, D2).

**Floating-point state (review A6, A7).** `-ffp-contract=off -fno-fast-math` now hold for the whole native tree, not target by target. Every chain sets the web engine's float state when it starts (round to nearest, tiny numbers kept: FTZ and DAZ off on Intel, FZ off on ARM) and puts the caller's back, so a plug-in that leaves flush-to-zero on cannot change AudioLab's devices.

**Checked by:** `tools/native-lab/make_ref_core.py` (the app in headless Chromium: every preset of the ten devices, extra settings for every mode, four chains; 240 cases), `alrender`, `compare_core.py`; `tools/native-lab/wl_node.js` (runs the app's worklet bundle in Node, to trace a difference statement by statement); workflow `native-core.yml` now also runs the maths probe, call sizes 32 and 64, and the system-maths control. **GitHub's Linux machine, run 46014683118 (Chromium 159): 240 of 240 bit for bit; maths probe 0 differences for all five functions; 239 of 240 at 32 and at 64 frames; 231 with the system's maths; its web renders identical to the ones recorded here.** On the Mac: queued, no machine yet.

## Review fix NB-R1: native CI on every push (27 November 2026)

**Built.** `.github/workflows/native-ci.yml`, started by every push that touches `native/`, `desktop/native-engine.js`, `desktop/preload.js`, `tools/native-lab/` (and by hand, with a box for the Apple Silicon job):
- **linux**: every native target in Release and with ASan + UBSan; `alengine selftest` in both; the ring under two real threads (`alringstress`, new, `native/tests/ring_stress.cpp`: a writer and a reader thread with wandering block sizes; exact mode checks that every sample is the next one sent except after a counted drop or underrun, follow mode that no frame is torn); the mixer's 10 scenes; all 240 device cases against the web engine rendered fresh in headless Chromium (Release at 128 frames, sanitizers at 128 and at 7 frames per call).
- **tsan**: the ring stress under ThreadSanitizer, 10 seconds per mode.
- **node**: syntax of every bridge file, and `tools/native-lab/bridge-unit/bridge_unit.js`: the shell's side of the bridge (`desktop/native-engine.js` with `native/bridge/engine-bridge.js`) driven through a fake Electron against a stand-in engine (`fake-alengine.js`, same JSON lines, a real socket). 27 checks: one engine for two starts at once, what the page may not send (`quit`, `source`, `selftest`), options cannot change the command, bad numbers fall back, every frame of 100 worklet blocks reaches the engine, killed three times it comes back with the same device and sound settings, the fourth time `gave-up`, a requested stop is not a crash, quitting the app stops it, an engine that always dies gives up after 3, a hung engine is killed.
- **mac** (by hand): the same build, selftest, ring stress (also under clang's TSan), mixer and bridge checks on Apple Silicon.

**Proven** (run 46016736940, GitHub's Linux machines, all four jobs green): selftest ok in both builds; ring stress ok (exact: 0 wrong samples, 0 torn; follow: 0 torn), no TSan report; mixer 10 of 10 identical in both builds; devices **240 of 240** (Release), **240 of 240** (sanitizers, 128 frames), **239 of 240** (sanitizers, 7 frames: the known pair of devices sharing the worklets' one random stream, D2); bridge 27 of 27.

**Found and fixed on the way.**
- A helper that never says "ready" stayed running behind the app after the start gave up: `engine-bridge.js` now kills it (found by the unit test).
- `run_mix.py` failed with a relative path to `almix` (the renderer runs inside `ref/mix`); `native-engine.yml`'s macOS step had the same fault and would have failed its first Mac run. Both fixed. Summary steps no longer fail when a result file is missing.
- UBSan flags a left shift of a negative number in the vendored LLVM libc (`log_range_reduction.h`): defined behaviour from C++20 and in every compiler used here, so CI leaves that one check out instead of changing vendored code.

**Not proven.** The macOS compile of N2b and its cases A to D: `native-engine.yml` was dispatched again (run 46016748702) and was still waiting for a Mac when this run ended. That is D9 (a Mac to build on): until a runner exists, only your Mac proves the Mac.

## The research and the review, folded into the stages (27 November 2026)

The scheduling chat asked to fold RN2 (Windows), RN3 (lessons), RN4 (native screens) and RN6 (testing, licences, distribution) into the stages, and RN5 (the independent review, `docs/review-native.md`) when it landed. What changes, and what moved:

**Decided and done in this run**
- Block size (RN1 point 5, RN3 D4, RN5 A4/D4): the 128-frame grid in sample time, see N3c. Proven, no latency added.
- The maths library (RN5 A5): the engine carries V8's own functions. **The reference moves when Electron's V8 changes them**: references record the browser version (`web.json`); a change is re-baselined only with a reason line (RN3 RL2).
- Float flags and state (RN5 A6, A7), done.

**Waiting for your decision (each also in `docs/review-native.md` section 5)**
- **D2, one random stream per device.** Without it, devices that draw random numbers (Bitcrusher with dither or jitter, vocoder noise, later the instruments) are bit-identical alone but not with each other, and multicore is ruled out for them. It is one deliberate sound change in the web engine (an `index.html` task, versioned). Until you decide, the engine keeps the shared stream for single-threaded renders, as N3b does.
- **D3, the reference is a single-pass render in the shipped Electron on the Mac,** not headless Chromium 158 on Linux and not the chunked export. The engine side is ready (any quantum, any call size); the reference script needs Electron on the Mac runner.
- **D6, Fractals v10 as the first native build's song (your pick U5b):** RN6 found the vocals are cut from Electric Universe's commercial recording and v7 to v10 take riffs from its stems. **N7 will not put v10 in the DMG until you decide** (QL1): v6 without the original vocals, a new song, or written permission.
- **D9, a Mac to build on.** Every macOS run of this task today waited and was cancelled. A self-hosted runner on your Mac mini (free while it is on) or GitHub's paid larger runners would end that; until then the Mac proofs keep waiting and your test builds are the only Mac evidence.
- **D7, the ASIO agreement (RN2, W0):** send it now if Windows matters; replies take weeks.

**Moved into the stages (from RN3's RL list and RN5's NB-R list)**

| Stage | Now includes |
|---|---|
| N2c (the hook) | the rate contract (NB-R2: the page and the engine agree on the sample rate or refuse), the sound path off the shell's main thread (NB-R3), engine hardening (NB-R4), follower quality (NB-R5), CI on every push for `native/` with sanitizers (NB-R1 **done on Linux**, RN6 QL6); the native engine stays a setting with the web engine as fallback until stage 3 ends (RL6) |
| N3 (engine core) | NB-R6 rules (the grid, float flags and state: done; per-device random streams after D2); the state and edit protocol design (NB-R7) before the bridge carries edits; reference songs compared web against native after every engine change (RL2); a one-hour soak per engine change and a weekly eight-hour one (RL12, NB-R10); RealtimeSanitizer on the audio path when the Mac runner exists (RN1, QL6) |
| N3 order | N3d the mixer's sends, groups, returns and the master's chain (N3b's run); then the remaining worklets (the FFT family: pitch shifter, pitch corrector, resonance suppressor; the delays, voice, ducker, loudness); then the worklet instruments; then the browser-node devices with a measured tolerance each (NB-R11); a check-point after 30 port tasks against the estimate, with a JUCE or Tracktion review if over by half (RL9). Stage 3 is done when "Fractals plays wholly native" holds, not by count (RL9) |
| New, before N4 | **project safety**: `minReader` beside `formatVersion` and a loader that reads it, a placeholder device that keeps a missing plug-in's bytes, atomic saves with rotating backups, start with plug-ins off after a crash (RL1, RL4, NB-R9); **projects out of browser storage** into real files before any change to the desktop app's identity (RL1b). Both need `index.html` work in turn |
| N4 (VST3 in the app) | host hardening (NB-R8: module cache, scanner with a deadline, FPCR saved and restored around every plug-in call), the plug-in corpus run after every host change (RL3, QL8); no second plug-in format until the VST3 corpus and your U3 self test pass twice (RL9) |
| N7 (packaging) | third-party notices including LLVM libc now (QL2), no silent calls to Google Fonts or CDNs (QL3), **signed updates** (Ed25519) before the native build reaches anyone else (QL4), a stable self-signed identity so the microphone permission survives updates, and the App Translocation warning (QL9); the fresh-install song waits for D6 |
| Windows (after the engine has moved) | WASAPI exclusive first, then shared and low latency, ASIO after the agreement; power-throttling and timer opt-out, MMCSS, P-cores; plug-in host defences (RN2 section 9.2, N-W1 to N-W10) |
| Stage 4 | "AppKit with Metal" is superseded until question R2 is asked again (RN5 D8); RN4's route: stay on the web interface, move heavy surfaces to a GPU scene layer that can be ported (U0 to U3), decide at a measured gate. Not NB work; the engine keeps all state for it |

**Bridge parts and when they go (RN3 D5):** the socket, the ring and the page's clock device (N2), the clock follower (N2b) and the page tap: all removed when the native engine makes the whole sound (end of stage 3).

**Port debt (RN3 RL10):** devices native **10 of 42**, instruments **0 of 32**, the mixer: tracks, volume, pan and master (N3b). The rule that every task adding a device to `index.html` also adds it to the port list touches other tasks, so it is yours to set.

## Next: N2c, and why it was not started here

N2c puts the engine under the app: copy `alNativeTap` into `index.html`, Settings > "Native output" (device, rate, buffer, exclusive use, device volume both ways, the switch back to the web engine), `alengine` built into the desktop app. The design chain still has `index.html` work queued and the user's order is design first.

## Earlier note: N2, and why it was not started in N2a

N2 puts the engine under the app: the desktop shell ships `alengine`, the page sends its master output to it, the web engine's own output goes silent, and Settings gets "Native output" with device, rate, buffer, exclusive use and volume. That needs a hook in `index.html` and changes in `desktop/`. Other tasks (the design chain) are working in `index.html`, only one task may edit it at a time, and the user's order was "first finish all the complete new design, and then build the native engine". So N2 is left for task NB, fired in its turn.
