# AudioLab Pro: glass engine, design picks and next tasks (27 November 2026 planning hand-over)

Written for the scheduling chat: everything decided, measured and researched on 26 November, and a task list that can be split over several agents. **Nothing in index.html was changed by this work.** App version when this was written: v0.217.

Related: `docs/design-language-research.md` (round 1 research and options), `claude/audiolab-liquid-glass-research.md` (Chromium internals, 24 Nov), `claude/audiolab-glass-rebuild-status-3.md` (last Mac measurements).

## 1. What the user decided

**Design round 1 picks:** A0, B0, C1, D3, E0, F4, G2, H0. In words: keep today's overall look, colours, buttons and icons; Inter on the strict scale (11/12/13/15, three weights); **full glass** on panels; **glass mixer strips**; **display-first devices**.

**Must stay as they are (user's words: "the stuff that I originally wanted"):**
- The half pan with a dial in the mixer, the way the mixer header is made, the stereo field displays.
- The whole cable system.
- Fader design **"Flat bars" (the original, design 7), not "Flat bars 2"**. It becomes the standard again.
- Devices: titles stay sideways (vertical) to save height; the black display boxes as large as possible, with floating buttons inside them as in G2.

**Change asked for:** the sidechain outline (sender and receiver strips light up) should show **only when the sender or the receiver is the selected channel**. Cables stay visible as now, unless "Selected only" is on.

**Glass:** the most important thing. Must work "exactly like Apple does it", with refraction, at the highest frame rate and lowest CPU, so everybody can leave it on. Same result on Mac and Windows. Rebuilding from the ground up is allowed.

**Answers given on 26 Nov:**
- Platform: **stay on Electron, build our own glass engine.** Native audio and VST host later, as a separate helper.
- Lens width on big panels: wanted to compare first; now a per-surface setting (see below).
- Source: **go private with our own updates, keep a browser version.**
- Science look: **both** our own visuals drawn in code and real NASA / Webb images with credit.

**Decided after trying the Glass Bench (26 Nov, late):**
- **The GL engine is the glass from now on.** "Lens now" (the SVG lens in `backdrop-filter`) is dropped.
- Three levels only: **GL engine** (normal), **Blur** (plain blur, no lens) as the light version, **Solid** as the absolute lightest. The Performance page and Light mode are rebuilt around these three.
- **Lens width and blur strength are presets, not sliders** (the user does not want to hunt for the fastest value). Lens: Off, Fine (up to 12 px), Apple (up to 20 px), **Wide (up to 45 px, default)**. Blur: **Light (default)**, Regular, Heavy. One choice for the whole app; the width still differs per surface because each preset follows the panel's size (Apple's rule: a quarter of the short side up to the preset's maximum), so the 48 px transport gets a 12 px lens, the track headers 20 px, a pill 8 px.
- **Defaults chosen by the user (27 Nov): lens Wide at 45 px, blur Light.** The Wide preset's maximum is therefore 45 px (a third of the short side up to 45: track headers and big panels 45, the 48 px transport 16, a 32 px pill about 11). These two are the app's defaults; the other presets stay as choices in Settings.
- **Do the presets differ in speed? Measured: no.** Each preset timed three times at 1600x1000 on the cloud machine (software renderer, so only the comparison counts): lens off 53 to 60 ms, fine 55 to 59, Apple 55 to 60, wide 58 to 63, blur light 53 to 60, regular 53 to 58, heavy 57 to 70. All inside the run-to-run noise, with heavy blur possibly a little dearer. This matches the design: the lens is the same single lookup per pixel at any width, and each extra blur level works on a quarter of the pixels of the one before. So the presets are a matter of taste; the real speed steps are GL engine, Blur, Solid, and later the size and refresh rate of the shared backdrop. The Glass Bench has a "Compare presets" button that checks this on a real GPU (it counts how many times the whole glass fits into one screen frame).
- **Corner artifact fixed in the bench shader** (a line from each corner toward the middle): the lens used the panel's own corner radius, so on square or tightly rounded panels the bending direction flipped along the corner diagonal. The lens now uses its own distance field with a corner radius of at least the lens width, and the direction is computed directly instead of from four extra samples, so it is cheaper than before, not dearer. The engine (task G2) must take this shader as its starting point.

**Design philosophy (new, user's words):** scientific. The atom logo, Caltech, JPL, Jupiter, Hubble, the James Webb telescope, measurements, "mathematical beauty". The app should feel "smart and sciencey, clear, intuitive, snappy".

## 2. What was found

### 2.1 Where the glass cost is today (audit of v0.217 + benchmark)

Benchmark caveat: the cloud machine has no GPU, so numbers are from Chromium's software compositor. The ranking and the damage findings should carry over; absolute numbers and "the lens is nearly free" must be re-measured on the Mac.

| Finding | Evidence |
|---|---|
| **Idle is not idle.** The logo glow animation (`#bLogo`, `logoGlow`) lives inside the transport's glass element, so the full-width lens and blur are re-run on every display frame, also when stopped. | Capped 60 Hz run: compositor work 545 ms/s with glass, 102 ms/s without, 140 ms/s with only the transport's filter off, 133 ms/s with only the glow stopped. |
| **The mixer window is the biggest single cost**, with no lens at all: 588,000 px of live 27 px blur over an arrangement that repaints every playing frame, 61 meter canvases inside, plus glass on glass (its tab `.fwh`, and a 1.6 px blur on each pan handle `.ck`, which is in Skia's expensive band). | Removing its glass saved 28 to 32 ms of a 44 ms glass cost per frame in the software run. |
| **Area times blur is the cost; the lens was about 5 % in software.** Refraction off saved 0.5 to 4 ms of 16 to 68 ms. | Needs the Mac: the user's experience is that refraction off is clearly snappier there. |
| **Follow "center" is the default** and marks the arrangement dirty every frame, so a full redraw plus the half-size backdrop copies (`gbCopy`, `abDraw`) run every playing frame. The playhead is not a separate layer. | Code, lines about 4435 and 19820. |
| Meters (up to 120/s), time text and the CPU graph are children of the transport glass. | Code. |
| Menus, sheets and windows stack glass on glass; there is no budget for the number of glass surfaces. | Code. |
| Already good: small cached lens maps, one filter list per panel, `#arr` clipped under docked glass with a half-size picture behind it, device panel on a pre-blurred picture. | Code. |
| Last Mac numbers (M4 mini, 240 Hz): v0.152 135 fps paused with the device panel as lens + blur; v0.153 240 paused with it solid; dips to 118. **Nothing measured on the Mac since v0.153.** | Status doc 3. |

### 2.2 How Apple does it (documented by Apple, or reverse-engineered by others; the numbers are reverse-engineered and from two sources that could not be cross-checked)

1. Glass is drawn outside the app, by the system compositor.
2. **One backdrop capture per group of glass**, not one per element. Glass never samples glass.
3. The backdrop is captured at **quarter resolution (macOS 26) or half (iOS 27)**.
4. Blur is done by picking a level of a small pyramid, not by a wide kernel.
5. **One shader pass** per group does refraction, blur, colour and shadow. Highlights are two cheap extra layers.
6. **Refraction is only in a rim**: quarter-circle profile, band `min(d/4, 20)` points where d is the short side. Large panels have a flat frosted middle. Size effects stop growing at 160 points.
7. Large glass is more opaque; text-heavy glass gets more frost; the content layer gets no Liquid Glass at all.
8. Cost in one independent test: about twice the old blur material.

Useful numbers: face colour matrix dark 0.125 / 1.125 / saturation 1.3; rim light at 0° and 180° (iOS 27) or +45° and −135° (macOS 26), amount 0.5, about 0.5 pt wide; shadow offset (0, 8), radius 4 + 20t, opacity 0.04 + 0.56t dark (t = clamp((d − 64)/96, 0, 1)); chromatic aberration only while pressed; springs (damping, response): menu open 0.75 / 0.35 s, close 0.80 / 0.49 s, interactive 0.85 / 0.15 s.

So "exactly like Apple" and "cheap" point the same way: a shared low-resolution backdrop, a rim lens, no glass on glass.

### 2.3 Why Chromium's `backdrop-filter` cannot get there

Every glass element runs its own capture and blur. Chromium does keep the result when nothing under it changed, but any change under, inside or over the panel re-runs the whole panel, and in a DAW something always changes while playing. No Chromium 157 to 160 work on this was found.

### 2.4 The engine to build ("AudioLab glass engine")

Our own shader, the same code on Mac and Windows, using Apple's recipe rather than Apple's system glass (which does not exist on Windows and cannot be placed inside a web page anyway).

1. One WebGL2 canvas over the arrangement. **No `backdrop-filter` anywhere in the app.**
2. The arrangement picture goes into one texture. One **dual-Kawase pyramid** is built from it at half or quarter resolution, **only when the picture under glass changed**. (Dual filtering: fastest of the tested blurs in ARM's study, about 7 % of the memory traffic of a Gaussian.)
3. Every glass surface is one quad in one shader: rounded-rectangle distance field, rim refraction with Apple's profile, face colour matrix, tint, rim light. DOM controls sit on top with no filter.
4. Moving a window costs one quad redraw; the pyramid is not rebuilt.
5. Quality steps for weak machines: smaller pyramid, backdrop refreshed at 30 or 60 per second while panels still move at screen rate, then a static tint with noise (what Windows Acrylic falls back to).
6. WebGL2 first, not WebGPU (Figma found no clear win and mid-session failures on Windows).

**Known gap:** glass that floats over DOM (the mixer window over the device panel's knobs, a menu over a window) cannot see that DOM. Options, in order: (a) feed the engine a flat picture of what is underneath (panel colour, device displays are canvases and can be fed directly), (b) HTML-in-Canvas, which shipped in Chrome 157; Electron 45 is on Chromium 156, Electron 46 alpha is on 160, so this arrives with the next Electron major.

**If the app ever goes native:** the same shader ports to Metal and Direct3D almost line for line. Nothing in this engine is thrown away.

### 2.5 Glass Bench (ready for the user's Mac)

- Page: https://claude.ai/artifact/PvnyAiQHa3LSAuANE5o5G4 and `tools/glass-lab/glass-bench.html` (open it in Chrome, and if possible inside the AudioLab desktop app, full window).
- Draws AudioLab-sized panels (track headers, transport, device panel, moving mixer window, pill) over a scrolling arrangement in four ways: Solid (the ceiling), Blur only, Lens now (today's SVG lens), GL engine (a small version of 2.4, uploading the 2D canvas every frame, which is the cautious variant).
- "Run" measures each for 5 s and gives a table to copy. "Lens width" slider: 20 px is Apple's, up to 80 px, for the open question in section 1.
- Per-surface benchmark of the real app: `tools/glass-lab/bench.py` (+ `common.py`, `report.py`); on a machine with a GPU: `ALAB_HEADED=1 ALAB_ARGS="" ALAB_INDEX=/path/index.html python3 bench.py`.
- Only checked here that all four modes draw correctly; the cloud has no GPU, so its frame rates mean nothing.

### 2.6 Native Mac and Windows software: the honest answer

- A full native rewrite is not needed for the glass and would cost far more usage: about 3.4 MB of working JavaScript (engine, every device, every editor) redone in C++ or Swift, builds and tests through CI instead of in seconds, and the cloud sessions cannot run or screenshot a Mac app, so every visual check would go through the user. Ongoing work would also cost more per change.
- VST hosting does need native code. The usual way is a native audio engine and plug-in host (C++, JUCE) beside the existing interface. That can start when VST support starts, without rewriting the interface.
- Closed source: JavaScript in a browser version is always readable (minified at best). A private repo plus a desktop app is "mostly closed". Compiled native code is the most closed.

### 2.7 Going private: what breaks if the repo is simply switched to private

The desktop app's updater reads `index.html` and `app-version.json` **from the public GitHub repo** (GitHub API, then raw.githubusercontent.com). A private repo answers 404 there, so every installed app would stop updating, and a GitHub Pages web version stops unless the plan allows private Pages. **Do not flip the repo to private until the update feed has moved.** Order: (1) set up our own update address (a small static host or bucket: `app-version.json`, the program file, installers); (2) ship an app version that reads the new address first and the old one second; (3) wait until users have it; (4) switch the repo to private; (5) host the browser version from the same place, built with a minify step. Code signing for Mac and Windows belongs in the same piece of work (it also allows the normal updater on the Mac).

### 2.8 Science look: sources and rules

- The YouTube video sent as an example (Ridddle, "Jupiter Is Not a Planet") could not be watched from here, and its own graphics belong to the channel: not usable. The screenshots show the taste: field lines around Jupiter, orbit rings on a dark grid, small capital mono labels in amber, thin lines, a date stamp.
- NASA and JPL-Caltech images are generally free to use with a credit line and without implying endorsement or using NASA logos; Webb images (NASA, ESA, CSA, STScI) likewise with credit. Each image's own page must be checked before use, because some carry third-party rights.
- Our own visuals in code fit best (tiny, animated, no licences, same family as the atom): dipole field lines, orbits and resonances, wave interference, Lissajous and harmonograph curves, spectrograms of the user's own project. They can run on the glass engine's canvas.

## 3. Tasks

Rule for parallel work: **index.html is one file.** Tasks that edit it must run one after another (each: `git pull --rebase`, small commits, the existing UI tests, Fractals demo levels unchanged: Kick −9.75669 dB, Bass −25.48699 dB). Tasks marked "parallel" touch other files only.

| # | Task | Touches | Parallel? | Depends on |
|---|---|---|---|---|
| U1 | **User:** run the Glass Bench on the Mac (Chrome; scrolling, mixer moving, all panels), copy the table; then "Compare presets" and copy that table too. | nothing | yes | none |
| G1 | **Quick wins in today's glass**, each measured before and after with `tools/glass-lab/bench.py`: move the logo glow, meters, time text and CPU graph out of the transport's glass element (sibling layer, as `#fxglass` does); remove glass on glass in the mixer (`.fwh`, the 1.6 px `.ck` blur); playhead as its own layer; Follow centre without a full redraw and backdrop copy per frame; mixer window and sheets on the picture blur; pointer capture on window drags. | index.html | serial | none |
| G2 | **Engine as a stand-alone module** in `tools/glass-lab/`: the design in 2.4 with Apple's numbers from 2.2, starting from the shader in `tools/glass-lab/glass-bench.html` (corner fix and presets included), an API (register a panel with rectangle, radius, kind; set backdrop sources; mark dirty), context-loss recovery, fallbacks (plain tint), Reduce Transparency and Increase Contrast behaviour, quality steps, a test page with AudioLab-sized panels. No code copied from the reverse-engineering repos (no licence given); numbers only. | tools/ only | **parallel** | none (U1 result tunes it) |
| G3 | **Integrate behind a switch** "Glass engine (preview)" in Settings: arrangement as backdrop; track headers, transport, tab band and device panel first; then floating windows; then menus and sheets (2.4 gap, option a). Old glass stays as the fallback. | index.html | serial | G2, U1 |
| G4 | After the user confirms on the Mac: remove `backdrop-filter` and the SVG lens, rebuild the Performance page around three levels (GL engine, Blur, Solid) plus the lens and blur presets (no sliders). | index.html | serial | G3 |
| G5 | Electron: check real 240 Hz pacing in the shipped app; plan the move to Electron 46 (Chromium 160, HTML-in-Canvas) when it is stable. | desktop/ | parallel | none |
| D1 | "Flat bars" (design 7) is the default again; undo the one-time migration for people it moved to "Flat bars 2", without overriding anyone who chose 2 themselves afterwards if that can be told apart (else ask). | index.html | serial | none |
| D2 | Sidechain outline only when the sender or receiver is selected (`abxLights`, about line 17288); cables unchanged; "Selected only" unchanged. | index.html | serial | none |
| D3 | Type scale C1: Inter at 11/12/13/15, weights 400/500/600, equal-width digits. | index.html | serial | none |
| D4 | Display-first devices (G2): pick page done and picked; **the spec is `docs/devices-display-first.md` section 7** (eye opens the glass rail; closed shows hover reveal, or on the picture by right-clicking the eye; per-device starting states; applies to future devices too). Now implement device by device. | page: parallel; index.html: serial | | engine for the floating glass |
| D5 | Glass mixer strips (F4), keeping the half pan dial, header, stereo displays, cables and Flat bars. | index.html | serial | G3 |
| D6 | Science look: pick page with splash and About backgrounds drawn in code plus a shortlist of NASA / Webb images with credit lines and licence notes. | page only | **parallel** | none |
| S1 | Own update feed, then private repo, then browser build (order in 2.7); code signing plan. Needs the user's choices on hosting and accounts. | desktop/, CI | parallel (plan); careful (rollout) | none |
| N1 | Later: research note on a native audio engine and VST host beside the interface. | docs only | parallel | none |

Suggested order for index.html work: D2, D1 (small, asked for directly), G1, D3, then G3 once G2 and U1 are in.

### 3.1 Go-ahead and notes for whoever implements (added 27 Nov)

**The user approved implementation** ("Let's start implementing it into AudioLab as best as possible, in a smart way; snappiness and CPU speed are the most important thing, together with the effects and the sound engine") and asked that the scheduling chat split and run the tasks. No implementation was started in the planning session; index.html is untouched by it.

How to fit the engine into what exists (from the audit; line numbers are for v0.219 and will drift):
- The app already keeps "pictures behind glass": `#arrBack` (a half-size copy of the arrangement, made by `gbLayout`/`gbCopy`/`gbTick`, about line 9086) and `#arrBlur` (a pre-blurred picture for the device panel, `abDraw`, about line 10709). `#arr` itself is clipped away under docked glass (`gbClip`). **The engine's canvas takes the place of these two pictures**: one WebGL2 canvas inserted where `#arrBack` sits (before `#arr`), drawing the finished glass faces for the docked surfaces. The DOM elements (`#hglass`, `#tr`, `#fxband`, `#fxglass`) then carry no `backdrop-filter`, only their border and content.
- Source for the engine: the arrangement canvas. Upload it only when `drawArr` actually repainted; a playhead-only frame should not rebuild the blur (draw the playhead as its own thin layer, or accept it unblurred under glass).
- **Step 1: docked surfaces only** (track headers, transport, tab band, device panel). They are always on screen and decide the idle and playing frame rate. Do the G1 fixes in the same step where they touch the same code (logo glow, meters and time text out of the transport's glass element; Follow centre).
- **Step 2: floating windows, sheets and menus.** One more engine layer directly under the floating layer, or a face per window; where a window covers DOM, feed the flat picture (plan 2.4). Remove the nested blurs in the mixer.
- **Step 3: remove the old path** (`rfAttach`, `rfBuild`, `rfMap`, `rfStyle`, the `feImage` lens, `elTick`'s read-back if no longer needed) only after the user confirms on the Mac. Until then the old path is the fallback when WebGL2 is missing or the context is lost.
- Settings: three levels (GL engine, Blur, Solid) replace Full / Optimised / Lighter / Lightest; `UI.pm` and `UI.fx` must migrate existing choices (Full and Optimised to GL engine, Lighter to Blur, Lightest to Solid). Lens preset (Off, Fine, Apple, Wide) and blur preset (Light, Regular, Heavy) as plain choices. Automatic stepping-down stays, now between the three levels.
- Nothing in the audio path changes. Check the Fractals levels and the existing glass tests (`tools/ui-tests/glass*.py`) after each step; headless machines have no GPU, so frame rates there prove nothing: correctness and "no backdrop-filter left on docked surfaces" are what can be tested, the frame rate is the user's to confirm.
- The release routine and editing rules are the ones in the existing task prompts (new JS before `function askChoice(`, new CSS before `.dacv{display:flex;`, Python edit scripts with unique-replacement asserts, `git pull --rebase`, version bump, `sync-app.js`, update note, backlog log, project doc, notification, artifact).

### 3.2 First numbers from the user's Mac (27 Nov) and what they change

M4 Mac mini, Chrome 157, **3840x2027 window (7.8 megapixels) at 240 Hz**, arrangement scrolling, mixer moving, all five panels, lens Wide, blur Light, first version of the bench engine (half-size backdrop, 2D canvas uploaded and blurred on every frame):

| Mode | fps | median ms | 95 % ms | worst ms |
|---|---|---|---|---|
| Solid | 240 | 4.20 | 4.60 | 4.7 |
| Blur (plain `backdrop-filter` blur) | 240 | 4.20 | 4.50 | 4.8 |
| GL engine, first version | **198** | 4.20 | 8.40 | 8.8 |

Preset test (how often the whole glass fits in one 4.2 ms frame): only "blur light" reached x2; every other preset x1.

What this says, honestly:
- **The first engine version is not yet faster than Chromium's plain blur at this size.** It drops about one frame in six. At 7.8 megapixels and 240 Hz one full-screen pass is already 1.9 billion pixels a second, and the frame budget is 4.2 ms.
- Plain blur holding 240 here is for four plain panels with nothing drawn inside them; the app's real glass (lens, content inside, glass on glass, the mixer's meters) is what fell to 135. So this does not mean "use plain blur"; it means the engine has to be cheaper than its first version.
- **Blur strength does matter on a real GPU** (light fits twice, regular once). The earlier "no measurable difference" came from the cloud's software renderer and was wrong for the Mac. Lens width still shows no difference.
- The preset test was too coarse (x1 or x2 only). Bench 2 reports the share of frames delivered instead.

Where the first version spends its time, and the fixes now in **Bench 2** (same page, `tools/glass-lab/glass-bench.html`):
1. **Quarter-size backdrop** (what macOS itself uses): the blur starts from a quarter-size copy made by the GPU's own mipmaps. About a quarter of the blur work.
2. **Backdrop refreshed every 2nd or 4th frame** while panels still move on every frame: at 240 Hz that is a 120 or 60 per second backdrop under frosted glass, where it cannot be seen. Halves or quarters upload and blur again.
3. Two check rows: "no upload" (is copying the 2D canvas into the GPU the cost? If yes, the arrangement must be drawn in WebGL or uploaded only on change) and "layer only" (what the extra full-screen layer costs with the engine doing nothing).

**Requirement for the engine (task G2 and glass step 1): on this Mac at this window size it must deliver 100 % of frames with room to spare, or it is not ready.** Design consequences already clear: quarter-size backdrop by default; backdrop refresh decoupled from the screen rate (default every 2nd frame at 240 Hz, every frame at 60 Hz); never upload or blur on a playhead-only frame; keep the engine's canvas no larger than the glass it draws if "layer only" turns out to cost frames. The Bench 2 table from the Mac decides the rest.

### 3.3 Bench 2 on the user's Mac (27 Nov, four runs): the cost is the upload, not the blur

Same Mac, same 3840x2027 window at 240 Hz, lens Wide, blur Light. Share of frames delivered, four runs:

| Mode | Run 1 | Run 2 | Run 3 | Run 4 |
|---|---|---|---|---|
| Solid | 100 | 100 | 100 | 100 |
| Blur (plain `backdrop-filter`) | 100 | 100 | 100 | 100 |
| GL, half-size backdrop, every frame | 85 | 83 | 82 | 83 |
| GL, quarter-size backdrop, every frame | 85 | 84 | 82 | 84 |
| GL, quarter-size, backdrop every 2nd frame | 90 | 96 | 90 | 100 |
| GL, quarter-size, backdrop every 4th frame | **100** | **100** | **100** | **100** |
| Check: no upload (blur and all panels still drawn every frame) | **100** | **100** | **100** | **100** |
| Check: layer only | 100 | 100 | 100 | 100 |

Reading:
- **The blur pyramid and the glass shader are cheap.** With the upload switched off, the whole glass is drawn on every frame at 7.8 megapixels and 240 Hz without losing a frame (95 % frame time 4.2 to 4.3 ms, as good as Solid).
- **Copying the full-size 2D arrangement canvas into the GPU (`texImage2D` from a 7.8 megapixel canvas) is what drops frames.** Half-size and quarter-size blur behave the same, which confirms the blur is not the cost.
- The extra full-screen engine layer costs nothing measurable.
- Uploading 60 times a second (every 4th frame at 240 Hz) holds every frame; 120 times a second is borderline.

**Rules for the engine that follow (binding for G2 and glass step 1):**
1. **Never upload the full-size arrangement canvas per frame.** In order of preference: (a) draw the backdrop on the GPU directly as a small proxy: the clips as flat coloured rectangles, straight into the quarter-size target (under frosted glass nothing finer can be seen); (b) upload a quarter-size copy of the arrangement (the app already makes a half-size copy, `#arrBack`); (c) upload the full canvas at most 60 times a second.
2. Blur and glass may run on every frame; they are not the bottleneck.
3. Bench 3 (`tools/glass-lab/glass-bench.html`, link below) has (a) and (b) as rows "GL drawn on GPU" and "GL small copy", each on every frame. The user's run of Bench 3 decides between them. Only checked in the cloud that both draw correctly.
4. If the G2 module was built around a per-frame full-size upload, change its source to (a) or (b) before it is integrated.

Bench 3: https://claude.ai/artifact/68cA3L4uNaJ5jE3kmZeQas

## 4. Open questions for the user

1. (Answered: Wide 45 px and Light.)
2. The Glass Bench frame-rate table from the Mac (not received yet; the user reported that the GL engine "looks very good").
3. Where should updates and the browser version be hosted once the repo is private (own domain, which provider)? Are Apple and Windows signing certificates wanted now?
4. Menus and windows over other glass: Apple never lets glass sample glass. Is "the top glass shows the arrangement and a flat picture of the panel under it" acceptable until HTML-in-Canvas arrives?

## 5. Sources (opened on 26 Nov 2026 by research helpers; pages were read through a fetch tool that summarises, Apple pages as raw text)

Apple and reverse engineering: [WWDC25 219](https://developer.apple.com/videos/play/wwdc2025/219/), [323](https://developer.apple.com/videos/play/wwdc2025/323/), [284](https://developer.apple.com/videos/play/wwdc2025/284/), [310](https://developer.apple.com/videos/play/wwdc2025/310/), [Applying Liquid Glass to custom views](https://developer.apple.com/documentation/swiftui/applying-liquid-glass-to-custom-views), [HIG Materials](https://developer.apple.com/design/human-interface-guidelines/materials), [ShatteredGlass](https://github.com/AlexStrNik/ShatteredGlass), [GlassExplorer](https://github.com/ktiays/GlassExplorer), [liquid-gpu](https://github.com/nshelia/liquid-gpu), [sspai on the implementation](https://sspai.com/post/100983), [CABackdropLayer notes](https://medium.com/@avaidyam/capluginlayer-cabackdroplayer-f56e85d9dc2c).

Algorithms and Chromium: [Bjørge, SIGGRAPH 2015 (dual filtering)](https://community.arm.com:443/cfs-file/__key/communityserver-blogs-components-weblogfiles/00-00-00-20-66/siggraph2015_2D00_mmg_2D00_marius_2D00_notes.pdf), [Intel fast blur study](https://intel.com/content/www/us/en/developer/articles/technical/an-investigation-of-fast-real-time-gpu-based-image-blur-algorithms.html), [frost.kiwi on dual Kawase](https://blog.frost.kiwi/dual-kawase/), [Grida: Chromium effect optimisations](https://grida.co/docs/wg/research/chromium/effect-optimizations), [HTML-in-Canvas](https://developer.chrome.com/docs/web-platform/html-in-canvas), [Electron releases](https://releases.electronjs.org/), [Figma on WebGPU](https://www.figma.com/blog/figma-rendering-powered-by-webgpu/), [Flutter BackdropGroup](https://api.flutter.dev/flutter/widgets/BackdropGroup-class.html), [Microsoft: Acrylic](https://learn.microsoft.com/windows/uwp/style/acrylic), [Microsoft: Mica](https://learn.microsoft.com/windows/apps/design/style/mica), [Skia Graphite](https://blog.google/chromium/introducing-skia-graphite-chromes/).

Not found or not confirmed: Apple's re-sampling policy (every frame or on change); what Apple does on old devices; the Chromium 60 fps cap bug on macOS (page needs a sign-in); any published frame-rate numbers for web liquid-glass libraries that can be trusted.
