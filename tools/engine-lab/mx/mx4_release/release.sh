#!/bin/bash
# Task MX-4 release (lane K): run in a fresh clone of main, after `git pull --rebase`, when desktop/release-freeze.json is NOT on main
# and MX-3 is already in index.html (release MX-2 and MX-3 first with their release.sh).
# Re-runs the edit script on main's index.html, VERSION = main + 0.001, fills the version into the texts, adds them to the backlog,
# the update notes, Where it stands and the plan's status, syncs the app (never desktop/app-version.json), lints.
# Then: run tools/ui-tests/taskMX_4.py (and taskMX_1 to 3) and the gate's quick run, fill @GATE@ in the backlog entry, commit 'v<ver>: task MX-4 ...' and push.
set -e
D=tools/engine-lab/mx/mx4_release
[ -f desktop/release-freeze.json ] && { echo "release freeze on main: wait"; exit 2; }
grep -q "/\* ===== task MX-3 (lane K" index.html || { echo "MX-3 is not in index.html yet: release it first"; exit 3; }
grep -q "/\* ===== task MX-4 (lane K" index.html && { echo "MX-4 already in index.html"; exit 3; }
CUR=$(grep -o "const VERSION='[0-9.]*'" index.html | grep -o "[0-9.]*[0-9]")
NEW=$(python3 -c "print('%.3f'%(float('$CUR')+0.001))")
V2=$(grep -o "^## [0-9]* November 2026, v[0-9.]*: task MX-2" docs/backlog-log.md | tail -1 | grep -o "v[0-9.]*" | tr -d v)
V3=$(grep -o "^## [0-9]* November 2026, v[0-9.]*: task MX-3" docs/backlog-log.md | tail -1 | grep -o "v[0-9.]*" | tr -d v)
echo "main $CUR, MX-4 releases as $NEW (MX-2 was $V2, MX-3 was $V3)"
python3 tools/engine-lab/mx/mx4.py
sed -i "s/const VERSION='$CUR'/const VERSION='$NEW'/" index.html
python3 - "$D" "$NEW" "$V2" "$V3" <<'PY'
import sys;D,V,V2,V3=sys.argv[1:5];f=lambda n:open(D+'/'+n).read().replace('@VER@',V).replace('@VER2@',V2).replace('@VER3@',V3)
p='docs/backlog-log.md';s=open(p).read().rstrip('\n')+'\n\n'+f('backlog-entry.md');open(p,'w').write(s)
p='desktop/update-notes.txt';s=open(p).read().rstrip('\n')+'\n'+f('update-note.txt');open(p,'w').write(s)
line=f('where-it-stands.md').rstrip('\n')
p='docs/device-backlog-2026-11-25.md';s=open(p).read();i=s.index('- Task MX (mixing engine, lane K');s=s[:i]+line+s[s.index('\n',i):];open(p,'w').write(s)
p='docs/mixing-build.md';s=open(p).read();a=s.index('| MX-4 | X3, X19 |');b=s.index('\n',a)
s=s[:a]+'| MX-4 | X3, X19 | the Ducker\'s Spectral focus (32 bands); Bass mono switch on tracks and the master; `MX_HOOKS.bandFilter` for lane E\'s band listen (X17) | **done** (v'+V+') |'+s[b:];open(p,'w').write(s)
PY
node desktop/scripts/sync-app.js | tail -1
git diff --quiet -- desktop/app-version.json || { echo "desktop/app-version.json changed: stop"; exit 4; }
[ -d tools/release-gate/.deps/node_modules/acorn ] || npm install -s --prefix tools/release-gate/.deps acorn@8.14.0 >/dev/null
[ -x desktop/node_modules/electron/dist/electron ] || (cd desktop && node node_modules/electron/install.js) || true
node tools/release-gate/lint.js index.html | tail -1
echo "now: python3 tools/ui-tests/taskMX_4.py index.html, gate.py --here --quick, fill @GATE@, commit 'v$NEW: task MX-4 ...' and push"
