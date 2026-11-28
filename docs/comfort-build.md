# Comfort modes (task CF, lane P, prefix `cf`)

The user's wishes of 27 November 2026, 22:23 Brussels (end of `docs/research-ux-long-sessions.md`). One step per run, fired again and again by the scheduling chat. Lane P owns the map's Hide mode and its overlay (where the map lives, not what it draws: drawing is lane A's, scrolling lane O's), OLED care, Night mode and Focus mode. Colour changes only as added tokens or a mode class. Settings rows through lane B's hooks (`CF_HOOKS.rows`, the S4 settings-table shape), the three modes together in one place.

Rules for every step: with every mode off and the map docked the app looks and behaves as before (screenshots equal); old projects and settings load; no audio code (exports bit-identical, Fractals levels unchanged); no per-frame work while idle; reduced motion respected; dark and Light; plain language, no em dashes in UI text; tooltips on new controls. Timings 0 / 50 / 80 / 120 ms (lane F's motion tokens; until they land in LOOK, `--cf-t1` 50 ms and `--cf-t2` 80 ms multiplied by lane F's `--ov-mo`, which is 0 under reduced motion).

## Steps

| Step | What | Status |
|---|---|---|
| CF-1 | The map's Hide button; in Hide mode the map's space is given back; the map rises as an overlay (glass engine face, no backdrop-filter) when the pointer comes to the edge where it is docked (top or bottom), goes away when the pointer leaves; Hide again re-docks; remembered (`UI.cfMapHide`); command `view.mapHide` | released in v0.301 |
| CF-2 | OLED care, off by default: dimmed static brights (E10, mode class), dim when idle (E11, transport hook), the OLED care card (E13) | |
| CF-3 | Night mode (E14), off by default: brightness 100 to 50 %, warmth, optional schedule, one filter outside the glass engine's backdrop | |
| CF-4 | Focus mode (E15), off by default: arrangement, transport and map only; command and key through lane H's registry. Then "comfort modes complete" | |

The Settings rows of OLED care, Night and Focus sit together in one place (lane B's hooks).

## CF-1 as built (released in v0.301, 28 Nov)

- Edit script `tools/design-lab/cf/cf1_edit.py` (CSS before `.dacv{display:flex;`, JS before `askChoice`; anchors asserted; refuses to run twice). At release: `python3 tools/design-lab/cf/cf1_edit.py index.html --commands docs/commands.md --version 0.xxx` (the `view.mapHide` row must land together with index.html, or taskXT_DL2 fails on main).
- The button `#cfMapHide` ("Hide", tooltip) sits at the right of the map's caption row (bottom row when the map is on top), `aria-pressed` while hidden.
- Hidden: `body.cfmh`; `#mapw` is `display:none` until shown, so the stage, or whatever is around the map, takes its place (no empty strip). `drawMap` is wrapped: nothing draws the map while it is hidden and not shown.
- The edge: the bottom of what is above the map's place (map in `#topOut`) or the top of what is below it (map in `#botOut`), read at most twice a second from the pointer handler, never per frame. Reveal within 6 px of it (window edges: only on the inside), no button held. Right after Hide is clicked, the map waits until the pointer has left the edge once.
- Shown: `#mapw.cfon` is `position:fixed` at the edge, 6 px in from the window sides, z-index 20 (over the panels, under floating windows, menus and sheets), translucent like the floating windows and listed in `GLFSEL` as a `window` face, so the glass engine's floating layer draws its frosted backdrop (no backdrop-filter). Solid (`body.gls`, `fxmin`, `glfsol`) draws it solid. Slide 12 px and fade in 80 ms, out 50 ms, leave grace 120 ms, all times lane F's `--ov-mo` (0 under reduced motion: at once).
- Leaves when the pointer is outside the map and the edge for 120 ms with no button held and no context menu open; Escape puts it away; a layout change or a window resize puts it away.
- Hide again (the button in the overlay, or `view.mapHide`) re-docks it at the same place and size.
- Test `tools/ui-tests/taskCF_1.py [index.html] [out] [old index.html]`: 43 checks (button and tooltip, screenshot equal to v0.294 outside the button with Hide off, space given back at the bottom and at the top, reveal and leave at the window bottom, under the tabs, under the transport and above other bottom panels, glass face, usable map, nothing drawn while hidden, Escape, re-dock same rect and same picture, reload keeps it, the command, reduced motion, Solid, idle frame time, no console errors). Also run on the build (v0.301): taskXT_DL2 24/24; taskXT_DL2 24/24 (with the commands row), taskGS4 42/42, glass_gs2 48/48, overview.py same output as v0.294.
