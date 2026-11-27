#!/bin/bash
# Compiles the Icon Composer document (icon-assets/mac-icon/AppIcon.icon) into build/Assets.car for macOS 26 (task IC1).
# Needs a Mac with Xcode 26 or newer (the first actool that reads '.icon'). Run from desktop/:  bash scripts/build-mac-icon.sh
# The app then carries BOTH icons: Assets.car + CFBundleIconName=AppIcon (macOS 26 and later) and icon.icns + CFBundleIconFile (older).
set -euo pipefail
cd "$(dirname "$0")/.."
ICON=icon-assets/mac-icon/AppIcon.icon
OUT=build/mac-icon
[ -f "$ICON/icon.json" ] || { echo "missing $ICON/icon.json"; exit 1; }

# Pick an Xcode whose major version is 26 or more: the selected one if it is new enough, else the newest installed.
ver() { /usr/libexec/PlistBuddy -c 'Print :CFBundleShortVersionString' "$1/Contents/version.plist" 2>/dev/null || echo 0; }
pick=""; pickv=0
cur="$(xcode-select -p 2>/dev/null | sed 's#/Contents/Developer$##')"
if [ -n "${cur}" ] && [ -d "$cur" ]; then v=$(ver "$cur"); if [ "${v%%.*}" -ge 26 ] 2>/dev/null; then pick="$cur"; pickv="$v"; fi; fi
if [ -z "$pick" ]; then
  for x in /Applications/Xcode_*.app /Applications/Xcode.app; do
    [ -d "$x" ] || continue; [ -L "$x" ] && continue
    case "$x" in *beta*|*Beta*|*_RC*|*Release_Candidate*) continue;; esac
    v=$(ver "$x"); [ "${v%%.*}" -ge 26 ] 2>/dev/null || continue
    if [ -z "$pick" ] || [ "$(printf '%s\n%s\n' "$pickv" "$v" | sort -V | tail -1)" = "$v" ]; then pick="$x"; pickv="$v"; fi
  done
fi
[ -n "$pick" ] || { echo "No Xcode 26 or newer on this Mac; installed:"; ls -d /Applications/Xcode* 2>/dev/null; exit 1; }
export DEVELOPER_DIR="$pick/Contents/Developer"
echo "Xcode for actool: $pick (version $pickv)"

run_actool() {
  rm -rf "$OUT"; mkdir -p "$OUT"
  xcrun actool "$ICON" --compile "$OUT" \
    --app-icon AppIcon --include-all-app-icons \
    --platform macosx --target-device mac --minimum-deployment-target 26.0 \
    --enable-on-demand-resources NO --development-region en \
    --output-partial-info-plist "$OUT/partial-info.plist" \
    --output-format human-readable-text --notices --warnings --errors "$@"
}
# First try without the flat pictures actool adds for macOS 15 and older (an undocumented switch): those systems then take icon.icns,
# which has a hand-drawn picture for every size. If this actool does not know the switch, compile the plain way.
if ! run_actool --enable-icon-stack-fallback-generation=disabled || [ ! -s "$OUT/Assets.car" ]; then
  echo "actool refused --enable-icon-stack-fallback-generation=disabled; compiling without it"
  run_actool
fi
echo "--- actool wrote:"; ls -la "$OUT"
echo "--- partial Info.plist:"; plutil -p "$OUT/partial-info.plist" || true
[ -s "$OUT/Assets.car" ] || { echo "actool wrote no Assets.car"; exit 1; }
xcrun assetutil --info "$OUT/Assets.car" > "$OUT/assetutil.json"
python3 - "$OUT/assetutil.json" <<'PY'
import json, sys, collections
rows = [r for r in json.load(open(sys.argv[1])) if isinstance(r, dict) and r.get('AssetType')]
print('--- Assets.car: %d renditions' % len(rows))
seen = collections.Counter((r.get('AssetType'), r.get('Name'), r.get('Appearance', '(any)'), r.get('RenditionName', '')) for r in rows)
for k, n in sorted(seen.items(), key=str): print('   %-22s %-12s %-28s %s  x%d' % (k + (n,)))
kinds = {r.get('AssetType') for r in rows if r.get('Name') == 'AppIcon'}
stacks = {r.get('Appearance') for r in rows if r.get('AssetType') == 'IconImageStack' and r.get('Name') == 'AppIcon'}
need = {'NSAppearanceNameAqua', 'NSAppearanceNameDarkAqua', 'ISAppearanceTintable'}
if not need <= stacks: sys.exit('Assets.car lacks the layered AppIcon for: ' + ', '.join(sorted(need - stacks)))
# The tile colour of each appearance must be the Ocean blue (a 'Color' layer), never the system's grey gradient.
bad = []
for r in rows:
    if r.get('AssetType') == 'IconImageStack' and r.get('Name') == 'AppIcon':
        first = (r.get('Layers') or [{}])[0]; c = first.get('Color components') or []
        okc = first.get('AssetType') == 'Color' and len(c) == 4 and abs(c[0] - 0.078) < 0.01 and abs(c[1] - 0.314) < 0.01 and abs(c[2] - 0.659) < 0.01
        print('   tile of %-26s %s' % (r.get('Appearance'), ('blue ' + str([round(v, 3) for v in c])) if okc else 'NOT the blue: ' + str(first.get('Name'))))
        if not okc: bad.append(r.get('Appearance'))
if bad: sys.exit('the tile is not blue for: ' + ', '.join(map(str, bad)))
flat = sum(1 for r in rows if r.get('AssetType') in ('Icon Image', 'MultiSized Image'))
print('   flat pictures for macOS 15 and older inside Assets.car: %d (0 = those systems use icon.icns)' % flat)
PY
cp "$OUT/Assets.car" build/Assets.car
echo "build/Assets.car ready ($(stat -f %z build/Assets.car) bytes, sha256 $(shasum -a 256 build/Assets.car | cut -d' ' -f1))"
