# AE2: performance and playing latency (task AE2)

Measurement scripts and the pick page for `docs/research-engine-performance.md`. They open this checkout's `index.html` headless through `tools/remake/alab.py` and build the Fractals remake v6 (`tools/remake/examples/fractals_v6`).

- `probe.py`: what Chromium reports (base, output latency, render block) for each buffer setting.
- `latency_chain.py [presses]`: real key presses to the first sample of the note, split into main thread, start, and browser/device parts. Result: `latency_chain_result.json`.
- `perf_load.py`: CPU per track (solo offline renders, one thread), the song at x1, x2, x4, and live load, dropouts and long tasks. Result: `perf_load_result.json`.
- `pdc_live.py`: the delay compensation applied to a played track. Result: `pdc_live_result.json`.
- `pick-page.html`: the published pick page (with the key-to-sound tester).
