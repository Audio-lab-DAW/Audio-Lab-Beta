# AudioLab Pro: display-first devices, round 1 (task D4, pick page part, 26 November 2026)

Pick page: **"AudioLab devices, display first, round 1"**, https://claude.ai/artifact/FdsjNefeJo8UJfXfkDQNjZ

**The user has picked (section 7)**; the implementation runs as task DV, one step per run (section 10). DV-1 (the shared frame for every device) is in v0.274.

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

## 7. Round 1 result (26 November 2026, late)

**The user's picks: Psy Bass DD2, Kick designer DD2, Pro EQ DD3, Compressor DD4, Echo delay DD4, Voice DD2**, and they are to be combined into one behaviour that every device has:

- **Rail open** (the eye is on): the glass rail, DD2.
- **Rail closed**: **hover reveal** (DD4) is the standard: a clean display, values as text, the dock on hover.
- **Right-click the eye** (top right, beside the pin): a drop-down with a choice of what the closed state shows, **Hover reveal** or **On the picture** (DD3). Available on every device.
- On the picture goes away while the rail is open, and comes back when it is closed.
- User's words: "The glass rail is not for everything", so the picks above stay as each device's own starting state.

**Confirmed by the user on 26 November: this is the spec for the implementation, and it applies to every device, including instruments and effects added in the future.**

Starting state per device:

| Device | Starts with | Closed state shows |
|---|---|---|
| Psy Bass | rail open | hover reveal |
| Kick designer (and the other drum designers) | rail open | hover reveal |
| Pro EQ | rail closed | on the picture |
| Compressor (and Sidechain) | rail closed | hover reveal |
| Echo delay (and Reverb) | rail closed | hover reveal |
| Voice | rail open | hover reveal |

Rules, all confirmed by the user:

- Every device has all three states, also the ones that start closed (Compressor, Echo delay and Pro EQ can still open a rail from the eye).
- A plain click on the eye opens and closes the rail; the right-click menu also has "Open / Close the glass rail". On touch the menu opens with a long press.
- The choice between hover reveal and on the picture is kept per device (per instance), like today's open or shut parameters (`kOpen`). It is not one setting for the whole app.
- Devices of the same family as a picked one take its starting state. For the roughly sixty devices not shown in round 1, and for every new device: the rail starts open when the device has more than about eight parameters or has pages, otherwise it starts closed with hover reveal.
- A new instrument or effect is built display first from the start: sideways title strip, the display filling the device, a glass rail, a hover-reveal dock, and positions for on the picture where its controls have a place in the display.

The prototype of this behaviour is the first section of the pick page ("Your pick: one device, three states"): six devices, each starting in its picked state, with the eye and its right-click menu working.

Notes for the implementation:

- Today's `kOpen` (parameters open or shut) maps onto rail open or closed; the new per-device value is the closed-state mode (`hover` or `picture`), default `hover`.
- CPU: with the rail closed and hover reveal, a device has no glass over its display at rest (only the preset and pin pills, 4 to 9% of the display). That is the cheapest case, and it is now the standard for narrow effects.
- On the picture needs a position for every control on each device's display; where a control has no place in the picture it lines up along the bottom or goes to a More drawer (section 3). Devices without such positions yet (the Reverb, for one) fall back to hover reveal until they have them.
- Hover reveal needs a touch and keyboard way in: tap the display, or focus a control with Tab.

## 8. Lab prototype on the glass engine (26 November 2026, late)

The user chose to try the behaviour in the lab before the app is touched. **No index.html or desktop/ changes; `glass-engine.js` was not changed either.**

| File | What it is |
|---|---|
| `tools/glass-lab/devices-lab.html` | The six devices at real size in a scrolling devices panel, with the picked behaviour (section 7). The floating controls are glass faces drawn by `glass-engine.js`; each display canvas is fed to the engine as a flat picture. Needs `glass-engine.js` beside it. |
| `tools/glass-lab/devices_lab.py` | 17 headless checks. `python3 tools/glass-lab/devices_lab.py [screenshot dir]` |

One-file version as an artifact (engine inlined): https://claude.ai/artifact/MWV7AobnkFob1icGw5j6mA

Switches on the page: glass (GL engine, browser blur, solid), engine quality (high, medium, low), displays (still, or live: every visible display repaints and is handed to the engine each frame), all devices (as picked, rail open, hover reveal, on the picture). A live readout shows frames per second, frame times, CPU time in the engine's calls, and per second: display uploads, blur rebuilds, face redraws. **Measure** runs all 24 combinations for two seconds each and gives a table to copy.

### How it is wired (this is the wiring proposed for the app)

- **One engine canvas over the whole devices panel**, above the display canvases and below the DOM controls (z-index only; no device creates a stacking context). Not one engine per device: browsers allow only a limited number of WebGL contexts.
- Each device display: `setFlat('d:'+id, {source: displayCanvas, rect})`, and `markFlatDirty` when that display repainted.
- Each floating control (rail, dock, tray, chip, pill, menu, drawer): `addPanel({over:'flats', kind:'pill' or 'window', rect, radius, opacity})`. The DOM element keeps only its content: no fill, no border, no `backdrop-filter`.
- Panel rectangles and opacity are read from the DOM only for about 300 ms after something changed (a click, a state change, a hover, a scroll, a resize). When nothing changes, no DOM is read and `render()` returns at once.
- Hover reveal follows the CSS fade: the dock's opacity is passed to its panel each frame during the fade.

### What the checks show (headless, no GPU, so counters only)

- All 17 checks pass, no console errors.
- **Still displays: 0 uploads, 0 blur rebuilds, 0 face redraws per second in every state**, with 14 panels (rail open), 28 (hover reveal at rest, counted with hidden docks) or 56 (on the picture) on six devices. Glass over a display that does not change costs nothing, whatever the layout.
- Live displays, quality high: every visible display is uploaded every frame and the blur is rebuilt once per frame. Quality low: capped at 30 rebuilds per second while the displays and controls keep the screen rate.
- Hover reveal: the dock is hidden at rest, appears under the mouse as a glass face, goes away again, and the engine is idle afterwards.
- The eye and its right-click menu: rail to hover reveal, switch to on the picture, rail open hides it, closing brings it back.
- Scrolling the panel keeps every glass face on its control.
- In software rendering the engine's calls took about 2.4 to 3.1 ms per frame with two live displays visible at high and 1.2 to 2.0 ms at low; the three layouts were within noise of each other. These numbers are from a machine without a graphics card and say nothing about a real one. The real numbers are the user's to take with the Measure button.

### Findings for the engine (for whoever owns `glass-engine.js`)

1. **Hover reveal is not free while a display is live.** At rest only the small preset and pin pills are glass, but the engine uploads the whole display canvas and rebuilds the blur for the whole layer whenever a fed display is dirty and any panel with `over:'flats'` is visible. Measured: the same uploads and rebuilds per second in hover reveal as with the rail open. Two ways out: (a) the engine uploads and blurs a fed canvas only where a visible panel covers it (the region cull that already exists for docked panels, extended to flats); (b) in the app, the two pills over a live display are drawn as plain tint instead of glass while the rail is closed. (a) is the better fix: it also makes on the picture cheaper than the rail, as section 5 assumed.
2. **Flats need a backdrop.** `render()` only handles flats once a backdrop source was uploaded, so a layer that has only fed displays needs a dummy backdrop (the lab gives it a 2 x 2 canvas in the panel colour). A flat-only layer should work without one.
3. **The flat blur is rebuilt for the whole layer** when one display changes. With a 1600 x 253 panel that is small, but a region limited to the dirty display would be cheaper still.
4. Counting in the readout: `flatUploads`, `flatPyramids` and `draws` from `g.stats` were enough to see all of the above.

Section 5's ranking by area under glass therefore holds only after finding 1 is fixed; until then every layout costs the same over a live display, and nothing over a still one.

## 9. What happens next

1. Done: the user picked and confirmed the rules (section 7).
2. The user runs Measure in the lab page on the Mac and copies the table.
3. Engine: findings 1 to 3 in section 8.
4. Implementation device by device in index.html (serial work, after or together with G3, since the floating glass uses the glass engine with the flat-picture feed for canvases).
5. The pick page's source is in its artifact; the lab page is in the repo.

## 10. Implementation steps (task DV, one step per run)

Each run does the next step not yet logged in `docs/backlog-log.md` ("task DV-<n>"). Binding for every step: sections 7 and 8 above; glass over displays only through the engine (flat-picture feed, no `backdrop-filter`); today's colours, buttons and icons; titles stay sideways; every device keeps its parameters, presets, automation and saved projects (old projects open, `kOpen` keeps its meaning); the audio path does not change (exports bit-identical); tooltips on every control; Glass, Light and Solid; touch and keyboard ways into hover reveal; no cost at rest with the rail closed. Each step: screenshots of the changed devices in the three states (rail open, closed at rest, closed revealed) at Glass and Light, frame time, its own UI test, the Fractals levels.

| Step | What | Devices |
|---|---|---|
| **DV-1** (v0.274, done) | **The shared frame for all devices** in the devices panel: sideways title strip kept; the right-hand Parameters strip gone, its width to the display; the display box (black) fills the device; the pill at the top right with the eye and the pin; plain click on the eye = rail open or closed; right-click, long press, Shift+F10 = the menu (Open / Close the glass rail, Hover reveal, On the picture); rail open = the controls on one glass rail; rail closed = clean picture with a values line, the controls revealed on hover, keyboard focus or a tap; `kMode` per instance (`hover` or `picture`, default per type from section 7; Pro EQ `picture`), `kOpen` unchanged; the devices engine (`DVG`): one engine canvas over the panel, faces for open rails and revealed panels, the display canvases under them as flat pictures. No device's own layout changed; On the picture falls back to hover reveal everywhere (no positions yet, `DVPIC` empty). Starting states not applied yet. | all (in the panel; pinned windows keep their look) |
| **DV-2** (v0.285, done) | **Starting states** (section 7 table and the rule: rail open with more than about eight parameters or pages, otherwise closed with hover reveal) for newly added devices only (old projects keep theirs). **The rail-open picks**: the picture runs on under the rail where the drawing allows (Psy Bass already does), each device's rail laid out as in the pick page (DD2: pages as tabs on the rail, the step row; drum designers' Click menu and Key track onto the rail; Voice's menus, modes, knobs and fields). | Psy Bass; Kick designer, Snare, Clap, Hat, Tom designers; Voice |
| **DV-3** (v0.304, done) | **On the picture**, the mechanism (`DVPIC`: control positions per device, chips as engine faces, a More drawer for controls without a place) and **Pro EQ** (closed, on the picture: the band editor as a capsule under the selected dot, Gain as a slim fader at the right edge, the "no band selected" hint). | Pro EQ |
| DV-4 | **The closed picks**: hover reveal tuned as a bottom dock (DD4/DD1: knobs in one row, label over value), values line placed clear of each picture's own handles; on-the-picture positions where controls have a place (Threshold and Ratio on the curve, Attack and Release on their dots, Makeup at the output). | Compressor, Sidechain; Echo delay, Space reverb |
| DV-5 | Synths: starting state by the rule, picture under the rail, dock, on-the-picture positions where they have a place. | Venom, Plant, Wavetable, Orbit, Vector FM, Saw lead, Square lead, Soft pad, Strings, Pluck, Bounce, Soft keys |
| DV-6 | Bass, acid and drums, the same. | Sub, Growl, Sub bass, Square bass, Reese bass, Acid, Fractal (instrument), Drum kit, Percussion |
| DV-7 | Sampling, FX, Grid (no parameter side today: the eye only where there are controls), and the first dynamics. | Sampler, Emit, Vector Grain, FX, Grid, OTT, Limiter, Soft Clipper, Gate |
| DV-8 | Dynamics and space. | Multiband Dynamics, Transient Shaper, De-Esser, Resonance Suppressor, Ducker, Timeless delay, Blur, Convolution Reverb, Tape Stop / Stutter |
| DV-9 | Delays, tone and colour. | Vector Delay, Bounce Delay, Low-pass filter, Drive, Auto Filter, Bitcrusher, Pitch & Formant, Pitch Correction |
| DV-10 | Modulation and stereo. | Phaser, Chorus / Flanger, LFO Shaper, Vocoder, Frequency Shifter, Fractal (effect), Stereo Imager |
| DV-11 | MIDI and analysis. | Chord, Bouncy Notes, Arpeggiator, MIDI Toolkit, Spectrum, Loudness, Tuner, Meter |
| DV-12 | **The check of every device and the rule for new ones**: every instrument and effect in the three states at Glass, Light and Solid; a UI test that fails when a device has no frame, no eye where it has controls, no starting state, or a control without a tooltip; the rule for new devices written into the device-building notes (display first: sideways title strip, display filling the device, glass rail, hover-reveal dock, on-the-picture positions where controls have a place); whether pinned windows take the frame. Then "display-first devices complete". | all |

### How DV-1 is built (v0.274)

- Block "(task DV-1)" before `askChoice`, CSS before `.dacv`, made by `tools/edits/taskDV1.py` from `taskDV1_block.js` and `taskDV1_css.txt`. Test `tools/ui-tests/taskDV_1.py` (39 checks; a third argument, the previous build, adds the old-project check).
- **Closed devices keep their controls in the page**: `renderFx` sets `kOpen` to true on the current track's closed devices only while the markup is built, then back (in a `finally`); the pictures are drawn afterwards and read false, so they are drawn closed as before. The device is then laid out closed: the controls and the gain are positioned over the right of the picture, hidden (opacity 0, no pointer events, still reachable with Tab). Effects (`.fxd`) lose `kopen` again so their picture keeps its closed width. Pinned devices are left out.
- **Widths**: the strip's 26 px go to the display box; open devices keep today's width exactly (checked: 970, 982, 602, 602, 1116 for Psy Bass, Pro EQ, Compressor, Echo delay, Voice); closed devices keep today's closed width, but never narrower than their revealed controls (the basic synths get wider when closed). Psy Bass, whose picture already ran under its controls, keeps its full width when closed.
- **Values line** (closed): label and value of the first eight controls (`CT` label and `spec.f`), updated on edits inside the device and when the mouse leaves; left out where the picture has its own buttons along its bottom edge (Acid, Venom, Echo delay's cut bar is canvas and stays visible). Values that move by automation update at the next edit or render.
- **Glass**: `DVG`, an engine canvas `.dvgCv` right after `#fxin` (z-index 1: above the display canvases, under the controls at 3 and the tint panel `.dvrail` at 2). Faces: every `.dvrail` (kind window, no shadow, tint 0, `over:'flats'`, the element keeps its own see-through tint); opacity follows the fade. Flats: the device's canvases under a visible face, refreshed at most 2 times a second when stopped and 20 while playing. Rectangles read only for 320 ms after a render, scroll, hover, focus or resize. At Solid or without WebGL2 there is no engine and `.dvrail` is a near-solid tint. The pill is plain tint (finding 1 option b).
- Not done in DV-1, on purpose: starting states, device-specific layouts, On the picture positions, the bottom-dock shape (the revealed panel is the rail's shape), engine findings 1 to 3.

### How DV-2 is built (v0.285)

- Block "(task DV-2)" before `askChoice` (after DV-1's), CSS before `.dacv`, made by `tools/edits/taskDV2.py` from `taskDV2_block.js` and `taskDV2_css.txt`. Test `tools/ui-tests/taskDV_2.py` (21 checks).
- **Starting states** (`DVSTART`): Compressor, Sidechain, Echo delay, Space reverb closed with hover reveal; Pro EQ closed with `kMode:'picture'`; Voice open. `mkFx` queues a new effect made inside one trusted user event (a click, a key, a drop: from the browser, the chain and mixer menus, Change); the next render sets `kOpen`/`kMode` when the event made one or two new devices and the device has neither field yet. A project being opened, a demo song, a template or a script (`AudioLab.build`) never passes through this, so stored states stay as they are. Instruments in the table (Psy Bass, the drum designers) start open, which is already the default. The rule for the other devices (more than about eight parameters or pages) is applied group by group in DV-5 to DV-11.
- **Rail-open picks** (`DVFILL`: Psy Bass, Kick, Snare, Clap, Hat and Tom designers, Voice): the picture (canvas, or the drum designers' `.pzc` box) grows to fill the display box and never gets narrower than it was. The Kick designer's `.kside` (Click menu, Key track) moves from the picture onto the rail as a row under the preset row (`.dvkrow`), the rail is fitted again (`duFit`) and the device keeps its width (877 px; its picture 380 to 444 px). The drawing inside the pictures is lane E's.
- **Fix of DV-1**: devices with a set width (Psy Bass, Orbit, Vector FM, Bounce, Sub, Fractal) had the display box 25 px wider than the device, which cut off the gain and the pin. The box is now held inside the device (`dvFitBox`); checked on all 74 device types, rail open and closed.
- **LOOK tokens** (task LK): the rail and the pill edges are hairlines (`--lk-hair`, W1); the values line writes units in amber small caps (`--unit`, L2).

### How DV-3 is built (v0.304)

- Block "(task DV-3)" before `askChoice` (after DV-2's), CSS before `.dacv`, made by `tools/edits/taskDV3.py` from `taskDV3_block.js` and `taskDV3_css.txt`. Test `tools/ui-tests/taskDV_3.py` (37 checks; a third argument, the previous build, adds the old-project check).
- **The mechanism**: `DVPIC[type] = {lay(D, own, B)}`. When the rail is closed and the instance's `kMode` is `picture`, `dvFrame` (wrapped) adds `.dvpic` and calls `lay`, which moves the device's own controls (the same elements, so parameters, presets, automation and undo work as on the rail) to their places as chips (`.dvface`) and returns the sections of the More drawer (`dvPicMore`: a "More" button, `aria-expanded`, kept open per instance over renders in `DV3.more`, Escape closes it and gives the focus back). The rail, the hover panel and the values line are hidden. Devices without an entry keep hover reveal.
- **Chips as engine faces**: DV-1's `dvgSync` now takes `.dvface` elements too (kind `pill`, their own radius); at Solid or without WebGL2 they are a near-solid tint. A press on a chip's empty part does not pan the devices panel; a tap on a chip does not toggle hover reveal.
- **Pro EQ** (`dvpEq`, the user's DD3): the band editor (`.eqb`) is a capsule under the selected dot, at the place the EQ's own hit test computes (`fX`, the gain scale, dynamic gain), above the dot when there is no room, at the middle of several selected dots (Off, On, Gain 0, Delete), and follows the dot while it is dragged or scrolled (`dvCapPos`, one frame at most per input); with no band selected a hint ("Click a dot to edit its band, double-click the graph to add one", the full help as its tooltip) sits low on the graph. Gain is a slim fader (30 px) at the right edge, always shown. The preset arrows, Change and More float at the top left, clear of the dB scale; the drawer holds Bands (the chips with their on/off ticks and +), Analyser (Off, Post, Pre+Post, Auto) and Whole EQ (Scale, Out). A closed Pro EQ's pill (pin on top, eye under it) stands in the column right of the graph, so it no longer covers lane E's "analyzer, tilt" label or the selected band's label (DV-1's open point).
- **Cost** (DV-1's engine, three small changes): pictures under glass are no longer refreshed at rest (only while playing, for two seconds after a change and once after the song stops); a picture under chips only is refreshed while it is being edited, not while it plays (a live analyser under small chips costs nothing); only the frame's own fades keep the page being read (the meters' transitions inside devices, about 50 a second while playing, kept every rail being re-read before). Measured while playing with a Pro EQ on the picture: the devices engine took 40 ms in 4 s against 48 ms on the build before (where the closed Pro EQ had no glass at all).
