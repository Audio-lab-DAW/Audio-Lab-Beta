"""Build the self-contained pick page: themes.json, the icons (96 px PNG data URIs) and the research list go into page.src.html.
  python3 check.py && python3 build.py   ->  pick-page.html"""
import json, os, base64, io
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
PICK = os.path.join(ROOT, 'desktop', 'icon-assets', 'picker')

data = json.load(open(os.path.join(HERE, 'themes.json')))
for t in data['themes']:
    t.pop('src', None)
    for r in t['m']['rules']: r['worst'].pop('ok', None)
icons = {}
for t in data['themes']:
    for i in t['icons']:
        if i in icons: continue
        im = Image.open(os.path.join(PICK, i + '.png')).convert('RGBA').resize((96, 96), Image.LANCZOS)
        b = io.BytesIO(); im.save(b, 'PNG', optimize=True)
        icons[i] = 'data:image/png;base64,' + base64.b64encode(b.getvalue()).decode()

R = [
 ('Ableton Live 12', 'Theme & Colors: a theme picker, Light, Dark or follow the system, a warm, cool or neutral tone, High Contrast; Customization: grid intensity, brightness, colour intensity and hue. Themes are XML <code>.ask</code> files with 8-digit hex (alpha last). Users found the Live 12 dark theme washed out; Ableton pointed to zoom and the contrast settings.',
  [('Live 12 manual: First Steps', 'https://www.ableton.com/en/live-manual/12/first-steps/'), ('Ableton forum: Live 12 readability', 'https://forum.ableton.com/viewtopic.php?p=1826691'), ('Ableton forum: arrangement shading', 'https://forum.ableton.com/viewtopic.php?p=1836508')]),
 ('Bitwig Studio', 'One colour scheme; Settings › User Interface offers display profile, scaling and contrast, no themes (still none in Bitwig 6, March 2026). Community theming patches the program (unsupported).',
  [('Bitwig user guide: Dashboard', 'https://www.bitwig.com/userguide/latest/the_dashboard/'), ('CDM: Bitwig 6 details', 'https://cdm.link/bitwig-studio-6-details/'), ('CDM: Bitwig themes', 'https://cdm.link/2024/07/bitwig-themes/')]),
 ('FL Studio', 'Options › Theme: hue, saturation, brightness, contrast and text knobs, plus colour pickers for selection, highlight, mute lights, steps, meters and waveforms; a Light mode switch; saved as small <code>.flstheme</code> files. Meaning colours (selection, mute, meters) are user slots.',
  [('FL Studio manual: Themes', 'https://www.image-line.com/fl-studio-learning-content/fl-studio-online-manual/html/envsettings_themes.htm')]),
 ('REAPER', 'WALTER themes: <code>.ReaperTheme</code> text files with colours and an image folder, zipped as <code>.ReaperThemeZip</code>; the Default 7 Theme Adjuster (7.17) edits colours and layouts per page. Track colour can tint the track panels.',
  [('WALTER reference', 'https://www.reaper.fm/sdk/walter/walter'), ('Theme structure', 'https://www.reaper.fm/sdk/walter/images'), ('REAPER Blog: Theme Adjuster', 'https://reaper.blog/2024/06/theme-adjuster/')]),
 ('Cubase and Nuendo', 'Colour schemes and per-element colours up to 14, with a Color Strength slider for track colours; Cubase 15 replaced them with a few scheme and accent sliders, and users miss the old control. A Cubase 14 thread lists low contrast, thin small type and a white playhead on light backgrounds.',
  [('Nuendo 11: track and channel colours', 'https://steinberg.help/nuendo/v11/en/cubase_nuendo/topics/preferences/preferences_user_interface_track_channel_colors_r.html'), ('Steinberg forum: Cubase 15 colours', 'https://forums.steinberg.net/t/missing-ui-colors/1013780'), ('Steinberg forum: Cubase 14 regressions', 'https://forums.steinberg.net/t/cubase-14-gui-design-regressions/953624')]),
 ('Studio One, now Fender Studio Pro', 'Appearance: hue shift, saturation, luminance and contrast for the whole program, separate brightness and contrast for the arrange grid, presets; options to colour track controls, channel strips and plug-in headers with the track colour.',
  [('Fender Studio Pro manual: General options', 'https://fenderstudiopromanual.fender.com/en/Content/Setup_Topics/General_Options.htm'), ('Advanced options', 'https://fenderstudiopromanual.fender.com/en/Content/Setup_Topics/Advanced_Options.htm')]),
 ('Logic, Pro Tools, Renoise, Reason, Vital', 'Logic: dark app; the tracks area background can be dark, light or a custom grey, regions take the track colour, the piano roll has a bright background. Pro Tools: Dark (default since 2020.11) or Classic. Renoise: an editor for every element with a global HSV filter, <code>.xrnc</code> XML. Reason: three themes, restart needed. Vital: JSON skins.',
  [('Logic Pro: Tracks settings', 'https://support.apple.com/guide/logicpro/lgcp8e0207b2/mac'), ('Pro Tools dark theme', 'https://www.production-expert.com/home-page/pro-tools-2020-11-released?format=amp'), ('Renoise: GUI customisation', 'https://tutorials.renoise.com/wiki/GUI_Customisation'), ('Reason themes', 'https://help.reasonstudios.com/hc/en-us/articles/360002215614-How-can-I-change-Themes-in-Reason'), ('Vital skins', 'https://forum.vital.audio/t/how-to-make-your-own-skin-in-vital-a-free-skin/5602')]),
 ('Design tokens', 'The W3C Design Tokens format reached its first stable version (2025.10): <code>$value</code>, <code>$type</code>, aliases like <code>{color.ink}</code>, a colour type with colour spaces, and a resolver that applies a theme as a set of overrides. Style Dictionary builds tokens into CSS and JS. IBM Carbon: a token is a role that never changes between themes, only its value.',
  [('W3C DTCG: first stable version', 'https://www.w3.org/community/design-tokens/2025/10/28/design-tokens-specification-reaches-first-stable-version/'), ('Format 2025.10', 'https://www.designtokens.org/tr/2025.10/'), ('Resolver module', 'https://www.designtokens.org/tr/2025.10/resolver/'), ('Carbon themes', 'https://carbondesignsystem.com/elements/themes/overview/')]),
 ('GitHub Primer, Material, Spectrum', 'Primer ships 9 colour themes (light, dark, dimmed, high contrast, two colour-blind sets each) and runs a contrast check on every pull request. Material 3 pairs every fill with an "on" colour and generates schemes by tone. Adobe Spectrum generates colours from target contrast ratios (Leonardo), so text tokens pass on every background layer.',
  [('primer/primitives', 'https://github.com/primer/primitives'), ('Primer contrast workflow', 'https://raw.githubusercontent.com/primer/primitives/main/.github/workflows/a11y-contrast.yml'), ('Material Web: Color', 'https://material-web.dev/theming/color'), ('Spectrum colour system', 'https://spectrum.adobe.com/page/color-system')]),
 ('VS Code, JetBrains, Figma, Blender', 'VS Code: about 960 workbench colour ids, live preview while choosing, per-theme overrides, separate high-contrast themes with extra borders. JetBrains: UI theme and editor scheme are separate; Islands (2025.3) asks for at least 1.2 : 1 between zones. Figma: about 350 semantic tokens replaced 5,100 hard-coded colours, and a lint rejects untokenised colours. Blender: XML themes, edits shown live.',
  [('VS Code theme colours', 'https://code.visualstudio.com/api/references/theme-color'), ('VS Code themes', 'https://code.visualstudio.com/docs/configure/themes'), ('JetBrains Islands', 'https://plugins.jetbrains.com/docs/intellij/supporting-islands-theme.html'), ('Figma: Illuminating dark mode', 'https://www.figma.com/blog/illuminating-dark-mode/'), ('Blender themes', 'https://docs.blender.org/manual/en/latest/editors/preferences/themes.html')]),
 ('macOS, Windows, the web', 'macOS: every colour needs light, dark and increased-contrast values; app accents apply only with the Multicolor accent. Windows: accent generated to keep contrast; contrast themes are a fixed 8-colour set used in pairs. CSS: <code>color-scheme</code>, <code>light-dark()</code>, <code>prefers-contrast</code>, <code>forced-colors</code>. Electron: <code>nativeTheme</code> and the system accent.',
  [('Apple HIG: Color', 'https://developer.apple.com/design/human-interface-guidelines/color'), ('Windows contrast themes', 'https://learn.microsoft.com/windows/apps/design/accessibility/high-contrast-themes'), ('MDN: light-dark()', 'https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Values/color_value/light-dark'), ('Electron nativeTheme', 'https://www.electronjs.org/docs/latest/api/native-theme')]),
 ('Contrast', 'WCAG 2.2: 4.5 : 1 for text, 3 : 1 for large text and for controls and graphics (1.4.11: meters, waveforms, clip edges, focus rings). APCA (beta, not normative; WCAG 3 is still a draft in September 2026): Lc 75 body text, 60 other content text, 45 large or non-body text, 30 spot text such as disabled. WCAG 2 overrates dark-on-dark pairs, so dark themes are checked with both.',
  [('WCAG 2.2', 'https://www.w3.org/TR/WCAG22/'), ('Understanding 1.4.11', 'https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html'), ('apca-w3 source', 'https://github.com/Myndex/apca-w3'), ('APCA introduction', 'https://github.com/Myndex/apca-introduction'), ('WCAG 3 history', 'https://www.w3.org/standards/history/wcag-3.0')]),
 ('Dark, light and glass', 'Material: dark surfaces not pure black, desaturated colours on dark. Pure white text on black halates for people with astigmatism (about half of us have some). Liquid Glass drew legibility complaints; Apple added a Tinted option, and Reduce Transparency makes layers solid. Windows: no accent-coloured text on acrylic, and a solid fallback.',
  [('Material dark theme', 'https://codelabs.developers.google.com/codelabs/design-material-darktheme/'), ('Level Access: astigmatism', 'https://www.levelaccess.com/blog/accessibility-for-people-with-astigmatism/'), ('Six Colors: Liquid Glass', 'https://sixcolors.com/post/2025/11/soaping-up-liquid-glass-less-transparency-more-contrast/'), ('Microsoft Acrylic', 'https://learn.microsoft.com/windows/uwp/style/acrylic')]),
 ('Colour vision and meaning colours', 'Red-green colour-vision deficiency affects about 8 % of men of European descent. Machado 2009 matrices simulate it; cols4all calls a smallest CIEDE2000 of 10 friendly. Okabe-Ito and Paul Tol palettes are safe but have 7 to 9 colours, so tracks also need a name or number (WCAG 1.4.1). Design systems keep error, warning and success meanings fixed and check them on every surface.',
  [('Birch 2012', 'https://pubmed.ncbi.nlm.nih.gov/22472762/'), ('Machado 2009', 'https://www.inf.ufrgs.br/~oliveira/pubs_files/CVD_Simulation/CVD_Simulation.html'), ('cols4all', 'https://mtennekes.github.io/cols4all/articles/01_paper.html'), ('Paul Tol', 'https://personal.sron.nl/~pault/'), ('Atlassian colour', 'https://www.atlassian.design/foundations/color'), ('W3C C40 two-colour focus', 'https://www.w3.org/WAI/WCAG22/Techniques/css/C40')]),
]

src = open(os.path.join(HERE, 'page.src.html')).read()
src = src.replace('/*@DATA@*/null', json.dumps(data, separators=(',', ':')))
src = src.replace('/*@ICONS@*/{}', json.dumps(icons, separators=(',', ':')))
src = src.replace('/*@RESEARCH@*/[]', json.dumps(R, separators=(',', ':')))
open(os.path.join(HERE, 'pick-page.html'), 'w').write(src)
print('pick-page.html', len(src) // 1024, 'KB,', len(icons), 'icons')
