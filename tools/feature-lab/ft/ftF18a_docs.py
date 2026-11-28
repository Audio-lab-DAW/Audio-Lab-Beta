#!/usr/bin/env python3
"""Task FT-F18a docs: backlog-log entry, Where it stands line, features-build row, update-notes line. python3 ftF18a_docs.py VERSION"""
import sys, os
V = sys.argv[1]
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
def rw(p, f):
    s = open(p, encoding='utf-8').read(); t = f(s); assert t != s, p; open(p, 'w', encoding='utf-8').write(t)
# features-build row
rw('docs/features-build.md', lambda s: s.replace("low-band correlation. | built and tested 28 Nov 17:40 UTC (taskFT_F18a 26/26), waiting for the release freeze to push index.html |", "low-band correlation. | **done v%s** (as a row of lane D's lab: bass line key, tail overlap, low-band correlation) |" % V, 1))
# Where it stands
line = ("- Task FT-F18a (kick and bass lab part 1, lane C, starred card F18): **done**, v%s. Lane D's Kick and bass lab (main menu, or the command "
        "`ni.kickBass`) gets a new row under its words: **Bass line** (the key the bass line itself plays in, from all its notes, flagged when it "
        "differs from the song key), **Tail overlap** (how long the bass sounds while the kick still rings, and how much shorter the tail would have to be), "
        "**Low band** (kick and bass each rendered alone for the bar, low-passed at 120 Hz, correlated while the kick sounds: +1 they add up, -1 they cancel, "
        "with the level change in dB) and a strip per 16th. Equal to an offline calculation (scipy) within 0.001. Next: FT-F18b (phase rotation, shorten tail, suggestions, X15 kick and bass lock).\n") % V
def ws(s):
    a = "- Task FT-F16b (volume shaper part 2, lane C"
    assert s.count(a) == 1; return s.replace(a, line + a, 1)
rw('docs/device-backlog-2026-11-25.md', ws)
# update notes
def un(s):
    return s.rstrip('\n') + "\nKick and bass lab (v%s): new row with the bass line's own key, how long the bass rings into the kick's tail, and whether the two cancel each other under 120 Hz.\n" % V
rw('desktop/update-notes.txt', un)
# backlog log
E = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ftF18a_log.md'), encoding='utf-8').read().replace('{V}', V)
rw('docs/backlog-log.md', lambda s: s.rstrip('\n') + '\n\n' + E.rstrip('\n') + '\n')
print('docs updated for', V)
