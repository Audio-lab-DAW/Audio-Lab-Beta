"""Task NI-7b release docs (lane D). Re-runnable after a rebase: python3 tools/feature-lab/ni/ni_7b_docs.py VERSION (after ni_31_docs.py)"""
import sys, os
V = sys.argv[1]
R = os.path.dirname(os.path.abspath(__file__)) + '/../../../'
def rd(p): return open(R + p, encoding='utf-8').read()
def wr(p, s): open(R + p, 'w', encoding='utf-8').write(s)
log = rd('tools/feature-lab/ni/ni_7b_log.md').replace('{V}', V)
b = rd('docs/backlog-log.md')
if 'task NI-7b, the gain staging check' not in b: wr('docs/backlog-log.md', b.rstrip('\n') + '\n\n' + log.rstrip('\n') + '\n')
d = rd('docs/device-backlog-2026-11-25.md')
W = ('- Task NI (the picked ideas, lane D): **step NI-7b done**, v%s: the gain staging check (X23): a window (main menu, command `ni.gainStaging`) with one line '
     'per track that is hot before its fader (over -1 dBFS, named by the device it goes into), quiet into a compressor, drive or limiter (under -30 dBFS) or '
     'barely heard (under -40 dBFS after the fader), and the master\'s headroom; next NI-10a (I7 draw the arc).\n') % V
if 'step NI-7b done' not in d:
    i = d.index('- Task NI (the picked ideas, lane D): **step NI-'); d = d[:i] + W + d[i:]; wr('docs/device-backlog-2026-11-25.md', d)
c = rd('docs/commands.md')
if '`ni.gainStaging`' not in c:
    a = [l for l in c.split('\n') if l.startswith('| `ni.hpHints` |')]; assert len(a) == 1, 'run ni_31_docs.py first'
    c = c.replace(a[0], a[0] + "\n| `ni.gainStaging` | Gain staging check (tracks too hot into their devices or too quiet, the master's headroom) (lane D, task NI-7b) |  |  | %s |" % V); wr('docs/commands.md', c)
p = rd('docs/ideas-build.md')
i = p.index('| NI-7b |'); j = p.index('\n', i); row = p[i:j]
if '**done' not in row:
    k = row.rstrip().rstrip('|').rstrip().rindex('|')
    row = row[:k] + ('| **done v%s** (a window, main menu and `ni.gainStaging`, over NI-7\'s range (the loop or the 8 bars around the playhead, at most 16 bars); '
                     'hot over -1 dBFS before the fader, quiet under -30 dBFS into a level-sensitive device, barely heard under -40 dBFS after the fader; '
                     'the master after its chain, a problem over -1 dBFS without a limiter on it; groups and returns not measured on their own) |') % V
    p = p[:i] + row + p[j:]
h = '| `NI_HOOKS.listenLens` (planned, if lane D is first)'
if '`NI_HOOKS.gainStaging`' not in p and h in p:
    p = p.replace(h, '| `NI_HOOKS.gainStaging` (`open()`, `measure(o)` the tracks, the problems and the master), `NI.gs.judge(t, journey)` | NI-11 Ask the mix; the mixer (a mark on a strip) | NI-7b, v%s |\n' % V + h)
wr('docs/ideas-build.md', p)
print('docs for NI-7b v' + V)
