# View engine build (task UV, lane O): plan and status

Lane O owns **how and when the arrangement and the editors move and redraw**: zoom and scroll input (`zsWheel`, `szStep`, `zoomAround`, `smoothZoom`, `smoothPan`, `clampV`'s rounding), Follow's page turns, the header layout during a pinch, the tile cache, fling, and coalesced and predicted pointer points. **What is drawn** (grid, clips, waveforms, piano roll drawing, the header rows themselves) stays lane A's (task DS). Prefix `uv`, hooks `UV_HOOKS.<name>`. Edit scripts in `tools/design-lab/uv/`, tests `tools/ui-tests/taskUV_<n>.py`.

Source: the user's UX1 picks (27 Nov 2026, 22:02 Brussels), `docs/research-ux-speed.md`: S9, S13 (UV-1), S14 (UV-2), S10, S11 (UV-3); and from the long-sessions wishes (UX2, `docs/research-ux-long-sessions.md`) E19, calmer Follow page turns (folded into UV-1, see the note at the end). Motion timings for anything animated come from lane F's S16 LOOK tokens (0 / 50 / 80 / 120 ms).

## Steps

| Step | Picks | Contents | Status |
|---|---|---|---|
| UV-1 | S9, S13, E19 | Direct trackpad: a pinch and a trackpad scroll with a zoom key applied in the frame they arrive in; only notched mouse wheels eased, tau 15 ms (was 40); Speed and Anchor kept. Zoom without page layout: the header keeps its layout during a zoom, rows moved by transforms (each row its own layer), clip pictures scaled from their cache; laid out and drawn once at rest. Calmer Follow page turns. Frame test pinch against scroll. | built and tested, held by the release freeze |
| UV-2 | S14 | (a) Tiled arrangement, (b) the glass engine reads the tiles. Tiled arrangement: the arrangement picture kept in tiles (track rows by a fixed time span); scrolling draws only the new strip, an edit only the touched tiles; the glass engine reads the tiles (see `docs/glass-engine-plan.md` §3.11, the GS3 strip-shift experiment). The tiles cache what lane A's drawers draw and never change it: a version counter (`UV_HOOKS.bump()` for lane A, plus a signature of the drawing inputs) drops old tiles on any drawing change. Pixel test at rest against the untiled drawing; frame tables for scroll, pinch and an edit while scrolled. | claimed 28 Nov 09:20 UTC |
| UV-3 | S10, S11 | Grab and fling with the middle button and on the overview (0.998 per ms glide, rubber band at the ends, stopped by any touch, none with reduced motion); coalesced points (`getCoalescedEvents`) for freehand drawing (automation pencil, piano roll paint); a predicted point (`getPredictedEvents`) for drag ghosts only (never for the committed result). After UV-3: "view engine complete". | |

## UV-1: what changed in the code

- `zsWheel` (keys and pinch over the arrangement and the map): `ez = !pinch && uvEase(e)`. A pinch, or a trackpad scroll with a zoom key, calls the apply function at once (`f(Math.exp(amt))`); a notched wheel goes through `smoothZoom` / `smoothPan` as before. The amount (Speed, Invert), the anchor (pointer or playhead) and the job of each key are computed exactly as before.
- `uvNotch(e)`: lines (deltaMode 1), the 40 px steps `mouseLike` already knew, or a whole multiple of 120 in `wheelDelta` on one axis. `uvEase(e)` = notched and motion allowed. With reduced motion nothing is eased (`uvTau()` = 0).
- `szStep` eases with `uvTau()` (15 ms) instead of 40. This also makes the zoom buttons of the grid and the instrument browser glide faster.
- Plain two-finger scrolling was already direct and is unchanged; a Shift scroll is still eased (Shift + mouse wheel cannot be told apart from Shift + trackpad with every Mac mouse).
- Piano roll and overview: a pinch (and Option over the piano roll) is applied at once through `uvZoomBy`.
- Header hold (S13): the first zoom step that can change the track height calls `uvHold()`: it notes the header's current height, lane height and row tops, and puts the class `uvz` on `#hdrin` (each row `will-change: transform`). While it holds, `drawArr` does not write `--th`, `--lh`, `--msh`, `--mh` or the size classes (one guarded block, `if(!(UV&&UV.hold&&uvHdrPose()))`); `uvHdrPose()` gives each row `translate3d(0,dy)` to where the new heights put it and a `clip-path` when the rows got lower. 90 ms after the last step, and at least two frames later, `uvRest()` removes the transforms and the class; the next `drawArr` writes the variables once. If the header is rebuilt during a hold (`renderHeaders`), the hold lets go at once.
- `clampV` keeps V.y's sub-pixel value during the hold (as it already did during an eased zoom) and rounds it at rest.
- Clip pictures during the hold: `drawClipC` is wrapped (lane A's function is not edited): during the hold a clip whose cached picture exists is drawn from that picture scaled to its new size; outside the hold the original runs and the wrapper notes the size its picture was made at. At rest lane A's code draws every picture again at the final zoom.
- E19: Follow "Page" turns when the playhead reaches 90 % of the view (was 95 %) and moves the view by 80 %, so the last fifth of the old page stays in view and the playhead lands at 10 % (`uvPageTurn`); a playhead outside the view still lands at 5 %. No turn while a pointer edit is held in the arrangement or the piano roll (`uvEditing`); the turn comes when it is let go. The other Follow ways are unchanged.
- Hook: `UV_HOOKS.holding()` is true while a zoom holds the header (for other lanes' header code that wants to skip work during a pinch).

## UV-2 part a: what changed in the code

- `drawArr` is wrapped (lane A's code is not edited). `uvPrep` runs before it: it lays out what drawArr lays out (X0, AY, the rows), takes a signature of everything that decides the whole picture (`uvSig`: sizes, zoom, rows, tracks, loop, selection range, sections, settings and look, drags, recording, `UV.ver`) and of every clip that can be on screen (`uvClips`: lane A's `clipSig`, selected, hovered, place). Same signature and the view moved: **shift** (the kept copy `UVT.bb` is drawn moved by whole device pixels, a clip region holds the new strip and the bands that do not scroll, `uvR` rectangles). Same signature, view still, clips changed: **edit** (their old and new boxes and their group lane bars). Anything else: **full**.
- The kept picture's own view (`UVT.base.vx/vy`) moves by whole pixels, so rounding never accumulates; the strips are drawn at the true view, under half a device pixel apart while moving.
- `arrSnap` is wrapped to lift the clip region before lane A's snapshot; `snapTo` of the canvas by anyone else and `CLC.clear` (clip pictures thrown away) drop the kept picture.
- 90 ms (`UV.rest`) after the last tiled frame one full drawing: at rest pixel for pixel the untiled drawing.
- On: `UVT.on='auto'`: edits everywhere, scroll tiles only with a graphics card (`uvGpu`); `true`/`false` force.
- Hooks: `UV_HOOKS.bump()` (lane A), `UV_HOOKS.tiles()` (glass engine, part b).

## UV-2 part b (next)

The glass engine (`upload()` in the engine) reduces the whole arrangement canvas to its first pyramid level every time the arrangement changed. With `UV_HOOKS.tiles()` it can move its small copy by dx/dy and reduce only the painted rectangles.

## Measurements

Set-up: `tools/ui-tests/frametime.py` (Fractals, 31 tracks and 364 clips, glass engine on, SwiftShader on a 2-core cloud machine, no graphics card) with the new `pinch` scene (one ctrlKey wheel event per frame through the app's own listener); latency with `tools/design-lab/ux1/measure_ux1.py` (real input through the DevTools protocol). Absolute numbers are this machine's; the Mac's are several times faster. Tables in the UV-1 entry of `docs/backlog-log.md`.

## What only the user's Mac can confirm

- Whether the direct pinch feels right on the Magic Trackpad (no extra easing on top of macOS's own).
- The pinch frame at 240 Hz on the M4: here the app's own work per pinch frame fell to that of a scroll frame; on the Mac the remaining cost is mostly drawing the arrangement, which UV-2's tiles take on.
- Whether a notched mouse wheel with a zoom key is recognised as a wheel on the user's mouse (then it glides for about 35 ms) or taken for a trackpad (then each notch jumps at once).

## Added from the long-sessions wishes (UX2, 27 Nov 2026, 22:23 Brussels)

**E19 calmer Follow page turns, as the standard behaviour (no setting):** turn at 90 % of the view, keep the last fifth of the old page in view, no page turns while editing. See `docs/research-ux-long-sessions.md` (the user's wishes at its end). Fold it into your next step. **Done in UV-1** (the step was in progress when this was added).
