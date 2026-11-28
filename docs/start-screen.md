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

## Round 2 (task WS-0b): drawings, the dipole's particles, the hand-over

Pick page: **Start screen round 2**, https://claude.ai/artifact/Hu3XawkiQC1jAwXZCe2e7r (source `tools/design-lab/ws/start2.src.html` and `r2draw.js`, built by `build2.py` into `start2.html`; screenshots and console check by `shot2.py`). No `index.html` change. `r2draw.js` holds every new drawing in the splash's own function shape `fn(c,w,h,t,P,d)` with a palette like `SPLBG.PAL`, so WS-1 can add them beside `SPLBG` without changing it.

### R, new drawings for the random set (S1 dipole and S2 moons are already in)
Each is real physics or maths, drawn in the splash's look (hairlines, amber dots and mono labels, one palette each), live at Ambient motion only, one still ink picture in Light mode, still with Reduce motion. Shown on the page in the splash card and in the start screen's 172 point band (each drawing has its own band scale so its figure fits).
- **R1 ★ Chladni plate:** nodal lines of a free square plate, cos(nπx)cos(mπy) ∓ cos(mπx)cos(nπy) (Ritz; [Paul Bourke](https://paulbourke.net/geometry/chladni/), [Wolfram](https://resources.wolframcloud.com/FunctionRepository/resources/ChladniFigure)); 1300 sand grains are thrown where the plate shakes and settle on the still lines; a new mode every 12 s and the sand walks to it.
- **R2 ★ Pendulum wave:** 15 pendulums, 51 to 65 swings in 60 s, seen from above ([Harvard Natural Sciences Lecture Demonstrations](https://sciencedemonstrations.fas.harvard.edu/presentations/pendulum-waves)).
- **R3 Two magnets:** field lines of two parallel dipoles, stepped along B = Σ(3(m·r̂)r̂ − m)/r³, dots flowing from each north pole to a south pole.
- **R4 Wave interference:** two sources in step, each falling off as 1/√r; the still lines are hyperbolas (rendered at 200 points wide and scaled, like the splash's spectrogram).
- **R5 Phase portrait:** the Van der Pol oscillator (μ 1.2), 34 tracers ending on the limit cycle, a faint direction field ([Lebl and Bazett](https://web.uvic.ca/~tbazett/diffyqs/limitcycles_section.html)).
- **R6 ★ Lissajous figure:** an oscilloscope with two tones in a simple ratio (3:2, 5:4, 1:2, 3:4, 5:3, 2:3), the phase drifting; a new ratio every 16 s.
- **R7 TRAPPIST-1:** seven planets, orbits to scale, periods 1.51 to 18.77 days in the 8:5 5:3 3:2 3:2 4:3 3:2 chain ([Tamayo et al. 2017](https://ar5iv.arxiv.org/html/1704.02957)); close to the moons.
- **R8 ★ Fourier series:** six harmonics as turning circles building a square, a sawtooth or a triangle wave, a new wave every 14 s.

### F, the dipole's particles
Research. The splash's dipole draws field lines r = L sin²θ; the field's strength along them is ∝ √(1 + 3cos²θ)/r³, 2 at the pole's surface and 1 at the equator's ([LibreTexts](https://phys.libretexts.org/Bookshelves/Electricity_and_Magnetism/Electricity_and_Magnetism_(Tatum)/03%3A_Dipole_and_Quadrupole_Moments/3.10%3A_A_Geophysical_Example), [NASA CCMC](https://webarchive.library.unt.edu/web/20201218011644/https://ccmc.gsfc.nasa.gov/RoR_WWW/presentations/Dipole.pdf)). Today's dots copy trapped charges in a radiation belt: a charge spirals round its line and turns back at a mirror point where B = B_eq / sin²(pitch angle), with v_parallel = v √(1 − B/B_mirror) ([Fitzpatrick, magnetic mirrors](https://farside.ph.utexas.edu/teaching/plasma/Plasma/node23.html), [Marsch](https://www2.mps.mpg.de/solar-system-school/lectures/space_plasma_marsch/Lecture_3.pdf)); without the spiral, in a flat drawing, it reads as sliding to and fro. What the user describes is the field's direction: out of one pole, along the line, in at the other, closing through the magnet. Inside a uniformly magnetised ball the field is uniform, so each line closes as a straight chord ([Fitzpatrick, Electromagnetism](https://farside.ph.utexas.edu/teaching/jk1/Electromagnetism/node61.html), [Goshen College](https://www.goshen.edu/physix/303/gco/6.3.Magnetizedsphere.pdf)). Jupiter's dipole points opposite to Earth's, so at Jupiter (the splash's 10 degree tilt) the field leaves the north half ([Magnetosphere of Jupiter](https://wikiwand.com/EN/Magnetosphere_of_Jupiter), [NASA](https://pwg.gsfc.nasa.gov/stargaze/planetmg.htm)); the page has a Jupiter / Earth switch.
- **F0 Today:** the bounce as it ships.
- **F1 ★ Field flow, closed loops:** out of the north pole, along the line, in at the south pole and up through the ball (faint chords, dim dots, seen through it); speed V·(B/2)^0.2 (faster near the ball; the true ratio would freeze the outer lines), dots evenly spaced in travel time (1.1 s), so they spread near the ball and close up far out, as a real flow does.
- **F2 Field flow, even:** the same direction at one speed with even gaps, surface to surface, nothing inside the ball.
- **F3 Trapped particles, done properly:** ten charges on five lines with equatorial pitch angles 32 to 62 degrees, mirror points solved from the field and marked, spiral (gyration radius ∝ 1/√B) and the right slowing near the mirror points.

### M, the hand-over as one motion (the user's description)
Drawn at the user's window, 1254 x 651 points: the splash (577 x 427) shows its drawing for 1.2 s with the bar filling, then the card grows into W1's card (1020 x 607), the drawing rises into the 172 point band (one canvas, the drawing's frame moved and scaled, clipped to the band), the name glides from the splash's centre to the band's lower left with "Digital audio workstation · v0.300" rising under it, the loading bar becomes the band's lower edge, and the recent projects and the tiles rise from below. A length slider (300 to 2000 ms), four easings (smooth out cubic-bezier(.2,.7,.2,1), in-out (.65,0,.35,1), emphasised (.2,0,0,1), a gentle spring), Replay, a scrubber, Dark and Light (Light ends on the still ink picture).
- **M1 ★ Together** (900 ms, smooth out): all at once, rows 220 ms in, 30 ms apart.
- **M2 Three beats:** the drawing rises, then the name moves, then the rows.
- **M3 Full window:** the card grows to the whole window, band edge to edge.
- **M4 Sheet from below:** the drawing fills the card; the lower half comes up as one sheet carrying the lists.
In the app: Reduce motion makes it a 120 ms fade; Enter works from the first frame (it opens the last project at once); no per-frame work once it ends except the band's ambient drawing (Motion Ambient, Dark, window shown).

Round 2 picks line format: `Start screen round 2: R1 R2 R6 R8 | dipole F1 Jupiter | motion M1 900 ms smooth` (★).

### Round 2 picks
(waiting for the user's line; WS-1 builds W1 T1 D3 P1 with these picks)

## The user's round 2 picks (28 November 2026, 01:46 Brussels)

**Start screen round 2: R4 R5 R6 R7 R8 | dipole F1 Jupiter | motion M1 1000 ms smooth**

- **The random set:** S1 dipole field and S2 moons in resonance (round 1) plus **R4, R5, R6, R7, R8** from round 2.
- **The dipole:** particle flow **F1**, in the **Jupiter** option as the page names it. The user also wants the S1 dipole's particles **a little smaller and fewer** ("let's have the particles a little smaller and a little less particles").
- **The hand-over:** **M1, 1000 ms, smooth** easing: one fluid motion from the splash into the start screen (the drawing moves up, the logo and the 'Digital Audio Workstation' text move to the left, the recent projects slide up from the bottom).
- With round 1's **W1 T1 D3 P1**. WS-1 builds all of this.

## Added 01:53 Brussels: choose which drawings appear

The user: "you should have in the settings where you can turn off some of these or only have one on. And that setting should be a little bit more hidden. But put it on a place where it makes sense."
- A setting listing the drawings of the random set (S1 dipole field, S2 moons, R4 to R8), each with a switch, plus "Only this one" per drawing; at least one stays on; the default is all on.
- A little hidden: not on the start screen itself and not a top-level Settings row. Proposed place: Settings, Appearance, under the start screen's own row 'Show the start screen at start-up', as an expanding 'Start screen drawings…' line (a hook for lane B: WS_HOOKS.settingsRows in the S4 shape); the splash uses the same choice, since it picks the same drawings.
- If WS-1 is already released without it, do it as WS-1b.
## WS-1: the build (lane Q)

Built in `tools/design-lab/ws/ws1.js` and `ws1.css`, put into `index.html` by `python3 tools/design-lab/ws/ws1_edit.py` (anchors asserted; `r2draw.js` goes in as `WSR2`). Test: `tools/ui-tests/taskWS_1.py` (38 checks).

- **Start-up (T1, D3):** the stored tabs come back as they were: no Fractals song at every start, no demo songs added, no "Demo song loaded" toast. With no stored project there is one empty "Untitled" project (one audio and one instrument track, 120 BPM) behind the start screen; it is dropped when you open something else without touching it. Old profiles keep every tab and saved project and see them as recent, the one open at quit first.
- **The start screen (W1):** recent projects (open tabs and Saved projects; name, where it lives, when it was last on screen, tempo, length and track count with the units in amber, a small map of the song in its track colours), New empty project, Beat starter, Audio tracks, My templates, Open a file, More options (lane F's New project window), the keyboard line and the Show at start-up switch. Enter opens the selection (the last project first; with no projects the empty project), arrows move, typing searches, Escape clears the search and then closes, ⌘N / Ctrl+N, ⌘O / Ctrl+O; a click outside the card closes it (Blender's way).
- **The drawings:** S1 dipole with the F1 field flow (Jupiter; particles smaller, about 30 % fewer), S2 moons, R4 interference, R5 phase portrait, R6 Lissajous, R7 TRAPPIST-1, R8 Fourier; never the same twice in a row. When the splash already shows the dipole or the moons, the start screen keeps that picture, so the hand-over is one picture; otherwise the splash's picture dissolves into the start screen's while the card grows (SPLBG itself is not changed, so its five pictures still come first in the splash).
- **The hand-over (P1, M1):** 1000 ms, smooth out cubic-bezier(.2,.7,.2,1): the card grows from the splash's rect, the drawing rises into the band, the name glides to the lower left with "Digital audio workstation · vX" rising under it, the loading bar becomes the band's edge, the rows rise one after another. The splash's hold after loading is 400 ms when the start screen follows. Reduce motion, Light mode or Motion "Signal only": a 120 ms fade. Enter pressed during the splash opens the last project straight away.
- **Motion:** the band's drawing moves only at Motion Ambient, never in Light mode, with Reduce motion or while the window is hidden; otherwise one still picture. Closed: nothing per frame.
- **Where it is reachable later:** the + menu next to the tabs, "Start screen…" (it replaces "Demo: Fractals remake"); `WS_HOOKS.open()` for lane F's menus.
- **Settings (lane B):** the row "Show the start screen at start-up" in the S4 table shape (`WS_HOOKS.row`, pushed into `STT`), its checkbox right after the splash's on the General page (`WS_HOOKS.settingsRow()`); lane B may move it.
- **D3:** the New project window hides Demo song and the Demo songs list (CSS only); `openDemo`, `openDemoFractals` and `demo()` stay as functions (the Beat starter uses `demo()`'s first two tracks; the release gate and the tests open Fractals by name).
- **Automation:** under `navigator.webdriver` (the Playwright UI tests, `export_same.py` through `tools/remake/alab.py`) the start is the one before this step (task AI's Fractals song), unless localStorage `audiolab-ws-test` is `1`; so the gate's UI tests and its Fractals levels keep their song. The desktop smoke test opens Fractals by name and opening a project closes the start screen. Lane M's lesson offer uses the same `navigator.webdriver` test.
- **Not in this step:** a key per project (projects store no key yet); thumbnails of the arrangement are a small clip map, not audio waveforms.

- **Next: WS-1b**, the drawings setting the user asked for at 01:53 (above): it is not in this build, which was made before that note.

### WS-1 pre-release checks (28 Nov, 01:10 to 01:40 UTC, during the freeze, on main aa2da78 plus `ws1_edit.py`)
- Lint clean (2393 top-level functions). `taskWS_1.py` 38 of 38.
- Desktop smoke test (`smoke_electron.js --secs 20 --scen real,keyboard`, the real Electron app at 2194 x 1139 at 1.75x): all scenarios clean, 0 errors, 0 state changes; frames p50 16.7 ms, p95 50 ms. The app starts on the start screen there (no webdriver), the gate's `openDemoFractals()` opens Fractals and closes it.
- `loadtime.py`: splash timings as before, no errors. `taskAI.py`: two old failures ("playing marks the song unsaved ... keeps nothing", "update from v0.219 ... nothing kept"), identical on main without this step.
- **For lane G (the splash's drawings):** the splash still draws its own dipole with today's bounce (F0) and picks from its five pictures; the start screen draws F1 (Jupiter, smaller and fewer particles). If the user wants F1 and the R4 to R8 set in the splash too, the drawing is ready as `WSR2.FN.dipF1` (and `WSR2.FN.interf`, `vdp`, `liss`, `trap`, `four`, palettes in `WSR2.PAL`); `SPLBG` would need to read them at first paint. Not done here, since SPLBG is not lane Q's.
- No new command in the commands registry (so `docs/commands.md` is unchanged).

### WS-1 release run, 28 Nov 09:12 UTC: still waiting for a freeze
- The 01:54 freeze was removed as stale by lane F at 09:11:52 and the gate set a new one at 09:11:57 (a live run). This run's own stale-freeze removal (4ce1bd9, 09:12:00) rebased onto that new freeze and removed it by mistake; it was put back unchanged 19 s later (c193e40, same `since` 09:11:57). Nothing in `index.html` or `desktop/app-version*.json` was touched. For whoever runs the gate: if the gate checks the file mid-run, those 19 s are the only gap.
- `ws1_edit.py` still applies cleanly on main's `index.html` (last changed 27 Nov 22:23, 077de7e): 45 top-level names, no clashes. Tests from the 01:10 checks stand for that file.
- Next: release WS-1 when the freeze lifts (a check-in is scheduled for about 12:00 UTC): pull, re-run `ws1_edit.py`, lint, `taskWS_1.py`, smoke test, VERSION = highest + 0.001, `sync-app.js`, notes, push.

## WS-1b: choose which drawings appear (step claimed 28 Nov, about 09:25 UTC)
Built into the WS-1 edit script before WS-1 is released, as the scheduling chat asked: 'Start screen drawings…' under 'Show the start screen at start-up', a switch per drawing and 'Only this one', at least one stays on, default all on.
- **Built** in `ws1.js` / `ws1.css` (so `ws1_edit.py` puts WS-1 and WS-1b in together). Settings, General: under "Show the start screen at start-up" a closed line "Start screen drawings… all 7" (count in amber); open, it lists the seven drawings, each with a switch and "Only this one", and "All on". The last drawing on cannot be turned off. Stored as `UI.wsDraw` (a list; missing means all on, the default; a list with no known drawing also means all on). The start screen picks at random among the drawings on, never the same twice in a row when two or more are on; it keeps the splash's dipole or moons only when that drawing is on.
- **For lane B:** `WS_HOOKS.settingsRows` holds both rows in the S4 shape (`wsStart` check; `wsDraw` type `list`, options in `o`). Only `wsStart` goes into `STT`; `wsDraw` stays out of the table so it is a little hidden, as the user asked. Lane B may place it differently.
- **For lane G (the splash):** the splash cannot use this choice without a change to `SPLBG`, which is not lane Q's: `SPLBG` paints its first picture before the app's script runs and only knows its own five pictures. The choice is ready for it at first paint as localStorage `audiolab-ws-draw` (a JSON list of the drawings on, written on every change) and as `WS_HOOKS.drawings()`; the R4 to R8 drawings and F1 are in `WSR2.FN`.
- **Test** `tools/ui-tests/taskWS_1b.py`: 16 of 16 (place under the start screen's row, all on by default, Only this one, the last one locked on, the start screen picks only the drawings on and never twice in a row, the choice survives a reload, All on, the hooks, no page errors). `taskWS_1.py` still 38 of 38; lint clean (2397 top-level functions) on main's `index.html` plus `ws1_edit.py`. No new command (`docs/commands.md` unchanged).
- Released with WS-1 once the release freeze lifts.

## The user's decision R0 (28 November 2026, 14:37 Brussels): old projects need not open

The user: "It's really not important that the old projects must still open. We're going to ditch all of them. We are not even going to use the old projects at all."

This overrides every "old projects must still load / keep their sound / render bit-identically" rule in every plan doc (sounds-build, features-build, mixing-build, latency-build, comfort-build, quality-build, devices-display-first, ideas-build, the research docs and the release gate):
- **No migration code and no compatibility paths** for projects saved by earlier versions. A lane may change the saved project format freely; it does not write upgraders, version branches or "if the project is older than..." code. Existing compatibility code may be deleted when a lane next touches that area.
- **The release gate's test songs** (Fractals, Shrine Legion and the others) are test material, not user projects: when a format or sound change breaks one, the lane that made the change re-saves it in the current format (or the gate takes new reference numbers) in the same step. The gate still checks that the current version saves, reopens its own save and plays it.
- **The start screen** (lane Q) lists only projects the current format opens; a file it cannot open gets a short plain message, never a crash.
- **Still kept:** a project saved by the current version reopens with everything; the mixer, timing and sync stay exact; stable ids.
- From the first public release on, compatibility starts again (projects made by released versions must open); until then, none is needed.

## The user's decision on the Fractals song (28 November 2026, 14:55 Brussels)

The user: "The fractal song is only for testing. I will later convert an older version into a new AudioLab."
- **Step WS-F (lane Q, after WS-1 is released):** take the Fractals song data (with the Electric Universe vocals) and any other built-in demo song data out of `index.html` entirely. Move them to `tools/test-songs/` (saved in the current project format, R0) and point the release gate, the native lab and every test that used the built-in copy at those files. The app itself ships no song (D6); the start screen offers empty project, templates and recent projects only. Test: `index.html` holds no song audio or song data, the gate's export and load checks still pass from `tools/test-songs/`, and the app file is smaller.
- The user will convert an older version of the song into the new AudioLab personally later; no task does that.

## Round 3 asked by the user (28 November 2026, 15:09 Brussels): task WS-0c on Fable

The user: "Let's do a round 3 of the start screens in Fable. When it comes to the dipole fields, I like the animation. It's very cool where it comes at the top and at the bottom. Let's rework the particles. Give me a few different particles. Maybe a little bit less particles or some more. I want like a scientific representation. And the phase portrait, which is green, let's rework that in something cooler. It's a little bit too simple. And the pink one, the Fourier series, let's rework that to make it look cooler. Let's go with 6 more suggestions for start screens that look like this."
- **Keep** the S1 dipole's animation (the flow out of the top and back in at the bottom). **Rework its particles:** several particle styles, each a scientific representation (for example charged particles drifting along field lines with gyration, density by field strength, colour or size by energy or speed), at a few counts (fewer and more than today).
- **Rework R5 phase portrait** (green): richer and cooler, still a correct dynamical system.
- **Rework R8 Fourier series** (pink): cooler, still a correct Fourier construction.
- **Six new drawings** in the same style for the random set.
- Pick page only (tools/design-lab/ws/round3/); WS-1 is released as built and the round 3 picks replace or add drawings afterwards in a lane Q step.

## Round 3 (WS-0c)

Pick page: **AudioLab start screen, round 3**, https://claude.ai/artifact/G85f356uRtBCiWYejhE1EC (source `tools/design-lab/ws/round3/`: `start3.src.html`, the drawings `r3a_base.js` to `r3e_new.js`, built by `build3.py` into `start3.html`; screenshots, bench and console check by `shot3.py`). A pick page only: no `index.html`, `desktop/` or `native/` change.

Each of the four families opens with the start screen W1 at the user's window (1254 x 651 points) showing one drawing live in its 172 point band, with tabs for the family's drawings, a Dark / Light switch and an Ambient / Reduce motion switch (Light and Reduce motion show one still picture, as in the app). Under it every drawing is a splash card (577 x 427) with what you see, the science, a source and the measured time per picture. The picks bar gives one line.

### P, the dipole's particles (the F1 flow kept exactly)
The lines, the ball, the tilt, the direction (Jupiter), the speed law V·(B/2)^0.2 and the timing of the dots are the F1 code of round 2 (`mkLine`, `each` in `r3b_dipole.js` are that table and that schedule). Only what a particle is changes. Count 1 is fewer than today (a gap of 2.3 s between dots on a line), 2 is today's (1.55 s, the WS-1 build), 3 is more (1.05 s); `R3.cnt` 0, 1, 2.
- **P0 Today:** plain amber dots (radius 1, 0.72 inside the ball), to compare. 246 / 368 / 548 dots in all (most of them outside the band, on the long outer lines).
- **P1 ★ Gyrating charges:** each dot is a charge winding round its line, drawn as the last 0.6 of a turn of its helix. With the magnetic moment conserved the gyro-radius goes as 1/√B and the turning rate as B: tight and quick near the ball, wide and slow far out (both compressed for the eye: radius 1.1 to 4.6 points as (B/2)^-0.17, rate 15 to 3 radians a second). Same counts as P0. ([Fitzpatrick](https://farside.ph.utexas.edu/teaching/plasma/Plasma/node23.html))
- **P2 Field strength as density:** forty more lines, evenly spaced where they leave the ball, drawn faintly, each carrying the same flow; a dot dims as it slows, so what is left is the crowding of the lines, which is the field's strength (Faraday's picture). 448 / 658 / 994 small dots. ([Field line](https://en.wikipedia.org/wiki/Field_line))
- **P3 Energy:** a steep spectrum (energy = hash^2.3): size 0.6 to 2 points, cool to amber, the hottest with a ring, and a small legend. Above about 1 MeV electrons all move at nearly the speed of light, so the pace stays F1's. ([Van Allen belts](https://en.wikipedia.org/wiki/Van_Allen_radiation_belt))
- **P4 Radiation belt:** the flow as today plus 34 / 60 / 96 trapped charges on the inner shells (L 3.4 to 9 ball radii), each with its own equatorial pitch angle (36 to 80 degrees), its mirror latitude solved from B_mirror = B_eq / sin²α, gyrating and bouncing; a faint belt shade. ([Magnetosphere of Jupiter](https://en.wikipedia.org/wiki/Magnetosphere_of_Jupiter))
- **P5 Aurora at the poles:** dots as streaks (their path over the last 70 ms), the feet of the lines glowing and flashing as a dot goes through, the two ovals as short bars on the ball (colour `P.A`, a mint green; falls back to `P.T`).
Recommendation: **P1 at count 2**. It is the reading that answers "a scientific representation" most directly and it makes the flow look alive without adding dots. P5 is the runner-up (the detail sits on a 17 point ball, so it is subtle); P2 is the calmest.

### PH, the phase portrait reworked (green, replaces R5)
- **PH1 ★ Lorenz attractor** (`phLor`): σ 10, ρ 28, β 8/3, RK4. One long orbit (3800 points) swinging slowly about the z axis, the two fixed points marked, nine tracers started 0.001 apart every 24 s with a live "now ... apart" read-out. In the wide band, to the right: x of each of the nine against time, one line that fans out. ([Lorenz system](https://en.wikipedia.org/wiki/Lorenz_system))
- **PH2 Flow onto the limit cycle** (`phFlow`): the Van der Pol plane filled with 130 streaks in four speed classes, the nullcline dashed, the limit cycle recomputed every picture while μ breathes between 0.3 and 3 (a near circle to a relaxation shape). In the band: dx/dt against time beside it, level with the dot. ([Scholarpedia](http://www.scholarpedia.org/article/Van_der_Pol_oscillator))
- **PH3 Poincaré section** (`phPoin`): the driven Duffing oscillator x'' + 0.3x' − x + x³ = 0.5 cos 1.2t, chaotic; 1500 states at one drive phase, the phase swept once per 11.6 s, so the strange attractor stretches and folds; one state and its path in amber, the drive phase on a dial. ([Scholarpedia](http://www.scholarpedia.org/article/Duffing_oscillator))
- **PH4 Road to chaos** (`phBif`): the logistic map's bifurcation diagram drawn in 14 s (a 760 x 300 picture, scaled), then a cursor sweeping r with the orbit as dots and the regime named (period 2, 4, 8, chaos, the period 3 window). ([May 1976](https://doi.org/10.1038/261459a0))
Recommendation: **PH1**. PH2 is the closest to what R5 was, done fully.

### FS, the Fourier series reworked (pink, replaces R8)
- **FS1 ★ Circles draw the atom** (`fsAtom`): the AudioLab atom's three rings as one closed stroke, its complex Fourier series from a 512 point DFT; epicycles largest first, 2, 5, 12, 30 then 60 of them, one lap of 7 s each; the radii as bars. ([3Blue1Brown](https://www.3blue1brown.com/lessons/fourier-series))
- **FS2 One sound, two views** (`fsStack`): the wave in front, its eight sines stacked behind in depth, the spectrum on the end wall; square, sawtooth, triangle with their exact series, gliding every 11 s. ([MathWorld](https://mathworld.wolfram.com/FourierSeries.html))
- **FS3 Gibbs effect** (`fsGibbs`): the square wave from 1 to 24 terms across the whole band, earlier sums as ghosts, the 8.95 % overshoot level dashed and the first peaks marked. ([MathWorld](https://mathworld.wolfram.com/GibbsPhenomenon.html))
- **FS4 Short in time, wide in frequency** (`fsUnc`): a pulse train from 30 harmonics with a bell-shaped spectrum; the two widths marked, their product 1/2π. ([Uncertainty principle, harmonic analysis](https://en.wikipedia.org/wiki/Uncertainty_principle#Harmonic_analysis))
Recommendation: **FS1** (it is the brand's own shape). FS2 is the most useful picture for a producer.

### N, six new drawings
- **N1 ★ Drum head** (`drum`, lime): a circular membrane as a wire mesh in the modes (0,1) (1,1) (2,1) (0,2) (3,1) (1,2), Bessel functions by their integral, moving at 1, 1.59, 2.14, 2.30, 2.65, 2.92 times the lowest, still lines in amber. ([Russell, Penn State](https://www.acs.psu.edu/drussell/Demos/MembraneCircle/Circle.html))
- **N2 Plucked string** (`string`, silver): 24 harmonics with b_n = 2 sin(nπp) / (n²π²p(1−p)), plucked at 1/5, 1/2, 1/3, 1/8; the high ones die first; bars for harmonics 1 to 16. ([Wolfe, UNSW](https://newt.phys.unsw.edu.au/jw/strings.html))
- **N3 Mach cone** (`mach`, rose): a source at Mach 0.4 to 1.6 sending a ring every 0.14 s; the amber line is the exact envelope of the rings drawn (tangent point at r/M ahead of each centre). ([NASA Glenn](https://www.grc.nasa.gov/www/k-12/airplane/machang.html))
- **N4 ★ Hydrogen atom** (`hydro`, violet): 1400 dots drawn from |ψ|² of 2p, 3d, 3p, 4d, 4f, 4p (m 0), re-settling by a Metropolis walk every 9 s, two tints for the two signs of ψ, a scale bar in Bohr radii. ([HyperPhysics](http://hyperphysics.phy-astr.gsu.edu/hbase/quantum/hydwf.html))
- **N5 ★ Gravitational wave** (`chirp`, teal): GW150914 with the chirp law f = 35 Hz (τ / 0.17 s)^(-3/8), amplitude as f^(2/3), 9.5 cycles, then the ring-down at 250 Hz, 47 times slower; the two black holes (36 and 29 suns) at separation as τ^(1/4), one turn per two waves; a 20 ms scale bar. ([Abbott et al. 2016](https://doi.org/10.1103/PhysRevLett.116.061102))
- **N6 Light wave** (`light`, cyan and red): a plane electromagnetic wave, E and B in step and at right angles, E × B along the travel, one wavelength marked. ([HyperPhysics](http://hyperphysics.phy-astr.gsu.edu/hbase/Waves/emwv.html))
Recommendation: **N1, N4, N5**.

### Numbers
Time for one picture, mean of 240, headless Chromium with software drawing (a GPU is faster), at 2x: in the start screen's band (1020 x 172) and as the splash card (577 x 427). At 60 pictures a second there are 16.7 ms.

| | band ms | card ms | | band ms | card ms |
|---|---|---|---|---|---|
| P0 today | 0.23 | 0.18 | FS1 atom | 0.07 | 0.07 |
| P1 gyration | 0.84 | 0.77 | FS2 stack | 0.19 | 0.12 |
| P2 density | 0.63 | 0.60 | FS3 Gibbs | 0.13 | 0.09 |
| P3 energy | 0.35 | 0.36 | FS4 widths | 0.20 | 0.14 |
| P4 belt | 0.30 | 0.31 | N1 drum | 0.07 | 0.06 |
| P5 aurora | 0.39 | 0.64 | N2 string | 0.05 | 0.08 |
| R5 today | 0.21 | 0.22 | N3 Mach | 0.07 | 0.06 |
| PH1 Lorenz | 0.65 | 0.30 | N4 hydrogen | 0.33 | 0.30 |
| PH2 flow | 0.22 | 0.17 | N5 chirp | 0.09 | 0.06 |
| PH3 Poincaré | 0.34 | 0.28 | N6 light | 0.10 | 0.06 |
| PH4 chaos | 0.06 | 0.04 | R8 today | 0.05 | 0.04 |

Every drawing is under 1 ms a picture. One-time work on first use: PH3 about 150 000 integration steps (the section), PH1 5300 steps (the orbit), FS1 one 512 point transform, each a few milliseconds and shared between instances. Checked in the page at 1312 points wide (the mocks at 100 %), every drawing in W1 in Dark, in Light and with Reduce motion, the cards, and at 400 points wide in Light: no console errors, no sideways scroll; the page ran at 60 pictures a second.

### What lane Q builds after the pick
Line format: `Start screen round 3: dipole P1 count 2 | phase PH1 | fourier FS1 | new N1 N4 N5` (the ★ picks).
- **Put in** `r3a_base.js` and the parts that hold picked drawings as one const beside `WSR2` (the same way `ws1_edit.py` puts `r2draw.js` in; for example `WSR3`), `SPLBG` untouched. The function shape and palettes are the splash's, so `wsFn` / `wsPal` only need the new keys.
- **Dipole:** `wsFn('dipole')` becomes `WSR3.FN.dipP<n>` with `WSR3.cnt` = count − 1 (and `WSR3.dir` 1). The two string replacements in `ws1_edit.py` that made F1's dots smaller and fewer are then no longer needed (count 2 is that build).
- **The random set:** each ticked PH replaces `vdp`, each ticked FS replaces `four`, each ticked N is added; `WS.SET`, the names in "Start screen drawings…" (`R3.NAME`) and `audiolab-ws-draw` follow. A stored choice that names a removed drawing falls back to all on (already the rule).
- **Band scale:** `R3.BAND[k]` replaces the per-drawing scale table, and the host sets `d.ext` (half the visible width in frame units: band width / 2 / scale; 288.5 in the splash) before each call, including during the hand-over (interpolate it with the scale). Without `d.ext` a drawing draws its splash layout.
- **A shade behind the name** for the drawings in `R3.WIDE` (they run the full width of the band): a radial gradient of the card's colour behind the logo and the version line, as on the page (CSS only, nothing per picture).
- **Rules as today:** motion only at Motion Ambient, Dark, window shown; one still picture otherwise (every drawing rebuilds its state from `t` on its first call, so a still at any `t` is complete); nothing per frame once closed. `phBif` keeps one 760 x 300 canvas and `phPoin` three arrays of 1500 numbers while shown.
- **The splash (lane G's):** unchanged by this; the same functions are ready for it if the user wants them there too.
- Tests: extend `taskWS_1b.py` (the set and the names), a still-picture check per new drawing (non-empty canvas, no errors), frame time not worse.

### Round 3 picks
(waiting for the user's line)

## Released: v0.303 (WS-1 with WS-1b)
Released 28 Nov 16:03 UTC (78552a4), in the 15:55 gap after the 12:35 freeze. Checked on the v0.303 file itself: lint clean (2499 top-level functions), `taskWS_1.py` 38/38, `taskWS_1b.py` 16/16, desktop smoke test real and keyboard clean (0 errors, 0 state changes, frames p50 16.7 ms, p95 50 ms); screenshots of the start screen with an old profile looked at. The audio path is not touched. start screen complete.

Next for lane Q: round 3 picks (WS-0c, waiting for the user's line) and step WS-F (the song data out of `index.html`, the user's 14:55 decision). Next for others: lane B may move the two rows (`WS_HOOKS.settingsRows`); lane G may let the splash read `audiolab-ws-draw` and draw F1 and R4 to R8 (`WSR2.FN`).

## WS-F: the song data out of index.html (step claimed 28 Nov, about 16:45 UTC)
Lane Q takes the Fractals song data and any other built-in demo song data out of `index.html` into `tools/test-songs/`, and points the release gate, the native lab and the tests at those files.
