# Lane D (task NI): edit scripts for the picked ideas

Plan: `docs/ideas-build.md`. One Python edit script per step (`ni_<step>.py`) with unique asserted anchors, so a rebase re-runs it on the fresh `index.html`. New JS goes before `function askChoice(title,text,btns,icon){`, new CSS before `.dacv{display:flex;`, names prefixed `NI_` / `ni`.

- `check_plan.py`: NI-0 check that every picked idea has a step and no unpicked idea has one.
