# AudioLab Pro: arrangement lines (task DR6, 27 November 2026)

The user (27 Nov, live): *"Let's also improve the lines on the arrangement view. Do some research on what the best lines are, not just on DAWs, but also on other applications. Maybe we can make it look a little bit more scientific and come back with a few line designs, and then we'll go from there."*

**Pick page (artifact "AudioLab arrangement lines"):** https://claude.ai/artifact/YGbbF7XNgkjPnWp5jopAu9 (source `tools/design-lab/dr6/arrangement-lines.html`).
Zoom around in each design, pick, then paste the line from the bar at the bottom, for example `L1 · R2 P2 S2 T1 Z2`.

Scope: only the lines of the arrangement: bar, beat and sub-beat grid lines; the ruler with its ticks and numbers; track separators; loop and selection edges; the playhead line; snap guides; what shows at which zoom; and the same lines in the piano roll where they are shared. Clips, waveforms and the overall look of the arrangement are task **DR2**: `docs/design-round-2.md`, pick page https://claude.ai/artifact/VW7jsEAkc6wrxWmVvyTYvX. Nothing here changes clips.

**Overlap with DR2, and how to resolve it.** DR2 has two rows that touch lines: **AG** (grid and ruler: 0 today, 1 three strengths, 2 ★ plus grid value, …) and **AP** (playhead and selection), plus the piano roll's P1 "fine graticule", and proposes implementation tasks DR2-A1 (grid and ruler) and DR2-A2 (playhead and selection). DR6 is the detailed round on exactly those lines. Proposal: **the DR6 pick replaces DR2's AG choice and the line part of AP and P1**; DR2-A1 and the line half of DR2-A2 become task GL1 below (one task, so the grid is not built twice). DR2's playhead flag with position and time (A3, AP) is not a line and stays with DR2; DR6's P options only change the line and its cap. DR6 R2 (grid read-out at the right end of the ruler) is the same idea as DR2 AG2 and A1, worked out with units. Strength stays **subtle** (the user's standing choice), today's colours stay, direction is scientific ("smart and sciencey, clear, intuitive, snappy", measurement details, mathematical beauty). **Nothing in index.html or desktop/ was changed by this task.**

Related: `docs/glass-engine-plan.md` §1 (design philosophy), `docs/design-language-research.md`, `docs/science-look.md`, `docs/science-look-round-2.md`, picks in `claude/audiolab-science-picks.md` (MD1: M1 read-outs with units, M3 caliper while dragging; round 2: **X4 ruler that reveals on zoom** and **X11 scale bars** were picked, X3 crosshair was not, X12 grid coordinates on demand was picked).

## 1. Today (v0.228, measured)

Screenshots: `tools/design-lab/dr6/shots_today.py` opens the Fractals demo headless at the user's size (2194 × 1139 CSS px at 1.75x) at three zooms (whole song 1.71 px per beat, 16 bars 30.9, 1 bar 494.5).

From `drawArr` (index.html about line 4644) and the ruler code just below it:

| Line | Today |
|---|---|
| Grid step | `step = ppb ≥ 28 ? 0.25 : 1`, then doubled while `step·ppb < 8`. Whole levels appear and vanish at once (pop). No 1/32. |
| Grid strength | white, 4-bar lines 0.15 at **1.5 CSS px**, bars 0.10, beats 0.055, sixteenths 0.03, all × Grid brightness (`UI.gridB/50`) × theme factor (`TH.grk`, Light 2.2). Positions are rounded to device pixels, **widths are not**: at 1.75x a 1 px line is 1.75 device px, the 4-bar line 2.6, so both have soft edges. |
| Ruler | bar numbers only (Inter 11), each with a full-height 1 px line, every `lb` bars where `lb·4·ppb ≥ 44`. **No beat or sixteenth ticks.** Zoomed to one bar the ruler shows nothing but the first number. |
| Track separators | `TH.sep` 1 CSS px at the bottom of each lane, alternating lane shades `lane0/lane1`, a 2 px track-colour strip. |
| Loop | ruler: fill 0.13, edges 0.8, flags; lanes: fill 0.035 and **device-pixel hairline** edges at 0.55 (already crisp). |
| Selection | fill 0.16, dashed 5-3 outline at 0.95 drawn at `round(x)+.5` in CSS px (soft at 1.75x). |
| Snap / drop guide | white 2 px line (section drag); clip drag has no guide line. |
| Playhead | `phDraw`, 1.5 CSS px green `#3ecf8e` (2.6 device px at 1.75x, soft). |
| Piano roll | `drawPR`: own step loop (`while(st·PR.ppb<7) st*=2`), solid colours `#3a3a46 / #26262e / #1b1b21`, bar numbers like the arrangement ruler. |
| Cost | with Follow on, the whole arrangement (grid included) is redrawn every playing frame (`ARRWH=null`), see glass plan §2.1. |

What the screenshots show: at the whole-song zoom the lanes carry a line every two bars plus the 4-bar lines, the ruler numbers every 8 bars with no marks between them; at 16 bars the beat lines are present but the eighth-note level has just popped away (31 px per beat, quarter step 7.7 px < 8); at one bar the sixteenths are faint and the ruler is empty.

## 2. Research (sources)

### DAWs
- **Ableton Live** ([Live 12 manual](https://www.ableton.com/en/live-manual/12/arrangement-view)): the grid is zoom-adaptive or fixed; ⌘1 / ⌘2 narrow or widen it (double or halve the line density), ⌘3 triplets, ⌘4 snap, ⌘5 fixed/adaptive. **The current grid spacing is shown as a read-out next to the ruler.** Two rulers (bars-beats-sixteenths and min:sec:ms). Alternating 4-bar background shading; users complain that the grouping jumps while zooming and does not follow odd phrase lengths ([forum](https://forum.ableton.com/viewtopic.php?p=1724090)); theme keys `ArrangerGridTiles` / `DetailGridTiles`.
- **Bitwig** ([arrange view](https://www.bitwig.com/userguide/latest/the_arrange_view_and_tracks), [timing](https://www.bitwig.com/userguide/latest/a_matter_of_timing)): adaptive beat grid; ruler labels change with zoom between BAR, BAR.BEAT and BAR.BEAT.TICK; optional realtime ruler.
- **Logic Pro** ([snap](https://support.apple.com/guide/logicpro/snap-items-to-the-grid-lgcpf7c0f66a/11.1/mac/14.6), [bar ruler](https://help.apple.com/logicpro/mac/9.1.6/en/logicpro/usermanual/chapter_4_section_11.html)): Smart snap follows the ruler division and the zoom; bars numbered in steps of **1, 4, 8 or 16**; rank shown by tick length (a line per bar in the bottom third, beats shorter and only when there is room).
- **Cubase / Nuendo** ([grid types](https://steinberg.help/nuendo/v12/en/cubase_nuendo/topics/project_window/project_window_grid_types_r.html), [ruler formats](https://steinberg.help/nuendo/v12/en/cubase_nuendo/topics/project_window/project_window_ruler_display_formats_r.html)): Bar, Beat, Use Quantize, **Adapt to Zoom** (bars down to 1/64). Users asked for separate bar and beat line colours back ([forum](https://forums.steinberg.net/t/project-area-grid-lines-separate-color-settings-for-barline-and-beats/144561)).
- **REAPER** ([Sound On Sound](https://www.soundonsound.com/node/4904964), [tutsplus](https://music.tutsplus.com/how-to-use-reaper-tempo-grid-and-snap-settings--cms-107661t)): **minimum grid line spacing in pixels, default 20 px**; by default snap follows grid visibility (you snap only to lines you see); solid or dotted grid lines (Preferences/Appearance).
- **Studio One** ([SOS](https://www.soundonsound.com/techniques/studio-one-snap-grid-quantize-settings), [manual](https://fenderstudiopromanual.fender.com/en/Content/Editing_Topics/The_Grid.htm)): adaptive snap by default; grid lines extend the ruler ticks; "draw events translucent" lets grid lines show through clips.
- **FL Studio** ([playlist](https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/playlist.htm)): snap resolution grows as you zoom in up to the snap setting.
- **Renoise** ([song options](https://tutorials.renoise.com/wiki/Song_Options)): rows highlighted every LPB (beat): rank shown with bands rather than lines.
- **Pro Tools** ([main time scale](https://apps.avid.com/proToolsFirstHelp/version12.0/enu/Pro%20Tools%20First%20Help/Arr1.conductors.31.05.html)): grid follows the main time scale; grid lines toggle ([Production Expert](https://www.production-expert.com/home-page/2018/8/25/toggle-grid-lines-and-grid-value-expert-tip?format=amp)).

### Design and CAD tools
- **Figma** ([help](https://help.figma.com/hc/en-us/articles/360041065034)): the pixel grid shows only at 400 % zoom and above; snapping works at any zoom (seeing and snapping are separate).
- **Sketch** ([docs](https://www.sketch.com/docs/canvas/rulers-guides-grids/)): square grid with a setting for how often thicker lines appear.
- **Blender** 2D editors ([commit](https://developer.blender.org/rB667af6cf411918ba181afc1a7d6bcb474f9fadb8)): major steps from 1-2-5 lists, the first that keeps **50 px × UI scale** between major lines, minor lines halfway; the sequencer triples the minimum because it looked too fine and its default grid colour was darkened from `#404040` to `#212121` ([commit](https://developer.blender.org/rB0491052a9697a706b4cd14a1f478180ad6fb8c75)). 3D grid alpha made themable "to reduce visual strain" ([mailing list](https://lists.blender.org/pipermail/bf-blender-cvs/2018-November/115843.html)).
- **AutoCAD** ([GRIDDISPLAY](https://help.autodesk.com/cloudhelp/2022/ENU/AutoCAD-LT/files/GUID-4D6AC943-FC9C-4CB8-A4E6-AD7313BF9C3A.htm)): adaptive grid limits density when zoomed out and adds subdivisions when zoomed in, in the proportion of the major lines. **Fusion 360** fixed vs adaptive sketch grid ([forum](https://forums.autodesk.com/t5/fusion-support-forum/gridlines-change-when-zooming-amp-moving-project-even-when-grid/m-p/12367340)).
- Infinite-grid shaders choose the level from the log of the zoom and cross-fade the next level by the fractional part ([Godot Shaders](https://godotshaders.com/shader/infinite-not-quite-zoom-grid/)).

### Scientific plotting and instruments
- **matplotlib** defaults ([customizing](https://matplotlib.org/3.9.2/users/explain/customizing.html)): major tick 3.5 pt × 0.8 pt, minor 2 pt × 0.6 pt (minor ≈ 57 % of the length); grid `#b0b0b0` 0.8 pt; `axes.axisbelow: 'line'` (grid above fills, below data lines).
- **d3** ([ticks](https://d3js.org/d3-array/ticks)): ticks are a power of ten times 1, 2 or 5. **Grafana** ([axis](https://docs.aws.amazon.com/grafana/latest/userguide/v10-time-series-axis.html)): grid lines Auto / On / Off.
- **Bartram & Stone, "Whisper, Don't Scream: Grids and Transparency"** ([PDF](https://tableau.com/sites/default/files/2023-01/2011-WhisperGrids.pdf)): people set usable grid alpha between about **0.1 (faintest) and 0.45 (too strong)**; **0.2 works in every tested case**; denser grids are set fainter; light grids on dark grounds behave differently (about 0.1 alpha shift).
- **Tufte / Wilke** ([Fundamentals of Data Visualization](https://clauswilke.com/dataviz/balance-data-context), [summary](https://staff.washington.edu/larryg/Classes/R560/zz-tufte.html), [leancrew](https://leancrew.com/all-this/2017/12/drum-tufte-grids-axes/)): grids muted, not removed; major plus minor grids get too dense; white space can be the grid.
- **Oscilloscope graticule** ([Teledyne LeCroy](https://blog.teledynelecroy.com/2014/09/back-to-basics-using-display-graticule.html), [SparkFun](https://learn.sparkfun.com/tutorials/how-to-use-an-oscilloscope/all?print=1)): 10 × 8 divisions, **5 minor ticks per division drawn only on the two centre axes**, dotted reference lines at ±2.5 div, solid at the 10/90 % levels. The LeCroy figure shows that grid over a step response on an HDO6054: solid outer frame, faint inner lines, fine ticks along the centre cross. Internal graticules (scribed into the screen) removed the parallax of external ones ([patent US3500115A](https://patents.google.com/patent/US3500115A/en)): the grid belongs in the same plane as the data.
- **Bloomberg** ([Tech at Bloomberg](https://www.bloomberg.com/company/stories/how-bloomberg-terminal-ux-designers-conceal-complexity)): density and "toned down" colour; chart grid details not published.

### Paper, maps, sky charts, video
- **Graph paper** ([Wikipedia](https://en.wikipedia.org/wiki/Graph_paper)): millimetre paper 1 mm squares with heavier 5 and 10 mm lines; engineering paper prints its grid on the back so it shows faintly through (physical muting), in light green, blue or tan.
- **GIS graticules** ([ArcGIS Pro](https://doc.esri.com/en/arcgis-pro/latest/help/layouts/add-and-modify-graticules.html)): grid lines, edge ticks, edge labels, **intersection crosses instead of lines**, interior ticks; several tick styles combined to show major and minor divisions; intervals set by scale. Web map zoom halves the scale per level ([OSM](https://wiki.openstreetmap.org/wiki/Zoom_level)).
- **Sky charts**: an amCharts star atlas draws its graticule at 0.5 px and 0.15 opacity ([demo](https://www.amcharts.com/demos/star-atlas/)); SkySafari labels hours only along the celestial equator, ticks every 10′ ([guide](https://userguide.skysafariastronomy.com/app-specific/settings-help/display-options-help/grids-and-reference-help)).
- **Video editors**: Shotcut thins ruler labels with zoom, and labels vanishing at the left edge while scrolling is reported as a bug ([forum](https://forum.shotcut.org/t/improve-timeline-keyframe-ruler-label-display/36251)); Resolve users find ruler numbers too small and faint ([forum](https://forum.blackmagicdesign.com/viewtopic.php?p=772449)); Final Cut documents only the basics ([Apple](https://support.apple.com/guide/final-cut-pro/ver1632c98e/mac)).

### Crisp lines on high-DPI screens
- A 1 px stroke on an integer coordinate straddles two pixels; offset by half a pixel ([Konva](https://konvajs.org/docs/posts/Canvas_Blurry.html)). `css × devicePixelRatio` is only approximate at fractional ratios; `ResizeObserver` with `device-pixel-content-box` gives the exact backing size (Chrome 84+, so fine for Electron) ([web.dev](https://web.dev/articles/device-pixel-content-box)). At 1.75x every width must be chosen in device pixels.

Not verified from sources (kept out of the numbers): Bitwig, FL and Pro Tools line colours; Figma/Sketch defaults; AutoCAD GRIDMAJOR default; Final Cut and Premiere ruler thinning rules.

### Rules taken from the research (used by every design)
1. **Three ranks plus phrase**, told apart by alpha first, then dash or length, width last: 4-bar ≈ 0.20, bar ≈ 0.12, beat ≈ 0.065, sixteenth ≈ 0.035 on the dark theme (bar at the "whisper" 0.1 to 0.2 band, sub-beats at the faint limit). Light theme × 1.6.
2. **Show only what is at least 8 px apart; fade in up to 16 px** (one octave of zoom). Ruler labels need about 46 px, full strength at 70.
3. **Steps of two** for subdivisions (bar, half, beat, eighth, sixteenth, 1/32, 1/64), coarsening to 2, 4, 8, 16 bars; or **steps of four** (Z4) for a purely musical ladder.
4. **Fade, never pop**, and the snap grid is the finest level at least half faded in (you snap to what you see, REAPER rule).
5. **Grid under the clips, edges and playhead over them** (matplotlib `axisbelow`, internal graticule).
6. **Whole device pixels**: hairline = 1 device px, playhead 2 px at 1x / 3 px at 1.75x and 2x; dots in whole pixels and aligned row to row; hairlines × 1.25 alpha at 1.5x and above.
7. **Ruler ranks by tick length** (bar 9 px, beat 6, sixteenth 3.5) and mono digits, a grid read-out with units (M1), the current bar pinned at the left edge.
8. **Separators are a different family** from time lines: horizontal, never stronger than bar lines.
9. **One accent held back**: only the playhead, loop and guides carry colour; the M3 caliper amber appears only while dragging.

## 3. The designs (all live on the pick page)

Every design keeps today's colours and clips. ★ = recommended.

| # | Design | Lines |
|---|---|---|
| L0 | Today | as section 1 |
| **L1 ★** | **Graph paper** | every level a solid hairline; 4-bar 0.20 at 1 CSS px (whole device px), bar 0.12, beat 0.065, sixteenth 0.035. Quiet and exact. |
| **L2 ★** | **Oscilloscope graticule** | bars solid 0.13, beats dotted 1-on-3-off at 0.16, sixteenths not as lines but as ±2.5 px ticks on each track's centre line (0.22), like a scope's centre axes. The most instrument-like. |
| L3 | CAD adaptive | strength from spacing, not musical meaning: α = 0.24 × ((log₂ s − log₂ 6) / log₂ 37)^1.25, so the coarsest visible level always leads. |
| L4 | Dotted beats, solid bars | bars and 4-bar solid, beats dots 1:2 at 0.15, sixteenths dots 1:4 at 0.10. |
| L5 | Bar bands, hairline beats | alternating bands (±0.028) anchored to bars, cross-fading between 1, 4 and 16 bars while zooming; 4-bar hairline 0.12, beats 0.05, sixteenths 0.03; no bar lines. |
| L6 | Lab notebook | lines tinted in the theme's own hue (215°), 4-bar lines doubled like ruled paper, red margin line at the song start. |
| L7 | Minimal | bars 0.075, beats only from 24 px at 0.04, no sixteenth lines (the ruler has them), no separator lines. |
| L8 | Star chart | dotted bar lines (1:5, 0.12), a small cross where each bar meets a track line (0.40), beat ticks on the track lines; grid points instead of a mesh. |

Mixable rows (each design brings its own set; "auto" follows the design):

| Row | Options |
|---|---|
| **R ruler** | R0 today · R1 graduated ticks (bar 9, beat 6, sixteenth 3.5 px, mono numbers down to 33.2 and 33.2.3 when there is room) · **R2 ★ caliper with read-out** (R1 + `GRID 1/16 · BAR 1.655 s · 124 px` at the right end, the current bar pinned at the left edge) · R3 dual scale (bars from the top edge, min:sec in 1-2-5 steps on the bottom edge) · R4 numbers and beat dots |
| **P playhead** | P0 today · P1 solid crisp (2/3/3 device px) with a cap · **P2 ★ index line** (bright 1-CSS-px core, faint 1-device-px flanks, index mark in the ruler) · P3 index line with ticks at each track line |
| **S edges** | S0 today · S1 dimension lines (amber dimension line with the selection length `2 BARS · 3.310 s`; snap guide with the offset, M3) · **S2 ★ registration marks** (hairline edges, corner marks outside the box, dashed snap guide with a diamond and `45.1.1` in the ruler) · S3 focus dim (outside the loop 0.20 darker) |
| **T separators** | T0 today · **T1 ★ hairline** (one dark device pixel, even lanes) · T2 engraved (dark + faint light pixel, alternating lanes) · T3 gap (2 px of background, no line) · T4 ticked (beat and sixteenth ticks along each separator) |
| **Z zoom** | Z0 today (pop at 8 px) · Z1 pop at 12 px · **Z2 ★ fade over one octave** (8 → 16 px, smoothstep on log₂ spacing) · Z3 slow CAD fade (6 → 32 px) · Z4 steps of four (16 bars, 4 bars, bar, beat, sixteenth) faded 10 → 24 px |

**Recommended line: `L1 · R2 P2 S2 T1 Z2`.** Graph paper is the calmest base and reads for hours; R2 brings the picked X4/X11 ideas (ruler that reveals on zoom, scale read-out) and M1 units; P2 and S2 are crisp and quiet; Z2 removes the popping. If the user wants more character: `L2 · R1 P3 S2 T4 Z2` (graticule set).

Light mode: same rules, black lines × 1.6 (the app's Light theme today uses × 2.2), amber read-out labels darkened to `#7a5500` for contrast on the light ruler.

## 4. Pixel check and cost

The page has a pixel loupe: the same 72 × 70 px spot (a 4-bar line, beats, the playhead at a fractional x, a track separator) drawn at 1x, 1.75x and 2x, every device pixel magnified, Today on top and the current mix below. Today's 1.5 px lines and playhead smear across 2 to 3 device columns at 1.75x; the designs stay one or three whole columns.

Cost on the page (cloud machine, software rendering): the whole scene with lines about 1 to 2 ms per view change at 1280 px; per frame 0.03 to 0.1 ms (copy of the cached picture plus the playhead). Lines are drawn once per view change, never per frame.

Checks: `tools/design-lab/dr6/check.py` (loads the page at 1280 px at 1x, 1.75x, 2x and at 400 px, clicks every option, screenshots; no console errors, no horizontal scroll).

## 5. Piano roll

The same rules apply where the lines are shared: `drawPR` gets the same ladder and fade (one function for both), the same rank strengths (it uses solid greys today: `#3a3a46 / #26262e / #1b1b21`, which become the theme ink at the chosen alphas), the same ruler (PRUL 20 px: bar ticks 8, beat 5, sixteenth 3) and the same playhead. The piano roll's horizontal key lines stay as they are (they are DR2/piano-roll territory) but use the T choice's thickness rule (whole device pixels).

## 6. What the implementation task (proposed **GL1**, serial, touches index.html; absorbs DR2-A1 and the line half of DR2-A2) would change

1. **One grid function** `gridLines(g, x0px, y0, y1, b0, b1, ppb, style)` used by `drawArr`, the master lane beat lines (`drawMasterLane`, `UI.mapBeats`), `drawPR` and the tempo lane, replacing the three separate step loops. It walks the chosen ladder from the finest visible level (`finestL`), finds each position's coarsest level, and draws with the design's rank style × fade(spacing) × Grid brightness × theme factor. Time signatures: the ladder runs on `barStart`/`barPos` positions, as `isBarB` does today; non-4/4 bars become the bar rank, beats stay beats.
2. **Device-pixel drawing**: all lines drawn with the transform reset to identity (`vl` / `hl` helpers from the pick page): x snapped with `Math.round(x·dpr)`, widths and dots in whole device pixels, hairlines × 1.25 at dpr ≥ 1.5. Canvas sized with `device-pixel-content-box` (`fit()` today uses `css × dpr`). `DPX` already includes `ZOOM`.
3. **Ruler** (the block after `drawTempoLane` in drawArr and the copy at index.html ~10240): ticks by rank, labels from the finest level ≥ 46 px apart fading 46 → 70 px, mono digits, sticky bar at the left, the read-out at the right (GRID value, bar length in seconds and pixels; it is the snap value, so it also answers "what will I snap to").
4. **Snap = what you see**: the adaptive snap value becomes `snapL()` (finest level at least half faded in) when Snap is on Auto, so the read-out, the visible lines and the snap agree.
5. **Edges and guides**: selection outline and corner marks in device pixels (S choice); a snap guide while dragging clips (today only section drags have one); with S1 the M3 caliper label.
6. **Playhead**: `phDraw` widths rounded to device pixels (`max(2, round(1.5·dpr))`), index mark in the ruler (P choice). Keep the `tmFlag` time flag as is.
7. **Track separators**: T choice in the lane pass of drawArr (`TH.sep` line, `lane0/lane1`), header column separators to match.
8. **Cost**: draw the static picture (lanes, grid, clips, edges, ruler) into the cached `ARRC` once per view change and only blit it plus the playhead per frame, also with Follow on (glass plan §2.1 found Follow "center" redraws everything each frame; scrolling by a whole number of device pixels can shift the cached picture instead of redrawing it).
9. **Settings** keep working: Grid brightness scales all line alphas, "Sub ticks" hides the sixteenth level, "Bars 4" hides the phrase rank. Optional new setting "Grid lines: Fade / Pop" only if the user asks.
10. Version bump and the usual release routine; screenshots at 2194 × 1139 @1.75x at the three zooms before and after.

Not decided yet (for the user): which design and rows; whether L2's centre ticks should hide under clips (today's clips are see-through, so ticks show through faintly).
