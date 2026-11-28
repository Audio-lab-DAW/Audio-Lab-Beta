# Test songs (task WS-F)

The app ships no song (D6). The user, 28 Nov 2026: "The fractal song is only for testing." The Fractals song lives here, for the
release gate, the native lab and the tests only. It is not packed into the app and not offered in it.

- `Fractals_remake.audiolab`: the project (the current .audiolab format, formatVersion 1; the same bytes the app carried as DEMO_FRACTALS up to v0.314).
- `vox/fractals_vox_01.flac` to `10`: the vocal samples cut from Electric Universe's commercial recording (the same FLACs the app carried as DEMO_VOX_FLAC; the same samples as the old `vox/*.wav`).
- `fractals.json`: the project file and the beat where each vocal sample goes (was DEMO_VOX).
- `alsong.py` / `alsong.js`: serve the files to the browser tests (`alsong(handler)` around the `https://app.test/**` route) or put them in as `window.AL_TEST_SONGS` (the Electron tests).

In the app, `frxProject()` and `openDemoFractals()` read these files; under automation (navigator.webdriver) the app opens the song at start, as before. Without the files the app opens an empty project and says nothing.

When the project format changes (R0), re-save `Fractals_remake.audiolab` in the same step.
