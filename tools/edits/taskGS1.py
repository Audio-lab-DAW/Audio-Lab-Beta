# Task GS1 (glass step 1, v0.223): the glass engine for the docked panels.  python3 tools/edits/taskGS1.py index.html
# Every replacement is asserted to match exactly once. The engine is pasted from tools/glass-lab/glass-engine.js unchanged, the app code from tools/edits/taskGS1_block.js.
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
f = sys.argv[1]; s = open(f, encoding='utf-8').read()
def rep(a, b):
    global s
    assert s.count(a) == 1, (s.count(a), a[:90]); s = s.replace(a, b)

rep("const VERSION='0.222',BUILD='27 November 2026'", "const VERSION='0.223',BUILD='27 November 2026'")

# ---- CSS ----
css = """/* v0.223 (task GS1): the glass engine draws the docked panels. Its canvas sits under the arrangement canvas; the docked panels carry no backdrop-filter at any level.
   Their see-through tint has its own value (--gad), so they are glass at the level Light too; .glsol = no engine face behind this panel, so it is solid. */
#glassCv{position:absolute;left:0;top:0;width:100%;height:100%;display:block;pointer-events:none}
#hglass,#tr,#fxglass,#fxband{backdrop-filter:none!important;-webkit-backdrop-filter:none!important;--ga:var(--gad,.5)}
#hglass.glsol,#tr.glsol,#fxglass.glsol,#fxband.glsol{--ga:1}
/* the playhead layer over the arrangement */
#arrPhW{position:absolute;left:0;top:0;width:100%;height:100%;overflow:hidden;pointer-events:none}
#arrPhC,#arrPhJ{position:absolute;left:0;top:0;display:block;pointer-events:none;will-change:transform}
/* Settings, Performance: docked panels */
#glBox .glseg button:disabled{opacity:.38;cursor:default}
.glnote{margin:7px 2px 2px;font-size:11px;line-height:1.45;color:#8f95a5}
"""
a = ".dacv{display:flex;"
assert s.count(a) == 1; s = s.replace(a, css + a)

# ---- window drags keep the pointer (pointer capture once the drag has really started), and end on pointercancel too ----
rep("let d=null;w.querySelector('.fwh').addEventListener('pointerdown',e=>{if(e.target.closest('button,select,input,.seg'))return;d={x0:e.clientX,y0:e.clientY,l:w.offsetLeft,t:w.offsetTop};",
    "let d=null;w.querySelector('.fwh').addEventListener('pointerdown',e=>{if(e.target.closest('button,select,input,.seg'))return;d={x0:e.clientX,y0:e.clientY,l:w.offsetLeft,t:w.offsetTop,pid:e.pointerId,hd:e.currentTarget};")
rep("addEventListener('pointermove',e=>{if(!d)return;const z=ZOOM,dx=(e.clientX-d.x0)/z,dy=Math.max(-d.t,(e.clientY-d.y0)/z);d.dx=dx;d.dy=dy;",
    "addEventListener('pointermove',e=>{if(!d)return;/* v0.223: once the window really moves it keeps the pointer, so the page under it is not searched on every step and the drag cannot be lost */if(d.hd&&!d.cap&&Math.abs(e.clientX-d.x0)+Math.abs(e.clientY-d.y0)>3){d.cap=1;try{d.hd.setPointerCapture(d.pid)}catch(x){}}const z=ZOOM,dx=(e.clientX-d.x0)/z,dy=Math.max(-d.t,(e.clientY-d.y0)/z);d.dx=dx;d.dy=dy;")
rep("addEventListener('pointerup',e=>{if(d){if(d.dx!=null){w.style.left=d.l+d.dx+'px';w.style.top=Math.max(0,d.t+d.dy)+'px'}w.style.translate='';w.classList.remove('mv');const mv=Math.abs(e.clientX-d.x0)+Math.abs(e.clientY-d.y0)>3;d=null;if(w._onDrop&&w._onDrop(e))return;if(mv){UI.winMoved=UI.winMoved||{};UI.winMoved[id]=true}save()}});",
    "const fwUp=e=>{if(d){if(d.cap)try{d.hd.releasePointerCapture(d.pid)}catch(x){}if(d.dx!=null){w.style.left=d.l+d.dx+'px';w.style.top=Math.max(0,d.t+d.dy)+'px'}w.style.translate='';w.classList.remove('mv');const mv=Math.abs(e.clientX-d.x0)+Math.abs(e.clientY-d.y0)>3;d=null;if(w._onDrop&&w._onDrop(e))return;if(mv){UI.winMoved=UI.winMoved||{};UI.winMoved[id]=true}save()}};addEventListener('pointerup',fwUp);addEventListener('pointercancel',fwUp);")

# ---- Performance tab: what the stops mean now ----
rep("'Solid panels, no animations. Pictures redraw 30 times a second.','Glass with blur from a ready-made picture. Smooth on most computers.','Refraction, live blur, edge light and every animation.'];",
    "'Light glass on the docked panels, solid windows and menus, no animations. Pictures redraw 30 times a second.','Glass on the docked panels. Windows and menus with blur from a ready-made picture. Smooth on most computers.','Glass on the docked panels. Windows and menus with refraction, live blur, edge light and every animation.'];")
rep('title="Lighter: solid panels, no animations, pictures 30 times a second"', 'title="Lighter: light glass on the docked panels, solid windows and menus, no animations, pictures 30 times a second"')
rep('title="Optimised: glass with blur from a ready-made picture"', 'title="Optimised: glass on the docked panels, windows and menus with blur from a ready-made picture"')
rep('title="Full effects: refraction, live blur, edge light, all animations"', 'title="Full effects: glass on the docked panels, windows and menus with refraction, live blur, edge light, all animations"')
rep('<div class="pmh">What each effect costs</div><div class="pmlist">', '<div class="pmh">Windows, sheets and menus: what each effect costs</div><div class="pmlist">')
rep("row('glBack','back','Half-size picture behind glass','What shows through live glass is a half-size copy of the arrangement. Only matters with live blur.',",
    "row('glBack','back','Half-size picture behind glass','Not needed any more: the glass engine draws what is behind the docked panels itself, so this switch changes nothing now.',")

# ---- the engine and the app code ----
eng = open(os.path.join(HERE, '..', 'glass-lab', 'glass-engine.js'), encoding='utf-8').read().rstrip() + '\n'
blk = open(os.path.join(HERE, 'taskGS1_block.js'), encoding='utf-8').read()
assert blk.count('/*GLASS-ENGINE*/\n') == 1
blk = blk.replace('/*GLASS-ENGINE*/\n', '/* ---- the engine: tools/glass-lab/glass-engine.js, pasted unchanged ---- */\n' + eng + '/* ---- end of the engine ---- */\n')
a = "function askChoice(title,text,btns,icon){"
assert s.count(a) == 1; s = s.replace(a, blk + a)
open(f, 'w', encoding='utf-8').write(s)
print('ok', len(s))
