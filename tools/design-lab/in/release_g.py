"""Release notes for task IN-G (lane E). Re-runnable after a rebase: every edit checks whether it is already there.
  python3 tools/design-lab/in/release_g.py <version> <entry.md>
Sets VERSION in index.html, adds the update-notes line, the 'Where it stands' line, the backlog-log entry, and marks the step done in
docs/design-round-4-instruments.md."""
import sys, re
V = sys.argv[1]; ENTRY = open(sys.argv[2], encoding='utf-8').read().replace('@VER@', V)
def rd(p): return open(p, encoding='utf-8').read()
def wr(p, s): open(p, 'w', encoding='utf-8').write(s)

s = rd('index.html'); assert len(re.findall(r"const VERSION='[\d.]+'", s)) == 1
s = re.sub(r"const VERSION='[\d.]+'", "const VERSION='%s'" % V, s); wr('index.html', s)

p = 'desktop/update-notes.txt'; s = rd(p)
LINE = ("Dynamics displays: the Compressor, Limiter, Gate and Ducker show the last 4 seconds with the gain reduction in red hanging from the top on the same dB scale as the level, "
        "with the reduction now as a big number and the most in 4 seconds; the Compressor's curve is drawn exactly as it compresses, with the sound riding it as a dot and an amber caliper giving the reduction; "
        "OTT, Multiband Dynamics and the De-Esser show a reduction bar per band on a studio scale with the band's frequencies.\n")
if 'Dynamics displays: the Compressor, Limiter' not in s: wr(p, LINE + s)

p = 'docs/device-backlog-2026-11-25.md'; s = rd(p)
W = ("- Task IN (lane E): **step IN-G done**, v%s: the dynamics displays (G1, G3, G4): one gain reduction history drawer `INS.grh` (4 s, input grey, output blue, GR red from the top on the same dB scale, numbers) "
     "in the Compressor, Limiter, Gate and Ducker; the Compressor's curve as Chromium computes it with the live point, trail and amber caliper; G4 bars per band (`ingBar`, studio scale) in OTT, Multiband and the De-Esser. "
     "Next: IN-O (O0 kept, O1, O4).\n") % V
if 'step IN-G done' not in s:
    i = s.index('step IN-E done'); j = s.index('\n', i) + 1
    s = s[:j] + W + s[j:]
else:
    s = re.sub(r"(step IN-G done\*\*, v)[\d.]+", r"\g<1>" + V, s)
wr(p, s)

p = 'docs/backlog-log.md'; s = rd(p)
if 'task IN-G, the dynamics displays' not in s: s = s.rstrip('\n') + '\n\n' + ENTRY
else: s = re.sub(r"## 27 November 2026, v[\d.]+: task IN-G,", "## 27 November 2026, v%s: task IN-G," % V, s)
wr(p, s)

p = 'docs/design-round-4-instruments.md'; s = rd(p)
D = ("   **Done in v%s** (task IN-G, G1 G3 G4): `INS.grh` (the one gain reduction history drawer) in the Compressor, Limiter, Gate and Ducker; the Compressor's curve "
     "as Chromium computes it (`ingCK`) with the live point, a 30-point trail and the amber caliper; `ingBar` (G4 bars on the studio scale) in OTT, Multiband and the De-Esser. See the backlog log.\n") % V
if '(task IN-G, G1 G3 G4)' in s: s = re.sub(r"\*\*Done in v[\d.]+\*\* \(task IN-G, G1 G3 G4\)", "**Done in v%s** (task IN-G, G1 G3 G4)" % V, s)
else:
    A = "from the GR values the devices already post.\n"; assert s.count(A) == 1; s = s.replace(A, A + "\n" + D)
wr(p, s)
print('release notes for v%s in place' % V)
