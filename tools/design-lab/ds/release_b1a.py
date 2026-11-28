#!/usr/bin/env python3
"""Task DS-B1a release docs: python3 tools/design-lab/ds/release_b1a.py 0.315 "gate line"
Writes the backlog entry, the Where it stands line, section 6 of docs/design-round-2.md and the update note."""
import sys
V = sys.argv[1]
GATE = sys.argv[2] if len(sys.argv) > 2 else ''

def edit(p, fn):
    s = open(p, encoding='utf-8').read(); t = fn(s); assert t != s, p; open(p, 'w', encoding='utf-8').write(t)

def rep1(old, new):
    def f(s):
        assert s.count(old) == 1, old[:80]; return s.replace(old, new)
    return f

edit('docs/design-round-2.md', rep1(
    "9. **DR2-B1, browser** (B look, BR, BP): the new layout behind the same entry points (Instrument Browser, Effects Browser), preview in tempo, arrow keys.",
    "9. **DR2-B1, browser** (B look, BR, BP): the new layout behind the same entry points (Instrument Browser, Effects Browser), preview in tempo, arrow keys. **Part a done (task DS-B1a), v%s**: B3 catalogue (categories with counts, search, Cards to go back to the live cards), BR2 rows with tag colours, BP1 waveform with a time scale and a scrub line (rendered once offline, cached), presets with arrow keys, In tempo next bar, the one live device; only the AudioLab look. Part b (DS-B1b): S3, the pop-up browser where you click, frecency per word." % V))

LINE = ("- Task DS (design round 2, lane A): **step DS-B1a done**, v%s: the Instrument and Effects browsers as a catalogue with a measured preview (B3, BR2, BP1): "
        "a search field with the focus, categories with counts, one row per device with up to three tag colours and its kind; the preview with the sound's waveform, a time scale and a scrub line while it plays (worked out once per sound, phrase and tempo), key, tempo, length and peak, the presets (left and right arrows), In tempo next bar and the one live device; "
        "up and down choose and play, Enter adds, uses or keeps; Change works as before; Cards brings back the live cards. Only the AudioLab look. Next: DS-B1b (S3 pop-up browser where you click).\n") % V
def _ws(s):
    import re
    m = re.search(r"- Task DS \(design round 2, lane A\): step DS-B1a \([^\n]*\n", s)
    if m: return s[:m.start()] + LINE + s[m.end():]
    a = "- Task DS (design round 2, lane A): **step DS-T2 done**"
    i = s.index(a); return s[:i] + LINE + s[i:]
edit('docs/device-backlog-2026-11-25.md', _ws)

edit('desktop/update-notes.txt', lambda s: "Browser: instruments and effects in a searchable list with categories; the chosen sound shows its waveform, key, tempo and presets (arrow keys step and play), and can start on the next bar. Cards brings back the big live cards.\n" + s)

ENTRY = open('tools/design-lab/ds/entry_b1a.md', encoding='utf-8').read().replace('{V}', V).replace('{GATE}', GATE)
edit('docs/backlog-log.md', lambda s: s.rstrip('\n') + '\n\n' + ENTRY)
print('docs for v' + V)
