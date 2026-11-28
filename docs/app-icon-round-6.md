# AudioLab app icon, round 6: K5a, the Earth and Moon, and the small icons (task IC10)

Pick page: **AudioLab app icon, round 6: K5a, the Earth and Moon, and the small icons**, https://claude.ai/artifact/GL1tMVeLszraoj1QNKMQqP

> "Let's consolidate icon round 5b, icon round 5c, and small icons together into a Fable task. And let's redo them in Fable. And then I'm going to pick." (28 November 2026, 14:33 Brussels)

Round 6 replaces round 5b (IC7, tapered K5a and M5d), round 5c (IC8, the Earth and the Moon) and the small-icon round (IC9) with one page, drawn anew. Nothing in the app changed: no edit to `index.html` or `desktop/`. Everything is in `tools/icon-lab/round6/` and this doc.

The user's notes this round answers (docs/app-icon-round-5.md):
- K5a and M5d are the two picked designs.
- Rings are tapered, never flat, "so it looks like it's in 3D anatomically correct".
- M5d is the Earth (yellow) and the Moon (blue), kept scientific.
- Small icons: MS2, the lit one, never a flat nucleus; a small M5c.
- The 32 picker removals stand.

## How to pick
On the page: the K row (K5a as picked, dashed, then K6a to K6d) and the E row (M5d as picked, dashed, then E6a to E6e), with a P2 / P8 switch for the whole page; a table of what is to scale; a bench for the selected design (1024, also at 100 %, 512, 128, 64 on dark and light; the Dock on a dark and a light desktop next to invented stand-in app icons; macOS 26 Default and Dark, Dark stays navy); a compare view with a wipe slider between any two (every design in both palettes, K5a and M5d as picked) at 1024, 512, 128 and 64; the small icons KS6 to KS8 and ES5 to ES7 at 16, 20, 24 and 32, real pixels on dark and light and magnified, 1x and 2x; the real places (the smallest Dock, the Finder list, a browser tab, the Windows title bar and taskbar, a menu bar template); the two families; stars on the recommendations; the picks bar. Give one design **Main**, one from the other family **Other**, one small icon per family, then paste the line, for example:

`Round 6 picks: main K6a | other E6b | small KS6 ES5`

(A palette is added only when it is not P2, for example `main K6a P8`. The small icon of the main's family comes first.)

## What is new in the drawing
Rounds 2 to 5 wrote SVG strokes and let `rsvg-convert` paint them, so a tapered ring was a stroke cut into pieces. Round 6 paints the pixels itself (`r6.py`, numpy):
- **One camera, one depth buffer.** Every ring, orbit and bold field line is a round tube round a curve in space, every body a sphere. Screen position, tube width, what hides what at a crossing and behind the nucleus all come from the same geometry.
- **Taper.** A tube's width follows the camera's scale times an exaggeration with depth (as the shipped Ocean Yellow rings exaggerate theirs): K6a 34 px near, 11 px far (3 to 1).
- **Dimming.** The far half fades toward the ground (to about half) and lies under the nucleus glow; the near half is full colour and lit from the top left (or from the Sun).
- **Shading.** Per pixel, from the tube's or sphere's surface normal: a lit side, a shaded side, an optional highlight. No seams: each sample takes the piece of the tube whose axis it is closest to.
- **Hairlines** (the fine field lines) are flat see-through lines blended with a depth test: over what is behind them, under what is in front.
- **Anti-aliasing** by supersampling (9 samples a pixel at 1024, 64 at 64 px, 144 for the small icons), and half a step of noise before rounding to 8 bits so the dark gradients do not band.
- **Levels of detail** as before: 128 px and up everything (lines a third heavier between 100 and 200 px, the Dock); 48 to 96 px the bold structure; 32 and below the small icons.

## Designs
### K6: K5a with real rings
The three rings are circles of the shipped geometry (long axis 360, short 150 in the mark frame, so tilted 65.4 degrees) at -30, 30 and 90 degrees, nested like a gyroscope (3.5 % apart in radius, so they never run through each other), seen from a camera at 1500. K5a's soft glass (a hint of sheen, a thin light edge), glow, soft shadow and J3's field stay. The inner field lines run on under the rings, unbroken.

| Code | Name | What it is |
|---|---|---|
| K6a ★ | Woven tubes | The rings tip the same way round the centre, so each passes over its neighbour on one side and under on the other. 34 px near, 11 px far. |
| K6b | Seen from above | The lower half of every ring is the near half: one atom seen a little from above. Closest to round 5b's K5a-T2. |
| K6c | Turned in space | The same rings as one rigid object turned 11 degrees to the side and 7 toward you: the three ellipses differ, the near ring passes in front of the nucleus. |
| K6d | Bold taper, lit | The weight of the shipped rings: 48 px near, 11 px far (4 to 1), a highlight along each tube and a darker edge. |

### E6: M5d as the Earth and the Moon
The field is the Earth's magnetic field, a dipole: each line follows r = L sin²θ. The bold white lines are the shells L = 2.7, 4.1 and 5.9 Earth radii (M5d's orbits; the Earth is M5d's nucleus, 75.7 px), the fine lines L = 3.4 to 13.6, all in one meridian plane turned 28 degrees round the magnetic axis: the right side comes toward you (thick, bright, in front of the Earth), the left goes away (thin, dim, its feet behind the Earth). The axis leans 12 degrees as in M5d and tips 12 degrees toward you.

| Code | Name | What it is |
|---|---|---|
| E6a ★ | The dipole in space | M5d as picked, in space; the Moon where the electron was; K5a's soft light. |
| E6b ★ | Day and night | E6a lit by the Sun from the left: the Earth has a day and a night side, the Moon shows the same phase, the tubes are lit from the same side. |
| E6c | Two axes, the globe | A graticule (equator, tropics, polar circles, meridians) makes the Earth a globe; the rotation axis dashed, the magnetic axis solid, 9.2 degrees apart (2025), a small arc between them. |
| E6d | The magnetosphere | A traced model field: the dipole, an image dipole 28 times as strong on the Sun's side (the classic image-dipole magnetopause) and a tail current sheet. Day side squeezed, night side drawn into a tail, polar lines open into the lobes, the magnetopause dashed (Shue et al. 1997) at 7 Earth radii as in a strong solar storm, the Moon in the tail as at full Moon. |
| E6e | The Moon on its orbit | The Moon's path as a blue tube, thick in front of the Earth and thin behind, 5.1 degrees to the dotted ecliptic; two white shells inside; lit by the Sun. |

What is to scale and what is drawn for legibility:

| | Real | In the icons |
|---|---|---|
| Field lines | near the Earth a dipole | exact in E6a, E6b, E6c, E6e; E6d traces the model above (`mag_field` in `designs6.py`) |
| Magnetic axis | 9.2° from the rotation axis (2025) | exact in E6c; the picture's lean is 12° as in M5d |
| Magnetopause | about 10 Earth radii, 6 to 7 in a strong storm | E6d: 7, so the Earth stays large |
| Moon, size | 0.273 Earth radii | 0.48 (0.5 in E6d) |
| Moon, distance | 60.3 Earth radii | 3 to 9 |
| Moon's orbit | 5.1° to the ecliptic | exact in E6e |
| Sunlight | parallel, one phase for every body | E6b, E6d, E6e |

Sources are round 5c's (docs/app-icon-round-5c.md: NASA GSFC on the dipole and the magnetosphere, NOAA NCEI and BGS on the 2025 pole, Shue et al. 1997, the NSSDC Moon fact sheet). The image-dipole model of the magnetopause (an image dipole about 28 times the Earth's moment, 40 Earth radii toward the Sun, for a quiet magnetopause near 10) is an old textbook model; here it is scaled to 26 Earth radii for the storm-time picture, and the tail sheet is a simple added term. The model's numbers were written from memory and not checked against a source this round, so E6d is a faithful sketch of the shape, not a calibrated field model.

### The small icons (32 px and below)
Each is its own drawing for 16, 20, 24 and 32 pt at 1x and 2x, on the full tile (Windows, favicon) and on the Apple grid (icns), painted by the same renderer with measures in pixels (`small6.py`): nucleus and electron (Earth and Moon) with whole-pixel diameters, centred on a pixel centre (odd) or corner (even); line widths per size, near and far side (about 2 to 1 at 32, gentle at 16); a ring's outermost point on the half-pixel grid; the Moon moved out along its line until a pixel of ground shows between it and the Earth; a hairline rim; the 2x picture is its point size's drawing with lines 1.75 times wider. The nucleus is always a lit sphere with a glow.

| Code | Family | Name | What it is |
|---|---|---|---|
| KS6 ★ | K | The crop, tapered | S1's crop (the atom zoomed into its top right, the electron in the corner) with K6's rings and a lit nucleus. |
| KS7 | K | The whole atom | Nothing cut: two rings at 16 and 20 px, three from 24, a bigger lit nucleus. |
| KS8 | K | Closer, glowing | Further in: a big glowing nucleus, heavy ring arcs out of the tile, the electron with its own glow and a light top edge from 24 px. |
| ES5 ★ | E | MS2, lit and tapered | The user's MS2: the Earth low left, lit, the field tilted 24°, two lines (the outer out of the tile), the Moon on the inner; the lines tapered tubes; light top edge from 24 px. |
| ES6 | E | A small M5c | The whole of M5c simplified: glowing core in the middle, half orbits left and right; one pair at 16, two at 20 and 24, three at 32. |
| ES7 | E | Day and night | ES5 lit by the Sun, as E6b and E6d: day and night sides, the Moon in the same phase. |

## Recommendations (stars on the page)
1. **Main K6a P2** with **KS6**: the atom people know, now a real object; holds in the Dock and at 64 px; its small icon is the crop already shipped (S1), with the new rings.
2. **Other E6b P2** with **ES5**: the day and night sides say "planet" at once, and the field is true.
3. **K6d** if the rings should have the weight of the shipped Ocean Yellow logo.
4. **E6d** as the most scientific picture, best in the picker or the About window (its Earth is smaller).

Weak spots seen in the renders:
- K6a and K6b differ only in how the rings weave; at Dock size they look alike.
- K6c's near ring covers the lower edge of the nucleus.
- The far halves are thin: at 128 px a far ring is about 1.5 px, in P8 it turns grey.
- E6a to E6c are lopsided by design (the near side is larger and heavier than the far side).
- E6c's graticule and axes are lost below 128 px; there it is E6a.
- E6d's Earth is 108 px of 1024, and its fine lines end at the dashed magnetopause.
- E6e's orbit ring is thin behind the Earth and its end by the Moon is cut by the Moon's halo.
- On the Apple grid at 16 pt (a 14 px tile) the K small icons are crowded; KS7 is the calmest there.
- At 16 px ES5 and ES7 are mostly the Earth, the Moon and two arcs; ES7's night side is two or three darker pixels.
- ES6's far (left) orbits are soft at 1x.
- K5a and M5d "as picked" on the page are round 5's 256-colour PNGs, so they show bands that the new renders do not.

## Files (`tools/icon-lab/round6/`)
| File | What |
|---|---|
| `r6.py` | the renderer: camera, canvas with depth, tubes, flat lines, spheres, materials, the tile's shape |
| `designs6.py` | palettes (P2, P8, P8N), K6a to K6d, E6a to E6e, the magnetosphere model, the tile's glass, the Apple grid; `render(id, pid, px, frame, style)` |
| `small6.py` | KS6 to KS8, ES5 to ES7: `small(id, pid, pt, scale, frame)`, `template(id, pt, scale)` (the one-colour mark) |
| `render6.py` | every picture into `renders/` and `renders/manifest.json` (about ten minutes on two cores) |
| `page.src.html`, `build_page.py`, `pick-page.html` | the pick page (the self-contained build is what was published) |
| `renders/big/` | per design and palette: `-1024.webp`, `-512.webp`, `-128.png`, `-64.png`, `-mac-256.png`, `-mac-128.png`, and `<id>-P8N-mac-256.png` (P8's Dark entry) |
| `renders/small/` | `<id>-<P>-<pt>@<s>x[-mac].png`, `<id>-tpl-16@<s>x.png` |
| `renders/ref/` | K5a and M5d of round 5, for the compare view |

Regenerate: `python3 render6.py && python3 build_page.py` (Python 3 with numpy, scipy and Pillow).

## What the implementation task does after the pick
1. **Main** becomes the default app icon, drawn at 1024 by `designs6.render` (full tile for the Icon Composer layer, Apple grid for the flat files) through the IC1 pipeline: `desktop/icon-assets/mac-icon/make_icon.py` writes `AppIcon.icon`, `desktop/scripts/build-mac-icon.sh` compiles `Assets.car`. **Dark stays navy**: the fill #132044 for default, dark and tinted, only as `fill-specializations`. A P8 Main needs the P8N fill and layer for Dark. The shading of the tubes and the glass edge are drawn, so Icon Composer's specular stays off (or the drawn edge is left out of the layer), not both.
2. **Main's small icon** (its KS or ES) replaces S1 everywhere at 32 px and below: `icon.icns` 16 and 32 pt at 1x and 2x (`small(id, pid, pt, 2, 'mac')` for the 2x slots), `icon.ico` 16, 20, 24, 32, `doc.icns`/`doc.ico` small tiers, the favicons `web-16`, `web-32`. `ic6/ship6.py` calls `round6/small6.py` and `designs6.py` (Python) in place of `svgs6.js`.
3. **Other** goes into the picker (`desktop/icon-assets/picker/`, 512 px, a 128 thumb, small 16, 32, 48 from its own small icon, `icons.json` group "Dipole field"). J3 (Dipole Field, today's default) stays in the picker as an option.
4. **The 32 removals of round 5** (docs/app-icon-round-5.md, "The user's picker removals") leave `icons.json`'s list; their pictures stay resolvable, so a user who has one chosen keeps it. The stored choice is never reset.
5. Regenerate `icon.icns`, `icon.ico`, `Assets.car`, `dock-icon.png`, `icon.png` and the favicons on the macOS runner (macos-latest); run the "Mac icon proof" job (Default and Dark both navy) and `tools/ui-tests/taskAH_electron.js`. Check on a Mac whether macOS 26 uses the .icns small slots in the Finder list when `Assets.car` is present (still not verified).
6. One line in `desktop/update-notes.txt`; any `index.html` edit (the browser tab icon) waits while `desktop/release-freeze.json` is on main. Promotion to installed apps goes through the release gate only; the Dock shows the new icon with the next desktop build.

## The user's notes on round 6 (28 November 2026, 18:25 Brussels): round 7 on Fable

The user: "When it comes to icon round 6, let's rethink the whole shape, because the last shape was done in Opus and I didn't like the shape. So the tapering that was done last time based on the research you did on design. Take all the research you've ever done about design, use that to redo these logos. But what is good is that you're going 3D instead of more flat. That's good. And I do like the idea of the Earth and the Moon with the Van Allen belt, or like the magnetic belt. E6 is cool with like the magnetic field of the Earth, and then you can see the orbit around it. Let's redo that based on some design rules based on your research. If you want, you can do some extra research on the Van Allen belt, the magnetic field, the Moon and its orbit, the Earth, and how to design this in an interesting way. And let's redo the small icons as well. I do like KS8 where you're closer, where the big circle is aligned with the left bottom corner, and where the blue circle is aligned with the top right corner. And then it's zoomed in and you can see the glow. And you can do some more research on how to make small icons. E6e looks cool. E6d looks cool. E6c also looks cool. And let's make the pick screen a little bit less busy. I do like the small dock, the Finder list and the browser tab. Let's keep that, but it's too much text. Let's have it short and simple so I can go through it fast. And do everything in Fable."

- Not liked: the round 6 shapes and their tapering. Liked: 3D rather than flat; the Earth and the Moon with the Van Allen belts and the magnetic field; the Moon's orbit seen around it; **E6c** (the globe with its two axes), **E6d** (the magnetosphere), **E6e** (the Moon on its orbit); small icon **KS8** (zoomed in, the big circle aligned to the bottom left corner, the blue circle to the top right, the glow visible).
- Round 7 (task IC11, Fable): new shapes from all earlier design research (docs/app-icon-*.md, docs/app-icon-small-sizes.md, docs/app-icon-mac-styles.md, docs/design-languages-research.md, docs/look-tokens.md); extra research on the Van Allen belts, the magnetosphere, the Moon and its orbit and how to draw them well; new small icons in the KS8 direction. A simpler pick page: few designs, one short line each, the small Dock, the Finder list and the browser tab kept; everything else trimmed.
