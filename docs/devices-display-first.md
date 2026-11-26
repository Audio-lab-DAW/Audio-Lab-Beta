# AudioLab Pro: display-first devices, round 1 (task D4, pick page part, 26 November 2026)

Pick page: **"AudioLab devices, display first, round 1"**, https://claude.ai/artifact/FdsjNefeJo8UJfXfkDQNjZ

**Nothing in index.html or desktop/ was changed.** This is the pick page only. The implementation, device by device, comes after the user picks a layout number (per device, or one for all).

Related: `docs/glass-engine-plan.md` (section 1, the user's decisions; section 2.4, the engine; section 3, task D4), `docs/design-language-research.md` (section 2, option G2 "Display first"; section 9, round 1 result).

## 1. What was asked and what is fixed

The user's picks from design round 1 that this page builds on:

- **G2 display-first devices**: the black display boxes as large as possible, with floating glass buttons inside them.
- Device titles stay **sideways** (vertical) to save height.
- Today's colours, buttons and icons (B0, E0, H0), Inter on the 11/12/13/15 scale (C1), full glass (D3).

Kept in every layout on the page:

- The left title strip from v0.196: on/off (effects) or the logo (instruments) on top, the name upright, remove at the bottom.
- The pin at the top right.
- Preset arrows, the preset name and Change; the play button on instruments.
- Each device keeps **today's width**, so the panel still fits the same number of devices.

One thing changes in every layout: the right-hand "Parameters" strip (26 px) goes. Its job, showing and hiding the controls, moves to an eye button beside the pin, and its width goes to the display.

## 2. How the page was made

- "Today" is a headless screenshot of v0.219 at twice the size for each of six devices: **Psy Bass** (synth), **Kick designer** (drum designer), **Pro EQ**, **Compressor**, **Echo delay**, **Voice**. Clap designer, Sidechain and Reverb were also captured to check that they share a frame with Kick designer, Compressor and Echo delay.
- Sizes, labels and values were read from the running app (panel 261 px, device 253 px high; left strip 28 px, right strip 26 px, Gain bar 44 px):

| Device | Width today | Picture today | Controls |
|---|---|---|---|
| Psy Bass | 970 | 410 × 250 visible (the canvas already runs behind the parameters) | 8 always-on knobs, 3 pages (Roll and gate, Sound, Envelopes), 16-step row, Gain |
| Kick designer | 872 | 380 × 238 | 7 knobs, 2 bars (Level, Length), Click menu, Key track, Pitch/Amp view, Gain |
| Pro EQ | 982 | 560 × 238 | band chips, band editor (type, Freq, Gain, Q, Stereo/Mid/Side, Dynamic, Solo), analyser, Auto, Scale, Out, Gain |
| Compressor | 602 | 300 × 238 | Ratio, Attack, Release, Makeup, Threshold, Gain |
| Echo delay | 602 | 300 × 238 | Feedback, Mix, Low cut, High cut, Time, Gain |
| Voice | 1116 | 600 × 238 | 5 menus, Keep formant, 6 mode buttons, 8 knobs, 4 number fields, Gain |

- The layouts are built in real HTML, CSS and canvas at real size (1 CSS px = 1 app px), with the real labels and values. The displays are redrawn to look like the real ones; they are not the app's drawing code.
- Switches on the page: Dark, Light mode (no glass, solid panels) and Bright theme; panel height 253 px or the smallest, 215 px. The eye button, page tabs, "More" drawers and hover reveal work.

## 3. The four layouts

The same four ideas are shown for every device, so one number can be picked for all.

| # | Name | Idea | Many parameters | Small screens (215 px) |
|---|---|---|---|---|
| **DD1** | Glass dock | The display fills the device. One glass dock along the bottom holds the knobs (knob, label over value). Preset and view switches float at the top. | A page opens as a second tray above the dock and closes when its tab is clicked again (Psy Bass); a More drawer for the rest (Voice). | The dock keeps its height, the picture gives up the difference. On narrow devices the dock scrolls sideways. |
| **DD2** | Glass rail | The display fills the device. One glass rail at the right holds everything, as today's parameter side does, but floating on the picture. Narrow effects get a one-column rail and a floating preset. | Pages as tabs on the rail; nothing is ever behind a second click. | The last row of a page scrolls inside the rail. |
| **DD3** | On the picture | No panel. Each control is a small glass chip at the thing it shapes (a handle, a curve, an edge). Pro EQ: the band editor is a capsule under the selected dot. Gain is a slim fader at the right edge. | Controls with no place in the picture line up along the bottom, or go to a More drawer. | Chips keep their place; labels can drop to value only, with the label on hover. |
| **DD4** | Hover reveal | The display is clean. Values are written as plain text at the bottom. The DD1 dock rises when the mouse is over the device. | Same as DD1 once revealed. | The best fit: at rest nothing covers the picture. Needs a tap or a key on touch screens. |

### Numbers from the page (253 px panel)

"Clear" is the part of the display not under the layout's main panel. "Under glass" counts every glass panel, the preset and pin pills included.

| Device | Today | DD1 clear / glass | DD2 clear / glass | DD3 clear / glass | DD4 clear / glass at rest |
|---|---|---|---|---|---|
| Psy Bass | 410 × 250 | 941 × 143 (+31%) / 4 panels, 36% | 509 × 251 (+25%) / 2, 42% | 941 × 251 (+130%) / 12, 16% | 941 × 251 (+130%) / 2, 4% |
| Kick designer | 380 × 238 | 843 × 195 (+82%) / 4, 24% | 579 × 251 (+61%) / 2, 29% | 843 × 251 (+134%) / 13, 21% | 843 × 251 (+134%) / 3, 8% |
| Pro EQ | 560 × 238 | 953 × 195 (+39%) / 4, 23% | 651 × 251 (+23%) / 2, 29% | 953 × 251 (+79%) / 5, 17% | 953 × 251 (+79%) / 3, 8% |
| Compressor | 300 × 238 | 573 × 195 (+56%) / 3, 20% | 409 × 251 (+44%) / 3, 31% | 573 × 251 (+101%) / 8, 19% | 573 × 251 (+101%) / 2, 6% |
| Echo delay | 300 × 238 | 573 × 195 (+56%) / 3, 20% | 409 × 251 (+44%) / 3, 31% | 573 × 251 (+101%) / 8, 18% | 573 × 251 (+101%) / 2, 6% |
| Voice | 600 × 238 | 1087 × 195 (+48%) / 4, 20% | 675 × 251 (+19%) / 2, 35% | 1087 × 251 (+91%) / 10, 14% | 1087 × 251 (+91%) / 3, 9% |

Honest reading of these numbers: in DD3 and DD4 the picture is "clear" of a main panel, but in DD3 the chips sit on top of it. The devices panel is short and wide, so height is the scarce side: a dock (DD1) costs height, a rail (DD2) costs width. Psy Bass with its tray open in DD1 keeps only 143 px of height, and at the 215 px panel it ends up with slightly less clear picture than today.

## 4. Recommendations

| Device | ★ | Why |
|---|---|---|
| Psy Bass | **DD2** | Closest to today, so the least to relearn. All 8 main knobs, the open page and the step row fit on the rail in four columns; nothing is hidden behind a second click. |
| Kick designer (and Clap, Snare, Hat, Tom) | **DD2** | A two-column rail works for every drum designer whatever its parameters are. DD3 is the alternative if the user wants the knobs at the handles: six of nine parameters have a place in the picture. |
| Pro EQ | **DD3** | The device is its picture. A capsule under the selected dot keeps eyes and mouse in one place and leaves the whole graph free. |
| Compressor (and Sidechain) | **DD3** | Every value already has a handle or a place: Threshold and Ratio on the curve, Attack and Release on their dots, Makeup at the output. |
| Echo delay (and Reverb) | **DD1** | Few knobs, narrow device, a picture that reads left to right: the dock keeps the full width, and the same dock fits the Reverb unchanged. |
| Voice | **DD2** | The most kinds of controls of any device; the rail shows all of them at once and the piano roll keeps its full height. |

If one number is wanted for everything: **DD2**. It is the only layout that holds any device without a drawer. The rule behind the per-device stars: DD2 as the house layout; DD3 where every control has a place in the picture; DD1 for narrow effects with a handful of knobs.

DD4 is not starred anywhere because controls that appear only on hover are slower to reach and do not exist on touch screens. It could be offered later as a setting on top of DD1 ("hide the dock until the mouse is over the device"), since it is the same dock.

## 5. CPU cost

**Nothing here is measured.** The glass engine (task G2) does not exist yet, and the headless machine has no GPU. The notes below follow from the engine design in `docs/glass-engine-plan.md` section 2.4 and should be checked with the Glass Bench once the engine can take a device display as a source.

How floating glass over a display works in the engine: the display is a canvas, so it is fed to the engine as a flat picture (plan 2.4, known gap, option a). Each glass panel is one rectangle in one shader pass. The work that costs is rebuilding the blur of the picture under the glass, and that is needed only when the display actually redraws.

So the cost of a layout depends on two things:

1. **How much display area is under glass.** This is the area the engine has to blur again per display redraw. Smallest in DD3 (14 to 21%), then DD1 (20 to 36%), largest in DD2 (29 to 42%). DD4 is the lowest at rest (only the preset and pin pills, 4 to 9%).
2. **How often the display redraws.** Read from the screenshots and the code, not timed: Pro EQ (analyser), Compressor (level and gain reduction) and Voice (live view) redraw while sound plays; the Kick designer, Psy Bass and Echo delay pictures appeared to change only when a control changes. For those three a floating panel costs close to nothing between edits in any layout.

The number of panels matters very little: DD3 has up to 13 chips, but each is one more rectangle in the same draw call.

Per layout:

- **DD1**: one or two panels in one low strip. Cheap and the same on every device.
- **DD2**: one panel, the largest area. On a display that redraws while playing (Pro EQ, Compressor, Voice) this is the dearest of the four, by area.
- **DD3**: most panels, least area. A drawer adds one panel only while it is open.
- **DD4**: no glass until the mouse is over the device, then the same as DD1. With ten devices in the panel only one ever pays.

Rules for the implementation so that floating glass stays cheap:

- One feed per device display; upload it only on frames where the display repainted.
- Blur only the rectangles under glass (plus the blur margin), at quarter resolution, not the whole display.
- Under glass, a live display may refresh its blurred copy at 30 per second while the sharp display keeps its own rate (plan 2.4, quality steps).
- Knobs and values are DOM on top of the glass with no filter; turning a knob must not rebuild the blur unless the display itself changed.
- No `backdrop-filter` (the page uses it only as a stand-in).
- Every layout must stay readable in the Blur and Solid levels. The "Light mode (no glass)" switch on the page shows the Solid case.

## 6. Limits of this round

- The displays on the page are redrawn, not the app's own drawing code, and the glass is the browser's plain blur without AudioLab's lens.
- Six devices of about seventy are shown. Grid, the particle devices (Orbit, Fractal, Venom) and the analysis devices (Spectrum, Loudness) are not covered; Grid has no parameter side at all today.
- The Pro EQ band editor is drawn with band 3 selected; the "no band selected" hint text has no place yet in DD1, DD3 and DD4.
- Bright theme: the display stays black and only the frame and the glass turn light. This follows the user's "black display boxes"; it was not checked against the app's own bright themes.
- Not tested with a real mouse, a trackpad or touch; nothing was tried on the user's Mac.

## 7. What happens next

1. The user picks a layout number per device, or one for all.
2. Implementation device by device in index.html (serial work, after or together with G3, since the floating glass uses the glass engine with the flat-picture feed for canvases).
3. The page source is in the artifact; it can be read back from the link above.
