"""Task DV-4 release docs: python3 tools/edits/taskDV4_docs.py <version> "<releases since DV-3>" (run from the repo root after the edit script, and after
taskDV3_docs.py has written DV-3's release). Writes section 10 of docs/devices-display-first.md, the Where it stands line, the backlog-log entry and the
update-notes line. Check the frame-time and Fractals numbers in the log text against the release run before pushing."""
import sys
V = sys.argv[1]; PREV = sys.argv[2]
def rd(p): return open(p, encoding='utf-8').read()
def wr(p, s): open(p, 'w', encoding='utf-8').write(s)
def rep(s, a, b):
    assert s.count(a) == 1, (a[:60], s.count(a)); return s.replace(a, b)

p = 'docs/devices-display-first.md'; s = rd(p)
s = rep(s, '| DV-4 | **The closed picks**', '| **DV-4** (v%s, done) | **The closed picks**' % V)
s = s.rstrip('\n') + '''

### How DV-4 is built (v%s)

- Block "(task DV-4)" before `askChoice` (after DV-3's), CSS before `.dacv`, made by `tools/edits/taskDV4.py` from `taskDV4_block.js` and `taskDV4_css.txt` (one asserted change inside DV-1's `dvVals`: it leaves out what the picture writes). Test `tools/ui-tests/taskDV_4.py` (71 checks; a third argument, the previous build, adds the old-project check). `taskDV_1.py` now turns Attack instead of Ratio (the Compressor's picture writes Ratio itself, so the values line leaves it out).
- **Handles** (`dvHandles`): the places of a picture's own handles, from `HND` (lane A's grab handles) or, for the Echo delay, from its drawing's geometry (`dGeo`: the first echo, the second, the two cuts), in the device body's pixels, with the rectangles of the picture's own words (`DVTXT[type].clear`).
- **One placing routine** (`dvScore`, `dvBest`, `dvNear`): a place outside the body costs 100, over a handle 10, over another placed control 20, over the picture's words 2; the first free place wins, else the cheapest. Later steps only add a device's `DVTXT` (words to keep clear and to leave out of the values line) and `DVANC` (which handle each control belongs to), and its type to `DVDOCK`.
- **Hover reveal as a bottom dock** (`DVDOCK`: comp, side, delay, reverb): the device's own `.dfs` laid out as one row (each knob with its label over its value, faders as a short bar with label and value, the Sidechain's Rate menu first), the gain after a hairline, centred; the preset row (`.dspr`) moved out as a pill (`.dvdpre`, an engine face) at the top. The dock takes the lowest place that covers no handle (at the bottom, just above or just under a handle, under the top row), else the one that covers the fewest; the pill the first place clear of the handles. DV-1's rail panel (`dvRail`, the union of `.dfs` and `.dug`) is the dock's one glass panel. The device gets wider only when the row needs it.
- **Values line**: leaves out what the picture writes (Compressor: Threshold and Ratio; Echo delay: Time, Feedback, Mix; Reverb: Decay, Pre-delay) and is placed by the same routine (bottom, then under the picture's top line, left or right).
- **On the picture** (`DVPIC.comp/side/delay/reverb = dvpAnchored`): each control with a handle (`DVANC`) is a chip beside it (right, left, above, below, then a step further out); the preset, the Rate menu, controls without a handle and Gain go to the More drawer (sections Preset, Rhythm, Other controls, Output); More takes the first clear place at the top (left of the eye pill, the middle, the left) or the bottom.
- **Following**: the dock, the values line and the chips are placed again on `pointermove` with a button down, `pointerup`, `wheel`, `input` and `change` inside a closed device of these types (one frame at most; on the window, because the pictures' handle drag stops the event at the panel); a chip being dragged stays where it is until it is let go. Nothing runs at rest.
- A short fader (in the dock, on a chip or in the drawer) is dragged over 150 px for its whole range (`cd.h`), like a knob, not over its own 30 px.
''' % V
wr(p, s)

p = 'docs/device-backlog-2026-11-25.md'; s = rd(p)
a = s.index('**Step DV-3 done**'); b = s.index('**Steps DV-1 and DV-2 done**')
s = s[:a] + s[a:b].replace('**Step DV-3 done**', '**Steps DV-3 and DV-4 done**', 1).rstrip() + ' DV-4, v%s: the Compressor, Sidechain, Echo delay and Space reverb closed: a clean picture with a values line clear of their handles, hover shows a bottom glass dock (the controls in one row, label over value, Gain, the preset as a pill on top), placed so every handle stays draggable; On the picture puts each control as a chip beside its handle, the preset and Gain in More. ' % V + s[b:]
s = s.replace('Steps DV-2 to DV-12 in section 10 of that doc; next DV-3 (On the picture and Pro EQ).', 'Steps DV-5 to DV-12 in section 10 of that doc; next DV-5 (the synths).')
wr(p, s)

p = 'docs/backlog-log.md'; s = rd(p)
s = s.rstrip('\n') + '''

## 28 November 2026, v%s: task DV-4, display-first devices, step 4: the bottom dock, the values line, On the picture for the Compressor, Sidechain, Echo delay and Space reverb (lane I)
Step DV-4 of `docs/devices-display-first.md` section 10. Built on 28 Nov while the release gate's freeze held DV-3; released after %s: `index.html` taken fresh from main and the edit script run again. Edit script `tools/edits/taskDV4.py` with `taskDV4_block.js` and `taskDV4_css.txt` (asserted anchors before `askChoice` and `.dacv`, one asserted change inside lane I's own `dvVals`); test `tools/ui-tests/taskDV_4.py` (71 checks). New names start with `dv`/`DV`.

### Built
- **Hover reveal is a bottom dock** on the four devices (the user's DD4 with DD1's dock): at rest a clean picture with a values line; under the mouse (or Tab into it, or a tap) the controls rise in one glass row, each knob with its label over its value, Gain after a hairline, and the preset arrows, menu and Change as a pill at the top. The dock sits as low as it can without covering any of the picture's handles, so a dot or the Echo delay's cut bar can still be dragged while it shows.
- **The values line** leaves out what the picture already writes in words (the Compressor's Threshold and Ratio, the Echo delay's Time, Feedback and Mix, the Reverb's Decay and Pre-delay) and is placed clear of every handle and of the picture's words (on the Compressor, Echo delay and Reverb under the picture's top line, on the Sidechain at the bottom right, clear of its hint).
- **On the picture** for the four: Threshold and Ratio on the curve, Makeup at the output, Attack and Release at their dots; Time and Mix at the first echo, Feedback at the second, the cuts at the filter band; Pre-delay, Decay, Damp, Mix and Low cut at their dots; Depth and Shape at the pump's dot, Punch at its own. The preset, the Sidechain's Rate and Gain are in More. The chips follow a dragged handle.
- One placing routine for all of it, from the handles each picture already has, so the groups DV-5 to DV-11 only add a device's anchors and words.
- A short fader in the dock or on a chip moves over 150 px for its range, like a knob.

### Tested
- `taskDV_4.py` 71 of 71 (with the old-project check): on each device, at rest the dock hidden and the values line clear of every handle and word and without the picture's own values; on hover one row, label over value, inside the device, over no handle, one glass panel, the preset pill clear of the handles; Tab and a tap reveal it; a knob and a fader in the dock; the Echo delay's low cut and the Compressor's attack dot dragged with the dock shown; On the picture one chip per handle control, each beside its handle, none over another, a handle or More; the Threshold chip follows its dot; More holds the preset and Gain, both work; the eye menu offers On the picture as ready; tooltips on every control (the Sidechain's Rate menu got one); rail open and closed again; engine faces; nothing read, refreshed, uploaded or placed at rest in either mode; Solid; switching states never changes a value; kOpen/kMode saved; an old project opens the same.
- `taskDV_1.py` 37 of 37, `taskDV_2.py` 21 of 21, `taskDV_3.py` 35 of 35.
- Screenshots, looked at: the four devices with the rail open, the dock revealed and On the picture at Glass, Light and Solid, and at rest.

### Left
- DV-5 to DV-11: the other devices get their `DVDOCK` entry, `DVTXT` and `DVANC` (their dock and chips) group by group; DV-12 the check of every device.
- When every place covers a handle (the Compressor with a high Makeup has handles from top to bottom), the dock covers the fewest it can; that handle is reachable with the dock hidden (move the mouse off and on) or from the dock's own fader.
- Lane K's sidechain source for the Compressor (task MX-3), when released, joins the dock's row like the Sidechain's Rate menu; to be checked then.
''' % (V, PREV)
wr(p, s)

p = 'desktop/update-notes.txt'; s = rd(p)
s = s.rstrip('\n') + '\nDevices, step 4: Compressor, Sidechain, Echo delay and Space reverb show a clean picture; point at one and its controls rise in one glass row at the bottom, placed so the dots stay draggable. Right-click the eye for On the picture: each control sits beside its dot.\n'
wr(p, s)
print('docs written for', V)
