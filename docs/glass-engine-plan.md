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

### 3.4 Bench 3 on the user's Mac (27 Nov, one run): decided, the backdrop is drawn on the GPU

Same Mac, 3840x2027 at 240 Hz, lens Wide, blur Light, arrangement scrolling, mixer moving:

| Mode | fps | frames delivered | 95 % ms | worst ms |
|---|---|---|---|---|
| Solid | 240 | 100 % | 4.60 | 4.8 |
| Blur (plain `backdrop-filter`) | 240 | 100 % | 4.70 | 4.8 |
| GL, full-size upload every frame (half or quarter blur) | 200 to 202 | 84 to 85 % | 8.40 | 8.9 |
| GL, quarter, upload every 4th frame | 240 | 100 % | 4.70 | 4.8 |
| GL, small (quarter-size) copy uploaded every frame | 237 | about 100 % | 4.60 | 8.4 |
| **GL, backdrop drawn on the GPU, every frame** | **240** | **100 %** | **4.60** | **4.8** |

**Decision: the engine draws its own backdrop on the GPU** (clips as flat coloured rectangles straight into the quarter-size target, then the blur pyramid, then the glass, all on every frame). At 7.8 megapixels and 240 Hz it is indistinguishable from Solid in this test: no dropped frames, same worst frame. The small-copy upload is the fallback (it loses an occasional frame: worst 8.4 ms). A full-size upload is not allowed.

What the proxy must contain in the real app (keep it this small): the track lane background, each clip's rectangle in its track colour (body and title band), selection tint if cheap, and the playhead line. No waveforms, notes, text or grid: under frost they cannot be seen. It is rebuilt from the same clip geometry `drawArr` uses, only when the view or the clips change (scroll, zoom, edit), and the playhead is one extra rectangle. For glass over other things than the arrangement (piano roll, device displays) use the small-copy route for that source.

Caveat: one run, on a test page, in Chrome 157; the app runs in Electron's Chromium 156. The first real check is glass step 1 in the app on this Mac.

### 3.5 The Light level also uses the engine (27 Nov)

The user saw a slight flicker (shimmer, like aliasing) in the background of the **Blur** mode on the bench while the arrangement scrolled, and none in the GL engine. Blur mode is Chromium's `backdrop-filter: blur()`, which blurs a reduced copy with a cheap filter; moving sharp edges shimmer through it. It cannot be tuned from the page.

So the three levels become:
- **Glass**: the engine with lens (default Wide 45, blur Light).
- **Light**: the same engine with the lens off and a cheaper backdrop (smaller, refreshed less often, for example 30 per second). No `backdrop-filter`.
- **Solid**: no glass. Also the fallback when WebGL2 is not available.

`backdrop-filter` is then used nowhere in the app. On the bench, Light corresponds to the GL engine with Lens set to off.

### 3.6 Engine 2.0 test on the user's Mac (27 Nov) and engine 2.1 (task G2c)

The user ran the engine 2.0 test page (`tools/glass-lab/engine-test.html`) on the Mac: M4, Chrome 157, ANGLE Metal, 3840x2027 at 1x, 240 Hz, mixer moving, panels hdr tr band dev mix menu pill, lens Wide, blur Light.

| Mode | fps | frames delivered | median ms | 95 % ms | worst ms | GPU background per s | uploads | lists |
|---|---|---|---|---|---|---|---|---|
| Solid | 219 | 92 % | 4.20 | 8.30 | 8.9 | 0 | 0 | 0 |
| Light, drawn on GPU | 217 | 91 % | 4.20 | 8.30 | 8.8 | 60 | 0 | 0 |
| **Glass, drawn on GPU (scrolling)** | **160** | **67 %** | **7.80** | 8.50 | 8.9 | 319 | 0 | 0 |
| Glass, drawn on GPU, playing | 222 | 93 % | 4.20 | 8.30 | 8.4 | 444 | 0 | 0 |
| Light, small copy | 210 | 88 % | 4.20 | 8.40 | 8.9 | 0 | 60 | 0 |
| Glass, small copy | 187 | 78 % | 4.20 | 8.40 | 12.5 | 0 | 120 | 0 |

For comparison, Bench 3 on the same Mac (3.4): Solid 240 fps 100 %, and "GL, backdrop drawn on the GPU, every frame" 240 fps 100 % with worst 4.8 ms, scrolling with the mixer moving.

**Reading.**
1. Uploads and lists are 0, as required.
2. Glass while scrolling keeps 67 % (median 7.8 ms: every second frame missed). Glass while playing keeps 93 %, the same as Solid on this page, although the background is drawn more often (444 against 319 per second). So drawing the background is not the problem as such.
3. Solid keeps only 92 % on this page against 100 % on Bench 3. The page itself was heavier than Bench 3, so its ceiling was wrong.

**What comparing the engine 2.0 code with the Bench 3 code showed** (suspect by suspect; the cloud machine has no graphics card, so this is from reading the code, not from measuring):

| Suspect | Finding |
|---|---|
| Anti-aliasing in the rectangle shader costs many samples | **No.** It is not multi-sampling and not a box filter over samples. The shader works out, from the rectangle's own edges, how much of the pixel is covered: a few multiplications, one result per pixel, no texture lookup. The comment near line 62 was misleading and is rewritten. A switch on the test page turns it off to prove it. |
| Background larger than quarter size, or two layers at full cost | Quarter size (960x507 here). But there **are** two layers and each is its own WebGL context, so each draws its own background and blur: 444 per second is 2 x 222. In 2.0 the background colour and the lanes were blended rectangles over the whole small target (about three layers of overdraw where Bench 3 has a clear and opaque clips). 2.1 removes one of them: the background colour is now the clear. |
| Pyramid larger or more passes while scrolling | **No.** With blur Light it is one same-size pass (8 lookups per small pixel); Bench 3 does one pass down and one up. Scrolling and playing are the same work for the engine: one number each. |
| Extra work in `setView` | **No** state changes, buffer uploads, `getError`, `readPixels`, `finish` or `flush` anywhere on the frame path. One thing was found: the area under docked glass was worked out again on every frame, with a few dozen small arrays thrown away per frame at 240 per second. 2.1 works it out only when a panel changes. |
| Canvas size or devicePixelRatio | The size is right (1x, 3840x2027). But the engine page has **two full-window engine canvases** where Bench 3 has one, and both are cleared, redrawn and handed to the compositor on every frame while scrolling. |
| The menu and pill panels | One small quad each, no full-screen pass. The second **layer** is what adds full-screen work, not these panels. |
| The test page | **Yes, for Solid.** On the engine page Solid kept both engine canvases on screen and redrew the floating one on every frame (the mixer moves). Bench 3's Solid has no GL canvas at all. 2.1's Solid row is now the same as Bench 3's. |

**The reading that fits all six rows.** What differs between "Glass, playing" (93 %) and "Glass, scrolling" (67 %) is not inside the engine. It is the page: while scrolling, the 7.8 megapixel 2D arrangement canvas is redrawn in full on every frame (as the app does); while playing it stands still. So:

| Row | Full-window canvases redrawn per frame | Kept |
|---|---|---|
| Bench 3, GL drawn on GPU | 2D arrangement + one GL layer | 100 % |
| Engine page, Glass playing | two engine layers | 93 % (the page's ceiling then) |
| Engine page, Light scrolling | 2D arrangement + floating layer, docked layer 30 per second | 91 % |
| Engine page, Solid scrolling | 2D arrangement + floating layer | 92 % |
| **Engine page, Glass scrolling** | **2D arrangement + both engine layers** | **67 %** |

Two full-window surfaces per frame fit into 4.2 ms on this Mac; three do not. **This is an inference, not a measurement.** The code cannot say whether the third surface costs because of its pixels (two more 7.8 megapixel layers for the compositor), because of its backdrop and blur work, or because a second WebGL context costs a fixed amount per frame. The next run decides (below).

**What changed (engine 2.1.0, test page; `index.html` and `desktop/` not touched, API kept).**

Engine, on by default:
- The scene's background colour is the clear of the view rectangle, no longer a blended rectangle over the whole target. One clear per pixel instead of two.
- The area under docked glass is worked out only when a panel, the size or the blur changes.

Engine, new and off by default (built and checked for correct pixels; the Mac decides which is needed):
- `setOrigin(x, y)`: the canvas may be **only as large as the glass it draws** (a floating window plus 34 px for its shadow) instead of the whole window. It is moved with its window by CSS; rectangles are still given in window coordinates. All of that layer's work (clear, compositing, backdrop, blur) shrinks with the canvas: for the mixer window here 1168x504 instead of 3840x2027, 13 times fewer pixels. This is the rule from 3.2 ("keep the engine's canvas no larger than the glass it draws").
- `setBackdropRate(n)`: the backdrop is drawn again at most n times per second while the panels still move on every frame (120 or 60 at a 240 Hz screen; under frost this cannot be seen, 3.2).
- `debug.set({aa:false})` and `debug.set({freeze:true})` for the test page.

Test page:
- **Solid (page only, as Bench 3)**: no engine canvas, plain panels. This row sets the screen rate and should reach 240.
- **Bench 3 path**: the GPU code of Bench 3 ("backdrop drawn on the GPU, every frame", its five panels) copied into the page as a row, for a direct comparison on the same page in the same minute.
- **Find the cost** (about 2 minutes): "Glass, scrolling" measured 25 times with one piece switched off at a time, as a table to copy.
- The readout stands still during a run; the frame loop reads no controls from the DOM; the screen's frame time is the shortest median of the run.
- A switch "floating canvas only as large as its glass".

Checked headless: `python3 tools/glass-lab/engine_test.py`, 151 checks, all pass, no console errors (was 126). Frame rates from the cloud mean nothing.

**What the next run must show** (same Mac, same window, other heavy tabs closed):

1. "Solid (page only)" at 240 fps, 100 %. If not, the Mac was busy: run again before reading anything else.
2. "Bench 3 path" at 100 %, as in 3.4. If not, this page or this hour differs from the Bench 3 run and the other rows cannot be judged yet.
3. Uploads and lists 0 on the "drawn on GPU" rows.
4. **"Glass, drawn on GPU" at 100 %: this is the requirement.** If it is still below, the Find the cost table names the piece:

| Row that jumps to (about) 100 % | Then the cost is | Fix that is ready |
|---|---|---|
| "floating layer off" or "docked layer off" | the second layer as a whole | fitted canvas for floating glass; or one layer redrawn at half the rate |
| "engine canvases at half size" | the pixels of the engine canvases (compositing), not the backdrop | `setOrigin` canvases; the docked layer as strips |
| "same, canvas fitted to it" (against "only the mixer floating") | the same, proven for the floating window | `setOrigin`, already in 2.1 |
| "background frozen, faces drawn" (and not "half size") | drawing the backdrop and its blur | `setBackdropRate`; a smaller target |
| "background 120 per second" or "60 per second" | the same | make that rate the default at a 240 Hz screen |
| "page scrolling off (2D still)" only | the app's own full redraw of the 2D arrangement, together with the glass | outside the engine: `drawArr` while scrolling |
| "anti-aliasing off" | the coverage shader (not expected) | hard edges plus a mipmap of the target |
| one "without ..." row | that panel's face | look at that kind |
| only "engine idle" | a fixed cost per WebGL canvas per frame | one context: fewer layers |

No fix that changes the look or the defaults was made blind. After this run the fix is one line (a default) or one integration rule for G3.

### 3.7 Engine 2.1 on the user's Mac: the requirement is met on the test page; square corners (27 Nov) and engine 2.2 (task G2d)

**Good news first.** The user ran the engine 2.1 test page on the Mac: M4, Chrome 157, 2560x1337 at 1.5x (7.7 megapixels), 238 Hz, mixer moving, lens Wide, blur Light.

| Row | fps | frames delivered | GPU background per s | uploads | lists |
|---|---|---|---|---|---|
| Solid (page only, as Bench 3) | 240 | 100 % | 0 | 0 | 0 |
| Solid, drawn by the engine | 240 | 100 % | 0 | 0 | 0 |
| Light, drawn on GPU | 240 | 100 % | 60 | 0 | 0 |
| **Glass, drawn on GPU (scrolling)** | **240** | **100 %** | 480 | 0 | 0 |
| **Glass, drawn on GPU, playing** | **240** | **100 %** | 480 | 0 | 0 |
| Light, small copy | 240 | 100 % | | | |
| Glass, small copy | 240 | 100 % | | | |
| Bench 3 path (its own GL code) | 240 | 100 % | | | |

Median 4.20 ms on every row, 95 % between 4.3 and 4.6 ms, worst between 4.7 and 4.8 ms. Uploads 0 and lists 0 on the "drawn on GPU" rows. **"Find the cost" showed no row that changes anything**: all 100 %, worst 4.5 to 4.8 ms.

**Reading.** Engine 2.1 meets the requirement on the test page: full glass with the Wide lens at the screen's own rate, scrolling and playing, with both layers and the mixer moving. The two savings of 2.1 and the lighter page were enough; **the fitted canvas (`setOrigin`) and a backdrop rate (`setBackdropRate`) are not needed** and stay off. (This run was at 2560x1337 at 1.5x, the run in 3.6 at 3840x2027 at 1x: about the same number of pixels.) **The real check is now in the app**, where the arrangement canvas, the DOM and the meters share the frame (GS1b).

**The problem the user saw**, in the user's words: "There is still a weird little artifact. When you have square corners, it looks on the inside that the corners are still rounded with the diffraction." The screenshot shows the Track headers panel (square corners, flush with the left edge of the window and with the panel below it) with the lens on: in its bottom left corner, and at the top left corner of the Device panel, the refracted rim follows a large quarter circle inside the square corner. A bright curved band inside a panel whose outline is square.

**Cause.** The earlier corner fix (section 1, "Corner artifact fixed in the bench shader"). To stop the bending direction from flipping along the corner diagonal, the lens got its own distance field with a corner radius of at least the lens width: 45 px on Wide. That is right for rounded panels and wrong for square ones: the outline is square, the refraction is a 45 px arc. A second thing made it stand out: both corners in the screenshot lie on edges that border nothing (the window's left edge, the seam between two panels). A lens rim there bends content that the user never sees enter the panel, so it reads as a fault and not as glass.

**What was compared** (one lookup per pixel in each; pictures of the same corners side by side, and pixel checks):

| | Square panels | Result |
|---|---|---|
| K1 | as before: rounded lens | the arc |
| K2 | the nearest edge bends; its direction turns to the other edge's across the diagonal within 4 px (a smooth minimum of the two edge distances) | no arc, but a **crease along the diagonal** wherever a clip edge crosses it: on one side the picture is moved sideways by up to 54 px, on the other side up or down, and 4 px cannot hide that |
| K3 | the nearest edge bends; the bend fades to nothing on the diagonal | no arc, but a **wedge of unbent picture** along the diagonal |
| **K4** | **each edge bends along its own axis by the usual profile; in the corner the two add** | **clean**: the band runs straight into the corner on both edges, and nothing can jump on the diagonal, because the sideways move depends only on x and the vertical move only on y |
| K5, K6, **K7** | K2, K3, **K4**, with the lens only on free edges | K7: the corners in the screenshot have no rim at all; corners between two free edges look like K4 |

**Decided (recommendation, the user judges on the Mac): K7.** Square lens for square panels, and the rim only on free edges.

**What changed (engine 2.2.0, test page; `index.html` and `desktop/` not touched, API kept).**

- **Square panels** (corner radius under 8 px) get the square lens (K4). **Rounded panels are pixel-identical to 2.1** (checked against the 2.1 file).
- **Panel option `edges`**: `'all'`, `'none'`, letters `t r b l`, or `'auto'`. Auto closes an edge that lies on the window border or against other docked panels along its whole length. **Docked panels default to auto**, floating kinds to all. On the test page: track headers bend on top and right, the tab band on top, device panel and transport nowhere.
- `setCorners('square' | 'blend' | 'fade' | 'round')`, `setBounds(rect)`, `panelInfo(id)`; panel option `corners` to force one panel square or round.
- The other three models are separate programs, built only if chosen. The default program holds the rounded shape (same instructions as 2.1) and the square shape (two square roots, no `length()`, no division), chosen per panel by one uniform. Still one lookup per pixel. **Expected cost: nothing measurable; not measured**, the cloud machine has no graphics card.
- Test page: a **Corners** chooser (K1 to K7, the star on K7, which is the default) with a **zoomed corner** (3x; five corners to pick from). The zoom is drawn at most 12 times per second and not at all while a table runs. **The eight rows of Run and the 25 rows of Find the cost are unchanged.**

Checked headless: `python3 tools/glass-lab/engine_test.py`, **171 checks, all pass**, no console errors (was 151). Among them: on a square panel the bend at a given distance from an edge is the same in the corner region as along the straight edge (0 px difference, all four edges); the same check fails by 22 to 37 px on K1, K2 and K3; closed edges are pixel-identical to lens off; rounded panels identical with every model.

**What the user is asked to do:** open the test page, look at Corners K1 to K7 with the zoomed corner and say which looks right; run the table once more (every row should stay at 100 %).

**Left open on purpose:**
- The rim light (the thin bright line on the outline) still runs along every edge, closed ones too. It was not what the user pointed at. If it should follow `edges`, that is a small change.
- The "Bench 3 path" row keeps Bench 3's own shader (the rounded lens): it is a speed reference, not a look.
- Slightly rounded panels (radius 8 to 44 px with the Wide lens) keep 2.1's lens, whose corner radius is the lens width and not the panel's. Nobody has pointed at it; on the 12 and 16 px corners of menus and windows it reads as round glass.
- For GS1b: where a docked panel lies against something that is not glass (toolbar, ruler), auto cannot know; such an edge is named in the app (`edges:'r'`). See `docs/glass-engine-module.md` section 7c.

### 3.8 The user's look at engine 2.2: K7 picked, rounded corners looked too round; engine 2.3 (task G2e, 27 Nov)

**The user's answer** (27 Nov, on the Mac): "K7 looks good, but there's still some weirdness in the round corners. When you look at the mixer window, it looks like the corner is more rounded than it's actually square."

**Decided: K7 for square panels** (square lens, each edge on its own axis, the two add; lens only on free edges). It stays, unchanged to the pixel, inside the new default.

**The remaining problem.** The screenshot shows the floating Mixer window (corners of about 20 px) over the arrangement with lens Wide. In its top left, top right and bottom left corners a bright refracted band sweeps a large quarter circle, far bigger than the window's own corner; the straight edges look right. The glass so looks as if its corner were much rounder than its outline.

**Cause, found in the shader and measured.** For rounded panels the lens field used `R = max(panel radius, lens width)`: 45 px on Wide for a 20 px corner. That was the earlier fix against a flip on the corner diagonal (section 1), and 3.7 had left it "open on purpose" for radii of 8 to 44 px. Two things follow from it. The bend direction turns around a centre 45 px in from both edges, not 20: measured from the picture, the centre of the band's arc lay **24.4 px** from the panel's corner centre (34.5 px for a 10 px corner). And every pixel between the panel's real arc and the lens's wider arc counts as "at the edge" and is bent at full strength: **9 px of full bend along the diagonal**, the bright crescent. The rim light's direction term used the same oversized corner (top left brighter, top right darker, over 45 px of each edge).

**The model now (engine 2.3, corner model `'outline'`, K8 on the test page).** One field for every panel, built on the panel's own radius `r`; a square panel is `r = 0`.

- **At the outline** it is the true rounded-rectangle field: inside the corner's own square the bend points away from the panel's corner centre and its depth is counted from the panel's own arc (arcs with the panel's centre, radius `r` at the edge, shrinking inward); beside the corner it is the plain edge.
- **Behind the corner centre**, where the band is deeper than the radius (45 against 20), the true field would pinch at the centre and crease along the diagonal. There it is K7's square corner: each edge on its own axis, the two add.
- **In between, one turns into the other** over the radius (over lens width minus radius when that is less): the true field at the outline, K7's at the corner centre. No seam, no flip.
- **`r = 0` is K7 exactly; `r` of at least the lens width is the lens of 2.1 and 2.2 exactly** (pills, round buttons, a 20 px window on Apple and Fine).
- The rim light takes its direction from the panel's own corner.
- Lens only on free edges: as in 2.2.

**Why not the true field all the way in.** It was the first thing considered. With the band deeper than the radius its arcs shrink to a point at the corner centre while the bend there is still 9 px (20 px corner, Wide) or 20 px (10 px corner): every direction meets in one point, and behind it the diagonal crease of K2 returns. The blend removes both and keeps everything curved inside the corner's own radius.

**Checked headless** (`python3 tools/glass-lab/engine_test.py`, **191 checks, all pass**, no console errors; was 171):

| | Engine 2.2 (K7) | Engine 2.3 (K8) |
|---|---|---|
| 20 px corner, Wide: centre of the band's arc, distance from the panel's corner centre | 24.4 px (both axes) | **0.0 px** |
| 10 px corner, Wide | 34.5 px | 0.7 px (both axes) |
| Bend further than the radius from the other edge, against the straight edge (20 / 10 / 30 px corners) | 20 / 22 / 11 px off | **0 / 0 / 0** |
| Full bend along the corner diagonal (20 px corner) | 9 px (the crescent) | none; falls steadily from the outline |
| Largest step between neighbouring pixels, 3 px or more inside (20 px corner; a straight edge has 3) | 10.4 px | 3.2 px |
| Rim light 22 to 45 px from the corner against mid-edge | 4 levels or more | 0 to 1 |
| Square panels | | pixel-identical to K7 (Fine, Apple, Wide; the test page's whole docked layer) |
| Pills, round buttons, corners of 60 px, fully round | | pixel-identical to 2.2 (Fine, Apple, Wide) |

**Cost.** Still one texture lookup per pixel; one `length()` and at most three square roots, no new pass. **Not measured**: the cloud machine has no graphics card. Nothing in the two tables' rows was changed (same eight rows of Run, same 25 of Find the cost); the Mac run must show every row still at 100 %.

**Test page** (same artifact link, `docs/glass-engine-module.md`): Corners K1 to K8, the star on K8, K7 kept for comparison. The mixer window now has 20 px corners and the menu 10 px, like the app's. The zoomed corner starts on the mixer window. **Corner sheet**: a square corner, a 20 px corner, a 10 px corner and a pill, each at lens Fine, Apple and Wide, K8 beside K7.

**What the user is asked to do:** look at the mixer window's corners (and the corner sheet) and run the table once more.

**Left open on purpose:**
- A small-radius corner under a wide lens keeps one visible property of a true outline: right at a straight edge the picture is moved only across that edge, and the other edge's share fades in over the radius. On a 10 px corner on Wide that is up to 20 px of sideways move appearing within 10 px. It reads as the corner of the glass; if the user sees it as a fault, the fade can be made longer (one number).
- The rim light still runs along every edge, closed ones too (as in 3.7).
- The "Bench 3 path" row keeps Bench 3's own shader: a speed reference, not a look.
- `index.html` still carries an older engine; GS1b ports 2.3.0 (module doc section 7d).

### 3.9 Glass step 1 is in the app (27 Nov, v0.223, task GS1)

Done as section 3.1 "Step 1" and the rules of 3.2 to 3.5 say: one engine canvas under the arrangement for the docked panels, backdrop drawn on the graphics card from the clip geometry, levels Glass / Light / Solid, defaults Wide 45 and Light, no `backdrop-filter` on the docked panels at any level. From the G1 list, in the same step: the playhead as its own layer, Follow centre without a redraw in frames where the view did not move, pointer capture on window drags; the transport's logo glow, meters, time text and CPU graph no longer sit inside a filtered element because the transport has no filter any more (its glass is the engine's canvas, a separate layer under it). What was built, what was measured and what was not: `docs/backlog-log.md` (task GS1) and `docs/glass-engine-module.md` section 9.

The app has **one** engine canvas (the docked layer), so while scrolling two full-window surfaces are redrawn per frame (the 2D arrangement and the engine canvas), the case that held every frame in Bench 3; the second engine layer arrives with GS2 (3.7: with engine 2.1 two layers held every frame on the test page, so no fitted canvas and no backdrop rate are used). The engine text in the app is 2.3.0 from task G2e (for the square docked panels that is K7 exactly, 3.8) with one method added for the app, `setBackdropColor`. The app names the free edges itself: the track headers bend only towards the arrangement, the device panel on its top edge under the track tabs, the transport only while no device panel lies against it. So the corner artifact the user saw on the test page (3.7) is not in the app.

**Still open: the frame rate on the Mac** (3840x2027 at 240 Hz must deliver 100 % of the frames with room to spare). The cloud machine has no graphics card, so nothing measured there says anything about it. Next: GS2 (floating windows, sheets, menus), then step 3 (remove the old glass code) after the user's check.

### 3.10 Glass step 2 is in the app (27 Nov, v0.227, task GS2)

Done as 3.1 "Step 2" says, under the rules of 3.2 to 3.5: windows, sheets and menus get their glass from the engine, and **`backdrop-filter` is used nowhere in the app any more, at no level** (one CSS rule). The engine draws its backdrop on the graphics card from the same rectangle scene as the docked panels (0 uploads); levels Glass, Light, Solid as for the docked panels; defaults Wide 45 and Light.

**Layer or face per window, decided: layers.** Each layer is one more engine on one full-window canvas, put into the page's stacking order directly under the floating elements it serves; at most three. An element that overlaps another floating element goes one layer up and sees the one below as a flat picture (plan 2.4 option a), as do the docked panels (their colour) and the device displays and the piano roll (small copies, capped). So glass never samples glass, and moving a window is one face redraw: no list, no backdrop, no blur pyramid (counted). A face per window (one engine per window on a canvas only as large as the window) was built as a debug mode and measured too (backlog log, task GS2): it needs one more graphics context per open window and has to draw the backdrop and the blur again on every move of the window, because its canvas moves with it. That breaks the rule "moving a window costs one quad redraw", so the layers stay the default. The nested blurs in the mixer (tab, pan handles) are gone.

How it is wired: `docs/glass-engine-module.md` section 10. What was measured and tested: `docs/backlog-log.md` (task GS2).

**Still open: the frame rate on the Mac** with the mixer open (3840x2027 at 240 Hz must deliver 100 % of the frames with room to spare); the cloud machine has no graphics card. Next: the user's check, then step 3 (delete `rfAttach`, `rfBuild`, `rfMap`, `rfStyle`, the `feImage` lens): done in 3.11.

### 3.11 Glass step 3 (27 Nov, v0.228, task GS3): the old lens code is gone; where the app's own drawing spends the frames

**The user's check on the Mac** (v0.223, Mac mini M4, 240 Hz, the real app): about 180 fps idle, 100 to 120 while moving the arrangement with Settings open over it, 90 at the lowest, "a big improvement ... it looks good". The engine test page on the same Mac held 240 fps with every frame kept, so the engine itself is not the limit. With that, step 3 was done:

- **Removed**: the SVG lens (`rfMap`, `rfBuild`, `rfStyle`, `rfAttach`'s body, the `feImage` map), the blurred picture (`#arrBlur`, `abDraw`, `fxBlurPic`), the half-size copy behind live glass, the edge light's reader of the blurred picture, 90 `backdrop-filter` declarations (the guard rule that sets it to none everywhere stays), the Glass preview that imitated the old levels, and the settings that changed nothing any more (Blur, Refraction, Softer blur while playing, Half-size picture behind glass). Their stored choices are dropped once.
- **Measured** with `tools/ui-tests/frametime.py` (the user's size, Fractals open, one drawing part switched off at a time): scrolling costs the full drawing of the arrangement canvas on every frame and the glass drawn again for the new view; idle cost frames because things were drawn again without any change: the capture button's dot pulsed through an opacity animation that the compositor runs on **every screen frame** (on a 240 Hz screen the whole window was put together 240 times a second just for it), the master meter drew 120 times a second in silence, and the Settings logo up to 160 times a second.
- **Fixed**: the dot pulses through its colour in 12 steps, the meter draws only on change, the Settings logo at most 60 a second, two forced layout reads per arrangement drawing are kept. Idle compositor frames went from one per screen frame (57 a second at 60 Hz) to the logo's 30; in the moving scenes the compositor no longer makes extra frames between the app's own.
- **Tried, left out**: scrolling by shifting the old picture and drawing only strips. Pixel-identical, but no faster on the cloud machine's software renderer (its copies of a full-window picture cost as much as drawing it); it might pay on a graphics card, kept as an unused experiment.
- **The frame-rate read-out**: Settings > Performance > "Frame-rate read-out on screen": frames per second and the slowest frame of the last 5 seconds, in a corner, on top of everything.

**Still open**: the frame rate on the Mac with v0.228 (idle should now reach the screen rate; scrolling still draws the whole arrangement every frame). Scrolling at 240 with Settings open needs the arrangement drawn in tiles the compositor moves, or by the glass engine on the graphics card: a task of its own. Numbers and tests: `docs/backlog-log.md` (task GS3).

## 4. Open questions for the user

1. (Answered: Wide 45 px and Light.)
2. The Glass Bench frame-rate table from the Mac (not received yet; the user reported that the GL engine "looks very good").
3. Where should updates and the browser version be hosted once the repo is private (own domain, which provider)? Are Apple and Windows signing certificates wanted now?
4. Menus and windows over other glass: Apple never lets glass sample glass. Is "the top glass shows the arrangement and a flat picture of the panel under it" acceptable until HTML-in-Canvas arrives?

## 5. Sources (opened on 26 Nov 2026 by research helpers; pages were read through a fetch tool that summarises, Apple pages as raw text)

Apple and reverse engineering: [WWDC25 219](https://developer.apple.com/videos/play/wwdc2025/219/), [323](https://developer.apple.com/videos/play/wwdc2025/323/), [284](https://developer.apple.com/videos/play/wwdc2025/284/), [310](https://developer.apple.com/videos/play/wwdc2025/310/), [Applying Liquid Glass to custom views](https://developer.apple.com/documentation/swiftui/applying-liquid-glass-to-custom-views), [HIG Materials](https://developer.apple.com/design/human-interface-guidelines/materials), [ShatteredGlass](https://github.com/AlexStrNik/ShatteredGlass), [GlassExplorer](https://github.com/ktiays/GlassExplorer), [liquid-gpu](https://github.com/nshelia/liquid-gpu), [sspai on the implementation](https://sspai.com/post/100983), [CABackdropLayer notes](https://medium.com/@avaidyam/capluginlayer-cabackdroplayer-f56e85d9dc2c).

Algorithms and Chromium: [Bjørge, SIGGRAPH 2015 (dual filtering)](https://community.arm.com:443/cfs-file/__key/communityserver-blogs-components-weblogfiles/00-00-00-20-66/siggraph2015_2D00_mmg_2D00_marius_2D00_notes.pdf), [Intel fast blur study](https://intel.com/content/www/us/en/developer/articles/technical/an-investigation-of-fast-real-time-gpu-based-image-blur-algorithms.html), [frost.kiwi on dual Kawase](https://blog.frost.kiwi/dual-kawase/), [Grida: Chromium effect optimisations](https://grida.co/docs/wg/research/chromium/effect-optimizations), [HTML-in-Canvas](https://developer.chrome.com/docs/web-platform/html-in-canvas), [Electron releases](https://releases.electronjs.org/), [Figma on WebGPU](https://www.figma.com/blog/figma-rendering-powered-by-webgpu/), [Flutter BackdropGroup](https://api.flutter.dev/flutter/widgets/BackdropGroup-class.html), [Microsoft: Acrylic](https://learn.microsoft.com/windows/uwp/style/acrylic), [Microsoft: Mica](https://learn.microsoft.com/windows/apps/design/style/mica), [Skia Graphite](https://blog.google/chromium/introducing-skia-graphite-chromes/).

Not found or not confirmed: Apple's re-sampling policy (every frame or on change); what Apple does on old devices; the Chromium 60 fps cap bug on macOS (page needs a sign-in); any published frame-rate numbers for web liquid-glass libraries that can be trusted.
