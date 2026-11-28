# Lane Q, task WS-0c: start screen round 3 (pick page only)

The user's round 3 (28 Nov 2026, 15:09 Brussels): new particles for the dipole with its flow kept, a cooler phase portrait (R5), a cooler Fourier series (R8), six more drawings.

- `r3a_base.js` to `r3e_new.js`: the drawings, in the splash's function shape `fn(c,w,h,t,P,d)` with palettes like `SPLBG.PAL`. Loaded in that order they make one object `R3` (`R3.FN`, `R3.PAL`, `R3.BAND` band scale per drawing, `R3.WIDE` drawings that run the full width, `R3.NAME`, options `R3.cnt` 0 1 2 and `R3.dir`). Nothing changes `SPLBG` or `R2` / `WSR2`.
  - `r3b_dipole.js`: `dipP0` (today) and the five particle styles `dipP1` to `dipP5` on the unchanged F1 flow.
  - `r3c_phase.js`: `phLor`, `phFlow`, `phPoin`, `phBif`. `r3d_fourier.js`: `fsAtom`, `fsStack`, `fsGibbs`, `fsUnc`. `r3e_new.js`: `drum`, `string`, `mach`, `hydro`, `chirp`, `light`.
- `start3.src.html`: the pick page. `python3 build3.py` inlines the round 1 CSS, `../r2draw.js` (today's R5 and R8, to compare) and the five parts, and writes `start3.html`, published as the artifact "AudioLab start screen, round 3".
- `shot3.py <abs path to start3.html> <out dir> [stage|cards|bench|all]`: every drawing in the start screen (W1) at 100 %, Dark, Light and Reduce motion; the cards; ms per picture (`__bench`); a phone-width overflow check; console errors.
- Plan, numbers and picks: `docs/start-screen.md`, section "Round 3 (WS-0c)".
