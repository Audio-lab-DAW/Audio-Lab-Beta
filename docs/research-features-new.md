# AudioLab Pro: features no DAW has yet (task RF2, 27 November 2026)

Pick page: **AudioLab: ideas no DAW has yet**, https://claude.ai/artifact/Pgjr4Phc29hAkxUpQdFcZm

**Nothing in index.html or desktop/ was changed, no version bump.** This is research, 34 ideas and a pick page with ten live mock-ups. Files: this document, `tools/feature-lab/rf2/` (`ideas.json` is the single source for the ideas; `build.py` builds the page and section 4 of this document from it; `template.html` holds the page and its mock-ups; `check.js` is the headless check, 36 checks pass at desktop and phone width).

The user's words (27 Nov): "Even features that other DAWs don't have, features that other DAWs don't have that could be interesting and make the app maybe more intuitive."

A parallel task, **RF1**, covers features other DAWs already have. Ideas here were left out or flagged when a mainstream DAW already ships them (I15, I28 and I32 sit close to that line and say so).

## 1. Summary

- **34 ideas in eight groups**: understanding the sound (6), arrangement and flow (5), mixing help (5), learning and guidance (5), safety and never losing work (5), performance and live (3), AI that helps without taking over (4), accessibility (1).
- **Six are starred as most valuable**, each with a proposed task (section 5): **I3 "Why is this clipping?"**, **I2 kick and bass tuning lab**, **I1 frequency map of the whole song**, **I12 masking cables in the mixer**, **I24 What-if branch**, **I30 ghost suggestions**. Together they are about 11 tasks.
- **None of the 34 needs the native engine.** All work with today's web engine and offline renders; a few get cheaper later (I1, I3), and haptics in I34 need the native Mac app.
- **Why these six:** they turn things that every DAW only *shows* (a clip light, a spectrum, an A/B) into answers (which track, which note, which band), which is the "smart and sciencey, clear, intuitive" direction. Two of them reuse parts the user already loves: I12 uses the cable system, I24 uses the Time Machine's version tree. I2 targets the psytrance low end directly.
- **What AudioLab already has was checked first** so it is not proposed again: Time Machine with version tree and crash recovery, Capture (notes played without recording), Mix A/B, Mono check, headphone safety ceiling, loudness target, guided tour, settings search, ghost notes, Assistant with tools, stem splitter, audio to MIDI. Several ideas build on these (I14 on Mix A/B, I22 to I25 on the Time Machine, I27 on Capture, I4 on Mono check).
- **One rule for every AI idea**, from three surveys and two studies (section 2.3): the AI proposes, shows and labels; the user accepts piece by piece and can undo. I30 makes that rule into one picture (ghosts) and I33 keeps a record of it.
- Picks line from the page, for example `RF2 picks: I1 I2 I3 I12 I24 I30`.

## 2. Research

Gathered on 27 Nov 2026 with web search and a fetch tool. "Read" means the page was opened and the point taken from it. Anything else is general knowledge and marked **(not verified)**. Lines marked **(speculation)** are my reading, not a finding.

### 2.1 HCI and music-technology research

| Source | What it says | Used for |
|---|---|---|
| Vanka et al., "Adoption of AI Technology in the Music Mixing Workflow", AES 2023 ([pdf](https://arxiv.org/pdf/2304.03407), read) | Amateurs want a one-button result; pro-ams want precision; professionals want control and assistive tools. "Black box" distrust is the main barrier. Proposes selectable modes (full, partial, assistive, none). Stem labelling and auto-mastering were most accepted, automatic effects least. Quoted forum comment: "AI can't meaningfully interpret what your song calls for, its vibe." | I30, I31: assistive by default, a mode switch later |
| Ronchini et al., "AI-Assisted Music Production: A User Study on Text-to-Music Models", 2025 ([pdf](https://arxiv.org/pdf/2509.23364v1), read) | 17 producers. Output misses intent; loops in the wrong tempo or key; no piano-roll editing, no regenerating only a part, no stems. "It was frustrating that I was not able to modify the tracks/ideas given." | I32 (fills from your own clips, in key and tempo, as editable notes) |
| Karpodini et al., "Haptic Feedback to Overcome Barriers for Visually Impaired Users in DAWs", Birmingham City University ([pdf](https://www.open-access.bcu.ac.uk/16223/1/Haptic_Feedback_to_Overcome_Barriers_for_Visually_Impaired_Users_in_Digital_Audio_Workstations_2_.pdf), read in part) | 19 blind or visually impaired users. "The majority of commercially available DAWs are not designed to be compatible with screen readers." Speech feedback is slow and linear; hardware and motor faders help; 7 participants proposed vibration for peak levels (the last two points from the part read through a summary). | I34 |
| Roos and McLean, "Strudel: Live Coding Patterns on the Web", ICLC 2023 ([abstract](https://iclc.toplap.org/2023/catalogue/paper/strudel-live-coding-patterns-on-the-web.html), read) and a technical analysis of Strudel's highlighting ([blog](https://ddrscott.github.io/blog/2026/strudel-live-code-highlighting), read; third-party) | Strudel ports TidalCycles to the browser; each playing event carries the source position of the text that made it, so the editor outlines exactly what is sounding, at about 60 frames a second ("temporal source mapping"). | I11 activity glow |
| Hopkins et al., "MR-DAW: Towards Collaborative DAWs in Mixed Reality", 2026 ([arXiv](https://arxiv.org/html/2601.00326v1), read in part) | Loop tracks driven by a foot pedal over Ableton; "loop duration is determined by the first track recorded". 20 musicians; workload slightly lower, not significant. | Background only: no idea taken |
| NIME 2024, "Opening DAWs to Interactive Music" ([NIME](https://nime.org/proc/nime2024_10/), found, not read) | Title only. | Not used |
| Bret Victor, "Inventing on Principle", 2012 (talk; [transcript](https://jamesclear.com/great-speeches/inventing-on-principle-by-bret-victor), found, not read) | Immediate feedback and scrubbing through time while creating (not verified beyond the well-known talk). | I22, I26 |

### 2.2 Experimental and indie tools

| Tool | What is different | Used for |
|---|---|---|
| **Endlesss** ([undo help](https://endlesss.freshdesk.com/support/solutions/articles/80000570917--how-do-i-undo-things-), [forward-moving](https://endlesss.freshdesk.com/support/solutions/articles/80000480291), [MusicRadar 2019](https://www.musicradar.com/news/tim-exiles-collaborative-music-app-endlesss-is-nearly-ready-and-you-can-help), read) | Every capture becomes a new "rifff" in a jam timeline; undo means "go back in the timeline and keep working from there". Muting a layer and committing makes a copy; nothing is removed. Retrospective looper captures after the moment. | I22, I24, I27 |
| **Emacs undo-tree** ([GNU ELPA](https://elpa.gnu.org/devel/undo-tree.html), read) | Redo never discards a branch; a visualiser jumps to any node; "undo in region" undoes only changes in a selection and records a new branch. | I23, I24 |
| **Bitwig Grid, VCV Rack** (general knowledge; forum threads [found](https://community.vcvrack.com/t/bitwig-3-the-grid/4700)) | Modular patching inside or beside the DAW; Bitwig shows modulation on the knobs (not verified in detail). | I11 |
| **Orca** (Hundred Rabbits; general knowledge, not verified) | A grid where every letter is an operator; the whole program is visible and moving at once. | I11 (see what is moving) |
| **TidalCycles, Strudel, Sonic Pi** | Patterns as text; Strudel's live highlighting above. | I11 |
| **Max/MSP** | Patching with live value display on cables (general knowledge). | I11, I13 |
| **Teenage Engineering OP-1** ([tape mode guide](https://teenage.engineering/guides/op-1/original/tape-mode), found) | Four-track tape metaphor; limits as a creative tool (reviews, not read). | Not used directly; shaped the one-button style of I24 (speculation) |
| **Elektron** (parameter locks and trig conditions; [Elektronauts threads](https://www.elektronauts.com/t/ot-trig-conditions-trc-thread/44828), found) | Per-step parameter locks, conditional and probability trigs, Octatrack scenes with a crossfader. Probability exists in several DAWs now, so it belongs to RF1. | I28 (scenes) |
| **Ableton Note, Koala Sampler, Blocs Wave** (app store pages found; reviews not read) | Phone sketchpads: one screen, resample everything, quick capture. | Not used as ideas; Capture already covers the quick-capture part |
| **Sonic Visualiser** ([reference](https://sonicvisualiser.org/doc/reference/4.1/en), found) | Analysis layers (spectrograms, pitch tracks, annotations) over audio. Analysis app, not a DAW. | I1, I5 prior art |
| **Sonic Charge Synplant** (general knowledge, not verified) | Patches grown and bred like plants. | I8 |
| **XLN Audio XO, Sononym** (general knowledge, not verified) | Samples placed on a similarity map. | I20 |

### 2.3 AI in music software: what musicians like and dislike

| Source | Finding |
|---|---|
| Muse Group survey, April 2026, 1,200 users of Ultimate Guitar, MuseScore, Audacity ([post](https://www.mu.se/posts/muse-group-ai-survey), read) | 70% already use AI. Wanted: cleanup (70%), practice help (68%), transcription (58%). Resisted: lyrics (37%), auto-finishing (32%). **93% prefer more control even if slower; 43% want clear labelling of changes; 39% want undo and compare; 32% would refuse a feature whose changes are unclear.** "AI can be useful, but I want clear control over what it does." |
| Sound On Sound, "AI & Music Tech in 2026", Sam Inglis, about 1,200 creators ([article](https://www.soundonsound.com/music-business/ai-music-tech-2026), read) | About one in five use AI regularly. "Producers are most willing to use AI for tasks they see as technical rather than creative." Two-thirds rate ethical sourcing as very important; only 6% would hide AI use. |
| Sonarworks with Sound On Sound, 1,194 producers, Feb 2026 ([post](https://www.sonarworks.com/blog/research/future-music-production-human-producer-survey-2026), read) | AI accepted for cleanup, noise reduction, stem separation, session organisation; resisted for composing and aesthetic choices. Top worry: loss of originality (77%). "The consensus is that AI can make the process easier, but it should not decide what matters." |
| iZotope Neutron 3 review, Sound On Sound ([review](https://www.soundonsound.com/reviews/izotope-neutron-3-advanced), read) | Mix Assistant moves faders on its own Relay plug-ins; the Masking Meter is "a visual aid" that does not fix clashes; Track Assistant works only with iZotope's plug-ins. |
| Stem tools, generative MIDI, Suno-era generators (general knowledge) | Stem splitting is widely accepted (AudioLab has it). Full-song generators are the part musicians resist most (consistent with the surveys above). Generative MIDI inside DAWs is RF1's field. |

**Rule drawn from this (speculation, but consistent across all five sources):** AI in AudioLab should (1) do technical jobs freely, (2) propose creative changes only as visible, separately acceptable ghosts, (3) label what it made, (4) stay inside the song's own key, tempo and material where it generates, (5) always be undoable as one step.

### 2.4 Accessibility in DAWs

- REAPER with the OSARA extension is the standard for blind producers ([OSARA](https://www.github.com/jcsteh/osara), found; [AFB article](https://afb.org/aw/23/6/17971), found). Logic Pro has VoiceOver support (general knowledge, not verified).
- The BCU study above: speech is slow, hardware helps, vibration for peaks is wanted.
- AudioLab is a single web page with canvas-drawn meters and a glass layer; canvas content is invisible to screen readers unless described (general web knowledge). I34 proposes earcons and a spoken mix summary as a first step; real testing with screen-reader users is needed before more.

### 2.5 Game-UI ideas

- **Undo trees and branches** (Emacs undo-tree; Fortnite's branch explorer for creators, [found](https://dev.epicgames.com/documentation/fortnite/branch-explorer-in-fortnite)) → I23, I24.
- **Time rewind** (Braid, Prince of Persia; general knowledge) → I26 knob memory, I22 scrubbing versions.
- **Replays and time-lapses** (game replays, Endlesss' playable history) → I22, I25.
- **Skill games** (ear-training apps such as SoundGym; general knowledge) → I19.
- Achievements and streaks were considered and left out: they reward use, not music (speculation).

### 2.6 Science and data-viz ideas

- Spectrograms and annotation layers (Sonic Visualiser) → I1, I5.
- DJ software's phrase and energy analysis (rekordbox, Mixed In Key; general knowledge, not verified) → I6, I29.
- Kick-bass tuning today is by ear: tune by octave, move the bass note, nudge the bass "about 1-5ms" ([MusicRadar / Computer Music](https://www.musicradar.com/tuition/tech/how-to-tune-your-kick-and-bass-to-stop-them-from-clashing-639140), read; more at [MusicRadar](https://musicradar.com/tuition/tech/how-to-find-the-perfect-kick-and-bass-combo-639138) and [Armada](https://www.armadamusic.com/university/music-production-articles/how-to-tune-your-kick-drum-for-a-better-mix), found) → I2.
- Phylogenetic trees for variations → I8; star maps for presets → I20. Both fit the Webb and Hubble look of the app (speculation).

### 2.7 Common complaints about DAWs

| Complaint | Where it shows up | Ideas that answer it |
|---|---|---|
| Menu diving, not knowing what a control does | Settings research SR2 (this project), forum threads ([Gearspace](https://gearspace.com/threads/plugin-interfaces-are-too-complex-sometimes.1432842/), found) | I17, I18 |
| Routing and "where is this sound coming from" | KVR threads on Bitwig and Cubase ([example](https://www.kvraudio.com/forum/viewtopic.php?p=8089716), found, not read) | I11, I13 |
| Lost work, fear of breaking a mix | A KVR thread titled "The DAW feature I care about more now is mistake recovery" ([thread](https://www.kvraudio.com/forum/viewtopic.php?p=9273348), found; the fetch failed, so only the title is used) | I22 to I26 |
| Plug-in chaos | Neutron's assistant working only with its own plug-ins (above) | I20 for AudioLab's own presets; plug-in management is RF1's and the native plan's field |
| Mixing fatigue and fooling yourself | General engineering practice (not verified as a survey) | I14, I16 |
| Clipping and low end that "just doesn't work" | Tutorials above | I2, I3, I12 |

## 3. How the ideas were chosen

- New or rare in DAWs: each card's "Prior art" says what was found. "Not found" means the searches for this task did not turn it up, not that it cannot exist.
- Fits the user: psytrance and EDM (low end, 8 and 16-bar phrases, long builds), the science look ("smart and sciencey, clear, intuitive, snappy"), and what AudioLab already has.
- Answers a real complaint (section 2.7) or a research finding (sections 2.1 and 2.3).
- Effort is given in this project's task size (one scheduled run). "Native engine" says whether the idea waits for the C++ engine in docs/native-mac-plan.md.

## 4. The ideas

Generated from `tools/feature-lab/rf2/ideas.json`. ★ = most valuable.

### A. Understanding the sound

Science-look views that tell you what is in the sound, not just draw it.

#### I1. Frequency map of the whole song ★ (live mock-up)

- **What you see:** One wide picture of the full song: time left to right, frequency bottom to top (log, 20 Hz to 20 kHz), each pixel coloured by the track that owns the most energy there. Section names from the arrangement sit along the top. Click any spot: the arrangement jumps there and that track is selected. A switch shows a single track as a glowing layer over the rest.
- **Why it is more intuitive:** Answers "what is happening where" for a whole psytrance track in one look: whether the sub is owned by one track, where the leads and the pads pile up at 2 to 5 kHz, which section is thin. A normal spectrum shows only the present moment and mixes all tracks together.
- **Prior art:** Spectrograms exist everywhere (Sonic Visualiser layers, iZotope RX); iZotope Neutron's masking meter compares two tracks at a time inside a plug-in. A whole-song, per-track ownership map inside the DAW was not found.
- **Risks:** Needs an offline analysis pass of every track (cost grows with track count; do it in a worker, cache per clip). Colours for 30 tracks need grouping by the track colours or by bus.
- **Effort:** 2 tasks (analysis worker and cache; the map view and click-to-jump)
- **Native engine:** No. Works with the web engine's offline render; the native engine later makes the pass faster.

#### I2. Kick and bass tuning lab ★ (live mock-up)

- **What you see:** A note ruler (C0 to C3) with the song key's notes lit. The kick's pitch is drawn as its falling curve over its 300 ms life, with the note it settles on marked. The bass notes of the current bar are bars on the same ruler. Where the kick tail and a bass note sit a semitone or two apart, the gap glows red and the beat rate is shown ("beating at 3.4 Hz"). Buttons: tune the kick to the key root, or shift the bass by an octave. For rolling psytrance bass, a strip shows the gap the bass leaves for each kick.
- **Why it is more intuitive:** Kick-bass clashes are the classic low-end problem in psytrance and EDM. Producers tune kicks by ear with a tuner device and a note chart. Seeing both on one pitch ruler in the song's key turns a guessing job into a reading.
- **Prior art:** Kick plug-ins (for example Sonic Academy Kick) show the kick's pitch envelope; tuners show one note; tutorials teach tuning by ear and nudging the bass 1 to 5 ms (MusicRadar). Nothing found that draws kick and bass on one ruler with the key.
- **Risks:** Pitch tracking of a kick's short tail is not exact under 40 Hz; show it as a range. Psytrance kicks often do not settle on a clean note.
- **Effort:** 2 tasks (pitch track of kick samples and synth kick; the view and the two fixes)
- **Native engine:** No.

#### I3. "Why is this clipping?" explainer ★ (live mock-up)

- **What you see:** Click a red clip light on the master or on any strip. A card opens with the moment it happened (bar and beat) and a short chain: "Kick + Bass add up here: +2.1 dB over 0 dBFS. Biggest share: Bass (58%), Kick (31%). Inter-sample peak: +0.6 dB." Each line has a fix button: lower the bass by 5 dB, turn on the limiter, play the moment again. A small bar chart shows each track's share of the peak.
- **Why it is more intuitive:** Every DAW shows THAT something clipped, none says WHY. Beginners lower the master fader, which fixes nothing upstream. Tracing the peak back to the tracks that made it is exactly the "smart and sciencey" help the app is aiming for.
- **Prior art:** Clip indicators and peak-hold everywhere; loudness meters with history. A causal breakdown by track was not found.
- **Risks:** A peak is a sum of signals with phase, so "share" needs a careful definition (contribution at the peak sample, signed). Needs short per-track ring buffers around each clip event.
- **Effort:** 2 tasks
- **Native engine:** No. The ring buffers are cheaper in the native engine later.

#### I4. Mono-loss map

- **What you see:** Next to the existing Mono check: a band-by-band bar per track showing how much level that track loses when the mix is folded to mono ("Pad: −7 dB at 200 to 800 Hz"). Tracks that cancel each other are joined by a line.
- **Why it is more intuitive:** Mono check tells you the mix sounds worse in mono; it does not tell you which track and which band. Club systems and phones are mono in the low end.
- **Prior art:** Correlation meters and per-band imagers exist as plug-ins (for example in mastering suites). Per-track, per-band loss inside the mixer was not found.
- **Risks:** Needs a mid and side analysis per track; cheap with existing analysers but many tracks add up.
- **Effort:** 1 task
- **Native engine:** No.

#### I5. Harmonic ruler on every spectrum

- **What you see:** Any spectrum view can show a piano strip under it. Peaks are labelled with their note and cents ("A1 −12 c"); peaks outside the song's scale glow amber, resonances that ring longer than a beat glow red.
- **Why it is more intuitive:** Turns a spectrum from a picture into a reading in musical terms: a resonance becomes "that F# rings". Helps tuning, EQ and finding a bad note in a pad.
- **Prior art:** Some analysers show the note under the mouse (for example Voxengo SPAN, not verified). Scale-aware labelling of all peaks was not found.
- **Risks:** Busy at full mix; show only the five strongest peaks.
- **Effort:** 1 task
- **Native engine:** No.

#### I6. Energy arc (live mock-up)

- **What you see:** A thin curve under the arrangement: loudness, density (how many tracks play) and brightness over the song, with the sections marked. A dashed curve can show a reference track's arc or a typical psytrance arc (build, drop, break, second drop).
- **Why it is more intuitive:** You see the shape of the song: whether the drop really lifts, whether the break is long enough, whether the second half sags. DJs read this kind of energy curve; producers rarely get it inside their DAW.
- **Prior art:** DJ software analyses phrases and energy (rekordbox phrase analysis, Mixed In Key energy level). In a DAW arrangement: not found.
- **Risks:** "Energy" is a made-up measure; keep the three ingredients visible so it can be trusted.
- **Effort:** 1 task
- **Native engine:** No.

### B. Arrangement and flow

Shaping a track from start to finish, with the energy visible.

#### I7. Draw the arc

- **What you see:** Draw the energy curve you want with the mouse above the arrangement. The app marks where the song falls short ("bars 97 to 112 sit 4 dB under your line") and offers moves you can try one at a time: a riser, a filter sweep, a drum fill, a layer to add. Nothing is changed until you click.
- **Why it is more intuitive:** Starts from the musical intention (where should it build) instead of from tools. Fits the user's way of working on long psytrance structures.
- **Prior art:** None found. Research on generative arrangement exists, but not this kind of target curve in a DAW.
- **Risks:** Suggestions can feel generic; they must come from your own project (your sounds, your automation). Builds on I6.
- **Effort:** 2 tasks after I6
- **Native engine:** No.

#### I8. Variation family tree

- **What you see:** Right-click a MIDI clip: "Breed variations". Six children appear as a small tree, each a mutation (notes moved, rhythm shifted, octave jumps) at a strength you set. Play them, pick one, breed again from it, or cross two clips. The tree stays with the clip so you can go back to any ancestor.
- **Why it is more intuitive:** Sound design by choosing instead of by programming: you only judge with your ears. Good for acid lines and psytrance bass patterns where small changes matter. The tree looks like a phylogenetic chart, which fits the science look.
- **Prior art:** Sonic Charge Synplant breeds synth patches; genetic-algorithm music research (for example Biles' GenJam). For clips inside a DAW, with a kept tree: not found.
- **Risks:** Random mutations can be boring; mutations must respect the scale lock and the groove.
- **Effort:** 2 tasks
- **Native engine:** No.

#### I9. Transition doctor

- **What you see:** Select the border between two sections. Three or four transitions are prepared and can be played in place: riser plus filter sweep, reverse crash and snare roll, a one-bar cut to silence, a tape stop. Pick one: it is built from AudioLab's own devices on its own track, editable.
- **Why it is more intuitive:** Transitions are where tracks lose momentum, and making them is repetitive. Hearing options in context beats dragging samples around.
- **Prior art:** Sample packs of transitions; some apps offer riser generators. Context-aware options built at the section border: not found.
- **Risks:** Can make every song sound the same; options should use the song's own sounds where possible.
- **Effort:** 2 tasks
- **Native engine:** No.

#### I10. Reference ghost lane

- **What you see:** Drop a finished reference track on a ghost lane above the arrangement. Its sections are found and lined up with yours (drop to drop). While playing, a split meter compares the matching sections: loudness, low end, width.
- **Why it is more intuitive:** Comparing "my drop" with "their drop" at the right moment, without jumping around.
- **Prior art:** Reference plug-ins (for example Mastering The Mix REFERENCE, ADPTR Metric AB) compare level-matched audio, not section by section against your arrangement.
- **Risks:** Section finding in someone else's track is a guess; let the user drag the boundaries.
- **Effort:** 2 tasks
- **Native engine:** No.

#### I11. Activity glow

- **What you see:** While the song plays, whatever is changing the sound right now glows softly: the automation lane, the LFO, the knob being moved by it, the cable from the modulator. Pause and the glow freezes, so you can see what was moving at that moment.
- **Why it is more intuitive:** "Where is that wobble coming from?" is a common hunt in big projects. Strudel lights up the exact piece of code that is playing; this does the same for devices.
- **Prior art:** Strudel's live highlighting of the playing code ("temporal source mapping"); Bitwig shows modulation amounts on knobs. A song-wide glow of everything that is moving: not found.
- **Risks:** Visual noise in busy songs; a filter for "only the selected track" is needed. Glass and frame-rate budget.
- **Effort:** 1 task
- **Native engine:** No.

### C. Mixing help

Tools that show where the problem is and leave the decision to you.

#### I12. Masking cables in the mixer ★ (live mock-up)

- **What you see:** With "Clashes" on, the mixer's cable lane shows a cable between two strips that fight in a band right now, its thickness the size of the overlap, labelled with the band ("Bass vs Kick, 45 to 70 Hz"). Click the cable: options to duck one under the other in that band only, or to carve a little EQ notch.
- **Why it is more intuitive:** Masking is the hardest mix problem to hear. AudioLab's cable system is the part the user loves, so showing clashes as cables reuses a picture the user already reads well.
- **Prior art:** iZotope Neutron's masking meter (one pair, inside a plug-in, "does not fix them automatically", Sound On Sound). Across the whole mixer, with cables: not found.
- **Risks:** Pairwise comparison grows with the square of track count; limit to the 12 loudest tracks or to the selected track. Must not clutter the cable lane: its own colour and a switch.
- **Effort:** 2 tasks
- **Native engine:** No.

#### I13. Level journey (live mock-up)

- **What you see:** For one channel, a vertical strip that follows the signal from the clip through each device to the fader and the bus: level in and out at every step as a small waterfall, with the biggest jumps marked.
- **Why it is more intuitive:** Gain staging is invisible: each device has its own meter, if any. One picture of the whole path shows where the level jumps or drops.
- **Prior art:** Per-plug-in meters; some channel strips show input and output. A whole-path view: not found.
- **Risks:** Needs a tap after every device; cheap with analysers, but only for the selected channel.
- **Effort:** 1 task
- **Native engine:** No.

#### I14. Blind shoot-out

- **What you see:** When you compare two versions (Mix A/B, two EQ settings, two kicks), a "Blind" button hides which is which, level-matches them and plays them in random order. You vote; after five rounds it shows whether you really heard a difference.
- **Why it is more intuitive:** A louder version always sounds better. Blind, level-matched comparison is how engineers stop fooling themselves, and AudioLab already has Mix A/B to build on.
- **Prior art:** ABX test tools for audio formats; level matching in some reference plug-ins. Inside a DAW's own A/B: not found.
- **Risks:** Some users will find it a gimmick; keep it one button.
- **Effort:** 1 task
- **Native engine:** No.

#### I15. Listening lenses

- **What you see:** A row of small lenses on the master: phone speaker, laptop, earbuds, car, club PA (big low end, mono below 120 Hz), and "sub only". One click hears the mix through it.
- **Why it is more intuitive:** Mixes are checked on many systems; walking to the car is slow. Ties in with the DAC and audiophile work in Settings.
- **Prior art:** Plug-ins exist (for example Audified MixChecker, Sonarworks). Built into the master section of a DAW: rare. Close to RF1's field; kept here because the club PA and sub-only lenses are tuned for psytrance.
- **Risks:** Simulations are approximations; label them as such. Must be off for export.
- **Effort:** 1 task
- **Native engine:** No.

#### I16. Ear-fatigue guardian

- **What you see:** A small dose meter near the loudness read-out: how much sound your ears have had in this session (level times time, from the output level and the DAC setting). After a long loud stretch it suggests a break; after a break, "fresh ears" plays your mix and a reference for 20 seconds before you change anything.
- **Why it is more intuitive:** Mixing decisions made with tired ears are the ones you undo the next day. AudioLab already has a headphone safety ceiling; this adds the time dimension.
- **Prior art:** Phone and watch headphone-exposure tracking. In a DAW: not found.
- **Risks:** The real level at the ear is unknown without calibration; show it as an estimate and let the user calibrate once. Not medical advice.
- **Effort:** 1 task
- **Native engine:** No.

### D. Learning and guidance

Learning inside your own project instead of in a video.

#### I17. Explain mode with a live picture

- **What you see:** Hold a key and hover any knob: a small card explains it in one line and shows a live picture of what it does to the sound you are playing (attack reshapes the drawn envelope, the filter cutoff moves on a mini spectrum).
- **Why it is more intuitive:** Learning by seeing the effect on your own sound, not on a textbook example. Ableton's Info View explains in text only.
- **Prior art:** Ableton Info View (text). Live pictures per control: not found.
- **Risks:** Needs a picture type for each kind of control; start with filter, envelope, compressor and delay.
- **Effort:** 2 tasks
- **Native engine:** No.

#### I18. Recipe cards that act on your project

- **What you see:** A card like "Rolling psytrance bass in 6 steps". Each step points at the real control in your project (it glows), says what to listen for, and ticks itself when the change is made. Cards can be written as extension files (docs/extensions-plan.md).
- **Why it is more intuitive:** Tutorials live in videos, away from the work. Here the steps happen in your own song.
- **Prior art:** Ableton's built-in lessons and the Learning Music site (outside your project). Steps that watch your real project: not found.
- **Risks:** Writing good cards takes time; start with four for the user's genres.
- **Effort:** 2 tasks plus content
- **Native engine:** No.

#### I19. Ear training on your own mix

- **What you see:** A two-minute game: AudioLab boosts a band on one of your tracks and you guess the frequency, or it changes a compressor and you guess which one. Score and progress are kept.
- **Why it is more intuitive:** Training on your own sounds transfers better to your own mixing than training on generic loops.
- **Prior art:** Ear-training apps such as SoundGym and TrainYourEars (separate apps with their own audio). Inside a DAW with your audio: not found.
- **Risks:** Fun is hard to design; keep it short and optional.
- **Effort:** 1 task
- **Native engine:** No.

#### I20. Preset galaxy

- **What you see:** All 1,238 presets as a star map: similar sounds sit close together, colour by instrument, brightness by how bright the sound is. Hover to hear, drag a lasso to collect favourites, type "dark pluck" to light up a region.
- **Why it is more intuitive:** Browsing by sound instead of by name. The star map fits the Webb and Hubble look of the app.
- **Prior art:** XLN Audio XO arranges drum samples as a map; Sononym maps samples. For synth presets of a DAW's own instruments: not found.
- **Risks:** Needs one render and analysis per preset (offline, once).
- **Effort:** 2 tasks
- **Native engine:** No.

#### I21. Your mix habits

- **What you see:** Once a month, a private one-page report from your own projects: "You boost 3 to 4 kHz on leads in 80% of songs", "your sub sits 2 dB above your references", "you finish songs in about 9 sessions".
- **Why it is more intuitive:** Habits are invisible from the inside. Seeing your own tendencies is how you improve without a teacher.
- **Prior art:** Not found.
- **Risks:** Can feel like being watched; local only, opt in, easy to delete.
- **Effort:** 1 task
- **Native engine:** No.

### E. Safety and never losing work

Builds on the Time Machine AudioLab already has.

#### I22. Listen through the Time Machine (live mock-up)

- **What you see:** The Time Machine's timeline gets a scrub bar: drag it and hear the same 8 bars as they sounded in each saved version, like a time-lapse of the song growing. Two versions can be put side by side for a quick A/B, and one track can be pulled out of an old version into today's song.
- **Why it is more intuitive:** "It sounded better on Tuesday" can be checked in seconds instead of opening old files. Pulling one track from the past fixes the case where only one part got worse.
- **Prior art:** Endlesss keeps every jam step as a playable rifff ("go back in the timeline and keep working from there"); game replays and Braid-style time rewind. In a DAW's version history: not found.
- **Risks:** Each version needs a short render, cached in the background; storage grows (needs the storage read-out the settings audit asked for).
- **Effort:** 2 tasks
- **Native engine:** No.

#### I23. Undo only here

- **What you see:** Select tracks or a time range, then "Undo here": steps back only the changes that touched that selection and leaves the rest of your later work alone. The undo history list highlights which steps that will be.
- **Why it is more intuitive:** Today, undoing a mistake made an hour ago on the bass also undoes everything done since on the drums.
- **Prior art:** Emacs undo-tree's "undo in region" (records a new branch, never edits history). In a DAW: not found.
- **Risks:** Changes that depend on each other (a moved clip that was later edited) need clear rules; refuse with a reason when a step cannot be separated.
- **Effort:** 2 tasks
- **Native engine:** No.

#### I24. What-if branch ★ (live mock-up)

- **What you see:** A "Try" button in the top bar. Press it and everything from now on happens on a side branch, shown by a coloured outline around the app and a branch name. At any time: Keep (merge into the song), Drop (back to before, nothing lost), or Keep both (the branch becomes a version in the Time Machine). Branches can be compared with Mix A/B.
- **Why it is more intuitive:** Fear of breaking a good mix stops people from experimenting. Making the experiment explicit and free removes that fear. The Time Machine already has a version tree, so branches have a home.
- **Prior art:** Git branches; Emacs undo-tree; Endlesss' forward-only rifffs. In a DAW as one button: not found.
- **Risks:** Merging is only simple if the branch replaces the song (no three-way merge); say so. Audio recorded on a branch needs its files kept until the branch is dropped.
- **Effort:** 2 tasks
- **Native engine:** No.

#### I25. Session diary

- **What you see:** When you open a project, a short card: "Last time (Tuesday, 2 h): you built the second drop, added the Growl lead, left the break unfinished", with an 8-bar sound snapshot of where you stopped. Write a note to your future self on closing.
- **Why it is more intuitive:** Getting back into a song after days away is a real cost. The diary is made from the undo history, so it costs you nothing.
- **Prior art:** Not found in DAWs.
- **Risks:** Summaries from undo steps can be dull; keep them to three lines, optionally written by the Assistant.
- **Effort:** 1 task
- **Native engine:** No.

#### I26. Knob memory (live mock-up)

- **What you see:** Right-click any knob: a small timeline of its last values in this session. Drag along it to scrub the knob back in time while hearing it, then let go to keep that value.
- **Why it is more intuitive:** "It sounded better a minute ago" for a single control, without undoing everything else. Like rewinding time in a game.
- **Prior art:** Braid-style rewind in games. In a DAW: not found.
- **Risks:** Memory per parameter must be small (ring buffer of values, not audio).
- **Effort:** 1 task
- **Native engine:** No.

### F. Performance and live

Keeping the good moments you did not plan to record.

#### I27. Capture knob moves after the fact

- **What you see:** AudioLab's Capture already keeps the notes you played. This keeps knob and fader moves too: after a great filter sweep you did while jamming, press Capture and it becomes automation at the right place.
- **Why it is more intuitive:** The best moves happen when you are not recording.
- **Prior art:** Ableton's Capture MIDI and Endlesss' retrospective looper capture notes and audio; for automation: not found.
- **Risks:** Needs a ring buffer of control changes; cheap.
- **Effort:** 1 task
- **Native engine:** No.

#### I28. Scene morph pad

- **What you see:** Save up to four snapshots of chosen knobs (for example two filter and delay settings). An XY pad morphs smoothly between them, and the path you draw can be recorded as automation.
- **Why it is more intuitive:** One gesture for a big change, useful for live sets and for long psytrance builds.
- **Prior art:** Elektron Octatrack scenes and crossfader; some plug-ins morph presets. As a DAW-wide pad over any knob: rare.
- **Risks:** Close to features in other tools; RF1 may list it too.
- **Effort:** 1 task
- **Native engine:** No.

#### I29. Phrase rings

- **What you see:** In a live or loop view, a ring around the play button fills over the current 8 or 16-bar phrase. Launched clips wait for the next phrase and show a countdown in beats.
- **Why it is more intuitive:** Psytrance and EDM are built in 8 and 16-bar phrases; launching at the phrase keeps a live set clean.
- **Prior art:** Launch quantisation in clip-based DAWs; phrase analysis in DJ software. The phrase ring itself: not found.
- **Risks:** Small; mostly visual.
- **Effort:** 1 task
- **Native engine:** No.

### G. AI that helps without taking over

Suggestions you can see, compare, accept one by one and undo.

#### I30. Ghost suggestions ★ (live mock-up)

- **What you see:** Whatever the Assistant proposes appears as ghosts, never as changes: ghost notes in the piano roll, a ghost automation line, a ghost EQ curve over the real one. Each ghost has a tick and a cross; "Hear it" plays the song with the ghost included. Accepted ghosts are marked as AI-made in the undo history.
- **Why it is more intuitive:** Surveys agree: musicians accept AI for help and reject AI that decides. 93% prefer more control even if slower, 43% want changes labelled, 39% want undo and compare (Muse Group, 2026). Ghosts are control, labels and compare in one picture.
- **Prior art:** Ghost notes from other clips exist in AudioLab and other DAWs; AI tools usually apply their changes directly (Neutron's Mix Assistant moves Relay faders). Every AI change as an acceptable ghost: not found.
- **Risks:** Each kind of change needs its own ghost drawing; start with notes and automation. Plays well with the extensions plan (stage 4 tools).
- **Effort:** 2 tasks
- **Native engine:** No.

#### I31. Ask the mix

- **What you see:** Ask the Assistant a question about the song: "Why does the second drop feel weaker?" It answers with measurements, not opinions ("the second drop is 1.8 dB quieter, 30% narrower, and the lead is missing between bars 161 and 176"), each with a link that jumps there.
- **Why it is more intuitive:** An answer you can check is one you can trust. Uses the same measurements as I1, I3 and I6.
- **Prior art:** Chat assistants in DAWs mostly do actions or general advice. Answers grounded in measurements of your own project: not found.
- **Risks:** Needs a model connection for free questions; without one, a set of fixed questions works offline.
- **Effort:** 2 tasks
- **Native engine:** No.

#### I32. Fill the gap from your own clips

- **What you see:** Select an empty bar or two: the Assistant offers fills made only from material in this song (variations of your own clips, in key and tempo), as ghosts (I30).
- **Why it is more intuitive:** The study of producers using text-to-music tools found wrong tempo and key, no editing and no partial regeneration were the main problems (Ronchini et al., 2025). Working from your own clips avoids all three and the training-data worry.
- **Prior art:** Generative MIDI tools (in other DAWs and plug-ins) use their own models; RF1 covers those. Restricting to the song's own material: rare.
- **Risks:** Variety is limited to what is in the song; that is the point.
- **Effort:** 2 tasks after I30
- **Native engine:** No.

#### I33. AI provenance layer

- **What you see:** A switch that tints everything the AI made or changed (notes, automation, stems, device settings). A read-out "AI share of this song: 6% of notes, 2 stems". One button removes all AI changes, and the export can include a short honest credit line.
- **Why it is more intuitive:** Only 6% of creators would hide AI use, and most want clear labelling (Sound On Sound 2026 survey; Muse Group). Knowing where the AI was keeps authorship clear.
- **Prior art:** Not found in DAWs.
- **Risks:** Every AI tool must tag its changes; easy if done from the start (stage 4 of the extensions plan).
- **Effort:** 1 task
- **Native engine:** No.

### H. Accessibility

Hearing and feeling what the screen shows.

#### I34. Hear and feel the meters

- **What you see:** For anyone who cannot or does not want to look: levels as a soft pitch in one ear, a short earcon when a track clips or the master passes the loudness target, and "Describe the mix" which reads a short summary ("Bass loudest, master −8 LUFS, two tracks clip in the drop"). Haptics on supported trackpads and controllers.
- **Why it is more intuitive:** "The majority of commercially available DAWs are not designed to be compatible with screen readers" (Karpodini et al.). Blind producers rely on REAPER with the OSARA add-on; building it in is rare. Earcons also help sighted users mixing with eyes closed.
- **Prior art:** OSARA for REAPER (screen reader support, peak reports); research on haptic meters (Karpodini et al., BCU). Built into a DAW: rare.
- **Risks:** Needs testing with screen reader users; sighted design guesses go wrong.
- **Effort:** 2 tasks
- **Native engine:** No (haptics on Mac trackpads need the native app).

## 5. Proposed tasks for the starred ideas

Order suggested: smallest and clearest first. All six touch `index.html` only through new code before `askChoice`, with their own name prefix, the way earlier runs did; none touches `desktop/` or the native engine.

| Task | Idea | Builds | Checks |
|---|---|---|---|
| **NF1** | I3 "Why is this clipping?" | Short per-track ring buffers (about 50 ms around each peak) on the master's clip event; contribution of each track at the peak sample (signed, so cancelling tracks show as negative); the clip card from a click on any clip light; three fixes (lower the top contributor by the overshoot plus 0.5 dB, master limiter on, play the moment). | Headless: a project where Kick plus Bass clip at a known bar; card names the bar and both tracks with shares within 2%; the fix removes the clip on re-render. |
| **NF2** | I2 kick and bass tuning lab | Pitch tracking of the kick (YIN or autocorrelation on the tail, reported as a range under 40 Hz); for the synth kick, read the pitch envelope from its parameters; note ruler in the song key (from the piano roll's scale and root); bass notes of the bar under the playhead; beat-rate read-out; "tune kick to root" and "bass octave" fixes. | Synthetic kicks at known end notes are found within 20 cents; clash read-out matches computed beat rates. |
| **NF3** | I1 frequency map, part 1 | Worker that renders each track offline in 24-beat pieces (reuse `renderMixChunked`), computes a 1/6-octave band energy per beat, caches it per clip and invalidates on edits. | Cache hits on second open; analysis of the Fractals demo finishes in the background without audio dropouts. |
| **NF4** | I1 frequency map, part 2 | The map panel (dockable like the analyser), track-owner colouring, single-track layer, sections along the top, click to jump and select. | Clicking a known kick-only spot selects Kick and moves the playhead. |
| **NF5** | I12 masking cables | Band overlap between the 12 loudest tracks (or the selected track against all), 1/3-octave, smoothed over a beat; cables in their own colour in the existing cable lane under a "Clashes" switch; click a cable for band and two fixes (a band-limited ducker using the existing Ducker device, or a 2 dB notch on the EQ). | Two test tones in the same band produce one cable; moving one tone away removes it; fixes are single undo steps. |
| **NF6** | I24 What-if branch | "Try" in the top bar; snapshot into the Time Machine as branch start; outline and branch name; Keep (branch becomes the song), Drop (restore the snapshot), Keep both (branch saved as a version, song restored); recorded audio kept until a branch is dropped. | Each of the three exits restores or keeps exactly the expected project (compare saved JSON); no audio file lost. |
| **NF7** | I30 ghost suggestions | Assistant tools (`add_notes`, automation tools) write to a ghost layer instead of the song; ghost notes and ghost automation drawing; tick, cross, accept all, "Hear it"; accepted items tagged as AI in the undo history (this is also the base for I33). | An Assistant proposal changes nothing until accepted; accept and undo are single steps; the AI tag survives save and load. |

Not starred but cheap and close to the starred ones, for a later round: I6 energy arc (1 task, and I7 builds on it), I13 level journey (1 task), I26 knob memory (1 task), I22 listen through the Time Machine (2 tasks).

## 6. What was not done, and limits

- No app code was changed. The mock-ups on the pick page use made-up example data and simple Web Audio sounds; they show the idea, not the final look (the final look follows docs/glass-engine-plan.md and docs/devices-display-first.md).
- Several prior-art lines rest on general knowledge and are marked "not verified". Forum pages from KVR could not be read (one fetch failed); only titles were used.
- Effort figures are estimates from the size of earlier tasks in this project (docs/backlog-log.md), not measurements.
- RF1 runs in parallel. If RF1 finds that a mainstream DAW ships one of these 34, that idea should move to RF1's list.

## 7. Sources

- [Adoption of AI Technology in the Music Mixing Workflow (Vanka et al., AES 2023)](https://arxiv.org/pdf/2304.03407)
- [AI-Assisted Music Production: A User Study on Text-to-Music Models (Ronchini et al., 2025)](https://arxiv.org/pdf/2509.23364v1)
- [Muse Group AI survey, April 2026](https://www.mu.se/posts/muse-group-ai-survey)
- [Sound On Sound: AI & Music Tech in 2026](https://www.soundonsound.com/music-business/ai-music-tech-2026)
- [Sonarworks: The Future of Music Production Is Human, 2026 survey](https://www.sonarworks.com/blog/research/future-music-production-human-producer-survey-2026)
- [Haptic Feedback to Overcome Barriers for Visually Impaired Users in DAWs (BCU)](https://www.open-access.bcu.ac.uk/16223/1/Haptic_Feedback_to_Overcome_Barriers_for_Visually_Impaired_Users_in_Digital_Audio_Workstations_2_.pdf)
- [OSARA for REAPER](https://www.github.com/jcsteh/osara)
- [Strudel: Live Coding Patterns on the Web (ICLC 2023)](https://iclc.toplap.org/2023/catalogue/paper/strudel-live-coding-patterns-on-the-web.html)
- [Live Code Highlighting: A Technical Deep Dive (Strudel analysis)](https://ddrscott.github.io/blog/2026/strudel-live-code-highlighting)
- [MR-DAW: Collaborative DAWs in Mixed Reality](https://arxiv.org/html/2601.00326v1)
- [Endlesss: how do I undo things](https://endlesss.freshdesk.com/support/solutions/articles/80000570917--how-do-i-undo-things-)
- [Endlesss: the forward moving nature of Endlesss](https://endlesss.freshdesk.com/support/solutions/articles/80000480291)
- [MusicRadar: Tim Exile's Endlesss](https://www.musicradar.com/news/tim-exiles-collaborative-music-app-endlesss-is-nearly-ready-and-you-can-help)
- [GNU ELPA: undo-tree](https://elpa.gnu.org/devel/undo-tree.html)
- [Sound On Sound: iZotope Neutron 3 Advanced](https://www.soundonsound.com/reviews/izotope-neutron-3-advanced)
- [MusicRadar: How to tune your kick and bass to stop them from clashing](https://www.musicradar.com/tuition/tech/how-to-tune-your-kick-and-bass-to-stop-them-from-clashing-639140)
- [Sonic Visualiser reference](https://sonicvisualiser.org/doc/reference/4.1/en)
- [Fortnite branch explorer](https://dev.epicgames.com/documentation/fortnite/branch-explorer-in-fortnite)
- [Teenage Engineering OP-1 tape mode](https://teenage.engineering/guides/op-1/original/tape-mode)
- [Inventing on Principle transcript](https://jamesclear.com/great-speeches/inventing-on-principle-by-bret-victor)
