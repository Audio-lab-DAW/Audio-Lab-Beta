# Lane K (task MX, mixing engine): edit scripts

One Python edit script per step, `mx<step>.py` (for example `mx1.py`), with unique asserted anchors in `index.html`, re-runnable on a fresh file after a rebase. The plan is `docs/mixing-build.md`; the UI tests are `tools/ui-tests/taskMX_<step>.py`.

## Files per step
- MX-1: `mx1.py`, `mx1.js` (released in v0.294).
- MX-2: `mx2.py`, `mx2.js`; release kit `mx2_release/`.
- MX-3: `mx3.py`, `mx3.js`; release kit `mx3_release/` (after MX-2).
- MX-4: `mx4.py`, `mx4.js` (main thread: Bass mono, hooks, the switch) and `mx4_wl.js` (the Ducker worklet's Spectral methods, inserted into `abxWLF`); release kit `mx4_release/` (after MX-3). Test: `python3 tools/ui-tests/taskMX_4.py index.html out --base <main + MX-2 + MX-3>` compares the old Ducker modes bit for bit.

Release order while the gate's freezes hold: `mx2_release/release.sh`, then `mx3_release/release.sh`, then `mx4_release/release.sh`, each in a fresh clone of main with no `desktop/release-freeze.json`.
