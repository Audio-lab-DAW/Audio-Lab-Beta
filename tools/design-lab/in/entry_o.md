## 27 November 2026, v@VER@: task IN-O, stereo field and phase: marks, afterglow, polar view (lane E, instruments)

Step IN-O of `docs/design-round-4-instruments.md`, the user's picks **O0** (today's stereo and scope drawing kept), **O1** (marks and afterglow) and **O4** (polar view as an extra menu choice). Edit script `tools/design-lab/in/in_o.py` with `in_o_block.js` (every anchor asserted unique), test `tools/ui-tests/taskIN_O.py` (25 checks, all pass), cost `tools/design-lab/in/stereo_cost_o.py`. Written on v0.276.

### Built (block "lane E (task IN-O)" before `askChoice`, one CSS line before `.dacv`)
- **O0 kept:** the mixer's stereo field box (every strip and the master): diamond grid, L R M, dots in the strip's colour scheme on today's mapping, its menu (colours, size, grid, fading trails, phase, balance and width read-outs). The Visualizer's scope is untouched (O3 was not picked).
- **O1 marks (`inoMarks`):** amber ticks at 0, −6, −12 and −18 dB where such a sample lands on the display's own mapping: a mono sample on the M axis, a one-sided sample on the L and R diagonals (on today's scale a mono sample reaches the box edge at −3 dBFS, so 0 dB mono is outside; the −6 and −12 marks are labelled), +S and −S at the sides. Drawn once per box size into an image, then copied.
- **O1 afterglow (`inoLayer`):** a small layer per display that fades by time (to 18 % in 1/6 s, the pick page's 0.82 per 60th), so the shape reads instead of flickering dots; none at the Light level (dots straight on the display, as today). The newest sample is an amber dot. The dots are drawn in six level steps of the strip's colour scheme (`inoCols`, today's `mxC` at each step's middle), one fill colour per step.
- **O1 phase bar (`inoCorr`):** the strip's PHASE bar gets ticks every 0.1 (heavier at −1, −0.5, 0, +0.5, +1), the negative half hatched, the value with a real minus and the phase angle (arccos of the correlation): "+1.00 0°", "−1.00 180°", "0.00 90°". The balance bar gets ticks at L, the quarters, C and R (`inoBalTicks`).
- **Master box:** the Stereo value with a real minus and the phase angle (`inoMaster`), the bar's negative half hatched (CSS).
- **Overlay:** the analyser overlay's stereo module (it already fades) gets the same marks on its own scale.
- **O4 polar view:** right-click the stereo field: under **Picture**, Stereo field (checked) or **Polar view** (kept with the other mixer options, `mxOpt('stereo','pol')`). iZotope's polar sample: the angle is the stereo position (up = mono, 45° = only left or only right), the distance the level (rings every 12 dB from −48 to 0), beyond 45° is out of phase on a hatched red ground; MONO, L, R; "in phase" and the share of samples within 45° in percent (red under 90 %). The phase, balance and width read-outs below stay.
- **Not changed:** the track taps (`N.aL`, `N.aR`) stay at 256 samples. Reading 512 in the stereo view doubled the dots and the other readers' work: drawMixer 6.7 to 8.7 ms median with every strip in the stereo view (about 20 on screen), so it was taken out; the afterglow builds the shape over the frames instead. No audio code; the correlation, balance and width sums are today's.
- **Overlaps named:** lane K (MX, X19's bass mono switch) and IN-X19 (low-band correlation on the meters) will add to the correlation read-outs: `inoCorr` is the one bar drawer. Lane I (DV) frames device displays, not the mixer.

### Tested (`tools/ui-tests/taskIN_O.py`, at 2194x1139)
- Known samples drawn into a test canvas: a mono sine at −6 dBFS reaches the −6 mark on the M axis (top 19.5 against 19.6 px) and stays on the upright line; the same left only lies on the L diagonal both ways through the centre and reaches the −6 tick; an anti-phase pair is a flat line through the centre; labels 0, −6, −12, +S, −S.
- Polar: mono 100 % in phase, anti-phase 0 %, left only 100 % (at 45°), independent noise shows the share computed here (57 %); a −6 dB mono sample straight up at the −6 dB radius, a left-only one at 45°.
- Phase bar: +1, −1, 0 and +0.5 read "+1.00 0°", "−1.00 180°", "0.00 90°", "+0.50 60°"; the canvas font is put back.
- Afterglow: a dot fades to 14 % in 1/6 s and is gone after a second.
- Live, four tracks (mono, anti-phase, left only, independent noise) in the stereo view: correlation +1.00, −1.00, 0.00, 0.00; the menu's Picture choice works; the master box with the anti-phase pair reads "−1.00" and its angle; its bar hatched. Nothing drawn in the background freeze (the app's heartbeat held during the probe) or with the mixer closed. No audio nodes in the block, no em dashes, no console errors.
- Screenshots looked at (dark and the Light level): the four strips and the master in the stereo field and in the polar view; they match the pick page's O1 and O4 mock-ups (the afterglow only at the normal level).
- `taskIN_A.py` 37 of 37, `taskIN_M.py` 26 of 26, `taskIN_L.py` 24 of 24, `taskIN_S.py` 34 of 34, `taskIN_E.py` 17 of 17, `taskIN_G.py` 31 of 31 (its OTT check read the device a moment after drawing and could miss by the live change; it now allows 1 dB for that and checks that each bar shows the reading it was given). Lint of the release gate clean; the gate's start-up smoke test cannot run on the cloud machine (the Electron binary download is blocked here), as before.
- **Fractals levels unchanged** (`tools/engine-tests/export_same.py`, measured on this file): Kick −19.05560 dB (fb577dd5202b), Bass −35.48685 dB (392ec52590c7) with the master at −10 dB; at 0 dB Kick −9.75669 (0496bb147f6c), Bass −25.48699 (09e0415bec5e).
- **Cost of the stereo view** (`stereo_cost_o.py`, Fractals playing, mixer open, every strip in the stereo view, four runs alternating with the untouched v0.276): drawMixer 3.85 ms median and 5.21 ms mean untouched, 6.15 and 6.71 with IN-O. The mixer draws every second frame, so about 0.75 ms a frame on average, about 0.1 ms per stereo display (the pick page's estimate was 0.15); the Light level has no afterglow layer. Per display, the new dot drawing is cheaper than today's (0.31 to 0.40 ms against 0.53 ms for 512 samples); the extra is the afterglow layer.
- **Frame time** (`tools/ui-tests/frametime.py`, 2194x1139 at 1.75x, Fractals, the default mixer view, two runs alternating with the untouched v0.276; app ms per frame, main-thread ms in brackets):

| Scene | v0.276 untouched | with IN-O |
|---|---|---|
| idle | 0.71, 0.63 (9.4, 9.4) | 0.72, 0.78 (9.6, 10.3) |
| playing, mixer closed | 3.24, 3.20 (25.9, 25.2) | 3.67, 4.21 (26.3, 31.2) |
| playing, mixer open | 9.06, 8.27 (71.7, 67.0) | 9.00, 10.06 (72.1, 73.4) |

  Within the drift of this machine: nothing of IN-O runs with the mixer closed or in the default waveform view (only the master box's value, at the number rate).

### Left
IN-V next: the Visualizer (V1, one frequency axis, viridis with a colour bar, the right-click menu entries). Then IN-C and IN-D (C1, D1), and the additions from the AE3 picks: IN-X17 band listen on any spectrum (filter from lane K, MX-4), IN-X19 low-band correlation on the meters, IN-X25 the target band in the loudness history. Open: E1's gain zoom (IN-E); growing the track taps, if the Mac's frame time allows it.
