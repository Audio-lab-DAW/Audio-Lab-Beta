"""Release notes for task IN-C and IN-D (lane E). Re-runnable after a rebase: every edit checks whether it is already there.
  python3 tools/design-lab/in/release_cd.py <version> <entry.md>
Sets VERSION in index.html, adds the update-notes line, the 'Where it stands' line, the backlog-log entry, and marks the step done in
docs/design-round-4-instruments.md. Then run: node desktop/scripts/sync-app.js (it writes desktop/app-version-dev.json, never app-version.json)."""
import sys, re
V = sys.argv[1]; ENTRY = open(sys.argv[2], encoding='utf-8').read().replace('@VER@', V)
def rd(p): return open(p, encoding='utf-8').read()
def wr(p, s): open(p, 'w', encoding='utf-8').write(s)

s = rd('index.html'); assert len(re.findall(r"const VERSION='[\d.]+'", s)) == 1
s = re.sub(r"const VERSION='[\d.]+'", "const VERSION='%s'" % V, s); wr('index.html', s)

p = 'desktop/update-notes.txt'; s = rd(p)
LINE = ("CPU graph and device scopes: the CPU graph in the top bar has an amber budget line at 75 % and turns red only above it; its pop-up shows the graph large with a scale, "
        "the load now, the highest of the last 4 seconds and the time per screen frame. The Soft Clipper shows the last 300 ms with a scale, a time bar, the peak in dBFS and red marks where the sound hits full scale; the Bitcrusher gets the same scale and peak.\n")
if 'CPU graph and device scopes:' not in s: wr(p, LINE + s)

p = 'docs/device-backlog-2026-11-25.md'; s = rd(p)
W = ("- Task IN (lane E): **step IN-C and IN-D done**, v%s: the CPU graph (C1: budget tick at 75 %%, red only above it; the pop-up's large graph with a 0, 50, 100 %% scale, "
     "now, peak of 4 s and ms per frame; `INC.btn` is the one CPU graph drawer for DS-T2's TC1) and the scope preview in devices (D1, `IND`: the Soft Clipper's 300 ms of min and max columns, "
     "scale, time bar, peak in dBFS, full-scale marks; the Bitcrusher's scale, time bar and peak). The original order is complete; next the AE3 additions IN-X17, IN-X19, IN-X25.\n") % V
if 'step IN-C and IN-D done' not in s:
    i = s.index('step IN-V done'); j = s.rfind('\n', 0, i) + 1
    s = s[:j] + W + s[j:]
else:
    s = re.sub(r"(step IN-C and IN-D done\*\*, v)[\d.]+", r"\g<1>" + V, s)
wr(p, s)

p = 'docs/backlog-log.md'; s = rd(p)
if 'task IN-C and IN-D, the CPU graph' not in s: s = s.rstrip('\n') + '\n\n' + ENTRY
else: s = re.sub(r"## 28 November 2026, v[\d.]+: task IN-C and IN-D,", "## 28 November 2026, v%s: task IN-C and IN-D," % V, s)
wr(p, s)

p = 'docs/design-round-4-instruments.md'; s = rd(p)
D = ("   **Done in v%s** (task IN-C and IN-D, C1 D1): `INC` (C1: the button's graph with the budget tick, red only above 75 %%; the pop-up's large graph with its scale and three read-outs; "
     "`INC.btn` is the one drawer for DS-T2's TC1) and `IND` (D1: 300 ms of min and max columns, scale, X11 time bar, peak in dBFS, full-scale marks) in the Soft Clipper and the Bitcrusher. See the backlog log.\n") % V
if '(task IN-C and IN-D, C1 D1)' in s: s = re.sub(r"\*\*Done in v[\d.]+\*\* \(task IN-C and IN-D, C1 D1\)", "**Done in v%s** (task IN-C and IN-D, C1 D1)" % V, s)
else:
    A = "The smallest; they can go with IN-M or IN-G.\n"; assert s.count(A) == 1; s = s.replace(A, A + "\n" + D)
wr(p, s)
print('release notes for v%s in place' % V)
