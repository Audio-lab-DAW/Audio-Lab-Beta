# AudioLab Studio – desktop app (Electron)

Runs the same `index.html` as the website, as a real Mac and Windows app.

What the desktop app adds over the browser:
- Cross-origin isolation always on (SharedArrayBuffer, the fast meter path).
- Direct audio-output selection (iFi Gryphon etc.) – no permission-policy blocks.
- Audio never throttled when the window is hidden or in the background.
- Double-click `.audiolab` files to open them; File ▸ Open Project (Cmd/Ctrl+O).
- Remembers window size and position.
- Auto-update from GitHub Releases (Windows installs by itself; the unsigned Mac build tells you and opens the download page).

## Get the apps (no tools needed)
1. GitHub repo ▸ **Actions** ▸ enable workflows if asked.
2. Run **Build desktop apps** (Actions ▸ *Build desktop apps* ▸ *Run workflow*), or push a tag named `desktop-v0.114`.
3. After ~10 minutes the **Releases** page holds:
   - `AudioLab Studio-<version>-arm64.dmg` – Mac Apple Silicon
   - `AudioLab Studio Setup <version>.exe` – Windows 64-bit

### Opening the unsigned Mac app the first time
macOS blocks apps without an Apple Developer signature. Drag it into Applications, then **right-click ▸ Open ▸ Open** once. If macOS still refuses: System Settings ▸ Privacy & Security ▸ *Open Anyway*.
Windows may show "Windows protected your PC": click *More info* ▸ *Run anyway*.

## Develop locally
```
cd desktop
npm install
npm start          # copies ../index.html into app/ and opens the window
npm run dist:mac   # on a Mac  -> dist/*.dmg
npm run dist:win   # on Windows -> dist/*.exe
```
`npm run sync` copies the current `../index.html` and sets the app version from `VERSION` in it.

## Releasing a new version
Update `index.html` (bump `VERSION`), push, then push a tag `desktop-vX.Y` (or run the workflow by hand). Installed apps pick it up on their next start.
