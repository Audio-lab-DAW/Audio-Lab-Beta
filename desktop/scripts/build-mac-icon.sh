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
run_actool
echo "--- actool wrote:"; ls -la "$OUT"
echo "--- partial Info.plist:"; plutil -p "$OUT/partial-info.plist" || true
[ -s "$OUT/Assets.car" ] || { echo "actool wrote no Assets.car"; exit 1; }
xcrun assetutil --info "$OUT/Assets.car" > "$OUT/assetutil.json"
python3 ../tools/mac-icon/check-car.py "$OUT/assetutil.json"
cp "$OUT/Assets.car" build/Assets.car
echo "build/Assets.car ready ($(stat -f %z build/Assets.car) bytes, sha256 $(shasum -a 256 build/Assets.car | cut -d' ' -f1))"
