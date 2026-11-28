## 28 November 2026, v{V}: task UV-2 (part a), tiled arrangement (lane O, pick S14)

Second step of the view engine. Plan `docs/view-build.md`. Edit script `tools/design-lab/uv/uv_2.py` (anchored, asserted; lane A's drawing code is not edited: `drawArr`, `arrSnap`, `snapTo` and `CLC.clear` are wrapped), test `tools/ui-tests/taskUV_2.py` (66 checks, all pass). The step was claimed in Where it stands before it started. Built while the release gate's freeze held `index.html`; released after it.

### Built
- **Scroll: only the new strip.** When only the view moved, the picture drawn last is moved by whole device pixels (from a copy kept after each frame that moved) and lane A's `drawArr` runs unchanged under a clip region, so it paints only: the strip that scrolled in, the bands outside the scrolling area (ruler and sections, the track header column, the bottom dock when the look paints over it), the master lane (it samples per screen column), clips that cross the left edge (their names, marks and note count follow the part in view), the overshoot of group lane bars that start left of the edge, empty tracks' hints, the track colour stripe, and while playing the automation lanes. About 30 % of the picture in Fractals at the user's size.
- **Edit: only the touched clips.** With the view still, a clip whose picture signature (lane A's `clipSig`), selection, hover or place changed is painted again in its old and new box, with its bar in every group lane it plays through: a mute, a move, a note changed in the piano roll, a selection, the hover. 2 to 5 % of the picture. A clip added or deleted is the same.
- **Everything else draws in full**, as before: the zoom and the track height (UV-1's pinch path), a setting, the theme or Light, the tracks, the loop, the sections, a drag with its ghosts (`ad`), a marquee, recording, the overview, Follow Centre and Stay, and any frame where nothing the tiles can see changed. 90 ms after the last tiled frame (`UV.rest`) the arrangement is drawn once in full, so **at rest every pixel is the untiled drawing**. While moving, the only possible difference is on anti-aliased edges (Skia rasterises curves a little differently under a clip of several rectangles: under 0.3 % of the pixels, a few levels).
- **When it is on** (`UVT.on = 'auto'`): edits are tiled everywhere (they copy nothing); scroll tiles only where a graphics card draws the canvas (`uvGpu`, the WebGL renderer name): on a software renderer copying the picture costs as much as drawing it (as task GS3 found), so there it stays off. `UVT.on = true / false` forces it.
- **Found in lane A's drawing (not changed):** `drawGroupLanes` draws a member clip that starts left of the track headers from the edge with the clip's whole length, so its bar runs past the clip's end by the part that is hidden; the half-covered last device column (2194 CSS px at 1.75 = 3839.5) blends with what was there before, so two drawings of the same view differ there. The tiles repaint both.
- Hooks: `UV_HOOKS.bump()` for lane A (a drawing change that the signature cannot see drops the kept picture; any of its releases that changes what a frame draws from the same state should call it, or add the input to `uvSig`); `UV_HOOKS.tiles()` = what the last frame painted (`{mode, dx, dy, rects}`), for the glass engine (part b).
- Tools: `frametime.py` has an `edit` scene (edit while scrolled) and `--pre`; `tools/ui-tests/uv_bench_electron.js` and the hand-started workflow `uv-bench.yml` measure before and after in Electron on the macOS runner.

### Measured
Cloud machine (2 cores, software rendering: SwiftShader in the harness, llvmpipe in Electron), `frametime.py` at the user's size (2194 x 1139 at 1.75, Fractals, glass engine on), two windows each, main thread ms per frame:

| Scene | before (UV-1) | after, standard setting | after, scroll tiles forced on |
|---|---|---|---|
| scroll (6 CSS px a frame) | 139.3 / 146.6 | 138.8 / 147.3 | 157.9 / 148.5 (app's frame 9 to 29: the copies) |
| pinch | 148.7 / 151.5 | 154.5 / 153.5 (unchanged: a zoom draws in full) | |
| edit while scrolled (a clip moved every frame) | 155.8 / 153.5 | **133.1 / 127.5** | 130.5 / 130.5 |
| one drawing during a scroll, with a 1 px read-back | 9.7 / 10.4 ms | the same (off here) | 18.3 / 20.7 ms |

Mac runner (macOS 26, Apple M1 virtual, Metal through ANGLE on a paravirtual device; Electron 45; window 1600 x 760 at 1x, the runner's screen), `uv-bench.yml`, same build with the tiles off and on:

| Scene | tiles off | tiles on (standard) |
|---|---|---|
| one drawing during a scroll | 14.0 ms (earlier run 18.0) | 12.0 ms (earlier run 12.6) |
| scroll | 128 fps, main 7.5 ms/f | 132 fps, main 7.3 ms/f |
| edit with the view still | 128 fps, main 7.5 ms/f | 129 fps, main 7.6 ms/f |

On the runner's small window the arrangement drawing is a small part of a frame, and the numbers move by about as much from run to run as between off and on; the one-drawing bench is the clearest (14 to 18 ms down to 12). On the user's 3840 x 1993 device pixels the strips are a smaller share of a larger picture.

### Checked
- `taskUV_2.py` 66 of 66, dark and Light: one sideways step of 7 device px is tiled, paints under 40 % and is the fresh drawing (anti-aliased edges aside); 40 steps in a row, 20 up and down (whole CSS px), 20 diagonal; a trackpad scroll of 10.5 device px a frame is tiled and **at rest pixel for pixel the fresh drawing**; mute, move by a beat, a note changed, a selection, the hover each paint only their boxes (under 8 to 15 %) and at rest are pixel for pixel; an edit and a scroll in the same frame; a setting, a zoom, the track height, the loop and `UV_HOOKS.bump()` draw in full; with the standard setting on this machine a scroll draws in full and an edit is tiled; idle: nothing drawn, no timer; no console errors.
- `taskUV_1.py` 34 of 34 on the build with both steps; lint clean.

### What only the user's Mac can confirm, and what to try
- Scroll the arrangement with two fingers, zoomed in, with the frame-rate read-out on (Settings > Performance): it should hold the screen rate at least as well as before. Nothing should lag behind or smear at the edges while scrolling; a clip's name at the left edge stays readable.
- Edit while scrolled (mute clips, change notes in the piano roll with the arrangement visible): the arrangement should answer at once.
- If anything is ever left behind while scrolling (a stray line, a label in the wrong place), it disappears 0.1 s after the scroll stops; please say where it was.

### Left
UV-2b: the glass engine reads the tiles (moves its small copy of the arrangement and reduces only the painted strips instead of the whole picture, `UV_HOOKS.tiles()`). Then UV-3 (S10 grab and fling, S11 coalesced and predicted points), then "view engine complete".
