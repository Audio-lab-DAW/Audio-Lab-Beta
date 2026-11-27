# Comfort modes (task CF, lane P, prefix `cf`)

The user's wishes of 27 November 2026, 22:23 Brussels (end of `docs/research-ux-long-sessions.md`). One step per run, fired again and again by the scheduling chat. Lane P owns the map's Hide mode and its overlay (where the map lives, not what it draws: drawing is lane A's, scrolling lane O's), OLED care, Night mode and Focus mode. Colour changes only as added tokens or a mode class. Settings rows through lane B's hooks (`CF_HOOKS.rows`, the S4 settings-table shape), the three modes together in one place.

Rules for every step: with every mode off and the map docked the app looks and behaves as before (screenshots equal); old projects and settings load; no audio code (exports bit-identical, Fractals levels unchanged); no per-frame work while idle; reduced motion respected; dark and Light; plain language, no em dashes in UI text; tooltips on new controls. Timings 0 / 50 / 80 / 120 ms (lane F's motion tokens; until they land in LOOK, `--cf-t1` 50 ms and `--cf-t2` 80 ms multiplied by lane F's `--ov-mo`, which is 0 under reduced motion).

## Steps

| Step | What | Status |
|---|---|---|
| CF-1 | The map's Hide button; in Hide mode the map's space is given back; the map rises as an overlay (glass engine face, no backdrop-filter) when the pointer comes to the edge where it is docked (top or bottom), goes away when the pointer leaves; Hide again re-docks; remembered (`UI.cfMapHide`); command `view.mapHide` | in progress |
| CF-2 | OLED care, off by default: dimmed static brights (E10, mode class), dim when idle (E11, transport hook), the OLED care card (E13) | |
| CF-3 | Night mode (E14), off by default: brightness 100 to 50 %, warmth, optional schedule, one filter outside the glass engine's backdrop | |
| CF-4 | Focus mode (E15), off by default: arrangement, transport and map only; command and key through lane H's registry. Then "comfort modes complete" | |

The Settings rows of OLED care, Night and Focus sit together in one place (lane B's hooks).
