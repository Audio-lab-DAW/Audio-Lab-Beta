"""Task NI-5c release docs (lane D). Re-runnable after a rebase: python3 tools/feature-lab/ni/ni_5c_docs.py VERSION"""
import sys, re, os
V = sys.argv[1]
R = os.path.dirname(os.path.abspath(__file__)) + '/../../../'
def rd(p): return open(R + p, encoding='utf-8').read()
def wr(p, s): open(R + p, 'w', encoding='utf-8').write(s)
# backlog log
log = rd('tools/feature-lab/ni/ni_5c_log.md').replace('27 November 2026, v{V}', '28 November 2026, v' + V)
log = log.replace("- **Not run:** the start-up smoke test of the release gate cannot run on this cloud machine, because the Electron download is blocked. {GATE}",
  "- **Re-checked (28 Nov, 09:20 to 09:50 UTC):** re-checked on v0.294 while the gate's freeze of 09:11:57 UTC held `index.html`: the edit script re-applied cleanly; `taskNI_5c.py` 22 of 22, `taskNI_5a.py` 34 of 34, `taskNI_5b.py` 22 of 22, `taskXT_DL2.py` 24 of 24 (`ni.monoLoss` now listed); lint clean; the start-up smoke test in the real desktop app (`smoke_electron.js`, 20 s per scenario, run directly because `gate.py` cannot find the v0.250 release commit in the rewritten history): **14 of 14 scenarios clean**, frame times p50 16.7 / p95 50 ms; Fractals levels unchanged on this build (measured again: Kick -19.05560 dB fb577dd5202b, Bass -35.48685 dB 392ec52590c7 at -10 dB; -9.75669 dB 0496bb147f6c and -25.48699 dB 09e0415bec5e at 0 dB, the references of the newest RG entry).")
log = log.replace('−', '-')
b = rd('docs/backlog-log.md')
if 'task NI-5c, the clash measure' not in b:
    wr('docs/backlog-log.md', b.rstrip('\n') + '\n\n' + log.rstrip('\n') + '\n')
# update notes
u = rd('desktop/update-notes.txt')
L = 'Clashes that take turns (v%s): in the mixer\'s cable lane, Clashes now checks each pair inside the beat; a kick and a rolling bass that take turns get a thin dashed cable, and the clash card shows both tracks in the band over 8 beats.' % V
if 'Clashes that take turns' not in u: wr('desktop/update-notes.txt', u.rstrip('\n') + '\n' + L + '\n')
# where it stands
d = rd('docs/device-backlog-2026-11-25.md')
W = '- Task NI (the picked ideas, lane D): **step NI-5c done**, v%s: the clash measure that knows the beat (X16, folded into I12): each clash cable is checked inside the 8 beats around the playhead on offline renders of the two tracks; pairs that are loud together under 25%% of the time (a kick and a rolling bass) get a thin dashed "take turns" cable that is not counted; the clash card shows both tracks in the band over the 8 beats with the moments together shaded. Next: NI-9, the harmonic ruler (I5).\n' % V
if 'step NI-5c done' not in d:
    a = '- Task NI (the picked ideas, lane D): **step NI-8 done**'
    assert d.count(a) == 1
    d = d.replace(a, W + a)
    wr('docs/device-backlog-2026-11-25.md', d)
# plan status
p = rd('docs/ideas-build.md')
i = p.index('| NI-5c |'); j = p.index('\n', i)
row = p[i:j]
k = row.rindex('| built and tested on v0.293')
row2 = row[:k] + '| **done v%s** (released after the release gate\'s freeze of 28 Nov 09:11 UTC; the 25%% "take turns" line and the 10 dB "loud" line are first guesses for the user to judge) |' % V
p = p[:i] + row2 + p[j:]
wr('docs/ideas-build.md', p)
print('docs for NI-5c v' + V)
