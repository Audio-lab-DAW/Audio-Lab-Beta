# Mixing workflow and clarity (task AE3, 27 November 2026)

**Pick page:** https://claude.ai/artifact/1ctqK1M5mMUXtesYDWpqPy (title "AudioLab mixing: workflow and clarity"). 27 options (X1 to X27) in seven groups, nine starred. Tick the ones you want; the bar at the bottom gives one line to paste, for example `AE3 picks: X1 X2 X5 | note`.

This was a research and pick-page task only. Nothing in `index.html`, `desktop/` or `native/` was changed. The page source and a check script are in `tools/engine-lab/ae3/`.

## 1. Summary

The user asked (27 Nov, 20:02 Brussels) for audio-engine research on mixing workflow, and named the pains in a big psytrance project: latency when playing and mixing clarity (hard to hear or see what clashes, kick and bass, loudness).

What AudioLab already has is more than most DAWs in some places (a Ducker that takes any track as its trigger, LUFS and true peak, a Meter device with correlation, reversible freeze) and the running plans cover a lot (cards F16, F18, F25, F27, F29; ideas I1, I2, I4, I12, I13, I14, I15; the meter picks). The gaps the research found, and that no plan covers yet:

1. **Sidechain only reaches the Ducker.** The Compressor has no sidechain input, and nothing else can be keyed from another track. Every DAW studied lets any dynamics device pick any track, with a tap point (X1).
2. **Delay compensation stops at groups.** Returns, sends and sidechain triggers are not compensated (code: `fxLat`, `trkLat`, `pdcMap`, `N.pdc`; v0.146). For KBBB psytrance, where kick and bass sit a few ms apart, this matters, and the native plan needs full compensation for VST3 anyway (X5). Latency is not shown per device (X6), and there is no low-latency monitoring mode for playing through heavy devices (X7, shared with the performance research).
3. **Sends are post-fader and post-pan only; output goes to the parent group or the master only** (`busRoute`). No pre-fader sends (X12), no free output routing (X13), no overall view of where signals go (X11).
4. **Bounce and freeze do not say where they record from.** Freeze is with or without effects; Bounce takes a whole track or a clip (X8, X9, X10).
5. **Clarity:** the planned masking cables (I12) and kick and bass lab (F18, I2) are the right ideas. The research shows how to make them better: count clashes in time, not on average, because in KBBB kick and bass share 40 to 120 Hz but take turns (X16); and draw the kick, the bass and their sum on one time axis with polarity and nudge, which is exactly what psy producers do by hand in bounced audio (X15).
6. **References and loudness:** F25 plans level-matched slots and overlaid spectra. A difference line around 0 dB, four band lights and a low-end punch needle read faster (X21); no commercial tool ships a psytrance target (X22). No device has a gain-matched bypass (X20).
7. **Snapshots:** Mix A/B stores fader, pan, mute and solo only. F29 should store the whole mixer with partial recall, as Studio One and Cubase do (X26).

Recommended (the stars): X1, X2, X5, X8, X11, X15, X16, X21, X26.

## 2. What AudioLab has today (v0.263, read in index.html)

- **Tracks** (`mkTrack`): kinds audio, inst, group, return. Groups nest through `t.grp` (`groupTracks`, `grpOf`, `grpAnc`, `grpMembers`). Returns from `retNew`. Sends are `t.sends = {returnId: level}`, no pre/post flag. The master is `S.master` with effects `S.mfx`.
- **Graph** (`syncGraph`): `in → effects → pdc delay → utility (width, phase, trim) → fader → pan`, meters after the pan. `busRoute` connects each track to its group or the master; sends are taken from `N.pan`, so they are post-fader and post-pan and a muted track's sends are silent too.
- **Master** (`routeMaster`, `syncMaster`): master gain → master effects → limiter → `outBus` → monitor section (`monSet`: DC block, balance, mono, swap, dim).
- **Sidechain:** the "Sidechain" effect (`side`) is a tempo pump; "Duck to kick" only points it at the kick track. The **Ducker** (`duck`, worklet `al-abxduck`) is a real audio-rate sidechain: source any track except itself, groups and tracks that already reach it (`abxPickSrc`, `abxReach`), tapped after effects and before the fader (`abxWire`), with amount, trigger level, attack, hold, release, curve, look-ahead, focus (all, lows, one band, highs), listen; cables between strips (`abxConnect`). No note trigger. The **Compressor** is a plain DynamicsCompressor, no sidechain.
- **Delay compensation** (v0.146): `fxLat` per effect (compressor 6 ms, multiband 6.2 ms, clipper up to 192 samples, limiter and gate look-ahead, pitch tools 2048 samples), `trkLat`, `pdcMap` with group effects; each track delayed by `N.pdc`. Returns and sends not compensated. `UI.pdc` turns it off.
- **Mixer** (`renderMixer`, `drawMixer`, `mxSends`): strips with inserts, a picture (wave, meter, spec, stereo), fader with meter, pan, M/S/arm; master with LUFS, peak, true peak, target, correlation, Mix A/B.
- **Export and render:** `renderMix` (OfflineAudioContext, with groups, sends, compensation, Ducker triggers, master effects), `renderMixChunked`, `doExport` (mix or stems; stems use `only=trackId`, so without group or sends). Freeze (`freezeAsk`, `freezeTrack`, kept in `t.frz`, chain stays live from the first sidechain effect). Bounce of a track (`bounceTrack`) or a clip (`bounce`, `bounceRender`).
- **Loudness and checks:** EBU R128 worklet `al-meter` (M, S, I, LRA, true peak), targets `LMT`; the Meter device (loudness, levels, spectrum, low end with mono check, spectrogram, vectorscope, correlation, width per band); master Mono and Swap; one reference song (`REF`, into `outBus`, not level-matched); Mix A/B (`MAB`: fader, pan, mute, solo); Time Machine.
- Not confirmed: whether `renderMix` applies the utility (width, phase, trim); worth a check by whoever builds X8 or X10.

## 3. Findings with sources

### 3.1 Sidechain from anything, and ducking by shape
- Bitwig: dynamics devices and plug-ins have a sidechain menu listing tracks before or after the fader, and a nested menu to any point inside a chain or a Drum Machine pad. https://www.bitwig.com/learnings/sidechaining-tutorial-49/
- Bitwig modulators: Audio Sidechain (any audio in the project) and Note Sidechain (an ADSR gated by any note source) can drive any parameter. https://www.bitwig.com/userguide/bws44-504/modulator
- Live 12: Compressor's sidechain lists Live's routing points; tap Pre FX, Post FX or Post Mixer. https://ableton.com/manual/live-audio-effect-reference
- Cubase: a Side-Chain Routing panel per plug-in, several inputs where the plug-in supports it. https://steinberg.help/nuendo/v12/en/cubase_nuendo/topics/audio_effects/audio_effects_side_chain_multiple_inputs_creating_t.html
- Logic: Side Chain menu in the plug-in header (tracks, inputs, buses). https://help.apple.com/logicpro/mac/10.4/en.lproj/lgcpbc21a1fd.html
- FL Studio: "Sidechain selected to this track" and the Peak Controller (negative volume ducks). https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/mixer_mixermenu.htm, https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/plugins/Fruity%20Peak%20Controller.htm
- REAPER: track channels 3/4 and the pin matrix; sends can be tapped after any insert. https://www.soundonsound.com/techniques/reaper-using-tracks-internal-channels
- Kickstart 2: 16 fixed curves; sync, MIDI or audio trigger. https://www.musictech.com/reviews/plug-ins/cableguys-kickstart-2-review/ ; Cableguys MIDI retrigger: https://www.cableguys.com/support/midi-triggering
- Spectral ducking: Trackspacer (32 bands, inverse curve of the sidechain, depth, HP/LP limits, M/S, attack and release) https://www.musictech.com/reviews/wavesfactory-trackspacer-review/ ; soothe2 with sidechain (Attack's kick-to-bass example ducks most around 170 Hz) https://www.attackmagazine.com/technique/tutorials/frequency-sidechaining-with-oeksound-soothe2/ ; Sonible smart:comp spectral ducking https://www.sonible.com/blog/smartcomp-working-with-sidechain-ducking/ ; Pro-Q 4 dynamic bands on the external sidechain https://prod.fabfilter.com/help/pro-q/using/dynamic-eq
- Lesson: pick the source where it is used, show the tap point, show links as wires or badges; keep the trigger (tempo, notes, audio) separate from the shape.

### 3.2 Delay compensation and low-latency monitoring
- Live compensates audio, automation and modulation, but returns fed back into an audio track are not compensated; latency shows on hovering the device title. https://help.ableton.com/hc/en-us/articles/209072409 ; Reduced Latency When Monitoring bypasses compensation for armed tracks, with side effects (late returns, misplaced automation). https://help.ableton.com/hc/en-us/articles/209072249
- Logic compensates and has Low Latency Mode with a Limit slider that routes the monitored track around plug-ins over the limit. https://help.apple.com/logicpro/mac/10.4/en.lproj/lgcpe11997ba.html
- Cubase Constrain Delay Compensation switches off latent plug-ins on record and instrument channels (FX channels are unaffected). https://archive.steinberg.help/nuendo/v12/en/cubase_nuendo/topics/vst_instruments/vst_instruments_constrain_delay_compensation_c.html
- Studio One native low-latency monitoring (green Z): plug-ins over about 3 ms are silenced on the monitor path. https://support.presonus.com/hc/en-us/articles/360045431251
- FL Studio automatic PDC covers inter-track routing and sidechains; the PDC icon turns orange and the hint bar shows the latency. https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/mixer_trackprops.htm
- soothe2's manual: main and sidechain must arrive in sync; the DAW's bus compensation handles it. https://oeksound.com/manuals/soothe2/
- Psy producers do not trust compensation and nudge the bass in bounced audio. https://psynews.org/forums/topic/72935-the-ins-and-outs-of-psytrance-bassline
- REAPER anticipative FX and Bitwig's monitoring behaviour: not verified from official pages in this run.

### 3.3 Freeze, flatten, bounce in place
- Live 12: Bounce Track in Place replaces Freeze and Flatten; single tracks post-FX pre-mixer, groups post-mixer. https://www.ableton.com/en/live-manual/12/bounce-to-audio/
- Bitwig: source Pre-FX, Pre-Fader, Post-Fader or Custom (any junction); Bounce In Place replaces the clip. https://www.bitwig.com/userguide/latest/bouncing_to_audio
- Cubase Render in Place: Dry, Channel Settings, Complete Signal Path, Complete Signal Path + Master FX; tail in bars or seconds. https://archive.steinberg.help/cubase_pro/v12/en/cubase_nuendo/topics/rendering_to_audio/rendering_to_audio_render_selection_r.html
- Logic Freeze Source Only or Pre Fader; Bounce in Place with options. https://support.apple.com/guide/logicpro/freeze-tracks-lgcpf1cbfd51/mac , https://help.apple.com/logicpro/mac/10.2.1/en.lproj/lgcp8aa3b784.html
- Studio One (Fender Studio Pro manual): Freeze to Audio Track keeps the original state so it can be undone. https://fenderstudiopromanual.fender.com/en/Content/Editing_Topics/Track_Freeze.htm
- REAPER: freeze up to a chosen FX. https://reaper.blog/2017/07/freeze-selected-fx
- FL Studio Consolidate (insert FX in, master FX out by default). https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/playlist.htm

### 3.4 Routing that stays understandable, VCA
- Bitwig sends Pre, Post or Auto, blue and yellow rings. https://bitwig.com/userguide/latest/the_mix_view
- Logic folder stacks (no routing change) versus summing stacks (a bus). https://help.apple.com/logicpro/mac/10.4/en.lproj/lgcp9bc4b63d.html
- Cubase 15.0.20 folders with Group Channel mode. https://www.soundonsound.com/techniques/cubase-pro-folder-tracks-and-group-channels-v15020?amp
- REAPER Routing Matrix https://www.soundonsound.com/techniques/route-master and VCA grouping (master governs slaves without moving their faders) https://www.soundonsound.com/techniques/reaper-vca-grouping-linking
- Studio One VCA: relative automation shown as a grey line beside each track's volume, Merge VCA Automation. https://fenderstudiopromanual.fender.com/en/Content/Mixing_Topics/VCA_Channels.htm
- FL Studio mixer cables; sources keep the master send by default (a common source of doubled signals). https://www.image-line.com/support/flstudio_online_manual/html/mixer_iorouting.htm

### 3.5 Mix snapshots
- Studio One Scenes: partial recall by group (volume/pan/mute, inserts, sends, selected channels only). https://fenderstudiopromanual.fender.com/en/Content/Mixing_Topics/Scenes.htm
- Cubase MixConsole Snapshots, recall undoable in MixConsole History. https://steinberg.help/nuendo/v12/en/cubase_nuendo/topics/mixconsole/mixconsole_snapshots_c.html
- REAPER SWS snapshots with filters. https://sws-extension.org/snapshots.php
- Logic, Live, Bitwig, FL: no built-in mixer scenes found (absence not verified).

### 3.6 Gain staging, mid/side, mono
- Live Utility: gain to +35 dB, Mono, Bass Mono 50 to 500 Hz, Width, Mid/Side. https://www.ableton.com/en/live-manual/12/live-audio-effect-reference/
- Logic Gain plug-in (phase invert, swap, mono). https://support.apple.com/ro-md/guide/logicpro/gain-controls-lgcef2d8c650/11.0/mac/13.5
- Cubase Pre-Gain. https://archive.steinberg.help/nuendo/v13/en/cubase_nuendo/topics/mixconsole/mixconsole_making_input_gain_settings_t.html ; Studio One clip gain curves https://fenderstudiopromanual.fender.com/en/Content/Editing_Topics/Clips_and_Clip_Gain_Curves.htm
- Studio One Listen Bus has a mono switch on the monitor path. https://fenderstudiopromanual.fender.com/en/Content/Mixing_Topics/Listen_Bus.htm
- Ozone Imager: bands, correlation, vectorscope with safe lines. https://s3.amazonaws.com/izotopedownloads/docs/ozone9/en/imager/index.html

### 3.7 Reference matching and loudness
- Mastering The Mix REFERENCE: level match on by default; Level Line (difference around 0 dB, aim within ±3 dB), averaging 3 s, 10 s or integrated; punch dots per band; Track Align. https://www.masteringthemix.com/pages/reference-2-manual , https://www.masteringthemix.com/pages/reference-everything-you-need-to-know
- ADPTR Metric AB: up to 16 references, spectrum, correlation across the spectrum, dynamics, loudness match, band filters, L/R/side solo. https://www.musictech.net/reviews/plug-ins/adptr-audio-plugin-alliance-metricab/
- iZotope Tonal Balance Control: four bands with target ranges, low-end crest factor meter. https://s3.amazonaws.com/izotopedownloads/docs/tbc2/en/targets-and-views/index.html ; TBC 3 has about 35 genre targets, none for psytrance, and captures your own. https://weraveyou.com/2026/03/izotope-tonal-balance-control-3-review/
- Ozone Gain Match and the Reference panel (up to 10, LUFS matched). https://www.izotope.com/en/learn/how-to-use-ozone-utilities ; Master Assistant with a reference. https://izotope.com/en/learn/how-to-use-master-assistant-in-ozone
- Logic Mastering Assistant Loudness Compensation (level-matched bypass). https://support.apple.com/en-gb/108294
- Cubase has no reference feature; users still match by hand. https://www.soundonsound.com/techniques/cubase-pro-reference-tracks
- Loudness windows (M 400 ms, S 3 s, I, PLR). https://youlean.co/youlean-loudness-meter-measurements-explained/
- Targets: loud masters about −6 LUFS short-term at the loudest part; Spotify plays at −14 LUFS integrated. https://www.masteringthemix.com/pages/how-loud-should-you-master ; psy masters often −8 to −10 LUFS integrated, mix with peaks near −6 dBFS, limit 2 to 3 dB (vendor blog). https://www.myloops.net/common-psytrance-production-mistakes
- Loudness Penalty Studio: turn-down per service, level-matched playback. https://www.soundonsound.com/reviews/meterplugs-loudness-penalty-studio?amp

### 3.8 Clarity and masking tools
- iZotope Neutron Masking Meter: loudness loss (phons minus partial loudness) per critical band, red collision histogram with a 3 s hold, needs the pre-fader gain offset to be right. https://s3.amazonaws.com/izotopedownloads/docs/neutron4/en/masking-meter/index.html ; Unmask (32 bands, dynamic, sidechain). https://s3.amazonaws.com/izotopedownloads/docs/neutron4/en/unmask/index.html
- FabFilter Pro-Q 4: another instance's spectrum in red outline, "Show Collisions" red glow, "merely an indication, and not exact science"; tilt 4.5 dB/oct by default. https://www.fabfilter.com/help/pro-q/using/analyzer ; Instance List and Spectral Dynamics. https://www.soundonsound.com/reviews/fabfilter-pro-q-4?amp
- Sonible smart:EQ 4 groups and front/middle/back layers (algorithm not published). https://www.sonible.com/blog/use-cases-smarteq4/
- MeldaProduction MMultiAnalyzer collision detector across instances. https://meldaproduction.com/MMultiAnalyzer ; Voxengo SPAN Plus spectrum exchange. https://www.voxengo.com/product/spanplus
- Waves Curves Equator learns a sidechain profile. https://www.waves.com/curves-equator-a-deep-dive-into-every-feature-for-perfect-resonance-suppression
- Built in: Studio One spectrum with a second (sidechain) spectrum; Bitwig EQ+ shows a reference track's spectrum; Cubase compares two channels' EQ curves. https://bitwig.com/bitwig-eqs , https://steinberg.help/nuendo/v12/en/cubase_nuendo/topics/mixconsole/mixconsole_comparing_channels_t.html
- "Mixanalog" (mix:analog) is a remote analog hardware service, not a masking tool. https://www.kvraudio.com/news/mixanalog-releases-elysia-nvelope-on-their-platform-47920
- Research: Ronan, Ma, Mc Namara, Gunes and Reiss: masker-to-signal ratio per band from an MPEG psychoacoustic model of the other tracks, normalised by 20 dB; subgrouping reduces masking. https://arxiv.org/pdf/1803.09960 ; Hafezi and Reiss (JAES 2015): objective masking measures can predict perceived masking poorly. https://www.aes.org/e-lib/browse.cfm?elib=17637

### 3.9 How psytrance producers mix kick and bass
- Bonedo workshop: kick on every quarter, three 16th bass notes (KBBB), kick no longer than an 8th; lower the first bass note; phase cancellation between kick tail and bass root; fixes: polarity, a tiny time shift, remove the fundamental from the first note. https://www.bonedo.de/artikel/psytrance-produzieren-workshop-1-kick-bass-percussion/
- Psynews: line the first bass note up with the kick tail; check bounced audio zoomed and nudge the bass by a few ms; velocity patterns instead of sidechain; split the bass at about 200 Hz. https://psynews.org/forums/topic/72935-the-ins-and-outs-of-psytrance-bassline
- Myloops (vendor blog, numbers): kick fundamental 50 to 70 Hz, tail 80 to 150 ms for full-on; bass starts 5 to 15 ms after the kick; volume shaping preferred (hold 30 to 50 ms, recover 60 to 80 ms; a 16th is about 103 ms at 145 BPM); tune until beating is under 1 Hz; mono below about 80 to 120 Hz. https://www.myloops.net/how-to-make-psytrance-kick-and-bass-work-together ; pads and FX high-passed 300 to 500 Hz, reverb returns 400 to 600 Hz, mud zone 150 to 300 Hz. https://www.myloops.net/common-psytrance-production-mistakes
- Keys E, F, F#, G most used (blog level). https://feelyoursound.com/articles/psytrance-basslines/
- Attack Magazine (rolling techno): find the kick's pitch first, leave the first 16th empty. https://www.attackmagazine.com/technique/tutorials/warehouse-rolling-techno-bass/
- Vini Vici and Astrix bass: fundamental replaced by a separate sine for control. https://idmmag.com/tech/tutorials/what-makes-the-vini-vici-and-astrix-bass-so-huge/
- Not verified: a "−6 to −8 LUFS short-term" psytrance figure; no interview with a named psy artist could be loaded (Sonic Academy and KVR pages failed).

### 3.10 Lessons used for the options
1. In psytrance the kick and bass problem is timing, not spectrum: they share 40 to 120 Hz and take turns. Any clash view must count only what sounds at the same moment, or it flags every kick and bass (X16, demonstrated on the page).
2. The useful kick and bass picture is a beat-locked overlay of both waveforms and their sum, with polarity and nudge (X15).
3. Separate the trigger from the shape (X2); offer spectral ducking for the cases where whole-signal ducking takes too much (X3).
4. Compensation must cover every path, and latency must be visible and bounded with a named list of what was skipped (X5, X6, X7).
5. A bounce states its tap point and keeps a way back (X8).
6. Every comparison is loudness-matched by default and never in export (X20, X21, X24).
7. Suggestions the user accepts, never silent automatic processing (X18); label every masking number as an estimate.

## 4. The options

Label: **new**; **improves** a planned card or idea (named); **covered**. Value 1 to 5 for a big psy project. Effort in tasks.

| # | ★ | Option | Label | Value | Effort | Lane |
|---|---|---|---|---|---|---|
| **A. Sidechain and ducking** |
| X1 | ★ | Sidechain from anything: a source menu with tap point on Compressor, Gate, Multiband, OTT, EQ dynamic bands, later VST3 | new (reuses `abxPickSrc`, `abxReach`) | 5 | 2 | MX; badge by I |
| X2 | ★ | Ducking by shape, three triggers (tempo, notes of any track, audio of any track); curve over the bass, ms and 16ths | improves card F16 (FT-F16a/b) | 5 | +0.5 in F16 | C |
| X3 | | Spectral ducking: 32 bands, the bass goes down only where the kick is | new (extends the Ducker's Focus; NI-5b's fix can call it) | 4 | 1–2 | MX |
| X4 | | Keep the reverbs off the kick: one switch per return | new | 4 | 1 | C |
| **B. Delay compensation and latency** |
| X5 | ★ | Compensation for returns, sends and sidechain triggers; latency changes re-aligned (VST3) | new (finishes v0.146; native plan needs it) | 5 | 2 + native | MX; NB |
| X6 | | Latency you can see: per device on hover, per strip, the longest path | new (next to F37) | 3 | 1 | I and C |
| X7 | | Play through: devices over a limit skipped on the monitored track, listed | new (also in the performance research) | 4 | 1 | MX |
| **C. Freeze and bounce** |
| X8 | ★ | Bounce with a tap point (before effects, after effects, after fader, after group, after a device), tail, replace or new, original kept | new (joins Freeze and Bounce) | 4 | 1–2 | C |
| X9 | | Freeze up to here | new | 3 | 1 | C |
| X10 | | Print a group with its share of the returns (stems) | new (hook for lane B's Export page) | 3 | 1 | C, B |
| **D. Routing view** |
| X11 | ★ | Routing map: tracks, groups, master, sends, sidechains, latency per path; re-route by dragging | new | 4 | 2 | C |
| X12 | | Pre or post per send (blue and yellow rings) | new | 4 | 1 | MX |
| X13 | | Output to any group, return or track | new | 3 | 1–2 | MX |
| X14 | | VCA done right: relative, grey line beside the lane, merge | improves card F27 (FT-F27) | 3 | +0 | C |
| **E. Clarity and clashes** |
| X15 | ★ | Kick and bass lock: kick, bass and sum on one axis, overlap, adds or cancels under 90 Hz, polarity, nudge | improves card F18 (FT-F18a/b) and idea I2 | 5 | +1 in F18 | C, analysis D |
| X16 | ★ | Clash meter that knows the beat: per band, how often both are loud at the same moment | improves idea I12 (NI-5a) | 5 | +1 in NI-5 | D |
| X17 | | Band listen on any spectrum | new (near I15's sub-only lens) | 3 | 1 | E, MX |
| X18 | | High-pass hints with one-click cut | new (reads the NI-3 cache) | 4 | 1 | D |
| X19 | | Low end in mono: Bass mono switch, low-band correlation, side warning | improves idea I4 (NI-8) | 4 | 1 | MX, E |
| X20 | | Fair compare: gain-matched bypass on every device | new (I14 covers Mix A/B only) | 4 | 1 | C, I |
| **F. Loudness and references** |
| X21 | ★ | Reference difference line, four band lights, low-end punch needle, loop the loudest 8 bars | improves card F25 (FT-F25b) | 5 | +1 in F25 | C, drawing E |
| X22 | | Your own psytrance target from your references | new (uses F25's slots) | 3 | 1 | C, D |
| X23 | | Gain staging check for the whole mix | improves idea I13 (NI-7) | 3 | 1 | D |
| X24 | | Streaming preview (turn-down per service) | new (next to F26) | 2 | 1 | C |
| X25 | | Loudness along the song | covered by I6 and meter pick L2 (only the target band is new) | 2 | +0 | D |
| **G. Snapshots** |
| X26 | ★ | Mix scenes with partial recall (levels, sends, inserts, selected tracks), one undo step | improves card F29 (FT-F29) | 4 | +0.5 in F29 | C |
| X27 | | Glide between scenes over bars | improves idea I28 (NI-20) | 3 | 1 | C |

The page's live mock-ups: X2 synthesizes a 145 BPM kick and a bass on every 16th and applies the drawn curve (drag hold and recovery, play); X15 computes the overlap of the kick tail (on F1) and the first bass note and whether their sum under 90 Hz adds or cancels (checked headless: from −3.2 dB at −4 ms nudge to +2.1 dB at +4 ms; polarity flip turns +0.6 into −0.7 dB; the short tail leaves a 3.4 ms gap); X16 counts clashes per third-octave band in time (checked: the sum of clash fractions falls from 5.1 with the bass on every 16th to 2.4 with the gap and to 1.1 with the gap and a short tail, while the average overlap at 40 to 80 Hz does not change).

## 5. Proposed tasks (after the picks)

The lane table in CLAUDE.md has no owner for the audio graph itself (`syncGraph`, `busRoute`, `fxLat`, `renderMix`). Several options change it, so this proposes **a new lane MX (mixing engine, prefix `mx`)** for X1, X3, X5, X7, X12, X13 and the filter of X17 and X19, so that lane C (FT, already 40 cards) is not the bottleneck and two lanes do not edit `busRoute` at once. If the scheduling chat prefers, these go to lane C instead. Each task: build, headless test, release through the gate, log entry.

| Task | Options | Lane | Depends on | Check |
|---|---|---|---|---|
| MX-1 | X12 pre/post sends, X13 output to any bus (`busRoute`, `renderMix`, loop check) | MX | — | sends pre and post measured with a test tone; export equals playback within 0.1 dB |
| MX-2 | X5 compensation for returns, sends and triggers; X6's numbers (`pdcMap` per path) | MX (+ I for X6's badge) | MX-1 | impulse through every path arrives on the same sample, live and in export |
| MX-3 | X1 sidechain menu on dynamics devices (a shared `mxScPick` built on `abxPickSrc`) | MX (+ I hook `DV_HOOKS.scBadge`) | MX-1 | Compressor keyed from the kick reduces the bass only on kicks |
| MX-4 | X3 spectral ducking (Ducker focus "Spectral") and X19's Bass mono switch | MX | MX-3 | bass band 40–120 Hz ducked, 300 Hz unchanged within 0.5 dB |
| MX-5 | X7 play-through monitoring | MX | MX-2 | skipped devices listed; playback unchanged |
| NB (native) | X5 for VST3: latency reports and changes | NB | native plan section 6 | as MX-2 with a latent test plug-in |
| FT-F16 (+) | X2 into F16a/b: curve over the bass waveform, ms and 16ths, note trigger first | C | FT-F16a | gain curve matches the drawing to 0.1 dB |
| FT-F18 (+) | X15 into F18a/b: sum trace, polarity, nudge saved on the track | C, D (NI-2a) | NI-2a | adds/cancels reading matches an offline render |
| FT-F25 (+) | X21 difference line, band lights, punch needle; X22 own target | C (drawing E) | FT-F25a | difference of a track against itself is 0 dB |
| FT-F27 (+), FT-F29 (+) | X14 VCA behaviour; X26 scenes with partial recall; X27 glide | C | — | recall undoes in one step; VCA leaves member faders |
| FT-X8 | X8 bounce window with tap points, X9 freeze up to here | C | MX-1 for "after group" | each tap point equals the live signal at that point |
| FT-X10 | X10 group stems with returns | C, hook for B | FT-X8 | stems sum to the mix within 0.1 dB |
| FT-X11 | X11 routing map | C | MX-1 | every link in the project drawn once; loops refused |
| FT-X20 | X20 fair compare, X24 streaming preview, X4 returns ducked under the kick | C (+ I button) | — | matched within 0.5 LU; off in export |
| NI-5 (+) | X16 time-gated clash measure in NI-5a, pair view on a cable click | D | NI-3 | KBBB demo flags less than the plain average |
| NI-x | X18 high-pass hints, X23 gain staging check | D | NI-3, NI-7 | hints only on tracks with energy under the line |
| IN-x | X17 band listen on the analysers, X19's low-band correlation meter | E (+ MX filter) | MX-4 | listened band equals the drawn band |

## 6. Limits

- Facts marked as blogs (Myloops, FeelYourSound) are practitioner rules of thumb. REAPER anticipative FX, Bitwig's monitoring mode and the absence of scenes in Logic, Live, Bitwig and FL were not verified from official pages.
- Pro-Q, Melda and Sonible do not publish their collision algorithms; the page's clash rule is my own estimate and is labelled as such.
- The latency-when-playing pain mostly belongs to the performance research task; X7 is the mixing-side part and should be picked in one place only.

---

## The user's picks (27 November 2026, 21:07 Brussels)

`AE3 picks: X1 X3 X4 X5 X6 X8 X11 X12 X13 X14 X15 X16 X17 X18 X19 X20 X21 X22 X23 X25 X26 X27`

Not picked as written: X2 (ducking by shape: card F16 is built by lane C anyway), X7, X9, X10 and X24. The user's notes change several options:

- **X4 duck under the kick, in the cable menu too.** The Ducker tuned for tails (fast attack, recovery in one 16th, keyed from the kick) is not only a switch on each return: it is one of the choices offered whenever you draw a cable to a sidechain or to a Ducker ("Duck under the kick, tuned for tails").
- **X6 latency you can see: subtle, few places.** First in the track's first device on the left (the channel strip with the main volume), then only where it makes sense (the device's hover and the routing map). Not on every surface.
- **X7 replaced by the user's idea (proposal, waiting for the user's yes):** instead of skipping slow devices on the played track, play the fast part at once and let the slow part come in later, in sync. For the other tracks this is what delay compensation and render ahead already do (they come from the timeline, so they are started early: AE2 L4 and L9). For the played track: the dry part now and the wet part of a parallel device (a send to a reverb, a Mix knob) when it is ready; a device with look-ahead runs a low-latency stand-in while you play and the exact version in playback and export. Answer in the chat: Cubase, Ableton, Logic, Studio One and Pro Tools all have a monitoring mode of this family, but none of them lets the slow part of the played track arrive late on purpose.
- **X8 bounce with a tap point lives in the bounce pop-up** (and the automatic bounce's settings), not in a new window.
- **X9 freeze up to here, as a right-click on the freeze button only**, with a small pop-up.
- **X10 group stems ("extends" in the voice note = stems): an option in Export, kept out of the way** (an Advanced part of the export window). The user is unsure how useful it is.
- **X25 loudness along the song goes into the existing loudness history** (meter pick L2, task IN-L): the target band is added there, no second view.

### Who builds it
A new lane K, task **MX** (mixing engine, prefix `mx`): MX-1 X12 pre/post per send and X13 output to any bus; MX-2 X5 compensation for returns, sends and sidechain triggers with X6's numbers and X6's subtle display; MX-3 X1 sidechain from anything and X4 (switch on returns and the cable menu choice); MX-4 X3 spectral ducking and X19's Bass mono switch; MX-5 the user's play-through idea, only after the user's yes. Lane C (FT): X8 with X9, X10 (Advanced in Export, hook for lane B), X11, X14 into F27, X15 into F18, X20, X21 and X22 into F25, X26 into F29. Lane D (NI): X16 into NI-5, X18, X23, X27 into idea I28. Lane E (IN): X17 band listen, X19's low-band correlation, X25 the target band in the loudness history. Native engine (NB): X5 for VST3.

## The user's answer on the play-through idea (X7, MX-5), 28 November 2026, 00:27 Brussels

**Yes, with these conditions** (the user's words: "Yes, I want to go through it, but it is off by standard, and you have to turn it on in the settings. And make it clear it's a special feature that we have that is unique to our DAW in like a subtle way, or a pop-up or something."):
- **Off by default.** Turned on in Settings (a row through lane B's hooks, on the Audio page, MX_HOOKS.settingsRows or the S4 table shape).
- **Shown as AudioLab's own feature, subtly:** proposed (the user was unsure how; adjust if the user answers otherwise): a small amber tag "Only in AudioLab" beside the Settings row (L2 unit style, no badge colours of its own); the first time it is turned on, one short card (lane F's dialog code, not a blocking pop-up) with a small drawing: the fast part plays at once, the slow devices join later in time, the exact version in playback and export; an entry in the About window's "Under the hood" list. No other pop-ups.
- **The name is still open:** the user asked whether other DAWs do this and for a name; proposals given in chat: "Instant Play" (recommended), "Split monitoring", "Fast lane", "Early sound". Use "Instant Play" as the working name until the user picks.
- **What other DAWs do** (researched 28 Nov): Logic's Low Latency Mode bypasses plug-ins whose latency is over a limit (default 5 ms) on the played track; Cubase's Constrain Delay Compensation turns off latency-causing plug-ins on armed and instrument tracks; Studio One's native low-latency monitoring (the Z button) bypasses latent plug-ins on the monitored track; Ableton's Reduced Latency When Monitoring skips delay compensation on armed tracks. All of them **turn the slow devices off or let them run late**; none found keeps the slow devices and brings their part in later, in sync, with stand-ins for look-ahead devices. So the claim "only in AudioLab" holds as far as this research found; the card should say "a way of playing through slow devices we have not seen in other studios" rather than an absolute claim.
- Build order unchanged: MX-5 after MX-4.

## The user's name for MX-5 (28 November 2026, 14:39 Brussels): Dual Path Latency

The user: "And we're going to call it dual path latency."
- The feature's name in all UI text is **Dual Path Latency** (Settings row, button, menus, tooltip, first-use card, About). Replace the working name "Instant Play" everywhere (one constant). Command ids keep the `mx` prefix.
- The user wants it shown, subtly, as an AudioLab original that the user developed. Until the user picks otherwise, build the recommended marks: **U1** a small grey "AudioLab original" tag with the atom mark next to the name in Settings; **U2** one tooltip and first-use card line: "An AudioLab original. Other DAWs turn slow devices off to cut latency; AudioLab keeps them and brings them back in sync."; **U3** an "AudioLab originals" section on the About card listing Dual Path Latency, designed by Ilja V. Jakovliev. (U4, a small atom next to the name everywhere, is not built unless picked.)
- Still off by default, turned on in Settings.

- **Update 14:40 Brussels:** the user does NOT want the word "original" ("original is more like for food"). The tag wording is being picked again: do not build the text "AudioLab original"; keep the tag text in one constant (working text "AudioLab technology") so the pick is a one-line change.
