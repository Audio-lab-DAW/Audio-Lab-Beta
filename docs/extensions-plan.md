# AudioLab Pro: extensions plan, round 1 (task EX1, 27 November 2026)

Pick page: **AudioLab extensions, round 1**, https://claude.ai/artifact/Xz4hiGRdHZM67suL4KiWq5

**Nothing in index.html or desktop/ was changed, no version bump.** This is research, a staged design and four working prototypes in `tools/extension-lab/`.

**Section 9, "The deep layer" (task EX2), extends this plan** for advanced users: an everything list of settings, rules that hide, rename or move any control, a commands registry with macros, CSS snippets, user scripts, the Workshop tabs for them, and safe mode. Its six prototypes and twelve decisions are a new part of the same pick page.

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

## 9. The deep layer (task EX2, 27 November 2026)

Added to the same pick page as a new part, **"The deep layer"**, between prototype 4 and the questions: https://claude.ai/artifact/Xz4hiGRdHZM67suL4KiWq5#deep

**Nothing in index.html or desktop/ was changed, no version bump.** Research, a design in seven parts, six working prototypes and twelve decisions.

The user's added words: "And maybe in that API system, we can have some very advanced loose features. So if people want to hide certain buttons or features, modify in a very advanced way that goes much, much deeper than the settings. Or maybe if people want to use code or write their own code, something like that."

### 9.1 Summary

- **Yes: one layer under Settings, in seven parts that build on each other.** (a) an everything list of settings by id, (b) a rules file that hides, renames or moves any control, (c) a registry where every action is a named command, (d) small CSS snippets, (e) user scripts with a small API, (f) a Workshop page to write them in, (g) safe mode and reset behind all of it.
- **Two lists must exist first, and they are the real work:** a stable id on every control, and every action as a named command. Everything else reads those two lists plus the settings table of step S4 (`docs/settings-round-1.md`). The app is closer than it looks: the shortcut list `SCA` already holds 57 actions with an id, a group, a name, a default key and a function, and `UI.keys` already stores the user's own keys.
- **The first wish, "hide certain buttons", needs no code and no Workshop.** A right-click "Hide this" writes one line into the rules file. That part can ship early.
- **Safety is by construction, as in EX1:** files are data and are checked field by field; the safety values of the sound engine are locked in every door (list, file, CSS, script); a script works on a copy of the project and hands back a list of changes that AudioLab checks and applies as one undo step; it runs away from the window and the sound, with a time limit.
- **Cost when unused: nothing that can be measured.** No worker, no extra stylesheet and no rule lookups exist until the user makes a first change. (Expected from the design; not measured, because nothing is in the app yet.)
- **Six prototypes run on the pick page, all on one small mock AudioLab.** 73 headless checks pass (`node tools/extension-lab/deep_check.js`).
- **Twelve decisions** (K1 to K12) and a Yes / Later / No per tool join EX1's picks line.

### 9.2 How this fits the plan above

| Point | EX1 (sections 1 to 8) | Deep layer |
|---|---|---|
| What the user makes | Themes, devices, script devices | Changes to AudioLab itself: settings, controls, keys, macros, look, helpers |
| Code that runs | **Device scripts**: a small language AudioLab compiles, per sample, in the sound engine, no access to the project | **Workshop scripts**: JavaScript, in a sandbox outside the sound engine, never per sample, access to the project only through a checked list of changes |
| Home | The Workshop window (question 3A) | The same Workshop, as more tabs. K2 and K3 only matter if question 3 is not answered A |
| Chat box | `make_theme`, `make_device`, `edit_device` | Three more tools of the same kind: `write_rules`, `write_macro`, `write_script`, each shown before it is applied (K10) |
| Sharing | Import card (question 6) | Same card; K7 follows question 6 |

Three places where the two parts touch:

1. **Safety rule 1 in section 5 needs one sentence added** if scripts are picked (K1c): "Workshop scripts are the one exception: they may read the project and propose changes through the script API, and nothing else." Device files stay exactly as rule 1 says.
2. **Question 2E** ("full JavaScript for developers only") is about device code in the sound engine and stays not recommended. Workshop scripts are how JavaScript is offered safely: they never run in the audio thread.
3. **Question 5C** ("custom CSS for developers") is the same thing as part (d) here. If 5A (guarded themes) is picked, K1b or K1c still gives CSS, as a separate file with its own switch, which is the Obsidian arrangement.

### 9.3 Research: how other programs expose a layer far below their settings

Read from the official pages unless marked. "Unverified" means the page could not be opened in this run and the statement is from general knowledge.

**Lists of everything and layered settings**

| Program | How it works | What to take |
|---|---|---|
| Firefox `about:config` ([Mozilla](https://support.mozilla.org/en-US/kb/about-config-editor-firefox), [how prefs are stored](https://firefox-source-docs.mozilla.org/modules/libpref/index.html)) | Search by preference name. Each one has a default and, perhaps, a user value; the user value wins; changed ones are bold; Reset puts back the default. Names are dotted (`security.OCSP.enabled`). User values live in `prefs.js` (written by Firefox) and `user.js` (written by the user, only read). Prefs can be locked. | The list itself: id, value, default, changed mark, reset. Dotted ids. Locked values. |
| VS Code settings ([docs](https://code.visualstudio.com/docs/configure/settings)) | JSON files in layers; later wins: default, user, workspace, folder, then policy. Extensions declare their settings with a type and a scope (`application`, `machine`, `window`, `resource`) ([contribution points](https://code.visualstudio.com/docs/extensionAPI/extension-points)). | Three layers and a scope per setting (some belong to the machine and never travel). This is the "computer / project" mark of settings round 1. |
| Sublime Text ([settings](https://www.sublimetext.com/docs/settings.html)) | JSON files consulted in a fixed order (default, platform, user, project, syntax, buffer). The settings view has two panes: the documented defaults on the left, the user's file on the right. | Only the differences are in the user's file, so a better default in an update reaches everyone who did not change it. The two-pane view. |
| Ableton `Options.txt` ([Ableton](https://help.ableton.com/hc/en-us/articles/6003224107292)) | A plain text file in the Preferences folder, one `-Option` per line, restart needed. Ableton calls the options experimental and unsupported and says they may change or go without warning. Examples from the article: `-_PluginAutoPopulateThreshold=64`, `-EnableArmOnSelection`. | The warning in reverse: hidden options with no list, no check and no promise are a support problem. An everything list with types and ranges is the better form. |
| Source engine console ([Valve wiki](https://developer.valvesoftware.com/wiki/Developer_console), [flags](https://developer.valvesoftware.com/wiki/Console_command_flags)) | Named variables and commands, `bind <key> <command>`, `autoexec.cfg` runs at start. A flag (`FCVAR_CHEAT`) marks variables that only work when the server allows cheats. | A flag per setting that says who may change it. Our "locked" mark is that flag. |

**Changing the interface**

| Program | How it works | What to take |
|---|---|---|
| Firefox `userChrome.css` ([Mozilla](https://support.mozilla.org/en-US/kb/contributors-guide-firefox-advanced-customization)) | A CSS file in a `chrome` folder of the profile, read only when a pref is switched on (off by default). Mozilla does not officially support such rules: the inner markup changes between versions and user files break. | Off until asked for. And the lesson: user CSS needs a small list of names that are promised to stay, or every update breaks it. |
| Obsidian CSS snippets ([help](https://obsidian.md/help/snippets)) | Plain `.css` files in a snippets folder of the vault's configuration folder, each with its own switch in Appearance; edits apply on save. | One switch per snippet. Apply on save. |
| REAPER WALTER ([reaper.fm](https://www.reaper.fm/sdk/walter/walter.php)) | A theme's `rtconfig.txt` places every element of a track or mixer panel by name: `set tcp.mute [0 0 10 10]`, `clear tcp.*`, `front tcp.solo`, with layouts and macros. | Every element has a name (`tcp.mute`). Position and visibility are data in a text file, per layout. (That a zero size hides an element is common practice; unverified from the page.) |
| REAPER menus and toolbars ([user guide](https://dlx.reaper.fm/userguide/ReaperUserGuide681c.pdf), chapter 15) | Options, Customize menus/toolbars: any action can be put on a toolbar or in a menu; sets export as `.ReaperMenu` and `.ReaperMenuSet`. | Toolbars are lists of command ids. |
| Blender ([API overview](https://raw.githubusercontent.com/blender/blender/main/doc/python_api/rst/info_overview.rst), [quickstart](https://raw.githubusercontent.com/blender/blender/main/doc/python_api/rst/info_quickstart.rst)) | The interface is drawn by Python classes (panels, menus). With Python Tooltips on, hovering a button shows the operator behind it; a right-click offers Copy Data Path and the online reference; the Info editor logs what you do as Python lines. | The "pick an element" idea: point at a control and learn its name. And a log that shows each click as a command, which teaches the API by using the program. |

**Commands, keys and macros**

| Program | How it works | What to take |
|---|---|---|
| REAPER Actions list ([user guide](https://dlx.reaper.fm/userguide/ReaperUserGuide681c.pdf), chapter 15; [ReaScript](https://www.reaper.fm/sdk/reascript/reascript.php)) | Everything is an action with a command id (shown with "Show action IDs"). A custom action chains several, with "Consolidate undo points". Keys, toolbars, menus, scripts and control surfaces all call actions. Key maps export as `.ReaperKeyMap`. | The model for part (c), including one undo step per macro. |
| VS Code ([key bindings](https://code.visualstudio.com/docs/getstarted/keybindings), [command palette](https://code.visualstudio.com/api/ux-guidelines/command-palette.md)) | Every command has an id (`editor.action.deleteLines`). `keybindings.json` holds only the user's rules: key, command, and a `when` condition; a `-` before the command removes a default. The built-in `runCommands` runs a list in order. | Namespaced ids. A user file that only holds differences. A `when` field for keys that mean different things in the piano roll and the arrangement. |
| Emacs ([manual](https://raw.githubusercontent.com/emacs-mirror/emacs/master/doc/emacs/m-x.texi)) | "Every Emacs command has a name"; `M-x name` runs it. | The oldest proof that the idea scales. |
| Blender ([API reference notes](https://raw.githubusercontent.com/blender/blender/main/doc/python_api/rst/info_api_reference.rst)) | Every button is an operator with an id such as `object.simple_operator`, called as `bpy.ops.object.simple_operator()`. | One name serves the button, the key, the script and the search. |
| JetBrains ([Find Action](https://jetbrains.com/guide/tips/find-action), [macros](https://www.jetbrains.com/help/idea/using-macros-in-the-editor.html)) | Find Action searches actions and settings together. Recorded macros cover editor actions only, not clicks in dialogs. | Macros are chains of commands, never recorded mouse clicks. |

**Scripts and their limits**

| Program | How it works | What to take |
|---|---|---|
| Figma plug-ins ([how they run](https://developers.figma.com/docs/plugins/how-plugins-run), [manifest](https://developers.figma.com/docs/plugins/manifest), [network](https://developers.figma.com/docs/plugins/making-network-requests), [history](https://www.figma.com/blog/how-we-built-the-figma-plugin-system/)) | The plug-in's code runs in a sandbox with no browser functions at all, only the `figma` API. Network is declared in the manifest (`networkAccess.allowedDomains`, with `["none"]` blocking all); other sites fail. The API version is in the manifest and is not upgraded by itself. The sandbox is QuickJS compiled to WebAssembly, chosen after weaknesses in an earlier approach. A plug-in in an endless loop still hangs the tab ([frozen plug-ins](https://developers.figma.com/docs/plugins/frozen-plugins)). | The model for (e): a tiny API, network only by declaration, a version in the file. And the gap to close: we stop a stuck script by ending its worker. |
| Userscripts ([Tampermonkey](https://www.tampermonkey.net/documentation.php?locale=en), [Violentmonkey](https://violentmonkey.github.io/api/metadata-block/)) | A header block lists what the script wants: `@grant` names each special function, `@connect` names each site; a site that is not listed brings up a question. `@version` drives updates. | The permission card: the script states what it needs at the top, AudioLab asks once per need. |
| Blender add-ons ([extensions](https://docs.blender.org/manual/en/4.5/advanced/extensions/getting_started.html)) | A manifest with `blender_version_min` and declared permissions (`files`, `network`, `clipboard`, …). (That scripts inside a file do not run by themselves when the file is opened is general knowledge; unverified in this run.) | Declared permissions. And K6: a project file never runs code by being opened. |
| REAPER ReaScript ([reaper.fm](https://www.reaper.fm/sdk/reascript/reascript.php)) | Lua, EEL2 or Python with the full API, a built-in editor, and a function list generated inside the program (Help, ReaScript documentation). The page says a script can crash REAPER but should not do permanent damage. No sandbox. | The built-in editor and the generated reference. Not the missing sandbox. |
| Ableton Max for Live ([Live API](https://docs.cycling74.com/userguide/m4l/live_api_overview)) | Objects reach anything by a path such as `live_set tracks 1 mixer_device volume`; changes through `live.object` go into the undo history; a notification may not change the Set directly. | Paths that read like the program's own structure. Script changes belong in undo. |
| Bitwig controller scripts ([user guide](https://www.bitwig.com/userguide/latest/midi_controllers)) | JavaScript files in a Controller Scripts folder. (Details such as `loadAPI(version)` and `host.defineController` are documented only inside the program; unverified here.) | Asking for an API version at the top of a script. |
| Obsidian plug-ins ([security](https://obsidian.md/help/plugin-security), [manifest](https://docs.obsidian.md/Reference/Manifest), [commands](https://docs.obsidian.md/Plugins/User+interface/Commands)) | Restricted mode is on by default and blocks all third-party code. Obsidian states that it cannot restrict a plug-in to particular permissions. `manifest.json` carries `minAppVersion`. Plug-ins add commands with an id; users bind the keys. | Off by default. `minAppVersion`. And the same honesty as EX1 found: without a sandbox, a switch is only a warning. |
| VS Code extensions ([manifest](https://code.visualstudio.com/Docs/extensionAPI/extension-manifest), [activation](https://code.visualstudio.com/api/references/activation-events), [bisect](https://code.visualstudio.com/blogs/2021/02/16/extension-bisect), [proposed API](https://code.visualstudio.com/api/advanced-topics/using-proposed-api)) | Extensions declare what they add (commands, menus, keys, settings) in the manifest and are only loaded when needed. `engines.vscode` names the versions they work with. New API is "proposed" first and cannot be published against. Extension Bisect finds a bad extension by halving. | Declaring UI additions as data. Loading late. A proposed stage before an API is promised. |
| Neovim ([API](https://raw.githubusercontent.com/neovim/neovim/master/runtime/doc/api.txt), [deprecations](https://raw.githubusercontent.com/neovim/neovim/master/runtime/doc/deprecated.txt)) | Configuration is code (`init.lua`). The API contract: a released function's signature does not change, only optional things are added, and each retired function is listed with the level since which it is deprecated. | The promise to make for our API, and how to retire things. |
| Factorio mods ([libraries](https://lua-api.factorio.com/latest/auxiliary/libraries.html), [structure](https://lua-api.factorio.com/latest/auxiliary/mod-structure.html)) | Lua with `io`, `os`, `loadfile` and others removed; `info.json` names the game version and dependencies. | Removing abilities works better than asking for trust. |
| World of Warcraft add-ons ([community wiki](https://warcraft.wiki.gg/wiki/Secure_Execution_and_Tainting), [TOC](https://warcraft.wiki.gg/wiki/TOC_format)) | Add-on code is marked as tainted; protected functions refuse to run from it, and protected frames lock during combat. The TOC file names the interface version, and an older add-on counts as out of date. | A set of actions that user code can never call, enforced by the program. Our locked safety values and protected controls are that set. |

**Safe mode and reset**

| Program | How it starts clean |
|---|---|
| Firefox ([Troubleshoot Mode](https://support.mozilla.org/en-US/kb/diagnose-firefox-issues-using-troubleshoot-mode)) | Help menu, or hold Shift while starting, or `-safe-mode`. It switches off add-ons, themes, hardware acceleration and `userChrome.css`, and deletes nothing. |
| Sublime Text ([safe mode](https://www.sublimetext.com/docs/safe_mode.html)) | `--safe-mode`, or hold Shift+Alt (Windows) or Option (Mac) while starting. It uses a separate, fresh data folder. |
| VS Code ([command line](https://code.visualstudio.com/docs/configure/command-line)) | `--disable-extensions`; Extension Bisect. |
| Neovim, Emacs ([starting](https://raw.githubusercontent.com/neovim/neovim/master/runtime/doc/starting.txt), [options](https://raw.githubusercontent.com/emacs-mirror/emacs/master/doc/emacs/cmdargs.texi)) | `nvim --clean`; `emacs -Q`. |
| REAPER ([user guide](https://dlx.reaper.fm/userguide/ReaperUserGuide681c.pdf)) | A Start-menu entry that resets the configuration to factory defaults; the whole configuration exports as one zip with tick boxes. |
| Ableton Live ([reset](https://help.ableton.com/hc/en-us/articles/209070609)) | Move `Preferences.cfg` out of the Preferences folder by hand. |

**Limits user changes cannot cross in audio programs:** Bitwig and REAPER run plug-ins in separate processes so a crash does not take the program down ([Bitwig](https://bitwig.com/userguide/latest/vst_plug-in_handling_and_options); REAPER user guide 16.16). No DAW was found that documents an output limiter the user cannot switch off; AudioLab's always-on safety stage (EX1 rule 7, question 9A) would be stricter than the field.

**Building blocks for the sandbox** ([Worker.terminate](https://developer.mozilla.org/en-US/docs/Web/API/Worker/terminate): ends a worker at once; [iframe sandbox](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/iframe): a frame without `allow-same-origin` gets an origin of its own; [CSP connect-src](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy/connect-src): blocks `fetch`, XHR, WebSocket and EventSource; [quickjs-emscripten](https://raw.githubusercontent.com/justjake/quickjs-emscripten/main/README.md): a JavaScript engine in WebAssembly with memory, stack and interrupt limits; [Electron security list](https://www.electronjs.org/docs/latest/tutorial/security), which `desktop/main.js` already follows.)

### 9.4 What makes such a layer safe and maintainable

Six things recur in every system above that has lasted. Each becomes a rule for AudioLab.

1. **Stable ids for every control.** REAPER (`tcp.mute`), Blender (operator ids), VS Code (command ids). Firefox's `userChrome.css` is the counter-example: it hooks into inner markup that was never promised, so Mozilla cannot support it. Rule: an id, once released, is never renamed or reused; a retired id stays in an alias table that maps it to its successor.
2. **A registry of commands.** One name per action, used by the button, the key, the toolbar, the macro, the script and the chat box. Then a new feature is reachable from all of them the day it lands.
3. **Layered settings.** Defaults, then the user's, then the project's; the files hold differences only. An update can then improve a default without touching anyone's file.
4. **Validation at every door.** One function per kind of file. Unknown keys are kept and reported, never run (EX1 rule 9). A broken file changes nothing and the last good state stays.
5. **A safe mode that deletes nothing.** Firefox and Sublime both: start as it came, leave the user's files alone. Offered by itself after a start that did not finish.
6. **Versioning.** Every file names its format version; scripts name the API version they were written for; a file from a newer AudioLab is refused with a clear sentence; an old one is upgraded on reading. New API starts as "proposed" (VS Code) and is only promised after a release or two.

A seventh, from the audio side: **a short list that nothing can touch.** The limiter and its ceiling, the output gain cap, the start-up fade, the record light, the master meter, the script time limit. They show in the list with a lock so that the user can see they exist and why.

### 9.5 What exists in the app today (v0.221, read for this task)

| Part | Today | For the deep layer |
|---|---|---|
| Settings | About 190 `UI.*` keys in one object saved under `audiolab-ui`; read and written all over the file; defaults live where each is read. Audit: `docs/settings-audit.md` (about 124 settings in the window and many outside it) | Step S4 (one table with id, label, page, scope, default) is the base of the everything list. The deep layer asks S4 for three more fields: type with range, "has a normal control", and "locked". |
| Actions | `SCA`: 57 entries `{id, g, l, d, ic, run}` (id, group, label, default key, icon, function); `UI.keys` holds the user's keys; four key presets; the list is searchable in Settings | Already a small command registry. It needs: every menu item and button moved in, ids with a namespace (`transport.play` in place of `play`, old ids kept as aliases), and one `runCommand(id)` door. |
| Controls | About 550 `id="…"` attributes with short names (`bPlay`, `bRec`, `trAuto`), and many controls built in template strings without any id (mixer strips, device knobs) | The largest job. Each control gets `data-al="group.name"` from one table; repeated controls (one per strip, one per device) share an id, so one rule covers them all. |
| Customising that exists | Transport modules can be hidden and reordered (`UI.trHide`, `UI.trOrder`, the "Edit…" palette); track header controls (`UI.hcz`); mixer strip parts (`UI.mxOpt`, `UI.mxs`); device panel hiding (`UI.fxHide`) | Four small rule systems, each with its own storage. The rules file replaces their storage with one format; their existing panels stay as friendly editors of the same rules. |
| Assistant | `AITOOLS` with tools that log undoable actions | The script API and the Assistant's tools should be the same functions underneath: one place that reads and changes the project safely. |
| Desktop shell | `contextIsolation: true`, `nodeIntegration: false`, `sandbox: true` | Scripts never get a bridge. The only new desktop piece is reading and writing one customisation folder (K5). |

### 9.6 The design

All seven parts live in the Workshop (EX1 question 3A) and are invisible until used. Names below are proposals.

#### (a) Advanced settings: the everything list

- **The user sees:** one searchable list. Each row: the id (`mixer.meterFps`), a plain sentence, the value with the right editor, the default, the allowed range, a mark for "yours" or "project", a ↺ to reset. Filters: all, changed, no normal control, locked. A choice where a change is written: mine, or this project. Prototype P1.
- **What is in it:** every row of the S4 table, plus the values that are constants in the code today and are worth opening (tooltip delay, double-click time, drag threshold, meter redraw rate, undo depth, voice limit, sleep time, wheel zoom step, …), plus the locked safety values, shown read-only. The 38 "no normal control" rows in the prototype are examples of the kind; the real list is found by reading the code in step DL3.
- **File** `settings.json` in the user's folder; the project part sits inside the `.audiolab` file:

```json
{ "audiolab": "settings", "version": 1,
  "values": { "mixer.meterFps": 30, "ui.tooltipDelayMs": 200, "arrange.trackHeight": 38 } }
```

- **Layers:** default, then user, then project; later wins. A setting marked "computer" (audio device, buffer, interface size, glass level) is refused in the project layer, with a sentence saying why.
- **Checks:** type, range, list of allowed words. An unknown id is kept in the file and shown as "not used" (it may belong to a newer version). A locked id is refused everywhere.
- **Risks:** a value that makes the app slow or odd (a 10 fps meter): bounded by the range, and one ↺ away. Support questions from people who changed something and forgot: the "changed" filter and safe mode answer them. Ids that must then stay for ever: only ids marked stable are promised; rows for internals are marked "may change" and carry no promise.
- **Cost:** none. Today each setting is read from `UI`; after S4 it is read through one table. The list is drawn only when opened.

#### (b) UI rules: hide, rename or move any control

- **The user sees:** right-click any control: "Hide this" and "Customise…" (K12). In the Workshop: "Pick an element", then click anything; its id shows; buttons Hide, Rename, Move earlier, Move later, Reset; a choice between every layout and only the current one; "Show hidden ones faintly" to get things back; the file beside it, editable, with a message line. Prototype P2.
- **File** `ui-rules.json`:

```json
{ "audiolab": "ui-rules", "version": 1,
  "layouts": {
    "all":  [ { "id": "transport.tap", "rename": "Tap tempo" },
              { "id": "mixer.strip.sends", "hide": true } ],
    "mix":  [ { "id": "transport.loop", "before": "transport.record" } ] } }
```

- **Rules:** `hide`, `rename` (24 characters at most, plain text), `before` or `after` another id in the same container. A control cannot leave its container in version 1 (a mixer button cannot move into the transport bar); panels as a whole are placed by the layout settings that exist. An id that covers repeated controls (`mixer.strip.sends`) applies to every strip. Later ideas that need no new machinery: `tooltip`, `icon`, `size: small`.
- **Protected controls** cannot be hidden: the limiter light, the record light, the master meter, the CPU and dropout warnings, the Workshop's own "safe mode" entry and the menu path to Settings. The picker says why.
- **Hidden is not gone:** a hidden button's command still works by key, toolbar and script.
- **Risks:** hiding the way back (answered by the protected list, safe mode, and "what is changed"); a tutorial or the guided tour pointing at a hidden control (the tour must skip steps whose control is hidden); screenshots in help no longer matching; two rules that contradict (applied in file order, the later wins, and the message line says so).
- **Cost:** rules are applied where a panel is built, one lookup in a `Map` per control, and only if the map is not empty. No observers, no polling. With no rules: one `if`.

#### (c) Commands registry

- **The user sees:** a list of every command with its id, name and key; ▶ to run it; click the key to change it; "bar" to put it on a toolbar of their own; "New macro" to chain several. A macro is itself a command (`macro.tidy-clip`) and runs as one undo step. Prototype P3. The same list feeds a command bar (D3c in settings round 1, a later option) and the Assistant.
- **File** `commands.json`, differences only:

```json
{ "audiolab": "commands", "version": 1,
  "keys":    { "transport.metronome": "C", "macro.tidy-clip": "Shift+T", "view.mixer": "" },
  "toolbar": [ "macro.tidy-clip", "track.mute" ],
  "macros":  { "tidy-clip": { "name": "Tidy clip",
               "steps": [ "note.selectAll", "clip.quantize16", "note.velocityDown" ] } } }
```

- **A command** is `{ id, name, group, defaultKey, when, args, run }`. `when` names the place where it applies (arrangement, piano roll, mixer), so one key can do different things in different editors, as today's piano-roll keys already do. Steps may carry arguments later: `{ "do": "note.transpose", "by": 12 }`.
- **Checks:** unknown command in a macro: the macro is kept, marked broken, and does not run. A macro may call a macro, five levels deep at most. A key given twice: the newer wins and the list says which command lost its key (the app's `scRender` already does this for presets).
- **Risks:** a macro that deletes things in one keypress (one undo step puts it back); renamed commands breaking user files (alias table, rule 1 of 9.4); commands that need a selection running with none (each command already checks; the result is a toast, not an error).
- **Cost:** none. The registry is the `SCA` array with more rows; keys are already looked up per keypress.

#### (d) CSS snippets within guard rails

- **The user sees:** a "Snippets" tab: files with a switch each, a text box, examples, and a report of anything left out. Prototype P4.
- **What a snippet may address:** controls by id, `[al="mixer.strip.mute"]`, and a short list of named parts that are promised to stay: `.al-strip`, `.al-track`, `.al-clip`, `.al-meter`, `.al-device`, `.al-panel`, plus the colour variables of the theme format (section 4, stage 1). Anything else in the markup carries no promise.
- **Guard rails:** every rule is rewritten to apply only inside AudioLab's window root and placed in its own cascade layer after the app's; `@import`, `@font-face` and any `url(…)` are left out (no files, no network, no tracking pixels); `position: fixed` is left out; after applying, AudioLab checks that each protected control is still visible and at least a few pixels large, and switches the snippet off with a sentence if not. The glass engine reads its own values and is not reachable from CSS.
- **File:** plain `.css` in `snippets/`, with the on/off state in `settings.json`.
- **Risks:** unreadable text or a control moved off-screen (safe mode; the snippet's switch); slow selectors or heavy filters and shadows that cost frame rate (the report shows the count of rules; a later check can time a frame before and after); breakage after an update (only the promised names are stable, and the report can list selectors that matched nothing).
- **Cost:** one stylesheet, only when a snippet is on.

#### (e) User scripts

- **The user sees:** a "Scripts" tab with an editor, Run and Stop, a console, examples, and the API on one page. A script can run once (tidy something), or stay and add a toolbar button, a menu item or a small panel, or listen to events. Prototype P5.
- **The API, version 0.1 (sketch).** Small on purpose; every name below maps to something that exists.

| Area | Read | Change (collected, checked, one undo step) |
|---|---|---|
| Project | `al.project.tempo`, `.tracks`, `.sections`, `.length` | `setTempo`, `addTrack`, `removeTrack` |
| Track | `id, name, type, color, muted, soloed, volume, pan, devices, clips` | `setName, setColor, setMuted, setSoloed, setVolume, setPan` |
| Clip and notes | `clip.start, length, name, notes`; note `start, length, pitch, velocity` | `clip.set({…})`, `note.set({…})`, `clip.addNote`, `clip.removeNote` |
| Devices | `device.type, name, params` (each with min, max, default, unit from `FXDEF`) | `param.set(value)` inside its range |
| Transport | `al.transport.playing, position, loop` | `play(), stop(), seek(bar)` |
| Selection | `al.selection.track, clips, notes` | `select(…)` |
| Commands | `al.commands.list()` | `al.commands.run(id)` |
| Settings | `al.settings.get(id)` | `al.settings.set(id, value)`, same checks as (a) |
| Interface | | `al.ui.addToolbarButton`, `addMenuItem`, `addPanel` (a panel is a description of rows, sliders and buttons that AudioLab draws; no HTML from the script) |
| Events | `al.on('transport.play' \| 'transport.stop' \| 'selection.changed' \| 'project.saved' \| 'bar', fn)` | |
| Other | `console.log`, `al.storage.get/set` (a few kilobytes per script), `await al.net.fetch(url)` (asks first) | |

- **File:** a `.js` file with a header, the userscript idea:

```js
// ==AudioLabScript==
// @name        Colour tracks by type
// @id          user.colour-by-type
// @version     1.0.0
// @api         0.1
// @runs        once            // or: at start
// @asks        none            // or: network presets.example.org
// ==/AudioLabScript==
const colours = { drums: '#e5534b', bass: '#4c8dff', lead: '#e3b341' };
for (const track of al.project.tracks) track.setColor(colours[track.type] || '#8b8b97');
```

- **How it runs.** The script gets a copy of the part of the project it reads. Its changes are recorded as a list. When it finishes (or when one event handler returns), AudioLab checks every change against the same rules as the interface (ranges, existing ids, locked values), applies the good ones as one undo step named after the script, and prints the refused ones with the reason. The script never holds a live object of the app.
- **The sandbox.** No Node (the window has none to give: `nodeIntegration: false`, `sandbox: true`). No DOM. No network: the frame that holds the script's worker has a content security policy of `default-src 'none'`, so `fetch`, XHR, WebSocket and loading further code fail at the browser's own level. The only route out is `al.net.fetch`, which AudioLab performs on the script's behalf after a permission card names the site (K8). The prototype's worker removes the network functions by hand; that is not a hard wall and is said so on the page. For the app, the choice between a worker inside a sandboxed frame and QuickJS in WebAssembly (Figma's choice, with memory and step limits) should be made with a small test of escape attempts, like the 14 in EX1's `check.js`. This is a design proposal, not something tried in Electron yet.
- **Time limits.** A run is stopped after 2 seconds unless the user chooses to wait (K9); an event handler gets about 50 ms; a script that fails or times out three times in a row is switched off with a note. Stopping means ending the worker, which works even inside an endless loop. The window and the sound never wait for a script: changes arrive as a message, and the audio thread is never called from one. Events such as `bar` are sent at most a few times a second and are dropped, not queued, when a script is still busy.
- **What a script can never do:** touch the locked values; hide a protected control; write to disk outside its small storage; read other scripts; call into the audio worklets; run per sample (that is a script device, EX1 stage 3); run from a project file by being opened (K6).
- **Risks:** a script that makes hundreds of valid but unwanted changes (one undo step; the console says how many); a shared script that asks for the network to send the project somewhere (the card names the site, off by default, and a script without `@asks` cannot ask later); API growth that locks the app's inner structure (the API is a separate, small layer of functions shared with the Assistant, version in every script, "proposed" before promised); support load.
- **Cost:** no worker exists until a script runs. A script that stays costs one idle worker (a few megabytes of memory, no CPU). Each event costs one message.

#### (f) The Workshop page

- **The user sees:** one window (EX1 question 3A), reached from the logo menu and a link at the foot of Settings, hidden until switched on if K4b or K4c is picked. Tabs: Settings list, Controls, Commands, Snippets, Scripts, and EX1's Themes and Devices. Each tab has the tool on the left and the file on the right, as on the pick page. A console at the bottom shows what commands ran ("the Info editor" idea from Blender: click Play and the line `transport.play` appears, which teaches the names).
- **Examples:** each tab ships with a handful that can be opened, changed and saved as the user's own.
- **API reference:** generated at run time from the three lists (settings table, controls table, commands registry) and the script API table, so it cannot go out of date. Search works across all of them.
- **The chat box:** three tools next to EX1's: `write_rules`, `write_macro`, `write_script`. The Assistant shows the file and what it will do, the user presses Accept (K10a), and the result is an ordinary file in the Workshop. "Explain this" works on any file. The rule-based helper without a model can cover the plain cases ("hide the sends", "put quantize on Q"); writing scripts needs a model.
- **Cost:** the Workshop's code is only run when the window opens. If size matters later it can be loaded on first use.

#### (g) Safety

- **Safe mode:** hold Shift while AudioLab starts, or "Restart in safe mode" in the menu, or offered by itself when the last start did not reach the first frame (a flag written at start and cleared when the window is ready). In safe mode nothing of (a) to (e) is read: defaults, no rules, default keys, no snippets, no scripts. Nothing is deleted. A bar across the top says so and offers "Leave safe mode" and "Show what is changed". Prototype P6.
- **What is changed:** one list across all five kinds, each entry with its own ✕. This is also the answer to "why does my AudioLab look different from the video".
- **Reset my customisations:** asks first, keeps a dated backup, and can be undone from the same page.
- **Files:** one folder per user. In the desktop app: `…/AudioLab Pro/customise/` with `settings.json`, `ui-rules.json`, `commands.json`, `snippets/*.css`, `scripts/*.js`, opened with "Show folder". In the browser version: the same content inside the app's storage, with export and import as one file, `audiolab-customisations.json` (this is step S18 of settings round 1 made larger). Audio devices and locked values are never in the export.
- **Locked for ever, in every door:** safety limiter and ceiling range, output gain cap, start-up fade, auto-mute of the EX1 safety stage, the script time limit, protected controls. The check is in one function that the list, the file loader, the CSS check and the script change list all call.
- **A bad file never stops a start:** each file is read in a `try`; on failure it is skipped, the last good copy is used, and a note says which file and which line.

### 9.7 The work in index.html, in small steps

One task per row, run one at a time with the usual release routine, after the picks. **Rows DL1 and DL2 come first and change nothing the user can see.** S4 is step S4 of `docs/settings-round-1.md`.

| Step | Task | Depends on | Visible |
|---|---|---|---|
| S4 | The settings table (already planned). Ask it for type and range, "has a normal control", "locked" | none | no |
| DL1 | Control ids, part 1: a `CONTROLS` table and `data-al` on the transport bar, the mixer strip and the track header. A headless test that fails when a control in these areas has no id or a released id disappears (the list is kept in `docs/ids.md`) | none | no |
| DL2 | Commands registry: grow `SCA` into `COMMANDS` with namespaced ids and an alias table; one `runCommand(id)`; menus and buttons call it | none | no |
| DL3 | Advanced settings list (read and change), with the first batch of opened constants | S4 | yes |
| DL4 | Safe mode, "what is changed", reset with backup | S4 | yes |
| DL5 | Rules engine, hide and rename, right-click "Hide this"; today's four small systems (`trHide`, `hcz`, `mxOpt`, `fxHide`) store through it | DL1 | yes |
| DL6 | Move within a container, per layout, the picker and the file view | DL5 | yes |
| DL7 | Control ids, part 2: devices and their knobs (id from `FXDEF` keys), piano roll, menus, Settings rows | DL1 | no |
| DL8 | Own toolbar and macros; `when` for keys | DL2 | yes |
| DL9 | The customisation folder (desktop) and the one-file export and import | DL3, DL5, DL8; touches desktop/ | yes |
| DL10 | Workshop tabs for the above, with the command console (together with EX1's EX7) | DL3 to DL8 | yes |
| DL11 | CSS snippets with the guard rails | DL1, DL4 | yes |
| DL12 | Script sandbox spike: worker in a sandboxed frame against QuickJS, escape tests, time limit; no user feature | none | no |
| DL13 | Scripts, run once: project read, change list, checks, one undo step, console | DL2, DL4, DL12 | yes |
| DL14 | Scripts that stay: toolbar buttons, menu items, panels, events, permission cards | DL13 | yes |
| DL15 | Generated reference; Assistant tools `write_rules`, `write_macro`, `write_script` with Accept | DL10, DL13 | yes |

If K1a is picked the chain ends at DL10; K1b adds DL11; K1c adds the rest. DL1, DL2, DL4 and S4 are worth doing even if nothing else is: they make the app easier to test and to change.

### 9.8 What it costs in speed

| Part | Unused | In use |
|---|---|---|
| Ids on controls | A few kilobytes of attributes in the markup | The same |
| Settings table | One table lookup where there is a property read today | The same |
| Rules | One empty-map test where a panel is built | One map lookup per control when a panel is built; nothing per frame |
| Commands, keys, macros | As today (`SCA` is already searched per keypress) | A macro costs the sum of its commands |
| CSS snippets | No stylesheet | One small stylesheet; cost depends on what the user writes |
| Scripts | No worker, no frame | One idle worker per script that stays; one message per event; never on the audio thread |
| Workshop | Not built until opened | A normal window |

These are expectations from the design. The frame-time check in `tools/ui-tests/` should be run before and after DL1, DL5 and DL11 to confirm them.

### 9.9 The prototypes (`tools/extension-lab/`)

| File | What it is |
|---|---|
| `extensions-with-deep-layer.html` | **The published pick page**: EX1's page with the part "The deep layer" added. Built by `build_deep.py`; EX1's own file `extensions-round-1.html` is not modified. |
| `deep-layer.html` | The deep layer alone, for testing. |
| `deep-src/` | `part.html`, `part.css`, `02-core.js`, `03-tools.js` (the part), and the small page files for the stand-alone build. All CSS is scoped under `#dlRoot` and all script is in one closure, so EX1's prototypes are untouched. |
| `build_deep.py` | Builds both pages. |
| `deep_check.js` | 73 headless checks over both pages (35 alone, 38 inside EX1's page): each tool's main path, each refusal, safe mode and reset, the picks line, no console errors, no sideways scroll at 1280 and 400 px. |

What each tool shows, and where it is not the real thing:

- **P1 the everything list:** 59 settings, 38 with no normal control, 4 locked. Search, filters, two write targets, range checks, the two files. Eight of the settings really change the mock (accent hue, interface size, track height, clip corners, strip width, animation time, meter redraw rate, clock format). The ids and the hidden options are proposals.
- **P2 pick and change:** 29 controls with ids on the mock's transport bar, strips and master. Hide, rename, move, per layout, ghosts, hand-editing the file with messages for broken JSON, unknown ids and protected controls. One canned "chat box" request.
- **P3 commands and macros:** 35 commands that really act on the mock, key capture with conflict handling, an own toolbar, a macro builder, one undo step per macro.
- **P4 CSS:** three examples; the third is stopped by each guard rail in turn.
- **P5 scripts:** seven examples in a real worker: colour tracks by type, humanise the selected notes, add a toolbar button, an endless loop (stopped at 2 seconds while the mock keeps playing), a network request (permission card; the answer is made up), an attempt on a locked value (refused), and one "written by the chat box" with its explanation. The worker is not a hard sandbox (see 9.6 e).
- **P6 safe mode and reset:** the list of every change from the other five, safe mode on the same mock, reset with a backup, the one-file export.

### 9.10 Decisions on the pick page (★ is the recommendation)

Each tool P1 to P6 gets Yes, Later or No. Then:

| # | Decision | Options | ★ | Reason |
|---|---|---|---|---|
| K1 | How deep | a rules only (P1 to P3); b rules and CSS; c everything including scripts, built in that order | c | Each stage is useful alone and prepares the next |
| K2 | Where it lives | a a page inside Settings; b its own window; c the list in Settings, the rest in a window | b | Settings stays calm; follows EX1 question 3A |
| K3 | Name | a Workshop; b Developer; c Advanced; d Lab bench | a | The name EX1 already uses |
| K4 | Who sees it | a always in the menu; b hidden until a switch; c hidden, but right-click "Hide this" works for everyone | c | Hiding a button is the common wish and needs no Workshop |
| K5 | Files | a inside AudioLab only; b real files in a folder, one export file in the browser; c also reloaded when saved from another editor | b | Files can be backed up, compared and shared |
| K6 | What a project may carry | a nothing; b settings and control rules, never CSS or code; c also scripts, asking on open | b | Opening someone's song must never run code |
| K7 | Sharing scripts and macros | a none; b as a file with a card that shows what it asks and the code; c plus a gallery later | b | Follows EX1 question 6 |
| K8 | Network for scripts | a never; b per script and site, on a card; c on for your own scripts | b | The Figma and userscript model |
| K9 | A script takes too long | a stopped at 2 s; b asks at 2 s: wait or stop; c no limit for your own | b | Long honest jobs finish; the sound never waits either way |
| K10 | Chat box | a writes, shows, you accept; b applies at once; c only explains | a | Nothing changes unseen |
| K11 | Safe mode starts by | a hold Shift; b a menu item; c offered after a failed start (any mix) | a, b and c | The usual door may be the broken thing |
| K12 | Right-click on a control | a "Hide this" and "Customise…" in every right-click menu; b picker in the Workshop only; c Alt+Shift+click | a | The shortest route to the first wish |

The picks line gains a second half, for example: `EX1 picks: 1A 2B 3A 4A 5A 6A 7A 8A 9A | Deep layer | P1 yes, P2 yes, P3 yes, P4 later, P5 yes, P6 yes | K1c K2b K3a K4c K5b K6b K7b K8b K9b K10a K11abc K12a`

### 9.11 What is a guess

- The counts of work are estimates from reading: about 550 ids exist, but how many controls have none (strips, device knobs, menus) was not counted.
- Which constants are worth opening as settings (the "no normal control" rows) is a proposal; each needs a look at the code that uses it.
- The speed table is expected behaviour, not measured.
- The sandbox for scripts in Electron (worker in a sandboxed frame with a strict content security policy, or QuickJS) is designed from the documentation and Figma's account, not tried here; step DL12 is there to find out.
- The 2 second and 50 millisecond limits are starting values.
- Items marked "unverified" in 9.3 could not be opened in this run: Blender's factory start and its rule that scripts in a file do not run by themselves, REAPER's numeric and named command ids and zero-size hiding in WALTER, Bitwig's script API details, the Python remote scripts of Ableton Live, and the exact snippet folder path in Obsidian. None of them carries a design decision.

## Added from the speed and feel picks (UX1, 27 Nov 2026, 22:02 Brussels)

Lane H builds **S7** in its commands registry: a single-key layer (S, M, Q, R, L, [ ], arrows by the grid, Enter), **K** toggles the keyboard piano, "G then M/P/B/D" jumps; plain letters yield to the keyboard piano when it is on; the palette K1 shows the keys. S8 was not picked.
