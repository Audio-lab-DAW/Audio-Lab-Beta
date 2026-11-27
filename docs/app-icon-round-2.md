# AudioLab app icon, round 2: science style (task IC2)

Pick page: **AudioLab app icon, round 2: science style**, https://claude.ai/artifact/AWKbYKUTX6q9REWnDjW17d

> "Let's work on the shortcut logo a little bit more. Let's have some more versions that look more like the splash screen we have. So maybe some scientific details, or maybe we can change a little bit of the shape of the icon. I definitely want to have like a family of colors that we can test out that would match the scientific style that we have now on the splash screen." (27 November 2026)

Nothing in the app changed: no edit to `index.html` or `desktop/`. Everything is in `tools/icon-lab/round2/` and this doc.

## How to pick
On the page: a palette row (P0 to P8), a grid of designs (I0 to I14), coloured dots on each card to put that design in any palette, a bench for the selected design (big preview, sizes 1024 to 16, the real pixels of 32 and 16 magnified, Dock on a dark and a light desktop, the four macOS 26 icon styles, Windows taskbar at 100 % and 150 %), stars on the recommendations, and a picks bar. Press **Pick** on what you like and paste the line, for example:

`Icon round 2: I5 P1 (default), I3 P5, I9 P2`

The first pick becomes the default shortcut icon; the others are added to the in-app icon picker.

## Built from
- The atom is the shipped geometry, unchanged: the three tapered rings, nucleus and satellite electron of Ocean Yellow, read from `desktop/icon-assets/source/icon-{L,M,S,XS}.svg` and the thinner W7 rings from `desktop/icon-assets/shortcut/shortcut-{L,M,S}.svg` (`extract_geom.py` writes `geom.json`). The electron keeps its cut-out halo (now a mask, so it works on gradients and detail).
- Colours come from the splash palettes in `index.html` (`SPLBG.PAL`, task SP1, v0.224) and the About window's colours (task AB1, v0.225); today's Ocean Yellow is P0 as reference.
- Tile: the macOS 26 shape is fixed by the system (IC1, `docs/app-icon-mac-styles.md`), so it is drawn as a squircle (superellipse, n = 5) and every shape change happens inside it. Mac renders sit on Apple's grid (824 px tile, 100 px margin) like `icon.icns`.

## Palettes
Contrast is WCAG (worst of the tile's two gradient ends). The mark parts need 3 : 1 (non-text graphics) at 16 px; all nine pass for rings, nucleus and electron (P8 nucleus exactly 3.0 after darkening it from #E8901A, which was 1.8). Dark tiles nearly vanish against a dark desktop (1.2 : 1), as dark icons do; those palettes draw a hairline rim in their detail colour on the tile edge (and macOS 26 adds its own light rim). Chart paper is the reverse: it vanishes on a light desktop and gets a dark rim.

| Code | Name | From | Tile (top → bottom) | Rings | Nucleus | Electron / accent | Detail lines | Rings : tile | Nucleus : tile | Electron : tile | Tile : light desktop | Tile : dark desktop |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| P0 | Ocean Yellow | Today's logo (reference) | #1450A8 | #FFFFFF | #FFD23A | #FFD23A | #BFD6FF | 7.7 | 5.3 | 5.3 | 6.3 | 2.2 |
| P1 | Ocean chart | Today's blue, deepened, with the splash's cyan | #1C62C8 → #0B2F6E | #FFFFFF | #FFD23A | #FFD23A | #9FC8FF | 5.8 | 4.0 | 4.0 | 10.4 | 2.9 |
| P2 | Orbit night | Splash S2, moons in resonance | #132044 → #070910 | #EAF1FF | #FFC43C | #4CC9F0 | #6096FF | 14.1 | 10.0 | 8.3 | 16.2 | 1.2 (+ rim) |
| P3 | Dipole cyan | Splash S1, dipole field (line and particle colours) | #0A3049 → #03111C | #E6F7FF | #FFC43C | #4CC9F0 | #4CC9F0 | 12.5 | 8.6 | 7.1 | 15.6 | 1.2 (+ rim) |
| P4 | Harmonograph lilac | Splash S5, harmonograph (periwinkle to lilac) | #1A1E48 → #07080F | #EEF0FF | #A99BFF | #78AAFF | #A99BFF | 14.0 | 6.7 | 6.8 | 16.3 | 1.2 (+ rim) |
| P5 | Chart amber | Splash S7, orbit chart | #1C2036 → #07080D | #F5F1E8 | #FFB627 | #FFD27A | #FFB627 | 14.2 | 9.1 | 11.3 | 16.3 | 1.2 (+ rim) |
| P6 | Spectrogram | Splash S6, spectrogram heat scale | #173A82 → #05070D | #EAF6FF | #FFD23A | #3FB8E8 | #3FB8E8 | 9.7 | 7.4 | 4.7 | 16.4 | 1.6 |
| P7 | Van Allen | About window: Earth and the radiation belts | #0F1A30 → #05080E | #E8EEF9 | #F0A878 | #6ED0EE | #7AAAFF | 14.9 | 8.7 | 9.8 | 16.4 | 1.2 (+ rim) |
| P8 | Chart paper | The orbit chart's ink colour as the ground, drawn like a printed plate | #F7F3EA → #E4DCCA | #1B2340 | #C8610A | #2F6BFF | #1B2340 | 11.3 | 3.0 | 3.3 | 1.1 | 15.2 (light: + rim) |

Tinted and Clear (macOS 26) throw the colours away by design; the page approximates them by keeping each part's brightness (tint #5EA8FF for Tinted, grey glass for Clear). The Dark style shows the same tile as Default, because the Icon Composer file of IC1 gives the Dark appearance the same fill.

## Designs
Each design draws three levels of detail: 128 px and up everything (L ring tier); 48 to 64 px only bold structure with thicker lines (M tier); 24 to 32 px the small master (S tier, fine lines dropped; dial and porthole keep their ring); 16 px the XS atom, with the zoomed designs going back to the whole atom as the shipped icon does at 16 to 20 px.

| Code | Name | Shape | Best palette | What it is |
|---|---|---|---|---|
| I0 | W7 today | Zoom and tilt | P0 | Today's shortcut icon (zoomed 1.5 times into the top right, tilted 6 degrees) with nothing added. The reference for each palette. |
| I1 | Graticule | Centred | P2 | The centred atom on a faint coordinate grid with heavier axes through the nucleus, as on a plotted chart. |
| I2 | Orbit ticks | Centred | P5 | A tick ring around the atom like the orbit chart on the splash: 120 marks, every tenth long. |
| I3 | Instrument dial | Dial inside the tile | P5 | A round instrument dial inside the tile: a bezel with degree graduations and the atom on the dial face. Reads as a circle even at 16 px. |
| I4 | Porthole | Lens inside the tile | P2 | A round lens in the tile; inside it the atom is zoomed in like W7, cut by the lens's edge. Outside the lens a faint grid. |
| I5 | W7 with measurements | Zoom and tilt | P1 | Today's W7 crop and tilt, with ruler marks along the left and bottom edges and a faint grid behind, like a plate in a lab notebook. |
| I6 | Breaking the frame | Atom breaks the frame line | P7 | A plot frame with axis ticks inside the tile; the atom is larger than the frame and its rings cut through the frame line. |
| I7 | Dipole field | Centred | P3 | Field lines of a dipole (r = L sin²θ), tilted 10 degrees through the nucleus, with trapped particles on them, as on the splash. |
| I8 | Harmonograph | Centred | P4 | A harmonograph trace (two slowing pendulums at 3 : 2) drawn faintly inside the tile, behind the atom. |
| I9 | Moons in resonance | Centred | P2 | The nucleus as the planet with three moons on orbits at 4 : 2 : 1 (radii by Kepler, 1 : 1.59 : 2.52), as on the splash. |
| I10 | Spectrogram band | Centred, raised | P6 | A band of spectrogram (the splash's 145 BPM pattern, kick, hats and a line) rising from the bottom of the tile; the atom above it. |
| I11 | Van Allen belts | Centred | P7 | Two soft radiation belts (warm inner, cool outer) and their field lines around the atom, tilted 9.2 degrees as in the About window. |
| I12 | Fine particles | Centred | P7 | The atom of the About window in the tile: the thin W7 rings plus fine particles running on the three orbits. At small sizes the particles drop out. |
| I13 | Specimen | Zoom and crop | P8 | The atom zoomed 1.2 times and set low left like a specimen under a reticle: cross-hair through the nucleus, a measuring circle, rulers along the top and right edges. |
| I14 | Polar chart | Tilt | P4 | A polar grid (rings every 120, spokes every 15 degrees) centred on the nucleus; the atom tilted 12 degrees on it, like a star chart. |

## Recommendations (stars on the page)
1. **I5 P1**, W7 with measurements in Ocean chart: today's W7 in a deeper ocean blue with ruler marks. Lowest-risk change; the Dock and taskbar still read as the icon users know.
2. **I3 P5**, Instrument dial in Chart amber: the strongest new silhouette, a circle inside the squircle that still reads at 16 px.
3. **I9 P2**, Moons in resonance in Orbit night: the splash the user picked first (S2).
4. **I11 P7**, Van Allen belts in Van Allen: the About window in an icon.
5. **I4 P2**, Porthole in Orbit night: a shape change inside Apple's rules.

Weak spots seen in the renders: the Ocean palettes (P0, P1) make the belt glow of I11 look muddy; the spectrogram band of I10 reads best in P6 and poorly on Chart paper; fine detail (graticules, particles) is invisible below 128 px by design.

## Files (`tools/icon-lab/round2/`)
| File | What |
|---|---|
| `extract_geom.py`, `geom.json` | the atom geometry from the shipped sources |
| `icons.js` | all palettes, designs, small-size rules and mock-ups as SVG (browser and Node) |
| `render.js`, `shrink.py` | render PNGs with `rsvg-convert`, then 256-colour dithered PNGs |
| `page.src.html`, `build_page.py`, `pick-page.html` | the pick page (self-contained build is what was published) |
| `renders/Ix/` | per design in its best palette: `Ix-Pn-{1024,512,128,64,32,16}.png` (full tile), `Ix-Pn-mac-1024.png` (Apple grid), `Ix-palettes.png` (all nine palettes), `Ix-dock-dark.png`, `Ix-dock-light.png`, `Ix-styles.png`, `Ix-taskbar-dark.png`, `Ix-taskbar-light.png` |
| `renders/family-all.png` | every design in every palette |

Regenerate: `python3 extract_geom.py && node render.js && python3 shrink.py && python3 build_page.py`. Stand-in app icons in the mock-ups are invented shapes, not real apps.

## What the implementation task does after the picks
1. **Default shortcut icon** = the first pick. Draw it at 1024 from `icons.js` (full tile for the layer art, Apple grid for flat files) and feed it through the IC1 pipeline: `desktop/icon-assets/mac-icon/make_icon.py` writes `AppIcon.icon` (fill = the palette's tile colour for Default, Dark and Tinted; for a gradient tile the fill becomes a gradient fill or the gradient goes into the layer), `desktop/scripts/build-mac-icon.sh` compiles `Assets.car`. Icon Composer draws all sizes from one set of layers on macOS 26, so the small master only reaches `icon.icns`, `icon.ico` and the favicons; check that the chosen design's large art survives being scaled to 16 there (I3, I4 and the centred designs do; the zoomed I0, I5, I13 lean on the small master).
2. Regenerate `icon.icns` and `icon.ico` with the four tiers (small master at 16 to 32), `dock-icon.png` (macOS 15 and older), `desktop/build/icon.png`, and the web favicons (`favicon-16/32/48`, `apple-touch-icon`, `icon-192/512`), `doc.icns`/`doc.ico` only if the user wants the document icon to follow.
3. **Picker**: add every pick to `desktop/icon-assets/picker/` (512 px PNG plus a 128 px thumb) and to `icons.json` as a new group "Science style" with plain names (for example "Instrument dial, Chart amber"), default stays marked.
4. Run the "Mac icon proof" job on macOS 26 with the new tile colour as the expected value (it checks Default and Dark), and `tools/ui-tests/taskAH_electron.js`.
5. App version, update note ("New app icon ... log out and in once if the old one still shows"), desktop build.
