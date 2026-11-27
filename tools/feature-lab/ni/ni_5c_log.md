## 27 November 2026, v{V}: task NI-5c, the clash measure that knows the beat (lane D, AE3 pick X16, improves I12)

The AE3 picks for lane D are now in the plan: NI-5c is X16, NI-7b is X23, NI-31 is X18, and NI-20b is X27, which waits for lane C's F29 scenes. X16 is starred and improves the masking cables that already exist, so it ran first. Edit script `tools/feature-lab/ni/ni_5c.py` with `ni_5c_block.js` (anchored; needs NI-8), test `tools/ui-tests/taskNI_5c.py` (22 checks, all pass). It was built and tested on v0.293 while the release gate's freeze held `index.html`.

### Built
- **Timing for every clash cable.** NI-5a finds clash candidates from the per-beat average, and in a rolling bass (KBBB) that average flags every kick and bass. Kick and bass share 40 to 120 Hz but take turns inside each beat. Now each candidate is checked in time:
  - both tracks are rendered offline on their own over the 8 beats around the playhead (NI-7's one-track render, after fader and pan, 22.05 kHz)
  - each render is split into NI-5a's 1/3-octave bands (two cascaded band-passes) and the level followed every 11.6 ms
  - a moment counts when both are loud in the clash's band at once: each within 10 dB of its own top in those bars, and within 12 dB of each other
  - the share = those moments / the moments either one is loud
- **Under 25%: "take turns".** The cable is drawn thin and dashed and labelled "Kick and Bass take turns, 48 to 76 Hz". It is not counted in the legend, and it sorts after the real clashes.
- **A real clash:** the cable's thickness is scaled by the share.
- **Tooltips:** each one gives the share and says the number is an estimate.
- **The clash card has a pair view:** both tracks in the band over the 8 beats, with beat and bar lines (LOOK grid tokens), the moments they are loud together shaded magenta, and "Loud together 9% of the time: they take turns".
  - A take-turns card offers no fix ("Nothing to fix here: they already take turns"). In a low band it offers the kick and bass lab instead.
  - A real clash keeps NI-5b's two fixes.
- **Kept and cheap:**
  - The timing is kept per track and window under NI-3's piece key, so an edit measures again only the edited track.
  - It is measured in the background by NI-3's rules: not during an export, and while playing only with a quiet CPU.
  - Nothing is worked out while the playhead stands still.
  - Nothing is added to the audio path.
  - `NI_HOOKS.clashTiming` (`gate(c, beat)`, `get(track, window)`).

### Checked
- **Test song** (145 BPM, 16 beats):
  - **Kick**: a 55 Hz hit on every beat, 110 ms with a 70 ms decay.
  - **Bass**: 55 Hz notes on the three 16ths after each kick, 85 ms each.
  - **Pad** (400 Hz) and **Lead** (410 Hz, 2 dB quieter), all through.
- **Results**:
  - The per-beat average flags both pairs. With the timing, Kick and Bass are loud together **9%** of the time ("take turns"), Pad and Lead **100%**. The real clash comes first, and the legend counts 1.
  - The take-turns cable is dashed and 1.2 px wide; the Pad and Lead cable is 5.4 px.
  - Both cards show the pair view and the share. The take-turns card offers the kick and bass lab, not a fix; the Pad and Lead card keeps the two fixes.
  - A second look renders nothing. An edit of Lead's fader renders Lead's window once, and nothing else.
  - The song is unchanged and a render of Bass is bit-identical.
- **Also:** `taskNI_5a.py` 34 of 34, `taskNI_5b.py` 22 of 22. Lint clean. Tooltips on the new parts; no em dashes; no audio nodes; no console errors.
- **Fractals levels unchanged** (`tools/engine-tests/export_same.py` on this build): Kick −19.05560 dB (fb577dd5202b), Bass −35.48685 dB (392ec52590c7) with the master at −10 dB; −9.75669 (0496bb147f6c) and −25.48699 dB (09e0415bec5e) at 0 dB. One of two runs read the Bass at 0 dB as −26.74 dB, the known run-to-run noise of that line, noted in NI-3.
- **Not run:** the start-up smoke test of the release gate cannot run on this cloud machine, because the Electron download is blocked. {GATE}
- **Screenshots looked at**: the mixer with both cables (normal and Light level), the take-turns card and the clash card.

### Limits and what only the user can judge
- The window is 8 beats; a pair that clashes only in another part of the song shows its numbers where the playhead is.
- The 25% line and the 10 dB "loud" line are first guesses.
- **What to try**: turn Clashes on in the mixer's cable lane on a rolling-bass drop. The kick and bass cable should now say "take turns" if the bass leaves room for the kick. Click it to see the two curves. Say whether 25% is the right line.

### Left
Next: NI-9, the harmonic ruler (I5); then NI-31 (X18 high-pass hints), NI-7b (X23 gain staging check).
