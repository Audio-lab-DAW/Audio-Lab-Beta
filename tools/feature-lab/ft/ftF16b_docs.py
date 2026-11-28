#!/usr/bin/env python3
"""docs for task FT-F16b; run in the repo root: python3 docs_f16b.py VERSION GATE_LINE"""
import sys
V = sys.argv[1]; GATE = sys.argv[2]
def rw(p, fn):
    s = open(p, encoding='utf-8').read(); t = fn(s); assert t != s, p; open(p, 'w', encoding='utf-8').write(t)

LOG = f"""## 28 November 2026, v{V}: Volume Shaper, part 2: started by notes or hits, up to three bands (task FT-F16b, lane C)
Step FT-F16b of `docs/features-build.md` (starred card F16, `docs/research-features-gap.md` section 4 "RF-F16 Volume shaper"). Built and tested by the run of 27 Nov 22:40 UTC, which pushed the edit script and the test (commit 06e2918) but could not push `index.html` during the release freeze; this run (28 Nov, fired 00:35 UTC) re-ran the edit script on v0.294, tested again and released it after the next freeze. Edit script `tools/feature-lab/ft/ftF16b.py` (replaces lane C's own F16a worklet string and its node stretch with `ftF16b_wl.js` and `ftF16b_node.js`, two anchored lines of the F16a display, then `ftF16b_block.js` after the F16a hook line; every anchor asserted unique), test `tools/ui-tests/taskFT_F16b.py` (38 checks).

### Built
- **Start** (new first row of the Volume Shaper): **On the bar lines** (as in v0.293), **On notes of a track** or **On hits of a track**.
  - *On notes*: the notes of another track start the curve (a ghost kick: a muted MIDI track whose notes only start the curve). Every note, or **Only** one note (the kick of a drum kit; the menu lists the notes that track uses). Read from the song's clips (note effects and sustain applied), so the curve starts on the note's sample, the same live and in an export, also when a render starts between notes. A note played live on that track starts it at once.
  - *On hits*: the sound of another track, after its effects and before its fader (the Ducker's tap), starts the curve when it crosses the **Level** (-48 to -6 dB, default -24 dB) after being quiet; found in the worklet per sample. A muted track still works; an export builds the trigger track even when it is not heard.
  - The track menu offers the other tracks (not this one, not groups, nothing that would make a loop). Choosing Start on notes or hits picks a likely track by itself when there is one (a track named Ghost, else Kick or BD). Back on the bar lines the track is put aside (`src0`), so it can sleep again.
- **Bands**: Whole sound, Two bands or Three bands, with **Split** (60 Hz to 500 Hz) and **and** (800 Hz to 8 kHz), and a switch per band (**Low**, **Mid**, **High**) for which bands follow the curve (default: only Low). The crossover adds up flat with no band shaped, and every band shaped is the same as the whole sound, sample for sample.
- The display's caption says what starts the curve and which bands follow it ("1/4 note from each note of Kick, only below 150 Hz").
- Old songs: no new fields, so the curve runs on the bar lines over the whole sound with the same arithmetic: **an export through a Volume Shaper on the bar lines is bit-identical to v0.294** (7367ca30cd6c). New optional fields in the device's `f.p`: `trig`, `src`, `src0`, `nf`, `thr`, `bnd`, `x1`, `x2`, `bs`.
- Wrappers (no other lane's code rewritten): `syncGraph` (lane K) and `mxUtilOff` (lane K, offline taps) to wire the trigger input, `abxKeys` (a render builds a trigger track), `start`, `stop`, `noteOn`. Tooltips on every new control, no em dash.

### Tested (`tools/ui-tests/taskFT_F16b.py`, headless Chromium, 38 checks, all pass)
- Bar lines as before (Psy roll gap's point at 1/16 on frame 4966, next gap 19863 to 24828) and the export bit-identical to v0.294.
- Notes: triggers [1, 2.5, 3.25] in song beats; full before the first note, the curve starts on frame 19863 at 145 BPM; Only C2 ignores note 38; a render starting at beat 0.5 still starts on beat 1; export = dry pad times the curve from each ghost note (5845 samples, worst 7.6e-9), the muted ghost track silent; live, the worklet has the triggers and a live note starts the curve.
- Hits: starts on the sample a hit crosses -24 dB, a -34 dB hit does not; export with the kick track muted gates the pad on each hit; live, the kick's sound feeds the trigger input and its hits start the curve; a track cannot start its own curve.
- Bands: two bands at 150 Hz, Low shaped: 60 Hz at -32.1 dB, 5 kHz at -0.000 dB; three bands, only Mid shaped: mids -41.9 dB, lows and highs pass; flat sum 40 Hz to 12 kHz (worst 0.0000 dB).
- UI: the rows and their menus, one undo step per change, tooltips, saved with the song, no console errors. Screenshots looked at: three bands with Start on hits (Low and Mid lit), the band tooltip, and the Light level.
- Also: {GATE}

### Only the user can test
- Put a Volume Shaper on the rolling bass, set Start to **On hits of a track** and pick the kick: the bass dips on every kick, also when the kick pattern is irregular. Then set **Bands** to Two bands, Split 120 Hz: only the bass's lows duck, the top stays. Or make a muted MIDI track with only kick notes and use **On notes of a track** (a ghost kick).

### Left
- The curve behind the waveform in the arrangement: lane A through `FT_HOOKS.volumeShaper` (unchanged). Lane E may restyle the display, lane L may move the processor into the shared bundle. F17 (multi-shaper) reuses this curve editor and its triggers.
- Next in lane C: **FT-F18a** (kick and bass lab, part 1).

"""
def log(s):
    a = "## 28 November 2026, task WS-0 (lane Q)"
    assert s.count(a) == 1
    i = s.index(a); return s[:i] + LOG + s[i:]
rw('docs/backlog-log.md', log)
rw('docs/features-build.md', lambda s: s.replace("| FT-F16b | Volume shaper, part 2: triggered by notes of another track or by audio, up to three bands. | open |",
   f"| FT-F16b | Volume shaper, part 2: triggered by notes of another track or by audio, up to three bands. | **done v{V}** |", 1))
DB = f"- Task FT-F16b (volume shaper part 2, lane C, starred card F16): **done**, v{V}. The Volume Shaper's curve can start on the notes of another track (a muted ghost kick works, sample exact live and in exports, one note only if wanted) or on the hits of another track's sound (after its effects, a level to cross), and the sound can be split into two or three bands so only the lows (or any band) follow the curve; old songs export bit-identically. Next in lane C: FT-F18a (kick and bass lab)."
def db(s):
    a = s[s.index("- Task FT-F16b (volume shaper part 2, lane C): **in progress**"):]; a = a[:a.index("\n")]
    return s.replace(a, DB, 1)
rw('docs/device-backlog-2026-11-25.md', db)
def un(s):
    return s.rstrip('\n') + "\nVolume Shaper part 2 (v%s): the curve can start on every hit of your kick (Start: On hits of a track) or on the notes of a muted ghost kick track, and with Bands set to two or three only the lows duck.\n" % V
rw('desktop/update-notes.txt', un)
print('docs done')
