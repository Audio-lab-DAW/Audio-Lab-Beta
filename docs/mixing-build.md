# Mixing engine: the build plan (task MX, lane K)

Plan for the user's AE3 picks of 27 November 2026, 21:07 Brussels, the part that changes the audio graph:
`AE3 picks: X1 X3 X4 X5 X6 X8 X11 X12 X13 X14 X15 X16 X17 X18 X19 X20 X21 X22 X23 X25 X26 X27`.
Research, findings and the user's notes: `docs/research-mixing.md` (section 2 today's code, section 3 the findings, section 4 the options, section 5 the proposed tasks, and "The user's picks" at the end). The pick page `tools/engine-lab/ae3/mixing-picks.html` is the reference for look and behaviour (blue and yellow send rings, the output menu, the tails Ducker, the spectral ducking picture).

Written in step MX-0 (27 November 2026). `index.html`, `desktop/` and `native/` were not touched in this step.

Lane K owns the audio graph: `syncGraph`, `busRoute`, `fxLat`, `trkLat`, `pdcMap`, `renderMix` (and `renderMixChunked`'s graph part), sends pre and post, outputs, sidechain sources (`abxPickSrc`, `abxReach`, `abxWire`, `abxOpts`, `abxKeys`) and the Ducker's focus. Everything else is another lane's; what lane K needs there goes through a hook (`MX_HOOKS.<name>`) and a line in the log saying which lane picks it up.

## Status

| Step | Options | What | Status |
|---|---|---|---|
| MX-0 | | this plan | **done** (27 Nov) |
| MX-1 | X12, X13 | pre or post per send (blue and yellow rings); output to any group, return or track; one loop check for every link | **done** (v0.294) |
| MX-2 | X5, X6 | delay compensation for returns, sends and sidechain triggers, live and in export; latency changes re-aligned without a click; latency you can see, subtly, in few places; first the `S.pauto` export check (end of this file) | next |
| MX-3 | X1, X4 | sidechain from anything (`mxScPick`, tap points) on Compressor, Gate, Multiband, OTT and the EQ's dynamic bands; "Duck under the kick" on each return and in the cable menu | |
| MX-4 | X3, X19 | the Ducker's Spectral focus (32 bands); Bass mono switch; `MX_HOOKS.bandFilter` for lane E's band listen (X17) | |
| MX-5 | (X7 replaced) | the user's play-through idea, **only if this repository records the user's yes**; otherwise the run says "MX waits for the user's answer on the play-through idea" and stops | waits for the user |

After the last step the run says "mixing engine complete".

## Rules every step keeps

- **Old projects sound the same.** Every new field is optional and absent means today's behaviour. A project without the new settings builds exactly today's nodes (no extra gain, delay or worklet in the path) so it renders **bit-identically**: each step runs `tools/engine-tests/export_same.py` on Fractals and compares with the newest backlog numbers: Kick -19.05560 dB (fb577dd5202b), Bass -35.48685 dB (392ec52590c7) with the master at -10 dB; -9.75669 dB (0496bb147f6c) and -25.48699 dB (09e0415bec5e) at 0 dB (measured in the v0.261 to v0.273 entries). Each log says which of these it measured on its own build.
- **Export equals playback within 0.1 dB** for every new path (the step's test renders the same scene through `renderMix` and records it live through the app's graph).
- **Exception that is the point of MX-2:** a project whose return or send path has latency today (a compressor or a limiter on a return, for example) is now lined up. That changes timing on purpose; the log names it and the test shows the before and after. Projects without latency on those paths stay bit-identical.
- No per-frame work while idle (nothing new in `requestAnimationFrame` or intervals; read-outs refresh on `changed()` and on the existing meter tick only while playing).
- Dark and Light, plain language, no em dashes in UI text, a tooltip on every new control, glass from the engine only (`LOOK` tokens, no new glass of my own).
- New JS before `function askChoice(title,text,btns,icon){`, new CSS before `.dacv{display:flex;`. Every new top-level name starts with `mx` or `MX_`; hooks for other lanes live in one object `window.MX_HOOKS`. Existing functions of lane K are changed in place by the edit script (asserted unique anchors) or wrapped once, never renamed.
- Edit scripts `tools/engine-lab/mx/mx<step>.py` (Python, unique asserted anchors, re-runnable on a fresh `index.html` after a rebase), tests `tools/ui-tests/taskMX_<step>.py` (headless Chromium through the app). Before every push: `git pull --rebase`, re-run the edit script on the fresh file, the UI tests, the lint and the start-up smoke test of `docs/release-gate.md` (`python3 tools/release-gate/gate.py --here --skip-ui` or `--quick`), and check no top-level function name is defined twice.
- Release per step: VERSION = the highest on main + 0.001, `node desktop/scripts/sync-app.js` (never `desktop/app-version.json`), one line in `desktop/update-notes.txt`, a `docs/backlog-log.md` entry headed "task MX-<step>" with what is left, the line in "Where it stands" of `docs/device-backlog-2026-11-25.md`, this file's status row, the project doc `claude/audiolab-mixing-build.md`, the notification "Mixing step MX-<step> is out (vX.XXX): ...", and `index.html` (lines 3 to 10 removed) published to the artifact.

## Where the code is (anchors in `index.html` at v0.273)

| What | Anchor | Notes |
|---|---|---|
| track nodes | `function syncGraph(){`, the `if(!N){N={ut:mkUtil(ctx),...` line | live chain `N.in → effects → N.pdc (DelayNode) → N.ut (width, phase, trim) → N.vol → N.pan → N.dest`; meters on `N.pan`. `N.slp` (sleeping tracks, lane J's LT-4 later) disconnects `N.ut.out → N.vol`: new taps must not undo that. |
| outputs and sends | `function busRoute(){` | `N.pan` to the group's `G.in` or `master`; sends `N.snd` (a GainNode per return) tapped from `N.pan`, so post-fader and post-pan; muted tracks' sends are silent. |
| groups | `grpOf`, `grpAnc`, `grpMembers`, `trkAudible`, `groupTracks` | `t.grp` is also the arrangement's folder; X13 must not change it. |
| returns | `const RETN=`, `function retNew(` | |
| compensation | `function fxLat(f,sr)`, `const trkLat=`, `function pdcMap(sr)` | tracks only: `path = own latency + groups' latency`, delay = target - path. `UI.pdc===false` turns it off. Lane J's LT-2 (planned) adds `pdcMap(sr,live)` and `LT_HOOKS.pdcLive` (the played track outside compensation while playing): MX-2 keeps that signature and that hook, whichever lands first. |
| export | `async function renderMix(sr,b0,b1,tail,lim,only,fast,prog){`, `renderMixChunked`, `doExport` | builds the same graph offline: effects, `PDC` delay, fader, pan, groups, sends from `pn`, Ducker keys from `n.pre`. **It does not build the utility** (width, phase, trim) that the live graph has: MX-1 checks this and, if true, adds it only for tracks where width, phase or trim differ from neutral (old projects that never touched them stay bit-identical). |
| Ducker | `function abxNode(c)`, `abxReach`, `abxWire` (wrapper on `syncGraph`), `abxKeys`, `abxPickSrc`, `abxOpts`, `abxConnect`, `abxMake`, `abxCabMenu`, `ABXFO` (focus all, low, band, high), worklet `al-abxduck` | key tapped at the source's `N.ut.out` (after effects, after compensation, before the fader). Lane D's `NI_HOOKS.duckBandRow` adds a band row to the Ducker's focus: kept. |
| Compressor | `if(type==='comp'){` in `mkFxNode` | a `DynamicsCompressorNode`: no key input. |
| Gate, Multiband, OTT, EQ | `ND('gate'`, `ND('mband'`, `if(type==='ott')`, `mkEQ2` and the band menu's "Make dynamic" (`b.dyn`) | inventory in MX-3 which are worklets with a free input and which are browser nodes. |
| mixer | `renderMixer`, `drawMixer`, `function mxSends(` | the send knobs are drawn by `mxSends` (lane K owns the sends). The strip's other parts belong to lanes A, C, E and I. |
| cables | `const CAB=`, `cabDraw`, `cabSoon`, `cabList`, `cabPop`; lane D's masking cables (I12) | the cable menu itself is `abxOpts`/`abxCabMenu` (sidechain sources, lane K); lane D's own cable drawing gets a hook if it draws a menu of its own. |
| the track's first device | `.tdev2` (the channel strip on the left of the device chain, with the main volume), built near `<div class="dev tdev tdev2" data-d="track"` | X6's first read-out goes here, small. |
| master | `routeMaster`, `syncMaster` | master effects, limiter, `outBus`. |

## Hooks lane K offers (`window.MX_HOOKS`)

| Hook | Step | For |
|---|---|---|
| `links()` → every link of the project `{k:'out'|'send'|'sc', a, b, pre, tap, lat}` | MX-1 (sc from MX-3, lat from MX-2) | lane C's routing map (X11), lane D's cables |
| `canLink(a,b,kind)` → `{ok, why}` (one loop check for outputs, sends, sidechains) | MX-1 | lane C (routing map drag), lane D |
| `outOf(t)`, `setOut(t,id)` | MX-1 | lane C (X11 drag to re-route) |
| `tap(t,point)` → the live node at "before effects", "after effects", "after fader", "after group" | MX-1 | lane C's bounce with a tap point (X8, "after group" needs MX-1) |
| `lat(t)`, `devLat(t,f)`, `pathLat()` → ms and samples, the longest path and the device that sets it | MX-2 | lane I (device hover in the title strip), lane C (routing map) |
| `scBadge(t,f)` → the source's name and colour, or null | MX-3 | lane I's `DV_HOOKS.scBadge` in the title strip |
| `duckTails(ret, kick)` → puts the tails Ducker and returns it | MX-3 | lane D's cable menu (if it draws its own), lane C |
| `bandFilter(ctx, lo, hi)` → `{in, out}` (Linkwitz-Riley band) | MX-4 | lane E's band listen (X17) and the low-band correlation (X19 meter) |
| `bassMono(t)` → `{on, f}` | MX-4 | lane E (X19's warning on the strip) |

What lane K asks of other lanes: lane I shows `MX_HOOKS.devLat` on a device's hover and `MX_HOOKS.scBadge` in the title strip; lane B, if a Settings row is wanted, reads `UI.pdc` (already there) and nothing new; lane F, when its notification API exists, may show "Delay compensation is now X ms (Reverb return: Limiter)"; lane E draws the band correlation with `MX_HOOKS.bandFilter`.

## MX-1: X12 pre or post per send, X13 output to any bus

**Data (optional fields):** `t.sendPre = {returnId: true}` (absent = post, as today); `t.out = id` of a group, return or another track (absent = the group in `t.grp`, else the master, as today). `t.grp` stays the arrangement's folder: X13 does not regroup.

**Engine:**
- Post sends unchanged (from `N.pan`). A pre send taps after effects, compensation and the utility, before the fader (`N.ut.out`), through its own GainNode whose gain is `level × (audible ? 1 : 0)`: pre sends ignore the fader but follow mute and solo (as Cubase and Bitwig). A sleeping track (`N.slp`) keeps its pre sends asleep too.
- `busRoute`: destination = `t.out`'s input when set and allowed, else today's. Into a track: the signal enters that track's `N.in` and plays through its chain together with its clips (the resampling path; recording it is lane C's).
- `renderMix`: the same rules (pre sends from the node before `vol`, outputs from `t.out`), so export equals playback; the utility check above.
- Loop check `mxReach(b,a)`: one walk over groups, `t.out`, sends (pre and post), Ducker keys and (from MX-3) sidechain keys; `abxReach` calls it so the Ducker and every new link refuse loops the same way, with the reason in plain words ("Bass already plays into Perc glue, so this would make a loop").
- Solo: a track routed to a return or a track counts as feeding it (a soloed track's destination stays audible, as a soloed member keeps its group).

**UI (lane K's parts only):**
- Each send knob in `mxSends` gets a thin ring: blue before the fader, yellow after it (the pick page's colours, from `LOOK` when the tokens exist; added as new tokens otherwise). Click the ring (or the knob's right-click menu "Before the fader" / "After the fader") to switch; tooltip "Blue: taken before the fader, so fading the track keeps its send. Yellow: after the fader. Click to switch."
- An output menu on the strip's output label (or, if that label is another lane's, a small "Out" entry in the strip's right-click menu through a hook): Master, every group, every return, every other track; refused entries greyed with their reason. Tooltip on the label.
- Cable menu (`abxOpts`): "Play into <bus>" for a return or a track as a destination (today only groups and the master).
- Undo: one step each.

**Test `tools/ui-tests/taskMX_1.py`:**
- A 1 kHz test tone on a track with a send to a return (no effects): post send measured at the return follows the fader (fader -12 dB → return -12 dB); pre send stays (within 0.05 dB) when the fader moves; mute silences both.
- Output to a group, a return and a track: the tone arrives at that bus and not at the master directly; a loop (A out to B, B out to A; a return out into a track that sends to it) is refused with a reason.
- Export equals playback within 0.1 dB for each scene (live recorded through the graph against `renderMix`).
- Fractals bit-identical (hashes above); an old project saved without the fields loads and its JSON round-trips without new keys.
- UI: ring colours in Dark and Light, tooltips present, no console errors, frame time while idle unchanged.

## MX-2: X5 compensation for every path, X6 latency you can see

**Model:** one graph of points: each track's input, each bus's input (groups, returns, tracks that receive outputs), the master, and each sidechain key input inside a device. Edges: a track's output (to its group, `t.out` or the master), each send (pre or post), each Ducker or sidechain key (from MX-3) with the latency of the devices before the keyed device. Latencies from `fxLat` (and the native engine's reports later, task NB). Solve as a longest path over the loop-free graph (the loop check guarantees none): the time each point's signal is ready; every edge gets the delay that makes its signal arrive with the others; a key that would arrive late pushes the keyed track later instead (delays are never negative). The master target is the longest path to the master.

**Nodes:** today's `N.pdc` keeps the delay common to all of a track's edges (so tracks with no sends or keys are exactly as today); an extra DelayNode only on an edge that needs more (a send, an output, a key). Renderer builds the same delays from the same function, so live and export agree to the sample.

**Lane J:** the function keeps `pdcMap(sr,live)` and asks `LT_HOOKS.pdcLive` (when LT-2 has landed) which tracks are played live: those get no extra delay while playing, exactly as LT-2 does; the rest of the graph is solved without them. If LT-2 lands after MX-2, its hook goes into the same function (it is lane J's small hook in lane K's `pdcMap`).

**Changes while playing:** when a device's latency changes (a look-ahead turned up, a device added), the delays move with a short fade (about 8 ms down and up on the affected edges) instead of a jump, so there is no click; nothing runs while nothing changes.

**X6, subtle and in few places (the user's note):**
1. The track's first device on the left (the channel strip with the main volume, `.tdev2`): a small grey read-out under the name, only when the track's own devices add latency: "6.0 ms" (the unit in the small-caps unit style of `LOOK`/`lkVU` when present). Tooltip: "This track's devices delay its sound by 6.0 ms (288 samples). AudioLab delays the other tracks to match. Longest path in the song: 52.5 ms (Lead, Resonance suppressor)."
2. A device's hover: through `MX_HOOKS.devLat(t,f)` for lane I's title strip (lane K does not draw there).
3. The routing map later (lane C, `MX_HOOKS.pathLat`).
Nowhere else: no badge on every surface, no master read-out unless lane C's routing map asks.

**Test `tools/ui-tests/taskMX_2.py`:** an impulse on a source track through every path (direct, through a group, through a post and a pre send into a return with a 6 ms Compressor, through a return with a 2 ms look-ahead Limiter, through an output into a track with a pitch device, a Ducker key from a latent track) arrives at the master **on the same sample**, live (recorded through the graph) and in export; changing a latency while playing re-aligns with no sample over -60 dB of click energy beyond the fade; `UI.pdc=false` still turns it all off; LT's played-track exception still holds when `LT_HOOKS.pdcLive` exists; Fractals bit-identical (Fractals' returns: measure whether any carries latency and say so); the read-out shows only on tracks with latency, in Dark and Light; idle frame time unchanged.

## MX-3: X1 sidechain from anything, X4 duck under the kick

**Sidechain menu:** a row "Sidechain" with the source's dot and name on Compressor, Gate, Multiband, OTT and the EQ's dynamic bands (and later VST3 plug-ins with a sidechain bus, through the native engine). The menu, `mxScPick(f,x,y)`, is built on `abxPickSrc` and `mxReach`: every track except itself, its groups and tracks it already reaches; each with tap points "after its effects" (default, as the Ducker today), "after its fader", "before its effects", and one level down any device in its chain ("after <device>"). Data: `f.p.sc = {src, tap, dev}` (absent = no sidechain, the device as today).

**Engine:** a device with a source gets the key on a second input:
- devices that are worklets: a second input (the Ducker's pattern);
- the Compressor is a browser `DynamicsCompressorNode` with no key input: with a source set it switches to a keyed worklet compressor (`al-mxcomp`) made to match the browser node's static curve (threshold, ratio, 6 dB knee, attack, release, make-up) within 0.5 dB on a steady tone; **without a source it stays the browser node, so old projects are bit-identical**;
- MX-3 starts by listing which of Gate, Multiband, OTT and the EQ's dynamic bands are browser nodes and which are worklets, and gives each the same treatment.
Keys are wired in `abxWire`'s place (one `mxWire` for every keyed device, wrapping `syncGraph` once) and in `renderMix` (today's `ABD` list grows to every keyed device), with MX-2's compensation on the key edge. The badge in the title strip is lane I's: `MX_HOOKS.scBadge(t,f)` (and `DV_HOOKS.scBadge` used if lane I has made it).

**X4 "Duck under the kick", tuned for tails:**
- A switch on each return (in the return's channel strip and the mixer strip's menu): on puts a Ducker on the return with attack fast (0.5 ms), hold 0, recovery one 16th at the song tempo (`15/bpm` s, re-tuned when the tempo changes while the switch is on, marked `f.p.mxTail`), keyed from the kick track, and draws its cable. The kick track: the one named "Kick" or lane D's kick analysis (`NI_HOOKS.kickBass`) when present, else the user picks (menu).
- **In the cable menu too (the user's note):** whenever a cable is drawn to a sidechain or to a Ducker, `abxOpts` offers "Duck under <kick>, tuned for tails" next to the plain Ducker. If lane D's masking cables draw a menu of their own, they call `MX_HOOKS.duckTails`.

**Test `tools/ui-tests/taskMX_3.py`:** a Compressor on the bass keyed from the kick reduces the bass only on kicks (gain reduction above 3 dB within 10 ms of each kick, under 0.3 dB between them); the same through Gate, Multiband, OTT and a dynamic EQ band; loops refused; a Compressor without a source renders bit-identically to before; export equals playback within 0.1 dB; the tails switch gives the release 15/bpm s and follows a tempo change; the cable menu offers the tails choice; Fractals bit-identical.

## MX-4: X3 spectral ducking, X19's Bass mono switch

**Spectral focus:** a fifth focus "Spectral" for the Ducker (`ABXFO`): 32 bands (third-octave-like, 20 Hz to 20 kHz); in each band the ducked track goes down only as much as the key is present there and only while it sounds (amount, attack, release from the Ducker's dials). Built as an STFT in the Ducker's worklet (Hann, 75 % overlap, unity when nothing ducks), so its latency is reported by `fxLat` and compensated by MX-2. Other focus modes unchanged (bit-identical). Lane D's `NI_HOOKS.duckBandRow` keeps working; NI-5b's "duck in this band" fix can call it.

**Bass mono:** a switch with a frequency (50 to 500 Hz, 120 by default) on any track and the master: below the frequency the side goes away (side through a Linkwitz-Riley high-pass, the mid through the matching all-pass so the sum stays flat), built in the track's utility only when on (old projects: no nodes). Data `t.bmono = {on, f}`, `S.bmono` for the master. The filter is exported as `MX_HOOKS.bandFilter(ctx, lo, hi)` for lane E's band listen (X17) and low-band correlation (X19's meter and warning are lane E's).

**Test `tools/ui-tests/taskMX_4.py`:** kick keying a bass made of 60 Hz and 300 Hz: the 40 to 120 Hz band ducked by more than 6 dB on kicks while 300 Hz stays within 0.5 dB; with nothing ducking the spectral Ducker is within 0.1 dB of the input; Bass mono at 120 Hz: a side-only 60 Hz tone falls by more than 30 dB, a side-only 1 kHz tone within 0.2 dB, a mono signal within 0.1 dB at every frequency; export equals playback; Fractals bit-identical.

## MX-5: the user's play-through idea (waits for the user)

The idea (the user's, written in `docs/research-mixing.md`): while playing a track, its dry part plays at once and the wet part of a parallel device (a send to a reverb, a Mix knob) comes in when it is ready; a device with look-ahead runs a low-latency stand-in while playing, the exact version in playback and export. The research's answer: Cubase, Ableton, Logic, Studio One and Pro Tools all have a monitoring mode of this family, but none lets the slow part of the played track arrive late on purpose. It shares the played-track path with lane J (LT-2).

**Gate:** the run first reads `docs/research-mixing.md` (and the newest backlog entries) for the user's yes. Without it the run says "MX waits for the user's answer on the play-through idea" and stops. With it, this section is expanded into the build plan (with lane J's hook) before building.

## What is not lane K's
X8 bounce with a tap point (lane C, through `MX_HOOKS.tap`), X9, X10, X11 routing map (lane C, through `MX_HOOKS.links`, `canLink`, `pathLat`), X14, X15, X20, X21, X22, X26 (lane C); X16, X18, X23, X27 (lane D); X17 band listen, X19's meter, X25 (lane E, with `MX_HOOKS.bandFilter`); X5 for VST3 in the native engine (task NB).

## Added 27 Nov 2026, 21:48 Brussels: a bug to fix first (from the sound-quality research AE1)

`docs/research-engine-sound.md` (side findings) reports that device parameter automation (`S.pauto`, applied by `paApply` from the main thread every 33 ms while playing) seems not to be rendered by `renderMix` / `renderMixChunked`: an export would differ from what plays. Verify with a render (a filter sweep automated on a device, export against a live recording); if it holds, render it in the export at sample accuracy (and say how close live playback is). Do it in your next step before or together with MX-1's remainder. Lane N (SQ) changes only the export's post-processing (`postProc`: the safety limiter, dither, the report), not the graph.

## Added from the speed and feel picks (UX1, 27 Nov 2026, 22:02 Brussels)

S18: export renders in slices (renderMixChunked) so the screen answers within 100 ms; lane F shows the progress line.
