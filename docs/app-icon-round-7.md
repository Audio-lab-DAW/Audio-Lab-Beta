# AudioLab app icon, round 7: the Earth, the Moon and the belts (task IC11)

Pick page: **AudioLab app icon, round 7: the Earth, the Moon and the belts**, https://claude.ai/artifact/DWG6igbr2v1H5WoYrhfzpM

The user's notes this round answers are at the end of docs/app-icon-round-6.md (28 November 2026, 18:25 Brussels): rethink the whole shape, use all the design research, stay 3D, the Earth and the Moon with the Van Allen belts and the field and the Moon's orbit, the liked E6c, E6d and E6e, small icons in the KS8 direction, a simpler pick page.

Nothing in the app changed: no edit to `index.html`, `desktop/` or `native/`. Everything is in `tools/icon-lab/round7/` and this doc.

## How to pick
The page has one grid of seven designs (G1 to G7), one row of four small icons (S1 to S4) with the Finder list and a browser tab, and a picks bar. Click a design to see it at 1024, 128 and 64 px and in the small Dock on a dark and a light desktop. A switch shows P8 Chart paper. Stars mark the recommendations, which are preselected. Paste the line, for example:

`Round 7 picks: main G7 | other G1 | small S1`

(`P8` is added when Chart paper is on.)

## Design rules taken from the earlier research
From rounds 2 to 6, docs/app-icon-small-sizes.md, docs/app-icon-mac-styles.md, docs/design-languages-research.md, the LOOK tokens (the project doc claude/audiolab-look-tokens.md; `docs/look-tokens.md` does not exist in the repository) and Apple's guidance. The earlier docs hold numbers (contrast, sizes, the grid); the general rules 1, 2 and 5 were not written down before and are stated here.

1. **Silhouette first.** Each design is one shape that can be named in three words (a cut ring, a half shell, a bow). Round 6's lopsided loops had no such shape.
2. **One focal point.** The Earth is the only warm colour and the brightest thing; the belts' front is cleared or cut away so nothing veils it. The Moon is the second accent, always small and blue, in the upper right where it can be.
3. **Light from one side.** One light from the upper left, in front, for the spheres, the tubes, the belts and the tile's sheen (round 5: one light drives highlights, sheen, edge and shadow).
4. **Depth by overlap and value, not by outlines or taper.** Things pass in front of and behind the Earth; far parts are darker and bluer. Widths follow true perspective only: the exaggerated taper of rounds 5b and 6 is gone.
5. **Few elements.** Earth, Moon, belts, and at most one of orbit or field lines (two bold lines per side at most). No particles, no hairline fans.
6. **Filled, overlapping shapes** rather than thin lines (Apple: filled overlapping shapes, vary opacity in the foreground, avoid extremely thin line weights). Belts are bodies; cut faces are solid crescents.
7. **How 3D bands and orbits read at icon size.** A see-through torus reads when its skin is brighter than its middle (a bright rim, a clear centre). A cutaway reads better than a whole torus, because the crescent section is a flat, filled shape. An orbit reads as a perspective ellipse only when it passes in front of something and behind something, and when it is not centred like Saturn's ring: the Moon sits on it.
8. **Levels of detail** (rounds 2 to 5): 128 px and up everything; 48 to 96 px fewer lines, 1.5 times heavier, denser belts, a larger Moon; 32 px and below a separate small icon.
9. **The macOS 26 grid and glass** (app-icon-mac-styles.md): 1024 canvas, 824 tile, 100 margin; the layer is full-bleed and macOS cuts the shape. Dark stays navy (#132044, written as `fill-specializations` only). The sheen and light edge are drawn, so Icon Composer's specular stays off (one or the other, never both).
10. **Contrast and glow** (round 2, round 3): mark parts 3:1 against the tile; a soft #6096FF centre glow on P2; glow under the Earth, not over the belts.
11. **Small icons** (app-icon-small-sizes.md): a separate drawing per size, whole-pixel diameters on the pixel grid, line widths in pixels, a pixel of ground between parts, 2x is its point size's drawing, tested at 100 % on dark and light.

## Research: the belts, the field, the Moon
| | Real | Source |
|---|---|---|
| Inner belt | about 1 to 3 Earth radii from the centre at the equator, mostly protons | Fitzpatrick; NASA SVS 11212 |
| Outer belt | about 3 to 9 or 10 Earth radii, strongest near 4 to 5, mostly electrons | Fitzpatrick; Wikipedia |
| Slot | between them; sources give 2 to 4 Earth radii or L 2.5 to 4 (they do not agree on one number) | Wikipedia (belt, L-shell) |
| Shape | two "donut-shaped regions"; crescent sections, because they follow dipole field lines | NASA SVS 11212 |
| Third belt | a temporary storage ring, September 2012, about four weeks | NASA, Van Allen Probes |
| Field line | r = L cos²(latitude), L the distance at the equator in Earth radii | Fitzpatrick |
| Dipole tilt | 9.21° to the rotation axis (WMM 2025; pole at 80.79° N) | NOAA NCEI |
| Axial tilt | 23.44° | NASA Earth fact sheet |
| Magnetopause | nose 10 to 11 Earth radii, bow shock 3 to 4 further out | NASA GSFC |
| Magnetotail | far beyond the Moon's orbit; the Moon is in it about six days a month | NASA; ScienceDaily reprint of a 2008 NASA story |
| Moon | 384,400 km (60.3 Earth radii), 5.145° to the ecliptic, eccentricity 0.0549, 0.2727 of the Earth's radius | NASA Moon fact sheet |

How illustrators draw them: NASA's visualisations cut the belts open so the nested sections show, and use one colour per belt (SVS 4048, 11239, the cutaway graphic); the magnetotail piece uses a few lines over one soft tail shape with the Moon's orbit crossing it (SVS 5623). No source was found on perspective ellipses round a sphere at icon size; rule 7 above is this round's own observation from the renders.

## What is new in the drawing
`r7.py` is a small renderer of a real scene in Earth radii: one true perspective camera, a depth buffer for the spheres and tubes, and the belts and the magnetopause as volumes marched along every pixel's ray (denser in a skin under the surface, so they look like lit glass; a cut shows a capped crescent). In whole belts a soft window is cleared toward the viewer so the Earth stays crisp (an illustrator's ghosting, not physics).

## Designs
| Code | Name | What it is |
|---|---|---|
| G1 ★ | Belts cut open | Both belts with the front third cut away, the crescent sections showing; the Moon on its orbit behind. |
| G2 | Moon on its orbit | Whole glass belts; the Moon's orbit passes behind and in front, the Moon near. E6e's successor. |
| G3 | Magnetosphere | The magnetopause as a see-through bow, the field squeezed on the Sun's side and drawn into the tail, the Moon behind. E6d's successor. P2 only (muddy on paper). |
| G4 ★ | Globe, two axes | Close on a globe with graticule, rotation axis dashed, magnetic axis solid, 9.21° apart; belts cut open behind. E6c's successor. |
| G5 | From above | Seen from 58° above: the two rings, the slot between, the orbit round them. |
| G6 | Close-up | The big version of the small icons: the Earth low left, a belt section and two field lines toward the Moon top right. |
| G7 ★ | Half shell | The belts cut in half; the field lines lie on the cut. The picked M5d emblem as a 3D object, symmetric. |

What is to scale and what is drawn for legibility:

| | Real | In the icons |
|---|---|---|
| Field lines, belt sections | r = L cos²(latitude) | exact shape |
| Belts | inner 1 to 3, outer 3 to 10 Earth radii | inner L 1.4 to 1.9, outer L 2.3 to 3.7, so the Earth stays large |
| Magnetic axis | 9.21° from the rotation axis, itself 23.44° from the ecliptic's normal | exact in G1, G2, G4, G5; G3 and G7 lean 9 and 11°, G6 is turned toward the Moon |
| Moon's orbit | 60.3 Earth radii, 5.145° to the ecliptic | 4.2 to 4.5 Earth radii; the tilt exact |
| Moon, size | 0.273 Earth radii | 0.40 to 0.50 |
| Magnetopause | 10 to 11 Earth radii, Shue's shape | 3.75, Shue's shape (exponent 0.58); the field lines in G3 are a dipole stretched by hand, a sketch and not a model |
| Light | the Sun, one phase for every body | one light for everything; from the upper left for the picture's sake, also in G3 where the Sun is to the left |

### Small icons (32 px and below)
The KS8 direction: zoomed in, the Earth in the bottom left corner (half the tile wide: 8, 10, 12, 16 px at 16, 20, 24, 32), the Moon in the top right (4, 5, 6, 8 px), both lit, both with a glow. Drawn per size at 1x and 2x, on the full tile and on the Apple grid (`small7.py`).

| Code | Name | What it is |
|---|---|---|
| S1 ★ | Field loops | One bold field line from the Earth round through the Moon. |
| S2 ★ | Belt | A filled belt section between the Earth and the Moon; a second, warm one at 32 px. |
| S3 | Orbit | The Moon's orbit: far half thin behind the Earth, near half bright across its limb. |
| S4 | Two bodies | Only the Earth, the Moon and the strongest glow. |

## Recommendations (stars on the page)
1. **Main G7 P2** with **S1**: the clearest silhouette, symmetric, holds at 64 px, and it is M5d (picked in round 5) made solid. S1 is its line through the Moon.
2. **Other G1**: the most 3D, with the orbit; or **G4** if the globe and its two axes matter most.
3. **S2** if the small icon should be a filled shape rather than a line.

Weak spots seen in the renders:
- The Earth is about a fifth of the tile in G1, G2, G3 and G7; at 64 px it is 12 px wide.
- G4's graticule, dashed axis and angle mark are dropped below 120 px.
- G3's field lines are thin at 128 px, and the bow is cut by the tile's left edge.
- G5 is the flattest of the seven; its orbit touches the tile's left edge.
- G6's lower belt section is cut by the corner.
- The cut faces carry a fine grain at 1024 px (from the ray marching).
- P8: the belts are blue-grey washes; G3 was left out.
- S2's belt can be read as a crescent moon. At 16 px on the Apple grid (a 14 px tile) S1's loop is a pixel from the Moon and the edge.
- The 32 px Dock picture in the detail view is the big design scaled, shown to judge it; the shipped icon uses the small icon there on 1x screens.

## Files (`tools/icon-lab/round7/`)
| File | What |
|---|---|
| `r7.py` | the renderer: camera, depth buffer, spheres, tubes, the volume march, belt and shell volumes, the tile |
| `designs7.py` | palettes P2 and P8, G1 to G7, the tile's glass, the Apple grid; `render(id, pid, px, frame)` |
| `small7.py` | S1 to S4: `small(id, pid, pt, scale, frame)` |
| `render7.py` | every picture into `renders/` and `renders/manifest.json` (about 25 minutes on two cores) |
| `page.src.html`, `build_page.py`, `pick-page.html` | the pick page (the self-contained build is what was published) |
| `renders/big/` | `<id>-<P>-1024.webp`, `-512.webp`, `-128.png`, `-64.png`, `-mac-128.png`, `-mac-64.png`, `-mac-32.png` |
| `renders/small/` | `<id>-<P>-<pt>@<s>x[-mac].png` |

Regenerate: `python3 render7.py && python3 build_page.py` (Python 3 with numpy, scipy and Pillow).

## What the implementation task does after the pick
1. **Main** becomes the default app icon, drawn at 1024 by `designs7.render` (full tile for the Icon Composer layer, Apple grid for the flat files) through the IC1 pipeline (`desktop/icon-assets/mac-icon/make_icon.py`, `desktop/scripts/build-mac-icon.sh`). Dark stays navy: #132044 as `fill-specializations` only. A P8 Main needs a night palette for Dark (round 7 has none; P8N of round 6 is the base). Specular stays off, the edge is drawn.
2. **The small icon** replaces S1 of round 3 at 32 px and below: `icon.icns` 16 and 32 pt at 1x and 2x (`small(id, pid, pt, 2, 'mac')` for the 2x slots), `icon.ico` 16, 20, 24, 32, the doc icons' small tiers, the favicons.
3. **Other** goes into the picker (`desktop/icon-assets/picker/`, 512 px, a 128 thumb, small sizes from the same small icon), group "Earth and Moon". J3 stays as an option.
4. The 32 removals of round 5 leave `icons.json`'s list; their pictures stay resolvable and the stored choice is never reset.
5. Regenerate the Mac, Windows and browser files on the macOS runner, run the "Mac icon proof" job and `tools/ui-tests/taskAH_electron.js`. Still to check on a Mac: whether macOS 26 uses the .icns small slots in the Finder list when `Assets.car` is present.
6. One line in `desktop/update-notes.txt`; any `index.html` edit waits while `desktop/release-freeze.json` is on main; installed apps get it through the release gate only.

## Sources
- NASA SVS, Van Allen Probes and the belts: https://svs.gsfc.nasa.gov/11212 , https://svs.gsfc.nasa.gov/4048 , https://svs.gsfc.nasa.gov/11239/
- NASA, cutaway graphic of the Van Allen belts: https://www.nasa.gov/image-article/cutaway-graphic-of-van-allen-belts/
- NASA, the third belt: https://www.nasa.gov/news-release/nasas-van-allen-probes-reveal-a-new-radiation-belt-around-earth
- R. Fitzpatrick (University of Texas), Plasma Physics, Van Allen radiation belts: https://farside.ph.utexas.edu/teaching/plasma/Plasma/node23.html
- Wikipedia, Van Allen radiation belt, L-shell, Magnetosphere: https://en.wikipedia.org/wiki/Van_Allen_radiation_belt , https://en.wikipedia.org/wiki/L-shell , https://en.wikipedia.org/wiki/Magnetosphere
- NOAA NCEI, wandering geomagnetic poles (WMM 2025): https://www.ncei.noaa.gov/products/wandering-geomagnetic-poles
- NASA, Earth and Moon fact sheets: https://nssdc.gsfc.nasa.gov/planetary/factsheet/earthfact.html , https://nssdc.gsfc.nasa.gov/planetary/factsheet/moonfact.html
- NASA GSFC, the magnetosphere: https://pwg.gsfc.nasa.gov/Education/Iexplore.html ; https://www.nasa.gov/image-article/earths-magnetosphere-3
- The Moon in the magnetotail: https://www.sciencedaily.com/releases/2008/04/080420123319.htm ; NASA SVS https://svs.gsfc.nasa.gov/5623/
- Shue et al. (1997), JGR 102(A5), 9497 (the magnetopause shape; as cited in round 5c, not reopened)
- Apple Human Interface Guidelines, App icons: https://developer.apple.com/design/human-interface-guidelines/app-icons
- Smashing Magazine, Easy steps to better logo design: https://www.smashingmagazine.com/2016/05/easy-steps-to-better-logo-design/
- Font Awesome, Designing icons, simplification of form: https://blog.fontawesome.com/designing-icons-simplification-of-form/
