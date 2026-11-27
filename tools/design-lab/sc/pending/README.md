# Task SC-B, waiting for the release freeze

SC-B (About as the random set Y1) was built and tested on 27 November 2026 (written on v0.287, rebased onto v0.292 as v0.293), but at push time
`desktop/release-freeze.json` was on main (the release gate's run from 22:10 UTC), so `index.html` could not be pushed (CLAUDE.md, release freeze).
Tested before the freeze: `taskSC_B.py` 19 of 19, `taskAB1.py` 192 of 192 with the patch below, start-up smoke test 14 of 14, lint clean.

To release (the next SC run, once the freeze file is gone from main):
1. `python3 tools/design-lab/sc/sc_b.py index.html <version>` on the fresh file (version = highest on main + 0.001), bump `const VERSION`.
2. `git mv tools/design-lab/sc/pending/taskSC_B.py tools/ui-tests/taskSC_B.py`; `git apply tools/design-lab/sc/pending/taskAB1_y1.patch`
   (taskAB1's two odds checks expect Y1 instead of an even split of two pictures).
3. Run the lint, `taskSC_B.py`, `taskAB1.py . <out>`, and the start-up smoke test; `node desktop/scripts/sync-app.js`.
4. Log: `sc_b_log.md` here (replace vVV and the GATE line), update note, "Where it stands"; delete this folder; push.
