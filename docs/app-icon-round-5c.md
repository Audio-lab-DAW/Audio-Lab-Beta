# AudioLab app icon, round 5c: the Earth and the Moon (task IC8)

Pick page: **AudioLab app icon, round 5c: the Earth and the Moon**, https://claude.ai/artifact/L7N8p7viVb8FAGqocQDncW

> "And how is this field called? And is it the earth or? Let's go with the second M5 logo. Let's pretend that is the yellow is the earth and the blue is the moon. Maybe we can do some variations with that information and keep it scientific." (28 November 2026, 01:14 Brussels)

Read as M5d (Field to the edge, the second design picked a minute earlier), with the round 5 note that rings and orbits are always **tapered, real 3D, never flat**. Ran beside task IC7 (round 5b, K5a tapered and M5d tapered); nothing of IC7's was touched. Nothing in the app changed: no edit to `index.html` or `desktop/`. Everything is in `tools/icon-lab/round5c/` and this doc.

## How to pick
On the page: a short explanation of the field with a labelled diagram and a table of what is to scale; the E row (M5d as picked, dashed, then E1 to E8), each with a P2 / P8 switch and a Pick button (as many as you like); a bench for the selected design (1024, 512, 128, 64; the Dock on a dark and a light desktop next to invented stand-in app icons; macOS 26 Default and Dark, Dark stays navy); a compare view with a wipe slider or side by side (E1 to E8, M5d, the small versions) at 1024 down to 16 px; the zoomed-in small versions ES1 to ES4 at 16 and 32 pt, 1x and 2x, magnified, plus 16 to 48 px and the Apple grid; the families (big icon at 128 and 64 with its small version); stars on the recommendations; the picks bar. Paste the line, for example:

`Round 5c picks: E1 E7 E2 P8 | small ES1 ES2`

(A palette is added only when it is not P2.)

## The answer to the question: what the field is
It is **Earth's magnetic field**, drawn as a **magnetic dipole**, the field of a bar magnet at the centre of the Earth. Each line follows r = L sin²θ (θ from the magnetic pole, L the distance in Earth radii where the line crosses the magnetic equator); the set of lines with one L is an "L-shell". So yes: the yellow centre is the Earth, and M5d is the textbook picture of its field. The real field near the Earth is close to this dipole; further out the solar wind reshapes it into the **magnetosphere**.

## Research (short, with sources)
| Fact | Value | Source |
|---|---|---|
| Dipole field lines | r = L sin²θ; the near-Earth field is roughly a dipole | NASA GSFC, "Exploration of the Earth's Magnetosphere" (D. Stern) |
| Magnetic axis against the rotation axis | about 9.2° in 2025 (geomagnetic north pole near 80.8° N); the 11° often quoted is an older value | NOAA NCEI, "Wandering geomagnetic poles"; BGS on the IGRF/WMM 2025 update; the About window (AB1) uses 9.2° too |
| Magnetopause (day side) | about 10 Earth radii toward the Sun, where the field's pressure balances the solar wind's | NASA GSFC Stern; NASA Science "Magnetosphere" |
| Magnetopause shape | Shue et al. (1997): r = r0 (2 / (1 + cos θ))^α, r0 ≈ 10, α ≈ 0.58 | Shue et al., JGR 102 (1997) |
| Magnetotail | stretched on the night side to hundreds of Earth radii; open lines in two lobes, a plasma sheet between | NASA Science blog "Earth's Magnetosphere and Plasmasheet" (2023) |
| Van Allen belts | inner belt (mostly protons) about L 1.2 to 2, peak near 1.5; outer belt (mostly electrons) about L 3 to 6, peak near 4 to 5; the slot between | NASA GSFC "The Radiation Belts" (Stern); NASA "Van Allen Belts"; Britannica |
| Moon | radius 1,737.4 km = 0.273 Earth radii; mean distance 384,400 km = 60.3 Earth radii; orbit inclined 5.145° to the ecliptic | NASA NSSDC Moon Fact Sheet |
| Moon in the magnetotail | crosses the tail around full Moon, about six days each month | NASA SVS 5623 "The Moon Passes Through Earth's Magnetotail"; NASA Science (2008) "The Moon and the Magnetotail" |

Sources:
- https://pwg.gsfc.nasa.gov/Education/Iexplore.html
- https://pwg.gsfc.nasa.gov/Education/Iradbelt.html
- https://science.nasa.gov/magnetosphere/
- https://science.nasa.gov/blogs/the-sun-spot/2023/09/26/earths-magnetosphere-and-plasmasheet/
- https://science.nasa.gov/biological-physical/stories/van-allen-belts/
- https://britannica.com/science/Van-Allen-radiation-belt
- https://www.ncei.noaa.gov/products/wandering-geomagnetic-poles
- https://www.bgs.ac.uk/news/update-to-essential-scientific-reference-maps-reveals-new-movement-of-the-earths-magnetic-field/
- https://nssdc.gsfc.nasa.gov/planetary/factsheet/moonfact.html
- https://svs.gsfc.nasa.gov/5623/
- Shue, J.-H. et al. (1997), "A new functional form to study the solar wind control of the magnetopause size and shape", J. Geophys. Res. 102(A5), 9497.

### What is to scale and what is drawn for legibility
| | Real | In the icons |
|---|---|---|
| Field lines | dipole r = L sin²θ | exact in E1 to E3, E5 to E7; in E4 and E8 a simple deformation (day side squeezed, night side stretched by L², thinned toward the plasma sheet; open lobe lines as curves from the polar cap into the tail) |
| Lines drawn | any L | M5d's: white L 2.7, 4.1, 5.9 (the Earth is 75.7 px, M5d's nucleus); fine L 3.4 to 13.6 |
| Magnetic tilt | 9.2° from the rotation axis | E3 exact; the field leans 12° in the picture, as in M5d |
| Van Allen belts | L 1.2–2 (peak 1.5), L 3–6 (peak 4.5) | to scale (E5, E8); drawn in the picture plane, behind the Earth, not stretched into the tail |
| Magnetopause | about 10 Earth radii | E4 to scale (Shue, r0 10); E8 at 6 so the Earth stays large |
| Moon size | 0.273 Earth radii | E6 and E8 to scale; 0.45 to 0.48 elsewhere (as M5d's electron) |
| Moon distance | 60.3 Earth radii | 5 to 9 everywhere: at true distance it would sit 4 to 5 tile widths from the Earth |
| Moon orbit | 5.1° to the ecliptic | 5° to a dotted hairline, seen from 13° above (E2, E5, E6) |
| Sunlight | parallel, from the Sun | from the left, 14° toward the viewer; Earth and Moon show the same phase (E4, E7, E8) |

## What is new in the drawing: the field in 3D, tapered
- Every line is a dipole line in a **meridian plane** turned round the magnetic axis (E1: 28° toward you), seen from 12° above. The point goes through the dipole tilt, the optional magnetosphere deformation, then the camera.
- Each line is a filled **ribbon** whose width and brightness follow its depth: toward you up to 1.66 times wider and full colour, away from you thinner and mixed toward the tile (solid colours, so no overlap seams). The far parts are drawn before the Earth (the planet hides them), the near parts after it (they pass over it). A line is thickest where it is closest to you, at the equator of the front half.
- The Moon's orbit (E2, E5, E6) is a tapered ribbon too: a circle seen from 13° above, inclined 5° to the ecliptic hairline, its far half behind the Earth, its near half passing below it.
- Below 32 px the ribbons become plain strokes per run (in front / behind), so nothing is lost to anti-aliasing.

## Designs
| Code | Name | What it is |
|---|---|---|
| E1 ★ | The dipole in 3D | M5d with its lines in 3D and tapered; the Moon where the electron was. |
| E2 ★ (P8) | The Moon on its orbit | The white ribbon is the Moon's orbit, 5° to the ecliptic; the field in blue, plus two lines in a second plane (a cage round the planet). |
| E3 | Two axes | E1 with the rotation axis dashed and the magnetic axis solid, 9.2° apart, a small arc between them. |
| E4 ★ | The magnetosphere | Sun to the left, solar wind lines, the magnetopause at 10 Earth radii (Shue), the day side squeezed, the tail stretched, the open lobe lines, the Earth lit from the left, the Moon in the tail. |
| E5 | Van Allen belts | The two belts as shaded bands (inner in the Earth's colour, outer in blue), fine field lines, the Moon on its inclined orbit. |
| E6 | The Moon to scale | Bigger Earth, the Moon at 0.273 Earth radii with a faint glow; the orbit drawn at 4.8 Earth radii. |
| E7 ★ | Day and night | E1 lit by the Sun from the left: both bodies half lit, the same phase; the tile's sheen from the same side. |
| E8 | The full plate | Magnetosphere, belts, sunlight and the true-size Moon in the tail; magnetopause drawn at 6. |

### Zoomed-in small versions (32 px and below)
| Code | For | What it is |
|---|---|---|
| ES1 ★ | E1, E3 | The Earth low left, axis 18°, two white lines (the outer runs out of the tile), the Moon on it top right. |
| ES2 ★ | E7 | ES1 with day and night halves. |
| ES3 | E2, E5, E6 | The Moon's orbit as a white ribbon round the Earth, one blue field line pair. |
| ES4 | E4, E8 | The day-side loops, the stretched tail out of the right edge, the Moon in it. |

Earth and Moon have whole-pixel diameters (Earth 5, 6, 7, 9 px at 16, 20, 24, 32; Moon 3 to 5) centred on the pixel grid; line widths in device pixels; the 2x pictures are drawn for their point size.

## Recommendations (stars on the page)
1. **E1 P2**: closest to the M5d picked, now a real 3D field with the far halves hidden by the Earth. The safest main icon. Small: **ES1**.
2. **E7 P2**: E1 lit by the Sun; the day and night halves make the yellow read as a planet at once. Small: **ES2**.
3. **E4 P2**: the real magnetosphere with the Moon in the tail; the most scientific picture that still reads in the Dock; best as a picker option or for the About window.
4. **E2 P8**: the inclined orbit as the white ribbon reads cleanly on Chart paper.

Weak spots seen in the renders: E4's Earth is small (the price of the true 10 Earth radii); E8 is the busiest and its belts become soft clouds at 64 px; the true-size Moon of E6 and E8 is about 2 px in the Dock; E5's belts are faint on P2 and strong on P8; the night half of E7 makes the Earth look smaller at 64 px; ES4 at 16 px is a dot with arcs (the tail reads from 24 px); ES3 at 16 px looks a little like Saturn.

## Files (`tools/icon-lab/round5c/`)
| File | What |
|---|---|
| `icons5c.js` | the 3D dipole, tapered ribbons, spheres lit by the Sun, belts, magnetopause and tail; E1 to E8; reuses round 5's palettes, Dock and macOS mock-ups (round 5 unchanged) |
| `small5c.js` | ES1 to ES4 (16 to 64 px, 1x and 2x, full tile or Apple grid) |
| `render5c.js`, `sheet5c.js`, `sheet_small5c.py`, `shrink.py` | PNGs with `rsvg-convert`, overview sheets, 256-colour PNGs |
| `page.src.html`, `build_page.py`, `pick-page.html` | the pick page (the self-contained build is what was published) |
| `renders/<id>/` | per design and palette: `-{1024,512,128,64}.png`, `-mac-1024.png`, `-dock-dark.png`, `-dock-light.png`, `-styles.png` |
| `renders/small/` | `<id>-<P>-{16,20,24,32,48}.png`, `-32-at16.png`, `-64-at32.png`, `-mac-{16,32}.png` |
| `renders/sheet-big-{P2,P8}.png`, `renders/sheet-small-{P2,P8}.png` | every design at 320 and 64; every ES magnified |

Regenerate: `node render5c.js && python3 shrink.py && python3 build_page.py`.

## After the pick
The E picks join round 5b's choice as the M5d candidates: one becomes the Main or the Other (the rest can go into the picker's Dipole field group), with its ES as the small version, through the IC1 pipeline as written in docs/app-icon-round-5.md ("What the implementation task does after the pick"): Dark stays navy, a P8 pick needs the P8N entry, `index.html` edits wait while `desktop/release-freeze.json` is on main, promotion only through the release gate.
