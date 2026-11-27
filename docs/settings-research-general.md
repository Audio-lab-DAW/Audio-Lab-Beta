# Settings design research: general (task SR1)

Date: 2026-11-27. Scope: settings design outside the music world (phones, operating systems, apps, creative tools, games, cameras, cars) plus design-system guidance and UX research. DAWs are in SR2, audiophile gear and the DAC in SR3, the audit of AudioLab's own settings in SR4.

How to read the evidence: every claim comes from a page that was opened during this research unless it is marked **GUESS** (inference, or commonly described behaviour that no opened page confirmed). The source list at the end says for each link whether it was read or only seen in search results.

## 1. Summary

1. **The best settings screen is a short one.** Every serious guideline (Apple, Material, Microsoft, GNOME) says the same three things: choose good defaults, keep the count down, and keep anything used during work out of settings and next to the thing it affects. Most people never change defaults, so the default is the design.
2. **Three places, not one.** The products that handle many options well split them by scope and say so: per machine (hardware), per user (taste and workflow), per project (the document). DaVinci Resolve and Final Cut do this; VS Code and JetBrains mark the scope on each setting. The failure case is always the same: the user cannot tell which place a value lives in or which value is winning.
3. **Search is the real navigation once there are more than about 50 settings.** macOS, iOS and Windows critics all end at "I now rely on search". So search has to be good: match synonyms and descriptions, show where the result lives, scroll to and highlight the control.
4. **Instant apply is the norm, with three exceptions.** Toggles must act at once. Use an explicit confirm only for changes that are slow, that must commit together, or that can lock the user out (display mode in games, audio device in a DAW), and there the pattern is a timed "keep these settings?" revert.
5. **Show state, not description.** Rows should show the current value, whether it differs from the default, and a one-click reset. VS Code's modified bar, KDE's "highlight changed settings", God of War's blue markers and Fujifilm's red values are the same idea in four industries.
6. **Games are the best teachers for the "sciencey" feel.** Gears Tactics and Resident Evil 2 show, per setting, a plain sentence, a live preview and the cost in GPU, CPU and memory, with a live total. The DAW equivalent (latency in ms, CPU load, RAM) is the single most transferable idea in this document.
7. **Frequent controls never belong in a menu.** Euro NCAP now scores cars on physical buttons, Figma reversed UI3 changes that added clicks to frequent toggles, and cameras settled on a user-curated quick panel on top of the deep menu.
8. **What fails, consistently:** a narrow scrolling list on a wide desktop screen (macOS Ventura), two homes for the same setting (Windows), "Advanced" and "General" dumping grounds, hidden second tools for common needs (GNOME Tweaks), options that break the product with no way back (old Firefox), and upsell or filler on the settings home page (Windows 11).

## 2. Findings per area

### 2.1 Phones

**iOS Settings**
- Search arrived in iOS 9 (seen in search-result titles only). iOS 18 moved app settings into an "Apps" section, which cut the root list to "just over 2 pages", and added explainer headers with "learn more" links and search suggestions.
- Criticism: TidBITS counted "over 1200 items", groupings that look arbitrary and move every release, and searches that "often fail". Commenters on the iOS 18 change say the Apps section only pushes the long list one level down.
- What works: a short root, an alphabetical list where no better order exists, search as the escape hatch.
- **GUESS:** the 2007 original was a single grouped list; the Apple ID banner came in iOS 10.3; iOS 26 moved the search field to the bottom. None of these was confirmed by an opened page.

**Android and Material**
- Call it "Settings", never "Options" or "Preferences".
- Leave out frequently used actions (put them in context) and anything the device already sets.
- Order by importance and frequency. No "Other" or "Miscellaneous" groups. At 15 or more settings, move related ones to a subscreen whose title matches its entry.
- Labels: important word first, neutral wording ("Block", not "Don't allow"), no generic verbs such as Set, Change, Manage.
- Secondary text: "Show the setting status instead of describing the setting". Longer explanation goes one level down.
- A dependent setting sits under its parent and says why it is unavailable.
- On large screens use list plus detail; do not stretch one column to full width.
- AOSP platform rules: 10 to 15 items per screen; an "Advanced" collapse only when it hides three or more items, and its subtext lists what is inside; search results show the breadcrumb; one canonical screen per setting even if several entry points lead to it.

**Samsung One UI**
- The top of the screen is a "viewing area" with large titles and no touch targets; controls live in the lower "interaction area". Setting names stay within 31 characters; subtext only when a setting is hard to understand.
- **GUESS:** the "Looking for something else?" block of cross-links at the bottom of pages is real One UI behaviour, but no source was found. It is still a good idea: related settings linked from the page where people look first.

### 2.2 Operating systems

**macOS System Settings (Ventura, 2022): the reference failure**
- The icon grid became an iOS-style sidebar with scrolling forms. Named criticisms:
  - The window has a fixed width and the sidebar cannot be resized, so text truncates on a large display.
  - The sidebar never shows all items; the overview is gone ("Welcome to scrolling").
  - Switches replaced checkboxes against Apple's own guidance, and switch labels are not clickable.
  - Tabs became buttons that open modal sheets.
  - Search returns results that do not apply to the machine or do nothing.
  - Keyboard navigation broke in places.
  - "Eight unlabeled subgroups" at top level; common settings buried (default browser on the second page of Desktop & Dock, Time Machine inside General); vague "Advanced" buttons.
- Fixes proposed by Jason Snell: use the width with columns, add favourites and recents, allow bulk edits, offer a simple and a full mode.
- Sequoia reshuffled the sidebar; critics still say "I now rely on search".
- One point in its favour: Howard Oakley grants that search and navigation improved over the old System Preferences.

**Windows 11 Settings versus Control Panel**
- Works: a left navigation that stays on every page, breadcrumbs that jump to any level (System > Display > Graphics), a status header.
- Fails: deep nesting; two places for the same job (Programs & Features and Apps both uninstall); legacy dialogs that survive for years because drivers depend on them; a Home page that ghacks calls "half promotion half pointless", with cards that cannot be hidden.
- Lesson: a migration left half done is worse than either design. Move a whole area at once and leave a signpost.

**GNOME**
- Old HIG: "Update values or settings immediately". An Apply button only when a change takes longer than about a second or several fields must commit together.
- Group by topic, not by skill level; avoid "Advanced", "Options", "General". "Using preferences as a band-aid is the root of much UI evil."
- Building blocks are boxed lists of rows in groups on pages (libadwaita).
- Cost: common needs (fonts, startup apps, window buttons) live in a separate Tweaks tool that users must discover.

**KDE**
- Exposes hundreds of options and adds tools to manage them: "Highlight Changed Settings" (Plasma 5.20) marks every value that differs from the default, with per-page Defaults.
- Explicit Apply, a prompt on leaving a page with unapplied changes, and a revert timer for display changes. Users defend Apply as protection against stray scrolls and clicks; others want instant apply for trivial settings.
- KDE's own tracker lists the cost: too many sidebar items, an "overwhelming" feel, keyword-only search. Bug reports show the highlight feature is uneven across pages.

**The contrast:** GNOME shrinks the surface and hides the rest; KDE shows everything and gives tools to cope. A professional audio app is closer to KDE in volume, so it needs KDE's tools (changed markers, defaults, search) with GNOME's discipline about what gets in.

### 2.3 Apps

**VS Code: the reference for many settings**
- One editor with a search field, a category tree, and a "Commonly Used" group on top. The same data as `settings.json`, one command away, with autocomplete.
- Search filters: `@modified`, `@ext:`, `@feature:`, `@id:`, `@lang:`, `@tag:`. Advanced settings stay hidden unless asked for with `@tag:advanced`.
- Instant apply.
- Scopes: Default, User, Workspace and more, later wins. Changed settings get a coloured bar on the left; a hint says "Modified elsewhere" when another scope overrides.
- Per-setting gear: Reset Setting, Copy Setting ID, Copy as JSON, Copy settings URL (`vscode://settings/<name>`).
- Profiles bundle everything and export to one file. Settings Sync leaves machine-specific settings out, keeps backups, and offers a merge on conflict.
- Known failure (issue #50827): a user saw the default in the Workspace tab while the User value was the one acting, and could not tell why. Showing a scope's default as if it were set there misleads.

**JetBrains**
- One dialog, search plus category tree, explicit OK / Apply / Cancel. An icon marks settings that apply only to the current project. Search Everywhere (double Shift) reaches settings, and typing `/` lists settings groups.
- Keymaps: built-in ones are read-only, editing makes a child copy, "Find Action by Shortcut" searches by pressing the keys.
- Sync through the account by category, plus export as ZIP with checkboxes for what to include.
- **GUESS:** search highlights the matching control, modified values show in blue, and boolean settings toggle directly from the search list. Widely described, not confirmed in the pages read.

**Figma UI3**
- Figma's own post on the beta: floating panels "slowed people down", and hiding blend mode behind an icon and moving Clip content into a dropdown each added clicks. They reversed all three.
- Lesson: professionals object to extra clicks on frequent toggles and to state hidden behind icons.

**Linear**
- Blog post "Settings are not a design failure": get defaults right, but some things are "simply a matter of taste". Users sent screenshots of settings pages when something misbehaved, so Linear treats settings as a place that also explains what the product can do.
- **GUESS:** full page with sidebar, reachable from the command menu, instant save.

**Raycast**
- One window with tabs; Cmd+F searches all settings. Extensions list with the selected item's preferences beside it. Hotkeys are recorded inline and saved at once.
- Required preferences are asked for the first time a command runs, with help text beside the form, not at install.
- Whole configuration exports and imports as a file.

**Slack**
- Global notification defaults in Preferences; per-channel overrides are set in the channel and listed centrally under "Exceptions to the defaults", each with a button that returns it to the default. A model for local overrides with one audit list.

**Discord**
- November 2025: settings moved from a full-screen takeover to a floating window, with a search field that also narrows the sidebar. December 2025 patch notes mention a fix for searches that showed empty categories.

**Obsidian**
- Sidebar: Options, Core plugins, Community plugins; each plugin brings its own page. Hotkeys page with search, an assigned-only filter, conflicts in red with a count.
- All settings sit in a `.obsidian` folder inside the vault, so they travel with the project.

**Arc, Notion, Spotify**
- Arc: a profile scopes logins, history and settings to one or more Spaces. Notion: personal settings split from workspace settings; risky actions have their own buttons.
- Spotify: not verified. **GUESS:** one long scrolling page with search and complaints about finding things.

### 2.4 Creative tools

**Blender**
- Preferences with a left sidebar (Interface, Themes, Viewport, Input, Keymap, Add-ons, System, Save & Load, File Paths). A small menu holds Save Preferences, Revert to Saved, Load Factory Preferences and the Auto-Save toggle.
- Keymap editor: presets (including "Industry Compatible"), filter by name or by key binding, export of only the changed bindings as a "delta", restore per section.
- **GUESS (manual pages blocked):** right-click any property for "Reset to Default Value", Backspace over a field resets it; scene and render settings are per file in the Properties editor. Criticism that conflicts are not flagged and add-on preferences are buried.

**Photoshop**
- Opened pages gave little. **GUESS (well known):** modal dialog with a category list and OK / Cancel; a Performance page that shows available RAM, an "Ideal Range" and a slider, with the detected GPU beside it; many changes need a restart, flagged inconsistently.
- Worth copying: telling the user the safe range of a risky resource slider, and showing the detected hardware next to the setting.

**Final Cut Pro**
- Five panes only (General, Editing, Playback, Import, Destinations). Reset by holding keys at launch, which first writes a backup of the old settings. Settings move by copying one file.
- **GUESS:** it stays small because everything about a project lives with the project in the inspector.

**DaVinci Resolve**
- Preferences split into System (hardware) and User (workflow, keyboard); Project Settings open from the cog at the bottom right. Stated order: system, then user, then project.
- Criticism: after the split "it looked like half the settings had been removed"; project preset logic is "completely undiscoverable"; the timeline frame rate locks once media is added. Even the manual mislabels the Preferences steps as Project Settings.
- Lesson: the three-way split is right, but it needs signposts ("this moved to...") and a visible scope on each setting.

### 2.5 Games

- **Gears Tactics** (PC Gamer: "the best graphics option menus I've ever seen"): a preview image that updates as you change a setting, one plain sentence per setting, notched sliders, an estimate per setting of GPU, CPU and memory load, and a built-in benchmark with a graph.
- **Resident Evil 2 remake:** a screenshot per setting, bars for how demanding each one is, and a graphics-memory total that changes live.
- **GTA V:** a video memory bar at the top of the graphics page.
- **Accessibility presets:** The Last of Us Part II has 60+ options and three presets that switch on bundles which stay editable one by one. God of War Ragnarök has four presets with Off / Some / Full, shows settings a preset changed in blue, and has hold-to-reset-all.
- **Xbox Accessibility Guideline 114:** always show where the user is in the hierarchy, give help text per control, preview "in realistic context", keep wording simple with a glossary for jargon.
- **Game Accessibility Guidelines:** let settings be saved as profiles.
- **GUESS (common, not confirmed here):** quality presets that flip to "Custom" when one option changes; "Keep these display settings? Reverting in 15 s"; reset per tab; accessibility choices on first boot.

### 2.6 Cameras and cars

- **Sony:** the old menus were "labyrinthine". The redesign (A7S III) shows three levels at once in vertical tabs and changes options with the mode. Cryptic abbreviations survive ("Emph disp dur REC").
- **Fujifilm Q menu:** a 16-slot grid the user fills from about 30 options. Quick changes do not overwrite the saved bank, and values that differ from the bank show in red.
- **Canon C1 to C3:** "Register settings" stores the camera's whole state in a mode; "Auto update" decides whether later tweaks stick.
- **Pattern:** a user-curated quick panel, a full deep menu, and named banks with visible "changed" marks.
- **Cars:** Euro NCAP now rewards direct physical controls for basic functions, "not buried in touchscreen menus". VW is bringing buttons back for "the five most important functions".
- For a DAW: transport, monitoring, metronome, input gain and latency read-out must never live only in a settings window.

### 2.7 Design-system guidance and UX research

**What belongs in settings**
- Apple: general, rarely changed options, because people "must suspend what they're doing" to get there. Task options stay in the screen they affect; a separate area "disconnects it from its context". "Minimize the number of settings you offer." Do not ask for what you can detect.
- Microsoft: options that "don't require frequent readjustment". Workflow commands (brush size) do not belong.
- macOS specifics: Cmd+comma, a fixed row of panes, window title equal to the pane, reopen on the last pane.

**Defaults**
- NN/g: users stick with defaults; "Assume that users will not change defaults".
- Jared Spool's Word study: "Less than 5% of the users we surveyed had changed any settings at all"; users assumed autosave was off for a reason. It is a 2011 blog post about an older study with no published data, so treat it as an anecdote. In the same account, programmers and designers changed 40 to 80% of settings: professionals are the exception.
- Havoc Pennington: every preference "has a price" (more bugs, fewer real features, harder to find any). Alex Limi: options are often an unresolved team argument, and old Firefox checkboxes let users break the product with no hint how to recover.

**Toggles versus checkboxes**
- NN/g, Microsoft and Material agree: a switch takes effect at once and never needs Save. If a Save step is needed, use a checkbox.
- Apple on macOS: a switch to turn a whole group on or off, checkboxes for a hierarchy of options, radio buttons for 2 to 5 exclusive choices, a pop-up menu beyond that.
- Labels: short nouns that describe the on state, not questions; the label does not change with the state.

**Instant apply versus Apply buttons**
- Microsoft: "don't require a confirmation button". GNOME: instant "wherever possible".
- Explicit apply is justified when a change is slow or several values must commit together; then group those controls with their own Apply (GNOME).
- GitHub Primer: switches save themselves, text fields save explicitly, and "Avoid mixing explicit and automatic save patterns on a single page".
- KDE users add the stray-scroll argument for Apply, and the timed "keep these settings?" revert for risky changes.

**Reset and changed markers**
- Three levels exist in practice: per setting (VS Code gear, KDE indicator that resets on click), per page (KDE Defaults, game tabs), everything (Blender factory preferences, Final Cut reset that writes a backup first).
- Old Windows guidance: offer Restore Defaults when settings are complex or a wrong value breaks things, and confirm when the effect is not obvious.

**Dangerous settings**
- NN/g: confirm only for serious consequences; name the action and what it does; label buttons with outcomes; "Go to great lengths to provide undo".
- Primer and Smashing: scale friction to the damage. Undo for reversible actions, a danger zone and typed confirmation only for irreversible, wide-impact ones.
- Firefox about:config: a warning gate, name search, changed values in bold, reset per value. A model for an expert layer.
- Restart-required settings: no authoritative guidance found. **GUESS:** label the setting in place and offer "Restart now / Later".

**Progressive disclosure**
- Nielsen (2026 rewrite): the first level should serve about 80% of tasks, split by frequency of use, use specific labels ("Advanced color settings", not "More options"), stop at two levels.
- Microsoft: no expander nested deeper than one level.
- Baymard (from e-commerce accounts): collapsed details performed as badly as missing ones. Hiding has a cost.

**Onboarding versus settings**
- NN/g: "avoid creating app onboarding whenever possible"; ask only what is needed to start. Apple: "Postpone nonessential setup flows".
- Raycast asks for a required value at the moment the command first needs it.
- **GUESS for a DAW:** the audio device is the one thing that cannot be defaulted safely on every machine, so it is the only candidate for a first-run question.

**Scope: per project versus global**
- Git is the cleanest mental model: system, global, local, last one wins, and a command that shows where a value comes from.
- Apple: document options go with the document (File menu), app options in the app menu.
- **GUESS (synthesis):** wherever a value can be overridden, show the value in force and where it comes from.

**Sync, export, files**
- VS Code and JetBrains: sync by category, machine-specific settings excluded, export as one file with a choice of contents.
- Obsidian: settings as readable files in the project folder. Resolve was criticised for years for having no export of user preferences.

**Contextual versus central, and deep links**
- Rule of thumb from Apple and Microsoft (**GUESS** on the wording): frequent and local goes in place; rare and app-wide goes in the central window; per document goes with the document.
- Deep links exist everywhere serious: `vscode://settings/<name>`, Windows `ms-settings:` addresses, iOS `openSettingsURLString`, Raycast `openCommandPreferences()`. Microsoft: when the app cannot reach a resource, give "a convenient link to the privacy settings for that resource".
- VS Code: right-click an action, Configure Keybinding opens the shortcut editor already filtered.
- Chrome's settings search highlights the match and puts a marker on parent rows whose subpage holds the hit.

**Command palettes**
- Superhuman's rules: available everywhere, the one place for every command, tolerant of typos and synonyms, best match first, shortcuts shown so the palette teaches them.
- Maggie Appleton: the user "need only remember its name", not the location.
- Retool: a "Top result" row so grouping does not bury the best match.

**Findability with hundreds of settings**
- ChromeOS keeps a file of search tags per setting: Audio is also found by "Volume", "Sound", "Speakers", "Microphone".
- Chrome and Firefox search the full text of every page, including sub-dialogs, and highlight the hit.
- VS Code's `@modified` answers "what did I change?", the question people have when something misbehaves.
- No source found for "recently changed" lists. **GUESS:** worth testing, since `@modified` is the closest shipped form.

**Shortcut editors**
- The good ones share five things: search by action name and by pressing the keys, conflict display, presets from other apps, export of only the changes, restore per section (VS Code, JetBrains, Blender, Obsidian).

**Accessibility and keyboard (WAI-ARIA practices)**
- Switch: `role="switch"`, Space toggles, helper text attached to the control.
- Category list as a tree or vertical tabs: Up and Down move, Right and Left open and close, Home and End jump, type-ahead finds.
- Dialog: focus moves in on open, Tab stays inside, Escape closes, focus returns to where it came from.
- Apple: never rely on colour alone to show a state.

## 3. Patterns that work, patterns that fail

**Work**

| Pattern | Examples |
| --- | --- |
| Search that matches synonyms and descriptions, shows the path, and highlights the control | ChromeOS search tags, Chrome, Firefox, Android, VS Code |
| Changed-from-default marker with one-click reset | VS Code, KDE, God of War Ragnarök, Fujifilm |
| "Show only what I changed" filter | VS Code `@modified`, Slack exceptions list |
| Row shows the current value, not a description | Material, Android |
| Cost read-out per setting and a live total | Gears Tactics, Resident Evil 2, GTA V, Photoshop RAM range |
| Presets that set a bundle and stay editable | Game quality presets, The Last of Us Part II, Canon C1 to C3 |
| Scope split with a visible marker | Resolve, Final Cut, JetBrains project icon, VS Code |
| Timed revert for changes that can lock you out | KDE display settings, games (**GUESS** for games) |
| Deep link from the place of use to the exact setting | VS Code, Windows, Raycast |
| Readable settings files, export, profiles | VS Code, Obsidian, Raycast, JetBrains |
| User-curated quick panel over a deep menu | Fujifilm Q menu, VS Code "Commonly Used" |
| Ask at the moment of need | Raycast required preferences |
| Persistent sidebar plus breadcrumbs | Windows 11 |

**Fail**

| Pattern | Examples |
| --- | --- |
| Narrow scrolling column on a wide screen, fixed window size | macOS Ventura System Settings |
| Two homes for one setting, half-finished migration | Windows Settings and Control Panel |
| "Advanced", "General", "Other" as dumping grounds | macOS, criticised by GNOME and Material rules |
| A second hidden tool for common needs | GNOME Tweaks |
| Scope confusion: the wrong value shown as if in force | VS Code issue #50827, Resolve's three places |
| Options that break the product with no way back | Old Firefox checkboxes (Limi) |
| Extra clicks on frequent toggles, state hidden behind icons | Figma UI3 beta, car touchscreens |
| Search that returns dead or irrelevant results | macOS, iOS |
| Switches used where checkboxes fit, labels not clickable | macOS Ventura |
| Filler or upsell on the settings home | Windows 11 Home page |
| Moving things without a signpost | Resolve 14, iOS and macOS reshuffles |
| Cryptic abbreviations | Sony "Emph disp dur REC" |
| Mixed save models on one page | Named as a fault by Primer |

## 4. Principles for AudioLab

Thirteen principles for a settings design that feels smart and sciencey, clear, intuitive and snappy. Each follows from the findings above; the application to a DAW is my synthesis.

1. **Fewer, better defaults first.** Before adding a setting, try to fix the behaviour or detect the answer. Every setting that stays must have a default that is right for most people, because most will never change it.
2. **Three scopes, always labelled: this computer, me, this project.** Audio device and buffer belong to the computer; appearance, shortcuts and workflow belong to the user; tempo, sample rate and routing belong to the project. Every row shows which scope it is, and project values are never mixed into the user list.
3. **Used while working means not in settings.** Transport, monitoring, metronome, meter options and anything changed mid-session sit on the surface, with a quick panel the user can fill for the rest. The settings window is for what is set once.
4. **Everything applies at once; risky changes revert themselves.** No Apply or OK button. Changes that can cut the sound (device, sample rate, buffer) take effect immediately and offer "Keep / Revert" with a countdown. One save model across the whole window.
5. **Every row shows its value, its unit and its cost.** Buffer size shows the resulting latency in ms; quality options show CPU or memory cost; a live read-out at the top of the audio page sums it up. This is the "sciencey" part: measured numbers in place of adjectives.
6. **Preview live.** Appearance, meter and glass settings change the app behind the window as the control moves, so the window must not cover the whole app.
7. **Changed is visible, reset is one click.** A mark on every value that differs from the default, reset per setting from that mark, reset per page, and a full reset that first saves a backup. A "Changed" filter lists everything the user has touched.
8. **Search is the main way in, and it is forgiving.** One field, focused on open, matching names, descriptions and synonyms ("latency" finds buffer size, "sound card" finds audio device). Results show the page they live on; choosing one scrolls to the control and flashes it.
9. **One home per setting, many doors.** Each setting lives in exactly one place. Right-click on a meter, a device or a panel offers "Settings for this..." and lands on that exact row; error messages link to the setting that fixes them.
10. **Settings are also commands.** The command palette can open any setting by name and flip any on/off setting directly, showing the new state.
11. **Group by what the musician is doing, two levels at most.** Page names are tasks and things (Audio, MIDI, Appearance, Shortcuts, Files), never "General", "Advanced" or "Other". Rare expert options sit in a named, collapsed group on the page they belong to, with one line saying what is inside.
12. **Plain words, consequences stated, danger separated.** One short sentence per setting in the user's terms, jargon explained on hover. Settings that delete data or need a restart say so in the row, and destructive actions sit apart with friction in proportion to the damage and an undo wherever possible.
13. **Portable and fully keyboard-driven.** Settings are stored in a readable file, export and import as one file, and can be saved as named profiles (studio, laptop, live). Every control works from the keyboard: Cmd/Ctrl+comma opens, arrows move through pages, Escape closes and returns focus.

## 5. Layouts worth testing

For the multiple-choice round. Each can be mocked with the same real settings so the comparison is fair.

| Layout | What it is | Strength | Risk | Seen in |
| --- | --- | --- | --- | --- |
| A. Sidebar plus pages | Category list on the left, one page on the right, search on top | Familiar, scales to many pages, sidebar always visible | Becomes the Ventura scrolling list if pages are long and the window narrow | VS Code, Windows 11, Discord, Obsidian, Blender |
| B. Search-first | Opens on a search field with "Commonly used" and "Changed" below; categories are secondary | Fastest for people who know what they want; fits the command palette | Poor for browsing and for learning what exists | VS Code filters, Raycast, command palettes |
| C. Grouped cards | Each page is a wide grid of titled cards, each card a group with values and read-outs | Uses the width, gives the overview Ventura lost, room for live meters and graphs | Needs care to keep scanning order clear; long groups break the grid | Windows SettingsCard, game menus with preview pane |
| D. Tabs across the top | Five to seven fixed panes in a top row | Very clear when the count is small | Does not scale; forces dumping grounds when settings grow | Final Cut Pro, classic macOS, Raycast |
| E. Inspector style | No central window for most things: a side panel shows the settings of whatever is selected (device, track, meter, project), with a small central window for the rest | Settings stay in context with instant feedback; nothing covers the app | Global options need a second home; harder to search as a whole | Final Cut and Resolve inspectors, Figma, Blender Properties |

Combinations worth a mock: **A with C** (sidebar, pages built from cards, live read-out strip), and **E with a small B** (inspector for context, search-first window for the rest). A split view with the preview on the right, as in Gears Tactics, can be added to A or C for the audio and appearance pages.

## 6. Sources

Read unless marked "search result only". One line on what each supports.

**Phones**
- [Apple HIG: Settings](https://developer.apple.com/design/human-interface-guidelines/settings.md): what belongs in settings, defaults, macOS window rules.
- [9to5Mac: iOS 18 Settings](https://9to5mac.com/2024/09/18/ios-18-settings-whats-new/): Apps section, headers, search suggestions.
- [AppleInsider: New Settings in iOS 18](https://appleinsider.com/inside/ios-18/tips/new-settings-in-ios-18-will-take-some-getting-used-to): reader friction with the Apps section.
- [TidBITS: Alphabetize Settings in iOS](https://tidbits.com/2018/02/21/bad-apple-2-alphabetize-settings-in-ios/): 1200+ items, arbitrary grouping, weak search.
- [MacRumors: iOS 9 hidden features](https://www.macrumors.com/2015/09/16/ios-9-hidden-features/): Settings search in iOS 9 (search result only).
- [Material Design 1: Settings pattern](https://m1.material.io/patterns/settings.html): placement, exclusions, 15-item threshold, label rules.
- [Android Developers: Settings pattern](https://developer.android.com/design/ui/mobile/guides/patterns/settings): current rules, list plus detail, dependencies, search.
- [AOSP Settings design guidelines](https://source.android.com/docs/core/settings/settings-guidelines): 10 to 15 items, Advanced collapse, breadcrumbs in search.
- [Android: Customize your settings](https://developer.android.com/guide/topics/ui/settings/customize-your-settings): summaries show the current value.
- [Samsung One UI: Basic layout](https://developer.samsung.com/one-ui/layout/basic.html): viewing and interaction areas.
- [Samsung One UI: List](https://developer.samsung.com/one-ui/comp/list.html): setting names and subtext.

**Operating systems**
- [Michael Tsai: System Settings (2022)](https://mjtsai.com/blog/2022/06/08/system-settings/): roundup of named Ventura criticisms.
- [Six Colors: making Ventura System Settings better](https://sixcolors.com/post/2022/08/ways-to-make-macos-ventura-system-settings-better/): Snell's critiques and fixes.
- [Eclectic Light: a turn for the worse?](https://eclecticlight.co/2022/09/20/system-settings-in-ventura-a-turn-for-the-worse/): buried settings, improved search.
- [Michael Tsai: System Settings in Sequoia](https://mjtsai.com/blog/2024/07/19/system-settings-in-sequoia): reshuffle and continuing complaints.
- [Neowin: Settings app UI in Windows 11](https://www.neowin.net/news/closer-look-settings-app-ui-in-windows-11/): left navigation, breadcrumbs, nesting.
- [PC Gamer: old menus in Windows 11](https://www.pcgamer.com/uk/i-cant-believe-windows-11-still-hasnt-gotten-rid-of-these-old-ass-menus/): duplicated and legacy dialogs.
- [Pureinfotech: Control Panel transition](https://pureinfotech.com/windows-11-control-panel-transition/): Microsoft's compatibility reason.
- [ghacks: Settings homepage](https://www.ghacks.net/2023/08/25/windows-11s-new-settings-homepage-is-half-promotion-half-pointless): Home cards and upsell.
- [Windows Central: Settings in 24H2/25H2](https://www.windowscentral.com/microsoft/windows-11/settings-apps-best-features-available-in-2025-on-windows-11-version-25H2-and-24H2): search move, settings agent.
- [GNOME wiki: HIG planning, Configuration](https://wiki.gnome.org/Design/HIG/Planning/Configuration): instant apply, when Apply is allowed, grouping.
- [GNOME Discourse: graduating Tweaks features](https://discourse.gnome.org/t/proposal-graduating-essential-gnome-tweaks-features-into-main-settings-for-better-ux/33607): why options stay out of Settings.
- [Nate Graham: Highlight changed settings](https://pointieststick.com/2020/08/14/this-week-in-kde-highlight-changed-settings-and-much-much-more/): the KDE feature.
- [KDE D27540](https://phabricator.kde.org/D27540): differs-from-default indicator that resets on click.
- [KDE Discuss: why settings don't auto-apply](https://discuss.kde.org/t/why-wont-settings-automatically-apply-changes/51669.md): Apply versus instant apply.
- [KDE systemsettings issue 25](https://invent.kde.org/plasma/systemsettings/-/issues/25): KDE's own list of problems.
- [KDE HIG: Simple by default](https://develop.kde.org/hig/simple_by_default/): default-setting rules.

**Apps**
- [VS Code: User and workspace settings](https://code.visualstudio.com/docs/configure/settings): layout, filters, gear menu, scopes, settings URL.
- [VS Code 1.69 release notes](https://code.visualstudio.com/updates/v1_69): "Modified elsewhere" indicator.
- [VS Code issue #50827](https://github.com/microsoft/vscode/issues/50827): scope-confusion failure case.
- [VS Code: Profiles](https://code.visualstudio.com/docs/configure/profiles): profile contents and export.
- [VS Code: Settings Sync](https://code.visualstudio.com/docs/configure/settings-sync): what syncs, machine scope, conflicts, backups.
- [VS Code: Keybindings](https://code.visualstudio.com/docs/configure/keybindings.md): shortcut editor, conflicts, keymaps.
- [VS Code 1.26 release notes](https://code.visualstudio.com/updates/v1_26): the settings editor preview.
- [dev.to: All new VS Code settings editor UI](https://dev.to/vscode/all-new-vscode-settings-editor-ui-----3j48): default in 1.27, modified line.
- [JetBrains: Settings dialog](https://jetbrains.com/help/idea/settings-preferences-dialog.html): search, tree, project icon, OK/Apply/Cancel.
- [JetBrains: project and IDE settings](https://jetbrains.com/help/idea/configuring-project-and-ide-settings.html): global versus project.
- [JetBrains: Search Everywhere](https://www.jetbrains.com/help/idea/searching-everywhere.html.md): settings from search.
- [JetBrains: Keymap settings](https://www.jetbrains.com/help/idea/settings-keymap.html): copy-on-modify keymaps, find by shortcut.
- [JetBrains: settings backup and sync](https://www.jetbrains.com/help/idea/sharing-your-ide-settings.html.md): sync categories, ZIP export.
- [Figma: Our approach to designing UI3](https://www.figma.com/blog/our-approach-to-designing-ui3/): beta criticism and reversals.
- [Figma help: Navigating UI3](https://help.figma.com/hc/articles/23954856027159): what moved where.
- [Linear: Settings are not a design failure](https://linear.app/blog/settings-are-not-a-design-failure): philosophy, settings as education.
- [Linear docs: Preferences](https://linear.app/docs/account-preferences): preference sections.
- [Raycast manual: Settings](https://manual.raycast.com/settings): tabs, extensions, export.
- [Raycast manual: aliases and hotkeys](https://manual.raycast.com/command-aliases-and-hotkeys): inline alias, hotkey recorder.
- [Raycast API: Preferences](https://developers.raycast.com/api-reference/preferences): required preferences on first run, deep-link functions.
- [Arc help: Profiles](https://resources.arc.net/hc/en-us/articles/19227964556183): profiles versus spaces.
- [Notion help: Account settings](https://www.notion.com/help/account-settings): personal versus workspace.
- [Slack help: channel notifications](https://slack.com/intl/en-ie/help/articles/360056534254-Manage-notifications-for-specific-channels-and-direct-messages): "Exceptions to the defaults".
- [Discord changelog, Nov 6 2025](https://discord.com/blog/a-cornucopia-of-updates-make-discord-on-desktop-fresher-than-a-crisp-fall-breeze): floating settings window, search.
- [Discord patch notes, Dec 8 2025](https://discord.com/blog/discord-patch-notes-december-8-2025): redesign shipped, search fix.
- [Spotify community: Where are the settings](https://community.spotify.com/t5/App-Features/Where-are-the-settings-in-the-new-desktop-interface/m-p/5571729/highlight/true): complaint thread (search result only).
- [Obsidian help: Settings](https://obsidian.md/help/settings): sections, plugin pages, hotkey search.
- [Obsidian help: Configuration folder](https://obsidian.md/help/configuration-folder): per-vault settings folder.
- [Obsidian forum: hotkey conflicts](https://forum.obsidian.md/t/implemented-v1-13-hotkeys-click-on-n-commands-with-conflicts-to-show-all-hotkey-conflicts/84829): conflict display.

**Creative tools**
- [Blender manual: Keymap preferences](https://docs.blender.org/manual/en/4.2/editors/preferences/keymap.html): presets, delta export, search by key.
- [Brandon3D: Blender Preferences guide](https://brandon3d.com/blender-preferences/): sections, save menu, auto-save.
- [Adobe: Photoshop performance preferences](https://helpx.adobe.com/photoshop/desktop/get-started/settings-and-preferences/configure-photoshop-performance-preferences.html): performance page (search result only).
- [Apple: Change settings in Final Cut Pro](https://support.apple.com/guide/final-cut-pro/ver8e3f2f66/mac): five panes, reset with backup.
- [Mixing Light: Resolve 14 preferences overhaul](https://mixinglight.com/color-tutorial/davinci-resolve-14-public-beta-7/): System/User split and the confusion.
- [Mixing Light: Project Presets in Resolve](https://mixinglight.com/color-tutorial/project-presets-in-davinci-resolve/): "undiscoverable" presets, frame-rate lock.
- [DaVinci Resolve 18.6 manual, Preferences](https://www.steakunderwater.com/VFXPedia/__man/Resolve18-6/DaVinciResolve18_Manual_files/part117.htm): panes, mislabelled heading (unofficial mirror).
- [PremiumBeat: Resolve basic settings](https://www.premiumbeat.com/blog/davinci-resolve-15-basic-settings/): project settings cog.

**Games, cameras, cars**
- [PC Gamer: Gears Tactics graphics menus](https://www.pcgamer.com/gears-tactics-has-the-best-graphics-option-menus-ive-ever-seen-and-every-game-should-copy-them): preview, descriptions, load estimates, benchmark.
- [Kotaku: Resident Evil 2 graphics menu](https://kotaku.com/resident-evil-2-remake-on-pc-has-a-fantastic-graphics-m-1832085885): screenshots, demand bars, live memory.
- [WCCFtech: GTA V PC graphics settings](https://wccftech.com/gta-v-pc-graphics-settings-detailed-supports-nvidia-txaa-nvidia-pcss-and-amd-chs/): video memory bar.
- [PlayStation Blog: The Last of Us Part II accessibility](https://blog.playstation.com/2020/06/09/the-last-of-us-part-ii-accessibility-features-detailed): presets and option count.
- [PlayStation: God of War Ragnarök accessibility](https://www.playstation.com/en-us/games/god-of-war-ragnarok/accessibility/): tiered presets, blue changed markers.
- [Xbox Accessibility Guideline 114](https://learn.microsoft.com/en-us/gaming/accessibility/xbox-accessibility-guidelines/114): hierarchy, help text, previews.
- [Game Accessibility Guidelines: settings profiles](https://gameaccessibilityguidelines.com/allow-settings-to-be-saved-to-different-profiles-at-either-game-or-platform-level/): profiles.
- [Digital Camera World: Sony new menus](https://www.digitalcameraworld.com/news/finally-sony-fixed-the-camera-menus): redesign and old criticism.
- [Fujifilm X-T3 manual: Q button](https://fujifilm-dsc.com/en/manual/x-t3/shortcuts/q_button/index.html): 16 slots, banks, red markers.
- [Canon manual: Custom Shooting Mode](https://cam.start.canon/en/C005/manual/html/UG-08_Set-up_0330.html): register, auto update, clear.
- [Euro NCAP: Buttons are back for basic functions](https://www.euroncap.com/en/press-media/buttons-are-back-for-basic-functions-euro-ncap-confirms-in-testing/): physical controls scored.
- [Autocar: VW reintroducing physical controls](https://www.autocar.co.uk/car-news/new-cars/volkswagen-reintroducing-physical-controls-vital-functions): five functions get buttons.

**Guidance and research**
- [Apple HIG: Toggles](https://developer.apple.com/design/human-interface-guidelines/toggles.md): switch, checkbox, radio on macOS.
- [Apple HIG: Onboarding](https://developer.apple.com/design/human-interface-guidelines/onboarding.md): postpone setup.
- [Material Components Android: Switch](https://github.com/material-components/material-components-android/blob/master/docs/components/Switch.md): switches act immediately.
- [Microsoft: Guidelines for app settings](https://learn.microsoft.com/en-us/windows/apps/design/app-settings/guidelines-for-app-settings): what belongs, instant apply, layout, nesting.
- [Microsoft: Toggle switches](https://learn.microsoft.com/en-us/windows/apps/design/controls/toggles): toggle versus checkbox.
- [Windows Community Toolkit: SettingsCard](https://learn.microsoft.com/en-us/dotnet/communitytoolkit/windows/settingscontrols/settingscard): card anatomy.
- [Microsoft: Launch Windows Settings](https://learn.microsoft.com/en-us/windows/apps/develop/launch/launch-settings): `ms-settings:` links from errors.
- [Win32 UX guide: Property windows](https://learn.microsoft.com/en-ie/Windows/Win32/uxguide/win-property-win): OK/Cancel/Apply, Restore Defaults.
- [Win32 UX guide: Control panels](https://learn.microsoft.com/en-ie/Windows/Win32/uxguide/winenv-ctrl-panels): immediate versus delayed commit.
- [NN/g: Toggle-switch guidelines](https://www.nngroup.com/articles/toggle-switch-guidelines/): immediate effect, labels.
- [NN/g: The Power of Defaults](https://www.nngroup.com/articles/the-power-of-defaults/): default bias.
- [NN/g video: The Danger of Defaults](https://www.nngroup.com/videos/the-danger-of-defaults/): assume defaults stay.
- [NN/g: Customization vs personalization](https://www.nngroup.com/articles/customization-personalization/): most users will not tweak.
- [NN/g: Confirmation dialogs](https://www.nngroup.com/articles/confirmation-dialog/): when and how to confirm.
- [NN/g: User control and freedom](https://www.nngroup.com/articles/user-control-and-freedom/): exit, cancel, undo.
- [NN/g: Mobile-App Onboarding](https://www.nngroup.com/articles/mobile-app-onboarding/): avoid onboarding, ask only what is needed.
- [NN/g: Progressive disclosure](https://nngroup.com/articles/progressive-disclosure/): could not be loaded (search result only).
- [Nielsen, UX Tigers: Progressive Disclosure](https://uxtigers.com/post/progressive-disclosure): 80% rule, two levels, specific labels.
- [Spool: Do users change their settings?](https://archive.uie.com/brainsparks/2011/09/14/do-users-change-their-settings/): the under-5% Word claim.
- [Pennington: Free software UI](https://ometer.com/preferences): every preference has a price.
- [Limi: Checkboxes that kill your product](https://limi.net/checkboxes): options that break the product.
- [Tanya Donska: When your settings page becomes the product](https://dev.to/tanya-donska/when-your-settings-page-becomes-the-product-1824): settings sprawl, honest "Advanced".
- [Primer: Saving](https://primer.style/ui-patterns/saving): automatic versus explicit save.
- [Primer: Delete pattern](https://primer.style/product/scenario-patterns/delete): danger zone, friction scaling.
- [Smashing: Dangerous actions](https://www.smashingmagazine.com/2024/09/how-manage-dangerous-actions-user-interfaces): confirmation range, undo versus confirm.
- [Baymard: Accounts and self-service](https://baymard.com/research-articles/accounts-and-self-service-ux-research-2026): collapsed details, findability.
- [git-config docs](https://git-scm.com/docs/git-config/2.43.0): scope levels and showing a value's origin.
- [Mozilla: Configuration Editor](https://support.mozilla.org/en-US/kb/about-config-editor-firefox): expert layer with warning gate.
- [Mozilla bug 1363721](https://bugzilla.mozilla.org/show_bug.cgi?id=1363721): search highlighting in sub-dialogs.
- [Chromium search_settings.ts](https://chromium.googlesource.com/chromium/src/+/cff8ad5/chrome/browser/resources/settings/search_settings.ts): full-text settings search with highlights.
- [ChromeOS settings search tags](https://chromium.googlesource.com/chromium/src/+/lkgr/chrome/app/os_settings_search_tag_strings.grdp): synonym tags per setting.
- [Apple Developer Forums thread 761314](https://developer.apple.com/forums/thread/761314): supported ways to open settings.
- [Superhuman: remarkable command palette](https://blog.superhuman.com/how-to-build-a-remarkable-command-palette/): five palette rules.
- [Maggie Appleton: Command K Bars](https://maggieappleton.com/command-bar): the pattern and its benefits.
- [Retool: Designing the command palette](https://retool.com/blog/designing-the-command-palette): top result, scoping.
- [WAI-ARIA practices: Switch](https://w3.org/WAI/ARIA/apg/patterns/switch): role, keys, labels.
- [WAI-ARIA practices: Tabs](https://w3.org/WAI/ARIA/apg/patterns/tabs/): keyboard and activation.
- [WAI-ARIA practices: Tree view](https://www.w3.org/WAI/ARIA/apg/patterns/treeview/): keyboard for a category tree.
- [WAI-ARIA practices: Modal dialog](https://www.w3.org/WAI/ARIA/apg/patterns/dialogmodal/): focus management.

**Gaps:** no usable source for settings search in specific games, Chrome flags, Photoshop's dialog details, Blender's reset gestures, Spotify, or "recently changed" lists. Those points are marked GUESS above.
