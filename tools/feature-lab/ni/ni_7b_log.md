## 28 November 2026, v{V}: task NI-7b, the gain staging check (lane D, the AE3 pick X23, folded into I13)

X23 is complete. Edit script `tools/feature-lab/ni/ni_7b.py` with `ni_7b_block.js` (anchored; needs NI-31 in the file), test `tools/ui-tests/taskNI_7b.py` (25 checks, all pass). Built on v0.314 + NI-31 on 28 Nov between 17:25 and 18:00 UTC while the release gate's freeze of 16:41 held `index.html`; released together with NI-31.

### Built
- **A window "Gain staging"**: main menu (right-click the logo: Gain staging…), command `ni.gainStaging`. It only reads; nothing in the song changes.
- **Every track that plays in the range** (NI-7's: the loop, or the 8 bars around the playhead) is measured with NI-7's one-track render: the peak after its clips or instrument, after each device that is on, and after its fader and pan. Nothing is added to the live path.
- **One line per problem**, the worst first, each with the track's colour; a click selects the track, **Journey** selects it and opens its level journey (NI-7):
  - **hot** (red): a peak over −1 dBFS anywhere before the fader, named by where it goes: "hot into Compressor: peaks at +6.0 dBFS after Pro EQ", "hot into the fader: peaks at +2.9 dBFS after its clips"; the tooltip says what to turn down and by how much (the overshoot plus 0.5 dB, in half dB steps) and to raise the fader by the same
  - **quiet** (amber): under −30 dBFS going into a device that reacts to level (compressor, drive, OTT, limiter, gate, clipper, multiband dynamics...): "quiet into Compressor: peaks at −34.0 dBFS"
  - **barely heard** (amber): under −40 dBFS after the fader
- **The master**: its peak over the same range after its own chain and the app's headroom setting, without the safety limiter (a direct render of the mix), shown as "Master: peaks at −12.6 dBFS, 12.6 dB of headroom". It is a problem line when it is over −1 dBFS and no limiter or clipper sits on the master; with one, the line says "(after its Limiter)".
- A clean mix says "Nothing to fix". Measures again 0.8 s after an edit settles while stopped; nothing runs while the window is closed; an edit or a project change during a run stops it.
- `NI_HOOKS.gainStaging` (`open()`, `measure(o)` with the tracks, problems and master), `NI.gs.judge(t, journey)` for NI-11 Ask the mix.

### Checked
- `taskNI_7b.py` 25 of 25. The test song: Hot (a sine at +2.92 dBFS, no device) "hot into the fader … +2.9 dBFS after its clips", turn down 4.5 dB; Hot2 (−6.02 dBFS, Pro EQ +12 dB, Compressor) "hot into Compressor … +6.0 dBFS after Pro EQ"; Quiet (−33.98 dBFS into a Compressor) −34.0; Faint (−46.02 dBFS) barely heard; Clean nothing; exactly those four lines, numbers within 0.05 dB; the master's peak equals a direct render of the mix; Hot's clip gain down 4.5 dB removes its line; a master over −1 dBFS is the first line ("it clips"), not with a Limiter on the master; a clean mix lists nothing; clicks select, Journey opens the level journey of that track; idle does nothing; a render bit-identical before and after; tooltips; no em dashes; no console errors.
- On Fractals (bars 29 to 36): 14 tracks measured; Kick +0.9 dBFS and Impact −0.4 dBFS into their faders, after their Pro EQs; the master −3.6 dBFS after its Soft Clipper.
- `taskNI_31.py` (NI-31, built in the run before) passes with NI-7b in the file; lint clean (2620 top-level functions); Fractals levels unchanged (measured, `export_same.py` on v0.314 + NI-31 + NI-7b): Kick −19.05560 dB (fb577dd5202b), Bass −35.48685 dB (392ec52590c7) at −10 dB; −9.75669 dB (0496bb147f6c) and −25.48699 dB (09e0415bec5e) at 0 dB.
- Screenshots looked at: the test song, a clean mix, Fractals, the Light level.

### Limits and what only the user can judge
- **Try it**: right-click the logo, choose Gain staging…, with the playhead in a loud part (or a loop over the drop). Hot lines are the ones to fix first; a kick or a bass hot into its own fader, as on Fractals, is common and harmless in this app (it works in floating point), but devices after it hear it that hot.
- The −1, −30 and −40 dBFS lines are first guesses. Which devices count as level-sensitive is read from their names.
- Groups and returns are not measured on their own (their sound comes from other tracks); sends and sidechains are not in a track's line. The range is at most 16 bars (NI-7's), because a whole long song can crash the page (see NI-31's log).

### Also found in this run (for NI-31, not changed here)
- Run in parallel with the run that built NI-31, this run built the same step once more before it saw that one's push (its copy was dropped). Two points from that copy, for whoever next touches NI-31: on Fractals the Crash track is a drum machine that plays only its crash pad, so "drum kit, left alone" could be narrowed to drum machines that play a kick pad; and returns could get an estimated hint from what is sent into them (each sender's bands times its send level squared).

### Left
NI-10a and b (I7 draw the arc), NI-11a and b (I31 Ask the mix), NI-12 and on (control tape, Time Machine, undo here, habits, blind shoot-out, listening lenses, ear-fatigue, morph pad, phrase rings, activity glow, variations, transitions, explain mode, recipe cards, fill the gap, preset galaxy); NI-20b and NI-25a/b stay gated on lane C (F29, F25a). Also: the NI-3 whole-song memory problem.
