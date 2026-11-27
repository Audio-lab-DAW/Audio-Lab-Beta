# Settings research: DAC and audio interface (task SR3, 27 November 2026)

Research only. Nothing in `index.html` or `desktop/` was changed, no version bump.

The user's words: "Also audiophile equipment and physical equipment, and also software, because we have a DAC, so I want to integrate the DAC correctly with the right audiophile things I need to connect it. So I want a separate DAC option and a separate interface option, but maybe you can split it in two or have it in one and then automatically."

The user's gear: iFi xDSD Gryphon (USB DAC and headphone amp), Zoom AMS-24 (interface), Stax SR-L500 MkII with an SRM-323S driver, M4 Mac mini.

How to read this: "read" means a research helper opened the page on 27 Nov 2026 (through a fetch tool that summarises, so quoted labels should be re-checked before they are printed in the app). "Guess" and "not confirmed" are marked every time. Nothing here was tried on real hardware.

## Summary

1. **AudioLab already has most of the frame** (v0.172): an Audio devices window, a Settings tab "Interface and DAC" with Automatic / DAC mode / Interface mode, device profiles (Gryphon, AMS-24 included), a bit-perfect checklist, a Mac helper (`alvol`) that reads devices, sets hardware volume and sets the device's sample rate. None of it has been seen on the user's Mac with the real devices. **The first job is a hardware check, not new code.**
2. **The weak point of today's design: one mode for one output device.** The user owns both devices at once. The real need is two roles that can be filled by two devices: *Listen through* (Gryphon) and *Record from* (AMS-24). Recommendation: design (b), one page "Audio devices" with two role slots filled automatically and changeable by hand, plus two setups the app switches between by itself: **Listening** (out: Gryphon, large buffer, device rate follows the engine) and **Recording** (in and out: AMS-24, small buffer, one clock).
3. **"Bit-perfect" has a different meaning in a DAW.** A player passes a file's samples through untouched. A DAW calculates new samples in 32-bit float, so there is no file to be identical to. The honest goal for AudioLab is: **one rate everywhere (no conversion), no hidden volume or limiter in the path, enough bit depth at the device, nothing else mixed in, a visible proof of all four.** Call it "Clean path", not bit-perfect. True bit-perfect only applies to the lossless listening player (playing a file at 0 dB with nothing on the master).
4. **What Chromium allows.** The engine can run at the device's rate and Chromium converts only once, at the very end, and only if the rates differ. On the Mac the helper can set the device to the engine's rate, so no conversion happens anywhere (this is an inference from the source code, still to be proven with a test). Exclusive use (hog mode, WASAPI exclusive, ASIO), integer mode and bypassing the Windows mixer are **not possible** without a native audio output. On Windows the shared mixer always stays in the path today.
5. **Safe volume matters more than anything else for this user.** The Gryphon's line out is variable, up to 3.5 V (single-ended); the Stax driver reaches its rated output at 0.1 V. The Gryphon's "Volume Sync" probably lets the Mac (and so AudioLab's DAC volume slider) move the Gryphon's analogue volume (not confirmed). The app must never raise a device's volume by itself, must remember volume per device, and should offer a per-device volume ceiling.
6. **Staged plan:** now (web engine): role slots, signal-path read-out, safe volume, unplug behaviour, lossless audio recording, test tone. Small helper (Mac first): live listeners, bit depth, proof of "no conversion", Windows read-only device info. Native engine (with VST hosting, glass-engine-plan 2.6): exclusive use, integer mode, WASAPI exclusive and ASIO, more than two inputs, drift-corrected two-device recording.

## 0. What AudioLab does today (read in the code and the log)

- **Engine start** (`ensureCtx`): `new AudioContext({latencyHint, sampleRate, renderSizeHint})`. `latencyHint` is the chosen buffer in seconds, or 'balanced' / 'interactive'; "Auto" starts at 256 samples and steps up after dropouts. `sampleRate` only when the user fixed one (`UI.sr`), otherwise the device's rate at start. Output device through `ctx.setSinkId(UI.sink)`.
- **Unplug**: a `devicechange` listener moves to the default output with a toast, and back when the device returns.
- **Input**: `getUserMedia` with echo cancellation, noise suppression and auto gain off (`inCons`), chosen input device (`UI.inDev`), channel choice stereo / 1 / 2, optional monitoring. Audio takes on tracks are still recorded with `MediaRecorder` (compressed); the Voice device records 32-bit float.
- **Audio devices window and "Interface and DAC" tab** (v0.172, log lines 440 to 515): device cards with kind, model, rate, bit depth, channels, volume; mode switch Automatic / DAC / Interface; device profiles `DEVP`; bit-perfect checklist; "Switch the DAC to the engine's sample rate automatically" (`UI.rateFollow`); measured round trip (`rtMeasure`); output pair for devices with more than two outputs.
- **Desktop** (`main.js`, `preload.js`, `native/alvol.swift`, Mac only): `dac.list / get / set` (hardware volume), `dac.info` (every device: connection kind, channels, rate, rates on offer, bit depth, which process holds it exclusively), `dac.rate(uid, hz)`. Permissions for media, speaker selection and MIDI are granted. Windows has no helper.
- **Not verified, per the log**: what `alvol` returns on a real Mac; the Gryphon's and AMS-24's names; whether setting the device rate really stops conversion; the output pair on a real 4-output device; the round trip with a cable. The measured round trip is shown but not applied to audio takes.
- **Worth a check**: the code comment says the larger render block (`renderSizeHint`) works from Chrome 147 and Electron 45. The ship notice read today says it ships in Chrome 153 and was an origin trial in 145 to 151. The app feature-detects it, so nothing breaks; it may simply be inactive in the current app build.

## 1. What "correct" DAC playback means, and what the players do

**The five conditions** (Roon, Audirvana, Tonal, Spotify all list the same things): the app owns the device alone; the device runs at the material's rate; the device's bit depth is at least the material's; no software volume, levelling or DSP; nothing else (system sounds, other apps) mixed in.

| Topic | What the players do (read) |
|---|---|
| Exclusive use | Roon "Exclusive Mode" (on by default, "bypassing the operating system mixer", needed for DSD). JRiver "Open device for exclusive access". Audirvana "Direct and exclusive access", WASAPI, ASIO, Kernel Streaming. Tidal "Exclusive Mode" with "Force Volume". Qobuz Windows "WASAPI (Exclusive mode)" and ASIO. BitPerfect takes hog mode while playing. Spotify added a Windows "Exclusive Mode" in 2026. foobar2000's FAQ says of alternate outputs: "There is NO benefit in terms of audio quality to using these", a useful counterweight. |
| Rate switching | Roon, Audirvana, JRiver switch as part of exclusive use. Swinsian and BitPerfect switch the device rate (and Swinsian the bit depth) per track. **Apple Music on the Mac still does not** (a 2025 Apple forum thread; helper apps LosslessSwitcher and SyncHz exist for macOS 26). Tidal and Qobuz per-track switching: not confirmed. |
| Integer mode (Mac) | Sends the DAC's own integer format instead of 32-bit float. Removed in macOS 10.7, back in 10.9 (JRiver, BitPerfect). Roon: "Enable Integer Mode (CoreAudio only)". It needs hog mode. A forum title reports it failing on macOS Tahoe in Audirvana (not confirmed). |
| Bit depth | Roon "Max Bits Per Sample"; the "interface format" (bits on the cable) versus the "virtual format" (float the apps see). |
| Buffers | Players use large buffers and memory play (Audirvana loads the whole track; BitPerfect 256 MB; HQPlayer "Driver default"). Latency does not matter to a listener. Roon "Resync delay": silence at each new stream so the DAC locks. |
| DSD | Roon "DSD Playback Strategy": Convert to PCM / Native / DoP. macOS cannot send raw DSD, so DoP; native DSD on Windows needs the maker's ASIO driver. |
| MQA | MQA Ltd went into administration April 2023; Lenbrook bought it September 2023; Tidal replaced MQA with FLAC July 2024. Not worth supporting. |
| Volume | Roon "Volume Control Mode": "Use Device Controls" / "DSP Volume" (64-bit, dithered) / "Fixed Volume". JRiver: Application / Internal / System / Disabled, and "Volume Protection" (small steps, back to 20% after 30 minutes of silence). Audirvana: maximum volume limit, alert above 90%. BitPerfect dithers whenever it changes level. |
| Volume limits | Roon "Comfort limits" (soft, can be passed on purpose), "Safety limits" (hard), "Device limits". Forum titles report limits lost on reconnect, so a limit must be applied again on every reconnect. |
| Headroom | Roon "Headroom Management" (-3 dB suggested when DSP is on), a clipping indicator that reacts to a single sample and flashes the signal-path light red. Benchmark's DAC3 keeps 3.5 dB of headroom inside the DAC for peaks between samples. HQPlayer advises a maximum of -2 dBFS when resampling. |
| Signal path | Roon's light: purple = Lossless, blue = Enhanced (processing you asked for), green = High Quality (OS mixer, conversions, DSP volume), yellow = Low Quality (lossy source), red flash = clipping. The clearest idea to borrow. |
| Upsampling, crossfeed, EQ | Audirvana (SoX, r8brain), Roon MUSE, HQPlayer filters. Roon crossfeed presets (Bauer, Chu Moy, Jan Meier). Roon headphone EQ from the open OPRA list. |
| Device profiles | Roon "Device Setup" per zone: exclusive, DSD strategy, volume mode, max rate, max bits, integer mode, buffer options, resync delay, volume limits. |

**What this means for AudioLab**
- Borrow: the signal-path light with plain reasons, per-device setup, volume mode per device, comfort and safety limits, a clipping light that reacts to one sample, rate follows the material.
- Skip: DSD, MQA, memory play, upsampling filters (the Gryphon has its own, see below).
- Translate: in a DAW the "material's rate" is the project's engine rate. "Rate switching" means: the device follows the engine, and the lossless player may restart the engine at a file's rate when nothing else is playing (a later option, a guess that it is wanted).

## 2. The hardware

### iFi xDSD Gryphon (manual and product page read)
- **Inputs**: USB-C, Bluetooth 5.1 (aptX family, LDAC, LHDC, AAC, SBC), S/PDIF (3.5 mm coax and optical), analogue line in (4.4 mm and 3.5 mm). A second USB-C port is for charging only.
- **Outputs**: headphones 3.5 mm S-Balanced (3.5 V max) and 4.4 mm balanced (6.7 V max). The rear jacks are line outputs when the input is digital. **The line out is variable only; the manual describes no fixed level.**
- **Formats**: PCM 44.1 to 768 kHz, DSD64 to DSD512, MQA. 32-bit and the DoP limits: not confirmed on the pages read.
- **Filters** (menu): BP (Bit-Perfect, no digital filter), STD (default, modest ringing), GTO (upsamples to 352.8/384 kHz, no pre-ringing).
- **Analogue extras**: XBass II (Bass / Presence / both), XSpace (wider stage), iEMatch (attenuator for sensitive in-ears).
- **Display**: format, rate, volume, input, effects, battery. LED colour: yellow 44.1/48, cyan 88.2/96, white 176.4 and up. **This is the user's own proof of the rate that arrives.**
- **Volume**: analogue, 0 to 106; limiter Off / 95% / 80% / 60%; soft ramp; "Volume Sync" on by default. A review says it keeps the source's volume and the Gryphon in step. Whether the Mac sees a hardware volume, and the USB name ("iFi (by AMR) HD USB Audio" is a guess): **check on the device.**
- The app cannot read or set any Gryphon menu item over USB (class audio has no such channel). They belong in the profile as **advice text**, not as controls.

### Stax SRM-323S and SR-L500 MkII
- SRM-323S: one RCA input with a parallel out, 100 mV in gives 100 V out (gain 60 dB), 400 V max, 50 kΩ (a forum post quoting Stax). L500 MkII: 101 dB at 100 V, 580 V bias (dealer page).
- **Arithmetic**: 0.1 V at the driver with its knob fully up is about 101 dB. The Gryphon's line out can deliver 35 times that. The Stax knob is the real limit, and no software can see where it stands.
- **How to connect (a guess, general practice, not from iFi or Stax)**: Gryphon rear 3.5 mm single-ended to RCA. Do not use a simple 4.4 mm balanced to RCA cable. Keep XBass, XSpace and iEMatch off. Set the Gryphon to one fixed moderate level, turn its limiter to 60% or 80% as a guard, and use the Stax knob for level. Then lock the volume in AudioLab (see section 5).

### RME ADI-2 DAC and Pro: the reference menu (manuals read)
- Four keys: VOL, I/O, EQ, SETUP. Each output has its own settings: reference level with **Auto Ref Level** (the analogue stage switches in 6 dB steps so the digital volume stays near full), mono, width, polarity, crossfeed 1 to 5, DA filter, volume with **Lock Volume**, loudness, 5-band EQ.
- **State Overview**: one screen with lock, the rate set by the host, channel mode, bit depth, warnings in red.
- **Bit Test**: special WAV files carry a pattern; the display shows "Bit Test 24 bit passed" when the path is exact. No message means not exact. **This is the best proof idea found**: AudioLab can ship its own pattern and check it on a loopback, and an ADI-2 owner can use RME's files.
- Lessons: one status screen; per-output settings; lock volume; proof instead of promise.

### Other DACs (short)
Chord Qutest: fixed 1 / 2 / 3 V line level, no volume, rate shown as colour. Mojo 2: crossfeed, lossless EQ. Topping DX5 II: line out as Preamp (variable) or DAC (fixed), UAC 1/2 switch, 8 filters. FiiO K11: gain, 6 filters, PO/LO output. Benchmark DAC3: 3.5 dB internal headroom, calibrated fixed output. Common pattern: **fixed or variable output, a filter choice, a gain range**. The profile needs one field for each: "volume: hardware / fixed / none".

### Zoom AMS-24 (manual read)
- 2 inputs (combo, gain to +58 dB, Hi-Z on input 1, stereo link), 4 playback channels. Output A (TRS and headphones A) and headphones B. 44.1 to 96 kHz, 24 bit, class compliant; no driver on the Mac, Zoom's driver on Windows (ASIO not stated on the page). Name "ZOOM AMS-24".
- **MUSIC mode**: inputs separate; USB 1/2 to A, USB 3/4 to B. **STREAMING mode**: inputs summed to stereo; USB 1/2 on both.
- **LOOPBACK** switch mixes inputs and playback 1/2 back to the computer (feedback risk if the DAW also monitors). **DIRECT MONITOR** switch: input monitoring without delay. 48V for both inputs.
- Gain, loopback, direct monitor and mode are **hardware switches the computer cannot read**. The app can only explain them and detect the symptoms (for example: the test click comes back with zero cable, so loopback is on).

### Interface control software
- Focusrite Control 2 (guide read): tabs Inputs (gain, 48V, Auto Gain, Clip Safe, Air), Mixer (one mix per output), Routing (a source per output, loopback as an input pair), sample rate in preferences.
- MOTU M2/M4 (review read): no software; loopback as extra driver channels; a monitor mix knob.
- RME TotalMix FX and UA Console: not read today, from general knowledge: TotalMix has three rows (hardware inputs, software playback, hardware outputs) and a control room section; Console has preamp and insert slots, cue outputs, and clock and rate under hardware settings.
- Lesson: these are mixers for monitoring inside the hardware. AudioLab should not copy them; it should **name the outputs and inputs clearly** and leave hardware mixing to the device.

## 3. Interface versus DAC

| | Recording interface | Listening DAC |
|---|---|---|
| Wanted | inputs, output pairs, low delay, direct monitoring, one clock for in and out | clean stereo, the right rate, no conversion, safe volume, headroom, nothing mixed in |
| Buffer | as small as runs without clicks (Ableton: 256 or 512 as a compromise) | large is fine; stability first |
| Rate | project rate; the device is set to it | the device follows the material |
| Volume | knobs on the unit | hardware volume, fixed, or dithered digital |
| Proof | measured round trip, recording offset | signal path, bit test |

**How DAWs handle two devices (read)**
- Mac: Ableton has "Audio Input Device" and "Audio Output Device" and allows different ones, warning of "clocking errors, resulting in audio drop outs". Logic has "Output Device" and "Input Device" and advises a common word clock. Bitwig builds a "Combined Device" with a clock master. FL Studio and Reaper recommend an Aggregate Device.
- Apple's Aggregate Device: pick the most reliable clock; tick "Drift Correction" for every other device. Apple's own guide says this correction is resampling.
- Windows: ASIO is one device for in and out (Ableton); ASIO4ALL combines devices but needs one clock. Reaper and Studio One offer WASAPI shared and exclusive. Microsoft's own low-latency USB audio and ASIO driver was still in preview work in late 2026 (not confirmed as released).
- Other labels worth knowing: Ableton "Driver Error Compensation" and "Use System Device"; Logic "Resulting Latency (Roundtrip/Output)" and "Recording Delay"; Bitwig gives each stereo output a role, "Speakers" or "Headphones", the nearest thing found to a listening role.

**Clock drift**
- Two devices each have their own crystal. At 100 parts per million apart, that is 360 ms per hour (ASIO4ALL page), or about 6 ms per minute at 48 kHz (own arithmetic). Typical crystal figures were not found on a page.
- Listening only on the Gryphon: no problem, there is one clock.
- Recording from the AMS-24 while listening on the Gryphon: the browser resamples the input to the engine's clock, so there are no clicks, but (a guess from how it works) a long take slowly shifts against the song, and the delay is larger and less steady. Fine for a sketch, wrong for tight overdubs.
- **So the app's rule should be: when recording matters, play and record through the same device.** That is why two setups are better than one.

**Unplugging (read)**: macOS moves to another device by itself. Logic shows "Last selected audio interface is not available". Ableton users report lost channel settings. No DAW was found that documents a volume rule on device change.

## 4. What is possible, honestly

**Chromium and Electron today (sources read; code versions older than the one in the app)**
- The engine renders at `ctx.sampleRate`. Chromium resamples "only once, at the very end of the output chain", and only when the device's rate differs (a Chromium engineer, October 2025).
- On the Mac Chromium **reads** the device's rate and never sets it. It **does** set the device's buffer size from `latencyHint`. Output is 32-bit float; the system converts to the device's integer format.
- Without a fixed rate the engine takes the device's rate at start. Whether it follows a later change: not confirmed; by inference it does not (the rate is fixed for the context's life), so the app must restart the engine or switch the device.
- Reading a device's rate without the helper: open a short default context on that device and read its rate.
- `setSinkId` since Chrome 110; `sinkchange` event; `groupId` ties an interface's input and output together (how reliably per driver: not confirmed).
- Outputs above two: `destination.maxChannelCount`; a Mac source comment mentions an 8-channel limit for layouts.
- Inputs: a 2024 note says Chrome hard-codes microphone capture to **2 channels**; current state not confirmed. Fine for the AMS-24 (2 inputs).
- Dropout and delay figures: `AudioContext.playbackStats` (Chrome 146; `playoutStats` is the old name).
- Windows: shared mode always. A switch `--enable-exclusive-audio` exists (restored December 2023 for DTS passthrough), with a warning in the code about bad performance. An experiment at most, not a product path.

**Native facts (read)**
- Mac: setting the nominal sample rate needs no ownership (QA1196; practice, the page does not say "any process"). Hog mode is per process; integer formats are only shown to the process that holds hog mode; a hog change stops the device's I/O. **So a helper cannot give Chromium hog or integer mode.** It needs the process that plays the sound.
- Windows: exclusive mode bypasses the audio engine; the shared format is the user's choice in the Sound panel, with no documented setter (an undocumented one, IPolicyConfig, exists in third-party headers). A limiter sits in the shared path (third-party source). Strict clean output on Windows needs native exclusive or ASIO.
- ASIO: since October 2025 Steinberg offers the SDK under GPLv3 beside its own licence; a closed app still needs the proprietary agreement.
- A native output fed from the web engine (worklet, shared memory, native process) runs on a different clock than the device, so it needs drift handling or the device pulling the graph. That is real work and belongs with the native engine, not before it.

### Feasibility table

| Capability | Now (web engine) | Small helper in the Electron shell | Native engine (plan 2.6) |
|---|---|---|---|
| Choose output and input device | yes (have) | | yes |
| Two roles, two devices | yes | | yes, with drift correction |
| Read the device's rate | indirect (probe context) | yes, Mac (have); Windows new, read-only | yes |
| Set the device's rate | no | Mac yes (have, unproven); Windows not cleanly | yes |
| No conversion anywhere | only if engine rate = device rate | Mac: set the rate to match (inference, prove it) | yes |
| Bit depth at the device | no | Mac: read (have); set: not confirmed | yes |
| Exclusive use, integer mode | no | no (per process) | yes |
| WASAPI exclusive, ASIO | no (unsupported flag only) | no | yes |
| Bypass the Windows mixer and limiter | no | no | yes |
| Hardware volume | no | Mac yes (have); Windows possible (documented API), new | yes |
| Instant news of rate, volume, device changes | `devicechange`, `sinkchange` only | yes, with a listener (new; today it polls) | yes |
| Buffer size | `latencyHint` (have) | no (would fight Chromium) | yes |
| Outputs above 2 | yes (have, untested on hardware) | | yes |
| Inputs above 2 | probably not | no | yes |
| Measured delay and dropouts | yes (`rtMeasure`, `playbackStats`) | | yes |
| Lossless recording | yes (worklet to WAV, to build) | | yes |
| DSD, MQA | no | no | not planned |

### Staged plan

**Stage 0, with the user at the Mac (no code):** plug in both devices; note the names; run the helper's `info`; switch the rate from the app and watch the Gryphon's display and LED colour; check whether the Mac's volume moves the Gryphon; measure the AMS-24 round trip with a cable; try outputs 3/4.

**Stage 1, web engine only:**
1. Two role slots, Listen through and Record from, and the two setups Listening and Recording (section 5).
2. Signal-path read-out with a light.
3. Safe volume: per-device memory, ceiling, never raise on change, lock.
4. Unplug behaviour per role.
5. Record audio takes lossless (worklet to 32-bit float WAV) and apply the measured round trip to takes (both already listed as "left" in the log).
6. Test tone and channel check.
7. A clipping light on the master that reacts to one sample, and an optional headroom figure (peaks between samples).

**Stage 2, small helper:**
1. Mac: turn `alvol` into a listener that reports rate, volume and device changes at once; report the physical format; prove "no conversion" with a pattern test over a loopback.
2. Mac: when the engine starts at another rate, set the device first, then start (order matters; today the app sets it after).
3. Windows: a read-only helper (device name, shared-mode rate and bit depth, hardware volume) so the signal path can at least say "Windows converts 48 to 44.1 kHz here" and tell the user where to change it.

**Stage 3, native engine (together with VST hosting):** exclusive use and integer mode on the Mac, WASAPI exclusive and ASIO on Windows, more than two inputs, input and output on two devices with drift correction, device buffer control.

## 5. Design options for the settings page

### (a) Two separate sections: "Listening output (DAC)" and "Recording interface"
- For: matches the user's first wording; each section stays short; nothing surprising.
- Against: an interface is also an output, so the output appears twice; someone with one device sees an empty half; the two sections can contradict each other (two rates, two buffers) with one engine underneath.

### (b) One page "Audio devices", roles assigned automatically, changeable by hand
- For: matches "have it in one and then automatically"; works with one device or two; one place for the signal path; today's Automatic / DAC / Interface switch grows into it without throwing work away.
- Against: the automatic choice must explain itself or it feels like magic; needs good device recognition (names unconfirmed).

### (c) One device for everything, optional separate monitor output
- For: simplest for the engine; one clock; what most DAWs do.
- Against: makes the Gryphon the "extra", when for this user it is the main listening path; no home for the DAC-specific things.

### Recommendation: (b), with the two roles shown as two cards

**Top of the page: two role cards**
- **Listen through**: device, kind icon, profile name, "In use" badge.
- **Record from**: device, or "No input" (a DAC alone).
- Under them one line in plain words, for example: "Gryphon for listening, AMS-24 for recording. While a track is armed, AudioLab plays through the AMS-24 too, so the take lines up."

**How the automatic part decides**
- A device with inputs in the same group, or a recognised interface: can fill both roles.
- A device with outputs only, or a recognised DAC: Listen through only.
- Both present: DAC for listening, interface for recording.
- **Two setups**, each remembering device, buffer and rate:
  - *Listening*: out = DAC, buffer large (stable), device rate follows the engine, volume as the profile says.
  - *Recording*: in and out = interface, small buffer, direct monitoring advice, measured offset in use.
- Switching: by hand (a two-way switch on the page and in the transport's audio menu), or **automatic: arming a track or the Voice device proposes Recording; disarming the last one goes back to Listening.** The first time it asks; "always do this" makes it silent. Changing the output restarts or moves the engine, so it must never happen while playing or recording.
- If the user prefers to keep listening on the DAC while recording: allowed, with one honest line ("two clocks: fine for sketches, long takes can drift by a few milliseconds per minute").

**Device card with a live signal path**

One row of boxes, left to right, each green or amber:

`Project 48 kHz` → `Engine 48 kHz, 32-bit float` → `Master 0.0 dB, limiter idle` → `System: shared, no conversion` → `Gryphon 48 kHz, 24 bit, volume 62% (hardware)` 

- Beside it: buffer (samples and ms), delay reported, delay measured, dropouts in the last minute.
- **One light** with a sentence, after Roon: *Clean* (one rate, nothing in the way), *Processed* (things you asked for: mono, balance, safety ceiling), *Converted* (the system changes the rate or the device is at a lower bit depth), *Unknown* (browser or Windows without helper: say what cannot be seen), red flash for clipping.
- Never show "exclusive" as available. Show "Shared with other apps" with one line: system sounds and other apps can mix in; turn them off for critical listening.
- "Why?" on every amber box opens the reason and the one action that fixes it.

**Profiles remembered by device name**
- Per device: role, buffer, rate rule (follow / fixed), volume mode (hardware / fixed / digital), ceiling, last volume, output pair, input channel, measured offset, notes.
- The Gryphon's profile adds advice only the user can act on: filter BP for an untouched signal or GTO if preferred; XBass and XSpace off for mixing decisions; iEMatch off for the Stax path; the LED colour to expect at this rate; charge port.
- The AMS-24's profile: MUSIC mode for DAW work; LOOPBACK off while recording; DIRECT MONITOR on and monitoring in the app off, or the other way round; USB 3/4 feeds headphones B.

**Unplugged**
- Listen-through device gone: **stop playback** (do not jump to the Mac's speakers at full level), show a card "Gryphon disconnected: Play through Mac mini speakers / Wait". When it returns: reconnect, restore its remembered volume only if that is lower than or equal to the ceiling, stay stopped.
- Record-from device gone while recording: keep the take so far, stop, say so.
- Today's behaviour (fall back to the default output and keep playing) is the risky one for sensitive headphones.

**Safe volume**
- Volume is remembered per device; a new, unknown device starts low (for example 20%).
- A **ceiling** per device (soft: can be passed on purpose, like Roon's comfort limit) and "Lock volume" (the app never touches the device's volume; for the Stax chain, where the knob on the driver is the control).
- The app never raises hardware volume by itself, also not for "bit-perfect": today's "Set 100%" button should warn when the profile says the device has a variable line out into another amplifier.
- First sound after a device change fades in over a second or two.
- Plain note for electrostatics: "AudioLab cannot see the volume knob on your Stax driver. Turn it down before changing devices."

**Test tone and measurement**
- Test tone: pink noise and 1 kHz sine at -20 dBFS (never full level), left / right / both, with a channel label spoken or shown; a slow fade in.
- Latency: the existing two-click measurement with a cable drawing for the AMS-24 (output 1 to input 1), result stored in the profile and used for takes. If the click comes back with no cable, say "LOOPBACK is on".
- Clean-path test (stage 2): play a known pattern, record it over loopback or read RME's bit-test display, and show "passed at 24 bit" or what changed.

**Plain explanations (one sentence each, behind a "?")**
- Sample rate: how many snapshots of the sound per second; device and project should use the same so nothing has to be recalculated.
- Buffer: how much sound is prepared ahead; small for playing and recording, large for calm playback.
- Shared and exclusive: shared lets other apps play too; exclusive would lock them out, and AudioLab cannot do that yet.
- Hardware volume: the DAC turns itself down; the sound data stays untouched.
- Two clocks: every device counts time itself; two devices slowly disagree.

**What to drop from today's wording**: the "bit-perfect" switch should become "Clean path" for the engine and keep "bit-perfect" only for the lossless player, where it can be true.

## Open questions for the user
1. Is the Stax driver fed from the Gryphon's rear line out, and which knob do you want to be the volume: Gryphon, Stax, or AudioLab?
2. Do you record through the AMS-24 and listen through the Gryphon at the same time, or one after the other?
3. May AudioLab switch the output by itself when you arm a track, or should it always ask?
4. Is Windows clean playback wanted soon, or is the Mac the only listening machine?

## Sources (opened 27 November 2026 by research helpers)

Players
- Roon: [Exclusive Mode](https://help.roonlabs.com/portal/en/kb/articles/faq-what-s-exclusive-mode) · [Audio setup basics](https://help.roonlabs.com/portal/en/kb/articles/audio-setup-basics) · [Signal Path](https://help.roonlabs.com/portal/en/kb/articles/signal-path) · [Headroom Management](https://help.roonlabs.com/portal/en/kb/articles/dsp-engine-headroom-management) · [Volume Leveling](https://help.roonlabs.com/portal/en/kb/articles/volume-leveling) · [Volume limits](https://help.roonlabs.com/portal/en/kb/articles/volume-limits) · [Crossfeed](https://help.roonlabs.com/portal/en/kb/articles/dsp-engine-crossfeed) · [Sample rate conversion](https://help.roonlabs.com/portal/en/kb/articles/dsp-engine-sample-rate-conversion) · [OPRA](https://blog.roonlabs.com/opra-makes-optimized-headphone-tuning-accessible-to-everyone/)
- JRiver: [Exclusive Mode](https://wiki.jriver.com/index.php/Exclusive_Mode) · [Output Mode](https://wiki.jriver.com/index.php/Output_Mode) · [Volume](https://wiki.jriver.com/index.php/Volume) · [DSD](https://wiki.jriver.com/index.php?title=DSD) · [Audiophile Info](https://wiki.jriver.com/index.php/Audiophile_Info) · [integer mode, 2013](https://yabb.jriver.com/interact/index.php/topic,84657.0.html)
- Audirvana: [core player](https://audirvana.com/exclusive-core-player/) · [best sound](https://help.audirvana.com/en/support/solutions/articles/202000050813-how-to-get-the-best-sound-possible-with-audirvāna-) · [volume](https://help.audirvana.com/en/support/solutions/articles/202000050819-which-volume-setting-can-i-change-in-audirvāna-) · [upsampling](https://help.audirvana.com/en/support/solutions/articles/202000072896-how-upsampling-works-in-audirvāna-) · [native DSD](https://help.audirvana.com/en/support/solutions/articles/202000075482-how-to-play-dsd-natively-)
- [Tidal Exclusive Mode](https://support.tidal.com/hc/en-us/articles/28548110049681-Exclusive-Mode) · [Qobuz hi-res on PC](https://help.qobuz.com/en/articles/10202-how-do-i-experience-hi-res-on-pc) · [Spotify Exclusive Mode](https://community.spotify.com/t5/Community-Blog/Desktop-Exclusive-Mode-now-available/ba-p/7371590) · [foobar2000 WASAPI](https://foobar2000.org/components/view/foo_out_wasapi) · [foobar2000 FAQ](https://foobar2000.org/FAQ) · [BitPerfect manual](https://bitperfectsound.blogspot.com/p/manual.html) · [Swinsian changelog](https://swinsian.com/support/changelog/) · [HQPlayer 3 manual](https://sonore.us/HQPlayer-manual.pdf) · [Amarra Luxe](https://www.sonicstudio.com/amarra/amarra4luxe.php) · [Tonal: audiophile playback on macOS](https://medium.com/tonal-app/secrets-of-audiophile-playback-on-macos-8f940e8f4625)
- Apple Music: [Apple, lossless](https://support.apple.com/118295) · [forum thread, 2025](https://discussions-jp-prz.apple.com/thread/256138473) · [LosslessSwitcher](https://github.com/vincentneo/LosslessSwitcher) · [SyncHz](https://github.com/jcongaku/SyncHz)
- MQA: [What Hi-Fi, administration](https://www.whathifi.com/features/mqa-has-gone-into-administration-what-does-this-mean-for-tidal-and-supported-products) · [ChannelNews, Tidal drops MQA](https://www.channelnews.com.au/tidal-dumps-mqa-high-res-format-major-blow-to-lenbrook/)

Hardware
- iFi xDSD Gryphon: [product page](https://ifi-audio.com/collections/all/products/xdsd-gryphon) · [manual](https://r2.gear4music.com/media/112/1127398/download_1127398.pdf) · [review, volume sync](https://positive-feedback.com/reviews/hardware-reviews/ifi-xdsd-gryphon/)
- Stax: [SRM-323S figures, forum quoting Stax](https://www.stereonet.com/forums/topic/88146-stax-srm-323s/) · [SR-L500 MkII](https://www.wooaudio.com/headphones/l500mk2)
- RME: [ADI-2 DAC manual](https://rme-audio.de/downloads/adi2dacr_e.pdf) · [ADI-2 Pro manual](https://rme-audio.de/downloads/adi2profs_e.pdf)
- [Chord Qutest manual](https://www.richersounds.com/content/product_files/Qutest_User_manual_2_1.pdf) · [Chord Mojo 2 manual](https://resources.sevenoakssoundandvision.co.uk/images/manuals/Mojo%202%20User%20Manual.pdf) · [Topping DX5 II manual](https://cdn.shopify.com/s/files/1/0153/8863/files/Headphone-zone-Topping-dx5II-user-manual.pdf) · [FiiO K11](https://www.fiio.com/newsinfo/934272.html) · [Benchmark DAC3 manual](https://cdn.shopify.com/s/files/1/0321/7609/files/DAC3_Series_Manual_Rev_F.pdf)
- [Zoom AMS-24 manual](https://zoomcorp.com/manuals/ams-24-en/) · [Focusrite Scarlett 4i4 4th Gen guide](https://fael-downloads-prod.focusrite.com/customer/prod/downloads/scarlett_4i4_4th_gen_user_guide_v5_en.pdf) · [MOTU M2/M4 review](https://www.soundonsound.com/reviews/motu-m4-m2)

DAWs and systems
- Ableton: [two devices and aggregates](https://help.ableton.com/hc/en-us/articles/209071609-Using-Aggregate-Devices-and-multiple-audio-interfaces) · [latency](https://help.ableton.com/hc/en-us/articles/360010545559) · [Driver Error Compensation](https://help.ableton.com/hc/en-us/articles/115000234830) · [monitoring](https://help.ableton.com/hc/en-us/articles/360006569179) · [sample rate](https://help.ableton.com/hc/en-us/articles/209774965)
- [Logic Pro audio settings](https://support.apple.com/guide/logicpro/lgcpbb81aca5/mac) · [Bitwig dashboard](https://www.bitwig.com/userguide/latest/the_dashboard/) · [FL Studio audio settings](https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/envsettings_audio.htm) · [Reaper guide](https://dlx.reaper.fm/userguide/html/) · [Studio One I/O (SOS)](https://www.soundonsound.com/techniques/studio-one-audio-io-routing)
- Apple: [Aggregate Device](https://support.apple.com/en-ae/102171) · [Audio MIDI Setup, sync](https://support.apple.com/guide/audio-midi-setup/ams094c7edb4/mac) · [device disconnected](https://support.apple.com/en-au/guide/audio-midi-setup/ams0c519de39/mac)
- [ASIO4ALL, device aggregation and drift](https://asio4all.org/device-aggregation/) · [SOS, digital clocking](https://www.soundonsound.com/techniques/digital-clocking-explained) · [Microsoft, low-latency audio driver post](https://devblogs.microsoft.com/windows-music-dev/wp-json/wp/v2/posts/815)

Chromium, Core Audio, Windows
- [Chromium media-dev: one resampler at the end](https://groups.google.com/a/chromium.org/g/media-dev/c/pBSbas5OQvI) · [audio_manager_mac.cc](https://chromium.googlesource.com/chromium/src/+/c56d17048ae4886edba18e26d6d02128ae1e8a3b/media/audio/mac/audio_manager_mac.cc) · [renderer_webaudiodevice_impl.cc](https://chromium.googlesource.com/chromium/src/+/ff0d241ac8df72ad2cb4d3105cf90d802b62cbfd/content/renderer/media/renderer_webaudiodevice_impl.cc) · [Windows output, exclusive switch](https://chromium.googlesource.com/chromium/src/media/+/master/audio/win/audio_low_latency_output_win.cc) · [switch restored, 2023](https://chromium.googlesource.com/chromium/src/+/14618e3440e84b68f0310dd139ec216eab6be97e)
- [Chrome: AudioContext.setSinkId](https://developer.chrome.com/blog/audiocontext-setsinkid) · [MDN setSinkId](https://developer.mozilla.org/en-US/docs/Web/API/AudioContext/setSinkId) · [W3C Audio Output Devices](https://www.w3.org/TR/audio-output/) · [MDN maxChannelCount](https://developer.mozilla.org/en-US/docs/Web/API/AudioDestinationNode/maxChannelCount) · [capture limited to 2 channels, 2024](https://lists.w3.org/Archives/Public/public-webrtc-logs/2024Nov/0191.html) · [MDN AudioPlaybackStats](https://developer.mozilla.org/en-US/docs/Web/API/AudioPlaybackStats) · [playbackStats ship notice](https://groups.google.com/a/chromium.org/g/blink-dev/c/p-IHBp8Nw2Q) · [renderSizeHint ship notice](https://groups.google.com/a/chromium.org/g/blink-dev/c/i4c1unRSmcE)
- Apple: [QA1196, device sample rate](https://developer.apple.com/library/content/qa/qa1196/_index.html) · [hog mode](https://developer.apple.com/documentation/coreaudio/audiohardwaredevice/togglehogmode().md) · [integer formats need hog mode, 2008](https://lists.apple.com/archives/coreaudio-api/2008/Jun/msg00132.html) · [hog change stops I/O, 2010](https://lists.apple.com/archives/coreaudio-api/2010/Jan/msg00058.html) · [integer mode removed in Lion, 2011](https://lists.apple.com/archives/coreaudio-api/2011/Jul/msg00143.html)
- Microsoft: [exclusive-mode streams](https://learn.microsoft.com/en-us/windows/win32/CoreAudio/exclusive-mode-streams) · [device formats](https://learn.microsoft.com/en-ie/Windows/Win32/coreaudio/device-formats) · [low latency audio](https://learn.microsoft.com/en-sg/WINDOWS-HARDWARE/DRIVERS/audio/low-latency-audio) · [Windows limiter, third party](https://github.com/dechamps/WinSoftVol)
- [Steinberg opens VST3 and ASIO (CDM)](https://cdm.link/open-steinberg-vst3-and-asio/) · [audify (RtAudio for Node)](https://github.com/Xcraft-Inc/audify)

Earlier AudioLab research on the same subject: `docs/backlog-log.md`, v0.172 (run 11), with its own source list.
