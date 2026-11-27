# AudioLab Pro About page, round 2: Earth and the Van Allen belts (task SR7, 27 November 2026)

Pick page: **AudioLab About page, round 2: Earth and the Van Allen belts**, https://claude.ai/artifact/LifTY2KrH9JdwgR1hAFCw3

A pick page only: **nothing in index.html or desktop/ was changed, no version bump.** Round 1 is `docs/about-science-backgrounds.md` (task SR6); the user picked **AB5, Earth with the Van Allen belts**, and asked for changes. This round starts from the AB5 code.

How to answer: one number (for example "E2"), or a mix (for example "P2 S1 B3 C2 L1"). The picks bar on the page gives the line to paste. ★ marks the recommendation.

## What was asked, and how it was read

| The user's words | What the page does |
|---|---|
| "let's not have any text" | The background picture has no text, labels, scale bars or date stamps at all. |
| "dots ... more anatomically correct with this field ... move inside of the lines, aligned with the lines" | Every dot sits on a drawn field line and travels along it, with the real speed profile (see Physics). No dot crosses a line. |
| "remove the animated atom nucleus for now and keep that in the background. We will use that. And then the AudioLab logo." | The animated atom is taken off the About page and the static AudioLab logo (the atom mark from `desktop/icon-assets/mark-colour.svg`) stands in its place. **This is an assumption**, see below. |
| "the rest of the colors of the About page should match" | Text, rules, accent and logo colours come from the picture (see Colours). |
| "a few places to put it ... bigger, different tilts ... Earth spinning ... shapes of the continents, very subtly ... Earth itself in a line, more subtle" | Four placements with their own size and tilt, four Earth styles in line work with coastlines, slow spin. |
| "features ... too flashy ... less text ... more professional and scientific" | Three quiet content styles with the same facts; the icon tiles, the amber heading and the sub-heading are gone. |

### The assumption about the atom

The sentence can be read two ways: (a) take the animated atom off this page, keep its code for later, and show the AudioLab logo instead; or (b) keep the animated atom, but smaller and further back. The page follows (a). **E6 and the mix option L2 show (b)** for comparison: a small animated atom drawn on the same canvas at the logo's place.

Whichever is picked, the app's atom code stays where it is and is not deleted: `paintAtom()` and `drawAtom()` in index.html (near line 7749, with the `AT` and `ATC` data they use). The splash screen keeps using it. Only the About window would stop calling it.

## The options

Every option is shown as a complete About window (780 x 720) with the real content of v0.222. All are drawn live on one canvas.

### Complete pages

| # | Name | Mix | What it is | Cost |
|---|---|---|---|---|
| E1 | Emblem | P1 S1 B2 C1 L1 | Earth centred behind the logo, belts reaching both edges, contour lines, measurement table. | 0.43 ms |
| **E2 ★** | **Corner chart** | P2 S1 B1 C2 L1 | Large hairline Earth low right, cut by the edge, soft belts sweeping up the right side, one line per feature. | 0.62 ms |
| E3 | Left sweep | P3 S2 B1 C2 L1 | Half an Earth on the left edge with land tint, soft belts, one line per feature. | 0.40 ms |
| E4 | Field from above | P4 S1 B2 C3 L1 | The largest Earth, mostly above the window, contour lines arching down, spec list. | 0.28 ms |
| E5 | Drafted corner | P2 S3 B3 C1 L1 | Corner Earth drawn heavier with a night side, sparse lines, measurement table. | 0.28 ms |
| E6 | Emblem with the atom | P1 S2 B1 C1 L2 | As E1 with soft belts and the small animated atom kept (the comparison for the assumption). | 0.82 ms |
| E7 | Chart sheet | P3 S3 B2 C3 L1 | Left Earth drafted, contour lines, spec list. | 0.32 ms |
| E8 | Quietest | P4 S4 B3 C1 L1 | Still Earth above the page, sparse lines, measurement table. | 0.10 ms |

### Mix rows

- **P, placement and size.** P1 centred behind the logo (radius 60 px, axis leaning 23.4°, seen from 13° above the equator). P2 low right corner, cut off (radius 140, lean 26°, from 22° above). P3 left edge, belts sweeping across (radius 104, lean 12° the other way, from 9°). P4 from the top, axis lying over at 83° so the field arches down (radius 156, from 20°). In round 1 the Earth's radius was 27 px.
- **S, Earth style.** S1 hairline: thin outline, graticule every 30°, coastlines as hair strokes, turning. S2 land tint: no graticule, land as a very faint tint, turning. S3 drafted: heavier line, graticule every 15°, night side shaded, axis ticks, turning. S4 outline only, still: outline, equator, a whisper of coastline, no spin.
- **B, belts and dots.** B1 soft glow: the two belts as a faint glow, 9 shells of lines, 93 dots. B2 fine contour lines: no glow, 15 shells of thin lines, 100 dots. B3 sparse: 5 shells, 40 dots.
- **C, content style.** C1 measurement table: thin rules, columns Feature, Measured, Value, values in equal-width digits. C2 one line each: a name, a dotted leader, the number; the eight info values as two plain lines. C3 spec list: a compact data-sheet grid with a hairline at the left of each entry.
- **L, logo.** L1 static AudioLab logo. L2 the small animated atom (comparison).

Cost of the parts, as far as the eight measurements show: B decides most of it (B3 is the lightest, B1 the dearest because of the glow), a larger Earth on screen costs a little more, and L2 adds a few tenths of a millisecond. A mix that is not one of the eight shows its own live figure above the window.

### Recommendation: E2, second choice E5

E2 leaves the logo and name alone at the top, puts the Earth where no text is, and with the one-line content the lower right corner stays open so the globe and its coastlines can be seen. It is the least "flashy" page that still shows the picture well. E5 is the same placement with the measurement table and the drafted Earth: more "instrument", a little less of the picture visible because the table is taller. E1 is the choice if a symmetric emblem is wanted; there the logo sits on top of the Earth, which is busier.

## Physics notes (so the picture is honest)

- **Field lines.** Each line is a dipole field line, r = L cos²(latitude), drawn in three dimensions around the dipole axis. The axis leans 9.2° from the spin axis toward the geomagnetic north pole at 80.8° N, 72.8° W (NOAA, epoch 2025.0: 80.85° N geodetic, 72.76° W, inclination 9.21°). Because the pole is fixed to the ground, the field wobbles as the Earth turns, as it really does.
- **Bounce.** A trapped particle spirals along its field line and is turned back where the field has grown to B_mirror, with sin²(equatorial pitch angle) = B_equator / B_mirror and, on a dipole, B / B_equator = sqrt(1 + 3 sin²λ) / cos⁶λ. Its speed along the line is v · sqrt(1 − B/B_mirror): fastest at the equator, zero at the mirror point. The page integrates exactly this along the line (arc length ds = L cos λ sqrt(1 + 3 sin²λ) dλ) into a small table for six mirror latitudes (10° to 46°) and moves each dot by it. The short tail behind a dot is where it was a moment before, so its length shows the speed. Mirror points are kept above the surface (at least 1.08 Earth radii from the centre). The bounce period carries the standard factor (1.30 − 0.56 sin α) of Hamlin et al. 1961 and grows with L.
- **Drift.** Electrons drift eastward, protons and other positive ions westward. A dipole is the same at every longitude, so any meridian is a field line: the page turns each shell's set of lines slowly around the dipole axis, outer-belt lines with their electrons (blue dots) eastward and inner-belt lines with their protons (warm dots) westward, faster further out (drift period goes as 1/L at a given energy). This shows the drift while every dot stays exactly on its line. Lines in the slot and outside the belts only turn with the Earth.
- **Where the dots are.** Inner belt shells L 1.3 to 2.8, outer belt shells L 4 to 7 (NASA: about 1.25 to 3.0 and 4.0 to 7.3 Earth radii from the centre, converted from 1 000 to 8 000 and 12 000 to 25 000 miles altitude). The slot around L 3.5 has one dot in B1 and none in B2 and B3. Most dots mirror at low latitudes, as real trapped particles do.
- **Earth.** Turns eastward. Coastlines are about 300 hand-placed longitude and latitude points for the continents and the larger islands, drawn as strokes in code. No image files.

### Real numbers against what is shown

| Motion | Real (1 MeV electron near L 4; 10 MeV proton near L 1.7 to 4) | On the page |
|---|---|---|
| Spiral around the line | electron about 2 × 10⁻⁴ s, proton about 0.13 s | not drawn |
| Bounce between mirror points | electron about 0.3 s, proton about 1.7 s | about 5 to 20 s for both (the electron slowed roughly 20 times or more, the proton less) |
| Drift once around the Earth | electron about a quarter of an hour (formula below), proton about 1 minute | outer lines about 80 to 135 s, inner lines about 55 to 125 s |
| Earth's rotation | 23 h 56 min | 4 minutes |

So there are three clocks, each set so the motion can be seen. Directions, the shape of the motion along the line and the ordering with L are true; the ratios between the three motions are not.

A disagreement between sources, stated openly: the ECSS table gives 3.5 minutes for the drift of a 1 MeV electron at 20 000 km altitude, while Walt's formula (τ ≈ 5300 s / [L (E + 0.511 MeV)(v/c)²]) gives about 16 minutes at the same place. The proton figure and both bounce figures agree with the formulas. The page text says "about a quarter of an hour".

### What is simplified

- A pure dipole. The real field is pressed in on the sunward side (magnetopause near 10 Earth radii) and stretched into a tail; neither is drawn in this round, and the geostationary shell marker of AB5 is gone with the labels.
- The inner belt also holds electrons; only its protons are drawn. The outer belt is drawn as electrons only.
- The belt edges move with solar activity; NASA's own pages give slightly different figures.
- Seen from the Sun or not: no day and night side of the field. The night shading in S3 is a drawing choice.

### Sources

Read on 27 November 2026 by a research helper through a fetch tool that summarises pages, so figures are as that reader reported them.

- NASA Scientific Visualization Studio, radiation belt extents: https://svs.gsfc.nasa.gov/11212/
- NASA Radiation Belt Storm Probes press kit (inner belt mainly protons, outer mainly electrons): https://www.nasa.gov/wp-content/uploads/2015/03/677837main_rbsp_pk_final81712_lores.pdf
- NASA GSFC, "The Exploration of the Earth's Magnetosphere", inner belt and synchronous orbit at 6.6 radii: https://pwg.gsfc.nasa.gov/Education/Iradbelt.html
- ESA SPENVIS, trapped radiation background (three motions; drift westward for ions, eastward for electrons): https://www.spenvis.oma.be/help/background/traprad/traprad.html
- AFRL Handbook of Geophysics and the Space Environment 1985, chapter 5, hosted by NOAA (drift directions; bounce factor 1.30 − 0.56 sin α; magnetopause about 10 radii): https://www.ngdc.noaa.gov/stp/space-weather/online-publications/miscellaneous/afrl_publications/handbook_1985/Chptr05.pdf (first half read)
- ECSS-E-ST-10-04C table I-1, time scales at 20 000 km: https://spenvis.oma.be/ecss/e_st_10_04c/ecss_20_08_01.htm
- R. Fitzpatrick, University of Texas at Austin, plasma physics notes (field line equation, mirror condition, bounce period (L R_E / v)(3.7 − 1.6 sin α)): https://farside.ph.utexas.edu/teaching/plasma/Plasma/node23.html
- M. Walt, Introduction to Geomagnetically Trapped Radiation, appendix B (drift period formula; the scan was hard to read and the formula was rebuilt from its worked example, so treat it as partly checked): course copy at the University of Athens e-class, document DI492
- NOAA NCEI, geomagnetic poles and dipole inclination (WMM2025): https://www.ncei.noaa.gov/products/wandering-geomagnetic-poles

**No NASA pictures and no logos of others are used.** Everything in the picture is drawn in code.

## Colours taken from the picture

| Use | Colour | From |
|---|---|---|
| Ground | #05080e to #0b1322 | the night-blue behind the field |
| Lines and rules, "PRO" outline, logo rings | #7aaaff (rules at 22 % strength) | the field lines |
| Accent: values, "Under the hood", the "Lab" gradient start | #6ed0ee | the outer belt (electrons) |
| Warm accent: logo nucleus and electron only | #f0a878 | the inner belt (protons) |
| Text | #e8eef9, #a3b3cd, #8fa0bb | blue-tinted greys in place of today's neutral greys |

Today's amber heading (#f5c84c), the purple in the wordmark and the coloured icon tiles are gone. The logo is the real mark, recoloured; its file colours (ocean blue and yellow) are unchanged in the repo.

## Content: what changed and what did not

Same facts as today, nothing invented: the eight info values (version, build, audio engine, running at, instruments, effects, platform, cores) and the six highlighted features with their measured numbers from the About showcase (`AHF` in index.html): 32 voices per track and up to 14 oscillators each; a note moved by 293 samples, difference 0; old sound gone in 13 to 19 ms; six heavy tracks, 59 % to 7 % of the audio thread; 4 or 6 stems, offline after one download; held notes within about 4 cents.

Left out to have less text: the line "What runs inside AudioLab Pro, with the numbers we measured", the icons, the stem splitter's timing example, and "Version" as its own line (now beside "Digital audio workstation"). The content column is 540 px wide instead of 700, which leaves the margins for the picture. "All 35 features" and "Check for updates" stay as two plain buttons.

## Readability

The picture lives in the top band and the two margins. Behind the text column and behind the name there is a soft dark veil (86 % at full strength, built once as a small picture), and dots inside the column are drawn at about a fifth of their strength.

Checked in a headless browser for all eight pages, moving (six moments each) and Light level: the text colour against the **brightest single point** of the picture behind each piece of text.

| Text | Worst case, moving | Worst case, Light level |
|---|---|---|
| "Audio" / "Lab" in the name | 11.7 : 1 / 7.5 : 1 | 12.9 : 1 / 8.6 : 1 |
| "Digital audio workstation · Version" | 6.5 : 1 | 6.7 : 1 |
| Designed by / the name | 8.1 : 1 / 14.7 : 1 | 8.5 : 1 / 15.4 : 1 |
| Info labels / info values | 6.4 : 1 / 7.4 : 1 | 6.9 : 1 / 8.4 : 1 |
| Table head | 6.8 : 1 | 7.2 : 1 |
| Feature names / "measured" column / values | 11.1 : 1 / 8.7 : 1 / 7.3 : 1 | 13.8 : 1 / 8.9 : 1 / 7.6 : 1 |
| "Under the hood" | 10.0 : 1 | 10.5 : 1 |
| Copyright line | 6.8 : 1 | 7.0 : 1 |

Everything is above 6 : 1. Today's weakest lines (version 2.97 : 1, copyright 4.27 : 1) are fixed by the new greys.

**"Dark and Light".** The app's About window is dark, so the window on the page is dark in both cases; "Light" is the app's Light performance level, shown by the "Light level, still picture" switch (one frame, drawn once). The pick page around it follows the viewer's dark or light theme and was checked in both.

## Cost

Rules built into the page and meant for the app: one canvas for the whole background, the small atom of L2 included; at most 30 pictures a second; pixel ratio capped at 2; no blur, no shadows; drawing stops when the window is off screen or the page hidden, and in the app when About is closed or the app is in the background-freeze state; the Light level and "reduce motion" draw one still picture once.

Measured drawing time per picture at 780 x 720, pixel ratio 2, on the cloud machine (no graphics card): the figures in the table above, 0.10 to 0.82 ms. At 30 a second that is 0.3 % to 2.5 % of one core, only while About is open. The page shows the live figure for the viewer's own computer above the window. Checked with screenshots at 1280 x 720 and 1920 x 1080 (and at phone width): no errors, no sideways scroll.

## Next (after the pick; nothing started)

Implement the chosen page in index.html as a serial task with the usual release routine: the canvas behind `#splash.ab`, the new content markup and colours for `.about`, `.abg`, `.ahf*`, the static logo in place of the atom canvas in the About window only, the freeze and Light rules above, and a headless test. The drawing code on the pick page is written to be lifted: about 150 lines for one P, S and B choice with the physics tables and the coastline list.
