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
