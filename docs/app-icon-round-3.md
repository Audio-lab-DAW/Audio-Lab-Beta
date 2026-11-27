# AudioLab app icon, round 3: dipole field (task IC3)

Pick page: **AudioLab app icon, round 3: dipole field**, https://claude.ai/artifact/Hmz594R6X1gEPmudeiCGV4

> "For the logo, I like the I7 dipole field, and for the colors, I like P2 Orbit Night, and I like P8 Chart Paper. Just make sure that the field in the center should be centered with a circle. So you have the yellow circle of the logo, and the field should be perfectly around that as if it's the Earth. Let's also use the porthole. That's I4. And let's pick W7 with measurements [I5]. ... I do like the fine particles [I12]. We might use that later for an animated version." (27 November 2026, 18:09 Brussels)

Nothing in the app changed: no edit to `index.html` or `desktop/`. Everything is in `tools/icon-lab/round3/` and this doc.

## How to pick
On the page: the three palettes with their contrast, a grid of designs J1 to J11 (each with a P2 / P8 switch), a bench for the selected design (big preview, sizes 1024 to 16, the real pixels of 32 and 16 magnified, Dock on a dark and a light desktop, the macOS 26 icon styles, Windows taskbar at 150 % and 100 %), a small-size table of every design, the animated preview (marked as a later option), stars on the recommendations, and a picks bar. Press **Pick** and paste the line, for example:

`Icon round 3: J2 P2 (default), J7 P2, J10 P8`

The first pick becomes the default shortcut icon; the others are added to the in-app icon picker.

## The fix to I7
- In round 2 the field was drawn around the tile's centre (512, 512), but the shipped atom carries an optical offset (`off` in `geom.json`: -11, -22.6 at the L tier), so with the atom at 0.9 the nucleus sat at about (502, 492): the field ran 10 px left and 20 px above the nucleus. The lines were also cut at a fixed radius of 100 instead of meeting a surface.
- Now each design decides where the **nucleus** goes, `placeAt()` positions the atom so its nucleus lands exactly there for every ring tier (L, M, S, XS and the W7 tiers, each with its own offset), and the field r = L sin²θ is drawn around that same point.
- Every line starts and ends on a circle a clean gap outside the nucleus (24 px at full size, 30 to 40 px at small sizes): the nucleus is the planet, as on the splash's dipole picture (SP1, S1), where the lines begin at the planet's surface. The innermost line crosses the equator at 150 px, about twice the nucleus radius (69 px).
- Two short stubs on the magnetic axis mark the poles (full size only).
- Inside the ring envelope (radius 300 at atom scale 0.86) only the innermost loops are drawn in full; the outer lines come out from behind the atom. Drawing all the line feet between the rings made a comb around the nucleus. The lines pass under the rings with a cut (knock-out mask, as in round 2's I6), and their feet fade to 30 % at the surface.
- Upright (J1) and tilted 10 degrees like the Earth's magnetic axis (9.2 degrees today, WMM2025, as in the About window); only the field leans, the atom stays as shipped.
- Trapped particles: two per line, set near their mirror points (where a bouncing particle spends most time), alternating nucleus and electron colours; none behind the atom.
- Rings: kept (J1, J2), thinned (J3: W7 rings at 90 %), or replaced by the field (J4: three field lines in the ring colour become the orbits, the electron rides the middle one 60 degrees from the axis, where the shipped electron sits).

## Palettes
Contrast is WCAG (worst of the tile's two gradient ends). Field lines are drawn at 44 to 66 % strength on top of the listed value.

| Code | Name | Tile (top → bottom) | Rings | Nucleus | Electron | Field / detail | Rings : tile | Nucleus : tile | Electron : tile | Field : tile | Tile : light desktop | Tile : dark desktop |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| P2 | Orbit night | #132044 → #070910 | #EAF1FF | #FFC43C | #4CC9F0 | #6096FF | 14.1 | 10.0 | 8.3 | 5.5 | 16.2 | 1.2 (+ rim) |
| P8 | Chart paper | #F7F3EA → #E4DCCA | #1B2340 | #C8610A | #2F6BFF | #1B2340 | 11.3 | 3.0 | 3.3 | 11.3 | 1.1 (+ rim) | 15.2 |
| P8N | Chart paper, night (proposed Dark entry of P8, new) | #1E2742 → #0C1020 | #F3EEE2 | #F08A2C | #6E9BFF | #D9CDB4 | 12.7 | 5.9 | 5.5 | 9.4 | 15.4 | 1.1 (+ rim) |

P2 and P8 are unchanged from round 2. P2 also has a soft glow (#6096FF at 20 % in the centre).

### macOS 26 styles
- **P2**: Default and Dark are the same navy tile. The Icon Composer file of IC1 gives the Dark appearance the same fill, so Dark stays blue.
- **P8** is a light tile, so Dark needs a decision. The page shows three versions. *Kept as paper*: the same fill in Dark, so the icon stays bright among dark ones. *macOS automatic* (approximation): with no Dark entry, macOS 26 replaces the paper with its black tile and the dark ink nearly vanishes, so this one is not an option. *Proposed P8N*: paper and ink swapped, the same orange and blue made lighter. P8N needs its own dark fill and its own dark layer in `AppIcon.icon`.
- **Tinted and Clear** are the system's own treatment for every app and are approximated on the page. No app can keep its colours there.

## Designs
Levels of detail: 128 px and up everything; 48 to 64 px the bold structure (three field lines, M ring tier, ticks thinned to 24); 24 to 32 px the small master (one bold field arc each side of the atom, drawn only round the magnetic equator so it clears the rings; S ring tier; no particles, ticks or grid); 16 px the XS master (XS atom and one heavier arc pair). The nucleus and the field's two lobes stay readable at 32; at 16 the arcs read as a soft oval behind the atom, and J4 / J10 stay clearest (nucleus, lobes, dot).

| Code | Name | Group | What it is |
|---|---|---|---|
| J1 | Field, upright | Field fixed | I7 fixed: field centred on the nucleus, axis upright, rings and electron as shipped. |
| J2 | Field, tilted 10° | Field fixed | The same with the magnetic axis leaning 10 degrees like the Earth's. |
| J3 | Field, thin rings | Field fixed | Tilted field with the thinner W7 rings at 90 %; more room for the field. |
| J4 | Field as orbits | Field fixed | Rings replaced by three field lines in the ring colour; the electron rides the middle one. |
| J5 | Porthole, field | Porthole | I4 + I7: the atom centred in the lens, the field running out to the lens and cut by its edge; faint grid outside. |
| J6 | Porthole, zoomed | Porthole | Closest to I4: atom zoomed 1.16 times and set low left in the lens, field centred on its nucleus. |
| J7 | Porthole dial | Porthole | The porthole with 120 measurement ticks round the rim (every fifth and tenth longer); field centred inside. |
| J8 | Field with measurements | Measurements | J2 with I5's elements: faint grid, rulers on the left and bottom edges, the magnetic equator dashed with an unlabelled tick at each field line (the L-shells), a small scale bar. No text. |
| J9 | W7 field | Measurements | I5 + I7: today's W7 crop and tilt with rulers and grid, the field centred on its nucleus and cut by the tile edge. |
| J10 | Field-orbit dial | Porthole | J4's mark inside J7's dial. |
| J11 | I5 for comparison | Reference | Round 2's I5 unchanged, in P2 and P8. |

## Recommendations (stars on the page)
1. **J2 P2** (first choice), Field tilted 10°, Orbit night: what was asked, the field centred on the yellow nucleus like the Earth, shipped atom on top; Dark stays navy.
2. **J7 P2**, Porthole dial: porthole and measurements in one, a circle in the squircle that still reads at 16 px.
3. **J8 P8**, Field with measurements in Chart paper: a printed plate; needs the P8N Dark entry.
4. **J10 P8**, Field-orbit dial: the most distinctive mark, cleanest at 16 px.
5. **J4 P2**, Field as orbits: the new mark alone; a bigger step away from today's atom.

Weak spots seen in the renders: J6 and J9 are busy at 64 px (zoomed rings plus field); J9 leans on the W7 small master at 16 px; at 16 px the field arcs of J1 to J3 merge into an oval around the atom.

## Animated version (later option, I12)
Not part of the pick; the static icon does not depend on it. On the page: J2, J7 and J4 animated in their current palette at preview size, 64 and 32 px. Trapped particles bounce between their mirror points along the field lines; on J2 and J7, fine particles also run on the three orbits as in the About window's atom (FATOM). The page measures its own drawing time live.

| Where | macOS | Windows | CPU cost |
|---|---|---|---|
| Dock or taskbar icon while the app runs | Possible: `app.dock.setIcon` 10 to 15 times a second, or a native `NSDockTile` view. Only while running; Finder, Launchpad and the closed app's Dock tile stay static. While a picture is set, macOS 26 does not apply Tinted or Clear (IC1). | No real support: swapping the window icon many times a second works but reloads it into the shell each time and flickers on some setups; the overlay badge is 16 px only. Keep it static. | Drawing a 256 px frame takes about 0.1 ms (measured: headless Chromium, 2-core cloud machine, no graphics card; 9 preview canvases 0.6 ms together). Encoding it as PNG takes about 8.7 ms a frame, about 10 % of one core at 12 fps. Passing raw pixels (`nativeImage.createFromBitmap`) costs about 0.4 ms to read them. The Dock's own redraw has to be measured on a Mac. Stop the animation when the app is hidden, with reduce motion, and at the Light level. |
| Splash | Already a canvas animation (SP1); this would be another picture, or new dots for the dipole picture. | Same. | The splash's dipole picture costs 0.10 to 0.19 ms a frame (v0.224 log); this adds about the same. |
| About window / menu card | Already runs FATOM only while open; the field particles would join it there. | Same. | Only while open; stands still at the Light level and with reduce motion. |

## Files (`tools/icon-lab/round3/`)
| File | What |
|---|---|
| `icons3.js` | palettes, designs, placement on the nucleus, field drawing, small-size rules, animation geometry and mock-ups (browser and Node); reads `../round2/geom.json` |
| `render3.js`, `shrink.py` | PNGs with `rsvg-convert`, then 256-colour dithered PNGs |
| `page.src.html`, `build_page.py`, `pick-page.html` | the pick page (the self-contained build is what was published) |
| `renders/Jn/` | per design and palette (P2, P8): `Jn-Pp-{1024,512,128,64,32,16}.png` (full tile), `Jn-Pp-mac-1024.png` (Apple grid), `Jn-Pp-dock-dark.png`, `Jn-Pp-dock-light.png`, `Jn-Pp-styles.png` (for P8 with the Dark choices and P8N), `Jn-Pp-taskbar-dark.png`, `Jn-Pp-taskbar-light.png` |
| `renders/sheet-all.png` | every design in P2 and P8 at 256 with 64, 32 and 16 |

Regenerate: `node render3.js && python3 shrink.py && python3 build_page.py`. Stand-in app icons in the mock-ups are invented shapes, not real apps.

## What the implementation task does after the pick
1. **Default shortcut icon** = the first pick, drawn at 1024 from `icons3.js` (full tile for the layer art, Apple grid for flat files) and fed through the IC1 pipeline. `desktop/icon-assets/mac-icon/make_icon.py` writes `AppIcon.icon`; `desktop/scripts/build-mac-icon.sh` compiles `Assets.car`.
   - **P2**: the same navy fill for Default, Dark and Tinted, written only as `fill-specializations` (IC1's lesson), so Dark stays blue. The gradient goes into the layer or a gradient fill.
   - **P8**: Default gets the paper fill. Dark gets the P8N fill and a dark layer of its own (P8N colours), unless the user wants the paper kept in Dark.
2. Regenerate `icon.icns` and `icon.ico` with the four tiers (the small masters at 16 to 32 px), `dock-icon.png` (macOS 15 and older), `desktop/build/icon.png`, and the web favicons (`favicon-16/32/48`, `apple-touch-icon`, `icon-192/512`). Icon Composer draws all sizes from one set of layers on macOS 26, so the small masters only reach `icns`, `ico` and the favicons.
3. **Picker**: add every pick to `desktop/icon-assets/picker/` (512 px plus a 128 px thumb) and to `icons.json` as a group "Dipole field" with plain names ("Dipole field, Orbit night"); mark the default.
4. Run the "Mac icon proof" job on macOS 26 with the new tile colour as the expected value for Default and Dark (P8N's for Dark when P8 is chosen), and `tools/ui-tests/taskAH_electron.js`.
5. Raise the app version, write the update note ("New app icon ... log out and in once if the old one still shows"), and run the desktop build. The animated icon stays a separate later task.

## The user's picks (27 November 2026, 19:25 Brussels)

In the user's words: "For the big icon round 3, let's go with J3 actually. I like that it's a little bit transparent, like you can see the rings in full and sense its energy. Maybe it makes sense that it's a little bit transparent. So that's cool. Let's have J4 as an extra option in the options. Same for J6. And have J10 and J8 also in the options. And then for the main logo, I think the 32 pixel one should be the zoomed in tilted one. And should be optimized a little bit more for the smaller, because the rings look way too fat on the 32 pixel."

- **Default app icon: J3** (field with the thinner, slightly transparent rings), in Orbit night (P2) as the user's palette pick; Dark stays navy/blue.
- **Extra options in the in-app icon picker:** J4, J6, J8 and J10 (in P2, and in P8 Chart paper where the round marked that palette as strong: J8 and J10).
- **Small sizes (32 px and below):** use the zoomed-in, tilted crop (like W7) instead of the whole mark, redrawn for small sizes with thinner rings (the rings are far too fat at 32 px today).
