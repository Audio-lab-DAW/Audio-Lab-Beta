"""Task DV-3 release docs: python3 tools/edits/taskDV3_docs.py <version> "<releases since the claim>" (run from the repo root after the edit script).
Writes section 10 of docs/devices-display-first.md, the Where it stands line, the backlog-log entry and the update-notes line. Check the frame-time
and Fractals numbers in the log text against the release run before pushing."""
import sys
V = sys.argv[1]; PREV = sys.argv[2]  # version, list of releases since the claim
def rd(p): return open(p, encoding='utf-8').read()
def wr(p, s): open(p, 'w', encoding='utf-8').write(s)
def rep(s, a, b):
    assert s.count(a) == 1, (a[:60], s.count(a)); return s.replace(a, b)

p = 'docs/devices-display-first.md'; s = rd(p)
s = rep(s, '| DV-3 | **On the picture**', '| **DV-3** (v%s, done) | **On the picture**' % V)
s = s.rstrip('\n') + '''

### How DV-3 is built (v%s)

- Block "(task DV-3)" before `askChoice` (after DV-2's), CSS before `.dacv`, made by `tools/edits/taskDV3.py` from `taskDV3_block.js` and `taskDV3_css.txt`. Test `tools/ui-tests/taskDV_3.py` (37 checks; a third argument, the previous build, adds the old-project check).
- **The mechanism**: `DVPIC[type] = {lay(D, own, B)}`. When the rail is closed and the instance's `kMode` is `picture`, `dvFrame` (wrapped) adds `.dvpic` and calls `lay`, which moves the device's own controls (the same elements, so parameters, presets, automation and undo work as on the rail) to their places as chips (`.dvface`) and returns the sections of the More drawer (`dvPicMore`: a "More" button, `aria-expanded`, kept open per instance over renders in `DV3.more`, Escape closes it and gives the focus back). The rail, the hover panel and the values line are hidden. Devices without an entry keep hover reveal.
- **Chips as engine faces**: DV-1's `dvgSync` now takes `.dvface` elements too (kind `pill`, their own radius); at Solid or without WebGL2 they are a near-solid tint. A press on a chip's empty part does not pan the devices panel; a tap on a chip does not toggle hover reveal.
- **Pro EQ** (`dvpEq`, the user's DD3): the band editor (`.eqb`) is a capsule under the selected dot, at the place the EQ's own hit test computes (`fX`, the gain scale, dynamic gain), above the dot when there is no room, at the middle of several selected dots (Off, On, Gain 0, Delete), and follows the dot while it is dragged or scrolled (`dvCapPos`, one frame at most per input); with no band selected a hint ("Click a dot to edit its band, double-click the graph to add one", the full help as its tooltip) sits low on the graph. Gain is a slim fader (30 px) at the right edge, always shown. The preset arrows, Change and More float at the top left, clear of the dB scale; the drawer holds Bands (the chips with their on/off ticks and +), Analyser (Off, Post, Pre+Post, Auto) and Whole EQ (Scale, Out). A closed Pro EQ's pill (pin on top, eye under it) stands in the column right of the graph, so it no longer covers lane E's "analyzer, tilt" label or the selected band's label (DV-1's open point).
- **Cost** (DV-1's engine, three small changes): pictures under glass are no longer refreshed at rest (only while playing, for two seconds after a change and once after the song stops); a picture under chips only is refreshed while it is being edited, not while it plays (a live analyser under small chips costs nothing); only the frame's own fades keep the page being read (the meters' transitions inside devices, about 50 a second while playing, kept every rail being re-read before). Measured while playing with a Pro EQ on the picture: the devices engine took 40 ms in 4 s against 48 ms on the build before (where the closed Pro EQ had no glass at all).
''' % V
wr(p, s)

p = 'docs/device-backlog-2026-11-25.md'; s = rd(p)
a = s.index('**step DV-3 claimed**'); b = s.index('**Steps DV-1 and DV-2 done**')
s = s[:a] + '**Step DV-3 done**, v%s: On the picture works (`DVPIC`: the device\'s own controls as chips on the picture, glass faces of the devices engine, a More drawer for the rest), first on the Pro EQ (the band editor as a capsule under the selected dot, a hint with no band selected, Gain as a slim fader at the right edge, presets and More at the top left; the eye and pin beside the graph, clear of its labels); pictures under glass cost nothing at rest or under chips while playing. ' % V + s[b:]
wr(p, s)

p = 'docs/backlog-log.md'; s = rd(p)
s = s.rstrip('\n') + '''

## 27 November 2026, v%s: task DV-3, display-first devices, step 3: On the picture and the Pro EQ (lane I)
Step DV-3 of `docs/devices-display-first.md` section 10 (claimed at 21:36 UTC). Released after %s, and after waiting for the release gate's freeze (`desktop/release-freeze.json`) to end: `index.html` taken fresh from main and the edit script run again. Edit script `tools/edits/taskDV3.py` with `taskDV3_block.js` and `taskDV3_css.txt` (asserted anchors before `askChoice` and `.dacv`, and six small asserted changes inside lane I's own DV-1 block); test `tools/ui-tests/taskDV_3.py` (37 checks). New names start with `dv`/`DV`.

### Built
- **On the picture** (the user's DD3, chosen per device instance from the eye's right-click menu): `DVPIC` gives a device type the places of its controls; with the rail closed and the mode On the picture, the device's own controls (so parameters, presets, automation and undo are untouched) float as small glass chips over the picture, and what has no place goes to a **More** drawer (kept open over renders, Escape closes it). The rail open hides the chips; closing brings them back. Devices without positions keep hover reveal and the menu says so; the Pro EQ is the first with positions, the others follow in DV-4 to DV-11.
- **Pro EQ**: the band editor is a capsule under the selected dot (above it when the dot is low; at the middle of several selected bands with Off, On, Gain 0, Delete) and follows the dot while it is dragged; with no band selected a hint sits on the graph; Gain is a slim fader at the right edge; the preset arrows, Change and More at the top left; the drawer holds the band chips, the analyser, Auto, Scale and Out. The eye and the pin stand in the column right of the graph when closed, so they no longer cover the graph's labels.
- **Chips are glass faces** of the devices engine over the display's flat picture (DV-1's engine takes `.dvface`); at Solid a near-solid tint.
- **Cost**: pictures under glass are not refreshed at rest any more; a live display under chips only is not re-uploaded while it plays; the meters' transitions inside devices no longer keep the page being read (they did about 50 times a second while playing, for every device with a rail).

### Tested
- `taskDV_3.py` 37 of 37 (with the old-project check against main): no rail, hover panel or values line on the picture; the menu offers On the picture as ready; the hint and its tooltip; the capsule under dot 3, above a dot dragged low, following it while dragging, inside the picture and clear of the gain; type buttons and Solo from the capsule; Tab through it; two bands share one capsule at their middle; the slim Gain visible at rest with its tooltip; the next-preset arrow; More with Bands, Analyser, Whole EQ, the analyser switch from the drawer, kept over a render, Escape gives the focus back; tooltips on every control on the picture; rail open and closed again; Hover reveal still works on the Pro EQ; the chips are engine faces over the graph; nothing read, refreshed or uploaded at rest; Solid; kOpen and kMode saved; switching states never changes the EQ's values; a Pro EQ the user adds shows On the picture; an old project opens with the same values, rails and modes.
- `taskDV_1.py` 39 of 39 (its at-rest check sets the Pro EQ to hover reveal: On the picture is now real on it), `taskDV_2.py` 21 of 21, `sideheaders.py` 0 failures (a closed device On the picture keeps its preset row visible), lint clean.
- Screenshots, looked at: the Pro EQ with the rail open, closed On the picture (no band, a band, a low band, the drawer open) and closed with hover reveal revealed and at rest, at Glass, Light and Solid.
- Frame time with the devices panel open (headless, 240 frames, two Pro EQs, one On the picture with a band selected, and a Compressor), two runs each: at rest 16.7 to 17.2 ms on both builds; playing 20.3 ms mean (p95 33.4) against 20.5 ms (p95 33.4) before.
- **Fractals levels unchanged** (`export_same.py`): Kick -19.05560 dB (fb577dd5202b), Bass -35.48685 dB (392ec52590c7) at master -10 dB; -9.75669 and -25.48699 dB at 0 dB; Saw, Pad, Acid, Wavetable, Venom the same hashes (Plant, Sampler, Sampler grains, Drum kit vary between any two runs).

### Left
- DV-4: Compressor, Sidechain, Echo delay, Space reverb (bottom dock for hover reveal, values line clear of the handles, positions On the picture: Threshold and Ratio on the curve, Attack and Release on their dots, Makeup at the output). Then the groups DV-5 to DV-11 and the check DV-12.
- The values line on the drum designers lies over the picture's time scale labels (300 ms); placed per device later.
- With the rail closed in Hover reveal, the Pro EQ shows no values line when no band is selected (nothing to show); unchanged.
''' % (V, PREV)
wr(p, s)

p = 'desktop/update-notes.txt'; s = rd(p)
s = s.rstrip('\n') + '\nDevices, step 3: a closed Pro EQ now shows its controls on the graph: click a dot and the band editor appears right under it, Gain is a slim fader at the right edge, and More (top left) holds the band list, the analyser, Scale and Out. Right-click the eye to switch between this and Hover reveal.\n'
wr(p, s)
print('docs written for', V)
