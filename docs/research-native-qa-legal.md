# Native apps: testing, licensing and distribution (task RN6)

Research for the native AudioLab (Mac first, then Windows), written 27 November 2026. Companion tasks: RN1 and RN2 (how to build the engine), RN3 (lessons from other DAWs), RN4 (the interface technology), RN5 (code review). This one covers the three areas that tend to surprise teams late: **testing, licences, and getting the app onto other people's computers and keeping it updated**.

> **This is research, not legal advice.** It sums up licence texts, terms pages and court decisions as they read on the dates given. Before anything is sold, or if anyone complains, ask a lawyer (in Belgium: a lawyer for intellectual property and data protection).

Labels used below: **[checked]** read on an official page or in this repository on 27 Nov 2026; **[search]** the page was found and its title/summary says this, but the full text was not read; **[memory]** from the researcher's knowledge (to mid-2026), not re-checked; **[guess]** an inference. Several research helpers ran out of page reads during this task, so the [memory] items are listed again in section 8 for checking.

---

## 1. Summary

### The one most important finding: AudioLab ships someone else's recording
The start-up song (`DEMO_FRACTALS`, embedded in `index.html` since v0.220, plus `vox/fractals_vox_01..10.wav` in the public repo) contains the audio track **"Vocals (original)"**: ten vocal samples cut out of Electric Universe's commercial track "Fractals" (album *Sacred Geometry*, 2022) with a stem splitter [checked: project docs `claude/reference-analysis-fractals.md`, `claude/audiolab-fixes-run-AI.md`]. That audio is protected twice: the recording (producer's neighbouring right, 70 years from publication, Directive 2011/77/EU) and the vocal performance (performer's right). Splitting it out with Demucs does not change that. It is already distributed today (the public repository, the GitHub Pages site and every desktop release since v0.220), and the picks (U5b) plan to make Fractals v10 the fresh-install song of the first native build.

- **This is a legal blocker for a public native build** and, strictly, a problem already. Fix: take the original vocals out of everything that is shipped or public (the app, the `vox/` folder, and, if the repo stays public, ideally its history), or get written permission from the rights holders (the artist and the label, Sacred Technology). Replace them with vocals the user records, commissions or takes from a source that allows redistribution (CC0, or a sample licence that explicitly allows bundling in software, which most do **not**).
- The remakes from v7 on also take riffs and bass lines transcribed from the original's stems. A melody or riff can be protected as part of the composition (life of the author + 70 years). The v6 song that ships today was "composed from the psytrance rules" with only the section plan and the vocals from the original [checked: project docs], so its notes are probably fine; **v7 to v10 should not become the shipped demo** without permission or rewritten parts. [guess, ask a lawyer before shipping a remake of any kind]

### Must be done before the first public native build
1. **Remove the third-party vocals** (above).
2. **A third-party notices page** in the app and a `THIRD-PARTY-NOTICES` file in the bundle: Electron and Chromium (`LICENSES.chromium.html`), onnxruntime (`ThirdPartyNotices`), the VST3 SDK (MIT), OpenVoice V2 (MIT), HT-Demucs ONNX (MIT), lamejs (**LGPL-3.0**), Inter (SIL OFL 1.1). Today there is no such page and no notices file in the repo [checked].
3. **Stop silent calls to third parties.** The page loads Inter from Google Fonts and lamejs and onnxruntime-web from jsDelivr at run time [checked: `index.html`]. A German court fined a site for sending visitors' IP addresses to Google Fonts without consent (LG München I, 20 Jan 2022, 3 O 17493/20, EUR 100) [checked: law-firm summary]. Bundle the font and the libraries inside the app instead (the OFL and the LGPL both allow this, with notices). Hugging Face model downloads are started by the user and can stay, with a line in the privacy notice.
4. **Sign the in-app program update.** The desktop app downloads `index.html` (the whole program, which talks to the native engine and the disk) and checks it only against a sha256 that comes from the same place [checked: `desktop/main.js` lines 398-413]. Anyone who can push to the repo, or who gets a token, can ship code to every installed app. The Ed25519 signature in `docs/update-feed-plan.md` section 5.4 must land before a native build reaches other people, and the native engine and its updates must be covered by the same key.
5. **A short privacy notice** (who you are, what the update check sends, crash reports off unless the user turns them on, model downloads from Hugging Face, the right to complain to the Belgian Data Protection Authority).
6. **The minimum native test set**: a headless render with golden files and null tests against the web engine; address/undefined-behaviour and thread sanitizer jobs; RealtimeSanitizer on the audio path; a fuzzer on the project loader; plug-in scanning in its own process (already done in stage 0) and crash recovery (done in NB-N2b).
7. **Mac without an Apple account (U1c):** a stable self-signed identity instead of a new ad-hoc one each build, so macOS does not ask for the microphone again after every update (test it); detect App Translocation and say "move AudioLab to Applications"; a download page with the "Open Anyway" steps.

### Can wait
- **Apple Developer Program** (99 USD a year [checked]; about 99 EUR with VAT in Belgium [guess]): needed for notarisation and the normal Mac updater. The user chose to wait (U1c). Section 5.2 says what to do on the day it is bought.
- **Windows signing.** Azure Artifact Signing (9.99 USD a month) is open to EU **organisations** but to individuals only in the US and Canada [checked: Microsoft quickstart, updated 20 Nov 2026]. As a Belgian individual: a standard OV certificate (about EUR 100-250 a year [guess]) or ship unsigned with "Run anyway" instructions. Certum's EUR 49 "Open Source Developer" certificate [checked] is for software shared as open source, which AudioLab (licence "UNLICENSED", `desktop/package.json`) is not.
- **Crash reporting service** (opt-in Sentry in the EU region, or local crash files the user can send): useful once others use it, not needed for the user's own Mac.
- **Audio Units, CLAP, ARA, AAX** licences: none blocks anything; see section 4.
- **EU Cyber Resilience Act:** a free app from a natural person is outside its scope; it matters from 11 Dec 2027 if AudioLab is ever sold [checked: summary of the Commission guidance].
- Long soak tests and performance tracking on a fixed machine.

### Legal blockers, in one list
| Blocker | Where | Way out |
|---|---|---|
| Electric Universe vocals (and transcribed riffs in v7+) | shipped today; planned for native (U5b) | remove, or written permission |
| ASIO on Windows | Windows stage only | sign Steinberg's ASIO agreement (allow weeks) or ship WASAPI only; the GPLv3 option only if AudioLab itself becomes GPLv3 |
| VST2 hosting | only if ever added (P6a) | Steinberg gives no new VST2 licences since 2018: do not add it without an old licence |
| AAX hosting | never planned | not possible for third-party hosts |
| Third-party voice models for the voice feature | if anyone wants to bundle community RVC voices | never bundle them; the shipped OpenVoice V2 is MIT |

---

## 2. What AudioLab has today (from the repository, 27 Nov 2026)

| Area | What is there | Where |
|---|---|---|
| Desktop shell | Electron 45.4.1, electron-builder 25, electron-updater ^6.3.9 (6.8.11 is the newest on npm today) | `desktop/package.json` |
| Mac build | arm64 DMG, `identity: null`, ad-hoc signed in `afterPack.js`, hardened runtime off, `NSMicrophoneUsageDescription` set; no updater on Mac (opens the Releases page) | `desktop/package.json`, `docs/update-feed-plan.md` |
| Windows build | NSIS, per-user (`perMachine: false`), unsigned, electron-updater from GitHub Releases | `desktop/package.json` |
| Program updates | `index.html` downloaded from GitHub, sha256 from the same feed, no signature | `desktop/main.js` 398-413 |
| Native work | `alengine` (Core Audio engine helper), `alnative` (VST3 host, scanner, test app), bridge in Node | `native/` |
| Native CI | macOS 15 Apple Silicon runners; BlackHole installed with Homebrew and used as loop-back (works on the hosted runner, proven in run 45939789700); VST3 SDK **v3.8.1_build_84 (MIT)**; Surge XT 1.3.4 downloaded for tests, not redistributed; scan in a separate process; bit-for-bit test of the Bitcrusher against the web engine; crash recovery test (case D) | `.github/workflows/native-lab.yml`, `native-engine.yml` |
| Web engine tests | `tools/engine-tests/export_same.py` checksums (Kick, Bass, Saw, Pad, Acid, Wavetable, Venom; Plant, Samplers and Drum kit differ every load) | `tools/engine-tests/` |
| AI models | HT-Demucs 4- and 6-stem ONNX (StemSplitio, MIT) fetched from Hugging Face in the page; OpenVoice V2 converter (MyShell, MIT; ONNX fp16 by moonbox-dev) fetched at a pinned revision with sha256 per file in the desktop app; onnxruntime-node 1.31.1 (MIT) bundled; onnxruntime-web 1.20.1 (MIT) from jsDelivr | `index.html`, `desktop/voice-ai*.js` |

---

## 3. Testing a native audio engine and host

### 3.1 Golden renders, null tests, tolerances
- [ ] **A headless render command** for the engine (project in, 32-bit float file out) running on a null device driven by a clock, so no sound card is needed. This one tool carries most of the tests below. (The engine's `selftest` and Test A already work this way for one effect.)
- [ ] **Deterministic mode**: fixed random seeds, dither off, flush-denormals set explicitly on the render thread, a fixed order for summing tracks. Today Plant, the Samplers and the Drum kit render differently on every load in the web engine [checked]; the native engine should not inherit that.
- [ ] **Three levels**: (1) bit-exact hash per platform (macOS arm64 now, Windows x64 later; never compare hashes across CPUs); (2) null test against the reference (subtract, fail above about -120 dBFS peak; -140 for plain gain and mixing, -100 for long feedback filters) [guess: community practice, not a standard]; (3) ULP comparison for single DSP kernels.
- [ ] **Invariance renders**: the same project at block sizes 32, 64, 256, 512 and an odd one (37) must null; realtime against offline must null.
- [ ] **Web engine against native engine**, device by device, as each device is ported (stage N3): the Bitcrusher test is the model.
- [ ] Compiler flags: no `-ffast-math` in the engine; consider `-ffp-contract=off` for golden builds (Clang fuses multiply-add on arm64 by default, which changes the last bits) [memory].
- [ ] Golden files change only through a script and a reviewed commit.

Sources: [Infinum, snapshot testing for audio DSP](https://infinum.com/blog/snapshot-testing-for-audio-dsp/) [search]; [HART DSP testing cookbook](https://daleonov.github.io/HART/DSPTestingCookbook.html) [search]; [Ardour's command-line exporter](https://manpages.ubuntu.com/manpages/lunar/man1/ardour7-export.1.html) [search].

### 3.2 Property tests and fuzzing
- [ ] **libFuzzer** harness for the project loader (`.audiolab` JSON), WAV/FLAC/MIDI import and the engine's JSON-lines protocol: `clang++ -fsanitize=fuzzer,address,undefined`. Runs on Linux runners; on macOS use Homebrew LLVM [memory]. Every crash input becomes a regression test.
- [ ] **ClusterFuzzLite** (OSS-Fuzz style fuzzing inside GitHub Actions; a few minutes per change, longer at night). OSS-Fuzz itself takes only widely used open-source projects [search].
- [ ] **RapidCheck** (C++, BSD-2) for engine properties: load(save(p)) = p; gain 0 gives silence; automation never yields NaN or Inf; transport never runs backwards [memory].
- [ ] **fast-check** (JS, MIT) on the page side: round trip of project files, random JSON never crashes the loader.
- [ ] Treat project files as untrusted: size and depth limits, schema check.

### 3.3 Sanitizers
- [ ] **RealtimeSanitizer (RTSan)**: mark the audio callback and every `process()` path `[[clang::nonblocking]]`, build with `-fsanitize=realtime`; it stops on `malloc`, locks or file access inside them. Suppress third-party plug-ins with `__rtsan::ScopedDisabler` around their `process` call, so AudioLab's own code is held strictly. Turn on `-Wfunction-effects` too (the same check at compile time). [checked: clang docs page]. First released in LLVM 20 (March 2025) [memory]; **Apple's Xcode clang does not appear to have it** (an Apple forums thread asks for it) [search], so use Homebrew LLVM in a separate test build.
- [ ] **AddressSanitizer + UndefinedBehaviorSanitizer** job and a separate **ThreadSanitizer** job on macOS (Apple clang has both) and Linux [memory]. TSan reports false alarms on lock-free rings that use relaxed atomics with fences; fix with proper atomics, suppress the rest.
- [ ] Windows later: MSVC has `/fsanitize=address` only (no TSan, no UBSan) [search: Microsoft Learn].
- [ ] Sanitized builds run 2 to 15 times slower: use them on offline renders, not live device tests. Never put ASan into the Electron process.

Sources: [Clang RealtimeSanitizer](https://clang.llvm.org/docs/RealtimeSanitizer.html) [checked]; [LLVM 20.1.0 release notes](https://releases.llvm.org/20.1.0/docs/ReleaseNotes.html) [search]; [Apple forums: RTSan in Apple Clang](https://developer.apple.com/forums/thread/807360) [search]; [MSVC ASan known issues](https://learn.microsoft.com/en-us/cpp/sanitizers/asan-known-issues) [search].

### 3.4 Plug-in compatibility
- [ ] **pluginval** (Tracktion, GPLv3, using it as a tool is fine): checks plug-ins, not hosts; `--strictness-level 5` is the accepted minimum; exit code 0/1 for CI [checked: README]. Useful to know what plug-ins expect from a host, and to test any plug-in AudioLab ships itself.
- [ ] **Steinberg's `validator`**, built from the VST3 SDK (`--target validator`) [search]; the SDK's EditorHost/AudioHost examples are reference hosts.
- [ ] `auval -v <type> <subtype> <maker>` for AU; `clap-validator validate` for CLAP (MIT) [memory].
- [ ] **A nightly matrix** of free plug-ins with pinned versions and checksums (Surge XT already used; add Dexed, Odin 2, Vitalium, Airwindows, Dragonfly Reverb; all GPL or MIT) [memory: check each licence]. Per plug-in: scan, load, play 10 s, save and restore state, null against the previous night's render. Keep the binaries in the Actions cache or download them; never publish them in a release. Loading a GPL plug-in in a test does not make AudioLab GPL [guess, not legal advice].
- [ ] Commercial plug-ins (the U3 list: FabFilter, Ozone, Kontakt, Serum 2, Melodyne...) can only be tested on the user's Mac: keep a written checklist per release (load, window, latency report, state size, delay compensation) as in the picks reports.

Sources: [pluginval README](https://raw.githubusercontent.com/Tracktion/pluginval/develop/README.md) [checked]; [VST3 validator](https://steinbergmedia.github.io/vst3_dev_portal/pages/What+is+the+VST+3+SDK/Validator.html) [search]; [clap-validator](https://github.com/robbert-vdh/clap-validator) [search].

### 3.5 Devices on CI
- [x] **macOS**: BlackHole 2ch installs with Homebrew on the hosted Apple Silicon runner and works as a loop-back (this project's own runs prove it). BlackHole is GPL-3.0: fine on a test machine, not to be bundled with AudioLab [checked: README].
- [ ] Keep 95 % of tests on the null device; BlackHole only for the hand-over and device-control tests.
- [ ] **Windows** hosted runners have no audio endpoint [memory]; virtual cards (Scream, VB-CABLE) are fragile there. Plan a self-hosted Windows PC (or the user's) for WASAPI and ASIO tests [guess].
- [ ] Linux (if ever): JACK dummy backend or a PipeWire null sink.

### 3.6 Soak and performance
- [ ] **Soak**: 1 to 8 hours on a real Mac (the user's M4 overnight, or a Mac mini), logging memory, failed blocks, overloads, worst block time and thread count each minute. Fail on memory growth after warm-up or any failed block at 256 frames [guess: thresholds to tune]. Hosted runners stop at 6 hours and are noisy.
- [ ] **Benchmarks** with Google Benchmark per device and per graph; on pull requests compare old and new in the same job (shared runners vary by 5-20 % [guess]); keep history with github-action-benchmark or Bencher.
- [ ] The figures in the picks reports (time per block, worst block at 32 frames) become the baseline numbers.

### 3.7 Crash reports and privacy
- [ ] Electron already contains **Crashpad** (`crashReporter`); for the native engine use **sentry-native** (Crashpad inside) or Crashpad directly [memory]. PLCrashReporter is Apple-only and its future after App Center's end is unclear [memory].
- [ ] A minidump holds stacks, registers, loaded modules with full paths (`/Users/<name>/...`, so the user's name), and pieces of memory (project names, audio) [memory]. So: **off until the user turns it on**, small dumps only, paths scrubbed, never attach project files, keep 90 days at most.
- [ ] If Sentry: create the organisation in the **EU (Germany) data region** (cannot be changed later) and accept its data processing agreement [search: Sentry docs]. Check the free plan's limits on sentry.io/pricing (not read).
- [ ] Simplest first step: the engine writes its own crash file locally and the app offers "copy crash report" for the user to paste, as with the test-app reports today.

### 3.8 Beta channel
- [ ] A **beta** feed next to stable, a switch in Settings, and later a separate app id so a beta can sit next to the stable app [memory: Bitwig and REAPER do public betas].
- [ ] A **project-format version** in each file: an older app refuses or warns on a file saved by a newer beta.
- [ ] Staged rollout (10 %, 50 %, 100 %) once there are users: electron-updater's `stagingPercentage`, Sparkle's phased rollout [search].

---

## 4. Licensing

### 4.1 Plug-in and driver SDKs
| SDK | Licence today | What AudioLab must do | Blocker? |
|---|---|---|---|
| **VST3 SDK** 3.8+ | **MIT** since 3.8.0 (29 Oct 2025); VSTGUI and the mda examples BSD-style. The old GPLv3/proprietary choice and the signed agreement are gone [checked: Steinberg portal and press release] | Keep the MIT notice. AudioLab already builds against v3.8.1 | No |
| VST name and logo | Trademark. Optional. If used: follow the "Steinberg VST Usage Guidelines": ® on first use, the line "VST is a registered trademark of Steinberg Media Technologies GmbH", logo at its minimum size; never "VST" in the product name or brand style [checked] | Writing "hosts VST3 plug-ins" with the trademark line is enough | No |
| **VST2** | Proprietary; no new licences since October 2018; the headers may not be redistributed; MIT VST3 did not change this [checked]. Clean-room headers (VeSTige, FST) exist but carry legal risk and FST is GPL [memory] | Do not add VST2 (P6a puts it last anyway) | **Yes** |
| **ASIO SDK** 2.3.4 | Dual since October 2025: Steinberg's proprietary agreement **or GPLv3** [checked: SDK licence text, press releases] | A closed-source Windows app must **sign the ASIO agreement**; forum reports in 2026 speak of slow answers and doubts about signing as an individual [search]. Do not commit the SDK to a public repo; fetch it at build time. WASAPI needs no licence | **Yes, for ASIO on Windows** |
| Audio Units | Part of macOS; only the Xcode/SDK terms apply. Apple's AudioUnitSDK is Apache-2.0 [memory] | Nothing extra for hosting | No |
| **CLAP** | MIT (also clap-helpers, clap-wrapper) [memory] | MIT notice | No |
| **ARA** (for Melodyne) | Apache-2.0 since ARA 2.2 [memory] | Apache licence and NOTICE; "ARA" and "Melodyne" are Celemony trademarks | No |
| AAX | Avid's SDK is for plug-ins in Avid hosts; third-party hosting is not offered [memory] | Nothing | Not relevant |
| JUCE 8 (fallback, R3a) | AGPLv3 or commercial EULA (Starter, Indie, Pro). 2024 discussion: Starter free up to about USD 20k revenue, Indie limit about 200k, Pro about USD 3,500 perpetual; the forum now links a "JUCE 9 EULA" [search: forum thread 24 Apr 2024; current prices **not** confirmed] | Check juce.com before choosing; AudioLab's own code avoids the question | No, a choice |

### 4.2 Shell and libraries
| Component | Licence | Duty |
|---|---|---|
| Electron 45 | MIT [checked: npm] | Keep `LICENSE` |
| Chromium (inside Electron) | BSD-3 plus hundreds of others | Ship `LICENSES.chromium.html` (Electron's download has it; check it ends up in the built DMG and Windows folder) [memory] |
| Electron's ffmpeg | LGPL, built with proprietary codecs (H.264, AAC); a build without them exists [memory] | Dynamic library, notice; codec patents are a separate, small risk in the EU [guess] |
| LGPL libraries in a native build (libsndfile, SoundTouch, LAME) | LGPL-2.1/3.0 | Link dynamically, ship licence and source (or written offer), let users replace the library. With the hardened runtime this needs `disable-library-validation`, which a host has anyway [memory] |
| Rubber Band | GPL or paid commercial licence | Avoid in closed source unless bought |
| libsamplerate, r8brain, miniaudio, RtAudio, PortAudio, nlohmann/json, Sparkle | BSD-2, MIT, public domain/MIT-0, MIT-like | Notices (RtAudio and PortAudio with ASIO still need the ASIO licence) |

### 4.3 The licence audit: what AudioLab ships today
| Item | Where | How it reaches the user | Licence | What it requires | Status |
|---|---|---|---|---|---|
| **"Vocals (original)": 10 samples from Electric Universe, "Fractals" (2022)** | FLAC in `index.html` (`DEMO_FRACTALS`), WAV in `vox/` | in every copy of the page and app | **none; copyrighted recording and performance** | permission, or removal | **Blocker** |
| Fractals remake v6 project (notes, sounds, mix) | `index.html` | in every copy | AudioLab's own; section plan from the original | probably fine (form and structure are not protected alone) [guess] | OK; v7+ (transcribed riffs) not OK without permission |
| Inter font | Google Fonts CSS at run time | fetched from Google on every start | SIL OFL 1.1 | bundle `OFL.txt` when bundled; the run-time fetch sends the user's IP to Google | **Change**: bundle locally |
| lamejs 1.2.1 (MP3 export) | jsDelivr at run time | fetched when exporting MP3 | **LGPL-3.0** [checked: npm] | LGPL notice; if bundled, keep it a separate replaceable file with its source link | Change: bundle as a separate file plus notice |
| onnxruntime-web 1.20.1 | jsDelivr at run time | fetched for the stem splitter | MIT [checked: npm] | notice, plus its third-party notices | Change: bundle locally |
| onnxruntime-node 1.31.1 | `desktop/node_modules` | inside the desktop app | MIT [checked: npm] | ship `ThirdPartyNotices.txt` | Add notice |
| HT-Demucs 4 and 6 stems, ONNX fp16 (StemSplitio) | Hugging Face, downloaded on first use | user-triggered download | MIT, "matching the original HT-Demucs" [checked: model cards] | notice; Meta's code is MIT. The training data (MUSDB18-HQ plus Meta's own) is a theoretical question the licence does not raise [guess] | Add notice |
| OpenVoice V2 converter (MyShell), ONNX by moonbox-dev | Hugging Face, pinned revision, sha256 per file | user-triggered download | MIT (both) [checked: code comment; project voice research] | notice | Add notice |
| Electron, Chromium, electron-updater | desktop app | inside | MIT; BSD and others | `LICENSE`, `LICENSES.chromium.html` | Check they are in the build |
| VST3 SDK 3.8.1 | `native/` builds (test app, engine) | inside the native test app | MIT, VSTGUI BSD | notice in the app | Add notice |
| BlackHole, Surge XT | CI only | not distributed | GPL-3.0 | nothing while they stay out of releases | OK |
| Icons, logo, app icon, glass art | `desktop/icon-assets`, docs | inside | AudioLab's own (made in this project) | none | OK |
| Factory presets of AudioLab devices | `index.html` | inside | AudioLab's own (designed from research, not copied) [checked: `docs/preset-research.md` describes counts and categories of other synths, not their data] | keep it that way: never import a third-party preset bank | OK |
| AudioLab itself | repo | public repo, licence "UNLICENSED" | all rights reserved | add a short licence line and a `LICENSE` file so visitors know the code is not open source [guess] | Decide |

### 4.4 Songs, presets and samples in general
- Any **song** shipped as a demo needs a written licence for the composition and the recording that covers bundling in software. The user's own music, or music made for AudioLab with a written agreement, is the safe road. Belgian law (Code of Economic Law, Book XI) does not let authors waive moral rights wholesale, so put the credit and "may be edited by users" in the agreement [memory].
- **Sample packs** almost always allow use inside your own music but forbid redistributing the samples, alone or inside software [memory]. Do not put pack samples into the Sampler's library or the drum kit.
- **Presets** of commercial synths: whether a preset is protected is unclear, but pack licences forbid redistribution; AudioLab's own devices only use AudioLab's own presets.
- If the user ever trains models on music, the EU text-and-data-mining opt-out (Directive 2019/790, Article 4) applies [memory].

Sources: [VST3 licence](https://steinbergmedia.github.io/vst3_dev_portal/pages/VST+3+Licensing/VST3+License.html) [checked]; [Which files fall under which licence](https://steinbergmedia.github.io/vst3_dev_portal/pages/VST+3+Licensing/Which+files+fall+under+which+license.html) [checked]; [VST usage guidelines](https://steinbergmedia.github.io/vst3_dev_portal/pages/VST+3+Licensing/Usage+guidelines.html) [checked]; [heise on ASIO GPLv3](https://www.heise.de/-10963451) [checked]; Libre Arts, 4 Nov 2025 (librearts.org) [search]; [JUCE tier thread](https://forum.juce.com/t/revenue-limits-for-juce-tiers/61058) [checked, 2024]; [StemSplitio HT-Demucs ONNX](https://huggingface.co/StemSplitio/htdemucs-onnx) [checked]; [6-stem](https://huggingface.co/StemSplitio/htdemucs-6s-onnx) [checked]; [lamejs](https://github.com/zhuker/lamejs) [checked via npm metadata]; [LG München I on Google Fonts, summary](https://www.activemind.legal/guides/ruling-google-fonts/) [checked]; [the judgment](https://www.gesetze-bayern.de/Content/Document/Y-300-Z-GRURRS-B-2022-N-612) [search].

---

## 5. Distribution and updates

### 5.1 Mac without a paid Developer ID (the current pick, U1c)
- [x] Since macOS 15, Control-click > Open no longer bypasses Gatekeeper; the user goes to **System Settings > Privacy & Security > Open Anyway** after a first blocked start, enters the password and confirms [checked: Apple, 6 Aug 2024]. The user already does this for the test app.
- [ ] **Quarantine**: downloads carry `com.apple.quarantine`; a copy out of the DMG inherits it. `xattr -dr com.apple.quarantine /Applications/AudioLab.app` removes it; document it as the fallback [memory]. Files the app downloads itself are not quarantined unless the app asks for it [memory].
- [ ] **App Translocation**: a quarantined app started from Downloads or the DMG runs from a random read-only copy; it cannot update itself or find files next to it. Detect it (`SecTranslocateIsTranslocatedURL`) and show "Move AudioLab to Applications" [memory].
- [x] Apple Silicon needs at least an ad-hoc signature; `afterPack.js` does it.
- [ ] **Microphone permission resets**: an ad-hoc signature identifies the app by its exact hash, so every new build looks like a new app to macOS's privacy database and the keychain: the microphone question comes back after each update [memory; Apple forum thread on lost permissions after ad-hoc updates, not read]. **Test a self-signed code-signing certificate** kept by the user (Keychain Access > Certificate Assistant): the identity then stays the same from build to build, so the permission should survive; Gatekeeper still asks for Open Anyway once [guess: test on two builds].
- [ ] **Updating itself**: an ad-hoc app in `/Applications`, not translocated, can download a new bundle, check an Ed25519 signature, replace itself and restart. Electron's own updater (Squirrel.Mac) and electron-updater refuse unsigned apps [memory; already noted in `docs/update-feed-plan.md` 5.3]. **Sparkle 2** works with ad-hoc apps because it checks its own EdDSA signature, but then that key is the only protection [memory]. Today's Mac app updates its page (`index.html`) in place and sends users to the download page for the shell; the native build needs the same for the engine binaries, signed.
- [ ] Keep `NSMicrophoneUsageDescription` (set; its text says it is also used to list output devices, which is true for Electron's device list).

Sources: [Apple: runtime protection in macOS Sequoia](https://developer.apple.com/news/?id=saqachfa) [checked, 6 Aug 2024]; [Eclectic Light, running code that is not notarised](https://eclecticlight.co/2026/08/11/how-can-you-run-code-that-hasnt-been-notarised/) [search, 11 Aug 2026]; [Apple forum 795739](https://developer.apple.com/forums/thread/795739) [search]; [Sparkle discussion 2401](https://github.com/sparkle-project/Sparkle/discussions/2401) [search].

### 5.2 The day the Apple account is bought
- [ ] Enrol as an **individual** (a sole trader must; the name on the certificate is the user's legal name) or as an **organisation** (needs a company such as a BV/SRL, a free D-U-N-S number, a website) [checked: Apple enrolment page]. 99 USD a year [checked].
- [ ] Create a **Developer ID Application** certificate; keep the `.p12` offline and in Actions secrets only for a protected release job.
- [ ] **Hardened runtime on**, and entitlements [memory; Apple forum on allow-jit]:
  - `com.apple.security.device.audio-input` (without it the hardened runtime silences the microphone);
  - `com.apple.security.cs.disable-library-validation` (without it no third-party VST3/AU/CLAP loads; every non-sandboxed host ships it, and notarisation accepts it);
  - `com.apple.security.cs.allow-jit` for Electron (current Electron needs only this; try without `allow-unsigned-executable-memory`); the C++ engine needs neither;
  - not `allow-dyld-environment-variables`.
  - The engine and any plug-in helper process get the same plug-in and audio entitlements as the app (separate entitlement files for Electron's helpers).
- [ ] Sign inside out (no `--deep` for the final signature), notarise with `xcrun notarytool submit --wait` (altool stopped on 1 Nov 2023), staple the DMG, test on a clean Mac with a downloaded copy [checked: TN3147].
- [ ] Do **not** sandbox: a sandboxed host cannot load the user's plug-ins without workarounds [search: Apple forum 845750].
- [ ] Then electron-updater works on Mac (needs a `zip` target next to the DMG); one manual install of the first signed app (planned in `update-feed-plan.md`).

Sources: [Apple enrolment](https://developer.apple.com/help/account/membership/program-enrollment/) [checked]; [TN3147 notarytool](https://developer.apple.com/documentation/technotes/tn3147-migrating-to-the-latest-notarization-tool) [search]; [Hardened runtime](https://developer.apple.com/documentation/security/hardened-runtime) [search]; [allow-jit vs unsigned memory](https://developer.apple.com/forums/thread/776290) [search]; [JUCE forum: code signing for hosts](https://forum.juce.com/t/codesigning-for-plugin-hosts/67474) [search].

### 5.3 Sparkle, if the shell is ever native
- [ ] Latest: **Sparkle 2.10.1** (25 Oct 2026, macOS 12+). 2.9.2, 2.9.5 and 2.9.6 fixed security bugs, so always ship the newest [checked: releases page].
- [ ] `generate_keys` (Ed25519; export the private key once, keep two offline copies), `SUPublicEDKey` in Info.plist, `sign_update`, `generate_appcast` (makes delta updates too), `<sparkle:channel>beta`, phased rollout, `minimumSystemVersion`, `criticalUpdate`. The XPC installer services are only for sandboxed apps; a host does not need them [memory].

### 5.4 Windows
- [ ] **SmartScreen**: unsigned files show "Windows protected your PC" until the file builds reputation; since 2024 an EV certificate no longer skips this [checked: Microsoft Artifact Signing FAQ, 20 Nov 2026; search: ToDesktop]. Any signature at least shows a publisher name.
- [ ] **Signing options for a Belgian developer**:

| Option | Cost | Who | Notes |
|---|---|---|---|
| Unsigned | 0 | anyone | "More info > Run anyway"; electron-updater then checks only the sha512 from the same feed (see 5.5) |
| Azure Artifact Signing Basic | USD 9.99/month (5,000 signatures) | EU **organisations**; individuals only US/Canada | GA about 14 Jan 2026; certificates last a day and renew; built into electron-builder 25.1+ [checked] |
| Standard OV certificate (Certum, SSL.com, others) | about EUR 100-250/year plus a cloud key or token [guess] | individuals too | since 1 Jun 2023 keys must live in hardware or a cloud HSM; from 1 Mar 2026 certificates last at most 460 days [checked: DevClass] |
| Certum Open Source Developer | EUR 49 [checked] | individuals sharing open-source software | not for AudioLab while it is not open source |

- [ ] **Installer**: keep **NSIS per-user** (`%LOCALAPPDATA%\Programs`, no admin prompt, updates itself). Avoid **MSIX** for a plug-in host: it must be signed, its file and registry views are virtualised and plug-ins' own licensing tools break [memory; search: JUCE forum].
- [ ] **Plug-in folders**: `C:\Program Files\Common Files\VST3` and the per-user `%LOCALAPPDATA%\Programs\Common\VST3`; CLAP in `Common Files\CLAP` and `%LOCALAPPDATA%\Programs\Common\CLAP`; on Mac `/Library/Audio/Plug-Ins/{VST3,Components,CLAP}` and the same under `~`. Plus user-added folders [memory].
- [ ] **ASIO is only present** if the interface's driver (or ASIO4ALL/FlexASIO) is installed; list drivers from `HKLM\SOFTWARE\ASIO`. **WASAPI exclusive** for low latency and WASAPI shared as the safe default need no licence [memory]. Licence in 4.1.

Sources: [Artifact Signing quickstart](https://learn.microsoft.com/azure/artifact-signing/quickstart) [checked, 20 Nov 2026]; [FAQ](https://learn.microsoft.com/en-us/azure/artifact-signing/faq) [checked]; [pricing](https://azure.microsoft.com/en-us/pricing/details/trusted-signing/) [checked]; [DevClass, 14 Jan 2026](https://www.devclass.com/security/2026/01/14/code-signing-windows-apps-may-be-easier-and-more-secure-with-new-azure-artifact-service/4079554) [checked]; [ToDesktop on EV](https://www.todesktop.com/blog/posts/windows-apps-psa-ev-certs-do-not-grant-immediate-reputation-anymore) [search]; [Certum open-source certificate](https://shop.certum.eu/open-source-code-signing-on-simplysign.html) [checked]; [JUCE forum: Store and VST3](https://forum.juce.com/t/windows-11-store-vst3-distribution/47724) [search].

### 5.5 Update security
- [ ] HTTPS only; **sign what is downloaded with a key that is not the hosting account**: Ed25519 over the version file (already designed in `update-feed-plan.md` 5.4) and over every program file, page and engine alike. On an unsigned Windows app electron-updater verifies nothing but the sha512 from the same feed [memory].
- [ ] **No downgrades**: refuse a version file older than the installed program, and give the signed file an expiry date so an old one cannot be replayed forever (an idea from The Update Framework; full TUF is too much for one developer [guess]).
- [ ] **Keys**: the private key offline (password manager or hardware key) or in a GitHub environment that needs manual approval and runs on tags only; two backups. A lost key means users cannot update; a leaked key with no Apple/Microsoft signature next to it can only be fixed by a manual reinstall [memory].
- [ ] Keep electron-updater current: CVE-2024-39698 (Windows signature check bypass) was fixed in 6.3.0; the project's ^6.3.9 is past it [memory].
- [ ] A kill switch: pulling a bad version from the feed stops it spreading; staged rollout once there are users.

Sources: [NVD CVE-2024-39698](https://nvd.nist.gov/vuln/detail/CVE-2024-39698) [search]; [Doyensec on electron-updater](https://blog.doyensec.com/2020/02/24/electron-updater-update-signature-bypass.html) [search]; [The Update Framework, security](https://theupdateframework.io/docs/security/) [search].

### 5.6 GDPR, ePrivacy and the Cyber Resilience Act (Belgium)
- [ ] An **update check** sends an IP address, which is personal data (CJEU *Breyer*, C-582/14, 2016) [memory]. Basis: legitimate interest (security updates), written down in a few lines. Send only version, OS and architecture, no installation id, no analytics; keep server logs short (GitHub, as host, keeps its own logs as its own controller [guess]).
- [ ] **ePrivacy, Article 5(3)**: the EDPB says software that reads information from the device and sends it falls under it; consent is needed unless strictly necessary for what the user asked for [memory: EDPB Guidelines 2/2023 v2, Oct 2024]. An update check presented as part of the app is arguably necessary; crash reports and any statistics are not. So: "Check for updates automatically" (on, explained, can be turned off) and crash reports off until turned on.
- [ ] **Privacy notice** (GDPR Articles 13-14): who, contact, purposes and bases, data, recipients (GitHub, Hugging Face, Sentry if used), transfers, retention, rights, the right to complain to the Gegevensbeschermingsautoriteit / Autorité de protection des données. A record of processing is advisable [memory].
- [ ] **US services**: the EU-US Data Privacy Framework stands (General Court dismissed *Latombe*, T-553/23, 3 Sep 2025); an appeal to the CJEU is pending [checked: WilmerHale, 1 Dec 2025]. Prefer EU regions; check the vendor is certified; keep the standard clauses in its agreement as a fallback.
- [ ] **Cyber Resilience Act** (Regulation 2024/2847): reporting from 11 Sep 2026, the rest from 11 Dec 2027. Free software from a natural person is not "placed on the market"; charging, monetising through other services, or collecting personal data beyond security needs makes it commercial. If AudioLab is ever sold: security by design, an SBOM, security updates for the support period (usually at least 5 years), vulnerability reports to ENISA within 24 h/72 h/14 days, CE marking by self-assessment [checked: Orrick summary of the Commission guidance, Sep 2026; category guess].

Sources: [EDPB Guidelines 2/2023 v2](https://edpb.europa.eu/system/files/2024-10/edpb_guidelines_202302_technical_scope_art_53_eprivacydirective_v2_en_0.pdf) [search]; [WilmerHale on Latombe](https://www.wilmerhale.com/en/insights/blogs/wilmerhale-privacy-and-cybersecurity-law-blog/20251201-european-court-of-justice-to-review-challenge-to-eu-us-data-privacy-framework) [checked]; [Clifford Chance, Sep 2025](https://www.cliffordchance.com/insights/resources/blogs/talking-tech/en/articles/2025/09/transatlantic-data-transfers-where-the-dpf-stands-post-latombe.html) [search]; [Orrick on CRA guidance](https://www.orrick.com/en/Insights/2026/09/EU-Cyber-Resilience-Act-New-Guidance-Clarifies-Scope-Reporting) [checked]; [GitHub on the CRA](https://github.blog/open-source/maintainers/what-the-eus-new-software-legislation-means-for-developers/) [search]; [Sentry data storage location](https://docs.sentry.io/organization/data-storage-location/) [search].

### 5.7 Costs in one place
| Item | Per year | When |
|---|---|---|
| Ad-hoc or self-signed Mac signing | 0 | now |
| Apple Developer Program | USD 99 (about EUR 99 with VAT [guess]) | when the user decides (U1c) |
| Windows unsigned | 0 | Windows stage, first builds |
| Windows OV certificate | about EUR 100-250 + key service [guess] | when there are Windows users |
| Azure Artifact Signing | about USD 120 | only with a company |
| Sentry, EU region | free plan or from about USD 26/month [guess] | when others test |
| ASIO licence | free, but needs Steinberg's signature (weeks) | before a Windows build with ASIO |

---

## 6. Proposed tasks

Sized like this project's tasks (one session each unless said). Order: QL1 to QL4 before the first public native build.

| Task | What | Size | Files |
|---|---|---|---|
| **QL1** (user decision first) | Take the Electric Universe vocals out of the shipped song and the `vox/` folder; add a stand-in vocal (recorded by the user, or none); decide whether to rewrite the public history; keep Fractals v10 out of the fresh install unless permission is in writing. Update U5b in the picks | 1 session + user | `index.html` (DEMO_FRACTALS), `vox/`, `docs/native-mac-picks.md` |
| **QL2** | Third-party notices: `THIRD-PARTY-NOTICES.md` in the repo and the app, "Licences" page under About, check `LICENSES.chromium.html` is in the DMG and the Windows folder; a `LICENSE` line for AudioLab itself | 1 | new file, `index.html` (About), `desktop/package.json` |
| **QL3** | No silent third-party calls: Inter, lamejs and onnxruntime-web bundled inside the app (desktop) and served from the own site (browser); privacy notice page; "check for updates automatically" switch | 1 to 2 | `index.html`, `desktop/scripts/sync-app.js` |
| **QL4** | Signed updates: Ed25519 for `app-version.json` and the program files, downgrade refusal, key in a protected environment (task S1 step 2 brought forward), extended to the engine binaries | 1 to 2 | `desktop/main.js`, workflow, `update-feed-plan.md` |
| **QL5** | Engine test harness: headless render command, golden hashes, null tests web vs native, block-size and offline/realtime invariance; runs in `native-engine.yml` | 2 | `native/`, `tools/engine-tests/` |
| **QL6** | Sanitizer jobs: ASan+UBSan, TSan, RTSan (Homebrew LLVM) on the engine selftests and renders; `[[clang::nonblocking]]` on the audio path; `-Wfunction-effects` | 1 | `native/CMakeLists.txt`, new workflow job |
| **QL7** | Fuzzing: libFuzzer on project loading and the engine's command protocol, ClusterFuzzLite on pull requests; fast-check round trips on the page side | 1 | `native/`, `tools/` |
| **QL8** | Plug-in matrix: nightly free plug-ins (pinned, checksummed) with scan, load, play, state round trip, null; a release checklist for the U3 plug-ins on the user's Mac | 1 + nightly | workflow, `tools/native-lab/` |
| **QL9** | Mac without an account: self-signed identity test (does the microphone permission survive two builds?), translocation warning, DMG with Applications link, Open Anyway page with pictures | 1 + user test | `desktop/scripts/afterPack.js`, download page |
| **QL10** | Crash reports: local crash file and "copy report" first; later opt-in sentry-native + `@sentry/electron` in the EU region with path scrubbing | 1 | `native/engine`, `desktop/main.js` |
| **QL11** | Beta channel and project-format version gate | 1 | `desktop/main.js`, `index.html` |
| **QL12** | Soak and performance: Google Benchmark suite, same-job comparison on pull requests, an overnight soak script for the user's Mac | 1 | `native/`, `tools/` |
| QL13 (when bought) | Developer ID: entitlements files, hardened runtime, notarytool and stapling in CI, first signed app (see 5.2) | 1 | `desktop/package.json`, workflows |
| QL14 (Windows stage) | Apply for Steinberg's ASIO agreement early (user); WASAPI first; plug-in folders; signing decision | user + 1 | `native/` Windows layer |

---

## 7. Decisions for the user
1. **QL1**: remove the original vocals now (recommended), or ask Electric Universe / Sacred Technology for written permission first?
2. **AudioLab's licence**: stay closed ("all rights reserved") or open-source (GPLv3 would allow the free ASIO route and Certum's EUR 49 certificate, and requires publishing all code)?
3. **Crash reports** for the first native build: local file only (recommended), or Sentry in the EU region?
4. **When** to buy the Apple account: unchanged (U1c), or when the first native build goes to anyone other than the user?

## 8. Not confirmed in this research
Re-check before relying on them: current JUCE prices (the forum now refers to a JUCE 9 EULA); the Belgian euro price of the Apple program; Electron's current entitlement advice (`allow-jit` alone); Sparkle's documentation on apps without Developer ID; whether a self-signed certificate keeps macOS's microphone permission across updates (test, QL9); the text of Steinberg's current ASIO agreement and whether an individual can sign it; Sentry's free-plan limits; pluginval's current version; whether `snd-dummy` loads on Ubuntu runners; the licence and reserved-name status of JetBrains Mono (only if it is ever used).

## 9. Research method
Three research helpers (testing, licensing, distribution) searched the web on 27 Nov 2026; a fourth read six pages to settle open points (model-card licences, the JUCE thread, the Google Fonts ruling, Certum). npm licence fields were read with `npm view`. The repository was read at commit 47e6989 (`index.html` v0.228, `desktop/`, `native/`, the four workflows). The page-read quota of the helpers ran out part way, which is why many items are [search] or [memory].
