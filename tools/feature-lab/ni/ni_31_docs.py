"""Task NI-31 release docs (lane D). Re-runnable after a rebase: python3 tools/feature-lab/ni/ni_31_docs.py VERSION"""
import sys, os
V = sys.argv[1]
R = os.path.dirname(os.path.abspath(__file__)) + '/../../../'
def rd(p): return open(R + p, encoding='utf-8').read()
def wr(p, s): open(R + p, 'w', encoding='utf-8').write(s)
log = rd('tools/feature-lab/ni/ni_31_log.md').replace('{V}', V)
b = rd('docs/backlog-log.md')
if 'task NI-31, high-pass hints' not in b: wr('docs/backlog-log.md', b.rstrip('\n') + '\n\n' + log.rstrip('\n') + '\n')
u = rd('desktop/update-notes.txt')
L = 'High-pass hints (v%s): right-click the logo, High-pass hints… lists tracks with low end they do not need, each with a one-click gentle cut on its Pro EQ (Undo takes it back).' % V
if 'High-pass hints (v' not in u: wr('desktop/update-notes.txt', u.rstrip('\n') + '\n' + L + '\n')
d = rd('docs/device-backlog-2026-11-25.md')
W = ('- Task NI (the picked ideas, lane D): **step NI-31 done**, v%s: high-pass hints (X18): a window (main menu, command `ni.hpHints`) with tracks that have level '
     'under a line they do not need (0.6 x their lowest note, 150 Hz for audio; never kicks, basses, subs, drum kits) and a one-click 12 dB/oct cut on the Pro EQ '
     '(one undo step); found: analysing a whole long song can crash the page (renderer memory of offline renders), see the log; next NI-7b.\n') % V
if 'step NI-31 done' not in d:
    i = d.index('- Task NI (the picked ideas, lane D): **step NI-'); d = d[:i] + W + d[i:]; wr('docs/device-backlog-2026-11-25.md', d)
c = rd('docs/commands.md')
if '`ni.hpHints`' not in c:
    a = [l for l in c.split('\n') if l.startswith('| `ni.harmonicRuler` |')]; assert len(a) == 1
    c = c.replace(a[0], a[0] + '\n| `ni.hpHints` | High-pass hints (tracks with low end they do not need, one-click gentle cut) (lane D, task NI-31) |  |  | %s |' % V); wr('docs/commands.md', c)
p = rd('docs/ideas-build.md')
i = p.index('| NI-31 |'); j = p.index('\n', i); row = p[i:j]
if '**done' not in row:
    k = row.rstrip().rstrip('|').rstrip().rindex('|')
    row = row[:k] + ('| **done v%s** (a window, main menu and `ni.hpHints`; the line is 0.6 x the lowest note for tracks with notes, 150 Hz for audio; measured on up to four '
                     '24-beat stretches per track, because analysing a whole long song can crash the page; returns not checked; the Pro EQ high-pass rises about 0.5 dB above its corner) |') % V
    p = p[:i] + row + p[j:]; wr('docs/ideas-build.md', p)
print('docs for NI-31 v' + V)
