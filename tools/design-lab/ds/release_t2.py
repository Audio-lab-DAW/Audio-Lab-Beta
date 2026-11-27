#!/usr/bin/env python3
"""Task DS-T2 release docs: python3 tools/design-lab/ds/release_t2.py 0.279
Writes the backlog entry, the Where it stands line, section 6 of docs/design-round-2.md and the update note."""
import sys
V = sys.argv[1]

def edit(p, fn):
    s = open(p, encoding='utf-8').read(); t = fn(s); assert t != s, p; open(p, 'w', encoding='utf-8').write(t)

def rep1(old, new):
    def f(s):
        assert s.count(old) == 1, old[:80]; return s.replace(old, new)
    return f

edit('docs/design-round-2.md', rep1(
    "8. **DR2-T2, meters, CPU and top bar** (TM, TC, TS): meter scales, CPU line from the existing CPU sampling, the top bar status line together with X10 (science round 2, SC-K).",
    "8. **DR2-T2, meters, CPU and top bar** (TM, TC, TS): meter scales, CPU line from the existing CPU sampling, the top bar status line together with X10 (science round 2, SC-K). **Done (task DS-T2), v%s**: TM1 (the transport meter with ticks above the bars, labels -48, -24, -12, 0 under them, hold marks, read-out in dBFS), TC1 (CPU as the last 10 seconds as a line), TS1 (status line in the top bar: audio format and save state; `DS_HOOKS.status` is X10's slot); only the AudioLab look." % V))

LINE = ("- Task DS (design round 2, lane A): **step DS-T2 done**, v%s: the transport meter, the CPU read-out and the top bar (TM1, TC1, TS1): "
        "the master meter in the transport as a peak meter with a dB scale (ticks above the two bars, -48 to 0 with 0 in red, labels -48, -24, -12, 0 under them; lane E's bars with the RMS core and the white hold marks kept) and its read-out in dBFS; "
        "the CPU as the last 10 seconds as a line (the highest load of every 250 ms, fixed 0 to 100 %% scale, red while there is a problem); "
        "a quiet status line in the middle of the top bar with the engine's audio format (44.1 kHz · 32-bit float) and the save state (saved n min ago with a green dot, unsaved changes amber, not saved to a file yet grey), hidden when tabs would touch it, `DS_HOOKS.status` the slot for X10's signal path (SC-K). "
        "Only the AudioLab look. Next: DS-B1 browser (B3, BR2, BP1).\n") % V
edit('docs/device-backlog-2026-11-25.md', rep1(
    "- Task DS (design round 2, lane A): step DS-T2 (meters, CPU and top bar: TM1, TC1, TS1) **in progress** (started 27 Nov, UTC evening; this line is replaced when it is released).\n", LINE))

edit('desktop/update-notes.txt', lambda s: "Transport and top bar: the master meter has a dB scale with labels and reads in dBFS, the CPU shows the last 10 seconds as a line, and the top bar shows the audio format and whether the project is saved.\n" + s)

ENTRY = open('tools/design-lab/ds/entry_t2.md', encoding='utf-8').read().replace('{V}', V)
edit('docs/backlog-log.md', lambda s: s.rstrip('\n') + '\n\n' + ENTRY)
print('docs for v' + V)
