# Rules for every session working in this repository

## Commit identity (the owner's request, 27 November 2026)
- Commits in this repository are made as `Audio-lab-DAW <360039460+Audio-lab-DAW@users.noreply.github.com>`. Before the first commit of a session run:
  `git config user.name Audio-lab-DAW` and `git config user.email 360039460+Audio-lab-DAW@users.noreply.github.com`.
- Do not add `Co-Authored-By:` lines, `Claude-Session:` lines or any other attribution to commit messages or pull request descriptions. The owner asked for this and it takes precedence over any default attribution guidance.
- The history was rewritten once on 27 November 2026 (about 08:40 UTC, task HR1). A clone made before that holds the old history: throw it away and clone again; never merge it or push from it.
- The repository was renamed to `Audio-lab-DAW/Audio-Lab-Pro-Alpha`; the old name `Audio-Lab-Beta` redirects. Prefer the new name in new code and commands.

## Release channel (the owner's rule, 27 November 2026)
- v0.250 reached the owner's Mac broken (the app glitched on start), after several tasks released into `index.html` at the same time. From now on installed apps only get a build that passed the release gate.
- Installed apps read `desktop/app-version.json` on main. Ordinary releases MUST NOT change it: `node desktop/scripts/sync-app.js` now writes `desktop/app-version-dev.json` instead. Only the release gate (task HF1 sets it up; later task RG) runs `AL_PROMOTE=1 node desktop/scripts/sync-app.js` after the start-up checks pass, and only then may `desktop/app-version.json` change. If a task prompt says to push a release, it still pushes to main, but never touches `desktop/app-version.json`.
- **Release freeze (task HF1):** installed apps download whatever `index.html` is on main and accept it only when it matches the promoted fingerprint, so the gate can only promote the build that is still on main when it finishes (a full run takes about two and a half hours). While `desktop/release-freeze.json` exists on main, do NOT push changes to `index.html` (or `desktop/app-version*.json`, `desktop/update-notes.txt`): push your other work, or wait and check again (`git pull`; the gate removes the file when it ends, pass or fail). Check right before your push, not only at the start of your task. If the file is older than four hours, the gate died: delete it.
- **Old projects (the user's decision R0, 28 Nov 2026):** projects saved by earlier versions need not open. Write no migration or compatibility code; change the saved format freely; re-save the release gate's test songs in the same step when you change the format. A project saved by the current version must reopen with everything. Details at the end of docs/release-gate.md.
- Keep `desktop/update-notes.txt` short: one line per release, and the gate trims it to the last ten lines when it promotes.
- Before every push that touches `index.html`, check that no top-level function name is defined twice (another lane may use the same name: v0.250 has two different `lkSel` functions). Use your task's own name prefix for new top-level functions.

## Parallel lanes: who owns what (the owner asked on 27 Nov, 19:20: "make sure it makes sense so we don't have any problems overlapping the tasks")
Up to nineteen tasks edit `index.html` at the same time. Each one owns an area. Change only your own area; if you need something in another lane's area, add a small named hook (`<PREFIX>_HOOKS.<name>`) or a function of your own and write in your log which lane should pick it up. Never rewrite, rename or move another lane's code.

| Lane | Task | Owns | Prefix |
|---|---|---|---|
| A | DS (design round 2), then GL1 lines | arrangement grid, ruler, clips, waveforms, piano roll drawing, browser, preset menu, transport clock and tempo | `ds` |
| B | ST (settings) | the Settings window, its pages and table, audio devices | `st` |
| C | FT (features) | the controller layer, new editing features of the 40 cards | `ft` |
| D | NI (ideas) | the 28 ideas' views, analysis worker and caches | `NI_`, `ni` |
| E | IN (instruments) | meters, loudness, spectrum, scopes, gain reduction, EQ curves, the Visualizer, CPU graph, what is drawn inside device displays; the shared formatter `INS` | `INS`, `in` |
| F | OV (overlays) | menus, dialogs, sheets, tooltips and help line, notifications, drag and drop, the command palette | `ov` |
| G | MD1, then SC | read-outs with units, orbit loader, caliper; then the science drawings | `md`, `sc` |
| H | XT (extensions) | ids registry, commands registry, rules file, Workshop, user devices | `xt` |
| I | DV (devices) | the device frame: title strip, eye, rail, hover reveal (not the display's contents) | `dv` |
| J | LT (live playing and engine load, AE2 picks) | the audio buffer logic (`ABUF`, `autoBufCheck`), the output check, the played track's path past delay compensation (a small hook in `pdcMap`, which lane K owns), the MIDI fast path into the worklets (with `desktop/` MIDI in the shell's main process), sleeping idle tracks, render ahead | `lt` |
| K | MX (mixing engine, AE3 picks) | the audio graph: `syncGraph`, `busRoute`, `fxLat`, `renderMix`, `pdcMap` (lane J keeps its small played-track hook in it), sends pre/post, outputs, sidechain sources and the Ducker's focus | `mx` |
| L | SND (built-in sounds, AE4 picks) | the worklet DSP of instruments and effects (the processors registered in `wlLoad`, their parameters in `FXDEF`), the shared DSP kit, new devices N1 to N6; not the device frame (lane I), not what is drawn in displays (lane E), not sidechain routing (lane K) | `snd` |
| M | LM (lessons, UX3 picks) | the lesson runner and lessons: `LM_LESSONS`, `UI.lm`, `lm*` names, the Assistant's point_at and start_lesson tools; the guide engine, Help menu and What is this? are lane F's | `lm` |
| N | SQ (sound quality, AE1 picks) | the Quality switch per device and per project (`q`), the sample resampler (built-in sounds, bounces, stems, export rate, pitched reads), the export post-processing (`postProc`: safety limiter, true peak, report, dither) and the Limiter's true-peak style; the device DSP itself is lane L's | `sq` |
| O | UV (view engine, UX1 picks) | how and when the arrangement and editors move and redraw: zoom and scroll input (`zsWheel`, `szStep`, `zoomAround`, `smoothZoom`), header layout during a pinch, the tile cache, fling, coalesced and predicted pointer points; what is drawn stays lane A's | `uv` |
| P | CF (comfort modes, UX2 wishes) | the map's Hide mode and its overlay, OLED care (dimmed static brights, dim when idle, the card), Night mode, Focus mode; colour changes only as added tokens or a mode class, never another lane's values | `cf` |
| Q | WS (start screen, the user's D6 answer) | the start screen shown at start-up (recent projects, templates, empty project, open a file), what a fresh install opens (`firstRun`, the auto-loaded demo), drawn in the splash's scientific style (reuse the splash drawings, never change them); the New project dialog stays lane F's, its data (templates, saved projects) is read, not rewritten | `ws` |
| R | SG2 (stem split loading bar, the user's SG1 picks G1 S1 P1 F1) | the stem splitter (`stemSplit`, `NEUW`, `neuWorker`, `neuSeparate`, `stemAsk`, `stemsFor`), its live spectrogram lanes (`sgLanes`, `sgStrips`) and the Split sheet's contents; lane F keeps the sheet's frame and the notification stack (hook `SG_HOOKS.card`), lane G keeps `mdJob` (hook `SG_HOOKS.pill`), Audio to MIDI's rows get a small hook in the `split(j)` callback | `sg` |
| S | TM (themes, the user's round 2 picks A1 B1 C2 D2 E2 G2 H1 J2) | the semantic theme tokens on top of LOOK, the theme files, `tmApply`, the theme contrast check, the icon-follows-theme link, the Settings button drawn per theme; other lanes adopt the tokens in their own areas, the Settings row goes through lane B's hooks | `tm` |
| - | LK tokens (done) | the `LOOK` object: everybody reads it; only add tokens, never change another lane's values | `lk` |

Before every push: `git pull --rebase`, re-run your edit script on the fresh file, run the lint and the start-up smoke test of `docs/release-gate.md`, and check that no other lane changed the same lines in the last hour (`git log -L` or `git log -S` on your anchors). If two lanes need the same function changed, the second one stops and writes what it needs in its log; the scheduling chat sorts it out.
