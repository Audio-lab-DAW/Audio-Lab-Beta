# AudioLab native Mac app: plan, plug-in hosting and first tests (task NM1)

Pick page: **AudioLab native Mac**, https://claude.ai/artifact/17AwgeWUCCTaDX1Ct3mmcn

Test app for your Mac: **AudioLab VST3 test**, https://github.com/Audio-lab-DAW/Audio-Lab-Pro-Alpha/releases/tag/native-lab-1 (how to open it is in section 10)

The repository now answers under the name `Audio-Lab-Pro-Alpha` (the old address `Audio-Lab-Beta` forwards); links here use the new name.

No app changes in this task. `index.html` and `desktop/` were not touched. New: this document, `native/` (the test code), `tools/native-lab/` (reference files and scripts), `.github/workflows/native-lab.yml` (runs only when started by hand).

## 0. The short version

- You chose a truly native Mac app, with VST3 plug-ins now and Audio Units, CLAP and VST2 later, Apple Silicon only, no Apple Developer account yet.
- A full rewrite of AudioLab is large. The app is 5.8 MB of source in one file: about 3 MB of program code, 31 audio processors, 42 devices, 32 instruments, 1,238 presets, about 17 windows and 124 settings. Rewriting all of it is in the order of **250 to 400 tasks** of the kind this project runs. That is months, and most of it is the interface, which a cloud task cannot see.
- The part where native matters for you (audio devices, latency, CPU, plug-ins) is the **engine**. It is the smaller half: about **95 to 150 tasks**, and it can be checked by machines, bit for bit, without a Mac.
- **Recommendation: route C then B.** Build one native engine in C++ (the same engine later serves Windows), keep the present interface on top of it while the engine takes over, and replace the interface with native screens afterwards, screen by screen. Every stage gives you something that works on the Mac.
- The first tests were built and run on an Apple Silicon build machine. In short: all three ran. The Bitcrusher ported to C++ gives the same bits as the web engine (144,000 of 144,000 samples). The native program listed the devices, opened the output on Core Audio, set a 64-frame buffer, switched the device to 96 kHz and back, and took exclusive use. The VST3 host scanned in a child process (one bundle was made to crash; the host stayed up), loaded Surge XT, Surge XT Effects and four of Steinberg's examples, played notes, ran audio, saved and restored state and rendered in export mode. The test app opened Surge XT's own window on the build machine and played. None of this ran on real audio hardware; that is what the test app on your Mac is for.
- What only you can answer is on the pick page: 6 route and stage questions, 7 plug-in assumptions you can change, 5 questions about Apple, the plug-ins you own and what matters most.

## 1. What was read in the app

Numbers from `index.html` v0.222 (5,813,605 bytes, 21,316 lines), counted by script.

### 1.1 The sound engine

- **Worklets.** `wlLoad(c)` joins 17 source strings into one module and loads it. There are **31 processors** (`registerProcessor`), together about 207,000 characters, about 1,850 dense lines. 13 sit in `WLSRC` (limiter, meter, gate, crusher, transient shaper, de-esser, vocoder, frequency and pitch shifter, resonator, tape stop, chorus, imager); the rest are one string each (Venom, Voice, Crackle, vector delay, Orbit, vector FM, sub bass, psy bass, poly synth, bouncy notes, Emit, grains, ducker, bounce delay, retro buffer).
- **Devices.** `FXDEF` has **42 devices**. `mkFxNode` builds them. They fall into three kinds, and the kind decides how well the sound can be kept:
  - **19 are worklets** (own arithmetic in JavaScript): vdelay, bdelay, crk, voice, duck, loud, limit, chorus, crush, gate, imager, trans, deess, vocoder, fshift, pshift, pcorr, reson, tstop. These can be ported statement by statement. Test A shows what that gives.
  - **16 are built from the browser's own audio nodes**: eq (Biquad), comp, ott and mband (DynamicsCompressor), delay, tdelay, reverb and conv (Convolver), drive, clip and shaper (WaveShaper with oversampling), filter, afilt, side, blur, phaser. Their arithmetic is Chromium's, not AudioLab's. The master limiter (a WaveShaper) and the export limiter (a DynamicsCompressor) belong here too.
  - **6 are note or analysis devices** (chord, bouncy notes, arp, MIDI utility, tuner, spectrum), plus `measure`.
- **Instruments.** `PRESETS` has **32 instruments**. Ten run as worklets (the pooled poly synth with 40 voices, grain sampler, Emit, vector grain, vector FM, Orbit, sub bass, bouncy ball, psy bass, Crackle, Venom). The others are built from browser nodes or rendered to buffers on the main thread (drums, kick, perc, sfx, the modular grid, the sampler outside grain mode, growl, the z-drums).
- **Browser node use in the code:** createGain 277, BiquadFilter 50, Analyser 48, Oscillator 34, BufferSource 26, Delay 17, StereoPanner 13, WaveShaper 11, DynamicsCompressor 6, Convolver 5. The mixer itself (gains, pans, sends, groups, returns) is browser nodes.
- **Presets:** 882 effect presets in 40 devices, 356 instrument presets in 7 banks. They are data and move over unchanged.
- **Export:** `doExport` → `renderMixChunked` (24-beat pieces in parallel OfflineAudioContexts, the "multicore" export) → `renderMix` → `postProc` (normalise, dither with a seeded generator) → `encodeOne`. WAV 16, 24 and 32-bit float, FLAC (own encoder in JavaScript), MP3 (lamejs). Sample rates 44.1 to 192 kHz; the browser resamples inside the offline context, there is no resampler of AudioLab's own.
- **Stem splitter:** HTDemucs as an ONNX model (136 or 166 MB, downloaded) on onnxruntime-web in a worker, with a plain STFT split as fallback.
- **Voice parts:** OpenVoice V2 (ONNX, 64 MB) on onnxruntime-node in a helper process of the desktop app; the Voice device DSP (`vxCore`) runs in a worklet and in workers.
- **No WebAssembly in the engine.** Everything that makes sound is JavaScript or a browser node.

### 1.2 The interface

- 390,616 bytes of CSS, about 70 KB of HTML, about 3.04 MB of JavaScript code (the other 2.3 MB of script is data: the Fractals vocals, icons, the demo song).
- 1,854 named functions and about 5,600 arrow functions.
- 47 canvases (`getContext('2d')`), about 143 drawing functions, plus one drawing function per device.
- 6 sheets and about 11 floating windows (mixer, devices, Voice, Venom, envelopes, presets, the modular grid, audio editor, visualiser, pins, AI voices).
- Settings: 10 tabs, about 124 settings (`docs/settings-audit.md`). 8 themes.
- The glass engine (`tools/glass-lab/glass-engine.js`, 802 lines of WebGL2) now draws the docked panels in v0.223.

### 1.3 The project file

`.audiolab` is a gzip around a 16-byte header, a JSON part (`format`, `formatVersion: 1`, `app`, `name`, `project`, `view`, `audio[]`) and raw 32-bit float audio after it. `project` holds bpm, loop, master, tracks, sections, master effects, the export seed. A track holds kind (instrument, audio, group, return), volume, pan, effects, clips, instrument, sends. This format is simple and a native engine can read it as it is. A plug-in fits in as one more device type with a block of bytes (section 6.8).

One thing to know: **the Fractals v10 song is not in the repository.** The app embeds "Fractals remake v6"; v10 exists only as build code in the project doc `claude/audiolab-remake-v10-code.md`. "Fractals v10 opens as the only project on a fresh install" therefore needs the v10 file added to the repository first (one small task, not part of this one because it touches the app).

### 1.4 What the web engine cannot do (from `docs/settings-research-audiophile.md`)

The web engine renders 32-bit float at the rate Chromium gives it. It cannot take exclusive use of a device (hog mode on the Mac, WASAPI exclusive or ASIO on Windows), cannot switch the device's sample rate, cannot choose the device's real format (integer, bit depth), cannot set a true device buffer, cannot use more than 2 inputs, and on Windows cannot get past the system mixer and its limiter. Exclusive use belongs to a process, so a helper program cannot give it to Chromium. Only an engine that opens the device itself can do these. `desktop/native/alvol.swift` (186 lines) already reads and sets the device volume and reads rates and formats from outside; it is the first native code in the project.

## 2. The routes

A "task" below is one cloud task of 1 to 3 hours, as this project runs them. No Mac is in the loop except your own tests and the macOS build machine.

### Route A: full rewrite in Swift (AppKit or SwiftUI, AVAudioEngine or Core Audio)

- **What it is.** Everything new, in Apple's language and Apple's toolkits.
- **Engine.** AVAudioEngine is Apple's ready node graph. It has no way to take exclusive use of a device or to choose the device's real format ([AVAudioEngine](https://developer.apple.com/documentation/avfaudio/avaudioengine)), so a DAW that wants bit-perfect output goes one level lower anyway, to the HAL ([Technical Note TN2091](https://developer.apple.com/library/content/technotes/tn2091/_index.html)). AudioLab's devices are not AVAudioEngine nodes either; each one would be re-typed in Swift.
- **Cost.** Engine 80 to 120 tasks, interface 150 to 250 tasks: **230 to 370 tasks**.
- **What you get and when.** Nothing usable for a long time: a DAW with half its devices is not a DAW.
- **Windows.** Nothing. Swift's interface toolkits do not exist on Windows; the Windows version stays the web app or becomes a second rewrite.
- **Sound risk.** High. Every line of DSP is re-typed in a language whose number handling has to be made to match by hand, and there is no shared code with the reference.
- **Without a Mac.** Builds and command line tests run on the build machine. Screens cannot be seen except as screenshots from the build machine.

### Route B: one shared engine in C++ (or Rust), native Mac interface

- **What it is.** The engine is written once in a portable language. On the Mac it talks to Core Audio, on Windows to WASAPI and ASIO. The Mac interface is native (AppKit, SwiftUI or Metal).
- **C++ or Rust.** C++. The plug-in formats are C++ (VST3) or C (CLAP, Audio Units), and Rust's hosting side is young: the `vst3` crate is raw bindings with no host layer ([vst3 0.1.2](https://docs.rs/crate/vst3/0.1.2/source/README.md)), the `rack` crate hosts VST3 on macOS only and without plug-in windows ([rack](https://docs.rs/crate/rack/latest)), and nih-plug is for writing plug-ins and is in maintenance mode ([nih-plug](https://github.com/robbert-vdh/nih-plug)). Almost every DAW engine is C or C++: Live, Logic, REAPER, Bitwig's engine, Ardour, Waveform, Audacity 4 and Zrythm 2 ([Live](https://en.wikipedia.org/wiki/Ableton_Live), [REAPER](https://en.wikipedia.org/wiki/REAPER), [Bitwig](https://en.wikipedia.org/wiki/Bitwig_Studio), [Ardour](https://en.wikipedia.org/wiki/Ardour_(software)), [Audacity 4](https://phoronix.com/news/Audacity-4.0-Released), [Zrythm 2](https://phoronix.com/news/zrythm-2.0-alpha)). FL Studio is the exception, in Delphi ([Embarcadero](https://www.embarcadero.com/de/case-study/image-line-software-case-study)).
- **Cost.** Engine 95 to 150 tasks (section 2.1), Mac interface 150 to 250 tasks: **245 to 400 tasks**. The engine half is shared with Windows.
- **What you get and when.** As route A if done in this order: nothing until both halves exist.
- **Windows.** The engine carries over. The interface is written again for Windows, or Windows keeps the web interface on the same engine.
- **Sound risk.** Low to medium, see section 4. C++ can run the same arithmetic as the JavaScript, and test A shows it gives the same bits.

### Route C: the same shared engine, the present interface kept and moved over part by part

- **What it is.** The engine of route B, but the interface you have stays on screen while the engine underneath is replaced. The interface runs in a web view; the engine is a native program beside it.
- **Which web view.** Two choices:
  - **The system's own (WKWebView).** Small app. But WKWebView draws at most 60 frames a second: the WebKit bug is still open on 24 November 2026 ([bug 294338](https://bugs.webkit.org/show_bug.cgi?id=294338)), and the only switch is a private one. Your display is 240 Hz and the glass engine was built to reach 240. WKWebView also cannot pass binary data to native code without turning it into text ([Apple forum, June 2026](https://developer.apple.com/forums/thread/830260)). And WebKit is a different browser from the one the whole interface was tested in.
  - **The present Electron shell.** Larger app, but 240 Hz works, the interface is unchanged, and a native add-on or a helper program can share memory with the page.
  - **For the time the web interface lives, keep Electron.** This is a step on the way, not the end state.
- **What a web engine cannot do here.** Plug-ins are native code. They cannot run inside the browser's audio thread: a worklet runs JavaScript in a sandbox with no way to load a VST3. So in route C the plug-ins live in the native engine, and their sound reaches the output there, not in the page. This is why the engine has to own the output from the first stage on (section 3).
- **Known price.** A developer who shipped an Electron interface over a separate native audio engine for four years says "you will always pay a price in terms of synchronicity" ([JUCE forum](https://forum.juce.com/t/electron-js-app-talking-to-juce-audio-engine/40559)): meters and playheads arrive through a bridge. The answer is shared memory for meters and positions and messages only for edits.
- **Cost.** Engine 95 to 150 tasks, bridge and shell 10 to 15, interface 0 at first.
- **What you get and when.** Something after the first 8 to 12 tasks (native output with device control), VST3 after 15 to 25 more, then more of the engine with every task.
- **Windows.** The engine and the bridge carry over; the Windows part is the device layer (WASAPI exclusive, ASIO), 20 to 30 tasks.
- **Is it "truly native"?** The sound is. The window is still drawn by Chromium until the interface is replaced. Said plainly, because you chose "truly native": route C alone is not the end, it is the road.

### Route D: a framework (JUCE and others)

- **JUCE** is the framework most audio software is built on. Version 9.0.5 is current; 9.0 brought a new Core Audio layer ([JUCE releases](https://github.com/juce-framework/JUCE/releases)). It gives a device layer for Mac and Windows, plug-in hosting for VST3, Audio Units and LV2 (VST2 only if you bring Steinberg's old headers yourself, [JUCE breaking changes](https://raw.githubusercontent.com/juce-framework/JUCE/master/BREAKING_CHANGES.md)), an interface toolkit and a web view component ([JUCE README](https://raw.githubusercontent.com/juce-framework/JUCE/master/README.md)).
- **Its price** ([juce.com/get-juce](https://juce.com/get-juce/)): Starter is free up to US$20,000 a year of revenue or funding; Indie is $40 a user a month or $800 once, up to $300,000; Pro is $175 a month or $3,500 once, no limit. The other choice is AGPLv3, which means publishing AudioLab's whole source.
- **Tracktion Engine** is a whole DAW engine on top of JUCE (Waveform is built on it). GPLv3 or paid: free under $50,000 revenue with their branding, then $35 to $300 a seat a month by revenue, and a JUCE licence on top. The figures were read through a mirror of engine.tracktion.com and should be confirmed there ([licensing announcement](https://forum.juce.com/t/announcement-tracktion-engine-licensing-update/56897)). It would replace AudioLab's engine with its own, so the sound would change. Not suitable.
- **iPlug2** is for writing plug-ins, not for hosting them ([iPlug2](https://github.com/iPlug2/iPlug2)).
- **Smaller device layers:** RtAudio (Core Audio, WASAPI, ASIO; [RtAudio](https://github.com/thestk/rtaudio)), PortAudio ([PortAudio](https://www.portaudio.com/docs/v19-doxydocs/api_overview.html)), miniaudio (no ASIO; [miniaudio](https://github.com/mackron/miniaudio)), libsoundio (no ASIO; [libsoundio](https://github.com/andrewrk/libsoundio)). None of them was found to offer exclusive use or the device's real format on the Mac, which are the audiophile points.
- **What JUCE would save.** The device layer for Windows, Audio Unit hosting and plug-in windows on both systems: an estimated 20 to 35 tasks, and it brings years of fixes for odd devices and odd plug-ins. It does not help with the sound engine (that is AudioLab's own arithmetic either way) and it does not write the interface.
- **What it costs beyond money.** A large dependency, its way of doing things in the whole engine, and a licence that starts to cost at $20,000 a year. CLAP hosting was not in the list of formats we read.
- **Judgement.** Tests A and B below were written straight on Core Audio and on Steinberg's SDK, in about 1,500 lines, and they passed on the build machine at the first run. So for the Mac the framework is not needed. It stays the fallback: if Audio Unit hosting or the Windows device layer turns out harder than expected, JUCE can be put under the same `plugin_api.h` interface without changing the engine above it. This is question R3 on the pick page.

### 2.1 Where the engine tasks go (routes B and C)

| Part | What | Tasks |
|---|---|---|
| Device layer, Mac | Core Audio HAL: devices, rates, buffer, exclusive use, real format, volume, inputs, device changes while running | 6 to 10 |
| Bridge and shell | Engine program, shared memory for audio, meters and positions, messages for edits, Settings for the native output | 8 to 12 |
| Plug-in hosting | VST3: scanner, blocklist, tracks, windows, state in the project, delay compensation, export (section 6) | 15 to 25 |
| Worklets | 31 processors, ported statement by statement, each with a bit comparison | 22 to 30 |
| Browser-node devices | 16 devices plus the two limiters: Chromium's biquad, compressor, convolver, shaper and delay arithmetic rebuilt | 15 to 22 |
| Instruments not in worklets | drums, kick, perc, sfx, modular grid, sampler, growl, z-drums | 15 to 22 |
| The mixer and the song | tracks, groups, returns, sends, pan, automation, clips, warp, scheduler, transport, recording, meters, delay compensation | 15 to 22 |
| Export | offline render on all cores, WAV, FLAC, MP3, dither, resampling, loudness | 5 to 8 |
| Stems and voices | ONNX Runtime natively (it has a C++ library), same models | 4 to 8 |
| **Engine total** | | **about 95 to 150** (hosting and bridge included) |
| Windows device layer | WASAPI shared and exclusive, ASIO, VST3 windows on Windows | 20 to 30 |
| Native interface | about 17 windows, 47 canvases, 42 device panels, 124 settings, 8 themes, glass | 150 to 250 |

### 2.2 What native gives, in figures

- **Latency.** Chrome 153 on an M4 with an RME Babyface, round trip through a loopback cable: 25.7 ms at 64 frames, 28.6 ms at 128, 31.5 ms at 256, with the new `renderSizeHint` ([measurement](https://dev.classmethod.jp/en/articles/chrome-153-webaudio-render-size-hint-latency/)). Native Core Audio with a Scarlett 6i6 at 44.1 kHz: about 5.5 ms calculated at 64 frames and 14.2 ms at 256, measured about 3 ms more ([coreaudio-api list](https://lists.apple.com/archives/coreaudio-api/2020/Jan/msg00008.html)). So native is about 3 to 4 times lower on comparable hardware. Different interfaces, so read it as a size, not a promise.
- **CPU.** For compiled code against the browser the best published figure is for WebAssembly: 45 to 55 % slower than native on average, up to 2.5 times ([Jangda et al., 2019](https://arxiv.org/abs/1901.09056v3)). AudioLab's worklets are JavaScript, not WebAssembly, and no solid published figure was found for that. Test A gives our own first figure: the native Bitcrusher runs about 2,400 to 3,900 times faster than real time on one core on the build machine. A like-for-like figure against the worklet needs a measurement in the app (one small task).
- **Real-time safety.** A native audio thread joins the device's workgroup, so the system schedules it with the audio device ([Understanding Audio Workgroups](https://developer.apple.com/documentation/audiotoolbox/understanding-audio-workgroups), [Porting your audio code to Apple silicon](https://developer.apple.com/documentation/apple-silicon/porting-your-audio-code-to-apple-silicon)). It has no garbage collector that can pause it.
- **Devices.** Exclusive use, the device's sample rate, its real format, its buffer size and its volume are plain properties on the HAL. Test A reads and sets them (section 9).

## 3. Recommendation and stages

**Route C as the road, route B as the destination, in C++, without a framework for now.**

Reasons: the engine is where native pays for your priorities (snappiness, low CPU, the effects and the sound engine, DACs and interfaces, plug-ins); it is the half that machines can verify; it is the half Windows can share; and you keep a working AudioLab on the Mac the whole way.

Every stage ends with something you can use on the Mac and a test that proves the sound did not change.

**Stage 0. The proofs (done in this task).** Tests A, B and C, section 9.

**Stage 1. Native output. 8 to 12 tasks.**
- A native program, "AudioLab Engine", starts with the app and opens the output device itself.
- The web engine keeps making the sound; its master output goes to the native engine through shared memory and from there to the device.
- You get: pick the device, switch its sample rate from the app, set its buffer, take exclusive use, pick its real format (for the Gryphon: the exact rate and bit depth, nothing in between), device volume. These are the things section 1.4 says the web engine cannot do.
- Limit, said plainly: the latency does not get lower in this stage. The web engine still runs on Chromium's clock, so a small safety buffer sits between the two (in the order of 10 to 20 ms) and the two clocks are kept together by a resampler that corrects a few parts per million. Playback through the DAC gets better; playing live does not yet.
- Proof: a recording of what the engine sent to the device (through a loopback device on the build machine) against the web export of the same passage. With the clocks locked for the test it must be the same samples.
- Your test: a small build, your Gryphon and your AMS-24, the report file.

**Stage 2. VST3 on a plug-in track. 15 to 25 tasks.**
- A new track kind: the instrument is a VST3. Effects on that track can be VST3 too. The master can hold VST3 effects, because the master is native since stage 1.
- The plug-in runs in the native engine and plays with low latency from the first day, since its sound never passes through the browser.
- The plug-in's own window, a strip in the device chain with its main parameters, presets and a meter, its state saved inside the `.audiolab` file, delay compensation, export.
- Limit: a VST3 effect on a track that is still made by the web engine is not possible until that track has moved (stage 3). Until then VST3 effects work on plug-in tracks and on the master.
- Proof: the checks of test B for every plug-in in a test set, on the build machine; the web part of the mix still compared bit for bit.
- Your test: the plug-ins you own.

**Stage 3. The engine moves. 70 to 110 tasks.**
- Devices and instruments are ported one by one. A track whose whole chain exists natively runs in the native engine; the others keep running in the web engine and arrive as before. The list of native devices grows with every task and is visible in Settings.
- Order by your priorities: first the worklet effects and instruments (the same arithmetic, provable to the bit), then the mixer, then the browser-node devices, then the rest, then export.
- Milestone on the way: "Fractals v10 plays wholly native" as soon as its devices are done; the song uses a part of the list, not all of it.
- When the last device has moved, the web engine is switched off. From then on the whole song runs at the device's buffer size (32 or 64 frames), on all cores, with no browser in the audio path.
- Proof for every device: the web render and the native render of the same input, compared sample by sample, on Linux and on the Apple Silicon build machine, for the factory settings and for presets. Proof for the whole: the Fractals export, web against native.
- Your test: every few tasks a build; you listen and send the report.

**Stage 4. The native interface. 150 to 250 tasks.**
- The interface is rebuilt in native views (AppKit with Metal for the arrangement, the mixer and the glass), window by window, until Chromium is gone. The download shrinks from 154 MB today to a few tens, and the app starts faster and uses less memory.
- This is the largest stage and the one a cloud task can verify least: it can build and take screenshots on the build machine, it cannot feel a drag at 240 Hz. Every window needs your eyes.
- It can start before stage 3 ends, and it can also be decided later: after stage 3 you have native sound, native devices and plug-ins. Question R2 on the pick page.

**Windows** follows after stage 2 or 3 with the same engine: 20 to 30 tasks for WASAPI exclusive, ASIO and plug-in windows. For a closed-source app the ASIO SDK needs Steinberg's own agreement; since October 2025 the SDK is offered under GPLv3 or that agreement ([CDM](https://cdm.link/open-steinberg-vst3-and-asio/), [Libre Arts](https://librearts.org/2025/11/steinberg-relicenses-vst3-and-asio/)), and one developer reports waiting five weeks for an answer in October 2026 ([Steinberg forum](https://forums.steinberg.net/t/proprietary-asio-sdk-license-agreement-no-response-after-5-weeks-odemi-daw/1043608)). Worth sending early.

## 4. Will the sound change? The honest answer, device kind by device kind

The exports of the web engine are the reference.

1. **Worklet devices and instruments (19 devices, 10 instruments): the same bits are possible.** JavaScript numbers are 64-bit floats and its arrays are 32-bit floats; C++ has both. Test A ported the Bitcrusher and got the same bits as the browser in all three cases, including the case with dither and jitter, because the worklet bundle replaces `Math.random` with its own seeded generator and that was ported too. Three rules make this hold:
   - **No fused multiply-add.** On Apple chips the compiler may turn `a*b+c` into one instruction that rounds once instead of twice. Clang allows this by default ([Clang manual, -ffp-contract](https://clang.llvm.org/docs/UsersManual.html)). The engine is built with `-ffp-contract=off`. Test A built the program both ways to see the difference: for this device both builds gave the same bits, so the flag made no difference here; it stays a rule for the engine.
   - **The same maths library.** `Math.exp`, `Math.pow`, `Math.sin` and the others are not defined to the last bit. The browser in today's desktop app (Electron 45, V8 15.6) takes most of them from LLVM's C library; `tanh`, `sinh` and `cosh` are still V8's own in that version ([V8 15.6 source](https://raw.githubusercontent.com/v8/v8/15.6.77/src/base/ieee754.cc)). The native engine will carry the same LLVM functions inside it (they are open source), so the results do not depend on the Mac's or Windows's own library. Test A measured the Mac's own library on the numbers this device needs: the same bits as the browser in all three cases.
   - **The small details of JavaScript.** `Math.round` rounds halves up, `%` keeps the sign of the left side, the bundle zeroes tiny state values every 16 blocks, the block is 128 frames. Each is a line in the port and each is caught by the bit comparison.
2. **Devices made of browser nodes (16 devices, both limiters, the mixer, most non-worklet instruments): measured, not promised.** Their arithmetic is Chromium's. Chromium is open source, so the same formulas can be rebuilt: the biquad, gain, pan, delay and wave shaper are plain arithmetic and should come out the same or within the last bit. Two are harder: the DynamicsCompressor (a long routine with its own look-ahead and curves) and the Convolver (it uses a fast Fourier transform, and Chromium uses a different FFT library on different systems, so even two browsers do not agree to the bit). For these the plan is: rebuild from Chromium's source, measure the difference against the web export, and write the figure down per device. This paragraph is from knowledge of Chromium, not checked against its source today; stage 3 starts with that check.
3. **Resampling in export.** The browser resamples inside the offline context. The native engine needs its own resampler. To keep exports the same, the first native export renders at the project rate with no resampling; other rates are measured against the web export.
4. **Plug-ins.** Not ours, see section 6.9.

Each stage keeps a gate: `tools/engine-tests/export_same.py` (Fractals Kick and Bass levels and checksums) stays as it is, and a new gate compares web and native per device.

## 5. What can and cannot be checked without a Mac

| Can be checked by machines | Needs your Mac |
|---|---|
| Sound equality, device by device and for whole songs (Linux and the Apple Silicon build machine) | Your real devices: exclusive use, rates and formats on the iFi Gryphon and the Zoom AMS-24 |
| That the engine builds and starts on Apple Silicon | True latency (a loopback cable) and whether 32 frames run without clicks |
| Core Audio calls against the build machine's device and a virtual device | Plug-ins you own (paid ones cannot be installed on the build machine) |
| VST3 loading, notes, audio, state, export, time per block, with free plug-ins | How plug-in windows look and behave |
| A window opening and a screenshot of it | How anything feels: drags, 240 Hz, the glass |
| CPU figures on the build machine (shared, so rough) | CPU figures that count: the M4 |

## 6. Plug-in hosting

### 6.1 The VST3 SDK and its licence today

- Since version 3.8 (20 October 2025) the VST 3 SDK is under the **MIT licence**. No agreement to sign, no fee; the GPLv3 and the Steinberg proprietary licence are no longer offered ([VST 3 licence](https://steinbergmedia.github.io/vst3_dev_portal/pages/VST+3+Licensing/VST3+License), [LICENSE.txt](https://raw.githubusercontent.com/steinbergmedia/vst3sdk/master/LICENSE.txt)). The hosting code is covered ([licensing options](https://steinbergmedia.github.io/vst3_dev_portal/pages/VST+3+Licensing/What+are+the+licensing+options.html)).
- The tests use tag `v3.8.1_build_84` (11 August 2026, [release note](https://forums.steinberg.net/t/vst-3-8-1-sdk-released/1038865)).
- **The name.** Using the word "VST" and the logo is optional. If AudioLab writes "VST", Steinberg's usage guidelines apply: the VST Compatible logo next to it, and no "VST" in a company or product name ([usage guidelines](https://steinbergmedia.github.io/vst3_dev_portal/print.html)). So the app says "VST3 plug-ins" with the logo on the same screen, and the test app is not called a "VST" product in any shop.

### 6.2 What a host has to do

All of this is in Steinberg's documentation ([API documentation](https://steinbergmedia.github.io/vst3_dev_portal/pages/Technical+Documentation/API+Documentation/Index.html)); the right column says where the test code already does it.

| Duty | What it means | In the tests |
|---|---|---|
| Find | Look in the standard folders, do not look inside bundles | `findBundles` |
| Scan in a separate process | Loading a plug-in runs its code. A bad one can crash or hang. A child process loads it; if it dies, only the child dies | `scan.cpp`; test B kills one on purpose |
| Blocklist | Remember what failed and why, do not try again until asked | list in the scan result |
| Load | Load the bundle, call its entry function, read its factory ([plug-in format](https://steinbergmedia.github.io/vst3_dev_portal/pages/Technical+Documentation/Locations+Format/Plugin+Format.html)), create the audio part and the control part, connect the two | `vst3_format.cpp` `create` |
| Buses | Audio in and out (main and side-chain), note in and out; ask for stereo, give buffers for every bus | `prepare`, `process` |
| Notes | Note on and off with a position inside the block | `process`; test B plays a pattern |
| Parameters | List them, show their text, send changes with a position inside the block (automation), receive changes made in the plug-in's window | `params`, `setParam`, `Handler` |
| State | Ask both parts for their state as bytes, store them, give them back in the right order | `getState`, `setState` |
| Window | Create the plug-in's view and put it into a native view (`NSView` on the Mac), let it resize | `openEditor`; test C |
| Latency | Read the plug-in's delay, read it again when the plug-in says it changed | `latencySamples`, `takeLatencyChanged` |
| Rate and buffer changes | Stop, set up again, start | `prepare`; test B switches a running plug-in to 96 kHz and 32 frames |
| Export | Tell the plug-in it is not real time, then render faster than real time | `prepare(offline)`; test B |
| Protection while running | Section 6.5 | not yet |

### 6.3 Where plug-ins live on a Mac

| Format | Folders |
|---|---|
| VST3 | `~/Library/Audio/Plug-Ins/VST3`, `/Library/Audio/Plug-Ins/VST3`, `/Network/Library/Audio/Plug-Ins/VST3` ([plug-in locations](https://steinbergmedia.github.io/vst3_dev_portal/pages/Technical+Documentation/Locations+Format/Plugin+Locations.html)) |
| CLAP | `~/Library/Audio/Plug-Ins/CLAP`, `/Library/Audio/Plug-Ins/CLAP`, and what `CLAP_PATH` names ([CLAP entry.h](https://raw.githubusercontent.com/free-audio/clap/main/include/clap/entry.h)) |
| Audio Units | `/Library/Audio/Plug-Ins/Components` and the same under the home folder; the system keeps the list, the host asks the system |
| VST2 | `/Library/Audio/Plug-Ins/VST` and the same under the home folder (by convention) |

### 6.4 Apple Silicon and Intel-only plug-ins

A program built for Apple Silicon cannot load a plug-in built only for Intel into itself. Ableton says the same of Live: its Apple Silicon build sees only VST plug-ins built for Apple Silicon ([Ableton](https://help.ableton.com/hc/en-us/articles/4410323149074)). There are two ways out: run the whole app under Rosetta (everything slower), or run Intel plug-ins in a helper process under Rosetta and send audio across, which is what Bitwig does ([CDM on Bitwig 4](https://cdm.link/bitwig-studio-4-apple-silicon-m1/)) and what Apple does for Audio Units ([Apple: out-of-process Audio Units](https://developer.apple.com/documentation/audiotoolbox/debugging-out-of-process-audio-units-on-apple-silicon)).

The scanner in the tests already reads each bundle's header and reports "built for Intel only" instead of a failure. The helper process is the same piece as the crash protection below, so it comes with it. How many of your plug-ins are Intel-only is question U3; the test app's report answers it.

### 6.5 Crash protection: where a plug-in runs, and what each choice costs

- **Scanning** always in a child process. Cost: none that is heard; the scan is a little slower. Done in the tests.
- **Running, choice 1: inside the engine.** Lowest latency and CPU. A plug-in that crashes takes the engine down. In route C the engine is already a separate program from the interface, so the window, the project and unsaved edits survive, and the engine can be started again. This is the level REAPER calls native and Bitwig calls "within Bitwig" ([Bitwig plug-in handling](https://www.bitwig.com/userguide/latest/vst_plug-in_handling_and_options)).
- **Running, choice 2: plug-ins in their own helper process** (all together, per maker, or each alone, as Bitwig offers). A crash silences that plug-in only. Cost: the audio crosses a process border twice per block. Published figures are thin. Bitwig and Apple publish none; Apple only says in-process loading still matters for apps that need minimal latency ([Apple: porting audio code](https://developer.apple.com/documentation/apple-silicon/porting-your-audio-code-to-apple-silicon)). Ardour's own estimate, not a measurement, is about 30 microseconds per switch and so several milliseconds per block for a full session if every plug-in is alone ([Ardour](https://ardour.org/plugins-in-process.html)). A third-party note on REAPER says its dedicated-process mode adds no latency ([REAPER blog](https://reaper.blog/2012/02/run-plugin-as-dedicated-process/)). In short: done with shared memory and a wake-up, it costs CPU per plug-in and no extra buffer; done with a queue, it costs one buffer. It has to be measured on our own code.
- **Plan:** choice 1 first (stage 2), since the engine is already apart from the interface. Choice 2 as a setting per plug-in afterwards ("Run apart"), which is also the Intel helper. Measured before it is offered.

### 6.6 How plug-ins fit the device chain and the mixer

- A plug-in is a device like any other in the chain: it has a place in the order, a bypass, a strip.
- **The strip** shows the plug-in's name and maker, eight parameters of your choice (the first eight to start with), a preset menu, a meter, and a button that opens the plug-in's own window. The strip uses AudioLab's knobs; the window is the plug-in's.
- **An instrument plug-in** takes the instrument slot of a track and gets the track's notes.
- **Automation** uses the same lanes as AudioLab's own parameters; values are sent with their position inside the block.
- **Latency** reported by the plug-in goes into the same delay compensation the app already has.
- **Side-chain:** a second audio input bus; a later step.

### 6.7 Sample rate, buffer, export

Shown working in test B: the same plug-in is set up at 48 kHz and 128 frames, then while it lives at 96 kHz and 32 frames, and a second copy in export mode. For export the engine waits for the plug-in instead of dropping blocks, and plug-ins that load samples in the background get time to finish (some need a moment after loading; a known cause of silent first notes).

### 6.8 State in the project file

A plug-in device in the `.audiolab` file holds: format (`vst3`), the plug-in's id, name and maker (so a missing plug-in can be named), and its state as bytes in the audio part of the file, untouched. Opening a project without the plug-in keeps the bytes and shows "missing: name by maker"; saving again loses nothing.

### 6.9 Exports with a plug-in in the chain cannot be promised bit-identical

AudioLab's own devices are deterministic by design (the export seed). A plug-in is someone else's program. Many are the same twice in a row; many are not: free-running oscillators, random phases, their own random numbers, analogue-style noise. Test B measures this instead of assuming it: for each plug-in it compares two fresh copies, a fresh copy against a restored one, and real time against export mode. The results for the test plug-ins are in section 9.

What follows for AudioLab:
- The promise "same project, same seed, same sound" holds for the part of the project made by AudioLab's own devices. The export sheet says so when a plug-in is in the song.
- The engine tests keep comparing the web engine and the native engine on projects without plug-ins.
- "Freeze" on a plug-in track gives a fixed sound when you need it: it renders the track once and plays the file.

### 6.10 Audio Units, CLAP and VST2 later

`native/host/plugin_api.h` is the interface the engine talks to. It names no format: a plug-in has information, buses, parameters from 0 to 1, notes, a process call, a state as bytes, a window in a native view. VST3 is the first class behind it. Each further format is one more class; the engine, the mixer, the project file and the tests do not change.

- **Audio Units.** Apple's own format; a system API, no SDK to licence. Older units (AUv2) load into the host; newer ones (AUv3) are app extensions that run apart by default, and one API hosts both ([hosting with the AUv2 API](https://developer.apple.com/documentation/audiotoolbox/hosting-audio-unit-extensions-using-the-auv2-api), [migrating to the AUv3 API](https://developer.apple.com/documentation/audiotoolbox/migrating-your-audio-unit-host-to-the-auv3-api)). The system does the scanning (`auval` checks a unit). Estimated 8 to 12 tasks.
- **CLAP.** MIT licence, plain C headers, version 1.2.10 ([CLAP](https://github.com/free-audio/clap)). The host gives the plug-in a small table of functions and searches the folders above. A checker exists ([clap-validator](https://github.com/robbert-vdh/clap-validator)). The simplest of the four. Estimated 6 to 10 tasks.
- **VST2.** Here the honest part:
  - Steinberg stopped giving VST2 licences in October 2018. Its position: without an agreement signed before then "you are not allowed to distribute new VST 2 plug-ins or VST 2 hosts", and the old headers may not be passed on ([Steinberg licensing FAQ](https://steinbergmedia.github.io/vst3_dev_portal/pages/FAQ/Licensing.html)). AudioLab has no such agreement and cannot get one.
  - What others do: write the interface again from observation, without Steinberg's files. Three such headers exist. VeSTige (used by LMMS and Ardour) is GPL ([vestige.h in Ardour](https://raw.githubusercontent.com/Ardour/ardour/master/libs/ardour/ardour/vestige/vestige.h)); FST is GPL v3 and says products built with it may not be called "VST" ([FST](https://git.iem.at/zmoelnig/FST)); Xaymar's vst2sdk is BSD and says "ask a lawyer first anyway" ([vst2sdk](https://github.com/Xaymar/vst2sdk)). GPL headers would force AudioLab's source open; only the BSD one fits a closed app.
  - The limits: none of these has been tested in court as far as we found. The word "VST" and the logo cannot be used for that part. The risk is a letter from Steinberg, and it is yours to weigh; this is not legal advice.
  - How much it matters: Steinberg's own Cubase cannot load VST2 at all when it runs natively on Apple Silicon ([Steinberg help](https://helpcenter.steinberg.de/hc/en-us/articles/22554401894162)). VST2 plug-ins built for Apple Silicon exist (Valhalla and TAL ship them), but the old plug-ins people keep VST2 for are mostly Intel-only, and those need the Rosetta helper as well.
  - So VST2 is last in the order: after the helper process exists, on the clean-room header, named "legacy plug-ins" in the app, and only if your answers on the pick page say you own plug-ins that need it.

### 6.11 Licence notes for the plug-ins used in tests

- **Surge XT** is GPLv3 and is downloaded by the workflow from its official releases ([releases-xt](https://github.com/surge-synthesizer/releases-xt/releases)). A closed host may load a GPL plug-in when the two are separate works; the FSF's own text draws the line at whether they form "a single combined program" ([GPL FAQ](https://www.gnu.org/licenses/old-licenses/gpl-2.0-faq)). Closed hosts load GPL plug-ins as a matter of routine. The careful line, which this plan keeps: AudioLab never ships a GPL plug-in inside itself.
- **Vital** needs an account and its terms forbid automated requests ([Vital EULA](https://vital.audio/eula)); **Valhalla Supermassive** and **TAL-NoiseMaker** are free but their terms do not say a build machine may fetch them. So the build machine tests with Surge XT and Steinberg's example plug-ins, and Vital, Valhalla and TAL are tested on your Mac with the test app, where you installed them yourself. All three ship for Apple Silicon.

### 6.12 Which route makes hosting easiest

- **Route A** (Swift): VST3 is a C++ interface; Swift needs a C++ layer in between anyway.
- **Route B and C** (C++ engine): the SDK is used directly. This is what test B does.
- **Route C specifically:** the plug-ins cannot run in the web engine's audio thread, so their sound has to meet the rest of the mix in the native engine. That is why stage 1 moves the output there first. Until a web-made track has moved, a VST3 effect cannot sit on it.
- **Route D** (JUCE): the least own code for hosting and windows, at the price in section 2.

## 7. Mac distribution without a paid Apple account

- A program built for Apple Silicon is signed "ad hoc" by the build tools; that needs no account. Downloaded, it is stopped once by Gatekeeper. Since macOS 15 the Control-click shortcut is gone ([Apple, August 2024](https://developer.apple.com/news/?id=saqachfa)); the way is System Settings > Privacy & Security > Open Anyway ([Apple support, macOS 15](https://support.apple.com/guide/mac-help/open-a-mac-app-from-an-unknown-developer-mh40616/15.0/mac/15.0), [macOS 26](https://support.apple.com/guide/mac-help/open-a-mac-app-from-an-unknown-developer-mh40616/26/mac/26)).
- An app without Apple's "hardened runtime" may load plug-ins signed by anyone. That is the state of the test app.
- With the paid account (US$99 a year, [Apple](https://developer.apple.com/programs/whats-included/?product=WM)) come Developer ID signing and notarisation: no warning for your users. Notarisation requires the hardened runtime ([Apple: hardened runtime](https://developer.apple.com/documentation/xcode/configuring-the-hardened-runtime)), and a host then needs the entitlement that switches off library validation, which exists for exactly this case ([Apple: disable library validation](https://developer.apple.com/documentation/bundleresources/entitlements/com.apple.security.cs.disable-library-validation)).
- **The Mac App Store** requires the sandbox. A sandboxed host loading VST3 plug-ins from the system folders is technically possible only with the user allowing each bundle by hand, and whether App Review accepts it is not known ([Apple forum, September 2026](https://developer.apple.com/forums/thread/845750)). For a plug-in host, direct download is the practical way. Question U2.

## 8. Assumptions written down (you can change each on the pick page)

1. **Instruments and effects** are both wanted.
2. **The first test plug-ins** are well-known free ones. On the build machine: Surge XT (instrument and effect) and Steinberg's examples. On your Mac: whatever you have, and Vital, Valhalla Supermassive and TAL-NoiseMaker if you install them.
3. **A plug-in shows its own window and also gets an AudioLab strip** in the device chain with its main parameters, presets and a meter.
4. **Order of formats after VST3:** Audio Units, then CLAP, then VST2.
5. **Crash protection:** scanning apart always; plug-ins run inside the engine at first, "run apart" per plug-in later.
6. **VST2** last, on a clean-room header, and only if plug-ins you own need it.
7. **Intel-only plug-ins** later, with the same helper process as "run apart".

On the pick page these are P1 to P7. The first three are the scheduling chat's; 4 to 7 are this task's.

## 9. The first tests and their results

Workflow `.github/workflows/native-lab.yml`, run 2 (run id 45933483595, commit 95abd8d), on GitHub's `macos-15` Apple Silicon machine: a virtual Apple M1, macOS 15.8.2, Apple clang 17. It ran twice; both runs passed every step, the first at the first attempt. Full text of the results: `docs/native-lab/results-run-2.md`; the raw files are on the branch `native-lab-results`.

### Test A: Core Audio, and one effect against the web engine

**The effect.** The Bitcrusher (`al-crush`): quantiser, sample-rate reduction with jitter, dither, an input and an output filter, drive, mix. It was chosen because it is small and still uses everything that can go wrong: `Math.pow`, `Math.exp`, `Math.round`, `%`, the seeded random numbers and the zeroing of tiny values.

**The reference.** `tools/native-lab/make_ref.py` opens the real app (v0.223) in headless Chromium 158, builds the device exactly as the app does (`mkFxNode(c,'crush')` in an OfflineAudioContext, the app's own worklet bundle) and renders half a second of a fixed test signal at 48 kHz. Two runs gave the same files. One catch found on the way: the first reference came out equal to the input, because the worklet module had not loaded when rendering started and the device passed sound through untouched; the script now waits for `wlLoad` as the app's own export does. The reference browser is Chromium 158, the desktop app's is Chromium 156; both take `exp` and `pow` from the same library.

**The port.** `native/dsp/al_crush.h`, 100 lines.

| Case | Settings | Native with the Mac's own `pow` and `exp` | Native with the browser's numbers handed over |
|---|---|---|---|
| plain | 6 bit, downsample 3, both filters off (the worklet accepts 0; the dials stop at 200 Hz) | identical, 48,000 of 48,000 samples | identical |
| filter | 8 bit, downsample 2.5, drive 6 dB, mix 70 %, out -3 dB, filters 6 kHz and 9 kHz | identical, 48,000 of 48,000 | identical |
| dither | 5 bit, downsample 4, jitter 30 %, dither 50 %, fold, drive 9 dB | identical, 48,000 of 48,000 | identical |

- **144,000 of 144,000 samples are the same bits as the web engine**, on Apple Silicon. The same holds on Linux x86-64 (checked in this task's own machine).
- **The maths library:** the five numbers the device works out with `pow` and `exp` came out the same bits from the Mac's library as from the browser, in all three cases. That is true for these numbers, not a promise for all; the plan to carry the browser's maths functions inside the engine stands.
- **Fused multiply-add:** the same program built with fusing allowed gave the same bits here too. So for this device the flag made no difference with this compiler. It stays a rule, because one device is not all devices and a later compiler may choose differently.
- **Speed:** the native Bitcrusher renders about 2,400 to 3,900 times faster than real time on one core of the build machine (2,400 with jitter and dither on). That is one stereo effect at about 0.03 to 0.04 % of one core. No like-for-like figure for the worklet exists yet.

**Core Audio** (`native/common/coreaudio.cpp`, straight on the HAL):

- **Devices listed** with sample rates, buffer range, format on the wire, and whether the device has a volume the computer can set. The build machine has "Apple Virtual Sound Device" (48 and 96 kHz, buffer 15 to 4096 frames, a settable main volume, 32-bit float) and "Null Audio Device"; the workflow adds the virtual device BlackHole (13 rates from 8 to 768 kHz).
- **Default output opened** with an IOProc on the device, and the Bitcrusher's output played for one second: 832 callbacks of 64 frames.
- **Buffer:** asked for 64 frames, the device ran 64.
- **Sample rate:** asked for 96 kHz, the device switched to 96 kHz; put back to 48 kHz.
- **Exclusive use (hog mode):** taken and given back.
- The same four on BlackHole: all worked, 0 overloads.
- **Not clean:** on the default device the system reported 6 overloads in that second (1 in the first run). The buffer had just been changed to 64 frames on a shared virtual machine with no real sound card; the render itself took 0.7 microseconds per callback. Whether 64 and 32 frames run clean is a question for your Mac.
- **Not shown:** anything about real hardware. The virtual devices say yes to everything. Whether the iFi Gryphon offers a volume the computer can set (many USB DACs do not), which formats it offers, and how the AMS-24 behaves at 32 frames, only the test app on your Mac can say; its report lists exactly these.

### Test B: the command line VST3 host

`native/host/` (`plugin_api.h` 99 lines, `vst3_format.cpp` 382, `scan.cpp` 139, `cli.cpp` 224), on Steinberg's SDK 3.8.1.

**Scan.** 6 bundles: Surge XT and Surge XT Effects (downloaded by the workflow from Surge's official releases, version 1.3.4, GPLv3) and four example plug-ins built from Steinberg's SDK. Each bundle was loaded in a child process. One (`adelay`) was made to crash on purpose while loading: the scan reported "crashed while loading (signal 6)" for it, read the other 5 (40 plug-ins in them) and the host stayed alive. A scan takes 0.01 to 0.04 s per bundle.

**Per plug-in** (48 kHz, 128 frames, 4 seconds; notes for instruments, the test signal for effects):

| Plug-in | Loaded | Parameters | Sound | Time per block, average | State saved and restored | Two fresh copies the same? | Export against real time | 96 kHz, 32 frames |
|---|---|---|---|---|---|---|---|---|
| Surge XT (instrument) | 44 ms | 2,855 (774 automatable) | -5.5 dB peak | 19.4 µs = 0.73 % | yes, 50,251 bytes | no, differ by up to -7.6 dB | differs, -7.5 dB | ok |
| Surge XT Effects | 25 ms | 14 | -2.6 dB | 4.2 µs = 0.16 % | yes, 1,044 bytes | identical | identical | ok |
| mda JX10 (instrument) | 28 ms | 31 | -5.3 dB | 2.7 µs = 0.10 % | yes, 8,088 bytes | identical | identical | ok |
| Note Expression Synth (instrument) | 3 ms | 18 | -14.9 dB | 2.3 µs = 0.09 % | yes, 129 bytes | no, -41.4 dB | differs, -42.2 dB | ok |
| ADelay (effect) | 13 ms | 2 | -1.4 dB | 0.4 µs = 0.01 % | yes, 20 bytes | identical | identical | ok |
| AGain (effect) | 4 ms | 3 | -1.4 dB | 0.5 µs = 0.02 % | yes, 281 bytes | identical | identical | ok |

- For every plug-in a changed setting was saved, restored into a new copy and read back with the new value.
- 0 failed blocks in every render.
- **Surge XT is not the same twice.** Two fresh copies playing the same notes differ sample against sample by up to -7.6 dB (they sound the same; the oscillators start at other points). This is the measured case behind section 6.9. Steinberg's Note Expression Synth differs too, at -41 dB. The others are identical every time, also between real time and export mode.
- **Worst blocks.** Surge XT's slowest single block took 4.4 ms, more than the 2.7 ms a 128-frame block lasts; its 99th percentile is 27 µs. The slow one is the first block (the plug-in sets itself up), on a shared machine. In a real engine a plug-in is warmed up before it joins the audio thread. Worth watching on your Mac, where the report shows the worst block too.
- **Not tested here:** a plug-in with latency (all six report 0), side-chain buses, automation curves inside a block (single changes only), plug-ins that need a licence dongle or an online check, and any paid plug-in.

### Test C: the test app

`native/testapp/main.mm` (439 lines, AppKit). Built, signed ad hoc (no Apple account), zipped: 140 KB. Its scanner is the same child-process scanner as in test B; its output is the same Core Audio stream as in test A.

The workflow started it on the build machine with nobody to click: it listed the 4 audio devices, opened the default output at 48 kHz and 512 frames, found Surge XT and Surge XT Effects, loaded Surge XT in 36 ms, opened Surge XT's own window (913 × 569), played the test pattern for five seconds (1,160 blocks, average 115 µs per block = 1.1 % of the block, 0 failed, 0 overloads), wrote the report and quit. A screenshot from the first run shows both windows: `docs/native-lab/test-app-on-build-machine.png`. In that picture the plug-in window ran off the small screen and the key hint was cut; both were fixed before the published build, and that fix has not been looked at in a picture.

**Not verified:** anything a hand does. Clicking the list, the keyboard notes, the Buffer menu, changing the device while a plug-in plays, moving a control in the plug-in's window, and every plug-in other than Surge XT. That is your test.

### What could not run at all

- No test on real audio hardware, and none on an M4.
- No latency measurement (needs a cable from output to input).
- Vital, Valhalla Supermassive and TAL-NoiseMaker were not installed on the build machine, for the licence reasons in section 6.11.
- Nothing on Windows.

## 10. The test app on your Mac

**Download:** https://github.com/Audio-lab-DAW/Audio-Lab-Pro-Alpha/releases/tag/native-lab-1 (file `AudioLab-VST3-test-mac-arm64.zip`). It is a pre-release and is not marked as the latest release, so the desktop app's download page and updater still point at AudioLab Pro 0.223.0. The workflow can build it again at any time (start "Native lab" by hand with "release" ticked).

It is not the AudioLab app. Apple Silicon, macOS 12 or later.

**Opening it** (it has no Apple signature, so macOS asks once):
1. Double-click the zip, then the app. macOS says it cannot check it. Click Done.
2. System Settings > Privacy & Security, scroll to Security, click Open Anyway next to the app's name, then Open Anyway again, and enter your password. The button is there for about an hour after step 1.
3. If the button does not appear: in Terminal, `xattr -dr com.apple.quarantine "/path/to/AudioLab VST3 test.app"`.

**Using it:**
1. The list shows every VST3 found in `/Library/Audio/Plug-Ins/VST3` and in your own `Library/Audio/Plug-Ins/VST3`. Lines that start with PROBLEM could not be read, with the reason (for example "built for x86_64 only").
2. Pick the output at the top (Gryphon, AMS-24). Try Buffer 64 and 32.
3. Click a plug-in, Load, "Open its window", "Play test pattern", or play the keys A W S E D F T G Y H U J K. An effect gets a plucked test sound to work on. Sound is at half level and never above full scale.
4. "Copy report", paste it into the chat. The same text is in `AudioLab-VST3-test-report.txt` on your Desktop.

**What the report holds:** Mac model and macOS version; every audio device with its rates, buffer range, format on the wire, whether it has a volume the computer can set and whether exclusive use can be taken; every plug-in found or failed and why; what loaded, how long it took, parameters, state size, latency; the time per block (average and worst), failed blocks, overloads, buffer size. Nothing is sent anywhere.

## 11. What happens next

Nothing is built further until you have answered the pick page. The picks line there looks like `NM1 picks: R1c R2b R3a R4a R5a R6a | P1a P2a P3a P4a P5a P6a P7a | U1b U2a U4abcd U5a | U3: your plug-ins`. If you only do one thing: run the test app with your DAC and your plug-ins and paste the report. It answers more than any question can.

## 12. Files

| File | What |
|---|---|
| `docs/native-mac-plan.md` | this document |
| `native/dsp/al_crush.h` | the Bitcrusher port |
| `native/common/coreaudio.*` | Core Audio device list and output stream |
| `native/alnative/main.cpp` | test A program |
| `native/host/plugin_api.h` | the plug-in interface, no format named |
| `native/host/vst3_format.cpp`, `scan.cpp`, `cli.cpp` | VST3 behind it, the scanner, test B program |
| `native/testapp/` | test C, the app |
| `tools/native-lab/make_ref.py`, `ref/` | the web engine's reference renders of the Bitcrusher (made by the real app in headless Chromium) |
| `tools/native-lab/run_a.py`, `summary.py` | test drivers |
| `tools/native-lab/pick-page.html` | the pick page source |
| `.github/workflows/native-lab.yml` | the workflow, started by hand |
| `docs/native-lab/results-run-2.md`, `test-app-on-build-machine.png` | the results as text, and the screenshot |
| branch `native-lab-results` | the raw results of the last run |
