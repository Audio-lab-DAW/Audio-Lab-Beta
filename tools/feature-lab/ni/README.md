# Lane D (task NI): edit scripts for the picked ideas

Plan: `docs/ideas-build.md`. One Python edit script per step (`ni_<step>.py`) with unique asserted anchors, so a rebase re-runs it on the fresh `index.html`. New JS goes before `function askChoice(title,text,btns,icon){`, new CSS before `.dacv{display:flex;`, names prefixed `NI_` / `ni`.

- `check_plan.py`: NI-0 check that every picked idea has a step and no unpicked idea has one.
- `ni_1a.py`: NI-1a, the engine of I3 "Why is this clipping?" (clip event log hooks in `meters()` and `trackMeters()`, `NI_clipExplain`). Test: `tools/ui-tests/taskNI_1a.py`.
- `ni_1b.py`: NI-1b, the card of I3 (Clip button, `#niClip`, fixes, command `ni.clipExplain`). Needs `ni_1a.py` first. Test: `tools/ui-tests/taskNI_1b.py`.
- `ni_2a.py`: NI-2a, the analysis of I2 kick and bass tuning lab (`NI_kickBass`, `NI_HOOKS.kickBass`, `NI.kickModel`, `NI_key`). Needs `ni_1a.py` first. Test: `tools/ui-tests/taskNI_2a.py`.
- `ni_2b.py`: NI-2b, the view of I2 (card `#niKB`, canvas drawn once per measurement, fixes, command `ni.kickBass`, main menu entry, `NI_HOOKS.kickBassView`). Needs `ni_2a.py` first. Test: `tools/ui-tests/taskNI_2b.py [repo] [screenshot dir]` (screenshots go outside the repo by default).
- `ni_3.py`: NI-3, the analysis worker and the per-beat band cache (`NI_anWork`, `NI.an`, `NI_HOOKS.analysis`, IndexedDB `audiolab-ni`). Needs `ni_2a.py` first. Test: `tools/ui-tests/taskNI_3.py [repo]` (about 5 minutes: it plays the Fractals demo twice for 45 s).
- `ni_4.py`: NI-4, the frequency map view (`#niMap` window, `NI.map`, command `ni.freqMap`; adds `grp` to NI-3's list of track fields left out of the key). Needs `ni_3.py` and lane E's IN-A first. Test: `tools/ui-tests/taskNI_4.py [repo] [screenshot dir]`.
- `ni_5a.py`: NI-5a, masking cables part 1: the clashes (`NI_clashAt`, `NI.clash`, the Clashes switch in the cable legend, magenta cables in the cable lane, the click card, command `ni.clashes`, `NI_HOOKS.clashPop`). Needs `ni_4.py` first. Test: `tools/ui-tests/taskNI_5a.py [repo] [screenshot dir]`.
