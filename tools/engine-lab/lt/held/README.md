# LT-2, built and tested, held by the release freeze (27 Nov, 22:57 UTC)

The release gate's `desktop/release-freeze.json` has been on main since 21:47 UTC, so `index.html` was not pushed. Built and tested on v0.294 (and before on v0.289 and v0.291): `taskLT_2.py` 13 of 13, `taskLT_1.py` 42 of 42, `taskST_S4.py`, lint clean, Fractals levels unchanged, start-up smoke test 14 of 14 clean (on v0.291 + LT-2).

To release when the freeze is gone (the next LT run):
1. `git pull --rebase`; `python3 tools/engine-lab/lt/lt_2.py` (asserts its anchors; LT-1 must be in).
2. `git mv tools/engine-lab/lt/held/taskLT_2.py tools/ui-tests/taskLT_2.py`; run it and `taskLT_1.py`; lint; smoke test.
3. `python3 tools/engine-lab/lt/held/lt2_release.py <version> <rebased onto>` from the repository root (VERSION, update notes, backlog entry from `LT-2_log.md`, latency-build.md, Where it stands); `node desktop/scripts/sync-app.js`; commit, push; the project doc; the artifact; the notification.

Second LT-2 run (27 Nov, 23:00 to 23:50 UTC, found the step already built and pushed, so it did not build its own): added to `lt_2.py` the fix that keeps a recording going when the playing buffer crackles (LT-1's switch waited for nothing and its restart ended the take), a check for it in `taskLT_2.py` (14 of 14 on v0.294; the check fails without the fix), and `lt2_release.py` now appends the notes line at the end (one line per release, newest last). `taskLT_1.py` 42 of 42, lint clean on v0.294 + LT-2. Still held: `desktop/release-freeze.json` on main since 22:26 UTC.

Third LT-2 run (28 Nov, 09:10 to 09:25 UTC): the 01:54 freeze was stale, but the release gate started a new run at 09:11:57 UTC (its freeze was removed by mistake by WS-1 at 09:12 and restored in c193e40), so `index.html` was again not pushed. `index.html` on main has not changed since the second run (still v0.294) and `lt_2.py` applies cleanly to it, so the tests of the second run stand. The next LT run releases LT-2 once `desktop/release-freeze.json` is gone (the gate takes about two and a half hours: about 11:40 UTC), following the three steps above.

## LT-3a, built and tested, held behind LT-2 (28 Nov, 10:00 UTC)

Fast MIDI notes in the desktop app (L5): `LT-3a_log.md`. The shell's side (`desktop/lt-midi.js`, one line in `main.js`, the hook at the end of `preload.js`, `lt-midi.js` in `package.json`'s file list) is on main: it does nothing until a page posts `{ ltMidiPort: true }`. The page's side waits for LT-2. Release it after LT-2 (its own version):
1. `git pull --rebase`; `python3 tools/engine-lab/lt/lt_3a.py` (asserts its anchors; LT-2 must be in).
2. `git mv tools/engine-lab/lt/held/taskLT_3a_electron.js tools/ui-tests/`; `node desktop/scripts/sync-app.js`; `xvfb-run -a node tools/ui-tests/taskLT_3a_electron.js` (20 checks; while it sits in held/ pass the desktop folder as the first argument); `taskLT_1.py`, `taskLT_2.py` one at a time; lint; smoke test.
3. `python3 tools/engine-lab/lt/held/lt3a_release.py <version> <rebased onto>`; `node desktop/scripts/sync-app.js`; commit, push; the project doc; the artifact; the notification.

28 Nov, 12:21 to 12:35 UTC: the freeze lifted for 14 minutes; LT-2 was being smoke-tested (20 minutes) and missed the window before the gate froze main again (12:35:47). Both steps were then tested again on v0.297 (smoke 14 of 14, all four LT tests). At the next lift: rebase, re-run the edit scripts, lint, the step's own test, push LT-2 at once, then LT-3a the same way.
