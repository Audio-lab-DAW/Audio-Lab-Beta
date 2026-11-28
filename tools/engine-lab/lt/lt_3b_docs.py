"""Task LT-3b (lane J): the release's docs (backlog entry, Where it stands, the plan's status, the update note). Run after the VERSION bump:
  python3 tools/engine-lab/lt/lt_3b_docs.py"""
import os,re
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'../../..'))
def load(p):return open(os.path.join(ROOT,p),encoding='utf-8').read()
def save(p,s):open(os.path.join(ROOT,p),'w',encoding='utf-8').write(s)
def rep(s,a,b):
    n=s.count(a);assert n==1,(n,a[:90]);return s.replace(a,b)
V=re.search(r"const VERSION='([\d.]+)'",load('index.html')).group(1)

ENTRY=f"""
## 28 November 2026, v{V}: task LT-3b, fast MIDI notes for every worklet instrument and the Drum kit (lane J, the user's AE2 pick L5, second part)

Step LT-3b of `docs/latency-build.md` (research id AE2-3). Edit script `tools/engine-lab/lt/lt_3b.py` (unique asserted anchors; it replaces lane J's own LT-3a block and one line of LT-2's placement), test `tools/ui-tests/taskLT_3b_electron.js` (44 checks: the real desktop app under xvfb, then the browser), export check `tools/engine-lab/lt/lt3b_exports.py`. `desktop/` is not changed in this step: the shell's side came with LT-3a.

### Built
- **Every worklet instrument whose live notes are held voices** is now played straight by the worklet when a MIDI keyboard plays it in the desktop app: the pooled engine (Plant, the basic synths, Wavetable), Sampler grains, Emit, Vector grains, Vector FM, Orbit, Sub bass, Psy bass and Crackle. The page works out the played track's note message once for all 128 keys with the instrument's own play function (the batch is taken back before it is sent, so nothing plays), and the worklet only puts in the time, the tag and the velocity: the sound is the engine's own, the voice handling, release and stealing too. It is worked out again when the sound changes (a click or key on the page, a controller message, a note the page sees with a changed sound).
- **The Drum kit:** a small worklet player of lane J's own (`al-lt-drum`) plays the kit's 16 pads from the same rendered pad buffers the page plays (`PADBUF`, `kickRender`), with the pad's level and pan (the StereoPanner's equal-power law), the open hat cut by the next hat (6 ms), a kick cut by the next kick (4 ms), and the key-up fade of the page's path. Pads still being rendered, and keys outside the 16 pads, are left to the page. The pads still light up.
- **Left to the page, as before:** Acid (slide and accent need the page), Venom (an engine per note), Bouncing ball (its display follows each ball), the classic Sampler and the Kick designer (built-in nodes), a locked instrument, and any track with a MIDI effect or a chord device on.
- **Recording placed by the MIDI time stamp** (browser and desktop): a note from a MIDI keyboard is placed by its Web MIDI event's time stamp, when it arrived, not by when the page got to it (LT-2 placed key presses by their key event's time but MIDI notes by the page's time). Up to a second late is corrected.
- **The Settings row "Fast MIDI notes"** (desktop app only, on by default, under the Playing buffer rows; `LT_HOOKS.audioRows` and the settings table, row id `fastMidi`, key `UI.ltFast`), with a tooltip.
- **The page's check sits outside every other voiceOn wrapper:** instruments add their own wrappers while the app starts, after lane J's script, and one that answers a key itself would have played a fast note a second time (found in this step's test: Plant, Emit and the others played twice before the fix; only the first LT-3a instrument kinds were safe). `ltFastWrap` puts it back on the outside when a fast track is set up, keeping the other wrappers' flags.
- `LT_HOOKS.fastNotes()` now also reports each fast track's kind (`al-poly`, `al-orb`, `kit` ...) and why a played track was left to the page.

### Measured (build machine, Electron 45 under xvfb, Linux output clock; before = the page's own path on the same build)
- Note to the voice's first sample while the page runs a 200 ms long task, median of 6: **Drum kit 181.4 to 41.9 ms, Orbit 185.3 to 40.1 ms** (LT-3a's Lead: 185 to 40 ms). Both include about 30 ms of headless Linux output latency.
- Fast note against the page's own note, same key and velocity, peak at the track's input: Plant +0.22, saw +0.41, Wavetable 0.00, Sampler grains -0.42, Emit 0.00, Vector grains 0.00, Vector FM +0.04, Orbit -0.69, Sub bass 0.00, Psy bass 0.00, Crackle +0.21 dB (the ones that move have random parts or a free-running LFO); Drum kit kick, snare, clap, closed hat, open hat, crash all 0.00 dB with the same take of each pad (the page and the player each pick one of three takes at random). The open hat is cut by a closed hat (0.017 to 0 RMS 210 ms on).
- **Recording while the page is busy for 150 ms after each press** (browser, the Fractals Lead, 8 presses): **before (v0.314) 150.0 ms late (median; worst 154.5), after 0.1 ms (worst 0.15 ms)**.
- `taskLT_3b_electron.js` 44 of 44; `taskLT_3a_electron.js`, `taskLT_1.py`, `taskLT_2.py` again on this build (results below); lint clean; the release gate's quick run (below).
- **Exports unchanged.** `tools/engine-tests/export_same.py` on this build: Fractals Kick -19.05560 dB (fb577dd5202b), Bass -35.48685 dB (392ec52590c7) at master -10 dB; -9.75669 (0496bb147f6c) and -25.48699 dB (09e0415bec5e) at 0 dB; Saw, Pad, Acid, Wavetable, Venom identical to v0.314. Plant, Sampler, Sampler grains and Drum kit change from one page load to the next on v0.314 too. The newly wrapped engines: `lt3b_exports.py --toggle` renders each line in the same page with lane J's worklet piece and without it: Wavetable, Sampler grains, Emit, Vector grains, Vector FM, Orbit, Sub bass, Psy bass, Crackle and Bouncing ball identical (Plant and the Drum kit are not repeatable even on one page). Emit and Vector grains differ from one page load to the next on v0.314 as well (-18.47 and -17.54 dB for Emit on two loads): their sounds are made with the page's unseeded random numbers, older than this step.

### Only the user's Mac can prove
- The Push 1 and the nanoKEY over USB through CoreMIDI, with a drum kit and the other instruments, while the arrangement scrolls or a project loads. **It needs a new desktop app** (LT-3a's `main.js`, `preload.js` and `lt-midi.js`, task MB1's build); in an installed app that only downloads `index.html` the page's path plays, nothing breaks.

### Left
- LT-3 is complete. Next: LT-4 (sleep idle tracks, L8). Not in this step: the end of a recorded note still comes from the page's time at key-up (a long task while a key is let go makes the note longer); the classic Sampler and the Kick designer could get the drum player's path later.
"""

b=load('docs/backlog-log.md')
if f'v{V}: task LT-3b' not in b:
    save('docs/backlog-log.md',b.rstrip('\n')+'\n'+ENTRY)

d=load('docs/device-backlog-2026-11-25.md')
a="**step LT-3b built and tested** (28 Nov: fast MIDI notes for every worklet instrument and the Drum kit, recording by the MIDI time stamp, the Settings row; taskLT_3b_electron 44/44 on v0.314; waits for the release gate's freeze of 16:41:15 UTC; this sentence is replaced when it is released)."
if a in d:
    d=rep(d,a,f"**step LT-3b done**, v{V}: fast MIDI notes for every worklet instrument whose notes are held voices (Plant, basic synths, Wavetable, Sampler grains, Emit, Vector grains, Vector FM, Orbit, Sub bass, Psy bass, Crackle) and the Drum kit (a worklet pad player); note to sound during a 200 ms long task 181 to 42 ms (Drum kit), 185 to 40 ms (Orbit); recorded MIDI notes placed by their time stamp (150 ms late while the page was busy, now 0.1 ms); the Settings row Fast MIDI notes; needs a new desktop app. LT-3 complete. Next: LT-4.")
    save('docs/device-backlog-2026-11-25.md',d)

l=load('docs/latency-build.md')
a="| LT-3b | AE2-3 | L5 | desktop: every worklet instrument, drums, recording and the read-out; the Electron proof | claimed (28 Nov) |"
if a in l:
    l=rep(l,a,f"| LT-3b | AE2-3 | L5 | desktop: every worklet instrument, drums, recording and the read-out; the Electron proof | **done**, v{V} (28 Nov): 11 instrument kinds and the Drum kit played by the worklet; long task 181 to 42 ms (kit), 185 to 40 ms (Orbit); recorded MIDI notes 150 to 0.1 ms off while the page is busy |")
    l=rep(l,"| LT-4 | AE2-5 | L8 | sleep idle tracks | |","| LT-4 | AE2-5 | L8 | sleep idle tracks | next |")
    save('docs/latency-build.md',l)

u=load('desktop/update-notes.txt')
line=f"Fast MIDI notes (v{V}): in the next desktop app every instrument that plays held notes and the Drum kit sound straight from a MIDI keyboard, even while the app is busy; recorded MIDI notes now land where you played them. Settings, Fast MIDI notes."
if f'(v{V})' not in u:
    save('desktop/update-notes.txt',u.rstrip('\n')+'\n'+line+'\n')
print('docs for v'+V)
