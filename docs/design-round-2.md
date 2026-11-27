# AudioLab Pro design round 2: arrangement, piano roll, browser, transport (task DR2, 27 November 2026)

Pick page: **AudioLab design round 2: arrangement, piano roll, browser, transport**, https://claude.ai/artifact/VW7jsEAkc6wrxWmVvyTYvX

A pick page only: **nothing in index.html or desktop/ was changed, no version bump.** Reference release: v0.228.

The user's choices for this round (27 November, from a short question list): areas = arrangement and clips, piano roll and MIDI, browser and presets, transport and top bar (all four); strength = "Subtle, as now" (fine lines and measurement details, nothing that distracts while working); format = pick pages as before (research, then a page with numbered live options and a picks bar to paste).

Built on: the philosophy in `docs/glass-engine-plan.md` section 1 ("smart and sciencey, clear, intuitive, snappy"; snappiness and low CPU first), the round 1 picks in `docs/design-language-research.md` (A0 B0 C1 D3 E0 F4 G2 H0: today's colours, buttons and icons; Inter 11/12/13/15 with equal-width digits; full glass), `docs/science-look.md` and `docs/science-look-round-2.md` with the user's picks (`claude/audiolab-science-picks.md`), `docs/devices-display-first.md`, and the released work in the backlog log (SP1 splash v0.224, AB1 About v0.225, D3 type scale v0.226, GS1 to GS3 glass v0.223, v0.227, v0.228).

**Not repeated here, because it is decided or queued elsewhere:** MD1 (M1 read-outs with units, M2 orbit loader, M3 caliper while dragging), and from science round 2 X1, X2, X4 (ruler that reveals on zoom), X5, X6 (change while dragging), X7, X8 (frequency with its note), X9 (units and prefixes), X10 (signal path line), X11 (scale bars), X12, X14, X15 and the W places. X3 (crosshair) and X13 (calibration marks) were not picked, so no option here uses them. Where an option touches the same spot (the ruler, the status line, frequencies on keys), the page says which earlier pick it builds on.

## 1. How to answer

On the page: pick one look per part (A, P, B, T, or 0 for today), optionally one detail per row to override single pieces of that look, then **Copy my picks** and paste the line. It looks like:

`My picks: A3 P3 B3 T2 | AW1 PK2 TM2`

The part before `|` is the four looks; after it, the details that should differ from the look. "Take all ★" gives `My picks: A3 P3 B3 T2`. A switch at the top shows every mock-up in Dark with glass or in Light mode (no glass).

## 2. Research summary

About 50 pages were read on 27 November 2026 by a research helper through a web fetch tool that returns a summary of each page, so details are as that tool reported them. Full list in section 7.

**Arrangement and clips**
- Grids change with the zoom: Bitwig's adaptive beat grid and ruler labels (BARs, BARs.BEATs, BARs.BEATs.TICKs), Live 12's adaptive or fixed grid with the current grid value printed by the ruler, triplets on a key.
- Clip anatomy: in Live 12 only the title band drags a clip; Bitwig marks loop repeats inside a clip (dashed at the first repeat, dotted after), puts fade handles on the top edge, onsets as small triangles on the top edge, and draws gain on the waveform with labelled centre lines (0 dB, 0.00 st).
- Waveforms by band: Serato colours lows red, mids green, highs blue; Rekordbox's RGB view is the most detailed but "can be overwhelming", its 3-band view (blue lows, amber mids, white highs) is the calm one that makes kicks easy to find.
- Colour noise: Live 12.4 tints the borders between clips from their neighbours to stop "colour strobing"; Studio One 7 made selection boxes denser to be "easier to see in a large project"; Bitwig 6 added a darker grey and gentle gradient fills.

**Piano roll and MIDI**
- Velocity: shading of the note colour (Live 12), saturation (Bitwig, clip mode), a line inside the note whose length is the velocity (Logic), cool to warm colours (Logic option), stems with a dot (FL Studio).
- Scale: Live 12 highlights rows in the scale and "the root note is indicated by a prominent highlight", Fold to Scale; Cubase colours notes by scale and chord; Melodyne's Chord Snap greys notes outside the chord; Logic has no scale rows.
- Context: FL Studio draws other channels' notes as grey ghosts, offers grid contrast high/medium/low and shades 4-bar blocks; Live 12 shows a chance triangle only when rows are tall enough; Melodyne draws a pitch curve through each blob.

**Browser and presets**
- Live 12: sidebar (Collections, Library, Places), search with tags (`#tag`), filter groups with a count and Clear, sortable columns, up to three colour labels per item, Preview tab with a scrubbable waveform, preview in tempo from the next bar, arrow keys step and preview, Similar Sounds.
- Studio One: tabs per kind, tree or tiles (bigger drag targets), Favourites and Recent on top, previews matched to the song tempo, audition while the song plays; Studio One 7 "Search With Sound" returns loops in tempo and key.
- Cubase MediaBay: filters by attribute, "same attribute value" search, a previewer. Bitwig: one source for all timeline content.

**Transport and top bar**
- Bitwig: BARs.BEATs.TICKs.% beside MIN:SEC.MS, DSP meter with a graph, loop start and length optional; Bitwig 6 puts the scale in the transport.
- Logic: display modes from beats only to both clocks plus tempo, key, signature, locators, CPU and disk.
- Cubase 14: CPU graphed against the song position, dropouts marked.
- Meters: Sound On Sound calls VU and PPM obsolete and recommends ITU BS.1770 (LUFS, true peak); EBU R128 momentary 400 ms, short-term 3 s, EBU +9 and +18 scales, colour change at ±7 LU, loudness range "unstable" for the first 60 s.

**Readable for hours**
- NN/g's summary of polarity studies: light text on dark is harder to read at small sizes, more so at night; no difference in reported eye strain. A chart-reading study (134 people) found no overall winner. So: dark stays, but nothing that matters goes under 11 px.
- Material's dark theme: text at about 87, 60 and 38 % white; saturated colours "vibrate" on dark grounds, so use lighter tones.
- NASA colour usage: pure blue carries little edge detail and is "barely legible at any size" on black; fine detail should use paler blues. For AudioLab: today's blue (#4c8dff) stays for fills and buttons, never for hairlines or small text.
- Adjustable contrast helps (Renoise: global contrast, four font sizes; Bitwig: one contrast setting).

**Lab instruments and mission control**
- Oscilloscopes: 8 x 10 divisions, minor ticks only on the centre axes, graticule on the trace's plane (Tektronix); grid strength set separately from the trace (Keysight); five minor divisions per major, scale settings outside the grid (Teledyne LeCroy); digital phosphor shows how often a point is hit as brightness.
- NASA Open MCT: only yellow and red limits, stale or paused data in an orange-bordered state, day-of-year time stamps, hash marks dashed at 0.2 opacity, 12 px base font, legends hidden on small plots.

**What this round takes from it:** three line strengths like a graticule; ticks on the ruler and axes rather than more lines over the work; read-outs with true values; velocity and scale shown in the notes and rows rather than extra panels; previews in tempo; loudness in LUFS; blue never as a hairline; amber for "attention" marks only (root, out-of-scale, target), as Open MCT keeps its limit colours rare.

## 3. The options

★ = recommended. 0 is always today (a headless screenshot of v0.228). Every option keeps today's colours, buttons, icons, type scale and glass, and draws only on top of the panels the glass engine already draws (no backdrop-filter anywhere).

### A. Arrangement and clips (mock-ups 600 x 326 at the app's size: 96 px rows, 1 bar = 100 px, header 200 px)

| # | Look | What changes | CPU |
|---|---|---|---|
| A0 | Today | | |
| A1 | Fine graticule | Bar, beat and sixteenth lines at three fixed strengths, ticks on the ruler, the grid value at the ruler's right end, playhead cap. Clips as today. | Same lines as today; 0 extra per frame |
| A2 | Clip anatomy | Title band 12 px with the length in bars and seconds; darker body; loop repeats dashed then dotted; waveform as an outline with a zero line. | One text per visible clip, drawn with the clip |
| **A3 ★** | **Calibrated** | A1 + A2, waveform as a soft peak envelope with a brighter loudness body, playhead flag with position and time (18.2.3 · 0:28.759). | Flag text per playhead move (already redrawn); waveform 2 fills instead of 1, cached per clip |
| A4 | Quiet ink | No title band (name on the body, 2 px colour edge), sixteenths only as ticks at the top of each lane, waveform outline. | Fewer lines than today |
| A5 | Spectral bands | A3 with audio clips in three muted bands (lows, mids, highs). | One band analysis per audio clip when made or changed, then cached |
| A6 | Full lab bench | A3 with lane ticks, plus selection with corner brackets and its size (1 bar 2 beats × 2 tracks · 2.483 s). | As A3; the label redraws only when the selection changes |

Details to mix: **AC** clip body and title band (0 today, 1 thin band, **2 ★** thin band with length and loop marks, 3 no band); **AW** waveform (0 today, 1 outline, **2 ★** peak and loudness body, 3 three bands); **AG** grid and ruler (0 today, 1 three strengths, **2 ★** plus grid value, 3 sixteenths as lane ticks; X4 decides what shows at each zoom); **AP** playhead and selection (0 today, 1 cap, **2 ★** cap and flag, 3 plus selection size; M3 covers dragging).

### P. Piano roll and MIDI (600 x 330: toolbar 30, ruler 16, rows 14 px, keys 56 px, velocity lane 64 px; a lead in A minor over the pad's Am F C G)

| # | Look | What changes | CPU |
|---|---|---|---|
| P0 | Today | | |
| P1 | Fine graticule | Three line strengths, ruler ticks and grid value, a hairline at every C with its name. | 0 extra |
| P2 | Velocity gauge | A gauge line inside each note (length = velocity); velocity lane with a 32/64/96/127 scale and the selected value. | One short line per visible note |
| **P3 ★** | **Scale aware** | Scale rows lift, others sink, a fine amber line on the root (A); a note outside the scale gets a dotted amber ring and says so; crisp note edge with a lit top. | Row colours from the scale once |
| P4 | Harmony strip | P3 + chord names in the ruler, the pad's notes as ghost outlines, names inside wide notes, every C and A with its frequency in Hz on the key, velocity as note strength. | Chords found once per edit; one rectangle per ghost note |
| P5 | Tracker names | Narrow keys with every row named, out-of-scale names grey, root amber; velocity as bars with their value. | One name per visible row |
| P6 | Full lab notes | P4 + a read-out on the note under the pointer (C4 · 261.63 Hz · velocity 104 · 1.3.1 · 1/4). | Read-out only when the pointer moves to another note |

Details: **PN** note shape (0 today, **1 ★** crisp edge and lit top, 2 velocity gauge inside, 3 name inside); **PV** velocity (0 today, **1 ★** stems with scale and value, 2 strength in the note colour, 3 bars with values); **PS** scale and chords (0 today, 1 scale rows, **2 ★** plus root line and out-of-scale ring, 3 plus chord names); **PK** key column (0 today, **1 ★** every C named with an octave hairline, 2 plus Hz at every C and A, 3 narrow keys with every row named; X8 already gives frequencies with notes elsewhere); **PG** ghost notes and read-out (0 none, **1 ★** other tracks as faint outlines, 2 plus the note read-out).

### B. Browser and presets (600 x 360; today's browser is a full-window sheet of large live device cards)

| # | Look | What changes | CPU |
|---|---|---|---|
| B0 | Today | | |
| B1 | Catalogue | Categories with counts, one row per instrument with kind and up to three tag colours, search; today's autoplay bar. | Lowest: no live displays while browsing (today draws every card's display) |
| B2 | Specimen cards | Today's live cards made small, three across, a still picture of each sound, name, kind and preset. | Pictures drawn once when the browser opens |
| **B3 ★** | **Catalogue with a measured preview** | B1 + a preview side: waveform with a scrub line and a time scale, key, tempo and length, presets with arrow keys to step and play, "In tempo, next bar". | One small waveform per preview, drawn once; scrub line moves only while playing |
| B4 | Preset sheet | Inside a device, the preset menu as a sheet: search, tag chips, stars, what a preset changes (Ratio 1.5:1 → 4:1 · +2 more), A/B compare. | Change line worked out on hover from stored values |
| B5 | One search | One field over instruments, presets, effects and samples, grouped results, Enter adds, Space plays. | Searching a few thousand names is under 1 ms |

Details: **BR** result rows (0 today's large card, 1 name and kind, **2 ★** plus tag colours, 3 plus current preset); **BP** preview (0 today's autoplay bar, **1 ★** waveform with scrub line and time scale, 2 spectrum with Hz scale and the main note, 3 spectrogram strip); **BM** preset menu (0 today's grouped list, 1 plus search and tags, **2 ★** plus what the preset changes, 3 plus stars and A/B).

### T. Transport and top bar (1520 x 100 strip: top bar 30 px, transport 40 px, drawn at full width and scaled to the card; the clock runs at 145 BPM)

| # | Look | What changes | CPU |
|---|---|---|---|
| T0 | Today | | |
| T1 | Bays | Three quiet bays (loop and transport, tempo and clock, signal) with hairline separators; 18.2.3.240 and 0:28.759; 145.00 BPM. | 0 extra |
| **T2 ★** | **Dual clock** | One clock, position large and time under it; a tiny orbit beside the tempo, once round per bar; peak meter with a dB scale and hold; CPU as the last 10 seconds. | Orbit and sparkline move with the clock that already redraws; still in Light mode |
| T3 | Mission clock | T+ elapsed time, beat length under the tempo, short-term loudness against a target with a caliper mark, CPU ring, top bar with audio format and work time. | As T2 |
| T4 | On the glass | No black wells: numbers on the glass with a fine tick line under each read-out. | Less than today |
| T5 | Full instrument panel | T1's bays, T2's clock, beat length, momentary and short-term loudness, status line in the top bar. | Two loudness numbers instead of one |

Details: **TT** time display (0 today, 1 compact, **2 ★** dual, 3 mission T+); **TB** tempo (0 today, 1 145.00 BPM, **2 ★** plus the bar orbit, 3 plus beat length); **TM** meter (0 today, **1 ★** peak with scale and hold, 2 short-term loudness with a target, 3 momentary and short-term); **TC** CPU (0 today, **1 ★** last 10 s line, 2 ring); **TS** top bar (0 today, **1 ★** plus audio format and save state, the home for X10's signal path, 2 plus work time); **TL** read-out wells (0 today, 1 bays, 2 on the glass).

## 4. Recommendations and why

**A3, P3, B3, T2.**
- **A3:** the three line strengths make bars findable without counting (the scope graticule rule), the length read-out answers the most common question about a clip, and the peak-plus-loudness waveform shows both transients and body in one picture, at almost no cost. A5's bands are the most "scientific" but add colour where the track colours already speak; better as the detail AW3 for people who want it.
- **P3:** the scale is the piano roll's single most useful context (Live 12, Cubase, Melodyne all show it); the amber root line and out-of-scale ring are the only coloured marks and both mean something. P4 is the next step once chords are detected.
- **B3:** today's browser draws every device's live display while browsing, which is the opposite of "snappy, low CPU". A catalogue with one measured preview keeps the live picture for the one item you look at, adds the preview-in-tempo that Live and Studio One users expect, and arrow-key auditioning.
- **T2:** one clock that reads both musical and real time, a tempo that shows its beat as an orbit (the atom motif, once per bar), and meters with scales. Everything moves only with what already redraws. T3's mission clock is the more playful choice.

## 5. CPU and draw times

Each option's CPU line on the page is an estimate from what it draws compared with today's drawing. Not measured in the app. The page's own draw times (cloud machine, software renderer, a whole mock-up including the simplified app around it, average of 5): arrangement looks 0.30 to 0.58 ms, piano roll 0.10 to 0.30 ms, browser 0.14 to 0.38 ms, transport 0.16 to 0.24 ms; all 90 drawings on the page 17 ms in total. Only the transport strips animate, at 30 pictures a second, while on screen and the page is visible; with "reduce motion" everything stands still.

Rules the implementation must keep: nothing draws per frame that did not before (the playhead flag, beat orbit, sparkline and meters ride on redraws that already happen); clip read-outs and waveform shapes are cached per clip and redrawn only when the clip or the zoom changes; in Light mode the same marks are drawn on solid panels and the beat orbit stands still.

## 6. Proposed implementation order (each an index.html task, one at a time, after the picks)

Small and visible first, the shared grid before the things drawn on it, the browser last because it is the biggest change. Each task: only the picked items, the usual release routine (git pull --rebase, small commits, existing UI tests, Fractals levels unchanged), a headless test with screenshots in Dark and Light mode, and a frame-time check with `tools/ui-tests/frametime.py` that idle and playback cost no more than before. Run after MD1 where noted, since MD1 brings the number formatting and unit labels.

1. **DR2-A1, grid and ruler** (AG, and the grid strengths of P): one shared function for bar/beat/sixteenth strengths used by the arrangement and the piano roll, ruler ticks, the grid value; works with X4's zoom levels if that has landed.
2. **DR2-A2, playhead and selection** (AP): cap, flag with position and time, selection size at rest. After MD1 (time formatting, caliper style).
3. **DR2-A3, clips** (AC): band height, body tint, length read-out, loop repeat marks; cached text per clip. **Done (task DS-A3), v0.252**: AC3, no band (name on the body, 2 px colour edge, darker body); loop repeat marks not drawn, the app has no clip looping.
4. **DR2-A4, waveforms** (AW): peak and loudness body or outline, cached per clip and zoom level; the three-band analysis only if AW3 or A5 is picked. **Done (task DS-A4), v0.254**: AW3, three bands (lows blue, mids amber, highs white), analysis once per buffer, drawing in the per-clip cache.
5. **DR2-P1, piano roll rows and keys** (PS, PK): scale rows, root line, out-of-scale ring, octave names, Hz on keys; chord names (PS3) as a separate step if picked.
6. **DR2-P2, notes and velocity** (PN, PV, PG): note shape, velocity display, ghost outlines, note read-out.
7. **DR2-T1, clock and tempo** (TT, TB, TL): after MD1; the beat orbit reuses MD1's orbit loader drawing.
8. **DR2-T2, meters, CPU and top bar** (TM, TC, TS): meter scales, CPU line from the existing CPU sampling, the top bar status line together with X10 (science round 2, SC-K).
9. **DR2-B1, browser** (B look, BR, BP): the new layout behind the same entry points (Instrument Browser, Effects Browser), preview in tempo, arrow keys.
10. **DR2-B2, preset menu** (BM): search, tags, change line, stars and A/B.

## 7. Sources

**Arrangement, clips and waveforms**
- [Bitwig: The Arrange View and Tracks](https://www.bitwig.com/userguide/latest/the_arrange_view_and_tracks)
- [Bitwig: Arranger Clips and the Browser Panel](https://www.bitwig.com/userguide/latest/arranger_clips_and_the_browser_panel)
- [Bitwig: Working with Audio Events](https://www.bitwig.com/userguide/latest/working_with_audio_events)
- [Sound On Sound: Bitwig Studio 6](https://www.soundonsound.com/reviews/bitwig-studio-6)
- [Live 12 Manual: Arrangement View](https://www.ableton.com/en/live-manual/12/arrangement-view)
- [Live 12 Release Notes](https://www.ableton.com/en/release-notes/live-12/)
- [Sound On Sound: Studio One Pro 7](https://www.soundonsound.com/reviews/presonus-studio-one-pro-7)
- [Serato: Main Waveform Display](https://support.serato.com/hc/en-us/articles/224969307-Main-Waveform-Display)
- [The Secret Language of Waveforms](https://reallychrism.substack.com/p/the-secret-language-of-waveforms) (Rekordbox modes)
- [Digital DJ Tips](https://www.digitaldjtips.com/?p=2475091)
- [Sound On Sound: Cubase Pro 14](https://soundonsound.com/reviews/steinberg-cubase-pro-14), [MusicRadar: Cubase Pro 14](https://www.musicradar.com/music-tech/daws/steinberg-cubase-pro-14-review)

**Piano roll and MIDI**
- [Live 12 Manual: Editing MIDI](https://www.ableton.com/en/manual/editing-midi-notes-and-velocities), [Ableton: Keys and Scales FAQ](https://help.ableton.com/hc/articles/11425083250972), [Sound On Sound: Ableton Live 12](https://www.soundonsound.com/reviews/ableton-live-12)
- [Logic Pro: Edit note velocity](https://support.apple.com/guide/logicpro/lgcpa8fee137/mac), [Sound On Sound: Logic Scale Quantise](https://www.soundonsound.com/techniques/logic-scale-quantise-midi-transposition)
- [Bitwig: Working with Note Events](https://bitwig.com/userguide/latest/working_with_note_events)
- [Steinberg: Event Colors Menu](https://archive.steinberg.help/cubase_pro/v12/en/cubase_nuendo/topics/midi_editors/midi_editors_note_events_coloring_r.html)
- [FL Studio: Piano Roll](https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/pianoroll.htm), [FL Studio: Piano Roll menu](https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/pianoroll_menu.htm)
- [Celemony: Display options](https://helpcenter.celemony.com/M5/doc/melodyneStudio5/en/M5tour_ViewOptions-ARA), [Sound On Sound: Melodyne 5](https://www.soundonsound.com/reviews/celemony-melodyne-5)

**Browser and presets**
- [Live 12 Manual: Working with the Browser](https://www.ableton.com/en/live-manual/12/working-with-the-browser/), [Ableton: Similarity Search FAQ](https://help.ableton.com/hc/en-us/articles/11386675465628), [Ableton: Browser and Tags FAQ](https://help.ableton.com/hc/articles/11425042663708), [MusicRadar: Live 12, five things](https://www.musicradar.com/how-to/live-12-5-things-you-need-to-know)
- [Sound On Sound: Studio One Browser](https://www.soundonsound.com/techniques/studio-one-browser)
- [Steinberg: MediaBay Filters](https://steinberg.help/cubase_le/v11/en/cubase_nuendo/topics/mediabay/mediabay_filters_section_c.html)

**Transport and meters**
- [Bitwig: Window Menus and Transport Area](https://bitwig.com/userguide/latest/the_window_menus_transport_area)
- [Logic Pro: LCD display mode](https://help.apple.com/logicpro/mac/10.4.5/en.lproj/lgcp5bdd6d9d.html)
- [Sound On Sound: PPM and VU meters](https://www.soundonsound.com/sound-advice/q-whats-difference-between-ppm-and-vu-meters)
- [Flux: Loudness metering](https://doc.flux.audio/analyzer/Metering_Loudness.html)

**Readability**
- [NN/g: Dark Mode](https://www.nngroup.com/articles/dark-mode/), [arXiv 2409.10841 (polarity in chart reading)](https://arxiv.org/html/2409.10841v1), [Kim et al., SUI '19](https://sreal.ucf.edu/wp-content/uploads/2019/10/Kim2019edm.pdf)
- [Material dark theme codelab](https://codelabs.developers.google.com/codelabs/design-material-darktheme/index.html)
- [NASA Color Usage: Blue](https://colorusage.arc.nasa.gov/blue_2.php)
- [Renoise: GUI Customisation](https://tutorials.renoise.com/wiki/GUI_Customisation), [Renoise: Tracker Interface](https://tutorials.renoise.com/wiki/Tracker_Interface), [CDM: Bitwig themes](https://cdm.link/2024/07/bitwig-themes/)

**Instruments and mission control**
- [Tektronix: XYZs of Using a Scope](https://www.qsl.net/w2aew/XYZs_of_Using_a_Scope.pdf), [Teledyne LeCroy: Display Graticule](https://blog.teledynelecroy.com/2014/09/back-to-basics-using-display-graticule.html), [Keysight: Graticule Grid](https://helpfiles.keysight.com/csg/d9300a/Help/Infiniium-UG/Content/Topics/Display/Graticule_Grid.htm), [Control Engineering: Digital Phosphor](https://www.controleng.com/digital-phosphor-oscilloscope-combines-analog-digital-strengths), [Rohde & Schwarz: MXO 3](https://www.rohde-schwarz.com/hu/_251220-1587861.html)
- [iZotope RX 9: Spectrogram](https://s3.amazonaws.com/izotopedownloads/docs/rx9/en/spectrogram-waveform-display/index.html), [iZotope: Understanding Spectrograms](https://www.izotope.com/en/learn/understanding-spectrograms.html)
- [Open MCT Users Guide](https://nasa.github.io/openmct/docs/static/files/Open_MCT_Users_Guide.pdf), [About Open MCT](https://nasa.github.io/openmct/about-open-mct), [Open MCT Espresso theme constants](https://cdn.jsdelivr.net/npm/openmct@4.3.0-rc1/src/styles/_constants-espresso.scss), [Open MCT issue 7673](https://github.com/nasa/openmct/issues/7673)

**Gaps:** did not load: a PMC paper (captcha) and Material's m2 dark theme page (needed JavaScript; the codelab was used). No usable text: several Logic help pages (Piano Roll, Live Loops), the Cubase Key Editor display page, the Reaper 7 Theme Adjuster (marked not yet available), Rohde & Schwarz SmartGrid (video library). Not covered: Reaper theme parameters, Cubase velocity colour values, Melodyne blob shape rules, Logic Live Loops visuals.

## 8. How the page was made and checked

- **Today:** `tools/design-lab/shoot_today.py` and `shoot_today2.py` open v0.228 headless at 1600 x 900 with the Fractals song, hold Dark (glass) or Light mode (the slow headless machine would otherwise switch itself to Light mode), and shoot the window, the transport, the arrangement at 1 bar = 100 px, the piano roll, the Instrument Browser, the Effects Browser and a preset menu (`tools/design-lab/today/`, not committed; the scripts make them again). `crop_today.py` cuts the cards' crops into `tools/design-lab/page/today/`. In software rendering the glass engine draws little over empty lanes, so the Dark and Light shots look almost the same.
- **Options:** `tools/design-lab/page/index.html` (the published page; the artifact service adds the document head). Four parameterised canvas renderers (arrangement, piano roll, browser, transport) draw every look and detail from one set of switches, at the app's sizes and colours (`--bg #0a0a0c`, `--pn #121216`, `--ink #ececf1`, `--mut #8b8b97`, green `#3ecf8e`, blue `#4c8dff`, track colours from the palette).
- **Checked:** `tools/design-lab/check_page.py` at 1280 x 720 (dark page), 1920 x 1080 (light page) and 400 x 800: no console errors, no sideways scroll, both app looks, "Take all ★" gives `My picks: A3 P3 B3 T2`, draw times as in section 5.
- Honest limits: the mock-ups are drawings in the style of the app, not the app's drawing code; the glass in them is a tinted panel with a rim, not the engine; names, presets and numbers are examples from the Fractals project at 145 BPM; the "Today (redrawn)" cards in the detail rows are approximations, the large Today cards are real screenshots.

## The user's picks (27 November 2026, 14:36 Brussels)

`A5 P4 B3 T3 | AC3 AW3 AG2 AP2 PN3 PV3 PS3 PK3 PG1 BR2 BP1 BM2 TT3 TB3 TM1 TC1 TS1 TL1`

Built by the steps of section 6 (DR2-A1 to DR2-B2), only the picked items. The grid step (DR2-A1, AG2) is shared with the arrangement-lines round (docs/design-grid-lines.md, proposed task GL1): if the user's lines picks are in by then, GL1 and DR2-A1 are one step.
