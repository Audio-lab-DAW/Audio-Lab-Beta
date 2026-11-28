# AudioLab app icon, round 5: K5 and M5 depth (task IC7)

Pick page: **AudioLab app icon, round 5: K5 and M5 depth**, https://claude.ai/artifact/75BnXoeDy5x8xSKRsSBCdc

> "Let's pick K5 depth, and let's also go with M5 depth and give me a few variations of those. And when it comes to smaller logos, so smaller than 32, we need a zoomed in version of both. And I'll pick one or the other and then put the other in the settings to choose from later. Also give the other ones that you remembered to put in the settings, and we'll pick them and remove a few that people can pick in the settings to have as startup as icons for their dock or their shortcuts." (28 November 2026, 00:58 Brussels)

Nothing in the app changed: no edit to `index.html` or `desktop/`. Everything is in `tools/icon-lab/round5/` and this doc.

## How to pick
On the page: the K5 row (round 4's K5, then K5a to K5f) and the M5 row (round 4's M5, then M5a to M5f), each with a P2 / P8 switch; a bench for the selected design (1024, 512, 128, 64; the Dock on a dark and a light desktop next to invented stand-in app icons; macOS 26 Default and Dark, Dark stays navy); a **compare view** with a wipe slider or side by side between any two (the variations, K5 and M5 of round 4, J3 as shipped, S1, IC6's small M5, KS and MS) at 1024 down to 16 px; the **zoomed-in small versions** KS1 to KS3 and MS1 to MS3 at 16 and 32 pt, 1x and 2x, magnified, plus 16 to 48 px and the Apple grid, next to S1 as shipped and IC6's small M5; the two **families** (big icon at 128 and 64 with its small version at 32, 16 and 2x); a Windows taskbar and a browser tab; the **picker review** (all 61 icons of today's picker in its groups, at 128 and 32 px, each with a keep box, all ticked); stars on the recommendations; the picks bar. Give one design **Main**, one from the other family **Other**, one **KS** and one **MS**, untick what should leave the picker, then paste the line, for example:

`Round 5 picks: main K5c | other M5b P8 | small KS3 MS1 | remove: sputnik synthwave`

(A palette is added only when it is not P2. Removed icons are named by their picker id.)

## What changed in the drawing
- `icons5.js` is round 4's `icons4.js` with a **depth block** per design: the light direction (degrees from straight up; moves the sphere highlights, the sheen, the glass edge and the shadow, which falls away from the light), the sheen's strength and how far into the tile it reaches, the light edge's strength and width, a shade toward the far side of the tile, the shadow's strength and distance. Per drawing: the nucleus glow's reach and strength, a glow round the electron, glass rings' or glass orbits' bright core. K5 and M5 of round 4 have no depth block and draw exactly as in round 4.
- At 48 to 96 px (the bold level) glass rings and glass orbits fall back to plain strong strokes (round 4's K2 lost its core there).
- `small5.js` is new. KS: S1's geometry (the W7 crop, the electron anchored top right, rings with their straight edges on the pixel grid) with K5's lighter rings and lit nucleus. MS: the nucleus low left of centre, the field axis tilted 18 to 24°, the orbits r = L sin²θ centred on it and cut by the tile edges, each scaled so its outermost point lands on a pixel centre, each half orbit ending a quarter of its reach from the nucleus so the ends stay apart at the poles, the electron on an orbit at the top right as in S1.

## Designs
### K5 depth (K)
| Code | Name | What changed from K5 |
|---|---|---|
| K5a ★ | Soft glass | Half the sheen, a quarter into the tile; edge thinner (7) and fainter; lighter shadow. Sits best if macOS 26 adds its own specular. |
| K5b | Deep glass | Rings as glass tubes (28 px band at 46 % with a bright core), sheen two thirds down, edge 14 wide, far corner shaded, deeper shadow, light from the top left. |
| K5c ★ | Glowing core | Nucleus glow reaches 4.1 radii and a third stronger, electron with its own glow, rings 22 px at 72 %. |
| K5d | Wide field | K3's field with K5's depth: atom 8 % smaller, seven lines out past the tile edge, tilt 12°. |
| K5e | Light from the right | Light from the top right (38°): highlights, sheen and edge turn round, shadow to the bottom left; rings 28 px at 86 %. |
| K5f | Fine lines | Rings 18 px at 70 %, field 3.4 px, electron r 40, gentle depth. |

### M5 depth (M)
| Code | Name | What changed from M5 |
|---|---|---|
| M5a | Soft glass | As K5a. |
| M5b | Glass orbits | Orbits as glass tubes (24, 21, 18 px at 45 % with a bright core), deep sheen and shade, light from the top left. |
| M5c ★ | Glowing core | Half orbits at 74 % (brighter where they gather at the poles), glow 4 radii, electron glow. The pair of K5c. |
| M5d ★ | Field to the edge | M3's five fine lines out past the tile edge with M5's depth, tilt 12°. |
| M5e | Light from the right | As K5e; orbits 21, 18, 15 px. |
| M5f | Fine lines | Orbits 14, 12, 10 px, fine lines 3.4 px, electron r 38. |

### Zoomed-in small versions (32 px and below)
| Code | Family | Name | What it is |
|---|---|---|---|
| KS1 | K5 | S1, lit | S1 with rings at 82 %, the nucleus lit from the top left with a glow of a pixel or two. |
| KS2 | K5 | Closer, tilted field | Zoom 1.5 to 1.6 (S1: 1.3 to 1.4), field tilted 10°, two pairs from 24 px. |
| KS3 ★ | K5 | Glowing core, light edge | KS1 with a stronger glow, a lit electron and, from 24 px, a one-pixel light edge along the top. |
| MS1 ★ | M5 | Two orbits, zoomed | Two orbits, the outer cut by the edges, electron top right; three orbits and a hairline pair at 40 px and up. Flat nucleus. |
| MS2 | M5 | Closer, lit | Further in, nucleus a pixel bigger, only the arcs of the outer orbit in the tile; lit nucleus. |
| MS3 | M5 | Three orbits at 32 | Three orbits from 24 px (two at 16 and 20) at 80 %, lit nucleus, light top edge. |

## Recommendations (stars on the page)
1. **Main K5c P2** (Glowing core): K5 as picked, with the light from the nucleus; holds up in the Dock and at 64 px. Small: **KS3**.
2. **Other M5c P2** (or **M5d**): the same idea on M5, as its sibling in the picker. Small: **MS1**.
3. **K5a** if the depth should stay quiet (no double edge with macOS 26's specular).

Weak spots seen in the renders: K5b and M5b's glass tubes go grey and soft in P8, and the shade dirties P8's paper; the light edge of KS3 and MS3 hardly shows on P8; K5f and M5f thin out first in the Dock; MS1 to MS3 at 16 px are a nucleus with arcs round it (the orbits read as orbits from 24 px), KS1 to KS3 at 16 stay close to S1.

## The picker review
All 61 icons of `desktop/icon-assets/picker/icons.json` (Dipole field 12, Main logo colours 5, Spirograph & fractal 14, Realistic 3D 2, Decades 9, 1950s illustration 3, Scientific illustration 5, Atom models in history 11), each at 128 px (the picker's thumbnail) and 32 px (IC6's small version where one exists, the 512 px picture reduced otherwise).

## Files (`tools/icon-lab/round5/`)
| File | What |
|---|---|
| `icons5.js` | round 4's module with the depth block; K5, K5a to K5f, M5, M5a to M5f; Dock and macOS style mock-ups |
| `small5.js` | KS1 to KS3, MS1 to MS3 (16 to 64 px, 1x and 2x, full tile or Apple grid) |
| `render5.js`, `sheet5.js`, `sheet_small5.js`, `shrink.py` | PNGs with `rsvg-convert`, overview sheets, 256-colour PNGs |
| `picker_data.py`, `picker-review.json` | today's picker with thumbnails for the review |
| `page.src.html`, `build_page.py`, `pick-page.html` | the pick page (the self-contained build is what was published) |
| `renders/<id>/` | per design and palette: `-{1024,512,128,64}.png`, `-mac-1024.png`, `-dock-dark.png`, `-dock-light.png`, `-styles.png` |
| `renders/small/` | `<id>-<P>-{16,20,24,32,48}.png`, `-32-at16.png`, `-64-at32.png`, `-mac-{16,32}.png` |
| `renders/sheet-big-{P2,P8}.png`, `renders/sheet-small-{P2,P8}.png` | every design at 320 and 64; S1, IC6's small M5 and every KS and MS magnified |

Regenerate: `node render5.js && python3 shrink.py && python3 picker_data.py && python3 build_page.py`.

## What the implementation task does after the pick
1. **Main** becomes the default app icon, drawn at 1024 from `icons5.js` through the IC1 pipeline (`desktop/icon-assets/mac-icon/make_icon.py` writes `AppIcon.icon`, `desktop/scripts/build-mac-icon.sh` compiles `Assets.car`). **Dark stays navy**: the fill #132044 for default, dark and tinted, only as `fill-specializations`. The drawn glass edge and sheen stay in the flat files (`icon.png`, `dock-icon.png`, `icon.ico` 48 and up, `web-*`); in the Icon Composer layer either the drawn edge or the system specular, not both. A P8 Main needs the P8N fill and layer for Dark.
2. **Main's small version** (its KS or MS) replaces S1 everywhere at 32 px and below: `icon.icns` 16 and 32 pt at 1x and 2x (each 2x drawn for its point size), `icon.ico` 16, 20, 24, 32, `doc.icns`/`doc.ico` small tiers, favicons `web-16`, `web-32`. `ic6/ship6.py` and `svgs6.js` take `round5/icons5.js` and `small5.js`.
3. **Other** goes into the picker (`desktop/icon-assets/picker/`, 512 px, a 128 thumb, small 16, 32, 48 drawn from its own KS or MS, `icons.json` group "Dipole field"). J3 (Dipole Field) stays in the picker as an option unless ticked off.
4. **Removed icons** leave `icons.json`'s list, but their pictures stay (or move to a hidden `retired` list the shell still resolves), so a user who has one chosen keeps it in the Dock, taskbar and tab; the stored choice is never reset.
5. Regenerate `icon.icns`, `icon.ico`, `Assets.car`, `dock-icon.png`, `icon.png` and the favicons on the macOS runner (macos-latest); run the "Mac icon proof" job (Default and Dark both navy) and `tools/ui-tests/taskAH_electron.js`.
6. One line in `desktop/update-notes.txt`; any `index.html` edit (the browser tab icon) waits while `desktop/release-freeze.json` is on main. Promotion to installed apps goes through the release gate only; the Dock shows the new icon with the next desktop build.

## The user's picks (28 November 2026, 01:13 Brussels)

The user: "I like K5A, but when it comes to the Atom, I forgot to say that I wanted the tapered version ... I don't want the flat version, and maybe you can improve the tapering so it looks like it's in 3D anatomically correct. And then I like M5D. And let's go pick those both."

- **K5a (soft glass) and M5d (field to the edge)** are the two picked designs.
- **Tapered rings, never flat:** the rings must be tapered like the shipped Ocean Yellow atom (thicker where the ring comes towards you, thinner where it goes away), improved so they read as real 3D: each ring drawn as a tilted circular band seen in perspective (width and brightness from the projection, the far half dimmer and thinner, the part behind the nucleus hidden by it, the near part passing in front), the three rings at consistent tilts like one object. Apply it to K5a, and also give a tapered version of M5d (its orbits) so both can be compared.
- Not picked yet: which of the two is the main icon (the other goes in the picker), the small versions, and the picker removals: round 5b asks again.

### Next: round 5b (IC7, second run)
A short pick page: K5a tapered in 3 to 4 taper styles (T1 ...: from today's shipped taper to a full perspective band with occlusion), M5d flat and tapered, both in P2 and P8 at 1024 to 64 with the Dock mock-ups; their zoomed-in small versions (32 px and below) redrawn to match; the main/other choice; and the picker review again. Picks line for example 'Round 5b picks: main K5a-T3 | other M5d-T2 | small KS3 MS1 | remove: ...'.

## The user, 01:14 Brussels: M5d as the Earth and the Moon

The user: "How is this field called? And is it the earth or? Let's go with the second M5 logo. Let's pretend that the yellow is the earth and the blue is the moon. Maybe we can do some variations with that information and keep it scientific." Read as M5d (the second design picked at 01:13). Built as its own pick page by task IC8 (docs/app-icon-round-5c.md, tools/icon-lab/round5c/), next to round 5b.

## The user, 01:20 Brussels: the small icons

The user: "For the zoomed ones: let's try MS2. I want the lit one, not the flat one. And let's try an M5c, the actual one, the non-flat one, and let's do some research on how to make icons like this smaller. And how do you do it? Do you zoom in or whatever? I actually really don't know."
- **MS2 (closer, lit nucleus)** is the small icon to develop; never the flat nucleus.
- A small version of **M5c** (glowing core, not flat) to try next to it.
- Research on how small icons are made. Built by task IC9 (docs/app-icon-small-sizes.md, tools/icon-lab/round5s/), next to rounds 5b and 5c.
## Round 5b: tapered K5a and M5d (IC7, second run, 28 November 2026)

Pick page: **AudioLab app icon, round 5b: tapered K5a and M5d**, https://claude.ai/artifact/HZRyiwMrb55yH6hy5H7kcW

Picks line to paste, for example: `Round 5b picks: main K5a-T2 | other M5d-T2 | small KS4 MS4 | remove: ...` (the page's bar builds it; *Swap main and other* turns the two round).

### How the taper is drawn (the 3D)
- **The shipped taper** (Ocean Yellow, `desktop/icon-assets/source/icon-L.svg`, `tiers.py`): each ring is a flat crescent, an outline whose inner ellipse is offset, so the ring is widest at one end of its long axis and narrowest at the other, about 3:1, exaggerated to 4:1 at 24 to 64 px and dropped (even rings) at 16 and 20 px. It reads as "tapered", but it is not perspective: it is thick at a side of the ring, not where the ring comes toward you.
- **A ring in 3D:** the drawn ellipse (rx 360, ry 150) is a circle of radius R = rx whose plane is tilted so that cos i = ry / rx (i = 65.4 degrees). The point at angle t sits at depth z = R sin i sin t, and is projected from a camera at 5 R: screen = centre + (x, y) * D / (D - z). The near half grows and the far half shrinks a little, so the ellipse becomes slightly egg-shaped, as a real ring would.
- **A round tube** looks the same width from every side, so its seen width only follows the perspective scale. A true camera at 5 R gives only about 1.5:1; it is exaggerated to about 2.6:1 (width = w (1 + 0.45 dn), dn = sin t, the depth from -1 far to +1 near), as the shipped icon exaggerates its taper.
- **A flat band** (a hoop of height h round the ring's axis) has a seen width of h times the sine of the angle between the line of sight and the band: widest where the ring comes toward you and where it goes away, edge-on at the ends of the long axis; its outer face shows on the near half, its inner face on the far half.
- **Brightness:** the far half fades toward the background (up to 50 to 62 %), and it also lies under the nucleus glow (the glow is painted at the nucleus' depth).
- **Occlusion:** every ring is cut into short pieces, grouped into chunks of about 30 degrees. Each chunk is drawn layer by layer and runs two pieces into the next chunk, where it draws the same pixels, so there are no seams. The chunks, the nucleus, its glow and the electron are painted back to front, so the rings pass over and under each other at their crossings like one object. With K5's geometry a ring never crosses the nucleus (the ring's short semi-axis, 129, is larger than the nucleus radius, 69), so its occlusion shows at the crossings. On the field orbits it shows at the nucleus.
- **One object:** the two slanted rings tip their lower halves toward you and the upright ring its left half: one atom seen a little from above, the electron on the near side of ring 0 (t = 18 degrees).
- **Field orbits (M5d):** each orbit r = L sin^2(theta) lies in a plane through the dipole axis. The plane is turned 26 degrees round the axis (all the orbits the same way, so the right side of the field comes toward you and the left goes away), and the axis is tipped 12 degrees toward you. The camera is at 2600. The bold orbits start on the nucleus surface, so their far feet go behind the nucleus and the near feet pass in front of it. The fine field lines behind stay flat.

### The designs
| Id | Name | What |
|---|---|---|
| K5a | as picked (reference) | flat even rings, 24 px at 80 % |
| K5a-T1 | Shipped taper | the Ocean Yellow crescent, about 3:1, thick toward the bottom left; flat and see-through (crossings brighter) |
| **K5a-T2** ★ main | Perspective tube | tube in perspective, about 2.6:1, far half fading under the glow, over and under at the crossings |
| K5a-T3 ★ alt | Lit tube | T2 with darker tube edges and a highlight toward the light (from above); at 64 px only the highlight stays |
| K5a-T4 | Perspective band | flat hoops, wide toward and away from you, edge-on at the sides, lit outer face near, darker inner face far, a light rim |
| M5d | as picked (reference) | flat even orbits 18, 16, 13 px, five fine lines past the edge, tilt 12 degrees |
| M5d-T1 | Shipped taper | flat; each half orbit widest at its outermost point, narrowing to a third into the poles |
| **M5d-T2** ★ other | Perspective orbits | orbit planes turned 26 degrees, axis tipped 12: the right side near (thick, bright, in front of the nucleus), the left far (thin, dim, its feet behind the nucleus) |
| M5d-T3 ★ alt | Lit perspective orbits | M5d-T2 lit as K5a-T3 |

Small versions (32 px and below, zoomed in as before, now tapered and woven in the same 3D; the taper is about 2:1 at 32 px and gentle at 16, like the shipped tiers; the varying widths are no longer pixel-snapped, while the nucleus and electron still are):
| Id | What |
|---|---|
| **KS4** ★ | S1's crop with K5a-T2's rings, lit nucleus and glow |
| KS5 | KS2's closer crop (1.5 to 1.6 times), tapered and woven |
| **MS4** ★ | MS1 (two orbits, zoomed) in perspective, the near ends in front of the nucleus |
| MS5 | MS3's three orbits (two at 16 and 20) in perspective, a one-pixel light top edge from 24 px |
| KS1, MS1 | round 5's flat versions, for comparison |

Note: the user's small-icon picks of 01:20 (MS2 lit, a small M5c, the research on how small icons are made) are task IC9's (docs/app-icon-small-sizes.md); KS4 to MS5 here only show how the tapered 3D carries down to 32 px and below, so the two rounds can be compared. The Earth and Moon reading of M5d is task IC8's (docs/app-icon-round-5c.md).

The picker review again lists the same 61 icons (nothing has been removed yet), each with a keep box.

**Recommendation:** main **K5a-T2** (P2) with **KS4**, other **M5d-T2** with **MS4**. K5a-T2 is the closest to the icon people know (the shipped taper's look), made physically right, and calm with K5a's soft glass. If it should look most like a solid object: K5a-T3 and M5d-T3.

Weak spots seen in the renders:
- K5a-T4's bands almost vanish where they turn edge-on, and it is the least like the shipped icon.
- K5a-T3's tube edges are lost below 128 px, so it reads as T2 in the Dock.
- M5d-T2 and T3 are lopsided: the near side is larger than the far side.
- In P8 the far halves turn grey, and in its Dark entry (P8N) the rings are light grey.
- The tapered small versions are a touch softer than S1 at 16 px.
- KS5 is busy at 32 px.
- MS4 and MS5 at 16 px read as a nucleus with arcs.

### Files (round 5b, `tools/icon-lab/round5/`)
| File | What |
|---|---|
| `icons5b.js` | round 5's module with the 3D layer (`taperRings`, `taperOrbits`, depth-sorted chunks); K5a-T1..T4, M5d-T1..T3 (exports `AL5B`, its `T3D` helpers) |
| `small5b.js` | KS4, KS5, MS4, MS5 (and KS1, MS1 for comparison), exports `AL5BS` |
| `render5b.js`, `sheet5b.js`, `sheet_small5b.js`, `shrink5b.py` | PNGs into `renders5b/` (same layout as `renders/`: per design and palette 1024, 512, 128, 64, mac-1024, dock-dark, dock-light, styles; `small/` at 16 to 48 with 2x; overview sheets) |
| `page5b.src.html`, `weak5b.txt`, `build_page5b.py`, `pick-page-5b.html` | the pick page (the self-contained build is what was published) |

Regenerate: `node render5b.js && python3 shrink5b.py && python3 picker_data.py && python3 build_page5b.py`.

### What the implementation task does after the 5b pick
As in "What the implementation task does after the pick" above, with these designs:
1. **Main** becomes the default icon, drawn from `icons5b.js`.
2. The main's KS or MS replaces S1 at 32 px and below.
3. **Other** and its small version go into the picker's Dipole field group.
4. Unticked icons leave the picker list, but a user who has one chosen keeps it working.
5. `icon.icns`, `icon.ico`, `Assets.car` and the favicons are regenerated on macos-latest, with Dark staying navy. The Dock shows the new icon with the next desktop build, through the release gate only.

Point `ic6/ship6.py` and `svgs6.js` at `round5/icons5b.js` and `small5b.js`.
In Icon Composer the tapered rings stay one layer: their depth shading is drawn, so the system's specular stays off for them or is kept faint.
