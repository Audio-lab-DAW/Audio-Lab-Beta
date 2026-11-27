# The release gate

Since 27 November 2026 (task HF1) installed apps only get a build that passed the release gate. v0.250 reached the user's Mac broken: on start the app clicked around by itself (tracks selected, play and stop several times a second, the instrument browser opening, EQ points moving, a track duplicated, quitting froze). The cause was a MIDI loop: the user's Mac has the IAC Driver online with a port called "Ableton Push to Cubase"; from v0.242 AudioLab took any port named "Ableton Push…" as a Push 1, lit its buttons, and IAC sent those light messages straight back, where they read as button presses. No test started the real app with the MIDI ports a real Mac has. The gate does that now, every time.

## How releases reach installed apps

- Installed apps read `desktop/app-version.json` on main (the "live" manifest).
- An ordinary release (`node desktop/scripts/sync-app.js`) writes only `desktop/app-version-dev.json`. Releasing never changes what installed apps get.
- Only the gate promotes: when every check passes it runs `AL_PROMOTE=1 node desktop/scripts/sync-app.js` in its own checkout of main. That writes `desktop/app-version.json` with the build's fingerprint and the update notes (trimmed to the ten newest lines; the newest line is on top). Then it commits and, with `--push`, pushes to main.
- Anything fails: nothing is promoted. The result says what failed.

## Running it

```
python3 tools/release-gate/gate.py --promote --push      # the real run: decides and promotes
python3 tools/release-gate/gate.py                       # every check, no promotion
python3 tools/release-gate/gate.py --quick               # smoke scenarios at 20 s, no UI tests, never promotes
python3 tools/release-gate/gate.py --here --skip-ui      # the working copy as it is, never promotes
```

The gate fetches main and tests a fresh worktree of `origin/main` (`tools/release-gate/out/new`). It never tests your working copy, unless you pass `--here`. The reference is the build installed apps have now: the version in `desktop/app-version.json`, checked out from its release commit into `out/ref`. `--ref 0.257` picks another one.

It needs Node 22, Python 3 with Playwright, `xvfb-run`, and Electron (`desktop/node_modules/electron`; the gate installs it when it is missing). The lint needs acorn: `npm install --prefix tools/release-gate/.deps acorn@8.14.0 acorn-walk@8.3.4`. The result is in `tools/release-gate/out/result.json` and `out/gate.log`. A full run takes about an hour on a 2-core machine, most of it the UI tests.

## What it checks

**a) Lint** (`lint.js`)
- A top-level function name declared twice fails. The app's scripts share one scope, so the later declaration silently replaces the first. v0.255 had two `lkSel` functions; every selection outline got an array instead of a colour.
- A function with the same name as a top-level `const`/`let`/`class` fails.
- An element id written twice in the static HTML, or twice in one piece of markup, fails.
- Ids that code creates at run time are checked in the running app (step c).
- A known, harmless duplicate can be listed in `lint-allow.json` with its reason.

**b) Every UI test** in `tools/ui-tests` (`*.py` and `*_electron.js`, without the helpers)
- Each test is run with the new build.
- A failing test is run again on the reference build with the reference's own copy of the test. When it fails there too, it is reported as old, not as a regression.
- A new test must pass.
- `ui-skip.json` lists the few that are not pass/fail tests or need files that are not in the repository, each with its reason.

**c) The start-up smoke test in the real desktop app** (`smoke_electron.js`)
- Electron with `desktop/main.js`, at the user's size (2194 × 1139 at 1.75×), with the Fractals song open.
- 60 s idle, then the mouse moves over the whole window without clicking.
- Web MIDI is replaced by fakes, one scenario each:

  | Scenario | Ports |
  |---|---|
  | `real` | none faked |
  | `none` | no ports |
  | `keyboard` | a plain keyboard |
  | `push1` | a Push 1 on both ports |
  | `push1-loop` | the same Push 1, echoing back what it gets |
  | `push1-loop-on` | the echoing Push 1, turned on as a surface |
  | `loopback` | an IAC loop-back |
  | `iac-push`, `iac-push-short` | the user's IAC ports, "Ableton Push to Cubase" and "nanoKey2 to Cubase", as they looped |
  | `macnames` | the virtual ports a Mac shows |
  | `mackie-loop`, `mackie-loop-on` | a Mackie surface that echoes |
  | `loopback-maps` | IAC with mappings left by an old MIDI learn |
  | `noise` | a port sending random messages |

- A scenario fails on:
  - any change of a track's solo, mute, arm or record state, the selected track, clip or master, the playhead running, or the master level
  - any synthetic (untrusted) click, key or pointer event
  - any command run or `changed()` call nobody asked for
  - any console error
  - any duplicate element id in the page
  - a MIDI loop that keeps going without the device being stopped
- Frame times of the idle app (p50 and p95, twice each) are compared with the reference build. It fails above 1.25 × p50 + 2 ms or 1.5 × p95 + 10 ms.

**d) Windows**
- Settings, Mixer, Devices, Keyboard shortcuts, Controllers, both browsers, Time Machine, the frequency map, the kick and bass lab, the clip explainer, Export and About are each opened and closed. No errors are allowed.
- The update window is opened with 40 long lines of notes at 2194 × 1139, 1280 × 720 and 900 × 560. At each size:
  - Update and Later must be in view and clickable.
  - The notes must be newest first, at most 8 shown.
  - Later must close the window.

**e) Sound**
- `tools/engine-tests/export_same.py` runs on both builds.
- The Fractals Kick and Bass must be −19.05560 dB (fb577dd5202b) and −35.48685 dB (392ec52590c7) with the master at −10 dB.
- Each build renders twice. A line that differs between two renders of the same build is not repeatable, so it is listed and not compared. On 27 Nov 2026 that was Plant, Sampler, Sampler grains and Drum kit, which move by up to 1 dB from run to run on one build because their randomness runs free. The Fractals lines must always be repeatable.
- Every repeatable export line must be bit-identical to the reference build. A release that changes a sound on purpose names that line in `audio-changes.json` with its version and reason.

## What the HF1 fix changed in the app

- A control-surface profile (Push 1, Mackie Control, HUI, Launchpad, APC) takes a port only after the user ticks **Control surface** for it on the Controllers page, or picks it under Works as. Until then the port is a plain device: its notes play, mappings work, and nothing is sent to it. AudioLab says once when a port looks like a surface.
- Mapping feedback goes only to devices turned on as surfaces.
- Every message AudioLab sends is remembered for 50 ms, and the same message coming back within that time is ignored. Two kinds are never dropped:
  - note-offs (dropping one would leave a stuck note)
  - Mackie and HUI motor faders
- A device that keeps returning what it was sent (at least 24 a second, at least 60 % of its messages) is stopped for the session with a notice: "a MIDI loop". So is one that sends over 1500 messages a second. Ticking **Use this device** again retries it.
- **Stop all controllers**, on the Controllers page and in the command list, ignores all MIDI controllers and sends them nothing. It stays that way after a restart (`UI.ctlStop`), until the user starts them again.
