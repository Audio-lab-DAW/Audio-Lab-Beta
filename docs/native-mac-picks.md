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

### Still open from the Mac
- Load plug-ins and play them (time per block on the M4, the plug-in windows, the keys).
- Buffer 128, 64 and the Gryphon's lowest (106 frames at 352.8 kHz).
- The AMS-24.
