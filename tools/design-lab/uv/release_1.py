#!/usr/bin/env python3
"""Task UV-1 release docs: python3 tools/design-lab/uv/release_1.py 0.291
Run after tools/design-lab/uv/uv_1.py has been applied to the fresh index.html and VERSION bumped.
Writes the backlog entry (from entry_1.md), the Where it stands line, the update note and marks UV-1 done in docs/view-build.md."""
import sys, re
V = sys.argv[1]

def edit(p, fn):
    s = open(p, encoding='utf-8').read(); t = fn(s); assert t != s, p; open(p, 'w', encoding='utf-8').write(t)

LINE = ("- Task UV (view engine, lane O, the user's UX1 picks S9 S13 S14 S10 S11, one step per run): **step UV-1 done**, v%s: "
        "S9 direct trackpad: a pinch and a trackpad scroll with a zoom key are applied in the frame they arrive in (no easing on top of the trackpad's own), only notched mouse wheels glide, now with 15 ms (was 40), none with reduced motion; Speed, Zoom around, Invert and the keys work as before and every zoom ends where the old eased one did; "
        "S13 zoom without page layout: during a pinch the track headers keep their layout and move by transforms (each row its own layer), clip pictures are scaled from their cache, laid out and drawn once 90 ms after the last step (at rest pixel for pixel a fresh drawing); "
        "E19 calmer Follow page turns (Page turns at 90 %% and keeps the last fifth in view, none while an edit is held). "
        "Measured on the cloud machine: a pinch frame 50 to 15 ms of main thread at 1280 x 800 (a scroll frame 12), the app's own part 48 to 7 ms at the user's size; a pinch on screen at 90 %% 441 to 33 ms (user's size). `UV_HOOKS.holding()`. Plan `docs/view-build.md`. Next: UV-2 (S14 tiled arrangement).\n") % V
def _ws(s):
    m = re.search(r"- Task UV \(view engine, lane O[^\n]*\n", s)
    assert m, 'claim line'; return s[:m.start()] + LINE + s[m.end():]
edit('docs/device-backlog-2026-11-25.md', _ws)
edit('desktop/update-notes.txt', lambda s: "Trackpad zoom follows your fingers: a pinch is applied at once with no extra glide, the track headers no longer re-layout while you pinch, and a mouse wheel glides for 15 ms instead of 40. Follow Page turns are calmer (at 90 %%, keeping the last fifth of the page in view).\n".replace('%%', '%') + s)
edit('docs/view-build.md', lambda s: s.replace("| **done** (v0.288) |", "| **done** (v%s) |" % V) if "| **done** (v0.288) |" in s else s.replace("held by the release freeze", "**done** (v%s)" % V))
ENTRY = open('tools/design-lab/uv/entry_1.md', encoding='utf-8').read().replace('{V}', V)
edit('docs/backlog-log.md', lambda s: s.rstrip('\n') + '\n\n' + ENTRY)
print('UV-1 docs for v' + V)
