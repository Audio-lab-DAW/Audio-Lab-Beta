#!/bin/bash
# Task WS-1 with WS-1b (lane Q): build the release on a fresh main. Does not commit or push.
#   bash tools/design-lab/ws/release.sh
# Applies ws1_edit.py to index.html, sets VERSION to the highest on main + 0.001, syncs the dev manifest (never
# desktop/app-version.json), writes the docs with release_ws1.py and runs the lint. The caller runs the UI tests and the smoke test.
set -e
if [ -f desktop/release-freeze.json ]; then echo "release freeze on main: do not push index.html"; exit 2; fi
python3 tools/design-lab/ws/ws1_edit.py index.html
CUR=$(grep -o "const VERSION='[0-9.]*'" index.html | grep -o "[0-9.]*[0-9]")
V=$(python3 -c "print('%.3f' % (float('$CUR') + 0.001))")
sed -i "s/const VERSION='$CUR'/const VERSION='$V'/" index.html
grep -q "const VERSION='$V'" index.html
node desktop/scripts/sync-app.js > /dev/null
git diff --quiet -- desktop/app-version.json || { echo "app-version.json changed: not allowed"; exit 3; }
python3 tools/design-lab/ws/release_ws1.py $V
node tools/release-gate/lint.js index.html
echo "VERSION $V"
