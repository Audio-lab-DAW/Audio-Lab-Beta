"""Release notes for task IN-O (lane E). Re-runnable after a rebase: every edit checks whether it is already there.
  python3 tools/design-lab/in/release_o.py <version> <entry.md>
Sets VERSION in index.html, adds the update-notes line, the 'Where it stands' line, the backlog-log entry, and marks the step done in
docs/design-round-4-instruments.md."""
import sys, re
V = sys.argv[1]; ENTRY = open(sys.argv[2], encoding='utf-8').read().replace('@VER@', V)
def rd(p): return open(p, encoding='utf-8').read()
def wr(p, s): open(p, 'w', encoding='utf-8').write(s)

s = rd('index.html'); assert len(re.findall(r"const VERSION='[\d.]+'", s)) == 1
s = re.sub(r"const VERSION='[\d.]+'", "const VERSION='%s'" % V, s); wr('index.html', s)

p = 'desktop/update-notes.txt'; s = rd(p)
LINE = ("Stereo field: the mixer's stereo view marks where a mono and a one-sided signal at 0, -6 and -12 dB land, keeps a short afterglow so the shape reads, shows the newest sample as an amber dot, and its phase bar has a scale, the value and the phase angle; "
        "right-click the stereo view and choose Polar view under Picture for iZotope's polar sample with the share in phase. The master box's Stereo value shows the phase angle.\n")
if 'Stereo field: the mixer' not in s: wr(p, LINE + s)

p = 'docs/device-backlog-2026-11-25.md'; s = rd(p)
W = ("- Task IN (lane E): **step IN-O done**, v%s: stereo field and phase (O0 kept, O1, O4): today's mixer stereo field with marks (0, -6, -12, -18 dB on the M axis and the L and R diagonals, +S and -S), a short afterglow and the newest sample amber; "
     "the phase bar with a scale, hatched negative half, value and angle; the master box's Stereo value with the angle and the bar hatched; the overlay's stereo module with the marks; Polar view as a Picture choice in the stereo view's menu. "
     "Next: IN-V (V1, viridis).\n") % V
if 'step IN-O done' not in s:
    i = s.index('step IN-G done'); j = s.index('\n', i) + 1
    s = s[:j] + W + s[j:]
else:
    s = re.sub(r"(step IN-O done\*\*, v)[\d.]+", r"\g<1>" + V, s)
wr(p, s)

p = 'docs/backlog-log.md'; s = rd(p)
if 'task IN-O, stereo field and phase' not in s: s = s.rstrip('\n') + '\n\n' + ENTRY
else: s = re.sub(r"## 27 November 2026, v[\d.]+: task IN-O,", "## 27 November 2026, v%s: task IN-O," % V, s)
wr(p, s)

p = 'docs/design-round-4-instruments.md'; s = rd(p)
D = ("   **Done in v%s** (task IN-O, O0 O1 O4): today's stereo field kept with `inoMarks` (the O1 marks), `inoLayer` (the afterglow), the newest sample amber, `inoCorr` (the phase bar's scale, value and angle); "
     "the master box's Stereo value and bar; the overlay's stereo module with the marks; the polar view (`inoPolBg`, `inoPol`) as a Picture choice in the stereo view's menu. The track taps stay at 256. See the backlog log.\n") % V
if '(task IN-O, O0 O1 O4)' in s: s = re.sub(r"\*\*Done in v[\d.]+\*\* \(task IN-O, O0 O1 O4\)", "**Done in v%s** (task IN-O, O0 O1 O4)" % V, s)
else:
    A = "The polar view as a menu choice.\n"; assert s.count(A) == 1; s = s.replace(A, A + "\n" + D)
wr(p, s)
print('release notes for v%s in place' % V)
