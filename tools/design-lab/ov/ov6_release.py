#!/usr/bin/env python3
"""Task OV6a release (lane F): run on a fresh main once desktop/release-freeze.json is gone.
   python3 tools/design-lab/ov/ov6_release.py "<smoke test result in one sentence>"
Applies ov6.py when index.html does not have it yet, takes VERSION = the highest on main + 0.001, puts the test into tools/ui-tests,
writes the notes line, the backlog entry (entry_ov6a.md), the line in Where it stands, marks OV6a done in section 5 and runs
desktop/scripts/sync-app.js (dev manifest only). Then: lint, taskOV6a.py, commit, push."""
import sys, os, re, subprocess, shutil
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
os.chdir(ROOT)
assert not os.path.exists('desktop/release-freeze.json'), 'release freeze on main: wait'
SMOKE = sys.argv[1] if len(sys.argv) > 1 else 'not run'
s = open('index.html', encoding='utf-8').read()
if 'task OV6a' not in s:
    subprocess.check_call([sys.executable, 'tools/design-lab/ov/ov6.py', 'index.html']); s = open('index.html', encoding='utf-8').read()
m = re.search(r"const VERSION='(\d+)\.(\d+)'", s); assert m
V = '%s.%03d' % (m.group(1), int(m.group(2)) + 1)
s = s.replace(m.group(0), "const VERSION='%s'" % V, 1); open('index.html', 'w', encoding='utf-8').write(s)
shutil.copy('tools/design-lab/ov/taskOV6a.py', 'tools/ui-tests/taskOV6a.py')
def edit(p, old, new):
    t = open(p, encoding='utf-8').read(); assert t.count(old) == 1, (p, old[:80]); open(p, 'w', encoding='utf-8').write(t.replace(old, new))
with open('desktop/update-notes.txt', 'a', encoding='utf-8') as f:
    f.write('Tooltips (v%s): a card on an amber line from the control, with its name, key, value now, default and scope; the next one shows at once, you can move onto it to read, Esc hides it, and Tab shows it too.\n' % V)
e = open('tools/design-lab/ov/entry_ov6a.md', encoding='utf-8').read().replace('{V}', V).replace('{SMOKE}', SMOKE)
with open('docs/backlog-log.md', 'a', encoding='utf-8') as f: f.write(e)
t = open('docs/device-backlog-2026-11-25.md', encoding='utf-8').read()
i = t.index('- Task OV (overlays'); j = t.index('\n', i)
t = t[:i] + ('- Task OV (overlays: menus, dialogs, tooltips, notifications, drag and drop, palette; the user\'s picks `R2 D3 T3 N1 X1 K1`, lane F, one step per run): '
    '**step OV6a done (v%s)**: tooltips are T3 callouts (amber leader, name and key, value now, default and scope; 500 ms then at once; hoverable; Esc; keyboard focus). '
    'Before: OV8 (v0.300) palette, OV2 (v0.278, v0.286) right-click menus in R2, OV1 (v0.256) tokens. Next: OV6b (texts for the controls without one), then OV4, OV5, OV7, OV3; S16, S18, E20, LM1 to LM3.' % V) + t[j:]
open('docs/device-backlog-2026-11-25.md', 'w', encoding='utf-8').write(t)
edit('docs/design-round-5-overlays.md', '| **OV6** | Help line plus tags (T1).', '| **OV6** (built as T3) part a ✅ done v%s (callouts with a leader); part b open (texts for the controls without one) | Help line plus tags (T1).' % V)
subprocess.check_call(['node', 'desktop/scripts/sync-app.js'])
print('released as', V)
