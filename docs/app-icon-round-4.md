# AudioLab app icon, round 4: J3 and J4, and the small J9 (task IC5)

Pick page: **AudioLab app icon, round 4: J3 and J4, and the small J9**, https://claude.ai/artifact/TDpdQhRRWbv5p8rrLFKriu

> "We are picking J3 as our main logo. And we will keep J4 in the background. Let's actually work on J3 and J4 together. I actually can decide which one's better. I do like J4. We'll keep J6 as an extra in the options. Same for J8. And let's use W7 field, that is J9. We'll use that for the 32 pixels, maybe the small one. And let's keep J10 in the options. We'll keep the animated particles for later. Give me the next round." (27 November 2026, 22:37 Brussels)

Nothing in the app changed: no edit to `index.html` or `desktop/`. Everything is in `tools/icon-lab/round4/` and this doc.

## How to pick
On the page: the J3 row (J3 as shipped, then K1 to K5), the J4 row (J4 of round 3, then M1 to M5), the hybrids (H1, H2), each with a P2 / P8 switch; a bench for the selected design (1024, 512, 128, 64; the Dock on a dark and a light desktop next to invented stand-in app icons; macOS 26 Default and Dark); a **compare view** (any two designs, the round 3 references and the S variants included, at the same size from 1024 to 16 px, with a wipe slider or side by side; 64 px and below show the real pixels); the **small-size section** (S1 to S4 and IC4's current small master at 16 and 32 pt, 1x and 2x, magnified, plus 16 to 48 px and the Apple grid; the family strip with the big Main and Alt next to the small one; a Windows taskbar, a browser tab and a one-colour menu-bar template); the row "stays in the picker" (J6, J8 P2 and P8, J10 P2 and P8); stars on the recommendations; the picks bar. Give one design **Main**, one **Alt** and one S **Small**, then paste the line, for example:

`Round 4 picks: main K1 | alt M2 | small S1`

(A palette is added only when it is not P2, for example `main K3 P8`.)

## What changed in the drawing
- Round 3 drew the rings from the shipped outline paths (`round2/geom.json`), so their weight could not change. Round 4 draws them as **stroked ellipses with the same geometry** (rx 360, ry 150 in the mark frame at -30, 30 and 90 degrees round the nucleus; the shipped W7 rings are about 37 units wide, 32 px in the tile at J3's atom scale 0.86). Ring weight, transparency, glass style, the electron's ring and place, and the nucleus size become parameters.
- Each ring is drawn on its own with its own opacity, so the crossings show brighter: the transparency the user liked in J3.
- The dipole field is round 3's: r = L sin²θ centred on the nucleus, from a surface circle a gap outside it, the feet faded, the outer lines hidden inside the ring envelope, cut under the rings (or not, where the field is meant to show through).
- In J4's family each half of each field orbit is its own path, so transparent orbits brighten where they gather at the poles.
- Levels of detail: 128 px and up everything; 48 to 96 the bold structure (three field lines, rings 1.3 times heavier, no particles); 32 and below the small master (S row).

## Designs
### J3 refined (K)
| Code | Name | What changed from J3 |
|---|---|---|
| K1 ★ | Lighter rings | Rings 24 px instead of 32, 78 % instead of 90 %; the field as J3 (six lines, tilt 10°). |
| K2 | Glass rings | Each ring a translucent band (42 %) with a thin bright core, like a lit glass tube; nucleus glow; the field passes under the rings without a cut. |
| K3 ★ | Wide field | Atom 10 % smaller; seven field lines, the outer ones running out past the tile edge and cut by it; inner lines stronger (74 % to 40 %); tilt 12°; nucleus glow. |
| K4 | Planet | Nucleus a fifth bigger, lit as a sphere with a glow; electron smaller, at the top of the upright ring; rings 26 px at 84 %. |
| K5 | Depth (macOS 26) | K1 with a light edge along the top of the tile and a faint sheen, nucleus and electron lit as spheres, a soft shadow under the atom. |

### J4 refined (M)
| Code | Name | What changed from J4 |
|---|---|---|
| M1 | Lighter orbits | Orbits 17, 15, 13 px instead of 22, 19, 16; four fine lines; electron a touch smaller. |
| M2 ★ | Transparent orbits | J3's transparency on J4: each half orbit at 70 %, brighter where they gather at the poles; nucleus glow; fine lines stronger. |
| M3 | Field to the edge | Three orbits inside five fine lines that run out past the tile edge; tilt 12°; nucleus glow. |
| M4 | From the poles | No surface gap: the orbits come straight out of the nucleus at its poles, one connected mark. |
| M5 | Depth (macOS 26) | M1 with K5's glass edge, lit spheres and shadow. |

### Hybrids (H)
| Code | Name | What it is |
|---|---|---|
| H1 ★ | Rings behind orbits | J3's three rings thin and transparent (14 px at 38 %) behind J4's three field orbits in the ring colour, electron on the middle orbit. From afar it reads as J4, up close the known atom is inside. |
| H2 | Field through rings | J3's atom with transparent rings (26 px at 72 %) over a field as strong as J4's, in a lighter blue, without the cut under the rings. Strongest in P2; in P8 field and rings share the ink and it gets busy. |

### J9 as the small icon (S)
W7's crop and tilt (atom zoomed 1.3 to 1.5 times into its top right, tilted 6°, electron anchored top right) with the dipole field centred on the nucleus and cut by the tile edge, drawn per size from IC4's small master (`ic4/small.js`, reproduced pixel for pixel as "IC4" in `small4.js` for comparison): rings in device pixels (1.0 px at 16, 1.3 at 32) nudged so their straight-on edges land on the pixel grid, nucleus and electron with whole-pixel diameters on the grid, the field a hairline (1 px), lifted to #7AA8FF on the navy tile so it reads. 16 pt at 2x is drawn at 32 physical px with rings a hair heavier.

| Code | Name | What it is |
|---|---|---|
| S1 ★ | Thin field | IC4's thin rings at 90 % plus one field line pair (crossing at 600 in the tile), a hairline; at 48 px two pairs. Calmest at 16. |
| S2 | Field first | Rings 75 %, nucleus one pixel bigger, two field pairs at 24 to 32 px (one at 16), stronger; closest to J9's big drawing. |
| S3 | Field and ruler | S1 with J9's ruler reduced to a hairline along the left and bottom edges with three ticks, 24 px and up; at 16 it is S1. |
| S4 | Less zoom | Crop opened to zoom 1.15 to 1.3 so more atom and field fit; the field's left lobe enters the tile. Reads as an atom first. |

Also shown: the one-colour template (rings, nucleus, electron, outer field arc) for a menu-bar or tray icon. AudioLab has none today; this is how the small master would serve one.

### Stays in the picker
J6 (Porthole, zoomed), J8 (Field with measurements, P2 and P8) and J10 (Field-orbit dial, P2 and P8), unchanged from round 3 and v0.270.

## Recommendations (stars on the page)
1. **Main K1 P2**, Lighter rings: the safest step from the shipped J3; the crossings glow, the field reads round the nucleus, holds up at 64 px.
2. **Alt M2 P2**, Transparent orbits: J4 with J3's transparency; the boldest Dock silhouette.
3. **Alt H1 P2**, Rings behind orbits: if J3 and J4 are hard to choose between, this keeps both.
4. **Main K3 P2**, Wide field: the most "magnetosphere" of the J3 row.
5. **Small S1**: thin rings and one clean field arc; keeps IC4's crisp atom and adds J9's field where it reads.

Weak spots seen in the renders: at 16 px the field of every S is a single faint arc, so the small icon reads as the atom first (S3's ruler disappears there); K2's glass rings lose their core below 128 px (they fall back to plain rings at the bold level); H2 is busy in P8; the drawn glass edge of K5 and M5 doubles up with macOS 26's own if Icon Composer's specular is switched on (IC1 has it off).

## Files (`tools/icon-lab/round4/`)
| File | What |
|---|---|
| `icons4.js` | palettes, ring and field-orbit drawing with all parameters, the designs K1 to K5, M1 to M5, H1, H2, levels of detail, Dock and macOS style mock-ups (browser and Node) |
| `small4.js` | the small master for S1 to S4 (and IC4's, reproduced), 16 to 64 px, 1x and 2x, full tile or Apple grid, and the one-colour template |
| `render4.js`, `sheet_small.py`, `shrink.py` | PNGs with `rsvg-convert`, the overview sheets, then 256-colour PNGs |
| `page.src.html`, `build_page.py`, `pick-page.html` | the pick page (the self-contained build is what was published; it embeds `round2/geom.json` and `round3/icons3.js` for the references) |
| `renders/<id>/` | per design and palette (P2, P8): `<id>-<P>-{1024,512,128,64}.png`, `-mac-1024.png`, `-dock-dark.png`, `-dock-light.png`, `-styles.png` (Default and Dark) |
| `renders/small/` | `<S>-<P>-{16,20,24,32,48}.png`, `-32-at16.png` (16 pt at 2x), `-64-at32.png` (32 pt at 2x), `-mac-{16,32}.png`, `<S>-template-{16,32}-{black,white}.png` |
| `renders/sheet-big.png`, `renders/sheet-small.png` | every design at 256 and 64; every S and IC4 magnified |

Regenerate: `node render4.js && python3 shrink.py && python3 build_page.py`.

## What the implementation task does after the pick
1. **Main** becomes the default app icon, drawn at 1024 from `icons4.js` (full tile for the layer art, Apple grid for flat files) through the IC1 pipeline: `desktop/icon-assets/mac-icon/make_icon.py` writes `AppIcon.icon`, `desktop/scripts/build-mac-icon.sh` compiles `Assets.car`. **Dark stays navy**: the fill #132044 for default, dark and tinted, written only as `fill-specializations` (IC1's lesson). A P8 Main would need the P8N fill and layer for Dark. For K5 or M5, decide whether the drawn glass edge stays in the layer or Icon Composer's specular takes over (not both).
2. **Alt** goes into Settings › App icon (`desktop/icon-assets/picker/`, 512 px plus a 128 thumb, and `icons.json`, group "Dipole field") next to J6, J8 (P2, P8) and J10 (P2, P8). If Alt is an M or H, J4 itself stays in the picker too.
3. **Small**: the chosen S replaces IC4's small master everywhere at 32 px and below: `icon.icns` (16 and 32 pt at 1x and 2x), `icon.ico` (16, 20, 24, 32; 48 and up from Main), `doc.icns`/`doc.ico` small tiers, the favicons `web-16`, `web-32` (and `web-48` from Main). `tools/icon-lab/ic4/svgs.js` and `ship.py` take `small4.js` instead of `ic4/small.js`.
4. Regenerate `icon.icns`, `icon.ico`, `Assets.car`, `dock-icon.png`, `icon.png` and the favicons; run the "Mac icon proof" job on macOS 26 (Default and Dark both navy) and `tools/ui-tests/taskAH_electron.js`.
5. Raise the app version, one line in `desktop/update-notes.txt`, and run the desktop build. Promotion to installed apps goes through the release gate (`AL_PROMOTE=1`), never by editing `desktop/app-version.json`.
