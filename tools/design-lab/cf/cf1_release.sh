#!/bin/sh
# Task CF-1 release: run from the repo root on a fresh main (no freeze file). Applies the edit, the commands row, the version, the dev manifest.
set -e
test ! -e desktop/release-freeze.json
V=$(grep -o "const VERSION='[0-9.]*'" index.html | grep -o "[0-9][0-9.]*")
N=$(python3 -c "print('%.3f'%($V+0.001))")
python3 tools/design-lab/cf/cf1_edit.py index.html --commands docs/commands.md --version $N
sed -i "s/const VERSION='$V',BUILD='[^']*'/const VERSION='$N',BUILD='28 November 2026'/" index.html
grep -q "const VERSION='$N'" index.html
node tools/release-gate/lint.js index.html
node desktop/scripts/sync-app.js
echo $N > /tmp/claude-0/ver
