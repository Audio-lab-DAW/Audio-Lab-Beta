# Lane D (task NI): edit scripts for the picked ideas

Plan: `docs/ideas-build.md`. One Python edit script per step (`ni_<step>.py`) with unique asserted anchors, so a rebase re-runs it on the fresh `index.html`. New JS goes before `function askChoice(title,text,btns,icon){`, new CSS before `.dacv{display:flex;`, names prefixed `NI_` / `ni`.

- `check_plan.py`: NI-0 check that every picked idea has a step and no unpicked idea has one.
- `ni_1a.py`: NI-1a, the engine of I3 "Why is this clipping?" (clip event log hooks in `meters()` and `trackMeters()`, `NI_clipExplain`). Test: `tools/ui-tests/taskNI_1a.py`.
- `ni_1b.py`: NI-1b, the card of I3 (Clip button, `#niClip`, fixes, command `ni.clipExplain`). Needs `ni_1a.py` first. Test: `tools/ui-tests/taskNI_1b.py`.
- `ni_2a.py`: NI-2a, the analysis of I2 kick and bass tuning lab (`NI_kickBass`, `NI_HOOKS.kickBass`, `NI.kickModel`, `NI_key`). Needs `ni_1a.py` first. Test: `tools/ui-tests/taskNI_2a.py`.
- `ni_2b.py`: NI-2b, the view of I2 (card `#niKB`, canvas drawn once per measurement, fixes, command `ni.kickBass`, main menu entry, `NI_HOOKS.kickBassView`). Needs `ni_2a.py` first. Test: `tools/ui-tests/taskNI_2b.py [repo] [screenshot dir]` (screenshots go outside the repo by default).
