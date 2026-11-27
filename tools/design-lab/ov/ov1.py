#!/usr/bin/env python3
"""Task OV1 (lane F, overlays; docs/design-round-5-overlays.md section 5): shared overlay tokens and timing.
   python3 tools/design-lab/ov/ov1.py index.html
The user's picks (27 Nov): DR5 picks: R2 D3 T3 N1 X1 K1. This step only adds the shared vocabulary the next steps draw with:
  - CSS tokens --ov-* (row 26 px, radii, R2's blue focus fill, the soft tint, the hairline, the mono label, keys, amber from LOOK's
    --unit) and motion tokens (90 ms in, 60 ms out, 140 ms sheet, 80 ms tag, 140 ms card), all times --ov-mo;
  - --ov-mo is 0 with reduced motion (system setting) and with Motion set to 'Signal only' (LOOK, body.lkm1);
  - the same numbers as LOOK.ov (lkT().ov) for JS, with ovMs(k) (0 for the transitions when motion is off) and ovStill();
  - the one visible change: the right-click menu fades in (90 ms, 3 px) and out (60 ms), not in Light mode (no animations there). The menu is still closed at once for
    the code (ctxm.hidden is true straight away, inert while it fades); the glass engine keeps drawing its face during the
    fade-out (glfShown lets a hidden element with class ovout through) and follows the opacity it already reads.
Every anchor is asserted. Re-run on a fresh file after a rebase."""
import sys
F = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
s = open(F, encoding='utf-8').read()
assert 'task OV1' not in s, 'already applied'

def rep(old, new, n=1):
    global s
    c = s.count(old)
    assert c == n, (c, n, old[:120])
    s = s.replace(old, new)

CSS = r"""/* task OV1 (lane F, overlays, picks R2 D3 T3 N1 X1 K1): shared overlay tokens and timing. Sizes: --ov-row list row, --ov-r menus and
   popovers (R2, D3), --ov-r-tip the callout (T3), --ov-r-card notifications (N1), --ov-r-pal the palette (K1), --ov-r-item a row.
   Colours: --ov-hi the focused row (R2: today's blue fill), --ov-tint a soft tint (drop targets, palette rows), --ov-ln the hairline,
   --ov-mut quiet text, --ov-amb amber (LOOK's unit colour: T3 leader, Advanced). Type: --ov-lab mono capitals with --ov-labsp, --ov-key.
   Motion: --ov-in 90 ms, --ov-out 60 ms, --ov-sheet 140 ms, --ov-tip 80 ms, --ov-card 140 ms, all multiplied by --ov-mo (0 = none). */
:root{--ov-row:26px;--ov-r:10px;--ov-r-item:6px;--ov-r-tip:8px;--ov-r-card:9px;--ov-r-pal:12px;--ov-pad:4px;
  --ov-hi:var(--blf,#4c8dff);--ov-tint:rgba(var(--bl3,76,141,255),.17);--ov-ln:rgba(255,255,255,.09);--ov-mut:#8b8b97;--ov-amb:var(--unit,#ffb547);
  --ov-lab:500 9.5px/1.2 "JetBrains Mono",ui-monospace,Menlo,monospace;--ov-labsp:.12em;--ov-key:400 11px "JetBrains Mono",ui-monospace,Menlo,monospace;
  --ov-mo:1;--ov-in:90ms;--ov-out:60ms;--ov-sheet:140ms;--ov-tip:80ms;--ov-card:140ms;--ov-ease:cubic-bezier(0,0,0,1)}
body.lkm1{--ov-mo:0}
@media (prefers-reduced-motion:reduce){:root,body{--ov-mo:0}}
@keyframes ovIn{from{opacity:0;transform:translateY(-3px)}to{opacity:1;transform:none}}
@keyframes ovFade{from{opacity:0}to{opacity:1}}
@media (prefers-reduced-motion:no-preference){body:not(.lite):not(.fxstill):not(.lkm1) #ctxm:not([hidden]):not(.dropup){animation:ovIn calc(var(--ov-mo)*var(--ov-in)) var(--ov-ease)}}
#ctxm[hidden].ovout{display:flex;opacity:0;pointer-events:none;transition:opacity calc(var(--ov-mo)*var(--ov-out)) linear}
"""
rep('.dacv{display:flex;', CSS + '.dacv{display:flex;')

JS = r"""/* task OV1 (lane F, overlays): the overlay numbers for JS, as LOOK entries (lkT().ov), the same as the --ov-* tokens.
   ms: in/out (menus, dropdowns, popovers), sheet, tip (tag fade), card (notification in), sub (submenu hover), typeahead (menu
   type-ahead buffer), tipDelay and tipWarm (tag after 500 ms, then at once for 300 ms), drain (notification time, paused on hover),
   log (a log line fades), cards (most notifications on screen). ovMs(k): the time, 0 for the transitions when motion is off. */
function ovLook(){const L=lkT();if(!L.ov)L.ov={row:26,rad:10,radItem:6,radTip:8,radCard:9,radPal:12,pad:4,
  ease:'cubic-bezier(0,0,0,1)',lab:'500 9.5px "JetBrains Mono",ui-monospace,Menlo,monospace',labSp:'.12em',
  ms:{in:90,out:60,sheet:140,tip:80,card:140,sub:120,typeahead:600,tipDelay:500,tipWarm:300,drain:6000,log:8000},cards:3};return L.ov}
let OVMQ=null;
function ovStill(){try{if(!OVMQ)OVMQ=matchMedia('(prefers-reduced-motion: reduce)');if(OVMQ.matches)return true}catch(e){}return!!(document.body&&document.body.classList.contains('lkm1'))}
function ovMs(k){const v=ovLook().ms[k];if(v==null)return 0;return(k==='in'||k==='out'||k==='sheet'||k==='tip'||k==='card')&&ovStill()?0:v}
ovLook();
/* the menu's fade-out: the code sees it closed at once (hidden, inert); it stays drawn for 60 ms while it fades (class ovout).
   Focus leaves it at once, as when it was hidden before. Not for the three-column menus (their layout changes on close), not in
   Light mode (it has no animations) and not when motion is off. */
{let tm=0;const end=()=>{clearTimeout(tm);tm=0;ctxm.classList.remove('ovout');ctxm.inert=false};
 new MutationObserver(rs=>{if(!ctxm.hidden){if(ctxm.classList.contains('ovout')||tm)end();return}
   if(ctxm.classList.contains('ovout'))return;let was=false,cols=false;for(const r of rs){if(r.attributeName==='hidden'&&r.oldValue===null)was=true;if(r.attributeName==='class'&&/\bmcols\b/.test(r.oldValue||''))cols=true}
   if(!was||cols||ovStill()||document.body.classList.contains('lite')||document.body.classList.contains('fxstill')||!ctxm.childElementCount)return;{const a=document.activeElement;if(a&&ctxm.contains(a))a.blur()}ctxm.inert=true;ctxm.classList.add('ovout');tm=setTimeout(end,ovMs('out')+30)})
  .observe(ctxm,{attributes:true,attributeFilter:['hidden','class'],attributeOldValue:true})}
"""
rep('function askChoice(title,text,btns,icon){', JS + 'function askChoice(title,text,btns,icon){')

# the glass engine keeps the menu's face while it fades out
rep("for(let t=el;t&&t!==document.body;t=t.parentElement)if(t.hidden)return false;return el.getClientRects().length>0}",
    "for(let t=el;t&&t!==document.body;t=t.parentElement)if(t.hidden&&!(t===el&&t.classList.contains('ovout')))return false;return el.getClientRects().length>0}")

open(F, 'w', encoding='utf-8').write(s)
print('task OV1 applied')
