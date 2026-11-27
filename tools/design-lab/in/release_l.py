"""Release notes for task IN-L (lane E). Re-runnable after a rebase: every edit checks whether it is already there.
  python3 tools/design-lab/in/release_l.py <version> <entry.md>
Sets VERSION in index.html, adds the update-notes line, the 'Where it stands' line, the backlog-log entry, and marks the step done in
docs/design-round-4-instruments.md."""
import sys, re
V = sys.argv[1]; ENTRY = open(sys.argv[2], encoding='utf-8').read().replace('@VER@', V)
def rd(p): return open(p, encoding='utf-8').read()
def wr(p, s): open(p, 'w', encoding='utf-8').write(s)

s = rd('index.html'); assert len(re.findall(r"const VERSION='[\d.]+'", s)) == 1
s = re.sub(r"const VERSION='[\d.]+'", "const VERSION='%s'" % V, s); wr('index.html', s)

p = 'desktop/update-notes.txt'; s = rd(p)
LINE = ("Loudness history: the loudness pop-up (click the LUFS box in the top bar) shows the last 30 seconds as a graph: the short-term loudness as a line that turns yellow above your target band and red more than 3 LU above it, "
        "the momentary loudness faint behind it, the integrated loudness dashed and the target band shaded green. The small graphs in the top bar and in the mixer's master box, and the Loudness and Meter devices, draw it the same way; "
        "the loudness range is marked as settling for its first 60 seconds.\n")
if 'Loudness history: the loudness pop-up' not in s: wr(p, LINE + s)

p = 'docs/device-backlog-2026-11-25.md'; s = rd(p)
W = ("- Task IN (lane E): **step IN-L done**, v%s: loudness (L2), one history drawer `INS.lhist` (short-term line coloured by the target rule, momentary faint, integrated dashed, target band, LUFS and time scales) "
     "in the pop-up (30 s, 10 a second while open), the top-bar box, the mixer master box, the Loudness device and the Meter device; LRA settling for 60 s. Next: IN-S (S2 analyzer front panel).\n") % V
if 'step IN-L done' not in s:
    i = s.index('step IN-M done'); j = s.index('\n', i) + 1
    s = s[:j] + W + s[j:]
else:
    s = re.sub(r"(step IN-L done\*\*, v)[\d.]+", r"\g<1>" + V, s)
wr(p, s)

p = 'docs/backlog-log.md'; s = rd(p)
if 'task IN-L, loudness' not in s: s = s.rstrip('\n') + '\n\n' + ENTRY
else: s = re.sub(r"## 27 November 2026, v[\d.]+: task IN-L,", "## 27 November 2026, v%s: task IN-L," % V, s)
wr(p, s)

p = 'docs/design-round-4-instruments.md'; s = rd(p)
C = "   **Claimed 27 November 2026** by a lane E run (task IN-L, L2); a second lane E run does not repeat it.\n"
D = ("   **Done in v%s** (task IN-L, L2): `INS.lhist` (the one loudness history drawer), `INL` (the master's momentary and short-term, 10 a second). "
     "The devices keep their own measurement, span and scale; LRA settling for 60 s. See the backlog log.\n") % V
if C in s: s = s.replace(C, D)
elif '(task IN-L, L2)' in s: s = re.sub(r"\*\*Done in v[\d.]+\*\* \(task IN-L, L2\)", "**Done in v%s** (task IN-L, L2)" % V, s)
else:
    A = "LRA settling uses X15.\n"; assert s.count(A) == 1; s = s.replace(A, A + "\n" + D)
wr(p, s)
print('release notes for v%s in place' % V)
