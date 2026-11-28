"""Task XT-DL3, the release half (built and tested on v0.294 during the release freeze of 27 Nov, 22:26 UTC; index.html waited).
Run on a fresh main AFTER `python3 tools/edits/taskXT_DL3.py index.html` (which prints the version):
  python3 tools/edits/taskXT_DL3_release.py <version>
It puts the docs that only hold once DL3 is in index.html in place (so the DL1, DL2 and DL3 tests do not fail on a main without it):
docs/settings-ids.md, the new rows of docs/commands.md and docs/ids.md, the test tools/ui-tests/taskXT_DL3.py; and writes the
update note, the backlog entry and the line in 'Where it stands'. Then: node desktop/scripts/sync-app.js, tests, push."""
import sys, os, re, shutil
V = sys.argv[1]; assert re.match(r'^0\.\d{3}$', V), V
H = os.path.dirname(os.path.abspath(__file__)); R = os.path.join(H, '..', '..')
def rd(p): return open(os.path.join(R, p), encoding='utf-8').read()
def wr(p, s): open(os.path.join(R, p), 'w', encoding='utf-8').write(s)
assert "const VERSION='%s'" % V in rd('index.html') and 'task XT-DL3' in rd('index.html'), 'run taskXT_DL3.py first'
# docs that describe what DL3 adds
wr('docs/settings-ids.md', open(os.path.join(H, 'taskXT_DL3_settings-ids.md'), encoding='utf-8').read().replace('0.295', V))
s = rd('docs/commands.md')
a = "| `view.closeWindows` | Close all floating windows |  | `closewins` | 0.273 |\n"
assert s.count(a) == 1 and 'view.workshop' not in s
s = s.replace(a, a + "| `view.workshop` | Workshop: advanced settings by id |  |  | %s |\n" % V)
a = "| `ni.levelJourney` | Level journey of the selected track (level after each device) (lane D, task NI-7; listed by XT-DL12) |  |  | 0.279 |\n"
if '`ni.monoLoss`' not in s:
    assert s.count(a) == 1
    s = s.replace(a, a + "| `ni.monoLoss` | Mono loss map (what each track loses in mono, band by band) (lane D; listed by XT-DL3) |  |  | 0.292 |\n")
wr('docs/commands.md', s)
s = rd('docs/ids.md')
a = "| `mixer.cables.clashes` | cable legend Clashes switch | `.cablg [data-ni=clash]` | 0.266 |\n"
assert s.count(a) == 1 and 'mixer.strip.output' not in s
s = s.replace(a, a + "| `mixer.strip.sendPrePost` | send before or after the fader ring (lane K, MX-1; named by XT-DL3) | `.mxsr .mxpp` | %s |\n"
              "| `mixer.strip.output` | channel Output button (lane K, MX-1; named by XT-DL3) | `.mx:not(.master) .mxout` | %s |\n"
              "| `mixer.master.monoLoss` | Mono loss button (lane D; named by XT-DL3) | `.mx.master [data-niml]` | %s |\n" % (V, V, V))
wr('docs/ids.md', s)
shutil.copy(os.path.join(H, 'taskXT_DL3_test.py'), os.path.join(R, 'tools', 'ui-tests', 'taskXT_DL3.py'))
# the update note (one line)
s = rd('desktop/update-notes.txt').rstrip('\n') + '\n'
s += 'Workshop (v%s): right-click the logo, Workshop… An advanced list of every setting by its id, with its default and range, a few values with no other control (how many steps Undo keeps, memory for frozen tracks) and the locked safety values; ↺ puts any change back.\n' % V
wr('desktop/update-notes.txt', s)
# the backlog entry
E = open(os.path.join(H, 'taskXT_DL3_log.md'), encoding='utf-8').read().replace('v0.295', 'v' + V)
s = rd('docs/backlog-log.md').rstrip('\n') + '\n\n' + E.strip('\n') + '\n'
wr('docs/backlog-log.md', s)
# Where it stands
s = rd('docs/device-backlog-2026-11-25.md')
a = '- Task XT (extensions and the Workshop, lane H, one step per run): '
h = re.search(r'\*\*Step DL3 built and tested, not yet released\*\*.*?the push\. ', s)
if h:  # the held note of the freeze run gives way to the done note
    s = s[:h.start()] + s[h.end():]; i = s.index(a)
    s = s[:i] + '- Task XT (extensions and the Workshop, lane H, one step per run): ' + s[i + len(a):]
assert s.count(a) >= 1
s = s.replace(a, a + '**Step XT-DL3 done**, v%s: the advanced settings list, the first visible part of the Workshop: its own window from the logo menu (Workshop…, marked Advanced, a first-use note on how to undo), every setting by a stable id (102 from Settings, 8 with no control in Settings, 4 locked; `docs/settings-ids.md`), search, filters, ↺ per row, what is kept; Undo\'s depth opened (`edit.undoSteps`). Next: DL4, safe mode. ' % V, 1)
wr('docs/device-backlog-2026-11-25.md', s)
print('ok', V)
