# tools/native-lab (task NM1)

Scripts and reference files for the first native tests. The native code itself is in `native/`, the plan in `docs/native-mac-plan.md`.

| File | What |
|---|---|
| `make_ref.py` | Makes the web engine's reference: opens the real app in headless Chromium, builds the Bitcrusher as the app does, renders `ref/crush_in.wav` for three settings. Needs numpy and Playwright Chromium. |
| `ref/crush_in.wav` | The fixed test signal (half a second, 48 kHz, stereo, 32-bit float), made with whole-number arithmetic so it is the same on every machine. |
| `ref/crush_*_web.wav`, `ref/crush_ref.json` | The web engine's renders, and the numbers JavaScript worked out with `pow` and `exp`, as hex. |
| `run_a.py` | Test A driver: native renders, bit comparison with the web files. `python3 tools/native-lab/run_a.py build/alnative out/a` |
| `summary.py` | Turns a run's JSON files into one text page. |
| `READ-ME-FIRST.txt` | The text that goes with the test app. |
| `pick-page.html` | Source of the pick page (published as an artifact). |

To run everything on an Apple Silicon machine: start the workflow "Native lab (task NM1 tests)" by hand. Tick "release" to publish the test app again as a pre-release.
