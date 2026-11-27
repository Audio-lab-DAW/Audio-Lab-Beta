# AudioLab Pro settings, round 1 (task SR5, 27 November 2026)

Pick page: **AudioLab settings, round 1**, https://claude.ai/artifact/WVkEqbepgsNWX5JZdXtz5p

**Nothing in index.html or desktop/ was changed, no version bump.** This is the pick page and its notes only. It turns the four research parts into things to choose from: `docs/settings-research-general.md` (SR1), `docs/settings-research-daw.md` (SR2), `docs/settings-research-audiophile.md` (SR3) and `docs/settings-audit.md` (SR4, the inventory of v0.221).

The user's words: "after this preparation, we'll start building it together by multiple choice. Or if you have better techniques than multiple choice, you can do that as well." Also: a separate DAC option and a separate interface option, "maybe split it in two or have it in one and then automatically"; move things between the application and Settings where it helps; no double settings.

What stays fixed from the earlier rounds: today's look, colours, buttons and icons; Inter at 11, 12, 13 and 15; full glass; the science philosophy ("smart and sciencey, clear, intuitive, snappy"); snappiness and low CPU first. The glass settings on the page already use the three levels (Glass, Light, Solid) and the presets of `docs/glass-engine-plan.md`.

## How to answer

Try the prototypes, then press "Copy my picks" in the bar at the bottom of the page and paste the line into the chat. It looks like this:

`Settings round 1 | A: A3 | B: B2, U1, safe volume V1+V2+V3+V4 | C: all 52 as recommended | D: D1b, D2 all, D3b, D4c, D5c, D6 all, D7b, D8b`

A and B start unpicked. C and D start on the recommendation, so only the differences need a click. "Take all ★" fills in every recommendation.

## How the page was made

- One self-contained HTML file (about 98 KB), in the style of the design round 1 page and the display-first devices page: numbered options, a ★ on the recommendation with one line of reason, a Dark (glass) and Light mode (no glass) switch, a picks bar.
- Techniques used in place of plain multiple choice: whole working windows to try (A), a test bench that changes the situation under three designs (B), a sorting board that is already sorted (C), and toggles whose preview reacts (D).
- The prototypes share one table of about 140 of AudioLab's real settings, each with its page, block, scope, default, help line and search words, plus 10 options that stay in place. A change in one window shows in all the others, which is the "one home per setting" rule made visible.
- Search really works: it matches names, help text and synonyms ("latency" finds Buffer size, "sound card" finds Output device), shows the path, and a click on the path jumps to the row and flashes it. In A1 to A4 it also finds options that live in place (metronome, snap, capture) and offers "Show me". A0 searches as the app does today, so the gap can be felt.
- Kept light: one blur on one visible window, only one prototype in the page at a time, one timer for the live read-outs that runs only while part A is on screen and the page is visible.
- Checked headless at 1280 x 720, 1920 x 1080 and 400 px wide: no console errors, no sideways scroll, and a scripted run through search, jump, pick, unplug, arm, rate change, the board and the decisions.

Limits: long lists are behind a button (the 57 shortcut rows, the 22 fader designs, the layout picture, the app icons). Figures in part B are examples, not measurements. Device names are as expected, not read from the user's Mac.

## A. The whole Settings window

Five complete, clickable windows with the same settings in five structures.

| # | Structure | What it is | For | Against |
|---|---|---|---|---|
| A0 | Today, tidied | Today's 11 tabs and names, copies removed, nothing else moved | No relearning | Interface stays a four-screen page; metronome, snap and capture still have no home; search stays blind outside the window |
| A1 | Sidebar with pages | The audit's 13 short pages in four groups (Program, Working, Sound, Project), scope mark on each row, blue bar on what changed | Familiar; every page about one screen; scales | A narrow column on a wide window if the pages stay single-column |
| A2 | Search first | Opens on one field with "Commonly used" and "Changed"; pages are chips | Fastest when you know the word | Weak for browsing and for learning what exists |
| **A3 ★** | Cards with live read-outs | The same 13 pages built from cards that use the width, under a strip of live numbers (rate, buffer, CPU, frame rate, glass level, output); each number opens its page | Uses the width; measured numbers always in view; status is a door | Scanning order needs care; long blocks make uneven cards |
| A4 | Inspector | No big window: click a part of AudioLab and a side panel shows that part's settings | Nothing covers the music; settings in context | App-wide things (look, shortcuts, updates) still need a list; harder to see the whole |

**Recommendation: A3.** It is SR1's "sidebar with cards" combination on SR4's page list. It fits "smart and sciencey, clear, snappy" best: every page fits about one screen, the numbers stay in view, and the sidebar keeps it familiar. A1 is the safe second choice (same pages, plain rows); the two share almost all of their code, so A3 can fall back to A1 per page where cards do not suit (the shortcut list).

The 13 pages, as proposed in the audit: General, Appearance, Performance, Layout, Keyboard shortcuts (Program); Navigation, Editing, Mixer and meters (Working); Audio, DAC and audio interface, Recording and metronome (Sound); Project, Export (Project).

## B. DAC and audio interface

Three working versions of the audio page with device cards for the iFi xDSD Gryphon and the Zoom AMS-24. A test bench above them unplugs either device, arms a track, starts and stops playback, switches the mono check, changes the engine's and the Gryphon's rate, switches "Device follows the engine", and switches between the desktop app with helper and the browser.

| # | Design | What it is | For | Against |
|---|---|---|---|---|
| B1 | Two separate sections | "Listening output (DAC)" and "Recording interface" | Matches the first wording; short | The interface is also an output, so it appears twice; one half is empty with one device; two buffers asked for with one engine underneath; arming shows the two-clock case |
| **B2 ★** | One page, roles filled automatically | Role cards "Listen through" and "Record from", filled by themselves, changeable by hand; a Listening and a Recording setup; arming a track proposes Recording (AMS-24 for both, one clock, small buffer), disarming returns to Listening on the Gryphon | "Have it in one and then automatically"; works with one device or two; one signal path | The automatic choice must explain itself (the page does it in one sentence); needs the device names confirmed |
| B3 | One device, optional monitor output | One device for everything plus a "Separate monitor output" switch | Simplest; what most DAWs do | Makes the Gryphon the extra although it is the main listening path |

**Recommendation: B2**, as in SR3.

**The live signal path** (the same in all three): a light with one sentence (Clean, Processed, Converted, or "Clean as far as the browser can see"), then boxes for source, engine rate, master, resampling yes or no, system (shared), device and rate, bit depth at the device, device volume, buffer in samples and ms, latency reported, round trip measured, dropouts, exclusive use, and proof of "no conversion".

**What is possible when**, marked on every read-out and control (from SR3's feasibility table):

| Mark | Meaning | On the page |
|---|---|---|
| now | Works with today's web audio engine | Choosing devices and the two roles; engine rate; device rate (read through a short probe); resampling yes or no; buffer and its ms; latency reported; round trip measured; dropouts; "shared with other apps"; output pair; input channels; stopping on unplug; lock volume; fade in |
| helper | Needs the small native helper in the desktop app (Mac first; `alvol` exists but has not been tried on the user's hardware) | Bit depth at the device; device volume and its ceiling; setting the device to the engine's rate; proof of "no conversion" by a pattern test |
| native engine | Needs the planned native audio engine (with VST hosting); shown switched off | Exclusive use and integer mode; WASAPI exclusive and ASIO; more than two inputs; drift correction for two devices |

Never shown as available: exclusive use. In the browser the page says plainly that bit depth and device volume cannot be seen. The Gryphon's menu items and the AMS-24's switches appear as advice text only, because the computer cannot read them; the Gryphon card names the LED colour to expect at the current rate as the user's own proof.

**When the listening device is unplugged**

| # | Behaviour | Note |
|---|---|---|
| **U1 ★** | Stop and ask | Playback stops; a card offers the next output at 20 % or waiting. On return it reconnects, takes back its old volume only if that is under the ceiling, and stays stopped |
| U2 | Fall back and keep playing | Today's behaviour. No interruption, but a jump to another output at that output's level: the risky one for sensitive headphones |
| U3 | Stop and wait | No card; reconnects when the device is back; the user presses Play |

**Safe volume** (all four recommended, each can be unticked)

- V1 A volume ceiling per device (helper): soft limit, applied again on every reconnect.
- V2 Lock volume (now): AudioLab never touches the device's volume; for the Stax chain.
- V3 A new, unknown device starts at 20 % (helper).
- V4 Fade in over 1.5 s after any change of output (now).
- Always, not a choice: AudioLab never raises a device's volume by itself, and it says that it cannot see the knob on the Stax driver.

## C. Sorting board

52 cards: every setting from the audit that is doubled today or could move. Three positions per card: **In place** (only where it is used), **Settings** (only in the Settings window), **Both, linked** (a short list in place and the full page in Settings, drawn by the same code, with a link both ways). Each card says where the setting is today and why it is placed where it is. "Accept all recommendations" puts every card back.

Recommended positions (the audit's section 5):

| Area | In place | Settings | Both, linked |
|---|---|---|---|
| Mixer | C1 Compact channels, C2 Cables, C3 Keep the master in view, C4 Mixer display, C5 a channel's own display, C13 Spectrum overlay, C16 Mono, Dim, swap, balance, C17 Loudness target (stored per project) | C7 Pan control style, C8 Fader and meter design, C11 channel number and the two sizes, C12 Level meters (once), C15 Stereo field behind pan | C6 Strip width, C9 Each channel shows, C10 Master shows, C14 cable kinds |
| Devices and piano roll | C18 devices panel view, C21 piano roll working controls (remembered), C22 scale and root (per project) | C19 default for new devices, C20 audio savers, C23 piano roll defaults | |
| Transport | C24 metronome and count-in on or off, C26 capture source and length, C29 keyboard piano, C30 clock format (new), C31 tempo lane (per project) | C28 Play flash source, C33 tour button | C25 Metronome setup, C27 capture options, C32 transport bar editing |
| Arrangement and visualizer | C34 Follow on or off, C43 visualizer view and size, C44 automation show, hide, write | C36 playhead look, C37 zoom keys and style, C39 grid look | C35 follow modes (all six in both), C38 snap (new), C40 track controls, C41 map, C42 visualizer on or off and place |
| Program and sound | C48 Save, Save as, Open (out of Settings) | C49 sample rate, buffer, output device (once), C50 interface size (one zoom), C51 recording offset and inputs, C52 test tone | C45 glass level quick switch, C46 automatic updates, C47 export options |

Two rules behind it: one home per setting, with every second door a link and never a second control; a right-click menu may repeat a setting but never own it.

## D. Small decisions

| # | Decision | Options | Recommended | Reason |
|---|---|---|---|---|
| D1 | When a change takes effect | a at once everywhere (today); b at once, and device, rate and buffer ask "Keep?" and go back by themselves; c an Apply button | **b** | Instant is the norm and what the app does; the countdown guards only the three changes that can cut the sound |
| D2 | Reset | per setting (blue bar and ↺), per page, everything after a backup | **all three** | Today only "Reset all", which also resets options outside Settings without saying so |
| D3 | Where search lives | a field at the top of Settings (today); b the same, also finding in-place options with "Show me"; c one command bar for the whole app | **b** | Fixes today's gap without a new surface; c can follow later (the assistant uses ⌘K today) |
| D4 | Help text | a tooltips (today, 112 of 339 controls have none); b a line under every row; c a help line at the foot of the window with default and scope | **c** | No hover delay, and pages do not get longer |
| D5 | How per-project settings show | a a mark on each row; b a Project group in the sidebar; c both; d a switch "App / This project" at the top | **c** | Unclear scope is the most common complaint in every DAW; the group is the home, the marks catch the rest |
| D6 | Quick routes | eight routes, each on or off (click the CPU read-out for the performance panel with links, right-click it for Performance, click the latency read-out for Audio, right-click the metronome, right-click a level meter, click the clock, right-click the empty transport bar, right-click Capture) | **all eight** | Read-outs become doors; each lands on its block and flashes it once |
| D7 | Profiles and export | a none (today); b one file with tick boxes; c the file plus named profiles | **b** | The missing backup; keeps this computer's audio devices out of a file carried to another machine |
| D8 | Numbers in the rows | a value only; b value, unit and what it costs or gives | **b** | Measured numbers in place of adjectives, only where a real number exists |

SR2 recommended testing the scope switch (D5d) first. After building it next to the others, the group plus marks (D5c) reads better, because the switch hides half the window at a time; both are on the page to compare.

## Proposed implementation order

After the picks, and after the glass chain. Each step is one index.html task with the usual release routine, run one at a time. The first three need no picks and fix what the audit found.

| Step | Task | Depends on |
|---|---|---|
| S1 | Remove the copies inside Settings: the second Level meters list, the three hidden controls, the doubled file buttons and Audio devices button | none |
| S2 | Remember the export options (last used; file name per project) and the piano roll options (snap, chord, ghost, lane; scale and root in the project) | none |
| S3 | Fix what is out of sync: Mono and swap on the master strip, the Follow list (six modes in both places, the command), the visualizer's own header | none |
| S4 | One settings table in the code (id, label, page, block, scope, default, help line, search words) that draws the rows. No visible change; everything after builds on it | none |
| S5 | The new pages in the picked structure (A), each block moved whole, old names kept as search words | A, S4 |
| S6 | Search: synonyms and help text, the path in each result, in-place options with "Show me" | D3, S4 |
| S7 | Changed mark, reset per setting and per page, "Reset all" that lists what it resets and saves a backup first | D2, S4 |
| S8 | Scope: marks and the Project group; loudness target, key and tempo lane move into the project, with defaults for new projects | D5, S5 |
| S9 | Help text in the picked form, and a line for every control that has none | D4, S4 |
| S10 | Audio page: one copy of device, buffer and rate, the Control Panel pop-up folded in, a "running now" read-out, and the Keep or go back countdown | D1, S5 |
| S11 | Audio devices in the picked design (B): role cards, the Listening and Recording setups, the proposal on arming | B, S10 |
| S12 | Signal path read-out with the light, with the marks for what the browser cannot see | S11 |
| S13 | Safe volume and the picked unplug behaviour | U, V, S11 |
| S14 | Mixer and meters: the gear popover and the Settings page from one list, level meters once, links both ways, right-click menus that link | C1 to C17, S5 |
| S15 | Recording and metronome page; capture options into the Capture panel; right-click the metronome | C24 to C27, S5 |
| S16 | Quick routes | D6, S5 |
| S17 | Navigation and Editing pages; the arrangement snap select; the clock format | C30, C34 to C39, S5 |
| S18 | Export and import of the settings file with tick boxes | D7, S4 |
| S19 | Numbers in the rows | D8, S4 |
| with G4 | Performance and the Glass block of Appearance are rebuilt in the glass chain's task G4, not here | glass chain |

Not index.html, and not in this chain: the hardware check with the user at the Mac (SR3 stage 0: device names, the helper's read-out, rate switching against the Gryphon's display, the round trip with a cable), the helper work in `desktop/` (SR3 stage 2) and the native engine (stage 3). S12 and S13 show their helper parts as "not visible" until the helper is proven.

## Open questions from the research that the picks do not settle

1. Is the Stax driver fed from the Gryphon's rear line out, and which knob is the volume: Gryphon, Stax or AudioLab?
2. May AudioLab switch the output by itself when a track is armed, or always ask? (The prototype asks the first time.)
3. Is clean playback on Windows wanted soon, or is the Mac the only listening machine?
