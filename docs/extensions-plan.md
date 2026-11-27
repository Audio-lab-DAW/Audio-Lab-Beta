# AudioLab Pro: extensions plan, round 1 (task EX1, 27 November 2026)

Pick page: **AudioLab extensions, round 1**, https://claude.ai/artifact/Xz4hiGRdHZM67suL4KiWq5

**Nothing in index.html or desktop/ was changed, no version bump.** This is research, a staged design and four working prototypes in `tools/extension-lab/`.

The user's words: "Can we make an API or a system so people can customize the UI themselves or build their own devices if they want? And maybe find a way to have that implemented inside of the software somewhere. We already have a chat box, so I don't know."

## 1. Summary

- **Yes, and it can be done safely, in five small stages.** 1 themes and layouts as a file, 2 devices from a description file built from AudioLab's own blocks, 3 a script device, 4 building by talking in the Assistant, 5 sharing with an import card.
- **One rule decides the whole design:** a user file never gets the app's powers. Themes and device descriptions are read as data. Scripts are written in a small language that AudioLab itself compiles, so a script can only touch its own numbers and cannot loop for ever. Safety comes from what the format cannot express, not from asking the user for permission. The research backs this: the systems that are really safe (Figma, Factorio, Reason) remove capabilities; the ones that ask for trust (VS Code, Obsidian) say openly that they cannot restrict a plug-in.
- **The audio path stays safe** (glass-engine-plan section 1: snappy, low CPU, audio first): a host-owned safety stage after every user device (broken numbers become silence, a limiter, an auto-mute for blasts), a test run off the audio thread before a device goes live, and a watchdog that bypasses a device that overruns.
- **Four prototypes run on the pick page**: a theme editor that restyles a mock AudioLab from a file; a device built from a description file (edit the text, the knobs and the sound change); a script device with a code box and a cost meter; a mock-up of the chat box building a device from a sentence. 44 headless checks pass, including sound through the safety stage.
- **The chat box:** the Assistant already exists (`aiOpen`, `aiSend`, tools in `AITOOLS`). It uses a model only when AudioLab runs inside claude.ai (`claude.use('sample')`); in the desktop app it falls back to about a dozen rules (`aiLocal`). Building devices by talking needs three new tools and, for the full version, a model connection. A rule-based helper without a model works for common words (the mock-up knows about 70).
- **Nine questions** are on the page with a recommendation each. The picks bar gives one line to paste, for example `EX1 picks: 1A 2B 3A 4A 5A 6A 7A 8A 9A`.

## 2. What exists in the app today (v0.221, read for this task)

| Part | How it is built | What it means for extensions |
|---|---|---|
| Effect descriptors | `FXDEF.<type> = {name, p: {key: [min, max, default, unit, log]}}`; `mkFx(type)` makes the parameter object from the defaults; `mk<Type>(ctx)` returns `{in, out, set(p)}` (example: `mkPhaser`, a patch of Web Audio nodes) | A description device is the same shape written as a file: parameters with ranges and units, and a patch that ends in `{in, out, set}`. Stage 2 can plug into `mkFxNode` with one extra branch. |
| Worklet devices | About 30 processors. Sources are template strings (`WLSRC`, `VWL`, `RWL`, `PWL`, `GWL`, …) joined into one Blob module by `wlLoad(ctx)`, also for offline renders (`bounceRender`) | A script device must load the same way: one more module per script, added to both the live and the offline context, or exports would differ from what was heard. |
| Presets | Effects: `FXPRE.<type>.<id> = [name, values]`. Instruments: `PRS(group, [[id, name, values], …])` | The device file's `presets` uses the `FXPRE` shape, so the existing preset arrows and "Change" work unchanged. |
| Device pictures and layout | `docs/devices-display-first.md`: display as large as possible, sideways title strip (on/off, name, remove), glass dock (DD1) or rail (DD2), eye button, each device keeps its width | The file's `layout` names a style (`dock` first) and lists which knobs sit in the dock and which under "More". The frame is drawn by AudioLab, so user devices look like the others. |
| Themes | `THEMES` table (`id`, `n`, `bgL`, `tintH`, `tintA`, `gridB`, `clipA`, `pal`, colour overrides) chosen by `UI.dawLook`; many more look settings in `UI.*` (docs/settings-audit.md 2.4 to 2.8: `UI.trans`, `UI.blur`, `UI.edge`, `UI.bgL`, `UI.tintH`, `UI.tintA`, `UI.clipA`, `UI.gridB`) | A theme file is a `THEMES` entry plus the look settings, with every value clamped. Glass uses the three levels and the presets from glass-engine-plan (no free sliders). |
| Assistant | Button `#bAI`, panel `#aip`. `aiSend` sends the last 12 messages plus a system text to `claude.use('sample')` with the `AITOOLS` list (get_song, add_notes, add_effect, set_effect_param, …); each tool runs a function in `AIT` and logs an undoable action. Without a model: `aiLocal`, regular expressions for risers, breakdowns, brighter, louder, tempo, reverb, echo | Stage 4 adds tools (`make_theme`, `make_device`, `edit_device`) to the same list. Their output is a file that goes through the same checker as a hand-written one. |
| Desktop shell | `desktop/main.js`: `contextIsolation: true`, `nodeIntegration: false`, `sandbox: true` | Already matches Electron's security checklist. Extensions must never get a preload bridge of their own. |

## 3. Research: how other tools do it

Gathered by a research helper on 27 Nov 2026 through search and a fetch tool. "Read" means the page was opened; everything else is general knowledge and marked as not verified.

### 3.1 Music software

| Tool | How users build | Format | Sandbox | Lesson for AudioLab |
|---|---|---|---|---|
| **Max for Live** ([overview](https://docs.cycling74.com/legacy/max8/vignettes/max_for_live_topic), [Live Object Model](https://docs.cycling74.com/api/latest/max8/vignettes/live_object_model), read) | Visual patching. `live.dial`, `live.toggle` are host-aware controls; `live.path`, `live.observer` reach the Live Object Model | One `.amxd` file | None: full Max, with scripts and file access (not verified) | A small set of host-native controls that are automatically saved, automatable parameters |
| **Bitwig** ([The Grid](https://bitwig.com/the-grid), [controller scripts](https://www.bitwig.com/en/community/control_scripts.html), read) | The Grid: modular patching inside the DAW, saved as presets. Controller scripts in JavaScript or Java drive the app, not the sound | Presets; `.control.js`, `.bwextension` (not verified) | Not verified | Keep "control the app" scripting apart from "make sound" scripting. Sharing is informal ("mostly … on Github") |
| **Reaper JSFX** ([reference](https://www.reaper.fm/sdk/js/js.php), read) | A text file compiled on the fly. `desc:`, then `@init`, `@slider`, `@block`, `@sample`, `@gfx`. One line is both the knob and the parameter: `slider1:5<0,10,1>name` | Plain text | Light: memory cap, files only in one folder, **no CPU guard** | The proven shape for a script device: declarative parameter lines plus code sections that run at fixed moments. We add the CPU guard it lacks |
| **Reaper ReaScript and WALTER** ([ReaScript](https://www.reaper.fm/sdk/reascript/reascript.php), [WALTER](https://www.reaper.fm/sdk/walter/walter)) | Lua, EEL or Python scripts automate the app; themes are image sets plus layout rules in WALTER | Text files, shared through ReaPack (not verified) | None | Layout as rules in a file works, but WALTER is known as hard to learn (opinion); keep ours to named choices |
| **FL Studio** ([MIDI scripting](https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/midi_scripting.htm), [piano roll scripting](https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/pianoroll_scripting_api.htm)) | Patcher wires existing plug-ins into a new device with its own control surface; Python for controllers and piano-roll tools | Presets, `.pyscript` (not verified) | Embedded interpreter with a limited module set (not verified) | "Combine existing devices and expose macro knobs" is the lowest-risk kind of user device: no code |
| **VCV Rack** ([manifest](https://vcvrack.com/manual/Manifest), read; [panels](https://vcvrack.com/manual/Panel)) | C++ modules, SVG panels | `plugin.json`: slug, name, version, modules | None (native code); a central library builds and reviews | "The slug must never change, otherwise patch compatibility would be broken", and the major version follows the host |
| **Reason Rack Extensions** ([SDK](https://developer.reasonstudios.com/documentation/rack-extension-sdk/4.3.0/jukebox-concepts), [talk summary](https://www.synthtopia.com/content/2018/12/13/inside-the-propellerhead-reason-rack-extension-format/), read) | C++ DSP against a narrow API, plus Lua descriptor files for properties and the panel (file names not verified) | Shop only | Sandboxed, shipped as LLVM bitcode, declarative UI | Declarative descriptors plus a narrow host API make third-party devices portable and crash-contained |
| **Web Audio Modules 2** ([API](https://www.github.com/webaudiomodules/api), read) | An ES module exporting a `WebAudioModule` class; `createInstance`, `createGui`, `getParameterInfo`, `getState`, `setState` | `descriptor.json`: name, vendor, version, apiVersion, isInstrument, IO flags | None: the plug-in runs in the host page and worklet | Copy the descriptor and the parameter and state contract, not the trust model |
| **Faust** ([LLM guide](https://faustdoc.grame.fr/manual/llm/), read; [syntax](https://faustdoc.grame.fr/manual/syntax/), [web IDE](https://github.com/grame-cncm/faustide), [faustwasm](https://github.com/Fr0stbyteR/faustwasm)) | The UI is declared inside the DSP code (`hslider`, groups); the compiler emits a JSON description for the host to draw. Compiles in the browser to WebAssembly in an AudioWorklet | `.dsp` text | WebAssembly | Derive the UI from parameter declarations. A compile step is a cheap first check for model-written code. Faust's own guide warns of "invented library names, wrong argument order, unsafe UI ranges, clipping, self-oscillation, and silence" |
| **Cmajor** ([patch format](https://cmajor.dev/docs/PatchFormat), read) | A manifest plus DSP source plus an optional web view that talks to the DSP through one `PatchConnection` object | `.cmajorpatch` JSON: `ID`, `version`, `name`, `source`, `view` | Runs as WebAssembly in a worklet for the web | The closest model to what we want: manifest, DSP source, optional view behind one connection object |
| **plugdata, Pure Data** ([plugdata](https://github.com/plugdata-team/plugdata), [hvcc](https://www.github.com/Wasted-Audio/hvcc)) | Visual patching; a patch is a text file; Heavy compiles a subset of objects | `.pd` | None (not verified) | A restricted set of objects is what makes a patch portable |
| **SuperCollider** ([client and server](https://docs.supercollider.online/Guides/ClientVsServer.html)) | The language builds a graph of fixed unit generators (`SynthDef`) and sends it to a separate audio server | `SynthDef` | Only built-in units run on the audio side (not verified beyond the guide's title) | The strongest pattern: user code describes a graph, only trusted units run on the audio thread. This is stage 2 |
| **Norns** ([maiden](https://monome.org/docs/norns/maiden/), read; [params](https://monome.org/docs/norns/reference/params)) | Lua scripts; a web editor served by the device; a uniform `params` menu gives every script presets and MIDI mapping | Folders; catalogues or `;install <GitHub URL>` | Editor limited to one folder | A uniform parameter system gives every script presets and mapping for free. Updating overwrites local edits: we must not |
| **Teenage Engineering** ([videolab](https://teenage.engineering/products/op-z/videolab)) | No official user scripting or device SDK was found for OP-1, OP-Z or EP-133; videolab is Unity visuals | – | – | Nothing to copy; treated as "none" |

### 3.2 Extension models outside music

| System | Manifest | Sandbox and permissions | Lesson |
|---|---|---|---|
| **VS Code** ([runtime security](https://code.visualstudio.com/docs/configure/extensions/extension-runtime-security.md), read) | `package.json` with contribution points and activation events | A separate extension host that "has the same permissions as VS Code itself". Protection is social and store-side: publisher trust prompt, malware scan, signatures, block list | A manifest is good for discovery and versioning, not for safety |
| **Figma** ([how plug-ins run](https://developers.figma.com/docs/plugins/how-plugins-run), [how it was built](https://www.figma.com/blog/how-we-built-the-figma-plugin-system/), read) | `manifest.json`, with `networkAccess` listing allowed domains | Logic runs in "a minimal JavaScript environment [that] does not expose browser APIs"; the UI in an iframe; messages between them. Their first sandbox (a Realms shim) had a hole, so they moved to a JavaScript VM compiled to WebAssembly | Trying to fence off full JavaScript is hard even for a large team. A smaller language is the cheaper route |
| **Obsidian** ([plug-in security](https://obsidian.md/help/plugin-security), read) | `manifest.json` | Restricted Mode by default; otherwise plug-ins get full access "because permissions cannot be enforced" | Be honest in the UI about what a file can do |
| **Factorio** ([mod structure](https://lua-api.factorio.com/latest/auxiliary/mod-structure.html), [libraries](https://lua-api.factorio.com/latest/auxiliary/libraries.html), read) | `info.json`: name, version n.n.n, game version, dependencies | Lua with `io`, `os`, `loadfile`, `dofile` removed | Safety by removing capabilities from the language works at scale |

### 3.3 AI-assisted creation in other products

- **ChatDSP**, **Amorph**, **Pluginmaker.ai** ([MusicRadar overview](https://www.musicradar.com/music-tech/ai-prompt-plugins), read): a Max for Live device that sends a prompt to a model with the user's own key; a plug-in whose AI assembles prebuilt DSP blocks; a browser generator with credits and a marketplace. All beta or new.
- **Synplant 2** ([CDM](https://cdm.link/synplant-phenotype/), read): Genopatch matches a patch to a sample; PhenoType is text to patch with a small local network and about 200 tags. Not a language model, and it only sets the parameters of one fixed synth.
- **Claude artifacts** ([Simon Willison](https://simonwillison.net/2025/Jun/25/ai-powered-apps-with-claude/), read): a page can ask a model; the cost goes to the viewing user. AudioLab's Assistant already uses this when it runs inside claude.ai.
- **Hype check:** every product that works writes code or a patch for a constrained target and then compiles it. No first-party text-to-device feature from Ableton or Bitwig was found. Faust's own guide says that compiling proves neither stability nor musical quality.

### 3.4 Security for user code in the browser and in Electron

- **Electron** ([security checklist](https://electronjs.org/docs/latest/tutorial/security), read): context isolation, process sandbox, no Node integration, a restrictive CSP, limited navigation, validated IPC, no Electron APIs for untrusted content. AudioLab's shell already sets the first three.
- **Sandboxed iframes** ([web.dev](https://web.dev/articles/sandboxed-iframes.md.txt), read): `sandbox="allow-scripts"` gives a unique origin; never combine it with `allow-same-origin` for own-origin content. Only needed if user-written interface code is ever allowed (not proposed).
- **AudioWorklet** ([MDN](https://developer.mozilla.org/docs/Web/API/AudioWorkletGlobalScope), [working group issue](https://www.github.com/WebAudio/web-audio-api/issues/2499), read): no DOM; "there is no comprehensive list of blocked APIs" and browsers differ. **The worklet scope is not a security boundary** and must not be relied on as one.
- **Infinite loops** ([Chrome's worklet patterns](https://developer.chrome.com/blog/audio-worklet-design-pattern.md.txt), [HTML spec](https://html.spec.whatwg.org/dev/worklets.html), read): the budget is about 3 ms per 128 samples; the spec only says a browser *may* stop a runaway worklet. Nothing can interrupt the audio thread from outside. Known ways out: metering injected into WebAssembly ([wasm-metering](https://www.github.com/ewasm/wasm-metering)), loop counters added by one's own compiler, an interpreter with a step budget, or running user DSP in a Worker behind a ring buffer (a hang then gives silence; using that as a kill switch is an inference).
- **Output safety:** replacing NaN and infinity, flushing denormals and a hard limit after third-party DSP is standard practice among plug-in developers ([JUCE forum thread](https://forum.juce.com/t/hearing-protection-in-audio-plugins/64802), not opened).
- **Signing and import:** WebCrypto can verify Ed25519 signatures ([MDN](https://developer.mozilla.org/docs/Web/API/SubtleCrypto/sign), not opened). For archives: refuse paths with `..`, cap size and file count ([Zip Slip](https://security.snyk.io/research/zip-slip-vulnerability), not opened). Our files are single text files, so most of this risk does not arise.

## 4. The staged design

Each stage is one task, or two where marked. The same checker pattern runs through all of them: parse, check field by field, clamp, report what was changed in plain words, and keep the last good version if the new one is refused.

### Stage 1: themes and layouts as a file

- **The user sees:** in Settings, "Save look as a theme file" and "Open theme file"; theme cards beside the built-in ones. Later the Workshop (question 3) with the file on the left and the app restyling live.
- **File** `.audiolabtheme` (JSON, values only):

```json
{
  "format": "audiolab.theme", "formatVersion": 1,
  "id": "user.jupiter", "name": "Jupiter", "author": "you", "mode": "dark",
  "colors": {"accent": "#ff9a3c", "second": "#e0633a", "tracks": ["#ff9a3c", "#f5c84c"]},
  "background": {"brightness": 34, "tintHue": 24, "tintAmount": 45},
  "glass": {"level": "engine", "blur": "regular", "transparency": 60, "edge": 70},
  "clips": {"opacity": 48, "grid": 40},
  "layout": {"devicePanel": "tall", "mixer": "right", "trackHeight": "normal",
             "show": {"sections": true, "visualizer": true, "assistant": true, "meters": true}}
}
```

- **Mapping to the app:** `background` to `UI.bgL`, `UI.tintH`, `UI.tintA`; `clips` to `UI.clipA`, `UI.gridB`; `glass` to the three levels and presets of the glass engine; `colors.tracks` to a `THEMES` `pal`; `layout` to the existing panel-size and show/hide settings. The exact list of layout keys should follow the Settings rebuild (settings round 1), so the names here are a sketch.
- **Inside the design language:** every number is clamped; colours are moved in lightness until the accent has 3:1 and text 4.5:1 against the panels (prototype 1 shows the corrected value and says why); unknown keys are ignored and listed. Type scale, fonts, icons and the fader design are not in the file at all.
- **Risks:** an unreadable or ugly look (handled by the clamps; question 5 decides how strict); a theme written for a later version (handled by `formatVersion`: refuse newer, upgrade older).
- **Waits for the native engine:** nothing.

### Stage 2: description devices (two tasks: the format and checker; the frame and browser entry)

- **The user sees:** "My devices" in the device browser and "New device…". A user device looks like any other: sideways title, big display, glass dock, preset arrows. An Edit button opens its file.
- **File** `.audiolabdevice` (JSON):

```json
{
  "format": "audiolab.device", "formatVersion": 1,
  "id": "user.warm-echo", "name": "Warm echo", "kind": "effect", "author": "you", "version": "1.0.0",
  "params": [
    {"id": "time", "name": "Time", "min": 40, "max": 1200, "default": 330, "unit": "ms", "curve": "log"},
    {"id": "feedback", "name": "Feedback", "min": 0, "max": 90, "default": 48, "unit": "%"}
  ],
  "blocks": [
    {"id": "d", "type": "delay", "time": "$time / 1000"},
    {"id": "fb", "type": "gain", "gain": "$feedback / 100"}
  ],
  "wires": [["in", "d"], ["d", "fb"], ["fb", "d"], ["d", "out"], ["in", "out"]],
  "display": {"type": "spectrum"},
  "layout": {"style": "dock", "dock": ["time", "feedback"], "more": []},
  "presets": {"slap": ["Slapback", {"time": 95, "feedback": 10}]}
}
```

- **How it makes sound:** `blocks` are AudioLab's own building blocks, wired by `wires`; a block setting is a number or a small formula over the knobs (`$time / 1000`, `db($level)`). Formulas are parsed and walked by our own evaluator, never `eval`. A wire may end at a setting (`"lfo1" → "d.time"`) for modulation. In the prototype the blocks are plain Web Audio nodes (gain, delay, filter, drive, pan, comp, reverb, lfo). **In the app the block list should be the existing effects** (`FXDEF` types: Pro EQ, compressor, echo delay, phaser, OTT, …) plus those few primitives, so a user device is a rack with macro knobs.
- **Checker rules:** at most 16 knobs, 24 blocks, 64 wires; ids unique and never renamed (VCV's rule, because projects refer to them); a feedback loop must contain a delay; a gain inside a loop is capped at 95%; something must reach `out`; unknown keys ignored.
- **Display:** a small set of host-drawn types (`spectrum`, `scope` in the prototype; later `curve` for a filter response, `echoes`, `meter`), chosen by name. No user drawing code in this stage.
- **Risks:** runaway feedback through a resonant filter (the cap helps, the safety stage is the backstop); a device that depends on a block AudioLab later changes (blocks need a version in the file once they are the real effects); offline export must build the same graph (use the same builder for `OfflineAudioContext`, as `mkFxNode` does).
- **Waits for the native engine:** VST plug-ins as blocks; anything a rack of built-in effects cannot do is stage 3.

### Stage 3: script devices (two tasks: effects; then instruments with notes)

- **The user sees:** a device whose file has a `script` part, a code box in the Workshop, and three cost bars: work per sample (known before it runs), the test run, and live.
- **Language (prototype 3; question 2 decides):** a header declares the knobs, then up to three sections.

```
name Soft clip and tone
param drive 0..30 = 12 dB
param tone 200..12000 = 4000 Hz log

init:                  // once
  lp0 = 0;
block:                 // once per 128 samples
  g = db(drive);
  k = 1 - exp(-2 * pi * tone / sr);
sample:                // every sample
  a = tanh(in0 * g);
  lp0 = lp0 + k * (a - lp0);
  out0 = lp0;  out1 = lp0;
```

- **What the language has:** numbers, variables (kept between samples, as in JSFX), `+ - * / %`, comparisons, `if`/`else`, `loop (N)` with N written out (1 to 64, nested 3 deep at most), a delay memory `mem[i]` of 131,072 slots (about 2.7 s), and 20 functions (`sin`, `tanh`, `pow`, `clamp`, `blend`, `db`, `noise`, …). `in0 in1 out0 out1 sr pi` are given.
- **What it does not have, on purpose:** strings, objects, function definitions, `while`, any name from outside. The compiler turns the script into JavaScript that only contains what the compiler itself emitted: variables become slots in a private array, `mem[i]` becomes a masked index, functions come from a fixed list. So `fetch(…)`, `window = 1`, `this`, a template string or an arrow function are compile errors (14 escape attempts are in the checks). Because loops have a written-out count, the worst-case number of steps per sample is known at compile time; above 2000 the script is refused before it runs.
- **Before it goes live:** the compiled code processes one second of test sound in a Worker (which can be killed after 4 s). Measured: time (refused above 25% of one core), bad numbers, peak level. On the cloud machine the examples measured under 1%.
- **While it runs:** the host processor times each block; six blocks over 1.5 times the block's duration and the script is bypassed (dry sound passes) with a message. If the script produces a bad number its memory is cleared and re-initialised. Then the safety stage.
- **Not verified:** whether `performance.now()` exists inside the audio thread in every browser; the host falls back to `Date.now()` (1 ms steps, shown as an approximate reading). The test-run figure does not depend on it.
- **Risks:** a language we must maintain and document (kept small for that reason); zipper noise or clicks from bad scripts (not dangerous); users expecting JSFX compatibility (question 2C); export must load the script module into the offline context too.
- **Waits for the native engine:** heavy scripts (many voices, large FFTs, oversampling), scripts compiled to native speed, more than one core. Until then a script shares the one audio thread with everything else, so the budget is deliberately tight.

### Stage 4: building by talking

- **The user sees:** in the Assistant: "a warm tape echo with wobble". A card: built, 6 knobs, checked. The device appears on the selected track or in the Workshop; "more feedback", "darker", "call it Moon echo", "remove the echo" change it; every step is undoable; "Open in Workshop" shows the file.
- **How:** three tools beside the existing ones in `AITOOLS`: `make_theme(file)`, `make_device(file)`, `edit_device(id, file)`. The model's output is a file in the formats above. It goes through the same checker and test run as a hand-written file; errors go back to the model as the tool result so it can correct itself (Faust's loop: write, compile, inspect, listen).
- **What this needs, honestly:**
  - *A model connection.* Inside claude.ai it exists already (`claude.use('sample')`, billed to the viewing user). In the desktop app there is none today. The options are the user's own API key kept in the system keychain by the shell (the app then talks to the provider directly), or a service AudioLab runs (a server, accounts and a budget on the owner's side). Cost per built device is a guess: a few cents with a mid-size model, since the request is a system text with the format (a few thousand tokens) plus a file of one to three thousand tokens. Not measured.
  - *Or a rule-based helper without a model.* Prototype 4 is one: about 70 words mapped to 12 building blocks, plus more/less, darker/brighter, rename and remove. It is free and offline, and it only understands what it was taught. It can write description devices and themes, not scripts.
  - Recommended: both (question 4A). The helper is the floor; a model, when connected, replaces it in the same chat.
- **Risks:** a model writes a plausible but poor device (the checks catch broken, loud and heavy, not dull); cost surprises (show that a model is in use, never call it silently); a key stored carelessly (keychain only, never in a project or theme file).
- **Waits for the native engine:** nothing.

### Stage 5: sharing

- **The user sees:** drag a `.audiolabtheme` or `.audiolabdevice` onto AudioLab (or "Import…"). A card shows the name, author, version, what is inside and what it cannot do, with numbers the app measured itself (knobs, steps per sample, test-run cost), and "Add to My devices" or "Cancel". Later, maybe a gallery (question 6).
- **File:** the same single text files, plus `"madeFor": "0.23"` (oldest AudioLab version that reads it), a checksum of the content, and an optional signature block (Ed25519 public key and signature, verifiable with WebCrypto). A device used in a project is copied into the project file, so a song opens on another computer without the device installed.
- **Why the card has little to ask:** there are no permissions to grant, because the formats cannot ask for any. The card informs; it does not shift responsibility to the user.
- **Risks:** files over a sensible size (cap at 256 kB); name clashes (ids are namespaced, `user.` or `author.`; importing a second device with the same id asks to replace or keep both); a later format that adds power (must go through a new `formatVersion` and never through an unknown key).
- **Waits for the native engine:** sharing native plug-ins, which should never go through this system.

## 5. Safety rules (hold in every stage)

1. User files never get the app's powers: no file access, no network, no access to the project, no Node, no preload bridge.
2. Themes and descriptions are data. Formulas are parsed and walked, never evaluated as JavaScript.
3. Scripts are compiled by AudioLab into code that contains only what the compiler emitted. The worklet scope is not treated as a sandbox.
4. No script can loop for ever; worst-case work per sample is known before it runs and capped.
5. Every device is test-run off the audio thread first. Too heavy or timing out: it does not go live.
6. A watchdog in the audio thread bypasses a device that overruns and says so.
7. A host-owned safety stage follows every user device: bad numbers become silence, a limiter at about -1 dB, an auto-mute of 1.5 s when the input stays above +12 dB for 50 ms. The file cannot remove it (question 9 asks whether the user may).
8. A refused file never replaces a working one: the last good version keeps playing.
9. Unknown fields are ignored and reported, never run. New power only comes with a new format version.
10. Ids never change after release; versions are `n.n.n`; files name the oldest AudioLab that can read them.

## 6. The prototypes (`tools/extension-lab/`)

| File | What it is |
|---|---|
| `extensions-round-1.html` | The pick page: all four prototypes, the stage table, the import-card sketch, nine questions, the picks bar. One file, no libraries. |
| `check.js` | 44 headless checks (`node tools/extension-lab/check.js`): theme clamps and contrast, device checker (loop without a delay refused, feedback capped), formulas, script compiler (examples compile, the heavy one is refused, 14 escape attempts refused), test runs, the chat flow, sound through the safety stage (the runaway device and the loud script are held), picks line, no sideways scroll at 1280 and 400 px. Also writes `open.html` and the example files. |
| `examples/` | 4 themes (`.audiolabtheme`), 4 devices (`.audiolabdevice`), 4 scripts (`.alscript`), as used on the page. |

What each prototype shows and where it is not the real thing:

- **P1 theme editor:** text and controls edit the same file both ways; five examples, one deliberately wrong (the checker corrects seven values and ignores an `onLoad` key). The mock is a drawing of AudioLab, not the app; its glass is CSS blur, not the engine.
- **P2 description device:** five examples, one a runaway loop that the checker caps and the safety stage holds. Knobs, presets, "More" tray, on/off and the display are generated from the file. Blocks are Web Audio nodes, not AudioLab's effects. Effects only.
- **P3 script device:** seven examples: four working, one refused as too heavy, one loud bug that the safety stage mutes, one that tries to reach outside and does not compile. Effects only; no notes yet.
- **P4 chat mock-up:** marked as a mock-up on the page. No model is connected; a rule helper writes real description files that go through the P2 checker. It also makes a theme from a colour word.

## 7. Questions on the pick page (★ is the recommendation)

1. Which stages first: **A ★ in order**, B devices first, C chat first, D stop after stage 2.
2. How open is scripting: A none, **B ★ the small safe language**, C the same written like JSFX, D Faust, E full JavaScript for developers only.
3. Where it lives: **A ★ a Workshop window with doors from the device browser and the Assistant**, B the device browser only, C the chat only, D a page outside the app.
4. What answers in the chat: **A ★ rule helper built in, a model when one is connected**, B model only with the user's key, C a model through an AudioLab service, D no chat building.
5. Theme freedom: **A ★ guarded**, B free colours, C plus custom CSS for developers.
6. Sharing: **A ★ files with the import card**, B plus a gallery later, C signatures required.
7. Device file style: **A ★ JSON**, B a friendlier text form, C a visual editor.
8. **A ★ effects first**, B instruments from the start.
9. Safety limiter: **A ★ always on**, B a switch in Settings.

Answer by pasting the line from the picks bar, for example `EX1 picks: 1A 2B 3A 4A 5A 6A 7A 8A 9A`.

## 8. Proposed tasks after the picks (if the starred answers are chosen)

| Task | Content | Touches |
|---|---|---|
| EX2 | Theme files: checker from the prototype, save and open in Settings, mapping to `THEMES` and `UI.*` | index.html (Settings, theme code) |
| EX3 | Device file format and checker in the app; builder that returns `{in, out, set}`; live and offline | index.html (`mkFxNode`, export) |
| EX4 | User device frame in the display-first style; "My devices" in the browser; presets | index.html (devices panel, browser) |
| EX5 | Safety stage worklet after user devices; test run; watchdog | index.html (`wlLoad`, one new processor) |
| EX6 | Script devices (effects): compiler, host processor, cost meter | index.html |
| EX7 | Workshop window: file left, result right, three tabs | index.html |
| EX8 | Assistant tools `make_theme`, `make_device`, `edit_device`; the rule helper grown from the mock-up | index.html (`AITOOLS`, `aiLocal`) |
| EX9 | Import card, checksum, optional signature, devices stored in the project file | index.html, desktop/ (file association) |
| EX10 | Script instruments: notes in, voices | index.html |

EX5 should land before any user device can make sound in the app.
