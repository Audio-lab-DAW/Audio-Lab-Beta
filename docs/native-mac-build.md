# AudioLab native Mac: the build, stage by stage

The running list of the native Mac work (task NB). Plan: `docs/native-mac-plan.md`. The user's picks and the reports from their Mac: `docs/native-mac-picks.md`.

## Where it stands

| Stage | What | State |
|---|---|---|
| 0 | The proofs: one effect bit for bit, a VST3 host, the test app | done (task NM1), proven on the user's Mac |
| N1 | Native audio output and device control, as a helper the app can talk to | **done as a helper and proven on the build machine; not yet inside the app** |
| N2 | The bridge: the app sends its sound to the engine, with a switch back | **N2a done**: the path is proven outside the app. **N2b built**: the clock follower (proven in the engine's own tests), the shell's side and the page's side of the bridge, crash recovery; the Mac proof (cases A to D) is written but waits for a macOS build machine. **N2c** (the hook in `index.html`, the settings, `alengine` in the desktop build) waits for the design chain |
| N3 | The engine core, devices ported family by family | **N3a done**: the core's device layer, chains and offline render; the dynamics family (limiter, gate, transient shaper, de-esser) and the Bitcrusher, **119 of 119 cases bit for bit** against the web engine (every preset) on Linux, here and on GitHub's Linux machine; the Apple Silicon run waits for a build machine. **N3b built**: the mixer (track volume, pan, the master, tracks summed) from Chromium's arithmetic, **10 of 10 scenes bit for bit** against the app's own export path on Linux, including the Bitcrusher in a track at 128 and 512 frames. **N3c done**: five more devices (chorus, stereo imager, frequency shifter, vocoder, tape stop), the browser's own maths functions carried by the engine, **240 of 240 cases bit for bit**; the same bits at any buffer size from 1 to 4,096 frames on the web engine's grid (exceptions measured and explained), the export's 512 quantum. Devices native: 10 of 42. Next: N3d (sends, groups and returns; the mixer's tracks run the core's chains) |
| N3d | The mixer's sends, groups, returns and the master's chain | **in progress** (claimed 27 November 19:18 UTC by an NB run; a second NB run should take another step) |
| R7 | Review fix NB-R7: the state and edit protocol (review A10) | **done on Linux** (task NB-R7): the design (`docs/native-state-protocol.md`) and a working prototype on both sides: the engine keeps an exact copy of the project, the page sends each change as a small numbered edit that carries its own undo, the engine checks every edit and refuses one that does not fit, both sides compare a 64-bit hash. Proven with 1,000 random edits and undos on each built-in song (Fractals, the Psytrance demo, Shrine Legion): page and engine equal after every step, with the app's own undo and with the engine's. Also: edits overtaken by the engine's own change, lost lines, an engine restart, damaged save files. Nothing changes in the app yet; the hook goes in with N2c |
| R5 | Review fix NB-R5: the clock follower's quality | **done on Linux** (task NB-R5): when the engine follows the page's clock it is now flat to 20 kHz at 44.1 kHz (it took 4.2 dB off 20 kHz before), bit for bit at speed 1, learns a clock 1,000 ppm off in about a minute instead of more than five, and holds through a 25 ms stall each second without running empty. The default safety margin is 40 ms (was 30 ms, which those stalls emptied). The status now shows the worst stall and the lowest fill, so the settings page can choose the margin from measurements. Cost 0.6 % of one core's time per block. Only affects the 'follow' clock mode; 'exact' is unchanged |
| R4 | Review fix NB-R4: engine hardening | **R4a done on Linux** (task NB-R4a, `alengine` 0.5): bad samples (NaN, infinity, past full scale) never reach the DAC; the DAC's volume moves in a ramp and never louder than it has been without your yes; a format change from outside restarts the stream; dither off; every number checked; request numbers and a protocol number. Tested on the null device (43 checks, also under the sanitizers). **R4b done on Linux** (task NB-R4b, `alengine` 0.6): the engine keeps taking sound and commands when the app stops reading what it says (before, only 12,032 of 72,064 frames got in over 6 s in that case; now all of them in 1.4 s); a format change no longer waits on the system's listener thread; a race between the format restart and `status` that ThreadSanitizer found is fixed; a file at another rate than the device is refused; the page can no longer confirm a louder DAC volume by itself: the app asks you in its own dialog. 50 checks on the null device in all three builds. The Core Audio format listener is still compiled by no machine (D9) |
| R3 | Review fix NB-R3: the sound path out of the shell's main process | **done, proven with the real Electron shell on Linux** (task NB-R3): the page's sound goes to a small helper process (the feeder) that only writes it into the engine, with a bounded queue and back-pressure; a watchdog replaces a feeder or an engine that stops answering (3 s); with the main process blocked 50 or 250 ms every second every frame arrived bit for bit with no gap, where the old path made gaps; `alengine` 0.4 no longer stalls a source switch on a frozen sender. The Mac waits for D9 |
| R2 | Review fix NB-R2: the rate contract, the source hand-shake, the engine off the Mac | **done on Linux** (task NB-R2): the page must say its rate and the engine refuses any other; a device that changes rate goes silent, tells the page and resumes when the rate comes back; source switching without the 30 ms sleep (review C1, C2, C5); the engine now runs everywhere on a null device and is tested end to end on every push (24 checks, also under ASan, UBSan and TSan). The Mac build of this code waits for a Mac runner (D9) |
| R1 | Review fix NB-R1: native CI on every push | **done on Linux** (task NB-R1): workflow `native-ci.yml` builds every native target normally and with AddressSanitizer + UndefinedBehaviorSanitizer, runs the engine's selftest, the ring under two real threads (also under ThreadSanitizer), the mixer's 10 scenes and all 240 device cases against the web engine (green: 240 of 240, sanitizers 240 of 240 at 128 frames, 239 of 240 at 7 as known), and 27 bridge checks against a stand-in engine. The Apple Silicon part waits for a Mac runner (D9) |
| N4 | VST3 in the app | host layer and scanner exist from stage 0, the test app is at 0.5; **Pigments sounds on the user's Mac** (report 6), Phase Plant not played yet, Pigments' knob moves not reaching the host (task NL6 next) (task NL5: the host now gives the controller the processor's state and delivers messages between the two from any thread, the gap most likely behind the silent Phase Plant and Pigments; a silence probe and [diag] lines measure it on your Mac); not in the app |
| N5 to N8 | Recording, export, packaging, polish | not started |

## What you can try now

Test app 0.5 (task NL5, below): load Phase Plant and Pigments, play the pattern on the Gryphon at 44.1 kHz, paste the report. Stages N2b to N3c change nothing you can hear or click yet.

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

## The user's fifth report on test app 0.4 (27 November 2026, 18:04 Brussels), and test app 0.5 (task NL5)

The report: `tools/native-lab/reports/2026-11-27-test-app-0.4-report-5.txt`.

What it shows:
- **Search works**: Phase Plant was found and loaded (Kilohearts 2.2.1, 2,174 parameters, 251 ms, its window 1259 x 642).
- **Knob moves reach the host**: 1,428 moves from Phase Plant's window, gestures begun and ended 4 and 4, last "Lane 2 > Gain = 0.83 (+3.61 dB)".
- **Phase Plant stayed silent**: peak 0.000 on the iFi Gryphon at 48 kHz (63 notes) and at 44.1 kHz (80, then 113 notes), 0 failed blocks, about 96 microseconds per 512-frame block. Pigments was silent the same way in report 4. So the 16 kHz explanation from report 4 is wrong at least for Phase Plant: the rate was fine here.
- **The Gryphon** was off at the start (not in the [device] list), appeared during the scan and the app switched to it by itself, but 0.4 wrote no [device] line for a device that appears later.
- **32 bundles are Intel-only**: Output's Arcade, Black, Boost, Brass, Clone, Duck, Hatz, Infiltrator, Minipol, PitchMonster, Shaper2, Tantrum, Tapex2, Texture, Transient Master, Vybz, Midnight Mirage, and all 14 RX 9 plug-ins. **One is broken**: helisert_6.0 ("Could not create Bundle").
- **Mojibake**: "12‚ÄØ%" and "‚àí3.26‚ÄØdB" are a narrow no-break space and a minus sign, written as UTF-8 by 0.4 and read as Mac Roman.

### The cause found for the silent instruments (by reading the code against the SDK and JUCE, then measuring)

0.1 to 0.4 set plug-ins up through the VST 3 SDK's helper `PlugProvider`. Checked line by line against JUCE's VST3 host (`juce_VST3PluginFormatImpl.h`) and the SDK's own sources, two things differ, and both matter only for plug-ins whose processor and controller are separate objects that talk to each other, which is how Kilohearts and Arturia build theirs (JUCE-built plug-ins such as Surge XT and Serum share one object, which is why they always sounded):
1. **The controller was never given the processor's state.** `PlugProvider` initialises both halves and connects them, but never calls `IEditController::setComponentState`. JUCE does it right after connecting (`synchroniseStates`). A plug-in whose controller loads the start patch and hands it to the processor on that call never gets a patch into its processor.
2. **Messages between the two halves were dropped unless they came from the main thread.** `PlugProvider` connects them through the SDK's `ConnectionProxy`, whose `notify` says "We discard the message if we are not in the UI main thread". JUCE connects the two directly. A plug-in that prepares its patch on a loader thread and sends it from there loses it.

The bus set-up, process data, events and process context were also checked against the list in the task (arrangements before `setActive`, main output and event input active, aux outputs off but given buffers, `setupProcessing` with the real rate and largest block, `setProcessing(true)` after `setActive(true)`, buffers for every output bus, note-on on channel 0 with velocity 0 to 1 and a matching note-off, offsets inside the block, tempo, time signature, project time and the playing flag, `kSample32`, the main thread's run loop turning): 0.4 already did these, except that it set up the buses before `setupProcessing` (the validator and JUCE do it after), forced stereo on the main buses, and activated only the first event input. 0.5 follows the validator's order and the plug-in's own preferences there too, but nothing found there explains a silent instrument.

**What is proven and what is not.** The two gaps are real (the code shows them). That they are what silences Phase Plant and Pigments is the most likely explanation, not yet proven: neither plug-in is on the build machine (both are paid; Kilohearts' free plug-ins and Phase Plant's trial come only through the Kilohearts Installer with a signed-in account, which a build machine cannot do lawfully). To prove the mechanism, 0.5 brings a small test instrument, **AL Strict Synth**, built to behave the way we suspect: it only sounds after its controller has been given the state and has sent the patch from a loader thread. And to prove it on your Mac, 0.5 measures it there (below).

### Built (0.5)
1. **The host** (`native/host/vst3_format.cpp`): its own set-up instead of `PlugProvider`: component and controller created and initialised, the component handler set, the two connected through counting links that deliver messages from any thread (as JUCE), then `setComponentState` with the processor's state. Then `setupProcessing`, `setBusArrangements` with the arrangements the plug-in prefers (read back and logged), main buses on (aux buses off, still given buffers), every event input on, `setActive(true)`, `setProcessing(true)`. Process context with system time and bar position as well. `HostOptions` holds each of these choices, so each 0.4 behaviour can be switched back one at a time.
2. **Diagnostics** ("Diagnostic lines in the report", on by default): `[diag]` lines per plug-in with the buses it offers (name, main or aux, channels, default on or off), the arrangements it prefers and what it now has, the result of every call (initialise, connect, setComponentState, setupProcessing, setBusArrangements, each activateBus, setActive, setProcessing), the buffers given; and at the summary: blocks in which the plug-in's own main output held sound (measured before the app copies or halves it), other output buses, silence flags it set, process() results, notes handed over and refused, parameter changes, and the messages between its halves (to each side, from other threads, dropped).
3. **"Why silent?"** (and by itself once, when you stop the pattern and an instrument stayed silent): loads the plug-in again in a separate process and plays 2 s of the pattern under nine set-ups: the 0.5 host, the 0.4 host, and 0.5 with one thing changed (no state given to the controller; off-thread messages dropped; buses as in 0.4; unique note ids; every audio bus on; transport stopped; its first factory preset). One `[probe]` line each (sound or silent, peak, blocks with sound, messages) and a one-line conclusion. The same on the command line: `alvst3 diag`.
4. **Factory presets**: the plug-in's program list (through `IUnitInfo` and its program-change parameter) and `.vstpreset` files in the standard folders, in a menu. Phase Plant and Pigments keep their presets in their own windows, so the report says to choose one there; a `[state]` line says when the plug-in's state changed size since loading (a preset was loaded).
5. **`[device] appeared:`** a line with the same details for a device that is switched on or plugged in after the start.
6. **At the end of every report**: `[rosetta]` the Intel-only bundles ("These need Rosetta: a helper comes later") and `[broken]` the ones that could not be read.
7. **`[clap]` and `[au]`**: the CLAP folders (`~/Library/Audio/Plug-Ins/CLAP`, `/Library/Audio/Plug-Ins/CLAP`) and the Audio Units folders (`Components`) listed, not loaded: counts, Apple Silicon or Intel-only, kinds (from the Audio Unit's Info.plist) and names, for decision D5.
8. **The report in ASCII**: narrow and no-break spaces become spaces, the minus sign and dashes a hyphen-minus, and so on; if anything outside ASCII is left (an accented name), the file starts with a UTF-8 byte order mark.
9. Everything else as in 0.4 (search, knob moves, the Bluetooth warning).

Code: `native/host/vst3_format.cpp` (host), `native/host/diag.cpp` (probe, [diag] text, the CLAP and AU listing), `native/host/plugin_api.h`, `native/host/cli.cpp` (`alvst3 diag`), `native/testapp/main.mm` (the app), `native/testapp/strictsynth/` (the test instrument, built only for the tests), `.github/workflows/native-lab.yml`.

### Tested
Build machine: GitHub's `macos-latest` runner (virtual Apple M2 Pro, macOS 26.7.2), run 46041572291 on commit 141af31 (main with this task's commit 0e3bb3a): this is the published build. The `macos-15` run queued for 12 minutes without a machine and was cancelled once `macos-latest` started; the `macos-14` run was cancelled by GitHub at once. Also on Linux here (`alvst3 diag`, normal and under AddressSanitizer + UndefinedBehaviorSanitizer: no errors).
- **AL Strict Synth** (the test instrument) at 48 and 44.1 kHz: 0.5 host SOUND (-8.0 dB, sound in 188 of 188 blocks, 1 message from its loader thread delivered); 0.4 host SILENT (0 of 188); 0.5 without the state given to the controller SILENT; 0.5 with off-thread messages dropped SILENT (1 message dropped); buses as in 0.4, unique note ids, every bus on, transport stopped: all SOUND. Conclusion line: "the 0.4 host's set-up was the cause ... Silent again with: 0.5 without giving the controller the processor's state; 0.5 but messages from other threads dropped". The same in the app itself: loaded, 47 notes, live peak 0.200 ("it sounded"), and the same probe from the app's child process.
- **Surge XT**, **mda JX10**, **Note Expression Synth** (48 and 44.1 kHz): sound under all nine set-ups (nothing broken by the change; Surge's controller answers setComponentState with "not implemented", which is allowed).
- **The app** with Surge XT: search, grouping, load, window, 47 notes, peak 0.192, drags reached the host (3 moves, 13 gestures), [diag] lines, the probe from a child process (all nine set-ups sound), `[state]` line, `[clap]` 2 bundles and `[au]` 2 bundles listed with names and kinds (Surge's CLAP and Audio Unit copied there by the workflow).
- **Report encoding**: the strict-synth report is pure ASCII (no BOM); the Surge report starts with EF BB BF because its self-test search "SÜRGE XT" is written into it.
- Pre-release `native-lab-5` published; the latest release is still v0.223.0 (checked after publishing).

### What only your Mac can prove
Whether Phase Plant and Pigments now sound, and if they still do not, which of the probe's set-ups (if any) makes them sound. The `[probe] ... conclusion:` line says it in one sentence.

**AudioLab VST3 test 0.5**: https://github.com/Audio-lab-DAW/Audio-Lab-Pro-Alpha/releases/tag/native-lab-5 (a pre-release; open it once with Open Anyway as before).

What to try: choose the Gryphon at 44.1 kHz, load Phase Plant, open its window, play the pattern ten seconds, stop it; the same with Pigments; if either stays silent, wait for the [probe] lines (10 to 40 s), then choose a preset in its own window and play again. Paste the report.

## The user's sixth report, on test app 0.5 (27 November 2026, 20:12 Brussels): "works well"

The report: `tools/native-lab/reports/2026-11-27-test-app-0.5-report-6.txt`.

What it shows:
- **Pigments sounds now.** Loaded in 3.5 s (4,365 parameters, 128 programs through VST3, latency 44 samples), `setComponentState` = ok, 155 notes from the pattern, sound in 2,854 of 3,468 blocks, peak -13.4 dB, on the Bose and then on the iFi Gryphon at 44.1 kHz. Average 0.69 ms per 11.6 ms block (5.9 %), worst 1.69 ms (14.6 %), 0 failed blocks, 1 overload reported by the device (at the switch to the Gryphon). In reports 4 and 5 it was silent with the 0.4 host: the 0.5 host's set-up (state given to the controller, messages from any thread) is what fixed it. The "Why silent?" probe never had to run.
- **Phase Plant was not played this time** (0 notes sent, its window open, `setComponentState` = not implemented, which is allowed). Whether it sounds is still open.
- **Pigments' knob moves did not reach the host**: 222 drag steps and 2 clicks in its window, 0 parameter moves, 0 gestures begun. In report 5 Phase Plant's moves did arrive (1,428). Not known yet whether the drags were on knobs or in its preset browser, or whether Pigments reports moves in a way the host does not catch.
- **The iFi Gryphon runs at 16-bit integer on the wire** ("format on the wire: 16-bit integer, 2 ch, 44100 Hz", 60 formats offered). macOS turns the float mix into 16 bits before the DAC. Set in Audio MIDI Setup; the native engine should choose the deepest integer format when it opens a device.
- **Devices**: the Bluetooth speaker came back at 44.1 kHz and the app followed ("switched to 44100 Hz from outside this app; following it"); when the eqMac device went away it moved to the default output by itself; the Gryphon was switched on during the run and got a `[device] appeared` line. One blank device appeared for a moment during the Bluetooth reconnect ("(, unknown) ... now 0 Hz").
- Scan: 253 bundles, 221 readable, 222 plug-ins, every bundle in a separate process; 31 Intel-only (Midnight Mirage, Output's Arcade, Black, Boost, Brass, Clone, Duck, Hatz, Infiltrator, Minipol, PitchMonster, Shaper2, Tantrum, Tapex2, Texture, Transient Master, Vybz, 14 RX 9), 1 broken (helisert_6.0). `[au]` 104 Audio Units (96 Apple Silicon, 8 Intel-only), `[clap]` none. The report is ASCII; two empty lines between summaries.

Next: task NL6 (below).

### The user's seventh report (20:17 Brussels): Phase Plant sounds, and Pigments' knobs do reach the host

The report: `tools/native-lab/reports/2026-11-27-test-app-0.5-report-7.txt` (the same run continued).
- **Phase Plant sounds**: 136 notes, sound in 2,314 of 3,438 blocks; `setComponentState` = not implemented (allowed). With the 0.4 host it was silent (report 5). Both of the user's main instruments now play in the host.
- **Pigments' knob moves do arrive**: 938 moves, 19 gestures begun and ended, last "Wavetable 1 PM Amount = 0.37"; 465 parameter changes handed to the processor; 5 restarts because all values changed (presets loaded). The 0 moves in report 6 were drags outside knobs (preset browser). So NL6 item 1 is not a host fault; the poll check for unreported moves is still worth having. Phase Plant: 98 moves, 98 gestures, 12 restarts.
- **Phase Plant peaked at +27.9 dBFS** inside the plug-in (output peak 1.000 after the app): the patch as the user left it was far over full scale. The app must protect the ears and the DAC: a plug-in output past 0 dBFS should be shown (a [warning] line and a red meter) and the master must never pass full scale (the engine already keeps bad samples and values past full scale from the DAC). NL6 or the next task: add the warning.
- **Worst block 5.4 ms (47 %)** of 11.6 ms with Phase Plant and Pigments while their windows were in use (average 9 % and 6 %); no failed blocks, 1 overload (at the device switch). Log when the worst block happened (window opened, preset loaded, knob moved) so a spike can be tied to its cause.
- **Mojibake again** in strings that come from the plug-in itself ("17.1‚ÄØms": Phase Plant's narrow no-break space): the ASCII clean-up does not reach parameter value texts. NL6: run every plug-in string through the same clean-up.
- Empty lines between summaries still there (NL6 item 4).

**The user's decision (20:20 Brussels): skip test app 0.6 for testing.** NL6 finishes and publishes as planned, but the user only tests the next version: task NL7 builds test app 0.7 on top of NL6 with the three findings above (the warning past 0 dBFS with a red meter, the worst block tied to its cause, plug-in strings cleaned) plus anything from NL6's list not finished, and that is the version the user is given.

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

## The review (RN5), item by item: which stage takes it, and where it stands (27 November 2026, task NB-R2)

The review has 34 issues (A1 to A15, C1 to C14, P1 to P5) and nine decisions for you (D1 to D9, in `docs/review-native.md` section 5). Blockers first: nothing is built further on a blocker until it is fixed.

| Item | What | Stage that takes it | State |
|---|---|---|---|
| **A1 (blocker)** | no sample-rate contract between the page and the engine | NB-R2 | **fixed** (engine refuses a page rate that is not the device's; rate change pauses, tells, resumes); the page side (context made at the device rate, rebuilt on the event) is two helpers in `page-tap.js` that N2c copies in |
| **A2 (blocker for N3)** | one random generator shared by all worklets | NB-R6 after **D2** | **waiting for D2.** Fixing it changes the web engine's sound once (one stream per device, an `index.html` change, versioned). The task's rule "the sound must not change" and the review's own D2 make this your decision. Until then: single devices and chains with at most one random-drawing device are bit for bit; two in one song match only at 128 frames per call |
| **P1 (blocker)** | nothing native runs on a push; N2b never compiled on macOS | NB-R1, NB-R2 | **fixed for Linux**: `native-ci.yml` on every push, now including the whole engine on the null device. **macOS still not compiled by a machine**: see D9 below |
| A3 | the reference is a chunked render | D3 (yours), then the reference script | open; the engine side is ready (any quantum) |
| A4 | the 128 quantum is part of the sound | N3c | done |
| A5 | what bit identity can promise per family | NB-R11 | open (research) |
| A6, A7 | fused multiply-add, float control state | N3c | done |
| A8 | sound path through Electron's main process | NB-R3 | **fixed** (task NB-R3): utilityProcess feeder, bounded queue with drops counted, back-pressure honoured, watchdog for the feeder and the engine; proven on Linux with Electron 45.4.1 and the null device |
| A9 | bit-perfect versus exclusive use | D1 (yours) | open |
| A10, A11 | state ownership and protocol; project file version | NB-R4, NB-R7, NB-R9 | **protocol part fixed** (NB-R4a: protocol 1 checked at start, request numbers, parse errors answered); ownership and the edit protocol (NB-R7) and the file version (NB-R9) open |
| A12, A13, A14 | plug-in module lifetime, host gaps, scanner hang | NB-R8 (N4) | open |
| A15 | delay compensation | N4 | open |
| **C1** | source switching: a race and a sleep | NB-R2 | **fixed**: the socket thread stops first, the device thread is waited out of render; the new test finds 17 ThreadSanitizer races in the old order and none in the new |
| C2 | sinc table built on the audio thread | NB-R2 | **fixed** (built at start) |
| C3, C4 | follower response and steering | NB-R5 | **fixed** (NB-R5): 128-tap kernel cut at the top frequency, flat to 20 kHz at 44.1 kHz (error about -120 dB), bypass at speed 1; steering 2.5 times faster with a 30 s acquisition phase, the learned clock kept through a gap; tested at the production target with a bursty sender |
| C5 | data races outside the ring | NB-R2 | **fixed** for the device rate, the device id and the steering reset; TSan clean on Linux |
| C6, C7 | output safety; the integer path | NB-R4 | **fixed** (NB-R4a): protect (NaN and infinity to silence, a clip at full scale, both counted, legal samples untouched); device volume ramped, above the loudest level only with a confirmation; format listener and restart; dither off by default; the integer path ran with sound for the first time (null device, 24-bit bit for bit) |
| C8 | latency figure understates | NB-R4 | **fixed** (NB-R4a): `deviceLatencyFrames` and `ringLatencyFrames` with a note; the page's own buffering is named as not included |
| C9 | possible stalls | NB-R4 | **fixed** (NB-R1, NB-R3, NB-R4b): a hung engine is killed at start and after 3 s without an answer; a frozen sender no longer holds a source switch; everything the engine says goes through one writer thread, and the command reader no longer flushes the output on every line, so a shell that stops reading stalls neither the sound nor the commands |
| C10, C11 | bad input; bridge details | NB-R4 | **fixed** (NB-R4a): checked numbers, `\u` escapes, the WAV reader's bounds; request numbers, SIGKILL after an ignored stop |
| C12, C13 | page tap allocates; preload trusts any message | N2c | open |
| C14 | test app's audio thread | test app, later | for the record |
| P2 | proofs are short | NB-R10 | open |
| P3 | no sanitizers | NB-R1 | **done** on Linux (ASan, UBSan, TSan) |
| P4 | references from headless Chromium, not the app's Electron | D3 | open |
| P5 / **D9** | no macOS build machine | yours | **open, and now clearer**: on 27 November `macos-15` jobs waited 15 minutes and were cancelled (runs 46009024051, 46016748702), a `macos-14` job was cancelled at once without a machine (run 46019198450), `macos-latest` waited too (run 46019206859, still queued after 15 minutes). That pattern looks like the account's macOS minutes or spending limit rather than a busy queue: worth a look in the repository's Billing and plans > Actions. A self-hosted runner on the Mac mini costs nothing and ends it |

## Review fix NB-R7: who owns the project, and how an edit travels (27 November 2026)

The review (A10) said the engine cannot grow further without a defined owner of the project and an edit protocol; your picks say the engine keeps all state and the interface is a view on it. The design is in **`docs/native-state-protocol.md`**; in short:

- **The document is the app's project object `S`**, as JSON, exactly what the app already snapshots for undo and saves. The view, the transport and the audio of recordings are not in it.
- **Until the end of stage 3 the page owns it, from N4 the engine.** The protocol is the same; only the side that presses undo moves. So a native view later needs no second move of the state.
- **Edits are differences, not 327 rewritten call sites.** At every `changed()` the page compares `S` with the copy it last sent and sends the difference: `set`, `del`, `ins`, `rm` operations that carry the old value. Each edit is its own undo, and the engine checks the old values, so drift is found at the first edit that touches it.
- **Order:** every change has a number (`seq`); an edit names the one it was made on and is refused as stale if the engine changed meanwhile; one edit in flight, the rest queued per undo step. When the engine changes the project first (its undo, later a plug-in window or a control surface), the page rolls back, takes the engine's change and puts its own on top; at the same place the engine wins. A lost line, a wrong old value or an engine restart: the whole project is sent again.
- **Undo** by step (one `pushUndo` = one step, a whole knob drag); the engine keeps operations, not snapshots, 64 MB, oldest whole steps dropped first.
- **A half-native song:** both engines read the same document; where each track sounds is the engine's decision from its port list, never stored, so moving a track between engines can never leave anything behind.
- **Saving:** atomic (write, flush to disk, `F_FULLFSYNC` on the Mac, rename), five older copies, `minReader` (an older AudioLab refuses rather than half-reads), a hash that finds a damaged file; the newest whole copy opens instead.

**Proven** (Linux, here and on GitHub run 46052350883, green on every job): `aldoc selftest` 22 checks (also under AddressSanitizer + UndefinedBehaviorSanitizer) and `tools/native-lab/doc_sync_test.js` on the three built-in songs:

| Phase | What | Result per song |
|---|---|---|
| A | about 850 random edits of 34 kinds (clips, notes, devices, tracks, names in any script with emoji and broken surrogates, odd numbers, keys that look like numbers, `__proto__`) and about 100 undos by the app's own snapshot restore | engine's hash equal to the page's after **every** step, whole JSON equal every 100 |
| B | the engine's undo and redo (about 210 and 15) sent back to the page | every undo gives exactly the state before its step; undoing all reaches the song as loaded |
| C | 200 times the engine's change overtakes the page's edit | refused, rebased, equal every time; the page's change kept 191 to 197 times, the engine's won the rest (same track) |
| D | a lost line, a stale base, a wrong old value, the engine killed and restarted | found, whole project sent, equal again |
| E | saves: seven in a row, a crash before the rename, a file cut in half, one number changed in a file, a file for a newer AudioLab | the right copy opens every time |
| F | the diff alone on 3,000 arrays moved, reversed, shuffled, filtered, changed | always exact; moving one Fractals track is a 0.7 KB edit |

**Measured (Fractals, 514 KB):** an edit is 176 bytes in the middle (90 % under 1.3 KB, the largest 203 KB when whole tracks come and go); the engine applies one in microseconds and hashes the project in 2 ms; the page needs about 10 ms to compare an unchanged project (the app already spends 3 ms on `JSON.stringify(S)` at every undo point). That 10 ms is fine for clicks and too much for a knob dragged at 240 Hz, so the hook commits once per frame and hot paths will pass a hint where they changed.

**Found and fixed by the sanitizer run:** the history limit could cut an undo step in half (now whole steps only, checked); moving one track resent all tracks (now only the moved one).

**The first Mac machine (D9):** the Mac job of native-ci got a `macos-latest` machine at last (run 46052838752: macOS 26.7.2, Apple clang 21, arm64). `alengine` built and its selftest passed on Apple Silicon, the ring too. The devices and the mixer did not build: the vendored LLVM maths lacked its ARM files. Added (13 files, same LLVM commit) and dispatched again: **run 46054867320, the Mac job green on everything**: every native target builds for arm64 (`alengine`, `alrender`, `almix`, `aldoc`, the maths probe), `alengine selftest` passes (follower flat to 20 kHz, every clock offset steered within 2 ppm, 14.8 us per block), the ring under two threads also with ThreadSanitizer, **the mixer's 10 scenes bit for bit against the web engine on Apple Silicon (ALL IDENTICAL)**, `aldoc selftest` and the protocol test (300 steps per song, PASS), the bridge's 55 checks.

**Not proven yet:** the page side inside the real app and its cost in Chromium (N2c); the 240 device cases on Apple Silicon (the Mac job does not make the web references yet: next NB run adds them).

Mac runs: the D9 row of the review table no longer holds as written; `macos-latest` machines come within a minute now (`macos-15` and `macos-14` still got none earlier today).

## Review fix NB-R5: the clock follower (27 November 2026)

When the page's sound and the DAC run on two different clocks, the engine either hands every sample over untouched and corrects now and then ("exact"), or reads between the samples at a speed steered to the page's clock ("follow", no corrections, not bit-perfect). The review (C3, C4) found the follow mode dull at the top and slow to settle. Both fixed; "exact" is unchanged.

| Measured (selftest) | before (48 taps) | now (128 taps) |
|---|---|---|
| 44.1 kHz: 19 kHz | -0.82 dB | 0.000 dB, error -120 dB |
| 44.1 kHz: 20 kHz | **-4.23 dB** | 0.000 dB, error -120 dB |
| 44.1 kHz: 21 kHz | -12.7 dB | -0.018 dB |
| 48 kHz: 21 kHz | -1.44 dB | 0.000 dB |
| speed exactly 1 | bit for bit except -0.0 | bit for bit, -0.0 too |
| sender 1,000 ppm off, after 5 min | 1,018 ppm, fill 19 ms over target | 1,000.7 ppm, fill within 2 ms |
| sender 1,000 ppm slow, 25 ms stall each second, 40 ms target | ran empty 14 times | never empty, never a drop |
| cost at 48 kHz, one 128-frame block | | 16 us (0.6 %) |

- **The kernel** is 128 taps long, cut at the top frequency. At a whole sample it is the sample itself, so the response changes smoothly as the read position slips (the old one jumped once every half second or so at 50 ppm). One table serves every rate.
- **The steering** is about 2.5 times faster (critically damped, 0.05 rad/s) and three times faster again for its first 30 s, then hands over without a jump. Its speed wobbles 5 to 15 parts per million (worst 37), under 0.07 cent: inaudible. When the ring runs empty or drops, it keeps the clock it learned instead of starting over (starting over made a slow sender run empty again and again).
- **The default margin is 40 ms, not 30.** NB-R3 measured gaps of up to 25 ms between blocks at the shell's feeder under load; with 4 ms of jitter and the device's own block, 30 ms ran empty even with a sender 50 ppm off. 40 ms held in every case with 8 ms to spare. The status now gives `worstGapMs` (the longest wait between arrivals) and `fillMinMs` (the lowest fill), so the settings page (N2c) can offer a lower margin where your Mac shows it is safe. Lowest latency stays the aim: native playback (N3) has no ring at all.

**Tested** here: selftest (the table above, four bursty senders for 4 minutes each), `engine_null_test.py` 52 checks in all three builds (new: the 40 ms default, a 20 ms stall read back from the status: worst wait 20.3 ms, lowest fill 26 ms, never empty), the ring under two threads, bridge 55, the Electron feeder test 13 of 13. **On GitHub:** run 46042034200 green on every Linux job. **Not proven:** the real clocks of the Gryphon and the Zoom (how far off they are, and the gaps on your Mac); the 1-hour run is NB-R10.

## Review fix NB-R4b: the engine never waits on the app (27 November 2026)

`alengine` 0.6. What R4a left, and three gaps found while doing it:

- **The engine never waits on the app (review C9).** Everything the engine says (answers and events) now goes into a queue that one writer thread empties. So the thread that takes the page's sound, the system's listener and the volume ramp never wait if the app is slow to read. Found on the way: the engine's command reader was tied to its output, so every command it read first flushed the output. With the app not reading, the engine **stopped reading commands too**. Measured with the app's reading stopped and the output pipe full: alengine 0.5 let **12,032 of 72,064** frames in over 6 s and took no more commands; 0.6 took **all 72,064 in 1.4 s** and every one of 3,000 commands, and all 3,000 answers arrived once the app read again (events past 4,096 waiting lines are dropped and counted; answers never are).
- **Format changes never wait on the listener.** In 0.5 the system's listener thread waited for the previous restart to finish, which can wait for the command thread. On the Mac that could hang. Now the listener only asks and a worker does the restart: 40 format changes during 40 device opens, every open answered in 0.7 s.
- **A race fixed.** ThreadSanitizer found that the format restart changed the stream while `status` read it (present since 0.5, not reached by the earlier tests). `status` now reads under the device lock.
- **Your yes for a louder DAC, for real.** In 0.5 the engine asked for a confirmation, but the app passed on whatever the page sent, so a page could confirm by itself. Now the app throws away a confirmation from the page and asks you in its own dialog ("Raise the Gryphon's own volume from 40 % to 80 %?"). Only after "Make it louder" does it send the confirmation. With no window to ask in, the answer is no.
- **Files at the wrong rate.** A test file at 44.1 kHz on a device at 48 kHz played too fast and too high. It is now refused, with both rates named.
- The app passes the engine's `format` event to the page, for the settings page in N2c.

**Tested** here: `engine_null_test.py` 50 checks (7 new) in a normal build, under ASan + UBSan and under ThreadSanitizer, each run twice; against 0.5 the new checks fail as they should. Bridge unit tests 55 (5 new: the dialog says yes, no, or is missing; the page's own confirmation never reaches the engine; the format event reaches the page). The real Electron shell with the feeder (NB-R3) 13 of 13. The mixer's 10 scenes identical. **On GitHub**: run 46038950323 (which carries this commit) green on every Linux job; the Mac job waits for a machine (D9).

**Not proven:** anything on Core Audio (D9: no Mac runner has started since NB-R1). Nothing here changes sound: legal samples pass untouched, and the app still plays through the web engine.

## Review fix NB-R4a: the engine hardened (27 November 2026)

What the review asked for (RN5 C6 to C11, A10), and what `alengine` 0.5 now does:

- **Nothing harmful reaches the DAC.** A sample that is not a number or infinite becomes silence, and one past full scale is held at full scale. Both are counted (`protect` in the status). Every legal sample (from -1 to 1) passes untouched, so bit-perfect playback is not affected: the bit-for-bit checks below ran with it on.
- **The DAC's own volume never jumps.** It moves in a ramp (at most 2 % every 5 ms: 0.25 to 0.9 took 56 ms), and the page gets one event at the end, not one per step. It can only go above the loudest level the device has had with a confirmation: the device's level when the engine first opened it, a level the user confirmed, or one set outside the app (Audio MIDI Setup). Without it the answer is `needsConfirm` with that level, so the app must ask you first. That matters because the page arrives through updates that are not signed yet (RN6).
- **Format changes.** If another program, Audio MIDI Setup or a re-plug changes the device's format while the engine plays, the engine starts its stream again in the new format instead of writing the old layout into it. The Core Audio side listens to the stream's formats now. 16-bit dither is off unless asked for, so a 16-bit file reaches a 16-bit DAC bit for bit.
- **The integer path ran with sound for the first time.** The null device now offers 16-bit and 24-bit integer formats the system does not mix, and the engine writes the DAC's bytes itself as it would on the Gryphon in integer mode. 1 s of 24-bit samples came back **bit for bit** (96,000 of 96,000).
- **Latency told honestly.** The status gives the device's part and the ring's part, with a note that the page's own buffering is not included.
- **Numbers checked.** Buffer, device id, bits, rate, volume, the ring's sizes: a negative, huge, fractional or text value is refused by name and nothing happens. `\u` escapes are read as UTF-8, so device names with accents come back as they went in. A WAV file whose header runs past its end is refused.
- **Protocol.** `ready` says `protocol: 1` and the app refuses an engine that speaks another one. Every command carries a request number and its answer carries the same, so a late answer can never be taken for the next one (the review's `status` mix-up), and a line that is not JSON gets an answer instead of a 15-second wait. A helper that ignores the stop signal is killed after 3 s.

**On GitHub** (commit 67a1158): the push run 46033808827 green on every job (the engine null test in Release, sanitizers and TSan; the 240 device cases; bridge 50; the Electron feeder test). A run with the Apple Silicon box ticked (46033821125) finished all Linux jobs green; its Mac job was still waiting for a machine after 7 minutes (D9 as before) and is left queued.

**Tested** here on the null device: `engine_null_test.py` 43 checks (19 new), in a normal build and under ASan + UBSan and ThreadSanitizer; bridge unit tests 50 (5 new: another protocol refused and not left running, a late answer not taken for the next, request numbers on every command, stop); the feeder test (NB-R3) still 13 of 13.

**Not proven:** the Core Audio format listener is written but no machine has compiled it (D9); whether the Gryphon reports a format change the way the null device does, and how it sounds when the engine writes its bytes, only your Mac can show. **Left for NB-R4b:** the socket thread writes two messages (connected, disconnected) that could wait if the app stopped reading the engine's output; the app always reads it, so this is latent.

## Review fix NB-R3: the sound path out of the shell's main process (27 November 2026)

**What was wrong (review A8).** The page's 128-frame blocks went through the desktop shell's main process on their way to the engine. That process also runs the menus, every request from the page (AI voices, the DAC volume, updates) and the updater's downloads and hashing. With 30 ms of sound in hand at the engine, one 30 ms pause there was a gap you hear. The socket's "wait" signal was ignored.

**What changed.**
- **The feeder** (`desktop/native-feeder.js`): a small Electron utilityProcess that does nothing but take the blocks from the page's worklet port and write them into the engine's socket. The shell hands it the port and the socket's address; no block passes the main process any more. If the socket says "wait", blocks go into a queue of 250 ms; when that is full, new blocks are dropped whole and counted (order kept, memory bounded).
- **The watchdog**: once a second, while the engine is wanted, the shell asks the feeder and the engine for an answer. After 3 missed answers the feeder is replaced (event `feeder-restarted`, the page gives the new one a port through `tap.reconnect()`, done by `alNativeWatchFeeder` in `page-tap.js`) or the engine is killed and started again by the crash recovery from N2b (event `engine-hung`, then `restarted`). Three restarts in a minute: `gave-up`, back to the web engine.
- **`alengine` 0.4**: switching the sound source used to wait until the old sender closed its connection; a frozen feeder held the engine's command thread. Now the old connection is shut down at once (found by this task's frozen-feeder test).
- The status's `tap` now says which path carries the sound (`feeder` or `main`) with the feeder's counts (blocks, frames written, back-pressure, largest queue, drops, the longest wait between two blocks).
- `AL_FEED_IN_MAIN=1` keeps the old path, for the comparison only. Nothing changes for the app today: the shell stays idle until the page asks for the native engine (stage N2c).

**Proven** (here, on a 2-core Linux machine, with the real Electron 45.4.1 shell, `native-engine.js`, the feeder, `preload.js`, `page-tap.js`, and the real `alengine` on the null device, which records what it played; production settings: 30 ms prefill, exact clock; `tools/native-lab/feeder_test.py`, 13 checks):

| Case | Main process | Frames bit for bit | Gaps | Ring ran empty |
|---|---|---|---|---|
| A, feeder | blocked 50 ms every second, 20 s | 960,000 of 960,000 | 0 | 0 |
| B, feeder | blocked 250 ms every second, 12 s | 576,000 of 576,000 | 0 | 0 |
| E, feeder | spinning 50 ms every second (using a core) | 960,000 of 960,000 | 0 | 0 |
| C, old path (comparison) | spinning 50 ms every second | 960,000, but with gaps | 2 to 5 per run (up to 152 ms) | 2 to 5 |
| D, feeder frozen at second 4 | blocked 50 ms every second | after the gap, every frame bit for bit to the end | one, 3.7 s (the watchdog's 3 s and the restart) | |

Spread over more runs here: with the main process blocked (waiting) 0 gaps in 9 runs; with it spinning a whole core 2 of 8 runs had one short gap, every time from blocks that reached the feeder up to 74 ms apart, so upstream of the feeder: the spin took half of this 2-core machine from the page's audio thread. On 4 or more cores (GitHub's machines, the user's M4) the test counts that case as strict.

Unit tests (`bridge_unit.js`, 45 checks, 16 new): the port goes on to the feeder and the main process does not listen to it; every frame arrives; a new page port keeps the socket; a frozen feeder is replaced within about 3 s; an engine that does not read: the queue stops at its bound and every frame is written, queued or counted as dropped; an engine that stops answering while it runs is killed and started again with its device and sound. `engine_null_test.py` 26 checks (2 new: a sender that stops sending and never closes does not hold a source switch, 3 ms instead of waiting forever).

**On GitHub** (run 46030650243, commit 4fdbfcb, 4 cores): the new whole run green (all four Linux jobs, including the 240 device cases); the new `electron` job 14 of 14: A, B and the spinning case E (strict on 4 cores) bit for bit with no gap and the blocks at most 11 ms apart at the feeder; the old path 2 gaps (18.7 and 2.7 ms); the frozen feeder replaced, 3.7 s silent, then bit for bit to the end. `node` (bridge unit tests 45 of 45) and `tsan` (the engine on the null device under ThreadSanitizer, with the new frozen-sender check) green.

**Not proven:** the Mac (D9). What only the Mac can show: the same with Core Audio's clock and the app's real main process; that comes with N2c.

## Review fix NB-R2: the rate contract, the source hand-shake, the engine off the Mac (27 November 2026)

**The rate contract (review blocker A1).** Your Mac's default output was eqMac's copy of the Bose at 16 kHz while the Gryphon ran 48 to 384 kHz; the page's AudioContext follows its clock device unless told otherwise, so the engine could have been fed 16 kHz sound and played it at 48 kHz (three times too fast and too high). Now:
- `source` with `type: socket` must carry `pageRate`. Missing, or not the device's rate: refused, and the answer names both rates ("the page renders at 16000 Hz but the device runs 48000 Hz: make the page's AudioContext at 48000 Hz").
- The device changes rate while sound plays (your Rate menu, Audio MIDI Setup, another program): the device plays **silence at once** (never sound at the wrong speed), the engine sends `{ ev: 'rate', value, pageRate, soundPaused: true }`, and counts the frames it threw away (`framesAtWrongRate` in status). When the device comes back to the page's rate, sound resumes by itself (`resumed: true`). Opening a device at another rate checks the contract again.
- The page's side for N2c: `alNativeContext(rate)` makes the AudioContext at the device's rate; `alNativeWatchRate(nativeEngine, rebuild)` calls `rebuild(newRate)` on such an event. The shell and the bridge pass `pageRate` through; crash recovery sends it again (and gives up, back to the web engine, if the device came back at another rate).

**Switching sources safely (review C1, C2, C5).** The engine replaced the ring while the old socket thread could still write into it, guarded by a 30 ms sleep. Now every switch stops the socket thread first and then waits until the device thread has left its render call (a two-flag hand-shake, no timing guess). The follower's table is built when the engine starts, not the first time the device thread needs it. The device rate, the device id and the steering reset are safe across threads.

**The engine runs off the Mac (the null device).** `native/common/nulldevice.cpp` gives the engine the same device layer as Core Audio on any machine: two pretend outputs shaped like your two DACs (one with 16 to 384 kHz, a device volume and exclusive use like the Gryphon; one with 44.1 to 96 kHz and no device volume like the Zoom), a device thread in real time, events from a listener thread, unplugging, another program holding exclusive use, and a recording of what was played. So the whole engine (not only its parts) is now built and tested on every push.

**Proven** (here, and on GitHub's Linux machines, run 46020439496: the same test green in all three builds): `tools/native-lab/engine_null_test.py`, 24 checks with the real engine, in a normal build and under ASan + UBSan and ThreadSanitizer: the refusals above; 2 s sent through the socket came out of the device **bit for bit** (192,000 of 192,000 samples); 48 to 96 kHz while playing: silence, counted, peak 0; back to 48 kHz: resumed with sound; a new source at 96 kHz plays; device volume both ways; "no volume" on the Zoom-like device; exclusive use held by another program named; unplug reported; **300 source switches under load** (socket after socket while the old sender still streams, tone, file, silence, clock flips), every one answered. The same test on the old switching order gives **17 ThreadSanitizer data races in `Ring::init`** (the review's C1), on the new order none. Bridge unit tests 29 of 29 (two new: no page rate, 16 kHz into 96 kHz).

**Not proven.** None of this ran on macOS: the Core Audio side of the same code waits for a Mac runner (above). The real rate-change notification from Core Audio, and how quickly the Gryphon reports it, only your Mac can show.

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
