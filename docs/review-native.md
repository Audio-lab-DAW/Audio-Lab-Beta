# Independent review of the native engine (task RN5)

Review only, written 27 November 2026. No code was changed: `index.html`, `desktop/`, `native/` and `tools/` were not touched. Only this file is new.

**Reviewer's position.** I did not build any of this. I read the plan, the picks, the build log, the five research documents (RN1 Mac, RN2 Windows, RN3 lessons, RN4 screens and RN6 testing and legal; all five existed), the NM1, NB-N1, NB-N2a, NB-N2b and NL4 entries in `docs/backlog-log.md`, the user's report in `tools/native-lab/reports/`, every C++ and JavaScript file in `native/` and the bridge (`desktop/native-engine.js`, `desktop/preload.js`, `native/bridge/`), and the parts of `index.html` the native engine has to match (`wlLoad`, `dnGuard`, `renderMixChunked`, the project writer). I read the code line by line where it touches audio, threads or devices.

**What I ran (Linux x86-64, this machine):**
- `alengine selftest` built with g++ 13 under AddressSanitizer and UndefinedBehaviorSanitizer. It passed and found no faults (26 s).
- It also passed built with `-ffp-contract=fast -march=haswell` (fused multiply-add allowed).
- A ThreadSanitizer stress test of `ring.h` in three cases:
  - normal one-writer, one-reader use: clean;
  - `init()` called while the writer runs, which is what the `source` command can do: **7 data races, and the program hung** (stopped by the time limit);
  - switching `follow` on and off: clean.
- 2 million random messages through `parseMsg` under ASan/UBSan: no fault.
- The edge cases of `floatToInt`.
- A frequency-response measurement of the clock follower's filter.
- cppcheck 2.13 on `native/`: one portability note (`engine_main.cpp:160`) and one style note (`vst3_format.cpp:108`).
- clang-tidy 18 on the engine: only return values not checked and the widening of int products in the self test.
- UBSan confirmed that casting a negative number to `uint32_t`, as `engine_main.cpp` does with `(uint32_t)m.num(...)`, is undefined behaviour.

**What I could not run:** anything that needs Core Audio, the VST3 SDK host on macOS, or RealtimeSanitizer (clang 18 here has no runtime for it, and LLVM 20 or newer is needed). These need the macOS runner (section 6).

**NB moved on while this review was written.** My clone was at `b79ab32`. By the time I pushed, NB-N3a (the engine core: devices, chains, `alrender`, the dynamics family, 119 of 119 cases bit for bit on Linux) and NB-N3b (the mixer in `native/engine/mix/`, 10 of 10 scenes bit for bit on Linux) had landed. The findings above were reviewed against `b79ab32`. A short check of the new code shows:
- **It confirms A5.** N3b found on its own that "the web engine's own order of tracks into a bus changes between renders", so the web export is not repeatable with three or more tracks into one bus.
- **It answers part of A2, not all of it.** `mix_graph.h:52` keeps **one** generator "shared by the devices in creation order, as in the page", and draws for whole quanta, as Chromium does. That matches the serial page, which is good work. But it ties the engine to one serial order, so NR3's parallel graph cannot use it for any device that draws random numbers, and the generator would be a data race the day two threads share it. D2 stands.
- **It sharpens A4.** `mix_graph.h:10` notes that the web engine uses 128-frame quanta while playing and **512 in an export** (`renderSizeHint`). So `dnGuard`'s "every 16 calls" flush and its silence gate fall at different sample positions in playback and in export. The reference itself differs between the two, which is one more reason for the grid rule in sample time (D4).
- **A6 is still open.** `-ffp-contract=off` is still set target by target (`alnative`, `alrender`, `almix`), not for the whole engine.

The new code was not read line by line. It is worth its own short review once NB-N3 settles.

---

## 1. Summary: the top ten

| # | Issue | Severity | Where |
|---|---|---|---|
| 1 | **No sample-rate agreement between the page and the engine.** The engine plays the page's samples "at the device's rate", but the page's AudioContext runs at the rate of its own clock device. On your Mac today the default output (eqMac) runs at **16 kHz** while the Gryphon runs 48 to 384 kHz. N2c as planned would play the mix at the wrong speed. The follower can absorb 2,000 ppm, not a factor of 3. A rate change from outside (`onWatch` "rate") does not update the ring either. | **blocker** (for N2c) | `engine_main.cpp:236, 268-270`; `page-tap.js`; `native-engine.js:90-97` |
| 2 | **The N2b code has never been compiled on macOS, and nothing native runs on a push.** All six `native-engine.yml` runs were cancelled or are still queued. Every native workflow starts only by hand. A regression in `native/` or the bridge is caught by nobody until someone remembers to start a run on a runner that may not come. | **blocker** (before N2c) | `.github/workflows/native-*.yml` |
| 3 | **One shared random generator for all worklets.** `wlLoad` replaces `Math.random` with **one** seeded generator for the whole worklet scope. Which device gets which number depends on the order in which Chromium runs every worklet node in the graph. A native graph, and above all a parallel one, cannot reproduce that order. So "the same bits" is impossible for every device that draws random numbers (Crusher jitter and dither, Crackle, grains, Emit and others) once two such devices are in a song. Shared across threads, it is also a data race. | **blocker** (for N3: decide before the first port) | `index.html` `wlLoad`; `al_crush.h:63` |
| 4 | **The reference export is chunked.** `renderMixChunked` renders 24-beat pieces in fresh OfflineAudioContexts, each with a fresh random generator and fresh device state, and pre-rolls only 10 to 64 beats. "The web export" is therefore not a continuous render. A native single pass cannot match it bit for bit wherever random numbers, or memory longer than the pre-roll, are involved. | high | `index.html` `renderMixChunked` |
| 5 | **The sound path runs through the Electron main process.** Every 128-frame block (375 a second) passes through `port.on('message')` in the main process, which also runs menus, IPC, the updater and window work. A pause there longer than the 30 ms prefill empties the ring and costs at least 30 ms of silence before it refills. `feed()` ignores back-pressure, so a stalled engine makes the main process buffer about 1.4 GB an hour. | high | `native-engine.js:101-118`; `engine-bridge.js:204-208` |
| 6 | **Switching the sound source is synchronised by `sleep(30 ms)`.** The ring is re-initialised (its buffer reallocated) **before** the old socket thread is stopped. ThreadSanitizer shows the race, and the reproduction hung. | high | `engine_main.cpp:265-273`; `ring.h:32-37` |
| 7 | **Bit-perfect and exclusive use cannot both hold in stage N2.** With exclusive use on the DAC, the page needs another clock device, so `follow` mode must resample. Bit-perfect `exact` mode works only with the page and the engine sharing the device without exclusive use. Your first priority (U4a) is reachable in N2 only in shared mode. This needs your decision (section 5, D1). | high (decision) | `native-mac-build.md` N2a/N2b |
| 8 | **No state model for N3 yet.** The page owns all project state, and the engine is a stateless output. Your picks require "the engine keeps all state". The protocol has no request ids (answers are matched by command name, so a late answer resolves the wrong caller), no protocol version and no edit or undo model. This has to be designed before the first port, not after twenty. | high | `engine-bridge.js:162`; picks line 33 |
| 9 | **The clock follower is a 19 to 20 kHz low-pass that switches off at fraction 0.** At 44.1 kHz it measures -0.8 dB at 19 kHz, -4.2 dB at 20 kHz and -12.7 dB at 21 kHz. At 48 kHz it measures -1.4 dB at 21 kHz. Exactly at fraction 0 it is flat, so the top octave's response jumps each time the read position slips a whole sample (about every 0.45 s at 50 ppm). The self test checks only 997 Hz and 15 kHz. | medium | `follow.h:231-254` |
| 10 | **No output safety in the engine.** NaN and Inf pass straight to the device in the float path, and nothing clips. The page can set the DAC's own hardware volume to 100 %. The program update that drives the page is not signed (RN6). The integer path reads the device format once and never watches it, so a format change while running sends wrong bytes, which is loud noise. | medium (high once others use it) | `coreaudio.cpp:241-257, 279-288`; `engine_main.cpp:260` |

**In all: 34 issues, 3 blockers, 8 high, 15 medium, 8 low.** They are A1 to A15 (section 3), C1 to C14 (section 4) and P1 to P5 (section 6).
- Blockers: A1, A2, P1.
- High: A3, A4, A8, A9, A10, C1, P2, P5.
- Medium: A5, A6, A7, A11, A12, A13, A14, C2 to C7, P3, P4.
- Low: A15, C8 to C14. None of them means the route is wrong. Route C then B, own code on the HAL, and VST3 behind a format-neutral interface all stand. The blockers sit at two gates: N2c (items 1 and 2) and the first N3 port (item 3).

---

## 2. Risk register

Likelihood and impact: H high, M medium, L low. "Stage" is the latest point at which the guard must be in place.

| Risk | Where | Lik. | Impact | How to detect | Fix or guard | Stage |
|---|---|---|---|---|---|---|
| Mix plays at the wrong speed or pitch, or underruns endlessly | page AudioContext rate vs engine device rate | H | H | a status field `pageRate` vs `deviceRate`; a test at 16/44.1/48/96 kHz | rate handshake (R2) | N2c |
| A regression ships unseen | no native CI on push; macOS runners unavailable | H | H | a red check on the commit | Linux CI on every push plus a macOS gate (R1) | now |
| Native renders never match web bits for random-using devices | shared `Math.random` in `wlLoad` | H (certain with 2+ such devices) | H | a two-device bit test | per-device generator streams, decided with you (D2, R6) | before the first N3 port |
| The "reference" is itself chunk-dependent | `renderMixChunked` | H | M | compare a chunked web export with a single-pass web render | reference = single-pass render (D3) | N3 |
| Gaps when the shell's main thread stalls | `native-engine.js` port handler | M | H | `tap.worstGapMs`, ring `ranEmpty` in a long run with the UI busy | utilityProcess or native add-on, bounded queue (R3) | N2c |
| Memory grows without limit when the engine hangs | `feed()` ignores back-pressure | L | H | main-process RSS in a hang test | bounded queue and a hang watchdog (R3) | N2c |
| Heap corruption or hang on a source switch | `ring.init` before `stopSocket` | L-M | H | TSan stress (reproduced here) | a command queue to the audio thread, then stop, then init (R4) | N2c |
| The audio thread allocates on the first `follow` block | `SincTable::get()` lazy static | H (once per run) | M (one glitch) | RTSan, or a first-block time | build the table at start (R4) | N2c |
| Top-octave dulling and flutter in follow mode | `follow.h` kernel | H | M (audiophile) | response test at 20 kHz / 44.1 kHz | longer kernel, no identity row while following (R5) | N2c |
| Full-scale noise or NaN to the DAC | float path has no scrub; integer format not watched | L | H (ears, speakers) | inject NaN/Inf; change the format while playing | scrub, a clip option, a format listener (R4) | N2c |
| The page raises the hardware volume to 100 % | `volume` command, unsigned update | L | H | audit of the IPC surface | a ramp and a cap confirmed by you; signed updates (RN6) | before anyone else uses it |
| Late or wrong answers to commands | answers matched by command name | M | M | two `status` calls while an `open` takes 4 s | request ids and a protocol version (R4) | N2c |
| Dual state during N3 (page and engine disagree) | no state model | H | H | none today | engine-owned state and an edit protocol (R7) | before the first N3 port |
| FMA changes bits on arm64 only | `-ffp-contract=off` only on target `alnative` | M | M | an arm64 bit test of double state | a global flag and a CI grep (R6) | N3 |
| Plug-ins leave flush-to-zero set and change AudioLab's bits | same thread, no FPCR policy | M | M | a denormal case after a plug-in in a bit test | set FPCR per AudioLab segment; save and restore around plug-ins (R6, R8) | N3/N4 |
| Browser-node devices and the mixer differ from Chromium in the last bits | Chromium summation order, SIMD, platform libm | H | L-M | a null test per family | tolerances per family, written down (R11) | N3 |
| A plug-in crashes when the first of two instances unloads | one `Module` per instance, `bundleExit` per instance | L-M | H | load A, load A, close the first | a module cache, no unload during the session (R8) | N4 |
| Silence or stale audio after a buffer change | `process()` returns false without clearing output | M | M | buffer above `maxBlock` | clear output on failure; reprepare (R8) | N4 |
| Scanner hangs the host | parent `read()` has no timeout; grandchildren keep the pipe open | L-M | H | a test plug-in that spawns a sleeping child | poll with timeout, kill the process group, posix_spawn (R8) | N4 |
| Long exports corrupt | 32-bit RIFF sizes (over 4 GB in 23 min at 384 kHz stereo float) | M (at high rates) | M | a 30-minute export at 384 kHz | RF64 (R9) | N5 export |
| A new file opens silently wrong in an older build | `formatVersion` written, never read | M | H | open a v2 file in today's build | `minReader` and a loader that reads it (RL1, R9) | N4 |
| Drift and leaks over hours | tests of 3 to 20 s | H | M | none yet | 1-hour soak per change, overnight weekly (R10) | N2c |

---

## 3. Detailed findings: architecture

### A1. No sample-rate contract between the page and the engine (blocker for N2c)
- The engine says "Sound reaches it ... at the device's rate" (`engine_main.cpp:10`). The ring is built at `E.rate` (`:268-270`). The page sends whatever its AudioContext renders.
- The page's context runs at the rate of its clock device unless it is created with `sampleRate`. The N2a decision makes that device a different one from the DAC whenever exclusive use is on. On your Mac the default output was eqMac's Bose copy at **16,000 Hz** (`reports/...-report-4.txt`, line 11), and the Gryphon was used at 48, 192 and 352.8 kHz.
- When the DAC's rate changes while sound plays (your Rate menu, Audio MIDI Setup, another app), `onWatch("rate")` updates `E.rate` (`:236`) but not `E.ring.rate`, `target` or `high`. The page keeps sending at the old rate.
- The follower clamps at 2,000 ppm by default, 20,000 at most (`native-engine.js:94`). Exact mode would underrun on every block.
- **Guard (R2):**
  - The bridge creates or recreates the page's AudioContext with `sampleRate` equal to the engine's device rate. Chromium resamples to the clock device on its own side, which is harmless because that device plays silence.
  - The engine reports `pageRate`, given in the `source` command, and refuses to play when it differs from the device rate.
  - A rate event pauses the sound, tells the page to rebuild its context, and resumes.
  - Note for you: rendering the web engine at 352.8 kHz costs about 8 times the CPU of 44.1 kHz.

### A2. The shared random generator makes multi-device bit identity impossible (blocker for N3)
- `wlLoad` puts one generator into the worklet scope (`Math.random=()=>{...}`, the same xorshift-like code as `al_crush.h:15-27`). Every worklet that calls `Math.random` takes the next number. The sequence each device sees depends on how many numbers every other device drew before it in Chromium's render order, and on whether the `dnGuard` silence gate skipped a node (below).
- The NM1 proof used one device alone, so this could not show.
- A native engine with its own graph order will hand out different numbers. A parallel engine (NR3) makes the order non-deterministic, and a shared generator becomes a data race.
- **Decision (D2) and guard (R6):** give every device instance its own stream, seeded from the project's export seed and the device's id. That changes the web engine's sound once, deliberately and versioned (RN3's RL2: algorithm version per device). It has to happen in the web engine **before** porting, so that both engines share the new reference. The alternative, emulating Chromium's render order exactly, is fragile and rules out multicore.

### A3. The reference is a chunked render (high)
- `renderMixChunked`: `SEG=24` beats, a pre-roll `pre=min(s,64,max(W,mapPre(s)))` with `W` = 10, or 20 when a reverb or delay is on.
- Each piece is a fresh `renderMix` with fresh worklet scopes: the generator restarts at its seed, and every filter, delay and envelope starts from zero at `bs`.
- The spliced result differs from one continuous render:
  - wherever random numbers matter;
  - wherever state outlives the pre-roll (long feedback delays, reverb tails over 10 to 20 beats, slow LFOs);
  - wherever a device's behaviour depends on the number of 128-frame quanta since its start (`dnGuard`'s counter).
- The plan says "the exports of the web engine are the reference" (plan section 4), and the gate is "the Fractals export, web against native".
- **Decision (D3):** the reference is a **single-pass** web render of the same span (one `renderMix` over the whole song), made by the shipped Electron on macOS arm64 (see A5). Treat the chunked export as the web engine's own approximation, and measure its difference from the single pass once, to learn how much it already deviates.

### A4. The 128-frame quantum is part of the sound (high; settles RN1 point 5)
- Several behaviours are defined per render quantum, not per sample:
  - `dnGuard` flushes state below 1e-30 every 16 calls of `process`;
  - its silence gate counts quanta of silent input and, after 3 s, **skips `process` entirely** (no state advance, no random numbers drawn);
  - worklet parameters arrive by port message and take effect at the next quantum;
  - k-rate AudioParams change per quantum.
- RN1 point 5 asks to choose between "every device proven block-size independent" and "fixed 128-frame sub-blocks with a ring at the device". Strict block-size independence is impossible for these devices, because the behaviour is defined on the 128-frame grid. A fixed 128-frame ring adds up to 96 frames (2 ms at 48 kHz) on the live path at 32-frame buffers.
- **Recommendation (R6):** a third way. The engine keeps a **virtual 128-frame quantum grid in sample time**. Devices may process any number of frames, but everything that is per quantum (the flush, the silence gate test, parameter take-over, k-rate values) happens exactly at grid boundaries. This is testable bit for bit at block sizes 32, 64, 128, 37 and 512, and it costs no latency.

### A5. What bit identity can honestly promise, family by family
| Family | Bits realistic? | Where it breaks | Guard |
|---|---|---|---|
| Worklet devices without random numbers (19 devices, the same arithmetic) | **yes** | FMA (A6), FPCR (A7), math functions (below), the quantum grid (A4) | the NM1 method, extended |
| Worklet devices with random numbers | **only after A2** | the shared generator order | per-device streams (D2) |
| Instruments in worklets (10) | yes, as above | voice allocation order, random numbers | as above |
| Instruments rendered on the main thread (drums, sampler and others) | **no reference exists**: RN6 found Plant, the samplers and the drum kit render differently on every load today | unseeded randomness in the web engine | make the web side deterministic first, as a versioned change |
| Browser-node devices (16, plus both limiters) | last-bit differences likely; compressor and convolver certainly | Chromium's SIMD `vector_math` (NEON vs SSE), platform `sin`/`cos` in panners and automation curves, the platform FFT | measured tolerance per device, written down (R11) |
| The mixer (gains, sends, groups) | **not bits** once a bus has 3 or more inputs: Chromium very likely sums an input's connections in hash-set order (from knowledge of `AudioNodeInput`; to be checked in Chromium's source, R11), and float sums of 3 or more terms are not associative | the summation order | null test with a threshold (RN6: about -140 dB for gain and mixing) |
| Export resampling | no | Chromium's resampler vs our own | the plan already renders at the project rate first |
| Plug-ins | no (plan 6.9, correct) | | Freeze |

**Math functions.** The 5 `pow`/`exp` values matched on the Mac. That proves those 5 numbers, not the functions. The plan's rule of carrying the exact implementations V8 uses is the right one. Add: **the reference moves when Electron is upgraded** (V8 changed its `ieee754` functions before). The reference here was made with Chromium 158, while the app ships Chromium 156. Pin the Electron version used for references, record it in each golden file's metadata, and re-baseline only with a reason line (RL2).

### A6. Fused multiply-add is guarded on one target only (medium)
- `CMakeLists.txt:20` sets `-ffp-contract=off` on `alnative` only. `alengine` (`:32`) has no such flag, and future DSP code will be built into it.
- Apple clang on arm64 contracts within expressions by default. The **Linux x86-64 checks cannot see FMA at all**: baseline x86-64 has no FMA instruction, so "the same bits on Linux" says nothing about the M4.
- The FMA control build matched for the Crusher partly because its double state is rounded to float32 at the output, which hides most last-bit differences in double.
- **Guard (R6):**
  - `add_compile_options(-ffp-contract=off -fno-fast-math)` for the whole engine;
  - a CI grep that fails if the flag disappears;
  - bit tests that also compare a hash of the **double state** after N blocks, not only the float output.

### A7. Floating-point control state (medium)
- On arm64 macOS the FPCR flush-to-zero bit is off by default, which matches the web reference (RN1 1.3).
- But plug-ins run on the same IO thread, and RN2 notes that plug-ins change the float state and do not always restore it. One FabFilter call that leaves FZ on changes every AudioLab device computed after it on that thread.
- **Guard:** set the FPCR explicitly at the start of every AudioLab DSP segment, and save and restore it around every plug-in call (RN1 E3 covers only the "around the plug-in" half). Add a bit test with a denormal-producing input after a plug-in that sets FZ.

### A8. The audio path through the Electron main process (high)
- `desktop/native-engine.js:101-118` receives each block in the main process and writes it to the socket.
- The N2a proof ran in a bare Electron with nothing else to do. In the real app the main process also handles menus, every `ipcMain.handle` (AI voices, DAC volume, updates), window events and the updater's downloads and hashing.
- With `prefillMs: 30` (the bridge default), one 30 ms stall empties the ring. In exact mode the engine then waits for 30 ms of fill before playing again (`ring.h:62-64`), so a short stall costs at least 30 ms of silence.
- `feed()` returns the socket's back-pressure flag, and the caller ignores it (`native-engine.js:114`).
- **Fix (R3):** hand the `MessagePortMain` to an Electron **utilityProcess** that does nothing but feed the engine (Electron supports passing the port on), with:
  - a bounded queue that drops and counts when full;
  - a hang watchdog (a `status` ping every second; restart after 3 missed pings).
- Later, NR12's native add-on can carry the audio too.

### A9. Bit-perfect versus exclusive use in N2 (high, a decision)
See D1. The facts:
- the page needs a running device clock (N2a: 0.59 of real time without one);
- with exclusive use the page cannot use the DAC, so the DAC's clock and the page's clock differ, and only `follow` mode (resampling, A1, item 9) avoids gaps;
- the integer, non-mixable formats (`sample_convert.h`) also need exclusive use.

So in N2 you can have **either** bit-perfect float output in shared mode, **or** exclusive use with resampled output, not both. Both together arrive with N3, when the engine makes the sound on the DAC's own clock.

### A10. State ownership and the protocol (high)
- Today the page owns `PS` (the whole project). The engine holds only device settings, which the shell replays after a crash (`lastOpen`, `lastSound`).
- Your picks say "the engine keeps all state and the interface stays a view on it" (picks, U4f).
- N3 will have tracks that live in one engine or the other for 70 to 110 tasks. Without a defined owner and an edit protocol, every edit has to be mirrored by hand, and undo, autosave and crash recovery all break in new ways.
- The protocol as built:
  - matches answers to callers by command name (`engine-bridge.js:162`), so a `status` that timed out is answered later into the next `status`;
  - has no protocol version: `ready` says `alengine 0.2`, and nothing checks it;
  - answers a parse error with `"re":"?"`, which never matches, so the caller waits 15 s.
- **Guard (R4, R7):** request ids and a `protocol` number checked at `ready`, now. Before N3, a short design: the engine owns the document; the page sends edits as small, numbered operations with an inverse (undo); the engine sends snapshots and changes back; autosave is the engine's job.

### A11. The project file and versioning (medium)
- `formatVersion: 1` is written and never read (confirmed: the single occurrence in `index.html` is the writer). There is no `minReader`. RN3's RL1 covers this; I agree, and it must land before the first file with a plug-in in it is saved.
- The plug-in state blob `ALV3` (`vst3_format.cpp:227-251`) is a magic and two lengths, with no version byte and no class id or plug-in version inside. A future blob change cannot be told apart. Add a version and the class id, version and SDK, so that a "missing plug-in" placeholder keeps everything (RL1).
- The whole `.audiolab` file is one gzip with raw float audio, so it must be decompressed whole. RN1 NR13 covers the streaming side.
- The WAV header is 32-bit (`setUint32(4,36+data)` in the web writer; `common/wav.h` too). A stereo float export at 384 kHz passes 4 GB after about 23 minutes. Native export (N5) needs RF64.

### A12. Plug-in module lifetime (medium)
- `Vst3Format::create` makes a new `VST3::Hosting::Module` for every instance (`vst3_format.cpp:362`) and drops it in the destructor (`:114`).
- Two instances of one bundle therefore call `bundleEntry` twice. Closing the first calls `bundleExit` while the second still runs. Plug-ins built on the SDK's own entry code count these calls; others may not (to verify, R8).
- Each instance also re-reads the factory.
- **Guard (R8):** one module per bundle in a cache, reference-counted, and never unloaded during the session (RN2 point 6 says the same for Windows).

### A13. Gaps in the host layer (medium)
- `process()`:
  - returns `false` without touching `out` when `frames > maxBlock` (`:185`), so the caller plays whatever was in the buffer;
  - `prepare()` flips `active` (a plain `bool`) and reallocates `data` with no synchronisation against a running `process()`. The test app guards this with its mutex; the engine must stop the graph or swap instances instead.
- `outputParameterChanges` are cleared without being read (`:219`), so the plug-in's own changes (meters, read-only and output parameters) never reach the controller or the host.
- `restartComponent(kReloadComponent)` and `kIoChanged` are counted, not acted on; only latency is noted.
- `setParam` calls `controller->setParamNormalized` from whatever thread calls it. VST3 wants the UI thread (RN1 1.5).
- Not in the interface yet:
  - bypass (only `isBypass` on the parameter);
  - side-chain buses;
  - MIDI CC and pitch bend through `IMidiMapping` (RN3 C3: Serum's mod wheel will do nothing);
  - a "latency changed, reprepare" path.
- These fit NR5 and RL3. They are listed here so that NR5's scope is complete.

### A14. The scanner can hang the host (medium)
- `scanOutOfProcess` reads the pipe until EOF with no parent-side time limit (`scan.cpp:209`). The only limit is `alarm()` inside the child. Two ways this fails:
  - a plug-in that blocks or catches SIGALRM;
  - **any grandchild that inherits the pipe**: licensing helpers started by a plug-in at load. Then EOF never comes, and the scan of all 253 bundles stops at that bundle.
- After `fork()` in a multi-threaded parent (the test app is a Cocoa app), the child calls `std::to_string` and so allocates (`:203`). That is undefined after fork and can deadlock on the allocator's lock.
- **Guard (R8):**
  - `posix_spawn` with the strings built beforehand;
  - the child in its own process group;
  - the parent polls with a deadline and kills the whole group.

### A15. Delay compensation (low for now)
Latency is read once at `prepare` and on `takeLatencyChanged`. There is no compensation yet, which is correct for this stage. Your plug-ins report up to 2,875 samples (Pro-L 2). NR11's test with a settable-latency plug-in is the right proof. The point to add: latency must be re-read after **every** `setActive(true)`, because some plug-ins change it with the rate.

---

## 4. Detailed findings: code

### C1. Source switching: a race and a sleep (high)
`engine_main.cpp:265-273`. The `source` command does the following, in this order:
1. sets `E.source = 0`;
2. sleeps 30 ms, hoping the IOProc has left `render`;
3. calls `E.ring.init(...)`, which reallocates `buf` and resets `w` and `r`;
4. and only then calls `startSocket()`, which calls `stopSocket()`.

So the old socket thread can be inside `ring.write()` during step 3. ThreadSanitizer, in the harness `ring_tsan.cpp` described in section 0, reports races at `ring.h:33` and `:41` and in vector copying, and the program **hung**: the writer stored an old `w` over the reset one, so `fill()` wrapped.

The `file` branch swaps `E.file` (a vector) under the same sleep. A sleep is not synchronisation: an IOProc can be pre-empted for longer than 30 ms.

**Fix (R4):**
- stop the socket thread first;
- hand the audio thread a new source through one atomic pointer swap, freeing the old one later, off the audio thread (RN1 1.3);
- never call `init` on a ring that a live thread can see.

### C2. The follower's table is built on the audio thread (medium)
`SincTable::get()` is a function-local static (`follow.h:255`), first called inside `readFollow` (`ring.h:66`), on the IO thread. It allocates 4,097 × 48 floats (about 786 KB), computes about 200,000 Bessel series, and takes the static-initialisation guard (a lock). One glitch per engine start in follow mode. **Fix:** call `SincTable::get()` at program start.

### C3. The follower's frequency response (medium)
Measured here from the table itself. Worst of the fractions 0.125, 0.25, 0.5 and 0.75:

| Rate | 18 kHz | 19 kHz | 20 kHz | 21 kHz | 22 kHz |
|---|---|---|---|---|---|
| 44.1 kHz | -0.05 dB | -0.82 dB | **-4.23 dB** | -12.7 dB | -41.9 dB |
| 48 kHz | 0.00 | 0.00 | -0.18 | **-1.44** | -5.52 |
| 96 kHz | 0 | 0 | 0 | 0 | 0 |

- Row 0 (fraction 0) is set to the identity (`follow.h:253`) and is flat. Row 1, a fraction of 1/4096, already has the full roll-off. So the top octave's response jumps each time the read position slips one whole sample: about every 0.45 s at 50 ppm and 44.1 kHz.
- The comment "passes up to 0.92 of the top frequency" is not what the kernel does: with 48 taps and β = 11 the transition band is wide.
- The self test checks only 997 Hz and 15 kHz, where all is well.
- Likely inaudible to most listeners. Measurable, and against U4a's spirit.
- **Fix (R5):**
  - a longer kernel (96 to 128 taps) or a per-rate cutoff;
  - no identity row while following: keep bit-perfection by **bypassing** the interpolator only when `u == 0` exactly;
  - self-test points at 19, 20 and 21 kHz at 44.1 kHz.

### C4. The follower's steering (medium)
- `kp = 0.04`, `ki = 0.0004` gives a natural frequency of 0.02 rad/s: a 2 % settling time of about 5 minutes, not "about a minute" (`follow.h:259`).
- The engine's own self test agrees: the 1,000 ppm case is still at 1,019.5 ppm after 5 minutes, with the fill 856 frames (18 ms) under target after two minutes.
- The test uses a 50 ms target; the shell sends `prefillMs: 30`. The test feeds perfectly regular 128-frame blocks; the real feed comes in bursts after main-thread pauses (A8).
- Real crystals are usually well under 100 ppm, so the slowness is acceptable. The test must use the production settings and a bursty sender, and run for an hour (R5, R10).

### C5. Data races outside the ring (medium)
- `E.rate` is a plain `double`, written by the HAL listener thread (`:236`) and read by the IO thread in `render` (`:117`).
- `E.ring.steer.reset()` is called from the command thread (`:277`) while the IO thread uses `steer`.
- `E.dev` is read by the listener thread while `openDevice` writes it.
- These are formally undefined behaviour and practically mostly harmless. Make them atomics or move them through the command queue (R4). Add a TSan job on the macOS runner, since Apple clang has TSan.

### C6. Output safety (medium; high once anyone else uses it)
- Float path: the samples go to the device untouched (`coreaudio.cpp:254-256`). NaN, Inf and 1e30 reach Core Audio, which clips to full scale or worse.
- Integer path: NaN becomes 0 and Inf becomes full scale (tested here: `inf -> 8388607`).
- The test app halves and clamps (`main.mm:93-99`); the engine does not.
- The `volume` command sets the DAC's own analogue volume to any value from 0 to 1 (`engine_main.cpp:260`). It is reachable from the page (`native-engine.js` COMMANDS), and the page arrives through an update channel that is not signed (RN6 1.4).
- **Guard (R4):**
  - replace NaN and Inf with 0 and count them, in every path;
  - a "protect" clip at ±1.0, which is bit-transparent for every legal sample, so it costs nothing in bit-perfect terms;
  - hardware volume changes ramped, and anything above the level you last set yourself confirmed by you.

### C7. The integer path (medium)
- `OutputStream::start` reads `kAudioStreamPropertyVirtualFormat` once (`coreaudio.cpp:279-288`). There is no listener on the stream's virtual or physical format.
- If another program, Audio MIDI Setup or a re-plug changes the format while the engine runs, the IOProc keeps writing the old layout: wrong bytes to a DAC, which is loud noise.
- With exclusive use nobody else can change it, but without it they can.
- 16-bit output is dithered by default (`dither16 = true`). That breaks bit-perfect playback of 16-bit material, which is common (CD rips).
- **Fix (R4):** listen for format changes and restart the stream; dither off by default, and on only for sources with more than 16 bits.
- Remember that this path has never run with sound (build doc, N1).

### C8. The latency figure understates (low)
`statusJson` reports buffer + device latency + safety + stream latency. In N2 the real path adds the ring's prefill (30 ms) and Chromium's own output buffering on the page side. A settings page showing "1.25 ms" while the true figure is about 35 ms would be wrong. Label the figure as the device's part, and add the ring.

### C9. Possible stalls (low)
- `stopSocket()` joins a thread that may be blocked in `read()` on a client that keeps its connection open. Shutting down the listening socket does not wake it. The bridge closes its side first today, so this is latent. **Fix:** `shutdown()` the client socket too.
- `say()` holds a mutex and can block on a full stdout pipe. When the socket thread calls it on connect or disconnect, feeding stops until the shell reads.

### C10. Undefined behaviour on bad input (low)
- `(uint32_t)m.num("buffer")` and `(uint32_t)m.num("id")` with negative or huge values (UBSan confirmed).
- `minijson` turns `é` into `u00e9`: device names with accents survive one way only.
- `wav.h` reads the `fmt ` chunk without a bounds check.
- The engine trusts its stdin, so this is low. RN6 asks for a fuzzer on the protocol, and the harness used here is a start.

### C11. Bridge details (low)
- `"re":"?"` is never matched (A10).
- `stop()` sends SIGTERM after 1.5 s but never SIGKILL.
- The `restarts` window is fine.
- Hog mode on a dead engine should be released by the system when the process dies. Expected, not checked: case D on the macOS runner will show it.

### C12. The page tap allocates on the web engine's audio thread (low)
`page-tap.js:240` makes a new `Float32Array` for every 128-frame block (375 a second), and `postMessage` clones it. That is garbage on the very thread that renders the whole web mix, and GC pauses there become late blocks. The N2a run had no web mix to disturb. **Fix:** a small preallocated ring in the worklet, posting larger chunks (for example 4 quanta) or transferable buffers to a dedicated relay.

### C13. The preload trusts any message (low)
`preload.js:69-71` forwards the port of **any** `window.postMessage` that carries `alNativePort: true`, from any frame or origin. Check `e.source === window` and the origin.

### C14. The test app's audio thread (low; for the record)
- `try_lock` on a `std::mutex` (RN1 already flagged it).
- `G.in[...].assign()` can allocate on the IO thread (`main.mm:58`).
- Fine for a test app. These patterns must not move into the engine. RTSan in CI (RN1 NR2) is the guard.

### Checked and fine
- **Sample counters:** every counter is 64-bit (`Ring::w/r`, callbacks, frames), so no overflow in any realistic session. The ring's modulo arithmetic is right. `ProcessContext::samplePos` is `int64_t`.
- **The ring in normal use:** single-writer, single-reader with seq_cst atomics, clean under TSan; it keeps `HISTORY` frames behind the reader for the interpolator.
- **`floatToInt`** rounds, clamps and handles NaN as intended. 24-bit values round-trip (self test).
- **`setState` order** follows the VST3 rule: processor, `setComponentState`, then the controller state.

---

## 5. Decisions to revisit (each needs your decision; nothing was changed)

**D1. In stage N2: bit-perfect or exclusive use?** (picks U4a "bit-perfect output to the DAC", and the N2a/N2b design)
- Evidence: A9 and C3.
- Recommendation: N2's default is **shared mode on the DAC with `exact` clock**: bit-perfect in float, and no exclusive use. "Exclusive use" stays offered, labelled "resamples slightly until the native engine makes the sound (stage 3)". Integer and non-mixable formats wait for N3.
- The alternative is follow mode by default, after R5's filter fix.

**D2. One random stream per device, as a deliberate sound change in the web engine before the first port.** (plan section 4, "the same bits are possible")
- Evidence: A2.
- Recommendation: yes. Do it once, versioned (RL2), with the Fractals levels checked as usual. Without it, the bit promise holds for single devices only, and multicore (NR3) is ruled out for devices that draw random numbers.

**D3. The reference is a single-pass web render, made by the shipped Electron on macOS arm64.** (plan section 4: "the exports of the web engine are the reference"; NM1 made its references with headless Chromium 158 on Linux)
- Evidence: A3 and A5.
- Recommendation: yes. Pin the Electron version for reference renders, and keep the chunked export as an approximation with its measured distance from the single pass.

**D4. The block-size rule (RN1 point 5): a 128-frame grid in sample time.**
- Evidence: A4.
- Recommendation: neither of RN1's two options. A virtual quantum grid instead: bit-exact, no added latency.

**D5. CLAP before Audio Units (RN1 point 12, your pick P4).**
- Evidence: VST3 already reaches every maker on your U3 list, and all of them loaded. A second format adds little for you now. RN3's C9 gate says no second format until the VST3 corpus is solid.
- Recommendation: keep P4's order open. Let test app 0.5 also **list** the CLAP and Components folders (cheap), so the choice is made on your own plug-ins, after the VST3 gate.

**D6. Fractals v10 as the fresh-install song of the first native build (U5b).**
- Evidence: RN6 found the vocals are cut from a commercial recording, and v7 to v10 take riffs from the original's stems.
- Recommendation: do not tie the first native build to v10. Ship v6 without the original vocals, or a new song.

**D7. Windows read-only tasks and the ASIO agreement now (R5b).**
- Evidence: RN2 point 1. Replies take 5 weeks to 3 months, and it costs nothing.
- Recommendation: send the agreement now. This does not change R5b's order for the engine work.

**D8. Stage 4 "AppKit with Metal" (plan section 3).**
- Evidence: RN2 point 7 and RN4. Windows is wanted, and AppKit would mean a second interface.
- Recommendation: mark that line as superseded until question R2 is asked again. Nothing in stages 1 to 3 depends on it.

**D9. The macOS build machine.**
- Evidence: six of six `native-engine.yml` runs on 27 November got no machine. The hosted Apple Silicon queue is not something the plan can rely on.
- Recommendation, for you to decide because it costs money or uses your machine: a self-hosted runner on your Mac mini (free, only while it is on), or GitHub's larger macOS runners (paid).

---

## 6. Process

**The five process issues**
- **P1 (blocker).** No native check runs on a push, and the N2b code was never compiled on macOS: runs 1 to 6 of `native-engine.yml` were all cancelled or are still queued (checked through the GitHub API on 27 November).
- **P2 (high).** The proofs are short: 3 s (N1), 20 s (N2a), 5 simulated minutes (the follower). There is no soak, no real pair of clocks, no cable loop-back, and the integer path never ran with sound.
- **P3 (medium).** No sanitizer, RTSan or static-analysis job. My runs (section 0) found the C1 race, which a TSan job would have caught.
- **P4 (medium).** References come from headless Chromium 158 on Linux, while the app is Electron with Chromium 156 on arm64 (A5, D3). Nothing pins or records the version.
- **P5 (high).** The plan depends on the hosted macOS runner, which gave no machine for hours on 27 November (D9).

**Testing strategy.** The bit-test method (port statement by statement, render the real app's worklet, compare every sample) is the strongest part of the project. It is used once, on one device, at one block size, with float outputs. To carry 70 to 110 port tasks it needs:
- the grid rule (A4) and the random-stream rule (A2);
- block sizes 32, 37, 64, 128 and 512;
- a double-state hash (A6);
- a denormal case;
- runs on arm64 for every port. Linux x86 cannot see FMA.

RN6 section 3 lists the right tools. The gap is that **none of it runs automatically**.

**CI coverage today.**
| What | Linux | macOS | On push? |
|---|---|---|---|
| `alengine selftest` | no CI (runs by hand) | `native-engine.yml`, `native-lab.yml` | **no**, hand start only |
| Crusher bit test | no | `native-lab.yml` | no |
| VST3 host checks | no | `native-lab.yml` | no |
| Bridge cases A to D | not possible | `native-engine.yml`, **never ran** | no |
| Sanitizers, RTSan, static analysis | no | no | no |
| Windows | no | | |

**Proven on your Mac vs assumed.**
| Claim | Status |
|---|---|
| HAL output, rate switching, exclusive use, hot-plug, Gryphon and AMS-24 formats | **proven on the M4** (test app 0.2 to 0.4) |
| 32 frames clean with Serum 2, also with its window open | **proven on the M4** (worst block 32.6 % of the deadline) |
| VST3 load, state, windows, latency figures for your plug-ins | **proven on the M4** (57 loads, no failure) |
| Crusher bit-identical | proven on a virtual M1 and on Linux; not on the M4 |
| Engine hand-over bit for bit | proven on a virtual M1 with BlackHole, 3 s |
| Page to shell to engine path | proven in a bare Electron on a virtual M1, 20 s |
| Clock follower | proven in simulation only (Linux) |
| N2b bridge (crash recovery, preload, page tap) | **not compiled or run on macOS** |
| Integer output path | arithmetic only; **never ran with sound** |
| `alengine` hot-plug handling | not run on hardware |
| Drift between the page's clock and the Gryphon | not measured |
| Real round-trip latency | not measured (calculated 1.25 ms) |
| Hog mode released after an engine crash | assumed |
| App Nap does not slow `alengine` | assumed (RN1 1.7) |

**How a regression would be caught today:** by you, by ear, after a release, or by the next hand-started run if a runner comes. That is the gap that R1 closes.

**Release and rollback.**
- The test apps are pre-releases not marked as latest, so the desktop updater cannot pick them. Good.
- For `alengine` in the desktop build (N2c), four rules:
  1. the shell checks the engine's protocol version at `ready` and falls back to the web engine on a mismatch;
  2. the native output is a setting, with the web engine as the fallback, until stage 3 ends (RL6);
  3. `index.html` updates arrive separately from the app binary, so a newer page must cope with an older engine, and the reverse;
  4. the program update must be signed before the page can drive hardware (RN6 1.4).

---

## 7. What is already good (earned)

- **The route and its order.** Route C then B, the HAL rather than AVAudioEngine, VST3 on the MIT SDK, and plug-ins in the engine with "run apart" later all match the evidence, and the research documents back each choice with sources.
- **Measuring instead of assuming.**
  - Test B measures whether plug-ins are deterministic, and found Surge XT is not.
  - The NM1 reference generation caught its own mistake: the worklet had not loaded yet, so the first reference equalled the input.
  - N2a found that a page without a device clock runs at 0.59 of real time.
- **The test app on your Mac from day one.** It already found a real fault: the stale rate after a re-plug, fixed in 0.3.
- **Honest documents.** Every stage has a "not proven" list, and they are accurate: I found nothing claimed as proven that was not. The one overstatement is the follower's "passes up to 0.92" and "settles in about a minute" (C3, C4).
- **The shapes are sound.**
  - The ring is single-writer, single-reader, lock-free, with 64-bit counters.
  - Exact mode is the default.
  - The engine ends when its stdin closes, so it cannot be orphaned holding exclusive use.
  - The sound socket sits in the per-user temporary folder.
  - Crash recovery is capped at 3 a minute, then falls back to the web engine.
  - Scanning runs in a child process, and Intel-only bundles are told apart from crashes.
- **`plugin_api.h` really is format-neutral.** No VST3 type leaks through it. Bypass, side-chain, MIDI mapping and a reprepare path still need adding (A13).
- **The project file stores decoded audio as float.** That removes a whole class of decoder differences between the engines.

---

## 8. Fix tasks for NB to fold in

Sized like this project's tasks (one cloud task of 1 to 3 hours). In order. R1 to R5 come before N2c, and R6 and R7 before the first N3 port.

| Task | What | Proof | Size |
|---|---|---|---|
| **NB-R1** | CI on every push for `native/`, `desktop/native-engine.js` and `native/bridge/` (Linux): build, `alengine selftest` under ASan/UBSan, the ring stress under TSan, Node syntax and unit tests of the bridge. Dispatch `native-engine.yml` and fix whatever the first macOS compile of N2b shows. Ask for D9. | green checks; cases A to D read | 1 |
| **NB-R2** | The rate contract (A1): `pageRate` in `source`, refusal on a mismatch, the page's context created at the device rate, the rate event renegotiates; a status field. | runner: page at 48 kHz, engine at 96 kHz, refused; renegotiated without a click; 16 kHz default output case | 1 to 2 |
| **NB-R3** | Sound path out of the main process (A8): a utilityProcess feeder, a bounded queue, a back-pressure count, a hang watchdog. | case A again with the main process artificially blocked for 50 ms every second: no gap | 1 |
| **NB-R4** | Engine hardening: source switch by atomic swap (C1); `SincTable` built at start (C2); atomics for shared fields (C5); NaN/Inf scrub and a protect clip (C6); volume ramp and cap; format listener and dither off by default (C7); request ids, a protocol version, the parse-error answer (A10, C11); client `shutdown()` (C9); checked integer conversions (C10). | TSan clean on macOS; injected NaN counted; format change restarts cleanly | 2 |
| **NB-R5** | Follower quality (C3, C4): kernel and cutoff per rate, bypass at speed 1, test points at 19 to 21 kHz, production targets, a bursty sender in the simulation. | response table in the self test; 20 kHz at 44.1 kHz within 0.5 dB | 1 |
| **NB-R6** | N3 ground rules, written and tested before the first port: the quantum grid (A4), per-device random streams (A2, after D2), global FP flags and a CI check (A6), the FPCR policy (A7), the reference rule (D3), and the per-family bit/tolerance table (A5). | the Crusher at block sizes 32/37/64/128/512, bit-identical; a two-Crusher song bit-identical after D2; a denormal case after an FZ-setting plug-in | 2 (+1 `index.html` task in its turn for D2) |
| **NB-R7** | State and edit protocol design (A10): owner, numbered edits with inverses, snapshots, autosave in the engine, how a half-native song is kept in step. | a document plus a prototype test: 1,000 random edits and undos give the same state in page and engine | 1 |
| **NB-R8** | Host hardening, with NR5/RL3: a module cache (A12); `prepare` only when the plug-in is out of the graph; output cleared on failure; `outputParameterChanges` forwarded; reload and IO changes queued to the main thread; `IMidiMapping`; FPCR save and restore; the scanner on `posix_spawn` with a process group and a parent deadline (A13, A14). | Steinberg's validator in CI; two instances of one bundle, close the first; a scanner test plug-in that forks a sleeper | 2 |
| **NB-R9** | File safety, with RL1/RL4: `minReader` read; ALV3 v2 with version, class id and plug-in version; RF64 for long exports. | a v2 file in today's loader says so; a placeholder round-trips its bytes; a 5 GB export reads back | 1 to 2 |
| **NB-R10** | Long runs, with RL12: 1 hour on the runner per engine change (drift corrections, gaps, memory, threads), and a weekly 8-hour run; a "leave it playing overnight" mode in the test app; NR-LAT on the AMS-24 with a cable. | soak report in `docs/native-lab/`; your overnight report | 1 |
| **NB-R11** | Chromium check for A5: the summation order in `AudioNodeInput`, `vector_math` on NEON, the panner and automation maths, the FFT on macOS. A per-family table of "bits" or "tolerance" with numbers. | a table in `native-mac-build.md` | 1 (research) |

Together: 14 to 17 tasks. Most of them are pieces RN1, RN3 and RN6 already proposed, given a firm place in the order. The new ones are R2, R3, R5, R6 (its A2, A3 and A4 parts), R7 and R11.
