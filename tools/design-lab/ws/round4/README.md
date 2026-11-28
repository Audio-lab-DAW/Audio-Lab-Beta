# Lane Q, task WS-0d: start screen round 4, the final set (pick page only)

The user's last round (28 Nov 2026, 18:39 Brussels): everything picked in round 3 goes into the random set; PH4, FS1, N1, N2 and N4 reworked; the rest polished.

- `r4a_base.js` to `r4e_new.js`: the drawings, in the splash's function shape `fn(c,w,h,t,P,d)` with palettes like `SPLBG.PAL`. Loaded in that order they make one object `R4`, self-contained (it needs nothing from round 3): `R4.FN`, `R4.PAL`, `R4.BAND` (band scale per drawing), `R4.WIDE` (drawings that run the full width: the host shades behind the name), `R4.NAME`, `R4.STILL` (the time of the still picture per drawing; 40 when not listed), `R4.SET` (the final random set in the order of the Settings list), options `R4.cnt` 0 1 2 and `R4.dir`. Nothing changes `SPLBG` or `R2` / `WSR2`.
  - `r4b_dipole.js`: `dipP2` density, `dipP3` energy, `dipP4` radiation belt, `dipP5` aurora, on the unchanged F1 flow.
  - `r4c_phase.js`: `phLor`, `phFlow`, `phPoin`, and the new `phFrac` (PH4). `r4d_fourier.js`: the new `fsWind` (FS1), `fsStack`, `fsGibbs`, `fsUnc`. `r4e_new.js`: `drum`, `string`, `hydro` (reworked), `mach`, `chirp`, `light`.
- `start4.src.html`: the pick page. `python3 build4.py` inlines the round 1 CSS, `../splbg.js` and `../r2draw.js` (the four drawings that stay in the set unchanged) and the five parts, and writes `start4.html`, published as the artifact "AudioLab start screen, the final set".
- `shot4.py <abs path to start4.html> <out dir> [stage|times|cards|bench|all] [ids]`: every drawing in the start screen (W1) at 100 %, Dark, Light and Reduce motion; a drawing at chosen times of its own clock (`__at`); the grid; ms per picture (`__bench`); a phone-width overflow check; console errors.
- Plan, numbers and the line to paste: `docs/start-screen.md`, section "Round 4 (WS-0d)".
