# AudioLab for long sessions (task UX2, 27 November 2026)

Interface research, second of three parallel tasks (UX1 speed and feel, **UX2 long sessions**, UX3 first use and help), asked for by the user on 27 Nov at 20:02 Brussels. Research only: `index.html`, `desktop/` and `native/` are untouched.

- Pick page: **"AudioLab for long sessions"**, https://claude.ai/artifact/3e9BvwsCHanzjGSka4QtUH (source `tools/design-lab/ux2/long-sessions.html`, images in `tools/design-lab/ux2/img/`).
- Measurements and scripts: `tools/design-lab/ux2/` (`shoot_measure.py`, `contrast.py`, `cvd.py`, `oled.py`, `check.py`; raw output in `measure/`).

## 1. Summary

The user mixes for hours, mostly at night, in Dark, on a 32-inch QD-OLED (Samsung Odyssey OLED G8, G80SD) at 2194 × 1139 points (1.75×). Measured on today's app (v0.263, Fractals demo, at exactly that size):

1. **Small grey text is too faint.** 90 % of the text is 11 px. Half of all text runs (240 of 496) are under APCA Lc 60 and 27 % under Lc 45, the floor APCA gives for small labels. The single most used text colour is the quiet grey `#80838f` (84 runs) at Lc 33 to 40. Four texts fail every guideline: the white folder arrow on a yellow track strip (Lc 15, 1.3:1), the peak "max" read-out (Lc 29), the mixer's cable legend (Lc 29) and canvas tick labels drawn in `LOOK.tick` (9 px, Lc 18).
2. **Track colours collapse for colour-blind users.** Simulated protanopia makes today's blue `#4c8dff` and violet `#b583ff` identical (CIEDE2000 ΔE 1.0); deuteranopia merges yellow and orange (5.8), tritanopia green and cyan (5.9). Clip bodies (36 % over the lane) go down to ΔE 0.4. About 1 in 12 men has a red-green deficiency.
3. **Dark AudioLab is easy on the OLED panel** (average picture level 4.8 %, 1.6 % of the screen above half white). The remaining risk is a handful of bright parts that never move: the full-colour number strips, white fader caps and pan marks, the 100 % white map box and the help line (4.3 % of the screen bright and static). The bright Pro Tools style theme is a different story: APL 32 %, 48 % of the screen bright and static.
4. **Motion is concentrated in the mixer and the Follow page turn.** Stopped: 0.015 % of pixels change per 125 ms. Playing: 0.21 %. With the mixer open: 6.3 % per step and 42 % of the screen within 3 s. A Follow page turn changes 39 % of the screen at once.
5. **The G80SD itself is flicker-free** (no PWM); what the monitor does for burn-in (Pixel Shift, Screen Optimization after 4 h in standby) works best if users know about it.

Strongest options on the page (five stars): **E2** quiet grey at the APCA content floor with weight 500, **E4** fix the four failing texts, **E6** today's eight colours tuned apart (worst pair ΔE 1.0 → 12.3 for any deficiency, same look), **E10** static brights at 70 %, **E20** follow macOS Reduce motion and Dim flashing lights, **E21** a Comfort group in Settings › Appearance. Four-star: E3 text size setting, E8 number and texture on clips, E11 dim when idle, E13 OLED care card, E14 night brightness and warmth, E15 focus mode, E16 listen mode, E18 calm displays.

Nothing here changes the standing picks (today's colours, buttons and icons, Inter 11/12/13/15, the glass engine, G3, W1, L2, A1, M3, N3). The options are refinements, defaults and settings.

## 2. How it was measured

All with headless Chromium on the app's own `index.html`, viewport 2194 × 1139 at device scale 1.75, the Fractals demo open, AudioLab theme, full glass.

- **Contrast** (`shoot_measure.py`, `contrast.py`): every visible text node, its computed colour, size, weight and opacity; the background read from the screenshot (most common colour around and inside the text box, excluding pixels near the text colour), so glass and transparency count. WCAG 2 contrast ratio and APCA-W3 0.0.98G Lc. Three states: Dark (AudioLab theme), Light mode (the lighter graphics mode; AudioLab has no light colour theme) and the bright Pro Tools style theme. Canvas text (ruler, displays) from the colour values in `LOOK`, `TH` and `INS`.
- **Physical size**: 3840 px over 708.5 mm, 1.75 device px per point: 1 point = 0.32 mm. Inter x-height 0.546 em. Viewing distance 70 cm.
- **Colour vision** (`cvd.py`): Machado, Oliveira and Fernandes 2009, severity 1.0, in linear sRGB; CIEDE2000 between every pair of the eight track colours, as the clip edge (full colour) and as the clip body (36 % over the lane `#1a1f26`).
- **Motion**: 24 screenshots 125 ms apart, share of pixels changed by more than 12 of 255, stopped, playing, playing with the mixer open, and a Follow page turn.
- **OLED** (`oled.py`): average picture level (mean linear luminance), share above 25 % and 50 % luminance, and the bright pixels outside the "changed while playing" mask, grouped into regions.

Caveat: the cloud machine renders with SwiftShader; colours and layout are exact, frame timing is not used here.

## 3. Measurements

### 3.1 Text contrast

| State | Text runs | Below 4.5:1 | Below Lc 60 | Below Lc 45 | Below Lc 30 | Median abs(Lc) |
|---|---|---|---|---|---|---|
| Dark (AudioLab theme, glass) | 496 | 97 (20 %) | 240 (48 %) | 136 (27 %) | 4 | 69.7 |
| Light mode | 346 | 9 | 133 (38 %) | 47 | 5 | 74.4 |
| Pro Tools style (bright) | 329 | 27 | 135 (41 %) | 51 | 12 | 74.4 |

Weakest texts (Dark):

| Text | Where | Size | Colours | WCAG | Lc |
|---|---|---|---|---|---|
| ▸ folder arrow | yellow track strip | 11/600 | `#e6e8ee` on `#f5c84c` | 1.29 | -15 |
| max -∞ | transport peak read-out | 11/500 | `#6d7384` on `#090a0d` | 4.18 | -29 |
| Arrows point where the sound goes… | mixer legend | 11/600 | `#6f7482` on `#101215` | 4.02 | -29 |
| Selected only | mixer legend | 11/600 | `#777b85` on `#101215` | 4.43 | -32 |
| Sends | mixer strip | 11/600 | `#7d8292` on `#29261f` | 3.94 | -33 |
| +6, 0, -6 … | mixer fader scale | 11/600 | `#80838f` on `#242629` | 4.01 | -33 |
| LOOK.tick labels (canvas) | display scales | 9/500 | white at 32 % on `#0b0c10` | 2.83 | -18 |
| Ruler bar numbers (canvas) | ruler | 11/500 | `#b0b4ba` on `#272b31` | 6.63 | -56 |

The two greys: `#80838f` reads Lc -33 on a mixer strip, -36 on a panel; `#8b8b97` (`--mut`, `LOOK.mut`) -37 to -40. Candidates: `#9a9eab` Lc -47 to -50, `#adb1bd` Lc -57 to -60, `#c4c7d1` Lc -70 to -73. Ink `#ececf1` is Lc -92 to -95.

### 3.2 Text sizes

| Size | Runs | Device px | Cap height | x-height | at 70 cm |
|---|---|---|---|---|---|
| 7 px (▲▼ steppers) | 4 | 12.3 | | | |
| 9 px (canvas labels) | | 15.8 | 2.11 mm | 1.59 mm | 7.8′ |
| 9.5 px (amber units) | 8 | 16.6 | 2.23 mm | 1.67 mm | 8.2′ |
| 11 px | 445 (90 %) | 19.2 | 2.58 mm | 1.94 mm | 9.5′ |
| 12 px | 28 | 21.0 | 2.82 mm | 2.12 mm | 10.4′ |
| 13 / 15 px | 7 / 2 | 22.8 / 26.2 | 3.05 / 3.52 mm | 2.29 / 2.64 mm | 11.3′ / 13.0′ |

### 3.3 Track colours under colour-vision deficiency

Smallest CIEDE2000 between any two of the eight colours, edge / body:

| Palette | Normal | Protan | Deutan | Tritan | Closest |
|---|---|---|---|---|---|
| Today `#4c8dff #3ecf8e #f5c84c #ff6b6b #ff9a3c #b583ff #4cc9f0 #ff7ac8` | 18.6 / 11.1 | **1.0 / 0.4** | 5.8 / 3.0 | 5.9 / 3.0 | blue and violet (protan) |
| E6 tuned `#7075ff #40ad81 #ffec39 #f3413f #e8ab4b #afabff #8de6f1 #d867a7` | 16.8 / 8.1 | 14.2 / 7.4 | 12.3 / 7.4 | 13.4 / 7.5 | yellow and amber (deutan) |
| E7 Okabe-Ito lifted `#56b4e9 #14b386 #f0e442 #e2661c #eea52b #d78fb8 #3f7fd9 #c8c8d0` | 17.8 / 9.4 | 9.7 / 4.9 | 8.7 / 4.4 | 7.4 / 3.7 | sky blue and green (tritan) |
| Okabe-Ito as published | 21.1 / 8.1 | 12.2 / 5.9 | 11.6 / 5.5 | 10.9 / 5.1 | |

E6 was found by random hill climbing in OKLCH with each colour held within 16° of hue, 0.09 of lightness and 0.035 of chroma of today's, maximising the smallest distance over all four visions, edges and bodies. A side effect: its yellow `#ffec39` moves away from the selection yellow `#f5c84c` (A1), which today is the same colour as track yellow.

### 3.4 Motion

| State | Changed per 125 ms | Changed within 3 s |
|---|---|---|
| Stopped | 0.015 % | 0.06 % |
| Playing, arrangement | 0.21 % | 1.9 % |
| Playing, mixer open | 6.3 % | 41.7 % |
| Follow page turn (zoomed in) | 8.9 % average, 39 % in the turn frame | 39.2 % |

### 3.5 OLED load

| State | Average picture level | Above 50 % white | Bright and static |
|---|---|---|---|
| Dark arrangement | 4.84 % | 1.57 % | 4.31 % |
| Dark with mixer | 4.22 % | 1.39 % | |
| Light mode | 4.09 % | 1.19 % | 3.42 % |
| Pro Tools style | 32.0 % | 31.9 % | 47.8 % |

Largest bright static regions in Dark: the number strips (full height, 45 % luminance), the help line and map (75 %), clip title rows of clips that do not scroll. The mock on the pick page reproduces the picture level within 0.7 points (4.2 % against 4.8 %).

## 4. Findings with sources

**Eyes, screens and light**
- Blue-light-filtering lenses may give no short-term benefit for eye strain (17 RCTs, low certainty). [Cochrane CD013244](https://www.cochrane.org/CD013244/EYES_do-blue-light-filtering-spectacle-lenses-reduce-digital-eye-strain), [PubMed 37593770](https://pubmed.ncbi.nlm.nih.gov/37593770/)
- The AAO does not recommend blue-blocking glasses; it advises blinking, 20-20-20, arm's-length distance and adjusting brightness and contrast to comfort. [AAO](https://aao.org/newsroom/news-releases/detail/protect-your-eyes-in-home-office)
- Blink rate drops about five-fold at a screen. [Optom Vis Sci 1991](https://pubmed.ncbi.nlm.nih.gov/1766652/); [AAO EyeWiki](https://eyewiki.aao.org/Computer_Vision_Syndrome_(Digital_Eye_Strain))
- Matching screen and surroundings (about 3:1) and bias lighting are plausible comfort advice, from vendor and office-lighting guidance, not trials. [BenQ](https://www.benq.com/en-us/knowledge-center/knowledge/behind-monitor-lighting); soft diffuse light in a studio, anecdotal: [Sound On Sound](https://www.soundonsound.com/people/why-love-mood-lighting)

**Flicker and the G80SD**
- Flicker-free, no PWM; a small refresh-synchronous ripple not visible in use. VRR flicker can appear in near-black areas when the frame rate swings; "VRR Control" reduces it. Typical SDR brightness about 250 nits, minimum 19, no ABL in SDR. [TFTCentral review](https://tftcentral.co.uk/reviews/samsung-odyssey-g80sd), [TFTCentral on OLED flicker](https://tftcentral.co.uk/articles/helping-avoid-oled-burn-in-and-flicker-exploring-the-latest-asus-oled-technologies-for-2025)
- For AudioLab: a steady frame rate (the frame cap in Settings › Performance) avoids VRR flicker in dark areas; nothing in the app should simulate flicker.
- IEEE 1789 is for LED lighting, now inactive-reserved. [IEEE](https://standards.ieee.org/ieee/1789/4479/)

**Dark mode**
- Positive polarity (dark on light) gives better acuity and proofreading, most of all for small text; the advantage is due to higher luminance. [Piepenbrock et al., Uni Mannheim](https://madoc.bib.uni-mannheim.de/26118/)
- Light mode won for glance reading under night-time lighting; no difference by day; NN/g: offer dark, do not force it. [NN/g](https://www.nngroup.com/articles/dark-mode/), [Dobres et al. 2017](https://pubmed.ncbi.nlm.nih.gov/28166901/)
- The better polarity varies by person, and preference often does not match it. [While and Sarvghad 2024](https://arxiv.org/html/2409.10841v1)
- Light text on black can smear for people with astigmatism (practitioner claim). [BOIA](https://www.boia.org/blog/dark-mode-can-improve-text-readability-but-not-for-everyone)
- Dark mode saves 3-9 % power on OLED at 30-50 % brightness. [Purdue](https://www.purdue.edu/newsroom/releases/2021/Q3/dark-mode-may-not-save-your-phones-battery-life-as-much-as-you-think,-but-there-are-a-few-silver-linings.html)
- For AudioLab: dark stays the default (dim rooms, OLED), with off-white text (already `#ececf1`), contrast enough for small text (E2, E4), and a brightness control (E14).

**OLED burn-in and static UI**
- Samsung (G80SD): Screen Optimization runs automatically after 4 or more hours of cumulative use, with the monitor off (standby), 10-15 minutes, cannot be disabled, stops if the power is cut; Pixel Refresh by hand (over an hour); Pixel Shift on by default; Adjust Logo Brightness. [Samsung support](https://www.samsung.com/us/support/troubleshoot/TSG10003240/), [Samsung CA image shift](https://www.samsung.com/ca/support/displays/how-to-solve-image-shift-issues-on-your-samsung-oled-monitor/)
- OLED Safeguard+: heat pipe cooling and brightness lowered by predicted temperature; logo and taskbar brightness reduced; screen saver after 10 minutes idle; burn-in covered by warranty. [Samsung G80SD](https://www.samsung.com/us/monitors/gaming/odyssey-oled-g8-g80sd-32-inch-240hz-oled-uhd-ls32dg800snxza/). TFTCentral found only logo dimming and the pixel clean cycle in its unit's menu (firmware may differ). [TFTCentral](https://tftcentral.co.uk/reviews/samsung-odyssey-g80sd)
- Pixel shift amount is not published by Samsung; Dell's QD-OLED moves 1 px every 3 minutes. [Dell](https://www.dell.com/support/kbdoc/en-us/000197755/Alienware-34-Curved-Oled-Monitor-Aw3423dw-Pixel-Shift-Pixel-Orbiter). For AudioLab: no pixel shift of our own (the monitor does it; two shifts would fight and move hairlines off the pixel grid, against W1).
- RTINGS' torture test (static CNN feed, 126.5 h/week, maximum brightness): burn-in on QD-OLED by 2,000 h; on all OLED monitors by two years. [PC Gamer](https://pcgamer.com/rtings-latest-oled-monitor-burn-in-tests-are-not-good-news-for-samsung), [Tom's Hardware](https://www.tomshardware.com/monitors/large-scale-simulated-10-year-torture-test-confirms-burn-in-haunts-all-oled-monitors-testing-also-reveals-edge-lit-tvs-are-insanely-failure-prone), [TFTCentral](https://tftcentral.co.uk/articles/oled-and-qd-oled-image-retention-and-burn-in-longevity-testing)
- Desktop use, 32-inch 4K QD-OLED, 6,000 h at about 60 h/week in light mode: faint marks where the taskbar and a window edge sat; green subpixels wore most. [PC Gamer, Monitors Unboxed](https://www.pcgamer.com/hardware/gaming-monitors/after-two-years-and-over-6-000-hours-monitors-unboxeds-long-term-oled-gaming-monitor-test-shows-increasing-burn-in)
- Vendor advice: auto-hide the taskbar, moderate brightness, keep pixel shift and panel care on. [MSI](https://www.msi.com/blog/how-to-use-msi-oled-monitors-for-productivity-essential-tips-to-prevent-burn-In). macOS: "Automatically hide and show the Dock" and the menu bar. [Apple Dock](https://support.apple.com/en-gb/guide/mac-help/-mchlp1119/mac), [Apple menu bar](https://support.apple.com/en-au/guide/mac-help/-mchlad96d366/mac)

**Type and contrast**
- macOS: default 13 pt, minimum 10 pt; Subheadline 11/14; avoid light weights at small sizes; more tracking below 12 pt (+6/1000 em at 11 pt). [Apple HIG Typography](https://developer.apple.com/design/human-interface-guidelines/typography)
- APCA: Lc 90 preferred for body text, 75 minimum, 60 for other content text, 45 for large or non-body text, 30 for spot text, 15 invisible for some; WCAG 2 is "largely meaningless for dark mode". [APCA introduction](https://github.com/Myndex/apca-introduction), [Bronze simple mode](https://a11yreadtech.github.io/ARC/tests/bronze-simple-mode)
- WCAG 2.2: 4.5:1 text, 3:1 large text and UI components. [1.4.3](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html), [1.4.11](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html)
- Inter text cut: tall x-height for small sizes; `tnum` and the disambiguation features (`cv05`, `cv08`, `zero`) help read values. [rsms.me/inter](https://rsms.me/inter/)

**Colour vision**
- Red-green deficiency 2-8 % of men, about 0.5 % of women; tritan about 1 in 500. [Simunovic, Eye 2010](https://www.nature.com/articles/eye2009251); by type, deuteranomaly 5 % of men is the most common. [WebExhibits](https://webexhibits.org/causesofcolor/2C.html)
- Okabe-Ito palette. [NYU Siegal lab](https://siegal.bio.nyu.edu/color-palette/); cividis. [PNNL](https://www.pnnl.gov/publications/optimizing-colormaps-consideration-color-vision-deficiency-enable-accurate); simulation model. [Machado et al. 2009](https://www.inf.ufrgs.br/~oliveira/pubs_files/CVD_Simulation/CVD_Simulation.html)
- Colour must not be the only cue. [WCAG 1.4.1](https://www.w3.org/WAI/WCAG22/Understanding/use-of-color.html)

**Motion**
- Animation from interactions should be possible to turn off (vestibular symptoms). [WCAG 2.3.3](https://www.w3.org/WAI/WCAG22/Understanding/animation-from-interactions.html); `prefers-reduced-motion` [MDN](https://developer.mozilla.org/en-US/docs/Web/CSS/@media/prefers-reduced-motion); macOS Motion settings: Reduce motion, Dim flashing lights, Prefer non-blinking cursor [Apple](https://support.apple.com/guide/mac-help/mchla3c4f1da/mac)
- About 35 % of US adults over 40 show vestibular dysfunction (NHANES). [MDedge](https://mdedge.com/content/vestibular-dysfunction-common-after-age-40)
- Motion onset captures attention; moving items are searched first. [Abrams and Christ 2003](https://pubmed.ncbi.nlm.nih.gov/12930472/), [Franconeri and Simons 2005](https://link.springer.com/content/pdf/10.3758/BF03193623.pdf); peripheral motion detected in about 1 s (Bartram, Ware and Calvert 2003, in docs/design-languages-research.md section C).

**Quiet modes in other apps**
- Live 12, Settings › Theme & Colors: light/dark/follow OS, warm, cool or neutral tone, high contrast; Customization: grid line opacity, brightness, colour intensity and hue; Reduced Automatic Colors. [Ableton manual](https://www.ableton.com/en/live-manual/12/first-steps/)
- Logic Pro: tracks background grey level, grid line visibility, region colour; hideable control bar; screensets. [Tracks view settings](https://support.apple.com/guide/logicpro/lgcp8e0207b2/mac), [control bar](https://support.apple.com/guide/logicpro/lgcp5bdd6d9d/mac), [screensets](https://support.apple.com/guide/logicpro/create-recall-and-switch-screensets-lgcp9bbbcb23/10.6/mac)
- Figma Minimize UI (⌘⇧\\) and Hide UI (⌘\\). [Figma](https://help.figma.com/hc/en-us/articles/41414918021271-Hide-or-minimize-the-UI); VS Code Zen Mode (⌘K Z), Centered Layout. [VS Code](https://code.visualstudio.com/docs/configure/custom-layout); Premiere Appearance Brightness. [Adobe](https://helpx.adobe.com/premiere-pro-next/learn-the-basics/configure-preferences/appearance-preferences.html); Bitwig Dashboard › User Interface: Contrast. [Bitwig](https://www.bitwig.com/userguide/latest/the_dashboard/); DaVinci Resolve full-screen timeline and viewer (no dim UI setting found). [Larry Jordan](https://larryjordan.com/articles/how-to-zoom-the-viewer-full-screen-in-davinci-resolve-20/)

**Long mixing nights**
- Mix at about 70 dB; break about every hour, away from the screen; turning up is a sign of fatigue (Dom Morley). [Production Expert](https://www.production-expert.com/production-expert-1/ear-fatigue-top-mixer-gives-advice-on-how-to-deal-with-it)
- 10 minutes off every hour or 20 every 90. [iZotope](https://www.izotope.com/en/learn/how-to-prevent-ear-fatigue-when-mixing-audio); NIOSH 85 dBA over 8 h, 3 dB exchange. [CDC NIOSH](https://www.cdc.gov/niosh/noise/prevent/understand.html)
- Colourful waveform screens pull attention from listening; show less or close your eyes. [Sound On Sound](https://www.soundonsound.com/people/sounding-focus-listening); decide by ear, confirm with meters, except loudness specs. [Production Expert](https://www.production-expert.com/production-expert-1/mixing-with-eyes-or-ears-which-is-best)
- No AES standard on control-room screen brightness was found.

## 5. Options (as on the pick page)

Stars are this task's judgement for hours of use on the user's screen. One of E1/E2 and one of E6/E7.

| # | Option | Stars | Measured effect |
|---|---|---|---|
| **Contrast and text** ||||
| E1 | Quiet grey one step lighter: `#9a9eab` | ★★★ | Lc -34 → -48 on a mixer strip |
| E2 | Quiet grey `#adb1bd` and weight 500 for 11 px grey text | ★★★★★ | Lc -34 → -58; ink stays Lc -93 |
| E3 | Text size setting: Standard 11/12/13/15 or Large 12/13/15/17 (text only) | ★★★★ | x-height 9.5′ → 10.4′ |
| E4 | Fix the four failing texts (strip glyphs pick dark or light ink; hint, Sends, legend, max read-out to the quiet grey; tick labels use LOOK.mut) | ★★★★★ | folder arrow Lc -15 → 76; max read-out -29 → -60 |
| E5 | Contrast: Standard or High | ★★★ | grey Lc -34 → -71 |
| **Colour-blind safe track colours** ||||
| E6 | Today's eight colours tuned apart | ★★★★★ | worst edge pair 1.0 → 12.3 |
| E7 | Okabe-Ito lifted for dark, as a palette choice | ★★★ | worst edge pair 7.4 |
| E8 | Second cue on clips: track number chip and one of four light textures | ★★★★ | colour no longer the only cue (WCAG 1.4.1) |
| E9 | "See as" colour-vision preview (Normal, Protan, Deutan, Tritan) | ★★★ | one CSS filter |
| **OLED care** ||||
| E10 | Static brights at 70 %: 5 px colour edge on the number strip, number in the track colour; white caps and marks `#c9ccd4`; map box 55 %; Follow pill darker | ★★★★★ | bright share in the mock 2.5 → 2.1 % |
| E11 | Dim when idle (10 min, not while playing or recording, any input wakes) | ★★★★ | APL 4.2 → 0.4 % when idle |
| E12 | Help line and map hide until the pointer reaches the bottom | ★★★ | fixed text and the white box off screen; +103 pt |
| E13 | OLED care card in Settings (monitor's own features, macOS auto-hide, E10-E12) | ★★★★ | text only |
| **Night and focus modes** ||||
| E14 | Night: brightness (100-50 %) and warmth, optional schedule | ★★★★ | APL 4.2 → 2.7 %, contrast ratios kept |
| E15 | Focus mode: arrangement, transport and map only | ★★★★ | moving pixels 0.97 → 0.12 % per step |
| E16 | Listen mode: meters and displays rest, warnings still light | ★★★★ | moving pixels 0.95 → 0.07 % per step |
| E17 | Session clock and optional break reminder (60 or 90 min) | ★★★ | one timer |
| **Motion and visual noise** ||||
| E18 | Calm displays: IEC fall (20 dB in 1.7 s), 1.5 s peak hold, 30 fps, spectra averaged over 300 ms | ★★★★ | moving pixels 0.95 → 0.67 % per step (mixer docked) |
| E19 | Calmer Follow page turns (turn at 90 %, keep the last fifth in view, no turns while editing) | ★★★ | today a turn changes 39 % at once |
| E20 | Follow macOS Reduce motion and Dim flashing lights | ★★★★★ | no cost |
| **Settings to add** ||||
| E21 | A Comfort group in Settings › Appearance | ★★★★★ | about 8 rows, in the settings search |
| E22 | Comfort presets Day, Night, Focus | ★★★ | Night: APL 4.2 → 2.6 % |

Moving-pixel numbers in this table are measured on the page's mock (quarter size), so compare them with each other; the app's own measured values are in section 3.

## 6. Proposed tasks and lanes

Lanes as in CLAUDE.md. Several options change a shared value (the quiet grey, the palette): those need the scheduling chat because the rule is "only add tokens, never change another lane's values".

| Task | Options | Lane | Notes |
|---|---|---|---|
| UX2-T Text tokens | E1 or E2, E3, E5 | **LK tokens** (new tokens `--mut2`, a weight token, a text-size step and a high-contrast set), then each lane switches its greys to the token | Changes a value everybody reads: schedule it as one step, then lanes A, E, F, G adopt it in their next task. Settings rows by lane B. |
| UX2-F Fix failing texts | E4 | A (strips, group lanes), E (peak read-out, tick labels), the mixer owner ("Sends", legend) | Small; each lane in its own area |
| UX2-P Palette | E6 (or E7), E8, E9 | A (`PAL`, clip drawing, number chip and texture), B (theme palette, colour choice, See as) | New projects only; existing projects keep their colours unless recoloured |
| UX2-O OLED care | E10, E11, E12, E13 | A (strip, map, Follow pill), F (idle dim, help line), B (card), I (device frames if any bright static part) | Idle dim needs a hook from the transport (playing or recording) |
| UX2-N Night and focus | E14, E15, E16, E17 | B (settings), F (window filter, break card), H (commands for Focus and Listen keys), E (displays read the Listen flag), A (layout, session clock) | Brightness as one filter outside the glass engine's backdrop; check its cost on the Mac |
| UX2-M Motion | E18, E19, E20 | E (meter ballistics, spectrum averaging), A (Follow), LK and F (motion token, OS settings) | E18 also lowers drawing cost |
| UX2-S Comfort group | E21, E22 | B (ST) | Last, once the switches exist |

## 7. Files

- `tools/design-lab/ux2/long-sessions.html`: the pick page (self-contained but for `img/`).
- `tools/design-lab/ux2/shoot_measure.py`, `contrast.py`, `cvd.py`, `oled.py`: measurements; `check.py`: headless check of the page.
- `tools/design-lab/ux2/measure/`: the raw output (text runs, contrast, CVD, motion, OLED).
- `tools/design-lab/ux2/img/`: screenshots of today, simulated colour vision, the static-bright and motion maps.

## The user's picks

(waiting: paste the line from the page's picks bar, for example `UX2 picks: E2 E4 E6 E10 E20 E21`)
