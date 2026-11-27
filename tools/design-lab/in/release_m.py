"""Release notes for task IN-M (lane E). Re-runnable after a rebase: every edit checks whether it is already there.
  python3 tools/design-lab/in/release_m.py <version> <entry.md>
Sets VERSION in index.html, adds the update-notes line, the 'Where it stands' line, the backlog-log entry, and marks the step done in
docs/design-round-4-instruments.md."""
import sys, re
V = sys.argv[1]; ENTRY = open(sys.argv[2], encoding='utf-8').read().replace('@VER@', V)
def rd(p): return open(p, encoding='utf-8').read()
def wr(p, s): open(p, 'w', encoding='utf-8').write(s)

s = rd('index.html'); assert len(re.findall(r"const VERSION='[\d.]+'", s)) == 1
s = re.sub(r"const VERSION='[\d.]+'", "const VERSION='%s'" % V, s); wr('index.html', s)

p = 'desktop/update-notes.txt'; s = rd(p)
LINE = ("Level meters show peak and average in one bar: the bright part is the average level (RMS over 300 ms), the fainter part above it reaches the peak. "
        "The master strip in the mixer shows the RMS and the crest factor (how far the peaks stand above the average), and so do the tooltips of the channel peak read-outs and the transport's peak box. "
        "The mixer's meter view and the big meter in Settings now use the fader's scale.\n")
if 'Level meters show peak and average in one bar' not in s: wr(p, LINE + s)

p = 'docs/device-backlog-2026-11-25.md'; s = rd(p)
W = ("- Task IN (lane E): **step IN-M done**, v%s: the level meters (M2): an RMS 300 ms core (AES17) in every meter with the peak part faint above it "
     "(mixer fader meters in every design incl. Flat bars, track headers, the device panel's track meter, the transport meter, the mixer's meter view, the Settings preview), "
     "RMS and crest read-outs (master strip, tooltips, Settings preview), the meter view and preview on the fader taper with the M1 scale; one drawer `INS.mbar` for DS-T2's TM1. Next: IN-L (L2 loudness history).\n") % V
if 'step IN-M done' not in s:
    i = s.index('step IN-A done'); j = s.index('\n', i) + 1
    s = s[:j] + W + s[j:]
else:
    s = re.sub(r"(step IN-M done\*\*, v)[\d.]+", r"\g<1>" + V, s)
wr(p, s)

p = 'docs/backlog-log.md'; s = rd(p)
if 'task IN-M, the level meters' not in s: s = s.rstrip('\n') + '\n\n' + ENTRY
else: s = re.sub(r"## 27 November 2026, v[\d.]+: task IN-M,", "## 27 November 2026, v%s: task IN-M," % V, s)
wr(p, s)

p = 'docs/design-round-4-instruments.md'; s = rd(p)
C = "   **Claimed 27 November 2026** by a lane E run (task IN-M, M2); a second lane E run does not repeat it.\n"
D = ("   **Done in v%s** (task IN-M, M2): `INS.pr` (300 ms window), `INS.mbar` (the one canvas bar drawer, for DS-T2's TM1), `INM` (the core as a veil on the page-element meters, read-outs). "
     "The speed, reading, colour and hold settings stay the user's; the core shows with the Peak reading. See the backlog log.\n") % V
if C in s: s = s.replace(C, D)
elif '(task IN-M, M2)' in s: s = re.sub(r"\*\*Done in v[\d.]+\*\* \(task IN-M, M2\)", "**Done in v%s** (task IN-M, M2)" % V, s)
else:
    A = "RMS and crest come from `al-meter` or the analyser data already read.\n"; assert s.count(A) == 1; s = s.replace(A, A + "\n" + D)
wr(p, s)
print('release notes for v%s in place' % V)
