# How native Mac DAWs work, and what AudioLab's native engine should take from them (task RN1)

Research only. No code changed: `index.html`, `desktop/` and `native/` were not touched. This document is for task NB and for the scheduling chat. Written 27 November 2026.

Read with: `docs/native-mac-plan.md` (the route), `docs/native-mac-picks.md` (your picks and the reports from your M4), `docs/native-mac-build.md` (what NB has built: `alengine`, the bridge, test app 0.4).

How to read the sources: each finding names where it comes from. **Apple** and **Steinberg** pages are the makers of the system and the format. **Forum** means a developer's report, true for them, not a promise. **Guess** or **from knowledge** means not checked against a source in this task; each such line says so.

---

## 0. The summary

**The three biggest findings**

1. **On Apple Silicon, every real-time thread the engine makes must join the audio device's workgroup, or the Mac may run it on a slow core at a low clock and it will miss the deadline even when the load is low.** This is Apple's own mechanism (Audio Workgroups, macOS 11). Plug-in makers saw "random dropouts, especially under low CPU load" on Apple Silicon until they joined it (Blue Cat Audio). Today's engine has one thread (the device's own), so it is safe; the moment NB adds worker threads for many tracks, this becomes the rule that decides whether 32 frames still work. Ableton says Live runs audio only on performance cores.
2. **Every serious DAW runs two paths at once: what you play live at the device's small buffer, and everything else computed ahead in a much larger buffer on all cores.** Cubase calls it ASIO-Guard (23 to 280 ms ahead), Logic "live" and "playback" tracks, REAPER "anticipative FX". It is the single biggest lever for "many plug-ins at 32 frames". AudioLab's engine should be designed for it from N3, not added later.
3. **Plug-in stability is mostly about obeying threading rules, not about sandboxes.** VST3 says state, edits and restarts happen on the main thread and the audio thread never waits for anything. Separate processes per plug-in (Bitwig) cost a few microseconds to tens of microseconds per plug-in per block (Ardour's estimate), which is too much for every plug-in at 32 frames but fine for a few risky ones. The plan already has the right order (in the engine first, "run apart" per plug-in later). One concrete fix now: the test app's audio thread uses `std::mutex::try_lock`, which experts show is not safe on the audio thread (its unlock can make a system call); the engine must not copy that.

**What else matters, in one line each**

- Turn off "flush denormals to zero" for AudioLab's own devices (the web reference keeps denormals, so the bits would change) but turn it **on around plug-in calls**, as hosts do.
- Use Clang's RealtimeSanitizer on CI: it stops the test the moment anything on the audio thread allocates memory or takes a lock. That turns "real-time safe" from a promise into a check.
- Meters, playhead and waveforms must reach the screen through shared memory that the screen reads at its own rate (240 times a second), never as messages from the audio thread. This holds for Electron now and for Metal later.
- For 240 Hz native screens: `CVDisplayLink` is deprecated; use the display link from `NSView`/`NSScreen` (a `CADisplayLink`, macOS 14) or `CAMetalDisplayLink` for Metal, and always draw for the frame's target time.
- Scan once, cache, load the project first and the plug-ins after (Bitwig's "projects load immediately, plug-ins follow"). Your Pigments loads in 4 s and Neutron modules in 1.1 s each, so this is felt.
- Keep App Nap off while the engine runs (one call), watch the Mac's thermal state and shed drawing before audio.
- ARA (for Melodyne) is now an open SDK under Apache 2.0: no licence obstacle, only work.
- CLAP has a host thread pool: the host, not the plug-in, owns the real-time threads, which is exactly what point 1 needs. A reason to move CLAP up the list.

**Proposed new tasks:** 16, in section 3, each one cloud task of 1 to 3 hours with a proof on the macOS runner and a check on your Mac. **What NB should change:** 12 points in section 4.

---

## 1. Findings by area

### 1.1 The real-time audio thread on macOS

**Which level of Core Audio.**
- There are three levels a program can open a device through: the HAL (an IOProc on the device, the lowest public level), the AUHAL output unit on top of it, and AVAudioEngine on top of that. AVAudioEngine cannot take exclusive use of a device or choose its real format (already in the plan, section 2, [AVAudioEngine](https://developer.apple.com/documentation/avfaudio/avaudioengine)). NB's choice of the HAL is the right one for your priorities (bit-perfect, exclusive use, exact rate). The test app and `alengine` already do this.
- The cost of the HAL: the program does what AUHAL would do for it, including format conversion (NB does it in `sample_convert.h`) and following device changes (NB does it). Nothing in the research suggests changing this.

**The deadline.** The IOProc is called once per buffer and must return before the device needs the next one. At 32 frames and 48 kHz that is 0.67 ms. Your M4 ran Serum 2 there with a worst block of 20.8 % of the time, 32.6 % with Serum's window drawing (`docs/native-mac-picks.md`). The worst block, not the average, decides clicks. Ross Bencina's rule: "If you don't know how long it will take, don't do it" ([Bencina, Real-time audio programming 101](https://hn.jakechampion.name/reader/http://www.rossbencina.com/code/real-time-audio-programming-101-time-waits-for-nothing)).

**Device latency and the safety offset.** The HAL reports a device latency and a safety offset per direction; the way out is buffer + latency + safety. On your Gryphon at 48 kHz: 14 + 14 frames, so 32 + 28 = 60 frames, 1.25 ms (calculated in the picks doc, not measured). A loop-back cable measurement is still the only true figure (task NR-LAT in section 3).

**`kAudioDevicePropertyIOCycleUsage`.** A client can tell the HAL that it needs less than the whole cycle, so the HAL calls it later and the latency drops by that much. The default is the whole cycle ([Apple forum 651617](https://developer.apple.com/forums/thread/651617)). The header documentation is the reference; it was not read here. Worth a measurement only after the engine is stable; the gain is a fraction of a buffer and the risk is overloads. Low priority.

### 1.2 Audio Workgroups, P-cores and E-cores

What Apple says:
- An audio workgroup is "a collection of real-time threads that work together to produce audio by a common deadline while spanning multiple processes, including the audio server and client apps and plug-ins". The system uses it to "balance the competing interests of power consumption and performance" ([Apple: Understanding audio workgroups](https://developer.apple.com/documentation/audiotoolbox/understanding-audio-workgroups)).
- The device's IO thread (the thread that runs the IOProc) is in the device's workgroup automatically. "Your app or plug-in requires no additional work if the only real-time thread it uses is the one that the audio frameworks provide" (same page). That is today's `alengine`.
- Extra real-time threads must join: get the workgroup from the device (`kAudioDevicePropertyIOThreadOSWorkgroup` on the HAL, or from the output unit), call `os_workgroup_join` once in each thread, `os_workgroup_leave` before it ends. `os_workgroup_max_parallel_threads` says how many to make ([Apple: Adding parallel real-time threads](https://developer.apple.com/documentation/audiotoolbox/adding-parallel-real-time-threads-to-audio-workgroups), [Apple: Workgroup management](https://developer.apple.com/documentation/audiotoolbox/workgroup-management), [WWDC20 session 10224](https://developer.apple.com/videos/play/wwdc2020/10224/)).
- Threads that run on their own clock (a disk thread, a render-ahead thread) get their own "interval" workgroup (`AudioWorkIntervalCreate`) and call `os_workgroup_interval_start` and `_finish` around each cycle (WWDC20 10224).
- Apple's advice on making your own real-time threads: "the answer is probably no", and "measure everything" (WWDC20 10224). In other words: join, do not invent.

What developers found:
- **A thread must already be a real-time (time-constraint) thread before it can join**, or the join fails with `EINVAL`. Apple's support told one developer so; it is not in the documentation ([JUCE forum 54240](https://forum.juce.com/t/os-workgroup-join-consistently-returns-einval-cant-join-audio-workgroup/54240)). The values given do not matter much once joined: Blue Cat says "any random value will be fine" ([Blue Cat, 2023](https://www.bluecataudio.com/Blog/preview/realtime-audio-multicore-issues-for-apple-silicon-end-of-the-story/)); one developer set period, computation and constraint all to the buffer's length and reported a large gain (forum 54240, one person's report). An Adobe developer joined only while the IO thread was running ([coreaudio-api, June 2021](https://lists.apple.com/archives/coreaudio-api/2021/Jun/msg00004.html)).
- **Workgroups are reference counted** (retain and release), and the join token must live on the thread that joined (Blue Cat; forum 54240).
- **Without joining, worker threads land on E-cores.** A developer saw his time-constrained worker threads run on P-cores at 256 frames or less and on E-cores at 512 or more (seen in Instruments' System Trace) ([Apple forum 726096](https://developer.apple.com/forums/thread/726096)). Blue Cat's multicore plug-ins had "random audio dropouts ... especially when working under low CPU load" on Apple Silicon since about macOS Ventura; Intel was not affected; "some major DAWs have been impacted too". Cause: the cores are not alike, and the scheduler did not know the threads shared a deadline (Blue Cat, 2023).
- **macOS has no core affinity API.** A program cannot pin a thread to a P-core; the workgroup is the only way to tell the system ([Apple forum 651617](https://developer.apple.com/forums/thread/651617), [JUCE forum 52188](https://forum.juce.com/t/mac-m1-thread-priority-audio-workgroups/52188?page=2)).
- **Plug-ins cannot reach the host's workgroup through VST3.** Audio Units get it (render context observer); VST3 and CLAP have no public way, so Blue Cat now reads it from a private thread-local key of Apple's own code and asks Apple for a public API ([Blue Cat, October 2025](https://www.bluecataudio.com/Blog/?p=8798)). What this means for AudioLab: when the engine calls a plug-in from a thread that has joined the workgroup, that plug-in's own work is scheduled right. A plug-in that makes its own threads (some large synths do) is on its own. CLAP's thread pool solves this (1.6).
- **E-cores and P-cores on paper.** On the M1 family, E-cores reach about 2 GHz and have about half the units of a P-core; P-cores reach about 3.2 GHz; threads with the lowest QoS run only on E-cores ([Eclectic Light, 2022](https://eclecticlight.co/2022/04/25/how-macos-manages-m1-cpu-cores/)). Your M4 Mac mini has 4 P-cores and 6 E-cores (from knowledge, not checked here). So the useful audio budget is about 4 fast cores; using all 10 for audio would add slow cores to the critical path.
- **Ableton:** Live "supports up to 64 cores"; on hybrid CPUs audio runs "exclusively on Performance cores, if available" ([Ableton: Multi-core FAQ](https://help.ableton.com/hc/en-us/articles/209067649)). A KVR thread says Bitwig on M4 uses 4 of 10 cores and that Bitwig support confirmed it; the thread could not be loaded, so this is a pointer, not a finding.

**For AudioLab:** worker threads = at most `os_workgroup_max_parallel_threads` minus one (the IO thread works too), made real-time, joined to the device's workgroup, rejoined when the device changes. The render-ahead path (1.4) gets its own interval workgroup. Everything else (disk, scan, UI) stays at normal QoS.

### 1.3 Rules for the audio thread: memory, locks, page faults, denormals

**What never happens on the audio thread** ([Bencina](https://hn.jakechampion.name/reader/http://www.rossbencina.com/code/real-time-audio-programming-101-time-waits-for-nothing), [LMMS realtime conventions](https://github.com/LMMS/lmms/wiki/Realtime-Conventions), [Timur Doumler](https://hn.jakechampion.name/reader/https://timur.audio/using-locks-in-real-time-audio-processing-safely)):
- No `malloc`, `free`, `new`, `delete`; no `std::vector::push_back` that may grow; no `std::string` that may grow; no `std::function` that may allocate.
- No mutex, condition variable, semaphore wait, `sleep`, file or socket I/O, `printf`, logging.
- No Objective-C or Core Foundation calls: Apple's Jeff Moore, quoted by Bencina, "You also cannot be making calls to any ObjC or CF objects from inside your IOProc."
- `mach_absolute_time()` is the one call Bencina names as acceptable on the Mac (and he is "not 100 % confident").

**Locks.** The reason is priority inversion: the audio thread waits for a lower thread that holds the lock. Timur Doumler shows that even `std::mutex::try_lock` is not safe on the audio thread, because the unlock can make a system call when another thread waits: "you should not use std::mutex on the audio thread, not even with try_lock" ([timur.audio](https://hn.jakechampion.name/reader/https://timur.audio/using-locks-in-real-time-audio-processing-safely)). **The test app does exactly this** (`native/testapp/main.mm` line 28: "the audio thread only tries it"). Fine for a test app; the engine must use one of these instead:
- a single value: `std::atomic` (parameters, flags, meters);
- a stream (notes, parameter changes, commands): a single-producer single-consumer lock-free queue of fixed size;
- a structure that changes rarely (the graph, a plug-in list): build a new copy off the audio thread, swap one atomic pointer, and free the old one later on another thread (deferred deletion). Timur calls immutable copies "thread-safe by design"; LMMS warns to swap everything that belongs together in one pointer, or the audio thread sees a new buffer with an old setting;
- when a lock cannot be avoided: Timur's spin lock where only the other thread waits, and the audio thread only tries once.

**Page faults.** Memory the audio thread touches for the first time, or that the system paged out, costs a fault of unknown length. Core Audio list advice over the years: lock the memory (`mlock`), or touch it before use ([coreaudio-api 2018](https://lists.apple.com/archives/coreaudio-api/2018/Feb/msg00051.html), [2003](https://lists.apple.com/archives/coreaudio-api/2003/Oct/msg00107.html)). Practical rule: allocate and touch every buffer when a graph is built, before it is swapped in; pre-fault the stacks of worker threads. This is why Surge XT's first block took 4.4 ms on the build machine (plan, test B): plug-ins must be **warmed up off the audio thread** (one or two silent blocks in a non-real-time call) before they join the graph.

**Denormals.** Very small floating-point numbers can be many times slower; one measurement cited on KVR is about 3 times the CPU for silence on an Intel Nehalem; a Rust crate claims 50 to 100 times per operation (unverified) ([KVR](https://www.kvraudio.com/forum/viewtopic.php?p=8314064), [truce-core](https://docs.rs/truce-core/0.48.7/src/truce_core/denormal.rs.html)). On Apple Silicon, flush-to-zero is bit 24 of the FPCR register; JUCE's `ScopedNoDenormals` sets it and restores it (KVR). Whether Apple Silicon's cores are slowed by denormals at all is disputed in the thread and not settled here.

**The catch for AudioLab: the web reference keeps denormals.** The current web-platform test for AudioWorklet asserts that "denormals should be non-zeros in AudioWorkletGlobalScope" ([WPT test](https://kdab.searchfox.org/firefox-main/source/testing/web-platform/tests/webaudio/the-audio-api/the-audioworklet-interface/audioworklet-denormals.https.window.js)). In 2017 a Chrome engineer said Chrome ran the audio graph with flush-to-zero on ([W3C list](https://lists.w3.org/Archives/Public/public-audio/2017JulSep/0008.html)); the browser's own nodes may still do so. So: AudioLab's ported worklet devices must run **without** flush-to-zero, or the bits can differ from the reference (the worklet bundle already zeroes tiny state values every 16 blocks, plan section 4, which is why this is cheap). Browser-node devices: check per device when it is ported. **Plug-ins: set flush-to-zero around each plug-in call and restore it after**, as JUCE hosts do. This is a rule to write into N3.

**A tool that checks all of this.** Clang's RealtimeSanitizer: build with `-fsanitize=realtime`, mark the audio-thread functions `[[clang::nonblocking]]`, and any `malloc`, `free`, `pthread_mutex_lock` "or anything else known to have a non-deterministic execution time" inside them stops the program with a stack trace ([Clang: RealtimeSanitizer](https://clang.llvm.org/docs/RealtimeSanitizer.html)). The page's own examples are macOS output. Apple's Xcode clang may not have it; upstream LLVM from Homebrew on the runner does (from knowledge; to be checked in task NR2). This is the strongest single proof a cloud task can give for "the audio thread is real-time safe".

### 1.4 Using many cores: how the big DAWs do it

| DAW | What it does | Source |
|---|---|---|
| Ableton Live | Splits the signal graph into independent segments; one thread per segment; summing points are "wait points"; the **critical path**, not total CPU, limits how much fits. The CPU meter "measures how close Live is to missing its audio deadline". Parallelising one chain "comes at the cost of increased latency and decreased responsiveness", so Live does not. | [Ableton FAQ](https://help.ableton.com/hc/en-us/articles/209067649) |
| Cubase, Nuendo | **ASIO-Guard**: tracks that are not monitored or record-armed are computed ahead in a larger buffer into a queue; record-armed instrument and monitored tracks switch to the real-time path at once. Cubase 16 levels: 23, 35 (standard), 93, 140, 280 ms of pre-processing. Some plug-ins can be excluded. | [Steinberg: ASIO-Guard](https://www.steinberg.help/r/details-on-asio-guard-in-cubase-and-nuendo), [Steinberg help center](https://helpcenter.steinberg.de/hc/en-us/articles/206103564) |
| Logic Pro | "Playback tracks" are computed ahead ("process buffer range", Apple says set it to Large); the selected instrument track is "live" at the device buffer. With "Playback & Live Tracks", "each live channel strip can be processed by a different core". Apple's overload advice: do not select an instrument track during playback (it becomes live). | [Apple: Multithreading](https://support.apple.com/HT205975), [Apple: avoid overloads](https://support.apple.com/en-us/HT203930) |
| REAPER | "Anticipative FX processing ... runs at irregular intervals, often out of order, and slightly ahead of time"; over 95 % use of all cores on 8+ core machines (2011 article). Input monitoring falls back to synchronous processing. The Cockos wiki page on buffering could not be loaded. | [Sound On Sound, 2011](https://www.soundonsound.com/techniques/running-multiple-plug-ins) |
| Bitwig | Application, engine and plug-ins apart; the engine can be reloaded after a crash; "projects will load immediately, with plug-ins following after"; device code compiled in parallel and cached since 5.3. No published engine detail. | [Bitwig: Modern foundations](https://www.bitwig.com/modern-foundations/) |
| A 2026 open-source DAW | Graph as a DAG, run with a parallel form of Kahn's algorithm (count inputs, run every node whose inputs are done); a custom pool where the audio thread works too; workers spin briefly then sleep. 84 nodes at 512 frames: single-threaded missed 25 deadlines in 38,000, multi-threaded none. "The difficulty ... is not parallelizing work, but ensuring the scheduler itself has bounded latency." | [edwloef, March 2026](https://hn.jakechampion.name/reader/https://edwloef.github.io/posts/real-time-safe-multi-threaded-daw-audio) |
| Tracktion Engine | Its graph rewrite ("tracktion_graph") was presented at ADC 2020; the talk was not read here. | [JUCE forum](https://forum.juce.com/t/adc-tracktion-graph-talk/43052) |

What follows for AudioLab:
- **Two paths.** The "live" set = the track you play (selected instrument or record-armed), everything it feeds, and the master after it. Everything else runs ahead by a chosen amount (start at about 23 to 35 ms, as Cubase's lower levels) on worker threads, into a ring the live path reads. This gives the low latency for what you play and lets 4 P-cores carry the rest without the 0.67 ms deadline.
- **Same bits either way.** A track computed ahead and a track computed live must give identical samples. The engine's arithmetic is block-size independent only if every device is written for it (AudioLab's worklets use 128-frame blocks; plan section 4). So the render-ahead path should also use 128-frame internal blocks, and the live path processes 128-frame blocks too, with a small adapter when the device runs 32 or 64 frames. **This is a design decision for N3** (section 4, point 5): either the whole engine runs in 128-frame sub-blocks with a ring at the device (adds up to 128 frames, 2.7 ms, on the live path), or every ported device is proven block-size independent. The latter is the better product and is testable bit for bit.
- **Parallel graph inside a block.** Schedule by inputs done (Kahn), let the IO thread work, keep workers joined (1.2), measure the critical path and show it (Ableton's meter).
- **Automation, tempo changes and transport jumps** invalidate what was computed ahead. The render-ahead path must be able to drop its queue and refill within one ahead period. Cubase advises turning ASIO-Guard down for automation recording for this reason.

### 1.5 Plug-in hosting stability

**VST3 threading rules (Steinberg).**
- Plug-in functions are called by the host on the main (UI) thread, except `IAudioProcessor::process` and `setProcessing`, which may be on the audio thread. Configuration (`setupProcessing`, bus layouts) only while inactive. `setProcessing(true)` must reset the plug-in's state ([VST3 API documentation](https://steinbergmedia.github.io/vst3_dev_portal/pages/Technical+Documentation/API+Documentation/Index.html)).
- `beginEdit`, `performEdit`, `endEdit` come from the plug-in on the UI thread, in that order (same page). Test app 0.4 already counts them.
- `getState`/`setState` are "called normally from the UI Thread" in real time; in offline rendering they "could be called in the same thread than the process call" (Steinberg, [forum 201734](https://forums.steinberg.net/t/is-icomponent-getstate-setstate-thread-safe/201734)). Bitwig crashed a plug-in by calling `getState` while a program change ran on the audio thread (same thread).
- Restoring: processor state first, then `setComponentState` on the controller, then re-read parameters (VST3 docs).
- When a plug-in calls `restartComponent(kReloadComponent)`: fade out, `setProcessing(false)`, `setActive(false)`, `setActive(true)`, `setProcessing(true)` (Steinberg's Arne Scheffler, [forum 201851](https://forums.steinberg.net/t/what-is-the-correct-call-sequence-between-plugin-and-host-when-parameters-have-changed-while-it-is-processing-audio/201851)). And: "normally a plug-in is only allowed to call IComponentHandler::restartComponent from the UI thread. But we already saw plug-ins doing it whenever they want." So the host must accept these calls on any thread and hand them to the main thread through a queue.
- **Preset recall storms:** some plug-ins call `performEdit` for every parameter after a preset change; Live reacts to each "synchronously" and lags. Ableton's page asks plug-ins to change; a host can also defend itself by batching edits per UI frame ([Ableton: VST3 preset recall lag](https://ableton.github.io/plugins/vst3-preset-recall-lag)). Your Pigments has 4,365 parameters, Abyss 3,158, Kick 3 3,087: this will happen.
- JUCE's host takes a message-thread lock around state calls; in offline rendering from a background thread this deadlocked a plug-in ([JUCE forum 59348](https://forum.juce.com/t/hosted-vst3-threading-issue/59348)). Lesson: export should call state functions only from the main thread, or not at all during a render.
- **Steinberg's SDK ships a validator** that runs a plug-in through these rules (from knowledge: `validator` in the VST3 SDK's hosting samples; check in task NR5). Running it on the test plug-ins in CI, and the host's own sequence checks, is how to prove the host side.

**Process isolation: what it costs and who does it.**
- **Bitwig** offers five modes: within the engine, all together (the default), by maker, by plug-in, individually; a crashed plug-in shows Reload in its device panel ([Bitwig user guide](https://bitwig.com/userguide/latest/vst_plug-in_handling_and_options), [Bitwig crash protection](https://www.bitwig.com/en/19/plugin-hosting-video.html)). Memory cost is stated only as "most memory-intensive" for individual.
- **Ardour** refuses it and gives the arithmetic: two context switches per plug-in per block, about 3 µs fixed and 10 to 300 µs in real use (30 µs assumed); for 384 plug-ins that is 7.7 to 23 ms of switching per block, against 1.3 ms at 64 frames. "May work for 4 track Bitwig session with 12 plugins" ([Ardour](https://ardour.org/plugins-in-process.html)). These are Ardour's estimates, not measurements.
- **Apple** loads Audio Units out of process on Apple Silicon "that depends on the architecture or host preference" (processes `AUHostingServiceXPC` and `_arrow` for Rosetta); an Intel-only AU in an Apple Silicon host can only run that way ([Apple: out-of-process AUs](https://developer.apple.com/documentation/audiotoolbox/debugging-out-of-process-audio-units-on-apple-silicon)). A developer hosting Intel AUs this way got render time-outs and "instance invalidated" errors that did not happen when the host ran under Rosetta ([Apple forum 805894](https://developer.apple.com/forums/thread/805894)). Whether Logic ever loads AUv3 in process could not be confirmed ([forum 766503](https://developer.apple.com/forums/thread/766503), no answer read).

**For AudioLab:** the plan's choice stands (engine apart from the interface; plug-ins in the engine; "run apart" per plug-in later). Add: (a) the engine already being a separate program means a plug-in crash costs the sound for a moment, not the project, **if** the app restarts the engine and reloads the project state automatically; this is cheap and worth more than sandboxing; (b) a crash or hang is recorded against that plug-in, and next time it is offered "run apart" or blocked; (c) the "run apart" helper uses shared memory and a Mach semaphore or `os_sync` wake per block, and its real cost is measured on your M4 before it is offered (task NR9).

**ARA.** Melodyne's full mode needs ARA. The ARA SDK has been open source under Apache 2.0 since May 2021; ARA 2 is in Logic, Cubase, Studio One, REAPER, Pro Tools and others; Bitwig and Live are not on Celemony's list ([ARA SDK](https://github.com/Celemony/ARA_SDK), [Celemony: 10 years of ARA](https://www.celemony.com/en/10-years-of-ara), [Wikipedia: ARA](https://en.wikipedia.org/wiki/Audio_Random_Access)). The host gives the plug-in random access to the audio of a clip and its tempo and key, outside real time. No licence cost; it needs audio clips in the native engine first.

**Scanning and the cache.** Already in place: one child per bundle, Intel-only detected. Your scan of 253 bundles had Kontakt at 1.5 s and most at 0.01 to 0.15 s. Hosts keep a cache keyed by path, size and modification time so a restart scans only what changed (Bitwig, REAPER and Live all behave this way; from knowledge). Under the hardened runtime later, the **scanner child also needs** the "disable library validation" entitlement, and must not be signed with `--options runtime,library`, or every plug-in looks like a crash with no message ([JUCE forum 48425](https://forum.juce.com/t/child-process-hardened-runtime-issue/48425)).

### 1.6 CLAP and its host thread pool

CLAP lets "the host manage a small number of real-time threads for all plug-ins"; the host knows each track's deadline and can run first what must finish first; the CLAP site claims up to twice as many instances before dropouts and at least 20 to 25 % in other cases (vendor claim) ([CLAP: thread pool](https://cleveraudio.org/1-feature-overview/_thread-pool/)). The header's exact rules for the call could not be read here (the mirror was blocked); from knowledge: the plug-in calls the host's `request_exec(task_count)` from inside `process`, the host runs the plug-in's `exec(task_index)` on its pool and returns when all are done. With AudioLab's pool joined to the workgroup (1.2), CLAP plug-ins get correct scheduling on Apple Silicon for free, which VST3 cannot give. Surge XT, u-he and others ship CLAP. **Suggestion: CLAP before Audio Units in the order** (plan P4 says AU, CLAP, VST2); CLAP is also the smallest of the formats (6 to 10 tasks in the plan). This changes your pick P4, so it is a question for you, not a change made here.

### 1.7 Power and thermals

- **App Nap.** macOS may slow down an app it thinks is idle. An app doing "lengthy user-initiated work" should call `beginActivityWithOptions:` with `NSActivityUserInitiated` or `...AllowingIdleSystemSleep` ([Apple: prioritize work](https://developer.apple.com/library/archive/documentation/Performance/Conceptual/power_efficiency_guidelines_osx/PrioritizeWorkAtTheAppLevel.html)). The Zed editor's audio was "temporarily scrambled" during heavy I/O until it held such an activity for as long as audio plays ([Zed commit](https://git.secluded.site/zed/commit/4f59ec05e25268a1e239f542923724fb68b8797d)). `alengine` runs as a helper process without a window, which is exactly the kind of process App Nap targets (guess; to be checked with `pmset -g assertions` on your Mac). One call fixes it. (`NSActivityLatencyCritical` exists too; it was not found in the pages read.)
- **Thermal state.** `ProcessInfo.thermalState` is nominal, fair, serious or critical; at serious Apple says reduce CPU, GPU, I/O and "reduce frame rates" ([Apple: thermal state](https://developer.apple.com/documentation/foundation/processinfo/thermalstate-swift.enum.md), [Apple: respond to thermal changes](https://developer.apple.com/library/mac/documentation/Performance/Conceptual/power_efficiency_guidelines_osx/RespondToThermalStateChanges.html)). A Mac mini rarely gets there; a MacBook can. For a DAW: drop the screen's frame rate and visual effects first (the glass), never the audio; show a notice; do not change the buffer on its own.
- **"Sudden motion"** (the old hard-disk sensor) does not exist on Apple Silicon Macs with SSDs (from knowledge); nothing to do.
- **Efficiency.** The workgroup is also how the system decides the clock: Apple's engineer says the IOProc thread in its workgroup tends to run on P-cores at higher power ([forum 651617](https://developer.apple.com/forums/thread/651617)). When nothing plays, the engine should stop its IOProc (or output silence without waking workers) so the Mac can idle. Today's `alengine` keeps running while the app is open (guess from the code; to check).

### 1.8 The screen side at 240 Hz

- **`CVDisplayLink` is deprecated.** Its replacements on `NSView`, `NSWindow` and `NSScreen` "return a CADisplayLink" (macOS 14 and later); Apple calls CADisplayLink "the recommended and supported way forward", with `CAMetalDisplayLink` "a closely related specialized version" for Metal ([Apple forum 791564](https://developer.apple.com/forums/thread/791564), [Apple forum 800540](https://www.developer.apple.com/forums/thread/800540), [CADisplayLink](https://developer.apple.com/documentation/quartzcore/cadisplaylink.md), [CAMetalDisplayLink](https://developer.apple.com/documentation/quartzcore/cametaldisplaylink.md)). Apple's own custom Metal view sample is stale on this point.
- **Draw for the target time.** Use `targetTimestamp`, not `timestamp`; never hard-code the rate; compute the time step each frame, because a skipped frame doubles it ([WWDC21 10147](https://developer.apple.com/wwdc21/10147)). A frame rate request is rounded to a factor of the display's rate; the "Limit frame rate" setting and Low Power Mode can cap it.
- **Rosetta clamps display links to 60 Hz** (developer report, [forum 800540](https://www.developer.apple.com/forums/thread/800540)): the native app must be arm64 only, which it is.
- **Full-screen stutter with MTKView** was reported and fixed by triple buffering (at most 3 frames in flight) or by pacing presents oneself ([forum 733033](https://developer.apple.com/forums/thread/733033)).
- **Your monitor** (Odyssey G80SD, DisplayPort, in the test report) is the 240 Hz one; the Mac mini drives it. At 240 Hz a frame lasts 4.17 ms.
- **How native DAWs keep meters smooth without loading the audio thread** (from knowledge, consistent with the plan's shared-memory note): the audio thread writes peak and RMS per block into a small fixed array (atomics or a sequence-locked snapshot); the screen reads the latest values once per frame and does the falling and the peak hold itself, using time, not block counts. Waveforms are drawn from precomputed peak files at several zoom levels (REAPER's `.reapeaks` is the known example), never from the audio. The playhead is computed on the screen from the device's sample time and the host clock (`mach_absolute_time`), so it moves every frame even when audio blocks arrive in bursts.
- **For Electron now:** the same snapshot, mapped into the page as shared memory by a small native add-on, is what removes "you will always pay a price in terms of synchronicity" (plan section 2, route C). JSON lines stay for commands only.

### 1.9 Disk streaming and large libraries

- Kontakt's DFD keeps only "the first portion of each sample" in memory and reads the rest from disk while playing ([Native Instruments: DFD](https://support.native-instruments.com/support/solutions/articles/69000879768-what-is-dfd-)); the default preload is 60 KB per sample, and on an SSD Spitfire says "as low as 6KB" works ([Spitfire](https://support.spitfireaudio.com/en/articles/11815486-reducing-ram-usage-when-using-ssds)).
- **Kontakt does its own streaming.** The host's job is only to call it in time and not to starve its disk threads; nothing to build for it.
- **AudioLab's own streaming** (audio clips, recordings, the sampler) needs the same pattern when projects grow: the start of each clip in memory, a disk thread (normal QoS, or an interval workgroup if it must meet deadlines) reading ahead into lock-free rings, the audio thread never opening a file. The `.audiolab` file today holds audio inside the gzip (plan 1.3), which cannot be streamed; a project folder or an uncompressed audio part is needed for long recordings. That is a project-format decision for later (task NR13).

### 1.10 Memory and startup speed

- Load the project and the audio first, plug-ins after, each in the background, and show each device strip as "loading" until ready (Bitwig's approach, 1.4). Your load times make this matter: Pigments 4.0 s, Neutron 4 1.2 s, Abyss 0.3 s.
- Instantiate plug-ins in parallel where the format allows (VST3 says main thread for creation; so parallel only across separate helper processes; in the engine, one at a time on the main thread but **without** blocking the screen: the engine's main thread is not the app's).
- Keep plug-in state bytes as they are, untouched, in the project (already the plan).
- Wired memory: lock only the engine's own audio buffers, not plug-ins' (Kontakt's sample pools would make the Mac swap; guess).

### 1.11 Signing, sandbox and notarisation

- Already in the plan (section 7): ad hoc signing now; with an account later, the hardened runtime plus "disable library validation" so third-party plug-ins load. New here: the scanner child needs the entitlement too, and the `library` option must not be used (1.5). Microphone use needs `com.apple.security.device.audio-input` under the hardened runtime, and the system asks once (from knowledge and the JUCE thread's entitlement list).
- A sandboxed host can load user-installed VST3: Apple's DTS engineer prototyped it; the user must grant the folders through an open panel and the host keeps a security-scoped bookmark ([Apple forum 845750](https://developer.apple.com/forums/thread/845750)). Relevant only if the Mac App Store is ever wanted (your pick U2a is direct download).

### 1.12 Accessibility

- Logic offers a "controls view" for every plug-in: a plain list of its parameters that VoiceOver reads and changes ([Apple: VoiceOver and plug-ins](https://support.apple.com/en-ie/101781)). AudioLab's device strip for plug-ins (P3) is already a list of parameters; making it the accessible view costs little.
- Native screens: knobs and faders drawn in one Metal view each need an `NSAccessibilityElement` child with the slider role, a label, a value that can be read and set, and a value-changed notification ([Apple: custom controls](https://developer.apple.com/library/content/documentation/Accessibility/Conceptual/AccessibilityMacOSX/ImplementingAccessibilityforCustomControls.html)). A rule for stage 4, not a task now.

---

## 2. Recommendations for AudioLab's native engine and screens

Gain: what you get. Effort: in cloud tasks of 1 to 3 hours. The task names point to section 3.

### Engine

| # | Recommendation | Expected gain | Effort | Task |
|---|---|---|---|---|
| E1 | Every engine worker thread is a time-constraint thread joined to the device's workgroup; rejoin on device change; count from `os_workgroup_max_parallel_threads` | Multicore without dropouts at low load on Apple Silicon (the Blue Cat failure); P-cores for audio | 1 | NR1 |
| E2 | No locks, no allocation on the audio thread: SPSC queues, atomics, pointer swap with deferred deletion; RealtimeSanitizer on CI | "Real-time safe" proven, not assumed; fewer rare clicks | 1 to 2 | NR2 |
| E3 | Flush-to-zero around plug-in calls only; AudioLab's own devices without it; bit test covers a denormal case | Plug-ins safe from denormal spikes; AudioLab's bits still match the web | under 1 (part of NR2) | NR2 |
| E4 | Parallel graph scheduler (inputs-done order, IO thread works too, critical path measured) | Uses the 4 P-cores; the meter shows the real limit | 2 to 3 | NR3 |
| E5 | Two paths: live at the device buffer, the rest computed ahead (about 23 to 35 ms) | The biggest single gain for many plug-ins at 32 frames; Cubase and Logic class | 2 to 3 | NR4 |
| E6 | Warm up every plug-in off the audio thread before it joins the graph; pre-fault all buffers | Removes first-block spikes (Surge XT: 4.4 ms) | under 1 | NR5 |
| E7 | Overload and worst-block telemetry: the HAL's overload notification, a per-block time histogram, per-track and per-plug-in time | You see what clicked and why; the test app reports already point this way | 1 | NR6 |
| E8 | App Nap off while the engine plays; stop the IOProc when idle; thermal state watched | No scrambled audio under load; lower power when idle | under 1 | NR7 |
| E9 | Clock drift: smooth correction between the page's clock and the DAC (already named in N2) | No gaps over minutes in stage 1 to 2 | 1 | (NB N2) |
| E10 | Measured latency with a loop-back cable, reported per buffer size | A true number for the settings page | 1 | NR-LAT |
| E11 | Disk streaming for AudioLab's own clips | Long recordings and big projects without memory growth | 2 | NR13 |

### Plug-ins

| # | Recommendation | Expected gain | Effort | Task |
|---|---|---|---|---|
| P1 | A host-side VST3 conformance layer: all calls on the right thread, restartComponent queued from any thread, the restart sequence, state only on the main thread, edit storms batched per frame | Fewer crashes and hangs with real plug-ins (Pigments, Kontakt); no preset-recall lag | 2 | NR5 |
| P2 | Steinberg's validator on the test plug-ins in CI, plus the host's own sequence checks | Proof of P1 | part of NR5 | NR5 |
| P3 | Engine crash → the app restarts it and reloads the project state; the plug-in is recorded; next load offers "run apart" or block | A crash costs a second of sound, not work | 1 to 2 | NR8 |
| P4 | Per-plug-in hang detection: a block that takes more than N deadlines is noted against that plug-in | Finds the bad one in a full song | part of NR6 | NR6 |
| P5 | "Run apart" helper: shared memory plus a Mach semaphore wake, measured at 32, 64 and 128 frames on your M4 | Isolation and Intel plug-ins (31 of your bundles) with a known cost | 2 to 3 | NR9 |
| P6 | Scan cache and background rescan; project first, plug-ins after | Start in seconds, not the scan time; project usable during Pigments' 4 s | 1 to 2 | NR10 |
| P7 | Delay compensation proven with real latencies (Pro-L 2 2,875, Ozone 2,227) and latency changes while playing | Phase-aligned mixes with mastering plug-ins | 1 to 2 | NR11 |
| P8 | CLAP host with the thread pool, before AU (your call: it changes pick P4) | Right scheduling of plug-in threads on Apple Silicon; smallest format | 2 to 3 | NR14 |
| P9 | ARA 2 host for Melodyne once audio clips are native | Melodyne in full mode | 3 to 5 | NR15 (spike) |

### Screens (now in Electron, later native)

| # | Recommendation | Expected gain | Effort | Task |
|---|---|---|---|---|
| U1 | Meters, playhead, CPU and overload numbers through a shared-memory snapshot read once per frame; JSON only for commands | Smooth meters at 240 Hz, no audio-thread cost, no bridge lag | 1 to 2 | NR12 |
| U2 | A deadline meter (how close to missing the deadline), not CPU %; per track and per plug-in time in a performance view | You see the real limit, as in Live and REAPER | part of NR6/NR12 | |
| U3 | "Live" marker on tracks that run on the low-latency path; a setting for the ahead amount | Explains why the selected track costs more (Logic's lesson) | with NR4 | |
| U4 | Device strip for each plug-in: "loading", "crashed: Reload", "running apart", "Intel only" states | Trust; Bitwig's Reload button | with NR8/NR10 | |
| U5 | Plug-in manager: scan results, blocklist, Intel only, run apart per plug-in, rescan | One place for 222 plug-ins | 1 to 2 | (N4) |
| U6 | Latency read-out: buffer, device, safety, plug-in delay compensation, measured round trip | Honest numbers | with NR-LAT | |
| U7 | Native screens: display link from `NSView` (a CADisplayLink) or `CAMetalDisplayLink`, draw for `targetTimestamp`, triple buffering, arm64 only | 240 Hz without stutter | spike 1 | NR16 |
| U8 | Under thermal "serious": lower the frame rate and the glass first, show a notice | Audio never pays for the screen | with NR7 | |
| U9 | Accessible "controls view" for plug-ins (the strip as a list) | VoiceOver can reach every plug-in parameter | later | |
| U10 | Waveforms from precomputed peak files at several zoom levels | Smooth zoom on long clips | with NR13 | |

---

## 3. Proposed new tasks

Each is one cloud task of 1 to 3 hours, touches only `native/`, `tools/native-lab/` and the native-lab workflow (no `index.html`, no `desktop/`), and ends with a proof on the macOS runner (`macos-15` Apple Silicon, virtual) and a short check in the test app on your Mac. They fit inside NB's stages; the scheduling chat decides the order. Suggested order: NR2, NR1, NR6, NR5, NR12, NR3, NR4, then the rest.

**NR1. Real-time worker threads in the device's workgroup.**
- Builds: a worker pool in `native/engine/` (time-constraint policy set first, then `os_workgroup_join` on the device's `kAudioDevicePropertyIOThreadOSWorkgroup`; rejoin when the device changes; leave on exit; retain and release the workgroup). Size from `os_workgroup_max_parallel_threads`.
- Runner proof: a test program opens the virtual device, joins N workers, logs every join result (0, not EINVAL), runs a synthetic load split over the workers for 60 s at 64 frames, and counts deadline misses with and without joining.
- Your Mac: test app 0.5 gets a "workers" menu (0, 2, 3); the report shows join results and the worst block at 32 and 64 frames with Serum 2 plus three copies of Pigments.

**NR2. Real-time safety, enforced.**
- Builds: SPSC queue and pointer-swap-with-deferred-delete helpers in `native/common/`; the test app's mutex replaced; a scoped flush-to-zero guard used only around plug-in calls; `[[clang::nonblocking]]` on the IOProc path.
- Runner proof: a CI job builds with upstream Clang (`-fsanitize=realtime`) and plays Surge XT and the Steinberg examples for 10 s, failing on any allocation or lock on the audio thread; ThreadSanitizer run of the queue stress test; the Bitcrusher bit test with a denormal input still gives the web's bits.
- Your Mac: test app 0.5 behaves as 0.4 (same report lines), and opening a plug-in's window while playing no longer shares a lock with the audio thread.

**NR3. Parallel graph scheduler.**
- Builds: a DAG of nodes (tracks, sends, groups, master), scheduled by inputs done on the NR1 pool, with the IO thread taking part; critical-path and per-node time measured.
- Runner proof: graphs of 16, 64 and 256 synthetic nodes with fixed work; output bit-identical to the single-threaded run; deadline misses counted at 64 and 128 frames; scheduler overhead per block reported.
- Your Mac: the same graphs in the test app ("graph test"), with the report's worst block per graph size.

**NR4. Render ahead for tracks that are not live.**
- Builds: the second path: non-live nodes computed ahead by a set amount (23, 35, 93 ms) into rings; the live set on the device buffer; switching a track live without a gap; flush and refill on transport jump or automation edit.
- Runner proof: a song of 32 synthetic tracks rendered both ways is bit-identical; a track switched live mid-play has no gap or repeated block; jump test.
- Your Mac: 16 instances of a heavy plug-in at 32 frames with render ahead off and on; failed blocks and worst block in the report.

**NR5. VST3 host conformance and warm-up.**
- Builds: in `vst3_format.cpp` and the engine: every controller call on the main thread through a queue; `restartComponent` accepted from any thread; the full restart sequence; `getState`/`setState` only on the main thread; edit storms coalesced per UI frame; output parameter changes from `process` read back; a warm-up of two silent blocks before a plug-in enters the graph.
- Runner proof: Steinberg's validator on the four example plug-ins and Surge XT in CI; a host-side log that asserts the call order; first-block time after warm-up under 2× the average.
- Your Mac: preset changes in Pigments, Serum 2 and Kontakt 8 while playing: no failed blocks; `[param]` lines show batching.

**NR6. Overloads, worst blocks and who caused them.**
- Builds: the HAL overload listener, a per-block time histogram, per-node and per-plug-in time, a "slow plug-in" record when one exceeds its share many times; all in the engine's status.
- Runner proof: an artificial slow node is found and named; histogram sums match the block count.
- Your Mac: the report gets a table of the five slowest plug-ins and every overload with its time.

**NR7. Power: App Nap, idle, thermal.**
- Builds: `beginActivity` while the engine plays (and only then); IOProc stopped after N seconds of transport stop and silence (setting); thermal state events sent to the app.
- Runner proof: `pmset -g assertions` shows the activity while playing and not after; the IOProc stops and restarts with the first note within one buffer.
- Your Mac: the report shows the assertion and the thermal state; you play after the app was in the background for 10 minutes and nothing is scrambled.

**NR8. Engine crash recovery.**
- Builds: the bridge notices the engine died, restarts it, reopens the device, restores the graph and every plug-in's last saved state, and records which plug-in was running at the crash (a crash marker written before each plug-in call, read at restart).
- Runner proof: a test plug-in that crashes on a note; the engine comes back within 2 s with the other plug-ins' state identical; the culprit is named.
- Your Mac: the same test plug-in shipped with the test app.

**NR9. "Run apart": one plug-in in a helper process, measured.**
- Builds: a helper that hosts one plug-in; audio and events in shared memory; one Mach semaphore (or `os_sync_wait_on_address`) wake each way per block; the helper's thread joins the device's workgroup if the API allows from another process (to be found out; else an interval workgroup); the same helper under Rosetta for Intel-only plug-ins.
- Runner proof: cost per block at 32, 64, 128 frames against in-process for AGain and Surge XT; bit-identical output; killing the helper silences only that plug-in.
- Your Mac: the same table on the M4; one of your Intel-only plug-ins (Arcade) plays through the Rosetta helper.

**NR10. Scan cache and project-first loading.**
- Builds: a cache file of scan results keyed by path, size and modification time; a background rescan of only what changed; parallel child scanners (4 at a time); in the engine, plug-ins created one by one after the project's own audio runs, each strip "loading" until ready.
- Runner proof: second start rescans 0 bundles; a changed bundle is rescanned; a project with 6 plug-ins plays its non-plug-in tracks before the plug-ins are ready.
- Your Mac: scan time of the 253 bundles first and second time (expected: the second well under a second).

**NR11. Delay compensation with real latencies.**
- Builds: latency per node through the graph, compensation on parallel paths and sends, a change of latency while playing handled without a click (fade, re-align).
- Runner proof: a test plug-in with settable latency (built in CI from Steinberg's ADelay example) on one of two parallel paths; an impulse comes out aligned to the sample; latency changed mid-play.
- Your Mac: Pro-L 2 and Ozone on one track, a dry copy on another; null test in the report.

**NR12. Meters and positions through shared memory.**
- Builds: a fixed-layout snapshot (peaks, RMS, playhead sample time with its host time, CPU, overloads) written by the engine each block with a sequence counter; a small native add-on for the shell that maps it into the page (no `desktop/` change needed in this task: proven in `tools/native-lab/electron-tap/`).
- Runner proof: the page reads the snapshot 240 times a second for 60 s; no torn reads; reading adds nothing measurable to the audio thread; meter delay from engine to page under one frame.
- Your Mac: the tap test app shows a meter and playhead at 240 Hz on the Odyssey.

**NR13. Disk streaming for AudioLab's own clips (design and proof).**
- Builds: a reader thread with read-ahead rings per clip, the first part of each clip resident, the audio thread never touching files; peak files at several zoom levels for waveforms.
- Runner proof: 128 clips streamed at once from the runner's disk at 64 frames without a gap; output identical to all-in-memory.
- Your Mac: the same test with 256 clips.

**NR14. CLAP host with the thread pool (if you move CLAP before AU).**
- Builds: CLAP behind `plugin_api.h` (entry, factory, audio ports, note ports, params, state, GUI on Cocoa, latency) and the thread-pool extension on the NR1 pool.
- Runner proof: Surge XT's CLAP build loads, plays, saves and restores state; clap-validator passes; a plug-in using the thread pool runs its tasks on joined workers.
- Your Mac: u-he and Surge CLAPs you own, against their VST3 versions (time per block).

**NR15. ARA 2 spike for Melodyne.**
- Builds: the ARA SDK (Apache 2.0) added; a minimal host that gives Melodyne one audio clip with ARA, reads its analysis and plays its edit back. Only after audio clips exist in the native engine.
- Runner proof: the SDK's own example ARA plug-in analyses and plays a clip in CI.
- Your Mac: Melodyne opens a clip in ARA mode and shows the notes.

**NR16. Native 240 Hz drawing spike.**
- Builds: a small Metal view in the test app driven by the `NSView` display link (or `CAMetalDisplayLink`), drawing the NR12 meters and a waveform from a peak file, at most 3 frames in flight, drawing for `targetTimestamp`; a frame-time histogram.
- Runner proof: the build machine's virtual display (60 Hz) shows no missed frames over 60 s; screenshots.
- Your Mac: 240 Hz on the Odyssey, frame-time histogram in the report; you judge the smoothness.

**NR-LAT. Measured round-trip latency.**
- Builds: a test that plays a click and finds it in the input; reports frames and ms for each buffer size, against the calculated figure.
- Runner proof: on BlackHole loop-back (which gives the software part only).
- Your Mac: a cable from the AMS-24's output to its input; the table for 32, 64, 128 frames.

---

## 4. What NB should change in its current plan

NB was not edited by this task. These are suggestions for whoever runs NB next; each says where it fits.

1. **No `std::mutex` on any audio path in the engine** (the test app's `try_lock` is the pattern not to copy). Use the queues and the pointer swap of 1.3. Fits N2 and every later stage.
2. **Plan the worker threads around the workgroup from the start of N3** (1.2): no thread pool that is not joined; at most the recommended count; the IO thread works too.
3. **Flush-to-zero: off for AudioLab's devices, on around plug-in calls** (1.3). Add a denormal case to the bit tests. Fits N3 and N4.
4. **Warm up plug-ins before they enter the graph** (two silent blocks off the audio thread), and pre-fault every buffer at graph build. Fits N4.
5. **Decide the block-size rule in N3 before porting devices**: either every ported device is proven block-size independent (bit test at 32, 64, 128 and odd sizes), or the engine runs fixed 128-frame sub-blocks with a ring at the device. Render ahead (NR4) and the live path depend on it.
6. **Design the graph for two paths** (live and ahead) even if only one is built at first: nodes know whether they are live; the scheduler can run a subgraph ahead.
7. **Meters and positions through shared memory in N2**, JSON lines for commands only. The N2a socket stays for audio from the page until the page stops making sound.
8. **VST3 call threads by the rules** (1.5): the engine's main thread does creation, state and controller calls; the audio thread only `process`; `restartComponent` from any thread goes into a queue; export calls state only from the main thread.
9. **App Nap guard and idle stop in `alengine`** (1.7): one call each.
10. **Engine crash recovery in N2's bridge** (the bridge already starts the engine; restarting it with the last state is the next step), before "run apart" (1.5).
11. **Scan cache in N4**, and the scanner child signed with the same entitlements as the app when signing comes (1.5, 1.11).
12. **Ask the user whether CLAP should come before Audio Units** (1.6). It changes pick P4, so NB should not change the order on its own.

---

## 5. What this research could not settle

- **Time-constraint values** for worker threads: no page read gives Apple's recommended numbers; the forum practice is "the buffer's length for all three" and "any value works once joined". NR1 measures.
- **Whether a helper process's thread can join the device workgroup of another process** (for "run apart"): not found. NR9 finds out.
- **CLAP thread-pool call rules**: the header could not be read here; the summary in 1.6 is from knowledge.
- **Whether Chromium's built-in audio nodes flush denormals today**: a 2017 statement says yes for the graph; the current AudioWorklet test says no for worklets. Checked per device when ported.
- **REAPER's buffering page** and **the KVR thread about Bitwig on M4** could not be loaded.
- **Out-of-process cost**: only Ardour's estimate exists; no DAW publishes measurements. NR9 measures.
- **The M4's core counts and clocks** are from knowledge, not read here.

## 6. Sources

Apple
- [Understanding audio workgroups](https://developer.apple.com/documentation/audiotoolbox/understanding-audio-workgroups)
- [Adding parallel real-time threads to audio workgroups](https://developer.apple.com/documentation/audiotoolbox/adding-parallel-real-time-threads-to-audio-workgroups)
- [Workgroup management](https://developer.apple.com/documentation/audiotoolbox/workgroup-management)
- [WWDC20 10224, Meet Audio Workgroups](https://developer.apple.com/videos/play/wwdc2020/10224/)
- [Forum 726096: workgroup threads not on P-cores](https://developer.apple.com/forums/thread/726096), [732171](https://developer.apple.com/forums/thread/732171), [651617: IOCycleUsage and asymmetric cores](https://developer.apple.com/forums/thread/651617)
- [coreaudio-api, June 2021: joining the device workgroup](https://lists.apple.com/archives/coreaudio-api/2021/Jun/msg00004.html)
- [Debugging out-of-process audio units on Apple silicon](https://developer.apple.com/documentation/audiotoolbox/debugging-out-of-process-audio-units-on-apple-silicon), [forum 805894](https://developer.apple.com/forums/thread/805894), [forum 766503](https://developer.apple.com/forums/thread/766503)
- [Logic Pro multithreading](https://support.apple.com/HT205975), [Logic Pro: avoid system overloads](https://support.apple.com/en-us/HT203930), [Logic Pro: plug-ins with VoiceOver](https://support.apple.com/en-ie/101781)
- [CADisplayLink](https://developer.apple.com/documentation/quartzcore/cadisplaylink.md), [CAMetalDisplayLink](https://developer.apple.com/documentation/quartzcore/cametaldisplaylink.md), [forum 791564](https://developer.apple.com/forums/thread/791564), [forum 800540](https://www.developer.apple.com/forums/thread/800540), [forum 733033](https://developer.apple.com/forums/thread/733033), [WWDC21 10147](https://developer.apple.com/wwdc21/10147), [Creating a custom Metal view](https://developer.apple.com/documentation/metal/creating-a-custom-metal-view.md)
- [ProcessInfo.ThermalState](https://developer.apple.com/documentation/foundation/processinfo/thermalstate-swift.enum.md), [Respond to thermal state changes](https://developer.apple.com/library/mac/documentation/Performance/Conceptual/power_efficiency_guidelines_osx/RespondToThermalStateChanges.html), [Prioritize work at the app level](https://developer.apple.com/library/archive/documentation/Performance/Conceptual/power_efficiency_guidelines_osx/PrioritizeWorkAtTheAppLevel.html)
- [Forum 845750: sandboxed host loading VST3](https://developer.apple.com/forums/thread/845750), [forum 122467](https://developer.apple.com/forums/thread/122467)
- [Implementing accessibility for custom controls](https://developer.apple.com/library/content/documentation/Accessibility/Conceptual/AccessibilityMacOSX/ImplementingAccessibilityforCustomControls.html)

Steinberg, plug-in formats
- [VST3 API documentation (threading)](https://steinbergmedia.github.io/vst3_dev_portal/pages/Technical+Documentation/API+Documentation/Index.html)
- [Forum: getState/setState thread](https://forums.steinberg.net/t/is-icomponent-getstate-setstate-thread-safe/201734), [forum: restart sequence](https://forums.steinberg.net/t/what-is-the-correct-call-sequence-between-plugin-and-host-when-parameters-have-changed-while-it-is-processing-audio/201851)
- [ASIO-Guard details](https://www.steinberg.help/r/details-on-asio-guard-in-cubase-and-nuendo), [ASIO-Guard levels, Cubase 16](https://helpcenter.steinberg.de/hc/en-us/articles/206103564)
- [CLAP thread pool](https://cleveraudio.org/1-feature-overview/_thread-pool/)
- [ARA SDK](https://github.com/Celemony/ARA_SDK), [Celemony: 10 years of ARA](https://www.celemony.com/en/10-years-of-ara), [Wikipedia: ARA](https://en.wikipedia.org/wiki/Audio_Random_Access)

DAW makers
- [Ableton: multi-core FAQ](https://help.ableton.com/hc/en-us/articles/209067649), [Ableton: VST3 preset recall lag](https://ableton.github.io/plugins/vst3-preset-recall-lag)
- [Bitwig: plug-in handling](https://bitwig.com/userguide/latest/vst_plug-in_handling_and_options), [Bitwig: crash protection](https://www.bitwig.com/en/19/plugin-hosting-video.html), [Bitwig: modern foundations](https://www.bitwig.com/modern-foundations/)
- [Ardour: why no plug-in crash protection](https://ardour.org/plugins-in-process.html)
- [Sound On Sound 2011: REAPER anticipative FX](https://www.soundonsound.com/techniques/running-multiple-plug-ins)
- [Native Instruments: DFD](https://support.native-instruments.com/support/solutions/articles/69000879768-what-is-dfd-), [Spitfire: RAM and SSDs](https://support.spitfireaudio.com/en/articles/11815486-reducing-ram-usage-when-using-ssds)

Developers
- [Ross Bencina: Real-time audio programming 101](https://hn.jakechampion.name/reader/http://www.rossbencina.com/code/real-time-audio-programming-101-time-waits-for-nothing)
- [Timur Doumler: Using locks in real-time audio processing, safely](https://hn.jakechampion.name/reader/https://timur.audio/using-locks-in-real-time-audio-processing-safely), [CppCon 2015: C++ in the audio industry](https://isocpp.org/blog/2016/06/cppcon-2015-cpp-in-the-audio-industry-timur-doumler)
- [LMMS realtime conventions](https://github.com/LMMS/lmms/wiki/Realtime-Conventions)
- [edwloef: real-time safe multi-threaded DAW audio](https://hn.jakechampion.name/reader/https://edwloef.github.io/posts/real-time-safe-multi-threaded-daw-audio)
- [Blue Cat 2023: multicore issues on Apple Silicon](https://www.bluecataudio.com/Blog/preview/realtime-audio-multicore-issues-for-apple-silicon-end-of-the-story/), [Blue Cat 2025: how to fix](https://www.bluecataudio.com/Blog/?p=8798)
- [JUCE AudioWorkgroup](https://docs.juce.com/develop/classAudioWorkgroup.html), [JUCE forum 54240: EINVAL on join](https://forum.juce.com/t/os-workgroup-join-consistently-returns-einval-cant-join-audio-workgroup/54240), [JUCE forum 52188](https://forum.juce.com/t/mac-m1-thread-priority-audio-workgroups/52188?page=2), [JUCE forum 59348: hosted VST3 threading](https://forum.juce.com/t/hosted-vst3-threading-issue/59348), [JUCE forum 48425: scanner under hardened runtime](https://forum.juce.com/t/child-process-hardened-runtime-issue/48425), [JUCE forum: Tracktion graph talk](https://forum.juce.com/t/adc-tracktion-graph-talk/43052)
- [Eclectic Light: how macOS manages M1 cores](https://eclecticlight.co/2022/04/25/how-macos-manages-m1-cpu-cores/)
- [KVR: are denormals still an issue?](https://www.kvraudio.com/forum/viewtopic.php?p=8314064), [truce-core denormal guard](https://docs.rs/truce-core/0.48.7/src/truce_core/denormal.rs.html)
- [coreaudio-api 2018: page faults](https://lists.apple.com/archives/coreaudio-api/2018/Feb/msg00051.html), [2003](https://lists.apple.com/archives/coreaudio-api/2003/Oct/msg00107.html)
- [Clang RealtimeSanitizer](https://clang.llvm.org/docs/RealtimeSanitizer.html)
- [WPT: AudioWorklet denormals](https://kdab.searchfox.org/firefox-main/source/testing/web-platform/tests/webaudio/the-audio-api/the-audioworklet-interface/audioworklet-denormals.https.window.js), [W3C public-audio 2017](https://lists.w3.org/Archives/Public/public-audio/2017JulSep/0008.html)
- [Zed: prevent App Nap during audio](https://git.secluded.site/zed/commit/4f59ec05e25268a1e239f542923724fb68b8797d)
