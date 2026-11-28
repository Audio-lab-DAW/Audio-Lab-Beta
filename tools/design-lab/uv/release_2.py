#!/usr/bin/env python3
"""Task UV-2 release docs: python3 tools/design-lab/uv/release_2.py 0.297
Run after tools/design-lab/uv/uv_2.py has been applied to the fresh index.html and VERSION bumped.
Writes the backlog entry (from entry_2.md), the Where it stands line, the update note and marks UV-2a done in docs/view-build.md."""
import sys, re
V = sys.argv[1]

def edit(p, fn):
    s = open(p, encoding='utf-8').read(); t = fn(s); assert t != s, p; open(p, 'w', encoding='utf-8').write(t)

LINE = ("- Task UV (view engine, lane O, the user's UX1 picks S9 S13 S14 S10 S11, one step per run): **step UV-2a done**, v%s: "
        "S14 tiled arrangement: a scroll shifts the picture already drawn by whole device pixels and lane A's drawing paints only what is new (the strip that scrolled in, "
        "the ruler, the header column, the master lane, clips at the left edge), about 30 %% of the picture; an edit with the view still (a clip muted, moved, a note in the piano roll, "
        "the selection, the hover) paints only the changed clips' boxes, about 2 to 5 %%; anything else draws in full, and 90 ms after the last tiled frame one full drawing "
        "(at rest pixel for pixel the untiled drawing). Edits are tiled everywhere; scroll tiles only where a graphics card draws the canvas (on a software renderer the copies cost more). "
        "Measured: one drawing during a scroll on the Mac runner's Metal 14 to 18 ms down to 12; edit while scrolled on the cloud machine 154 to 130 ms of main thread per frame; scroll and pinch unchanged there (software rendering: scroll tiles off). "
        "Hooks `UV_HOOKS.bump()` (lane A: drop the kept picture) and `UV_HOOKS.tiles()` (what the last frame painted). Plan `docs/view-build.md`. Next: UV-2b (the glass engine reads the tiles), then UV-3.\n") % V
def _ws(s):
    m = re.search(r"- Task UV \(view engine, lane O[^\n]*\n", s)
    assert m, 'claim line'; return s[:m.start()] + LINE + s[m.end():]
edit('docs/device-backlog-2026-11-25.md', _ws)
edit('desktop/update-notes.txt', lambda s: "The arrangement redraws less: an edit repaints only the clips it changed, and with a graphics card a scroll repaints only the strip that comes into view (the rest of the picture is moved).\n" + s)
edit('docs/view-build.md', lambda s: s.replace("| claimed 28 Nov 09:20 UTC |", "| **part a done** (v%s); part b next |" % V))
ENTRY = open('tools/design-lab/uv/entry_2.md', encoding='utf-8').read().replace('{V}', V)
edit('docs/backlog-log.md', lambda s: s.rstrip('\n') + '\n\n' + ENTRY)
print('UV-2a docs for v' + V)
