"""Task SND-R (lane L): the release's docs (backlog-log entry, the 'Where it stands' line, the plan's table, the update note).
Re-runnable after a rebase:  python3 tools/engine-lab/snd/sndr_docs.py <version> <previous version> <gate summary>"""
import sys, os, re, json
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..')
V = sys.argv[1]; PREV = sys.argv[2]; GATE = sys.argv[3] if len(sys.argv) > 3 else 'see the gate log'
def rd(p): return open(os.path.join(ROOT, p), encoding='utf-8').read()
def wr(p, s): open(os.path.join(ROOT, p), 'w', encoding='utf-8').write(s)

# 1 the plan's table
p = 'docs/sounds-build.md'; s = rd(p)
s = re.sub(r"\| SND-R \| \(the user's D2\) \| (.*?) \| [^|\n]* \|\n",
           lambda m: "| SND-R | (the user's D2) | %s | **done**, v%s (28 Nov): every worklet device its own sfc32 stream from the export seed and its key; same numbers whatever other devices draw and at every block size |\n" % (m.group(1), V), s, 1)
assert ('**done**, v%s (28 Nov): every worklet device' % V) in s
wr(p, s)

# 2 Where it stands
p = 'docs/device-backlog-2026-11-25.md'; s = rd(p)
a = s.index('- Task SND (built-in sounds'); b = s.index('\n', a) + 1
L = ("- Task SND (built-in sounds, lane L, the user's AE4 picks: everything, B1 to B37 and N1 to N6, one step per run): **step SND-R done**, v%s: "
     "one random stream per device (the user's D2): every worklet device draws from its own seeded generator (the project's export seed and the device's key), "
     "so a device's noise, jitter and dither no longer depend on what the other devices draw or on the render block size, and another export seed now changes them; "
     "level unchanged (two Bitcrushers -27.40 dB before and after). **Step SND-1 done**, v0.313 (Filter v2, the Auto Filter's Hi-Fi models); **SND-0 done**, v0.281 (the shared DSP kit). "
     "Next: SND-2 Compressor v2. Plan: `docs/sounds-build.md`.\n") % V
s = s[:a] + L + s[b:]
wr(p, s)

# 3 update note (newest on top)
p = 'desktop/update-notes.txt'; s = rd(p)
N = ('Random parts of the built-in sounds (dither, jitter, noise, grains) now come from one stream per device, so a device sounds the same '
     'whatever the other devices do, and a new export seed gives a new noise pattern. Same level and character.\n')
if not s.startswith(N): s = N + s
wr(p, s)

# 4 backlog-log entry
R = json.load(open(os.path.join(ROOT, 'tools/engine-lab/snd/results_sndr.json')))
p = 'docs/backlog-log.md'; s = rd(p)
H = "## 28 November 2026, v%s: task SND-R, one random stream per device (built-in sounds, lane L, the user's D2)" % V
E = H + '''

The step the user's decision D2 (28 Nov, 00:27 Brussels) put after SND-1: docs/review-native.md A2. The worklet module had one generator (`Math.random` replaced by sfc32 with fixed constants in `wlLoad`) shared by every processor, so the numbers a device got depended on how many every other device drew before it in Chromium's render order, on the render block size and on the silence gate; a native engine with its own graph order, or a parallel one (NR3), could never match it. Under the user's R1 (28 Nov, 14:36: one sound, no v1 kept) there is no version field: every project uses the new streams.

### Built
- Worklet side (`sndRWL`, put at the top of the worklet module by `wlLoad`, after the old shared generator and before every processor, in both load paths): `registerProcessor` is wrapped once; every processor class is registered as a subclass whose constructor makes the instance's own sfc32 stream from `processorOptions.sndSeed` (4 words), and whose `process()` and port message handler set `Math.random` to that stream when they start (only when it is not already, nothing restored, so a song with one random device writes nothing per block). No processor's code changed; every one that calls `Math.random` (Bitcrusher dither and jitter, Vocoder noise and phases, the sampler's grains, the drums and the rest) now draws from its own stream.
- Main thread (`sndRSeed`, `sndRInstall`): every `AudioWorkletNode` made by the app carries `processorOptions.sndSeed` = the 4 words of seedRng's hash of `'sndr|<S.seed>|<key>'` (Fixed seed off in Export: 4 random words, so two exports differ, as the Export page says). The key is `processorOptions.sndKey` when the code that makes the node gives one, otherwise `'<processor name>#<n>'`, n = the nodes of that processor this audio context made before (an offline render builds the graph in project order, so n is the device's place in the song). The worklet runs sfc32 on the words and drops 15 numbers, exactly as `seedRng`, so a device's stream is `seedRng('sndr|'+S.seed+'|'+key)`, checked sample for sample.
- Hook `SND_HOOKS.rseed` (the seed function); any lane can pass `processorOptions.sndKey` (a device id) so a node's stream does not depend on the order nodes are made. Lane K (the graph): passing the device id there would make the stream survive adding a device earlier in the song; not needed for bit identity.
- Edit script `tools/engine-lab/snd/sndr_edit.py` (block `sndr_src.js` before `askChoice`, two anchors in `wlLoad`), docs script `sndr_docs.py`, cost `sndr_cost.py`, renders `sndr_renders.py`.

### Measured (before: main v%(prev)s; after: this build)
- `tools/ui-tests/taskSND_R.py`: %(after)s on this build; %(before)s on the build before (the checks that show the shared stream fail there: a device's numbers move when another draws more, at another block size, with another node made first; the export seed did not reach the worklets, so another seed and Fixed seed off changed nothing in them). Exact: a probe processor reads seedRng's stream for 5120 samples; two Bitcrushers with dither 60-80 %% and jitter 30-50 %%: the second one's output is bit-identical whether the first dithers or not, and at render blocks of 128 and 512; the same seed renders the same twice; Fractals opened and played without console errors.
- Level: two saw tracks through Bitcrushers with dither and jitter, 8 bars: %(rb)s dB RMS before, %(ra)s dB after (peak %(pb)s and %(pa)s dB); only the noise pattern differs.
- Cost (8 Bitcrushers, 20 s offline at 48 kHz, best of 15 runs, both builds side by side): with dither and jitter %(cb).0f ms before, %(ca).0f ms after; without random draws %(pb2).0f ms before, %(pa2).0f ms after. Not worse. Nothing runs while idle (no timer, no per-frame work; the cost is one comparison per processor per block).
- Release gate (`gate.py --here --skip-ui --quick`) on this build: %(gate)s.
- A/B renders (`tools/engine-lab/snd/renders/`, 44.1 kHz): `sndr_crush2_before` against `sndr_crush2_after` (listen: the same grit, a different noise pattern).

### For NB (native port)
NB-R6's per-device streams: each device instance owns an sfc32 state (the same step as `al_crush.h`), set from the 4 seed words the page sends with the device (`processorOptions.sndSeed`; the bridge passes them on) and advanced 15 times; the device draws `(t>>>0)/4294967296` from its own state only. No shared generator. Test: the two-Crusher song of `taskSND_R.py` bit for bit at block sizes 32, 37, 64, 128 and 512, and the probe stream against `seedRng`.

### Left
SND-2 Compressor v2 (B26) next, then SND-3 to SND-19 as `docs/sounds-build.md` lists. Then "built-in sounds complete".
''' % dict(prev=PREV, after='%d of %d' % (R['after']['passed'], R['after']['total']), before='%d of %d' % (R['before']['passed'], R['before']['total']),
           rb=R['renders']['before']['rms'], ra=R['renders']['after']['rms'], pb=R['renders']['before']['peak'], pa=R['renders']['after']['peak'],
           cb=R['cost']['before']['rand'], ca=R['cost']['after']['rand'], pb2=R['cost']['before']['plain'], pa2=R['cost']['after']['plain'], gate=GATE)
if H in s:
    a = s.index(H); b = s.find('\n## ', a + 1); s = s[:a] + E + ('\n' + s[b + 1:] if b >= 0 else '')
else:
    s = s.rstrip('\n') + '\n\n' + E
wr(p, s)
print('SND-R docs done', V)
