# LT-2, built and tested, held by the release freeze (27 Nov, 22:57 UTC)

The release gate's `desktop/release-freeze.json` has been on main since 21:47 UTC, so `index.html` was not pushed. Built and tested on v0.294 (and before on v0.289 and v0.291): `taskLT_2.py` 13 of 13, `taskLT_1.py` 42 of 42, `taskST_S4.py`, lint clean, Fractals levels unchanged, start-up smoke test 14 of 14 clean (on v0.291 + LT-2).

To release when the freeze is gone (the next LT run):
1. `git pull --rebase`; `python3 tools/engine-lab/lt/lt_2.py` (asserts its anchors; LT-1 must be in).
2. `git mv tools/engine-lab/lt/held/taskLT_2.py tools/ui-tests/taskLT_2.py`; run it and `taskLT_1.py`; lint; smoke test.
3. `python3 tools/engine-lab/lt/held/lt2_release.py <version> <rebased onto>` from the repository root (VERSION, update notes, backlog entry from `LT-2_log.md`, latency-build.md, Where it stands); `node desktop/scripts/sync-app.js`; commit, push; the project doc; the artifact; the notification.

Second LT-2 run (27 Nov, 23:00 to 23:50 UTC, found the step already built and pushed, so it did not build its own): added to `lt_2.py` the fix that keeps a recording going when the playing buffer crackles (LT-1's switch waited for nothing and its restart ended the take), a check for it in `taskLT_2.py` (14 of 14 on v0.294; the check fails without the fix), and `lt2_release.py` now appends the notes line at the end (one line per release, newest last). `taskLT_1.py` 42 of 42, lint clean on v0.294 + LT-2. Still held: `desktop/release-freeze.json` on main since 22:26 UTC.
