# AudioLab native Mac: the picks and the first report from the Mac (task NM1)

Plan: `docs/native-mac-plan.md`. Pick page: https://claude.ai/artifact/17AwgeWUCCTaDX1Ct3mmcn

## The picks line, 27 November 2026

`NM1 picks: R1c R2b R3a R4a R5b R6a | P1a P2a P3a P4a P5a P6a P7a | U1c U2a U4abcdf U5b | U3: Fab filter ozone native instruments kick 3 kilohearts melodyne izotope neutron arturia scaler xfer serum 2 steinberg sublabXL`

| Pick | Meaning | Same as recommended? |
|---|---|---|
| R1c | Route C then B: the native C++ engine first, the present interface kept, native screens after | yes |
| R2b | The native screens (stage 4) are decided when the engine has moved | yes |
| R3a | Own code now, JUCE as the fallback | yes |
| R4a | Native output with device control first, then VST3 | yes |
| **R5b** | **Windows follows after the engine has moved (stage 3)**: Mac first all the way | no, the star was "after stage 2" |
| R6a | Keep the present shell (Electron) while the screens are web | yes |
| P1a | Instruments and effects | yes |
| P2a | Free well-known plug-ins as the first tests | yes |
| P3a | The plug-in's own window and an AudioLab strip | yes |
| P4a | Then Audio Units, CLAP, VST2 | yes |
| P5a | Plug-ins inside the engine first, "run apart" per plug-in later | yes |
| P6a | VST2 last, and only if owned plug-ins need it | yes |
| P7a | Intel-only plug-ins later, with "run apart" | yes |
| **U1c** | **No Apple Developer account for now** | no, the star was "when the first native build goes to other people" |
| U2a | Direct download | yes |
| **U4abcdf** | What matters most: bit-perfect output to the DAC, lowest latency, low CPU, the plug-ins, **and a native look and feel at 240 Hz**. Not picked: a small app that starts fast | f was added |
| **U5b** | **Fractals v10 becomes the fresh-install song later, with the first native build** | no, the star was "add it now" |
| U3 | Plug-ins that must work: FabFilter, Ozone, Native Instruments, Kick 3, Kilohearts, Melodyne, iZotope Neutron, Arturia, Scaler, Xfer Serum 2, Steinberg, SubLabXL | |

### What the picks change in the plan
- **Windows (R5b):** the Windows device layer moves behind stage 3. Stages 1 to 3 are Mac only. The engine stays portable C++ so nothing has to be redone.
- **No Apple account (U1c):** every native build is signed ad hoc and opened through "Open Anyway". Nothing in stages 1 to 3 needs the account. Notarisation and the hardened runtime stay out until the account exists.
- **240 Hz and native look (U4f) with R2b:** the screens are still decided after stage 3, but they are wanted, so nothing in stages 1 to 3 may make stage 4 harder: the engine keeps all state and the interface stays a view on it. R6a (Electron, not the 60 Hz system web view) fits this pick.
- **Fractals v10 (U5b):** no task now. It is added with the first native build.
- **Order inside the stages (U4 a, b, c, d):** stage 1 does exclusive use, exact rate and the real format first; latency and CPU are the measure for every engine task in stage 3.

## The first report from the Mac (27 November 2026)

"AudioLab VST3 test" 0.1 on the user's Mac: Mac16,10, Apple M4, macOS 27.2. The app ran, scanned and opened the DAC. No plug-in was loaded yet in this report, so there are no figures for time per block.

### Devices
- **iFi Gryphon** ("iFi (by AMR) HD USB Audio", USB): 2 outputs; rates 44.1, 48, 88.2, 96, 176.4, 192, 352.8, 384, 705.6 and 768 kHz, and the rate can be set; 32-bit integer on the wire, 60 formats offered; **a volume the computer can set (main)**; exclusive use can be taken; buffer 106 to 4096 frames. It opened at 352.8 kHz with 512 frames (1.45 ms); device latency 90 + safety 90 frames.
- **Zoom AMS-24: not in the list.** The list is everything Core Audio reports, inputs included, so macOS did not see the unit at that moment. Open.
- Others seen: Mac mini Speakers (44.1 to 96 kHz), Odyssey G80SD over DisplayPort (24-bit integer, no settable volume), Bose Mini II SoundLink over Bluetooth, a USB microphone, and virtual devices (Background Music, BlackHole, eqMac, a Cubase aggregate). The default output was the eqMac device at 16 kHz.
- Things the engine must cope with, seen here: a default device at 16 kHz; virtual devices that offer "1 to 1,000,000,000 Hz"; a device (Odyssey) with no volume; an aggregate that refuses exclusive use.

### Plug-ins
- 253 bundles in the two VST3 folders. **221 read, 222 plug-ins.** No crash, no time-out. Slowest scans: Kontakt 7 and 8 at about 1.5 s; Native Instruments effects about 0.25 s; most others 0.01 to 0.15 s.
- **Every maker in U3 was found built for Apple Silicon:** FabFilter (25), iZotope Ozone 11 (18), Neutron 4 (9) and RX 11 (17), Native Instruments (Kontakt 7 and 8, Bite, Choral, Dirt, Flair, Freak, Raum, Replika), Kick 3, Kilohearts (Phase Plant, Multipass, Snap Heap and the kHs set), Melodyne, Arturia (Pigments, Efx FRAGMENTS), Scaler 3, Serum 2 and Serum 2 FX, Steinberg (HALion 7, HALion Sonic, Padshop, Retrologue, The Grand 3, SpectraLayers, WaveLab), SubLabXL.
- **31 bundles are Intel only** and were reported as such: the 14 RX 9 modules (RX 11 is installed and loads), Arcade, Infiltrator, Shaper2, PitchMonster, Tantrum, Tapex2, Texture, Transient Master, Midnight Mirage, Black, Boost, Brass, Clone, Duck, Hatz, Minipol, Vybz. None of them is in U3, which fits P7a (the Rosetta helper later).
- **1 bundle is broken:** `helisert_6.0.vst3` ("Could not create Bundle").
- Only two bundles are Apple Silicon only (Mammoth, The Infinite Crate); the rest are universal.

### Notes for stage 2 from the U3 list
- **Melodyne** works fully only through ARA, an extension next to VST3 with its own SDK. As a plain VST3 it works in its transfer mode (you play the audio into it). ARA is not in the plan yet; it is a separate piece of work after VST3 tracks exist.
- **Kontakt** loads samples in the background and keeps large states; it is the test for "wait for the plug-in in export" and for state size in the project file.
- **Ozone, Neutron, Pro-L 2, Pro-Q 4 (linear phase)** report latency; they are the test for delay compensation, which the build machine could not test (all its plug-ins report 0).
- **Serum 2.vst3** holds two plug-ins in one bundle (instrument and effect); the scanner listed both.
- **Scaler 3 and ChordPotion** are note plug-ins: they need note output from a plug-in to reach another track. Not in stage 2's first cut; written down here.

### Second report, the same day: plug-ins loaded and played
- **43 loads of 41 different plug-ins, none failed.** FabFilter (One, Micro, Pro-C 2, Pro-DS, Pro-G, Pro-L 2, Pro-Q 2, 3 and 4, Pro-R and Pro-R 2, Saturn and Saturn 2, Simplon, Timeless 2 and 3, Twin 2 and 3, Volcano 2 and 3), iZotope (Aurora, six Neutron 4 modules and Neutron 4, six Ozone 11 modules), Native Instruments (Flair, Freak), BABY Audio (Atoms, BA-1, Parallel Aggressor), OTT, Omnivocal Beta, Pigments. The Intel-only Arcade was refused with the right reason.
- **Load times:** most 15 to 190 ms; every Neutron 4 module about 1.1 s; Ozone 11 Master Rebalance 0.6 s; Pigments 3.3 and 4.1 s.
- **Latency is reported by real plug-ins** (the build machine had none): Pro-L 2 2,875 samples, Ozone 11 Vintage Tape 2,227, Master Rebalance 2,048, Aurora 1,152, Ozone Clarity and Neutron Unmask 1,024, Pro-DS 661, Neutron Compressor 353, Neutron Transient Shaper 132, Pigments 44, Flair and Freak 16, OTT 2.
- **State sizes:** 99 bytes (Micro) to 284,170 bytes (Pigments).
- **Parameter counts:** up to 4,365 (Pigments); several above 2,000 (Atoms, BA-1, Omnivocal). The strip must not list all of them.
- **Sound:** the user heard the test melody. Pigments through the Bose Bluetooth speaker at 44.1 kHz and 512 frames: 1,823 blocks, average 0.70 ms per block (6.1 % of the block), worst 1.55 ms (13.3 %), 0 failed blocks, 1 overload reported by the device.
- **Not done in this report:** no plug-in window was opened, the Buffer menu was not used, and no plug-in was played through the Gryphon (the output was switched to the Bose before loading).
- **Small faults of the test app seen in the report:** "Play test pattern" with nothing loaded is silent and does not say so; the line after "test pattern off." runs on without a break.

### Third report, the same day: Serum 2 through the Gryphon, down to 32 frames
The Gryphon was set to 48 kHz, 32-bit integer, in Audio MIDI Setup; its buffer range at that rate is 15 to 4096 frames, device latency 14 + safety 14 frames. Serum 2 loaded in 100 ms (2,623 parameters, 2,172 bytes of state). The user heard the melody clearly at every size.

| Buffer | Block lasts | Serum 2, average per block | Worst block | Failed blocks | Overloads |
|---|---|---|---|---|---|
| 512 frames | 10.67 ms | 289 µs = 2.7 % | 1,021 µs = 9.6 % | 0 | 0 |
| 128 frames | 2.67 ms | 38 µs = 1.4 % | 185 µs = 7.0 % | 0 | 0 |
| 64 frames | 1.33 ms | 24.5 µs = 1.8 % | 178 µs = 13.3 % | 0 | 0 |
| 32 frames | 0.67 ms | 16.1 µs = 2.4 % | 139 µs = 20.8 % | 0 | 0 |

- Every buffer size asked for was accepted by the device. **32 frames ran clean on real hardware**: this is the point the build machine could not show.
- Calculated, not measured: at 32 frames the way out is 32 + 14 + 14 = 60 frames, 1.25 ms at 48 kHz. The web engine's measured round trip in the plan is 25 ms and more.
- The figures are one instrument playing a simple pattern from its start patch. A full song is another matter; the worst block (20.8 % at 32 frames) is the number to watch as more is added.

### The plug-in window, the same day (screenshot from the user)
Serum 2's own window opened at 1190 x 740, drawn in full, next to the main window. Clicking the piano in Serum's window makes sound through the Gryphon at 32 frames. The two layout fixes made blind before the published build (the plug-in window placed on the screen, the key hint in full) are both seen working in this picture. The read-out showed "moves in its window 0": piano clicks are notes, not parameter moves, so whether a knob turned in the window reaches the host is not shown yet.

### Still open from the Mac
- A knob turned in a plug-in window (the read-out "moves in its window" should count up), and the computer keys A to K.
- The Zoom AMS-24, once macOS lists it.
- Kontakt 8, Serum 2, Phase Plant, Kick 3, Melodyne, Scaler 3, SubLabXL and a Steinberg instrument were scanned but not loaded yet.
- The AMS-24.
