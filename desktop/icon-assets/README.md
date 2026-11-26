# AudioLab Pro icon assets (prepared 2026-11-26)

Main logo: **PR4** (Tapered + Satellite, LA1 proportions), white on orange `#F2661C`.
The colour is not final yet; these files use the current orange. Swapping the colour later means re-rendering these same files.

| File | Use |
|---|---|
| `icon.png` / `icon.svg` | 1024 px app icon on Apple's macOS grid (824 px rounded square, 100 px margin, soft shadow) |
| `icon.icns` | Mac app icon (16 to 1024 px) -> replaces `desktop/build/icon.icns` |
| `icon.ico` | Windows app icon (16 to 256 px) -> replaces `desktop/build/icon.ico` |
| `dock-icon.png` | replaces `desktop/dock-icon.png` (set as Dock icon at start) |
| `doc.icns` / `doc.ico` / `doc.png` | `.audiolab` document icon: white page with folded corner, orange atom, AUDIOLAB label -> replaces `desktop/build/doc.*` |
| `PR4-full.*` | full-bleed logo (no margin), for in-app use (About, splash) |
| `PR4-mark-black.*`, `PR4-mark-white.*` | logo mark alone in one colour, transparent background |
| `web-*.png` | favicon / web app manifest sizes |
| `picker/*.png` + `picker/icons.json` | the Settings icon picker: 45 icons (default + 44 choices), 512 px on the same Apple grid, with their display names and groups |

Design history and the canvas: project doc `claude/audiolab-app-icon-decisions.md`.
