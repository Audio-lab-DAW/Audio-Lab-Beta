# Lane L (task SND): edit scripts, tests and renders

- `kit_src.js`: the shared DSP kit as inserted into `index.html` by `snd0_edit.py` (from SND-1 on, `index.html` is the master copy).
- `snd0_edit.py`: SND-0's edit script (re-runnable after a rebase).
- `kit_run.js` + `kit_test.py`: the kit's unit tests against the analog responses (`python3 tools/engine-lab/snd/kit_test.py index.html`).
- `halfband_design.py`: the halfband coefficients (Valenzuela and Constantinides, as in HIIR, WTFPL; own implementation).
- `renders.js`: A/B renders for listening, written to `renders/`.
- `results_snd0.json`: SND-0's numbers (kit tests, exports before and after).
- `snd1_src.js` + `snd1_edit.py`: SND-1 (Filter v2 `filter2`, the Auto Filter's Clean mode, the processor `al-snd-filter`); the edit script puts the block before `askChoice` and re-runs on a fresh file.
- `snd1_measure.py`: SND-1's before and after numbers (Classic Auto Filter and Low-pass filter checksums, responses against the analog curves, aliasing with drive, cost); `results_snd1.json`.
- `snd1_renders.py`: SND-1's A/B renders (`renders/snd1_*.wav`).
- `snd1_docs.py`: SND-1's release docs (backlog entry, Where it stands, the plan table, the update note): `python3 tools/engine-lab/snd/snd1_docs.py <version> <previous version>`.
