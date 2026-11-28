"""Task NI-10a release docs (lane D). Re-runnable after a rebase: python3 tools/feature-lab/ni/ni_10a_docs.py VERSION (after ni_7b_docs.py)"""
import sys, os
V = sys.argv[1]
R = os.path.dirname(os.path.abspath(__file__)) + '/../../../'
def rd(p): return open(R + p, encoding='utf-8').read()
def wr(p, s): open(R + p, 'w', encoding='utf-8').write(s)
log = rd('tools/feature-lab/ni/ni_10a_log.md').replace('{V}', V)
b = rd('docs/backlog-log.md')
if 'task NI-10a, draw the arc' not in b: wr('docs/backlog-log.md', b.rstrip('\n') + '\n\n' + log.rstrip('\n') + '\n')
d = rd('docs/device-backlog-2026-11-25.md')
W = ('- Task NI (the picked ideas, lane D): **step NI-10a done**, v%s: draw the arc (I7 part 1): draw the energy you want in the energy lane '
     '(right-click it, Draw your line…, or `ni.drawArc`), saved as `S.ni_arc` v1; stretches where the song sits clearly under the line are shaded red '
     'with their size ("bars 9 to 12 sit about 22 dB under your line"); next NI-10b (the moves).\n') % V
if 'step NI-10a done' not in d:
    i = d.index('- Task NI (the picked ideas, lane D): **step NI-'); d = d[:i] + W + d[i:]; wr('docs/device-backlog-2026-11-25.md', d)
c = rd('docs/commands.md')
if '`ni.drawArc`' not in c:
    a = [l for l in c.split('\n') if l.startswith('| `ni.gainStaging` |')]; assert len(a) == 1, 'run ni_7b_docs.py first'
    c = c.replace(a[0], a[0] + '\n| `ni.drawArc` | Draw your energy line (the energy you want over the song; the parts under it are marked) (lane D, task NI-10a) |  |  | %s |' % V); wr('docs/commands.md', c)
p = rd('docs/ideas-build.md')
i = p.index('| NI-10a |'); j = p.index('\n', i); row = p[i:j]
if '**done' not in row:
    k = row.rstrip().rstrip('|').rstrip().rindex('|')
    row = row[:k] + ('| **done v%s** (drawn in NI-6\'s energy lane on its 0 to 1 scale, one undo step per stroke, Alt-drag erases; `S.ni_arc` v1 with one value per beat; '
                     'a shortfall is 0.06 under the line for a bar or more, its dB the loudness change that would close it; only shortfalls are marked) |') % V
    p = p[:i] + row + p[j:]
h = '| `NI_HOOKS.listenLens` (planned, if lane D is first)'
if '`NI_HOOKS.arcLine`' not in p and h in p:
    p = p.replace(h, '| `NI_HOOKS.arcLine` (`line()`, `short()` the stretches under the line with bars, gap and dB, `set(b0, b1, v0, v1)`, `mode(on)`) | NI-10b, NI-11 Ask the mix | NI-10a, v%s |\n' % V + h)
wr('docs/ideas-build.md', p)
print('docs for NI-10a v' + V)
