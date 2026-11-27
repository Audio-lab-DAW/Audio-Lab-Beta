#!/bin/bash
# Looks at the Mac app icon on a macOS runner (task IC1). Run from the repository root after desktop/scripts/build-mac-icon.sh:
#   bash tools/mac-icon/proof.sh <out dir> [path to a built AudioLab Pro.app]
# 1. Icon Composer's own renderer (ictool) draws the '.icon' in every style: Default, Dark, Tinted, Clear.
# 2. Two stand-in apps (one with Assets.car + icon.icns, one with icon.icns only = the app before IC1) and, if given, the built app
#    are drawn by macOS itself (NSWorkspace) under each 'Icon & widget style', as far as a runner without a logged-in desktop allows.
set -uo pipefail
FAIL=0
blue() {  # blue <label> <output of render-icon>: the tile must be Orbit night navy, give or take 14 a channel (task IC4; IC1: Ocean blue 20 80 168)
  # at the sampled spot (35 %, 14 % of the picture) J3 shows the navy of its gradient: 22 31 65 (tools/icon-lab/ic4 render); the fill is 19 32 68
  local t; t=$(echo "$2" | awk '/^TILE/ {print $2, $3, $4}'); echo "   $1: tile colour $t"
  echo "$t" | awk '{ exit !(($1-21)^2 <= 196 && ($2-32)^2 <= 196 && ($3-66)^2 <= 196) }' || { echo "   NOT BLUE: $1"; FAIL=1; }
}
OUT="${1:-icon-proof}"; APP="${2:-}"
mkdir -p "$OUT"; OUT="$(cd "$OUT" && pwd)"
D=desktop; ICON=$D/icon-assets/mac-icon/AppIcon.icon
sw_vers | tee "$OUT/system.txt"
TAHOE=0; [ "$(sw_vers -productVersion | cut -d. -f1)" -ge 26 ] && TAHOE=1
DEV="${DEVELOPER_DIR:-$(xcode-select -p)}"
for x in /Applications/Xcode_*.app /Applications/Xcode.app; do [ -d "$x/Contents/Applications/Icon Composer.app" ] && IC="$x/Contents/Applications/Icon Composer.app"; done
ICTOOL="${IC:-}/Contents/Executables/ictool"
echo "ictool: $ICTOOL" | tee -a "$OUT/system.txt"
if [ -x "$ICTOOL" ]; then
  "$ICTOOL" --help > "$OUT/ictool-help.txt" 2>&1; head -60 "$OUT/ictool-help.txt"
  for r in Default Dark TintedLight TintedDark ClearLight ClearDark; do
    "$ICTOOL" "$ICON" --export-image --output-file "$OUT/ictool-$r.png" --platform macOS --rendition "$r" --width 512 --height 512 --scale 1 2>&1 | tail -3 \
    || "$ICTOOL" "$ICON" --export-preview macOS "$r" 512 512 1 "$OUT/ictool-$r.png" 2>&1 | tail -3
  done
else echo "no ictool on this runner"; fi

swiftc -O tools/mac-icon/render-icon.swift -o "$OUT/render-icon" 2>&1 | tail -5
mk() {  # mk <dir.app> <with car: 1/0> <bundle id>
  mkdir -p "$1/Contents/MacOS" "$1/Contents/Resources"
  printf '#!/bin/sh\nsleep 1\n' > "$1/Contents/MacOS/standin"; chmod +x "$1/Contents/MacOS/standin"
  cp $D/build/icon.icns "$1/Contents/Resources/icon.icns"
  [ "$2" = 1 ] && cp $D/build/Assets.car "$1/Contents/Resources/Assets.car"
  cat > "$1/Contents/Info.plist" <<P
<?xml version="1.0" encoding="UTF-8"?><!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict><key>CFBundleExecutable</key><string>standin</string><key>CFBundleIdentifier</key><string>$3</string>
<key>CFBundleName</key><string>Standin</string><key>CFBundlePackageType</key><string>APPL</string><key>CFBundleIconFile</key><string>icon.icns</string>
$([ "$2" = 1 ] && echo '<key>CFBundleIconName</key><string>AppIcon</string>')
<key>LSMinimumSystemVersion</key><string>11.0</string></dict></plist>
P
  codesign --force --sign - "$1" >/dev/null 2>&1
}
echo "--- icon style defaults before:"; defaults read -g AppleIconAppearanceTheme 2>&1; defaults read -g AppleInterfaceStyle 2>&1
W="$OUT/work"; rm -rf "$W"; mkdir -p "$W"
n=0
for style in Default:none:light RegularDark:RegularDark:dark TintedDark:TintedDark:dark ClearDark:ClearDark:dark; do
  name="${style%%:*}"; rest="${style#*:}"; theme="${rest%%:*}"; ui="${rest#*:}"
  if [ "$theme" = none ]; then defaults delete -g AppleIconAppearanceTheme 2>/dev/null; else defaults write -g AppleIconAppearanceTheme -string "$theme"; fi
  if [ "$ui" = dark ]; then defaults write -g AppleInterfaceStyle -string Dark; else defaults delete -g AppleInterfaceStyle 2>/dev/null; fi
  killall -u "$USER" cfprefsd iconservicesagent 2>/dev/null; sleep 2
  n=$((n+1))
  mk "$W/new-$name.app" 1 "com.audiolab.standin.new$n"; mk "$W/old-$name.app" 0 "com.audiolab.standin.old$n"
  # the first answer of the icon service can be a quick stand-in; ask, wait, ask again and keep the second picture
  "$OUT/render-icon" "$W/new-$name.app" "$OUT/system-$name-with-assets-car.png" 512 >/dev/null; "$OUT/render-icon" "$W/old-$name.app" "$OUT/system-$name-icns-only.png" 512 >/dev/null
  [ -n "$APP" ] && [ -d "$APP" ] && { cp -R "$APP" "$W/built-$name.app"; "$OUT/render-icon" "$W/built-$name.app" "$OUT/system-$name-built-app.png" 512 >/dev/null; }
  sleep 4
  echo "--- style $name"
  r=$("$OUT/render-icon" "$W/new-$name.app" "$OUT/system-$name-with-assets-car.png" 512); [ "$name" = Default ] || [ "$name" = RegularDark ] && [ "$TAHOE" = 1 ] && blue "stand-in app with Assets.car, $name" "$r"
  r=$("$OUT/render-icon" "$W/old-$name.app" "$OUT/system-$name-icns-only.png" 512); echo "   stand-in app with icon.icns only (the app before IC1), $name: $(echo "$r" | grep ^TILE)"
  if [ -n "$APP" ] && [ -d "$APP" ]; then r=$("$OUT/render-icon" "$W/built-$name.app" "$OUT/system-$name-built-app.png" 512); if { [ "$name" = Default ] || [ "$name" = RegularDark ]; } && [ "$TAHOE" = 1 ]; then blue "the built app, $name" "$r"; else echo "   the built app, $name: $(echo "$r" | grep ^TILE)"; fi; rm -rf "$W/built-$name.app"; fi
done
defaults delete -g AppleIconAppearanceTheme 2>/dev/null; defaults delete -g AppleInterfaceStyle 2>/dev/null
rm -rf "$W" "$OUT/render-icon"
cp $D/dock-icon.png "$OUT/reference-dock-icon-1024.png"
ls -la "$OUT"
[ "$FAIL" = 0 ] && echo "icon proof: blue in the Default and the Dark style" || { echo "icon proof FAILED: see NOT BLUE above"; exit 1; }
