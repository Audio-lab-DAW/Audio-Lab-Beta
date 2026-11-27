# Features you might be missing (task RF1, 27 November 2026)

The user's words (27 November): "Come back with ... features I am still missing that I might look into."
The user makes EDM, mostly psytrance in the Electric Universe style, on very revealing gear, and already knows Cubase, Bitwig and FL Studio.

**Pick page:** https://claude.ai/artifact/8oyfz7sMBcYEpXmDRHQA68 (title "AudioLab: features you might be missing"). It has 40 numbered cards (F1 to F40) in six groups, nine of them starred. Tick the ones you want; the bar at the bottom gives one line to paste, for example `RF1 picks: F1 F9 F16`.

This was a research and pick-page task only. Nothing in `index.html` or `desktop/` was changed. The inventory script and its output are in `tools/feature-lab/rf1/`.

## 1. What AudioLab has today (v0.228)

Sources: `docs/backlog-log.md` (v0.159 to v0.228), `docs/device-backlog-2026-11-25.md`, `docs/settings-audit.md` (sections 2.11, 3.3, 3.5, 4.8), the About window's "Show all" list (35 rows), `FXDEF` (42 entries) and `PRESETS` (32 instruments). Lists and screenshots came from a headless run: `python3 tools/feature-lab/rf1/inventory.py . tools/feature-lab/rf1/shots` produced `inventory.json` and four screenshots (no page errors).

**Instruments (32).** Saw lead, Square lead, Sub bass, Square bass, Reese bass, Soft pad, Strings, Pluck, Soft keys, Drum kit (16 pads), Acid (303 style with slide and accent), FX (risers, downlifters, impacts), Plant, Percussion (physical model), Sampler (with grains), Grid (modular), Kick designer, Wavetable, Snare, Clap, Hat and Tom designers, Growl, Emit, Vector Grain, Vector FM, Orbit, Sub, Bounce, Psy Bass, Fractal and Venom.

**Effects (39 audio effects plus 3 MIDI effects).**
- Audio effects: Pro EQ (dynamic bands, stereo/mid/side per band), Compressor, Echo delay, Space reverb, Drive, Low-pass filter, Sidechain (trance gate presets), OTT, Timeless delay, Blur, Phaser, Spectrum, Loudness, Limiter, Soft Clipper, Auto Filter, Chorus/Flanger, Bitcrusher, Gate, LFO Shaper, Tuner, Stereo Imager, Multiband Dynamics (mid/side mode), Transient Shaper, De-Esser, Vocoder, Frequency Shifter, Pitch & Formant, Pitch Correction, Convolution Reverb, Resonance Suppressor, Tape Stop/Stutter, Vector Delay, Bounce Delay, Meter, Fractal, Voice and Ducker.
- MIDI effects: Arpeggiator (16-step velocity and transpose editor), MIDI Toolkit (with a global chance setting, humanize and echo) and Bouncy Notes.
- Chord is in `FXDEF` too.

**Arrangement and editing.**
- Sections with names and colours, a song overview and a map.
- Tempo changes with glides and time signature changes.
- Warp markers on transients, warp to beats or tempo only, and quantize of the hits.
- Groove pool, with grooves extracted from clips, plus humanize and a Feel window.
- Clip fades, reverse, normalize, clip gain, split, Shift-drag duplicate, arrow-key nudge and right-drag select.
- Automation per track (Read and Write, and Write mode for any control), and per-clip envelopes with an envelope editor (shapes, LFOs, lanes).
- Groups (tracks play through a bus), return channels, sends, sidechain (Ducker, Sidechain follower), and cables in the mixer.
- Freeze per track plus automatic background freeze, bounce to audio and bounce to a new audio track.
- Undo, and the Time Machine, which shows saved versions on a timeline. Autosave keeps versions.
- Project templates (your own), and MIDI capture ("Capture MIDI now").
- Export: WAV, FLAC or MP3, stems, dither, peak normalize, fixed seed and fast offline render. MIDI export per clip or track.
- Audio import is supported, but **MIDI file import is not** (the file inputs accept only audio and `.audiolab`).

**Piano roll.**
- Nine tools.
- Timing, Length and Shape actions (quantize, humanize, legato, chop, glue, strum and more).
- Snap, scale highlight, scale lock, chord stamp and ghost notes.
- Lanes for velocity, pitch bend and CC.

**Modulation.** A Modulators column on every track (LFO, envelope, sidechain and step modulators), Macros on every track, Vector Map, and MIDI learn on any knob. MIDI learn has no list of its mappings (settings audit 4.8).

**Audio intelligence.**
- Neural stem splitter (HTDemucs v4).
- Audio to MIDI on drop (melody, harmony, chord symbols, drums).
- Voice: note editing like Melodyne, live voice changer and AI voices.

**Measurement.**
- Meter: LUFS, loudness range and true peak to BS.1770-5, with targets for club, psytrance and the streaming services; it also has views for low end, stereo and spectrogram.
- A dockable analyser.
- A reference song on the master lane, from the Map menu. There is one reference, and there is no automatic loudness matching.
- Per channel, Phase invert, Mono and A/B.

**Performance.** Pooled voices, sleeping tracks, background freeze, delay compensation, and a CPU panel showing totals, dropouts, late notes, sleeping and frozen tracks. There is no reading per track.

**Plug-ins.** Not in the web app. The native Mac lab (tasks NM1, NB-N1, NB-N2a, NL1 to NL4) hosts VST3 and AU in a test app, which the user is testing with Pro-Q, Kick 3, Pigments, OTT, Melodyne and others. It is not yet in AudioLab itself.

## 2. Gap table

How to read the table:
- **DAWs** that have the feature (versions as of 27 Nov 2026): Live 12.4, Bitwig 6.1, Cubase 15, Logic Pro 12, FL Studio 2025.2, Fender Studio Pro 8.2 (formerly Studio One 7), REAPER 7, Reason 13/14, Renoise 3.5, Waveform Pro 13/14.
- **Today** is what AudioLab has now: yes, partial or no.
- **Value** is how much the feature is worth for this user (psytrance, Cubase/Bitwig/FL background), from 1 (low) to 5 (high).
- **Effort** is counted in this project's tasks, where one task is one session with build, test, release and log. "Native" means the feature belongs to the native Mac track.
- The **Card** column links a row to its card on the pick page.

### Arrangement and editing
| Feature | DAWs that have it | Today | Value | Effort | Card |
|---|---|---|---|---|---|
| Take lanes and comping, loop recording | Live, Bitwig, Cubase, Logic, Studio Pro, REAPER, Reason, Waveform; FL partly | no | 2 | 2–3 | F7 |
| Warping and time-stretch | all ten | yes (warp markers, beats, tempo only) | – | – | – |
| Quantise and groove templates, extract groove | Live, Cubase, Logic, REAPER, Reason (ReGroove), Waveform; others partly | yes (groove pool, extract) | – | – | – |
| Clip launcher / session view | Live, Bitwig, Logic (Live Loops), Studio Pro, Waveform; FL partly | no | 3 | 4+ | F8 |
| Automation lanes with curve shapes per segment | all ten | partial (lanes; shapes only in the clip envelope editor) | 4 | 1 | F3 |
| Automation clips you can loop, cut and stretch | Bitwig 6 (automation clips, Spread), Live (unlinked clip envelopes), FL (automation clips) | partial (clip envelopes) | 4 | 2 | F4 |
| Linked / alias clips (edit one, all change) | Bitwig 6 (aliases), FL (patterns), Reason partly | no | 5 | 1–2 | **F1** ★ |
| Arranger: move, copy, reorder whole sections | Cubase (Arranger track), Studio Pro (Arranger), Bitwig and Live partly | partial (sections: loop, select, delete) | 4 | 1 | **F2** ★ |
| Arrangement snap and grid menu | all ten | no (step follows zoom; audit 4.8) | 3 | 1 | F5 |
| Crossfades, glue clips into one | all ten | partial (fades, piano-roll glue) | 3 | 1 | F6 |
| Modulators on any parameter | Bitwig, Cubase, REAPER, Reason, Renoise, Waveform; Live, Logic, FL partly | yes (track Modulators) | – | – | – |
| Macro controls | all ten | yes (track Macros) | – | – | – |
| Device racks: parallel chains with macros, saved as presets | Live (racks), Bitwig (chains), FL (Patcher), Reason (Combinator), REAPER (containers) | partial (serial chain plus track macros) | 4 | 2 | F33 |
| Track folders and groups | all ten | yes (groups) | – | – | – |
| VCA faders | Cubase, Logic, Studio Pro, REAPER | no | 2 | 1 | F27 |
| Sends, returns, sidechain | all ten | yes | – | – | – |
| Freeze, bounce in place | all ten (Bitwig bounce only) | yes | – | – | – |

### MIDI
| Feature | DAWs that have it | Today | Value | Effort | Card |
|---|---|---|---|---|---|
| MPE and per-note expressions or slides | Live, Bitwig, Cubase, Logic, FL, Studio Pro, Waveform; REAPER partly; Renoise per-note effect columns | no | 3 | 2–3 | F14 |
| Chord track / progression tool | Cubase, Logic 12, Studio Pro, FL (Chord Progression), Live (Stacks), Waveform 14, Reason (Player) | partial (Chord effect, chord stamp) | 3 | 2 | F12 |
| Global project key that devices follow | Live 12, Bitwig 6, Cubase (Scale Assistant), Logic, Studio Pro | partial (piano-roll scale, per session only) | 4 | 1 | F11 |
| Arpeggiator | all but REAPER (JSFX) | yes | – | – | – |
| Note probability, ratchets, conditions | Live (chance), Bitwig (operators), Logic (step chance), Reason 13.1, Renoise, Waveform partly | partial (one global chance in MIDI Toolkit) | 4 | 1 | F10 |
| Generators: Euclidean, seeded melodies, rhythm transforms | Live 12 (MIDI Generators/Transformations), Bitwig, Cubase 15 (Pattern Editor), FL (Riff Machine) | partial (Bouncy Notes, Bounce) | 3 | 1–2 | F15 |
| Step sequencer clips with accent, slide and per-step level | FL (Channel rack), Logic (Step Sequencer), Bitwig (Note Grid), Reason (Matrix, Redrum), Renoise | partial (Arp steps, Fractal, Acid accent and slide as notes) | 5 | 2 | **F9** ★ |
| MIDI file import | all ten | no (export only) | 4 | 1 | F13 |

### Audio
| Feature | DAWs that have it | Today | Value | Effort | Card |
|---|---|---|---|---|---|
| Pitch correction | Live 12.1, Cubase, Logic, FL, Studio Pro, Reason, Waveform (bundled) | yes (Pitch Correction, Voice) | – | – | – |
| Spectral editing | REAPER; Cubase (SpectraLayers One) and FL (Edison) partly | no | 2 | 3 | F22 |
| Slice audio to pads or sampler | Live, Bitwig 6.1, Cubase, Logic, FL (Slicex), Reason (REX), Renoise, Studio Pro | partial (transients to warp markers; Sampler plays one sample) | 4 | 2 | F23 |
| Multisample zones, round robin | Live, Bitwig 6.1, Logic, FL (DirectWave), Reason (NN-XT), Renoise | partial | 2 | 2 | F24 |
| Stem separation | Live 12.3, Cubase 15, Logic, FL, Studio Pro | yes | – | – | – |

### Mixing and mastering
| Feature | DAWs that have it | Today | Value | Effort | Card |
|---|---|---|---|---|---|
| LUFS, true peak, correlation, spectrum | Cubase, Logic, REAPER 7, FL (Wave Candy), Studio Pro partly; Live has spectrum only | yes (Meter, analyser) | – | – | – |
| Reference tracks: several slots, loudness matched, A/B | none natively (Metric AB, REFERENCE plug-ins) | partial (one reference song, not matched) | 5 | 1–2 | **F25** ★ |
| Export normalised to LUFS and true peak, export presets | Cubase, Studio Pro, REAPER; Logic partly | partial (peak normalize only) | 4 | 1 | F26 |
| Mid/side | all ten | yes (EQ per band, Multiband, Imager) | – | – | – |
| Dither | all ten | yes | – | – | – |
| Mastering page with sequencing and DDP | Studio Pro (Mastering Page); REAPER partly | no | 2 | 3 | F28 |
| Mix snapshots you flip between | Cubase (mixer snapshots), Studio Pro (Scenes), Logic (alternatives) | partial (A/B per channel) | 3 | 1 | F29 |

### Psytrance and EDM tools (from the producer research)
| Feature | Where producers get it | Today | Value | Effort | Card |
|---|---|---|---|---|---|
| Drawable volume shaper, note-triggered, band split | LFOTool, Kickstart 2, ShaperBox Volume; Bitwig curves | partial (LFO Shaper, Sidechain shapes, Ducker) | 5 | 1–2 | **F16** ★ |
| Multi-shaper: filter, pan, width, crush curves per bar | ShaperBox 3 | no | 4 | 2 | F17 |
| Kick and bass lab: pitch of the kick, phase, overlap | Kick 3 (phase lock, pitch snap), Bonedo and Attack tutorials; no DAW has it | partial (Tuner, Meter low end, Phase invert, Sub "Duck to kick") | 5 | 2 | **F18** ★ |
| Step-sequenced FX: stutter, reverse, gate, crush | Effectrix 2, ShaperBox Time, Bitwig and FL devices | partial (Tape Stop / Stutter) | 4 | 2 | F19 |
| Build designer: one control for a 8/16/32-bar riser | used with risers and macros in every DAW; Live clip envelopes, Bitwig automation clips | partial (FX risers, macros) | 5 | 2 | **F20** ★ |
| FX throws (momentary send that writes automation) | Live/Bitwig via racks; mixer automation everywhere | no | 4 | 1 | F21 |
| Genre starter projects (145 BPM full-on, 138 prog, DJ intro) | templates in every DAW | partial (your own templates, Psy demo) | 3 | 1 | F34 |
| Club check: mono, side, small speaker, sub only | Metric AB, REFERENCE 2 | partial (Mono per channel, Meter) | 3 | 1 | in F25 |

### Workflow
| Feature | DAWs that have it | Today | Value | Effort | Card |
|---|---|---|---|---|---|
| Sample browser with folders, tags, favourites, preview in time and key | Live, Bitwig, Cubase (MediaBay), Logic, FL, Studio Pro, Reason 13.1 | no (Import audio, drop) | 5 | 2 | **F31** ★ |
| Project templates | all ten | yes | – | – | – |
| Undo history, versions, autosave | all ten in some form | yes (Undo, Time Machine, autosave) | – | – | – |
| DAWproject import and export | Bitwig, Cubase 15, Studio Pro, Waveform 14 | no | 4 | 2 | F32 |
| Collaboration and cloud | Live (Note, Link Audio), FL Cloud, Cubase (VST Connect); little elsewhere | no | 2 | 4+ | F35 |

### Performance and hardware
| Feature | DAWs that have it | Today | Value | Effort | Card |
|---|---|---|---|---|---|
| Plug-in hosting (VST3, AU) | all ten | partial (native Mac lab, test app 0.4) | 5 | native (underway) | **F36** ★ |
| CPU per track and device | Live (Performance Impact), REAPER, Waveform 13, Studio Pro partly | partial (totals only) | 3 | 1 | F37 |
| Offline render faster than real time | all ten | yes (Fast render) | – | – | – |
| Multicore audio | all ten; REAPER anticipative | partial (particle devices on their own threads) | 3 | 3 / native | F40 |
| MIDI learn with a mappings page | all ten | partial (learn, no list) | 3 | 1 | F38 |
| Controller scripts, Mackie Control / HUI | all ten (FL, Renoise partly) | no | 3 | 2 | F38 |
| Ableton Link, MIDI clock, OSC | Live, Bitwig, Reason, Renoise, REAPER (OSC), Logic (OSC) | no | 2 | 1–2 | F39 |

One card is not a row above: **F30, Phrase markers and DJ check** (8/16/32-bar phrase marks and a check that the intro and outro are mixable) comes from the producer research, not from a DAW feature list. The full numbering is in section 3.

## 3. The 40 cards on the pick page

★ marks the ones of most value for this user: F1, F2, F9, F16, F18, F20, F25, F31 and F36.

**A. Arrangement**
- F1 ★ Linked clips
- F2 ★ Arranger moves
- F3 Automation curve shapes
- F4 Automation clips
- F5 Snap and grid menu
- F6 Crossfades and glue
- F7 Take lanes and comping
- F8 Clip launcher

**B. MIDI and sequencing**
- F9 ★ Step sequencer clips
- F10 Note chance and ratchets
- F11 Project key
- F12 Chord track
- F13 MIDI file import
- F14 Per-note slides and MPE
- F15 Generators

**C. Psytrance sound tools**
- F16 ★ Volume shaper
- F17 Multi-shaper
- F18 ★ Kick and bass lab
- F19 Step FX
- F20 ★ Build designer
- F21 FX throws
- F22 Spectral editing
- F23 Slice to pads
- F24 Multisample zones

**D. Mix and master**
- F25 ★ Reference A/B
- F26 Loudness export and presets
- F27 VCA faders
- F28 Mastering page
- F29 Mix snapshots
- F30 Phrase markers and DJ check

**E. Workflow**
- F31 ★ Sample browser
- F32 DAWproject
- F33 Racks with macros
- F34 Genre starters
- F35 Collaboration

**F. Engine and hardware**
- F36 ★ Plug-ins in AudioLab
- F37 CPU per track
- F38 Controllers and mappings
- F39 Link, clock and OSC
- F40 Multicore engine

## 4. Proposed tasks for the starred features

Each task is one session: build, headless test, release, and a log entry in `docs/backlog-log.md`. They are not scheduled; the user's picks decide.

- **RF-F1 Linked clips.** A clip can be a linked copy, shown with a small chain mark. Editing its notes or envelopes changes every copy. "Make unique" breaks the link. Shift-drag makes a plain copy and Alt-Shift-drag makes a linked copy. It works for MIDI clips first, then audio clip settings. The demo's repeated kick and bass clips become linked. Test: one edit is heard in all copies; undo is one step; the project file stays small.
- **RF-F2 Arranger moves.** Drag a section in the section strip to move it with all its clips, automation, tempo and signature changes. Use Alt to copy, insert empty bars or delete a section and close the gap. One undo step. Test: the demo's Breakdown moved and copied renders bit-identical to the same edit done by hand.
- **RF-F9 Step sequencer clips.**
  - A clip type with 16, 32 or 64 steps over rows: drum pads, or notes of the key.
  - Each step has level, accent, slide, chance and ratchet.
  - A "Roll" preset writes the KBBB pattern for Psy Bass, with the first bass hit lower.
  - Converts to a normal MIDI clip and back.
  - Test: same render as the equivalent notes; slide plays as legato into Acid and Psy Bass.
- **RF-F16 Volume shaper.**
  - A new effect with a drawable curve per 1/4, 1/2 or 1 bar.
  - Triggered by the tempo, by notes of another track (ghost kick), or by audio.
  - Up to three bands, so only the lows duck.
  - Presets from LFOTool and Kickstart practice.
  - Its curve is drawn live behind the waveform.
  - Test: a curve point at 1/16 lands to the sample at 145 BPM, and the result is the same in an export.
- **RF-F18 Kick and bass lab.**
  - A view, or a mode of Meter, on a pair of tracks.
  - It shows the kick fundamental as a note, and the bass key.
  - It shows the overlap of the kick tail and the first bass note in time, the low-band correlation of the two, and a phase-rotation knob on the bass.
  - Its suggestions are "tune kick to E", "shorten tail by 18 ms" and "rotate 40°", each applied with one click.
  - Test: on the Psy demo, the reading matches an offline calculation.
- **RF-F20 Build designer.**
  - Pick a range of 8, 16 or 32 bars, and one "Build" control writes curves.
  - The curves are high-pass up, reverb send up, noise riser, snare roll density and pitch rise, with the bass filter closing.
  - It writes them as normal automation that can be edited afterwards.
  - Shapes: linear, exponential, late, stepped.
  - Test: the written lanes match the chosen shape at every bar line.
- **RF-F25 Reference A/B.**
  - Up to eight references in a panel, each matched in loudness (LUFS) automatically.
  - One key flips between the mix and the reference at the same song position or at its own cue.
  - Spectra are overlaid.
  - Listening modes: mono, side, sub only, small speaker.
  - Test: the loudness match is within 0.2 LU; switching makes no click.
- **RF-F31 Sample browser.**
  - Add folders. The desktop app reads them; the web app uses the folder picker.
  - Search, tags, favourites and colours.
  - Each file is analysed once for tempo, key, length and type (loop, one-shot, kick, vocal).
  - Preview plays in the song's tempo and key.
  - Drag a file to a track or to a pad.
  - Test: 10 000 files indexed without blocking the page; previews start in under 50 ms.
- **RF-F36 Plug-ins in AudioLab.** This continues the native Mac track (NM1 to NL4). Its next steps are hosting the user's tested plug-ins inside AudioLab's tracks, delay compensation, state saved in the project, and offline render. It is already planned in `docs/native-mac-plan.md`; ticking F36 only raises its priority.

## 5. Sources

### DAW feature sets
**Bitwig**
- https://www.bitwig.com/whats-new/
- https://www.bitwig.com/stories/bitwig-studio-6-416/
- https://downloads.bitwig.com/6.1/Release-Notes-6.1.html
- https://www.bitwig.com/userguide/latest/the_unified_modulation_system/
- https://www.bitwig.com/userguide/latest/other_mixing_interfaces/
- https://synthanatomy.com/2026/03/bitwig-studio-6.html
- https://www.musicradar.com/music-tech/daws/bitwig-studio-6-review

**Ableton Live**
- https://www.ableton.com/en/release-notes/live-12/
- https://www.ableton.com/en/blog/live-12-3-is-here/
- https://help.ableton.com/hc/en-us/articles/26963870210076-What-s-new-in-Live-12-4
- https://www.ableton.com/en/blog/live-121-is-out-now/
- https://www.ableton.com/en/live-manual/12/computer-audio-resources-and-strategies/
- https://www.ableton.com/en/live-manual/12/clip-envelopes/

**Cubase**
- https://www.synthtopia.com/content/2025/11/07/steinberg-cubase-15-now-available-heres-whats-new/
- https://www.soundonsound.com/reviews/steinberg-cubase-pro-15
- https://www.soundonsound.com/techniques/cubase-pro-reference-tracks
- https://steinberg.help/nuendo/v10/en/cubase_nuendo/topics/loudness/loudness_normalizing_loudness_on_export_r.html
- https://www.attackmagazine.com/technique/tutorials/cubase-pro-14-modulators-redefining-creative-automation/

**Logic Pro**
- https://www.synthtopia.com/content/2026/01/30/apple-logic-pro-12-mainstage-4-now-available-heres-whats-new/
- https://support.apple.com/en-gb/109503

**FL Studio**
- https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/basics_new_25.htm
- https://www.image-line.com/fl-studio-news/fl-studio-2025-2
- https://image-line.com/support/flstudio_online_manual/html/plugins/Wave%20Candy.htm
- https://www.image-line.com/support/FLHelp/html/plugins/Patcher.htm

**Fender Studio Pro**
- https://soundonsound.com/reviews/fender-studio-pro-8
- https://www.fender.com/newsroom/273556-fender-studio-pro-8-2-expands-mixing-and-creative-production-tools/
- https://fenderstudiopromanual.fender.com/en/Content/Mastering_Topics/Chapter-Mastering.htm
- https://fenderstudiopromanual.fender.com/en/Content/Mixing_Topics/The_Console.htm

**REAPER**
- https://dlx.reaper.fm/userguide/WhatsNewReaper7Summary_r2.pdf

**Reason**
- https://www.reasonstudios.com/news/post/announcing-reason-13-words-from-the-product-manager
- https://www.reasonstudios.com/news/post/announcing-reason-14-words-from-the-product-manager
- https://www.reasonstudios.com/reason/updates/release-notes

**Renoise**
- https://forum.renoise.com/t/renoise-3-5-and-redux-1-4-released/76590
- https://tutorials.renoise.com/wiki/Toc

**Waveform**
- https://www.soundonsound.com/news/tracktion-announce-waveform-pro-13
- https://musicradar.com/reviews/tracktion-waveform-pro-13-review
- https://www.pluginboutique.com/product/3-Studio-Tools/23-DAW/17567-Waveform-Pro-14

### Psytrance and EDM practice
**Kick and bass**
- https://www.bonedo.de/?p=1868976 (kick and bass, phase)
- https://www.elektronauts.com/t/psytrance-kick-bass-parameters/253875
- https://www.attackmagazine.com/?p=85913 (kick tuning)
- https://www.kvraudio.com/news/sonic-academy-releases-kick-3-62006

**Shapers, gates and FX**
- https://blog.faderpro.com/plugins/how-to-use-xfer-records-lfo-tool/
- https://www.musicradar.com/reviews/nicky-romerocableguys-kickstart-2
- https://www.soundonsound.com/reviews/cableguys-shaperbox-3
- https://www.musicradar.com/news/overused-production-technique-trance-gate
- https://www.musicradar.com/news/sugar-bytes-effectrix2

**Arrangement, builds and sound sources**
- https://www.bonedo.de/?p=1899360 (progressive psy, FX, bouncing tails)
- https://soundbridge.io/en/create-a-psytrance-riser
- https://www.musicradar.com/how-to/how-to-create-the-perfect-intro-for-your-club-track
- https://www.musicradar.com/tuition/tech/26-trance-tips-34006
- https://www.musicradar.com/news/producers-guide-roland-tb-303

**Genre**
- https://en.wikipedia.org/wiki/Psychedelic_trance
- https://psytranceguide.com

**Mixing and mastering**
- https://www.musicradar.com/how-to/how-to-break-the-rules-and-work-with-stereo-bass
- https://www.masteringthemix.com/blogs/learn/song-mastering-for-cd-club-play-and-streaming
- https://www.musicradar.com/reviews/adptr-metric-ab

**What to trust in these tables**
- **Old features may be unchecked.** Some cells for long-standing features (comping, freeze, Mackie Control and others) came from the researchers' general knowledge and were not checked against a page in this run. Treat a "yes" there as likely, not confirmed.
- **No sources on Electric Universe's studio.** The sources say nothing about Electric Universe's studio setup. The psytrance cards rest on general full-on practice.
