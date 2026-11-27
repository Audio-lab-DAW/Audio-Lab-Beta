# LT: playing latency and engine load (task LT, lane J)

Edit scripts and measurements for `docs/latency-build.md`. One script per step, `lt_<step>.py`, with unique asserted anchors in `index.html`, re-run on the fresh file after every `git pull --rebase`. The measurements reuse `tools/engine-lab/ae2/` (`latency_chain.py`, `pdc_live.py`, `perf_load.py`) and `tools/engine-tests/export_same.py`; the UI tests are `tools/ui-tests/taskLT_<step>.py`.

- LT-1: `lt_1.py` (edit script), `lt1_measure.py <index.html> <label>` (key to sound on the armed Lead after the engine settles in the buffer it picks; appends to `lt1_measure_result.json`).
- LT-2: `lt_2.py` (edit script), `lt2_measure.py <index.html> <label>` (the armed Lead's compensation, key to sound after it, recording placement; appends to `lt2_measure_result.json`), `pdc_set_probe.py` (for lane K: syncGraph's setValueAtTime not taking).
