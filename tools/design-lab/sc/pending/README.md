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

28 November 2026, 09:1x UTC: re-checked on main v0.294 (applied as v0.295 in a scratch copy): every anchor still unique, lint clean (2354 top-level functions),
`taskSC_B.py` 19 of 19 (20,000 picks: corner 5935, sheet 6072, orbit 3997, arcs 3996; 23 and 24 pictures a second while open; 0 when closed; no console errors).
Not pushed: the gate started a new freeze at 09:11:57 UTC. Release unchanged: the steps above, once the freeze is gone.

28 November 2026, 16:40 to 17:15 UTC (third try): applied to main v0.314 as v0.315 in the working copy: every anchor unique, lint clean (2600 top-level functions),
`taskSC_B.py` 19 of 19 (20,000 picks: corner 5813, sheet 6040, orbit 4184, arcs 3963; 21 and 23 pictures a second while open; 0 when closed; no console errors),
`taskAB1.py` 192 of 192 with the patch, `taskSC_A.py` 30 of 30, About screenshots of the orbit corner and the field arcs looked at (faint, clear of the text).
`gate.py --here --quick --ref 0.314`: every step passed (smoke 14 of 14 clean, idle frame times p50 16.7 ms and p95 66.7 ms as v0.314, windows 19 checks,
Fractals Kick -19.05560 dB and Bass -35.48685 dB, same checksums, 9 export lines bit-identical). Not pushed: the gate's freeze from 16:41:15 UTC was on main.
(Note for the next run: the quick gate needs `--ref <newest version>`; the default reference v0.250 has no release commit in the rewritten history.)

