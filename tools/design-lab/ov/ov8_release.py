#!/usr/bin/env python3
"""Task OV8 release (lane F): run on a fresh main once desktop/release-freeze.json is gone.
   python3 tools/design-lab/ov/ov8_release.py "<smoke test result in one sentence>"
Applies ov8.py when index.html does not have it yet, takes VERSION = the highest on main + 0.001, writes the notes line, the
backlog entry (entry_ov8.md), the line in Where it stands, marks OV8 done in section 5, sets the version of the two rows in
docs/commands.md and runs desktop/scripts/sync-app.js (dev manifest only). Then: lint, taskOV8.py, commit, push."""
import sys, os, re, subprocess
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
os.chdir(ROOT)
assert not os.path.exists('desktop/release-freeze.json'), 'release freeze on main: wait'
SMOKE = sys.argv[1] if len(sys.argv) > 1 else 'not run'
s = open('index.html', encoding='utf-8').read()
if 'task OV8' not in s:
    subprocess.check_call([sys.executable, 'tools/design-lab/ov/ov8.py', 'index.html']); s = open('index.html', encoding='utf-8').read()
m = re.search(r"const VERSION='(\d+)\.(\d+)'", s); assert m
V = '%s.%03d' % (m.group(1), int(m.group(2)) + 1)
s = s.replace(m.group(0), "const VERSION='%s'" % V, 1); open('index.html', 'w', encoding='utf-8').write(s)
def edit(p, old, new):
    t = open(p, encoding='utf-8').read(); assert t.count(old) == 1, (p, old[:80]); open(p, 'w', encoding='utf-8').write(t.replace(old, new))
with open('desktop/update-notes.txt', 'a', encoding='utf-8') as f:
    f.write('Command palette (v%s): press ⌘K (Ctrl+K) and type a few letters of any command; Recent comes first, keys show on the right, and the last row asks the Assistant with what you typed (⌘K again opens the Assistant). Press ? for a sheet of every shortcut.\n' % V)
e = open('tools/design-lab/ov/entry_ov8.md', encoding='utf-8').read().replace('{V}', V).replace('{SMOKE}', SMOKE)
with open('docs/backlog-log.md', 'a', encoding='utf-8') as f: f.write(e)
t = open('docs/device-backlog-2026-11-25.md', encoding='utf-8').read()
i = t.index('- Task OV (overlays'); j = t.index('\n', i)
t = t[:i] + ('- Task OV (overlays: menus, dialogs, tooltips, notifications, drag and drop, palette; the user\'s picks `R2 D3 T3 N1 X1 K1`, lane F, one step per run): '
    '**step OV8 done (v%s)**: ⌘K opens the command palette (every command, fuzzy search, keys on the right, Recent first, the last row asks the Assistant, ⌘K again opens it); ? shows the key sheet. '
    'Before: OV2 (v0.278, v0.286) right-click menus in R2, OV1 (v0.256) tokens. Next: S16 timings, S18, E20, LM1 to LM3; then OV6, OV4, OV5, OV7, OV3.' % V) + t[j:]
open('docs/device-backlog-2026-11-25.md', 'w', encoding='utf-8').write(t)
edit('docs/design-round-5-overlays.md', '| **OV8** | Command palette', '| **OV8** (built as K1, on ⌘K with the Assistant inside) ✅ done v%s | Command palette' % V)
c = open('docs/commands.md', encoding='utf-8').read()
if '`help.palette`' not in c:
    edit('docs/commands.md', "| `help.assistant` | Assistant | `Mod+K` | `ai` | 0.273 |",
         "| `help.assistant` | Assistant (no default key from 0.289: `Mod+K` opens the palette, `Mod+K` again the Assistant; a key the user gave it is kept) |  | `ai` | 0.273 |\n| `help.palette` | Command palette (every command, and the Assistant) | `Mod+K` | `help.palette` | 0.289 |\n| `help.keySheet` | Key sheet (every shortcut at a glance) | `?` | `help.keySheet` | 0.289 |")
c = open('docs/commands.md', encoding='utf-8').read()
c = c.replace('from 0.289: `Mod+K`', 'from %s: `Mod+K`' % V).replace('| `help.palette` | 0.289 |', '| `help.palette` | %s |' % V).replace('| `help.keySheet` | 0.289 |', '| `help.keySheet` | %s |' % V)
open('docs/commands.md', 'w', encoding='utf-8').write(c)
subprocess.check_call(['node', 'desktop/scripts/sync-app.js'])
print('released as', V)
