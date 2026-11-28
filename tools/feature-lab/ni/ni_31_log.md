## 28 November 2026, v{V}: task NI-31, high-pass hints with a one-click cut (lane D, the AE3 pick X18)

X18 is complete. Edit script `tools/feature-lab/ni/ni_31.py` with `ni_31_block.js` (anchored; needs NI-9), test `tools/ui-tests/taskNI_31.py` (23 checks, all pass).

First, the scheduling chat's request of 12:36 UTC (the Loss button's id): already done on main. Lane H gave it the id `mixer.master.monoLoss` in v0.295 (XT-DL3, `docs/ids.md`), and NI-5c with the Fractals export fix went out in v0.299. On v0.299 `taskXT_DL1.py` 21/21 and `taskXT_DL2.py` 24/24.

### Built
- **A window "High-pass hints"**: main menu (right-click the logo: High-pass hints…), command `ni.hpHints`. Suggestions only: nothing is cut until you click.
- **One row per track with level under a line it does not need**: "3.6 % under 150 Hz, a usual line for a sound that is not a kick or a bass", with a button "Cut under 150 Hz".
  - **The line**: for a track with notes, 0.6 times the frequency of its lowest note (so its fundamental keeps its level), at most 300 Hz; for a track without notes (audio), 150 Hz.
  - **A hint** when at least 1 % of the track's level sits under the line. An audio track with more than 20 % there is left alone ("much of its sound is low: probably needed").
  - **Never**: kicks, basses, subs, drum kits (they may hold the kick), tracks that play a bass line (the kick and bass lab's scores), lines under 40 Hz. The window says which tracks it left alone and why.
- **The cut**: one undo step. It switches on the high-pass band of the track's Pro EQ (raised, never lowered) or puts a new Pro EQ first in the chain: 12 dB per octave at the line, at the band's lowest Q. A second click at the same line does nothing.
- **Measured** from NI-3's per-beat bands on up to four stretches of 24 beats per track where it plays, spread over the song. Measured again 0.8 s after an edit settles while stopped; nothing runs while the window is closed.
- `NI_HOOKS.hpHints` (`open()`, `measure()`, `cut(id, hz)`, `line(track)`) for NI-11 Ask the mix and any lane that wants the hints.

### Found on the way (lane D's own NI-3, for the scheduling chat)
- **Analysing a whole long song can crash the page.** On Fractals (1152 beats, 26 tracks: 1274 pieces of 24 beats), the headless test browser's page crashed after about 1220 renders. The renderer's memory grew by about 5 MB per piece (1 GB to 2.2 GB within 2 minutes) while the JavaScript heap stayed at 86 MB, so it is native memory of the offline renders (`renderMixChunked`, lane K's), not lane D's caches. Forcing garbage collections with large throwaway buffers did not help.
- **Affected**: NI-8's "Whole song" switch, NI-4's frequency map and NI-6's energy arc on long songs. NI-31 avoids it by measuring at most four pieces per track.
- **Not yet checked**: whether the desktop app crashes too. Its renderer may have more room.
- **Next for lane D**: a cap or a pause between pieces in NI-3. Lane K may want to look at whether offline contexts are released.

### Checked
- `taskNI_31.py` 23 of 23. The test song:
  - Pad (a 440 Hz tone with a 50 Hz rumble 15 dB under it) gets the one hint: 3.6 % under 150 Hz (3.1 % in theory, measured 3.6 %).
  - Clean (1 kHz) and Keys (a saw on C4 to C5, line 157 Hz) get none. Bass is skipped as a bass, Loop as probably needed.
  - The cut is one undo step and puts a Pro EQ first with the 12 dB/oct high-pass at 150 Hz: the rumble is 18.6 dB lower, the 440 Hz tone +0.5 dB. Undo gives a bit-identical render.
  - An existing Pro EQ is reused. Idle does nothing. Tooltips; no em dashes; no console errors.
- On Fractals: hints for Toms (13 % under 50 Hz, under its lowest note E2) and Vocals (1.6 % under 150 Hz); Kick, Bass, Crash (drum kit) and Acid (bass line) left alone.
- Lint clean, `taskXT_DL1.py`, `taskXT_DL2.py`, Fractals levels and the start-up smoke test: see the release check below.
- Screenshots looked at: the test song, Fractals, the Light level.

### Limits and what only the user can judge
- **Try it**: right-click the logo, choose High-pass hints…, and listen to a hinted track before and after its cut (Undo takes it back). Some sounds need their low end. The 1 % and 20 % lines and the 150 Hz line for audio are first guesses.
- **The Pro EQ's high-pass rises a little above its corner**: about +0.5 dB at three times the cut frequency, even at its lowest Q (0.3). The browser reads a high-pass Q in dB, so no band setting is flat. A flat (Butterworth) choice would be a small change in the EQ (lane I or L).
- **Returns are not checked**: NI-3 measures tracks, and a return's sound comes from the sends.

### Left
NI-7b (X23 gain staging check), NI-10a and b (I7 draw the arc), NI-11a and b (I31 Ask the mix), NI-12 and on (control tape, Time Machine, undo here, habits, blind shoot-out, listening lenses, ear-fatigue, morph pad, phrase rings, activity glow, variations, transitions, explain mode, recipe cards, fill the gap); NI-20b and NI-25a/b stay gated on lane C (F29, F25a). Also: the NI-3 whole-song memory problem above.
