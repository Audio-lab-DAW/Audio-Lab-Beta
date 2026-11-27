#!/bin/bash
# experiment (test branch only): which Icon Composer document keeps the blue under the Dark style
set -uo pipefail
OUT="$1"; mkdir -p "$OUT"; OUT="$(cd "$OUT" && pwd)"
for x in /Applications/Xcode_26*.app; do [ -L "$x" ] || X="$x"; done
export DEVELOPER_DIR="$X/Contents/Developer"; echo "Xcode $X"; ls -d /Applications/Xcode*
for x in /Applications/Xcode_*.app /Applications/Xcode.app; do [ -d "$x/Contents/Applications/Icon Composer.app" ] && IC="$x/Contents/Applications/Icon Composer.app"; done
ICTOOL="${IC:-}/Contents/Executables/ictool"
swiftc -O tools/mac-icon/render-icon.swift -o /tmp/render-icon
W=/tmp/vw; rm -rf $W; mkdir -p $W
mkdir -p tools/mac-icon/variants/v1-current tools/mac-icon/variants/v1-nofallback; cp -R desktop/icon-assets/mac-icon/AppIcon.icon tools/mac-icon/variants/v1-current/; cp -R desktop/icon-assets/mac-icon/AppIcon.icon tools/mac-icon/variants/v1-nofallback/
for d in tools/mac-icon/variants/*/; do
  v=$(basename "$d"); extra=""; [ "$v" = v1-nofallback ] && extra="--enable-icon-stack-fallback-generation=disabled"
  mkdir -p "$W/$v/car"
  xcrun actool "$d/AppIcon.icon" --compile "$W/$v/car" --app-icon AppIcon --include-all-app-icons --platform macosx --target-device mac --minimum-deployment-target 26.0 --output-partial-info-plist "$W/$v/p.plist" $extra 2>&1 | grep -v '^$' | tail -6
  echo "== $v: $(ls "$W/$v/car" | tr '\n' ' ')"
  xcrun assetutil --info "$W/$v/car/Assets.car" | python3 -c "
import json,sys,collections
r=[x for x in json.load(sys.stdin) if x.get('AssetType')]
print('   ',dict(collections.Counter(x['AssetType'] for x in r)))"
  if [ -x "$ICTOOL" ]; then for r in Default Dark; do "$ICTOOL" "$d/AppIcon.icon" --export-image --output-file "$OUT/$v-ictool-$r.png" --platform macOS --rendition $r --width 256 --height 256 --scale 1 >/dev/null 2>&1; done; fi
done
i=0
for style in Default RegularDark; do
  if [ $style = Default ]; then defaults delete -g AppleIconAppearanceTheme 2>/dev/null; else defaults write -g AppleIconAppearanceTheme -string $style; fi
  killall -u "$USER" cfprefsd iconservicesagent 2>/dev/null; sleep 2
  for d in $(ls -rd tools/mac-icon/variants/*/); do
    v=$(basename "$d"); i=$((i+1)); A="$W/$v-$style.app"
    mkdir -p "$A/Contents/MacOS" "$A/Contents/Resources"; printf '#!/bin/sh\nsleep 1\n' > "$A/Contents/MacOS/standin"; chmod +x "$A/Contents/MacOS/standin"
    cp desktop/build/icon.icns "$A/Contents/Resources/icon.icns"; cp "$W/$v/car/Assets.car" "$A/Contents/Resources/"
    cat > "$A/Contents/Info.plist" <<P
<?xml version="1.0" encoding="UTF-8"?><plist version="1.0"><dict><key>CFBundleExecutable</key><string>standin</string><key>CFBundleIdentifier</key><string>com.audiolab.rvar$i</string>
<key>CFBundleName</key><string>Standin</string><key>CFBundlePackageType</key><string>APPL</string><key>CFBundleIconFile</key><string>icon.icns</string><key>CFBundleIconName</key><string>AppIcon</string></dict></plist>
P
    codesign --force --sign - "$A" >/dev/null 2>&1
    /tmp/render-icon "$A" "$OUT/$v-system-$style.png" 256 >/dev/null
  done
done
defaults delete -g AppleIconAppearanceTheme 2>/dev/null
ls "$OUT" | wc -l
