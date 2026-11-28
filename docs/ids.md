# Control ids (task XT-DL1, from v0.266)

Every control a person can press, drag or type into gets one stable id, written on the element as `data-al="<id>"`.
They are the base of the Workshop (docs/extensions-plan.md, section 9): rules that hide, rename or move a control
(DL5, DL6), CSS snippets (DL11) and scripts name controls by these ids, so **an id, once released, is never renamed or
reused** (section 9.4, rule 1).

- The table is `CONTROLS` in index.html: `[id, selector inside the area, plain name]`. The area is the id's first word:
  `transport` (`#tr`), `track` (`#hdrin`), `mixer` (`#mixWin`). The name is what menus will say ("Hide the Loop button").
- Repeated controls share one id: every track's Mute button is `track.mute`, every channel's fader `mixer.strip.volume`.
  The master header and the master channel have their own ids (`track.master.*`, `mixer.master.*`).
- Retiring an id: keep its row here, mark it retired, and add `old: new` to `CONTROL_ALIAS` in index.html.
  `xtControlOf(element)` follows the alias table, so a rules file written for an older AudioLab keeps working.
- Adding a control in these areas: give it a row in `CONTROLS` and a row here (with the version), or the test fails.
- The test: `python3 tools/ui-tests/taskXT_DL1.py` fails when a control in these areas has no id, when an id listed
  here is missing from `CONTROLS` (and from `CONTROL_ALIAS`), or when `CONTROLS` has an id that is not listed here.
- Ids appear only in some states: `transport.tutorial` (only while the guided tour button is shown).
- Still without ids (DL7, control ids part 2): devices and their knobs, the piano roll, menus, Settings rows.

## Transport bar (`#tr`)

| Id | Control | Selector inside the area | Since |
|---|---|---|---|
| `transport.logo` | AudioLab menu button | `#bLogo` | 0.266 |
| `transport.assistant` | Assistant button | `#bAI` | 0.266 |
| `transport.locatorLeft` | left locator | `.lcd.loc:has(>#locL)` | 0.266 |
| `transport.locatorRight` | right locator | `.lcd.loc:has(>#locR)` | 0.266 |
| `transport.home` | Go to start button | `#bHome` | 0.266 |
| `transport.loop` | Loop button | `#bLoop` | 0.266 |
| `transport.stop` | Stop button | `#bStop` | 0.266 |
| `transport.play` | Play button | `#bPlay` | 0.266 |
| `transport.record` | Record button | `#bRec` | 0.266 |
| `transport.capture` | Capture button | `#bCap` | 0.266 |
| `transport.keyboard` | Keyboard piano button | `#bKbd` | 0.266 |
| `transport.tempo` | tempo box | `#bpm` | 0.266 |
| `transport.tempoUp` | tempo up arrow | `#bpmUp` | 0.266 |
| `transport.tempoDown` | tempo down arrow | `#bpmDn` | 0.266 |
| `transport.signature` | time signature | `.lcd.tempo .sig` | 0.266 |
| `transport.tap` | Tap tempo button | `#bTap` | 0.266 |
| `transport.metronome` | Metronome button | `#bClick` | 0.266 |
| `transport.countIn` | Count-in button | `#bCount` | 0.266 |
| `transport.clickPattern` | click pattern | `#mpat` | 0.266 |
| `transport.position` | position display | `.lcd:has(>#posBars)` | 0.266 |
| `transport.clock` | clock display | `.lcd:has(>#posTime)` | 0.266 |
| `transport.tutorial` | Tutorial mode button | `#bTut` | 0.266 |
| `transport.mixer` | Mixer button | `#mBtn` | 0.266 |
| `transport.masterMeter` | master meter | `#mtr` | 0.266 |
| `transport.clipWarning` | clip warning | `#niClipB` | 0.266 |
| `transport.peak` | peak level box | `#peakBox` | 0.266 |
| `transport.loudness` | loudness box | `#lufsB` | 0.266 |
| `transport.performance` | performance meter | `#cpu` | 0.266 |
| `transport.extra.gap` | flexible gap | `.trx-gap` | 0.266 |
| `transport.extra.space` | fixed space | `.trx-space` | 0.266 |
| `transport.extra.line` | divider line | `.trx-line` | 0.266 |
| `transport.extra.timeOfDay` | time of day | `.trx-tod` | 0.266 |
| `transport.extra.progress` | song progress | `.trx-prog` | 0.266 |
| `transport.extra.tap` | extra Tap tempo button | `.trx-tap` | 0.266 |
| `transport.extra.loopLength` | loop length | `.trx-sel` | 0.266 |
| `transport.extra.workTimer` | work timer | `.trx-work` | 0.266 |
| `transport.extra.section` | current section | `.trx-sect` | 0.266 |
| `transport.extra.sectionPrevious` | Previous section button | `.trx-nav [data-sn="-1"]` | 0.266 |
| `transport.extra.sectionNext` | Next section button | `.trx-nav [data-sn="1"]` | 0.266 |
| `transport.extra.midi` | MIDI activity light | `.trx-midi` | 0.266 |
| `transport.extra.clip` | clip indicator | `.trx-clip` | 0.266 |

## Track headers (`#hdrin`): one id per kind of control, shared by every track

| Id | Control | Selector inside the area | Since |
|---|---|---|---|
| `track.name` | track name | `.hdr .nm` | 0.266 |
| `track.fold` | group fold arrow | `.hdr [data-gfold]` | 0.266 |
| `track.volume` | track volume slider | `.hdr [data-c^="hd:"]` | 0.266 |
| `track.mute` | track Mute button | `.hdr [data-a=mute]` | 0.266 |
| `track.solo` | track Solo button | `.hdr [data-a=solo]` | 0.266 |
| `track.arm` | track Record arm button | `.hdr [data-a=arm],.hdr [data-z=arm]` | 0.266 |
| `track.edit` | Edit channel button | `.hdr [data-a=edit]` | 0.266 |
| `track.read` | Read automation button | `.hdr [data-a=read]` | 0.266 |
| `track.pan` | track pan slider | `.hdr [data-c^="hp:"]` | 0.266 |
| `track.writeAutomation` | Write automation button | `.hdr [data-a=aar]` | 0.266 |
| `track.lanes` | Automation lanes button | `.hdr [data-a=lanes]` | 0.266 |
| `track.freeze` | Freeze button | `.hdr [data-z=freeze]` | 0.266 |
| `track.effectsOff` | Effects off button | `.hdr [data-z=byp]` | 0.266 |
| `track.output` | track Output button | `.hdr [data-z=out]` | 0.266 |
| `track.sends` | track Sends button | `.hdr [data-z=sends]` | 0.266 |
| `track.color` | track colour button | `.hdr [data-z=color]` | 0.266 |
| `track.meter` | track level meter | `.hdr .vm` | 0.266 |
| `track.resize` | track height handle | `.hdr .rsz` | 0.266 |
| `track.lane.write` | lane Write button | `.lhd [data-la=w]` | 0.266 |
| `track.lane.editor` | lane Envelope editor button | `.lhd [data-la=ed]` | 0.266 |
| `track.lane.hide` | lane Hide button | `.lhd [data-la=x]` | 0.266 |
| `track.lane.resize` | lane height handle | `.lhd .lrz` | 0.266 |
| `track.recordAutomation` | Record automation button | `#bAR` | 0.266 |
| `track.showAutomation` | Show all automation button | `#bAut` | 0.266 |
| `track.add.audio` | Add audio track button | `.addrow [data-add=audio]` | 0.266 |
| `track.add.instrument` | Add instrument track button | `.addrow [data-add=inst]` | 0.266 |
| `track.add.return` | Add return track button | `.addrow [data-add=return]` | 0.266 |
| `track.master.volume` | master volume slider | `.mhdr [data-c="hp:master"]` | 0.266 |
| `track.master.effects` | master Effects button | `.mhdr [data-mact=fx]` | 0.266 |
| `track.master.mixer` | master Mixer button | `.mhdr [data-mact=mixer]` | 0.266 |
| `track.master.view` | master View button | `.mhdr [data-mact=view]` | 0.266 |

## Mixer (`#mixWin`): one id per kind of control, shared by every channel

| Id | Control | Selector inside the area | Since |
|---|---|---|---|
| `mixer.view` | mixer View menu | `#mxVw` | 0.266 |
| `mixer.spectrumOverlay` | Spectrum overlay button | `#mxDev` | 0.266 |
| `mixer.compact` | Compact channels button | `#mxCmp` | 0.266 |
| `mixer.cables` | Cables button | `#mxCab` | 0.266 |
| `mixer.settings` | Mixer settings button | `#mxSetB` | 0.266 |
| `mixer.close` | mixer Close button | `.fwh>.fwc` | 0.266 |
| `mixer.strip.name` | channel name | `.mx:not(.master)>.mxn` | 0.266 |
| `mixer.strip.instrument` | channel instrument slot | `.mxi .slot.inst` | 0.266 |
| `mixer.strip.device` | channel device slot | `.mxi .slot:not(.inst)` | 0.266 |
| `mixer.strip.display` | channel picture | `.mx:not(.master) canvas.mxv` | 0.266 |
| `mixer.strip.send` | channel send knob | `.mx:not(.master) .mxsnd [data-c]` | 0.266 |
| `mixer.strip.volume` | channel fader | `.mx:not(.master) .fwrap>[data-c]` | 0.266 |
| `mixer.strip.pan` | channel pan knob | `.mx:not(.master) .mxp [data-c]` | 0.266 |
| `mixer.strip.mute` | channel Mute button | `.mx:not(.master) .mxb [data-a=mute]` | 0.266 |
| `mixer.strip.solo` | channel Solo button | `.mx:not(.master) .mxb [data-a=solo]` | 0.266 |
| `mixer.strip.arm` | channel Record arm button | `.mx:not(.master) .mxb [data-a=arm]` | 0.266 |
| `mixer.master.name` | master channel name | `.mx.master>.mxn` | 0.266 |
| `mixer.master.pin` | master Pin button | `.mx.master .mxpin` | 0.266 |
| `mixer.master.display` | master picture | `.mx.master canvas.mxv` | 0.266 |
| `mixer.master.volume` | master fader | `.mx.master .fwrap>[data-c]` | 0.266 |
| `mixer.master.mono` | Mono button | `[data-mon=mono]` | 0.266 |
| `mixer.master.dim` | Dim button | `[data-mon=dim]` | 0.266 |
| `mixer.master.swap` | Swap left and right button | `[data-mon=swap]` | 0.266 |
| `mixer.ab.a` | mix A button | `.abt [data-ab=a]` | 0.266 |
| `mixer.ab.b` | mix B button | `.abt [data-ab=b]` | 0.266 |
| `mixer.ab.copy` | Copy mix button | `[data-ab=copy]` | 0.266 |
| `mixer.cables.sends` | cable legend Sends switch | `.cablg [data-cl=send]` | 0.266 |
| `mixer.cables.outputs` | cable legend Outputs switch | `.cablg [data-cl=out]` | 0.266 |
| `mixer.cables.sidechains` | cable legend Sidechains switch | `.cablg [data-cl=sc]` | 0.266 |
| `mixer.cables.selectedOnly` | cable legend Selected only switch | `.cablg [data-cl=sel]` | 0.266 |
| `mixer.cables.style` | cable legend Style switch | `.cablg [data-cl=sty]` | 0.266 |
| `mixer.cables.clashes` | cable legend Clashes switch | `.cablg [data-ni=clash]` | 0.266 |
| `mixer.strip.sendPrePost` | send before or after the fader ring (lane K, MX-1; named by XT-DL3) | `.mxsr .mxpp` | 0.295 |
| `mixer.strip.output` | channel Output button (lane K, MX-1; named by XT-DL3) | `.mx:not(.master) .mxout` | 0.295 |
| `mixer.master.monoLoss` | Mono loss button (lane D; named by XT-DL3) | `.mx.master [data-niml]` | 0.295 |

## Stem split (lane R, task SG2): written as `data-al` by the code itself

Not yet in `CONTROLS` (its areas are the transport, the track headers and the mixer); lane H adds them when the Workshop covers dialogs.

- `stem.lanes`: the lanes of a stem split (Split sheet, Audio to MIDI) (0.307)
- `stem.keepWorking`: Keep working button (0.307)
- `stem.stop`: Stop button (0.307)
- `stem.discard`: Discard button (0.307)
- `stem.add`: Add N tracks button (0.307)
- `stem.lane.keep`: a stem's tick (0.307)
- `stem.card`: the stem split card (0.309)
- `stem.card.close`: its ✕ (0.309)
- `stem.card.open`: Open (0.309)
- `stem.card.stop`: Stop (0.309)
- `stem.card.undo`: Undo (0.309)

## Instrument and Effects browser, catalogue (lane A, task DS-B1a): written as `data-al` by the code itself

Not yet in `CONTROLS` (its areas are the transport, the track headers and the mixer); lane H adds them when the Workshop covers dialogs.

- `browser.search`: the search field (DS-B1a)
- `browser.category`: a category on the left, All included (DS-B1a)
- `browser.row`: an instrument's or effect's row (DS-B1a)
- `browser.view`: Cards (in the catalogue) and List (in the cards) (DS-B1a)
- `browser.close`: the catalogue's ✕ (DS-B1a)
- `browser.preset`: a preset in the preview (DS-B1a)
- `browser.inTempo`: In tempo, next bar (DS-B1a)
- `browser.play`: play the preview again (DS-B1a)
- `browser.device`: the live device in the preview (DS-B1a)
