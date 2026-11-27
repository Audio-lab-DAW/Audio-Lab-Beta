#!/usr/bin/env python3
"""Task GS3 (glass step 3): remove the old lens code, then the frame-time fixes and the frame-rate read-out.
   python3 tools/edits/taskGS3.py index.html            (edits in place; every replacement is asserted unique)
Part A removes what the glass engine replaced: the SVG lens (rfAttach, rfBuild, rfMap, rfStyle, the feImage map), the blurred picture
(#arrBlur, abDraw, fxBlurPic), the half-size copy behind live glass (gbCopy's copy), the edge light's read of the blurred picture, the Glass preview
that imitated the old levels, every backdrop-filter declaration (one guard rule stays), and the settings that changed nothing any more.
Part B (frame time) and part C (read-out) are the block tools/edits/taskGS3_block.js and the CSS in tools/edits/taskGS3_css.txt."""
import sys, re, os
P = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
S = open(P, encoding='utf-8').read()
HERE = os.path.dirname(os.path.abspath(__file__))
def rep(old, new, cnt=1):
    global S
    n = S.count(old)
    assert n == cnt, ('expected %d, found %d: ' % (cnt, n)) + old[:160]
    S = S.replace(old, new)
def cut(a, b, new=''):
    """replace from the unique start text a up to and including the unique end text b (the first b after a)"""
    global S
    assert S.count(a) == 1, 'start not unique: ' + a[:120]
    i = S.index(a); j = S.index(b, i)
    assert j - i < 200000, 'span too long'
    S = S[:i] + new + S[j + len(b):]
def line_with(t):
    """the whole line (with its newline) that contains the unique text t"""
    assert S.count(t) == 1, 'not unique: ' + t[:120]
    i = S.index(t); a = S.rindex('\n', 0, i) + 1; b = S.index('\n', i) + 1
    return S[a:b]

assert "const VERSION='0.227'" in S, 'expects v0.227'

# ---------------- A1: CSS of the blurred picture ----------------
rep(line_with('#arrBlur{position:absolute;'), '')
rep(line_with('body.fxpic #fxglass{'), '')

# ---------------- A2: the SVG lens ----------------
rep("NS='http://www.w3.org/2000/svg',RFX=new Map();let rfSvg=null,rfRO=null,rfN=0;", "NS='http://www.w3.org/2000/svg';")
cut('function rfMap(w,h,r,band){', 'function rfAll(){for(const el of RFX.keys())rfUpdate(el)}',
    "/* glass step 3 (v0.228, task GS3): the old SVG lens (rfAttach, rfBuild, rfMap, rfStyle and its feImage map) is gone; the glass engine draws every lens.\n"
    "   The three names stay as empty calls because older code still calls them. */\nfunction rfAttach(){}function rfUpdate(){}function rfAll(){}")
rep(";try{rfAttach(el.querySelector('.spgl'))}catch(e){}", ';')
rep("try{rfAttach(document.getElementById('gpPane'))}catch(e){}fxSync()}", 'fxSync()}')
rep(line_with("if(on&&!B.contains('fxmin')&&typeof rfAttach==='function'&&!RFX.has(b))"), '')
rep(line_with("for(const el of[$('#hglass'),$('#tr'),$('#ctxm'),$('#mPop'),$('#presWin'),...document.querySelectorAll('.sheet')])rfAttach(el);"), '')
# GS1 and GS2 overrides of the lens
rep(line_with('/* the SVG lens never runs for the docked panels (they have no backdrop-filter at any level) */'), '')
rep(line_with("{const _ru=rfUpdate;rfUpdate=function(el){if(el&&(el.id==='hglass'||el.id==='tr'||el.id==='fxband'||el.id==='fxglass'))"), '')
rep(line_with('/* the old SVG lens is not used any more: it makes no filter and no map (the code stays until step 3) */'), '')
rep('rfAttach=function(){};\n', '')
rep(line_with("{const _ru=rfUpdate;rfUpdate=function(el){const o=RFX.get(el);if(o){clearTimeout(o.tm);o.tm=0;if(o.v){o.v='';el.style.backdropFilter='';el.style.webkitBackdropFilter=''}}}}"), '')
rep("   The old lens code (rfAttach, rfBuild, rfMap, rfStyle, the feImage lens) stays in the file but is not used: rfAttach makes nothing any more. Step 3 deletes it\n   after the user's frame-rate check on the Mac.\n",
    "   The old lens code (rfAttach, rfBuild, rfMap, rfStyle, the feImage lens) was deleted by glass step 3 (v0.228, task GS3).\n")

# ---------------- A3: the blurred picture, the copy behind live glass ----------------
cut('/* ---- the blurred picture ---- */\nconst ABL=', "  ABL.p=fxBlurPic(arr,ABL.q,ABL.cv,w,h,b*.8*d*ZOOM*s,1+b/30);ABL.w=w;ABL.h=h}\n", '')
cut('/* the half-size sharp copy behind live glass, as before; with blur from a picture it is not needed and only passes clicks on.',
    "gbTick=function(){if(!GB.on&&!gbOn())return;const n=performance.now();if(n-GB.last>=8)gbCopy(true);else if(!GB.tm)GB.tm=setTimeout(()=>{GB.tm=0;gbCopy(true)},10)};\n", '')
old_copy = line_with('function gbCopy(){GB.last=performance.now();GB.stale=false;if(!gbLayout())return;')
rep(old_copy, "/* glass step 3: nothing is copied any more. #arrBack is an empty 2 x 2 layer that passes clicks on to the arrangement (the glass engine draws what is behind the glass).\n"
    "   The check of which panels cover the arrangement reads layout, so while scrolling it runs 4 times a second instead of on every call. */\n"
    "function gbCopy(fast){const n=performance.now();GB.last=n;GB.stale=false;let ok;if(fast&&n-(GB.lt||0)<250)ok=GB.ok;else{ok=gbLayout();GB.lt=n;GB.ok=ok}\n"
    "  if(ok&&GB.cv&&GB.cv.width!==2){GB.cv.width=2;GB.cv.height=2}elSoon()}\n")
old_tick = line_with('function gbTick(){if(!GB.on&&!gbOn())return;const n=performance.now();/* up to 120 times a second (was 20)')
rep(old_tick, "function gbTick(){if(!GB.on&&!gbOn())return;const n=performance.now();if(n-GB.last>=8)gbCopy(true);else if(!GB.tm)GB.tm=setTimeout(()=>{GB.tm=0;gbCopy(true)},10)}\n")
rep(line_with('/* #arrBack stays as an empty 2 x 2 layer that passes clicks on to the arrangement; nothing is copied into it */'), '')
cut("gbCopy=function(fast){const n=performance.now();GB.last=n;GB.stale=false;let ok;if(fast&&n-(GB.lt||0)<250)ok=GB.ok;else{ok=gbLayout();GB.lt=n;GB.ok=ok}\n  if(ok&&GB.cv&&GB.cv.width!==2)",
    "abDraw();elSoon()};\n", '')
rep(line_with('/* #arrBlur (the blurred picture) is gone */'), '')
rep(line_with("abDraw=function(){const c=ABL.cv;if(c&&c.width){c.width=0;c.height=0;c.style.display='none'}"), '')
rep(line_with("{const _ab=abDraw;abDraw=function(){const r=_ab.apply(this,arguments);try{if(fxGet().blur==='live'&&ABL.cv"), '')
# the edge light read the blurred picture; the version from glass step 1 (a tiny copy of the arrangement) is now the only one
cut("function elTick(){EL.t=performance.now();const f=fxGet(),e=(UI.edge??60)/100;if(!f.edge||e<=0||document.hidden||!ABL.w||!ABL.cv){elClear();return}",
    "for(const el of[...EL.set])if(!seen.has(el)){el.style.removeProperty('--elb');el._elb='';EL.set.delete(el)}}\n", '')
rep("elTick=function(){EL.t=performance.now();const f=fxGet(),e=(UI.edge??60)/100;if(!f.edge||e<=0||document.hidden||arr.width<8||arr.height<8){elClear();return}",
    "function elTick(){EL.t=performance.now();const f=fxGet(),e=(UI.edge??60)/100;if(!f.edge||e<=0||document.hidden||arr.width<8||arr.height<8){elClear();return}")
rep("  for(const el of[...EL.set])if(!seen.has(el)){el.style.removeProperty('--elb');el._elb='';EL.set.delete(el)}};\n{const _at=applyTrans;",
    "  for(const el of[...EL.set])if(!seen.has(el)){el.style.removeProperty('--elb');el._elb='';EL.set.delete(el)}}\n{const _at=applyTrans;")
rep("   nearby light the rim up, dark areas leave it dim. The light is read from a 64 x 36 copy of the blurred picture above (never from the screen), at most",
    "   nearby light the rim up, dark areas leave it dim. The light is read from a 64 x 36 copy of the arrangement (elTick, glass step 1; never from the screen), at most")
# Lightest takes the layers out of the page: only the click layer and the header column are left of them
rep(line_with('function pmLayers(min){try{if(min){if(rfSvg&&rfSvg.isConnected)rfSvg.remove();'),
    "function pmLayers(min){try{if(min){for(const c of[GB.cv,GB.col])if(c&&c.isConnected){c.width=0;c.height=0;c.remove()}elClear()}\n")
rep(line_with('  else{if(rfSvg&&!rfSvg.isConnected)document.body.appendChild(rfSvg);for(const c of[GB.cv,ABL.cv,GB.col])'),
    "  else{for(const c of[GB.cv,GB.col])if(c&&!c.isConnected)arr.before(c)}}catch(e){}}\n")
# softer live blur while playing: there is no live blur
rep("glassPlay=function(on){FXK=on&&UI.glPlay!==false?.5:1;if(fxGet().blur==='live')applyTrans()};",
    "glassPlay=function(){};/* there is no live blur any more (glass step 3), so nothing changes when the song starts or stops */")
rep("let FXK=1;const RFK=60;/* refraction strength, fixed: 75% of the old slider's maximum (the old slider only changed this one number, never the cost) */\n", "let FXK=1;\n")
rep("rfAll();try{GB.lt=0;gbCopy()}catch(e){}dirty=true;try{elSoon();fxSync();GPV.k=''}catch(e){}};", "try{GB.lt=0;gbCopy()}catch(e){}dirty=true;try{elSoon();fxSync()}catch(e){}};")

# ---------------- A4: the Glass preview (it imitated the old levels: refraction bands, blur from a picture, live blur) ----------------
rep(line_with('<div class="gprev" aria-hidden="true"><i class="gb1"></i>'), '')
rep('<div class="gprev" id="gpv" aria-hidden="true"><canvas id="gpBack"></canvas><canvas id="gpBlur"></canvas><div class="gpane lg" id="gpPane"><b>Glass preview</b><span id="gpTxt"></span></div><output id="gpFps"></output></div>`;', '`;')
cut('/* ---- the preview: a real glass panel over moving content, drawn with the same functions as the app (rfAttach, fxBlurPic, elGrad) ---- */',
    "  else if(!f.edge&&pane._elb){pane._elb='';pane.style.removeProperty('--elb')}}\n",
    "/* the Settings loop calls this on every frame: the frame-rate graph of the Performance tab (the Glass preview that was drawn here imitated the old levels and is gone, glass step 3) */\nfunction gpDraw(now){try{pmFpsDraw(now)}catch(e){}}\n")
rep("/* ---- one loop while Settings is open: the logo at a steady 120 pictures a second (it used to follow the visualiser clock, which drops to 2 a second when the mouse rests), and the preview ---- */",
    "/* ---- one loop while Settings is open: the logo (at most 60 pictures a second since glass step 3; it used to follow the visualiser clock, which drops to 2 a second when the mouse rests) and the frame-rate graph ---- */")
rep("{const _gd=gpDraw;gpDraw=function(now){try{pmFpsDraw(now)}catch(e){}return _gd.apply(this,arguments)}}\n", '')
cut('/* --- Glass and light preview: loops made once per setting from ready-made pictures, not live glass.',
    "  gpvFrame(cv,V,(now/1000*36)%GPVP)};\n", '')
rep("const t=document.getElementById('gpTxt');if(t){const f=fxGet(),z=f.blur==='off'&&!f.refr;t.textContent=z?'Solid, no effects':(f.refr?'Refraction':'No refraction')+' · '+(f.blur==='live'?'live blur':f.blur==='copy'?'blur from a picture':'no blur')+(f.edge?' · live edge light':'')}};",
    '};')

# ---------------- A5: settings that change nothing any more ----------------
# Glass and light page: the Blur and the Refraction cards (the engine's Frosting and Lens presets on the Performance tab replace them)
m = re.search(r'<div class="gcard gbl">.*?</div></div></div>', S); assert m and S.count('<div class="gcard gbl">') == 1
S = S[:m.start()] + S[m.end():]
m = re.search(r'<div class="gcard gr">.*?</div></div></div>', S); assert m and S.count('<div class="gcard gr">') == 1
S = S[:m.start()] + S[m.end():]
rep("['#setBlur','blur',18,v=>v+' px'],", '')
rep("['#setRefr','refr',40,v=>v+'%'],", '')
rep("sec.querySelector('#fxRefr').onchange=e=>fxSet({refr:e.target.checked});", '')
rep('<label class="chk"><input type="checkbox" id="glPlay"> Lighter glass while the song plays (smoother playback; the blur is softer only while playing)</label><label class="chk"><input type="checkbox" id="glBack"> Efficient glass: what shows through the panels is refreshed 20 times a second instead of every frame. The arrangement itself still moves at the full screen rate.</label>', '')
rep('<p class="hint" id="refrHint">Refraction bends what\'s behind the glass near its edges, like a thick pane. Edge light adds the bright rim.</p>',
    '<p class="hint" id="refrHint">Edge light adds the bright rim along the top edges of glass.</p>')
# Performance tab: the rows that said "changes nothing now"
rep("<div class=\"pmh\">Windows, sheets and menus: other effects</div><div class=\"pmlist\">`+\n  row('refr','refr','Refraction','Not used any more: windows, sheets and menus get their lens from the glass engine (Lens, above), so this switch changes nothing now.',sw('pmRefr'))+\n  row('blur','blur','Blur','Not used any more: the frosting of windows, sheets and menus comes from the glass engine (Frosting, above), so this choice changes nothing now.','<div class=\"seg\" id=\"pmBlur\"><button type=\"button\" data-bm=\"off\">Off</button><button type=\"button\" data-bm=\"copy\">Picture</button><button type=\"button\" data-bm=\"live\">Live</button></div>')+\n",
    "<div class=\"pmh\">Other effects</div><div class=\"pmlist\">`+\n")
rep("  row('glPlay','play','Softer blur while playing','Not needed any more: there is no live blur in the app, so this switch changes nothing now.','<span data-mv=\"glPlay\"></span>',1)+\n  row('glBack','back','Half-size picture behind glass','Not needed any more: the glass engine draws what is behind the docked panels itself, so this switch changes nothing now.','<span data-mv=\"glBack\"></span>',1)+\n", '')
rep("sec.querySelector('#pmRefr').onchange=e=>pmToggle({refr:e.target.checked});", '')
rep("  sec.querySelector('#pmBlur').onclick=e=>{const b=e.target.closest('[data-bm]');if(b)pmToggle({blur:b.dataset.bm})};\n", '')
rep("q('pmRefr').checked=!!f.refr;q('pmRefr').disabled=!isChromium;q('pmEdge')", "q('pmEdge')")
rep("  for(const b of q('pmBlur').children)b.classList.toggle('on',b.dataset.bm===f.blur);\n", '')
rep(";if(k==='glPlay'||k==='glBack')r.classList.toggle('dis',f.blur!=='live')}}\n  const a=q('pmAuto');", "}}\n  const a=q('pmAuto');")
# the texts of the stops say what they do now (the docked panels, windows, sheets and menus are all glass from the engine)
rep("const PMD=['Fastest and lightest: no transparency, no blur, no shadows, no animations.','Light glass on the docked panels, solid windows and menus, no animations. Pictures redraw 30 times a second.','Glass on the docked panels. Windows and menus with blur from a ready-made picture. Smooth on most computers.','Glass on the docked panels. Windows and menus with refraction, live blur, edge light and every animation.'];",
    "const PMD=['Fastest and lightest: no transparency, no glass, no shadows, no animations.','Light glass without the lens on panels, windows and menus, no animations. Pictures redraw 30 times a second.','Glass with the lens on panels, windows and menus. Smooth on most computers.','Glass with the lens on panels, windows and menus, edge light and every animation.'];")

# ---------------- A6: every backdrop-filter declaration (one guard rule stays, so none can come back by accident) ----------------
rep('(one CSS rule: *,*::before,*::after{backdrop-filter:none!important}).', '(one CSS rule sets it to none on every element and pseudo element).')
GUARD = '\n*,*::before,*::after{backdrop-filter:none!important;-webkit-backdrop-filter:none!important}'
assert S.count(GUARD) == 1, 'guard rule'
S = S.replace(GUARD, '@@GUARD@@')
n0 = len(re.findall(r'(?:-webkit-)?backdrop-filter\s*:', S))
S = re.sub(r'(?:-webkit-)?backdrop-filter\s*:[^;}"\'`]*;?', '', S)
S = S.replace('@@GUARD@@', GUARD)
print('backdrop-filter declarations removed:', n0)
assert not re.findall(r'(?:-webkit-)?backdrop-filter\s*:', S.replace(GUARD, '')), 'left'
for _k in ['function rfMap',"mk('feImage'",'function fxBlurPic','ABL.','gpvSetup','rfSvg','function rfBuild','function rfStyle']: assert _k not in S, (_k, S[S.index(_k)-200:S.index(_k)+100])

# saved settings of the removed controls are dropped once (UI.refr stays: the first start of an older version still reads it)
PART_A_DONE = True

# ---------------- B and C: frame time and the read-out ----------------
block = open(os.path.join(HERE, 'taskGS3_block.js'), encoding='utf-8').read()
css = open(os.path.join(HERE, 'taskGS3_css.txt'), encoding='utf-8').read().strip()
rep('function askChoice(title,text,btns,icon){', block.rstrip('\n') + '\nfunction askChoice(title,text,btns,icon){')
rep('.dacv{display:flex;', css + '\n.dacv{display:flex;')
exec(open(os.path.join(HERE, 'taskGS3_b.py'), encoding='utf-8').read())
S = S.replace("const VERSION='0.227'", "const VERSION='0.228'")
open(P, 'w', encoding='utf-8').write(S)
print('ok', P)
