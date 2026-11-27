## 27 November 2026, v{V}: task NI-8, the mono-loss map (lane D, idea I4)

Idea I4 is complete. Edit script `tools/feature-lab/ni/ni_8.py` with `ni_8_block.js` (anchored; needs NI-7), test `tools/ui-tests/taskNI_8.py` (32 checks, all pass). The step was claimed in the plan before it started.

### Built
- **A window "Mono loss"** (the app's floating window: moves, resizes, remembers its place). It opens from:
  - the main menu (right-click the logo: Mono loss…)
  - the command `ni.monoLoss`
  - a small **Loss** button next to Mono, Dim and L↔R on the master strip
- **One row per track that plays** in the range (not groups, returns or muted tracks):
  - a band strip from 20 Hz to 20 kHz (1/6 octave, NI-3's bands), each band coloured by how much of that track's level is lost in mono there: cyan holds, grey −3 dB (wide or one-sided), amber −6 dB (partly cancels), red −12 dB and more (cancels); faint where the band is quiet for that track
  - the whole track's loss in dB (power over its bands)
  - the worst stretch in words, for example "−10.0 dB at 381 to 427 Hz" (amber from 3.5 dB, red from 6 dB), else "wide, nothing cancels" or "holds up in mono"
  - click a row to select the track
- **How the per-band loss is measured**: from NI-3's per-beat mid and side bands (the cache; nothing new is rendered for it): loss = mid / (mid + side) in power, summed over the beats where the track plays. A centred mono sound loses 0 dB, a hard-panned or uncorrelated wide sound 3 dB, out-of-phase content more.
- **Tracks that cancel each other in mono** are joined by a line beside their names, with a sentence under the rows: "Left and Right cancel at 143 to 180 Hz: they cancel out in mono, fine in stereo" (or "in stereo too (−x dB)").
  - Found on their own renders: the 8 loudest tracks of the range, each rendered offline on its own after its fader and pan (NI-7's one-track render, at 22.05 kHz, at most 8 bars).
  - Compared pair by pair per 1/3 octave in a worker: a pair is named where the two together lose at least 3 dB in mono against the sum of their powers, both are within 15 dB of each other, and the band matters for the pair.
- **Hear in mono**: the master strip's Mono switch, from the window.
- **Range**: the loop when it is on, else the 8 bars around the playhead (as the level journey), or the whole song (switch; the pairs are then still checked around the playhead, and the window says which bars).
- **When it runs**: it measures again 0.8 s after an edit or a move settles, only while the song is stopped. A 300 ms check runs only while the window is open. Closing stops it.
- **Hooks**:
  - `NI_HOOKS.monoLoss` (`open`, `measure`, `tracks`) for NI-11 Ask the mix.
  - `NI_HOOKS.mxMon(w)`, called by one added call in the mixer's render after `monPaint()`, adds the Loss button. Whoever rebuilds the master strip keeps that call.
  - NI-7's `NI_jourRender` (lane D's own) learned `taps.raw` and `taps.sr`. Its normal use is unchanged; the test checks this.

### Checked
- **Test song** (audio, 120 BPM, 32 beats):
  - **Pad**: a 100 Hz sine in both channels plus a 400 Hz sine at +1 left and −0.5 right. Its 400 Hz band loses **9.96 dB** (computed −10.0 dB) and its 100 Hz band 0.0 dB. The worst stretch reads "−10.0 dB at 381 to 427 Hz".
  - **Mono** (1 kHz, both channels): 0.0 dB in every band, "holds up in mono".
  - **Left** (150 Hz on the left only) and **Right** (the same sine inverted on the right only): **3.01 dB** each, not flagged. Together they are the **one pair**: they cancel completely in mono and lose 0 dB in stereo. The line joins exactly their two rows.
  - With Right muted, it has no row and there is no pair. With Right playing 2.5 kHz instead, there is no pair and the window says so.
- **Window and controls**:
  - Range: beats 0 to 32 at beat 12; the loop 8 to 24; whole song 0 to 32.
  - Hear in mono switches the master's Mono and back.
  - The Loss button on the master strip opens the window.
  - Idle for 2 s: nothing measured. Closing stops the check.
- **Live path and exports**: a render of Pad is bit-identical before and after the map measured it, and the level journey reads the same numbers before and after.
- **Fractals levels unchanged** (`tools/engine-tests/export_same.py` on this build): Kick −19.05560 dB (fb577dd5202b), Bass −35.48685 dB (392ec52590c7) with the master at −10 dB; −9.75669 (0496bb147f6c) and −25.48699 dB (09e0415bec5e) at 0 dB; the other nine lines the same checksums.
- **Also**: `taskNI_7.py` 24 of 24. Lint clean. {GATE}
- Tooltips on every control, row, column and line; no em dashes in the UI text; no console errors.
- **Screenshots looked at**: the test song; the master strip with the Loss button; Fractals at bars 29 to 36, normal and Light level. In that stretch of Fractals every track holds up in mono (0.0 to 0.4 dB), except the Pad: −2.0 dB, wide. No pair cancels among the 8 loudest.

### Limits and what only the user can judge
- The per-band numbers come from NI-3's renders, which go through the master chain, so a stereo widener on the master shows on every track. The pairs are measured without the master.
- The pairs are checked only among the 8 loudest tracks and only up to 11 kHz (the renders run at 22.05 kHz).
- A track with reverb or chorus reads as "wide" (about −3 dB in its upper bands). That is expected, not a fault.
- **What to try**: open Mono loss on a drop of your own song and look for amber or red stretches. A stereo bass or a doubled pad with a flipped copy shows up there. Then press Hear in mono to hear what the strip shows. Say whether the Loss button on the master strip is the right place, or whether a strip per mixer channel would help more.

### Left
Group U, next: NI-9, the harmonic ruler (I5).
