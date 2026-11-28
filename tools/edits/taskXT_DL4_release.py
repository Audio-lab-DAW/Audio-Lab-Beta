"""Task XT-DL4, the release half. Run on a fresh main AFTER taskXT_DL3 is in index.html (released) and
`python3 tools/edits/taskXT_DL4.py index.html` (which prints the version):
  python3 tools/edits/taskXT_DL4_release.py <version>
Puts the docs that only hold once DL4 is in index.html in place (the two new rows of docs/commands.md, the test
tools/ui-tests/taskXT_DL4.py) and writes the update note, the backlog entry and the line in 'Where it stands'.
Then: node desktop/scripts/sync-app.js, the checks, check the freeze, push."""
import sys, os, re, shutil
V = sys.argv[1]; assert re.match(r'^0\.\d{3}$', V), V
H = os.path.dirname(os.path.abspath(__file__)); R = os.path.join(H, '..', '..')
def rd(p): return open(os.path.join(R, p), encoding='utf-8').read()
def wr(p, s): open(os.path.join(R, p), 'w', encoding='utf-8').write(s)
assert "const VERSION='%s'" % V in rd('index.html') and 'task XT-DL4' in rd('index.html'), 'run taskXT_DL4.py first'
s = rd('docs/commands.md')
a = "| `view.workshop` | Workshop: advanced settings by id |  |  |"
assert s.count(a) == 1 and 'help.safeMode' not in s, 'DL3 released first'
i = s.index(a); j = s.index('\n', i) + 1
s = s[:j] + ("| `view.whatIsChanged` | What is changed: every customisation, with reset |  |  | %s |\n"
             "| `help.safeMode` | Restart in safe mode (or leave it) |  |  | %s |\n" % (V, V)) + s[j:]
wr('docs/commands.md', s)
shutil.copy(os.path.join(H, 'taskXT_DL4_test.py'), os.path.join(R, 'tools', 'ui-tests', 'taskXT_DL4.py'))
s = rd('desktop/update-notes.txt').rstrip('\n') + '\n'
s += 'Safe mode (v%s): Restart, Restart in safe mode…, or hold Shift while AudioLab starts: it starts as it came, deleting nothing. Workshop, What is changed: every customisation in one list, each with ✕, and a reset you can undo.\n' % V
wr('desktop/update-notes.txt', s)
E = open(os.path.join(H, 'taskXT_DL4_log.md'), encoding='utf-8').read().replace('v0.000', 'v' + V)
wr('docs/backlog-log.md', rd('docs/backlog-log.md').rstrip('\n') + '\n\n' + E.strip('\n') + '\n')
s = rd('docs/device-backlog-2026-11-25.md')
a = '- Task XT (extensions and the Workshop, lane H, one step per run): '
h = re.search(r'\*\*Step DL4 built and tested, not yet released\*\*.*?the push\. ', s)
if h: s = s[:h.start()] + s[h.end():]
assert s.count(a) >= 1
s = s.replace(a, a + '**Step XT-DL4 done**, v%s: safe mode (Restart › Restart in safe mode…, Shift held at start, offered after a start that did not finish): AudioLab starts as it came and deletes nothing, a bar says so; the Workshop\'s What is changed tab lists every customisation (settings, Workshop values, shortcuts, layout) with ✕ each, and Reset my customisations keeps a backup and can be undone. Next: DL5, the rules engine with the right-click Advanced entries. ' % V, 1)
wr('docs/device-backlog-2026-11-25.md', s)
print('ok', V)
