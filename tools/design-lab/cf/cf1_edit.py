"""Task CF-1 (lane P, comfort modes): the map's Hide button and its overlay.
  python3 tools/design-lab/cf/cf1_edit.py [index.html] [--commands docs/commands.md --version 0.xxx]
With --commands it also adds the row of view.mapHide to docs/commands.md (only together with the index.html release: taskXT_DL2 fails when a listed
command is missing from the registry).
Adds CSS before `.dacv{display:flex;` and JS before `function askChoice(title,text,btns,icon){`. Every anchor is asserted unique.
Run again on a fresh index.html after a rebase; it refuses to run twice (marker check)."""
import sys
A = [a for a in sys.argv[1:]]
def opt(k):
    if k in A: i = A.index(k); v = A[i + 1]; del A[i:i + 2]; return v
CMDS = opt('--commands'); VER = opt('--version')
P = A[0] if A else 'index.html'
s = open(P, encoding='utf-8').read()
assert 'task CF-1 (lane P' not in s, 'CF-1 is already in this file'
def one(a):
    n = s.count(a); assert n == 1, (a[:60], n)
for a in ['.dacv{display:flex;', 'function askChoice(title,text,btns,icon){', '<footer id="mapw">', 'function drawMap(phOnly){',
          "const XT_CMD_EXTRA=[", "const GLFSEL=[", "const PANEL={fx:$('#fx'),tr:$('#tr'),map:$('#mapw')}", 'function applyMapH(){']:
    one(a)
assert 'cfMapHide' not in s and 'CF_HOOKS' not in s

CSS = r"""/* ===== task CF-1 (lane P, comfort modes): the map's Hide mode. Hidden: the map leaves the layout (its space goes to the rest); near the edge where it
   was docked it rises over everything as a glass window (a face of the glass engine's floating layer, no backdrop-filter). Timings: lane F's motion
   multiplier --ov-mo (0 under reduced motion) times 50 ms out and 80 ms in. ===== */
#cfMapHide{position:absolute;top:1px;right:8px;z-index:5;box-sizing:border-box;height:16px;min-height:0;min-width:0;padding:0 9px;margin:0;border-radius:8px;border:1px solid rgba(255,255,255,.12);background:rgba(var(--gtr2),.92);color:var(--mut);font:inherit;font-size:var(--fs1);font-weight:var(--fw6,600);line-height:14px;cursor:pointer}
#cfMapHide:hover{color:var(--ink);border-color:rgba(255,255,255,.26)}
#cfMapHide:focus-visible{outline:2px solid var(--blf);outline-offset:1px}
#cfMapHide[aria-pressed="true"]{color:var(--ink);background:rgba(var(--bl3),.30);border-color:rgba(var(--bl3),.65)}
body.map-top #cfMapHide{top:auto;bottom:1px}
body.cfmh #mapw{position:fixed;left:6px;right:6px;z-index:20;border-radius:10px;border:1px solid rgba(255,255,255,.12);box-shadow:0 18px 50px rgba(0,0,0,.55);background:rgba(var(--gtr2),max(var(--ga),.42));overflow:hidden;opacity:0;transform:translateY(var(--cfdy,12px));transition:transform calc(var(--ov-mo,1)*50ms) linear,opacity calc(var(--ov-mo,1)*50ms) linear}
body.cfmh #mapw:not(.cfon){display:none!important}
body.cfmh #mapw.cfin{opacity:1;transform:none;transition-duration:calc(var(--ov-mo,1)*80ms);transition-timing-function:var(--ov-ease,ease-out)}
body.gls #mapw.cfon,body.fxmin #mapw.cfon,#mapw.cfon.glfsol{background:rgb(var(--gtr2))!important}
"""

JS = r"""/* ====================== task CF-1 (lane P, comfort modes, docs/comfort-build.md): the map's Hide mode ======================
   The user's words (27 Nov): a Hide button on the map; in Hide mode everything else fills the window (no empty or black space); the map comes up over
   everything when the pointer comes close to where it is docked (top or bottom, wherever the layout puts it), and goes away when the pointer leaves;
   Hide again puts it back in its docked place. Remembered in UI.cfMapHide. Command view.mapHide.
   Lane P owns only where the map lives and the button: what it draws is lane A's (drawMap), how it scrolls lane O's.
   - Hidden and not shown: #mapw is display:none (body.cfmh), drawMap is skipped (no work at all), the pointer check is one comparison per move.
   - Shown: #mapw is position:fixed at its docked edge (z-index 20: over the panels, under floating windows, menus and sheets), a 'window' face of the
     glass engine's floating layer (GLFSEL), so it is frosted glass drawn by the engine; Solid draws it solid.
   - Edge: the bottom of what is above the map's place (map at the top) or the top of what is below it (map at the bottom), read at most twice a
     second, never per frame. Reveal: within 6 px of it, no button held. Leave: outside the map (and the edge) for 120 ms, no button held, no menu open.
   - After Hide is clicked the pointer is right at the edge: the map waits until the pointer has left the edge once. */
const CF={hid:false,show:false,arm:true,edge:null,edgeT:0,t:0,t2:0,mo:1};
const CF_HOOKS={};
function cfMo(){try{const v=parseFloat(getComputedStyle(document.body).getPropertyValue('--ov-mo'));return isFinite(v)?v:1}catch(e){return 1}}
function cfMapEl(){return typeof PANEL!=='undefined'&&PANEL.map||document.getElementById('mapw')}
/* may the hidden map come up now? (not when the map is switched off, or a full-screen view, split view or the start-up animation hides it) */
function cfMapCan(){const mw=cfMapEl(),b=document.body.classList;return!!(CF.hid&&mw&&!UI.mapOff&&!mw.hidden&&mw.parentElement&&!b.contains('prfull')&&!b.contains('split')&&!b.contains('booting'))}
/* where the docked map was, in client px: {y, top} (top = the map lives above the arrangement and comes down from y) */
function cfMapEdge(force){const n=performance.now();if(!force&&CF.edge&&n-CF.edgeT<500)return CF.edge;CF.edgeT=n;const mw=cfMapEl(),p=mw&&mw.parentElement;if(!p){CF.edge=null;return null}
  const top=p.id==='topOut',vis=e=>e&&e.getClientRects().length>0&&e.id!=='cfMapHide';let y;
  if(top){let e=mw.previousElementSibling;while(e&&!vis(e))e=e.previousElementSibling;y=e?e.getBoundingClientRect().bottom:p.getBoundingClientRect().top}
  else{let e=mw.nextElementSibling;while(e&&!vis(e))e=e.nextElementSibling;y=e?e.getBoundingClientRect().top:Math.min(innerHeight,p.getBoundingClientRect().bottom)}
  return CF.edge={y,top}}
function cfInZone(y,E){const z=6*(typeof ZOOM!=='undefined'?ZOOM:1);if(!E.top&&E.y>=innerHeight-1)return y>=E.y-z;if(E.top&&E.y<=1)return y<=E.y+z;return Math.abs(y-E.y)<=z}
function cfMapShow(){if(CF.show||!cfMapCan())return false;const E=cfMapEdge(true);if(!E)return false;const mw=cfMapEl(),z=ZOOM||1;CF.show=true;clearTimeout(CF.t);clearTimeout(CF.t2);CF.mo=cfMo();
  if(E.top){mw.style.bottom='auto';mw.style.top=(E.y/z+6)+'px';mw.style.setProperty('--cfdy','-12px')}
  else{mw.style.top='auto';mw.style.bottom=Math.max(0,(innerHeight-E.y)/z+6)+'px';mw.style.setProperty('--cfdy','12px')}
  mw.classList.add('cfon');void mw.offsetWidth;mw.classList.add('cfin');
  try{GLF.cand=null}catch(e){}MAPK='';dirty=true;return true}
function cfMapOut(now){clearTimeout(CF.t);if(!CF.show&&!now)return;CF.show=false;const mw=cfMapEl();if(!mw)return;mw.classList.remove('cfin');clearTimeout(CF.t2);
  const done=()=>{if(CF.show)return;mw.classList.remove('cfon');for(const k of['top','bottom'])mw.style[k]='';mw.style.removeProperty('--cfdy')};
  const ms=50*CF.mo;if(now||!(ms>0))done();else CF.t2=setTimeout(done,ms)}
function cfMapBtnSync(){const b=document.getElementById('cfMapHide');if(!b)return;b.setAttribute('aria-pressed',String(CF.hid));
  b.title=CF.hid?'The map is hidden. Click Hide again to put it back in its place.':'Hide the map. Everything else gets its space; move the pointer to the edge where the map was and it comes up over everything. Click Hide again to put it back.'}
function cfMapApply(){const on=!!UI.cfMapHide;if(on!==CF.hid){CF.hid=on;if(on)CF.arm=false;else cfMapOut(true)}document.body.classList.toggle('cfmh',on);CF.edge=null;cfMapBtnSync();MAPK='';dirty=true}
function cfMapToggle(){UI.cfMapHide=!UI.cfMapHide;saveUI();cfMapApply();return true}
{const mw=cfMapEl();if(mw&&!document.getElementById('cfMapHide')){const b=document.createElement('button');b.id='cfMapHide';b.type='button';b.textContent='Hide';
  b.addEventListener('click',e=>{e.stopPropagation();cfMapToggle()});b.addEventListener('pointerdown',e=>e.stopPropagation());b.addEventListener('dblclick',e=>e.stopPropagation());mw.appendChild(b)}}
/* no drawing while the map is hidden and not shown */
{const _dm=drawMap;drawMap=function(){if(CF.hid&&!CF.show)return;return _dm.apply(this,arguments)}}
/* the shown map is a glass window of the floating layer */
try{GLFSEL.push(['#mapw.cfon','window'])}catch(e){}
/* the pointer: reveal at the edge, leave after 120 ms outside (only while Hide is on) */
addEventListener('pointermove',e=>{if(!CF.hid)return;
  if(!CF.show){if(e.buttons||!cfMapCan())return;const E=cfMapEdge(false);if(!E)return;const inz=cfInZone(e.clientY,E);if(!CF.arm){if(!inz)CF.arm=true;return}if(inz)cfMapShow();return}
  const mw=cfMapEl(),r=mw.getBoundingClientRect(),m=4,E=CF.edge,inside=(e.clientX>=r.left-m&&e.clientX<=r.right+m&&e.clientY>=r.top-m&&e.clientY<=r.bottom+m)||(E&&cfInZone(e.clientY,E))||mw.contains(e.target);
  if(inside||e.buttons){clearTimeout(CF.t);CF.t=0;return}
  const cm=document.getElementById('ctxm');if(cm&&!cm.hidden)return;
  if(!CF.t){const ms=120*CF.mo;if(ms>0)CF.t=setTimeout(()=>{CF.t=0;cfMapOut(false)},ms);else cfMapOut(false)}},{passive:true,capture:true});
addEventListener('keydown',e=>{if(e.key==='Escape'&&CF.show)cfMapOut(false)},true);
addEventListener('resize',()=>{CF.edge=null;if(CF.show)cfMapOut(true)});
/* a layout change (the map moved to the other side, switched off) puts a shown map away */
{const _al=applyLayout;applyLayout=function(){const r=_al.apply(this,arguments);CF.edge=null;if(CF.show)cfMapOut(true);return r}}
try{XT_CMD_EXTRA.push({id:'view.mapHide',g:'view',l:'Hide the map (it comes up at its edge) or put it back',run:cfMapToggle});XT_CMD.map=null}catch(e){}
setTimeout(cfMapApply,0);

"""
s = s.replace('.dacv{display:flex;', CSS + '.dacv{display:flex;', 1)
s = s.replace('function askChoice(title,text,btns,icon){', JS + 'function askChoice(title,text,btns,icon){', 1)
open(P, 'w', encoding='utf-8').write(s)
print('CF-1 applied to', P)
if CMDS:
    assert VER, '--version is needed with --commands'
    c = open(CMDS, encoding='utf-8').read(); a = '| `view.closeWindows` | Close all floating windows |  | `closewins` | 0.273 |\n'
    assert c.count(a) == 1 and 'view.mapHide' not in c
    c = c.replace(a, a + '| `view.mapHide` | Hide the map (it comes up at its edge) or put it back (lane P, task CF-1) |  |  | %s |\n' % VER, 1)
    open(CMDS, 'w', encoding='utf-8').write(c); print('view.mapHide listed in', CMDS)
