# AudioLab Pro design directions: scientific and beyond (task DR3, 27 November 2026)

Pick page: **"AudioLab design directions: scientific and beyond"**, https://claude.ai/artifact/3AgiFL32Qgf29NQ6WfRW9F

The user's words (27 Nov): "Maybe you can do some extra design, deep research, specifically for like this scientific type, maybe other types of design."

**Nothing in index.html or desktop/ was changed.** No version bump. Reference version: v0.228. This task runs in parallel with DR2 (design round 2: arrangement, piano roll, browser and transport), and it does not pick component details for those surfaces. It compares whole looks. Where a direction is chosen, DR2's component picks are drawn in that look (section 6). DR2's own page and research: `docs/design-round-2.md` (recommendations A3 P3 B3 T2, drawn in the subtle scientific look, which matches DS7 here).

Files: `tools/design-lab/dr3/directions.html` (the pick page source), `today-v0228.jpg` (reference screenshot used on the page), `shots_today.py` (headless screenshots of today's app), `check.py` (headless check of the page at 1280 × 720, 1920 × 1080, 400 px, in Dark, Light mode and Bright), `today/` (screenshots of v0.228).

## 1. Summary

- **Recommendation ★: DS7 "Liquid glass science"** with the details `G2 W3 L2 A2 M1 N2`. The paste line is `DR3 picks: DS7 | G2 W3 L2 A2 M1 N2`.
  - This is today's AudioLab finished, not replaced. It keeps everything the user already chose: the glass engine, Inter on the strict scale, today's colours, flat-bar fader, half pan dial, stereo field, sideways device titles and the atom logo.
  - It places the science language only where something is measured:
    - a graticule in lanes and displays (G2);
    - three line weights by role, √2 apart as in ISO 128 (W3);
    - amber mono units (L2, which is the M1 detail already picked);
    - yellow to select, amber to measure (A2);
    - motion only for signal (M1);
    - today's density (N2).
  - It is also the cheapest change to build, because most of it is already queued (MD1, SC-H to SC-J, D4).
- **Worth borrowing from other directions:**
  - DS2 Lab instrument for device displays: a graticule, and one channel colour repeated on the trace, knob ring and meter.
  - DS1 Mission control for status (fixed colour meanings and a read-out bar).
  - DS3 Observatory for the spectrum: a perceptual colour map, and optionally colour by register.
  - DS4 Blueprint for measurement overlays (calipers, dimension lines).
- **Best kept as themes or for special views:**
  - DS4 Blueprint, DS5 Phosphor and DS3 Observatory as whole looks. They are striking but tiring for hours.
  - DS6 Swiss data as the basis for a Bright theme.
  - DS8 Industrial calm is the friendly contrast. Notably, Braun's ET66 already uses yellow for the one key pressed most, which supports AudioLab's yellow accent.
- **What the research says most clearly:**
  - Real science software is plain, dense text with units on a mid-dark ground. Glow and complexity are film devices.
  - Colour should carry one fixed meaning, and always come with a second cue.
  - Use perceptual colour maps, not rainbows.
  - Motion in the corner of the eye always pulls attention.
  - In Chromium, `backdrop-filter` and canvas `shadowBlur` are the expensive effects. A glow drawn as a line stroked twice is cheap.

## 2. What was looked at first

- **Read:**
  - `docs/glass-engine-plan.md` section 1: the round 1 picks A0 B0 C1 D3 E0 F4 G2 H0, what must stay, and the philosophy "smart and sciencey, clear, intuitive, snappy".
  - `docs/design-language-research.md` (round 1).
  - `docs/science-look.md` and `docs/science-look-round-2.md`.
  - The project doc `claude/audiolab-science-picks.md`. Splash is random among S2, S5, S1, S7 and S6. About is Earth E2/E7 with rule Y1. M1, M2 and M3 are all picked. Round 2 picked W1, W2, W4 to W13 and X1, X2, X4 to X12, X14, X15.
  - `docs/devices-display-first.md` (DD1 to DD4).
- **Headless screenshots of v0.228** (`tools/design-lab/dr3/today/`, arrangement, playing and mixer at 1280 × 720 and 1920 × 1080):
  - Layout: track headers about 210 px wide, tracks about 96 px high at 1080p, the devices panel about 260 px, the transport 48 px.
  - Colours:
    - Ground near-black, `#0a0a0c`.
    - Track colours red, blue, yellow, orange, green and violet.
    - The compressor curve is yellow on a black display.
  - The headless machine has no GPU, so the app chose its solid glass level.
- **The page redraws one AudioLab screen at these proportions.** It is 1200 app px wide:
  - a tab bar;
  - a ruler with section markers;
  - five tracks (Kick, Bass, Hat, Lead, Pad) with clips over bars 5 to 28;
  - Pro EQ as a display-first device with its sideways title and a floating knob dock;
  - four mixer strips and the master;
  - the transport.

## 3. Research by area

How claims are marked: claims with a link come from pages that research helpers opened on 27 Nov 2026. "(snippet)" means only a search result was seen. "(unverified)" means it is background knowledge that was not checked. All CPU costs are estimates unless measured on the page (section 5).

### A1. Space agencies and mission operations

- **NASA Graphics Standards Manual (1975, Danne & Blackburn)** ([PDF, NASA](https://www.nasa.gov/wp-content/uploads/2015/01/nasa_graphics_manual_nhb_1430-2_jan_1976.pdf)):
  - The logotype strokes are "all of one width, evoking the qualities of unity and technical precision".
  - Type is Helvetica Light and Medium.
  - The grid is "a predetermined understructure", with one, two or three columns by publication type.
  - Pastels are discouraged.
  - NASA red is for white or light grounds only, never on black.
  - NASA red is Pantone 179, about `#E03C31` ([Wikipedia](https://en.wikipedia.org/wiki/NASA_insignia)).
  - The 2015 reissue was by Smyth and Reed ([designboom](https://www.designboom.com/design/hamish-smyth-jesse-reed-nasa-identity-guidelines-09-27-2015/)).
  - **Image:** a white page with a wide outer margin, a small red worm top left and Helvetica text hung in columns.
  - **For AudioLab:** grid discipline and the one-width line. It also gives the warning that a saturated red on dark needs a lighter tint.
  - **Cost:** none.
- **JPL operations and Eyes on the Solar System:**
  - The Space Flight Operations Facility has run since 1958, in its building since 1963, with consoles, video displays and projection screens ([NPS](https://www.nps.gov/articles/space-flight-operations-facility.htm)).
  - Eyes on the Solar System was rebuilt in 2022 as a browser app with 126 spacecraft ([JPL](https://www.jpl.nasa.gov/news/explore-the-solar-system-with-nasas-new-and-improved-3d-eyes/)).
  - The "Dark Room" nickname is unverified.
- **NASA Open MCT** is the closest model to AudioLab. It is a browser framework built at Ames with JPL, and missions have used it ([about](https://nasa.github.io/openmct/about-open-mct)).
  - **Layout:** stacked plots share one time axis; real-time and fixed time modes; yellow and red limits ([user guide](https://nasa.github.io/openmct/docs/static/files/Open_MCT_Users_Guide.pdf)).
  - **Espresso theme** ([theme file](https://cdn.jsdelivr.net/npm/openmct@4.3.0-rc1/src/styles/_constants-espresso.scss)):

    | Token | Value |
    |---|---|
    | Background | `#2c2c2c` |
    | Text | `#acacac` |
    | Key colour | `#03ace4` |
    | Limit red (background / text) | `#940000` / `#ffa489` |
    | Limit yellow | `#b18b05` |
    | Info / alert / error | `#60ba7b` / `#ffb66c` / `#da0004` |

  - **Snow (light) theme:** `#fcfcfc` on `#666` ([theme file](https://cdn.jsdelivr.net/npm/openmct@4.3.0-rc1/src/styles/_constants-snow.scss)).
  - **Severity colours are still debated.** An open issue proposes ordering them by the visible spectrum and calls cyan over-saturated ([issue 7673](https://github.com/nasa/openmct/issues/7673)).
  - **Image:** a charcoal screen tiled with stacked strip plots on one time axis. A value cell turns dark red with a pink number when it passes a limit.
  - **For AudioLab:** tracks are stacked plots on a shared time axis already. Colour only for limits (clipping, overs). A mid-dark ground, not black.
  - **Cost:** low for the chrome. Plots belong on canvas.
- **ESA / ESOC:** a circle of workstations under wall screens with ground tracks and telemetry ([ESA](https://www.esa.int/ESA_Multimedia/Images/2026/09/Main_Control_Room_at_ESA_s_ESOC)).
- **SpaceX Dragon:**
  - "Chromium in this context is used as a UI rendering engine only." Web components run on a custom reactive framework ([InfoQ, from a SpaceX AMA](https://www.infoq.com/news/2020/06/javascript-spacex-dragon/)).
  - There are three touchscreens and a row of critical physical buttons ([The Drive](https://www.thedrive.com/news/22887/the-spacex-dragon-capsule-has-controls-like-a-tesla)).
  - The crew helped tune touch registration ([Space.com](https://www.space.com/spacex-crew-dragon-touchscreen-astronaut-thoughts.html)).
  - **Lesson:** a science-grade UI in Chromium is normal. Keep the critical actions on keys.

### A2. CERN control rooms and event displays

- **CERN Control Centre:**
  - Four islands: PS/Booster, SPS, LHC and technical infrastructure.
  - Wall monitors show beam quality, intensity and cooling.
  - At least two operators work per island ([Symmetry](https://www.symmetrymagazine.org/article/march-2015/inside-the-cern-control-centre)).
- **ATLAS colour code** ([IPPOG masterclass](https://ippog-masterclasses-website.web.cern.ch/en/wpath_3D_particleid3.htm)):
  - inner-detector tracks yellow-green;
  - calorimeter deposits green;
  - muon hits blue;
  - jets purple cones;
  - missing energy a red dashed line.
- **Phoenix** is the browser event display, built on three.js ([GitHub](https://github.com/HSF/phoenix)). The views are wireframe, fish-eye and cross-section, with palettes chosen so that objects stay distinct ([CERN Courier](https://cerncourier.com/a/event-displays-in-motion/)).
- **Image:** a black field, a pale grey wireframe detector, yellow-green helices fanning out from the centre, and purple jet cones.
- **For AudioLab:** a dark ground, thin grey structure and a few saturated hues by category. This suits signal types (audio, MIDI, automation, sidechain), which the cable system already colours. 3D belongs in About or idle views only.
- **Cost:** flat is light. three.js that animates all the time is high.

### A3. Hubble and Webb imaging

- **Chromatic ordering:** "The shortest wavelengths are assigned blue", "the longest wavelengths are assigned red". Purple, teal and orange are added for extra filters ([NASA, how Webb's colour images are made](https://science.nasa.gov/mission/webb/science-overview/science-explainers/how-are-webbs-full-color-images-made)).
  - NIRCam F070W to F200W are shown violet to cyan, F200W to F356W green and yellow, and F356W to F444W orange and red.
  - Raw frames hold over 65,000 grey levels and look almost black until a non-linear "stretch".
- **Joe DePasquale** prefers "representative color" to "false color", and warns against oversaturating ([NASA Gravity Assist](https://www.nasa.gov/mediacast/gravity-assist-how-we-make-webb-and-hubble-images)). Travis Rector: for broadband filters "one main rule… chromatic ordering" ([Physics Today](https://physicstoday.aip.org/news/bringing-jwst-images-to-life)).
- **Image:** Webb's Cosmic Cliffs, an orange-brown ridge of gas under a blue, star-speckled sky.
- **For AudioLab:**
  - Order colour by frequency: low red to high violet. DS3 does this for tracks by register.
  - Use a log or asinh stretch for meters and spectrograms.
  - Keep nebula pictures out of working areas. The splash and About already use them.
- **Cost:** a colour-map lookup costs nothing. Animated nebula shaders are high.

### A4. Scientific plotting

- **Tufte:** data-ink ratio is data ink divided by total ink, and chartjunk "should be removed, within reason" ([data.europa.eu](https://data.europa.eu/apps/data-visualisation-guide/chart-junk-and-data-ink-origins)). Sparklines and small multiples are unverified detail.
- **viridis, magma, inferno and plasma** were presented by van der Walt and Smith at SciPy 2015. They are perceptually uniform, colour-blind friendly and survive greyscale ([viridis vignette](https://cran.r-project.org/web/packages/viridis/vignettes/intro-to-viridis.html)).
- **cividis** is viridis optimised for deuteranomaly, running straight from blue to yellow ([Nuñez et al. 2018](https://pmc.ncbi.nlm.nih.gov/articles/PMC6070163)).
- **Crameri, Shephard and Heron 2020:**
  - Rainbow maps "visually distort data through uneven colour gradients".
  - About 8 % of men and 0.5 % of women have a colour-vision deficiency.
  - Always show a colour bar ([Nature Communications](https://pmc.ncbi.nlm.nih.gov/articles/PMC7595127)).
- **ColorBrewer** (Brewer, 2002) offers sequential, diverging and qualitative schemes with colour-blind-safe options ([Wikipedia](https://en.wikipedia.org/wiki/ColorBrewer)).
- **Observable Plot defaults:** turbo for continuous data, observable10 for categories, RdBu for diverging data ([Plot scales](https://observablehq.github.io/plot/features/scales)).
- **For AudioLab:**
  - magma or viridis for spectrograms (DS3 uses magma for the spectrum and meters);
  - a categorical track palette with matched lightness;
  - hairline grids;
  - direct labels instead of legends.
- **Cost:** none.

### A5. Oscilloscopes and lab instruments

- **Tektronix default channel colours** (2 to 6 Series): CH1 yellow, CH2 cyan, CH3 red, CH4 green, CH5 orange, CH6 blue, CH7 magenta, CH8 mint ([Tektronix FAQ](https://tek.com.cn/support/faqs/what-are-the-default-channel-colors)). DS2 uses this order.
- **Keysight InfiniiVision:** "each analog channel's information appears in a different color", with 256 intensity levels ([user's guide](https://tjr-lab.mit.edu/wp-content/uploads/2023/09/Keysight-InfiniiVision-4000-X-Series-Oscilloscopes-Users-Guide.pdf)). The exact Keysight colour order is unverified.
- **Rohde & Schwarz MXO 4** ([brochure](https://scdn.rohde-schwarz.com/ur/pws/dl_downloads/pdm/cl_brochures_and_datasheets/product_brochure/3609_8473_12/MXO-4_bro_en_3609-8473-12_v0900.pdf)):
  - a 13.3" touch display;
  - signal icons in a lower-left bar;
  - dialogs as left-hand tabs that leave room for waveforms;
  - keys and knobs colour-coded to their sources;
  - a learning curve claimed to be under 15 minutes.
- **Phosphors, from HP AN-25** ([PDF](https://www.qsl.net/iv3cve/hp/an/pdf/an_25.pdf)): P1 green; P31 blue-green with green afterglow; P7 blue-white with yellow afterglow.
- **The 10 × 8 division graticule** with 5 minor ticks is unverified detail, though it is the common scope layout.
- **Image:** a yellow CH1 sine and a cyan CH2 square wave on black, with small coloured channel tags at the left edge and a measurement bar at the bottom.
- **For AudioLab:** one track, one colour, on the header tag, clip, meter, knob ring and read-out. Add a graticule and a read-out bar on displays.
- **Cost:** a static graticule is free. Persistence (an accumulating canvas) is moderate.

### A6. Synth panels

- **Moog:** a 1967 901 oscillator is in the Smithsonian ([Smithsonian](https://www.si.edu/object/moog-voltage-controlled-oscillator%3Anmah_609212)). The black panels with white legends are unverified, though well known.
- **Buchla 200e jack colours** encode direction and signal type: orange pulse in, red pulse out, black or grey CV in, blue/green/purple CV out ([sdiy wiki](https://sdiy.info/wiki/Banana_jack_colour_codes)). Audio uses 3.5 mm sockets and CV uses banana sockets, so they cannot be cross-patched ([Sound On Sound](https://www.soundonsound.com/reviews/buchla-200e-part-1)).
- **For AudioLab:** colour by signal type and direction fits the cable system (audio, sidechain, automation, MIDI, with input and output shades).

### A7. Swiss / International style and technical drawing

- **Müller-Brockmann:**
  - *Grid Systems in Graphic Design*, 1981.
  - First Tonhalle poster in 1950, later the "Musica Viva" series.
  - Akzidenz-Grotesk; "shapes and other geometric elements… without illustration" ([Wikipedia](https://en.wikipedia.org/wiki/Josef_M%C3%BCller-Brockmann)).
  - The posters "evoke the very sounds of music by visual equivalents… the most complete freedom within the rigid system of the grid" ([Socks Studio](https://socks-studio.com/2016/11/30/joseph-muller-brockmann-musica-viva-posters-for-the-zurich-tonhalle/)).
  - Whitespace "can never be underrated" ([Smashing](https://www.smashingmagazine.com/2009/07/17/lessons-from-swiss-style-graphic-design/)).
  - **Image:** arcs and rings of flat colour in a rhythmic grid on black, with a small block of flush-left type.
- **ISO 128-20 line widths:** 0.13, 0.18, 0.25, 0.35, 0.5, 0.7, 1, 1.4 and 2 mm, a ratio of about √2. Extra-wide, wide and narrow are 4 : 2 : 1 ([ISO sample](https://cdn.standards.iteh.ai/samples/1408/f62555427b87436eafe1e6abc5271860/ISO-128-20-1996.pdf)).
- **Other drawing standards:**
  - ISO 3098 lettering heights from 1.8 to 20 mm ([Roymech](https://www.roymech.co.uk/Useful_Tables/Drawing/Lettering.html)).
  - ISO 7200 title blocks ([Wikipedia](https://en.wikipedia.org/wiki/ISO_7200)).
  - Blueprints come from Herschel in 1842: Prussian blue with white lines, replaced by diazo prints in the 1940s and then CAD ([Wikipedia](https://en.wikipedia.org/wiki/Blueprint)).
- **For AudioLab:**
  - a √2 weight ladder (W3);
  - dimension-line styling for the caliper (M3) and loop braces;
  - flush-left labels and two or three sizes (already C1).
  - Poster-scale whitespace belongs in About and Settings.

### A8. Braun, Teenage Engineering, Leica

- **Rams' ten principles** include "unobtrusive" and "as little design as possible" ([Vitsoe](https://www.vitsoe.com/gb/about/good-design)).
- **Braun ET66 (1987):** black number keys, brown operator keys and a yellow "=" key, so the eye goes to "the most frequently used function" ([V&A](https://collections.vam.ac.uk/item/O1360553)). AudioLab's yellow accent for the main action follows the same rule.
- **T3 radio,** 1958 ([Core77](https://www.core77.com/posts/24768/a-history-of-braun-design-part-3-audio-products-24768)).
- **OP-1:** "A green graphical element… hints that the green encoder will change its value" ([TE guide](https://teenage.engineering/guides/op-1/original/layout)). The original's encoders are blue, green, white and orange; the OP-1 field has darker blue, ochre, grey and orange ([Perfect Circuit](https://perfectcircuit.com/signal/teenage-engineering-op-1-field-review)).
- **Leica M11:** a quick-access strip on the first Menu press and the full menu on the second ([PetaPixel](https://petapixel.com/2022/01/13/leica-m11-first-impressions-review/)).
- **For AudioLab:**
  - a neutral body with one accent per function;
  - knobs mapped to screen graphics by colour. This fits display-first devices, where the dock knob and its handle on the picture would share a colour;
  - a two-level menu.

### A9. Glass cockpits, HUDs, medical monitors, Bloomberg

- **FAA AC 25-11B colour meanings** ([PDF](https://www.faa.gov/documentLibrary/media/Advisory_Circular/AC_25-11B.pdf)):

  | Colour | Meaning |
  |---|---|
  | Red | Warnings and limit exceedances |
  | Amber | Cautions |
  | Magenta | "Fly to" targets |
  | Cyan | Armed modes and selected data |
  | Green | Engaged modes |
  | White | Scales |

  - "Good practice to use six colors or less."
  - "If color is used for coding, at least one other distinctive coding parameter should be used."
  - Red, blue and magenta on black are listed as pairs to avoid.
- **HUD:** the green comes from the combiner coating, and collimation means no refocusing ([Flying](https://www.flyingmag.com/how-it-works-head-up-display/)).
- **Patient monitors:**
  - "There are no agreed upon standards" for parameter colours. An example scheme is HR green, arterial pressure red, SpO₂ yellow and CO₂ white. About 10 % of men are red-green colour-blind, so position and waveform shape must also identify a parameter ([APSF](https://www.apsf.org/article/colors-for-ecg-tracings-spo2-pulse-oximetry-on-patient-monitors-in-the-or-and-icu/)).
  - Alarm flashing from one maker's manual: high priority red at 1.4 to 2.8 Hz; medium yellow at 0.4 to 0.8 Hz; low steady ([Edan iM50 manual](https://www.manualslib.com/manual/2874758/Edan-Im50.html?page=54)).
  - **For AudioLab:** "number plus waveform in the same colour, fixed position" fits meters. Flashing is for clipping or a lost device only.
- **Bloomberg Terminal:**
  - "We're hiding complexity" across thousands of functions; changes ship gradually and can be switched on and off ([Bloomberg](https://www.bloomberg.com/company/stories/how-bloomberg-terminal-ux-designers-conceal-complexity)).
  - Alternative colour schemes exist for deuteranopia and protanomaly ([Bloomberg UX](https://www.bloomberg.com/ux/accessibility/)).
  - The first terminal used a monochrome CRT and colour-coded keys ([IEEE Spectrum](https://spectrum.ieee.org/bloomberg-terminal)).
  - **For AudioLab:** the lessons are about process (change slowly, keep a way back, offer colour-blind schemes) more than about the amber look.

### A10. Film and game interfaces

- **The Martian (Territory Studio):**
  - More than 400 screens. Gridnik type for Mission Control, JPL and the Hermes. Modular widgets from watch size to a 9 × 3 m wall ([Pushing Pixels](https://www.pushing-pixels.org/?p=11034), [Fonts In Use](https://fontsinuse.com/uses/10500/the-martian-ui-graphics)).
  - The real NASA screen was "a spreadsheet of events".
  - **Lesson:** a modular widget system and standardised sizes. Gridnik-like monoline numerals read well small.
- **Prometheus and Blade Runner 2049:** confusion used as a futuristic device, and organic optical textures ([Pushing Pixels](https://www.pushing-pixels.org/?p=9769), [AWN](https://awn.com/vfxworld/communicating-abstract-user-interfaces-blade-runner-2049)). Not for a working tool.
- **Oblivion (GMUNK and team):**
  - The light table was mostly captured in camera.
  - The goals were "functionality and minimalism"; a palette that reads on dark and light ([GMUNK](https://gmunk.com/OBLIVION-GFX)).
  - The best film reference for a Bright theme: hairlines and restraint.
- **Interstellar:** a "utilitarian, functional, NASA style design" based on Shuttle screens, futuristic to us and dated to the crew ([VProFX](https://vprofx.squarespace.com/blog/interstellar)). The right tone for a tool.
- **The Expanse:**
  - The in-house team was led by Sumeet Vats.
  - Each ship has its own style guide; NASA and military guidelines were used as sources; the star maps have a faint distance grid ([HUDS+GUIS](https://www.hudsandguis.com/home/2021/theexpanse)).
  - **Lesson:** per-view style guides, and a faint grid as a background.
- **Arrival:** circular logograms ([MPA](https://motionpictures.org/?p=7187)), with Wolfram Language code behind the analysis screens ([Wolfram blog](https://blog.wolfram.com/2017/01/31/analyzing-and-translating-an-alien-language-arrival-logograms-and-the-wolfram-language/)).
- **Alien (1979):**
  - Ordinary CRTs for a "beaten-up" ship.
  - Ron Cobb's Semiotic Standard icons ([Typeset in the Future](https://typesetinthefuture.com/2014/12/01/alien/)).
  - **Lesson:** a bold pictographic icon set reads well small. Green phosphor is for accents only.
- **Gravity:** real engineering as "purely functional non-design design" ([KCRW](https://www.kcrw.com/shows/design-and-architecture/stories/andy-nicholson-gravity)).
- **General lessons:**
  - Blue dominates film UIs because blue reads as "unnatural, future" ([99% Invisible](https://99percentinvisible.org/episode/future-screens-are-mostly-blue/)).
  - Film screens are "an illustration and a storytelling device"; real software aims to be simple; every screen needs an instant "read"; motion should answer where am I, how did I get here and where can I go ([Mark Coleran](https://www.pushing-pixels.org/?p=18414)).
- **Elite Dangerous:**
  - The orange HUD is recoloured by a 3 × 3 matrix in a config file ([PC Gamer](https://www.pcgamer.com/how-to-change-the-colour-of-your-ships-hud-in-elite-dangerous), [Arkku's editor](https://arkku.com/elite/hud_editor)).
  - Players complain about neon orange over long play (snippet: [Frontier forum](https://forums.frontier.co.uk/threads/a-hud-colour-modification-that-works-in-odyssey-reduces-neon-orange.583790)).
  - **Lesson:** one remap recolours everything, which is how AudioLab's theme tokens should work.
- **KSP 2:**
  - Interaction is "a series of tiny trust falls" ([dev diary](https://kerbalspaceprogram.com/news/dev-diaries-developer-insights-7-ksp-2-ux-architects)).
  - Players praised tape indicators, and criticised pixel fonts, low-contrast secondary numbers and wrong SI capitals ([forum](https://forum.kerbalspaceprogram.com/topic/210240-the-new-ui-for-ksp2-improvements-and-regressions-from-previous-concepts)).
  - **Lesson:** this supports X9 (proper units).

### A11. Audio software that already leans scientific

- **iZotope Insight 2:**
  - a 3D spectrogram;
  - BS.1770 loudness (momentary, short-term, integrated, LRA);
  - a Sound Field display ([iZotope](https://izotope.com/products/insight)).
  - Sound On Sound found Insight 1's subdued look "easy on the eye" for long sessions, with a loudness history that turns red above target ([SOS](https://www.soundonsound.com/node/4903554)).
- **FabFilter Pro-Q 4:**
  - The analyser is the canvas: ranges of 60, 90 and 120 dB, tilt 4.5 dB per octave by default, spectrum grab, and collision glow between instances ([FabFilter](https://www.fabfilter.com/help/pro-q/using/analyzer)).
  - It adds accessible colours, more subdued colours than Pro-Q 3, and a scaling option ([SOS](https://www.soundonsound.com/reviews/fabfilter-pro-q-4?amp)).
  - **Lesson:** display-first (already G2 / DD), a 4.5 dB per octave tilt, and collision marks.
- **Voxengo SPAN:** correlation, K-system, true-peak and clipping statistics, EBU R128, colour schemes ([Voxengo](https://voxengo.com/product/span/features)). **Lesson:** a plain statistics block under the plot, like the DS1 and DS2 read-out bars.
- **MeldaProduction:** styles from "vintage hardware" to futuristic; frame rate adjustable "up to 100" fps ([MAnalyzer](https://meldaproduction.com/MAnalyzer/features), [GUI engine](https://meldaproduction.com/about/technology/gui-engine)). **Lesson:** a frame-rate cap per display; one curated look rather than unlimited styles.
- **Bitwig Grid:**
  - Signal colours by type: logic yellow, phase purple, pitch orange, untyped red.
  - The stereo scope draws the left channel in the cable colour and the right in white ([Bitwig](https://www.bitwig.com/userguide/latest/on_grid_signals)).
- **VCV Rack:**
  - Panels are 128.5 mm by multiples of 5.08 mm. Outputs sit on an inverted dark background. Text must be readable at 100 % on a non-HiDPI screen ([VCV manual](https://vcvrack.com/manual/Panel)).
  - "Prefer dark panels" arrived in 2.4.0, with light and dark SVGs per module ([VCV community](https://community.vcvrack.com/t/vcv-rack-2-4-0-released/20372)).

### B. Other directions compared

| Direction | What defines it | For hours of use | Cost in a browser (estimate) |
|---|---|---|---|
| **Apple Liquid Glass and visionOS** | Lensing is "the primary way Liquid Glass visually defines itself". There are two variants, never mixed; no glass in the content layer, no glass on glass; Reduce Transparency and Reduce Motion are respected ([WWDC25 talk 219](https://developer.apple.com/videos/play/wwdc2025/219/), [HIG materials](https://developer.apple.com/design/human-interface-guidelines/materials)). visionOS windows use one fixed glass material and have no dark mode. | Good when kept to the control layer, which AudioLab's rules already do. Moving content under glass keeps changing the chrome. | High with CSS `backdrop-filter`; AudioLab solved this with its own GL engine. |
| **Brutalist and neo-brutalist** | Thick borders, solid offset shadows, primary colours ([NN/g, April 2025](https://www.nngroup.com/articles/neobrutalism/)). Gumroad's 2021 redesign replaced about 140 CSS files with 40 components ([Gumroad](https://gumroad.com/blog/behind-gumroads-new-design-system)). | Large saturated areas tire in a dim room. NN/g warns of weak hierarchy and unclear interactivity. Only the honesty (flat fills, crisp rules) carries over. | Very low. |
| **Skeuomorphic DAWs (Reason, UAD)** | Rendered hardware. Reason flips the rack with Tab to show cables ([Reason manual](https://docs.propellerheads.se/reason9/RoutingAudioAndCV.15.5.html)). "A circular control is extremely difficult to operate precisely with a mouse" ([The Outline](https://theoutline.com/post/2157/why-are-there-so-many-knobs-in-garage-band)). | Familiar but noisy. Bitmaps blur at fractional scaling. Round-1 research already advised against photo-real panels. | Low when still; medium with animated cables. |
| **Minimal monochrome (Linear, OP-1 field)** | Linear moved its themes to LCH, built from three variables (base, accent, contrast) instead of 98, and reduced blue in the chrome ([Linear](https://linear.app/blog/how-we-redesigned-the-linear-ui)). It recommends a design reset every 2 to 3 years ([Linear](https://linear.app/blog/a-design-reset)). | Probably the best for long sessions; the risk is grey-on-grey below readable contrast. | Very low. |
| **Retro-futurist (CRT, vector)** | Phosphors: P1 green 525 nm, P3 amber 602 nm, P31 yellow-green ([Wikipedia](https://en.wikipedia.org/wiki/Phosphor)). Vector screens redraw 30 to 40 times a second ([Wikipedia](https://en.wikipedia.org/wiki/Vector_monitor)); the Vectrex used colour overlays ([Wikipedia](https://en.wikipedia.org/wiki/Vectrex)). | Simulated flicker and bloom raise fatigue and halation. | High for real shaders: CRT-Royale is a problem "for all but monster GPU's" ([libretro](https://docs.libretro.com/shader/crt_royale/)); Blur Busters' simulator needs 240 Hz or more ([Blur Busters](https://blurbusters.com/crt)). |
| **Organic and generative** | Nervous System's Floraform simulates "a differentially growing elastic surface" ([Ars Electronica](https://starts-prize.aec.at/floraform)). Refik Anadol's Unsupervised at MoMA is live generative imagery ([MoMA](https://www.moma.org/collection/works/442077)). | Constant motion in the periphery; only for splash, idle or About. AudioLab's science drawings already follow this rule. | Medium to high and continuous unless throttled or drawn once. |
| **Editorial Swiss** | See A7. | The grid and type hierarchy carry over; poster whitespace does not. | Very low. |

### C. Evidence on long sessions

- **Polarity.** Dark text on light gives better proofreading of small text, and the gain grows as text shrinks from 14 to 8 pt. Pupils are smaller and acuity is better, in young and old readers ([Piepenbrock, Düsseldorf 2014](https://docserv.uni-duesseldorf.de/servlets/DerivateServlet/Derivate-31413); Ergonomics 2013 and 2014). The preferred explanation is higher display luminance.
  - Glance reading at night favoured dark text on light (snippet: [Dobres et al. 2017](https://pubmed.ncbi.nlm.nih.gov/28166901/)).
  - NN/g: light mode generally performs better; they found no fatigue difference; offer dark as a choice ([NN/g](https://www.nngroup.com/articles/dark-mode/)).
  - **For AudioLab:** used in dim studios, so dark stays the default. That makes larger text, not-quite-white text and a Bright theme worth having.
- **Halation.** About half of people have at least 0.5 D of astigmatism. White on pure black fuzzes, and contrast checkers do not catch it ([Level Access](https://www.levelaccess.com/blog/accessibility-for-people-with-astigmatism/)). Every direction on the page uses off-white text, and glow is limited to DS2, DS3 and DS5.
- **Chromostereopsis.** Red tends to float in front of blue on a dark surround ([Wikipedia](https://en.wikipedia.org/wiki/Chromostereopsis)). Avoid saturated red text on blue clips or tracks.
- **APCA.** WCAG 2 "far overstates contrast for dark colors". Use Lc 90 for body text and Lc 75 as the minimum for larger text ([APCA, Why APCA](https://www.github.com/Myndex/SAPC-APCA/blob/master/documentation/WhyAPCA.md)). Check dark-theme greys with APCA.
- **Motion in the periphery** (Bartram, Ware and Calvert 2003, [PDF](https://www.interruptions.net/literature/Bartram-IJHCS03.pdf)):
  - Motion was detected almost always, far out in the field of view, in about 1 s. Colour detection errors rose from 5.5 % near the point of focus to 24 % far from it.
  - Travelling motion distracted most; slow linear motion least.
  - **For AudioLab:** M1 is the default, and M3 (ambient) stays optional.
- **Flicker.** IEEE 1789 sets a no-observable-effect level of 0.03 × frequency modulation, for example 3.6 % at 120 Hz (reported by the US DOE, [energy.gov](https://www.energy.gov/cmei/ssl/flicker-measurement-and-standards)). Never simulate CRT flicker.

### D. Chromium rendering costs

- **`backdrop-filter`:** "may harm performance" ([web.dev](https://web.dev/articles/backdrop-filter)).
  - It is called "the most expensive effect in the compositor": it always uses a saveLayer, and a backdrop over changing content redraws the whole surface ([Grida notes on Chromium](https://grida.co/docs/wg/research/chromium/effect-optimizations)).
  - This is why AudioLab's GL engine exists.
- **CSS `filter: blur`:** a naive animated blur measured about 90 ms a frame. The fix is pre-rendered blur stages cross-faded with opacity ([Chrome blog](https://developer.chrome.com/blog/animated-blur)).
- **Canvas:**
  - "Avoid the `shadowBlur` property whenever possible." Use layered canvases, pre-render to an offscreen canvas, and use whole-pixel coordinates ([MDN](https://developer.mozilla.org/en-US/docs/Web/API/Canvas_API/Tutorial/Optimizing_canvas)).
  - Batch paths and avoid state changes ([web.dev](https://web.dev/articles/canvas-performance)).
  - A glow drawn as a wide, faint line under a thin bright line costs two path strokes and no convolution. No primary source was found for this technique; it is reasoning, and the page measures it (section 5).
- **Layers:**
  - Only `transform` and `opacity` skip layout and paint. Every layer costs memory, so do not promote elements needlessly ([web.dev](https://web.dev/articles/stick-to-compositor-only-properties-and-manage-layer-count)).
  - `will-change` is "a last resort" ([MDN](https://developer.mozilla.org/en-US/docs/Web/CSS/will-change)).
- **`OffscreenCanvas`** moves drawing to a worker ([web.dev](https://web.dev/articles/offscreen-canvas)). It is worth it for meters and analysers when the main thread is busy.

## 4. The eight directions

All eight are drawn on the same screen (section 2), in Dark, Light mode (no glass, no glow, no ambient motion) and Bright. Every one keeps the atom logo, the layout, the flat-bar fader, the half pan dial with its faint stereo field, the stereo field display on the master, the sideways device title and the display-first device.

| Code | Name | Its own details | Colours (change from today?) | Hours of use | Cost |
|---|---|---|---|---|---|
| DS1 | Mission control | G4 dots, W1, L3 capitals, own accent (cyan selection), M1, N3 dense | **Changes:** charcoal ground, muted track colours, cyan selection; amber and red only for limits | Good; capitals slow in long lists | Low |
| DS2 | Lab instrument | G2, W3, L4 mono, A3 channel colours, M1, N2 | **Changes:** Tektronix channel colours for tracks, black lanes, grey bezel | Calm up close; arrangement structure harder to see from far out | Low to medium (double-stroke glow) |
| DS3 | Observatory | G5, W1, L1, A1, M3 ambient, N1 roomy | **Changes:** tracks coloured by register, red to violet; magma spectrum | Beautiful, lowest contrast; ambient motion pulls the eye | Low |
| DS4 | Blueprint | G3 drafting, W3, L4, A4 redline, M1, N2 | **Changes:** Prussian blue ground and white ink; track colour only as a tag | Tiring for hours; good for overlays | Very low |
| DS5 | Phosphor (contrast) | G2, W2, L4, A4, M2, N2 | **Changes:** one green; tracks by brightness and dash | Poor for hours | Medium (glow everywhere, scanlines) |
| DS6 | Swiss data | G5, W1, L1, A4 Swiss red, M1, N1 | Keeps track colours; panels lose surfaces; red selection | Very readable; controls look less clickable | Lowest |
| **DS7 ★** | **Liquid glass science** | **G2, W3, L2, A2, M1, N2** | **Keeps today's colours**; amber for measurements | Good; today's contrast | As today (GL engine) |
| DS8 | Industrial calm (contrast) | G1, W2, L1, A1, M2, N1 | **Changes:** warm graphite, OP-1 field-like track set; keeps yellow | Very calm; can look muddy | Very low |

Mixable details on the page:

| Group | Options | ★ |
|---|---|---|
| Grid | G1 Today, G2 Graticule, G3 Drafting, G4 Dots, G5 Swiss | G2 |
| Lines | W1 Hairline, W2 Standard, W3 Drafting weights | W3 |
| Labels | L1 Sentence case, L2 Amber units, L3 Tracked capitals, L4 Technical mono | L2 |
| Accent | A1 Yellow selection, A2 Yellow and amber, A3 Channel colours, A4 Mono and one red | A2 |
| Motion | M1 Signal only, M2 Signal and transitions, M3 Ambient | M1 |
| Density | N1 Roomy (76 px tracks), N2 Today (62 px at this size), N3 Dense (48 px) | N2 |

A detail overrides the direction's own choice, and the mix preview shows the result live. The picks bar builds `DR3 picks: <direction> | <details> | note: <text>`.

## 5. Checked

- **Headless Chromium**, via `tools/design-lab/dr3/check.py`, with the page wrapped in the artifact skeleton:
  - Sizes: 1280 × 720 and 1920 × 1080 in Dark, plus 1280 × 720 in Bright and Light mode, plus 400 × 800.
  - No console errors. No sideways page scroll at any size.
  - Every direction was screenshotted at 1280 px. "Take all ★" gives `DR3 picks: DS7 | G2 W3 L2 A2 M1 N2`.
- **Drawing time per frame** (playhead, transport text, five meters, stereo field, spectrum and display), cloud machine, software renderer, averaged over 1.5 s, two runs:

  | Direction | Run 1 (ms) | Run 2 (ms) |
  |---|---|---|
  | DS1 | 0.48 | 0.72 |
  | DS2 | 0.27 | 0.80 |
  | DS3 | 0.60 | 0.61 |
  | DS4 | 0.26 | 0.56 |
  | DS5 | 0.27 | 0.38 |
  | DS6 | 0.23 | 0.62 |
  | DS7 | 0.28 | 0.36 |
  | DS8 | 0.42 | 0.50 |

  - All are well under 1 ms. The differences between directions are inside the run-to-run noise.
  - The lanes, grid, clips and the display's grid and curve are drawn once, when the screen is built. Per frame, only the playhead (moved with a transform), the meters and the spectrum are drawn.
  - The CSS blur (DS7's glass stand-in) and DS5's scanline layer cost compositor time, which this number does not include.
- **Not checked:** the user's Mac with a real GPU. Fonts came from fallbacks in the cloud run, because the Google Fonts host may not be reachable there.

**Honest limits:**
- The screens are redrawn approximations at AudioLab's sizes, not the app's own drawing code.
- The flat-bar fader is drawn from its description.
- The glass is CSS blur, not the GL engine.
- The today reference is a headless screenshot at the solid glass level.

## 6. How a chosen direction would be rolled out over the queued tasks

The same order works for any direction. Only the values change. Nothing starts until the user pastes a line.

1. **DL0, look tokens (before or with MD1).**
   - One small `LOOK` object, together with CSS custom properties at the top of the style block, holds:
     - grid style;
     - the three line weights;
     - label style (fonts and case for labels, values and units);
     - accent roles (`--sel`, `--meas`, limit colours);
     - motion level;
     - density.
   - Every canvas drawer (arrangement, devices, mixer meters, science drawings) reads from it instead of literals.
   - No visible change at first. This is round 1's planned token layer, extended to the canvas.
2. **MD1, measurement details** (already queued): read-outs with units, orbit loader, caliper. Build them on `LOOK`; L2 and A2 are exactly M1's amber units. Add X9 (units and prefixes) to the same number formatter (SC-H).
3. **DR2 (design round 2, running in parallel).** Its arrangement, piano roll, browser and transport picks are drawn in the chosen direction's values:
   - the arrangement grid style (G) and line weights (W);
   - piano roll lanes with the same graticule;
   - transport read-outs in the label style.
   - X4 (ruler levels) belongs here (SC-J).
4. **D4 display-first devices** (picked, not started): each device display gets the direction's display grid (G2 graticule for DS7) and the selected-band label with its note (X8). With DS2-style details, also the channel-colour rule (dock knob ring and picture handle share a colour) and the read-out bar.
5. **Mixer (SC-I and SC-K):**
   - fader tick scales with the index mark (X1, as on the page);
   - knob rings (X2);
   - change while dragging (X6);
   - meter style from the direction;
   - the signal path line (X10, shown in DS7's transport).
6. **Science drawings (SC-A to SC-G):**
   - Colour and line weight come from `LOOK`, so the splash and About drawings, empty states and waiting windows share the arrangement's line weights and amber.
   - M3 ambient motion only ever runs where the SC rules already allow motion: empty states and waiting.
7. **Bright and Light mode.**
   - Light mode stays the low-power path (no glass, no glow, no ambient motion), as on the page.
   - If a Bright theme is wanted, it is the same tokens with the Bright values; DS6 or DS7 Bright are the starting points.
8. **If a different direction is picked:**
   - DS1, DS2 and DS3 change the palette or track-colour rule. They ship behind a "New look (preview)" switch, as round 1 planned, so old and new can be compared on the user's own projects.
   - DS4 and DS5 are best offered as themes in Appearance.
   - DS6 and DS8 are mainly token values plus a few CSS rules (surfaces, button shapes).

Each step is one index.html task with the usual release routine, a headless test with screenshots, and a frame-time check.

## 7. Sources

Every link above was opened by research helpers on 27 November 2026, unless the text marks it "(snippet)" or "(unverified)". Pages that refused automated reading:
- PubMed Central and Mannheim MADOC (bot checks);
- MoMA work 7233;
- the KSP navball wiki;
- the DOE flicker page (its claims are cited as the helper reported them).

## The user's picks (27 November 2026, 14:43 Brussels)

`DR3 picks: (no direction) | G3 W1 L2 A1 M3 N3`

No single direction: today's colours and look stay, with these details everywhere: G3 drafting grid, W1 hairline lines, L2 amber units, A1 yellow selection, M3 ambient motion (only where motion is already allowed: empty and waiting states; Light mode stays without it), N3 dense (track rows about 48 px where today's are 62 px on the page). Built first as the look tokens of section 6 step 1 (task LK, lane A, after GS4), then used by design round 2 (task DS), MD1, SC and DV. Where a more specific pick covers the same thing (design round 2's AG2 grid detail, the arrangement-lines round), the specific pick decides that surface and the tokens supply its line weights and colours.
