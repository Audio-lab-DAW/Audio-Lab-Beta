# Settings audit (task SR4)

Audited version: **AudioLab Pro v0.221** (build 27 November 2026, commit `6765edd`). Read only: nothing in `index.html` or `desktop/` was changed. Other tasks are editing the app in parallel, so later versions may differ from this list. One difference is already known: **v0.222** (on main when this was written) makes "Flat bars" (design 7) the standard fader design again, so where this document says the default is "22 Flat bars 2", read "7 Flat bars" from v0.222 on.

How it was checked: the code in `index.html` and `desktop/`, plus a headless run of the app (Chromium, 1600x1000, the Fractals song open). Every Settings tab, the Control Panel, the mixer popover and each right-click menu was opened, its controls were read from the page and a screenshot was taken to compare with the list. Sync between two places was tested by changing one and reading the other. Anything that was not opened on screen is marked "code only". Two things could not be shown in the headless browser: the app icon picker (its pictures did not load there) and the desktop-only controls (automatic updates, the DAC volume link).

Related research from the same round: `docs/settings-research-general.md` (SR1), `docs/settings-research-daw.md` (SR2), `docs/settings-research-audiophile.md` (SR3). This document is the inventory of what AudioLab has today; it was written without reading those three, so its proposals in sections 5 to 7 should be weighed against them.

Words used in the tables:

- **`UI.x`**: one object saved in the browser's localStorage under `audiolab-ui`. Per computer, the same for all projects ("global").
- **`S.x`, `t.x`, `V.x`**: inside the project (song, track, the project's view). Travels with the `.audiolab` file ("project").
- **session**: not stored; back to the default after a restart.
- **Live**: the change is applied at once, without a restart. "restarts audio" means the audio engine restarts by itself.
- **Tip**: hovering shows an explanation (a `title` or an entry in the app's tips table).

## 1. Summary

| What | Count |
|---|---|
| Tabs in Settings | 11 (General, Audio system, Interface and DAC, Interface, Performance, Glass & light, Colours & clips, Zoom and playhead, Keyboard shortcuts, Project file, Export audio) |
| Different settings inside Settings | about 124 (General 5, Audio system 9, Interface and DAC 14, Interface 45, Performance 14, Glass & light 3, Colours & clips 8, Zoom and playhead 6, Keyboard shortcuts 2 plus 57 shortcut rows, Project file 3, Export audio 15) |
| Extra copies of a setting inside Settings itself | 10 (sample rate 3 times, buffer, recording offset, keep awake and output device twice each, the four level-meter settings twice on one page) plus doubled buttons (Save, Save as, Open; Audio devices; Performance link) |
| Setting-like options that exist only outside Settings | about 75 (mixer 12, devices panel 6, piano roll 14, transport and metronome 25, arrangement 9, visualizer 2, hidden flags without any control 7) |
| Options settable both in Settings and in place | 30 (mixer 23, follow 2, map and visualizer 3, track controls 1, light mode 1) |
| Of those, not fully in sync | 5 (Mono, L and R swap, Follow modes, the Follow command, the visualizer's own buttons) |
| Options reachable only by a right-click | 14 (Play flash source, 5 capture options, 3 Follow extras, per-channel picture, picture colours, stereo field behind pan, hide all automation, remove loop) |
| Options that are stored nowhere | 22 (12 export options, 8 piano roll options, mixer Dim, test tone); the first 20 are ones users expect to stay |
| Dead or obsolete | 3 hidden controls in Settings, 7 flags without a control, 7 one-time flags, the old glass keys |

The five most important findings:

1. **The mixer is the main source of doubles.** 23 mixer options are in the gear popover and in Settings › Interface, several also on a header button or in a right-click menu (pan style is in four places). The level-meter settings are shown twice on the same Settings page. Everything stays in sync except Mono and the L and R swap.
2. **Audio is split over three surfaces that repeat each other**: the Audio system tab, its Control Panel pop-up, and the Interface and DAC tab. Sample rate can be set in three places, buffer, recording offset, keep awake and output device in two.
3. **Glass is split over two tabs with the same words for different things** (Blur and Edge light are a switch on Performance and a slider on Glass & light), and its four levels are due to become three under the glass engine plan.
4. **A group of options has no home at all**: the metronome, capture, the piano roll, snap, the loudness target and the clock are not in Settings and Settings search cannot find them; some are only in a right-click menu.
5. **Export options are forgotten at every restart**, and the piano roll forgets its snap, scale and ghost choice.

## 2. Inventory: the Settings window

The window: a search field ("Search settings"), 11 tabs in two groups (Settings: 9, Output: 2), a footer with **Reset all settings…** (asks first; resets every `UI` key except the shortcuts, reloads), the note "Changes apply right away" and **Done**. The window can be resized; its size is kept in `UI.setSize`. Opened by a click on the logo, ⌘, , the logo menu, and links from menus.

All settings in this window are **global** (`UI.*`) unless the Scope column says otherwise.

### 2.1 General

| Control (as shown) | What it does | Type | Default | Stored in | Live | Tip |
|---|---|---|---|---|---|---|
| Performance: "Light mode, effects and frame rate: Performance" | Jumps to the Performance tab | link button | – | – | – | no |
| Show tooltips with short explanations when hovering | Tooltips on or off, everywhere | checkbox | on | `UI.tips` | yes | no |
| Show the AudioLab splash screen at start | Splash at start | checkbox | on | `UI.splash` | next start | no |
| Show now | Shows the splash once | button | – | – | – | no |
| Show the guided tour button (?) in the top bar | Shows or hides the ? button | checkbox | on | `UI.tutBtn` | yes | no |
| Start the guided tour (F1) | Starts the tour | button | – | – | – | no |
| Keyboard shortcuts (⌘/) | Jumps to the Keyboard shortcuts tab | button | – | – | – | no |
| Ask before closing a project with unsaved changes | Question before a tab closes | checkbox | on | `UI.askClose` | yes | no |
| Install updates automatically (desktop app only, added by code; not seen in the browser) | Installs an update when nothing plays, records or exports | checkbox | off | `UI.updAuto` | yes | yes |
| Check for updates | Opens the Updates window | button | – | – | – | yes |
| What's inside AudioLab | Opens the About window | button | – | – | – | yes |

### 2.2 Audio system

| Control (as shown) | What it does | Type | Default | Stored in | Live | Tip |
|---|---|---|---|---|---|---|
| Output device | Which device AudioLab plays through | select | System default | `UI.sink` | yes | no |
| Control Panel | Opens a pop-up with the next six rows | button | – | – | – | no |
| ↳ Buffer size | Auto, Browser default, 64 to 2048 samples | select | Auto | `UI.buf` | restarts audio | yes |
| ↳ Render blocks | Auto (half the buffer), Whole buffer, 128 samples | select | Auto | `UI.rq` | restarts audio | yes |
| ↳ Sample rate | Automatic (device), 44.1 to 384 kHz | select | Automatic | `UI.sr` | restarts audio | yes |
| ↳ Advanced: Internal headroom | 0, −3, −6, −12 dB | select | −6 dB | `UI.headroom` | yes | no |
| ↳ Advanced: Recording latency offset | −200 to 200 ms | number | 0 | `UI.recOff` | yes | no |
| ↳ Advanced: Keep the audio engine awake when idle | No wake-up click | checkbox | off | `UI.keepAwake` | yes | no |
| Audio devices | Opens the Audio devices window (every input and output, pick, test) | button | – | – | – | yes |
| Pick up notes that are already sounding | Notes that began before the playhead are heard at once | checkbox | on | `UI.chase` | yes | yes |
| Safety limiter on the master | Catches loud peaks before the output | checkbox | on | `UI.limiter` | yes | yes |
| Test tone: On / Off, kind (Sine, Sweep, Pink noise, White noise, L ⇄ R), Frequency (slider, number, 4 quick buttons), Volume | A test signal; stops when Settings closes | button, 5 buttons, slider, number, slider | off, sine, 440 Hz, −24 dB | session | yes | only the On button |

The pop-up also shows read-outs (Running at, Output latency, Clock) and a line that points to Interface and DAC.

### 2.3 Interface and DAC

The page changes with the mode. In DAC mode the "Speed and delay", "Inputs" and "Outputs" blocks are hidden; in Interface mode they appear (checked on screen).

| Control (as shown) | What it does | Type | Default | Stored in | Live | Tip |
|---|---|---|---|---|---|---|
| Audio devices | Opens the Audio devices window (second button for it) | button | – | – | – | yes |
| Automatic / DAC mode / Interface mode | Listening and mixing, or recording and playing live | 3 buttons | Automatic | `UI.ifMode` | yes | yes |
| Apply the recommended settings | Sets the buffer and sample rate that fit the mode | button | – | changes `UI.hq`, `UI.sr` | yes | yes |
| Device profile | Automatic or one of 14 DACs and interfaces | select | Automatic | `UI.dac` | yes | no |
| Volume on the DAC (desktop app on a Mac only) | Links a volume slider to the DAC's own volume | slider | – | the device, not AudioLab | yes | – (not seen) |
| Bit-perfect mode | Straight path: no trim, no limiter, no monitor processing | switch | off | `UI.bitPerfect` | yes | yes |
| Engine sample rate ("Lock to DAC rate") | **Copy of Sample rate** in the Control Panel | select | Follow the device | `UI.sr` | restarts audio | no |
| Switch the DAC to the engine's sample rate automatically (desktop only) | Sets the DAC to the engine's rate | checkbox | off | `UI.rateFollow` | yes | yes |
| DC blocker | Removes inaudible offset | checkbox | off | `UI.dcBlock` | yes | yes |
| Headphone safety ceiling | −1, −3, −6, −10 dBFS | select | −1 dBFS | `UI.ceil` | yes | yes |
| Keep the audio engine awake when nothing plays | **Copy of Keep awake** in the Control Panel | checkbox | off | `UI.keepAwake` | yes | yes ("the same setting as in the Control Panel") |
| Steadier playback: bigger buffer for heavy mixing | Larger playback buffer | checkbox | on | `UI.hq` | restarts audio | yes |
| Balance | Left / right balance of the monitor path | slider | centre | `UI.bal` | yes | no |
| Mono check | Sums left and right. **Also on the master strip** | checkbox | off | `UI.monoChk` | yes | yes |
| Swap left and right channels | **Also on the master strip (L↔R)** | checkbox | off | `UI.swapChk` | yes | no |
| Interface mode: Buffer size | **Copy of Buffer size** | select | Auto | `UI.buf` | restarts audio | yes |
| Interface mode: Sample rate | **Third copy of Sample rate** | select | Follow the device | `UI.sr` | restarts audio | yes |
| Interface mode: Measured round trip: Measure, Use as offset | Measures the delay and can copy it to the offset | 2 buttons | – | – | – | yes |
| Interface mode: Recording latency offset | **Copy of the offset** in the Control Panel | number | 0 | `UI.recOff` | yes | yes |
| Interface mode: Record from | Input device | select | System default | `UI.inDev` | yes | yes |
| Interface mode: Input channels | Stereo 1 and 2, input 1 only, input 2 only | select | Stereo | `UI.inCh` | yes | yes |
| Interface mode: Input monitoring | Hear armed audio tracks through AudioLab | checkbox | off | `UI.inMon` | yes | yes |
| Interface mode: Play through | **Copy of Output device** | select | System default | `UI.sink` | yes | yes |
| Interface mode: Output channels (only with more than two outputs) | Which output pair | select | first pair | `UI.outPair` | yes | yes |
| Profile (None, iFi xDSD Gryphon, Zoom AMS-24) | Old profile select; **always hidden**, replaced by Device profile | select | None | `UI.dac` | – | no |

Read-outs on this page: Current output, a "Not bit-perfect right now" check list, Lossless listening (engine, rate, resampling), and two explanation blocks (Sample rate, Exclusive use of the DAC).

### 2.4 Interface

One long page (about 2800 px, four screens) with these blocks.

| Control (as shown) | What it does | Type | Default | Stored in | Live | Tip |
|---|---|---|---|---|---|---|
| Interface size ("Aa", 75% to 200%) | Scales the whole interface | slider | 100% | `UI.scale` | when you let go | no |
| **Zoom and scroll**: AudioLab default / Ableton style / Logic style / FL Studio style | Fills the four keys below in one click | 4 buttons | AudioLab default | `UI.zs` | yes | yes |
| Zoom, Track height, Clip width, Sideways | Which key (Ctrl, Alt, Shift, Ctrl + Shift, Alt + Shift, None) does what while scrolling | 4 selects | Ctrl, Alt, Shift, Ctrl + Shift | `UI.zs.zoom, th, cw, side` | yes | yes |
| Zoom speed | 25% to 300% | slider | 100% | `UI.zs.speed` | yes | yes |
| Zoom around: Mouse pointer / Playhead | The fixed point while zooming | 2 buttons | Mouse pointer | `UI.zs.anchor` | yes | yes |
| Invert direction | Reverses the scroll direction of zoom | checkbox | off | `UI.zs.inv` | yes | yes |
| Trackpad pinch zooms | Pinch zooms | checkbox | on | `UI.zs.pinch` | yes | yes |
| Reset (Zoom and scroll) | Back to the defaults | button | – | – | – | yes |
| **Layout**: the picture (Tracks, Arrangement, Devices, Transport, Map) | Drag the blocks to order the window; header strip left or right; dashed panels float | drag picture | Classic | `UI.order` and related | yes | partly |
| Presets… (Classic, Map on top, Ableton-style, Cubase-style, Focus, Headers right) | Ready-made layouts | button + 6 buttons | Classic | sets the same keys | yes | no |
| Edit (on the Transport block of the picture) | Starts the transport bar's edit mode | button | – | – | – | yes |
| Panels: Map | Shows the map | checkbox | on | `UI.mapOff` | yes | yes |
| Panels: Visualizer | Shows the visualizer | checkbox | off | `UI.viz` | yes | yes |
| Panels: visualizer place | Docked top, bottom, left, right or floating | select | bottom | `UI.vizDock` | yes | yes |
| Transport bar: Edit… / Reset | Edit mode for the transport modules; back to the standard bar | 2 buttons | 12 modules | `UI.trOrder, trCompact, trHide, trX` | yes | yes |
| Transport bar: Shrink on small screens | Modules get compact when space is short | checkbox | on | `UI.trAuto` | yes | yes |
| Track controls: preview, Customise…, Reset | Which buttons and sliders every track header shows | preview + 2 buttons | standard set | `UI.hcz` | yes | buttons yes, preview no |
| **Themes: the look of another DAW** (AudioLab, Live, FL, Cubase, Logic, Bitwig, Pro Tools, Reaper style) | Sets colours, clip look, fader and meter design and meter colours in one click | 8 picture buttons | AudioLab | `UI.dawLook` (and it overwrites `UI.mxs.fd`, `UI.mtr.col`, colours) | yes | yes |
| Also recolour the tracks in this project | The theme also changes track colours | checkbox | off | `UI.dawRecol`; the colours go into the project | yes | no |
| **Mixer** › Channels: Compact channels | Thin strips | checkbox | off | `UI.mxCompact` | yes | yes |
| Channel number | Number before each name | checkbox | on | `UI.mxs.num` | yes | yes |
| Strip width | 64 to 170 px | slider | 96 px | `UI.mxs.w` | yes | yes |
| Master strip width | 110 to 240 px | slider | 136 px | `UI.mxs.mw` | yes | yes |
| Fader height | 76 to 320 px, far left = Auto | slider | Auto | `UI.mxs.fh` | yes | yes |
| Pan control | Automatic, Slider, Half dial, Full dial | select | Automatic | `UI.mxs.panst` | yes | yes |
| Keep the master in view | Master stays at the right edge | checkbox | on | `UI.mxs.pin` | yes | yes |
| Each channel shows: Effect slots, Sends, Picture, Pan, Mute solo record, dB scale, Volume number | Show or hide each part | 7 checkboxes | on | `UI.mxs.fx, snd, view, pan, btn, sc, val` | yes | yes |
| Each channel shows: Highest peak, Group colour band | Two more parts | 2 checkboxes | off | `UI.mxs.pkr, gband` | yes | yes |
| Routing: Cables | Shows the cables under the channels | checkbox | on | `UI.mxs.cab` | yes | yes |
| Master shows: Loudness and peak, True peak, Loudness target, Stereo correlation | Show or hide the read-outs on the master | 4 checkboxes | on | `UI.mxs.mLu, mTp, mTgt, mCorr` | yes | yes |
| Level meters (inside the Mixer block): Speed, Reading, Peak hold, Colours | For every meter in the app | 4 selects | Instant, Peak, 1 second, Classic | `UI.mtr.spd, alg, hold, col` | yes | yes |
| Fader and meter design | One of 22 designs | picture list | 22 Flat bars 2 | `UI.mxs.fd` | yes | yes |
| **Level meters** (own block, directly below): big test meter, peak Reset | Shows the choice live | meter + button | – | – | yes | yes |
| Speed (Instant, Fast, Normal, Smooth), Reading (Peak, RMS, VU, Loudness), Colours (7), Peak hold (Off, 1 s, 3 s, Until reset) | **The same four settings again**, as picture cards | 19 cards | as above | `UI.mtr.*` | yes | no |

The Mixer block ends with the sentence "These are the same settings as the settings button at the top right of the mixer. Change them in either place."

### 2.5 Performance

In the headless run Light mode was on by itself ("On · Lighter") because the test machine is slow; on a normal computer it starts off.

| Control (as shown) | What it does | Type | Default | Stored in | Live | Tip |
|---|---|---|---|---|---|---|
| Light mode | Lighter graphics on or off | switch | off (switches on by itself on slow hardware) | `UI.pm.on` (older: `UI.lite`, `UI.liteMan`) | yes | yes |
| Lightest / Lighter / Optimised / Full effects | The graphics level | 4 buttons | Automatic chooses | `UI.pm.st`, `UI.fx` | yes | yes |
| Automatic (and Undo after it) | Measures this computer and picks the level | button | – | `UI.pm.user` | yes | yes |
| Frame limit | As fast as the screen (up to 240), 120, 60 fps | select | as fast as the screen | `UI.fpsCap` | yes | no |
| Frame rate, Lowest 10 s, Work a frame | Live read-outs with a graph | read-out | – | – | – | – |
| What each effect costs: Refraction | Bending at the glass edges (Chromium only) | switch | follows the level | `UI.fx.refr` | yes | yes |
| Blur: Off / Picture / Live | How the blur behind glass is made | 3 buttons | follows the level | `UI.fx.blur` | yes | yes |
| Edge light | The light line inside glass edges | switch | follows the level | `UI.fx.edge` | yes | yes |
| Animations | Moving effects | switch | follows the level | `UI.fx.anim` | yes | yes |
| Savers: Softer blur while playing | Lighter glass during playback | switch | on | `UI.glPlay` | yes | yes |
| Half-size picture behind glass | What shows through glass is refreshed less often | switch | on | `UI.glBack` | yes | yes |
| Note cache | Repeating notes are rendered once | switch | on | `UI.noteCache` | yes | yes |
| Sleeping tracks | Tracks with nothing to play are unplugged | switch | on | `UI.fxSleep` | yes | yes |
| Background freeze | Tracks that do not change are frozen in the background | switch | on | `UI.bgFreeze` | yes | yes |
| Freeze when in the background | Stops drawing when AudioLab is not in front | switch | on | `UI.aoFreeze` | yes | yes |
| Keep visuals in the background | Keeps drawing anyway | switch | off | `UI.aoVisuals` | yes | yes |

### 2.6 Glass & light

| Control (as shown) | What it does | Type | Default | Stored in | Live | Tip |
|---|---|---|---|---|---|---|
| Glass preview: Your setting / Full effects / Optimised / Lighter / Lightest | Shows the preview at another level. Changes only the preview, not the app | 5 chips | Your setting | – | – | yes |
| "Light mode and what each effect costs: Performance" | Jumps to the Performance tab | link | – | – | – | no |
| Transparency (Solid to Clear) | How much shows through panels | slider | 50% | `UI.trans` | yes | no |
| Blur (Sharp to Soft) | Blur strength | slider | 18 px | `UI.blur` | yes | yes |
| Edge light (Off to Bright) | Strength of the edge line | slider | 60% | `UI.edge` | yes | yes |
| Refraction (Off to Strong) | **Hidden in the page** (display none) | slider | 40% | `UI.refr` | – | – |
| A second Refraction switch (`fxRefr`) | **Hidden in the page** | switch | off | – | – | – |

### 2.7 Colours & clips

| Control (as shown) | What it does | Type | Default | Stored in | Live | Tip |
|---|---|---|---|---|---|---|
| Background (Black to Light) | Brightness of the background | slider | 40% | `UI.bgL` | yes | no |
| Tint | Hue of the background | slider | 215° | `UI.tintH` | yes | no |
| Tint amount | How strong the tint is | slider | 25% | `UI.tintA` | yes | no |
| Clip transparency (Clear to Solid) | How solid clips are | slider | 36% | `UI.clipA` | yes | yes |
| Arrangement grid (Dim to Bright) | Brightness of the grid lines | slider | 50% | `UI.gridB` | yes | no |
| Thin ticks between beats when zoomed in | Extra grid ticks | checkbox | on | `UI.subTicks` | yes | no |
| Stronger lines every 4 bars | Stronger 4-bar lines | checkbox | on | `UI.bars4` | yes | no |
| App icon | Icon in the dock or taskbar, or the browser tab | picture grid | Ocean Yellow | browser: localStorage `audiolab-app-icon`; desktop: `app-icon.json` in the shell | yes | yes (code only; pictures did not load headless) |

### 2.8 Zoom and playhead

| Control (as shown) | What it does | Type | Default | Stored in | Live | Tip |
|---|---|---|---|---|---|---|
| Zoom style (map and arrangement): Picture / Ableton | Picture: time and track height zoom together. Ableton: drag down on the map or ruler to zoom | 2 cards | Picture | `UI.mapZoom` | yes | no |
| Playhead: Keep centred / Page by page / Stay in place / Don't follow | How the view follows the playhead | 4 cards | Keep centred | `UI.follow`, `UI.followMode` | yes | no |
| Playhead look: Shape (Line, Triangle head, Handle, Glow, Beam, Double line, Comet tail, Scanning bar, Dashed) | Shape of the playhead | 9 picture buttons | Line | `UI.ph` (shape) | yes | yes |
| Colour: Accent, 8 swatches, Other | Colour of the playhead | 9 buttons + colour field | Accent | `UI.ph` (colour) | yes | yes |
| Thickness | 1 to 6 px | slider | 1.5 px | `UI.ph` (width) | yes | no |
| Show the time above the playhead | Time flag on the playhead | checkbox | on | `UI.ph.t` | yes | no |
| Back to the standard playhead | Resets the look | button | – | – | – | no |

### 2.9 Keyboard shortcuts

| Control (as shown) | What it does | Type | Default | Stored in | Live | Tip |
|---|---|---|---|---|---|---|
| Shortcut set | AudioLab (default), Ableton Live, FL Studio, Cubase | select | AudioLab | `UI.scPre` | yes | no |
| Search field | Filters the list | search | – | – | – | no |
| 57 rows: 44 commands that can be changed (31 have a key, 13 are "not set") and 13 fixed rows that only explain (Delete, Copy, Cut, Paste, drag gestures, arrow keys, MIDI learn) | Click a key to change it, ✕ to clear it | key buttons | see the list in the app | `UI.keys` | yes | yes |
| ↺ Reset all (shown after a change) | Back to the chosen set | button | – | – | – | no |

Commands without a key: Quantize the selected clip, Mute / unmute the selected clip, Rename the selected clip, Mute the selected track, Solo the selected track, Instrument browser, Effects browser, Open the selected clip in the piano roll, Keyboard piano on / off, Follow the playhead, Zoom in, Zoom out, Show automation lanes, Close all floating windows.

### 2.10 Project file

| Control (as shown) | What it does | Type | Default | Stored in | Scope | Live | Tip |
|---|---|---|---|---|---|---|---|
| Save, Save as…, Open… | File actions | 3 buttons | – | – | – | – | no |
| Save as template… | Saves the project as a template | button | – | – | – | – | yes |
| Autosave | Autosave on or off | switch | on | `UI.autosave` | global | yes | yes |
| Every 1 / 2 / 5 / 10 minutes | Autosave interval | select | 2 minutes | `UI.asMin` | global | yes | no |
| Also write to the project's .audiolab file when it has one | Otherwise only a backup copy in the browser | checkbox | on | `UI.asFile` | global | yes | no |

Read-outs: project name, file name, "All saved", time the project was open, time actually working, what a `.audiolab` file holds, where files are saved.

### 2.11 Export audio

| Control (as shown) | What it does | Type | Default | Stored in | Scope | Live | Tip |
|---|---|---|---|---|---|---|---|
| Save, Save as .audiolab…, Open… | **The same three file buttons as on Project file** | 3 buttons | – | – | – | – | no |
| File name | Name of the exported file | text | "AudioLab mix" | **not stored** | session | – | no |
| Format: WAV / FLAC / MP3 | File format | 3 cards | WAV | **not stored** | session | – | no |
| Sample rate | Same as the engine, 44.1 to 192 kHz | select | same as the engine | **not stored** | session | – | no |
| Bit depth | 16, 24, 32-bit float | select | 24-bit | **not stored** | session | – | no |
| MP3 bitrate (MP3 only) | 128 to 320 | select | 320 | **not stored** | session | – | no |
| FLAC compression (FLAC only) | Best, Fast | select | Best | **not stored** | session | – | no |
| Dither | TPDF, TPDF + noise shaping, Off | select | TPDF | **not stored** | session | – | yes |
| Normalize | Off, peak to −1.0, peak to −0.1 dBFS | select | Off | **not stored** | session | – | yes |
| Range | Whole song, from the playhead to the end | select | Whole song | **not stored** | session | – | no |
| Tail | None, 1, 2, 4, 8 s | select | 2 s | **not stored** | session | – | no |
| Fixed seed | Same project and seed give the same sound every export | checkbox | on | `UI.exSeed` | global | – | no |
| Seed number, New seed | The seed | number + button | random per project | `S.seed` | **project** | – | button yes |
| Fast render | Off: gentle background render. On: as fast as possible | switch button | off | `UI.exFast` | global | – | no |
| Safety limiter on the export | Stops overs above −1 dBFS | checkbox | on | **not stored** | session | – | yes |
| Pick a folder first when the browser allows it | Folder picker before the export | checkbox | on | **not stored** | session | – | no |
| Export stems (one file per track), Export mix, Cancel render | Actions | 3 buttons | – | – | – | – | stems yes |

Tested: after changing format, bit depth, dither, tail, limiter and file name and restarting the app, all were back at their defaults.

## 3. Inventory: setting-like controls outside Settings

Device knobs, presets, clip and note data are the song itself and are not listed. Listed is everything that sets how the program looks or behaves.
### 3.1 Mixer

#### 3.1.1 Mixer window header (always visible)

| Control | Where / how reached | What it does | Type | Default | Stored in | Scope | Live | Tip | Also in Settings? (in sync?) |
|---|---|---|---|---|---|---|---|---|---|
| Picture dropdown ("Waveform ▾", `#mxVw`) | header, click | What every channel shows: Waveform, Level meters, Spectrum, Spectrogram, Stereo field, Fun. Opens the picture menu `#w9m` (which also has the 4 pan styles) | button + popup grid | Waveform | `UI.mxView` | global | yes | yes | No. Not in Settings and not in the gear popover |
| Spectrum (`#mxDev`) | header, click | Opens/closes the floating spectrum overlay of the master (plus the selected track) | toggle | off | overlay list `SPO.list` (session; not verified further) | session | yes | yes | Gear popover "Spectrum overlay" (same thing, in sync). Not in Settings |
| Compact channels (`#mxCmp`) | header, click | Thin strips: name, level, fader only; window gets shorter | toggle | off | `UI.mxCompact` (+ `UI.mxFullH` remembers the old height) | global | yes | yes | Yes: gear popover and Settings › Interface › Mixer "Compact channels". In sync both ways (tested) |
| Cables (`#mxCab`) | header, click | Shows sends, group outputs and sidechains as cables under the channels | toggle | on | `UI.mxs.cab` | global | yes | yes | Yes: gear popover and Settings › Interface › Mixer › Routing "Cables". In sync (tested) |
| Mixer settings (gear, `#mxSetB`) | header, click | Opens the popover "Mixer settings" (next table) | button | – | – | – | – | yes | Popover ends with "More mixer settings…" which opens Settings › Interface and scrolls to the Mixer block |
| Window size and place | drag edges / title | Mixer window position, size, narrower width | drag | 1100x470 | `UI.win.mixWin`, `UI.winSized`, `UI.mxCapW`, `UI.mxAutoV` | global | yes | no | No |

#### 3.1.2 Gear popover "Mixer settings" (`#mxsPop`) and its copy in Settings

The same builder (`mxsHtml`, line 9496) draws both. The Settings copy has 5 more options (marked "Settings only"). Both are synced by `mxsSync()`.

| Control | Where / how reached | What it does | Type | Default | Stored in | Scope | Live | Tip | Also in Settings? (in sync?) |
|---|---|---|---|---|---|---|---|---|---|
| Spectrum overlay | popover › Window | Same as the header Spectrum button | checkbox | off | session | session | yes | yes | **Popover only** (not in the Settings copy) |
| Compact channels | popover › Channels | see 3.1.1 | checkbox | off | `UI.mxCompact` | global | yes | yes | Yes, in sync. Third place: header button |
| Channel number | **Settings only** | The number in front of each channel name | checkbox | on | `UI.mxs.num` | global | yes | yes | Settings only |
| Strip width | popover › Channels | Channel width 64 to 170 px; double-click resets | slider | 96 px | `UI.mxs.w` | global | yes | yes | Yes, in sync |
| Master strip width | **Settings only** | Master width 110 to 240 px | slider | 136 px | `UI.mxs.mw` | global | yes | yes | Settings only |
| Fader height | **Settings only** | 76 to 320 px, far left = Auto | slider | Auto | `UI.mxs.fh` | global | yes | yes | Settings only |
| Pan control | popover › Channels | Pan look: Automatic, Slider, Half dial, Full dial | select | Automatic | `UI.mxs.panst` | global | yes | yes | Yes, in sync (tested). Also in the picture menu and in the right-click menu on a pan control: **4 places** |
| Keep the master in view | popover › Channels | Master stays at the right edge while scrolling | checkbox | on | `UI.mxs.pin` | global | yes | yes | Yes, in sync (tested). Third place: pin button on the master strip |
| Effect slots / Sends / Picture / Pan / Mute, solo, record / dB scale / Volume number (7) | popover › Each channel shows | Show or hide that part of every strip | 7 checkboxes | all on | `UI.mxs.fx, snd, view, pan, btn, sc, val` | global | yes | yes | Yes, in sync |
| Highest peak | **Settings only** | Loudest peak per channel under the fader | checkbox | off | `UI.mxs.pkr` | global | yes | yes | Settings only |
| Group colour band | **Settings only** | Second colour band on channels in a group | checkbox | off | `UI.mxs.gband` | global | yes | yes | Settings only |
| Cables | popover › Routing | see 3.1.1 | checkbox | on | `UI.mxs.cab` | global | yes | yes | Yes, in sync. Third place: header button |
| Loudness and peak / True peak / Loudness target / Stereo correlation (4) | popover › Master shows | Show or hide those read-outs on the master strip | 4 checkboxes | all on | `UI.mxs.mLu, mTp, mTgt, mCorr` | global | yes | yes | Yes, in sync |
| Level meters: Speed / Reading / Peak hold / Colours (4) | popover › Level meters | Meter ballistics and colours for **every** meter in the app | 4 selects | Instant / Peak / 1 second / Classic | `UI.mtr.spd, alg, hold, col` | global | yes | yes ("The same setting as Settings, Interface, Level meters") | Yes, **three places**: popover, Settings › Interface › Mixer (same selects), and Settings › Interface › Level meters (`#mtrSet`, picture buttons). All in sync (tested both ways) |
| Fader and meter design | popover (bottom) | One of 22 designs (Classic … Flat bars 2), used in the mixer and on the track bars | picture list button | 22 Flat bars 2 | `UI.mxs.fd` | global | yes | yes | Yes, in sync (tested). Also right-click on any fader: **3 places**. The Settings look presets (AudioLab / Live / FL / Cubase …, `data-thp`) also overwrite it and the meter colours |
| More mixer settings… | popover (bottom) | Opens Settings › Interface, scrolled to Mixer | link button | – | – | – | – | yes | The reverse link is only a sentence in Settings ("the same settings as the settings button at the top right of the mixer"), not a button |

#### 3.1.3 On the strips and under them

| Control | Where / how reached | What it does | Type | Default | Stored in | Scope | Live | Tip | Also in Settings? (in sync?) |
|---|---|---|---|---|---|---|---|---|---|
| Master pin | pin button in the master's name | Same as "Keep the master in view" | toggle | on | `UI.mxs.pin` | global | yes | yes (changes with state) | Yes (3.1.2), in sync |
| Per-channel picture | **right-click only** on a channel's picture | That channel shows its own picture; "On every channel", "Like the mixer" | popup grid `#w9m` | follows the mixer | `t.mxv` (track), `S.mxvM` (master) | **per project** | yes | yes | No |
| Picture colours and options | **right-click a preview inside the picture menu** (second level) | Colour scheme per view; Look; Size (stereo); Show toggles; Animation (Fun) | menu | per view (`MXDEF`) | `UI.mxCol[view]`, `UI.mxOpt` | global | yes | only the hint "Right-click for colours and options" | No. Two right-clicks deep |
| Pan style | right-click a pan control | Automatic / Slider / Half dial / Full dial | menu | Automatic | `UI.mxs.panst` | global | yes | no | Yes (3.1.2), in sync |
| Centre this channel | right-click a pan control | Pan back to the middle (an action) | menu item | – | project | – | yes | no | No |
| Stereo field behind pan | **right-click only** on a pan control | Faint stereo picture behind the pan control | switch | on | `UI.w9pf` | global | yes | sub-text | **No. Only here** |
| Fader and meter design | right-click a fader (any strip, master too) | 22 designs | menu | 22 | `UI.mxs.fd` | global | yes | no | Yes (3.1.2), in sync |
| Highest peak reset | click the number (Shift = all) | Resets peak memory | action | – | session | – | yes | in Settings tip | – |
| Loudness target | click "Target" on the master strip | 8 targets (Spotify −14 … Podcast −16) | menu | Spotify, YouTube, Tidal | `UI.lufsP` | **global** | yes | yes | Not in Settings. Second place: the Loudness window (`#lmSel`), kept in sync when open |
| Mono / Dim / L↔R | master strip buttons | Monitor checks; not in the export | 3 toggles | off | `UI.monoChk`, `UI.swapChk`; Dim = session (`MONDIM`) | global / session | yes | yes | Mono and L↔R: **yes**, Settings `#monoChk`, `#swapChk`. Mixer → Settings in sync. **Settings → mixer: the value changes but the mixer buttons do not repaint** (tested: Mono stayed lit after unticking, L↔R stayed dark after ticking). Dim: mixer only |
| Mix A / B, A→B | master strip | Two versions of the mix | buttons | A | project (not verified in detail) | per project | yes | yes | No |
| Cable legend: Send / Output to group / Sidechain | legend under the channels | Hide or show each cable kind | 3 toggles | all on | `UI.mxs.cabHide` | global | yes | yes | **No. Only here** |
| Selected only | cable legend | Only cables of the selected channel | toggle | off | `UI.mxs.cabSel` | global | yes | yes | **No. Only here** |
| Tidy | cable legend | Tidy straight lines or loose curves | toggle | on (tidy) | `UI.mxs.cabSty` | global | yes | yes | **No. Only here** |

#### 3.1.4 Mixer right-click menus (what really opens)

| Right-click on | Menu |
|---|---|
| Channel name, peak number, empty part of a strip | The track menu (Rename, colour, Import audio, Mute, Solo, Duplicate, Spectrum overlay, Freeze, Bounce, Add track, Routing…, Delete). No settings |
| Picture | Picture menu `#w9m` for that channel (3.1.3) |
| Pan area | Pan control menu (3.1.3) |
| Fader | Fader and meter design (3.1.3) |
| Effect slot | Device menu: Turn off, Copy, Paste after, Duplicate, Delete |
| "+ Add effect" slot | Paste device + the list of 42 effects |
| **Send knob, Mute, Solo, Record arm** | The same "Devices · Add effect" list (looks unintended: the strip handler for slots catches them) |
| Master name, master read-outs, Mono/Dim, A/B, header buttons, title bar, cable legend, cables, empty mixer area | Nothing |

### 3.2 Devices panel

Almost everything in the devices panel is a device parameter saved in the project (knobs, presets, on/off, EQ bands, analyser Off/Post/Pre+Post). Those are not settings and are not listed. Setting-like controls:

| Control | Where / how reached | What it does | Type | Default | Stored in | Scope | Live | Tip | Also in Settings? (in sync?) |
|---|---|---|---|---|---|---|---|---|---|
| Devices tab (`#fxHide`) | panel header, click | Hide / show the devices panel | toggle | shown | `UI.fxHide` | global | yes | yes | No (the Settings layout picture places the panel, not this) |
| Pop out (`#fxPop`, or drag the tab) / "Back to panel" | panel header | Devices as a floating window; drag back to dock top or bottom | toggle + drag | docked | `UI.devPop`, `UI.win`, `UI.order` | global | yes | yes | Top/bottom place = `UI.order`, the same key the Settings › Interface layout picture edits |
| Panel height | drag the border `#prDiv` / `#prTopH` | Height of devices vs piano roll | drag | 262 px | `UI.fxDH`, `UI.prDH` | global | yes | yes | No |
| Track tabs, Master tab | panel header | Which track's chain is shown | tabs | selected track | selection | session | yes | yes | – |
| Modulators column collapse | chevron on the column | Collapse / open the modulators | toggle | open | `UI.modC` | global | yes | yes | No |
| Parameters (show/hide) | button on each device | Only the picture stays | toggle | shown | instrument: `t.inst.kOpen` (project); effects: on the device (project, not verified per type) | per device, per project | yes | yes | No. Display-first default for new devices is not a setting anywhere |
| Pin | button on each device | Device in its own window over the arrangement | toggle | off | `S.pins` | per project | yes | yes | No |
| FX on (bypass all) | track box | Turns the track's effects off to compare | toggle | on | project (not verified) | per track | yes | yes | – |
| Effects A/B, A→B | track box | Two versions of the effect chain | buttons | A | project | per track | yes | yes | – |
| Change | on each device | Try other devices in that place | button | – | – | – | – | yes | – |
| Right-click a device header | menu | Turn off, Copy device, Paste after this, Duplicate, Delete | menu | – | – | – | – | – | No settings |
| Right-click anywhere else in the chain (track box, instrument, modulators, add box, empty) | menu | Paste device + "Add effect" list (42) | menu | – | – | – | – | – | No settings |
| Right-click track tabs, Master tab, Devices tab, title | – | Nothing | – | – | – | – | – | – | – |
| Effects sleep when silent | **Settings only** (`#slpOn`, Performance) | Devices stop working while their track is silent | checkbox | on | `UI.fxSleep` | global | yes | no title | No control in the devices panel |
| Note cache | **Settings only** (`#ncOn`, Performance) | Pre-renders notes; only works with the old voice engine (`UI.poly===false`) | checkbox | on | `UI.noteCache` | global | yes | no title | No control in the panel |
| `UI.eqAll` | **no control anywhere** | Run EQ bands at 0 dB too | flag | off | `UI.eqAll` | global | – | – | Read once (line 6399), never set |
| `UI.fxBand` | **no control anywhere** | Devices band layout switch | flag | on | `UI.fxBand` | global | – | – | Read once (line 14865), never set |

### 3.3 MIDI panel (piano roll)

| Control | Where / how reached | What it does | Type | Default | Stored in | Scope | Live | Tip | Also in Settings? (in sync?) |
|---|---|---|---|---|---|---|---|---|---|
| Tools (9): Draw P, Paint B, Delete D, Mute T, Slice C, Select E, Move H, Zoom Z, Scrub Y | header | Editing tool | segmented | Draw | `PR.tool` | **session** | yes | yes (one word) | Keys listed in Settings › Keyboard shortcuts (not verified which are editable) |
| Timing ▾ / Length ▾ / Shape ▾ | header | Actions (Quantize, Humanize, Legato, Chop, Glue, Strum, Flip, Reverse, Octave…) | 3 menus | – | – | – | – | yes (one word) | Actions, not settings |
| Snap | header | Note grid: 1/4, 1/8, 1/16, 1/32, 1/8T, 1/16T, Off | select | 1/16 | `PR.snap` | **session** | yes | yes | No. Separate from the arrangement snap |
| Scale root + Scale | header | Highlighted key: C…B; none, major, minor, harmonic minor, dorian, 2 pentatonics | 2 selects | A minor | `PR.root`, `PR.scale` | **session** (not in the project, not in UI) | yes | yes | No |
| Scale lock | header | New and moved notes snap into the key | toggle | off | `UI.prLock` | global | yes | yes | No |
| Chord | header | Draw a whole chord per click | select | none | `PR.chord` | session | yes | yes | No |
| Ghost ▾: In colour / Subtle grey / Off | header menu | Other tracks' notes behind the clip | menu | In colour | on/off `PR.ghost` (**session**), grey `UI.ghostGrey` (global) | mixed | yes | yes | No |
| Ghost ▾: per-track ticks | header menu | Which tracks are ghosted | checks | all on | `PR.ghostOff` | session | yes | no | No |
| Feel | header | Groove pool, humanize, chords window | window | Groove tab | tab `UI.feelTab`; amounts session | global / session | yes | yes | No |
| Lane select | bottom lane | Velocity, Pitch bend, CC… | select | Velocity | `PR.lane` | session | yes | yes | No |
| Lane height | drag | Height of the bottom lane | drag | 64 px (128 full screen) | `UI.velH`, `UI.velHF` | global | yes | no | No |
| Floating window / Full screen / Close | header right | Window mode | 3 buttons | docked | `UI.prMode`, `UI.prW` | global | yes | yes | No |
| Show devices (`#prDev`, full screen only) | header right | Devices strip under the full-screen piano roll | toggle | off, switched on automatically | `UI.prDev` | global | yes | aria-label only | No |
| Height borders | drag `#prTopH`, `#prDiv` | Piano roll height vs devices | drag | follows devices | `UI.prDH`, `UI.fxDH` | global | yes | yes | No |
| Zoom / scroll | wheel, Zoom tool | `PR.ppb`, `PR.rh`, `PR.x`, `PR.y` | – | 90 px per beat, 14 px rows | session | session | yes | – | No (Settings › Zoom and playhead is about the arrangement; not verified whether it also drives the piano roll) |
| Right-click in the piano roll | canvas, title, header | **No menu at all** (`contextmenu` is only blocked, line 6927) | – | – | – | – | – | – | – |

Adjacent, seen but outside this slice: the MIDI capture menu (line 8078: phrase gap, look-back, quantize, place, buffer) stores `UI.capGap, capMax, capQ, capPlace` and exists only as a menu; keyboard piano (`UI.kbPiano, kbMode, kbCompact, kbHidden`); `UI.midiMap` (MIDI learn).

### 3.4 Top bar and transport

| Control | Where / how reached | What it does | Type | Default | Stored in | Scope | Live | Tip | Also in Settings? (in sync?) |
|---|---|---|---|---|---|---|---|---|---|
| Logo button | Transport bar, left click | Opens Settings | Button | – | – | – | – | Yes | It is the route to Settings |
| Logo quick menu | Right-click the logo | Save, Save as, Open, Quick export mixdown / stems, Export settings…, MIDI learn, Undo, Panic, Restart audio engine, Restart AudioLab, Song overview, **Light mode: on/off**, Interface and DAC…, Settings… | Menu | – | – | – | Yes | No | Light mode = Performance `#liteChk` (in sync, tested). Three links into Settings (Export, Interface and DAC, Settings) |
| Left / right locator | Transport bar read-outs | Show loop start and end; set by dragging on the ruler | Read-out | bar 1 / song end | `S.loopRange` | Project | Yes | Yes | No |
| Cycle (loop) | `#bLoop`, shortcut Shift+L | Loop on / off | Toggle | On in the demo | `S.loop` | Project | Yes | Yes | No |
| Play: flash source | **Right-click the Play button only** | Play button flashes on: Auto (kick, else beat) / Every beat / Kick drum only | Menu, 3 choices | Auto | `UI.flashSrc` | Global | Yes | No (the Play tooltip does not mention it) | No |
| Stop, Home, Record | Transport bar | Actions | Buttons | – | – | – | – | Yes | No |
| Capture panel: Sound buffer source | Click `#bCap` | Off / Master out / Audio input | 3 buttons | Master out | `UI.retroOn`, `UI.retroSrc` | Global | Yes | No | No |
| Capture panel: keep last N seconds | Click `#bCap` | 5 / 10 / 15 / 30 / 60 s | 5 buttons | 15 s | `UI.retroLen` | Global | Yes | No | No |
| Capture: phrase ends after silence | **Right-click `#bCap` only** | 4 / 10 / 30 seconds | Menu | 10 s | `UI.capGap` | Global | Yes | No | No |
| Capture: look back at most | Right-click `#bCap` only | 1 / 5 / 30 minutes | Menu | 5 min | `UI.capMax` | Global | Yes | No | No |
| Capture: quantize | Right-click `#bCap` only | Off / 1/16 / 1/8 / 1/4 | Menu | Off | `UI.capQ` | Global | Yes | No | No |
| Capture: place it | Right-click `#bCap` only | Where I played it / At the playhead | Menu | Where I played it | `UI.capPlace` | Global | Yes | No | No |
| Capture: sound buffer keeps | Right-click `#bCap` only | 30 / 60 / 120 seconds | Menu | 60 s | `UI.retroSec` | Global | Yes | No | No |
| Keyboard piano on / off | `#bKbd`, command "Keyboard piano on / off" (no key set) | Shows the on-screen keyboard | Toggle | Off | `UI.kbPiano` | Global | Yes | No (aria-label only) | No |
| Keyboard piano: layout | Buttons in the keyboard panel | Piano / QWERTY / Pads | 3 buttons | Piano | `UI.kbMode` | Global | Yes | No | No |
| Keyboard piano: Compact, Hide | Buttons ▭ and - in the panel | Small panel; hide but keep on | Toggles | Off | `UI.kbCompact`, `UI.kbHidden`, position `UI.kbw` | Global | Yes | Yes | No |
| Tempo | `#bpm` field, ▲▼, drag | Song tempo 40 to 240 | Number | 120 (145 in the demo) | `S.bpm` (tempo changes: tempo lane points) | Project | Yes | No | No |
| Tap tempo | `#bTap` | Sets the tempo from taps | Button | – | – | – | Yes | Yes | No |
| Time signature | Click the "4/4" read-out | Chips 4/4, 3/4, 2/4, 5/4, 6/8, 7/8, 9/8, 12/8, 5/8, 7/4, Other… | Menu with chips | 4/4 | `S.sigs` | Project | Yes | No | No |
| Show the tempo and time signature lane | Same menu, last item; also the section-strip menu | Shows a lane above the tracks | Toggle item | Off | `UI.tempoLane` | Global | Yes | No | No |
| Metronome on / off | `#bClick`, key C, Metronome setup "Activate metronome click" (`#msOn`) | Click while the song plays | Toggle | Off | `S.click` | **Project** | Yes | Yes | No. Button and setup window in sync |
| Count-in on / off | `#bCount`, Metronome setup `#msCI` | Count in before playback | Toggle | Off | `UI.countIn` | **Global** | Yes | Yes | No. Both in sync |
| Count-in bars | Metronome setup, General, − / + | Bars of count-in | Stepper | 1 | `UI.countBars` | Global | Yes | No | No |
| Click while playing / recording / during count-in | Metronome setup, General | Three switches | Checkboxes | all on | `UI.clickPlay`, `UI.clickRec`, `UI.clickCount` | Global | Yes | No | No |
| Click sound | Metronome setup, Click sounds | Cubase beep, Firm wood, Soft wood, Rim click, Cowbell, Hi-hat, Sine ping | 7 buttons | Cubase beep | `UI.clickSnd` | Global | Yes | No | No |
| Hi (accent), Lo (beats), Overall level | Metronome setup, Click sounds | Click volumes | 3 sliders | 90, 70, 50 % | `UI.clickHi`, `UI.clickLo`, `UI.clickLvl` | Global | Yes | No | No |
| Click pattern | Metronome setup, Click patterns; the pattern box `#mpat` opens it | 8 presets, steps per bar (2 to 16), per-step accent / beat / off | Buttons, select | Default, 4 steps | `UI.clickPat` | Global | Yes | `#mpat` yes, inside no | No |
| Position (bars) | Click `#posBars` | "Go to bar" box | Read-out + dialog | – | – | – | – | No | No |
| Clock | `#posTime` | Time read-out. No modes, click does nothing | Read-out | h:mm:ss.ms | – | – | – | No | No |
| Undo / Redo / Time Machine | Buttons; right-click any of the three for the undo history | Actions | Buttons, menu | – | – | – | – | Yes | No |
| Mixer button, master level | `#mBtn` click; right-click for the master fader pop-up | (mixer is in the other part of the audit) | Button | – | – | – | – | Yes | – |
| Master loudness target | Click the LUFS read-out `#lufsB`, select "Target"; also the mixer's loudness target menu | Spotify / Apple / Amazon / SoundCloud / Club… | Select | Spotify, −14 LUFS | `UI.lufsP` | **Global** | Yes | No | Not in Settings (Settings › Interface › Master shows › "Loudness target" only shows or hides it). LUFS pop-up and mixer menu in sync |
| Spectrum overlay | Button in the LUFS pop-up; also in the track menu | Pinned see-through spectrum | Button | Off | `UI.spov` (pinned overlays) | Global | Yes | Yes | No |
| CPU read-out | Click `#cpu` | Opens the Performance panel: figures, Reset counters, **Turn on / off light mode**, Restart audio engine, Restart AudioLab | Pop-up | – | Light mode: `UI.pm.on`, `UI.liteMan`, `UI.lite` | Global | Yes | Partly (`#latV`, some rows) | Light mode = `#liteChk` (in sync, tested). **No link from this panel to Settings › Performance or Audio**, though its warning text says "Try a bigger buffer in the Control Panel" |
| Tutorial mode button (?) | Top right `#bTut`, F1 | Guided tour | Button | Shown | Visibility: `UI.tutBtn` | Global | Yes | Yes | Visibility only in Settings › General `#genTut` |
| Full screen | Top right `#bFs` | Browser / window full screen | Toggle | Off | Not stored by the page (the desktop shell remembers it in window-state.json) | – | Yes | Yes | No |
| Assistant | `#bAI`, Mod+K | Opens the assistant panel | Toggle | Off | – | – | Yes | Yes | No |
| Project tabs: ＋ | Click `#pAdd` | New project…, Open project…, Demo: Fractals remake | Menu | – | – | – | – | Yes | No |
| Project tab menu | Right-click a tab, or any empty part of the tab bar **or of the transport bar** | Save, Save as…, Open…, Rename…, Duplicate, New project…, **Project file settings…**, Close, Close other tabs | Menu | – | – | – | – | No | Link to Settings › Project file |
| Transport bar: edit mode | Only from Settings › Interface › Layout › Transport "Edit…" (and the Edit button on the layout picture) | Drag modules, ▭ compact, ● hide per module; add Flexible gap, Fixed space, Divider line, Time of day, Song progress, Tap tempo, Loop length, Work timer, Current section, Previous / next section, MIDI activity, Clip indicator | Edit mode with palette | 12 modules shown | `UI.trOrder`, `UI.trCompact`, `UI.trHide`, `UI.trX` | Global | Yes | Partly | Settings is the only entry. "Reset" and "Shrink on small screens" (`UI.trAuto`) are in Settings only |
| Song overview | Shift+O, logo menu, shell View menu | Whole song at a glance; right-click inside for Leave / Zoom in here | Mode | Off | Not stored | – | Yes | – | No |
| Time above the playhead (flag) | Shown at the playhead | Time read-out | – | On | `UI.ph.t` | Global | Yes | Yes | Settings › Zoom and playhead `#phT` only |

### 3.5 Arrangement

| Control | Where / how reached | What it does | Type | Default | Stored in | Scope | Live | Tip | Also in Settings? (in sync?) |
|---|---|---|---|---|---|---|---|---|---|
| Follow on / off | "Follow" chip on the ruler, left click; command "Follow the playhead" (no key set) | View scrolls with the playhead | Toggle | On | `UI.follow` | Global | Yes | No (canvas) | Settings › Zoom and playhead › Playhead ("Off" card). Chip and menu call `setFollow`, which re-syncs Settings. The command toggles `UI.follow` without re-sync (tested: Settings still showed "Keep centred" lit); Settings re-syncs when opened |
| Follow mode | Right-click the Follow chip | Keep the playhead in the middle / Stay in place / Look ahead / Page by page / Push at the edge, smoothly / Off | Menu, 6 choices | Middle (`center`) | `UI.followMode` | Global | Yes | No | **Partly.** Settings offers only 4 cards (Keep centred, Page, Stay, Off). "Look ahead" (`lead`) and "Push at the edge" (`edge`) exist only in the menu; with either chosen, no card is lit in Settings (tested) |
| Follow again 3 s after I stop scrolling | Right-click the Follow chip only | Auto-resume of Follow | Check item | On | `UI.followResume` | Global | Yes | No | No |
| Jump back to the playhead | Right-click the Follow chip; clicking the "back to playhead" marker | Action | Item | – | – | – | – | No | No |
| Playhead look in Settings | Last item of the Follow menu | Opens Settings › Zoom and playhead | Link | – | – | – | – | – | Existing quick route |
| Snap / grid step | **No control.** Clip moves snap to a step that follows the zoom (shortcut list: "the step follows the zoom"; Shift = 4×, Alt = 1/64) | – | – | – | – | – | – | – | No. (The piano roll has its own Snap select.) Missing setting |
| Grid brightness, thin ticks, 4-bar lines | Settings only | Look of the grid | – | 50 %, on, on | `UI.gridB`, `UI.subTicks`, `UI.bars4` | Global | Yes | – | Settings › Colours & clips only |
| Zoom (time) and track height | Pinch, Ctrl/⌘-scroll, modifiers set in Settings, map box edges, commands Zoom in / Zoom out (no keys set) | View zoom | Gestures | – | `V.ppb`, `V.th`, `V.x`, `V.y` (the project's view) | **Project** | Yes | – | Gesture keys and speed: Settings › Interface › Zoom and scroll (`UI.zs`); zoom style: Settings › Zoom and playhead (`UI.mapZoom`) |
| Track height (all tracks) | Drag the lower edge of a track header | One height for all tracks, 24 to 240 px | Drag | 96 | `V.th` | Project | Yes | No | No |
| Automation lane height | Drag the edge of an automation lane | Lane height factor 0.3 to 4 | Drag | 1 | `UI.laneZ` | **Global** (track height is per project) | Yes | No | No |
| Collapse all tracks | `#bColl` in the Tracks caption | Thin strips, click again to restore | Toggle | Off | `UI.collAll`, `UI.collPrev`, `UI.collTh` | Global flag, but it changes the project's `V.th` | Yes | Yes | No |
| Show all automation | `#bAut`; **right-click = hide all automation** | Opens every lane / hides them | Toggle | Off | Lanes: `t.lanes` in the project; the toggle state is not stored | Project | Yes | Yes (mentions right-click) | No |
| Record automation ("Write") | `#bAR` | Moving any control writes automation | Toggle | Off | `UI.autoRec` | Global | Yes | Yes | No |
| Track controls shown in every header | "Controls" button in the Tracks caption; **right-click a track header › "Customise track controls…"** | Which buttons and sliders each track shows, their order, icon Normal / Big / Hidden, pan style, M/S size, meter | Editor panel | Default layout | `UI.hcz` | Global | Yes | Yes | Settings › Interface › Layout: preview, "Customise…" (`#hczSetB`, opens the same editor) and "Reset" (`#hczSetR`). Same data, in sync |
| Track menu | Right-click a track header or an empty lane | Rename, colour, instrument, Mute, Solo, Duplicate, Spectrum overlay, Freeze, Bounce, add tracks, Export MIDI, Routing (group, sends, returns), Delete | Menu | – | Project | Project | Yes | No | No (actions and per-track data, no app options) |
| Clip menu | Right-click a clip | Open, Rename, Duplicate, Split, Quantize 1/16, Transpose, Bounce, Export MIDI, **Pitch bend range: 2 / 7 / 12 / 24**, Copy / Cut / Paste, Envelope editor, Envelope: Volume / Pan / Filter cutoff / Resonance, Mute, Delete | Menu | – | Clip, in the project | Project | Yes | No | No |
| Envelope editor "Live" | Checkbox in the envelope editor (clip menu) | Apply changes while dragging | Checkbox | On | `UI.envLive` | Global | Yes | No | No (code only, panel not opened) |
| Section strip menu | Right-click a section or the empty strip | Section: Loop this section, Play from here, Rename, colour, Select its clips, Delete. Empty strip: Add 8-bar section here, Loop the whole song, Show / Hide the tempo lane | Menu | – | Sections: project; tempo lane: `UI.tempoLane` | Mixed | Yes | No | No |
| Loop range | Drag along the ruler; **right-click the loop bar removes the loop** (no menu, toast only) | Loop range | Gesture | – | `S.loopRange`, `S.loop` | Project | Yes | No | No |
| Ruler right-click | Right-click the ruler outside the loop | Nothing (tested) | – | – | – | – | – | – | – |
| Master lane view | "View" button on the master lane (code only, lane not on screen in the test) | Master lane shows: Loudness map / Waveform / Colour waveform / Outline waveform; Beat and bar lines; Re-analyse now; Clear live loudness; Reset height; Reference song | Menu | Loudness map; lines on | `UI.mapView`, `UI.mapBeats` | Global | Yes | No | No |
| Map panel | Right-click the map: switch "Map", switch "Visualizer", "Visualizer sits" ×5. Drag the grip for height, double-click to reset | Show / hide, height | Menu, drag | Shown, 110 px | `UI.mapOff`, `UI.mapH` | Global | Yes | Grip yes | Settings › Interface › Layout `#layMap` (in sync through `pvSync`) |

### 3.6 Visualizer

| Control | Where / how reached | What it does | Type | Default | Stored in | Scope | Live | Tip | Also in Settings? (in sync?) |
|---|---|---|---|---|---|---|---|---|---|
| Visualizer on / off | Right-click the map or the visualizer › switch "Visualizer"; ✕ in its header | Shows the panel | Switch | Off | `UI.viz` | Global | Yes | ✕ yes | Settings › Interface › Layout `#layViz`. The right-click menu re-syncs Settings; the ✕ button does not (tested: checkbox stayed on); Settings re-syncs when opened |
| Visualizer sits | Select in its header (Top / Bottom / Left / Right / Window); same list in the right-click menu | Docking | Select and menu | Bottom | `UI.vizDock` | Global | Yes | No | Settings `#layVizDock`. Menu re-syncs; the header select does not (tested); re-syncs when opened. **Three places for one option** |
| View | Header buttons All / Spectrogram / Spectrum / Waveform / Levels | What is drawn | 5 buttons | All | `UI.vizMode` | Global | Yes | Yes | No |
| Size | Drag the resize corner / edge | Width and height | Drag | – | `UI.vizW`, `UI.vizH` | Global | Yes | Yes | No |
| Right-click menu | Right-click anywhere in the visualizer or the map | The "Panels" menu above (Map, Visualizer, Visualizer sits) | Menu | – | – | – | – | – | Same as Settings › Layout |

### 3.7 Performance, light mode and glass levels outside Settings

| Control | Where / how reached | What it does | Type | Default | Stored in | Scope | Live | Tip | Also in Settings? (in sync?) |
|---|---|---|---|---|---|---|---|---|---|
| Light mode on / off | (1) logo right-click "Light mode: on"; (2) CPU panel "Turn on / off light mode"; (3) shortcut ⌘⇧L; (4) "Turn off" on the "Light mode is on" card | Switches the lighter graphics level on or off | Toggle | Off (on by itself on weak hardware) | `UI.pm` {on, st, user}, `UI.liteMan`, `UI.lite` | Global | Yes | No | Settings › Performance `#liteChk`. All five places go through `pmSetOn` or the checkbox; tested in sync |
| "Light mode is on" card | Appears by itself for 10 s when the app switches light mode on (`liteAuto`) | Says why; buttons Turn off, ✕ | Card | – | – | – | – | No | No link to Settings › Performance |
| Level (Lightest / Lighter / Optimised / Full effects) | Settings only | Which graphics level light mode uses | – | – | `UI.pm.st`, `UI.fx` | Global | Yes | – | Settings › Performance only. Nothing outside Settings shows which level is active |
| Performance link | Settings › General and Settings › Glass & light: "Performance" button (`data-pmgo`) | Jumps to the Performance tab | Link | – | – | – | – | – | Existing quick route inside Settings |
| Frame limit, blur mode, edge, animation, glass while playing… | Settings only | – | – | – | `UI.fpsCap`, `UI.fx`, `UI.glPlay`, `UI.glBack`… | Global | – | – | Settings › Performance only |
| Engine status dot, latency read-out | In the CPU button | Read-outs | – | – | – | – | – | Yes | No |

Glass levels versus the new engine: docs/glass-engine-plan.md (section 1 and step G4) replaces the four levels Full / Optimised / Lighter / Lightest with three (GL engine, Blur, Solid) and replaces the sliders by presets. Today's `UI.pm.st` 0 to 3, `UI.fx`, and the old keys `UI.lite`, `UI.liteMan`, `UI.refr`, `UI.fxUser`, `UI.blur`, `UI.edge`, `UI.trans` are still read; several are kept only to migrate older choices (`pmInit`, `fxGet`).

### 3.8 Update window, icon picker, About, splash, tour

| Control | Where / how reached | What it does | Type | Default | Stored in | Scope | Live | Tip | Also in Settings? (in sync?) |
|---|---|---|---|---|---|---|---|---|---|
| Updates window | Settings › General "Check for updates"; desktop app menu "Check for Updates…" | Shows the version and what is new; in the browser only "Close" | Window | – | – | – | – | Yes | Opened from Settings |
| Update card / "update ready" window | Appears by itself in the desktop app | Install now, Later, Close | Card and window | – | "Later" per version: localStorage `al-upd-later`; last check: `al-upd-at`; finished update: `al-upd-done` | Global | – | Yes | No |
| Install updates automatically | Settings › General, desktop app only (`#updAutoChk`, added by code) | Installs when nothing plays, records or exports | Checkbox | Off | `UI.updAuto` | Global | Yes | Yes | Settings only. Not offered in the update window itself |
| App icon picker | Settings › Colours & clips › "App icon" (`#apicBox`) | Dock / taskbar icon, or the browser tab icon | Picture grid | Ocean Yellow | Browser: localStorage `audiolab-app-icon`; desktop: `app-icon.json` in the shell's user-data folder | Global | Yes | Yes | Settings only (inside "Colours & clips") |
| Track icon picker | Right-click a track's picture | Icon, symbol or emoji tab, icon colour | Pop-up | – | Icon: project; last tab: `UI.icTab` | Mixed | Yes | No | No |
| About window | Settings › General "What's inside AudioLab" | Information | Window | – | – | – | – | Yes | No settings found (code only, not opened) |
| Splash screen | Settings › General `#setSplash`, "Show now" | Splash at start | Checkbox | On | `UI.splash`; last start time `audiolab-boot` | Global | Next start | No | Settings only |
| Guided tour | F1, `#bTut`, Settings › General "Start the guided tour" | Tour | Button | – | – | – | – | Yes | Button visibility in Settings › General |

### 3.9 Hidden options: only a menu, a shortcut, or no control at all

| Option | How reached | Stored in | Note |
|---|---|---|---|
| Play button flash source | Right-click Play | `UI.flashSrc` | Not hinted anywhere |
| Capture: silence gap, look-back, quantize, placement, buffer length | Right-click Capture | `UI.capGap`, `UI.capMax`, `UI.capQ`, `UI.capPlace`, `UI.retroSec` | The capture panel shows only two of the seven capture options |
| Follow: Look ahead, Push at the edge, Follow again after 3 s | Right-click the Follow chip | `UI.followMode`, `UI.followResume` | Not in Settings |
| Hide all automation | Right-click `#bAut` | not stored | Tooltip mentions it |
| Remove loop | Right-click the loop bar | `S.loopRange` | No menu |
| Customise track controls | Right-click a track header (also the Controls button) | `UI.hcz` | Also in Settings |
| Map / Visualizer / dock side | Right-click the map or the visualizer | `UI.mapOff`, `UI.viz`, `UI.vizDock` | Also in Settings |
| Tempo and time signature lane | Time signature menu, section strip menu | `UI.tempoLane` | Not in Settings, not in the shortcut list |
| Undo history | Right-click Undo, Redo or Time Machine | – | |
| Project file settings | Right-click a tab or an empty part of the transport bar | – | Link to Settings |
| Commands with no key set | Shortcut list (Settings › Keyboard shortcuts): Instrument browser, Effects browser, Open in piano roll, Keyboard piano, Follow the playhead, Zoom in, Zoom out, Show automation lanes, Close all floating windows, Quantize, Mute / Rename clip, Mute / Solo track | `UI.keys` | Reachable only after binding a key, or by their buttons |
| Pooled voice engine off | **No control.** `UI.poly=false` only by hand (console) | `UI.poly` | Shown as "Voice engine: on / off" in the CPU panel |
| Delay compensation off | No control. `UI.pdc=false` by hand | `UI.pdc` | Shown in the CPU panel |
| Skip muted tracks | No control. Read as `UI.skipMuted!==false`, never written | `UI.skipMuted` | |
| One shared Space reverb | No control. `UI.spaceShared=false` by hand | `UI.spaceShared` | |
| Fixed look-ahead | No control. `UI.laFix` read, never written | `UI.laFix` | |
| `UI.eqAll`, `UI.fxBand` | No control. Read, never written | – | |
| One-time flags | Written once by migrations: `UI.lat2`, `UI.lat3`, `UI.lat4`, `UI.fd22`, `UI.kickUp`, `UI.shrineAdded`, `UI.psyAdded` | – | Not settings; they stay in `audiolab-ui` |

### 3.10 Where things are stored: localStorage, other browser stores, the desktop shell

| Key / file | Holds | Scope |
|---|---|---|
| localStorage `audiolab-ui` | The whole `UI` object: every global option named above, window positions (`UI.win`, `UI.winSized`, `UI.setSize`, `UI.kbw`, `UI.tmGeo`), shortcuts (`UI.keys`, `UI.scPre`), MIDI map (`UI.midiMap`). Saved 250 ms after a change and on page hide. Not written from child (popped-out) windows | Global |
| localStorage `audiolab-projects` | Open project tabs: each project's song `S`, its view (`V`: scroll, zoom, track height), dirty flag, current tab | Per project |
| localStorage `audiolab-saved` | Projects kept aside when the Fractals song opens at start | Per project |
| localStorage `audiolab-v3` | Older single-project save (`KEY`), still read | Per project |
| localStorage `audiolab-boot` | Duration of the last start in ms (length of the splash bar) | Global |
| localStorage `audiolab-app-icon` | Chosen app icon id (browser) | Global |
| localStorage `al-upd-later`, `al-upd-at`, `al-upd-done` | "Later" for one version; time of the last update check; result of the last update | Global |
| localStorage `al-exp-last` | Last export (path, time), removed after use | Global |
| localStorage `al-sess-<id>` | Time Machine session heartbeat | Session |
| sessionStorage `al-coi` | Cross-origin-isolation reload marker | Session |
| IndexedDB `audiolab-files`, `audiolab-tm` | Audio files; Time Machine versions | Per project |
| Cache `audiolab-models` | Downloaded AI voice models | Global |
| Shell: `window-state.json` | Window position, size, maximised, full screen | Global, desktop |
| Shell: `app-icon.json` | Chosen app icon | Global, desktop |
| Shell: `app-update/meta.json` + `index.html` | Downloaded newer program version and its state | Global, desktop |
| Shell: app menu | AudioLab Pro › Check for Updates…; File › Open Project…; View › Toggle Full Screen, Song Overview, **Actual Size / Zoom In / Zoom Out**, Reload, Developer Tools; Help › GitHub, Releases | – |
| Shell: fixed switches | No background throttling, GPU rasterisation, autoplay allowed; power-save blocker while playing. Not user options | – |

Not verified: whether Electron remembers the View › Zoom level between starts.

## 4. Findings

### 4.1 Duplicates: the same thing in two or more places

| Setting | Places | In sync? |
|---|---|---|
| Level meters: speed, reading, peak hold, colours | 3: mixer gear popover; Settings › Interface › Mixer (selects); Settings › Interface › Level meters (cards), the last two right under each other | Yes, all three (tested) |
| Pan control style | 4: gear popover; Settings › Interface › Mixer; the mixer's picture menu; right-click on a pan control | Yes (tested) |
| Fader and meter design | 3: gear popover; Settings; right-click on a fader. A theme in Settings also overwrites it without saying which design it picked | Yes (tested) |
| Compact channels | 3: mixer header button; gear popover; Settings | Yes (tested) |
| Cables | 3: mixer header button; gear popover; Settings | Yes (tested) |
| Keep the master in view | 3: pin on the master strip; gear popover; Settings | Yes (tested) |
| Strip width, the 7 "each channel shows" switches, the 4 "master shows" switches | 2: gear popover; Settings | Yes |
| Mono check, swap left and right | 2: master strip buttons; Settings › Interface and DAC | **No.** Mixer to Settings works. Settings to mixer changes the sound but the master strip buttons keep their old state (tested) |
| Sample rate | 3, all inside Settings: Control Panel; Interface and DAC "Engine sample rate"; Interface mode "Sample rate" | The value is shared; the other copies show it after the tab is clicked again (tested) |
| Buffer size, recording latency offset, keep awake, output device | 2 each, all inside Settings: Control Panel or Audio system, and Interface and DAC | Shared value; the copy refreshes when its tab is opened. Keep awake: Control Panel to the DAC page did not update at once, the other way did (tested) |
| Follow on / off and follow mode | Follow chip and its right-click menu; Settings › Zoom and playhead; the command "Follow the playhead" | **Partly.** The menu has 6 choices, Settings 4. With "Look ahead" or "Push at the edge" chosen, no card is lit in Settings. The command does not refresh an open Settings window (tested) |
| Visualizer on / off and place | 3: the visualizer's header (✕ and a select); right-click on the map or visualizer; Settings › Interface › Layout | The right-click menu refreshes Settings; the header's ✕ and select do not until Settings is reopened (tested) |
| Map on / off | Right-click on the map; Settings › Interface › Layout | Yes |
| Track controls | "Controls" button and track right-click; Settings › Interface › Layout "Customise…" | Yes: one editor with two doors |
| Light mode | 6 doors: Settings › Performance; logo menu; CPU panel; ⌘⇧L; the "Light mode is on" card; automatic | Yes (tested) |
| Loudness target | Master strip "Target"; the loudness pop-up in the transport | Yes when open. Not in Settings (Settings only shows or hides it) |
| Spectrum overlay | Mixer header; gear popover; loudness pop-up; track menu | Yes |
| Save, Save as, Open | Settings › Project file and again on Settings › Export audio; logo menu; tab menu; shortcuts; desktop menu | Actions, nothing to sync |
| "Audio devices" button, "Performance" link | Twice each inside Settings | Actions |
| Interface size | Settings "Aa" slider (`UI.scale`) and the desktop menu View › Zoom In / Out | **Two separate zooms that do not know about each other** |
| Check for updates | Settings › General; desktop app menu | Action |

### 4.2 Near-duplicates and conflicts

- **Blur and Edge light mean two things.** On Performance they are switches (how the blur is made; edge line on or off). On Glass & light they are sliders with the same names (how strong). A user who sets the Blur slider while Blur is "Off" on Performance sees nothing change.
- **Glass level in two tabs.** Performance has the four level buttons; Glass & light has five chips with the same names that only change the preview. They look like the same control but only one does something.
- **Two zoom settings in two tabs.** Settings › Interface › "Zoom and scroll" has presets "AudioLab default / Ableton style / Logic style / FL Studio style" (`UI.zs`). Settings › Zoom and playhead has "Zoom style: Picture / Ableton" (`UI.mapZoom`). Choosing "Ableton style" in one does not set "Ableton" in the other.
- **Three kinds of "the look of another DAW"**: Themes (look), Zoom and scroll presets (keys), Shortcut set (keyboard), plus Layout presets (Ableton-style, Cubase-style). Four places to become "like Ableton", in three tabs.
- **Themes overwrite other settings silently**: fader and meter design and meter colours (tested: "Live style" set design 7 and colours Lime).
- **Steadier playback** (`UI.hq`) and **Buffer size** (`UI.buf`) both set the buffer; "Apply the recommended settings" changes both. Three controls steer one number.
- **Two pop-ups inside Settings**: the Control Panel and the Audio devices window repeat what the two audio tabs show.
- **The gear popover and Settings › Interface › Mixer are almost the same list**: Settings has five more (Channel number, Master strip width, Fader height, Highest peak, Group colour band), the popover has one more (Spectrum overlay). Nobody can tell which one is complete.
- **"Reset all settings"** also resets everything that lives outside Settings (metronome, capture, follow, visualizer, transport layout, track controls); the question it asks does not say so.
- **Default against the decision (fixed in v0.222).** The design decision says the original "Flat bars" (design 7) is the standard again; in v0.221 the default was still 22 "Flat bars 2". Task D1 corrected this in v0.222.

### 4.3 Settings in the wrong tab

| Setting | Where it is | Why it is wrong |
|---|---|---|
| Themes | Interface (between Track controls and Mixer) | It is about colours and look; belongs with Colours & clips and Glass |
| App icon | Colours & clips | Not a colour of the workspace; belongs with General or the look page as its own block |
| Interface size | Interface (first row, no heading) | A look setting; easy to miss above "Zoom and scroll" |
| Zoom and scroll (keys, speed) | Interface | Belongs with "Zoom style" on Zoom and playhead |
| Arrangement grid (brightness, ticks, 4-bar lines) | Colours & clips | Fine as a look setting, but there is no arrangement page that links to it |
| Mixer and Level meters | Interface, at the bottom of a four-screen page | Deserve their own page; the name "Interface" does not suggest them |
| Mono check, swap, balance | Interface and DAC | They are monitoring controls used while mixing; the master strip is their natural home |
| Pick up notes that are already sounding | Audio system › Playback | A playback behaviour, not a driver setting |
| Note cache, Sleeping tracks, Background freeze | Performance, also printed under "Performance" in the old Glass page markup | Audio savers mixed with picture savers under one heading "Savers" |
| Save, Save as, Open | Settings › Project file and Export audio | Actions, not settings; they are already in the menus |
| Save as template… | Settings › Project file only | An action that exists nowhere else |
| Transport bar "Edit…" | Settings › Interface only | The edit mode works on the bar itself; it cannot be started there |
| Install updates automatically | General | Not offered in the Updates window, where the user thinks about it |

Also: the tab "Interface" (`data-tab=layout`) and the tab "Interface and DAC" have nearly the same name for two unrelated things (screen layout, audio hardware).

### 4.4 Unclear names

| Name today | Problem | Suggestion |
|---|---|---|
| "Interface" and "Interface and DAC" | Two meanings of interface | "Layout" and "DAC and audio interface" |
| "Zoom and playhead" | Holds zoom style, follow and the playhead look, but not zoom keys | "Navigation" |
| "Render blocks" | Engine word | "Processing block" with the explanation up front |
| "Steadier playback: bigger buffer for heavy mixing" under "Lossless listening" | It is a buffer setting, not about lossless | Move next to Buffer size, name "Larger playback buffer" |
| "Picture" (mixer), also "view" and "display" | Three words for what a channel shows | One word everywhere: "Display" |
| "Half-size picture behind glass" / "Softer blur while playing" | Describe the trick, not the gain | Fine once the three glass levels replace them (see 4.7) |
| "Background freeze" next to "Freeze when in the background" | Two different things with almost the same name (frozen tracks; app not in front) | "Freeze unchanged tracks" and "Pause the screen when AudioLab is not in front" |
| "Picture" and "Live" for Blur | Not self-explaining | Goes away with the presets of the glass plan |
| "Highest peak" and "Peak hold" | Two peak memories | "Peak number under the fader" and "Peak hold line" |
| "Tidy" (cables) | Unclear until tried | "Straight cables" |
| "Capture" options "Sound buffer keeps" and "keep last N seconds" | Two lengths for one buffer (`UI.retroSec` and `UI.retroLen`) | One setting |
| "Feel", "Ghost" (piano roll) | Short, no explanation in the tip | Tips with one sentence |

### 4.5 Settings nobody can find

Only in a right-click menu, with no visible hint:

- Play button: what the flash follows (Auto, every beat, kick only).
- Capture button: silence gap, look-back time, quantize, where the capture is placed, buffer length (five options; the capture panel shows two others).
- Follow chip: "Look ahead", "Push at the edge, smoothly", "Follow again 3 s after I stop scrolling".
- Mixer: a channel's own picture; the picture's colours and options (two right-clicks deep); "Stereo field behind pan".
- "Show all automation" button: right-click hides all automation. Loop bar: right-click removes the loop.

Only in a place that can disappear:

- Cable kinds, "Selected only" and "Tidy" sit in the legend under the channels, which is hidden when Cables is off.
- The mixer-wide picture is only in the mixer header dropdown.
- The tempo and time signature lane is only in the time signature menu and the section strip menu.
- The transport bar's edit mode starts only from Settings › Interface.
- The master lane's view (Loudness map, Waveform…) is only behind its "View" button (code only).

Not findable by Settings search: metronome, count-in, click, capture, snap, loudness target, piano roll, visualizer view. Search only knows what is inside the Settings window.

Menus that open in the wrong place: a right-click on a send knob, Mute, Solo or Record arm in the mixer opens the "Add effect" list; a right-click anywhere on the empty transport bar (also on Stop, Record, Metronome, the CPU read-out) opens the project tab menu.

### 4.6 Stored in the wrong place, or not at all

| Setting | Today | Better | Why |
|---|---|---|---|
| Export: format, sample rate, bit depth, dither, normalize, tail, range, limiter, folder, MP3 bitrate, FLAC compression | Not stored; defaults after every restart | Global (last used), file name per project | People export the same way every time |
| Piano roll: snap, chord, ghost on / off, lane, tool | Not stored | Global (last used) | A reload brings back 1/16 and Draw; ghost "Off" is forgotten while "Subtle grey" is remembered |
| Piano roll: scale and root | Not stored | **Per project** | The key belongs to the song |
| Loudness target | Global | **Per project**, with a global default | A club master and a podcast need different targets |
| Count-in, click sound, levels | Global | Keep global | Personal taste |
| Click pattern | Global, but its presets are made for the song's time signature | **Per project** (pattern follows the signature) | A 7/8 song needs its own pattern |
| Metronome on / off | Per project | Global | Whether you want a click is about how you work, not the song. Low priority |
| Tempo lane shown | Global | Per project | Only useful in songs with tempo changes |
| Automation lane height, "Collapse all tracks" | Global, while track height and zoom are per project | Per project | They belong to the same view |
| Mixer per-channel picture | Per project | Keep | Correct; say so in the menu |
| Mono check, swap | Global and remembered | Global, but **off at every start** | A remembered Mono makes the next session sound wrong without a sign |
| Mixer Dim | Session | Keep | Correct for a momentary control |
| Seed | Per project | Keep | Correct |
| Also recolour the tracks in this project | Global switch that changes the project | Keep, but ask each time a theme is applied | It changes saved data |
| App icon | Browser key or shell file | Keep | Must be read before the page starts |
| Window sizes and places | Global | Keep | Per screen, not per song |

### 4.7 Dead or obsolete

- **Hidden controls still in the Settings page**: the Refraction slider (`setRefr`, display none), a second Refraction switch (`fxRefr`, display none), the old DAC "Profile" select (`dacSel`, always hidden, three entries, replaced by "Device profile").
- **Old markup that is rebuilt at start**: the static page text still has Light mode and Screen updates under General, "Performance" savers under Glass, and a "DAC and monitoring" block; the running app replaces them. Safe, but anything that reads the static markup (for example a search index built too early) sees the old layout.
- **Glass levels.** The glass engine plan (section 1 and task G4) replaces Full effects / Optimised / Lighter / Lightest with three levels (Glass, Light, Solid; the plan's first names were GL engine, Blur, Solid) and replaces the sliders by presets (lens: Off, Fine, Apple, Wide; blur: Light, Regular, Heavy). That makes these obsolete: the four level buttons, the "What each effect costs" switches (Refraction, Blur Off / Picture / Live, Edge light), the savers "Softer blur while playing" and "Half-size picture behind glass", the Blur slider, the hidden Refraction slider, the five preview chips, and the keys `UI.pm.st` (0 to 3), `UI.fx`, `UI.fxUser`, `UI.blur`, `UI.refr`, `UI.glPlay`, `UI.glBack`, `UI.lite`, `UI.liteMan`. Transparency and Edge light strength can stay as presets or sliders (to be decided in G4). Existing choices must be carried over (Full and Optimised to Glass, Lighter to Light, Lightest to Solid).
- **Note cache** only does something when the pooled voice engine is off (`UI.poly===false`, which has no control), so for almost everyone the switch does nothing.
- **Flags that are read but never written**: `UI.skipMuted`, `UI.laFix`, `UI.eqAll`, `UI.fxBand`. **Flags that can only be set by hand**: `UI.poly`, `UI.pdc`, `UI.spaceShared`.
- **One-time flags that stay in the settings object**: `UI.lat2`, `UI.lat3`, `UI.lat4`, `UI.fd22`, `UI.kickUp`, `UI.shrineAdded`, `UI.psyAdded`.
- **Old menu code**: `mxMenuItems` and the first mixer view menu are replaced by the picture menu; its "Colours and options" entry survives only as a right-click inside the picture menu.
- **Two buffer lengths for capture** (`UI.retroSec` in the right-click menu, `UI.retroLen` in the panel).

### 4.8 Missing settings users would expect

- **Arrangement snap and grid**: no selector at all; the step follows the zoom. Every DAW has a snap menu in the arrangement.
- **Clock display**: the time read-out has one format; no bars, seconds, samples or timecode choice.
- **Metronome in Settings**: nothing, not even a link.
- **MIDI**: no page for MIDI inputs, the keyboard piano, MIDI learn mappings (stored in `UI.midiMap`, no list to see or clear them).
- **Recording**: no defaults (count-in, where takes go, capture options) in one place.
- **Default for new projects**: tempo, time signature, loudness target, track height.
- **Language and date format**: none (English only today; note for later).
- **Default for device parameters shown or hidden** (display-first devices are the decided direction; there is no switch for the default).
- **Undo history length, Time Machine storage**: no setting and no read-out of the space used.
- **Export presets** (for example "Streaming master", "Stems 24-bit").
- **Delay compensation on / off and voice engine**: shown in the CPU panel as a status but cannot be changed anywhere.
- **Back up and restore settings**: no export or import of `audiolab-ui`; a browser clean-up loses every setting and shortcut.
- **Reset per page**: only "Reset all settings" for everything; three blocks have their own Reset (Zoom and scroll, Transport bar, Track controls).
- **Tooltips**: 112 of 339 controls in Settings have none (General 8 of 10, Audio system 17 of 24, Export audio 19 of 25, Colours & clips 6 of 7). Outside Settings: nothing in the Metronome setup, the capture panel or on the loudness target.

## 5. Where each setting should live

Three homes:

- **In place**: changed while working, often, with the result in view. Stays where the hand already is. Not repeated in Settings.
- **Settings**: set once or seldom, or has no natural place on screen.
- **In place + link**: a short list in place for the few things changed often, the full page in Settings, and a link both ways ("More … settings" in place; "Show the mixer" in Settings). The short list and the full page are drawn by the same code, as the mixer already does, so they cannot drift apart.

Two rules that follow from the decided direction (keep today's look; clear, intuitive, snappy):

1. **One home per setting.** A second door is always a link that opens the first, never a second copy of the control.
2. **A right-click menu may repeat, never own.** Anything that today exists only in a right-click menu also gets a visible home.

### 5.1 Mixer

| Setting | Home | Reason |
|---|---|---|
| Compact channels, Cables | In place (header buttons) | Toggled while mixing; the buttons are already there. Remove the copies in the popover |
| Keep the master in view | In place (pin on the master) | The pin is the control; remove the copies |
| Mixer picture (Waveform, Spectrum…) | In place (header dropdown) | A view choice |
| Per-channel picture, picture colours and options | In place: add a visible "Display options" entry in the header dropdown; right-click stays as a shortcut | Today two right-clicks deep |
| Strip width | In place + link | Changed by eye |
| Pan control style | Settings › Mixer and meters; right-click on a pan stays as a shortcut that links there | Set once; four places today |
| Fader and meter design | Settings › Mixer and meters; right-click on a fader links there | Set once; a picture list needs room |
| Each channel shows (9), Master shows (4), Channel number, Master strip width, Fader height | In place + link: popover keeps the 9 + 4 show switches; the three sizes only in Settings | The show switches are tried by eye; sizes are set once |
| Level meters: speed, reading, peak hold, colours | Settings › Mixer and meters, **once** (the card version with the live meter); popover gets one line "Level meters…" that opens it | They apply to every meter in the app, not only the mixer; three copies today |
| Spectrum overlay | In place (header button only) | A window toggle |
| Cable kinds, Selected only, Tidy | In place (legend), and listed in Settings › Mixer and meters so search finds them | The legend is the natural place but hides with the cables |
| Stereo field behind pan | Settings › Mixer and meters | Only in a right-click today |
| Mono, Dim, L↔R, Balance | In place (master strip); remove from Settings, keep a read-out line with a link on the DAC page | Monitoring is done at the master; fixes the sync bug by removing the copy |
| Loudness target | In place (master strip and loudness pop-up), stored per project; default in Settings › Project | Chosen per song |
| Mixer window size and place | In place | Dragging |

### 5.2 Devices panel and piano roll

| Setting | Home | Reason |
|---|---|---|
| Devices panel: show / hide, pop out, height, modulators collapsed, pin, parameters shown | In place | View state |
| Default for new devices: parameters shown or hidden | Settings › Layout | No place today; needed for display-first devices |
| Sleeping tracks, note cache, background freeze | Settings › Performance | Set once |
| Piano roll: tool, snap, chord, ghost, lane, lane height, window mode | In place, remembered | Working controls; they only need to be stored |
| Piano roll: scale and root, scale lock | In place, stored per project | The song's key |
| Piano roll defaults (snap for new clips, ghost look) | Settings › Editing | So search finds "snap" and "ghost" |

### 5.3 Transport

| Setting | Home | Reason |
|---|---|---|
| Tempo, time signature, loop, locators | In place (project) | The song |
| Metronome on / off, count-in on / off | In place (buttons) | Toggled while working |
| Metronome setup (count-in bars, when it clicks, sound, levels, pattern) | In place + link: the setup window stays; Settings › Recording and metronome shows the same rows or a button that opens it; right-click on the metronome button opens the setup | It is a full settings window that Settings does not know about |
| Capture: source and length | In place (capture panel) | Chosen while playing |
| Capture: silence gap, look-back, quantize, placement | In place + link: move into the capture panel under "More"; the same rows on Settings › Recording and metronome | Right-click only today |
| Play button flash source | Settings › Layout › Transport bar | A taste setting nobody finds |
| Keyboard piano: on / off, layout, compact | In place | A tool |
| Clock format (new) | In place: click the clock to change the format | The standard place in every DAW |
| Tempo and time signature lane | In place (menu), per project; add a key or a small button on the ruler | View state of the song |
| Transport bar edit mode, Reset, Shrink on small screens | In place + link: right-click on the bar offers "Edit the transport bar…"; Settings › Layout keeps Edit, Reset and Shrink | Editing happens on the bar |
| Tour button shown | Settings › General | Set once |
| Full screen | In place | A window command |
| Master loudness pop-up | In place | Read-out with its own target select |

### 5.4 Arrangement and visualizer

| Setting | Home | Reason |
|---|---|---|
| Follow on / off | In place (Follow chip) | Toggled all the time |
| Follow mode (all six), "Follow again after 3 s" | In place + link: the chip's menu stays; Settings › Navigation shows **all six** modes and the 3 s switch; menu keeps its link "Playhead look in Settings" | The menu and Settings must offer the same list |
| Playhead look (shape, colour, thickness, time flag) | Settings › Navigation | Set once |
| Zoom keys, speed, anchor, pinch, zoom style | Settings › Navigation, one block | Two blocks in two tabs today |
| Zoom, scroll, track height | In place (per project) | View |
| Automation lane height, collapse all | In place, per project | View |
| Show all / hide all automation, Write automation | In place; make "Hide all" a visible second state of the button | Right-click only today |
| Snap and grid step (new) | In place: a snap select on the arrangement's caption bar; default in Settings › Editing | Missing today |
| Grid look (brightness, ticks, 4-bar lines) | Settings › Appearance | Set once |
| Track controls | In place + link (Controls button; Settings › Layout "Customise…"), as today | Already right |
| Map on / off, map height | In place (right-click, grip) + the switch in Settings › Layout, as today | Already right |
| Visualizer on / off, place | In place (its header); Settings › Layout keeps the two controls as the full list of panels; remove the copy from the map's right-click menu or keep it as a link | Three places today |
| Visualizer view, size | In place | View |
| Master lane view | In place | View |
| Envelope editor "Live" | In place | Tool option |

### 5.5 What is in Settings today

| Setting | Home | Reason |
|---|---|---|
| Tooltips, splash, tour button, ask before closing | Settings › General | Set once |
| Automatic updates | Settings › General, and the same switch in the Updates window | That is where the user decides |
| Output device, buffer, sample rate, processing block, headroom, keep awake | Settings › Audio, on the page itself (no Control Panel pop-up), each **once** | Three copies of sample rate today |
| Recording latency offset, round-trip measurement, input device, input channels, input monitoring | Settings › Recording and metronome | Recording belongs together |
| Mode (DAC / Interface), device profile, bit-perfect, DC blocker, safety ceiling, safety limiter, DAC volume link, output channels | Settings › DAC and audio interface | The hardware page; the limiter moves here from Audio system because it is a protection |
| Larger playback buffer ("Steadier playback") | Settings › Audio, next to Buffer size | One number, one place |
| Pick up sounding notes | Settings › Editing (playback behaviour) | Not a driver setting |
| Test tone | Settings › Audio, or inside the Audio devices window | A tool; fine where it is |
| Interface size, theme, background, tint, clip transparency, grid look, app icon | Settings › Appearance | One page for the look |
| Glass: lens preset, blur preset, transparency, edge light | Settings › Appearance › Glass | The glass plan's presets |
| Glass level (Glass, Light, Solid), frame limit, automatic choice, background behaviour, audio savers | Settings › Performance | One page for speed; the level is set only here, Appearance shows it as a read-out with a link |
| Layout picture, layout presets, panels, transport bar, track controls | Settings › Layout | Today's Interface tab without the mixer and themes |
| Mixer and level meters | Settings › Mixer and meters | Own page, see 5.1 |
| Zoom style, zoom keys, follow, playhead look | Settings › Navigation | See 5.4 |
| Keyboard shortcuts, shortcut set | Settings › Keyboard shortcuts | As today |
| Autosave (on, interval, also to file) | Settings › Project | As today |
| Save, Save as, Open buttons | Remove from Settings (keep one row "Save as template…" until it has a menu entry) | Actions live in menus |
| Export options | In place + link: Settings › Export stays the full page; the logo menu's "Quick export" uses the remembered options; all options are stored | Already linked from the logo menu |
| Reset all settings | Settings footer, plus "Reset this page" on each page | Finer control |

## 6. Proposed pages

Thirteen pages in four groups (today: 11 in two groups), same window, same look, search on top. Two more pages than today, but each is short: no page needs more than about one and a half screens, where Interface needs four today. The names say what is inside.

| Group | Page | Blocks | Comes from |
|---|---|---|---|
| Program | **General** | Help while you work (tooltips, splash, tour button); Closing projects; Updates (check, automatic); About; Back up and restore settings (new) | General |
| Program | **Appearance** | Theme; Interface size; Glass (lens preset, blur preset, transparency, edge light, with the live preview); Background and tint; Clips; Arrangement grid; App icon | Themes block of Interface; Glass & light; Colours & clips |
| Program | **Performance** | Level: Glass, Light, Solid, with Automatic; Frame limit and the live frame graph; Audio savers (sleeping tracks, freeze unchanged tracks); When AudioLab is not in front | Performance (rebuilt in task G4) |
| Program | **Layout** | Window layout picture and presets; Panels (map, visualizer, devices default); Transport bar (edit, reset, shrink, play flash); Track controls | Interface (first half) |
| Program | **Keyboard shortcuts** | Shortcut set; list | Keyboard shortcuts |
| Working | **Navigation** | Zoom (style, keys, speed, anchor, pinch); Following the playhead (six modes, follow again after 3 s); Playhead look | Zoom and playhead; Zoom and scroll block of Interface |
| Working | **Editing** | Snap defaults (arrangement, piano roll); Piano roll (ghost look, scale lock); Playback behaviour (pick up sounding notes); Automation (write mode default) | new; collects what is spread over menus |
| Working | **Mixer and meters** | Channels; Each channel shows; Master shows; Cables; Fader and meter design; Pan control; Level meters (once, with the live meter). Button "Show the mixer" at the top | Mixer and Level meters blocks of Interface |
| Sound | **Audio** | Output device; Buffer (one control, with "Larger playback buffer"); Sample rate; Processing block; Headroom; Keep awake; Status (running at, latency, dropouts); Test tone | Audio system and its Control Panel |
| Sound | **DAC and audio interface** | Mode; Device profile; Bit-perfect and its check list; Protection (DC blocker, ceiling, safety limiter); DAC volume; Output channels. Sample rate and buffer shown as read-outs with a link to Audio | Interface and DAC |
| Sound | **Recording and metronome** | Inputs (device, channels, monitoring); Latency (offset, measure); Count-in and metronome (or a button that opens the Metronome setup); Capture (gap, look-back, quantize, placement, buffer); MIDI (inputs, learned controls with a clear button) | Interface mode blocks of Interface and DAC; metronome and capture menus |
| Project | **Project** | Autosave; This song (loudness target, key, seed, tempo lane); Defaults for new projects; Storage used; Save as template | Project file |
| Project | **Export** | As today, with the options remembered and presets | Export audio |

Order of work, smallest first: (1) remove the copies inside Settings (second Level meters list, the three hidden controls, the doubled file buttons); (2) store the export and piano roll options; (3) fix the Mono and swap repaint and the Follow list; (4) add the links in section 7; (5) regroup the pages; (6) rebuild Performance and Glass with task G4.

## 7. Quick routes

Existing routes to keep: a click on the logo opens Settings; logo menu "Export settings…", "Interface and DAC…", "Settings…"; the Follow menu's "Playhead look in Settings"; the tab menu's "Project file settings…"; the mixer popover's "More mixer settings…"; the pattern box opens the Metronome setup; the "Performance" links inside Settings.

New routes proposed:

| From | Opens |
|---|---|
| Click on the CPU read-out | The performance panel, as today, with two new links at the bottom: "Performance settings…" and "Audio buffer…" |
| Right-click on the CPU read-out | Settings › Performance directly |
| "Light mode is on" card | A third button "Performance…" |
| Click on the latency or engine status read-out | Settings › Audio |
| Right-click on the metronome or count-in button | Metronome setup |
| Right-click on the Capture button | The capture panel with all options (not a separate menu) and a link "Recording settings…" |
| Right-click on any level meter (track, mixer, master, transport) | Menu "Level meters…" that opens Settings › Mixer and meters at the Level meters block |
| Right-click on a fader, right-click on a pan control | Keep the quick lists, add a last entry "More in Settings…" |
| Settings › Mixer and meters | Button "Show the mixer" (the reverse of "More mixer settings…") |
| Right-click on the empty transport bar | "Edit the transport bar…" and "Layout settings…" (instead of the project tab menu) |
| Right-click on the playhead | The Follow menu (same as the chip), with "Playhead look…" |
| Click on the clock | Clock format (new) |
| Click on the loudness read-out | As today, plus "Mixer and meters…" |
| Visualizer header | A small gear with its view, place and "Layout settings…" |
| Update card and Updates window | The "Install updates automatically" switch itself |
| Audio devices window | Link "Audio settings…" back to the page that opened it |
| Settings search | Also finds in-place options (metronome, snap, capture, loudness target) and offers "Show me": it closes Settings and flashes the control, as it already flashes controls inside Settings |
| Export finished message | "Export settings…" |
| Any "Reset" in Settings | Says in one line what it will reset, including in-place options |

Each route opens the page scrolled to the block and flashes it once, as the Settings search does today, so the jump is instant and clear.
