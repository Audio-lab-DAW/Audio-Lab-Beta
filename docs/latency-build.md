# Playing latency and engine load: the build plan (task LT, lane J)

Plan for the user's AE2 picks of 27 November 2026, 20:41 Brussels:
`AE2 picks: L1a L2a L3b L4a L5a L6b L7? L8a L9a L10? L11b L12a L13a L14a L15a L16a L17a` (a now, b later).
Research and measurements: `docs/research-engine-performance.md` (section 1 the numbers, section 3 the options, section 4 the proposed tasks). This file is the plan for the web engine and the desktop shell; the native items L12 to L17 belong to task NB (`docs/native-mac-build.md`).

Written in step LT-0 (27 November 2026). `index.html`, `desktop/` and `native/` were not touched in this step.

## Status

| Step | Research id | Picks | What | Status |
|---|---|---|---|---|
| LT-0 | | | this plan | **done** (27 Nov) |
| LT-1 | AE2-1 | L1, L2 | output check; playing buffer, Auto that comes back down | next |
| LT-2 | AE2-2 | L4 | the played track skips delay compensation; recorded notes on the compensated clock | |
| LT-3a | AE2-3 | L5 | desktop: notes read outside the page, posted into the worklet (the path, one instrument kind) | |
| LT-3b | AE2-3 | L5 | desktop: every worklet instrument, drums, recording and the read-out; the Electron proof | |
| LT-4 | AE2-5 | L8 | sleep idle tracks | |
| LT-5a | RA1 | L9 | render ahead: the window renderer and playback as buffers | |
| LT-5b | RA2 | L9 | render ahead: invalidation (edits, automation, tempo, arming) | |
| LT-5c | RA3 | L9 | render ahead: memory limit, the Settings row, the x4 proof; then "live playing complete" | |

Later, on the user's go: L3 (start played notes at once, without the +2 ms), L6 (a lighter main thread while playing, lanes A and E), L11 (cost per track, lane E). Not chosen: L7, L10.

## Baseline to beat (measured in AE2 on the build machine, v0.263 era)

From `tools/engine-lab/ae2/*_result.json`. Every step re-measures its own row on the version it starts from and on its release, with the same script.

| What | Script | Before (AE2) |
|---|---|---|
| Key to the track's input, idle, Lead, Auto 256 (block 128) | `latency_chain.py` | median 43.1 ms, worst 47 ms |
| same at 128 frames | `latency_chain.py` | median 17.4 ms, worst 43 ms |
| same at 1,024 frames (where Auto ends after dropouts) | `latency_chain.py` | median 86.1 ms, worst 359 ms |
| song playing, Lead high, Auto 256 | `latency_chain.py` | median 62.7 ms, worst 158 ms (main thread median 25.4 ms) |
| delay compensation on the played track, Fractals | `pdc_live.py` | 6.0 ms; 52.5 ms with one resonance suppressor; 16 ms with a 10 ms look-ahead limiter |
| live load, Fractals x1 / x2 / x4, Auto 256, 9.5 s from bar 161 | `perf_load.py` | 39 % avg, 6 dropouts / 70 %, 20 / 132 %, 894 dropouts |
| Fractals export levels (`tools/engine-tests/export_same.py`) | | Kick -9.75669 dB (0496bb147f6c), Bass -25.48699 dB (09e0415bec5e) with the master at 0 dB; -19.05560 / -35.48685 dB at -10 dB (newest backlog entries, v0.264 to v0.266) |

The build machine has no sound card and no MIDI device: the device part of key to sound, Bluetooth, eqMac and the Push 1 path can only be proved on the user's Mac. Each step says so plainly in its log.

## Where the code is (anchors in `index.html` at v0.266)

| What | Anchor | Owner |
|---|---|---|
| context creation, buffer and render block | `function rqWant(bsz)`, `function ensureCtx()` (latencyHint from `UI.buf` / `UI.abuf`, `renderSizeHint` from `rqWant`) | shared engine; lane J may add hooks |
| Auto buffer | `const ABUF=[256,512,1024,2048];`, the 500 ms dropout interval, `function autoBufCheck()` (only goes up) | **lane J** |
| restart of the audio context | `function restartAudio(quiet)` (stops, closes, recreates, starts again) | shared |
| output device | `UI.sink`, `ctx.setSinkId` in `ensureCtx`, `devicechange` listener, `listOuts()` (`#outSel`), desktop `audiolabDesktop.dac.list()` (Mac only) | lane B (Settings, devices) |
| settings table | `const STT=[` (task ST-S4 shape: `id,l,pg,b,sc,k,c,t,d,h,w`), helpers `SETT`; rows `outDev` and `buffer` are on page `audio`, block "Audio driver" | lane B |
| notices | `toast(m)`, `askChoice(title,text,btns,icon)`, `updCard(v,notes)`; lane F (OV) has no notification API yet (OV1 done, N1 not built) | lane F |
| delay compensation | `function fxLat(f,sr)`, `function pdcMap(sr)`; live call in `syncGraph` (`PDC=pdcMap(ctx.sampleRate)`, applied to `N.pdc.delayTime`), offline call in the exporter (`PDC=only\|\|fast?new Map():pdcMap(sr)`) | shared engine; AE3 may extend it to returns and sends |
| played notes | `function noteOn(p,v,key)` (wrapped three times by other lanes), `function voiceOn(t,p,v)`, `const liveTracks=` (armed instrument tracks, else the selected one when the computer keyboard is on) | lane C (live playing, controller layer) |
| worklet voice start | `emPlay(ctx,t.inst,{...},p,ctx.currentTime+.002,...)` in `voiceOn` paths (the +2 ms is L3, later) | voice engine owner |
| recording placement | the take built with `n.s-a-(UI.recOff\|\|0)/1000*S.bpm/60` | lane C |
| Web MIDI | `ctlStart()` (controller layer, Web MIDI with SysEx), `initMidi()` (notes to `noteOn`) | lane C; HF1's rules |
| desktop | `desktop/main.js` (permissions already allow `midi`, `midiSysex`), `desktop/preload.js` (`audiolabDesktop`) | shared with MG1, IC4, MB1, NB |

New JS goes before `function askChoice(title,text,btns,icon){`, new CSS before `.dacv{display:flex;`. Every new top-level name starts with `lt` (or `LT_`). Hooks other lanes may call or fill live in one object `LT_HOOKS`.

## LT-1 (AE2-1): output check (L1) and the playing buffer (L2)

**L1 output check.**
- When: at the first `ensureCtx`, on `devicechange`, and when the output is changed. Event driven: no timer, nothing per frame.
- What it reads: the label of the device in use (`ctx.sinkId`, or the default output's label from `enumerateDevices`), `ctx.sampleRate`, `ctx.outputLatency`; in the desktop app on the Mac also `audiolabDesktop.dac.list()` (transport, nominal rate) where it gives them.
- What it warns about (each a plain reason in the notice):
  - Bluetooth: the transport says so, or the label matches Bose, SoundLink, AirPods, Beats, JBL, "Hands-Free", WH-, Buds and the like.
  - a virtual device: eqMac (labels ending in "(eqMac)"), Background Music, BlackHole, Soundflower, Loopback, an aggregate such as "Cubase System Sound Link", call apps' devices (Teams, Zoom Audio, Krisp).
  - call mode: the device or the context runs at 16 kHz or 8 kHz.
  - a reported output latency above 40 ms whatever the device.
- The one button: "Play through <wired device>", the wired output to use: the one the user picked before (remembered as `UI.ltWired`), else a known wired DAC or interface present now (iFi, shown on the user's Mac as "iFi (by AMR) HD USB Audio"; Zoom AMS-24; Focusrite, RME, MOTU, Apogee, Audient, SSL, UA), else any USB output that is not virtual. It sets the output through the same path as the Settings output select (`UI.sink`, `setSinkId`, `saveUI`). Other buttons: "Keep this output" (no more warnings for this device, `UI.ltOkOut`) and "Not now" (this session).
- Shown with lane F's notification when lane F has released one (`OV_HOOKS` or the N1 notice), else `askChoice` once, with `toast` for the result. `LT_HOOKS.notify` is the one place to switch over.

**L2 playing buffer.**
- Auto comes back down: after a full minute of playing with no dropouts (the existing counters `URS`, `urNow`, `CPU.dropT`), Auto marks one step down (2,048 to 1,024 to 512 to 256); the step is applied at the next Stop (the context is restarted only while stopped, as `autoBufCheck` already does for going up). Never below 256 for mixing; a step up and a step down are at least a minute apart so it cannot swing.
- Playing buffer: while a track is armed or the computer keyboard plays notes (`liveTracks()` not empty) and the transport is stopped, the context runs at 128 frames with a 64-frame render block where Chromium allows it (`renderSizeHint` 64; checked afterwards with `ctx.renderQuantumSize`, falling back to 128). Pressing Play goes back to the mixing buffer (Auto or the user's fixed value). Switching restarts the context, so it happens only on the state change, after 400 ms of quiet, and never while a key is held. Measured in this step: the cost of a restart; if it is long enough to be felt at Play, the switch at Play is dropped and the playing buffer stays until dropouts (the Auto rule) and that is written in the log.
- Settings: two rows in lane B's table shape, given to lane B as `LT_HOOKS.audioRows` (page `audio`, block "Audio driver"): "Playing buffer" (Off, 128, 256; default 128; tooltip: "While a track is armed or the computer keyboard plays, and the song is stopped, AudioLab uses this smaller buffer so notes sound sooner.") and "Check the output device" (on by default). If lane B has no row API yet, LT draws these two rows itself right under the Buffer size row, in its own elements, with the same classes; the log asks lane B to take them over.
- Old settings: `UI.buf`, `UI.abuf`, `UI.rq` keep their meaning; the new keys are optional with defaults.

**Tests** (`tools/ui-tests/taskLT_1.py`): fake output labels (Bose via eqMac at 16 kHz, Background Music, BlackHole, Cubase System Sound Link, a Bluetooth name, the iFi) through a stubbed `enumerateDevices`: the warning shows for the bad ones and not for the iFi, the button names the iFi and sets `UI.sink`; "Keep this output" silences it. Auto: forced dropouts take it up, a simulated clean minute marks a step down that is applied at Stop. Playing buffer: arm a track while stopped, the context is at 128 (and 64 where allowed); Play returns to the mixing buffer. `latency_chain.py` before and after (idle, Lead, Auto; and the armed case). Dark and Light screenshots of the notice and the rows. No console errors, the UI tests pass, Fractals export levels unchanged. **Only the Mac proves**: the real device labels and transport, the 16 kHz call mode, the time to sound through the iFi.

## LT-2 (AE2-2): the played track skips delay compensation (L4)

- A hook in `pdcMap`, as small as possible: `pdcMap(sr,live)`; the live call in `syncGraph` passes `true`, the exporter's call is untouched, so exports stay bit for bit the same. With `live`, `LT_HOOKS.pdcLive(M,sr)` sets the delay of the played tracks (`liveTracks()`) to 0. AE3's later work on returns and sends extends the same map; the hook only lowers entries of played tracks, so it composes with that.
- The played track then sounds earlier than the compensated tracks by its compensation (6 ms in Fractals; 52 ms with a resonance suppressor elsewhere): the same trade as Ableton's reduced latency when monitoring. Its own devices' latency still applies.
- The switch happens on arm, disarm and keyboard on or off; the delay changes with a short ramp so there is no click.
- Recording: notes recorded on a played track are placed by the compensated clock: the press time minus (the compensation target minus the played track's own path latency), on top of today's `UI.recOff`. Goal: notes land on the grid within 1 ms.
- `CPU.pdc` and the read-out keep showing the song's compensation; the played track's row says it is outside.

**Tests** (`taskLT_2.py`): `pdc_live.py` before and after (Lead 6.0 ms to 0; with a resonance suppressor on the Bass 52.5 ms to 0); `latency_chain.py` with a resonance suppressor in the song: the total no longer changes with it; a scripted performance (presses timed to the heard beat) records notes within 1 ms of the grid, with and without a suppressor; exports bit for bit (Fractals levels and checksums). **Only the Mac proves**: how it feels with a Push 1.

## LT-3a and LT-3b (AE2-3): notes past the main thread in the desktop app (L5)

- The path: `desktop/lt-midi.js` (new, lane J's own module) reads MIDI inputs off the page's main thread and posts each note message with its timestamp through a `MessagePort` straight into the audio worklet. Two ways, decided in LT-3a by measurement: (1) a hidden, sandboxed window of the shell that only listens to Web MIDI (its own main thread, idle otherwise), with a `MessageChannelMain` whose ends go to that window and to the app page, which hands its end to the worklet; no native module needed; (2) a native MIDI module in the shell's main process (only if (1) is not fast or not reliable; it needs MB1's build to carry it). `main.js` and `preload.js` get one small hook each (create the channel; hand the port to the page).
- In the worklet: a note-on starts the voice at the start of the next block; the page is told afterwards (for the piano display, the record take and the meters) so the main thread is out of the timing path but still knows what was played.
- Lane C's controller layer keeps everything that is not a note: CC, pitch bend, the Push 1, Launchpad and Mackie surfaces, MIDI learn. Notes from a port that the fast path plays are not played a second time by `initMidi()`: lane C's code is not changed; LT adds a check through a hook (`LT_HOOKS.ownsNote(portId)`) that lane C's next step calls, and until then LT wraps `noteOn` the way other lanes already do, skipping the sound (not the recording) for notes the fast path already played.
- HF1's MIDI rules stay: the fast path only reads, never sends (no feedback loop); it listens only to ports the controller layer treats as note inputs; unknown ports stay off as control surfaces; the IAC "Ableton Push to Cubase" kind of port is never taken.
- L14 holds: the fast path plays into the web engine's own output, never through the native bridge's 40 ms ring.
- LT-3a: the path for one instrument kind (the plant voice engine of the Lead) and the measurement. LT-3b: every worklet instrument, a worklet path for the drum voices (today built-in nodes), recording with the MIDI timestamps, a Settings row ("Fast MIDI notes", desktop only, on by default) through `LT_HOOKS.audioRows`, and the Electron proof.

**Tests** (`taskLT_3a.py`, `taskLT_3b.py`): in Electron under xvfb (the release gate's way of running it) with a fake MIDI input injected in the listening window: note to first sample while the page runs a 200 ms long task: before, the note waits for the task (about 200 ms); after, about one block. Without the desktop app nothing changes (the web path as before). No double notes, CC still reaches lane C's layer, the record take matches the timestamps. **Only the Mac proves**: the Push 1 over USB, CoreMIDI's timing.

## LT-4 (AE2-5): sleep idle tracks (L8)

- A track sleeps in the live engine when it has no notes or clips in the next two bars, no voice is sounding, and its output has been silent (below -120 dBFS) for longer than its devices' tail (reverb and delay tails estimated from their settings, else measured by the meter). It wakes one bar ahead of its next note (the scheduler already knows it) and at once when played or armed.
- Sleeping means: the voice worklets skip their work and write silence; the device chain is disconnected from its input so Chromium can skip it; nothing per frame while idle (the check runs in the existing scheduler tick while playing, not on a timer while stopped).
- Live only. The exporter is not changed, so exports are bit for bit the same by construction; the test also renders the live graph's sleeping sections offline to show the samples match where the track was asleep (exact zeros).
- Not asleep: a track that keys a sidechain, a return, a group with an awake child, a track with automation that moves inside the next bar.

**Tests** (`taskLT_4.py`): `perf_load.py` in the Peak and in a sparse section (breaks, risers): live load and dropouts before and after; exports bit for bit; no cut tails on a reverb and a delay throw (the tail renders the same with sleeping on and off).

## LT-5a, 5b, 5c (RA1 to RA3): render ahead in the web engine (L9)

- What: tracks that are not played (not armed, not keyboard-played) are rendered by OfflineAudioContexts into a window ahead of the playhead and played back as buffers in place of their live instrument and devices (the rendered signal enters before the track's fader and pan, so mixer moves, sends and meters stay live). The played track and the master stay live.
- Note from the research: Chromium runs every OfflineAudioContext of a page on one background thread, so this moves the work from the real-time thread to one other core (two in all), not to all cores. That is still the gap between x4 failing and x4 playing on the build machine.
- Same samples: the window is rendered with the exporter's own per-track render, with enough pre-roll for each device's state (tails, delay lines, LFOs started from the song's clock); the test compares the rendered window with the export of that track over the same range, sample for sample.
- LT-5a: the window renderer (a few bars at a time, from the playhead on, refilled while playing), playback as buffers, a switch while stopped. LT-5b: invalidation: a note, clip, device, parameter, automation or tempo change on a track drops its rendered window from the change on and it plays live until refilled; arming or playing a track makes it live at once; jumps of the playhead refill from there. Tracks that cannot be rendered ahead are left live (a ducker keyed by a live track, an input monitor, a device with live input). LT-5c: memory limited (a window per track from a budget, default 256 MB, stereo float about 0.38 MB per second per track at 48 kHz), the Settings row ("Render ahead", Off / On, with the window shown), the x4 proof, then "live playing complete".

**Tests** (`taskLT_5a.py` to `taskLT_5c.py`): rendered and live samples identical (per track, against the export of the same range); `perf_load.py` live: Fractals x4 at Auto 256 without dropouts on the build machine (before: 894 in 9.5 s); edits during playback are heard within the refill time; memory stays under the budget; exports bit for bit.

## How every step is built and released

- Edit scripts in Python with unique, asserted anchors: `tools/engine-lab/lt/lt_<step>.py`, re-run on the fresh file after every `git pull --rebase`.
- A "step claimed" docs commit at the start (a line in "Where it stands" of `docs/device-backlog-2026-11-25.md`).
- Before the push: `git pull --rebase`; re-run the edit script; the lint and the start-up smoke test of `docs/release-gate.md` (`tools/release-gate/gate.py --here --quick`); no top-level function defined twice; no other lane changed the same lines in the last hour (`git log -S` on the anchors); the UI tests again after a rebase.
- Release: `VERSION` = the highest on main + 0.001; `node desktop/scripts/sync-app.js` (writes `app-version-dev.json`; `desktop/app-version.json` is never touched); one line in `desktop/update-notes.txt`; `docs/backlog-log.md` entry headed "task LT-<step>" with the measured before and after and what is left; the line in "Where it stands"; this file's status table; the project doc `claude/audiolab-latency-build.md`; the notification "Playing latency step LT-<step> is out (vX.XXX): ..."; `index.html` (lines 3 to 10 removed) published to the app artifact.
- Nothing may break: exports bit for bit (Fractals levels and checksums above), old projects and settings load, dark and Light, plain language, no em dashes in UI text, tooltips on new controls, no per-frame work while idle.

## Who else this touches

- Lane B (ST): the Settings rows come as `LT_HOOKS.audioRows` in the `STT` shape; lane B places them for good.
- Lane F (OV): the output warning uses lane F's notification once it exists (`LT_HOOKS.notify` switches).
- Lane C (FT): notes through the fast path; `LT_HOOKS.ownsNote` for `initMidi()`; recording placement (LT-2, LT-3b) is a small hook beside lane C's take code.
- Task AE3 (mixing): may extend delay compensation to returns and sends inside `pdcMap`; LT's hook only lowers played tracks' entries.
- Task NB: L12 to L17 (native). L14 is a rule for both: never play through the bridge.
- Desktop tasks MG1, IC4, MB1: LT adds only `desktop/lt-midi.js` and the smallest hooks in `main.js` and `preload.js`; never dispatches a desktop build while another runs.
- Lane D (NI): its analysis worker also renders offline; render ahead (LT-5) shares Chromium's one offline thread with it, so LT-5 yields while the analysis runs during playback.

## Added from the speed and feel picks (UX1, 27 Nov 2026, 22:02 Brussels)

The user picked **S15 steady timing** (docs/research-ux-speed.md): notes at the event's time stamp plus a small fixed offset, no main-thread task over 2 ms while playing, and meters and mixer drawn at half rate while a track is armed (lane E gives the rate through a hook). This is AE2's L7, now picked: build it as an LT step after LT-3 (it uses the same timestamped note path).
