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
- Lens width on big panels: **wants to compare first** (slider added to the Glass Bench).
- Source: **go private with our own updates, keep a browser version.**
- Science look: **both** our own visuals drawn in code and real NASA / Webb images with credit.

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
| U1 | **User:** run the Glass Bench on the Mac (Chrome; scrolling, mixer moving, all panels), copy the table; try the Lens width slider and say which width. | nothing | yes | none |
| G1 | **Quick wins in today's glass**, each measured before and after with `tools/glass-lab/bench.py`: move the logo glow, meters, time text and CPU graph out of the transport's glass element (sibling layer, as `#fxglass` does); remove glass on glass in the mixer (`.fwh`, the 1.6 px `.ck` blur); playhead as its own layer; Follow centre without a full redraw and backdrop copy per frame; mixer window and sheets on the picture blur; pointer capture on window drags. | index.html | serial | none |
| G2 | **Engine as a stand-alone module** in `tools/glass-lab/`: the design in 2.4 with Apple's numbers from 2.2, an API (register a panel with rectangle, radius, kind; set backdrop sources; mark dirty), context-loss recovery, fallbacks (plain tint), Reduce Transparency and Increase Contrast behaviour, quality steps, a test page with AudioLab-sized panels. No code copied from the reverse-engineering repos (no licence given); numbers only. | tools/ only | **parallel** | none (U1 result tunes it) |
| G3 | **Integrate behind a switch** "Glass engine (preview)" in Settings: arrangement as backdrop; track headers, transport, tab band and device panel first; then floating windows; then menus and sheets (2.4 gap, option a). Old glass stays as the fallback. | index.html | serial | G2, U1 |
| G4 | After the user confirms on the Mac: remove `backdrop-filter` and the SVG lens, rebuild the Performance page around the engine's quality steps, keep Light mode as the lowest step. | index.html | serial | G3 |
| G5 | Electron: check real 240 Hz pacing in the shipped app; plan the move to Electron 46 (Chromium 160, HTML-in-Canvas) when it is stable. | desktop/ | parallel | none |
| D1 | "Flat bars" (design 7) is the default again; undo the one-time migration for people it moved to "Flat bars 2", without overriding anyone who chose 2 themselves afterwards if that can be told apart (else ask). | index.html | serial | none |
| D2 | Sidechain outline only when the sender or receiver is selected (`abxLights`, about line 17288); cables unchanged; "Selected only" unchanged. | index.html | serial | none |
| D3 | Type scale C1: Inter at 11/12/13/15, weights 400/500/600, equal-width digits. | index.html | serial | none |
| D4 | Display-first devices (G2): pick page first (three to five layouts of real devices with sideways titles, biggest possible display, floating glass controls), then implement device by device. | page: parallel; index.html: serial | | engine for the floating glass |
| D5 | Glass mixer strips (F4), keeping the half pan dial, header, stereo displays, cables and Flat bars. | index.html | serial | G3 |
| D6 | Science look: pick page with splash and About backgrounds drawn in code plus a shortlist of NASA / Webb images with credit lines and licence notes. | page only | **parallel** | none |
| S1 | Own update feed, then private repo, then browser build (order in 2.7); code signing plan. Needs the user's choices on hosting and accounts. | desktop/, CI | parallel (plan); careful (rollout) | none |
| N1 | Later: research note on a native audio engine and VST host beside the interface. | docs only | parallel | none |

Suggested order for index.html work: D2, D1 (small, asked for directly), G1, D3, then G3 once G2 and U1 are in.

## 4. Open questions for the user

1. Lens width on big panels (after trying the slider): Apple's 20 px, or wider?
2. The Glass Bench table from the Mac.
3. Where should updates and the browser version be hosted once the repo is private (own domain, which provider)? Are Apple and Windows signing certificates wanted now?
4. Menus and windows over other glass: Apple never lets glass sample glass. Is "the top glass shows the arrangement and a flat picture of the panel under it" acceptable until HTML-in-Canvas arrives?

## 5. Sources (opened on 26 Nov 2026 by research helpers; pages were read through a fetch tool that summarises, Apple pages as raw text)

Apple and reverse engineering: [WWDC25 219](https://developer.apple.com/videos/play/wwdc2025/219/), [323](https://developer.apple.com/videos/play/wwdc2025/323/), [284](https://developer.apple.com/videos/play/wwdc2025/284/), [310](https://developer.apple.com/videos/play/wwdc2025/310/), [Applying Liquid Glass to custom views](https://developer.apple.com/documentation/swiftui/applying-liquid-glass-to-custom-views), [HIG Materials](https://developer.apple.com/design/human-interface-guidelines/materials), [ShatteredGlass](https://github.com/AlexStrNik/ShatteredGlass), [GlassExplorer](https://github.com/ktiays/GlassExplorer), [liquid-gpu](https://github.com/nshelia/liquid-gpu), [sspai on the implementation](https://sspai.com/post/100983), [CABackdropLayer notes](https://medium.com/@avaidyam/capluginlayer-cabackdroplayer-f56e85d9dc2c).

Algorithms and Chromium: [Bjørge, SIGGRAPH 2015 (dual filtering)](https://community.arm.com:443/cfs-file/__key/communityserver-blogs-components-weblogfiles/00-00-00-20-66/siggraph2015_2D00_mmg_2D00_marius_2D00_notes.pdf), [Intel fast blur study](https://intel.com/content/www/us/en/developer/articles/technical/an-investigation-of-fast-real-time-gpu-based-image-blur-algorithms.html), [frost.kiwi on dual Kawase](https://blog.frost.kiwi/dual-kawase/), [Grida: Chromium effect optimisations](https://grida.co/docs/wg/research/chromium/effect-optimizations), [HTML-in-Canvas](https://developer.chrome.com/docs/web-platform/html-in-canvas), [Electron releases](https://releases.electronjs.org/), [Figma on WebGPU](https://www.figma.com/blog/figma-rendering-powered-by-webgpu/), [Flutter BackdropGroup](https://api.flutter.dev/flutter/widgets/BackdropGroup-class.html), [Microsoft: Acrylic](https://learn.microsoft.com/windows/uwp/style/acrylic), [Microsoft: Mica](https://learn.microsoft.com/windows/apps/design/style/mica), [Skia Graphite](https://blog.google/chromium/introducing-skia-graphite-chromes/).

Not found or not confirmed: Apple's re-sampling policy (every frame or on change); what Apple does on old devices; the Chromium 60 fps cap bug on macOS (page needs a sign-in); any published frame-rate numbers for web liquid-glass libraries that can be trusted.
