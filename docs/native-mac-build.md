# AudioLab native Mac: the build, stage by stage

The running list of the native Mac work (task NB). Plan: `docs/native-mac-plan.md`. The user's picks and the reports from their Mac: `docs/native-mac-picks.md`.

## Where it stands

| Stage | What | State |
|---|---|---|
| 0 | The proofs: one effect bit for bit, a VST3 host, the test app | done (task NM1), proven on the user's Mac |
| N1 | Native audio output and device control, as a helper the app can talk to | **done as a helper and proven on the build machine; not yet inside the app** |
| N2 | The bridge: the app sends its sound to the engine, with a switch back | not started (needs a hook in `index.html`, which waits for the design chain) |
| N3 | The engine core, devices ported family by family | not started |
| N4 | VST3 in the app | host layer and scanner exist from stage 0; not in the app |
| N5 to N8 | Recording, export, packaging, polish | not started |

## What you can try now

**AudioLab VST3 test 0.2**: https://github.com/Audio-lab-DAW/Audio-Lab-Pro-Alpha/releases/tag/native-lab-2 (file `AudioLab-VST3-test-mac-arm64.zip`; open it once through System Settings > Privacy & Security > Open Anyway, as before).

New in 0.2, the second row of the window:
1. **Rate**: switches the Gryphon's sample rate from inside the app. Try 44.1, 96 and 192 kHz with a plug-in playing.
2. **Exclusive use of the device**: tick it, then try to play something from another program through the Gryphon. It should stay silent there until you untick it.
3. **Device volume**: the Gryphon's own volume. Move it in the app and watch Audio MIDI Setup; then move it in Audio MIDI Setup and watch the app.
4. Plug the Gryphon (or the AMS-24) out and in while the app is open: the list should update by itself, and if the device in use goes away the app should move to the default output and say so.
5. "Play test pattern" with nothing loaded now says what to do.

Paste the report as before. The lines to look for start with `[rate]`, `[exclusive]`, `[devices]`.

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

- **Nothing of 0.2's new controls has been clicked by a hand.** The picture `docs/native-lab/test-app-0.2-main-window.png` shows them in place; that is all.
- **The integer path** (the engine writing the DAC's own bytes) has only its arithmetic tested. No device on the build machine offers a format the system does not mix, so it never ran with sound. Whether the Gryphon's 60 formats include such ones, the engine's `formats` answer will show; the test app does not use that path yet.
- **Bit-perfect to a real DAC** cannot be shown without one. What was shown is that the engine's output equals its input sample for sample on a float loop-back device.
- **Drift over a long time.** The test lasted 3 seconds. Over minutes the two clocks drift; the ring then drops or waits once and counts it. A smooth correction (a resampler that moves by parts per million) is not built; it belongs to N2, where the web engine's clock meets the device's.
- **Hot-plug** (a device going away while in use) is written and unseen: the build machine has nothing to unplug.
- **Not inside the app.** `index.html` and `desktop/` were not touched. No setting in AudioLab uses the engine yet.

## Assumptions made (change any of them)

- The engine talks JSON lines over its standard input and output, and takes sound over a local socket. Shared memory would be a little faster; the socket needs no native add-on in the desktop app and passed the sample-exact test. It can be swapped later without changing the commands.
- The first hand-over is "exact, with rare corrections" rather than "always smooth": for listening through a DAC, untouched samples matter more than hiding one correction every few minutes.
- Exclusive use is released when the engine moves to another device or closes.
- This work was started in the session where the user said "yes continue" after the tests on their Mac, and is logged as `task NB-N1` so that task NB continues from N2 and does not repeat it.

## Next: N2, and why it was not started here

N2 puts the engine under the app: the desktop shell ships `alengine`, the page sends its master output to it, the web engine's own output goes silent, and Settings gets "Native output" with device, rate, buffer, exclusive use and volume. That needs a hook in `index.html` and changes in `desktop/`. Other tasks (the design chain) are working in `index.html`, only one task may edit it at a time, and the user's order was "first finish all the complete new design, and then build the native engine". So N2 is left for task NB, fired in its turn.
