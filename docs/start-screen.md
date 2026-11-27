# AudioLab start screen (task WS, lane Q, prefix `ws`)

Pick page: **AudioLab start screen**, https://claude.ai/artifact/WTti2BsZN4ZvzGrE9GpQ8S (source `tools/design-lab/ws/start.src.html`, built by `tools/design-lab/ws/build.py` into `start.html`; the drawings are `tools/design-lab/ws/splbg.js`, a plain copy of `SPLBG` from `index.html`, never changed).

## Summary

The user's answer to D6 (28 Nov, 00:27 Brussels): "Empty, no songs. To start up, you have to choose or open your own project. Maybe if there is an empty project, so you start up, there should probably be a splash screen to choose your previous projects, or maybe open a template. And let's use the same scientific style that we have on the actual splash screen."

So a fresh install opens with no song (QL1's concern about the Electric Universe vocals in Fractals does not reach the install) and shows a start screen: recent projects, a new empty project, templates (built-in and My templates), open a file, in the splash's style. WS-0 is the pick page with four layouts and three small option families; WS-1 builds the pick.

## What is there today (read for WS-0)

- **Splash (SP1, v0.224):** `SPLBG` (in the body right after `#splash`) draws one of five pictures on one canvas: S2 moons in resonance, S5 harmonograph, S1 dipole field, S7 orbit chart, S6 spectrogram (a third of the chance of each other). Each has its own palette (`SPLBG.PAL`: card gradient, "Lab" gradient, PRO, bar). At most 60 pictures a second (30 in the lighter looks), frames through the activity gate (AO), one still picture with Reduce motion. The card stays `SP1.hold` = 1500 ms after loading, then fades.
- **About (AB1, v0.225):** the same family, Earth with radiation belts, the "Under the hood" spec list.
- **New project dialog `#np` (lane F's):** templates Empty, Beat starter, Audio tracks, Demo song; My templates (IndexedDB, `tplAll`, `tmDB`); Saved projects (`localStorage` `audiolab-saved`, `savedList`); Demo songs (Shrine Legion, Psytrance demo, `openDemo`).
- **Projects (PJ):** tabs in `localStorage` `audiolab-projects` (`{cur,list,win}`, each with `name`, `S`, `file`, `savedAt`, `tOpen`, `tAct`). `.audiolab` files by `openProjectFile` / `openProjectBlob`.
- **Start today:** `firstRun` is set when there is no stored song (`demo()` runs) and a toast says "Demo song loaded...". Since task AI (v0.220) the wrapped `initProjects` closes every restored tab at every start and opens `Fractals_remake` (`frxBoot`), keeping tabs with unsaved work under Saved projects. The release gate (`tools/release-gate/gate.py`, `smoke_electron.js`) measures with the Fractals song open and checks its Kick and Bass levels.
- **Look (LK):** G3 drafting grid in W1 hairlines, L2 amber units (#ffb547), A1 yellow selection (#f5c84c), M3 ambient motion only at Motion Ambient and never in Light mode, N3 dense. Lane F's motion tokens 0 / 50 / 80 / 120 ms (DR5 pick D3: dialogs in place where possible). Glass from the GL engine only, no `backdrop-filter` (glass-engine-plan section 1).

## Research

| App | At start | What makes it fast | Setting |
|---|---|---|---|
| Ableton Live | No start screen; opens the Default Set (or the last Set) | Nothing between you and the work | Save Live Set As Default ([Ableton](https://help.ableton.com/hc/en-us/articles/209067189)) |
| Bitwig Studio | Dashboard: Recent projects, Templates, Demo packages, Open; tabs for Packages, Help, Settings | Search, tabs, same window from the logo later | ([Bitwig](https://www.bitwig.com/userguide/latest/the_dashboard/)) |
| Logic Pro | Project Chooser: New, Recent, Templates, Open | Startup Action: chooser, open most recent, new empty, and more | Settings, General, Project Handling ([Apple](https://support.apple.com/en-mo/guide/logicpro/lgcp43defb63/12.2/mac/15.6)) |
| Cubase | Steinberg Hub: recent projects, templates by category, Create Empty, Open Other | Recent first, empty in one click | Preferences, Startup: Show Hub, Open last project, default template ([Steinberg](https://steinberg.help/cubase_ai/v13/en/cubase_nuendo/topics/project_handling/project_handling_steinberg_hub_r.html)) |
| Studio One | Start page: new song, open, recent files, demos, audio device | Recent files and the audio device on the first screen | ([PreSonus](https://support.presonus.com/hc/en-us/articles/210050353-Studio-One-3-Start-Page)) |
| FL Studio | No start screen; new project from the default or a chosen startup template | Straight into the playlist | File, Templates ([Image-Line](https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/menu_file.htm)) |
| Blender | The splash is the start screen: recent files, new-file templates, open, recover last session; click outside closes it | One click to a recent file; an empty file already waits behind | Preferences, Interface, Splash Screen ([Blender](https://docs.blender.org/manual/en/4.5/interface/window_system/splash.html)) |
| Figma | Home: Recents with thumbnails, search on top, a side rail | Search focused, thumbnails tell files apart | ([Figma](https://help.figma.com/hc/en-us/articles/14381406380183)) |

Taken into every layout: Enter opens the most recent project (with no projects, Enter makes an empty one); typing goes straight into search; arrows move; ⌘N empty project; ⌘O open a file; Esc closes the start screen (the empty app stays). Blender is the closest model for what the user described (the splash holds the choices).

## The layouts (family W)

All four carry the same content: recent projects (name, date, tempo and key with the units in amber, length and track count, a small waveform with the track-colour strip), New empty project, built-in templates, My templates, Open a file, the quiet keyboard line, the Show at start-up switch. Drawn at the user's window (2194 x 1139 at 1.75x = 1254 x 651 points), dark and Light; Light shows the drawing as one still ink picture.

- **W1 ★ Card over the drawing.** The loading card grows into the start screen (1020 x 607 at the user's size); the drawing runs in its top band with the name where the splash has it; recent projects on the left, start something new on the right; drafting grid behind.
- **W2 Drawing in a side panel.** A 430 point panel at the left with the drawing, the name, the version and the switch; the right side has the recent list with 180 point waveforms and a row of five tiles to start. Close to Logic's chooser and Cubase's Hub.
- **W3 Search first, drawing behind.** The drawing fills the window at about a third of its splash brightness; one centred column with a large search field (focused), the recent list and a row of chips. Keyboard first.
- **W4 Dashboard with tabs.** A band of the drawing across the top, a rail (Recent, Templates, Open a file), a grid of cards with large waveforms. Close to Bitwig's Dashboard.

## The other families

- **T, when it shows:** T1 ★ every start (Enter opens the last project); T2 only when no project was open at quit; T3 never at start, only from File, Start screen. Every option keeps the Show at start-up switch on the screen and as a Settings row (lane B).
- **D, the demo songs:** D1 ★ only under New project, Demo songs (not on the start screen); D2 also a quiet line on the start screen; D3 nowhere in the app. Fractals is never offered on a fresh install.
- **P, the hand-over from the splash:** P1 ★ the splash card grows into the start screen and the same drawing keeps running (120 ms); P2 the splash fades, the start screen fades in with another drawing; P3 the start screen's drawing is a still picture. Motion is M3 ambient in all: only at Motion Ambient, never in Light mode, stopped while the window is hidden (AO gate), still with Reduce motion.

Picks line format: `Start screen picks: W1 T1 D1 P1` (★ = W1 T1 D1 P1).

## What WS-1 builds

- The picked layout in its own block of `index.html` (prefix `ws`, before `function askChoice(`; CSS before `.dacv{display:flex;`), shown after the loading splash; lane F's dialog and motion tokens read; `SPLBG` reused through `SPLBG.FN` / `SPLBG.PAL`, never changed; glass from the engine only.
- A fresh install opens the start screen with **no demo song loaded and no demo toast**. The every-start Fractals of task AI stops for normal starts (the tabs are no longer closed and replaced); old users' projects stay and show as recent. Demo songs only where the D pick says.
- Recent projects from the stored tabs, Saved projects and opened files, newest first; templates read from `#np`'s data (`tplAll`, the built-in set); Open a file through `openProjectFile`.
- Show at start-up switch, plus a Settings row for lane B through `ST_HOOKS` (or the S4 table shape). File menu, Start screen to open it any time (a hook for lane F's menu).
- No per-frame work while closed; the drawing asks `LOOK.ambientOK()`; Reduce motion respected; plain language, no em dashes, tooltips.
- The release gate keeps loading its Fractals reference explicitly (check `tools/release-gate/smoke_electron.js` and `gate.py` and keep them working, for example by opening Fractals by name in the gate's own profile).
- Tests `tools/ui-tests/taskWS_1.py`: fresh profile (start screen, no demo, Enter opens the last project, search, every template opens, a saved project opens), old profile (projects listed), screenshots dark and Light at 2194 x 1139 at 1.75x, no console errors; Fractals levels unchanged.

## Picks

**Start screen picks: W1 T1 D3 P1** (the user, 28 November 2026, 00:55 Brussels).

- **W1** card over the drawing, **T1** every start, **D3 no demo songs anywhere in the app** (the user: "once we have the actual app, we're gonna try and make a few new demo songs. The ones we have now aren't that good and unfinished."), **P1** the splash grows into the start screen.
- **The drawings: the dipole field (S1) and the moons in resonance (S2), picked at random each start**, and the user wants **more drawings to add to the random set** "so we have some diversity".
- **The dipole's particles must be right.** The user: "the yellow particles need to come out of the center of the Earth, or the ball in the middle, and then they need to follow the line back in the correct manner ... do some research how to do this scientifically correct. Because now they're just moving back and forth, and that's not ideal. It's good that they are moving on the lines though." Note for the research: today's back and forth is the bounce of particles trapped between mirror points (real Van Allen physics, but it reads as wrong); what the user describes is the field's direction: out of one pole of the ball, along the line, back in at the other pole (and through the inside of the ball to close the loop). Research both (sources), show the corrected flow, keep particles on the lines, speed by the field's strength (faster near the ball, where the lines bunch), spacing even along each line, no particle drawn inside the ball's disc unless shown as passing behind it.
- **The hand-over as one fluid animation** (the user's words): the splash randomises into, for example, the dipole; the drawing moves up; the logo moves to the left, with the 'Digital Audio Workstation' text under it; the recent projects slide up from the bottom; it reads as one single element. "We are going to try a few animations out and then figure out how many milliseconds or seconds the animation should take."

### Next: WS-0b, a second pick page (before WS-1)
1. **More drawings for the random set:** 6 to 8 new scientific drawings in the splash's style and palettes (for example a Lissajous or harmonograph variant, a standing-wave or Chladni plate, a pendulum wave, a spectrogram ribbon of a real kick and bass, an orbital resonance with more moons, a magnetic field of two dipoles, a wave interference pattern, a phase portrait), numbered R1, R2 ..., each live, each running at Ambient motion only, stopped when hidden; the user picks which join S1 and S2 in the random set.
2. **The dipole particles corrected:** today's next to the corrected version(s), with the research and sources in this doc.
3. **The hand-over animation:** 3 to 4 variants of the one fluid motion (drawing up, logo and text to the left, recent projects up from the bottom), each with a duration slider (for example 300 ms to 2 s) and an easing choice, played on a mock at the user's size, with a Replay button; the picks bar gives one line such as 'Start screen round 2: R2 R5 R7 | dipole F2 | motion M3 900 ms'.
Then WS-1 builds W1 T1 D3 P1 with the round 2 picks.

**task WS-0b step claimed** (28 November 2026, 00:57 Brussels): the round 2 pick page (drawings R, dipole flow F, hand-over motion M).
