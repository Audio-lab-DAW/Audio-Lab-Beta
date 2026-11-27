#!/bin/bash
# Starts a built AudioLab Pro.app on the macOS runner and photographs the screen with the Dock, once per icon style (task IC1):
#   bash tools/mac-icon/dock-shot.sh <AudioLab Pro.app> <out dir> <label>
set -uo pipefail
APP="$1"; OUT="$2"; LABEL="$3"; mkdir -p "$OUT"
defaults write com.apple.dock tilesize -int 128; defaults write com.apple.dock autohide -bool false; defaults write com.apple.dock magnification -bool false
for style in Default RegularDark; do
  if [ "$style" = Default ]; then defaults delete -g AppleIconAppearanceTheme 2>/dev/null; defaults delete -g AppleInterfaceStyle 2>/dev/null
  else defaults write -g AppleIconAppearanceTheme -string "$style"; defaults write -g AppleInterfaceStyle -string Dark; fi
  killall -u "$USER" cfprefsd iconservicesagent 2>/dev/null; sleep 1; killall Dock 2>/dev/null; sleep 6
  open -n "$APP" || echo "could not start $APP"
  sleep 30
  screencapture -x "$OUT/screen-$LABEL-$style.png" && echo "wrote screen-$LABEL-$style.png" || echo "screencapture failed"
  pkill -f "$(basename "$APP" .app).app/Contents/MacOS" 2>/dev/null; sleep 4
done
defaults delete -g AppleIconAppearanceTheme 2>/dev/null; defaults delete -g AppleInterfaceStyle 2>/dev/null
