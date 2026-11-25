# Work in progress: backlog task 11 (updates, Audio devices window, "Interface and DAC")

Started 25 November 2026 by a scheduled run that the user stopped early ("started too early"). Nothing was released and `index.html` is untouched.
This branch (`wip/backlog-11`) holds the finished desktop-side part and these notes, so the next run does not start from zero.

## A1. Why "Check for updates" stopped working (found and reproduced)
Tested the real desktop app under xvfb with a local update server (`tools/engine-tests/updater/rig_check.js`, modes `same`, `new`, `hang`, `down`).
- With a server that answers, the old button works (it shows the system dialogs).
- **Cause:** `updFetch` in `desktop/main.js` had no time limit. One request that never answers (laptop woke from sleep, a network that drops packets; the app checks every hour) leaves `updBusy = true` for good, and `checkUpdates` then returns at once without saying anything. From then on the button does nothing until the app is restarted. Reproduced with `MODE=hang`: first click no dialog, every later click nothing.
- Second, smaller cause: a click while the automatic check or download is running was also dropped silently.
- The repo is public and both GitHub addresses answer 200, so it is not an access problem.

## What is done on this branch (tested under xvfb, not released)
`desktop/main.js`
- `updFetch(file, ms)`: every request has a time limit (15 s manifest, 120 s program) and is aborted.
- `updDo(download)` / `updCheck(download)`: one check that always answers with a plain result and never shows a dialog: `{status, installed, app, latest, notes, size, at, reason, error}`. `status`: `current`, `available` (only when download is false), `ready`, `needs-app`, `reverted`, `publishing`, `error` (`reason`: `offline`, `timeout`, `http`, `bad`, `unreachable`, `disk`). Checks queue up (`updChain`) instead of being dropped. `updLast` keeps the last result.
- `checkUpdates(manual)` (menu, hourly timer, old program versions): if the page has `audiolabHost.updOpen` it calls that and the page shows its own window; otherwise the old dialogs, now with a reason (offline, no answer in time, GitHub not reachable).
- New IPC: `al:update-check` ({download}), `al:update-status`, `al:update-app` (Windows: start the app updater, Mac: open the download page), `al:dac-info`, `al:dac-rate`. `applyContent` returns true or false.
- `manualCheck` and `updBusy` are gone.
`desktop/preload.js`: `updateCheck(o)`, `updateStatus()`, `updateApp()`, `dac.info()`, `dac.rate(uid, hz)`.
`desktop/native/alvol.swift`: `alvol info` (every device, inputs too: `transport` builtin/usb/bluetooth/hdmi/displayport/thunderbolt/virtual/aggregate, `out` and `in` channel counts, `rate`, `rates` on offer, `bits`, `hog` pid or -1, `defaultOut`, `defaultIn`, volume) and `alvol rate <uid> <hz>` (sets the device's own sample rate, waits up to 2 s for it). **Not compiled here (no Swift in the container): check the Mac job of the desktop workflow after the first push to main.**
All of this only reaches users who install a new app build. The page must feature-detect (`D.updateCheck`, `D.dac.info`, `D.dac.rate`).

Rig results with the new main.js: `hang` gives "Could not check for updates. GitHub did not answer in time." after 15 s on every click; `new` shows the card at start and the dialog on a click; `same` and `down` as before.

## Plan for the page (not written yet)
Updates
- `updOpen()`: own popup in the app's style. New app build: `D.updateCheck({download:false})`, then "Update now" = `updateCheck({download:true})` then `applyUpdate()`. Old app build (what the user has until a new build is installed): the page fetches `https://raw.githubusercontent.com/Audio-lab-DAW/Audio-Lab-Beta/main/desktop/app-version.json` itself (with a time limit) to show installed, newest, size; "Update now" calls the old `checkForUpdates()` and says honestly: if nothing appears within a few seconds the updater of this app build is stuck, quit and reopen AudioLab and it updates at start. Browser: "the web version is always current", Reload if the manifest is newer.
- Notes: `desktop/update-notes.txt` is read by `sync-app.js` into the manifest but does not exist, so notes were always empty. Write it at each release, and/or read commit messages (`api.github.com/repos/Audio-lab-DAW/Audio-Lab-Beta/commits?path=index.html`, messages start with `v0.xxx:`).
- `genUpd` (Settings, General) and `#abUpd` (About) both call `updOpen`; show both in the browser too. `audiolabHost.updOpen` for the menu.
- "Install updates automatically" (`UI.updAuto`, off): wrap `audiolabHost.updateReady`; when on, wait for a safe moment (`!play.on && !REC.on`, export not running: `#exGo` not disabled and `BUSYN===0`, `#cdlg` hidden, no input for about 20 s) then `applyUpdate()` (main runs `beforeReload`). Remember `{from,to}` in localStorage and show "Updated to version X" after the reload. Works with old app builds too.
Audio devices window (`audDevOpen`, `audDevRender`, `audDevClick`, CSS `.adw .adc .adi .adt .adb`)
- Headings with icons, a kind icon per device, rate and channels (from `dac.info` in a new Mac app build; else `ctx.sampleRate`, `ctx.destination.maxChannelCount`, `InputDeviceInfo.getCapabilities()`), Test as a small round ghost button with a play icon, Use as the solid main button, the active device shows an "In use" badge instead. Inputs get Use (new `UI.inDev`) and a short level test.
Interface and DAC (settings page `data-page="dac"`, nav text, menu entry at about line 6519, hint at line 2112)
- Keep the existing inputs (`bpChk`, `lockSr`, `ceilSel`, `balR`, `monoChk`, `swapChk`, `dcChk`, `dacSel`, `hqChk`) and move them into the new layout so their handlers stay.
- `UI.ifMode` auto / dac / int; profiles table with model sub-matches; old `DACS` (gryphon, ams24) folds into it.
- DAC mode: volume link (the `DAC` object, `dacPick`, `dacSend`), bit-perfect with a live checklist (mode on, master at 0 dB, device rate equals engine rate when `dac.info` is there, device volume 100% or fixed, note that other apps and system sounds cannot be shut out), rate switching with `dac.rate` (`UI.rateFollow`), exclusive use stated as not possible.
- Interface mode: mirrors of `#bufSel`, `#srSel`, `#recOff`; input device and channel (replace the two `getUserMedia({audio:{echoCancellation:false,noiseSuppression:false,autoGainControl:false}})` calls, lines about 4527 and 7240, by one helper); input monitoring (armed track's stream to `prevIn`); output pair when `ctx.destination.maxChannelCount > 2` (splitter and merger after `MON.out` and `clickOut`, only when a pair other than 1+2 is chosen); round trip measured with a small worklet that plays a click and listens.
- Facts found: audio takes are recorded with `MediaRecorder` on the raw stream (`recStart`), `UI.recOff` is only applied to recorded notes, not to audio takes; there is no input monitoring and no input choice today.

## Research (sources at the end; "unconfirmed" = not found on a page that was read)
DACs, all 2 channels out
- iFi xDSD Gryphon: 44.1 to 768 kHz, 32 bit, DSD512. Filters Bit-Perfect, Standard, GTO. USB name unconfirmed (probably "iFi (by AMR) HD USB Audio").
- Chord Mojo 2, Hugo 2, Qutest: up to 768 kHz, 32 bit. Hugo 2 driverless on Mac (stated). Qutest has no volume (fixed 1, 2 or 3 V). Mojo (first): 768 kHz unconfirmed.
- Topping: D10s up to 384 kHz, E30 II and D90 up to 768 kHz; DX3 Pro+ and E50 unconfirmed.
- FiiO: K5 Pro ESS up to 768 kHz, K9 Pro ESS up to 384 kHz; K7, KA3, BTR5 unconfirmed.
- RME ADI-2 DAC FS and ADI-2 Pro FS R: up to 768 kHz, class compliant, 2 in 2 out in stereo mode.
Interfaces, 24 bit unless noted
- Focusrite Scarlett 3rd and 4th gen: 44.1 to 192 kHz; channels follow the name (2i2 = 2 in 2 out, 18i20 and so on); 3rd gen plug and play on Mac.
- M-Audio M-Track Solo and Duo: 44.1 and 48 kHz only, 16 bit, 2x2. AIR 192|4: up to 192 kHz, 2x2.
- Zoom AMS-22 / 24 / 44: 44.1 to 96 kHz, 2x2 / 2x4 / 4x4. Use Music mode for DAW work (Streaming mode sums to stereo). Direct monitor and loopback are switches on the unit.
- Universal Audio Volt: 44.1 to 192 kHz, class compliant; 276 is 2x2 (others unconfirmed).
- MOTU M2 / M4 / M6: 44.1 to 192 kHz, 2x2 / 4x4 / 6x4, plug and play on Mac; loopback needs MOTU's driver.
- Audient iD4 MkII, iD14 MkII, EVO 4, EVO 8: up to 96 kHz; 2x2, 10x6, 2x2, 4x4.
- RME Babyface Pro FS (12x12) and Fireface UCX II: 44.1 to 192 kHz.
- PreSonus Studio 24c: up to 192 kHz, 2x2. AudioBox USB 96: 96 kHz unconfirmed.
- Behringer UMC202HD / 204HD / 404HD: up to 192 kHz (204HD confirmed, 2x4), no driver on Mac. UMC22 unconfirmed.
Platform facts
- macOS: any app may set a device's sample rate (Apple QA1196). Exclusive "hog" mode belongs to one process; a Chromium or Electron app cannot get it or WASAPI exclusive mode through Web Audio.
- Bit-perfect in audiophile players means: exclusive access, device rate switched to the material's rate, device bit depth at least the material's, no software volume or processing, nothing else mixed in.
- Buffer: as small as the computer manages without clicks for recording, larger for mixing (Sound On Sound, Focusrite); the usual 64 to 256 and 512 to 2048 samples are common practice, not from a page that was read.
Sources: ifi-audio.com/collections/all/products/xdsd-gryphon · richersounds.com/content/product_files/Qutest_User_manual_2_1.pdf · audioadvisor.com (Chord Hugo 2, Mojo 2) · techpowerup.com/review/topping-e30-ii-dac-l30-ii-amplifier-desktop-stack/4.html · apos.audio/blogs/news/topping-l30-vs-d30-pro-vs-d90-comparison-chart · fiio.com/k5proess_parameters · fiio.com/k9proess_parameters · rme-audio.de/downloads/adi2dacr_e.pdf · rme-audio.de/adi-2-pro-fs.html · rme-audio.de/babyface-pro-fs.html · rme-audio.de/fireface-ucx-ii.html · us.focusrite.com/scarlett-in-depth · userguides.focusrite.com (Scarlett 8i6 3rd Gen) · soundonsound.com/reviews/m-audio-m-track-solo-duo · m-audio.com/audio-midi-interfaces/air-192-4.html · zoomcorp.com (AMS series) · soundonsound.com/reviews/zoom-ams-22-24-44 · uaudio.com/products/volt-276 · motu.com/de/news/introducing-the-m2-and-m4 · soundonsound.com/reviews/audient-id4-id14-mkii · soundonsound.com/reviews/audient-evo-4-evo-8 · fender.com/studio-24c/2777700403.html · behringer.com/en/products/0805-aas · developer.apple.com/library/content/qa/qa1196/_index.html · audirvana.com/exclusive-playback-technology · learn.microsoft.com/en-us/windows/win32/CoreAudio/exclusive-mode-streams · soundonsound.com/sound-advice/q-what-buffer-size-should-use
