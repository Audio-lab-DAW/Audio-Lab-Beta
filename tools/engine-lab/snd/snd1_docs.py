"""Task SND-1 (lane L): the release's docs (backlog-log entry, the 'Where it stands' line, the plan's table, the update note).
Re-runnable after a rebase:  python3 tools/engine-lab/snd/snd1_docs.py <version> <previous version>"""
import sys, os, re
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..')
V = sys.argv[1]; PREV = sys.argv[2]  # the version on main before this release
def rd(p): return open(os.path.join(ROOT, p), encoding='utf-8').read()
def wr(p, s): open(os.path.join(ROOT, p), 'w', encoding='utf-8').write(s)

# 1 the plan's table
p = 'docs/sounds-build.md'; s = rd(p)
s = re.sub(r'\| SND-1 \| B37, N5 \| (.*?) \| [^|\n]* \|\n',
           lambda m: '| SND-1 | B37, N5 | %s | **done**, v%s (28 Nov): new device Filter (7 models, drive inside, 2x), the Auto Filter\'s Hi-Fi models; Classic bit for bit |\n' % (m.group(1), V), s, 1)
assert ('**done**, v%s (28 Nov): new device Filter' % V) in s
wr(p, s)

# 2 Where it stands
p = 'docs/device-backlog-2026-11-25.md'; s = rd(p)
L = ('- Task SND (built-in sounds, lane L, the user\'s AE4 picks: everything, B1 to B37 and N1 to N6, one step per run): **step SND-1 done**, v%s: '
     'a new effect Filter (Tone & colour) on the shared kit: Ladder 24, Diode 24, MS-20 12, SVF 12 and 24, Comb and Formant, drive inside the filter, '
     'every value smoothed (20 ms), 2x oversampling (Off to save CPU), 14 presets; the Auto Filter gets Hi-Fi models (a new Auto Filter starts with Hi-Fi on; '
     'every saved one stays off and renders bit for bit) and Ladder, Diode and MS-20 types; aliasing of full drive -29.2 dB (Classic) to -56.2 dB (Hi-Fi). '
     '**Step SND-0 done**, v0.281 (the shared DSP kit). Next: SND-R (one random stream per device), then SND-2 Compressor v2. Plan: `docs/sounds-build.md`.\n') % V
a = s.index('- Task SND (built-in sounds'); b = s.index('\n', a) + 1
s = s[:a] + L + s[b:]
wr(p, s)

# 3 update note (newest on top)
p = 'desktop/update-notes.txt'; s = rd(p)
N = ('New effect, Filter (Tone & colour): seven filter models (Ladder, Diode for acid, MS-20, clean 12 and 24 dB, Comb, Formant vowels) '
     'with drive inside the filter and smooth sweeps. The Auto Filter has a Hi-Fi switch: on for new ones (cleaner when driven, plus Ladder, Diode and MS-20 types), off for your saved songs, which sound as before.\n')
if not s.startswith(N): s = N + s
wr(p, s)

# 4 backlog-log entry
p = 'docs/backlog-log.md'; s = rd(p)
H = '## 28 November 2026, v%s: task SND-1, Filter v2 and the Auto Filter\'s Hi-Fi models (built-in sounds, lane L, B37 and N5)' % V
E = H + '''

The second step of the user's AE4 picks (everything). B37: "Filter v2 on the shared filter set, and the Auto Filter's models". Built on the kit of SND-0. Built and tested on 27 Nov (22:49 UTC) while the release freeze held `index.html`; released this run on main v%(prev)s.

### Built
- Processor `al-snd-filter` (registered in the worklet module by `sndFltWL`, the core `sndFltCore` shared with the main thread): the kit's Ladder 24 (Moog style, driven Huovilainen stages), Diode 24 (303 style), MS-20 12 (Sallen-Key, driven feedback), SVF 12 and SVF 24 (Butterworth at resonance 0), Comb (feedback, or negative feedback for Hollow) and Formant (a e i o u), plus a +12 dB bell for the Auto Filter's Peak. Drive is inside the filter; cutoff, resonance, drive, mix, output and vowel glide per sample (20 ms); 2x oversampling by the kit's halfbands, with the dry part of the mix through the same pair so a mix under 100 %% does not comb; sleeps after 1 s of silence in and out (zeros, no work) and wakes on sound.
- New effect **Filter** (`filter2`, group Tone & colour): Model, Mode (low-pass, band-pass, high-pass, notch, peak), Oversampling 2x or Off; dials Cutoff, Resonance, Drive, Vowel, Mix, Output; 14 presets in three groups (Low-pass, Other shapes, Comb and vowels); the display draws the analog curve of the setting (`sndFltResp`; drive not shown); a tooltip on every menu and dial. The old Low-pass filter (`filter`) is untouched.
- **Auto Filter Hi-Fi** (the `q` field of lane N's switch, labelled Hi-Fi): a saved Auto Filter has no `q` and stays Hi-Fi off, its old biquads bit for bit; a new one starts Hi-Fi on (the AE1 rule: new devices on); presets carry no `q`, so picking one keeps the switch. Hi-Fi on runs the sound through `al-snd-filter` (each type mapped to a kit model: Low-pass 24 to SVF 24, Formant to Formant, Comb to Comb, and so on) with the LFO and the envelope follower still moving the cutoff; the Type list gains Ladder, Diode and MS-20 (Hi-Fi only). Hook for the frame: the switch is a plain `select[data-x="q"]`; lane N's SQ1, when released, can take it over (same field and values).
- Edit script `tools/engine-lab/snd/snd1_edit.py` (block `snd1_src.js` before `askChoice`, one anchor in the Auto Filter's node); docs script `snd1_docs.py`.

### Measured (before: main v%(prev)s without the block; after: this build)
- `tools/ui-tests/taskSND_1.py`: 22 of 22 on this build (the worklet gives the same bits as the core for 30 cases, every model at 2x and Off, with jumps and a stereo part; a 200 Hz to 5 kHz jump glides, 63 %% in 18.7 ms; sleep after 1.01 s, wakes; menus with tooltips; a model change reaches the processor; Auto Filter q rules above; Light screenshot; no console errors). `tools/engine-lab/snd/kit_test.py` 43 of 43.
- Old projects (`snd1_measure.py ... classic`): 15 Auto Filter presets in Classic and the old Low-pass filter at two settings give the same level and checksum before and after, except that the Classic Auto Filter's Vowel and Talk presets change checksum from one render to the next on the same build (the level never moves, -27.84164 and -26.93009 dB; seen on v%(prev)s without the block, two runs, two hashes): the Classic formant path is not repeatable, which is older than this step. Fractals Kick -19.05560 dB (fb577dd5202b), Bass -35.48685 dB (392ec52590c7) at master -10 dB, measured on this build by the release gate's export check; every repeatable export line (9) bit-identical to v0.250; Drum kit, Plant, Sampler and Sampler grains are not repeatable on either build, so not compared (release gate step e passed).
- Response against the analog curve, 30 Hz to 8 kHz (max deviation): ladder 0.13 dB, diode 0.13, MS-20 0.40, SVF 12 0.40, SVF 24 0.12, formant 0.21 dB; comb 3.2 dB (its damping one-pole is not in the analog curve).
- Aliasing of a 4.5 kHz sine at -3 dBFS with full drive (cutoff 18 kHz): Auto Filter Classic -29.2 dB, Hi-Fi -56.2 dB; Filter ladder 2x -53.3 / Off -30.2, diode -49.6 / -28.7, MS-20 and SVF 12 -55.6 / -32.4 (both use the same input drive at resonance 0).
- Cost (offline, %% of a core at 48 kHz stereo): Auto Filter Classic 2.3, Hi-Fi 4.1 (4.98 with the LFO); Filter at 2x: ladder 2.9 (driven 6.4), diode 2.4, MS-20 2.4, SVF 1.9 to 2.0, comb 3.2, formant 2.5; ladder Off 0.8; the old Low-pass filter 0.09. v1 (Classic) cost unchanged. Nothing runs while idle.
- Release gate on this build (`gate.py --here --skip-ui --quick`): every step passed: lint clean; start-up smoke test in the desktop app clean in all 14 MIDI scenarios; frame times p50 16.7 ms, p95 50.0 ms (reference the same); windows 19 checks; the Fractals levels and exports.
- A/B renders (`tools/engine-lab/snd/renders/`, 44.1 kHz): `snd1_afilt_<preset>_classic` against `_clean` for lpslow, acid, wobble, rolling, talkb (listen to the acid and wobble ones: the resonance sings without the gritty fold-back); `snd1_filter2_<preset>` for warm, acid, ms20, butter, comb, vowo.

### For NB (native port)
Port `sndFltCore` with the kit (`snd_kit.h`): the Engine's per-block targets (float32 AudioParam values read once per block, `Math.log` of the cutoff, `Math.exp` for the output gain), per-sample smoothing, the prewarp (`ieee754::tan`), the model switch and the 2x pair; the sleep counter (1 s of input and output below 1e-9, then zeros). Test: the 30 cases of `taskSND_1.py` (noise seed 4242, 8192 samples, the jumps at blocks 24 and 40) bit for bit. The Auto Filter in Hi-Fi feeds the same engine; in Classic nothing new to port.

### Left
SND-R next (one random stream per device, the user's D2), then SND-2 Compressor v2 (B26) and on as `docs/sounds-build.md` lists. For lane N (SQ1): the Auto Filter's `q` is set and read by `sndAfClean`; when the Quality switch is released, its per-project "Hi-Fi everywhere" sets `p.q` and rebuilds the node, as the device's own menu does.
''' % {'prev': PREV}
if H not in s:
    s = s.rstrip('\n') + '\n\n' + E
wr(p, s)
print('SND-1 docs done', V)
