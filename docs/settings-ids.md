# Settings ids (task XT-DL3, from v0.295)

Every setting of AudioLab has one stable id, shown in the Workshop's settings list (`xtWsOpen`, logo menu > Workshop…) and used by the settings file (DL9), scripts (DL13) and the Assistant (DL15); docs/extensions-plan.md section 9.6 (a).

- Rows of the Settings window come from the settings table `STT` (task ST-S4). `XT_SET_NS` in index.html names each once, as page.id at the time it was named; a row that later moves to another page keeps its id.
- **A released id is never renamed or reused.** A retired setting keeps its row here, marked retired.
- A new `STT` row needs a row in `XT_SET_NS` and here, or `tools/ui-tests/taskXT_DL3.py` fails (until then it shows as `settings.<id>`).
- Values with no control in Settings live in `XT_SET_OWN`: kind `none` (no control anywhere), `else` (set by a menu or a drag elsewhere), `lock` (shown read-only, nothing can change them). A value with no key of its own is kept in `UI.xtSet`, differences only.

## From the Settings window

| Id | Setting | Table row | Since |
|---|---|---|---|
| `general.tips` | Show tooltips | `tips` | 0.295 |
| `general.splash` | Splash screen at start | `splash` | 0.295 |
| `general.tourBtn` | Guided tour button in the top bar | `tourBtn` | 0.295 |
| `general.askClose` | Ask before closing with unsaved changes | `askClose` | 0.295 |
| `audio.outDev` | Output device | `outDev` | 0.295 |
| `audio.buffer` | Buffer size | `buffer` | 0.295 |
| `audio.renderBlocks` | Render blocks | `renderBlocks` | 0.295 |
| `audio.rate` | Sample rate | `rate` | 0.295 |
| `audio.headroom` | Internal headroom | `headroom` | 0.295 |
| `audio.recOffset` | Recording latency offset | `recOffset` | 0.295 |
| `audio.keepAwake` | Keep the audio engine awake | `keepAwake` | 0.295 |
| `editing.chase` | Pick up notes that are already sounding | `chase` | 0.295 |
| `dac.limiter` | Safety limiter on the master | `limiter` | 0.295 |
| `audio.ttFreq` | Test tone frequency | `ttFreq` | 0.295 |
| `audio.ttVol` | Test tone volume | `ttVol` | 0.295 |
| `audio.ttKind` | Test tone kind | `ttKind` | 0.295 |
| `dac.ifMode` | Automatic, DAC mode or Interface mode | `ifMode` | 0.295 |
| `dac.devProfile` | Device profile | `devProfile` | 0.295 |
| `dac.bitPerfect` | Bit-perfect mode | `bitPerfect` | 0.295 |
| `dac.rateFollow` | Switch the DAC to the engine rate (desktop) | `rateFollow` | 0.295 |
| `dac.dcBlock` | DC blocker | `dcBlock` | 0.295 |
| `dac.ceiling` | Headphone safety ceiling | `ceiling` | 0.295 |
| `dac.steady` | Steadier playback | `steady` | 0.295 |
| `dac.inDev` | Record from | `inDev` | 0.295 |
| `dac.inCh` | Input channels | `inCh` | 0.295 |
| `dac.inMon` | Input monitoring | `inMon` | 0.295 |
| `dac.outPair` | Output channels | `outPair` | 0.295 |
| `dac.balance` | Balance | `balance` | 0.295 |
| `dac.mono` | Mono check | `mono` | 0.295 |
| `dac.swap` | Swap left and right | `swap` | 0.295 |
| `appearance.scale` | Interface size | `scale` | 0.295 |
| `navigation.zsPreset` | Zoom and scroll keys style | `zsPreset` | 0.295 |
| `navigation.zsSpeed` | Zoom speed | `zsSpeed` | 0.295 |
| `navigation.zsAnchor` | Zoom around | `zsAnchor` | 0.295 |
| `navigation.zsInv` | Invert zoom direction | `zsInv` | 0.295 |
| `navigation.zsPinch` | Trackpad pinch zooms | `zsPinch` | 0.295 |
| `layout.layout` | Window layout | `layout` | 0.295 |
| `layout.map` | Show the map | `map` | 0.295 |
| `layout.viz` | Show the visualizer | `viz` | 0.295 |
| `layout.vizDock` | Where the visualizer sits | `vizDock` | 0.295 |
| `layout.trShrink` | Shrink the transport bar on small screens | `trShrink` | 0.295 |
| `appearance.dawLook` | Theme: the look of another DAW | `dawLook` | 0.295 |
| `appearance.dawRecol` | Also recolour the tracks | `dawRecol` | 0.295 |
| `mixer.mixer` | Mixer options | `mixer` | 0.295 |
| `mixer.meters` | Level meters | `meters` | 0.295 |
| `appearance.glassTrans` | Glass transparency | `glassTrans` | 0.295 |
| `appearance.glassEdge` | Edge light | `glassEdge` | 0.295 |
| `appearance.bg` | Background brightness | `bg` | 0.295 |
| `appearance.tintHue` | Background tint | `tintHue` | 0.295 |
| `appearance.tintAmt` | Tint amount | `tintAmt` | 0.295 |
| `appearance.clipA` | Clip transparency | `clipA` | 0.295 |
| `appearance.grid` | Arrangement grid brightness | `grid` | 0.295 |
| `appearance.subTicks` | Thin ticks between beats | `subTicks` | 0.295 |
| `appearance.bars4` | Stronger lines every 4 bars | `bars4` | 0.295 |
| `project.autosave` | Autosave | `autosave` | 0.295 |
| `project.asMin` | Autosave every | `asMin` | 0.295 |
| `project.asFile` | Autosave into the .audiolab file | `asFile` | 0.295 |
| `export.exName` | Export file name | `exName` | 0.295 |
| `export.exFmt` | Export format | `exFmt` | 0.295 |
| `export.exSr` | Export sample rate | `exSr` | 0.295 |
| `export.exBit` | Export bit depth | `exBit` | 0.295 |
| `export.exKbps` | MP3 bitrate | `exKbps` | 0.295 |
| `export.exFlac` | FLAC compression | `exFlac` | 0.295 |
| `export.exDither` | Dither | `exDither` | 0.295 |
| `export.exNorm` | Normalize | `exNorm` | 0.295 |
| `export.exRange` | Export range | `exRange` | 0.295 |
| `export.exTail` | Export tail | `exTail` | 0.295 |
| `export.exSeedOn` | Fixed seed | `exSeedOn` | 0.295 |
| `export.exSeed` | Seed number | `exSeed` | 0.295 |
| `export.exFast` | Fast render | `exFast` | 0.295 |
| `export.exLim` | Safety limiter on the export | `exLim` | 0.295 |
| `export.exFolder` | Pick a folder first | `exFolder` | 0.295 |
| `keys.scSet` | Shortcut set | `scSet` | 0.295 |
| `keys.keys` | Keyboard shortcuts | `keys` | 0.295 |
| `navigation.zoomStyle` | Zoom style | `zoomStyle` | 0.295 |
| `navigation.follow` | Follow the playhead | `follow` | 0.295 |
| `navigation.followResume` | Follow again 3 s after scrolling | `followResume` | 0.295 |
| `navigation.phShape` | Playhead shape | `phShape` | 0.295 |
| `navigation.phColour` | Playhead colour | `phColour` | 0.295 |
| `navigation.phWidth` | Playhead thickness | `phWidth` | 0.295 |
| `navigation.phTime` | Show the time above the playhead | `phTime` | 0.295 |
| `performance.lite` | Light mode | `lite` | 0.295 |
| `performance.fpsCap` | Frame limit | `fpsCap` | 0.295 |
| `performance.fpsHud` | Frame-rate read-out on screen | `fpsHud` | 0.295 |
| `performance.noteCache` | Note cache | `noteCache` | 0.295 |
| `performance.fxSleep` | Sleeping tracks | `fxSleep` | 0.295 |
| `performance.bgFreeze` | Background freeze | `bgFreeze` | 0.295 |
| `performance.aoFreeze` | Freeze when in the background | `aoFreeze` | 0.295 |
| `performance.aoVisuals` | Keep visuals in the background | `aoVisuals` | 0.295 |
| `appearance.density` | Density | `density` | 0.295 |
| `appearance.motion` | Motion | `motion` | 0.295 |
| `appearance.caliper` | Caliper while dragging | `caliper` | 0.295 |
| `project.songLufs` | Loudness target of this song | `songLufs` | 0.295 |
| `project.songRoot` | Key of this song: root | `songRoot` | 0.295 |
| `project.songScale` | Key of this song: scale | `songScale` | 0.295 |
| `project.songLane` | Show the tempo and time signature lane | `songLane` | 0.295 |
| `project.songHiFi` | Hi-Fi for this song (lane N, task SQ1, named in SQ3) | `songHiFi` | 0.310 |
| `project.newBpm` | Tempo for new projects | `newBpm` | 0.295 |
| `project.newLufs` | Loudness target for new projects | `newLufs` | 0.295 |
| `project.newLane` | Show the tempo lane in new projects | `newLane` | 0.295 |
| `appearance.scOn` | Science drawings | `scOn` | 0.295 |
| `audio.playBuf` | Playing buffer | `playBuf` | 0.295 |
| `audio.outCheck` | Check the output device | `outCheck` | 0.295 |

## Not in the Settings window

| Id | Setting | Kind | Since |
|---|---|---|---|
| `edit.undoSteps` | How many steps Undo keeps | none | 0.295 |
| `performance.frozenMemoryMB` | Memory for frozen tracks | none | 0.295 |
| `workshop.consoleLines` | Commands kept in the run log | none | 0.295 |
| `capture.phraseGapS` | Capture: a phrase ends after a silence of | else | 0.295 |
| `capture.maxMinutes` | Capture: longest phrase kept | else | 0.295 |
| `metronome.countInBars` | Count-in length | else | 0.295 |
| `arrange.mapHeight` | Height of the Map | else | 0.295 |
| `pianoRoll.velocityHeight` | Height of the velocity lane in the piano roll | else | 0.295 |
| `scripts.timeLimitMs` | Time a script may run before you are asked to wait or stop it | lock | 0.295 |
| `scripts.maxLogLines` | Lines a script may print in one run | lock | 0.295 |
| `scripts.maxChanges` | Changes a script may ask for in one run | lock | 0.295 |
| `scripts.maxCodeKB` | Largest script that can run | lock | 0.295 |
