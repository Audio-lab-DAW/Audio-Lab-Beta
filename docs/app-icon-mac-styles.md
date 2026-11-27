# The Mac app icon under macOS 26 icon styles (task IC1)

27 November 2026. Desktop app only; `index.html` is not touched.

## The report

On the user's Mac (dark mode) the AudioLab Pro icon showed with a **black** background: white rings, yellow dots.
Wanted: always the blue square with the Ocean Yellow W7 logo.

## Short answer

- The black icon is made by **macOS 26 (Tahoe)** itself. Under System Settings > Appearance > "Icon & widget style" > **Dark**
  it redraws every app icon that brings no dark version of its own: it finds the background colour of the picture and replaces it
  with its black tile, keeping the light parts. Our app shipped only an `.icns` (plain pictures), so it got this treatment.
  This was reproduced on a macOS 26.7 build machine: same `icon.icns`, style Dark, black tile, white rings, yellow dots.
- The fix: the app now also carries an **Icon Composer icon** (`Assets.car`, named by `CFBundleIconName`) whose dark version is
  set to the same blue as the default one. macOS 26 then uses our dark version instead of making its own.
  Proven on the build machine: the built app's icon under Dark is pixel for pixel the icon under Default (blue).
- **Tinted** and **Clear** cannot be blue. In those two styles macOS throws every app's colours away by design (Apple's own apps
  too): Tinted shows the shape in the one tint colour the user picked, Clear shows it as grey glass. The developer has no say.
- While the old app was **running**, its Dock icon was already blue (the app sets a picture on the Dock at start, and the Dock
  leaves such a picture alone). The black one showed wherever macOS draws the app's own icon: the Dock tile when the app is
  not running, Finder, Launchpad, Spotlight, the app switcher's first frame.

## Research

### How macOS 26 picks an app's icon

- Two Info.plist keys can name an icon. `CFBundleIconFile` names an `.icns` file in `Contents/Resources` (the old way, a set of
  plain pictures, one per size). `CFBundleIconName` names an icon inside `Contents/Resources/Assets.car`, the compiled asset
  catalogue. From macOS 26 on, the icon in `Assets.car` can be a layered **Icon Composer** icon (an `IconImageStack`): a
  background fill plus picture layers, with separate values for the default, dark and tinted appearance. macOS 26 prefers it;
  older systems that do not find a usable icon under that name fall back to the `.icns`.
  Sources: Apple, "Creating your app icon using Icon Composer" (developer.apple.com/documentation/Xcode/creating-your-app-icon-using-icon-composer)
  and WWDC25 session 361 "Create icons with Icon Composer" (developer.apple.com/videos/play/wwdc2025/361);
  Hendrik Erz, "Supporting Liquid Glass Icons in Apps Without Xcode"
  (https://www.hendrik-erz.de/post/supporting-liquid-glass-icons-in-apps-without-xcode): set `CFBundleIconName`, keep the `.icns`
  ("Don't just throw out your existing .icns-file").
- The four styles (Default, Dark, Clear, Tinted) are a system setting, not the same thing as dark mode, although "Dark" follows
  dark mode when the style is set to Automatic. MacRumors, "macOS Tahoe's New Theming System Explained"
  (https://www.macrumors.com/2025/06/13/macos-tahoes-new-theming-system-explained/).

### What macOS 26 does to an app with no variants of its own

- Dark: "macOS draws its own darkened version of such an icon"; an `.icns`-only app showed "as a black tile" with its mark kept
  (TraceRoost pull request 421, https://github.com/traceroost/core/pull/421). GitButler's issue 11481 says the same: macOS
  "automatically adapts app icon to dark mode" (https://github.com/gitbutlerapp/gitbutler/issues/11481).
- An `.icns` that does not sit on Apple's grid is shrunk onto a light grey plate, from 26.6.2 also in the Default style
  (PwrGit pull request 196, https://github.com/pwrdrvr/PwrGit/pull/196). Ours sits on the grid (824 px tile, 100 px margin of
  1024), and the build machine drew it without a plate.
- Our own measurement on macOS 26.7.2 (GitHub runner, see "Proof" below) agrees: the `.icns`-only app is blue under Default,
  black tile under Dark, one-colour under Tinted, grey under Clear.

### What `app.dock.setIcon` does under the styles

- Electron's `app.dock.setIcon(image)` sets AppKit's `NSApplication.applicationIconImage`. A picture set this way is a flat
  bitmap; macOS "never" applies the style treatments to it (cmux pull request 11199,
  https://github.com/manaflow-ai/cmux/pull/11199), and setting one "silently disables the Tinted/Clear Dock icon treatments"
  (cmux pull request 4108, https://github.com/manaflow-ai/cmux/pull/4108). Handing back `nil` lets "macOS render the layered
  bundle icon" again (same pull request).
- Electron cannot take an Icon Composer icon in `setIcon`: "This is not technically possible", the icon has to be compiled into
  the bundle; with the icon in the bundle it "works the same as for any other macOS app (no `setIcon` needed)"
  (Electron issue 48476, https://github.com/electron/electron/issues/48476).
- Our own measurement: the released desktop app (DMG 0.219, the newest one) running under Dark has a blue Dock icon (the bitmap is left alone); the new app,
  which sets no picture for the default icon, is blue too (the bundle icon with our dark version).

### How apps not built with Xcode ship an Icon Composer icon

- The `.icon` document is a folder: `icon.json` plus `Assets/` with the layer pictures (PNG, SVG). Apple does not publish the
  format; the reference used here is the reverse-engineered one in https://github.com/peterpoliwoda/icon-composer-template.
- It is compiled with Xcode's `actool` (Xcode 26 is the first that reads `.icon`):
  `xcrun actool AppIcon.icon --compile <dir> --app-icon AppIcon --platform macosx --target-device mac --minimum-deployment-target 26.0 --output-partial-info-plist <file>`
  (Hendrik Erz, above; pladder pull request 96, https://github.com/dinooo13/pladder/pull/96). The result is `Assets.car`
  (and a small `.icns` we do not use). `assetutil --info Assets.car` lists what is inside.
- electron-builder compiles a `.icon` given as `mac.icon` by itself only from version 26.2 on (Bruno pull request 9433,
  https://github.com/usebruno/bruno/pull/9433; PwrGit and TraceRoost use 26.15). This project is on electron-builder 25.1.8, and
  that way would also replace our hand-made `icon.icns` with actool's (which stops at 256 px). So the other known way is used:
  compile `Assets.car` in the workflow, ship it with `extraResources`, set `CFBundleIconName` through `extendInfo`, and leave
  `icon.icns` and `CFBundleIconFile` as they are (Bruno does the same).
- Build machines: the GitHub image `macos-15-intel` (used for the release build) has Xcode 16.4 as its default but also has
  Xcode 26.x installed; `macos-26` has Xcode 26.6 and the Icon Composer command line renderer `ictool`
  (https://github.com/actions/runner-images, issue 14167 there). The build picks the newest Xcode 26 or later for the one actool step.

## What was built

| Piece | Where | What |
|---|---|---|
| Icon Composer document | `desktop/icon-assets/mac-icon/AppIcon.icon` | `icon.json` + `Assets/mark.png`. Written by `make_icon.py` beside it from the W7 source `icon-assets/shortcut/shortcut-L.svg`. |
| Compile step | `desktop/scripts/build-mac-icon.sh` | Picks Xcode 26+, runs `actool`, checks the result (`tools/mac-icon/check-car.py`), writes `desktop/build/Assets.car` (not committed, built each time). |
| Packaging | `desktop/package.json` | `mac.extendInfo.CFBundleIconName = "AppIcon"`; `Assets.car` goes to `Contents/Resources`. `CFBundleIconFile = icon.icns` stays (electron-builder writes it from `build/icon.icns`, unchanged). |
| Guard | `desktop/scripts/afterPack.js` | A release build stops before the DMG is made if `Assets.car`, `icon.icns` or either plist key is missing. |
| Dock while running | `desktop/main.js` | macOS 26+ with `Assets.car` in the bundle: the default icon sets no Dock picture (the bundle icon shows); coming back from another icon hands the Dock back with `setIcon(null)`. The other 48 picker icons, and every icon on macOS 15 and older, work as before. |
| Workflow | `.github/workflows/desktop.yml` | Mac build compiles the icon first. New job "Mac icon proof" on `macos-26` takes the finished DMG, checks it, draws the icon in every style, photographs the Dock, uploads the pictures, and fails if Default or Dark is not blue. |
| Check without a build | `.github/workflows/mac-icon-check.yml` | Run by hand: compiles and draws the icon on `macos-26` and `macos-15-intel`. |
| Tools | `tools/mac-icon/` | `proof.sh` (pictures + colour check), `dock-shot.sh` (Dock photographs), `render-icon.swift` (asks macOS for a file's icon), `check-car.py`. |
| Test | `tools/ui-tests/taskAH_electron.js` | 4 new checks for the macOS 26 Dock path (21 in all, all pass). |

### The document

- Fill: Ocean blue `#1450A8`, written as three `fill-specializations` entries: default, `dark`, `tinted`, all the same value.
- One group, one layer `mark.png`: the white rings and the yellow nucleus and electron of W7 on a transparent full-bleed
  1024 px canvas. macOS cuts the rounded shape and adds the margin. The blue of the source was turned into transparency exactly
  (white and yellow both have red = 255, so the share of the mark in a pixel is (R − 20) / 235); laid back over the blue the
  layer differs from the source by at most 1.4 of 255.
- Effects off: `glass: false`, `specular: false`, shadow `none`, translucency off. The icon is meant to look flat, as today.

### Two things learned the hard way (both seen on the build machine)

1. With a plain `"fill"` key **beside** `"fill-specializations"`, the dark entry is ignored and the Dark icon is black again.
   The fill must be written only as specializations, with the default as an entry without `appearance`.
2. The icon service answers the first request for a new app with a quick picture that can be the old automatic treatment;
   the right one comes a moment later. The proof asks twice and keeps the second.

## Proof (no Mac here; GitHub's macOS 26.7.2 machine)

How the styles were switched: `defaults write -g AppleIconAppearanceTheme RegularDark | TintedDark | ClearDark` (key absent =
Default) plus `AppleInterfaceStyle Dark`, then the icon service and the Dock restarted. The Dock's own icons turned dark, so
the setting took.

| Check | Result |
|---|---|
| `assetutil --info Assets.car` | Layered `AppIcon` present for `NSAppearanceNameAqua`, `NSAppearanceNameDarkAqua`, `ISAppearanceTintable`; the tile of all three is the colour 0.078, 0.314, 0.659 (the blue). Before fix 1 above the dark tile was the system's grey gradient. |
| Icon Composer's own renderer (`ictool`), Default and Dark | Both blue. |
| macOS drawing the icon (`NSWorkspace`), app with `icon.icns` only | Default blue; **Dark black tile, white rings, yellow dots** (the report, reproduced); Tinted one colour on black; Clear grey. |
| macOS drawing the icon, app with `Assets.car` | Default blue; **Dark blue, 0.00 difference to Default** at 512 px; Tinted and Clear as above (system treatment). |
| Same for the really built AudioLab Pro.app | Same result: Default and Dark blue, tile colour 21, 80, 168 against 20, 80, 168 wanted. |
| Default against today's picture (`dock-icon.png`) at 512 px | Tile box identical (50 to 461 px in both, so no grey plate and the same margin). Mean difference inside the tile 1.6 of 255; 1.4 % of pixels differ by more than 24, all on the edges of the rings (smoothing) and the tile's rim, where macOS 26 adds its thin light edge. The old `.icns` drawn by macOS 26 differs from the same reference by 3.2, so the new icon is the closer one. |
| Real Dock, style Dark (photographs of the build machine's screen, `docs/app-icon-mac-styles/dock-macos26.png`) | Released desktop app (DMG 0.219) kept in the Dock, closed: **black tile**. The same app open: blue (its own picture). New build closed: **blue**. New build open: **blue**. |
| The four styles as macOS draws the new app (`docs/app-icon-mac-styles/styles-macos26.png`) | Default blue, Dark blue, Tinted and Clear the system's treatment; beside them the old app's Default and Dark. |
| Windows | `desktop/build/icon.ico` not touched (sha256 unchanged, see the log); the Windows part of `package.json` and the Windows code path in `main.js` are unchanged. |

## What macOS decides and we cannot change

- **Tinted**: one colour for every app, the user's tint. Our rings and dots show in that colour on a dark tile.
- **Clear**: grey glass for every app.
- The thin light rim and the soft shadow macOS 26 puts on every icon.
- One picture for all sizes: an Icon Composer icon is drawn by macOS at every size from the same layers, so on macOS 26 the
  hand-drawn small versions inside `icon.icns` (the simple logo at 16 to 20 px, thicker lines at 24 to 64 px) are no longer
  used. Small icons (Finder list view) show W7 scaled down.
- macOS 15 and older: `actool` also puts flat pictures of the icon into `Assets.car` for those systems, and they take them
  instead of `icon.icns` (seen on the macOS 15 machine: the same W7 picture with a faint light rim; the switch
  `--enable-icon-stack-fallback-generation=disabled` did not remove them with Xcode 26.6). `icon.icns` stays in the app and
  in Info.plist as the fallback.

## Not verified without a real Mac

- The user's own Mac: Finder, Launchpad, Spotlight and the Dock there. macOS keeps an icon cache per app; after replacing the
  app the old black picture can stay until the Dock restarts or the user logs out and in once.
- `app.dock.setIcon(null)` (back to the bundle icon after choosing another icon and returning to Ocean Yellow) was run only
  against a recording stand-in, not a real Dock. If Electron refused null, the code falls back to the old blue picture.
- Tinted and Clear in a real Dock (only drawn through `NSWorkspace`).
- `assetutil` on macOS 15 cannot read the layered entries, so the release build (on `macos-15-intel`) only counts them; the
  strict check of the three appearances runs afterwards in the proof job on macOS 26.

## What the user should check

1. Install the newest DMG (drag over the old app). With the style on Dark (or Automatic in dark mode): the icon in the
   Applications folder, in Launchpad and in the Dock (app closed and app open) is the blue square.
2. If it is still black right after installing: log out and in once (icon cache), then look again.
3. Settings > App icon: pick another icon, then Ocean Yellow again; the Dock goes back to the blue icon.
4. Tinted and Clear will not be blue; that is macOS.
