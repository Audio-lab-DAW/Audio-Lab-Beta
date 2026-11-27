# AudioLab Pro: learn mode, the Help button and lessons (task UX3, 27 November 2026)

**Pick page: "AudioLab learn mode"**, https://claude.ai/artifact/LdqqqCHY6PLCx1GKn1arRq (source `tools/design-lab/ux3/learn.html`; `build.py` inlines the screenshots; `check.py` is the headless test, 21 checks).
To answer, pick one number per family on the page and copy the line from the bar at the bottom, for example `Learn picks: N1 H1 P1 W1 L1 G1 (Field guide)`. ★ marks the recommendation.

**Nothing in index.html, desktop/ or native/ was changed.** This task wrote this file, `tools/design-lab/ux3/` and the project doc.

## 1. Summary

The user picked FIRST USE AND HELP (27 Nov, 20:02 Brussels): "Redo the tutorial mode and give it a more appropriate name, rework the whole help button and make it intuitive and clear how everything works live so you can still do things, move parameters while learning through the help."

Today's ? button switches on a **tutorial mode that freezes the app**: every click, key and right-click is swallowed while blue outlines cover up to 200 controls. You can read about a knob but you cannot turn it. It is also the only door into help: there is no search, no lessons, no shortcuts sheet from Help, no what's new.

The proposal, with the recommended picks:
- **N1 "Field guide"** as the name. Its "what is this?" verb is **Identify**; its lessons are **Lessons**.
- **H1:** the ? opens a small **Help menu**: a search box first (controls, commands, lessons, what's new; with no match it offers "Ask the Assistant"), then Identify (F1), Lessons with progress, Keyboard shortcuts (⌘/), What's new, and the Assistant (⌘K).
- **P1:** the guide points with **your T3 callout** (an amber hairline and dot from a card to the control). The card never covers the control or the meter it asks you to watch. It shows the live value with its unit and a small picture that moves as you turn (for example the note envelope against the 16th grid). It ticks and moves on when the project reaches the target. **Nothing is ever blocked.**
- **W1 Identify:** a toggle (F1) that never blocks. Hover anything to get its name, live value, what it does, default, range, key, command id and the lesson that uses it. Clicks, drags and keys keep working; the card follows the value as you turn.
- **L1:** lessons of 4 to 6 steps **on your own song**. Each step waits for a state, not a click: tempo in range, notes on the off-beats, pump on, peak under −1 dBFS. Steps already done are passed with "already done". Back, Skip, "Do it for me" where it helps, and End/Esc are on every step.
- **G1 quiet progress:** ticks and "2 of 4 done". No streaks or points.
- Four psytrance lessons, each built and tested in the prototype:
  - a rolling bass;
  - sidechain kick and bass;
  - a build with a filter sweep (automation write);
  - mixing a drop.
- Lessons name **control ids** (`data-al`, extensions step DL1) and **command ids** (`COMMANDS`, DL2), never positions, so they survive layout changes. The prototype's "Shuffle the layout" and "Hide devices" buttons show this: the guide finds the moved knob, or offers "Show devices ⇧D" (it runs the command, then points).
- **Off costs nothing.** No elements, no timers, and no listeners beyond the ? button and F1. Today's mode re-scans every 900 ms at **86 ms per scan** (headless software drawing).

## 2. What exists today (v0.263, read in index.html and measured)

Script: `tools/design-lab/ux3/shots_today.py` (Fractals demo, 1600 × 1000, headless). Numbers: `tools/design-lab/ux3/today/measure.json`. The screenshots were converted to JPEG for the page.

| Part | Where | What it does |
|---|---|---|
| ? button | `#bTut` in `#tutgrp`, in the tab bar between redo and full screen | Toggles tutorial mode. It is the only help entry point. The tooltip reads "Tutorial mode (F1)". |
| Tutorial mode | `tutSet`, `tutScan`, `tutShow`, `tutHide`, `tutVirt`, `TUT`, `TUTX` (about line 25416) | Shows a banner: "Hover any button or area to see what it does. Nothing you click changes anything." Capture listeners swallow click, pointerdown, mousedown, dblclick, contextmenu and keys; only Esc and F1 work. Checked headless: the metronome did not toggle. |
| Outlines | `#tutl` | **200 boxes (the cap).** Each control is tested with `elementFromPoint` at 5 points. The scan re-runs **every 900 ms**: **86 ms per scan** and **163 ms** to switch on, both headless in software. |
| Arrow card | `#tutcard`, `#tuta` (SVG), `#tuth` | A card with a blue curved arrow and a highlight box. The card text comes from `TIPS`, then `TUTX`, then `title`. Virtual areas cover the ruler, sections, clips and the loudness map. |
| Texts | `TIPS` (89 entries), `TUTX` (9), 675 elements with `title` or `data-tip`, `TV` gesture pictures | Settings audit: 112 of 339 controls have no text. |
| Tooltips | `tipShow`, `#tip`, 420 ms | Hidden while tutorial mode is on. The user picked **T3** (a callout with an amber leader) in DR5; lane F (OV) builds it. |
| Help line | none (Map hint only) | Settings round 1 D4c keeps a help line at the foot of the Settings window. |
| Commands | `SCA` (63 entries with id, group, label, key, icon, run). Group `help` holds `keys` (⌘/), `ai` (⌘K) and `tour`. | The K1 palette on ⌘K with the Assistant inside is planned as OV8. The commands registry `COMMANDS` and `runCommand(id)` are planned as DL2. |
| Control ids | none yet (`data-al` count 0) | DL1 adds `data-al="group.name"` and a `CONTROLS` table. |
| Assistant | ⌘K chat. Tools: `get_song, add_notes, add_fx_hit, set_track, set_instrument_param, add_effect, set_effect_param, set_tempo, add_section, silence_range, automate`. Offline fallback with regexes. | It edits the song with undo. **It cannot point at a control.** |
| First run | `toast('Demo song loaded. Press space to play. Right-click a clip, a track or empty space for options.')` | No tour, nothing pushed. |

## 3. Research (sources opened on 27 November 2026)

**Music software**
- **Bitwig, interactive help.** "Interactive Help is built in to every device, modulator, and Grid module." Open it with F1, Show Help in the Inspector, or right-click › Show Item Help. It gives "a live, editable copy of the device, and links to any relevant online videos". In the Grid, "parameters can be freely adjusted while this view is open", and the copy follows mode changes. There is no separate Help mode toggle. ([Device descriptions](https://www.bitwig.com/userguide/latest/device_descriptions), [Welcome to the Grid](https://www.bitwig.com/userguide/latest/welcome_to_the_grid))
  - Taken for option P3 (live copies) and for the Assistant's "explain this device" walk-through.
- **Ableton Live.**
  - Info View "displays the name and function of whatever element of the UI that you hover over with the mouse". Toggle it with the `?` key. ([Live 12 manual, First steps](https://www.ableton.com/en/live-manual/12/first-steps/))
  - Live 12.4 (5 May 2026) added a **Learn View** that "replaces the earlier Help View and its associated lessons". It has structured modules, filtering and completion tracking; Pack lessons became "Pack Info pages". ([Live 12 release notes](https://www.ableton.com/release-notes/live-12/))
  - Taken for W3 (help line), H2 (side panel) and G1 (completion ticks).
- **Logic Pro, Quick Help.** It "shows a brief description of interface elements without interrupting your work", in the inspector, a floating window or bubbles at the pointer. Turn it on from the control-bar button or Help › Quick Help. ([Logic Pro User Guide](https://support.apple.com/en-ae/guide/logicpro/lgcpa0902aeb/mac); read from a summary of the page.)
  - Taken for W1: identify never interrupts.
- **FL Studio, hint bar.** "If you place your cursor over any control a short description of it will appear here." It also shows values while you adjust. The floating hint panel is "transparent to mouse clicks". ([FL Studio manual, toolbar panels](https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/toolbar_panels.htm))
  - Taken for P2 and W3.

**Other software**
- **Blender.** Tooltips appear on hover. Python tooltips show the operator's expression. F1 or right-click › Online Manual opens the manual page for the hovered control ("We do not currently have 100% coverage"). ([Blender manual, Help system](https://docs.blender.org/manual/en/4.2/getting_started/help.html))
  - Taken for the id line in W1's card. It makes ids learnable and is the bridge to the Workshop.
- **Figma** (a vendor teardown, so treat it as opinion). "Figma Basics" files are dropped into the workspace on first login, so people "learn by touching actual objects". ([Supademo](https://supademo.com/content/plg-onboarding-gallery/figma))
  - Taken for L2 (a lesson project).
- **Duolingo** (vendor article). A lesson comes before sign-up, lessons are short, and "a progress bar helps set a user's expectations of effort". ([Appcues GoodUX](https://goodux.appcues.com/blog/duolingo-user-onboarding))
  - Taken for the step dots and for G2, which is not recommended.

**Research on tutorials and help**
- **NN/g.**
  - "Tutorials interrupt users, don't necessarily improve task performance, and are quickly forgotten."
  - Favour **pull revelations**: help "triggered by some signal that the user would benefit from that information at that moment".
  - Make help "easy to dismiss (and recall)" and "skip the obvious stuff".
  - Proactive help should also be reachable from the UI.
  - ([Onboarding tutorials](https://www.nngroup.com/articles/onboarding-tutorials/), [Help and documentation](https://www.nngroup.com/articles/help-and-documentation/))
- **Coach marks.** "If users are in the middle of a task, coachmarks can be perceived as an obstruction." Coach marks do not fix a badly composed interface, and we can hold 3 to 4 things at a time. ([UI-Patterns](https://ui-patterns.com/patterns/coachmarks))
- **Chameleon** (vendor, unsourced rules of thumb).
  - More than 3 to 5 pieces of help in a first session is too many.
  - Stop a tip once the feature has been used ("clicked it ten times? Don't show it again").
  - People must be able to skip or exit a tour and restart it later.
  - ([Chameleon, contextual help](https://www.chameleon.io/blog/contextual-help-ux))
- **Accessible tours.**
  - Use non-modal popovers (`popover="manual"`) that do not close on outside clicks, with an explicit close.
  - Return focus to the related control on close, and start each step with a heading (`aria-labelledby`).
  - Never cover the focused control (WCAG 2.4.11).
  - The page also says focus must not jump into a popover on load, while its sample moves focus into each step; the design below moves focus only on request.
  - ([Chrome, persistent app tours](https://developer.chrome.com/docs/modern-web-guidance/guides/ui-components/persistent-app-tours))

**What makes tutorials annoying, and the rule this design follows**

| Annoyance | Rule |
|---|---|
| It blocks the app (today's mode) | Nothing is blocked: no scrim and no swallowed input. The callout is placed so it never covers its control, or a control the step asks you to watch (`avoid`). |
| Too long, can't skip | 4 to 6 steps, 2 to 4 minutes. Back, Skip step and End/Esc on every step. Steps already satisfied pass with "already done". |
| Pushed at you | Nothing starts by itself. At first run, one N1 notification offers the Field guide; everything else is pulled from Help. |
| Forgotten | You do the thing on your own song while it plays; the guide confirms it. Lessons can be reopened any time. |
| Costs speed | Off: nothing drawn, no timer. On: one card, one SVG leader, one ring, re-placed only on a value change or layout change (one rAF). |

**Accessibility rules for the build**
- The card is `role="dialog"` (non-modal) with `aria-live="polite"` on the live line.
- Focus never moves on its own. Shift+F1 (proposed) moves focus to the card, and Esc returns focus to the control.
- Every target is reachable by keyboard: the knobs are sliders with `aria-valuetext` in units.
- With reduced motion, the ring does not pulse and the next step waits 1.4 s instead of 1 s.
- In the lessons, colour is never the only signal of done: there is also a ✓ and the text "fits ✓".

## 4. The design

### 4.1 Name (N)

| # | Name | "What is this?" | Why |
|---|---|---|---|
| **N1 ★** | **Field guide** | Identify | A field guide is what a scientist carries while working: you look something up beside the real thing. "Identify" is the field-guide verb. It fits the science look without sounding like a mode. |
| N2 | Lab notes | Annotate | Matches the lab look and the Workshop, but reads like notes you keep. |
| N3 | Explain | Explain | Plain and searchable, with less character. |
| N4 | Guide | What is this? | Short, but sounds like a one-time tour. |
| N5 | Learn | What is this? | Familiar from Ableton's Learn View; the same word. |
| N6 | Bench notes | Annotate | A lab-bench feel next to the Workshop; less obvious to a newcomer. |

### 4.2 Help button (H)

| # | What the ? opens |
|---|---|
| H0 | Today: toggles the blocking tutorial mode. |
| **H1 ★** | A **Help menu** under the button, 340 px wide. A search box comes first and searches controls (`TIPS` plus the settings table), commands (`COMMANDS`), lessons and what's new; with no match, the last row is "Ask the Assistant: …". Default rows: Identify (F1), Lessons (with progress dots), Keyboard shortcuts (⌘/), What's new in the current version, Ask the Assistant (⌘K). Choosing a control result **points at the control** (it stays usable). Arrows, Enter and Esc work; focus returns to the ? button. |
| H2 | A **side panel** docked at the right, 280 px, with tabs for Lessons, Search, Keys and New. The arrangement narrows, and the panel stays while you work (Ableton Learn View, Logic Quick Help in the inspector). |
| H3 | The ? opens the **K1 palette** with a `?` scope: one surface for commands and help, but less discoverable. |

H1 and H3 share their rows, so H1 costs little once OV8 exists. F1 stays "Identify" in every option.

### 4.3 How the guide points (P)

| # | Style |
|---|---|
| P0 | Today: a dim layer and a blue arrow card. The knob is locked (the prototype shakes the card when you try). |
| **P1 ★** | The **T3 callout**: a card hung from the control by an amber 1 px hairline with a dot at each end. The ring is a 1 px amber outline. The card is placed on the side with room, never over its target or a watched control. It shows the step, the live value in units, a small live picture and the step dots, then ticks ✓ and moves on after 1 s. |
| P2 | A pulsing ring on the control, with the text in a help line at the foot (FL hint bar, Ableton Info View). |
| P3 | **Rearranged focus** (Bitwig's live copy): a strip over the arrangement with live copies of the 2 or 3 knobs the step needs and a bigger picture. The originals stay usable and move together. |

### 4.4 "What is this?" (W)

| # | Mode |
|---|---|
| W0 | Today: tutorial mode. |
| **W1 ★** | **Identify**, a toggle (F1, the Help menu, the side panel). A pill at the top reads "Field guide · Identify. Hover anything. Everything still works. Done · Esc". Hovering a control shows a P1 callout: name, live value, what it does, DEFAULT, RANGE, KEY, COMMAND, the `data-al` id, and a link "Lesson: … ›". The card follows the value while you turn. No scanning and no outlines: one dashed box under the pointer only. |
| W2 | Hold ? (a quasimode). |
| W3 | Help line only: the hovered control's name, value, default and key at the foot of the window. |

### 4.5 Lessons (L)

| # | Format |
|---|---|
| **L1 ★** | Steps that **wait for a state** on your own song. Each step has a target id, an optional reveal command, a check, a live line, an optional picture and an optional "Do it for me". Steps already true pass ("Already done ✓, moving on"). Steps that need a fresh action (`mustAct`, for example "move Cutoff at least 0.4 octave", "toggle the pump twice") always wait. Every change is a normal undoable edit. |
| L2 | A **lesson project** in its own tab from a prepared start (Figma Basics). On exit, "Back to your song" restores the user's song untouched. |
| L3 | A **checklist** in a side panel: any order, with "Show me" per item. |

**The four psytrance lessons** (as built in the prototype; times are estimates):

| Lesson | Steps | Checks (the state, not clicks) |
|---|---|---|
| A rolling bass, about 3 min | 1. Tempo 143 to 147. 2. Play. 3. Fill the three 16ths after each kick. 4. Decay shorter than a 16th. 5. Shape with Cutoff. | 1. `143 ≤ bpm ≤ 147`. 2. Playing. 3. All 12 off-kick steps on, none on 1/5/9/13 ("Do it for me" offered). 4. `decay < 60000/bpm/4`; the live line reads "1/16 at 145 BPM = 103 ms". 5. Cutoff moved more than 0.4 octave and ends in 300 Hz to 2 kHz. |
| Sidechain kick and bass, about 2 min | Play; pump on; Depth 50 to 80 %; Release near a 16th; compare off and on. | Release ratio to a 16th between 0.6 and 1.5. Two power toggles since the step started. |
| A build with a filter sweep, about 3 min | Loop the Build; Cutoff under 200 Hz; automation write on (W); Play; sweep up across the 8 bars; write off and listen. | At least 40 % of the build written, spanning at least 4 octaves. Write off with a line present (the knob then moves on its own). |
| Mixing a drop, about 4 min | Loop the Drop and play; solo the kick; kick peak −8 to −4 dBFS; unsolo; fit the bass; check the pump. | Master peak (1.5 s hold) in range. Bass at least 2 dB under the kick. Master peak under −1 dBFS. Pump on with Depth of 30 % or more. The card avoids covering the master meter. |

The level targets in the mixing lesson are starting points for a lesson, not mastering rules. The lesson text says "leave room", not "the correct level".

### 4.6 Progress (G)

| # | |
|---|---|
| G0 | None. |
| **G1 ★** | **Quiet**: step dots, lesson ticks, "2 of 4 done" in Help, and a line in the N1 log when a lesson finishes. Stored in `UI.lm` (a few bytes). |
| G2 | Streaks, points and reminders. Not recommended: it nags, and it is out of place in a studio tool. |

### 4.7 How lessons use the ids, and survive layout changes

A lesson is data (`LM_LESSONS`). It never holds selectors or coordinates:

```json
{ "id": "lm.rollingBass", "title": "A rolling bass", "minutes": 3,
  "steps": [
    { "target": "transport.tempo", "check": "song.bpm >= 143 && song.bpm <= 147" },
    { "target": "transport.play", "command": "transport.play", "check": "transport.playing" },
    { "target": "device.bass.steps", "reveal": "view.devices",
      "check": "steps.bass.offbeats == 12 && steps.bass.onKick == 0", "doIt": "lm.fillRollingBass" },
    { "target": "device.bass.decay", "reveal": "view.devices",
      "check": "param('device.bass.decay') < sixteenthMs()", "picture": "envelopeVsSixteenths" },
    { "target": "device.bass.cutoff", "mustAct": true,
      "check": "movedOctaves('device.bass.cutoff') > 0.4 && inRange(300, 2000)" } ] }
```

At run time the guide does three things:
1. It finds `[data-al="<target>"]`.
2. If the target is missing or hidden, it shows "Not on screen" with the reveal command as a button (or runs the command when the step asks for it), then points.
3. It re-places the callout on resize, scroll, layout change or a value change. There is no polling.

The checks read project state through getters (`S`, `FT_HOOKS`, `INS` meters), so a lesson does not care which button changed the state: a key, a MIDI controller or the Assistant all count.

A headless test (`tools/ui-tests/taskLM_*.py`) walks every lesson:
- each target resolves to a visible control after its reveal;
- each check is false before and true after a simulated action.

A renamed or removed control therefore fails CI, not the user. Released ids never change (extensions plan rule 10).

### 4.8 The Assistant inside help

Two new tools, `point_at(id, text)` and `start_lesson(id)`, let the Assistant answer with the real control:
- "What does Decay do?" points at Decay with its live value and the 16th length.
- "Explain this device" walks the four knobs one callout at a time, like Bitwig's device help.
- "Why is my bass muddy?" links Decay, Depth and Resonance; each name points when clicked.

The prototype has canned answers for these.

### 4.9 Cost

- **Off.** Nothing is in the DOM. The only listeners are the ? button and the existing F1 key handler. No timers. The prototype's stage bars show "guide layer: 0 elements (nothing drawn)".
- **On.** One card, one SVG and one ring element; one rAF per value change; no `elementFromPoint` scan; no interval.
- **Identify** uses one delegated `pointermove` (rAF-throttled) that walks up to the nearest `[data-al]`.
- **Lesson checks** run on the app's existing change notifications (`changed()`), plus the meter's 200 ms peak update for the mixing lesson.

## 5. The prototype (`tools/design-lab/ux3/`)

| File | What |
|---|---|
| `learn.html` | The pick page source. It has four mocks of AudioLab at 16:10 (drawn at 1120 × 700 and scaled). In each mock: the tab bar with the ? button; tracks at 48 px rows (N3 dense); sections; a Bass synth with Cutoff, Resonance, Decay and Drive, an INS-style display and a 16-step kick and bass grid; a Sidechain pump; a master peak meter; the transport at the bottom with tempo and W; the foot line and the map. The audio is WebAudio (kick, saw bass through a filter, drive and ducking). Every knob drags, scrolls, takes arrow keys and resets on double-click. |
| `build.py` | Inlines `today/*.jpg` into one file for publishing. |
| `check.py` | Headless check at 1280 and 400 px (21 checks). It covers: no horizontal scroll; the Decay step advances by itself after Decay is lowered by keyboard; the knob stays usable under P1 and is locked under P0; the card never covers its control; Help search for "reso" points at Resonance; Identify follows the knob (100 %); W3 fills the help line; the sidechain lesson detects Play and pump on; after Shuffle the ring is still on Depth; with devices hidden the card offers "Show devices" and it works; the ★ picks line. |
| `shots_today.py`, `today/` | Today's ? button and tutorial mode, and `measure.json`. |

## 6. Proposed tasks after the picks (lanes from CLAUDE.md)

| Step | Lane | What | Needs |
|---|---|---|---|
| LM0 | H (XT) | Ids first: `data-al` on the transport, track headers, device knobs and the ? button (DL1 part 1 and the knob part of DL7); `COMMANDS` with `runCommand(id)` (DL2). No visible change. | none |
| LM1 | F (OV) | The guide engine `ovGuide(id, card)`: the P1 callout sharing T3's leader drawing, the ring, placement that avoids the target and watched ids, reveal by command, Esc and focus rules. **It replaces `tutSet` and its capture listeners.** F1 and the ? button move to it; `SCA` `tour` becomes `help.identify`. | LM0, OV1 |
| LM2 | F (OV) | The Help menu (the picked H): search over commands, controls, lessons and settings; the shortcuts sheet; what's new from `desktop/update-notes.txt`; the Assistant row. Shares rows with the OV8 palette. | LM1, OV8 |
| LM3 | F (OV) | Identify (the picked W), fed by `TIPS`, the S4 settings table and `INS` for live values with units. Missing texts are written as part of OV6. | LM1, S4 |
| LM4 | **new lane J (lessons, prefix `lm`)** | The lesson runner and the four lessons as `LM_LESSONS` data: checks, "already done", `mustAct`, "Do it for me", progress in `UI.lm`, the first-run N1 offer. Headless test `taskLM_*.py` walks every lesson. | LM1 |
| LM5 | J, with hooks from C (FT) and E (IN) | Getters the checks need (sidechain state, automation write, master peak hold) exposed as `FT_HOOKS.*` and `INS.*`, never by reaching into another lane's code. | LM4 |
| LM6 | J and the Assistant owner | Assistant tools `point_at(id, text)` and `start_lesson(id)`, plus "explain this device". | LM1, LM4 |

Lane J owns only `lm*` names, `LM_LESSONS` and `UI.lm`; it adds one row to the CLAUDE.md table. Until LM1 lands, today's `tutSet` stays as it is (it is lane F's to replace, not J's).

## 7. What is a guess

- The tutorial-mode timings come from software drawing in the cloud; on the Mac they will be lower, but the 900 ms rescan still runs for as long as the mode is on.
- The psytrance figures (tempo range, Release near a 16th, the peak targets) are common practice, used as lesson targets. They are not cited rules.
- The Figma, Duolingo and Chameleon points come from vendor articles.
- Logic's Quick Help was read from a summary of Apple's page.

## The user's picks

(waiting)
