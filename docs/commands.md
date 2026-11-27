# Commands (task XT-DL2, from v0.273)

Every action of AudioLab has one namespaced command id. `runCommand(id)` in index.html is the one door that runs it, for keys,
macros (DL8), toolbars, scripts (DL13) and the Assistant (DL15); docs/extensions-plan.md section 9.6 (c).

- The registry is built over the shortcut list `SCA` (`xtCommands()`: id, name, group, default key, current key, old id).
  `SCA` keeps its old ids as the keys of `UI.keys`, the key presets and `SCM`, so nobody's shortcuts change.
- `XT_CMD_NS` gives each old id its namespaced id; ids that already had one (`ctl.*`, `ni.*`, `clip.*`) are kept.
  `COMMAND_ALIAS` maps every old or retired id to the namespaced one; `xtCommandId(any id)` resolves it.
- **A released command id is never renamed or reused.** Retiring one: keep its row, mark it retired, add `old: new` to `COMMAND_ALIAS`.
- Adding a command: a row in `SCA` (with a namespaced id, or a row in `XT_CMD_NS`), and a row here, or `tools/ui-tests/taskXT_DL2.py` fails.
  Commands with a button but no shortcut row go in `XT_CMD_EXTRA` (they stay out of the Settings shortcut list).
- Gestures (Copy, Shift-drag and the like) are listed so the shortcut page can show them, but `runCommand` refuses them.
- The section is the id's first word. Ids by section; "Old id" is the id in `SCA`, `UI.keys` and the key presets.
- Only in the desktop app: `mg.native` (Install the native AudioLab, task MG1), added there at start; not in this list until it exists in every build.

## Transport

| Id | Command | Default key | Old id | Since |
|---|---|---|---|---|
| `transport.play` | Play / pause | `Space` | `play` | 0.273 |
| `transport.stop` | Stop | `Shift+Space` | `stop` | 0.273 |
| `transport.home` | Go to start | `Home` | `home` | 0.273 |
| `transport.record` | Record | `Shift+R` | `rec` | 0.273 |
| `transport.loop` | Cycle (loop) on / off | `Shift+L` | `loop` | 0.273 |
| `transport.metronome` | Metronome | `C` | `click` | 0.273 |
| `transport.countIn` | Count-in on / off |  |  | 0.273 |
| `transport.tapTempo` | Tap tempo |  |  | 0.273 |
| `transport.capture` | Capture what you just played |  |  | 0.273 |

## Project and files

| Id | Command | Default key | Old id | Since |
|---|---|---|---|---|
| `project.save` | Save project | `Mod+S` | `save` | 0.273 |
| `project.saveAs` | Save as… | `Mod+Shift+S` | `saveas` | 0.273 |
| `project.open` | Open project… | `Mod+O` | `open` | 0.273 |
| `project.new` | New project… | `Mod+Alt+N` | `new` | 0.273 |
| `project.export` | Export… | `Mod+E` | `export` | 0.273 |
| `project.timeMachine` | Time Machine (earlier versions) | `Mod+Shift+H` | `tm` | 0.273 |
| `project.exportMidi` | Export MIDI (selected clip, or the whole song) | `Mod+Shift+E` | `midiexp` | 0.273 |

## Editing

| Id | Command | Default key | Old id | Since |
|---|---|---|---|---|
| `edit.undo` | Undo | `Mod+Z` | `undo` | 0.273 |
| `edit.redo` | Redo | `Mod+Shift+Z` | `redo` | 0.273 |
| `edit.redoAlt` | Redo (second key) | `Mod+Y` | `redo2` | 0.273 |
| `edit.delete` | Delete selection (gesture) | `Delete` | `del` | 0.273 |
| `edit.copy` | Copy (gesture) | `Mod+C` | `copy` | 0.273 |
| `edit.cut` | Cut (gesture) | `Mod+X` | `cut` | 0.273 |
| `edit.paste` | Paste (also between projects) (gesture) | `Mod+V` | `paste` | 0.273 |

## Clips

| Id | Command | Default key | Old id | Since |
|---|---|---|---|---|
| `clip.linkedDup` | Duplicate as linked copy |  |  | 0.273 |
| `clip.unique` | Make unique (break the link) |  |  | 0.273 |
| `clip.duplicate` | Duplicate clip | `Mod+D` | `dup` | 0.273 |
| `clip.split` | Split clip at the playhead | `Shift+S` | `split` | 0.273 |
| `clip.dragCopy` | Duplicate clips: start dragging with Shift held (gesture) | `Shift+Drag` | `ajdup` | 0.273 |
| `clip.nudge` | Move selected clips in time (the step follows the zoom) (gesture) | `ArrowLeft+ArrowRight` | `ajnudge` | 0.273 |
| `clip.moveToTrack` | Move selected clips to the track above or below (gesture) | `ArrowUp+ArrowDown` | `ajtrack` | 0.273 |
| `clip.marquee` | Select clips with a rectangle (every clip it touches, also partly; Shift adds) (gesture) | `Right-click+Drag` | `akmarq` | 0.273 |
| `clip.dropToAudio` | Drop, copy or paste a MIDI clip on an audio track: it is bounced to audio (gesture) | `Drag` | `akbounce` | 0.273 |
| `clip.nudgeBig` | Move clips by a bigger step (4 times) (gesture) | `Shift+ArrowLeft+ArrowRight` | `ajbig` | 0.273 |
| `clip.nudgeFine` | Move clips by the finest step (1/64 note) (gesture) | `Alt+ArrowLeft+ArrowRight` | `ajfine` | 0.273 |
| `clip.quantize16` | Quantize the selected clip (1/16) |  | `quant` | 0.273 |
| `clip.mute` | Mute / unmute the selected clip |  | `clipmute` | 0.273 |
| `clip.rename` | Rename the selected clip |  | `rename` | 0.273 |

## Arrangement

| Id | Command | Default key | Old id | Since |
|---|---|---|---|---|
| `arr.secDup` | Duplicate the section at the playhead |  |  | 0.273 |
| `arr.insertBars` | Insert empty bars at the playhead… |  |  | 0.273 |
| `arr.secDelete` | Delete the section at the playhead and close the gap |  |  | 0.273 |

## Windows and view

| Id | Command | Default key | Old id | Since |
|---|---|---|---|---|
| `view.mixer` | Mixer window | `Shift+M` | `mixer` | 0.273 |
| `view.devices` | Show / hide devices | `Shift+D` | `devs` | 0.273 |
| `view.lightMode` | Light mode on / off | `Mod+Shift+L` | `lite` | 0.273 |
| `view.settings` | Settings | `Mod+,` | `settings` | 0.273 |
| `view.instrumentBrowser` | Instrument browser |  | `browser` | 0.273 |
| `view.effectsBrowser` | Effects browser (selected track) |  | `fxbrowser` | 0.273 |
| `view.pianoRoll` | Open the selected clip in the piano roll |  | `pianoroll` | 0.273 |
| `view.keyboard` | Keyboard piano on / off |  | `kbd` | 0.273 |
| `view.follow` | Follow the playhead |  | `follow` | 0.273 |
| `view.zoomIn` | Zoom in |  | `zoomin` | 0.273 |
| `view.zoomOut` | Zoom out |  | `zoomout` | 0.273 |
| `view.overview` | Song overview on / off | `Shift+O` | `overview` | 0.273 |
| `view.automation` | Show automation lanes |  | `aut` | 0.273 |
| `view.closeWindows` | Close all floating windows |  | `closewins` | 0.273 |

## Help and tools

| Id | Command | Default key | Old id | Since |
|---|---|---|---|---|
| `help.shortcuts` | Keyboard shortcuts | `Mod+/` | `keys` | 0.273 |
| `help.assistant` | Assistant | `Mod+K` | `ai` | 0.273 |
| `help.tour` | Guided tour | `F1` | `tour` | 0.273 |

## Controllers

| Id | Command | Default key | Old id | Since |
|---|---|---|---|---|
| `ctl.learn` | MIDI learn | `Mod+L` |  | 0.273 |
| `ctl.mappings` | Controllers and MIDI mappings |  |  | 0.273 |
| `ctl.stopAll` | Stop all controllers (MIDI control off) |  |  | 0.273 |

## Tracks

| Id | Command | Default key | Old id | Since |
|---|---|---|---|---|
| `track.newAudio` | New audio track | `Mod+Shift+A` | `newaudio` | 0.273 |
| `track.newInstrument` | New instrument track | `Mod+Shift+I` | `newmidi` | 0.273 |
| `track.mute` | Mute the selected track |  | `mute` | 0.273 |
| `track.solo` | Solo the selected track |  | `solo` | 0.273 |
| `track.group` | Group the selected tracks | `Mod+G` | `group` | 0.273 |
| `track.ungroup` | Ungroup | `Mod+Shift+G` | `ungroup` | 0.273 |

## Ideas

| Id | Command | Default key | Old id | Since |
|---|---|---|---|---|
| `ni.clipExplain` | Why is this clipping? (explain the last clip) |  |  | 0.273 |
| `ni.freqMap` | Frequency map of the whole song |  |  | 0.273 |
| `ni.clashes` | Show clashes between tracks in the mixer |  |  | 0.273 |
| `ni.kickBass` | Kick and bass lab (is the kick in tune with the bass?) |  |  | 0.273 |
| `ni.energyArc` | Energy arc on / off (loudness, tracks playing and brightness over the song) |  |  | 0.273 |
