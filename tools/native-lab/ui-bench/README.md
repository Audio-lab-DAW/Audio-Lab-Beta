# UI bench (task RN4)

One scene drawn three ways, to compare a native Metal screen with what Electron can do today:

- a 64-track arrangement scrolling at 800 px/s: clips, 12 notes per clip, beat lines, separators, track headers, playhead;
- 1,000 meters (background, level, peak hold), all moving every frame;
- about 11,000 rectangles a frame, rebuilt on the CPU every frame.

| File | What |
|---|---|
| `metal/main.swift` | Metal: one instanced draw, `CAMetalDisplayLink` asking for up to 240 Hz, 3 drawables |
| `web/scene.js` | The scene, identical to `buildScene` in the Swift file |
| `web/bench.html` | WebGL2 (instanced, as the glass engine draws) and Canvas 2D (`fillRect`, as the arrangement is drawn today); open with `?run=10` to try it in any browser |
| `web/main.js` | Runs the page in Electron and writes JSON |
| `summary.py` | One table from the JSON files |

Each renderer is measured twice: at 3840x2160 off screen with every frame waited for (what a frame costs), and in a
1600x1000 window paced by the display (what the screen gets).

Run on the macOS runner: Actions, "UI bench (task RN4)", Run workflow. Results land on the branch `ui-bench-results`
and as the run's artifact. **The runner is a virtual Mac** (virtual display, paravirtual graphics): its numbers compare
the three ways with each other; they do not predict the user's M4 at 240 Hz.

On the user's Mac: `swiftc -O metal/main.swift -o metalbench && ./metalbench 10` (Xcode command line tools), and
`bench.html?run=10` in Chrome or in AudioLab's Electron.

Findings: `docs/research-native-ui.md`, section 4.
