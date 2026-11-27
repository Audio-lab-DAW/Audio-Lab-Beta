# LT: playing latency and engine load (task LT, lane J)

Edit scripts and measurements for `docs/latency-build.md`. One script per step, `lt_<step>.py`, with unique asserted anchors in `index.html`, re-run on the fresh file after every `git pull --rebase`. The measurements reuse `tools/engine-lab/ae2/` (`latency_chain.py`, `pdc_live.py`, `perf_load.py`) and `tools/engine-tests/export_same.py`; the UI tests are `tools/ui-tests/taskLT_<step>.py`.
