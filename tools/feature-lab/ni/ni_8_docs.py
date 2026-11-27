"""Task NI-8 docs: plan row, hook table, Where it stands, update note, backlog entry. Re-runnable on fresh docs (asserted anchors).
  python3 tools/feature-lab/ni/ni_8_docs.py VERSION"""
import sys, re
V = sys.argv[1]
def rep(p, old, new, cnt=1):
    s = open(p, encoding='utf-8').read()
    if new in s: return
    assert s.count(old) == cnt, (p, old[:60], s.count(old))
    open(p, 'w', encoding='utf-8').write(s.replace(old, new))
# plan
p = 'docs/ideas-build.md'; s = open(p, encoding='utf-8').read()
s2 = re.sub(r"(\| A test track with a known phase-inverted side shows the computed loss; a mono track shows none\. \| )[^|\n]*\|",
  r"\1**done v%s** (a window from the main menu, the command `ni.monoLoss` and a Loss button next to Mono on the master strip; per track and per 1/6 octave from NI-3's mid and side bands, so -3 dB means wide or one-sided and more means cancelling; the tracks that cancel each other are found on their own offline renders of the 8 loudest tracks, compared pair by pair in a worker, at most 8 bars) |" % V, s)
assert s2 != s or ('done v%s' % V) in s; s = s2
a = "| `NI_HOOKS.harmonicRuler` (planned) |"
if '`NI_HOOKS.monoLoss`' not in s:
    assert s.count(a) == 1
    s = s.replace(a, "| `NI_HOOKS.monoLoss` (`open()`, `measure(o)` the tracks with per-band loss and the cancelling pairs, `tracks(b0, b1)`), `NI.mono.pairsOf(list, b0, b1)`, `NI_HOOKS.mxMon(w)` (called by the mixer's render, adds the Loss button next to Mono) | NI-11 Ask the mix; whoever rebuilds the mixer's master strip keeps the one-line call; lane C (FT-F25b listening stage) if it wants a mono-loss read-out | NI-8, v%s |\n" % V + a)
open(p, 'w', encoding='utf-8').write(s)
# Where it stands
rep('docs/device-backlog-2026-11-25.md', "- Task NI (the picked ideas, lane D): **step NI-7 done**",
  "- Task NI (the picked ideas, lane D): **step NI-8 done**, v%s: the mono-loss map (I4): a window (main menu Mono loss…, command `ni.monoLoss`, a Loss button next to Mono on the master strip) with one row per track that plays: a band strip 20 Hz to 20 kHz coloured by how much that track loses in mono (cyan holds, grey -3 dB wide or one-sided, amber partly cancels, red cancels), its whole loss in dB and the worst stretch in words (\"-10 dB at 381 to 427 Hz\"); tracks that cancel each other in mono joined by a line, with a sentence and whether stereo cancels too; Hear in mono; the loop or 8 bars around the playhead, or the whole song. From NI-3's cache and offline renders only. Next: NI-9, the harmonic ruler (I5).\n- Task NI (the picked ideas, lane D): **step NI-7 done**" % V)
# update note
p = 'desktop/update-notes.txt'; s = open(p, encoding='utf-8').read()
line = "Mono loss map (v%s): right-click the logo, Mono loss… (or Loss next to Mono on the master strip) shows what each track loses when the mix is heard in mono, band by band, and joins tracks that cancel each other." % V
if line not in s: open(p, 'w', encoding='utf-8').write(s.rstrip('\n') + '\n' + line + '\n')
# backlog entry
p = 'docs/backlog-log.md'; s = open(p, encoding='utf-8').read()
if ('task NI-8,') not in s:
    s = s.rstrip('\n') + '\n\n' + open('tools/feature-lab/ni/ni_8_log.md', encoding='utf-8').read().replace('{V}', V)
    open(p, 'w', encoding='utf-8').write(s)
print('docs ok', V)
