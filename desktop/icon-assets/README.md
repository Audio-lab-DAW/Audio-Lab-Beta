# AudioLab Pro icon assets: Ocean Yellow

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
| dock-icon.png | desktop/dock-icon.png | Mac Dock icon at runtime (main.js) |
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
