# AudioLab Pro design language: research and round 1 (task AM, 26 November 2026)

User's words: "Let's do deep research to improve the design language. Learn from the Figma pages about their design, and similar modern, beautiful designs like that, and start mixing it with the whole design that AudioLab has. We're going to tweak the whole design language to make everything look a little better. [...] come back and start creating small little test UIs that I can pick from, just in the same way that we designed the logo. And then we'll slowly start implementing it."

**Status: round 1 is out for picking. Nothing in the app was changed** (index.html, desktop/ and VERSION untouched; v0.214 is the reference).

- Pick page: "AudioLab design language, round 1", https://claude.ai/artifact/KrC2VeKQC3EDbLpEkoMmnN (self-contained HTML, 8 areas, 46 test UIs, switch for Dark / Light mode (no glass) / Bright theme, picks collect in a bar at the bottom).
- How to answer: one number per area (for example "A3, B1, C1, D2, E2, F1, G1, H1"), or "mix" with what to combine. Then round 2 narrows it, or implementation starts in small steps.

## 1. Proposed direction in one paragraph

**"Calm glass."** Take Figma UI3's calm (work in the centre, quiet chrome, grouping by space instead of lines, one icon set, labels that give full context) for every surface the user works *in*, and keep AudioLab's glass for what *floats over the music*: track headers the lanes slide under, the transport, menus, pills and floating windows. Carry the Ocean Yellow logo into the app as the palette: darks tinted slightly ocean blue, yellow as the one accent for selection and the main action, green only for play, red only for record. Keep Inter, on a strict four-size scale. Put all of it into a small set of design tokens first, so the look can be changed in one place and rolled out surface by surface.

Why this and not "all glass" or "all Figma": Figma itself shipped floating panels in the UI3 beta and took them back because they cramped small screens, distracted, and slowed people down; Apple's own guidance says glass belongs to the control layer, never the content layer, and must be used sparingly; Linear skipped refraction in dense UI for legibility. AudioLab's glass is its identity and its liquid-glass work is done, so it stays, but only where those three sources agree it works.

## 2. Round 1 options and recommendations

★ = recommended. 0 is always today's look.

| Area | Options | ★ |
|---|---|---|
| **A Overall direction** | A0 Today · A1 Today refined (same layout, one radius, flat buttons, yellow accent) · A2 UI3 calm (solid graphite, almost no lines, floating transport) · A3 Calm glass (UI3 calm on working surfaces, glass on what floats, ocean darks, yellow) · A4 Hardware warm (warm charcoal, amber, tactile knobs, capital labels) · A5 Dense studio (smaller type, square corners, six tracks where others show four) | **A3** |
| **B Colour and contrast** | B0 Today (green accent, blue selection) · B1 Ocean Yellow (ocean-tinted darks, yellow accent, green for play only) · B2 Graphite (pure neutral greys, yellow the only colour) · B3 Warm charcoal (brownish darks, cream text, amber) · B4 High contrast (true black, white text, stronger lines) | **B1** (B4 fits as an optional switch on top) |
| **C Typography** | C0 Today (Inter 13/11, capital section labels, mono values) · C1 Inter strict scale (11/12/13/15, three weights, equal-width digits, mono only for time) · C2 Geist + Geist Mono · C3 IBM Plex Sans + Mono · C4 Space Grotesk titles + JetBrains Mono capital labels | **C1** |
| **D Panels and surfaces** | D0 Today (glass panels, solid black-edged menus) · D1 Flat layers (no blur, one grey step per layer) · D2 Two levels (working panels solid, floating things glass with a light rim, corners 12/7 nested) · D3 Full glass (everything floats, 16 px corners) · D4 Raised solids (no glass, three shadow steps) | **D2** |
| **E Buttons, toggles, tabs, menus** | E0 Today (bevelled, 3 px, blue when on) · E1 Quiet (outline and plain text) · E2 Soft filled (flat tonal fills, 6 px, yellow main button with dark text, tab marked by a yellow line, mute orange, solo blue) · E3 Glass capsules · E4 Hardware keys | **E2** |
| **F Mixer strip** | F0 Today · F1 Calm strip (short colour tab, no outlines, bigger fader handle, wider meters) · F2 Console (long caps, LED segments) · F3 Dense (40 px strips) · F4 Glass strips | **F1** |
| **G Device frame and header** | G0 Today · G1 Calm frame (no outline or header line, display on top, knobs in a row with label and value) · G2 Display first (display fills the device, knobs float on glass) · G3 Faceplate · G4 Dense rack | **G1** (G2 is worth a second look for devices that are mostly a picture, such as Pro EQ) |
| **H Icons** | H0 Today (approximation) · H1 Outline 1.5 px, round ends · H2 Bold 2 px · H3 Solid · H4 Two-tone with yellow | **H1** |

Measured contrast of the recommended palette B1 (dark): text 17.4:1, muted text 6.8:1, dark label on the yellow main button 12.6:1. Today: 16.8:1, 5.9:1, 9.5:1. Floor is 4.5:1, target 7:1 for small text (Apple HIG, Carbon, Atlassian).

Honest limits of the test UIs: they are small sketches, the "Today" cards are redrawn from the v0.214 CSS and screenshots (close, not exact), the H0 icons are an approximation, and the glass in the sketches is plain blur without AudioLab's refraction lens.

## 3. AudioLab's look today (v0.214)

From the CSS at the top of index.html, the project docs and headless screenshots (transport, arrangement, mixer, devices panel, Settings, a menu).

- Stated idea in the CSS: "a hardware console behind frosted glass: lanes slide under glass track headers"; near-black, track colours carry meaning, green = play, blue = modes; Inter.
- Tokens that exist: `--bg #0a0a0c`, `--pn #121216`, `--pn2 #18181d`, `--ln #25252c`, `--ink #ececf1`, `--mut #8b8b97`, `--acc #3ecf8e` (green), `--blue #4c8dff`, glass `rgba(28,28,36,.5)` with `blur(18px) saturate(1.6)`, glass border white 11 %. Everything else is literal values spread through about 2,750 lines of CSS.
- Buttons: bevelled gradient (#363741 to #2a2b33), black 1 px edge, 3 px radius, 26 px high. Many other radii in use (3, 6, 10, pills).
- Type: Inter 13/1.4, 11 px muted labels, capital micro-labels (TRACKS, SENDS), monospace numbers in the transport.
- Colour roles overlap: green is play, "on" lamps and the focus ring; blue is selection, modes and switched-on buttons; the logo's yellow is hardly used in the app. Yellow is also a track colour (Clap, Drums), which matters for the accent (see 5.3).
- Strong points to keep: the glass headers, the track-colour system, live device displays, the bottom map, tabular numbers, the Ocean Yellow identity, Light mode as a real low-power path.
- Weak points the new language should fix: many slightly different radii, borders and button styles; lines everywhere in the mixer and devices; no single accent; no token layer, so every change is hand work.

Note on the reference screenshots: the headless machine is slow, so AudioLab switched itself to Light mode (no blur) during the run. The glass-on look was taken from the CSS and the earlier glass docs, not re-shot.

Note on "Light": in AudioLab, Light mode is the low-power switch, not a bright colour theme. The pick page therefore has both: "Light mode (no glass)" and a "Bright theme" sketch. A bright theme does not exist in the app today beyond the theme presets.

## 4. How the logo round was run (and what this round copies)

From `claude/audiolab-app-icon-decisions.md`: ten rounds on one page, every option with a short code (KX6, PR4, W7), side by side at small size, a clear lineage from round to round, research notes kept short (60-30-10 rule, 3:1 icon contrast, test at 16 px), the user answers with a code. This round copies that: codes A0 to H4, small cards, a star per area, one-line reasons, picking by number.

## 5. Principles extracted

### 5.1 Hierarchy and density for pro tools
- The work is the hero. UI3's stated goal was to clear space so the user's work is centre stage; Raycast enlarged the input and results; FabFilter lets the interactive display fill the window with thin bars above and below.
- Dim the chrome, not the content. Linear's 2026 refresh made the sidebar dimmer, icons smaller, separators fewer and softer.
- Density should be the user's choice (Production Expert; Raycast compact mode; Ableton's mixer hides sections as it shrinks). Dense is an option, not the default.
- Do not break familiar patterns for looks: Google's Material 3 Expressive research (46 studies, 18,000+ participants) found key actions spotted up to 4x faster with stronger emphasis, but usability fell when familiar layouts were broken or text labels removed, and function-first apps should keep established patterns.

### 5.2 Panels and floating UI
- Figma UI3: floating panels in beta, then back to fixed and resizable. Reasons given: cramped on small screens, distracting when the design peeked out behind them, slower. "Speed is a feature." Floating survives where it earns it (the bottom toolbar, Minimize UI).
- Apple: Liquid Glass is for controls and navigation above content, not for content; do not stack glass on glass; bigger glass surfaces are more opaque; tint only what needs emphasis; corners concentric with their container; test with Reduce Transparency, Increase Contrast, Reduce Motion.
- Linear's glass: blur, a subtle gradient, a specular highlight and a shadow; refraction skipped for legibility; solid outlines when Increase Contrast is on.
- Geist ties radius to elevation: surfaces 6 or 12 px, tooltip 6, menu 12, modal 12, fullscreen 16, shadow rising with each level.
- For AudioLab: two levels. Solid for panels you work in (devices, mixer, Settings). Glass for what floats over the arrangement (track headers, transport, menus, pills, floating windows). This also keeps the number of glass surfaces low, which the liquid-glass performance research asked for.

### 5.3 Colour and contrast for long sessions
- One accent, one meaning (Apple: one colour should carry one meaning, never colour alone). Ableton and Bitwig: hue belongs to tracks and clips; state colours must not be confused with track colours.
- Consequence for a yellow accent: yellow is used for selection, focus and the main action only as a line, ring, soft wash or a button fill with dark text, never as a clip-like block; and the default track palette should move its yellow toward amber/gold so a selected thing and a yellow track never look alike. Mute orange, solo sky blue, record red, play green stay fixed.
- Neutrals: Linear moved from cool blue-grey to a less saturated grey and warns that too warm looks muddy; Geist uses ten-step functional scales (backgrounds, borders, text). A slight ocean tint keeps the brand without colouring the work.
- Contrast: 4.5:1 floor, 7:1 target for small text. Linear treats contrast as one dial that generates high-contrast themes; Ableton has a High Contrast toggle plus brightness and colour-intensity sliders; Bitwig has one Contrast setting. AudioLab already has background and tint sliders, so a contrast dial fits.
- Dark mode depth: higher surfaces are lighter (Apple, Carbon, Atlassian). A dark-only app is fine for media tools (Apple).

### 5.4 Typography for dense UI
- Few sizes, by role. Geist: 14 for menus, 13 secondary, 12 tertiary in busy views. Carbon's "productive" set is fixed-size for task UIs. Apple: macOS default 13, minimum 10, no thin weights.
- Tabular numbers for anything numeric (Geist); mono only where digits must line up in time.
- Goodhertz uses variable-width fonts so labels fit fixed slots; Notion gets rhythm from spacing rather than baselines.
- For AudioLab: stay on Inter (already there, nothing to load in a single-file app), four sizes 11/12/13/15, weights 400/500/600, sentence-case labels, capitals only for tiny section labels if at all.

### 5.5 Iconography
- UI3: 200 icons hand-drawn as one set; Raycast: one outline set, redrawn bolder, sharing one stroke and corner rule.
- Labels: UI3 made property labels optional and found an early minimalist version failed accessibility; the rule became "each label gives full context". Nothing essential behind hover alone.
- For AudioLab: one set on a 16 px grid, 1.5 px line, round ends; solid only for transport play/stop/record where convention expects it.

### 5.6 Spacing and radii
- A 4/8 scale: Carbon 2, 4, 8, 12, 16, 24, 32; Atlassian 0, 2, 4, 6, 8, 12, 16, 20, 24 with 0 to 8 for compact UI.
- Proposed for AudioLab: spacing 2, 4, 6, 8, 12, 16, 24; radii 4 (small controls), 6 (buttons, fields), 8 (inner panels), 12 (floating panels and menus), full (pills); nested corners concentric (outer = inner + padding).

### 5.7 Motion
- Framer: every animation serves hierarchy, feedback or spatial continuity; ease-out in, ease-in out; shorter for frequent actions; the layout must read with animation skipped.
- Apple Reduce Motion: fades instead of moves, no animating into or out of blur.
- Music tools: animate only signal and state (meters, playhead, modulation). Sound On Sound praised informative scopes and criticised decorative ones.
- No source gave durations, so these are a proposal to test: 90 ms for hover and press, 140 ms for menus and popovers, 200 ms for panels; none during playback-critical redraws.

### 5.8 Light and dark
- Apple: every custom colour needs light, dark and increased-contrast values. Carbon: token names are the same in every theme, only values change. Raycast: every theme is declared light or dark.
- For AudioLab: dark stays the main look. With role tokens, Light mode (no glass) and a possible bright theme become value sets, not separate CSS.

### 5.9 How they tested and iterated
- Figma UI3: more than a year of work; limited beta with a waitlist; anyone could switch back and was asked why; revert rate tracked over time; several decisions reversed from feedback (floating panels, a dropdown that added a click, an icon that hid state); the old UI kept until the new one was ready. Inside the team, 60-minute "speed rounds" where everyone comments at once replaced 30-minute one-to-one crits.
- Linear: explore freely under a "concept" label, stress-test every core view, a flag that toggles old and new, private beta, then a daily percentage rollout; about six weeks of build; a reset every two to three years.
- For AudioLab: the pick rounds are the concept stage; implementation behind a "New look (preview)" switch in Settings so old and new can be compared on the user's own projects and switched back at any time; surface by surface.

### 5.10 Design to code: tokens
- Correction to the brief: the Figma post "Build by design" is not about tokens. It is Dylan Field's announcement of AI and code workflows (code layers on the canvas, design-system guidelines for agents, Figma Specs, MCP). The token material is in Figma's Pattern Library and Dev Mode posts.
- Figma's UI3 library: five designers and engineers, five months, 680+ tokens, two collections: primitives (colour ramps 100 to 1000) and semantic tokens that alias them, with modes per theme. Publishing the library regenerates the CSS tokens through a GitHub Action. The migration exposed 280+ mismatches.
- Carbon and Atlassian name tokens by role, not by value (`layer-01`, `color.background.danger.bold.hovered`, `elevation.surface.raised`). The Design Tokens format reached its first stable version in October 2025 (a community report, not a W3C standard).
- For AudioLab (single file, no build step): three small tiers as CSS custom properties at the top of the style block. Primitives (`--ocean-900`, `--yellow-500`), roles (`--surface-panel`, `--surface-float`, `--text-muted`, `--accent`, `--state-solo`), and a few component tokens (`--btn-radius`, `--strip-width`). Step one of implementation is replacing literals with these tokens without changing a pixel.

## 6. What to take, and what not

| Take | From |
|---|---|
| Work centre stage, quiet chrome, grouping by space | Figma UI3, Linear, FabFilter |
| Fixed, resizable working panels; glass only on the floating layer | Figma UI3 reversal, Apple HIG |
| One accent with one meaning; state colours fixed; hue for tracks | Apple, Ableton, Bitwig |
| Role-named tokens in tiers, same names in every theme | Figma Pattern Library, Carbon, Atlassian |
| Radius tied to elevation, concentric corners | Geist, Apple |
| One icon set, one stroke | UI3, Raycast |
| A contrast dial and a high-contrast option | Linear, Ableton, Bitwig |
| Opt-in preview with a way back, feedback before removal | Figma UI3 beta, Linear |
| Display-first devices where the picture is the control | FabFilter, Bitwig |

| Leave | Why |
|---|---|
| Floating working panels | Figma tried and reverted; a DAW needs every pixel of the arrangement |
| Glass on glass, glass under small text | Apple and Linear advise against; costly in Chromium |
| Icon-only controls without labels or tooltips | UI3 and Material research both found it hurts |
| Photo-real hardware panels | Poor fit for a mouse (Production Expert, Valhalla) |
| Expressive, playful shapes and springs everywhere | Fine for consumer apps; function-first tools should keep familiar patterns |
| Anyone's brand assets, icon drawings or fonts as identity | Only principles are borrowed; AudioLab keeps its name, logo and colours |

## 7. Suggested order of implementation (after the picks; nothing started)

1. Token layer with today's values (no visible change), checked with the existing UI tests and screenshots.
2. Palette and type scale behind a "New look (preview)" switch.
3. Controls (buttons, toggles, tabs, menus), then surfaces (radii, borders, glass levels).
4. Mixer strip, then device frame, then icons.
5. Light mode and high-contrast values; then remove the old look once the user says so.

## 8. Sources

Read by research helpers through a web fetch tool that returns a summary of each page, so figures are as that tool reported them; Apple's pages were read as raw text. Pages that did not load are listed at the end.

**Figma**
- [Our approach to designing UI3](https://www.figma.com/blog/our-approach-to-designing-ui3/): panels, Minimize UI, labels, sliders, change management.
- [Build by design](https://www.figma.com/blog/build-by-design/): AI and code workflows; not about UI3 or tokens.
- [Making the move to UI3](https://www.figma.com/blog/making-the-move-to-ui3-a-guide-to-figmas-next-chapter/): retirement of UI2, final fixes.
- [Navigating UI3 (Help Centre)](https://help.figma.com/hc/articles/23954856027159): where controls moved, panel sections.
- [Config 2024 in review](https://www.figma.com/blog/config-2024-recap/) and [Figma 2024: We shipped it, you shaped it](https://www.figma.com/blog/figma-2024-we-shipped-it-you-shaped-it/): rationale, the floating-panel reversal.
- [Figma Pattern Library](https://www.figma.com/blog/figma-pattern-library/) and [How Figma uses Dev Mode](https://www.figma.com/best-practices/how-figma-uses-dev-mode/): tokens, variables to CSS.
- [Fast Company on UI3](https://www.fastcompany.com/91145720/figma-update-ui-more-powerful-than-ever), [Creative Bloq on UI3](https://www.creativebloq.com/web-design/i-cant-tell-you-how-scary-it-is-figmas-redesign-is-a-big-deal-for-figma): goals, beta, 200 icons.

**Linear, Geist, Raycast, Arc, Notion, Framer**
- Linear: [How we redesigned the Linear UI](https://linear.app/blog/how-we-redesigned-the-linear-ui), [A design reset](https://linear.app/blog/a-design-reset), [Behind the latest design refresh](https://linear.app/blog/behind-the-latest-design-refresh), [Linear liquid glass](https://linear.app/blog/linear-liquid-glass).
- Geist: [Colors](https://vercel.com/geist/colors), [Materials](https://vercel.com/geist/materials), [Typography](https://vercel.com/geist/typography).
- Raycast: [A fresh look and feel](https://www.raycast.com/blog/a-fresh-look-and-feel), [Colors API](https://developers.raycast.com/api-reference/user-interface/colors), [Themes](https://manual.raycast.com/themes).
- Arc: [Inverse interview with the design team](https://www.inverse.com/input/design/the-browser-company-arc-design-interview), [Chris Coyier's review](https://chriscoyier.net/2022/12/08/whats-good-about-the-arc-browser/) (no first-party write-up found).
- Notion: [Updating the design of Notion pages](https://www.notion.com/blog/updating-the-design-of-notion-pages).
- Framer: [Transitions and easing](https://framer.com/academy/lessons/framer-animations-transitions-and-easing) (weakest sourcing; no write-up of the current editor found).

**Apple, Google, IBM, Atlassian, tokens**
- Apple HIG: [Materials](https://developer.apple.com/design/human-interface-guidelines/materials), [Adopting Liquid Glass](https://developer.apple.com/documentation/technologyoverviews/adopting-liquid-glass), [Color](https://developer.apple.com/design/human-interface-guidelines/color), [Typography](https://developer.apple.com/design/human-interface-guidelines/typography), [Dark Mode](https://developer.apple.com/design/human-interface-guidelines/dark-mode), [Accessibility](https://developer.apple.com/design/human-interface-guidelines/accessibility).
- [Google Design: the research behind expressive design](https://design.google/library/expressive-material-design-google-research).
- Carbon: [themes](https://carbondesignsystem.com/elements/themes/overview/), [colour](https://carbondesignsystem.com/elements/color/overview/), [spacing](https://carbondesignsystem.com/elements/spacing/overview/), [typography](https://carbondesignsystem.com/elements/typography/overview/).
- Atlassian: [design tokens](https://atlassian.design/foundations/tokens/design-tokens/), [elevation](https://atlassian.design/foundations/elevation), [spacing](https://atlassian.design/foundations/spacing).
- [Design Tokens format, first stable version](https://www.w3.org/community/design-tokens/2025/10/28/design-tokens-specification-reaches-first-stable-version/).

**Music software and hardware**
- Bitwig: [5.2 release notes](https://downloads.bitwig.com/5.2/Release-Notes-5.2.html), [Unified Modulation System](https://www.bitwig.com/userguide/latest/the_unified_modulation_system/), [Sound On Sound on Bitwig Studio 6](https://www.soundonsound.com/reviews/bitwig-studio-6).
- Ableton: [CDM, Live 12 everything new](https://cdm.link/ableton-live-12-everything-new/), [manual: First Steps](https://www.ableton.com/en/manual/first-steps/), [manual: Accessibility and Keyboard Navigation](https://www.ableton.com/en/manual/accessibility-and-keyboard-navigation/).
- Native Instruments: [Kontakt 8.8 UI changes](https://support.native-instruments.com/support/solutions/articles/69000879707-kontakt-8-8-user-interface-changes), [Sound On Sound on Massive X](https://www.soundonsound.com/reviews/native-instruments-massive-x).
- Arturia: [Sound On Sound on Pigments](https://www.soundonsound.com/reviews/arturia-pigments).
- FabFilter Pro-Q 4 help: [overview](https://www.fabfilter.com/help/pro-q/using/overview), [knobs](https://www.fabfilter.com/help/pro-q/using/knobs), [display](https://www.fabfilter.com/help/pro-q/using/eqdisplay).
- Teenage Engineering: [OP-XY layout guide](https://teenage.engineering/guides/op-xy/layout), [Sound On Sound on OP-XY](https://www.soundonsound.com/reviews/teenage-engineering-op-xy).
- Others: [Valhalla, Minimalism in Plugin GUIs](https://valhalladsp.com/?p=149652), [Production Expert on plug-in designs](https://www.production-expert.com/production-expert-1/plugin-designs-why-we-love-some-and-hate-others), [CDM on Serum 2](https://cdm.link/serum-2/).

**Gaps**
- No Config talk video or transcript was found; Config coverage is from Figma's recap and press.
- No source gave UI3's icon stroke, font sizes, colour values or radii, nor motion durations for any product.
- The m3.material.io pages (Material 3 Expressive motion and shape numbers) did not load.
- Not covered: Komplete Kontrol, Arturia V Collection, OP-1 field, u-he, Logic, Studio One; no first-party design write-up for Arc or the current Framer editor.
- Earlier AudioLab research this builds on: `claude/audiolab-liquid-glass-research.md` (how the glass is drawn and what it costs).
