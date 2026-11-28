# AudioLab Pro: menus, dialogs and notifications (design round 5, task DR5, 27 November 2026)

**Pick page: "AudioLab menus, dialogs and notifications"**, https://claude.ai/artifact/D1Ab4rKNMZiCKXKogpJXHq (source `tools/design-lab/dr5/overlays.html`).
To answer, pick one number per family on the page and copy the line from the bar at the bottom, for example `DR5 picks: R1 D1 T1 N1 X1 K1`. ★ marks the recommendation.

**Scope.** This round covers everything that floats over the work:
- right-click menus, the main (logo) menu, dropdowns and pickers;
- dialogs: askChoice, askText, Export and Bounce, Audio to MIDI, the stem splitter, the update window, unsaved-changes and confirm dialogs;
- sheets;
- tooltips and the help line;
- toasts and notifications;
- drag-and-drop feedback and drop zones;
- a command palette and a keyboard-shortcut overlay;
- loading and progress states.

Progress uses the **MD1 orbit loader as specified (M2), not a new design**. Empty states and their science drawings are task SC's and are left alone.

**What stays the same:**
- The glass engine draws all glass, with no `backdrop-filter`.
- Today's colours, buttons and icons.
- Inter at 11, 12, 13 and 15.
- The subtle science look.
- Snappiness and low CPU come first.
- The **K12 rule** from the extensions picks: right-click entries that hide or customise a control name it ("Hide the Mute button") and sit in a marked **Advanced** group.

**Nothing in index.html or desktop/ was changed.** This task only wrote this file, `tools/design-lab/dr5/` and the project doc.

## 1. Today (v0.228, headless screenshots and measurements)

Scripts:
- `tools/design-lab/dr5/shots_today.py` opens the Fractals demo at 1600 × 1000 and captures each overlay.
- `tools/design-lab/dr5/measure_today.py` times each open, as the median of 7 runs.

The cloud machine draws in software (SwiftShader), so compare these numbers with each other, not with the Mac.

| Overlay | Where in index.html | How it looks today | Open call (JS) | Click to second frame |
|---|---|---|---|---|
| Right-click menus (about 40 callers) | `openMenu` / `#ctxm`, menus such as `trackMenu`, `clipMenu`, `tabMenu`, logo `Quick actions` | One flat list. 8 px corners, 28 px rows, a blue filled row on hover, shortcut chips, every sub-line always shown, coloured dots, grey heads. The track menu has **27 rows in 5 groups**. No submenus, type-ahead or Advanced group. The first item is focused, but arrow keys are not handled by the menu. | track menu **6.9 ms**, clip menu 3.6 ms | 39 ms, 79 ms |
| askChoice (close project, delete, save) | `askChoice`, `#cdlg` | A centred card with an icon tile and a light dim. Buttons are Cancel on the left, Don't save in red and Save… in blue. Esc cancels and the primary button gets focus. There is no Tab trap. | 0.2 ms | 42 ms |
| askText | `askText`, `#dlg` | A small card with a field (green focus ring) and Cancel / OK. | 0.1 ms | 36 ms |
| Stem splitter | `stemAsk`, `#stq` | A sheet with three engine cards (🧠 and ⚡ emoji as icons), stem check boxes, and Reset / Cancel / Split. | not timed | |
| Audio to MIDI | `openA2M`, `#a2m` | A large modal sheet with the waveform, notes, and Detection and Clean-up columns. | not timed | |
| Update notice | `updCard` | A card at the top right with Later and a green "Restart now". It stays until you answer it. | | |
| Light-mode notice | `liteNotice` | A bar at the top with Turn off and ×. | | |
| Toast | `toast`, `#toast` | Plain text at the bottom centre for **4.2 s**. The next toast replaces it, and there is no history, pause or action. | 0.1 ms | 29 ms |
| Tooltip | `tipShow`, `#tip`, the `TIPS` table | A rich card after **420 ms** every time (title, sentence, sometimes a picture). There is no warm-up, and Esc does not hide it. 112 of 339 controls have none (settings audit). | | |
| Help line | the Map hint row only | "Map · drag the box to move · …". Settings round 1 picked **D4c** (a help line at the foot of the Settings window). | | |
| Drag and drop | `arr` dragover (`FDRAG`), mixer reference slot | A tinted ghost row for a new track. Over an audio track nothing shows where the file lands. Other drop targets give no sign. | | |
| Command palette | none | ⌘K is the **Assistant**. ⌘/ opens Settings › Keyboard shortcuts. `SCA` holds 57 commands with ids, groups, names and keys. | | |

## 2. Research (sources opened on 27 November 2026 by a research helper; anything that could not be opened is marked)

**Apple Human Interface Guidelines**
- Menus ([Menus](https://developer.apple.com/design/human-interface-guidelines/menus)):
  - Use "…" when an item needs more input.
  - Dim unavailable items.
  - Put frequent items first.
  - Keep submenus to one level, and consider a new menu beyond about five items.
  - Use icons on all items of a group or on none.
- Context menus ([Context menus](https://developer.apple.com/design/human-interface-guidelines/context-menus)):
  - Keep them to "a small number" of items and "not more than about three groups".
  - Hide unavailable items.
  - Put the most frequent items nearest the pointer.
  - Show keyboard shortcuts in main menus, not context menus.
  - Every context command must also be in the menu bar.
- Alerts ([Alerts](https://developer.apple.com/design/human-interface-guidelines/alerts)):
  - Up to three buttons.
  - Titles wrap to at most 2 lines.
  - Use specific verbs, never "OK" for a choice.
  - Cancel goes on the leading side and the default button on the trailing side.
  - Esc and ⌘. cancel.
  - A suppression check box is allowed.
- Sheets and popovers ([Sheets](https://developer.apple.com/design/human-interface-guidelines/sheets), [Popovers](https://developer.apple.com/design/human-interface-guidelines/popovers)):
  - A sheet is modal to its window. Show one at a time.
  - Use a panel for repeated input.
  - Show one popover at a time and never use one for a warning.
- Tooltips and progress ([Offering help](https://developer.apple.com/design/human-interface-guidelines/offering-help), [Progress indicators](https://developer.apple.com/design/human-interface-guidelines/progress-indicators)):
  - Tooltips are at most 60–75 characters, start with a verb and don't repeat the control's name.
  - Progress is determinate when the length is known.
  - Never turn a spinner into a bar.
  - Offer Cancel.
- Liquid Glass ([Materials](https://developer.apple.com/design/human-interface-guidelines/materials), [Meet Liquid Glass, WWDC25](https://developer.apple.com/videos/play/wwdc2025/219/)):
  - Glass is for controls and navigation only. Use the regular (frostier) variant for text-heavy alerts and popovers.
  - Never put glass on glass. This is already the engine's layer rule (glass plan 3.10).
  - Reduce Transparency, Increase Contrast and Reduce Motion each change the material.
  - macOS 26 put an icon on every menu item. This was widely criticised, and macOS 27 removes most of them ([MacRumors](https://www.macrumors.com/2026/06/11/macos-27-golden-gate-menu-items/)).
- Motion ([Motion](https://developer.apple.com/design/human-interface-guidelines/motion)): keep motion brief, avoid it on frequent actions, and make it optional.

**Windows 11 and Fluent**
- Motion durations ([Timing and easing](https://learn.microsoft.com/en-us/windows/apps/design/motion/timing-and-easing)):
  - ControlFaster is **83 ms**, ControlFast 167 ms and ControlNormal 250 ms.
  - The entry curve is `cubic-bezier(0,0,0,1)`.
  - The Fluent web token values were not verified.
- [Menus and context menus](https://learn.microsoft.com/en-us/windows/apps/design/controls/menus-and-context-menus): Cut, Copy, Paste and Share go in a horizontal row at the top (CommandBarFlyout). This is option R2 on the pick page.
- [Acrylic](https://learn.microsoft.com/en-us/windows/apps/design/style/acrylic): falls back to solid with Transparency off, on Battery Saver, or when the window is inactive. Our Solid level matches this.
- [Dialogs](https://learn.microsoft.com/en-us/windows/apps/design/controls/dialogs-and-flyouts/dialogs): up to 3 buttons, a safe close button is required, specific labels, Enter for the default and Esc to close.
- [InfoBar](https://learn.microsoft.com/en-us/windows/apps/design/controls/infobar): persistent, never auto-dismissed. Never rely on colour alone.
- [TeachingTip](https://learn.microsoft.com/en-us/windows/apps/design/controls/dialogs-and-flyouts/teaching-tip): people read 3–5 words, so never use one for errors.

**Figma, Linear, Raycast, VS Code**
- Figma UI3 opens Actions with ⌘K ([Use quick actions](https://help.figma.com/hc/en-us/articles/23570416033943-Use-quick-actions)).
- Linear:
  - Command menu on ⌘K, and **?** opens the shortcut help ([Navigating Linear](https://linear.app/enablement/guide/navigating-linear), [changelog](https://linear.app/changelog/2021-03-25-keyboard-shortcuts-help)).
- Raycast:
  - The action panel opens with ⌘K. ↵ runs the first action, shortcuts sit on the right, and fuzzy search flattens the sections ([Action Panel](https://manual.raycast.com/action-panel)).
  - Toasts come in Animated, Success and Failure styles, and fall back to a HUD ([Toast API](https://developers.raycast.com/api-reference/feedback/toast)).
- VS Code:
  - Notifications: show one at a time, combine messages, offer "Do not show again", and put low-priority progress in the status bar ([Notifications](https://code.visualstudio.com/api/ux-guidelines/notifications)).
  - Status bar: short text, no custom colours ([Status Bar](https://code.visualstudio.com/api/ux-guidelines/status-bar)).
  - Quick Pick: a placeholder, "1/3" steps and labelled separators ([Quick Picks](https://code.visualstudio.com/api/ux-guidelines/quick-picks)).
  - Keybindings: a modal editor that also finds conflicts ([Keybindings](https://code.visualstudio.com/docs/configure/keybindings)).

**DAWs and pro audio**
- Ableton:
  - Info View shows "the name and function of whatever element… you hover over". **?** toggles it, and users can edit the info text ([Live 12 First Steps](https://www.ableton.com/en/live-manual/12/first-steps/)).
  - Browser drop into the empty space makes a new track; Shift+Enter previews ([Browser](https://www.ableton.com/live-manual/12/working-with-the-browser/)).
  - The exact "Drop Files and Devices Here" wording was not verified.
- Bitwig: the pop-up browser and its source icons ([Browsers](https://www.bitwig.com/userguide/latest/browsers)), the Inspector that follows the selection ([Inspector](https://bitwig.com/userguide/latest/meet_inspector_panel)), and the Dashboard ([Dashboard](https://www.bitwig.com/userguide/latest/the_dashboard/)).
- Pro Tools bounce: Source, File type, Format, Bit depth, Sample rate, Offline or Real-time ([Avid](https://www.avid.com/pro-tools/user-guide/bouncing-final-mix)).
- Logic bounce: MP3 settings are shown only when needed ([Logic](https://help.apple.com/logicpro/mac/10.2.1/en.lproj/lgcp8314da07.html)).

**Instrument-panel labels**
- FAA flight-deck guidance ([FAA HF guidance, ch. 3.2](https://hfcc.dot.gov/publications/docs/GeneralGuidance/zz_FAA_GeneralGuidanceDoc_Chapter_03_Section_02.html)):
  - All capitals is fine for **labels**. Use mixed case for messages, menus and buttons.
  - One abbreviation per function, and don't abbreviate words of four letters or fewer.
  - Contrast at least 3:1, 7:1 recommended.
- Tektronix TBS2000B ([manual](https://docs.make.rit.edu/Textiles%20&%20Electronics/Electronics%20Equipment/assets/tbs2000/TBS2000BSeriesUserManual.pdf)):
  - Read-outs are always visible, with units ("5 mV per division").
  - Optional "Help Everywhere" overlay, off by default.
- The NASA typography summary was not opened.

**Accessibility**
- WCAG 2.2:
  - 1.4.13 Content on Hover or Focus: dismissible with Esc, hoverable, and persistent ([Understanding](https://www.w3.org/WAI/WCAG22/Understanding/content-on-hover-or-focus.html)).
  - 1.4.11: 3:1 for component states and focus rings ([Understanding](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html)).
  - 2.4.11: the focused item must not be hidden. Toasts sit in unused space ([Understanding](https://www.w3.org/WAI/WCAG22/Understanding/focus-not-obscured-minimum.html)).
  - 2.4.13: the focus ring is at least 2 px with 3:1 contrast ([Understanding](https://www.w3.org/WAI/WCAG22/Understanding/focus-appearance.html)).
  - 2.2.1: a message that disappears must be findable elsewhere or held open ([Understanding](https://www.w3.org/WAI/WCAG22/Understanding/timing-adjustable.html); [Primer, toasts](https://primer.style/accessibility/toasts/)).
  - 2.3.3: motion triggered by an interaction can be turned off. Technique C39 is `prefers-reduced-motion`; replace scale and slide with fades ([Understanding](https://www.w3.org/WAI/WCAG22/Understanding/animation-from-interactions.html), [MDN](https://developer.mozilla.org/en-US/docs/Web/CSS/@media/prefers-reduced-motion)).
  - 1.4.3 text contrast (4.5:1) and 2.4.7 Focus Visible are standard and were not opened again.
- WAI-ARIA Authoring Practices:
  - Menus ([menubar](https://www.w3.org/WAI/ARIA/apg/patterns/menubar/)): focus the first item, arrows move, Home and End jump, type-ahead, → opens a submenu, Esc returns focus to the trigger, use `menuitemcheckbox` and `menuitemradio`.
  - Modal dialog ([dialog](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/)): Tab wraps inside. For actions that can't be undone, focus the least destructive button. Return focus to the trigger. Use `aria-modal`.
  - Combobox ([combobox](https://www.w3.org/WAI/ARIA/apg/patterns/combobox/)): focus stays in the field, with `aria-activedescendant`.
  - Tooltip ([tooltip](https://www.w3.org/WAI/ARIA/apg/patterns/tooltip/)): shows after a small delay, Esc hides it, it never takes focus, and it is linked with `aria-describedby`.

**Timing**
- Nielsen's limits ([NN/g](https://www.nngroup.com/articles/response-times-3-important-limits/)): 0.1 s feels instant, 1 s keeps the flow, and 10 s is the limit of attention. Beyond 10 s, show percent done and a way to stop.
- Animation length ([NN/g](https://www.nngroup.com/articles/animation-duration/)): 100–500 ms, small feedback about 100 ms, and exits shorter than entrances.
- Progress ([NN/g](https://www.nngroup.com/articles/progress-indicators/)): nothing under 1 s, a looping indicator for 2–10 s, and percent beyond 10 s.
- Drag and drop ([NN/g](https://www.nngroup.com/articles/drag-drop/)): highlight targets as the pointer nears and show the result before release. Space picks up from the keyboard.
- Tooltips ([NN/g](https://www.nngroup.com/articles/tooltip-guidelines/)): must work with keyboard focus and must not hold vital information.
- Material:
  - Desktop motion takes 150–200 ms ([M1](https://m1.material.io/motion/duration-easing.html)).
  - Snackbars stay 4–10 s and show one at a time. This was read from a mirror of the original page ([snackbars](https://zyun.gitbook.io/temporary-views/official/material-design/original/snackbars)).
- Radix tooltip: 700 ms delay, then a 300 ms warm window ([Radix](https://www.radix-ui.com/primitives/docs/components/tooltip)). The "~500 ms OS convention" was not verified, so 500 ms on the pick page is a choice, not a cited norm.

**Timing used on the pick page**

| Overlay | Open | Close |
|---|---|---|
| Menu or dropdown | 0 ms wait, then a 90 ms fade and 3 px | 60 ms fade |
| Sheet | 140 ms slide of 10 px | 0 ms |
| Tooltip tag | 500 ms, then 0 ms within 300 ms | |
| Help line | 0 ms | |
| Toast | in 140 ms | gone after 6 s, paused on hover or focus |
| Drop targets | within one frame | |
| Progress | none under 1 s, the orbit for 1–10 s, percent and Stop beyond 10 s | |

With reduced motion, nothing moves; only fades remain, or nothing at all. Every option on the page shows its timing and measures the click-to-painted-frame time in the viewer's browser (about 18–32 ms headless, which includes the browser's own frame wait).

## 3. Options (all live on the pick page; ★ = recommended)

### R: right-click menus, the main menu, dropdowns
Each card has four things to open: the track-header menu, the Mute-button menu (the K12 test), the AudioLab (logo) menu and the Quantize dropdown.

| # | Option | What it is |
|---|---|---|
| R0 | Today | A flat list with a blue filled hover, shortcut chips, every description always shown and coloured dots. 27 rows in the track menu. |
| **R1 ★** | Instrument panel | Groups labelled EDIT, SOUND, ADD and ROUTING in small mono capitals with a hairline. Routing becomes one submenu ("Groups, returns and sends ›"), so the track menu goes from 27 to 17 rows. Hover is a soft tint with a 2 px blue edge. Keys are quiet mono text. Descriptions move to a help line at the foot of the menu. **◇ ADVANCED** comes last, in amber, with entries that name their control. Keyboard per APG: arrows, Home and End, type-ahead, → and ← for the submenu, Esc returns focus, Shift+F10 or the Menu key opens. |
| R2 | Command row on top | Rename, Duplicate, Mute, Solo and Delete as an icon row (Windows CommandBarFlyout), the colours under it, the rest as today. |
| R3 | Two columns | Groups side by side, Routing opened inline, no submenus, about 470 px wide. |
| R4 | Type to filter | A filter field on top, already focused. Rows are 24 px. "dru" puts Move into Drums first and ↵ runs it (Raycast). |

Why R1:
- It follows Apple's "about three groups, one submenu level" without losing an entry.
- It keeps today's colours.
- It makes the K12 Advanced group visibly separate.
- Its foot line reuses the help line of T1, so long descriptions no longer make the menu taller.
- R4's filter can be added to R1 later for the long menus (only when the menu has more than about 15 entries).

### D: dialogs and sheets
Each card opens Close project (unsaved), Rename and Split into stems. The split runs a job with the orbit loader.

| # | Option | What it is |
|---|---|---|
| D0 | Today | A centred card, an icon tile, a light dim and no Tab trap. |
| **D1 ★** | Sheet from the top | It hangs from the top of the window and dims only the work area. Title at 15, a mono label, and the facts as read-outs (3 CHANGES · 12:04:31 LAST SAVE UTC · 2.41 MB). Don't save sits apart on the left; Cancel and the default sit on the right, each with its key (⌘⌫, Esc, ↵). Tab stays inside, and focus returns to the trigger. A long job offers "Keep working", which moves its progress into the notifications (N1). Opens with a 140 ms slide; with reduced motion, a fade. |
| D2 | Centred, instrument header | Today's position with a mono header strip (subject on the left, state in amber on the right), the same read-outs and key hints, and a 120 ms fade from 98 %. |
| D3 | In place, no window | A popover from the tab's ×; Rename turns the tab into a field; Split opens from the clip. Nothing dims. |
| D4 | Sheets for choices, a side panel for work | Confirmations are D1 sheets. Stems, Export, Bounce and Audio to MIDI dock at the right edge without being modal, so the song keeps playing. |

Why D1:
- It is the macOS pattern the glass engine already draws (GS2 sheets).
- It keeps the transport readable.
- It satisfies the Apple, Windows and APG button and keyboard rules.
- It adds the measurement details (M1) without new chrome.

D4's side panel is the natural next step for Audio to MIDI if its sheet is ever made non-modal. D3's in-place rename is worth taking for tab names whatever is picked.

### T: tooltips and the help line

| # | Option | What it is |
|---|---|---|
| T0 | Today | A rich card after 420 ms every time; no help line except under the Map. |
| **T1 ★** | Help line plus short tags | The help line at the foot of the window fills **instantly** on hover or focus: what the control does, NOW, DEFAULT, SCOPE and KEY as read-outs (Settings D4c, made window-wide). The floating tooltip becomes a tag (name and key) after 500 ms, and the next one within 300 ms shows at once. Esc hides it. |
| T2 | Help line only | No floating tooltips; ? shows or hides the line (Ableton Info View). |
| T3 | Callout with a leader | A rich card hung from the control by an amber hairline and dot, with name, value and unit, sentence, default and scope. It stays while hovered. |

Why T1:
- Reading never waits.
- The help line is where the settings work already put its text (D4c), so one table (`TIPS` and the S4 settings table) feeds both.
- Tags are short, which follows Apple's 60–75 characters and the TeachingTip note that people read 3–5 words.
- It meets WCAG 1.4.13.

### N: toasts, notifications, progress

| # | Option | What it is |
|---|---|---|
| N0 | Today | Three places: the bottom-centre toast (4.2 s), the update card at the top right and the Light-mode bar at the top. No history. |
| **N1 ★** | One stack with a log | Bottom right, above the transport. Each card has a glyph, the UTC time, one line, one action and ×, plus a draining hairline over 6 s that pauses on hover or focus. Errors, the update and notices stay until answered. At most 3 cards on screen. Everything also goes to a log behind a bell in the status bar (WCAG 2.2.1). A long job is a card with the orbit loader, percent, time left and Stop. |
| N2 | In the status line | Nothing floats; messages replace the status text, as in VS Code. |
| N3 | Short HUD plus cards | A 1.2 s HUD in the centre for finished actions (Undo stays on ⌘Z); cards at the top right for the rest. |
| N4 | Instrument log | One mono line per message: time to the millisecond, a category in colour, the text and an action. Lines fade after 8 s. |

Why N1:
- It gives one place for all messages, so the update card and the Light-mode bar join the toasts (VS Code's "one place").
- Nothing is lost (the log).
- Errors persist (InfoBar).
- Progress gets percent and Stop past 10 s (NN/g).

N4's look can be the log list's style.

### X: drag and drop

| # | Option | What it is |
|---|---|---|
| X0 | Today | A ghost row for a new track only. |
| **X1 ★** | Targets and a caliper | When files enter the window, every target gets a dashed hairline and the one under the pointer fills. An amber start line shows a read-out (bar, seconds and where the file goes), and a caliper shows the file's length in bars. This reuses MD1's M3 caliper. The keyboard alternative: Space picks up, arrows move, Space drops. |
| X2 | Drop sheet | Three large zones: new tracks, into this track, or open as a project. |
| X3 | Card at the pointer | A small card says what will happen; the lanes only tint. |
| X4 | Insertion line only | Ableton's minimal line. |

Why X1:
- It answers "where in time and onto which track" before release (NN/g).
- It reuses the caliper being built for MD1.
- It costs one overlay of a few divs per pointer move, with no redraw of the arrangement canvas.

### K: command palette and shortcuts

| # | Option | What it is |
|---|---|---|
| K0 | Today | Settings › Keyboard shortcuts (⌘/). No palette. |
| **K1 ★** | Palette on ⌘K, Assistant inside | A palette at the top over the 57 `SCA` commands. Search is fuzzy, matched letters show in blue, keys show in mono on the right, and Recent comes first. If nothing matches, the last row is "Ask the Assistant: …". ⌘K therefore keeps the Assistant and gains the commands. ? opens the key sheet. Accessibility follows the combobox pattern (`aria-activedescendant`). |
| K2 | Palette with the selection first | Actions for what is selected come first, with a tag such as CLIP · KICK 17. It uses ⌘P, so ⌘K stays the Assistant only. |
| K3 | Keys on the controls | Hold ⌘ or Ctrl for 500 ms and amber key badges appear on the controls. |
| K4 | Searchable key sheet on ⌘/ | Two columns by area, a search box that also finds keys, and a conflict count. |

Why K1:
- It is the convention in Figma, Linear and Raycast.
- `SCA` already exists, so the palette is a view over it.
- It is the "command bar" the extensions plan (registry, macros) feeds.

**Decision for the user:** whether ⌘K may host both the commands and the Assistant (K1), or the palette goes on ⌘P (K2's key). K3 and K4 can be added to any K pick later; K4 is cheap.

## 4. Recommendations in one line

`DR5 picks: R1 D1 T1 N1 X1 K1`

All six share one visual grammar:
- labels in small mono capitals with a hairline;
- values as read-outs with amber units (M1);
- a soft tint with a 2 px blue edge for the focused row;
- keys in quiet mono text;
- the amber ◇ for Advanced;
- the orbit loader for anything that takes time.

## 5. Implementation order (index.html tasks, one at a time, the usual release routine)

| Task | What | Needs |
|---|---|---|
| **OV1** ✅ done v0.256 | Shared overlay tokens and timing. Tokens: `--ov-*` (row height 26, radius 10, tint, label style), motion tokens (90 ms in, 60 ms out, 140 ms sheet), and the reduced-motion rule. No visual change beyond the menu fade. | glass engine layers (GS2) unchanged |
| **OV2** (built as R2) ✅ done: part a v0.278 (engine, track and clip menus), part b v0.286 (tab, Quick actions and device menus; the mixer's menus are choosers and keep the list) | The `openMenu` rewrite to R1. Group heads (`{g:'Edit'}`), one-level submenus (`kids`), a foot help line, the APG keyboard (arrows, Home/End, type-ahead, →/←, Shift+F10 and the Menu key, Esc returning focus), `aria-haspopup` and `aria-expanded`. Then regroup the long menus: track, clip, tab, logo and mixer. The JS open call must stay at or below today's 6.9 ms for the track menu. | OV1 |
| **OV3** | The K12 Advanced group in every right-click menu that sits on a control: "Hide the X button" and "Customise the X…", plus the first-time explanation. | OV2, extensions XT-DL steps (rules file) |
| **OV4** | askChoice, askText and the stem, Export, Bounce and Audio to MIDI dialogs become D1 sheets. Includes the Tab trap, focus return, key hints, read-outs, and "Keep working" sending a job to N1. | OV1, MD1 (orbit loader) |
| **OV5** | One notification centre (N1). `toast()`, `updCard`, `liteNotice` and job progress go through `notify({kind, text, action, keep})`. Adds the stack, the drain pause, the log behind a bell in the status bar, and a "Do not show again" option for notices. | OV1, MD1 |
| **OV6** | Help line plus tags (T1). A window-wide help line fed by `TIPS` and the S4 settings table. Tags at 500 / 300 ms, Esc hides them, keyboard focus shows them, and the missing text is written for the 227 controls without it. | Settings S4 and S9 |
| **OV7** | Drop targets and caliper (X1) on the arrangement, the mixer reference slot and the device racks, with the keyboard alternative. | MD1 (M3 caliper) |
| **OV8** (built as K1, on ⌘K with the Assistant inside) ✅ done v0.300 | Command palette (K1) over `SCA`, with Recent, the Assistant row and the ? key sheet. | user's answer on ⌘K vs ⌘P |

OV2 and OV4 to OV7 can be done in any order after OV1; OV3 waits for the rules file. Each task checks:
- Dark, Light and Solid levels;
- reduced motion;
- open-time measurements against section 1 (no slower than today);
- that the glass engine still draws each floating layer with no `backdrop-filter`.

## 6. Files

- `tools/design-lab/dr5/overlays.html`: the pick page as published.
- `tools/design-lab/dr5/today/*.jpg`: today's screenshots used on the page.
- `tools/design-lab/dr5/shots_today.py`: headless screenshots of every overlay in v0.228.
- `tools/design-lab/dr5/measure_today.py`: today's open times.
- `tools/design-lab/dr5/check.py`: 76 headless checks of the pick page, all passing. It covers:
  - menus open, keys move, Esc returns focus, and the K12 entries are present;
  - dialogs trap Tab and jobs finish;
  - the help line, tags and Esc;
  - the notification limits and the log;
  - drag feedback, including from the keyboard;
  - palette search and Enter;
  - the picks line;
  - no `backdrop-filter`;
  - no sideways scroll at 400 px;
  - no console errors in dark or light.

## The user's picks (27 November 2026, 17:39 Brussels)

`DR5 picks: R2 D3 T3 N1 X1 K1`

Right-click menus R2, dialogs D3, tooltips and help line T3, notifications N1, drag and drop X1, command palette K1 (on ⌘K with the Assistant inside, as K1 describes). Built by the steps of section 5 (OV1 to OV8) with the picked options in place of the starred ones, drawn with the look tokens of task LK (DR3 picks).

## Added from the learn-mode picks (UX3, 27 Nov 2026, 21:20 Brussels): lane F builds LM1 to LM3

The user picked `Learn picks: N5 H1 P1 W1 L1 G1 (Learn)` (docs/research-learn-mode.md, picks at its end; the name is **Learn**, the hover mode **What is this?**). Lane F builds, after OV1 and OV8 and in the order of that doc's section 6: **LM1** the guide engine `ovGuide(id, card)` with the P1 callout (shares T3's leader drawing), which replaces `tutSet` and its capture listeners (F1 and the ? button move to it); **LM2** the H1 Help menu (search over commands, controls, lessons and settings, shortcuts sheet, what's new, the Assistant row; shares rows with the OV8 palette); **LM3** W1 What is this? (fed by `TIPS`, the S4 settings table and `INS` live values with units). Lane M (task LM) builds the lessons on top of LM1.

## Added from the speed and feel picks (UX1, 27 Nov 2026, 22:02 Brussels): S16 and S18 for lane F

**S16 motion timings, faster than the page proposed, as the user asked** ("make it even faster. Like 100 milliseconds, or maybe even 75 or 80"): LOOK tokens **0 / 50 / 80 / 120 ms** (instant; menus, tooltips, hovers 50 ms; panels, sheets and dialogs opening and closing 80 ms; page turns and view changes 120 ms), one ease-out, interruptible, reduced motion respected; apply them to every overlay you own and offer them to the other lanes through LOOK. **S18:** a progress line and the rule that every action answers within 100 ms (a visible start within 100 ms, long work in slices or a worker by its owner lane).

## Added from the long-sessions wishes (UX2, 27 Nov 2026, 22:23 Brussels)

**E20:** follow macOS Reduce motion and Dim flashing lights (and Windows' animation setting) by default: your motion tokens drop to 0 and flashing elements stop when the system asks. A switch to ignore the system setting goes in the advanced part of Settings (lane B's hook), not out in the open.
