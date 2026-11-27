# The script sandbox (task XT-DL12, v0.291)

The spike of step DL12 of `docs/extensions-plan.md` (section 9.7): find out, with escape tests, how user scripts (DL13, DL14) can run in AudioLab safely, in the browser version and in the desktop app. No user feature: nothing in the app calls the sandbox yet.

## The decision

**A Worker inside a sandboxed iframe with its own content security policy**, not QuickJS. Built into `index.html` as `xtSandboxRun(code, opts)` and `xtSandboxStop(id)` (block "SCRIPT SANDBOX" before `askChoice`).

| | Worker in a sandboxed frame | QuickJS in WebAssembly (quickjs-emscripten 0.31) |
|---|---|---|
| Size added to `index.html` | about 6 kB of code | the WebAssembly alone is 519 kB (243 kB gzipped, 692 kB as base64 in the single file), plus its glue |
| Speed (a loop of 10 million steps) | 18 ms (V8) | 1424 ms: about 80 times slower |
| Start of a run | 70 to 105 ms for a fresh frame and worker | 13 ms to load, 5 ms per context (but it then needs a worker of its own to keep the page free) |
| Endless loop | stopped by removing the frame, which ends the worker | stopped by an interrupt handler, after 300 ms in the test |
| Memory | no limit inside; with site isolation the frame has its own process, which dies alone (below) | a hard limit (32 MB set in the test, "out of memory" thrown) |
| Network, eval | refused by the browser itself (the policy), tested below | not present at all |
| Language | all of modern JavaScript, async | ES2023 in QuickJS, a separate engine with its own bugs |

QuickJS stays the fallback if a future Chromium or Electron weakens one of the walls below; the tests are written to notice that.

## How it works

1. Each run creates a hidden iframe with `sandbox="allow-scripts"` and nothing else: an opaque origin (`null`), so no access to the page, its storage, its DOM, the desktop bridge (`audiolabDesktop`), popups, navigation of the window or dialogs.
2. The frame's document (`srcdoc`) carries its own policy: `default-src 'none'; script-src 'unsafe-inline' blob:; worker-src blob:`. Only the frame's own small script and blob workers can run. A worker made from a blob inherits the policy, so the user's code meets it too.
3. The frame's script makes a Worker from a blob: the prelude (`console`, `al.input`, `al.change`) and the user's code inside an async function. The user's code never runs on the page's thread or the frame's.
4. The page talks to the frame through one `MessageChannel` handed over at start (no `message` listener on the page). Only plain data goes in (`al.input`, a frozen copy) and out (log lines, changes, a value). Every message is checked: known kinds only, 200 log lines of 500 characters, 10,000 changes, 1 MB in all, 256 kB of code.
5. A time limit (2 s by default). `onSlow` is asked at each limit and may answer "wait" (the user's pick K9b: "asks at 2 s: wait or stop"; the card itself is DL13's).
6. The frame beats every 200 ms; no beat for 1.5 s means its process died (a script that ate all memory) and the run ends with "used too much memory".
7. Stopping removes the frame, which ends the worker even inside an endless loop. A finished run leaves nothing: no frame, no worker, no listener.

Nothing exists until a run: no frame, no worker, no listener, no timer. Measured: load time and frame time the same within noise (below).

## Escape tests

`tools/ui-tests/taskXT_DL12.py` (the browser, and cross-origin isolated as the desktop app serves it; Chromium with site isolation on, as Chrome and Electron have it) and `tools/ui-tests/taskXT_DL12_electron.js` (the real desktop app: the `audiolab://` scheme, cross-origin isolated, the preload bridge present). A local server counts requests; it must see none from the sandbox.

| Attempt | Result |
|---|---|
| `fetch` (cors and no-cors), `XMLHttpRequest`, `WebSocket`, `EventSource` | refused by the policy; the server saw nothing |
| `importScripts`, `import()`, a worker from a URL | refused |
| a worker from a blob | made, but it inherits the same walls (its `eval` and `fetch` fail) and ends with the frame |
| `eval`, `new Function`, `setTimeout` with a string | refused (EvalError; the string is not run) |
| `indexedDB`, `caches` | refused (opaque origin) |
| a `BroadcastChannel` to the page (the app uses one between its windows) | nothing arrives: another origin |
| `window`, `document`, `parent`, `top`, `localStorage`, `UI`, `AudioLab`, `audiolabDesktop`, `SharedArrayBuffer`, `require`, `process` | none exist in the worker; its origin is `null` |
| `fetch('audiolab://app/index.html')` in the desktop app | refused |
| forged messages (`self.postMessage({t:'done'})`) | never reach the page: only the prelude holds the port |
| breaking out of the wrapper (`}; …`) | only reaches the worker itself, with the same walls |
| control 1: the page itself fetches from the same server | it arrives |
| control 2: the same sandbox with its policy lifted | it arrives: so the walls above are the policy's, not an accident of the test |

## Limits

- **Endless loop:** stopped at the limit (1.0 to 1.1 s with a 1 s limit) while the page kept drawing (57 to 63 frames) and the sound kept playing.
- **Memory bomb:** with site isolation the sandbox frame runs in its own process (checked in Electron 45: the frame's process id differs from the window's). A script that fills memory crashes only that process; the heartbeat notices and the run ends ("memory"), the window lives and the next script runs. In Electron 9.6 s with arrays of 200,000 numbers; 61 s with small objects in Chromium. **Without site isolation** (Playwright turns it off by default) the frame shares the page's process and a long memory bomb crashes the page: the 2 s limit keeps a script far from that (the bomb ran 8 s without harm), but DL13 should cap "wait" (for example 3 times, 8 s in all) unless the frame is known to have its own process. The desktop app has site isolation by default; no switch is needed in `desktop/main.js`.
- **Cost:** a run starts in 70 to 105 ms (a fresh frame and worker each time: a clean state, nothing left over). Scripts that stay (DL14) keep one frame and worker alive; that is one idle process.

## Measured on this build

- `taskXT_DL12.py`: 85 of 85 (with the memory bomb), 82 of 82 with `--quick`. `taskXT_DL12_electron.js`: all passed (21).
- Load time (3 runs each, to `AudioLab.version`): before 1.89, 1.65, 1.78 s; after 1.57, 1.55, 1.57 s. Frame time with Fractals playing (240 frames, headless): before 18.1, 17.0, 17.5 ms mean; after 18.2, 17.2, 18.4 ms. The same within noise.
- Exports (`tools/engine-tests/export_same.py`): Fractals Kick -19.05560 dB (fb577dd5202b), Bass -35.48685 dB (392ec52590c7) with the master at -10 dB; Kick -9.75669 dB (0496bb147f6c), Bass -25.48699 dB (09e0415bec5e) at 0 dB, over beats 64 to 96: identical to v0.290.

## For the next steps

- **DL13 (scripts, run once)** builds on `xtSandboxRun`: the script header (`// ==AudioLabScript==`), `al.project` as a copy in `opts.input`, the change list checked against the same rules as the interface and applied as one undo step, the console, and the K9b card on `onSlow`.
- **DL14 (scripts that stay)** needs a long-lived variant: one frame per script, events sent as messages and dropped while busy, 50 ms per handler, `al.net.fetch` performed by the page after the K8b card (the sandbox itself never gets network).
- **Script devices (EX stages)** do not use this sandbox: they are compiled by AudioLab into worklet code (section 4, stage 3).
