#!/bin/bash
# Task MX-2 release (lane K): run in a fresh clone of main, after `git pull --rebase`, when desktop/release-freeze.json is NOT on main.
# Re-runs the edit script on main's index.html, VERSION = main + 0.001, fills the version into the texts, adds them to the backlog,
# the update notes, Where it stands and the plan's status, syncs the app (never desktop/app-version.json), lints.
# Then: run tools/ui-tests/taskMX_2.py and the smoke test, if main moved on a lot, re-run them and correct the backlog entry's test line, commit, push.
set -e
D=tools/engine-lab/mx/mx2_release
[ -f desktop/release-freeze.json ] && { echo "release freeze on main: wait"; exit 2; }
grep -q "/\* ===== task MX-2 (lane K" index.html && { echo "MX-2 already in index.html"; exit 3; }
CUR=$(grep -o "const VERSION='[0-9.]*'" index.html | grep -o "[0-9.]*[0-9]")
NEW=$(python3 -c "print('%.3f'%(float('$CUR')+0.001))")
echo "main $CUR, MX-2 releases as $NEW"
python3 tools/engine-lab/mx/mx2.py
sed -i "s/const VERSION='$CUR'/const VERSION='$NEW'/" index.html
python3 - "$D" "$NEW" <<'PY'
import sys;D,V=sys.argv[1],sys.argv[2];f=lambda n:open(D+'/'+n).read().replace('@VER@',V)
p='docs/backlog-log.md';s=open(p).read().rstrip('\n')+'\n\n'+f('backlog-entry.md');open(p,'w').write(s)
p='desktop/update-notes.txt';s=open(p).read().rstrip('\n')+'\n'+f('update-note.txt');open(p,'w').write(s)
line=f('where-it-stands.md').rstrip('\n')
p='docs/device-backlog-2026-11-25.md';s=open(p).read();i=s.index('- Task MX (mixing engine, lane K');s=s[:i]+line+s[s.index('\n',i):];open(p,'w').write(s)
p='docs/mixing-build.md';s=open(p).read();a=s.index('| MX-2 | X5, X6 |');b=s.index('\n',a)
s=s[:a]+'| MX-2 | X5, X6 | delay compensation for returns, sends and sidechain triggers, live and in export; latency changes re-aligned without a click; latency you can see, subtly, in few places; first the `S.pauto` export check (end of this file) | **done** (v'+V+') |'+s[b:];open(p,'w').write(s)
PY
node desktop/scripts/sync-app.js | tail -1
git diff --quiet -- desktop/app-version.json || { echo "desktop/app-version.json changed: stop"; exit 4; }
node tools/release-gate/lint.js index.html | tail -1
echo "now: python3 tools/ui-tests/taskMX_2.py index.html, the smoke test, fill @TESTS@ @SMOKE@, commit 'v$NEW: task MX-2 ...' and push"
