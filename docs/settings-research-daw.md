# Settings in DAWs and music software: research (task SR2, 27 November 2026)

User's words: "Let's do some extensive deep research on settings design... look at the DAWs and anything music related... if you have suggestions to move certain things inside of the application to the settings or the other way around; sometimes we have double settings, like in the mixer we have some settings, but then more in the full settings."

**Status: research only. Nothing in the app was changed** (index.html, desktop/ and VERSION untouched; v0.221 is the reference). This is one of four parallel parts: SR1 general settings design, **SR2 DAWs and music software (this file)**, SR3 audiophile gear and the DAC, SR4 audit of AudioLab's own settings. The moves proposed in section 7 are suggestions from the outside view; SR4's audit decides which of them match what is really in the app.

How it was researched: 24 products (23 in the table; Serum 2 only in the findings), read from official manuals where they could be fetched, then reviews (mostly Sound On Sound) and forum threads. Every claim below was read on a fetched page unless it is marked "not confirmed" or "guess". Section 9 lists what could not be confirmed.

## 1. Summary

1. **Every DAW ends up with the same three layers, and the ones users like make the layers visible.** Layer one is the app and the machine (audio device, MIDI, look, folders, shortcuts). Layer two is the project (sample rate, tempo, metronome, tuning, pan law, mappings). Layer three is the thing in front of you (a track, a strip, a device), set in place. Logic for iPad shows this best: one Settings sheet with an "App Settings / Project Settings" switch at the top. Studio One has a button at the bottom of Options that jumps to Song Setup and back. Logic for Mac puts a button in a Settings pane that opens the related Project Settings pane, and the reverse.
2. **The most common complaint is not knowing the scope of a setting.** Pro Tools has preferences that are per session without saying so, and users report settings that "don't seem to stick". Elektron forum threads keep asking whether something is track, pattern or project. rekordbox mixes per-USB and profile settings and users call it a bug. No product read labels scope on every setting. This is the cheapest place for AudioLab to be better than all of them.
3. **The second most common complaint is one job spread over several windows.** Cubase has Preferences, Studio Setup, Audio Connections and Project Setup; users call it "very 1990s" and "very hard to find any setting", and Cubase 15 added a fifth window (Audio Settings) that duplicates two pages of Studio Setup, with a bug report that a change made in one does not stick while the same change in the other does. Pro Tools splits Playback Engine, I/O Setup, Session, Peripherals and Preferences. This is the user's "double settings" problem at full size.
4. **Search is rare and loved.** Only REAPER has a search box in its preferences (it highlights each match and also searches the help text). A reviewer wrote "I wish every DAW had this". Cubase users were still asking for one in 2025. AudioLab already has settings search, which puts it ahead of Ableton, Bitwig, Logic, Cubase, Studio One and Pro Tools on this point.
5. **Status displays should be the door to their settings.** The best examples: Akai MPC (the CPU/memory readout opens System Resources, the Wi-Fi and Bluetooth icons open their pages in Preferences, the BPM field opens the Tempo window), REAPER (the audio device text in the menu bar has a menu that leads to the Audio Device page), Cubase 14 (the performance meter opens a monitor whose "ASIO-Guard" button opens the Audio System page), Bitwig (the CPU icon opens the DSP graph), Logic (double-click the CPU meter for the Performance Meter).
6. **Frequent choices live where they are used; the settings window holds what is rare.** Hardware does this best because it has to: Elektron's FUNC plus a page key opens that page's setup, Push 3 has "press and hold Metronome" for metronome settings, FabFilter has no settings window at all (quality, latency mode, size and output sit in a bottom bar). Desktop equivalents: right-click the metronome (Logic, REAPER), a wrench next to the metronome (Studio One), right-click the record button (FL Studio, REAPER).
7. **"Save as default" beats a second copy of the setting.** FabFilter's "Save As Default", Serum 2's "Set x% as Default", REAPER's "Save as default project settings", Studio One's "[Make Default]" for I/O, Ableton's "Save Live Set As Default Set", MPC's "Project Defaults" tab. One place to change the thing, one click to make it the starting point. This is the cleanest answer to the mixer-versus-Settings duplicates.
8. **Small top levels work.** Hardware uses 6 to 8 sections; Bitwig 9; Ableton 10; Reason 8; Renoise 8. The outliers are REAPER (a tree so large the official guide admits it is hard to remember where things are) and Traktor (24 flat pages). AudioLab has 11 today, which is within the good range.
9. **Proposed for AudioLab:** keep one Settings window with search; make scope visible (a "This project" group and a small scope mark on each row); make every status readout open its page; let each in-place control carry a small "more" link to its Settings section and each Settings section name where the live control is; replace duplicated controls by one control plus "Use as default for new projects". A page list to test is in section 8.

## 2. Comparison table

"Route" means a click on a status display that leads to the setting. "n/c" means not confirmed.

| Product | Settings windows | Per-project settings | Audio state shown | Route from status | Search in settings | Shortcut editor | Profiles and export |
|---|---|---|---|---|---|---|---|
| **Ableton Live 12** | One Settings window, 10 tabs | No project settings window; tempo, key and MIDI mappings live in the Set; default Set and templates | Sample rate in Control Bar; CPU meter (average or current); per-track performance impact; Overall Latency in Audio tab | CPU meter has its own menu; sample-rate click n/c | No | No (users still ask in 2026) | None; Options.txt hidden file |
| **Bitwig Studio** | Dashboard > Settings, 9 pages | Project panel > Settings tab | CPU icon, disk meter; red notifications | CPU icon opens DSP graph; header right-click has scaling and display profile | No (shortcut search n/c) | Yes, keys and MIDI, named sets | Named shortcut sets; no export |
| **Logic Pro (Mac)** | Settings (global) + Project Settings | Yes, a full second window (sample rate, metronome, tuning, sync, assets) | LCD custom mode: sample rate, CPU and HD meters; "Resulting Latency" in Audio Devices | Double-click CPU meter opens Performance Meter; click sample rate in LCD; buttons between Settings and Project Settings | No | Yes, search, conflict filter, presets, import, merge | Key command sets; import project settings |
| **Logic for iPad** | One sheet with App / Project switch; a few items in iPadOS Settings | Yes | CPU/memory in control bar (optional); no latency readout | n/c | No | No | n/c |
| **GarageBand** | 6 panes (Mac) | Song Settings (iOS) | None; no buffer or sample rate option | None | No | No | None |
| **Cubase / Nuendo** | Preferences + Studio Setup + Audio Connections + Project Setup (+ Audio Settings in 15) | Project Setup dialog | Transport performance meter; input, output and ASIO-Guard latency in Audio System | Meter opens Audio Performance; its buttons open the driver panel and the Audio System page | No (requested 2025) | Yes, search, filters, presets, macros | Preference presets; Profile Manager (Pro) with import/export |
| **Studio One / Fender Studio Pro** | Options, 5 pages + Song (Session) Setup | Yes, with a button to switch between the two | Transport: sample rate, Performance button; latency, rate and bit depth under device | Performance button opens monitor; sample-rate click opens options (which, n/c) | No | Yes, search, conflict link, schemes for other DAWs, export as text | Appearance, customization, key scheme and I/O presets |
| **Pro Tools** | Setup menu: Playback Engine, I/O Setup, Session, Peripherals, MIDI, Preferences (9 tabs) | Session Setup; some Preferences are silently per session | System Usage window | None found | No | Yes since 2022.4: search by word or key, tags, conflicts, presets | I/O settings import/export; shortcut presets |
| **FL Studio** | One System Settings window (F10), tabs incl. Project | Project tab, "stored locally in each file" | Status line with total latency; underruns counter; CPU panel | Double-click CPU panel opens Plugin Performance Monitor | No | No, only "Manage shortcuts" for a few items | Toolbar presets |
| **REAPER 7** | Preferences tree + Project Settings (5 pages) | Yes; "Save as default project settings"; per-track overrides | Menu bar text: device info, disk, recording path; Performance Meter | Right-click that text: Audio Device page, project Media page | **Yes**, highlights matches, searches help text | Yes, Actions list with filter, "Find shortcut", key maps | Export configuration (19 categories), portable install |
| **Reason 13** | Preferences, 8 pages; many toggles in Options menu | Song Information, self-contain settings | Input and output latency readouts in Audio page | n/c | No | No (piano keys only) | n/c |
| **Renoise** | Preferences, 8 tabs | Song Options | CPU load threshold triggers Panic | n/c | No | Yes, with conflict warning, load/save | Themes and key files import/export |
| **Koala Sampler** | One screen, 4 sections | None (template only) | Read-only I/O line: rate, channels, buffer | None | No | QWERTY map edit, import/export | Export Settings; no import listed |
| **Elektron (Digitakt II)** | One SETTINGS key, 8 sections, 3 levels | PROJECT, PATTERN sections; scope not labelled per item | Key LED colours | FUNC + page key opens that page's setup | No | n/a | Global slots on Analog Rytm (4 per project) |
| **Akai MPC 3** | Preferences, about 14 tabs | Project Defaults, Project Load/Save, template file | Toolbar Mem/CPU, MIDI in/out, Wi-Fi, Bluetooth | **Each indicator opens its window or Preferences page** | No | n/a | Reset; template |
| **OP-1 field** | No tree; 6 groups on one screen | None (reels are not projects) | Battery via LEDs | Shift + key opens related screen | No | n/a | None |
| **Push 3 standalone** | Setup, 8 flat tabs | Metronome and time signature per Set | Status tab; battery icon below 7%; no CPU meter (criticised) | Press and hold Metronome | No | n/a | None |
| **FabFilter** | None; bottom bar | Per instance, "Save As Default" | Processing mode shows latency class | n/a | Preset search | MIDI Learn | Default preset; size becomes default |
| **Kontakt** | Options, 10 tabs | n/a | Header: voices, memory, CPU %, disk %; "!" restart button | None documented | No | n/a | n/c |
| **iZotope RX 11 / Ozone** | Preferences, 7 tabs (RX); Options with per-module tabs (Ozone 9) | n/a | Test Tone in RX Audio tab | Gear in Repair Assistant opens its preferences tab | Command search in Keyboard tab | Yes (RX), shows conflicts, presets | Shortcut presets; per-tab Reset (Ozone) |
| **rekordbox 7** | Preferences, categories with tabs; some appear only in one mode | n/a | n/c | n/c | No | Yes | My Settings travel on USB and sync back; library backup |
| **Traktor Pro 4** | Preferences, 24 flat pages | n/a | Header lights: MIDI, connection, audio, load, battery; computed Latency | Click behaviour not documented | No | Controller Manager | **Selective import/export by category** |
| **Serato DJ Pro** | Setup screen, 8 tabs, some only with matching hardware | n/a | CPU meter, limiter and drop-out warning lights | n/c | No | MIDI assign mode | MIDI presets |

## 3. Findings by product

### Ableton Live 12
- One "Settings" window (renamed from Preferences), Cmd or Ctrl + comma. Ten tabs in the current manual: Display & Input, Theme & Colors, Audio, Link, Tempo & MIDI, File & Folder, Library, Plug-Ins, Record, Warp & Launch, Licenses & Updates. Link got its own tab in 12.4; older pages show a combined "Link, Tempo & MIDI".
- Zoom can be set separately for the main window, the second window and the Settings window.
- Theme & Colors: themes, light or dark or follow the system, warm/cool/neutral tone, High Contrast, sliders for grid line opacity, brightness, colour intensity and hue. Reviewers liked it ("much easier on the eyes"); forum users complained about the thinner font and that zoom "squeezes the work area".
- Audio tab: driver type, devices, sample rate, buffer size, Driver Error Compensation, Overall Latency, a testing section.
- There is no project settings window. What belongs to the project is in the Set and in the Control Bar (tempo, time signature, scale, sample rate display). "Save Live Set As Default Set" turns the current Set into the starting point.
- The CPU meter is configured from its own menu (triangle or right-click): Average, Current, off, warn on overload. Per-track "Performance Impact" bars are switched on from the Mixer Config menu. So the mixer's view options live in the mixer, not in Settings.
- No shortcut editor, no settings search, no export. Hidden options sit in a text file (Options.txt), which is the opposite of discoverable.
- Complaint that matters for AudioLab: Live forgets the I/O configuration and channel names when the interface is not connected (threads from 2020 to 2023); users ask for I/O profiles per device.

### Bitwig Studio
- The Dashboard opens from the logo in the centre of the window header. Tabs: User, Settings, Packages, Help. Settings pages: User Interface, Behavior, Audio, Recording, Locations, Plug-ins, Controllers, Synchronization, Shortcuts. Nine pages, named by job.
- Per project: the Project panel (Settings, Info, Sections, Files, Plug-ins). Its Settings tab holds launcher defaults and remote and modulator options. Project-specific controller mappings sit in a Mappings Browser panel.
- Audio page: sample rate and block size can each be "Automatic", which keeps the current values when the interface changes; a notification appears when an interface is recognised. When the project's audio is off, the transport is replaced by one activation button, so the state cannot be missed.
- Controllers: detected controllers with a matching script are added automatically. Takeover modes: Immediate, Catch, Relative scaling.
- Display profiles (eight, from Single Display (Large) to Triple Display) and per-display scaling are in Settings and also in the header's right-click menu.
- Duplicate worth noting: pre-roll and record quantisation are in the Play menu and on the Recording page of the Dashboard.
- Complaints: no scaling under 100%, no darker theme, no official themes, no export of custom shortcut mappings.

### Logic Pro for Mac
- Two windows: Logic Pro > Settings (global, saved on quit) and File > Project Settings (saved with the project). The current guide (13.0) lists Settings panes General, Project Handling, Editing, Cycle, Catch, Notifications, Accessibility, Sound Library, Audio, MIDI, Score, Movie, Automation, Control Surfaces, MIDI Controllers, View, My Info. Project Settings: General, Audio, Channel Strips, Recording, Smart Tempo, MIDI, Score, Movie, Synchronization, Unitor, Metronome, Tuning, Assets. (Sub-pane nesting was read from a flattened list.)
- "Some Logic Pro Settings panes contain a button that opens related options in the Project Settings window", and the reverse. Both windows can be open together.
- Sample rate is a project setting. Apple warns that changing it after recording gives playback at the wrong pitch.
- Audio Devices pane: devices, I/O Buffer Size, a "Resulting Latency (Roundtrip/Output)" display, Recording Delay, Processing Threads, Process Buffer Range, and an Apply button that reloads the driver.
- The control bar is the status surface: Control-click > "Customize Control Bar and Display" with Save As Default and Revert. In custom mode the LCD shows sample rate (click to change) and CPU and HD meters (double-click for the Performance Meter).
- Control-click the metronome for its options. Low Latency Monitoring is a control bar button linked to a checkbox and limit slider in Audio > General.
- Key Commands window: search with history, a Conflicts filter, presets, import, merge, copy to clipboard.
- "Enable Complete Features" (11.x: Settings > Advanced) hid the Key Commands window, extra settings, screensets, track header configuration, the Environment and more behind one switch. It could not be found in the 13.0 guide, and Focusrite's help says its article on the switch does not apply to Logic Pro 12. That Apple removed the switch is an inference, not confirmed. Forum thread titles show people looking for the switch and for "missing" project settings; that is the cost of hiding settings behind a mode.
- No search in the Settings window.

### Logic Pro for iPad, GarageBand, Koala
- **Logic for iPad:** three tiers stated in the guide: App settings, Project settings, and the iPadOS Settings app (only the MIDI 2.0 switch, reset, privacy). Route: More button > Settings, then an **App Settings / Project Settings switch at the top**; it reopens on the last view. App: General, Audio, Recording, MIDI, Automation, View. Project: General, Audio, Recording, Flex, Synchronization, Metronome, Tuning. This is the clearest layout found for showing scope.
- **GarageBand (Mac):** six panes: General, Audio/MIDI, Metronome, Loops, My Info, Advanced. No buffer size, no sample rate. On iPhone the per-song items (count-in, metronome sound) are in Song Settings.
- **Koala:** one screen, four sections (General, Audio, MIDI, Extras), about 30 rows, all global. A read-only "I/O" line shows sample rate, channels and buffer size. Sound On Sound praises the small feature set and the logical layout.

### Cubase and Nuendo
- Four places: Preferences (Edit menu; categories Editing, Editors, Event Display, General, MIDI, MediaBay, Metering, Record, Scores, Transport, User Interface, VST, VariAudio, Video), Studio Setup (Studio menu; audio system, MIDI ports, remote devices), Audio Connections (Inputs/Outputs, Group/FX, External FX, External Instruments, Control Room), Project Setup (frame rate, sample rate, bit depth, pan law, tuning).
- Scope, per a forum moderator: Studio Setup is global, Audio Connections is per project. The windows do not say so.
- Cubase 15 added "Audio Settings", which gathers the Audio System and driver pages "rather than serving as a replacement" for them. Users: "They actually link together but are in completely separate sections in the main menu". A bug report says changes in the new window did not persist while the same change in Studio Setup did. Two controls for one value drifted apart, exactly the risk of duplicates.
- Good parts: Preference Presets with "Save marked preferences only" (partial presets); the Audio System page shows input, output and ASIO-Guard latency as read-only values; the Cubase 14 Audio Performance Monitor has a dropout timeline and a list of high-load tracks, with buttons that open the driver panel and the Audio System page; Key Commands has search, filters (All, Assigned, Customized, Unassigned), presets and macros; a Safe Mode dialog at start can disable or delete preferences when they are corrupt.
- Profile Manager (Pro) bundles preferences, toolbars, workspaces, key commands and more, with import and export, but leaves out device setup and connections; one thread calls it "plain useless" because it does not show what a profile contains.
- No search in Preferences; requested in February and December 2025.

### Studio One (now Fender Studio Pro)
- The current manual is "Fender Studio Pro 8.2" and says "Session" where Studio One 5 to 7 said "Song". Options has five pages: General (tabs General, Appearance, Keyboard Shortcuts, Network, Touch Input), Locations, Audio Setup, External Devices, Advanced (tabs Editing, Automation, Audio, MIDI, Console, Synchronization, Services, Video).
- A "Song Setup" (now "Session Setup") button at the bottom of Options switches to the per-project window.
- I/O configurations are stored "with your Session, per computer and per audio device driver", with "[Make Default]" and import/export. This solves the Ableton complaint about forgotten I/O.
- Audio Setup shows total input and output latency, sample rate and bit depth under the device. Processing has "Dropout Protection" with a second buffer; Sound On Sound: effective, but "If all this seems like a lot to absorb, well, it is".
- In place: a Metronome Setup button next to the metronome; right-click the toolbar, inspector, transport or browser > "Customize...". A Customization Editor shows and hides interface parts, saved as named settings.
- Keyboard shortcuts: search, a conflict link, schemes for other DAWs, "Export as Text".
- Complaint (Sound On Sound): I/O cannot be reached before a song exists.

### Pro Tools
- The Setup menu holds separate dialogs: Playback Engine, I/O Setup, Session, Peripherals, MIDI input devices, Keyboard Shortcuts, and Preferences (tabs Display, Operation, Editing, Mixing, Metering, Processing, MIDI, Collaboration, Synchronization).
- "All preferences are global, except for the following, which are local" (per session). The window does not mark which; users see settings that "don't seem to stick".
- Changing the playback engine or interface needs the session closed; a 2026 article lists this among features still missing. A trainer says I/O Setup causes "the greatest confusion".
- The Keyboard Shortcuts window (2022.4, "For the first time ever") is the best one found: search by word or by pressing the key, tags, conflict resolve, lockable presets, quick presets, export as text.
- No route from the System Usage meters to Playback Engine was found. Trashing the preferences folder is standard troubleshooting advice.

### FL Studio
- One System Settings window (F10) with icon tabs for MIDI, Audio, General, Files, Themes, Project and others (labels read from the manual's link names, not confirmed as printed). The Project page is in the same window and is "stored locally in each file", so global and project sit side by side without a second window. One item on that page ("Fast declick for cut groups") is per session, which shows how easily scope gets muddled.
- Audio page: a Status line with total output latency including plug-ins, buffer length in ms and samples, an "Underruns" counter, playback tracking source and offset, multithreading options.
- Right-click is the route to options: record button (recording filter), tempo display (presets, tap), CPU panel (refresh rate; double-click opens the Plugin Performance Monitor), empty toolbar (edit, presets).
- General > Display has separate scaling for the main interface, pop-ups and toolbars.
- No full shortcut editor; staff said in November 2025 they are "(slowly) working on this".

### REAPER 7
- Options > Preferences (Ctrl P), a resizable window with a large tree (General, Project, Audio > Device and Buffering, Appearance, Editing Behavior, Media, Plug-ins, Control/OSC/web and more). File > Project Settings (Alt Enter) has five pages and "Save as default project settings". Per-track overrides (timebase, performance options) are in the track's context menu.
- **The Find box** (bottom left): each click highlights the next match in colour, supports "solo OR mute", and searches the help text too. Hovering any option shows help at the foot of the window.
- The right end of the menu bar can show audio device information, free disk space or the recording path; its menu "gives you access to the Audio Device page of your preferences, the Media Settings page of your project settings, and the Monitoring FX window". (A plain left-click opening the Audio Device page is not stated in the guide.)
- Right-click almost any toolbar button for its options: metronome, ripple editing, grid, lock, the track's record-arm button, the transport bar.
- Actions list: filter with boolean operators, "Find shortcut..." (press a key to see what it does), import and export of key maps.
- "Export configuration" writes one zip with 19 tickable categories; import by dragging the zip onto the window. Portable install.
- Complaints: the guide itself says there are "so many that it can sometimes be difficult to remember where to go"; a reviewer: "Too many options sucks", options in unexpected menus, hundreds of settings with "zero official documentation". Praise from the same reviewer for the search: "I wish every DAW had this", with the limit that it "searches exactly for the text in the dialog".

### Reason 13 and Renoise
- **Reason:** Preferences pages User Interface, Browsing, Audio, MIDI, Sync, Other Controls, Folders, Account. The Audio page shows Input Latency and Output Latency. Many working toggles are in the Options menu instead (Delay Compensation, Show CPU Load for Devices, Application Zoom, precount bars). Theme and language need a restart. Application Zoom scales everything; a reviewer wanted a rack-only zoom.
- **Renoise:** Preferences tabs Audio, MIDI, OSC, Files, Keys, GUI, Theme, Plugins/Misc; per song "Song Options" (headroom, metronome, ticks per line). A CPU load threshold triggers Panic automatically. Keys tab with a focus selector and conflict warning. Themes import and export as files.

### Hardware with screens
- **Elektron Digitakt II:** one SETTINGS key, eight sections (PROJECT, SONG, PATTERN, MIDI CONFIG, SYSEX DUMP, AUDIO ROUTING, PERSONALIZE, SYSTEM), three levels deep. The sections are ordered by scope: project, song, pattern, then device. Frequent setup is reached with FUNC + a page key (FUNC + FLTR for track setup, FUNC + TRIG for quantise); the metronome is inside the TEMPO menu. Hold SETTINGS + a trig key changes brightness without entering the menu. Forum threads keep asking which settings are track, pattern or project, and how to change the defaults for new projects (answer: keep a template project, which users call cumbersome).
- **Analog Rytm:** four Global slots per project store sequencer, MIDI and routing configuration, for different rigs. A Machinedrum thread shows the risk: loading a snapshot overwrote the user's global MIDI settings.
- **Akai MPC (3.10):** Preferences from the Menu or Shift + Menu; about 14 tabs (Info, Activations, Wi-Fi, Ethernet, Bluetooth, Audio Device, Audio/Export, MIDI / Sync, Hardware, Sequencer, Project Defaults, Project Load/Save, General, Splice). "Changes to the Preferences are saved automatically." **Project Defaults** is its own tab (default tempo, bars, monitoring). The toolbar indicators are shortcuts: Mem/CPU opens System Resources (with a Purge button, the remedy next to the reading), MIDI in/out opens the MIDI Monitor, Wi-Fi and Bluetooth "open their respective setup pages in the Preferences", BPM opens the Tempo window. Each mode has its own gear for mode settings. Sync appears both in Preferences and in the Tempo window, and the manual says it is "the same setting".
- **OP-1 field:** no tree; six groups on one screen (keyboard, system, midi, clock, battery, monitor). Sync mode lives on the tempo screen next to the metronome. Sound On Sound's criticism is about scope: "Reels are not Projects".
- **Push 3 standalone:** Setup opens one flat row of eight tabs: Status, Expression, Sensitivity, Audio, MIDI, Pedals & CV, Preferences, Software. Status is the first tab (mode, battery, disk, brightness, Wi-Fi, Link). "Press and hold the Metronome button" for metronome and time signature settings of the Set. Criticised for having no CPU meter. A user thought the Wi-Fi menu was "completely missing" after it moved into the Status tab between firmware versions.

### Plug-ins
- **FabFilter:** no settings window. The bottom bar holds processing mode (Zero Latency, Natural Phase, Linear Phase), analyzer, output options, MIDI Learn and Resize. "The Default Setting preset is loaded automatically"; "Save As Default" overwrites it. A chosen size "will automatically become the default size for new plug-in instances". Sound On Sound: "efficient, intuitive and powerful". The one complaint is about scope: Character mode cannot be switched for all instances at once.
- **Serum 2:** UI size by dragging the corner or from the logo menu, with "Set x% as Default". A global settings page and a preferences screen exist; their exact contents could not be read (not confirmed).
- **Kontakt:** Options dialog (F12) with tabs Interface, Engine, Handling, Loading, Libraries, Memory, Developer, Usage data, Audio, MIDI. "CPU overload protection" with Relaxed, Medium, Strict. Header shows voices, memory, CPU % and disk %, with a "!" button that restarts the audio engine next to them. No zoom setting; a long user thread complains about small, blurry instrument views.
- **iZotope:** Ozone (9 help; newer not fetchable) has Options behind a gear with one tab per module plus General and I/O, and a Reset button that resets only the selected tab. RX 11 Preferences: Audio, Display, Keyboard, Misc, License and Updates, Plug-ins, Assistant; the Audio tab has a Test Tone; the Keyboard tab has "Show commands containing" and "Shortcut key currently used by"; a gear in Repair Assistant opens the Assistant tab directly.

### DJ software
- **rekordbox 7:** two levels (categories with tabs); some categories appear only in Export or Performance mode. "My Settings" is a set of player settings that travels on USB or over the network to the club's players, and changes made on the player are written back. Users are confused where part of it is stored per USB instead.
- **Traktor Pro 4:** 24 flat pages. Audio Setup shows a computed Latency value. Header lights for MIDI, connection, audio, load, battery, recording. **Import and Export with category checkboxes** (keyboard mappings, controller mappings, layout, paths, audio device settings, MIDI clock, effects, other), so mappings can move to another machine without overwriting its audio setup. The older Setup Wizard "resets all other settings to their default values"; a user lost settings after being forced through it.
- **Serato DJ Pro:** a Setup screen with tabs DJ Preferences, Audio, CD/Vinyl, Library + Display, Mixer, FX, MIDI, Expansion Packs. "Some options will only be available depending on the Serato DJ hardware connected"; the CD/Vinyl tab appears only with hardware that supports it. One latency slider ("USB Buffer Size") with a recommended starting value.

## 4. The common structure

**Page names that recur** across the DAWs: Audio and MIDI or controllers (all of them), look and interface and a general or behaviour page (nearly all), file locations (most), plug-ins, recording and shortcuts (about two thirds; shortcuts are often a separate window), sync (about half), account or licence (under half). These proportions are a rough tally from the notes, not a survey.

**What is almost always global:** audio device and buffer, MIDI ports and controllers, theme and scaling, folders, plug-in scanning, shortcuts, editing behaviour, updates and account.

**What is almost always per project:** sample rate (Logic, Cubase, REAPER, Pro Tools, Studio One; Ableton and Bitwig treat it as a device setting shown in the transport), tempo and time signature, metronome and count-in (Logic, Push, Renoise, GarageBand iOS), tuning, pan law (Cubase, FL Studio), frame rate and sync, bus and I/O naming (Studio One, Pro Tools buses, Cubase connections), controller mappings made by learning (Ableton, MPC, Bitwig), notes and info.

**What is almost always in place:** track height, colour, input, monitoring and record options (track header and its right-click menu); which mixer sections are shown (a mixer menu in Ableton, Cubase, Studio One); metronome on/off and its quick options (transport); meter mode of the CPU display (its own menu); toolbar and transport content (right-click > customize in Logic, Cubase, Studio One, REAPER, FL Studio).

**How audio state is shown:** device name, sample rate and buffer; latency as a computed, read-only number (Logic "Resulting Latency", Cubase input/output/ASIO-Guard, Reason, Studio One, Traktor, FL Studio's status line); a CPU meter in the transport that opens a detail window (Cubase, Studio One, Bitwig, Logic, FL Studio, MPC); a dropout count or history (FL Studio's Underruns, Cubase 14's timeline, REAPER's yellow transport flash); a test tone in a few (Ableton's testing section, RX).

## 5. Good ideas worth taking

1. **A scope switch at the top of one window** (Logic for iPad: App Settings / Project Settings; FL Studio: Project as a tab in the same window). One window, two clearly named scopes.
2. **Cross-links between scopes** (Logic's pane buttons, Studio One's Song Setup button).
3. **Search that highlights the row and reads the help text** (REAPER). AudioLab has search; the two extras are highlighting the found row and matching words from tooltips and descriptions.
4. **Status as a door** (MPC, REAPER, Cubase 14, Bitwig). Click the CPU reading for the performance view; click the sample rate or device name for the audio page.
5. **The remedy next to the reading** (MPC's Purge in System Resources, Kontakt's "!" restart beside the meters, Cubase 14's buttons inside the performance monitor). AudioLab's quick actions already have "Restart audio engine" and "Stop all sound (panic)"; the idea is to put them beside the meter too.
6. **Read-only state in the audio page** (Koala's I/O line, Cubase latency values, Logic's "Resulting Latency"). Show what is actually running, apart from what was asked for.
7. **"Automatic" as a real value** (Bitwig's sample rate and block size; Renoise's interface scaling "Auto").
8. **Explicit defaults** (MPC's Project Defaults tab; REAPER's "Save as default project settings"; Studio One's "[Make Default]"; FabFilter's "Save As Default"; Serum's "Set x% as Default").
9. **Device-aware I/O memory** (Studio One stores I/O per computer and per driver) and **hardware-aware pages** (Serato shows a tab only when matching hardware is connected; rekordbox shows categories per mode).
10. **Selective export** (Traktor's category checkboxes, REAPER's 19 categories, Cubase's "Save marked preferences only"). Keep machine-bound settings (audio device, folders) apart from user-bound ones (shortcuts, look, layout) so a move to another computer does not break audio.
11. **Reset per page** (Ozone's Reset for the selected tab) next to a reset for everything.
12. **A shortcut editor with search by pressing the key and visible conflicts** (Pro Tools, REAPER, Cubase, RX, Studio One), plus export as text.
13. **Customize in place** (right-click the transport or toolbar > Customize in Logic, Cubase, Studio One, REAPER, with "Save As Default" and "Revert" in Logic).
14. **Hold or right-click a control for its settings** (Push's Metronome button, Elektron's FUNC + key, right-click the metronome in Logic and REAPER, Studio One's wrench).
15. **Status first** (Push 3's first Setup tab is Status; the MPC's first tab is Info).
16. **Safe start** (Cubase's Safe Mode dialog: use, disable or delete preferences). Useful once settings can be corrupt or misbehave.
17. **Changes apply at once** (MPC: "saved automatically"; Cubase 15 made scaling immediate). AudioLab already says "Changes apply right away". The counterexample is Reason, where theme and language need a restart.

## 6. Mistakes to avoid

1. **Unlabelled scope** (Pro Tools' silent per-session preferences, Elektron, rekordbox's per-USB items, FL Studio's per-session item on the Project page).
2. **One job in several windows** (Cubase's four to five windows; Pro Tools' Setup menu). If two windows must exist, link them and never let the same value be edited by two different pieces of code.
3. **Two controls for one value that can disagree** (Cubase 15's Audio Settings bug). A duplicate is only safe when both are views of the same stored value and update each other at once. The MPC's manual saying the Tempo window's sync is "the same setting" as in Preferences is the right way to do it.
4. **Hiding settings behind a mode** (Logic's Complete Features switch: people could not find settings that the manual described).
5. **Hidden text-file options** (Ableton's Options.txt, Serum's preferences JSON workarounds).
6. **Working toggles scattered over menus and preferences without a rule** (Reason's Options menu, REAPER's "options sit in unexpected menus", Cubase "logic of what lives in Preferences versus menus is unclear").
7. **Too many options without help** (REAPER: "zero official documentation" for hundreds). Every row needs one line that says what it does.
8. **Flat lists that are too long** (Traktor's 24 pages; MPC's 14 tabs on a small screen).
9. **Forgetting I/O when the device is absent** (Ableton threads).
10. **Wizards or project loads that reset unrelated settings** (Traktor's wizard; Machinedrum snapshot overwriting global MIDI).
11. **Moving a setting between versions without leaving a pointer** (Push 3's Wi-Fi). Search should also find the old name.
12. **Settings window that cannot be resized** (Traktor's Controller Manager needing sideways scrolling).
13. **Requiring a restart or closed project for audio changes** (Pro Tools).
14. **No status where it is needed** (Push 3 has no CPU meter; Logic for iPad shows no latency value).
15. **Presets or profiles that do not show what they contain** (Cubase Profile Manager).

## 7. Recommended split: in place, Settings, per project

The rule that fits what the best products do, as four questions asked in order:

1. **Does it change while making music, or is it about the thing under the pointer?** Then it lives **in place** (transport, track header, mixer strip, device, right-click menu). Examples: metronome on/off and level, count-in, follow playhead, monitoring, record arm, strip width, which mixer sections show, meter mode, track colour.
2. **Does the song sound or behave differently when it changes, and should it travel with the song file?** Then it is **per project**. Examples: sample rate the project was made at, tempo and time signature, tuning, pan law, master ceiling, metronome sound, export format last used for this song, learned mappings.
3. **Is it about this computer or this person?** Then it is **Settings**. Examples: audio device and buffer, DAC and output chain, MIDI devices, look, scale, performance level, shortcuts, folders, updates.
4. **Is it the starting value for something that is then set in place or per project?** Then it is a **default**, shown in Settings under "New projects" (or reached by "Use as default" from the in-place control), and never a second live control.

Rules for the borders:

- **One live control per value.** If a value shows in two places, one of them is the control and the other is either the same control mirrored (both update at once) or a link ("Mixer look: in the mixer menu").
- **In place gets the frequent three or four choices; Settings gets the full set.** The in-place menu ends with one link to the full section (Logic's metronome menu, Studio One's wrench). Settings sections that have an in-place twin say where it is.
- **Every Settings row carries its scope**: "This computer", "This project" or "New projects". A small mark is enough.
- **Status readouts open their page.** CPU reading opens Performance; sample rate, buffer or device name opens Audio system; the output or DAC name opens Interface and DAC; the tempo opens tempo and metronome options; the zoom readout opens Zoom and playhead.

### Suggestions for AudioLab (to check against SR4's audit)

AudioLab's Settings window today (v0.221, seen headless): search field; pages General, Audio system, Interface and DAC, Interface, Performance, Glass & light, Colours & clips, Zoom and playhead, Keyboard shortcuts; group "Output" with Project file and Export audio; footer with "Reset all settings...", "Changes apply right away" and Done. The quick actions menu has follow-playhead modes with a note "Playhead look in Settings". These are guesses from the outside about where the doubles are:

| Topic | Today (as far as seen) | Suggestion | Seen in |
|---|---|---|---|
| Mixer look and meters | In Settings > Interface, and some in the mixer | Make the mixer's own menu the live control (sections shown, strip width, meter mode). Settings > Interface keeps only "Defaults for new projects" and a link "Mixer options are in the mixer menu" | Ableton Mixer Config menu, Cubase rack setup, Studio One customize |
| Track and transport controls shown | Settings > Interface | Add right-click > "Customize..." on the transport and the track header that opens the same section directly; keep one stored value | Logic, Cubase, Studio One, REAPER |
| Follow playhead | Quick actions (modes) plus Settings > Zoom and playhead (look) | Keep modes in place; keep look in Settings; the in-place menu already links to Settings, add the reverse line in Settings | Logic metronome pattern |
| Metronome and count-in | n/c | On/off and level in the transport; right-click or hold for pattern and count-in; sound choice per project | Logic, Push 3, REAPER, Studio One |
| Audio device, buffer, sample rate | Settings > Audio system and Interface and DAC | Keep in Settings; add a read-only "Running now" line (device, rate, buffer, measured latency); make the transport's CPU and rate readouts open these pages | Koala, Cubase, Logic, MPC, REAPER |
| Light mode and effect levels | Performance page, a banner, a link on General | Good as is (one page, links elsewhere). Make the CPU readout in the transport open Performance | MPC, Cubase 14 |
| Export audio, Project file | In Settings under "Output" | These are per project. Either move them to a project dialog (File > Project settings, Export dialog) or keep them in the window under a clearly named "This project" group. Recommended test: the scope switch | Logic for iPad, FL Studio, Studio One |
| Master ceiling, mono, swap, balance (Interface and DAC) | Settings | Decide per item with question 2 above: listening checks (mono, swap) are in-place monitor controls on the master strip; ceiling for export is per project; DAC choice is this computer | Cubase Control Room, Studio One |
| Reset | One "Reset all settings..." in the footer | Add "Reset this page" beside it | Ozone |
| Moving to another computer | n/c | Export settings with tick boxes: look, shortcuts, layout (portable) apart from audio device and folders (this computer) | Traktor, REAPER |

## 8. Page lists for AudioLab to test

Three variants, to be built as small test UIs like the logo and design-language rounds. All keep the search field, immediate apply and the footer.

**Variant A: same pages, scope made visible (smallest change).** Sidebar in three labelled groups.

- THIS COMPUTER: General · Audio system · Interface and DAC · MIDI and controllers (when there is something to set) · Performance
- LOOK: Interface · Glass & light · Colours & clips · Zoom and playhead · Keyboard shortcuts
- THIS PROJECT: Project file · Export audio · Tempo, metronome and tuning (if these exist as settings)
- Each row with a small scope mark; each section with an in-place twin shows where it is.

**Variant B: scope switch at the top (Logic for iPad model).** A two-part switch "App | This project" above the search; search covers both and shows the scope in each result.

- App: General · Audio · Output and DAC · MIDI · Look (Interface, Glass & light, Colours & clips as sections of one page, or as sub-tabs) · Zoom and playhead · Performance · Shortcuts · New projects (all defaults in one place)
- This project: Project file · Audio (rate, ceiling) · Tempo and metronome · Export

**Variant C: fewer, larger pages named by job (Bitwig and Push model, seven pages).**

- Status (what is running now: device, rate, buffer, latency, CPU, version, update; each line links to its page) · Audio (system, interface and DAC) · Look (interface, glass, colours) · Behaviour (zoom, playhead, editing, help) · Performance · Shortcuts · Project (file, export, defaults for new projects)

Recommendation: **test B first**, with A as the fallback. B answers the user's question about doubles most directly (it forces every setting to declare a scope), it matches the clearest product found, and it leaves the existing pages mostly intact. C is the tidiest list but merges pages the user has already shaped (Glass & light, Colours & clips), so it is the riskiest. In all variants add the same three behaviours: status readouts open their page, in-place menus end with a link to their section, and "Use as default for new projects" replaces second copies of a control.

Things to measure in the test UIs: can "where do I change the buffer", "why is export quality different in this song" and "make the mixer strips narrower" each be found in under three clicks or one search; does the scope mark get noticed; does anyone miss a page that was merged.

## 9. What is confirmed and what is not

- Read on fetched official pages or manuals: everything stated without a marker for Ableton, Bitwig, Logic (Mac, iPad), GarageBand, Koala, REAPER (User Guide 7.86), FL Studio settings pages, Reason 13, Renoise, Elektron (Digitakt II, Octatrack, Analog Rytm manuals), MPC 3.10 and 2.10, OP-1 field, Push 3, FabFilter, Kontakt, RX 11, rekordbox 7.2.18, Traktor Pro 4.
- Version caveats: Cubase facts are mostly from Cubase 13 and Nuendo 10 to 13 manual pages plus the Cubase 15 Sound On Sound review and forum threads. Studio One facts are from the Fender Studio Pro 8.2 manual, the Studio One 5 manual and Sound On Sound. Pro Tools facts are from avid.com guide pages, Sound On Sound, Production Expert and Sweetwater (the Reference Guide PDF could not be fetched). Ozone is from the Ozone 9 help. Serato's tab list is from a manual copy with no version stated. The Bitwig guide version was not confirmed.
- Not confirmed: whether clicking Ableton's sample-rate display opens the Audio tab; separate input and output latency readouts and the name "Test Tone" in Ableton; Bitwig shortcut search; a left-click on REAPER's device text opening the Audio Device page (the menu route is confirmed); which dialog Studio One's sample-rate click opens; click behaviour of Traktor's header lights; Serum 2's global page contents; FL Studio's exact tab labels and Theme page; whether Apple removed "Enable Complete Features" in Logic 12 or later (inferred); Logic's Learn button and track header configuration; Renoise and Reason CPU meter click behaviour; Neutron (not read).
- Guesses: the "today" column in section 7 beyond what the headless view of the Settings window showed, and the proportions in section 4.
- Forum quotes are single threads, not surveys. No Reddit pages could be read.

## 10. Sources

**Ableton Live 12**
- [Live 12 Manual, First Steps](https://www.ableton.com/en/live-manual/12/first-steps/)
- [Live 12 release notes](https://www.ableton.com/en/release-notes/live-12/)
- [Live's MIDI Settings](https://help.ableton.com/hc/en-us/articles/209774205)
- [Driver Error Compensation FAQ](https://help.ableton.com/hc/en-us/articles/115000234830)
- [How to reduce latency](https://help.ableton.com/hc/articles/209072289)
- [Managing Files and Sets](https://www.ableton.com/en/live-manual/12/managing-files-and-sets/)
- [Live Concepts](https://www.ableton.com/en/live-manual/12/live-concepts/)
- [Setting up an Audio Interface](https://help.ableton.com/hc/articles/211476789)
- [Computer Audio Resources and Strategies](https://www.ableton.com/en/live-manual/12/computer-audio-resources-and-strategies/)
- [Navigation and View Options in Live 12](https://help.ableton.com/hc/en-us/articles/12243771208092)
- [MIDI and Key Remote Control](https://www.ableton.com/live-manual/12/midi-and-key-remote-control/)
- [Accessibility Options in Live](https://www.ableton.com/en/live-manual/12/accessibility-options-in-live/)
- [Options.txt file](https://help.ableton.com/hc/en-us/articles/6003224107292)
- [Live's CPU Meter](https://help.ableton.com/hc/articles/360019151379)
- [CDM, Twelve things to try in Live 12](https://cdm.link/2024/03/twelve-things-to-try-in-live-12/)
- [Forum: Ableton forgetting output config when device not available](https://forum.ableton.com/viewtopic.php?p=1779463)
- [Forum: Custom and remappable keyboard shortcuts](https://forum.ableton.com/viewtopic.php?p=1837301)
- [Forum: 12 font is different from 11](https://forum.ableton.com/viewtopic.php?p=1826691)

**Bitwig Studio**
- [User Guide, The Dashboard](https://www.bitwig.com/userguide/latest/the_dashboard/)
- [Anatomy of the Bitwig Studio Window](https://www.bitwig.com/userguide/latest/anatomy_of_the_bitwig_studio_window)
- [The Window Menus / Transport Area](https://bitwig.com/userguide/latest/the_window_menus_transport_area)
- [The Project Panel](https://www.bitwig.com/userguide/latest/the_project_panel)
- [User Interfacing](https://www.bitwig.com/userguide/latest/user_interfacing)
- [Plug-in Handling and Options](https://bitwig.com/userguide/latest/vst_plug-in_handling_and_options)
- [A Musical Swiss Army Knife (display profiles)](https://www.bitwig.com/userguide/latest/a_musical_swiss_army_knife)
- [CDM, Bitwig themes](https://cdm.link/2024/07/bitwig-themes/)
- [KVR: Bitwig export custom keyboard mappings](https://www.kvraudio.com/forum/viewtopic.php?p=9012323)
- [KVR: What drives you crazy in Bitwig?](https://www.kvraudio.com/forum/viewtopic.php?p=8232990)

**Logic Pro, GarageBand, Koala**
- [Overview of Logic Pro settings](https://support.apple.com/guide/logicpro/lgcp53689108/mac)
- [Logic Pro User Guide contents](https://support.apple.com/guide/logicpro/lgcp04687f98/mac)
- [Overview of preferences (10.7)](https://support.apple.com/en-kz/guide/logicpro/lgcp53689108/10.7/mac)
- [Overview of project settings (10.7.3)](https://support.apple.com/guide/logicpro/project-settings-overview-lgcp9734a054/10.7.3/mac)
- [Use the complete set of features (11.2)](https://support.apple.com/en-au/guide/logicpro/lgcp5cbf192f/11.2/mac/14.4)
- [Audio Devices settings](https://support.apple.com/en-jo/guide/logicpro/lgcpbb81aca5/mac)
- [General Audio settings](https://support.apple.com/guide/logicpro/lgcp0ed343a9/mac)
- [General MIDI settings](https://support.apple.com/guide/logicpro/lgcpb839d947/mac)
- [General View settings](https://support.apple.com/en-kz/guide/logicpro/lgcp9793a910/mac)
- [Set the sample rate of a project](https://support.apple.com/en-sa/guide/logicpro/lgcpce0958b8/mac)
- [Avoid system overloads](https://support.apple.com/en-us/HT203930)
- [Customize the control bar](https://support.apple.com/guide/logicpro/lgcp5bdd6d9d/mac)
- [Metronome project settings](https://support.apple.com/guide/logicpro/lgcpe1d6118e/mac)
- [Use the metronome](https://support.apple.com/en-eg/guide/logicpro/lgcp0534986f/mac)
- [Browse, import, and save key commands](https://support.apple.com/en-bh/guide/logicpro/lgcp68d9ced1/mac)
- [Controller assignments Easy view](https://support.apple.com/en-am/guide/logicpro/ctls71c30f28/mac)
- [Focusrite, Advanced Tools in Logic Pro 11 and below](https://support.focusrite.com/hc/en-gb/articles/360001323785)
- [Sound On Sound, Apple Logic Pro 12](https://www.soundonsound.com/reviews/apple-logic-pro-12?amp)
- [Logic for iPad, Overview of app settings](https://support.apple.com/guide/logicpro-ipad/lpip81dcb620/ipados)
- [Logic for iPad, Overview of project settings](https://support.apple.com/guide/logicpro-ipad/lpipf05c1559/ipados)
- [Logic for iPad, Audio Devices settings](https://support.apple.com/guide/logicpro-ipad/lpip53bd0492/ipados)
- [Logic for iPad, settings in the Settings app](https://support.apple.com/guide/logicpro-ipad/lpipa0d02dcf/ipados)
- [Logic for iPad, Customize the control bar](https://support.apple.com/guide/logicpro-ipad/lpipe1b324c2/ipados)
- [GarageBand, Change Audio/MIDI settings](https://support.apple.com/guide/garageband/gbnd967819b9/mac)
- [GarageBand, Change Advanced settings](https://support.apple.com/guide/garageband/gbnded6e79bc/mac)
- [GarageBand for iPhone, Play and navigate songs](https://support.apple.com/guide/garageband-iphone/chsb34ba051/ios)
- [Koala Sampler manual, 8. Settings](https://metawork-studio.github.io/koala-documentation/mobile/8-settings)
- [Sound On Sound, Elf Audio Koala Sampler](https://www.soundonsound.com/reviews/elf-audio-koala-sampler)

**Cubase and Nuendo**
- [Preferences dialog (Nuendo 11)](https://archive.steinberg.help/nuendo/v11/en/cubase_nuendo/topics/preferences/preferences_the_preferences_dialog_r.html)
- [Saving partial preference settings (Nuendo 13)](https://archive.steinberg.help/nuendo/v13/en/cubase_nuendo/topics/preferences/preferences_partial_settings_saving_t.html)
- [Cubase Pro 13 manual contents](https://archive.steinberg.help/cubase_pro/v13/en)
- [Studio Setup dialog (Nuendo 13)](https://archive.steinberg.help/nuendo/v13/en/cubase_nuendo/topics/setting_up/setting_up_studio_setup_dialog_r.html)
- [Audio Connections window (Nuendo 12)](https://archive.steinberg.help/nuendo/v12/en/cubase_nuendo/topics/vst_connections/vst_connections_window_r.html)
- [Project Setup dialog (Nuendo 12)](https://archive.steinberg.help/nuendo/v12/en/cubase_nuendo/topics/project_handling/project_handling_project_setup_dialog_r.html)
- [Audio System page (Cubase 13)](https://archive.steinberg.help/cubase_ai/v13/en/cubase_nuendo/topics/setting_up/setting_up_audio_vst_audio_system_r.html)
- [New Audio Performance Monitor in Cubase 14](https://www.steinberg.help/r/new-audio-performance-monitor-in-cubase-14/nuendo-14)
- [Transport Bar sections (Nuendo 12)](https://archive.steinberg.help/nuendo/v12/en/cubase_nuendo/topics/playback/playback_transport_sections_c.html)
- [Key Commands dialog (Cubase Pro 13)](https://archive.steinberg.help/cubase_pro/v13/en/cubase_nuendo/topics/key_commands/key_commands_dialog_r.html)
- [Preferences of Cubase and Nuendo (file locations)](https://www.steinberg.help/r/preferences-of-cubase-and-nuendo)
- [Profiles (Cubase Pro 9)](https://archive.steinberg.help/cubase_pro_artist/v9/en/cubase_nuendo/topics/customizing/customizing_profiles_c.html)
- [Safe Mode dialog (Nuendo 10)](https://archive.steinberg.help/nuendo/v10/en/cubase_nuendo/topics/customizing/customizing_safe_mode_dialog_r.html)
- [Sound On Sound, Steinberg Cubase Pro 15](https://www.soundonsound.com/reviews/steinberg-cubase-pro-15?amp)
- [Sound On Sound, Using MIDI Remote in Cubase 12](https://www.soundonsound.com/techniques/using-midi-remote-cubase-12?amp)
- [Forum: Audio Settings fail to save](https://forums.steinberg.net/t/bug-audio-settings-accessed-via-edit-menu-or-audio-connections-fail-to-save/1023002)
- [Forum: Add Audio Connections to the Studio Setup window](https://forums.steinberg.net/t/fr-add-audio-connections-to-the-studio-setup-window/786982)
- [Forum: Please add search box to the Settings window](https://forums.steinberg.net/t/please-add-search-box-to-the-settings-window/1015936)
- [Forum: Search in preferences](https://forums.steinberg.net/t/search-in-preferences/974674)
- [Forum: Why are the Audio Settings placed under "Edit"?](https://forums.steinberg.net/t/why-are-the-audio-settings-placed-under-edit/1020121)
- [Forum: Please make Profile manager actually useful](https://forums.steinberg.net/t/please-make-profile-manager-actually-useful/979205)

**Studio One / Fender Studio Pro**
- [General Options](https://fenderstudiopromanual.fender.com/en/Content/Setup_Topics/General_Options.htm)
- [Advanced Options](https://fenderstudiopromanual.fender.com/en/Content/Setup_Topics/Advanced_Options.htm)
- [Audio Device Input/Output Setup](https://fenderstudiopromanual.fender.com/en/Content/Setup_Topics/Audio_Device_Input_Output.htm)
- [Set Up Your Audio Device](https://fenderstudiopromanual.fender.com/en/Content/Setup_Topics/Set_Up_Your_Audio_Device.htm)
- [Set Up Your MIDI Devices](https://fenderstudiopromanual.fender.com/en/Content/Setup_Topics/Set_Up_Your_MIDI_Devices.htm)
- [Customization](https://fenderstudiopromanual.fender.com/en/Content/Setup_Topics/Customization.htm)
- [Key Commands](https://fenderstudiopromanual.fender.com/en/Content/Fundamentals_Topics/Key_Commands.htm)
- [Studio One 5 User Manual (PDF)](https://www.fullcompass.com/common/files/47470-StudioOne5UserManual.pdf)
- [Sound On Sound, Studio One: Audio I/O Routing](https://www.soundonsound.com/techniques/studio-one-audio-io-routing)
- [Sound On Sound, Studio One: Buffers and Low Latency](https://www.soundonsound.com/techniques/studio-one-buffers-low-latency)
- [Loopmasters, Studio One Song Page tutorial part three](https://www.loopmasters.com/articles/2454-PreSonus-Studio-One-Song-Page-Tutorial-Part-Three)

**Pro Tools**
- [Avid, Changing buffer size](https://www.avid.com/pro-tools/user-guide/change-buffer-size)
- [Avid, Changing sample rate and bit depth](https://www.avid.com/pro-tools/user-guide/change-sample-rate-bit-depth)
- [Sound On Sound, Creating Custom Shortcuts in Pro Tools](https://www.soundonsound.com/techniques/creating-custom-shortcuts-pro-tools)
- [Sound On Sound, How to optimise Pro Tools preferences](https://www.soundonsound.com/techniques/how-optimise-pro-tools-preferences)
- [Sound On Sound, Using Window Configurations](https://www.soundonsound.com/techniques/using-window-configurations)
- [Production Expert, Why do some Pro Tools preferences change between sessions](https://www.production-expert.com/home-page/why-do-some-pro-tools-preferences-change-between-sessions)
- [Production Expert, Playback Engine: every setting explained](https://www.production-expert.com/production-expert-1/pro-tools-playback-engine-every-setting-explained)
- [Production Expert, Pro Tools I/O Setup: a complete guide for 2026](https://www.production-expert.com/production-expert-1/pro-tools-i/o-setup-a-complete-guide-for-2026)
- [Production Expert, 3 Pro Tools features still missing in 2026](https://www.production-expert.com/production-expert-1/3-pro-tools-features-still-missing-in-2026)
- [Production Expert, Understanding the System Usage meters](https://www.production-expert.com/home-page/2014/1/16/understanding-the-system-usage-meters-in-pro-tools.html)
- [Sweetwater, Pro Tools DAW controller setup](https://www.sweetwater.com/sweetcare/articles/pro-tools-daw-controller-setup/)
- [Sweetwater, How do I trash my Pro Tools preferences](https://www.sweetwater.com/sweetcare/articles/how-do-i-trash-my-pro-tools-preferences)

**FL Studio, REAPER, Reason, Renoise**
- [FL Studio manual, Audio settings](https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/envsettings_audio.htm)
- [FL Studio manual, General settings](https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/envsettings_general.htm)
- [FL Studio manual, MIDI settings](https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/envsettings_midi.htm)
- [FL Studio manual, File settings](https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/envsettings_files.htm)
- [FL Studio manual, Project General Settings](https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/songsettings_settings.htm)
- [FL Studio manual, Toolbar panels](https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/toolbar_panels.htm)
- [Image-Line forum: ability to change shortcuts](https://forum.image-line.com/viewtopic.php?p=2035613)
- [Up and Running: A REAPER User Guide v7.86 (PDF)](https://www.reaper.fm/userguide/ReaperUserGuide786c.pdf)
- [Sound On Sound, Reaper To Go](https://www.soundonsound.com/techniques/reaper-go)
- [Admiral Bumblebee, REAPER Day 30](https://www.admiralbumblebee.com/music/2021/02/07/reaper-day-30)
- [Admiral Bumblebee, Things that I really dislike about REAPER](https://www.admiralbumblebee.com/music/2017/04/04/things-that-i-really-dislike-about-reaper)
- [REAPER Blog, Learn REAPER's preferences in just 90 minutes](https://reaper.blog/2015/04/learn-reapers-preferences-in-just-90-minutes)
- [Reason 13, Menu and Dialog Reference](https://docs.reasonstudios.com/reason13/menu-and-dialog-reference)
- [Sound On Sound, Reason's New High-resolution GUI](https://www.soundonsound.com/techniques/reasons-new-high-resolution-gui)
- [Renoise manual, Preferences](https://tutorials.renoise.com/wiki/Preferences)
- [Renoise manual, Song Options](https://tutorials.renoise.com/wiki/Song_Options)
- [Renoise manual, Transport Panel](https://tutorials.renoise.com/wiki/Transport_Panel)

**Hardware**
- [Elektron Digitakt II User Manual (PDF)](https://www.analoguehaven.com/elektron/digitakt-ii/manual.pdf)
- [Elektron Syntakt User Manual OS 1.20 (PDF)](https://cdn.www.elektron.se/media/downloads/syntakt/Syntakt_User_Manual_ENG_OS1.20_221123.pdf)
- [Elektron Octatrack User Manual OS 1.40A (PDF)](https://elektron.se/wp-content/uploads/2024/09/Octatrack-User-Manual_ENG-OS1.40A_220204.pdf)
- [Elektron Analog Rytm User Manual OS 1.71 (PDF)](https://elektron.se/wp-content/uploads/2024/10/analog_rytm_user_manual_eng_os1.71_241016.pdf)
- [Akai MPC Standalone OS User Guide v3.10 (PDF)](https://cdn.inmusicbrands.com/Software/M310PCFIN26OCT/MPC%20Standalone%20OS%20-%20User%20Guide%20-%20v3.10.pdf)
- [Akai MPC User Guide v2.10 (PDF)](https://cdn.inmusicbrands.com/akai/M2P10CUP/MPCX-MPCLive-MPCLiveII-MPCOne-MPC%20Touch-UserGuide-v2.10.pdf)
- [Akai Pro, Adjusting Project Defaults](https://support.akaipro.com/support/solutions/articles/69000822965-akai-pro-mpc-series-adjusting-project-defaults)
- [OP-1 field user guide (PDF)](https://assets.teenage.engineering/_img/69f248938d433104c4dd1846_original.pdf)
- [Ableton Push 3 Manual](https://www.ableton.com/en/push/manual/)
- [Sound On Sound, Ableton Push 3](https://www.soundonsound.com/reviews/ableton-push-3)
- [Sound On Sound, Teenage Engineering OP-1 Field](https://www.soundonsound.com/reviews/teenage-engineering-op-1-field)
- [Elektronauts: Parameters, track vs pattern vs project](https://stage2.elektronauts.com/t/parameters-track-vs-pattern-vs-project/150062)
- [Elektronauts: Global MIDI default configuration](https://stage2.elektronauts.com/t/global-midi-default-configuration/86004)
- [Elektronauts: Change default settings for every new project?](https://www.elektronauts.com/t/change-default-settings-for-every-new-project/12097)
- [Elektronauts: slots and global MIDI settings getting reset](https://www.elektronauts.com/t/trying-to-understand-slots-global-midi-settings-getting-reset/17644)
- [Ableton forum: Push 3 standalone missing menus](https://forum.ableton.com/viewtopic.php?p=1830015)

**Plug-ins**
- [FabFilter Pro-Q 4, Overview](https://www.fabfilter.com/help/pro-q/using/overview)
- [Pro-Q 4, Full Screen mode, resizing and scaling](https://www.fabfilter.com/help/pro-q/using/fullscreenandresize)
- [Pro-Q 4, Loading presets](https://www.fabfilter.com/help/pro-q/presets/loadingpresets)
- [Pro-Q 4, MIDI Learn](https://www.fabfilter.com/help/pro-q/using/midilearn)
- [Pro-Q 4, Processing mode](https://www.fabfilter.com/help/pro-q/using/processingmode)
- [Pro-Q 4, Output options](https://www.fabfilter.com/help/pro-q/using/output)
- [Pro-L 2, Overview](https://www.fabfilter.com/help/pro-l/using/overview)
- [Pro-L 2, Oversampling](https://www.fabfilter.com/help/pro-l/using/oversampling)
- [Sound On Sound, FabFilter Pro-Q 4](https://www.soundonsound.com/reviews/fabfilter-pro-q-4?amp)
- [Serum 2 web manual, Resizing the UI](https://xferrecords.com/web-manual/serum-2/resizing-the-ui)
- [Serum 2 What's New (PDF)](https://static.xferrecords.com/Serum%202%20What's%20New.pdf)
- [Kontakt manual, Options dialog](https://docs.native-instruments.com/online-guides/kontakt-manual/en/options-dialog)
- [Kontakt manual, Main Control Panel](https://native-instruments.com/ni-tech-manuals/kontakt-manual/en/main-control-panel)
- [NI community: can't we make Kontakt bigger?](https://community.native-instruments.com/discussion/10506/seriously-cant-we-make-kontakt-bigger)
- [Ozone 9 help, Options](https://s3.amazonaws.com/izotopedownloads/docs/ozone9/en/options/index.html)
- [RX 11 Manual (PDF)](https://docs.native-instruments.com/pdf-guides/RX/RX_11_Manual_English.pdf)

**DJ software**
- [rekordbox 7.2.18 manual (PDF)](https://cdn.rekordbox.com/files/20260807093645/rekordbox7.2.18_manual_EN.pdf)
- [rekordbox FAQ, Cloud Library Sync](https://rekordbox.com/en/support/faq/library-sync-7/)
- [Pioneer DJ community: Load My Settings](https://community.pioneerdj.com/hc/en-us/community/posts/54462046555673/comments/54512150064153)
- [Traktor Pro manual, Preferences](https://docs.native-instruments.com/online-guides/traktor-pro-manual/en/preferences)
- [Traktor Pro manual, Overview (header)](https://docs.native-instruments.com/online-guides/traktor-pro-manual/en/traktor-overview)
- [DJ TechTools, Traktor Setup Wizard](https://techtools.zendesk.com/hc/en-us/articles/202184614-Traktor-Setup-Wizard)
- [NI community: Setup Wizard data loss](https://community.native-instruments.com/discussion/comment/165281)
- [DJ TechTools forum: resizing the Traktor preference window](https://forum.djtechtools.com/t/how-to-resize-the-preference-window-in-traktor/45774)
- [Serato, Software Overview DJ Pro 3.0](https://support.serato.com/hc/en-us/articles/224859147-Software-Overview-DJ-Pro-3-0)
- [Serato DJ Pro user manual (copy, PDF)](https://r2.gear4music.com/media/36/366330/download_366330.pdf)
