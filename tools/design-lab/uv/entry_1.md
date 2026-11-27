## 27 November 2026, v{V}: task UV-1, direct trackpad and zoom without page layout (lane O, picks S9 and S13; E19 folded in)

First step of the view engine (new lane O, prefix `uv`). Plan `docs/view-build.md`. Edit script `tools/design-lab/uv/uv_1.py` (anchored, asserted), test `tools/ui-tests/taskUV_1.py` (34 checks, all pass). The step was claimed in Where it stands before it started.

### Built
- **S9 direct trackpad.** A pinch (a wheel event with ctrlKey and no Control key down) and a trackpad scroll with a zoom key are applied in the frame they arrive in: `zsWheel` calls `zoomAround` at once instead of adding to `smoothZoom`. Only notched mouse wheels are still eased, now with tau **15 ms** (was 40; `szStep`); with reduced motion nothing is eased. Speed, Zoom around (pointer or playhead), Invert, the key per job and "Trackpad pinch zooms" are computed exactly as before. The piano roll and the overview take a pinch at once too. Plain two-finger scrolling was already direct and is unchanged; a Shift scroll is still eased.
- **S13 zoom without page layout.** While a zoom changes the track height, the track header keeps its layout: `drawArr` does not write `--th`, `--lh`, `--msh`, `--mh` or the size classes (one guarded block); every row is moved with a transform to where the new heights put it, clipped to its new height, each row its own layer (`#hdrin.uvz`). The clip pictures are drawn from their cached picture scaled to the new size (a wrapper around lane A's `drawClipC`; its code is not edited) instead of being drawn again at every step. 90 ms after the last step (and at least two frames later) the header is laid out once and every clip picture drawn again at the final zoom.
- **E19 calmer Follow page turns** (the user's long-sessions wish, added to the plan during this step): Follow "Page" turns at 90 % of the view (was 95 %) and moves the view by 80 %, so the last fifth of the old page stays in view; no turn while a pointer edit is held in the arrangement or the piano roll (the turn comes when it is let go). The other Follow ways are unchanged.
- Hook `UV_HOOKS.holding()` (true while a zoom holds the header). `tools/ui-tests/frametime.py` has a new `pinch` scene; `taskAN.py`'s "one wheel step is eased" now counts the eased steps inside `szStep` (with 15 ms the easing can finish within two frames of a slow test machine).

### Measured (cloud machine: 2 cores, SwiftShader, no graphics card; the Mac is several times faster, the comparison is what counts)
Frame times with `tools/ui-tests/frametime.py` (Fractals, 31 tracks, 364 clips, glass engine on; pinch = one ctrlKey wheel event per frame through the app's own listener), two windows each, ms per frame:

| User's size, 2194 x 1139 at 1.75x | main before | main after | app's own frame before | after | script before | after | style + layout before | after |
|---|---|---|---|---|---|---|---|---|
| scroll | 140.5 to 144.5 | 138.8 to 139.3 | 7.7 to 7.8 | 6.9 to 8.4 | 10.6 to 10.9 | 9.7 to 10.1 | 1.6 to 1.8 | 1.9 to 2.0 |
| pinch | 182 to 191 | **157 to 159** | 47.5 to 49.5 | **6.3 to 7.0** | 38.8 to 39.3 | **8.2 to 8.9** | 18.2 to 20.0 | **2.6 to 3.1** |

| 1280 x 800 at 1x | main before | main after | app before | after | style + layout before | after |
|---|---|---|---|---|---|---|
| scroll | 30.7 to 31.7 | 32.7 to 33.6 | 4.9 to 5.1 | 5.2 to 5.7 | 0.9 | 0.9 to 1.0 |
| pinch | 50.7 to 65.4 | **32.6 to 32.7** | 24.1 to 34.1 | **5.5 to 5.6** | 13.3 to 15.5 | **1.9 to 2.0** |

With real input (`tools/design-lab/ux1/measure_ux1.py`, events through the DevTools protocol), 1280 x 800: **a pinch frame 50.0 → 15.4 ms of main thread** (a scroll frame 12.1 ms; the research's 61 → about 12 target), layout in it 17.9 → 1.0 ms. At the user's size the main thread is mostly this machine's software drawing of the 3840 x 1748 px arrangement (scroll and pinch alike); the app's own share of a pinch frame fell to that of a scroll frame.

Latency from the event's time stamp (median of 12, real input): pinch, 90 % of the zoom on screen: **137 → 18 ms** (1280 x 800) and **441 → 33 ms** (user's size); first drawing 32 → 18 and 85 → 33 ms. A notched wheel: 90 % at 122 → 87 ms (1280 x 800) and 360 → 61 ms (user's size). Two-finger scroll unchanged (10 → 9 ms, 28 → 19 ms, within noise). Model for the Mac at 240 Hz: a pinch shows in the next frame instead of 90 % after about 96 ms; a notched wheel reaches 90 % after about 35 ms instead of 92 (the test steps `szStep` at 240 Hz: 25 ms against 83 ms from the first step).
Fling and "edit while scrolled" have nothing to measure yet (UV-3 and UV-2); their scenes come with those steps.

### Checked
- `taskUV_1.py` 34 of 34: a pinch changes the view inside its event by the same factor as before; nothing is left to ease; a notched Ctrl wheel is still eased and ends exactly where it was going; a two-finger scroll is 1:1 as before; reduced motion applies a wheel at once; **the end position of ten zoom cases is the old eased path's** (tau 40, every input eased) to 1e-9 in x, zoom and track height, V.y within the pixel it is rounded to at rest: pinch in and out, Speed 50 % and 200 %, around the playhead, over the map, Option (track height), Shift (clip width), Ctrl+Shift (sideways), Invert, the Ableton zoom style; pinch off ignores a pinch; the piano roll takes a pinch at once; during a pinch --th and the size classes are not written and every row sits on its track within 0.005 px; at rest --th is the new height, no transform is left, nothing is left running; style and layout per pinch frame 2.5 ms against 14.5 ms with the hold switched off; **at rest the arrangement canvas and the header column are pixel for pixel a fresh drawing** (every clip picture and the headers drawn again), dark and Light; Follow Page moves 80 % at 90 %, no turn while an edit is held; no console errors.
- Screenshots looked at in the middle of a pinch (zoomed out: rows clipped to their new height; zoomed in: rows at their new tops, laid out at the old height until rest).
- `taskST_S3.py` 62 of 62; `taskAN.py`: the eased-step check passes; its "Zoom and scroll group first in the Layout box" check and a later scroll-into-view also fail on v0.287 (old, from the settings rebuild).
- **The release gate on this build** (`gate.py --here --skip-ui --quick --ref 0.287`, never promotes; v0.287 was the newest release when it ran): lint clean; the start-up smoke test in the desktop app, 14 MIDI scenarios clean; idle frame times p50 16.7 ms and p95 50.0 ms, the same as v0.287; windows 19 checks; **Fractals levels unchanged**, measured by the gate's export step: Kick -19.05560 dB, Bass -35.48685 dB with the master at -10 dB (the reference numbers of the newest backlog entries, NI-7 and the gate), and the 9 repeatable export lines bit-identical to v0.287 (Drum kit, Plant, Sampler, Sampler grains are not repeatable from run to run on either build). The audio path is not touched by this step.

### What only the user's Mac can confirm, and what to try
- Pinch on the Magic Trackpad over the arrangement, the map, the piano roll: the view should stay under the fingers with no glide after them. The header rows move as one picture while the fingers move and settle into their final layout about 0.1 s after.
- The frame rate of a pinch at 240 Hz (the frame-rate read-out): the app's own part of a pinch frame is now that of a scroll; the rest is drawing the arrangement, which UV-2 takes on.
- A mouse wheel with a zoom key: if it glides briefly the mouse was recognised; if every notch jumps at once, say so (the wheel is then taken for a trackpad on that mouse).
- Follow › Page while playing zoomed in: the turn should feel calmer (the last fifth of the old page stays in view).

### Left
UV-2 (S14 tiled arrangement with the glass engine reading tiles, the version counter hook for lane A), then UV-3 (S10 fling, S11 coalesced and predicted points), then "view engine complete".
