# Lessons from other DAWs and from big rewrites, for AudioLab's native route (task RN3)

Research task, 27 November 2026. Only this file was written. `index.html`, `desktop/` and `native/` were not touched, and no other task was edited.

Read first: `docs/native-mac-plan.md` (the route), `docs/native-mac-picks.md` (your picks, the reports from your Mac, and the decision to fold RN1 into the engine), `docs/native-mac-build.md` (where the build stands), `docs/research-native-mac.md` (RN1, the technical how-to). `docs/research-native-windows.md` (RN2) did not exist yet when this was written. This document does **not** repeat RN1: there is nothing here on workgroups, lock-free queues, render-ahead or the VST3 call rules. Where a lesson leans on one of those, it points to RN1.

**What this is about:** what went wrong for others when they built, rebuilt or moved an audio app, or any big app, and what that means for AudioLab's route. The route is a native C++ engine under the present interface, native screens later, Mac first then Windows, VST3 then AU, CLAP and VST2.

**How far to trust the sources.** Five research passes, more than 150 links. Each source is marked:
- **(read)**: the page was opened and read.
- **(headline)**: only the search result's title and address were seen. The claim rests on that.
- **(not checked)**: from background knowledge, with no page opened in this task.

The research tools hit their hourly page limit partway through, so many links are "headline". Nothing in quotation marks comes from a page that was not read. Where something is my own judgement, it says so.

---

## 0. The summary: the ten biggest risks, in plain words

1. **The new version can do less than the old one.** Final Cut Pro X (2011) could not open Final Cut 7 projects and had no multicam and no XML. The Sonos app (2024) shipped without alarms and queue editing, and the CEO left. iWork (2013), Maschine 3 and Logic X all dropped features people used. For AudioLab this risk sits in two places:
   - the day the web engine is switched off (end of stage 3);
   - every native screen in stage 4.
   
   *Guard:* nothing is switched off or replaced until a written parity list, built from the feature inventory, is green. Publish what is missing before release, never after.

2. **A project that does not open, or opens wrong.** Live never opens a set saved by a newer Live, even across point releases. A Rekordbox 6 update corrupted a DJ's library of five years of cue points. Affinity's new files do not open in the old apps.

   AudioLab has a sharper version of this:
   - Your open projects, their audio and the Time Machine snapshots live **inside the desktop shell's browser storage**: localStorage `audiolab-projects`, IndexedDB `audiolab-files` and `audiolab-tm`.
   - The file writer stamps `formatVersion: 1`, but a text search finds no code that reads it back.
   - The day the shell changes (a new app identity, or Chromium removed in stage 4), that storage can vanish.

   *Guard:* make sure your projects survive the move. Back them up before any change that touches them, keep a "minimum version that can read this" field in every file, and keep every old loader.

3. **The sound changes without anyone deciding it.** Live 11.1 changed its filters, MP3 encoder and warp modes, with no legacy mode. Studio One 4 had to explain why old songs sounded different.

   AudioLab's bit tests cover single devices. They do not yet cover:
   - the mixer, pan law, sends and the master chain;
   - defaults kept in settings rather than in the project;
   - the difference between the Linux test machine and the M4 (fused multiply-add is one known cause; see mistake B3).

   *Guard:* reference songs rendered and compared on every engine change, on both machines. The algorithm version and the defaults go into each project.

4. **A plug-in takes your work down with it.** Every DAW forum is full of "X crashed my session". Bitwig made "a crash no longer stops playback" its selling point (2.5, 2019). Ardour shows that isolating every plug-in costs too much at small buffers.

   *Guard:* before plug-ins enter the app (stage N4), have an atomic autosave, rotating backups and a start in safe mode after a crash. Then build "run apart" for the plug-ins that crash.

5. **Hosting by the book when real plug-ins don't follow it.** Plug-in makers list host bugs by name: lifecycle calls made twice or in the wrong order, buffer-size surprises, MIDI CC in VST3 (it arrives as parameters). Hosts list plug-in bugs too: `setProcessing` "fails in many plugins".

   *Guard:* your own plug-in list (U3) becomes a corpus. Run it automatically after every host change, and record each failure in the project as a known case.

6. **Changing several things at once, with no way back.** Pro Tools 11 changed to 64-bit and to AAX-only plug-ins in the same release, and every RTAS plug-in stopped. Sonos could not give people the old app back because the server side had changed under it.

   *Guard:* one change you cannot undo per release, the previous build always downloadable, and the web engine kept as a working fallback until the parity list is green.

7. **An engine shaped by the old engine's limits.** Reason ran third-party plug-ins in its rack's 64-frame blocks. CPU use was bad for about 18 months, and the fix "requires reworking much of Reason's code". Live added multicore late, and serial chains still limit it.

   AudioLab's version of this trap is the web engine's 128-frame block and its single thread. RN1 has the technical rules. The lesson here is about order: settle these in N3, before the first device is ported, not after twenty.

8. **The move takes years, and the old side keeps growing.** Audiotool took about 3.5 years from announcing HTML5 to shipping it. Slack's rebuild ran more than two years. Martin Fowler says the bridge code is a real cost but worth it.

   AudioLab adds devices to the web engine almost every week (the design chain, RF1 and RF2). Each one is a new port that stage 3 must catch up with.

   *Guard:* a "port debt" count in `docs/native-mac-build.md`, and a rule that no new device is added without a line on the port list.

9. **Apple changes the ground every year.** Apple Silicon came in November 2020; native support followed in about 10 months (FL Studio), 12 (Studio One), 15 (Live), 16 (Cubase 12) and 28 (Pro Tools). Serato tells its users "don't update yet" almost every autumn.

   AudioLab has no Apple Developer account (pick U1c). It relies on "Open Anyway", which Apple has already made harder once: Sequoia removed the Control-click route (not checked).

   *Guard:* test on each macOS beta from June, publish a short compatibility line each September, and revisit the account question before the first build goes to anyone else.

10. **Trust lost over money, licences and promises.**
    - Waves went subscription-only and reversed it in two days, with an apology.
    - Rekordbox 6 forced subscriptions.
    - Free Cakewalk became paid.
    - Studio One changed its model and then its name.
    - iLok outages stopped studios working.
    - Bitwig has promised collaboration since 2012.

    None of this is code, and all of it costs more trust than bugs.

    *Guard:* decide the price model before the first native build goes public, never let a licence check block opening the app or a project, and do not announce features before they work.

**Already right in AudioLab** (section 4): the strangler route (C then B), bit-for-bit proofs, Mac first, VST2 last, the plug-in scan in a child process, the test app on your Mac from day one, crash recovery with fallback to the web engine, a project file that is plain JSON plus audio, Intel-only plug-ins refused with a reason, and work done in small steps that you can see.

**Proposed:** 13 new tasks or rules, RL1 to RL12 plus RL1b, in section 5. Each says which stage it belongs in. Nothing in other tasks was changed.

---

## 1. The case studies

Each case gives what happened, what broke trust, what saved them, and the lesson for AudioLab. Team sizes are given where a source states them.

### 1.1 Ableton Live

- **History.** Live 1 came on 30 Oct 2001, audio clips only. MIDI came in Live 4 (2004), Max for Live in 2009, and Max was fully built in with Live 10 after Ableton bought Cycling '74 (June 2017). Comping came only in Live 11 (2021), "a long requested feature" ([MusicRadar](https://www.musicradar.com/news/the-history-of-ableton-live-in-10-key-updates), read; [CDM](https://cdm.link/2017/06/exclusive-ableton-acquires-max-maker-cycling-74-inside-the-deal), headline).
- **Multicore came late and stays limited.** Live splits independent paths over up to 64 cores. A serial chain on one track cannot be split, and sends, sidechains and routing force serial work, so the longest path sets the limit ([Ableton help](https://help.ableton.com/hc/en-us/articles/209067649), read). Users wrote "Multicore support needs a big overhaul" for years ([forum](https://forum.ableton.com/viewtopic.php?p=1434035), headline).
- **Projects open only forward.** "Sets created or saved in later versions of Live cannot be opened in earlier versions", and that includes 12.3 to 12.2. Live's guard is to ask you to Save As when it opens an old set ([Ableton help](https://help.ableton.com/hc/en-us/articles/360000841004), read). Threads such as "Live won't open previous projects… INCREDIBLY FRUSTRATING" ([forum](https://forum.ableton.com/viewtopic.php?p=1795144), headline).
- **Sound changes without a legacy mode.** Live 11.1 changed the analog-modelled filters (Sampler, Simpler, Wavetable, Operator, Auto Filter, Echo), the MP3 encoder and the Complex warp modes. Ableton's advice for getting the old sound back: open the old copy in the old Live, freeze and flatten the tracks, then import them ([Ableton help](https://help.ableton.com/hc/en-us/articles/4406754127378-Sound-changes-in-Ableton-devices-in-Live-11), read).
- **Updated Packs overwrote Live 10 content** ([Ableton help](https://help.ableton.com/hc/en-us/articles/360019558479-Updated-Packs-in-Live-11-overwrite-Pack-content-from-Live-10), headline).
- **Apple Silicon:** M1 shipped Nov 2020. Live 11.1 beta came Sept 2021 and the release 1 Feb 2022, about 15 months later ([Ableton blog](https://ableton.com/en/blog/free-live-11-1-update-apple-silicon-support-out-now), read). Max for Live devices with Intel-only externals still fail ([help](https://help.ableton.com/hc/en-us/articles/4417090747026), headline).
- **The embedded scripting is a contract.** Remote scripts are Python. The move from Python 2 to 3 in Live 11 broke third-party scripts (not checked; [release notes](https://www.ableton.com/release-notes/live-11/)).
- **UI freezes** run through Live 10 to 12 in forum threads ([1](https://forum.ableton.com/viewtopic.php?p=1834538), [2](https://forum.ableton.com/viewtopic.php?p=1822065), headline). That the coupling of UI and engine is the cause is my reading, not a source.
- **What saved them:** a workflow nobody else had (Session view, warping), and an ecosystem: Max for Live, Push (2013), Link (2015).
- **Lesson:** decide the project's forward and backward rules on day one. Any extension surface you open becomes a contract. A graph that was not built for parallel work stays serial-limited.

### 1.2 Bitwig Studio

- **History.** Founded in Berlin in 2009 by former Ableton people. Announced in January 2012 as "coming soon", with VST "with crash protection" for 1.0 and network jamming and a "native modular system" for later ([Synthtopia](https://www.synthtopia.com/content/2012/01/12/bitwig-studio/), read). 1.0 shipped on 26 March 2014, about five years after founding ([Wikipedia](https://en.wikipedia.org/wiki/Bitwig_Studio), read). The team was "now at 30 people, and it still feels very lean" in 2024 ([MusicRadar](https://www.musicradar.com/news/10-years-bitwig), read).
- **1.0 was judged against mature DAWs.** Sound On Sound listed what was missing: no AU, no MIDI routing, no time-signature changes, no arrangement fades, VST3 only promised. The reviewer lost sample files when reorganising project folders. Verdict: an "impressive first release from a small startup" ([SOS](https://www.soundonsound.com/reviews/bitwig-studio?amp), read).
- **Crash protection became the trust feature.** In 2.5 (2019) the hosting was reworked: "playback will not be interrupted" when a plug-in crashes, it reloads, and you choose how plug-ins are grouped (within Bitwig, together, by maker, by plug-in, individually) ([MusicRadar](https://musicradar.com/news/with-bitwig-studio-25-plugins-will-no-longer-crash-your-entire-projects), read; [user guide](https://www.bitwig.com/userguide/latest/vst_plug-in_handling_and_options), read). Note that this took five years after 1.0.
- **The Grid was the engine all along.** "Every device you see in Bitwig Studio is already based on this modular environment", and modules are compiled at run time for the CPU ([CDM](https://cdm.link/2019/01/bitwig-studio-3-modular/), read). The 5.2 release rewrote the graphics engine for the GPU: the screens, not the audio ([MusicRadar](https://www.musicradar.com/news/10-years-bitwig), read).
- **The promise that never came.** Collaboration was announced in 2012. The FAQ still says it is "planned for future versions" and that the file format "was designed with collaboration in mind" ([Bitwig](https://bitwig.com/support/technical_support/when-will-the-collaboration-features-become-available-16), read).
- **Focus.** They declined iOS because "the iOS risk might kill us" (MusicRadar, read).
- **Lesson:** build your own devices on the primitives the engine will one day expose. Make plug-in isolation a choice, not a switch. Do not pre-announce. Expect version one to be measured against everyone's basics.

### 1.3 Logic (Notator to Emagic to Apple)

- **Apple bought Emagic on 1 July 2002** ([Apple](https://apple.com/newsroom/2002/07/01Apple-Acquires-Emagic), headline). Logic for Windows ended within months ([The Register](https://www.theregister.co.uk/2002/07/01/apple_drops_emagic_bombshell/), headline). Windows users were stranded overnight.
- **Logic Pro X (July 2013):** a new interface, 64-bit only, and 32-bit plug-ins gone ([Apple Discussions](https://discussions.apple.com/thread/5174334), headline; the third-party bridge "32 Lives", [MusicRadar](https://musicradar.com/news/tech/use-32-bit-plugins-in-logic-pro-x-with-32-lives-583683), headline). The simpler look read as "dumbed down" to some ([Attack](https://attackmagazine.com/reviews/gear-software/apple-logic-pro-x/2), headline).
  - **What limited the damage:** Logic 9 and X installed side by side ([CDM](https://cdm.link/2013/07/logic-pro-tips-x-coexists-peacefully-with-previous-versions-unsolicited-advanced-tools-advice/), headline), and a bug-fix update came within weeks.
- **Old projects age badly in their routing.** Projects carried from Logic 4 to 6 through 7 to 9 can arrive with "unexpected output routings". Apple's fix is to save in 10, then import the tracks (content only, not I/O) into a new project ([Apple support](https://support.apple.com/en-gb/101924), read).
- **Apple Silicon on day one** (10.6, 12 Nov 2020), with Rosetta for the whole app as the escape hatch for Intel-only Audio Units ([9to5Mac](https://9to5mac.com/2020/11/12/logic-pro-10-6-update/), headline; [Apple](https://support.apple.com/102082), headline). Owning the platform made that possible.
- **Lesson:** when you replace the interface, let old and new be installed side by side, with one project format both can read. A cut plug-in format is felt as data loss, so give an escape hatch and a clear report. Routing and device settings are the part of a project that ages worst.

### 1.4 Studio One (KristalLabs, PreSonus, Fender)

- **History.** KristalLabs was founded in Hamburg in 2006 by Matthias Juwan and Wolfgang Kundrus, both from Steinberg. About two thirds of a "small team" came from Steinberg. Juwan's freeware KRISTAL engine was rewritten from scratch as "K2" on a new framework. K2 became Capture (a recording app bundled with PreSonus interfaces), then Studio One 1.0 in 2009 ([Audiofanzine interview](https://en.audiofanzine.com/general-sequencer/presonus/studio-one-2-professional/editorial/articles/interview-with-the-father-of-studio-one.html), read).
- **Their own framework (CCL)** is now public ([CCL](https://cclsoftware.github.io/based-on-ccl), headline).
- **Discipline:** comping was held back from 2.0 because "it wasn't ready". They keep settings few, and admit the split between global and song settings still caused conflicts. They partner (Celemony's Melodyne) instead of building everything (Audiofanzine, read).
- **Apple Silicon** in 5.4, Nov 2021, about a year after M1 ([KVR](https://www.kvraudio.com/news/presonus-updates-studio-one-to-v5-4---native-apple-silicon-support-and-performance-improvements-52805), headline).
- **Sound and preset changes:** a support article on why old songs "sound different in version 4" in Impact XT and SampleOne ([PreSonus](https://support.presonus.com/hc/en-us/articles/360006948331-Why-do-songs-created-in-previous-versions-of-S1-sound-different-in-version-4-for-Impact-XT-as-well-as-SampleOne), headline). Later, "Ampire Legacy Presets" were shipped so old presets still load ([PreSonus](https://support.presonus.com/hc/en-us/articles/31413043275533-Studio-One-Pro-7-Ampire-Legacy-Presets), headline).
- **Trust after the sale:**
  - Fender bought PreSonus (Nov 2021).
  - Version 7 changed the licence model (Oct 2024; [KVR](https://www.kvraudio.com/forum/viewtopic.php?p=8976012), headline).
  - Version 8 renamed the program "Fender Studio Pro" (Jan 2026; [MusicRadar](https://www.musicradar.com/music-tech/presonus-studio-one-pro-is-dead-long-live-fender-studio-pro-fender-launches-music-production-ecosystem-with-rebranded-daw-interfaces-and-new-controller), headline).
  - Users asked "Why did you leave Studio One?"
- **Lesson:**
  - People who had already built a DAW chose to start clean on a framework they owned, and kept it.
  - Hold a feature back until its foundations are ready.
  - Ship something narrow early to get real users.
  - Licence and brand changes cost more than bugs.

### 1.5 Cubase and Nuendo (Steinberg)

- **VST2 to VST3 took more than a decade, and Steinberg had to force it.**
  - VST3 came in 2008. Maintenance of the VST2 SDK stopped in late 2013, and VST2 closed "for good" in October 2018 ([MusicRadar](https://www.musicradar.com/news/steinberg-says-that-vst-2-is-coming-to-an-end-but-what-does-this-mean-for-your-daw-and-plugins), read).
  - In January 2022 Steinberg's own hosts were given "24 months" to drop VST2 ([Gearnews](https://www.gearnews.com/steinberg-discontinues-support-for-vst2-plug-ins), read).
  - Developers resisted partly because VST3 made something users relied on worse: plain MIDI CC ([Steinberg forum](https://forums.steinberg.net/t/vst3-and-midi-cc-pitfall/201879), headline). Live 11 still had trouble with it in 2022 ([JUCE forum](https://forum.juce.com/t/midi-cc-from-vst3-in-ableton-live-11/51107), headline).
- **Dropping 32-bit and the VST Bridge stranded projects.** Threads include "Bring the 32bit bridge back" and a petition ([1](https://forums.steinberg.net/t/bring-the-32bit-bridge-back/107750), [2](https://forums.steinberg.net/t/32bit-plugin-bridge-petition-please-sign/98127?page=3), headline). Dropping ReWire in Cubase 12 broke old Reason setups ([forum](https://forums.steinberg.net/t/using-reason-4-in-cubase-12-now-rewire-has-gone/790812), headline).
- **Licensing:** the USB eLicenser was "creaking at the seams during product launches". It was replaced in 2021–22 by sign-in licences for 3 computers, putting "less emphasis on our anti-piracy measures" ([KVR interview with Ben Timms](https://www.kvraudio.com/interviews/steinbergs-new-licensing-system-an-interview-with-ben-timms-56005), read). When the eLicenser service ended in 2025, users asked whether they were "FORCED to upgrade" ([forum](https://forums.steinberg.net/t/are-we-forced-to-upgrade-elicenser-no-longer-working/1015042), headline).
- **Apple Silicon** in Cubase 12 (2022). The reviewer expected people to stay on Rosetta for a while until plug-ins caught up ([SOS](https://www.soundonsound.com/reviews/steinberg-cubase-pro-12), read).
- **Blocklisting a well-known plug-in:** "Cubase 14 puts Scaler 3.1.2 on a VST Blocklist" ([Scaler forum](https://forum.scalermusic.com/t/cubase-14-pro-puts-scaler-3-1-2-on-a-vst-blocklist/23576), headline). Scaler is on your U3 list.
- **What saved them:** long notice (five years for the SDK, two for the hosts) and an honest explanation for the licensing change.
- **Lesson:** retire things on a schedule announced long ahead. Never make the new path worse at what users rely on. A host's blocklist must be visible and reversible.

### 1.6 Pro Tools (Avid)

- **Pro Tools 11 (2013) changed both architecture and plug-in format.** It went 64-bit and AAX-only, so RTAS, TDM and 32-bit AAX all stopped. At launch:
  - some of Avid's own plug-ins were not ported;
  - Waves, SoundToys and Sonnox were still working on theirs;
  - offline bounce needed an AAX Native version of every plug-in in the session;
  - the new iLok licence manager's problems "were mostly resolved by late July".
  
  Avid bundled a Pro Tools 10 licence (the two could not run at once). The reviewer found the app got "less attention than the engine", but judged the cut necessary ([SOS review](https://www.soundonsound.com/reviews/avid-pro-tools-11), read).
- **The iLok launch in June 2013** failed on a Sunday night, and Pro Tools would not start. PACE said it "could have done a better job communicating"; some problems lasted over a month ([SonicScoop](https://sonicscoop.com/?p=42974), read). There were later iLok Cloud outages in 2019 and 2023 ([Production Expert](https://www.pro-tools-expert.com/production-expert-1/ilok-servers-down-for-planned-maintenance-today-march-25th-2023), headline). Cubase 12 stuck at the plug-in scan while the iLok site was down ([forum](https://forums.steinberg.net/t/ilok-website-down-cubase-12-wont-proceed-past-scanning-plugins/915779), headline).
- **Apple Silicon:** a public beta in 2022.12 still started under Rosetta by default. Avid's own AIR plug-ins were not native, and several control surfaces were missing. Full support came in 2023.3, about 28 months after M1 ([Avid](https://www.avid.com/resource-center/pro-tools-apple-silicon-public-beta), read).
- **Subscription only from April 2022** for new licences ([Engadget](https://www.engadget.com/pro-tools-subscription-service-perpetual-license-160010247.html?src=rss), read).
- **What saved them:** the previous version shipped with the new one, the native mode was opt-in, and post-production had no alternative.
- **Lesson:** never change the architecture and the plug-in format in one release. Port your own devices before calling the native build ready. Opt-in first, with the old path as the default.

### 1.7 REAPER (Cockos)

- **Team and model.** Released in 2005 by Justin Frankel (Winamp). The team is "two people, without a marketing team". A few hundred users test development builds almost daily, with no closed list. "We're always keeping the installer size in mind" ([MusicRadar](https://www.musicradar.com/music-tech/daws/i-used-to-think-that-reaper-was-a-joke-if-i-saw-someone-using-it-i-would-assume-theyre-not-serious-how-reaper-is-taking-over-the-production-world-one-enthusiastic-user-at-a-time), read).
  - On QA at big firms, Frankel: "anyone who thinks QA is even north of 50 percent effective is delusional".
  - On releases: "We don't ever need to push out new releases in order to increase revenue."
  - His caution about control comes from his first company, which he "lost control of and sold" ([Tape Op](https://tapeop.com/interviews/80/justin-frankel-and-christophe-thibault), read).
- **Plug-in model:** any plug-in can run "as dedicated process", per plug-in ([reaper.blog](https://reaper.blog/2012/02/run-plugin-as-dedicated-process/), headline). Its own plug-in language (JSFX) is open. Projects are plain text (`.rpp`) with `.rpp-bak` and timed backups ([Cockos wiki](https://www.cockos.com/wiki/index.php/Preferences_Project), headline).
- **Licence on the honour system** ([REAPER](https://reaper.FM/purchase.php), headline).
- **No significant trust break found.**
- **Lesson:** this is the nearest model to AudioLab's team. It runs on a public daily beta, small builds, per-plug-in isolation as a choice, plain-text projects with backups, and honest licensing.

### 1.8 Cakewalk and SONAR

- **History.** Gibson ended development in November 2017 after about 30 years, keeping only the licence and forum servers. BandLab bought the IP in February 2018 and hired back the CTO, Noel Borthwick. "Cakewalk by BandLab" shipped free on 4 April 2018; its first releases were only bug fixes, and new features came from the fourth release ([Wikipedia](https://en.wikipedia.org/wiki/Cakewalk_by_BandLab), read).
- **The free product ended.** In June 2023 BandLab announced that the free product would end and Sonar would return as a paid product. No prices were given; the promise was that old projects would open ([MusicRadar](https://www.musicradar.com/news/free-cakewalk-daw-discontinued), read). Later Cakewalk was available only through a BandLab membership ([BandLab](https://bandlabtechnologies.com/news/cakewalk-software-exclusively-available-bandlab-membership/), headline).
- **The question users asked:** "What happened to the old SONAR? What happens to everything I paid for?" ([Cakewalk help](https://help.cakewalk.com/hc/en-us/articles/360021858293-What-happened-to-the-old-SONAR-What-happens-to-everything-I-paid-for), headline).
- **Lesson:** the promise that survives owners and business models is "every project you ever saved opens". Free-then-paid reads as bait and switch.

### 1.9 Reason (Propellerhead, Reason Studios)

- **The rack stayed closed for about 17 years, then plug-ins were added badly.** VST came in Reason 9.5 (2017), with no MIDI routing ([SOS](https://www.soundonsound.com/techniques/vst-support-reason), read). Plug-ins ran in the rack's 64-frame blocks and used far more CPU than in other DAWs. The fix "requires reworking much of Reason's code", and CDM wrote that when 10.3 shipped it would give "performance on par with other DAWs" ([CDM](https://cdm.link/2018/12/reason-10-3-vst/), read). Users asked whether Reason was "completely unusable since VST support" ([KVR](https://www.kvraudio.com/forum/viewtopic.php?p=7343677), headline).
- **What saved them:** they admitted the cause and did the rework. The rack became a plug-in for other DAWs (Reason 11, 2019), and they offered a cheap subscription ([Synthtopia](https://www.synthtopia.com/content/2019/08/26/propellerhead-becomes-reason-studios-announces-reason-11-as-plugin/), headline). ReWire was ended in favour of the Rack Plugin ([Reason Studios](https://help.reasonstudios.com/hc/en-us/sections/360000648153-ReWire-discontinued), headline).
- **Lesson:** an engine tuned for its own devices does not automatically suit third-party plug-ins. AudioLab's own devices were built for 128-frame web blocks. Measure plug-in CPU against another DAW on the same Mac before saying plug-ins are supported.

### 1.10 FL Studio (Image-Line)

- **Ported instead of rewritten.**
  - Over 2.5 million lines of Delphi plus 300 assembler DSP functions, about 15 developers.
  - Delphi was kept because small changes rebuilt in seconds against about 1.5 minutes in C++.
  - Delphi's macOS and 64-bit compilers made the Mac port possible, with the aim of running "natively on both Windows and OS X without customers having to jump through hoops" ([Embarcadero case study](https://www.embarcadero.com/case-study/image-line-software-case-study), read).
  - FL Studio 20 (May 2018) shipped native on both, about two decades after FL first came out ([Synthtopia](https://www.synthtopia.com/content/2018/05/22/fl-studio-20-now-available-for-mac-native-windows/), headline).
- **Apple Silicon** in 20.8.4, Sept 2021 ([CDM](https://cdm.link/2021/09/fl-studio-20-8-4-apple-silicon-frequency-shifter-video-scrubbing-3x-oscillators/), headline).
- **"Lifetime free updates"**, kept for 28 years, with old versions still downloadable ([Image-Line](https://www.image-line.com/lifetime-free-updates), read).
- **Lesson:** porting proven code beats rewriting it, and AudioLab's statement-by-statement port of the worklets is that instinct. A promise kept for decades is worth more than any feature.

### 1.11 Tracktion, Waveform and JUCE

- **History.** Julian Storer wrote Tracktion around 2001 and drew JUCE out of it. Mackie took Tracktion over around 2003, and he stopped working on it by 2005. In 2011 he and James Woodburn took it back. The company is "100% customer funded with low overheads" ([MusicRadar](https://musicradar.com/news/tech/meet-the-programmers-tracktion-software-corporation-624725), read).
- **Tracktion Engine** became open source (GPLv3 plus paid tiers) in Nov 2018: the engine as a reusable product ([CDM](https://cdm.link/the-guts-of-tracktion-are-now-open-source-for-devs-to-make-new-stuff/), read).
- **JUCE's terms changed twice.** PACE bought JUCE in April 2020 ([MusicRadar](https://musicradar.com/news/ilok-developer-pace-acquires-the-juce-development-framework-from-roli), headline). The JUCE 8 licence (May 2024) lowered the Indie cap and added a "Products that create Products" clause, then was amended after more than 400 forum posts ([JUCE forum](https://forum.juce.com/t/amendments-to-the-juce-end-user-licence-agreement-for-juce-8/61265), read).
- **"Why You Shouldn't Write a DAW"** (Dave Rowland, Tracktion, ADC 2023). The forum summary: the engine is the hard part, so reuse one ([KVR thread](https://www.kvraudio.com/forum/viewtopic.php?p=8951463), read; [talk page](https://classcentral.com/course/youtube-why-you-shouldn-t-write-a-daw-david-rowland-adc23-320016), headline).
- **Lesson:**
  - Whoever owns your foundation sets your terms. AudioLab picked R3a (own code, JUCE as the fallback), and that keeps it free of this risk.
  - Rowland's talk is a reason to keep the fallback real: write down the point at which you would switch, rather than drift past it.
  - The licence ground has moved in AudioLab's favour. The VST3 SDK went MIT on 29 Oct 2025, and ASIO became GPLv3 or a proprietary agreement ([Libre Arts](https://librearts.org/2025/11/steinberg-relicenses-vst3-and-asio/), read).

### 1.12 Ardour and Mixbus

- **Plug-ins run in-process on purpose.** Ardour's figures: about 30 µs per process switch × 256 to 768 switches per block for 128 tracks and about 384 plug-ins comes to roughly 7.7 to 23 ms of switching, against a 1.3 ms block (64 frames at 48 kHz). Their advice for a crashing plug-in: don't use it, or use another host ([Ardour](https://ardour.org/plugins-in-process.html), read).
- **Money.** In 2018: more than 3,000 subscribers, about US$8.5k a month, income for 2017 US$130,565. Harrison's Mixbus, built on Ardour, pays a developer and feeds back into the core ([Ardour forum](https://discourse.ardour.org/t/ardour-and-money-early-2018-edition/78585), read).
- **Lesson:** users experience a plug-in crash as a DAW crash, whatever the engineering says. So the guard against lost work (autosave, recovery) must come before the isolation question.

### 1.13 Renoise

- **A small team that plans "only a few steps at a time".** They built Redux as a smaller, manageable product and let the community extend the program with scripts ([MusicRadar](https://www.musicradar.com/news/tech/meet-the-programmers-renoise-604106), read).
- **Lesson:** narrow scope, stable formats, and an extension surface that lets users build what the team can't.

### 1.14 Audiotool, openDAW and BandLab (web DAWs)

- **Audiotool rebuilt three times** ([Wikipedia](https://en.wikipedia.org/wiki/Audiotool), read):
  - Flash, 2010.
  - HTML5: announced Feb 2015, shipped Oct 2018, about 3.5 years. Flash had been the whole platform, and Flash died.
  - Rust: a beta in Jan 2026.
- **Its founder now builds openDAW** in the browser, funded by Patreon ([Gearnews](https://www.gearnews.com/opendaw-studio), read).
- **BandLab** passed 100 million users ([MBW](https://musicbusinessworldwide.com/music-making-app-bandlab-surpasses-100-million-users), headline).
- **Lesson:** a platform move takes years even for a team that knows its app. AudioLab's way, moving piece by piece while the app keeps working, is the better of the two.

### 1.15 Native Instruments and iZotope

- **Rewrites that dropped things.** Maschine 3 users: "These options do not exist on maschine 3" ([NI community](https://community.native-instruments.com/discussion/39115/why-did-ni-remove-great-features), read). Maschine 2.0 (2013) was a big rework too; which features it removed could not be confirmed.
- **The installer blocked paid users.** Native Access 2 (2022) needed a pinned "Known Issues" thread and many "cannot be installed" threads ([NI](https://community.native-instruments.com/discussion/comment/23842), headline). After the account merge, iZotope users asked "Did you guys mess up iZotope logins?" ([NI](https://community.native-instruments.com/discussion/16311/did-you-guys-mess-up-izotope-logins), headline).
- **A slow Apple Silicon move:**
  - the compatibility thread ran for years;
  - Native Access itself still ran under Rosetta late on ([NI](https://community.native-instruments.com/discussion/comment/216925), headline);
  - users asked "Why can't NI keep up with Apple updates?" ([NI](https://community.native-instruments.com/discussion/comment/187598), headline).
- **The company:**
  - preliminary insolvency in January 2026 ([Bedroom Producers Blog](https://bedroomproducersblog.com/2026/01/28/native-instruments-insolvency/), read);
  - bought by inMusic in May 2026, with iZotope, Plugin Alliance and Brainworx ([MBW](https://www.musicbusinessworldwide.com/native-instruments-acquired-by-inmusic-owner-of-akai-and-moog-three-months-after-entering-insolvency/), headline).
  
  Kontakt, Ozone and Neutron are on your U3 list. Their makers' future is less certain than it was a year ago, so AudioLab must never depend on one maker's plug-in to open a project.
- **What saved them:** Kontakt is the library standard, and products kept working through the insolvency.
- **Lesson:** never ship a rewrite that silently drops features. Licensing and installers must let paid users work when the server or the login breaks.

### 1.16 Serato and Rekordbox

- **Rekordbox 6 (April 2020)** moved to subscriptions; old licences did not carry over unless you owned unlocking hardware ([CDM](https://cdm.link/rekordbox-6-sync-cloud-more/), read).
- **Library damage on update.** A DJ wrote that 6.04 "possibly corrupted my library", putting five to six years of cue points at risk; restoring the old version from Time Machine did not fix it ([Pioneer forum](https://forums.pioneerdj.com/hc/fr/community/posts/900001469586-Rekordbox-6-04-possibly-corrupted-my-library-and-other-glitches), read).
- **Lock-in.** Rekordbox 6 stopped exporting XML, so people could not take their collection to another program ([Engine DJ forum](https://community.enginedj.com/t/no-more-xml-export-in-rekordbox-6-blocks-denon-prime-users-to-access-their-rekordbox-collection/21170), headline).
- **Serato** warns "don't upgrade to macOS … yet" nearly every year: Sierra, Mojave, Big Sur ([Serato](https://serato.com/latest/blog/20136/dont-upgrade-to-macos-sierra-yet), [DJ TechTools](https://djtechtools.com/2018/09/11/macos-mojave-out-soon-serato-warns-users-to-avoid-updating-for-now/), headline).
- **Lesson:** the user's library is sacred. Back it up automatically before any migration, keep a way back, and keep an open export. A clear "wait" notice every autumn builds trust.

### 1.17 Waves

- **Subscription-only, reversed in two days.** On 27 March 2023 Waves ended perpetual licences in favour of subscriptions. On 29 March it reversed, with co-founder Meir Shashoua writing: "We are genuinely sorry for the distress it has caused" ([MusicTech](https://www.musictech.com/news/industry/waves-subscription-only-u-turn-licenses/), read).
- **Lesson:** people who bought for keeps react hard to forced change. If you get it wrong, reverse within days and say sorry in plain words.

### 1.18 Netscape and Joel Spolsky

- **The essay.** "Things You Should Never Do, Part I" (6 April 2000): Netscape threw away working code. Version 6 came almost three years after 4, and they lost the market. The odd details in old code "are bug fixes" ([Joel on Software](https://joelonsoftware.com/2000/04/06/things-you-should-never-do-part-i), read).
- **Lesson:** `index.html` is 5.8 MB of fixes for real cases, such as how the Gryphon reports its rate after a plug-in, or what a Bluetooth speaker does. The bit-for-bit rule is how a port keeps those fixes instead of rediscovering them.

### 1.19 The strangler fig (Martin Fowler)

- **Why like-for-like replacement fails.** It "usually fails": replacements take long, users can't wait for features, existing behaviour is hard to specify, and much of it isn't wanted ([Fowler](https://www.martinfowler.com/bliki/StranglerFigApplication.html), read).
- **What works instead.** Small pieces built alongside the old system give value early. The temporary bridge code looks like waste, but "the reduced risk and earlier value from the gradual approach outweigh its costs" (same page, read).
- **Lesson:** count the bridge (N2's socket, the page's clock device, the ring) as planned work with a planned removal date.

### 1.20 Basecamp (37signals)

- **Old versions kept running.** Ta-da List was retired in 2012 but kept running for its users "until the end of the internet". DHH did not want to be a "digital landlord that evicts people" ([Signal v. Noise](https://signalvnoise.com/posts/3830-ta-da-list-until-the-end-of-the-internet), read). Basecamp 3 was a new code base sold next to the old ones, which kept working ([post](https://signalvnoise.com/posts/3959-rewrite-why-basecamp-3-is-a-brand-new-code), headline).
- **Lesson:** a full rewrite is acceptable when nobody is forced off the old one.

### 1.21 Sketch and Figma

- **Sketch** stayed native-Mac-only. In 2021 it added a web app for viewing, comments and handoff, and real-time collaboration, years after Figma ([Sketch blog](https://www.sketch.com/blog/sketch-in-2021-and-beyond/), read). That this is why Figma won is my reading.
- **Figma** runs a C++ core compiled to WebAssembly under a web shell. Moving from asm.js to WebAssembly cut load time "more than 3x" ([Figma](https://www.figma.com/blog/webassembly-cut-figmas-load-time-by-3x/), read).
- **Figma's WebGPU move took about a year** ([Figma](https://www.figma.com/blog/figma-rendering-powered-by-webgpu/), read). How they did it:
  - they first cleaned the old interface so a new backend couldn't regress;
  - they converted shaders automatically rather than keeping two copies;
  - they built the same C++ natively for tests;
  - they rolled out by percentage, broken down by GPU and system;
  - they added a **fallback in the middle of a session** when the new path failed, and blocklisted devices that fell back often.
- **Lesson:**
  - This is the nearest model to AudioLab's stages 1 to 3: a native-quality core under a web interface.
  - Copy the in-session fallback and the per-machine record; the N2b "gave-up" path already starts this.
  - Do not lose what the web gives. A C++ engine can also be compiled to WebAssembly later, so a web build of AudioLab stays possible.

### 1.22 Affinity (Serif, Canva)

- **History.** Built from scratch to replace PagePlus and DrawPlus. Designer 1.0 came Oct 2014 (Mac) and Nov 2016 (Windows); V2 in Nov 2022 ([Wikipedia](https://en.wikipedia.org/wiki/Affinity_Designer), read).
- **2025: one app under Canva.** On 30–31 Oct 2025 the three apps became one free "Affinity" app under Canva. It opens old files, but its files are "not backward-compatible" with the old apps, and the old apps get no more updates. Users worried about accounts, how long free will last, and file support ([TidBITS](https://tidbits.com/2025/10/31/canvas-affinity-combines-photo-designer-and-publisher-into-one-free-app/), read).
- **Lesson:** every new file format breaks trust in the old one. Keep the old loader for ever, and give a way to save for the previous version.

### 1.23 VS Code (stayed on Electron)

- **The sandbox took about three years** (2020 to 2023) while monthly releases continued: "flying an airplane that is being fundamentally rebuilt while it is in the air" ([VS Code blog](https://code.visualstudio.com/blogs/2022/11/28/vscode-sandbox), read). How they did it:
  - the sandbox was a setting, on for Insiders first;
  - **the build failed** when code broke the layer rule;
  - the extension host moved to its own process, with direct ports so the main process stays free for input.
- **Lesson:** a written layer rule checked by the build is cheap and stops drift. That matters most when many AI sessions work in parallel, as in this project.

### 1.24 Slack (2019): "When a rewrite isn't"

- **The new client grew inside the old one.** It was built in a "modern" folder of the same code base, with a two-way bridge to the old code. Pieces shipped as they were done (the emoji picker first, then the sidebar, then messages). The new-only build ran internally for about a year before the July 2019 rollout, and the whole project took more than two years. "Had we waited until the entirety of Slack was rewritten… our users would have had a worse day-to-day experience" ([Slack Engineering](https://slack.engineering/rebuilding-slack-on-the-desktop/), read).
- **Lesson:** this is the closest precedent for stage 4, where native screens replace web ones window by window. Run a new-only build in private long before it is the default.

### 1.25 1Password 8 (native to Electron, 2021)

- **They went from native apps to Electron with a shared Rust core.** A SwiftUI Mac app was tried and stopped as a "painful decision" when it fell behind schedule ([1Password](https://1password.com/blog/1password-8-the-story-so-far), read). Jason Snell: "A long-running and beloved Mac app is getting thrown in the trash and replaced with a web app" ([Six Colors](https://sixcolors.com/post/2021/08/not-important-enough-1password-abandons-its-native-mac-app/), read).
- **Lesson:** Mac users punish what feels non-native. AudioLab will be a web interface in Electron for a long time (pick R6a), so the interim interface must feel right on a Mac: menus, shortcuts, file dialogs, sounds, text. Your pick U4f (native look and feel at 240 Hz) says the same.

### 1.26 Linear

- **Speed comes from the architecture.** A local copy of all the data, and an interface that never waits for the network ([Linear](https://linear.app/blog/scaling-the-linear-sync-engine), read, though the page is only an outline; details not checked).
- **Lesson:** an interface feels fast because of its architecture, not its toolkit. Before rewriting a screen natively, check the cheaper fix: no heavy work on the screen's thread.

### 1.27 Discord (news from November 2026)

- **"Phoenix".** Discord announced a rewrite of its desktop and mobile apps in Rust: GPUI on the desktop instead of Electron, native views over a shared core on mobile, WebAssembly in the browser. The early figures are its own: about 290 MB of memory against several GB, and a near-instant start. It has not shipped yet ([InfoQ](https://infoq.com/news/2026/11/discord-rust-rewrite-gpui-zed), read).
- **Lesson:** the order is the same as AudioLab's: shared native core first, screens per platform after. It is a live experiment to watch, not a proof.

### 1.28 Final Cut Pro X (2011)

- **The launch.** FCP X shipped at $299.99 and Final Cut Studio was withdrawn. It had no import of FCP 7 projects, no EDL, OMF or XML, no multicam, and no proper tape capture ([TidBITS](https://tidbits.com/2011/06/22/apple-starts-over-with-new-final-cut-pro-x/), read).
- **The damage control.** Apple put Final Cut Studio back on sale by phone on 1 Sept 2011 ([MacRumors](https://www.macrumors.com/2011/09/01/apple-puts-legacy-final-cut-pro-studio-back-on-sale/), headline). Multicam and better XML came in Jan 2012 ([Apple](https://www.apple.com/newsroom/2012/01/31Apple-Updates-Final-Cut-Pro-X/), headline). Many editors left for Premiere and Avid (not checked).
- **Lesson:** professionals judge a rewrite by what it can exchange: old projects, stems, MIDI, interchange formats.

### 1.29 Sonos app (May 2024)

- **What happened:**
  - The rebuilt app shipped without alarms, queue editing and some accessibility. The CEO apologised in July ([MacRumors](https://www.macrumors.com/2024/07/25/sonos-app-update-apology/), headline).
  - The old app could not be brought back ([MacRumors](https://www.macrumors.com/2024/08/20/sonos-not-rereleasing-old-app/), headline); reportedly because the server side had changed (not checked).
  - It launched over employees' objections ([MacRumors](https://www.macrumors.com/2024/09/23/sonos-app-development-insight/), headline).
  - Two product launches were held back until the app was fixed ([Engadget](https://www.engadget.com/audio/speakers/sonos-is-delaying-two-product-launches-until-it-fixes-its-buggy-app-213743460.html?src=rss), headline).
  - The CEO stepped down in January 2025 ([MacRumors](https://www.macrumors.com/2025/01/13/sonos-ceo-steps-down-after-app-redesign), headline).
- **Lesson:** never tie a rewrite to a change you cannot undo. Keep the previous build downloadable and able to work.

### 1.30 Microsoft Teams 2.0 and iWork 2013

- **Teams 2.0** was rebuilt on WebView2, with claims of 2x faster and 50 % less memory. The old and new clients ran side by side through a "try the new Teams" switch ([Microsoft](https://techcommunity.microsoft.com/blog/microsoftteamsblog/microsoft-teams-advantages-of-the-new-architecture/3775704), headline; the switch is not checked).
- **iWork (Oct 2013)** was rebuilt to match iOS and lost features and AppleScript. Apple published a list of features that would come back within six months, and iWork '09 stayed installed ([TidBITS](https://tidbits.com/2013/11/06/apple-promises-restored-iwork-features/), headline).
- **Lesson:** a switch between old and new, and a dated list of what is coming back, both limit the damage.

---

## 2. Patterns across the cases

1. **The rewrites that failed users all dropped something people relied on** (FCP X, Sonos, iWork, Logic X's 32-bit, Pro Tools 11's RTAS, Maschine 3, Rekordbox's XML). **The ones that kept trust ran old and new side by side** (Logic 9 and X, PT10 in PT11, Basecamp, Teams, iWork '09, Slack's interop, Avid's opt-in native beta).
2. **"Old projects open" is the promise users care about most.** Cakewalk kept it through two owners. Ableton's forward-only rule is documented, but it still produces angry threads.
3. **Sound changes are handled by honesty, not by perfection.** Ableton and PreSonus published what changed. The DAW null-test debates trace "sounds different" to defaults such as pan law, sample-rate conversion, dither and smoothing, not to summing ([Admiral Bumblebee](https://www.admiralbumblebee.com/music/2019/02/17/daw-v-daw-differ), headline; [Production Expert](https://www.pro-tools-expert.com/production-expert-1/daws-can-sound-different-to-each-other-but-not-for-the-reasons-you-think-heres-how), headline).
4. **Plug-in hosting is judged by the worst plug-in.** Bitwig's crash protection, REAPER's dedicated process, Studio One's skip-or-disable scan and Cubase's blocklist all exist because plug-ins misbehave. Ardour shows that isolating everything has a real price.
5. **Platform moves take a year or more, even for big teams.** Apple Silicon took 10 to 28 months for every third-party DAW. The Flash to HTML5 move took 3.5 years, Slack's rebuild more than 2, Bitwig 1.0 five.
6. **Small teams that last keep scope narrow, ship to their users constantly, and keep promises about money** (REAPER, Renoise, Tracktion, FL Studio).
7. **Trust breaks over money and licensing outlast trust breaks over bugs** (Waves, Rekordbox 6, Cakewalk, Studio One 7, Pro Tools subscription, iLok, eLicenser, Native Access).

---

## 3. The mistakes to avoid, with guards

40 mistakes in seven groups. Each one gives:
- **Evidence:** from the cases above.
- **Here:** how likely it is on AudioLab's route, and why.
- **Detect early:** a sign that shows up before users are hurt.
- **Guard:** a test, a rule, a stage gate or a backup format.

Where a guard is already in RN1 or the build, it says so instead of repeating it.

### A. Projects and the user's data

**A1. Projects that live only in the browser's storage are lost in a shell change.**
- *Evidence:* the Rekordbox library corruption; Sonos could not roll back. In AudioLab, `index.html` keeps the open projects (`audiolab-projects`, the whole state), the audio (`audiolab-files`) and the Time Machine (`audiolab-tm`) in Chromium's storage inside the desktop shell.
- *Here:* **high, at stage 4.** Removing Chromium removes that storage. Changing the app's name, identity or data folder in `desktop/` can do the same earlier.
- *Detect early:* list every key and store the app keeps (the list in this document's header is a start), and ask the shell where its data folder is.
- *Guard:* RL1 (section 5).
  - Each open project is also written as a real `.audiolab` file in a known folder.
  - A tested move of browser storage into files comes before any change to the shell's identity.
  - A rule: no stage-4 window replaces a web one while any user data still exists only in browser storage.

**A2. The file says what version it is, but nobody reads it.**
- *Evidence:* Ableton's forward-only rule, with its Save As guard; Affinity's new files not opening in the old apps. In AudioLab the writer stamps `formatVersion: 1`, and a text search finds no reader of it.
- *Here:* **high**, the day the native engine adds anything (a plug-in device, per-device algorithm versions).
- *Detect early:* open a file with `formatVersion: 2` in today's app and see what happens.
- *Guard:* RL1.
  - Add `minReader` next to `formatVersion`.
  - An older build that meets a newer file says so in words and opens nothing silently wrong.
  - Every loader version is kept, and a test opens one saved file from every version.
  - Before the first save of an older file in a newer format, keep `name.v1.audiolab` beside it, once (Ableton's Save As prompt, Logic's "import into a new project" advice).

**A3. No atomic save, autosave or rotating backups.**
- *Evidence:* REAPER keeps `.rpp-bak` and timed backups; Ableton has crash recovery; the Rekordbox loss.
- *Here:* **high once plug-ins are in the app.** A plug-in crash then takes the engine down, and if the engine is mid-write, the file goes with it.
- *Detect early:* kill the app (and the engine) during a save in a test, then open the file.
- *Guard:* RL4.
  - Write to a temp file, flush it, then rename.
  - Keep N rotating backups and a timed autosave.
  - A "kill during save" test in CI.

**A4. A missing plug-in's state is thrown away when the project is saved.**
- *Evidence:* u-he's VST3 move gives "missing plug-in" errors unless the host supports the compatibility mapping ([u-he](https://u-he.com/support/faq/troubleshooting/vst3-migration/), read). Plug-ins can come back reset ([Ableton help](https://help.ableton.com/hc/en-us/articles/115001443850-VST-AU-plug-ins-reset-to-default-preset), headline).
- *Here:* **high.** You will open projects on a machine without some plug-in. The Intel-only ones are refused today, and a maker may disappear (NI's insolvency).
- *Detect early:* a test that removes a plug-in, then opens, saves and reopens the project with it back.
- *Guard:* RL1. A placeholder device keeps the plug-in's state bytes, format, ID, maker, version and parameter snapshot exactly as they were. A round-trip test checks the bytes are unchanged.

**A5. Plug-in identity tied to one format.**
- *Evidence:* Steinberg's guideline for VST3 replacing VST2: the compatibility list in `moduleinfo.json`, `IPluginCompatibility`, `IRemapParamID` ([Steinberg](https://steinbergmedia.github.io/vst3_dev_portal/pages/Tutorials/Guideline+for+VST3+replacing+VST2.html), read). A forum complaint says the call "is never called" ([forum](https://forums.steinberg.net/t/iplugincompatibility-the-function-is-never-called/869752), headline).
- *Here:* **medium, at the AU, CLAP and VST2 stages.** Your U3 makers mostly ship several formats, and the same plug-in must survive a change of format.
- *Detect early:* the same project saved with Pro-Q 4 as VST3 must reopen with the AU or CLAP build if only that is present.
- *Guard:* store parameter IDs, never list positions. Store maker, name and version beside the format ID. Read the compatibility data from the start of N4.

**A6. No way out of the format.**
- *Evidence:* Rekordbox's XML removal; ReWire and VST2 ending and stranding projects; FCP X without interchange.
- *Here:* **medium.**
- *Detect early:* ask whether a project can be finished in another DAW today.
- *Guard:* RL1. "Export for another DAW" writes stems, MIDI, tempo and a readable JSON of the project. The `.audiolab` format gets a short written description in `docs/`.

**A7. Routing and device settings age worst.**
- *Evidence:* Apple's note on old projects arriving with "unexpected output routings" ([Apple](https://support.apple.com/en-gb/101924), read).
- *Here:* **medium.** Native output brings device names, rates, exclusive use, inputs on the AMS-24 and, later, Windows devices.
- *Detect early:* open a project on a machine with other devices.
- *Guard:* device choices live in settings, not the project. The project holds only "main output" and named inputs, with a clear fallback.

### B. Sound

**B1. Sound changes nobody decided on.**
- *Evidence:* Live 11.1 changed several filters with no legacy mode; Studio One 4 had to explain why old songs sounded different.
- *Here:* **high, through 70 to 110 port tasks.** One task "tidies" a filter or a smoothing constant, and the bit test for that device is updated rather than failed.
- *Detect early:* the bit tests' reference files change in a commit.
- *Guard:* RL2.
  - A reference file may change only in a commit that says why, in a fixed line.
  - Each device has an algorithm version, written in the project.
  - An old project keeps the old version until you choose otherwise.

**B2. Single-device proofs that miss the whole.**
- *Evidence:* the null-test literature traces DAW differences to pan law, dither, sample-rate conversion and automation smoothing.
- *Here:* **high.** Today's proofs are per device, plus the Fractals export as the final check. The mixer, sends, groups and the master limiter (a WaveShaper today) are not covered piece by piece.
- *Detect early:* render a reference song web and native, then subtract one from the other.
- *Guard:* RL2.
  - Three to five reference songs (Fractals, the Shrine demo, a test song using every device) are rendered and nulled after every engine change.
  - The target is exact bits for ported worklet devices, and below an agreed residual for the rest.
  - Pan law, dither, rate-conversion quality and every other setting that changes an export's sound (about 124 settings exist; list which) are copied into the project on save, and the project's copy wins (Logic keeps pan law per project: [Apple](https://support.apple.com/guide/logicpro/lgcp7a500829/mac), headline).

**B3. The same C++ gives different bits on the Linux test machine and on the M4.**
- *Evidence:* not from a case study. This is compiler behaviour (not checked here). Clang may fuse a multiply and an add into one instruction (FMA) depending on the target and the flags, and fused results differ in the last bit. `-ffast-math` changes results freely.
- *Here:* **medium.** The plan proves bits on Linux and on the Apple Silicon runner, so it would show up, but as a puzzle late in a task.
- *Detect early:* run the bit tests on both machines from every port task, which the plan already does. Treat a mismatch as a stop, not a note.
- *Guard:* build the engine's own devices with `-ffp-contract=off` and without fast-math. A CI check fails if those flags change.

**B4. "It sounds different" with no tool to answer it.**
- *Evidence:* the Gearspace and Cakewalk "4 DAWs, 4 renders, 4 results" threads ([Cakewalk](https://discuss.cakewalk.com/topic/57073-4-daws-4-renders-4-results), headline).
- *Here:* **high, from you.** You listen closely, through a Gryphon.
- *Detect early:* your first "sounds different" report.
- *Guard:* a hidden "compare engines" command that exports the same passage through both engines and reports the difference in dB. RL2 builds it once, and it serves every later report.

### C. Plug-ins

**C1. Trusting plug-ins to follow the specification.**
- *Evidence:* "`setProcessing` fails in many plugins" ([Steinberg forum](https://forums.steinberg.net/t/iaudioprocessor-setprocessing-fails-in-many-plugins/785558), headline); host-by-host VST3 issue lists ([KVR](https://www.kvraudio.com/forum/viewtopic.php?p=5720102), headline).
- *Here:* **high.** Your U3 list has 12 makers, and Kontakt, Melodyne and Serum 2 are each unusual.
- *Detect early:* a log of every call to a plug-in and its result.
- *Guard:* RL3. Every result code is checked and tolerated, and the host keeps going. RN1's NR5 covers the threading side.

**C2. Lifecycle calls made twice or out of order.**
- *Evidence:* a host calling `setActive` inside `reset` "kills performance" ([JUCE forum](https://forum.juce.com/t/vst3-hosting-calling-setactive-in-reset-should-not-be-necessary-kills-performance/30723), headline); hosts not calling the bypass path ([JUCE forum](https://forum.juce.com/t/hosts-not-calling-processblockbypassed/15307), headline).
- *Here:* **medium.**
- *Detect early:* a test build that asserts the order of calls.
- *Guard:* RL3. A small state machine per plug-in in the host allows only legal moves, and debug builds stop on any other.

**C3. Treating VST3 MIDI like VST2.**
- *Evidence:* the MIDI CC thread above. In VST3, controllers and pitch bend reach the plug-in as parameters, through a MIDI-mapping interface.
- *Here:* **high once you play a controller into Serum 2 or Pigments.** The mod wheel does nothing, and it looks like AudioLab's fault.
- *Detect early:* the test app sends mod wheel and pitch bend.
- *Guard:* RL3. Controllers go through the MIDI mapping from the first plug-in track, with a test using a synth that reacts to the mod wheel.

**C4. No corpus of real plug-ins run automatically.**
- *Evidence:* pluginval ([Tracktion](https://github.com/Tracktion/pluginval/blob/master/docs/Testing%20plugins%20with%20pluginval.md), headline), clap-validator, auval. Logic refuses plug-ins that fail auval ([JUCE forum](https://forum.juce.com/t/plugin-fails-logic-pro-x-auval/19128), headline).
- *Here:* **high.** Today each check is one report from your Mac.
- *Detect early:* count how many U3 plug-ins were *loaded* (not only scanned) after the last host change.
- *Guard:* RL3.
  - On the runner: the free plug-ins (Surge XT, the Steinberg examples, Vital and the like) go through load, play, state round-trip, rate change, block-size change and layout change on every host change.
  - On your Mac: a one-button self test in the test app does the same for every installed plug-in and writes a report.

**C5. An opaque or one-way blocklist.**
- *Evidence:* "Cubase 14 puts Scaler 3.1.2 on a VST Blocklist"; makers publish "how to get off Studio One's blocklist" guides ([Soundtoys](https://support.soundtoys.com/article/75-studio-one-blacklist-guide), headline).
- *Here:* **medium.** It arrives with crash recovery (NR8 names the culprit).
- *Detect early:* the first time a plug-in is marked.
- *Guard:* each entry stores the plug-in version and the reason, clears itself when the version changes, can be removed with one click, and is shown in a list.

**C6. A crash in one plug-in costs the project.**
- *Evidence:* Bitwig 2.5; REAPER's dedicated process; Ardour's figures.
- *Here:* **high.**
- *Detect early:* the crashing test plug-in from NR8.
- *Guard:* A3 (save safety) comes first. Then NR8 (restart with state, already partly built in N2b). Then NR9 ("run apart") per plug-in, as a choice. Plan order is fine. The lesson is that A3 must not slip behind them.

**C7. Starting in the same crash loop.**
- *Evidence:* Ableton's manual recovery after a crash ([Ableton help](https://help.ableton.com/hc/en-us/articles/115001878844-Recovering-a-Set-manually-after-a-crash), headline); Studio One's skip-or-disable scan ([PreSonus](https://support.presonus.com/hc/en-us/articles/360004055292-What-is-the-difference-between-skip-and-disable-in-the-new-plug-in-scan-and-how-do-I-manage-my-plug-ins-now), headline).
- *Here:* **medium.**
- *Detect early:* a test that crashes on load, then restarts.
- *Guard:* RL4. After a crash, the next start offers "open with plug-ins off". The project opens with placeholders (A4), and you turn plug-ins on one by one.

**C8. Measuring plug-in CPU only in your own terms.**
- *Evidence:* Reason 9.5 to 10.3.
- *Here:* **medium.** Your reports give per-block times. Nobody has compared them with Logic or Cubase on the same M4.
- *Detect early:* the same Serum 2 patch at 32 frames in Logic or Cubase (you have a Cubase aggregate device, so Cubase is installed).
- *Guard:* one comparison row in every stage-2/N4 report, on the same patch and buffer, with the CPU seen in Activity Monitor or each DAW's meter.

**C9. Formats added before the first one is solid.**
- *Evidence:* VST3 took ten years to settle. Bitwig 1.0 was criticised for gaps it then had to fill, rather than for missing formats.
- *Here:* **medium.** AU, CLAP and VST2 are tempting, and RN1 point 12 asks whether CLAP should move up.
- *Detect early:* a second format started while C4's corpus is not green.
- *Guard:* a stage gate. No second format until the VST3 corpus and your U3 list pass a full self test twice in a row.

**C10. Licence checks on the start or scan path.**
- *Evidence:* the iLok outages; Cubase stuck at the plug-in scan while the iLok site was down.
- *Here:* **low for AudioLab's own app, which has no licence. Medium for plug-ins**: Kontakt, Ozone and others check their own licences when loaded, and some show dialogs.
- *Detect early:* scan and open with the network off.
- *Guard:* plug-ins load after the project plays (NR10). A plug-in that shows a dialog or blocks gets a time limit and a placeholder, never a frozen app.

### D. The engine and the stages

**D1. Two changes you cannot undo in one release.**
- *Evidence:* Pro Tools 11; Sonos.
- *Here:* **high at the end of stage 3.** The web engine is switched off, and that would be tempting to combine with a new file version and new defaults.
- *Detect early:* a release note that lists more than one "cannot go back" item.
- *Guard:* RL9. Each release names its one change you cannot undo, or "none". A second one waits for the next release.

**D2. No way back.**
- *Evidence:* Sonos could not re-release the old app. Logic 9 and X, and PT10 inside PT11, were the way back.
- *Here:* **medium.** GitHub releases keep old builds. But if a newer build writes a newer project, the older build cannot open it (A2).
- *Detect early:* try last week's build on this week's project.
- *Guard:* every build stays downloadable. Native engine use is a setting until stage 3 ends. With RL1, a newer project opens in the previous build, or says why it can't.

**D3. The old engine keeps growing while you port it.**
- *Evidence:* Fowler's point that users can't wait for features; Audiotool's 3.5 years. AudioLab added the RF1 and RF2 ideas, the design chain and new devices this month alone.
- *Here:* **high.** This project ships web features constantly, and stage 3 is the longest stage (70 to 110 tasks).
- *Detect early:* the count of web-only devices goes up between two NB runs.
- *Guard:* RL10.
  - A "port debt" line in `docs/native-mac-build.md`: devices native over devices total.
  - Any new device in `index.html` is added to the port list in the same commit.
  - New DSP should be written so it can be ported with little work. This is a rule for those tasks, to be set by the user (see section 5).

**D4. The engine built around the web engine's shape.**
- *Evidence:* Reason's 64-frame blocks; Live's late multicore.
- *Here:* **medium.** RN1 already lists the block-size rule and the two paths, live and ahead (section 4, points 5 and 6).
- *Detect early:* the first port in N3 begins before those decisions are written down.
- *Guard:* a gate. The N3 port order starts only after the block-size and two-path decisions are in `docs/native-mac-build.md`.

**D5. Bridge code that never goes away.**
- *Evidence:* Fowler's transitional architecture.
- *Here:* **medium.** N2 brings the socket, the page's clock device, the ring and the drift correction.
- *Detect early:* a bridge part with no planned removal.
- *Guard:* list each bridge part in `docs/native-mac-build.md` with the stage that removes it.

**D6. Tests too short to find drift and leaks.**
- *Evidence:* AudioLab's own N1 proof lasted 3 seconds and N2a 20 seconds. RN1 flags drift as unsolved. Users play for hours.
- *Here:* **high.**
- *Detect early:* nobody has run an hour-long test yet.
- *Guard:* RL12. A soak test runs for one hour on the runner on each engine change, and eight hours once a week (counting drift corrections, failed blocks, memory, open files). The test app gets a "leave it playing overnight" report.

**D7. The fallback point passes unnoticed.**
- *Evidence:* Rowland, "Why You Shouldn't Write a DAW"; Bitwig took five years with a team.
- *Here:* **medium.** R3a says own code with JUCE as the fallback, but the plan names no point at which to switch.
- *Detect early:* stage 3 tasks running well over the 70 to 110 estimate.
- *Guard:* a written check-point (RL9). When 30 port tasks are done, compare actual against estimate. If the work runs over by half, look at JUCE or Tracktion Engine again, as a decision for you, not drift.

### E. Native screens (stage 4)

**E1. Native screens that do less than the web ones.**
- *Evidence:* FCP X; Sonos; iWork; Logic X; Maschine 3.
- *Here:* **high.** About 17 windows and 124 settings, and a cloud task cannot feel a drag.
- *Detect early:* a native window lands before its parity list exists.
- *Guard:* RL5.
  - A parity list for each window, generated from the feature inventory (`tools/feature-lab/rf1/inventory.py`).
  - A native window becomes the default only when its list is complete, or when the gaps are published to you and you accept them.
  - The web window stays available behind a switch until then.

**E2. Big-bang switch of the screens.**
- *Evidence:* Slack shipped piece by piece with a two-way bridge and ran a new-only build in private for a year.
- *Here:* **medium.**
- *Guard:* one window at a time, as the plan says. Add a private "native only" build for you long before any window is the default.

**E3. The interim web interface feels foreign on a Mac.**
- *Evidence:* 1Password 8.
- *Here:* **medium.** AudioLab will be an Electron interface for months or years. Your U4f pick values native feel.
- *Detect early:* list Mac conventions the app misses: menu bar, Cmd shortcuts, standard file dialogs, text fields, scroll physics.
- *Guard:* a short Mac-conventions checklist added to the design chain's reviews. It is cheaper than waiting for stage 4.

**E4. Rewriting the screen when the problem is the thread.**
- *Evidence:* Linear; VS Code's process work.
- *Here:* **medium.** 47 canvases drawn on the page's thread.
- *Detect early:* measure frame times at 240 Hz with the meters moved to shared memory (NR12) before deciding stage 4.
- *Guard:* record the frame-time histogram before and after NR12. Decide R2 (native screens) with that number in hand.

### F. Platforms

**F1. Being caught out by the yearly macOS release.**
- *Evidence:* Serato's warnings; Gearnews on Sequoia ([Gearnews](https://www.gearnews.com/macos-sequoia/), read); NI users asking why it can't keep up.
- *Here:* **high, every September.** You run macOS 27.2 now. Unsigned apps are the first to feel Gatekeeper changes.
- *Detect early:* Apple's June beta.
- *Guard:* RL8. In June, build and run the test app on the beta runner image if GitHub has one (not checked). A one-line status in `docs/native-mac-build.md` each September.

**F2. No Apple account when it suddenly matters.**
- *Evidence:* not from a case. Sequoia made opening unsigned apps harder (not checked), and every DAW is notarised.
- *Here:* **medium.** Fine for you alone (U1c). A blocker the day someone else installs it, or if a macOS release tightens "Open Anyway" again.
- *Guard:* keep the build signable (the hardened-runtime entitlements written down and tested in CI, unsigned), so getting the account is one step, not a project. Revisit U1c before the first build goes to another person.

**F3. Windows treated as "the same engine, plus a driver".**
- *Evidence:* Windows Defender slowing plug-in scans ([Steinberg](https://helpcenter.steinberg.de/hc/en-us/articles/18208450029330-Slow-VST-plug-in-scanning-on-Windows), headline); DPC latency from drivers ([LatencyMon](https://www.resplendence.com/latencymon_using), headline); ASIO driver quality ([Cakewalk](https://help.cakewalk.com/hc/en-us/articles/36144391116953-Troubleshooting-Common-Issues-with-Driver-Modes-in-Cakewalk), headline). Logic dropped Windows once and never returned.
- *Here:* **medium, after stage 3** (R5b). Low now.
- *Guard:* for RN2 and the Windows stages:
  - a diagnostics page (driver, latency, what blocks);
  - the scan cache and the out-of-process scan from day one;
  - the ASIO licence request sent early, as the plan already says;
  - no promise of a Windows date until the work has started.

### G. Trust, team and money

**G1. Announcing before it works.**
- *Evidence:* Bitwig's collaboration feature, promised since 2012.
- *Here:* **medium.** This project writes many plans and pick pages. They are internal now, but they will read as promises if they are ever made public.
- *Guard:* public notes describe what is in a build, never what will be.

**G2. A late or forced change of price model.**
- *Evidence:* Waves; Rekordbox 6; Cakewalk; Studio One 7; the Pro Tools subscription.
- *Here:* **low now, high later.** No price has been decided.
- *Guard:* RL11. Decide and write down the model (and what is promised to early users) before the first native build goes to anyone else. Never convert later without a choice for existing users.

**G3. A licence or account server that can stop work.**
- *Evidence:* iLok 2013; the eLicenser's end; Native Access 2; iZotope logins.
- *Here:* **low.** Nothing exists yet.
- *Guard:* RL11. The app and its projects always open offline. Any future licence check has a long grace period and never runs on the start path.

**G4. Promising "every old project opens" without testing it.**
- *Evidence:* Cakewalk kept the promise; Ableton's limits produced angry threads anyway.
- *Here:* **medium.**
- *Guard:* a folder of saved projects, one from each `formatVersion` and app version (`tests/projects/`), opened by CI on every change to the loader (RL1).

**G5. Moving from one AI session's memory to another's without a written rule.**
- *Evidence:* AudioLab's own situation. Many parallel tasks edit different parts. VS Code's lesson is to let the build enforce the layer rules.
- *Here:* **high.** RN1 point 1 says "no `std::mutex` on the audio path", and that holds only if every future session reads it.
- *Detect early:* a rule that exists only in a document.
- *Guard:* turn each rule into a check that fails the build where possible:
  - RealtimeSanitizer (NR2);
  - the float flags (B3);
  - reference files changed only with a reason line (B1);
  - no new device without a port-list line (D3);
  - no user data only in browser storage (A1).

---

## 4. What AudioLab is already doing right

- **The route itself.** Route C then B (R1c) is the strangler fig. It is what Fowler recommends, what Slack did, and what Figma did with its renderer, and it is the opposite of Netscape and Sonos. Every stage leaves a working app.
- **Bit-for-bit proofs** (144,000 of 144,000 samples for the Bitcrusher, 287,998 of 287,998 through the engine). This is how a port keeps Spolsky's "bug fixes" and how B1 can be caught at all.
- **Mac first, one platform at a time** (R5b). No ground lost to a half-finished Windows port, which is what stranded Logic's Windows users.
- **VST2 last, and only if needed** (P6a). This avoids the format Steinberg spent a decade retiring.
- **The plug-in scan in a child process.** One bad bundle (`helisert_6.0.vst3`) did not stop the scan.
- **Intel-only plug-ins refused with a reason.** The honest compatibility report that Logic users lacked in 2013.
- **The test app on your Mac from day one**, with real hardware reports: the Gryphon, the AMS-24, Serum 2 at 32 frames. This is REAPER's daily-beta lesson at a small scale, and it already found a real fault (the rate read before re-plug, fixed in 0.3).
- **Crash recovery with a fallback** (N2b): the engine restarts at most three times a minute, then the page goes back to the web engine. This is Figma's in-session fallback.
- **An open project format.** JSON plus raw audio in a gzip, versioned from the start. It is readable by anything, so no Rekordbox-style lock-in.
- **Plug-ins inside the engine first, "run apart" per plug-in later** (P5a). This matches the Ardour and Bitwig evidence: isolation as a per-plug-in choice, not for everything.
- **Your own plug-in list** (U3) as the test target, rather than abstract conformance.
- **Writing decisions down** (picks, assumptions, "what is not proven"). This is what lets many sessions avoid repeating each other's mistakes.

---

## 5. Proposed changes and new tasks for the native plan

None of these was added to another task or to `docs/native-mac-build.md`. Task NB folds research into its own stage order (your decision of 27 November for RN1), so these are written for NB to adopt the same way, or for you to choose.

| # | What | Where it fits | Size |
|---|---|---|---|
| **RL1** | **Project safety.** `minReader` beside `formatVersion` and a loader that reads both. A backup before the first save in a newer format. A placeholder device keeping a missing plug-in's state byte for byte. A test folder of projects from every version, opened in CI. "Export for another DAW" (stems, MIDI, tempo, JSON). A short written description of the format. | Before plug-in tracks enter the app (N4). The placeholder must exist before the first saved project with a plug-in. Needs an `index.html` change, so it runs in turn. | 2 to 3 tasks |
| **RL1b** | **Get the user's data out of browser storage.** Every open project also kept as a real `.audiolab` file in a known folder. A tested move of `audiolab-projects`, `audiolab-files` and `audiolab-tm` into files. A rule that the desktop shell's identity and data folder never change without this. | Before any change to the app's identity in `desktop/`, and long before stage 4. | 1 to 2 tasks |
| **RL2** | **Reference songs and sound versions.** 3 to 5 songs rendered web against native and subtracted after every engine change, on Linux and Apple Silicon. Algorithm version per device in the project. Sound-changing settings saved in the project. Reference files changed only with a reason line. A hidden "compare engines" command for your "sounds different" reports. Float flags fixed (`-ffp-contract=off`, no fast-math) and checked by CI. | Start of N3, before the first port. | 2 tasks |
| **RL3** | **Plug-in corpus and host state machine.** Free plug-ins run through load, play, state, rate, block-size and layout changes on the runner after every host change. A legal-call state machine. MIDI controllers through the VST3 MIDI mapping. A one-button self test in the test app over every installed plug-in. | With NR5, in N4. | 2 tasks |
| **RL4** | **Saving safely and starting after a crash.** Atomic save, rotating backups, timed autosave, a "kill during save" test, and "open with plug-ins off" after a crash. | Before N4 puts plug-ins in the app; can go with NR8. | 1 to 2 tasks |
| **RL5** | **Parity lists for the switch-offs.** Generated from `tools/feature-lab/rf1/inventory.py`: one for the web engine's switch-off (every device and export option) and one per window for stage 4. Nothing replaces its web version until its list is green or you accept the published gaps. | End of stage 3 and all of stage 4. | 1 task to build, then a check per window |
| **RL6** | **Old and new side by side.** Native engine use stays a setting (default chosen by you) until stage 3 ends. Every build is downloadable. A newer project opens in the previous build or explains why not. | From N2 onwards. | Rule plus a small part of N2 |
| **RL7** | **A private "native only" build for you** in stage 4, long before any native window is the default (Slack's year of internal use). | Stage 4. | Part of stage 4 |
| **RL8** | **The yearly macOS check.** In June, build and run on the newest macOS image GitHub offers. In September, a one-line status in `docs/native-mac-build.md`. Keep the build signable (entitlements tested unsigned) so getting the Apple account is one step. Revisit U1c before any build goes to another person. | Yearly; the first check in June 2027. | Small |
| **RL9** | **Stage gates written down.** One change you cannot undo per release, named in the notes. No second plug-in format until the VST3 corpus and your U3 self test pass twice. Stage 3 is called done when "Fractals v10 plays wholly native" holds, not by task count. A check-point after 30 port tasks: estimate against actual, and a JUCE or Tracktion Engine review if the work runs over by half. | Add to `docs/native-mac-build.md` as rules. | No task; a doc change by NB |
| **RL10** | **Port debt.** A "devices native / devices total" line in `docs/native-mac-build.md`, updated by every NB run. A rule for every task that adds a device to `index.html`: add it to the port list in the same commit. **This rule touches other tasks, so it is your decision.** | From now. | Rule |
| **RL11** | **Money and promises, decided early.** Write down the price model and what early users are promised before a native build goes to anyone else. Offline always works. No feature announced before it works. | Before the first build goes to other people. | A pick for you |
| **RL12** | **Soak tests.** One hour of playback on the runner on each engine change, and eight hours once a week (counting drift corrections, failed blocks, memory, open files). A "leave it playing overnight" report in the test app. | From N2 (drift) onwards. | 1 task |

**Two changes to the existing plan, for NB to weigh:**
1. **Move "saving safely" (RL4) and the plug-in placeholder (RL1) ahead of plug-in tracks in the app.** In the evidence, losing work hurts more than every other failure. The present stage order puts crash recovery (NR8) and "run apart" (NR9) in N4, but nothing protects the file itself.
2. **Treat browser storage as user data (RL1b).** The native plan describes `.audiolab` files, but today the working copy of every open project is in Chromium's storage. Stage 4 removes Chromium, so this must be solved before then, and it is cheap now.

---

## 6. What this research could not settle

- **Team sizes** for Ableton, Steinberg, Avid, Apple's Logic team and Reason Studios were not found. Bitwig (30 in 2024), Cockos (two), Image-Line (about 15 on the Mac port) and KristalLabs ("small") were.
- **Which features Maschine 2.0 removed**, and the exact text of Serato's macOS warnings: not read.
- **Whether Logic X had any 32-bit bridge**, and **whether Avid later brought back perpetual Pro Tools licences**: headline-level only.
- **The current CLAP host list:** Bitwig, REAPER, FL Studio and Studio One are from knowledge. Ableton Live 13's public beta (around 10 Nov 2026) was announced with ARA 2, and no headline seen mentions CLAP ([The Fader](https://thefader.com/2026/11/10/ableton-announces-live-13-with-ara-2-support-and-a-new-step-sequencer), headline).
- **Sonos's cost figure**, **Slack's memory figures** and **Linear's sync internals**: not checked.
- **Whether a GitHub macOS beta runner exists in June**, for RL8: not checked.
- **The FMA point (B3)** is compiler knowledge, not something a case study showed. RL2's check on both machines will show whether it matters.
- **Talks on "what I'd do differently"** by Jules Storer and Timur Doumler were found only as titles ([Audio Programmer podcast](https://forum.juce.com/t/jules-storer-interview-on-the-audio-programmer-podcast/34061), [CppCon 2015](https://isocpp.org/blog/2016/06/cppcon-2015-cpp-in-the-audio-industry-timur-doumler)). Neither was watched. Fabian Renn-Giles, "Real-time Confessions in C++" (ADC23), the same ([Class Central](https://classcentral.com/classroom/youtube-real-time-confessions-in-c-fabian-renn-giles-adc23-320061)). Ross Bencina's "Real-time audio programming 101" was read; its rules ("If you don't know how long it will take, don't do it"; "It's OK to make the user wait, so long as the audio callback doesn't have to") are already in RN1 in substance ([Bencina](https://hn.jakechampion.name/reader/http://www.rossbencina.com/code/real-time-audio-programming-101-time-waits-for-nothing), read).

---

## 7. Sources

All links are given in place above, each marked "read", "headline" or "not checked". The most useful, by the weight they carry here:

- Ableton, backward compatibility: https://help.ableton.com/hc/en-us/articles/360000841004
- Ableton, sound changes in Live 11: https://help.ableton.com/hc/en-us/articles/4406754127378-Sound-changes-in-Ableton-devices-in-Live-11
- Ableton, multicore: https://help.ableton.com/hc/en-us/articles/209067649
- Bitwig 2.5 crash protection: https://musicradar.com/news/with-bitwig-studio-25-plugins-will-no-longer-crash-your-entire-projects
- Bitwig's 10 years: https://www.musicradar.com/news/10-years-bitwig
- Bitwig 1.0 review: https://www.soundonsound.com/reviews/bitwig-studio?amp
- Bitwig 3, the modular core: https://cdm.link/2019/01/bitwig-studio-3-modular/
- Studio One founders: https://en.audiofanzine.com/general-sequencer/presonus/studio-one-2-professional/editorial/articles/interview-with-the-father-of-studio-one.html
- Apple, old Logic projects: https://support.apple.com/en-gb/101924
- Pro Tools 11 review: https://www.soundonsound.com/reviews/avid-pro-tools-11
- Pro Tools Apple Silicon beta: https://www.avid.com/resource-center/pro-tools-apple-silicon-public-beta
- iLok 2013: https://sonicscoop.com/?p=42974
- Steinberg on VST2's end: https://www.musicradar.com/news/steinberg-says-that-vst-2-is-coming-to-an-end-but-what-does-this-mean-for-your-daw-and-plugins
- Steinberg licensing interview: https://www.kvraudio.com/interviews/steinbergs-new-licensing-system-an-interview-with-ben-timms-56005
- VST3 replacing VST2: https://steinbergmedia.github.io/vst3_dev_portal/pages/Tutorials/Guideline+for+VST3+replacing+VST2.html
- u-he on the VST3 move: https://u-he.com/support/faq/troubleshooting/vst3-migration/
- Steinberg relicensing (VST3 MIT, ASIO GPLv3 or proprietary): https://librearts.org/2025/11/steinberg-relicenses-vst3-and-asio/
- Reason 10.3: https://cdm.link/2018/12/reason-10-3-vst/
- REAPER: https://tapeop.com/interviews/80/justin-frankel-and-christophe-thibault and the MusicRadar piece linked in 1.7
- FL Studio's port: https://www.embarcadero.com/case-study/image-line-software-case-study
- Cakewalk: https://en.wikipedia.org/wiki/Cakewalk_by_BandLab and https://www.musicradar.com/news/free-cakewalk-daw-discontinued
- Ardour on in-process plug-ins: https://ardour.org/plugins-in-process.html
- Tracktion: https://musicradar.com/news/tech/meet-the-programmers-tracktion-software-corporation-624725
- JUCE 8 licence: https://forum.juce.com/t/amendments-to-the-juce-end-user-licence-agreement-for-juce-8/61265
- "Why You Shouldn't Write a DAW": https://www.kvraudio.com/forum/viewtopic.php?p=8951463
- Audiotool: https://en.wikipedia.org/wiki/Audiotool
- Native Instruments' insolvency: https://bedroomproducersblog.com/2026/01/28/native-instruments-insolvency/
- Rekordbox: https://cdm.link/rekordbox-6-sync-cloud-more/ and https://forums.pioneerdj.com/hc/fr/community/posts/900001469586-Rekordbox-6-04-possibly-corrupted-my-library-and-other-glitches
- Waves: https://www.musictech.com/news/industry/waves-subscription-only-u-turn-licenses/
- Joel Spolsky: https://joelonsoftware.com/2000/04/06/things-you-should-never-do-part-i
- Martin Fowler: https://www.martinfowler.com/bliki/StranglerFigApplication.html
- Slack: https://slack.engineering/rebuilding-slack-on-the-desktop/
- Figma, WebGPU: https://www.figma.com/blog/figma-rendering-powered-by-webgpu/
- Figma, WebAssembly: https://www.figma.com/blog/webassembly-cut-figmas-load-time-by-3x/
- VS Code sandbox: https://code.visualstudio.com/blogs/2022/11/28/vscode-sandbox
- 1Password: https://1password.com/blog/1password-8-the-story-so-far and https://sixcolors.com/post/2021/08/not-important-enough-1password-abandons-its-native-mac-app/
- Basecamp: https://signalvnoise.com/posts/3830-ta-da-list-until-the-end-of-the-internet
- Sketch: https://www.sketch.com/blog/sketch-in-2021-and-beyond/
- Affinity: https://tidbits.com/2025/10/31/canvas-affinity-combines-photo-designer-and-publisher-into-one-free-app/
- Final Cut Pro X: https://tidbits.com/2011/06/22/apple-starts-over-with-new-final-cut-pro-x/
- Sonos: https://www.macrumors.com/2024/08/20/sonos-not-rereleasing-old-app/
- Discord: https://infoq.com/news/2026/11/discord-rust-rewrite-gpui-zed
- Ross Bencina: https://hn.jakechampion.name/reader/http://www.rossbencina.com/code/real-time-audio-programming-101-time-waits-for-nothing
