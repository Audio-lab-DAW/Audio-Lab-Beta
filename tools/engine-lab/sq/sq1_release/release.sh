#!/bin/bash
# Task SQ1 release (lane N): run in a fresh clone of main, after `git pull`, when desktop/release-freeze.json is NOT on main.
# Re-runs the edit script on main's index.html, VERSION = main + 0.001, fills the version into the texts here, adds them to the
# backlog, the update notes and Where it stands, syncs the app, lints. Then: run tools/ui-tests/taskSQ1.py, commit, push.
set -e
D=tools/engine-lab/sq/sq1_release
[ -f desktop/release-freeze.json ] && { echo "release freeze on main: wait"; exit 2; }
grep -q "const SQ=" index.html && { echo "SQ1 already in index.html"; exit 3; }
CUR=$(grep -o "const VERSION='[0-9.]*'" index.html | grep -o "[0-9.]*[0-9]")
NEW=$(python3 -c "print('%.3f'%(float('$CUR')+0.001))")
OLDV=$(grep -o "const SQ={v:'[0-9.]*'" tools/engine-lab/sq/sq1.js | grep -o "[0-9]\.[0-9]*")
echo "main $CUR, SQ1 releases as $NEW (texts said $OLDV)"
sed -i "s/v$OLDV/v$NEW/g;s/'$OLDV'/'$NEW'/g" docs/quality-build.md tools/engine-lab/sq/sq1.js $D/*.md $D/*.txt
python3 tools/engine-lab/sq/sq1.py
sed -i "s/const VERSION='$CUR'/const VERSION='$NEW'/" index.html
python3 - "$D" <<'PY'
import sys;D=sys.argv[1]
p='docs/backlog-log.md';s=open(p).read().rstrip('\n')+'\n\n'+open(D+'/backlog-entry.md').read();open(p,'w').write(s)
p='desktop/update-notes.txt';s=open(p).read().rstrip('\n')+'\n'+open(D+'/update-note.txt').read();open(p,'w').write(s)
line=open(D+'/where-it-stands.md').read().rstrip('\n')
p='docs/device-backlog-2026-11-25.md';s=open(p).read();i=s.index('- Task SQ (sound quality, lane N');s=s[:i]+line+s[s.index('\n',i):];open(p,'w').write(s)
PY
node desktop/scripts/sync-app.js | tail -1
node tools/release-gate/lint.js index.html | tail -1
echo "now: python3 tools/ui-tests/taskSQ1.py index.html, then commit 'v$NEW: task SQ1 ...' and push"
