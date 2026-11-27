# Native screens for AudioLab: options, evidence and a migration path (task RN4)

Research only. `index.html`, `desktop/` and `native/engine` were not touched. New: this document, a small benchmark in `tools/native-lab/ui-bench/` and a workflow that runs only when started by hand (`.github/workflows/ui-bench.yml`). Written 27 November 2026.

Read with: `docs/native-mac-plan.md` (the route; stage 4 is the native interface), `docs/native-mac-picks.md` (your picks R2b, R5b, R6a and U4f), `docs/research-native-mac.md` sections 1.8 and 1.12 (240 Hz and accessibility on the Mac), `docs/glass-engine-plan.md` sections 3.6 to 3.11 (the glass engine and the frame times from your Mac). `docs/research-native-windows.md` (task RN2) did not exist when this was written; the Windows points here are from this task's own sources.

**How to read the sources.** Every finding names its source with a link. Three kinds of marks:
- **[read]**: a page that a research helper opened and read today.
- **[title]**: only the title or address of a page was seen in a search result, so the claim rests on that title.
- **[guess]**: background knowledge or reasoning, not checked against a source in this task.

The web-page reader hit its hourly limit partway through, so some points stay [title] or [guess]. Each one says so.

---

## 0. Summary

### The question
You want a native look and feel at 240 Hz (pick U4f), on Mac and Windows. The interface stays in Electron until the engine has moved (R2b, R6a). This document prepares the later decision, so that it can be made on measurements rather than on taste.

### The three realistic options

1. **W: stay web, draw the heavy parts on the graphics card.**
   - Keep Electron.
   - Move the arrangement, piano roll, meters and device displays from Canvas 2D to the GPU. WebGL2 now, WebGPU later. The glass engine already works this way.
   - Feed meters and the playhead from shared memory (RN1's U1, task NR12).
   - Plug-in editors stay in their own windows, as in the test app today.
2. **N: own native GPU interface.**
   - One C++ renderer for both systems. This is what Ableton, Bitwig, Zed and Figma do.
   - The renderer is either WebGPU-native (Dawn, on Metal and D3D12) or Metal and Direct3D written separately.
   - Text comes from the system (CoreText on Mac, DirectWrite on Windows) and is put into a glyph atlas.
   - A thin native shell per system: AppKit on Mac, Win32 on Windows.
   - Accessibility goes through a small per-system layer, written once against the same tree (AccessKit or your own).
   - Plug-in editors can be docked as child views.
3. **Q: Qt Quick 6.**
   - A bought toolkit with a GPU scene graph on Metal and D3D, the most complete accessibility of the cross-platform kits, and built-in embedding of native windows.
   - The arrangement, meters and glass become custom scene-graph items.
   - Costs: an LGPL or commercial licence, and a look that is all custom anyway.

Ruled out as the main interface (section 3 gives the reasons):
- **SwiftUI**: slow for dense views, and Mac only.
- **JUCE graphics**: no Metal renderer, and weak at high refresh rates.
- **Dear ImGui and GPUI**: no accessibility.
- **Flutter**: native-view embedding is unfinished on desktop.
- **Tauri**: WKWebView is held to 60 fps on the Mac.
- **The Rust kits** (Iced, egui, Vizia, Slint): young, and they mean a second language next to the C++ engine.

**AppKit with Metal** (the Logic way) is the best Mac-only answer. With Windows wanted, it is only the Mac shell of option N, not a choice of its own.

### Recommendation

**Stay on W now, and build it so that N is a port rather than a rewrite. Decide between W and N at a measured gate after the engine has moved (R2b).**

Concretely:
- Every heavy surface becomes a **scene of GPU primitives**: rectangles, rounded rectangles, lines, glyph runs and textures. This is already how the glass engine works.
- These surfaces are drawn by one small renderer with a fixed interface. WebGL2 implements it today, and WebGPU when Electron's is solid.
- A C++ implementation on Dawn or Metal can later draw the same scene in a native window.
- The scene description, the hit-testing and the accessibility tree are written once.

The rest (settings, browser, menus, dialogs) stays HTML until the gate. It is cheap there, and it is where a rewrite costs most and gains least.

### What would change the recommendation

- **Toward N sooner:**
  - The scrolling arrangement in Electron cannot hold 240 fps on your M4 even after it is drawn on the GPU (gate measurement G1).
  - Input-to-screen latency in Electron is measured a frame or more worse than native (G2).
  - You want plug-in editors docked inside the main window, not floating.
- **Toward Q:**
  - Accessibility becomes a hard requirement early. Qt has the most finished screen-reader support across both systems.
  - The work is shared with people who know Qt, and the licence is acceptable.
- **Toward staying on W indefinitely:**
  - G1 and G2 pass in Electron.
  - Floating plug-in windows are fine for you.
  - Then going native buys little except Liquid Glass from the system, and AudioLab's own glass engine already matches the look.

### The benchmark
The same arrangement and 1,000 meters were drawn three ways on the macOS build machine: Metal, WebGL2 in Electron, and Canvas 2D in Electron (section 4). The build machine is a **virtual Mac with a virtual display**. Its numbers compare the three ways with each other. They do not say what your M4 at 240 Hz will do.

---

## 1. Comparison table

Effort is in this project's tasks: one cloud session of 1 to 3 hours. "Rewrite" means the whole present interface (section 5). Risk means the chance of a dead end or a long stall.

| | W: Electron, GPU surfaces | N: own native GPU UI (C++) | Q: Qt Quick 6 | AppKit + Metal (Mac only) | SwiftUI | JUCE UI | Tauri (system web view) |
|---|---|---|---|---|---|---|---|
| **240 Hz** | Possible: the glass test page held 240 fps on your M4 (plan 3.7); the real app 90 to 180 (3.11) because the arrangement is Canvas 2D | Yes, if paced by `CAMetalDisplayLink` / DXGI waitable swap chain and the frame stays under ~4 ms (Zed holds 120) | Vsync-driven RHI; 240 not shown by any source [guess: possible] | Yes (same as N on the Mac) | Not for dense views (no numbers found; many reports) | Weak: no Metal; Direct2D had 240 Hz faults, fixed 2024, newer regressions | **No on Mac**: WKWebView rAF held near 60 fps (WebKit bug 294338 open) |
| **Input latency** | Chromium's compositor adds a stage [guess: about 1 frame more than native]; measure (G2) | Lowest possible: draw for the target time, 2 to 3 drawables | Close to native [guess] | Lowest | Good for simple views | Medium | Worse (60 fps) |
| **Effort for today's interface** | Low: 10 to 25 tasks to put the arrangement, piano roll and meters on the GPU | High: 150 to 250 tasks (plan stage 4), less if the scene layer was built first under W | High: similar to N, a little less for forms and lists | High, and Windows is a second job | High, Mac only | High; drawing must be redone anyway | Medium, but Mac stays at 60 fps |
| **Risk** | Low; known ground | Medium: own toolkit means own text, input, focus, accessibility | Medium: licence, custom look against Qt's grain, build size | Low on Mac, but no Windows | High for this kind of view | Medium-high | High (frame-rate cap is outside our control) |
| **Accessibility** | Good: Chromium's tree; canvases need ARIA or hidden DOM mirrors (the app has 531 `aria-` attributes today) | Must be built: `NSAccessibilityElement` per control on Mac, UI Automation providers on Windows; AccessKit gives one tree for both [guess for C++ use] | Best of the cross-platform kits (UIA and NSAccessibility for Widgets and Quick) | Native, best on the Mac | Native | Basic but real (since 6.1) | As web |
| **Plug-in windows** | Separate native window per plug-in (works in the test app today: Serum 2 at 1190×740) | Real child view (NSView / HWND) docked in the window; nothing can be drawn over it | `QWindow::fromWinId` + `WindowContainer` (Qt 6.7) | Child `NSView`, as Logic | Through AppKit | `NSViewComponent` / `HWNDComponent`, the industry standard | Separate window |
| **Two platforms** | Free (one code) | One renderer and scene, two thin shells, two accessibility back-ends | One code | No | No | One code | One code, two web engines |
| **Glass look** | AudioLab's own engine (WebGL2), already in the app | Port the engine's shaders (they are small); system Liquid Glass usable for window chrome on macOS 26 | Own shaders in `ShaderEffect` [guess] | System Liquid Glass (tint and shape only, no blur control) or own Metal | System glass only | Own | Own (WebGL in the web view) |

---

## 2. Findings with sources

### 2.1 What real DAWs and pro apps use

| Product | Interface | What is known about drawing and frame rate | Accessibility |
|---|---|---|---|
| **Ableton Live** | Own toolkit [guess] | Since 11.2 the Mac version draws with **Metal** by default. Ableton's stated reason: "increasing the rate at which Live's UI is updated". A switch brings back the old renderer [read: [Ableton](https://help.ableton.com/hc/en-us/articles/6012665671836-Metal-based-GPU-Rendering-in-Live-11-2-on-macOS)]. Windows users ask for the same smoothness [title: [forum](https://forum.ableton.com/viewtopic.php?p=1806509)]. | Live 12 works with screen readers through each system's accessibility layer. The manual lists the parts that do not yet work: some plug-ins, Max for Live, Wavetable's modulation matrix, clip fades [read: [manual](https://www.ableton.com/en/live-manual/12/accessibility-and-keyboard-navigation)]. |
| **Bitwig Studio** | Java with its own interface | 5.2 (2024) rewrote the graphics engine for the GPU: "native hardware acceleration", "more CPU for your audio". Requirements: DX11 on Windows, Vulkan on Linux. Display refresh **up to 144 Hz on macOS 14**, 60 Hz on older versions [read: [release notes](https://downloads.bitwig.com/5.2/Release-Notes-5.2.html)]. The renderer is **Skia** (`skia-vulkan`, `skia-gl` on Linux) [read: [Bitwig support](https://bitwig.com/support/technical_support/the-bitwig-studio-window-is-not-displayed-correctly-after-updating-to-version-52-on-linux-67)]. Metal on the Mac is a [guess]. Plug-ins run in separate processes [title: [user guide](https://bitwig.com/userguide/latest/vst_plug-in_handling_and_options)]. | None found [guess: none]. |
| **Logic Pro** | AppKit [guess, widely known] | No source on its drawing. | VPAT published [title: [Apple VPAT](https://support.apple.com/content/dam/edam/applecare/images/en_US/otherassets/accessibility/vpat_logic_pro_2024.pdf)]. Blind users call it "still usable with VoiceOver" but less accessible than REAPER [read: [AppleVis](https://applevis.com/forum/macos-mac-apps/has-any-blind-engineer-mixed-or-mastered-professionally-logic-pro-real-studio)]. Flex Pitch "mostly inaccessible" [title: [AppleVis](https://applevis.com/comment/204553)]. |
| **REAPER** | Win32; on the Mac through SWELL, a Win32 layer over Cocoa [guess, widely known] | Mostly CPU drawing [guess]. | Through **OSARA**, an open-source extension for NVDA, JAWS and VoiceOver; the blind community's favourite [title: [OSARA](https://github.com/jcsteh/osara)]. |
| **Cubase / Nuendo** | Steinberg's own toolkit; Qt not confirmed. Dorico is Qt [guess]. VSTGUI is the plug-in library, not Cubase's [read: [forum](https://forums.steinberg.net/t/toolkit-qt-or-custom/814775)]. | HiDPI on Windows: added in Cubase 10, per-monitor in 11, with a host-side resize for DPI-unaware plug-ins. OpenGL plug-ins can appear "tiny in a corner" [read: [Steinberg](https://www.steinberg.help/r/cubase-11-using-dpi-unaware-plug-ins-on-windows)]. Cubase 14's redesign drew a long complaint thread [title: [forum](https://forums.steinberg.net/t/cubase-14-gui-design-regressions/953624)]. | Unknown. |
| **Studio One** | CCL, PreSonus's own C++ framework | High DPI on all platforms. On Windows, a hardware-accelerated 2D engine on **Direct2D and DirectComposition**, since Studio One 3 in 2015 [read: [CCL](https://kreatives.org/platform/blog/the-ccl-framework)]. | Unknown. |
| **FL Studio** | Delphi; the Mac port isolated the system calls [read: [Synthtopia](https://www.synthtopia.com/content/2014/11/28/fl-studio-coming-natively-to-os-x/), [Embarcadero](https://embarcadero.com/case-study/image-line-software-case-study)] | Vector interface [guess]. | Unknown. |
| **Pro Tools** | Unknown | Not covered. | VoiceOver works track by track. **Flo Tools**, a set of macros now ten years old, makes it practical, and breaks when Avid renames things [read: [Production Expert](https://www.production-expert.com/production-expert-1/flo-tools-2026-pro-tools-accessibility-macros-ten-years-on)]. |
| **Figma** | C++ renderer compiled to WebAssembly | WebGL since 2015, **moved to WebGPU** with a fallback to WebGL mid-session. Their shaders were translated GLSL to WGSL. "Performance improvement on some classes of devices" [read: [Figma](https://www.figma.com/blog/figma-rendering-powered-by-webgpu/)]. | Not covered. |
| **Blender** | Own interface on its GPU module | Vulkan default on Linux and Windows in 5.3 [read, secondary: [Linux Journal](https://www.linuxjournal.com/node/1341478)]. | Weak; a VPAT issue expects much "Does Not Support" [read: [Blender](https://projects.blender.org/blender/blender/issues/104144)]. |
| **DaVinci Resolve** | Qt (licence list on the forum, may be incomplete) [read: [forum](https://forum.blackmagicdesign.com/viewtopic.php?p=1140967)] | GPU viewers [guess]. | Not covered. |
| **Zed** | GPUI, its own toolkit | Metal with one shader per primitive (rectangles, shadows, text, icons, images), signed distance fields for rounded corners, text from CoreText into a glyph atlas drawn in one instanced call. A general vector renderer "wasn't fast enough". 8.33 ms budget at 120 Hz [read: [Zed](https://zed.dev/blog/videogame)]. Lessons for ProMotion [read: [Zed 120 fps](https://zed.dev/blog/120fps)]: the display slows down when no frames come, so keep presenting for 1 s after input; some states held 60 fps until they changed the display link; a buffer race fixed with a pool of buffers; triple buffering. Windows: **DirectX 11 and DirectWrite** "to match the Windows look and feel" [read: [Zed for Windows](https://zed.dev/blog/zed-for-windows-is-here)]. | Not mentioned upstream. |
| **Ardour** | Own canvas on Cairo, a GTK2 fork (YTK) | Redraws only changed areas; Cairo's coordinate limit is about 32,767 px [read: [Ardour](https://ardour.org/canvas.html)]. | Not covered. |
| **Tracktion Waveform** | JUCE | Users report a sluggish interface when zoomed out [title: [KVR](https://www.kvraudio.com/forum/viewtopic.php?p=9032509)]. | JUCE's layer. |

**What this says.**
- The DAWs that care about smoothness (Live, Bitwig, Studio One) moved to their **own toolkit drawn on the GPU**, and Zed and Figma did the same. None of them uses a stock widget kit for the main screens.
- Apple's Logic is the exception, because AppKit is Apple's own.
- None of the DAWs publishes a frame rate above 144 Hz. **AudioLab at 240 Hz would be ahead of all of them.** This also means there is no prior art to copy at that rate.

### 2.2 The Mac side: AppKit, Core Animation, Metal

- **Display link.**
  - Use `CAMetalDisplayLink`, or the display link from `NSView`/`NSScreen` on macOS 14 and later.
  - `CVDisplayLink` is deprecated (RN1 section 1.8, with Apple's sources).
  - Apple DTS told a developer to use `CAMetalDisplayLink` for low latency at 120 Hz. Two drawables are "acceptable on macOS if within frame budget".
  - That developer's frames took 2 to 3 ms, yet only about **80 Hz** came out in full screen until three drawables were used, which costs one frame of latency. The thread was never resolved [read: [Apple forum 763426](https://developer.apple.com/forums/thread/763426)]. The lesson: frame pacing on the Mac must be measured, not assumed.
- **Rosetta holds display links at 60 Hz** [title: [forum 731514](https://developer.apple.com/forums/thread/731514), [800540](https://developer.apple.com/forums/thread/800540)]. The native app must be arm64 only, which it is.
- **240 Hz monitors on the Mac.**
  - macOS drives 240 Hz on recent Macs; the HDMI 2.1 route arrived in macOS 26 on M3 and newer [read: [Plugable](https://plugable.com/en-ca/blogs/news/hdmi-2-1-on-mac-how-the-latest-macos-expands-external-display-support)].
  - Users report limits by port and chip: a 390 Hz monitor running at 240 on a Mac Studio [read: [forum 717481](https://developer.apple.com/forums/thread/717481)], and 4K 240 reaching only 120 on an M4 Pro [title: [Apple Community](https://discussions.apple.com/thread/255849893)].
  - Your Odyssey G80SD on DisplayPort runs at 240 on the Mac mini (your reports). Plan for 240 on your setup and 120 as the common case for others.
- **A macOS 27 beta thread reports unstable ProMotion cadence and scroll judder** [title: [forum 840214](https://developer.apple.com/forums/thread/840214)]. You run macOS 27.2. Worth watching, because it would hit every option alike.
- **Many controls.**
  - Thousands of `NSView`s or layers are slow [guess, Apple's general advice].
  - Native DAWs draw meters and the arrangement into one surface per area, which is what option N and the glass engine do.
- **Accessibility for drawn controls.**
  - The view that draws returns `NSAccessibilityElement` children, one per knob or fader. Each has the slider role, a label, a value, a frame, and increment and decrement actions.
  - Value changes are posted throttled, never at meter rate [title: [Apple: custom controls](https://developer.apple.com/library/content/documentation/Accessibility/Conceptual/AccessibilityMacOSX/ImplementingAccessibilityforCustomControls.html), [sample](https://developer.apple.com/library/archive/samplecode/AccessibilityUIExamples/Listings/AccessibilityUIExamples_Slider_CustomSliderView_swift.html)].
  - Cheap in CPU, real work in engineering. It must sit in the control model from day one.

### 2.3 SwiftUI

- No numbers were found. There are many reports of slow updates many times a second, slow `List` and `Table` on macOS, and regressions [title: [Swift forums](https://forums.swift.org/t/how-to-update-swiftui-many-times-a-second-while-being-performant/71249), [Apple forum 806786](https://developer.apple.com/forums/thread/806786), [784845](https://developer.apple.com/forums/thread/784845), [Apple: SwiftUI performance](https://developer.apple.com/documentation/xcode/understanding-and-improving-swiftui-performance)].
- The safe design, used by Mac developers [guess]: Metal or one `CALayer` surface for meters and timelines, fed from a ring buffer, with SwiftUI only for settings and inspectors.
- It is Mac only, so for AudioLab it could at most be the Mac's settings screens. That is not worth a second interface technology.

### 2.4 Liquid Glass (macOS 26) and your own glass engine

- **AppKit:** `NSGlassEffectView` (content view, corner radius, tint) and `NSGlassEffectContainerView` (merges nearby glass shapes).
- **SwiftUI:** `.glassEffect`.
- **There is no public control of blur radius or refraction.** You get tint, shape and variant only [title: [Apple](https://developer.apple.com/documentation/appkit/nsglasseffectcontainerview), [WWDC25 310](https://developer.apple.com/videos/play/wwdc2025/310/); API details guess]. The Rio terminal uses it over a GPU-drawn surface from Rust [title: [rio glass.rs](https://docs.rs/crate/rio-window/0.5.14/source/src/platform_impl/macos/glass.rs)], so it can sit over Metal content.
- **Complaints:** window resizing performance [title: [forum 807970](https://developer.apple.com/forums/thread/807970)], and GPU and battery use [title: [MacRumors](https://forums.macrumors.com/threads/liquid-glass-performance-gpu-battery.2463522)]. No numbers from Apple.
- **Windows:** Mica and Acrylic through `DWMWA_SYSTEMBACKDROP_TYPE`, with as little control [title: [Microsoft](https://learn.microsoft.com/en-us/windows/win32/api/dwmapi/ne-dwmapi-dwm_systembackdrop_type)].
- **For AudioLab:**
  - Your look (Wide 45 lens, Light frosting, K7 square panels, plan 3.8) is not something the system glass can be set to.
  - In every option the **content glass stays AudioLab's own engine**: WebGL2 today, ported to Metal or Dawn shaders under N.
  - System glass could be used only for the window's own chrome (title bar, toolbar). The risk is two kinds of glass side by side.
  - Recommendation: own glass everywhere, the system's only for things the system draws anyway (menus, the title bar).

### 2.5 Cross-platform toolkits

- **Skia** (Chrome, Flutter, Bitwig):
  - BSD licence. Ganesh draws on GL, Vulkan, Metal and D3D; Graphite on Dawn, Metal and Vulkan. Chrome turned Graphite on for Apple Silicon Macs [read: [Google](https://blog.google/chromium/introducing-skia-graphite-chromes/)].
  - Excellent text (Chrome's).
  - It only draws. Windows, input, accessibility and widgets are yours to build.
  - A strong candidate for N's renderer if you want paths, gradients and text without writing shaders. It is large and its build is heavy [guess].
- **Flutter desktop:**
  - Impeller is the default on macOS (Metal) and Windows (Vulkan) since 3.47 (August 2026) [read: [Flutter 3.47](https://flutter.dev/blog/whats-new-in-flutter-3-47)].
  - Native views on macOS are "not fully functional" [read: [Flutter docs](https://docs.flutter.dev/platform-integration/macos/platform-views)], and nothing official exists for Windows. Plug-in editors would have to float.
  - Dart. **Not recommended.**
- **Dear ImGui:**
  - MIT, fast, any frame rate.
  - **No accessibility** [read: [discussion](https://ziggit.dev/t/accessible-immediate-mode-guis/12210)].
  - Only for developer panels.
- **Slint:**
  - GPL, royalty-free with an attribution badge, or commercial [read: [licence](https://raw.githubusercontent.com/slint-ui/slint/HEAD/LICENSE.md)].
  - Accessibility through AccessKit. Few large desktop apps, and no first-class embedding of foreign windows [guess].
- **Qt Quick 6:**
  - The scene graph runs on RHI: Metal on Mac, D3D11 or D3D12 on Windows [title: [Qt](https://doc.qt.io/qt/qrhi.html)].
  - The most mature accessibility of the cross-platform options [guess, widely known].
  - Embedding native windows with `WindowContainer` since 6.7 [title: [Qt](https://www.qt.io/blog/window-embedding-in-qt-quick)].
  - LGPLv3 or commercial [title: [Qt licensing](https://doc.qt.io/qt-6/licensing.html)].
  - Qt-based plug-ins froze in Cubase 13 on Windows [read: [Qt list](https://lists.qt-project.org/pipermail/interest/2024-February/039531.html)]. Mixing two Qt event loops in one process is a known source of trouble.
- **Qt Widgets:** CPU raster drawing. Not for 240 Hz surfaces.
- **JUCE:**
  - **No Metal renderer.** A JUCE developer said in June 2025 that "JUCE doesn't currently have a way to talk to Metal directly". CoreGraphics beats JUCE's OpenGL path on Apple Silicon [read: [JUCE forum](https://forum.juce.com/t/hardware-accelerated-drawing-on-apple-silicon/66477)].
  - Direct2D (JUCE 8) showed out-of-order frames at 240 Hz, fixed in June 2024 [read: [JUCE forum](https://forum.juce.com/t/juce-8-direct2d-high-refresh-rates-problem/61844)]. Later threads report regressions and freezes with several editors open [title: [JUCE forum](https://forum.juce.com/t/host-freezing-when-multiple-plugin-ui-instances-are-open-since-juce-8-0-8/67441)].
  - Licence: AGPLv3, free up to $20k revenue, Indie $800 perpetual, Pro $3,500 [read: [JUCE](https://forum.juce.com/t/important-changes-to-the-juce-end-user-licence-agreement-for-juce-8/61265)].
  - JUCE stays your fallback for **plug-in hosting** (R3a), not for the screens.
- **wgpu, Dawn, Vello:**
  - wgpu (Rust) and Dawn (C++, Chrome's WebGPU) are mature GPU layers on Metal, D3D12 and Vulkan [guess, widely known].
  - Vello, a compute-based 2D renderer, is pre-1.0 [title: [Vello](https://skia.googlesource.com/external/github.com/linebender/vello/+/refs/heads/main/sparse_strips)].
  - Dawn is the interesting one for AudioLab: **WGSL shaders written for WebGPU in Electron run unchanged on Dawn in a native app.** That is the bridge between W and N. Figma did exactly this move inside the browser.
- **Rust kits:**
  - egui (AccessKit merged), Iced (accessibility long open [title: [issue 552](https://github.com/iced-rs/iced/issues/552)]), Vizia (plug-in editors with nih-plug), Xilem (experimental), GPUI (not stable outside Zed).
  - AccessKit is the one piece worth borrowing: one accessibility tree, translated to UIA, NSAccessibility and AT-SPI [title: [AccessKit](https://accesskit.dev/)]. Whether its C interface is ready for a C++ app is a [guess] to check (task NU5).

### 2.6 Staying web

- **Chromium and Electron:**
  - Chromium-based browsers run `requestAnimationFrame` at the display rate, 240 Hz included, on Windows [read: [Blur Busters](https://www.blurbusters.com/microsoft-edge-browser-now-supports-240hz-on-testufo-motion-testing-website/)].
  - On the Mac: your own measurements show Chrome 157 at 240 fps on the glass test page (plan 3.7), and the app at 180 idle in v0.223 (3.11).
  - WebGPU shipped in Chrome 113 on Mac and Windows [read: [web.dev](https://web.dev/blog/webgpu-supported-major-browsers)], so Electron 45 (the desktop shell) has it [guess: on by default, as in Chrome].
- **Tauri:**
  - On the Mac it uses WKWebView, whose `requestAnimationFrame` is held near **60 fps** by a private WebKit preference. WebKit bug 294338 ("Allow WKWebView to support 120Hz") was still open on 24 Nov 2026 [read: [WebKit](https://bugs.webkit.org/show_bug.cgi?id=294338)].
  - Tauri closed the request as "not planned" [read: [Tauri #13978](https://github.com/tauri-apps/tauri/issues/13978)].
  - A plug-in flips the private flag, which means Mac App Store rejection, and its README claims macOS 26 lifted the cap [read: [README](https://docs.rs/crate/tauri-plugin-macos-fps/0.1.0/source/README.md)]. That claim is unconfirmed.
  - Safari itself keeps "Prefer page rendering updates near 60fps" **on by default** [read: [MacRumors](https://www.macrumors.com/how-to/enable-smoother-120hz-browsing-in-safari/)].
  - On Windows Tauri uses WebView2, which is Chromium [guess: same frame rate as Electron].
  - **Tauri fails U4f on the Mac.** Your pick R6a (keep Electron) was right.
- **Hybrid: native GPU views over a web page.**
  - Electron gives the window's native handle. A native add-on can put a Metal `NSView` or a child `HWND` over part of the page.
  - That view always sits **above** the page: no HTML menu, tooltip or glass can cover it, and size, focus and z-order are managed by hand [guess, with [Electron issue 41979](https://github.com/electron/electron/issues/41979) as an example of the work].
  - It is how a plug-in editor could be docked inside today's Electron window. It is a poor fit for the arrangement, which has menus, drags and glass over it.
- **HTML-in-Canvas** (Chrome origin trial to version 160) would let the glass engine sample real HTML. Its API changed in Chrome 150 and 155 [read: [Chrome](https://developer.chrome.com/blog/html-in-canvas-ot-changes)]. Do not build on it yet.

### 2.7 Plug-in windows

- **VST3:** the host gives the plug-in an `NSView` (Mac) or `HWND` (Windows) through `IPlugView::attached`, and resizes through `IPlugFrame::resizeView`.
  - Content scale is mostly ignored on the Mac, because the window's backing scale rules [title: [Steinberg forum](https://forums.steinberg.net/t/iplugview-contentscalesupport-and-macos/930318)].
  - On Windows, DPI-unaware plug-ins need the host's help, as in Cubase 11 (2.1).
- **AUv3:** the host asks for a view controller and adds its view [guess].
- **Native host:** the plug-in's view is a real subview and composites **above** the host's Metal layer in its rectangle. No glass or overlay can cover it, so overlays must avoid it or be child windows [guess, follows from how AppKit composites].
- **Electron:** a foreign `NSView` cannot be put inside Chromium's compositor in a supported way, so each plug-in gets its own window. This is what the test app does today, and it works (Serum 2 at 1190×740, picks report).
- **What this means:** docked plug-in editors are the one feature only N (or Q) gives. The floating editor window that Logic, Live and Bitwig also use works under W.

### 2.8 Text, high DPI, input latency

- **Text:**
  - The best results come from the system's own rasteriser: CoreText on Mac, DirectWrite on Windows. Zed does this in a glyph atlas [read: [Zed](https://zed.dev/blog/videogame), [Zed Windows](https://zed.dev/blog/zed-for-windows-is-here)].
  - Chromium's text is as good on both [guess].
  - Under N, text is the hardest single piece of the renderer: shaping (HarfBuzz or the system's), atlas, sub-pixel position, emoji. Plan a task for it, not a line.
- **High DPI:**
  - Mac: one backing scale per window.
  - Windows: per-monitor DPI with mixed scales across screens. Chromium and Qt handle both, and N must handle both by hand [guess].
- **Input latency:**
  - No source gave input-to-screen numbers for any of the options.
  - The reasoning [guess]: Chromium adds its compositor between the page's frame and the screen, and a native Metal view drawing for the target time with 2 or 3 drawables does not. That suggests about one frame of difference, 4.2 ms at 240 Hz.
  - Gate measurement G2 settles it with a camera or a photodiode, or with the system's own presentation timestamps.

### 2.9 Two platforms

- **Under W:** one code. The Mac and Windows differences are the shell's (`desktop/`), already handled.
- **Under N:** one renderer, one scene and widget layer, and one accessibility tree, written once in C++. Two of each of the following:
  - window shell: AppKit / Win32;
  - GPU back-end: Metal / D3D12, or both through Dawn;
  - text back-end: CoreText / DirectWrite;
  - accessibility back-end: NSAccessibility / UIA;
  - plug-in view embedding: NSView / HWND.
- My estimate of the platform part: **15 to 25 % of the interface work** [guess, by analogy with Zed's Windows port and Studio One's CCL]. Windows comes after the Mac (R5b).

---

## 3. Options ruled out, in one line each

- **SwiftUI as the main interface:** Mac only, and no evidence it holds dense views at 240 Hz.
- **JUCE graphics:** no Metal, CoreGraphics is CPU, Direct2D had high-refresh faults. Keep JUCE only as the plug-in hosting fallback.
- **Dear ImGui, GPUI:** no accessibility, and GPUI is not a stable library.
- **Flutter:** Dart, desktop multi-window still experimental, no working native child views.
- **Tauri:** 60 fps on the Mac.
- **Qt Widgets:** CPU drawing.
- **Rust kits (Iced, egui, Vizia, Slint, Xilem):** a second language beside the C++ engine, young accessibility, few large desktop apps. Worth borrowing AccessKit from, not building on.

---

## 4. The benchmark (macOS build machine, virtual)

What was built (`tools/native-lab/ui-bench/`):
- **The scene:** a 64-track arrangement scrolling at 800 px/s (clips, 12 notes per clip, beat lines, separators, track headers, playhead) and 1,000 meters (background, level, peak hold), all moving every frame. That is about 11,000 rectangles, rebuilt on the CPU every frame.
- **Three ways of drawing it:**
  - Metal: one instanced draw, `CAMetalDisplayLink` asking for 240 Hz, 3 drawables.
  - WebGL2 in Electron 45 (the desktop shell's version): instanced, the way the glass engine draws.
  - Canvas 2D in Electron: `fillRect`, the way the arrangement is drawn today.
- **Two measurements for each:**
  - at 3840x2160 off screen, every frame waited for (what a frame costs);
  - in a 1600x1000 window paced by the display (what the screen gets).

**Status: no numbers yet.**
- The workflow run (Actions, "UI bench (task RN4)", run 46003825128) waited in the queue for a macOS runner for 15 minutes and was then **cancelled before it started**, at 13:18 UTC. A Native engine run (task NB) was cancelled the same way.
- This task did not start it again, so as not to compete with the engine's Mac runs.
- The web half was checked on the cloud machine; it runs with no errors and draws about 11,000 rectangles a frame. That machine has no graphics card, so its times say nothing.
- To get the numbers:
  - **Runner:** start the workflow by hand (a few minutes; results on the branch `ui-bench-results`).
  - **Your Mac** (task NU1), which is worth more:
    - `swiftc -O tools/native-lab/ui-bench/metal/main.swift -o metalbench && ./metalbench 10`
    - then `tools/native-lab/ui-bench/web/bench.html?run=10` in Chrome.
- **Reading guide for when the numbers come.** Look at the frame time at 3840x2160 for each way of drawing, against 4.17 ms (240 Hz):
  - If WebGL2 is close to Metal, option W holds and the arrangement's problem is Canvas 2D, not Electron.
  - If Metal is several times faster than WebGL2, gate G leans to N.
  - What to expect [guess]: Canvas 2D will be the slowest by far, and WebGL2 and Metal within a small factor of each other, because both are one instanced draw. In that case most of the difference is in the CPU time to build the scene (JavaScript against Swift) and in the compositor's extra stage.

---

## 5. How large is a rewrite of today's interface

Counted by script from `index.html` (v0.228 and later commits on main, 5,956,601 bytes, 22,721 lines; about 2.26 MB of it is embedded data such as audio, icons and the demo song):

| What | Count |
|---|---|
| Buttons (`<button`) | 574 |
| Text and number fields, sliders, switches (`<input`) | 136 |
| Drop-down lists (`<select`) | 95 |
| Canvases | 86, of which 50 Canvas 2D contexts, plus the glass engine (WebGL2) |
| Named functions | 1,976 (plus several thousand arrow functions) |
| Event listeners | 809 |
| `aria-` attributes | 531 (a base for accessibility in any option) |
| Settings tabs | 11 named tabs (General, Audio, DAC, Layout, Glass, Colours, Keys, Files, Export, Navigation, Copy), about 124 settings (`docs/settings-audit.md`) |
| Devices with their own display | 42 effects and 3 MIDI effects (`FXDEF`), 32 instruments (`PRESETS`) |
| Windows and sheets | about 17 (plan 1.2): mixer, devices, piano roll, envelope editor, modular grid, presets, audio editor, visualiser, AI voices, Voice, Venom, Time Machine, export, about, settings, audio to MIDI, browser |

**What this means:**
- The native-mac plan put stage 4 (all native screens) at **150 to 250 tasks**. This count supports that.
- The interface is about **3.7 MB of code and markup**, most of it behaviour (edits, drags, menus, undo) rather than drawing.
- About 60 named drawing functions and one display per device are the part that moves to the GPU.
- Under the recommended path, the **drawing part (perhaps a fifth of the work [guess]) is done once under W and ported, not rewritten**. Forms, lists and settings, the long tail, are left for last.

---

## 6. Migration path: never without a working app

Every stage ends with a released Electron app that works on your Mac. Stages U0 to U3 are inside the present plan (R2b, R6a) and do not need the native decision.

| Stage | What | Proof | You always have |
|---|---|---|---|
| **U0 (now, with the engine's N3)** | Meters, playhead and CPU through the shared-memory snapshot read once per frame (RN1 U1, NR12). The frame-rate read-out (v0.228) also records the slowest frame and missed frames. | Meters at 240 with no messages from the audio thread. | Today's app. |
| **U1** | **The scene layer**: a small description of what a surface draws (rectangles, rounded rectangles, lines, glyph runs, textures, clip rectangles), with one WebGL2 renderer (the glass engine's code is the start). The arrangement draws through it, Canvas 2D kept behind a switch. Text: glyph atlas from the page's own fonts. | Your Mac: scrolling the arrangement with Settings open at 240 fps (today 90 to 120). Pixel compare with the Canvas 2D drawing on the build machine. | The app, faster. |
| **U2** | Piano roll, mixer meters, device displays and the master lane through the same scene layer. Hit-testing and an accessibility mirror (hidden ARIA elements) generated from the scene. | 240 fps in each window on your Mac. VoiceOver reads tracks and faders. | The app. |
| **U3** | WebGPU renderer for the scene layer next to WebGL2, chosen at start, with a fallback (Figma's pattern). Its shaders in WGSL. | Same pictures. Frame times on your Mac. | The app. |
| **Gate G (after the engine has moved, R2b)** | Measure on your Mac: G1, 240 fps in every window with 64 tracks playing. G2, input to screen, Electron against a native Metal test window drawing the same scene. G3, whether you want docked plug-in editors. Then decide: stay W, go N, or Q. | A short decision page with numbers. | The app. |
| **U4 (if N)** | A native shell: AppKit window, Metal through Dawn (or straight Metal), the U3 WGSL shaders and the scene layer ported to C++. **One surface first** (the arrangement) in a native window beside the Electron app, both reading the same engine (the engine owns all state, plan R2b). | The arrangement at 240 in the native window. Electron still runs everything. | Both. |
| **U5** | The native window takes over the main screens one at a time: arrangement, mixer, piano roll, device panel with docked plug-in editors. Settings, browser and dialogs stay in a web view inside the native window (WKWebView is fine at 60 fps for forms) until last. Accessibility: `NSAccessibilityElement` per control from the scene's tree. | Each screen switchable back to Electron for a few releases. | Both. |
| **U6** | Windows shell: Win32, Dawn on D3D12, DirectWrite, UIA (after the engine's Windows stage, R5b). | The same scene tests on a Windows runner. | Both. |
| **U7** | The last web panels go native; Electron is retired when nothing uses it. | | The native app. |

**Rules for every stage:**
- The engine keeps all state, and the interface is a view on it (from RN1).
- Nothing draws from the audio thread.
- Every surface draws for the display's target time and never assumes 240.
- One switch per surface brings back the old drawing.

---

## 7. Proposed tasks

| Task | What | Size | Needs your Mac |
|---|---|---|---|
| **NU1** | Run `tools/native-lab/ui-bench` on your Mac: `metalbench` and `bench.html?run=10` in Chrome and in AudioLab's Electron, at 240 Hz on the Odyssey. Gives the real Metal against WebGL2 against Canvas 2D numbers. | 1 | yes (10 minutes) |
| **NU2** | Scene layer and WebGL2 renderer (U1). The arrangement draws through it behind a switch, with a pixel compare against Canvas 2D. | 2 to 3 | check |
| **NU3** | Text on the GPU: glyph atlas from the page's fonts, sub-pixel positions, compared with Canvas 2D text at 1x, 1.5x and 2x. | 1 to 2 | check |
| **NU4** | Piano roll, meters, device displays through the scene layer (U2), with an accessibility mirror. | 3 to 5 | check |
| **NU5** | Spike: AccessKit from C++ (or own tree) on a Metal view with 8 knobs and 8 faders; VoiceOver reads and sets them. | 1 to 2 | yes |
| **NU6** | Spike: Dawn in a native Mac window drawing the same WGSL scene as Electron's WebGPU. Frame times and the presentation timestamps (input latency) against Electron. This is gate measurement G2. | 2 | yes |
| **NU7** | Spike: a VST3 editor docked as a child `NSView` in a Metal window, with a menu and a glass panel next to it (not over it); resize and scale. | 1 to 2 | yes |
| **NU8** | WebGPU renderer for the scene layer (U3) with WebGL2 fallback. | 2 | check |
| **NU9** | Decision page for gate G with the measured numbers. | 1 | pick |

NU1 is the cheapest and most useful next step. NU2 to NU4 make today's app faster whatever is decided, so nothing is wasted if the answer at the gate is "stay on Electron".

---

## 8. Open points

1. Whether WKWebView on macOS 26 and 27 still holds `requestAnimationFrame` near 60 fps. The WebKit bug says yes; a plug-in's README says the cap was lifted. It matters only for a web view inside a native app (U5), where 60 fps is acceptable for forms.
2. Whether Electron on your Mac reaches 240 Hz in every window once the arrangement is on the GPU (G1).
3. Input-to-screen latency of Electron against native on your Mac (G2). No source gives numbers.
4. AccessKit's C interface for a C++ app (NU5).
5. Qt Quick's behaviour at 240 Hz. No measurements found.
6. Whether `NSGlassEffectView` samples Metal content without cost, and its GPU cost per instance. No numbers from Apple.
7. The macOS 27 ProMotion judder thread (forum 840214, title only).
8. Which UI toolkits Ableton, Pro Tools, Kontakt, FabFilter and Reason use. No primary source found.

## 9. Sources

All links are in the findings above. The main ones:
- **Ableton:** [Metal in Live 11.2](https://help.ableton.com/hc/en-us/articles/6012665671836-Metal-based-GPU-Rendering-in-Live-11-2-on-macOS), [Live 12 accessibility](https://www.ableton.com/en/live-manual/12/accessibility-and-keyboard-navigation)
- **Bitwig:** [5.2 notes](https://downloads.bitwig.com/5.2/Release-Notes-5.2.html), [Skia back-ends](https://bitwig.com/support/technical_support/the-bitwig-studio-window-is-not-displayed-correctly-after-updating-to-version-52-on-linux-67)
- **Studio One:** [CCL](https://kreatives.org/platform/blog/the-ccl-framework)
- **Cubase:** [DPI-unaware plug-ins](https://www.steinberg.help/r/cubase-11-using-dpi-unaware-plug-ins-on-windows)
- **Figma:** [WebGPU](https://www.figma.com/blog/figma-rendering-powered-by-webgpu/)
- **Zed:** [renderer](https://zed.dev/blog/videogame), [120 fps](https://zed.dev/blog/120fps), [Windows](https://zed.dev/blog/zed-for-windows-is-here)
- **Ardour:** [canvas](https://ardour.org/canvas.html)
- **Apple forums:** [763426](https://developer.apple.com/forums/thread/763426), [717481](https://developer.apple.com/forums/thread/717481)
- **Plugable:** [HDMI 2.1 on Mac](https://plugable.com/en-ca/blogs/news/hdmi-2-1-on-mac-how-the-latest-macos-expands-external-display-support)
- **WebKit, Safari and Tauri:** [bug 294338](https://bugs.webkit.org/show_bug.cgi?id=294338), [Tauri #13978](https://github.com/tauri-apps/tauri/issues/13978), [macos-fps README](https://docs.rs/crate/tauri-plugin-macos-fps/0.1.0/source/README.md), [Safari 60 fps setting](https://www.macrumors.com/how-to/enable-smoother-120hz-browsing-in-safari/)
- **Chromium and WebGPU:** [Blur Busters 240 Hz](https://www.blurbusters.com/microsoft-edge-browser-now-supports-240hz-on-testufo-motion-testing-website/), [WebGPU support](https://web.dev/blog/webgpu-supported-major-browsers), [HTML-in-Canvas](https://developer.chrome.com/blog/html-in-canvas-ot-changes)
- **JUCE:** [Metal](https://forum.juce.com/t/hardware-accelerated-drawing-on-apple-silicon/66477), [Direct2D at 240 Hz](https://forum.juce.com/t/juce-8-direct2d-high-refresh-rates-problem/61844), [licence](https://forum.juce.com/t/important-changes-to-the-juce-end-user-licence-agreement-for-juce-8/61265)
- **Flutter:** [3.47](https://flutter.dev/blog/whats-new-in-flutter-3-47), [macOS platform views](https://docs.flutter.dev/platform-integration/macos/platform-views)
- **Slint:** [licence](https://raw.githubusercontent.com/slint-ui/slint/HEAD/LICENSE.md)
- **Qt:** [Qt list on Cubase 13](https://lists.qt-project.org/pipermail/interest/2024-February/039531.html)
- **Accessibility:** [AppleVis on Logic](https://applevis.com/forum/macos-mac-apps/has-any-blind-engineer-mixed-or-mastered-professionally-logic-pro-real-studio), [Flo Tools](https://www.production-expert.com/production-expert-1/flo-tools-2026-pro-tools-accessibility-macros-ten-years-on), [Blender VPAT issue](https://projects.blender.org/blender/blender/issues/104144)
- **Liquid Glass:** [Apple: NSGlassEffectContainerView](https://developer.apple.com/documentation/appkit/nsglasseffectcontainerview), [WWDC25 310](https://developer.apple.com/videos/play/wwdc2025/310/)
