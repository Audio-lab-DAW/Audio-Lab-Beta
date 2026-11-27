# Task AE1: engine sound quality lab

Measures what AudioLab's engine does to the sound today and compares the candidate improvements. Write-up: `docs/research-engine-sound.md`. Pick page: https://claude.ai/artifact/EveKcsa3xrtaedKUCShSqW

| File | What it does |
|---|---|
| `measure_app.py` | renders through the app itself (AudioLab bridge, `tools/remake/alab.py`): al-poly saw and Acid aliasing, Drive and Soft Clipper, al-limit and the export safety limiter (true peak), 64-track summing against Float64, AudioBufferSourceNode and decodeAudioData resampling, postProc dither, Soft Clipper DC. Writes `results/app.json` |
| `dsp.js` | today's algorithms ported from index.html v0.263 (each checked against the app) and the candidates: table BLEP, ZDF SVF, ADAA, half-band oversampling, sinc resampler, BS.1770 true-peak limiter, 9-tap shaped dither, DC blocker |
| `lab.js` | runs `dsp.js` on the test signals (`results/sig/`, not committed) and measures CPU (`results/cpu.json`) |
| `lab_anal.py`, `anal.py` | aliasing against harmonics (Kaiser β 20, floor −165 dB), true peak (16x), spectra; writes `results/lab.json` and `results/plots.json` |
| `page_template.html`, `build_page.py` | the pick page (`sound-quality-picks.html`): A/B tests computed in the browser with the same `dsp.js` |

Run, from the repository root:

    python3 tools/engine-lab/ae1/measure_app.py index.html      # about 10 minutes
    python3 -c "import numpy as np;np.load('tools/engine-lab/ae1/results/demo_climax.npy').astype(np.float32).tofile('tools/engine-lab/ae1/results/demo_climax.f32')"
    node tools/engine-lab/ae1/lab.js
    python3 tools/engine-lab/ae1/lab_anal.py
    python3 tools/engine-lab/ae1/build_page.py
