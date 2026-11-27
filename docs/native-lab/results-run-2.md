# Native lab results

```
arch: arm64
ProductName:		macOS
ProductVersion:		15.8.2
BuildVersion:		24H232
Apple M1 (Virtual)
VirtualMac2,1
Apple clang version 17.0.0 (clang-1700.0.13.5)
Target: arm64-apple-darwin24.6.0
cmake version 4.5.0
```

## Test A: one effect, native against the web engine

```
plain   own maths: identical, all 48000 samples | web numbers: identical, all 48000 samples | pow/exp results same as the browser: yes | speed 3929 x real time
filter  own maths: identical, all 48000 samples | web numbers: identical, all 48000 samples | pow/exp results same as the browser: yes | speed 3919 x real time
dither  own maths: identical, all 48000 samples | web numbers: identical, all 48000 samples | pow/exp results same as the browser: yes | speed 2438 x real time
--- control: the same program built with fused multiply-add allowed ---
plain   own maths: identical, all 48000 samples | web numbers: identical, all 48000 samples | pow/exp results same as the browser: yes | speed 3990 x real time
filter  own maths: identical, all 48000 samples | web numbers: identical, all 48000 samples | pow/exp results same as the browser: yes | speed 4574 x real time
dither  own maths: identical, all 48000 samples | web numbers: identical, all 48000 samples | pow/exp results same as the browser: yes | speed 3214 x real time
```

### Devices of the build machine as it comes

- **Apple Virtual Sound Device** (built-in): out 0 ch, in 2 ch, 48000 Hz now; rates offered: 48000, 96000; rate can be set: yes; buffer 512 (range 15 to 4096, can be set: yes); volume the computer can set: no; on the wire: ?; exclusive use can be taken: yes
- **Apple Virtual Sound Device** (built-in, default output): out 2 ch, in 0 ch, 48000 Hz now; rates offered: 48000, 96000; rate can be set: yes; buffer 512 (range 15 to 4096, can be set: yes); volume the computer can set: yes (main); on the wire: 32-bit float, 2 ch, 48000 Hz, mixable; exclusive use can be taken: yes
- **Null Audio Device** (virtual): out 2 ch, in 2 ch, 44100 Hz now; rates offered: 44100, 48000; rate can be set: yes; buffer 512 (range 14 to 4096, can be set: yes); volume the computer can set: yes (main); on the wire: 32-bit float, 2 ch, 44100 Hz, mixable; exclusive use can be taken: yes

### Devices after adding the virtual device BlackHole

- **Apple Virtual Sound Device** (built-in): out 0 ch, in 2 ch, 48000 Hz now; rates offered: 48000, 96000; rate can be set: yes; buffer 512 (range 15 to 4096, can be set: yes); volume the computer can set: no; on the wire: ?; exclusive use can be taken: yes
- **Apple Virtual Sound Device** (built-in, default output): out 2 ch, in 0 ch, 48000 Hz now; rates offered: 48000, 96000; rate can be set: yes; buffer 512 (range 15 to 4096, can be set: yes); volume the computer can set: yes (main); on the wire: 32-bit float, 2 ch, 48000 Hz, mixable; exclusive use can be taken: yes
- **BlackHole 2ch** (virtual): out 2 ch, in 2 ch, 48000 Hz now; rates offered: 8000, 16000, 24000, 44100, 48000, 88200, 96000, 176400, 192000, 352800, 384000, 705600, 768000; rate can be set: yes; buffer 512 (range 15 to 4096, can be set: yes); volume the computer can set: yes (main); on the wire: 32-bit float, 2 ch, 48000 Hz, mixable; exclusive use can be taken: yes
- **Null Audio Device** (virtual): out 2 ch, in 2 ch, 44100 Hz now; rates offered: 44100, 48000; rate can be set: yes; buffer 512 (range 14 to 4096, can be set: yes); volume the computer can set: yes (main); on the wire: 32-bit float, 2 ch, 44100 Hz, mixable; exclusive use can be taken: yes

### Opening the default output

- opened **Apple Virtual Sound Device** through Core Audio and played 1.0 s: 832 callbacks, 64 to 64 frames per callback, 6 overloads, render 0.7 microseconds on average
- buffer: asked for 64 frames, device now runs 64 (accepted)
- sample rate: asked for 96000 Hz, device then ran 96000 Hz (switched); put back to 48000 Hz (ok)
- exclusive use: taken; given back: yes

### Opening BlackHole

- opened **BlackHole 2ch** through Core Audio and played 1.0 s: 772 callbacks, 64 to 64 frames per callback, 0 overloads, render 0.7 microseconds on average
- buffer: asked for 64 frames, device now runs 64 (accepted)
- sample rate: asked for 96000 Hz, device then ran 96000 Hz (switched); put back to 48000 Hz (ok)
- exclusive use: taken; given back: yes

## Test B: command line VST3 host

Scan: 6 bundles, 5 read, 1 failed, 40 plug-ins. The host stayed alive: yes.
- Surge XT Effects.vst3 [x86_64 arm64], 0.04 s: Surge XT Effects (effect)
- Surge XT.vst3 [x86_64 arm64], 0.04 s: Surge XT (instrument)
- adelay.vst3 [arm64]: FAILED, crashed while loading (signal 6)
- again.vst3 [arm64], 0.03 s: AGain VST3 (effect), AGain SideChain VST3 (effect)
- mda-vst3.vst3 [arm64], 0.01 s: mda Ambience (effect), mda Bandisto (effect), mda BeatBox (effect), mda Combo (effect), mda DeEsser (effect), mda Degrade (effect), mda Delay (effect), mda Detune (effect) and 26 more
- note-expression-synth.vst3 [arm64], 0.04 s: Note Expression Synth With UI (instrument), Note Expression Synth (instrument)

### ADelay (Steinberg Media Technologies, effect) [arm64]

- loaded in 13 ms; audio in 2 ch, out 2 ch, note inputs 0; latency 0 samples
- parameters: 2 (2 can be automated); first: Bypass = Off, Delay = 1.0000 sec
- sound: audio run through, peak -1.4 dB, 1500 blocks of 128 frames at 48000 Hz, 0 failed
- time per block: average 0.4 microseconds (0.01 % of the block), 99th percentile 0.5, worst 16.8 (0.6 %)
- state: saved yes (20 bytes), restored into a new copy yes; two fresh copies sound: identical; fresh against restored: identical
- a changed setting (Delay: 1.000 to 0.100) travels in the saved state (read back 0.100 in a new copy)
- export mode: ok, peak -1.4 dB; against the real-time render: identical
- switched the running plug-in to 96 kHz and 32 frames: ok, peak -1.4 dB, average 0.03 % of the block

### AGain VST3 (Steinberg Media Technologies, effect) [arm64]

- loaded in 4 ms; audio in 2 ch, out 2 ch, note inputs 1; latency 0 samples
- parameters: 3 (2 can be automated); first: Gain = 0.00 dB, VuPPM = 0.0000, Bypass = Off
- sound: audio run through, peak -1.4 dB, 1500 blocks of 128 frames at 48000 Hz, 0 failed
- time per block: average 0.5 microseconds (0.02 % of the block), 99th percentile 0.9, worst 18.5 (0.7 %)
- state: saved yes (281 bytes), restored into a new copy yes; two fresh copies sound: identical; fresh against restored: identical
- a changed setting (Gain: 1.000 to 0.100) travels in the saved state (read back 0.100 in a new copy)
- export mode: ok, peak -1.4 dB; against the real-time render: identical
- switched the running plug-in to 96 kHz and 32 frames: ok, peak -21.4 dB, average 0.05 % of the block

### mda JX10 (mda, instrument) [arm64]

- loaded in 28 ms; audio in 0 ch, out 2 ch, note inputs 1; latency 0 samples
- parameters: 31 (24 can be automated); first: Factory Presets = 5th Sweep Pad %, OSC Mix = 0.00 %, OSC Tune = 0.00 %, OSC Fine = -100.00 %, Glide = Poly, Gld Rate = 0.00 %
- sound: notes played, peak -5.3 dB, 1500 blocks of 128 frames at 48000 Hz, 0 failed
- time per block: average 2.7 microseconds (0.10 % of the block), 99th percentile 4.2, worst 17.4 (0.7 %)
- state: saved yes (8088 bytes), restored into a new copy yes; two fresh copies sound: identical; fresh against restored: identical
- a changed setting (OSC Mix: 0.000 to 0.900) travels in the saved state (read back 0.900 in a new copy)
- export mode: ok, peak -5.3 dB; against the real-time render: identical
- switched the running plug-in to 96 kHz and 32 frames: ok, peak -5.0 dB, average 0.30 % of the block

### Note Expression Synth With UI (Steinberg Media Technologies, instrument) [arm64]

- loaded in 3 ms; audio in 0 ch, out 2 ch, note inputs 1; latency 0 samples
- parameters: 18 (16 can be automated); first: Master Volume = 80.0 %, Master Tuning = 0 cent, Velocity To Level = 30.0 %, Release Time = 0.025 sec, Noise Volume = 0.0 %, Sinus Volume = 80.0 %
- sound: notes played, peak -14.9 dB, 1500 blocks of 128 frames at 48000 Hz, 0 failed
- time per block: average 2.3 microseconds (0.09 % of the block), 99th percentile 4.1, worst 18.3 (0.7 %)
- state: saved yes (129 bytes), restored into a new copy yes; two fresh copies sound: differs (largest difference -41.4 dB); fresh against restored: differs (largest difference -42.5 dB)
- a changed setting (Master Volume: 0.800 to 0.100) travels in the saved state (read back 0.100 in a new copy)
- export mode: ok, peak -15.0 dB; against the real-time render: differs (largest difference -42.2 dB)
- switched the running plug-in to 96 kHz and 32 frames: ok, peak -70.8 dB, average 0.14 % of the block

### Surge XT (Surge Synth Team, instrument) [x86_64 arm64]

- loaded in 44 ms; audio in 2 ch, out 2 ch, note inputs 1; latency 0 samples
- parameters: 2855 (774 can be automated); first: M1: - = 0.000000, M2: - = 0.000000, M3: - = 0.000000, M4: - = 0.000000, M5: - = 0.000000, M6: - = 0.000000
- sound: notes played, peak -6.1 dB, 1500 blocks of 128 frames at 48000 Hz, 0 failed
- time per block: average 19.4 microseconds (0.73 % of the block), 99th percentile 27.2, worst 4387.5 (164.5 %)
- state: saved yes (50251 bytes), restored into a new copy yes; two fresh copies sound: differs (largest difference -7.6 dB); fresh against restored: differs (largest difference -7.7 dB)
- a changed setting (M1: -: 0.000 to 0.900) travels in the saved state (read back 0.900 in a new copy)
- export mode: ok, peak -7.1 dB; against the real-time render: differs (largest difference -7.5 dB)
- switched the running plug-in to 96 kHz and 32 frames: ok, peak -10.5 dB, average 1.13 % of the block

### Surge XT Effects (Surge Synth Team, effect) [x86_64 arm64]

- loaded in 25 ms; audio in 2 ch, out 2 ch, note inputs 0; latency 0 samples
- parameters: 14 (14 can be automated); first: FX Parameter 0 = -, FX Parameter 1 = -, FX Parameter 2 = -, FX Parameter 3 = -, FX Parameter 4 = -, FX Parameter 5 = -
- sound: audio run through, peak -2.6 dB, 1500 blocks of 128 frames at 48000 Hz, 0 failed
- time per block: average 4.2 microseconds (0.16 % of the block), 99th percentile 5.4, worst 79.5 (3.0 %)
- state: saved yes (1044 bytes), restored into a new copy yes; two fresh copies sound: identical; fresh against restored: identical
- a changed setting (FX Parameter 0: 0.500 to 0.100) travels in the saved state (read back 0.100 in a new copy)
- export mode: ok, peak -2.6 dB; against the real-time render: identical
- switched the running plug-in to 96 kHz and 32 frames: ok, peak -5.4 dB, average 0.36 % of the block

## Test C: the test app on the build machine

```
AudioLab VST3 test 0.1 (task NM1). Report file: paste all of it back.
[machine] VirtualMac2,1, Apple M1 (Virtual), macOS Version 15.8.2 (Build 24H232), this app runs as arm64
[device] Apple Virtual Sound Device (Apple Inc., built-in): out 0 ch, in 2 ch, now 48000 Hz, rates offered: 48000 96000, rate can be set: yes, buffer 512 (range 15 to 4096), volume the computer can set: no, format on the wire:  (0 formats offered), exclusive use can be taken: yes
[device] Apple Virtual Sound Device (Apple Inc., built-in): out 2 ch, in 0 ch, now 48000 Hz, rates offered: 48000 96000, rate can be set: yes, buffer 512 (range 15 to 4096), volume the computer can set: yes (main), format on the wire: 32-bit float, 2 ch, 48000 Hz, mixable (2 formats offered), exclusive use can be taken: yes, DEFAULT OUTPUT
[device] BlackHole 2ch (Existential Audio Inc., virtual): out 2 ch, in 2 ch, now 48000 Hz, rates offered: 8000 16000 24000 44100 48000 88200 96000 176400 192000 352800 384000 705600 768000, rate can be set: yes, buffer 512 (range 15 to 4096), volume the computer can set: yes (main), format on the wire: 32-bit float, 2 ch, 48000 Hz, mixable (13 formats offered), exclusive use can be taken: yes
[device] Null Audio Device (Apple Inc., virtual): out 2 ch, in 2 ch, now 44100 Hz, rates offered: 44100 48000, rate can be set: yes, buffer 512 (range 14 to 4096), volume the computer can set: yes (main), format on the wire: 32-bit float, 2 ch, 44100 Hz, mixable (2 formats offered), exclusive use can be taken: yes
[output] Apple Virtual Sound Device: opened, 48000 Hz, buffer 512 frames (10.67 ms), device latency 0 + safety 100 + stream 0 frames
[scan] found Surge XT Effects by Surge Synth Team, effect, version 1.3.4 [x86_64 arm64] in Surge XT Effects.vst3 (0.03 s)
[scan] found Surge XT by Surge Synth Team, instrument, version 1.3.4 [x86_64 arm64] in Surge XT.vst3 (0.03 s)
[scan] done: 2 bundle(s) in /Users/runner/Library/Audio/Plug-Ins/VST3, /Library/Audio/Plug-Ins/VST3, /Network/Library/Audio/Plug-Ins/VST3; 2 could be read, 0 could not; 2 plug-in(s). The app itself was never at risk: every bundle was opened in a separate process.
[load] Surge XT loaded in 36 ms: instrument, audio in 2 ch, out 2 ch, note inputs 1, 2855 parameters (first: M1: -, M2: -, M3: -, M4: -, M5: -, M6: -, M7: -, M8: -), state saved (50251 bytes), latency 0 samples
[selftest] load ok
[window] Surge XT: its own window is open, 913 x 569
[pattern] test pattern on
[selftest] five seconds of the pattern played
[pattern] test pattern off.[audio] plug-in Surge XT: 1160 blocks, average 115.5 microseconds per block (1.08 % of the block), worst 4362.4 (40.9 %), block lasts 10667 microseconds, failed blocks 0, overloads reported by the device 0, device callbacks 1186, frames per callback 512 to 512, peak level 0.207
[selftest] end

[audio] plug-in Surge XT: 1160 blocks, average 115.5 microseconds per block (1.08 % of the block), worst 4362.4 (40.9 %), block lasts 10667 microseconds, failed blocks 0, overloads reported by the device 0, device callbacks 1186, frames per callback 512 to 512, peak level 0.207
```

