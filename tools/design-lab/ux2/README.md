# UX2: long sessions

- `long-sessions.html`: the pick page, published as the artifact "AudioLab for long sessions", https://claude.ai/artifact/3e9BvwsCHanzjGSka4QtUH (uses `img/`).
- `shoot_measure.py`: screenshots of today's app at the user's size (2194 x 1139 @1.75x; Dark, Light mode, Pro Tools style), every visible text run, moving pixels. Start `python3 -m http.server 8765 --bind 127.0.0.1` in the repo first. `python3 shoot_measure.py <out>`
- `contrast.py <out>`: WCAG 2 and APCA for every text run and the canvas colour pairs; physical sizes.
- `cvd.py <out> [screenshot]`: colour-vision simulation (Machado 2009) of the track palette, the tuned palette search, Okabe-Ito; simulated screenshots.
- `oled.py <out>`: average picture level and bright static regions.
- `check.py [out]`: headless check of the pick page (1280 at 1x and 1.75x, 400 px).
- `measure/`: the output of the run on v0.263.

Write-up: `docs/research-ux-long-sessions.md`.
