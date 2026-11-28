## 28 November 2026, v{V}: task NI-10a, draw the arc, part 1 (lane D, idea I7)

Edit script `tools/feature-lab/ni/ni_10a.py` with `ni_10a_block.js` (anchored; needs NI-7b in the file), test `tools/ui-tests/taskNI_10a.py` (24 checks, all pass). Built on v0.314 + NI-31 + NI-7b on 28 Nov from 17:40 UTC while the release gate's freeze of 17:28 held `index.html`; released together with NI-31 and NI-7b.

### Built
- **Draw the energy you want** in NI-6's energy lane (the curve under the sections): right-click the lane, Draw your line…, or the command `ni.drawArc` (it turns the lane on). Drag across the lane to draw; Alt-drag erases; Esc or a right-click ends. Each stroke is one undo step. The line is on the lane's own scale (0 to 1, the same as the energy curve), drawn in green.
- **Saved with the song** as `S.ni_arc = {v: 1, line: [one value per beat, or null]}`. A song without it has no line and nothing marked.
- **The shortfall**: wherever the measured energy sits 0.06 or more under the line for at least a bar (gaps of up to 2 beats joined; the edges trimmed where the gap is under half the stretch's middle gap, because NI-6 smooths over 4 beats), the band between the line and the energy is shaded red with its size, "−22 dB". The lane's menu lists the stretches ("Bars 9 to 12 sit about 22 dB under your line", click to go there) and Clear your line; a toast says the same after each stroke.
- **What the dB means**: the loudness change that would close the gap if only loudness moved (energy is 55 % loudness on a 30 dB scale, plus tracks playing and brightness). It is a guide to size, not a gain to apply: more tracks or a brighter sound close the gap too, and NI-10b will suggest such moves.
- Nothing new is measured (NI-6's numbers); the line and the shortfall are drawn inside the arrangement's normal redraw, nothing per frame while idle. `NI_arcDraw` (NI-6, lane D) is wrapped; one anchor added to NI-6's lane menu.
- `NI_HOOKS.arcLine` (`line()`, `short()` the stretches with bars, gap and dB, `set(b0, b1, v0, v1)`, `mode(on)`) for NI-10b and NI-11 Ask the mix.

### Checked
- `taskNI_10a.py` 24 of 24, on NI-6's test song (a quiet break in bars 9 to 12): a song without the key loads with no line; a mouse stroke in draw mode is one undo step, follows the pointer (0.3 to 0.8 within 0.03) and does not move the playhead; Undo removes it; a flat line at the drops' energy over beats 16 to 64 marks exactly bars 9 to 12 with 22 dB, the measured gap within 1 dB; the menu lists it and moves the playhead there; the toast; the break is shaded red, nothing above the drop; idle 2 s draws nothing; Alt-drag erases (one undo step); the line survives a save and reopen; a line under the song marks nothing; Clear and its undo; Esc ends drawing; a render is the same with and without the line; no em dashes; no console errors.
- `taskNI_6.py` (the energy arc) passes with NI-10a in the file; lint clean.
- Renders of that test song differ by up to 3e-8 (the last bit) between runs, with or without a line; the test allows 1e-6. Not caused by this step (it renders nothing); noted for lane K.
- Screenshots looked at: the lane with a line over the drops and the red break.

### Limits and what only the user can judge
- **Try it**: turn on the energy arc (right-click the section row), right-click the lane, Draw your line…, and draw the shape you want for the song. The red parts are where the song falls short. Whether 0.06 is the right "clearly under" and whether the dB reads well is for you to judge.
- Parts above the line are not marked (only shortfalls, as planned). The lane is 40 px high, so drawing is coarse; zoom in for detail.

### Left
NI-10b (the moves toward the line), NI-11a and b (I31 Ask the mix), NI-12 and on; NI-20b and NI-25a/b stay gated on lane C. Also: the NI-3 whole-song memory problem.
