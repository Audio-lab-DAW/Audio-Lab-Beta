#!/usr/bin/env python3
"""Task GS2 (glass step 2, v0.227): windows, sheets and menus on the glass engine; backdrop-filter nowhere in the app.
   python3 tools/edits/taskGS2.py index.html
Every replacement is asserted to be unique. The app code is tools/edits/taskGS2_block.js; it goes before askChoice, the CSS before .dacv."""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
f = sys.argv[1]; s = open(f, encoding='utf-8').read()
def rep(a, b):
    global s
    n = s.count(a); assert n == 1, (n, a[:90]); s = s.replace(a, b)

rep("const VERSION='0.226',BUILD='27 November 2026'", "const VERSION='0.227',BUILD='27 November 2026'")

# ---- CSS, before .dacv ----
css = """/* v0.227 (task GS2, glass step 2): backdrop-filter is used nowhere in the app, at no level. Windows, sheets and menus get their glass from the engine
   (canvases .glfCv in the page's stacking order directly under them); the element itself keeps only its tint, border, shadow and content. */
*,*::before,*::after{backdrop-filter:none!important;-webkit-backdrop-filter:none!important}
.glfCv{position:fixed;left:0;top:0;width:100%;height:100%;pointer-events:none;display:block;margin:0;padding:0;border:0;transform-origin:0 0}
.glfCv[hidden]{display:none!important}
/* no engine face behind a floating element (Solid, no WebGL2, a fourth level of overlap): it is solid */
body.gls :is(.fwin,.abxw,.pinw>.pinb,#mixWin>.fwh,.modal>.sheet,#uywM .uyww,#ctxm,.pop,#w9m),body.gls .spov>.spgl,.glfsol,.spov.glfsol>.spgl{background:rgb(var(--gtr2))!important}
.spov.glfsol{background:none!important}
/* small things that had a blur of their own (inside glass, over a display, or with nothing to frost): a little more opaque instead */
#toast{background:rgba(36,36,46,.95)}#presWin{background:rgba(30,31,40,.97)}#vizp{background:rgba(var(--gtr2),max(var(--ga),.9))}
#fxin .dev.eq2 .eqov2{background:rgba(10,11,15,.9)}.dev.gridd>.devh .kpre,.dev.gridd>.devh>button{background:rgba(10,11,15,.92)}
.w9gd{background:color-mix(in srgb,var(--c) 16%,rgba(22,24,31,.96))}#exFz{background:rgba(14,15,19,.93)}
"""
a = ".dacv{display:flex;"
rep(a, css + a)

# ---- JS, before askChoice ----
blk = open(os.path.join(HERE, 'taskGS2_block.js'), encoding='utf-8').read()
a = "function askChoice(title,text,btns,icon){"
rep(a, blk + a)

# ---- Settings, Performance: the glass block now covers windows, sheets and menus; the old switches say that they change nothing ----
rep("h.textContent='Docked panels: track headers, transport bar, devices';", "h.textContent='Glass: docked panels, windows, sheets and menus';")
rep("'How the docked panels are drawn. It follows the Light mode slider", "'How the glass is drawn: docked panels, windows, sheets and menus. It follows the Light mode slider")
rep("['glass','Glass','Glass: the docked panels (track headers, transport bar, devices) are frosted glass with a lens at the edges, drawn by the glass engine on the graphics card.']",
    "['glass','Glass','Glass: the docked panels, windows, sheets and menus are frosted glass with a lens at the edges, drawn by the glass engine on the graphics card.']")
rep("['solid','Solid','Solid: no glass on the docked panels. Costs nothing.", "['solid','Solid','Solid: no glass on panels, windows and menus. Costs nothing.")
rep("'Solid: this computer cannot run the glass engine (no WebGL2 graphics), so the docked panels are solid.'", "'Solid: this computer cannot run the glass engine (no WebGL2 graphics), so panels, windows and menus are solid.'")
rep("(lv==='solid'?'Solid: no glass on the docked panels.'", "(lv==='solid'?'Solid: no glass on panels, windows and menus.'")
rep('title="Lighter: light glass on the docked panels, solid windows and menus, no animations, pictures 30 times a second"',
    'title="Lighter: light glass without the lens on panels, windows and menus, no animations, pictures 30 times a second"')
rep('title="Optimised: glass on the docked panels, windows and menus with blur from a ready-made picture"',
    'title="Optimised: glass with the lens on panels, windows and menus"')
rep('title="Full effects: glass on the docked panels, windows and menus with refraction, live blur, edge light, all animations"',
    'title="Full effects: glass with the lens on panels, windows and menus, edge light, all animations"')
rep('<div class="pmh">Windows, sheets and menus: what each effect costs</div>', '<div class="pmh">Windows, sheets and menus: other effects</div>')
rep("row('refr','refr','Refraction','Bends the picture near the edges of glass, like a thick pane. The most expensive effect.',",
    "row('refr','refr','Refraction','Not used any more: windows, sheets and menus get their lens from the glass engine (Lens, above), so this switch changes nothing now.',")
rep("row('blur','blur','Blur','Live: the browser blurs what is behind each panel whenever anything changes. Picture: the arrangement is blurred once into a small picture. Off: solid panels.',",
    "row('blur','blur','Blur','Not used any more: the frosting of windows, sheets and menus comes from the glass engine (Frosting, above), so this choice changes nothing now.',")
rep("row('glPlay','play','Softer blur while playing','Halves the live blur during playback. Only matters with live blur.',",
    "row('glPlay','play','Softer blur while playing','Not needed any more: there is no live blur in the app, so this switch changes nothing now.',")

open(f, 'w', encoding='utf-8').write(s)
print('ok', len(s))
