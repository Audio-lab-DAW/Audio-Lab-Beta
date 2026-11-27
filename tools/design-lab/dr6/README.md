# DR6: arrangement lines

- `arrangement-lines.html`: the pick page, published as the artifact "AudioLab arrangement lines", https://claude.ai/artifact/YGbbF7XNgkjPnWp5jopAu9 (self-contained; the publish wraps it in a document skeleton).
- `check.py`: headless check of the page (1280 px at 1x, 1.75x, 2x and 400 px; clicks every option; screenshots; console errors; horizontal scroll). `python3 check.py [outdir]`
- `shots_today.py`: screenshots of today's arrangement (Fractals demo) at the user's size 2194 x 1139 @1.75x, whole song, 16 bars and 1 bar. `python3 shots_today.py index.html [outdir]`

Write-up: `docs/design-grid-lines.md`.
