# AudioLab Pro: building the picked features (task FT, lane C)

Plan written in step FT-0, 27 November 2026, from v0.229. One step per run; each run does the first step in the table below that is not marked done, and marks it here with its version.

**The user's picks (27 Nov):** `RF1 picks: F1 F2 F3 ... F40` (all forty cards of "AudioLab: features you might be missing", `docs/research-features-gap.md`), plus: "Let's also add MIDI controller support, I have an Ableton Push I want to link and set up in AudioLab, and also support for other MIDI controllers." The Push is a **Push 1** (made by Akai for Ableton: plain class-compliant MIDI over USB, 8x8 velocity pads, encoders, buttons, a touch strip and a 4-line character display written by SysEx; no colour screen).

## 1. Rules every step keeps

- **Lanes.** Three index.html tasks run at once: lane A (main window, glass, devices: AB2, GS4, MD1, SC, DV), lane B (Settings window and audio devices: ST), lane C (this plan). Edits are small Python scripts with unique asserted anchors, kept in `tools/feature-lab/ft/`, so a rebase re-runs them on the fresh file. `git pull --rebase` before every commit and push; VERSION is the highest on main + 0.001 at push time, re-checked after a rebase; UI tests run again after a rebase.
- **Where things go.** New actions become entries in `SCA` (the shortcut list that task DL2 grows into the commands registry, `docs/extensions-plan.md` 9.6 c) with ids that already carry a namespace (`ctl.learn`, `ctl.mappings`, `arr.sectionMove`...), so DL2 only has to adopt them. New settings get one row each in the shape of the settings table of step S4 (`docs/settings-round-1.md`: id, label, page, block, scope, default, help line, search words). Where a page of the new Settings window (lane B) is needed and not there yet, the feature ships its own small window or popover, drawn by one function, and leaves a named hook (`FT_HOOKS.<name>`) that lane B can call to show the same thing inside Settings. Each hook is listed in the step's log entry.
- **Nothing breaks.** Old projects load: new project fields are optional, live under one versioned key per feature (`proj.ctl = {v:1,...}`, `clip.link`, `clip.steps`...) and are ignored when missing. Every existing feature works as before. The audio path of existing devices does not change (exports bit-identical; the Fractals levels Kick -19.05560 dB and Bass -35.48685 dB checked in every run) unless the card is about sound, and then only the new part.
- **Look and feel.** Today's look, Inter 11/12/13/15, glass from the engine (no `backdrop-filter`), dark and Light, tooltips on every new control, plain language, no em dashes in UI text. Snappy: nothing runs per frame while idle; MIDI input is event driven; controller feedback is sent only on change and at most 30 times a second per device.
- **Tests.** `tools/ui-tests/taskFT_<step>.py` headless, screenshots of anything visible looked at, the existing UI tests pass, no console errors. Controller steps use a **fake MIDI device** in the harness (a stub of `navigator.requestMIDIAccess` with SysEx, injected before the page loads) that sends Push 1 or other controller messages and records what AudioLab sends back.
- **What only the user can test** (the real Push 1, real keyboards, real ears) is written plainly in the log and the notification, with what to try.

## 2. What exists today (v0.229, read for this plan)

- `initMidi()` asks for Web MIDI **without SysEx**, hooks every input the same way: CC to `ccLive` and `midiCC`, pitch bend to `ccLive('pb')`, notes to `noteOn(note-24)` on the selected track. There is no output, no per-device handling, and a Push would today play its pads as raw notes and ignore its display.
- MIDI learn (`midiLearn`, Mod+L, menu entry, `SCA` id `learn`): `UI.midiMap` maps `"channel:cc"` to a control id (`data-c`), global only, absolute 0 to 127 jump, no list (settings audit 4.8), not in pinned windows (task M).
- The desktop shell already allows `midi` and `midiSysex` (`desktop/main.js`), so C1 needs no desktop change; the browser asks the user once.
- Scales and roots exist (`SCALES`, piano roll scale lock), sections exist (name, colour, range), the drum kit has 16 pads, tracks have colours, the transport has tempo, metronome, undo.
- There are **no clips to launch**: no session view (F8 not built). Push's session mode therefore starts with sections as scenes (C2c) and gets clip slots after F8 (C2d).
- The project file has `formatVersion:1`, which is written but never read (research RN3); every new field is optional so this stays true.

## 3. Push 1: what the plan relies on

To be checked line by line in FT-C2a against the sources below; the test's fake Push sends exactly these messages.

- **Ports.** Push 1 shows two MIDI ports, "Live Port" and "User Port" (names differ a little per system: "Ableton Push", "MIDIIN2 (Ableton Push)"). AudioLab drives the Live port and leaves User mode to the user.
- **Pads.** 64 pads send note on and off with velocity on notes 36 to 99 (36 bottom left, rows of 8) and polyphonic aftertouch. A pad's LED is set by sending a note on to the same note, the velocity picking a colour from Push's fixed palette (no free RGB).
- **Encoders.** The 8 track encoders send relative CC 71 to 78 (1 to 63 one way, 65 to 127 the other); the tempo encoder CC 14, swing CC 15, master CC 79; touching an encoder sends notes 0 to 10.
- **Buttons.** Every button is a CC with value 127 pressed and 0 released; its LED is set by sending that CC back (off, dim, full, blink values).
- **Touch strip.** Sends pitch bend; touching sends note 12. Its LEDs can be set by SysEx.
- **Display.** 4 lines of 68 characters, each written by `F0 47 7F 15 <18..1B> 00 45 00 <68 ASCII bytes> F7`, cleared by `F0 47 7F 15 <1C..1F> 00 00 F7`. The display has its own characters for bars and arrows above 127 in the ASCII range used by Live.

Sources (to cite in the C2 log):
- Ableton, Using Push 1 (Live 12 manual): https://www.ableton.com/en/manual/using-push-1/
- Ableton help, Push User Mode for custom MIDI mappings: https://help.ableton.com/hc/en-us/articles/209071249
- Cycling '74 forum, How to control the Push LCD with sysex messages: https://cycling74.com/forums/how-to-control-the-push-lcd-with-sysex-messages/
- DrivenByMoss, Push 1 and 2 support for Bitwig (open source): https://github.com/git-moss/DrivenByMoss-Documentation/blob/master/Ableton/Ableton-Push.md
- Live MIDI remote scripts sources (Push folder), as discussed on the Ableton forum: https://forum.ableton.com/viewtopic.php?p=1670104 and the unofficial documentation thread https://forum.ableton.com/viewtopic.php?p=1837228
- Push 1 hobby projects with the full map: https://github.com/Carlborg/hardpush, https://github.com/zazze/teensy_and_push1
- Novation, Launchpad Mini default MIDI mappings (for C3c): https://userguides.novationmusic.com/hc/en-gb/articles/23731330800146-Launchpad-Mini-s-default-MIDI-mappings

## 4. The steps

Status column: open, **done vX.XXX**, or gated (waits for something outside lane C). Split parts (a, b, c) are separate runs.

### Group 0: the plan
| Step | What | Status |
|---|---|---|
| FT-0 | This plan | **done** (docs only, no version) |

### Group C: controllers (F38 extended)
| Step | What | Status |
|---|---|---|
| FT-C1a | **Controller layer.** One MIDI service: Web MIDI with SysEx (falls back to no SysEx when refused), device detection and hot plug, a device list with a known-profile match by port name, a router so each device's messages go to its profile (generic devices keep today's behaviour: notes play the selected track, CC go to mappings). Mapping model `{id, dev, type cc/note/pb, ch, num, target control id, min, max, takeover pickup/scale/jump, scope project/global}`; project mappings in `proj.ctl` (v1), global in `UI.ctl`; today's `UI.midiMap` read once and turned into global mappings (kept so an older build still works). Takeover modes; relative encoders (two's complement, sign bit, offset 64); MIDI feedback (control value sent back to the CC on change, throttled). Learn reaches pinned device windows too. Commands `ctl.learn` (old `learn` id kept as alias), `ctl.mappings`. Test with a fake generic controller. | **done v0.233** |
| FT-C1b | **Mappings page.** A window from the MIDI learn menu entry and `ctl.mappings`: every mapping in a list (device, control on the controller, what it moves, range, takeover, scope), learn from the list, edit, delete, move between project and global, filter by device, a "last message" read-out; the connected devices with their profile and a switch per device. Drawn by one function with hook `FT_HOOKS.controllersPage` for lane B's Settings. | **done v0.235** |
| FT-C2a | **Push 1, part 1: connect, display, pads.** Profile for Push 1 (Live port): hello and goodbye (display cleared, LEDs off when AudioLab quits or the page hides), the 4-line display driver (only changed lines sent), pads as a note grid with scale and root (in-key and chromatic layouts, fourths or thirds), octave up and down, pad colours from the track colour (nearest of Push's palette; root and in-key shades), velocity curves (linear, soft, hard, fixed), aftertouch off or channel or poly, the touch strip as pitch bend or modulation. Checks every message of section 3 against the sources. | **done v0.238** |
| FT-C2b | **Push 1, part 2: control.** The 8 encoders on the selected device's first 8 parameters, banks with the arrows, names and values on the display; track select (upper row) and arm or mute or solo (lower row), track names on the display; transport (play, record, loop), tempo and swing encoders, master encoder on the master level, metronome, undo and redo, new, duplicate, delete, quantize where AudioLab has the action; drum-rack 4x4 mode on the drum kit's 16 pads (and on any instrument with pads) with the other pads as a 16-step lane of the selected pad. | **done v0.242** |
| FT-C2c | **Push 1, part 3: sections as scenes.** Session-like mode: the scene buttons launch sections (jump at the next bar, or queued like a scene), pads show sections per track as "has notes here"; Push's user mode left alone. Clip launching waits for F8 (step FT-C2d). | **done v0.244** |
| FT-C3a | **Generic controllers.** Templates for class-compliant keyboards and pad controllers (Akai MPK, Arturia KeyLab and MiniLab, Novation Launchkey, Native Instruments Komplete Kontrol in MIDI mode, generic 8 knobs and 8 faders): knobs to the selected device's parameters, faders to track levels, pads to the drum kit, transport buttons; a template is a mapping set the user can edit and save as their own. | **done v0.247** |
| FT-C3b | **Mackie Control and HUI.** Faders (14-bit pitch bend per channel) with motor feedback, V-pots, mute, solo, arm, select, banks of 8, transport, jog, the 2x56 display and the time code display. | **done v0.248** |
| FT-C3c | **Launchpad and APC.** Novation Launchpad (Mini MK3, X, Pro MK3) in programmer mode and Akai APC40 MK2 and APC mini: grid to sections now and clips after F8, colours, faders on the APCs. | | **done v0.253** |

### Group S: the starred cards (section 4 order of the research)
| Step | What | Status |
|---|---|---|
| FT-F1 | Linked clips: chain mark, edits change every copy, Make unique, Alt-Shift-drag makes a linked copy, MIDI clips then audio clip settings, the demo's repeated clips linked; one undo step; small file. | | **done v0.255** |
| FT-F2 | Arranger moves: drag a section with its clips, automation, tempo and signature changes; Alt copies; insert empty bars; delete and close the gap; one undo step; bit-identical to the same edit by hand. | **done v0.268** |
| FT-F9a | Step sequencer clips, part 1: clip type with 16, 32 or 64 steps over drum pads or notes of the key; level, accent, slide, chance and ratchet per step; editor. | in progress (claimed 27 Nov 19:50 UTC, lane C run) |
| FT-F9b | Step sequencer clips, part 2: the Roll preset (KBBB for Psy Bass, first hit lower), convert to and from a normal MIDI clip, slide plays legato into Acid and Psy Bass; same render as the equal notes. Push's step lane (C2b) gets these clips. | open |
| FT-F16a | Volume shaper, part 1: the effect with a drawable curve per 1/4, 1/2 or 1 bar, tempo triggered, drawn live behind the waveform, presets. | open |
| FT-F16b | Volume shaper, part 2: triggered by notes of another track or by audio, up to three bands. | open |
| FT-F18a | Kick and bass lab, part 1: the view on a pair of tracks: kick fundamental as a note, bass key, overlap in time, low-band correlation. | open |
| FT-F18b | Kick and bass lab, part 2: the bass phase-rotation knob and the one-click suggestions (tune kick, shorten tail, rotate). | open |
| FT-F20 | Build designer: range of 8, 16 or 32 bars, one Build control writes normal automation (high-pass, reverb send, noise riser, snare roll density, pitch rise, bass filter), four shapes. | open |
| FT-F25a | Reference A/B, part 1: panel with up to eight references, loudness matched within 0.2 LU, one key flips at the same position or the reference's cue, no click. | open |
| FT-F25b | Reference A/B, part 2: spectra overlaid; listening modes mono, side, sub only, small speaker (the "club check" row). | open |
| FT-F31a | Sample browser, part 1: folders (desktop reads them, the browser uses the folder picker), index without blocking the page, search, tags, favourites, colours, drag to a track or pad. | open |
| FT-F31b | Sample browser, part 2: one-time analysis (tempo, key, length, kind), preview in the song's tempo and key under 50 ms. | open |
| FT-F36 | Plug-ins in AudioLab: the AudioLab side only (a Plug-in device that keeps its state in the project and talks to the native host through the bridge when it is there; "needs the desktop app on a Mac" otherwise). The hosting itself is the native track (`docs/native-mac-plan.md`). | gated on native N2c and the host step |

### Group A: automation and arrangement editing
| Step | What | Status |
|---|---|---|
| FT-F3 | Automation curve shapes per segment in the track lanes (the clip envelope editor's shapes). | open |
| FT-F4 | Automation clips you can loop, cut and stretch. | open |
| FT-F21 | FX throws: a momentary send that writes automation (works from Push's buttons too). | open |
| FT-F5 | Arrangement snap and grid menu (setting row for lane B's Navigation page, hook). | open |
| FT-F6 | Crossfades between audio clips and glue clips into one. | open |

### Group K: key, notes and generators
| Step | What | Status |
|---|---|---|
| FT-F11 | Project key that the piano roll, Push's pads, Chord, Arpeggiator and generators follow (in the project; hook for lane B's Project page). | open |
| FT-F10 | Note chance, ratchets and conditions per note. | open |
| FT-F13 | MIDI file import (drop or Import: tracks, tempo, signature). | open |
| FT-F15 | Generators: Euclidean, seeded melodies, rhythm transforms. | open |
| FT-F12 | Chord track and progression tool. | open |
| FT-F14a/b | Per-note slides and MPE: a, per-note pitch and pressure in clips and the piano roll; b, MPE input and the instruments that follow it. | open |

### Group T: sound tools
| Step | What | Status |
|---|---|---|
| FT-F17 | Multi-shaper: filter, pan, width and crush curves per bar (the F16 curve editor). | open |
| FT-F19 | Step FX: stutter, reverse, gate, crush by step. | open |
| FT-F23 | Slice audio to pads or the Sampler. | open |
| FT-F24 | Multisample zones and round robin in the Sampler. | open |
| FT-F22a/b | Spectral editing: a, the view and selection; b, the edits and render. | open |

### Group M: mix and master
| Step | What | Status |
|---|---|---|
| FT-F26 | Export normalised to LUFS and true peak, export presets (hook for lane B's Export page). | open |
| FT-F29 | Mix snapshots to flip between. | open |
| FT-F30 | Phrase markers (8/16/32 bars) and the DJ check of intro and outro. | open |
| FT-F27 | VCA faders. | open |
| FT-F28a/b | Mastering page: a, the album sequence with gaps and fades; b, the export (DDP if feasible in the browser, otherwise a cue sheet with the WAV). | open |

### Group W: workflow
| Step | What | Status |
|---|---|---|
| FT-F33a/b | Racks: a, parallel chains in one device slot; b, rack macros and saving a rack as a preset. | open |
| FT-F32a/b | DAWproject: a, export; b, import. | open |
| FT-F34 | Genre starter projects (145 BPM full-on, 138 progressive, DJ intro). | open |

### Group E: engine and hardware
| Step | What | Status |
|---|---|---|
| FT-F37 | CPU per track and per device. | open |
| FT-F39a/b | a, MIDI clock in and out and MIDI time code (on the controller layer); b, OSC in the desktop app and Ableton Link (Link needs a desktop helper; if not cheap, logged as left). | open |
| FT-F40 | Multicore audio: tracks on several audio worklets where the browser allows, or handed to the native track; measured first, then done or logged as native only. | open |

### Group L: the big ones last
| Step | What | Status |
|---|---|---|
| FT-F8a/b/c | Clip launcher: a, clip slots and scenes beside the arrangement; b, launching with quantise and follow actions; c, recording the session into the arrangement. | open |
| FT-C2d | Push 1 session mode with clip slots (after F8), and the Launchpad and APC grids moved to clips. | after F8 |
| FT-F7a/b | Take lanes, loop recording and comping. | open |
| FT-F35a/b | Collaboration: a, a project bundle to send (audio included) with notes per bar; b, live sharing if a service fits the private-source rule, otherwise logged as left. | open |

**Count:** 40 cards (F38 is the C group) in 64 runs: 1 plan, 9 controller runs (C1a to C3c and C2d), 54 runs for the other 39 cards counted with their parts. When every row is done the log says "features complete".

## 5. Order and why

Controllers first, as asked (the user has a Push 1 waiting). Then the nine starred cards in the order of the research's section 4. Then groups that share code and value: automation (F3, F4, F21 build on the same lanes, and the Build designer F20 already writes them), key and notes (F11 first, because Push's pads, generators and chords follow the project key), sound tools (F17 reuses F16's curve editor), mix and master, workflow, engine and hardware, and the large cards that need several runs last (F8 clip launcher, F7 comping, F35 collaboration). Inside each group the more valuable card (column Value of the gap table) comes first.

## 6. Hooks left for other lanes (filled in as steps run)

| Hook | For | Left in step |
|---|---|---|
| `FT_HOOKS.controllersPage(host)` draws the Controllers page (devices and every mapping) into any element; `FT_HOOKS.controllersPaint()` redraws it; `FT_HOOKS.controllersChanged()` and `FT_HOOKS.controllerMessage(last)`, when set, are called on device changes and on every message | Lane B: a MIDI or Controllers page in Settings | FT-C1a, v0.233 |
| Settings rows in the S4 shape: `ctl.take` (UI.ctlTake, "Takeover for new mappings", page MIDI, block Controllers, global, default `pickup`, options pick up, scale, jump; help "What a knob does when it and the control on screen are at different places"; search words takeover, pickup, soft, jump); `ctl.scope` (UI.ctlScope, "Where new mappings are kept", global, default `global`, options every project or this project); `ctl.off` (UI.ctlOff, a switch per device) | Lane B: the settings table (S4) | FT-C1a, v0.233 |
| The Controllers page is now the full mappings page; `FT_HOOKS.controllersPage(host)` gives the host the class `ctlpg` and brings its own styles, so it looks the same in a Settings page body | Lane B | FT-C1b, v0.235 |
| `FT_HOOKS.pressure(midiNote or null, 0..1)`: Push 1 pad pressure (per pad or for the whole grid), for per-note pressure and MPE (FT-F14) | Lane C, FT-F14 | FT-C2a, v0.238 |
| `FT_HOOKS.push1Paint()` repaints every Push 1 (display, pads, buttons); the Push 1 settings show on the Controllers page (and in lane B's Settings through `FT_HOOKS.controllersPage`) while a Push 1 is connected. Settings rows in the S4 shape: `p1.lay` (UI.p1.lay, "Push pad layout", page MIDI, block Push 1, global, default `key`, options in key, chromatic), `p1.rows` (default `4th`: fourths, thirds, in a row), `p1.vc` (velocity curve, default `lin`: linear, soft, hard, fixed), `p1.at` (pressure, default `off`: off, per pad, whole grid), `p1.strip` (touch strip, default `pb`: pitch bend, modulation), `p1.oct` (octave of the lowest pad, default 2) | Lane B | FT-C2a, v0.238 |
| No new settings. `window.P1B` holds the Push 1 control state per device (`d.p1.b`: encoder mode `em` dev, vol or pan; lower row `lr` arm, mute or solo; track bank `tb`); `p1bDevs()` reads the device panel of the selected track, so a device whose controls are in the panel (`[data-c^="fx:"]`) is reachable from the Push with no extra work. The Push's buttons call the `SCA` commands (`play`, `rec`, `stop`, `loop`, `click`, `quant`, `newmidi`, `dup`), so DL2's registry keeps them in step | Lane B, DL2 | FT-C2b, v0.242 |
| `FT_HOOKS.push1Launch(sectionId, now)` launches a section as the Push's Session mode does (queued for the next bar, the end of the section or at once; `now` jumps at once), for a section launcher on screen or other controllers (FT-C3c Launchpad and APC). Settings row in the S4 shape: `p1.sq` (UI.p1.sq, "Launch", page MIDI, block Push 1, global, default `bar`, options next bar, end of the section, at once; help "Session mode on the Push: when a section you launch starts while the song plays"; search words launch, scene, session, quantize) | Lane B (STT), lane C (C3c) | FT-C2c, v0.244 |
| `FT_HOOKS.controllerTemplates` = `{list(), apply(deviceName, templateId), setup(deviceName, templateId), save(deviceName, name), remove(deviceName)}`: the controller templates for a Settings page; the Templates block is part of the Controllers page that `FT_HOOKS.controllersPage` already draws. No settings rows (user templates in `UI.ctlTpl`, the controllers that were offered their template in `UI.ctlTplSeen`). Template mappings carry `tpl` and `slot`; their targets start with `@` (`@dev:0..7` the selected device's knobs, `@vol:k` / `@pan:k` a bank of 8 tracks, `@ms` master, `@pad:0..15` the drum kit's pads, `@cmd:<id>` a command or navigation) | Lane B; lane C (C3b, C3c reuse the `@` targets) | FT-C3a, v0.247 |
| `FT_HOOKS.surfacePaint()` repaints every Mackie Control and HUI surface; `FT_HOOKS.surfaceAs(deviceName, 'mcu' or 'hui' or 'generic' or '')` sets what a device works as (the "Works as" block on the Controllers page). Settings row in the S4 shape: `ctl.as` (UI.ctlAs, "Works as", page MIDI, block Controllers, global, per device, default automatic, options automatic, keyboard or controller, Mackie Control, HUI; help "What this device is to AudioLab"; search words mackie, hui, mcu, x-touch, surface, motor faders) | Lane B | FT-C3b, v0.248 |
| `FT_HOOKS.gridPaint()` repaints every Launchpad and APC. No new settings rows: the grids use the Push's `p1.sq` (Launch) and Push 1 pad layout rows, and `ctl.take` for the APC faders; `ctl.as` (Works as) gets six more options: `lpm3` Launchpad Mini MK3, `lpx` Launchpad X, `lpp3` Launchpad Pro MK3, `apc40` APC40 MK2, `apcm` APC mini, `apcm2` APC mini mk2. The grids keep their own track bank (`LPG.tb`), shared by every connected grid | Lane B (STT), lane C (C2d moves the grids to clips after F8) | FT-C3c, v0.253 |
| `FT_HOOKS.clipLinks` = `{group(linkId), linkedCopy(clipId), unique(clipId), sync()}`; commands `clip.linkedDup` (Duplicate as linked copy) and `clip.unique` (Make unique) in `SCA`. No settings rows. `clip.link` is the project field (optional). Steps that copy clips (F2 arranger moves, F4, F8 clip slots) keep `link` on a copy that should stay linked and delete it on a plain copy | Lane C (F2, F4, F8), DL2 | FT-F1, v0.255 |
| `FT_HOOKS.arrangerMoves` = `{edit(op, start, length, dst), move(sectionId, dst), copy(sectionId, dst), insert(beat, beats), del(sectionId)}`: the arranger moves (clips, automation, tempo, signatures, sections, loop in one undo step) for a section launcher, Push buttons or an AI tool. Commands `arr.secDup`, `arr.insertBars`, `arr.secDelete` in `SCA`. No settings rows | DL2, lane C | FT-F2, v0.268 |
