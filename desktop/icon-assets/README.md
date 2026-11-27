# AudioLab Pro icon assets: J3 "Dipole Field" (task IC4, 27 November 2026)

Since IC4 the app icon is **J3** from round 3 (`docs/app-icon-round-3.md`): the dipole field tilted 10 degrees round the yellow nucleus,
with the thinner W7 rings at 90 % so the field shows through them, in **Orbit night** (P2: tile #132044 to #070910, rings #EAF1FF,
nucleus #FFC43C, electron #4CC9F0, field #6096FF). Everything is drawn from code: `python3 tools/icon-lab/ic4/ship.py` writes every file
below (it reads `tools/icon-lab/round3/icons3.js` and `tools/icon-lab/ic4/small.js`).

| Size | Picture |
|---|---|
| 128 px and up | J3 (full detail); 96 px J3 at its bold level |
| 64 px and below | the **small master** (`tools/icon-lab/ic4/small.js`): the zoomed, tilted W7 crop, thin rings (about 1 px at 16, 1.3 px at 32, 2.3 px at 64) at 90 %, nucleus and electron with whole-pixel sizes on the pixel grid, the ring edges on pixel centres |

- `icon.icns`: 16 pt and 32 pt (1x and 2x) the small master on the Apple grid, 128 to 512 pt J3. `icon.ico`: 16, 20, 24, 32, 40, 48, 64 the small master, 96, 128, 256 J3.
- `dock-icon.png`, `icon.png`: J3 on the Apple grid at 1024. `web-*.png` and the website's favicons: 16, 32, 48 the small master, 180 to 512 J3.
- `mac-icon/AppIcon.icon`: fill #132044 for the default, dark and tinted appearance (Dark stays navy); one layer, the whole J3 picture taken apart against that fill (`mac-icon/make_icon.py`).
- Picker: group "Dipole field" first: Dipole Field (J3, default), Field Orbits (J4), Porthole Field (J6), Measured Field (J8), Measured Field, Chart Paper (J8 P8), Field Dial (J10), Field Dial, Chart Paper (J10 P8). Each has `picker/<id>.png` (512, Apple margin), `thumb/<id>.png` (128) and `small/<id>-{16,32,48}.png` (its own small versions, used in the Windows .ico the app writes for a choice). `icons.json` has `previous_default: ocean-yellow`: a choice of Ocean Yellow saved before IC4 means the default and now gives J3.
- `shortcut/` keeps the W7 files of task AH (v0.219) as a record; nothing ships from there any more.

## Before IC4: Ocean Yellow

Final app icon: the tapered atom with a satellite electron (design code PR4), colour **Ocean Yellow**.
Ocean blue tile `#1450A8`, white rings `#FFFFFF`, yellow nucleus and electron `#FFD23A`.

## Geometry
- Optically centred: the mark's centre of weight sits at (512, 504) on a 1024 canvas, a few px above the true centre.
- Four size tiers, each drawn separately (thin lines vanish at small sizes). Ring width runs from thin side w·(1−taper) to thick side w·(1+taper):

| Tier | Used at | Ring w | Taper (thick:thin) | Nucleus / electron |
|---|---|---|---|---|
| L | 128 px and up | 44 | 0.46 (2.7:1) | 80 / 46 |
| M | 48 to 64 px | 64 | 0.60 (4:1, exaggerated) | 92 / 54 |
| S | 24 to 32 px | 80 | 0.60 (4:1, exaggerated) | 112 / 64 |
| XS | 16 to 20 px | 80 | none (taper cannot show) | 118 / 68 |

`icon.icns`, `icon.ico`, `doc.icns`, `doc.ico` and the `web-*` favicons already contain the right tier at each size.
`source/` has the tier SVG/PNG files (full-bleed `icon-*`, Apple-grid `icon-grid-*`).

## Files
| File | Goes to | Purpose |
|---|---|---|
| icon.icns | desktop/build/icon.icns | Mac app icon (Apple grid: 824 px tile, 100 px margin) |
| icon.ico | desktop/build/icon.ico | Windows app icon (16–256 px) |
| icon.png | desktop/build/icon.png | 1024 px source used by electron-builder |
| dock-icon.png | desktop/dock-icon.png | Mac Dock icon at runtime (main.js) on macOS 15 and older |
| mac-icon/AppIcon.icon | compiled to Assets.car at build time | Icon Composer icon for macOS 26: W7 on the blue in the Default AND the Dark icon style (task IC1, `docs/app-icon-mac-styles.md`). Regenerate with `mac-icon/make_icon.py`; compile with `desktop/scripts/build-mac-icon.sh` |
| doc.icns / doc.ico | desktop/build/doc.* | `.audiolab` project file icon |
| web-16/32/48/180/192/512.png | web app | favicons, apple-touch-icon, manifest |
| mark-black / mark-white / mark-colour | branding | logo without the tile |
| picker/*.png + icons.json | Settings → App icon | 49 choices; default `ocean-yellow` |

## Picker groups (icons.json)
1. **Main logo colours**: Ocean Yellow (default), Ink Electric, Charcoal Ember, Teal Coral, Navy Cream
2. Spirograph & fractal, Realistic 3D, Decades, 1950s illustration, Scientific illustration, Atom models in history (44 alternates, all with plain names; design codes kept only in `design_code`).

## `.audiolab` question-mark fix
electron-builder needs the file type exported, not only associated:
`fileAssociations[0]` keeps `icon: "build/doc"`, and `mac.extendInfo` gets
`UTExportedTypeDeclarations` for `com.audiolab.project` (conforms to `public.data`, extension `audiolab`, icon `doc.icns`)
plus `LSItemContentTypes: ["com.audiolab.project"]` and `LSHandlerRank: "Owner"` in the document type.
