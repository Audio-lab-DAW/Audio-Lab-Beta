# The stem split's loading bar is the spectrogram (task SG1, 28 November 2026)

**Pick page: "AudioLab stem split: the loading bar is the spectrogram"**, https://claude.ai/artifact/WMBGrvG9xy3ZZFfQqWcjkG (source `tools/design-lab/sg1/stem-split.html` with its data `tools/design-lab/sg1/sg1-data.json`).

The user (28 Nov, 02:09 Brussels): "When you're splitting stems anywhere, the loading bar should be the spectrogram of every stem that you're splitting … Maybe to do it actually live, so it's actually the spectrogram appearing as the loading bar, and do some research on that to get this right."

Research and pick page only: no change to `index.html`, `desktop/` or `native/`.

## Summary

- It can be live and honest. HTDemucs separates a song in 7.8 s chunks, one after another from the start of the song, with a 25 % overlap and linear cross-fades. Each finished chunk already holds every stem's audio for that stretch. A spectrogram of that stretch costs about 0.1 % of the chunk's time, so each stem's lane can fill to the true position in the song as soon as the model gets there.
- The pick page runs three layouts (G1 to G3) and two small versions (S1, S2) on real stems. The clip is 40 s of the Fractals song (bars 1 to 24: the sung intro over the pad, then kick and bass at 0:26). It was rendered by the app, split by the app's own quick splitter and by the app's HTDemucs worker loop, and the chunks arrive at the measured times. The page has Dark and Light themes, a Reduce motion switch, a "first split ever" switch (the model download comes first), ×1/×4/×16 speed, and the 4-stem, 6-stem and quick engines.
- Recommended (★): **G1** lanes under the mix, **S1** the notification card with a strip per stem, **P1** the draft stretch at half strength, **F1** a soft scan over the chunk being worked on (still under Reduce motion). The picks bar gives one line to paste, for example `SG1 picks: G1, S1, P1, F1`.

## Today's code (v0.294)

| What | Where | How it reports progress |
|---|---|---|
| Quick split | `stemSplit(buf, prog, P)` (after the comment "stem splitter (quick DSP…)") | Runs on the main thread in blocks of `SEG = 1<<18` samples (5.9 s at 44.1 kHz), each with a 20-hop margin (0.23 s) on both sides, in song order. Calls `prog(s1/len)` once per block and yields with `setTimeout(0)`. Each block's four stems (drums, bass, vocals, other) are final when it ends. |
| Neural split | `NEUM` (n4: 166 MB, Drums/Bass/Other/Vocals; n6: 136 MB, adds Guitar/Piano, with their colours), the worker source `NEUW`, `neuWorker`, `neuTo44`, `neuSeparate(buf, kind, keep, prog)` | onnxruntime-web 1.20.1 (WASM) in a blob worker. The model comes from Hugging Face once and is kept in Cache Storage. The worker uses threads `min(8, cores)` when cross-origin isolated, otherwise 1. Chunks are `N = 343980` samples (7.8 s), `OV = N/4`, step `ST = 257985` (5.85 s), with linear cross-fades, in order and no shifts. It posts `dl` during the download, `st` (cached, init), one `p` per chunk, and the stems only at the end (`done`). |
| Split dialog | `stemAsk(name)` → `stemsFor(t, c)` | The sheet closes on Split. Progress then shows in MD1's pill `mdJob('stem', …)`: "Downloading the stem model, 166 MB" with a percent, "Loading the stem model" with the orbit, then "Separating with HTDemucs" with a percent that moves once per chunk. The tracks are added at the end and the original clip is muted. |
| Callers | the clip menu "Split into stems…" (`clipMenu`), the import question on a drop (`ch.mode==='stems'` → `stemsFor`), Audio to MIDI's "Split into stems first, then choose" (`openA2M`, its `split(j)`) | Audio to MIDI shows "Splitting *clip*…" with a 4 px bar (`a2dbar`) and a percent. It then lists the stems as listen rows (▶, Convert, mode). |
| Spectrogram drawings | INS colour maps (`INS.CMH`, viridis, lane E), the Visualizer (IN-V, viridis by default), the splash's S6 spectrogram (one column at a time), the Meter's spectrogram | — |
| Look | LOOK tokens: L2 units in amber (`--unit`, `lkVU`, `lkOut`), W1 hairlines (`--lk-hair`), A1 `--sel`, M3 motion, N3 density, G3 grid; lane F's motion tokens 0 / 50 / 80 / 120 ms, Reduce motion sets `--ov-mo: 0`; the glass engine draws lenses (no backdrop-filter) | — |

## Research

How HTDemucs works through a song:
- Hybrid Transformer Demucs is trained on 7.8 s segments of 44.1 kHz stereo. At inference "we split the audio into chunks having the same duration as the one used for training, with an overlap of 25% and a linear transition from one chunk to the next" ([Rouard, Massa, Défossez 2022](https://ar5iv.labs.arxiv.org/html/2211.08553)). "The Hybrid Transformer models only support a maximum segment length of 7.8 seconds" ([Demucs README](https://github.com/adefossez/demucs)).
- Demucs's `apply_model` walks `range(0, length, stride)` with `stride = (1 - overlap) * segment`. It weights each chunk with a triangle raised to `transition_power` (1 by default, which is linear at 25 % overlap), sums the chunks and divides by the summed weights. With `num_workers > 0` on CPU it runs chunks in a thread pool, but it still collects them in time order ([apply.py](https://huggingface.co/spaces/Rooc/Vocal-Remover/raw/main/demucs/apply.py)). The app's worker does the same in one thread of JavaScript, so a stretch is final once the next chunk has been added.
- The shift trick (`shifts`) repeats the pass with random offsets up to 0.5 s and averages the results. It "makes prediction SHIFTS times slower" for up to 0.2 SDR ([README](https://github.com/adefossez/demucs), apply.py docstring). The app uses no shifts. If shifts are ever added, the lanes fill once per pass, or fill once and get refined.
- Speed: the paper reports a real-time factor of 1.49 on one CPU core for the 7.8 s model in PyTorch. The README says CPU time is "roughly equal to 1.5 times the duration of the track". In WebAssembly here it is 2.3 times (2 threads) to 4.1 times (1 thread); see the measurements below.

How other apps show it:
- Logic Pro Stem Splitter: no progress picture is described. The stems appear as a summing stack when done, "typically half a minute for an average-length song" on Apple silicon ([Apple](https://support.apple.com/guide/logicpro/lgcp61bae908/mac), [Sound On Sound](https://www.soundonsound.com/techniques/logic-pro-how-use-stem-splitter)).
- Ableton Live 12.3: a status line with a task count such as "1/2" for decoding and each pass. High Speed is one pass; High Quality is several and slower. Apple silicon uses the GPU ([Ableton FAQ](https://help.ableton.com/hc/en-us/articles/23730994755996), [Ableton](https://www.ableton.com/en/stem-separation-in-ableton-live/), [CDM](https://cdm.link/ableton-live-12-3-guide/)).
- Serato: a status message, plus a crate icon that turns from grey to white when the stems are prepared ([Serato](https://support.serato.com/hc/en-us/articles/5700969287183)). Engine DJ users complain that "no progress is shown" for stem analysis ([Engine DJ community](https://community.enginedj.com/t/stems-super-slow-analysis-no-progress-indicator/60640)).
- iZotope RX Music Rebalance ([iZotope](https://www.izotope.com/en/learn/stem-separation-music-rebalance)), FL Studio, UVR ([GitHub](https://github.com/Anjok07/ultimatevocalremovergui)), Moises and LALAL.AI ([MusicRadar test](https://www.musicradar.com/music-tech/i-tested-11-of-the-best-stem-separation-tools-and-you-might-already-have-the-winner-in-your-daw)) show a bar or a job status. None that we found draws the stems while they are being made.
- Progress timing follows lane F's rule from [NN/g](https://www.nngroup.com/articles/progress-indicators/): nothing under 1 s, the orbit for 1 to 10 s, percent and Stop beyond 10 s.

Keeping the drawing cheap:
- The worker computes the columns, not the page. After each chunk it takes the final stretch of each stem and does one 4096-point FFT per column, with one column per lane pixel. A 4-minute song in a 480 px lane at 2x is about 23 columns per chunk per stem. The FFT bins fold into 96 log-frequency rows (32 Hz to 16 kHz), and the worker posts a Uint8Array of dB values from -84 to 0 (about 13 KB for six stems).
- One canvas per lane. Each chunk paints only its new columns with one `putImageData` dirty rectangle, and for P1 it repaints the draft stretch. Nothing runs per frame: the amber edge moves by a 120 ms CSS transition, the chunk being worked on is a CSS gradient (F1) or a still hatch (F2), and the read-out text changes once a second. The pick page itself is built this way: timers fire at the chunk times, with no animation loop.
- Reduce motion (the system setting, or the app's Motion setting below Ambient): no moving gradient and no transition on the edge. The lanes still fill, because the fill is the information. Light (low-power) mode: the same, and no draft stretch.
- The mix's own spectrogram needs no model, so it is drawn at once, before the download starts.

## Measurements

Run on a cloud container with 2 x86-64 cores, headless Chromium and Node 22, app v0.294. These are not the user's Mac: the Mac will be faster, and the desktop shell is cross-origin isolated, so the worker runs with up to 8 threads there.

| What | Measured |
|---|---|
| Clip | Fractals, beats 0 to 96 at 145 BPM, 1 751 835 samples at 44.1 kHz = 39.72 s, rendered with `renderMix` |
| Quick split, whole clip (Chromium, main thread) | 3.11 s, 0.078 times the clip; 7 progress calls, one per block, about 440 ms apart (each one a main-thread pause) |
| Neural, model load (`InferenceSession.create`, optimiser off) | 8.8 s (4 stems), 8.8 s (6 stems) |
| Neural 4 stems, one chunk, 2 threads | 13.3 s mean (13.5, 13.0, 13.3, 13.7, 13.5, 13.0, 12.9); each chunk moves the edge 5.85 s |
| Neural 6 stems, one chunk, 2 threads | 12.3 s mean |
| Neural 4 stems, one chunk, 1 thread | 24.1 s mean of 2 |
| Overlap-add per chunk in the worker | 4 to 52 ms |
| Progress callback today (neural) | once per chunk, so every 13.3 s here |
| Spectrogram columns | 0.10 ms per 4096-point FFT (384 in 38 ms); about 14 ms per chunk for 6 stems at 23 columns, 0.1 % of a chunk |
| A 4-minute song | 42 chunks; on this machine about 9:30 with 2 threads and 17:00 with 1 thread, model load included |
| Engine memory with the 4-stem model | about 1.5 GB resident |

How: `tools/design-lab/sg1/run.py` (with `probe.py`) opens the app through the AudioLab bridge (`tools/remake/alab.py`). It renders the clip, runs `stemSplit` with a timer on its progress callback, and times the FFT. The neural split in headless Chromium crashed the page while the model loaded (it ran out of memory in the test browser, not a user report). So `chunks_node.mjs` runs the worker loop from `NEUW` unchanged in Node, with the same engine and options: onnxruntime-web 1.20.1 WASM, the same Hugging Face model files, `graphOptimizationLevel: 'disabled'`. The stems on the pick page are that output. `spec.py` makes the log-frequency spectrograms and `build_data.py` writes `sg1-data.json`. `shot.py` takes the screenshots (dark, light, phone).

## The designs

The pick page is measured and live. In every layout the lanes fill at the true position in the song. The amber hairline edge carries the time of the last final sample. The read-out row uses L2: values in ink with equal-width digits, units in amber small caps (`4 / 7 CHUNKS · 0:23.4 / 0:39.7 S · ≈ 1:12 LEFT`). Stem colours are those of `NEUM` and the quick split.

- **G1 ★ Lanes under the mix.** The mix's spectrogram sits faint on top (22 px) as the reference. Below it, one lane per stem (34 px; 26 px for 6 stems) in viridis from INS, labelled with the stem's colour and name. When the split ends, each lane shows its level and a tick (silent stems unticked, as today's Audio to MIDI does), and "Add 3 tracks" creates them.
- **G2 The mix turns into each stem.** Every lane starts as the faint mix. As chunks land, the mix is replaced by that stem in its own track colour, which is the colour its new track will have.
- **G3 The mix coloured in by stem.** One tall spectrogram of the mix. Finished columns take the colour of the stem that owns each pixel (shares of the stems' energy). A legend counts each stem's share of what is visible.
- **S1 ★ Notification card.** Inside lane F's N1 stack: the orbit with the real progress, the clip name, a 6 px strip per stem, the remaining time, Open and Stop. When it ends it says what was added and offers Undo.
- **S2 Status pill.** MD1's `mdJob` pill gets a 96 × 16 strip coloured as G3, plus the percent.
- **P1 ★ / P2 Draft stretch.** When a chunk ends, its last 1.95 s will still be cross-faded with the next chunk. P1 shows it at half strength and repaints it; P2 shows only final columns.
- **F1 ★ / F2 Between chunks.** F1 is a faint CSS scan over the next 5.85 s while the model works on it (a still hatch under Reduce motion). F2 is always the still hatch.
- **Remaining time.** The mean of the last three chunk times multiplied by the chunks left, counting down once a second. Before the first chunk it uses this computer's last speed for that model (save `UI.sgRate[kind]`, seconds per chunk). On a first-ever split it says "estimating…" until one chunk is done. During the download it shows MB of MB.
- **Quick split.** The same lanes as one fast sweep, block by block, with no draft stretch (its blocks are final). No loader under 1 s. Move it into a worker (or yield more often), because today it pauses the app about 0.45 s per block.
- **Where.** The Split sheet stays open after Split and becomes the layout; Keep working sends it to S1 (or S2). In Audio to MIDI the lanes replace `a2dbar`, and each lane then becomes its listen row (▶, Convert, mode). During the download and load the lanes are there and empty, with the mix drawn. With several clips: one set of lanes for the clip being split, "clip 2 of 3" in the read-out.

## Who builds it

- **The splitter** (`stemSplit`, `NEUW`, `neuWorker`, `neuSeparate`, `stemAsk`, `stemsFor`) predates the lanes and no lane in CLAUDE.md owns it. The build task (**SG2**, prefix `sg`) takes it:
  - the worker posts `{t:'cols', i, s0, s1, fin, prov, cols}` after each chunk (cols: Uint8Array, stems × rows × new columns, transferred);
  - `neuSeparate` and `stemSplit` take an optional fifth argument `onCols`;
  - `SG_HOOKS.onChunk(job, msg)` lets other code listen;
  - `sgLanes(host, job)` draws a layout, and `sgStrips(host, job)` draws the small strips;
  - the quick split moves into a worker that computes the same columns.
- **Lane F** (overlays): the Split sheet's frame and S1 inside the N1 notification stack. SG2 adds `SG_HOOKS.card(job)`, which returns the strips element; lane F puts it in the card when OV5 builds `notify({kind, text, action, keep})`. Until then SG2 draws the card under `mdJob`.
- **Lane G** (MD1): `mdJob` keeps the pill. For S2 it reads an optional strip from `SG_HOOKS.pill(key)`.
- **Audio to MIDI** (`openA2M`'s stems step): SG2 replaces `a2dbar` with `sgLanes` and turns the finished lanes into the `a2sr` rows. This is a small hook in the `split(j)` callback, with no rewrite of the rows.
- **Lane E** (INS): viridis is read from `INS.cmap('viridis')`, never copied or changed. **LK**: `--unit` and `lkVU` for the units, `--lk-hair` for the edge.
- Motion: the edge's transition is the 120 ms token, and with Reduce motion (`--ov-mo: 0`) it is 0.

## The user's picks (28 November 2026, 14:53 Brussels)

`SG1 picks: G1, S1, P1, F1` (all four recommendations): **G1** lanes under the mix, **S1** the notification card with a strip per stem, **P1** the draft stretch at half strength, **F1** a soft scan over the chunk being worked on (a still hatch under Reduce motion). Built by task **SG2**, lane R (prefix `sg`, row in CLAUDE.md), as "Who builds it" above says, with the quick split moved off the main thread. Ends 'stem split lanes complete'.

## Build (task SG2, lane R, prefix `sg`)

- 28 Nov 2026, 14:00 UTC: **step SG2-1 claimed** (the worker posts per-chunk spectrogram columns; `stemSplit` and `neuSeparate` take `onCols`; the quick split moves into a worker). The release gate's freeze (`desktop/release-freeze.json`, since 12:35:47 UTC) holds `index.html`: the steps are built as edit scripts in `tools/edits/` and released when it lifts.
- 28 Nov 2026, 15:00 UTC: SG2-1 to SG2-4 **built and tested** as edit scripts on v0.297 (`tools/edits/taskSG2_<k>.py` with their `_block.js`, `_css.txt` and `_test.py`; `taskSG2_release.py <k> <version>` writes the notes and logs of a step): taskSG2_1 23/23, taskSG2_2 42/42, taskSG2_3 15/15, taskSG2_4 17/17 on v0.297 + all four; the release gate's quick run (`gate.py --here --quick`) on v0.297 + SG2-1 passed every step (lint, smoke 14 of 14, frame times, windows, Fractals and exports bit-identical). `index.html` waits for the freeze; each step is then released on its own.
- 28 Nov 15:56 UTC: **SG2-1 released**, v0.302: per-chunk spectrogram columns, the quick split in a worker. Test `tools/ui-tests/taskSG2_1.py`.
- 28 Nov 16:07 UTC: **SG2-2 released**, v0.307: G1 lanes in the Split sheet, P1 draft stretch, F1 scan. Test `tools/ui-tests/taskSG2_2.py`.
- 28 Nov 16:15 UTC: **SG2-3 released**, v0.309: S1 card with a strip per stem, hooks for lanes F and G. Test `tools/ui-tests/taskSG2_3.py`.
