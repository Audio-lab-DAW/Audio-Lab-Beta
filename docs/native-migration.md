# From the Electron app to the native AudioLab (task MG1)

Written 27 November 2026 for the user's wish of that evening (19:36 Brussels, in `docs/native-mac-picks.md`):

> "Can we have it so that the people that are on Electron can just update from inside the app and then it just starts installing the native version? And can we have a special window popping up explaining that we are going to an actual native version? And then they can press OK or do it later or something. And it should pop up in the center and be persistent until someone clicks something or clicks it away."

The native app does not exist yet (task NB builds the engine; packaging is stage N7). MG1 builds the **path** now, so that it is in the Electron shell before the native app ships. Nothing is offered to anyone until the release gate puts a `native` block into the live manifest.

This document is also the contract for N7: **section 4 is the folder the native app imports on its first start.**

## 1. What the user sees

1. The Electron app reads the update manifest every hour (as it always did). When the manifest has a `native` block that this computer can install, and the user did not choose Later in the last 3 days, a window opens in the centre of the app:
   - Title: **AudioLab is becoming a native app**.
   - What changes: its own sound engine (lower latency, steadier playback), VST3 plug-ins inside AudioLab, the same look.
   - What comes along: every project (open tabs and Saved projects, with their audio), settings, presets, controller mappings, the app icon choice, the recent list. This app stays, so the user can go back.
   - Size and time: the download in MB (amber unit) and "about 1 minute on a fast connection, up to N on a slow one".
   - Mac: where it goes, and that macOS normally opens it straight away (see 5.1). Windows: per-user install, and what to click if SmartScreen shows.
   - Buttons **Later** (Esc) and **Install now** (Enter). The close cross is Later.
2. It stays until a button is clicked. A click beside it, keys and time do nothing. While something plays, records or exports, or the update window is open, it waits until that has been quiet for 1.5 s before it opens.
3. **Later** hides it for 3 days (also across restarts; stored by the shell in `native-migrate.json` in the user-data folder). The offer stays in:
   - the **Updates** window (a green row, "Install the native AudioLab…"),
   - the app menu (Mac: AudioLab Pro menu; Windows: Help): **Install the native AudioLab…**, or **Open the native AudioLab** once installed,
   - the command list: **Install the native AudioLab**.
4. **Install now** shows five steps: Download (progress bar, MB), Check (sha256, and the Ed25519 signature when the shell has a key), Projects and settings (n of m), Install, Open the native app. Then: "The native AudioLab is opening. This app closes in a moment." and the Electron app quits.
5. Anything fails: "The native AudioLab was not installed" with the reason (checksum, signature, incomplete download, could not export, could not install), **Try again** and **Later**. Nothing is half-done: the export happens only after the download checked out, and the install only after the export read back correctly.
6. Mac, if macOS still stops the app: "One more step on this Mac" with the Open Anyway steps, buttons Show in Finder, Privacy & Security (opens System Settings), Open it again.

The window is built on lane F's overlay tokens (`--ov-*`: label style, key hints, motion 140 ms × `--ov-mo`, hairlines, amber units) in the same family as the update window. Lane F's D3 pick is "in place, no window", which does not fit a centred persistent window; the user's wish asks for a centred window, so it is one. In Light mode (`body.lite`) and with reduced motion it appears at once on a solid background.

## 2. The manifest block (`desktop/app-version.json`)

Optional. Shells before MG1 read only `version`, `sha256`, `size`, `minShell` and `notes`, so they ignore it (tested: a v0.261 shell reads such a manifest as before).

```json
"native": {
  "version": "1.0.0",
  "released": "2026-12-15",
  "notes": "one line per change",
  "platforms": {
    "darwin-arm64": { "url": "https://…/AudioLab-1.0.0-mac-arm64.zip", "size": 123456789, "sha256": "64 hex", "signature": "", "minOS": "13.0", "kind": "zip", "app": "AudioLab.app" },
    "win32-x64":    { "url": "https://…/AudioLab-1.0.0-Setup.exe",     "size": 123456789, "sha256": "64 hex", "signature": "", "minOS": "10.0.19041", "kind": "exe", "args": [] }
  }
}
```

- Platform keys: `darwin-arm64`, `darwin-x64`, `darwin` (any Mac), `win32-x64`, `win32-arm64`, `win32`. The shell takes the most specific one for `process.platform` and `process.arch`.
- `url`: https only (the shell refuses plain http outside its tests).
- `kind`: Mac `zip` (made with `ditto -c -k --keepParent AudioLab.app`) or `dmg`; Windows `exe` (a per-user installer).
- `app`: the bundle name inside the zip or DMG. It must **not** be `AudioLab Pro.app` (that is the Electron app, which stays; the gate refuses it).
- `minOS`: compared with `process.getSystemVersion()` (macOS `14.5.0`, Windows `10.0.22631`). Below it: not offered.
- `signature`: Ed25519 over the file's bytes, base64 (64 bytes). See 5.3.
- `args` (Windows): the installer's arguments; empty means `--migrated-from-electron <migrate folder>`.

**Only the release gate writes it** (CLAUDE.md, release channel):

```
python3 tools/release-gate/gate.py --native native-1.0.0.json --native-only --promote --push   # offer a native build; the program version stays
python3 tools/release-gate/gate.py --native native-1.0.0.json --promote --push                 # with a program promotion
python3 tools/release-gate/native_block.py remove desktop/app-version.json                     # (by hand, then commit) stop offering it
```

`--native` downloads every platform's file and checks size, sha256 and, with `AL_NATIVE_PUBKEY`, the signature (`tools/release-gate/native_block.py`). A normal promotion keeps the block that is already in the live manifest (`sync-app.js` with `AL_PROMOTE=1`). The dev manifest never has one.

## 3. The install (`desktop/native-migrate.js`)

**Mac**
1. Download to `<user data>/native-download/` with progress; the size must match; sha256 (and the signature) must match, or the file is deleted and nothing happens.
2. Unpack: zip with `ditto -x -k`; DMG mounted read-only and out of sight (`hdiutil attach -nobrowse -readonly -noautoopen -mountpoint …`), the `.app` copied out with `ditto`, unmounted.
3. Copy to `/Applications/<app>` when this user can write there (an admin user can, without a password); otherwise `~/Applications/<app>`. No password prompt, no privileged helper. An older native copy is replaced (moved aside, the new one put in, the old one removed; put back if that fails). The running Electron app is never the target.
4. `xattr -dr com.apple.quarantine` on the copy it wrote, and nothing else.
5. `open -n <app> --args --migrated-from-electron <migrate folder>`, then wait up to 10 s for its executable to run (`pgrep -f <app>/Contents/MacOS/`). Running: the Electron app quits 1.8 s later. Not running: the window shows the Open Anyway step (1.6).

**Windows**
1. The same download and checks.
2. The installer is started detached with `--migrated-from-electron <migrate folder>` (or the block's `args`), then the Electron app quits.
3. The file was written by the app itself, so it carries no Mark of the Web and SmartScreen normally does not ask. If it does: More info, then Run anyway (the window says so).

The Electron app, its program, its user-data folder and its browser storage are **never deleted**. The user can open the Electron app again at any time; the menu then says "Open the native AudioLab".

## 4. The migrate folder (for the native app's first start)

**Where**
- Mac: `~/Library/Application Support/AudioLab/migrate/`
- Windows: `%APPDATA%\AudioLab\migrate\`
- (Linux, tests only: `~/.config/AudioLab/migrate/`)

The native app also gets the path as `--migrated-from-electron <path>` when the shell starts it, but it must look in the folder on every start, because the user may start it by hand.

**How it is written**
- Into `migrate.incoming/` next to it; every file is read back and compared with its sha256; then an existing `migrate/` becomes `migrate.previous/` (the one before is removed), `migrate.incoming/` becomes `migrate/`, and `READY` is written last.
- No `READY`: an export was interrupted. Do not import.

**Layout (format `audiolab-migrate`, formatVersion 1)**

```
migrate/
  READY                          the time the export finished (written last)
  manifest.json                  see below
  projects/index.json            every project: file, origin (open | saved), order, name, flags
  projects/open-001-<name>.audiolab    the open tabs, in tab order (torn-off windows included, tornOff: true)
  projects/saved-001-<name>.audiolab   Saved projects (the in-app list), newest first
  settings/ui.json               the app's whole settings object (UI), as the Electron app stores it
  settings/local-storage.json    every key of the Electron app's storage as a string, exactly as stored
  settings/presets.json          the preset parts of UI (fxUser, scPre, …): a readable copy
  settings/controllers.json      the controller parts of UI (ctl*: surfaces, templates, Works as, Stop all) and MIDI learn: a readable copy
  settings/app-icon.json         { id, chosen }: the icon picked in the Electron app (ids of desktop/icon-assets/picker/icons.json)
  settings/window-state.json     the main window's size and place (when saved)
  recent.json                    current tab, open tabs and Saved projects in order
```

`manifest.json`:

```json
{ "format": "audiolab-migrate", "formatVersion": 1, "created": "2026-…Z",
  "from": { "app": "AudioLab Pro (Electron)", "shell": "0.262.0", "program": "0.262", "build": "27 November 2026",
            "platform": "darwin", "arch": "arm64", "os": "15.1.0", "userData": "…/AudioLab Studio" },
  "to": { "version": "1.0.0" },
  "counts": { "projects": 7, "open": 4, "saved": 3, "audioMissing": 0 },
  "files": [ { "path": "projects/open-001-Fractals_remake.audiolab", "size": 1234, "sha256": "…", "kind": "project" }, … ] }
```

`kind` is one of `project`, `index`, `storage`, `settings`, `presets`, `controllers`, `recent`, `icon`, `window`. `audioMissing` counts audio buffers a project refers to that were not in the Electron app's storage (normally 0).

`projects/index.json`: `{ "format": "audiolab-migrate-projects", "formatVersion": 1, "projects": [ { "file", "origin": "open"|"saved", "order", "name", "id", "current", "tornOff", "savedAs" (the .audiolab file name it was last saved as, or null), "savedAt", "unsaved", "sha256", "size" } ] }`.

**The `.audiolab` files** are exactly what the Electron app writes with Save (`packProject`), so the native app needs one reader for both:
- gzip around the whole file (check `1f 8b`; an uncompressed file is allowed);
- bytes 0–7 `AUDIOLAB`, 8–11 uint32 LE format (1), 12–15 uint32 LE length of the JSON;
- the JSON: `{ format: "audiolab", formatVersion: 1, app, saved, name, project, view, audio: [ { id, sr, ch, len, off } ] }`; `project` is the song (tracks, clips, devices, master, …) as the web app keeps it;
- then the audio: for each entry, `ch` channels of `len` float32 LE samples, one after the other, starting `off` bytes after the JSON.

**What the native app should do on its first start**
1. If `migrate/READY` exists and `manifest.json` has format `audiolab-migrate` and a formatVersion it knows: check every file's size and sha256. A mismatch: tell the user plainly and import nothing from that file.
2. Import: open the projects in `recent.json`'s order (the current one in front), put the saved ones into its project list, apply the settings, presets, controller mappings and the icon choice.
3. Write `migrate/imported.json` (`{ at, version, created: <manifest.created>, files }`). Import a given export once (compare `created`); a newer export (the user went back to the Electron app and installed again) is imported again, as new projects, never over the user's newer work.
4. Never delete the folder or anything of the Electron app.

**Not exported** (stays in the Electron app, which stays installed): Time Machine history (`audiolab-tm` in its browser storage), the analysis cache of the frequency map (`audiolab-ni`, rebuilt by itself), downloaded AI voice models.

## 5. Safety

### 5.1 Mac without an Apple account
The native app is ad hoc signed and not notarised (`docs/native-mac-picks.md`). Files a program downloads itself are not quarantined unless it asks for that (`docs/research-native-qa-legal.md`, section 4), and the shell also removes the mark from its copy, so Gatekeeper does not check it and there is no App Translocation. If a future macOS still stops it, the window shows the Open Anyway steps (System Settings › Privacy & Security), and the test checks that the installed copy carries no quarantine mark.

### 5.2 Windows SmartScreen
An unsigned installer shows "Windows protected your PC" when it carries the Mark of the Web; the shell's own download does not, so normally nothing is shown. The window explains More info, Run anyway in any case.

### 5.3 Signature (task QL4)
`NATIVE_PUBKEY` in `desktop/native-migrate.js` (raw 32-byte Ed25519 public key, base64) is empty today: the sha256 from the manifest is the check. Once QL4 sets it, every native build must carry a valid `signature` in the block, or the shell refuses it. The gate checks the same with `AL_NATIVE_PUBKEY`. The private key belongs in a protected CI environment, never in the repository.

### 5.4 Never lose work (`docs/research-native-lessons.md`)
- The export is complete and checked before anything is installed.
- Torn-off project windows are brought home first; the open projects and settings are stored before the export.
- Nothing is deleted on either side.

## 6. Tests

- `tools/ui-tests/taskMG1_electron.js` (39 checks), in the real desktop app against a stand-in native build (`tools/migrate-tests/fake_native.js`: an ad hoc signed `.app` with a quarantine mark as zip or DMG on the Mac, a small installer `.exe` on Windows, a zip on Linux with `AL_NATIVE_TEST=1`) served by a local update server (`AL_UPDATE_BASE`), each launch in its own application-data folder (`AL_TEST_APPDATA`).
- `tools/migrate-tests/unit_native_migrate.js`: what each computer is offered, http refused, file names kept inside the folder.
- `.github/workflows/native-migrate.yml`: both on `macos-latest` (zip into the real `/Applications`, then a DMG) and `windows-latest`.

## 7. For N7 (packaging the native app)

1. Name the bundle `AudioLab.app` (or set `app` in the block); per-user NSIS installer on Windows that accepts `--migrated-from-electron <path>`.
2. Implement section 4's import on first start.
3. Publish the files, write the block, run `gate.py --native block.json --native-only --promote --push`.
4. Raise nothing else: Electron shells from MG1 on offer it by themselves; older shells keep updating their program as before (and will get MG1's shell with their next desktop build).
