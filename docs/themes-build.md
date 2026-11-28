# Themes: the build plan (task TM, lane S, prefix `tm`)

Written 28 November 2026 by task TM0. Source of truth for what ships: the user's round 2 picks (28 Nov, 18:31 Brussels)
`Theme round 2 picks: A1 B1 C2 D2 E2 G2 H1 J2 | default A1`, icons follow theme: yes, and on C: "a little bit darker, but
more NASA themed. And let's have the settings button match your theme." Research and every token value:
`docs/research-themes.md` (sections 4, 5, 7, round 2 and the picks); reference pictures and token files:
`tools/design-lab/th2/` (`themes.json`, `themes_src.py`, `check.py`, `pick-page.html`).

Lane S owns: the semantic theme tokens on top of `LOOK`, the theme files, `tmApply`, the theme contrast check, the
icon-follows-theme link, and the Settings button drawn per theme. Other lanes adopt the tokens in their own areas (TM5's
guide). Themes never touch audio: no audio node, no worklet, no export path is read or written by any `tm` code.

## Status

| Step | What | Status |
|---|---|---|
| TM0 | this plan | done (28 Nov, docs only) |
| TM1 | tokens, eight theme files, `tmApply`, the Settings row, default A1 | next |
| TM2 | the contrast check as a release-gate step, A's known misses as the baseline | to do |
| TM3 | the app icon follows the theme | to do |
| TM4 | the Settings (gear) button and the theme's small marks drawn per theme | to do |
| TM5 | the adoption guide for lanes A, E, F, I and the glass floor per theme | to do; then "themes complete" |

## The themes that ship

Ten colour sets in eight themes. Ids are stable (they are stored in `UI.tmTheme` and named in the settings file).

| Theme id | Name | Version | Mode | Partner for "Follow system appearance" | Icons that follow it (first one is used) |
|---|---|---|---|---|---|
| `orbit` | Orbit night (default) | A1 | dark | none | `dipole-field`, `field-depth` |
| `chart` | Chart paper | B1 | light | none | `dipole-field-paper`, `measured-field-paper`, `field-dial-paper` |
| `space` | Space Race | C2, made darker and more NASA (below) | dark | none | `three-rings`, `space-race` |
| `chalk` | Chalkboard | D2 | dark | none | `science-fair`, `chalkboard` |
| `blueprint` | Blueprint | E2 (dark) + E2L Whiteprint (light) | both | yes | `blueprint`, `cutaway-nucleus` |
| `cutaway` | Cutaway nucleus | G2 | dark | none | `cutaway-nucleus` |
| `rutherford` | Rutherford scattering | H1 | dark | none | `rutherford-scattering` |
| `patent` | Patent drawing | J2 (light) + J2D Photostat (dark) | both | yes | `patent-drawing` |

The values are copied from `tools/design-lab/th2/themes.json` (`t`, `pal`, `style`, `icons` of each version) by the TM1 edit
script, never typed by hand, so the shipped file and the measured file cannot drift. The icon lists are checked against the
icon picker's ids (`listAppIcons()` / the picker's groups) in TM3 (all twelve are in `desktop/icon-assets/picker/` on 28 Nov); a name the picker does not have is dropped with a log line.

### C2 for the user: darker, more NASA

Made in `tools/design-lab/tm/c2_nasa.py` from C2 (`themes_src.py`), then fitted and measured with the round 2 rules
(`th2/check.py`'s functions), and written to `tools/design-lab/tm/themes.json` as `C2N`, which is what ships as `space`.
Through tokens only (colours, hairlines, type accents, grid), nothing drawn on top:
- **Darker:** every surface (bg, chrome, ruler, lanes, panels, strip, display, glass) about 0.02 to 0.03 lower in OKLCH
  lightness, the graphite kept; text keeps its measured contrast (the fit raises text lightness, never lowers it).
- **Mission-control colours** (Apollo-era consoles and print, as colour references only): a deep console blue-black ground,
  the "insignia" blue `#0B3D91` family as `accentFill` (filled buttons, lighter `accent` for lines), the flight red family for
  `rec` and `over` only (meaning unchanged), a warm off-white for ink (console lettering, never pure white, rule H1), a
  phosphor-green tint for `ok`/`okS` and the meter's low segment, the amber `unit` unchanged.
- **Hairlines and grid:** cooler steel hairlines (`line`, grid colour toward `143,161,187`), `gridMinor` a little higher so the
  arrangement reads like a plotting board; `dash` stays 0 (solid lines read better at 1 px).
- **Type accents:** `caps 1` (section labels in tracked capitals, like console panel lettering), numerals `plex`
  (IBM Plex Mono, as C2), titles `ui`.
- **Not used:** no logos, insignia, worm or meatball shapes, mission patches, trademarks or the agency's name anywhere in the
  app. Nothing that moves.
- Must pass all 27 round 2 rules (as C2 did) and keep track colours at 10 or more under all four visions.

## Token names (the same in every theme; values change, meanings never)

Semantic colours (section 4 and round 2): `bg chrome ruler lane0 lane1 laneSel panel panel2 strip display glass line ink lab
mut dis rulerTxt inkD accent accentFill onAccent accentD sel selFill selD unit unitD rec over overD warn ok okS ph m0 m1 m2 m3
focusIn focusOut tip tipInk tipEdge`; numbers `glassA` (tint strength), `glassFloor`, `clipA`, `grid` (r,g,b) and `gridK`;
`pal` (the eight track colours); style `caps fNum fTitle dash edgeW clipHead gridMinor`; `mode` (dark or light).

- **On `:root`** as `--tm-<name>` (for example `--tm-ink`, `--tm-accentFill`), plus `--tm-glassA`, `--tm-clipA`,
  `--tm-edgeW`, `--tm-fNum`, `--tm-fTitle`, and the class `tm-caps` / `tm-light` on `<html>`. The old variables lane by lane
  (`--bg --pn --ink --mut --acc --blue ...`) are set from the tokens by `tmApply` too, so areas that read the old names follow
  the theme before their lane adopts the new names. Lane F's `--ov-*` and lane K/LK's `--sel --unit ...` are their owners'; TM
  writes them only through the owners' hooks or leaves them (TM1 checks which ones already alias the LK values).
- **In `LOOK`** as `LOOK.tm` (one object with every token) and, for the names LK already has (`ink`, `mut`, `lab`, the grid
  levels), LK's own fields are recomputed by `lkMake()` from the active theme: `lkMake` is LK's (done task), so TM adds a
  small hook `LK_HOOKS.base` (or wraps `lkMake` without renaming it) that returns the theme's values. Only added tokens; no LK
  value is changed for A1 except where A1 itself differs from today (quiet grey, disabled grey, ruler numbers, `accentFill`,
  track colours: A1's repairs).
- **`TH`** (lanes, ruler, grid, map) is rebuilt by `applyTheme()` as today; TM gives it the theme's lanes and ruler instead of
  the hue slider's, and the Adjust sliders shift on top.
- **Device displays stay dark wells** in every theme (section 1); only `display inkD unitD accentD selD overD m0..m3` change.

## TM1: tokens, theme files, `tmApply`, the Settings row

Touches (index.html, new code before `function askChoice(title,text,btns,icon){`, new CSS before `.dacv{display:flex;`):
- `TM_THEMES` (the bundled theme files, one object; W3C Design Tokens shape `{"color":{"ink":{"$type":"color","$value":..}},
  "$extensions":{"audiolab":{glassA, clipA, grid, style, icons, mode, pair}}}`), also written as files to `themes/<id>.tokens.json`
  for reading and for the gate. No file loading at start-up.
- `tmTokens(id, mode)` flattens a file; `tmApply(id, {mode})`: writes the `:root` variables once, sets `LOOK` (rebuild through
  `lkMake`), rebuilds `TH` (`applyTheme`), clears the colour caches (`THMX`, `CLC`, lane O's tile cache through a hook: TM asks
  lane O for `UV_HOOKS.flush`, until then sets `dirty=true` and the cache's own key changes), one redraw (`dirty=true`,
  `rfAll()`). No reload, no timer, no per-frame code: nothing in `draw()` reads `UI.tmTheme`.
- `TM_HOOKS`: `applied(fn)` (lanes subscribe to theme changes instead of polling), `tokens()` (the active tokens), `mode()`.
- Start-up: `tmApply(UI.tmTheme||'orbit')` once, before the first draw, so there is no flash of the old colours.
- Follow system appearance: one `matchMedia('(prefers-color-scheme: dark)')` change listener (and the desktop shell's
  `nativeTheme` through the same media query), only for themes with a partner (Blueprint, Patent drawing).
- Studio looks (the existing "Theme: the look of another DAW" row, `THEMES`/`DAWLOOK`): stay as they are. Picking a TM theme
  sets the studio look back to AudioLab; picking another studio look sets the TM theme to Orbit night. Both are reversible
  from the same page. (Converting the eight studio looks to theme files is not in TM's steps; noted for the scheduling chat.)
- **Settings row** on the Colours page (`section[data-page=colors]`, lane B's): a "Theme" block at the top, inserted by TM's
  own code at a fixed anchor and registered in the settings table the way lanes J, G, N and Q do (`STT.push` / `STX.set`,
  rows in `TM_ROWS`). Lane B's table keeps search, help and reset. If lane B wants a hook (`ST_HOOKS.block`), TM switches to it.
  - Theme cards: 168 × 96 pictures drawn like the round 2 page's thumbnails (`page.src.html`, "the Settings-row thumbnail: the
    theme in six strokes"), one canvas each, drawn once per change, not per frame.
  - Adjust: today's Background, Tint and Tint amount sliders become "Adjust" over the active theme; a value that would break a
    rule is clamped by the in-page check (`tmContrast`: WCAG 2.2 and APCA 0.1.9, ported from `th1/colour.py`).
  - Follow system appearance (on for themes with a partner; greyed with a note for the others).
  - Icon follows theme (on by default: the user said yes; built in TM3, the switch is placed in TM1 and disabled until TM3).
- Settings ids (`XT_SET_NS` and `docs/settings-ids.md`): `appearance.theme` (Theme), `appearance.themeFollow` (Follow system
  appearance), `appearance.iconFollow` (Icon follows theme). Adjust keeps `appearance.bg`, `appearance.tintHue`,
  `appearance.tintAmt`. Control ids (`data-al`, docs/ids.md): `settings.theme.card` (each card, with `data-tm` = the theme id),
  `settings.theme.follow`, `settings.theme.icon`. Commands (docs/commands.md): `view.themeNext` (Next theme),
  `view.themePick` (Choose a theme…, opens the Colours page at the Theme block).
- Saved: `UI.tmTheme`, `UI.tmFollow`, `UI.tmIcon` (app settings, not the project; R0: no migration code, a missing value is
  simply the default).
- Edit script `tools/design-lab/tm/tm1_edit.py` (unique asserted anchors; re-run on a fresh file after every rebase).

Tests `tools/ui-tests/taskTM1.py` (`# for: TM1`): every theme and both modes of the pairs applied live, no reload (a
`window` marker survives), no console or page errors; `getComputedStyle` shows the tokens; LOOK and TH follow; idle frames do
no work (a `requestAnimationFrame` counter and the draw counter stay still for 3 s after a switch); every token pair passes the
round 2 rules in the page (`tmContrast` against `th2/check.py`'s numbers within 0.02); screens checked by layout (R5): Settings,
Mixer, Devices, a context menu, Export and a tooltip in each theme, every `data-al` control visible and inside its panel, no
overlap; a project saved and reopened in each theme (the theme is not in the project, the project reopens with everything);
Fractals levels unchanged (Kick −19.05560 dB, Bass −35.48685 dB with the master at −10 dB, `export_same.py`).

## TM2: the contrast check as a release-gate step

- `tools/release-gate/themes_gate.py`: reads `TM_THEMES` out of the `index.html` under test (not the design-lab file, so it
  checks what ships), runs the round 2 rules (`th2/check.py`'s measuring functions, imported, no fitting), exits 1 when a
  rule fails that is not in the baseline.
- Baseline `tools/release-gate/themes-baseline.json`: theme A's known misses (A0, today's chrome as still drawn by literal
  colours in areas that have not adopted the tokens: quiet grey over glass, labels over glass on bright clips, disabled text,
  ruler numbers, white on the blue accent, clip titles, tooltip outline, glass floor). The shipped picks must pass every rule
  (27 of 27 dark, 26 of 26 light). A baseline entry is removed when the area that causes it adopts the tokens.
- Step "f) Themes" in `docs/release-gate.md` with a line for task RG (the gate's owner) to call it from `gate.py`; TM does not
  edit `gate.py` unless RG's log says to.
- Test `tools/ui-tests/taskTM2.py`: the gate passes on main, fails on a deliberately broken copy (ink equal to bg), and
  passes the baseline misses.

## TM3: the app icon follows the theme

- The icon picker (`apicPick`, `apicRender`, `#apicBox`, the desktop shell's `setAppIcon`) is not TM's. TM calls the public
  `apicPick(id)` when a theme is chosen and "Icon follows theme" is on; a click on an icon tile (`#apicBox [data-apic]`) is
  picked up by TM's own listener and turns the link off ("picking an icon by hand turns the link off", section 5). If the icon
  owner adds a hook (`APIC_HOOKS.picked`), TM moves to it.
- Each theme's icon is the first of its list that the picker has; checked in Electron (`listAppIcons`) and the browser.
- Test `taskTM3.py` (browser) and `taskTM3_electron.js`: choosing each theme sets the icon, a hand pick turns the link off,
  turning the switch on again re-applies the theme's icon; no error when the icons cannot be loaded.

## TM4: the Settings button and the theme's small marks

- The Settings marks: the logo menu's Settings row (`crow:'set'`, its gear path), the command palette's Settings entry and the
  Settings window's title strip; plus the theme's small marks: the focus ring (two colours), the selection corner, the toggle
  and check marks, the playhead cap. Drawn per theme from the tokens (stroke colour, weight from `edgeW`, caps lettering from
  `caps`), the same gear shape everywhere (no new pictures, no logos). Where the mark sits in another lane's area (lane F's
  menus and palette), TM provides `TM_HOOKS.mark(name)` returning the SVG and lane F places it.
- Test `taskTM4.py`: each mark in each theme passes 3 : 1 against its surface and is the theme's colour.

## TM5: the adoption guide and the glass floor

- A short section here for lanes A (arrangement, clips, lanes, ruler: `lane0 lane1 laneSel ruler rulerTxt ph pal clipA edgeW
  clipHead grid gridK gridMinor dash`), E (meters and displays: `display inkD unitD accentD selD overD m0..m3 warn ok`), F
  (menus, dialogs, tooltips: `panel panel2 line ink lab mut dis tip tipInk tipEdge accentFill onAccent focusIn focusOut caps
  fTitle`), I (device frames: `strip panel2 line lab accent sel`): which literal colours map to which token, how to subscribe
  (`TM_HOOKS.applied`), what to test (their pairs in the gate's list).
- The glass floor per theme for the glass engine's owner: `glassA` and `glassFloor` of every shipped set (from the round 2
  table: A1 59 %, B1 81 %, C2 31 % (C2N measured in TM1), D2 68 %, E2 50 % / E2L 0 %, G2 47 %, H1 53 %, J2 0 % / J2D 23 %),
  the rule "never draw the tint thinner than the floor", the optional text plate, and never `backdrop-filter`.
- After TM5: "themes complete".

## Rules every step keeps

- CLAUDE.md: commit identity Audio-lab-DAW, no attribution lines; never touch `desktop/app-version.json`; while
  `desktop/release-freeze.json` is on main, push only `tools/` and `docs/` and schedule a check-in to release; only lane S's
  area; `tm` prefix for every new top-level name, checked for duplicates by the lint; R0 (no migration code).
- Release: VERSION = the highest on main + 0.001 at push time; `node desktop/scripts/sync-app.js`; one line in
  `desktop/update-notes.txt`; a `docs/backlog-log.md` entry headed "task TM<n>"; the status table above; the project doc
  `claude/audiolab-themes-build.md`; the notification "Themes step TM<n> is out (vX.XXX): <what to try>"; `index.html` (lines 3
  to 10 removed) published to the app artifact.
- Before every push: `git pull --rebase`, re-run the edit script on the fresh file, the lint and the start-up smoke test of
  `docs/release-gate.md`, the step's UI tests, and `git log -S` on the anchors for another lane's change in the last hour.
