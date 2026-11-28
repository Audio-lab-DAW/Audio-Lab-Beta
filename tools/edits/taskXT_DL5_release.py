"""Task XT-DL5, the release half. Run on a fresh main AFTER XT-DL4 is released and `python3 tools/edits/taskXT_DL5.py index.html`
(which prints the version):  python3 tools/edits/taskXT_DL5_release.py <version>
Puts the test in tools/ui-tests, writes the update note, the backlog entry and the line in 'Where it stands'.
Then: node desktop/scripts/sync-app.js, the checks, check the freeze, push."""
import sys, os, re, shutil
V = sys.argv[1]; assert re.match(r'^0\.\d{3}$', V), V
H = os.path.dirname(os.path.abspath(__file__)); R = os.path.join(H, '..', '..')
def rd(p): return open(os.path.join(R, p), encoding='utf-8').read()
def wr(p, s): open(os.path.join(R, p), 'w', encoding='utf-8').write(s)
assert "const VERSION='%s'" % V in rd('index.html') and 'task XT-DL5' in rd('index.html'), 'run taskXT_DL5.py first'
assert 'task XT-DL4' in rd('index.html') and 'help.safeMode' in rd('docs/commands.md'), 'DL4 released first'
shutil.copy(os.path.join(H, 'taskXT_DL5_test.py'), os.path.join(R, 'tools', 'ui-tests', 'taskXT_DL5.py'))
s = rd('desktop/update-notes.txt').rstrip('\n') + '\n'
s += 'Advanced right-click (v%s): right-click a control for "Hide the Loop button" or "Customise the Loop button…" (rename, hide, put back); Workshop, What is changed brings any of it back.\n' % V
wr('desktop/update-notes.txt', s)
E = open(os.path.join(H, 'taskXT_DL5_log.md'), encoding='utf-8').read().replace('v0.000', 'v' + V)
wr('docs/backlog-log.md', rd('docs/backlog-log.md').rstrip('\n') + '\n\n' + E.strip('\n') + '\n')
s = rd('docs/device-backlog-2026-11-25.md')
a = '- Task XT (extensions and the Workshop, lane H, one step per run): '
h = re.search(r'\*\*Step DL5 built and tested, not yet released\*\*.*?the push\. ', s)
if h: s = s[:h.start()] + s[h.end():]
assert s.count(a) >= 1
s = s.replace(a, a + '**Step XT-DL5 done**, v%s: right-click a control of the transport bar, track headers or mixer: a marked Advanced group with "Hide the Loop button" and "Customise the Loop button…" (rename, hide, put back), explained on first use; protected controls cannot be hidden; every rule in What is changed. Next: DL6, moving controls and the picker. ' % V, 1)
wr('docs/device-backlog-2026-11-25.md', s)
print('ok', V)
