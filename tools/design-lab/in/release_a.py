"""Release notes for task IN-A (lane E). Re-runnable after a rebase: every edit checks whether it is already there.
  python3 tools/design-lab/in/release_a.py <version> <entry.md>
Sets VERSION in index.html, adds the update-notes line, the 'Where it stands' line, the backlog-log entry, and marks the step done
(with the user's picks line) in docs/design-round-4-instruments.md."""
import sys, re
V = sys.argv[1]; ENTRY = open(sys.argv[2], encoding='utf-8').read().replace('@VER@', V)
def rd(p): return open(p, encoding='utf-8').read()
def wr(p, s): open(p, 'w', encoding='utf-8').write(s)

s = rd('index.html'); n = len(re.findall(r"const VERSION='[\d.]+'", s)); assert n == 1
s = re.sub(r"const VERSION='[\d.]+'", "const VERSION='%s'" % V, s); wr('index.html', s)

p = 'desktop/update-notes.txt'; s = rd(p)
LINE = "Behind the scenes for the new meters and analysers: one shared base for scales, units, colour maps and meter speeds. Two fixes you can see: the meter's Loudness reading (Settings, Level meters) is now truly K-weighted like the loudness meter, and the Sidechain device shows its picture again.\n"
if 'one shared base for scales, units, colour maps' not in s: wr(p, LINE + s)

p = 'docs/device-backlog-2026-11-25.md'; s = rd(p)
W = ("- Task IN (instruments: meters, scopes and analyzers, lane E): **step IN-A done**, v%s: the shared instrument base `INS` (look constants until LK, one number formatter for MD1 and X9, "
     "colour maps magma, inferno, viridis and today's heat, scale drawers for the taper scale, log frequency axis, dB grid and graticule, ballistics for digital peak, VU, PPM IIb, RMS and K-weighted loudness, "
     "one analyser read per frame); the meter's Loudness reading is K-weighted (it was not), the Sidechain device's picture is back (double `vizSide`). Next: IN-M, the level meters (M2).\n") % V
if 'step IN-A done' not in s:
    i = s.index('## Where it stands'); j = s.index('\n- ', i) + 1
    s = s[:j] + W + s[j:]
else:
    s = re.sub(r"(step IN-A done\*\*, v)[\d.]+", r"\g<1>" + V, s)
wr(p, s)

p = 'docs/backlog-log.md'; s = rd(p)
if 'task IN-A, the shared instrument base' not in s: s = s.rstrip('\n') + '\n' + ENTRY
else: s = re.sub(r"## 27 November 2026, v[\d.]+: task IN-A,", "## 27 November 2026, v%s: task IN-A," % V, s)
wr(p, s)

p = 'docs/design-round-4-instruments.md'; s = rd(p)
A = "   No visible change yet. While there, fix the meter \"Loudness\" reading so it is K-weighted (or label it truthfully), and fix the double `vizSide`."
if '**Done in v' not in s.split('2. **IN-M')[0].split('1. **IN-A')[1]:
    assert s.count(A) == 1
    s = s.replace(A, A + "\n\n   **Done in v%s** (task IN-A): module `INS` in index.html; the Loudness reading is K-weighted, `vizSide` fixed (the Visualizer's helper is `vizDockSide`). See the backlog log." % V)
else:
    s = re.sub(r"\*\*Done in v[\d.]+\*\* \(task IN-A\)", "**Done in v%s** (task IN-A)" % V, s)
if "## The user's picks" not in s:
    s = s.rstrip('\n') + """

## The user's picks (27 November 2026, 15:08 Brussels)

`My picks: M2 | L2 | S2 | O0 O1 O4 | G1 G3 G4 | E3 | V1 map viridis | C1 | D1`

- L2 (loudness history) replaces L1.
- O0 keeps today's stereo and scope drawing as one kept view; O1 (marks and afterglow) and O4 (polar view as an extra menu choice) are added to it.
- The Visualizer's colour map is viridis.

Built by task IN (lane E), one step per run in the implementation order above: IN-A, IN-M, IN-L, IN-S, IN-E, IN-G, IN-O, IN-V, IN-C/IN-D.
"""
wr(p, s)
print('release notes for v%s in place' % V)
