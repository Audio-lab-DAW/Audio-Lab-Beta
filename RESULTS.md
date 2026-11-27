# Native lab results

```
arch: arm64
ProductName:		macOS
ProductVersion:		26.7.2
BuildVersion:		25G332
Apple M1 (Virtual)
VirtualMac2,1
Apple clang version 21.0.0 (clang-2100.1.1.101)
Target: arm64-apple-darwin25.6.0
cmake version 4.5.0
```

## Test A: one effect, native against the web engine

```
plain   own maths: identical, all 48000 samples | web numbers: identical, all 48000 samples | pow/exp results same as the browser: yes | speed 3514 x real time
filter  own maths: identical, all 48000 samples | web numbers: identical, all 48000 samples | pow/exp results same as the browser: yes | speed 1847 x real time
dither  own maths: identical, all 48000 samples | web numbers: identical, all 48000 samples | pow/exp results same as the browser: yes | speed 2796 x real time
--- control: the same program built with fused multiply-add allowed ---
plain   own maths: identical, all 48000 samples | web numbers: identical, all 48000 samples | pow/exp results same as the browser: yes | speed 2491 x real time
filter  own maths: identical, all 48000 samples | web numbers: identical, all 48000 samples | pow/exp results same as the browser: yes | speed 3564 x real time
dither  own maths: identical, all 48000 samples | web numbers: identical, all 48000 samples | pow/exp results same as the browser: yes | speed 2368 x real time
```

### Devices of the build machine as it comes

- **Apple Virtual Sound Device** (built-in, default output): out 2 ch, in 0 ch, 48000 Hz now; rates offered: 48000, 96000; rate can be set: yes; buffer 512 (range 15 to 4096, can be set: yes); volume the computer can set: yes (main); on the wire: 32-bit float, 2 ch, 48000 Hz, mixable; exclusive use can be taken: yes
- **Apple Virtual Sound Device** (built-in): out 0 ch, in 2 ch, 48000 Hz now; rates offered: 48000, 96000; rate can be set: yes; buffer 512 (range 15 to 4096, can be set: yes); volume the computer can set: no; on the wire: ?; exclusive use can be taken: yes
- **Null Audio Device** (virtual): out 2 ch, in 2 ch, 44100 Hz now; rates offered: 44100, 48000; rate can be set: yes; buffer 512 (range 14 to 4096, can be set: yes); volume the computer can set: yes (main); on the wire: 32-bit float, 2 ch, 44100 Hz, mixable; exclusive use can be taken: yes

### Devices after adding the virtual device BlackHole

- **Apple Virtual Sound Device** (built-in, default output): out 2 ch, in 0 ch, 48000 Hz now; rates offered: 48000, 96000; rate can be set: yes; buffer 512 (range 15 to 4096, can be set: yes); volume the computer can set: yes (main); on the wire: 32-bit float, 2 ch, 48000 Hz, mixable; exclusive use can be taken: yes
- **Apple Virtual Sound Device** (built-in): out 0 ch, in 2 ch, 48000 Hz now; rates offered: 48000, 96000; rate can be set: yes; buffer 512 (range 15 to 4096, can be set: yes); volume the computer can set: no; on the wire: ?; exclusive use can be taken: yes
- **BlackHole 2ch** (virtual): out 2 ch, in 2 ch, 48000 Hz now; rates offered: 8000, 16000, 24000, 44100, 48000, 88200, 96000, 176400, 192000, 352800, 384000, 705600, 768000; rate can be set: yes; buffer 512 (range 15 to 4096, can be set: yes); volume the computer can set: yes (main); on the wire: 32-bit float, 2 ch, 48000 Hz, mixable; exclusive use can be taken: yes
- **Null Audio Device** (virtual): out 2 ch, in 2 ch, 44100 Hz now; rates offered: 44100, 48000; rate can be set: yes; buffer 512 (range 14 to 4096, can be set: yes); volume the computer can set: yes (main); on the wire: 32-bit float, 2 ch, 44100 Hz, mixable; exclusive use can be taken: yes

### Opening the default output

- opened **Apple Virtual Sound Device** through Core Audio and played 1.0 s: 890 callbacks, 64 to 64 frames per callback, 5 overloads, render 0.7 microseconds on average
- buffer: asked for 64 frames, device now runs 64 (accepted)
- sample rate: asked for 96000 Hz, device then ran 96000 Hz (switched); put back to 48000 Hz (ok)
- exclusive use: taken; given back: yes

### Opening BlackHole

- opened **BlackHole 2ch** through Core Audio and played 1.0 s: 773 callbacks, 64 to 64 frames per callback, 0 overloads, render 0.5 microseconds on average
- buffer: asked for 64 frames, device now runs 64 (accepted)
- sample rate: asked for 96000 Hz, device then ran 96000 Hz (switched); put back to 48000 Hz (ok)
- exclusive use: taken; given back: yes

## Test B: command line VST3 host

Scan: 8 bundles, 7 read, 1 failed, 44 plug-ins. The host stayed alive: yes.
- Surge XT Effects.vst3 [x86_64 arm64], 0.07 s: Surge XT Effects (effect)
- Surge XT.vst3 [x86_64 arm64], 0.09 s: Surge XT (instrument)
- al-strict-synth.vst3 [arm64], 0.01 s: AL Strict Synth (instrument), AL Strict Synth 33 outs (instrument)
- adelay.vst3 [arm64]: FAILED, crashed while loading (signal 6)
- again.vst3 [arm64], 0.03 s: AGain VST3 (effect), AGain SideChain VST3 (effect)
- al-strict-synth.vst3 [arm64], 0.01 s: AL Strict Synth (instrument), AL Strict Synth 33 outs (instrument)
- mda-vst3.vst3 [arm64], 0.06 s: mda Ambience (effect), mda Bandisto (effect), mda BeatBox (effect), mda Combo (effect), mda DeEsser (effect), mda Degrade (effect), mda Delay (effect), mda Detune (effect) and 26 more
- note-expression-synth.vst3 [arm64], 0.23 s: Note Expression Synth With UI (instrument), Note Expression Synth (instrument)

### ADelay (Steinberg Media Technologies, effect) [arm64]

- loaded in 14 ms; audio in 2 ch, out 2 ch, note inputs 0; latency 0 samples
- parameters: 2 (2 can be automated); first: Bypass = Off, Delay = 1.0000 sec
- sound: audio run through, peak -1.4 dB, 1500 blocks of 128 frames at 48000 Hz, 0 failed
- time per block: average 1.3 microseconds (0.05 % of the block), 99th percentile 2.0, worst 86.0 (3.2 %)
- state: saved yes (20 bytes), restored into a new copy yes; two fresh copies sound: identical; fresh against restored: identical
- a changed setting (Delay: 1.000 to 0.100) travels in the saved state (read back 0.100 in a new copy)
- export mode: ok, peak -1.4 dB; against the real-time render: identical
- switched the running plug-in to 96 kHz and 32 frames: ok, peak -1.4 dB, average 0.14 % of the block

### AGain VST3 (Steinberg Media Technologies, effect) [arm64]

- loaded in 7 ms; audio in 2 ch, out 2 ch, note inputs 1; latency 0 samples
- parameters: 3 (2 can be automated); first: Gain = 0.00 dB, VuPPM = 0.0000, Bypass = Off
- sound: audio run through, peak -1.4 dB, 1500 blocks of 128 frames at 48000 Hz, 0 failed
- time per block: average 0.8 microseconds (0.03 % of the block), 99th percentile 1.1, worst 47.2 (1.8 %)
- state: saved yes (281 bytes), restored into a new copy yes; two fresh copies sound: identical; fresh against restored: identical
- a changed setting (Gain: 1.000 to 0.100) travels in the saved state (read back 0.100 in a new copy)
- export mode: ok, peak -1.4 dB; against the real-time render: identical
- switched the running plug-in to 96 kHz and 32 frames: ok, peak -21.4 dB, average 0.08 % of the block

### mda JX10 (mda, instrument) [arm64]

- loaded in 5 ms; audio in 0 ch, out 2 ch, note inputs 1; latency 0 samples
- parameters: 31 (24 can be automated); first: Factory Presets = 5th Sweep Pad %, OSC Mix = 100.00 %, OSC Tune = 37.00 %, OSC Fine = -50.00 %, Glide = Poly-Legato, Gld Rate = 32.00 %
- sound: notes played, peak -5.3 dB, 1500 blocks of 128 frames at 48000 Hz, 0 failed
- time per block: average 3.5 microseconds (0.13 % of the block), 99th percentile 12.6, worst 89.5 (3.4 %)
- state: saved yes (8088 bytes), restored into a new copy yes; two fresh copies sound: identical; fresh against restored: identical
- a changed setting (OSC Mix: 1.000 to 0.100) travels in the saved state (read back 0.100 in a new copy)
- export mode: ok, peak -5.3 dB; against the real-time render: identical
- switched the running plug-in to 96 kHz and 32 frames: ok, peak -3.2 dB, average 0.44 % of the block

### mda JX10 (mda, instrument) [arm64]

- loaded in 3 ms; audio in 0 ch, out 2 ch, note inputs 1; latency 0 samples
- parameters: 31 (24 can be automated); first: Factory Presets = 5th Sweep Pad %, OSC Mix = 100.00 %, OSC Tune = 37.00 %, OSC Fine = -50.00 %, Glide = Poly-Legato, Gld Rate = 32.00 %
- sound: notes played, peak -3.7 dB, 500 blocks of 128 frames at 16000 Hz, 0 failed
- time per block: average 5.5 microseconds (0.07 % of the block), 99th percentile 15.1, worst 36.2 (0.5 %)
- state: saved yes (8088 bytes), restored into a new copy yes; two fresh copies sound: identical; fresh against restored: identical
- a changed setting (OSC Mix: 1.000 to 0.100) travels in the saved state (read back 0.100 in a new copy)
- export mode: ok, peak -3.7 dB; against the real-time render: identical
- switched the running plug-in to 96 kHz and 32 frames: ok, peak -0.3 dB, average 0.71 % of the block

### Note Expression Synth With UI (Steinberg Media Technologies, instrument) [arm64]

- loaded in 5 ms; audio in 0 ch, out 2 ch, note inputs 1; latency 0 samples
- parameters: 18 (16 can be automated); first: Master Volume = 50.0 %, Master Tuning = 0 cent, Velocity To Level = 100.0 %, Release Time = 0.005 sec, Noise Volume = 10.0 %, Sinus Volume = 100.0 %
- sound: notes played, peak -14.9 dB, 1500 blocks of 128 frames at 48000 Hz, 0 failed
- time per block: average 3.5 microseconds (0.13 % of the block), 99th percentile 20.2, worst 204.5 (7.7 %)
- state: saved yes (129 bytes), restored into a new copy yes; two fresh copies sound: differs (largest difference -41.4 dB); fresh against restored: differs (largest difference -42.5 dB)
- a changed setting (Master Volume: 0.500 to 0.100) travels in the saved state (read back 0.100 in a new copy)
- export mode: ok, peak -15.0 dB; against the real-time render: differs (largest difference -42.2 dB)
- switched the running plug-in to 96 kHz and 32 frames: ok, peak -70.8 dB, average 0.46 % of the block

### Surge XT (Surge Synth Team, instrument) [x86_64 arm64]

- loaded in 90 ms; audio in 2 ch, out 2 ch, note inputs 1; latency 0 samples
- parameters: 2855 (774 can be automated); first: M1: - = 0.000000, M2: - = 0.000000, M3: - = 0.000000, M4: - = 0.000000, M5: - = 0.000000, M6: - = 0.000000
- sound: notes played, peak -4.8 dB, 1500 blocks of 128 frames at 48000 Hz, 0 failed
- time per block: average 30.7 microseconds (1.15 % of the block), 99th percentile 65.5, worst 5216.5 (195.6 %)
- state: saved yes (50251 bytes), restored into a new copy yes; two fresh copies sound: differs (largest difference -7.5 dB); fresh against restored: differs (largest difference -7.7 dB)
- a changed setting (M1: -: 0.000 to 0.900) travels in the saved state (read back 0.900 in a new copy)
- export mode: ok, peak -5.5 dB; against the real-time render: differs (largest difference -7.8 dB)
- switched the running plug-in to 96 kHz and 32 frames: ok, peak -10.5 dB, average 1.56 % of the block

### Surge XT (Surge Synth Team, instrument) [x86_64 arm64]

- loaded in 68 ms; audio in 2 ch, out 2 ch, note inputs 1; latency 0 samples
- parameters: 2855 (774 can be automated); first: M1: - = 0.000000, M2: - = 0.000000, M3: - = 0.000000, M4: - = 0.000000, M5: - = 0.000000, M6: - = 0.000000
- sound: notes played, peak -5.5 dB, 500 blocks of 128 frames at 16000 Hz, 0 failed
- time per block: average 55.5 microseconds (0.69 % of the block), 99th percentile 429.1, worst 8631.9 (107.9 %)
- state: saved yes (50251 bytes), restored into a new copy yes; two fresh copies sound: differs (largest difference -7.9 dB); fresh against restored: differs (largest difference -8.0 dB)
- a changed setting (M1: -: 0.000 to 0.900) travels in the saved state (read back 0.900 in a new copy)
- export mode: ok, peak -6.2 dB; against the real-time render: differs (largest difference -7.0 dB)
- switched the running plug-in to 96 kHz and 32 frames: ok, peak -10.5 dB, average 2.09 % of the block

### Surge XT Effects (Surge Synth Team, effect) [x86_64 arm64]

- loaded in 56 ms; audio in 2 ch, out 2 ch, note inputs 0; latency 0 samples
- parameters: 14 (14 can be automated); first: FX Parameter 0 = -, FX Parameter 1 = -, FX Parameter 2 = -, FX Parameter 3 = -, FX Parameter 4 = -, FX Parameter 5 = -
- sound: audio run through, peak -2.6 dB, 1500 blocks of 128 frames at 48000 Hz, 0 failed
- time per block: average 5.0 microseconds (0.19 % of the block), 99th percentile 12.2, worst 42.6 (1.6 %)
- state: saved yes (1044 bytes), restored into a new copy yes; two fresh copies sound: identical; fresh against restored: identical
- a changed setting (FX Parameter 0: 0.500 to 0.100) travels in the saved state (read back 0.100 in a new copy)
- export mode: ok, peak -2.6 dB; against the real-time render: identical
- switched the running plug-in to 96 kHz and 32 frames: ok, peak -5.4 dB, average 0.59 % of the block

## Test C: the test app on the build machine

```
﻿AudioLab VST3 test 0.8 (tasks NM1, NB-N1, NL4, NL5, NL7 and NL8). Report file: paste all of it back.
[machine] VirtualMac2,1, Apple M1 (Virtual), macOS Version 26.7.2 (Build 25G332), this app runs as arm64
[device] Apple Virtual Sound Device (Apple Inc., built-in): out 2 ch, in 0 ch, now 48000 Hz, rates offered: 48000 96000, rate can be set: yes, buffer 512 (range 15 to 4096), volume the computer can set: yes (main), format on the wire: 32-bit float, 2 ch, 48000 Hz, mixable (2 formats offered), exclusive use can be taken: yes, DEFAULT OUTPUT
[device] Apple Virtual Sound Device (Apple Inc., built-in): out 0 ch, in 2 ch, now 48000 Hz, rates offered: 48000 96000, rate can be set: yes, buffer 512 (range 15 to 4096), volume the computer can set: no, format on the wire:  (0 formats offered), exclusive use can be taken: yes
[device] BlackHole 2ch (Existential Audio Inc., virtual): out 2 ch, in 2 ch, now 48000 Hz, rates offered: 8000 16000 24000 44100 48000 88200 96000 176400 192000 352800 384000 705600 768000, rate can be set: yes, buffer 512 (range 15 to 4096), volume the computer can set: yes (main), format on the wire: 32-bit float, 2 ch, 48000 Hz, mixable (13 formats offered), exclusive use can be taken: yes
[device] Null Audio Device (Apple Inc., virtual): out 2 ch, in 2 ch, now 44100 Hz, rates offered: 44100 48000, rate can be set: yes, buffer 512 (range 14 to 4096), volume the computer can set: yes (main), format on the wire: 32-bit float, 2 ch, 44100 Hz, mixable (2 formats offered), exclusive use can be taken: yes
[output] Apple Virtual Sound Device: opened, 48000 Hz, buffer 512 frames (10.67 ms), device latency 0 + safety 100 + stream 0 frames; why: the system's default output, at the start; nothing chosen yet, so the app follows the default until you choose an output in the Output menu
[format] Apple Virtual Sound Device: on the wire 32-bit float, 2 ch, 48000 Hz, mixable (2 formats offered); the deepest integer format at 48000 Hz: none (float only, or not offered)
[scan] found Surge XT Effects by Surge Synth Team, effect, version 1.3.4 [x86_64 arm64] in Surge XT Effects.vst3 (0.10 s)
[scan] found Surge XT by Surge Synth Team, instrument, version 1.3.4 [x86_64 arm64] in Surge XT.vst3 (0.09 s)
[scan] found AL Strict Synth by AudioLab test, instrument, version 0.8.0 [arm64] in al-strict-synth.vst3 (0.02 s)
[scan] found AL Strict Synth 33 outs by AudioLab test, instrument, version 0.8.0 [arm64] in al-strict-synth.vst3 (0.02 s)
[scan] found mda Ambience by mda, effect, version 3.8.1.0 [arm64] in mda-vst3.vst3 (0.07 s)
[scan] found mda Bandisto by mda, effect, version 3.8.1.0 [arm64] in mda-vst3.vst3 (0.07 s)
[scan] found mda BeatBox by mda, effect, version 3.8.1.0 [arm64] in mda-vst3.vst3 (0.07 s)
[scan] found mda Combo by mda, effect, version 3.8.1.0 [arm64] in mda-vst3.vst3 (0.07 s)
[scan] found mda DeEsser by mda, effect, version 3.8.1.0 [arm64] in mda-vst3.vst3 (0.07 s)
[scan] found mda Degrade by mda, effect, version 3.8.1.0 [arm64] in mda-vst3.vst3 (0.07 s)
[scan] found mda Delay by mda, effect, version 3.8.1.0 [arm64] in mda-vst3.vst3 (0.07 s)
[scan] found mda Detune by mda, effect, version 3.8.1.0 [arm64] in mda-vst3.vst3 (0.07 s)
[scan] found mda Dither by mda, effect, version 3.8.1.0 [arm64] in mda-vst3.vst3 (0.07 s)
[scan] found mda DubDelay by mda, effect, version 3.8.1.0 [arm64] in mda-vst3.vst3 (0.07 s)
[scan] found mda DX10 by mda, instrument, version 3.8.1.0 [arm64] in mda-vst3.vst3 (0.07 s)
[scan] found mda Dynamics by mda, effect, version 3.8.1.0 [arm64] in mda-vst3.vst3 (0.07 s)
[scan] found mda EPiano by mda, instrument, version 3.8.1.0 [arm64] in mda-vst3.vst3 (0.07 s)
[scan] found mda Image by mda, effect, version 3.8.1.0 [arm64] in mda-vst3.vst3 (0.07 s)
[scan] found mda JX10 by mda, instrument, version 3.8.1.0 [arm64] in mda-vst3.vst3 (0.07 s)
[scan] found mda Leslie by mda, effect, version 3.8.1.0 [arm64] in mda-vst3.vst3 (0.07 s)
[scan] found mda Limiter by mda, effect, version 3.8.1.0 [arm64] in mda-vst3.vst3 (0.07 s)
[scan] found mda Loudness by mda, effect, version 3.8.1.0 [arm64] in mda-vst3.vst3 (0.07 s)
[scan] found mda MultiBand by mda, effect, version 3.8.1.0 [arm64] in mda-vst3.vst3 (0.07 s)
[scan] found mda Overdrive by mda, effect, version 3.8.1.0 [arm64] in mda-vst3.vst3 (0.07 s)
[scan] found mda Piano by mda, instrument, version 3.8.1.0 [arm64] in mda-vst3.vst3 (0.07 s)
[scan] found mda RePsycho! by mda, effect, version 3.8.1.0 [arm64] in mda-vst3.vst3 (0.07 s)
[scan] found mda RezFilter by mda, effect, version 3.8.1.0 [arm64] in mda-vst3.vst3 (0.07 s)
[scan] found mda RingMod by mda, effect, version 3.8.1.0 [arm64] in mda-vst3.vst3 (0.07 s)
[scan] found mda Round Panner by mda, effect, version 3.8.1.0 [arm64] in mda-vst3.vst3 (0.07 s)
[scan] found mda Shepard by mda, effect, version 3.8.1.0 [arm64] in mda-vst3.vst3 (0.07 s)
[scan] found mda Splitter by mda, effect, version 3.8.1.0 [arm64] in mda-vst3.vst3 (0.07 s)
[scan] found mda Stereo Simulator by mda, effect, version 3.8.1.0 [arm64] in mda-vst3.vst3 (0.07 s)
[scan] found mda Sub-Bass Synthesizer by mda, effect, version 3.8.1.0 [arm64] in mda-vst3.vst3 (0.07 s)
[scan] found mda TalkBox by mda, effect, version 3.8.1.0 [arm64] in mda-vst3.vst3 (0.07 s)
[scan] found mda TestTone by mda, effect, version 3.8.1.0 [arm64] in mda-vst3.vst3 (0.07 s)
[scan] found mda Thru-Zero Flanger by mda, effect, version 3.8.1.0 [arm64] in mda-vst3.vst3 (0.07 s)
[scan] found mda Tracker by mda, effect, version 3.8.1.0 [arm64] in mda-vst3.vst3 (0.07 s)
[scan] found mda SpecMeter by mda, effect, version 3.8.1.0 [arm64] in mda-vst3.vst3 (0.07 s)
[scan] done: 4 bundle(s) in /Users/runner/Library/Audio/Plug-Ins/VST3, /Library/Audio/Plug-Ins/VST3, /Network/Library/Audio/Plug-Ins/VST3; 4 could be read, 0 could not; 38 plug-in(s). The app itself was never at risk: every bundle was opened in a separate process.
[clap] 2 CLAP bundle(s) in /Users/runner/Library/Audio/Plug-Ins/CLAP, /Library/Audio/Plug-Ins/CLAP (listed, not loaded): 2 for Apple Silicon, 0 Intel-only
[clap] names: Surge XT Effects; Surge XT
[au] 2 Audio Unit bundle(s) in /Users/runner/Library/Audio/Plug-Ins/Components, /Library/Audio/Plug-Ins/Components (listed, not loaded): 2 for Apple Silicon, 0 Intel-only; kinds: 1 effect, 1 instrument
[au] names: Surge Synth Team: Surge XT Effects (effect); Surge Synth Team: Surge XT (instrument)
[selftest] search "SÜRGE XT": 2 of 38, first: Surge XT
[selftest] search "instrument": 7 of 38, first: Surge XT
[selftest] search "effect": 31 of 38, first: mda Ambience
[selftest] search "zzzz-nothing": 0 of 38, first: (none)
[selftest] grouped by maker: 3 group heading(s), 41 rows
[load] Surge XT loaded in 65 ms: instrument, audio in 2 ch, out 2 ch, note inputs 1, 2855 parameters (first: M1: -, M2: -, M3: -, M4: -, M5: -, M6: -, M7: -, M8: -), state saved (50251 bytes), latency 0 samples (0.00 ms at 48000 Hz)
[diag] Surge XT: plug-in: Surge XT by Surge Synth Team, version 1.3.4, built with VST 3.7.8, categories Instrument|Synth
[diag] Surge XT: component initialize = ok
[diag] Surge XT: controller: a separate object, initialize = ok
[diag] Surge XT: processor and controller connected (IConnectionPoint): processor = ok, controller = ok; messages from other threads: delivered (as JUCE's host)
[diag] Surge XT: controller->setComponentState(the processor's state, 50239 bytes) = not implemented
[diag] Surge XT: parameters: 2855; messages so far: 1 to the processor, 0 to the controller, 0 from other threads, 0 dropped
[diag] Surge XT: buses the plug-in offers: [audio in 0 "Sidechain": aux, 2 ch, default active] [audio out 0 "Output": main, 2 ch, default active] [audio out 1 "Scene A": main, 2 ch, default inactive] [audio out 2 "Scene B": main, 2 ch, default inactive] [event in 0 "MIDI Input": main, 16 ch, default active]
[diag] Surge XT: setupProcessing(realtime, 32-bit float, 48000 Hz, largest block 4096) = ok
[diag] Surge XT: arrangements the plug-in prefers: in 0: stereo out 0: stereo out 1: stereo out 2: stereo
[diag] Surge XT: setBusArrangements( in 0: stereo out 0: stereo out 1: stereo out 2: stereo ) = ok; the plug-in now has in 0: stereo out 0: stereo out 1: stereo out 2: stereo
[diag] Surge XT: activateBus: audio in 0 off = ok; audio out 0 on = ok; audio out 1 off = ok; audio out 2 off = ok; event in 0 on = ok;
[diag] Surge XT: setActive(true) = ok
[diag] Surge XT: setProcessing(true) = ok
[diag] Surge XT: process data: in bus 0 2 ch; out bus 0 2 ch; out bus 1 2 ch; out bus 2 2 ch; event list, parameter changes in and out, process context (tempo 120, 4/4, playing, system time, bar position), note ids -1
[presets] Surge XT: 0 reachable through VST3 (no program list, no .vstpreset file): to rule out an empty start patch, choose a preset in its own window, then play the pattern
[selftest] load ok
[window] Surge XT: its own window is open, 913 x 569
[pattern] test pattern on
[selftest] five seconds of the pattern played
[param] Surge XT: first move from its window: A Filter Configuration = 0.57 (Dual 2)
[selftest] 24 drags in the plug-in's window: 3 parameter move(s) reached the host
[pattern] test pattern off. [audio] plug-in Surge XT: 1186 blocks, average 236.3 microseconds per block (2.21 % of the block), worst 8283.3 (77.7 %), block lasts 10667 microseconds, failed blocks 0, overloads reported by the device 1, device callbacks 1475, frames per callback 512 to 512, peak level 0.188
[audio] the slowest blocks (at least 100 ms apart) and what happened in the 100 ms before each, and during it:
[audio]   1) 8283.3 microseconds (77.7 % of the block) at 22:11:30.325: a plug-in was loaded (54 ms before)
[audio]   2) 3683.3 microseconds (34.5 % of the block) at 22:11:41.016: nothing happened in the window, the plug-in's controls or the devices (the plug-in's own work, or the system)
[audio]   3) 2446.0 microseconds (22.9 % of the block) at 22:11:30.442: nothing happened in the window, the plug-in's controls or the devices (the plug-in's own work, or the system)
[param] Surge XT: 3 moves from its window (gestures begun 13, ended 13), last: A Filter Configuration = 0.57 (Dual 2); it asked the host to restart 1 time(s), 1 of them because all its values changed
[param] Surge XT: no value changed without telling the host (polled its 2855 values every 200 ms while its window was open: 59 polls, 0.44 ms on average, worst 1.34 ms)
[notes] Surge XT: 47 notes sent (47 from the test pattern, 0 from the keys), output peak 0.188: it sounded
[level] Surge XT: its own output stayed at or below 0 dBFS (peak -8.5 dBFS); the app's safety limiter engaged 0 time(s); the app's output peak 0.188 (-14.5 dBFS), never past full scale
[diag] Surge XT: 1186 blocks processed; the plug-in's own main output held sound in 1074 of them (peak -8.5 dB, measured before this app copies or halves it); other output buses held sound in 0 (peak silent (0)); blocks with a silence flag set by the plug-in: 0 of 1186 (on any of its 3 output buses; on the main bus: 0, 0 of them although the main bus held sound; flags summed over all buses: 0); process() not ok: 0 (last result: ok); notes handed over: 47 on, 46 off, 0 refused by the event list; parameter changes handed over: 3; messages between its two parts: 1 to the processor, 0 to the controller, 0 of them from a thread other than the main thread, 0 dropped
[state] Surge XT: its state is now 51912 bytes (50251 when loaded): a preset or patch was loaded or changed since
[param] Surge XT: 3 moves from its window (gestures begun 13, ended 13), last: A Filter Configuration = 0.57 (Dual 2); it asked the host to restart 1 time(s), 1 of them because all its values changed
[param] Surge XT: no value changed without telling the host (polled its 2855 values every 200 ms while its window was open: 59 polls, 0.44 ms on average, worst 1.34 ms)
[notes] Surge XT: 47 notes sent (47 from the test pattern, 0 from the keys), output peak 0.188: it sounded
[level] Surge XT: its own output stayed at or below 0 dBFS (peak -8.5 dBFS); the app's safety limiter engaged 0 time(s); the app's output peak 0.188 (-14.5 dBFS), never past full scale
[diag] Surge XT: 1187 blocks processed; the plug-in's own main output held sound in 1075 of them (peak -8.5 dB, measured before this app copies or halves it); other output buses held sound in 0 (peak silent (0)); blocks with a silence flag set by the plug-in: 0 of 1187 (on any of its 3 output buses; on the main bus: 0, 0 of them although the main bus held sound; flags summed over all buses: 0); process() not ok: 0 (last result: ok); notes handed over: 47 on, 47 off, 0 refused by the event list; parameter changes handed over: 3; messages between its two parts: 1 to the processor, 0 to the controller, 0 of them from a thread other than the main thread, 0 dropped
[state] Surge XT: its state is now 51912 bytes (50251 when loaded): a preset or patch was loaded or changed since
[probe] Surge XT: loading it again in a separate process and playing it under several host set-ups at 48000 Hz (your sound keeps playing meanwhile)
[probe] Surge XT, the 0.5 host (as JUCE and the SDK's validator): SOUND, peak -4.5 dB; its main output held sound in 188 of 188 blocks, other buses in 0; messages 1 to the processor, 0 to the controller, 0 from other threads, 0 dropped; controller given the state: not implemented
[probe] Surge XT, the 0.4 host (as on your Mac in reports 4 and 5): SOUND, peak -4.5 dB; its main output held sound in 188 of 188 blocks, other buses in 0; messages 1 to the processor, 0 to the controller, 0 from other threads, 0 dropped; controller given the state: not called
[probe] Surge XT, 0.5 without giving the controller the processor's state: SOUND, peak -4.6 dB; its main output held sound in 188 of 188 blocks, other buses in 0; messages 1 to the processor, 0 to the controller, 0 from other threads, 0 dropped; controller given the state: not called
[probe] Surge XT, 0.5 but messages from other threads dropped (the SDK's proxy): SOUND, peak -6.7 dB; its main output held sound in 188 of 188 blocks, other buses in 0; messages 1 to the processor, 0 to the controller, 0 from other threads, 0 dropped; controller given the state: not implemented
[probe] Surge XT, 0.5 but buses set up as in 0.4 (stereo forced, before setupProcessing): SOUND, peak -4.6 dB; its main output held sound in 188 of 188 blocks, other buses in 0; messages 1 to the processor, 0 to the controller, 0 from other threads, 0 dropped; controller given the state: not implemented
[probe] Surge XT, 0.5 with a unique id on every note: SOUND, peak -7.6 dB; its main output held sound in 188 of 188 blocks, other buses in 0; messages 1 to the processor, 0 to the controller, 0 from other threads, 0 dropped; controller given the state: not implemented
[probe] Surge XT, 0.5 with every audio bus active: SOUND, peak -6.2 dB; its main output held sound in 188 of 188 blocks, other buses in 188; messages 1 to the processor, 0 to the controller, 0 from other threads, 0 dropped; controller given the state: not implemented
[probe] Surge XT, 0.5 with the transport stopped: SOUND, peak -4.9 dB; its main output held sound in 188 of 188 blocks, other buses in 0; messages 1 to the processor, 0 to the controller, 0 from other threads, 0 dropped; controller given the state: not implemented
[probe] Surge XT, 0.5 after loading its first factory preset: no factory preset reachable through VST3 (no program list, no .vstpreset file)
[probe] Surge XT, conclusion: it sounds with both hosts here. If it was silent while you played, the difference is elsewhere (its patch, or what it was doing at that moment).
[selftest] end
[audio] plug-in Surge XT: 2350 blocks, average 186.3 microseconds per block (1.75 % of the block), worst 8283.3 (77.7 %), block lasts 10667 microseconds, failed blocks 0, overloads reported by the device 1, device callbacks 2639, frames per callback 512 to 512, peak level 0.188
[audio] the slowest blocks (at least 100 ms apart) and what happened in the 100 ms before each, and during it:
[audio]   1) 8283.3 microseconds (77.7 % of the block) at 22:11:30.325: a plug-in was loaded (54 ms before)
[audio]   2) 3683.3 microseconds (34.5 % of the block) at 22:11:41.016: nothing happened in the window, the plug-in's controls or the devices (the plug-in's own work, or the system)
[audio]   3) 2446.0 microseconds (22.9 % of the block) at 22:11:30.442: nothing happened in the window, the plug-in's controls or the devices (the plug-in's own work, or the system)
[param] Surge XT: 3 moves from its window (gestures begun 13, ended 13), last: A Filter Configuration = 0.57 (Dual 2); it asked the host to restart 1 time(s), 1 of them because all its values changed
[param] Surge XT: no value changed without telling the host (polled its 2855 values every 200 ms while its window was open: 120 polls, 0.50 ms on average, worst 1.34 ms)
[notes] Surge XT: 47 notes sent (47 from the test pattern, 0 from the keys), output peak 0.188: it sounded
[level] Surge XT: its own output stayed at or below 0 dBFS (peak -8.5 dBFS); the app's safety limiter engaged 0 time(s); the app's output peak 0.188 (-14.5 dBFS), never past full scale
[diag] Surge XT: 2350 blocks processed; the plug-in's own main output held sound in 1332 of them (peak -8.5 dB, measured before this app copies or halves it); other output buses held sound in 0 (peak silent (0)); blocks with a silence flag set by the plug-in: 0 of 2350 (on any of its 3 output buses; on the main bus: 0, 0 of them although the main bus held sound; flags summed over all buses: 0); process() not ok: 0 (last result: ok); notes handed over: 47 on, 47 off, 0 refused by the event list; parameter changes handed over: 3; messages between its two parts: 1 to the processor, 0 to the controller, 0 of them from a thread other than the main thread, 0 dropped
[state] Surge XT: its state is now 51912 bytes (50251 when loaded): a preset or patch was loaded or changed since
```

