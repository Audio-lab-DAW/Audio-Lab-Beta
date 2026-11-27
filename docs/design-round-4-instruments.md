# AudioLab Pro design round 4: meters, scopes and analyzers (task DR4, 27 November 2026)

Pick page: **AudioLab instruments: meters, scopes and analyzers**, https://claude.ai/artifact/7EZJLqYsdLKZQEDmgja5y8

**This is a pick page only.** Nothing in index.html or desktop/ was changed, and there is no version bump. The page source and tools are in `tools/design-lab/dr4/`:
- `page_src.html` with `build.py` makes `instruments.html`.
- `shoot_today.py` and `shoot_devices.py` take the "Today" screenshots of v0.228, and `crops.py` cuts them into `today/family_*.png`.
- `check.py` is the headless check; its screenshots are in `shots/`.

This round follows the science look (`docs/science-look.md`, `docs/science-look-round-2.md` and the picks in `claude/audiolab-science-picks.md`), the design philosophy in `docs/glass-engine-plan.md` section 1, and `docs/design-language-research.md` ("animate only signal and state"; "informative scopes, not decorative ones").

The user asked for "everything in AudioLab that measures sound, drawn as precise scientific instruments". Today's colours stay. The look stays subtle. Snappiness and low CPU come first.

**Kept, the user's standing picks:**
- the mixer's **Flat bars** design
- the half pan dial
- the mixer header
- the stereo field displays
- the cables

For these, only the drawing and the scales improve; nothing replaces them.

**Not duplicated:** MD1 (M1 read-outs with units, M2 orbit loader, M3 caliper). The round-2 details X5, X8, X11 and X15 are used where they fit, and keep their own tasks.

## How to answer

On the page:
- Click one card per family.
- In O and G, click any number of cards; they add to each other.
- Set the Visualizer menu (V menu).
- Press "Copy my picks" and paste the line. It looks like `My picks: M2 | L1 | S1 | O1 O2 | G1 G3 | E1 | V1 map magma | C1 | D1`.

"Take all ★" fills in exactly that line, which is the recommendation.

## How the page works (so the pictures can be trusted)

One measuring engine reads each new block of a test signal once per frame and feeds every card. The test signals are made in code at 48 kHz:
- a 145 BPM mix loop (drums, bass, wide pad) with sample peak −1.0 dBFS
- the drum loop alone
- pink noise with L and R independent, at −20 dBFS RMS
- a log sine sweep from 20 Hz to 20 kHz at −12 dBFS
- a 1 kHz sine at −18 dBFS
- a stereo test that steps through mono, wide, anti-phase and left only

"Listen" plays the same buffer, and the drawing follows the audio clock.

The engine measures:
- Sample peak and **true peak**: 4× oversampling with a 48-tap windowed-sinc interpolator, 12 taps per phase.
- **RMS** in 300 and 600 ms windows (AES17, +3.01 dB, so a sine reads its peak level).
- **VU**: second order on the rectified signal, ζ 0.81, 13.4 rad/s. It reaches 99 % in 0.30 s with 1.3 % overshoot (IEC 60268-17), checked by simulation.
- **PPM type IIb**: 6.3 ms attack (10 ms burst at −2 dB), falling 24 dB in 2.8 s.
- **Loudness** per BS.1770-5:
  - K-weighting with the 48 kHz coefficients of the standard
  - 100 ms blocks
  - M from 400 ms and S from 3 s
  - I with the −70 LUFS absolute gate and −10 LU relative gate
  - LRA per Tech 3342: −20 LU relative gate, 10th to 95th percentile
- **Correlation**, balance and width over 500 ms.
- A real **compressor**: −18 dBFS, 4:1, 6 dB knee, 10 and 120 ms.
- A **limiter**: +6 dB in, −1 dBFS ceiling, instant attack, 100 ms release.
- A **three-band compressor** with bands split at 120 Hz and 2.5 kHz.
- A five-band **example EQ** run on the signal, so "post" is the real filtered sound.
- FFTs (Hann window, scaled so a full-scale sine reads 0 dBFS), computed once per frame and shared by every card that needs them.

**Calibration check, measured headless with the 1 kHz −18 dBFS sine:**

| Measurement | Reading |
|---|---|
| Sample peak | −18.00 dBFS |
| True peak | −18.00 dBTP |
| RMS (AES17) | −18.00 dBFS |
| VU (aligned so −18 dBFS sine = −18) | −18.01 |
| Momentary, short-term and integrated loudness | −17.99 LUFS each |
| Correlation | +1.00 |

Pink noise (L and R independent) reads correlation +0.04 and width 0.96.

**Drawing rules:**
- Pictures are drawn only at screen rate, only while on screen (IntersectionObserver), and stop when the tab is hidden.
- The device pixel ratio is capped at 2.
- The "Light mode" button applies the app's Light mode: half rate, no afterglow or persistence, 4096-point FFT.
- Each card shows its own median draw time, measured live.

On the cloud machine (software renderer, 1300 px wide, two cards per row), every card drew in 0.1 to 1.5 ms per frame, with two exceptions:
- **E1** 1.9 ms: it pays for the two shared 8192-point FFTs, pre and post.
- **O3** 3.1 ms: the oscilloscope's afterglow layer.

On a GPU both should be far lower. Measure them in the app before shipping.

Checks:
- No console errors, dark at 1300 px and light at 400 px.
- No sideways scroll at phone width.

## Today (headless screenshots of v0.228, Fractals playing; where each lives in index.html)

**Frame loop:**
- One rAF loop, `frame()`.
- Meters run every ≥ 7.5 ms.
- `drawMixer()` runs every second frame.
- `drawViz()` runs every 15 to 33 ms, and every 500 ms when calm.
- `cpuFrame()` runs every 100 ms.

**Meter engine:**
- `mtrPeak()` reads new samples only.
- Settings live in `UI.mtr`, with speeds instant, fast, normal and smooth, and readings peak, RMS 50 ms, VU and "Loudness".
- Colours come from `LVC` and `MCOLS`.
- The scale is `TAPER`, from −60 to +6 dB, with 0 dB at 82 %.

**Level meters:**
- Transport meter: `meters()` (#mtr) with `#peakBox`.
- Track headers: `trackMeters()`, in the DOM.
- Mixer strips: `drawMixer()` and `mxsTick()`. The design comes from `FDS`, where 'Flat bars' is design 7.
- `miniMeter()` sits beside the LUFS box.

**Loudness:**
- `al-meter` worklet, BS.1770-5 compliant.
- `lmPaint()` and `lmOpen()`.
- The `.mxme` master box.
- The `ND('loud')` and `ND('measure')` devices.

**Spectrum:**
- `ND('spec')` with `drawSpec()`.
- `spoOpen()` (SPO/ANZM).
- The Visualizer `VZ`: tabs `VZM`, menu `pvMenu`.
- The mixer's spec view.

**Stereo:** the `drawMixer` stereo view and `.mxco`.

**CPU:** `cpuFrame()` (#cpuC).

**Dynamics:**
- `vizComp()`
- `ND('limit')`
- `vizOTT()`
- gate, multiband, de-esser, transient and ducker displays

**EQ:** `vizEQ2()` (±24 dB, analyzer with 4.5 dB/oct tilt) and `vizFilter()`.

**Device previews:** `level()`, `miniWave()`, the Soft Clipper and Gate displays.

**Two things noticed in passing** (not fixed; index.html is out of scope here):
- `function vizSide` is declared twice: the sidechain device display near line 3446 and the Visualizer layout helper near line 8875. The later one may replace the first, so the sidechain device may lose its picture.
- The meter's "Loudness" reading (`MTRWIN.lufs`) is plain mean-square with −0.691 added. Its label says "K-weighted, 400 ms", but that path has no K-weighting.

## Research summary (sources opened 27 November 2026 by a research helper; derived numbers marked)

### 1. Standards

**EBU R128:**
- Programme target −23.0 LUFS (±0.5 LU, or ±1 LU live).
- Maximum true peak −1 dBTP.
- LRA is reported but not limited.
- [EBU R 128, Wikipedia](https://en.wikipedia.org/wiki/EBU_R_128)

**EBU Tech 3341 ("EBU Mode"):**
- Momentary is 0.4 s and short-term is 3 s, both ungated. M and S update at ≥ 10 Hz, I at ≥ 1 Hz.
- EBU +9 scale (default): −18 to +9 LU. EBU +18 scale: −36 to +18 LU.
- The target must not move when switching between relative and absolute scales.
- Units are always shown, readouts carry at most one decimal, and LRA is flagged "not yet stable" for 60 s after a reset.
- The spec deliberately sets no colours.
- [EBU Tech 3341](https://tech.ebu.ch/docs/tech/tech3341.pdf)

**EBU Tech 3342 (LRA):**
- Built from 3 s short-term values updated at ≥ 10 Hz.
- Gates: −70 LUFS absolute, −20 LU relative.
- LRA is the 95th percentile minus the 10th.
- [EBU Tech 3342](https://tech.ebu.ch/docs/tech/tech3342.pdf)

**ITU-R BS.1770-5:**
- Two-stage K-weighting.
- Loudness = −0.691 + 10 log of the summed mean square.
- 400 ms blocks with 75 % overlap; gates at −70 LKFS absolute and −10 dB relative.
- True peak by 4× oversampling.
- Surround channels weighted 1.41; LFE excluded.
- [ITU-R BS.1770-5](https://www.itu.int/dms_pubrec/itu-r/rec/bs/R-REC-BS.1770-5-202311-I!!PDF-E.pdf)

**Streaming targets:**
- Spotify normalises to −14 LUFS (Loud −11, Quiet −19) and recommends true peak below −1 dBTP, or below −2 dBTP above −14 LUFS. [Spotify for Artists](https://support.spotify.com/artists/article/loudness-normalization/)
- Apple Music −16, YouTube −14, Tidal −14, Amazon −14, Deezer −15. These come from iZotope's summary, not from the platforms' own pages. [iZotope](https://www.izotope.com/en/learn/mastering-for-streaming-platforms.html)
- AES TD1008: −16 LUFS for music, −18 for speech. [Production Advice](https://productionadvice.co.uk/td1008/)

**K-system:**
- 0 sits at −20, −14 or −12 dBFS (K-20, K-14, K-12).
- Calibration: 83 dB SPL C-weighted per channel with pink noise. [MeterPlugs](https://meterplugs.com/blog/2016/10/14/k-system-metering-101.html)
- Colours: green below 0, yellow up to +4, red above. [SOS, K-Meter review](https://www.soundonsound.com/reviews/meterplugs-k-meter)
- Katz on the zones: sustained red means the monitoring is too quiet. [Digido](https://www.digido.com/?p=1441)
- RMS integration in K modes: 600 ms in Voxengo SPAN. [Voxengo SPAN guide](https://www.voxengo.com/files/userguides/VoxengoSPAN_en.pdf/getbyname/Voxengo%20SPAN%20User%20Guide%20en.pdf)

**PPM (IEC 60268-10)** ([Wikipedia](https://en.wikipedia.org/wiki/Peak_programme_meter)):
- Type I (DIN): 5 ms integration; returns 20 dB in 1.7 s.
- Type IIa (BBC) and IIb (EBU): 10 ms integration; fall 24 dB in 2.8 s. The EBU scale is −12 to +12 around TEST.
- Digital peak meters (IEC 60268-18): < 5 ms, returning 20 dB in 1.7 s, which is 11.8 dB/s (derived).
- Digital alignment level: −18 dBFS (EBU R68) or −20 dBFS (SMPTE).

**VU (IEC 60268-17):**
- 300 ms to 99 %, 1 to 1.5 % overshoot.
- [VU meter, Wikipedia](https://en.wikipedia.org/wiki/VU_meter)

**Peak hold:**
- Logic MultiMeter: 2, 4, 6 s or infinite. [Apple](https://help.apple.com/logicpro/mac/10.4.5/en.lproj/lgcef24f402d.html)
- RME DIGICheck: hold from 0.2 to 100 s, release 10 dB/s recommended. [RME](https://archiv.rme-audio.de/old/english/techinfo/digich.htm)

### 2. How the best tools draw them

**RME DIGICheck** ([RME](https://archiv.rme-audio.de/old/english/techinfo/digich.htm), [overview](https://docs.rme-audio.de/aoxd/706-1c_digicheck_win)):
- Peak in the inner bar and RMS in the outer, as one meter.
- Overs counted from 1 to 20 consecutive full-scale samples; readouts in 0.1 dB steps.
- Goniometer with oscilloscope-style afterglow.

**iZotope Insight** ([SOS review](https://www.soundonsound.com/node/4903554)):
- Loudness history of M, S and I against the target, with overs in red.
- Spectrogram.
- Polar Sample: fading dots, within ±45° = mono compatible.
- Polar Level.
- Lissajous in a diamond.

**FabFilter Pro-Q** ([analyzer](https://prod.fabfilter.com/help/pro-q/using/analyzer), [spectrum grab](https://www.fabfilter.com/help/pro-q/using/spectrumgrab)):
- Analyzer range 60, 90 (default) or 120 dB; resolution 1024 to 8192 points.
- **Tilt 4.5 dB/oct around 1 kHz**.
- Pre, post and sidechain spectra; Freeze builds a held maximum.
- Spectrum grab: pause, then drag a peak into a band.

**FabFilter Pro-L 2** ([metering](https://prod.fabfilter.com/help/pro-l/using/metering), [loudness](https://www.fabfilter.com/help/pro-l/using/loudnessmetering)):
- History of input (light), output (dark blue) and **gain reduction in red**, plus a thin loudness line.
- Level scales of 16, 32 and 48 dB, plus K-modes.
- True-peak readout: green, orange above the output level, red above 0.
- Loudness: +9 and +18 LU scales.

**Voxengo SPAN** ([guide](https://www.voxengo.com/files/userguides/VoxengoSPAN_en.pdf/getbyname/Voxengo%20SPAN%20User%20Guide%20en.pdf)):
- 4.5 dB/oct default slope.
- Secondary max trace drawn darker.
- Crest factor over 50 ms; correlation over 500 ms; integrated loudness updated at 2 Hz.

**NUGEN VisLM 2** ([manual](https://nugenaudio.com/files/manuals/VisLM2%20Manual.pdf)):
- History from 10 s to 24 h, with an LRA envelope.
- True-peak overs as red dots; orange on a limit breach.
- Short-term histogram.

**TC Electronic Clarity M** ([SOS](https://www.soundonsound.com/node/4917026)):
- Loudness Radar: momentary on the outer ring, target at 12 o'clock.
- 6 dB rings, 4-minute rotation.
- True peak shown from −60 to +3.

**Waves PAZ** ([manual](https://images.equipboard.com/uploads/item/manual/6474/waves-paz-analyzer-plugin-manual.pdf)):
- Polar display: ±45° for hard L or R; the background turns red beyond 60°.
- 52-band RTA.

**Studio One** ([SOS](https://www.soundonsound.com/techniques/studio-one-metering-options)): exact value on hover; heavy marks at −12, −9, −6 and −3.

**Not found:** usable official pages for Bitwig, Logic's own meters, Ozone and NUGEN Stereoizer. MeldaProduction's MAnalyzer page gives no numbers.

### 3. Scientific plotting

- **Tufte's data-ink ratio:** remove non-data ink "within reason". [data.europa.eu](https://data.europa.eu/apps/data-visualisation-guide/chart-junk-and-data-ink-origins)
- **Counter-evidence on memorability:** Bateman 2010 and Borkin 2013 found embellishment can help. [Wikipedia, Chartjunk](https://en.wikipedia.org/wiki/Chartjunk)
- **matplotlib colour maps:** viridis, plasma, inferno, magma and cividis rise steadily in lightness. jet, hsv and turbo do not, and cannot be read in greyscale. Avoid red with green. [matplotlib](https://matplotlib.org/stable/users/explain/colors/colormaps)
- **Crameri, Shephard and Heron (2020):** rainbow maps distort by more than 7 % of the data range. Colour-vision deficiency affects about 8 % of men. Use uniform, lightness-ordered maps and always a colour bar. [Nature Communications (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC7595127)
- **Origin of viridis:** Smith and van der Walt, SciPy 2015. [pyvideo](https://pyvideo.org/scipy-2015/a-better-default-colormap-for-matplotlib.html)
- **Log-axis tick hierarchy:** ggplot2 uses long 2.25, mid 1.5 and short 0.75. [ggplot2](https://search.r-project.org/CRAN/refmans/ggplot2/html/guide_axis_logticks.html)

### 4. Instrument front panels

**Oscilloscopes:**
- Graticule of 8 by 10 major divisions with minor marks on the centre axes; V/div and s/div shown on screen.
- Digital phosphor: intensity by how often a point is hit.
- [Tektronix, XYZs of Oscilloscopes](https://www.ece.ucdavis.edu/~spencer/195/datasheets/XYZ.pdf)
- Persistence from 0.5 s to infinite, with colour grading. [EE Times Asia](https://www.eetasia.com/oscilloscope-persistence-displays/)
- Fill the screen without clipping; cursors and automatic measurements. [Rohde & Schwarz](https://www.rohde-schwarz.com/_254512.html)

**Spectrum analyzers:**
- 10 by 10 graticule with the **reference level on the top line**; log scale of 70 to 100 dB.
- RBW and VBW; detectors (positive peak by default); trace averaging.
- [Keysight, Spectrum Analysis Basics](https://www.dinfo.unifi.it/upload/sub/laboratori/emc/Dispense%20Misure%20Elettroniche/Keysight_Spectrum%20analysis%20basics_2015.pdf)
- Marker, **delta marker**, peak search. [Keysight](https://www.keysight.com/used/au/en/knowledge/guides/how-to-use-a-spectrum-analyzer)

### 5. Readable while mixing

**Ian Shepherd** ([SOS](https://www.soundonsound.com/techniques/ian-shepherd-loudness-dynamics)):
- Short-term LUFS is the most useful reading; momentary moves too fast for music.
- Loud sections of a master no higher than about −10 LUFS short-term.
- Integrated is for distribution.

**Mastering The Mix LEVELS** ([page](https://www.masteringthemix.com/pages/mixing-with-levels)): status icons, plus a tooltip giving the value, the threshold and the fix.

**SOS on level meters** ([SOS](https://www.soundonsound.com/techniques/level-meters)):
- Average meters show loudness better than peak meters.
- Colour turn points placed close together read as a crisp threshold.
- A clip light should stay latched.

**SOS on PPM and VU** ([SOS](https://www.soundonsound.com/techniques/mysteries-metering)): an EBU PPM reads about 8 dB above a VU on the same signal.

### Rules taken from this into the options

1. **Units and decimals.** Units always shown, one decimal, a real minus sign.
2. **The loudness target stays put** when the scale changes from relative to absolute.
3. **Peak and average in one bar**, with the max read-out latched until clicked.
4. **Ballistics from the standards.** Digital peak falls 11.8 dB/s; VU and PPM follow IEC; LRA is marked as settling for 60 s.
5. **Log frequency axes.** Long marks at decades, shorter at 2 and 5, labels only where they fit.
6. **Spectra:** 4.5 dB/oct tilt, reference level on the top line, max hold dimmer than the live trace.
7. **Heat pictures** use magma, inferno or viridis, always with a colour bar.
8. **Graticule first** for scopes, with the settings in the corners.
9. **Gain reduction hangs from the top** on the level's own dB scale.
10. **Red never carries a meaning alone.** A position or a hatching goes with it.
11. **The least ink that still reads.**

## The options

★ marks a recommendation. Every family has a "Today" card (0) with a screenshot of v0.228.

### M. Level meters (track header, mixer strip, master, transport; one pick)

The Flat bars, cap, pointer and colours stay in every option.

| # | Option | What changes |
|---|---|---|
| M1 | Calibrated peak | The scale follows the fader taper: a mark per dB from +6 to −12, every 3 dB to −24, then every 6. Digital peak ballistics: instant rise, 20 dB in 1.7 s. 2 s hold. Highest peak in a box, CLIP latched. True peak max beside it. |
| **M2 ★** | Peak and RMS in one bar | M1, plus RMS 300 ms (AES17) as the bright core with the peak faint above it. Read-outs for peak, RMS and crest factor. DIGICheck style. |
| M3 | Peak with a loudness mark | M1, plus an amber mark at the momentary LUFS across both bars. |
| M4 | K-14 scale | Same strip; 0 = −14 dBFS (K-20 and K-12 in the menu). The bar is the 600 ms average: green, then yellow to +4, then red. Peak as a thin line. |

Why M2: it is the reading that helps most while mixing. Peak says "will it clip", average says "how loud", and the crest factor says "how punchy". It costs one more fill.

### L. Loudness and true peak (top-bar box, pop-up, mixer master box, Loudness device; one pick)

| # | Option | What it is |
|---|---|---|
| **L1 ★** | EBU Mode read-out | EBU +9 scale around the target, with a short-term bar and a momentary line. M, S and I in LUFS, LRA (settling for 60 s), TP max in dBTP (red above −1), and I relative to the target. The top-bar box: green within ±1 LU, yellow to +3, red above. |
| L2 | Loudness history | 30 s: S as a line, M faint, I dashed, the target band ±1 LU shaded; above the band the line turns yellow. |
| L3 | Loudness radar | Clarity M in the orbit style: one turn per 30 s (4 min in the app), rings every 6 LU, the target ring green, momentary on the outer arc. |
| L4 | Loudness distribution | Histogram of short-term values. An LRA caliper from P10 to P95 (Tech 3342); I and the target as lines. |

Why L1: it is the standard layout, so a number reads the same as in every other tool. L2 is the natural companion inside the pop-up and the Loudness device, if wanted later.

### S. Spectrum analyzer (Spectrum device, overlay, Visualizer spectrum, mixer spec view; one pick)

| # | Option | What it is |
|---|---|---|
| **S1 ★** | Calibrated spectrum | A fine line with a faint fill. Max hold falling 3 dB/s. Tilt 4.5 dB/oct at 1 kHz. 0 to −90 dB with a line every 10. A marker with frequency, note and level that follows the peak or the pointer. FFT, window and RBW in a corner. |
| S2 | Analyzer front panel | A 10 by 10 graticule, REF at the top line, 10 dB/div. Start and stop frequency, RBW, AVG and DET shown. Trace 1 live, trace 2 max hold. Marker 1 and a delta marker. |
| S3 | 1/3-octave bars | The 31 IEC 61260 bands, summed band power, peak caps held 2 s. Pink noise reads flat. |
| S4 | Persistence | A density picture of recent traces in magma with a colour bar; the live trace on top. |

### O. Oscilloscope, stereo field and phase (any number)

| # | Option | What it is |
|---|---|---|
| **O1 ★** | Stereo field with marks and afterglow | The kept display, plus marks only (X5): dB ticks on the M, L and R axes; +S and −S; a short afterglow; the newest point as an amber dot. A correlation bar with a −1 to +1 scale, the negative half hatched, the value and the phase angle. |
| **O2 ★** | Correlation, balance and width | Three scales with pointers and numbers. A 10 s correlation history with the negative part hatched red. |
| O3 | Oscilloscope | For the Visualizer's waveform. An 8 by 10 graticule with minor marks, triggered on the rising zero crossing of L. L yellow, R cyan. Phosphor afterglow. Read-outs: 2 ms/div and 0.25/div. |
| O4 | Polar view (extra view) | iZotope's polar sample as an extra choice in the stereo display's menu, never instead of it. ±45° guides and a hatched out-of-phase area, with "in phase" in percent. |

### G. Gain reduction (any number)

| # | Option | What it is |
|---|---|---|
| **G1 ★** | Gain reduction history | 4 s in the Pro-L style. Input as a grey area, output as a blue line, GR in red hanging from the top on the same dB scale. Big number for now, smaller for the 4 s maximum. |
| G2 | GR meters with a hardware scale | A bar falling from the top on the scale 0, 1, 2, 3, 4, 6, 8, 10, 15, 20, 30, so the first dB gets the most room. Peak tick held 2 s, a number, and a thin version for the device title. |
| **G3 ★** | Transfer curve with a live point | The compressor curve on −60 to 0 dBFS with a 6 dB grid and labels every 12. The signal rides the curve as a dot with a trail. An amber caliper to the 1:1 line gives the GR. |
| G4 | Per-band gain reduction | For OTT, Multiband and the de-esser: G2 bars per band, with band edges and numbers. |

### E. EQ curves and the Pro EQ display (one pick)

| # | Option | What it is |
|---|---|---|
| **E1 ★** | Calibrated EQ | Gain scale on the left (±12 dB here, zooming 6, 12, 18 or 30) and analyzer dBFS on the right, each in its own colour. Pre in grey and post in blue, with the tilt named. Band curves faint, the sum on top. The selected band reads frequency, note, gain, Q and bandwidth in octaves. |
| E2 | Measured response | E1 plus post minus pre measured over 2 s as dots, and how close it is to the curve (dB RMS). |
| E3 | Bandwidth calipers | Fill between the curve and 0 dB, an amber −3 dB bandwidth caliper under each bell, corner marks on shelves and cuts. |
| E4 | Quiet | Decades only, the sum curve and a post line. For small devices and Light mode. |

### V. The Visualizer and its right-click menu (one pick, plus a colour map)

| # | Option | What it is |
|---|---|---|
| **V1 ★** | One frequency axis | Spectrogram and spectrum share one frequency axis (the spectrum lies sideways). Magma with a colour bar in dBFS. Waveform with a scale bar. Levels as M2. |
| V2 | Instrument rack | Four modules, each with its settings in the header: spectrogram (FFT, Hz/bin), spectrum (RBW, tilt), scope (ms/div, trigger), levels. |
| V3 | Spectrogram first | Full-panel spectrogram with a bars-and-beats time axis at the project tempo and bar lines, an upright colour bar, a waveform strip and slim levels. |

The **V menu** keeps today's items (View; where it sits: top, bottom, left, right, own window). It adds:
- Colour map: **Magma ✓**, Inferno, Viridis, Today's heat
- Range: 60, **90 ✓**, 120 dB
- Spectrum tilt: 0, 3, **4.5 ✓** dB/oct
- Hold: Off, **Max hold ✓**
- Speed: Slow, **Normal ✓**, Fast

The chosen map goes into the picks line.

### C. CPU graph (one pick)

| # | Option | What it is |
|---|---|---|
| **C1 ★** | Load against budget | Today's filled graph with a 0, 50 and 100 % scale and a dashed budget line at 75 %; red only above it. Read-outs: now, the 4 s peak, ms per frame. A budget tick in the button. |
| C2 | Frame-time histogram | For the CPU pop-up: 0 to 33 ms with the 16.7 ms line, the median and the 99th percentile. |
| C3 | Orbit gauge | A 240° arc with a tick ring and an amber mark at the 75 % budget. At button size, a ring with a dot. |

### D. Waveform and spectrum previews in devices (one pick)

| # | Option | What it is |
|---|---|---|
| **D1 ★** | Scope preview | 300 ms as min and max columns, lines at 0 and ±0.5, a time scale bar (X11), peak in dBFS, red marks at full scale. |
| D2 | Level envelope in dB | Mirrored −48 to 0 dB with an RMS core, so tails and gate action show. |
| D3 | Mini spectrum | 1/6-octave smoothed line, decade marks, the peak with its note. |

## Recommendation (the "Take all ★" line)

`My picks: M2 | L1 | S1 | O1 O2 | G1 G3 | E1 | V1 map magma | C1 | D1`

## Implementation order (index.html tasks, one per instrument family, after the picks)

Each task:
- builds only what was picked, with the usual release routine;
- keeps the audio path untouched (meters read what the worklets already send);
- runs a headless test with screenshots;
- checks the frame time with the instrument on screen and off screen (zero when hidden, and in the background freeze);
- gives Light mode its half-rate variant.

1. **IN-A, shared instrument base.** One small module with:
   - the scale drawers: taper scale, log frequency axis, dB grid, graticule
   - one number formatter, shared with MD1 and X9
   - colour maps as lookup tables (magma, inferno, viridis, today's heat)
   - the ballistics: digital peak 11.8 dB/s, hold, VU, PPM
   - one FFT cache per analyser per frame

   No visible change yet. While there, fix the meter "Loudness" reading so it is K-weighted (or label it truthfully), and fix the double `vizSide`.

   **Done in v0.241** (task IN-A): module `INS` in index.html; the Loudness reading is K-weighted, `vizSide` fixed (the Visualizer's helper is `vizDockSide`). See the backlog log.
2. **IN-M, level meters (M).** Mixer strips (Flat bars kept), track headers, master, transport and the settings preview `mtrPv`. Uses IN-A's scale and ballistics. RMS and crest come from `al-meter` or the analyser data already read.

   **Done in v0.257** (task IN-M, M2): `INS.pr` (300 ms window), `INS.mbar` (the one canvas bar drawer, for DS-T2's TM1), `INM` (the core as a veil on the page-element meters, read-outs). The speed, reading, colour and hold settings stay the user's; the core shows with the Peak reading. See the backlog log.
3. **IN-L, loudness (L).** Top-bar box, `#lufsPop`, `.mxme` master box, `ND('loud')` and `ND('measure')`. The data is already in `LM`; only the drawing and the colour rule change. LRA settling uses X15.

   **Done in v0.259** (task IN-L, L2): `INS.lhist` (the one loudness history drawer), `INL` (the master's momentary and short-term, 10 a second). The devices keep their own measurement, span and scale; LRA settling for 60 s. See the backlog log.
4. **IN-S, spectrum (S).** `ND('spec')`, the overlay (SPO), the Visualizer spectrum and the mixer spec view share one drawer. Analyser fftSize and smoothing move to the IN-A cache.

   **Done in v0.263** (task IN-S, S2): `INS.spec` (the one analyzer front-panel drawer: 10 by 10 graticule, REF on the top line, START, STOP, RBW, AVG, DET, trace 1 live, trace 2 max hold, marker 1 and the delta marker), `INS.an` (analyser size and smoothing in one place). Levels calibrated to dBFS (a sine reads its peak level). The Spectrum device, the overlay's spectrum module and the Visualizer's spectrum draw through it; the mixer's spec view keeps its bars and gets decade marks. See the backlog log.
5. **IN-E, EQ (E).** `vizEQ2()`, `vizFilter()`, Auto Filter. The curve is cached per change; pre and post come from the existing analysers.

   **Done in v0.264** (task IN-E, E3): the Pro EQ with the fill between the summed curve and 0 dB, an amber caliper under each bell (band-pass, notch) measured on the band's own response, corner marks on shelves and cuts, the gain scale on the left and the analyzer's dBFS scale and tilt on the right, note and octaves in the band read-out; the Filter and Auto Filter displays the same. The ±24 dB range stays (E1's zoom not built: the hit test, drag and box select share the range). See the backlog log.
6. **IN-G, dynamics (G).** `vizComp()`, the limiter, gate, ducker, OTT and multiband displays, from the GR values the devices already post.

   **Done in v0.276** (task IN-G, G1 G3 G4): `INS.grh` (the one gain reduction history drawer) in the Compressor, Limiter, Gate and Ducker; the Compressor's curve as Chromium computes it (`ingCK`) with the live point, a 30-point trail and the amber caliper; `ingBar` (G4 bars on the studio scale) in OTT, Multiband and the De-Esser. See the backlog log.
7. **IN-O, stereo and scope (O).** Marks and afterglow on the kept stereo displays: mixer strips (strips off screen keep only history, as today) and the master. The correlation, balance and width scales. The scope in the Visualizer. The polar view as a menu choice.

   **Done in v0.280** (task IN-O, O0 O1 O4): today's stereo field kept with `inoMarks` (the O1 marks), `inoLayer` (the afterglow), the newest sample amber, `inoCorr` (the phase bar's scale, value and angle); the master box's Stereo value and bar; the overlay's stereo module with the marks; the polar view (`inoPolBg`, `inoPol`) as a Picture choice in the stereo view's menu. The track taps stay at 256. See the backlog log. v0.283: the phase angle from the value as shown (`in_o_fix1.py`).
8. **IN-V, Visualizer (V).** The layout, plus the right-click menu entries (colour map, range, tilt, hold, speed).
9. **IN-C and IN-D, CPU graph and device previews (C, D).** The smallest; they can go with IN-M or IN-G.

## Open questions for the user

- Whether L2 (the history) should also sit in the loudness pop-up next to L1. The page treats L as one pick.
- K-system (M4) could be a menu choice beside any M pick rather than a design of its own.

## The user's picks (27 November 2026, 15:08 Brussels)

`My picks: M2 | L2 | S2 | O0 O1 O4 | G1 G3 G4 | E3 | V1 map viridis | C1 | D1`

- L2 (loudness history) replaces L1.
- O0 keeps today's stereo and scope drawing as one kept view; O1 (marks and afterglow) and O4 (polar view as an extra menu choice) are added to it.
- The Visualizer's colour map is viridis.

Built by task IN (lane E), one step per run in the implementation order above: IN-A, IN-M, IN-L, IN-S, IN-E, IN-G, IN-O, IN-V, IN-C/IN-D.

## Added from the mixing research picks (AE3, 27 Nov 2026, 21:07 Brussels)

After the current order, lane E adds (read `docs/research-mixing.md`, picks and notes at its end): **IN-X17** band listen on any spectrum (the filter comes from lane K, MX-4), **IN-X19** low-band correlation on the meters, **IN-X25** the user's own target band drawn in the existing loudness history (pick L2, IN-L): no second loudness view.
