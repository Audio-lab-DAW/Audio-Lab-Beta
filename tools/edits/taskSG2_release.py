"""Task SG2 (lane R), the release half of one step. On a fresh main, after `python3 tools/edits/taskSG2_<k>.py index.html` printed the version:
  python3 tools/edits/taskSG2_release.py <k> <version>
Copies the step's test to tools/ui-tests/taskSG2_<k>.py, adds the update note, the backlog entry and the line in docs/stem-split-progress.md
(step 2 and 3 also list the new control ids in docs/ids.md; step 4 writes 'stem split lanes complete').
Then: node desktop/scripts/sync-app.js, the lint, the start-up smoke test, check the freeze, push."""
import sys, os, re, shutil, datetime
K = sys.argv[1]; V = sys.argv[2]; assert K in '1234' and re.match(r'^0\.\d{3}$', V), (K, V)
H = os.path.dirname(os.path.abspath(__file__)); R = os.path.join(H, '..', '..')
def rd(p): return open(os.path.join(R, p), encoding='utf-8').read()
def wr(p, s): open(os.path.join(R, p), 'w', encoding='utf-8').write(s)
ix = rd('index.html')
assert "const VERSION='%s'" % V in ix and ('task SG2-%s' % K) in ix, 'run taskSG2_%s.py first' % K
assert ('SG2-%s released' % K) not in rd('docs/stem-split-progress.md'), 'already released'
shutil.copy(os.path.join(H, 'taskSG2_%s_test.py' % K), os.path.join(R, 'tools', 'ui-tests', 'taskSG2_%s.py' % K))
NOTE = {
 '1': 'Stem splits (v%s): the quick split now works in the background, so AudioLab no longer stops for a moment at every few seconds of the song while it splits; behind the scenes the splitter reports each finished stretch, for the spectrogram loading bar that comes next.',
 '2': 'Stem split loading bar (v%s): after Split the window stays open and shows the spectrogram of every stem filling in as the split gets to that point of the song, under the mix, with an amber line where it is done, the time left, Keep working and Stop; when it ends each stem shows its level and a tick, and Add 3 tracks adds them.',
 '3': 'Stem split card (v%s): Keep working sends a running split to a small card with a strip per stem, the time left, Open and Stop; when it ends the card says what was added, with Undo.',
 '4': 'Audio to MIDI (v%s): Split into stems first shows the stems\' spectrograms filling in while it splits, and each listen row then shows its stem\'s picture.'}[K] % V
s = rd('desktop/update-notes.txt').rstrip('\n') + '\n' + NOTE + '\n'
wr('desktop/update-notes.txt', s)
LOG = {
 '1': """- `sgColsOf` (one 4096-point FFT per lane column, 96 log rows 32 Hz to 16 kHz, Uint8 dB -84..0, row 0 at the top) and `sgColEnds` (a column is final when its whole window is final) are shared by the page and both workers (their source is copied in).
- The neural worker `NEUW` posts `{t:'cols', i, n, s0, s1, pe, fin:[c0,c1], prov:[c1,c2], rows:96, ns, cw, cols}` after every chunk (kept stems only, the draft stretch is the overlap the next chunk cross-fades) and `{t:'st',m:'run'}` once the model is loaded; `neuSeparate(buf,kind,keep,prog,onCols)` passes them on (onCols.cw = columns over the clip), can be stopped (`sgStopNeural`), and makes the stem buffers one per task.
- The quick split runs in a worker (`SGW`: `sgQuickCore` is the old arithmetic, unchanged; `stemSplit(buf,prog,P,onCols)`), one cols message per block; `sgMixCols(buf,cw)` gives the mix's own columns; `sgStopQuick`. `SG_HOOKS.onChunk(job,msg)` for any lane.
- Measured (2-core container, headless Chromium): a 40 s clip's quick split posts 7 messages, the main thread's longest piece of the split is under 10 ms (the old main-thread split paused about 0.45 s per block); the stems are bit-identical to the old main-thread split; the columns equal sgColsOf on the finished stems (0 of 255 steps apart).
- Test `tools/ui-tests/taskSG2_1.py` (neural worker on a stand-in engine and model served by the test, same chunking).""",
 '2': """- G1 in the Split sheet: `stemAsk` resolves with the open sheet, `stemsFor` (rewritten, lane R's) turns it into `sgSheet`: read-out (L2: `.lku` units in amber), the mix lane (grey, drawn at once from `sgMixCols`), one viridis lane per kept stem (`INS.cmap('viridis')`, quiet bins fade into the lane as on the pick page), the amber edge (`--unit`, `--lk-hair`, 120 ms × `--ov-mo`), the chunk at work with the soft scan (F1; a still hatch with Reduce motion, Motion Signal only, still effects or Light mode), the time axis; Keep working / Stop / Add N tracks (ticks per stem, silent ones unticked, levels in dB), Discard.
- P1: draft columns at half strength, repainted when final (none in Light mode). Nothing per frame: one putImageData per lane per chunk, the read-out once a second while a split runs; `UI.sgRate[kind]` keeps this computer's seconds per chunk for the next estimate; 'estimating…' on a first split; MB of MB during the download (lanes empty, the mix drawn).
- Several clips (a drop with 'the same for the other files'): 'clip 2 of 3' (a wrapper round `importFiles` counts them, lane F's code unchanged). Only one split at a time.
- Control ids written as `data-al` (listed in docs/ids.md, section 'Stem split', for lane H to add to `CONTROLS` when the Workshop covers dialogs).
- Test `tools/ui-tests/taskSG2_2.py`.""",
 '3': """- S1: Keep working sends the split to `#sgCard` (`sgCard`, in the job pill's place, solid, `.up` when MD1's pill shows): the orbit (`mdOrb`/`mdOrbSet`, the real progress), the clip name, one 6 px strip per stem (`sgStrips`, one putImageData per strip per chunk), chunks and time left, Open (the sheet again with every lane so far) and Stop; at the end '3 stems added below “Loop”' with Undo (only while the split is the last undo step), closing by itself after 20 s.
- Hooks: `SG_HOOKS.card(job)` returns the strips element **for lane F** (put it in OV5's `notify` card when it exists; then the card here can go), `SG_HOOKS.pill(key)` returns a 96 × 16 strip for key 'stem' while a split runs in the background (null otherwise) **for lane G** (MD1's `mdJob` pill may show it), `SG_HOOKS.keep(job)`, `SG_HOOKS.added(job)`.
- Test `tools/ui-tests/taskSG2_3.py`.""",
 '4': """- Audio to MIDI: a small hook in `split(j)` (the `sgo` lines) calls `SG_HOOKS.a2m(m, job, engine, buffer)` (`sgA2M`): the lanes replace `a2dbar` while it splits (put back when the pop-up redraws its body), and when it is done each `.a2sr` listen row gets its stem's spectrogram next to the name (`.sgA2`, `.sgA2l`); ▶, Convert and the mode are unchanged.
- Test `tools/ui-tests/taskSG2_4.py`."""}[K]
TITLE = {'1': 'per-chunk spectrogram columns, the quick split in a worker', '2': 'G1 lanes in the Split sheet, P1 draft stretch, F1 scan', '3': 'S1 card with a strip per stem, hooks for lanes F and G', '4': 'Audio to MIDI shows the lanes, then the listen rows'}[K]
today = datetime.datetime.utcnow().strftime('%d %B %Y').lstrip('0')
s = rd('docs/backlog-log.md').rstrip('\n') + '\n\n## %s, task SG2-%s (lane R): %s, v%s\n%s\n' % (today, K, TITLE, V, LOG)
if K == '4': s += '- **stem split lanes complete** (SG2-1 to SG2-4, the user\'s picks G1, S1, P1, F1).\n'
wr('docs/backlog-log.md', s)
s = rd('docs/stem-split-progress.md').rstrip('\n') + '\n- %s UTC: **SG2-%s released**, v%s: %s. Test `tools/ui-tests/taskSG2_%s.py`.\n' % (datetime.datetime.utcnow().strftime('%d %b %H:%M'), K, V, TITLE, K)
if K == '4': s += '\n**stem split lanes complete**: G1, S1, P1 and F1 are in the app (v%s).\n' % V
wr('docs/stem-split-progress.md', s)
if K in '23':
    s = rd('docs/ids.md')
    if '## Stem split' not in s:
        s = s.rstrip('\n') + ('\n\n## Stem split (lane R, task SG2): written as `data-al` by the code itself\n\n'
             'Not yet in `CONTROLS` (its areas are the transport, the track headers and the mixer); lane H adds them when the Workshop covers dialogs.\n\n')
    if K == '2':
        s += ('- `stem.lanes`: the lanes of a stem split (Split sheet, Audio to MIDI) (%s)\n- `stem.keepWorking`: Keep working button (%s)\n- `stem.stop`: Stop button (%s)\n'
              '- `stem.discard`: Discard button (%s)\n- `stem.add`: Add N tracks button (%s)\n- `stem.lane.keep`: a stem\'s tick (%s)\n') % ((V,) * 6)
    else:
        s += ('- `stem.card`: the stem split card (%s)\n- `stem.card.close`: its ✕ (%s)\n- `stem.card.open`: Open (%s)\n- `stem.card.stop`: Stop (%s)\n- `stem.card.undo`: Undo (%s)\n') % ((V,) * 5)
    wr('docs/ids.md', s)
print('ok', K, V)
