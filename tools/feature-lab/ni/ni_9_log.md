## 28 November 2026, v{V}: task NI-9, the harmonic ruler (lane D, idea I5)

Idea I5 is complete. Edit script `tools/feature-lab/ni/ni_9.py` with `ni_9_block.js` (anchored; needs NI-5c), test `tools/ui-tests/taskNI_9.py` (27 checks, all pass). Built on v0.297 while the release gate's freeze of 12:35 UTC held `index.html`, released together with NI-5c and the Fractals export fix.

### Built
- **A piano strip along the bottom of every live spectrum view**: the Spectrum device, the spectrum overlay and the Visualizer's spectrum (everything lane E's drawer `INS.spec` draws at its full or middle size; the small mixer-size views get none, there is no room).
  - octave cells with C1 to C9 named where there is room, black keys where a semitone is at least 1.6 px wide, the song key's notes lit as a thin yellow line along the bottom
  - **the five strongest peaks** of the live trace marked on the strip and named above it with note and cents: "A2 0 c", "G♯7 −12 c"; names that would touch go on a second row
  - **amber**: the peak's note is outside the song key (lane C's project key when it exists, otherwise the piano roll's scale and root, as the kick and bass lab reads it); no amber when no scale is set
  - **red, with "rings"**: the pitch keeps sounding for more than a beat after the rest of the sound faded by 6 dB more than it did, and it fades itself (a held note that does not fade is a note, not a ringing resonance); the rest of the sound must have been within 12 dB of the pitch when it started, so the click of a tone starting is not a hit
- **How the peaks are found**: from the bins the view has already read this frame (lane E's shared FFT read, nothing new on the audio side): local maxima standing 8 dB over the 1/6 octave around them, within 54 dB of the loudest, one per 70 cents, refined by a parabola through the top bin and its neighbours (with the analyser's Blackman window that is within about 0.01 bin of a steady tone: 110 Hz reads 110.02 Hz at FFT 8192).
- **Snappy**: the peaks are found at most 8 times a second per view (3 at the Light level), the drawing is a few rectangles and up to five names; nothing is found or drawn when the view is not live (stopped Visualizer, closed overlay) or the ruler is off.
- **Lane E's code is not changed**: `INS.spec` is wrapped once from lane D's block after it is defined (its own function kept as `INS.spec.niBase`); the ruler draws into the view's canvas after lane E's drawer.
- **The switch** (on by default): the main menu (right-click the logo: Harmonic ruler: on / off), the command `ni.harmonicRuler`, a settings row `ni.harmonicRuler` in `NI_SETTINGS` (S4 shape, key `UI.niHr`, page Display, block Analysis) for lane B to show.
- **Hooks**: `NI_HOOKS.harmonicRuler(g, box, peaks, o)` draws a ruler into any canvas (box: x, y, w, h of the strip, lo and hi of the log axis); `NI_HOOKS.harmonicPeaks(an, lo, hi, st)` finds the named peaks of an analyser and keeps their history in `st`. For lane A or lane I if a rebuilt device display wants the ruler, and for NI-11 Ask the mix.

### Changed from the plan
- The plan said the red "rings longer than a beat" would come from NI-3's cache. It is measured on the live trace instead: the cache is per track and per beat, while a spectrum view shows whatever passes through its device or the master, and the live trace needs no background analysis. The cache stays for NI-11.

### Checked
- `taskNI_9.py` 27 of 27: A2 named "A2 0 c" and measured within 0.05 Hz; A4, D♯6 and G♯7 −12 c named right; four peaks and no false ones; in A minor D♯6 and G♯7 amber, A2 and A4 not, and no amber without a scale; steady tones never red; a 200 Hz tone ringing after a noise burst red as "G3 +35 c rings", and not before a beat has passed; off draws and finds nothing while the view plays, on again draws; at most 8 finds a second (measured 3 to 8), 3 at the Light level; the Visualizer (FFT 4096, smoothed) names A2 within 2 c; the hook draws into a plain canvas; a render bit-identical with the ruler on and off; no em dashes; no console errors.
- `taskIN_S.py` (lane E's spectrum): 33 of 34 with the ruler; the one failure ("averaging by time … one time constant", a timing check) fails the same way on v0.297 without lane D's changes (32 of 34 there, the Visualizer's hold check also timing).
- `taskNI_5c.py` 22 of 22, `taskNI_sideb0.py` 6 of 6, `taskXT_DL1.py` 21 of 21 (run alone; with three browsers at once its "one pass is cheap" timing check went over), `taskXT_DL2.py` with `ni.harmonicRuler` listed in `docs/commands.md`; lint clean.
- Fractals levels unchanged (measured, `export_same.py` on this build): Kick −19.05560 dB (fb577dd5202b), Bass −35.48685 dB (392ec52590c7) at −10 dB; −9.75669 dB (0496bb147f6c) and −25.48699 dB (09e0415bec5e) at 0 dB, the references of the newest RG entries; the voice engine lines unchanged.
- Screenshots looked at: the Spectrum device with the four tones (A2 and A4 white, D♯6 and G♯7 amber), with the ringing tone (red "G3 +35 c rings"), with the ruler off, at the Light level; the Visualizer's spectrum docked at the bottom.

### Limits and what only the user can judge
- Try it: put a Spectrum device on the bass or on the master and play; the strongest notes are named under the curve. On a kick, a red "rings" name is a resonance worth a narrow cut; an amber name on a bass is a note outside the key.
- The thresholds are first guesses: 8 dB to count as a peak, 6 dB for "the rest faded more", one beat. Busy full mixes give many peaks; only the five loudest are named.
- Low notes need a fine FFT: at the Spectrum device's 2048 setting a bin is 21.5 Hz wide, so peaks under about 100 Hz may be named a few cents off or merge; 8192 (the default) and up are fine.
- Whether the ruler should be on by default (it is) and whether its strip covers too much of the curve's foot is the user's call; one click in the main menu turns it off.

### Left
NI-31 (X18 high-pass hints), NI-7b (X23 gain staging check), NI-10a and b (I7 draw the arc), NI-11a and b (I31 Ask the mix), NI-12 and on (control tape, Time Machine, undo here, habits, blind shoot-out, listening lenses, ear-fatigue, morph pad, phrase rings, activity glow, variations, transitions, explain mode, recipe cards, fill the gap, NI-29); NI-20b and NI-25a/b stay gated on lane C (F29, F25a).
