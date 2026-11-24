# AudioLab remake framework

Tools for recreating an existing song inside AudioLab Studio and checking the result against the original.
A script drives the real app, builds the project, renders it through the app's own audio engine, measures
the render against the original and its stems, and corrects the project. Then it does that again.

## What is in here

| File | What it does |
|---|---|
| `alab.py` | The bridge client. Opens AudioLab headless and talks to `window.AudioLab` (built into the app from v0.131). `build(recipe)`, `render(...)`, `run(code)`, `state()`, `add_audio(...)`, `save(path)`. |
| `measure.py` | The "ears". Loudness (LUFS), tonal balance per band, spectrogram distance, rhythm and low-end envelope correlation, chroma, stereo width, one 0-100 score, and a picture (`plot_compare`). `Ref` cuts any span of beats out of the original or a stem. |
| `fit.py` | Fitting. `fit_params` (bounded pattern search through real renders), `eq_match` (Pro EQ gains that give a sound the target's octave balance), `automix` (track levels by non-negative least squares on band energy over time). |
| `models.py` | Exact Python ports of simple AudioLab sound models (the Kick designer), so a fit can run thousands of times without the browser. Always verified with a real render afterwards. |

## The bridge inside the app

`window.AudioLab` (see the comment block in `index.html`):

- `run(code)`: runs JavaScript in the app's own scope. Every internal function and variable is reachable, so anything can be inspected or changed.
- `build(recipe)`: replaces the current project with one described as plain data.
- `render({b0,b1,sr,only,tracks,tail})`: offline render through the real engine (mix, one track, or a set of tracks). `pull` reads the samples back.
- `audioNew/audioPut/audioDone`: brings audio in (reference tracks, samples).
- `pack()`: the current project as an `.audiolab` file.

Nothing runs unless a script calls it.

## Recipe format

```json
{"name": "Song", "bpm": 145, "master": 0,
 "sections": [{"name": "Intro", "start": 0, "len": 64, "color": "#4cc9f0"}],
 "mfx": [{"type": "clip", "p": {"gain": 11, "thr": -8, "ceil": -1.8, "shape": "tanh"}}],
 "tracks": [{
   "name": "Kick", "preset": "kick", "color": "#ff6b6b", "vol": 1.0,
   "inst": {"tune": 30.5, "start": 405, "sweep": 0.25},
   "fx": [{"type": "eq", "p": {"out": 2.8, "bands": [{"t": "peaking", "f": 90, "g": 0.5, "q": 1.2, "on": true}]}}],
   "clips": [{"start": 0, "len": 32, "name": "Kick 1",
              "notes": [{"p": 36, "s": 0, "l": 0.25, "v": 0.95}],
              "env": {"cut": [{"b": 0, "v": 0.5}]}}]}]}
```

Positions and lengths are in beats. `inst` overrides fields of the instrument preset; `fx[].p` overrides effect
parameters; clip `env` holds the clip envelopes (`vol`, `pan`, `cut`, `res`; `b` in beats from the clip start, `v` 0-1).

## The loop

1. **Analyse the original.** Tempo and beat grid (find the kick's click, not its low end), structure per bar, key.
2. **Split into stems** (Demucs `htdemucs`: drums, bass, other, vocals).
3. **Transcribe** each stem on the 16th grid: kick, bass notes and levels, hats, claps, fills, and where a part is filtered.
4. **Fit the sounds.** Kick: fit the pitch sweep first, then length, click and drive. Bass and other synths: `fit_params` through real renders. Then `eq_match` each sound against its stem.
5. **Build** the recipe and send it to the app.
6. **Render and compare** in 8-bar blocks: `compare(ref.cut(b0, b1), render)`.
7. **Correct**: `automix` for levels, a master clipper for loudness, and a closed loop that corrects each band in each block.
8. Repeat 6 and 7 until the numbers stop improving, then render the whole song, save the `.audiolab` file and the report.

## What it can and cannot do

- Drums and bass with a clear shape (kick, rolling bass, hats) can be rebuilt as real instruments and notes and fitted closely.
- Parts whose character is timbre movement on one note (most psytrance leads and effects) are rebuilt as *followers*: a drone on the song's root through a band-pass, with a clip volume envelope that follows the original's energy in that band. This tracks rhythm and tone well; it is not a note-for-note transcription and it does not reproduce the exact waveform.
- Voices and samples cannot be synthesised. The followers treat them like any other sound.
- "Listening" here is measurement. A high score means the render is close in loudness, tone, rhythm and harmony by these measures. It does not replace a human listen.

## Requirements

Python 3 with `playwright` (Chromium), `numpy`, `scipy`, `librosa`, `soundfile`, `pyloudnorm`, `matplotlib`, and `demucs` for the stems.
