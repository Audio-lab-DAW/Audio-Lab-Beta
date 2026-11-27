# AudioLab Pro: speed of working, feel and smoothness (task UX1, 27 November 2026)

**Pick page:** https://claude.ai/artifact/Un3Rpwe5SzD5b6FjprqzoY (title "AudioLab speed and feel"). 18 options S1 to S18 in five groups, each with a live mock-up. To answer, pick on the page and paste the line from the bar at the bottom, for example `UX1 picks: S1 S3 S7 S9 S13 S15`.

Written for the scheduling chat. **Nothing in index.html, desktop/ or native/ was changed.** App version measured: v0.263. Files: `tools/design-lab/ux1/` (the page `speed-feel.html`, the measurement script `measure_ux1.py`, its results `results-2026-11-27.json`, the page check `check_page.py`).

The user asked on 27 Nov (20:02 Brussels) for interface research on **speed of working** and **feel and smoothness**. Their biggest pains in big psytrance projects are **latency when playing** and **mixing clarity**. Long sessions (UX2) and first use and help (UX3) are separate tasks. This one does not repeat what is already picked: the command palette K1 and menus R2 (OV, `docs/design-round-5-overlays.md`), design round 2 including the catalogue browser B3 (DS), the commands registry and macros (XT, `docs/extensions-plan.md`), and the controller layer and Push 1 (FT). Each option below says which of those it builds on.

## 1. Summary

- **Common tasks take 74 actions today** across 15 typical psytrance jobs (clicks, keys and drags on the shortest path, counted in the code). **With the recommended picks plus S2, S4, S5, S6 and S8 it would be 50 (−32 %).** The biggest gaps are:
  - no time verbs (duplicate or insert time across all tracks);
  - clips that cannot loop;
  - no search in either browser;
  - automation that only exists inside clips;
  - common commands without keys (quantize, solo, mute, rename, browser, piano roll; no next-section key).
- **Every zoom is eased again by 40 ms**, on top of the trackpad's own smoothing. At 240 Hz the view reaches 90 % of a pinch about 96 ms after the fingers. Two-finger scrolling is already applied directly and is fine.
- **A pinch costs about five times a scroll.** Measured at 1280×800: 61 ms against 12 ms of main thread per frame. 15 ms of each pinch frame is page layout: the linked zoom also changes the track height, so the header rows are laid out again on every frame.
- **Playing while the screen is busy adds jitter.** A key of the keyboard piano reaches `noteOn` in 1.6 ms when idle. While playing with the mixer open it took a median of 17 ms and a worst case of 51 ms (cloud, small size), because the key waits for the frame being drawn. MIDI arrives on the same main thread. This is the part of "latency when playing" that the interface causes. The audio buffer (Auto, 256 samples) is not the problem.
- **Scrolling draws the whole arrangement on every frame**, as GS3 already found: 12 ms per frame at 1280×800 and 50 ms at the user's size on the cloud machine.
- **Recommendation (the six five-star options):**
  - S1 time verbs
  - S3 pop-up browser with search
  - S7 single-key layer with "G then" jumps
  - S9 direct trackpad (no extra easing)
  - S13 zoom without layout
  - S15 steady timing when playing

## 2. Today's measurements

### 2.1 Clicks and keys for 15 tasks (v0.263, read in index.html; line numbers of v0.263)

Counting rules: a double-click counts as 1 click, a typed word as 1 action, and a held modifier adds nothing. The project is a 145 BPM project with about 30 tracks. Ableton figures are estimates from its manual.

| # | Task | Shortest path today | Today | With picks | Ableton 12 (est.) |
|---|---|---|---|---|---|
| 1 | 16-bar loop at bar 33, play | drag on the ruler 33→49 (sets and turns on the loop, `loopSet` 7085), double-click the ruler (7117) | 2 | 2 | 3 |
| 2 | Kick + bass, bass ducked by kick | ⌘⇧I, double-click Kick; ⌘⇧I, double-click Psy Bass; Shift+M; click Cables (off by default, `MXSD` 9787); drag a cable; "ducks" (`abxMake` 17440); Shift+M | 9 | 6 (S5) | ≈ 12 |
| 3 | Duplicate a 16-bar section, all tracks | Alt+right-drag a range (7067), ⌘C, click the top header, drag the playhead, ⌘V. The paste overwrites, and the range drag has no vertical auto-scroll, so all tracks must be on screen | 5 | 2 (S1) | 3 |
| 4 | Filter sweep over a 16-bar build | right-click the lane button › Filter cutoff, Esc, two clicks. Points can only go inside one clip (`laneClip` 5360), so four clips take 8 clicks (11 in total) | 5 | 4 (S4) | ≈ 6 |
| 5 | Bounce one track | right-click the header › Bounce to new audio track (5126) | 2 | 2 | 2 |
| 6 | Find a preset by name | right-click › Change instrument…, look through the tiles, double-click, pick the sub-preset. **There is no search field in either browser** (only Settings and Shortcuts have one, 3239 and 3406) | ≈ 5 + looking | 3 (S3) | 3 |
| 7 | Send reverb from two tracks | right-click › New reverb return, send this track (`retNew` 9072); right-click › Send to Return A | 4 | 4 | 2–6 |
| 8 | Rolling bass (off-beat 1/16), 4 bars | double-click the lane, B, paint, right-click ×4, ⌘A, Shift-drag, ⌘A, Shift-drag, Esc. ⌘B repeats by the selection's span, not the bar, so off-beat patterns drift by 1/16 (7374) | 12 | 7 (S8, S2) | ≈ 9 |
| 9 | Loop a 1-bar clip for 16 bars | click, ⌘D, Shift-click, three doubling Shift-drags. Clips cannot loop (`res` 7095) | 6 | 1 (S2) | 1 |
| 10 | Solo the drum tracks | Shift-click the headers, ⌘G to group, then S on the group. The S button and the `solo` command act on one track only | 4 | 3 (S7) | 4 |
| 11 | EQ, high-pass at 30 Hz | click the header, "+ Add effect" (modal), double-click Pro EQ, double-click the graph at about 30 Hz (`eqNewBand` 6802) | 4 | 4 | ≈ 5 |
| 12 | Rename and recolour a track | Alt+double-click the name, type, Enter; right-click › swatch. A plain double-click opens the devices (15247) | 5 | 4 (S6) | 5–6 |
| 13 | Jump to the drop and play | right-click the section › Play from here (7160). A left-click on a section loops it; `secJump` has no key | 2 | 2 (keyboard only with S7) | 2 |
| 14 | Export the song to WAV | ⌘E, Export mix, Esc | 3 | 3 | 3 |
| 15 | Quantize to 1/16 and nudge 1/16 | right-click › Quantize notes (1/16, start only); Alt+→ ×4. The arrow step follows the zoom (`ajStep` 18122) | 6 | 3 (S7, S6) | 4–5 |
| | **Total** | | **74** | **50** | **≈ 67** |

Already strong today: send/return in 4 clicks, bounce and freeze in 2–3, ⌘E export, and the section menu's "Play from here".

### 2.2 Input to paint, and frame times (`tools/design-lab/ux1/measure_ux1.py`)

Method:
- **Set-up:** the same as `tools/ui-tests/frametime.py` (Fractals: 31 tracks and 364 clips; glass engine on; SwiftShader).
- **Input:** real browser input sent through the Chrome DevTools protocol (`Input.dispatchMouseEvent` / `dispatchKeyEvent`), so it takes the same path as a trackpad, mouse or key on the Mac.
- **Timings:**
  - **queue** runs from the event's own time stamp to the app's first listener;
  - **first drawn** runs to the end of the first `drawArr` that shows the change;
  - **90 %** runs to the drawing that reaches 90 % of the final change.
- **Sizes:** "small" is 1280×800 at 1×. It is closer to the M4's speed, because the cloud machine rasterises in software. "User" is 2194×1139 at 1.75× (3840×1993 px).

| Input | Today's handling | Small: queue / first / 90 % | User size: queue / first / 90 % |
|---|---|---|---|
| Two-finger scroll (deltaX 12) | applied directly (arr wheel handler, 7125) | 6.0 / 8.9 / 8.9 ms | 19.7 / 24.0 / 24.0 ms |
| Notched wheel with Shift (deltaY 100) | `smoothPan`, τ = 40 ms | 5.7 / 34 / 142 ms | 50 / 140 / 392 ms |
| Trackpad pinch (ctrlKey wheel, deltaY −6) | `smoothZoom`, τ = 40 ms | 5.3 / 40 / 149 ms | 57 / 137 / 488 ms |
| Clip drag, one 12 px move | pointermove is held until the next frame (Chrome) | – | 14 / 17 / 17 ms |
| Keyboard piano key, idle | `noteOn` in the key handler (5708) | 1.6 → note 1.7 ms | 4.2 → note 4.3 ms |
| Same key while playing, mixer open | waits for the current frame | median 17, 90 % 43, worst 51 ms | median 94, 90 % 140, worst 188 ms |

| Main-thread ms per frame (style + layout) | idle | scroll | pinch | clip drag | playing + mixer |
|---|---|---|---|---|---|
| small | 1.0 (0.2) | 12.4 (0.5) | **60.9 (15.4)** | – | 63.1 (3.0) |
| user size | 5.2–12.4 | 49.6 (0.6) | **204–223 (13.6–15.7)** | 29.1 (0.5) | 100–318 (4–5) |

**Model for the Mac at 240 Hz.** `szStep` eases with `1 − exp(−dt/40)` per frame. After one input that is:
- 50 % at 28 ms;
- 90 % at 92 ms (96 ms including the first frame);
- about 250 ms before the remaining zoom falls below its stop threshold.

macOS already smooths a pinch. So the 40 ms easing is a second low-pass filter, and the view trails the fingers by roughly 90 ms. The research threshold for noticing lag in indirect dragging is about 55 ms (Deber et al. 2015).

A JavaScript profile of a pinch is 78 % "(program)", meaning raster and layout rather than script, which fits the layout numbers above.

The audio context in the test reported a 10 ms base latency with the `balanced` hint. On the Mac, the app's Auto buffer starts at 256 samples (`UI.lat4`, line 3844).

## 3. Findings with sources

All sources were opened on 27 Nov 2026 by a research helper. "(not verified)" means the page could not be read.

**What makes DAWs fast**
- **Ableton Live 12** has single chords for time:
  - Duplicate Time ⌘⇧D, Delete Time ⌘⇧⌫, Insert Silence ⌘I;
  - loop brace ⌘L, consolidate ⌘J, split ⌘E;
  - browser search ⌘F, hot-swap Q;
  - a plain-key layer: B draw, Z/X zoom to the selection and back, S solo, F1–F8 activate tracks.

  [Live 12 keyboard shortcuts](https://www.ableton.com/en/live-manual/12/live-keyboard-shortcuts/). Leads to S1, S7, S12.
- **Bitwig's Inspector** follows the selection: clip, note, device, automation point or track ([Inspector](https://bitwig.com/userguide/latest/meet_inspector_panel)). Its pop-up browser opens where you clicked with the focus in search, arrows audition in Live Preview, and S jumps back to search ([browsers](https://www.bitwig.com/userguide/latest/browsers), [common elements](https://bitwig.com/userguide/latest/common_browser_elements)). Leads to S3, S6.
- **REAPER:** every command is an action with an id. Custom actions chain several actions with "consolidate undo points" ([Sound On Sound](https://www.soundonsound.com/techniques/automate-anything-reapers-custom-actions)). XT already covers this; S8 adds repetition.
- **FL Studio's playlist** has single-key tools (P draw, B paint repeated clips, C slice, Shift+Z zoom to the selection) and "make unique" ([Playlist](https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/playlist.htm)). Leads to S2 (painting repeats).
- **Logic:** T opens a tool menu at the pointer, and single keys pick the tool ([Tool menu keys](https://support.apple.com/guide/logicpro/lgcp0182c4e5/mac)).

**Keyboard-first apps**
- **Vim:** operator + motion with a count ("d4w"), and "." repeats the last change (Vim `usr_04`). Leads to S8.
- **Figma:** Space-drag to pan, Shift+1 to fit, Shift+2 to the selection ([shortcuts](https://help.figma.com/hc/en-us/articles/360040328653)). Figma left the DOM and 2D canvas for a tiled WebGL engine ([Figma blog](https://www.figma.com/blog/building-a-professional-design-tool-on-the-web/)). Leads to S12, S14.
- **Linear:**
  - ⌘K, single-letter keys, and "G then I" sequences ([navigation](https://linear.app/enablement/guide/navigating-linear));
  - it feels fast because of local data, optimistic edits, per-field updates, and animations of 0.1–0.25 s ([performance.dev](https://performance.dev/how-is-linear-so-fast-a-technical-breakdown)).

  Leads to S7, S18.
- **Raycast:** aliases first, then fuzzy title match, then frecency per query ([search bar](https://manual.raycast.com/search-bar)). Leads to S3's ranking.

**macOS gestures**
- **Apple HIG:** pinch to zoom, two-finger scroll, smart zoom, force click; do not redefine system gestures ([Pointing devices](https://developer.apple.com/design/human-interface-guidelines/pointing-devices)).
- **No momentum flag on the web.** Natively, `NSEvent.momentumPhase` marks momentum events. The web exposes only deltas, and a WICG request for an inertia flag was never resolved ([WICG](https://discourse.wicg.io/t/inertia-momentum-property-to-scroll-and-wheel-events/1565)). So treat trackpad deltas as direct movement and do not add a second inertia. Leads to S9.
- **Pinch in Chromium** arrives as `wheel` with `ctrlKey`. Safari uses `GestureEvent` ([Burzo](https://dev.to/danburzo/pinch-me-i-m-zooming-gestures-in-the-dom-a0e), [MDN GestureEvent](https://developer.mozilla.org/en-US/docs/Web/API/GestureEvent)). AudioLab already handles both (ZSK, 18227).
- **Force click** exists only as WebKit-only `webkitmouseforce*` events, so it is not available in Electron ([MDN](https://developer.mozilla.org/en-US/docs/Web/API/Force_Touch_events)). No option uses it.
- **The Magic Mouse** has no pinch, so every zoom needs a key route as well (S12).

**Smooth zoom and scroll**
- **UIScrollView deceleration** is 0.998 per ms (normal) or 0.99 (fast), and the rubber band is b = (1 − 1/(x·0.55/d + 1))·d ([Lobanov](https://medium.com/@esskeetit/scrolling-mechanics-of-uiscrollview-142adee1142c), [gist](https://gist.github.com/originell/6961057)). Leads to S10.
- **Only `transform` and `opacity` skip layout and paint** ([web.dev](https://web.dev/articles/stick-to-compositor-only-properties-and-manage-layer-count)). Leads to S13.
- **Confluence Whiteboards** redraws only when something changed and uses sparse tiles and reused typed arrays: p90 pan and zoom is 2 ms ([Atlassian](https://www.atlassian.com/engineering/rendering-like-butter-a-confluence-whiteboards-story)). Leads to S14.
- **Scroll work under about 10 ms goes unnoticed and over 15 ms is felt.** Momentum is supplied only where the system does not supply it ([ultra-scroll-mac](https://github.com/jdtsmith/ultra-scroll-mac)). That "eased wheel input on a trackpad adds lag" is our own conclusion, which this source and the measurements support.

**Input latency at high refresh rates**
- **Chrome aligns continuous events** (wheel, pointermove) to the next frame. Discrete events (keydown, pointerdown) fire at once ([aligned input](https://developer.chrome.com/blog/aligning-input-events)). This fits the 14 ms drag queue measured here.
- **Pointer helpers:** `getCoalescedEvents` (every point) and `getPredictedEvents` (an estimate of where the pointer is going) ([MDN](https://developer.mozilla.org/en-US/docs/Web/API/PointerEvent/getPredictedEvents)); `pointerrawupdate` for tiny, latency-critical handlers. Lead to S11.
- **`desynchronized: true` canvas** skips the DOM update path, but nothing from the DOM may sit above it ([Chrome](https://developer.chrome.com/blog/desynchronized)). It only fits a playhead or cursor overlay; macOS behaviour is not verified. It is listed in S11 as a later experiment.
- **Input delay** is `processingStart − startTime` ([Event Timing](https://www.w3.org/TR/event-timing/)). `scheduler.yield()` resumes before other queued tasks ([Chrome](https://developer.chrome.com/blog/use-scheduler-yield)). Leads to S15, S18.
- **Web Audio and MIDI timing:** read `baseLatency` and `outputLatency` ([MDN](https://developer.mozilla.org/en-US/docs/Web/API/AudioContext/baseLatency)). Web MIDI `send(data, timestamp)` schedules output on the `performance.now()` clock ([MDN](https://developer.mozilla.org/en-US/docs/Web/API/MIDIOutput/send)). Leads to S15.
- **Refresh rate on the Mac:** Chrome on macOS was moving to `CADisplayLink` to match the display's refresh rate ([MacObserver](https://www.macobserver.com/macos/chrome-for-mac-to-soon-offer-smoother-refresh-rates-on-macos-14-or-later/)). Measure the rAF rate rather than assume 240 Hz (S17). (Whether Electron runs rAF at 240 Hz on the M4 with the G80SD: not verified here; the user's frame-rate read-out answers it.)

**Perception**
- **Nielsen's limits:** 0.1 s feels instant, 1 s keeps the flow of thought, 10 s loses attention ([NN/g](https://www.nngroup.com/articles/response-times-3-important-limits/)). Doherty: productivity rises below 400 ms ([Laws of UX](https://lawsofux.com/doherty-threshold/)). Leads to S18.
- **Deber et al., CHI 2015:** the just-noticeable lag is 11 ms for direct dragging, **55 ms for indirect dragging** (mouse or trackpad), 69 ms for direct tapping and 96 ms for indirect tapping. Improvements of 8.3 ms were noticeable ([PDF](https://dcmpx.remotevs.com/com/tactuallabs/www/SL/papers/howMuchFasterIsFastEnoughCHI15.pdf)). Leads to S9, S11.
- **Wessel & Wright 2002:** aim for about 10 ms of latency for musical control, with jitter of 1 ms or less ([PDF](https://ccrma.stanford.edu/workshops/mid2005/Wright-SIMS2002.pdf)). Leads to S15.
- **NVIDIA Reflex:** do not queue frames; sample input as late as possible ([NVIDIA](https://www.nvidia.com/en-gb/geforce/news/reflex-low-latency-platform)).

**Animation timing**
- **Material:** 150–200 ms on desktop, and over 400 ms feels slow ([M1](https://m1.material.io/motion/duration-easing.html)). Material 3's short tokens are 50–200 ms ([Motion.md](https://github.com/material-components/material-components-android/blob/master/docs/theming/Motion.md)).
- **Fluent:** 83, 167 and 250 ms ([timing](https://learn.microsoft.com/en-us/windows/apps/design/motion/timing-and-easing)).
- **Apple HIG Motion:** be brief, avoid motion on frequent interactions, never make people wait for an animation, and make motion optional ([HIG Motion](https://developer.apple.com/design/human-interface-guidelines/motion)).

  Leads to S16.

**Frame budget**
- **web.dev:** about 10 of the 16.7 ms at 60 Hz are left for the page. The same ratio at 240 Hz leaves about 2.5 ms for the app ([web.dev](https://web.dev/articles/rendering-performance)).
- **Avoid forced layout** ([web.dev](https://web.dev/articles/avoid-large-complex-layouts-and-layout-thrashing)).
- **Canvas:** layer canvases by how often they change ([MDN](https://developer.mozilla.org/en-US/docs/Web/API/Canvas_API/Tutorial/Optimizing_canvas)); use OffscreenCanvas in workers ([web.dev](https://web.dev/articles/offscreen-canvas)).
- **Long Animation Frames (LoAF)** only reports frames over 50 ms, so the 240 Hz target needs its own histogram ([Chrome](https://developer.chrome.com/docs/web-platform/long-animation-frames)). Leads to S17.
- **Keystroke-level model**, used for the seconds on the page: a click or point is about 1.1–1.5 s, a key about 0.28 s, a mental step about 1.35 s ([KLM](https://en.wikipedia.org/wiki/Keystroke-level_model)).

## 4. Options (as on the pick page)

★ is the value for this user. The recommendation is the six five-star options.

| Id | Option | ★ | Measured or estimated saving | Builds on | Lane |
|---|---|---|---|---|---|
| **S1** | Time verbs: duplicate, insert and delete time across all tracks; L loops the selection | 5 | task 3: 5 → 2 actions, about 3 s each, no overwriting paste | F2 Arranger moves, sections, K1, XT ids `time.*` | C (FT), A draws the ruler selection |
| S2 | Loop a clip by dragging its corner notch | 4 | task 9: 6 → 1, about 6 s | F1 linked clips, F4 automation clips | C, A draws repeats |
| **S3** | Pop-up browser with search where you click; arrows audition, Enter inserts, frecency per word | 5 | task 6: ≈ 5 clicks + 5–10 s of looking → ≈ 3 s | DS B3 (S3 is how B3 opens and is searched), K1 matcher, F31 | A (browser), F (sheet, focus) |
| S4 | Automation drawn over a time range, across clips, with shapes | 4 | task 4 over four clips: 11 → 4, about 8 s, no gaps | F3, F4, F20 Build designer | C |
| S5 | "Duck to ▸" in the track menu, kick-like tracks first | 3 | sidechain part of task 2: 5 → 2, 4–8 s | R2 menus, cables (kept), `abxMake`, NI | F menu, C routing |
| S6 | Inspector that follows the selection | 3 | tasks 12 and 15: 5 → 4, 6 → 3 | DS layout, MD read-outs | A with G |
| **S7** | Single-key layer (S, M, Q, R, L, [ ], ← → by the grid, Enter), K toggles the keyboard piano, "G then M/P/B/D" | 5 | one menu command (≈ 2.6 s) → one key (0.3 s); tasks 10, 13, 15 | XT registry, K1 shows keys, `SCA` | H, C for new actions |
| S8 | "." repeats the last edit; counts before commands; grid-true duplicate in the piano roll | 3 | task 8: 12 → 7 | XT macros | H |
| **S9** | Direct trackpad: pinch and scroll 1:1 in the same frame; only notched wheels eased (15 ms) | 5 | ≈ 90 ms less lag per pinch at 240 Hz | ZS presets, `zoomAround`, `smoothZoom` | A |
| S10 | Grab and fling (middle button, overview) with 0.998/ms glide and rubber band | 3 | one flick instead of 4–6 drags | `map`, `OVW` | A |
| S11 | Coalesced points for freehand drawing, predicted point for drag ghosts | 3 | smooth curves at any speed; ghost about one frame closer | automation pencil, PR paint | A, C |
| S12 | Zoom keys Z / X (stack), ⇧1 / ⇧2 / ⇧3, 160 ms, interruptible | 4 | whole song → drop → back: ≈ 3 s → 0.6 s | `zoomAround`, S7 | A |
| **S13** | Zoom without page layout: header rows moved by transforms during a pinch, laid out once at rest; arrangement picture scaled between redraws | 5 | pinch frame from 61 to about 12 ms (cloud, small); mock-up measures it in the viewer's browser | GS3, glass engine | A, with I (DV) for the header frame |
| S14 | Tiled arrangement: draw only the new strip when scrolling, only touched tiles on an edit | 4 | 70–95 % less drawing while scrolling (estimate; the mock-up measures it) | GS3 strip-shift experiment, glass engine | A with the glass engine |
| **S15** | Steady timing when playing: notes at the event's time stamp + small fixed offset; meters and mixer at half rate while armed; no task over 2 ms | 5 | key → note today median 17, worst 51 ms jitter (small) → constant, jitter < 1 ms | FT-C1a controller layer, `noteOn`, Auto buffer | C, E (meter rate) |
| S16 | Four motion timings as LOOK tokens (0 / 90 / 150 / 220 ms), one ease-out, interruptible | 4 | ≈ 150 ms per panel open or close against 300 | LK, OV | LK, then F |
| S17 | Frame guard: histogram against the real frame, slowest part named, budget per part in the gate | 3 | keeps the gains from slipping back | GS3 read-out, `frametime.py`, RG | E and the release gate |
| S18 | An answer within 100 ms; bounce, freeze, export and analysis in slices or a worker | 3 | no frozen screen | particle threads, NI worker | C, D, F |

Notes for whoever builds them:
- **S7 and the keyboard piano.** Plain letters must yield to the keyboard piano when it is on (`liveTracks()` uses the armed track or the piano). K is not a piano key in either layout and is free.
- **Mod+L is MIDI learn today.** S1 therefore uses plain L for loop selection rather than Ableton's ⌘L.
- **S15's offset.** Measure the 95th percentile of the handler delay over the last 20 notes, plus 1 ms, capped at about 8 ms on the Mac. Start notes at `getOutputTimestamp()`-mapped `event.timeStamp + offset`. Apply the same to `MIDIMessageEvent.timeStamp` in the controller layer.
- **S9 keeps the "Speed" and "Anchor" settings.** It changes only what happens when the input is a pinch or a pixel-mode trackpad scroll: `szStep` is bypassed and `zoomAround` is applied in the same frame.

## 5. Proposed tasks (after the user's picks)

| Task | Contents | Lane | Depends on |
|---|---|---|---|
| UX-A1 | S9 direct trackpad and S13 zoom without layout (one task: both live in `zsWheel`, `szStep`, header layout); frame test of pinch vs scroll at the user's size | A | none |
| UX-A2 | S14 tiled arrangement with the glass engine reading tiles | A (+ GS) | UX-A1 |
| UX-A3 | S12 zoom keys and stack, S10 fling, S11 drag ghost | A | S7 registry entries |
| UX-C1 | S15 steady timing for keys and MIDI; with lane E: meters at half rate while armed | C, E | none |
| UX-C2 | S1 time verbs (with F2 Arranger moves) and S2 looping clips | C, A | none |
| UX-C3 | S4 automation across clips (with F3 and F4), S5 Duck to (with OV R2) | C, F | F3 |
| UX-H1 | S7 key layer and "G then" jumps, S8 repeat and counts, in the XT registry | H | XT registry step |
| UX-A4 | S3 pop-up browser with search (with DS B3), S6 Inspector if picked | A, F, G | DS B3 |
| UX-E1 | S17 frame guard in Settings › Performance and the release gate | E, RG | none |
| UX-F1 | S16 motion tokens (LK adds them) applied to OV's menus and dialogs; S18 progress line | LK, F, C | OV steps |

Every task keeps to CLAUDE.md:
- each lane works only in its own area;
- new functions carry the lane's prefix;
- before a push, check that no top-level function is defined twice;
- no change to `desktop/app-version.json`.

## 6. What only the user can check

- **S9:** whether direct pinch feels better than the eased one on the Magic Trackpad. Try the mock-up with a real pinch: both views get the same input.
- **The real rAF rate in Electron on the G80SD**, through the frame-rate read-out.
- **S15:** whether the steady offset is felt on the Push 1 and on the computer keyboard while the mixer is open.
- **S13 and S14:** the mock-ups measure in the viewer's own browser, so opening the page on the Mac gives the Mac's numbers.

## The user's picks (27 November 2026, 22:02 Brussels)

`UX1 picks: S1 S2 S3 S4 S7 S9 S10 S11 S13 S14 S15 S16 S18`, and for S16: "make it even faster. Like 100 milliseconds, I think. Or maybe even 75 or 80."

- **S16 with the user's faster timings:** the four motion tokens become **0 / 50 / 80 / 120 ms** (instant; small things such as menus, tooltips and hovers 50 ms; panels, sheets and dialogs opening or closing **80 ms**; large moves such as a page turn or a view change 120 ms), one ease-out, every motion interruptible, reduced motion respected. They are LOOK tokens so they can be tuned later without code changes.
- Not picked: S5, S6, S8, S12, S17.

Who builds it: a new lane O, task **UV** (view engine: how and when the arrangement and the editors move and redraw, prefix `uv`): UV-1 = UX-A1 (S9 direct trackpad, S13 zoom without page layout), UV-2 = UX-A2 (S14 tiled arrangement with the glass engine reading tiles; the tiles cache what lane A draws, never change it), UV-3 S10 grab and fling, S11 coalesced and predicted points. Lane A (DS) builds S3, the pop-up browser with search, together with its browser step DS-B1. Lane C (FT) builds S1 time verbs and L for loop (with F2), S2 looping clips (with F1, F4), S4 automation across clips (with F3, F4), and its part of S18 (bounce and freeze in slices). Lane H (XT) builds S7, the single-key layer, K for the keyboard piano and "G then" jumps, in its commands registry. Lane J (LT) builds S15, steady timing for keys and MIDI (this also answers AE2's open L7), with lane E giving meters at half rate while a track is armed through a hook. Lane F (OV) builds S16 (the tokens above, applied to menus, dialogs, sheets and panels) and S18's progress line and the rule "an answer within 100 ms"; lane D runs analysis in its worker, lane K's export renders in slices.
