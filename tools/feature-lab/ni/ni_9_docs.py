"""Task NI-9 release docs (lane D). Re-runnable after a rebase: python3 tools/feature-lab/ni/ni_9_docs.py VERSION"""
import sys, os
V = sys.argv[1]
R = os.path.dirname(os.path.abspath(__file__)) + '/../../../'
def rd(p): return open(R + p, encoding='utf-8').read()
def wr(p, s): open(R + p, 'w', encoding='utf-8').write(s)
# backlog log
log = rd('tools/feature-lab/ni/ni_9_log.md').replace('{V}', V).replace('−', '-')
b = rd('docs/backlog-log.md')
if 'task NI-9, the harmonic ruler' not in b:
    wr('docs/backlog-log.md', b.rstrip('\n') + '\n\n' + log.rstrip('\n') + '\n')
# where it stands
d = rd('docs/device-backlog-2026-11-25.md')
W = ('- Task NI (the picked ideas, lane D): **step NI-9 done**, v%s: the harmonic ruler (I5): a piano strip along the bottom of every live spectrum view '
     '(Spectrum device, spectrum overlay, Visualizer), the five strongest peaks named with note and cents ("A2 0 c"), amber outside the song key, '
     'red "rings" when a pitch keeps ringing for more than a beat after the rest faded; on by default, switch in the main menu and command '
     '`ni.harmonicRuler`; lane E\'s drawer wrapped, not changed; next NI-31 (X18 high-pass hints).\n') % V
if 'step NI-9 done' not in d:
    a = '- Task NI (the picked ideas, lane D): **step NI-'
    i = d.index(a)
    d = d[:i] + W + d[i:]
    wr('docs/device-backlog-2026-11-25.md', d)
# commands list
c = rd('docs/commands.md')
if '`ni.harmonicRuler`' not in c:
    a = [l for l in c.split('\n') if l.startswith('| `ni.monoLoss` |')]
    assert len(a) == 1
    c = c.replace(a[0], a[0] + '\n| `ni.harmonicRuler` | Harmonic ruler on / off (note names of the strongest peaks under every spectrum view) (lane D, task NI-9) |  |  | %s |' % V)
    wr('docs/commands.md', c)
# plan status and the hooks table
p = rd('docs/ideas-build.md')
i = p.index('| NI-9 |'); j = p.index('\n', i); row = p[i:j]
if '**done' not in row:
    k = row.rstrip().rstrip('|').rstrip().rindex('|')
    row2 = row[:k] + ('| **done v%s** (on every live spectrum view drawn by lane E\'s `INS.spec`, which is wrapped, not changed; the red "rings" is measured '
                      'on the live trace, not from NI-3\'s cache: a view shows its device or the master, the cache is per track; on by default, main menu '
                      'and `ni.harmonicRuler`) |') % V
    p = p[:i] + row2 + p[j:]
h = '| `NI_HOOKS.harmonicRuler` (planned) | lane A, device displays | NI-9 |'
if h in p:
    p = p.replace(h, '| `NI_HOOKS.harmonicRuler(g, box, peaks, o)` (draws a ruler into any canvas), `NI_HOOKS.harmonicPeaks(an, lo, hi, st)` (the named peaks of an analyser, with their history in `st`) | lane A or lane I (a rebuilt device display), NI-11 Ask the mix | NI-9, v%s |' % V)
wr('docs/ideas-build.md', p)
print('docs for NI-9 v' + V)
