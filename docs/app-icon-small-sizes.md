# AudioLab small icons: how they are made, MS2 and a small M5c (task IC9)

Pick page: **AudioLab small icons: how they are made, MS2 and a small M5c**, https://claude.ai/artifact/EK4Gq95FjovreZoYXMwPaJ

> "For the zoomed ones: let's try MS2. I want the lit one, not the flat one. And let's try an M5c, the actual one, the non-flat one, and let's do some research on how to make icons like this smaller. And how do you do it? Do you zoom in or whatever? I actually really don't know." (28 November 2026, 01:20 Brussels)

Nothing in the app changed: no edit to `index.html` or `desktop/`. Everything is in `tools/icon-lab/round5s/` and this doc. Rounds 5b (IC7) and 5c (IC8) run next to this one and are untouched.

## How small icons are made, in plain words

**Short answer.** Designers do zoom in, but in two different senses. First, they work zoomed in on the screen (800 to 1600 %) on the actual 16 × 16 or 32 × 32 pixel grid and redraw that size by hand. Shrinking the big picture is not enough. Second, the drawing itself is sometimes zoomed: it is cropped to the part people recognise. MS2 does this. The other common move keeps the whole picture and takes detail out: fewer lines, a bigger centre, heavier strokes. The small M5c (MC) does this. Each small size is then checked at 100 % in the places it really shows.

**Why not just scale down?** A 16 px icon has 256 pixels. When M5c is scaled down from 1024:
- every line becomes thinner than a pixel and turns into grey haze;
- the fine field lines vanish;
- the nucleus shrinks to about five pixels and the electron to two.

The page shows M5c scaled down next to MC1 drawn for 16 and for 32.

The techniques, with where they come from:
1. **A separate master per small size** instead of one picture scaled down. Bjango keeps simplified layers for the tiniest sizes and switches them on. Louie Mantia: removing detail from a small icon matters as much as adding detail to a big one. KDE: "an icon isn't really one icon at all" but a family of sizes.
2. **Take detail out.** Apple asks for "simplicity" and a minimal number of shapes, and warns against "extremely thin line weights". Microsoft asks for few shapes and layers and gradients of one or two steps.
3. **Zoom into the recognisable part.** Crop so the nucleus and its orbits fill the tile and get cut by the edges (W7, J9, S1, MS2). No guideline names this as a rule. It is a common way to keep the shapes big enough to read. Evil Martians: for a favicon that blurs at 16, make "a special version of the logo".
4. **Thicker lines and more contrast as it shrinks.** Lines do not shrink in proportion: 1 px at 16, about 1.4 at 32. Microsoft asks that at least half of the icon have 3:1 contrast on both light and dark.
5. **Pixel fitting.** Snap edges to whole pixels so they stay sharp:
   - a round shape of odd width is centred on a pixel centre, one of even width on a pixel corner;
   - a line's outermost point lands on the grid;
   - check again at 2x (Bjango; Material: whole-number coordinates).
6. **2x is its own size.** 16 pt on a Retina screen has 32 × 32 pixels. It keeps the 16 drawing's level of detail with finer pixels; it is not the 32 pt icon. Bjango lets the 2x reuse the 1x drawing. Mantia notes there is no settled rule.
7. **Keep the family.** Same colours, silhouette and idea at every size (Apple: consistent features across appearances; GNOME: the same metaphor).
8. **Test where it really shows**, at 100 %, on light and dark:
   - Dock, Finder list;
   - Windows title bar and taskbar;
   - a browser tab (Microsoft's size table; Adobe: shrink it, look away, glance back).

**Where the small sizes show**

| Place | Size | Master used |
|---|---|---|
| macOS Finder list, sidebar, Spotlight | 16 pt (16 / 32 px) | icns 16 at 1x and 2x |
| macOS Finder small icon view, Get Info, smallest Dock | 32 pt (32 / 64 px) | icns 32 at 1x and 2x |
| Windows title bar, context menu, tray | 16 · 20 · 24 · 32 at 100 · 125 · 150 · 200 % | ico 16, 20, 24, 32 |
| Windows taskbar, search, Start all apps | 24 · 30 · 36 · 48 | ico 24 and up |
| Browser tab | 16 px (32 on Retina) | favicon 16 and 32 |
| macOS menu bar | only if the app adds an item | a one-colour template glyph, not the app icon |

Microsoft's bare minimum for an .ico is 16, 24, 32, 48 and 256. The full set adds 20, 30, 36, 40, 60, 64, 72, 80 and 96.

Apple's current guidance asks for one 1024 picture, and the system scales it. A macOS 26 Icon Composer file has no slot for a hand-drawn 16. Hand-drawn small sizes still go in through the classic routes:
- the .icns file, with 16 and 32 at 1x and 2x, which AudioLab already ships;
- the asset catalog's All Sizes slots;
- the .ico on Windows.

Whether macOS 26 prefers the .icns slots over the Icon Composer file in the Finder list is **not verified**. The implementation task checks it on a Mac.

## The designs

Each design is drawn in `small5s.js` as its own master for 16, 20, 24 and 32 pt, at 1x and 2x, in both frames: the full tile (Windows, favicon) and the Apple grid (icns).

At every size and in every design:
- **Nucleus:** lit from the top left, with a glow. It is never flat.
- **Pixel fitting:** nucleus and electron have whole-pixel diameters on the grid. Each orbit is scaled a hair so its widest point lands on the grid.
- **Electron:** it moves out along its orbit until it clears the nucleus by a pixel and stays inside the tile.
- **Orbit opacity:** at 16 and 20 the see-through orbits go almost opaque, because one pixel at 75 % turns grey.
- **2x masters:** each keeps its point size's level of detail, with lines 1.75 times wider.

### MS2 developed: the zoom (nucleus low left, field tilted 24°, outer orbit cut by the edges)
| Code | Name | What it is |
|---|---|---|
| MS2a | Lit, electron clear | Round 5's MS2 with one fix: at 16 and 20 px its electron touched the nucleus. Nucleus a pixel bigger than MS1, soft glow. |
| MS2b ★ | Lit, stronger | Heavier, almost opaque orbits. The nucleus two pixels bigger than MS1, with a stronger glow. The electron is lit with a small glow from 24 px, and from 24 px a one-pixel light edge runs along the top (the glass edge of K5a and M5d, reduced). |
| MS2c | Glowing poles | M5c's idea inside the zoom: see-through orbits (74 %) running in close, so they brighten at the poles. The strongest glow of the four. The dimmest at 16. |
| MS2d | Three arcs at 32 | Like MS2a at 16 and 20. A third arc from 24 px. At 32, a hairline field line past the edge (the step to M5d). Light top edge from 24 px. |

### A small M5c: the whole picture, simplified
| Code | Name | What it is |
|---|---|---|
| MC1 ★ | Whole, simplified | M5c itself: the nucleus near the middle, half orbits left and right, tilt 10°, the electron on the right. One orbit pair at 16, two at 20 and 24, three at 32. Orbits at 80 %, so they brighten at the poles (near-opaque at 16 and 20). Wide glow. Light top edge from 24 px. |
| MC2 | Big glowing core | The nucleus two pixels bigger with the strongest glow. One orbit pair up to 20 px, two from 24, gathering close to the nucleus. At 16 it is a bright sun with one orbit. |
| MC3 | Closer whole | M5c a quarter closer. The outer orbit runs out past the left and right edges, like M5d's lines to the edge. Two orbits, three at 32. Sits between MC1 and the MS2 zoom. |

The page shows each design:
- at 1:1 on dark and light (a Retina screen shows the 2x master);
- magnified: 16 and 32 at 1x and 2x, then 20 and 24;
- next to M5c and M5d at 128 and 64, and next to S1 as shipped;
- in mock-ups:
  - the macOS Dock at its smallest (32 pt), on dark and light;
  - the Finder list (16 pt), on dark and light;
  - a browser tab with its favicon;
  - the Windows 11 title bar (16 px) and taskbar (24 px), on dark and light;
  - the menu bar, with a template glyph sketch (AudioLab has no menu bar item today).

There is a P2 / P8 switch. The picks bar gives one line, for example:

`Small icon picks: MS2b MC1`

(`P8` is added when Chart paper is on.)

## Recommendations (stars on the page)
1. **MS2b**: the zoom you asked for, done the way the research says: heavier lines, near-opaque orbits, a bigger lit nucleus, the light top edge from 24 px. It holds in the Finder list and on a light desktop, where MS2a and MS2c fade. It is the small version of the M family (M5d, picked at 01:13).
2. **MC1**: the actual M5c at every size, with less detail as it shrinks. It is the clearest family link to the big icon, if the small icon should not be a crop.

Weak spots seen in the renders:
- At 16 px every MS2 is mostly the nucleus and the electron with two arcs. The orbits read as orbits from 20 to 24 px.
- MS2c is the dimmest at 16.
- On the Apple grid at 16 pt (a 14 px tile) the MC row gets crowded, and MC3 loses its outer orbit.
- The electron at 16 is 3 px, a small cross rather than a round dot.
- In P8 the glow tints the paper round the nucleus.

## Files (`tools/icon-lab/round5s/`)
| File | What |
|---|---|
| `small5s.js` | MS2a to MS2d and MC1 to MC3: `smallSvg(id, P, pt, scale, frame)`, plus the menu bar template sketch. Reads the palettes from `round5/icons5.js`. |
| `render5s.js` | PNGs with `rsvg-convert`:<br>- `renders/small/<id>-<P>-<pt>@<s>x[-mac].png`<br>- references: S1 from `ic6/small6.js` and round 5's MS2 in `renders/ref/`<br>- M5c and M5d at 512, 128 and 64 in `renders/big/`<br>- the before and after in `renders/ba/`<br>- `renders/sheet-<P>.png`<br>- `renders/manifest.json` |
| `page.src.html`, `build_page.py`, `pick-page.html` | The pick page (the self-contained build, PNGs as data URIs, is what was published). |

Regenerate: `node render5s.js && python3 build_page.py`.

## What the implementation task does after the pick
1. The picked MS2 becomes the small version of the M-family icon that ends up as Main or Other (round 5b decides):
   - `icon.icns` at 16 and 32 pt, 1x and 2x (each 2x drawn for its point size);
   - `icon.ico` at 16, 20, 24 and 32;
   - the `web-16` and `web-32` favicons.

   This goes through `ic6/ship6.py` with `round5s/small5s.js` (`smallSvg(id, P, pt, 2, 'mac')` for the 2x slots).
2. The picked MC goes with M5c wherever M5c is used (for example the picker's small 16 and 32).
3. Check on a Mac whether macOS 26 uses the .icns small slots in the Finder list when `Assets.car` (Icon Composer) is present.
4. Regenerate on the macOS runner. Any `index.html` change (the browser tab icon) waits while `desktop/release-freeze.json` is on main. Promotion to installed apps goes through the release gate only.

## Sources
- Apple Human Interface Guidelines, App icons: https://developer.apple.com/design/human-interface-guidelines/app-icons
- Apple, Creating your app icon using Icon Composer: https://developer.apple.com/documentation/xcode/creating-your-app-icon-using-icon-composer
- Apple, Configuring your app icon using an asset catalog: https://developer.apple.com/documentation/xcode/configuring-your-app-icon
- macOS icon sizes (MakeAppIcon; Apple no longer prints the table): https://makeappicon.com/macosicon
- Chromium, Mac icons: https://chromium.googlesource.com/chromium/src.git/+/fafff21/docs/mac/icons.md
- Microsoft, App icon construction: https://learn.microsoft.com/en-us/windows/apps/design/iconography/app-icon-construction
- Microsoft, App icon design: https://learn.microsoft.com/windows/apps/design/iconography/app-icon-design
- Material Design (2014), Icons: https://m1.material.io/style/icons.html
- Bjango, My Mac app icon design workflow: https://bjango.com/articles/macappiconworkflow/
- Bjango, My icon design workflow: https://bjango.com/articles/icondesignworkflow/
- Bjango, Designing for Retina: https://diagnostics.bjango.com/articles/designingforretina/
- Bjango, Smaller Mac app icons: https://bjango.com/articles/smallermacappicons/
- Louie Mantia, 1024×1024: https://lmnt.me/blog/1024x1024.html
- John Marstall, The double-drawn method of icon design: https://medium.com/bpxl-craft/the-double-drawn-method-of-icon-design-b6d7f1742ad2
- Nuno Pinheiro (KDE), Small icons, big problems: https://planet.kde.org/nuno-pinheiro-2026-07-19-small-icons-big-problems/
- Evil Martians, How to Favicon in 2026: https://evilmartians.com/chronicles/how-to-favicon-in-six-files-that-fit-most-needs
- GNOME HIG, App icons: https://developer.gnome.org/hig/guidelines/app-icons.html
- Adobe Design, How to design effective icons, part 2: https://adobe.design/stories/leading-design/how-to-design-effective-icons-part-2

Nothing was found from the Iconfactory or Michael Flarup on small sizes specifically. Two pages could not be opened: the Win32 "Icons" UX guide, and the Material 2 and 3 pages (which need JavaScript).
