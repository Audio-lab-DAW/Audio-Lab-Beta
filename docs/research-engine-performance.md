# Performance and playing latency: research and options (task AE2)

Research and a pick page. No app code changed: `index.html`, `desktop/` and `native/` were not touched. Written 27 November 2026 for the user's question of 20:02 Brussels (biggest pains in a big psytrance project: the delay between pressing a key or a Push 1 pad and hearing it, and mixing clarity; this task is the performance and latency part).

Pick page: published as the artifact **"AudioLab performance and playing latency"** (https://claude.ai/artifact/VJqhdY1m4Aeid56aRGo8Cg, source `tools/engine-lab/ae2/pick-page.html`). Measurements and scripts: `tools/engine-lab/ae2/`.

Read with: `docs/research-native-mac.md` (workgroups, render-ahead in other DAWs, NR tasks), `docs/research-native-windows.md` (WASAPI, MMCSS), `docs/native-mac-build.md` (where NB stands), `docs/native-mac-picks.md` (the reports from the user's M4).

How to read the numbers: **measured** means run in this task (on the build machine: 2 vCPU Intel Xeon 2.1 GHz, headless Chromium 158, Linux, no sound card, so Chromium's output is a fake device whose reported latency is not a Mac's). **Reported** means from the user's own test reports. **Published** means from a named source. **Estimated** means worked out here and says so.

---

## 0. Summary

### Today's latency chain, key or pad to sound (desktop app on the user's M4, iFi Gryphon wired, Settings › Audio buffer Auto)

| Step | Idle | While the song plays | Where the number comes from |
|---|---|---|---|
| Push 1 pad or key reaches the app | about 1 ms | about 1 ms | estimated (USB MIDI full speed polls every 1 ms) |
| Waits on the page's main thread (the input event queue) | 5 ms (median) | 2.5 to 25 ms (median), **worst 45 to 270 ms** | measured: real key presses through Chromium's input pipeline to the app's keydown handler |
| The app's own start offset and the wait for the next render block | 2 ms | 2 ms | measured: worklet voices start at `currentTime + 2 ms`; drum voices start at once (0 ms) |
| Delay compensation applied to the played track | **6 ms** in the Fractals remake; **52 ms** with one resonance suppressor, pitch shifter or pitch corrector anywhere in the song; 16 ms with a 10 ms look-ahead limiter | same | measured (`pdcMap`): the group compressors (6 ms each) delay every other track, the played one too |
| Chromium's buffers and the device (Auto 256 frames at 48 kHz) | about 16 ms | about 16 ms | estimated from a published Chrome 153 loop-back on an M4 (28.6 ms round trip at 128 frames) and the Gryphon's 14 + 14 frames |
| **Total** | **about 30 ms** | **about 40 ms, with spikes past 100 ms** | |

Three things can make it much worse on the user's Mac today:
- **The output device.** The Mac's default output in both reports is "Bose Mini II SoundLink (eqMac)": eqMac's virtual device reports **1,312 frames of device latency at 16 kHz = 82 ms**, and behind it the Bose is a Bluetooth speaker in call mode (reported). Bluetooth links commonly add 100 to 200 ms or more (published, RTINGS; not measured on the Bose). If AudioLab plays to the system default, a pad can take **200 ms or more** to sound.
- **Auto buffer only goes up.** After a few dropouts Auto moves 256 → 512 → 1,024 → 2,048 frames and never comes back (code: `ABUF`, `autoBufCheck`). Measured on the build machine: 17 ms total at 128 frames, 47 ms at 512, **86 ms at 1,024**.
- **A resonance suppressor, pitch shifter or pitch corrector anywhere** delays everything by 46 ms more, including what you play.

### What it can become

| Path | Key to sound | How |
|---|---|---|
| Today | about 30 ms (40 while playing, spikes past 100) | |
| Web engine with the quick options L1 to L5 | **about 13 to 15 ms**, steady | wired output, 128-frame buffer with a 64-frame render block, no +2 ms, the played track outside delay compensation, notes that skip the main thread |
| Native engine, live path (L13, L15) | **about 2 to 3 ms** | 32 frames on the Gryphon: 0.67 ms block + 14 + 14 frames (0.58 ms) + at most one block of wait + about 1 ms USB MIDI (calculated; 32 frames ran clean with Serum 2 on the user's M4, reported) |

### The three biggest findings

1. **Most of today's delay is not the engine's arithmetic.** It is the output device and its route, a buffer that only grows, delay compensation that also delays what you play, and the page's main thread that is busy drawing while the song plays. Four of the five can be fixed in the web engine now.
2. **One AudioContext is one core, and Chrome puts every real-time AudioContext of a page on the same thread** (Chromium's 2020 change, Chrome 87: one real-time thread shared by all AudioContexts). Measured: the Fractals remake needs 20.5 % of one build-machine core per second of sound; two copies 39.5 %; **four copies 102 %: it runs out**, with 894 dropouts in 9.5 s of live play at Auto 256 and 856 at 512. Offline renders can use more cores (each OfflineAudioContext gets its own thread), so the web engine's only multicore route is to render ahead what is not being played (L9). The native engine can spread the graph over the M4's four performance cores (L12).
3. **Every serious DAW runs two paths**: the track you play at the device's small buffer, and everything else computed ahead in a larger buffer on all cores (Cubase ASIO-Guard, Logic live and playback tracks, Studio One's dual buffer, REAPER anticipative FX). This is the design that gives low playing latency *and* big projects at once. It needs the native engine to be done properly (L15); the web engine can do a coarse version (L9).

---

## 1. Measurements (this task)

Scripts in `tools/engine-lab/ae2/`: `latency_chain.py` (key to sound), `perf_load.py` (CPU per track, the song at x1, x2, x4, live load), `pdc_live.py` (delay compensation), `probe.py` (what Chromium reports per buffer setting). Results beside them as JSON.

### 1.1 Key to sound in the web engine (build machine)

Method: Playwright presses a real key (it goes through Chromium's input pipeline like a keyboard). The app's keydown handler calls `noteOn` on an armed track. A tap worklet on the track's input finds the note's first sample. Times are taken from the event's own `timeStamp`, the handler's `performance.now()`, `ctx.currentTime` and `ctx.getOutputTimestamp()` (which maps context time to the moment the browser says it is heard). 12 presses per case.

| Case | Buffer (render block) | Chromium reports base / output | Main thread wait (median, worst) | App start + block wait | Render runs ahead of what is heard | Total (median, worst) |
|---|---|---|---|---|---|---|
| idle, Lead (worklet voice) | 128 (128) | 2.9 / 8 ms | 5.8, 31 ms | 2.95 ms | 9.1 ms | **17.4**, 43 ms |
| idle, Lead | Auto 256 (128) | 10 / 32 ms | 5.6, 8.8 ms | 2.04 ms | 32.8 ms | 43.1, 47 ms |
| idle, Lead | 512 (256) | 11.6 / 32 ms | 5.1, 27 ms | 2.04 ms | 41.6 ms | 47.0, 72 ms |
| idle, Lead | 1,024 (512) | 23.2 / 72 ms | 4.9, **270 ms** | 2.04 ms | 77.6 ms | **86.1**, 359 ms |
| idle, Kick (built-in nodes) | 128 (128) | 2.9 / 8 ms | 4.1, 13 ms | 0 ms | 9.6 ms | 15.1, 25 ms |
| song playing, Lead high | 128 (128) | 2.9 / 8 ms | 2.5, 45 ms | 2.04 ms | 9.8 ms | 14.3, 58 ms |
| song playing, Lead high | Auto 256 (128) | 10 / 32 ms | **25.4, 119 ms** | 2.04 ms | 33.7 ms | 62.7, 158 ms |

Notes:
- These totals stop at the track's input; delay compensation (1.3) comes on top.
- The "runs ahead" column is Chromium's own buffering plus what the (fake) device reports. On Linux Chromium picks 441 frames for a 256-frame hint and the fake device reports 32 ms; on a Mac the same setting is smaller (section 0 estimate). The main-thread and start numbers do not depend on the device.
- The build machine has two slow cores; the M4's performance cores are faster per thread (estimated two to three times), so main-thread waits on the Mac should be shorter, but the long tasks are the same kind.

### 1.2 Long tasks on the main thread while playing

`perf_load.py`, 9.5 s of play from bar 161 (the Peak), Fractals x1: **51 long tasks (over 50 ms each), 3.5 s in total, the longest 120 ms** at Auto 256; at x2 75 tasks, 6.3 s, longest 211 ms. A key press or a Push pad that lands in one waits for it to end. The drawing lanes (A, E) own most of what runs there.

### 1.3 Delay compensation on the played track

`pdc_live.py` on the Fractals remake: the "Kick & Bass" and "Drums" groups each have a compressor that reports 6 ms (`fxLat`: comp and OTT 6 ms, multiband 6.2 ms, clipper 2.9 to 4.4 ms, drive 4.4 ms, limiter its look-ahead, pitch shifter, pitch corrector and resonance suppressor 2,048 frames = 46 ms). The engine delays every other track to line up, **the armed track included**: the Lead is delayed 6.0 ms today. One resonance suppressor on the Bass makes it 52.5 ms; a limiter with 10 ms look-ahead makes it 16 ms.

### 1.4 CPU per track and where a big project runs out

`perf_load.py`: 8 bars of the Peak (bars 161 to 168, 13.2 s) rendered in one OfflineAudioContext (one thread), time per second of sound. Each solo render includes the master chain (compressor and a 4x oversampled clipper), about 15 to 17 ms per second, so subtract that floor for the track itself.

| Track (kind) | ms per s of sound | Track (kind) | ms per s |
|---|---|---|---|
| Impact (sfx) | 62.0 | Hat (drum) | 36.3 |
| Blip (sfx) | 60.4 | Kick (drum) | 35.7 |
| Hook right (plant synth, delay) | 56.2 | Percussion (drum) | 35.6 |
| Downlifter (sfx) | 55.4 | Snare (drum) | 34.8 |
| Acid (acid synth) | 49.9 | Lead (plant, delay) | 33.8 |
| Hook left (plant, delay) | 45.8 | Arp (plant, delay) | 33.6 |
| Lead high (plant, delay) | 39.6 | Clap (drum) | 33.1 |
| Open hat (drum) | 38.4 | Crash, Toms, Riser, Wind, Lead low, Pad, Shaker, Snare roll | 17 to 30 |
| Bass (plant, sidechain) | 36.8 | | |

| Project | Tracks | One core's share, offline | Live, Auto 256 (block 128): load avg, peak, dropouts in 9.5 s | Live, 512 (block 256) |
|---|---|---|---|---|
| Fractals x1 | 30 | 20.5 % | 39 %, 95 %, 6 | 30 %, 72 %, 0 |
| Fractals x2 | 60 | 39.5 % | 70 %, 107 %, 20 | 59 %, 100 %, 5 |
| Fractals x4 | 120 | **102 %** | 132 %, 894 dropouts | 110 %, 856 dropouts |

On the M4 (estimated two to three times faster per thread) x4 would take roughly 35 to 50 % of one core in the same engine, and peaks would come close to the limit at small buffers. Everything is on one core whatever the machine has.

### 1.5 What the desktop shell adds

- Electron uses Chromium's own audio path, so it adds no buffer of its own. Its flags (`desktop/main.js`): autoplay without a gesture, no background throttling, GPU rasterisation. Nothing raises the audio thread's priority or changes the buffer (Electron was not run here: its binary is not installed on the build machine).
- **The native bridge (stage N2) adds a 40 ms ring** between the page's sound and the native engine (`docs/native-mac-build.md`, NB-R5: 40 ms is the margin that held through 25 ms gaps at the feeder). Playing through the bridge would add 40 ms to every key press. See L14.

---

## 2. Findings with sources

### 2.1 How DAWs reach low playing latency with heavy projects

| DAW | How | Source |
|---|---|---|
| Cubase, Nuendo | ASIO-Guard: tracks that are not monitored or record-armed are computed ahead in a larger buffer; armed instrument and monitored tracks switch to the real-time path at once. Levels 23, 35, 93, 140, 280 ms ahead (Cubase 16). | [Steinberg: ASIO-Guard](https://www.steinberg.help/r/details-on-asio-guard-in-cubase-and-nuendo), [Steinberg help center](https://helpcenter.steinberg.de/hc/en-us/articles/206103564) |
| Logic Pro | "Playback tracks" computed ahead (process buffer range Large); the selected instrument track is "live" at the device buffer; with "Playback & Live Tracks" each live strip can use its own core; selecting an instrument track during playback makes it live and costs more. | [Apple: multithreading](https://support.apple.com/HT205975), [Apple: avoid overloads](https://support.apple.com/en-us/HT203930) |
| Studio One | Dual buffer since 3.5: Device Block Size sets monitoring latency, Process Block Size (Dropout Protection) runs playback and plug-ins; native low-latency monitoring (green Z) needs Process larger than Device. **Only plug-ins adding under 3 ms may sit on the low-latency monitoring path**; sends to bus effects still carry the larger buffer. "The total amount of data that needs to be processed is still the same. It's just better distributed." | [Sound On Sound: Studio One buffers](https://www.soundonsound.com/techniques/studio-one-buffers-low-latency), [PreSonus FAQ](https://support.presonus.com/hc/en-us/articles/360045431251-Studio-One-5-Audio-Dropout-Protection-and-Low-Latency-Monitoring-FAQ) |
| REAPER | Anticipative FX: processing "at irregular intervals, often out of order, and slightly ahead of time"; input monitoring falls back to synchronous processing; over 95 % use of all cores on 8+ core machines (2011). | [Sound On Sound 2011](https://www.soundonsound.com/techniques/running-multiple-plug-ins) |
| Ableton Live | No split buffer. Splits the graph into independent chains, one thread each; the critical path limits what fits; runs audio on performance cores. "Reduced Latency When Monitoring" removes delay compensation from the armed, monitored track only (returns may then be out of sync; not a fix for the track's own device latency). A track behind 80 ms of compensation "will feel quite sluggish when playing". | [Ableton: multicore FAQ](https://help.ableton.com/hc/en-us/articles/209067649), [Reduced latency when monitoring](https://help.ableton.com/hc/en-us/articles/209072249), [How latency works](https://help.ableton.com/hc/en-us/articles/360010545559) |
| FL Studio | Buffer advice: 128 samples as the start on Apple Silicon; "Triple buffer" doubles latency to survive near-100 % load; "Smart disable" turns off instruments and effects while they are inactive; multithreaded generator and mixer processing; "Safe overloads" leaves CPU for the interface. | [Image-Line: audio settings](https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/envsettings_audio.htm) |
| Bitwig | Engine apart from the interface, plug-ins sandboxed in modes; no public detail of a render-ahead path was found (a KVR thread searched turned out to be about Tracktion, which has none). | [Bitwig: modern foundations](https://www.bitwig.com/modern-foundations/), [KVR thread](https://www.kvraudio.com/forum/viewtopic.php?p=8879243) |
| Samplitude, Sequoia | "Hybrid audio engine": a low-latency path for monitored tracks and a larger buffer for the rest; "economy tracks". | [Boris FX: Hybrid audio engine](https://cdn.borisfx.com/borisfx/Documentation/sequoia-2026/en/Content/Hybrid%20Audio%20Engine.htm) |

### 2.2 Multicore graph scheduling

Already researched for the native engine in `docs/research-native-mac.md` 1.2 and 1.4: worker threads must be real-time and join the device's audio workgroup on Apple Silicon or land on efficiency cores; schedule by inputs-done (Kahn) with the audio thread working too; measure the critical path; CLAP's host thread pool lets the host own the threads. Not repeated here.

### 2.3 What Chromium's Web Audio allows

- **latencyHint**: AudioLab already passes seconds (`bsz / sampleRate`) or `'interactive'` / `'balanced'` (`ensureCtx`). Measured on this machine: 128 → base 2.9 ms; 256 → 10 ms (Linux picks 441 frames); 512 → 11.6 ms; 1,024 → 23.2 ms.
- **Render quantum (`renderSizeHint`)**: AudioLab already asks for a larger block at big buffers (`rqWant`). A Chrome 153 loop-back on an M4 with an RME Babyface: **25.7 ms round trip at a 64-frame block, 28.6 ms at 128, 31.5 ms at 256** ("a hint, not a guarantee"; requested 64 gave 64) ([classmethod, September 2026](https://dev.classmethod.jp/en/articles/chrome-153-webaudio-render-size-hint-latency/)). The W3C working group expects the configurable render quantum in the next Web Audio revision, Q4 2026; Chrome also shipped "Output Buffer Bypass", which "removes one buffer of latency" ([TPAC 2025 update](https://www.w3.org/2025/11/TPAC/demo-audio-wg-update.html)).
- **The worklet thread**: since Chrome 87 the AudioWorklet runs on a real-time priority thread when the context is real-time and the document top-level; **one real-time thread is shared by all AudioContexts** and one background thread by all OfflineAudioContexts ([Chromium: changing the thread model of Audio Worklet, 2020](https://groups.google.com/a/chromium.org/g/platform-architecture-dev/c/sxpZizgpDFM)). The hop from Chromium's audio device thread to the worklet thread was named "the weakest link" ([scheduler-dev, 2019 to 2020](https://groups.google.com/a/chromium.org/g/scheduler-dev/c/-NRtiAlX1Xw/m/CnB-wnnHBAAJ)). Nothing found says Chromium joins macOS audio workgroups.
- **Playout statistics** (`ctx.playbackStats`): glitches and average latency, which AudioLab's Auto buffer already reads where available.
- **A browser DAW's floor**: Soundtrap reported "something like 30ms best case round-trip latency" ([W3C workshop 2021](https://w3.org/2021/03/media-production-workshop/talks/ulf-hammarqvist-audio-latency.html)). Chris Wilson (Google, 2014): a 128-frame block at 44.1 kHz is just under 3 ms, double-buffered 6 ms ([public-audio](https://lists.w3.org/Archives/Public/public-audio/2014JulSep/0177.html)).
- **What only native can do**: choose the device buffer exactly (32 frames ran clean on the M4), take exclusive use, join the device's workgroup, run the graph on several cores within one deadline, read MIDI on its own real-time thread with hardware timestamps, run two paths (live and ahead) in one engine.

### 2.4 MIDI input latency

- **Web MIDI in Chromium** delivers each message to the page's **main thread** as an event with a timestamp (`MIDIMessageEvent.timeStamp`, from the system's MIDI time). Whatever runs on the main thread delays it: the waits in 1.1 and 1.2 apply to Push 1 pads exactly as to keys. Web MIDI is not available inside an AudioWorklet.
- **In Electron** the main process can read MIDI with a native module (or the native engine can read CoreMIDI) and post messages to the AudioWorklet through a `MessagePort` handed to the page and on to the worklet; the page's main thread is then out of the path (estimated; not built).
- **Native**: CoreMIDI delivers packets with host-time stamps on its own high-priority thread; an engine places each note at its sample in the next block. USB MIDI full speed polls every 1 ms (estimated).

### 2.5 Low-latency monitoring of the armed track while the rest renders ahead

From 2.1: the armed or selected track and what it feeds run at the device buffer; everything else ahead. Rules other DAWs apply: only low-latency devices on the live path (Studio One: under 3 ms); the live track bypasses delay compensation (Ableton); selecting a track during playback makes it live (Logic); automation, tempo and transport jumps invalidate what was computed ahead, so the ahead path must refill within one period (Cubase advice). The same-bits rule from `docs/research-native-mac.md` 1.4 holds: a track computed ahead and a track computed live must give identical samples.

### 2.6 Output devices

- Reported on the user's Mac: Gryphon at 48 kHz, 14 + 14 frames of device latency and safety offset; Mac mini speakers and BlackHole 512-frame default buffers; eqMac's device 1,312 frames at 16 kHz (82 ms); Bose in Bluetooth call mode at 16 kHz.
- Bluetooth A2DP links commonly add 100 to 200 ms or more ([RTINGS latency tests](https://www.rtings.com/headphones/learn/research/latency)); Apple's own forum shows output latency of Bluetooth devices changing over time ([Apple forum 679274](https://developer.apple.com/forums/thread/679274)).
- Windows: WASAPI shared adds the engine's period; exclusive and ASIO reach 3.7 to 8 ms round trip at 64 frames on good interfaces (`docs/research-native-windows.md` 1.6).

---

## 3. Options

Stars: ★★★★★ do it, ★★★★ strongly worth it, ★★★ good, ★★ optional, ☆ not recommended. "Gain" is milliseconds off a key press or CPU saved; "web" means the engine in `index.html` today, "native" means `native/`.

### Playing latency

| # | Option | Gain | Risk | Web or native | How it would feel | Stars |
|---|---|---|---|---|---|---|
| L1 | **Output check.** Warn when the output is Bluetooth, a virtual device (eqMac, Background Music, BlackHole) or a device in call mode at 16 kHz; one button "Play through the Gryphon" (or the AMS-24). | 82 ms (eqMac) plus 100 to 200+ ms (Bluetooth) | none | both; lane B (audio devices) with lane F's notification | pads that answer instead of echoing; obvious once seen | ★★★★★ |
| L2 | **A playing buffer.** Auto comes back down; while a track is armed or the keyboard is on (and the transport is stopped) use 128 frames with a 64-frame render block; the larger buffer for mixing. | 3 to 5 ms against Auto 256; up to 70 ms against the 1,024 trap (measured 17 vs 86 ms) | dropouts on heavy songs (pairs with L8, L9) | web; lane B | the same key feels tight in a big song | ★★★★ |
| L3 | **Start played notes at once.** Drop the +2 ms start offset for worklet voices (drum voices already start at once). | 2 ms | the voice must start inside a block | web; the voice engine's owner (proposed lane C) | barely felt alone; adds up with the rest | ★★★ |
| L4 | **The played track skips delay compensation** (Ableton's "reduced latency when monitoring"), recorded notes placed by the compensated clock. | 6 ms in Fractals today; 46 ms more with a resonance suppressor or pitch device anywhere | the played note is early against a compensated track by that amount while you play (it is how Ableton and Studio One do it) | web and native; lane C | a mixing device on the master never makes the keys sluggish again | ★★★★★ |
| L5 | **Notes that skip the main thread** (desktop): MIDI read in the shell's main process (later in the native engine) and posted into the audio worklet through a MessagePort, with its timestamp. | main-thread wait: median 2.5 to 25 ms, worst 45 to 270 ms → about 1 ms, steady | medium: a native MIDI module in the shell; only worklet instruments can be started from the worklet (all of AudioLab's own voice engines are worklets; built-in-node drums need a worklet path) | desktop app; lane C with NB for the shell | Push 1 pads stay tight while the screen is busy | ★★★★ |
| L6 | **A lighter main thread while playing**: break up long tasks, draw less while a key is held, put input first. | the worst cases (120 to 280 ms long tasks) | low; drawing lanes must agree | web; lanes A and E | fewer late notes in a full arrangement | ★★★ |
| L7 | **Steady timing**: place each note at its event time plus a fixed offset instead of "as soon as possible". | jitter of up to one block plus the main thread → under 0.1 ms; costs a fixed 3 ms | low | web and native; lane C | drums feel even; latency slightly higher but constant | ★★ |

### Big projects and CPU

| # | Option | Gain | Risk | Web or native | How it would feel | Stars |
|---|---|---|---|---|---|---|
| L8 | **Sleep idle tracks** (FL's "Smart disable"): a track with no notes in the next bars and a silent tail stops computing. | estimated 20 to 40 % in sparse sections (risers, impacts, breaks); the sfx tracks are among the costliest (55 to 62 ms per s) | tails cut if silence is judged wrong | web now, native later; engine owner (proposed new lane or NB) | fewer dropouts in the busy drops | ★★★★ |
| L9 | **Render ahead in the web engine** (a coarse ASIO-Guard): tracks that are not armed are rendered by OfflineAudioContexts on other cores into a window ahead of the playhead and played as buffers; the armed track and the master stay live; any edit re-renders that track. | live thread load from about 100 % (x4 here) to the armed track plus the master; the buffer can stay small | high: invalidation on edits, automation and tempo; memory (stereo float is about 10 MB per track-minute, so a window, not the whole song) | web; new task series RA | big songs play at the playing buffer | ★★★★ |
| L10 | Several AudioContexts to use more cores | none: Chrome runs all real-time contexts of a page on one thread | | web | | ☆ |
| L11 | **Cost per track shown**: ms per second of sound per track in the mixer, from a short background render (this task's method). | finds the heavy track | low | web; lane E (CPU graph) | you see what to freeze | ★★★ |

### Multicore (native engine)

| # | Option | Gain | Risk | Stars |
|---|---|---|---|---|
| L12 | **Parallel graph on the performance cores**: real-time workers joined to the device's workgroup, inputs-done order, the critical path shown (NR1, NR3 in `docs/research-native-mac.md`). | 4 performance cores instead of one; Fractals x4 fits at small buffers (estimated) | medium; the known Apple Silicon trap if threads do not join | ★★★★★ |
| L13 | **MIDI in the engine**: CoreMIDI (and Windows MIDI) read by the engine, timestamps placed at the sample; Push 1 to sound about 2 to 3 ms at 32 frames on the Gryphon. | 10 to 30 ms against the web path | low | ★★★★★ |
| L14 | **Never play through the bridge**: the N2 bridge adds a 40 ms ring; keep the web output for playing until the native engine makes the played track itself. | avoids +40 ms | none (a rule for NB) | ★★★★★ |

### The live track and render-ahead (native engine)

| # | Option | Gain | Risk | Stars |
|---|---|---|---|---|
| L15 | **Two paths**: the live set (armed or selected track, what it feeds, the master) at 32 to 64 frames; everything else 23 to 35 ms ahead on the workers; same bits either way. | low latency and big projects together | high; the core design of N3 (point 5 of the Mac research) | ★★★★★ |
| L16 | **Live path rules**: only devices under 3 ms on the live path while playing (Studio One); a look-ahead device on the played track is marked and can be bypassed while recording; a send from the live track to a reverb keeps that return live. | keeps the live path at the device buffer | low | ★★★★ |
| L17 | **"Live" marker and an honest read-out**: the track that runs live is marked; Settings shows key to sound (buffer, device, compensation, measured loop-back) and the app can measure it with a cable (NR-LAT, U3, U6). | trust in the number | low | ★★★★ |

---

## 4. Proposed tasks

| Task | What | Lane or engine | Size | Proof |
|---|---|---|---|---|
| AE2-1 | L1 output check and warning; L2 playing buffer, Auto that comes down | lane B (Settings, audio devices), lane F for the notice | 1 run | headless: fake device names trigger the warning; Auto steps back down after a clean minute; user's Mac: the read-out with the Gryphon |
| AE2-2 | L4 played track outside delay compensation; L3 no start offset; recording keeps note positions | lane C (live playing) | 1 run | `latency_chain.py` with a resonance suppressor in the song: total does not change; recorded notes land on the grid within 1 ms |
| AE2-3 | L5 notes past the main thread in the desktop app | lane C with NB for `desktop/` | 2 runs | electron smoke test: MIDI from the IAC port to sound while a 200 ms long task runs on the page |
| AE2-4 | L6 main-thread diet while playing | lanes A and E | 1 run each | long tasks while playing under 50 ms on the build machine |
| AE2-5 | L8 sleep idle tracks | engine owner (new lane or NB) | 1 run | Fractals renders bit for bit the same; CPU in the Peak lower |
| RA1 to RA3 | L9 render ahead in the web engine (window, invalidation, memory) | engine owner | 3 runs | the Fractals x4 plays without dropouts at 256 on the build machine; rendered and live samples identical |
| AE2-6 | L11 cost per track | lane E | 1 run | numbers equal to `perf_load.py` within 10 % |
| NB (folded) | L12 to L17 | NB, stages N3 to N4 | already in NR1, NR3, NR4, NR-LAT | as in `docs/research-native-mac.md` |

Order suggested: AE2-1 and AE2-2 first (largest gain for the least work, both today), then AE2-3, then L9 or the native live path, whichever lands first.

---

## 5. What was not measured, and assumptions

- No loop-back cable on a real device here: the Mac's Chromium output part (about 16 ms at Auto 256) is an estimate from a published Chrome 153 measurement on an M4 and the Gryphon's reported device latency. The pick page's tester measures it on the user's own Mac in a browser.
- Web MIDI could not be measured (no MIDI devices on the build machine); the Push 1 path is the same main-thread path as keys, plus about 1 ms of USB.
- The M4 per-thread speed against the build machine (two to three times) is an estimate.
- Electron was not run; the analysis of `desktop/main.js` says it adds no audio buffer of its own.

## Sources

- [Steinberg: ASIO-Guard](https://www.steinberg.help/r/details-on-asio-guard-in-cubase-and-nuendo); [Steinberg help center](https://helpcenter.steinberg.de/hc/en-us/articles/206103564)
- [Apple: Logic multithreading](https://support.apple.com/HT205975); [Apple: avoid overloads](https://support.apple.com/en-us/HT203930)
- [Sound On Sound: Studio One buffers and low latency](https://www.soundonsound.com/techniques/studio-one-buffers-low-latency); [PreSonus: dropout protection and low-latency monitoring FAQ](https://support.presonus.com/hc/en-us/articles/360045431251-Studio-One-5-Audio-Dropout-Protection-and-Low-Latency-Monitoring-FAQ)
- [Sound On Sound 2011: REAPER anticipative FX](https://www.soundonsound.com/techniques/running-multiple-plug-ins)
- [Ableton: multicore](https://help.ableton.com/hc/en-us/articles/209067649); [Ableton: reduced latency when monitoring](https://help.ableton.com/hc/en-us/articles/209072249); [Ableton: how latency works](https://help.ableton.com/hc/en-us/articles/360010545559)
- [Image-Line: FL Studio audio settings](https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/envsettings_audio.htm)
- [Bitwig: modern foundations](https://www.bitwig.com/modern-foundations/); [KVR: hybrid buffering thread](https://www.kvraudio.com/forum/viewtopic.php?p=8879243); [Boris FX: Sequoia hybrid audio engine](https://cdn.borisfx.com/borisfx/Documentation/sequoia-2026/en/Content/Hybrid%20Audio%20Engine.htm)
- [classmethod: Chrome 153 renderSizeHint latency on an M4](https://dev.classmethod.jp/en/articles/chrome-153-webaudio-render-size-hint-latency/)
- [W3C TPAC 2025: Audio WG update](https://www.w3.org/2025/11/TPAC/demo-audio-wg-update.html)
- [Chromium: changing the thread model of Audio Worklet](https://groups.google.com/a/chromium.org/g/platform-architecture-dev/c/sxpZizgpDFM); [Chromium scheduler-dev: realtime priority for AudioWorklet](https://groups.google.com/a/chromium.org/g/scheduler-dev/c/-NRtiAlX1Xw/m/CnB-wnnHBAAJ); [Chromium: thread priority in Blink and WebAudio rendering](https://groups.google.com/a/chromium.org/g/platform-architecture-dev/c/EnlQMTRwyrw/m/nmdihrCSAwAJ)
- [W3C workshop 2021: audio latency in browser-based DAWs](https://w3.org/2021/03/media-production-workshop/talks/ulf-hammarqvist-audio-latency.html); [public-audio 2014: Chris Wilson on buffering](https://lists.w3.org/Archives/Public/public-audio/2014JulSep/0177.html)
- [RTINGS: latency tests](https://www.rtings.com/headphones/learn/research/latency); [Apple forum 679274: Bluetooth output latency](https://developer.apple.com/forums/thread/679274)
- Earlier AudioLab research: `docs/research-native-mac.md`, `docs/research-native-windows.md`, `docs/native-mac-picks.md`, `docs/native-mac-build.md`
