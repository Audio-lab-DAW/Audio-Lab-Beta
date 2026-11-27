# Lane L (task SND): edit scripts, tests and renders

- `kit_src.js`: the shared DSP kit as inserted into `index.html` by `snd0_edit.py` (from SND-1 on, `index.html` is the master copy).
- `snd0_edit.py`: SND-0's edit script (re-runnable after a rebase).
- `kit_run.js` + `kit_test.py`: the kit's unit tests against the analog responses (`python3 tools/engine-lab/snd/kit_test.py index.html`).
- `halfband_design.py`: the halfband coefficients (Valenzuela and Constantinides, as in HIIR, WTFPL; own implementation).
- `renders.js`: A/B renders for listening, written to `renders/`.
- `results_snd0.json`: SND-0's numbers (kit tests, exports before and after).
