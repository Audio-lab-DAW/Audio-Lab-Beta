# AudioLab Pro science look, round 2 (task SC2, 27 November 2026)

Pick page: **AudioLab science look, round 2**, https://claude.ai/artifact/DhZ8v8FWJz6UyqiorjDLoM

A pick page only: **nothing in index.html or desktop/ was changed, no version bump.** It follows round 1 (`docs/science-look.md`, task D6), the About page (`docs/about-science-backgrounds.md`, task SR6) and the philosophy in `docs/glass-engine-plan.md` section 1: scientific, "smart and sciencey, clear, intuitive, snappy", snappiness and low CPU first, today's colours stay.

The user's words for this round: "I want to use these designs in other places of the DAW. Give me suggestions based on design where I could use these in the background to make the DAW look more attractive and scientific and cool in the subtle way. And I really like all the measurement details... the orbit loader... let's use all of that, and you can come back with more stuff like this."

Already decided on 27 November and not asked again: splash = random among S2, S5, S1, S7 and less often S6, without centre logo and edge text (task SP1); About = the Earth with the Van Allen belts (round 2 in task SR7), B2 and B3 also liked; measurement details M1, M2, M3 all wanted (task MD1).

How to answer: on the page set each W to Off, Faint or Normal, click the X details wanted, pick one Y, press "Copy my picks" and paste the line. It looks like `My picks: W1 normal, W2 faint, W3 off | X1 X3 X4 | Y1`. "Take all ★" fills in the recommendations: `W1 normal, W2 faint, W5 normal, W6 normal, W8 normal, W10 normal, W12 faint, W14 faint | X1 X3 X4 X6 X7 X8 X10 | Y1`.

## The rules every place follows

1. **Nothing moves where you work.** On working surfaces (mixer, Settings, lanes) the drawing is a still picture, drawn once. Motion only on empty states and while waiting.
2. **Never behind dense text or meters.** Drawings sit in empty areas, margins and headers; boxes with text or meters keep a solid backing.
3. **The drawing means something.** Orbits for timing and tempo, field lines for routing and sidechain, harmonics and Lissajous figures for pitch and tuning, the spectrogram for audio.
4. **Faint** = lines at under half strength (0.45 on the page), no labels. **Normal** = full strength plus the small amber mono labels, which must carry true values.
5. **Cheap.** A moving drawing is a few dozen 1 px lines at 30 pictures a second, only while visible; it stops with its window, in the background freeze and with "reduce motion". No blur, no shadows on the canvas.

## W. Where the drawings can live

Each is shown on the page as a small live mock-up of the real surface in v0.222 (the app was looked at in a headless browser first: arrangement and devices, mixer, Settings, Updates, visualizer). ★ = recommended to build first; every place has a recommended strength.

| # | Place | Drawing | Motion | Strength | Why this drawing | Cost |
|---|---|---|---|---|---|---|
| **W1 ★** | Empty arrangement of a new project | Orbit chart (S7): three rings, tick ring, dashed cross; inner body once per 4 bars, outer once per 16, at the project tempo | Slow; **fades out when the first clip lands** and does not return in that project | normal | Orbits are timing; the one place with nothing else to look at | About 80 lines a picture while the project is empty, nothing afterwards |
| **W2 ★** | Empty devices panel | Field lines (S1, B3) from the input side to the output side, all passing through "Add effect" | Slow; gone with the first device | faint | Field lines are routing: where the signal would flow | 12 curves and 12 dots a picture while the chain is empty |
| W3 | Mixer, master strip | Orbit corner (B2): tick rings from the lower corner, behind the strip only; LUFS box, fader, meter keep solid backing | Still | faint | The master is where everything ends up | Drawn once into the strip background |
| W4 | Settings window header | Orbit corner (B2) from the top right, visible in the header and between cards; at Normal a tick scale under the header and a count of settings | Still | faint | Settings is where things are measured and set | Drawn once when the window opens |
| **W5 ★** | Update window | Moons in resonance (S2) in the header; the download is the orbit loader that fills (M2) | Only while checking or downloading | normal | Same family as the splash: start-up and update feel like one piece | 3 ellipses and one arc a picture while working |
| **W6 ★** | Export and bounce window | Spectrogram (S6) of what has been rendered so far, growing left to right, amber line at the front; at Normal Hz ticks, speed, true peak | Grows with the work | normal | The spectrogram is audio, and here it is real data | One column per rendered block on a small picture (240 x 48), scaled; uses data the export already has |
| W7 | Stem splitter while it works | Spectrogram, one band per stem row; orbit loader in the title | Grows with the work | normal | Shows what the tool does: takes one sound apart | Four small strips, one column each per step |
| **W8 ★** | Audio to MIDI while it listens | String harmonics (B4) and the harmonic comb; an amber bracket measures the spacing = the pitch; the note drops into a strip | While listening | normal | Harmonics are pitch; the picture explains the result | 3 curves and about 12 lines a picture |
| W9 | Background freeze state | Amber corner calibration marks around the window and a small stamp "HOLD · IN BACKGROUND" with a dashed orbit whose body stands still | Still | faint | A frozen picture should look deliberate, not like a hang | Drawn once on freezing, zero while frozen |
| **W10 ★** | Project list (start page) | Orbit chart (S7): one ring per recent project, each body turning at that project's tempo | Slow | normal | Orbits are tempo; the list is a waiting state | 5 rings and a tick ring a picture while open |
| W11 | Empty lanes and empty clips | Lane: one centre line with beat ticks. Empty audio clip: dashed zero line with a +1 / 0 / −1 scale | Still | faint | Empty space reads as "ready to measure"; ticks help aim a drop | A few more lines in the normal grid drawing, no timer |
| **W12 ★** | Visualizer when nothing plays | Lissajous fifth (S4) in the spectrogram pane, harmonics of A (55 Hz × n) marked in the spectrum pane, zero line in the waveform; **all gone the instant audio starts** | Slow drift while silent | faint | Lissajous and harmonics are tuning; they also show the axes | One curve of 240 points a picture, only while silent and open |
| W13 | Drag and drop overlay | Field lines between the pointer and the landing place, with landing position and length | Only during the drag | normal | Field lines are attraction and routing | 7 curves a picture for the seconds a drag lasts |
| **W14 ★** | Light mode | A rule: every drawing above becomes one still picture with thinner lines; Off = no drawings in Light mode | Still | faint | The look stays, the cost goes to zero | None after the first picture |

Notes on the places:
- W10: the app has no separate start page today (projects open through the browser panel and the saved list); W10 is a proposal for that list or a future start page.
- W9: the stamp must be drawn in the same step that freezes drawing, and removed on return, so it costs nothing while frozen.
- W3 and W4 must be checked against the glass engine: the still drawing belongs to the panel's own background, under the glass content, not in the shared backdrop.

Draw time of the mock-ups on the cloud machine (software renderer, whole mock-up including the simplified app around the drawing, so an upper bound for the drawing itself): W1, W2, W12, W14 about 0.10 to 0.15 ms a picture; W3, W9, W11, W13 0.20 to 0.26 ms; the dialog mock-ups (W4 to W8, W10) 0.76 to 1.12 ms, almost all of it the mock song redrawn behind the dialog, which the app does not do. Not measured in the app.

## X. More measurement details

In the spirit of M1 (read-outs with units), M2 (orbit loader) and M3 (caliper). Each is live on the page.

| # | Detail | What it is |
|---|---|---|
| **X1 ★** | Tick scales with an index mark | Every fader and slider gets a fine scale with numbers and a small amber pointer that carries the exact value while it moves. |
| X2 | Knob rings with ticks | A tick ring around each knob, longer mark every fifth step, an amber dot riding outside the ring. |
| **X3 ★** | Crosshair with a read-out | In the arrangement the pointer casts two dashed lines to the ruler and the track list; a small box gives bar.beat.sixteenth, time and track. On a key or always, to be decided when built. |
| **X4 ★** | Ruler that reveals on zoom | Bars only when zoomed out; beat ticks fade in, then sixteenths, each level shorter. A scale bar says how long a bar is on screen. |
| X5 | Phase dot and correlation | The stereo display's Lissajous trace gets a bright dot at the newest point; the correlation meter gets a −1 to +1 scale and the phase angle in degrees. Must respect "the stereo field displays stay as they are": added marks only. |
| **X6 ★** | Change shown while dragging | While any control is dragged: the change next to the value (Δ +1.5 dB), a dashed mark at the start position, for levels the gain factor (× 1.189). |
| **X7 ★** | Orbit for LFO phase | Each tempo-synced LFO gets a tiny orbit: once round per cycle, quarter marks, phase as a number, real rate in Hz (1/4 at 145 BPM = 2.417 Hz). |
| **X8 ★** | Frequency with its note | Wherever a frequency shows (EQ, filter, oscillator, sidechain filter): nearest note and offset in cents, with a small tuning mark. |
| X9 | Proper units and prefixes | One rule for every number: three figures, SI prefixes (µ, m, k, M), a real minus sign, a thin space before the unit. 12400 Hz → 12.40 kHz, 0.0005 s → 500.0 µs. |
| **X10 ★** | Signal path line | One line in the status area that follows the selected track: input, track, group, master, converter, with sample rate, bit depth and latency. |
| X11 | Scale bars on waveforms | Like the bar on a microscope picture: "100 ms", "6 dB", "1 decade", changing with the zoom. |
| X12 | Grid coordinates on demand | Hold a key: every crossing of a bar line and a track line gets a tiny cross and its coordinate. Release: gone. |
| X13 | Calibration marks on panels | Corner brackets, centre crosses, edge ticks and a tiny panel label on the main panels. Still and very quiet. Same motif as W9. |
| X14 | Sunrise progress arc | For longer jobs: a sun rising along an arc over a horizon line with a tick scale, large and at 28 px. A partner to the orbit loader. |
| X15 | Settling read-out with ± | A measured value (loudness, tempo detection, pitch) shows how sure it is: a ± that shrinks as more audio is measured and turns green at "settled". |

Why the seven stars: X1, X4, X6 and X8 change how every control and ruler reads and reuse one piece of code each; X3 and X10 answer "where am I" and "where does this go" at a glance; X7 carries the orbit motif into daily work. X9 is worth doing together with MD1 (M1), since both touch number formatting. All X details cost nothing at rest: they draw only when a value changes, except X7 (one small arc per visible LFO while playing).

## Y. About: the random set

One choice. The set is the Earth with the Van Allen belts (whichever Earth versions come out of SR7 share the Earth slot), B2 orbit corner and B3 field arcs.

| # | Rule | What happens |
|---|---|---|
| **Y1 ★** | Earth most often | Earth 3 times in 5, orbit corner 1 in 5, field arcs 1 in 5, chosen each time About opens. |
| Y2 | Equal thirds, no repeats | The three are equally likely; the one just seen is not shown again straight away. |
| Y3 | Earth plus a second layer | Earth always; half the time alone, a quarter with the orbit rings behind it, a quarter with the field arcs. |
| Y4 | One per day | Follows the date, the same all day; Earth on most days. |

Why Y1: Earth is the picture the user chose, so it should be what About usually looks like; the other two keep it fresh without a rule to explain. Y3 is the choice if Earth should never be missing.

## How the page is kept light

One canvas per mock-up (33 in all), one shared timer at 30 pictures a second, a mock-up runs only while it is on screen and the page is visible, device pixel ratio capped at 2, no blur or shadows. One spectrogram picture (240 x 48) is built once and shared by W6, W7 and W12. The still places (W3, W4, W11, X13) are drawn once. With "reduce motion" on, everything stands still. Checked in a headless browser at 1280 px (dark) and 400 px (light): no errors, no sideways scroll.

## Implementation order (each an index.html task, one at a time, after the picks)

Shared base first, then the cheapest and most visible, working surfaces last. SP1 (splash), SR7 (About) and MD1 (M1 to M3) are separate tasks already running or queued; these come after them and reuse their code.

1. **SC-A, shared drawing module.** One small module with the drawings as functions (orbit chart, orbit corner, field lines, Lissajous, harmonics, spectrogram column) taking strength and a still flag, one shared 30 fps timer that stops off screen, in the background freeze, in Light mode (W14) and with "reduce motion". A hidden setting for strength per place. No visible change yet. Take what SP1 and SR7 already built.
2. **SC-B, About random set (Y)**, on top of SR7.
3. **SC-C, empty states:** W1 empty arrangement, W2 empty devices, W11 empty lanes and clips.
4. **SC-D, waiting windows:** W5 update, W6 export and bounce, W7 stem splitter, W8 audio to MIDI (all use the orbit loader from MD1).
5. **SC-E, idle and overlay:** W12 visualizer idle, W13 drag overlay, W9 background freeze stamp.
6. **SC-F, still backgrounds on working surfaces:** W3 mixer master, W4 Settings header; check against the glass engine.
7. **SC-G, project list:** W10 (needs a decision on where the list lives).
8. **SC-H, number formatting:** X9 units and prefixes, X8 frequency with note (one formatter for the whole app, with MD1).
9. **SC-I, scales:** X1 fader and slider scales, X2 knob rings, X6 change while dragging.
10. **SC-J, arrangement:** X4 ruler levels, X3 crosshair, X12 coordinates on demand, X11 scale bars.
11. **SC-K, status and meters:** X10 signal path line, X5 phase dot and correlation scale, X15 settling read-out, X7 LFO orbit.
12. **SC-L, motifs:** X13 calibration marks, X14 sunrise arc.

Each task: only the picked items, the usual release routine and a headless test with screenshots, and a frame-time check that the place costs nothing when it is not shown.
