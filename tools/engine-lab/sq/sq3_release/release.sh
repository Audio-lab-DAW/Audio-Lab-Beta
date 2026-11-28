#!/bin/bash
# Task SQ3 release (lane N): run in a fresh clone of main, after `git pull`, when desktop/release-freeze.json is NOT on main and SQ1 is
# already released (const SQ= in index.html). Re-runs the edit script, VERSION = main + 0.001, fills the versions into the texts here,
# adds them to the backlog, the update notes and Where it stands, syncs the app, lints. Then: run the tests, commit, push.
set -e
D=tools/engine-lab/sq/sq3_release
[ -f desktop/release-freeze.json ] && { echo "release freeze on main: wait"; exit 2; }
grep -q "const SQ=" index.html || { echo "SQ1 is not released yet: release it first (sq1_release/release.sh)"; exit 3; }
grep -q "const SQRS=" index.html && { echo "SQ3 already in index.html"; exit 3; }
CUR=$(grep -o "const VERSION='[0-9.]*'" index.html | grep -o "[0-9.]*[0-9]")
NEW=$(python3 -c "print('%.3f'%(float('$CUR')+0.001))")
SQ1V=$(grep -o "const SQ={v:'[0-9.]*'" index.html | grep -o "[0-9]\.[0-9]*")
echo "main $CUR (SQ1 in $SQ1V), SQ3 releases as $NEW"
sed -i "s/vX\.XXX/v$NEW/g;s/vSQ1V/v$SQ1V/g" $D/*.md $D/*.txt
sed -i "s/released after SQ1 with \`tools\/engine-lab\/sq\/sq3_release\/release.sh\`/**done**, v$NEW/;s/## SQ3: resample once (built; released after SQ1)/## SQ3: resample once (done, v$NEW)/" docs/quality-build.md
python3 tools/engine-lab/sq/sq3.py
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
echo "now: python3 tools/ui-tests/taskSQ3.py . && python3 tools/ui-tests/taskSQ1.py . , gate --here --quick, then commit 'v$NEW: task SQ3 ...' and push"
