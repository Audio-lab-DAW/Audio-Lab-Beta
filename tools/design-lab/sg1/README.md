# Task SG1: stem split progress (research and pick page)

- `stem-split.html` + `sg1-data.json`: the pick page (published as "AudioLab stem split: the loading bar is the spectrogram"). Serve the folder (`python3 -m http.server`) to open it locally; `shot.py . <outdir>` takes screenshots.
- Measurements (working folder `/home/claude/sg1w` in the run that made them; pass your own):
  1. `run.py iso quick` (with `probe.py`, the AudioLab bridge with cross-origin isolation, the ONNX engine and model routed to local copies): renders Fractals beats 0 to 96, times the quick split and the FFT, saves the mix and quick stems.
  2. `chunks_node.mjs <threads> <n4|n6>`: the app's HTDemucs worker loop (NEUW) unchanged in Node with onnxruntime-web 1.20.1 WASM; chunk times and stems. Needs `npm i onnxruntime-web@1.20.1` and the two model files from Hugging Face (StemSplitio/htdemucs-onnx, htdemucs-6s-onnx) in `../model/`.
  3. `spec.py quick n4 n6`: log-frequency spectrograms (72 rows, 32 Hz to 16 kHz, 4096/2048 at 44.1 kHz), then `build_data.py` writes `sg1-data.json`.
- Report: `docs/stem-split-progress.md`.
