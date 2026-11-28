# Themes for AudioLab: research, design and picks (task TH1)

28 November 2026. Pick page artifact: https://claude.ai/artifact/DYx81SWUzRiJADYuHAJZLF. Research and pick-page task only: nothing in `index.html`, `desktop/` or `native/` was changed. Pick page: `tools/design-lab/th1/pick-page.html` (published as the artifact "AudioLab themes"). Measurements: `tools/design-lab/th1/check.py`, results in `themes.json` and `report.md`.

The user's request (28 Nov, 01:27 Brussels, shortened): build a system for different themes. Today's theme counts as the "normal" one, based on the dipole field and field depth icons (J3 P2, M5 P2). Other themes: the P8 colours (J3, J8, J10 in P8); RC2 three rings as an old-school Space Race theme; science fair and chalkboard; also cutaway nucleus, blueprint, Dalton sphere, Rutherford scattering, Chadwick; patent drawing as the lightest. Research how applications and music programs do themes and how to keep complex programs readable. Everything must stay readable and no UI element may break.

## 1. Summary

- **15 themes proposed**: TH-A (today, unchanged), B Chart paper (light) with its dark half B2, C Space Race, D Chalkboard, E Blueprint, F Dalton sphere, G Cutaway nucleus, H Rutherford scattering, I Chadwick (light), J Patent drawing (the lightest), and four new ones from the same images: K Cyanotype, L Atomic age, M Phosphor, N Deep orbit.
- **Every new theme passes every readability rule.** That is 20 rules and 94 measured pairs per theme: WCAG 2.2 ratio and APCA level for text, 3 : 1 for controls and graphics, meaning colours kept apart, and track colours measured under protan, deutan and tritan simulation (smallest CIEDE2000 12 to 23; today's palette is 1.0 under protan).
- **Theme A keeps today's five known misses**: the quiet grey over glass, labels over glass on bright clips, disabled text, the ruler numbers, and white on the blue accent buttons. The user declined E1 to E9 of the long-sessions round, so A is left as it is. The gate treats them as a baseline.
- **Glass needs a floor.** To keep quiet text readable over the brightest clip behind a glass panel, the glass tint has to be 80 to 85 % in most themes (today it is 50 %, and today's quiet text fails there). Two ways: raise the tint per theme, or have the glass engine put a slightly thicker tint only behind text runs (proposed). The page compares "Theme's floor", "Today's 50 %" and "Solid".
- **Device displays stay dark wells in every theme**, including the light ones. This follows the user's display-first devices and keeps meters, scopes and science drawings measured against one known dark ground. It also keeps most of the 4,300 literal colours in `index.html` valid.
- **The system**: semantic tokens on top of LOOK (same names in every theme, values change, meanings never), one JSON theme file per theme in the W3C Design Tokens format, live switching with no reload and no per-frame cost, "Icon follows theme" through the icon picker, and `check.py --gate` as a release-gate step.
- **Recommended** (stars on the page): A ★★★★★, B ★★★★★, E ★★★★★; then B2, C, D, G, H, J, K, N ★★★★.

## 2. How themes work today

| Layer | Where | What it holds |
|---|---|---|
| CSS custom properties | the `:root` rules at the top of the style block, LK's block before `.dacv` | `--bg --pn --pn2 --ln --ink --mut --acc --blue --gtr --gtr2 --glass --glassb`, `--bl3 --blf --blu1 --blu2`, task LK's `--sel --sel3 --meas --unit --lim-warn --lim-over --lk-hair --lk-tick`, type tokens `--fs1..4 --fw4..6`, lane F's `--ov-*` |
| `LOOK` (task LK) | `lkMake()` | grid levels (G3), hairlines (W1), ink, quiet grey, label grey, units amber (L2), selection yellow (A1), warn, over, ok, density (N3); INS (lane E) reads it through `INS.look()` |
| `TH` | `applyTheme()` | lanes, ruler, grid, map from three Settings sliders: hue 215, tint 25 %, background 40 % |
| `THEMES` "Studio themes" (v0.171) | `const THEMES=[`, `thPaint()`, `thPick()`, `thCard()` | 8 looks of other programs (AudioLab, Live, FL, Cubase, Logic, Bitwig, Pro Tools, Reaper): panel colours, accent, arrangement, clip shape, fader design (21 designs), meter colours, track palette |
| Glass | `applyTrans()`, the glass engine (docs/glass-engine-plan.md) | `--ga` opacity (1 − Transparency, 50 % by default), `--blur`, `--edge`; `thGlass()` forces 90 % on light arrangements |
| Comfort (lane P) | docs/comfort-build.md | OLED care (dims static brights), Night mode (brightness and warmth filter), Focus mode |

"Light mode" in AudioLab is the performance mode for slow computers (`UI.lite`), not a colour theme.

**What has to change.** `index.html` has about 4,300 hex literals and 2,400 `rgb()`/`rgba()` literals; about 1,200 places read a CSS variable. The most common literals are device and science colours (`#4cc9f0` 280 times, `#3ecf8e` 255, `#f5c84c` 190). With displays kept as dark wells, only the chrome has to move to tokens: panels, strips, text, lines, menus, dialogs, track headers, lanes, the ruler, the transport and the clips' frames. The canvas drawers already read `LOOK` and `TH`; they need the new token names in those objects, not a rewrite. `THEMES` becomes the theme list; the 8 studio looks become a group "Other programs" in the same format, keeping their fader and clip shapes as extras.

## 3. Research

### 3.1 Music programs

| Program | What the user can change | Format | Notes |
|---|---|---|---|
| Ableton Live 12 | Theme, Light/Dark/follow system, warm/cool/neutral tone, High Contrast; grid intensity, brightness, colour intensity and hue | XML `.ask`, 8-digit hex | Live 12 dark called "washed out"; Ableton pointed to zoom and contrast settings [1][2][3] |
| Bitwig Studio | One scheme; display profile, scaling, contrast | none (community patch) | No themes in Bitwig 6 (March 2026) [4][5][6] |
| FL Studio | Hue, saturation, brightness, contrast, text knobs; pickers for selection, highlight, mute lights, steps, meters, waveforms; Light mode switch | `.flstheme` | Meaning colours are user slots [7] |
| REAPER | WALTER themes; Default 7 Theme Adjuster (7.17); track colour can tint panels | `.ReaperTheme`, `.ReaperThemeZip` | The most open model [8][9][10] |
| Cubase / Nuendo | Up to 14: colour schemes, per-element colours, track Color Strength; 15: a few scheme and accent sliders | preferences | Users miss the old control; 14 thread lists low contrast and thin type [11][12][13] |
| Studio One / Fender Studio Pro | Hue shift, saturation, luminance, contrast; separate arrange grid brightness and contrast; colourise track controls, strips, plug-in headers | presets | [14][15] |
| Logic Pro | Dark app; tracks background dark, light or custom grey; regions take track colour; bright piano roll | none | Region names hard to read on bright regions [16] |
| Pro Tools | Dark (default since 2020.11) or Classic | none | [17] |
| Renoise | Every element, global HSV filter, shades | `.xrnc` XML | [18] |
| Reason | Default, Blue, Dark; restart needed | none | [19] |
| Vital, Serum 2 | Skins | JSON (Vital), folders (Serum 2, format unconfirmed) | [20] |

Patterns: most offer a few global sliders over a fixed palette (Live, FL, Studio One, Cubase 15); the open ones use text theme files (Live, REAPER, Renoise, FL, Vital); only Live follows the system appearance; track colour reach is a separate control (Cubase Color Strength, Studio One colourise switches, REAPER tint); the common complaint after a "flat" redesign is low contrast (Cubase 14 and 15, Live 12, Maschine 3).

### 3.2 Complex apps and design systems

- **Design tokens.** The W3C Design Tokens Community Group format reached its first stable version, 2025.10 (28 Oct 2025): `$value`, `$type`, aliases `{color.ink}`, a colour type with colour spaces, and a Resolver module that applies a theme as overrides on a base set [21][22][23]. Style Dictionary builds them to CSS and JS [24].
- **Tiers.** Primitive, semantic and component tokens. IBM Carbon: a token is a role that never changes between themes; only its value does [25]. GitHub Primer: base and functional tiers, 9 colour themes (including colour-blind and high-contrast sets), and a contrast check on every pull request [26][27]. Material 3: 49 colour roles, each fill paired with an "on" colour, schemes generated by tone, a contrast level setting [28]. Adobe Spectrum: colours generated from target contrast ratios with Leonardo [29].
- **Code editors.** VS Code: about 960 workbench colour ids, live preview while choosing, per-theme overrides, separate high-contrast themes with extra borders, follows the system [30][31]. JetBrains: UI theme and editor scheme are separate files; the Islands look (2025.3) asks for at least 1.2 : 1 between zones [32].
- **Creative apps.** Figma replaced about 5,100 hard-coded colours with about 350 semantic tokens and a lint rejects untokenised colours; user content never changes with the theme [33]. Blender: XML themes, about 18 editor sections, edits shown live [34]. Premiere Pro: brightness sliders and a highlight colour [35].
- **Systems.** macOS: every colour needs light, dark and increased-contrast values; app accents apply only with the Multicolor accent [36]. Windows: the accent is generated to keep contrast; contrast themes are a fixed set of 8 paired colours, test them all while the app runs [37]. CSS: `color-scheme`, `light-dark()`, `prefers-contrast`, `forced-colors` [38][39]. Electron: `nativeTheme.themeSource` and the system accent [40].

### 3.3 Readability in dense, themed interfaces

- **WCAG 2.2**: 4.5 : 1 text, 3 : 1 large text; 3 : 1 for UI components and graphics needed to understand content (1.4.11: meter fills, waveforms, fader tracks, knob arcs, clip edges); never rounded (2.999 fails) [41][42]. Colour must not be the only cue (1.4.1). Focus Appearance (2.4.13, AAA): an area as large as a 2 px perimeter changing by 3 : 1 [43]; a two-colour ring (C40) works on any background [44].
- **APCA** (apca-w3 0.1.9, constants checked in its source): Lc 90 preferred and 75 minimum for body text, 60 for other content text, 45 for large or non-body text, 30 for spot text such as disabled, 15 the invisibility point [45][46]. Not normative: WCAG 3 is still a working draft (10 Sep 2026) [47]. WCAG 2 overrates dark-on-dark pairs, so dark themes are checked with both.
- **Dark and light.** Not pure black; desaturate colours on dark (Material) [48]. Pure white on black halates for people with astigmatism [49]. In light themes the faint pairs (pale meter tracks, light gridlines) fail 1.4.11 first (seen here too: the selection yellow had to darken to gold).
- **Colour vision.** About 8 % of men of European descent have red-green deficiency [50]. Simulation: Machado 2009, applied in linear RGB [51]. A smallest CIEDE2000 of 10 between categorical colours is "friendly" (cols4all) [52]. Okabe-Ito and Tol palettes are safe but small [53]; tracks also need names or numbers.
- **Meaning colours.** Keep the meaning, let the value change per theme, check it on every surface it can sit on (Spectrum, Atlassian, Carbon, Primer) [29][54][25][26].
- **Glass.** Liquid Glass drew legibility complaints; Apple added Tinted and Reduce Transparency forces solid layers [55]. Windows: no accent-coloured text on acrylic, solid fallback [56]. Measure against the worst backdrop.
- **Automatic checks.** Primer's workflow, Terrazzo's `a11y/min-contrast`, Leonardo, axe (DOM text only; it cannot see a canvas) [27][57]. A DAW needs its own list of pairs, including canvas strokes.

## 4. The readability rules (what `check.py` measures)

Surfaces: `bg chrome ruler lane0 lane1 laneSel panel panel2 strip display`, and **glass over clips**: the theme's glass tint at its opacity over the lane, the selected lane, the background and the brightest and darkest clip body.

| Rule | Token | On | Needs |
|---|---|---|---|
| T1 Main text | ink | every surface and glass | WCAG 7 : 1 and Lc 75 |
| T2 Labels | lab | chrome, lane, panels, strip, glass | 4.5 : 1 and Lc 60 |
| T3 Quiet text (11 px, weight 500) | mut | bg, chrome, lane, panels, strip, glass | 4.5 : 1 and Lc 45 |
| T4 Disabled text | dis | panel, strip | Lc 30 (WCAG exempts disabled) |
| T5 Ruler numbers | rulerTxt | ruler | 4.5 : 1 and Lc 60 |
| T6 Units (L2 amber) on panels | unit | chrome, panel, strip | 4.5 : 1 and Lc 55 |
| T6d Units in displays | unitD | display | 4.5 : 1 and Lc 55 |
| T7 Text on accent buttons | onAccent | accent | 4.5 : 1 and Lc 60 |
| T8 Over read-out in displays | overD | display | 4.5 : 1 and Lc 45 |
| T9 Over / error text on panels | over | panel, strip | 4.5 : 1 and Lc 45 |
| T10 Text in displays | inkD | display | 7 : 1 and Lc 75 |
| U1 Accent | accent | bg, chrome, panel, strip | 3 : 1 |
| U2 Selection outline (A1) | sel | lane, selected lane, panel, strip | 3 : 1 |
| U3 Record button | rec | chrome, panel | 3 : 1 |
| U4 Playhead | ph | ruler, lanes | 3 : 1 |
| U5 Meter segments | m0 to m3 | display | 3 : 1 |
| U6 Limit colours in displays | warn, ok, overD | display | 3 : 1 |
| U7 Focus ring | the better of focusIn and focusOut | every surface | 3 : 1 |
| U8 Track colours (clip edges) | the 8 track colours | both lanes | 3 : 1 |
| U9 Curves and handles in displays | accentD, selD | display | 3 : 1 |
| D Meaning colours apart | accent/sel, sel/over, sel/rec, accent/rec, accent/ok, ph/sel, ph/rec | | CIEDE2000 15 (10 for accent/ok and ph/sel) |
| C Track colours, colour vision | smallest CIEDE2000 under normal, protan, deutan, tritan | | 6 minimum, 10 target |

Also: clip titles pick their ink per clip (theme ink, near black or white, whichever reads best); in dark themes main text is never pure white (halation), so the fit raises glass opacity before it lightens text.

**How the themes were fitted.** Each theme was drawn by hand from its icon (colours read from `desktop/icon-assets/picker/*.png` and the P2, P8, P8N tables). `check.py` then raised the glass to the floor needed by the hand-picked text, moved only the lightness (OKLCH L) of any text, status or display colour that failed, flipped the accent's text colour when needed, and tuned the eight track colours within small limits (lightness 0.10, chroma 0.05, hue 18°) for the smallest CIEDE2000 under all four visions while every clip edge keeps 3 : 1 on both lanes. Theme A is locked. Every change is listed per theme below and on the page.

## 5. The token design

- **Tiers.** Primitives: each theme's raw colours. Semantic tokens: the names in section 4 (37 colours plus glass opacity, clip opacity, grid colour and strength, and 8 track colours). Component tokens only as aliases where a lane needs them.
- **Meanings never change.** Record and over stay red, selection stays the selection (yellow in dark themes, darker gold in light ones, cyan only in H where the accent is gold), units stay amber, ok stays green.
- **Theme file.** One JSON file per theme in the W3C Design Tokens format, for example `themes/blueprint.tokens.json` with `{"color":{"ink":{"$type":"color","$value":"#F4F8FF"}, ...}}`, plus `$extensions` for AudioLab's own fields (`glassA`, `clipA`, `grid`, `icons`, `mode`, `pair` for the light or dark partner). The release bundles them into `index.html` as one object, so there is no file loading at start-up.
- **Live switch.** `tmApply(theme)`: write CSS variables on `:root` once, rebuild `LOOK` from the tokens (`lkMake` reads them), rebuild `TH`, clear the caches that hold colours (`THMX`, `CLC`, lane O's tile cache), one redraw. No reload, nothing per frame. The canvas drawers keep reading `LOOK` and `TH` as today.
- **Adjust.** Today's Hue, Tint and Background sliders stay as "Adjust" on top of any theme; values that would break a rule are clamped (the check runs in the page in under a millisecond per pair).
- **System appearance.** Optional: a light and a dark theme as a pair (B and B2), switched with `nativeTheme` / `prefers-color-scheme`.
- **Glass.** Each theme has a glass tint and a floor; the glass engine never draws the tint thinner than the floor. Proposed refinement for the glass engine: a "text plate", a local thicker tint only under text runs, so panels keep 50 % glass elsewhere.
- **Displays.** `display`, `inkD`, `unitD`, `accentD`, `selD`, `overD` and the meter stops are the only colours a display's contents may use besides its own drawing colours, all measured against the dark well.
- **Icon follows theme.** A setting (on, off, ask); on: choosing a theme sets the app icon to the theme's first icon through the icon picker's own hook; picking an icon by hand turns the link off.
- **Other programs.** The 8 studio looks of `THEMES` become theme files too, keeping their fader and clip shapes as extras; they get the same check and keep their known misses as a baseline.
- **Gate.** `python3 tools/design-lab/th1/check.py --gate` (or its JavaScript port in `desktop/scripts/`) fails the release when a theme breaks a rule that passed before.

## 6. The themes

Recommendations: ★★★★★ A, B, E. ★★★★ B2, C, D, G, H, J, K, N. ★★★ F, I, L, M.

Combinations (icon with theme): E Blueprint with the cutaway nucleus icon (the user's example); D Chalkboard with the science fair icon; C with three-rings or space-race; B and B2 with any P8 icon (J3, J8, J10); A and N share the P2 icons; J Patent drawing and B Chart paper as an all-paper pair; G's cutaway icon also suits H.

Contrast notes: "Lc" is APCA (negative = light text on dark); "glass over clips" is the worst of five backdrops.

Today's theme A also drives the glass floor rule: at today's 50 % glass, the quiet grey `#8b8b97` reaches Lc −31.8 and 3.2 : 1 over the brightest clip.

### TH-A Orbit night (dark) ★★★★★

Today's AudioLab, unchanged: blue-tinted charcoal, see-through clips, yellow selection, amber units. The default. From: J3 P2 (Dipole Field), M5 P2 (Field Depth): today's app. Icons that follow it: `dipole-field`, `field-depth`.

Tokens: bg `#101214`, chrome `#17191C`, ruler `#272B30`, lane0 `#1E2125`, lane1 `#202328`, laneSel `#292D33`, panel `#121216`, panel2 `#18181d`, strip `#24272E`, display `#0B0C10`, glass `#1C1C24`, line `#25252c`, ink `#ececf1`, lab `#b7b7c2`, mut `#8b8b97`, dis `#5c5e68`, rulerTxt `#AAB1BB`, inkD `#ececf1`, accent `#4c8dff`, onAccent `#ffffff`, accentD `#4c8dff`, sel `#f5c84c`, selD `#f5c84c`, unit `#ffb547`, unitD `#ffb547`, rec `#ff4d4d`, over `#ff6b6b`, overD `#ff6b6b`, warn `#f5c84c`, ok `#3ecf8e`, ph `#3ecf8e`, m0 `#12804f`, m1 `#3ecf8e`, m2 `#f5c84c`, m3 `#ff3b3b`, focusIn `#4c8dff`, focusOut `#4c8dff`, glass opacity 50 %, clip opacity 36 %, grid `255,255,255` × 1.

Track colours: `#4c8dff` `#3ecf8e` `#f5c84c` `#ff6b6b` `#ff9a3c` `#b583ff` `#4cc9f0` `#ff7ac8`. Smallest CIEDE2000: normal 18.6, protan 1.0, deutan 5.7, tritan 6.1. Glass floor 78 %.

| Rule | Worst pair (fg on surface) | WCAG | APCA Lc | Pairs | Result |
|---|---|---|---|---|---|
| T1 Main text | `#ececf1` on glass over clips `#443C2C` | 9.25 | -86.9 | 14 | pass |
| T2 Labels | `#b7b7c2` on glass over clips `#443C2C` | 5.48 | -55.1 | 10 | 2 miss (today, kept) |
| T3 Quiet text (11 px, weight 500) | `#8b8b97` on glass over clips `#443C2C` | 3.23 | -31.8 | 11 | 11 miss (today, kept) |
| T4 Disabled text | `#5c5e68` on strip `#24272E` | 2.32 | -16.6 | 2 | 2 miss (today, kept) |
| T5 Ruler numbers | `#AAB1BB` on ruler `#272B30` | 6.59 | -55.8 | 1 | 1 miss (today, kept) |
| T6 Units (amber, L2) on panels | `#ffb547` on strip `#24272E` | 8.51 | -67.5 | 3 | pass |
| T6d Units in displays | `#ffb547` on display `#0B0C10` | 11.13 | -70.6 | 1 | pass |
| T7 Text on accent buttons | `#ffffff` on accent `#4c8dff` | 3.20 | -64.2 | 1 | 1 miss (today, kept) |
| T8 Over read-out in displays | `#ff6b6b` on display `#0B0C10` | 7.04 | -48.9 | 1 | pass |
| T10 Text in displays | `#ececf1` on display `#0B0C10` | 16.60 | -95.5 | 1 | pass |
| T9 Over / error text on panels | `#ff6b6b` on strip `#24272E` | 5.39 | -45.8 | 2 | pass |
| U1 Accent (buttons on, links, toggles) | `#4c8dff` on strip `#24272E` | 4.67 | -39.6 | 4 | pass |
| U2 Selection outline (A1) | `#f5c84c` on laneSel `#292D33` | 8.73 | -72.2 | 4 | pass |
| U3 Record button | `#ff4d4d` on chrome `#17191C` | 5.39 | -41.8 | 2 | pass |
| U4 Playhead | `#3ecf8e` on ruler `#272B30` | 7.14 | -60.2 | 3 | pass |
| U5 Meter segments in their well | `#12804f` on display `#0B0C10` | 3.93 | -27.6 | 4 | pass |
| U6 Limit colours in displays | `#ff6b6b` on display `#0B0C10` | 7.04 | -48.9 | 3 | pass |
| U9 Curves and handles in displays | `#4c8dff` on display `#0B0C10` | 6.11 | -42.7 | 2 | pass |
| U7 Focus ring (two colours, best band) | `#4c8dff` on laneSel `#292D33` | 4.32 | – | 9 | pass |
| U8 Track colours against the lanes (clip edges) | `#4c8dff` on lane1 `#202328` | 4.92 | -40.4 | 16 | pass |

Meaning colours apart (CIEDE2000): accent/sel 61.2, sel/over 42.4, sel/rec 44.4, accent/rec 45.6, accent/ok 48.4, ph/sel 35.2, ph/rec 73.2.

### TH-B Chart paper (light) ★★★★★

A printed plate: warm chart paper, navy ink, the nucleus orange and the electron blue. Displays and meters sit in navy ink wells. From: J3 P8, J8 P8, J10 P8 (palette P8: paper #F7F3EA to #E4DCCA, ink #1B2340, nucleus #C8610A, electron #2F6BFF). Icons that follow it: `dipole-field-paper`, `measured-field-paper`, `field-dial-paper`.

Tokens: bg `#E4DCCA`, chrome `#EAE3D3`, ruler `#EFE9DC`, lane0 `#F7F3EA`, lane1 `#F2EDE2`, laneSel `#FBEFC9`, panel `#FAF7F0`, panel2 `#F1EBDF`, strip `#EDE6D7`, display `#1B2340`, glass `#FAF6EE`, line `#CFC5B0`, ink `#1B2340`, lab `#3E4560`, mut `#5B6074`, dis `#9A9888`, rulerTxt `#1B2340`, inkD `#F7F3EA`, accent `#2E6AFE`, onAccent `#FFFFFF`, accentD `#2E6AFE`, sel `#AA7B01`, selD `#C89200`, unit `#A34E00`, unitD `#FFB547`, rec `#D02F2F`, over `#C42C29`, overD `#FF6B6B`, warn `#F2C84B`, ok `#5AD39A`, ph `#C8610A`, m0 `#2E9E6B`, m1 `#5AD39A`, m2 `#F2C84B`, m3 `#FF5A4F`, focusIn `#2F6BFF`, focusOut `#FFFFFF`, glass opacity 90 %, clip opacity 85 %, grid `27,35,64` × 1.2.

Track colours: `#7D76FB` `#147B5C` `#8F5A08` `#CB5D78` `#6957B5` `#1796AA` `#93006F` `#988941`. Smallest CIEDE2000: normal 14.7, protan 13.8, deutan 13.0, tritan 12.9. Glass floor 85 %.

| Rule | Worst pair (fg on surface) | WCAG | APCA Lc | Pairs | Result |
|---|---|---|---|---|---|
| T1 Main text | `#1B2340` on bg `#E4DCCA` | 11.31 | 82.1 | 14 | pass |
| T2 Labels | `#3E4560` on chrome `#EAE3D3` | 7.38 | 75.6 | 10 | pass |
| T3 Quiet text (11 px, weight 500) | `#5B6074` on bg `#E4DCCA` | 4.57 | 60.9 | 11 | pass |
| T4 Disabled text | `#9A9888` on strip `#EDE6D7` | 2.34 | 41.0 | 2 | pass |
| T5 Ruler numbers | `#1B2340` on ruler `#EFE9DC` | 12.75 | 89.5 | 1 | pass |
| T6 Units (amber, L2) on panels | `#A34E00` on chrome `#EAE3D3` | 4.50 | 61.9 | 3 | pass |
| T6d Units in displays | `#FFB547` on display `#1B2340` | 8.78 | -67.9 | 1 | pass |
| T7 Text on accent buttons | `#FFFFFF` on accent `#2E6AFE` | 4.56 | -76.4 | 1 | pass |
| T8 Over read-out in displays | `#FF6B6B` on display `#1B2340` | 5.56 | -46.2 | 1 | pass |
| T10 Text in displays | `#F7F3EA` on display `#1B2340` | 13.93 | -97.2 | 1 | pass |
| T9 Over / error text on panels | `#C42C29` on strip `#EDE6D7` | 4.52 | 62.0 | 2 | pass |
| U1 Accent (buttons on, links, toggles) | `#2E6AFE` on bg `#E4DCCA` | 3.34 | 50.7 | 4 | pass |
| U2 Selection outline (A1) | `#AA7B01` on strip `#EDE6D7` | 3.05 | 50.7 | 4 | pass |
| U3 Record button | `#D02F2F` on chrome `#EAE3D3` | 3.98 | 57.3 | 2 | pass |
| U4 Playhead | `#C8610A` on ruler `#EFE9DC` | 3.36 | 54.4 | 3 | pass |
| U5 Meter segments in their well | `#2E9E6B` on display `#1B2340` | 4.57 | -37.9 | 4 | pass |
| U6 Limit colours in displays | `#FF6B6B` on display `#1B2340` | 5.56 | -46.2 | 3 | pass |
| U9 Curves and handles in displays | `#2E6AFE` on display `#1B2340` | 3.39 | -27.9 | 2 | pass |
| U7 Focus ring (two colours, best band) | `#2F6BFF` on bg `#E4DCCA` | 3.30 | – | 9 | pass |
| U8 Track colours against the lanes (clip edges) | `#988941` on lane1 `#F2EDE2` | 3.00 | 52.1 | 16 | pass |

Meaning colours apart (CIEDE2000): accent/sel 60.6, sel/over 34.4, sel/rec 34.6, accent/rec 44.7, accent/ok 53.4, ph/sel 16.7, ph/rec 19.2.

Readability fit: track colours: smallest CIEDE2000 over four visions 1.6 -> 12.9; mut #5F6478 → #5B6074; unit #A8520A → #A34E00; over #C8302C → #C42C29; sel #C89200 → #AA7B01; accent / onAccent #2F6BFF / #FFFFFF → #2E6AFE / #FFFFFF.

### TH-B2 Chart paper, night (dark) ★★★★

Chart paper turned over: navy night with paper-coloured ink. B's dark half, for when the system goes dark. From: P8N (Chart paper, night: #1E2742 to #0C1020, paper ink #F3EEE2, orange #F08A2C, blue #6E9BFF, field #D9CDB4). Icons that follow it: `dipole-field-paper`, `measured-field-paper`, `field-dial-paper`.

Tokens: bg `#0C1020`, chrome `#121729`, ruler `#1B2238`, lane0 `#141A2C`, lane1 `#171E33`, laneSel `#222A42`, panel `#151B2D`, panel2 `#1B2236`, strip `#1C2338`, display `#080B15`, glass `#1A2034`, line `#2C3550`, ink `#F3EEE2`, lab `#D9CDB4`, mut `#A69E8C`, dis `#817C6D`, rulerTxt `#D9CDB4`, inkD `#F3EEE2`, accent `#8AAFFE`, onAccent `#0C1020`, accentD `#8AAFFE`, sel `#F5C84C`, selD `#F5C84C`, unit `#FA9438`, unitD `#F58F32`, rec `#FF5555`, over `#FF6B6B`, overD `#FF6B6B`, warn `#F5C84C`, ok `#4FD39A`, ph `#F08A2C`, m0 `#1F8A5A`, m1 `#4FD39A`, m2 `#F5C84C`, m3 `#FF4D4D`, focusIn `#6E9BFF`, focusOut `#0C1020`, glass opacity 85 %, clip opacity 40 %, grid `217,205,180` × 1.

Track colours: `#776FE9` `#28E7BC` `#F1FB57` `#E02C00` `#E7A26A` `#BAB3FE` `#74AAAC` `#C0667E`. Smallest CIEDE2000: normal 20.5, protan 15.7, deutan 15.5, tritan 15.5. Glass floor 81 %.

| Rule | Worst pair (fg on surface) | WCAG | APCA Lc | Pairs | Result |
|---|---|---|---|---|---|
| T1 Main text | `#F3EEE2` on glass over clips `#262D35` | 12.02 | -92.6 | 14 | pass |
| T2 Labels | `#D9CDB4` on glass over clips `#262D35` | 8.84 | -72.6 | 10 | pass |
| T3 Quiet text (11 px, weight 500) | `#A69E8C` on glass over clips `#262D35` | 5.23 | -45.8 | 11 | pass |
| T4 Disabled text | `#817C6D` on strip `#1C2338` | 3.74 | -30.2 | 2 | pass |
| T5 Ruler numbers | `#D9CDB4` on ruler `#1B2238` | 10.01 | -74.3 | 1 | pass |
| T6 Units (amber, L2) on panels | `#FA9438` on strip `#1C2338` | 6.95 | -55.6 | 3 | pass |
| T6d Units in displays | `#F58F32` on display `#080B15` | 8.29 | -55.5 | 1 | pass |
| T7 Text on accent buttons | `#0C1020` on accent `#8AAFFE` | 8.68 | 60.5 | 1 | pass |
| T8 Over read-out in displays | `#FF6B6B` on display `#080B15` | 7.08 | -48.9 | 1 | pass |
| T10 Text in displays | `#F3EEE2` on display `#080B15` | 16.97 | -96.7 | 1 | pass |
| T9 Over / error text on panels | `#FF6B6B` on strip `#1C2338` | 5.62 | -46.4 | 2 | pass |
| U1 Accent (buttons on, links, toggles) | `#8AAFFE` on strip `#1C2338` | 7.16 | -56.7 | 4 | pass |
| U2 Selection outline (A1) | `#F5C84C` on laneSel `#222A42` | 8.96 | -72.6 | 4 | pass |
| U3 Record button | `#FF5555` on panel `#151B2D` | 5.45 | -42.8 | 2 | pass |
| U4 Playhead | `#F08A2C` on ruler `#1B2238` | 6.29 | -50.6 | 3 | pass |
| U5 Meter segments in their well | `#1F8A5A` on display `#080B15` | 4.53 | -31.8 | 4 | pass |
| U6 Limit colours in displays | `#FF6B6B` on display `#080B15` | 7.08 | -48.9 | 3 | pass |
| U9 Curves and handles in displays | `#8AAFFE` on display `#080B15` | 9.02 | -59.3 | 2 | pass |
| U7 Focus ring (two colours, best band) | `#6E9BFF` on laneSel `#222A42` | 5.27 | – | 9 | pass |
| U8 Track colours against the lanes (clip edges) | `#E02C00` on lane1 `#171E33` | 3.57 | -29.4 | 16 | pass |

Meaning colours apart (CIEDE2000): accent/sel 53.3, sel/over 42.4, sel/rec 44.0, accent/rec 43.9, accent/ok 41.2, ph/sel 21.3, ph/rec 24.5.

Readability fit: track colours: smallest CIEDE2000 over four visions 0.8 -> 15.5; glassA 0.55 → 0.85; mut #A49C8A → #A69E8C; dis #6B6658 → #817C6D; unit #F08A2C → #FA9438; unitD #F08A2C → #F58F32; accent / onAccent #6E9BFF / #0C1020 → #8AAFFE / #0C1020.

### TH-C Space Race (dark) ★★★★

Old school mission control: deep navy, a Space Race blue band for the top bar and transport, steel text, red only for record. From: RC2 Three Rings (graphite #0F141E, steel #8FA1BB, red #C73637, blue #5579C0) and FC4 Space Race (blue #0B3D91, white, red #D53D33). Icons that follow it: `three-rings`, `space-race`.

Tokens: bg `#070E1E`, chrome `#0A3478`, ruler `#0E1A33`, lane0 `#0D1730`, lane1 `#0F1A35`, laneSel `#18264A`, panel `#0C1630`, panel2 `#122045`, strip `#111D3A`, display `#040914`, glass `#0E1A38`, line `#22335A`, ink `#F2F4F8`, lab `#C4CEE0`, mut `#95A4C2`, dis `#6F7B95`, rulerTxt `#C4CEE0`, inkD `#F2F4F8`, accent `#82AFFD`, onAccent `#070E1E`, accentD `#82AFFD`, sel `#FFD23A`, selD `#FFD23A`, unit `#FFB547`, unitD `#FFB547`, rec `#E7493E`, over `#FF6B5E`, overD `#FF6B5E`, warn `#FFD23A`, ok `#3ECF8E`, ph `#F2F4F8`, m0 `#12804f`, m1 `#3ecf8e`, m2 `#FFD23A`, m3 `#ff3b3b`, focusIn `#FFFFFF`, focusOut `#0B3D91`, glass opacity 83 %, clip opacity 80 %, grid `160,180,215` × 1.

Track colours: `#61A4FF` `#5E8E6B` `#FEE384` `#CF0315` `#F66F1A` `#904FD6` `#3AEDFD` `#DA95B3`. Smallest CIEDE2000: normal 23.2, protan 15.9, deutan 15.8, tritan 15.6. Glass floor 81 %.

| Rule | Worst pair (fg on surface) | WCAG | APCA Lc | Pairs | Result |
|---|---|---|---|---|---|
| T1 Main text | `#F2F4F8` on chrome `#0A3478` | 10.74 | -92.9 | 14 | pass |
| T2 Labels | `#C4CEE0` on chrome `#0A3478` | 7.46 | -68.8 | 10 | pass |
| T3 Quiet text (11 px, weight 500) | `#95A4C2` on chrome `#0A3478` | 4.71 | -45.1 | 11 | pass |
| T4 Disabled text | `#6F7B95` on strip `#111D3A` | 3.92 | -30.4 | 2 | pass |
| T5 Ruler numbers | `#C4CEE0` on ruler `#0E1A33` | 10.91 | -75.0 | 1 | pass |
| T6 Units (amber, L2) on panels | `#FFB547` on chrome `#0A3478` | 6.73 | -63.2 | 3 | pass |
| T6d Units in displays | `#FFB547` on display `#040914` | 11.34 | -70.7 | 1 | pass |
| T7 Text on accent buttons | `#070E1E` on accent `#82AFFD` | 8.71 | 60.0 | 1 | pass |
| T8 Over read-out in displays | `#FF6B5E` on display `#040914` | 7.13 | -48.7 | 1 | pass |
| T10 Text in displays | `#F2F4F8` on display `#040914` | 18.09 | -100.4 | 1 | pass |
| T9 Over / error text on panels | `#FF6B5E` on strip `#111D3A` | 5.96 | -46.9 | 2 | pass |
| U1 Accent (buttons on, links, toggles) | `#82AFFD` on chrome `#0A3478` | 5.35 | -51.1 | 4 | pass |
| U2 Selection outline (A1) | `#FFD23A` on laneSel `#18264A` | 10.27 | -78.8 | 4 | pass |
| U3 Record button | `#E7493E` on chrome `#0A3478` | 3.05 | -29.0 | 2 | pass |
| U4 Playhead | `#F2F4F8` on lane1 `#0F1A35` | 15.64 | -99.0 | 3 | pass |
| U5 Meter segments in their well | `#12804f` on display `#040914` | 4.01 | -27.7 | 4 | pass |
| U6 Limit colours in displays | `#FF6B5E` on display `#040914` | 7.13 | -48.7 | 3 | pass |
| U9 Curves and handles in displays | `#82AFFD` on display `#040914` | 9.01 | -58.6 | 2 | pass |
| U7 Focus ring (two colours, best band) | `#FFFFFF` on chrome `#0A3478` | 11.83 | – | 9 | pass |
| U8 Track colours against the lanes (clip edges) | `#CF0315` on lane1 `#0F1A35` | 3.02 | -24.4 | 16 | pass |

Meaning colours apart (CIEDE2000): accent/sel 55.3, sel/over 43.3, sel/rec 47.3, accent/rec 46.7, accent/ok 42.6, ph/sel 31.0, ph/rec 42.3.

Readability fit: track colours: smallest CIEDE2000 over four visions 1.4 -> 15.6; glassA 0.6 → 0.83; mut #93A2C0 → #95A4C2; dis #56617A → #6F7B95; rec #E5473C → #E7493E; accent / onAccent #3D7BEA / #FFFFFF → #82AFFD / #070E1E.

### TH-D Chalkboard (dark) ★★★★

A science fair under a chalkboard: slate green, chalk-white text, chalk pastels for the tracks. From: VB3 Chalkboard (slate #344434, chalk) and VA10 Science Fair (green #2E4A3A, cream #D1C6A0, red #AD3528, gold #C6A85A). Icons that follow it: `chalkboard`, `science-fair`.

Tokens: bg `#18221A`, chrome `#1D2A20`, ruler `#223026`, lane0 `#25332A`, lane1 `#283729`, laneSel `#33463A`, panel `#1F2B22`, panel2 `#273529`, strip `#26342A`, display `#0E140F`, glass `#223026`, line `#3A4B3E`, ink `#ECE8DA`, lab `#CFCAB6`, mut `#A5AA96`, dis `#7B8676`, rulerTxt `#D1C6A0`, inkD `#ECE8DA`, accent `#8EC5E8`, onAccent `#14201A`, accentD `#8EC5E8`, sel `#F2D26B`, selD `#F2D26B`, unit `#F0B062`, unitD `#F0B062`, rec `#E25A4A`, over `#FF7A66`, overD `#FF7A66`, warn `#F2D26B`, ok `#8FDC8A`, ph `#F2EDE0`, m0 `#3E9E63`, m1 `#8FDC8A`, m2 `#F2D26B`, m3 `#FF6A55`, focusIn `#F2EDE0`, focusOut `#0E140F`, glass opacity 85 %, clip opacity 50 %, grid `232,228,212` × 1.1.

Track colours: `#C5E1FF` `#BCCC95` `#FBD639` `#B88D84` `#F07C3D` `#A795DB` `#77BDB8` `#FFFEFA`. Smallest CIEDE2000: normal 16.6, protan 13.8, deutan 13.8, tritan 13.9. Glass floor 85 %.

| Rule | Worst pair (fg on surface) | WCAG | APCA Lc | Pairs | Result |
|---|---|---|---|---|---|
| T1 Main text | `#ECE8DA` on laneSel `#33463A` | 8.24 | -82.5 | 14 | pass |
| T2 Labels | `#CFCAB6` on glass over clips `#334036` | 6.63 | -65.5 | 10 | pass |
| T3 Quiet text (11 px, weight 500) | `#A5AA96` on glass over clips `#334036` | 4.56 | -46.2 | 11 | pass |
| T4 Disabled text | `#7B8676` on strip `#26342A` | 3.43 | -30.7 | 2 | pass |
| T5 Ruler numbers | `#D1C6A0` on ruler `#223026` | 8.10 | -67.7 | 1 | pass |
| T6 Units (amber, L2) on panels | `#F0B062` on strip `#26342A` | 6.90 | -61.4 | 3 | pass |
| T6d Units in displays | `#F0B062` on display `#0E140F` | 9.85 | -66.0 | 1 | pass |
| T7 Text on accent buttons | `#14201A` on accent `#8EC5E8` | 9.03 | 66.6 | 1 | pass |
| T8 Over read-out in displays | `#FF7A66` on display `#0E140F` | 7.31 | -51.9 | 1 | pass |
| T10 Text in displays | `#ECE8DA` on display `#0E140F` | 15.21 | -92.2 | 1 | pass |
| T9 Over / error text on panels | `#FF7A66` on strip `#26342A` | 5.12 | -47.2 | 2 | pass |
| U1 Accent (buttons on, links, toggles) | `#8EC5E8` on strip `#26342A` | 7.03 | -62.3 | 4 | pass |
| U2 Selection outline (A1) | `#F2D26B` on laneSel `#33463A` | 6.84 | -70.4 | 4 | pass |
| U3 Record button | `#E25A4A` on panel `#1F2B22` | 4.06 | -35.2 | 2 | pass |
| U4 Playhead | `#F2EDE0` on lane1 `#283729` | 10.77 | -90.3 | 3 | pass |
| U5 Meter segments in their well | `#3E9E63` on display `#0E140F` | 5.58 | -40.5 | 4 | pass |
| U6 Limit colours in displays | `#FF7A66` on display `#0E140F` | 7.31 | -51.9 | 3 | pass |
| U9 Curves and handles in displays | `#8EC5E8` on display `#0E140F` | 10.04 | -66.9 | 2 | pass |
| U7 Focus ring (two colours, best band) | `#F2EDE0` on laneSel `#33463A` | 8.65 | – | 9 | pass |
| U8 Track colours against the lanes (clip edges) | `#B88D84` on lane1 `#283729` | 4.30 | -40.2 | 16 | pass |

Meaning colours apart (CIEDE2000): accent/sel 45.0, sel/over 37.6, sel/rec 42.4, accent/rec 49.3, accent/ok 38.6, ph/sel 20.7, ph/rec 38.8.

Readability fit: track colours: smallest CIEDE2000 over four visions 0.4 -> 13.8; glassA 0.6 → 0.85; mut #A3A894 → #A5AA96; dis #6A7465 → #7B8676.

### TH-E Blueprint (dark) ★★★★★

A drafting blueprint: Prussian blue paper, white lines, the G3 drafting grid made visible, tracing-paper clips. From: VB1 Blueprint (blue #13417A, grid #6888AD, white lines); pairs with VB6 Cutaway Nucleus as its icon. Icons that follow it: `blueprint`, `cutaway-nucleus`.

Tokens: bg `#0A2347`, chrome `#0D2A54`, ruler `#0F2E5A`, lane0 `#123463`, lane1 `#14376A`, laneSel `#1C4580`, panel `#0F2C57`, panel2 `#143466`, strip `#133263`, display `#061733`, glass `#10305E`, line `#2D5590`, ink `#F4F8FF`, lab `#CADBF2`, mut `#9CB6DA`, dis `#6885B1`, rulerTxt `#CADBF2`, inkD `#F4F8FF`, accent `#DDEBFF`, onAccent `#0A2347`, accentD `#DDEBFF`, sel `#FFD54A`, selD `#FFD54A`, unit `#FFC266`, unitD `#FFC266`, rec `#FF5A50`, over `#FF7A70`, overD `#FF7A70`, warn `#FFD54A`, ok `#5EE0A0`, ph `#FFFFFF`, m0 `#2FB37A`, m1 `#5EE0A0`, m2 `#FFD54A`, m3 `#FF5A50`, focusIn `#FFFFFF`, focusOut `#061733`, glass opacity 68 %, clip opacity 35 %, grid `200,220,255` × 1.4.

Track colours: `#BACBFE` `#5BC393` `#FBFFD1` `#F3703E` `#FED170` `#A592FF` `#9EFEF4` `#D28FB6`. Smallest CIEDE2000: normal 15.1, protan 14.0, deutan 13.8, tritan 14.0. Glass floor 68 %.

| Rule | Worst pair (fg on surface) | WCAG | APCA Lc | Pairs | Result |
|---|---|---|---|---|---|
| T1 Main text | `#F4F8FF` on glass over clips `#2B486C` | 8.78 | -90.9 | 14 | pass |
| T2 Labels | `#CADBF2` on glass over clips `#2B486C` | 6.65 | -71.7 | 10 | pass |
| T3 Quiet text (11 px, weight 500) | `#9CB6DA` on glass over clips `#2B486C` | 4.50 | -49.7 | 11 | pass |
| T4 Disabled text | `#6885B1` on strip `#133263` | 3.35 | -30.3 | 2 | pass |
| T5 Ruler numbers | `#CADBF2` on ruler `#0F2E5A` | 9.58 | -78.7 | 1 | pass |
| T6 Units (amber, L2) on panels | `#FFC266` on strip `#133263` | 7.91 | -70.0 | 3 | pass |
| T6d Units in displays | `#FFC266` on display `#061733` | 11.17 | -75.0 | 1 | pass |
| T7 Text on accent buttons | `#0A2347` on accent `#DDEBFF` | 12.94 | 89.7 | 1 | pass |
| T8 Over read-out in displays | `#FF7A70` on display `#061733` | 7.02 | -51.6 | 1 | pass |
| T10 Text in displays | `#F4F8FF` on display `#061733` | 16.74 | -101.8 | 1 | pass |
| T9 Over / error text on panels | `#FF7A70` on strip `#133263` | 4.97 | -46.6 | 2 | pass |
| U1 Accent (buttons on, links, toggles) | `#DDEBFF` on strip `#133263` | 10.46 | -87.8 | 4 | pass |
| U2 Selection outline (A1) | `#FFD54A` on laneSel `#1C4580` | 6.72 | -71.7 | 4 | pass |
| U3 Record button | `#FF5A50` on panel `#0F2C57` | 4.50 | -40.6 | 2 | pass |
| U4 Playhead | `#FFFFFF` on lane1 `#14376A` | 11.77 | -100.3 | 3 | pass |
| U5 Meter segments in their well | `#FF5A50` on display `#061733` | 5.80 | -44.0 | 4 | pass |
| U6 Limit colours in displays | `#FF7A70` on display `#061733` | 7.02 | -51.6 | 3 | pass |
| U9 Curves and handles in displays | `#FFD54A` on display `#061733` | 12.62 | -82.5 | 2 | pass |
| U7 Focus ring (two colours, best band) | `#FFFFFF` on laneSel `#1C4580` | 9.49 | – | 9 | pass |
| U8 Track colours against the lanes (clip edges) | `#F3703E` on lane1 `#14376A` | 4.03 | -39.4 | 16 | pass |

Meaning colours apart (CIEDE2000): accent/sel 40.9, sel/over 41.9, sel/rec 45.3, accent/rec 42.2, accent/ok 31.5, ph/sel 28.5, ph/rec 38.7.

Readability fit: track colours: smallest CIEDE2000 over four visions 0.5 -> 13.8; glassA 0.6 → 0.68; dis #5E7BA6 → #6885B1.

### TH-F Dalton sphere (dark) ★★★

An engraving: the dark umber of Dalton's sphere as the ground, cream ink, warm muted tracks. From: VC4 Dalton Sphere (cream #E9DDBF, umber sphere #2C2419, engraved hatching). Icons that follow it: `dalton-sphere`.

Tokens: bg `#14100B`, chrome `#1A150F`, ruler `#211B13`, lane0 `#221C14`, lane1 `#251F16`, laneSel `#3A3020`, panel `#1C1711`, panel2 `#241E15`, strip `#231D15`, display `#0C0906`, glass `#241D14`, line `#3D3426`, ink `#EDE2C4`, lab `#D2C5A3`, mut `#A89C7F`, dis `#827966`, rulerTxt `#D2C5A3`, inkD `#EDE2C4`, accent `#E9DDBF`, onAccent `#1C1711`, accentD `#E9DDBF`, sel `#F5C84C`, selD `#F5C84C`, unit `#E8A55A`, unitD `#E8A55A`, rec `#E5533F`, over `#FF7360`, overD `#FF7360`, warn `#F5C84C`, ok `#8FCB8A`, ph `#E9DDBF`, m0 `#4E9A5E`, m1 `#8FCB8A`, m2 `#F2C84B`, m3 `#FF5E4A`, focusIn `#E9DDBF`, focusOut `#0C0906`, glass opacity 85 %, clip opacity 45 %, grid `233,221,191` × 1.

Track colours: `#E29A19` `#82956B` `#FED69A` `#CA490D` `#769ADB` `#9F8396` `#67EBFA` `#BAB5AE`. Smallest CIEDE2000: normal 17.2, protan 15.5, deutan 15.5, tritan 16.0. Glass floor 84 %.

| Rule | Worst pair (fg on surface) | WCAG | APCA Lc | Pairs | Result |
|---|---|---|---|---|---|
| T1 Main text | `#EDE2C4` on laneSel `#3A3020` | 10.03 | -83.9 | 14 | pass |
| T2 Labels | `#D2C5A3` on glass over clips `#33291D` | 8.31 | -68.0 | 10 | pass |
| T3 Quiet text (11 px, weight 500) | `#A89C7F` on glass over clips `#33291D` | 5.24 | -45.2 | 11 | pass |
| T4 Disabled text | `#827966` on strip `#231D15` | 3.88 | -30.0 | 2 | pass |
| T5 Ruler numbers | `#D2C5A3` on ruler `#211B13` | 9.96 | -70.4 | 1 | pass |
| T6 Units (amber, L2) on panels | `#E8A55A` on strip `#231D15` | 7.92 | -59.3 | 3 | pass |
| T6d Units in displays | `#E8A55A` on display `#0C0906` | 9.42 | -61.0 | 1 | pass |
| T7 Text on accent buttons | `#1C1711` on accent `#E9DDBF` | 13.19 | 85.0 | 1 | pass |
| T8 Over read-out in displays | `#FF7360` on display `#0C0906` | 7.45 | -50.6 | 1 | pass |
| T10 Text in displays | `#EDE2C4` on display `#0C0906` | 15.39 | -89.3 | 1 | pass |
| T9 Over / error text on panels | `#FF7360` on strip `#231D15` | 6.26 | -48.9 | 2 | pass |
| U1 Accent (buttons on, links, toggles) | `#E9DDBF` on strip `#231D15` | 12.37 | -84.6 | 4 | pass |
| U2 Selection outline (A1) | `#F5C84C` on laneSel `#3A3020` | 8.16 | -71.1 | 4 | pass |
| U3 Record button | `#E5533F` on panel `#1C1711` | 4.78 | -36.8 | 2 | pass |
| U4 Playhead | `#E9DDBF` on lane1 `#251F16` | 12.10 | -84.3 | 3 | pass |
| U5 Meter segments in their well | `#4E9A5E` on display `#0C0906` | 5.78 | -39.9 | 4 | pass |
| U6 Limit colours in displays | `#FF7360` on display `#0C0906` | 7.45 | -50.6 | 3 | pass |
| U9 Curves and handles in displays | `#F5C84C` on display `#0C0906` | 12.53 | -76.5 | 2 | pass |
| U7 Focus ring (two colours, best band) | `#E9DDBF` on laneSel `#3A3020` | 9.58 | – | 9 | pass |
| U8 Track colours against the lanes (clip edges) | `#CA490D` on lane1 `#251F16` | 3.48 | -28.0 | 16 | pass |

Meaning colours apart (CIEDE2000): accent/sel 17.9, sel/over 37.7, sel/rec 41.3, accent/rec 38.4, accent/ok 20.7, ph/sel 17.9, ph/rec 38.4.

Readability fit: track colours: smallest CIEDE2000 over four visions 2.5 -> 15.5; glassA 0.6 → 0.85; mut #A69A7E → #A89C7F; dis #6E6552 → #827966.

### TH-G Cutaway nucleus (dark) ★★★★

Machined steel: cool slate, silver accent, the nucleus red and blue only where they mean something. From: VB6 Cutaway Nucleus (slate #1A2230, silver #A4B2C8, nucleus red #972C20 and blue #2D62A8). Icons that follow it: `cutaway-nucleus`.

Tokens: bg `#0F141C`, chrome `#151B26`, ruler `#1A2130`, lane0 `#1A2230`, lane1 `#1D2534`, laneSel `#2A3446`, panel `#161C27`, panel2 `#1E2533`, strip `#1F2634`, display `#080B10`, glass `#1D2433`, line `#2F394C`, ink `#EEF2F8`, lab `#C4CEDD`, mut `#95A1B6`, dis `#747E91`, rulerTxt `#C4CEDD`, inkD `#EEF2F8`, accent `#A4B2C8`, onAccent `#0F141C`, accentD `#A4B2C8`, sel `#F5C84C`, selD `#F5C84C`, unit `#FFB547`, unitD `#FFB547`, rec `#E0483A`, over `#FF6B60`, overD `#FF6B60`, warn `#F5C84C`, ok `#3ECF8E`, ph `#E6ECF5`, m0 `#12804f`, m1 `#3ecf8e`, m2 `#f5c84c`, m3 `#ff3b3b`, focusIn `#FFFFFF`, focusOut `#0F141C`, glass opacity 78 %, clip opacity 40 %, grid `164,178,200` × 1.

Track colours: `#516BC2` `#12A389` `#C6C069` `#C9335D` `#B67E16` `#9591FD` `#30EDFE` `#FD99B7`. Smallest CIEDE2000: normal 17.1, protan 14.8, deutan 15.1, tritan 14.8. Glass floor 78 %.

| Rule | Worst pair (fg on surface) | WCAG | APCA Lc | Pairs | Result |
|---|---|---|---|---|---|
| T1 Main text | `#EEF2F8` on laneSel `#2A3446` | 11.14 | -93.0 | 14 | pass |
| T2 Labels | `#C4CEDD` on glass over clips `#1E3544` | 8.02 | -70.5 | 10 | pass |
| T3 Quiet text (11 px, weight 500) | `#95A1B6` on glass over clips `#1E3544` | 4.89 | -45.2 | 11 | pass |
| T4 Disabled text | `#747E91` on strip `#1F2634` | 3.71 | -30.5 | 2 | pass |
| T5 Ruler numbers | `#C4CEDD` on ruler `#1A2130` | 10.14 | -74.0 | 1 | pass |
| T6 Units (amber, L2) on panels | `#FFB547` on strip `#1F2634` | 8.63 | -67.7 | 3 | pass |
| T6d Units in displays | `#FFB547` on display `#080B10` | 11.22 | -70.6 | 1 | pass |
| T7 Text on accent buttons | `#0F141C` on accent `#A4B2C8` | 8.60 | 60.8 | 1 | pass |
| T8 Over read-out in displays | `#FF6B60` on display `#080B10` | 7.06 | -48.7 | 1 | pass |
| T10 Text in displays | `#EEF2F8` on display `#080B10` | 17.54 | -98.9 | 1 | pass |
| T9 Over / error text on panels | `#FF6B60` on strip `#1F2634` | 5.43 | -45.8 | 2 | pass |
| U1 Accent (buttons on, links, toggles) | `#A4B2C8` on strip `#1F2634` | 7.06 | -57.0 | 4 | pass |
| U2 Selection outline (A1) | `#F5C84C` on laneSel `#2A3446` | 7.90 | -70.6 | 4 | pass |
| U3 Record button | `#E0483A` on panel `#161C27` | 4.19 | -33.3 | 2 | pass |
| U4 Playhead | `#E6ECF5` on lane1 `#1D2534` | 12.94 | -92.2 | 3 | pass |
| U5 Meter segments in their well | `#12804f` on display `#080B10` | 3.97 | -27.6 | 4 | pass |
| U6 Limit colours in displays | `#FF6B60` on display `#080B10` | 7.06 | -48.7 | 3 | pass |
| U9 Curves and handles in displays | `#A4B2C8` on display `#080B10` | 9.18 | -59.9 | 2 | pass |
| U7 Focus ring (two colours, best band) | `#FFFFFF` on laneSel `#2A3446` | 12.51 | – | 9 | pass |
| U8 Track colours against the lanes (clip edges) | `#C9335D` on lane1 `#1D2534` | 3.01 | -24.9 | 16 | pass |

Meaning colours apart (CIEDE2000): accent/sel 38.2, sel/over 40.2, sel/rec 43.6, accent/rec 39.4, accent/ok 31.9, ph/sel 34.0, ph/rec 43.6.

Readability fit: track colours: smallest CIEDE2000 over four visions 1.8 -> 14.8; glassA 0.55 → 0.78; dis #5A6476 → #747E91.

### TH-H Rutherford scattering (dark) ★★★★

Gold foil in the dark: near-black, gold accent and ruler, selection in the cyan of the scintillation screen. From: VC2 Rutherford Scattering (near black #0A0E18, gold traces #E9B751 / #CFA44A, the white nucleus). Icons that follow it: `rutherford-scattering`.

Tokens: bg `#07090F`, chrome `#0B0E16`, ruler `#10141D`, lane0 `#0F131C`, lane1 `#121620`, laneSel `#13232A`, panel `#0D1018`, panel2 `#141822`, strip `#131721`, display `#030406`, glass `#11151E`, line `#262A33`, ink `#F1EBDD`, lab `#CFC5AE`, mut `#A3987F`, dis `#807967`, rulerTxt `#E9B751`, inkD `#F1EBDD`, accent `#E9B751`, onAccent `#07090F`, accentD `#E9B751`, sel `#66D9F5`, selD `#66D9F5`, unit `#F2A65A`, unitD `#F2A65A`, rec `#FF4D4D`, over `#FF6B6B`, overD `#FF6B6B`, warn `#F5C84C`, ok `#3ECF8E`, ph `#F1EBDD`, m0 `#1F8A5A`, m1 `#3ECF8E`, m2 `#F5C84C`, m3 `#FF3B3B`, focusIn `#66D9F5`, focusOut `#07090F`, glass opacity 85 %, clip opacity 36 %, grid `233,183,81` × 0.8.

Track colours: `#FBE227` `#74B4ED` `#AEE1B0` `#F03C6D` `#7670FE` `#FB8F58` `#6FFEF4` `#B66EA4`. Smallest CIEDE2000: normal 18.1, protan 14.4, deutan 14.0, tritan 13.8. Glass floor 85 %.

| Rule | Worst pair (fg on surface) | WCAG | APCA Lc | Pairs | Result |
|---|---|---|---|---|---|
| T1 Main text | `#F1EBDD` on laneSel `#13232A` | 13.57 | -92.8 | 14 | pass |
| T2 Labels | `#CFC5AE` on glass over clips `#162129` | 9.54 | -69.8 | 10 | pass |
| T3 Quiet text (11 px, weight 500) | `#A3987F` on glass over clips `#162129` | 5.73 | -45.0 | 11 | pass |
| T4 Disabled text | `#807967` on strip `#131721` | 4.14 | -30.6 | 2 | pass |
| T5 Ruler numbers | `#E9B751` on ruler `#10141D` | 9.96 | -67.2 | 1 | pass |
| T6 Units (amber, L2) on panels | `#F2A65A` on strip `#131721` | 8.85 | -62.2 | 3 | pass |
| T6d Units in displays | `#F2A65A` on display `#030406` | 10.14 | -63.2 | 1 | pass |
| T7 Text on accent buttons | `#07090F` on accent `#E9B751` | 10.76 | 69.1 | 1 | pass |
| T8 Over read-out in displays | `#FF6B6B` on display `#030406` | 7.39 | -49.1 | 1 | pass |
| T10 Text in displays | `#F1EBDD` on display `#030406` | 17.26 | -95.0 | 1 | pass |
| T9 Over / error text on panels | `#FF6B6B` on strip `#131721` | 6.46 | -48.1 | 2 | pass |
| U1 Accent (buttons on, links, toggles) | `#E9B751` on strip `#131721` | 9.69 | -66.9 | 4 | pass |
| U2 Selection outline (A1) | `#66D9F5` on laneSel `#13232A` | 9.84 | -72.5 | 4 | pass |
| U3 Record button | `#FF4D4D` on panel `#0D1018` | 5.81 | -42.5 | 2 | pass |
| U4 Playhead | `#F1EBDD` on lane1 `#121620` | 15.21 | -94.1 | 3 | pass |
| U5 Meter segments in their well | `#1F8A5A` on display `#030406` | 4.73 | -32.0 | 4 | pass |
| U6 Limit colours in displays | `#FF6B6B` on display `#030406` | 7.39 | -49.1 | 3 | pass |
| U9 Curves and handles in displays | `#E9B751` on display `#030406` | 11.09 | -67.9 | 2 | pass |
| U7 Focus ring (two colours, best band) | `#66D9F5` on laneSel `#13232A` | 9.84 | – | 9 | pass |
| U8 Track colours against the lanes (clip edges) | `#7670FE` on lane1 `#121620` | 4.75 | -35.5 | 16 | pass |

Meaning colours apart (CIEDE2000): accent/sel 44.2, sel/over 64.9, sel/rec 68.4, accent/rec 38.9, accent/ok 36.2, ph/sel 26.9, ph/rec 38.8.

Readability fit: track colours: smallest CIEDE2000 over four visions 3.9 -> 13.8; glassA 0.6 → 0.85; mut #A0957C → #A3987F; dis #5F5847 → #807967.

### TH-I Chadwick (light) ★★★

A 1930s textbook plate: cream paper, brown ink, red and blue protons and neutrons. Warmer and darker-inked than Chart paper. From: FF8 Chadwick 1932 (cream #EFE4C8, brown ink #4A2A20, nucleus red #C9402E and blue #2A5AA8). Icons that follow it: `chadwick-1932`.

Tokens: bg `#E2D5B5`, chrome `#E8DDC0`, ruler `#EDE3CA`, lane0 `#F3EAD3`, lane1 `#EFE5CB`, laneSel `#F7E7B0`, panel `#F6EFDD`, panel2 `#ECE2C8`, strip `#EADFC4`, display `#2A1A14`, glass `#F4ECD8`, line `#C9B992`, ink `#2E1C15`, lab `#4A3326`, mut `#6E5747`, dis `#A3937A`, rulerTxt `#2E1C15`, inkD `#F3EAD3`, accent `#2A5AA8`, onAccent `#FFFFFF`, accentD `#3767B7`, sel `#A87400`, selD `#A87400`, unit `#A6421C`, unitD `#FFB062`, rec `#C9402E`, over `#B8321F`, overD `#FF6B55`, warn `#F2C84B`, ok `#5FCB82`, ph `#2A5AA8`, m0 `#3E9E5E`, m1 `#6FD08F`, m2 `#F2C84B`, m3 `#FF5A45`, focusIn `#2A5AA8`, focusOut `#FFFFFF`, glass opacity 90 %, clip opacity 85 %, grid `74,42,32` × 1.2.

Track colours: `#6468E2` `#4E7D50` `#A87C0F` `#E44D6A` `#8E5911` `#6C5491` `#0091A2` `#8E0B5F`. Smallest CIEDE2000: normal 14.4, protan 12.5, deutan 12.1, tritan 12.2. Glass floor 85 %.

| Rule | Worst pair (fg on surface) | WCAG | APCA Lc | Pairs | Result |
|---|---|---|---|---|---|
| T1 Main text | `#2E1C15` on bg `#E2D5B5` | 11.15 | 79.1 | 14 | pass |
| T2 Labels | `#4A3326` on glass over clips `#EBD9CE` | 8.56 | 76.5 | 10 | pass |
| T3 Quiet text (11 px, weight 500) | `#6E5747` on bg `#E2D5B5` | 4.63 | 59.2 | 11 | pass |
| T4 Disabled text | `#A3937A` on strip `#EADFC4` | 2.26 | 38.2 | 2 | pass |
| T5 Ruler numbers | `#2E1C15` on ruler `#EDE3CA` | 12.71 | 86.9 | 1 | pass |
| T6 Units (amber, L2) on panels | `#A6421C` on chrome `#E8DDC0` | 4.55 | 60.2 | 3 | pass |
| T6d Units in displays | `#FFB062` on display `#2A1A14` | 9.26 | -67.4 | 1 | pass |
| T7 Text on accent buttons | `#FFFFFF` on accent `#2A5AA8` | 6.72 | -87.8 | 1 | pass |
| T8 Over read-out in displays | `#FF6B55` on display `#2A1A14` | 5.96 | -46.8 | 1 | pass |
| T10 Text in displays | `#F3EAD3` on display `#2A1A14` | 13.95 | -92.6 | 1 | pass |
| T9 Over / error text on panels | `#B8321F` on strip `#EADFC4` | 4.51 | 60.1 | 2 | pass |
| U1 Accent (buttons on, links, toggles) | `#2A5AA8` on bg `#E2D5B5` | 4.61 | 58.7 | 4 | pass |
| U2 Selection outline (A1) | `#A87400` on strip `#EADFC4` | 3.07 | 49.1 | 4 | pass |
| U3 Record button | `#C9402E` on chrome `#E8DDC0` | 3.65 | 53.4 | 2 | pass |
| U4 Playhead | `#2A5AA8` on ruler `#EDE3CA` | 5.26 | 66.6 | 3 | pass |
| U5 Meter segments in their well | `#3E9E5E` on display `#2A1A14` | 4.98 | -39.1 | 4 | pass |
| U6 Limit colours in displays | `#FF6B55` on display `#2A1A14` | 5.96 | -46.8 | 3 | pass |
| U9 Curves and handles in displays | `#3767B7` on display `#2A1A14` | 3.01 | -22.5 | 2 | pass |
| U7 Focus ring (two colours, best band) | `#2A5AA8` on bg `#E2D5B5` | 4.61 | – | 9 | pass |
| U8 Track colours against the lanes (clip edges) | `#0091A2` on lane1 `#EFE5CB` | 3.00 | 49.5 | 16 | pass |

Meaning colours apart (CIEDE2000): accent/sel 52.8, sel/over 28.9, sel/rec 28.3, accent/rec 43.5, accent/ok 56.3, ph/sel 52.8, ph/rec 43.5.

Readability fit: track colours: smallest CIEDE2000 over four visions 1.1 -> 12.1; unit #A8441E → #A6421C; accentD #2A5AA8 → #3767B7.

### TH-J Patent drawing (light) ★★★★

The lightest theme: white drawing board, black ink, a blue pencil for the accent. Displays stay black wells. From: VB5 Patent Drawing (white #FBFAF6, black ink #535251 lines, dashed). Icons that follow it: `patent-drawing`.

Tokens: bg `#ECEBE6`, chrome `#F3F2EE`, ruler `#F7F6F2`, lane0 `#FDFCF9`, lane1 `#F8F7F3`, laneSel `#FFF7D6`, panel `#FFFFFF`, panel2 `#F4F3EF`, strip `#F1F0EB`, display `#1E1E1D`, glass `#FFFFFF`, line `#CFCDC6`, ink `#1E1E1D`, lab `#3A3A38`, mut `#5F5E5A`, dis `#A3A29C`, rulerTxt `#1E1E1D`, inkD `#FDFCF9`, accent `#1F4FB8`, onAccent `#FFFFFF`, accentD `#3163CE`, sel `#9C6F00`, selD `#9C6F00`, unit `#9A4A00`, unitD `#FFB547`, rec `#C62828`, over `#B71C1C`, overD `#FF6B6B`, warn `#F2C84B`, ok `#6FD08F`, ph `#1F4FB8`, m0 `#2E9E5E`, m1 `#6FD08F`, m2 `#F2C84B`, m3 `#FF5A45`, focusIn `#1F4FB8`, focusOut `#FFFFFF`, glass opacity 92 %, clip opacity 90 %, grid `40,40,38` × 1.3.

Track colours: `#6659EC` `#5F9682` `#906946` `#8B0109` `#CF7901` `#4E3471` `#2E6D6F` `#742E45`. Smallest CIEDE2000: normal 17.3, protan 14.8, deutan 14.9, tritan 14.7. Glass floor 80 %.

| Rule | Worst pair (fg on surface) | WCAG | APCA Lc | Pairs | Result |
|---|---|---|---|---|---|
| T1 Main text | `#1E1E1D` on bg `#ECEBE6` | 13.98 | 91.7 | 14 | pass |
| T2 Labels | `#3A3A38` on glass over clips `#F7EDED` | 9.93 | 86.9 | 10 | pass |
| T3 Quiet text (11 px, weight 500) | `#5F5E5A` on bg `#ECEBE6` | 5.44 | 70.3 | 11 | pass |
| T4 Disabled text | `#A3A29C` on strip `#F1F0EB` | 2.24 | 41.1 | 2 | pass |
| T5 Ruler numbers | `#1E1E1D` on ruler `#F7F6F2` | 15.43 | 98.2 | 1 | pass |
| T6 Units (amber, L2) on panels | `#9A4A00` on strip `#F1F0EB` | 5.49 | 71.6 | 3 | pass |
| T6d Units in displays | `#FFB547` on display `#1E1E1D` | 9.50 | -69.0 | 1 | pass |
| T7 Text on accent buttons | `#FFFFFF` on accent `#1F4FB8` | 7.32 | -89.7 | 1 | pass |
| T8 Over read-out in displays | `#FF6B6B` on display `#1E1E1D` | 6.01 | -47.3 | 1 | pass |
| T10 Text in displays | `#FDFCF9` on display `#1E1E1D` | 16.26 | -104.1 | 1 | pass |
| T9 Over / error text on panels | `#B71C1C` on strip `#F1F0EB` | 5.76 | 71.6 | 2 | pass |
| U1 Accent (buttons on, links, toggles) | `#1F4FB8` on bg `#ECEBE6` | 6.13 | 72.9 | 4 | pass |
| U2 Selection outline (A1) | `#9C6F00` on strip `#F1F0EB` | 3.93 | 61.8 | 4 | pass |
| U3 Record button | `#C62828` on chrome `#F3F2EE` | 5.02 | 68.7 | 2 | pass |
| U4 Playhead | `#1F4FB8` on ruler `#F7F6F2` | 6.77 | 79.4 | 3 | pass |
| U5 Meter segments in their well | `#2E9E5E` on display `#1E1E1D` | 4.90 | -38.7 | 4 | pass |
| U6 Limit colours in displays | `#FF6B6B` on display `#1E1E1D` | 6.01 | -47.3 | 3 | pass |
| U9 Curves and handles in displays | `#3163CE` on display `#1E1E1D` | 3.02 | -22.9 | 2 | pass |
| U7 Focus ring (two colours, best band) | `#1F4FB8` on bg `#ECEBE6` | 6.13 | – | 9 | pass |
| U8 Track colours against the lanes (clip edges) | `#CF7901` on lane1 `#F8F7F3` | 3.07 | 54.9 | 16 | pass |

Meaning colours apart (CIEDE2000): accent/sel 56.9, sel/over 32.4, sel/rec 32.5, accent/rec 43.3, accent/ok 60.1, ph/sel 56.9, ph/rec 43.3.

Readability fit: track colours: smallest CIEDE2000 over four visions 1.7 -> 14.7; accentD #1F4FB8 → #3163CE.

### TH-K Cyanotype (dark, new) ★★★★

New: a sun print. Softer and lighter than Blueprint, slate-blue ground and pale print lines; the brightest of the dark themes. From: VB7 Cyanotype (Prussian slate #324C73, pale print #D1E2EF). Icons that follow it: `cyanotype`.

Tokens: bg `#1D2D45`, chrome `#22344F`, ruler `#263A57`, lane0 `#2A405F`, lane1 `#2D4464`, laneSel `#3A5478`, panel `#243853`, panel2 `#2B4161`, strip `#2A3F5E`, display `#111C2D`, glass `#2A3F5E`, line `#45608A`, ink `#F2F7FB`, lab `#D1E2EF`, mut `#A8C0D6`, dis `#738CA9`, rulerTxt `#D1E2EF`, inkD `#F2F7FB`, accent `#D1E2EF`, onAccent `#1D2D45`, accentD `#D1E2EF`, sel `#FFD86B`, selD `#FFD86B`, unit `#FFC27A`, unitD `#FFC27A`, rec `#FF6A5C`, over `#FF8577`, overD `#FF8577`, warn `#FFD86B`, ok `#7FE3AE`, ph `#FFFFFF`, m0 `#3BB27A`, m1 `#7FE3AE`, m2 `#FFD86B`, m3 `#FF6A5C`, focusIn `#FFFFFF`, focusOut `#111C2D`, glass opacity 80 %, clip opacity 40 %, grid `209,226,239` × 1.

Track colours: `#87ACFE` `#B7EABF` `#FDFC6D` `#F4767D` `#E9B046` `#E6D0F9` `#F5FEFF` `#C3A0BA`. Smallest CIEDE2000: normal 13.4, protan 13.2, deutan 13.0, tritan 13.0. Glass floor 80 %.

| Rule | Worst pair (fg on surface) | WCAG | APCA Lc | Pairs | Result |
|---|---|---|---|---|---|
| T1 Main text | `#F2F7FB` on laneSel `#3A5478` | 7.16 | -85.7 | 14 | pass |
| T2 Labels | `#D1E2EF` on glass over clips `#3A4E6B` | 6.38 | -73.4 | 10 | pass |
| T3 Quiet text (11 px, weight 500) | `#A8C0D6` on glass over clips `#3A4E6B` | 4.50 | -52.7 | 11 | pass |
| T4 Disabled text | `#738CA9` on strip `#2A3F5E` | 3.07 | -30.1 | 2 | pass |
| T5 Ruler numbers | `#D1E2EF` on ruler `#263A57` | 8.68 | -79.8 | 1 | pass |
| T6 Units (amber, L2) on panels | `#FFC27A` on strip `#2A3F5E` | 6.72 | -67.3 | 3 | pass |
| T6d Units in displays | `#FFC27A` on display `#111C2D` | 10.79 | -75.0 | 1 | pass |
| T7 Text on accent buttons | `#1D2D45` on accent `#D1E2EF` | 10.46 | 81.9 | 1 | pass |
| T8 Over read-out in displays | `#FF8577` on display `#111C2D` | 7.23 | -54.3 | 1 | pass |
| T10 Text in displays | `#F2F7FB` on display `#111C2D` | 15.86 | -100.5 | 1 | pass |
| T9 Over / error text on panels | `#FF8577` on strip `#2A3F5E` | 4.50 | -46.5 | 2 | pass |
| U1 Accent (buttons on, links, toggles) | `#D1E2EF` on strip `#2A3F5E` | 8.03 | -78.3 | 4 | pass |
| U2 Selection outline (A1) | `#FFD86B` on laneSel `#3A5478` | 5.62 | -69.0 | 4 | pass |
| U3 Record button | `#FF6A5C` on panel `#243853` | 4.23 | -41.5 | 2 | pass |
| U4 Playhead | `#FFFFFF` on lane1 `#2D4464` | 9.89 | -97.0 | 3 | pass |
| U5 Meter segments in their well | `#FF6A5C` on display `#111C2D` | 6.08 | -47.0 | 4 | pass |
| U6 Limit colours in displays | `#FF8577` on display `#111C2D` | 7.23 | -54.3 | 3 | pass |
| U9 Curves and handles in displays | `#FFD86B` on display `#111C2D` | 12.45 | -83.8 | 2 | pass |
| U7 Focus ring (two colours, best band) | `#FFFFFF` on laneSel `#3A5478` | 7.72 | – | 9 | pass |
| U8 Track colours against the lanes (clip edges) | `#F4767D` on lane1 `#2D4464` | 3.64 | -38.9 | 16 | pass |

Meaning colours apart (CIEDE2000): accent/sel 34.6, sel/over 37.1, sel/rec 40.8, accent/rec 40.1, accent/ok 26.5, ph/sel 26.2, ph/rec 36.5.

Readability fit: track colours: smallest CIEDE2000 over four visions 0.6 -> 13.0; glassA 0.6 → 0.8; dis #6D86A3 → #738CA9.

### TH-L Atomic age (dark, new) ★★★

New: the 1950s atomic age. Deep teal, cream type, a sea-glass accent and a gold playhead. From: VA4 Sputnik (teal #1F3A4A, cream #E5D8B8, gold #E8B33B, orange #EA6A2E) and VA3 Halftone Print. Icons that follow it: `sputnik`, `halftone-print`.

Tokens: bg `#0F1E27`, chrome `#142833`, ruler `#18303D`, lane0 `#1A3240`, lane1 `#1C3544`, laneSel `#284556`, panel `#152A36`, panel2 `#1C3442`, strip `#1B3341`, display `#0A141A`, glass `#1C3442`, line `#2F4B5B`, ink `#F2EAD6`, lab `#E5D8B8`, mut `#B3A88C`, dis `#7E8476`, rulerTxt `#E5D8B8`, inkD `#F2EAD6`, accent `#6FD3C8`, onAccent `#0F1E27`, accentD `#6FD3C8`, sel `#F2C84B`, selD `#F2C84B`, unit `#F0A25A`, unitD `#F0A25A`, rec `#F2553C`, over `#FF7360`, overD `#FF7360`, warn `#F2C84B`, ok `#9ED67A`, ph `#6FD3C8`, m0 `#3E9E63`, m1 `#9ED67A`, m2 `#F2C84B`, m3 `#FF5E4A`, focusIn `#F2EAD6`, focusOut `#0A141A`, glass opacity 83 %, clip opacity 45 %, grid `229,216,184` × 1.

Track colours: `#D7B202` `#F07C74` `#67D8B4` `#99A9FA` `#AF647B` `#A282AF` `#DAEE99` `#F7CDF2`. Smallest CIEDE2000: normal 15.4, protan 13.8, deutan 13.6, tritan 13.6. Glass floor 83 %.

| Rule | Worst pair (fg on surface) | WCAG | APCA Lc | Pairs | Result |
|---|---|---|---|---|---|
| T1 Main text | `#F2EAD6` on laneSel `#284556` | 8.44 | -84.1 | 14 | pass |
| T2 Labels | `#E5D8B8` on glass over clips `#2A4248` | 7.53 | -74.1 | 10 | pass |
| T3 Quiet text (11 px, weight 500) | `#B3A88C` on glass over clips `#2A4248` | 4.51 | -46.2 | 11 | pass |
| T4 Disabled text | `#7E8476` on strip `#1B3341` | 3.41 | -30.4 | 2 | pass |
| T5 Ruler numbers | `#E5D8B8` on ruler `#18303D` | 9.71 | -78.9 | 1 | pass |
| T6 Units (amber, L2) on panels | `#F0A25A` on strip `#1B3341` | 6.28 | -56.2 | 3 | pass |
| T6d Units in displays | `#F0A25A` on display `#0A141A` | 8.88 | -60.8 | 1 | pass |
| T7 Text on accent buttons | `#0F1E27` on accent `#6FD3C8` | 9.57 | 69.2 | 1 | pass |
| T8 Over read-out in displays | `#FF7360` on display `#0A141A` | 6.98 | -50.1 | 1 | pass |
| T10 Text in displays | `#F2EAD6` on display `#0A141A` | 15.53 | -93.8 | 1 | pass |
| T9 Over / error text on panels | `#FF7360` on strip `#1B3341` | 4.93 | -45.5 | 2 | pass |
| U1 Accent (buttons on, links, toggles) | `#6FD3C8` on strip `#1B3341` | 7.41 | -64.9 | 4 | pass |
| U2 Selection outline (A1) | `#F2C84B` on laneSel `#284556` | 6.33 | -65.7 | 4 | pass |
| U3 Record button | `#F2553C` on panel `#152A36` | 4.34 | -37.6 | 2 | pass |
| U4 Playhead | `#6FD3C8` on lane1 `#1C3544` | 7.20 | -64.4 | 3 | pass |
| U5 Meter segments in their well | `#3E9E63` on display `#0A141A` | 5.56 | -40.4 | 4 | pass |
| U6 Limit colours in displays | `#FF7360` on display `#0A141A` | 6.98 | -50.1 | 3 | pass |
| U9 Curves and handles in displays | `#6FD3C8` on display `#0A141A` | 10.49 | -69.5 | 2 | pass |
| U7 Focus ring (two colours, best band) | `#F2EAD6` on laneSel `#284556` | 8.44 | – | 9 | pass |
| U8 Track colours against the lanes (clip edges) | `#AF647B` on lane1 `#1C3544` | 3.00 | -26.7 | 16 | pass |

Meaning colours apart (CIEDE2000): accent/sel 36.4, sel/over 38.4, sel/rec 40.8, accent/rec 57.8, accent/ok 22.3, ph/sel 36.4, ph/rec 57.8.

Readability fit: track colours: smallest CIEDE2000 over four visions 1.3 -> 13.6; glassA 0.6 → 0.83; dis #6E7466 → #7E8476.

### TH-M Phosphor (dark, new) ★★★

New: an oscilloscope screen. Black-green ground, phosphor-green accent and traces, amber selection like an amber CRT. From: VC6 Orbital Wireframe (black-green #02100E, phosphor #32B38F to #3EF8C5). Icons that follow it: `orbital-wireframe`.

Tokens: bg `#020B09`, chrome `#05120F`, ruler `#071814`, lane0 `#081A15`, lane1 `#0A1D18`, laneSel `#103028`, panel `#06140F`, panel2 `#0B1E19`, strip `#0B1D18`, display `#010605`, glass `#0A1C17`, line `#16362D`, ink `#DDF7EE`, lab `#AEE3D2`, mut `#7FB5A4`, dis `#568275`, rulerTxt `#8FE6C8`, inkD `#DDF7EE`, accent `#35E4B3`, onAccent `#02100E`, accentD `#35E4B3`, sel `#F5D04C`, selD `#F5D04C`, unit `#FFB547`, unitD `#FFB547`, rec `#FF5A5A`, over `#FF6B6B`, overD `#FF6B6B`, warn `#F5D04C`, ok `#C5F27C`, ph `#DDF7EE`, m0 `#1F9E70`, m1 `#35E4B3`, m2 `#F5D04C`, m3 `#FF4D4D`, focusIn `#35E4B3`, focusOut `#010605`, glass opacity 60 %, clip opacity 30 %, grid `50,179,143` × 1.

Track colours: `#8BFEDC` `#528CFE` `#F6FBA6` `#F34C06` `#FDBB2E` `#C6B8FD` `#91C4C1` `#D97993`. Smallest CIEDE2000: normal 16.7, protan 13.8, deutan 13.7, tritan 13.7. Glass floor 40 %.

| Rule | Worst pair (fg on surface) | WCAG | APCA Lc | Pairs | Result |
|---|---|---|---|---|---|
| T1 Main text | `#DDF7EE` on glass over clips `#263627` | 11.35 | -93.1 | 14 | pass |
| T2 Labels | `#AEE3D2` on glass over clips `#263627` | 8.98 | -77.3 | 10 | pass |
| T3 Quiet text (11 px, weight 500) | `#7FB5A4` on glass over clips `#263627` | 5.52 | -50.7 | 11 | pass |
| T4 Disabled text | `#568275` on strip `#0B1D18` | 4.03 | -30.4 | 2 | pass |
| T5 Ruler numbers | `#8FE6C8` on ruler `#071814` | 12.46 | -80.4 | 1 | pass |
| T6 Units (amber, L2) on panels | `#FFB547` on strip `#0B1D18` | 9.93 | -69.4 | 3 | pass |
| T6d Units in displays | `#FFB547` on display `#010605` | 11.61 | -70.8 | 1 | pass |
| T7 Text on accent buttons | `#02100E` on accent `#35E4B3` | 11.91 | 75.8 | 1 | pass |
| T8 Over read-out in displays | `#FF6B6B` on display `#010605` | 7.35 | -49.1 | 1 | pass |
| T10 Text in displays | `#DDF7EE` on display `#010605` | 18.08 | -98.8 | 1 | pass |
| T9 Over / error text on panels | `#FF6B6B` on strip `#0B1D18` | 6.29 | -47.7 | 2 | pass |
| U1 Accent (buttons on, links, toggles) | `#35E4B3` on strip `#0B1D18` | 10.72 | -74.1 | 4 | pass |
| U2 Selection outline (A1) | `#F5D04C` on laneSel `#103028` | 9.49 | -75.9 | 4 | pass |
| U3 Record button | `#FF5A5A` on panel `#06140F` | 6.16 | -44.8 | 2 | pass |
| U4 Playhead | `#DDF7EE` on lane1 `#0A1D18` | 15.49 | -97.4 | 3 | pass |
| U5 Meter segments in their well | `#1F9E70` on display `#010605` | 6.01 | -40.7 | 4 | pass |
| U6 Limit colours in displays | `#FF6B6B` on display `#010605` | 7.35 | -49.1 | 3 | pass |
| U9 Curves and handles in displays | `#35E4B3` on display `#010605` | 12.53 | -75.4 | 2 | pass |
| U7 Focus ring (two colours, best band) | `#35E4B3` on laneSel `#103028` | 8.74 | – | 9 | pass |
| U8 Track colours against the lanes (clip edges) | `#F34C06` on lane1 `#0A1D18` | 4.87 | -38.2 | 16 | pass |

Meaning colours apart (CIEDE2000): accent/sel 35.5, sel/over 45.4, sel/rec 46.8, accent/rec 72.6, accent/ok 21.2, ph/sel 29.4, ph/rec 48.2.

Readability fit: track colours: smallest CIEDE2000 over four visions 1.7 -> 13.7; dis #3F6B5E → #568275.

### TH-N Deep orbit (dark, new) ★★★★

New: the icon's own navy. Today's look moved onto P2: navy strips, field-blue accent, nucleus-yellow selection, electron-cyan playhead. From: P2 Orbit night as printed on the icon (tile #132044 to #070910, rings #EAF1FF, nucleus #FFC43C, electron #4CC9F0, field #6096FF). Icons that follow it: `field-depth`, `dipole-field`.

Tokens: bg `#070910`, chrome `#0C1228`, ruler `#101833`, lane0 `#111A36`, lane1 `#131D3B`, laneSel `#1E2A50`, panel `#0E1630`, panel2 `#141E3E`, strip `#132044`, display `#05070D`, glass `#132044`, line `#26325A`, ink `#EAF1FF`, lab `#C3CFEA`, mut `#8F9EC6`, dis `#6D7BA2`, rulerTxt `#C3CFEA`, inkD `#EAF1FF`, accent `#85AEFC`, onAccent `#070910`, accentD `#85AEFC`, sel `#FFC43C`, selD `#FFC43C`, unit `#FFB547`, unitD `#FFB547`, rec `#FF5A5A`, over `#FF6B6B`, overD `#FF6B6B`, warn `#FFC43C`, ok `#3ECF8E`, ph `#4CC9F0`, m0 `#12804f`, m1 `#3ecf8e`, m2 `#FFC43C`, m3 `#ff3b3b`, focusIn `#4CC9F0`, focusOut `#070910`, glass opacity 85 %, clip opacity 38 %, grid `96,150,255` × 0.9.

Track colours: `#626AC0` `#1DAA92` `#FEE3AB` `#FE4079` `#CC8614` `#BE8DFE` `#00ECFE` `#FC9AC9`. Smallest CIEDE2000: normal 18.6, protan 12.9, deutan 13.3, tritan 12.8. Glass floor 80 %.

| Rule | Worst pair (fg on surface) | WCAG | APCA Lc | Pairs | Result |
|---|---|---|---|---|---|
| T1 Main text | `#EAF1FF` on laneSel `#1E2A50` | 12.33 | -94.1 | 14 | pass |
| T2 Labels | `#C3CFEA` on glass over clips `#202A48` | 9.04 | -73.1 | 10 | pass |
| T3 Quiet text (11 px, weight 500) | `#8F9EC6` on glass over clips `#202A48` | 5.30 | -45.9 | 11 | pass |
| T4 Disabled text | `#6D7BA2` on strip `#132044` | 3.80 | -30.2 | 2 | pass |
| T5 Ruler numbers | `#C3CFEA` on ruler `#101833` | 11.19 | -75.9 | 1 | pass |
| T6 Units (amber, L2) on panels | `#FFB547` on strip `#132044` | 9.07 | -68.3 | 3 | pass |
| T6d Units in displays | `#FFB547` on display `#05070D` | 11.46 | -70.7 | 1 | pass |
| T7 Text on accent buttons | `#070910` on accent `#85AEFC` | 8.96 | 60.2 | 1 | pass |
| T8 Over read-out in displays | `#FF6B6B` on display `#05070D` | 7.26 | -49.0 | 1 | pass |
| T10 Text in displays | `#EAF1FF` on display `#05070D` | 17.77 | -98.4 | 1 | pass |
| T9 Over / error text on panels | `#FF6B6B` on strip `#132044` | 5.74 | -46.6 | 2 | pass |
| U1 Accent (buttons on, links, toggles) | `#85AEFC` on strip `#132044` | 7.18 | -56.0 | 4 | pass |
| U2 Selection outline (A1) | `#FFC43C` on laneSel `#1E2A50` | 8.80 | -72.2 | 4 | pass |
| U3 Record button | `#FF5A5A` on panel `#0E1630` | 5.83 | -44.2 | 2 | pass |
| U4 Playhead | `#4CC9F0` on lane1 `#131D3B` | 8.62 | -64.0 | 3 | pass |
| U5 Meter segments in their well | `#12804f` on display `#05070D` | 4.05 | -27.7 | 4 | pass |
| U6 Limit colours in displays | `#FF6B6B` on display `#05070D` | 7.26 | -49.0 | 3 | pass |
| U9 Curves and handles in displays | `#85AEFC` on display `#05070D` | 9.07 | -58.5 | 2 | pass |
| U7 Focus ring (two colours, best band) | `#4CC9F0` on laneSel `#1E2A50` | 7.27 | – | 9 | pass |
| U8 Track colours against the lanes (clip edges) | `#626AC0` on lane1 `#131D3B` | 3.43 | -26.3 | 16 | pass |

Meaning colours apart (CIEDE2000): accent/sel 53.3, sel/over 40.9, sel/rec 42.1, accent/rec 43.8, accent/ok 42.7, ph/sel 49.7, ph/rec 64.0.

Readability fit: track colours: smallest CIEDE2000 over four visions 1.0 -> 12.8; glassA 0.55 → 0.85; mut #8D9CC4 → #8F9EC6; dis #525F85 → #6D7BA2; accent / onAccent #6096FF / #070910 → #85AEFC / #070910.


## 7. Proposed tasks after the picks

| Task | Lane | What |
|---|---|---|
| TM1 tokens and switcher | new lane R (themes, prefix `tm`) | the semantic tokens in `LOOK` and on `:root`; the theme files for the picks; `tmApply`; the "Other programs" conversion of `THEMES`; `TM_HOOKS` for the other lanes |
| TM2 gate | lane R | `check.py --gate` (or a Node port) as a step in `docs/release-gate.md`, baseline file for theme A's known misses |
| TM3 icon link | lane R with the icon tasks' picker hook | "Icon follows theme" |
| Settings row | lane B | Theme cards (drawn like the page's thumbnails), Adjust sliders, Follow system appearance, Icon follows theme |
| Token adoption | lanes A, E, F, I (one step each, in their own area) | arrangement, clips and lanes; meters and displays read `LOOK`; menus, dialogs and tooltips; device frames |
| Glass floor | the glass engine's owner | never below the theme's floor; optional text plate |
| Comfort | lane P | Night and OLED care read the active theme; OLED care has nothing to dim in a light theme |

## 8. Files (`tools/design-lab/th1/`)

| File | What |
|---|---|
| `colour.py` | WCAG 2.2, APCA 0.1.9 (SA98G), OKLab/OKLCH, CIEDE2000, Machado 2009 |
| `themes_src.py` | the themes as drawn from the icons, before fitting |
| `check.py` | fit, tune, measure; `--gate` measures only and exits 1 on a failure |
| `themes.json`, `report.md`, `themes-tables.md` | results |
| `page.src.html`, `build.py`, `pick-page.html` | the pick page (self-contained; icons embedded at 96 px) |

## Sources

1. Ableton Live 12 manual, First Steps: https://www.ableton.com/en/live-manual/12/first-steps/
2. Ableton forum, Live 12 readability: https://forum.ableton.com/viewtopic.php?p=1826691
3. Ableton forum, arrangement shading (.ask keys): https://forum.ableton.com/viewtopic.php?p=1836508
4. Bitwig user guide, Dashboard: https://www.bitwig.com/userguide/latest/the_dashboard/
5. CDM, Bitwig Studio 6 details: https://cdm.link/bitwig-studio-6-details/
6. CDM, Bitwig themes (2024): https://cdm.link/2024/07/bitwig-themes/
7. FL Studio manual, Themes: https://www.image-line.com/fl-studio-learning-content/fl-studio-online-manual/html/envsettings_themes.htm
8. REAPER WALTER reference: https://www.reaper.fm/sdk/walter/walter
9. REAPER theme structure: https://www.reaper.fm/sdk/walter/images
10. REAPER Blog, Default 7 Theme Adjuster: https://reaper.blog/2024/06/theme-adjuster/
11. Nuendo 11, Track and MixConsole channel colours: https://steinberg.help/nuendo/v11/en/cubase_nuendo/topics/preferences/preferences_user_interface_track_channel_colors_r.html
12. Steinberg forum, Cubase 15 missing UI colours: https://forums.steinberg.net/t/missing-ui-colors/1013780
13. Steinberg forum, Cubase 14 GUI regressions: https://forums.steinberg.net/t/cubase-14-gui-design-regressions/953624
14. Fender Studio Pro manual, General options: https://fenderstudiopromanual.fender.com/en/Content/Setup_Topics/General_Options.htm
15. Fender Studio Pro manual, Advanced options: https://fenderstudiopromanual.fender.com/en/Content/Setup_Topics/Advanced_Options.htm
16. Logic Pro user guide, Tracks settings: https://support.apple.com/guide/logicpro/lgcp8e0207b2/mac
17. Production Expert, Pro Tools 2020.11 dark theme: https://www.production-expert.com/home-page/pro-tools-2020-11-released?format=amp
18. Renoise, GUI customisation: https://tutorials.renoise.com/wiki/GUI_Customisation
19. Reason Studios, changing themes: https://help.reasonstudios.com/hc/en-us/articles/360002215614-How-can-I-change-Themes-in-Reason
20. Vital forum, skins: https://forum.vital.audio/t/how-to-make-your-own-skin-in-vital-a-free-skin/5602
21. W3C DTCG, first stable version: https://www.w3.org/community/design-tokens/2025/10/28/design-tokens-specification-reaches-first-stable-version/
22. Design Tokens 2025.10: https://www.designtokens.org/tr/2025.10/
23. Design Tokens Resolver module: https://www.designtokens.org/tr/2025.10/resolver/
24. Style Dictionary, DTCG support: https://deploy-preview-1589--styledictionaryjs.netlify.app/info/dtcg
25. Carbon, themes: https://carbondesignsystem.com/elements/themes/overview/
26. primer/primitives: https://github.com/primer/primitives
27. Primer contrast workflow: https://raw.githubusercontent.com/primer/primitives/main/.github/workflows/a11y-contrast.yml
28. Material Web, colour: https://material-web.dev/theming/color
29. Spectrum colour system: https://spectrum.adobe.com/page/color-system
30. VS Code theme colour reference: https://code.visualstudio.com/api/references/theme-color
31. VS Code themes: https://code.visualstudio.com/docs/configure/themes
32. JetBrains, Islands theme: https://plugins.jetbrains.com/docs/intellij/supporting-islands-theme.html
33. Figma, Illuminating dark mode: https://www.figma.com/blog/illuminating-dark-mode/
34. Blender manual, themes: https://docs.blender.org/manual/en/latest/editors/preferences/themes.html
35. Premiere Pro, appearance preferences: https://helpx.adobe.com/premiere-pro-next/learn-the-basics/configure-preferences/appearance-preferences.html
36. Apple HIG, colour: https://developer.apple.com/design/human-interface-guidelines/color
37. Microsoft, contrast themes: https://learn.microsoft.com/windows/apps/design/accessibility/high-contrast-themes
38. MDN, light-dark(): https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Values/color_value/light-dark
39. MDN, forced-colors: https://developer.mozilla.org/en-US/docs/Web/CSS/@media/forced-colors
40. Electron, nativeTheme: https://www.electronjs.org/docs/latest/api/native-theme
41. WCAG 2.2: https://www.w3.org/TR/WCAG22/
42. Understanding 1.4.11: https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html
43. Understanding 2.4.13: https://www.w3.org/WAI/WCAG22/Understanding/focus-appearance.html
44. Technique C40: https://www.w3.org/WAI/WCAG22/Techniques/css/C40
45. apca-w3 source: https://raw.githubusercontent.com/Myndex/apca-w3/master/src/apca-w3.js
46. APCA introduction: https://github.com/Myndex/apca-introduction
47. WCAG 3.0 history: https://www.w3.org/standards/history/wcag-3.0
48. Material dark theme codelab: https://codelabs.developers.google.com/codelabs/design-material-darktheme/
49. Level Access, astigmatism: https://www.levelaccess.com/blog/accessibility-for-people-with-astigmatism/
50. Birch 2012: https://pubmed.ncbi.nlm.nih.gov/22472762/
51. Machado et al. 2009: https://www.inf.ufrgs.br/~oliveira/pubs_files/CVD_Simulation/CVD_Simulation.html
52. cols4all paper: https://mtennekes.github.io/cols4all/articles/01_paper.html
53. Paul Tol: https://personal.sron.nl/~pault/
54. Atlassian, colour: https://www.atlassian.design/foundations/color
55. Six Colors, Liquid Glass: https://sixcolors.com/post/2025/11/soaping-up-liquid-glass-less-transparency-more-contrast/
56. Microsoft, Acrylic: https://learn.microsoft.com/windows/uwp/style/acrylic
57. Terrazzo a11y-min-contrast: https://app.unpkg.com/@terrazzo/parser@0.8.1/files/src/lint/plugin-core/rules/a11y-min-contrast.ts

Unconfirmed or guessed: Serum 2's skin format, a track-colour intensity control in Live 12, Pro Tools' palette controls, the per-theme glass "text plate" (a proposal, not measured on the Mac), and the cost of `tmApply` (estimated from today's `applyTheme` plus one redraw; to be measured by TM1).

## The user's picks

28 November 2026, 15:05 Brussels: `Theme picks: A B C D E G H J | default: A | icons follow theme: yes`, then: "Let's rework these themes that I gave you in Fable and then come back to me."

- Kept: **A** Orbit night (the default), **B** Chart paper, **C** Space Race, **D** Chalkboard, **E** Blueprint, **G** Cutaway nucleus, **H** Rutherford scattering, **J** Patent drawing. Dropped: B2, F, I, K, L, M, N.
- Icons follow theme: yes (TM3).
- Next: task **TH2** (on Fable) reworks these eight into a second, higher-quality pick page; the user picks again, then the build lane (task TM, its own new lane, prefix `tm`; lane R is now SG2's) is created. Section 7's lane letter "R" is replaced by the next free letter.

## Round 2 (TH2)

28 November 2026. Pick page artifact "AudioLab themes, round 2: the eight picks reworked": https://claude.ai/artifact/W5Ph6nviNzJVJfSHhqr6Ga. Pick-page task only: nothing in `index.html`, `desktop/` or `native/` was changed. Files: `tools/design-lab/th2/` (`themes_src.py` the versions as drawn, `check.py` fit and measure with `--gate`, `themes.json` and `report.md` results, `page.src.html`, `build.py`, `pick-page.html` the page, `shoot.py` headless renders for review).

The user (28 Nov, 15:05 Brussels): "Theme picks: A B C D E G H J | default: A | icons follow theme: yes. Let's rework these themes that I gave you in Fable and then come back to me." Dropped themes (B2 night, F, I, K, L, M, N) are not shown. Picks line to paste, for example: `Theme round 2 picks: A1 B1 C1 D1 E1 G2 H1 J1 | default A1` (the page's bar builds it; that example is the recommended set).

### What round 2 is

- **Two versions per theme** (A1/A2 ... J1/J2), each shown as the whole app (arrangement with clips and lanes, the glass mixer, devices with their displays, a context menu, an export dialog, a tooltip, meters), with the theme's app icon, and as the thumbnail the Theme row in Settings would show (168 x 96).
- **A0** is today's app, locked and unchanged, kept as the baseline to compare against and still pickable. **A1** repairs today's misses without changing what the user knows; **A2** adds the icons' navy.
- **Two versions carry a second appearance** for following the system setting: E2 (dark) with E2L Whiteprint (light), J2 (light) with J2D Photostat (dark). "B2" in round 2 means version 2 of Chart paper, not the dropped night theme.
- **Tokens only**: colours, hairlines, grid, type accents, glass tint. The style tokens a theme may set besides colours: `caps` (section labels in tracked capitals), `fNum` (numeral face), `fTitle` (title face), `dash` (minor lines dashed), `edgeW` (clip outline width), `clipHead` (strength of the clip title band), `gridMinor` (strength of the minor grid). No decoration.
- **New colour tokens**: `accentFill` (filled buttons, separate from the line colour `accent`), `okS` (play and "on" green on panels), `selFill` (the selection's fill; a yellow highlighter in the paper themes so yellow still means selected), `tip`, `tipInk`, `tipEdge` (tooltips).
- **Type accents need two more faces in the app**: IBM Plex Mono (C1, C2 read-outs) and Source Serif 4 (B1, J1 titles). Body text stays Inter.
- **Glass**: the glass engine draws all glass; a theme sets only the tint and its strength, never below the measured floor; no `backdrop-filter` anywhere (the page itself uses none either). In round 2 quiet text may rise a little before the glass thickens, so most dark versions sit at 60 to 70 % instead of round 1's 78 to 85 %.
- The page also has: a compare wipe between any two colour sets, Dark and Light for E2 and J2, the three colour-vision simulations, glass at the version's tint / today's 50 % / solid, a 100 % size switch, moving meters that hold still under reduced motion (the system setting is read live; a theme itself adds no motion).

### Rules (round 1's twenty plus seven)

Round 1's rules are imported unchanged from `tools/design-lab/th1/check.py`, with two widenings: **T7** text on filled buttons is measured on `accentFill`; **U8** clip edges must keep 3 : 1 on the selected lane too. New: **U1b** filled buttons 3 : 1 against their panel; **U6s** play and "on" green 3 : 1 on panels (round 1 measured green only inside displays; it was too pale on paper); **T11** clip titles 4.5 : 1 and Lc 60 on the title band of every clip on all three lanes (today's app: Lc 43.7); **T12** tooltip text 7 : 1 and Lc 75; **U10** tooltip outline 3 : 1; **H1** main text in a dark theme is never pure white (OKLCH L at most 0.985); **G1** glass tint at or above the floor. 27 rules and 144 measured pairs per dark version (26 and 143 for light ones), plus the meaning-colour distances and the track colours under four visions. `python3 tools/design-lab/th2/check.py --gate` passes for all 18 fitted colour sets; A0 keeps today's misses (19 of 27: the five of round 1 plus the clip titles, the tooltip outline and the glass floor, which round 1 did not measure as rules).

### Numbers

| Version | Mode | Rules passed | Pairs | Main text (worst) | Quiet text (worst) | Clip titles (worst) | Clip edge (worst) | Track ΔE N / P / D / T | Glass floor | Glass |
|---|---|---|---|---|---|---|---|---|---|---|
| A0 Orbit night, today | dark | 19 of 27 (today's misses, kept) | 144 | 9.2 : 1, Lc -86.9 | 3.2 : 1, Lc -31.8 | 5.8 : 1, Lc 43.7 | 4.32 : 1 | 18.6 / 1.0 / 5.7 / 6.1 | 78 % | 50 % |
| A1 Orbit night, repaired | dark | 27 of 27 | 144 | 11.0 : 1, Lc -90.2 | 4.9 : 1, Lc -45.3 | 4.6 : 1, Lc -76.9 | 3.03 : 1 | 18.1 / 10.1 / 10.0 / 10.0 | 59 % | 60 % |
| A2 Orbit night, field depth | dark | 27 of 27 | 144 | 11.4 : 1, Lc -91.6 | 5.1 : 1, Lc -46.1 | 4.6 : 1, Lc -76.8 | 3.04 : 1 | 11.2 / 10.2 / 10.2 / 10.2 | 52 % | 60 % |
| B1 Chart paper, printed plate | light | 26 of 26 | 143 | 11.0 : 1, Lc 80.4 | 4.7 : 1, Lc 60.8 | 4.6 : 1, Lc -76.0 | 4.34 : 1 | 11.2 / 10.3 / 10.3 / 10.3 | 81 % | 86 % |
| B2 Chart paper, graph sheet | light | 26 of 26 | 143 | 11.8 : 1, Lc 82.5 | 4.9 : 1, Lc 62.9 | 9.3 : 1, Lc 63.6 | 3.02 : 1 | 17.1 / 14.1 / 14.1 / 14.1 | 12 % | 74 % |
| C1 Space Race, mission control | dark | 27 of 27 | 144 | 9.7 : 1, Lc -90.8 | 4.6 : 1, Lc -46.7 | 4.6 : 1, Lc -77.0 | 3.03 : 1 | 14.6 / 12.9 / 12.8 / 12.9 | 34 % | 70 % |
| C2 Space Race, three rings | dark | 27 of 27 | 144 | 12.2 : 1, Lc -92.3 | 5.8 : 1, Lc -49.8 | 4.6 : 1, Lc -76.7 | 3.03 : 1 | 15.2 / 14.1 / 14.2 / 14.1 | 31 % | 65 % |
| D1 Chalkboard, green board | dark | 27 of 27 | 144 | 7.2 : 1, Lc -81.5 | 4.8 : 1, Lc -51.7 | 4.5 : 1, Lc -77.1 | 3.04 : 1 | 18.9 / 12.1 / 12.2 / 12.1 | 61 % | 70 % |
| D2 Chalkboard, science fair | dark | 27 of 27 | 144 | 7.2 : 1, Lc -78.6 | 4.6 : 1, Lc -47.3 | 4.5 : 1, Lc -77.1 | 3.03 : 1 | 13.7 / 13.2 / 12.9 / 12.9 | 68 % | 70 % |
| E1 Blueprint, Prussian blue | dark | 27 of 27 | 144 | 7.4 : 1, Lc -87.2 | 5.4 : 1, Lc -60.4 | 5.0 : 1, Lc -79.6 | 3.03 : 1 | 13.0 / 11.6 / 11.0 / 11.0 | 41 % | 72 % |
| E2 Blueprint, night print | dark | 27 of 27 | 144 | 8.9 : 1, Lc -90.5 | 5.3 : 1, Lc -55.2 | 4.6 : 1, Lc -77.4 | 3.02 : 1 | 18.9 / 17.2 / 17.2 / 17.2 | 50 % | 68 % |
| E2L Blueprint, whiteprint | light | 26 of 26 | 143 | 10.9 : 1, Lc 83.5 | 4.9 : 1, Lc 64.7 | 8.8 : 1, Lc 61.1 | 3.03 : 1 | 12.8 / 12.2 / 12.1 / 12.2 | 0 % | 74 % |
| G1 Cutaway nucleus, machined steel | dark | 27 of 27 | 144 | 11.1 : 1, Lc -92.4 | 5.3 : 1, Lc -49.0 | 4.6 : 1, Lc -76.9 | 3.03 : 1 | 13.2 / 11.6 / 11.5 / 11.5 | 46 % | 68 % |
| G2 Cutaway nucleus, opened core | dark | 27 of 27 | 144 | 11.0 : 1, Lc -92.4 | 5.3 : 1, Lc -49.4 | 4.6 : 1, Lc -77.0 | 3.02 : 1 | 14.9 / 11.1 / 10.8 / 10.7 | 47 % | 68 % |
| H1 Rutherford scattering, gold foil | dark | 27 of 27 | 144 | 12.8 : 1, Lc -92.0 | 5.7 : 1, Lc -47.2 | 4.6 : 1, Lc -77.0 | 4.53 : 1 | 13.5 / 10.6 / 10.7 / 10.6 | 53 % | 70 % |
| H2 Rutherford scattering, scintillation | dark | 27 of 27 | 144 | 12.7 : 1, Lc -91.9 | 5.7 : 1, Lc -47.1 | 4.5 : 1, Lc -77.0 | 4.27 : 1 | 15.4 / 13.4 / 13.4 / 13.5 | 53 % | 70 % |
| J1 Patent drawing, drawing board | light | 26 of 26 | 143 | 14.3 : 1, Lc 92.0 | 5.7 : 1, Lc 71.5 | 8.8 : 1, Lc 61.3 | 3.02 : 1 | 16.1 / 15.7 / 15.8 / 15.7 | 0 % | 72 % |
| J2 Patent drawing, ink only | light | 26 of 26 | 143 | 14.6 : 1, Lc 91.9 | 5.7 : 1, Lc 71.4 | 9.0 : 1, Lc 62.0 | 3.02 : 1 | 17.6 / 16.0 / 15.8 / 16.0 | 0 % | 72 % |
| J2D Patent drawing, photostat | dark | 27 of 27 | 144 | 13.1 : 1, Lc -92.6 | 6.1 : 1, Lc -48.7 | 4.6 : 1, Lc -77.2 | 3.77 : 1 | 19.3 / 17.5 / 17.5 / 17.4 | 23 % | 68 % |


Every fitted set: track colours at 10.0 or more under normal, protan, deutan and tritan vision (today 1.0 under protan); every clip edge at 3 : 1 or more on both lanes and the selected lane; quiet text at 4.6 : 1 or more everywhere including glass over the brightest clip.

### Recommendations

★★★★★ (the version to ship per theme): **A1, B1, C1, D1, E1, G2, H1, J1**, default **A1**. ★★★★: A2, B2, C2, D2, E2 (with E2L), G1, H2, J2 (with J2D).

### The versions

#### A0 Orbit night, today (dark) (baseline)

Today's app, untouched: the locked baseline with its five known misses. Kept here to compare against and still pickable. Icons that follow it: `dipole-field`, `field-depth`.

Tokens: bg `#101214`, chrome `#17191C`, ruler `#272B30`, lane0 `#1E2125`, lane1 `#202328`, laneSel `#292D33`, panel `#121216`, panel2 `#18181d`, strip `#24272E`, display `#0B0C10`, glass `#1C1C24`, line `#25252c`, ink `#ececf1`, lab `#b7b7c2`, mut `#8b8b97`, dis `#5c5e68`, rulerTxt `#AAB1BB`, inkD `#ececf1`, accent `#4c8dff`, accentFill `#4c8dff`, onAccent `#ffffff`, accentD `#4c8dff`, sel `#f5c84c`, selFill `#f5c84c`, selD `#f5c84c`, unit `#ffb547`, unitD `#ffb547`, rec `#ff4d4d`, over `#ff6b6b`, overD `#ff6b6b`, warn `#f5c84c`, ok `#3ecf8e`, okS `#3ecf8e`, ph `#3ecf8e`, m0 `#12804f`, m1 `#3ecf8e`, m2 `#f5c84c`, m3 `#ff3b3b`, focusIn `#4c8dff`, focusOut `#4c8dff`, tip `#2a2a33`, tipInk `#ececf1`, tipEdge `#6a6c7a`, glass 50 % (floor 78 %), clip body 36 %, grid `255,255,255` × 1.

Style: caps 0, numerals mono, titles ui, dashed minor lines 0, clip outline 1 px, title band 55 %, minor grid × 1.

Track colours: `#4c8dff` `#3ecf8e` `#f5c84c` `#ff6b6b` `#ff9a3c` `#b583ff` `#4cc9f0` `#ff7ac8`. Smallest CIEDE2000: normal 18.6, protan 1.0, deutan 5.7, tritan 6.1.

Worst pairs: main text 9.25 : 1, Lc -86.9; labels 5.48 : 1, Lc -55.1; quiet text 3.23 : 1, Lc -31.8; units 8.51 : 1, Lc -67.5; text on filled buttons 3.20 : 1, Lc -64.2; clip titles 5.79 : 1, Lc 43.7; clip edge 4.32 : 1; accent 4.67 : 1; selection 8.73 : 1; record 5.39 : 1; playhead 7.14 : 1. Rules passed: 19 of 27 (kept misses: T2, T3, T4, T5, T7, U10, T11, G1). Meaning colours apart: accent/sel 61.2, sel/over 42.4, sel/rec 44.4, accent/rec 45.6, accent/ok 48.4, ph/sel 35.2, ph/rec 73.2.

#### A1 Orbit night, repaired (dark) ★★★★★

The app you know with its five misses closed. Surfaces, the blue, the yellow selection and the amber units are today's to the digit; only the faint greys rise a step and filled buttons take a slightly deeper blue so their white text reads. Icons that follow it: `dipole-field`, `field-depth`.

Changed from round 1: Quiet grey, disabled grey and ruler numbers one step lighter (lightness only). Filled buttons get their own deeper blue (new token accentFill), white text stays; lines and arcs keep #4c8dff. Track colours nudged apart for red-green colour vision (hue within 16 degrees); the clip title band is a little thinner so titles read. Glass tint at the measured floor, two-colour focus ring.

Tokens: bg `#101214`, chrome `#17191C`, ruler `#272B30`, lane0 `#1E2125`, lane1 `#202328`, laneSel `#292D33`, panel `#121216`, panel2 `#18181d`, strip `#24272E`, display `#0B0C10`, glass `#1A1A22`, line `#25252c`, ink `#ececf1`, lab `#BABAC5`, mut `#9F9FAB`, dis `#7B7D88`, rulerTxt `#B4BAC4`, inkD `#ececf1`, accent `#4c8dff`, accentFill `#2f6fe6`, onAccent `#ffffff`, accentD `#4c8dff`, sel `#f5c84c`, selFill `#f5c84c`, selD `#f5c84c`, unit `#ffb547`, unitD `#ffb547`, rec `#ff4d4d`, over `#ff6b6b`, overD `#ff6b6b`, warn `#f5c84c`, ok `#3ecf8e`, okS `#3ecf8e`, ph `#3ecf8e`, m0 `#12804f`, m1 `#3ecf8e`, m2 `#f5c84c`, m3 `#ff3b3b`, focusIn `#4c8dff`, focusOut `#0B0C10`, tip `#2a2a33`, tipInk `#ececf1`, tipEdge `#737583`, glass 60 % (floor 59 %), clip body 36 %, grid `255,255,255` × 1.

Style: caps 0, numerals mono, titles ui, dashed minor lines 0, clip outline 1 px, title band 30 %, minor grid × 1.

Track colours: `#4874C7` `#45AB88` `#CDB107` `#E44165` `#CA8A48` `#A17FFE` `#20C3E5` `#FE73C4`. Smallest CIEDE2000: normal 18.1, protan 10.1, deutan 10.0, tritan 10.0.

Worst pairs: main text 10.96 : 1, Lc -90.2; labels 6.71 : 1, Lc -60.1; quiet text 4.93 : 1, Lc -45.3; units 8.51 : 1, Lc -67.5; text on filled buttons 4.63 : 1, Lc -77.1; clip titles 4.57 : 1, Lc -76.9; clip edge 3.03 : 1; accent 4.67 : 1; selection 8.73 : 1; record 5.39 : 1; playhead 7.14 : 1. Rules passed: 27 of 27. Meaning colours apart: accent/sel 61.2, sel/over 42.4, sel/rec 44.4, accent/rec 45.6, accent/ok 48.4, ph/sel 35.2, ph/rec 73.2.

Readability fit: smallest CIEDE2000 over four visions 1.0 -> 10.0 (limits: lightness 0.09, chroma 0.045, hue 16 degrees); lab #b7b7c2 → #BABAC5; mut #9a9aa6 → #9F9FAB; dis #6e707b → #7B7D88; tipEdge #6a6c7a → #737583.

#### A2 Orbit night, field depth (dark) ★★★★

Orbit night with the navy of its own icons: the charcoal takes a little more blue and depth, the grid turns field-line blue. Same blue, same yellow, same layout of light and dark. Icons that follow it: `field-depth`, `dipole-field`.

Changed from round 1: Surfaces move from grey-blue charcoal toward the icons' navy (about 8 degrees of hue, more chroma). Grid lines tinted like the dipole field lines. All of A1's repairs.

Tokens: bg `#0A0E16`, chrome `#101620`, ruler `#1D2532`, lane0 `#161C27`, lane1 `#19202B`, laneSel `#222C3C`, panel `#0E121A`, panel2 `#151A24`, strip `#1F2633`, display `#07090E`, glass `#161B27`, line `#242C3A`, ink `#ECEEF3`, lab `#B9BFCC`, mut `#9AA1B1`, dis `#767D8E`, rulerTxt `#B2BBCA`, inkD `#ECEEF3`, accent `#4c8dff`, accentFill `#2f6fe6`, onAccent `#ffffff`, accentD `#4c8dff`, sel `#f5c84c`, selFill `#f5c84c`, selD `#f5c84c`, unit `#ffb547`, unitD `#ffb547`, rec `#ff4d4d`, over `#ff6b6b`, overD `#ff6b6b`, warn `#f5c84c`, ok `#3ecf8e`, okS `#3ecf8e`, ph `#3ecf8e`, m0 `#12804f`, m1 `#3ecf8e`, m2 `#f5c84c`, m3 `#ff3b3b`, focusIn `#4c8dff`, focusOut `#07090E`, tip `#283040`, tipInk `#ECEEF3`, tipEdge `#6B768B`, glass 60 % (floor 52 %), clip body 36 %, grid `170,195,240` × 1.05.

Style: caps 0, numerals mono, titles ui, dashed minor lines 0, clip outline 1 px, title band 30 %, minor grid × 1.

Track colours: `#666AD0` `#7CBC75` `#F5A620` `#E13673` `#DD7927` `#8E81FE` `#17C3F4` `#FD78C7`. Smallest CIEDE2000: normal 11.2, protan 10.2, deutan 10.2, tritan 10.2.

Worst pairs: main text 11.37 : 1, Lc -91.6; labels 7.16 : 1, Lc -62.8; quiet text 5.09 : 1, Lc -46.1; units 8.64 : 1, Lc -67.7; text on filled buttons 4.63 : 1, Lc -77.1; clip titles 4.57 : 1, Lc -76.8; clip edge 3.04 : 1; accent 4.74 : 1; selection 8.87 : 1; record 5.55 : 1; playhead 7.72 : 1. Rules passed: 27 of 27. Meaning colours apart: accent/sel 61.2, sel/over 42.4, sel/rec 44.4, accent/rec 45.6, accent/ok 48.4, ph/sel 35.2, ph/rec 73.2.

Readability fit: smallest CIEDE2000 over four visions 1.0 -> 10.2 (limits: lightness 0.10, chroma 0.050, hue 18 degrees); dis #6C7383 → #767D8E; tipEdge #687388 → #6B768B.

#### B1 Chart paper, printed plate (light) ★★★★★

A lithographed plate: warm chart paper, navy ink, clips printed as flat colour. The nucleus orange is the playhead, the electron blue the accent, titles set in a book serif. Icons that follow it: `dipole-field-paper`, `measured-field-paper`, `field-dial-paper`.

Changed from round 1: Selection is a yellow highlighter fill inside an ochre line, so yellow still means selected on paper. Play and "on" greens get a darker ink for paper (new token okS). Sepia hairlines, serif titles, clip titles pick ink per clip.

Tokens: bg `#E2D9C6`, chrome `#E9E1D0`, ruler `#EEE7D8`, lane0 `#F7F2E8`, lane1 `#F1EBDE`, laneSel `#FBEDC2`, panel `#FAF6EE`, panel2 `#F0E9DB`, strip `#ECE4D4`, display `#1B2340`, glass `#FAF6EE`, line `#CDC2AB`, ink `#1B2340`, lab `#3A4160`, mut `#575C72`, dis `#9A9685`, rulerTxt `#1B2340`, inkD `#F7F2E8`, accent `#2A62F0`, accentFill `#2A62F0`, onAccent `#FFFFFF`, accentD `#6E9BFF`, sel `#9A6B00`, selFill `#FFD84D`, selD `#F5C84C`, unit `#9E4A00`, unitD `#FFB547`, rec `#CC2B2B`, over `#BF2926`, overD `#FF6B6B`, warn `#F2C84B`, ok `#5AD39A`, okS `#1E8A5A`, ph `#C8610A`, m0 `#2E9E6B`, m1 `#5AD39A`, m2 `#F2C84B`, m3 `#FF5A4F`, focusIn `#2A62F0`, focusOut `#FFFFFF`, tip `#1B2340`, tipInk `#F7F2E8`, tipEdge `#1B2340`, glass 86 % (floor 81 %), clip body 90 %, grid `27,35,64` × 1.15.

Style: caps 0, numerals ui, titles serif, dashed minor lines 0, clip outline 1 px, title band 0 %, minor grid × 1.

Track colours: `#6155D6` `#285B4F` `#983A01` `#CC2964` `#4036AB` `#0D708E` `#7E1660` `#59623D`. Smallest CIEDE2000: normal 11.2, protan 10.3, deutan 10.3, tritan 10.3.

Worst pairs: main text 11.00 : 1, Lc 80.4; labels 7.39 : 1, Lc 73.6; quiet text 4.71 : 1, Lc 60.8; units 4.70 : 1, Lc 62.6; text on filled buttons 5.12 : 1, Lc -79.9; clip titles 4.57 : 1, Lc -76.0; clip edge 4.34 : 1; accent 3.65 : 1; selection 3.71 : 1; record 4.09 : 1; playhead 3.30 : 1. Rules passed: 26 of 26. Meaning colours apart: accent/sel 58.1, sel/over 30.6, sel/rec 31.3, accent/rec 44.4, accent/ok 54.6, ph/sel 15.3, ph/rec 19.3.

Readability fit: smallest CIEDE2000 over four visions 1.3 -> 10.3 (limits: lightness 0.09, chroma 0.030, hue 16 degrees).

#### B2 Chart paper, graph sheet (light) ★★★★

The measured-field sheet: cooler paper with a green graph ruling you can count on, clips drawn as ink outlines over a light wash, numerals in a fixed-width face. Icons that follow it: `measured-field-paper`, `dipole-field-paper`, `field-dial-paper`.

Changed from round 1: The drafting grid becomes visible graph paper (green ruling, stronger minor lines). Clips are line work over a wash instead of flat colour, so the grid shows through. Fixed-width numerals, capital section labels.

Tokens: bg `#DEDDCC`, chrome `#E6E5D6`, ruler `#ECEBDE`, lane0 `#F7F6EC`, lane1 `#F1F0E4`, laneSel `#FBEEC0`, panel `#FAF9F1`, panel2 `#EEEDDF`, strip `#E9E8D9`, display `#17203A`, glass `#F9F8F0`, line `#C3C5AE`, ink `#17203A`, lab `#384058`, mut `#555B6C`, dis `#96977F`, rulerTxt `#17203A`, inkD `#F7F6EC`, accent `#2A62F0`, accentFill `#2A62F0`, onAccent `#FFFFFF`, accentD `#6E9BFF`, sel `#946800`, selFill `#FFD84D`, selD `#F5C84C`, unit `#9A4A00`, unitD `#FFB547`, rec `#C92A2A`, over `#BC2724`, overD `#FF6B6B`, warn `#F2C84B`, ok `#5AD39A`, okS `#1B8456`, ph `#C8610A`, m0 `#2E9E6B`, m1 `#5AD39A`, m2 `#F2C84B`, m3 `#FF5A4F`, focusIn `#2A62F0`, focusOut `#FFFFFF`, tip `#17203A`, tipInk `#F7F6EC`, tipEdge `#17203A`, glass 74 % (floor 12 %), clip body 20 %, grid `38,112,92` × 1.7.

Style: caps 1, numerals mono, titles ui, dashed minor lines 0, clip outline 1.5 px, title band 12 %, minor grid × 1.8.

Track colours: `#706EEB` `#199584` `#CB7146` `#BC3251` `#5B10C4` `#0D6A7C` `#722D4E` `#445606`. Smallest CIEDE2000: normal 17.1, protan 14.1, deutan 14.1, tritan 14.1.

Worst pairs: main text 11.75 : 1, Lc 82.5; labels 8.10 : 1, Lc 78.0; quiet text 4.94 : 1, Lc 62.9; units 4.93 : 1, Lc 64.8; text on filled buttons 5.12 : 1, Lc -79.9; clip titles 9.27 : 1, Lc 63.6; clip edge 3.02 : 1; accent 3.73 : 1; selection 4.01 : 1; record 4.30 : 1; playhead 3.39 : 1. Rules passed: 26 of 26. Meaning colours apart: accent/sel 58.0, sel/over 30.6, sel/rec 31.4, accent/rec 44.3, accent/ok 54.6, ph/sel 16.3, ph/rec 19.5.

Readability fit: smallest CIEDE2000 over four visions 2.5 -> 14.1 (limits: lightness 0.10, chroma 0.050, hue 18 degrees).

#### C1 Space Race, mission control (dark) ★★★★★

The control room: night-navy consoles under a band of agency blue for the top bar and transport, white lettering, caution yellow for selection, red for record alone. Read-outs in a console typeface. Icons that follow it: `space-race`, `three-rings`.

Changed from round 1: Buttons that are on are console-blue lamps with dark lettering; clips glow through like today's instead of solid blocks. The blue band is the true #0B3D91 family; record red lifted to stay 3 : 1 on it. IBM Plex Mono numerals and capital labels, like console legends.

Tokens: bg `#060C1A`, chrome `#0B3A86`, ruler `#0C1830`, lane0 `#0B152B`, lane1 `#0D1830`, laneSel `#16254A`, panel `#0A142A`, panel2 `#111E3E`, strip `#101C38`, display `#030712`, glass `#0D1936`, line `#21325A`, ink `#F1F4F9`, lab `#C6D0E2`, mut `#9CABC8`, dis `#6F7B95`, rulerTxt `#C6D0E2`, inkD `#F1F4F9`, accent `#8DB8FF`, accentFill `#8DB8FF`, onAccent `#060C1A`, accentD `#8DB8FF`, sel `#FFD23A`, selFill `#FFD23A`, selD `#FFD23A`, unit `#FFB547`, unitD `#FFB547`, rec `#FF5A4E`, over `#FF7468`, overD `#FF7468`, warn `#FFD23A`, ok `#3ECF8E`, okS `#3ECF8E`, ph `#F1F4F9`, m0 `#12804f`, m1 `#3ecf8e`, m2 `#FFD23A`, m3 `#ff3b3b`, focusIn `#FFFFFF`, focusOut `#0B3D91`, tip `#F1F4F9`, tipInk `#060C1A`, tipEdge `#F1F4F9`, glass 70 % (floor 34 %), clip body 40 %, grid `160,185,225` × 1.

Style: caps 1, numerals plex, titles ui, dashed minor lines 0, clip outline 1 px, title band 30 %, minor grid × 1.

Track colours: `#4D63EB` `#579885` `#D2B208` `#BA5007` `#D87754` `#9A92FC` `#56BECB` `#AB689D`. Smallest CIEDE2000: normal 14.6, protan 12.9, deutan 12.8, tritan 12.9.

Worst pairs: main text 9.70 : 1, Lc -90.8; labels 6.89 : 1, Lc -67.9; quiet text 4.62 : 1, Lc -46.7; units 6.09 : 1, Lc -61.1; text on filled buttons 9.70 : 1, Lc 64.6; clip titles 4.56 : 1, Lc -77.0; clip edge 3.03 : 1; accent 5.31 : 1; selection 10.40 : 1; record 3.48 : 1; playhead 16.00 : 1. Rules passed: 27 of 27. Meaning colours apart: accent/sel 53.4, sel/over 42.5, sel/rec 45.1, accent/rec 45.5, accent/ok 41.5, ph/sel 32.7, ph/rec 38.9.

Readability fit: smallest CIEDE2000 over four visions 1.4 -> 12.8 (limits: lightness 0.10, chroma 0.050, hue 18 degrees).

#### C2 Space Race, three rings (dark) ★★★★

The hardware instead of the room: graphite and brushed steel from the three-rings icon, steel-grey labels, one cool blue and the nucleus red. Quieter and darker than C1. Icons that follow it: `three-rings`, `space-race`.

Changed from round 1: Graphite surfaces instead of the blue band; steel as the quiet text colour. See-through clips like today's. IBM Plex Mono numerals.

Tokens: bg `#090D14`, chrome `#111722`, ruler `#171E2B`, lane0 `#0F141E`, lane1 `#121823`, laneSel `#1D2738`, panel `#0D121A`, panel2 `#151C28`, strip `#19212E`, display `#05070B`, glass `#131A26`, line `#273040`, ink `#E9EEF5`, lab `#BCC7D8`, mut `#97A7BF`, dis `#717C8F`, rulerTxt `#BCC7D8`, inkD `#E9EEF5`, accent `#7C9EE0`, accentFill `#4568B6`, onAccent `#FFFFFF`, accentD `#7C9EE0`, sel `#F2C94C`, selFill `#F2C94C`, selD `#F2C94C`, unit `#FFB547`, unitD `#FFB547`, rec `#E5544C`, over `#FF7468`, overD `#FF7468`, warn `#F2C94C`, ok `#3ECF8E`, okS `#3ECF8E`, ph `#DCE4F0`, m0 `#12804f`, m1 `#3ecf8e`, m2 `#F2C94C`, m3 `#ff3b3b`, focusIn `#FFFFFF`, focusOut `#090D14`, tip `#2A3446`, tipInk `#E9EEF5`, tipEdge `#6B7A92`, glass 65 % (floor 31 %), clip body 34 %, grid `143,161,187` × 1.1.

Style: caps 0, numerals plex, titles ui, dashed minor lines 0, clip outline 1 px, title band 30 %, minor grid × 1.

Track colours: `#6B739A` `#82B08A` `#EAAC22` `#CE325E` `#B77D1E` `#9973F0` `#05CDF6` `#BC94B1`. Smallest CIEDE2000: normal 15.2, protan 14.1, deutan 14.2, tritan 14.1.

Worst pairs: main text 12.15 : 1, Lc -92.3; labels 8.30 : 1, Lc -68.0; quiet text 5.80 : 1, Lc -49.8; units 9.21 : 1, Lc -68.6; text on filled buttons 5.37 : 1, Lc -81.9; clip titles 4.56 : 1, Lc -76.7; clip edge 3.03 : 1; accent 6.03 : 1; selection 9.46 : 1; record 4.88 : 1; playhead 13.05 : 1. Rules passed: 27 of 27. Meaning colours apart: accent/sel 52.3, sel/over 39.9, sel/rec 44.1, accent/rec 42.1, accent/ok 41.7, ph/sel 35.6, ph/rec 40.9.

Readability fit: smallest CIEDE2000 over four visions 1.3 -> 14.1 (limits: lightness 0.10, chroma 0.050, hue 18 degrees); dis #6B7689 → #717C8F; accentFill #4467B5 → #4568B6.

#### D1 Chalkboard, green board (dark) ★★★★★

The board itself: the slate green of the icon, lighter than round 1, with chalk-white writing. Clips are chalk outlines over a light dusting of their colour, tracks in the pastel chalks of the box. Icons that follow it: `chalkboard`, `science-fair`.

Changed from round 1: The board is the icon's green (#344434 family), not a dark green-black. Clips drawn as chalk outlines (1.5 px line, thin fill), grid like wiped chalk. Quiet text lifted so it reads on the lighter board.

Tokens: bg `#1E2920`, chrome `#243026`, ruler `#2A382C`, lane0 `#2E3D30`, lane1 `#314133`, laneSel `#3D5142`, panel `#263328`, panel2 `#2E3C30`, strip `#2D3B2F`, display `#101611`, glass `#2A372C`, line `#46584A`, ink `#F0ECDF`, lab `#D6D1BE`, mut `#B4B8A5`, dis `#869080`, rulerTxt `#DAD4BC`, inkD `#F0ECDF`, accent `#9FD0F0`, accentFill `#9FD0F0`, onAccent `#15211A`, accentD `#9FD0F0`, sel `#F4D56E`, selFill `#F4D56E`, selD `#F4D56E`, unit `#F2B46A`, unitD `#F2B46A`, rec `#F06A58`, over `#FF8A76`, overD `#FF7A66`, warn `#F2D26B`, ok `#8FDC8A`, okS `#8FDC8A`, ph `#F4F0E4`, m0 `#3E9E63`, m1 `#8FDC8A`, m2 `#F2D26B`, m3 `#FF6A55`, focusIn `#F4F0E4`, focusOut `#101611`, tip `#F0ECDF`, tipInk `#1E2920`, tipEdge `#F0ECDF`, glass 70 % (floor 61 %), clip body 26 %, grid `240,236,220` × 1.05.

Style: caps 0, numerals mono, titles ui, dashed minor lines 0, clip outline 1.5 px, title band 0 %, minor grid × 1.

Track colours: `#7EA2C2` `#D4F8C8` `#FBE749` `#BC8F8D` `#EABB7F` `#E8C2FF` `#29CBB2` `#EBEBEB`. Smallest CIEDE2000: normal 18.9, protan 12.1, deutan 12.2, tritan 12.1.

Worst pairs: main text 7.24 : 1, Lc -81.5; labels 6.37 : 1, Lc -67.5; quiet text 4.80 : 1, Lc -51.7; units 6.47 : 1, Lc -61.5; text on filled buttons 10.09 : 1, Lc 72.7; clip titles 4.55 : 1, Lc -77.1; clip edge 3.04 : 1; accent 7.17 : 1; selection 5.95 : 1; record 4.35 : 1; playhead 9.53 : 1. Rules passed: 27 of 27. Meaning colours apart: accent/sel 43.4, sel/over 35.5, sel/rec 40.3, accent/rec 47.3, accent/ok 37.5, ph/sel 21.1, ph/rec 36.0.

Readability fit: smallest CIEDE2000 over four visions 0.4 -> 12.1 (limits: lightness 0.10, chroma 0.050, hue 18 degrees).

#### D2 Chalkboard, science fair (dark) ★★★★

The science-fair model on its felt board: deep forest green, cream lettering, and the model's own paints: nucleon blue for the accent, nucleon red for record, the gold beads for selection. Icons that follow it: `science-fair`, `chalkboard`.

Changed from round 1: Deeper green with cream ink instead of chalk white. Controls in the nucleon blue, record in the nucleon red, selection in the gold of the electrons. Clips in poster-paint colours.

Tokens: bg `#14211A`, chrome `#1B2C22`, ruler `#203427`, lane0 `#24392D`, lane1 `#273D30`, laneSel `#32503E`, panel `#1A2A20`, panel2 `#223528`, strip `#233629`, display `#0B120E`, glass `#1F3126`, line `#395342`, ink `#EFE6C8`, lab `#D1C6A0`, mut `#B2AB8C`, dis `#7F8570`, rulerTxt `#D1C6A0`, inkD `#EFE6C8`, accent `#8DB8F4`, accentFill `#8DB8F4`, onAccent `#10203A`, accentD `#8DB8F4`, sel `#F0CB5A`, selFill `#F0CB5A`, selD `#F0CB5A`, unit `#F0B062`, unitD `#F0B062`, rec `#E86050`, over `#FF8672`, overD `#FF7A66`, warn `#F0CB5A`, ok `#8FDC8A`, okS `#8FDC8A`, ph `#EFE6C8`, m0 `#3E9E63`, m1 `#8FDC8A`, m2 `#F0CB5A`, m3 `#FF6A55`, focusIn `#EFE6C8`, focusOut `#0B120E`, tip `#EFE6C8`, tipInk `#14211A`, tipEdge `#EFE6C8`, glass 70 % (floor 68 %), clip body 30 %, grid `209,198,160` × 1.05.

Style: caps 0, numerals mono, titles ui, dashed minor lines 0, clip outline 1 px, title band 0 %, minor grid × 1.

Track colours: `#769CB4` `#98AB7F` `#FEDDA1` `#E5793B` `#FBB501` `#AB91FD` `#2AE3F3` `#CBC9BD`. Smallest CIEDE2000: normal 13.7, protan 13.2, deutan 12.9, tritan 12.9.

Worst pairs: main text 7.15 : 1, Lc -78.6; labels 6.23 : 1, Lc -62.9; quiet text 4.61 : 1, Lc -47.3; units 6.80 : 1, Lc -61.1; text on filled buttons 7.98 : 1, Lc 61.4; clip titles 4.55 : 1, Lc -77.1; clip edge 3.03 : 1; accent 6.31 : 1; selection 5.69 : 1; record 4.35 : 1; playhead 9.36 : 1. Rules passed: 27 of 27. Meaning colours apart: accent/sel 48.1, sel/over 35.4, sel/rec 40.9, accent/rec 44.3, accent/ok 45.0, ph/sel 17.4, ph/rec 38.3.

Readability fit: smallest CIEDE2000 over four visions 0.8 -> 12.9 (limits: lightness 0.10, chroma 0.050, hue 18 degrees).

#### E1 Blueprint, Prussian blue (dark) ★★★★★

A real blueprint: the mid Prussian blue of the icon rather than a navy, white line work, the drafting grid drawn in, clips as tracing paper. Labels in drafting capitals. Icons that follow it: `blueprint`, `cutaway-nucleus`.

Changed from round 1: The paper is the icon's blue (#13417A family); round 1 was two steps darker. Grid clearly visible, as on the sheet; clips are thin washes with a white-ish 1.5 px edge. Capital labels with tracking, fixed-width numerals.

Tokens: bg `#0E3263`, chrome `#113A70`, ruler `#134079`, lane0 `#154380`, lane1 `#174785`, laneSel `#1C5296`, panel `#113A70`, panel2 `#164682`, strip `#15437E`, display `#071B3B`, glass `#123D76`, line `#3F6CA8`, ink `#F5F9FF`, lab `#D2E1F5`, mut `#B4CAE8`, dis `#7F9CC6`, rulerTxt `#D2E1F5`, inkD `#F5F9FF`, accent `#E3EEFF`, accentFill `#E3EEFF`, onAccent `#0E3263`, accentD `#E3EEFF`, sel `#FFD84A`, selFill `#FFD84A`, selD `#FFD84A`, unit `#FFC870`, unitD `#FFC870`, rec `#FF6A5E`, over `#FD9289`, overD `#FF7A70`, warn `#FFD54A`, ok `#6BE5A8`, okS `#6BE5A8`, ph `#FFFFFF`, m0 `#2FB37A`, m1 `#5EE0A0`, m2 `#FFD54A`, m3 `#FF5A50`, focusIn `#FFFFFF`, focusOut `#071B3B`, tip `#F5F9FF`, tipInk `#0E3263`, tipEdge `#F5F9FF`, glass 72 % (floor 41 %), clip body 20 %, grid `205,225,255` × 1.6.

Style: caps 1, numerals mono, titles ui, dashed minor lines 0, clip outline 1.5 px, title band 0 %, minor grid × 1.5.

Track colours: `#BACCFF` `#4BBFAA` `#FEEFC8` `#D19379` `#CCB857` `#A19AFC` `#8DFEF9` `#FFB5CC`. Smallest CIEDE2000: normal 13.0, protan 11.6, deutan 11.0, tritan 11.0.

Worst pairs: main text 7.37 : 1, Lc -87.2; labels 6.86 : 1, Lc -74.7; quiet text 5.44 : 1, Lc -60.4; units 6.44 : 1, Lc -67.5; text on filled buttons 10.84 : 1, Lc 87.7; clip titles 4.98 : 1, Lc -79.6; clip edge 3.03 : 1; accent 8.40 : 1; selection 5.63 : 1; record 4.01 : 1; playhead 9.23 : 1. Rules passed: 27 of 27. Meaning colours apart: accent/sel 39.4, sel/over 39.7, sel/rec 44.5, accent/rec 39.4, accent/ok 30.1, ph/sel 28.4, ph/rec 36.5.

Readability fit: smallest CIEDE2000 over four visions 5.2 -> 11.0 (limits: lightness 0.10, chroma 0.050, hue 18 degrees); over #FF8E84 → #FD9289.

#### E2 Blueprint, night print (dark) ★★★★

The blueprint for long nights: a deeper indigo that rests the eyes, the same white lines and grid. Comes with a light half, the whiteprint, for following the system appearance. Pairs with E2L. Icons that follow it: `blueprint`, `cutaway-nucleus`.

Changed from round 1: Round 1's darker blue, cleaned up: more even steps between surfaces, calmer grid. A light partner (Whiteprint: blue lines on white, the copy that replaced blueprints).

Tokens: bg `#081E40`, chrome `#0B264E`, ruler `#0E2B57`, lane0 `#103160`, lane1 `#123566`, laneSel `#1B457E`, panel `#0D2952`, panel2 `#123363`, strip `#12315F`, display `#051430`, glass `#0F2D5A`, line `#2C548F`, ink `#F2F7FF`, lab `#CADBF2`, mut `#A3BCDE`, dis `#6E8BB8`, rulerTxt `#CADBF2`, inkD `#F2F7FF`, accent `#DDEBFF`, accentFill `#DDEBFF`, onAccent `#081E40`, accentD `#DDEBFF`, sel `#FFD54A`, selFill `#FFD54A`, selD `#FFD54A`, unit `#FFC266`, unitD `#FFC266`, rec `#FF5F55`, over `#FF8278`, overD `#FF7A70`, warn `#FFD54A`, ok `#5EE0A0`, okS `#5EE0A0`, ph `#FFFFFF`, m0 `#2FB37A`, m1 `#5EE0A0`, m2 `#FFD54A`, m3 `#FF5A50`, focusIn `#FFFFFF`, focusOut `#051430`, tip `#F2F7FF`, tipInk `#081E40`, tipEdge `#F2F7FF`, glass 68 % (floor 50 %), clip body 28 %, grid `200,220,255` × 1.3.

Style: caps 1, numerals mono, titles ui, dashed minor lines 0, clip outline 1 px, title band 0 %, minor grid × 1.3.

Track colours: `#C7C2FC` `#4FB380` `#FFF8BE` `#DA7819` `#FFCC06` `#8883F8` `#CDFFF7` `#AB8AA5`. Smallest CIEDE2000: normal 18.9, protan 17.2, deutan 17.2, tritan 17.2.

Worst pairs: main text 8.88 : 1, Lc -90.5; labels 7.38 : 1, Lc -73.8; quiet text 5.35 : 1, Lc -55.2; units 8.07 : 1, Lc -70.4; text on filled buttons 13.70 : 1, Lc 90.6; clip titles 4.61 : 1, Lc -77.4; clip edge 3.02 : 1; accent 10.67 : 1; selection 6.76 : 1; record 4.82 : 1; playhead 12.16 : 1. Rules passed: 27 of 27. Meaning colours apart: accent/sel 40.9, sel/over 40.9, sel/rec 44.9, accent/rec 41.6, accent/ok 31.5, ph/sel 28.5, ph/rec 38.0.

Readability fit: smallest CIEDE2000 over four visions 8.6 -> 17.2 (limits: lightness 0.10, chroma 0.050, hue 18 degrees).

#### E2L Blueprint, whiteprint (light) ★★★★

E2's light half: a whiteprint. Cool white sheet, lines and lettering in blueprint-blue ink, the displays kept as blueprint-blue wells. Pairs with E2. Icons that follow it: `blueprint`, `cutaway-nucleus`.

Tokens: bg `#DCE3EE`, chrome `#E5EAF3`, ruler `#ECF0F7`, lane0 `#F8FAFD`, lane1 `#F1F4F9`, laneSel `#FDF1C2`, panel `#FBFCFE`, panel2 `#ECF0F7`, strip `#E7ECF4`, display `#0B2247`, glass `#FAFBFE`, line `#BECADC`, ink `#12295C`, lab `#2C4274`, mut `#4D5F88`, dis `#93A0B8`, rulerTxt `#12295C`, inkD `#F8FAFD`, accent `#1D4FC4`, accentFill `#1D4FC4`, onAccent `#FFFFFF`, accentD `#DDEBFF`, sel `#946800`, selFill `#FFD84D`, selD `#FFD54A`, unit `#9A4A00`, unitD `#FFC266`, rec `#C62828`, over `#B92322`, overD `#FF7A70`, warn `#FFD54A`, ok `#5EE0A0`, okS `#1B8456`, ph `#12295C`, m0 `#2FB37A`, m1 `#5EE0A0`, m2 `#FFD54A`, m3 `#FF5A50`, focusIn `#1D4FC4`, focusOut `#FFFFFF`, tip `#12295C`, tipInk `#F8FAFD`, tipEdge `#12295C`, glass 74 % (floor 0 %), clip body 20 %, grid `27,63,143` × 1.35.

Style: caps 1, numerals mono, titles ui, dashed minor lines 0, clip outline 1.5 px, title band 30 %, minor grid × 1.5.

Track colours: `#606DFF` `#307C54` `#78650E` `#DF3D64` `#BD7D27` `#565AB0` `#1197A3` `#9C4974`. Smallest CIEDE2000: normal 12.8, protan 12.2, deutan 12.1, tritan 12.2.

Worst pairs: main text 10.86 : 1, Lc 83.5; labels 8.13 : 1, Lc 79.9; quiet text 4.92 : 1, Lc 64.7; units 5.19 : 1, Lc 67.9; text on filled buttons 7.08 : 1, Lc -88.8; clip titles 8.79 : 1, Lc 61.1; clip edge 3.03 : 1; accent 5.48 : 1; selection 4.18 : 1; record 4.66 : 1; playhead 12.27 : 1. Rules passed: 26 of 26. Meaning colours apart: accent/sel 56.8, sel/over 30.9, sel/rec 31.3, accent/rec 43.5, accent/ok 61.4, ph/sel 52.2, ph/rec 43.6.

Readability fit: smallest CIEDE2000 over four visions 1.7 -> 12.1 (limits: lightness 0.10, chroma 0.050, hue 18 degrees).

#### G1 Cutaway nucleus, machined steel (dark) ★★★★

The shell of the model: cool slate and brushed silver. Buttons that are on turn silver with dark lettering like engraved caps; red and blue appear only where they mean record and level. Icons that follow it: `cutaway-nucleus`.

Changed from round 1: Steel hairlines one step clearer, surfaces more evenly spaced. Quiet text lifted; glass a little thinner than round 1.

Tokens: bg `#0E131B`, chrome `#141A25`, ruler `#1A2130`, lane0 `#19212F`, lane1 `#1C2433`, laneSel `#293447`, panel `#151B26`, panel2 `#1D2432`, strip `#202838`, display `#07090E`, glass `#1B2231`, line `#313C50`, ink `#EDF1F7`, lab `#C6CFDE`, mut `#9CA8BC`, dis `#747E92`, rulerTxt `#C6CFDE`, inkD `#EDF1F7`, accent `#AEBBCF`, accentFill `#AEBBCF`, onAccent `#0E131B`, accentD `#AEBBCF`, sel `#F5C84C`, selFill `#F5C84C`, selD `#F5C84C`, unit `#FFB547`, unitD `#FFB547`, rec `#E5503F`, over `#FF7468`, overD `#FF6B60`, warn `#F5C84C`, ok `#3ECF8E`, okS `#3ECF8E`, ph `#E6ECF5`, m0 `#12804f`, m1 `#3ecf8e`, m2 `#f5c84c`, m3 `#ff3b3b`, focusIn `#FFFFFF`, focusOut `#0E131B`, tip `#2C3649`, tipInk `#EDF1F7`, tipEdge `#717E95`, glass 68 % (floor 46 %), clip body 40 %, grid `164,178,200` × 1.05.

Style: caps 0, numerals mono, titles ui, dashed minor lines 0, clip outline 1 px, title band 30 %, minor grid × 1.

Track colours: `#6772EE` `#349184` `#C1A80F` `#F18F81` `#D06944` `#949CFA` `#1BB9BF` `#A368A6`. Smallest CIEDE2000: normal 13.2, protan 11.6, deutan 11.5, tritan 11.5.

Worst pairs: main text 11.05 : 1, Lc -92.4; labels 8.15 : 1, Lc -71.4; quiet text 5.32 : 1, Lc -49.0; units 8.41 : 1, Lc -67.3; text on filled buttons 9.59 : 1, Lc 65.7; clip titles 4.58 : 1, Lc -76.9; clip edge 3.03 : 1; accent 7.60 : 1; selection 7.90 : 1; record 4.56 : 1; playhead 13.10 : 1. Rules passed: 27 of 27. Meaning colours apart: accent/sel 37.0, sel/over 39.0, sel/rec 42.1, accent/rec 38.9, accent/ok 31.3, ph/sel 34.0, ph/rec 42.1.

Readability fit: smallest CIEDE2000 over four visions 1.8 -> 11.5 (limits: lightness 0.10, chroma 0.050, hue 18 degrees); dis #737D90 → #747E92; tipEdge #6E7B92 → #717E95.

#### G2 Cutaway nucleus, opened core (dark) ★★★★★

The cut itself: the same slate shell, but controls take the proton blue of the core (the icon's #2D62A8, lifted one step to stand off the panels) and record the neutron red. Silver stays for lines and quiet text. Icons that follow it: `cutaway-nucleus`.

Changed from round 1: Accent is the icon's blue: light blue for lines and arcs, a deeper blue for filled buttons with white text. Slightly warmer, lighter shell so the blue and red read as the inside.

Tokens: bg `#10141B`, chrome `#171C26`, ruler `#1D2330`, lane0 `#1B212D`, lane1 `#1E2531`, laneSel `#2A3447`, panel `#181D27`, panel2 `#202633`, strip `#242B39`, display `#07090E`, glass `#1E2431`, line `#343D4F`, ink `#EEF1F6`, lab `#C8CFDC`, mut `#9FA9BB`, dis `#767F92`, rulerTxt `#C8CFDC`, inkD `#EEF1F6`, accent `#86AEF0`, accentFill `#4075BD`, onAccent `#FFFFFF`, accentD `#86AEF0`, sel `#F5C84C`, selFill `#F5C84C`, selD `#F5C84C`, unit `#FFB547`, unitD `#FFB547`, rec `#E5503F`, over `#FF7468`, overD `#FF6B60`, warn `#F5C84C`, ok `#3ECF8E`, okS `#3ECF8E`, ph `#E6ECF5`, m0 `#12804f`, m1 `#3ecf8e`, m2 `#f5c84c`, m3 `#ff3b3b`, focusIn `#FFFFFF`, focusOut `#10141B`, tip `#2E3748`, tipInk `#EEF1F6`, tipEdge `#727E93`, glass 68 % (floor 47 %), clip body 40 %, grid `174,186,206` × 1.05.

Style: caps 0, numerals mono, titles ui, dashed minor lines 0, clip outline 1 px, title band 30 %, minor grid × 1.

Track colours: `#818BFF` `#529068` `#C9A50A` `#FC829A` `#BE7831` `#8B6FBA` `#24B6D3` `#B980A7`. Smallest CIEDE2000: normal 14.9, protan 11.1, deutan 10.8, tritan 10.7.

Worst pairs: main text 11.04 : 1, Lc -92.4; labels 8.05 : 1, Lc -71.3; quiet text 5.32 : 1, Lc -49.4; units 8.08 : 1, Lc -66.8; text on filled buttons 4.67 : 1, Lc -77.6; clip titles 4.59 : 1, Lc -77.0; clip edge 3.02 : 1; accent 6.30 : 1; selection 7.88 : 1; record 4.46 : 1; playhead 12.96 : 1. Rules passed: 27 of 27. Meaning colours apart: accent/sel 50.7, sel/over 39.0, sel/rec 42.1, accent/rec 45.3, accent/ok 40.9, ph/sel 34.0, ph/rec 42.1.

Readability fit: smallest CIEDE2000 over four visions 2.2 -> 10.7 (limits: lightness 0.10, chroma 0.050, hue 18 degrees); dis #757E90 → #767F92; tipEdge #6F7B90 → #727E93; accentFill #2D62A8 → #4075BD.

#### H1 Rutherford scattering, gold foil (dark) ★★★★★

The experiment in the dark: near-black, the alpha tracks' gold for the accent, the ruler and a faint gold grid, ivory text. Selection is the blue-white flash of the scintillation screen, because gold is taken. Icons that follow it: `rutherford-scattering`.

Changed from round 1: Gold grid traces a little finer; ivory text one step calmer than white. Quiet text lifted; disabled text now passes.

Tokens: bg `#07090F`, chrome `#0B0E16`, ruler `#10141D`, lane0 `#0F131C`, lane1 `#121620`, laneSel `#13232A`, panel `#0D1018`, panel2 `#141822`, strip `#151924`, display `#030406`, glass `#11151E`, line `#272B35`, ink `#F1EBDD`, lab `#CFC5AE`, mut `#A99E85`, dis `#817A69`, rulerTxt `#E9B751`, inkD `#F1EBDD`, accent `#E9B751`, accentFill `#E9B751`, onAccent `#07090F`, accentD `#E9B751`, sel `#66D9F5`, selFill `#66D9F5`, selD `#66D9F5`, unit `#F2A65A`, unitD `#F2A65A`, rec `#FF4D4D`, over `#FF6B6B`, overD `#FF6B6B`, warn `#F5C84C`, ok `#3ECF8E`, okS `#3ECF8E`, ph `#F1EBDD`, m0 `#1F8A5A`, m1 `#3ECF8E`, m2 `#F5C84C`, m3 `#FF3B3B`, focusIn `#66D9F5`, focusOut `#07090F`, tip `#262A34`, tipInk `#F1EBDD`, tipEdge `#7A735F`, glass 70 % (floor 53 %), clip body 36 %, grid `233,183,81` × 0.85.

Style: caps 0, numerals mono, titles ui, dashed minor lines 0, clip outline 1 px, title band 30 %, minor grid × 1.

Track colours: `#E1A73F` `#0CCBFE` `#21AB7C` `#FD4F68` `#9181FC` `#BB7A04` `#8DC1AA` `#B973B4`. Smallest CIEDE2000: normal 13.5, protan 10.6, deutan 10.7, tritan 10.6.

Worst pairs: main text 12.81 : 1, Lc -92.0; labels 8.88 : 1, Lc -68.8; quiet text 5.74 : 1, Lc -47.2; units 8.67 : 1, Lc -62.0; text on filled buttons 10.76 : 1, Lc 69.1; clip titles 4.61 : 1, Lc -77.0; clip edge 4.53 : 1; accent 9.49 : 1; selection 9.84 : 1; record 5.81 : 1; playhead 15.21 : 1. Rules passed: 27 of 27. Meaning colours apart: accent/sel 44.2, sel/over 64.9, sel/rec 68.4, accent/rec 38.9, accent/ok 36.2, ph/sel 26.9, ph/rec 38.8.

Readability fit: smallest CIEDE2000 over four visions 3.9 -> 10.6 (limits: lightness 0.10, chroma 0.050, hue 18 degrees); dis #7E7766 → #817A69.

#### H2 Rutherford scattering, scintillation (dark) ★★★★

The same dark room with the roles turned: gold is the selection, as yellow is in every other theme, and the controls take the cool glow of the zinc-sulphide screen. Ivory ruler, gold grid traces. Icons that follow it: `rutherford-scattering`.

Changed from round 1: Selection stays in the yellow family (gold), so nothing has to be relearned when switching themes. Accent is the screen's blue-green instead of gold.

Tokens: bg `#07090F`, chrome `#0B0E16`, ruler `#10141D`, lane0 `#0F131C`, lane1 `#121620`, laneSel `#241F12`, panel `#0D1018`, panel2 `#141822`, strip `#151924`, display `#030406`, glass `#11151E`, line `#272B35`, ink `#F1EBDD`, lab `#CFC5AE`, mut `#A99E85`, dis `#817A69`, rulerTxt `#D8CDB4`, inkD `#F1EBDD`, accent `#7FD8E6`, accentFill `#7FD8E6`, onAccent `#07090F`, accentD `#7FD8E6`, sel `#F0BE4A`, selFill `#F0BE4A`, selD `#F0BE4A`, unit `#F29A62`, unitD `#F29A62`, rec `#FF4D4D`, over `#FF6B6B`, overD `#FF6B6B`, warn `#F5C84C`, ok `#3ECF8E`, okS `#3ECF8E`, ph `#F1EBDD`, m0 `#1F8A5A`, m1 `#3ECF8E`, m2 `#F5C84C`, m3 `#FF3B3B`, focusIn `#7FD8E6`, focusOut `#07090F`, tip `#262A34`, tipInk `#F1EBDD`, tipEdge `#7A735F`, glass 70 % (floor 53 %), clip body 36 %, grid `233,183,81` × 0.85.

Style: caps 0, numerals mono, titles ui, dashed minor lines 0, clip outline 1 px, title band 30 %, minor grid × 1.

Track colours: `#BEBDB7` `#6B93B6` `#93C385` `#F03F34` `#906BFE` `#FAA321` `#1CD3DE` `#C36B83`. Smallest CIEDE2000: normal 15.4, protan 13.4, deutan 13.4, tritan 13.5.

Worst pairs: main text 12.72 : 1, Lc -91.9; labels 8.82 : 1, Lc -68.7; quiet text 5.70 : 1, Lc -47.1; units 8.00 : 1, Lc -58.0; text on filled buttons 12.20 : 1, Lc 75.6; clip titles 4.54 : 1, Lc -77.0; clip edge 4.27 : 1; accent 10.75 : 1; selection 9.51 : 1; record 5.81 : 1; playhead 15.21 : 1. Rules passed: 27 of 27. Meaning colours apart: accent/sel 40.7, sel/over 39.7, sel/rec 41.4, accent/rec 66.0, accent/ok 25.7, ph/sel 23.4, ph/rec 38.8.

Readability fit: smallest CIEDE2000 over four visions 3.9 -> 13.4 (limits: lightness 0.10, chroma 0.050, hue 18 degrees); dis #7E7766 → #817A69.

#### J1 Patent drawing, drawing board (light) ★★★★★

The sheet as filed: a warm white board, black ink, one blue pencil for the controls. Clips are ink outlines over the faintest wash, minor grid lines are dashed like the icon's orbits, titles in an italic book face like figure captions. Icons that follow it: `patent-drawing`.

Changed from round 1: Clips become line drawings (1.5 px ink outline, thin wash) instead of dark blocks: the page stays white. Dashed minor lines, serif italic titles. Selection is a yellow highlighter fill inside an ochre line.

Tokens: bg `#ECEBE6`, chrome `#F3F2EE`, ruler `#F7F6F2`, lane0 `#FDFCF9`, lane1 `#F8F7F3`, laneSel `#FFF6CF`, panel `#FFFFFF`, panel2 `#F3F2EE`, strip `#EFEEE9`, display `#1E1E1D`, glass `#FFFFFF`, line `#CBC9C2`, ink `#1C1C1B`, lab `#3A3A38`, mut `#5C5B57`, dis `#A09F99`, rulerTxt `#1C1C1B`, inkD `#FDFCF9`, accent `#1F4FB8`, accentFill `#1F4FB8`, onAccent `#FFFFFF`, accentD `#7FA6F5`, sel `#8F6500`, selFill `#FFE27A`, selD `#F2C84B`, unit `#964800`, unitD `#FFB547`, rec `#C62828`, over `#B71C1C`, overD `#FF6B6B`, warn `#F2C84B`, ok `#6FD08F`, okS `#1F7A4D`, ph `#1F4FB8`, m0 `#2E9E5E`, m1 `#6FD08F`, m2 `#F2C84B`, m3 `#FF5A45`, focusIn `#1F4FB8`, focusOut `#FFFFFF`, tip `#1C1C1B`, tipInk `#FDFCF9`, tipEdge `#1C1C1B`, glass 72 % (floor 0 %), clip body 14 %, grid `40,40,38` × 1.35.

Style: caps 0, numerals ui, titles serifItalic, dashed minor lines 1, clip outline 1.5 px, title band 22 %, minor grid × 1.4.

Track colours: `#6957FC` `#738E71` `#7E5F02` `#81062B` `#BC8312` `#4B2FAB` `#2F7570` `#55284D`. Smallest CIEDE2000: normal 16.1, protan 15.7, deutan 15.8, tritan 15.7.

Worst pairs: main text 14.29 : 1, Lc 92.0; labels 9.81 : 1, Lc 86.1; quiet text 5.69 : 1, Lc 71.5; units 5.61 : 1, Lc 71.5; text on filled buttons 7.32 : 1, Lc -89.7; clip titles 8.83 : 1, Lc 61.3; clip edge 3.02 : 1; accent 6.13 : 1; selection 4.49 : 1; record 5.02 : 1; playhead 6.77 : 1. Rules passed: 26 of 26. Meaning colours apart: accent/sel 55.2, sel/over 30.7, sel/rec 31.2, accent/rec 43.3, accent/ok 60.1, ph/sel 55.2, ph/rec 43.3.

Readability fit: smallest CIEDE2000 over four visions 3.6 -> 15.7 (limits: lightness 0.10, chroma 0.050, hue 18 degrees).

#### J2 Patent drawing, ink only (light) ★★★★

Technical pen and nothing else: a cooler white, solid hairlines, and black as the accent, so buttons that are on are simply inked in. Blue is kept for the playhead and the focus ring. Comes with a dark half, the photostat. Pairs with J2D. Icons that follow it: `patent-drawing`.

Changed from round 1: Accent is the ink itself: on-buttons are black with white lettering. Solid lines and sans titles: stricter than J1. A dark partner (Photostat: the white-on-black copy of the same sheet).

Tokens: bg `#E9EAEB`, chrome `#F1F2F3`, ruler `#F6F7F8`, lane0 `#FDFDFD`, lane1 `#F6F7F8`, laneSel `#FFF6CF`, panel `#FFFFFF`, panel2 `#F1F2F3`, strip `#ECEDEF`, display `#1A1B1C`, glass `#FFFFFF`, line `#C6C8CB`, ink `#18191B`, lab `#36383B`, mut `#585A5E`, dis `#9C9EA2`, rulerTxt `#18191B`, inkD `#FDFDFD`, accent `#18191B`, accentFill `#18191B`, onAccent `#FFFFFF`, accentD `#F1F2F3`, sel `#8F6500`, selFill `#FFE27A`, selD `#F2C84B`, unit `#964800`, unitD `#FFB547`, rec `#C62828`, over `#B71C1C`, overD `#FF6B6B`, warn `#F2C84B`, ok `#6FD08F`, okS `#1F7A4D`, ph `#1F4FB8`, m0 `#2E9E5E`, m1 `#6FD08F`, m2 `#F2C84B`, m3 `#FF5A45`, focusIn `#1F4FB8`, focusOut `#FFFFFF`, tip `#18191B`, tipInk `#FDFDFD`, tipEdge `#18191B`, glass 72 % (floor 0 %), clip body 14 %, grid `30,32,36` × 1.35.

Style: caps 0, numerals mono, titles ui, dashed minor lines 0, clip outline 1.5 px, title band 22 %, minor grid × 1.2.

Track colours: `#4863FF` `#139C7A` `#91613E` `#7A1302` `#D47614` `#4E2DA9` `#586C71` `#56274A`. Smallest CIEDE2000: normal 17.6, protan 16.0, deutan 15.8, tritan 16.0.

Worst pairs: main text 14.60 : 1, Lc 91.9; labels 10.04 : 1, Lc 86.3; quiet text 5.74 : 1, Lc 71.4; units 5.56 : 1, Lc 71.0; text on filled buttons 17.59 : 1, Lc -106.7; clip titles 8.96 : 1, Lc 62.0; clip edge 3.02 : 1; accent 14.60 : 1; selection 4.45 : 1; record 5.02 : 1; playhead 6.82 : 1. Rules passed: 26 of 26. Meaning colours apart: accent/sel 38.1, sel/over 30.7, sel/rec 31.2, accent/rec 38.7, accent/ok 66.8, ph/sel 55.2, ph/rec 43.3.

Readability fit: smallest CIEDE2000 over four visions 3.6 -> 15.8 (limits: lightness 0.10, chroma 0.050, hue 18 degrees).

#### J2D Patent drawing, photostat (dark) ★★★★

J2's dark half: the photostat negative. Neutral black sheet, white line work, the same single blue for playhead and focus. Pairs with J2. Icons that follow it: `patent-drawing`.

Tokens: bg `#0A0A0B`, chrome `#121213`, ruler `#19191B`, lane0 `#141415`, lane1 `#171719`, laneSel `#27241A`, panel `#101011`, panel2 `#18181A`, strip `#1D1D20`, display `#050506`, glass `#17171A`, line `#2D2D31`, ink `#EDECE7`, lab `#C6C5BF`, mut `#A2A19B`, dis `#7C7B79`, rulerTxt `#C6C5BF`, inkD `#EDECE7`, accent `#EDECE7`, accentFill `#EDECE7`, onAccent `#0A0A0B`, accentD `#EDECE7`, sel `#F2CE5A`, selFill `#F2CE5A`, selD `#F2CE5A`, unit `#FFB547`, unitD `#FFB547`, rec `#FF5A50`, over `#FF7468`, overD `#FF6B6B`, warn `#F2C84B`, ok `#6FD08F`, okS `#6FD08F`, ph `#7FA6F5`, m0 `#2E9E5E`, m1 `#6FD08F`, m2 `#F2C84B`, m3 `#FF5A45`, focusIn `#7FA6F5`, focusOut `#0A0A0B`, tip `#2B2B2F`, tipInk `#EDECE7`, tipEdge `#727170`, glass 68 % (floor 23 %), clip body 20 %, grid `235,235,230` × 1.05.

Style: caps 0, numerals mono, titles ui, dashed minor lines 0, clip outline 1.5 px, title band 30 %, minor grid × 1.2.

Track colours: `#7B6BE7` `#55A477` `#E6DFB4` `#E2461A` `#FFB918` `#B4ACFF` `#A8E3E2` `#AE7D9C`. Smallest CIEDE2000: normal 19.3, protan 17.5, deutan 17.5, tritan 17.4.

Worst pairs: main text 13.12 : 1, Lc -92.6; labels 9.09 : 1, Lc -68.8; quiet text 6.07 : 1, Lc -48.7; units 9.57 : 1, Lc -69.1; text on filled buttons 16.73 : 1, Lc 94.5; clip titles 4.57 : 1, Lc -77.2; clip edge 3.77 : 1; accent 14.22 : 1; selection 10.16 : 1; record 6.09 : 1; playhead 7.25 : 1. Rules passed: 27 of 27. Meaning colours apart: accent/sel 24.8, sel/over 40.4, sel/rec 43.5, accent/rec 37.0, accent/ok 26.0, ph/sel 53.8, ph/rec 43.9.

Readability fit: smallest CIEDE2000 over four visions 2.2 -> 17.4 (limits: lightness 0.10, chroma 0.050, hue 18 degrees); dis #737270 → #7C7B79.

### After the picks

The build task (TM, its own new lane, prefix `tm`) takes the picked versions as theme files in the W3C Design Tokens format, with the round 2 tokens (`accentFill`, `okS`, `selFill`, `tip*`, the style tokens) and `tools/design-lab/th2/check.py --gate` as the release-gate step. If A0 is picked for A, nothing changes for today's look and its misses stay the gate's baseline. Picking E2 or J2 also brings "Follow the system's light or dark setting" for that theme.

## The user's round 2 picks (28 November 2026, 18:31 Brussels)

`Theme round 2 picks: A1 B1 C2 D2 E2 G2 H1 J2 | default A1`

The user on C (Space Race): "With the space race version, so we are taking the 3 rings, I think a little bit darker, but I want it to be a little bit more NASA themed. And let's have the settings button match your theme. So with the space race, I want more like NASA things."
- **C2, adjusted:** a little darker, and more NASA in feel (mission-control and NASA-era references through tokens: colours, hairlines, type accents, grid; never decoration that costs readability; no NASA logos or trademarks).
- **The settings button matches the theme:** the Settings (gear) button, and by extension the theme's small UI marks, take the active theme's look (TM4 below).
- Default **A1**. Icons follow theme: yes (round 1).

Built by task **TM**, lane S (prefix `tm`, row in CLAUDE.md): TM1 the semantic tokens on top of LOOK, the eight theme files (A1 B1 C2 D2 E2 G2 H1 J2, C2 darker and more NASA), `tmApply` live switching with no reload and no per-frame cost, `TM_HOOKS` for other lanes; TM2 the contrast check (`check.py --gate` or a Node port) as a release-gate step, with A's known misses as the baseline; TM3 the app icon follows the theme (through the icon picker's hook); TM4 the Settings button and the theme's small marks drawn per theme; the Settings row (theme cards, Adjust, Follow system appearance, Icon follows theme) through lane B's hooks; token adoption by lanes A, E, F and I through their own steps (TM leaves the token names and a short guide). Ends 'themes complete'.
